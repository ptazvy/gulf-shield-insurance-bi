"""
Gulf Shield Insurance - Synthetic Data Generator
Stage 2 of the BI Analyst portfolio project.

Generates CSV source files matching the star schema defined in
docs/02_data_model.md:
  Dimensions: dim_date, dim_customer, dim_product, dim_agent,
              dim_branch, dim_claim_status
  Facts:      fact_policy, fact_claims, fact_premium_payments

Run:  python3 generate_data.py
Output: ./data/*.csv  (copy this folder into the repo's data/ directory)

Reproducible: seeded with SEED = 42, so re-running produces identical data.
"""

import numpy as np
import pandas as pd
from faker import Faker
from datetime import date, timedelta
import random

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUT_DIR = "data"
import os
os.makedirs(OUT_DIR, exist_ok=True)

DATA_START = date(2022, 1, 1)
DATA_END = date(2026, 8, 24)  # "today" for this project

# ---------------------------------------------------------------------------
# DIM_DATE
# ---------------------------------------------------------------------------
def build_dim_date(start, end):
    days = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({"full_date": days})
    df["date_key"] = df["full_date"].dt.strftime("%Y%m%d").astype(int)
    df["year"] = df["full_date"].dt.year
    df["quarter"] = df["full_date"].dt.quarter
    df["month"] = df["full_date"].dt.month
    df["month_name"] = df["full_date"].dt.strftime("%B")
    df["week"] = df["full_date"].dt.isocalendar().week.astype(int)
    df["day_name"] = df["full_date"].dt.strftime("%A")
    df["is_weekend"] = df["full_date"].dt.dayofweek.isin([4, 5])  # Fri/Sat weekend in KSA
    return df[["date_key", "full_date", "year", "quarter", "month",
               "month_name", "week", "day_name", "is_weekend"]]

dim_date = build_dim_date(DATA_START, DATA_END)


def date_key(d):
    return int(d.strftime("%Y%m%d"))


# ---------------------------------------------------------------------------
# DIM_BRANCH
# ---------------------------------------------------------------------------
branches = [
    ("BR01", "Riyadh Main", "Central", "Riyadh"),
    ("BR02", "Jeddah Corniche", "Western", "Jeddah"),
    ("BR03", "Dammam Business Bay", "Eastern", "Dammam"),
    ("BR04", "Makkah Central", "Western", "Makkah"),
    ("BR05", "Madinah Gate", "Western", "Madinah"),
]
dim_branch = pd.DataFrame(branches, columns=["branch_id", "branch_name", "region", "city"])
dim_branch.insert(0, "branch_key", range(1, len(dim_branch) + 1))

# ---------------------------------------------------------------------------
# DIM_PRODUCT
# ---------------------------------------------------------------------------
products = [
    ("Motor", "Motor Comprehensive", "Comprehensive"),
    ("Motor", "Motor Third-Party", "Third-Party Liability"),
    ("Health", "Health Individual", "Individual"),
    ("Health", "Health Family", "Family"),
    ("Health", "Health Corporate", "Group"),
    ("Property", "Property Fire & Perils", "Fire & Allied Perils"),
    ("Property", "Property All Risks", "All Risks"),
    ("Life", "Life Term", "Term Life"),
    ("Life", "Life Whole", "Whole Life"),
]
dim_product = pd.DataFrame(products, columns=["product_line", "product_name", "coverage_type"])
dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))

# rough annual premium ranges (SAR) and claim frequency/severity by product_key
PRODUCT_PREMIUM_RANGE = {
    1: (1500, 9000), 2: (600, 2500), 3: (2000, 12000), 4: (5000, 25000),
    5: (15000, 250000), 6: (3000, 40000), 7: (5000, 80000),
    8: (1200, 15000), 9: (3000, 30000),
}
PRODUCT_CLAIM_FREQ = {1: 0.35, 2: 0.20, 3: 0.30, 4: 0.32, 5: 0.28,
                       6: 0.08, 7: 0.10, 8: 0.03, 9: 0.02}

# ---------------------------------------------------------------------------
# DIM_AGENT
# ---------------------------------------------------------------------------
N_AGENTS = 40
agent_rows = []
for i in range(1, N_AGENTS + 1):
    branch = random.choice(branches)
    agent_rows.append((
        f"AG{i:03d}",
        fake.name(),
        random.choices(["In-house", "Broker"], weights=[0.65, 0.35])[0],
        branch[0],
    ))
dim_agent = pd.DataFrame(agent_rows, columns=["agent_id", "agent_name", "channel", "branch_id"])
dim_agent.insert(0, "agent_key", range(1, len(dim_agent) + 1))

# ---------------------------------------------------------------------------
# DIM_CUSTOMER
# ---------------------------------------------------------------------------
N_CUSTOMERS = 3000
saudi_cities = ["Riyadh", "Jeddah", "Dammam", "Makkah", "Madinah", "Khobar", "Taif", "Abha", "Tabuk", "Buraidah"]
age_bands = ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]

cust_rows = []
for i in range(1, N_CUSTOMERS + 1):
    segment = random.choices(["Individual", "SME", "Corporate"], weights=[0.75, 0.18, 0.07])[0]
    gender = random.choice(["Male", "Female"]) if segment == "Individual" else None
    name = fake.name() if segment == "Individual" else fake.company()
    since = fake.date_between(start_date=date(2018, 1, 1), end_date=DATA_END)
    cust_rows.append((
        f"CUST{i:05d}", name, segment, gender,
        random.choice(age_bands) if segment == "Individual" else None,
        random.choices(["Saudi", "Non-Saudi"], weights=[0.63, 0.37])[0],
        random.choice(saudi_cities), since,
    ))
dim_customer = pd.DataFrame(cust_rows, columns=[
    "customer_id", "customer_name", "segment", "gender", "age_band",
    "nationality", "city", "customer_since_date"])
dim_customer.insert(0, "customer_key", range(1, len(dim_customer) + 1))

# ---------------------------------------------------------------------------
# DIM_CLAIM_STATUS
# ---------------------------------------------------------------------------
claim_statuses = [
    ("New", "Open"), ("In Review", "Open"), ("Approved", "Open"),
    ("Paid", "Closed"), ("Rejected", "Closed"), ("Closed", "Closed"),
]
dim_claim_status = pd.DataFrame(claim_statuses, columns=["status_name", "status_group"])
dim_claim_status.insert(0, "claim_status_key", range(1, len(dim_claim_status) + 1))

# ---------------------------------------------------------------------------
# FACT_POLICY
# ---------------------------------------------------------------------------
N_POLICIES = 9000
policy_rows = []
total_days = (DATA_END - DATA_START).days

for i in range(1, N_POLICIES + 1):
    product_key = random.choices(
        dim_product["product_key"].tolist(),
        weights=[28, 14, 12, 8, 4, 8, 5, 12, 9],  # Motor/Health skew, matches KSA market mix
    )[0]
    customer_key = random.randint(1, N_CUSTOMERS)
    agent_key = random.randint(1, N_AGENTS)
    branch_id = dim_agent.loc[dim_agent["agent_key"] == agent_key, "branch_id"].values[0]
    branch_key = dim_branch.loc[dim_branch["branch_id"] == branch_id, "branch_key"].values[0]

    # slight upward growth trend over time: bias start dates later in the range
    offset_days = int(np.random.beta(2, 1.3) * total_days)
    policy_start = DATA_START + timedelta(days=offset_days)
    policy_end = policy_start + timedelta(days=365)

    policy_type = random.choices(["New Business", "Renewal", "Cancellation"], weights=[0.42, 0.48, 0.10])[0]
    is_renewal = policy_type == "Renewal"
    is_cancelled = policy_type == "Cancellation"

    low, high = PRODUCT_PREMIUM_RANGE[product_key]
    gwp = round(np.random.uniform(low, high), 2)
    sum_insured = round(gwp * random.uniform(8, 20), 2)
    if is_cancelled:
        gwp = round(gwp * random.uniform(0.1, 0.6), 2)  # partial/short-rated premium

    policy_rows.append((
        f"POL{i:06d}", date_key(policy_start), customer_key, product_key,
        agent_key, branch_key, policy_type, sum_insured, gwp,
        policy_start, policy_end, is_renewal, is_cancelled,
    ))

fact_policy = pd.DataFrame(policy_rows, columns=[
    "policy_id", "policy_date_key", "customer_key", "product_key", "agent_key",
    "branch_key", "policy_type", "sum_insured", "gross_written_premium",
    "policy_start_date", "policy_end_date", "is_renewal", "is_cancelled"])
fact_policy.insert(0, "policy_key", range(1, len(fact_policy) + 1))

# ---------------------------------------------------------------------------
# FACT_CLAIMS
# ---------------------------------------------------------------------------
claim_rows = []
claim_counter = 1
for _, pol in fact_policy[fact_policy["is_cancelled"] == False].iterrows():
    freq = PRODUCT_CLAIM_FREQ[pol["product_key"]]
    if random.random() > freq:
        continue  # no claim on this policy

    max_claim_date = min(pol["policy_end_date"], DATA_END)
    if pol["policy_start_date"] >= max_claim_date:
        continue
    span = (max_claim_date - pol["policy_start_date"]).days
    claim_date = pol["policy_start_date"] + timedelta(days=random.randint(1, max(span, 1)))

    status_key = random.choices(
        dim_claim_status["claim_status_key"].tolist(),
        weights=[10, 12, 10, 45, 13, 10],
    )[0]
    status_group = dim_claim_status.loc[
        dim_claim_status["claim_status_key"] == status_key, "status_group"].values[0]

    severity_pct = np.random.beta(1.5, 6)  # most claims are a modest % of sum insured
    reserved = round(pol["sum_insured"] * severity_pct, 2)
    if status_group == "Closed":
        paid_ratio = 0 if dim_claim_status.loc[
            dim_claim_status["claim_status_key"] == status_key, "status_name"].values[0] == "Rejected" \
            else random.uniform(0.85, 1.0)
        paid = round(reserved * paid_ratio, 2)
        days_to_settle = random.randint(5, 120)
    else:
        paid = round(reserved * random.uniform(0, 0.3), 2)  # partial interim payment possible
        days_to_settle = None

    claim_rows.append((
        f"CLM{claim_counter:06d}", date_key(claim_date), pol["policy_key"],
        pol["customer_key"], pol["product_key"], pol["branch_key"], status_key,
        reserved, paid, days_to_settle,
    ))
    claim_counter += 1

fact_claims = pd.DataFrame(claim_rows, columns=[
    "claim_id", "claim_date_key", "policy_key", "customer_key", "product_key",
    "branch_key", "claim_status_key", "claim_amount_reserved",
    "claim_amount_paid", "days_to_settle"])
fact_claims.insert(0, "claim_key", range(1, len(fact_claims) + 1))

# ---------------------------------------------------------------------------
# FACT_PREMIUM_PAYMENTS
# ---------------------------------------------------------------------------
payment_rows = []
payment_counter = 1
payment_methods = ["Bank Transfer", "Credit Card", "SADAD", "Cash"]

for _, pol in fact_policy.iterrows():
    if pol["gross_written_premium"] <= 0:
        continue
    n_installments = random.choices([1, 2, 4], weights=[0.55, 0.25, 0.20])[0]
    amounts = np.round(np.diff([0] + sorted(
        np.random.uniform(0, pol["gross_written_premium"], n_installments - 1)) +
        [pol["gross_written_premium"]]), 2) if n_installments > 1 else [pol["gross_written_premium"]]

    for k, amt in enumerate(amounts):
        pay_date = pol["policy_start_date"] + timedelta(days=k * 30 + random.randint(0, 5))
        if pay_date > DATA_END:
            continue
        payment_rows.append((
            f"PAY{payment_counter:06d}", date_key(pay_date), pol["policy_key"],
            round(float(amt), 2), random.choice(payment_methods),
        ))
        payment_counter += 1

fact_premium_payments = pd.DataFrame(payment_rows, columns=[
    "payment_id", "payment_date_key", "policy_key", "payment_amount", "payment_method"])
fact_premium_payments.insert(0, "payment_key", range(1, len(fact_premium_payments) + 1))

# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------
dim_date.to_csv(f"{OUT_DIR}/dim_date.csv", index=False)
dim_branch.to_csv(f"{OUT_DIR}/dim_branch.csv", index=False)
dim_product.to_csv(f"{OUT_DIR}/dim_product.csv", index=False)
dim_agent.to_csv(f"{OUT_DIR}/dim_agent.csv", index=False)
dim_customer.to_csv(f"{OUT_DIR}/dim_customer.csv", index=False)
dim_claim_status.to_csv(f"{OUT_DIR}/dim_claim_status.csv", index=False)
fact_policy.to_csv(f"{OUT_DIR}/fact_policy.csv", index=False)
fact_claims.to_csv(f"{OUT_DIR}/fact_claims.csv", index=False)
fact_premium_payments.to_csv(f"{OUT_DIR}/fact_premium_payments.csv", index=False)

print("Done. Row counts:")
for name, df in [
    ("dim_date", dim_date), ("dim_branch", dim_branch), ("dim_product", dim_product),
    ("dim_agent", dim_agent), ("dim_customer", dim_customer),
    ("dim_claim_status", dim_claim_status), ("fact_policy", fact_policy),
    ("fact_claims", fact_claims), ("fact_premium_payments", fact_premium_payments),
]:
    print(f"  {name}: {len(df):,} rows")
