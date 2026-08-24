# SQL Data Warehouse (Stage 3)

This folder builds a queryable data warehouse from the Stage 2 CSVs and contains a set of practice queries answering the business questions from `docs/01_business_scenario.md`.

## Files

| File | Purpose |
|---|---|
| `schema.sql` | DDL: creates all 9 star-schema tables with primary/foreign keys and indexes |
| `load_warehouse.py` | Builds `gulf_shield.db` (SQLite), loads all CSVs, runs referential integrity checks |
| `practice_queries.sql` | 15 queries covering joins, CTEs, window functions, subqueries, and conditional aggregation |
| `gulf_shield.db` | The built database (generated file — see note below on whether to commit it) |

## How to run it

```bash
cd sql
pip install pandas --break-system-packages   # if not already installed
python3 load_warehouse.py
```

This rebuilds `gulf_shield.db` from scratch every run (safe to re-run any time), and prints row counts plus integrity check results. All three checks should print `OK`:

```
Orphan fact_policy.customer_key: OK
Orphan fact_claims.policy_key: OK
Orphan fact_premium_payments.policy_key: OK
```

Then run any query against it, e.g.:

```bash
sqlite3 gulf_shield.db < practice_queries.sql
```

Or open `gulf_shield.db` in a GUI tool like DB Browser for SQLite to explore interactively.

## Why SQLite for a "SQL Server-style" job

SQLite was chosen purely for portability — it needs no server install, so anyone reviewing this repo can run it instantly. The DDL and queries use standard ANSI SQL (joins, CTEs, window functions, CASE logic) that ports directly to SQL Server, Synapse, or PostgreSQL with only minor syntax changes (e.g. `BOOLEAN` → `BIT`, `julianday()` → `DATEDIFF()`). The dialect choice doesn't change the SQL skills being demonstrated.

## Query index

| # | Question answered | Technique highlighted |
|---|---|---|
| Q1 | Monthly GWP trend | JOIN + GROUP BY |
| Q2 | Loss ratio by product line | CTE (pre-aggregation to avoid a grouping bug) |
| Q3 | Loss ratio by branch, ranked | CTE + `RANK()` |
| Q4 | Top agents, ranked within branch | `RANK() OVER (PARTITION BY ...)` |
| Q5 | Year-over-year GWP growth | `LAG()` |
| Q6 | Claims frequency & severity by product | Aggregation with LEFT JOIN |
| Q7 | Open claims aging | Date arithmetic + `CASE` bucketing |
| Q8 | Customer renewal rate | CTE + conditional aggregation |
| Q9 | Outstanding premium receivables | LEFT JOIN, `HAVING` |
| Q10 | Cumulative GWP (running total) | `SUM() OVER (... ROWS BETWEEN ...)` |
| Q11 | New business vs. renewal mix | Conditional aggregation (pivot-style) |
| Q12 | Payment method distribution | Window function for % of total |
| Q13 | Customer segment profitability | Multi-table JOIN |
| Q14 | Above-average agents | Subquery in `HAVING` |
| Q15 | Channel performance (in-house vs. broker) | Dimension attribute grouping |

## A note on the Q2 bug (kept visible on purpose)

While building this, an earlier version of Q2 grouped by a joined measure column instead of the true grouping key, which silently fragmented "Motor" into its two underlying products instead of rolling up to the product line. The comment in `practice_queries.sql` explains the fix. Leaving this note in is intentional — it's a common, easy-to-miss SQL mistake worth flagging in a portfolio piece rather than hiding.
