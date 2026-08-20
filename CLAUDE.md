# CLAUDE.md — 2621 Ibri Sewer, TE & STP (Renardet / NWS)

**MANDATORY: read `_BRAIN/00_CURRENT.md` (what is live vs superseded) then `_BRAIN/07_PROJECT_STATE.md` FIRST — it is the single-file orientation (data provided, project structure, settled engineering doctrine, progress stages, remaining tasks). Then `00_INDEX.md` and `02_DESIGN_CRITERIA.md` before any analysis, script, map or report work. No metric may be invented: every slope, velocity, depth, flow or spacing must trace to PAM-GUD-203 (G203-p##), PAM-GUD-201 (G201-p##) or PAM-GUD-202 (G202-p##), or be an explicitly tagged pending-data assumption per `_BRAIN/05_GAPS.md`. The flow/load calculation method is fixed in `TUTORIALS/T01` and the load-allocation doctrine in PROJECT-STATE §2 — do not re-derive either.**

## Project in one paragraph
Concept→detailed design + supervision of wastewater network, treated-effluent (TE) network and STP capacity for Ibri Wilayat, Oman (Client: Nama Water Services, Tender T/2719110/2025). Design horizon completion+25 yr or saturation; model years start/2030/2055/ultimate; SewerGEMS/WaterGEMS deliverables; ≥3 options each for sewer network, TE network and each STP. Existing STP at E444387 N2563352 (EPSG:32640, ground ≈327.5 m). Ultimate saturated Qadf ≈ 49,700 m³/d (>20,000 threshold → STP phasing is the pivotal decision).

## Working rules (user-mandated)
1. Work iterations live in `W1/`, `W2/`, … — a rework request means create the next `W#` folder and revise scripts there; never overwrite a previous W.
2. Outputs every iteration: shapefiles + DXF + PNG maps + evolving report, so the user can inspect in GIS/CAD.
3. QGIS: load outputs into a named group (`Claude W#`) with proper styling; layouts must be SAVED into the project (layout manager), not just exported.
4. Maps: Google satellite hybrid background at 30% opacity; MoH_Plots as the land-use display layer; scalebar with non-overlapping labels; bottom-right box = data table relevant to that map; roads shown as provided (never present derived hierarchy as deliverable).
5. Report: styled strictly on `Data/sample report/Sample.docx` (build script `W2/report/make_report_r1.py`); client-facing tone — no internal/meta talk; expanded criteria with rationale; executive summary with real numbers; data-request register maintained.
6. Elevation source = `Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt` (0.5 m bare-earth terrain blend, EPSG:32640; user-designated latest/authoritative 2026-08-18 — folder name "Sat_" is misleading, it IS terrain). Superseded: `Hydraulic/Terrain/DTM_terrain_mask.tif` (5 m, used W1–W3); 4 m NSA_DEM screening only. No buildings in any DEM.
7. Dual carriageways are two parallel polylines. **For SEWER corridors they are EXCLUDED, not collapsed (user 2026-08-19): no pipe of any kind runs along a dual carriageway, trunk included, because it cannot be dug up. Crossing is allowed only as a short perpendicular pipe.** Identify them from the `dual` column in `SHP/Road centerline 2` (1 = dual carriageway, 2 = two-lane pair where only ONE side is used). The old collapse-to-one-corridor rule still applies to screening-level trunk routing (W2), not to W5+ design.
8. Zones: contiguous road-network territories weighted by plot density, one outlet each — never raw DEM watersheds, never ragged multipart dissolves.
9. SLS: consolidate — one station per contiguous non-gravity pocket (12 m max cover rule, GUD-203 p33), cascade stations within ~1.5 km, absorb pockets <50 plots to detail design.
10. Responses to the user: concise, bullets and tables.
11. Git: commit one logical change per commit; **never push without explicit instruction**. Remote: https://github.com/mojikone/Ibri-Sewer-and-STP.git (PUBLIC — user accepted on record 2026-07-20).
12. **README.md and `_BRAIN/07_PROJECT_STATE.md` are LIVE documents**: with every substantive commit, add a dated row on top of README's "Current state" table, correct its key-numbers table if results changed, AND update PROJECT-STATE (progress table, key numbers, doctrine, next tasks) so a new session always reads current truth. A commit that changes outputs but not both files is incomplete. Since the user works remotely, push after committing (warn-once policy applies only to sensitive/client/imagery content).

## Folder map
| Path (relative to this repo root `Hydraulic/Claude/`) | Content |
|---|---|
| `_BRAIN/` | Source of truth: **07_PROJECT_STATE (start here)**, scope register, design criteria, data inventory, tools, gaps, W2 feedback |
| `_SETUP/` | Environment for a fresh Claude instance: MCP config, python/node deps, memory snapshot |
| `_STANDARDS/` | PAM-GUD-202 pdf (201/203 stay in `Data/`) |
| `_CLIENT/` | Inception R0 package (report + demand workbook) pushed for remote access |
| `TUTORIALS/` | T01 sewage flow & load calculation (docx/pdf + md digest + generator) |
| `W1/`, `W2/`, `W3/` | Iteration outputs (py scripts are the pipeline; re-runnable). W3 = capacity/spillover/built-status analyses + plot classification layers |
| `W4/` | First sewer design pipeline: hydraulics, chambers, loads, audit + two adversarial reviews. **Superseded** — kept as the record, plus `W4/shp/ELE_accounts.shp` which the current pipeline still reads |
| `W5/` | The run before the trunk was placed and before the 12 m limit was enforced. **Superseded by W6** — its depth and pumping numbers are wrong; `docs/CRITERIA_UPDATE_R1.md` is still the live rule register |
| **`W6/`** | **CURRENT design.** `py/sewnet/` (one class per step, incl. `stages/trunk.py` and `stages/sweep.py`), `report/` (Word + PDF, numbers read live from the run), `docs/WHAT_CHANGED.md`, `shp/ dxf/ img/ sewergems/ run/` |
| `../QGIS/QGIS 2621 ibri sewer stp.qgz` | Live QGIS project (layers + saved layouts W2 M1–M6) |
| `../../Data/` | Client documents (scope.pdf, PAM-GUD-203, PAM-GUD-201, sample report, figures) — NOT in repo |

## Current state (2026-08-19 evening) — read `_BRAIN/00_CURRENT.md` first, then `_BRAIN/07_PROJECT_STATE.md`
**W6 is the live design.** Main pipe placed on the western edge + southern side as the user asked, with every street draining to its nearest joining point on it. **12 m maximum depth is a hard limit with no exemptions** — the audit used to skip chambers flagged as an "SLS pocket", which hid 71 chambers up to 21.3 m; that exemption is deleted and depth is checked at every chamber and along the trench between them. Where the pipe would pass 12 m a **pumping station** lifts it and the sewer restarts at normal cover; rising mains are sized on pump duty (0.75-3.0 m/s), not on the arriving flow. Test area: **1,925 chambers / 78.7 km / Qadf 3,619 m3/d / peak 96 L/s / deepest 11.88 m / 4 pumping stations (1,941 properties)** / 3 checks failing (143 sharp inlets needing a special chamber, 240 house connections over 50 m whose only frontage is a dual carriageway, 2 branch starts to merge). W5 and earlier are superseded.

Settled since 2026-08-18 (all in `W5/docs/CRITERIA_UPDATE_R1.md`): terrain = 0.5 m VRT (rule 6) · dual carriageways excluded, not collapsed (rule 7) · farms narrowed — the farming carries no load, the houses on it do · load basis land-use driven, not blanket per-capita · Tab 12 drivers derived until the treated land-use data arrives.

**Next:** run the pipeline over the full study area, then three concept options, the SewerGEMS referee run, and F2 georeferencing. The user works remotely — deliverables must be committed AND pushed.
