# Scheduled Refresh & Alerts Setup (Stage 7)

Once the `.pbix` is published to Power BI Service, two automation features reduce manual reporting overhead: scheduled dataset refresh, and data-driven alerts on KPI tiles.

## 1. Publish to Power BI Service

1. In Power BI Desktop: **Home → Publish**, sign in with a Power BI account, choose a workspace (create one named e.g. "Gulf Shield Insurance BI" if none exists)
2. Once published, open the report in the Power BI Service (app.powerbi.com)

## 2. Configure scheduled refresh

1. In the workspace, find the dataset (not the report) → **⋯ → Settings**
2. Expand **Scheduled refresh** → toggle it **On**
3. Set refresh frequency — for this project, **Daily, once before business hours** (e.g. 5:00 AM Riyadh time) matches the visualization standard set in Stage 6
4. If the data source is local files (as in this project) rather than a cloud database, a **Personal Gateway** must be installed and running on the machine holding the source files for scheduled refresh to work unattended — flagged here since this is a common stumbling block that trips people up the first time
5. Set a **failure notification email** so a failed refresh doesn't go unnoticed — this is the "SLA monitoring" equivalent for a self-service BI deployment

## 3. Set up data alerts

Data alerts fire when a KPI on a **dashboard tile** (not a report visual directly — the KPI card needs to be pinned to a Power BI dashboard first) crosses a threshold:

1. Pin the Loss Ratio KPI card from the Executive dashboard to a Power BI dashboard (hover the visual → pin icon)
2. On the pinned tile, click **⋯ → Manage alerts → Add alert rule**
3. Example rule: *Alert me when Loss Ratio is above 80%*, checked **daily** after the scheduled refresh completes
4. Choose email notification (and optionally a Teams/Power Automate flow for a richer alert, if available)

Suggested alert rules for this project:

| Alert | Threshold | Why |
|---|---|---|
| Loss Ratio | Above 80% | Signals the book is approaching unprofitability |
| Open Claim Count | Above a set volume (e.g. 50) | Signals claims team may be falling behind |
| GWP MoM Growth % | Below 0% | Signals a revenue decline worth investigating |

## 4. Why this matters for the role

The job post specifically calls out "Report Automation: Automate scheduled reports and alerts to reduce manual reporting overhead" and "Data Pipeline Monitoring: Monitor ETL job execution, handle failures, and ensure data loads complete within defined SLAs." Scheduled refresh + failure notifications is the Power BI-side equivalent of ETL job monitoring — the same operational discipline applied to the reporting layer instead of the data layer.
