# DAX Measures (Stage 5)

All measures below are written to be pasted directly into Power BI's formula bar. Create a dedicated measures table first (see setup below) and add every measure there — this is standard practice and keeps them out of your physical fact/dimension tables.

## Setup: create a `_Measures` table

In Power BI: **Home → Enter Data** → name the table `_Measures` → leave it empty (just click Load with no columns, or add one dummy column and delete it later). Then right-click `_Measures` in the Fields pane → **New Measure** for each formula below. This keeps every KPI in one place instead of scattered across fact tables.

---

## 1. Core volume & revenue measures

```dax
Total GWP =
CALCULATE(
    SUM(fact_policy[gross_written_premium]),
    fact_policy[is_cancelled] = FALSE
)
```

```dax
Policy Count =
CALCULATE(
    COUNTROWS(fact_policy),
    fact_policy[is_cancelled] = FALSE
)
```

```dax
New Business Count =
CALCULATE(
    COUNTROWS(fact_policy),
    fact_policy[policy_type] = "New Business"
)
```

```dax
Renewal Count =
CALCULATE(
    COUNTROWS(fact_policy),
    fact_policy[policy_type] = "Renewal"
)
```

```dax
Cancellation Count =
CALCULATE(
    COUNTROWS(fact_policy),
    fact_policy[policy_type] = "Cancellation"
)
```

```dax
New Business Mix % = DIVIDE([New Business Count], [Policy Count])
```

---

## 2. Claims measures

```dax
Total Claims Paid = SUM(fact_claims[claim_amount_paid])
```

```dax
Total Claims Reserved = SUM(fact_claims[claim_amount_reserved])
```

```dax
Claim Count = COUNTROWS(fact_claims)
```

```dax
Open Claim Count =
CALCULATE(
    COUNTROWS(fact_claims),
    dim_claim_status[status_group] = "Open"
)
```

```dax
Claim Frequency = DIVIDE([Claim Count], [Policy Count])
```

```dax
Average Claim Severity = DIVIDE([Total Claims Paid], [Claim Count])
```

```dax
Average Days to Settle =
CALCULATE(
    AVERAGE(fact_claims[days_to_settle]),
    NOT ISBLANK(fact_claims[days_to_settle])
)
```

---

## 3. The headline KPI: Loss Ratio

```dax
Loss Ratio = DIVIDE([Total Claims Paid], [Total GWP])
```

```dax
Loss Ratio % = FORMAT([Loss Ratio], "0.0%")
```

> Loss Ratio is the single most-watched number in insurance BI — claims paid as a share of premium earned. Below 100% means the book is profitable before expenses; this is the measure the Executive dashboard in Stage 6 will lead with.

---

## 4. Premium collection measures

```dax
Total Premium Collected = SUM(fact_premium_payments[payment_amount])
```

```dax
Outstanding Premium = [Total GWP] - [Total Premium Collected]
```

```dax
Collection Rate = DIVIDE([Total Premium Collected], [Total GWP])
```

---

## 5. Time intelligence (requires dim_date marked as Date Table)

```dax
GWP Prior Year =
CALCULATE(
    [Total GWP],
    SAMEPERIODLASTYEAR(dim_date[full_date])
)
```

```dax
GWP YoY Growth % =
DIVIDE(
    [Total GWP] - [GWP Prior Year],
    [GWP Prior Year]
)
```

```dax
GWP YTD =
TOTALYTD(
    [Total GWP],
    dim_date[full_date]
)
```

```dax
GWP Prior Month =
CALCULATE(
    [Total GWP],
    DATEADD(dim_date[full_date], -1, MONTH)
)
```

```dax
GWP MoM Growth % =
DIVIDE(
    [Total GWP] - [GWP Prior Month],
    [GWP Prior Month]
)
```

```dax
GWP Running Total =
CALCULATE(
    [Total GWP],
    FILTER(
        ALLSELECTED(dim_date[full_date]),
        dim_date[full_date] <= MAX(dim_date[full_date])
    )
)
```

---

## 6. Rankings (for agent/branch leaderboards)

```dax
Agent GWP Rank =
RANKX(
    ALL(dim_agent[agent_name]),
    [Total GWP],
    ,
    DESC
)
```

```dax
Branch Loss Ratio Rank =
RANKX(
    ALL(dim_branch[branch_name]),
    [Loss Ratio],
    ,
    DESC
)
```

> Branches are ranked DESC on Loss Ratio because a *high* loss ratio is the underperformer here — rank 1 = worst loss ratio, worth flagging on the Claims Ops dashboard.

---

## 7. Customer retention

```dax
Customers with New Business =
CALCULATE(
    DISTINCTCOUNT(fact_policy[customer_key]),
    fact_policy[policy_type] = "New Business"
)
```

```dax
Customers Who Renewed =
CALCULATE(
    DISTINCTCOUNT(fact_policy[customer_key]),
    fact_policy[policy_type] = "Renewal"
)
```

```dax
Renewal Rate % = DIVIDE([Customers Who Renewed], [Customers with New Business])
```

---

## 8. Formatting note

For any `%` measure above, set the visual/card's display format to Percentage with 1 decimal place in the Format pane, rather than baking `FORMAT()` into every measure — keeping the raw numeric value (not a formatted text string) lets Power BI sort, conditionally format, and use the measure in other calculations. Only use `FORMAT()` (like the `Loss Ratio %` example) when you specifically need the value as a text label, e.g. inside a card title.

## 9. A note on grain (avoiding a repeat of the SQL Q2 bug)

Every measure that filters `fact_policy` on `is_cancelled = FALSE` does so because `fact_policy`'s grain is *one row per policy transaction* — new business, renewal, and cancellation are separate rows, not a status flag on a single policy record. Forgetting this filter (as very nearly happened in the Stage 3 SQL work) will silently double-count or misstate GWP whenever cancellations carry a nonzero short-rated premium. Keep this filter consistent across every revenue measure.
