"""Shared network machinery for W10 - built once, used by every phase after Phase 0.

The corridor network and the trunk are ONE graph here, not two. The trunk is a corridor
with a job, and keeping it separate would mean every phase re-deciding where a branch is
allowed to meet it. Merging them and re-noding makes the meeting points shared vertices,
so "what touches the trunk" becomes a property of the graph rather than a search.

Routing cost is not distance. A sewer cannot climb, so an edge that gains height is
charged for the height it gains, heavily. The result is a route that prefers to follow the
fall even when that is longer - which is what a sewer does and what a shortest-path search
on plain distance does not.
"""
import os
import sys

import geopandas as gpd
import networkx as nx
import numpy as np
import rasterio
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C

SNAP_M = 2.0
MIN_EDGE_M = 0.30
TRUNK_TOL_M = 3.0        # an edge this close to the main pipe IS the main pipe
CLIMB_PENALTY = 400.0    # metres of route charged per metre of height gained

# The 50-year flood grid: classes 4, 5 and 6 are wadi, where no pipe and no chamber may go
# (criteria HAZARD_WADI_CLASSES, user 2026-08-19). W8 applied this; W10 did not, and laid
# 156.0 km - 8.3 % of the network - on wadi ground.
#
# CORRECTION to what this comment said before: the grid is NOT continuous float. All
# 709,183,851 valid cells are exact integers 1 to 6, so W8's int(v) in (4,5,6) was never
# wrong and floor(v) >= 4 is identical to it here. W10's failure was that the rule was
# never called at all, not that it was called incorrectly. The floor() form is kept only
# because it survives a resampled grid; it fixed nothing.
#
# Charged rather than forbidden, because a sewer must sometimes cross a wadi. STILL
# INCOMPLETE: sewer_cost has NO dual-carriageway term, and the shipped design runs 1.67 km
# ALONG a dual carriageway with 47 crossings unscheduled (project rule 7). W11a.
WADI_MIN_CLASS = 4.0
WADI_PENALTY_M = 5000.0

last_labels = None       # endpoint->node labels from the most recent build()


def node_lines(lines):
    merged = unary_union(lines)
    if merged.geom_type == "LineString":
        return [merged]
    return [g for g in merged.geoms if g.length > MIN_EDGE_M]


def build(lines, snap_m=SNAP_M):
    """Graph over noded lines. Node ids index into the returned coordinate array.

    Endpoints are clustered with a BOUNDED radius, not by union-find over pairs. Chaining
    pairs transitively lets a cluster grow without limit - A within 2 m of B, B within 2 m
    of C, and A and C are merged though they are 4 m apart. With this network that turned
    genuine 3 m connecting lines into self-loops, which were then dropped, so the graph
    reported 8 connected pieces and reloading its own output gave 460. Here every member of
    a cluster is within `snap_m` of that cluster's first point, so a cluster is never wider
    than the tolerance.
    """
    ends = np.array([p for ln in lines for p in (ln.coords[0][:2], ln.coords[-1][:2])])
    tree = cKDTree(ends)
    lab = np.full(len(ends), -1, dtype=np.int64)
    for i in range(len(ends)):
        if lab[i] != -1:
            continue
        lab[i] = i
        for j in tree.query_ball_point(ends[i], snap_m):
            if lab[j] == -1:
                lab[j] = i

    G = nx.Graph()
    for i, ln in enumerate(lines):
        u, v = int(lab[2 * i]), int(lab[2 * i + 1])
        if u == v:
            continue
        if G.has_edge(u, v) and G[u][v]["len"] <= ln.length:
            continue
        G.add_edge(u, v, len=ln.length, line=i)
    xy = {n: tuple(ends[n]) for n in G}
    global last_labels
    last_labels = lab
    return G, xy


def ground(xy, nodes=None, terrain=None):
    nodes = nodes if nodes is not None else list(xy)
    with rasterio.open(terrain or C.TERRAIN) as src:
        z = np.array([v[0] for v in src.sample([xy[n] for n in nodes])], dtype=float)
    z[~np.isfinite(z)] = np.nan
    z[z <= 0] = np.nan
    return dict(zip(nodes, z))


def load_network(corridors=None, main_pipe=None, verbose=True):
    """Corridors and trunk as one graph, with ground level on every node.

    Returns (G, xy, z). Every edge carries `len`, `line` and `trunk`; `trunk` is 1 where
    the edge lies on the given main pipe.
    """
    corridors = corridors or os.path.join(C.OUT_SHP, "W10_corridors_noded.shp")
    main_pipe = main_pipe or C.MAIN_PIPE

    cor = gpd.read_file(corridors)
    mp = gpd.read_file(main_pipe).to_crs(C.EPSG)
    mp_lines = []
    for g in mp.geometry:
        mp_lines.extend(g.geoms if g.geom_type == "MultiLineString" else [g])

    lines = node_lines(list(cor.geometry) + mp_lines)
    G, xy = build(lines)
    z = ground(xy)

    # wadi exposure, per edge, from the midpoint of its line
    wadi = {}
    try:
        import rasterio as _rio
        with _rio.open(C.HAZARD) as _src:
            mids = [lines[d["line"]].interpolate(0.5, normalized=True)
                    for _u, _v, d in G.edges(data=True)]
            vals = np.array([w[0] for w in _src.sample([(p.x, p.y) for p in mids])],
                            dtype=float)
        for (u, v, d), val in zip(G.edges(data=True), vals):
            d["wadi"] = int(np.isfinite(val) and np.floor(val) >= WADI_MIN_CLASS)
    except Exception as e:
        for _u, _v, d in G.edges(data=True):
            d["wadi"] = 0
        print(f"   hazard grid unavailable ({e}); wadi rule NOT applied")

    trunk_buf = unary_union([l.buffer(TRUNK_TOL_M) for l in mp_lines])
    n_trunk = 0
    for u, v, d in G.edges(data=True):
        ln = lines[d["line"]]
        on = ln.intersection(trunk_buf).length > 0.8 * ln.length
        d["trunk"] = int(on)
        n_trunk += on
    for u, v, d in G.edges(data=True):
        zu, zv = z.get(u, np.nan), z.get(v, np.nan)
        dz = 0.0 if not (np.isfinite(zu) and np.isfinite(zv)) else abs(zu - zv)
        d["climb_uv"] = max(0.0, (zv - zu) if np.isfinite(zu) and np.isfinite(zv) else 0.0)
        d["climb_vu"] = max(0.0, (zu - zv) if np.isfinite(zu) and np.isfinite(zv) else 0.0)
        d["fall"] = dz

    if verbose:
        km = sum(d["len"] for *_, d in G.edges(data=True)) / 1000
        tkm = sum(d["len"] for *_, d in G.edges(data=True) if d["trunk"]) / 1000
        comps = sorted(nx.connected_components(G), key=len, reverse=True)
        wkm = sum(d["len"] for *_, d in G.edges(data=True) if d.get("wadi")) / 1000
        print(f"network: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges, "
              f"{km:,.1f} km ({tkm:,.1f} km of it trunk), {len(comps)} pieces, "
              f"largest holds {100*len(comps[0])/G.number_of_nodes():.1f} % of nodes; "
              f"{wkm:,.1f} km on wadi ground")
    return G, xy, lines, z


def nearest_node(xy, pt, nodes=None):
    ns = list(nodes) if nodes is not None else list(xy)
    arr = np.array([xy[n] for n in ns])
    i = int(np.argmin(np.hypot(arr[:, 0] - pt[0], arr[:, 1] - pt[1])))
    return ns[i], float(np.hypot(arr[i, 0] - pt[0], arr[i, 1] - pt[1]))


def sewer_cost(G, z, penalty=CLIMB_PENALTY, join_penalty=0.0, trunk_nodes=None):
    """Directed graph whose edge cost charges for height GAINED in the direction of flow.

    Flow runs from the node towards the sink, so traversing u->v downhill costs the
    length, and uphill costs the length plus `penalty` metres for every metre climbed. A
    Dijkstra run backwards from the sink over this graph therefore returns, for each node,
    the route a sewer would actually take rather than the shortest one on the map.

    `join_penalty` charges for stepping ONTO the trunk from anywhere else. Every join is a
    chamber that will be deep once a whole town drains through it, and the as-built says
    only about 16 things touch 111.6 km of NAMA's network. Without a charge, a two-street
    pocket that happens to sit beside the trunk gets its own connection; with one, it pays
    to travel to a neighbour's join instead, which is what the as-built does.
    """
    if trunk_nodes is None:
        trunk_nodes = {n for u, v, d in G.edges(data=True) if d["trunk"]
                       for n in (u, v)}
    D = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        for a, b, climb in ((u, v, d["climb_uv"]), (v, u, d["climb_vu"])):
            w = d["len"] + penalty * climb
            if d.get("wadi"):
                w += WADI_PENALTY_M
            if join_penalty and not d["trunk"] and b in trunk_nodes:
                w += join_penalty
            D.add_edge(a, b, w=w, len=d["len"], trunk=d["trunk"])
    return D
