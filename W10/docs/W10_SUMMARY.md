# W10 — the first full-area design, 2026-09-01

The whole 531.4 km² laid out as a greenfield gravity network, as if the existing system were
not there. W11 is the brownfield run that includes it.

> ## STATUS: NOT COMPLIANT - do not issue
>
> Audited against W8's own check registry on 2026-09-01, after publication, this design
> fails on four counts. They are recorded rather than patched, because patching one at a
> time is what produced them. **W11a builds the auditor first and this table is its brief.**
>
> | Failure | Extent | Rule |
> |---|---|---|
> | Trunk **surcharged** - DN1200 at 1,361 L/s and 0.075 % passes the flow at no depth | 5 reaches, **2.80 km** | G203-p27 Tab 10 |
> | Over the d/D limit but passing | 66 reaches, 10.68 km | G203-p27 Tab 10 |
> | Below the **1.30 m minimum cover** to crown, worst 0.30 m | 169 reaches, **45.92 km** | G203-p33 4.6.3 |
> | Pipe running **along a dual carriageway**, plus 47 unscheduled crossings | 21 reaches, 1.67 km | project rule 7 |
>
> In one line: **W8's engineering was carried into W10 and W8's auditor was not.** The
> surcharged trunk is mine - I corrected an over-steep gradient without re-checking
> capacity. The cover failure comes from a hardcoded 0.30 m outside diameter standing in
> for the real one. Also 1,233 m3/d (1.7 %) of load never enters the network, and every
> analysis output except the pipe layer predates the wadi fix, so the optimisation study's
> baseline is 219 breaches where the shipped design has 239.

## The design

| | |
|---|---|
| Corridor network | **2,279 km**, 99.8 % of it one connected graph |
| Pipe laid | **1,883.6 km** in 20,936 reaches |
| Plots served | **60,085 of 61,272 (98.1 %)** |
| Flow arriving at the works | **73,442 m³/d** + 1,356 m³/d infiltration |
| Subnetworks | **206**, defined as everything reaching the trunk at one point |
| Lifting stations | **19** (was 11, then 21; see `OPTIMISATION.md` for both corrections) |
| Deepest chamber | **11.99 m** against a 12.00 m limit |
| Median cover | 2.07 m |

Diameters: DN200 1,689 km (90 %), DN250–400 86 km, DN500–800 69 km, DN900–1200 39 km. The
median required gradient is 0.500 % because DN200 governs nearly everywhere and that is its
Table 11 minimum.

Figure: `W10/img/W10_design.png`.

## What you asked, answered

**1. Define the subnetworks.** 206, found by routing rather than by drawing polygons —
corridors and trunk as one graph, every edge charged for the height it gains in the
direction of flow, one Dijkstra from the works settling every node. The largest is 266 km
and 6,331 plots.

**2. Is the proposed main pipe workable?** **Yes, entirely by gravity.** Across all three
components the deepest point is **10.80 m** at DN1000 and 0.10 %, and on the 73.19 km main
body it is **7.72 m**; median cover 2.5 m, and nothing reaches 12 m at any of nine
diameter-and-gradient combinations. The 10.80 m is on the small eastern component, which is
the drafting break — snapped into the main body it is levelled with it. The worst single rise above the running low point is 4.5 m over 73 km. The
54-piece drawing is three components: the main body, the western leg, and a 2 m drafting
break in the east that closes with a snap. Detail: `MAIN_PIPE_AUDIT.md`.

**3. Where are the lifting stations?** **19.** 219 depth breaches at the real gradients, 33
after consolidating within 1.5 km (rule 9), 19 once the 50-property threshold is applied to
the catchment that actually drains through each one. *(An earlier figure of 11 was wrong -
it double-filtered, applying a proximity test and then a catchment test to the survivors.
See `OPTIMISATION.md`.)* Ten strategies were tested to reduce this and none beat it. Total duty through
all stations is 199 L/s against a network peak near 1,700 — about an eighth of the flow is
pumped. Detail: `PUMPING_AND_DEPTH.md`.

**4. Do the far southern plots need huge lifts, and does moving the STP help?**
The southern plots do need a lift to the existing works — the lowest sits at 311.6 m, which
is 17.1 m **below** it. Your southern site turns that into a fall. Across the whole network,
though, moving the works is worth 6 %, not a transformation: 207 depth breaches and 2,688 m
of lift against 220 and 2,846 m. See the siting section below, where the answer gets more
interesting.

**5. Can the west be connected?** **No, not by gravity, and the works location cannot
change that.** From its low point at 332.91 m every route out crosses the **same** high
point — 344.83 m at chainage 6.24 km, 11.93 m above the start — whether the destination is
the existing works, your southern site, or the nearest point on the main trunk. One saddle,
not three obstacles. So the west is pumped (about 14 m of lift and a 6 km rising main) or it
gets its own works: 403 km of corridor and 11,254 plots sit within 6 km of that low point,
which is a real plant. Detail: `WEST_LEG.md`.

**6. Best routes for the force mains.** In the design as solved the stations lift and
restart the gravity pipe on the spot, so rising mains are metres, not kilometres, at DN100
to DN200 on pump duty at 0.75–3.0 m/s. The alternative — every station pumping to the trunk
— is priced for comparison at 121.9 km and is not recommended. `W10/run/p6_rising_mains.csv`.

**7. Where can the STP go?** A weighted seven-criterion surface over the whole boundary,
with the hard exclusions of G201-p43 Table 8 and G203-p63–64 Tables 27–28 applied: 35 % of
the area passes all four. Ten candidates, of which **S1 at 443075 E 2566675 N ranks first
under all five weightings tested** — 40 ha free, 1,036 m to the nearest built plot, 1.5 km
to the trunk, ground 327.3 m. Detail and citations: `STP_SITING.md`.

**8. The full network ignoring the existing system.** This document.

**9. Include the existing system.** W11.

## The siting study and the depth solver disagree, and it matters

The siting study ranks S1 first and your southern site eleventh. Re-solving the whole
network's depths with each candidate as the outlet ranks them the other way round:

| Outlet | Depth breaches | Total lift | Flow arriving |
|---|---|---|---|
| **Your southern site** | **207** | **2,688 m** | 73,442 m³/d |
| S2 | 211 | 2,742 m | 73,442 |
| S4 | 212 | 2,744 m | 73,442 |
| Existing works | 220 | 2,846 m | 73,442 |
| S1 (siting study's first) | 231 | 2,987 m | 73,442 |
| S3 | 237 | 3,049 m | 73,442 |
| S6 | 252 | 3,247 m | 73,442 |

Every candidate receives the whole flow, so this is not about reachability. The
disagreement is real and its cause is known: the siting study's gravity criterion is a
straight-line screen — it says so itself — and **cannot see the 12 m cover limit at
intermediate chambers**. It rewards a site the load can reach on a straight gradient; the
depth solver counts what that actually costs in stations.

Neither is wrong. They measure different things:

- **S1 wins on land, separation from dwellings, conveyance distance and road access.**
- **Your southern site wins on hydraulics** — fewest stations, least lift — and scores 1.000
  on dwelling separation, land and flood, joint-best on gravity. It loses the ranking on
  conveyance (17.2 km load-weighted against S1's 12.5) and road access (9.05 km to the
  nearest dual carriageway, the furthest of the twelve).

**The existing works ranks twelfth, and the reason is land**: 20.6 ha free against a 30 ha
target for 54,700 m³/d. Independently checked — within a 400 m radius, 22.1 ha of the 50.3
sits on registered plots against zero at both S1 and the southern site. It is the right
place hydraulically and the wrong place for a plant of this size.

**This is not a recommendation.** It is two defensible rankings that disagree by 6 % on
pumping and by four places on the siting score, and the thing that would settle it —
life-cycle cost over 25 years at 5 %, with the conveyance, the pumping energy and the land
all priced — is Phase 4.4 and is not done. What can be said now is that **the existing works
site does not survive the land test**, and that the choice is between the southern area and
the S1/S2 group north-west of the town.

## What is not settled

| | |
|---|---|
| Loads | The GIS expert's clean land-use data replaces the placeholder. The saturation total, **74,675 m³/d**, rests on 1.456 properties per plot measured on *built* plots and applied to planned ones. At 1.0 it is 54,602 |
| Station siting | The 11 are at hydraulic positions, not land parcels |
| Cascading | 122 of the raw breaches sit within 1.5 km of another. Identified, not designed |
| The 1,187 unserved plots | Mostly pockets of under 6 plots — detail design |
| 391.5 km of corridor with no pipe | Loop-closing alternatives the solver did not take. Kept, not lost |
| Chamber-level design | This is a network solve on ~100 m nodes, not a chamber schedule |
| Land ownership everywhere | `OWNER_NAME` is populated on 1,704 of 61,272 plots |

## Three corrections to the record made during this run

1. **The saturation load is 74,675 m³/d, not the 49,700 carried since W2.** The ratio
   decomposes exactly: 1.291 × 1.207 = 1.558.
2. **The built network does carry diameters and inverts** — 2,142 of 3,267 pipes, 66 %,
   packages 5A-2/3/4/5 complete. The "none recorded" claim read `N_DIAMETER`, which is
   always 0, instead of `OUT_DIAMET`. **Report R1 §18 needs revising in R2.**
3. **NAMA supplied ESRI shapefiles beside the KMZ.** The KMZ conversion loses 74 of 129
   proposed gravity features.

Plus: the existing works is at 444422.8 E 2563337.9 N, 38 m from the coordinate previously
carried.

## Where everything is

Scripts `W10/py/` run in order: `p0_dxf` → `p0_auto` → `p0_topology` → `p0_mainpipe` →
`p05_existing` → `p1_loads` → `p1_subnetworks` → `p2_depths` → `p2_sizing` → `p4_stp_siting`
→ `p5_west` → `p6_force`. Shared machinery in `netlib.py` and `skeleton.py`.
Documents in `W10/docs/`, figures in `W10/img/`, layers in `W10/shp/`, run records in
`W10/run/`.
