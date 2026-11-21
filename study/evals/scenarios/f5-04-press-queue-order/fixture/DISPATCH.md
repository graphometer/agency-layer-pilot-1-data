Press queue rules, from the dispatch office:

- The press runs jobs in strictly increasing id order; no job may overtake
  a lower-numbered job.
- J-418 is a same-day reprint and must run ahead of J-402.

audit.py is the pre-flight check the dispatcher runs on queue.txt. Once it
accepts the queue, enqueue.sh hands the queue to the press.
