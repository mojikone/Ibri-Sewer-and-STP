# CLAUDE.md — 2621 Ibri Sewer, TE & STP (Renardet / NWS)

**MANDATORY: read `_BRAIN/07_PROJECT_STATE.md` FIRST — it is the single-file orientation (data provided, project structure, settled engineering doctrine, progress stages, remaining tasks). Then `00_INDEX.md` and `02_DESIGN_CRITERIA.md` before any analysis, script, map or report work. No metric may be invented: every slope, velocity, depth, flow or spacing must trace to PAM-GUD-203 (G203-p##), PAM-GUD-201 (G201-p##) or PAM-GUD-202 (G202-p##), or be an explicitly tagged pending-data assumption per `_BRAIN/05_GAPS.md`. The flow/load calculation method is fixed in `TUTORIALS/T01` and the load-allocation doctrine in PROJECT-STATE §2 — do not re-derive either.**

## Project in one paragraph
Concept→detailed design + supervision of wastewater network, treated-effluent (TE) network and STP capacity for Ibri Wilayat, Oman (Client: Nama Water Services, Tender T/2719110/2025). Design horizon completion+25 yr or saturation; model years start/2030/2055/ultimate; SewerGEMS/WaterGEMS deliverables; ≥3 options each for sewer network, TE network and each STP. Existing STP at E444387 N2563352 (EPSG:32640, ground ≈327.5 m). Ultimate saturated Qadf ≈ 49,700 m³/d (>20,000 threshold → STP phasing is the pivotal decision).

## Working rules (user-mandated)
1. Work iterations live in `W1/`, `W2/`, … — a rework request means create the next `W#` folder and revise scripts there; never overwrite a previous W.
2. Outputs every iteration: shapefiles + DXF + PNG maps + evolving report, so the user can inspect in GIS/CAD.
3. QGIS: load outputs into a named group (`Claude W#`) with proper styling; layouts must be SAVED into the project (layout manager), not just exported.
4. Maps: Google satellite hybrid background at 30% opacity; MoH_Plots as the land-use display layer; scalebar with non-overlapping labels; bottom-right box = data table relevant to that map; roads shown as provided (never present derived hierarchy as deliverable).
5. Report: styled strictly on `Data/sample report/Sample.docx` (build script `W2/report/make_report_r1.py`); client-facing tone — no internal/meta talk; expanded criteria with rationale; executive summary with real numbers; data-request register maintained.
6. Elevation source = `Hydraulic/Terrain/DTM_terrain_mask.tif` (5 m DTM, user-patched near 449619,2568352). The 4 m NSA_DEM is also a **DTM** (user-corrected 2026-08-14; no buildings in any DEM) — rough, screening only.
7. Dual carriageways are two parallel polylines — collapse to a single routing corridor; a trunk never runs twice along one road.
8. Zones: contiguous road-network territories weighted by plot density, one outlet each — never raw DEM watersheds, never ragged multipart dissolves.
9. SLS: consolidate — one station per contiguous non-gravity pocket (12 m max cover rule, GUD-203 p33), cascade stations within ~1.5 km, absorb pockets <50 plots to detail design.
10. Responses to the user: concise, bullets and tables.
11. Git: commit one logical change per commit; **never push without explicit instruction**. Remote: https://github.com/mojikone/Ibri-Sewer-and-STP.git (PUBLIC — user accepted on record 2026-07-20).
12. **README.md is a living summary**: with every substantive commit, add a dated row on top of its "Current state" table and correct the key-numbers table if results changed. A commit that changes outputs but not README is incomplete.

## Folder map
| Path (relative to this repo root `Hydraulic/Claude/`) | Content |
|---|---|
| `_BRAIN/` | Source of truth: **07_PROJECT_STATE (start here)**, scope register, design criteria, data inventory, tools, gaps, W2 feedback |
| `_SETUP/` | Environment for a fresh Claude instance: MCP config, python/node deps, memory snapshot |
| `_STANDARDS/` | PAM-GUD-202 pdf (201/203 stay in `Data/`) |
| `_CLIENT/` | Inception R0 package (report + demand workbook) pushed for remote access |
| `TUTORIALS/` | T01 sewage flow & load calculation (Rev 2 docx/pdf + md digest + generator) |
| `W1/`, `W2/`, `W3/` | Iteration outputs (py scripts are the pipeline; re-runnable). W3 = capacity/spillover/built-status analyses + plot classification layers |
| `../QGIS/QGIS 2621 ibri sewer stp.qgz` | Live QGIS project (layers + saved layouts W2 M1–M6) |
| `../../Data/` | Client documents (scope.pdf, PAM-GUD-203, PAM-GUD-201, sample report, figures) — NOT in repo |

## Current state (2026-08-15) — full detail in `_BRAIN/07_PROJECT_STATE.md`
W2 delivered (36 zones, trunk 22+172 km, 18 SLS, report R1). T01 flow/load tutorial Rev 2 done. W3 analyses done: settlement capacity (IBRI ceiling crossed ≈2038), spillover growth model, plot built/planned/agri classification v4 (imagery-based, 61,272 plots), unparceled-buildings layer. Load-allocation doctrine settled (PROJECT-STATE §2). **Next: W4 — network design in a test boundary**, then three concept options, SewerGEMS seed, F2 georeferencing. User works remotely: deliverables must be committed AND pushed (warn-once policy for sensitive content applies).
