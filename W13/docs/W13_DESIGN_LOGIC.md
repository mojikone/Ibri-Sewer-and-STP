# W13 design logic

Agreed 2026-09-07 between the engineer and Claude. This is the reasoning the engine is built
against. Change it by adding a dated line under the rule, never by rewriting the rule, so the
history of why a number moved stays readable.

The aim: a hydraulic design engine that runs the whole area in a few minutes, so different ways
of designing can be tried and compared, and that still reproduces the test-area gate first.

## The logic

1. **Sewage runs downhill.** Read the ground along the streets: sample the terrain on every
   centreline, take the fall junction to junction, point each street downhill. Derive the terrain
   streams and their Strahler order as the guide: high-order streams mark the valley streets and
   group the catchments; the hazard grid marks the wadis.
2. **Follow the arrows** from every junction until they stop. Where they stop is an outlet:
   either where the falling streets meet the main pipe, or a sink where every street rises away.
   Each outlet is one catchment.
   - 2026-09-07, Stage A method choices. The raw ground on the built area has 290 sinks, most of
     them cul-de-sacs falling away from their junction and small hollows in a street, which a
     pipe crosses by going a little deeper. So hollows are filled on the street graph by priority
     flood from the targets up to a spill of **2 m**; a sink needing more stays a **SINK** outlet
     labelled with its spill, because leaving it by gravity is a real cost for Stage B to decide.
     A part of the graph with no street path to any target is an island: its lowest node is a
     **LOW** outlet and the island is flooded from there. A junction within **30 m** of the drawn
     main pipe is a join (the main pipe is an eyeballed line; at 12 m a 24 km catchment ended
     23 m short of it). Inside a filled hollow the flow runs against the ground; those runs are
     classed AGAINST and drawn dash-dot, with a negative gradient.
3. **From each outlet, the gravity path to the main pipe is the spine.** One join per catchment.
   The ground sets the number of joins, not a cap.
   - 2026-09-07: where the streets give the outlet no proper way to the main pipe, connect the
     outlet to the main pipe directly, across open ground, provided no plot lies in the way. The
     link may cross a dual carriageway only at an underpass (the roads in the DXF that pass
     under one are the underpasses; engineer, 2026-09-07). An outlet that could reach the main
     pipe only across a dual carriageway with no underpass is reported as a pocket.
4. **Sub-mains first.** Long, straight, few bends. Low is the filter, long and straight is the
   choice. They earn their diameter from the houses they collect, and a bigger pipe reaches
   further on flat ground: about 2 km at DN200, 4 km at DN315, 5 km at DN400 before 12 m.
5. **Then hang the rest off them.** Every street drains to the sub-main below it, every house to
   the street it fronts. On flat ground, the shortest run to the nearest sub-main.
   - 2026-09-07 (engineer, from the Stage A drawing): **one outlet per junction, and no loops.**
     Which pipe leaves a junction is a design decision under the criteria and these rules, the
     sub-main first, then the lateral; the ground's steepest fall is one input, not the rule.
     Every other street on that junction starts as a head at the first house gate, the first
     plot's centroid dropped square onto the street, or 10 m along where no plot faces it, as in
     W8. **Checked against the as-built:** of 3,268 built manholes exactly one has two pipes
     leaving it.
   - 2026-09-07: **a street that touches the main pipe does not join it; only sub-mains join.**
     NAMA's 4.5 km trunk in this area takes 21 pipes at 18 manholes (8 sub mains, 13 laterals),
     median spacing 167 m, while 14.4 km of built pipe runs within 40 m of the trunk without
     joining it. The Stage A ground gave 96 joins; this rule brings it to NAMA's order. Every join
     is drawn as a connector from the street to the main pipe, on its own layer.
6. **A ridge is a boundary, not a place to build.** A street on a ridge drains whole into the
   lower side. A very long ridge street splits at the crest, two heads back to back.
7. **Gradient follows the ground in three bands.** Flatter than the minimum: lay at the minimum.
   Between the minimum and the velocity limit: parallel to the ground at cover. Steeper than
   3 m/s at peak flow: hold the gradient and take the rest as drops, 2 m per chamber at most,
   closer chambers if needed.
8. **Gradients are laid in steps of a tenth of that pipe's minimum gradient:** 0.5 mm/m at
   DN200, finer for bigger pipes. The diameter is earned by the flow, never chosen to flatten.
   - 2026-09-07 (engineer): **one gradient per street run, held until the cover is no longer
     enough.** The gradient changes only at a junction, or where holding it would breach the
     minimum cover or the maximum depth. G203-p29: "uniform slopes must be maintained between
     successive manholes". **As-built:** of 278 built street runs of three or more pipes, 55 %
     carry one gradient throughout, median spread 0.14 mm/m; NAMA's favourite values are 6.0 and
     5.0 mm/m; its depths are median 1.92 m, 90th percentile 4.57 m, maximum 8.85 m.
9. **Lay each catchment from its heads by rule 7.** That is the shallowest the route can ever be.
   Under 12 m at the main pipe: gravity, done.
10. **Over 12 m: reroute first.** A different join, a street where the ground helps, or the
    neighbouring catchment, street by street, for whatever can reach it within 12 m. Then cut
    where the pipe passes 12 m: a pump at the cut into the nearest gravity chamber, and the pipe
    restarts at cover. Never dig past 12 m to avoid a pump. Never pump to avoid a reroute. Until
    we cost, gravity within 12 m beats a pump.
11. **A closed hollow, or a ridge between a pocket and every neighbour, is a real pump.**

## What the engine does with each rule (proposed mapping, to be confirmed as it is built)

| Rule | Engine step | What it produces |
|---|---|---|
| 1 | read the ground | streets with fall, direction, nearest stream order; wadi flag |
| 2 | find outlets | every junction labelled with its outlet; outlets typed join / sink |
| 3 | spines | one route per outlet to the main pipe |
| 4 | sub-mains | the low, long, straight streets of each catchment, `TIER = sub main` |
| 5 | branches | streets to the sub-main below, houses to the fronting street, `TIER = lateral` |
| 6 | ridges | catchment boundaries at crests; long ridge streets split at the crest |
| 7, 8 | gradients | three bands, stepped; drops capped at 2 m |
| 9 | depth check | heads-down lay; depth at every chamber and along every trench |
| 10 | reroute, then cut | pumps only where a reroute could not remove them |
| 11 | real pumps | hollows and enclosed pockets, listed with the reason |

## Inputs (2026-09-07)

**Road network: `Hydraulic/DWG/road network 03092026 eyeballed.dxf`** (draftsman, 3 September
2026; UTM 40N metres). It replaces `SHP/Road centerline 2` as the corridor source.

| Layer | Meaning | Measured |
|---|---|---|
| `piping center line` | existing roads | 6,419 lines, 918 km; 89 % within 10 m of an SHP road |
| `piping center line-propo-01` | streets added where roads were missing, mostly through planned plots | 6,195 lines, 902 km; 7 % near any SHP road |

What the drawing already does for us: dual carriageways are left out (0.2 km along one), every
intersection is a node (0 unnoded crossings in 22,276), and the lines sit in the road reserve
(97 to 99 % of length outside any plot).

How the engine treats it:

- **Snap** line ends within 3 m (57 gaps of 0.3 to 3 m).
- **No crossings of dual carriageways are generated** (engineer, 2026-09-07). The drawing is the
  network as it may be used: 1,120 line ends stop at a dual carriageway and the 7 crossings the
  draftsman drew are the only ones. The engine never adds one.
- **Islands are reported, never dropped silently**: 57 small components, about 60 km in all,
  against one main component of 1,759 km. Each reaches the main pipe by its streets, or by the
  direct link of rule 3, or is reported as a pocket.
- **No attributes** come with it. None are needed: exclusion is already done, and rule 4 picks
  sub-mains by geometry and ground, not by road class.
- The SHP layer is kept only to draw where the dual carriageways are (`dual = 1`) as context.

Decided 2026-09-07, from the checks made before adoption: **trust the DXF as drawn.** The 290 km
of SHP roads with no DXF line (67 km of it beside built or planned plots) are not added. The
1.7 km of DXF line running 3 to 8 m from a dual carriageway is service road.

## Scope at this stage (2026-09-07)

Street sewers only. The tertiary layer, property connections and riders, is left out to keep the
engine fast. Consequence to remember: no house-level connectability check, so where a house sits
below its road the chamber that would have been deepened for it is not. Add the tertiary back when
the street network is settled.

## Stage A result on the built area (2026-09-07)

`python W13/py/run_stage_a.py`, 41 seconds. Drawing `W13/dxf/W13_A_ground.dxf`; shapefiles
`W13/shp/W13_A_*`; pictures `W13/img/W13_A_*.png`; numbers `W13/run/stage_a.json`.

| | |
|---|---|
| Area | 9.09 km², the 60 m envelope of the 111.6 km built in 2006, holes filled |
| Streets | 146.0 km of DXF street, 1,980 runs junction to junction, 82 split at a crest (41) or sag (41) |
| Raw ground | 100 km falls steeper than 0.5 %, 36 km flatter, 10 km level within 0.1 m |
| Targets | 114 junctions within 30 m of the main pipe, 1 at the STP |
| After filling hollows to 2 m | 187 catchments: **96 JOIN (84 km)**, 1 STP, **65 SINK (57 km, spill 2.4 to 10.3 m)**, 25 LOW islands (5 km, 23 of them under 0.5 km) |
| Against the ground | 11.4 km of run flows over the rim of a filled hollow |
| Largest | C01 JOIN 22 km and C02 JOIN 20 km (east, south and centre); C03 SINK 9.6 km, spill 3.0 m (east, north); the west settlement is SINKs of 2.4 to 6.6 m spill falling south-west, away from the main pipe, toward where NAMA built its own trunk |

**What a SINK means, checked against NAMA (2026-09-07).** A SINK is not "no gravity"; its spill
is the extra depth a pipe needs to leave it by gravity. 55 of the 65 sink basins have built
sewer inside them, and NAMA left them by gravity at depths in line with the spill plus cover:
C03 spill 3.0 m, NAMA max depth 5.4 m; C04 spill 4.5 m, NAMA 7.0 m; C05 2.4 m, NAMA 6.1 m; C12
5.3 m, NAMA 6.9 m. In the west settlement the spill is measured toward the main pipe, uphill,
while NAMA's route to the STP is cross-country and not a DXF street, so those spills overstate
the cost; the direct link of rule 3 corrects it. **Terrain check:** the 2 m terrain minus NAMA's
surveyed ground at 2,144 manholes is +0.14 m median, 0.34 m median absolute deviation, 1.01 m
RMSE, 90 % within −0.9 to +1.3 m. Good enough for the fall of a sloping street; on a flat street
the noise is the size of the fall, which is why direction there is a design choice (rule 5).

**Stage A rerun, agreed 2026-09-07.** The drawing is rebuilt as a tree, not as the raw ground:

1. **The outlet of a junction is chosen by rule, in this order:** the run that belongs to the
   sub-main; else the run on the cheapest route to the sub-main or the join, where cheap means
   short and least trench depth (W8's search with its depth cost: a flat street charged for the
   depth it forces on a pipe at the minimum gradient); the steepest fall only as the tie-break.
   W8's structure resolver stays as it is: chambers within 3 m are one structure, the tree is
   re-derived so a structure has one physical outlet, and every leftover branch starts at the
   next house gate along its own street or 10 m away. W8's join cap is replaced by the sub-main.
2. **Sub-mains are picked in Stage A**, because the tree needs them: the long, straight, low
   street of each catchment, from the ground and the street geometry, made the spine to its join.
   Laterals then search their cheapest route to the sub-main, not to the main pipe.
3. **Catchments follow the tree:** what drains through one sub-main to one join, not what
   steepest descent says. This ends the mixed colours in the south-east.
4. **Sinks relabelled** as "leaves by gravity at about X m", and the west settlement's cost
   measured toward the STP as well as toward the main pipe.

Two things the picture says for Stage B. The west settlement's outlet is its south-west corner
and its spine is to the STP, not to the main pipe. And the ground gives 96 joins on the main pipe
where W8 used 20 and NAMA's built network has about 16; 71 of the 96 carry under 0.5 km, so rule
4 will have to say whether a street that merely touches the main pipe gets its own join.

## Outputs to check the work (agreed 2026-09-07)

A DXF, and the same content as a KMZ for Google Earth. The drawing is the check, so it shows the
reasoning, not only the result.

- **One layer per element class**, each switchable: main pipe, sub-main, lateral, force main,
  chambers, pumps, joins (sub-network connection points to the main pipe), catchments, streets,
  streams.
- **Pipes coloured by sub-network**, from a dozen strong colours assigned so no two neighbouring
  catchments share one. **Thickness grows with diameter** as polyline width, not lineweight, so
  it scales with zoom and shows without switching lineweight display on.
- **A flow arrow on every pipe.** Every arrow must point downhill to its outlet.
- **Chambers shaded by depth in fixed bands**, light to dark: 0–2, 2–4, 4–6, 6–8, 8–10, 10–12 m,
  and anything past 12 m in red. Fixed bands, never a stretched ramp, so two runs compare. A depth
  label on every chamber over 8 m.
- **The ground behind it**: thin grey street centrelines, excluded dual carriageways dashed,
  terrain streams in blue thickening with Strahler order, catchment boundaries as dashed outlines
  with the outlet marked.
- **A stats text at each outlet**: sub-network ID, length, chambers, deepest, pump or not.
