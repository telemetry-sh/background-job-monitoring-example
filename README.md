# Background Job Monitoring With Telemetry

[![CI](https://github.com/telemetry-sh/background-job-monitoring-example/actions/workflows/ci.yml/badge.svg)](https://github.com/telemetry-sh/background-job-monitoring-example/actions/workflows/ci.yml)

A small Python worker that records starts, retries, completions, failures, and
duration as structured events in
[Telemetry](https://telemetry.sh/for/background-job-monitoring?utm_source=github&utm_medium=referral&utm_campaign=example-repositories&utm_content=background-job-monitoring).

The monitor records error classes, not exception messages or job payloads.

## Run it

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
export TELEMETRY_API_KEY=your_api_key
python -m job_monitor.main
```

Create an API key in the
[Telemetry app](https://telemetry.sh/register?utm_source=github&utm_medium=referral&utm_campaign=example-repositories&utm_content=background-job-monitoring-signup).
The demo intentionally fails its first attempt, then succeeds.

## Event schema

Events are written to `job_events`:

| Field | Example |
| --- | --- |
| `event_name` | `job_completed` |
| `job_name` | `account_import` |
| `queue_name` | `imports` |
| `worker_name` | `demo-worker` |
| `attempt` | `2` |
| `retry_count` | `1` |
| `status` | `success` |
| `duration_ms` | `83` |
| `item_count` | `250` |
| `error_type` | `TimeoutError` |

## Useful queries

```sql
SELECT
  job_name,
  countIf(event_name = 'job_completed') AS completed,
  countIf(event_name = 'job_failed') AS failed,
  quantile(0.95)(duration_ms) AS p95_duration_ms
FROM job_events
GROUP BY job_name
ORDER BY failed DESC;
```

```sql
SELECT job_name, queue_name, attempt, error_type, timestamp
FROM job_events
WHERE event_name IN ('job_failed', 'job_retried')
ORDER BY timestamp DESC
LIMIT 100;
```

## Adapt it

Implement `EventSink` for your queue system and call `JobMonitor.run` around
the job handler. The monitor is intentionally independent of Celery, RQ,
Dramatiq, and cloud queue providers.

## Verify

```bash
python -m unittest discover -s tests -v
```

## License

MIT
