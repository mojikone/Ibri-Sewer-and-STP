# AS-BUILT TARGETS — what NAMA actually built, as numbers W11b is checked against

Measured 3 September 2026 from `Data/Received/09-RECEIVED/NAMA/IBRI/WW/SHIP/`.
Every figure below is reproduced by `python W11b/py/w11b/asbuilt.py`.
Nothing here is quoted from W7 or W8; those two documents were read first and then
re-measured, and **three of their conclusions did not survive**.

---

## THE HEADLINE: "2,449 drop shafts against 37" compares a count with a count

**The 37 is right. I reproduce it exactly — 37 invert steps over 2.00 m across the built
network, every one of them at a junction.** But 37 sits in **63.2 km** of levelled sewer and
2,449 sits in **1,731.7 km**. Per km the two networks are:

| | built (NAMA) | W11a | ratio |
|---|---|---|---|
| vortex drop shafts per km | **0.585** | 1.475 | **2.5×** |
| per 1,000 chambers | **19.7** | 51.5 | 2.6× |
| length draining uphill | **34.1 %** | 44.3 % | 1.3× |
| ground climb bought, m per km | **4.06** | 4.24 | 1.04× |
| climb ÷ descent along the flow path | **0.483** | 0.747 | **1.5×** |

So the defect is real, and it is **two and a half times**, not sixty-six times. Three
consequences for how W11b is steered:

1. **A terrain-following network still runs uphill about a third of the time.** NAMA's does.
   Ibri sits on an alluvial fan cut by wadis; the road a sewer must follow does not run down
   the slope, and a lateral serving both sides of a street cannot. **A target of zero uphill
   length is unachievable and chasing it will buy pumping stations.** The achievable target
   is the built network's own: 34 %, and no worse than the worst package, 38 %.
2. **`climb ÷ descent` is the sharper test.** The length share barely separates the two
   networks (34 % vs 44 %); the ratio separates them properly (0.48 vs 0.75) because it
   weights a long climb by how much rise it actually buys. Use it as the stage-4 objective.
3. **W11a's climb per km is already at NAMA's rate (4.24 against 4.06 m/km).** Its problem is
   not that it climbs more; it is that **it descends much less** — 5.9 m/km against NAMA's
   8.4. It is laid across the contours where NAMA's is laid down them.

**And the rule the drops actually encode: all 37 sit at a junction, none on a straight run.**
NAMA never uses a drop to walk a main down a hill. It uses one only where a branch arrives
high and has to be let down into the main it joins. A design with drops on straight runs is
levelling its way out of a layout fault, and that single test is worth more than the count.

---

## What had to be thrown out before anything could be counted

| Filter | Rows | Length | Why |
|---|---|---|---|
| `STATUS = 'Design'` | 129 | **202.7 km** | SUREKHA proposals. The asset GIS holds two networks. Quoting a length without this filter more than triples it |
| Schematic rows | 2 | **16.12 km** | `L012750` 10,469 m at 317 m per vertex, `L012751` 5,648 m at 565 m per vertex. Both end at `5A-1-FL-STP` — they are the force main drawn into the gravity layer |
| **What is left: built gravity** | **3,265** | **95.45 km** | |

The schematic filter is a **measurement**, not a hard-coded pair of IDs: any row averaging
more than 100 m between vertices. The next-worst real pipe is 65 m per vertex, so the rule
is nowhere near marginal.

**Fields that are zero or null on every single built row** — this is the dataset where this
project has already drawn a wrong conclusion from an always-zero field, so the list matters:
`N_DIAMETER`, `UP_PIP_DEP`, `DS_PIP_DEP`, `SLOPE`, `P_CONDITIO`, `GROUND_TYP`, `MCLASS`,
`BED_MATERI`, `LINING_TYP`, `FLOOD_PROT`, `WATER_TABL`, `CONST_METH`. The real diameter is
`OUT_DIAMET`. There is **no condition data at all** — `P_CONDITIO` is 0 everywhere, so
nothing in this dataset says whether the 2006 pipes are still sound.

**Levels exist on 2,142 of 3,265 pipes — 63.20 km, 66.2 %.** The split is by package:
5A-2/3/4/5 complete, **5A-1 has none at all** (1,123 pipes, 32.2 km). Every level-derived
number below is measured on that 63.2 km and the sample is stated with it.

**Independent check that the recorded levels are real:** `US_GROUND_` against the 0.5 m
terrain VRT at the same point — median difference **+0.25 m**, 5th–95th percentile −0.50 to
+1.12 m. The ground levels are survey, not invention.

---

## The network in one table

| | |
|---|---|
| Built gravity | **3,265 pipes, 95.45 km** |
| Built force main (separate layer) | **9.99 km** — one metre in ten of this system is pumped |
| Manholes | **3,267** |
| Heads (no inflow) | 486 · **5.09 per km** |
| Junctions (2+ inflows) | 461 · **4.83 per km** |
| Terminals (outfalls) | **3** |
| Bifurcations | **1** (`5A-2-30-MH235`) — the built network is a tree, and so must W11b's be |
| Plots it fronts | 4,177 of 56,414 · **5,695 m³/d · 7.6 % of the 74,701 m³/d saturated load** |

---

## The targets

Bands are **the spread between construction packages**, not a guessed ±. The five packages
are five independent samples of the same designer's habits. A package needs 3 km of pipe to
set a geometry band and 5 km of *levelled* pipe to set a level band, so 5A-3 (3.5 km) does
not get to widen a band on its own.

| Target | As built | Band | Basis | Sample |
|---|---|---|---|---|
| **uphill length** | 34.10 % | ≤ 38.15 | MEASURED | 2,142 · 63.2 km |
| **climb ÷ descent** | 0.483 | ≤ 0.647 | MEASURED | 2,142 · 63.2 km |
| climb per km | 4.06 m/km | ≤ 5.08 | MEASURED (+25 % project tolerance) | 63.2 km |
| **vortex drops per km** | 0.585 | ≤ 0.605 | MEASURED | 37 · 63.2 km |
| vortex per 1,000 chambers | 19.71 | ≤ 21.06 | MEASURED | 37 |
| **vortex at a junction** | **100 %** | ≥ 100 | MEASURED | 37 |
| backdrops per km (0.60–2.00 m) | 1.329 | ≤ 1.700 | MEASURED | 84 |
| chamber spacing, median | 29.77 m | 26.85 – 30.30 | MEASURED | 3,265 · 95.4 km |
| chambers per km | 34.23 | 33.29 – 36.76 | MEASURED | 95.4 km |
| longest reach between chambers | 71.38 m | ≤ 100 | **G203-p30 Tab 12** | 95.4 km |
| laid gradient, median | 6.00 mm/m | 5.96 – 6.63 | MEASURED | 2,142 · 63.2 km |
| laid gradient, OD200 | 5.19 mm/m | info | MEASURED | 145 |
| reaches laid against the flow | 0 | ≤ 0 | MEASURED | 2,142 |
| cover to crown, median | 1.72 m | 1.34 – 2.07 | MEASURED | 2,142 · 63.2 km |
| cover, 90th percentile | 4.38 m | 2.82 – 4.48 | MEASURED | 2,142 |
| deepest cover | 8.19 m | ≤ 12 | **G203-p33 4.6.3** | 2,142 |
| **length below 1.30 m cover** | **35.9 %** | **≤ 0** | **G203-p33 4.6.3** | 63.2 km |
| trunk share of length | 5.78 % | 1.48 – 13.45 | MEASURED | 145 · 4.53 km |
| sub-main share | 16.61 % | 10.85 – 17.15 | MEASURED | 322 · 9.92 km |
| lateral share | 77.61 % | 71.57 – 81.37 | MEASURED | 2,798 · 81.0 km |
| lateral zones draining into another lateral | 87.69 % | ≥ 87.69 | MEASURED | 520 of 582 |
| joins per km of trunk | 4.64 | info | MEASURED | 21 joins · 4.53 km |
| run between junctions, median | 68.74 m | info | MEASURED | 945 runs |
| length on flood-hazard ground | 36.82 % | info | MEASURED | 95.4 km |
| length on wadi ground (class 4–6) | 4.40 % | info | ASSUMPTION | 135 pipes |
| **length along a dual carriageway** | **0.082 %** | ≤ 0.2 | MEASURED | 6 pipes · 78 m |
| **length below the OD 200 lateral minimum** | **61.5 %** | **≤ 0** | **G203-p22 Tab 6** | 95.4 km |
| built pipes over capacity, saturated load | 11.1 % | info | MEASURED | 2,137 |
| built pipes over capacity, today's load | 4.4 % | info | ASSUMPTION | 2,137 |
| **design tractive stress τ** | **1.0 Pa** | — | **ASSUMPTION** | GAP-9 |

**τ = 1.0 Pa is carried on every output of this module.** It is the engineer's decision of
3 September 2026 and NWS have not confirmed it. It gives shallower slopes, so shallower
pipes and fewer pumps. **If NWS return 2.0 Pa the required gradient rises 2.35× (2^1.23) and
every depth in W11b changes.**

---

## The four questions the brief asked, answered by measurement

### 1. Does the built network go shallower and steeper at a wadi? — **REFUTED, with a caveat**

| | median cover | median gradient | n |
|---|---|---|---|
| off hazard ground (class 0) | 1.64 m | 6.02 mm/m | 1,448 |
| on hazard ground (class 1+) | **1.92 m** | **5.94 mm/m** | 694 |
| on wadi ground only (class 4–6) | **1.19 m** | **6.18 mm/m** | **13** |

Taken over all hazard ground the built network goes **0.28 m deeper and 0.09 mm/m flatter** —
the opposite of the record's claim. The claim survives only inside classes 4–6, where cover
drops to 1.19 m and the gradient steepens, and **that rests on thirteen reaches**. Thirteen
is an anecdote, not a rule. Do not build a design rule on it; if a wadi rule is wanted, ask
NWS for the scour-depth criterion the guideline is actually pointing at.

What the built network *does* show clearly is that **G203-p30 4.4.1's "wadis must be avoided"
is read in practice as a risk to manage, not an absolute bar**: 36.8 % of the built length is
on mapped hazard ground and 135 pipes are in classes 4–6. That is the precedent behind the
engineer's decision to accept the 72 trunk chambers in a class-5/6 wadi.

Coverage caveat: the 50-year grid covers only **36.0 %** of built-pipe midpoints. The rest is
scored **dry high ground** by the engineer's decision of 3 September 2026.

### 2. How much runs along a dual carriageway? — **CONFIRMED: 0.082 %**

Six pipes, **78 m of 95.45 km**, within 4 m of a `dual = 1` centreline. The 0.1 % on record
reproduces. Project rule 7 is not a consultant's preference; it is what the operator does.

### 3. How many built pipes cannot pass the peak flow?

The screen loads the built network with the plots it fronts, accumulates on the designer's
own `US_MHID`/`DS_MHID` tree, peaks by **Merrimack (G201-p71)**, adds **10 % infiltration for
an existing inland network (G201-p72)**, and compares with the **Colebrook-White** full-bore
discharge at **k_s = 1.5 mm (G203-p28)** capped at the **Table 10 d/D (G203-p27)**.

| | today (electricity-account occupancy) | saturated |
|---|---|---|
| over capacity | **93 of 2,137 — 4.4 %, 3.00 km** | **238 — 11.1 %, 7.54 km** |
| trunk mains | 32 of 145 | **92 of 145 (63 %)** |
| sub mains | 61 of 322 | **144 of 322 (45 %)** |
| laterals | 0 of 1,675 | 2 of 1,675 |
| of which marginal (≤ 1.25×) | 65 of 93 | 43 of 238 |
| of which over 2× | 18 | 121 |

**Read it this way.** The laterals are fine and will stay fine — that is what a 150 mm bore at
6 mm/m is for. **The failures are entirely in the mains.** Today's trunk failures are
*marginal*: 65 of 93 sit under 1.25×, which is inside the error of the assumed OD200 bore
(188 mm — the dataset records no internal diameter for OD200 anywhere). Do not act on those.
**The sub-main failures are not marginal.** 5A-5's SM.1 runs at **3.0× today and 7.9× at
saturation**, because it is an **OD160 pipe** — a property-connection size by today's Table 6 —
carrying a whole sub-catchment.

**Five reaches are laid dead flat** (`US_INVERT_ = DS_INVERT_`). They carry nothing at any
flow. Reported separately, not averaged into the failure statistics as infinite utilisation.

**The reuse question this answers:** the 2006 network fronts **7.6 % of the saturated load**.
Its laterals are reusable; its mains are not. W11b should assume it lays new mains through
the built area and may keep the laterals, subject to a condition survey this dataset cannot
supply.

### 4. Did the status filter change anything? — **Yes, by a factor of three**

Unfiltered the layer reads **314.3 km**. Built gravity is **95.45 km** — a third of it. The
202.7 km difference is 129 SUREKHA `Design` rows plus 16.1 km of schematic, and
`00_CURRENT.md` already records that the SUREKHA proposals carry *"RG Master Plan (Concept
Design) not approved yet"* in their own `HYPERLINK` field.

---

## Three things in the record that did not survive re-measurement

| On record | Measured | Where it came from |
|---|---|---|
| "median cover depth 1.92 m" (W7) | **cover to crown 1.72 m.** The **1.89 m** W7 quoted is the depth to **invert** | W7 compared depth-to-invert against a design's cover-to-crown. G203-p33's datum is the **crown**, so the built network is 0.16–0.20 m shallower than the record says |
| "the as-built goes shallower and steeper at a wadi" | **deeper and flatter** on hazard ground overall; shallower and steeper only in classes 4–6, on 13 reaches | never measured against a hazard grid before |
| "2,449 drop shafts against 37" | true as counts, but the networks are 1,732 km and 63 km. Per km it is **1.475 against 0.585 — 2.5×** | the normalisation was never applied |

Two further findings that are new rather than corrections:

- **NAMA is below its own minimum cover on 35.9 % of the levelled length** (33.5 % once the
  1.000 m drawing defaults are struck out; 0.44 % is below even the 0.50 m protected floor).
  **This is a target of ZERO for W11b, not a habit to copy.** It is recorded here so that
  nobody cites the as-built as authority for a shallow pipe.
- **The built diameters must not be copied.** 61.5 % of the length is **OD160**, which
  G203-p22 Table 6 classes as a **rider sewer / property connection**, not a lateral. The
  guideline's lateral minimum is **OD 200**, and **the largest pipe anywhere in the built
  network is OD 200**. The 2006 network is, in today's vocabulary, a network of property
  connections with a 200 mm spine.

A data caveat on the cover finding: **369 upstream ends are recorded at exactly 1.000 m** to
the millimetre — a drawing default, not a survey. 79 reaches (2.35 km) carry it at both ends.
The module publishes the cover statistics with and without them; the finding holds either way
(35.9 % → 33.5 %).

---

## How the hierarchy is actually built

The tiers are read from the designer's own manhole IDs, never inferred from geometry:
`5A-2-TM-MH185` trunk main, `5A-2-SM.2-MH391` sub main 2, `5A-1-A49-MH3` lateral zone A49.

| Package | km | trunk | sub main | lateral |
|---|---|---|---|---|
| 5A-1 | 32.2 | — | — | 100 % |
| 5A-2 | 20.0 | 11.3 % | 17.1 % | 71.6 % |
| 5A-3 | 3.5 | 31.1 % | — | 68.9 % |
| 5A-4 | 5.0 | 13.4 % | 10.8 % | 75.7 % |
| 5A-5 | 34.7 | 1.5 % | 17.2 % | 81.4 % |

**The three-tier shape is a habit of this designer, not a law.** 5A-1 — a third of the whole
built network — has no trunk and no sub-main tier at all, and 5A-3 has no sub-mains. The
target above (5.78 / 16.61 / 77.61) is weighted over the packages that built all three.

Where each of the **582 lateral zones** discharges:

| into | zones | share |
|---|---|---|
| another lateral | **520** | **87.7 %** |
| a sub main | 60 | 10.1 % |
| the trunk main | 13 | 2.2 % |

**21 zones touch the trunk across 4.53 km of trunk — 4.64 per km.** Compare per km, never as
a count: W7's failure was 30 joins on a much longer trunk *with no sub-main tier at all*, and
W8 capped it at 19. The number that matters is the density, and whether a sub-main tier
exists to absorb the small catchments.

Runs between junctions: **945 runs, median 68.7 m, mean 100.8 m, 90th percentile 218.6 m,
median 2 chambers**.

---

## Calling it

```python
import sys; sys.path.insert(0, ".../W11b/py")
from w11b.asbuilt import AsBuilt, observe_design

ab = AsBuilt()                 # loads, filters, measures; everything is cached
ab.targets_frame()             # every target: value, band, basis, source, sample
ab.measured                    # the flat dict of 166 measured numbers
ab.by_package                  # the five-package spread that sets every band
ab.evidence_frame()            # measured dict as a DataFrame, for a CSV

obs = observe_design(reaches, fields={...})   # same observables from a W11b layer
ab.check(obs)                  # PASS / HIGH / LOW / NO DATA / INFO, worst first
```

Command line:

```
python W11b/py/w11b/asbuilt.py                 # the tables
python W11b/py/w11b/asbuilt.py --csv DIR       # targets, evidence, per-package CSVs
python W11b/py/w11b/asbuilt.py --json FILE     # the measured dict
```

**`observe_design(reaches, nodes=None, fields=..., slope_is_percent=True)`** maps a design's
own column names onto the observables. It computes only what the columns support and
**leaves the rest absent**, so `check()` reports `NO DATA` — never a silent pass. Column
names it looks for, all remappable: `length`, `grad_mm_m`, `cover`, `tier`, `diameter`,
`us_node`, `ds_node`, `us_ground`, `ds_ground`, `us_invert`, `ds_invert`. Pass
`dual_geometry` and `hazard_class` to add those two checks.

**Tier names are mapped, not guessed.** A tier called `main` is a **main sewer** and belongs
with the sub-mains — G203-p22 Table 6 names four classes in order (rider, lateral, main,
trunk). Getting that wrong once put 393 km of W11a `main` into the trunk share and made a
4.9 % trunk read as 27.6 %. Any tier name not in `TIER_ALIASES` is reported as
`tier_unmapped_pct` with the offending names, never binned.

Other objects worth calling directly: `ab.pipes`, `ab.levelled`, `ab.nodes`, `ab.drops`
(every invert step with its class), `ab.hazard`, `ab.capacity(today=True|False)`,
`ab.proposed`, `ab.schematic`.

### Worked example — W11a scored against these targets

Run on `W11a/shp/W11a.gpkg` (read only, nothing written), the module reproduces W11a's own
vortex count independently and returns **8 HIGH, 5 LOW, 7 PASS**:

| HIGH (worse than anything NAMA built) | LOW (below the built band) |
|---|---|
| uphill 44.3 % vs ≤ 38.1 | median gradient 5.00 vs 5.96–6.63 mm/m |
| climb ÷ descent 0.747 vs ≤ 0.647 | chambers/km 28.7 vs 33.3–36.8 |
| vortex 1.475/km vs ≤ 0.605 | vortex at a junction 99.92 % vs 100 % |
| vortex 51.5 per 1,000 chambers vs ≤ 21.1 | chamber spacing 26.8 m vs 26.8–30.3 |
| median cover 2.76 m vs 1.34–2.07 | lateral share 57.0 % vs 71.6–81.4 |
| 90th-percentile cover 8.74 m vs 2.82–4.48 | |
| **deepest cover 30.23 m vs ≤ 12** | |
| sub-main share 38.1 % vs 10.8–17.2 | |

Two of those are worth naming even though they are not this document's to fix: **W11a
publishes 406 reaches with more than 12 m of cover, the deepest at 30.2 m**, and its
**sub-main tier carries 38 % of the length against NAMA's 17 %** while its laterals carry
57 % against NAMA's 78 %. Its trunk share (4.91 %) passes cleanly.

---

## Assumptions, each labelled where it is used

| # | Assumption | Why it is not a measurement |
|---|---|---|
| A1 | **τ = 1.0 Pa** | GUD-203 4.2.2 gives no numeric τ. Engineer 3 Sep 2026, GAP-9 open. Flagged on every output |
| A2 | **wadi = hazard classes 4–6** of the 50-year grid | the guideline's criterion is *washout*, not a hazard class. Standing in until NWS give a scour depth |
| A3 | **flood no-data = dry high ground** | engineer 3 Sep 2026. The grid covers only 36 % of built-pipe midpoints, so this decision governs the other 64 % |
| A4 | **4.0 m buffer** defines "along a dual carriageway" | ~ one lane half-width; W7 used the same, so the 0.1 % on record is reproducible |
| A5 | **>100 m per vertex = schematic** | the two offenders are at 317 and 565; the worst real pipe is 65 |
| A6 | **60 m** plot-to-pipe radius for the capacity screen | ~ half a block. For the screen only — not a design allocation rule |
| A7 | **OD200 → ID 188.0 mm** | `IN_DIAMETE` is 0 on every OD200 row. The trunk-main bore is recorded nowhere in the dataset. (OD160 → ID 150.4 is corroborated: `IN_DIAMETE` reads 150 on every OD160 row) |
| A8 | **ν = 1.0 × 10⁻⁶ m²/s** | water at ~20 °C |
| A9 | **depth of exactly 1.000 m = drawing default** | 369 upstream ends carry it to the millimetre; no other value is close |
| A10 | **+25 % tolerance** where packages give no spread | used on `climb_m_per_km` only. A project tolerance, chosen, not measured |
| A11 | **3 km / 5 km package floors** for setting a band | so 5A-3's 3.5 km cannot widen a band on its own |
| A12 | **electricity accounts ÷ N_PROP = today's occupancy** | there is no metered flow anywhere in this project. The "today" column is a proxy and is labelled ASSUMPTION |

Guideline constants are quoted from the source PDFs, read back on 3 September 2026, not from
memory: G203 p22 (Table 6 sizes and the 45 m lateral length), p23 (Table 8 roughness), p26
(0.75 / 0.90 m/s), p27 (3 m/s, Table 10 d/D, Mara K), p28 (Colebrook k_s = 1.5 mm), p29
(Table 11 gradients), p30 (0.60 m backdrop trigger, 2.00 m maximum, 90° inlet, Table 12
spacing, 4.4.1 wadis), p33 (1.30 m cover, 0.50 m protected, 10–12 m recommended maximum);
G201 p71 (Merrimack), p72 (Peltier, the 5.0 recommendation, infiltration).

---

## What I could not do, and why

1. **5A-1 is invisible below ground.** 1,123 pipes, **32.2 km, a third of the built network** —
   no inverts, no ground levels, no diameters, no material. Every gradient, cover, drop and
   capacity number rests on the other 66 %. If 5A-1 behaves differently, none of it is known.
   This is the single biggest gap and only a survey closes it.
2. **There is no manhole layer.** Chamber diameter, cover type, benching and backdrop
   construction are nowhere in the dataset. "Chamber spacing" here is pipe length between
   consecutive IDs, which is the same number but not the same evidence. The 37 vortex shafts
   are **inferred from invert steps**, not observed as structures — the dataset does not say
   what NAMA actually built at those 37 manholes.
3. **No condition data.** `P_CONDITIO` is 0 on all 3,265 rows and `SOURCE` is `cctv` on
   exactly one. Nothing here says whether a 2006 pipe is still serviceable, so "reuse the
   laterals" is a hydraulic statement only.
4. **No metered flow anywhere.** "Today's peak flow" is an electricity-account proxy (A12).
   A real answer needs flow monitoring at the three outfalls, which is worth requesting: it
   would also calibrate the whole load model, not just this screen.
5. **The 50-year hazard grid covers 36 % of the built network.** Every wadi statement is
   about that 36 %; the rest is dry by decision, not by measurement.
6. **The wadi behaviour question is under-sampled.** 13 levelled reaches in classes 4–6. I
   have reported what they show and refused to turn it into a rule.
7. **The capacity screen is a screen.** One-dimensional, uniform flow, no backwater, no
   surcharge routing, no diurnal pattern. It ranks pipes; it does not model them. SewerGEMS
   remains the referee.
8. **I could not separate a genuinely shallow pipe from a defaulted one** beyond the exact
   1.000 m test. The 33.5 % below minimum cover is what the dataset says, and the dataset
   warns in every row that it is *"not reliable and must be used only for reference purpose"*.
