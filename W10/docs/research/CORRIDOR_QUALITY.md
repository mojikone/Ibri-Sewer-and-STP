# How good is the corridor network W10 was designed on?

Research note, 2026-09-01. Scripts `W10/py/research/r1`–`r4`, `r8`, `r9`; layer
`W10/shp/W10_corridor_quality.shp`; figures `W10/img/research/`.

---

## The verdict, one line per source

| Source | km | Trust it for | Do not trust it for | Overall |
|---|---|---|---|---|
| **`draft`** | 1,195.4 | everything. It is clean on every test | nothing found | **Good** |
| **`auto_road`** | 604.3 | alignment — it agrees with the draftsman to 1.5 m median | *where it goes*: 11.0 % on wadi ground, 15.8 % of its pipe collects nothing | **Usable, needs editing** |
| **`auto_block`** | 319.9 | the existence of a street reserve on a **platted** block | that a street is there now, and 14.9 % of it is inside plots | **Provisional** |
| **`auto_link`** | 92.3 | nothing on its own | everything — 22.8 % runs through plots, it is 63 % in unbuilt ground, and every link stops 1.0 m short of what it joins | **Poor** |

[Certain] on every number above; each is measured, and the script that produced it is named
in the section that carries it.

**The one-sentence answer.** The draftsman's work is good and the road layer is usable; the
two synthetic sources are not survey-grade and 412 km of the design rests on them. The
biggest single problem is not any of the five defects measured — it is that `auto_block`
draws streets in subdivisions that exist on the cadastre and not on the ground, and that
97.4 % of it was converted to pipe without anyone looking.

---

## What was measured, and on what

Two layers, deliberately:

| | Length | Why both |
|---|---|---|
| Corridors, `W10_corridors.shp` | 2,211.8 km in 22,827 lines | what was drawn |
| Pipe, `W10_pipes.shp` | 1,882.9 km in 20,936 reaches | what the solver used. A defect in a corridor nobody laid pipe in costs nothing |

The pipe carries no source tag, so each reach was attributed to the nearest corridor
(`r2_agreement.py`). 46.8 km sits more than 5 m from any corridor: that is the trunk, which
is a separate input, and it is reported as `trunk/other`.

**How much of each corridor became pipe** — the sources you trust least are the ones the
solver used most, because a capillary has no alternative:

| Source | corridor km | pipe km | used |
|---|---|---|---|
| `draft` | 1,195.4 | 911.8 | **76.3 %** |
| `auto_road` | 604.3 | 520.7 | **86.2 %** |
| `auto_block` | 319.9 | 311.4 | **97.4 %** |
| `auto_link` | 92.3 | 92.2 | **99.9 %** |

[Certain]. On this attribution 375.8 km of corridor carries no pipe — `W10_SUMMARY` puts it
at 391.5 km, the difference being that it works from the noded network including the trunk.
Either way the split is the same and it is the useful part: **283.6 km of it is `draft` and
83.6 km is `auto_road`, against 8.5 km of `auto_block` and 0.1 km of `auto_link`.** The
"loop-closing alternatives the solver did not take" are almost entirely in the two good
sources; the synthetic corridors had no alternatives to offer.

---

## 1. Dual carriageways — a non-problem

Rule 7: no pipe of any kind may run along a dual carriageway, because it cannot be dug up.
`dual` = 1 in `SHP/Road centerline 2` gives 289 lines, 146.9 km.

**Corridor length within a distance band of a dual centre line:**

| Band | 4 m | 6 m | 8 m | 12 m |
|---|---|---|---|---|
| `draft` | 0.10 | 0.56 | 1.37 | 8.27 |
| `auto_road` | 1.76 | 2.84 | 4.99 | 7.25 |
| `auto_block` | 0.01 | 0.05 | 0.08 | 0.16 |
| `auto_link` | 0.09 | 0.14 | 0.18 | 0.23 |
| **Total km** | **1.96** | **3.59** | **6.62** | **15.91** |

**On the pipe: 3.64 km of 1,882.9 km — 0.19 %.** [Certain]

Read the bands, not a single tolerance. A corridor 4 m from the centre line *is* the
carriageway; one 12 m away is the verge or the service road beside it, which is normal and
correct. The jump from 6.62 km at 8 m to 15.91 km at 12 m is that verge, not a violation.

**Conclusion: the rule is being obeyed.** 2.68 km of the 3.64 km is `auto_road`, which is
expected — the W8 `RoadTreatment` stage drops `dual`=1 lines whole, so what survives within
6 m of one is a *different, non-dual* road running alongside it. Those 2.68 km are worth an
eye during detail design but they are not the 3.5 km of trouble the raw number suggests.
The draftsman put 0.43 km of pipe inside the band across 911.8 km of his own work, which is
a clean result.

---

## 2. Wadi ground — the largest real defect, and it is in `auto_road`

Hazard grid `Data/04 Lekhuwair/Hazard_T50y.tif`, classes 4/5/6. The grid is continuous
float, so the test is `floor(v) >= 4`; sampled every 10 m along every line.

| Source | corridor km | on wadi | % | pipe km | on wadi | % |
|---|---|---|---|---|---|---|
| `draft` | 1,195.4 | 69.9 | 5.8 | 911.8 | 49.5 | 5.4 |
| `auto_road` | 604.3 | **66.5** | **11.0** | 520.7 | **60.0** | **11.5** |
| `auto_block` | 319.9 | 14.9 | 4.7 | 311.4 | 14.6 | 4.7 |
| `auto_link` | 92.3 | 6.5 | 7.1 | 92.2 | 6.5 | 7.0 |
| trunk / other | — | — | — | 46.8 | 5.4 | 11.5 |
| **Total** | **2,211.8** | **157.8** | **7.1** | **1,882.9** | **136.1** | **7.2** |

[Certain] on the measurement. **`auto_road` is twice as exposed as anything else** and holds
44 % of the wadi-borne pipe on 28 % of the length. That is not a fault in the treatment
stage — it is a fault in the underlying road layer, or rather a fact about it: roads in Ibri
follow wadi floors because that is where the flat ground is. A road that follows a wadi is
a perfectly good road and an impossible sewer corridor.

**Reconciling the three wadi figures the project now carries** — all three are right, they
measure different things:

| Figure | What it is |
|---|---|
| **170.5 km** | `netlib.load_network`, on the noded corridor network **including** the 92.3 km trunk, one sample at each edge midpoint |
| **157.8 km** | this note, on `W10_corridors.shp`, which **excludes** the trunk, sampled every 10 m |
| **136.1 km** | this note, on the **pipe** |
| 131.7 km | `OPTIMISATION.md`, on the pipe, one sample per edge midpoint |

The 136.1 / 131.7 gap is the sampling density: a 10 m walk catches short wadi crossings a
single midpoint misses. Use **136.1 km** as the pipe figure and say how it was measured.

`OPTIMISATION.md` already states the position: the routing now charges a wadi crossing, so
the router crosses rather than follows, and what remains "is a corridor problem for the next
iteration, not a routing one". This note says which corridor: **`auto_road`, and it is the
road layer telling the truth about where the roads are.**

---

## 3. Corridors running through plots — where the synthetic sources fail

A street centre line should run *between* plots. One that crosses a registered plot cannot
be built as drawn. Measured against `MoH_Plots.shp` (61,272 polygons), and reported twice:
raw intersection, and intersection with the plot shrunk 3 m, which separates a corridor
clipping a boundary from one running through the middle.

| Source | corridor km | inside a plot | **more than 3 m inside** | % | pipe: more than 3 m inside | % |
|---|---|---|---|---|---|---|
| `draft` | 1,195.4 | 25.7 | **17.5** | **1.5** | 15.5 | **1.7** |
| `auto_road` | 604.3 | 68.9 | 53.8 | 8.9 | 46.5 | 8.9 |
| `auto_block` | 319.9 | 58.7 | 47.7 | **14.9** | 46.7 | **15.0** |
| `auto_link` | 92.3 | 36.0 | 21.1 | **22.8** | 21.1 | **22.9** |
| **Total** | **2,211.8** | **189.3** | **140.1** | **6.3** | **131.4** | **7.0** |

[Certain]. This is the cleanest discrimination in the study — a factor of **15** between
the draftsman and the MST links. It is also the one with a direct consequence: 131.4 km of
pipe is drawn across land somebody owns, and `OWNER_NAME` is populated on 1,704 of 61,272
plots, so 97 % of the time nobody knows whose.

The `auto_link` result is structural rather than careless. `p0_auto.stitch` joins ~2,300
skeleton islands by a minimum spanning tree on straight lines between nearest points. A
straight line between two street networks separated by a block goes through the block.

---

## 4. Geometry — and one latent defect worth fixing

| Source | lines | median length | median vertex spacing | vertices / 100 m | lines < 15 m | free at both ends |
|---|---|---|---|---|---|---|
| `draft` | 5,721 | 109.3 m | 87.8 m | 2.1 | 67 (0.6 km) | 28 (10.5 km) |
| `auto_road` | 3,027 | 97.0 m | 30.8 m | 4.2 | 0 | 409 (79.9 km) |
| `auto_block` | 11,800 | **22.8 m** | **12.2 m** | **11.9** | **5,089 (10.2 km)** | 1,854 (67.4 km) |
| `auto_link` | 2,279 | 32.8 m | 32.8 m | 6.1 | 201 (2.4 km) | 1,887 (71.1 km) |

The `auto_block` profile is the signature of a raster skeleton: 11,800 fragments averaging
27 m, a vertex every 12 m, and 5,089 pieces under 15 m. `SIMPLIFY_M = 1.5` in `skeleton.py`
is doing less than it looks.

**Dangles must be read carefully, and the first version of this measurement was wrong.**
Testing whether an endpoint is shared with *another endpoint* called 1,364 drafted lines
free at both ends — 432.5 km, 36 % of the draftsman's work. That is not a defect, it is how
CAD is drawn: lines cross without sharing a vertex and the noding step splits them. Testing
whether *any part of another line* passes within 0.5 m of the endpoint gives 28 lines and
10.5 km, which is the real figure. Both numbers appear here because the wrong one is easy
to produce and is the kind of thing that ends up in a report.

**The latent defect.** Every `auto_link` endpoint sits **exactly 1.0 m** short of the
corridor it is meant to join:

| Test tolerance | 0.05 m | 0.50 m | 1.00 m | 1.05 m | 2.00 m |
|---|---|---|---|---|---|
| `auto_link` endpoints touching nothing | 91.4 % | 91.4 % | 41.9 % | **0.0 %** | 0.0 % |

[Certain] — the cliff at 1.05 m is `buffer(1.0)` in `p0_auto.stitch`, which finds the
nearest points on *buffered* geometries and draws the link between them. The links stop on
the buffer boundary, not on the line.

It does no harm **in this run**: `p0_topology.stitch_parts` bridges any gap under 250 m and
re-nodes, so the final network is 2,216.5 km in 10 pieces with 99.8 % in the largest and
8 pieces under 0.5 km holding 1.51 km between them. But it is being fixed by a downstream
repair rather than not happening, and it means ~2,300 extra 1 m stubs in the noded layer.
**Change `nearest_points(nodes[u], nodes[v])` to operate on the unbuffered geometry.**

---

## 5. Do the sources agree where they overlap?

They barely overlap in the *output*, because `p0_auto` cuts `auto_road` wherever the
draftsman covers the same street. So the test was run on the treated road layer *before*
that cut: 4,261 treated roads, **574.8 km**, lie more than 75 % inside the draft's 25 m
band — the same streets described twice. Sampled every 20 m, 30,979 points, distance from
each to the nearest drafted line:

| | median | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|
| Offset, m | **1.55** | 4.32 | 9.94 | 13.67 | 23.63 | 98.4 |

| Within | 2 m | 5 m | 10 m | 15 m | 20 m |
|---|---|---|---|---|---|
| of samples | 56.2 % | 79.1 % | 90.6 % | 95.7 % | 97.5 % |

**By street class** (`StrCls`, 01 widest to 05 local):

| Class | samples | median offset | p90 | max |
|---|---|---|---|---|
| 01 | 642 | **10.85 m** | 12.89 | 22.66 |
| 02 | 296 | 5.06 m | 5.82 | 16.27 |
| 04 | 1,740 | 5.00 m | 10.00 | 36.83 |
| 05 | 28,191 | **1.30 m** | 8.59 | 98.37 |

[Certain] on the measurement. [Likely] on the reading: **the two sources agree on where
local streets are and disagree systematically on wide roads.** A 10.85 m median on class 01
is about half a carriageway — consistent with the road layer holding one centre line for a
divided or wide road while the draftsman puts the pipe on one side of it, which is what a
designer should do. That is a *correct* disagreement, not an error.

The residual worth checking is the 2.5 % of samples beyond 20 m — about 15 km of street
where the two sources genuinely place the centre line differently. Point locations are in
`W10/run/r2_offsets.csv`.

---

## 6. Is `auto_block` finding real streets? — the biggest open question

319.9 km recovered by rasterising the free space between platted plots, skeletonising it and
tracing the skeleton back to lines. **97.4 % of it became pipe.** Nobody had checked it
against the ground.

### 6a. Twelve pockets read over the imagery

`r3_skeleton_check.py` clusters `auto_block` into 228 pockets (median 0.46 km, max 22.3 km)
and samples twelve **stratified by length, not by count** — sampling by count would have
checked twelve 20 m fragments and none of the corridor that carries the network. Each is
rendered bare on the left and with the skeleton on the right, at
`W10/img/research/R3_pocket_*.png`. Imagery: `Hydraulic/Imagery/esri_z17_mosaic_3857.tif`,
1.19 m/px, covering 529.4 km² of the 531.4 km² boundary. **Local only; never copied into the
repository.**

| Pocket | km | plots within 60 m | What the imagery shows | Verdict |
|---|---|---|---|---|
| 155 | 15.5 | 781 | dense plot grid north of a built village; ground bare, faint grading only | paper street |
| 67 | 17.5 | 708 | platted grid on a rocky hillside above the settled wadi floor; no roads | paper street |
| 21 | 14.7 | 647 | unbuilt strip north of the built town; many X-shaped stubs | paper street + artefact |
| 123 | 6.6 | 165 | mixed — some plot-grid rows real, some skeleton across eroded open ground | mixed |
| 157 | 4.9 | 142 | — | not read |
| 43 | 4.5 | 165 | large subdivision, **entirely bare desert**; skeleton draws the whole grid | paper street |
| 196 | 3.4 | 117 | empty subdivision; a clean central spine, plus Y-shaped fragments in open ground | paper street + artefact |
| 97 | 1.9 | 220 | regular grid **with visible graded tracks**; skeleton follows the plot rows | **real street** |
| 125 | 1.8 | 42 | — | not read |
| 151 | 0.8 | 52 | empty platted block on eroded ground with a wadi through it; fragments outside the plots | **artefact** |
| 172 | 0.8 | 24 | scattered rural plots; red fragments follow **no** visible track; isolated 30–80 m stubs | **artefact** |
| 2 | 0.5 | 20 | farm compound; branching Y-shapes in the gaps between strip plots, one crossing a plantation | **artefact** |

Eight read, four verdicts each way at the small end. [Likely] as a generalisation from eight
frames. The pattern is consistent and has a mechanism:

- **In platted subdivisions the skeleton is right about geometry and silent about time.**
  The street reserve *is* the negative space between blocks and the skeleton finds it
  correctly. But the ground is desert. The corridor is as good as the plat and no better.
- **In scattered rural settlement it is an artefact.** Where plots are large, irregular and
  far apart, the "free space" is not a street reserve, and skeletonising it produces
  branching Y and X shapes that follow nothing. Pockets 2, 151 and 172 are this.
- **Where a subdivision is partly occupied it works** (pocket 97): the plots are regular,
  the streets are graded, and the skeleton lands on them.

Caveat: the mosaic has holes (black rectangles in pockets 155, 67, 196, 21). None fell on a
skeleton pocket being judged.

### 6b. Is the ground built? — the whole network, not twelve frames

W3 classified every plot built or not (`BUILT_FIN`: 20,399 of 61,272, 33.3 %). Built fraction
of the plots each corridor fronts within 60 m:

| Source | km | no plot within 60 m | **0 % built** | < 25 % | 25–75 % | > 75 % | built % of plots fronted |
|---|---|---|---|---|---|---|---|
| `draft` | 1,195.4 | 74.0 | 152.8 | 299.2 | 454.4 | 215.0 | **47.0 %** |
| `auto_road` | 604.3 | 60.9 | 69.3 | 85.8 | 255.6 | 132.7 | **57.0 %** |
| `auto_block` | 319.8 | 0.0 | **143.1** | 76.6 | 85.5 | 14.7 | **19.2 %** |
| `auto_link` | 92.3 | 0.0 | **40.1** | 17.8 | 28.8 | 5.6 | **23.0 %** |

[Certain]. **143.1 km of `auto_block` — 45 % of it — fronts plots of which not one is
built**, and 69 % fronts ground under 25 % built. `auto_link` is 63 % in the same condition.
The two good sources sit at 47–57 % built. The visual impression generalises.

### 6c. Is there a street there? — imagery contrast, with controls

A street in this landscape reads: graded earth brighter than the desert, asphalt darker. For
each sample point, mean brightness at the corridor against the mean 12 m either side,
perpendicular. **The threshold is set by a control, not chosen**: the level 75 % of open
ground stays below, which here is 15.17 brightness units.

| Set | samples | median abs. contrast | p90 | **% above threshold** |
|---|---|---|---|---|
| open ground (≥100 m from any corridor) | 872 | 6.33 | 28.17 | **25.0 %** (by construction) |
| `auto_block` | 4,465 | 10.33 | 40.17 | **37.1 %** |
| `auto_link` | 4,813 | 11.50 | 46.50 | **41.5 %** |
| `draft` | 21,899 | 17.33 | 61.50 | **54.0 %** |
| `auto_road` | 20,248 | 22.33 | 60.67 | **64.0 %** |

[Certain] on the numbers. [Likely] on the reading: **`auto_block` sits closer to open desert
than to a drawn corridor.** Against a 25 % floor and a 54 % benchmark, its 37.1 % is about
40 % of the way from "nothing there" to "a street the draftsman traced". `auto_road` scores
highest, which is the sanity check the test needed — a road layer *is* roads.

Limitations, stated because they bound the claim: the open-ground control yielded only 872
usable samples of 3,000 attempts (mosaic holes and points outside coverage); open ground in
this terrain has real texture, so the 25 % floor is not zero; and a 12 m offset assumes a
street under about 24 m wide.

### 6d. What this means

**`auto_block` is not wrong, it is early.** [Likely] It correctly reads a street reserve
that the cadastre defines and construction has not yet built. For a design to saturation
that is legitimate. But three things follow and none of them is currently stated in the
design:

1. Its alignment is only as good as the plat, and the plat can be revised before the road is
   built. Every metre of `auto_block` is provisional in a way `draft` is not.
2. In scattered rural settlement — pockets 2, 151, 172 — it is producing lines that are not
   streets at all. 5,089 fragments under 15 m and 1,854 lines connected to nothing at either
   end are the measurable trace of the same thing.
3. 46.7 km of `auto_block` pipe runs more than 3 m inside a registered plot, which no
   platted street reserve should do. That is the internal contradiction: if the skeleton
   were reading the reserve correctly it would not be inside the plots that define it.

---

## What reaches the pipe

| Source | pipe km | wadi | dual | inside plots | collects nothing | collects **and** conveys nothing |
|---|---|---|---|---|---|---|
| `draft` | 911.8 | 49.5 (5.4 %) | 0.43 | 15.5 (1.7 %) | 73.4 (8.1 %) | 30.4 (3.3 %) |
| `auto_road` | 520.7 | **60.0 (11.5 %)** | 2.68 | 46.5 (8.9 %) | **82.4 (15.8 %)** | **59.6 (11.4 %)** |
| `auto_block` | 311.4 | 14.6 (4.7 %) | 0.05 | **46.7 (15.0 %)** | 30.0 (9.6 %) | 21.9 (7.0 %) |
| `auto_link` | 92.2 | 6.5 (7.0 %) | 0.14 | **21.1 (22.9 %)** | 7.5 (8.1 %) | 4.7 (5.1 %) |
| trunk / other | 46.8 | 5.4 (11.5 %) | 0.34 | 1.6 (3.4 %) | 1.7 (3.6 %) | 0.7 (1.5 %) |
| **Total** | **1,882.9** | **136.1 (7.2 %)** | **3.64 (0.19 %)** | **131.4 (7.0 %)** | **195.0 (10.4 %)** | **117.3 (6.2 %)** |

The last two columns belong to the companion note `WHAT_TO_SEWER.md`; they are here because
they are the strongest evidence about corridor quality. **`auto_road` produces half the
removable pipe on 28 % of the length.** The road layer reaches places the cadastre does not,
and the design followed it there.

---

## The quality layer

`W10/shp/W10_corridor_quality.shp`, one row per corridor line, 22,827 rows:

| Field | Meaning |
|---|---|
| `SRC`, `CORR_ID`, `LEN_M` | source, id, length |
| `DUAL4_M` … `DUAL12_M`, `ON_DUAL_M` | length inside each dual-carriageway band; `ON_DUAL_M` = the 6 m band |
| `WADI_M` | length on hazard class ≥ 4 |
| `PLOT_M`, `PLOTIN_M` | length inside a plot; length more than 3 m inside one |
| `DUP_M` | length within 8 m of a **near-parallel** unconnected corridor |
| `NVERT`, `MEDSEG_M`, `MAXSEG_M`, `VPER100M` | vertex statistics |
| `DANGLES`, `SHORT` | 0/1/2 free ends; shorter than 15 m |
| `F_DUAL`, `F_WADI`, `F_PLOT`, `F_DUP` | the same as a fraction of the line |
| `NPLOT`, `NBUILT`, `BUILTFRAC` | plots within 60 m, how many are built, and the ratio |
| `QFLAG` | `unbuildable` (any defect over 25 % of the line) · `suspect` · `ok` |

`QFLAG` is a triage aid, **not a length**: a 300 m line 26 % on wadi ground is flagged
whole. Use the metre columns for quantities. Flagged: 374.8 km `unbuildable`, 328.7 km
`suspect`, 1,508.4 km `ok`.

Duplicate corridors are worth a note on method. Proximity alone is useless — every junction
puts two lines within 8 m. The test used is proximity **plus** bearing within 25°, which a
crossing fails and a doubled-up street passes. That took the figure from 230.9 km to
140.8 km, and the 90 km difference was junctions.

---

## What to do

| | Action | Effort | Why |
|---|---|---|---|
| 1 | **Wait for the draftsman on the 412 km of `auto_block` + `auto_link`, or have him check it.** It is 22 % of the network and it fails every quality test | his time | 97.4 % of it became pipe, 15–23 % of it runs through plots, and 45 % of it fronts nothing built |
| 2 | **Re-route `auto_road` off the wadi floors, or accept it and price the protection.** 60.0 km of pipe | routing already charges for it; the corridors do not exist elsewhere | The road follows the wadi because that is the flat ground. This is a real conflict, not an error |
| 3 | **Fix `p0_auto.stitch`**: `nearest_points` on the unbuffered geometry | one line | Every link stops 1.0 m short and a downstream repair hides it |
| 4 | **Raise `SIMPLIFY_M` in `skeleton.py` and drop fragments under 15 m before stitching** | small | 5,089 fragments and 10.2 km of debris entering the graph |
| 5 | **Check the 15 km where `draft` and `auto_road` disagree by more than 20 m** | `r2_offsets.csv` | One of the two is in the wrong street |
| 6 | **Say in the report that `auto_block` is a cadastral reserve, not an observed street** | wording | It is 311.4 km of pipe whose alignment is provisional, and the report does not currently say so |

---

## Figures

| | |
|---|---|
| `R_F1_corridors_by_source.png` | the network by source. The draftsman has the town; the synthetic sources hold the periphery — which is where the marginal network is |
| `R_F2_corridor_defects.png` | wadi, through-plot and duplicate corridors against the whole network |
| `R_F3_ground_truth.png` | the two objective tests: built status, and imagery contrast against controls |
| `R3_pocket_*.png` | twelve skeleton pockets, bare imagery beside the same frame with the skeleton |

## Re-running

```
python W10/py/research/r1_corridor_quality.py    # defects per corridor  (~2 min)
python W10/py/research/r2_agreement.py           # offsets, connectivity, pipe by source
python W10/py/research/r3_skeleton_check.py      # the pocket renders    (imagery required)
python W10/py/research/r4_ground_truth.py        # built status + imagery contrast
python W10/py/research/r8_pipe_defects.py        # the same defects on the pipe
python W10/py/research/r9_figures.py             # the figures
```

Records: `W10/run/r1_corridor_quality.csv`, `r2_offsets.csv`, `r2_pipe_by_source.csv`,
`r3_pockets.csv`, `r3_sample.csv`, `r4_built_status.csv`, `r4_street_contrast.csv`,
`r8_pipe_defects.csv`.
