# W8 and W10 post-mortem — what generalises, what broke, and the audit contract for W11a

**The uncomfortable finding first: W8's registry of 22 checks, run against W10's own output layer, fails on five counts that nobody has reported — including 2.80 km of surcharged trunk at the works and 34.2 km of pipe laid with less than the guideline minimum cover. W10 did not fail because its engineering was worse than W8's. It failed because W8's engineering was carried across and its *auditor* was not.**

Written 2026-09-01. Every number below was recomputed from the output files named against it, not taken from a document. Where a document and its own run record disagree, both are quoted.

---

## 0. What was verified mechanically, and how

| Claim source | How it was checked here |
|---|---|
| `W10/shp/W10_pipes.shp` (20,936 reaches, 1,882.9 km) | re-read; every reach re-tested against `sewnet.hydra` and `sewnet.criteria` |
| `W10/shp/W10_lift_sized.shp` | 239 breaches counted directly |
| `W10/shp/W10_road_treatment.shp` | 7,890 features grouped by `EXCL_RSN`; the removed roundabout arcs re-polygonized and tested against `MoH_Plots` |
| `Data/04 Lekhuwair/Hazard_T50y.tif` | full array read — 709,183,851 valid cells |
| `SHP/Road centerline 2` `dual=1` | 289 lines, 146.9 km; buffered at 4 / 6 / 12 m and intersected with both designs |
| `W8/run/summary.json`, `W8/run/audit_table.txt` | read as the W8 record |
| file mtimes across `W10/run/` and `W10/shp/` | used to establish which outputs predate the wadi fix |

Nothing in this document is a re-quotation of a W10 headline figure without that check.

---

# PART A — which W8 choices generalise

## A.0 The scale change, stated properly

| | W8 | W10 | ratio |
|---|---|---|---|
| Area | 5.51 km² (measured from `W8_boundary.shp`) | 531.4 km² | 96× |
| Corridor treated | 97.4 km of raw road in | 2,211.8 km of corridor out | — |
| Pipe laid | 71.64 km, 1,414 reaches | 1,882.9 km, 20,936 reaches | 26× |
| Design unit | chamber (median reach ~50 m) | corridor node (~100 m, longest reach 6,541 m) | — |
| Trunk | 6.15 km, given | 92.3 km in the merged graph, 85.49 km given in 54 features | 15× |
| Pumping | 0 stations | 239 breaches → 19 stations | — |
| Audit | 22 checks, 3 failing, printed every run | **none** | — |

The last row is the whole post-mortem. W10 imports `sewnet.criteria` and `sewnet.hydra` and re-implements everything else — including the parts of `sewnet.stages` that existed to catch mistakes.

## A.1 The join cap — the rule is sound, the two "joins" are different objects

**Verdict: does NOT generalise as written, and the headline comparison is misleading.** [Certain] on the arithmetic, [Likely] on the cause.

The comparison as usually stated — W8 capped at 20, W10 found 206–214 and the cap bought nothing — compares two quantities that are not the same measurement.

| | W8 | W10 |
|---|---|---|
| What a "join" is | a connector chamber built at right angles from a street onto a manhole on the drawn trunk (`trunk.attach_to_roads`) | a graph node whose flow path first steps onto an edge tagged `trunk=1` (`p1_subnetworks.trace_joins`) |
| Candidate set | 55 streets that meet the trunk **square-on within 60 m** (`square_deg=45`, `max_conn_m=60`) | every node in the network |
| The cap | a hard `keep_k` on those 55, ranked by nearest-unit load | a **routing cost** (`join_penalty`) added to any edge entering a trunk node |
| Result | 20 kept of 55 | 214 at zero charge, 205 at 4,000 m/join, +30 % route length |

Normalise by trunk length and the picture inverts:

| | Things touching the trunk | Trunk length | Per km |
|---|---|---|---|
| NAMA as-built (test area) | ~16 | 4.02 km | **4.0** |
| **W8, capped at 20** | 20 | 6.15 km | **3.3** |
| **W10, uncapped** | 214 | 92.3 km | **2.3** |

So W10's uncapped design is already *sparser* on the trunk than the as-built, and W8's capped design is denser than W10's. "20 versus 206" is a length effect, not a discipline effect.

The structural reason W10's sweep flattens is stated correctly in `p1_subnetworks.py` and I agree with it: the drawn main pipe is a **spine running through the settlements**, not a collector at the edge of town. Merging trunk and corridors into one graph (`netlib.load_network`, `TRUNK_TOL_M = 3.0`) then makes "touching the trunk" a property of geometry rather than a design decision — a street that happens to run within 3 m of the alignment *is* the trunk, and charging it to join itself is meaningless.

**What to carry to W11a:** keep the join *concept* — it is the as-built's own decomposition — but define it the way W8 did, as a **built connector onto a trunk manhole**, and keep the trunk as a separate corridor from the streets that feed it. The W8 rule is not wrong; W10 dissolved the object the rule acts on. Charge per join, and report joins per kilometre of trunk against the as-built's 4.0, never joins in total.

## A.2 "ZERO pumping stations" — a special case, but a narrower one than expected

**Verdict: nearly holds inside its own footprint; does not survive the ground outside it.** [Likely] — there are three confounds, named below.

Direct test: how many of W10's 239 depth breaches fall inside the W8 test boundary?

| | |
|---|---|
| W10 pipe inside the 5.51 km² W8 boundary | **75.8 km in 1,186 reaches** |
| W10 depth breaches inside it | **3** |
| Total lift on those three | **32.6 m** |
| W8's own answer on the same ground | 0 breaches, deepest chamber 10.45 m |

So the flat town core really is flat: 3 breaches on 75.8 km, against 236 on the other 1,807 km. W8's zero is close to right and its trunk-alignment argument (`W7/docs/CALIBRATION_vs_EXISTING.md` §3 — "W7 gets shallow trenches for free from a better trunk") is confirmed rather than refuted.

Confounds that keep this at [Likely]: W10 uses different corridors on that ground (draftsman's DXF plus skeleton, not treated road centrelines), 100 m nodes instead of ~50 m chambers, a fixed 0.30 m outside diameter, and no reroute passes.

**What else in W8 is a special case of a flat town core, and should be re-earned rather than inherited:**

| W8 result | Why the test area produced it | Full-area evidence |
|---|---|---|
| Deepest chamber 10.45 m against a 12 m limit | the outfall sits at the meeting point of both trunk legs, 792 m outside the boundary and already low | W10 breaches by class: 62 adverse ground, 79 local ridge — terrain shapes absent from the core (`BREACH_DIAGNOSIS` §2) |
| Median required gradient irrelevant | DN200 at 0.500 % over ≤2 km never eats the allowance | at full scale 1,696 km of DN200 at 0.500 % — 5 m of depth per kilometre, and 105 reaches exceed 1 km |
| `SLS_MIN_PLOTS = 50` never binds | no pockets to absorb | it becomes the single most contested number in W10 — see B.4 |
| Every plot within reach of a corridor | dense grid | 1,186 plots unserved; 333 km of corridor collects 151 m³/d |
| Load conservation trivially exact (E1 passes at 3,619.6 vs 3,619.6 m³/d) | 3,017 units, all near a chamber | 98.3 % placed; ~1,233 m³/d silently unplaced at `ASSIGN_M = 160 m` |

## A.3 Gradients at round 0.05 % steps — untested at scale, because W10 never laid one

**Verdict: not carried across at all.** [Certain].

`criteria.SLOPE_STEP = 0.0005` is applied in `hydraulic.HydraulicDesigner._lay` (rounded **up** per pipe) and `_smooth_runs` (eased **down** along a run). W10 does neither. Recomputed from `W10_pipes.shp`: every one of the 20,936 reaches is laid at exactly `smin_for(own DN, own flow)` — DN200 at 0.5000 %, DN250 at 0.3750 %, DN315 at 0.2700 %, and so on, with zero variance inside each diameter class.

That is not "round gradients". It is *minimum* gradients, which happen to be round because Table 11 is round. The consequences differ:

- W8's rule produces a drawing a contractor can set out, at a measured cost of 1.0 % more excavation and 0.12 m on the deepest chamber, and cuts the number of distinct gradients from 448 to 103 (`criteria.ASSUMPTIONS['SLOPE_STEP']`).
- W10's behaviour means the pipe **never uses fall the ground gives it**. On a stretch falling at 1.2 %, W10 lays 0.5 % and lets the invert climb back to cover — which is correct in the lay-shallow construction — but it also means no reach anywhere carries a gradient chosen by the ground, so the run-smoothing question never arises.

**Carry to W11a:** the rule is good and cheap. It cannot be validated at scale until a run actually lays a gradient other than the minimum.

## A.4 One outlet per structure, chamber clearance, inlet angle

**Verdict: untested rather than failed — W10 has no chambers.** [Certain].

`StructureResolver`, `ChamberPlacer.nudge_out_of_plots`, `_clearance`, `_one_outlet`, `_branch_offset` all operate on chambers. W10 solves on corridor nodes. 4,763 of 20,936 W10 reaches (1,220 km, 65 % of network length) are longer than the Table 12 maximum manhole spacing for their diameter; splitting to Table 12 would create about **30,900** chambers. None of the chamber-level rules has been exercised at that count.

Two things that *are* wrong now and will be worse then:

**The inlet-angle deviation is documented as two different numbers in the same code.** `criteria.INLET_MIN_DEG = 85.0`; the check fires at 85° (`turn > 180 - 85 + 1`) and the W8 audit table reads `75 of 1414 inlets under 85 deg`; but `audit._inlet_angle`'s docstring says *"the threshold is the project value INLET_MIN_DEG, 75 deg"*, the registry entry reads `G203-p30 (deviation: 75 deg)`, and `ASSUMPTIONS['INLET_ANGLE']` says the user set **85** and then that *"anything sharper than 75 deg is flagged"*. Three artefacts, two thresholds, one stated deviation. Against a guideline that says 90° flat (G203-p30), a deviation carried at two values cannot be defended to NWS. [Certain]

**The 85° deviation itself is a real non-compliance, correctly flagged in `GRADIENT_CRITERIA_VERIFIED` §6 item 7 and never closed.** It is the only place in the criteria where the code is *looser* than the guideline. That has to be a written derogation or it has to go.

## A.5 The RoadTreatment stage — reused, and three of its nine steps silently became no-ops

**Verdict: it did NOT behave the same. This is the clearest generalisation failure in the whole comparison, and it is mechanically provable.** [Certain].

`W10/py/p0_auto.treat_roads` calls:

```python
rt = RoadTreatment(attrs=attrs)          # sampler=None
out = rt.run(segs, units=None, out_path=...)
```

`RoadTreatment` guards on `units` and `sampler` in five places. With both absent:

| Step | Guard | W8 (97.4 km in) | W10 (1,351 km in) |
|---|---|---|---|
| `_drop_traffic_links` | `if not units: return segs, 0` | 82 dropped | **0** |
| `_drop_stubs` | `if not units: return segs, 0` | 0 dropped | **0** |
| `_drop_orphan_links` | `serves = True` unless `tree` exists | 52 dropped | **0** |
| `_handle_duals` two-lane side choice | `score()` returns `(0, -0.0)` for both sides | 0 pairs (none in area) | **17 pairs, side chosen arbitrarily** |
| `_collapse_roundabouts` plots-inside guard | `if utree is not None and ...` | rejected **69 of 81** candidate rings | **guard disabled** |

Measured from `W10_road_treatment.shp` — the only exclusions written are `dual-carriageway` (289, 141.87 km), `dual-carriageway (twin)` (69, 14.49 km), `roundabout` (304 arcs, 9.44 km) and `two-lane-other-side` (17, 2.41 km). No traffic links, no stubs, no orphan links.

And the roundabout guard mattered. Re-polygonizing the 304 removed arcs gives **87 rings**, equivalent radius median 12.3 m, max 20.5 m. Tested against `MoH_Plots`:

> **34 of the 87 rings collapsed as "roundabouts" intersect at least one registered plot. 28 contain a plot outright.**

In W8 the same test rejected 69 of 81 candidates — it was doing almost all the work. Its own docstring says so: *"Telling a roundabout from a small block cannot be done on shape alone."* At full scale it was switched off by omission, and roughly a third of the collapses are city blocks whose street network has been dissolved to a point.

**This is a call-signature failure, not a design failure.** The fix is one line and one check: `RoadTreatment` must refuse to run without `units` and `sampler`, and every step must report a count or declare itself skipped.

## A.6 The reroute passes — W10 *did* test them, and they made it worse

**Verdict: the brief is wrong on two points, and the answer is measured.** [Certain].

Two corrections. First, W6 went from **6 stations to 4**, not to 3 (`W6/docs/WHAT_CHANGED.md`: *"That search took the count from 6 down to 4"*). Second, W10 did not skip the idea — `p3_variants.py` implements it explicitly as *"re-route around the nodes that breached in the previous solve, the way W8 did"*. From `W10/run/p3_variants.csv`:

| Strategy | Breaches | Clusters | Stations | Lift |
|---|---|---|---|---|
| base (climb 400) | 219 | 33 | **21** | 2,815 m |
| avoid, 1 round | 223 | 32 | 23 | 2,920 m |
| climb-400 + avoid | 223 | 32 | 23 | 2,920 m |
| climb-1000 | 207 | 33 | 21 | 2,683 m |
| climb-2500 | 206 | 40 | 28 | 2,665 m |

Rerouting made it worse. The reason is in `BREACH_DIAGNOSIS` §8 and it is a good one: **only 13 of the 108 irreducible breaches have any alternative corridor edge on their run at all.** In a dense town grid a reroute swaps one of many parallel streets; across 531 km² most breaches sit on class-B (adverse ground) and class-E (artefact corridor) branches where there is no second route to find.

Caveat that keeps this at [Certain] on the measurement and [Likely] on the conclusion: W10's `avoid` ran **one round**; W8 runs six alternating `climb`/`depth` passes and keeps the best. The variants table sweeps `climb` separately and finds the same flat response, so a six-pass version would very likely land in the same band — but it was not run.

## A.7 Summary table — Part A verdict

| W8 choice | Generalises? | Evidence |
|---|---|---|
| Trunk taken as an INPUT, not derived | **Yes** | main pipe audit: 0 points past 12 m at nine DN/gradient combinations |
| Hierarchy (trunk / sub-main / lateral), `TIER` on every pipe | **Yes in principle, not implemented in W10** | W10 has no `TIER` field at all |
| Join cap = 20 | **No, as written** | different object; per km of trunk W8 is 3.3, W10 2.3, as-built 4.0 |
| Zero pumping stations | **No — but nearly holds in its own footprint** | 3 breaches / 32.6 m of lift on the same 5.51 km² |
| Round 0.05 % gradient steps | **Untested** | W10 lays only Table 11 minima; zero variance within a DN class |
| Lift-and-reset at the depth limit | **Yes** | reproduced exactly at full scale; 220 of 220 breach positions to 0.000 m |
| Depth checked between nodes | **Yes in `p2_depths`, dropped in `p2_sizing`** | 82,187 samples computed and never used — see B.9 |
| One outlet / clearance / branch offset | **Untested** | no chambers in W10 |
| Inlet angle 85° | **No** — and it is documented at two values | `criteria` 85, docstring and registry 75 |
| RoadTreatment | **No** | three steps became no-ops; roundabout guard off; 34 of 87 rings hold a plot |
| Reroute before accepting a pump | **No** | measured; `avoid` gives 223 breaches against 219 |
| Wadi exclusion | **Yes, and W10 dropped it** | see B.1 |
| Independent audit registry | **Yes — and it is the single thing that should have been carried first** | see Part B |

---

# PART B — the defect post-mortem

## B.0 Error classes used

| Class | Definition |
|---|---|
| **unwired rule** | a declared criterion that no code path reads |
| **stale variable** | a value left over from an earlier loop iteration or design pass |
| **wrong quantity measured** | the code measures something adjacent to what the rule names |
| **double-filtered metric** | a filter applied twice, or applied to a set already filtered |
| **single-tolerance metric** | a threshold-sensitive quantity published at one threshold |
| **unread source** | a governing document, or the project's own manual, not read before acting |
| **dead computation** | an expensive result computed and then discarded |
| **stale artefact** | an output file not regenerated after an input or the code changed |

## B.1 — The wadi exclusion was never wired in

**Class: unwired rule.** `criteria.HAZARD_WADI_CLASSES = (4, 5, 6)` existed since W8 and was read only by `p4_stp_siting.py`. No corridor or routing phase read it; 156.0 km of pipe (8.3 %) was laid on wadi ground. Now charged in `netlib.sewer_cost` at 5,000 m per edge; **131.7 km still sits on wadi ground** (independently re-measured here: 1,089 reaches, 131.7 km, 7.0 % of the network) because the corridors themselves are there.

**A correction to the correction.** `netlib.py` and `BREACH_DIAGNOSIS` §9 both state that `Hazard_T50y.tif` is *"a continuous float grid (1.00, 1.01, 1.02 …)"* and that therefore *"testing membership of {4, 5, 6} matches almost nothing and silently reports no wadi anywhere"*. **That is wrong.** Reading the full array: 709,183,851 valid cells, float32 dtype, values exactly integer, minimum 1.000, maximum 6.000, class counts 1: 415.8 M · 2: 121.3 M · 3: 103.0 M · 4: 28.8 M · 5: 31.8 M · 6: 8.5 M, and zero cells with `floor > 6`. `int(v) in (4,5,6)` and `floor(v) >= 4` are **identical** on this grid. W8's `prep.HazardSampler.is_wadi` was never broken. The fix is right; the reason given for it is not, and it wrongly implies a second defect in W8. [Certain]

> **CHK-WADI-01.** Recomputes: for every pipe reach, hazard class sampled at ≤20 m intervals along the geometry (not the midpoint). Source: `Data/04 Lekhuwair/Hazard_T50y.tif`, read fresh. Compares against: `HAZARD_WADI_CLASSES` and a declared project allowance for unavoidable crossings. Reports: km on class ≥4, split into *crossing* (contiguous run ≤ a declared crossing length, near-perpendicular) and *running along* (everything else), plus the share of samples where the grid has no coverage. **Fails the build** if any reach runs along a wadi, or if the constant is not read by the routing cost function.

> **CHK-WADI-02 (provenance).** Recomputes: dtype, min, max, and the set of distinct values of any classified raster before any class test is applied. Compares against: the class definition in `criteria`. Reports the value set. **Fails the build** if the values are not a subset of the declared classes. This one check makes the "continuous float" misdiagnosis impossible in either direction.

## B.2 — `p2_sizing.size_all` stored a previous diameter's gradient

**Class: stale variable.** The loop iterates `dn` and `s` together; when `hydra.size_pipe` returns `None` it sets `dn = DN_SERIES[-1]` and `break`s, leaving `s` at the last computed value. Five trunk reaches — 2.80 km entering the works with all 62,615 plots behind them — were held as DN1200 at DN200's 0.500 % where the floor is 0.075 %: 11.90 m of fall that should have been 1.6 m, and the deepest breach in the network.

Independently re-verified here on the corrected `W10_pipes.shp`: **0 of 20,936 reaches** have a laid gradient differing from `smin_for(own DN, own flow)` by more than 1e-6. The fix holds. The check takes three seconds.

> **CHK-GRAD-01.** Recomputes: `smin_for(reach.DN, reach.QPK)` from `sewnet.hydra` and `sewnet.criteria`, using only the diameter and flow written on the reach. Source: the design output layer, not the solver's internal state. Compares against: the laid `SLOPE_PCT`. Reports: count, km and the worst offender. **Fails the build** on any reach where laid < required, or where laid ≠ required without a declared reason (velocity cap, ground-driven steepening).

> **CHK-SIZE-01 (the root cause, not the symptom).** Recomputes: whether the sizing loop converged for each reach. Compares against: a required `SIZED_BY` field on every reach with one of `{capacity, d/D, velocity, horizon, INFEASIBLE}`. Reports: every `INFEASIBLE`. **Fails the build** on any reach whose diameter was set by the fallback branch. A pipe that cannot be fitted must be named, never written silently at the top of the series.

## B.3 — Depth measured to the INVERT where G203 p33 says COVER

**Class: wrong quantity measured. Inherited from W8, not invented by W10.** `hydraulic.HydraulicDesigner._lay` tests `(target_ch.z - inv_dn_gravity) > MAX_DEPTH`; `audit._max_depth` tests `c.depth = z - invert`; `criteria.MAX_DEPTH: float = 12.0  # m cover` labels it cover. `p2_depths.solve` and `p2_sizing` do the same. Both iterations have been stricter than the guideline by one outside diameter on every reach — 0.30 m at DN200, 1.30 m at DN1200. Measured cost: 219 breaches to invert against 204 to cover (`W10/run/p3_cover_rule.csv`).

> **CHK-DEPTH-01.** Recomputes: cover = ground − (invert + **the reach's own outside diameter**), and separately depth-to-invert, at every node and at every terrain sample along every reach. Source: the 0.5 m terrain VRT, re-sampled. Compares against: `MAX_DEPTH`, declared explicitly as *cover*. Reports both quantities side by side with the count that differs between them. **Fails the build** on any cover breach; reports the invert figure without failing.

## B.4 — The station count reported as 11, then 21, then 19

**Class: double-filtered metric, compounded by definition drift.** The 11 came from applying a catchment test to a set already cut to stations with 50+ plots *within 750 m*. `W10_stations_final.shp` holds a third number, 28, on the proximity count alone. `p3_variants.stations()` now runs one funnel — breaches → consolidate at 1.5 km → catchment ≥ 50 properties (54 m³/d) — and gives 21 on the pre-wadi routing, 19 after.

**It is still not fixed in the documents.** `W10_SUMMARY.md` line 15 says **19**; line 40 of the same file says **21**. Two numbers, one page. [Certain]

The deeper problem, correctly identified in `OPTIMISATION.md` and worth repeating: **counting stations by distance-clustering measures breach density, not pumping need** — a *stricter* 10 m cover rule gives *fewer* stations (16) and *more* lift (3,095 m). Total lift is the honest measure.

> **CHK-METRIC-01.** Recomputes: the station count from the single funnel function, in the audit, from the breach layer. Source: `W10_lift_sized.shp` and the accumulated-flow dictionary. Compares against: every occurrence of a station count in `W10/docs/*.md`, `README.md` and `_BRAIN/07_PROJECT_STATE.md`, found by regex. Reports: any document figure that does not equal the funnel's output. **Fails the build.** Publish total lift beside the count, always.

> **CHK-METRIC-02 (no re-filtering).** Recomputes: for any metric built by a chain of filters, the size of the set at each stage. Reports the chain as `N0 → N1 → N2`. **Fails the build** if any filter is applied to a set that a filter of the same kind has already reduced.

## B.5 — Plots measured from centroids, not polygons

**Class: wrong quantity measured.** Caught in Phase 0.1 before it reached a finding (commit b1d35ff: *"A farm plot runs to 9 ha, so a centre-point measure calls it unserved while its frontage is on the street. Correcting it moved 1,903 plots."*). The pattern survives in three current uses: `p1_loads` line 378 uses `representative_point().within(poly)` for the boundary test — correct for containment; `p2_sizing.assign_loads` uses `sjoin_nearest` on the plot geometry — correct; `p2_sizing` writes station points as `keep.geometry.centroid` of a buffer union — a centroid of a buffer, which is fine but undeclared.

> **CHK-GEOM-01.** Recomputes: every plot-to-corridor and plot-to-anything distance from the **polygon**. Source: `MoH_Plots.shp` geometry. Compares against: the same distance computed from the centroid. Reports: the count and the largest plots where the two answers differ by more than one plot radius. **Fails the build** if any published served/unserved or distance figure was produced by a centroid measure without that being stated in the same table.

## B.6 — Dual-carriageway proximity reported at a single tolerance

**Class: single-tolerance metric.** Also caught in Phase 0.1: 8.27 km at 12 m, 0.56 km at 6 m, 0.10 km at 4 m — a factor of 80 across a band of 8 m, because 12 m catches service roads and verges. `p0_mainpipe.py` now reports at 6 and 12 m. Re-measured here on the finished design:

| Tolerance | W8 pipe (71.6 km) | W10 pipe (1,882.9 km) | NAMA as-built |
|---|---|---|---|
| 4 m | 0.198 km (0.28 %) | 2.06 km (0.11 %) | 4 of 3,267 pipes (0.1 %) |
| 6 m | 0.292 km (0.41 %) | 3.64 km (0.19 %) | — |
| 12 m | 2.965 km (4.14 %) | 19.06 km (1.01 %) | — |

Two honest readings. W8's 0.198 km is almost exactly its 26 legitimate perpendicular crossings (~8 m of buffer each). W10's 2.06 km is not — see B.11.

> **CHK-TOL-01.** Recomputes: any proximity metric at a declared band of tolerances (4 / 6 / 12 m for dual carriageways). Reports all of them. **Fails the build** if a single-tolerance figure appears in any document without the band beside it.

## B.7 — `lay()` recorded post-reset depth, so the optimiser silently did nothing

**Class: wrong quantity measured, presenting as a silent no-op.** After a breach the invert is reset to `shallow`, so `depth[n]` reads about 2.4 m. The relief calculation `excess = depth[n] - MAX_DEPTH` was therefore always negative and nothing was ever upsized. Fixed by recording `predepth[n]` before the reset — the fix is documented in the function's own comment.

This is the most dangerous class in the whole list: **the run completed, produced output, and reported no error.** The only symptom was that the answer did not move.

> **CHK-NOOP-01.** Recomputes: for any iterative improvement pass, the count of elements changed per pass and the objective value per pass. Source: the pass history. Compares against: zero. Reports the history. **Fails the build** if pass 0 changes nothing, or if the objective is identical to the un-optimised baseline to machine precision — an optimiser that finds nothing must say "nothing was available", never return silently.

> **CHK-NOOP-02 (companion).** Recomputes: whether the quantity the optimiser reads is the quantity the constraint acts on. Concretely: assert `predepth ≥ depth` at every reset node and that the relief test reads `predepth`. **Fails the build** on any node where the optimiser's input has been overwritten by the constraint's own remedy.

## B.8 — An optimisation strategy G203 p29 prohibits, already documented as prohibited in T02

**Class: unread source.** `p3_optimise.py` upsizes pipes so they can be laid flatter. G203 p29 §4.3.1: *"Sewers shall not be oversized to facilitate flatter slopes."* One sentence, "shall not", no exception in 201 pages, with the reason on p167 and p185. `TUTORIALS/T02` §6.3 already carried the clause and the consequence. The script was written without reading it.

The measurement is worth keeping — the prohibition costs 195 km of upsizing that would have cleared 112 of 220 breaches and 5 of 21 stations — but the answer is settled.

> **CHK-SRC-01 (provenance).** Recomputes: for every numeric constant in `criteria.py`, the value extracted from the source PDF at the cited page by text search. Source: `Data/PAM-GUD-203*.pdf`, `PAM-GUD-201*.pdf`. Compares against: the constant. Reports every mismatch and every constant with no citation. **Fails the build** on a mismatch; reports an uncited constant unless it is listed in `ASSUMPTIONS`.

> **CHK-SRC-02 (method gate).** Recomputes: nothing. It is a checklist assertion — any script whose docstring proposes a *method* (as opposed to a measurement) must name the `TUTORIALS/T02` section that governs it, and that section must not contain a prohibition of it. Reports: scripts with no declared T02 section. **Fails the build.** This is the check that would have cost ten minutes and saved a day.

## B.9 — NEW: the mid-span depth check is computed and thrown away

**Class: dead computation.** `p2_sizing.main()` calls `edge_profiles(G, lines)` — 82,187 terrain samples at 20 m — assigns `mid, midz`, and then runs its own inline depth loop that **never references either**. The check exists in `p2_depths.solve` (it takes `mid`/`midz` and clamps the invert at a ridge) and is the specific defence W8 added after the W6 audit passed chambers at 21 m. The sized run, which is the published design, does not have it.

`BREACH_DIAGNOSIS` §10 quantifies the consequence: **7 breaches that clear on nodes do not clear with the ground between them**, and one run hides a ridge worth 3.77 percentage points of gradient. With 102 reaches over 1 km and the longest at 6,541 m, this is not a rounding matter. [Certain]

> **CHK-DEAD-01.** Recomputes: nothing. Static — any name bound to the result of a function whose cost exceeds a threshold, and never subsequently read, is an error. Reports the binding and its line. **Fails the build.** A cheap linter rule catches the exact signature of this defect.

*(CHK-DEPTH-01 above, which re-samples the terrain independently of the solver, catches the consequence even if the linter does not catch the cause.)*

## B.10 — NEW: 120 reaches are laid with less than the minimum cover, worst 0.40 m

**Class: wrong quantity measured (a constant standing in for a variable).** `p2_depths.OD_DEFAULT = 0.30` is used as the outside diameter for every reach regardless of diameter, in both the swept solve and the sized solve (`shallow = zn - MIN_COVER_CROWN - 0.30`). At a run head the invert is set to `ground − 1.30 − 0.30`, so the crown of a DN1200 sits **0.40 m** below ground against a guideline minimum of 1.30 m (G203-p33 §4.6.3).

Recomputed from `W10_pipes.shp` using `criteria.outside_diameter(DN)`:

| DN | Worst cover | Reaches under 1.30 m |
|---|---|---|
| 200 | 1.40 m | 0 |
| 250 | 1.35 m | 0 |
| 315 | 1.29 m | 23 |
| 400 | 1.20 m | 15 |
| 500 | 1.10 m | 18 |
| 600 | 1.00 m | 14 |
| 700 | 0.90 m | 20 |
| 800 | 0.80 m | 9 |
| 900 | 0.75 m | 9 |
| 1200 | **0.40 m** | 12 |
| **Total** | | **120 reaches, 34.2 km** |

`BREACH_DIAGNOSIS` §10 records the *other* half of this ("the outside diameter in the solve is a fixed 0.30 m … a run upsized to DN900 would lose another 0.6 m of allowance") but only as an under-charge on depth. The over-charge on cover — a live G203 non-compliance on 34.2 km — was not reported. W8's check B1 (`_cover`, which uses `C.internal_diameter(r.dn_mm)` per reach) catches it in one pass. [Certain]

> Covered by **CHK-DEPTH-01** and **CHK-OD-01** below.

> **CHK-OD-01.** Recomputes: the outside diameter used by the depth solver for each reach. Compares against: `criteria.outside_diameter(reach.DN)`. Reports: every reach where the solver used a constant. **Fails the build.** No geometric constant may stand in for a per-reach property once diameters exist.

## B.11 — NEW: 2.80 km of trunk is surcharged, and 10.68 km exceeds the d/D limit

**Class: consequence of a fix, uncaught because the check was not carried across.** Re-running W8's check A6 (`_dod`) against `W10_pipes.shp`:

| | Reaches | Length |
|---|---|---|
| **Surcharged** — the diameter cannot pass its peak flow at the laid gradient | **5** | **2.80 km** |
| Over the Table 10 d/D limit | 66 | 10.68 km |
| Over 3 m/s | 0 | — (highest velocity 1.03 m/s) |

The worst is DN1200 carrying **1,361 L/s at 0.0750 %** — the trunk arriving at the existing works with the whole town behind it. `BREACH_DIAGNOSIS` §9 states the physics correctly (*"a single DN1200 cannot carry 1,361 L/s at 0.075 % inside its 0.50 d/D limit … Not fixed here"*), but the design was then re-run, published, exported to DXF and KMZ, and written into the live documents with that reach in it. **The gradient fix in B.2 converted an over-steep trunk into a hydraulically incapable one, and no check stood between the two.**

W8's `_dod` docstring says exactly why this matters: *"that is a surcharged pipe, the worst failure there is, and it must never be silently skipped."* [Certain]

> Covered by **CHK-DOD-01** in Part C. It must fail the build.

## B.12 — NEW: 1.67 km of pipe runs ALONG a dual carriageway

**Class: unwired rule.** Project rule 7 is absolute: *"no pipe of any kind runs along a dual carriageway, trunk included."* `netlib.sewer_cost` charges for length, climb, wadi and joins — there is **no dual-carriageway term at all**, and no check. W8 charged `CROSS_PENALTY_M = 2500` and, after the user found it, marked *every* physically crossing pipe rather than only the ones it created.

Measured on `W10_pipes.shp` against the 6 m band around the 289 `dual=1` lines:

| | Reaches | Overlap |
|---|---|---|
| More than 30 m inside the band — **running along** | **21** | **1.67 km**, longest single overlap 176 m |
| 30 m or less — crossings and clips | 135 | 1.98 km |

The 135 crossings are unchecked for perpendicularity, for the 70 m maximum, and for proximity to an underpass; none is charged. In proportion W10 is no worse than the as-built (0.11 % within 4 m against 0.1 %) — that is the honest reading, and it is [Likely] because the draftsman's DXF, which is most of the network, was drawn by a person who avoided the carriageways. But 1.67 km of running-along against a zero-tolerance rule is a defect, and nothing in the pipeline would have found it.

> Covered by **CHK-DUAL-01** and **CHK-DUAL-02** in Part C.

## B.13 — NEW: every analysis output except the pipes predates the fix it was used to justify

**Class: stale artefact.** The wadi penalty went into `netlib.py`, which every phase imports. Only two scripts were re-run afterwards. From file mtimes:

| Time | Output | Status |
|---|---|---|
| 09:46 | `W10_corridors.shp` | pre-fix |
| 09:57 | `W10_corridors_noded.shp` | pre-fix |
| 10:02 | `W10_joins.shp`, `W10_subnet_segments.shp`, `p1_subnetworks.csv` (**214 joins**) | pre-fix |
| 10:04–10:05 | `W10_nodes_depth.shp`, `W10_lift_stations.shp`, `p2_depth_sweep.csv` | pre-fix |
| 10:11 | `W10_west_*.shp`, `p5_west_options.csv` | pre-fix |
| 10:14 | `W10_stp_candidates.shp`, `p4_stp_candidates.csv` | pre-fix |
| 10:41–10:51 | **all of `p3_variants` / `p3_depthcost` / `p3_cover_rule` / `p3_prune` / `p3_multiworks`** | pre-fix |
| 11:08 | `W10_breach_diagnosis.shp` (220 breaches) | pre-fix |
| **11:12** | **`W10_pipes.shp`, `W10_lift_sized.shp` (239 breaches), `W10_stations_final.shp`** | **post-fix** |
| 11:15 | `p6_rising_mains.csv` | post-fix |

So `OPTIMISATION.md`'s ten-strategy table — the evidence for "nothing beats the baseline" — was computed on a routing that the shipped design no longer uses, with a baseline of 219 breaches against the current 239. The postscript records the corrected totals but the table above it was not re-run. Same for the breach diagnosis (220 against 239), the subnetwork layer (214 joins against a claimed 206), the STP siting surface, and the west-leg study.

The conclusions are [Likely] still right — the wadi penalty pushes routes off wadi beds, which raises pumping, and every strategy would move together. But nothing in the record demonstrates it. [Certain] on the timestamps.

> **CHK-STALE-01.** Recomputes: for every output artefact, the modification time of every input file and every source module in its import closure. Compares against: the artefact's own mtime. Reports: every artefact older than something it depends on. **Fails the build.** This is `make` semantics, and it is the single cheapest check in the registry.

## B.14 — NEW: W8's join sweep chose the cap with three exemptions baked into "OK"

**Class: unread source — the project's own doctrine.** `W8/py/sweep_joins.py`:

```python
def ok(r):
    return (r["stations"] == 0 and r["max_depth_m"] <= 12.0
            and set(r["fails"]) <= {"C4", "C8", "D1"})
```

The cap of 20 was selected by an acceptance function that treats failures of C4 (inlet angle), C8 (branch start offset) and D1 (property-connection length) as passes. The user's own standing rule is *"No exemptions in compliance checks — a skipped row reads as a PASS; check every element, whatever flag it carries."* Three named rows were flagged, so the sweep's verdict is "the cap works, apart from the things that were already broken". The number 20 may still be right; the argument for it is not clean. [Certain]

> **CHK-EXEMPT-01.** Recomputes: nothing. Static — no acceptance, sweep or optimiser function may contain a set of check ids it is willing to see fail. Reports the function and the whitelist. **Fails the build.** If a check is genuinely not applicable, it returns `NOT_CHECKABLE` from the registry with a reason, which is already counted as a failure.

## B.15 — NEW: 1.7 % of the load never lands on the network

**Class: silent drop.** `p2_sizing.assign_loads` uses `sjoin_nearest(..., max_distance=ASSIGN_M)` with `ASSIGN_M = 160.0`. 98.3 % of the load is placed; **74,675 − 73,442 = 1,233 m³/d never enters the network** and no reach carries it. The docstring calls the shortfall "a discretisation artefact, not unserved plots", which is true of the cause and not of the consequence: the design conveys 1,233 m³/d less than the design basis says exists.

W8's checks E1 (mass balance) and E2 (*"doctrine (zero silent drops)"*) both pass exactly on the test area — 3,619.6 against 3,619.6 m³/d, 3,017 of 3,017 units. Neither exists in W10.

> Covered by **CHK-LOAD-01/02** in Part C.

---

# PART C — the audit contract for W11a

## C.0 Principles

1. **The solver never grades its own homework.** Every check recomputes from the output layers and the raw sources — terrain VRT, hazard grid, cadastre, road file, guideline PDFs — never from solver state. W8 got this right and it is the reason its registry is worth keeping.
2. **A check that cannot run is a failure.** W8's `failures` property already counts `NOT_CHECKABLE` as failing. Keep it.
3. **No exemption whitelists anywhere** (B.14).
4. **Blocking versus reporting is decided by whether the finding is a guideline breach or a judgement.** A guideline breach blocks. A project convention, a cost trade or an assumption-dependent result reports.
5. **Every published number is produced by exactly one function**, and the document check compares the document against that function's output (B.4).

## C.1 The registry

Legend — **B** = fails the build, **R** = reports only. "New" marks a check neither W8 nor W10 has.

### Group A — Pipes and hydraulics

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| A1 | Minimum main diameter | G203-p22 Tab 6 | smallest `DN` in the pipe layer | ≥ DN200 on every reach | **B** |
| A2 | Material by diameter | G203-p22/23 Tab 6–7 | `criteria.material(DN)` per reach | recorded material matches | **B** |
| A3 | Minimum gradient | G203-p29 Tab 11 + p27 §4.2.2.1 | `hydra.smin_for(reach.DN, reach.QPK)` from the written DN and flow | laid ≥ required, and laid = required unless a declared reason | **B** |
| A4 | Maximum velocity | G203-p27 §4.2.2.2 | `hydra.pipe_state` at the laid gradient | v ≤ 3.0 m/s | **B** |
| A5 | Self-cleansing at peak | G203-p26–27 | velocity at peak, and the tractive minimum at τ = 1.0 Pa | v ≥ 0.75 m/s **or** gradient ≥ tractive minimum | **B** |
| A5b *(new)* | τ sensitivity | GAP-9 | re-run A5 at τ = 2.0 Pa | share of network that would fail — reported, never hidden | R |
| **A6** | **Proportional depth d/D and capacity** | G203-p27 Tab 10 | `hydra.pipe_state(DN, laid slope, QPK)`; `dod is None` means surcharged | zero surcharged reaches; d/D ≤ 0.65 (≤350) / 0.50 (>350) | **B** |
| A7 | No reverse gradient | G203-p29 §4.3.1 | `inv_up > inv_dn` on every gravity reach | zero reversed | **B** |
| A8 | Construction tolerance | G203-p29 §4.3.1 | fall per reach | > 40 mm unless velocity-capped | **B** |
| A9 | Rising mains | G203-p50 §8.1 | duty flow / area | 0.75 ≤ v ≤ 3.0 m/s; duty ≥ arriving flow | **B** |
| **A10** *(new)* | **Diameter provenance** | G203-p29 §4.3.1 prohibition | required `SIZED_BY` field per reach | value in {capacity, d/D, velocity, horizon}; **"depth" is not permitted** | **B** |
| **A11** *(new)* | **No silent fallback sizing** | project rule (B.2) | detect reaches whose DN came from the loop's fallback branch | zero; an unfittable reach is written `INFEASIBLE` and listed | **B** |
| A12 *(new)* | Table 11 gate | G203-p29 | reproduce all nine Table 11 rows from Colebrook-White, ±5 % | all nine reproduce | **B** |

### Group B — Cover and depth

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| **B1** | Minimum cover to crown | G203-p33 §4.6.3 | cover = ground − invert − `outside_diameter(reach.DN)`, at nodes **and** every terrain sample | ≥ 1.30 m everywhere | **B** |
| **B2** | Maximum depth | G203-p33 + project rule 9 | **cover** = ground − crown, reported beside depth-to-invert | ≤ 12.00 m cover, no exemptions | **B** |
| **B3** *(new)* | Depth between nodes | project rule (W6 failure) | terrain re-sampled at ≤20 m along every reach, in the **sized** solve | no sample over the limit | **B** |
| **B4** *(new)* | OD provenance | B.10 | the OD value the solver used per reach | equals `outside_diameter(DN)`; no constant | **B** |
| B5 *(new)* | Depth-limit economics | G203-p33 ("cost of excavation") | breaches and lift at 10 / 12 / 14 m cover | reported as a decision table for NWS | R |

### Group C — Chambers and layout

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| C1 | Maximum chamber spacing | G203-p30 Tab 12 | reach length vs `mh_max_spacing(DN)` | 100/120/150/200 m by class | **B** at chamber stage, R at network-solve stage (declare which stage the run is) |
| C2 | Chamber at change of direction | G203-p30 | interior deflection on cleaned vertices | ≤ `ROAD_BEND_DEG` | **B** |
| C3 | Drop / backdrop bookkeeping | G203-p30 §4.4 | inlet invert minus outgoing invert at every chamber | >600 mm recorded as backdrop, >2 m as vortex | **B** |
| **C4** | Inlet angle | G203-p30 (90°) | turn between inlet and outlet bearings | **one** declared threshold; anything sharper listed | R on the flag, **B** if the code carries two thresholds (A.4) |
| C5 | One outlet per structure | project rule / SWNETWROK | out-degree per node | exactly 1 | **B** |
| C6 | No loops | project rule | acyclic, one weakly connected component, edges = nodes − 1 | true | **B** |
| C7 | Chamber clearance | layout convention (no PAM minimum) | KD-tree pairs under 3 m, excluding consecutive | zero | **B** |
| C8 | Branch start offset | project rule (10 m) | head chambers within 10 m of a junction/outfall | listed | R |
| C9 *(new)* | Chamber not inside a plot | user 2026-08-21 | every chamber against **every** plot polygon, not only loaded ones | zero inside; those stuck are listed with the plot id | **B** on any not listed |

### Group D — Corridor quality *(entirely new group)*

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| **D1** | Wadi exposure | `HAZARD_WADI_CLASSES`, user 2026-08-19 | hazard class sampled at ≤20 m along every reach | zero reaches running along class ≥4; crossings listed | **B** |
| **D2** | Hazard-grid provenance | B.1 | dtype, min, max, distinct value set of the grid | values a subset of the declared classes | **B** |
| **D3** | No pipe along a dual carriageway | project rule 7 | overlap length inside the 6 m band per reach; >30 m = running along | zero running along | **B** |
| **D4** | Dual crossings | project rule 7 + user 2026-08-20 | every physical crossing, its angle, its length, distance to an underpass | ≤70 m, within 25° of square, and either at an underpass (≤30 m) or priced | R with a schedule; **B** if any crossing is uncounted |
| **D5** | Corridor treatment completeness | A.5 | every `RoadTreatment` step returns a count or declares itself skipped; the stage refuses to run without `units` and `sampler` | no step silently returns 0 for a missing argument | **B** |
| **D6** | Roundabout collapse evidence | `road_treatment` docstring | re-polygonize every collapsed ring; test against the cadastre | no collapsed ring contains or intersects a registered plot | **B** |
| D7 | Corridor productivity | `OPTIMISATION.md` §7 | m of corridor and m of pipe per m³/d, by branch | reported by decile; the emptiest branches listed with their pumping cost | R |
| D8 | Unserved plots | project scope | plots with no corridor within `PLOT_SERVED_M`, measured from the polygon | count and pocket-size distribution | R |
| D9 | Corridor connectivity | Phase 0.3 | connected components of the noded graph | ≥ 99.5 % of length in one component; stitching links listed with their length | **B** |

### Group E — Loads and conservation

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| **E1** | Mass balance at the outlet | bookkeeping | flow arriving at the sink vs the sum of placed unit loads plus infiltration | agree within 0.5 m³/d | **B** |
| **E2** | Every load unit placed | doctrine, zero silent drops | placed load vs the load layer total | 100 %, or an explicit listed exception set with its m³/d | **B** |
| E3 *(new)* | Accumulation monotonic | physics | accumulated flow along every flow path | never decreases downstream | **B** |
| E4 *(new)* | Load basis provenance | PROJECT-STATE §2 | OR, properties per plot, Tier A ratios, return factors printed with the run | match the locked basis; any deviation named | **B** |
| E5 *(new)* | Peaking factor hold | G1-p72 NOTE | PF applied per reach against the 100-property hold | no PF applied below the hold; PF never truncated | **B** |
| E6 | Infiltration | G1-p72–73 | 720 L/d/km × upstream length, unpeaked | matches | **B** |

### Group F — Hierarchy and tier consistency *(new)*

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| F1 | Every pipe carries a TIER | `LEARNING_FROM_ASBUILT` | field present and in {trunk main, sub main, lateral} | 100 % populated | **B** |
| F2 | Tier monotonicity | as-built decomposition | for every reach, the tier of what it receives | a lateral never receives from a sub-main or trunk | **B** |
| F3 | Joins per km of trunk | as-built 4.0/km | connectors onto trunk manholes ÷ trunk km | reported against 4.0; **never as a total** | R |
| F4 | Tier length shares | as-built 5.1 / 18.4 / 66.5 % | share of length by tier | reported against the as-built | R |
| F5 | Diameter monotonic | physics | DN along every flow path | never decreases downstream | **B** |

### Group G — Metric definition stability *(new — this group is what W10 most needed)*

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| **G1** | One function per published number | B.4 | the funnel function's output, run inside the audit | every occurrence of that number in `W10/docs/*.md`, `README.md`, `_BRAIN/07_PROJECT_STATE.md` equals it | **B** |
| **G2** | No re-filtering | B.4 | set size at each filter stage, printed as `N0 → N1 → N2` | no filter of a given kind applied twice | **B** |
| **G3** | Measurement geometry declared | B.5 | every plot distance from the polygon, and from the centroid for comparison | published figures use the polygon, or say they do not | **B** |
| **G4** | Threshold-sensitive metrics in bands | B.6 | proximity metrics at a declared band (4 / 6 / 12 m) | no single-tolerance figure published alone | **B** |
| **G5** | Artefact freshness | B.13 | mtime of every output vs every input and every module in its import closure | no output older than a dependency | **B** |
| **G6** | No dead computation | B.9 | static scan for expensive results bound and never read | none | **B** |
| **G7** | No silent no-op | B.7 | per-pass change count and objective for every iterative pass | pass 0 changes something, or the pass reports "nothing available" | **B** |

### Group H — Source fidelity and process *(new)*

| ID | Requirement | Source | Recomputes independently | Pass criterion | B/R |
|---|---|---|---|---|---|
| **H1** | Constant provenance | project rule (no invented metrics) | every `criteria` constant re-extracted from the cited PDF page by text search | value matches; uncited constants appear in `ASSUMPTIONS` | **B** on mismatch, R on missing citation |
| **H2** | No exemption whitelist | user doctrine (B.14) | static scan of every acceptance/sweep/optimiser function for a set of check ids | none | **B** |
| **H3** | Method gate against T02 | B.8 | every script proposing a *method* names its governing `TUTORIALS/T02` section | named, and that section contains no prohibition of it | **B** |
| H4 | Assumption register complete | `ASSUMPTIONS` | every assumed value appears in the register with its reason | complete | **B** |
| H5 | Figures read back | user 2026-09-01 | every exported figure re-opened and checked non-empty | no figure with an empty layer behind a full legend | **B** |

## C.2 Blocking versus reporting — the rule, stated once

The registry is **59 checks: 50 blocking, 9 reporting** (Group A 12 B / 1 R · B 4 / 1 · C 7 / 2 · D 6 / 3 · E 6 / 0 · F 3 / 2 · G 7 / 0 · H 5 / 0).

**Fails the build (50 checks):** anything that is a breach of PAM-GUD-201/202/203 as written; anything that is a breach of a settled project rule with no stated derogation (12 m depth, no pipe along a dual carriageway, no pipe on wadi ground, one outlet per structure); anything that makes a published number untraceable to the function that produced it; and every check that cannot run.

**Reports only (9 checks):** trade-offs the guideline frames as economic (B5 depth versus excavation cost), calibration against the as-built (F3, F4), assumption sensitivities (A5b at τ = 2 Pa), scope questions (D7, D8), and the C4/C8 flags that need a designer's eye rather than an automatic fix — **but they are reported as failures of a named check, never omitted, and never whitelisted in an acceptance function.**

## C.3 What the registry would have caught, and when

| Defect | Check | Would have fired |
|---|---|---|
| Wadi never wired | D1, D2 | first sized run |
| Stale gradient on 5 trunk reaches | A3, A11 | first sized run |
| Depth to invert | B2 | first sized run |
| 11 / 21 / 19 / 28 stations | G1, G2 | first document build |
| Centroid plot measures | G3 | Phase 0.1 |
| Single-tolerance dual proximity | G4 | Phase 0.1 |
| Optimiser silent no-op | G7 | first optimiser pass |
| Prohibited upsizing | A10, H3 | before the script was written |
| **Surcharged trunk, 2.80 km** | **A6** | **first sized run** |
| **Cover below 1.30 m, 34.2 km** | **B1, B4** | **first sized run** |
| **Mid-span check discarded** | **B3, G6** | **first sized run** |
| **1.67 km along a dual carriageway** | **D3** | **first sized run** |
| **Roundabout guard disabled** | **D5, D6** | **Phase 0.2** |
| **Stale analysis artefacts** | **G5** | **at every document build after 11:12** |
| **1,233 m³/d unplaced** | **E2** | **first sized run** |
| W8's whitelisted join sweep | H2 | W8 |
| W8's two inlet-angle thresholds | H1, C4 | W8 |

---

## D. What I could not check

- **W8's join sweep is not reproducible from the repository as it stands.** `sweep_joins.py` writes no CSV; the table in `LEARNING_FROM_ASBUILT.md` is the only record. Re-running it is a ~1-hour job and was not done here. The table is taken at face value. [Guessing] on whether the intermediate rows would reproduce exactly.
- **W10's 206-versus-214 join count.** `p1_subnetworks.csv` has 214 rows and `W10_SUMMARY.md` says 206. `p1_subnetworks.py` prints both `raw joins onto the trunk` and `subnetworks`, which are different quantities, and neither document says which one 206 is. Not resolved.
- **Whether a six-pass reroute would beat W10's one-round `avoid`.** Not run. The flat response across the climb-penalty sweep makes a large gain unlikely, but that is [Likely], not measured.
- **Whether the pre-11:12 analyses would change materially if re-run.** The wadi penalty is 5,000 m per edge, which is large; the direction of every effect is predictable but the magnitudes are not.
- **The tractive assumption.** τ = 1.0 Pa has no guideline basis (GAP-9, confirmed by full-text search of both PDFs). 915 of W8's 1,414 reaches and an unmeasured share of W10's would fail at τ = 2 Pa. That is a live exposure, not a defect.

---

## E. The one-paragraph recommendation

Build W11a's auditor **first**, from W8's `stages/audit.py`, before a single line of design code. Run it against W10's existing output layers on day one — it will produce a failing table immediately, and that table is the specification for what W11a has to fix. Then port the design stages one at a time, each with its checks green. The reason W8 shipped with three *named* failures and W10 shipped with at least eight unnamed ones is not that W10's engineering was worse. It is that W8 could see itself and W10 could not.
