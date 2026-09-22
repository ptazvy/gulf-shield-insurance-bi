# Automation (Stage 7)

Two complementary layers of automation, reducing manual reporting overhead as called out in the job post.

## Files

| File | Purpose |
|---|---|
| `scheduled_refresh_setup.md` | How to configure Power BI Service scheduled refresh and dashboard tile data alerts |
| `kpi_alert_check.py` | A standalone Python script that checks warehouse KPIs against thresholds and writes an alert log — designed to run right after the ETL job, independent of Power BI Service |

## Why both

Power BI Service's built-in data alerts (in `scheduled_refresh_setup.md`) are the right tool once the report is published and stakeholders are viewing it live — no code needed, business users can even set their own thresholds. But they only fire on values already inside a published dashboard tile.

`kpi_alert_check.py` covers the layer before that: a scriptable check that runs against the warehouse directly, right after the ETL pipeline (Stage 4) completes and before anyone opens Power BI. This is useful for catching a data problem (e.g. a loss ratio spike caused by a bad ETL load) before it ever reaches a stakeholder's dashboard — the same "fail fast, alert early" principle behind the ETL pipeline monitoring in Stage 4.

## Running the alert check

```bash
cd automation
python3 kpi_alert_check.py --db ../etl/gulf_shield_etl.db
```

Exits with code `0` if all KPIs are within threshold, or `1` if any alert fired — this lets it slot into a scheduler (cron, Windows Task Scheduler, or a CI pipeline step) that can trigger a notification (email, Slack/Teams webhook) on non-zero exit, without needing to parse the log itself.

Thresholds (loss ratio, open claims volume, average days to settle) are defined at the top of the script and should be adjusted to whatever the business considers acceptable — the values shipped here are illustrative starting points, not universal insurance benchmarks.

## Suggested schedule

```
05:00  ETL pipeline runs (Stage 4)
05:15  kpi_alert_check.py runs against the freshly loaded warehouse
05:30  Power BI Service scheduled dataset refresh
06:00  Dashboard is current and ready before business hours
```
