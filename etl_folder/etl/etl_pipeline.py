"""
Gulf Shield Insurance - ETL Pipeline
Stage 4 of the BI Analyst portfolio project.

Simulates what an Alteryx workflow or SSIS package would do in production:

  EXTRACT   -> read raw source files (etl/raw_extracts/)
  VALIDATE  -> apply data quality rules; split each table into
               clean rows (proceed) vs. rejected rows (quarantine)
  TRANSFORM -> business logic: standardize text, derive fields,
               add data lineage columns
  LOAD      -> write clean, transformed data into a fresh warehouse
               (etl/gulf_shield_etl.db), built from sql/schema.sql

Every step is logged to etl/logs/, and every rejected row is written to
etl/quarantine/ with a reason code, so a reviewer can see exactly what was
caught and why — the same way a real ETL job's error output would look.

Run:  python3 etl_pipeline.py
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "raw_extracts")
QUARANTINE_DIR = os.path.join(BASE_DIR, "quarantine")
LOG_DIR = os.path.join(BASE_DIR, "logs")
SQL_DIR = os.path.join(BASE_DIR, "..", "sql")
DB_PATH = os.path.join(BASE_DIR, "gulf_shield_etl.db")

os.makedirs(QUARANTINE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

RUN_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
LOAD_TIMESTAMP = datetime.now().isoformat(timespec="seconds")

# -----------------------------------------------------------------------------
# Logging setup — mirrors what an ETL job's monitoring output looks like
# -----------------------------------------------------------------------------
logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)
logger.handlers.clear()

file_handler = logging.FileHandler(os.path.join(LOG_DIR, f"etl_run_{RUN_TS}.log"))
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_step(step, table, message):
    logger.info(f"[{step}] {table}: {message}")


# =============================================================================
# EXTRACT
# =============================================================================
def extract():
    logger.info("=" * 70)
    logger.info("STAGE: EXTRACT")
    logger.info("=" * 70)
    tables = {}
    for name in ["dim_date", "dim_branch", "dim_product", "dim_agent",
                 "dim_customer", "dim_claim_status",
                 "fact_policy", "fact_claims", "fact_premium_payments"]:
        path = os.path.join(RAW_DIR, f"{name}.csv")
        df = pd.read_csv(path)
        tables[name] = df
        log_step("EXTRACT", name, f"{len(df):,} rows read from {path}")
    return tables


# =============================================================================
# VALIDATE — returns (clean_df, rejected_df_with_reason)
# =============================================================================
def quarantine(table_name, rejected):
    if len(rejected) > 0:
        out_path = os.path.join(QUARANTINE_DIR, f"{table_name}_rejects.csv")
        rejected.to_csv(out_path, index=False)
        log_step("VALIDATE", table_name,
                  f"{len(rejected)} row(s) quarantined -> {out_path}")


def validate_dim_customer(df):
    df = df.copy()
    reasons = pd.Series([None] * len(df), index=df.index)

    dupe_mask = df.duplicated(subset="customer_id", keep="first")
    reasons[dupe_mask] = "duplicate customer_id"

    rejected = df[reasons.notna()].copy()
    rejected["reject_reason"] = reasons[reasons.notna()]
    clean = df[reasons.isna()].copy()

    log_step("VALIDATE", "dim_customer",
              f"{len(clean)} passed, {len(rejected)} rejected (duplicate customer_id)")
    quarantine("dim_customer", rejected)
    return clean


def validate_fact_policy(df, valid_customer_keys):
    df = df.copy()
    reasons = pd.Series([None] * len(df), index=df.index)

    reasons[df.duplicated(subset="policy_id", keep="first")] = "duplicate policy_id"
    reasons[reasons.isna() & (df["gross_written_premium"] < 0)] = "negative gross_written_premium"
    reasons[reasons.isna() & (~df["customer_key"].isin(valid_customer_keys))] = "orphaned customer_key"
    reasons[reasons.isna() & (pd.to_datetime(df["policy_start_date"]) >
                               pd.to_datetime(df["policy_end_date"]))] = "policy_start_date after policy_end_date"

    rejected = df[reasons.notna()].copy()
    rejected["reject_reason"] = reasons[reasons.notna()]
    clean = df[reasons.isna()].copy()

    log_step("VALIDATE", "fact_policy",
              f"{len(clean)} passed, {len(rejected)} rejected")
    quarantine("fact_policy", rejected)
    return clean


def validate_fact_claims(df, valid_policy_keys):
    df = df.copy()
    reasons = pd.Series([None] * len(df), index=df.index)

    reasons[~df["policy_key"].isin(valid_policy_keys)] = "orphaned policy_key"
    reasons[reasons.isna() & (df["claim_amount_paid"] < 0)] = "negative claim_amount_paid"
    reasons[reasons.isna() & (df["claim_amount_paid"] > df["claim_amount_reserved"] * 1.5)] = \
        "claim_amount_paid grossly exceeds claim_amount_reserved"

    rejected = df[reasons.notna()].copy()
    rejected["reject_reason"] = reasons[reasons.notna()]
    clean = df[reasons.isna()].copy()

    log_step("VALIDATE", "fact_claims",
              f"{len(clean)} passed, {len(rejected)} rejected")
    quarantine("fact_claims", rejected)
    return clean


def validate_fact_premium_payments(df, valid_policy_keys):
    df = df.copy()
    reasons = pd.Series([None] * len(df), index=df.index)

    reasons[df["payment_amount"] <= 0] = "zero or negative payment_amount"
    reasons[reasons.isna() & (~df["policy_key"].isin(valid_policy_keys))] = "orphaned policy_key"

    rejected = df[reasons.notna()].copy()
    rejected["reject_reason"] = reasons[reasons.notna()]
    clean = df[reasons.isna()].copy()

    # blank payment_method is a WARNING, not a hard reject — it's fixable in
    # TRANSFORM rather than something to throw away
    blank_count = clean["payment_method"].isna().sum()
    if blank_count:
        log_step("VALIDATE", "fact_premium_payments",
                  f"WARNING: {blank_count} row(s) have a blank payment_method "
                  f"— will be defaulted in TRANSFORM, not rejected")

    log_step("VALIDATE", "fact_premium_payments",
              f"{len(clean)} passed, {len(rejected)} rejected")
    quarantine("fact_premium_payments", rejected)
    return clean


def validate(tables):
    logger.info("=" * 70)
    logger.info("STAGE: VALIDATE")
    logger.info("=" * 70)

    tables["dim_customer"] = validate_dim_customer(tables["dim_customer"])
    valid_customer_keys = set(tables["dim_customer"]["customer_key"])

    tables["fact_policy"] = validate_fact_policy(tables["fact_policy"], valid_customer_keys)
    valid_policy_keys = set(tables["fact_policy"]["policy_key"])

    tables["fact_claims"] = validate_fact_claims(tables["fact_claims"], valid_policy_keys)
    tables["fact_premium_payments"] = validate_fact_premium_payments(
        tables["fact_premium_payments"], valid_policy_keys)

    return tables


# =============================================================================
# TRANSFORM
# =============================================================================
def transform(tables):
    logger.info("=" * 70)
    logger.info("STAGE: TRANSFORM")
    logger.info("=" * 70)

    # --- dim_customer: standardize text, make nulls BI-friendly ---
    dc = tables["dim_customer"]
    dc["customer_name"] = dc["customer_name"].str.strip().str.title()
    dc["city"] = dc["city"].str.strip().str.title()
    dc["gender"] = dc["gender"].fillna("Not Applicable")
    dc["age_band"] = dc["age_band"].fillna("Not Applicable")
    tables["dim_customer"] = dc
    log_step("TRANSFORM", "dim_customer",
              "standardized name/city casing; filled gender/age_band nulls with 'Not Applicable'")

    # --- fact_premium_payments: default blank payment_method ---
    fpay = tables["fact_premium_payments"]
    blank_count = fpay["payment_method"].isna().sum()
    fpay["payment_method"] = fpay["payment_method"].fillna("Unknown")
    tables["fact_premium_payments"] = fpay
    log_step("TRANSFORM", "fact_premium_payments",
              f"defaulted {blank_count} blank payment_method value(s) to 'Unknown'")

    # --- fact_claims: derive claim_severity_band ---
    fc = tables["fact_claims"]
    fc["claim_severity_band"] = pd.cut(
        fc["claim_amount_paid"],
        bins=[-0.01, 5000, 20000, 50000, float("inf")],
        labels=["Low (<=5K)", "Medium (5K-20K)", "High (20K-50K)", "Severe (>50K)"],
    )
    tables["fact_claims"] = fc
    log_step("TRANSFORM", "fact_claims", "derived claim_severity_band from claim_amount_paid")

    # --- fact_policy: derive is_short_rated flag for cancelled policies ---
    fp = tables["fact_policy"]
    fp["is_short_rated"] = fp["is_cancelled"].astype(bool)
    tables["fact_policy"] = fp
    log_step("TRANSFORM", "fact_policy", "derived is_short_rated flag from is_cancelled")

    # --- data lineage: stamp every fact table with load metadata ---
    for name in ["fact_policy", "fact_claims", "fact_premium_payments"]:
        tables[name]["etl_load_timestamp"] = LOAD_TIMESTAMP
        tables[name]["source_system"] = "GULF_SHIELD_CORE_v1"
    log_step("TRANSFORM", "all fact tables",
              "stamped etl_load_timestamp and source_system for data lineage")

    return tables


# =============================================================================
# LOAD
# =============================================================================
def load(tables):
    logger.info("=" * 70)
    logger.info("STAGE: LOAD")
    logger.info("=" * 70)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(os.path.join(SQL_DIR, "schema.sql")) as f:
        schema_sql = f.read()

    # the ETL-loaded warehouse adds lineage/derived columns beyond schema.sql,
    # so extend the fact tables with those columns after creating the base schema
    cur.executescript(schema_sql)
    cur.execute("ALTER TABLE fact_policy ADD COLUMN is_short_rated BOOLEAN")
    cur.execute("ALTER TABLE fact_policy ADD COLUMN etl_load_timestamp TEXT")
    cur.execute("ALTER TABLE fact_policy ADD COLUMN source_system TEXT")
    cur.execute("ALTER TABLE fact_claims ADD COLUMN claim_severity_band TEXT")
    cur.execute("ALTER TABLE fact_claims ADD COLUMN etl_load_timestamp TEXT")
    cur.execute("ALTER TABLE fact_claims ADD COLUMN source_system TEXT")
    cur.execute("ALTER TABLE fact_premium_payments ADD COLUMN etl_load_timestamp TEXT")
    cur.execute("ALTER TABLE fact_premium_payments ADD COLUMN source_system TEXT")
    conn.commit()

    load_order = ["dim_date", "dim_branch", "dim_product", "dim_agent",
                  "dim_customer", "dim_claim_status",
                  "fact_policy", "fact_claims", "fact_premium_payments"]

    bool_cols = {
        "dim_date": ["is_weekend"],
        "fact_policy": ["is_renewal", "is_cancelled", "is_short_rated"],
    }

    for name in load_order:
        df = tables[name].copy()
        for col in bool_cols.get(name, []):
            df[col] = df[col].astype(bool).astype(int)
        if "claim_severity_band" in df.columns:
            df["claim_severity_band"] = df["claim_severity_band"].astype(str)
        df.to_sql(name, conn, if_exists="append", index=False)
        log_step("LOAD", name, f"{len(df):,} rows loaded into {os.path.basename(DB_PATH)}")

    conn.commit()
    conn.close()
    logger.info(f"Load complete. Warehouse: {DB_PATH}")


# =============================================================================
# SUMMARY REPORT
# =============================================================================
def write_summary(extracted, final):
    rows = []
    for name in extracted:
        rows.append({
            "table": name,
            "rows_extracted": len(extracted[name]),
            "rows_loaded": len(final[name]),
            "rows_rejected": len(extracted[name]) - len(final[name]),
        })
    summary_df = pd.DataFrame(rows)
    summary_path = os.path.join(LOG_DIR, f"etl_summary_{RUN_TS}.csv")
    summary_df.to_csv(summary_path, index=False)

    logger.info("=" * 70)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 70)
    for _, r in summary_df.iterrows():
        logger.info(f"  {r['table']:<26} extracted={r['rows_extracted']:>6} "
                     f"loaded={r['rows_loaded']:>6}  rejected={r['rows_rejected']:>4}")
    logger.info(f"Summary written to {summary_path}")
    return summary_df


# =============================================================================
def main():
    start = datetime.now()
    logger.info(f"ETL PIPELINE RUN STARTED — {start.isoformat(timespec='seconds')}")

    extracted = extract()
    extracted_counts = {k: v.copy() for k, v in extracted.items()}  # snapshot for summary

    validated = validate(extracted)
    transformed = transform(validated)
    load(transformed)
    write_summary(extracted_counts, transformed)

    duration = (datetime.now() - start).total_seconds()
    logger.info(f"ETL PIPELINE RUN COMPLETE — duration: {duration:.1f}s")


if __name__ == "__main__":
    main()
