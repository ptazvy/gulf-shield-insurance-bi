# Visualization Standards (Stage 6)

The job post specifically calls out establishing "visualization best practices, including consistent branding, accessibility, and layout standards" — this document is that deliverable. Apply these rules across all three dashboards so they read as one coherent product, not three separately-styled reports.

## Color palette

| Use | Color | Hex |
|---|---|---|
| Primary brand color (headers, key visuals) | Deep teal | `#0B5563` |
| Secondary accent | Sand/gold | `#C9A24B` |
| Positive/good performance | Green | `#2E7D32` |
| Warning | Amber | `#ED6C02` |
| Negative/risk | Red | `#C62828` |
| Neutral text | Charcoal | `#2B2B2B` |
| Background | Off-white | `#FAFAFA` |

Reserve red/amber/green strictly for performance-status meaning (loss ratio bands, aging buckets) — never use them decoratively elsewhere, or the color coding loses its signal value.

## Typography

- **Titles/headers:** Segoe UI Semibold, 14–16pt
- **Body/labels:** Segoe UI, 9–10pt
- **KPI card numbers:** Segoe UI Light, 28–32pt (large numbers should feel light, not bold, to avoid visual shouting)

Segoe UI is Power BI's native font and renders consistently without extra setup — no need to import custom fonts for a portfolio piece.

## Accessibility

- **Never rely on color alone** to convey meaning. Every red/amber/green indicator (loss ratio, claims aging) pairs a text label or icon alongside the color, so the dashboard remains usable for colorblind viewers.
- **Contrast:** body text stays at least 4.5:1 contrast ratio against its background (dark charcoal text on the off-white background satisfies this by default).
- **Alt text:** every visual gets a short alt-text description (Power BI: visual → Format pane → General → Alt Text) summarizing what it shows, for screen reader compatibility.
- **Tab order:** set a logical tab order on each page (Format pane → Tab Order) so keyboard navigation moves through visuals in a sensible sequence, not the order they were added.

## Layout standards

- **Consistent grid:** all three dashboards use the same page canvas size (1280×720, standard 16:9) and align KPI cards to the same top strip across pages
- **Consistent slicer placement:** slicers always live in the same position (left rail or top bar — pick one and use it everywhere)
- **White space:** don't fill every pixel — a 16px gutter between visuals keeps the page readable rather than cluttered
- **One dominant visual per page:** each dashboard has one "hero" visual (Executive: the GWP trend line; Claims Ops: the branch loss ratio ranking; Customer: the segment breakdown) sized larger than the rest, so a viewer's eye knows where to look first

## Self-service enablement

- Every measure has a clear, business-friendly name (no `Measure_1` or raw column references) and a description set in the Model view, so a business user hovering over a field understands what it means without asking
- A bookmark is set for each dashboard's "default" filter state (all time, all branches), so users can always reset back to a clean view with one click
- Tooltips are enabled on every chart showing the underlying numbers, not just the visual, for users who want the precise figure

## Report automation standard

- Scheduled refresh (Stage 7) is configured for early morning (before business hours) so numbers are current by the time stakeholders open the report, without a mid-day refresh disrupting anyone mid-analysis
