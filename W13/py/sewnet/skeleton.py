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


def link_targets(sources, spill, z, ground, mp_union, stp_xy, min_grad, mp_invert_depth,
                 max_len, plots=None, existing=(), spacing_m=0.0):
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
        if 1.0 < d_mp <= max_len and (z[s] - zf) >= min_grad * d_mp:
            cand.append(("LINK-MP", LineString([p, foot]), d_mp))
        if 1.0 < d_stp <= max_len and (z[s] - zstp) >= min_grad * d_stp:
            cand.append(("LINK-STP", LineString([p, Point(stp_xy)]), d_stp))
        for typ, line, d in sorted(cand, key=lambda c: c[2]):
            crossed = plots.crossed(line) if plots else (0, 0)
            if crossed[0] == 0:
                out[s] = (typ, crossed[1])
                ex_pts.append(p)               # the next link keeps its distance from this one
                break
    return out


def link_geometries(info, mp_union, stp_xy):
    out = {}
    for cid, i in info.items():
        p = Point(i["outlet"])
        if i["type"] == "LINK-MP":
            out[cid] = LineString([p, mp_union.interpolate(mp_union.project(p))])
        elif i["type"] == "LINK-STP":
            out[cid] = LineString([p, Point(stp_xy)])
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
