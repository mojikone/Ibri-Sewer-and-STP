# W13 evidence: the numbers behind the rules

Companion to `W13_DESIGN_LOGIC.md`, which carries rules only (engineer, 2026-09-07). Every
measurement that supports a rule, every check against the 2006 as-built network, and every run
result is recorded here, dated, so a rule can be traced to what was measured without the rule
file turning into a report.

The as-built used throughout is `W7/shp/EXISTING_SEWERLINE.shp` with `OP_STATUE = 1`: 3,267
segments, 111.6 km, 3,268 manholes by ID, inverts and ground levels on 2,144 segments (66 %),
no diameters recorded, project codes 5A-1 to 5A-5 and 8F-1.

## Checks by rule

**Rule 5, one outlet per junction (2026-09-07).** Of 3,268 built manholes, exactly one has two
pipes leaving it (`5A-2-30-MH235`). NAMA never fans out.

**Rule 5, only sub-mains join the main pipe (2026-09-07).** NAMA's trunk main in this area is
4.5 km. 21 pipes discharge into it at 18 distinct manholes: 8 sub mains and 13 laterals. On the
4.0 km trunk piece the joins are spaced at a median of 167 m (min 2, max 387). 14.4 km of
built pipe, 135 segments, runs within 40 m of the trunk without joining it. The Stage A ground
gave 96 joins on the drawn main pipe, 71 of them carrying under 0.5 km of street.

**Rule 8, one gradient per run (2026-09-07).** Of 278 built street runs of three or more pipes
between junctions, 153 (55 %) carry one gradient throughout (spread of 0.3 mm/m or less);
median spread 0.14 mm/m, 75th percentile 5.14 mm/m where the ground is steep. Median run 160 m,
6 pipes. Built gradients: median 6.00 mm/m; the most common values are 6.0 (309 pipes), 5.0
(147), 6.1, 5.9, 5.1. Built depths (4,288 manhole ends): median 1.92 m, 90th percentile 4.57 m,
99th 6.21 m, maximum 8.85 m.

**Rule 12, chamber spacing (2026-09-07).** NAMA's manhole-to-manhole lengths: median 30 m,
mean 34 m, 90th percentile 38 m; 0.1 % exceed 100 m. Most common lengths 30, 35, 31, 25, 28,
24 m; a quarter fall within 1 m of a multiple of 10. That is 3,268 manholes on 111.6 km,
against W8's 1,415 on 71.6 km at the 100 m split. W8 tested tighter spacing on the test area
and found it does not keep trenches shallower. **Engineer's decision, 2026-09-07: follow the
guideline spacing**, divided evenly and rounded (rule 12); W8's split does this: 230 m gives
80, 80, 70; 250 m gives 90, 80, 80; 105 m gives 55, 50.

**Rule 2, what a sink means (2026-09-07).** 55 of the 65 Stage A sink basins have built sewer
inside them, and NAMA left them by gravity at depths in line with the spill plus cover:

| Basin | Our spill (m) | NAMA depth inside, median / max (m) |
|---|---|---|
| C03, east north, 9.6 km | 3.0 | 1.7 / 5.4 |
| C04, west, 9.4 km | 4.5 | 2.3 / 7.0 |
| C05, west, 6.7 km | 2.4 | 2.5 / 6.1 |
| C08, west, 2.7 km | 2.5 | 3.4 / 5.6 |
| C12, west, 2.1 km | 5.3 | 2.4 / 6.9 |
| C15, west, 1.7 km | 6.6 | 2.6 / 4.8 |

In the west settlement the spill is measured toward the main pipe, uphill, while NAMA's route
to the STP is cross-country and not a DXF street, so those spills overstate the cost; rule 3's
direct link and the STP as a target correct it.

**Rule 1, the terrain (2026-09-07).** The 2 m read of the 0.5 m blend minus NAMA's surveyed
ground at 2,144 upstream manholes: median +0.14 m, median absolute deviation 0.34 m, RMSE
1.01 m, 90 % within −0.90 to +1.25 m. Good for the fall of a sloping street; on a flat street
the noise is the size of the fall, which is why direction there is a design choice (rule 5).

## The road DXF, measured before adoption (2026-09-07)

| Layer | Lines | Length | Relation to the SHP roads |
|---|---|---|---|
| `piping center line` (existing) | 6,419 | 918 km | 89 % within 10 m of an SHP road |
| `piping center line-propo-01` (added) | 6,195 | 902 km | 7 % near any SHP road; drawn through planned plots |

Dual carriageways: 0.2 km of DXF line runs along one. Topology: 0 unnoded crossings in 22,276
intersection points; 57 line ends stop 0.3 to 3 m short of another line. Plots: 97 % (existing)
and 99 % (added) of length outside any plot. Dual carriageways as gaps: 1,120 line ends stop at
one, 7 crossings drawn. Connectivity: one component of 1,759 km, 57 small ones totalling about
60 km. SHP roads with no DXF line within 10 m: 290 km inside the boundary, almost all access
roads, 67 km within 30 m of a built or planned plot (engineer: not added). DXF lines running
parallel to a dual carriageway at 3 to 8 m: 1.7 km (engineer: service roads); at 8 to 20 m:
36 km.

## Stage A, first run on the built area (2026-09-07)

`python W13/py/run_stage_a.py`, 41 seconds. Drawing `W13/dxf/W13_A_ground.dxf`; shapefiles
`W13/shp/W13_A_*`; pictures `W13/img/W13_A_*.png`; numbers `W13/run/stage_a.json`.

| | |
|---|---|
| Area | 9.09 km², the 60 m envelope of the 111.6 km built in 2006, holes filled |
| Streets | 146.0 km of DXF street, 1,980 runs junction to junction, 82 split at a crest (41) or sag (41) |
| Raw ground | 100 km falls steeper than 0.5 %, 36 km flatter, 10 km level within 0.1 m; 290 raw sinks |
| Targets | 114 junctions within 30 m of the main pipe, 1 at the STP |
| After filling hollows to 2 m | 187 catchments: 96 JOIN (84 km), 1 STP, 65 SINK (57 km, spill 2.4 to 10.3 m), 25 LOW islands (5 km, 23 of them under 0.5 km) |
| Against the ground | 11.4 km of run flows over the rim of a filled hollow |
| Largest | C01 JOIN 22 km and C02 JOIN 20 km (east, south and centre); C03 SINK 9.6 km, spill 3.0 m (east, north); the west settlement is SINKs of 2.4 to 6.6 m spill falling south-west, toward where NAMA built its own trunk |
| Join tolerance | at 12 m the 24 km catchment C01 ended 23 m short of the drawn main pipe; nodes within 12 / 20 / 30 / 40 m: 78 / 98 / 114 / 138 |

What the engineer found in the drawing: loops and two outlets at a junction; several catchments
mixed on the flat grid in the south-east; no connector drawn from the streets to the main pipe;
gradients varying along a street. Each became a rule (rules 5, 8, 12) and the rerun in the
logic file.

## Stage A rerun as a tree (2026-09-07), final after the engineer's second look and the QGIS check

Same runner, 88 seconds (the terrain window now covers both targets). Drawing
`W13/dxf/W13_A_tree.dxf` (the ground drawing is kept as `W13_A_ground.dxf` for reference);
shapefiles `W13/shp/W13_A_tree_*`; pictures `W13/img/W13_A_tree_*.png` and the QGIS close-ups
`W13/img/qgis_check_*.png`; numbers `W13/run/stage_a.json`; QGIS group `Claude W13 A`.

| | |
|---|---|
| Area | 7.21 km², the 60 m envelope of the built laterals and sub mains with the trunk clipped to the settlements; 119.8 km of DXF street, 1,732 runs |
| Joins | 47 candidates on the ground (96 before the corridor came out); 23 kept at 150 m spacing, 24 dropped into a neighbour, 3 restored because their streets had nowhere else to go |
| Direct links (rule 3) | 7 to the main pipe's invert (12 before links were held to the join spacing); none to the STP, every west-settlement line to the STP crosses plots |
| Sub-mains | 18.4 km (17 % of the network); 600 m stem floor, 1,500 m side stems |
| Tree | 1,215 tree runs, 517 leftovers, 0 unreached; **no loops, one outlet per node, no pipe ends nowhere** |
| Branches and heads | 508 branches, 28.6 km; 485 heads at the first gate, 23 at 10 m; 217 dead-end tree heads trimmed to the first gate |
| Tiers | sub main 18.4 km, lateral 62.0 km, branch 28.6 km |
| Catchments | 83: 23 JOIN (59.3 km), 7 LINK to the main pipe (4.3 km), 45 SINK (44.0 km), 8 LOW (1.4 km); 43 of the 83 carry under 0.3 km, 20 under 0.1 km |
| East | C01 JOIN 19.5 km, C02 JOIN 18.9 km; the northern basin links to the main pipe over 189 m with 3.0 m of fall to the invert |
| West | C03 8.8 km (spill 4.5 m toward the main pipe; to the STP +6.8 m over 3.4 km = 0.20 %), C04 6.1 km (2.4 m; +8.9 m over 3.5 km), C10 2.1 km, C16 1.6 km |

Defects found and fixed between the first tree and this one: the trunk corridor to the STP was
inside the area and its clipped street stubs made one-run catchments on the main pipe
(engineer); 256 branches drained into junctions whose outgoing run had been trimmed away as if
it were a head (programmatic check); the terrain window stopped at the area and clamped the
STP's level (the west's fall to the STP read −1.1 m instead of +6.8 m); links were not held to
the join spacing. Programmatic checks that pass: no loops, one outlet per node, no pipe ending
nowhere, no outlet labels within 20 m of another. Checks that report rather than fix: 23 heads
sit inside a plot and 54 pipes run more than 2 m inside one (1.3 km, the draftsman's lines);
12 head gaps exceed 45 m (max 81 m, no house near the start of the street).

## Stage A, basins resolved and the west settlement sent to the STP (2026-09-07, evening)

The engineer's third look: isolated groups are not sub-networks. Every basin now drains, and
the west settlement links to the STP along NAMA's corridor. Same runner, 90 seconds.

The engineer's fourth look: a 189 m link from the northern basin jumped over streets and
another sub-network to reach the main pipe. Links to the main pipe are now at most 150 m with
no street across the line, and the corridor to the STP is a second target with entry joins
reached by the settlement's own streets.

| | |
|---|---|
| Catchments | 38: **23 JOIN (81.9 km), 1 entry to the STP corridor (25.2 km, the west settlement), 3 LINK to the main pipe (0.7 km, all under 60 m), 0 SINK, 11 LOW islands (1.6 km)** |
| Basins crossed by depth | 39 marked; extra depth to leave them median 3.0 m, maximum 5.1 m; none over the 10 m pocket limit; the northern basin of the east now drains by its streets into the 5.2 km join at the top of the main pipe |
| West settlement | one sub-network of 25.2 km, outlet at its south edge (445219, 2566295); the corridor route to the STP falls 8.2 m over about 6 km, 0.14 %, within the DN600 class; NAMA's own western trunk (71 segments, 5A-5, with inverts) falls 0.219 % overall, median gradient 6.0 mm/m, depth median 2.7 m, max 6.9 m |
| East settlement | C01 29.4 km and C02 26.5 km on the main pipe; C04 5.2 km at the top of the main pipe now holds the northern basin |
| Tiers | sub main 22.8 km, lateral 61.3 km, branch 25.3 km |
| Checks | no loops, one outlet per node, no pipe ends nowhere |

On the way, two misfires of the corridor rule, both fixed: the eastern trunk corridor lies
under the drawn main pipe, so basins entering it were sent 9 km to the STP instead of 189 m to
the main pipe; and the western and eastern trunks end 37 m apart at the works, so only one of
them counted as reaching the STP until both ends were tied to one STP node.

What Stage B has to do with it: lay it, and decide the 36 basins on depth.

## Stage A, sub-mains as streets and the outlet at the corridor (2026-09-07, night)

The engineer's fifth look, on the west settlement: the sub-mains followed the streams and
converged on a stream exit at the west edge, while the true outlet is the south-west corner
where NAMA's trunk leaves the settlement. Two causes, both fixed: the heaviest-stem method read
sub-mains off the terrain's steepest descent, and the corridor included NAMA's trunk inside the
settlement, so the entry landed where that trunk begins.

| | |
|---|---|
| Street chains | 591 chains within 25° of deflection, 128 of them 250 m or longer; 63 became sub-mains |
| Sub-mains | 34.2 km (31 % of the network); the west settlement's are the three long parallel streets and the edge street, as the engineer sketched; the east's the long north-south streets |
| STP target level | the works inlet invert, 323.0 m, from the as-built: both trunks end at manhole 5A-1-FL-STP with inverts 322.7 and 323.0 m and ground 325.0 m; the terrain at the plant point reads 329.0 m, 6 m too high as a target |
| Corridor outside the settlement | 4 lines; entry join at (445360, 2566056), the south-west corner, 8 m from the corridor's upstream end; 12.3 m of fall to the inlet invert over 5.6 km, 0.22 %, against NAMA's own trunk at 0.219 % |
| Catchments | 30: 15 JOIN (83.0 km), 1 corridor entry to the STP (24.0 km, the west), 3 LINK to the main pipe (0.7 km), no sink, 11 LOW islands (1.6 km) |
| Basins crossed by depth | 37, median 2.8 m, max 5.1 m |
| Tiers | sub main 34.2 km, lateral 49.8 km, branch 25.3 km |
| Checks | no loops, one outlet per node, no pipe ends nowhere |

Open for the engineer: 250 m is the shortest street chain that becomes a sub-main, and it
takes cross streets of 300 to 600 m in with the long ones. NAMA's sub mains are under a tenth
of its network; ours are a third at 250 m. The threshold is a one-line change.

## Stage A, the depth check and the reroutes (2026-09-07, late night)

The engineer's sixth look: pipe size comes from the flow, never to flatten a gradient; above
12 m is not a design; can a reroute help? The runner now sizes and lays every run (rule 9),
and the answer was found by reading the governing path into the deepest chamber, five times.
Same runner, 88 seconds. The run's working state is kept in `W13/run/stage_a_state.pkl`, so
any question about a node or a pipe is answered in seconds from the record (not committed).

| Run | Deepest | What the governing path showed | Fix |
|---|---|---|---|
| 1 | **20.0 m**, west north join | 2.26 km of DN200 at 0.5 % climbing 7.4 m from the interior (333.8 m) to the join (341.1 m); the flood had sent the interior to the corner, the chain rule pointed the street uphill because a join is an outlet and "nearer an outlet" won | cut chains where the fall turns, orient by the fall |
| 2 | 11.6 m, east hollow | the hollow at 362.5 m left over a 367.6 m saddle to reach a sub-main 460 m away while its own rim is 365.4 m; the valley street below the rim was laterals for 2.8 km | connector: a chain attaches through up to 250 m of the fall |
| 3 | **15.6 m**, east hollow | the hollow's east half, which the flood had sent down the valley at 8.6 m, was pulled onto a ridge sub-main and rode 2.3 km round the hollow at 0.5 % | a node routes only inside its own catchment |
| 4 | 11.1 m | passes; but the 29.8 km east-centre catchment had 2.0 km of sub-main: its long streets were cut into fragments because on level ground the flood's arrow flips every few runs | only a decided run (over 0.1 m on the filled surface) cuts |
| 5 | 13.1 m, west rim | the same catchment was not level at all: it rises 15 m, and the flood gave the whole slope to its lowest join. Assigned by rule 5's cost, the slope splits between the four joins on its frontage. The west interior then went 1,000 m east to the nearest sub-main node and 650 m along it to the rim, past an 850 m street to the same rim, because sub-main edges were free | outlets by least depth; the search runs from the outlets with sub-mains at half cost |
| 6 | **11.5 m**, west rim | the interior (333.7 m) leaves over its 338.6 m rim by the edge street, 4.9 m of fill plus 0.5 % over 850 m | none; passes |

The depth weight was tested at 500, 2,000 and 5,000 m per metre between runs 1 and 2:
11.58, 11.44, 11.44 m. Depth is set by the structure of the tree, not by the weight.

| Final run | |
|---|---|
| Catchments | 37: **22 JOIN (86.9 km), 1 corridor entry to the STP (19.9 km, the west), 3 LINK to the main pipe (1.1 km), no sink, 11 LOW islands (1.6 km)**; 19 catchments under 0.3 km (7 JOIN stubs on the main pipe road, 10 islands, 2 links) |
| East | C01 33.8 km to (450575, 2567479), C03 16.3 km to (450261, 2567604), C07 4.1 km, C05 5.6 km, and six joins of 1.7 to 2.4 km along the west side of the main pipe road; the long north-south streets are the sub-mains |
| West | C02 19.9 km to the corner entry, sub-mains the long diagonals and the edge street; C04 6.0 km and C09 2.4 km to joins on the main pipe |
| Sub-mains | 33.0 km, 30 % of the network, 70 chains; 808 street chains, 226 cut at a crest, 218 at a turn of the fall |
| Tree | 1,261 tree runs, 471 leftovers, 0 unreached; 467 branches (24.6 km), 445 heads at the first gate, 22 at 10 m; 4 streets too short for a head (35 m) |
| Basins crossed by depth | 47, extra depth median 2.8 m, max 5.3 m |
| Load | 4,152 plots served, 5,530 properties at saturation |
| Diameters | DN200 105.3 km, DN250 2.0, DN315 1.3, DN400 0.9; every lateral and branch is DN200 |
| Depth | 1,765 chambers, median 1.55 m, 90th percentile 4.35 m, **maximum 11.47 m, none over 12 m**, 31 over 8 m (14 in the west, 10 in the east centre, 5 at the top of the main pipe, 2 in the west north) |
| Checks | no loops, one outlet per node, no pipe ends nowhere |

**NAMA on the same rim.** NAMA's western trunk main (5A-5, 16 segments, 6.2 km, inverts
recorded, diameter not) runs from the interior at ground 335.3 m and invert 333.0 m over the
rim at ground 338.3 to 338.4 m with an invert of 332.5 m, 5.9 m deep, on a constant **0.21 %**
to the corner and on to the works. 0.21 % is the Table 11 gradient of a DN400; the interior
serves about 350 properties, a DN200 by flow. NAMA bought its 5.9 m with a pipe sized for the
gradient; the rule as the engineer set it gives 11.5 m with a pipe sized for the flow.

Open for the engineer: the 7 stub catchments on the main pipe road, each a street touching
the main pipe with nowhere else to go, where the rule says only sub-mains join; the sub-main
share at 30 % against NAMA's tenth (the 250 m floor); the west rim at 11.5 m against NAMA's
5.9 m on the same line; and the mechanical form of rule 10, which was not needed on this
area and is not written.

## The test boundary: the west has no gravity way to the existing inlet (2026-09-08)

The engineer's seventh instruction: expand to `SHP/temp/W13 test boundary.shp`, connect the
west's north part to the part that goes to the works, and design a gravity pipe to the works
along the roads instead of taking NAMA's line. The main pipe was redrawn the same day. Same
runner, 49 seconds.

| Boundary | |
|---|---|
| Area | 21.37 km² in two parts; the east part 6.13 km², the west part 15.24 km² holding the west settlement, the works and the roads to it |
| Streets | 229.2 km of DXF street, 2,596 runs, 85 crest and 67 sag splits (the built area had 119.8 km) |
| Built network inside | 102.6 of the 111.6 km of 2006 sewer |
| Main pipe | 84.9 km drawn across the wilayat, 13.1 km inside the boundary; its south-west leg runs from the east's meeting point to the works along a ridge at 331 to 341 m, above the land on both sides |
| Plots | 7,643 built and planned plots served, 9,380 properties at saturation |

**What the engine finds.** 35 sub-networks: 29 joins (129 km), 1 to the works (25.3 km, the
low ground south-west of it), 3 pockets (55.6 km: the west settlement in two, 28.8 and 20.1
km, and 6.7 km west of it), 2 islands. 31 chambers over 12 m, the deepest 19.4 m; 4
catchments fail: the west interior (19.4 m), the basin south of the west settlement (17.8 m),
the low ground at the works (17.3 m, and it arrives **12.3 m under the inlet**), and the
basin between the west settlement and the ridge (14.0 m). The east settlement is as before:
C01 33.6 km at 6.7 m.

**Why the roads cannot deliver to the inlet at 323.0 m.** Measured along the streets from
every failing pocket to the works node, laid at cover from the pocket at each Table 11
gradient:

| From | Ground | Length | DN315 0.270 % | DN400 0.205 % | DN500 0.155 % | DN600 0.125 % | DN700 0.100 % |
|---|---|---|---|---|---|---|---|
| west corner | 335.0 | 5.6 km | 318.3 | 321.2 | 321.7 | 322.0 | 322.1 |
| west settlement low | 334.5 | 6.5 km | 315.4 | 319.6 | 321.7 | 322.0 | 322.1 |
| west interior low | 333.7 | 6.5 km | 314.6 | 318.8 | 321.7 | 322.0 | 322.1 |
| basin south (C05) | 330.9 | 4.2 km | 317.8 | 320.6 | 321.7 | 322.0 | 322.1 |
| basin by the ridge (C09) | 337.8 | 6.6 km | 318.5 | 321.2 | 321.7 | 322.0 | 322.1 |
| low ground SW (C03) | 326.7 | 3.8 km | 314.9 | 317.4 | 319.3 | 320.4 | 321.4 |
| west of the settlement (C10) | 327.7 | 8.1 km | 304.3 | 309.5 | 313.6 | 316.0 | 318.0 |

Arrival invert in metres against the inlet at 323.0. Every route from the west arrives at the
same 321.7 to 322.1 m once the pipe is DN500 or larger, whatever the start: the arrival is not
set by the gradient but by the road into the works, whose ground dips to **324.2 m about 800 m
before the plant** (hazard class 1, not a wadi) and rises to 328 m at the gate. A pipe at
cover under 324.2 m is at 322.6 m before the last stretch begins. NAMA's trunk alignment
never drops below 325.2 m and its trunk arrives at 322.99 m; at its own 0.14 % it passes
that low point with about 1.2 m to invert, under the guideline cover for its size.

**And why a lower inlet is not enough.** Run again with the inlet at 321.5 m
(`run/stage_a_scenario_inlet321.json`, `dxf/W13_A_tree_scenario_inlet321.dxf`): nothing
changes. The west's pockets are sized on their own properties, a DN315 at 0.27 %, and at that
gradient a 6.5 km trunk digs 12.7 m and arrives at 315 m. Only the whole west on one DN500
makes 321.7 m, and only if it starts at cover at the corner; but the interior reaches the
corner 9.6 m deep over its 4.9 m rim, and from that invert the trunk arrives near 317 m. The
arithmetic: rim 4.9 m, plus 0.5 % over 850 m to the corner, plus 0.155 % over 5.6 km to the
works, against 12 m of fall from the corner's ground to the inlet.

**The sub-network arithmetic the check surfaced.** Judged against a main pipe invert of ground
minus 3 m, 14 of the 29 join catchments arrive under it, by up to 11 m. The 3 m was an
allowance for the direct-link test; the main pipe's profile is Stage C's and will be set by
what arrives at its joins, so the check now applies at the works inlet only. It is a warning
worth carrying: the main pipe on the ridge will be deep.

**The mechanical rule 10, first use.** It ran three rounds, traced each failure to its basin,
offered a trunk to every target, and refused each one with a reason (12 m passed at a named
node on the ridge, or arrives under the inlet). One trunk it did accept, sized on pockets that
were supposed to join it and never could, was laid two sizes smaller by the flow and dug
deeper than the route was checked at; trunks are sized on their own flow only now.

For the engineer, three ways out, none of them a rule change the engine can make alone:

1. **One lift at the works.** Let everything arrive at the plant boundary as deep as gravity
   brings it within 12 m, and lift once in an inlet pumping station, which a plant of this
   size has anyway. The west's trunk then arrives at about 317 m, 8 to 11 m deep at the gate.
2. **NAMA's way.** A single trunk from the west interior at a DN600 to DN700 gradient, 0.10 to
   0.125 %, on NAMA's alignment for the last kilometre, a pipe two to three sizes above its
   flow, declared as a deviation.
3. **A pumping station at the west's corner**, lifting about 7 m into a DN500 trunk at
   0.155 % along the roads, plus a second for the low ground south-west of the works, which
   no inlet level short of 316 m reaches by gravity.

The low ground south-west of the works (C03, 25 km, and C10, 7 km) is planned land at 323 to
329 m, at the inlet's own level: it needs a pump under every option.

## Everything on gravity: the west converges on the works (2026-09-08, later)

The engineer's answer to the three ways out: none of them yet. The network converges on the
outlet, everything on gravity, the inlet stays at 323.0 m, the last kilometre may use NAMA's
alignment. Same runner, 51 seconds, rule 10 running for two rounds and keeping the better.

Tried first without the pocket cap at all: the west settlement went 6 km east to a ridge join
at 37 m, arriving 25.6 m under the main pipe's floor, because rule 5's cost prices every
route at a DN200's 0.5 % and a 10 m climb is cheaper than 6.5 km of level street. The cap
stays; a pocket takes its least-violation trunk instead.

| The run | |
|---|---|
| Sub-networks | 35: 29 joins (106.8 km), 3 to the works (98.8 km: the whole west side on one designed trunk), **1 pump** (6.4 km, the low ground west of the settlement at 327.7 m, 246 plots, whose best route violated by 19 m), 2 islands |
| The west's trunk | 11.9 km of trunk tier; checked from the settlement's low at DN315 and 0.27 %, 6.55 km, 12.8 m deep and 7.8 m under the inlet; laid by the flow at DN500 to DN600 for 8 km of it, 16.1 m at its deepest |
| Depth | 2,634 chambers, median 1.55 m, 90th percentile 5.0 m, **27 chambers over 12 m, deepest 16.1 m**; 11 in the west settlement, 11 in the low ground west and south-west, 5 between the settlement and the ridge |
| At the works | the trunk arrives at **315.2 m, 7.8 m under the inlet**, 12.9 m deep at the plant gate |
| Joins | 35 of 35 floored by the main pipe's profile; 4 sub-networks arrive 1 to 2.4 m under their join's floor |
| East | unchanged: 33.6 km at 6.7 m |
| Basins crossed by depth | 84, median 2.9 m, max 6.5 m |

What the mechanical rule 10 did: round 1 offered nine basins a trunk, routed eight and cut
one for a pump, taking the deepest from 30.8 to 16.1 m; round 2 routed three more and made
it worse, 19.1 m, so the best round was laid again. Two engine faults found and fixed on the
way: every round trimmed the heads again on the same runs, shrinking the network by 90 plots
a round; and a basin was being sized on the whole catchment's flow above its deepest chamber.

**What the picture says.** The west can converge on the works by gravity along the roads and
NAMA's last kilometre, at flow-sized pipes, but not within the rules: 27 chambers past 12 m,
and the trunk 7.8 m under an inlet that stays at 323.0 m. The 7.8 m is the low ground
south-west of the works at 323 to 329 m plus the interior's rim; the 16.1 m is the basins
between the settlement and the ridge climbing into the trunk. The one pump is the low ground
west of the settlement.

## Whole-street sub-mains, and the link for C06 (2026-09-08, later still)

The engineer's rulings after reading the all-gravity picture: gravity first, pumps later; the
sub-networks first, their levels at the main pipe later; a sub-main runs the whole street,
cut only at a hill; rule 10 must not build pipes; and try a 187 m street link from
(444167.1, 2566069.5) to (444189.8, 2565883.5) for the low ground west of the settlement.
Same runner, 47 seconds; the DXF written as `W13_A_tree_new.dxf` because the engineer had the
other open.

| | Fall turns cut (earlier) | Whole street, crest only | Whole street, crest, sag and outlet cuts |
|---|---|---|---|
| Sub-main strings, longest | fragments, rule 10 trunks of 130 to 1,300 m | 3.9, 3.9, 3.9, 3.7, 3.5 km | same order |
| Sub-main km | 67.5 | 82.7 | 76.7 |
| Chambers over 12 m | 27 | 75 | 88 |
| Deepest | 16.1 m | 31.0 m | 31.9 m |
| At the works | 7.8 m under | 23.0 m under | 24.5 m under |
| Sub-networks | 35 | 21 | 30 |

**Where the 31.9 m comes from.** One whole street from the west settlement's interior runs
west into the low ground at 327.7 m (C06's basin), and back up east to the trunk head at
335.3 m. As one sub-main it carries the basin's 6.5 m of fill plus 0.5 % over 1.5 km, and
arrives at the trunk 26 m deep; the trunk then leaves the settlement at 30 m and reaches the
works 24.5 m under the inlet. The second case is a street that rises 5 m to a join on the
ridge, dragging its lower half up to 21 m. Cutting at a sag did not fire, because the flood's
own answer for that basin is to leave it along the same street, over its 334.2 m rim.

**The link for C06.** It connects: 30 m in the graph at 330.7 to 330.8 m. It does not rescue
C06: its low at 327.7 m is 3 m below the link and 4 km from an inlet 4.7 m below it, so the
route south costs 3 m of fill and 20 m of fall at 0.5 %, and the route east over the rim
costs 6.5 m of fill and 1.5 km. Rule 5's cost picks east. Either way the basin drags whatever
it joins past 12 m.

For the engineer: C06 as a pump, or left out of the boundary; and the rule for a street
that crosses a basin, since whole-street sub-mains give the strings asked for and 31.9 m.
