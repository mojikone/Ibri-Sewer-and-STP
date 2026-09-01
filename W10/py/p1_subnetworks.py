"""Phase 1 - define the subnetworks.

A subnetwork here is everything that reaches the trunk main at one point. That definition
comes from the as-built rather than from convenience: NAMA's own manhole IDs say a network
is a hierarchy, properties feed riders, riders feed laterals, laterals feed laterals, and
only collectors reach the trunk. In their built network only about 16 things touch the
trunk across 111.6 km. W7 designed every catchment its own path to the main pipe, 30 things
touched it, and the result was a network no contractor would build.

So the question is not "which streets are near each other" but "where does the flow
actually leave for the trunk", and that is answered by routing, not by drawing polygons.

Method:
  1. corridors and trunk as one graph (netlib), ground on every node
  2. cost each edge by LENGTH PLUS a heavy charge for every metre climbed in the direction
     of flow, so a route prefers the fall even when it is longer
  3. Dijkstra outward from the works over the reversed graph - which gives, for every node
     at once, the route a sewer would take to get there
  4. walk each node's route until it first steps onto a trunk edge: that node is its JOIN
  5. a subnetwork is everything sharing a join

Nothing is sized here. This is the skeleton the Phase 2 solver will lay pipe on.

Run:  python p1_subnetworks.py
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
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C
import netlib as N

warnings.filterwarnings("ignore")

MIN_SUBNET_KM = 0.5      # smaller than this is folded into its neighbour
FRONTAGE_M = 60.0        # a plot belongs to the subnetwork whose corridor it fronts
JOIN_PENALTIES = (0, 250, 500, 1000, 2000, 4000)   # swept, metres of route per join
# Carried forward: ZERO. The sweep says charging for a join barely consolidates anything
# here - 214 joins at no charge, still 205 at 4,000 m - while total route length grows 30 %.
# The reason is structural and worth stating: the main pipe as drawn is not a trunk at the
# edge of the town collecting from a distance, it is a SPINE that runs through the
# settlements, so almost everything genuinely sits on it. Measured against the as-built the
# density is not high at all: NAMA has about 16 joins on 4.0 km of trunk main, 4 per km;
# this has 206 on 92.3 km, 2.2 per km. Paying 30 % more pipe to remove nine of them buys
# nothing.
JOIN_PENALTY = 0.0


def trace_joins(cost, nxt, trunk_nodes):
    """For every node, the trunk node its flow first reaches. Memoised down each chain."""
    join = {}
    for start in cost:
        n, seen = start, []
        while True:
            if n in join:
                j = join[n]
                break
            if n in trunk_nodes:
                j = n
                break
            seen.append(n)
            if n not in nxt:
                j = None
                break
            n = nxt[n]
        for s in seen:
            join[s] = j
    return join


def flow_tree(G, z, sink, penalty=N.CLIMB_PENALTY, join_penalty=0.0, trunk_nodes=None):
    """For every node: the next node downstream, and the cost of getting to the sink.

    The cost graph is directed - u->v is charged for the height gained going that way - so
    the tree is found by running Dijkstra from the sink over the REVERSED graph. One run
    settles the whole network.
    """
    D = N.sewer_cost(G, z, penalty, join_penalty, trunk_nodes)
    R = D.reverse(copy=False)
    cost, paths = nx.single_source_dijkstra(R, sink, weight="w")
    # A path in R reads sink -> ... -> n. In D that same chain runs n -> ... -> sink, so
    # the node one step DOWNSTREAM of n is the second-to-last entry.
    nxt = {n: p[-2] for n, p in paths.items() if len(p) > 1}
    return cost, nxt, D


def main():
    t0 = time.time()
    os.makedirs(C.OUT_RUN, exist_ok=True)
    G, xy, lines, z = N.load_network()

    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, d = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    print(f"outlet: node {d:.0f} m from the works at {C.STP_EXISTING}")

    trunk_nodes = {n for u, v, dd in G.edges(data=True) if dd["trunk"] for n in (u, v)}
    print(f"trunk nodes: {len(trunk_nodes):,}")

    # ---- how many joins is the right number? -------------------------------
    # Every join is a chamber the whole catchment above it drains through. Charging for
    # one and sweeping the charge shows what consolidation costs in extra pipe.
    print("\n  join charge   joins   total route km")
    sweep = []
    for jp in JOIN_PENALTIES:
        c, nx_, _ = flow_tree(G, z, sink, join_penalty=jp, trunk_nodes=trunk_nodes)
        j = trace_joins(c, nx_, trunk_nodes)
        n_joins = len({v for v in j.values() if v is not None})
        route_km = sum(c.values()) / 1000
        sweep.append((jp, n_joins, route_km))
        print(f"   {jp:8.0f} m {n_joins:7d}   {route_km:14,.0f}")
    print()

    cost, nxt, D = flow_tree(G, z, sink, join_penalty=JOIN_PENALTY,
                             trunk_nodes=trunk_nodes)
    print(f"chosen join charge {JOIN_PENALTY:.0f} m: routed {len(cost):,} nodes")
    join = trace_joins(cost, nxt, trunk_nodes)

    grp = defaultdict(list)
    for n, j in join.items():
        if j is not None and n not in trunk_nodes:
            grp[j].append(n)
    print(f"raw joins onto the trunk: {len(grp):,}")

    # ---- subnetwork per join ------------------------------------------------
    order = sorted(grp.items(), key=lambda kv: -len(kv[1]))
    node_sub, join_pt = {}, {}
    for si, (j, ns) in enumerate(order):
        join_pt[si] = j
        for n in ns:
            node_sub[n] = si

    rows = []
    for u, v, dd in G.edges(data=True):
        s = -1 if dd["trunk"] else node_sub.get(u, node_sub.get(v, -2))
        rows.append({"SUBNET": s, "LEN_M": round(dd["len"], 2),
                     "TRUNK": dd["trunk"], "geometry": lines[dd["line"]]})
    seg = gpd.GeoDataFrame(rows, crs=C.EPSG)
    seg.to_file(os.path.join(C.OUT_SHP, "W10_subnet_segments.shp"))

    km = seg[seg.SUBNET >= 0].groupby("SUBNET").LEN_M.sum() / 1000
    print(f"\nsubnetworks: {len(km):,}, {km.sum():,.1f} km "
          f"(+{seg[seg.TRUNK==1].LEN_M.sum()/1000:,.1f} km of trunk)")
    for t_ in (0.5, 1, 5, 10, 25):
        print(f"   over {t_:5.1f} km: {(km > t_).sum():4d} subnetworks "
              f"holding {km[km > t_].sum():7.1f} km")

    # ---- plots per subnetwork ----------------------------------------------
    plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
    sub_lines = seg[seg.SUBNET >= 0]
    near = gpd.sjoin_nearest(plots[["geometry"]], sub_lines[["SUBNET", "geometry"]],
                             how="left", max_distance=FRONTAGE_M, distance_col="D")
    near = near[~near.index.duplicated(keep="first")]
    plots["SUBNET"] = near["SUBNET"].values
    npl = plots.groupby("SUBNET").size()

    out = []
    for si in km.index:
        j = join_pt[si]
        out.append({"SUBNET": int(si), "KM": round(float(km[si]), 2),
                    "PLOTS": int(npl.get(si, 0)),
                    "JOIN_X": round(xy[j][0], 1), "JOIN_Y": round(xy[j][1], 1),
                    "JOIN_Z": round(float(z[j]), 2), "geometry": Point(xy[j])})
    joins = gpd.GeoDataFrame(out, crs=C.EPSG).sort_values("KM", ascending=False)
    joins.to_file(os.path.join(C.OUT_SHP, "W10_joins.shp"))
    joins.drop(columns="geometry").to_csv(
        os.path.join(C.OUT_RUN, "p1_subnetworks.csv"), index=False)

    ok = npl[npl.index.notna()] if hasattr(npl.index, "notna") else npl
    print(f"\nplots assigned to a subnetwork: {int(ok.sum()):,} of {len(plots):,}")
    print("\nlargest 15 subnetworks:")
    print(joins.drop(columns="geometry").head(15).to_string(index=False))
    print(f"\nsubnetworks under 25 plots: {int((joins.PLOTS < 25).sum()):,} "
          f"holding {joins[joins.PLOTS<25].KM.sum():.1f} km")
    print(f"total {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
