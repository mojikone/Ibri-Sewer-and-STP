# What is current, and what is not — checked 2026-08-31 (W9)

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
| `_SETUP/skills/report-writing/SKILL.md` | how a deliverable report is built here — install it with `bootstrap.ps1` | 2026-08-31 |

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
| Capacity of the built 2006 network | the survey — no diameter or invert level is recorded on any built gravity segment, and NAMA's own remark says the data is for reference only |
| Whether the SUREKHA proposed alignments are a client commitment | NWS. They carry project code SUREKHA, the same code as the 29,038 m³/d plant record marked "Design" |
