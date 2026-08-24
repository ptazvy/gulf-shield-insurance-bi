# Gulf Shield Insurance — BI Analyst Portfolio Project

An end-to-end Business Intelligence portfolio project built to demonstrate the skills required for a **Business Intelligence Analyst (Insurance/Financial Services)** role: dimensional data warehousing, ETL pipelines, advanced SQL, and Power BI dashboard development.

This project simulates the BI function for **Gulf Shield Insurance**, a fictional mid-size insurer operating in Riyadh, Saudi Arabia, offering Motor, Health, Property, and Life products.

## Why this project exists

This repo was built stage-by-stage to practice, in order, every core competency listed in a real BI Analyst job posting:
- Data visualization & dashboard development (Power BI)
- Data warehousing & dimensional modeling (star schema)
- ETL / data integration
- Advanced SQL
- Data governance & documentation
- Stakeholder-style requirements gathering

## Tech stack

| Layer | Tool |
|---|---|
| Data generation | Python (Faker, pandas) |
| Data warehouse | SQLite (portable stand-in for SQL Server / Synapse) |
| ETL | Python (pandas-based pipeline simulating Alteryx/SSIS logic) |
| Visualization | Power BI Desktop |
| Version control | Git / GitHub |

## Project roadmap

- [x] **Stage 1 — Scoping & Data Model**: business scenario + star schema design
- [x] **Stage 2 — Synthetic Dataset**: realistic CSV source data (9,000 policies, 1,772 claims, 16,385 payments, 3,000 customers)
- [x] **Stage 3 — SQL Data Warehouse**: DDL + load scripts + 15 practice queries (joins, CTEs, window functions)
- [ ] **Stage 4 — ETL Pipeline**: extract/validate/transform/load workflow
- [ ] **Stage 5 — Power BI Data Model**: star schema import + DAX measures
- [ ] **Stage 6 — Power BI Dashboards**: Executive / Claims Ops / Customer Analytics
- [ ] **Stage 7 — Automation**: scheduled refresh + alert logic
- [ ] **Stage 8 — Documentation & Publishing**: data dictionary, lineage, case study

## Repo structure (grows each stage)

```
insurance-bi-portfolio/
├── README.md
├── docs/
│   ├── 01_business_scenario.md
│   ├── 02_data_model.md
│   └── 03_data_dictionary.md
├── data/              # Stage 2: generator script + CSV source files
│   ├── generate_data.py
│   └── *.csv
├── sql/               # Stage 3: DDL, warehouse loader, practice queries
│   ├── schema.sql
│   ├── load_warehouse.py
│   ├── practice_queries.sql
│   └── README.md
├── etl/               (added Stage 4)
└── powerbi/           (added Stage 5-6)
```

## How to use this repo (for recruiters/reviewers)

Start with `docs/01_business_scenario.md` for the "why", then `docs/02_data_model.md` for the data architecture, `docs/03_data_dictionary.md` for the dataset itself, then `sql/README.md` for the warehouse and query set, then follow the numbered folders in order — the project is designed to read like a real BI delivery, from requirements to published dashboard.
