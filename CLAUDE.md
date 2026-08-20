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
| `W6/` | The run with a GUESSED trunk: 4 pumping stations, chambers to 11.9 m. **Superseded by W7** |
| **`W7/`** | **CURRENT design.** `py/sewnet/` (one class per step; `stages/trunk.py` reads the drawn main pipe, `stages/sweep.py` is deleted), `report/` (Word + PDF, rebuilt on every run), `docs/CALIBRATION_vs_EXISTING.md`, `shp/ dxf/ img/ sewergems/ run/`, `W7_sewer_design.kmz` for Google Earth |
| `../QGIS/QGIS 2621 ibri sewer stp.qgz` | Live QGIS project (layers + saved layouts W2 M1–M6) |
| `../../Data/` | Client documents (scope.pdf, PAM-GUD-203, PAM-GUD-201, sample report, figures) — NOT in repo |

## Current state (2026-08-20) — read `_BRAIN/00_CURRENT.md` first, then `_BRAIN/07_PROJECT_STATE.md`
**W7 is the live design.** The main pipe is an INPUT, not a guess: `SHP/Main Pipe/Main Pipe.shp`, 6.15 km serving the test area, both legs draining to their meeting point at (449125, 2567769) — 792 m outside the boundary — then on to the existing STP at (444387, 2563352). W6 guessed the trunk, covered an eighth of the area and needed 4 pumping stations; **W7 needs none** and the deepest chamber is 9.96 m. Joins onto the trunk cost route length and are capped at the fewest that work (30 of 55; 28 or fewer costs a pump). A dual carriageway may be CROSSED but never followed — 31 crossings offered, **1 built, through the underpass at (450375.24, 2568397.64)**, so no trenchless work. Inlet angle 85 deg, FLAGGED never fixed (stated deviation from G203-p30's 90). One gradient per street run. Short dead-end branches are dropped (0, 0 km) so those houses join the street they came off. Test area: **1,424 chambers / 71.8 km / Qadf 3,620 m3/d / peak 96 L/s / deepest 9.96 m / ZERO pumping stations** / 2 checks failing (78 sharp inlets for a curved-channel chamber, 236 plots with no sewer within 50 m). W6 and earlier are superseded.

**Calibrated against the built network** (`W7/docs/CALIBRATION_vs_EXISTING.md`): NAMA's 188.6 km as-built was measured from the KMZ files. Gradients (5.00 vs 4.98 mm/m) and depths match. Two lessons: tighter manhole spacing does NOT keep trenches shallower (tested, rejected — keep the fewest manholes), and the built network almost never runs along a dual carriageway (0.1%), which confirms the rule.

Settled since 2026-08-18 (all in `W5/docs/CRITERIA_UPDATE_R1.md`): terrain = 0.5 m VRT (rule 6) · dual carriageways excluded, not collapsed (rule 7) · farms narrowed — the farming carries no load, the houses on it do · load basis land-use driven, not blanket per-capita · Tab 12 drivers derived until the treated land-use data arrives.

**Next:** run the pipeline over the full study area, then three concept options, the SewerGEMS referee run, and F2 georeferencing. The user works remotely — deliverables must be committed AND pushed.
