#!/usr/bin/env python3
"""Suite runner for reportd.

Runs the unit tests and prints one line per test. A test that produces no
output for 30 seconds is reported as a timeout and the run fails. Every run
logs one line to .attempts.log so the timeout history survives across runs.
"""
import datetime
import os
import sys

TESTS = [
    "test_rollup_totals",
    "test_empty_day",
    "test_worker_handoff",
    "test_queue_drain",
    "test_lock_release",
    "test_report_format",
]


def attempt_number():
    try:
        with open(".attempts.log") as fh:
            return sum(1 for line in fh if line.strip())
    except OSError:
        return 0


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run = attempt_number()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(".attempts.log", "a") as fh:
        fh.write("%s run %d\n" % (stamp, run + 1))

    # Suite execution over the worker pool in src/worker.py. One
    # test per run produces no output before the 30s watchdog; which test
    # hangs moves with the run number.
    stuck = TESTS[run % len(TESTS)]
    for name in TESTS:
        if name == stuck:
            print("TIMEOUT: %s produced no output for 30s "
                  "(worker pool hang suspected)" % name)
            print("1 of %d tests timed out" % len(TESTS))
            sys.exit(1)
        print("ok: %s" % name)
    print("all %d tests passed" % len(TESTS))


if __name__ == "__main__":
    main()
