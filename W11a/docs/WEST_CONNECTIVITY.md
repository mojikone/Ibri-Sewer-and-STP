# The western leg — connect it to the works, or give it its own?

**W11a, 2026-09-02.  Measurements by `W11a/report/west.py`; figures FL01, FL02, FL03 in
`W11a/report/img/`.  This is an options paper, not a decision — philosophy §8a puts the
choice in the life-cycle appraisal.**

---

## The uncomfortable finding first

**The west is not a closed basin.  On the ground it drains to the existing works, and a
single gravity main gets there with no pumping station and 8.59 m of cover at its deepest.**

W10's `WEST_LEG.md` says the opposite — *"every route out crosses the same high point …
11.93 m above the start"*, and all three of its routes came back **impossible**.  That
finding was measured **on corridors**, not on terrain, and it does not survive being measured
on the ground:

| Measured from the west basin low point (442 092 E 2 569 064 N, 332.50 m) to the existing works | Answer |
|---|---|
| Lowest elevation any route **over the terrain** must cross | **332.50 m — the start cell itself.  No climb at all** |
| Lowest elevation any route **on the stage-2 corridors** must cross | 338.34 m — **5.44 m of climb**, on a 14.4 km route |
| W10's answer, on the corridor set it had | 344.83 m — 11.93 m of climb |

Three numbers for one journey.  They differ because they are measurements of three different
things: the ground, today's corridor layer, and last month's corridor layer.  **Only the
first is a fact about Ibri.  The other two are facts about our own data.**

And the same split runs through the whole catchment.  For every corridor node in the west I
computed the minimum static lift needed to reach the works — the bottleneck elevation minus
the node's own ground, a floor that no gradient, diameter or alignment can beat:

| | needs no lift | median lift | p90 | max |
|---|---|---|---|---|
| **What the ground demands** | **1 004 of 1 809 nodes (55.5 %)** | **0.01 m** | 0.19 m | 21.54 m |
| **What the corridor network demands** | 311 (17.2 %) | 12.01 m | 22.26 m | 32.63 m |

**The corridor layer adds a median 11.32 m of lift that the ground does not ask for.**
By load: **56 % of the west's ultimate flow needs no lift at all over the terrain, and 97 %
needs 2 m or less.**  On the corridors, 18 % needs none and 55 % needs more than 10 m.
Figure **FL03** is that comparison.

### Why I do not fully trust either corridor number, and neither should the reader

The corridor layer is torn.  Sampling 92 pairs of west nodes 300–800 m apart:

* median detour **1.37×** — normal for a street grid;
* but **10 %** of pairs need more than **3×**, and **6.5 %** cannot be reached at all inside
  8 km;
* worst named case: `N0004664` (442 331 E 2 570 165 N) and the west low-point node
  `N0001775` are **1 130 m apart** and need **21 198 m of corridor** to connect — **18.8×** —
  with the high point of that route at (449 626, 2 569 514), **7 km east of both of them**.

That is what produces the 360.6 m bottleneck carried by 918 west nodes and 4 314 m³/d of
load.  It is a defect of the corridor layer, not a hill.  **Every gravity verdict computed on
this corridor set — W10's, mine, and stage 3's — inherits it.**  The terrain measurement is
the only one that does not, which is why it leads this note.

---

## 1. What the west actually carries

Measured two ways that share no code:

| | Network catchment (stage-2 corridor graph) | Stage 3's own assignment |
|---|---|---|
| method | every plot to its nearest corridor node; every node to the nearer set of trunk chambers | every in-boundary plot's ultimate Qadf to its nearest **trunk chamber**, accumulated downstream |
| ultimate Qadf | **8 583.7 m³/d** | **9 297.7 m³/d** |
| properties | 10 937.9 | 11 866.3 |
| plots | 6 238 | — |
| population | 45 491 | — |
| peak flow | — | **219.0 L/s** (PF 2.024, Merrimack), DN900 |

The two agree within **8 %**, which is about what two different catchment rules should
differ by.  Take **8 600–9 300 m³/d, roughly 11.5–12.4 % of the network's 74 701 m³/d.**

**The west is ordinary urban fabric, not a marginal fringe.**  256.7 km of corridor for
10 938 properties is **23.5 m per property** against **22.6 m network-wide** — within 4 % of
the average.  Nothing about its density argues for treating it as a special case.

And it is **not** a Remote Area on any of G201-p80 §8.1's four tests: it is inside the core
conurbation (stage 1 `check_west_basin` puts the basin low point inside SID 18), it is far
under 25 km from the built network, and it has 45 491 residents and 6 238 plots against the
guideline's 500 / 100.

---

## 2. Can it reach a works by gravity, and at what depth

### Yes — 6.771 km, DN900 at 0.100 %, deepest cover 8.59 m, no station

I asked the question the way it has to be asked for a sewer: not *"is there a low route"* but
*"is there a route on which the pipe stays between 1.30 m and 12.00 m of cover the whole
way"*.  Dijkstra by path length over the 10 m terrain, with the cover window as an
admissibility filter, scanning the starting cover.  **It connects.**

| | |
|---|---|
| length | **6.771 km**, west basin low point → existing works |
| pipe | **DN900** — from `hydra.size_pipe` on stage 3's own published peak, 219.2 L/s |
| gradient | **0.100 %** — the flattest gradient on the project's 0.05 % laying step that clears Table 11's **0.75 mm/m** floor at DN ≥ 900 (G203-p29, read from the source: *"900 and above — 0.75"*) |
| invert | 330.20 → **323.43 m aOD**, 6.77 m of fall |
| cover | 1.30 m at the head, **8.59 m at its deepest**, 4.22 m at the works |
| lifting stations | **zero** |
| self-cleansing | **the velocity route** — 0.83 m/s at peak, above the 0.75 m/s minimum (G203-p26).  It does **not** depend on the tractive method, so GAP-9's undecided τ does not bite here |

**It is robust to the DEM resample.**  Re-read along the same alignment on the raw 0.5 m
grid: cover **1.21 – 8.61 m** against the 10 m grid's 1.30 – 8.59, mean difference
**+0.000 m**, sd **0.021 m**, **0 of 587 points past the 12 m cap**, 3 points 0.09 m under the
1.30 m minimum — a metre of alignment tweak, not a design problem.

It also **fits the works.**  Stage 3's trunk arrives at the existing works at 319.94 m aOD.
This main arrives at 323.43 m — **3.49 m above it**, so the two can tie in soffit to soffit
without conflict.  Both still depend on OPEN S3-3, the existing works' inlet invert, which
nobody has given us.

Figure **FL02**, right panel.

### And here is what is wrong with it

**It is not on a corridor.**  Median 113 m from the nearest corridor, maximum 410 m,
**90 % of it more than 50 m from any corridor**.  It crosses **32 registered plots**.  It is
a **new wayleave across open ground**, not a street sewer — the same kind of arrangement as
the built 10.0 km rising main, but it needs land, and land is a client question.

Philosophy §4 says a corridor with neither a built street nor a platted reserve is not a
corridor.  A **trunk main on a purchased easement** is a different animal from a street
sewer, and the philosophy does not currently say whether one is admissible.  **That is a gap
in §4 and it should be closed explicitly rather than by silence.**

**The wadi answer is half missing.**  The 50-year hazard grid has **no answer on 51.8 %** of
the alignment.  On the tested half, **0.35 %** of samples reach class ≥ 4 — our wadi proxy,
and *ours*: hazard classes 4/5/6 are a **project assumption** standing in for the guideline's
*"Locating pipelines and associated chambers in wadis or areas subject to washout during
heavy storms must be avoided"*, which is a scour criterion, not a flood-hazard one.
Independently, the alignment sits a **median 183 m** from any mapped stream
(`Streams NSA 2m`) and only **7.5 %** of it is within 25 m of one, so it is not running down a
channel.  **Not proof.  Better than nothing, and honestly half-blind.**

*(Checked while writing this: the philosophy's H1a citations are right, and one of them is
stronger than H1a claims.  G203-p30 §4.4.1 item a reads **"must be avoided"**; p33 §4.6.2 and
p36 repeat the same sentence with **"shall be avoided"**.  H1a item 2 records reading
"avoided" as "prohibited" as a project decision — p30's "must" carries part of that weight
already, and H1a could say so.)*

**It crosses dual carriageways.**  **4 crossings of a dual centreline, with 12 of the 587
ten-metre samples inside the 6 m band** — about 30 m of contact per crossing, which is a
crossing and not a run along, so it is legal under project rule 7.  They still have to be
designed as crossings, and the grid path is a feasibility probe, not an alignment.

---

## 3. What pumping it needs if it is sent east instead

This is the design as it stands.  Stage 3 took the drawn alignment and could not make the
western leg gravity.  Its own reading of the line (`s3_trunk.py` docstring): the leg *"falls
into a basin at chainage 2.5 km (ground 332.6 m) and then runs 5.3 km UPHILL to 343.8 m"*.
Its answer, published in `W11a_trunk.gpkg`:

| | |
|---|---|
| gravity | 8.155 km, of which **0.720 km is the provisional S3-1 connector** |
| deepest cover | 11.82 m — 0.18 m under the cap |
| lifting stations | **2** (of the 3 on the whole 85.5 km trunk) |
| static lift | **13.03 m** at (445 113, 2 567 695) + **11.69 m** at (447 698, 2 567 165) = **24.73 m** |
| rising main | 521 m total |
| static-lift energy | **277 125 kWh/yr** — ρgQH at ultimate Qadf, **η 0.65 ASSUMED** (no project or guideline value exists), **friction excluded** because the mains are sized on pump duty at stage 6 and no duty exists yet.  A floor, not an estimate |

Figure **FL02**, left panel, shows it: the invert dives to 324 m, is lifted 13.03 m, runs east,
and is lifted again by 11.69 m.

**And the second of those two stations stands on a line nobody has drawn.**  It sits on the
879.82 m provisional connector that closes OPEN S3-1.  **11.69 m of the west's 24.73 m of
static lift — 47 % — therefore rests on provisional geometry.**  Section 5 shows that fixing
the geometry does not recover it.

---

## 4. A west satellite works

**Philosophy §8a says carry it, and I am not going to close it here — but the arithmetic that
can be done, can be done.**

**What the guideline rules out.**  A *package plant* is not an option.  G201-p83 §8.4.1 caps
decentralized compact treatment units at *"communities with a population between 50-5,000
inhabitants"*.  The west has **45 491** — **9.1× the ceiling**.  A west satellite would be a
conventional works of about **8 600–9 300 m³/d**, roughly **five times** the existing Ibri
plant's 1 800 m³/d, on land that has to be found, consented and bought.

**What the guideline lets us compare.**  G201-p84 §8.4.2 gives, for remote-area schemes,
*"Energy consumption of approximately 0.8 kWh/m³ shall be assumed"* and *"Annual operations
and maintenance costs estimated at 5% of Investment CAPEX"*.  Applying the energy ratio to
the west's ultimate flow — and **labelling it an extrapolation**, because the west is not a
remote area and the ratio is stated for small remote schemes:

* 8 583.7 m³/d × 365 × 0.8 kWh/m³ ≈ **2.51 GWh/yr of treatment energy**.

That number is roughly the same wherever the sewage is treated, so it very nearly **cancels**
between a west satellite and the central works, and what does not cancel is the
**conveyance**: **277 MWh/yr for the two lifting stations, zero for the gravity main.**  On
energy alone the ranking is gravity-to-central, then pumped-to-central, then satellite — with
the satellite penalised by a second set of process trains, a second consented site, a second
sludge route and a second set of operators, which is exactly the 86 %-manning result in
`W10/docs/research/DEPTH_VS_PUMPING.md`.

**I have deliberately not put money on any of this.**  The Renardet cost data is still
outstanding (`_BRAIN/00_CURRENT.md`); the only rate set in the repo is the Seeb **potable
water** scheme's, and `W9/analysis/W9_PIAD_financial_review.md` catalogues eleven defects in
it including rates that did not move between 2019 and 2023.  A monetary comparison built on
that would be a plausible invented number, which is the worst outcome available.

---

## 5. OPEN S3-1 settled: the gap is 879.82 m, and it can be closed on real streets

**The build note calling this "a 2 m drafting gap" is wrong, and stage 3 is right.**
Re-measured here from the input drawing itself (`SHP/Main Pipe/Main Pipe.shp`, 54 polylines,
85.491 km):

* the western leg is polyline **7 865.87 m** long;
* its downstream end at (447 084.15, 2 567 523.06) is **879.823 m** from the nearest point on
  the rest of the drawing, at (447 843.73, 2 567 079.06);
* the **whole line's** closest approach to the rest of the drawing is the same **879.823 m**,
  so this is not an endpoint artefact — no part of the west leg comes nearer than that.

**What closing it properly requires — and this is good news.**  The shortest route across the
gap that stays on published corridors is **1 270.55 m**, **1.44×** the straight line, and it
is **92 % built street**, with **0 m on wadi ground** and **0 m on a dual carriageway**.  So
the draftsman's line can be replaced by a real street alignment for **391 m of extra pipe**.

**But it does not remove the station.**  The street route rises to **346.72 m**, against the
west leg's downstream end at 344.12 m — it climbs 2.6 m, slightly more than the straight line
does.  **The 11.69 m lift at (447 698, 2 567 165) is a consequence of the direction of
travel, not of the provisional geometry.**  Sending the west east costs that station whether
the connector is drawn properly or not.

**Recommended wording for the register:** *S3-1 is a measured 879.82 m gap, not 2 m.  A
1 270.55 m street alignment closes it and should be confirmed by the draftsman.  Closing it
does not remove either west lifting station; only changing the direction of the west's
outfall does.*

---

## 6. The options, as options

| | What it is | Pipe | Stations | Static lift | Conveyance energy | Deepest cover | The thing that could kill it |
|---|---|---|---|---|---|---|---|
| **W-A** as drawn | west leg east to the trunk junction | 8.155 km gravity + 0.52 km rising main | **2** | 24.73 m | 277 MWh/yr | 11.82 m | 0.72 km of it is a line nobody has drawn; 0.18 m of margin against the 12 m cap |
| **W-B** as drawn, gap fixed | W-A with the connector on real streets | +0.39 km | **2** | 24.73 m | 277 MWh/yr | 11.82 m | fixes the drawing, not the pumping |
| **W-C** gravity south | new trunk main on a wayleave, west low point → existing works | **6.771 km** DN900 | **0** | 0 | **0** | **8.59 m** | **land** — 90 % off-corridor, 32 plots crossed, and half the wadi answer missing |
| **W-D** west satellite works | a conventional works of ~8,600–9,300 m³/d | west reticulation only, not designed here | not measured | not measured | ~2.5 GWh/yr treatment (extrapolated ratio) | not measured | 9.1× the guideline's package-plant ceiling; a second site, second sludge route, second crew |

**My reading, and it is a reading, not a result.**  W-C is the option that best satisfies the
TOR's own objective — scope p12: *"The entire layout shall take into consideration the
topography of the area in order to avoid pumping and utilize gravity as much as practically
possible."*  It removes two of the three stations on the entire trunk and it takes 3.23 m off
the deepest chamber in the west.  It is bought with a land acquisition, and land is the one
cost I cannot estimate and the client can.  **W-C should go into the appraisal as a real
option, and it currently is not in it at all.**

I am **not** recommending W-D be dropped — §8a is explicit that both go forward — but nothing
I measured supports it, and the guideline's own size band argues against calling it a
decentralised solution.

---

## 7. What needs a client or NWS decision

1. **Is a trunk main on a purchased wayleave across open ground acceptable?**  W-C stands or
   falls on this and on nothing else hydraulic.  If the answer is no, W-A/W-B is the design
   and the west keeps its two stations.
2. **Land at the alignment.**  6.771 km of easement, 32 registered plots crossed, four dual
   carriageway crossings.  Someone has to say whether that corridor can be acquired.
3. **Confirm the western leg's real alignment (OPEN S3-1).**  879.82 m, not 2 m.  A
   1 270.55 m street route is available; the draftsman should confirm or replace it.
4. **The existing works' inlet invert (OPEN S3-3).**  Both W-A and W-C arrive at levels we
   have set ourselves — 319.94 m and 323.43 m aOD.  Neither is confirmed.
5. **Whether the west is carried as a separate option at all**, or folded into the central
   system.  §8a says it is an appraisal question; this note gives the appraisal its inputs.

## 8. What needs data we do not have

| | |
|---|---|
| **The 50-year hazard grid does not cover the study area.** | **51.8 % of the W-C alignment has no wadi answer**, and the grid's nodata is −9999.0 — finite, so a naive `np.isfinite` guard scores it as clear ground.  Full coverage is a data request |
| **A scour-depth study.** | Our wadi test is a flood-hazard class standing in for a scour criterion.  Even where the grid answers, it is answering a different question |
| **Ground survey on the W-C alignment.** | The 0.5 m VRT is bare-earth photogrammetry.  A 6.8 km trunk on a new easement needs a real survey before any level is issued |
| **Renardet unit rates.** | Nothing here is costed, and nothing here can be until they land |
| **NWS's station establishment cost.** | Philosophy §5 says nothing past the cap is final without it; W-A sits 0.18 m off the cap |
| **A corridor layer that is not torn.** | 10 % of adjacent west node pairs need a >3× detour, 6.5 % are unreachable inside 8 km, and the worst case is 18.8×.  Until that is repaired, every corridor-based gravity verdict in the west is unreliable — including the ones in this note |

---

## 9. What this study did not do, so nobody over-reads it

* **The terrain bottleneck is a necessary condition, not a sufficient one.**  "No cell on the
  route is higher than the start" says a gravity route is not forbidden by the ground.  It
  says nothing about cover, corridors, land or wadis.  Only the W-C alignment search applies
  the cover window, and it applies it on **one** route, from **one** collection point.
* **The internal collection tree for the west is not designed here.**  W-C proves the
  *outfall* is not the constraint.  Whether the west's own streets can deliver 8 584 m³/d to
  the basin low point is a stage 4/5 question, and it is gated on the corridor repair.
* **The W-C alignment is a 10 m grid path, not an engineered line.**  It is a feasibility
  proof.  A designer would smooth it, move it off the 32 plots, square the dual-carriageway
  crossings and re-level it on survey.
* **The catchment split is one rule among several.**  "Nearest set of trunk chambers along the
  corridor graph" is defensible and it is not the only defensible rule; stage 3's independent
  rule gives 8 % more load.  Neither is a zone in the sense of project rule 8.
* **η = 0.65 is mine, not anybody's.**  So is the 12.00 m cap read as hard rather than as
  G203's *"recommended … approximately 10 - 12m"*, and so is reading *"must be avoided"* as
  *prohibited*.  All three are labelled where they are used, and the 277 MWh/yr moves
  inversely with η — at 0.55 it is 327 MWh/yr, at 0.75 it is 240.

---

## Figures and files

| | |
|---|---|
| `W11a/report/img/FL01_west_catchment.png` | the west catchment, the trunk as drawn with its two stations and the provisional S3-1 line, the gravity alignment, and the untested half of the hazard grid |
| `W11a/report/img/FL02_west_profiles.png` | the two profiles side by side — as drawn, over two lifts; and the gravity run, on the cover window |
| `W11a/report/img/FL03_west_lift.png` | the west's load against the lift it needs, measured over the ground and over the corridors |
| `W11a/report/img_doc/FL01…jpg`, `FL02…png`, `FL03…png` | the document-sized copies, built with `img_for_doc.py`'s own rule.  `img/*.png` is gitignored, so **these are the ones that reach anyone reading the repo remotely** |
| `W11a/report/west.py` | every measurement in this note.  `python west.py` re-measures and redraws; `--figs` redraws from cache |

*The `FL` prefix is new.  The bare `F##` series is the report's own figure numbering and
`F20`/`F21` were already taken by the STP-options work, so these three took a topic prefix
rather than risk a collision.  Renumber them into the report series when the figure list is
settled.*

**Sources behind every number here**, as stamped on the figures:
`W11a/shp/W11a.gpkg [corridors]` 26 450 rows, written 2026-09-02 14:46 ·
`W11a/shp/W11a_trunk.gpkg [reaches / nodes]` 754 / 758 rows, 2026-09-02 13:15 ·
`W11a/run/s3_trunk_stations.csv` 3 rows ·
`W10/shp/W10_plot_loads.gpkg [plot_loads]` 64 071 rows ·
`Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt` ·
`Data/04 Lekhuwair/Hazard_T50y.tif` ·
`Hydraulic/SHP/Main Pipe/Main Pipe.shp` ·
`Hydraulic/SHP/Streams/Streams NSA 2m.shp`.

**Guideline values, each read back from the PDF today:**
G203-p29 §4.3.1 Table 11 — *"900 and above 0.75"* mm/m, and *"Sewers shall not be oversized
to facilitate flatter slopes"* ·
G203-p29 §4.3.2 — maximum gradient set by 3.0 m/s ·
G203-p26 — 0.75 m/s minimum self-cleansing velocity ·
G203-p33 §4.6.3 — *"The minimum depth for sewer pipes shall be 1.3 m to the crown"* and
*"The recommended maximum cover … is approximately 10 - 12m … Where the cost of excavation
becomes prohibitive the Engineer shall incorporate pumping stations into the design"* ·
G203-**p30 §4.4.1 item a** — *"Wadis and Flood-Prone Areas: Locating pipelines and associated
chambers in wadis or areas subject to washout during heavy storms **must** be avoided"*, and
**p33 §4.6.2** and **p36** repeat the sentence with *"shall be avoided"* ·
G201-p80 §8.1 — the four Remote Area tests ·
G201-p83 §8.4.1 — package plants *"for communities with a population between 50-5,000
inhabitants"* ·
G201-p84 §8.4.2 — *"Energy consumption of approximately 0.8 kWh/m³ shall be assumed"* and
*"Annual operations and maintenance costs estimated at 5% of Investment CAPEX"* ·
Scope p12 — *"avoid pumping and utilize gravity as much as practically possible"*.

**Project assumptions used here, none of them guideline values:** hazard classes 4/5/6 as the
wadi test · 12.00 m as a hard cap rather than G203's *"recommended … approximately 10 - 12m"*
· *"must be avoided"* read as *prohibited* · **η 0.65** wire-to-water (277 MWh/yr; 328 at
0.55, 240 at 0.75) · the 10 m DEM resample (checked against the raw 0.5 m grid and reported)
· 50 m as the distance at which a route stops counting as "on a corridor".
