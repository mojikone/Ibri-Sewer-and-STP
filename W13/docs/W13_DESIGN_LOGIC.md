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
3. **From each outlet, the gravity path to the main pipe is the spine.** One join per catchment.
   The ground sets the number of joins, not a cap.
   - 2026-09-07: where the streets give the outlet no proper way to the main pipe, connect the
     outlet to the main pipe directly, across open ground, provided no plot lies in the way. An
     outlet that could reach the main pipe only across a dual carriageway is not linked; it is
     reported as a pocket for the engineer to decide.
4. **Sub-mains first.** Long, straight, few bends. Low is the filter, long and straight is the
   choice. They earn their diameter from the houses they collect, and a bigger pipe reaches
   further on flat ground: about 2 km at DN200, 4 km at DN315, 5 km at DN400 before 12 m.
5. **Then hang the rest off them.** Every street drains to the sub-main below it, every house to
   the street it fronts. On flat ground, the shortest run to the nearest sub-main.
6. **A ridge is a boundary, not a place to build.** A street on a ridge drains whole into the
   lower side. A very long ridge street splits at the crest, two heads back to back.
7. **Gradient follows the ground in three bands.** Flatter than the minimum: lay at the minimum.
   Between the minimum and the velocity limit: parallel to the ground at cover. Steeper than
   3 m/s at peak flow: hold the gradient and take the rest as drops, 2 m per chamber at most,
   closer chambers if needed.
8. **Gradients are laid in steps of a tenth of that pipe's minimum gradient:** 0.5 mm/m at
   DN200, finer for bigger pipes. The diameter is earned by the flow, never chosen to flatten.
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
