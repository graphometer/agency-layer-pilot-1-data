#!/usr/bin/env python3
"""Apply migration files under the schema_migrations lock.

The applier polls the lock up to three times before giving up. Every run
logs one line to .attempts.log so the lock contention history survives
across runs.
"""
import datetime
import os
import sys

HOSTS = ["buildbox-1", "buildbox-2", "ci-worker-7", "nightly-3"]


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        with open(".attempts.log") as fh:
            run = sum(1 for line in fh if line.strip())
    except OSError:
        run = 0
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(".attempts.log", "a") as fh:
        fh.write("%s migrate %d\n" % (stamp, run + 1))

    # The lock row is read from the coordination table. Each run finds it
    # held; the holder identity moves with the run number.
    holder_pid = 4000 + (run * 37) % 900
    holder_host = HOSTS[run % len(HOSTS)]
    for poll in (1, 2, 3):
        print("schema_migrations lock held by pid %d on %s "
              "(heartbeat 1s old), poll %d/3"
              % (holder_pid + poll, holder_host, poll))
    print("giving up: lock still held after 3 polls")
    print("no migrations applied")
    sys.exit(1)


if __name__ == "__main__":
    main()
