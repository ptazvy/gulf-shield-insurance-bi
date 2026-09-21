# Power BI (Stages 5–6)

This folder documents the Power BI layer of the project. Because a `.pbix` file is a binary Power BI Desktop format, it isn't generated here — instead, this folder contains everything needed to rebuild it exactly: the setup steps, the full DAX measure library, and (from Stage 6 onward) dashboard design notes and screenshots.

## Files

| File | Purpose |
|---|---|
| `01_data_model_setup.md` | How the star schema was recreated inside Power BI: data source, Power Query types, relationships, date table |
| `dax_measures.md` | Every DAX measure used across the dashboards, organized by category, ready to paste in |

## Recommended workflow if you're following along

1. Read `01_data_model_setup.md` and rebuild the model in Power BI Desktop using the CSVs in `/data`
2. Paste each measure from `dax_measures.md` into a `_Measures` table
3. Once Stage 6 is added, follow the dashboard build notes there for each of the three dashboards
4. Export your finished `.pbix` (or a PDF/screenshot export) and add it to this folder — a real `.pbix` file, built by you in Power BI Desktop, is what actually goes in the repo for recruiters to see

## Why no `.pbix` file is checked in yet

`.pbix` files are binary and can't be authored outside Power BI Desktop itself, so this stage produces the *blueprint* rather than the file. Once you've built the model following the guide above, exporting your own `.pbix` into this folder is the natural next step — and it's genuinely better portfolio evidence than a generated one, since it's proof you did the hands-on build yourself.
