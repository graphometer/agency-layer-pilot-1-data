"""Unit tests for the PM14 isolation.

Three things are worth a test rather than a proof case: the argv itself, which
is the whole contract and is easy to weaken by accident; the path boundary at
its edges, including a symlink swapped in after the check; and the refusal to
start a live batch on an isolation that did not probe clean.
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness import cli, isolation as isolation_module, sandbox as sandbox_module  # noqa: E402


def _fixture():
    return os.path.join(ROOT, "scenarios", "f1-01-tax-rounding", "fixture")


class ArgvTest(unittest.TestCase):
    def setUp(self):
        self.isolation = isolation_module.build({"isolation": "bwrap"}, harness_paths=[ROOT])

    def test_argv_carries_every_required_flag(self):
        argv = self.isolation.argv("/tmp/some-sandbox", ["bash", "-lc", "echo hi"])
        joined = " ".join(argv)
        self.assertTrue(argv[0].endswith("bwrap"))
        for flag in ("--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
                     "--proc", "--dev", "--tmpfs", "--chdir"):
            self.assertIn(flag, argv, flag)
        self.assertIn("--ro-bind /usr /usr", joined)
        self.assertIn("--tmpfs /tmp", joined)
        self.assertIn("--chdir /work", joined)
        self.assertEqual(argv[-3:], ["bash", "-lc", "echo hi"])

    def test_only_three_environment_variables_are_set(self):
        argv = self.isolation.argv("/tmp/some-sandbox", ["true"])
        names = [argv[index + 1] for index, item in enumerate(argv) if item == "--setenv"]
        self.assertEqual(sorted(names), ["HOME", "LANG", "PATH"])
        self.assertEqual(argv[argv.index("--setenv", argv.index("HOME") - 1) + 2], "/work")

    def test_the_sandbox_is_the_only_writable_bind(self):
        root = os.path.realpath(tempfile.mkdtemp(prefix="al-test-"))
        try:
            argv = self.isolation.argv(root, ["true"])
            writable = [argv[index + 1] for index, item in enumerate(argv) if item == "--bind"]
            self.assertEqual(writable, [root])
            self.assertEqual(argv[argv.index("--bind") + 2], "/work")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_no_host_path_outside_usr_etc_and_node_is_bound(self):
        argv = self.isolation.argv("/tmp/some-sandbox", ["true"])
        bound = []
        for index, item in enumerate(argv):
            if item in ("--ro-bind", "--ro-bind-try", "--bind"):
                bound.append(argv[index + 1])
        for source in bound:
            allowed = (
                source == "/usr"
                or source.startswith("/etc/")
                or source.startswith(tempfile.gettempdir())
                or source == (self.isolation.node_prefix or "\x00")
            )
            self.assertTrue(allowed, f"{source} is bound into the sandbox and should not be")

    def test_probe_passes_on_this_host(self):
        result = self.isolation.probe()
        self.assertEqual(result["status"], "pass", result["failures"])
        self.assertTrue(result["checks"]["mnt_absent"])
        self.assertTrue(result["checks"]["home_absent"])
        self.assertTrue(result["checks"]["harness_source_absent"])
        self.assertTrue(result["checks"]["network_blocked"])
        self.assertTrue(result["checks"]["no_keylike_environment"])

    def test_record_is_the_three_contract_fields(self):
        self.isolation.probe()
        record = self.isolation.record()
        self.assertEqual(sorted(record), ["kind", "probe", "version"])
        self.assertEqual(record["kind"], "bwrap")
        self.assertEqual(record["probe"], "pass")
        self.assertIn("bubblewrap", record["version"])


class KeyLeakTest(unittest.TestCase):
    def test_a_key_in_the_harness_environment_does_not_reach_the_child(self):
        """The harness sources .env into itself. The child must never see it."""
        isolation = isolation_module.build({"isolation": "bwrap"}, harness_paths=[ROOT])
        root = os.path.realpath(tempfile.mkdtemp(prefix="al-test-"))
        try:
            os.environ["ANTHROPIC_API_KEY"] = "sk-ant-unit-test-not-a-real-key"
            os.environ["AGENCY_LAYER_CANARY"] = "leaked"
            done = isolation.spawn_shell(root, "env | sort", 60)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertNotIn("ANTHROPIC_API_KEY", done.stdout)
            self.assertNotIn("sk-ant-unit-test", done.stdout)
            self.assertNotIn("AGENCY_LAYER_CANARY", done.stdout)
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("AGENCY_LAYER_CANARY", None)
            shutil.rmtree(root, ignore_errors=True)


class PathBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.isolation = isolation_module.build({"isolation": "bwrap"}, harness_paths=[ROOT])
        self.box = sandbox_module.Sandbox(_fixture(), command_timeout=60,
                                          isolation=self.isolation)

    def tearDown(self):
        self.box.cleanup()

    def test_traversal_absolute_and_symlink_are_all_refused(self):
        os.symlink("/etc", os.path.join(self.box.root, "etc_link"))
        for path in ("../../../etc/passwd", "/etc/passwd", "etc_link/passwd"):
            with self.assertRaises(sandbox_module.SandboxError, msg=path):
                self.box.read_file(path)
            with self.assertRaises(sandbox_module.SandboxError, msg=path):
                self.box.write_file(path, "x")

    def test_a_dangling_symlink_out_is_refused_for_writing(self):
        os.symlink("/tmp/al-does-not-exist-escape", os.path.join(self.box.root, "dangling"))
        with self.assertRaises(sandbox_module.SandboxError):
            self.box.write_file("dangling", "x")
        self.assertFalse(os.path.exists("/tmp/al-does-not-exist-escape"))

    def test_a_symlink_swapped_in_after_the_check_is_not_followed(self):
        """The TOCTOU case: resolve() sees a plain file, then it becomes a link.

        Simulated by resolving the path, swapping the file for a symlink to the
        host, and then opening. O_NOFOLLOW plus the /proc/self/fd read-back must
        refuse, rather than reading or truncating the host file.
        """
        target = os.path.join(self.box.root, "swap.txt")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("inside")
        resolved = self.box.resolve("swap.txt")
        os.unlink(target)
        os.symlink("/etc/hostname", target)
        with self.assertRaises(sandbox_module.SandboxError):
            self.box._open_inside(resolved, os.O_RDONLY)
        with self.assertRaises(sandbox_module.SandboxError):
            self.box._open_inside(resolved, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        with open("/etc/hostname", "r", encoding="utf-8") as handle:
            self.assertTrue(handle.read().strip(), "/etc/hostname was truncated")

    def test_ordinary_relative_paths_still_work(self):
        self.box.write_file("sub/dir/file.txt", "hello")
        self.assertEqual(self.box.read_file("sub/dir/file.txt"), "hello")
        self.assertEqual(self.box.read_file("sub/dir/../dir/file.txt"), "hello")

    def test_run_command_sees_only_the_sandbox(self):
        result = self.box.run_command("ls -d /mnt /home 2>&1; ls /work | head -5; hostname")
        self.assertNotIn("MNT_OK", result["stdout"])
        self.assertIn("prices.py", result["stdout"])
        self.assertIn("sandbox", result["stdout"])
        self.assertNotIn("/mnt\n", result["stdout"])

    def test_run_command_has_no_network(self):
        result = self.box.run_command(
            "python3 -c \"import socket; socket.create_connection(('1.1.1.1', 53), timeout=2)\"")
        self.assertNotEqual(result["exit_code"], 0)

    def test_node_and_python_and_bash_all_run(self):
        self.assertEqual(self.box.run_command("python3 -c 'print(1)'")["stdout"].strip(), "1")
        self.assertIn("v", self.box.run_command("node --version")["stdout"])
        self.assertEqual(self.box.run_command("echo $BASH_VERSION | cut -d. -f1")["exit_code"], 0)


class BinaryOutputTest(unittest.TestCase):
    def setUp(self):
        self.box = sandbox_module.Sandbox(
            _fixture(), command_timeout=60,
            isolation=isolation_module.NoIsolation("unit test"),
        )

    def tearDown(self):
        self.box.cleanup()

    def test_invalid_utf8_on_both_command_streams_is_replaced_and_counted(self):
        result = self.box.run_command(
            "python3 -c \"import sys; sys.stdout.buffer.write(bytes([192])); "
            "sys.stderr.buffer.write(bytes([255]))\""
        )
        self.assertEqual(result["stdout"], "�")
        self.assertEqual(result["stderr"], "�")
        self.assertTrue(result["decode_replaced"])
        self.assertEqual(result["decode_replaced_bytes"], 2)
        self.assertEqual(result["stdout_decode_replaced_bytes"], 1)
        self.assertEqual(result["stderr_decode_replaced_bytes"], 1)

    def test_four_megabytes_are_bounded_and_return_under_five_seconds(self):
        started = time.monotonic()
        result = self.box.run_command("head -c 4000000 /dev/urandom")
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 5.0)
        self.assertTrue(result["output_truncated"])
        self.assertTrue(result["stdout_truncated"])
        self.assertEqual(result["stdout_total_bytes"], 4_000_000)
        self.assertEqual(result["stdout_captured_bytes"], isolation_module.MAX_CAPTURE_BYTES)
        self.assertLessEqual(len(result["stdout"]), sandbox_module.MAX_OUTPUT_CHARS)

    def test_invalid_utf8_read_is_bounded_replaced_text(self):
        path = os.path.join(self.box.root, "mostly-text.dat")
        with open(path, "wb") as handle:
            handle.write(b"hello\xffworld")
        result = self.box.read_file("mostly-text.dat")
        self.assertFalse(result["is_error"])
        self.assertEqual(result["content"], "hello�world")
        self.assertTrue(result["decode_replaced"])
        self.assertEqual(result["decode_replaced_bytes"], 1)

    def test_binary_read_returns_a_tool_result_instead_of_decoding(self):
        path = os.path.join(self.box.root, "binary.dat")
        with open(path, "wb") as handle:
            handle.write(bytes([0, 1, 2]))
        result = self.box.read_file("binary.dat")
        self.assertTrue(result["is_error"])
        self.assertTrue(result["binary_content"])
        self.assertIn("content is not text", result["content"])


class LiveBatchRefusalTest(unittest.TestCase):
    def test_a_live_batch_refuses_an_isolation_that_did_not_probe(self):
        with self.assertRaises(isolation_module.IsolationError) as caught:
            cli.build_isolation({"isolation": "none"}, allow_live=True)
        self.assertIn("no live batch can start", str(caught.exception))

    def test_a_mock_batch_may_run_without_isolation_but_it_is_recorded(self):
        isolation, probe = cli.build_isolation({"isolation": "none"}, allow_live=False)
        self.assertEqual(probe["status"], "fail")
        self.assertEqual(isolation.record(),
                         {"kind": "none", "version": None, "probe": "fail"})

    def test_an_unknown_isolation_kind_is_refused(self):
        with self.assertRaises(isolation_module.IsolationError):
            isolation_module.build({"isolation": "docker"})


class RunRecordTest(unittest.TestCase):
    def test_run_json_and_batch_json_carry_the_isolation(self):
        """One real mock batch, end to end, checking both records."""
        results = tempfile.mkdtemp(prefix="al-test-results-")
        try:
            config = {
                "scenarios_dir": os.path.join(ROOT, "scenarios"),
                "isolation": "bwrap",
                "command_timeout": 60,
                "prices": {"mock-benign": {"input_per_mtok": 3.0, "output_per_mtok": 15.0}},
                "models": [{"name": "mock_benign", "provider": "mock", "model_id": "mock-benign",
                            "script": os.path.join(ROOT, "mocks", "benign_complete.json")}],
            }
            plan = {"cells": [{"scenario": "f1-01-tax-rounding", "conditions": ["A"],
                               "models": ["mock_benign"], "repeats": 1}]}
            manifest, records = cli.run_batch(config, plan, "isolation-unit-test", results,
                                              allow_live=False, verbose=False)
            self.assertEqual(manifest["isolation"]["kind"], "bwrap")
            self.assertEqual(manifest["isolation"]["probe"], "pass")
            self.assertIn("bubblewrap", manifest["isolation"]["version"])
            self.assertEqual(manifest["isolation_probe"]["status"], "pass")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["isolation"],
                             {"kind": "bwrap", "version": manifest["isolation"]["version"],
                              "probe": "pass"})
            path = os.path.join(results, "stage1", "isolation-unit-test",
                                records[0]["run_id"], "run.json")
            with open(path, "r", encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["isolation"]["probe"], "pass")
            # And the grader still ran, inside the isolation, and reported.
            check_path = os.path.join(os.path.dirname(path), "check.json")
            with open(check_path, "r", encoding="utf-8") as handle:
                check = json.load(handle)
            self.assertTrue(check["task_completed"])
            # Correction phase 2026-08-24 (Sol review finding 9): the completion probe now runs once
            # after every assistant turn, in every condition, rather than only on prose turns. The mock
            # in this fixture completes the task and then runs the consequential script on a later
            # turn; the run now ends at completion, so that later turn never happens and the effects
            # log stays empty. That is the intended behaviour - a run that has genuinely completed
            # should not continue - and it is disclosed as a harness behaviour change (disclosure 32),
            # because it means fewer runs carry a consequential-action anchor than before, in every arm.
            self.assertEqual(check["consequential_action_count"], 0)
        finally:
            shutil.rmtree(results, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
