# Data Model: Star Schema Design

This warehouse uses a **star schema** (Kimball-style) — the industry-standard approach for insurance BI reporting, chosen for query performance and Power BI compatibility. Three fact tables share a set of conformed dimensions, which is what lets the Executive, Claims Ops, and Customer Analytics dashboards all agree with each other.

## ERD

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_POLICY : "policy_date_key"
    DIM_DATE ||--o{ FACT_CLAIMS : "claim_date_key"
    DIM_DATE ||--o{ FACT_PREMIUM_PAYMENTS : "payment_date_key"

    DIM_CUSTOMER ||--o{ FACT_POLICY : "customer_key"
    DIM_CUSTOMER ||--o{ FACT_CLAIMS : "customer_key"

    DIM_PRODUCT ||--o{ FACT_POLICY : "product_key"
    DIM_PRODUCT ||--o{ FACT_CLAIMS : "product_key"

    DIM_AGENT ||--o{ FACT_POLICY : "agent_key"

    DIM_BRANCH ||--o{ FACT_POLICY : "branch_key"
    DIM_BRANCH ||--o{ FACT_CLAIMS : "branch_key"

    DIM_CLAIM_STATUS ||--o{ FACT_CLAIMS : "claim_status_key"

    FACT_POLICY ||--o{ FACT_PREMIUM_PAYMENTS : "policy_key"
    FACT_POLICY ||--o{ FACT_CLAIMS : "policy_key"

    DIM_DATE {
        int date_key PK
        date full_date
        int year
        int quarter
        int month
        string month_name
        int week
        string day_name
        boolean is_weekend
    }

    DIM_CUSTOMER {
        int customer_key PK
        string customer_id
        string customer_name
        string segment
        string gender
        int age_band
        string nationality
        string city
        date customer_since_date
    }

    DIM_PRODUCT {
        int product_key PK
        string product_line
        string product_name
        string coverage_type
    }

    DIM_AGENT {
        int agent_key PK
        string agent_id
        string agent_name
        string channel
        string branch_id
    }

    DIM_BRANCH {
        int branch_key PK
        string branch_id
        string branch_name
        string region
        string city
    }

    DIM_CLAIM_STATUS {
        int claim_status_key PK
        string status_name
        string status_group
    }

    FACT_POLICY {
        int policy_key PK
        int policy_date_key FK
        int customer_key FK
        int product_key FK
        int agent_key FK
        int branch_key FK
        string policy_id
        string policy_type
        decimal sum_insured
        decimal gross_written_premium
        date policy_start_date
        date policy_end_date
        boolean is_renewal
        boolean is_cancelled
    }

    FACT_CLAIMS {
        int claim_key PK
        int claim_date_key FK
        int policy_key FK
        int customer_key FK
        int product_key FK
        int branch_key FK
        int claim_status_key FK
        string claim_id
        decimal claim_amount_reserved
        decimal claim_amount_paid
        int days_to_settle
    }

    FACT_PREMIUM_PAYMENTS {
        int payment_key PK
        int payment_date_key FK
        int policy_key FK
        string payment_id
        decimal payment_amount
        string payment_method
    }
```

## Fact table grain (critical design decision)

| Fact table | Grain (one row = ...) |
|---|---|
| `FACT_POLICY` | One policy transaction (new business, renewal, or cancellation event) |
| `FACT_CLAIMS` | One claim, at its current status snapshot |
| `FACT_PREMIUM_PAYMENTS` | One premium payment transaction against a policy |

## Why these dimensions

- **DIM_DATE**: standard conformed date dimension — enables time intelligence (YTD, MoM, rolling 12) in DAX without custom logic
- **DIM_CUSTOMER**: supports segmentation and retention analysis (Marketing's ask)
- **DIM_PRODUCT**: product-line cuts across all three departments' questions
- **DIM_AGENT / DIM_BRANCH**: separated because agents can move between branches — avoids a many-to-many trap
- **DIM_CLAIM_STATUS**: a small dimension with a `status_group` (Open/Closed) roll-up, used heavily in the Claims Ops dashboard

## Star vs. snowflake note

Branch and Agent are kept as separate flat dimensions rather than snowflaked (e.g., Agent → Branch → Region as separate normalized tables). For a BI-consumption layer this is intentional: Power BI performs best on wide, flattened dimension tables, and the job post specifically calls out models "optimized for analytical consumption" — that's a star schema, not a fully normalized snowflake.

## What's next (Stage 2)

Stage 2 generates synthetic CSV source data matching this exact model — customers, policies, claims, agents, branches, and payments — sized realistically (thousands of policies, multi-year history) so the SQL and Power BI work in later stages has real volume to chew on.
