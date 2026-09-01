"""Phase 0.4 - is the given main pipe alignment workable as a gravity trunk?

The trunk is an input, not something we derive: `SHP/Main Pipe/Main Pipe.shp`, 85.5 km in
54 pieces. Everything downstream is designed to drain onto it, so if the alignment cannot
be built the rest of the design is wasted effort. This asks one question and answers it
with the terrain: laid as SHALLOW as the cover rule permits and falling at no less than
the minimum gradient, how deep does it get, and where does it pass 12 m?

The construction is the same lift-and-reset the W8 solver uses, applied to the trunk alone:

    invert at a head       = ground - minimum cover - outside diameter
    invert further down    = the lower of
                                (invert upstream) - (minimum gradient x length), and
                                ground - minimum cover - outside diameter
    depth                  = ground - invert

Taking the lower of the two is what "as shallow as possible" means: the pipe rises back
towards the surface whenever the ground drops away, instead of carrying the depth it
gained under a ridge for the rest of its length. Where depth still passes 12 m, no laying
gradient can save it and a pumping station is the only answer - so those points are the
honest count of what this alignment costs.

Diameter and gradient are swept rather than assumed, because both are unknown until the
loads are allocated and both change the answer.

Run:  python p0_mainpipe.py
"""
import os
import sys
import warnings

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C

warnings.filterwarnings("ignore")

STEP_M = 10.0          # terrain sampled this often along the trunk
MIN_COVER_CROWN = 1.3  # m to crown (G203-p33 4.6.3)
MAX_DEPTH = 12.0       # m; beyond this a pumping station is the only answer (G203-p33)

# swept, because neither is known until the loads are allocated
DIAMETERS_MM = (600, 1000, 1400)
SLOPES = (0.0005, 0.0010, 0.0015)   # 0.05 %, 0.10 %, 0.15 %

WALL_ALLOW = 0.10      # m, allowance for wall thickness and bedding over the nominal bore


def outside_diameter(dn_mm):
    return dn_mm / 1000.0 + WALL_ALLOW


def build_graph(gdf, step=STEP_M):
    """The trunk as a graph, with a node every `step` metres so cover is checked between
    chambers and not only at them - a ridge halfway along a reach is exactly what a
    node-only check misses."""
    G = nx.Graph()

    def key(p):
        return (round(p[0], 2), round(p[1], 2))

    for geom in gdf.geometry:
        parts = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
        for ls in parts:
            n = max(1, int(round(ls.length / step)))
            pts = [ls.interpolate(t, normalized=True) for t in np.linspace(0, 1, n + 1)]
            cs = [(p.x, p.y) for p in pts]
            for a, b in zip(cs[:-1], cs[1:]):
                d = float(np.hypot(a[0] - b[0], a[1] - b[1]))
                if d > 0.01:
                    G.add_edge(key(a), key(b), w=d)
    return G


def sample_ground(nodes, terrain_path):
    with rasterio.open(terrain_path) as src:
        z = np.array([v[0] for v in src.sample(nodes)], dtype=float)
    z[~np.isfinite(z)] = np.nan
    z[z <= 0] = np.nan
    return z


def lay_shallow(G, root, z, slope_min, od, idx):
    """Invert levels for the whole tree, laid as shallow as the cover rule allows.

    Returns (invert, depth, order). Nodes are visited from the heads towards `root`, so a
    node is only levelled once everything draining into it has been.

    `idx` maps a node to its position in `z` and MUST come from the graph the ground was
    sampled on. Rebuilding it from a subgraph reads the elevations off the wrong nodes,
    which is how an earlier run of this reported a 159 m deep trunk on an alignment whose
    worst ridge is 4.5 m.
    """
    # tree of flow: every node drains along the shortest path to root
    dist = nx.single_source_dijkstra_path_length(G, root, weight="w")
    parent = {}
    for n in G:
        if n == root or n not in dist:
            continue
        best, bd = None, None
        for m in G.neighbors(n):
            if m in dist and dist[m] < dist[n] and (bd is None or dist[m] < bd):
                best, bd = m, dist[m]
        parent[n] = best

    order = sorted((n for n in G if n in dist), key=lambda n: -dist[n])

    invert = {}
    for n in order:
        zn = z[idx[n]]
        if not np.isfinite(zn):
            continue
        shallow = zn - MIN_COVER_CROWN - od
        ups = [invert[m] - slope_min * G[m][n]["w"]
               for m in G.neighbors(n)
               if m in invert and parent.get(m) == n]
        invert[n] = min([shallow] + ups) if ups else shallow

    depth = {n: z[idx[n]] - invert[n] for n in invert if np.isfinite(z[idx[n]])}
    return invert, depth, order


def main():
    os.makedirs(C.OUT_DOCS, exist_ok=True)
    os.makedirs(C.OUT_RUN, exist_ok=True)

    mp = gpd.read_file(C.MAIN_PIPE).to_crs(C.EPSG)
    print(f"main pipe: {len(mp)} features, {mp.length.sum()/1000:.2f} km")

    G = build_graph(mp)
    nodes = list(G.nodes)
    z = sample_ground(nodes, C.TERRAIN)
    idx = {n: i for i, n in enumerate(nodes)}
    print(f"graph: {G.number_of_nodes():,} nodes at {STEP_M:.0f} m, "
          f"{G.number_of_edges():,} edges; ground missing at "
          f"{int(np.isnan(z).sum())} nodes")

    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    print(f"\nCONTINUITY: {len(comps)} disconnected components")
    rows = []
    for ci, comp in enumerate(comps):
        sub = G.subgraph(comp)
        L = sum(d["w"] for _, _, d in sub.edges(data=True))
        zz = z[[idx[n] for n in comp]]
        zz = zz[np.isfinite(zz)]
        rows.append((ci, len(comp), round(L / 1000, 2), round(zz.min(), 1),
                     round(zz.max(), 1)))
        print(f"   component {ci}: {L/1000:6.2f} km   ground {zz.min():.1f} to {zz.max():.1f} m")

    # the gap between them, which is the user's "the west is not connected"
    if len(comps) >= 2:
        a = unary_union([Point(n) for n in comps[0]])
        b = unary_union([Point(n) for n in comps[1]])
        print(f"   shortest gap between component 0 and 1: {a.distance(b):,.0f} m")

    # ---- where does each component drain to? --------------------------------
    stp = Point(C.STP_EXISTING)
    results = []
    for ci, comp in enumerate(comps):
        sub = G.subgraph(comp).copy()
        # the outlet is the node closest to the works for the main body, and the lowest
        # node for a component that reaches no works at all
        near = min(comp, key=lambda n: stp.distance(Point(n)))
        d_stp = stp.distance(Point(near))
        if d_stp < 2000:
            root, why = near, f"{d_stp:.0f} m from the existing works"
        else:
            valid = [n for n in comp if np.isfinite(z[idx[n]])]
            root = min(valid, key=lambda n: z[idx[n]])
            why = (f"lowest point of the component, {z[idx[root]]:.1f} m; "
                   f"the works are {d_stp/1000:.1f} km away")
        print(f"\ncomponent {ci} outlet at {root} - {why}")

        for dn in DIAMETERS_MM:
            od = outside_diameter(dn)
            for s in SLOPES:
                inv, dep, _ = lay_shallow(sub, root, z, s, od, idx)
                if not dep:
                    continue
                d = np.array(list(dep.values()))
                over = int((d > MAX_DEPTH).sum())
                results.append({
                    "component": ci, "DN_mm": dn, "slope_pct": round(100 * s, 3),
                    "km": round(sum(e["w"] for _, _, e in sub.edges(data=True)) / 1000, 2),
                    "deepest_m": round(float(d.max()), 2),
                    "median_m": round(float(np.median(d)), 2),
                    "nodes_over_12m": over,
                    "pct_over_12m": round(100 * over / len(d), 1),
                    "length_over_12m_km": round(over * STEP_M / 1000, 2),
                })

    res = pd.DataFrame(results)
    print("\nHOW DEEP THE TRUNK GETS, laid as shallow as the cover rule allows")
    print(res.to_string(index=False))
    res.to_csv(os.path.join(C.OUT_RUN, "p0_mainpipe_depth.csv"), index=False)

    # ---- the design case, written out for mapping ---------------------------
    dn, s = 1000, 0.0010
    od = outside_diameter(dn)
    pts = []
    for ci, comp in enumerate(comps):
        sub = G.subgraph(comp).copy()
        near = min(comp, key=lambda n: stp.distance(Point(n)))
        if stp.distance(Point(near)) < 2000:
            root = near
        else:
            valid = [n for n in comp if np.isfinite(z[idx[n]])]
            root = min(valid, key=lambda n: z[idx[n]])
        inv, dep, _ = lay_shallow(sub, root, z, s, od, idx)
        for n, d in dep.items():
            pts.append({"COMP": ci, "X": n[0], "Y": n[1],
                        "GROUND": round(float(z[idx[n]]), 2),
                        "INVERT": round(float(inv[n]), 2), "DEPTH": round(float(d), 2),
                        "OVER_12": int(d > MAX_DEPTH), "geometry": Point(n)})
    prof = gpd.GeoDataFrame(pts, crs=C.EPSG)
    prof.to_file(os.path.join(C.OUT_SHP, "W10_mainpipe_profile.shp"))
    print(f"\nwrote W10_mainpipe_profile.shp  (DN{dn} at {100*s:.2f} %): "
          f"{int(prof.OVER_12.sum())} of {len(prof)} points past {MAX_DEPTH:.0f} m")

    # ---- other things that stop a trunk being built -------------------------
    roads = gpd.read_file(C.ROADS).set_crs(C.EPSG, allow_override=True)
    dual = roads[roads["dual"].astype(str) == "1"]
    for tol in (6.0, 12.0):
        on = mp.geometry.intersection(unary_union(dual.geometry.buffer(tol))).length.sum()
        print(f"trunk within {tol:4.1f} m of a dual carriageway: {on/1000:.2f} km")

    bnd = gpd.read_file(C.BOUNDARY).to_crs(C.EPSG).geometry.iloc[0]
    inside = mp.intersection(bnd).length.sum()
    print(f"trunk inside the study boundary: {inside/1000:.2f} km of "
          f"{mp.length.sum()/1000:.2f} km ({100*inside/mp.length.sum():.0f} %)")


if __name__ == "__main__":
    main()
