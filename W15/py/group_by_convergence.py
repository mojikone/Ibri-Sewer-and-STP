"""group_by_convergence — read a stage A run and group its subnetworks by where they converge
(engineer, 2026-09-12: the towns are administrative, networks follow gravity and roads; the
QGIS groups follow how the subnetworks converge and connect to the main pipe).

The main pipe is read as a tree rooted at the works: every join's subnetwork belongs to the
main pipe branch its join sits on, named by the first branch below the trunk; a subnetwork
that goes to the works directly, or by a designed link, is its own group; the pockets go with
the branch nearest to them. Writes run/groups.json and shp/W15_A_groups.shp (the catchment
polygons with a GROUP field) and prints the table.

    python group_by_convergence.py            on this folder's run
"""
import collections
import json
import math
import os
import sys

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_built as cfg   # noqa: E402

LEGS = {}
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)   # another run folder to read


def main_pipe_tree(mp, stp):
    """The main pipe features as a graph; the root is the feature end nearest the works.
    Returns node -> parent node (toward the works), feature -> (from, to) and the branch of
    every feature: the first node below the trunk on its way to the root."""
    key = lambda c: (round(c[0], 1), round(c[1], 1))
    adj = collections.defaultdict(list)
    feats = {}
    for i, g in enumerate(mp.geometry):
        if g is None or g.is_empty:
            continue
        lines = [g] if g.geom_type == "LineString" else list(g.geoms)
        for j, l in enumerate(lines):
            a, b = key(l.coords[0]), key(l.coords[-1])
            adj[a].append((b, l.length, (i, j))); adj[b].append((a, l.length, (i, j)))
            feats[(i, j)] = (a, b, l)
    nodes = list(adj)
    root = min(nodes, key=lambda n: math.dist(n, stp))
    parent, depth = {root: None}, {root: 0}
    frontier = [root]
    while frontier:
        n = frontier.pop()
        for m, L, f in adj[n]:
            if m not in parent:
                parent[m] = n; depth[m] = depth[n] + 1; frontier.append(m)
    # a piece of main pipe not connected to the works is its own tree, rooted at its lowest end
    # (the engineer: the west legs end at a low point); it is named as such
    global LEGS
    LEGS = {}
    left = [n for n in nodes if n not in parent]
    while left:
        seed = left[0]
        comp, stack = {seed}, [seed]
        while stack:
            n = stack.pop()
            for m, L, f in adj[n]:
                if m not in comp:
                    comp.add(m); stack.append(m)
        km = sum(l.length for (a, b, l) in feats.values() if a in comp) / 1000.0
        cx, cy = np.mean([n[0] for n in comp]), np.mean([n[1] for n in comp])
        dx, dy = cx - stp[0], cy - stp[1]
        ang = math.degrees(math.atan2(dy, dx))
        comp_dir = ("E" if -22.5 <= ang < 22.5 else "NE" if ang < 67.5 else "N" if ang < 112.5 else "NW" if ang < 157.5 else
                    "W" if ang >= 157.5 or ang < -157.5 else "SW" if ang < -112.5 else "S" if ang < -67.5 else "SE")
        name = f"main pipe {comp_dir} legs, not yet connected to the works ({km:.1f} km)"
        for n in comp:
            LEGS[n] = name
        left = [n for n in left if n not in comp]
    # the branch name of a node: the first node below the point where the pipe first forks
    def path(n):
        out = [n]
        while parent.get(out[-1]) is not None:
            out.append(parent[out[-1]])
        return out[::-1]                       # root first
    children = collections.defaultdict(list)
    for n, p in parent.items():
        if p is not None:
            children[p].append(n)
    # walk from the root until the first fork: the trunk
    trunk = [root]
    while len(children.get(trunk[-1], [])) == 1:
        trunk.append(children[trunk[-1]][0])
    fork = trunk[-1]
    branch_of = {}
    for n in parent:
        pth = path(n)
        if fork in pth:
            k = pth.index(fork)
            branch_of[n] = pth[k + 1] if k + 1 < len(pth) else fork
        else:
            branch_of[n] = pth[1] if len(pth) > 1 else root
    return parent, feats, branch_of, root, fork, trunk


def main():
    rep = json.load(open(os.path.join(OUT, "run", "stage_a.json")))
    table = rep["catchment_table"]
    mp = gpd.read_file(cfg.MAIN_PIPE)
    parent, feats, branch_of, root, fork, trunk = main_pipe_tree(mp, cfg.STP)
    mp_union = unary_union([l for _, _, l in feats.values()])
    node_pts = list(branch_of) + list(LEGS)
    # name the branches by compass direction from the fork and their length
    branch_len = collections.Counter()
    for (a, b, l) in feats.values():
        branch_len[branch_of.get(b, branch_of.get(a))] += l.length
    def bname(bn):
        dx, dy = bn[0] - fork[0], bn[1] - fork[1]
        ang = math.degrees(math.atan2(dy, dx))
        comp = ("E" if -22.5 <= ang < 22.5 else "NE" if ang < 67.5 else "N" if ang < 112.5 else "NW" if ang < 157.5 else
                "W" if ang >= 157.5 or ang < -157.5 else "SW" if ang < -112.5 else "S" if ang < -67.5 else "SE")
        return f"main pipe {comp} branch ({branch_len[bn] / 1000:.1f} km)"
    groups = {}
    polys = gpd.read_file(os.path.join(OUT, "shp", "W13_A_tree_catchments.shp")) if os.path.exists(os.path.join(OUT, "shp", "W13_A_tree_catchments.shp")) else None
    for c in table:
        o = Point(c["outlet_xy"])
        t = c["type"]
        if t in ("STP", "LINK-STP"):
            grp = "to the works"
        elif t in ("JOIN", "LINK-MP"):
            # the main pipe node nearest the join
            n = min(node_pts, key=lambda p: o.distance(Point(p)))
            if n in LEGS:
                grp = LEGS[n]
            else:
                b = branch_of[n]
                grp = "main pipe trunk to the works" if b == fork or n in trunk else bname(b)
        else:
            grp = "pocket"
        groups[c["id"]] = grp
    # a pocket goes with the nearest non-pocket subnetwork's group, by outlet distance
    named = {c["id"]: Point(c["outlet_xy"]) for c in table if groups[c["id"]] != "pocket"}
    for c in table:
        if groups[c["id"]] == "pocket":
            o = Point(c["outlet_xy"])
            near = min(named, key=lambda k: o.distance(named[k]), default=None)
            groups[c["id"]] = (groups[near] if near else "pockets") + " (pocket)"
    summary = collections.defaultdict(lambda: {"subnetworks": 0, "km": 0.0, "ids": [], "types": collections.Counter()})
    for c in table:
        g = groups[c["id"]].replace(" (pocket)", "")
        s = summary[g]; s["subnetworks"] += 1; s["km"] += c["km"]; s["ids"].append(c["id"]); s["types"][c["type"]] += 1
    out = {"fork": list(fork), "trunk_nodes": len(trunk), "root": list(root),
           "groups": {g: {"subnetworks": s["subnetworks"], "km": round(s["km"], 1), "types": dict(s["types"]),
                          "ids": s["ids"]} for g, s in sorted(summary.items(), key=lambda kv: -kv[1]["km"])},
           "by_subnetwork": groups}
    with open(os.path.join(OUT, "run", "groups.json"), "w") as f:
        json.dump(out, f, indent=2)
    if polys is not None:
        polys["GROUP"] = polys["CATCH"].map(groups).fillna("")
        polys.to_file(os.path.join(OUT, "shp", "W15_A_groups.shp"))
    print(f"main pipe: root at {tuple(round(v) for v in root)}, trunk of {len(trunk)} nodes to the fork at {tuple(round(v) for v in fork)}")
    print(f"{'group':44s}{'subnets':>8s}{'km':>8s}  types")
    for g, s in out["groups"].items():
        print(f"{g:44s}{s['subnetworks']:8d}{s['km']:8.1f}  {s['types']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
