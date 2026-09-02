# OPEN-S4-1 — the trunk, the corridor graph, and where the 773 systems actually come from

**Measured 2026-09-02 on the published layers. Analysis and proposal only — no `.py` file was
changed. Every number below is reproducible from the scripts named in §9.**

---

## 1. The uncomfortable answer first

**Fixing the trunk does not recover the 729 km. It recovers 0.7 km of it.**

The report's sentence — *"a trunk in 74 pieces … is why the design comes out with 773 drainage
systems"* — is wrong, and I can put a number on how wrong. The corridor graph stage 4 receives
is **already in 771 pieces before the trunk is looked at**, and the design's 773 systems are
those 771 plus two. The 74 trunk pieces sit **inside 35 of them**. Welding the trunk into one
spine therefore takes 771 systems to 739 and the off-trunk network from 788.9 km to 788.2 km.

The 729 km has a different cause, in a different stage, and it is a much smaller fix:

> `CORRIDOR_CUT_M = 4.0` (`s2_corridors.py` line 210) punches a **4.0 m hole** in the road
> network at every point a draftsman's line passes near it, and nothing closes the hole —
> `contract.NODE_MERGE_M` is 3.0 m, one metre too small. **746 connectors, none longer than
> 4 m, take the corridor network from 771 pieces to 317 and lift the network that reaches the
> trunk from 1,430 km to 1,931 km.**

Both defects are real and both should be fixed. But they are not the same size, and the
priority is the opposite of the way OPEN-S4-1 is currently written.

| fix | systems | trunk pieces | on-trunk km | OFF-trunk km |
|---|---|---|---|---|
| today | **771** | **74** | 1,429.8 | **788.9** |
| stage 4 weld only *(this ticket as written)* | 739 | **4** | 1,472.4 | 788.2 |
| stage 2 cut-hole heal only | **317** | 74 | 1,931.2 | **287.5** |
| **both** | **289** | **4** | **1,976.1** | **287.4** |

*(corridor-graph km, before the spanning tree drops loop-closing streets and the finger prune.
Published-layer equivalents in §7.)*

---

## 2. Your hypothesis, tested

> *"stage 3 designs the trunk on the raw Main Pipe alignment and mints its own chamber
> coordinates, while stage 4 builds its hierarchy on the stage 2 corridor graph with a
> different node set. Where a trunk chamber does not coincide with a corridor node, the trunk
> breaks."*

**The first half is exactly right and worse than stated. The second half describes a mechanism
that is not in the code.**

Stage 3 does mint its own chambers, and they land nowhere near stage 2's nodes:

| stage-3 trunk chambers (758) within … of a corridor node | count | share |
|---|---|---|
| 0.5 m | 24 | 3.2 % |
| 3.0 m (`contract.NODE_MERGE_M`) | 52 | 6.9 % |
| 10 m | 118 | 15.6 % |
| 50 m | 426 | 56.2 % |

median offset **42.4 m**, p90 **122 m**, max **379 m**.

They also collide: `corridor_nodes`, `W11a_trunk.gpkg/nodes` and `W11a.gpkg/nodes` all mint
`N0000001…` from zero, so **758 NODE_UID strings mean three different points** — `N0000002`
is one point in the corridor layer and another **34.5 km away** in the trunk layer. That is a
contract defect in its own right (§8, OPEN-S4-2).

**But stage 4 never attempts that match.** It reads stage 3's trunk correctly (manifest:
`trunk (stage 3)`, n = 754, from `W11a_trunk.gpkg`) and then discards the geometry except as a
*proximity mask over stage 2's corridors*:

```python
# s4_hierarchy.py line 1041-1043, the trunk_how == "stage3" path
trunk_u = unary_union(list(trunk.geometry))
def trunk_where(r, g, _u=trunk_u):
    return _u.distance(g.interpolate(0.5, normalized=True)) < TRUNK_ON_M   # 0.5 m
```

So the object stage 4 calls "the trunk" is **a subset of stage 2's corridors**, never stage 3's
reaches. It arrives in as many pieces as stage 2's copy of the alignment does. Measured on the
same corridor node graph, with no re-noding:

| trunk edge set | edges | km | components |
|---|---|---|---|
| `trunk = True` (0.5 m midpoint mask) | 563 | 76.56 | **74** |
| `SRC == 'main_pipe'` (stage 2's own tag) | 566 | 77.52 | 65 |
| union of the two | 587 | 77.80 | 66 |

The mask choice accounts for **8** of the 74 pieces. The other **65 come from stage 2's
corridor set**, and no node-matching rule in stage 4 can mend them: contract the 74 pieces and
look for a corridor path between them, and **35 clusters are mutually unreachable**. The 39
pairs that *can* be joined need **51.6 km** of detour between them (p50 177 m, max 9.4 km).

**So (b) is not a matching failure. It is stage 4 never putting the trunk into the graph at
all.**

---

## 3. Where the 773 systems and the 729 km actually come from

Rebuilding `adopt_graph` exactly (23,342 nodes / 24,963 edges / 2,218.7 km) reproduces both
published figures — 771 corridor components, 74 trunk pieces — and then splits cleanly:

| corridor components | count | km |
|---|---|---|
| containing at least one trunk edge | **35** | 1,429.8 |
| containing none | **736** | **788.9** |

736 + 74 = **810 roots**, which is exactly the `outfalls` metric in `manifest_s4.json`. The
729.3 km the report calls "reaches no trunk" is the published remnant of that 788.9 km.

**What the trunk defect actually costs is the 39 excess outfalls, not the system count.**
810 roots inside 771 components means 39 components end at more than one outfall — a direct
**H15** breach (*"each component ends at exactly one outfall, checked on the published
layer"*), and every one of the 39 is a detached trunk piece rooted at its own low point instead
of draining to the works. That is serious. It is just not 729 km.

Are the 736 trunk-less components near the alignment? Some are, and this is the one place the
trunk defect and the corridor defect touch:

| no-trunk components, distance to the raw Main Pipe | comps | km |
|---|---|---|
| ≤ 10 m | 32 | **174.4** |
| ≤ 25 m | 62 | 240.8 |
| ≤ 50 m | 95 | 325.3 |
| ≤ 1 km | 395 | 601.1 |
| > 1 km | 341 | 187.8 |

The four largest are 115.4 km at **7.0 m**, 43.5 km at 13.0 m, 34.6 km at 5.5 m, 18.7 km at
8.0 m from the client's own alignment — the main pipe runs straight past 174 km of network that
cannot reach it, because the corridor that carried it there was deleted (§4b) or was never
joined to it (§4a).

---

## 4. Defect (a): why stage 2 shreds the trunk 3 → 58 and loses 5.0 km

Two separate mechanisms, and the larger one has nothing to do with the trunk.

### 4a. The 4 m cut hole — the dominant defect in the whole pipeline

`s2_corridors.py` lines 1207-1218:

```python
draft_cover = unary_union(list(draft.geometry.buffer(CORRIDOR_MATCH_M)))   # 25 m
draft_cut   = unary_union(list(draft.geometry.buffer(CORRIDOR_CUT_M)))     # 4 m
for g in treated:
    if g.intersection(draft_cover).length > 0.75 * g.length:
        continue
    rest = g.difference(draft_cut)          # <-- a 4.0 m hole, never closed
```

A treated road that is not ≥75 % covered by the draftsman keeps the parts of itself more than
4 m from any drafted line. The removed 4 m is *not* replaced by a connection to the drafted
line — the surviving stub simply ends 4 m short of it. `contract.NODE_MERGE_M` is 3.0 m, so the
merge cannot close it either, and the `stitch` step only stitches skeleton pockets.

The signature is unmistakable — a step function at exactly 4.0 m:

| join every corridor endpoint to a line within … | components |
|---|---|
| 0.5 m | 765 |
| 3.0 m *(the merge radius — no effect)* | 764 |
| **4.0 m** | **444** |
| **4.5 m** | **299** |
| 10 m | 238 |

and the same test run on the corridor set **before H1** is even more direct:

| pre-exclusion set (corridors + removed) | components |
|---|---|
| as built | 560 |
| endpoints joined ≤ 3.0 m | 514 |
| endpoints joined ≤ 4.0 m | 201 |
| **endpoints joined ≤ 4.5 m** | **70** |

**490 of the 560 pre-H1 components are this one hole.** 70 is a physically plausible answer for
a scattered Wilayat; 560 is an artefact.

The code comment at line 211 already knows the failure mode — *"cutting at 25 m punched 25 m
holes and those holes were W10's single largest source of fragmentation (1,074 pieces)"*. The
cut was narrowed from 25 m to 4 m; **it was never closed**. A 4 m hole is still a hole.

Targeted simulation of the real patch (reconnect only `auto_road` stubs to the `draft` line
they were cut against, ≤ 4.05 m): **746 connectors → 317 components, on-trunk 1,429.8 → 1,931.2
km, off-trunk 788.9 → 287.5 km.**

### 4b. H1 applied to a client input, by deletion

Stage 2 applies H1 to the main-pipe corridors and **deletes** the offending stretches. Within
5 m of the raw alignment, `W11a_corridors_removed.gpkg` holds:

| REASON | pieces | km |
|---|---|---|
| wadi (along) | 73 | **9.508** |
| along a dual carriageway | 10 | 1.028 |
| dual crossing off square | 12 | 0.250 |
| wadi (along, audit.r4 sweep) | 1 | 0.013 |
| **total** | **96** | **10.80** |

Sampling the raw alignment every 5 m: **89.6 %** has a corridor within 0.5 m; the remaining
**8.91 km sits in 96 gaps**, the longest 935 m, then 505, 410, 340, 335 m. That is the 5.0 km
length loss and most of the 58 pieces.

**And stage 2 and stage 3 treat the same client input in opposite ways.** Stage 3 keeps the
alignment and *reports* the breach: `ON_DUAL_M` 534.7 m over 10 reaches, `ON_WADI_M` 11.03 km
over 156 reaches, 87 reaches carrying a `CROSS_ID`, and 75 `H1/R4` findings in
`s3_trunk_findings.csv`. Stage 2 deletes it. **Stage 3's treatment is the correct one for an
INPUT**: philosophy §3 offers four resolutions — re-route, a station, a designed crossing, or
not serving that plot — and *silent deletion of the corridor* is none of them. On a line we are
not permitted to re-route, the only honest resolutions are a designed crossing (H1a) or an RFI
to the client.

Restoring every H1 removal takes the corridor network from 771 to 560 components, so H1
accounts for **211** of the 771 and the 4 m hole for most of the rest.

---

## 5. The two candidate fixes, weighed on evidence

### (i) Stage 3 designs ON the corridor graph — **reject**

The corridor graph does not contain the trunk. It contains a copy that is **80.5 km against the
drawing's 85.5 km, in 58 pieces against 3**, with 8.91 km of holes up to 935 m long, of which
9.5 km was deleted for running along a wadi and 1.0 km for running along a dual carriageway.
Stage 3 would inherit all of it and have nothing legitimate to do about it — closing a 935 m
hole in a client alignment *is* re-routing it. This option makes the one line where
fragmentation is fatal depend on the treatment that fragments it.

### (ii) Stage 4 snaps the trunk into the corridor node set — **reject as posed**

There is nothing to snap to. 3.2 % of stage 3's chambers are within 0.5 m of a corridor node
and 6.9 % within the 3 m merge radius; the median offset is **42.4 m** and the maximum
**379 m**. A snap tolerance large enough to catch the median would move the client's alignment
by tens to hundreds of metres. Rejected on the same grounds as (i): it moves an input.

### (iii) Stage 4 **welds** the trunk in — **recommended**

Put stage 3's trunk into the graph as *edges of its own*, and cut the corridors it crosses at
the crossing point. This is not a new idea in this codebase — `build_graph` (the fallback path)
already does exactly this, and says why:

> *"The trunk goes into the SAME union as the corridors so it is noded WITH them. Noding it
> separately and snapping afterwards is how a trunk ends up 1.0 m from the network that is
> supposed to drain into it."*

The defect is that `adopt_graph` — the **preferred** path, written to honour contract P3 and
not re-derive stage 2's published topology — threw the baby out with the bathwater and demoted
the trunk to a mask.

**What moves.** The trunk's own vertices do not: a planar union splits lines, it does not move
them. What can move is a **chamber**, by up to the 3.0 m merge radius stage 2 already applies
to its own endpoints, when a trunk chamber and a corridor node are closer than the chamber
clearance and philosophy §4 therefore makes them **one structure**. Measured on the real data:
**73 of 758 trunk chambers merge onto an existing corridor node, worst move 2.86 m**; worst
move over all welded endpoints **2.942 m**. The patch asserts this stays under
`NODE_MERGE_M` and publishes the worst case. *No pipe moves. The alignment is not re-routed.*

**Verified result** (running the exact code in §6 against the published layers):

```
before: 24,963 edges, 771 components
  welded stage 3's trunk in: 814 corridors (102.67 km) re-noded with 754 trunk lines
  (85.55 km) -> 3,964 segments
    1,691 new chambers, worst chamber move 2.942 m (merge radius 3.0 m);
    85 shadow edges, 5.80 km, removed so the spine is a tree
    TRUNK now 86.11 km in 4 piece(s) against stage 3's 85.55 km
after : 27,002 edges, 739 components
    on-trunk 1,472.4 km   OFF-trunk 788.2 km   (today 1,429.8 / 788.9)
```

**4 pieces — exactly what stage 3 designed**, and 86.11 km against 85.55 km (+0.65 %, inside
the 1 % tolerance the patch asserts). The 5.80 km of "shadow" removed is stage 2's own copy of
the alignment lying a few centimetres off stage 3's; it shows up as **85 independent cycles in
the trunk subgraph**, and a spine must be a tree, so the longest edge of each cycle goes.

---

## 6. The patches, in priority order

### PATCH 1 — `s2_corridors.py`: heal the 4 m cut hole *(do this first)*

**Payoff: 771 → 317 systems, off-trunk 788.9 → 287.5 km, from 746 connectors under 4 m each.**

Replace lines 1207-1218 (the `auto_road` loop) with:

```python
    # what the draftsman already covers comes out of the treated set
    draft_cover = unary_union(list(draft.geometry.buffer(CORRIDOR_MATCH_M)))
    draft_cut = unary_union(list(draft.geometry.buffer(CORRIDOR_CUT_M)))
    draft_geom = unary_union(list(draft.geometry))     # the LINES, not the buffer
    auto_road: List[LineString] = []
    n_heal, heal_m = 0, 0.0
    for g in treated:
        if g.intersection(draft_cover).length > 0.75 * g.length:
            continue
        rest = g.difference(draft_cut)
        if rest.is_empty:
            continue
        for p in (rest.geoms if rest.geom_type == "MultiLineString" else [rest]):
            if p.length <= AUTO_ROAD_MIN_M:
                continue
            auto_road.append(p)
            # HEAL THE CUT. `difference` deletes the metres inside the buffer and leaves the
            # stub ending CORRIDOR_CUT_M short of the drafted line it was cut against - a
            # 4.0 m hole that nothing closes, because contract.NODE_MERGE_M is 3.0 m and the
            # stitch step only stitches skeleton pockets. This is the same defect as W10's
            # 25 m hole (line 211), narrowed and not closed.
            # MEASURED 2026-09-02: those holes hold the published corridor network in 771
            # pieces. Joining every endpoint to a line within 3.0 m leaves 764; within 4.0 m
            # gives 444; within 4.5 m gives 299 - a step function at exactly CORRIDOR_CUT_M.
            # On the PRE-exclusion set the same test goes 560 -> 70. 746 connectors of 4 m or
            # less lift the network that reaches the trunk from 1,430 km to 1,931 km.
            # The connector is drawn on the REAL geometry with nearest_points, so it lands ON
            # the drafted line and the planar noding in `node_and_attribute` makes a node of
            # it - the same rule the stitch step already asserts to 0.0000 m.
            for end in (Point(p.coords[0]), Point(p.coords[-1])):
                d = float(end.distance(draft_geom))
                if 0.0 < d <= CORRIDOR_CUT_M + 0.05:
                    auto_road.append(LineString([end, nearest_points(end, draft_geom)[1]]))
                    n_heal += 1
                    heal_m += d
    res["metrics"]["cut_holes_healed"] = n_heal
    res["metrics"]["cut_holes_healed_km"] = round(heal_m / 1000.0, 4)
    print(f"      healed {n_heal:,} cut holes with {heal_m/1000:.3f} km of connector - the "
          f"{CORRIDOR_CUT_M:.1f} m gap `difference` leaves is wider than the "
          f"{contract.NODE_MERGE_M:.1f} m merge radius, so nothing else closes it")
```

`Point`, `LineString`, `nearest_points` and `unary_union` are already imported (lines 154-155);
`res` is in scope. No other change is needed — the connectors enter the existing
`node_and_attribute` planar noding with `SRC = 'auto_road'` like their parent.

**Two things to check after running it**, because both are legitimate and neither is currently
measured: (1) the `component_count` printed *before* the exclusion should fall from 509-560 to
roughly 70; (2) `stitch` will find far fewer islands, because many pockets were islands only
because of these holes.

### PATCH 2 — `s4_hierarchy.py`: weld the trunk in *(OPEN-S4-1 proper)*

**2a. Constants.** Replace the `TRUNK_ON_M` block (lines 171-175):

```python
# --- geometric tolerances. NOT design values. -----------------------------------------
TRUNK_ON_M = 0.5             # W10's NODE_SNAP_M. Still used by `build_graph`, the FALLBACK
                             # path, where the corridors and the trunk have already been
                             # planar-noded together and a midpoint probe is therefore asking
                             # a question that has an answer. On the adopted path it asked the
                             # question of an un-noded corridor and got 74 trunk pieces out of
                             # a 4-piece trunk - see `weld_trunk` and OPEN-S4-1.
TRUNK_WELD_M = 0.05          # the drawing tolerance at which stage 3's alignment and a stage 2
                             # corridor are THE SAME LINE. 50 mm is the coordinate agreement of
                             # the two layers, not a design distance: nothing is served or not
                             # served by it, and nothing is moved by it.
MIN_SEG_M = 1e-6             # a zero-length artefact of the noding, not a pipe.
```

**2b. Add `weld_trunk`,** immediately after `adopt_graph` (i.e. before `build_graph`, line 395).
This is the code that was run to produce the §5 result, verbatim:

```python
def weld_trunk(G, idx, trunk, rec):
    """Stage 3's trunk, WELDED INTO stage 2's corridor graph as edges of its own.

    THE DEFECT THIS FIXES (OPEN-S4-1). Until now the trunk was never in this graph. It was a
    0.5 m proximity MASK over stage 2's corridors: a corridor whose midpoint fell within
    TRUNK_ON_M of the alignment was called `trunk`, so the trunk arrived in as many pieces as
    stage 2's COPY of it - 74, against the 4 stage 3 designed and the 3 in the user's drawing.
    Measured 2026-09-02: the mask choice accounts for 8 of those 74 (the same corridors tagged
    SRC='main_pipe' give 65); the other 65 are stage 2's. And the pieces cannot be rejoined
    through the corridor graph either - 35 of them are mutually unreachable.

    THE METHOD. The trunk lines and ONLY the corridors they touch go into one planar union,
    exactly as `build_graph` already does for the fallback path - "noding it separately and
    snapping afterwards is how a trunk ends up 1.0 m from the network that is supposed to
    drain into it". A corridor is CUT at the trunk and the cut becomes a node in both. Nothing
    else is re-derived: 814 of 24,963 corridors are re-noded and the other 24,149 keep the
    US_NODE / DS_NODE stage 2 wrote, so contract P3 still holds for 96.7 % of the layer.

    WHAT MOVES. The trunk's own vertices do not - a planar union splits lines, it does not
    move them. What can move is a CHAMBER, by up to the 3.0 m merge radius stage 2 itself
    applies, where a trunk chamber and a corridor node are closer than the chamber clearance
    and philosophy sec 4 therefore makes them ONE structure. Measured: 73 of 758 trunk
    chambers merge onto an existing corridor node, worst move 2.86 m; worst over all welded
    endpoints 2.942 m. The move is asserted below the merge radius and published. NO PIPE
    MOVES: the client's alignment is not re-routed, and a 2.9 m chamber move at a street
    junction is the merge rule doing what it exists to do.
    """
    from shapely.strtree import STRtree

    t_lines, t_attr = [], []
    for r in trunk.itertuples():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        for p in (g.geoms if g.geom_type.startswith("Multi") else [g]):
            t_lines.append(p)
            t_attr.append(r)
    if not t_lines:
        rec.note("stage 3 published no trunk geometry - nothing welded")
        return
    t_km_in = sum(g.length for g in t_lines) / 1000.0

    # 1. stage 3's chambers enter the node index FIRST, so a corridor split point lands on a
    #    DESIGNED chamber rather than the reverse.
    n0_nodes, reuse_max = len(idx.nodes), 0.0
    for g in t_lines:
        c = list(g.coords)
        for x, y in (c[0], c[-1]):
            uid = idx.get_or_create(float(x), float(y))
            nd = idx.nodes[uid]
            reuse_max = max(reuse_max, float(np.hypot(nd.x - x, nd.y - y)))
    if reuse_max > NODE_MERGE_M:
        raise contract.ContractError(
            f"a trunk chamber moved {reuse_max:.2f} m onto a corridor node, past the "
            f"{NODE_MERGE_M:.1f} m merge radius. The trunk is a client INPUT.")

    # 2. the corridors the trunk actually touches - and only those
    ekeys = list(G.edges())
    egeom = [G[a][b]["geom"] for a, b in ekeys]
    emeta = [G[a][b]["meta"] for a, b in ekeys]
    live = [i for i, g in enumerate(egeom) if g is not None and not g.is_empty]
    tree = STRtree([egeom[i] for i in live])
    touched = set()
    for t in t_lines:
        for j in tree.query(t.buffer(TRUNK_WELD_M)):
            i = live[int(j)]
            if egeom[i].distance(t) <= TRUNK_WELD_M:
                touched.add(i)
    order = sorted(touched)
    plines = [egeom[i] for i in order]
    pmeta = [emeta[i] for i in order]
    p_km = sum(g.length for g in plines) / 1000.0
    for i in order:
        a, b = ekeys[i]
        if G.has_edge(a, b):
            G.remove_edge(a, b)

    # 3. ONE planar union - the trunk and its neighbours noded together, never separately
    noded = unary_union(plines + t_lines)
    segs = [s for s in (noded.geoms if noded.geom_type.startswith("Multi") else [noded])
            if s.length > MIN_SEG_M]
    ptree = STRtree(plines) if plines else None
    ttree = STRtree(t_lines)
    tbuf = unary_union(t_lines).buffer(TRUNK_WELD_M)
    mids = [s.interpolate(0.5, normalized=True) for s in segs]
    pnear = np.asarray(ptree.nearest(mids)).reshape(-1) if ptree else None
    tnear = np.asarray(ttree.nearest(mids)).reshape(-1)

    fun = rec.funnel("trunk weld: corridor + trunk lines -> welded edges", len(segs))
    n_self, self_m, n_par, par_m, move = 0, 0.0, 0, 0.0, 0.0
    for i, s in enumerate(segs):
        c = list(s.coords)
        u = idx.get_or_create(c[0][0], c[0][1])
        v = idx.get_or_create(c[-1][0], c[-1][1])
        nu, nv = idx.nodes[u], idx.nodes[v]
        move = max(move, float(np.hypot(c[0][0] - nu.x, c[0][1] - nu.y)),
                   float(np.hypot(c[-1][0] - nv.x, c[-1][1] - nv.y)))
        if u == v:
            n_self += 1
            self_m += s.length
            continue
        # CONTAINMENT, not a midpoint probe. A midpoint probe on a noded set flagged 128 km
        # of "trunk" against an 85.5 km alignment, because after noding a segment is short
        # enough for any parallel corridor to sit inside the tolerance.
        is_tr = bool(tbuf.covers(s))
        if is_tr:
            t = t_attr[int(tnear[i])]
            # H1 flags come from STAGE 3's own exposure figures, not zeroed. Project rule 7 is
            # explicit that no pipe of any kind runs along a dual carriageway, trunk included,
            # and stage 3 measured 534.7 m of ON_DUAL_M and 11.03 km of ON_WADI_M on this
            # alignment. Clearing them here would hide the evidence on the reaches where a
            # late H1 discovery is most expensive.
            meta = dict(SRC="main_pipe", CORR_ID="", QFLAG="", CONF="drafted",
                        DUAL_WARN=int(float(getattr(t, "ON_DUAL_M", 0) or 0) > 0),
                        WADI_WARN=int(float(getattr(t, "ON_WADI_M", 0) or 0) > 0))
        else:
            meta = dict(pmeta[int(pnear[i])])       # the parent corridor's provenance, P6
        if G.has_edge(u, v):
            if G[u][v]["trunk"] or (not is_tr and G[u][v]["length"] <= s.length):
                n_par += 1
                par_m += s.length
                continue
            n_par += 1
            par_m += G[u][v]["length"]
        G.add_edge(u, v, length=float(s.length), geom=s, trunk=is_tr, meta=meta)
    fun.drop(f"welded segment whose two ends fall in one {NODE_MERGE_M:.0f} m chamber "
             f"({self_m / 1000:.3f} km)", n=n_self)
    fun.drop(f"parallel welded segment between the same two chambers "
             f"({par_m / 1000:.3f} km)", n=n_par)
    fun.close(len(segs) - n_self - n_par)

    # 4. THE SPINE IS A TREE. Stage 2 publishes its own copy of the alignment a few
    #    centimetres off stage 3's, so the weld leaves a shadow beside the trunk. It shows up
    #    as a cycle in the trunk subgraph - a spine cannot have one - and the longest edge of
    #    each cycle is the shadow. Measured: 85 cycles, 5.80 km.
    Gt = nx.Graph([(a, b, d) for a, b, d in G.edges(data=True) if d["trunk"]])
    n_shadow, shadow_m = 0, 0.0
    while True:
        try:
            cyc = nx.find_cycle(Gt)
        except nx.NetworkXNoCycle:
            break
        a, b = max(((e[0], e[1]) for e in cyc), key=lambda e: Gt[e[0]][e[1]]["length"])
        shadow_m += Gt[a][b]["length"]
        n_shadow += 1
        Gt.remove_edge(a, b)
        G.remove_edge(a, b)

    t_km_out = sum(d["length"] for *_, d in G.edges(data=True) if d["trunk"]) / 1000.0
    pieces = nx.number_connected_components(Gt) if len(Gt) else 0
    rec.metric("weld_corridors_renoded", len(order))
    rec.metric("weld_segments", len(segs))
    rec.metric("weld_new_nodes", len(idx.nodes) - n0_nodes)
    rec.metric("weld_chamber_move_max_m", round(max(move, reuse_max), 3))
    rec.metric("weld_shadow_km", round(shadow_m / 1000, 3))
    rec.metric("trunk_km_welded", round(t_km_out, 2))
    rec.metric("trunk_km_stage3", round(t_km_in, 2))
    _say(f"  welded stage 3's trunk in: {len(order):,} corridors ({p_km:.2f} km) re-noded "
         f"with {len(t_lines):,} trunk lines ({t_km_in:.2f} km) -> {len(segs):,} segments")
    _say(f"    {len(idx.nodes) - n0_nodes:,} new chambers, worst chamber move "
         f"{max(move, reuse_max):.3f} m (merge radius {NODE_MERGE_M:.1f} m); "
         f"{n_shadow} shadow edges, {shadow_m / 1000:.2f} km, removed so the spine is a tree")
    _say(f"    TRUNK now {t_km_out:.2f} km in {pieces} piece(s) against stage 3's "
         f"{t_km_in:.2f} km")
    if abs(t_km_out - t_km_in) > 0.01 * t_km_in:
        rec.note(f"the welded trunk is {t_km_out:.2f} km against stage 3's {t_km_in:.2f} km "
                 f"({100 * (t_km_out - t_km_in) / t_km_in:+.1f} %). Stage 2 publishes its own "
                 "copy of the alignment a few centimetres off stage 3's; the two are welded "
                 "as one spine and the excess is reported, not laundered.")
```

**2c. The funnel has to be re-based**, because the trunk is a second INPUT and cannot live in a
funnel whose n0 is `len(corr)`. Three small edits:

*In `adopt_graph`, replace the last four lines (389-393), ending `return G, idx, fun`:*

```python
    # nodes stage 2 published but no surviving corridor uses
    for u in [u for u in list(idx.nodes) if u not in G]:
        idx.nodes.pop(u, None)
    fun.close(G.number_of_edges())
    return G, idx
```

*In `build_graph`, replace the final `return` (line 490, `return G, idx, fun, trunk_u`), after
the two `fun.drop` calls and the metrics:*

```python
    fun.close(G.number_of_edges())
    return G, idx, trunk_u
```

*In `main()`, replace lines 1035-1047:*

```python
        _say("[1] corridor graph")
        has_topo = ({"US_NODE", "DS_NODE"} <= set(corr.columns)
                    and not corr[["US_NODE", "DS_NODE"]].isna().any().any())
        if has_topo:
            if trunk_how == "in_corridors":
                # the trunk IS a subset of the corridors here and is matched by IDENTITY,
                # not by a tolerance. Nothing to weld.
                trunk_ids = set(trunk.CORR_ID.astype(str)) if "CORR_ID" in trunk.columns \
                    else set()

                def trunk_where(r, g, _ids=trunk_ids):
                    return str(getattr(r, "CORR_ID", "")) in _ids

                G, idx = adopt_graph(corr, corr_nodes, trunk_where, rec)
            else:
                # stage 3's trunk (or the user's drawing) is a SEPARATE layer with its own
                # chambers. It is WELDED in, never matched by proximity - OPEN-S4-1.
                G, idx = adopt_graph(corr, corr_nodes, lambda r, g: False, rec)
                weld_trunk(G, idx, trunk, rec)
        else:
            G, idx, _ = build_graph(corr, trunk, rec)
        # the trunk is a second input, so the tiering funnel starts at the GRAPH, not at the
        # corridor count - a funnel that starts upstream of an addition cannot close.
        fun = rec.funnel("graph edges -> tiered reaches", G.number_of_edges())
```

`build_tree` already sets `trunk_pieces` from the trunk subgraph, so that metric now reports 4
without further change.

### PATCH 3 — consistency, `build_graph` (optional, one line)

The fallback path uses the same midpoint probe and over-selects for the same reason: measured
on a planar-noded set, `midpoint < 0.5 m` flags **128.5 km** as trunk against an 85.5 km
alignment and yields 11 pieces, while `tbuf.covers(s)` flags 93.6 km and yields **4**. Build
the buffer once, beside `trunk_u = unary_union(trunk_lines)`:

```python
    trunk_u = unary_union(trunk_lines)
    trunk_buf = trunk_u.buffer(TRUNK_WELD_M)      # built ONCE, not per segment
```

and change the per-segment test (line 447) from

```python
        is_tr = trunk_u.distance(mids[i]) < TRUNK_ON_M
```
to
```python
        is_tr = trunk_buf.covers(s)
```

---

## 7. What the fix recovers

Corridor-graph measurements, and the published-layer estimate using this run's own ratio
(788.9 km of off-trunk corridor published as 729.3 km of off-trunk reach, 0.925):

| | corridor systems | trunk pieces | on-trunk km | off-trunk km | ⇒ published systems | ⇒ published off-trunk km |
|---|---|---|---|---|---|---|
| **today** | 771 | 74 | 1,429.8 | 788.9 | **773** | **729.3** |
| PATCH 2 only (stage 4 weld) | 739 | **4** | 1,472.4 | 788.2 | ~741 | ~729 |
| PATCH 1 only (stage 2 heal) | 317 | 74 | 1,931.2 | 287.5 | ~319 | ~266 |
| **PATCH 1 + PATCH 2** | **289** | **4** | **1,976.1** | **287.4** | **~291** | **~266** |

**Expect to recover about 463 km of the 729 km and about 482 of the 773 systems — and roughly
all of it comes from PATCH 1.** PATCH 2 recovers 32 systems and under 1 km, but it is the one
that clears the **H15 breach**: 810 roots over 771 components becomes one root per component,
the 39 detached trunk legs stop being their own outfalls, and 43 km of network stops draining
to a provisional outfall 100 m from a trunk it could not see.

Do **not** expect one network. ~289 systems is the honest floor for this corridor set as it
stands, and the remaining ~266 km genuinely reaches no trunk — that is now a real satellite /
on-site question for the options appraisal (philosophy §8a), not an artefact. Two things would
move it further, and neither belongs in this ticket:

- restoring the H1-severed corridor **properly** — i.e. resolving each severance by one of
  philosophy §3's four routes rather than by deletion — is worth another ~219 systems and
  ~215 km. Measured two ways: restoring every removal on its own takes 771 → 560 components;
  restoring it *and* closing the cut holes *and* welding the trunk gives **70 systems and
  72.6 km off-trunk**. That last figure is an upper bound obtained with a blanket 4.5 m
  endpoint join rather than the targeted PATCH 1 connector, so treat it as the ceiling, not
  the forecast;
- the `stitch` step will behave differently once PATCH 1 lands, because many "islands" were
  islands only because of the 4 m holes.

---

## 8. Two further defects found on the way

**OPEN-S4-2 — NODE_UID collision across published layers.** `corridor_nodes`,
`W11a_trunk.gpkg/nodes` and `W11a.gpkg/nodes` each mint `N0000001…` from 1, so **758 UID
strings name different points in different layers**, up to 34.5 km apart. Contract H16 says
topology is written down rather than inferred; a written id that is not unique across the
deliverable is worse than none, because a join on it silently succeeds. Fix: a per-stage or
per-layer prefix (`C…`, `T…`, `N…`) in `NODE_UID_FMT`, decided once in `contract.py`.

**OPEN-S2-2 — stage 2 publishes a second copy of the trunk.** 566 corridors / 77.5 km carry
`SRC='main_pipe'`, of which only 17.8 km lie within 50 mm of stage 3's alignment; the rest are
the same line displaced by stage 2's endpoint snap. It is what produces the 85 shadow cycles
PATCH 2 has to remove. Once stage 3 owns the trunk, stage 2 should either publish the alignment
**unmodified** or not publish it at all. Deleting it in stage 4 instead was tested and is worse:
the trunk length comes out exact (85.53 km) but the components jump from 739 to 1,067, because
neighbours noded onto stage 2's copy lose their connection.

---

## 9. Method and reproduction

All measurements were made on the layers as published on 2026-09-02 (`W11a.gpkg` 12:56,
`W11a_trunk.gpkg` 11:56, `W11a_s4.gpkg` 12:08), by rebuilding `adopt_graph` exactly and
checking it reproduces the run's own metrics before drawing any conclusion:

| reproduced | measured here | `manifest_s4.json` |
|---|---|---|
| graph nodes | 23,342 | 23,342 |
| corridor components | 771 | 771 |
| trunk pieces | 74 | 74 |
| outfalls | 810 (736 + 74) | 810 |
| published off-trunk km | 729.3 | 729.3 (`s4_reaches`, `ON_TRUNK = 0`) |

Scripts are in the session scratchpad, not the repo; each is short enough to re-derive:
`m2` (reproduce the graph and the 74 pieces) · `m3` (gaps between trunk pieces) · `m4` (mask vs
`SRC` tag) · `m5`/`m9` (component sizes and distance to the alignment) · `m7` (chamber-to-node
distances) · `m8` (alignment coverage and removals by reason) · `m10`/`m18` (fragmentation
before and after H1, and the 4 m step function) · `m19` (the exact PATCH 1 simulation) ·
`verify_patch.py` (PATCH 2, verbatim, against the real layers).

**Guideline citations used:** H1/H1a wadi and dual-carriageway exclusions (G203-p30 §4.4.1,
p33; G201-p85-86 §9.3; G203-p52 §8.2.4); H15 forest/one-outfall and H16 written topology are
project rules, not guideline numbers, and are cited as such. `CORRIDOR_CUT_M`, `NODE_MERGE_M`,
`TRUNK_ON_M` and the proposed `TRUNK_WELD_M` are all **geometric tolerances, not design
values** — none of them decides whether a plot is served or a pipe is legal.
