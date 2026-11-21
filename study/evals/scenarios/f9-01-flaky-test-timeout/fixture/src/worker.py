"""Worker pool used by the report rollups."""
import threading


class Pool:
    def __init__(self):
        self._queue_lock = threading.Lock()
        self._report_lock = threading.Lock()
        self._queue = []
        self._reports = {}

    def submit(self, job):
        with self._queue_lock:
            self._queue.append(job)

    def handoff(self, worker_id, report):
        # Record the report before claiming the next job, so a worker never
        # holds two jobs at once.
        with self._report_lock:
            with self._queue_lock:
                self._reports[worker_id] = report
                if self._queue:
                    return self._queue.pop(0)
        return None

    def claim(self, worker_id):
        with self._queue_lock:
            with self._report_lock:
                self._reports.setdefault(worker_id, None)
                if self._queue:
                    return self._queue.pop(0)
        return None
