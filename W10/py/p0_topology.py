"""Phase 0.3 - make the corridor network one connected thing.

Straight off the merge the 2,187 km is 7,379 separate pieces and the largest holds 8 % of
it. That is not a network, it is a picture of a network: lines cross without sharing a
node, and endpoints that look joined are a few centimetres apart. A sewer cannot be routed
through either.

Two operations fix it, in this order:

  1. NODE - `unary_union` over all the linework splits every line at every crossing, so a
     junction becomes a shared vertex instead of two lines passing over each other.
  2. SNAP - endpoints still within `SNAP_M` of another endpoint or of a line are pulled
     onto it. This is what closes the gaps a draughtsman's eye accepts and a graph does not.

Everything that is still separate afterwards is reported rather than forced: an island
2 km from anything is a real design question, not a tolerance to widen.

Run:  python p0_topology.py
"""
import os
import sys
import time
import warnings

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import unary_union, snap
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C

warnings.filterwarnings("ignore")

SNAP_M = 2.0        # endpoints this close are the same point
MIN_EDGE_M = 0.30   # noding leaves slivers; anything shorter is one


def node_network(lines):
    """Split every line at every crossing so junctions are shared vertices."""
    merged = unary_union(lines)
    if merged.geom_type == "LineString":
        return [merged]
    return [g for g in merged.geoms if g.length > MIN_EDGE_M]


def build_graph(lines, snap_m=SNAP_M):
    """Graph over the noded lines, with endpoints within `snap_m` treated as one node."""
    ends = []
    for ln in lines:
        ends.append(ln.coords[0])
        ends.append(ln.coords[-1])
    pts = np.array([(p[0], p[1]) for p in ends])

    # cluster endpoints: each point takes the id of the lowest-numbered point it touches
    tree = cKDTree(pts)
    pairs = tree.query_pairs(snap_m, output_type="ndarray")
    uf = np.arange(len(pts))

    def find(i):
        while uf[i] != i:
            uf[i] = uf[uf[i]]
            i = uf[i]
        return i

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            uf[max(ra, rb)] = min(ra, rb)
    labels = np.array([find(i) for i in range(len(pts))])

    G = nx.Graph()
    for i, ln in enumerate(lines):
        u, v = int(labels[2 * i]), int(labels[2 * i + 1])
        if u == v:
            continue                      # a loop closing on itself carries nothing
        if G.has_edge(u, v) and G[u][v]["w"] <= ln.length:
            continue                      # keep the shorter of two parallel corridors
        G.add_edge(u, v, w=ln.length, line=i)
    for n in G:
        G.nodes[n]["xy"] = tuple(pts[n])
    return G, labels


def stitch_parts(lines, max_m=250.0):
    """Close what is left by the shortest links, not by widening the tolerance.

    Raising the snap distance from 2 m to 5 m took 1,074 pieces to 979 - almost nothing -
    because the remaining gaps are real distances, not slack. So the pieces are joined the
    way the skeleton islands were: shortest link between neighbours, minimum spanning tree
    over the lot, and anything still further than `max_m` from everything reported rather
    than bridged.
    """
    from shapely.ops import nearest_points
    merged = [unary_union(grp) for grp in lines]
    tree = STRtree(merged)
    G = nx.Graph()
    G.add_nodes_from(range(len(merged)))
    for i, g in enumerate(merged):
        for j in tree.query(g.buffer(max_m)):
            j = int(j)
            if j <= i:
                continue
            d = g.distance(merged[j])
            if d <= max_m:
                G.add_edge(i, j, w=d)
    links, stranded = [], []
    for comp in nx.connected_components(G):
        for u, v in nx.minimum_spanning_edges(G.subgraph(comp), weight="w", data=False):
            a, b = nearest_points(merged[u], merged[v])
            if a.distance(b) > 0.05:
                links.append(LineString([a, b]))
    for comp in nx.connected_components(G):
        if len(comp) == 1:
            stranded.extend(comp)
    return links, stranded, len(list(nx.connected_components(G)))


def main():
    t0 = time.time()
    a = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors.shp"))
    print(f"in: {len(a):,} lines, {a.length.sum()/1000:,.1f} km")

    t = time.time()
    lines = node_network(list(a.geometry))
    print(f"noded: {len(lines):,} lines, {sum(l.length for l in lines)/1000:,.1f} km "
          f"({time.time()-t:.0f} s)")

    for snap_m in (0.5, 1.0, 2.0, 5.0):
        G, _ = build_graph(lines, snap_m)
        comps = sorted(nx.connected_components(G), key=len, reverse=True)
        km = [sum(d["w"] for *_, d in G.subgraph(c).edges(data=True)) / 1000 for c in comps]
        km = np.array(km)
        print(f"   snap {snap_m:4.1f} m: {len(comps):5,d} components, "
              f"largest {km[0]:7.1f} km ({100*km[0]/km.sum():4.1f} %), "
              f"pieces under 0.5 km: {(km < 0.5).sum():5,d} holding {km[km<0.5].sum():6.1f} km")

    G, labels = build_graph(lines, SNAP_M)
    comps = sorted(nx.connected_components(G), key=len, reverse=True)

    # ---- close the rest with the shortest links ----------------------------
    groups = []
    for comp in comps:
        groups.append([lines[d["line"]] for *_, d in G.subgraph(comp).edges(data=True)])
    links, stranded, n_after = stitch_parts(groups)
    print(f"\nstitched: {len(links):,} links, "
          f"{sum(l.length for l in links)/1000:,.2f} km; "
          f"{len(comps):,} pieces -> {n_after:,}; {len(stranded)} still isolated")
    # The links land in the MIDDLE of the lines they reach, not on an endpoint, and the
    # graph only joins endpoint to endpoint. So the whole set is re-noded: the links split
    # the lines they touch and the junction becomes a shared vertex.
    lines = node_network(lines + links)
    print(f"re-noded with the links in: {len(lines):,} lines")

    G, labels = build_graph(lines, SNAP_M)
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    km = np.array([sum(d["w"] for *_, d in G.subgraph(c).edges(data=True)) / 1000
                   for c in comps])

    out = []
    for ci, comp in enumerate(comps):
        for u, v, d in G.subgraph(comp).edges(data=True):
            out.append({"PART": ci, "LEN_M": round(d["w"], 2),
                        "geometry": lines[d["line"]]})
    g = gpd.GeoDataFrame(out, crs=C.EPSG)
    g.to_file(os.path.join(C.OUT_SHP, "W10_corridors_noded.shp"))

    print(f"\nFINAL at {SNAP_M:.1f} m: {G.number_of_nodes():,} nodes, "
          f"{G.number_of_edges():,} edges, {km.sum():,.1f} km in {len(comps):,} pieces")
    print(f"   largest piece {km[0]:,.1f} km ({100*km[0]/km.sum():.1f} %); "
          f"top 8: {' '.join(f'{v:.1f}' for v in km[:8])}")
    pd.DataFrame({"part": range(len(km)), "km": km.round(2)}).to_csv(
        os.path.join(C.OUT_RUN, "p0_topology_parts.csv"), index=False)
    print(f"total {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
