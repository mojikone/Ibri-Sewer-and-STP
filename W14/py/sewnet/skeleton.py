"""sewnet.skeleton — Stage A rerun: the network as a tree (rules 3, 4 and 5).

Order of work, as agreed on 2026-09-07:

1. joins: among the outlets on the main pipe keep the biggest first and drop any within the
   join spacing of a kept one; only sub-mains join, a street that merely touches the main pipe
   runs into the nearest sub-main;
2. sub-mains: the heaviest low stem of each catchment, read off the flood tree by upstream
   street length, straight preferred where two children are near-equal, side stems where a
   child carries enough of its own;
3. the tree: every other junction routes to the nearest sub-main by the cheapest route in the
   least-depth sense (length plus the trench depth a flat or rising street forces on a pipe at
   the minimum gradient); one outlet per junction by construction;
4. branches: every street the tree does not use becomes a branch draining to its lower end,
   its head set back from the junction to the first house gate, or 10 m; tree heads on
   dead-end streets are trimmed to the first gate the same way;
5. connectors: each kept join is drawn from the outlet to the foot of the perpendicular on the
   main pipe.
"""
import heapq
import math

import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import substring
from shapely.strtree import STRtree


# ------------------------------------------------------------------ helpers
def run_lookup(runs):
    """(a, b) -> index of the shortest run joining a and b, both directions."""
    edge = {}
    for i, r in enumerate(runs):
        for a, b in ((r["up"], r["dn"]), (r["dn"], r["up"])):
            if (a, b) not in edge or r["len"] < runs[edge[(a, b)]]["len"]:
                edge[(a, b)] = i
    return edge


def accumulation(runs, parent, seq, edge):
    """Upstream street length at every node of the flood tree."""
    acc = {n: 0.0 for n in seq}
    for n in sorted(seq, key=lambda k: -seq[k]):        # children before parents
        p = parent.get(n)
        if p is None:
            continue
        i = edge.get((n, p))
        acc[p] = acc.get(p, 0.0) + acc[n] + (runs[i]["len"] if i is not None else 0.0)
    return acc


def _bearing(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _deflection(prev, cur, nxt):
    if prev is None:
        return 0.0
    d = math.degrees(_bearing(cur, nxt) - _bearing(prev, cur))
    return abs((d + 180.0) % 360.0 - 180.0)


# -------------------------------------------------------------------- joins
def select_joins(info, spacing_m):
    """Keep the biggest JOIN outlets first; drop any within spacing_m of a kept one.
    Returns the kept catchment ids and the dropped ones."""
    cands = sorted(((cid, i) for cid, i in info.items() if i["type"] == "JOIN"),
                   key=lambda x: -x[1]["km"])
    kept, kept_pts, dropped = [], [], []
    for cid, i in cands:
        p = Point(i["outlet"])
        if all(p.distance(q) >= spacing_m for q in kept_pts):
            kept.append(cid)
            kept_pts.append(p)
        else:
            dropped.append(cid)
    return kept, dropped


def restore_stranded_joins(info, kept, dropped, src2, spill2):
    """A dropped join whose streets ended up as an island (no street path to any kept
    outlet) gets its join back: it has no neighbour sub-main to run into. Returns the
    catchment ids to restore."""
    islands = {o for o, sp in spill2.items() if sp is None}
    back = []
    for cid in dropped:
        o = info[cid]["outlet"]
        if src2.get(o) in islands:
            back.append(cid)
    return back


class Streets:
    """The network's own streets, for the test 'is there a road between here and there'.
    A leg is blocked when it crosses any street run more than clear_m from its start."""

    def __init__(self, runs, clear_m=8.0):
        self.geoms = [r["geom"] for r in runs]
        self.tree = STRtree(self.geoms)
        self.clear = clear_m

    def blocked(self, leg):
        start = Point(leg.coords[0]).buffer(self.clear)
        body = leg.difference(start)
        if body.is_empty:
            return False
        for k in self.tree.query(body):
            if self.geoms[k].intersects(body):
                return True
        return False


def link_targets(sources, spill, z, ground, mp_union, stp_xy, min_grad, mp_invert_depth,
                 max_len, plots=None, existing=(), spacing_m=0.0, streets=None,
                 mp_max_len=None, stp_level=None):
    """Rule 3's direct link, as an outlet type. A basin or island low point whose ground can
    fall to the main pipe's invert, or to the STP, at min_grad over the straight distance, with
    no built or planned plot in the way and within max_len, is not a basin: it is an outlet with
    a direct link. The main pipe is measured at its invert, taken as mp_invert_depth below the
    ground at the foot of the link (a stated allowance). Returns {node: (type, plots crossed)}
    for the sources that qualify, preferring the main pipe when both work."""
    zstp = stp_level if stp_level is not None else float(ground.z_at([stp_xy[0]], [stp_xy[1]])[0])
    ex_pts = [Point(e) for e in existing]
    out = {}
    for s in sorted(sources):
        if s in spill and spill[s] == 0.0:          # already a target
            continue
        p = Point(s)
        # a link is a join: it keeps the join spacing from every existing target unless the
        # source is an island with no street path to anything (spill None)
        if spacing_m and spill.get(s) is not None and any(p.distance(q) < spacing_m for q in ex_pts):
            continue
        foot = mp_union.interpolate(mp_union.project(p))
        zf = float(ground.z_at([foot.x], [foot.y])[0]) - mp_invert_depth
        d_mp, d_stp = p.distance(foot), p.distance(Point(stp_xy))
        cand = []
        mp_cap = mp_max_len if mp_max_len is not None else max_len
        if 1.0 < d_mp <= mp_cap and (z[s] - zf) >= min_grad * d_mp:
            cand.append(("LINK-MP", LineString([p, foot]), d_mp))
        if 1.0 < d_stp <= max_len and (z[s] - zstp) >= min_grad * d_stp:
            cand.append(("LINK-STP", LineString([p, Point(stp_xy)]), d_stp))
        for typ, line, d in sorted(cand, key=lambda c: c[2]):
            crossed = plots.crossed(line) if plots else (0, 0)
            if crossed[0] != 0:
                continue
            # a link is for the case with no road between: where a street of the network
            # lies across the line, the water goes by the streets (engineer, 2026-09-07)
            if streets is not None and streets.blocked(line):
                continue
            out[s] = (typ, crossed[1])
            ex_pts.append(p)                   # the next link keeps its distance from this one
            break
    return out


def link_geometries(info, mp_union, stp_xy, corridor_paths=None):
    out = {}
    for cid, i in info.items():
        p = Point(i["outlet"])
        if i["type"] == "LINK-MP":
            out[cid] = LineString([p, mp_union.interpolate(mp_union.project(p))])
        elif i["type"] == "LINK-STP":
            cp = (corridor_paths or {}).get(i["outlet"])
            out[cid] = cp if cp is not None else LineString([p, Point(stp_xy)])
    return out


class TrunkCorridor:
    """NAMA's built trunk mains as a right-of-way a direct link may follow to the STP.
    Built from the trunk lines (manhole IDs with -TM-, or the given project codes), merged,
    turned into a graph of their end points, with the STP as the node nearest to it."""

    def __init__(self, built_gdf, stp_xy, codes=("8F-1",), snap_m=3.0, stp_reach_m=400.0,
                 envelope=None):
        from shapely.ops import linemerge, unary_union
        g = built_gdf
        tm = (g["US_MHID"].astype(str).str.contains("-TM-") |
              g["DS_MHID"].astype(str).str.contains("-TM-") |
              g["PROJECTCOD"].astype(str).isin(codes))
        flat = [LineString([(c[0], c[1]) for c in geom.coords]) for geom in g[tm].geometry
                if geom is not None and not geom.is_empty and geom.geom_type == "LineString"]
        merged = unary_union(flat)
        # only the corridor OUTSIDE the settlements: NAMA's trunk inside a settlement is a
        # street of our network and becomes a sub-main by rule 4 (engineer, 2026-09-07)
        if envelope is not None:
            merged = merged.difference(envelope)
        merged = linemerge(merged) if not merged.is_empty else merged
        self.lines = [LineString([(c[0], c[1]) for c in ln.coords]) for ln in
                      (merged.geoms if hasattr(merged, "geoms") else [merged])
                      if ln.geom_type == "LineString" and ln.length > 1.0]
        self.G = nx.Graph()
        key = lambda c: (round(c[0] / snap_m) * snap_m, round(c[1] / snap_m) * snap_m)  # noqa: E731
        self.key = key
        for i, ln in enumerate(self.lines):
            a, b = key(ln.coords[0]), key(ln.coords[-1])
            self.G.add_edge(a, b, w=ln.length, i=i)
        # the STP is one node, and every corridor end within reach of it is tied to it, so
        # the western and the eastern trunk, which end at different points of the works,
        # both lead there
        stp = Point(stp_xy)
        self.stp_node = ("STP",)
        tied = 0
        for n in list(self.G.nodes):
            if n == self.stp_node:
                continue
            d = Point(n).distance(stp)
            if d <= stp_reach_m:
                self.G.add_edge(n, self.stp_node, w=d, i=-1)
                tied += 1
        self.ok = tied > 0
        self.tied_ends = tied
        self.stp_xy = stp_xy

    def route(self, p, entry_m):
        """(path length to the STP, geometry) from point p via the nearest corridor line, or
        None if the corridor is farther than entry_m or does not lead to the STP."""
        if not self.ok or not self.lines:
            return None
        # the corridor is in pieces, some of them stubs that lead nowhere: try every piece
        # within reach, nearest first, and keep the shortest way to the STP
        cands = sorted(((self.lines[i].distance(p), i) for i in range(len(self.lines))
                        if self.lines[i].distance(p) <= entry_m))
        best = None
        for d1, k in cands:
            ln = self.lines[k]
            ch = ln.project(p)
            entry = ln.interpolate(ch)
            a, b = self.key(ln.coords[0]), self.key(ln.coords[-1])
            for end, along, sub in ((a, ch, substring(ln, ch, 0) if ch > 0 else None),
                                    (b, ln.length - ch, substring(ln, ch, ln.length))):
                try:
                    L = nx.shortest_path_length(self.G, end, self.stp_node, weight="w")
                    path = nx.shortest_path(self.G, end, self.stp_node, weight="w")
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
                total = d1 + along + L
                if best is None or total < best[0]:
                    best = (total, end, path, sub, entry, d1)
        if best is None:
            return None
        total, end, path, sub, entry, d1 = best
        coords = [(p.x, p.y), (entry.x, entry.y)]
        if sub is not None and not sub.is_empty:
            coords += list(sub.coords)[1:]
        for u, v in zip(path[:-1], path[1:]):
            i = self.G[u][v]["i"]
            if i < 0:                       # the tie from a corridor end to the STP
                continue
            seg = self.lines[i]
            cs = list(seg.coords)
            if self.key(cs[0]) != u:
                cs = cs[::-1]
            coords += cs[1:]
        coords.append(self.stp_xy)
        return total, LineString(coords), entry, d1


def corridor_entry_targets(nodes, z, ground, corridor, streets, entry_m, spacing_m, min_grad,
                           max_len, mp_union=None, mp_near_m=40.0, plots=None, stp_level=None):
    """NAMA's trunk corridor as a second target. A street junction within entry_m of the
    corridor, with no street and no built or planned plot between it and the corridor, whose
    ground falls to the STP at min_grad along the corridor within max_len, is an entry join.
    Entries are kept lowest first and spaced spacing_m apart, like joins on the main pipe.
    A corridor point under the drawn main pipe is not an entry (that is the main pipe's job).
    Returns ({node: 'LINK-STP'}, {node: geometry})."""
    if corridor is None or not corridor.ok:
        return {}, {}
    zstp = stp_level if stp_level is not None else \
        float(ground.z_at([corridor.stp_xy[0]], [corridor.stp_xy[1]])[0])
    cands = []
    for n in nodes:
        p = Point(n)
        r = corridor.route(p, entry_m)
        if r is None:
            continue
        total, geom, entry, d1 = r
        if mp_union is not None and mp_union.distance(entry) <= mp_near_m:
            continue
        if total > max_len or (z[n] - zstp) < min_grad * total:
            continue
        leg = LineString([(p.x, p.y), (entry.x, entry.y)])
        if streets is not None and streets.blocked(leg):
            continue
        if plots is not None and plots.crossed(leg)[0]:
            continue
        cands.append((z[n], n, geom))
    cands.sort()
    kept, pts, paths = {}, [], {}
    for zz, n, geom in cands:
        p = Point(n)
        if all(p.distance(q) >= spacing_m for q in pts):
            kept[n] = "LINK-STP"
            paths[n] = geom
            pts.append(p)
    return kept, paths


def corridor_links(sources, spill, z, ground, corridor, entry_m, min_grad, plots=None,
                   mp_union=None, mp_invert_depth=3.0, mp_near_m=40.0, max_len=4000.0,
                   streets=None, mp_max_len=None, stp_level=None):
    """Rule 3 along NAMA's corridor: a basin or island low point that can reach the built
    trunk corridor within entry_m, crossing no built or planned plot on that leg, links along
    it. Where the corridor entry lies under the drawn main pipe (the eastern trunk), the link
    is a LINK-MP to the main pipe's invert at the entry, not a ride to the STP; elsewhere the
    whole way to the STP must fall at min_grad and be no longer than max_len.
    Returns {node: (type, plots crossed, geometry)}."""
    if corridor is None or not corridor.ok:
        return {}
    zstp = stp_level if stp_level is not None else \
        float(ground.z_at([corridor.stp_xy[0]], [corridor.stp_xy[1]])[0])
    out = {}
    for s in sorted(sources):
        if s in spill and spill[s] == 0.0:
            continue
        p = Point(s)
        r = corridor.route(p, entry_m)
        if r is None:
            continue
        total, geom, entry, d1 = r
        leg = LineString([(p.x, p.y), (entry.x, entry.y)])
        crossed = plots.crossed(leg) if plots else (0, 0)
        if crossed[0] != 0:
            continue
        if streets is not None and streets.blocked(leg):
            continue
        if mp_union is not None and mp_union.distance(entry) <= mp_near_m:
            zf = float(ground.z_at([entry.x], [entry.y])[0]) - mp_invert_depth
            cap = mp_max_len if mp_max_len is not None else max_len
            if 1.0 < d1 <= cap and (z[s] - zf) >= min_grad * d1:
                out[s] = ("LINK-MP", crossed[1], leg)
            continue
        if total <= max_len and (z[s] - zstp) >= min_grad * total:
            out[s] = ("LINK-STP", crossed[1], geom)
    return out


# ---------------------------------------------------------------- sub-mains
def sub_mains(runs, parent, seq, src, stem_min_m, side_min_m):
    """The stems of every catchment on the flood tree. Returns the set of run indices that are
    sub-main, the stem parent of every sub-main node (toward the outlet), and a report."""
    edge = run_lookup(runs)
    acc = accumulation(runs, parent, seq, edge)
    children = {}
    for n, p in parent.items():
        if p is not None:
            children.setdefault(p, []).append(n)
    outlets = {s for s in src.values()}
    submain = set()
    stem_parent = {}
    n_stems = 0
    queue = [(o, None) for o in outlets]
    while queue:
        cur, prev = queue.pop()
        n_stems += 1
        while True:
            ch = [c for c in children.get(cur, [])
                  if acc[c] + runs[edge[(c, cur)]]["len"] >= stem_min_m]
            if not ch:
                break
            heaviest = max(ch, key=lambda c: acc[c])
            near = [c for c in ch if acc[c] >= 0.75 * acc[heaviest]]
            best = min(near, key=lambda c: _deflection(prev, cur, c))
            for c in ch:
                if c is not best and acc[c] + runs[edge[(c, cur)]]["len"] >= side_min_m:
                    submain.add(edge[(c, cur)])
                    stem_parent[c] = cur
                    queue.append((c, cur))
            submain.add(edge[(best, cur)])
            stem_parent[best] = cur
            prev, cur = cur, best
    km = sum(runs[i]["len"] for i in submain) / 1000.0
    return submain, stem_parent, {"stems": n_stems, "submain_runs": len(submain),
                                  "submain_km": round(km, 2)}


# ------------------------------------------------------ sub-mains by street
def street_chains(runs, straight_deg):
    """Streets as the draftsman meant them: a chain of runs that continues straight through
    junctions, within straight_deg of deflection. At a junction the two runs that continue
    most nearly straight are paired; every run belongs to exactly one chain.
    Returns chains as lists of run indices, each with its node sequence."""
    at = {}
    for i, r in enumerate(runs):
        at.setdefault(r["up"], []).append(i)
        at.setdefault(r["dn"], []).append(i)

    def other(i, n):
        r = runs[i]
        return r["dn"] if r["up"] == n else r["up"]

    def heading(i, n):
        """Bearing of run i leaving node n, taken over its first 12 m."""
        g = runs[i]["geom"]
        if _key(g.coords[0]) == n:
            q = g.interpolate(min(g.length, 12.0))
            return _bearing(g.coords[0], (q.x, q.y))
        q = g.interpolate(max(0.0, g.length - 12.0))
        return _bearing(g.coords[-1], (q.x, q.y))

    pair = {}                       # (node, run) -> the run it continues into at that node
    for n, idx in at.items():
        if len(idx) < 2:
            continue
        cands = []
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = idx[a], idx[b]
                d = math.degrees(heading(i, n) - heading(j, n))
                d = abs((d + 180.0) % 360.0 - 180.0)
                turn = 180.0 - d          # 180 = straight through
                if turn <= straight_deg:
                    cands.append((turn, i, j))
        used = set()
        for turn, i, j in sorted(cands):
            if i in used or j in used:
                continue
            pair[(n, i)] = j
            pair[(n, j)] = i
            used.add(i)
            used.add(j)

    seen = set()
    chains = []
    for i0 in range(len(runs)):
        if i0 in seen:
            continue
        # walk both ways from i0
        seq = [i0]
        seen.add(i0)
        for direction in (0, 1):
            i = i0
            n = runs[i]["dn"] if direction == 0 else runs[i]["up"]
            while True:
                j = pair.get((n, i))
                if j is None or j in seen:
                    break
                seen.add(j)
                if direction == 0:
                    seq.append(j)
                else:
                    seq.insert(0, j)
                i = j
                n = other(j, n)
        # node sequence along the chain
        nodes = []
        for k, i in enumerate(seq):
            r = runs[i]
            if k == 0:
                nxt = runs[seq[1]] if len(seq) > 1 else None
                if nxt is not None and r["up"] in (nxt["up"], nxt["dn"]):
                    nodes += [r["dn"], r["up"]]
                else:
                    nodes += [r["up"], r["dn"]]
            else:
                nodes.append(other(i, nodes[-1]))
        chains.append({"runs": seq, "nodes": nodes,
                       "len": sum(runs[i]["len"] for i in seq)})
    return chains


def _key(pt, nd=2):
    return (round(float(pt[0]), nd), round(float(pt[1]), nd))


def cut_at_crests(chains, runs, z, crest_m):
    """Rule 6: a chain is cut at every crest, an interior node that stands more than crest_m
    above the lowest ground on BOTH sides of it along the chain, so no sub-main runs over a
    hill. Returns the pieces as chains."""
    out = []
    for c in chains:
        nodes, seq = c["nodes"], c["runs"]
        zz = [z[n] for n in nodes]
        cuts = []
        for i in range(1, len(nodes) - 1):
            if zz[i] >= zz[i - 1] and zz[i] >= zz[i + 1]:
                if zz[i] - min(zz[:i]) > crest_m and zz[i] - min(zz[i + 1:]) > crest_m:
                    cuts.append(i)
        if not cuts:
            out.append(c)
            continue
        bounds = [0] + cuts + [len(nodes) - 1]
        for a, b in zip(bounds[:-1], bounds[1:]):
            part_nodes = nodes[a:b + 1]
            part_runs = seq[a:b]
            if part_runs:
                out.append({"runs": part_runs, "nodes": part_nodes,
                            "len": sum(runs[i]["len"] for i in part_runs), "cut": True})
    return out


def cut_at_divides(chains, runs, src, filled=None, level_m=0.0):
    """Rule 6 in the flood's terms: a chain is cut wherever the flood changes direction along
    it, at a divide (both neighbouring runs flow away) or a sag (both flow in), and wherever
    two neighbouring nodes drain to different outlets, at the end the water leaves from. A
    sub-main then never runs against the fall: measured 2026-09-07, a 2.3 km street chain
    from the west settlement's interior climbed 7 m to a join and dug 20 m because its
    'lower end' had been taken as the end nearer an outlet.

    Only a DECIDED run counts, one whose ends differ by more than level_m on the filled
    surface. On level ground the flood's arrow is a tie-break, and a straight street there
    flips every few runs (measured 2026-09-07 on the east grid: the long north-south streets
    fell below the 250 m floor and the 30 km half of the settlement kept one sub-main).
    Direction on level ground is the chain's own choice, rule 5."""
    out = []
    for c in chains:
        nodes, seq = c["nodes"], c["runs"]
        d = []
        for k, i in enumerate(seq):
            a, b = nodes[k], nodes[k + 1]
            fa = filled.get(a, runs[i]["z_up"]) if filled is not None else 1.0
            fb = filled.get(b, runs[i]["z_dn"]) if filled is not None else 0.0
            if filled is not None and abs(fa - fb) <= level_m:
                d.append(0)                                   # level: the chain decides
            else:
                d.append(1 if runs[i]["up"] == a else -1)
        cuts = set()
        last = None                      # (index, direction) of the last decided run
        for k, dk in enumerate(d):
            if dk == 0:
                continue
            if last is not None and last[1] != dk:
                # the flood turns between run last[0] and run k: cut at the end of the
                # earlier decided run, the level runs between go with the later one
                cuts.add(last[0] + 1)
            last = (k, dk)
        for k in range(len(seq)):
            if d[k] != 0 and src.get(nodes[k]) != src.get(nodes[k + 1]):
                cuts.add(k if d[k] == 1 else k + 1)
        cuts = sorted(x for x in cuts if 0 < x < len(nodes) - 1)
        if not cuts:
            out.append(c)
            continue
        bounds = [0] + cuts + [len(nodes) - 1]
        for a, b in zip(bounds[:-1], bounds[1:]):
            part_runs = seq[a:b]
            if part_runs:
                out.append({"runs": part_runs, "nodes": nodes[a:b + 1],
                            "len": sum(runs[i]["len"] for i in part_runs),
                            "cut": c.get("cut", False), "divide": True})
    return out


def cut_at_sags_and_outlets(chains, runs, z, src, parent, crest_m):
    """Rule 4 as the engineer set it on 2026-09-08, a sub-main runs the whole street, with the
    two cuts the ground forces: at a sag (an interior node more than crest_m below the ground
    on both sides along the chain) where the water leaves the street, that is where the
    flood's parent of the sag is not the next node along the chain; and between two nodes
    that drain to different outlets. A flip of the arrow on level ground never cuts."""
    out = []
    for c in chains:
        nodes, seq = c["nodes"], c["runs"]
        zz = [z[n] for n in nodes]
        cuts = set()
        for i in range(1, len(nodes) - 1):
            if zz[i] <= zz[i - 1] and zz[i] <= zz[i + 1]:
                if min(zz[:i]) - zz[i] > crest_m and min(zz[i + 1:]) - zz[i] > crest_m:
                    p_ = parent.get(nodes[i])
                    if p_ not in (nodes[i - 1], nodes[i + 1]):
                        cuts.add(i)
        for k in range(len(seq)):
            a, b = nodes[k], nodes[k + 1]
            if src.get(a) != src.get(b):
                # the run between them goes with the side the water leaves toward
                cuts.add(k if runs[seq[k]]["up"] == a else k + 1)
        cuts = sorted(x for x in cuts if 0 < x < len(nodes) - 1)
        if not cuts:
            out.append(c)
            continue
        bounds = [0] + cuts + [len(nodes) - 1]
        for a, b in zip(bounds[:-1], bounds[1:]):
            part_runs = seq[a:b]
            if part_runs:
                out.append({"runs": part_runs, "nodes": nodes[a:b + 1],
                            "len": sum(runs[i]["len"] for i in part_runs),
                            "cut": c.get("cut", False), "sag_or_outlet": True})
    return out


def sub_mains_by_chains(runs, chains, parent, src, chain_min_m, link_m=0.0, filled=None,
                        level_m=0.0):
    """Rule 4 as the engineer drew it: the sub-mains are the long straight streets. From each
    outlet, take the longest chain whose lower end touches the outlet or a sub-main already
    chosen, cut it at the first chosen node it meets, and repeat until no chain of
    chain_min_m or more attaches. A chain's lower end is the end its runs flow to under the
    final flood (cut_at_divides makes that one direction per chain). A chain whose lower end
    does not touch a chosen node may still attach through a connector of at most link_m
    along the flood tree, and the connector becomes sub-main with it (a 2.8 km valley street
    was left as laterals on 2026-09-07 because its foot was one short bend from the
    sub-main). Returns the sub-main run set, the stem parent of every sub-main node, and a
    report."""
    edge = run_lookup(runs)
    # distance to the outlet along the flood tree
    dist = {}

    def d_out(n):
        if n in dist:
            return dist[n]
        path = []
        m = n
        while m not in dist:
            p = parent.get(m)
            if p is None:
                dist[m] = 0.0
                break
            path.append(m)
            m = p
        for q in reversed(path):
            p = parent[q]
            i = edge.get((q, p))
            dist[q] = dist[p] + (runs[i]["len"] if i is not None else 0.0)
        return dist[n]

    by_outlet = {}
    for n, o in src.items():
        by_outlet.setdefault(o, set()).add(n)
    submain, stem_parent = set(), {}
    n_chains = 0
    for outlet, members in by_outlet.items():
        S = {outlet}
        cand = [c for c in chains if c["len"] >= chain_min_m
                and any(n in members for n in c["nodes"])]
        while True:
            best = None
            for c in cand:
                nodes = c["nodes"]
                if nodes[0] in S and nodes[-1] in S and all(n in S for n in nodes):
                    continue
                a, b = nodes[0], nodes[-1]
                # the lower end is where the flood flows to along the chain's own DECIDED
                # runs; a chain of level runs is pointed toward the outlet along the flood
                fwd = 0
                for k, i in enumerate(c["runs"]):
                    if filled is not None and abs(filled.get(nodes[k], 0.0)
                                                  - filled.get(nodes[k + 1], 0.0)) <= level_m:
                        continue
                    fwd += 1 if runs[i]["up"] == nodes[k] else -1
                if fwd < 0 or (fwd == 0 and d_out(a) <= d_out(b)):
                    seq_nodes, seq_runs = nodes[::-1], c["runs"][::-1]   # upstream first
                else:
                    seq_nodes, seq_runs = nodes, c["runs"]
                # cut at the first chosen node from the upstream end; the lower end must be in S
                cut = None
                for k, n in enumerate(seq_nodes):
                    if n in S:
                        cut = k
                        break
                if cut == 0:
                    continue
                conn_nodes, conn_runs = [], []
                if cut is None:
                    # reach S along the flood tree from the lower end, within link_m
                    m, Lc = seq_nodes[-1], 0.0
                    on_chain = set(seq_nodes)
                    while m not in S:
                        q = parent.get(m)
                        i = edge.get((m, q)) if q is not None else None
                        if i is None or src.get(q) != outlet or q in on_chain:
                            conn_nodes = None      # no way, or the flood turns back along
                            break                  # the chain itself (a level tail)
                        Lc += runs[i]["len"]
                        if Lc > link_m:
                            conn_nodes = None
                            break
                        conn_nodes.append(q)
                        conn_runs.append(i)
                        m = q
                    if conn_nodes is None:
                        continue
                    cut = len(seq_nodes) - 1
                part_nodes = seq_nodes[:cut + 1] + conn_nodes
                part_runs = seq_runs[:cut] + conn_runs
                L = sum(runs[i]["len"] for i in seq_runs[:cut])
                if L < chain_min_m:
                    continue
                if best is None or L > best[0]:
                    best = (L, part_nodes, part_runs, c)
            if best is None:
                break
            L, part_nodes, part_runs, c = best
            for k in range(len(part_nodes) - 1):
                u, v = part_nodes[k], part_nodes[k + 1]
                if u not in stem_parent and u != outlet:
                    stem_parent[u] = v
                S.add(u)
            S.add(part_nodes[-1])
            submain.update(part_runs)
            n_chains += 1
            cand = [x for x in cand if x is not c]
    km = sum(runs[i]["len"] for i in submain) / 1000.0
    return submain, stem_parent, {"chains_used": n_chains, "submain_runs": len(submain),
                                  "submain_km": round(km, 2)}


# --------------------------------------------------------------------- tree
def trunk_routes(runs, z, levels, ttype, pockets, props_of, depth_weight, max_depth, cover,
                 per_prop, stem=None, trunk_runs=None, try_targets=6, max_len=8000.0,
                 take_shortfall=False, violation_max=10.0):
    """Rule 3 as a designed trunk along the streets (2026-09-08). A pocket, biggest first, is
    sized on the properties behind it, and a route is searched through the street graph at
    that pipe's Table 11 gradient with rule 5's cost, to the cheapest target whose arrival
    level the laid invert clears: the works inlet, a main-pipe join's invert, or a trunk
    already accepted. The lay along the route must stay within max_depth everywhere. An
    accepted trunk fixes the stem of every node on it and offers its own inverts as levels
    to later pockets, so a second pocket joins the first trunk rather than running its own.
    Returns the accepted trunks, the stems, the trunk runs and the levels."""
    from . import quicklay as Q
    stem = dict(stem or {})
    trunk_runs = set(trunk_runs or ())
    levels = dict(levels)
    ttype = dict(ttype)
    adj = {}
    for i, r in enumerate(runs):
        u, v, L = r["up"], r["dn"], r["len"]
        adj.setdefault(u, []).append((v, L, i))
        adj.setdefault(v, []).append((u, L, i))
    accepted = {}
    total_props = float(sum(props_of.get(q, 0.0) for q in pockets))
    for p0 in pockets:
        if p0 in levels or p0 in stem or p0 not in adj:
            continue
        own = float(props_of.get(p0, 0.0))
        # sized on the pocket alone first; then on every pocket still waiting, because the
        # later ones join the first trunk and a bigger pipe takes a flatter gradient
        sizes = [(own, "own")]          # sized on what drains to it; a pipe sized on pockets
                                        # that never join is laid two sizes smaller and digs
                                        # deeper than the route was checked at (2026-09-08)
        tried = []
        nearly = []                       # routes within 12 m that arrive under the level
        for n_prop, basis in sizes:
            hit = _trunk_try(runs, z, adj, levels, ttype, p0, n_prop, per_prop, depth_weight,
                             max_depth, cover, try_targets, max_len, tried, nearly)
            if hit is None and take_shortfall and nearly:
                # everything on gravity: the least violation is taken and reported, unless
                # it is past violation_max, where the pocket is a pump and not a story
                cand_ = min(nearly, key=lambda h: h[9])
                if cand_[9] <= violation_max:
                    hit = cand_
                    basis = basis + ", with a violation"
                else:
                    tried.append(("least violation", f"{cand_[9]:.1f} m", "past the cap"))
            if hit is not None:
                path, ridx, prof, t, length, mx, inv, dn, smin = hit[:9]
                short = hit[9] if len(hit) > 9 else 0.0
                for (a, b), i in zip(zip(path[:-1], path[1:]), ridx):
                    if a not in stem:
                        stem[a] = b
                    trunk_runs.add(i)
                    if a not in levels:
                        levels[a] = prof[a]
                        ttype[a] = "TRUNK"
                accepted[p0] = {"target": t, "type": ttype.get(t, "?"), "path": path,
                                "runs": ridx, "len": round(length), "dn": dn, "smin": smin,
                                "max_depth": round(mx, 2), "arrives": round(inv, 2),
                                "level": round(levels[t], 2), "props": n_prop,
                                "sized_on": basis, "under_m": round(max(0.0, levels[t] - inv), 2),
                                "over_m": round(max(0.0, mx - max_depth), 2)}
                break
        if p0 not in accepted:
            accepted.setdefault("_refused", {})[p0] = tried
    refused = accepted.pop("_refused", {})
    return accepted, stem, trunk_runs, levels, ttype, refused


def _trunk_try(runs, z, adj, levels, ttype, p0, n_prop, per_prop, depth_weight, max_depth,
               cover, try_targets, max_len, tried, nearly=None):
    """One sizing of a trunk from p0: the route search at that pipe's gradient, every
    reachable target tried cheapest first. Returns the accepted route or None."""
    from . import quicklay as Q
    dn = Q.size_for(Q.peak_ls(n_prop, 0.0, per_prop))
    smin = Q.T11[dn]
    if True:
        cost, prev = {p0: 0.0}, {}
        heap = [(0.0, p0)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > cost[u]:
                continue
            if u in levels and u != p0:          # a route ends at a target or a trunk
                continue
            for v, L, i in adj.get(u, []):
                w = L + depth_weight * max(0.0, smin * L - (z[u] - z[v]))
                if d + w < cost.get(v, float("inf")):
                    cost[v] = d + w
                    prev[v] = (u, i)
                    heapq.heappush(heap, (d + w, v))
        cands = sorted((c, t) for t, c in cost.items() if t in levels and t != p0)
        if try_targets:
            cands = cands[:try_targets]
        for c, t in cands:
            path, ridx = [t], []
            while path[-1] != p0:
                u, i = prev[path[-1]]
                path.append(u)
                ridx.append(i)
            path.reverse()
            ridx.reverse()
            length = sum(runs[i]["len"] for i in ridx)
            if length > max_len:
                tried.append((f"DN{dn}", ttype.get(t), round(length), "too long"))
                continue
            inv = z[p0] - cover
            prof = {p0: inv}
            mx, where = 0.0, None
            for (a, b), i in zip(zip(path[:-1], path[1:]), ridx):
                inv = min(inv - smin * runs[i]["len"], z[b] - cover)
                dep = z[b] - inv
                prof[b] = inv
                if dep > mx:
                    mx, where = dep, b
            excess = max(0.0, mx - max_depth)
            short = max(0.0, levels[t] - inv)
            if excess > 0:
                tried.append((f"DN{dn}", ttype.get(t), round(length),
                              f"{max_depth} m passed by {excess:.1f} m at {tuple(round(v) for v in where)}"))
            if short > 0:
                tried.append((f"DN{dn}", ttype.get(t), round(length),
                              f"arrives {short:.1f} m under the level"))
            if excess > 0 or short > 0:
                if nearly is not None:
                    # the violation in metres: depth past the limit plus arrival shortfall
                    nearly.append((path, ridx, prof, t, length, mx, inv, dn, smin,
                                   excess + short))
                continue
            return path, ridx, prof, t, length, mx, inv, dn, smin, 0.0
    return None


def break_stem_cycles(stem, keep, runs, submain):
    """A trunk's stems override a street chain's; where the chain pointed the other way the
    two now chase each other. Walk every stem; on a cycle, drop the first stem in it that is
    not in `keep` (the trunks), and take the run it stood on out of the sub-main set, so the
    tree search routes it like any street (2026-09-08, after the divide cut came off)."""
    stem = dict(stem)
    edge = run_lookup(runs)
    dropped = 0
    changed = True
    while changed:
        changed = False
        for start in list(stem):
            seen, n = [], start
            while n in stem and n not in seen:
                seen.append(n)
                n = stem[n]
            if n in stem and n in seen:                 # a cycle through n
                cyc = seen[seen.index(n):]
                victim = next((u for u in cyc if u not in keep), None)
                if victim is None:
                    victim = cyc[0]
                v = stem.pop(victim)
                i = edge.get((victim, v))
                if i is not None:
                    submain.discard(i)
                dropped += 1
                changed = True
                break
    return stem, submain, dropped


def build_tree(runs, z, submain, stem_parent, depth_weight, smin, outlets=(), free_w=0.01,
               src=None, submain_discount=0.5):
    """Route every junction to its outlet by the least-depth route, rule 5's cost: length
    plus depth_weight metres per metre of trench a pipe at smin is forced to. A search edge
    from m to n carries the cost of a pipe FLOWING n -> m. A sub-main run costs the same
    times submain_discount, so the collector is preferred but its length still counts:
    measured 2026-09-07 with free sub-main edges, the west settlement's interior went
    1,000 m east to the nearest sub-main node and 650 m along it to the rim, 13.1 m deep,
    past an 850 m street to the same rim. A sub-main node is entered only along its own
    stem. With src given, a lateral routes only inside its own catchment (rule 1 decides
    the catchment, rules 4-5 work inside it); a street between two catchments is left over
    and becomes a branch with its head at the next gate. Returns the tree parent of every
    node (None at an outlet) and the route cost."""
    S = nx.DiGraph()
    for i, r in enumerate(runs):
        u, v, L = r["up"], r["dn"], r["len"]
        need = L * smin
        cost_uv = L + depth_weight * max(0.0, need - (z[u] - z[v]))     # pipe flows u -> v
        cost_vu = L + depth_weight * max(0.0, need - (z[v] - z[u]))     # pipe flows v -> u
        if i in submain:
            # the stem is fixed: only its own direction, at the discount
            if stem_parent.get(u) == v:
                S.add_edge(v, u, w=cost_uv * submain_discount, i=i)
            elif stem_parent.get(v) == u:
                S.add_edge(u, v, w=cost_vu * submain_discount, i=i)
            continue
        if src is not None and src.get(u) != src.get(v):
            continue
        if u not in stem_parent:            # u is not on a sub-main: it may drain to v
            S.add_edge(v, u, w=cost_uv, i=i)
        if v not in stem_parent:
            S.add_edge(u, v, w=cost_vu, i=i)
    sources = {s for s in outlets if s in S}
    for s_ in stem_parent.values():         # a stem that ends where no outlet is listed
        if s_ not in stem_parent and s_ in S:
            sources.add(s_)
    dist, paths = nx.multi_source_dijkstra(S, sources, weight="w")
    par = dict(stem_parent)
    for n, p in paths.items():
        if n in sources or n in stem_parent:
            continue
        if len(p) >= 2:
            par[n] = p[-2]
    unreached = [n for n in z if n not in dist and n not in stem_parent]
    return par, dist, unreached


def orient_tree(runs, par, z, level_m, flat_pct):
    """Split the runs into tree runs, pointed child -> parent, and the leftovers."""
    edge = run_lookup(runs)
    tree_idx = {}
    for n, p in par.items():
        if p is None:
            continue
        i = edge.get((n, p))
        if i is None:
            continue
        tree_idx[i] = (n, p)
    tree, extra = [], []
    for i, r in enumerate(runs):
        if i in tree_idx:
            child, parent = tree_idx[i]
            _point(r, child, parent, z, level_m, flat_pct)
            tree.append(i)
        else:
            extra.append(i)
    return tree, extra


def _point(r, up, dn, z, level_m, flat_pct):
    """Orient run r from up to dn and recompute its signed fall and class."""
    if r["up"] != up:
        r["geom"] = LineString(r["geom"].coords[::-1])
    r["up"], r["dn"] = up, dn
    r["z_up"], r["z_dn"] = z[up], z[dn]
    r["fall"] = r["z_up"] - r["z_dn"]
    r["grad"] = 100.0 * r["fall"] / r["len"] if r["len"] > 0 else 0.0
    f, g = r["fall"], r["grad"]
    r["cls"] = ("AGAINST" if f < -level_m else "LEVEL" if abs(f) < level_m
                else "FLAT" if g < flat_pct else "NORMAL")


# ----------------------------------------------------------------- branches
class Gates:
    """Where the first house gate sits along a street: the first plot centroid within
    search_m, dropped square onto the street."""

    def __init__(self, plots_path, envelope, search_m=45.0, link_pad_m=5000.0):
        gdf = gpd.read_file(plots_path, encoding="utf-8")
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
        area = envelope.buffer(search_m)
        self.pts = [g.centroid for g in gdf.geometry if g.intersects(area)]
        self.tree = STRtree(self.pts) if self.pts else None
        self.search = search_m
        wide = envelope.buffer(link_pad_m)
        cls = gdf["CLASS"].astype(str).values if "CLASS" in gdf.columns else ["?"] * len(gdf)
        self.polys, self.pcls = [], []
        for g, c in zip(gdf.geometry, cls):
            if g.intersects(wide):
                self.polys.append(g)
                self.pcls.append(c)
        self.ptree = STRtree(self.polys) if self.polys else None

    def crossed(self, line):
        """(built or planned plots crossed, agricultural plots crossed) by a line."""
        if self.ptree is None:
            return (0, 0)
        bp = ag = 0
        for k in self.ptree.query(line):
            if self.polys[k].intersects(line):
                if self.pcls[k] == "A":
                    ag += 1
                else:
                    bp += 1
        return (bp, ag)

    def first_gate(self, geom, min_ch=3.0):
        if self.tree is None:
            return None
        best = None
        for k in self.tree.query(geom.buffer(self.search)):
            p = self.pts[k]
            if geom.distance(p) > self.search:
                continue
            ch = geom.project(p)
            if ch >= min_ch and (best is None or ch < best):
                best = ch
        return best


def make_branches(runs, extra, z, dist, gates, level_m, flat_pct, fanout_m=10.0, min_len=15.0):
    """Every leftover street drains to its lower end; its head is set back from the other
    junction to the first gate, or fanout_m. Returns the branch runs (new dicts), the unpiped
    head gaps, and the dropped ones."""
    branches, gaps, dropped = [], [], []
    for i in extra:
        r = runs[i]
        u, v = r["up"], r["dn"]
        if abs(z[u] - z[v]) > level_m:
            head, drain = (u, v) if z[u] > z[v] else (v, u)
        else:
            head, drain = (u, v) if dist.get(u, 1e18) >= dist.get(v, 1e18) else (v, u)
        g = r["geom"] if r["up"] == head else LineString(r["geom"].coords[::-1])
        L = g.length
        if L < min_len:
            dropped.append(i)
            continue
        h = gates.first_gate(g) if gates else None
        how = "gate"
        if h is None or h > L - fanout_m:
            h, how = fanout_m, "offset"
        h = min(h, L - fanout_m)
        piped = substring(g, h, L)
        gap = substring(g, 0, h)
        hk = (round(piped.coords[0][0], 2), round(piped.coords[0][1], 2))
        zh = z[head] + (z[drain] - z[head]) * (h / L)
        b = dict(r)
        b.update({"geom": piped, "up": hk, "dn": drain, "len": piped.length, "z_up": zh,
                  "z_dn": z[drain], "head_of": head, "head_how": how, "head_offset": h,
                  "tier": "branch", "source_run": i})
        b["fall"] = b["z_up"] - b["z_dn"]
        b["grad"] = 100.0 * b["fall"] / b["len"] if b["len"] > 0 else 0.0
        f, gr = b["fall"], b["grad"]
        b["cls"] = ("AGAINST" if f < -level_m else "LEVEL" if abs(f) < level_m
                    else "FLAT" if gr < flat_pct else "NORMAL")
        branches.append(b)
        gaps.append(gap)
    return branches, gaps, dropped


def trim_tree_heads(runs, tree, par, gates, fanout_m=10.0, min_len=15.0, receiving=()):
    """A tree run that starts at a true dead-end head starts at the first gate instead. A node
    that receives any pipe, a tree child or a branch, is not a head and its run is left whole
    (found 2026-09-07: 256 branches were draining into a junction whose run had been trimmed
    away from under them)."""
    has_child = set(par.values()) | set(receiving)
    gaps, trimmed = [], 0
    for i in tree:
        r = runs[i]
        if r["up"] in has_child:
            continue
        g = r["geom"]
        L = g.length
        if L < min_len:
            continue
        h = gates.first_gate(g) if gates else None
        if h is None or h < 1.0 or h > L - fanout_m:
            continue
        gaps.append(substring(g, 0, h))
        piped = substring(g, h, L)
        zh = r["z_up"] + (r["z_dn"] - r["z_up"]) * (h / L)
        r.update({"geom": piped, "len": piped.length, "z_up": zh,
                  "head_how": "gate", "head_offset": h})
        r["fall"] = r["z_up"] - r["z_dn"]
        r["grad"] = 100.0 * r["fall"] / r["len"] if r["len"] > 0 else 0.0
        trimmed += 1
    return gaps, trimmed


# --------------------------------------------------------------- connectors
def connectors(info, kept, main_pipe_union):
    out = {}
    for cid in kept:
        p = Point(info[cid]["outlet"])
        foot = main_pipe_union.interpolate(main_pipe_union.project(p))
        out[cid] = LineString([p, foot])
    return out


# ------------------------------------------------------------------- checks
def check_tree(tree_runs, branches):
    """No loops, one outlet per node. Returns (is_dag, max_out_degree)."""
    G = nx.DiGraph()
    for r in tree_runs:
        G.add_edge(r["up"], r["dn"])
    for b in branches:
        G.add_edge(b["up"], b["dn"])
    return nx.is_directed_acyclic_graph(G), max((d for _, d in G.out_degree()), default=0)
