# ETL Pipeline (Stage 4)

A Python ETL pipeline that mirrors what an Alteryx workflow or SSIS package does in production: **Extract → Validate → Transform → Load**, with logging, quarantine of bad records, and a data lineage trail. This is deliberately built as a *separate* pipeline from Stage 3's simple loader — Stage 3 assumed clean data; this stage assumes the data arrives messy, because that's what a real source feed looks like.

## Why there's a separate "raw" dataset

The Stage 2 CSVs in `/data` are already clean, so there was nothing for a real ETL pipeline to actually clean. `generate_raw_extracts.py` solves that by copying those CSVs into `etl/raw_extracts/` and deliberately injecting a small, controlled set of realistic data problems (duplicate keys, negative amounts, orphaned foreign keys, blank fields). This is the "source system feed" the pipeline below is built to handle.

## Pipeline stages

| Stage | What it does |
|---|---|
| **Extract** | Reads all 9 raw CSVs from `raw_extracts/`, logs row counts |
| **Validate** | Applies data quality rules per table (see table below); splits each table into clean rows and rejected rows |
| **Transform** | Standardizes text casing, fills nulls with BI-friendly values, derives new analytical columns, stamps data lineage metadata |
| **Load** | Builds `gulf_shield_etl.db` from `sql/schema.sql` (extended with the new derived/lineage columns) and loads only the clean, transformed data |

Every run also writes:
- `logs/etl_run_<timestamp>.log` — full step-by-step log (extract counts, validation pass/fail, transform actions, load counts)
- `logs/etl_summary_<timestamp>.csv` — one row per table: extracted / loaded / rejected counts
- `quarantine/<table>_rejects.csv` — every rejected row, with a `reject_reason` column explaining why

## Data quality rules

| Table | Rule | Action |
|---|---|---|
| `dim_customer` | Duplicate `customer_id` | Reject (keep first occurrence) |
| `fact_policy` | Duplicate `policy_id` | Reject |
| `fact_policy` | `gross_written_premium` < 0 | Reject |
| `fact_policy` | `customer_key` not in `dim_customer` | Reject (orphaned FK) |
| `fact_policy` | `policy_start_date` after `policy_end_date` | Reject |
| `fact_claims` | `policy_key` not in cleaned `fact_policy` | Reject (orphaned FK — cascades from upstream rejects) |
| `fact_claims` | `claim_amount_paid` < 0 | Reject |
| `fact_claims` | `claim_amount_paid` > 1.5 × `claim_amount_reserved` | Reject (implausible overpayment) |
| `fact_premium_payments` | `payment_amount` <= 0 | Reject |
| `fact_premium_payments` | `policy_key` not in cleaned `fact_policy` | Reject (orphaned FK — cascades) |
| `fact_premium_payments` | Blank `payment_method` | **Warning only** — defaulted to `'Unknown'` in Transform, not rejected |

The distinction between a **reject** (data integrity is broken, can't safely load) and a **warning** (data is incomplete but usable with a sensible default) is intentional — real ETL design has to make this call constantly, and treating everything as a hard reject would throw away usable records.

## The cascade effect (worth noting)

When `fact_policy` rejects a row, any `fact_claims` or `fact_premium_payments` row pointing to that now-missing `policy_key` gets rejected too — not because that row itself was flawed, but because its parent was removed. In the last run, this accounted for 17 of the 23 rejected payment rows. This is exactly how referential integrity works in a real warehouse load, and it's why dimensions/parents must be validated *before* the facts that depend on them — reflected in the pipeline's validation order (dim_customer → fact_policy → fact_claims / fact_premium_payments).

## Transformations applied

- **Text standardization**: customer name and city cleaned to title case
- **Null handling**: `gender`/`age_band` nulls (legitimately blank for SME/Corporate customers) filled with `'Not Applicable'` rather than left blank, so Power BI visuals don't show empty categories
- **Derived field**: `claim_severity_band` (Low/Medium/High/Severe) bucketed from `claim_amount_paid`, ready for use as a dashboard filter
- **Derived field**: `is_short_rated` flag on cancelled policies
- **Data lineage**: every fact row stamped with `etl_load_timestamp` and `source_system`, so any downstream report can trace exactly when and from where a record was loaded

## How to run it

```bash
cd etl
python3 generate_raw_extracts.py   # only needed once, to (re)create the messy raw feed
python3 etl_pipeline.py            # runs the full E-V-T-L pipeline
```

Re-running `etl_pipeline.py` is safe — it rebuilds `gulf_shield_etl.db` from scratch each time.

## Last run results

| Table | Extracted | Loaded | Rejected |
|---|---|---|---|
| dim_customer | 3,004 | 3,000 | 4 |
| fact_policy | 9,005 | 8,989 | 16 |
| fact_claims | 1,772 | 1,760 | 12 |
| fact_premium_payments | 16,385 | 16,362 | 23 |

All post-load integrity checks (orphaned foreign keys, negative amounts, duplicate keys) passed at zero.
