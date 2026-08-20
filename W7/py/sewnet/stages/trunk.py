# -*- coding: utf-8 -*-
"""MainPipe — the trunk sewer, taken from the drawing rather than worked out.

W6 tried to FIND a main pipe by picking streets near a line the user described. It found a
2.1 km stub in the southern corner covering 13% of the area, so 92% of the town reached it
at a single point. That approach is gone.

From 20 August 2026 the main pipe is an input: `SHP/Main Pipe/Main Pipe.shp`, drawn by the
user. Both legs — one down the western side, one in from the east — drain to where they
meet at (449124.6, 2567769.4), and from there a 7.6 km trunk carries everything to the
existing Ibri STP at (444387, 2563352). The meeting point is the outfall for the test area;
it sits about 790 m OUTSIDE the test boundary, so the trunk is followed a little way past
the edge to reach it.

The drawn line is not a road centreline — it runs 8 to 13 m from the nearest street,
alongside the carriageway. So it is kept as its own corridor and side networks reach it by
short connections at right angles, which is how it would be built.

Where a side network may join is NOT free (user rule, 20 Aug): a connection lands on a
manhole on the main pipe, and those sit at the Table 12 spacing for the pipe size. Where a
street meets the main pipe square-on, the nearest manhole is nudged to that point instead,
so the connection can come in at right angles.
"""

import math

import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, unary_union

from ..criteria import DEFAULT
from ..model import key_of

SNAP = 0.5          # two trunk ends this close are the same point


def _k(x, y):
    return (round(x, 1), round(y, 1))


class MainPipe:
    """Reads the drawn trunk and hands back the piece that serves this area."""

    def __init__(self, path, crit=DEFAULT, lead_m=1200.0):
        self.path = path
        self.crit = crit
        self.lead_m = lead_m       # how far past the boundary to follow it to the outfall
        self.report = {}

    def build(self, boundary, confluence):
        """Returns (segments, outfall_xy, report).

        segments -- list of LineStrings forming one connected trunk, all draining to the
                    confluence;
        outfall  -- the confluence, snapped to the trunk.
        """
        gdf = gpd.read_file(self.path)
        conf = Point(*confluence)

        # 1. everything that touches this area, plus whatever links it to the outfall
        near = gdf[gdf.geometry.distance(boundary) < 1.0]
        G = nx.Graph()
        for i, row in gdf.iterrows():
            c = list(row.geometry.coords)
            G.add_edge(_k(*c[0][:2]), _k(*c[-1][:2]), idx=i, length=row.geometry.length)
        if not G:
            return [], None, {"error": "main pipe file is empty"}
        onode = min(G.nodes, key=lambda n: (n[0] - conf.x) ** 2 + (n[1] - conf.y) ** 2)

        keep = set(near.index)
        for i in list(near.index):
            c = list(gdf.geometry.iloc[i].coords)
            for end in (_k(*c[0][:2]), _k(*c[-1][:2])):
                if end not in G:
                    continue
                try:
                    path = nx.shortest_path(G, end, onode, weight="length")
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
                for u, v in zip(path, path[1:]):
                    keep.add(G[u][v]["idx"])

        # 2. Keep ONLY what this area needs: every piece of trunk inside the boundary,
        #    plus the shortest run of trunk from there down to the outfall. A blanket
        #    buffer does not work — it lets in kilometres of tail that serve other areas
        #    and never reach this one.
        V = nx.Graph()
        for i in sorted(keep):
            c = list(gdf.geometry.iloc[i].coords)
            for a, b2 in zip(c, c[1:]):
                ka, kb = _k(*a[:2]), _k(*b2[:2])
                if ka == kb:
                    continue
                V.add_edge(ka, kb, length=math.dist(ka, kb))
        if not V:
            return [], None, {"error": "no trunk near this area"}
        root = min(V.nodes, key=lambda n: (n[0] - conf.x) ** 2 + (n[1] - conf.y) ** 2)
        comp = next(c for c in nx.connected_components(V) if root in c)
        V = V.subgraph(comp).copy()
        _, paths = nx.single_source_dijkstra(V, root, weight="length")

        prepared = boundary.buffer(0)
        wanted = set()
        n_inside = 0
        for n, path in paths.items():
            if not prepared.contains(Point(n)):
                continue
            n_inside += 1
            for a, b2 in zip(path, path[1:]):          # the whole way back to the outfall
                wanted.add(frozenset((a, b2)))
        if not wanted:
            return [], None, {"error": "no trunk inside this area"}

        pieces = [LineString([tuple(a), tuple(b2)])
                  for a, b2 in (tuple(e) for e in wanted)]
        merged = linemerge(unary_union(pieces))
        segs = [p for p in getattr(merged, "geoms", [merged])
                if p.geom_type == "LineString" and p.length > 0.5]

        inside = sum(s.intersection(boundary).length for s in segs)
        total = sum(s.length for s in segs)
        self.report = {
            "source": "SHP/Main Pipe/Main Pipe.shp (given, not derived)",
            "features_considered": len(keep),
            "runs": len(segs),
            "trunk_km": round(total / 1000.0, 2),
            "inside_boundary_km": round(inside / 1000.0, 2),
            "lead_to_outfall_km": round((total - inside) / 1000.0, 2),
            "trunk_nodes_inside": n_inside,
            "outfall": [round(root[0], 2), round(root[1], 2)],
            "outfall_outside_boundary_m": 0 if boundary.contains(conf)
            else round(conf.distance(boundary.exterior)),
        }
        return segs, root, self.report


def chamber_chainages(length, dn_mm, crit=DEFAULT, fixed=()):
    """Where manholes go along the main pipe.

    Table 12 spacing for the pipe size (100 m to DN315, then 120 / 150 / 200 m), but any
    chainage in `fixed` is honoured first — those are the points where a street meets the
    main pipe square-on, and a manhole is wanted exactly there so the side network can come
    in at right angles (user rule, 20 Aug). The spacing rule then fills the gaps between
    them, so no gap ever exceeds the limit.
    """
    limit = crit.mh_max_spacing(dn_mm)
    stops = sorted({0.0, length} | {c for c in fixed if 0.0 < c < length})
    out = [stops[0]]
    for a, b in zip(stops, stops[1:]):
        gap = b - a
        n = max(1, math.ceil(gap / limit - 1e-9))
        for j in range(1, n + 1):
            out.append(a + gap * j / n)
    return out


def attach_to_roads(Gu, segs, outfall_xy, sampler, crit=DEFAULT, dn_mm=400,
                    max_conn_m=60.0, cluster_m=30.0, square_deg=45.0,
                    units=None, keep_k=None):
    """Put manholes on the main pipe and give the streets a way onto it.

    The main pipe is not a street — it runs 8 to 13 m to one side — so a side network
    cannot simply "be" on it. This adds:

      * a chamber every Table 12 spacing along the main pipe, AND one wherever a street
        comes at it square-on, so that street can connect at right angles;
      * a short connector at right angles from that street to that chamber.

    A street that meets the main pipe at a sharp angle is NOT given a connection — bringing
    a pipe in at a slant is what the inlet-angle rule exists to prevent. It reaches the main
    pipe through its neighbours instead.

    Returns (trunk_keys, report). Gu is modified in place.
    """
    line = max(segs, key=lambda s: s.length) if len(segs) > 1 else segs[0]
    for s in segs:                                  # any smaller runs stay as they are
        if s is not line:
            line = line if line.length >= s.length else s
    L = line.length

    def bearing_at(chn):
        a = line.interpolate(max(0.0, chn - 5.0))
        b = line.interpolate(min(L, chn + 5.0))
        return math.atan2(b.y - a.y, b.x - a.x)

    # --- which streets face the main pipe, and where do they meet it?
    wanted, cand = [], []
    for n, d in Gu.nodes(data=True):
        p = Point(d["x"], d["y"])
        if p.distance(line) > max_conn_m:
            continue
        chn = line.project(p)
        foot = line.interpolate(chn)
        if foot.distance(p) < 1.0:
            continue
        # direction of the street at this node, versus the main pipe
        best = None
        for m in Gu.neighbors(n):
            dm = Gu.nodes[m]
            ang = math.atan2(dm["y"] - d["y"], dm["x"] - d["x"])
            off = abs(math.degrees(ang - bearing_at(chn))) % 180.0
            off = min(off, 180.0 - off)             # 90 = square on to the pipe
            if best is None or abs(90.0 - off) < abs(90.0 - best):
                best = off
        if best is None or abs(90.0 - best) > square_deg:
            continue                                 # comes in at a slant: no connection
        cand.append((chn, n, foot, p.distance(foot), best))

    cand.sort()
    for chn, n, foot, dist, sq in cand:              # merge ones that land together
        if wanted and chn - wanted[-1][0] < cluster_m:
            continue
        wanted.append((chn, n, foot, dist, sq))

    # --- keep only the joins worth having.
    # Every join onto the main pipe becomes a chamber that will be deep once the whole town
    # drains through it, so they cost real money (user 2026-08-20). Rank the candidates by
    # how much land actually looks to each one, and keep the biggest `keep_k`. The rest of
    # the town still reaches the main pipe — through a neighbour's join.
    ranked = list(wanted)
    if keep_k is not None and units and len(wanted) > keep_k:
        import numpy as _np
        pts = _np.array([[u.x, u.y] for u in units])
        cx = _np.array([[w[2].x, w[2].y] for w in wanted])
        d2 = ((pts[:, None, :] - cx[None, :, :]) ** 2).sum(axis=2)
        nearest = d2.argmin(axis=1)
        load = _np.bincount(nearest, minlength=len(wanted))
        order = sorted(range(len(wanted)), key=lambda i: -load[i])[:keep_k]
        ranked = [wanted[i] for i in sorted(order)]
    wanted = ranked

    # --- chambers along the main pipe: spacing rule, honouring those meeting points
    chns = chamber_chainages(L, dn_mm, crit, fixed=[w[0] for w in wanted])
    tkeys, prev = [], None
    for chn in chns:
        p = line.interpolate(chn)
        k = key_of(p.x, p.y)
        if k in Gu and prev == k:
            continue
        Gu.add_node(k, x=p.x, y=p.y, z=float(sampler.z(p.x, p.y)), trunk=True)
        if prev is not None and prev != k:
            seg = LineString([(Gu.nodes[prev]["x"], Gu.nodes[prev]["y"]), (p.x, p.y)])
            Gu.add_edge(prev, k, length=seg.length, geom=seg, trunk=True)
        tkeys.append(k)
        prev = k

    # --- the connectors, at right angles onto the nearest chamber
    made, skipped = 0, 0
    for chn, n, foot, dist, sq in wanted:
        k = min(tkeys, key=lambda t: abs(line.project(Point(Gu.nodes[t]["x"],
                                                            Gu.nodes[t]["y"])) - chn))
        d = Gu.nodes[n]
        seg = LineString([(d["x"], d["y"]), (Gu.nodes[k]["x"], Gu.nodes[k]["y"])])
        if seg.length > max_conn_m * 1.5:
            skipped += 1
            continue
        Gu.add_edge(n, k, length=seg.length, geom=seg, connector=True)
        Gu.nodes[k]["trunk"] = True
        made += 1

    rep = {"trunk_chambers": len(tkeys), "trunk_km": round(L / 1000.0, 2),
           "join_candidates": len(cand), "joins_kept": len(wanted),
           "assumed_dn": dn_mm, "spacing_limit_m": crit.mh_max_spacing(dn_mm),
           "streets_facing_the_main_pipe": len(cand),
           "connection_points": made, "too_far_to_connect": skipped,
           "median_connector_m": round(sorted(w[3] for w in wanted)[len(wanted) // 2], 1)
           if wanted else 0}
    return tkeys, rep


def tree_to_trunk(Gu, trunk_path, outfall, crit=DEFAULT, climb_penalty=300.0,
                  arterial_factor=0.70, avoid=None, avoid_radius=60.0, avoid_factor=8.0,
                  depth_weight=500.0, smin_proxy=0.004, cost="climb"):
    """Every street drains to its NEAREST point on the main pipe, not to one far outfall.

    The main pipe itself runs downhill along its own path to the outfall. Everything else
    is worked out with a multi-start search: each street finds the closest joining point,
    counting uphill runs as expensive."""
    trunk = list(trunk_path)
    trunk_set = set(trunk)

    # cost to travel a street, seen from the joining point outwards
    S = nx.DiGraph()
    for u, v, d in Gu.edges(data=True):
        # a street may still route THROUGH the trunk line if there is no other way, but it
        # is made expensive so side networks do not run alongside the main pipe
        both = u in trunk_set and v in trunk_set
        zu, zv = Gu.nodes[u]["z"], Gu.nodes[v]["z"]
        base = d["length"] * (arterial_factor if d.get("arterial") else 1.0)
        # A crossing needs trenchless work and a join onto the main pipe becomes a deep
        # chamber. Both are allowed, but the search has to pay for them so it only takes
        # one where it genuinely helps (user 2026-08-20). An underpass is free.
        if d.get("crossing") and not d.get("free_crossing"):
            base += crit.CROSS_PENALTY_M
        if d.get("connector"):
            base += crit.CONNECT_PENALTY_M
        if both:
            base *= 50.0
        # streets that led to deep digging last time are made expensive, so the search
        # looks for another way round before we accept a pumping station
        if avoid:
            mid = d["geom"].interpolate(0.5, normalized=True)
            for ax, ay in avoid:
                if abs(mid.x - ax) < avoid_radius and abs(mid.y - ay) < avoid_radius:
                    base *= avoid_factor
                    break
        # What really matters is how much DEPTH a route adds. A pipe must fall at least
        # smin_proxy along its length; whatever the ground does not give, the trench has to.
        # Charging for that directly beats charging for "uphill", because a gentle downhill
        # that is flatter than the pipe needs still buries the pipe deeper.
        if cost == "depth":
            need = d["length"] * smin_proxy
            wuv = depth_weight * max(0.0, need - (zu - zv))
            wvu = depth_weight * max(0.0, need - (zv - zu))
        else:                                   # plain uphill cost
            wuv = climb_penalty * max(0.0, zu - zv)
            wvu = climb_penalty * max(0.0, zv - zu)
        S.add_edge(u, v, w=base + wuv)
        S.add_edge(v, u, w=base + wvu)

    sources = [n for n in trunk if n in S]
    dist, paths = nx.multi_source_dijkstra(S, set(sources), weight="w") if sources else ({}, {})

    Gd = nx.DiGraph()
    for n, d in Gu.nodes(data=True):
        Gd.add_node(n, **d)

    def add(child, parent):
        if not Gu.has_edge(child, parent):
            return
        geom = Gu[child][parent]["geom"]
        if key_of(*geom.coords[0]) != child:
            geom = LineString(list(geom.coords)[::-1])
        # carry the labels across, or the main pipe arrives at the design as if it were
        # ordinary street sewer and every one of its own pipes counts as a fresh join
        e = Gu[child][parent]
        Gd.add_edge(child, parent, length=e["length"], geom=geom,
                    trunk=bool(e.get("trunk")), connector=bool(e.get("connector")),
                    crossing=bool(e.get("crossing")),
                    free_crossing=bool(e.get("free_crossing")))

    # the main pipe drains along itself to its lowest point
    TS = nx.DiGraph()
    for u, v, d in Gu.subgraph(trunk_set).edges(data=True):
        zu, zv = Gu.nodes[u]["z"], Gu.nodes[v]["z"]
        base = d["length"]
        if cost == "depth":
            need = base * smin_proxy
            wuv = depth_weight * max(0.0, need - (zu - zv))
            wvu = depth_weight * max(0.0, need - (zv - zu))
        else:
            wuv = climb_penalty * max(0.0, zu - zv)
            wvu = climb_penalty * max(0.0, zv - zu)
        TS.add_edge(u, v, w=base + wuv)
        TS.add_edge(v, u, w=base + wvu)
    _, tpaths = nx.single_source_dijkstra(TS, outfall, weight="w")
    for n, pth in tpaths.items():
        if len(pth) >= 2:
            add(n, pth[-2])
    # every other street flows to its nearest joining point
    for n, path in paths.items():
        if n in trunk_set or len(path) < 2:
            continue
        add(n, path[-2])

    unreachable = [n for n in Gu.nodes if n not in paths and n not in trunk_set]
    for n in unreachable:
        if n in Gd:
            Gd.remove_node(n)
    assert nx.is_directed_acyclic_graph(Gd)
    for n in Gd.nodes:
        assert Gd.out_degree(n) <= 1
    return Gd, unreachable
