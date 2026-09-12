"""sewnet.export_tree — the Stage A tree drawing: DXF, shapefiles and PNG.

Sub-mains thick, laterals and branches thin, colour by catchment, an arrow on every pipe, the
unpiped head gaps in grey, every join drawn as a connector to the main pipe, outlets typed and
labelled with what leaving them costs, catchment outlines dashed with a stats label.
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

from .export_stage_a import PALETTE, OUTLET_COLOUR, _arrow, _poly_rings

TIER_WIDTH = {"trunk": 4.0, "sub main": 2.5, "lateral": 0.8, "branch": 0.8}
# temp 3 (2026-09-11, engineer): the guideline's tier names (G203 p17, p21). "Lateral" is the
# tertiary pipe, so the street pipe is a secondary main sewer. The engine's own roles stay in
# the ROLE field and the layers, so a branch (a leftover street, its head at a gate) still shows
TIER_NAME = {"trunk": "primary", "sub main": "secondary header",
             "lateral": "secondary main sewer", "branch": "secondary main sewer"}
TIER_LAYER = {"trunk": "A_PRIMARY", "sub main": "A_SECONDARY_HEADER",
              "lateral": "A_SECONDARY_MAIN", "branch": "A_SECONDARY_MAIN_BRANCH"}
OUT_COL = dict(OUTLET_COLOUR, **{"LINK-STP": 6, "LINK-MP": 6})
PNG_MARK = {"JOIN": "o", "STP": "*", "SINK": "v", "LOW": "s", "LINK-STP": "D", "LINK-MP": "D"}
PNG_COL = {"JOIN": "blue", "STP": "magenta", "SINK": "red", "LOW": "darkorange",
           "LINK-STP": "magenta", "LINK-MP": "purple"}


def outlet_label(cid, info):
    t = info["type"]
    if t == "JOIN":
        s = f"{cid} JOIN {info['km']:.1f} km"
    elif t == "STP":
        s = f"{cid} STP {info['km']:.1f} km"
    elif t == "SINK":
        s = f"{cid} basin {info['km']:.1f} km: leaves by gravity at ~{(info.get('spill_m') or 0.0):.1f} m extra depth"
    elif t == "LINK-STP":
        s = f"{cid} LINK to STP by gravity {info['km']:.1f} km"
    elif t == "LINK-MP":
        s = f"{cid} LINK to main pipe by gravity {info['km']:.1f} km"
    else:
        s = f"{cid} island low point {info['km']:.1f} km"
    if t in ("SINK", "LOW", "LINK-STP", "LINK-MP") and "to_mp" in info:
        s += (f" | to main pipe invert {info['to_mp'][0]:+.1f} m over {info['to_mp'][1] / 1000:.2f} km"
              f" | to STP {info['to_stp'][0]:+.1f} m over {info['to_stp'][1] / 1000:.2f} km")
    if info.get("agri_plots_crossed"):
        s += f" | link crosses {info['agri_plots_crossed']} agricultural plots"
    return s


def write_dxf(path, pipes, gaps, dropped_geoms, catch_info, catch_polys, catch_colour, joins,
              streams, wadis, main_pipe, built, envelope, stp, title, links=None, basins=None):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 6                  # metres
    doc.header["$LTSCALE"] = 8.0                 # dashes visible at town scale, not a solid line
    doc.header["$PSLTSCALE"] = 0
    for name, col in (("A_SUBMAIN", 7), ("A_LATERAL", 7), ("A_BRANCH", 7), ("A_HEAD_GAP", 8),
                      ("A_HEADS", 8), ("A_ARROWS", 7), ("A_GRADIENT", 8), ("A_JOIN_LINK", 6),
                      ("A_DIRECT_LINK", 6), ("A_BASINS", 1),
                      ("A_OUTLETS", 7), ("A_OUTLET_LABEL", 7), ("A_CATCHMENTS", 7),
                      ("A_CATCH_LABEL", 7), ("A_DROPPED", 1), ("A_STREAMS", 5), ("A_WADI", 4),
                      ("A_MAIN_PIPE", 5), ("A_BUILT_2006", 252), ("A_ENVELOPE", 3),
                      ("A_STP", 6), ("A_TITLE", 7)):
        doc.layers.add(name, color=col)
    msp = doc.modelspace()

    heads = set(p["dn"] for p in pipes)
    for p in pipes:
        col = PALETTE[catch_colour.get(p["catch"], 0)]
        attrs = {"layer": TIER_LAYER[p["tier"]], "color": col,
                 "const_width": TIER_WIDTH[p["tier"]]}
        if p["cls"] == "AGAINST":
            attrs["linetype"] = "DASHDOT"
        elif p["cls"] in ("FLAT", "LEVEL"):
            attrs["linetype"] = "DASHED"
        g = p["geom"]
        msp.add_lwpolyline(list(g.coords), dxfattribs=attrs)
        if g.length >= 12:
            _arrow(msp, g, "A_ARROWS", col, size=5.0 if p["tier"] in ("sub main", "trunk") else 4.0)
        if g.length >= 60:
            m = g.interpolate(0.5 * g.length)
            q = g.interpolate(min(g.length, 0.5 * g.length + 1.0))
            rot = math.degrees(math.atan2(q.y - m.y, q.x - m.x))
            if rot > 90 or rot < -90:
                rot += 180
            msp.add_text(f"{p['grad']:+.2f}%", height=2.0, rotation=rot,
                         dxfattribs={"layer": "A_GRADIENT", "color": col}
                         ).set_placement((m.x, m.y), align=TextEntityAlignment.BOTTOM_CENTER)
        if p["up"] not in heads:
            msp.add_circle(g.coords[0], 2.0, dxfattribs={"layer": "A_HEADS", "color": col})
    for g in gaps:
        msp.add_lwpolyline(list(g.coords), dxfattribs={"layer": "A_HEAD_GAP", "color": 8,
                                                       "linetype": "DASHED"})
    for g in dropped_geoms:
        msp.add_lwpolyline(list(g.coords), dxfattribs={"layer": "A_DROPPED", "color": 1,
                                                       "const_width": 1.0})
    for cid, g in joins.items():
        msp.add_lwpolyline(list(g.coords), dxfattribs={"layer": "A_JOIN_LINK", "color": 6,
                                                       "const_width": 1.5})
        msp.add_circle(g.coords[-1], 5.0, dxfattribs={"layer": "A_JOIN_LINK", "color": 6})
    for cid, g in (links or {}).items():
        msp.add_lwpolyline(list(g.coords), dxfattribs={"layer": "A_DIRECT_LINK", "color": 6,
                                                       "const_width": 2.0, "linetype": "DASHED"})
    for b in (basins or []):
        x, y = b["xy"]
        msp.add_circle((x, y), 6.0, dxfattribs={"layer": "A_BASINS", "color": 1})
        msp.add_text(f"basin: +{b['extra_m']:.1f} m to leave", height=3.0,
                     dxfattribs={"layer": "A_BASINS", "color": 1}
                     ).set_placement((x + 8, y - 6), align=TextEntityAlignment.LEFT)

    for cid, info in catch_info.items():
        x, y = info["outlet"]
        col = OUT_COL[info["type"]]
        msp.add_circle((x, y), 7.0, dxfattribs={"layer": "A_OUTLETS", "color": col})
        if info["type"] != "LOW":
            msp.add_circle((x, y), 4.0, dxfattribs={"layer": "A_OUTLETS", "color": col})
        msp.add_text(outlet_label(cid, info), height=4.0,
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
        msp.add_text(f"{cid} · {info['type']} · {info['km']:.1f} km · sub-main "
                     f"{info['submain_km']:.1f} km · {info['pipes']} pipes · "
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
        for q in parts:
            msp.add_lwpolyline(list(q.coords), dxfattribs={"layer": "A_BUILT_2006", "color": 252})
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


def write_shapes(out_dir, prefix, pipes, gaps, catch_info, catch_polys, joins, epsg=32640):
    os.makedirs(out_dir, exist_ok=True)
    crs = f"EPSG:{epsg}"
    gpd.GeoDataFrame({
        "PIPE_ID": [f"P{i + 1:05d}" for i in range(len(pipes))],
        "TIER": [TIER_NAME[p["tier"]] for p in pipes],
        "ROLE": [p["tier"] for p in pipes],
        "CATCH": [p["catch"] for p in pipes],
        "OUT_TYPE": [catch_info[p["catch"]]["type"] for p in pipes],
        "LEN_M": [round(p["len"], 1) for p in pipes],
        "Z_UP": [round(p["z_up"], 2) for p in pipes],
        "Z_DN": [round(p["z_dn"], 2) for p in pipes],
        "FALL_M": [round(p["fall"], 2) for p in pipes],
        "GRAD_PCT": [round(p["grad"], 3) for p in pipes],
        "CLASS": [p["cls"] for p in pipes],
        "HEAD_HOW": [p.get("head_how", "") for p in pipes],
        "HEAD_OFF": [round(p.get("head_offset", 0.0), 1) for p in pipes],
        "LAYER": [p.get("layer", "") for p in pipes],
        "DN_MM": [int(p.get("dn_mm", 0)) for p in pipes],
        "SLOPE_PCT": [round(p.get("grad_laid", 0.0) * 100, 3) for p in pipes],
        "Q_PEAK_LS": [round(p.get("q_peak_ls", 0.0), 2) for p in pipes],
        "PROPS_UP": [round(p.get("props_up", 0.0), 1) for p in pipes],
        "Q_ULT_M3D": [round(p.get("q_ult_up", 0.0), 2) for p in pipes],
        "Q30_M3D": [round(p.get("q_2030_up", 0.0), 2) for p in pipes],
        "PROPS_30": [round(p.get("props_2030_up", 0.0), 1) for p in pipes],
        "PF": [round(p.get("pf", 0.0), 2) for p in pipes],
        "Q_LOW_LS": [round(p.get("q_low_ls", 0.0), 3) for p in pipes],
        "V_LOW": [round(p.get("v_low", 0.0), 3) for p in pipes],
        "S_MARA_PC": [round(min(p.get("s_mara", 0.0), 9.99) * 100, 3) for p in pipes],
        "CLEANSE": [p.get("cleanse", "") for p in pipes],
        "S_TRAC_PC": [round(p.get("s_trac_design", 0.0) * 100, 3) for p in pipes],
        "S_TRACL_PC": [round(p.get("s_trac_low", 0.0) * 100, 3) for p in pipes],
        "TRAC_OVER": [p.get("trac_over", "") for p in pipes],
        "DEPTH_UP": [round(p.get("depth_up", 0.0), 2) for p in pipes],
        "DEPTH_DN": [round(p.get("depth_dn", 0.0), 2) for p in pipes],
    }, geometry=[p["geom"] for p in pipes], crs=crs).to_file(
        os.path.join(out_dir, f"{prefix}_pipes.shp"))
    if gaps:
        gpd.GeoDataFrame({"KIND": ["head gap"] * len(gaps)}, geometry=gaps, crs=crs).to_file(
            os.path.join(out_dir, f"{prefix}_headgaps.shp"))
    ids = list(catch_info)
    gpd.GeoDataFrame({
        "CATCH": ids, "OUT_TYPE": [catch_info[c]["type"] for c in ids],
        "KM": [round(catch_info[c]["km"], 2) for c in ids],
        "SUBMAIN_KM": [round(catch_info[c]["submain_km"], 2) for c in ids],
        "PIPES": [catch_info[c]["pipes"] for c in ids],
        "SPILL_M": [None if catch_info[c]["spill_m"] is None else round(catch_info[c]["spill_m"], 2)
                    for c in ids],
        "TO_MP_M": [round(catch_info[c]["to_mp"][0], 2) if "to_mp" in catch_info[c] else None for c in ids],
        "TO_MP_D": [round(catch_info[c]["to_mp"][1], 0) if "to_mp" in catch_info[c] else None for c in ids],
        "TO_STP_M": [round(catch_info[c]["to_stp"][0], 2) if "to_stp" in catch_info[c] else None for c in ids],
        "TO_STP_D": [round(catch_info[c]["to_stp"][1], 0) if "to_stp" in catch_info[c] else None for c in ids],
    }, geometry=[Point(catch_info[c]["outlet"]) for c in ids], crs=crs).to_file(
        os.path.join(out_dir, f"{prefix}_outlets.shp"))
    pid = [c for c in ids if c in catch_polys]
    gpd.GeoDataFrame({
        "CATCH": pid, "OUT_TYPE": [catch_info[c]["type"] for c in pid],
        "KM": [round(catch_info[c]["km"], 2) for c in pid],
        "AREA_KM2": [round(catch_polys[c].area / 1e6, 3) for c in pid],
    }, geometry=[catch_polys[c] for c in pid], crs=crs).to_file(
        os.path.join(out_dir, f"{prefix}_catchments.shp"))
    if joins:
        jid = list(joins)
        gpd.GeoDataFrame({"CATCH": jid, "LEN_M": [round(joins[c].length, 1) for c in jid]},
                         geometry=[joins[c] for c in jid], crs=crs).to_file(
            os.path.join(out_dir, f"{prefix}_joins.shp"))


def write_png(path, bounds, pipes, gaps, catch_info, catch_polys, catch_colour, joins, streams,
              main_pipe, built, envelope, stp, title, dpi=130, arrows=True, label=True):
    tab = plt.get_cmap("tab10")
    cmap = lambda k: tab(k % 10)                     # noqa: E731
    fig, ax = plt.subplots(figsize=(15, 11), dpi=dpi)
    for cid, poly in catch_polys.items():
        parts = list(poly.geoms) if hasattr(poly, "geoms") else [poly]
        for p in parts:
            if p.geom_type == "Polygon" and not p.is_empty:
                ax.fill(*p.exterior.xy, color=cmap(catch_colour.get(cid, 0)), alpha=0.10, lw=0)
                ax.plot(*p.exterior.xy, color=cmap(catch_colour.get(cid, 0)), lw=0.7, ls="--")
    for g in built:
        parts = list(g.geoms) if hasattr(g, "geoms") else [g]
        for q in parts:
            ax.plot(*q.xy, color="#c8c8c8", lw=0.4)
    for g, order in streams:
        ax.plot(*g.xy, color="#3b6fd6", lw=0.35 * order, alpha=0.5)
    for g in gaps:
        ax.plot(*g.xy, color="#888888", lw=0.8, ls=":")
    for p in pipes:
        col = cmap(catch_colour.get(p["catch"], 0))
        lw = {"trunk": 3.6, "sub main": 2.6, "lateral": 1.0, "branch": 1.0}[p["tier"]]
        ls = {"NORMAL": "-", "FLAT": "--", "LEVEL": "--", "AGAINST": ":"}[p["cls"]]
        ax.plot(*p["geom"].xy, color=col, lw=lw, ls=ls)
        if arrows and p["len"] >= 15:
            g = p["geom"]
            a = g.interpolate(0.6 * g.length)
            b = g.interpolate(min(g.length, 0.6 * g.length + 1.0))
            ax.annotate("", xy=(b.x, b.y), xytext=(a.x, a.y),
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=0.8, mutation_scale=8))
    for cid, g in joins.items():
        ax.plot(*g.xy, color="magenta", lw=1.6)
    for g in main_pipe:
        ax.plot(*g.xy, color="blue", lw=2.2)
    for cid, info in catch_info.items():
        x, y = info["outlet"]
        if not (bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
            continue
        mk = PNG_MARK[info["type"]]
        colr = PNG_COL[info["type"]]
        ax.plot(x, y, marker=mk, color=colr, ms=8, mec="black", mew=0.5, ls="none")
        if label:
            lab = f"{cid} {info['type']} {info['km']:.1f} km"
            if info["type"] == "SINK":
                lab += f" ~{(info.get('spill_m') or 0.0):.1f} m"
            ax.text(x + 8, y + 8, lab, fontsize=6, color=colr)
    for cid, info in catch_info.items():
        if info["type"].startswith("LINK") and "to_stp" in info:
            x, y = info["outlet"]
            tx, ty = (stp if info["type"] == "LINK-STP" else None) or (None, None)
            if tx is not None and bounds[0] - 3000 <= x <= bounds[2] + 3000:
                ax.plot([x, tx], [y, ty], color="magenta", lw=1.2, ls="--")
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
