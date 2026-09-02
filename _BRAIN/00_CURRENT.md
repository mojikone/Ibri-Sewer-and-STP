# What is current, and what is not — checked 2026-09-02

**READ THIS FIRST, THEN `07_PROJECT_STATE.md`, THEN `08_DESIGN_PHILOSOPHY.md` BEFORE LAYING
OUT ANY NETWORK.**

## Where the project actually stands, in six lines

1. **`_BRAIN/08_DESIGN_PHILOSOPHY.md` is new and binding** — 232 lines, rules only. `02` says
   whether a design is legal; `08` says how to make it good. Read it before any layout work.
2. **W10 is complete but NOT ISSUABLE** — four compliance failures, listed below. Its
   *findings* stand and are worth reading; its *design* is not.
3. **W11a has started.** Stage 0 — the auditor — is built and runs. Nothing else exists.
4. **The TOR requires ALL plots to be served** (scope p4 item 3). An earlier working
   assumption that 31 settlements would be dropped is **withdrawn**. The question is which
   *system* serves each, not whether.
5. **97 % of W10's self-cleansing rests on the tractive route**, whose τ the guideline never
   gives (GAP-9, assumed 1.0 Pa; at 2.0 the required gradient rises 2.35×). This is the
   largest open assumption in the hydraulic design.
6. **Waiting on two deliveries**: the draftsman's final treated lines, and the GIS expert's
   clean land-use data. The scripts are being purified so both drop straight in.

## Live — use these

| File | What it holds | Last checked |
|---|---|---|
| `CLAUDE.md` | working rules, folder map, current state | 2026-08-19 |
| `_BRAIN/07_PROJECT_STATE.md` | the one-page orientation: data, doctrine, progress | 2026-08-19 |
| `_BRAIN/02_DESIGN_CRITERIA.md` | every design number with its guideline page | 2026-08-19 |
| `_BRAIN/08_DESIGN_PHILOSOPHY.md` | **how to arrive at a GOOD design** — objectives in priority order, the order of design, layout/levelling/sizing philosophy, the cap-and-veto ladder for pumping, our constraint ranking, and the two-pass method. Binding on every network design | 2026-09-02 |
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

## W10 status — NOT COMPLIANT, do not issue (2026-09-01)

The full-area design in `W10/` is complete and its **findings stand**, but audited against
W8's own check registry it fails four ways:

| Failure | Extent | Rule |
|---|---|---|
| Trunk **surcharged** — DN1200 at 1,361 L/s and 0.075 % passes the flow at no depth | 5 reaches, **2.80 km** | G203-p27 Tab 10 |
| Over the d/D limit but passing | 66 reaches, 10.68 km | G203-p27 Tab 10 |
| Below the **1.30 m minimum cover**, worst 0.30 m | 169 reaches, **45.92 km** | G203-p33 4.6.3 |
| Pipe **along a dual carriageway**, plus 47 unscheduled crossings | 21 reaches, 1.67 km | project rule 7 |

Also: 1,233 m³/d (1.7 %) of load never enters the network (assignment radius drops it
silently, against the zero-silent-drops doctrine); `RoadTreatment` was called with
`units=None, sampler=None`, so its traffic-link, orphan-link and roundabout-guard steps
became no-ops — 34 collapsed rings intersect a registered plot; and every analysis output
except the pipe layer predates the wadi fix, so the optimisation study's baseline is 219
breaches where the shipped design has 239.

**Cause, in one line: W8's engineering was carried into W10 and W8's auditor was not.**
Detail: `W10/docs/research/W8_W10_POSTMORTEM.md`, which also specifies a 59-check contract
for W11a. **W11a builds the auditor FIRST and runs it against these layers on day one; the
failing table is the specification.**

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
| Capacity of the built 2006 network | **PARTLY ANSWERABLE NOW (corrected 2026-09-01).** The claim that no diameter or invert is recorded was wrong: it read `N_DIAMETER`, which is 0 on every built record, while `OUT_DIAMET` carries the real value. Measured on the ESRI shapefile: `OUT_DIAMET`, `US_INVERT_`, `DS_INVERT_` and `MATERIAL` are populated on **2,142 of 3,267 built pipes (66 %)**, and the split is by package — 5A-2/3/4/5 are 100 % complete, 5A-1 is 0 %. A hydraulic assessment of ~68.8 km is possible today. The survey is still needed for 5A-1 and for condition. NAMA's reference-only remark stands |
| Whether the SUREKHA proposed alignments are a client commitment | **Largely answered from the data itself (2026-09-01): NOT approved.** The 29,038 m³/d plant record carries `HYPERLINK` = *"RG Master Plan (Concept Design) not approved yet. Kindly consult Asset Planning for any NOC's"*, `STATUS` = Design, `SOURCE` = ASSET PLANNING, `REMARKS` = ZONING_Treatment_Solutions. It sits at 444376 E 2563217 N — about 120 m south of the existing 1,800 m³/d plant, effectively the same site. Still worth written confirmation from NWS, but treat it as an unapproved concept, not a commitment |

---

## W11a — the live iteration (started 2026-09-02)

| | |
|---|---|
| **Built** | `W11a/py/w11a/audit.py` — the stage 0 auditor. 22 checks: H1–H15 from the philosophy, 4 regression tests, 3 provenance checks. `python W11a/py/run_audit.py` runs it against W10 |
| **Result on W10** | **2 pass, 13 FAIL, 7 cannot run** (`W11a/run/audit_W10.csv`). That table is the specification for W11a |
| **Not built** | Everything else. Stages 1–9 of the build order in `W10/docs/research/W11a_BUILD_BRIEF.md` |

**Two architectural rules the auditor enforces, both learned from W10's failures:** it audits
the **published layers**, never an in-memory model; and **a check that cannot run is a
failure**, not a blank.

## W10 — NOT ISSUABLE, but its findings stand

| Failure | Extent | Rule |
|---|---|---|
| Trunk **surcharged** | 5 reaches, 2.80 km | G203-p27 T10 |
| Over the d/D limit | 66 reaches, 10.68 km | G203-p27 T10 |
| Below **1.30 m minimum cover** | 169 reaches, 45.92 km | G203-p33 |
| Pipe **along a dual carriageway** | 21 reaches, 1.67 km | project rule 7 |

Plus 131.7 km on wadi ground, a published layer in 7,919 disconnected pieces, and no `TIER`,
no laid gradient, no inverts, no constraint provenance.

**Cause, in one line: W8's engineering was carried into W10 and W8's auditor was not.**

## The nine research documents — read these before redesigning anything

`W10/docs/research/` — `HIERARCHY_RULES.md` (what generates the tiers, measured from the
as-built) · `CORRIDOR_QUALITY.md` (how trustworthy each of the four corridor sources is) ·
`WHAT_TO_SEWER.md` (the marginal settlements) · `DEPTH_VS_PUMPING.md` (the economics; manning
is 86 % of a station's life-cycle cost) · `SEWERGEMS_DESIGN_METHOD.md` and
`DESIGN_ENGINES_COMPARED.md` (no solver chooses a layout) · `W8_W10_POSTMORTEM.md` (the
59-check contract) · `DELIVERABLE_SPEC.md` (concept vs preliminary vs detailed, page-cited) ·
`PHILOSOPHY_REVIEW.md` (the adversarial review) · `W11a_BUILD_BRIEF.md` (the build order).

## Settled during 2026-09-01/02, do not re-litigate

- **Oversizing a pipe to lay it flatter is PROHIBITED** — G203-p29, and Ten States §33.43
  independently. An optimiser built on it was withdrawn (`W10/py/p3_optimise.py`, kept with a
  warning).
- **No solver chooses a layout** — SewerGEMS, InfoDrainage, Civil 3D, InfoWorks all size and
  level what you hand them, and none will ever propose a pumping station.
- **The cap-and-veto ladder** — 12 m of **cover** is the cap, with two distance-bounded exits
  (recovers within 500 m, or reaches the outfall within 1,000 m). Everything past 12 m is
  flagged. This reversed "12 m with no exceptions" deliberately, on 2026-09-02.
- **The station count** is 19–21 depending on the funnel; the number is far less meaningful
  than **total lift**, because distance-clustering measures breach density.
- **A lifting station is a commissioning device**, not only a depth device.
- **BAT is deliberately undecided** — 2,231 properties, 1,752 m³/d, 22–25 km out. Both
  conveyance and a satellite works go into the options appraisal.
