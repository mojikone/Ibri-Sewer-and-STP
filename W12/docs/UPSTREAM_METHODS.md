# UPSTREAM METHODS — what SWMManywhere and pysewer actually do, and what is worth taking

Written 3 September 2026. **Document only. No code was added to the W11b pipeline.**
Both repositories were cloned and read; nothing was installed into the project and nothing
was copied into `W11b/py`.

| | repository | licence | commit read |
|---|---|---|---|
| 1 | `ImperialCollegeLondon/SWMManywhere` | **BSD-3-Clause** (vendors `src/netcomp` under **MIT**) | `f0c18be0`, 21 May 2026 |
| 2 | `ddspot/pysewer` | **GPL-3.0-only** (© Helmholtz-Zentrum für Umweltforschung, UFZ) | `b5524b36`, 7 Aug 2026 |

`ddspot/pysewer` is a **fork** of the UFZ original with substantial additions of its own —
BS EN 752 deemed-to-satisfy gradients, Butler & Davies peak-factor models, a constraint
violation register and a benchmark harness. The copyright and the GPL are UFZ's.

---

## THE HEADLINE, AND IT IS UNCOMFORTABLE

**The one claim the engineer asked me to check is FALSE.** `derive_topology()` does not use
Tarjan's optimum branching. The function it calls is *named* `tarjans_pq` and its docstring
says "Tarjan's algorithm for a directed minimum spanning tree", but the code is **Prim's
algorithm run on the reversed graph**. There is no cycle contraction anywhere in the
repository — and cycle contraction is the entire content of Chu–Liu/Edmonds, which Tarjan's
1977 paper is an efficient implementation of. Prim's greedy is correct for an *undirected*
MST and is **not** correct for a minimum spanning arborescence.

I proved it rather than asserting it. Extracting `tarjans_pq` verbatim and running it against
`networkx.minimum_spanning_arborescence` on graphs shaped the way SWMManywhere's own pipeline
shapes them — a `waste` root with in-edges only, double-directed streets, weights asymmetric
between the two directions of an edge exactly as a signed slope weight makes them:

| test graph | `tarjans_pq` | true optimum | excess |
|---|---|---|---|
| 3 nodes, `a→waste 5`, `b→waste 6`, `a→b 1`, `b→a 9` | 11.0 | **7.0** | +57 % |
| 4 nodes, a chain running downhill `a→b→c→waste` | 19.0 | **14.0** | +36 % |

In the second case the tree it returns is not even the tree the ground asks for: it sends `a`
straight to the outfall at cost 10 rather than letting it run down the chain. That is the
exact failure mode we care about — a branch that should have joined a neighbour instead
strikes out on its own.

**Second correction to the brief.** `OutfallDerivation.method` defaults to `"separate"`
(`parameters.py`), and `"separate"` runs `dijkstra_pq` — a multi-source shortest-path forest.
The branching path (`"withtopo"`) is opt-in, and the shipped `demo_config.yml` does not select
it. So the default SWMManywhere topology is **not a branching at all**; it is nearest-outfall
shortest path, which is what W10 and W11a already do.

**None of this makes the idea wrong.** A true optimum branching over a slope-weighted
double-directed corridor graph is the right instrument for stage 4. It is just not what this
repository contains, and `networkx.minimum_spanning_arborescence` — Edmonds, correct, in a
library we already depend on — would be the thing to call.

---

## 1. SWMManywhere, read claim by claim

### 1.1 The Chahinian slope weight — the exact form

`topology_graphfcns.set_chahinian_slope`:

```
surface_slope(u,v) = (z_u − z_v) / length          # POSITIVE = downhill in the direction u→v
chahinian_slope    = np.interp(surface_slope*100,
                               [-1, 0.3, 0.7, 10],
                               [ 1,   0,   0,  1], left=1, right=1)
```

It is a **cost**, so 0 is preferred and 1 is refused. Evaluated:

| ground slope u→v | | weight |
|---|---|---|
| −1.0 % and steeper (adverse) | −10 mm/m | **1.000** |
| −0.5 % | −5 mm/m | 0.615 |
| −0.1 % | −1 mm/m | 0.308 |
| **0.0 % (dead flat)** | 0 | **0.231** |
| +0.1 % | +1 mm/m | 0.154 |
| **+0.3 % to +0.7 %** | **+3 to +7 mm/m** | **0.000 — the preferred band** |
| +1.0 % | +10 mm/m | 0.032 |
| +5.0 % | +50 mm/m | 0.462 |
| +10 % and steeper | +100 mm/m | 1.000 |

So "downhill ~0, adverse ~1" is roughly right but loose in the way that matters. It is a
**four-knee trapezoid on the SIGNED slope**, and the weight is only zero inside a narrow
3–7 mm/m band. Dead-flat ground scores 0.231, not 1 — the function treats flatness as mildly
unattractive, **not as undecidable**, which on our ground is the wrong reading (§4).

**Provenance is weaker than the brief implies.** The docstring cites
`https://doi.org/10.1016/j.compenvurbsys.2019.101370` with the words *"based on"*. That is
**Chahinian N., Delenne C., Commandré B., Derras M., Deruelle L., Bailly J.-S. (2019),
"Automatic mapping of urban wastewater networks based on manhole cover locations",
*Computers, Environment and Urban Systems* 78:101370** — a paper about **reconstructing an
existing network from manhole cover positions by minimising cost functions defined by industry
rules**, not about designing a new one. SWMManywhere's own JOSS-style paper (`docs/paper/`)
cites Chahinian only in a list of prior GIS-derivation literature and **nowhere derives or
defends these four breakpoints**. [Certain on the code and the citation; **I could not read
the paper** — ScienceDirect and HAL both returned HTTP 403 — so I cannot confirm whether
−1 / 0.3 / 0.7 / 10 % appear in it or were chosen by the SWMManywhere authors. Treat the
numbers as **unattributed** until someone with journal access checks.]

That distinction is not pedantry. A weight calibrated to *guess where a French designer put a
pipe* is a prior on designer behaviour, not a statement about hydraulics — and our own
measurement is that the terrain agrees with NAMA's built direction only 71 % of the time.

### 1.2 The bend penalty — three defects, and it is OFF by default

`set_chahinian_angle` interpolates the angle at the downstream node between the incoming edge
and each onward edge, taking the **minimum** (best) over all onward choices:

```
np.interp(angle_deg, [0, 90, 135, 180, 225, 270, 360], [1, 0.2, 0.7, 0, 0.7, 0.2, 1])
```

1. **`chahinian_angle_scaling` defaults to 0.** The bend penalty contributes nothing to the
   default weight. The brief's "multi-criteria weights including … a bend penalty" is, as
   shipped, a two-criteria weight: slope (scaling 1.0) and length + contributing area
   (0.1 each).
2. **Half the table is dead code.** `geospatial_utilities.calculate_angle` is built on
   `math.acos`, so it returns `[0, 180]` and can never return 225 or 270. Those rows are
   unreachable.
3. **It is non-monotone in a way we cannot use.** 90° scores 0.2 but 135° scores 0.7 — a
   right-angle inlet is *preferred* to an obtuse one. Our H10 requires ≥ 90° (G203-p30, read
   from the PDF: *"No inlet pipe at manholes shall have an angle less than 90° to the
   direction of flow"*) and P2 prefers straight. A 135° inlet is legal and good; this table
   ranks it nearly worst. Do not port the table.

The source's own docstring says *"TODO - in a double directed graph, not sure how meaningful
this is"*.

### 1.3 How the weights combine

`calculate_weights` normalises each attribute to [0,1] against **the whole graph's** min/max,
raises it to `{attr}_exponent` (all default 1), multiplies by `{attr}_scaling`, and sums.
Defaults: `chahinian_slope 1.0 · chahinian_angle 0.0 · length 0.1 · contributing_area 0.1`.

**Consequence worth stating:** for the two directions of the *same* corridor, `length` is
identical and `angle` is off, so the direction is decided by `chahinian_slope` (scaling 1.0)
against `contributing_area` (0.1). The slope term therefore dominates the direction choice
almost everywhere — **including on ground where it is measuring noise.**

### 1.4 `pipe_by_pipe` — what their sizing does and does not do

Method from Duque N., Bach P.M., Scholten L., Fappiano F., Maurer M. (2022), *"A Simplified
Sanitary Sewer System Generator for Exploratory Modelling at City-Scale"*, Water Research
209:117903 (`doi:10.1016/j.watres.2021.117903`). Cost equation from `doi:10.2166/hydro.2016.105`.

Grid-searches diameter × invert depth per pipe in topological order and sorts candidates
lexicographically on `surcharge_feasibility → v_feasibility → fr_feasibility → depth → cost`.

**What it does not have, and every one of these is a blocker for us:**

| missing | our rule |
|---|---|
| **Any minimum gradient.** None. Not diameter-dependent, not constant | H6 / G203-p29 Table 11 |
| **A prohibition on adverse gradient.** When the trial invert gives `slope ≤ 0` it *raises the upstream level in 0.05 m steps until the slope is positive* and records `surcharge_feasibility`. It permits an uphill pipe and calls it surcharged | H11 / G203-p29: *"combination of such deviation shall not create a reverse gradient"* |
| **Tractive force.** `min_shear = 2` Pa is declared in `parameters.py` and the code is commented out with the literal note *"TODO shear stress… got confused here"* | H5 / G203-p26–27 — 91 % of our self-cleansing rests on this route |
| **Partial-flow hydraulics.** `R = A/(πD) = D/4`, the full-bore radius, whatever the depth of flow | — |
| **Pumping.** The string `pump` occurs **once** in the entire source tree, as an empty `"PUMPS": None` SWMM `.inp` section. It cannot propose a station | §5 cap-and-veto ladder |
| **Wadis, flood hazard, washout.** Zero occurrences of `flood`, `hazard`, `wadi`, `floodplain` in the graph stage | H1 / H1a / G203-p30 §4.4.1 |

`max_depth` defaults to 5 m, `min_depth` 0.5 m, and the design storm is 0.006 m/hr — **it is a
stormwater tool.** Its sizing is not a candidate for anything here.

### 1.5 The one idea in SWMManywhere worth taking outright

`remove_non_pipe_allowable_links` deletes edges whose OSM `highway` tag is in `omit_edges`
(`motorway, motorway_link, bridge, tunnel, corridor`) **or** which carry a non-null property of
that name. It is the structural equivalent of our project rule 7, applied **at the corridor
stage before any routing**, which is exactly where philosophy §2 says the wadi and
dual-carriageway exclusions belong. We already do this (`PIPE_OK` / `EXCL_RSN` in
`W11b_roads.gpkg`). It is worth recording that an independent team arrived at the same
architecture — exclusion by deletion, not by penalty — because a penalty can always be
outvoted by a big enough slope term, and a deletion cannot.

---

## 2. pysewer, read claim by claim

### 2.1 `needs_pump()` — the claim is TRUE and the algorithm is clean

`optimization.needs_pump(profile, min_slope, tmax, tmin, inflow_trench_depth)` walks a sampled
ground profile from the upstream end and traces the invert:

```
invert[0] = ground[0] − inflow_trench_depth
for each step of length dx:
    invert_at_min_slope = invert[i] + dx·min_slope           # min_slope is NEGATIVE
    if invert_at_min_slope < ground[i+1] − tmax:  →  PUMP, return immediately
    elif invert_at_min_slope < ground[i+1] − tmin:  invert[i+1] = invert_at_min_slope
    else:                                           invert[i+1] = ground[i+1] − tmin
```

Three cases, in words: lay at the minimum gradient and see where the invert ends up; if it
would break the trench-depth cap, a pump is needed; if the ground falls faster than the minimum
gradient, come back up to minimum cover. That is a correct and honest trench tracer and it is
**the same shape as our own levelling pass**. Defaults: `min_slope −0.01`, `tmax 6.0 m`,
`tmin 0.25 m`, `min_cover 0.25 m` (`config/settings.yaml`).

Note the naming trap if anyone reads the source: the variable called `trench_depth` holds
**elevations**, not depths.

`optimize_sewer` then distinguishes a **pump** (needed even starting from the shallowest
possible inlet) from a **lifting station** (only needed because the actual arriving invert is
deep). That two-tier distinction is genuinely useful and we do not have it: our stage 7 places
a station wherever the cap is breached, without asking whether the breach is caused by the
ground or by inherited depth. **Worth reimplementing.**

### 2.2 The pump penalty — the claim is HALF true. It is a cliff, not a trade

`preprocessing.generate_connection_graph`:

```
weight = distance                          if gravity is possible
weight = distance × pump_penalty           if needs_pump()          # pump_penalty = 1000
```

and `routing.rsph_tree` runs Dijkstra on that weight.

So the brief's *"trading stations against excavation"* is not what happens. **There is no
excavation cost term anywhere in pysewer** — I grepped the whole package for `cost`,
`excavat`, `capex`: zero hits. Depth is free all the way to `tmax` and then costs 1000×
distance. It is a **hard feasibility cliff with a large constant multiplier**, which routes
*around* pumps rather than pricing them. Our philosophy §5 ladder is the better instrument
precisely because it separates CAP (feasibility) from VETO (maintainability) from ECONOMICS,
and puts the economics third. pysewer collapses all three into `tmax`.

### 2.3 RSPH — the claim is TRUE

`rsph_tree` is a textbook repeated shortest-path heuristic for a Steiner tree: precompute
all-pairs Dijkstra, repeatedly attach the terminal closest to the growing tree, absorb the path
into the tree. It is a heuristic, not an optimum. Two things to know if it is ever considered:
it calls `nx.all_pairs_dijkstra_path` (**O(n²) paths held in memory** — on 9,746 corridor
nodes that is not going to run), and `rsph_tree_fast` swallows every routing failure in a bare
`except:` and prints a warning, which is the silent-drop pattern our doctrine forbids.

### 2.4 The sizing order is inverted relative to ours

pysewer decides the **slope first** (from `min_slope` and the ground), then picks the smallest
diameter whose partial-flow capacity at `d/D ≤ 0.75` passes the flow *at that slope*
(`select_diameter_with_constraints`). It never goes back to re-lay the pipe steeper because the
chosen diameter demands a steeper minimum. Where the small-sewer branch fires
(`peak_flow < 0.001 m³/s`) it drops the `velocity_min` test and checks a fixed
`dts_min_gradient = 1/150` (6.67 mm/m) instead, recording `gradient_below_dts` as a
**reported violation, not a design correction**.

Its hydraulics are otherwise better than SWMManywhere's: `_partial_flow_capacity` and
`_proportional_depth` use the exact wetted-angle geometry, and the settings file carries a
warning against confusing Manning's *n* with Colebrook-White *k*<sub>s</sub>. **The method is
sound; the licence is the problem (§7).**

---

## 3. What their branching needs that we do not compute

Required by `calculate_weights` + `derive_topology`, against `W11b/shp/W11b_roads.gpkg` as it
stands today:

| attribute | where it lives upstream | do we have it |
|---|---|---|
| node `surface_elevation` | `set_elevation`, one raster sample per node | **NO.** The `nodes` layer carries `NODE_ID, DEGREE, MADE_BY, COMP, X, Y, TAU_PA` — no Z. This is the one genuinely missing input, and it is 9,746 samples off the 0.5 m VRT |
| edge `surface_slope`, then `chahinian_slope` | derived from the above | **NO**, follows from the above |
| a **double-directed** edge set | `double_directed` graphfcn | **NO.** Our corridors are single LineStrings whose `US_NODE`/`DS_NODE` are a naming convention, not a flow direction. A branching needs both arcs present, each with its own weight |
| edge `length` | OSM | **YES** — `LEN_M` |
| edge `contributing_area` | `calculate_contributing_area`; the edge value is **the upstream node's own impervious subcatchment area**, not the accumulated area | **BETTER THAN THEIRS, wrong shape.** We carry `N_PLOT`, `N_BUILT`, `Q_M3D`, `Q_NEAR_M3D` per corridor — a real foul load, not an impervious proxy. It would need re-expressing per node |
| edge `edge_type` ∈ {street, river, outfall} | `identify_outfalls` | **Trivial to construct.** Our outfall is the existing works at E444422.8 N2563337.9 and the trunk is an INPUT (`SHP/Main Pipe`) |
| a `waste` super-node with every plausible outfall attached | `outfall_graphfcns` | **Trivial**, and we need it in the multi-outfall form because H15 permits satellite works |
| node `x, y` for the angle term | — | **YES** |

Two things **their** branching does not need and ours must have, and neither repository has any
concept of either: a **hazard/wadi cost or exclusion**, and **`CONFIDENCE`/provenance carried
through the routing** so a provisional corridor can be identified in the output.

---

## 4. The hard question: a slope weight against a DIAMETER-DEPENDENT minimum gradient

**Straight answer: neither repository attempts it, and the reconciliation is not to make the
weight know the diameter — it is to notice that the weight does not need to.**

First, what the guideline actually says. Read out of the PDF today,
`Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf`, printed page 29 of 201, Table 11
*"Minimum Sewer Line Gradient"*, Colebrook-White at a self-cleansing velocity of 0.75 m/s:

| DN (mm) | 200 | 250 | 315 | 400 | 500 | 600 | 700 | 800 | 900 and above |
|---|---|---|---|---|---|---|---|---|---|
| min gradient (mm/m) | **5.00** | 3.75 | 2.70 | 2.05 | 1.55 | 1.25 | 1.00 | 0.85 | **0.75** |

The spread is **6.7×** from end to end. That is the whole difficulty in one number.

**What the two repos do instead.** SWMManywhere: nothing — no minimum gradient exists, and an
adverse gradient is permitted and relabelled `surcharge_feasibility`. pysewer: a single scalar
`min_slope = −0.01` (10 mm/m), diameter-independent, steeper than our steepest requirement,
applied identically to a house connection and a trunk. Neither is an answer.

**The reconciliation, in three parts.**

1. **A graph weight is a preference on direction; a minimum gradient is a constraint on a
   pipe.** The weight only has to get the *sign* and the *rank* right. It does not have to
   reproduce the constraint, and a weight that tries to will be wrong at every diameter but
   one.

2. **The right thresholds for our ground are the two ENDS of Table 11, not any single row.**
   Below **0.75 mm/m** no pipe of any diameter can follow the ground, so direction genuinely
   does not matter there and the weight should say so by going flat and letting the other terms
   decide. Above **5.00 mm/m** every diameter can follow the ground, so the weight should be at
   its best and stay there. Between them the preference ramps. That is exactly the *shape* of
   Chahinian's trapezoid with the knees moved from **3.0–7.0 mm/m** to **0.75–5.00 mm/m**.
   The measured consequence of getting this wrong is in §5: on our corridors, 33.5 % of the
   length falls more gently than Chahinian's lower knee, so a third of the network sits on the
   steep part of *their* ramp where in fact no diameter can be laid to the ground at all.

3. **The diameter is not unknowable at weighting time, and the design is already required to
   run twice.** The trunk is an INPUT, so its band is fixed. Every corridor already carries
   `Q_NEAR_M3D` and `N_PLOT`, so a load-derived a-priori diameter exists with no layout at all.
   Philosophy §7 already mandates two passes: weight with the load-derived diameter → branch →
   size → re-weight with the sized diameter → re-branch, and report how much the tree moved
   between the two. If it moves a lot, the weighting is unstable and should be said so; if it
   barely moves, the circularity was never binding.

**And the move that must NOT be made.** G203-p29, verbatim from the PDF: *"Sewers shall not be
oversized to facilitate flatter slopes."* A weight that prefers a route because a larger pipe
there would permit a flatter gradient is that prohibited move dressed as a graph cost. Keep the
weight on the ground and the gradient on the pipe. (This is the same trap that withdrew
`W10/py/p3_optimise.py`.)

---

## 5. Does either repository handle the flatness problem?

**No. Both assume terrain with usable fall.** Measured today against our own corridors, and
the measurement reproduces the brief's fact 3 independently.

**Method:** all 12,665 corridors in `W11b/shp/W11b_roads.gpkg` (1,819.4 km), end-to-end ground
gradient sampled from `W11b/run/terrain/L2_dem.tif` (the 2 m working grid derived from the
0.5 m VRT), length-weighted. Script run read-only in the scratchpad; nothing written to the
project.

| length-weighted percentile of \|ground gradient\| | p10 | p25 | **p50** | p60 | p75 | p90 |
|---|---|---|---|---|---|---|
| mm/m | 0.98 | 2.34 | **4.23** | 4.95 | 6.82 | 12.14 |

| share of corridor length falling more gently than… | % | km |
|---|---|---|
| 0.75 mm/m — DN900+ minimum, the flattest legal pipe there is | 7.4 | 134.9 |
| 1.55 mm/m — DN500 | 15.6 | 283.9 |
| 2.05 mm/m — DN400 | 21.6 | 392.3 |
| **3.00 mm/m — Chahinian's LOWER knee** | **33.5** | **609.0** |
| 3.75 mm/m — DN250 | 43.6 | 793.5 |
| **5.00 mm/m — DN200 minimum** | **60.5** | **1,100.7** |
| **7.00 mm/m — Chahinian's UPPER knee** | **75.6** | **1,375.3** |
| **10.00 mm/m — pysewer's `min_slope`** | **86.0** | **1,565.4** |

*(The 60.5 % / 1,100.7 km reproduces the brief's 60 % / 1,098.8 km. Independent confirmation,
different segmentation.)*

**What that does to each tool:**

- **SWMManywhere.** Only **42.1 % of our length** (766 km) falls inside the 3–7 mm/m band where
  its slope weight is zero. **33.5 %** sits below the lower knee, on the steep part of the ramp,
  where the weight is confidently discriminating direction on a signal that no pipe can use.
  Dead-flat ground scores 0.231 rather than "undecidable", and with `chahinian_slope_scaling`
  at 1.0 against `length` and `contributing_area` at 0.1 each, that 0.231 still decides. **The
  function is most confident exactly where the ground is least informative.**
- **pysewer.** `min_slope = −1 %` is steeper than every row of Table 11. On **86.0 %** of our
  corridor length the ground falls more gently than that, so its tracer would drive the invert
  down until it hit `tmax` and then call for a pump. **It handles flatness by pumping** — a
  defensible answer for a rural catchment and the exact opposite of the TOR, scope p12:
  *"The entire layout shall take into consideration the topography of the area in order to
  avoid pumping and utilize gravity as much as practically possible."*

**Neither repository contains the concept that the ground can be too flat to lay a pipe on.**
That concept is ours and it has no upstream to borrow from.

---

## 6. ESTIMATE: what a slope-weighted branching would do to 737.7 km uphill and 2,449 drops

Asked for before any code, and asked to be sceptical. I measured three things first.

### 6.1 The invariant that bounds everything

**For a FIXED set of corridors at a fixed segmentation, `climb + descent` is invariant under
re-orientation.** Reversing an edge turns its climb into descent; the sum of |Δz| does not
move. Only the *split* moves. Measured on our corridors, densified and sampled:

| segmentation | climb + descent |
|---|---|
| corridor ends (median corridor 93.9 m) | 6.12 m/km |
| ~100 m | 7.29 m/km |
| ~50 m | 8.43 m/km |
| **~30 m (NAMA's median chamber spacing is 29.77 m)** | **9.14 m/km** |

W11a's own figures are climb 4.24 + descent 5.90 = **10.14 m/km** (`AS_BUILT_TARGETS.md`),
consistent with 9.14 within 10 % — the residual is pipe inverts versus ground and a slightly
different corridor set. **So the invariant is real and it is the ceiling on the whole
exercise.**

On W11a's own 10.14 m/km, reaching NAMA's climb ÷ descent of 0.483 requires descent 6.84 and
climb 3.30 m/km. That is a **22 % cut in climb — 1,346 m removed** over 1,731.7 km. That is the
entire prize, and no orientation can beat it.

**One caveat that cuts against us.** NAMA's 0.483 was measured on 63.2 km whose own invariant
is 12.46 m/km — the older, steeper part of town. On flatter ground with a lower invariant the
achievable ratio is *worse*, not equal, because the descent available per km is smaller while
the network still has to climb the same local humps. **0.483 is not a ratio we are entitled to
on our ground.** [Likely]

### 6.2 The decidable fraction bounds it again

| | measured |
|---|---|
| corridor length with end-to-end \|Δz\| < 0.25 m | **16.6 %** (302 km) |
| < 0.50 m | **32.6 %** (593 km) |
| < 1.00 m | 55.5 % (1,010 km) |
| DEM vs NAMA's surveyed ground levels | median +0.25 m, 5th–95th −0.50 to +1.12 m (`AS_BUILT_TARGETS.md`) |
| terrain agrees with NAMA's built direction, when it decides at all | **71 %** (brief, fact 1) |
| NAMA's own SURVEYED levels agree with the direction their pipes run | **65 %** (brief, fact 2) |

Take the decidable share as 0.67–0.80 (the complement of the 0.50 m and 0.30 m relative-error
bands) and the probability of being right when it decides as p ≈ 0.65–0.71. Expected capture of
the gap ≈ decidable × (2p − 1) = **0.20 to 0.34**.

### 6.3 The estimate

| | W11a today | slope-weighted branching, expected | NAMA as-built |
|---|---|---|---|
| climb removed | — | **270 – 460 m** of the 1,346 m available | — |
| climb, m/km | 4.24 | 3.90 – 4.02 | 4.06 |
| climb ÷ descent | 0.747 | **0.68 – 0.70** | 0.483 (band ≤ 0.647) |
| uphill length | 44.3 % (737.7 km) | **41 – 42 %** (≈ 700 – 720 km) | 34.1 % (band ≤ 38.15) |

**It does not reach the as-built band on either measure.** It removes roughly one uphill
kilometre in twenty. That is worth having and it is not the fix the record implies. [Likely —
the invariant and the decidable fraction are measured; the capture fraction is a bound, not a
prediction.]

### 6.4 The drop shafts — and this is where the estimate turns

I checked the drops directly on `W11a/shp/W11a.gpkg`, and the result **refuted my first
hypothesis**:

| measured on W11a's published nodes | |
|---|---|
| VORTEX nodes | 2,449 |
| **at a junction (N_IN ≥ 2)** | **2,447 — 99.9 %** |
| on a straight run | **2** |
| DROP_M median | **4.24 m** (max 19.83 m) |
| all nodes with DROP_M > 0.60 m (G203-p30 backdrop trigger) | 4,066, of which 99.8 % at a junction |

So W11a already **passes** the qualitative as-built test — NAMA's 37 drops are 100 % at
junctions, and so are W11a's 2,449. The excess is purely in the *rate*, and the drops are not
a design levelling its way out of a straight-run fault.

Then, on the 5,063 reaches that arrive at a vortex node:

| | into a drop | all reaches |
|---|---|---|
| `GRAD_BY = table11` (the diameter's own minimum set the gradient) | **78.2 %** | 77.0 % |
| median `SLOPE_LAID / SLOPE_MIN` | **1.00** | — |
| median `UPSTR_KM` | **0.553 km** | 0.351 km (**1.6×**) |

**The arriving branches are laid at exactly their floor and they are 1.6× longer than
average.** A DN200 at its 5.00 mm/m minimum buys 2.77 m of invert over 553 m *whatever the
ground does and whichever way it points*. That is **65 % of the median 4.24 m drop, from
geometry alone**, before direction enters the question.

So: **the drops are bought by flatness and branch length, not by direction.** Re-orienting the
tree cannot change `GRAD_BY = table11` — that is the diameter's floor, not a choice. It can
only shorten the run over which the debt accrues, and SWMManywhere's default weights give
`length` a scaling of 0.1 against slope's 1.0, so a branching of that shape does not even
optimise the thing that matters.

**Estimate: 2,449 → roughly 1,800 – 2,100 vortex shafts, i.e. 1.04 – 1.21 per km against
NAMA's 0.585. Still about twice the built rate.** [Guessing on the scaling from climb to drop
count; the 20–34 % climb reduction behind it is the defensible part.]

### 6.5 The lever that would actually move it — and why it is closed

Cap the length a branch may run at its own Table 11 minimum before it must join a main.
Stepping DN200 → DN250 cuts the minimum from 5.00 to 3.75 mm/m (−25 % debt per metre); DN315
cuts it to 2.70 (−46 %). **G203-p29 forbids it**: *"Sewers shall not be oversized to facilitate
flatter slopes."* So the debt is genuinely unavoidable at a given branch length.

Which leaves **branch length itself** as the only remaining lever — shorter runs into more sub
mains, less debt per branch, more junctions. And that collides head-on with philosophy **P3
("long runs, few junctions")**, which pushes the opposite way. **The philosophy does not
resolve that conflict and it needs to.** It is a bigger question than the branching.

**And note how NAMA solved it: they didn't.** 35.9 % of the built network's length sits below
the 1.30 m minimum cover (`AS_BUILT_TARGETS.md`, G203-p33). They absorbed the depth debt by
going shallow and breaking the cover rule on more than a third of their length. **We cannot —
that row's band is `≤ 0`.** Any comparison of our drop count against theirs has to carry that
sentence beside it, or it flatters them.

---

## 7. LICENCE DISCIPLINE — this is a client deliverable and the repo is PUBLIC

The git remote is public (project rule 11). Anything vendored into it is *distributed*.

### SWMManywhere — BSD-3-Clause. Copying is PERMITTED, with conditions

**May be copied verbatim into `W11b/py`**, provided the source redistribution keeps the
copyright notice, the list of conditions and the disclaimer — in practice, a file header
naming *Copyright (c) 2022 barneydobson* and a copy of `LICENSE` alongside:

- `shortest_path_utils.dijkstra_pq` — but we do not need it; it is the method W10/W11a already
  use.
- `geospatial_utilities.calculate_angle` — 20 lines of trigonometry we already have.
- `topology_graphfcns.set_surface_slope`, `set_chahinian_slope`, `calculate_weights`.

**Do NOT copy `shortest_path_utils.tarjans_pq` under any circumstances.** It is mislabelled and
provably sub-optimal (§0). Vendoring a function named after Tarjan that is not Tarjan's
algorithm into a client deliverable is a defect we would be shipping knowingly.
`networkx.minimum_spanning_arborescence` (Edmonds, correct, already a dependency) is the
replacement.

**Do not copy the angle table** (§1.2). **Do not copy `pipe_by_pipe`** (§1.4) — it has no
minimum gradient and permits adverse gradients.

The third BSD clause bars using "Imperial College London" or the authors' names to endorse our
work. A citation in the method section is fine; an implication of endorsement is not.

`src/netcomp` is separately **MIT** and belongs to the metrics module we have no use for.
Leave it alone.

### pysewer — GPL-3.0-only. Take NOTHING verbatim

Copyleft, and `-only`, so there is no GPL-3-or-later escape hatch. **If any pysewer code
reached `W11b/py` and that repo stayed public, the GPL's obligations would attach to the whole
distributed work.** That is a real exposure on a client project, not a theoretical one.

- **NOT permitted:** any line, any function body, any constant table, any identifier name, any
  comment, any docstring. `needs_pump`, `rsph_tree`, `select_diameter_with_constraints`,
  `_partial_flow_capacity`, `_proportional_depth`, `settings.yaml` — all off limits as text.
- **Permitted:** the *methods*. An algorithm is not copyrightable; its expression is. The
  three-case trench tracer and the pump/lifting-station distinction (§2.1) are ideas, and the
  ideas are older than pysewer.
- **How to reimplement safely, if we decide to:** write the method down in prose in a design
  note first, put the source away, and implement from the prose with our own names, our own
  structure and our own constants read from G203. Do **not** implement with the source open
  beside you — that is how a "reimplementation" becomes a transcription. And every constant
  comes from Table 11 and the philosophy, never from `settings.yaml`: their `min_slope −0.01`,
  `tmax 6.0`, `tmin 0.25`, `pump_penalty 1000` are all wrong for us anyway.
- **Also fine:** citing pysewer in the report as prior art, and quoting a short phrase from it
  for criticism, as this document does.

**My recommendation: do not vendor either.** Take the *architecture* lesson from SWMManywhere
(exclusion at the corridor stage, signed slope as a directed edge weight, a `waste` super-node
so multi-outfall falls out for free), the *method* lesson from pysewer (the trench tracer, and
pump-versus-lifting-station), call `networkx.minimum_spanning_arborescence` for the branching,
and write the rest ourselves. That keeps `W11b` borrowing nothing, which is the standing
instruction anyway.

---

## 8. WHAT I COULD NOT DO

1. **I could not read the Chahinian 2019 paper.** ScienceDirect (`S0198971518306379`), HAL
   (`hal-02275903`) and IRD Horizon all refuse without credentials. So I **cannot confirm**
   that the breakpoints −1 / 0.3 / 0.7 / 10 % and the angle table come from that paper, and
   SWMManywhere's own paper does not derive them. **Anyone quoting "the Chahinian weighting" as
   published values is quoting a code comment, not a publication.** If we want them, the paper
   must be obtained.
2. **I did not run either package.** `loguru` and the geospatial stack are not installed, and
   installing them is outside my file ownership. I extracted `tarjans_pq` verbatim into an
   isolated file to test it — that test is sound and reproducible; nothing else was executed.
3. **The estimate in §6.3 is bounded, not predicted.** The invariant (6.12–9.14 m/km) and the
   drop diagnosis (99.9 % at junctions, 78.2 % `GRAD_BY = table11`, laid/min = 1.00) are
   measurements. The 20–34 % capture fraction is an argument from the decidability statistics,
   and the 1,800–2,100 drop-shaft figure assumes drops scale with climb, which I have not
   demonstrated.
4. **I did not check whether the corridor set W11b will actually route on equals the one I
   measured.** I measured all 12,665 corridors including those flagged `PIPE_OK = 0`; on this
   file that filter removed nothing, so the 1,819.4 km includes any corridor later excluded for
   a dual carriageway or a wadi. The percentages will shift slightly once the exclusions bite.

---

## 9. SOURCES

**Guideline, read from the PDF on 3 September 2026** —
`Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf`:

- **G203-p29** Table 11 *Minimum Sewer Line Gradient* — DN200 5.00 · 250 3.75 · 315 2.70 ·
  400 2.05 · 500 1.55 · 600 1.25 · 700 1.00 · 800 0.85 · 900 and above 0.75 mm/m; §4.3.1
  self-cleansing velocity 0.75 m/s; *"Sewers shall not be oversized to facilitate flatter
  slopes"*; *"Uniform slopes must be maintained between successive manholes"*; 20 mm laying
  tolerance and no reverse gradient; §4.3.2 maximum velocity 3.0 m/s.
- **G203-p30** backdrop required past 600 mm invert difference, external, maximum 2 m, vortex
  drop shaft beyond; *"No inlet pipe at manholes shall have an angle less than 90° to the
  direction of flow"*; Table 12 chamber spacing 100/120/150/200 m; §4.4.1 *"Locating pipelines
  and associated chambers in wadis or areas subject to washout during heavy storms must be
  avoided."*
- **G203-p33** minimum cover 1.30 m, maximum 12 m — via `_BRAIN/08_DESIGN_PHILOSOPHY.md` H3/H4,
  not re-read today.
- **Scope p12** *"avoid pumping and utilize gravity as much as practically possible"* — via
  philosophy §8a, not re-read today.

**Project measurements reused, not re-derived** — `W11b/docs/AS_BUILT_TARGETS.md` (3 Sep 2026):
NAMA climb 4.06 m/km, descent 8.40, ratio 0.483, uphill 34.10 %, vortex 0.585/km, 37 drops all
at junctions, 35.9 % of length below 1.30 m cover, median chamber spacing 29.77 m, DEM vs
survey median +0.25 m; W11a climb 4.24, descent 5.90, ratio 0.747, uphill 44.3 %, vortex
1.475/km, 1,731.7 km, 2,449 shafts.

**Measured by me today, read-only, nothing written to the project:**

| | source |
|---|---|
| corridor gradient distribution, 12,665 corridors / 1,819.4 km | `W11b/shp/W11b_roads.gpkg` layer `corridors` × `W11b/run/terrain/L2_dem.tif` |
| climb + descent invariant at 30/50/100/150 m | same |
| 2,449 vortex nodes, 99.9 % at a junction, median DROP_M 4.24 m | `W11a/shp/W11a.gpkg` layer `nodes` |
| 5,063 reaches into a drop, 78.2 % `GRAD_BY = table11`, laid/min 1.00, UPSTR_KM 0.553 km | `W11a/shp/W11a.gpkg` layer `reaches` |
| `tarjans_pq` sub-optimality, +57 % and +36 % | `tarjans_pq` extracted verbatim vs `networkx.minimum_spanning_arborescence` |

**Upstream source read** — `ImperialCollegeLondon/SWMManywhere` @ `f0c18be0`:
`src/swmmanywhere/graphfcns/{topology,design,outfall,subcatchment,network_cleaning}_graphfcns.py`,
`shortest_path_utils.py`, `parameters.py`, `graph_utilities.py`, `geospatial_utilities.py`,
`defs/demo_config.yml`, `docs/paper/`, `LICENSE`, `pyproject.toml`.
`ddspot/pysewer` @ `b5524b36`: `pysewer/{routing,optimization,preprocessing}.py`,
`pysewer/config/{settings.py,settings.yaml}`, `LICENSE`, `pyproject.toml`.

**Literature identified (not read):** Chahinian et al. 2019, *Comput. Environ. Urban Syst.*
78:101370, `doi:10.1016/j.compenvurbsys.2019.101370` — the slope/angle weights cite this.
Duque et al. 2022, *Water Research* 209:117903, `doi:10.1016/j.watres.2021.117903` — the
pipe-by-pipe method. `doi:10.2166/hydro.2016.105` — the excavation cost equation.
