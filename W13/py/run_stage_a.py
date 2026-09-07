"""Stage A of the W13 design logic on the built area: rules 1 and 2.

    python run_stage_a.py

Reads the draftsman's DXF inside the ground the 2006 network serves, reads the terrain along
every street, points every run downhill, splits runs at crests and sags, follows the arrows
to the outlets, fills shallow hollows so only real basins remain as sinks, tiles the
catchments, derives the terrain streams as the guide picture, and writes the check drawing
(DXF), shapefiles, PNGs and a JSON of the numbers.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import geopandas as gpd                                              # noqa: E402

import config_built as cfg                                           # noqa: E402
from sewnet import ground as G                                       # noqa: E402
from sewnet import outlets as O                                      # noqa: E402
from sewnet import streams as S                                      # noqa: E402
from sewnet import export_stage_a as X                               # noqa: E402

T0 = time.time()
SCRATCH = os.path.join(cfg.OUT_RUN, "scratch")


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def km_by(runs, field, values):
    return {v: round(sum(r["len"] for r in runs if r.get(field) == v) / 1000, 1) for v in values}


def main():
    for d in (cfg.OUT_SHP, cfg.OUT_DXF, cfg.OUT_IMG, cfg.OUT_RUN, SCRATCH):
        os.makedirs(d, exist_ok=True)
    rep = {}

    log("area: the ground the built 2006 network serves ...")
    envelope, built = G.built_envelope(cfg.BUILT_SEWER, cfg.AREA_BUFFER_M)
    rep["area_km2"] = round(envelope.area / 1e6, 2)
    rep["built_km"] = round(float(built.geometry.length.sum()) / 1000, 1)
    log(f"   {rep['area_km2']} km2 round {rep['built_km']} km of built sewer")

    log("streets: the draftsman's DXF, clipped, snapped, noded ...")
    lines = G.read_dxf_lines(cfg.ROADS_DXF, cfg.ROAD_LAYERS)
    lines = G.clip_lines(lines, envelope)
    rep["street_km_in_area"] = round(sum(g.length for g, _ in lines) / 1000, 1)
    noded, snapped, srep = G.snap_and_node(lines, cfg.SNAP_M)
    rep["snap"] = srep
    log(f"   {rep['street_km_in_area']} km of street; {srep}")

    log("ground: terrain at %.0f m over the area ..." % cfg.GROUND_RES_M)
    ground = G.Ground(cfg.TERRAIN, envelope.bounds, cfg.GROUND_RES_M)
    rep["ground"] = {"cells": int(ground.z.size), "nodata_filled": ground.nodata_cells}

    log("runs: junction to junction, split at crests and sags ...")
    runs0, _ = G.build_runs(noded)
    runs1, new_nodes = G.split_at_extrema(ground, runs0, cfg.CREST_M, cfg.MIN_SPLIT_M,
                                          cfg.PROFILE_STEP_M)
    kinds = dict(new_nodes)
    rep["runs_before_split"] = len(runs0)
    rep["splits"] = {"crest": sum(1 for _, k in new_nodes if k == "crest"),
                     "sag": sum(1 for _, k in new_nodes if k == "sag")}
    node_keys = set()
    for a, b, g, _ in runs1:
        node_keys.add(a)
        node_keys.add(b)
    znode = {n: ground.z_node(n[0], n[1]) for n in node_keys}
    runs = G.orient(runs1, znode, cfg.FLAT_PCT, cfg.LEVEL_M)
    runs = G.tag_layers(runs, snapped)
    rep["runs"] = len(runs)
    rep["run_km"] = round(sum(r["len"] for r in runs) / 1000, 1)
    rep["raw_class_km"] = km_by(runs, "cls", ("NORMAL", "FLAT", "LEVEL"))
    rep["layer_km"] = km_by(runs, "layer", ("existing", "proposed"))
    log(f"   {len(runs)} runs, {rep['run_km']} km; raw ground {rep['raw_class_km']}; "
        f"splits {rep['splits']}")

    log("outlets: follow the arrows, fill the shallow hollows ...")
    mp = gpd.read_file(cfg.MAIN_PIPE)
    main_pipe = [p for g in mp.geometry if g is not None and not g.is_empty
                 for p in (g.geoms if hasattr(g, "geoms") else [g])]
    targets = O.find_targets({n: n for n in node_keys}, main_pipe, cfg.STP, cfg.TARGET_M,
                             cfg.STP_M)
    ptr = O.pointers(runs, targets)
    raw_term = O.terminals(node_keys, ptr, targets)
    raw_sinks = {t for t in set(raw_term.values()) if t not in targets}
    src, filled, parent, seq, spill, iters = O.resolve_outlets(runs, znode, targets,
                                                                cfg.HOLLOW_M, raw_term)
    runs = O.flood_direction(runs, parent, filled, seq, cfg.FLAT_PCT, cfg.LEVEL_M)
    run_catch, info = O.catchments(runs, src, targets, spill)
    rep["targets"] = {"JOIN": sum(1 for v in targets.values() if v == "JOIN"),
                      "STP": sum(1 for v in targets.values() if v == "STP")}
    rep["raw_sinks"] = len(raw_sinks)
    rep["fill_iterations"] = iters
    rep["class_km"] = km_by(runs, "cls", ("NORMAL", "FLAT", "LEVEL", "AGAINST"))
    TYPES = ("JOIN", "STP", "SINK", "LOW")
    rep["catchments"] = {"count": len(info),
                         "by_type": {t: sum(1 for i in info.values() if i["type"] == t)
                                     for t in TYPES},
                         "km_by_type": {t: round(sum(i["km"] for i in info.values()
                                                     if i["type"] == t), 1)
                                        for t in TYPES}}
    sinks = sorted((i for i in info.values() if i["type"] == "SINK"),
                   key=lambda i: -(i["spill_m"] or 0))
    rep["sink_spills_m"] = [round(i["spill_m"], 2) for i in sinks if i["spill_m"] is not None]
    log(f"   {rep['targets']} target junctions; raw sinks {len(raw_sinks)} -> after filling "
        f"hollows to {cfg.HOLLOW_M} m: {rep['catchments']}")
    log(f"   after filling: {rep['class_km']}")

    log("catchment ground: nearest-street tiling ...")
    polys = O.catchment_polygons(runs, run_catch, envelope)
    colour = O.colour_catchments(polys)

    log("guide picture: terrain streams and wadi ground ...")
    try:
        streams, srep2 = S.derive_streams(cfg.TERRAIN, envelope.bounds, cfg.STREAM_RES_M,
                                          cfg.STREAM_THRESHOLD_CELLS, SCRATCH, cfg.STREAM_PAD_M)
        env_pad = envelope.buffer(300)
        streams = [(g.intersection(env_pad), o) for g, o in streams if g.intersects(env_pad)]
        streams = [(p, o) for g, o in streams
                   for p in (g.geoms if hasattr(g, "geoms") else [g])
                   if p.geom_type == "LineString"]
        rep["streams"] = srep2
    except Exception as e:
        streams, rep["streams"] = [], {"error": str(e)}
    log(f"   {rep['streams']}")
    try:
        l, b, r, t = envelope.bounds
        wadis = S.wadi_polygons(cfg.HAZARD, (l - 100, b - 100, r + 100, t + 100))
        env100 = envelope.buffer(100)
        wadis = [w.intersection(env100) for w in wadis if w.intersects(env100)]
        rep["wadi_polygons"] = len(wadis)
    except Exception as e:
        wadis, rep["wadi_polygons"] = [], f"error: {e}"

    deg = {}
    node_catch = {}
    for r, c in zip(runs, run_catch):
        for n in (r["up"], r["dn"]):
            deg[n] = deg.get(n, 0) + 1
            node_catch.setdefault(n, c)
    outlet_nodes = {i["outlet"]: (cid, i["type"]) for cid, i in info.items()}
    nodes = []
    for k, n in enumerate(sorted(node_keys)):
        d = deg.get(n, 0)
        kind = kinds.get(n, "head" if d == 1 else "junction")
        cid, typ = outlet_nodes.get(n, (node_catch.get(n, ""), ""))
        nodes.append({"key": n, "id": f"N{k + 1:05d}", "x": n[0], "y": n[1], "z": znode[n],
                      "fill": filled.get(n, znode[n]) - znode[n],
                      "degree": d, "kind": kind, "catch": cid, "is_outlet": n in outlet_nodes,
                      "out_type": typ})

    log("writing: DXF, shapefiles, PNG ...")
    date = time.strftime("%Y-%m-%d")
    title = [f"W13 STAGE A - THE GROUND READ ALONG THE STREETS - built area - {date}",
             "arrows point downhill · colour = catchment · dashed = flatter than 0.5 % (DN200 minimum) "
             "· dash-dot = flow runs against the ground, over the rim of a hollow filled to 2 m",
             "outlets: JOIN on the main pipe (blue) · STP (magenta) · SINK, a basin deeper than 2 m, "
             "labelled with its spill (red) · LOW, the low point of an island with no street path "
             "to a target (orange)",
             "streams in blue thicken with Strahler order · cyan = wadi ground (hazard 4-6) · "
             "grey = built 2006 sewer · gradient text is signed along the flow"]
    dxf = X.write_dxf(os.path.join(cfg.OUT_DXF, "W13_A_ground.dxf"), runs, run_catch, info, polys,
                      colour, nodes, streams, wadis, main_pipe, list(built.geometry), envelope,
                      cfg.STP, title)
    X.write_shapes(cfg.OUT_SHP, "W13_A", runs, run_catch, info, polys, nodes, streams, cfg.EPSG)
    b = envelope.bounds
    X.write_png(os.path.join(cfg.OUT_IMG, "W13_A_overview.png"),
                (b[0] - 200, b[1] - 200, b[2] + 200, b[3] + 200), runs, run_catch, info, polys,
                colour, streams, main_pipe, list(built.geometry), envelope, cfg.STP,
                "Stage A: arrows downhill, colour = catchment, outlets typed", arrows=False,
                label=False)
    X.write_png(os.path.join(cfg.OUT_IMG, "W13_A_east.png"), (449400, 2566900, 452100, 2571000),
                runs, run_catch, info, polys, colour, streams, main_pipe, list(built.geometry),
                envelope, cfg.STP, "Stage A, east settlement")
    X.write_png(os.path.join(cfg.OUT_IMG, "W13_A_west.png"), (444700, 2565700, 446900, 2567800),
                runs, run_catch, info, polys, colour, streams, main_pipe, list(built.geometry),
                envelope, cfg.STP, "Stage A, west settlement")

    rep["catchment_table"] = [{"id": c, "type": i["type"], "runs": i["runs"],
                               "km": round(i["km"], 2), "flat_km": round(i["flat_km"], 2),
                               "against_km": round(i["against_km"], 2),
                               "spill_m": None if i["spill_m"] is None else round(i["spill_m"], 2),
                               "outlet_xy": [round(i["outlet"][0], 1), round(i["outlet"][1], 1)],
                               "area_km2": round(polys[c].area / 1e6, 3) if c in polys else None}
                              for c, i in info.items()]
    rep["seconds"] = round(time.time() - T0, 1)
    with open(os.path.join(cfg.OUT_RUN, "stage_a.json"), "w") as f:
        json.dump(rep, f, indent=2, default=str)
    log(f"done: {dxf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
