# CLAUDE.md — 2621 Ibri Sewer, TE & STP (Renardet / NWS)

**MANDATORY: read `_BRAIN/00_CURRENT.md` (what is live vs superseded) then `_BRAIN/07_PROJECT_STATE.md` FIRST — it is the single-file orientation (data provided, project structure, settled engineering doctrine, progress stages, remaining tasks). Then `00_INDEX.md`, `02_DESIGN_CRITERIA.md` and — before laying out ANY network — `08_DESIGN_PHILOSOPHY.md`. **`02` says whether a design is legal; `08` says how to make it good, and it is binding.** W10 satisfied every number in `02` and still produced 4,041 dead-end fingers, a published layer in 7,919 disconnected pieces, 62 km of pipe in wadis serving nothing and a trunk carrying a main on 21 % of its length. Do not lay out a network without reading `08`. No metric may be invented: every slope, velocity, depth, flow or spacing must trace to PAM-GUD-203 (G203-p##), PAM-GUD-201 (G201-p##) or PAM-GUD-202 (G202-p##), or be an explicitly tagged pending-data assumption per `_BRAIN/05_GAPS.md`. The flow/load calculation method is fixed in `TUTORIALS/T01` and the load-allocation doctrine in PROJECT-STATE §2 — do not re-derive either.**

## Project in one paragraph
Concept→detailed design + supervision of wastewater network, treated-effluent (TE) network and STP capacity for Ibri Wilayat, Oman (Client: Nama Water Services, Tender T/2719110/2025). Design horizon completion+25 yr or saturation; model years start/2030/2055/ultimate; SewerGEMS/WaterGEMS deliverables; ≥3 options each for sewer network, TE network and each STP. Existing STP at **E444422.8 N2563337.9** (EPSG:32640, ground **328.7 m**; user-confirmed 2026-09-01, 47 m from the NAMA record and 5 m from the built rising main's end — the older E444387 N2563352 was 38 m out). Existing pumping station at **E449899.59 N2567301.72** (ground 351.1 m), the head of the built 10.0 km rising main. Ultimate saturated Qadf **≈74,700 m³/d** (W10 Phase 1.3, measured over 64,027 records at OR 5.32 and 1.456 properties per plot; **the 49,700 m³/d carried since W2 is retired** — it was built at OR 6.0 with one property per plot over only 53,503 plots, and the ratio decomposes exactly as 1.291 × 1.207 = 1.558). Far above the 20,000 threshold → STP phasing is the pivotal decision.

## Working rules (user-mandated)
1. **Iterations — see global rule 12.** Here the folders are `W1/`…`W12/`; the current design is named in `_BRAIN/00_CURRENT.md`.
   **A NEW `W#` COPIES THE PREVIOUS FOLDER AND REVISES IT. IT DOES NOT START FROM SCRATCH.**
   (User, 2026-09-06: *"where did I say do not carry the scripts from the previous working
   folder to the next? It is obvious the work is growing, not starting from scratch."*)
   "Never overwrite one" protects the **superseded** folder as the record — it has never meant
   the new folder starts empty. W10 was written fresh and kept exactly one string from W8
   across 36 scripts; it lost W8's 22-check auditor and shipped 45.92 km of pipe below minimum
   cover. W11b re-derived again and lost W8's pump-flag rule, publishing stations that were
   not needed. **Copy the code, then edit it. Read `_BRAIN/09_INHERITANCE.md` first and mark
   every row.** Anything deliberately NOT carried forward is a recorded decision, never a
   silent omission.
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
| `W8/` | **SUPERSEDED as a design, but the most valuable reference in the repo.** It is the only iteration that got the TEST AREA right - 71.6 km with ZERO pumping stations - and it is what every later iteration is measured against. `py/sewnet/stages/hydraulic.py` in particular: its `_lay` clears every pump flag at the top of each pass, and losing that one line cost W11b three phantom stations |
| `W10/`, `W11a/` | Superseded. W11a still holds `shp/W10_plot_loads.gpkg` (the load data W11b reads) and 100 figures |
| **`W11b/`** | **THE LIVE DESIGN.** Borrows nothing. `py/w11b/` (terrain, streams, hazard, criteria, hydra, contract, asbuilt, pumping, present), `py/s1..s8`, `py/tests/` (the project's first), `kmz/ dxf/ shp/ run/ docs/` |
| `../QGIS/QGIS 2621 ibri sewer stp.qgz` | Live QGIS project (layers + saved layouts W2 M1–M6) |
| `../../Data/` | Client documents (scope.pdf, PAM-GUD-203, PAM-GUD-201, sample report, figures) — NOT in repo |

## Current state (2026-09-03) — read `_BRAIN/00_CURRENT.md` first, then `07_PROJECT_STATE.md`, then `08_DESIGN_PHILOSOPHY.md`

**W11b IS THE LIVE DESIGN. W11a AND EVERYTHING BEFORE IT ARE SUPERSEDED.** W11b borrows
nothing — every module is under `W11b/`. Run from `W11b/py`: `s1_roads → s2_orient →
s3_hierarchy → s4_chambers → s5_flows → s6_levels → s7_pumps → s8_export`, then
`make_overview.py` for the KMZ and DXF.

**1,489.7 km · 56,930 chambers · 195 subnetworks · 47 pumping stations designed · 41 vortex
drop shafts.** Nothing below minimum cover, nothing over the depth-of-flow limit, nothing over
3.0 m/s.

**On the two measures that show whether a layout follows the ground, W11b beats the network
NAMA actually built**: 0.028 drop shafts per km against 0.585, and 26.3 % of length draining
against the ground against 34.1 %. W11a was 1.475/km and 42.5 %.

**THE FIX THAT GOT IT THERE CAME FROM THE ENGINEER'S EYE, NOT FROM A CHECK.** He saw that the
built network needs no pump in the test area, that W8's design of the same ground needs none,
and that W11b published three. They were **leftovers** — the solver only ever ADDED a station,
so one placed before the crown sweeps and relaid runs had recovered any fall survived to the
deliverable. **W8 had learned this two weeks earlier and cleared its pump flags every pass,
with the reason in a comment.** The rewrite lost it. Pruning: **83 → 14 demanded, 0 in the
test area.**

**The philosophy gained the general rule**: anything a pass can ADD, a later pass must be able
to TAKE AWAY, and the stage publishes how many it removed.

**TWO OF MY OWN DIAGNOSES WERE WRONG and were killed by measurement.** That 42.5 % drained
uphill is not a verdict — the BUILT network does it on 34 % of its length. And the claim that
W11b pinned every pipe at the minimum slope while W8 used the ground's fall came from looking
only at the median and the tenth percentile; across the full distribution they are
near-identical and W11b is steeper above the median.

**Open and named, all of it drawn on the KMZ and DXF rather than described**: the two station
counts disagree (14 demanded, 47 designed — s7 reads a pre-prune list); 15 of the 47 have
nothing upstream; **42 components discharge with more than half their catchment BELOW the
outlet — 389.5 km, worst outlet 22.8 m above its own low point**; 18 subnetworks stop short of
the main pipe, worst by 1,873 m; 5,521 plots cannot reach their chamber on gravity; 31 areas
holding 7,355 plots are not reached; and `s8_export` fails its own contract and cannot write
while QGIS holds the GeoPackage.

**W11b has the project's first tests** — six files written against the bugs that actually
happened, including one that fails if a published column is constant where it should vary.
And **pumps that are designed rather than located**: duty, lift, wet well, motor, life-cycle
cost and 47 rising mains, from the Oman standards directly.

**Already investigated, do not repeat** (`W11b/docs/UPSTREAM_METHODS.md`): two upstream sewer repositories. **Do NOT copy SWMManywhere's topology code** - its `tarjans_pq` is Prim's on a reversed graph, not Tarjan's branching, and measures 36-57 % worse than the correct algorithm. The IDEA is right and `networkx.minimum_spanning_arborescence` does it properly, but it buys about one uphill kilometre in twenty. `pysewer` is GPL - method only, never the code.

**Settled by the engineer, do not re-open:** τ = 1.0 Pa, flagged everywhere · flood no-data is
DRY HIGH GROUND · the 72 trunk chambers in a class-5/6 wadi are an ACCEPTED, flagged risk ·
the road DXF is clean, use all lines · no crossings manufactured for now · **stay in W11b, do
not start a W12** — four restarts have each lost something that worked.

### Superseded state (2026-08-23)
**W8 is the live design.** The main pipe is an INPUT (`SHP/Main Pipe/Main Pipe.shp`), both legs draining to their meeting point at (449125, 2567769) — 792 m outside the boundary — then on to the existing STP. **A sewer network is a hierarchy**, learned from NAMA's own manhole IDs (`5A-2-TM-MH185` = trunk main, `5A-2-SM.2-MH391` = sub main): in the built network 91% of laterals drain into another lateral and only ~16 things touch the trunk. W7 had no sub-main tier and 30 things touched the main pipe; W8 has **20 joins and ZERO pumping stations** (14 or fewer costs a pump, below 8 it starts crossing dual carriageways). Every pipe carries a `TIER` field. Gradients are laid at **round 0.05 % steps** so the drawing matches the levels, with `SLOPE_PCT` in every output. Test area: **1,415 chambers / 71.6 km / Qadf 3,620 m3/d / peak 96 L/s / deepest 10.45 m / ZERO pumping stations** / 3 checks failing. W7 and earlier are superseded.

**Learned from the built network** (`W8/docs/LEARNING_FROM_ASBUILT.md`, `W7/docs/CALIBRATION_vs_EXISTING.md`, and re-measured in `W11b/py/w11b/asbuilt.py`). **RETRACTED 2026-09-03: the claim that our gradients match the as-built at 5.00 against 4.98 mm/m does not hold.** Re-measured after filtering the status field, the built network's laid gradient is **mean 8.89 mm/m, median 6.00**, and it is **95.45 km built (63.20 km levelled), not 188.6 km** - the larger figure counted proposals, including two schematic records at over 300 m per vertex. Three lessons: tighter manhole spacing does NOT keep trenches shallower (tested, rejected); the built network almost never runs along a dual carriageway (0.1%), which confirms the rule; and the hierarchy is invisible in gradient/depth/spacing statistics — matching averages says the hydraulics are right and nothing about whether the layout is buildable.

**Guideline values are quoted from the source, never from memory** (user 2026-08-23). `TUTORIALS/T02` carries every design constraint with the page it came from. Verification corrected three loose quotes: the depth rule is a RECOMMENDATION of "approximately 10-12 m" COVER triggered by excavation COST; G203 Table 6 sets a 45 m maximum lateral length that the code declares but never enforces; Merrimack is stated only for catchments over 100 properties.

Settled since 2026-08-18 (all in `W5/docs/CRITERIA_UPDATE_R1.md`): terrain = 0.5 m VRT (rule 6) · dual carriageways excluded, not collapsed (rule 7) · farms narrowed — the farming carries no load, the houses on it do · load basis land-use driven, not blanket per-capita · Tab 12 drivers derived until the treated land-use data arrives.

**Next (2026-09-03):** fix the 42 badly-placed outfalls (389.5 km discharging with more than half their catchment below the outlet), reconcile the two station counts, and run the end-to-end test. Then the three concept options and the SewerGEMS referee run. **Do not start a W12** - four restarts have each lost something that worked. The user works remotely, so deliverables are committed AND pushed.
