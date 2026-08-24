# Business Scenario: Gulf Shield Insurance

## Company profile

Gulf Shield Insurance is a fictional mid-size composite insurer headquartered in Riyadh, writing **Motor, Health, Property, and Life** policies across five regional branches (Riyadh, Jeddah, Dammam, Makkah, Madinah). The company sells through a mix of in-house agents and broker partners.

## The problem (stakeholder brief)

> "Leadership currently gets performance numbers from disconnected Excel exports pulled by different departments — Finance has one version of premium revenue, Operations has a different claims count, and nobody trusts the numbers in the same room. We need a single source of truth: a proper data warehouse feeding governed Power BI dashboards, so executives, underwriters, and the claims team are all looking at the same facts."
>
> — VP of Operations, Gulf Shield Insurance

## Stakeholders & their asks

| Stakeholder | What they need |
|---|---|
| **CEO / Exec Committee** | Monthly executive scorecard: Gross Written Premium (GWP), loss ratio, retention rate, growth vs. target |
| **Head of Underwriting** | Policy volume and mix by product/branch/agent, new business vs. renewals |
| **Head of Claims** | Claims frequency, severity, open vs. closed aging, loss ratio by product |
| **CFO** | Premium vs. claims payout cashflow, outstanding receivables, regulatory (SAMA) reporting inputs |
| **Marketing/Customer team** | Customer segmentation, retention/churn, cross-sell opportunity by product |

## In-scope business processes

1. **Policy issuance & renewal** — new business, renewals, cancellations
2. **Claims lifecycle** — from FNOL (First Notice of Loss) to settlement
3. **Premium collection** — payment transactions against policies
4. **Agent/branch performance** — production and quality by channel

## Out of scope (for this practice project)

- Real regulatory submission formats (SAMA/ZATCA XML schemas) — noted as a future extension, not built
- Reinsurance accounting
- Live system integrations (all data is synthetic, generated in Stage 2)

## Success criteria for the BI solution

- Dimensional data warehouse that supports fast, consistent reporting across departments
- Automated ETL from "source" extracts into the warehouse with data quality checks
- Three governed Power BI dashboards (Executive, Claims & Underwriting Ops, Customer Analytics)
- Documented data dictionary and lineage so any analyst can trust and extend the model

## Key business questions the model must answer

1. What is our Gross Written Premium and Loss Ratio by month, product, and branch?
2. Which agents/branches are driving growth vs. underperforming?
3. What is our claims frequency and average severity by product line, and how is it trending?
4. What is our customer retention rate, and which segments are most likely to churn or cross-sell?
5. How much premium revenue is outstanding vs. collected, by branch and product?

