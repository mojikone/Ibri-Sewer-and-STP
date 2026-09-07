# What is current, and what is not — checked 2026-09-07

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
