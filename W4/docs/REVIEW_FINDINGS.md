# W4 Adversarial Hydraulic Review — confirmed findings and fixes (2026-08-18)

> **SUPERSEDED — kept as the record of W4.** The live design is **W5**; see `_BRAIN/00_CURRENT.md` for what is current. Numbers here use one property per plot and 6.0 people per property, both replaced on 2026-08-19.

21-agent skeptic panel (4 attack lenses + independent verification per finding) on `sewnet` after the first audit-clean run. **17 raw findings, 11 confirmed, 11 fixed** — all fixes verified by the 43-test suite plus a full re-run ending at 0 violations. Full evidence: workflow `wf_c3b61e4b-01d` transcripts.

| ID | Sev | What was wrong | Fix |
|---|---|---|---|
| EDGE-1 | critical | Node-spanning tree omitted every loop-closing street edge — 25.2 km of streets had no pipe; plots connected cross-block (177 m worst) | `topo.augment_cross_streets`: every off-tree street with frontage load gets a sewer, summit-split into two head branches (crest-manhole layout); +676 branches / 25.3 km; corner keys derived from geometry (networkx edge order is arbitrary — the first implementation wired half the chains to the wrong corner) |
| HYD-1 | major | `smax_for` bisection non-monotone: near/above velocity-capped capacity it returned a garbage ~1e-4 slope instead of the true v=3 cap or an infeasibility signal | Two-stage bisection (capacity slope first, then velocity) + explicit `INFEASIBLE` sentinel; solver skips infeasible DN candidates; unit tests for both regimes |
| HYD-2 | major | Hydraulics computed on nominal DN while OD-designated PVC-U bores ~6% smaller — ~15% capacity overstatement on 95% of the network; d/D certified against the wrong section | `criteria.internal_diameter()` (PVC-U SDR34 derate ≤315, GRP nominal=ID); all design-facing hydraulics via `hydra.pipe_state()` on the true bore; Table-11 gate keeps DN basis (the table's own convention); SDR class tagged assumption |
| SOLVER-1 | major | Drop trigger measured inlet-to-node-invert while the outgoing pipe sat lower — combined drops could split under the 600 mm/2 m thresholds unrecorded | Chamber datum = outgoing invert; drops = inlet inv minus outgoing inv; audit independently re-derives every drop and flags missing/misclassified records |
| SOLVER-2 | major | Manhole depth recorded to node invert, understating construction depth where drops exist; SLS pockets missed | Same datum fix: depth = ground − outgoing invert; pocket detection on real depth |
| SOLVER-3 | major | Sizing could oscillate between adjacent DNs forever and stop at max_iter with inverts inconsistent with final diameters | DN-history cycle detection breaks oscillation upward; a final lay pass always runs when not converged |
| F1 | major | "0 violations" concealed that ~96% of pipes miss 0.75 m/s at saturation peak and comply only via the untested τ=1 Pa assumption | `audit.selfclean_stats`: share below 0.75, tractive reliance, and τ=2 redesign exposure (1,626 pipes) reported in run log, summary and methodology |
| HYD-3 | minor | SewerGEMS export carried Manning n=0.010 — ~30% phantom capacity vs the CW ks=1.5 mm design basis | Export n=0.013 (ks-equivalent); Tab-8 conflict flagged as NWS kickoff item in the import procedure |
| F2 | minor | Start-year self-cleansing check loaded CLASS=B only, excluding 248 unparceled buildings that exist today | Start-year case = B + U |
| F3 | minor | Peltier comparison silently floored at 0.1 L/s — exactly the silent-truncation A9 forbids | Peltier held at its 100-property flow (same convention as Merrimack), tagged in ASSUMPTIONS |
| F4 | minor | Plots with CLASS outside A/B/P silently vanished from the load model | Counted (`class_other`), audited as a violation if nonzero |

Refuted (6): findings the verification stage could not reproduce or judged immaterial at concept stage — retained in the workflow transcript, not acted on.

---

## User structural audit (2026-08-18) — the two layout rules

The user asked whether the SWNETWROK rules had actually been adopted: **(1) no loops, (2) one outlet per junction, with extra branches starting ~10 m clear of the chamber.** Verifying against the run output rather than the code's intent found this:

| # | Rule | State before | Fix |
|---|---|---|---|
| U-1 | No loops | **Held.** Spanning tree by construction: 2,358 pipes over 2,359 chambers, acyclic, one component | — (invariant now asserted inside `resolve_structures`, not just at tree build) |
| U-2 | One outlet per junction | **Held in the graph, broken on the ground.** 0 nodes had out-degree >1, but 251 chamber pairs sat within 1 m of each other (many at the same point), each with its own outlet — physically a two-outlet junction. Root cause: centimetre-level node keys from road noding plus cross-street heads planted beside existing junctions | `manholes.resolve_structures`: merge chambers within 3 m → re-derive the shortest-path tree over the merged pipe set (merging can also close a loop) → the leftover pipes are the extra outlets |
| U-3 | Extra branch starts ~10 m clear | **Not adopted at all.** The W4 plan had said "discard the mechanism, keep the rule" — the topological rule was kept and the geometric separation never implemented, so augmented branch heads sat 2.5 m (and less) from junction chambers | `FANOUT_OFFSET_M = 10 m` in criteria; every leftover pipe is trimmed to start at the **next house connection** along its alignment, or 10 m when that connection is nearer; branches too short to keep a clear start are dropped and reported; a final pass slides any head still inside another chamber's clearance |

Test-area effect: 255 chambers merged, 125 fan-outs resolved, 357 branch starts offset, 90 branches dropped (streets served from the far end); network 95.3 → 90.4 km, chambers 2,359 → 2,137.

Independent verification on the exported network: loop-free **PASS**, one-outlet **PASS**, 568/569 branch heads ≥10 m clear, one chamber pair at 2.78 m (vs 3.0 m). The two residuals are reported, not suppressed. New permanent guards: `mh-clearance` and `head-offset` audit checks, assertions inside `resolve_structures`, and `test_one_physical_outlet_per_structure` on a synthetic two-chambers-at-one-point case.

---

## Refactor + road-treatment review (2026-08-18, 33 agents)

Run after the object-model refactor and the new road-treatment stage. 29 raw findings, **17 confirmed, all fixed**; 12 refuted. The refactor itself was clean (the equality gate held) — the damage was in the new treatment stage and in one check the refactor dropped.

| ID | Sev | What was wrong | Fix |
|---|---|---|---|
| RT-2 | critical | **The roundabout detector collapsed city blocks.** Circularity 4πA/P² ≥ 0.60 is vacuous — a square scores 0.785, a triangle 0.605 — so 12 of 15 "roundabouts" were residential blocks with plots inside, destroying 1.34 km of real street and welding 50 corner nodes up to 26 m away | Shape alone cannot tell a roundabout from a block, so the test is now evidence-based: **no plot inside the ring** (decisive), equivalent radius ≤ 30 m, at least two approach arms, curved arcs. 22 rings now rejected for plots inside, 44 for straight edges |
| RT-1 | critical | A blanket `length > 1.0` filter in the roundabout step deleted **every** sub-metre segment, not just re-anchored legs — 46 of 108 deletions had nothing to do with roundabouts, and one was the sole bridge to a 164-node sub-network. This, not stub removal, drove unreachable nodes 9 → 28 | The filter applies only to legs the step actually re-anchored. Unreachable nodes now 12; stubs dropped 18 → 1, confirming 17 were debris the stage created itself |
| F1 | critical | **The refactor silently dropped the over-capacity check.** A reach whose diameter cannot pass its peak flow returns `dod = None`; the new check skipped None instead of failing, so a surcharged pipe passed every hydraulic test | `_dod` now fails explicitly on `None` with "CANNOT CARRY … surcharged" |
| RT-7 | major | The outfall moved uphill (z 351.24 → 351.63, 665 m away) because `_dissolve` deletes degree-2 nodes — and the true lowest boundary node was one of them | The outfall is chosen on the **raw** graph and its node protected through treatment. Back at z 351.24 |
| RT-5 | major | Vertex de-duplication could drop a segment's **terminal** vertex, moving the endpoint beyond the 1 cm node key and detaching the corridor | Terminal vertex always preserved |
| F3 | major | The audit turned any crashing check into `NOT_CHECKABLE`, and the tally counted it as a pass — a broken check could hide a real violation | `NOT_CHECKABLE` now counts as a failure; the table reports the three states separately |
| F4/chambers | major | `enforce_spacing` runs after the tree assertion and could hand an existing chamber a second outlet when a cut landed on its key | Cuts landing on an existing chamber are skipped and the chain closed |
| F2/chambers | major | The change-of-direction rule went unenforced after re-anchoring: bends appeared post-merge with nothing to re-split them | `enforce_spacing` now splits on bends as well as length |
| RT-4/F6 | major | Main-road classification was computed, exported and **never applied**, while the docstring claimed it excluded corridors | Documented honestly as advisory-only pending your hierarchy layer; the corridor layer carries MAIN_ROAD / ELIGIBLE for review |
| RT-6/F8 | minor | `ROAD_BEND_DEG` and `ROAD_CHORD_DEV_M` were registered as active criteria but dead — the placer used a hardcoded 45° and the audit 45.5° | Placer and audit both read `ROAD_BEND_DEG`; the unused chord constant is declared as a W5 item |
| — | labelling | 14 of the 26 collapsed rings are 0.2–4 m noding slivers, not roundabouts | Reported separately as `sliver_rings_collapsed` — both collapse, but a 2 m triangle is not called a roundabout |

Refuted (12), each reproduced but judged immaterial or misattributed: frozen-dataclass sharing of TABLE11, `fingerprint` dead code, cover-check bore-vs-OD (12 mm, non-binding), `_cut`'s 0.5 m rule (never fires), and others — all retained in the workflow transcript.

**Net effect of the fixes:** chambers 2,137 → 1,655 (−23 %), network 90.4 → 89.5 km, unreachable nodes 28 → 12, max depth 15.1 → 13.4 m, audit failures 5 → **2** (inlet angle, and 152 house connections over 50 m).
