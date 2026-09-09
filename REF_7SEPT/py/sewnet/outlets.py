"""sewnet.outlets — Stage A, rule 2: follow the arrows until they stop.

Every junction points down its steepest outgoing run. Following the pointers ends at an
outlet: a junction on a target (the main pipe, or the STP), or a sink where every street
rises away. Each outlet is one catchment.

The raw ground has hundreds of sinks: cul-de-sacs falling away from their junction, small
hollows in a street. A pipe crosses those by going a little deeper, so they are not outlets
in any useful sense. They are filled on the street graph by priority flood from the targets
(the method pysheds uses on the raster), up to a spill height HOLLOW_M. A sink whose spill
is deeper than that stays an outlet of its own, labelled with the spill, because getting
out of it by gravity is a real cost that Stage B must decide. The catchment's ground is
tiled from the streets themselves (nearest-street cells), so the boundaries fall between
streets, not through them.
"""
import heapq
import math

import networkx as nx
from shapely.geometry import LineString, MultiPoint, Point
from shapely.ops import unary_union, voronoi_diagram
from shapely.strtree import STRtree


def find_targets(nodes_xy, main_pipe_geoms, stp_xy, target_m, stp_m):
    mp = unary_union(list(main_pipe_geoms))
    typ = {}
    for n, (x, y) in nodes_xy.items():
        p = Point(x, y)
        if mp.distance(p) <= target_m:
            typ[n] = "JOIN"
        elif math.dist((x, y), stp_xy) <= stp_m:
            typ[n] = "STP"
    return typ


def pointers(runs, targets):
    """node -> (downstream node, run index) along its steepest outgoing run on the raw
    ground. A target has no pointer: the flow has arrived."""
    out = {}
    for i, r in enumerate(runs):
        u = r["up"]
        if u in targets:
            continue
        if u not in out or r["grad"] > runs[out[u][1]]["grad"]:
            out[u] = (r["dn"], i)
    return out


def terminals(nodes, ptr, targets):
    term = {}
    for n0 in nodes:
        path = []
        n = n0
        while n not in term:
            if n in targets or n not in ptr:
                term[n] = n
                break
            path.append(n)
            n = ptr[n][0]
            if n in path:
                term[n] = n
                break
        t = term[n]
        for p in path:
            term[p] = t
    return term


# ------------------------------------------------------------ filling hollows
def adjacency(runs):
    adj = {}
    for i, r in enumerate(runs):
        adj.setdefault(r["up"], []).append((r["dn"], i))
        adj.setdefault(r["dn"], []).append((r["up"], i))
    return adj


def priority_flood(adj, z, sources):
    """Priority flood on the street graph from the sources. Returns the filled level of
    every reached node, the node each one drains to on the filled surface, and the order
    in which nodes were reached."""
    filled, parent, seq = {}, {}, {}
    heap = []
    for s in sources:
        filled[s] = z[s]
        parent[s] = None
        seq[s] = len(seq)
        heapq.heappush(heap, (z[s], s))
    while heap:
        f, n = heapq.heappop(heap)
        if f > filled[n]:
            continue
        for nb, _ in adj.get(n, []):
            if nb in filled:
                continue
            filled[nb] = max(z[nb], f)
            parent[nb] = n
            seq[nb] = len(seq)
            heapq.heappush(heap, (filled[nb], nb))
    return filled, parent, seq


def components_of(adj, subset):
    seen, comps = set(), []
    for n in subset:
        if n in seen:
            continue
        comp, stack = [], [n]
        seen.add(n)
        while stack:
            c = stack.pop()
            comp.append(c)
            for nb, _ in adj.get(c, []):
                if nb in subset and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        comps.append(comp)
    return comps


def resolve_outlets(runs, z, targets, hollow_m, raw_term):
    """Flood from the targets. A raw sink that would need more than hollow_m of fill to
    spill becomes an outlet of its own (a SINK, its spill recorded at that moment). A
    part of the graph with no street path to any target is an island: its lowest node
    becomes an outlet (a LOW point, spill None) and the island is then flooded from there,
    so its own hollows are filled and only its real basins remain. Repeat until stable.
    Returns the outlet of every node, the filled surface, the drain parents, the reach
    order, the spill of every outlet and the iteration log."""
    adj = adjacency(runs)
    nodes = list(z)
    sources = set(targets)
    spill = {t: 0.0 for t in targets}
    raw_sinks = {t for t in set(raw_term.values()) if t not in targets}
    iters = []
    filled = parent = seq = None
    for _ in range(30):
        filled, parent, seq = priority_flood(adj, z, sources)
        added = {}
        for s in raw_sinks:
            if s in sources or s not in filled:
                continue
            sp = filled[s] - z[s]
            if sp > hollow_m:
                added[s] = sp
        unreached = {n for n in nodes if n not in filled}
        islands = 0
        for comp in components_of(adj, unreached):
            low = min(comp, key=lambda n: z[n])
            added[low] = None
            islands += 1
        iters.append({"sources": len(sources),
                      "basins_added": sum(1 for v in added.values() if v is not None),
                      "islands_added": islands, "unreached": len(unreached)})
        if not added:
            break
        for s, sp in added.items():
            sources.add(s)
            spill[s] = sp
    src = {}

    def find_src(n):
        path = []
        while n not in src:
            p = parent.get(n)
            if p is None:
                src[n] = n
                break
            path.append(n)
            n = p
        s = src[n]
        for q in path:
            src[q] = s
        return s

    for n in nodes:
        if n in filled:
            find_src(n)
    return src, filled, parent, seq, spill, iters


def classify(fall, grad, flat_pct, level_m):
    if fall < -level_m:
        return "AGAINST"
    if abs(fall) < level_m:
        return "LEVEL"
    if grad < flat_pct:
        return "FLAT"
    return "NORMAL"


def flood_direction(runs, parent, filled, seq, flat_pct, level_m):
    """Point every run down the filled surface. Inside a filled hollow that means over the
    rim, against the raw ground; the run is then classed AGAINST and its gradient is
    negative (the ground rises along the flow)."""
    for r in runs:
        a, b = r["up"], r["dn"]
        if parent.get(b) == a:
            up, dn = b, a
        elif parent.get(a) == b:
            up, dn = a, b
        else:
            fa, fb = filled.get(a, r["z_up"]), filled.get(b, r["z_dn"])
            if fa > fb or (fa == fb and seq.get(a, 0) > seq.get(b, 0)):
                up, dn = a, b
            else:
                up, dn = b, a
        r["against_raw"] = up != r["up"]
        if up != r["up"]:
            r["geom"] = LineString(r["geom"].coords[::-1])
            r["up"], r["dn"] = up, dn
            r["z_up"], r["z_dn"] = r["z_dn"], r["z_up"]
            r["fall"] = -r["fall"]
            r["grad"] = -r["grad"]
        r["cls"] = classify(r["fall"], r["grad"], flat_pct, level_m)
    return runs


def catchments(runs, src, targets, spill):
    """Group runs by the outlet their downstream node drains to. Returns
    (catch_id per run, {catch_id: info})."""
    by_outlet = {}
    for i, r in enumerate(runs):
        t = src.get(r["dn"], r["dn"])
        by_outlet.setdefault(t, []).append(i)
    order = sorted(by_outlet, key=lambda t: -sum(runs[i]["len"] for i in by_outlet[t]))
    info = {}
    run_catch = [None] * len(runs)
    for k, t in enumerate(order):
        cid = f"C{k + 1:02d}"
        idx = by_outlet[t]
        for i in idx:
            run_catch[i] = cid
        typ = targets.get(t) or ("LOW" if spill.get(t) is None else "SINK")
        info[cid] = {"outlet": t, "type": typ, "runs": len(idx),
                     "km": sum(runs[i]["len"] for i in idx) / 1000.0,
                     "flat_km": sum(runs[i]["len"] for i in idx
                                    if runs[i]["cls"] in ("FLAT", "LEVEL")) / 1000.0,
                     "against_km": sum(runs[i]["len"] for i in idx
                                       if runs[i]["cls"] == "AGAINST") / 1000.0,
                     "spill_m": spill.get(t)}
    return run_catch, info


def catchment_polygons(runs, run_catch, envelope, step=15.0):
    """Nearest-street tiling of the area, grouped by catchment."""
    pts, labels, seen = [], [], set()
    for r, c in zip(runs, run_catch):
        g = r["geom"]
        n = max(1, int(g.length // step))
        for k in range(n + 1):
            p = g.interpolate(k * g.length / n)
            kk = (round(p.x, 1), round(p.y, 1))
            if kk in seen:
                continue
            seen.add(kk)
            pts.append(p)
            labels.append(c)
    vd = voronoi_diagram(MultiPoint(pts), envelope=envelope.buffer(300))
    cells = list(vd.geoms)
    tree = STRtree(cells)
    by = {}
    for p, c in zip(pts, labels):
        for k in tree.query(p):
            if cells[k].intersects(p):
                by.setdefault(c, []).append(cells[k])
                break
    polys = {}
    for c, cs in by.items():
        polys[c] = unary_union(cs).intersection(envelope).buffer(0)
    return polys


def colour_catchments(polys, n_colours=12):
    """A colour index per catchment such that touching catchments differ."""
    ids = list(polys)
    G = nx.Graph()
    G.add_nodes_from(ids)
    geoms = [polys[c] for c in ids]
    tree = STRtree(geoms)
    for i, c in enumerate(ids):
        gb = geoms[i].buffer(1.0)
        for j in tree.query(gb):
            if j != i and gb.intersects(geoms[j]):
                G.add_edge(c, ids[j])
    col = nx.greedy_color(G, strategy="largest_first")
    return {c: col[c] % n_colours for c in ids}
