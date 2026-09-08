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
from shapely.geometry import Point                                   # noqa: E402
from shapely.ops import unary_union                                  # noqa: E402

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
    rep["area_km2"] = round(envelope.area / 1e6, 2)
    rep["built_km"] = round(float(built.geometry.length.sum()) / 1000, 1)

    log("streets: the draftsman's DXF, clipped, snapped, noded ...")
    lines = G.clip_lines(G.read_dxf_lines(cfg.ROADS_DXF, cfg.ROAD_LAYERS), envelope)
    noded, snapped, srep = G.snap_and_node(lines, cfg.SNAP_M)
    rep["street_km_in_area"] = round(sum(g.length for g, _ in lines) / 1000, 1)
    rep["snap"] = srep

    log("ground: terrain at %.0f m over the area and both targets ..." % cfg.GROUND_RES_M)
    mp0 = gpd.read_file(cfg.MAIN_PIPE)
    l, b, r, t = envelope.bounds
    ml, mb, mr, mt = mp0.total_bounds
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
    mp = gpd.read_file(cfg.MAIN_PIPE)
    main_pipe = [p for g in mp.geometry if g is not None and not g.is_empty
                 for p in (g.geoms if hasattr(g, "geoms") else [g])]
    mp_union = unary_union(main_pipe)
    targets = O.find_targets({n: n for n in node_keys}, main_pipe, cfg.STP, cfg.TARGET_M,
                             cfg.STP_M)
    ptr = O.pointers(runs, targets)
    raw_term = O.terminals(node_keys, ptr, targets)
    raw_sinks = {t for t in set(raw_term.values()) if t not in targets}
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
            runs, znode, targets2, cfg.HOLLOW_M, raw_term)
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
    corridor = K.TrunkCorridor(built, cfg.STP)
    streets = K.Streets(runs)
    rep["corridor"] = {"lines": len(corridor.lines), "reaches_stp": corridor.ok,
                       "ends_tied_to_stp": corridor.tied_ends}
    # the corridor is a second target: its entry joins are chosen like joins on the main pipe
    entries, corridor_paths = K.corridor_entry_targets(
        node_keys, znode, ground, corridor, streets, cfg.LINK_MP_MAX_M, cfg.JOIN_SPACING_M,
        cfg.CORRIDOR_MIN_GRAD, cfg.CORRIDOR_MAX_M, mp_union=mp_union, plots=gates)
    entries = {n: t for n, t in entries.items() if n not in targets2}
    targets2.update(entries)
    rep["corridor"]["entry_joins"] = len(entries)
    log(f"   corridor entry joins: {len(entries)}")
    links = {}
    # 1. every basin deeper than HOLLOW_M is offered a direct link first: to the main pipe's
    #    invert, or along NAMA's corridor to the STP. Gravity with no extra depth beats
    #    climbing out of a basin (rule 5's least-depth logic; NAMA sent the west to the STP)
    for _ in range(8):
        src2, filled2, parent2, seq2, spill2, iters2 = O.resolve_outlets(
            runs, znode, targets2, cfg.HOLLOW_M, raw_term)
        new = K.link_targets(set(src2.values()), spill2, znode, ground, mp_union, cfg.STP,
                             cfg.LINK_MIN_GRAD, cfg.MP_INVERT_DEPTH_M, cfg.LINK_MAX_M, gates,
                             existing=list(targets2), spacing_m=cfg.JOIN_SPACING_M,
                             streets=streets, mp_max_len=cfg.LINK_MP_MAX_M)
        new = {n: v for n, v in new.items() if n not in targets2}
        rest = {s for s in set(src2.values()) if s not in targets2 and s not in new}
        cl = K.corridor_links(rest, spill2, znode, ground, corridor, cfg.CORRIDOR_ENTRY_M,
                              cfg.CORRIDOR_MIN_GRAD, gates, mp_union=mp_union,
                              mp_invert_depth=cfg.MP_INVERT_DEPTH_M, max_len=cfg.CORRIDOR_MAX_M,
                              streets=streets, mp_max_len=cfg.LINK_MP_MAX_M)
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
        runs, znode, targets2, cfg.BASIN_MAX_M, raw_term)
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

    log("sub-mains: the heaviest low stem of each catchment ...")
    submain, stem_parent, srep3 = K.sub_mains(runs, parent2, seq2, src2, cfg.STEM_MIN_M,
                                              cfg.SIDE_STEM_MIN_M)
    rep["submains"] = srep3
    log(f"   {srep3}")

    log("the tree: laterals to the nearest sub-main by least depth; one outlet per junction ...")
    par, dist, unreached = K.build_tree(runs, znode, submain, stem_parent, cfg.DEPTH_WEIGHT,
                                        cfg.SMIN_PROXY, outlets=set(src2.values()))
    tree_idx, extra = K.orient_tree(runs, par, znode, cfg.LEVEL_M, cfg.FLAT_PCT)
    for i in tree_idx:
        runs[i]["tier"] = "sub main" if i in submain else "lateral"
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
    zstp = float(ground.z_at([cfg.STP[0]], [cfg.STP[1]])[0])
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
    log(f"done: {dxf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
