"""TreeBuilder — S2: the loop-free collection tree.

Donor concept (SWNETWROK graph.py) upgraded: the spanning tree comes from a
COST-WEIGHTED Dijkstra instead of hop-count BFS — cost = length x road-class factor +
climb penalty — so collectors prefer proper streets over alleys and avoid routing over
humps. Loop-free by construction: each chamber keeps exactly one downstream reach.
"""

import math

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.ops import substring
from shapely.strtree import STRtree

from ..criteria import DEFAULT
from ..model import Network, key_of

CLIMB_PENALTY = 300.0    # m equivalent length per m of uphill climb (method choice)
ARTERIAL_FACTOR = 0.70   # prefer wide corridors (method choice)


class TreeBuilder:
    """segments + terrain -> Network (chambers at road nodes, reaches on streets)."""

    def __init__(self, sampler, crit=DEFAULT, expected_outfall=None, outfall_override=None):
        self.sampler = sampler
        self.crit = crit
        self.expected_outfall = expected_outfall
        self.outfall_override = outfall_override
        self.report = {}

    # ---------------- undirected road graph ----------------
    def build_undirected(self, segs):
        Gu = nx.Graph()
        for i, g in enumerate(segs):
            a, b = key_of(*g.coords[0]), key_of(*g.coords[-1])
            if a == b:
                continue
            for k, pt in ((a, g.coords[0]), (b, g.coords[-1])):
                if k not in Gu:
                    Gu.add_node(k, x=pt[0], y=pt[1], z=self.sampler.z(pt[0], pt[1]))
            if Gu.has_edge(a, b) and Gu[a][b]["length"] <= g.length:
                continue
            Gu.add_edge(a, b, length=g.length, geom=g, idx=i)
        return Gu

    def mark_arterials(self, Gu, top_quantile=0.90, k_samples=400):
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

    # ---------------- outfall ----------------
    def pick_outfall(self, Gu, boundary, edge_tol=30.0):
        cands = [(n, d) for n, d in Gu.nodes(data=True)
                 if boundary.exterior.distance(Point(d["x"], d["y"])) <= edge_tol]
        if self.outfall_override is not None:
            names = list(Gu.nodes)
            arr = np.array([[Gu.nodes[n]["x"], Gu.nodes[n]["y"]] for n in names])
            chosen = names[cKDTree(arr).query(np.array(self.outfall_override))[1]]
        else:
            chosen = min(cands, key=lambda t: t[1]["z"])[0]
        d = Gu.nodes[chosen]
        rep = {"node": chosen, "x": d["x"], "y": d["y"], "z": d["z"],
               "boundary_candidates": len(cands)}
        if self.expected_outfall is not None:
            dist = math.hypot(d["x"] - self.expected_outfall[0],
                              d["y"] - self.expected_outfall[1])
            rep.update(expected_xy=self.expected_outfall, dist_to_expected_m=dist,
                       agrees=dist <= 150.0)
        return chosen, rep

    # ---------------- directed tree ----------------
    def build_tree(self, Gu, outfall):
        """Dijkstra outward from the outfall; each chamber's next hop is its outlet.

        A search edge u->v corresponds to FLOW v->u, which climbs when z_u > z_v; that
        climb is penalised so the tree prefers downhill-friendly streets."""
        Gs = nx.DiGraph()
        for u, v, d in Gu.edges(data=True):
            zu, zv = Gu.nodes[u]["z"], Gu.nodes[v]["z"]
            base = d["length"] * (ARTERIAL_FACTOR if d.get("arterial") else 1.0)
            Gs.add_edge(u, v, w=base + CLIMB_PENALTY * max(0.0, zu - zv))
            Gs.add_edge(v, u, w=base + CLIMB_PENALTY * max(0.0, zv - zu))
        try:
            _, paths = nx.single_source_dijkstra(Gs, outfall, weight="w")
        except nx.NodeNotFound:
            return nx.DiGraph(), list(Gu.nodes)

        Gd = nx.DiGraph()
        for n, d in Gu.nodes(data=True):
            Gd.add_node(n, **d)
        for node, path in paths.items():
            if node == outfall or len(path) < 2:
                continue
            parent = path[-2]
            geom = Gu[node][parent]["geom"]
            if key_of(*geom.coords[0]) != node:
                geom = LineString(list(geom.coords)[::-1])
            Gd.add_edge(node, parent, length=Gu[node][parent]["length"], geom=geom)
        unreachable = [n for n in Gu.nodes if n not in paths]
        for n in unreachable:
            Gd.remove_node(n)
        assert nx.is_directed_acyclic_graph(Gd)
        return Gd, unreachable

    # ---------------- cross-street coverage ----------------
    def augment_cross_streets(self, Gu, Gd, units):
        """A node-spanning tree omits every loop-closing street edge — on the test area
        that was 22 km of streets with no pipe. Every omitted street with a loaded unit
        within CROSS_STREET_FRONTAGE gets a sewer, split at its terrain summit into two
        head branches draining to the corners (crest-manhole layout). Streets with no
        frontage load deliberately stay unsewered — counted, not hidden."""
        C = self.crit
        if not units:
            return {"added": 0, "added_km": 0.0, "skipped_empty": 0, "skipped_km": 0.0}
        tree = STRtree([Point(u.x, u.y) for u in units])
        in_tree = {frozenset((u, v)) for u, v in Gd.edges}
        added = skipped = 0
        added_km = skipped_km = 0.0
        off = C.FANOUT_OFFSET_M
        for u, v, d in Gu.edges(data=True):
            if frozenset((u, v)) in in_tree:
                continue
            geom = d["geom"]
            ca, cb = key_of(*geom.coords[0]), key_of(*geom.coords[-1])
            if ca not in Gd or cb not in Gd or geom.length < 6.0:
                continue
            if len(tree.query(geom.buffer(C.CROSS_STREET_FRONTAGE))) == 0:
                skipped += 1
                skipped_km += geom.length / 1000.0
                continue
            L = geom.length
            prof = self.sampler.profile(geom, 5.0)
            ch = min(max(max(prof, key=lambda r: r[3])[0], 2.0), L - 2.0)
            # crest layout under the one-outlet rule: the crest chamber drains ONE way;
            # the other branch starts a full offset past it, so heads are never neighbours
            if L < 2 * off + 10.0:
                low = ca if self.sampler.z(*geom.coords[0][:2]) < \
                    self.sampler.z(*geom.coords[-1][:2]) else cb
                plan = [(L - off, L, cb)] if low is cb else [(off, 0.0, ca)]
            else:
                plan = [(min(ch, L - off), 0.0, ca), (max(ch + off, off), L, cb)]
            for start, end, corner in plan:
                seg = substring(geom, start, end)
                if seg is None or seg.geom_type != "LineString" or seg.length < 1.0:
                    continue
                hk = key_of(*seg.coords[0])
                if hk in Gd:
                    continue
                Gd.add_node(hk, x=seg.coords[0][0], y=seg.coords[0][1],
                            z=self.sampler.z(*seg.coords[0][:2]))
                Gd.add_edge(hk, corner, length=seg.length, geom=seg)
                added += 1
                added_km += seg.length / 1000.0
        assert nx.is_directed_acyclic_graph(Gd)
        return {"added": added, "added_km": round(added_km, 2),
                "skipped_empty": skipped, "skipped_km": round(skipped_km, 2)}

    # ---------------- stage entry point ----------------
    def run(self, segs, boundary, units=None):
        Gu = self.build_undirected(segs)
        self.mark_arterials(Gu)
        outfall, of_rep = self.pick_outfall(Gu, boundary)
        Gd, unreachable = self.build_tree(Gu, outfall)
        aug = self.augment_cross_streets(Gu, Gd, units or [])
        self.report = {"outfall": of_rep, "unreachable": len(unreachable),
                       "nodes": Gd.number_of_nodes(), "edges": Gd.number_of_edges(),
                       "augmentation": aug}
        return Gd, outfall, of_rep
