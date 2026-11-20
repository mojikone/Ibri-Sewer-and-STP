---
name: w18-growth-plot-rule
description: "W18 load placement settled 2026-11-16/17 - existing plots fixed at 2026, growth equal on future plots 200-3,000 m2, any zoning, no odd shapes, no agricultural"
metadata:
  node_type: memory
  type: project
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-17T18:21:51.259Z
---

The engineer's rulings on where the W18 (NWS basis) flow goes, 2026-11-16 and 17. The code is `W18…/py/nws_loads.py`. The rulings are also in `_BRAIN/00_CURRENT.md` and `07_PROJECT_STATE.md`.

- **Existing plots:** each keeps its 2026 flow in every year to 2100. That flow follows the W14 pattern for homes, shops and government plots, scaled to the team's 2026 settlement total. Existing plots take no growth. The two estates are added on top (316.4 m³/d).
- **Growth:** shared equally by the growth plots, which must be:
  - future, and inside their own settlement boundary;
  - 200–3,000 m²;
  - not odd-shaped (W14's test: compact ≥ 0.6, aspect ≤ 3);
  - any zoning, because the planning layer's proposed uses are not trusted;
  - not agricultural (zoned so, or a grove on the satellite test), not heritage (zoned "Tourism") and not industrial or an estate.
  - This gives 43,230 plots; Ibri has 11,053.
- **Capacity (2026-11-17):** 2026 population + growth plots × the team's properties per plot (their sheet, column D) × 4.8. This replaces the team's (existing + future properties) × 4.8, which counted existing properties at 4.8 people. The team's average population is untouched; the capacity only sets the year growth stops. Total 403,668 people; Ibri 144,537, full 2063.
- **No flow:** plots outside their settlement boundary. **Not carried:** plots on an inactive manhole, or more than 200 m from an active sewer. Their flow is reported, not modelled.
- **Rejected on the way:**
  - growth-plot area caps of 1,000 and 2,000 m²;
  - residential zoning only;
  - a cut at 10 m wide (it caught real row plots);
  - putting the commercial share on shop plots (about 8.7 m³/d per plot, implausible).
- **Wording:** say "property", never "dwelling" ([[say-property-not-dwelling]]).
- **SewerGEMS:** the final loads are in `IBRI_W18_R3.stsw` (job 071) and `IBRI_W18_R4.stsw` (job 072, 13 years), 2026-11-17. SC1 was redesigned on them (job 074), and the 12 final designs use them.

**Why:** the engineer tuned these rules plot by plot on check maps (`img/oddplots_*.pdf`, `img/plotflow_2056_*.pdf`). Re-deriving them would undo a day of review.

**How to apply:** do not change the growth-plot test without the engineer. Any new map or table follows these rules. The plot layer `gis/W18_plots_2026_2100.zip` carries the `GROWTH` flag. Related: [[nws-basis-change-nov-2026]].
