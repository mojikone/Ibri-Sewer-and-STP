#!/usr/bin/env python
"""W12 - the three review themes as fully annotated DXF.

    python make_theme_dxf.py                  all three themes
    python make_theme_dxf.py --theme depth    one of structure | depth | exceptions
    python make_theme_dxf.py --scale 1000     size the text for a different plot scale

WHY THIS FILE EXISTS SEPARATELY FROM s8_export's write_dxf(). That one publishes the
deliverable geometry. This one publishes the SAME data as three REVIEW drawings, styled to
match the KMZ and the QGIS themes exactly, so a finding seen on one is findable on the other
two. It reads the published GeoPackage and computes nothing - if a number is wrong here it is
wrong in the design, not in the drawing.

THE LEGIBILITY PROBLEM, AND HOW IT IS SOLVED
    1,485 km, 56,943 chambers and 26,579 conduits cannot all carry a six-line label at any
    scale. Text small enough to fit is too small to read; text large enough to read overlaps
    its neighbours forty times over. So annotation is LAYERED BY DETAIL, not by element:

      ANN-*-KEY    name and size only, ONE line, ON by default. This is the layer you read
                   at 1:2000 while panning - every element identifiable, nothing else.
      ANN-*-FULL   the complete block the engineer specified, OFF by default. Switch it on
                   for the area you are actually looking at, at 1:500.

    Text height is derived from a stated PLOT SCALE (default 1:500) so that a label is a
    fixed size ON PAPER: h_model = TEXT_MM * scale / 1000. At 1:500 that is 1.25 m in model
    space against a 30 m chamber spacing - about one part in twenty-four, which reads.
    THE SCALE IS WRITTEN INTO THE FILE, on layer NOTES, because a drawing whose text size
    has no stated scale cannot be plotted by anyone else.

    Conduit labels sit ALONG the pipe, rotated to its bearing, offset clear of the line, and
    always read left-to-right (a label rotated past vertical is flipped 180 deg). Chamber
    labels sit off the point with a short leader, so the label and the symbol are never
    coincident. Alternate chambers along a run are offset to opposite sides.

THE THREE THEMES - the same three as the KMZ and the QGIS styles
    structure   subnetwork colour; conduit lineweight by bore; pumps, force mains, drop
                chambers and the chamber where each subnetwork meets the main pipe all
                distinct; flow direction; subnetwork polygons in the matching colour.
    depth       the MAGMA ramp on every element, light shallow to dark deep, on FIXED
                published breaks - never a per-run stretch, or the same colour means two
                different depths in two exports.
    exceptions  ONLY what could not be solved, and the count is in the layer name.

EVERY ELEMENT CARRIES WHAT THE ENGINEER ASKED FOR (2026-09-06)
    conduit     name, size, slope, flow, velocity, length, inlet and outlet chamber
    chamber     name, depth, ground level, invert level(s), drops, type
    pump        name, ground level, invert level, head, flow, required storage
    force main  name, size, slope, flow, velocity, length, inlet (pump) and outlet
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Dict, List, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
W12 = os.path.dirname(HERE)
GPKG = os.path.join(W12, "shp", "W12_export.gpkg")
OUTDIR = os.path.join(W12, "dxf")

# --------------------------------------------------------------------------------------
# LEGIBILITY CONSTANTS - all derived from a stated plot scale, none of them design values
# --------------------------------------------------------------------------------------
TEXT_MM = 2.5          # text height ON PAPER, mm. 2.5 mm is the smallest ISO 3098 size that
                       # survives a plot and a scan; 1.8 mm does not.
LEADER_MM = 3.0        # how far a chamber label sits off its symbol, on paper
OFFSET_MM = 1.2        # how far a conduit label sits off its pipe, on paper
DEFAULT_SCALE = 500    # 1:500 - the scale a sewer is set out at


def sizes(scale: int) -> Dict[str, float]:
    """Model-space sizes for a plot scale. h_model = mm_on_paper * scale / 1000."""
    return {"text": TEXT_MM * scale / 1000.0,
            "leader": LEADER_MM * scale / 1000.0,
            "offset": OFFSET_MM * scale / 1000.0,
            "scale": float(scale)}


# --------------------------------------------------------------------------------------
# MAGMA, sampled at 8 stops. Written out rather than importing matplotlib so the drawing
# does not depend on a plotting library being installed.
# --------------------------------------------------------------------------------------
MAGMA = [(252, 253, 191), (254, 217, 166), (252, 173, 131), (245, 128, 126),
         (222, 90, 138), (182, 62, 145), (131, 44, 131), (75, 28, 108)]

# FIXED depth breaks, in metres of cover. PUBLISHED, so two runs are comparable - the whole
# point of not auto-stretching. Chosen to bracket the decisions: 1.30 m is the minimum cover
# (G203-p33), 6 m is the layout-fault trigger from the as-built calibration (the built 2006
# network puts 98.67 % of its length under 6 m), and 12 m is the project cover cap.
DEPTH_BREAKS = [0.0, 1.30, 2.0, 3.0, 4.5, 6.0, 8.0, 12.0]


def magma_for(v: float) -> Tuple[int, int, int]:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return (128, 128, 128)
    i = int(np.searchsorted(DEPTH_BREAKS, float(v), side="right")) - 1
    return MAGMA[max(0, min(len(MAGMA) - 1, i))]


# 24 well-separated hues for subnetworks, cycled. Deliberately NOT a ramp - adjacent
# subnetworks must be told apart, and a ramp makes neighbours look related when they are not.
SUBNET_RGB = [
    (228, 26, 28), (55, 126, 184), (77, 175, 74), (152, 78, 163), (255, 127, 0),
    (166, 86, 40), (247, 129, 191), (153, 153, 153), (0, 139, 139), (190, 174, 212),
    (127, 201, 127), (253, 192, 134), (56, 108, 176), (240, 2, 127), (191, 91, 23),
    (102, 166, 30), (230, 171, 2), (166, 118, 29), (27, 158, 119), (217, 95, 2),
    (117, 112, 179), (231, 41, 138), (102, 102, 102), (26, 133, 255)]


def subnet_rgb(name: str) -> Tuple[int, int, int]:
    """Stable colour for a subnetwork name. Hash-free so it cannot change between runs."""
    s = str(name)
    acc = 0
    for ch in s:
        acc = (acc * 131 + ord(ch)) % 1_000_003
    return SUBNET_RGB[acc % len(SUBNET_RGB)]


def lw_for_dn(dn) -> int:
    """DXF lineweight in 1/100 mm. Thicker as the bore grows - the engineer's rule."""
    try:
        d = float(dn)
    except (TypeError, ValueError):
        return 13
    for lim, lw in ((200, 13), (315, 20), (450, 30), (600, 40),
                    (900, 50), (1200, 70), (1800, 100)):
        if d <= lim:
            return lw
    return 140


# --------------------------------------------------------------------------------------
# formatting - one place, so a number never appears in two shapes on the same drawing
# --------------------------------------------------------------------------------------
def f(v, nd=2, unit="", dash="-"):
    try:
        x = float(v)
        if math.isnan(x):
            return dash
        return f"{x:,.{nd}f}{unit}"
    except (TypeError, ValueError):
        return dash if v is None or str(v) == "" or str(v) == "nan" else str(v)


def conduit_key(r) -> str:
    return f"{r.get('NAME', '-')}  DN{f(r.get('DN'), 0)}"


def conduit_full(r, us: str, ds: str) -> str:
    return (f"{r.get('NAME', '-')}\\P"
            f"DN{f(r.get('DN'), 0)} {r.get('MATERIAL', '') or ''}\\P"
            f"S={f(r.get('SLOPE_LAID'), 3, ' %')} (min {f(r.get('SLOPE_MIN'), 3, ' %')})\\P"
            f"Q={f(r.get('QPK_LS'), 1, ' L/s')}  v={f(r.get('V_PK_MS'), 2, ' m/s')}\\P"
            f"L={f(r.get('LEN_M'), 2, ' m')}\\P"
            f"{us} -> {ds}")


def chamber_key(r) -> str:
    return f"{r.get('NAME', '-')}  {f(r.get('DEPTH_M'), 2, 'm')}"


def chamber_full(r) -> str:
    inv = f(r.get('INV_M'), 3, '')
    drop = r.get("DROP_M")
    dl = ""
    try:
        if float(drop) > 0:
            dl = f"\\Pdrop {f(drop, 2, ' m')} ({r.get('DROP_WHY', '') or r.get('DROP_TYPE', '') or '?'})"
    except (TypeError, ValueError):
        pass
    return (f"{r.get('NAME', '-')}\\P"
            f"{r.get('NODE_KIND', '')}  {r.get('TIER', '')}\\P"
            f"GL {f(r.get('GRD_M'), 3, '')}\\P"
            f"IL {inv}\\P"
            f"depth {f(r.get('DEPTH_M'), 2, ' m')}  cover {f(r.get('COVER_M'), 2, ' m')}"
            f"{dl}")


def pump_key(r) -> str:
    return f"{r.get('NAME', '-')}  {f(r.get('Q_DUTY_LS'), 1, ' L/s')}"


def pump_full(r) -> str:
    return (f"{r.get('NAME', '-')}   ({r.get('ST_TYPE', '')})\\P"
            f"GL {f(r.get('GRD_M'), 3, '')}\\P"
            f"IL {f(r.get('INV_M'), 3, '')}\\P"
            f"head {f(r.get('LIFT_M'), 2, ' m')}\\P"
            f"Q {f(r.get('Q_DUTY_LS'), 1, ' L/s')}\\P"
            f"storage {f(r.get('WELL_M3'), 1, ' m3')}\\P"
            f"serves {f(r.get('N_SUBNET'), 0)} subnet / {f(r.get('CATCH_KM'), 2, ' km')}")


def main_key(r) -> str:
    return f"{r.get('NAME', '-')}  DN{f(r.get('DN'), 0)}"


def main_full(r, us: str, ds: str) -> str:
    slope = "-"
    try:
        if float(r.get("LEN_M")) > 0:
            slope = f(100.0 * float(r.get("STAT_HD_M")) / float(r.get("LEN_M")), 3, " %")
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return (f"{r.get('NAME', '-')}   RISING MAIN\\P"
            f"DN{f(r.get('DN'), 0)} {r.get('MATERIAL', '') or ''}\\P"
            f"static/L = {slope}\\P"
            f"Q {f(r.get('Q_DUTY_LS'), 1, ' L/s')}  v {f(r.get('V_DUTY_MS'), 2, ' m/s')}\\P"
            f"L {f(r.get('LEN_M'), 2, ' m')}\\P"
            f"{us} -> {ds} ({r.get('DS_TYPE', '')})")


# --------------------------------------------------------------------------------------
def _pts(geom) -> List[Tuple[float, float]]:
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "LineString":
        return [(float(x), float(y)) for x, y in geom.coords]
    if geom.geom_type == "MultiLineString":
        out = []
        for g in geom.geoms:
            out.extend((float(x), float(y)) for x, y in g.coords)
        return out
    return []


def _label_anchor(pts) -> Tuple[float, float, float]:
    """Midpoint of a polyline and the bearing there, in degrees, always readable."""
    if len(pts) < 2:
        return (pts[0][0], pts[0][1], 0.0) if pts else (0.0, 0.0, 0.0)
    seg = [(math.dist(pts[i], pts[i + 1]), i) for i in range(len(pts) - 1)]
    tot = sum(d for d, _ in seg)
    half, acc = tot / 2.0, 0.0
    i = seg[-1][1]
    for d, k in seg:
        if acc + d >= half:
            i = k
            break
        acc += d
    (x0, y0), (x1, y1) = pts[i], pts[i + 1]
    x, y = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rot = math.degrees(math.atan2(y1 - y0, x1 - x0))
    if rot > 90 or rot <= -90:          # never upside down
        rot += 180.0
    return x, y, rot


def _perp(rot_deg: float, off: float) -> Tuple[float, float]:
    a = math.radians(rot_deg + 90.0)
    return off * math.cos(a), off * math.sin(a)


# --------------------------------------------------------------------------------------
def build(theme: str, scale: int) -> str:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment

    S = sizes(scale)
    th, leader, offs = S["text"], S["leader"], S["offset"]

    nodes = gpd.read_file(GPKG, layer="nodes")
    reach = gpd.read_file(GPKG, layer="reaches")
    stn = gpd.read_file(GPKG, layer="stations")
    rms = gpd.read_file(GPKG, layer="rising_mains")
    try:
        subs = gpd.read_file(GPKG, layer="subnetworks")
    except Exception:
        subs = gpd.GeoDataFrame(columns=["NAME", "geometry"], geometry="geometry")

    uid2name = dict(zip(nodes.NODE_UID.astype(str), nodes.NAME.astype(str)))

    doc = ezdxf.new("R2013", setup=True)
    doc.header["$INSUNITS"] = 6          # metres
    doc.header["$LWDISPLAY"] = 1         # show lineweights, or "thicker as size grows" is invisible
    msp = doc.modelspace()

    def layer(name, rgb, lw=None, off=False, frozen=False):
        if name in doc.layers:
            return doc.layers.get(name)
        L = doc.layers.add(name)
        L.rgb = rgb
        if lw is not None:
            L.dxf.lineweight = lw
        if off:
            L.off()
        if frozen:
            L.freeze()
        return L

    def mtext(txt, x, y, lay, h, rot=0.0, width=0.0):
        m = msp.add_mtext(txt, dxfattribs={"layer": lay, "char_height": h,
                                           "rotation": rot, "width": width})
        m.set_location((x, y))
        return m

    # ---------------------------------------------------------------- NOTES
    layer("NOTES", (255, 255, 255))
    minx, miny, _, maxy = reach.total_bounds
    note = (f"W12 CONCEPT DESIGN - theme: {theme.upper()}\\P"
            f"PLOTTED FOR 1:{scale}. Text is {TEXT_MM} mm on paper = {th:.2f} m in model "
            f"space. Plot at another scale and the text will not be {TEXT_MM} mm.\\P"
            f"ANNOTATION IS LAYERED: ANN-*-KEY (name and size, ON) and ANN-*-FULL "
            f"(everything the engineer asked for, OFF). Switch FULL on for the area you "
            f"are reading, at 1:{scale}.\\P"
            f"Depth colours use FIXED breaks {DEPTH_BREAKS} m of cover - never a per-run "
            f"stretch, so this drawing and the next one mean the same thing.\\P"
            f"Concept stage: no house connections, no phasing, no costing.")
    mtext(note, float(minx), float(maxy) + 40 * th, "NOTES", th * 1.6, width=160 * th)

    counts: Dict[str, int] = {}

    # ---------------------------------------------------------------- geometry + colour
    if theme == "structure":
        layer("SUBNET-AREA", (200, 200, 200), off=True)
        for _, r in subs.iterrows():
            g = r.geometry
            if g is None or g.is_empty:
                continue
            rgb = subnet_rgb(r.get("NAME", ""))
            lay = f"SUBNET-{r.get('NAME', 'x')}"
            layer(lay, rgb)
            for poly in (g.geoms if g.geom_type.startswith("Multi") else [g]):
                try:
                    msp.add_lwpolyline([(float(x), float(y)) for x, y in poly.exterior.coords],
                                       close=True, dxfattribs={"layer": lay})
                except Exception:
                    pass
        counts["subnetwork polygons"] = len(subs)

    for _, r in reach.iterrows():
        pts = _pts(r.geometry)
        if len(pts) < 2:
            continue
        if theme == "depth":
            cov = r.get("COVER_US")
            try:
                cov = min(float(r.get("COVER_US")), float(r.get("COVER_DN")))
            except (TypeError, ValueError):
                pass
            rgb, lay = magma_for(cov), f"DEPTH-{magma_for(cov)}"
        elif theme == "structure":
            rgb = subnet_rgb(r.get("SUBNET", r.get("NAME", "")[:6]))
            lay = f"PIPE-{r.get('SUBNET', 'x')}"
        else:
            continue                     # exceptions draws only the flagged, below
        layer(lay, rgb, lw=lw_for_dn(r.get("DN")))
        msp.add_lwpolyline(pts, dxfattribs={"layer": lay, "lineweight": lw_for_dn(r.get("DN"))})

    if theme in ("structure", "depth"):
        counts["conduits"] = len(reach)

        # flow direction: one arrow head at the downstream end of every reach
        layer("FLOW-DIR", (90, 90, 90))
        for _, r in reach.iterrows():
            pts = _pts(r.geometry)
            if len(pts) < 2:
                continue
            (x0, y0), (x1, y1) = pts[-2], pts[-1]
            a = math.atan2(y1 - y0, x1 - x0)
            for s in (+1, -1):
                msp.add_line((x1, y1),
                             (x1 - 2.2 * th * math.cos(a + s * 0.42),
                              y1 - 2.2 * th * math.sin(a + s * 0.42)),
                             dxfattribs={"layer": "FLOW-DIR"})

        # chambers, symbol by kind
        KIND_RGB = {"head": (0, 200, 0), "junction": (0, 128, 255), "chamber": (160, 160, 160),
                    "outfall": (255, 0, 0), "drop": (255, 140, 0)}
        for _, r in nodes.iterrows():
            g = r.geometry
            if g is None or g.is_empty:
                continue
            kind = str(r.get("NODE_KIND", "chamber"))
            if theme == "depth":
                rgb, lay = magma_for(r.get("COVER_M")), f"MH-DEPTH-{magma_for(r.get('COVER_M'))}"
            else:
                rgb, lay = KIND_RGB.get(kind, (160, 160, 160)), f"MH-{kind}"
            layer(lay, rgb)
            msp.add_circle((float(g.x), float(g.y)), 1.2 * th, dxfattribs={"layer": lay})
            try:
                if float(r.get("DROP_M") or 0) > 0:
                    layer("MH-DROP", (255, 140, 0))
                    msp.add_circle((float(g.x), float(g.y)), 2.0 * th,
                                   dxfattribs={"layer": "MH-DROP"})
            except (TypeError, ValueError):
                pass
            if str(r.get("JOIN_MAIN", 0)) in ("1", "1.0", "True"):
                layer("MH-JOINS-MAIN", (255, 0, 255))
                msp.add_circle((float(g.x), float(g.y)), 3.0 * th,
                               dxfattribs={"layer": "MH-JOINS-MAIN"})
        counts["chambers"] = len(nodes)

    # ---------------------------------------------------------------- pumps + mains, always
    layer("PUMP", (255, 0, 255), lw=50)
    for _, r in stn.iterrows():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        x, y = float(g.x), float(g.y)
        msp.add_circle((x, y), 4.0 * th, dxfattribs={"layer": "PUMP"})
        msp.add_lwpolyline([(x - 3 * th, y - 3 * th), (x + 3 * th, y - 3 * th),
                            (x, y + 4 * th)], close=True, dxfattribs={"layer": "PUMP"})
    counts["pumping stations"] = len(stn)

    layer("FORCE-MAIN", (255, 0, 255), lw=50)
    for _, r in rms.iterrows():
        pts = _pts(r.geometry)
        if len(pts) >= 2:
            msp.add_lwpolyline(pts, dxfattribs={"layer": "FORCE-MAIN", "lineweight": 50})
    counts["rising mains"] = len(rms)

    # ---------------------------------------------------------------- EXCEPTIONS
    if theme == "exceptions":
        def flagged(df, mask, lay_stem, rgb, radius=None):
            sub = df[mask]
            if not len(sub):
                return
            lay = f"EXC-{lay_stem}-{len(sub)}"      # THE COUNT IS IN THE LAYER NAME
            layer(lay, rgb)
            for _, r in sub.iterrows():
                g = r.geometry
                if g is None or g.is_empty:
                    continue
                if g.geom_type == "Point":
                    msp.add_circle((float(g.x), float(g.y)), (radius or 4.0) * th,
                                   dxfattribs={"layer": lay})
                else:
                    pts = _pts(g)
                    if len(pts) >= 2:
                        msp.add_lwpolyline(pts, dxfattribs={"layer": lay, "lineweight": 50})
            counts[lay_stem] = len(sub)

        cov = nodes.get("COVER_M")
        if cov is not None:
            flagged(nodes, pd.to_numeric(cov, errors="coerce") > 12.0,
                    "COVER-OVER-12M", (255, 0, 0), 5)
            flagged(nodes, (pd.to_numeric(cov, errors="coerce") > 6.0) &
                    (pd.to_numeric(cov, errors="coerce") <= 12.0), "COVER-6-12M", (255, 165, 0), 4)
        if "DROP_WHY" in nodes:
            flagged(nodes, nodes.DROP_WHY.astype(str) == "velocity_cap",
                    "DROP-FOR-VELOCITY", (255, 0, 255), 4)
        if "INLET_FLAG" in nodes:
            flagged(nodes, pd.to_numeric(nodes.INLET_FLAG, errors="coerce").fillna(0) > 0,
                    "INLET-UNDER-90DEG", (0, 200, 255), 3)
        if "JOIN_OFF_M" in nodes:
            flagged(nodes, pd.to_numeric(nodes.JOIN_OFF_M, errors="coerce").fillna(0) > 0,
                    "OUTFALL-OFF-LOW-POINT", (255, 255, 0), 5)
        if "FLAG" in subs:
            flagged(subs, subs.FLAG.astype(str).str.len() > 0, "SUBNET-FLAGGED", (255, 0, 0))
        if "GAP_M" in subs:
            flagged(subs, pd.to_numeric(subs.GAP_M, errors="coerce").fillna(0) > 0,
                    "SUBNET-SHORT-OF-MAIN", (255, 90, 0))
        # A PLOT THAT CANNOT BE CHECKED IS NOT A PLOT THAT CANNOT CONNECT, AND THEY MUST NOT
        # SHARE A LAYER. CAN_CONN = 0 holds both, and on this run 17,461 of the 29,023 zeros
        # are "the check could not run" - 12,334 receiving chambers with no bore and 5,127
        # with no designed invert. Drawing them as one number would tell the client that more
        # than half the town cannot be sewered, which is false. Philosophy sec 8: a check that
        # cannot run is a FAILURE - but it is a DIFFERENT failure, and it is ours, not the
        # ground's. Three layers, each counted in its own name.
        try:
            conn = gpd.read_file(GPKG, layer="connections")
            if "CAN_CONN" in conn:
                bad = pd.to_numeric(conn.CAN_CONN, errors="coerce").fillna(1) == 0
                why = conn.get("CONN_WHY", pd.Series([""] * len(conn))).astype(str)
                no_bore = bad & why.str.startswith("chamber bore unknown")
                no_inv = bad & why.str.startswith("chamber level unknown")
                real = bad & ~no_bore & ~no_inv
                flagged(conn, real, "PLOT-CANNOT-CONNECT", (255, 0, 0), 2)
                flagged(conn, no_bore, "CHECK-CANNOT-RUN-NO-BORE", (120, 120, 255), 2)
                flagged(conn, no_inv, "CHECK-CANNOT-RUN-NO-INVERT", (120, 200, 255), 2)
        except Exception:
            pass

        # The three stations s7 designed and the export rejected. They belong on the
        # exceptions drawing, not silently absent from it - 40 published + 3 rejected = the
        # 43 s7 reports, and a reader who counts symbols must be able to reach 43.
        try:
            rej = gpd.read_file(GPKG, layer="stations_rejected")
            if len(rej):
                lay = f"EXC-STATION-REJECTED-{len(rej)}"
                layer(lay, (255, 0, 0))
                for _, r in rej.iterrows():
                    g = r.geometry
                    if g is not None and not g.is_empty and g.geom_type == "Point":
                        msp.add_circle((float(g.x), float(g.y)), 6.0 * th,
                                       dxfattribs={"layer": lay})
                        mtext(rf"REJECTED {r.get('NAME', '')}\P{r.get('WHY', '')}",
                              float(g.x) + leader, float(g.y) + leader, lay, th * 1.2)
                counts["STATION-REJECTED"] = len(rej)
        except Exception:
            pass

    # ---------------------------------------------------------------- ANNOTATION
    layer("ANN-CONDUIT-KEY", (255, 255, 255))
    layer("ANN-CONDUIT-FULL", (200, 200, 255), off=True)
    layer("ANN-MH-KEY", (255, 255, 255))
    layer("ANN-MH-FULL", (200, 255, 200), off=True)
    layer("ANN-MH-LEADER", (110, 110, 110), off=True)
    layer("ANN-PUMP-KEY", (255, 0, 255))
    layer("ANN-PUMP-FULL", (255, 200, 255), off=True)
    layer("ANN-FM-KEY", (255, 0, 255))
    layer("ANN-FM-FULL", (255, 200, 255), off=True)

    if theme in ("structure", "depth"):
        for _, r in reach.iterrows():
            pts = _pts(r.geometry)
            if len(pts) < 2:
                continue
            x, y, rot = _label_anchor(pts)
            dx, dy = _perp(rot, offs + th * 0.7)
            mtext(conduit_key(r), x + dx, y + dy, "ANN-CONDUIT-KEY", th, rot)
            us = uid2name.get(str(r.get("US_NODE")), str(r.get("US_NODE")))
            ds = uid2name.get(str(r.get("DS_NODE")), str(r.get("DS_NODE")))
            dx2, dy2 = _perp(rot, -(offs + th * 4.5))
            mtext(conduit_full(r, us, ds), x + dx2, y + dy2, "ANN-CONDUIT-FULL", th, rot)

        for i, (_, r) in enumerate(nodes.iterrows()):
            g = r.geometry
            if g is None or g.is_empty:
                continue
            x, y = float(g.x), float(g.y)
            side = 1.0 if (i % 2 == 0) else -1.0        # alternate sides along a run
            lx, ly = x + side * leader, y + leader
            msp.add_line((x, y), (lx, ly), dxfattribs={"layer": "ANN-MH-LEADER"})
            mtext(chamber_key(r), lx, ly, "ANN-MH-KEY", th)
            mtext(chamber_full(r), lx, ly - th * 1.2, "ANN-MH-FULL", th)

    for _, r in stn.iterrows():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        x, y = float(g.x) + leader, float(g.y) + leader
        mtext(pump_key(r), x, y, "ANN-PUMP-KEY", th * 1.4)
        mtext(pump_full(r), x, y - th * 1.8, "ANN-PUMP-FULL", th * 1.2)

    for _, r in rms.iterrows():
        pts = _pts(r.geometry)
        if len(pts) < 2:
            continue
        x, y, rot = _label_anchor(pts)
        dx, dy = _perp(rot, offs + th)
        us = uid2name.get(str(r.get("US_NODE")), str(r.get("US_NODE")))
        ds = uid2name.get(str(r.get("DS_NODE")), str(r.get("DS_NODE")))
        mtext(main_key(r), x + dx, y + dy, "ANN-FM-KEY", th * 1.3, rot)
        dx2, dy2 = _perp(rot, -(offs + th * 5))
        mtext(main_full(r, us, ds), x + dx2, y + dy2, "ANN-FM-FULL", th * 1.2, rot)

    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, f"W12_theme_{theme}_1-{scale}.dxf")
    doc.saveas(out)
    mb = os.path.getsize(out) / 1e6
    print(f"  {os.path.basename(out):44s} {mb:8.1f} MB   " +
          "  ".join(f"{k} {v:,}" for k, v in counts.items()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", choices=["structure", "depth", "exceptions", "all"], default="all")
    ap.add_argument("--scale", type=int, default=DEFAULT_SCALE)
    a = ap.parse_args()
    themes = ["structure", "depth", "exceptions"] if a.theme == "all" else [a.theme]
    print(f"W12 theme DXF  -  plotted for 1:{a.scale}, text {TEXT_MM} mm on paper "
          f"= {sizes(a.scale)['text']:.2f} m model")
    for t in themes:
        build(t, a.scale)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
