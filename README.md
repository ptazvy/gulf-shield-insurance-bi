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
- Report automation & pipeline monitoring

## Tech stack

| Layer | Tool |
|---|---|
| Data generation | Python (Faker, pandas) |
| Data warehouse | SQLite (portable stand-in for SQL Server / Synapse) |
| ETL | Python (pandas-based pipeline simulating Alteryx/SSIS logic) |
| Visualization | Power BI Desktop |
| Automation | Python + Power BI Service scheduled refresh |
| Version control | Git / GitHub |

## Project roadmap

- [x] **Stage 1 — Scoping & Data Model**: business scenario + star schema design
- [x] **Stage 2 — Synthetic Dataset**: realistic CSV source data (9,000 policies, 1,772 claims, 16,385 payments, 3,000 customers)
- [x] **Stage 3 — SQL Data Warehouse**: DDL + load scripts + 15 practice queries (joins, CTEs, window functions)
- [x] **Stage 4 — ETL Pipeline**: extract/validate/transform/load workflow with logging, quarantine, and data lineage
- [x] **Stage 5 — Power BI Data Model**: star schema import + full DAX measure library
- [x] **Stage 6 — Power BI Dashboards**: Executive / Claims Ops / Customer Analytics — design blueprint + visualization standards
- [x] **Stage 7 — Automation**: scheduled refresh + alert setup guide, plus a tested Python KPI alert script
- [x] **Stage 8 — Documentation & Publishing**: data lineage doc, GitHub polishing checklist, LinkedIn case study draft

All eight stages are documented and design-complete. The one remaining piece is the hands-on build: constructing the actual Power BI model and dashboards in Power BI Desktop by following the guides in `powerbi/`, then exporting the finished `.pbix` and dashboard screenshots into this repo (see `docs/05_publishing_and_linkedin.md` for the pre-publish checklist).

## Repo structure

```
insurance-bi-portfolio/
├── README.md
├── docs/
│   ├── 01_business_scenario.md
│   ├── 02_data_model.md
│   ├── 03_data_dictionary.md
│   ├── 04_data_lineage.md
│   └── 05_publishing_and_linkedin.md
├── data/               # Stage 2: generator script + CSV source files
│   ├── generate_data.py
│   └── *.csv
├── sql/                # Stage 3: DDL, warehouse loader, practice queries
│   ├── schema.sql
│   ├── load_warehouse.py
│   ├── practice_queries.sql
│   └── README.md
├── etl/                # Stage 4: E-V-T-L pipeline with logging, quarantine, lineage
│   ├── generate_raw_extracts.py
│   ├── etl_pipeline.py
│   ├── raw_extracts/
│   ├── quarantine/
│   ├── logs/
│   └── README.md
├── powerbi/             # Stage 5-6: data model setup, DAX measures, dashboard design
│   ├── 01_data_model_setup.md
│   ├── 02_dashboard_design.md
│   ├── 03_visualization_standards.md
│   ├── dax_measures.md
│   └── README.md
└── automation/           # Stage 7: scheduled refresh + KPI alert script
    ├── scheduled_refresh_setup.md
    ├── kpi_alert_check.py
    └── README.md
```

## How to use this repo (for recruiters/reviewers)

Read in this order for the full story, from requirements to published dashboard:

1. `docs/01_business_scenario.md` — the "why": a stakeholder-style business problem and requirements
2. `docs/02_data_model.md` — the star schema design (Mermaid ERD)
3. `docs/03_data_dictionary.md` — the dataset itself
4. `sql/README.md` — the data warehouse and 15 practice SQL queries
5. `etl/README.md` — the ETL pipeline, data quality rules, and quarantine system
6. `powerbi/README.md` — the semantic model, DAX measures, and dashboard designs
7. `automation/README.md` — scheduled refresh and KPI alerting
8. `docs/04_data_lineage.md` — how every number traces back to its source
9. `docs/05_publishing_and_linkedin.md` — the project write-up

## Reproducing this project end to end

```bash
# 1. Generate the synthetic source data
cd data && python3 generate_data.py && cd ..

# 2. Build and validate the SQL warehouse
cd sql && python3 load_warehouse.py && cd ..

# 3. Run the full ETL pipeline (extract -> validate -> transform -> load)
cd etl
python3 generate_raw_extracts.py
python3 etl_pipeline.py
cd ..

# 4. Run a KPI threshold check against the loaded warehouse
cd automation && python3 kpi_alert_check.py --db ../etl/gulf_shield_etl.db && cd ..

# 5. Open Power BI Desktop and follow powerbi/01_data_model_setup.md
#    and powerbi/02_dashboard_design.md to build the model and dashboards
```

Every stage is independently reproducible and seeded, so results are identical on any machine that runs this.
