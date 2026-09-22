# Dashboard Design (Stage 6)

Three dashboards, each built for the stakeholder group that requested it in `docs/01_business_scenario.md`. All three share the same underlying model and measures from Stage 5 — this is the payoff of building a proper star schema: one source of truth, three audiences.

---

## Dashboard 1: Executive Summary

**Audience:** CEO / Exec Committee
**Question it answers:** *Are we growing, and are we profitable?*

| Visual | Type | Measures / fields used |
|---|---|---|
| Header KPI cards (4 across the top) | Card visuals | `Total GWP`, `Loss Ratio %`, `GWP YoY Growth %`, `Renewal Rate %` |
| GWP trend | Line chart | `Total GWP` by `dim_date[month]`/`[year]`, with `GWP Prior Year` as a second line for comparison |
| GWP by product line | Clustered bar chart | `Total GWP` by `dim_product[product_line]` |
| GWP by branch/region | Bar chart or filled map (if using `dim_branch[city]`) | `Total GWP` by `dim_branch[branch_name]` |
| New business vs. renewal mix | 100% stacked bar, by year | `New Business Count`, `Renewal Count`, `Cancellation Count` |
| Cumulative GWP (YTD) | Area chart | `GWP Running Total` |

**Slicers:** Year, Product Line, Branch (top of page, applied to all visuals)

**Design notes:**
- Lead with the KPI cards — this is the page a CEO looks at for 10 seconds, so the headline numbers need zero scrolling
- Conditional formatting on the Loss Ratio card: green under 60%, amber 60–80%, red above 80% (thresholds are illustrative — set them from what the business considers acceptable)
- Keep this page to a single screen, no scrolling — that's the test of a true executive summary

---

## Dashboard 2: Claims & Underwriting Ops

**Audience:** Head of Claims, Head of Underwriting
**Question it answers:** *Where is claims risk concentrated, and what needs attention now?*

| Visual | Type | Measures / fields used |
|---|---|---|
| KPI cards | Card visuals | `Claim Count`, `Open Claim Count`, `Average Days to Settle`, `Loss Ratio %` |
| Loss ratio by branch, ranked | Bar chart sorted descending | `Loss Ratio` by `dim_branch[branch_name]`, using `Branch Loss Ratio Rank` to sort |
| Claims aging | Bar/column chart | Claim count by aging bucket (0-30/31-60/61-90/90+ days — built in Power Query or a calculated column from `fact_claims[claim_date_key]`) |
| Claim severity distribution | Donut or bar chart | Claim count by `claim_severity_band` (from the Stage 4 ETL transform) |
| Claims frequency by product | Bar chart | `Claim Frequency` by `dim_product[product_line]` |
| Open claims detail table | Table visual | `claim_id`, `status_name`, `days_open`, `claim_amount_reserved`, filterable |

**Slicers:** Product Line, Branch, Claim Status Group (Open/Closed), Date range

**Design notes:**
- This is the working dashboard, not the pretty one — the detail table matters as much as the charts, since claims staff need to act on individual records
- Use a consistent red-amber-green convention for aging buckets (0-30 green, 90+ red) — but pair color with a text label, not color alone, for accessibility (see visualization standards below)

---

## Dashboard 3: Customer Analytics

**Audience:** Marketing / Customer team
**Question it answers:** *Who are our customers, and where's the retention/cross-sell opportunity?*

| Visual | Type | Measures / fields used |
|---|---|---|
| KPI cards | Card visuals | `Renewal Rate %`, `Customers with New Business`, `Total GWP`, `Average Claim Severity` |
| Customer segment breakdown | Donut chart | GWP by `dim_customer[segment]` (Individual/SME/Corporate) |
| Renewal rate by segment | Bar chart | `Renewal Rate %` sliced by `dim_customer[segment]` |
| Customer acquisition trend | Line chart | Count of distinct new customers by `dim_customer[customer_since_date]`, by month |
| Top 20 customers by GWP | Table | `customer_name`, `segment`, `Total GWP`, `Loss Ratio` |
| Payment method mix | Bar chart | Payment count/amount by `fact_premium_payments[payment_method]` |

**Slicers:** Segment, Nationality, City, Date range

**Design notes:**
- This dashboard is the most "self-service" of the three — Marketing will want to slice by demographic attributes frequently, so slicers should be generous and clearly labeled
- The Top 20 customers table doubles as a cross-sell prospect list in a real deployment (customers with high GWP in one product line are natural targets for another)

---

## Page navigation

All three dashboards live in one `.pbix` file as separate report pages, with a simple top-of-page navigation bar (buttons or a navigator visual) so a reviewer can move between Executive / Claims Ops / Customer Analytics without hunting through page tabs.
