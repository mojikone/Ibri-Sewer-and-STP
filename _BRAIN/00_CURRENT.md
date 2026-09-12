# What is current, and what is not — checked 2026-09-12

**Design flows: `W14/docs/DESIGN_FLOWS_FOR_NETWORK.md`** — size on `Q_ULT`; audit self-cleansing on `Q_2030` × 0.61 in three classes (velocity pass, tractive pass at τ = 1 Pa, needs washing); gradients at concept = Table 11 minimum in 0.05 % (secondary) / 0.025 % (trunks DN500+) steps, no Mara-raised gradient until preliminary (engineer, 2026-09-11). The W13 engine still carries a flat 5.0 per plot: the prompt `W14/docs/PROMPT_W13_SELFCLEANSING_AUDIT.md` is what the W13 engine chat followed (done in tmp3, 2026-09-11) to change that. **The method, taught: `TUTORIALS/T04/`** (T01, T02, T03_R01 frozen).

**Population, saturation and load per plot live in `W14/` (class v7, 2026-09-10); W13 stays the pipe-laying engine.** `W14/` holds the meter-to-plot chain, the plot class, the per-settlement occupancy (floor 4.0, cap 6.12, the under-1,000 rule), the growth to saturation and the **Concept Design Report Revision 2** (`W14/report/R2/`, 89 pages; `W14/deliverables/` is the packaged hand-over). Numbers: today 119,893 people / 20,852 m³/d; saturation **2070 at 349,029 people / 60,099 m³/d**; Ibri full 2056. Every plot's flow is one equation (report 15.4: 0.85 × 164 × OR × N_dom + 0.54 × (U_nd × N_nd + U_gov × N_gov + 93 × workers)) and the plots sum to the settlement layer in every column. Read `W14/docs/CONCEPT_NOTE_SATURATION_AND_LOAD.md` first. The `W14/` named below as a sub-mains-first trial was removed on 2026-09-07; the folder name was reused for the population work on 2026-09-10.

## READ THIS FIRST: W10, W11a, W11b AND W12 WERE REVERTED OUT OF THIS REPO

**The live design is W13, and W13 is a copy of W8.** Run it:
`python W13/py/run_test_boundary.py` — **26 seconds**, and it reproduces W8 to the digit:
**1,415 chambers · 1,414 reaches · 71.64 km · ZERO pumping stations · deepest 10.45 m ·
3 failing checks of 22.**

**Why the four folders are gone.** W8 designed the 5.51 km² test area well. W10 then scaled to
531 km² — **ninety-six times — in a single step, and was never required to reproduce W8's
answer on W8's own ground first.** W11a, W11b and W12 each inherited that. Measured on
2026-09-06 inside W8's own boundary, W12 produced **3,139 chambers against W8's 1,415, and one
pumping station on ground where W8 and the network NAMA actually built both need none.**
Six weeks, four iterations, four worse designs. The engineer reverted the line on 2026-09-07.

**THE GATE, and it is the whole lesson.** No change ships until the design still gives
**71.6 km, ~1,415 chambers and ZERO pumping stations on that 5.51 km²**. Twenty-six seconds.
Run it after every change. A design that cannot still do 5.51 km² has no business being
trusted on 531. See `CLAUDE.md` rule 1.

**STANDING DECISION 2026-09-07 — 12 m OF COVER IS A HARD LIMIT.** G203-p33 §4.6.3 makes
10–12 m a *recommendation* and makes **excavation cost** the real trigger for a pumping
station. We are not costing anything at concept stage, so **until the hydraulic design is
ready for cost analysis, nothing goes deeper than 12 m.** Do not read "recommendation" as
permission, and **do not build exits around it** — W12 capped at 12 m, allowed any breach
"within 1,000 m of an outfall", and 1,362 chambers came through that single exit at up to
19.98 m. Deleting the exit gave 3 chambers and 12.79 m. W13 implements the hard limit
correctly, including the trench *between* chambers. It has never bound on the test area
(deepest 10.45 m); it will bind at full area.

**The wadi rules were restored on 2026-09-07 with their real citations** — presence
*"must be avoided"* (p30 §4.4.1a) / *"shall be avoided"* (p33), read as `shall` where the
design finds no other way, with the presence recorded as a justified exception rather than a
silent one; **1.5 m cover at a crossing is a GUIDELINE value** (p52 §8.2.4, *"As for
gravitational sewer…"*), not the project assumption we had wrongly filed it as; and the 0.5 m
cover is a **conditional exception** needing a stated circumstance, concrete protection, and
the 0.5 m measured *above the protection*.

**Stage A of the new engine is done on the built area (2026-09-07):** `python W13/py/run_stage_a.py`,
88 s, the ground read along 120 km of DXF street inside the 7.21 km² the 2006 laterals serve
(trunk corridor out), then the network as a tree: 23 joins at NAMA's spacing, the west
settlement as one sub-network entering NAMA's corridor to the STP at its south-west corner, 3
short links to the main pipe (no road between, under 150 m), no sink (basins drain over their
rim with the extra depth marked), 11 islands; sub-mains are the long straight streets (chains,
250 m minimum, a threshold the engineer may tune), heads at the first gate, 30 contiguous
catchments, no loops, one outlet per node, checked in QGIS (group `Claude W13 A`). **Every run
now lays the tree and reports its depth (rule 9, `sewnet/quicklay.py`): 1,765 chambers, deepest
11.47 m, none over 12 m, no pump, after five reroutes found by reading the governing path into
the deepest chamber (20.0 m at first). Outlets are assigned by rule 5's least-depth cost, not the
flood (`ASSIGN_BY_DEPTH`); the search runs from the outlets with sub-mains at half cost.** **Since
2026-09-08 the scope is the engineer's test boundary (21.4 km², `AREA_SHP`), NAMA's corridor is off, a
pocket is offered a designed trunk along the streets, and rule 10 runs mechanically and reports its
refusals. On the boundary the west settlement and the low ground at the works have NO gravity way to
the existing inlet at 323.0 m (the road into the plant dips to 324.2 m; the interior's rim puts the
corner 9.6 m deep). The engineer ruled everything on gravity, converging on the outlet, inlet unchanged,
NAMA's last kilometre allowed: the run now puts the whole west side on one designed trunk to the works
with one pump west of the settlement, 27 chambers over 12 m, deepest 16.1 m, the trunk 7.8 m under the
inlet. Then whole-street sub-mains as the engineer asked (cut only at a crest, a sag the water leaves,
or a change of outlet; rule 10 builds no pipes; join floor set aside): strings of 3 to 4 km, but 31.9 m
at the deepest because one street crosses C06's basin and climbs back. Then the W14 trial, sub-mains
first (`W14/`, `SKELETON_FIRST`): every sub-network one clean block, the maze gone; then the 12 m rule as
the engineer stated it (`REROUTE_MODE = "cut"`): 8 pump candidates, 32.9 km, and nothing past 12 m except
the west's trunk to the works (15.7 m, 8.1 m under the inlet at 323.0 m). Measured for the engineer: with
nothing below 12 m that trunk meets the works at 317.3 m; to meet the inlet it may be no deeper than 3.3 m
at its head, where the west's interior arrives at 11.4 m, so meeting the inlet by gravity means a pump for
that interior. The two streets that climbed to the main pipe are a scratch layer in QGIS. W13 stays the record of the catchments-first line; W14 was removed the same day (below) and the engine grows in `W13/tmp2` now, nothing added to the logic until the engineer agrees the design.** **The drawing
to look at is `W13/dxf/W13_A_tree.dxf`**; `W13_A_ground.dxf` is the raw ground for reference;
numbers `W13/run/stage_a.json` and `W13/docs/W13_EVIDENCE.md`. **Next is Stage B (rules 3–6
routed).** The old test-boundary pipeline (`run_test_boundary.py`, `stages/tree.py`,
`stages/trunk.py`) still runs and is untouched; the new engine grows beside it in
`sewnet/ground.py`, `outlets.py`, `skeleton.py`, `streams.py`, `export_tree.py`.

**The W13 design logic is written (2026-09-07):** `W13/docs/W13_DESIGN_LOGIC.md`, twelve agreed
rules (rules only — every measurement, as-built check and run result lives in
`W13/docs/W13_EVIDENCE.md`, engineer's instruction), a proposed rule-to-engine-step mapping, the road input (the draftsman's DXF in
`Hydraulic/DWG/`, replacing the SHP road layer for corridors), the scope (street sewers only, no
tertiary yet), the check-drawing spec, and the rulings of the same day: no crossings of dual
carriageways are generated, the DXF is trusted as drawn, and an outlet without a street route to
the main pipe is linked directly across open ground where no plot is in the way. Read it before touching the engine. It lives in
W13 on purpose: the brain philosophy file was set aside to keep the process light while the engine
is rebuilt to run the full area in minutes. Change it by adding a dated line, never by rewriting.

**The design criteria exist as a clean Word document (2026-09-07):**
`W13/docs/design_criteria/R0/Ibri_Sewer_Design_Criteria_R0.docx` + `.pdf`, rebuilt by
`W13/docs/design_criteria/build.py` (`--pdf` renders through Word). It is the readable form of
`_BRAIN/02_DESIGN_CRITERIA.md` — same values, same page citations, internal history removed,
standing decisions kept and dated, plus an **"Adopted in W13"** column read from
`W13/py/sewnet/criteria.py` and two registers (decisions/assumptions; deviations to declare to
NWS). `02_DESIGN_CRITERIA.md` remains the source of truth; when a value changes, change it there
first and rebuild the document. **Known discrepancy it surfaced:** `criteria.py` OCCUPANCY = 5.0
(W8 inheritance) against the locked 5.32 — the gate figures were produced at 5.0, so the code is
unchanged and the decision is recorded in `07_PROJECT_STATE.md` §6.

**W14 was removed on 2026-09-08 at the engineer's instruction (created without being asked; its history stays in
git). The trial is `W13/tmp_compare`, the 7 September engine on the new main pipe. Reverted to `8529df6` the same
day, and the 7 September network is a fixed reference: `REF_7SEPT/` is commit `3897c0e`'s W13 with the main pipe of that day recovered from the drawing,
and it reproduces that run to the figure. Nothing later writes into it; later layouts are measured against it.**

**The trials of 2026-09-08 (late), both inside W13 and neither the live design.** `W13/tmp1/` is the 7 September engine (`REF_7SEPT`) on the main pipe as redrawn: the layout survives the pipe (the west still converges on its south-west corner, 28.2 km) and the maze came from the engine's later additions. `W13/tmp2/` is **W13 temp 2, the constructable layout**: W13's engine laid the engineer's way, the outfall as the target, sub mains first on the straight streets, the smaller streets hung on them, nothing optimised, a pocket only where 12 m cannot reach. 42 sub-networks, one block each, sub mains 69.9 km, 2,637 chambers, deepest 16.36 m, 16 over 12 m, all in the two sub-networks that go to the works, whose inlet at 323.0 m lies above their ground (the west 3.5 m under, the settlement around the works 10.7 m under); the cut rule does not reach them because the depth is on the way to the works, not in a basin. Drawing `W13/tmp2/dxf/W13_A_tree.dxf`, numbers `W13/tmp2/run/stage_a.json`, QGIS group `Claude W13 temp 2 (constructable layout)`. Open for the engineer: how the 12 m rule cuts a sub-network whose depth is not in a basin, and the works' inlet.

**2026-09-09: temp 2 is accepted and frozen, the work goes on in `W13/tmp3`.** The engineer accepted the temp 2 network as it is. Its logic is `W13/tmp2/docs/W13_TMP2_DESIGN_LOGIC.md` (also in `tmp3/docs`): nine rules in his words, the target the outfall and the main pipe, what was kept from W13's logic and what was dropped, and the engine's own choices flagged. `W13/tmp3/` is the clone and reproduces temp 2 to the digit; QGIS group `Claude W13 temp 3`. Standing instructions: the route to the works below 12 m stays as is, to be discussed later; subnetworks first, the overall network when all are prepared; nothing added to the logic without telling the engineer first. **W13 is still the live design folder; the engine's line is tmp2 → tmp3.**

**2026-09-11: temp 3 carries the plots' own flows, the gradient grid and the self-cleansing audit.** Plots: W14's `PLOTS_load` for everything. Sizing on `Q_ULT`, Merrimack above 100 properties, Peltier at or below; gradients at Table 11 or rounded up to 0.05 % (0.025 % from DN500); the audit on `Q_2030` × 0.61 (connected houses, no infiltration, 0.75 m/s or Mara at 1 Pa with no floor) gives **70 % of the length needing washing**, every such pipe DN200 under 1.29 l/s. Tiers in the guideline's names, `ROLE` in the engine's. One outlet moved: the 59 km around the works now links to the main pipe across a farm that PLOTS_load calls agricultural; its arrival there is unchecked because main-pipe joins are not floored. Logic `W13/tmp3/docs/W13_TMP3_DESIGN_LOGIC.md` (tmp2's stays frozen).

**2026-09-12: temp 3 is accepted and frozen; the engine folder is `W13/tmp4`.** The engineer accepted temp 3 as it is (plot flows, gradient grid, audit, QGIS style). `W13/tmp4/` is the clone and reproduces it to the digit; its logic is `W13/tmp4/docs/W13_TMP4_DESIGN_LOGIC.md` (no rule changed since tmp3), the layout gate `python gate_vs_ref.py tmp3`, and the open questions are listed in `W13/tmp4/README.md`: the pockets brainstorm (discharge chamber and length cap, pump rate, station site, rule 9, rising-main route, what to report), the metered farm south of the works that moved 59 km from the STP to a main-pipe link, and Stage C still to build (real lay, chambers, hydraulic check, overall network and inlet, pumps, crossings). **The QGIS project is `Hydraulic/QGIS/QGIS 2621 ibri sewer stp2.qgz` since 2026-09-12** (`stp.qgz` is the older copy); in `execute_code` never chain `renderer().categories()[i].symbol()`, bind names or style through a QML. **W13 is the live engine line: tmp2 → tmp3 → tmp4; W14 holds the loads and the report.**

**2026-09-12 (later): the tractive-force minimum gradient is checked with a 1.5 l/s design floor and never regrades a pipe.** The engineer re-read G203 p27 ("steeper of the two approaches shall be the minimum gradient; at the head, tractive force"): the head is defined nowhere, so it is read as the reach where 0.75 m/s cannot be reached at the minimum gradient, every DN200 under about 12 l/s; with the peak flow floored at Mara's 1.5 l/s the tractive slope never passes 0.47 %, a DN200 always passes at Table 11, and a bigger pipe keeps Table 11 and carries the answer as an attribute (`S_TRAC_PC`, `S_TRACL_PC`, `TRAC_OVER`). The floor and the curve `W13/tmp4/img/mara_curve.png` go into the concept report for NWS to confirm. The low-case audit (washing list) is unchanged. Rule 7 of `W13/tmp4/docs/W13_TMP4_DESIGN_LOGIC.md`.

**Nothing is lost.**

| Where | What |
|---|---|
| tag + branch `w12-archive-2026-09-06` (pushed) | all 902 tracked files of W10–W12 |
| `Hydraulic/Backup/2 Quarantine_W10_W12/` | the KNOWLEDGE those six weeks produced — the as-built calibration (20 gates measured from the built 2006 network), the depth-versus-pumping economics, the hierarchy rules read from NAMA's own manhole IDs, two solver studies, the W8/W10 post-mortem, the 22-check auditor and the test suite. **`CLAUDE.md` rule 14: not to be used unless the user asks for it by name** |
| `Hydraulic/Backup/1 Claude.rar` | the engineer's own full copy, including the outputs and the 25 GB of terrain products |

**Judge anything in quarantine by one question: does it help W13 beat W8 on W8's own
5.51 km²?** The failure being corrected was adding machinery faster than engineering, and
re-importing it wholesale would repeat that exactly.

**What is NOT settled and was deliberately dropped in the revert:** the cascade-pump rule and
the one-duty-pump rising-main rule (the engineer's instruction — re-decide them when the new
logic raises them), and four wadi/lateral rows in `02_DESIGN_CRITERIA.md`. Two of those four
are cited guideline values, not assumptions, and are waiting on the engineer to put back:
G203-p30 *"must be avoided"* / p33 *"shall be avoided"* for wadi presence, and p52 §8.2.4
**1.5 m cover at a wadi crossing**. Also verified from source on 2026-09-07 and worth carrying:
p33 §4.6.3 makes the 0.5 m cover a **conditional exception requiring concrete protection,
measured above the protection**, and makes **excavation COST** — not depth — the trigger for a
pumping station, with 10–12 m only a *recommendation* to be checked with pipe manufacturers.

---

## The pre-revert page, unchanged below

Read this before trusting any file in the repo. The job has grown, so this page says
plainly which document is live and which is a record of past work.

## Live — use these

| File | What it holds | Last checked |
|---|---|---|
| `CLAUDE.md` | working rules, folder map, current state | 2026-08-19 |
| `W14/` (2026-09-10) | population, saturation, load and the **Concept Design Report R2** (`W14/report/R2/`, built; `W14/deliverables/` packaged); W13 is pipe laying only. R1 in `W9/report/R1/` is superseded | 2026-09-10 |
| `W13/analysis/CRT_accounts_identified.csv` (copy in W14) | the 499 CRT electricity accounts placed by use from public data (110 still unresolved); shapefile in `W13/shp/` | 2026-09-09 |
| `W13/analysis/IDENTIFIED_PROJECTS.md` | identified projects and special consumption: the two industrial estates, the army camp, Ibri View, the tanker sources outside | 2026-09-09 |
| `W13/docs/CONCEPT_NOTE_SATURATION_AND_LOAD.md` | the note for the concept report: meters → categories → land use → ratio → saturation → load, and how it goes into the report | 2026-09-10 |
| `W13/shp/PLOTS_load.shp` + `W13/docs/W13_LOAD_AND_GROWTH.md` | the load table: every plot's meters, people, water, sewage, and population/Qadf for 2030, 2055, ultimate 2073, all settlements full (class v6: per-settlement occupancy floor 4 cap 6.12 — `OR_S` on every plot, table in `W13/analysis/occupancy_by_settlement.csv` — base 2024, NDVI groves, home-shaped capacity, spread by capped area; the workbook gives growth rates only); replaces `PLOTS_derived_class.shp` | 2026-09-09 |
| `_BRAIN/07_PROJECT_STATE.md` | the one-page orientation: data, doctrine, progress | 2026-08-19 |
| `_BRAIN/02_DESIGN_CRITERIA.md` | every design number with its guideline page | 2026-08-19 |
| `W5/docs/CRITERIA_UPDATE_R1.md` | the register of rules agreed 18–19 Aug and what is built | 2026-08-19 |
| `W8/report/W8_Sewer_Network_Design.docx / .pdf` | **the current report**, built on every run | 2026-08-23 |
| `W8/py/` | **the design code** that produced the current outputs | 2026-08-23 |
| `W8/shp/ dxf/ img/ sewergems/ run/` + `W8_sewer_design.kmz` | **the current design outputs** | 2026-08-23 |
| `W8/docs/LEARNING_FROM_ASBUILT.md` | the three-tier structure learned from NAMA's manhole IDs | 2026-08-23 |
| `W7/docs/CALIBRATION_vs_EXISTING.md` | the first calibration — gradients and depths match; still valid, but it MISSED the hierarchy | 2026-08-20 |
| `TUTORIALS/T02/` | **T02 — Hydraulic Design of a Gravity Sewer**: every design constraint, each value read back from the source PDF with its page | 2026-08-23 |
| `SHP/Main Pipe/Main Pipe.shp` | **the trunk is an INPUT now** — the user's drawing, not derived | 2026-08-20 |
| `TUTORIALS/T01…docx` | how the flow and load are worked out — **Rev 4** | 2026-08-19 |
| `TUTORIALS/T03_R01/` | **the concept-design method**: every equation, parameter and pipeline, with the economic and financial section built out | 2026-08-29 |
| `W9/report/R1/` | **the current client deliverable** — Concept Design Report Revision 1. R0 is frozen in `R1/`'s sibling folder as issued | 2026-08-31 |
| `W9/report/*.py` | the report build: `data_facts` (every measured figure), `charts`, `qgis_maps`, `flow`, `omml`, `notes` | 2026-08-31 |
| `W9/docs/CONCEPT_REPORT_STRUCTURE.md` | the 43-section structure, each section mapped to its T03_R01 method section | 2026-08-29 |
| `W9/analysis/W9_ele_landuse.md` | the tariff-to-category crosswalk, OR 5.32 and its coverage check | 2026-08-30 |
| `W9/analysis/W9_ghs_check.md` | GHS-POP against our population data — internal reliability read, cross-check only, never a load input | 2026-09-01 |
| `W9/analysis/W9_PIAD_financial_review.md` | how NWS actually appraises an investment (two PIADs, read end to end) — the CAPEX/OPEX rule sets to reuse, and eleven defects not to inherit | 2026-09-01 |
| `_SETUP/skills/report-writing/SKILL.md` | how a deliverable report is built here — install it with `bootstrap.ps1` | 2026-09-01 |
| `W9/py/make_appraisal_figure.py` | the appraisal method figure — A3 landscape, used by the report and by T03_R01 | 2026-09-01 |

## Superseded — keep for the record, do not quote as current

| File | Why it is out of date |
|---|---|
| `W7/**` | W7 placed the main pipe correctly and got to zero pumping stations, but had NO sub-main tier: 30 things touched the main pipe, 14 of them carrying under 100 properties. Superseded by W8 |
| `W6/**` | W6 guessed the trunk by picking streets near a described line. It found 2.1 km in the southern corner and needed 4 pumping stations. Superseded entirely — do not quote its pumping or depth numbers |
| `W5/**` | W5 was the run before the trunk was placed and before the 12 m depth limit was enforced. Its design has chambers past 12 m that the audit did not report. Do not quote its chamber, depth or pumping numbers |
| `W4/**` (all of it) | W4 was the first design pipeline. W5 replaces it. The one live file is `W4/shp/ELE_accounts.shp`, which W5 still reads |
| `W4/report/*`, `W4/docs/METHODOLOGY.md`, `W4/docs/PLAN.md` | describe the W4 design: 1,655 chambers, 89.5 km, one property per plot, OR 6.0 |
| `W2/report/*` | the R1 concept screening report, built on 36 zones and OR 6.0 |
| `W3/analysis/*` | still valid as analysis, but every population figure uses OR 6.0 and one property per plot — rescale before reuse |
| `TUTORIALS/T01…pdf` | **PDF is still Rev 3** — Word was open when Rev 4 was built, so only the .docx was refreshed. Re-export when Word is free |

## Numbers that changed, so old documents disagree with new ones

| Item | Old (W1–W4) | Now (W5) |
|---|---|---|
| People per property | 6.0 assumed | **5.0**, set by the client team |
| Properties per plot | 1.0 assumed | **counted from electricity accounts**, 1.4 average |
| Farms | no sewage load at all | **the farming carries none, the houses on it do** |
| Dual carriageways | merged into one corridor | **excluded entirely**, trunk included |
| Sewage per plot | 1.03 m³/day | **0.86 m³/day per property**, several properties per plot |
| Deepest chamber | 21.3 m (W6 first pass — the check was skipping them) | **11.88 m**, 12.00 m is a hard limit with no exemption |
| Pumping stations | "5 SLS spots" (W5, counted from deep pockets) | **4 real stations** with lift, rising main and duty flow for each |
| Road source | `W1/shp/roads_study.shp` | `SHP/Road centerline 2` with the `dual` column |
| People per property | 5.0 set by the client team (W5) | **5.32 DERIVED** 2026-08-30 from settlement population ÷ counted domestic properties |
| Existing sewer in the study area | "310.9 km of gravity sewer" | **111.6 km built, 199.3 km proposed** — the dataset holds two networks (2026-08-30) |
| Existing force main | "33.2 km" | **10.0 km built, 23.2 km proposed** |
| Existing treated effluent main | "45.7 km" | **none built** — all 45.7 km is proposed |

## Still open

| Item | Waiting on |
|---|---|
| Drag value for self-cleaning (1 Pascal assumed) | NWS — 1,124 pipes need steeper gradients if it is 2 |
| Plastic pipe wall class | NWS / PAM-SPC-207 |
| Floor areas, staff and pupil numbers | derived for now; colleague's treated land-use data will replace them |
| 143 junctions with a sharp inlet | they need a purpose-made chamber with a curved channel — no room to turn the pipe. Marked `SWEPT_CH=1` in `W6_manholes.shp` |
| 240 house connections over 50 m | their only frontage is a dual carriageway, where no pipe may be laid. Needs your call: a sewer in the service road, or a local collector |
| The trunk line | placed on the western + southern edge as you asked; confirm the alignment against `W6_pipes.shp` |
| Cascading the 3 pumping stations | all sit within 1.5 km, so detail design can look at feeding one into another |
| SewerGEMS comparison | your model run against the package in `W5/sewergems/` |
| Renardet cost data: financial submissions, cost estimates and priced BoQs from completed projects | A colleague. **These become the primary unit-rate basis** and demote the PIAD-derived rates to a cross-check. Until they land, the cost estimate rests on 2019-vintage NWS rates escalated to the tender date |
| Treated effluent price and offtaker | NWS. It is our one genuine volumetric revenue stream, and its volume is capped by irrigation demand rather than by what the plant treats |
| Capacity of the built 2006 network | the survey — no diameter or invert level is recorded on any built gravity segment, and NAMA's own remark says the data is for reference only |
| Whether the SUREKHA proposed alignments are a client commitment | **Largely answered from the data itself (2026-09-01): NOT approved.** The 29,038 m³/d plant record carries `HYPERLINK` = *"RG Master Plan (Concept Design) not approved yet. Kindly consult Asset Planning for any NOC's"*, `STATUS` = Design, `SOURCE` = ASSET PLANNING, `REMARKS` = ZONING_Treatment_Solutions. It sits at 444376 E 2563217 N — about 120 m south of the existing 1,800 m³/d plant, effectively the same site. Still worth written confirmation from NWS, but treat it as an unapproved concept, not a commitment |
