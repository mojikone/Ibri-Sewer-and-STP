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

## The gate

No change ships until the engine still gives 71.6 km, about 1,415 chambers and zero pumping
stations on the 5.51 km² test area (`W13/py/run_test_boundary.py`, 26 seconds). Then the full
area, in minutes, not hours.
