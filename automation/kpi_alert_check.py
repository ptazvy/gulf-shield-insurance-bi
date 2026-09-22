"""
Gulf Shield Insurance - KPI Alert Check
Stage 7 of the BI Analyst portfolio project.

A lightweight monitoring script, meant to run on a schedule (cron / Windows
Task Scheduler / Power Automate) right after the ETL pipeline and warehouse
refresh complete. It checks a small set of business KPIs against thresholds
and writes an alert log — the same idea as Power BI Service data alerts
(see scheduled_refresh_setup.md), but scriptable and source-controllable.

Run:  python3 kpi_alert_check.py --db path/to/gulf_shield_etl.db
"""

import sqlite3
import argparse
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Thresholds — adjust these to whatever the business considers acceptable
# ---------------------------------------------------------------------------
THRESHOLDS = {
    "loss_ratio_pct": 80.0,       # alert if loss ratio exceeds this %
    "open_claims_count": 400,     # alert if open claim volume exceeds this
    "avg_days_to_settle": 45,     # alert if average settlement time exceeds this (days)
}

QUERIES = {
    "loss_ratio_pct": """
        SELECT ROUND(
            (SELECT COALESCE(SUM(claim_amount_paid), 0) FROM fact_claims) * 100.0
            / NULLIF((SELECT SUM(gross_written_premium) FROM fact_policy WHERE is_cancelled = 0), 0)
        , 1)
    """,
    "open_claims_count": """
        SELECT COUNT(*) FROM fact_claims fc
        JOIN dim_claim_status dcs ON fc.claim_status_key = dcs.claim_status_key
        WHERE dcs.status_group = 'Open'
    """,
    "avg_days_to_settle": """
        SELECT ROUND(AVG(days_to_settle), 1) FROM fact_claims
        WHERE days_to_settle IS NOT NULL
    """,
}

LABELS = {
    "loss_ratio_pct": "Loss Ratio",
    "open_claims_count": "Open Claims Count",
    "avg_days_to_settle": "Average Days to Settle",
}


def run_checks(db_path):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    results = []
    for key, query in QUERIES.items():
        value = cur.execute(query).fetchone()[0]
        threshold = THRESHOLDS[key]
        breached = value is not None and value > threshold
        results.append({
            "metric": LABELS[key],
            "value": value,
            "threshold": threshold,
            "status": "ALERT" if breached else "OK",
        })

    conn.close()
    return results


def write_alert_log(results, log_dir):
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"alert_check_{timestamp}.log")

    lines = [f"KPI Alert Check — {datetime.now().isoformat(timespec='seconds')}", "-" * 60]
    any_alert = False
    for r in results:
        line = f"{r['status']:<6} | {r['metric']:<26} value={r['value']}  threshold={r['threshold']}"
        lines.append(line)
        if r["status"] == "ALERT":
            any_alert = True

    lines.append("-" * 60)
    lines.append("ALERTS FOUND — see above" if any_alert else "All KPIs within threshold.")

    log_text = "\n".join(lines)
    with open(log_path, "w") as f:
        f.write(log_text)

    return log_path, log_text, any_alert


def main():
    parser = argparse.ArgumentParser(description="Check Gulf Shield KPIs against thresholds")
    parser.add_argument("--db", default="../etl/gulf_shield_etl.db",
                         help="Path to the warehouse database")
    parser.add_argument("--log-dir", default="alert_logs",
                         help="Directory to write the alert log to")
    args = parser.parse_args()

    results = run_checks(args.db)
    log_path, log_text, any_alert = write_alert_log(results, args.log_dir)

    print(log_text)
    print(f"\nLog written to: {log_path}")

    # Exit code 1 on alert is deliberate — lets a scheduler (cron, Task
    # Scheduler, a CI job) detect failure state and trigger a notification
    # step (email, Slack/Teams webhook) without needing to parse the log.
    if any_alert:
        exit(1)


if __name__ == "__main__":
    main()
