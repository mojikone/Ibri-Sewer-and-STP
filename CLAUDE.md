# CLAUDE.md — 2621 Ibri Sewer, TE & STP (Renardet / NWS)

**MANDATORY: read `_BRAIN/00_CURRENT.md` (what is live vs superseded) then `_BRAIN/07_PROJECT_STATE.md` FIRST — it is the single-file orientation (data provided, project structure, settled engineering doctrine, progress stages, remaining tasks). Then `00_INDEX.md`, `02_DESIGN_CRITERIA.md` and — before laying out ANY network — `08_DESIGN_PHILOSOPHY.md`. **`02` says whether a design is legal; `08` says how to make it good, and it is binding.** W10 satisfied every number in `02` and still produced 4,041 dead-end fingers, a published layer in 7,919 disconnected pieces, 62 km of pipe in wadis serving nothing and a trunk carrying a main on 21 % of its length. Do not lay out a network without reading `08`. No metric may be invented: every slope, velocity, depth, flow or spacing must trace to PAM-GUD-203 (G203-p##), PAM-GUD-201 (G201-p##) or PAM-GUD-202 (G202-p##), or be an explicitly tagged pending-data assumption per `_BRAIN/05_GAPS.md`. The flow/load calculation method is fixed in `TUTORIALS/T01` and the load-allocation doctrine in PROJECT-STATE §2 — do not re-derive either.**

## Project in one paragraph
Concept→detailed design + supervision of wastewater network, treated-effluent (TE) network and STP capacity for Ibri Wilayat, Oman (Client: Nama Water Services, Tender T/2719110/2025). Design horizon completion+25 yr or saturation; model years start/2030/2055/ultimate; SewerGEMS/WaterGEMS deliverables; ≥3 options each for sewer network, TE network and each STP. Existing STP at **E444422.8 N2563337.9** (EPSG:32640, ground **328.7 m**; user-confirmed 2026-09-01, 47 m from the NAMA record and 5 m from the built rising main's end — the older E444387 N2563352 was 38 m out). Existing pumping station at **E449899.59 N2567301.72** (ground 351.1 m), the head of the built 10.0 km rising main. Ultimate saturated Qadf **≈74,700 m³/d** (W10 Phase 1.3, measured over 64,027 records at OR 5.32 and 1.456 properties per plot; **the 49,700 m³/d carried since W2 is retired** — it was built at OR 6.0 with one property per plot over only 53,503 plots, and the ratio decomposes exactly as 1.291 × 1.207 = 1.558). Far above the 20,000 threshold → STP phasing is the pivotal decision.

## Working rules (user-mandated)
1. **Iterations — see global rule 12.** Here the folders are `W1/`…`W9/`; the current design is named in `_BRAIN/00_CURRENT.md`.
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
12. **Live documents — see global rule 13.** Here they are `README.md` (a dated row on top of the "Current state" table, and the key-numbers table corrected if results changed) and `_BRAIN/07_PROJECT_STATE.md` (doctrine, progress, key numbers, next tasks). Check with `python _SETUP/check_live_docs.py`. **The user works remotely, so push after committing** — this is the standing authorisation that satisfies global rule 10; the warn-once policy applies only to sensitive, client or imagery content.
13. **RESPONSE DEPTH — see global rule 11.** `AUTO` is the default (no ceiling, always lead with a bold standalone headline); `L1`–`L5` bind only when invoked and they nest; sticky within a chat, released by `auto`/`L0`, never sticky across chats unless written as a standing default. Modifiers `why` and `show me`. At L4/L5 put long detail in a file — here that means `W9/analysis/` or the report — and give a one-line pointer. The full rule lives in `~/.claude/CLAUDE.md`, mirrored at `_SETUP/global-CLAUDE.md`; it is a working preference, not a project rule, so it is not duplicated here.

## Folder map
| Path (relative to this repo root `Hydraulic/Claude/`) | Content |
|---|---|
| `_BRAIN/` | Source of truth: **07_PROJECT_STATE (start here)**, scope register, design criteria, data inventory, tools, gaps, W2 feedback |
| `_SETUP/` | Environment for a fresh Claude instance: MCP config, python/node deps, memory snapshot |
| `_STANDARDS/` | PAM-GUD-202 pdf (201/203 stay in `Data/`) |
| `_CLIENT/` | Inception R0 package (report + demand workbook) pushed for remote access |
| `TUTORIALS/` | T01 sewage flow & load calculation; **T02 hydraulic design of a gravity sewer** — every constraint with its guideline page, Word + PDF from one source |
| `W1/`, `W2/`, `W3/` | Iteration outputs (py scripts are the pipeline; re-runnable). W3 = capacity/spillover/built-status analyses + plot classification layers |
| `W4/` | First sewer design pipeline: hydraulics, chambers, loads, audit + two adversarial reviews. **Superseded** — kept as the record, plus `W4/shp/ELE_accounts.shp` which the current pipeline still reads |
| `W5/` | The run before the trunk was placed and before the 12 m limit was enforced. **Superseded by W6** — its depth and pumping numbers are wrong; `docs/CRITERIA_UPDATE_R1.md` is still the live rule register |
| `W6/` | The run with a GUESSED trunk: 4 pumping stations, chambers to 11.9 m. **Superseded by W7** |
| `W7/` | Main pipe placed correctly and zero pumping stations, but NO sub-main tier — 30 things touched the trunk. **Superseded by W8**; `docs/CALIBRATION_vs_EXISTING.md` still valid |
| **`W8/`** | **CURRENT design.** `py/sewnet/` (one class per step), `report/` (Word + PDF, rebuilt on every run), `docs/LEARNING_FROM_ASBUILT.md`, `shp/ dxf/ img/ sewergems/ run/`, `W8_sewer_design.kmz` for Google Earth |
| `../QGIS/QGIS 2621 ibri sewer stp.qgz` | Live QGIS project (layers + saved layouts W2 M1–M6) |
| `../../Data/` | Client documents (scope.pdf, PAM-GUD-203, PAM-GUD-201, sample report, figures) — NOT in repo |

## Current state (2026-09-02) — read `_BRAIN/00_CURRENT.md` first, then `07_PROJECT_STATE.md`, then `08_DESIGN_PHILOSOPHY.md`

**A binding design philosophy now exists: `_BRAIN/08_DESIGN_PHILOSOPHY.md`, 232 lines, rules
only.** `02` says whether a design is LEGAL, `08` says how to make it GOOD, and `02` wins where
they conflict. **Do not lay out a network without reading it.**

**W10 — the first full-area design — is COMPLETE but NOT ISSUABLE.** 1,883 km of pipe,
73,442 m³/d, 19–21 lifting stations, 98.1 % of plots served. Audited against W8's own check
registry it fails four ways: **2.80 km of surcharged trunk, 10.68 km over d/D, 45.92 km below
minimum cover, 1.67 km along a dual carriageway** — plus 131.7 km on wadi ground and a
published layer in 7,919 disconnected pieces. Cause in one line: *W8's engineering was carried
into W10 and W8's auditor was not.* **Its findings stand; its design does not.**

**W11a has started and only stage 0 exists** — the auditor at `W11a/py/w11a/audit.py`,
22 checks, run with `python W11a/py/run_audit.py`. Against W10: **2 pass, 13 FAIL, 7 cannot
run** (`W11a/run/audit_W10.csv`), and that table is the specification for everything after.
Two architectural rules it enforces: audit the **published layers**, never an in-memory model;
and **a check that cannot run is a failure**, not a blank.

**THE TOR REQUIRES EVERY PLOT TO BE SERVED** — scope p4 item 3, p6 item 2, p8 item 17. An
earlier assumption that 31 marginal settlements would be dropped is **withdrawn**. But
*serviced* ≠ *connected to one network*: the question is which **system** serves each — central,
satellite, or on-site — decided on life-cycle cost. Scope p12 also makes pumping minimisation a
**client requirement**, not our preference.

**The largest open assumption:** 97 % of the network self-cleanses by the **tractive-force
route**, and the guideline gives **no numeric τ** (GAP-9, assumed 1.0 Pa; 2.35× harder at 2.0).

**Settled and not to be re-litigated:** oversizing to lay flatter is **prohibited** (G203-p29
and Ten States §33.43 independently) · **no solver chooses a layout**, and none will ever
propose a pumping station · the **cap-and-veto ladder** — 12 m of cover with two
distance-bounded exits (500 m recovery, 1,000 m to outfall), everything past it flagged · a
lifting station is also a **commissioning device** · **BAT is deliberately undecided**, both
options into the appraisal.

**Waiting on:** the draftsman's final treated lines and the GIS expert's clean land-use data —
the scripts are being purified so both drop straight in.

**Nine research documents in `W10/docs/research/`** underpin all of it: `HIERARCHY_RULES`,
`CORRIDOR_QUALITY`, `WHAT_TO_SEWER`, `DEPTH_VS_PUMPING`, `SEWERGEMS_DESIGN_METHOD`,
`DESIGN_ENGINES_COMPARED`, `W8_W10_POSTMORTEM`, `DELIVERABLE_SPEC`, `PHILOSOPHY_REVIEW`,
`W11a_BUILD_BRIEF`.

### Superseded state (2026-08-23)
**W8 is the live design.** The main pipe is an INPUT (`SHP/Main Pipe/Main Pipe.shp`), both legs draining to their meeting point at (449125, 2567769) — 792 m outside the boundary — then on to the existing STP. **A sewer network is a hierarchy**, learned from NAMA's own manhole IDs (`5A-2-TM-MH185` = trunk main, `5A-2-SM.2-MH391` = sub main): in the built network 91% of laterals drain into another lateral and only ~16 things touch the trunk. W7 had no sub-main tier and 30 things touched the main pipe; W8 has **20 joins and ZERO pumping stations** (14 or fewer costs a pump, below 8 it starts crossing dual carriageways). Every pipe carries a `TIER` field. Gradients are laid at **round 0.05 % steps** so the drawing matches the levels, with `SLOPE_PCT` in every output. Test area: **1,415 chambers / 71.6 km / Qadf 3,620 m3/d / peak 96 L/s / deepest 10.45 m / ZERO pumping stations** / 3 checks failing. W7 and earlier are superseded.

**Learned from the built network** (`W8/docs/LEARNING_FROM_ASBUILT.md`, and the earlier `W7/docs/CALIBRATION_vs_EXISTING.md`): gradients (5.00 vs 4.98 mm/m) and depths match NAMA's 188.6 km as-built. Three lessons: tighter manhole spacing does NOT keep trenches shallower (tested, rejected); the built network almost never runs along a dual carriageway (0.1%), which confirms the rule; and the hierarchy is invisible in gradient/depth/spacing statistics — matching averages says the hydraulics are right and nothing about whether the layout is buildable.

**Guideline values are quoted from the source, never from memory** (user 2026-08-23). `TUTORIALS/T02` carries every design constraint with the page it came from. Verification corrected three loose quotes: the depth rule is a RECOMMENDATION of "approximately 10-12 m" COVER triggered by excavation COST; G203 Table 6 sets a 45 m maximum lateral length that the code declares but never enforces; Merrimack is stated only for catchments over 100 properties.

Settled since 2026-08-18 (all in `W5/docs/CRITERIA_UPDATE_R1.md`): terrain = 0.5 m VRT (rule 6) · dual carriageways excluded, not collapsed (rule 7) · farms narrowed — the farming carries no load, the houses on it do · load basis land-use driven, not blanket per-capita · Tab 12 drivers derived until the treated land-use data arrives.

**Next:** run the pipeline over the full study area, then three concept options, the SewerGEMS referee run, and F2 georeferencing. Open items: 4 pipes crossing a dual carriageway with no underpass, 22 chambers that cannot be freed from a plot because the road centreline runs through it, 236 plots whose only frontage is a dual carriageway (user decision), and a coordinate for the surviving roundabout. The user works remotely — deliverables must be committed AND pushed.
