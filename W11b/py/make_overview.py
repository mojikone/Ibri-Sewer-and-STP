"""One KMZ and one DXF showing the same four things, so the design can be judged at a glance.

    subnetworks, each its own colour
    pumping stations
    force mains
    a boundary around any area that cannot be connected, with its plots inside it

Small and fast on purpose: each subnetwork is dissolved to one line before writing. 56,000
individual reaches make a file that will not pan, and at the zoom you judge a layout from you
cannot see one reach anyway.

    python make_overview.py
"""
import colorsys
import math
import os
import sys
import warnings
import zipfile
from xml.sax.saxutils import escape

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import MultiPoint

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
W11B = os.path.dirname(HERE)
REPO = os.path.dirname(W11B)
BASE = os.path.dirname(os.path.dirname(REPO))

EXPORT = os.path.join(W11B, "shp", "W11b_export.gpkg")
FLOWS = os.path.join(W11B, "shp", "W11b_flows.gpkg")
PLOTS = os.path.join(REPO, "W10", "shp", "W10_plot_loads.gpkg")
KMZ = os.path.join(W11B, "kmz", "W11b_overview.kmz")
DXF = os.path.join(W11B, "dxf", "W11b_overview.dxf")

UTM, WGS = 32640, 4326


def palette(n):
    """Golden-ratio hue steps, so subnetworks that touch on the map do not share a shade."""
    out = []
    for i in range(n):
        h = (i * 0.61803398875) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.62 + 0.28 * ((i % 3) / 2), 0.72 + 0.24 * (i % 2))
        out.append((int(r * 255), int(g * 255), int(b * 255)))
    return out


def kml_rgb(c):
    """KML is aabbggrr - reversed, alpha first."""
    return f"ff{c[2]:02x}{c[1]:02x}{c[0]:02x}"


def aci(c):
    """Nearest AutoCAD colour index. DXF true colour is cleaner but ACI survives more CAD
    round-trips, and this file exists to be opened, not to be perfect."""
    r, g, b = c
    return 1 + int((0.3 * r + 0.59 * g + 0.11 * b) / 256 * 250) % 250


def lines_of(geom):
    parts = geom.geoms if geom.geom_type.startswith("Multi") else [geom]
    return [list(p.coords) for p in parts
            if p.geom_type == "LineString" and len(p.coords) > 1]


def load():
    r = gpd.read_file(EXPORT, layer="reaches").to_crs(UTM)
    trunk = gpd.read_file(EXPORT, layer="trunk").to_crs(UTM)
    st = gpd.read_file(EXPORT, layer="stations").to_crs(UTM)
    try:
        rm = gpd.read_file(EXPORT, layer="rising_mains").to_crs(UTM)
    except Exception:
        rm = gpd.GeoDataFrame(geometry=[], crs=UTM)
    return r, trunk, st, rm


def unconnected_areas(r, plots):
    """A boundary around every plot the network does not reach.

    Not 'a polygon per orphan pipe' - the engineer asked for the AREA, with its plots inside,
    because that is the thing someone has to make a decision about: serve it another way, or
    do not serve it.
    """
    if plots is None or not len(plots):
        return gpd.GeoDataFrame(geometry=[], crs=UTM)
    served = r.geometry.union_all().buffer(60.0)     # 60 m, the frontage distance used
    load_col = next((c for c in ("Q_ADF_M3D", "QADF_M3D") if c in plots.columns), None)
    p = plots.copy()
    if load_col:
        p = p[pd.to_numeric(p[load_col], errors="coerce").fillna(0) > 0]
    miss = p[~p.geometry.centroid.within(served)]
    if not len(miss):
        return gpd.GeoDataFrame(geometry=[], crs=UTM)
    # cluster what is missed, then wrap each cluster - a single hull round everything would
    # enclose the whole wilayat and say nothing
    # Cluster with a KD-tree and union-find rather than sklearn, which is not installed here
    # and is a heavy dependency for one call. Same idea as DBSCAN: plots within EPS of each
    # other are one area, and an area needs MIN_PLOTS members to be worth drawing a boundary
    # round - a lone plot is a connection question, not a servicing area.
    from scipy.spatial import cKDTree
    EPS, MIN_PLOTS = 400.0, 8
    xy = np.c_[miss.geometry.centroid.x, miss.geometry.centroid.y]
    parent = list(range(len(xy)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    tree = cKDTree(xy)
    for a, b in tree.query_pairs(EPS):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups = {}
    for i in range(len(xy)):
        groups.setdefault(find(i), []).append(i)
    lab = np.full(len(xy), -1)
    for k, (_root, members) in enumerate(
            sorted((g for g in groups.items() if len(g[1]) >= MIN_PLOTS),
                   key=lambda g: -len(g[1]))):
        lab[members] = k
    rows = []
    for k in sorted(set(lab)):
        if k < 0:
            continue
        sel = miss[lab == k]
        hull = MultiPoint(list(sel.geometry.centroid)).convex_hull.buffer(120.0)
        rows.append(dict(AREA_ID=f"UNSERVED-{k + 1:03d}", N_PLOT=len(sel),
                         Q_M3D=round(float(pd.to_numeric(sel[load_col], errors="coerce").sum()), 1)
                         if load_col else 0.0,
                         KM2=round(hull.area / 1e6, 2), geometry=hull))
    return gpd.GeoDataFrame(rows, crs=UTM), len(miss)



def connections(r, trunk, nodes):
    """Where each subnetwork discharges, which way the flow is going there, and how far it
    still is from the main pipe.

    The last part is the one worth seeing. A subnetwork whose outfall sits 800 m from the
    trunk is not connected to it - it is a subnetwork with an unanswered question, and on a
    drawing that reads exactly like one that IS connected unless the gap is drawn.
    """
    out = nodes[nodes.get("IS_OUTFALL", 0).astype(float) > 0].copy() \
        if "IS_OUTFALL" in nodes.columns else \
        nodes[nodes.get("NODE_KIND", "").astype(str) == "outfall"].copy()
    if not len(out):
        return gpd.GeoDataFrame(geometry=[], crs=UTM)

    tline = trunk.geometry.union_all()
    # the reach ARRIVING at each outfall gives the bearing - the direction flow is travelling
    last = {}
    for u, v, g in zip(r.US_NODE.astype(str), r.DS_NODE.astype(str), r.geometry):
        last.setdefault(v, g)
    qcol = "QPK_LS" if "QPK_LS" in r.columns else ("QADF_M3D" if "QADF_M3D" in r.columns else None)
    qof = {}
    if qcol is not None:
        for v, q in zip(r.DS_NODE.astype(str), pd.to_numeric(r[qcol], errors="coerce")):
            qof[v] = max(qof.get(v, 0.0), float(q or 0.0))
    sub_of = dict(zip(r.DS_NODE.astype(str), r.get("SUBNET", pd.Series(dtype=object))))

    rows = []
    for _, nd in out.iterrows():
        uid = str(nd.NODE_UID)
        pt = nd.geometry
        g = last.get(uid)
        bearing = 0.0
        if g is not None:
            cs = list(g.coords)
            if len(cs) >= 2:
                (x0, y0), (x1, y1) = cs[-2][:2], cs[-1][:2]
                bearing = math.atan2(y1 - y0, x1 - x0)
        gap = float(pt.distance(tline))
        rows.append(dict(NODE_UID=uid, SUBNET=str(sub_of.get(uid, "")),
                         Q=round(qof.get(uid, 0.0), 1), BEARING=bearing,
                         GAP_M=round(gap, 1), geometry=pt))
    return gpd.GeoDataFrame(rows, crs=UTM)


def arrowhead(x, y, bearing, size=28.0):
    """Two short lines forming an open V pointing along `bearing`. Drawn as geometry rather
    than a block so the DXF opens the same way in every CAD package."""
    back = bearing + math.pi
    a = (x + size * math.cos(back + 0.42), y + size * math.sin(back + 0.42))
    b = (x + size * math.cos(back - 0.42), y + size * math.sin(back - 0.42))
    return [[a, (x, y)], [(x, y), b]]


def flow_arrows(r, every_m=600.0, size=22.0):
    """One arrow every `every_m` along the bigger pipes, pointing the way the flow goes.

    Only on main and sub-main tiers: an arrow on every lateral would be a grey smear at the
    zoom anyone actually reads this at.
    """
    keep = r[r.get("TIER", pd.Series("", index=r.index)).astype(str)
             .str.contains("main", case=False, na=False)] if "TIER" in r.columns else r
    segs = []
    run = 0.0
    for g in keep.geometry:
        parts = g.geoms if g.geom_type.startswith("Multi") else [g]
        for part in parts:
            cs = list(part.coords)
            for i in range(len(cs) - 1):
                (x0, y0), (x1, y1) = cs[i][:2], cs[i + 1][:2]
                d = math.hypot(x1 - x0, y1 - y0)
                run += d
                if run >= every_m and d > 1.0:
                    run = 0.0
                    segs += arrowhead((x0 + x1) / 2, (y0 + y1) / 2,
                                      math.atan2(y1 - y0, x1 - x0), size)
    return segs


def main():
    if not os.path.exists(EXPORT):
        raise SystemExit("no export yet: " + EXPORT)
    r, trunk, st, rm = load()

    key = next((c for c in ("SUBNET", "SUBNET_ID", "PACKAGE") if c in r.columns), None)
    r["_km"] = r.geometry.length / 1000.0
    sub = r.dissolve(by=key, aggfunc={"_km": "sum"}).reset_index()
    sub = sub.sort_values("_km", ascending=False).reset_index(drop=True)
    cols = palette(len(sub))

    plots = gpd.read_file(PLOTS).to_crs(UTM) if os.path.exists(PLOTS) else None
    res = unconnected_areas(r, plots)
    unserved, n_miss = (res if isinstance(res, tuple) else (res, 0))

    # a station with nothing upstream cannot be a real station - flag, never hide
    import networkx as nx
    G = nx.DiGraph()
    G.add_edges_from(zip(r.US_NODE.astype(str), r.DS_NODE.astype(str)))
    def upstream(u):
        return len(nx.ancestors(G, u)) if u in G else -1
    st = st.copy()
    st["_UP"] = [upstream(str(x)) for x in
                 (st["ANCHOR_ND"] if "ANCHOR_ND" in st.columns else st["NODE_UID"])]

    nodes = gpd.read_file(EXPORT, layer="nodes").to_crs(UTM)
    conn = connections(r, trunk, nodes)
    arrows = flow_arrows(r)

    _kmz(sub, cols, trunk, st, rm, unserved, conn)
    _dxf(sub, cols, trunk, st, rm, unserved, conn, arrows)

    q = pd.to_numeric(st.get("Q_DUTY_LS"), errors="coerce").fillna(0)
    print(f"{KMZ}\n{DXF}")
    print(f"  {len(sub):,} subnetworks, {r['_km'].sum():,.1f} km")
    print(f"  main pipe {trunk.geometry.length.sum() / 1000:,.1f} km")
    print(f"  {len(st)} stations, duty {q.min():.1f}-{q.max():.1f} L/s"
          f"   ({int((st['_UP'] <= 0).sum())} with NOTHING upstream - flagged)")
    print(f"  {len(rm):,} force mains, {rm.geometry.length.sum() / 1000:,.2f} km"
          if len(rm) else "  force mains: NONE published")
    print(f"  {len(unserved)} unconnected areas holding {n_miss:,} plots")
    if len(conn):
        gap = pd.to_numeric(conn.GAP_M, errors="coerce")
        print(f"  {len(conn)} subnetwork outfalls; distance to the main pipe: "
              f"median {gap.median():.0f} m, p90 {gap.quantile(0.9):,.0f} m, "
              f"max {gap.max():,.0f} m")
        print(f"     touching the main pipe (within 50 m): {int((gap <= 50).sum())} of {len(conn)}")
    print(f"  {len(arrows) // 2} flow arrows")
    return 0


def _kmz(sub, cols, trunk, st, rm, unserved, conn=None):
    s4 = sub.to_crs(WGS); t4 = trunk.to_crs(WGS); p4 = st.to_crs(WGS)
    r4 = rm.to_crs(WGS) if len(rm) else rm
    u4 = unserved.to_crs(WGS) if len(unserved) else unserved
    P = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
         '<name>W11b overview</name>']
    for i, c in enumerate(cols):
        P.append(f'<Style id="s{i}"><LineStyle><color>{kml_rgb(c)}</color><width>2.2</width>'
                 f'</LineStyle></Style>')
    P.append('<Style id="trunk"><LineStyle><color>ff0000ff</color><width>6</width></LineStyle></Style>')
    P.append('<Style id="rm"><LineStyle><color>ff00a5ff</color><width>4</width></LineStyle></Style>')
    P.append('<Style id="unsv"><LineStyle><color>ff0000ff</color><width>3</width></LineStyle>'
             '<PolyStyle><color>400000ff</color></PolyStyle></Style>')
    for i, sc in enumerate((0.8, 1.1, 1.5, 2.0, 2.6)):
        P.append(f'<Style id="p{i}"><IconStyle><color>ff00ffff</color><scale>{sc}</scale>'
                 f'<Icon><href>http://maps.google.com/mapfiles/kml/shapes/donut.png</href>'
                 f'</Icon></IconStyle></Style>')
    P.append('<Style id="pbad"><IconStyle><color>ff0000ff</color><scale>1.4</scale>'
             '<Icon><href>http://maps.google.com/mapfiles/kml/shapes/caution.png</href>'
             '</Icon></IconStyle></Style>')

    P.append(f'<Folder><name>Subnetworks ({len(s4):,})</name><open>0</open>')
    for i, row in s4.iterrows():
        segs = lines_of(row.geometry)
        if not segs:
            continue
        P.append(f'<Placemark><name>{escape(str(row.iloc[0]))} &#183; {row["_km"]:.1f} km</name>'
                 f'<styleUrl>#s{i}</styleUrl><MultiGeometry>')
        for s in segs:
            P.append('<LineString><tessellate>1</tessellate><coordinates>' +
                     " ".join(f"{x:.6f},{y:.6f},0" for x, y in s) +
                     '</coordinates></LineString>')
        P.append('</MultiGeometry></Placemark>')
    P.append('</Folder>')

    P.append('<Folder><name>Main pipe - CLIENT INPUT</name><open>1</open>')
    for _, row in t4.iterrows():
        for s in lines_of(row.geometry):
            P.append('<Placemark><styleUrl>#trunk</styleUrl><LineString><tessellate>1</tessellate>'
                     '<coordinates>' + " ".join(f"{x:.6f},{y:.6f},0" for x, y in s) +
                     '</coordinates></LineString></Placemark>')
    P.append('</Folder>')

    if len(r4):
        P.append(f'<Folder><name>Force mains ({len(r4)})</name><open>1</open>')
        for _, row in r4.iterrows():
            for s in lines_of(row.geometry):
                P.append('<Placemark><styleUrl>#rm</styleUrl><LineString><tessellate>1</tessellate>'
                         '<coordinates>' + " ".join(f"{x:.6f},{y:.6f},0" for x, y in s) +
                         '</coordinates></LineString></Placemark>')
        P.append('</Folder>')

    q = pd.to_numeric(p4.get("Q_DUTY_LS"), errors="coerce").fillna(0)
    lift = pd.to_numeric(p4.get("LIFT_M"), errors="coerce").fillna(0)
    band = q.rank(pct=True).fillna(0)
    P.append(f'<Folder><name>Pumping stations ({len(p4)})</name><open>1</open>')
    for j, (_, row) in enumerate(p4.iterrows()):
        g = row.geometry
        if g is None or g.is_empty:
            continue
        pt = g if g.geom_type == "Point" else g.centroid
        bad = row["_UP"] <= 0
        style = "pbad" if bad else f'p{min(4, int(band.iloc[j] * 5))}'
        note = " &#8212; NOTHING UPSTREAM, review" if bad else ""
        P.append(f'<Placemark><name>{escape(str(row.get("NODE_REF", "")))}</name>'
                 f'<description>duty {q.iloc[j]:.1f} L/s &#183; lift {lift.iloc[j]:.1f} m'
                 f'{note}</description><styleUrl>#{style}</styleUrl>'
                 f'<Point><coordinates>{pt.x:.6f},{pt.y:.6f},0</coordinates></Point></Placemark>')
    P.append('</Folder>')

    if len(u4):
        P.append(f'<Folder><name>NOT CONNECTED - {len(u4)} areas</name><open>1</open>')
        for _, row in u4.iterrows():
            ring = list(row.geometry.exterior.coords)
            P.append(f'<Placemark><name>{escape(str(row.AREA_ID))} &#183; {int(row.N_PLOT)} plots'
                     f' &#183; {row.Q_M3D:.0f} m3/d</name><styleUrl>#unsv</styleUrl>'
                     f'<Polygon><outerBoundaryIs><LinearRing><coordinates>' +
                     " ".join(f"{x:.6f},{y:.6f},0" for x, y in ring) +
                     '</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>')
        P.append('</Folder>')

    if conn is not None and len(conn):
        c4 = conn.to_crs(WGS)
        P.append(f'<Style id="cx"><IconStyle><color>ffff9000</color><scale>1.1</scale>'
                 f'<Icon><href>http://maps.google.com/mapfiles/kml/shapes/arrow.png</href>'
                 f'</Icon><heading>0</heading></IconStyle></Style>')
        P.append(f'<Folder><name>Subnetwork connections to the main pipe ({len(c4)})</name>'
                 f'<open>1</open>')
        for _, c in c4.iterrows():
            hdg = (90.0 - math.degrees(c.BEARING)) % 360.0
            gaptxt = (f' &#8212; NOT AT MAIN, {c.GAP_M:,.0f} m short'
                      if c.GAP_M > 50 else '')
            P.append(f'<Placemark><name>{escape(str(c.SUBNET))} &#183; {c.Q:.0f} L/s'
                     f'{gaptxt}</name>'
                     f'<Style><IconStyle><color>ffff9000</color><scale>1.1</scale>'
                     f'<heading>{hdg:.0f}</heading><Icon><href>'
                     f'http://maps.google.com/mapfiles/kml/shapes/arrow.png</href></Icon>'
                     f'</IconStyle></Style>'
                     f'<Point><coordinates>{c.geometry.x:.6f},{c.geometry.y:.6f},0'
                     f'</coordinates></Point></Placemark>')
        P.append('</Folder>')

    P.append('</Document></kml>')
    os.makedirs(os.path.dirname(KMZ), exist_ok=True)
    with zipfile.ZipFile(KMZ, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("doc.kml", "\n".join(P))


def _dxf(sub, cols, trunk, st, rm, unserved, conn=None, arrows=None):
    """Minimal ASCII DXF - LWPOLYLINE and POINT on named layers. Written by hand rather than
    with a library so the file has exactly the layers asked for and nothing else."""
    out = ["0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER"]
    layers = [(f"SUBNET_{i + 1:03d}", aci(c)) for i, c in enumerate(cols)]
    layers += [("MAIN_PIPE", 1), ("FORCE_MAIN", 30), ("PUMP_STATION", 2),
               ("PUMP_REVIEW", 1), ("NOT_CONNECTED", 1),
               ("CONNECTION", 5), ("CONNECTION_GAP", 6), ("FLOW_DIRECTION", 8)]
    for nm, c in layers:
        out += ["0", "LAYER", "2", nm, "70", "0", "62", str(c), "6", "CONTINUOUS"]
    out += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]

    def poly(coords, layer, closed=0):
        out.extend(["0", "LWPOLYLINE", "8", layer, "90", str(len(coords)), "70", str(closed)])
        for x, y in coords:
            out.extend(["10", f"{x:.3f}", "20", f"{y:.3f}"])

    for i, row in sub.iterrows():
        for s in lines_of(row.geometry):
            poly(s, f"SUBNET_{i + 1:03d}")
    for _, row in trunk.iterrows():
        for s in lines_of(row.geometry):
            poly(s, "MAIN_PIPE")
    for _, row in rm.iterrows():
        for s in lines_of(row.geometry):
            poly(s, "FORCE_MAIN")
    q = pd.to_numeric(st.get("Q_DUTY_LS"), errors="coerce").fillna(0)
    for j, (_, row) in enumerate(st.iterrows()):
        g = row.geometry
        if g is None or g.is_empty:
            continue
        pt = g if g.geom_type == "Point" else g.centroid
        lay = "PUMP_REVIEW" if row["_UP"] <= 0 else "PUMP_STATION"
        out.extend(["0", "POINT", "8", lay, "10", f"{pt.x:.3f}", "20", f"{pt.y:.3f}",
                    "30", "0.0"])
        out.extend(["0", "TEXT", "8", lay, "10", f"{pt.x + 15:.3f}", "20", f"{pt.y:.3f}",
                    "40", "12.0", "1",
                    f"{row.get('NODE_REF', '')} {q.iloc[j]:.0f}L/s"])
    for _, row in unserved.iterrows():
        poly(list(row.geometry.exterior.coords), "NOT_CONNECTED", closed=1)
        c = row.geometry.centroid
        out.extend(["0", "TEXT", "8", "NOT_CONNECTED", "10", f"{c.x:.3f}", "20", f"{c.y:.3f}",
                    "40", "25.0", "1", f"{row.AREA_ID} {int(row.N_PLOT)} plots"])
    # flow direction, on the bigger pipes only
    for seg in (arrows or []):
        poly(seg, "FLOW_DIRECTION")

    # where each subnetwork discharges, and the gap to the main pipe if there is one
    if conn is not None and len(conn):
        for _, c in conn.iterrows():
            x, y = c.geometry.x, c.geometry.y
            # a circle marks the point ...
            out.extend(["0", "CIRCLE", "8", "CONNECTION", "10", f"{x:.3f}", "20", f"{y:.3f}",
                        "40", "18.0"])
            # ... a big arrow says which way the flow leaves it ...
            for seg in arrowhead(x, y, c.BEARING, 55.0):
                poly(seg, "CONNECTION")
            out.extend(["0", "TEXT", "8", "CONNECTION", "10", f"{x + 25:.3f}",
                        "20", f"{y + 18:.3f}", "40", "16.0", "1",
                        f"{c.SUBNET} -> MAIN  {c.Q:.0f} L/s"])
            # ... and if it does not actually reach the main pipe, DRAW THE GAP. A subnetwork
            # ending 800 m short reads exactly like a connected one unless the gap is on the
            # drawing.
            if c.GAP_M > 50:
                out.extend(["0", "TEXT", "8", "CONNECTION_GAP", "10", f"{x + 25:.3f}",
                            "20", f"{y - 12:.3f}", "40", "16.0", "1",
                            f"NOT AT MAIN: {c.GAP_M:,.0f} m short"])

    out += ["0", "ENDSEC", "0", "EOF"]
    os.makedirs(os.path.dirname(DXF), exist_ok=True)
    with open(DXF, "w", encoding="ascii", errors="replace") as fh:
        fh.write("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
