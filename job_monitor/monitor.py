from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Protocol


class EventSink(Protocol):
    def emit(self, event: dict[str, Any]) -> None: ...


@dataclass(frozen=True)
class JobContext:
    job_name: str
    queue_name: str
    worker_name: str


class JobMonitor:
    def __init__(self, sink: EventSink) -> None:
        self.sink = sink

    def run(
        self,
        context: JobContext,
        handler: Callable[[], int],
        max_attempts: int = 3,
    ) -> int:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        for attempt in range(1, max_attempts + 1):
            started_at = perf_counter()
            self.sink.emit(self._event("job_started", context, attempt, "running"))

            try:
                item_count = handler()
            except Exception as error:
                duration_ms = round((perf_counter() - started_at) * 1000)
                error_type = type(error).__name__

                if attempt < max_attempts:
                    self.sink.emit(
                        self._event(
                            "job_retried",
                            context,
                            attempt,
                            "retrying",
                            duration_ms=duration_ms,
                            error_type=error_type,
                        )
                    )
                    continue

                self.sink.emit(
                    self._event(
                        "job_failed",
                        context,
                        attempt,
                        "failed",
                        duration_ms=duration_ms,
                        error_type=error_type,
                    )
                )
                raise

            self.sink.emit(
                self._event(
                    "job_completed",
                    context,
                    attempt,
                    "success",
                    duration_ms=round((perf_counter() - started_at) * 1000),
                    item_count=item_count,
                )
            )
            return item_count

        raise RuntimeError("job attempts exhausted")

    @staticmethod
    def _event(
        event_name: str,
        context: JobContext,
        attempt: int,
        status: str,
        **properties: Any,
    ) -> dict[str, Any]:
        return {
            "event_name": event_name,
            "job_name": context.job_name,
            "queue_name": context.queue_name,
            "worker_name": context.worker_name,
            "attempt": attempt,
            "retry_count": attempt - 1,
            "status": status,
            **properties,
        }
