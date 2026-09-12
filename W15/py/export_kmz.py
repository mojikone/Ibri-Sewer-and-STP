"""export_kmz — the stage A network as a KMZ for Google Earth (engineer, 2026-09-12): every
subnetwork in its own folder under its convergence group, one colour per subnetwork, sub
mains thick, the main pipe, the guide, and every outlet in a Points layer mirroring the tree.

    python export_kmz.py [run folder]              writes <run folder>/kmz/W15_A_network.kmz
    python export_kmz.py --no-labels [run folder]  the same with no label on any point,
                                                   as W15_A_network_nolabels.kmz

Plain KML, no library: lines in WGS84 with six decimals, laterals and branches merged into
one placemark per subnetwork to keep the file light, sub mains one placemark each with their
size, gradient, flow and depth in the balloon. Three overlays, off until ticked: flow arrows
on the sub mains, the pipes deeper than 12 m, and the convergence groups as outlines.
"""
import html
import json
import math
import os
import sys
import zipfile

import geopandas as gpd
import numpy as np
from pyproj import Transformer
from shapely.ops import transform

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_built as cfg   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
NO_LABELS = "--no-labels" in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = ARGS[0] if ARGS else os.path.dirname(HERE)
LABEL = "<LabelStyle><scale>0</scale></LabelStyle>" if NO_LABELS else ""   # Google Earth labels points only
TO_WGS = Transformer.from_crs(f"EPSG:{cfg.EPSG}", "EPSG:4326", always_xy=True)

# ten strong colours for the subnetworks; red is kept for the sink points and the deep overlay,
# yellow for the main pipe, magenta for the guide
PALETTE = ["1f77b4", "ff7f0e", "2ca02c", "9467bd", "17becf", "e377c2", "8c564b", "1b9e77", "66a61e", "7570b3"]
NEAR_M = 150.0      # subnetworks closer than this get different colours


def colour_near(polys, near_m=NEAR_M, n=len(PALETTE)):
    """A colour index per catchment: catchments within near_m of each other differ, the
    palette spread evenly (Welsh-Powell order, then the least-used colour that is free)."""
    from shapely.strtree import STRtree
    ids = list(polys); geoms = [polys[i] for i in ids]
    tree = STRtree(geoms)
    nb = {i: set() for i in ids}
    for k, g in enumerate(geoms):
        for j in tree.query(g.buffer(near_m)):
            if j != k:
                nb[ids[k]].add(ids[j]); nb[ids[j]].add(ids[k])
    order = sorted(ids, key=lambda i: -len(nb[i]))
    colour, used = {}, [0] * n
    for i in order:
        taken = {colour[j] for j in nb[i] if j in colour}
        free = [c for c in range(n) if c not in taken] or list(range(n))
        c = min(free, key=lambda c: used[c])
        colour[i] = c; used[c] += 1
    return colour


def kml_colour(hex_rgb, alpha="ff"):
    r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
    return f"{alpha}{b}{g}{r}"


def wgs(geom):
    return transform(TO_WGS.transform, geom)


def coords(line):
    return " ".join(f"{x:.6f},{y:.6f},0" for x, y in line.coords)


def line_xml(geom):
    g = wgs(geom.simplify(0.3))
    if g.geom_type == "LineString":
        return f"<LineString><tessellate>1</tessellate><coordinates>{coords(g)}</coordinates></LineString>"
    return "<MultiGeometry>" + "".join(f"<LineString><tessellate>1</tessellate><coordinates>{coords(p)}</coordinates></LineString>" for p in g.geoms) + "</MultiGeometry>"


def poly_xml(poly):
    g = wgs(poly)
    out = f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{coords(g.exterior)}</coordinates></LinearRing></outerBoundaryIs>"
    out += "".join(f"<innerBoundaryIs><LinearRing><coordinates>{coords(r)}</coordinates></LinearRing></innerBoundaryIs>" for r in g.interiors)
    return out + "</Polygon>"


def point_xml(x, y):
    lon, lat = TO_WGS.transform(x, y)
    return f"<Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point>"


def esc(s):
    return html.escape(str(s), quote=True)


def main():
    shp = os.path.join(OUT, "shp")
    pipes = gpd.read_file(os.path.join(shp, "W13_A_tree_pipes.shp"))
    outlets = gpd.read_file(os.path.join(shp, "W13_A_tree_outlets.shp"))
    polys = gpd.read_file(os.path.join(shp, "W13_A_tree_catchments.shp"))
    groups = json.load(open(os.path.join(OUT, "run", "groups.json"), encoding="utf-8"))
    rep = json.load(open(os.path.join(OUT, "run", "stage_a.json"), encoding="utf-8"))
    table = {c["id"]: c for c in rep["catchment_table"]}
    colour_idx = colour_near({r.CATCH: r.geometry for r in polys.itertuples() if r.geometry is not None})
    role_col = "ROLE" if "ROLE" in pipes.columns else "TIER"
    date = rep.get("date", "")
    parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
             f"<name>W15 stage A - the whole network</name>",
             "<description>Stage A layout: the streets read, sub mains first, laterals hung on them, sized on the plots' own flows, "
             "laid at Table 11; one colour per subnetwork; sub mains thick; a folder per subnetwork under the group it converges to; "
             "the pockets' sink points in their own folder. Depths are stage A's quick lay, not the real lay.</description>"]
    # styles
    for i, c in enumerate(PALETTE):
        parts.append(f'<Style id="sm{i}"><LineStyle><color>{kml_colour(c)}</color><width>4.5</width></LineStyle></Style>')
        parts.append(f'<Style id="lat{i}"><LineStyle><color>{kml_colour(c, "dd")}</color><width>1.6</width></LineStyle></Style>')
    parts.append('<Style id="mainpipe"><LineStyle><color>ff00ffff</color><width>7</width></LineStyle></Style>')
    parts.append('<Style id="guide"><LineStyle><color>ffff00ff</color><width>5</width></LineStyle></Style>')
    parts.append(f'<Style id="join">{LABEL}<IconStyle><color>ffff7f00</color><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle></Style>')
    parts.append(f'<Style id="sink">{LABEL}<IconStyle><color>ff0000ff</color><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/triangle.png</href></Icon></IconStyle></Style>')
    parts.append(f'<Style id="low">{LABEL}<IconStyle><color>ff00a5ff</color><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/square.png</href></Icon></IconStyle></Style>')
    parts.append(f'<Style id="stp">{LABEL}<IconStyle><color>ffff00ff</color><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/star.png</href></Icon></IconStyle></Style>')
    parts.append(f'<Style id="link">{LABEL}<IconStyle><color>ffff00ff</color><scale>0.9</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/diamond.png</href></Icon></IconStyle></Style>')
    # the main pipe and the guide
    mp = gpd.read_file(cfg.MAIN_PIPE)
    parts.append("<Folder><name>Main pipe (as drawn, %.1f km)</name>" % (mp.length.sum() / 1000))
    for i, g in enumerate(mp.geometry):
        if g is None or g.is_empty:
            continue
        parts.append(f"<Placemark><name>main pipe {i + 1}</name><styleUrl>#mainpipe</styleUrl>{line_xml(g)}</Placemark>")
    parts.append("</Folder>")
    if getattr(cfg, "GUIDE_SHP", None) and os.path.exists(cfg.GUIDE_SHP):
        gd = gpd.read_file(cfg.GUIDE_SHP)
        parts.append("<Folder><name>Sub main guide (engineer, %.1f km)</name>" % (gd.length.sum() / 1000))
        for i, g in enumerate(gd.geometry):
            parts.append(f"<Placemark><name>guide {i + 1}</name><styleUrl>#guide</styleUrl>{line_xml(g)}</Placemark>")
        parts.append("</Folder>")
    points_at = len(parts)                 # the Points layer goes here, after the main pipe and the guide
    # the subnetworks, by convergence group
    by_catch = {c: df for c, df in pipes.groupby("CATCH")}
    out_by = {r.CATCH: r for r in outlets.itertuples()}
    n_sub = 0
    pts = ["<Folder><name>Points: the outlets, by group and subnetwork</name>"]   # one layer to manage
    for gname, ginfo in groups["groups"].items():
        parts.append(f"<Folder><name>{esc(gname)}: {ginfo['subnetworks']} subnetworks, {ginfo['km']} km</name>")
        pts.append(f"<Folder><name>{esc(gname)}</name>")
        ids = sorted(ginfo["ids"], key=lambda c: -table.get(c, {}).get("km", 0))
        for cid in ids:
            df = by_catch.get(cid)
            if df is None:
                continue
            t = table.get(cid, {})
            ci = colour_idx.get(cid, 0) % len(PALETTE)
            o = out_by.get(cid)
            typ = t.get("type", "")
            name = f"{cid} · {typ} · {t.get('km', 0):.1f} km"
            parts.append(f"<Folder><name>{esc(name)}</name>")
            # the outlet, in the Points layer
            if o is not None:
                style = {"JOIN": "join", "SINK": "sink", "LOW": "low", "STP": "stp"}.get(typ, "link")
                desc = (f"{cid}: outlet {typ}; {t.get('km', 0):.1f} km, {t.get('pipes', 0)} pipes, sub mains {t.get('submain_km', 0):.1f} km"
                        + (f"; spill {t['spill_m']:.1f} m" if t.get("spill_m") else "")
                        + (f"; to the main pipe {t['to_mp'][0]:+.1f} m over {t['to_mp'][1]:.0f} m" if t.get("to_mp") else ""))
                pts.append(f"<Folder><name>{esc(name)}</name><Placemark><name>{esc(cid + ' outlet ' + typ)}</name><description>{esc(desc)}</description>"
                           f"<styleUrl>#{style}</styleUrl>{point_xml(o.geometry.x, o.geometry.y)}</Placemark></Folder>")
            # sub mains, one placemark each
            sm = df[df[role_col].isin(["sub main", "trunk"])]
            for p in sm.itertuples():
                desc = (f"sub main, DN{int(p.DN_MM)}, {p.LEN_M:.0f} m, ground {p.GRAD_PCT:.2f} %, "
                        + (f"laid {p.SLOPE_PCT:.3f} %, " if hasattr(p, "SLOPE_PCT") else "")
                        + f"peak {p.Q_PEAK_LS:.1f} l/s, depth {p.DEPTH_UP:.1f} to {p.DEPTH_DN:.1f} m")
                parts.append(f"<Placemark><name>{p.PIPE_ID}</name><description>{esc(desc)}</description><styleUrl>#sm{ci}</styleUrl>{line_xml(p.geometry)}</Placemark>")
            # laterals and branches, merged
            lt = df[~df[role_col].isin(["sub main", "trunk"])]
            if len(lt):
                from shapely.geometry import MultiLineString
                geom = MultiLineString([g for g in lt.geometry if g is not None])
                desc = f"{len(lt)} laterals and branches, {lt.LEN_M.sum() / 1000:.1f} km, deepest {lt.DEPTH_DN.max():.1f} m"
                parts.append(f"<Placemark><name>{esc(cid + ' laterals')}</name><description>{esc(desc)}</description><styleUrl>#lat{ci}</styleUrl>{line_xml(geom)}</Placemark>")
            parts.append("</Folder>")
            n_sub += 1
        parts.append("</Folder>")
        pts.append("</Folder>")
    pts.append("</Folder>")
    parts[points_at:points_at] = pts
    # --- overlays, switched off, for reading the drawing ---------------------------------
    # flow arrows: one per sub main at its midpoint, heading from its last segment (the
    # geometry runs upstream to downstream)
    parts.append(f'<Style id="arrow">{LABEL}<IconStyle><color>ff000000</color><scale>0.6</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/arrow.png</href></Icon></IconStyle></Style>')
    sm_all = pipes[pipes[role_col].isin(["sub main", "trunk"])]
    parts.append(f"<Folder><name>Flow arrows on the sub mains ({len(sm_all)})</name><visibility>0</visibility>")
    for pr in sm_all.itertuples():
        g = pr.geometry
        if g is None or g.is_empty:
            continue
        c = list(g.coords)
        (x0, y0), (x1, y1) = c[-2], c[-1]
        hdg = (math.degrees(math.atan2(x1 - x0, y1 - y0)) + 360) % 360
        m = g.interpolate(0.5, normalized=True)
        parts.append(f"<Placemark><visibility>0</visibility><styleUrl>#arrow</styleUrl><Style><IconStyle><heading>{hdg:.0f}</heading></IconStyle></Style>{point_xml(m.x, m.y)}</Placemark>")
    parts.append("</Folder>")
    # pipes deeper than the 12 m rule at stage A's quick lay
    deep = pipes[pipes.DEPTH_DN > 12.0]
    parts.append('<Style id="deep"><LineStyle><color>ff0000ff</color><width>6</width></LineStyle></Style>')
    parts.append(f"<Folder><name>Deeper than 12 m at stage A ({len(deep)} pipes, {deep.LEN_M.sum() / 1000:.1f} km)</name><visibility>0</visibility>")
    for pr in deep.sort_values("DEPTH_DN", ascending=False).itertuples():
        desc = f"{pr.CATCH} {pr.ROLE}, DN{int(pr.DN_MM)}, depth {pr.DEPTH_UP:.1f} to {pr.DEPTH_DN:.1f} m, laid {pr.SLOPE_PCT:.3f} %"
        parts.append(f"<Placemark><visibility>0</visibility><name>{pr.PIPE_ID} {pr.DEPTH_DN:.1f} m</name><description>{esc(desc)}</description><styleUrl>#deep</styleUrl>{line_xml(pr.geometry)}</Placemark>")
    parts.append("</Folder>")
    # the convergence groups as outlines
    gpath = os.path.join(shp, "W15_A_groups.shp")
    if os.path.exists(gpath):
        gp = gpd.read_file(gpath)
        gp["G"] = gp["GROUP"].str.replace(" (pocket)", "", regex=False)
        parts.append("<Folder><name>Convergence groups (outlines)</name><visibility>0</visibility>")
        for k, (gname, sub) in enumerate(gp.groupby("G")):
            col = PALETTE[k % len(PALETTE)]
            parts.append(f'<Style id="grp{k}"><LineStyle><color>{kml_colour(col)}</color><width>3</width></LineStyle><PolyStyle><color>{kml_colour(col, "40")}</color></PolyStyle></Style>')
            u = sub.geometry.union_all().simplify(5.0)
            polys_ = [u] if u.geom_type == "Polygon" else list(u.geoms)
            geo = "<MultiGeometry>" + "".join(poly_xml(q) for q in polys_) + "</MultiGeometry>"
            parts.append(f"<Placemark><visibility>0</visibility><name>{esc(gname)}</name><styleUrl>#grp{k}</styleUrl>{geo}</Placemark>")
        parts.append("</Folder>")
    parts.append("</Document></kml>")
    os.makedirs(os.path.join(OUT, "kmz"), exist_ok=True)
    path = os.path.join(OUT, "kmz", "W15_A_network_nolabels.kmz" if NO_LABELS else "W15_A_network.kmz")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("doc.kml", "\n".join(parts))
    print(f"{path}: {n_sub} subnetworks, {os.path.getsize(path) / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
