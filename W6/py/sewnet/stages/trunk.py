"""TrunkBuilder — the main pipe, and the points where side networks join it.

Until now everything drained to one point, so sewage from the far side of the area had to
travel the whole way there. That is what makes pipes go deep and turns into pumping
stations. With a main pipe running along the edge of the area, each side network only has
to reach the nearest point on it — much shorter, much shallower.

The user sets where the main pipe runs (19 August: along the western edge, then along the
southern side next to the dual carriageway). This stage finds the real streets that follow
that line, chains them into one path, and marks the joining points along it.

Nothing here is guessed about the route: the wanted line is given, and the code only picks
the streets that follow it.
"""

import math

import networkx as nx
from shapely.geometry import LineString, Point

from ..criteria import DEFAULT
from ..model import key_of


class TrunkBuilder:
    def __init__(self, sampler, crit=DEFAULT, hug_m=60.0):
        self.sampler = sampler
        self.crit = crit
        self.hug_m = hug_m          # how close to the wanted line a street must be
        self.report = {}

    def _wanted_line(self, boundary, sides=("west", "south")):
        """The line the main pipe should follow — taken from the REAL boundary outline,
        not a rectangle round it, because the area is not a rectangle. The west part is
        the outline where it lies in the western quarter, the south part where it lies in
        the southern quarter."""
        minx, miny, maxx, maxy = boundary.bounds
        w_cut, s_cut = minx + 0.30 * (maxx - minx), miny + 0.30 * (maxy - miny)
        ring = list(boundary.exterior.coords)
        parts = []
        run = []
        for i in range(len(ring) - 1):
            a, b = ring[i], ring[i + 1]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            wanted = (("west" in sides and mx <= w_cut) or ("south" in sides and my <= s_cut)
                      or ("east" in sides and mx >= maxx - 0.30 * (maxx - minx))
                      or ("north" in sides and my >= maxy - 0.30 * (maxy - miny)))
            if wanted:
                run.append(a)
            elif len(run) > 1:
                parts.append(LineString(run))
                run = []
            else:
                run = []
        if len(run) > 1:
            parts.append(LineString(run))
        return parts or [boundary.exterior]

    def build(self, Gu, boundary, sides=("west", "south")):
        """Pick the streets that follow the wanted line.

        Rather than searching for one path across the whole town (which wanders into the
        middle), take every street close to the wanted line and keep the largest connected
        run of them. That hugs the edge by construction. The main pipe then drains to the
        lowest point on itself, which is where the outfall goes.

        Returns (trunk_nodes, outfall_node, report)."""
        want = self._wanted_line(boundary, sides)

        def off(x, y):
            p = Point(x, y)
            return min(w.distance(p) for w in want)

        for hug in (self.hug_m, self.hug_m * 2, self.hug_m * 4, self.hug_m * 8):
            near = [n for n, d in Gu.nodes(data=True) if off(d["x"], d["y"]) <= hug]
            if len(near) < 5:
                continue
            sub = Gu.subgraph(near)
            comps = sorted(nx.connected_components(sub), key=len, reverse=True)
            if comps and len(comps[0]) >= 20:
                trunk = set(comps[0])
                break
        else:
            return [], None, {"error": "no streets found along the wanted line"}

        # the main pipe drains to its own lowest point
        outfall = min(trunk, key=lambda n: Gu.nodes[n]["z"])
        offs = sorted(off(Gu.nodes[n]["x"], Gu.nodes[n]["y"]) for n in trunk)
        length = sum(d["length"] for u, v, d in Gu.subgraph(trunk).edges(data=True))
        self.report = {"trunk_nodes": len(trunk), "trunk_km": round(length / 1000.0, 2),
                       "sides": list(sides), "hug_m": hug,
                       "offset_from_wanted_line_m": {
                           "median": round(offs[len(offs) // 2], 1), "max": round(offs[-1], 1)},
                       "outfall_z": round(Gu.nodes[outfall]["z"], 2)}
        return sorted(trunk), outfall, self.report


def tree_to_trunk(Gu, trunk_path, outfall, crit=DEFAULT, climb_penalty=300.0,
                  arterial_factor=0.70, avoid=None, avoid_radius=60.0, avoid_factor=8.0):
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
        S.add_edge(u, v, w=base + climb_penalty * max(0.0, zu - zv))
        S.add_edge(v, u, w=base + climb_penalty * max(0.0, zv - zu))

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
        Gd.add_edge(child, parent, length=Gu[child][parent]["length"], geom=geom)

    # the main pipe drains along itself to its lowest point
    TS = nx.DiGraph()
    for u, v, d in Gu.subgraph(trunk_set).edges(data=True):
        zu, zv = Gu.nodes[u]["z"], Gu.nodes[v]["z"]
        base = d["length"]
        TS.add_edge(u, v, w=base + climb_penalty * max(0.0, zu - zv))
        TS.add_edge(v, u, w=base + climb_penalty * max(0.0, zv - zu))
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
