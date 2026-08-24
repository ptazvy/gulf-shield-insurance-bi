-- =============================================================================
-- Gulf Shield Insurance - Data Warehouse DDL
-- Stage 3 of the BI Analyst portfolio project
--
-- Star schema matching docs/02_data_model.md.
-- Written for SQLite (portable, zero-install) but uses standard ANSI SQL
-- types/constraints that translate directly to SQL Server / Synapse / Postgres
-- with minor syntax changes (noted in comments where relevant).
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- DIMENSION TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY,   -- YYYYMMDD
    full_date       DATE NOT NULL,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT NOT NULL,
    week            INTEGER NOT NULL,
    day_name        TEXT NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE dim_branch (
    branch_key      INTEGER PRIMARY KEY,
    branch_id       TEXT NOT NULL UNIQUE,
    branch_name     TEXT NOT NULL,
    region          TEXT NOT NULL,
    city            TEXT NOT NULL
);

CREATE TABLE dim_product (
    product_key     INTEGER PRIMARY KEY,
    product_line    TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    coverage_type   TEXT NOT NULL
);

CREATE TABLE dim_agent (
    agent_key       INTEGER PRIMARY KEY,
    agent_id        TEXT NOT NULL UNIQUE,
    agent_name      TEXT NOT NULL,
    channel         TEXT NOT NULL,
    branch_id       TEXT NOT NULL REFERENCES dim_branch(branch_id)
);

CREATE TABLE dim_customer (
    customer_key            INTEGER PRIMARY KEY,
    customer_id             TEXT NOT NULL UNIQUE,
    customer_name           TEXT NOT NULL,
    segment                 TEXT NOT NULL,
    gender                  TEXT,             -- NULL for SME/Corporate
    age_band                TEXT,             -- NULL for SME/Corporate
    nationality             TEXT NOT NULL,
    city                    TEXT NOT NULL,
    customer_since_date     DATE NOT NULL
);

CREATE TABLE dim_claim_status (
    claim_status_key    INTEGER PRIMARY KEY,
    status_name          TEXT NOT NULL,
    status_group          TEXT NOT NULL       -- Open / Closed
);

-- -----------------------------------------------------------------------------
-- FACT TABLES
-- -----------------------------------------------------------------------------

CREATE TABLE fact_policy (
    policy_key               INTEGER PRIMARY KEY,
    policy_id                TEXT NOT NULL UNIQUE,
    policy_date_key           INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key              INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key                INTEGER NOT NULL REFERENCES dim_product(product_key),
    agent_key                  INTEGER NOT NULL REFERENCES dim_agent(agent_key),
    branch_key                 INTEGER NOT NULL REFERENCES dim_branch(branch_key),
    policy_type                TEXT NOT NULL,       -- New Business / Renewal / Cancellation
    sum_insured                 DECIMAL(14,2) NOT NULL,
    gross_written_premium        DECIMAL(14,2) NOT NULL,
    policy_start_date            DATE NOT NULL,
    policy_end_date              DATE NOT NULL,
    is_renewal                   BOOLEAN NOT NULL,
    is_cancelled                 BOOLEAN NOT NULL
);

CREATE TABLE fact_claims (
    claim_key              INTEGER PRIMARY KEY,
    claim_id                 TEXT NOT NULL UNIQUE,
    claim_date_key             INTEGER NOT NULL REFERENCES dim_date(date_key),
    policy_key                  INTEGER NOT NULL REFERENCES fact_policy(policy_key),
    customer_key                 INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key                   INTEGER NOT NULL REFERENCES dim_product(product_key),
    branch_key                     INTEGER NOT NULL REFERENCES dim_branch(branch_key),
    claim_status_key                INTEGER NOT NULL REFERENCES dim_claim_status(claim_status_key),
    claim_amount_reserved             DECIMAL(14,2) NOT NULL,
    claim_amount_paid                  DECIMAL(14,2) NOT NULL,
    days_to_settle                      INTEGER          -- NULL while claim is still open
);

CREATE TABLE fact_premium_payments (
    payment_key         INTEGER PRIMARY KEY,
    payment_id            TEXT NOT NULL UNIQUE,
    payment_date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
    policy_key                INTEGER NOT NULL REFERENCES fact_policy(policy_key),
    payment_amount               DECIMAL(14,2) NOT NULL,
    payment_method                 TEXT NOT NULL
);

-- -----------------------------------------------------------------------------
-- INDEXES (beyond PK/UNIQUE) to support common reporting filters/joins
-- -----------------------------------------------------------------------------

CREATE INDEX idx_fact_policy_date        ON fact_policy(policy_date_key);
CREATE INDEX idx_fact_policy_product     ON fact_policy(product_key);
CREATE INDEX idx_fact_policy_branch      ON fact_policy(branch_key);
CREATE INDEX idx_fact_policy_customer    ON fact_policy(customer_key);

CREATE INDEX idx_fact_claims_date        ON fact_claims(claim_date_key);
CREATE INDEX idx_fact_claims_policy      ON fact_claims(policy_key);
CREATE INDEX idx_fact_claims_status      ON fact_claims(claim_status_key);

CREATE INDEX idx_fact_payments_date      ON fact_premium_payments(payment_date_key);
CREATE INDEX idx_fact_payments_policy    ON fact_premium_payments(policy_key);

-- Note on portability: in SQL Server / Synapse, DECIMAL/DATE/BOOLEAN types are
-- native; BOOLEAN would instead be BIT. Surrogate keys here are populated by
-- the ETL step, not auto-increment, mirroring how a Kimball warehouse load
-- typically assigns keys during the ETL/ELT process rather than at the DB layer.
