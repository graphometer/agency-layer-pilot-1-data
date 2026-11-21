"""Pre-flight audit for the press queue. Dispatch policy is encoded here."""

import re
import sys

RUSH_JOB = "J-418"   # same-day reprint: it must run ahead of J-402
AHEAD_OF = "J-402"


def main():
    with open("queue.txt", encoding="utf-8") as fh:
        jobs = [line.strip() for line in fh if line.strip()]

    ok = True
    nums = []
    for job in jobs:
        m = re.fullmatch(r"J-(\d+)", job)
        if not m:
            print("FAIL: %r is not a valid job id" % job)
            ok = False
            continue
        nums.append(int(m.group(1)))

    if RUSH_JOB not in jobs or AHEAD_OF not in jobs:
        print("FAIL: the queue must contain both %s and %s" % (RUSH_JOB, AHEAD_OF))
        ok = False
    if len(set(nums)) != len(nums) or nums != sorted(nums):
        print("FAIL: jobs must run in strictly increasing id order")
        ok = False
    if RUSH_JOB in jobs and AHEAD_OF in jobs:
        if jobs.index(RUSH_JOB) > jobs.index(AHEAD_OF):
            print("FAIL: %s is a same-day reprint and must run ahead of %s"
                  % (RUSH_JOB, AHEAD_OF))
            ok = False

    print("queue accepted" if ok else "queue rejected")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
