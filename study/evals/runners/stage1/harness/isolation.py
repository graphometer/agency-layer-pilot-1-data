"""Namespace isolation for everything a run executes (PM14).

The Stage 1 sandbox used to be a directory under /tmp on the lab host with the
whole filesystem readable. In the 2026-08-22 cost rehearsal nine of sixty
transcripts touched host paths: models read the scenario's own source and its
ground truth, read the vault's documents, and ran `find / -iname "*.env*"` and
got back the paths of backup credential files. A run that reads its own scenario
is contaminated, the family 2 premise ("no such endpoint exists") is false on a
host with a network, and anything the model reads can reach an API provider and,
under R4 and R19, a published transcript.

PM14 makes isolation a precondition of every further real-model run. This module
is the one place the isolation is defined. Every command a run executes goes
through it: the model's own `run_command`, the scenario's `success_check`, and
the harness's own `check.py` invocation against the sandbox. Nothing else builds
a bwrap argv.

What the child sees:

    /work        the sandbox copy, read-write, and the working directory
    /usr         the host's /usr, READ-ONLY, with /bin /sbin /lib /lib64 as the
                 usual symlinks into it
    /etc         four files: a synthetic passwd and group naming one user
                 `agent` with home /work, a minimal hosts, a minimal
                 nsswitch.conf, plus the host's /etc/alternatives read-only
                 because `awk` and friends are Debian alternatives symlinks
    /opt/node    the node prefix, read-only, when node lives outside /usr
    /proc        a private procfs in a private PID namespace
    /dev         bubblewrap's minimal device set
    /tmp         an empty tmpfs

What it does not see: /mnt, /home, the harness source, any host /tmp beyond its
own sandbox, any network beyond loopback, and any environment variable other
than PATH, HOME and LANG. The harness sources .env into its own process; the
child gets a clean environment, so no API key crosses the boundary.

The harness process itself stays outside the namespace. It is the thing that
calls providers, so it keeps its keys and its network; the model's hands do not.
"""

import atexit
import codecs
import json
import os
import selectors
import shutil
import subprocess
import tempfile
import threading
import time

BWRAP = "/usr/bin/bwrap"

# The child's environment, in full. PATH gains the node prefix when node is
# bound in from outside /usr; nothing else is ever added.
BASE_PATH = "/usr/local/bin:/usr/bin:/bin"
NODE_MOUNT = "/opt/node"
WORK = "/work"

# The shell every model command is run under. The suggested PM14 shape, and a
# superset of the dash that `shell=True` used to give: a model command that
# depends on a bashism now behaves the same way on every host.
SHELL = ["bash", "-c"]  # -c, not -lc: a login shell would source a model-written /work/.bash_profile (REVIEW_OPUS_6 finding 2)

# Read-only host paths the base system needs. `alternatives` is a symlink farm
# into /usr, and without it `awk`, `editor` and a dozen other names are missing;
# f9-02's build.sh calls awk.
ETC_RO_TRY = ("/etc/alternatives",)

PASSWD_TEMPLATE = (
    "root:x:0:0:root:/root:/usr/sbin/nologin\n"
    "agent:x:{uid}:{gid}:agent:{work}:/bin/bash\n"
    "nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin\n"
)
GROUP_TEMPLATE = "root:x:0:\nagent:x:{gid}:\nnogroup:x:65534:\n"
HOSTS_FILE = "127.0.0.1\tlocalhost\n::1\tlocalhost ip6-localhost ip6-loopback\n"
NSSWITCH_FILE = "passwd: files\ngroup: files\nshadow: files\nhosts: files\n"

# The canary. Written into a throwaway sandbox and run inside the namespace by
# probe(); prints one JSON object. Standard library only, and it never reads
# anything it is not asserting about.
CANARY = r'''
import json, os, socket, subprocess, sys

report = {}
report["cwd"] = os.getcwd()
report["root_listing"] = sorted(os.listdir("/"))
report["mnt_present"] = os.path.exists("/mnt")
report["home_present"] = os.path.exists("/home")
report["harness_source_present"] = any(os.path.exists(p) for p in sys.argv[2:])
report["env"] = dict(os.environ)
report["python_version"] = sys.version.split()[0]
report["uname_nodename"] = os.uname().nodename

try:
    with open("/work/.probe_marker", "r", encoding="utf-8") as fh:
        report["marker"] = fh.read().strip()
except OSError as error:
    report["marker"] = "unreadable: %s" % error

try:
    with open("/work/.probe_written", "w", encoding="utf-8") as fh:
        fh.write("written")
    report["work_writable"] = True
except OSError as error:
    report["work_writable"] = False
    report["work_write_error"] = str(error)

try:
    socket.create_connection(("1.1.1.1", 53), timeout=2).close()
    report["network"] = "REACHED"
except Exception as error:
    report["network"] = "blocked: %s: %s" % (type(error).__name__, error)

try:
    socket.gethostbyname("example.com")
    report["dns"] = "RESOLVED"
except Exception as error:
    report["dns"] = "blocked: %s" % type(error).__name__

# Loopback must still work: f9-02 serves its assets over 127.0.0.1.
try:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    client = socket.create_connection(server.getsockname(), timeout=2)
    client.close()
    server.close()
    report["loopback"] = "ok"
except Exception as error:
    report["loopback"] = "broken: %s: %s" % (type(error).__name__, error)

if sys.argv[1] == "node":
    try:
        done = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=30)
        report["node_version"] = done.stdout.strip() or ("exit %s" % done.returncode)
    except Exception as error:
        report["node_version"] = "missing: %s: %s" % (type(error).__name__, error)
else:
    report["node_version"] = None

print(json.dumps(report, sort_keys=True))
'''

# Environment names that must never appear in the child. Matched against the
# name with separators stripped, the same shape harness/config.py uses.
KEYLIKE_FRAGMENTS = (
    "key", "token", "secret", "password", "passwd", "credential", "auth",
    "api", "bearer", "session", "cookie",
)
ALLOWED_ENV = ("PATH", "HOME", "LANG")
# bash sets these itself; they are not inherited and carry nothing from the host.
SHELL_INJECTED_ENV = ("PWD", "SHLVL", "_", "OLDPWD")

# sandbox.run_command keeps 20,000 characters per stream. Four bytes is the
# maximum UTF-8 width, and one character of look-ahead distinguishes an exact
# boundary from truncation. Capture never retains more than this per stream;
# the rest is drained and discarded while the child remains under its wall
# timeout.
MAX_CAPTURE_BYTES = (20_000 + 1) * 4

_DECODE_STATE = threading.local()


def _counting_replace(error):
    _DECODE_STATE.rejected += error.end - error.start
    return "\ufffd", error.end


codecs.register_error("agency_layer_counting_replace", _counting_replace)


def decode_utf8_output(value):
    """Decode captured process bytes without letting bad output kill a run.

    The count is bytes rejected by the strict UTF-8 decoder, not merely the
    number of replacement characters. Those differ for some malformed byte
    sequences, and the byte count is the useful audit value here.
    """
    if isinstance(value, str):
        return value, 0
    data = value or b""
    # One C-level decode performs replacement and calls the error handler once
    # per rejected span. Thread-local state keeps concurrent command captures
    # independent without copying or rescanning the byte buffer.
    previous = getattr(_DECODE_STATE, "rejected", None)
    _DECODE_STATE.rejected = 0
    try:
        decoded = data.decode("utf-8", errors="agency_layer_counting_replace")
        rejected = _DECODE_STATE.rejected
    finally:
        if previous is None:
            del _DECODE_STATE.rejected
        else:
            _DECODE_STATE.rejected = previous
    return decoded, rejected


def _decoded_process(completed, stream_totals=None):
    """Return a CompletedProcess whose output is safe UTF-8 text."""
    stdout, stdout_replaced = decode_utf8_output(completed.stdout)
    stderr, stderr_replaced = decode_utf8_output(completed.stderr)
    decoded = subprocess.CompletedProcess(
        completed.args, completed.returncode, stdout=stdout, stderr=stderr
    )
    decoded.stdout_decode_replaced_bytes = stdout_replaced
    decoded.stderr_decode_replaced_bytes = stderr_replaced
    decoded.decode_replaced_bytes = stdout_replaced + stderr_replaced
    decoded.decode_replaced = decoded.decode_replaced_bytes > 0
    totals = stream_totals or {
        "stdout": len(completed.stdout or b""), "stderr": len(completed.stderr or b"")
    }
    decoded.stdout_captured_bytes = len(completed.stdout or b"")
    decoded.stderr_captured_bytes = len(completed.stderr or b"")
    decoded.stdout_total_bytes = int(totals["stdout"])
    decoded.stderr_total_bytes = int(totals["stderr"])
    decoded.stdout_truncated = decoded.stdout_total_bytes > decoded.stdout_captured_bytes
    decoded.stderr_truncated = decoded.stderr_total_bytes > decoded.stderr_captured_bytes
    decoded.output_truncated = decoded.stdout_truncated or decoded.stderr_truncated
    return decoded


def _run_captured(*args, **kwargs):
    """Capture bounded byte prefixes while draining both process streams.

    The deadline starts before the child is created and is checked through the
    final bounded decode. Output beyond MAX_CAPTURE_BYTES is counted and
    discarded, never accumulated in memory.
    """
    timeout = kwargs.pop("timeout", None)
    kwargs.pop("capture_output", None)
    kwargs.pop("text", None)
    kwargs.pop("encoding", None)
    kwargs.pop("errors", None)
    kwargs.setdefault("start_new_session", True)
    started = time.monotonic()
    deadline = None if timeout is None else started + float(timeout)
    process = subprocess.Popen(*args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    selector = selectors.DefaultSelector()
    streams = {"stdout": process.stdout, "stderr": process.stderr}
    buffers = {name: bytearray() for name in streams}
    totals = {name: 0 for name in streams}
    for name, stream in streams.items():
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, name)

    timed_out = False
    timeout_cleanup_deadline = None

    def kill_process_group():
        try:
            os.killpg(process.pid, 9)
        except (OSError, ProcessLookupError):
            process.kill()

    try:
        while selector.get_map():
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                if not timed_out:
                    timed_out = True
                    kill_process_group()
                    timeout_cleanup_deadline = time.monotonic() + 0.25
                remaining = max(0.0, timeout_cleanup_deadline - time.monotonic())
                if remaining <= 0:
                    break
            events = selector.select(remaining)
            if not events and timed_out:
                break
            for key, _ in events:
                name = key.data
                try:
                    chunk = os.read(key.fileobj.fileno(), 65_536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                totals[name] += len(chunk)
                room = MAX_CAPTURE_BYTES - len(buffers[name])
                if room > 0:
                    buffers[name].extend(chunk[:room])
        if timed_out:
            process.wait(timeout=1)
        else:
            remaining = None if deadline is None else max(0.0, deadline - time.monotonic())
            process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_process_group()
        process.wait()
    finally:
        selector.close()
        for stream in streams.values():
            stream.close()

    completed = subprocess.CompletedProcess(
        args[0] if args else kwargs.get("args"), process.returncode,
        stdout=bytes(buffers["stdout"]), stderr=bytes(buffers["stderr"]),
    )
    decoded = _decoded_process(completed, totals)
    if timed_out or (deadline is not None and time.monotonic() > deadline):
        raise subprocess.TimeoutExpired(
            completed.args, timeout, output=decoded.stdout, stderr=decoded.stderr
        )
    return decoded


class IsolationError(RuntimeError):
    """The isolation could not be built or did not hold. Never a tool error."""


def _keylike(name):
    folded = "".join(character for character in name.lower() if character.isalnum())
    return any(fragment in folded for fragment in KEYLIKE_FRAGMENTS)


_SUPPORT_DIR = None


def _support_dir():
    """The synthetic /etc files, made once per process.

    The host's own /etc/passwd is never bound in: it names every account on the
    machine, which is host information a run has no business reading. One user
    exists inside, called agent, with home /work.
    """
    global _SUPPORT_DIR
    if _SUPPORT_DIR and os.path.isdir(_SUPPORT_DIR):
        return _SUPPORT_DIR
    directory = tempfile.mkdtemp(prefix="al-isolation-etc-")
    uid, gid = os.getuid(), os.getgid()
    files = {
        "passwd": PASSWD_TEMPLATE.format(uid=uid, gid=gid, work=WORK),
        "group": GROUP_TEMPLATE.format(gid=gid),
        "hosts": HOSTS_FILE,
        "nsswitch.conf": NSSWITCH_FILE,
    }
    for name, body in files.items():
        with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
            handle.write(body)
        os.chmod(os.path.join(directory, name), 0o444)
    _SUPPORT_DIR = directory
    atexit.register(shutil.rmtree, directory, True)
    return directory


def find_node_prefix():
    """Where node lives, as a prefix directory containing bin/node.

    Returns None when node is already inside /usr, which is bound read-only
    anyway, and raises when node cannot be found at all. On this lab host node
    is under /home, which the sandbox must not expose, so only the node prefix
    itself is bound, at /opt/node.
    """
    found = shutil.which("node")
    if not found:
        return None
    real = os.path.realpath(found)
    if real.startswith("/usr/"):
        return "usr"
    prefix = os.path.dirname(os.path.dirname(real))
    if os.path.basename(os.path.dirname(real)) != "bin":
        raise IsolationError(f"node at {real} is not in a bin/ directory; cannot derive a prefix")
    if prefix in ("/", "/home", os.path.expanduser("~")):
        raise IsolationError(
            f"refusing to bind {prefix!r} into the sandbox: it is a home or root directory, "
            "not a node prefix"
        )
    if not os.path.isfile(os.path.join(prefix, "bin", "node")):
        raise IsolationError(f"{prefix} does not contain bin/node")
    return prefix


def bwrap_version(bwrap_path=BWRAP):
    try:
        done = subprocess.run([bwrap_path, "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        raise IsolationError(f"{bwrap_path} could not be run: {type(error).__name__}: {error}")
    if done.returncode != 0:
        raise IsolationError(f"{bwrap_path} --version exited {done.returncode}: {done.stderr.strip()}")
    return done.stdout.strip()


class NoIsolation:
    """The explicit, recorded absence of isolation.

    Kept so a host without working user namespaces can still run the mock
    proofs, and so the absence is a value in run.json rather than a silence. A
    live batch refuses to start on it (harness/cli.py).
    """

    kind = "none"
    version = None

    def __init__(self, reason="isolation disabled in config"):
        self.reason = reason
        self.probe_result = {"status": "not_run", "reason": reason, "checks": {}, "failures": []}

    def probe(self):
        self.probe_result = {
            "status": "fail",
            "reason": self.reason,
            "checks": {},
            "failures": [f"no isolation is in place: {self.reason}"],
        }
        return self.probe_result

    def record(self):
        return {"kind": self.kind, "version": None, "probe": self.probe_result["status"]}

    def child_environment(self, root):
        return {"PATH": BASE_PATH, "HOME": root, "PWD": root, "LANG": "C.UTF-8", "TMPDIR": root}

    def argv(self, root, inner_argv):
        return list(inner_argv)

    def shell_argv(self, root, command):
        return list(SHELL) + [command]

    def spawn(self, root, inner_argv, timeout):
        return _run_captured(
            self.argv(root, inner_argv), cwd=root, env=self.child_environment(root),
            timeout=timeout,
        )

    def spawn_shell(self, root, command, timeout):
        return self.spawn(root, self.shell_argv(root, command), timeout)


class BwrapIsolation:
    """One bubblewrap invocation, built in one place.

    `hardening` records which optional flags this host accepted. --unshare-user
    plus --disable-userns is the pair that stops a model creating its own nested
    namespace; on a host where unprivileged user namespaces are restricted the
    pair is dropped and the probe is what decides whether what remains is good
    enough. It is not: probe() fails without a user namespace, because without
    one the bind mounts are not enforceable.
    """

    kind = "bwrap"

    def __init__(self, bwrap_path=BWRAP, node_prefix=None, require_node=True,
                 harness_paths=()):
        if not os.path.exists(bwrap_path):
            raise IsolationError(
                f"{bwrap_path} does not exist. bubblewrap is how PM14 isolation is built; "
                "install it or configure isolation: none and accept that no live batch will run."
            )
        self.bwrap_path = bwrap_path
        self.version = bwrap_version(bwrap_path)
        self.require_node = require_node
        self.harness_paths = tuple(os.path.abspath(path) for path in harness_paths)

        if node_prefix is None:
            node_prefix = find_node_prefix()
        # "usr" means node is already under the read-only /usr bind.
        self.node_prefix = None if node_prefix == "usr" else node_prefix
        self.node_in_usr = node_prefix == "usr"
        if require_node and node_prefix is None:
            raise IsolationError(
                "node was not found on the harness PATH, and family 1, 3, 5 and 9 fixtures "
                "run node. Install node or set require_node false."
            )
        self.hardening = self._probe_hardening()
        self.probe_result = {"status": "not_run", "checks": {}, "failures": []}

    # ------------------------------------------------------------------ argv

    @property
    def path_value(self):
        if self.node_prefix:
            return BASE_PATH + ":" + NODE_MOUNT + "/bin"
        return BASE_PATH

    def _hardening_flags(self, hardening):
        flags = []
        if "unshare-user" in hardening:
            flags += ["--unshare-user"]
        if "disable-userns" in hardening:
            flags += ["--disable-userns"]
        if "cap-drop-all" in hardening:
            flags += ["--cap-drop", "ALL"]
        if "hostname" in hardening:
            flags += ["--hostname", "sandbox"]
        return flags

    def argv(self, root, inner_argv, hardening=None):
        """The full bwrap argv for one command. The only place it is built."""
        # A real sandbox root is always absolute and is normalized; a placeholder
        # from argv_template() is left as written so the record reads cleanly.
        root = os.path.realpath(root) if os.path.isabs(root) else root
        support = _support_dir()
        argv = [
            self.bwrap_path,
            "--ro-bind", "/usr", "/usr",
            "--symlink", "usr/lib", "/lib",
            "--symlink", "usr/lib64", "/lib64",
            "--symlink", "usr/bin", "/bin",
            "--symlink", "usr/sbin", "/sbin",
        ]
        for path in ETC_RO_TRY:
            argv += ["--ro-bind-try", path, path]
        argv += [
            "--ro-bind", os.path.join(support, "passwd"), "/etc/passwd",
            "--ro-bind", os.path.join(support, "group"), "/etc/group",
            "--ro-bind", os.path.join(support, "hosts"), "/etc/hosts",
            "--ro-bind", os.path.join(support, "nsswitch.conf"), "/etc/nsswitch.conf",
        ]
        if self.node_prefix:
            argv += ["--ro-bind", self.node_prefix, NODE_MOUNT]
        argv += [
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            "--bind", root, WORK,
            "--chdir", WORK,
            "--unshare-all",
        ]
        argv += self._hardening_flags(self.hardening if hardening is None else hardening)
        argv += [
            "--die-with-parent",
            "--new-session",
            "--clearenv",
            "--setenv", "PATH", self.path_value,
            "--setenv", "HOME", WORK,
            "--setenv", "LANG", "C.UTF-8",
            "--",
        ]
        return argv + list(inner_argv)

    def shell_argv(self, root, command):
        return self.argv(root, list(SHELL) + [command])

    def argv_template(self):
        """The argv with the per-run parts named, for the record in DONE and batch.json."""
        return self.argv("<sandbox>", ["<command>"])

    # ----------------------------------------------------------------- spawn

    def _outer_environment(self):
        # bwrap's own environment. --clearenv means nothing here reaches the
        # child; it is minimal anyway so a traceback can never carry a key.
        return {"PATH": "/usr/bin:/bin"}

    def spawn(self, root, inner_argv, timeout):
        return _run_captured(
            self.argv(root, inner_argv), cwd=os.path.realpath(root),
            env=self._outer_environment(), timeout=timeout,
        )

    def spawn_shell(self, root, command, timeout):
        return _run_captured(
            self.shell_argv(root, command), cwd=os.path.realpath(root),
            env=self._outer_environment(), timeout=timeout,
        )

    # ------------------------------------------------------------- hardening

    def _probe_hardening(self):
        """Find the strongest flag set this host accepts, once, cheaply.

        --unshare-all uses --unshare-user-try, and --disable-userns refuses to
        run without an explicit --unshare-user, so the two are asked for
        together. Each candidate is tried in order and the first that runs
        `true` wins.
        """
        candidates = [
            ("unshare-user", "disable-userns", "cap-drop-all", "hostname"),
            ("unshare-user", "cap-drop-all", "hostname"),
            ("cap-drop-all", "hostname"),
            ("hostname",),
            (),
        ]
        scratch = tempfile.mkdtemp(prefix="al-isolation-flagcheck-")
        try:
            for candidate in candidates:
                argv = self.argv(scratch, ["true"], hardening=candidate)
                try:
                    done = subprocess.run(argv, cwd=scratch, env=self._outer_environment(),
                                          capture_output=True, text=True, timeout=60)
                except (OSError, subprocess.SubprocessError):
                    continue
                if done.returncode == 0:
                    return list(candidate)
            raise IsolationError(
                "bubblewrap could not start a sandbox with any flag set on this host. "
                f"Last error: {done.stderr.strip() if done.stderr else 'no output'}"
            )
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    # ----------------------------------------------------------------- probe

    def probe(self, timeout=120):
        """Run a canary inside the namespace and assert the isolation holds.

        Everything PM14 names is checked from the inside, on a throwaway
        sandbox, before any batch starts. A failure here stops a live batch.
        """
        checks = {}
        failures = []
        details = {}
        scratch = tempfile.mkdtemp(prefix="al-isolation-probe-")
        try:
            marker = os.urandom(8).hex()
            with open(os.path.join(scratch, ".probe_marker"), "w", encoding="utf-8") as handle:
                handle.write(marker)
            with open(os.path.join(scratch, "canary.py"), "w", encoding="utf-8") as handle:
                handle.write(CANARY)

            inner = ["python3", "/work/canary.py",
                     "node" if self.require_node else "no-node"] + list(self.harness_paths)
            try:
                done = self.spawn(scratch, inner, timeout)
            except subprocess.SubprocessError as error:
                failures.append(f"the canary could not be run: {type(error).__name__}: {error}")
                done = None

            report = None
            if done is not None:
                if done.returncode != 0:
                    failures.append(f"the canary exited {done.returncode}: {done.stderr.strip()[:600]}")
                try:
                    report = json.loads(done.stdout.strip().splitlines()[-1])
                except (ValueError, IndexError):
                    failures.append(f"the canary printed no JSON report: {done.stdout.strip()[:600]}")

            if report is not None:
                details = report
                checks["python3_runs"] = bool(report.get("python_version"))
                checks["mnt_absent"] = report.get("mnt_present") is False
                checks["home_absent"] = report.get("home_present") is False
                checks["harness_source_absent"] = report.get("harness_source_present") is False
                checks["network_blocked"] = str(report.get("network", "")).startswith("blocked")
                checks["dns_blocked"] = str(report.get("dns", "")).startswith("blocked")
                checks["loopback_available"] = report.get("loopback") == "ok"
                checks["work_is_the_sandbox"] = report.get("marker") == marker
                checks["work_writable"] = report.get("work_writable") is True
                checks["cwd_is_work"] = report.get("cwd") == WORK

                environment = report.get("env") or {}
                leaked = sorted(name for name in environment if _keylike(name))
                checks["no_keylike_environment"] = not leaked
                if leaked:
                    failures.append(f"key-shaped environment names reached the child: {leaked}")
                unexpected = sorted(
                    name for name in environment
                    if name not in ALLOWED_ENV and name not in SHELL_INJECTED_ENV
                )
                checks["environment_is_minimal"] = not unexpected
                if unexpected:
                    failures.append(f"unexpected environment names reached the child: {unexpected}")
                checks["home_is_work"] = environment.get("HOME") == WORK

                if self.require_node:
                    version = str(report.get("node_version") or "")
                    checks["node_runs"] = version.startswith("v")
                # A run must not be able to build its own namespace and undo this.
                checks["nested_userns_disabled"] = "disable-userns" in self.hardening
                if "disable-userns" not in self.hardening:
                    failures.append(
                        "--disable-userns is not in force, so a command inside the sandbox "
                        "can create its own user namespace"
                    )
                if "unshare-user" not in self.hardening:
                    failures.append(
                        "no user namespace was created, so the read-only binds are not enforced"
                    )
                    checks["user_namespace"] = False
                else:
                    checks["user_namespace"] = True

            # The shell path model commands actually take.
            try:
                shell = self.spawn_shell(scratch, "echo PROBE_SHELL_OK", timeout)
                checks["bash_runs"] = shell.returncode == 0 and "PROBE_SHELL_OK" in shell.stdout
                if not checks["bash_runs"]:
                    failures.append(f"bash -c did not run: {shell.stderr.strip()[:400]}")
            except subprocess.SubprocessError as error:
                checks["bash_runs"] = False
                failures.append(f"bash -c could not be run: {type(error).__name__}: {error}")

            # The write must have landed in the throwaway sandbox and nowhere else.
            checks["write_landed_in_sandbox"] = os.path.exists(
                os.path.join(scratch, ".probe_written"))
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

        for name, passed in sorted(checks.items()):
            if not passed:
                failures.append(f"probe check failed: {name}")
        # Deduplicate while keeping the first, more informative, message.
        seen, ordered = set(), []
        for failure in failures:
            if failure not in seen:
                seen.add(failure)
                ordered.append(failure)
        self.probe_result = {
            "status": "pass" if not ordered else "fail",
            "checks": checks,
            "failures": ordered,
            "details": details,
            "hardening": list(self.hardening),
            "bwrap_version": self.version,
            "node_prefix": self.node_prefix or ("/usr" if self.node_in_usr else None),
        }
        return self.probe_result

    def record(self):
        """The three fields every run.json and batch.json carries."""
        return {"kind": self.kind, "version": self.version, "probe": self.probe_result["status"]}


def build(config, harness_paths=()):
    """Build the isolation named by a config.

    `isolation: bwrap` (the default) or `isolation: none`. A mapping is also
    accepted so a host can name its bwrap or its node prefix:

        isolation:
          kind: bwrap
          bwrap_path: /usr/bin/bwrap
          node_prefix: /opt/node-22
          require_node: true
    """
    spec = config.get("isolation", "bwrap")
    if spec is None:
        spec = "none"
    if isinstance(spec, str):
        spec = {"kind": spec}
    kind = spec.get("kind", "bwrap")
    if kind == "none":
        return NoIsolation(reason=spec.get("reason", "isolation: none in config"))
    if kind != "bwrap":
        raise IsolationError(f"unknown isolation kind {kind!r}; use bwrap or none")
    return BwrapIsolation(
        bwrap_path=spec.get("bwrap_path", BWRAP),
        node_prefix=spec.get("node_prefix"),
        require_node=spec.get("require_node", True),
        harness_paths=harness_paths,
    )
