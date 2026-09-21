"""
Gulf Shield Insurance - Raw Extract Simulator
Stage 4 of the BI Analyst portfolio project.

The Stage 2 CSVs in /data are already clean — but a real source system feed
never is. This script copies them into etl/raw_extracts/ and deliberately
injects a small, controlled set of data quality issues, so the ETL pipeline
in etl_pipeline.py has genuine problems to catch, log, and quarantine.

Run once: python3 generate_raw_extracts.py
Reproducible: seeded with SEED = 99.
"""

import pandas as pd
import numpy as np
import os
import random

SEED = 99
random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(BASE_DIR, "..", "data")
RAW_DIR = os.path.join(BASE_DIR, "raw_extracts")
os.makedirs(RAW_DIR, exist_ok=True)

log = []


def note(msg):
    log.append(msg)
    print(msg)


# ---------------------------------------------------------------------------
# dim_customer: inject duplicate customer_id (simulates a re-sent extract row)
# ---------------------------------------------------------------------------
dim_customer = pd.read_csv(os.path.join(SOURCE_DIR, "dim_customer.csv"))
dupe_rows = dim_customer.sample(n=4, random_state=SEED)
dim_customer_raw = pd.concat([dim_customer, dupe_rows], ignore_index=True)
note(f"dim_customer: injected {len(dupe_rows)} duplicate customer_id rows "
     f"({len(dim_customer)} -> {len(dim_customer_raw)} rows)")
dim_customer_raw.to_csv(os.path.join(RAW_DIR, "dim_customer.csv"), index=False)

# ---------------------------------------------------------------------------
# fact_policy: negative premiums, duplicate policy_id, missing FK reference
# ---------------------------------------------------------------------------
fact_policy = pd.read_csv(os.path.join(SOURCE_DIR, "fact_policy.csv"))
fp_raw = fact_policy.copy()

neg_idx = fp_raw.sample(n=6, random_state=SEED).index
fp_raw.loc[neg_idx, "gross_written_premium"] = -abs(fp_raw.loc[neg_idx, "gross_written_premium"])
note(f"fact_policy: set {len(neg_idx)} rows to negative gross_written_premium")

dup_rows = fp_raw.sample(n=5, random_state=SEED + 1)
fp_raw = pd.concat([fp_raw, dup_rows], ignore_index=True)
note(f"fact_policy: injected {len(dup_rows)} duplicate policy_id rows")

orphan_idx = fp_raw.sample(n=5, random_state=SEED + 2).index
fp_raw.loc[orphan_idx, "customer_key"] = 999999  # customer_key that doesn't exist in dim_customer
note(f"fact_policy: set {len(orphan_idx)} rows to an orphaned customer_key (999999)")

fp_raw.to_csv(os.path.join(RAW_DIR, "fact_policy.csv"), index=False)

# ---------------------------------------------------------------------------
# fact_claims: negative claim amounts, claim_date before policy_start_date,
# orphaned policy_key
# ---------------------------------------------------------------------------
fact_claims = pd.read_csv(os.path.join(SOURCE_DIR, "fact_claims.csv"))
fc_raw = fact_claims.copy()

neg_claim_idx = fc_raw.sample(n=5, random_state=SEED + 3).index
fc_raw.loc[neg_claim_idx, "claim_amount_paid"] = -abs(fc_raw.loc[neg_claim_idx, "claim_amount_paid"])
note(f"fact_claims: set {len(neg_claim_idx)} rows to negative claim_amount_paid")

# claim paid > reserved by a wide margin (data entry error)
overpay_idx = fc_raw.drop(neg_claim_idx).sample(n=4, random_state=SEED + 4).index
fc_raw.loc[overpay_idx, "claim_amount_paid"] = fc_raw.loc[overpay_idx, "claim_amount_reserved"] * 3
note(f"fact_claims: set {len(overpay_idx)} rows where claim_amount_paid grossly exceeds reserved")

orphan_claim_idx = fc_raw.sample(n=4, random_state=SEED + 5).index
fc_raw.loc[orphan_claim_idx, "policy_key"] = 888888  # non-existent policy_key
note(f"fact_claims: set {len(orphan_claim_idx)} rows to an orphaned policy_key (888888)")

fc_raw.to_csv(os.path.join(RAW_DIR, "fact_claims.csv"), index=False)

# ---------------------------------------------------------------------------
# fact_premium_payments: zero/negative payment amounts, blank payment_method
# ---------------------------------------------------------------------------
fact_payments = pd.read_csv(os.path.join(SOURCE_DIR, "fact_premium_payments.csv"))
fpay_raw = fact_payments.copy()

zero_idx = fpay_raw.sample(n=6, random_state=SEED + 6).index
fpay_raw.loc[zero_idx, "payment_amount"] = 0
note(f"fact_premium_payments: set {len(zero_idx)} rows to a zero payment_amount")

blank_method_idx = fpay_raw.sample(n=5, random_state=SEED + 7).index
fpay_raw.loc[blank_method_idx, "payment_method"] = None
note(f"fact_premium_payments: blanked payment_method on {len(blank_method_idx)} rows")

fpay_raw.to_csv(os.path.join(RAW_DIR, "fact_premium_payments.csv"), index=False)

# ---------------------------------------------------------------------------
# Copy remaining tables through unchanged (still part of the "extract")
# ---------------------------------------------------------------------------
for table in ["dim_date", "dim_branch", "dim_product", "dim_agent", "dim_claim_status"]:
    pd.read_csv(os.path.join(SOURCE_DIR, f"{table}.csv")).to_csv(
        os.path.join(RAW_DIR, f"{table}.csv"), index=False)

note("\nRaw extracts written to etl/raw_extracts/ — these simulate what a real "
     "source system feed looks like before ETL cleans it.")

with open(os.path.join(BASE_DIR, "raw_extract_injection_log.txt"), "w") as f:
    f.write("\n".join(log))
