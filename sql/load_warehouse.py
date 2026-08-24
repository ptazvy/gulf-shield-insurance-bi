"""
Gulf Shield Insurance - Warehouse Loader
Stage 3 of the BI Analyst portfolio project.

Builds gulf_shield.db (SQLite) by:
  1. Executing schema.sql to create the star schema with keys/indexes
  2. Loading each CSV from ../data into its matching table
  3. Running row-count and referential integrity checks

Run from inside the /sql folder:  python3 load_warehouse.py
"""

import sqlite3
import pandas as pd
import os

SQL_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SQL_DIR, "..", "data")
DB_PATH = os.path.join(SQL_DIR, "gulf_shield.db")

TABLE_LOAD_ORDER = [
    # dimensions first (fact tables have FK references to these)
    "dim_date", "dim_branch", "dim_product", "dim_agent",
    "dim_customer", "dim_claim_status",
    # then facts, in FK dependency order
    "fact_policy", "fact_claims", "fact_premium_payments",
]

BOOLEAN_COLUMNS = {
    "dim_date": ["is_weekend"],
    "fact_policy": ["is_renewal", "is_cancelled"],
}


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # rebuild clean each run

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(os.path.join(SQL_DIR, "schema.sql")) as f:
        cur.executescript(f.read())
    conn.commit()
    print("Schema created.")

    for table in TABLE_LOAD_ORDER:
        csv_path = os.path.join(DATA_DIR, f"{table}.csv")
        df = pd.read_csv(csv_path)

        for col in BOOLEAN_COLUMNS.get(table, []):
            df[col] = df[col].astype(bool).astype(int)  # SQLite has no native BOOLEAN

        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"  Loaded {table}: {len(df):,} rows")

    conn.commit()

    # ---- Basic referential integrity checks ----
    print("\nIntegrity checks:")
    checks = {
        "Orphan fact_policy.customer_key": """
            SELECT COUNT(*) FROM fact_policy fp
            LEFT JOIN dim_customer dc ON fp.customer_key = dc.customer_key
            WHERE dc.customer_key IS NULL""",
        "Orphan fact_claims.policy_key": """
            SELECT COUNT(*) FROM fact_claims fc
            LEFT JOIN fact_policy fp ON fc.policy_key = fp.policy_key
            WHERE fp.policy_key IS NULL""",
        "Orphan fact_premium_payments.policy_key": """
            SELECT COUNT(*) FROM fact_premium_payments pp
            LEFT JOIN fact_policy fp ON pp.policy_key = fp.policy_key
            WHERE fp.policy_key IS NULL""",
    }
    all_clean = True
    for label, query in checks.items():
        result = cur.execute(query).fetchone()[0]
        status = "OK" if result == 0 else f"FAIL ({result} orphans)"
        if result != 0:
            all_clean = False
        print(f"  {label}: {status}")

    print(f"\n{'All integrity checks passed.' if all_clean else 'Integrity issues found — investigate before building on top of this warehouse.'}")
    print(f"Database ready at: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
