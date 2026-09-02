# DESIGN PHILOSOPHY — the rules for laying out a sewer network

**`02_DESIGN_CRITERIA.md` says whether a design is LEGAL. This says how to make it GOOD.**
Where the two conflict, `02` wins. Scope: the gravity foul network, property connection to
works inlet, with its lifting stations and rising mains.

Evidence, research and the history of how these rules were arrived at live in
`W10/docs/research/`. **This file is rules only.**

---

## 1. The six objectives, in priority order

1. **It complies** — a design that breaks a "shall" is not a design
2. **It can be built** — fingers, bends, loops and kilometre-long reaches are not buildable
3. **It can be operated** — NAMA runs it for fifty years; it must read like their own network
4. **It can be built in stages** — every package commissionable on its own
5. **It costs least over 25 years** — life-cycle, not capital
6. **It is hydraulically minimal** — smallest pipe, flattest legal gradient, least depth

**Six is last.** It is what a solver optimises by default, and it is the least important.

---

## 2. The order of design

| # | Decide | Why here |
|---|---|---|
| 0 | **The auditor** | Write the checks before the design |
| 1 | **What is served** | Deciding scope after design is how you sewer empty desert |
| 2 | **The corridors** | Wadi and dual-carriageway exclusions apply HERE, not in the router |
| 3 | **The trunk** | End to end, at main diameter, before anything drains to it |
| 4 | **The hierarchy** | Sub mains on through-streets, then laterals chained into them |
| 5 | **The chambers** | Spacing, junctions, bends, drops, heads at gates |
| 6 | **Levels and sizes** | Only now. This is the part software does |
| 7 | **The packages** | Phases and contracts, seams at lifting stations |

**Stage 3 before stage 6.** A trunk that emerges from accumulated flow is not a trunk.

---

## 3. Hard constraints — these never yield

Where two cannot both be met, the answer is one of four **physical** things — a station, a
drop chamber, a re-route, or **not serving that plot** — never relaxation of the constraint.

*H4 is the one hard constraint with a written exit, in §5. It never yields to another
constraint; it yields only to its own stated exits, and every use is flagged.*

| | Constraint | Source |
|---|---|---|
| **H1** | No pipe along a dual carriageway; no pipe or chamber in a wadi. Crossings perpendicular and scheduled | project rules 7, 8 |
| **H2** | Capacity ≥ discharge, within the d/D limit | G203-p27 T10 |
| **H3** | Minimum cover 1.30 m to crown, on the reach's **own** outside diameter | G203-p33 |
| **H4** | **Maximum cover 12 m** — exits only via §5 | G203-p33 |
| **H5** | Minimum velocity **0.75 m/s at peak flow** (preferred 0.90) | G203-p26 |
| **H6** | Gradient ≥ the steeper of Table 11 and the tractive minimum. *This is the starting point; **H5 is the test** — Table 11 is a full-bore derivation and the weaker of the two* | G203-p26–29 |
| **H7** | Maximum velocity **3.0 m/s gravity, 2.5 m/s rising main** | G203-p27, p50 |
| **H8** | Diameter set by flow — **never** by the depth wanted | G203-p29 |
| **H9** | Minimum sizes and materials by tier | G203-p22 T6 |
| **H10** | Inlet angle **≥ 90°** | G203-p30 |
| **H11** | No reverse gradient; laying tolerance **20 mm** | G203-p29 |
| **H12** | Chamber spacing within Table 12 | G203-p30 |
| **H13** | **Uniform slope between successive manholes** | G203-p29 |
| **H14** | An **existing** structure's invert is fixed and the design yields to it. Tie in **soffit to soffit**, never invert to invert | practice |
| **H15** | The network is a **forest** — zero loops, checked on the published layer | project rule |

**Every reach records which constraint set its diameter and which set its gradient.**
"Depth" is not an admissible answer for a diameter.

## 3a. Preferences — these yield, in this order

**P1** the *same* gradient carried across consecutive reaches where practical, on 0.05 %
steps — **H13 already requires uniformity *within* a reach; P1 extends it across a run** ·
**P2** straight between chambers ·
**P3** long runs, few junctions · **P4** sub mains on through-streets · **P5** invert or crown
matching at a chamber · **P6** minimum depth.

A preference never overrides a hard constraint. **P1 is never bought at the price of a
pumping station** — if rounding a gradient creates one, relax the rounding on that run.

---

## 4. Layout

- **The hierarchy is generated, not recognised.** A **lateral** is one unbranched street run
  (median ~130 m, cap 920 m). **At most 3 laterals and 750 m of flow path before a main.** A
  **sub main** is a collector route defined by its outlet. Two measures describe it — about
  21 % of the length of the catchment it drains, and one per 4–10 km of network. **Where they
  disagree, the outlet governs**: a sub main exists because a catchment needs one way out, not
  because a ratio was met. The **trunk** is traced from the outfall backwards.
- **Expect roughly 270 km of sub main** on this network. A design producing 20 km is wrong on
  sight. Target tier shares near the as-built: lateral 66 %, sub main 18 %, trunk 5 %.
- **Vocabulary:** G203 calls a 45 m tertiary pipe a "lateral"; NAMA's tokens call a street run
  one. **State which vocabulary any tier rule uses.** Governing set: rider, lateral, main, sub
  main, trunk main.
- **Chamber spacing (H12) and run length (P3) are different rules.** A 500 m run has five
  chambers at 100 m centres. Report run length as a **maximum**, never a median.
- **No fingers** — a dead-end reach under ~60 m serving nothing is pruned or absorbed. *Ours,
  on cost grounds; no adoption standard requires it.*
- **A head starts at the gate** — on the road, at the foot of the perpendicular from the first
  plot's centroid.
- **10 m clearance** between a branch start and the chamber it joins.
- **The corridor must be legal** — a public reserve of stated width, **3 m minimum horizontal
  clearance** to other utilities, and a shared trench puts the other utility on a separate
  bench on undisturbed soil (G203-p33).
- **A platted reserve with nothing built on it is a legitimate corridor at a saturation
  horizon — but it is not a street.** It carries `CONFIDENCE = provisional`, its pipes are
  identified separately in every drawing and schedule, and it is never reported as existing.
  A corridor with *neither* a built street *nor* a platted reserve is not a corridor: route
  elsewhere or do not serve.
- **Where no legal corridor exists at all, the plot is not served.** That is the fourth
  resolution in §3, and it is a scope answer, not a routing one.

---

## 5. Levels, and when to pump

- **Lay as shallow as H3 allows.** Depth is bought back nowhere.
- **On steep ground the pipe does not follow the cliff.** Hold the gradient and take the
  difference at a **drop chamber** — ramped not vertical, **external to the manhole**,
  required where the invert difference exceeds **600 mm** (G203-p30), vortex shaft beyond 2 m.
  **Never a drop used to dodge a station.**
- **Publish the LAID gradient**, with the minimum beside it. A layer carrying only the minimum
  cannot be checked.

**The cap-and-veto ladder — the economics is third, never first:**

1. **CAP** — cover reaches 12 m → station, unless an exit below applies
2. **VETO** — a chamber that cannot be maintained (no plant access, confined space with no
   rescue route, under a live carriageway) → station. Not a term in a sum
3. **ECONOMICS** — only now: is a station cheaper over 25 years than digging on?

Layers 1 and 2 can only ever **add** a station. The economics can only make you pump
**earlier**, never later.

**Past the cap, two exits — either alone is sufficient:**

- the cover **recovers within 500 m**, or
- the run **reaches the outfall** — works or an existing station — **within 1,000 m**

**Everything past 12 m is flagged**, with its depth, its length, which exit allowed it, and
what it waits on: a **manufacturer's rating** for that cover, and **NWS's station
establishment cost**. G203 gives no depth because that is a pipe question, and defines
"prohibitive" only as *more than a station costs*. Neither is settled, so nothing past the cap
is final.

*This reverses "12 m with no exceptions" — deliberately, on 2026-09-02, bounded by distance.*

---

## 6. Sizing, and the rising mains

- **Diameter follows flow; gradient follows diameter.** Oversizing to lay flatter is
  prohibited — G203-p29, and Ten States §33.43 independently.
- **Size on the ultimate horizon; check self-cleansing at start-year flows.** A pipe that
  scours in 2055 and silts in 2030 has failed.
- **Septicity is a design driver.** Long flat lightly-loaded runs at Omani temperatures are
  the H₂S combination. Report **retention time per route**. Air flows with the water at 5–30 %
  of water velocity (G203-p31), so **ventilation follows from layout** — decided in the review
  pass, not afterwards.
- **Rising mains** are sized on **pump duty**, not arriving flow; duty comes from the wet-well
  cycle. 0.75–2.5 m/s, air valves at summits, washouts at low points. A rising main is
  **anaerobic by definition**, so its discharge chamber is a septicity problem, not a pipe end.
- **A station is also a commissioning device.** One that makes a package independently
  buildable earns its place even when the trench would be cheaper — the only case where
  objective 4 beats objective 5.

---

## 7. Two passes, then the audit

| Pass | What it does |
|---|---|
| **1 — strict** | Every rule applied mechanically. Compliant, and ugly |
| **2 — review** | What a person would fix: sub mains onto through-streets, fingers absorbed, bends out of mains, stations onto package seams, runs merged. Feed the cost back into pass 1's layout |
| **3 — audit** | Re-run every check. Pass 2 must not have broken pass 1's compliance |

**One solver pass is not a design.** Bentley say so themselves: *"Automated design is not
meant to provide perfect results."*

**No solver chooses a layout.** SewerGEMS, InfoDrainage, Civil 3D and InfoWorks all size and
level what you hand them, and none will ever propose a pumping station — it deepens forever
instead. A solver can referee our hydraulics and never our routing. **The pumping decision is
ours, before the solver runs.**

---

## 8. The audit

**The checklist is H1–H15 and P1–P6** — one check per constraint, generated from the tables
above so a rule cannot exist without its check. Each recomputes its constraint independently,
from the designed values and the raw terrain, and carries its source.

Plus four regression tests, because these are the failures that made a previous run
non-issuable: **surcharged pipe · reaches below minimum cover · pipe along a dual carriageway ·
pipe on wadi ground**. And three provenance checks: **every published number from one
function · no re-filtered metric · no stage silently doing nothing.**

**Blocking:** any breach of a "shall"; any breach of a settled project rule without a stated
derogation; any published number that cannot be traced; any check that cannot run.
**Reporting only:** economic trades the guideline itself frames as trades, as-built
calibration, and assumption sensitivities.

---

## 8a. Two scope decisions, resolved as working assumptions

Both are reversible, both are the designer's to propose and the client's to confirm, and
both are recorded here so the design is not blocked waiting for them.

**What is served.** Sewer the **106 settlements** that cost 12.9–15.4 m of exclusive sewer
per property. **Price** the 17 marginal ones (21.1 km, 0.75 % of the load) as a separate
option. **Do not sewer** the 31 that cost 204 m per property for 0.36 % of the load — carry
them as a decentralised item instead. Evidence: `W10/docs/research/WHAT_TO_SEWER.md`.

**BAT.** 2,231 properties, 1,752 m³/d, 22–25 km out, above every decentralised ceiling in the
guidelines. **Do not choose — carry both**, conveyance and a satellite works, into the options
appraisal. The options doctrine already requires three per system, and this is exactly the
kind of question it exists to answer. Deciding it here would pre-empt the appraisal.

---

## 9. Where the evidence is

`W10/docs/research/` — the hierarchy rules measured from the as-built, the corridor quality
assessment, what to sewer, the depth-versus-pumping economics, the solver comparison, the
W8/W10 post-mortem, the deliverable specification, the adversarial review of this document,
and the long-form draft this replaced. `TUTORIALS/T02` — every constraint with its guideline
page.

**Nothing in this file is a measurement of past work. Rules only.**
