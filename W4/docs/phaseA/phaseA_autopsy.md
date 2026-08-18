# SWNETWROK Repo Autopsy — Storm Drainage Network Pipeline (v5)

Repo: `D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/_REFERENCE/SWNETWROK` (shallow clone, single commit `96e4afd`). ~3,340 lines Python across 6 modules + 4 test files. Confidence tags per project convention: statements below are [Certain] unless tagged otherwise — everything was read line-by-line.

---

## 1. Purpose & Architecture

**Purpose:** build a gravity stormwater *conveyance alignment* (not a sized hydraulic design) from road centrelines + DEM + outfall points. Deliverables: fully attributed channel/node shapefiles (SWMM/SewerGEMS-ready connectivity), annotated DXF, territory PNG.

**Scripts (all in `py/`):**

| Module | Lines | Role |
|---|---|---|
| `swnetwork.py` | 558 | Entry point + orchestration; ALL parameters at top (lines 30–47); also contains the inline fan-out resolver (lines 248–434) and hydraulic audit (lines 468–545) |
| `dem.py` | 175 | DEM load/reproject (`load_dem`), bilinear sampler factory (`make_sampler`), D8 catchment delineation via pysheds (`delineate_catchments`) |
| `roads.py` | 554 | Noding (`node_roads`), elevation sampling (`sample_line`), ridge/sag split, outfall snapping (`snap_outfalls_to_road_graph`), catchment-majority territory assignment (`assign_majority`), boundary reassignment (`reassign_boundary_roads`) |
| `graph.py` | 161 | Per-territory directed graph builder (`build_territory_graph`) — BFS orientation toward outfall, gap-healing |
| `hydraulics.py` | 517 | Invert solver (`route_topdown`), MAX_COVER + bottleneck pruning (`prune_to_feasibility`), pool re-assignment loop, plus a **dead** alternative fan-out resolver (`resolve_fanouts`, lines 430–517 — never called by the pipeline) |
| `outputs.py` | 816 | Attribute/naming engine (`_build_network_attrs`), `write_shp`, `write_dxf`, `write_img` |

**Execution order / data flow** (`swnetwork.py.__main__`, steps [1]–[9]):

1. Load Roads.shp + outfall.shp, reproject to EPSG:32640 (lines 59–64). Outfall invert = ground − `depth` field.
2. Load DEM once into memory, build bilinear sampler closure (lines 70–71).
3. `node_roads` → `ridge_sag_split` → list of `seg_tuples = (pts[(x,y,z)…], LineString, start_type, end_type)` (lines 77–78). This tuple/dict-of-`pts` structure is the lingua franca between all modules.
4. Snap outfalls onto the road graph (`snap_outfalls_to_road_graph`, line 83) — may split segments in-place.
5. Sample outfall ground/invert (lines 87–98).
6. D8 catchments per outfall (`delineate_catchments`, line 107), buffered by 1 DEM cell (lines 110–114).
7. `assign_majority` → each segment becomes a dict `{pts, geom, territory, blacklist, start/end_node_type}` (line 118).
8. Per territory: `build_territory_graphs` → `prune_to_feasibility` → segments touching pruned nodes go back to the pool with territory blacklisted (lines 132–176); release road-disconnected segments (183–200); `reassign_boundary_roads` (204); `pool_reassignment_loop` (208–211); rebuild graphs and recompute inverts (215–246).
   - [8b] Global inline fan-out resolution over `assigned` seg dicts (248–434) + post-injection slope cleanup (443–466).
   - [8c] Audit MIN_COVER / MAX_COVER / MIN_SLOPE on every assigned node/segment (468–545).
9. `write_shp` / `write_dxf` / `write_img` (550–556).

Central data structure throughout: the mutable list `assigned` of segment dicts — modules communicate by mutating `territory`/`blacklist`/`pts` in-place, and per-territory `inverts_by_territory {node_key: invert}` dicts keyed by `round_node(x,y)` (2-decimal, i.e. 1 cm merge tolerance, `graph.py:7–10`).

---

## 2. Tree-Network Construction (the repo's key strength)

The tree discipline is enforced **twice, at two different levels** — this is the essential thing to understand about the architecture.

### 2a. Graph construction — `graph.build_territory_graph` (graph.py:13–141)

- **Nodes:** segment endpoints keyed by `round_node(x, y)` = coordinates rounded to 0.01 m (graph.py:7–10). Attributes: `x, y, ground_elev, node_type` (`sag`/`ridge`/`normal`, priority-merged at graph.py:59–67). Endpoint identity relies entirely on `unary_union` noding in `roads.node_roads` (roads.py:116–140) producing bit-exact shared coordinates.
- **Edges:** one per segment, attributes `length` (2-D arc length) and `seg_pts` (the sampled `(x,y,z)` polyline, reversed if the edge is reversed).
- **Flow-direction assignment — BFS mode** (graph.py:73–111): build *undirected* adjacency from all territory segments, find the snap node (nearest graph node to the snapped outfall via KDTree, line 87), then **BFS outward from the outfall**; for every parent→child discovery, add directed edge `child → parent` (line 106). Flow therefore always points toward the outfall *regardless of local terrain dips* — the deliberate design decision that makes it a pipe network, not a surface-flow model (verified by test `test_bfs_orients_edge_through_local_dip`, test_graph.py:86–102).
- **Loop breaking is implicit in BFS:** a road edge whose both endpoints are already visited is *never added* — the resulting DiGraph is a **BFS spanning tree** (every node has out_degree ≤ 1 by construction). Loops in the road grid are broken at the discovery frontier.
- Nodes not reached by BFS (no road path to outfall) are deleted (graph.py:109–111); `swnetwork.py:183–200` later releases their segments to the pool.
- If the snap distance exceeds `outfall_snap_r` (30 m), the whole territory graph is returned empty and all its segments go to the pool (graph.py:91–92).
- **Fallback mode** (no outfall coordinate): pure high→low orientation per segment endpoint elevation (graph.py:113–119) — used only in unit tests and legacy paths.
- **Gap-healing** (graph.py:124–139): KDTree `query_pairs(connect_tol=0.5 m)` over node coordinates; a synthetic edge high→low ground is added between near-miss endpoints, then **rejected if `nx.is_directed_acyclic_graph` fails** (add-then-check, line 136–139). Synthetic edges carry `seg_pts=None` — they exist in the routing graph but have no corresponding segment in `assigned`, so they are never written to outputs (a hidden ~0.5 m pipe; see weaknesses).

### 2b. Outlet selection & territory partition

- Outfalls are **inputs** (outfall.shp), not discovered. Snapping priority (`roads.snap_outfalls_to_road_graph`, roads.py:236–358): (1) if within 2 m of a road line, project onto it and *split the segment there* to create an exact junction node (`_split_seg_at_proj`, roads.py:190–233); (2) else nearest road-graph *local elevation minimum* node within 30 m; (3) else lowest node within 30 m; (4) else keep raw position.
- **Territory = D8 surface catchment majority:** `dem.delineate_catchments` (dem.py:73–175) runs pysheds fill_pits → fill_depressions → resolve_flats → D8 flowdir → accumulation, snaps each outfall to a high-accumulation cell (1 % of max threshold, retry `acc ≥ 50`), and polygonizes `grid.catchment`. `roads.assign_majority` (roads.py:422–467) then gives each *whole* segment to the catchment holding the majority of its length — segments are never split at catchment boundaries (the older splitting variant `assign_to_catchments`, roads.py:363–419, is retained but unused by the main flow).
- **Note the README lie:** README §5 claims territory assignment is "Multi-source Dijkstra from outfalls". The v5 code does no such thing — it is catchment-majority + pool competition. Dijkstra appears only in `outputs.py` for naming.

### 2c. Repair loops that keep the forest consistent

1. **Prune-feedback** (swnetwork.py:164–176): segments whose endpoint got pruned lose their territory and blacklist it.
2. **Release of road-disconnected segments** (swnetwork.py:183–200): assigned by catchment overlap but absent from the BFS graph → back to pool, *without* blacklisting.
3. **`reassign_boundary_roads`** (roads.py:470–527): convergence loop — a segment neither of whose endpoints touches any other segment of its own territory is defected to the most common neighbouring territory (O(n²) per pass, comment at roads.py:502).
4. **`pool_reassignment_loop`** (hydraulics.py:278–375): each pooled segment tries every non-blacklisted territory whose graph contains one of its endpoints; the territory graph is rebuilt with the candidate included and accepted only if `route_topdown` passes AND no node exceeds max_cover (hydraulics.py:351–360); rejection blacklists that territory. Up to 10 rounds.

### 2d. Fan-out resolution — the second tree-enforcement layer (swnetwork.py:248–434)

Why needed: `assigned` segments are a **superset** of the BFS tree edges (loop-closing roads, parallel carriageways, and pool-added segments stay assigned even though the graph dropped them). When outputs orient every segment independently by endpoint inverts, a junction can appear to emit >1 channel.

- Build a global (cross-territory) registry `outlet_segs[junction] = [(tid, gap_end, seg, far_end_invert)…]` by orienting each assigned segment by *effective* endpoint inverts — actual routed invert if the node is in the invert dict, else the estimate `ground − MIN_COVER` (swnetwork.py:319–341). Ties in invert are skipped (line 341) — a hole, see weaknesses.
- For each junction with >1 outgoing channel (outfall snap nodes exempt, lines 299–308, 351):
  - **Winner:** same-territory case → steepest hydraulic drop = lowest far-endpoint invert (line 372). Cross-territory case → the territory with most tributaries *arriving* at the junction wins (`inlet_counts`, lines 363–370), tie-broken by steepest drop — losing the connectivity-rich outlet would strand its upstream branch in a foreign territory.
  - **Losers:** geometrically trimmed `FANOUT_GAP_M = 10 m` back from the junction (`_trim_pts_from_start/_end`, lines 269–290), becoming new source segments with head invert `ground − MIN_COVER`; feasibility gate: if `far_inv + MIN_SLOPE·remaining_length > ground_head − MIN_COVER` the loser is orphaned instead (lines 392–394, 412–414). Losers shorter than 10 m are orphaned.
- **Post-injection cleanup** (lines 436–466): because the pass is single-sweep in arbitrary junction order, an injected head invert can retroactively break a slope computed earlier; a second sweep orphans any assigned segment whose endpoint-invert slope < MIN_SLOPE.
- **Dead twin:** `hydraulics.resolve_fanouts` (hydraulics.py:430–517) is a cleaner graph-level algorithm — rebuild edges purely by invert orientation (`_build_hydraulic_graph`, 380–427), then per fan-out junction evaluate each outlet by re-routing and keep the one giving the **highest outfall invert** (least energy loss), severing losers. It is never imported by `swnetwork.py`; the README §9 describes *this* algorithm, not the inline one that actually runs. [Certain — grep confirms zero call sites.]

### 2e. Branch ordering / dendritic naming (`outputs._build_network_attrs`, outputs.py:111–376)

No flow accumulation exists anywhere. "Ordering" is purely nominal: a hand-rolled Dijkstra (outputs.py:218–230) over the undirected assigned-segment adjacency from each outfall snap node gives every node its network distance; nodes and channels are then numbered per type in **descending distance** — farthest element = index 1 (`O1-J1`, `O1-C1`; naming at outputs.py:239–334). Node types: outfall > sag > ridge > junction (priority at outputs.py:136).

---

## 3. Hydraulic "Design" Method — what it does and does NOT do

**It does not compute a single flow.** No rational method, no IDF, no runoff coefficients, no Manning capacity, no diameters, no velocities. `delineate_catchments` produces catchment polygons for *territory assignment and a shapefile* — the areas are never converted to discharge. The output channels carry no `Q`, no `D`, no `v`. This is an **alignment + invert solver**, and its own README oversells it as "hydraulically-correct".

**Invert solving — `hydraulics.route_topdown` (hydraulics.py:32–95): a single downstream sweep, not iterative.**

- Process nodes in `nx.topological_sort` order (line 53).
- Source node (in_degree 0): `I = ground − min_cover` (line 64).
- Edge U→D: target = `I_outfall` if D is the outfall else `ground_D − min_cover`; recovery slope `s_rec = (I_U − target)/L`, pipe slope `s_pipe = max(s_rec, min_slope)`, candidate `I_D = I_U − s_pipe·L` (lines 69–81). So the pipe *aims to come back up to minimum-cover depth* and only stays deep when MIN_SLOPE forces it. Since `s_pipe ≥ s_rec`, arrival is always at or below target → MIN_COVER is structurally guaranteed at nodes.
- Junction: `I_D = min(candidates)` — deepest arriving pipe sets the node invert (line 86).
- Feasibility: `I_arrived_at_outfall ≥ I_outfall` → PASS/FAIL (line 94). The outfall invert is a physical fixed point (from the `depth` field).

**Constraint enforcement is by pruning, not by redesign** (`prune_to_feasibility`, hydraulics.py:196–265):

- *Phase 1 — MAX_COVER:* loop `route_topdown` → delete every node deeper than max_cover (`prune_by_max_cover`, 161–193) → delete nodes that thereby lost their directed path to the outfall (`nx.ancestors` reachability, 187–191 — the "alternative-path rescue" of docs/plans/2026-03-27) → repeat until stable.
- *Phase 2 — bottleneck fallback for outfall-feasibility failures:* find node with highest excess cover (`find_bottleneck`, 100–112), trace upstream along the deepest-invert predecessor chain to its source (`find_guilty_branch`, 115–135), delete that source plus everything that loses its path (`collect_nodes_to_prune`, 138–154), repeat (max 2000 iterations).
- Pruned segments are pooled/orphaned, not redesigned (no pump option, no drop structure, no deeper outfall proposal).

**Constraints enforced:** MIN_SLOPE (0.0005), MIN_COVER (1.0 m), MAX_COVER (3.0 m), plus one-outlet-per-junction. **Not enforced:** max slope / max velocity, min velocity (self-cleansing), diameter-dependent minimum slopes, manhole spacing, drop-manhole handling, capacity of any kind.

**Per-channel inverts vs node inverts** (outputs.py:272–322): each channel recomputes its *own* downstream invert `own_dn_inv = up_inv − max(min_slope, (up_inv − target_dn)/L)·L`, which can sit **above** the junction node invert when a deeper sibling dominates — i.e. implicit external drops at junctions. These are silently embedded in `inv_dn` vs the node's `invert`; nothing labels them as drops.

**Verification:** step [8c] (swnetwork.py:468–545) independently re-audits every assigned endpoint for MIN/MAX_COVER and every segment for MIN_SLOPE and prints violations (outfall nodes exempted from MIN_COVER, line 471–473). Good hygiene — audit is separate from the solver.

---

## 4. Outputs

**Libraries:** geopandas `GeoDataFrame.to_file` (SHP), ezdxf R2010 (DXF), matplotlib Agg (PNG). All in EPSG:32640.

**Shapefiles** (`outputs.write_shp`, outputs.py:381–532):

| File | Geometry | Schema |
|---|---|---|
| `swnetwork.shp` | LineString | `territory, status='ASSIGNED', name (O#-C#), node_up, node_dn, inv_up, inv_dn, gnd_up, gnd_dn, length_m` (3-dp rounding) — connectivity-complete for SWMM/SewerGEMS import |
| `nodes.shp` | Point | `name (O#/O#-J#/S#/R#), type (outfall/junction/sag/ridge), territory, ground, invert, depth` |
| `orphan_channels.shp` | LineString | `territory (-1 or tid), status ∈ {DISCONNECTED_ORPHAN, DESIGN_ORPHAN}`, null attrs |
| `orphan_nodes.shp` | Point | `ground` only |
| `catchments.shp` | Polygon | `territory` |
| `sw_inlets.shp` / `sw_ridges.shp` | Point | `name, ground, territory` (sag and ridge nodes) |

**DXF** (`write_dxf`, outputs.py:537–771): layers `SW-DRAIN-SUB-NN` (ACI 1–6 cycled per territory), `SW-DRAIN-ORPHAN` (grey 8), `SW-OUTLETS`, `SW-JUNCTIONS`, `SW-DRAIN-LABELS`, `SW-INLETS`, `SW-RIDGES`. Per node: circle + stacked labels `name / G:ground / I:invert / D:depth` in distinct colours (`_node_label`, 581–600). Per channel: chevron flow tick at midpoint plus name above / slope% and length below, rotated with the pipe (`_add_flow_tick`, 27–89). Outfalls: double circle + full stack. Sags double-circle, ridges X-cross. This DXF annotation engine is genuinely good QA tooling.

**PNG** (`write_img`, 776–816): dark-theme territory map with legend.

---

## 5. Weaknesses (concrete)

1. **Hardcoded absolute path** `BASE = "D:/Projects/Renardet/SW Net - 2"` (swnetwork.py:30) — and it contradicts the README's documented repo layout: code reads `{BASE}/SHP/…` (not `data/SHP/…`) and writes to `{BASE}/W2/shp|dxf|img` (not repo-root `shp/`, `dxf/`, `img/`). The committed outputs were evidently hand-copied. The pipeline as cloned **does not run without editing paths**.
2. **README/doc drift (three material lies):** (a) §5 "Territory Assignment — Dijkstra from Outfalls" describes an algorithm the code doesn't use (it's catchment-majority); (b) §9 fan-out "winner = highest calculated outfall invert" describes the dead `resolve_fanouts`, not the inline steepest-drop/connectivity rule that runs; (c) README default `RIDGE_RISE = 0.10` vs code `0.05` (swnetwork.py:38). Docs/plans file says `MAX_COVER = 2.0`, code says 3.0.
3. **Broken test suite:** `test_hydraulics.py:7` imports `excess_cover` which does not exist in `hydraulics.py` → the whole module fails at import. Stale vs. some earlier version. [Certain]
4. **Dead code:** `hydraulics.resolve_fanouts` + `_build_hydraulic_graph` (~140 lines) never invoked; `roads.assign_to_catchments`, `roads.split_at_outfalls`, `roads.ridge_split`, `dem.sample_elev` also unused by the main flow. Two divergent fan-out implementations invite editing the wrong one.
5. **Silent elevation fallback = 0.0 m** for an outfall outside the DEM (swnetwork.py:92–94) — poisons the entire territory's routing instead of aborting.
6. **Gap-heal edges are invisible pipes:** synthetic edges (`seg_pts=None`, graph.py:136) participate in invert propagation but have no segment in `assigned`, hence never appear in SHP/DXF — up to 0.5 m of unmodeled pipe at heal points, and the invert dict values on either side embed its drop.
7. **Fan-out tie skip:** segments whose two effective endpoint inverts are exactly equal are never registered as outlets (swnetwork.py:341) — flat pairs can leave an unresolved multi-outlet junction that the audit won't flag (audit checks slope/cover, not out-degree).
8. **BFS shortest-hop tree is depth-blind:** the spanning tree minimizes hop count, not excavation. A route over a hump gets chosen over a marginally longer downhill street, then MAX_COVER pruning amputates it. A length- or elevation-weighted Dijkstra tree would orphan less. [Likely — structural inference, not benchmarked.]
9. **Order-dependent single-pass fan-out** with a patch-up second sweep that *orphans* rather than re-resolves (swnetwork.py:436–466) — collateral loss where a re-route existed.
10. **Performance scaling:** `reassign_boundary_roads` is O(n²) per convergence pass (roads.py:502); `pool_reassignment_loop` rebuilds the entire territory graph per (segment × territory) trial (hydraulics.py:328–332); `prune_to_feasibility` re-routes the full graph up to 2000 times. Fine at storm-test scale (~10³ segments), a real risk at Ibri scale (36 zones, tens of thousands of segments). [Likely]
11. **Fragile dependency:** pysheds 0.5 requires a manual site-packages patch (`np.in1d`→`np.isin`, requirements.txt:15–22) — non-reproducible environment.
12. **Cover audit only at endpoints:** interior ground points between nodes aren't checked against MAX_COVER; ridge/sag splitting at 5 cm thresholds mitigates MIN_COVER but a long segment through gently rising ground can exceed MAX_COVER mid-span unflagged. [Likely]
13. **Parallel edges collapse:** `edge_data[(sk,ek)]` overwrites duplicates (graph.py:81–82) and DiGraph can't hold parallel edges — dual-carriageway twin segments survive in `assigned` and surface as fan-out losers rather than being deliberately collapsed (the Ibri doctrine rule 7 handles this upstream instead).

---

## 6. Verdict Table — reuse for a GRAVITY SANITARY SEWER pipeline

| Module / function | Verdict | Notes |
|---|---|---|
| `dem.load_dem`, `dem.make_sampler` | **Reusable as-is** | Generic in-memory DEM + bilinear sampler; matches project's DTM workflow |
| `dem.delineate_catchments` (D8/pysheds) | **Discard** | Sanitary territories come from plot-density road zones (project rule 8: "never raw DEM watersheds"); also drags the fragile pysheds patch |
| `roads.node_roads` | **Reusable as-is** | unary_union noding with min-length filter — foundation of any road-following network |
| `roads.sample_line` | **Reusable as-is** | Elevation profile along segments; needed for cover checks |
| `roads.detect_ridges/sags`, `ridge_sag_split*` | **Adaptable** | Sag-inlet logic is storm-specific; ridge detection remains useful as a gravity-divide screen for zone boundaries and SLS pocket detection |
| `roads.snap_outfalls_to_road_graph`, `_split_seg_at_proj` | **Adaptable** | Exact on-road projection-split is directly what STP/SLS/trunk-connection snapping needs; drop the "local minimum" preference (sanitary outlets are designed, not terrain minima) |
| `roads.assign_majority` / `assign_to_catchments` | **Discard** | Catchment-overlap territory logic is storm-specific; keep only the `blacklist` seg-dict pattern |
| `roads.reassign_boundary_roads` | **Adaptable** | Territory-contiguity cleanup maps directly onto zone-boundary tidying (rule 8) |
| `graph.round_node`, node/edge schema | **Reusable as-is** | 1 cm coordinate keying, `ground_elev` attrs, `seg_pts` on edges |
| `graph.build_territory_graph` — BFS orientation toward outlet | **Adaptable (core keeper)** | Exactly the right paradigm for sanitary (flow to outlet regardless of dips, spanning-tree loop breaking, unreachable-node culling, snap-radius rejection). Upgrade BFS to length/elevation-weighted Dijkstra tree to cut depth (weakness 8) |
| `graph` gap-healing + DAG guard | **Adaptable** | Keep the add-then-DAG-check pattern; materialize healed edges as real segments (weakness 6) |
| `hydraulics.route_topdown` | **Adaptable (core keeper)** | The downstream-sweep invert solver transfers wholesale; replace scalar MIN_SLOPE with diameter-dependent minimums (G203) → needs flow accumulation + sizing to run first or iterate; MAX_COVER→12 m (G203 p33) |
| `hydraulics.prune_by_max_cover`, `prune_to_feasibility` | **Adaptable (reinterpret)** | For sanitary, "pruned" ≠ orphan — pruned pockets are SLS candidates (rule 9). The alternative-path-rescue reachability logic is directly reusable to *delimit* non-gravity pockets |
| `hydraulics.pool_reassignment_loop` | **Adaptable** | Try-territory/accept-if-feasible/blacklist loop is a sound zone-reassignment engine; fix the per-trial full-graph rebuild cost |
| `hydraulics.resolve_fanouts` (dead) | **Adaptable** | Ironically the cleaner one-out enforcement for sanitary (graph-level, re-route evaluation, no geometric gap hack); resurrect this, not the inline gap version |
| `swnetwork.py` [8b] inline fan-out + 10 m gap | **Discard (mechanism), keep rule** | One-outlet-per-manhole is mandatory in sanitary too, but the 10 m gap trick is a storm-channel visual device; a sanitary loser should flip flow direction or become an SLS boundary |
| `swnetwork.py` [8c] audit block | **Reusable as-is** | Solver-independent constraint audit; extend with velocity/diameter checks |
| `outputs._build_network_attrs` (Dijkstra dendritic naming) | **Reusable as-is** | Rename prefixes to manhole/pipe convention; distance-ranked naming carries over |
| `outputs.write_shp` | **Adaptable** | Schema needs `diameter, Q, v, material`; connectivity fields (`node_up/node_dn` + endpoint inverts) already SewerGEMS-shaped |
| `outputs.write_dxf` (label stacks, flow ticks) | **Reusable as-is** | Best-in-repo QA artifact; layer names/labels trivially re-branded |
| `outputs.write_img` | **Reusable as-is** | Quick territory overview |
| **Missing entirely for sanitary** | — | Plot-load allocation (T01 doctrine), flow accumulation down the tree, Manning partial-full pipe sizing, self-cleansing velocity check, manhole placement/spacing (G203), drop-manhole handling, SLS siting — none of this exists in the repo and must be built |

**Bottom line:** the transferable asset is the *skeleton* — noding → outlet-snapped BFS-oriented spanning tree per territory → single-sweep top-down invert routing with prune-and-repool feasibility → audit → attributed SHP/DXF. The hydrology (D8 catchments), the sag/inlet logic, and the gap-style fan-out surgery are storm baggage. Nothing in the repo computes flow or sizes a pipe, so the sanitary pipeline gains geometry and invert machinery, not hydraulic design.