"""sewnet.topo — S2: directed collection tree toward the outfall.

Donor concept (SWNETWROK graph.py) upgraded per PLAN §3: the spanning tree comes
from a COST-WEIGHTED Dijkstra instead of hop-count BFS — cost = length * road-class
factor + climb penalty, so collectors prefer proper streets over alleys and avoid
routing over humps (the W2 "alleys and bends" critique). Loop-free by construction:
each node keeps exactly one downstream edge (its Dijkstra predecessor toward the
outfall). Unreachable nodes are reported, never silently dropped.
"""

import math
import networkx as nx
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point
from shapely.ops import substring
from shapely.strtree import STRtree

CLIMB_PENALTY = 300.0    # m of equivalent length per m of uphill climb (W2 s3 KCLIMB — method choice)
ARTERIAL_FACTOR = 0.70   # prefer arterial/wide corridors (W2 s3 rf — method choice)


def nkey(x, y):
    return (round(x, 2), round(y, 2))


def build_undirected(segs, sampler):
    """Undirected graph: nodes = rounded endpoints with ground elevation, edges carry geometry."""
    Gu = nx.Graph()
    for i, g in enumerate(segs):
        a, b = nkey(*g.coords[0]), nkey(*g.coords[-1])
        if a == b:
            continue
        for k, pt in ((a, g.coords[0]), (b, g.coords[-1])):
            if k not in Gu:
                Gu.add_node(k, x=pt[0], y=pt[1], z=sampler.z(pt[0], pt[1]))
        if Gu.has_edge(a, b) and Gu[a][b]["length"] <= g.length:
            continue
        Gu.add_edge(a, b, length=g.length, geom=g, idx=i)
    return Gu


def mark_arterials(Gu, top_quantile=0.90, k_samples=400):
    """Approximate betweenness -> top decile flagged arterial (W1 s1 pattern)."""
    k = min(k_samples, len(Gu))
    if k < 10:
        for u, v in Gu.edges:
            Gu[u][v]["arterial"] = False
        return
    bt = nx.edge_betweenness_centrality(Gu, k=k, weight="length", seed=42)
    vals = np.array(list(bt.values()))
    thr = np.quantile(vals, top_quantile) if len(vals) else 0.0
    for (u, v), b in bt.items():
        Gu[u][v]["arterial"] = b >= thr


def pick_outfall(Gu, boundary, expected=None, edge_tol=30.0, override=None):
    """Lowest road node on/near the boundary edge. Returns (node_key, report dict).
    Cross-checks against the user's expected point — REPORT ONLY, never stops."""
    ring = boundary.exterior
    cands = [(n, d) for n, d in Gu.nodes(data=True)
             if ring.distance(Point(d["x"], d["y"])) <= edge_tol]
    if override is not None:
        arr = np.array([[d["x"], d["y"]] for n, d in Gu.nodes(data=True)])
        names = list(Gu.nodes)
        i = cKDTree(arr).query(np.array(override))[1]
        chosen = names[i]
    else:
        chosen = min(cands, key=lambda t: t[1]["z"])[0]
    d = Gu.nodes[chosen]
    rep = {"node": chosen, "x": d["x"], "y": d["y"], "z": d["z"], "boundary_candidates": len(cands)}
    if expected is not None:
        dist = math.hypot(d["x"] - expected[0], d["y"] - expected[1])
        rep["expected_xy"] = expected
        rep["dist_to_expected_m"] = dist
        rep["agrees"] = dist <= 150.0
    return chosen, rep


def edge_cost(Gu, u, v):
    d = Gu[u][v]
    rf = ARTERIAL_FACTOR if d.get("arterial") else 1.0
    climb = 0.0  # symmetric here; direction handled in the directed pass
    return d["length"] * rf + climb


def build_tree(Gu, outfall):
    """Directed tree: every reachable node gets exactly one downstream edge along its
    cost-shortest path toward the outfall, with uphill steps penalized.

    Implemented as Dijkstra from the outfall over a DIRECTED expansion where the cost
    of traversing an edge outfall->...->u->v includes a penalty when v must climb to
    reach u (i.e. sewage from v flows downhill-preferring paths to the outfall).
    Returns (Gd directed graph child->parent, unreachable node list)."""
    # Search runs FROM the outfall outward, so a search edge u->v corresponds to
    # FLOW v->u. That flow climbs when z_u > z_v; the climb is penalized so the
    # tree prefers downhill-friendly streets (less depth, fewer amputations).
    Gd_search = nx.DiGraph()
    for u, v, d in Gu.edges(data=True):
        zu, zv = Gu.nodes[u]["z"], Gu.nodes[v]["z"]
        rf = ARTERIAL_FACTOR if d.get("arterial") else 1.0
        base = d["length"] * rf
        Gd_search.add_edge(u, v, w=base + CLIMB_PENALTY * max(0.0, zu - zv))  # flow v->u
        Gd_search.add_edge(v, u, w=base + CLIMB_PENALTY * max(0.0, zv - zu))  # flow u->v
    try:
        _, paths = nx.single_source_dijkstra(Gd_search, outfall, weight="w")
    except nx.NodeNotFound:
        return nx.DiGraph(), list(Gu.nodes)

    Gd = nx.DiGraph()
    for n, d in Gu.nodes(data=True):
        Gd.add_node(n, **d)
    for node, path in paths.items():
        if node == outfall or len(path) < 2:
            continue
        parent = path[-2]           # next hop toward the outfall
        d = Gu[node][parent]
        geom = d["geom"]
        # orient geometry in flow direction node -> parent
        if nkey(*geom.coords[0]) != node:
            geom = type(geom)(list(geom.coords)[::-1])
        Gd.add_edge(node, parent, length=d["length"], geom=geom)
    unreachable = [n for n in Gu.nodes if n not in paths]
    for n in unreachable:
        Gd.remove_node(n)
    assert nx.is_directed_acyclic_graph(Gd)
    for n in Gd.nodes:
        assert Gd.out_degree(n) <= 1
    return Gd, unreachable


def augment_cross_streets(Gu, Gd, sampler, units, frontage_m=40.0):
    """Review EDGE-1 fix: a node-spanning tree omits every loop-closing street edge —
    on the test boundary that was 25 km of streets with no pipe, forcing plots into
    long cross-block connections. Every omitted street edge with at least one loaded
    unit within `frontage_m` gets a sewer, split at its terrain SUMMIT into two head
    branches draining to the corner manholes (the standard crest-manhole layout; two
    back-to-back head nodes 1 m apart keep the one-outlet-per-manhole discipline).
    Streets with no frontage load deliberately stay unsewered — counted, not hidden."""
    if not units:
        return {"added": 0, "added_km": 0.0, "skipped_empty": 0, "skipped_km": 0.0}
    pts = [Point(u["x"], u["y"]) for u in units]
    tree = STRtree(pts)
    tree_pairs = {frozenset((u, v)) for u, v in Gd.edges}
    added = skipped = 0
    added_km = skipped_km = 0.0
    for u, v, d in Gu.edges(data=True):
        if frozenset((u, v)) in tree_pairs:
            continue
        geom = d["geom"]
        # networkx yields undirected edges in arbitrary (u, v) order — the corner each
        # chain drains into MUST come from the geometry ends, not the iteration order
        ca = nkey(*geom.coords[0])
        cb = nkey(*geom.coords[-1])
        if ca not in Gd or cb not in Gd:    # unreachable corner — stays out, reported upstream
            continue
        if geom.length < 6.0:               # corner sliver — nearby units reach the corners
            continue
        if len(tree.query(geom.buffer(frontage_m))) == 0:
            skipped += 1
            skipped_km += geom.length / 1000.0
            continue
        prof = sampler.profile(geom, 5.0)
        ch = max(prof, key=lambda r: r[3])[0]
        ch = min(max(ch, 2.0), geom.length - 2.0)
        for start, end, corner in ((max(ch - 0.5, 1.0), 0.0, ca),
                                   (min(ch + 0.5, geom.length - 1.0), geom.length, cb)):
            seg = substring(geom, start, end)          # oriented summit -> corner
            if seg is None or seg.length < 1.0 or seg.geom_type != "LineString":
                continue
            hk = nkey(*seg.coords[0])
            if hk in Gd:
                continue
            Gd.add_node(hk, x=seg.coords[0][0], y=seg.coords[0][1],
                        z=sampler.z(*seg.coords[0][:2]))
            Gd.add_edge(hk, corner, length=seg.length, geom=seg)
            added += 1
            added_km += seg.length / 1000.0
    assert nx.is_directed_acyclic_graph(Gd)
    for n in Gd.nodes:
        assert Gd.out_degree(n) <= 1
    return {"added": added, "added_km": round(added_km, 2),
            "skipped_empty": skipped, "skipped_km": round(skipped_km, 2)}
