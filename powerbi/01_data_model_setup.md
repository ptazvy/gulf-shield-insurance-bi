# Power BI Data Model Setup (Stage 5)

This documents how the Power BI semantic model for Gulf Shield Insurance was built, recreating the star schema from `docs/02_data_model.md` inside Power BI Desktop.

## 1. Data source

Connected directly to the CSVs in `/data` via **Get Data → Text/CSV**. In a production environment, Power BI would typically point at the data warehouse (SQL Server / Synapse — what the `/sql` and `/etl` stages of this project represent) rather than flat files, via **Get Data → SQL Server**. Importing the CSVs directly here keeps this stage self-contained and reviewable without a database server running.

## 2. Power Query transformations

Each table was checked and corrected for data types in Power Query Editor before loading:

| Column type | Power BI type |
|---|---|
| `*_key`, `*_id` (keys) | Whole Number / Text (per natural vs. surrogate key) |
| Dates (`full_date`, `policy_start_date`, etc.) | Date |
| Money fields (`gross_written_premium`, `claim_amount_paid`, etc.) | Fixed Decimal Number |
| Flags (`is_renewal`, `is_cancelled`, `is_weekend`) | True/False |

Queries were renamed to match the source table names exactly (`dim_date`, `fact_policy`, etc.) for consistency with the SQL and ETL stages.

## 3. Relationships (the star schema)

All relationships are one-to-many (dimension "one" side → fact "many" side), single-direction filtering, matching the ERD in `docs/02_data_model.md`:

- `dim_date[date_key]` → `fact_policy[policy_date_key]`
- `dim_date[date_key]` → `fact_claims[claim_date_key]`
- `dim_date[date_key]` → `fact_premium_payments[payment_date_key]`
- `dim_customer[customer_key]` → `fact_policy[customer_key]`
- `dim_product[product_key]` → `fact_policy[product_key]`
- `dim_agent[agent_key]` → `fact_policy[agent_key]`
- `dim_branch[branch_key]` → `fact_policy[branch_key]`
- `fact_policy[policy_key]` → `fact_claims[policy_key]`
- `fact_policy[policy_key]` → `fact_premium_payments[policy_key]`
- `dim_claim_status[claim_status_key]` → `fact_claims[claim_status_key]`
- Direct dimension links to `fact_claims` (customer, product, branch) — kept **active**, with the equivalent path through `fact_policy` set **inactive** to avoid ambiguous filter paths

## 4. Date table

`dim_date` is marked as the official Date Table (**Table tools → Mark as date table**, using `full_date`), which is a prerequisite for every time-intelligence DAX function (`TOTALYTD`, `SAMEPERIODLASTYEAR`, `DATEADD`, etc.) used in Stage 5's measures.

## 5. Measures table

All DAX measures live in a dedicated, empty `_Measures` table rather than attached to physical fact tables — see `dax_measures.md` in this folder for the full list, organized by category:

1. Core volume & revenue
2. Claims
3. Loss Ratio (the headline KPI)
4. Premium collection
5. Time intelligence
6. Rankings
7. Customer retention

## 6. Field list hygiene

Foreign key columns on fact tables (e.g. `fact_policy[customer_key]`) are hidden from the Fields pane after relationships are built — they're only needed by the model, not by anyone building a visual. Dimension attribute columns (`branch_name`, `product_line`, etc.) remain visible.

## What's next (Stage 6)

With the model and measures in place, Stage 6 builds the three dashboards this whole project was scoped around: an Executive Summary, a Claims & Underwriting Ops view, and a Customer Analytics view — each aimed at the stakeholder group that asked for it in `docs/01_business_scenario.md`.
