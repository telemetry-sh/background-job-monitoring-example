import os

from telemetry_sh import Telemetry

from .monitor import JobContext, JobMonitor


class TelemetrySink:
    def __init__(self, api_key: str) -> None:
        self.client = Telemetry()
        self.client.init(api_key)

    def emit(self, event: dict) -> None:
        self.client.log("job_events", event)


def main() -> None:
    api_key = os.environ.get("TELEMETRY_API_KEY")
    if not api_key:
        raise RuntimeError("Set TELEMETRY_API_KEY before running the example.")

    attempts = 0

    def import_accounts() -> int:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("simulated provider timeout")
        return 250

    monitor = JobMonitor(TelemetrySink(api_key))
    count = monitor.run(
        JobContext(
            job_name="account_import",
            queue_name="imports",
            worker_name="demo-worker",
        ),
        import_accounts,
    )
    print(f"Imported {count} accounts")


if __name__ == "__main__":
    main()
