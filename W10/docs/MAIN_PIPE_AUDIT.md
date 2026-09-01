# Is the given main pipe workable? — W10 Phase 0.4, 2026-09-01

`SHP/Main Pipe/Main Pipe.shp`, 85.49 km in 54 features, 99 % inside the study boundary.
Everything downstream is designed to drain onto it, so this is asked and answered before
any of it is laid out.

Method: the alignment is turned into a graph with a node every 10 m — a ridge halfway
along a reach is exactly what a node-only check misses — ground is read from the 0.5 m
terrain blend, and the pipe is laid **as shallow as the cover rule allows**: invert at a
head is ground less 1.3 m cover less the outside diameter; further down it is the lower of
the upstream invert less the minimum gradient, and that same shallow level. Taking the
lower of the two lets the pipe rise back towards the surface whenever the ground falls
away, instead of carrying the depth it gained under a ridge for the rest of its length.
Diameter and gradient are swept, because neither is settled until the loads are allocated.

## The answer: the alignment works by gravity, with room to spare

| Component | Length | Deepest at DN1000, 0.10 % | Deepest at DN1400, 0.15 % | Points past 12 m |
|---|---|---|---|---|
| 0 — the main body | 73.19 km | **7.72 m** | 9.14 m | **0** |
| 1 — the western leg | 7.86 km | 5.87 m | 7.10 m | **0** |
| 2 — an eastern piece | 4.39 km | 10.80 m | 11.39 m | **0** |

Median cover is 2.5 m. Nothing anywhere reaches 12 m at any of the nine
diameter-and-gradient combinations tested.

Why it is so comfortable: the worst single rise above the running low point, going
downstream, is **4.5 m** on the south-east arm and **4.1 m** on the north-east arm. The
alignment is very nearly monotone downhill for 73 km. Cumulative "climb" measured on the
raw 10 m profile looks alarming — 136 m and 87 m — but it collapses to 5 m and 3 m when the
profile is smoothed over a kilometre, so almost all of it is surface roughness a trunk
sewer does not follow, not ridges it has to pass under.

## Continuity: three pieces, not two

| | Length | Ground | Nearest approach to component 0 |
|---|---|---|---|
| 0 | 73.19 km | 325.3 – 519.1 m | — |
| 1 (west) | 7.86 km | 332.4 – 345.8 m | **880 m** |
| 2 (east) | 4.39 km | 478.2 – 500.7 m | **2 m** |

**Component 2 is a drafting break, not a design problem.** Its end sits 2 m from the trunk
at the same ground level (478.2 m on both). Snap it and it is part of component 0.

**Component 1, the western leg, is genuinely separate** — as you said. What the levels show
is stronger than "not connected":

- Its outlet is its own low point, ground 332.36 m, invert 327.96 m, at 442092 E 2569064 N.
- At the closest approach the trunk is **higher** — ground 346.9 m, invert 344.04 m. Joining
  there means lifting about 16 m.
- Of 7,323 points on the trunk, only **325 have an invert below the west leg's outlet**, and
  every one of them is at the works. The nearest is **6.17 km** away.

So the west leg cannot reach the main trunk by gravity at any point along it.

## What the west leg can reach

Assuming a works inlet invert 4.0 m below ground, on a straight route:

| Destination | Distance | Gradient available | Deepest | Past 12 m |
|---|---|---|---|---|
| Existing works, 328.7 m | 6.18 km | **0.053 %** | 9.57 m | 0 |
| Proposed southern site, 311.7 m | 10.13 km | **0.200 %** | 10.48 m | 0 |

Both clear the depth limit. They do not both work hydraulically. At 0.053 % a DN1000 runs
about 0.70 m/s at full bore and a DN600 about 0.50 m/s, against a self-cleansing minimum of
0.75 m/s (G203-p26–27) — so the route to the existing works fails on velocity even though it
passes on depth. At 0.200 % a DN600 runs about 0.97 m/s and passes.

**The southern site turns the western leg from a pumping problem into a gravity one.**

## And it does the same for the south, and costs the main trunk nothing

| Route | Distance | Gradient | Deepest | Past 12 m |
|---|---|---|---|---|
| Main trunk outlet → southern site | 4.82 km | 0.286 % | 7.21 m | 0 |
| Lowest southern plot (311.6 m) → existing works | 5.05 km | **−0.338 %, uphill** | — | pumping certain |
| Lowest southern plot → southern site | 1.71 km | 0.23 % on a 4 m inlet | — | gravity |

Extending the trunk 4.82 km to the southern site is an easy gravity run. The 304 plots south
of N 2562000 currently have to be lifted 17 m to reach the existing works; to the southern
site they fall.

So one decision — where the works sits — answers three of the questions asked of this
stage: the western connection, the southern lift, and whether the plant should move.

## What is not proven yet

- **Every route above is a straight line on the terrain model, not a corridor.** A real
  route follows streets, is longer, and is therefore flatter and deeper. Depths of 9.6 and
  10.5 m have little margin against 12 m. This has to be re-tested on the corridor network
  in Phase 2 before the conclusion is relied on.
- **Nothing here prices the move.** The existing 1,800 m³/d works is a real asset; relocating
  means abandoning or repurposing it, acquiring land, and pumping treated effluent 4.8 km
  further back towards the irrigation demand. That is the Phase 4 appraisal, not this audit.
- **The trunk's own hydraulics are not checked** — only its levels. Diameter follows the
  load allocation in Phase 1.
- 0.54 km of the trunk runs within 6 m of a dual carriageway centre line, and 5.33 km within
  12 m. The tight band is what needs review.

## Where the numbers come from

`W10/py/p0_mainpipe.py`, outputs `W10/run/p0_mainpipe_depth.csv` and
`W10/shp/W10_mainpipe_profile.shp` (ground, invert and depth every 10 m), figure
`W10/img/W10_P0_mainpipe_profile.png`.

One correction worth recording: the first run of this audit reported a 159 m deep trunk.
The cause was an index rebuilt from a subgraph while the ground array was indexed on the
full graph, so elevations were read off the wrong nodes. The result was obviously wrong,
which is the only reason it was caught — a subtler version of the same bug would have
passed. The index is now passed in rather than rebuilt.
