# W13 design logic

Agreed 2026-09-07 between the engineer and Claude. This is the reasoning the engine is built
against. Change it by adding a dated line under the rule, never by rewriting the rule, so the
history of why a rule moved stays readable.

**Rules only.** Every measurement that supports a rule, every as-built check and every run
result lives in `W13_EVIDENCE.md`, not here (engineer, 2026-09-07).

The aim: a hydraulic design engine that runs the whole area in a few minutes, so different ways
of designing can be tried and compared.

## The logic

1. **Sewage runs downhill.** Read the ground along the streets: sample the terrain on every
   centreline, take the fall junction to junction, point each street downhill. Derive the terrain
   streams and their Strahler order as the guide: high-order streams mark the valley streets and
   group the catchments; the hazard grid marks the wadis.
2. **Follow the arrows** from every junction until they stop. Where they stop is an outlet:
   either where the falling streets meet the main pipe, or a sink where every street rises away.
   Each outlet is one catchment.
   - 2026-09-07, Stage A method. Hollows are filled on the street graph by priority flood from
     the targets. A dip needing **2 m** or less of fill is crossed by the pipe unremarked. A
     junction within **30 m** of the drawn main pipe is a join candidate. Inside a filled hollow
     the flow runs against the ground: those runs are classed AGAINST and drawn dash-dot.
   - 2026-09-07 (engineer): **a basin is not an outlet. A sub-network is what connects to the
     main pipe or the STP, never a local sink.** A basin deeper than 2 m is first offered a direct
     link (rule 3); failing that it drains over its lowest rim into the neighbouring sub-network,
     and the extra depth the pipe carries to leave it is marked on the drawing at the basin. Only
     a basin that would need more than **10 m** stays a pocket, for a pump or a cut under rule
     10, because with cover it would pass the 12 m limit. A part of the graph with no street path
     to any target is an island: its lowest node is a **LOW** outlet, to be linked or reported.
3. **From each outlet, the gravity path to the main pipe is the spine.** One join per catchment.
   The ground sets the number of joins, not a cap.
   - 2026-09-07: where the streets give the outlet no proper way to the main pipe, connect the
     outlet to the main pipe directly, across open ground, provided no plot lies in the way. The
     link may cross a dual carriageway only at an underpass (the roads in the DXF that pass
     under one are the underpasses). An outlet that could reach the main pipe only across a dual
     carriageway with no underpass is reported as a pocket.
   - 2026-09-07: a settlement whose ground falls away from the main pipe is measured toward the
     STP as well, and its spine goes to whichever it reaches by gravity.
   - 2026-09-07, Stage A method for the direct link. A basin or island low point becomes a
     LINK outlet when its ground falls to the target at **0.2 %** over the straight distance
     (the DN400 minimum, a link is a large pipe), the link is no longer than **4 km** (NAMA's
     own trunk from the west settlement to the STP), and the straight line crosses **no built
     or planned plot**; agricultural plots crossed are counted and reported. The main pipe is
     measured at its invert, taken as **3 m** below the ground at the foot of the link, a stated
     allowance until Stage C lays it. A basin that fails the straight-line test is not refused
     a link; it waits for Stage B to route one through the streets, and its label carries the
     fall and distance to both targets. A link is a join for the spacing rule: it keeps the
     join spacing from every existing join or link, unless its source is an island with no
     street path to anything.
   - 2026-09-07 (engineer): **a direct link is for a sub-network very close to the main pipe
     with no road between.** A link to the main pipe is at most **150 m** long and its line
     crosses no street of the network; where a street lies between, the water goes by the
     streets into the neighbouring sub-network, at the extra depth of rule 2.
   - 2026-09-07: **NAMA's built trunk corridor to the STP is a second target.** The corridor is
     the built trunk mains, a right-of-way with no plot in it. A street junction within 150 m
     of it, with no street and no built or planned plot between them, whose ground falls to the
     STP at **0.125 %** (the DN600 minimum, a trunk from a settlement of this size) along the
     corridor within **6.5 km** (NAMA's own western trunk runs 5.65 km along it), is an entry
     join, kept lowest first and spaced like joins on the main pipe. A corridor point under the
     drawn main pipe is not an entry; that is the main pipe's job. The settlement then reaches
     the entry by its own streets. Links are offered to basins before any basin is filled
     toward the main pipe: gravity with no extra depth beats climbing out.
4. **Sub-mains first.** Long, straight, few bends. Low is the filter, long and straight is the
   choice. They earn their diameter from the houses they collect, and a bigger pipe reaches
   further on flat ground: about 2 km at DN200, 4 km at DN315, 5 km at DN400 before 12 m.
   - 2026-09-07: sub-mains are picked in Stage A, because the tree needs them: the long,
     straight, low street of each catchment, from the ground and the street geometry, made the
     spine to its join.
   - 2026-09-07, Stage A method. The sub-main is read off the flood tree as the heaviest stem:
     from the outlet, step to the child carrying the most street upstream, preferring the
     straighter continuation where two children are within a quarter of each other, and stop
     where less than **600 m** of street lies upstream. A side child carrying **1,500 m** or more
     of its own is a sub-main too. Everything else is a lateral.
5. **Then hang the rest off them.** Every street drains to the sub-main below it, every house to
   the street it fronts. On flat ground, the shortest run to the nearest sub-main.
   - 2026-09-07 (engineer): **one outlet per junction, and no loops.** Which pipe leaves a
     junction is a design decision under the criteria and these rules: the run that belongs to
     the sub-main; else the run on the cheapest route to the sub-main or the join, where cheap
     means short and least trench depth; the steepest fall only as the tie-break. Every other
     street on that junction starts as a head at the first house gate, the first plot's centroid
     dropped square onto the street, or 10 m along where no plot faces it. Checked against the
     as-built: it holds.
   - 2026-09-07 (engineer): **a street that touches the main pipe does not join it; only
     sub-mains join.** A street beside the main pipe runs into the nearest sub-main. Every join
     is drawn as a connector from the street to the main pipe, on its own layer. Checked against
     the as-built: it holds.
   - 2026-09-07: **catchments follow the tree**, what drains through one sub-main to one join,
     not what steepest descent says.
   - 2026-09-07, Stage A method. Joins are kept biggest first and any candidate within **150 m**
     of a kept one is dropped into its neighbour; a dropped join whose streets have no path to
     any other outlet gets its join back. Laterals search their route to the nearest sub-main
     with W8's cost: length, plus **500 m of equivalent length per metre** of trench depth a
     street forces on a pipe at the **0.5 %** minimum. A leftover street drains to its lower end,
     or to the end nearer a sub-main where the ends are level; its head is set back to the first
     plot centroid within **45 m** of the street dropped square onto it, or **10 m** where no plot
     faces it; a street under **15 m** cannot carry a head and is reported.
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
     successive manholes". Checked against the as-built: it is NAMA's practice.
9. **Lay each catchment from its heads by rule 7.** That is the shallowest the route can ever be.
   Under 12 m at the main pipe: gravity, done.
10. **Over 12 m: reroute first.** A different join, a street where the ground helps, or the
    neighbouring catchment, street by street, for whatever can reach it within 12 m. Then cut
    where the pipe passes 12 m: a pump at the cut into the nearest gravity chamber, and the pipe
    restarts at cover. Never dig past 12 m to avoid a pump. Never pump to avoid a reroute. Until
    we cost, gravity within 12 m beats a pump.
11. **A closed hollow, or a ridge between a pocket and every neighbour, is a real pump.**
12. **Chambers** (2026-09-07, from W8). A chamber sits at every junction, every head, and every
    change of gradient or diameter. **Spacing follows the guideline**, G203-p30 Table 12 by
    diameter (engineer, 2026-09-07), and the chambers on a run are placed the way a setting-out
    engineer would: the fewest chambers that satisfy the spacing, spaced evenly, rounded to 10 m
    (5 m where 10 leaves an awkward remainder), the odd metres on the reach with the most room.
    A 230 m run gives 80, 80, 70, not 100, 100, 30. At a bend: up to 5°, none; 5° to 45°, one
    chamber at the bend; a sweeping curve over 45°, two or three on chords, never more than
    three; a corner chamber sits at the tangent intersection only if it is 2 m clear of every
    plot, otherwise the curve is followed. Two chambers closer than 3 m are one structure. Every
    chamber is checked against every plot and slid clear.

## What the engine does with each rule (proposed mapping, to be confirmed as it is built)

| Rule | Engine step | What it produces |
|---|---|---|
| 1 | read the ground | streets with fall, direction, nearest stream order; wadi flag |
| 2 | find outlets | every junction labelled with its outlet; outlets typed join / STP / sink / low |
| 3 | spines | one route per outlet to the main pipe or the STP |
| 4 | sub-mains | the low, long, straight streets of each catchment, `TIER = sub main` |
| 5 | tree and branches | one outlet per junction, heads at gates, streets to the sub-main, `TIER = lateral` |
| 6 | ridges | catchment boundaries at crests; long ridge streets split at the crest |
| 7, 8 | gradients | three bands, stepped, one gradient per run until cover; drops capped at 2 m |
| 9 | depth check | heads-down lay; depth at every chamber and along every trench |
| 10 | reroute, then cut | pumps only where a reroute could not remove them |
| 11 | real pumps | hollows and enclosed pockets, listed with the reason |
| 12 | chambers | guideline spacing, evenly divided and rounded; bend and clearance rules |

## Inputs (2026-09-07)

**Road network: `Hydraulic/DWG/road network 03092026 eyeballed.dxf`** (draftsman, 3 September
2026; UTM 40N metres). It replaces `SHP/Road centerline 2` as the corridor source. Layer
`piping center line` is the existing roads; `piping center line-propo-01` is the streets added
where roads were missing, mostly through planned plots. Dual carriageways are already left out,
every intersection is a node, and the lines sit in the road reserve.

How the engine treats it:

- **Trust the DXF as drawn** (engineer, 2026-09-07). Roads in the SHP that are absent from it
  are not added. Lines running close beside a dual carriageway are service roads.
- **Snap** line ends within 3 m.
- **No crossings of dual carriageways are generated** (engineer, 2026-09-07). The drawing is the
  network as it may be used; the crossings the draftsman drew are the only ones.
- **Islands are reported, never dropped silently.** Each reaches a target by its streets, or by
  the direct link of rule 3, or is reported as a pocket.
- **No attributes** come with it, and none are needed: exclusion is already done, and rule 4
  picks sub-mains by geometry and ground, not by road class.
- The SHP layer is kept only to draw where the dual carriageways are (`dual = 1`) as context.

**Terrain:** the 0.5 m blend, read once over the area at a 2 m cell for the ground pass.
**Targets:** the main pipe as drawn (`SHP/Main Pipe`) and the existing STP.
**The built network** (`W7/shp/EXISTING_SEWERLINE.shp`, `OP_STATUE = 1`) defines the area of
this stage and is the comparison for every rule.

## Scope at this stage (2026-09-07)

**The area:** the ground the 2006 network serves, every street within 60 m of a built lateral
or sub main, holes filled (engineer, 2026-09-07), so the new design can be compared with what
NAMA built. The part of a trunk main that lies inside a settlement stays, clipped to it, because
its street carries the joins; the trunk corridor between the settlements and to the STP is out,
since a street crossing that corridor is not served by this network (engineer, 2026-09-07).
Targets are the main pipe and the STP; each sub-network drains to whichever it reaches by
gravity.

**Street sewers only.** The tertiary layer, property connections and riders, is left out to keep
the engine fast. Consequence to remember: no house-level connectability check, so where a house
sits below its road the chamber that would have been deepened for it is not. Add the tertiary
back when the street network is settled.

## Outputs to check the work (agreed 2026-09-07)

A DXF, and the same content as a KMZ for Google Earth. The drawing is the check, so it shows the
reasoning, not only the result.

- **One layer per element class**, each switchable: main pipe, sub-main, lateral, force main,
  chambers, pumps, joins (sub-network connection points to the main pipe, drawn as connectors),
  catchments, streets, streams.
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
- **Sinks labelled** as "leaves by gravity at about X m", never as a verdict.

Stage A draws rules 1 and 2 only: runs with arrows, colour by catchment, dashed where flatter
than 0.5 %, dash-dot where against the ground, the gradient written on every run long enough to
carry it, outlets typed, the built network in grey behind.
