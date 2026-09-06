# What is current, and what is not — checked 2026-09-06

**READ THIS FIRST, THEN `07_PROJECT_STATE.md`, THEN `08_DESIGN_PHILOSOPHY.md` BEFORE LAYING
OUT ANY NETWORK — and `09_INHERITANCE.md` + `10_ASBUILT_CALIBRATION.md` BEFORE STARTING A NEW `W#`.**

## W12 IS THE LIVE DESIGN (started 2026-09-06). W11b IS SUPERSEDED.

**W12 is a COPY of W11b, revised — not a rewrite.** 28 files inherited plus W11a's auditor;
package renamed `w11b` -> `w12`; all compile and import. The user settled the rule on
2026-09-06: *"where did I say do not carry the scripts from the previous working folder to the
next? It is obvious the work is growing, not starting from scratch."* Sixteen inherited
docstrings said "W12 BORROWS NOTHING" and were rewritten — that sentence is the invention that
cost two iterations of lost work.

### W12 is a CONCEPT-STAGE design. Everything stays pure hydraulic until the layout is fixed.

| Rule (user, 2026-09-05/06) | What it means |
|---|---|
| **Follow the ground slope** | Laid slope is a clamp: never flatter than the guideline minimum, never steeper than the slope that meets max velocity, otherwise the ground's own fall |
| **Drops carry a reason** | Fall the pipe cannot take goes to a drop at a manhole, each flagged with why it exists |
| **Outfall at the lowest point** | A subnetwork joins the main pipe at the lowest point where it MEETS it. **No subnetwork crosses the main pipe and grows past it.** Where there is no street at the low point, connect at the nearest usable place and record the distance from the true low point |
| **Main-pipe chambers nudge to road crossings** | Within the spacing band, so connections arrive square rather than oblique |
| **Plot connectability, not house connections** | One simple gravity calculation per plot — the connection leaves BELOW ground, runs to a CHAMBER, and loses fall over its own length. Flag what cannot connect, with what it would take |
| **Naming** | `I-S03-SM-M012` — town letter (articles dropped; both towns extend on a clash), subnetwork, tier, element, zero-padded. Elements outside a town take the first downstream town's letter |
| **Switched OFF until the concept is approved** | House connection design (riders, laterals, PCC/HCC), motor sizing, life-cycle costing, the excavation-vs-pumping break-even, phasing and packages, SewerGEMS export, swept-channel detail |

**The as-built calibration is now a `_BRAIN` file**, not a folder file: `10_ASBUILT_CALIBRATION.md`
— 20 gates measured from the built 2006 network, six corrections to numbers in our own live
documents, and the three data requests to NWS. It also settles that **a terminal is legal if it
is the main pipe OR a pumping station with a designed rising main** (NAMA's 5A-1, a third of the
built network, ends 6,754 m short of the works), which retires the standing criticism of W11b's
18 subnetworks that stop short.

---

## Superseded — W11b (2026-09-03)

W11b borrowed nothing — every module lives under `W11b/`. Run it from `W11b/py`:
`s1_roads → s2_orient → s3_hierarchy → s4_chambers → s5_flows → s6_levels → s7_pumps →
s8_export`, then `make_overview.py` for the KMZ and DXF.

| | W10 | W11a | **W11b** | NAMA built |
|---|---|---|---|---|
| Gravity network | 1,883 km | 1,731.7 km | **1,489.7 km** | 95.4 km |
| Chambers | — | 49,624 | **56,930** (38.2/km) | 34.2/km |
| **Vortex drop shafts** | — | **2,449** | **41** (0.028/km) | **37** (0.585/km) |
| **Draining against the ground** | — | **42.5 %** | **26.3 %** | **34.1 %** |
| Climb ÷ descent | — | 0.747 | **0.416** | 0.483 |
| Below minimum cover | 45.9 km | 0 | **0** | 35.9 % of its length |
| Over the d/D limit | 66 | 168 | **0** | — |
| Over 3.0 m/s | — | 0 | **0** | — |

**On the two measures that say whether a layout follows the ground — drop shafts and uphill
drainage — W11b is better than the built network.** That is the first time any iteration has
managed it.

## THE FIX THAT MATTERED, and the lesson behind it

The engineer spotted it by eye: the built network has **no pumping station in the test area**,
W8's design of the same ground has none, and W11b published **three**.

They were **leftovers**. The solver works in passes — level, sweep the crowns, set the drops,
relay the runs to recover fall, then test the depth cap and add a station where it is
breached. **It only ever ADDED.** A station placed on pass 1, before any of that recovery,
survived to the end even where the ground turned out to have enough fall all along.

**W8 already knew**, and said so in a comment two weeks earlier: *"a pump placed in an earlier
pass may not be needed once diameters change, and a stale flag would double-count stations."*
It cleared every flag at the top of every pass. W11b did not carry the lesson.

Traced along the worst path into each test-area station:

| | verdict |
|---|---|
| PS006 | ground gives **23.1 m** of fall, the pipe needs **19.5 m**. Gravity works. Deepest pipe on the run **3.92 m** against a 12 m cap |
| PS030 | **nothing** draining into it |
| PS086 | **nothing** draining into it |

`solve()` now prunes. Stations **83 → 14 demanded**, and **0 in the test area**.

## Open defects, measured and named

| What | Size | Whose |
|---|---|---|
| **The two station counts disagree** — levelling demands 14, the pump stage designed 47 | 33 | s7 reads a list from before the prune |
| **15 of those 47 have nothing draining into them** | 15 | marked on both drawings |
| **42 components discharge with more than half their catchment BELOW the outlet** | 389.5 km, worst outlet 22.8 m above its own low point | s2/s3 — an outfall in the wrong place |
| 18 subnetworks do not reach the main pipe | worst 1,873 m short | drawn on the DXF with the distance in words |
| Plots that cannot drain to their chamber on gravity | 5,521 of 53,018 | G203-p18 Tab 5 |
| Areas the network does not reach | 31 areas, 7,355 plots | boundaries drawn on both files |
| Deepest excavation past the 12 m cover cap | 19.78 m | exits excuse it; needs review |
| Chambers per km slightly above the built band | 38.2 against 33.3–36.8 | more chambers than NAMA builds |
| `s8_export` fails its own contract, and cannot write while QGIS holds the file | — | drawings are built from the stage layers instead |

## What W11b has that no earlier iteration did

**Tests.** Six files, written against the bugs that actually happened — two constants for one
quantity; no-data read as safe ground; **a published column that is constant where it should
vary**, which would have caught a fabricated crossing angle the moment it was written; a
length field that disagrees with its own geometry; and dead code with a runtime bound.

**Pumps that are designed** rather than located: duty flow, lift, wet-well volume, motor size
and life-cycle cost, plus 47 rising mains. A survey of 839 sewer repositories found nothing
upstream that sizes a wet well or selects a pump — it came from the Oman standards directly.

## Already investigated — do not repeat, and do not copy

**Two upstream sewer-design repositories were evaluated on 2026-09-03**
(`W11b/docs/UPSTREAM_METHODS.md`, 37 kB, claim by claim against the source).

**DO NOT COPY `SWMManywhere`'s topology code.** Its `tarjans_pq` is *named* for Tarjan's
optimum branching and its docstring says so, but the code is **Prim's algorithm on a reversed
graph** — there is no cycle contraction anywhere in the repository, and cycle contraction is
the whole of Chu–Liu/Edmonds. Proved by running the function verbatim against
`networkx.minimum_spanning_arborescence`: **36–57 % worse**, and on one graph it sends a
branch straight to the outfall instead of letting it run downhill into a neighbour — the exact
fault we are trying to cure. Its default path (`OutfallDerivation.method = "separate"`) is not
a branching at all; it is nearest-outfall shortest path, which is what W10 and W11a already do.

**The IDEA is still right** — a true slope-weighted optimum branching is the right instrument
for the tree — and `networkx.minimum_spanning_arborescence` is correct and already a
dependency. But the estimate is sober: about **one uphill kilometre in twenty**, taking
climb ÷ descent from 0.747 to roughly 0.68–0.70 against the built network's 0.483. Worth
having; not the fix the idea was billed as.

`pysewer` (GPL-3.0, method only, never the code): its `needs_pump()` profile trace is clean
and its claims check out, but its pump penalty is a cliff rather than a trade.

**One idea worth recording because an independent team reached it too**: exclusions are
applied by DELETING the corridor before routing, never by pricing it. A penalty can always be
outvoted by a big enough number; a deletion cannot. We already do this.

## Waiting on a human

**The engineer decides:**
1. The **42 badly-placed outfalls** (389.5 km) — an outlet above its own catchment is a layout
   decision, not an arithmetic one.
2. The **18 subnetworks** that stop short of the main pipe.
3. The **31 unconnected areas** — serve them another way, or not at all.

**NWS must supply:** the design tractive stress τ (we hold 1.0 Pa, the engineer's decision,
flagged everywhere — at 2.0 the required gradients roughly double); the existing works inlet
invert; and confirmation of DN1400–2400.

**Settled by the engineer, do not re-open:** τ = 1.0 · flood no-data is DRY HIGH GROUND ·
the 72 trunk chambers in a class-5/6 wadi are an ACCEPTED risk, flagged · the road DXF is
clean, use all lines · no crossings manufactured for now.

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
