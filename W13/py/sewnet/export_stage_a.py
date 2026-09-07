"""sewnet.export_stage_a — the Stage A drawing: DXF, shapefiles and PNG.

The drawing is the check (W13_DESIGN_LOGIC.md, Outputs). One layer per element, runs
coloured by catchment with an arrow on every one, flat runs dashed, the gradient written on
every run long enough to carry it, outlets marked and typed, catchment outlines dashed with a
stats label, streams thickening with order, wadi ground, the main pipe, the built network for
reference, the envelope and the STP.
"""
import math
import os

import ezdxf
from ezdxf.enums import TextEntityAlignment
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Point

# AutoCAD colour indices that stay distinct on a white or black background
PALETTE = [1, 2, 3, 4, 5, 6, 30, 42, 92, 132, 172, 212]
OUTLET_COLOUR = {"JOIN": 5, "STP": 6, "SINK": 1, "LOW": 30}


def _arrow(msp, g, layer, col, size=4.0, at=0.6):
    L = g.length
    p = g.interpolate(at * L)
    q = g.interpolate(min(L, at * L + 1.0))
    ang = math.atan2(q.y - p.y, q.x - p.x)
    c, s = math.cos(ang), math.sin(ang)
    tip = (p.x + size * c, p.y + size * s)
    left = (p.x - 0.6 * size * c + 0.5 * size * s, p.y - 0.6 * size * s - 0.5 * size * c)
    right = (p.x - 0.6 * size * c - 0.5 * size * s, p.y - 0.6 * size * s + 0.5 * size * c)
    msp.add_solid([tip, left, right, right], dxfattribs={"layer": layer, "color": col})


def _poly_rings(geom):
    parts = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    for p in parts:
        if p.geom_type != "Polygon" or p.is_empty:
            continue
        yield list(p.exterior.coords)
        for r in p.interiors:
            yield list(r.coords)


def write_dxf(path, runs, run_catch, catch_info, catch_polys, catch_colour, nodes, streams,
              wadis, main_pipe, built, envelope, stp, title):
    doc = ezdxf.new("R2010", setup=True)
    for name, col in (("A_RUNS", 7), ("A_ARROWS", 7), ("A_GRADIENT", 8), ("A_JUNCTIONS", 8),
                      ("A_OUTLETS", 7), ("A_OUTLET_LABEL", 7), ("A_CATCHMENTS", 7),
                      ("A_CATCH_LABEL", 7), ("A_STREAMS", 5), ("A_WADI", 4), ("A_MAIN_PIPE", 5),
                      ("A_BUILT_2006", 252), ("A_ENVELOPE", 3), ("A_STP", 6), ("A_TITLE", 7)):
        doc.layers.add(name, color=col)
    msp = doc.modelspace()

    for r, c in zip(runs, run_catch):
        col = PALETTE[catch_colour.get(c, 0)]
        attrs = {"layer": "A_RUNS", "color": col}
        if r["cls"] == "AGAINST":
            attrs["linetype"] = "DASHDOT"
        elif r["cls"] != "NORMAL":
            attrs["linetype"] = "DASHED"
        msp.add_lwpolyline(list(r["geom"].coords), dxfattribs=attrs)
        g = r["geom"]
        if g.length >= 12:
            _arrow(msp, g, "A_ARROWS", col)
        if g.length >= 60:
            m = g.interpolate(0.5 * g.length)
            q = g.interpolate(min(g.length, 0.5 * g.length + 1.0))
            rot = math.degrees(math.atan2(q.y - m.y, q.x - m.x))
            if rot > 90 or rot < -90:
                rot += 180
            msp.add_text(f"{r['grad']:.2f}%", height=2.0, rotation=rot,
                         dxfattribs={"layer": "A_GRADIENT", "color": col}
                         ).set_placement((m.x, m.y), align=TextEntityAlignment.BOTTOM_CENTER)

    for n in nodes:
        if n["kind"] in ("junction", "head"):
            msp.add_circle((n["x"], n["y"]), 1.5, dxfattribs={"layer": "A_JUNCTIONS"})
        else:
            msp.add_circle((n["x"], n["y"]), 2.5, dxfattribs={"layer": "A_JUNCTIONS", "color": 30})

    for cid, info in catch_info.items():
        x, y = info["outlet"]
        col = OUTLET_COLOUR[info["type"]]
        msp.add_circle((x, y), 7.0, dxfattribs={"layer": "A_OUTLETS", "color": col})
        if info["type"] != "LOW":
            msp.add_circle((x, y), 4.0, dxfattribs={"layer": "A_OUTLETS", "color": col})
        lab = f"{cid} {info['type']}"
        if info["type"] == "SINK" and info.get("spill_m") is not None:
            lab += f" spill {info['spill_m']:.1f} m"
        elif info["type"] == "LOW":
            lab += " point of an island"
        msp.add_text(lab, height=4.0,
                     dxfattribs={"layer": "A_OUTLET_LABEL", "color": col}
                     ).set_placement((x + 9, y + 3), align=TextEntityAlignment.LEFT)

    for cid, poly in catch_polys.items():
        col = PALETTE[catch_colour.get(cid, 0)]
        for ring in _poly_rings(poly):
            msp.add_lwpolyline(ring, close=True,
                               dxfattribs={"layer": "A_CATCHMENTS", "color": col,
                                           "linetype": "DASHED"})
        info = catch_info[cid]
        rp = poly.representative_point()
        msp.add_text(f"{cid} · {info['type']} · {info['km']:.1f} km · {info['runs']} runs · "
                     f"{poly.area / 1e6:.2f} km²", height=5.0,
                     dxfattribs={"layer": "A_CATCH_LABEL", "color": col}
                     ).set_placement((rp.x, rp.y), align=TextEntityAlignment.MIDDLE_CENTER)

    for g, order in streams:
        msp.add_lwpolyline(list(g.coords), dxfattribs={"layer": "A_STREAMS", "color": 5,
                                                       "const_width": 0.8 * order})
    for p in wadis:
        for ring in _poly_rings(p):
            msp.add_lwpolyline(ring, close=True, dxfattribs={"layer": "A_WADI", "color": 4})
    for g in main_pipe:
        msp.add_lwpolyline(list(g.coords), dxfattribs={"layer": "A_MAIN_PIPE", "color": 5,
                                                       "const_width": 3.0})
    for g in built:
        parts = list(g.geoms) if hasattr(g, "geoms") else [g]
        for p in parts:
            msp.add_lwpolyline(list(p.coords), dxfattribs={"layer": "A_BUILT_2006", "color": 252})
    for ring in _poly_rings(envelope):
        msp.add_lwpolyline(ring, close=True, dxfattribs={"layer": "A_ENVELOPE", "color": 3})
    msp.add_circle(stp, 25.0, dxfattribs={"layer": "A_STP", "color": 6})
    msp.add_text("STP", height=12.0, dxfattribs={"layer": "A_STP", "color": 6}
                 ).set_placement((stp[0] + 30, stp[1]), align=TextEntityAlignment.LEFT)

    l, b, r, t = envelope.bounds
    y = t + 120
    for line in title:
        msp.add_text(line, height=14.0, dxfattribs={"layer": "A_TITLE"}
                     ).set_placement((l, y), align=TextEntityAlignment.LEFT)
        y -= 22
    doc.saveas(path)
    return path


def write_shapes(out_dir, prefix, runs, run_catch, catch_info, catch_polys, nodes, streams,
                 epsg=32640):
    os.makedirs(out_dir, exist_ok=True)
    node_id = {n["key"]: n["id"] for n in nodes}
    gdf = gpd.GeoDataFrame({
        "RUN_ID": [f"R{i + 1:05d}" for i in range(len(runs))],
        "UP_NODE": [node_id[r["up"]] for r in runs],
        "DN_NODE": [node_id[r["dn"]] for r in runs],
        "LEN_M": [round(r["len"], 1) for r in runs],
        "Z_UP": [round(r["z_up"], 2) for r in runs],
        "Z_DN": [round(r["z_dn"], 2) for r in runs],
        "FALL_M": [round(r["fall"], 2) for r in runs],
        "GRAD_PCT": [round(r["grad"], 3) for r in runs],
        "CLASS": [r["cls"] for r in runs],
        "SPLIT": [r["split"] for r in runs],
        "LAYER": [r.get("layer", "") for r in runs],
        "CATCH": run_catch,
        "OUT_TYPE": [catch_info[c]["type"] for c in run_catch],
    }, geometry=[r["geom"] for r in runs], crs=f"EPSG:{epsg}")
    gdf.to_file(os.path.join(out_dir, f"{prefix}_runs.shp"))

    gn = gpd.GeoDataFrame({
        "NODE_ID": [n["id"] for n in nodes], "Z": [round(n["z"], 2) for n in nodes],
        "DEGREE": [n["degree"] for n in nodes], "KIND": [n["kind"] for n in nodes],
        "CATCH": [n["catch"] for n in nodes], "IS_OUTLET": [int(n["is_outlet"]) for n in nodes],
        "OUT_TYPE": [n["out_type"] for n in nodes],
    }, geometry=[Point(n["x"], n["y"]) for n in nodes], crs=f"EPSG:{epsg}")
    gn.to_file(os.path.join(out_dir, f"{prefix}_nodes.shp"))
    gn[gn["IS_OUTLET"] == 1].to_file(os.path.join(out_dir, f"{prefix}_outlets.shp"))

    ids = list(catch_polys)
    gc = gpd.GeoDataFrame({
        "CATCH": ids, "OUT_TYPE": [catch_info[c]["type"] for c in ids],
        "RUNS": [catch_info[c]["runs"] for c in ids],
        "KM": [round(catch_info[c]["km"], 2) for c in ids],
        "FLAT_KM": [round(catch_info[c]["flat_km"], 2) for c in ids],
        "AREA_KM2": [round(catch_polys[c].area / 1e6, 3) for c in ids],
    }, geometry=[catch_polys[c] for c in ids], crs=f"EPSG:{epsg}")
    gc.to_file(os.path.join(out_dir, f"{prefix}_catchments.shp"))

    if streams:
        gs = gpd.GeoDataFrame({"ORDER": [o for _, o in streams]},
                              geometry=[g for g, _ in streams], crs=f"EPSG:{epsg}")
        gs.to_file(os.path.join(out_dir, f"{prefix}_streams.shp"))


def write_png(path, bounds, runs, run_catch, catch_info, catch_polys, catch_colour, streams,
              main_pipe, built, envelope, stp, title, dpi=130, arrows=True, label=True):
    tab = plt.get_cmap("tab10")
    cmap = lambda k: tab(int(round(k * 12)) % 10)      # noqa: E731  distinct hues per index
    fig, ax = plt.subplots(figsize=(15, 11), dpi=dpi)
    for cid, poly in catch_polys.items():
        parts = list(poly.geoms) if hasattr(poly, "geoms") else [poly]
        for p in parts:
            if p.geom_type == "Polygon" and not p.is_empty:
                ax.fill(*p.exterior.xy, color=cmap(catch_colour.get(cid, 0) / 12), alpha=0.12,
                        lw=0)
                ax.plot(*p.exterior.xy, color=cmap(catch_colour.get(cid, 0) / 12), lw=0.8,
                        ls="--")
    for g in built:
        parts = list(g.geoms) if hasattr(g, "geoms") else [g]
        for p in parts:
            ax.plot(*p.xy, color="#bbbbbb", lw=0.4)
    for g, order in streams:
        ax.plot(*g.xy, color="#3b6fd6", lw=0.4 * order, alpha=0.6)
    for r, c in zip(runs, run_catch):
        col = cmap(catch_colour.get(c, 0) / 12)
        ls = {"NORMAL": "-", "FLAT": "--", "LEVEL": "--", "AGAINST": ":"}[r["cls"]]
        ax.plot(*r["geom"].xy, color=col, lw=1.1, ls=ls)
        if arrows and r["len"] >= 15:
            g = r["geom"]
            p = g.interpolate(0.6 * g.length)
            q = g.interpolate(min(g.length, 0.6 * g.length + 1.0))
            ax.annotate("", xy=(q.x, q.y), xytext=(p.x, p.y),
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, mutation_scale=8))
    for g in main_pipe:
        ax.plot(*g.xy, color="blue", lw=2.2)
    for cid, info in catch_info.items():
        x, y = info["outlet"]
        if not (bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
            continue
        mk = {"JOIN": "o", "STP": "*", "SINK": "v", "LOW": "s"}[info["type"]]
        colr = {"JOIN": "blue", "STP": "magenta", "SINK": "red", "LOW": "darkorange"}[info["type"]]
        ax.plot(x, y, marker=mk, color=colr, ms=8, mec="black", mew=0.5, ls="none")
        if label:
            lab = f"{cid} {info['type']} {info['km']:.1f} km"
            if info["type"] == "SINK" and info.get("spill_m") is not None:
                lab += f" +{info['spill_m']:.1f} m"
            ax.text(x + 8, y + 8, lab, fontsize=6, color=colr)
    parts = list(envelope.geoms) if hasattr(envelope, "geoms") else [envelope]
    for p in parts:
        ax.plot(*p.exterior.xy, color="green", lw=1.0)
    ax.plot(stp[0], stp[1], marker="*", color="magenta", ms=16, mec="black")
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=9)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path
