-- =============================================================================
-- Gulf Shield Insurance - Practice SQL Queries
-- Stage 3 of the BI Analyst portfolio project
--
-- Each query answers one of the business questions from
-- docs/01_business_scenario.md. Written for SQLite; dialect notes are
-- included where SQL Server / Synapse syntax would differ.
-- Run against sql/gulf_shield.db (built by load_warehouse.py).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1. Monthly Gross Written Premium (GWP) trend
-- Business question: What is our GWP trend over time?
-- Technique: JOIN + GROUP BY + date truncation
-- -----------------------------------------------------------------------------
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(fp.gross_written_premium), 2) AS total_gwp,
    COUNT(*) AS policy_count
FROM fact_policy fp
JOIN dim_date d ON fp.policy_date_key = d.date_key
WHERE fp.is_cancelled = 0
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- -----------------------------------------------------------------------------
-- Q2. Loss ratio by product line
-- Business question: Which product lines are most/least profitable?
-- Technique: CTE to pre-aggregate GWP by product_line before joining claims,
-- avoiding a classic grouping bug (grouping by a joined measure column would
-- silently fragment the result down to product_key level instead of
-- product_line level — worth knowing this trap exists).
-- -----------------------------------------------------------------------------
WITH gwp_by_line AS (
    SELECT dp.product_line, SUM(fp.gross_written_premium) AS total_gwp
    FROM fact_policy fp
    JOIN dim_product dp ON fp.product_key = dp.product_key
    WHERE fp.is_cancelled = 0
    GROUP BY dp.product_line
),
claims_by_line AS (
    SELECT dp.product_line, SUM(fc.claim_amount_paid) AS total_paid
    FROM fact_claims fc
    JOIN dim_product dp ON fc.product_key = dp.product_key
    GROUP BY dp.product_line
)
SELECT
    g.product_line,
    ROUND(g.total_gwp, 2) AS total_gwp,
    ROUND(COALESCE(c.total_paid, 0), 2) AS total_claims_paid,
    ROUND(COALESCE(c.total_paid, 0) * 1.0 / g.total_gwp, 4) AS loss_ratio
FROM gwp_by_line g
LEFT JOIN claims_by_line c ON g.product_line = c.product_line
ORDER BY loss_ratio DESC;


-- -----------------------------------------------------------------------------
-- Q3. Loss ratio by branch, ranked
-- Business question: Which branches are underperforming on claims experience?
-- Technique: CTE + window function RANK()
-- -----------------------------------------------------------------------------
WITH branch_gwp AS (
    SELECT db.branch_key, db.branch_name, SUM(fp.gross_written_premium) AS gwp
    FROM fact_policy fp
    JOIN dim_branch db ON fp.branch_key = db.branch_key
    WHERE fp.is_cancelled = 0
    GROUP BY db.branch_key, db.branch_name
),
branch_claims AS (
    SELECT branch_key, SUM(claim_amount_paid) AS claims_paid
    FROM fact_claims
    GROUP BY branch_key
)
SELECT
    bg.branch_name,
    ROUND(bg.gwp, 2) AS total_gwp,
    ROUND(COALESCE(bc.claims_paid, 0), 2) AS total_claims_paid,
    ROUND(COALESCE(bc.claims_paid, 0) * 1.0 / bg.gwp, 4) AS loss_ratio,
    RANK() OVER (ORDER BY COALESCE(bc.claims_paid, 0) * 1.0 / bg.gwp DESC) AS loss_ratio_rank
FROM branch_gwp bg
LEFT JOIN branch_claims bc ON bg.branch_key = bc.branch_key
ORDER BY loss_ratio_rank;


-- -----------------------------------------------------------------------------
-- Q4. Top 10 agents by GWP, with their rank within their own branch
-- Business question: Who are our top-performing agents, and how do they
-- compare to peers at the same branch?
-- Technique: window function PARTITION BY + ORDER BY
-- -----------------------------------------------------------------------------
SELECT *
FROM (
    SELECT
        da.agent_name,
        db.branch_name,
        ROUND(SUM(fp.gross_written_premium), 2) AS agent_gwp,
        RANK() OVER (PARTITION BY db.branch_name ORDER BY SUM(fp.gross_written_premium) DESC) AS rank_in_branch
    FROM fact_policy fp
    JOIN dim_agent da ON fp.agent_key = da.agent_key
    JOIN dim_branch db ON da.branch_id = db.branch_id
    WHERE fp.is_cancelled = 0
    GROUP BY da.agent_name, db.branch_name
) ranked
ORDER BY agent_gwp DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- Q5. Year-over-year GWP growth
-- Business question: Are we growing vs. last year?
-- Technique: window function LAG()
-- -----------------------------------------------------------------------------
WITH yearly_gwp AS (
    SELECT d.year, SUM(fp.gross_written_premium) AS total_gwp
    FROM fact_policy fp
    JOIN dim_date d ON fp.policy_date_key = d.date_key
    WHERE fp.is_cancelled = 0
    GROUP BY d.year
)
SELECT
    year,
    ROUND(total_gwp, 2) AS total_gwp,
    ROUND(LAG(total_gwp) OVER (ORDER BY year), 2) AS prior_year_gwp,
    ROUND(
        (total_gwp - LAG(total_gwp) OVER (ORDER BY year)) * 100.0
        / LAG(total_gwp) OVER (ORDER BY year), 1
    ) AS yoy_growth_pct
FROM yearly_gwp
ORDER BY year;


-- -----------------------------------------------------------------------------
-- Q6. Claims frequency and average severity by product
-- Business question: Which products generate the most/costliest claims?
-- Technique: two-level aggregation via subquery
-- -----------------------------------------------------------------------------
SELECT
    dp.product_line,
    COUNT(DISTINCT fp.policy_key) AS policies_written,
    COUNT(fc.claim_key) AS claims_count,
    ROUND(COUNT(fc.claim_key) * 1.0 / COUNT(DISTINCT fp.policy_key), 3) AS claim_frequency,
    ROUND(AVG(fc.claim_amount_paid), 2) AS avg_claim_severity
FROM fact_policy fp
JOIN dim_product dp ON fp.product_key = dp.product_key
LEFT JOIN fact_claims fc ON fp.policy_key = fc.policy_key
WHERE fp.is_cancelled = 0
GROUP BY dp.product_line
ORDER BY claim_frequency DESC;


-- -----------------------------------------------------------------------------
-- Q7. Open claims aging (how long claims have been sitting open)
-- Business question: Which open claims need urgent attention?
-- Technique: date arithmetic against current date, CASE-based bucketing
-- -----------------------------------------------------------------------------
SELECT
    fc.claim_id,
    dcs.status_name,
    d.full_date AS claim_opened_date,
    CAST(julianday('now') - julianday(d.full_date) AS INTEGER) AS days_open,
    CASE
        WHEN CAST(julianday('now') - julianday(d.full_date) AS INTEGER) <= 30 THEN '0-30 days'
        WHEN CAST(julianday('now') - julianday(d.full_date) AS INTEGER) <= 60 THEN '31-60 days'
        WHEN CAST(julianday('now') - julianday(d.full_date) AS INTEGER) <= 90 THEN '61-90 days'
        ELSE '90+ days'
    END AS aging_bucket
FROM fact_claims fc
JOIN dim_claim_status dcs ON fc.claim_status_key = dcs.claim_status_key
JOIN dim_date d ON fc.claim_date_key = d.date_key
WHERE dcs.status_group = 'Open'
ORDER BY days_open DESC;


-- -----------------------------------------------------------------------------
-- Q8. Customer renewal rate (retention)
-- Business question: What % of customers who had a policy also renewed it?
-- Technique: CTE + conditional aggregation
-- -----------------------------------------------------------------------------
WITH customer_policy_types AS (
    SELECT
        customer_key,
        SUM(CASE WHEN policy_type = 'New Business' THEN 1 ELSE 0 END) AS new_business_count,
        SUM(CASE WHEN policy_type = 'Renewal' THEN 1 ELSE 0 END) AS renewal_count
    FROM fact_policy
    GROUP BY customer_key
)
SELECT
    COUNT(*) AS customers_with_new_business,
    SUM(CASE WHEN renewal_count > 0 THEN 1 ELSE 0 END) AS customers_who_renewed,
    ROUND(
        SUM(CASE WHEN renewal_count > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
    ) AS renewal_rate_pct
FROM customer_policy_types
WHERE new_business_count > 0;


-- -----------------------------------------------------------------------------
-- Q9. Outstanding premium receivables by policy
-- Business question: How much premium revenue is billed but not yet collected?
-- Technique: LEFT JOIN + aggregation to compare GWP vs. payments received
-- -----------------------------------------------------------------------------
SELECT
    fp.policy_id,
    dc.customer_name,
    ROUND(fp.gross_written_premium, 2) AS gwp,
    ROUND(COALESCE(SUM(pay.payment_amount), 0), 2) AS total_collected,
    ROUND(fp.gross_written_premium - COALESCE(SUM(pay.payment_amount), 0), 2) AS outstanding_balance
FROM fact_policy fp
JOIN dim_customer dc ON fp.customer_key = dc.customer_key
LEFT JOIN fact_premium_payments pay ON fp.policy_key = pay.policy_key
WHERE fp.is_cancelled = 0
GROUP BY fp.policy_id, dc.customer_name, fp.gross_written_premium
HAVING outstanding_balance > 0
ORDER BY outstanding_balance DESC
LIMIT 20;


-- -----------------------------------------------------------------------------
-- Q10. Running total (cumulative) GWP by month
-- Business question: What does our cumulative revenue curve look like YTD?
-- Technique: window function SUM() OVER with a frame clause
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT d.year, d.month, SUM(fp.gross_written_premium) AS monthly_gwp
    FROM fact_policy fp
    JOIN dim_date d ON fp.policy_date_key = d.date_key
    WHERE fp.is_cancelled = 0
    GROUP BY d.year, d.month
)
SELECT
    year, month,
    ROUND(monthly_gwp, 2) AS monthly_gwp,
    ROUND(SUM(monthly_gwp) OVER (
        PARTITION BY year ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total_gwp_ytd
FROM monthly
ORDER BY year, month;


-- -----------------------------------------------------------------------------
-- Q11. New business vs. renewal mix trend by year
-- Business question: Is our book growing from new business or just renewals?
-- Technique: conditional aggregation, pivot-style
-- -----------------------------------------------------------------------------
SELECT
    d.year,
    SUM(CASE WHEN fp.policy_type = 'New Business' THEN 1 ELSE 0 END) AS new_business_count,
    SUM(CASE WHEN fp.policy_type = 'Renewal' THEN 1 ELSE 0 END) AS renewal_count,
    SUM(CASE WHEN fp.policy_type = 'Cancellation' THEN 1 ELSE 0 END) AS cancellation_count,
    ROUND(
        SUM(CASE WHEN fp.policy_type = 'New Business' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
    ) AS new_business_pct
FROM fact_policy fp
JOIN dim_date d ON fp.policy_date_key = d.date_key
GROUP BY d.year
ORDER BY d.year;


-- -----------------------------------------------------------------------------
-- Q12. Payment method distribution
-- Business question: How are customers paying us?
-- Technique: simple aggregation, share-of-total calc
-- -----------------------------------------------------------------------------
SELECT
    payment_method,
    COUNT(*) AS payment_count,
    ROUND(SUM(payment_amount), 2) AS total_collected,
    ROUND(SUM(payment_amount) * 100.0 / SUM(SUM(payment_amount)) OVER (), 1) AS pct_of_total
FROM fact_premium_payments
GROUP BY payment_method
ORDER BY total_collected DESC;


-- -----------------------------------------------------------------------------
-- Q13. Customer segment profitability
-- Business question: Are Individual, SME, or Corporate customers most valuable?
-- Technique: multi-table JOIN with LEFT JOIN for claims
-- -----------------------------------------------------------------------------
SELECT
    dc.segment,
    COUNT(DISTINCT fp.customer_key) AS customer_count,
    ROUND(SUM(fp.gross_written_premium), 2) AS total_gwp,
    ROUND(SUM(fp.gross_written_premium) / COUNT(DISTINCT fp.customer_key), 2) AS avg_gwp_per_customer,
    ROUND(COALESCE(SUM(fc.claim_amount_paid), 0) * 1.0 / SUM(fp.gross_written_premium), 4) AS loss_ratio
FROM fact_policy fp
JOIN dim_customer dc ON fp.customer_key = dc.customer_key
LEFT JOIN fact_claims fc ON fp.policy_key = fc.policy_key
WHERE fp.is_cancelled = 0
GROUP BY dc.segment
ORDER BY total_gwp DESC;


-- -----------------------------------------------------------------------------
-- Q14. Agents with above-average GWP (subquery in WHERE clause)
-- Business question: Which agents are outperforming the average?
-- Technique: correlated-style subquery for a dynamic benchmark
-- -----------------------------------------------------------------------------
SELECT
    da.agent_name,
    db.branch_name,
    ROUND(SUM(fp.gross_written_premium), 2) AS agent_gwp
FROM fact_policy fp
JOIN dim_agent da ON fp.agent_key = da.agent_key
JOIN dim_branch db ON da.branch_id = db.branch_id
WHERE fp.is_cancelled = 0
GROUP BY da.agent_name, db.branch_name
HAVING SUM(fp.gross_written_premium) > (
    SELECT AVG(agent_total) FROM (
        SELECT SUM(gross_written_premium) AS agent_total
        FROM fact_policy
        WHERE is_cancelled = 0
        GROUP BY agent_key
    )
)
ORDER BY agent_gwp DESC;


-- -----------------------------------------------------------------------------
-- Q15. Channel performance: In-house vs. Broker
-- Business question: Is our in-house sales force or broker channel more efficient?
-- Technique: JOIN + GROUP BY on a dimension attribute (channel), with loss ratio
-- -----------------------------------------------------------------------------
SELECT
    da.channel,
    COUNT(DISTINCT fp.policy_key) AS policy_count,
    ROUND(SUM(fp.gross_written_premium), 2) AS total_gwp,
    ROUND(COALESCE(SUM(fc.claim_amount_paid), 0) * 1.0 / SUM(fp.gross_written_premium), 4) AS loss_ratio
FROM fact_policy fp
JOIN dim_agent da ON fp.agent_key = da.agent_key
LEFT JOIN fact_claims fc ON fp.policy_key = fc.policy_key
WHERE fp.is_cancelled = 0
GROUP BY da.channel
ORDER BY total_gwp DESC;
