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
                 mp_max_len=None):
    """Rule 3's direct link, as an outlet type. A basin or island low point whose ground can
    fall to the main pipe's invert, or to the STP, at min_grad over the straight distance, with
    no built or planned plot in the way and within max_len, is not a basin: it is an outlet with
    a direct link. The main pipe is measured at its invert, taken as mp_invert_depth below the
    ground at the foot of the link (a stated allowance). Returns {node: (type, plots crossed)}
    for the sources that qualify, preferring the main pipe when both work."""
    zstp = float(ground.z_at([stp_xy[0]], [stp_xy[1]])[0])
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

    def __init__(self, built_gdf, stp_xy, codes=("8F-1",), snap_m=3.0, stp_reach_m=400.0):
        from shapely.ops import linemerge, unary_union
        g = built_gdf
        tm = (g["US_MHID"].astype(str).str.contains("-TM-") |
              g["DS_MHID"].astype(str).str.contains("-TM-") |
              g["PROJECTCOD"].astype(str).isin(codes))
        flat = [LineString([(c[0], c[1]) for c in geom.coords]) for geom in g[tm].geometry
                if geom is not None and not geom.is_empty and geom.geom_type == "LineString"]
        merged = linemerge(unary_union(flat))
        self.lines = [LineString([(c[0], c[1]) for c in ln.coords]) for ln in
                      (merged.geoms if hasattr(merged, "geoms") else [merged])]
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
                           max_len, mp_union=None, mp_near_m=40.0, plots=None):
    """NAMA's trunk corridor as a second target. A street junction within entry_m of the
    corridor, with no street and no built or planned plot between it and the corridor, whose
    ground falls to the STP at min_grad along the corridor within max_len, is an entry join.
    Entries are kept lowest first and spaced spacing_m apart, like joins on the main pipe.
    A corridor point under the drawn main pipe is not an entry (that is the main pipe's job).
    Returns ({node: 'LINK-STP'}, {node: geometry})."""
    if corridor is None or not corridor.ok:
        return {}, {}
    zstp = float(ground.z_at([corridor.stp_xy[0]], [corridor.stp_xy[1]])[0])
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
                   streets=None, mp_max_len=None):
    """Rule 3 along NAMA's corridor: a basin or island low point that can reach the built
    trunk corridor within entry_m, crossing no built or planned plot on that leg, links along
    it. Where the corridor entry lies under the drawn main pipe (the eastern trunk), the link
    is a LINK-MP to the main pipe's invert at the entry, not a ride to the STP; elsewhere the
    whole way to the STP must fall at min_grad and be no longer than max_len.
    Returns {node: (type, plots crossed, geometry)}."""
    if corridor is None or not corridor.ok:
        return {}
    zstp = float(ground.z_at([corridor.stp_xy[0]], [corridor.stp_xy[1]])[0])
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


# --------------------------------------------------------------------- tree
def build_tree(runs, z, submain, stem_parent, depth_weight, smin, outlets=(), free_w=0.01):
    """Route every junction to the nearest sub-main node, or outlet, by the least-depth route.
    A search edge from m to n carries the cost of a pipe FLOWING n -> m. Returns the tree
    parent of every node (None at an outlet) and the route cost."""
    S = nx.DiGraph()
    for i, r in enumerate(runs):
        u, v, L = r["up"], r["dn"], r["len"]
        need = L * smin
        cost_uv = L + depth_weight * max(0.0, need - (z[u] - z[v]))     # pipe flows u -> v
        cost_vu = L + depth_weight * max(0.0, need - (z[v] - z[u]))     # pipe flows v -> u
        if i in submain:
            cost_uv = cost_vu = free_w
        S.add_edge(v, u, w=cost_uv, i=i)
        S.add_edge(u, v, w=cost_vu, i=i)
    sources = set(stem_parent) | set(stem_parent.values()) | set(outlets)
    sources = {s for s in sources if s in S}
    dist, paths = nx.multi_source_dijkstra(S, sources, weight="w")
    par = dict(stem_parent)
    for n, p in paths.items():
        if n in sources:
            continue
        if len(p) >= 2:
            par[n] = p[-2]
    unreached = [n for n in z if n not in dist]
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
