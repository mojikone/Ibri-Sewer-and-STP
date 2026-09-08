"""Stage A of the W13 design logic on the built area: rules 1 to 5 as a tree.

    python run_stage_a.py

Phase 1, the ground (rules 1 and 2): the draftsman's DXF inside the ground the 2006 network
serves, the terrain along every street, every run pointed downhill, crests and sags split,
the arrows followed to the outlets, shallow hollows filled. Written as W13_A_ground.*.

Phase 2, the tree (rules 3 to 5, agreed 2026-09-07): joins spaced as NAMA spaces them,
sub-mains as the heaviest low stem of each catchment, laterals routed to them by the
least-depth search, every leftover street a branch with its head at the first gate, connectors
drawn, catchments from the tree. Written as W13_A_tree.*. This is the drawing to look at.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import geopandas as gpd                                              # noqa: E402
from shapely.geometry import Point, LineString                                   # noqa: E402
from shapely.ops import unary_union
from shapely.strtree import STRtree                                  # noqa: E402

import config_built as cfg                                           # noqa: E402
from sewnet import ground as G                                       # noqa: E402
from sewnet import outlets as O                                      # noqa: E402
from sewnet import skeleton as K                                     # noqa: E402
from sewnet import streams as S                                      # noqa: E402
from sewnet import export_stage_a as X                               # noqa: E402
from sewnet import export_tree as XT                                 # noqa: E402

T0 = time.time()
SCRATCH = os.path.join(cfg.OUT_RUN, "scratch")
EAST = (449400, 2566900, 452100, 2571000)
WEST = (444700, 2565700, 446900, 2567800)


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def km_by(items, field, values):
    return {v: round(sum(r["len"] for r in items if r.get(field) == v) / 1000, 1) for v in values}


def main():
    for d in (cfg.OUT_SHP, cfg.OUT_DXF, cfg.OUT_IMG, cfg.OUT_RUN, SCRATCH):
        os.makedirs(d, exist_ok=True)
    rep = {}
    date = time.strftime("%Y-%m-%d")

    # ------------------------------------------------------------ phase 1: the ground
    log("area: the ground the built 2006 network serves ...")
    envelope, built = G.built_envelope(cfg.BUILT_SEWER, cfg.AREA_BUFFER_M)
    built_geoms = list(built.geometry)
    rep["built_km"] = round(float(built.geometry.length.sum()) / 1000, 1)
    if getattr(cfg, "AREA_SHP", None):
        # the engineer's boundary is the area; the built envelope stays as the comparison
        envelope = unary_union([g for g in gpd.read_file(cfg.AREA_SHP).geometry
                                if g is not None and not g.is_empty])
        rep["area_source"] = os.path.basename(cfg.AREA_SHP)
        log(f"   area from {rep['area_source']}: {envelope.area / 1e6:.2f} km2")
    else:
        rep["area_source"] = "built envelope"
    rep["area_km2"] = round(envelope.area / 1e6, 2)

    log("streets: the draftsman's DXF, clipped, snapped, noded ...")
    lines = G.clip_lines(G.read_dxf_lines(cfg.ROADS_DXF, cfg.ROAD_LAYERS), envelope)
    if getattr(cfg, "NAMA_ROW_M", 0):
        # the last stretch into the works may leave the road for NAMA's trunk alignment
        near_stp = Point(cfg.STP).buffer(cfg.NAMA_ROW_M)
        tm = built[built["US_MHID"].astype(str).str.contains("-TM-")]
        row = []
        for g in tm.geometry:
            if g is None or g.is_empty or not g.intersects(near_stp):
                continue
            c = g.intersection(near_stp)
            parts = [c] if c.geom_type == "LineString" else \
                [q for q in getattr(c, "geoms", []) if q.geom_type == "LineString"]
            row += [(LineString([(x, y) for x, y, *_ in q.coords]), "nama-row")
                    for q in parts if q.length > 0.5]          # the as-built carries a Z
        row = G.clip_lines(row, envelope)
        lines += row
        rep["nama_row_km"] = round(sum(g.length for g, _ in row) / 1000, 2)
        log(f"   NAMA's right-of-way into the works: {rep['nama_row_km']} km of line added")
    noded, snapped, srep = G.snap_and_node(lines, cfg.SNAP_M)
    rep["street_km_in_area"] = round(sum(g.length for g, _ in lines) / 1000, 1)
    rep["snap"] = srep

    log("ground: terrain at %.0f m over the area and both targets ..." % cfg.GROUND_RES_M)
    # the main pipe is 85 km across the wilayat; only its part near the area matters here
    mp0 = gpd.read_file(cfg.MAIN_PIPE)
    near_area = envelope.convex_hull.buffer(500.0)
    mp0 = mp0[mp0.geometry.intersects(near_area)].copy()
    mp0["geometry"] = mp0.geometry.intersection(near_area)
    mp0 = mp0[~mp0.geometry.is_empty]
    l, b, r, t = envelope.bounds
    ml, mb, mr, mt = mp0.total_bounds if len(mp0) else (l, b, r, t)
    ground = G.Ground(cfg.TERRAIN, (min(l, ml, cfg.STP[0]), min(b, mb, cfg.STP[1]),
                                    max(r, mr, cfg.STP[0]), max(t, mt, cfg.STP[1])),
                      cfg.GROUND_RES_M)

    log("runs: junction to junction, split at crests and sags ...")
    runs0, _ = G.build_runs(noded)
    runs1, new_nodes = G.split_at_extrema(ground, runs0, cfg.CREST_M, cfg.MIN_SPLIT_M,
                                          cfg.PROFILE_STEP_M)
    kinds = dict(new_nodes)
    node_keys = {n for a, b, _, _ in runs1 for n in (a, b)}
    znode = {n: ground.z_node(n[0], n[1]) for n in node_keys}
    runs = G.tag_layers(G.orient(runs1, znode, cfg.FLAT_PCT, cfg.LEVEL_M), snapped)
    rep["runs"] = len(runs)
    rep["run_km"] = round(sum(r["len"] for r in runs) / 1000, 1)
    rep["splits"] = {"crest": sum(1 for _, k in new_nodes if k == "crest"),
                     "sag": sum(1 for _, k in new_nodes if k == "sag")}
    log(f"   {len(runs)} runs, {rep['run_km']} km; splits {rep['splits']}")

    log("outlets on the raw ground, hollows filled ...")
    mp = mp0
    main_pipe = [p for g in mp.geometry if g is not None and not g.is_empty
                 for p in (g.geoms if hasattr(g, "geoms") else [g])]
    rep["main_pipe_km_near_area"] = round(sum(p.length for p in main_pipe) / 1000, 1)
    mp_union = unary_union(main_pipe)
    targets = O.find_targets({n: n for n in node_keys}, main_pipe, cfg.STP, cfg.TARGET_M,
                             cfg.STP_M)
    ptr = O.pointers(runs, targets)
    raw_term = O.terminals(node_keys, ptr, targets)
    raw_sinks = {t for t in set(raw_term.values()) if t not in targets}
    # the outlet of every node (rule 5's cost, or the flood: config ASSIGN_BY_DEPTH)
    assign = ({"depth_weight": cfg.DEPTH_WEIGHT, "smin": cfg.SMIN_PROXY}
              if getattr(cfg, "ASSIGN_BY_DEPTH", False) else {})
    src, filled, parent, seq, spill, iters = O.resolve_outlets(runs, znode, targets,
                                                                cfg.HOLLOW_M, raw_term)
    runs = O.flood_direction(runs, parent, filled, seq, cfg.FLAT_PCT, cfg.LEVEL_M)
    run_catch, info = O.catchments(runs, src, targets, spill)
    rep["ground_catchments"] = {"count": len(info),
                                "by_type": {t: sum(1 for i in info.values() if i["type"] == t)
                                            for t in ("JOIN", "STP", "SINK", "LOW")}}
    log(f"   {rep['ground_catchments']}")

    log("guide picture: terrain streams and wadi ground ...")
    try:
        streams, srep2 = S.derive_streams(cfg.TERRAIN, envelope.bounds, cfg.STREAM_RES_M,
                                          cfg.STREAM_THRESHOLD_CELLS, SCRATCH, cfg.STREAM_PAD_M)
        env_pad = envelope.buffer(300)
        streams = [(p, o) for g, o in streams if g.intersects(env_pad)
                   for p in (lambda c: c.geoms if hasattr(c, "geoms") else [c])(g.intersection(env_pad))
                   if p.geom_type == "LineString"]
        rep["streams"] = srep2
    except Exception as e:
        streams, rep["streams"] = [], {"error": str(e)}
    try:
        l, b, r, t = envelope.bounds
        env100 = envelope.buffer(100)
        wadis = [w.intersection(env100) for w in
                 S.wadi_polygons(cfg.HAZARD, (l - 100, b - 100, r + 100, t + 100))
                 if w.intersects(env100)]
    except Exception as e:
        wadis = []
        rep["wadi_error"] = str(e)

    # the ground drawing, kept for reference
    polys = O.catchment_polygons(runs, run_catch, envelope)
    colour = O.colour_catchments(polys)
    deg, node_catch = {}, {}
    for r, c in zip(runs, run_catch):
        for n in (r["up"], r["dn"]):
            deg[n] = deg.get(n, 0) + 1
            node_catch.setdefault(n, c)
    outlet_nodes = {i["outlet"]: (cid, i["type"]) for cid, i in info.items()}
    nodes = []
    for k, n in enumerate(sorted(node_keys)):
        d = deg.get(n, 0)
        cid, typ = outlet_nodes.get(n, (node_catch.get(n, ""), ""))
        nodes.append({"key": n, "id": f"N{k + 1:05d}", "x": n[0], "y": n[1], "z": znode[n],
                      "degree": d, "kind": kinds.get(n, "head" if d == 1 else "junction"),
                      "catch": cid, "is_outlet": n in outlet_nodes, "out_type": typ})
    X.write_dxf(os.path.join(cfg.OUT_DXF, "W13_A_ground.dxf"), runs, run_catch, info, polys,
                colour, nodes, streams, wadis, main_pipe, built_geoms, envelope, cfg.STP,
                [f"W13 STAGE A - THE GROUND READ ALONG THE STREETS (reference) - {date}",
                 "arrows = the ground's fall · this is NOT the network; see W13_A_tree.dxf"])
    X.write_shapes(cfg.OUT_SHP, "W13_A", runs, run_catch, info, polys, nodes, streams, cfg.EPSG)

    # ------------------------------------------------------------ phase 2: the tree
    log("joins: only sub-mains join, spaced as NAMA spaces them ...")
    kept, dropped_joins = K.select_joins(info, cfg.JOIN_SPACING_M)
    restored = []
    for _ in range(5):
        targets2 = {info[c]["outlet"]: "JOIN" for c in kept}
        targets2.update({n: "STP" for n, t in targets.items() if t == "STP"})
        src2, filled2, parent2, seq2, spill2, iters2 = O.resolve_outlets(
            runs, znode, targets2, cfg.HOLLOW_M, raw_term, **assign)
        back = K.restore_stranded_joins(info, kept, dropped_joins, src2, spill2)
        if not back:
            break
        kept += back
        dropped_joins = [c for c in dropped_joins if c not in back]
        restored += back
    rep["joins"] = {"candidates": len([c for c in info.values() if c["type"] == "JOIN"]),
                    "kept": len(kept), "dropped_into_a_neighbour": len(dropped_joins),
                    "restored_stranded": len(restored)}
    log(f"   {rep['joins']}")

    log("direct links (rule 3): a basin whose ground reaches the main pipe's invert, the STP, "
        "or NAMA's trunk corridor to the STP, with no plot in the way ...")
    gates = K.Gates(cfg.PLOTS_CLASS, envelope, cfg.GATE_SEARCH_M, cfg.LINK_PLOT_PAD_M)
    streets = K.Streets(runs)
    use_corridor = getattr(cfg, "USE_CORRIDOR", True)
    corridor_paths = {}
    if use_corridor:
        corridor = K.TrunkCorridor(built, cfg.STP, envelope=envelope)
        rep["corridor"] = {"lines": len(corridor.lines), "reaches_stp": corridor.ok,
                           "ends_tied_to_stp": corridor.tied_ends}
        # the corridor is a second target: its entry joins are chosen like joins on the main pipe
        entries, corridor_paths = K.corridor_entry_targets(
            node_keys, znode, ground, corridor, streets, cfg.LINK_MP_MAX_M, cfg.JOIN_SPACING_M,
            cfg.CORRIDOR_MIN_GRAD, cfg.CORRIDOR_MAX_M, mp_union=mp_union, plots=gates,
            stp_level=cfg.STP_INVERT_M)
        entries = {n: t for n, t in entries.items() if n not in targets2}
        targets2.update(entries)
        rep["corridor"]["entry_joins"] = len(entries)
        log(f"   corridor entry joins: {len(entries)}")
    else:
        corridor = None
        rep["corridor"] = {"used": False}
    links = {}
    # 1. every basin deeper than HOLLOW_M is offered a direct link first: to the main pipe's
    #    invert, or along NAMA's corridor to the STP. Gravity with no extra depth beats
    #    climbing out of a basin (rule 5's least-depth logic; NAMA sent the west to the STP)
    for _ in range(8):
        src2, filled2, parent2, seq2, spill2, iters2 = O.resolve_outlets(
            runs, znode, targets2, cfg.HOLLOW_M, raw_term, **assign)
        new = K.link_targets(set(src2.values()), spill2, znode, ground, mp_union, cfg.STP,
                             cfg.LINK_MIN_GRAD, cfg.MP_INVERT_DEPTH_M, cfg.LINK_MAX_M, gates,
                             existing=list(targets2), spacing_m=cfg.JOIN_SPACING_M,
                             streets=streets, mp_max_len=cfg.LINK_MP_MAX_M,
                             stp_level=cfg.STP_INVERT_M)
        new = {n: v for n, v in new.items() if n not in targets2}
        rest = {s for s in set(src2.values()) if s not in targets2 and s not in new}
        cl = {}
        if use_corridor:
            cl = K.corridor_links(rest, spill2, znode, ground, corridor, cfg.CORRIDOR_ENTRY_M,
                                  cfg.CORRIDOR_MIN_GRAD, gates, mp_union=mp_union,
                                  mp_invert_depth=cfg.MP_INVERT_DEPTH_M,
                                  max_len=cfg.CORRIDOR_MAX_M, streets=streets,
                                  mp_max_len=cfg.LINK_MP_MAX_M, stp_level=cfg.STP_INVERT_M)
        for n, (t, ag, geom) in cl.items():
            new[n] = (t, ag)
            corridor_paths[n] = geom
        if not new:
            break
        targets2.update({n: v[0] for n, v in new.items()})
        links.update(new)
    # 2. what is left drains over its rim into the neighbouring sub-network, up to
    #    BASIN_MAX_M of extra depth; deeper than that is a pocket for a pump or a cut
    src2, filled2, parent2, seq2, spill2, iters2 = O.resolve_outlets(
        runs, znode, targets2, cfg.BASIN_MAX_M, raw_term, **assign)
    # 3. a pocket is offered a designed trunk along the streets (rule 3 as a spine): sized
    #    on what lies behind it, laid at that pipe's Table 11 gradient, to the works inlet
    #    or a join's invert, biggest pocket first, later pockets joining an accepted trunk
    log("trunks: every pocket is offered a designed gravity trunk along the streets ...")
    # the main pipe's own gravity profile back from the inlet: a join cannot sit below it
    import math as _math
    import networkx as _nx
    _Gm = _nx.Graph()
    for g in main_pipe:
        cs = [(round(x, 1), round(y, 1)) for x, y in g.coords]
        for a, b in zip(cs[:-1], cs[1:]):
            _Gm.add_edge(a, b, w=_math.dist(a, b))
    _stp_v = min(_Gm.nodes, key=lambda v: _math.dist(v, cfg.STP))
    _mp_dist = _nx.single_source_dijkstra_path_length(_Gm, _stp_v, weight="w")

    def mp_floor(pt):
        foot = mp_union.interpolate(mp_union.project(Point(pt)))
        v = min(_Gm.nodes, key=lambda q: _math.dist(q, (foot.x, foot.y)))
        d = _mp_dist.get(v)
        if d is None:
            return None
        return cfg.STP_INVERT_M + cfg.MP_PROFILE_GRAD * (d + _math.dist(v, (foot.x, foot.y)))

    levels, ttype = {}, {}
    for t, typ in targets2.items():
        if typ == "STP":
            levels[t], ttype[t] = cfg.STP_INVERT_M, "STP"
        elif typ == "JOIN":
            fl = mp_floor(t)
            levels[t] = znode[t] - cfg.MP_INVERT_DEPTH_M if fl is None else fl
            ttype[t] = "JOIN"
    rep["main_pipe_floor"] = {"joins_with_profile_floor": sum(1 for t, typ in targets2.items() if typ == "JOIN" and mp_floor(t) is not None),
                              "joins_total": sum(1 for typ in targets2.values() if typ == "JOIN"),
                              "grad": cfg.MP_PROFILE_GRAD}
    from shapely.prepared import prep as _prep0
    _near0 = _prep0(envelope.buffer(cfg.GATE_SEARCH_M))
    served_pts = [g.centroid for g, c in zip(gates.polys, gates.pcls) if c in ("B", "P")
                  and _near0.contains(g.centroid)]
    _rtree = STRtree([r["geom"] for r in runs])
    plot_node = []
    for pt in served_pts:
        j = _rtree.nearest(pt)
        if j is not None and runs[j]["geom"].distance(pt) <= cfg.GATE_SEARCH_M:
            plot_node.append(runs[j]["up"])
    trunk_stem, trunk_runs, trunks, refused_all = {}, set(), {}, {}

    def pocket_props(src_map):
        props_of = {}
        for n in plot_node:
            o = src_map.get(n)
            if o is not None:
                props_of[o] = props_of.get(o, 0) + 1
        return props_of

    for _ in range(6):
        pockets = [s_ for s_ in set(src2.values()) if s_ not in targets2 and spill2.get(s_) is not None]
        props_of = pocket_props(src2)
        pockets.sort(key=lambda s_: -props_of.get(s_, 0))
        if not pockets:
            break
        acc, trunk_stem, trunk_runs, levels, ttype, refused = K.trunk_routes(
            runs, znode, levels, ttype, pockets, props_of, cfg.DEPTH_WEIGHT, cfg.MAX_DEPTH_M,
            cfg.TRUNK_COVER_M, cfg.PER_PROPERTY_M3D, stem=trunk_stem, trunk_runs=trunk_runs,
            try_targets=cfg.TRUNK_TRY, max_len=cfg.TRUNK_MAX_M,
            take_shortfall=getattr(cfg, 'TRUNK_TAKE_SHORTFALL', False),
            violation_max=getattr(cfg, 'TRUNK_VIOLATION_MAX_M', 10.0))
        refused_all.update(refused)
        if not acc:
            break
        for s_, a in acc.items():
            targets2[s_] = {"STP": "LINK-STP", "JOIN": "LINK-MP"}.get(a["type"], "LINK-TRUNK")
            trunks[s_] = a
            log(f"   trunk from {tuple(round(v) for v in s_)}: {a['len']} m DN{a['dn']} at "
                f"{a['smin'] * 100:.3f} % to the {a['type']}, deepest {a['max_depth']} m, "
                f"arrives {a['arrives']} against {a['level']} ({a['props']:.0f} properties)"
                + (f" UNDER BY {a['under_m']} m" if a.get('under_m') else "")
                + (f" OVER 12 m BY {a['over_m']} m" if a.get('over_m') else ""))
        src2, filled2, parent2, seq2, spill2, iters2 = O.resolve_outlets(
            runs, znode, targets2, cfg.BASIN_MAX_M, raw_term, **assign)
    for s_, tried in refused_all.items():
        log(f"   no trunk for the pocket at {tuple(round(v) for v in s_)}: {tried[:3]}")
    # point every run down the FINAL filled surface: the first flood stopped at every sink,
    # this one drains the basins over their rims, and the chains must read these arrows
    runs = O.flood_direction(runs, parent2, filled2, seq2, cfg.FLAT_PCT, cfg.LEVEL_M)
    rep["links"] = {"to_stp": sum(1 for v in links.values() if v[0] == "LINK-STP"),
                    "to_main_pipe": sum(1 for v in links.values() if v[0] == "LINK-MP"),
                    "crossing_agricultural_plots": sum(1 for v in links.values() if v[1] > 0)}
    log(f"   {rep['links']}; corridor {rep['corridor']}")
    # basins: raw sinks that the flood fills by more than HOLLOW_M are marked with the extra
    # depth the pipe carries to leave them; they are NOT outlets
    basins = []
    for s in raw_sinks:
        if s in filled2 and s not in targets2:
            sp = filled2[s] - znode[s]
            if sp > cfg.HOLLOW_M:
                basins.append({"xy": s, "extra_m": sp})
    rep["basins_marked"] = {"count": len(basins),
                            "extra_depth_m": {"median": round(float(__import__("numpy").median([b["extra_m"] for b in basins])), 2) if basins else None,
                                              "max": round(max((b["extra_m"] for b in basins), default=0.0), 2)}}
    log(f"   basins crossed by depth: {rep['basins_marked']}")

    # ------------------------------------------------------------ phase 3: assemble, lay, reroute
    rep["reroute"] = []
    import copy as _copy
    best_round = None                    # (score, snapshot of the state that produced it)
    restoring = False
    runs_pristine = _copy.deepcopy(runs)  # the heads are trimmed in place by every round
    for rr in range(cfg.REROUTE_ROUNDS + 2):
        snapshot = (dict(targets2), dict(src2), dict(filled2), dict(parent2), dict(seq2),
                    dict(spill2), dict(trunk_stem), set(trunk_runs), dict(trunks))
        runs = _copy.deepcopy(runs_pristine)
        runs = O.flood_direction(runs, parent2, filled2, seq2, cfg.FLAT_PCT, cfg.LEVEL_M)
        basins = []
        for s_ in raw_sinks:
            if s_ in filled2 and s_ not in targets2:
                sp = filled2[s_] - znode[s_]
                if sp > cfg.HOLLOW_M:
                    basins.append({"xy": s_, "extra_m": sp})
        rep["basins_marked"] = {"count": len(basins),
                                "extra_depth_m": {"median": round(float(__import__("numpy").median([b["extra_m"] for b in basins])), 2) if basins else None,
                                                  "max": round(max((b["extra_m"] for b in basins), default=0.0), 2)}}
        log("sub-mains: the long straight streets that attach to the outlet ...")
        chains = K.street_chains(runs, cfg.STRAIGHT_DEG)
        chains = K.cut_at_crests(chains, runs, znode, cfg.CREST_M)      # rule 6: never over a hill
        chains = K.cut_at_divides(chains, runs, src2, filled2, cfg.LEVEL_M)  # ... nor against it
        submain, stem_parent, srep3 = K.sub_mains_by_chains(runs, chains, parent2, src2,
                                                            cfg.CHAIN_MIN_M, cfg.CHAIN_LINK_M,
                                                            filled2, cfg.LEVEL_M)
        stem_parent.update(trunk_stem)          # a designed trunk fixes its own direction
        submain = set(submain) | set(trunk_runs)
        srep3["street_chains"] = len(chains)
        srep3["chains_cut_at_a_crest"] = sum(1 for c in chains if c.get("cut"))
        srep3["chains_cut_at_a_divide"] = sum(1 for c in chains if c.get("divide"))
        srep3["chains_over_min"] = sum(1 for c in chains if c["len"] >= cfg.CHAIN_MIN_M)
        rep["submains"] = srep3
        log(f"   {srep3}")

        log("the tree: laterals to the nearest sub-main by least depth; one outlet per junction ...")
        par, dist, unreached = K.build_tree(runs, znode, submain, stem_parent, cfg.DEPTH_WEIGHT,
                                            cfg.SMIN_PROXY, outlets=set(src2.values()), src=src2,
                                            submain_discount=cfg.SUBMAIN_DISCOUNT)
        tree_idx, extra = K.orient_tree(runs, par, znode, cfg.LEVEL_M, cfg.FLAT_PCT)
        for i in tree_idx:
            runs[i]["tier"] = ("trunk" if i in trunk_runs else
                               "sub main" if i in submain else "lateral")
        log(f"   tree {len(tree_idx)} runs, leftovers {len(extra)}, unreached {len(unreached)}")

        log("branches and heads: leftovers drain to their lower end, heads at the first gate ...")
        branches, gaps_b, dropped = K.make_branches(runs, extra, znode, dist, gates, cfg.LEVEL_M,
                                                    cfg.FLAT_PCT, cfg.FANOUT_OFFSET_M,
                                                    cfg.BRANCH_MIN_M)
        gaps_h, trimmed = K.trim_tree_heads(runs, tree_idx, par, gates, cfg.FANOUT_OFFSET_M,
                                            cfg.BRANCH_MIN_M,
                                            receiving={b["dn"] for b in branches})
        # every pipe must end where another pipe starts, or at an outlet
        starts = {p["up"] for p in [runs[i] for i in tree_idx] + branches}
        ends_ok = {p["dn"] for p in [runs[i] for i in tree_idx] + branches}
        dangling = [p for p in [runs[i] for i in tree_idx] + branches
                    if p["dn"] not in starts and p["dn"] not in set(src2.values())]
        rep["dangling_ends"] = len(dangling)
        rep["branches"] = {"count": len(branches), "km": round(sum(b["len"] for b in branches) / 1000, 2),
                           "heads_at_gate": sum(1 for b in branches if b["head_how"] == "gate"),
                           "heads_offset_10m": sum(1 for b in branches if b["head_how"] == "offset"),
                           "tree_heads_trimmed_to_gate": trimmed,
                           "too_short_for_a_head": len(dropped),
                           "too_short_km": round(sum(runs[i]["len"] for i in dropped) / 1000, 3)}
        log(f"   {rep['branches']}")

        # catchment of every pipe = the outlet its tree path ends at
        root_cache = {}

        def root(n):
            path = []
            while n not in root_cache:
                p = par.get(n)
                if p is None:
                    root_cache[n] = n
                    break
                if n in path:
                    raise RuntimeError(f"the tree has a cycle through {n}: {path[-4:]}")
                path.append(n)
                n = p
            rt = root_cache[n]
            for q in path:
                root_cache[q] = rt
            return rt

        tree_runs = [runs[i] for i in tree_idx]
        pipes = tree_runs + branches
        cid_of = {}
        outlets_final = {}
        for p in pipes:
            o = root(p["dn"])
            if o not in cid_of:
                cid_of[o] = f"C{len(cid_of) + 1:02d}"
            p["catch"] = cid_of[o]
            outlets_final[cid_of[o]] = o
        # rename by size, biggest first
        size = {}
        for p in pipes:
            size[p["catch"]] = size.get(p["catch"], 0.0) + p["len"]
        order = sorted(size, key=lambda c: -size[c])
        rename = {c: f"C{k + 1:02d}" for k, c in enumerate(order)}
        for p in pipes:
            p["catch"] = rename[p["catch"]]
        outlets_final = {rename[c]: o for c, o in outlets_final.items()}
        zstp = cfg.STP_INVERT_M           # the works inlet invert, from the as-built
        info2 = {}
        for cid, o in outlets_final.items():
            ps = [p for p in pipes if p["catch"] == cid]
            typ = targets2.get(o) or ("LOW" if spill2.get(o) is None else "SINK")
            d = {"outlet": o, "type": typ, "pipes": len(ps),
                 "km": sum(p["len"] for p in ps) / 1000.0,
                 "submain_km": sum(p["len"] for p in ps if p["tier"] == "sub main") / 1000.0,
                 "spill_m": spill2.get(o)}
            if typ in ("SINK", "LOW", "LINK-STP", "LINK-MP"):
                po = Point(o)
                foot = mp_union.interpolate(mp_union.project(po))
                zf = float(ground.z_at([foot.x], [foot.y])[0]) - cfg.MP_INVERT_DEPTH_M
                d["to_mp"] = (znode[o] - zf, po.distance(foot))       # to the trunk's invert
                d["to_stp"] = (znode[o] - zstp, po.distance(Point(cfg.STP)))
                if o in links:
                    d["agri_plots_crossed"] = links[o][1]
            info2[cid] = d
        dag, max_out = K.check_tree(tree_runs, branches)
        rep["tree_check"] = {"no_loops": bool(dag), "max_outlets_per_node": int(max_out)}

        log("depth: size every pipe on the plots it serves at saturation, lay heads-down (rule 9) ...")
        from sewnet import quicklay as Q
        from shapely.prepared import prep as _prep
        near = _prep(envelope.buffer(cfg.GATE_SEARCH_M))
        served_plots = [g for g, c in zip(gates.polys, gates.pcls) if c in ("B", "P")
                        and near.contains(g.centroid)]
        acc_pts = []
        if getattr(cfg, "ACCOUNTS", None):
            acc_pts = [g for g in gpd.read_file(cfg.ACCOUNTS).geometry
                       if g is not None and near.contains(g)]
        props, n_plots = Q.properties_per_pipe(pipes, served_plots, acc_pts, cfg.GATE_SEARCH_M)
        znode_all = dict(znode)
        for b in branches:
            znode_all.setdefault(b["up"], b["z_up"])
        # the works inlet is a fixed level, and every join is floored by the main pipe's
        # own gravity profile back from it (2026-09-08, engineer: everything on gravity)
        floors = {t: lv for t, lv in levels.items() if ttype.get(t) in ("STP", "JOIN")}
        depth, governs, laid = Q.lay(pipes, props, znode_all, cfg.PER_PROPERTY_M3D,
                                     floors=floors)
        rep["depth"] = Q.report(pipes, depth, cfg.MAX_DEPTH_M)
        rep["depth"]["plots_served"] = n_plots
        rep["depth"]["properties_at_saturation"] = int(props.sum())
        log(f"   {rep['depth']}")
        rep["tier_km"] = km_by(pipes, "tier", ("sub main", "lateral", "branch"))
        rep["class_km"] = km_by(pipes, "cls", ("NORMAL", "FLAT", "LEVEL", "AGAINST"))
        TYPES = ("JOIN", "STP", "LINK-STP", "LINK-MP", "SINK", "LOW")
        rep["catchments"] = {"count": len(info2),
                             "by_type": {t: sum(1 for i in info2.values() if i["type"] == t)
                                         for t in TYPES},
                             "km_by_type": {t: round(sum(i["km"] for i in info2.values()
                                                         if i["type"] == t), 1)
                                            for t in TYPES}}
        log(f"   check {rep['tree_check']}; tiers {rep['tier_km']}; {rep['catchments']}")


        # rule 10: over 12 m, reroute first. The basin behind each failure is offered a
        # designed trunk along the streets; then the tree is rebuilt and laid again
        over = rep["depth"]["catchments_over_limit"]
        score = (rep["depth"]["over_limit"], rep["depth"]["depth_max_m"],
                 round(sum(rep["depth"]["arrives_under_level"].values()), 2))
        if restoring:
            break                        # the best round, laid again: done
        if best_round is None or score < best_round[0]:
            best_round = (score, snapshot)
        if not over or rr >= cfg.REROUTE_ROUNDS or score > best_round[0]:
            if score > best_round[0]:
                # this round made it worse: go back to the best and lay it once more
                (targets2, src2, filled2, parent2, seq2, spill2, trunk_stem, trunk_runs,
                 trunks) = (_copy.copy(x) for x in best_round[1])
                rep["reroute"].append({"round": rr + 1, "kept": "the best round restored"})
                log(f"   rule 10: round {rr + 1} was worse; the best round is laid again")
                restoring = True
                continue
            break
        pockets = []
        raw_props = pocket_props(raw_term)       # the plots behind every raw sink
        for cid in over:
            ps = [p for p in pipes if p["catch"] == cid]
            dp = max(ps, key=lambda p: p["depth_dn"])
            # the basin that costs the depth: the raw sink on the governing path with the
            # largest fill, not the head's own hollow
            n, cands = dp["dn"], []
            while n in governs:
                q = pipes[governs[n]]
                if q["dn"] in raw_term:
                    s_ = raw_term[q["dn"]]
                    if s_ not in targets2 and s_ not in trunk_stem and s_ not in pockets:
                        cands.append((filled2.get(s_, znode.get(s_, 0.0)) - znode.get(s_, 0.0), s_))
                n = q["up"]
            if not cands:
                continue
            seen_ = set()
            for fill_, s_ in sorted(cands, reverse=True):
                if s_ in seen_:
                    continue
                seen_.add(s_)
                pockets.append(s_)
                if len(seen_) >= getattr(cfg, "REROUTE_BASINS", 1):
                    break
        props_of = {s_: raw_props.get(s_, 0) for s_ in pockets}
        acc, trunk_stem, trunk_runs, levels, ttype, refused = K.trunk_routes(
            runs, znode, levels, ttype, pockets, props_of, cfg.DEPTH_WEIGHT, cfg.MAX_DEPTH_M,
            cfg.TRUNK_COVER_M, cfg.PER_PROPERTY_M3D, stem=trunk_stem, trunk_runs=trunk_runs,
            try_targets=cfg.TRUNK_TRY, max_len=cfg.TRUNK_MAX_M,
            take_shortfall=getattr(cfg, 'TRUNK_TAKE_SHORTFALL', False),
            violation_max=getattr(cfg, 'TRUNK_VIOLATION_MAX_M', 10.0))
        rep["reroute"].append({"round": rr + 1, "over_limit": dict(over),
                               "pockets": [tuple(round(v, 1) for v in s_) for s_ in pockets],
                               "trunks": len(acc),
                               "cut_for_a_pump": [tuple(round(v, 1) for v in s_) for s_ in pockets if s_ not in acc],
                               "refused": {str(tuple(round(v, 1) for v in k)): v[:3] for k, v in refused.items()}})
        log(f"   rule 10, round {rr + 1}: {dict(over)} -> {len(pockets)} pockets offered a trunk, {len(acc)} routed")
        # rule 10's cut: a basin that no trunk can carry within the cap becomes a pocket
        # for a pump, so the rest is laid again without it
        cut = [s_ for s_ in pockets if s_ not in acc]
        for s_ in cut:
            targets2[s_] = "SINK"
            log(f"   rule 10, cut: the basin at {tuple(round(v) for v in s_)} is a pocket for a pump "
                f"({props_of.get(s_, 0)} plots)")
        if not acc and not cut:
            break
        for s_, a in acc.items():
            targets2[s_] = {"STP": "LINK-STP", "JOIN": "LINK-MP"}.get(a["type"], "LINK-TRUNK")
            trunks[s_] = a
            log(f"   trunk from {tuple(round(v) for v in s_)}: {a['len']} m DN{a['dn']} at "
                f"{a['smin'] * 100:.3f} % to the {a['type']}, deepest {a['max_depth']} m, "
                f"arrives {a['arrives']} against {a['level']}"
                + (f" UNDER BY {a['under_m']} m" if a.get('under_m') else "")
                + (f" OVER 12 m BY {a['over_m']} m" if a.get('over_m') else ""))
        src2, filled2, parent2, seq2, spill2, iters2 = O.resolve_outlets(
            runs, znode, targets2, cfg.BASIN_MAX_M, raw_term, **assign)
    rep["trunks"] = [{"from": [round(v, 1) for v in k], "to": a["type"], "len_m": a["len"],
                      "dn": a["dn"], "grad_pct": round(a["smin"] * 100, 3),
                      "max_depth_m": a["max_depth"], "arrives_m": a["arrives"],
                      "level_m": a["level"], "under_m": a.get("under_m", 0.0),
                      "over_m": a.get("over_m", 0.0), "sized_on": a.get("sized_on")}
                     for k, a in trunks.items()]
    rep["tier_km"] = km_by(pipes, "tier", ("trunk", "sub main", "lateral", "branch"))

    log("catchment ground and the drawing ...")
    polys2 = O.catchment_polygons(pipes, [p["catch"] for p in pipes], envelope)
    colour2 = O.colour_catchments(polys2)
    joins = K.connectors(info2, [c for c, i in info2.items() if i["type"] == "JOIN"], mp_union)
    link_geoms = K.link_geometries(info2, mp_union, cfg.STP, corridor_paths)
    gaps = gaps_b + gaps_h
    dropped_geoms = [runs[i]["geom"] for i in dropped]
    title = [f"W13 STAGE A - THE NETWORK AS A TREE - built area - {date}",
             "thick = sub-main · thin = lateral or branch · colour = catchment · arrow on every pipe "
             "· grey dotted = the head gap to the first gate · magenta = join connector to the main pipe",
             "dashed = flatter than 0.5 % · dash-dot = against the ground · gradient text is the "
             "GROUND fall along the flow, not a pipe gradient",
             "outlets: JOIN (blue) · LINK, a direct link to the main pipe or along NAMA's trunk "
             "corridor to the STP, dashed magenta (rule 3) · SINK = pocket needing more than 10 m, "
             "a pump or a cut (red) · island low point (orange)",
             "BASIN marks (red rings, layer A_BASINS) = a dip the network drains OVER by depth: the "
             "number is the extra depth the pipe carries to leave it; these are inside a "
             "sub-network, not outlets · red thick = street too short for a head"]
    dxf = XT.write_dxf(os.path.join(cfg.OUT_DXF, "W13_A_tree.dxf"), pipes, gaps, dropped_geoms,
                       info2, polys2, colour2, joins, streams, wadis, main_pipe, built_geoms,
                       envelope, cfg.STP, title, links=link_geoms, basins=basins)
    rep["basins"] = [{"xy": [round(b["xy"][0], 1), round(b["xy"][1], 1)],
                      "extra_m": round(b["extra_m"], 2)} for b in basins]
    XT.write_shapes(cfg.OUT_SHP, "W13_A_tree", pipes, gaps, info2, polys2, {**joins, **link_geoms},
                    cfg.EPSG)
    b = envelope.bounds
    XT.write_png(os.path.join(cfg.OUT_IMG, "W13_A_tree_overview.png"),
                 (b[0] - 200, b[1] - 200, b[2] + 200, b[3] + 200), pipes, gaps, info2, polys2,
                 colour2, joins, streams, main_pipe, built_geoms, envelope, cfg.STP,
                 "Stage A tree: sub-mains thick, colour = catchment", arrows=False, label=False)
    XT.write_png(os.path.join(cfg.OUT_IMG, "W13_A_tree_east.png"), EAST, pipes, gaps, info2,
                 polys2, colour2, joins, streams, main_pipe, built_geoms, envelope, cfg.STP,
                 "Stage A tree, east settlement")
    XT.write_png(os.path.join(cfg.OUT_IMG, "W13_A_tree_west.png"), WEST, pipes, gaps, info2,
                 polys2, colour2, joins, streams, main_pipe, built_geoms, envelope, cfg.STP,
                 "Stage A tree, west settlement")

    rep["catchment_table"] = [
        {"id": c, "type": i["type"], "pipes": i["pipes"], "km": round(i["km"], 2),
         "submain_km": round(i["submain_km"], 2),
         "spill_m": None if i["spill_m"] is None else round(i["spill_m"], 2),
         "to_mp": [round(v, 1) for v in i["to_mp"]] if "to_mp" in i else None,
         "to_stp": [round(v, 1) for v in i["to_stp"]] if "to_stp" in i else None,
         "outlet_xy": [round(i["outlet"][0], 1), round(i["outlet"][1], 1)],
         "area_km2": round(polys2[c].area / 1e6, 3) if c in polys2 else None}
        for c, i in info2.items()]
    rep["seconds"] = round(time.time() - T0, 1)
    with open(os.path.join(cfg.OUT_RUN, "stage_a.json"), "w") as f:
        json.dump(rep, f, indent=2, default=str)
    # the run's working state, so a question about any node or pipe is answered in seconds
    # from the record instead of by a rerun (not committed: see .gitignore)
    import pickle
    with open(os.path.join(cfg.OUT_RUN, "stage_a_state.pkl"), "wb") as f:
        pickle.dump({"runs": runs, "znode": znode, "znode_all": znode_all, "targets": targets2,
                     "src": src2, "filled": filled2, "parent": parent2, "spill": spill2,
                     "raw_sinks": raw_sinks, "basins": basins, "links": links,
                     "chains": chains, "submain": submain, "stem_parent": stem_parent,
                     "par": par, "dist": dist, "tree_idx": tree_idx, "branches": branches,
                     "pipes": pipes, "info": info2, "depth": depth, "governs": governs,
                     "props": props, "trunks": trunks, "trunk_runs": trunk_runs,
                     "levels": levels}, f)
    log(f"done: {dxf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
