---
name: ibri-project-facts
description: Ibri sewer/STP project — non-obvious data facts and client-context established 2026-07-20
metadata: 
  node_type: memory
  type: project
  originSessionId: f5cfffa6-125f-404a-9529-fa7140e83e90
  modified: 2026-07-20T16:11:27.723Z
---

- `IBRI STP` point layer = **existing** STP (ground ≈327.6 m); new STP siting is consultant scope. Client: Nama Water Services; kickoff meeting 2026-07-21.
- NSA_DEM (4 m) is a **rough DSM** — survey ongoing; screening only, never invert design.
- Road_Centercline: .shx stale (provider reports 0 of 57,584 feats); no hierarchy attributes; main roads appear as **two parallel polylines** (dual carriageway).
- `Data/sample report/` was empty on 2026-07-20 (report styling reference pending — GAP-4).
- PAM-GUD-203 lacks per-capita/infiltration/peaking values → deferred to PAM-GUD-201 / NWS Integrated Master Plan (GAP-1..3).
- Gravity to existing STP viable for ~95% of plots (median available grade ≈3.6 m/km); SLS pockets ~3–5%; east satellite cluster (1,144 plots @31.7 km) is a satellite-STP/deferral question.
- User instruction: zones must follow **roads + plot density**, not pure DEM catchments; trunk should stay near-straight (avoid many bends), dual-carriageway arterials preferred. See [[ibri-brain-workflow]].
- W2 state (2026-07-20): DTM at `Hydraulic/Terrain/DTM_terrain_mask.tif` (5 m, patched from DSM near 449619,2568352) is the elevation source; duals collapsed to single routing corridor; 36 zones / 18 consolidated SLS / 134 crossings; QGIS layouts "W2 M1..M6" SAVED in project (satellite bg 30%, MoH_Plots for landuse maps, info table bottom-right); report style source `Data/sample report/Sample.docx` (build via `W2/report/make_report_r1.py`, python-docx). Full W2 constraints in `_BRAIN/06_W2_FEEDBACK.md`.
