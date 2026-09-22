# Data Lineage (Stage 8)

A record of where every number on the dashboards ultimately comes from — the data governance deliverable called out in the job post ("Ensure data definitions, lineage, and cataloguing are maintained for all BI assets").

## End-to-end lineage

```
[Stage 2] Synthetic source data
   data/*.csv (9 files — dimensions + facts)
        |
        v
[Stage 4] Raw extract simulation
   etl/raw_extracts/*.csv  (adds realistic data quality issues)
        |
        v
[Stage 4] ETL Pipeline (etl_pipeline.py)
   EXTRACT  -> read raw_extracts/
   VALIDATE -> reject duplicates, orphaned FKs, negative amounts
               -> etl/quarantine/*_rejects.csv (rejected rows + reason)
   TRANSFORM -> standardize text, fill nulls, derive claim_severity_band,
                is_short_rated, stamp etl_load_timestamp + source_system
   LOAD     -> etl/gulf_shield_etl.db (the governed warehouse)
        |
        v
[Stage 5] Power BI data model
   Get Data -> gulf_shield_etl.db tables
   Relationships rebuilt as the star schema (docs/02_data_model.md)
   DAX measures (powerbi/dax_measures.md) calculated on top
        |
        v
[Stage 6] Dashboards
   Executive Summary | Claims & Underwriting Ops | Customer Analytics
```

## Table-level lineage

| Warehouse table | Source | Transformations applied |
|---|---|---|
| `dim_date` | `data/dim_date.csv` | None — passthrough |
| `dim_branch` | `data/dim_branch.csv` | None — passthrough |
| `dim_product` | `data/dim_product.csv` | None — passthrough |
| `dim_agent` | `data/dim_agent.csv` | None — passthrough |
| `dim_claim_status` | `data/dim_claim_status.csv` | None — passthrough |
| `dim_customer` | `data/dim_customer.csv` | Deduplicated on `customer_id`; name/city standardized to title case; `gender`/`age_band` nulls filled with `'Not Applicable'` |
| `fact_policy` | `data/fact_policy.csv` | Deduplicated on `policy_id`; negative premiums and orphaned `customer_key` rows rejected; `is_short_rated` derived |
| `fact_claims` | `data/fact_claims.csv` | Orphaned `policy_key` rows rejected (including cascaded rejects from `fact_policy`); negative/implausible `claim_amount_paid` rejected; `claim_severity_band` derived |
| `fact_premium_payments` | `data/fact_premium_payments.csv` | Zero/negative amounts and orphaned `policy_key` rows rejected; blank `payment_method` defaulted to `'Unknown'` |

## Measure-level lineage (a sample)

| Dashboard measure | DAX measure | Built from |
|---|---|---|
| Loss Ratio (Executive KPI card) | `Loss Ratio` | `Total Claims Paid` ÷ `Total GWP`, both aggregated from `fact_claims`/`fact_policy` |
| GWP YoY Growth % | `GWP YoY Growth %` | `Total GWP` compared to `GWP Prior Year` via `SAMEPERIODLASTYEAR` on `dim_date` |
| Claim Severity distribution | (direct field) | `fact_claims[claim_severity_band]`, derived in the Stage 4 ETL Transform step, not calculated in DAX |

The full measure list with formulas lives in `powerbi/dax_measures.md` — this document exists to show *where the inputs to those formulas come from*, not to duplicate the formulas themselves.

## Rejected data audit trail

Every row that fails validation is preserved (not silently dropped) in `etl/quarantine/`, with a `reject_reason` column. This means the warehouse's row counts are always reconcilable back to the raw extract counts — nothing simply vanishes unexplained. See `etl/README.md` for the full data quality rules table and the last run's reject counts.
