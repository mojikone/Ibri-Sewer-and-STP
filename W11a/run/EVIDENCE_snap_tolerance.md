# Why W10's "310 loops" was never a design defect

Measured 2026-09-02 on `W10/shp/W10_pipes.shp` (20,936 pipes), by clustering pipe endpoints
at a range of tolerances and counting components and independent cycles (`E - N + C`).

| snap (m) | nodes | components | cycles |
|---|---|---|---|
| 0.01 | 28,855 | 7,919 | 0 |
| 0.10 | 28,833 | 7,897 | 0 |
| 0.25 | 28,815 | 7,879 | 0 |
| 0.50 | 28,792 | 7,856 | 0 |
| **1.00** | 25,519 | **4,601** | **18** |
| 2.50 | 20,730 | 105 | 311 |

## What it means

**The loops are manufactured by the measurement.** At any tolerance a surveyor or a GIS would
accept, the layer has **zero** cycles — because it has 7,919 disconnected pieces, and a pile of
disconnected pieces is loop-free by accident. Snap at 2.5 m and the pieces fuse into 105, and
311 cycles appear. Same layer, different squeeze.

**The step at exactly 1.00 m is the `p0_auto.stitch` bug.** That function joined corridor
islands with `buffer(1.0)`, so 91.4 % of stitch links stop 1.000 m short of what they join
(verified separately on 4,558 endpoints). Below 1.00 m those gaps stay open; at 1.00 m they
close, 3,255 components disappear at one step, and the first cycles appear with them.

## Consequences

1. **Retract the "310 loops" figure** wherever it is quoted as a W10 design defect. It is a
   defect of the *published layer's connectivity*, reported through a 2.5 m snap. The honest
   statement is: *the layer was never connected, and how many loops it appears to have depends
   entirely on how hard you snap it.*
2. **One root cause, not two.** Disconnection and loops are the same bug. `G3` names it: the
   layer publishes no `US_NODE`/`DS_NODE`, so connectivity can only be inferred by a tolerance.
   W11a carries explicit node IDs and this whole class of question disappears.
3. **Never infer topology from geometry in a deliverable.** A tolerance is a guess about intent.
   The design knows which chamber a pipe runs between; it must write it down.
