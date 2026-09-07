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
     the targets up to a spill of **2 m**: a dip that shallow is crossed by the pipe with a
     little depth and is not an outlet. A sink needing more stays a **SINK** outlet; its spill is
     the extra depth a pipe needs to leave it by gravity, a cost for Stage B, never a verdict of
     "no gravity". A part of the graph with no street path to any target is an island: its
     lowest node is a **LOW** outlet and the island is flooded from there. A junction within
     **30 m** of the drawn main pipe is a join candidate. Inside a filled hollow the flow runs
     against the ground: those runs are classed AGAINST and drawn dash-dot.
3. **From each outlet, the gravity path to the main pipe is the spine.** One join per catchment.
   The ground sets the number of joins, not a cap.
   - 2026-09-07: where the streets give the outlet no proper way to the main pipe, connect the
     outlet to the main pipe directly, across open ground, provided no plot lies in the way. The
     link may cross a dual carriageway only at an underpass (the roads in the DXF that pass
     under one are the underpasses). An outlet that could reach the main pipe only across a dual
     carriageway with no underpass is reported as a pocket.
   - 2026-09-07: a settlement whose ground falls away from the main pipe is measured toward the
     STP as well, and its spine goes to whichever it reaches by gravity.
4. **Sub-mains first.** Long, straight, few bends. Low is the filter, long and straight is the
   choice. They earn their diameter from the houses they collect, and a bigger pipe reaches
   further on flat ground: about 2 km at DN200, 4 km at DN315, 5 km at DN400 before 12 m.
   - 2026-09-07: sub-mains are picked in Stage A, because the tree needs them: the long,
     straight, low street of each catchment, from the ground and the street geometry, made the
     spine to its join.
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

**The area:** the ground the 2006 network serves, every street within 60 m of a built sewer,
holes filled (engineer, 2026-09-07), so the new design can be compared with what NAMA built.
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
