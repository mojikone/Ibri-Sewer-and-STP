# What is current, and what is not — checked 2026-09-02, end of session

**READ THIS FIRST, THEN `07_PROJECT_STATE.md`, THEN `08_DESIGN_PHILOSOPHY.md` BEFORE LAYING
OUT ANY NETWORK.**

## The state in one paragraph

**W11a is a COMPLETE design that runs end to end** — scope, corridors, trunk, hierarchy,
chambers, tertiary connections, flows, levels and sizes, stations, packages, and a full
export (shapefiles, DXF, KMZ, profiles, nine schedules, SewerGEMS). Run it with
`s1 → s2 → s3 → s4 → s5 → s5b → s5c → s6 → s7 → s8 → s9` from `W11a/py`, then
`python run_audit.py W11a`. **It audits 18 pass / 4 FAIL / 0 cannot-run**, against W10's
3 / 12 / 7. The zero is the point: every check can now be *evaluated*.

| | W10 | W11a |
|---|---|---|
| Audit | 3 pass / 12 FAIL / **7 cannot run** | **18 / 4 / 0** |
| Network | 1,883 km in 7,919 pieces | **1,731.7 km, 247 components, one outfall each** |
| Chambers | — | 49,624, DN200–1700 |
| Connected load | — | **89.9 %** |
| Stations | 19–21 | 226 demanded by the depth cap |

## THE BIGGEST OPEN DEFECT — and it is not in the audit table

**42.5 % of the network length (737.7 km) drains UPHILL.** 7,061 m of cumulative climb
along the flow path against 10,177 m of descent. A reach carrying flow uphill buys its rise
in depth at the minimum gradient for its whole length, then pays again giving the depth back.

The diagnostic is the drop-structure count: **the design wants 2,449 vortex drop shafts
where NAMA's built network has 37.** No levelling arithmetic fixes this. It is a **stage 4
tree-orientation** problem and it is the next substantial job. Philosophy §4 now states the
rule and requires the quantity to be reported.

## The four audit failures, all real and all named

| Check | What |
|---|---|
| H1 / R3 | 8 reaches run along a dual carriageway (0.36 km) |
| H10 | 2,984 inlets below 90° — each needs a purpose-made chamber with a swept channel |
| R4 | 295 reaches run ALONG a wadi; 11 cross one unscheduled; **1,170 cannot be decided** because the far bank lies outside the hazard grid |

## Also open, not audited

- **The 226 stations are located, not designed.** `Q_DUTY_LS = 0` on all of them, zero rising
  mains published, `LAND_M2` a flat 100 m² constant. Nothing routes a rising main for a
  station that is a gravity *terminal*.
- **Two study-area boundaries are in use** — 439.8 km² (`MoHUP_DATA/Project_boundary.shp`)
  and 531.4 km² (`Study area/Project Boundary.shp`). Eight figure modules normalise against
  the smaller one; the pipeline scoped itself on the larger. **One must be chosen.**
- **The trunk figures (FT01–FT11) draw stage 3's intermediate**, not the published trunk.
- **The design review report's numbers are stale** — built before the last three fixes
  (R4's probe, the measured crossing angle, DN_SERIES). Rebuild with
  `python W11a/report/build_review.py`.
- **OPEN-S2-2**: stage 2 publishes its own displaced copy of the trunk (669 corridors,
  80.27 km, 58 pieces), which is why the weld must strip 5.8 km of shadow.

## Waiting on a HUMAN — nothing else moves these

**The engineer decides:**
1. **72 trunk chambers sit in a class-5/6 wadi**, with ~500 m of the trunk running down it
   near E450 050 / N2 569 400. It is the client's own drawn alignment and is an INPUT.
2. **Which study boundary** is the project's.
3. **Go / no-go on the stage-4 tree re-orientation.**

**NWS must supply:**
- **Full-coverage 50-year flood mapping.** 52 % of wadi samples fall outside the grid, so
  every wadi statement is about the other half.
- **The design tractive stress τ.** 91 % of self-cleansing rests on an assumed 1.0 Pa
  (GAP-9); at 2.0 the required gradient rises **2.35×** and every depth changes.
- **The existing works inlet invert.** The trunk is laid to its own 319.94 m aOD, 8.78 m
  below ground, unconfirmed — at the deepest and most expensive end of the scheme.
- **Confirmation of DN1400–2400** (their own tables print these sizes; extending the series
  cleared 168 d/D failures).
- Decision on the **236 plots whose only frontage is a dual carriageway**.

## What was retracted today — do not re-quote these

| Retracted | Truth |
|---|---|
| "W10 has 310 loops" | **Zero** at any tolerance a GIS would use. 311 appears only at a 2.5 m snap |
| Infiltration 1,259 L/s | **14.5 L/s.** Summing per-reach values counts every upstream km once per downstream reach |
| 1,051 chambers on wadi ground | **2,354** — the old figure predated stage 5 minting the chambers |
| "30 % of load fails the 45 m rule" | The rule owns **8.59 %** |
| `ANGLE_DEG = 90°` on 3,290 crossings | **Fabricated.** Measured: min 0.00°, 23 under 45° |
| H1a cited G201-p86 for banning chambers | That is a **valve-chamber** clause on a force main. The authority is G203-p30 §4.4.1 / p33 |
| H1a's 1.5 m cover as a guideline value | It is the **force-main** figure (G203-p52 §8.2.4). Adopted for gravity as OUR decision |

## Live — use these

| File | What it holds | Last checked |
|---|---|---|
| `CLAUDE.md` | working rules, folder map, current state | 2026-08-19 |
| `_BRAIN/07_PROJECT_STATE.md` | the one-page orientation: data, doctrine, progress | 2026-08-19 |
| `_BRAIN/02_DESIGN_CRITERIA.md` | every design number with its guideline page | 2026-08-19 |
| `_BRAIN/08_DESIGN_PHILOSOPHY.md` | **how to arrive at a GOOD design** — objectives in priority order, the order of design, layout/levelling/sizing philosophy, the cap-and-veto ladder for pumping, our constraint ranking, and the two-pass method. Binding on every network design | 2026-09-02 |
| `W11a/py/w11a/audit.py` | **the auditor — 22 checks, and the specification.** A check that cannot run is a FAILURE, not a blank. It audits PUBLISHED layers, never an in-memory model | 2026-09-02 |
| `W11a/py/w11a/contract.py` | the layer schemas, field by field, with the audit check each field feeds | 2026-09-02 |
| `W11a/py/s1…s9` | the stage modules. 1 scope · 2 corridors · 3 trunk · 4 hierarchy · 5 chambers · 5b tertiary · **5c flows (new)** · 6 levels · 7 stations · 8 packages · 9 export | 2026-09-02 |
| `W11a/shp/W11a.gpkg` | the canonical layers: `corridors`, `nodes`, `reaches`, `connections`, `servicing` | 2026-09-02 |
| `W11a/run/EVIDENCE_snap_tolerance.md` | why W10's "310 loops" was never a design defect | 2026-09-02 |
| `W11a/report/W11a_Design_Review_R1.docx` | **the design review** — what was wrong with the rules, where the design stands, and the recommendations. Internal, not for issue | 2026-09-02 |
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
