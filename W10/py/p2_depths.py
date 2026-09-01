"""Phase 2 and 3 - lay the whole network by gravity, and find where it cannot be.

This is the step that answers the questions the stage was set up to answer: where lifting
stations are needed, whether the far south needs a big lift, and whether the western leg
can be connected at all. All three are the same calculation - lay every corridor as
shallow as the cover rule allows, and see where 12 m is reached anyway.

The construction is the W8 solver's lift-and-reset, applied to the whole 2,279 km:

    invert at a head    = ground - minimum cover - outside diameter
    invert downstream   = the lower of (upstream invert - minimum gradient x length)
                          and that same shallow level
    if depth would pass MAX_DEPTH at a node, a LIFTING STATION goes in there: the sewage
    is raised back to normal cover and the pipe restarts, so the next stretch is gravity
    again.

Depth is checked BETWEEN nodes as well as at them, by sampling the terrain along each
edge. Corridor nodes sit about 100 m apart and a ridge halfway along a reach is exactly
what a node-only check misses - it is what made the W6 audit pass chambers at 21 m.

The minimum gradient is SWEPT rather than chosen. Pipe diameters are not settled until the
loads are allocated, and the gradient a pipe must be laid at follows its diameter, so a
single assumed value would hide the sensitivity that matters most: at 0.5 % almost every
long run digs itself into the ground, at 0.1 % almost none do. The sweep says how much of
the pumping is real and how much is an artefact of the assumption.

Run:  python p2_depths.py
"""
import os
import sys
import time
import warnings
from collections import defaultdict

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import LineString, Point

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C
import netlib as N
from p1_subnetworks import flow_tree, trace_joins

warnings.filterwarnings("ignore")

MIN_COVER_CROWN = 1.3       # m to crown (G203-p33 4.6.3)
MAX_DEPTH = 12.0            # m; beyond -> a lifting station (G203-p33), no exemption
OD_DEFAULT = 0.30           # m outside diameter used until the loads settle the sizes
SLOPES = (0.0010, 0.0020, 0.0030, 0.0050)
SLOPE_MAIN = 0.0030         # the one carried forward for the mapped output
MID_STEP_M = 20.0           # terrain sampled this often along each edge


def edge_profiles(G, lines, step=MID_STEP_M):
    """Ground along every edge, so cover is checked between nodes and not only at them."""
    pts, index = [], {}
    for u, v, d in G.edges(data=True):
        ln = lines[d["line"]]
        n = max(1, int(ln.length / step))
        ts = np.linspace(0, 1, n + 1)[1:-1]
        index[(u, v)] = (len(pts), len(ts))
        pts.extend((ln.interpolate(t, normalized=True).x,
                    ln.interpolate(t, normalized=True).y) for t in ts)
    if not pts:
        return {}, np.array([])
    with rasterio.open(C.TERRAIN) as src:
        z = np.array([w[0] for w in src.sample(pts)], dtype=float)
    z[~np.isfinite(z)] = np.nan
    z[z <= 0] = np.nan
    return index, z


def solve(G, z, nxt, sink, slope, od=OD_DEFAULT, mid=None, midz=None,
          max_depth=MAX_DEPTH):
    """Invert, depth and lifting stations for the whole tree.

    Returns (invert, depth, lifts) where `lifts` maps a node to the height it must raise.
    """
    ups = defaultdict(list)
    for n, m in nxt.items():
        ups[m].append(n)

    # heads first: a node is levelled only after everything draining into it
    order, seen = [], set()
    stack = [sink]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        order.append(n)
        stack.extend(ups.get(n, ()))
    order.reverse()

    invert, lifts = {}, {}
    for n in order:
        zn = z.get(n, np.nan)
        if not np.isfinite(zn):
            continue
        shallow = zn - MIN_COVER_CROWN - od
        cand = [shallow]
        for u in ups.get(n, ()):
            if u not in invert:
                continue
            L = G[u][n]["len"] if G.has_edge(u, n) else 0.0
            iv = invert[u] - slope * L
            # a ridge between u and n counts too
            if mid is not None:
                key = (u, n) if (u, n) in mid else ((n, u) if (n, u) in mid else None)
                if key is not None:
                    s, k = mid[key]
                    if k:
                        zz = midz[s:s + k]
                        zz = zz[np.isfinite(zz)]
                        if zz.size and (zz.max() - (invert[u] - slope * L / 2)) > max_depth:
                            iv = min(iv, zz.max() - max_depth)
            cand.append(iv)
        iv = min(cand)
        if zn - iv > max_depth:
            lifts[n] = (zn - iv) - (zn - shallow)     # how far it must be raised
            iv = shallow
        invert[n] = iv

    depth = {n: z[n] - invert[n] for n in invert if np.isfinite(z.get(n, np.nan))}
    return invert, depth, lifts


def main():
    t0 = time.time()
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, d = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])

    t = time.time()
    cost, nxt, D = flow_tree(G, z, sink)
    print(f"flow tree: {len(nxt):,} nodes ({time.time()-t:.0f} s)")
    t = time.time()
    mid, midz = edge_profiles(G, lines)
    print(f"mid-edge terrain: {len(midz):,} samples at {MID_STEP_M:.0f} m "
          f"({time.time()-t:.0f} s)")

    print("\n min gradient   lifting stations   total lift m   deepest m   median m")
    rows = []
    for s in SLOPES:
        inv, dep, lifts = solve(G, z, nxt, sink, s, mid=mid, midz=midz)
        dd = np.array(list(dep.values()))
        rows.append({"slope_pct": round(100 * s, 3), "stations": len(lifts),
                     "total_lift_m": round(sum(lifts.values()), 1),
                     "deepest_m": round(float(dd.max()), 2),
                     "median_m": round(float(np.median(dd)), 2)})
        print(f"   {100*s:8.2f} % {len(lifts):16,d} {sum(lifts.values()):14,.0f} "
              f"{dd.max():11.2f} {np.median(dd):10.2f}")
    pd.DataFrame(rows).to_csv(os.path.join(C.OUT_RUN, "p2_depth_sweep.csv"), index=False)

    # ---- the case carried forward ------------------------------------------
    inv, dep, lifts = solve(G, z, nxt, sink, SLOPE_MAIN, mid=mid, midz=midz)
    dd = np.array(list(dep.values()))
    print(f"\ncarried forward at {100*SLOPE_MAIN:.2f} %: {len(lifts):,} lifting stations, "
          f"deepest {dd.max():.2f} m, {int((dd > 6).sum()):,} nodes deeper than 6 m")

    pts = [{"NODE": int(n), "GROUND": round(float(z[n]), 2),
            "INVERT": round(float(inv[n]), 2), "DEPTH": round(float(dep[n]), 2),
            "LIFT_M": round(float(lifts.get(n, 0.0)), 2),
            "IS_LIFT": int(n in lifts), "geometry": Point(xy[n])}
           for n in dep]
    nodes = gpd.GeoDataFrame(pts, crs=C.EPSG)
    nodes.to_file(os.path.join(C.OUT_SHP, "W10_nodes_depth.shp"))
    ls = nodes[nodes.IS_LIFT == 1].copy()
    ls.to_file(os.path.join(C.OUT_SHP, "W10_lift_stations.shp"))
    print(f"wrote W10_nodes_depth.shp ({len(nodes):,}) and "
          f"W10_lift_stations.shp ({len(ls):,})")
    if len(ls):
        print(f"   lift heights: median {ls.LIFT_M.median():.1f} m, "
              f"max {ls.LIFT_M.max():.1f} m, total {ls.LIFT_M.sum():,.0f} m")

    # ---- the same network taken to the southern site instead ----------------
    sink2, d2 = N.nearest_node(xy, C.STP_PROPOSED_SOUTH, nodes=comps[0])
    print(f"\nthe SOUTHERN site: nearest corridor node is {d2:,.0f} m from it")
    cost2, nxt2, _ = flow_tree(G, z, sink2)
    inv2, dep2, lifts2 = solve(G, z, nxt2, sink2, SLOPE_MAIN, mid=mid, midz=midz)
    d2a = np.array(list(dep2.values()))
    print(f"   {len(lifts2):,} lifting stations, deepest {d2a.max():.2f} m, "
          f"total lift {sum(lifts2.values()):,.0f} m")
    print(f"   against the existing works: {len(lifts):,} stations, "
          f"total lift {sum(lifts.values()):,.0f} m")

    pd.DataFrame([
        {"outlet": "existing works", "stations": len(lifts),
         "total_lift_m": round(sum(lifts.values()), 1),
         "deepest_m": round(float(dd.max()), 2)},
        {"outlet": "southern site", "stations": len(lifts2),
         "total_lift_m": round(sum(lifts2.values()), 1),
         "deepest_m": round(float(d2a.max()), 2)},
    ]).to_csv(os.path.join(C.OUT_RUN, "p2_outlet_comparison.csv"), index=False)
    print(f"\ntotal {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
