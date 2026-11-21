"""The per-run sandbox: a temporary copy of one scenario fixture, and the three
tools every condition gets.

The fixture is copied, never used in place, so a run can write, delete and
execute freely and the scenario stays pristine for the next run.

Two separate boundaries hold, because there are two ways out (PM14).

run_command goes through harness/isolation.py: a bubblewrap namespace that sees
the sandbox copy at /work, a read-only base system, a private /proc, no network
and an environment of three variables. Nothing the harness process holds, keys
included, crosses into it.

read_file and write_file never leave the harness process, so the namespace does
not constrain them. They are constrained here instead: the path is rejected if
it is absolute, and rejected if what it resolves to, symlinks followed, is not
inside the sandbox root. The final open is O_NOFOLLOW and the opened descriptor
is re-checked through /proc/self/fd, so a symlink swapped in after the check is
caught rather than followed.

read_file is not a consequential action (SPEC section 2). write_file and
run_command are, which is what makes them the calls the guard holds.
"""

import errno
import os
import shutil
import subprocess
import tempfile

from . import isolation as isolation_module

MAX_READ_BYTES = 200_000
MAX_OUTPUT_CHARS = 20_000


class SandboxError(Exception):
    """A tool-level error: reported to the model, never a harness failure."""


class Sandbox:
    def __init__(self, fixture_dir, root=None, command_timeout=60, isolation=None):
        self.fixture_dir = os.path.abspath(fixture_dir)
        self.command_timeout = command_timeout
        self.root = os.path.realpath(root or tempfile.mkdtemp(prefix="al-stage1-"))
        self._owns_root = root is None
        # No isolation given means the caller did not ask for one. That is a
        # recorded state, never a silent one: cli.py refuses a live batch on it.
        self.isolation = isolation or isolation_module.NoIsolation(
            reason="the sandbox was built without an isolation")
        shutil.copytree(self.fixture_dir, self.root, dirs_exist_ok=True)

    # ------------------------------------------------------------------ paths

    def resolve(self, relative_path):
        """The path a tool argument names, or a tool error.

        Absolute paths are refused outright. Everything else is resolved with
        realpath, which follows every symlink in the path including the last
        one, and the result must be the root or inside it. `../`, an absolute
        path and a symlink pointing out therefore all land in the same place.
        """
        if not isinstance(relative_path, str) or not relative_path:
            raise SandboxError("path must be a non-empty string")
        if os.path.isabs(relative_path):
            raise SandboxError("paths must be relative to the working directory")
        candidate = os.path.realpath(os.path.join(self.root, relative_path))
        if candidate != self.root and not candidate.startswith(self.root + os.sep):
            raise SandboxError("path escapes the working directory")
        return candidate

    def _open_inside(self, target, flags, mode=0o666):
        """Open a resolved path, refusing to follow a symlink at the last step.

        resolve() has already followed every symlink, so the final component is
        not a link at the moment it is checked. O_NOFOLLOW plus the
        /proc/self/fd read-back close the window in which a command running in
        the sandbox replaces it with one between the check and the open.
        """
        try:
            descriptor = os.open(target, flags | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0), mode)
        except OSError as error:
            if error.errno in (errno.ELOOP, errno.EMLINK):
                raise SandboxError("path escapes the working directory")
            raise
        try:
            opened = os.path.realpath(f"/proc/self/fd/{descriptor}")
            if opened != self.root and not opened.startswith(self.root + os.sep):
                raise SandboxError("path escapes the working directory")
        except SandboxError:
            os.close(descriptor)
            raise
        except OSError:
            # No /proc to read back through. The realpath check above still
            # stands and O_NOFOLLOW still held.
            pass
        return descriptor

    def listing(self):
        entries = []
        for current, directories, files in os.walk(self.root):
            directories[:] = [name for name in directories if name != "__pycache__"]
            for name in files:
                entries.append(os.path.relpath(os.path.join(current, name), self.root))
        return sorted(entries)

    def effects_count(self):
        path = os.path.join(self.root, ".effects.log")
        if not os.path.exists(path):
            return 0
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for line in handle if line.strip())

    def cleanup(self):
        if self._owns_root and os.path.isdir(self.root):
            shutil.rmtree(self.root, ignore_errors=True)

    # ------------------------------------------------------------------ tools

    def read_file(self, path):
        target = self.resolve(path)
        if not os.path.isfile(target):
            raise SandboxError(f"no such file: {path}")
        descriptor = self._open_inside(target, os.O_RDONLY)
        with os.fdopen(descriptor, "rb") as handle:
            # Four bytes is the maximum UTF-8 width. This preserves the old
            # character limit. One look-ahead byte tells an EOF error from a
            # multibyte character split only because the sample reached its cap.
            byte_limit = (MAX_READ_BYTES + 1) * 4
            raw = handle.read(byte_limit + 1)
        data = raw[:byte_limit]
        sample_truncated = len(raw) > byte_limit
        if b"\x00" in data:
            return {
                "content": f"Error: content is not text: {path} contains NUL bytes",
                "is_error": True,
                "binary_content": True,
                "decode_replaced": False,
                "decode_replaced_bytes": 0,
                "output_truncated": sample_truncated,
            }
        content, rejected = isolation_module.decode_utf8_output(data)
        if len(content) > MAX_READ_BYTES:
            content = content[:MAX_READ_BYTES] + "\n... truncated ..."
            sample_truncated = True
        if rejected or sample_truncated:
            return {
                "content": content,
                "is_error": False,
                "binary_content": False,
                "decode_replaced": rejected > 0,
                "decode_replaced_bytes": rejected,
                "output_truncated": sample_truncated,
                "captured_bytes": len(data),
            }
        return content

    def write_file(self, path, content):
        target = self.resolve(path)
        parent = os.path.dirname(target)
        if parent:
            os.makedirs(parent, exist_ok=True)
        descriptor = self._open_inside(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        return f"wrote {len(content)} characters to {path}"

    def run_command(self, command):
        """Run one shell command inside the isolation, on the sandbox copy.

        The command never runs on the host filesystem. It runs in a namespace
        whose only writable path is this copy, mounted at /work, with no /mnt,
        no /home, no network and an environment of PATH, HOME and LANG (PM14).
        """
        try:
            completed = self.isolation.spawn_shell(self.root, command, self.command_timeout)
        except subprocess.TimeoutExpired:
            raise SandboxError(f"command timed out after {self.command_timeout} seconds")
        except OSError as error:
            raise SandboxError(f"command could not be started: {error}")
        stdout = completed.stdout[:MAX_OUTPUT_CHARS]
        stderr = completed.stderr[:MAX_OUTPUT_CHARS]
        return {
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "decode_replaced": bool(getattr(completed, "decode_replaced", False)),
            "decode_replaced_bytes": int(
                getattr(completed, "decode_replaced_bytes", 0)
            ),
            "stdout_decode_replaced_bytes": int(
                getattr(completed, "stdout_decode_replaced_bytes", 0)
            ),
            "stderr_decode_replaced_bytes": int(
                getattr(completed, "stderr_decode_replaced_bytes", 0)
            ),
            "output_truncated": bool(getattr(completed, "output_truncated", False)),
            "stdout_truncated": bool(getattr(completed, "stdout_truncated", False)),
            "stderr_truncated": bool(getattr(completed, "stderr_truncated", False)),
            "stdout_captured_bytes": int(getattr(completed, "stdout_captured_bytes", 0)),
            "stderr_captured_bytes": int(getattr(completed, "stderr_captured_bytes", 0)),
            "stdout_total_bytes": int(getattr(completed, "stdout_total_bytes", 0)),
            "stderr_total_bytes": int(getattr(completed, "stderr_total_bytes", 0)),
        }

    def run_argv(self, argv, timeout):
        """Run one program inside the isolation without a shell.

        The harness's own check.py invocation takes this path, so the grader
        runs under exactly the isolation the model ran under, and sees exactly
        the sandbox the model left behind.
        """
        return self.isolation.spawn(self.root, list(argv), timeout)


# The three sandbox tool definitions, identical in every condition so that the
# only thing that varies across arms is the system prompt and the affordances
# (methods 4.3).
SANDBOX_TOOLS = [
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file from the working directory. Give a path relative to the working directory.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path relative to the working directory."}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "kind": "sandbox",
    },
    {
        "name": "write_file",
        "description": "Write a UTF-8 text file in the working directory, replacing it if it exists. Give a path relative to the working directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path relative to the working directory."},
                "content": {"type": "string", "description": "The full new contents of the file."},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        "kind": "sandbox",
    },
    {
        "name": "run_command",
        "description": "Run one shell command in the working directory and return its exit code, stdout and stderr.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "The shell command to run."}},
            "required": ["command"],
            "additionalProperties": False,
        },
        "kind": "sandbox",
    },
]


def sandbox_tools():
    import copy

    return copy.deepcopy(SANDBOX_TOOLS)
