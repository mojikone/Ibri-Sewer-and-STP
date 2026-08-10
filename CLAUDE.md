# CLAUDE.md — 2621 Ibri Sewer, TE & STP (Renardet / NWS)

**MANDATORY: read `_BRAIN/` in full before any analysis, script, map or report work — `00_INDEX.md` first, then `02_DESIGN_CRITERIA.md`. No metric may be invented: every slope, velocity, depth, flow or spacing must trace to PAM-GUD-203 (cite p##) or PAM-GUD-201 (cite G1-p##), or be an explicitly tagged pending-data assumption per `_BRAIN/05_GAPS.md`.**

## Project in one paragraph
Concept→detailed design + supervision of wastewater network, treated-effluent (TE) network and STP capacity for Ibri Wilayat, Oman (Client: Nama Water Services, Tender T/2719110/2025). Design horizon completion+25 yr or saturation; model years start/2030/2055/ultimate; SewerGEMS/WaterGEMS deliverables; ≥3 options each for sewer network, TE network and each STP. Existing STP at E444387 N2563352 (EPSG:32640, ground ≈327.5 m). Ultimate saturated Qadf ≈ 49,700 m³/d (>20,000 threshold → STP phasing is the pivotal decision).

## Working rules (user-mandated)
1. Work iterations live in `W1/`, `W2/`, … — a rework request means create the next `W#` folder and revise scripts there; never overwrite a previous W.
2. Outputs every iteration: shapefiles + DXF + PNG maps + evolving report, so the user can inspect in GIS/CAD.
3. QGIS: load outputs into a named group (`Claude W#`) with proper styling; layouts must be SAVED into the project (layout manager), not just exported.
4. Maps: Google satellite hybrid background at 30% opacity; MoH_Plots as the land-use display layer; scalebar with non-overlapping labels; bottom-right box = data table relevant to that map; roads shown as provided (never present derived hierarchy as deliverable).
5. Report: styled strictly on `Data/sample report/Sample.docx` (build script `W2/report/make_report_r1.py`); client-facing tone — no internal/meta talk; expanded criteria with rationale; executive summary with real numbers; data-request register maintained.
6. Elevation source = `Hydraulic/Terrain/DTM_terrain_mask.tif` (5 m DTM, user-patched from DSM near 449619,2568352). The 4 m NSA_DEM is a rough DSM — screening only.
7. Dual carriageways are two parallel polylines — collapse to a single routing corridor; a trunk never runs twice along one road.
8. Zones: contiguous road-network territories weighted by plot density, one outlet each — never raw DEM watersheds, never ragged multipart dissolves.
9. SLS: consolidate — one station per contiguous non-gravity pocket (12 m max cover rule, GUD-203 p33), cascade stations within ~1.5 km, absorb pockets <50 plots to detail design.
10. Responses to the user: concise, bullets and tables.
11. Git: commit one logical change per commit; **never push without explicit instruction**. Remote: https://github.com/mojikone/Ibri-Sewer-and-STP.git (PUBLIC — user accepted on record 2026-07-20).

## Folder map
| Path (relative to this repo root `Hydraulic/Claude/`) | Content |
|---|---|
| `_BRAIN/` | Source of truth: scope register, design criteria, data inventory, tools, gaps, W2 feedback constraints |
| `_SETUP/` | Environment for a fresh Claude instance: MCP config, python/node deps, memory snapshot |
| `W1/`, `W2/` | Iteration outputs (py scripts are the pipeline; re-runnable) |
| `../QGIS/QGIS 2621 ibri sewer stp.qgz` | Live QGIS project (layers + saved layouts W2 M1–M6) |
| `../../Data/` | Client documents (scope.pdf, PAM-GUD-203, PAM-GUD-201, sample report, figures) — NOT in repo |

## Current state (2026-07-20)
W2 delivered: 36 zones, trunk 22+172 km, 18 consolidated SLS, 134 wadi crossings, report R1 (docx+pdf), DXF, saved layouts. Pending: NCSI occupancy (flows scale with it), existing-network as-builts (F2 area NE served district + existing trunk to STP), sample-report GAP closed. Next: georeference F2, three concept options, SewerGEMS seed model.
