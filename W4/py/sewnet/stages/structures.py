"""StructureResolver — ONE PHYSICAL OUTLET PER STRUCTURE (user rule 2026-08-18).

A spanning tree gives every NODE one outgoing reach, but two chambers can sit at the same
physical point (road noding rounds to the centimetre; cross-street heads land beside
existing junctions). Two chambers at one point, each with its own outlet, IS a two-outlet
junction on the ground — the thing the rule forbids.

  1. merge every cluster of chambers within MH_SNAP_M — one structure;
  2. re-derive the tree over the merged reach set, because merging can also close a loop
     (two chambers at one point may additionally be linked by a path). This restores
     one-outlet-and-no-loops in a single step and marks the leftovers as loop-closers;
  3. offset every leftover so it STARTS clear of the chamber: at the next house
     connection along its own alignment, or FANOUT_OFFSET_M when that sits nearer.
     A branch too short to keep a clear start is dropped and reported;
  4. slide any remaining branch head clear of neighbouring chambers.
"""

import math

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from shapely.ops import substring

from ..criteria import DEFAULT
from ..model import Network, key_of

SLIDE_PASSES = 8


class StructureResolver:
    def __init__(self, sampler, crit=DEFAULT):
        self.sampler = sampler
        self.crit = crit
        self.report = {"merged": 0, "fanouts": 0, "offset_branches": 0,
                       "dropped_branches": 0, "offsets_m": []}

    # ---------------- 1. merge coincident chambers ----------------
    def _merge(self, net: Network):
        keys = list(net.chambers)
        pts = np.array([[net.chambers[k].x, net.chambers[k].y] for k in keys])
        parent = {k: k for k in keys}

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for i, j in cKDTree(pts).query_pairs(self.crit.MH_SNAP_M):
            ra, rb = find(keys[i]), find(keys[j])
            if ra != rb:
                parent[ra] = rb

        clusters = {}
        for k in keys:
            clusters.setdefault(find(k), []).append(k)
        deg = {k: 0 for k in keys}
        for r in net.reaches:
            deg[r.up] = deg.get(r.up, 0) + 1
            deg[r.dn] = deg.get(r.dn, 0) + 1

        rep_of = {}
        for members in clusters.values():
            if len(members) == 1:
                rep_of[members[0]] = members[0]
                continue
            keep = next((m for m in members if net.chambers[m].kind == "outfall"), None)
            if keep is None:
                keep = max(members, key=lambda m: deg.get(m, 0))
            for m in members:
                rep_of[m] = keep
            self.report["merged"] += len(members) - 1

        for r in list(net.reaches):
            r.up, r.dn = rep_of[r.up], rep_of[r.dn]
            if r.up == r.dn:
                net.remove_reach(r)
                continue
            cs = list(r.geom.coords)
            cs[0] = net.chambers[r.up].xy
            cs[-1] = net.chambers[r.dn].xy
            r.geom = LineString(cs)
            r.length = r.geom.length
        for k in keys:
            if rep_of[k] != k:
                net.chambers.pop(k, None)

    # ---------------- 2-3. re-derive the tree, offset the leftovers ----------------
    def _rederive_and_offset(self, net: Network, units):
        Gu = nx.Graph()
        for idx, r in enumerate(net.reaches):
            if Gu.has_edge(r.up, r.dn) and Gu[r.up][r.dn]["length"] <= r.length:
                continue
            Gu.add_edge(r.up, r.dn, length=r.length, idx=idx)
        dist, paths = nx.single_source_dijkstra(Gu, net.outfall, weight="length")

        keep_edge, tree_parent = {}, {}
        for n, path in paths.items():
            if len(path) < 2:
                continue
            tree_parent[n] = path[-2]
            keep_edge[frozenset((n, path[-2]))] = True

        kept, extras, seen = [], [], set()
        for r in net.reaches:
            ek = frozenset((r.up, r.dn))
            if keep_edge.get(ek) and ek not in seen:
                seen.add(ek)
                child = r.up if tree_parent.get(r.up) == r.dn else r.dn
                parent = tree_parent.get(child)
                if parent is None:
                    extras.append(r)
                    continue
                if r.up != child:                      # orient toward the outfall
                    r.up, r.dn = child, parent
                    r.geom = LineString(list(r.geom.coords)[::-1])
                kept.append(r)
            else:
                extras.append(r)
        net.reaches = kept

        unit_tree = cKDTree(np.array([[u.x, u.y] for u in units])) if units else None
        off = self.crit.FANOUT_OFFSET_M

        def start_chainage(geom):
            """Next house connection along this alignment, else the fixed offset."""
            if unit_tree is None:
                return off
            d = off
            while d < min(geom.length - 2.0, 60.0):
                pt = geom.interpolate(d)
                if len(unit_tree.query_ball_point([pt.x, pt.y], 30.0)) > 0:
                    return d
                d += 2.0
            return off

        for r in extras:
            self.report["fanouts"] += 1
            du, dv = dist.get(r.up, 1e18), dist.get(r.dn, 1e18)
            geom = r.geom if dv <= du else LineString(list(r.geom.coords)[::-1])
            dn_key = r.dn if dv <= du else r.up
            if geom.length < off + 5.0:
                self.report["dropped_branches"] += 1
                continue
            cut = min(start_chainage(geom), geom.length - 5.0)
            seg = substring(geom, cut, geom.length)
            if seg is None or seg.geom_type != "LineString" or seg.length < 5.0:
                self.report["dropped_branches"] += 1
                continue
            hk = key_of(*seg.coords[0])
            if hk in net.chambers:
                self.report["dropped_branches"] += 1
                continue
            net.add_chamber(seg.coords[0][0], seg.coords[0][1],
                            self.sampler.z(*seg.coords[0][:2]), "head")
            net.add_reach(hk, dn_key, seg)
            self.report["offset_branches"] += 1
            self.report["offsets_m"].append(round(cut, 1))

    # ---------------- 4. branch starts stand clear ----------------
    def _slide_heads(self, net: Network):
        off = self.crit.FANOUT_OFFSET_M
        for pass_i in range(SLIDE_PASSES):
            ind, outd = net.degrees()
            heads = [k for k in net.chambers
                     if ind.get(k, 0) == 0 and outd.get(k, 0) == 1
                     and net.chambers[k].kind != "outfall"]
            if not heads:
                break
            allk = list(net.chambers)
            pts = np.array([[net.chambers[k].x, net.chambers[k].y] for k in allk])
            kd = cKDTree(pts)
            out_of = net.outgoing()
            moved = 0
            for h in heads:
                if h not in net.chambers:
                    continue
                rs = [q for q in out_of.get(h, []) if q in net.reaches]
                if len(rs) != 1:
                    continue
                r = rs[0]
                near = [allk[j] for j in kd.query_ball_point([net.chambers[h].x,
                                                             net.chambers[h].y], off)
                        if allk[j] in net.chambers and allk[j] != h and allk[j] != r.dn]
                if not near:
                    continue
                worst = min(math.dist(net.chambers[h].xy, net.chambers[k].xy) for k in near)
                need = off - worst + 0.5
                if pass_i == SLIDE_PASSES - 1:
                    need = max(need, off)
                drop = r.length - need < 5.0
                seg = None if drop else substring(r.geom, need, r.length)
                if drop or seg is None or seg.geom_type != "LineString" or seg.length < 5.0 \
                        or key_of(*seg.coords[0]) in net.chambers:
                    net.remove_reach(r)
                    del net.chambers[h]
                    self.report["dropped_branches"] += 1
                    moved += 1
                    continue
                hk = net.add_chamber(seg.coords[0][0], seg.coords[0][1],
                                     self.sampler.z(*seg.coords[0][:2]), "head")
                del net.chambers[h]
                r.up, r.geom, r.length = hk, seg, seg.length
                self.report["offset_branches"] += 1
                self.report["offsets_m"].append(round(need, 1))
                moved += 1
            if moved == 0:
                break

    # ---------------- stage entry point ----------------
    def run(self, net: Network, units=None):
        self._merge(net)
        self._rederive_and_offset(net, units or [])
        self._slide_heads(net)
        net.drop_orphans()
        net.refresh_kinds()
        net.assert_tree()          # the two binding rules, enforced here
        return net
