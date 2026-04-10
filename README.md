# pipewatch

> A lightweight CLI monitor for ETL pipeline health with alerting hooks

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/youruser/pipewatch.git && cd pipewatch && pip install -e .
```

---

## Usage

Run a health check against your pipeline configuration:

```bash
pipewatch check --config pipeline.yaml
```

Watch continuously with a polling interval and trigger alerts on failure:

```bash
pipewatch watch --config pipeline.yaml --interval 60 --alert slack
```

Example `pipeline.yaml`:

```yaml
pipelines:
  - name: daily_sales_etl
    source: postgres://localhost/sales
    target: s3://my-bucket/output/
    max_lag_minutes: 30
    alert_on_failure: true
```

Output:

```
[✓] daily_sales_etl   — healthy   (lag: 4m)
[✗] user_sync_job     — stale     (lag: 47m) → alert sent
```

### Alert Hooks

| Hook     | Flag              |
|----------|-------------------|
| Slack    | `--alert slack`   |
| PagerDuty| `--alert pagerduty` |
| Webhook  | `--alert webhook --webhook-url <url>` |

---

## License

MIT © 2024 — see [LICENSE](LICENSE) for details.