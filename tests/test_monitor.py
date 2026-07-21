import unittest

from job_monitor.monitor import JobContext, JobMonitor


class MemorySink:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def emit(self, event: dict) -> None:
        self.events.append(event)


class JobMonitorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sink = MemorySink()
        self.monitor = JobMonitor(self.sink)
        self.context = JobContext("account_import", "imports", "worker-1")

    def test_records_success(self) -> None:
        result = self.monitor.run(self.context, lambda: 12)

        self.assertEqual(result, 12)
        self.assertEqual(
            [event["event_name"] for event in self.sink.events],
            ["job_started", "job_completed"],
        )
        self.assertEqual(self.sink.events[-1]["item_count"], 12)

    def test_records_retry_without_error_message(self) -> None:
        calls = 0

        def flaky_job() -> int:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TimeoutError("customer payload must not be recorded")
            return 3

        self.monitor.run(self.context, flaky_job)

        retry = self.sink.events[1]
        self.assertEqual(retry["event_name"], "job_retried")
        self.assertEqual(retry["error_type"], "TimeoutError")
        self.assertNotIn("error_message", retry)
        self.assertEqual(self.sink.events[-1]["retry_count"], 1)


if __name__ == "__main__":
    unittest.main()
