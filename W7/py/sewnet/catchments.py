# -*- coding: utf-8 -*-
"""Catchment boundaries — the ground each subnetwork collects from.

A subnetwork is everything that drains into ONE point on the main pipe. This module draws
the piece of ground each one serves, so the map answers "which part of town feeds which
connection into the trunk, and how much does it bring".

Two things matter about the shape (user rule 8: never a ragged multipart dissolve):

  * every plot the subnetwork collects must sit INSIDE its own catchment, never cut in half
    and never claimed by a neighbour;
  * the catchments must tile the area — no gaps between them, no overlaps.

Neither falls out of simply merging the plot outlines, because plots do not touch: there are
roads, yards and open ground between them. So the space is divided by nearest-plot instead.
Each plot gets the ground closer to it than to any other plot (a Voronoi division), the cells
are grouped by subnetwork, and then each catchment takes back any part of its own plots that
fell the wrong side of a line. That gives a clean single boundary per subnetwork.

Chambers on the main pipe itself are not part of any subnetwork, but plots do connect
straight to them. Those plots are counted separately (`TRUNK_PR`) and their ground is given
to the nearest connection point, so the catchments still cover everything.
"""

import collections
import math

from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import unary_union, voronoi_diagram
from shapely.strtree import STRtree

from .criteria import DEFAULT

SLIVER_M2 = 50.0            # scraps smaller than this are not a catchment


def _rep_point(u):
    """A point that is certainly inside the plot (centroids can fall outside an L shape)."""
    g = getattr(u, "geom", None)
    if g is not None and not g.is_empty:
        try:
            return g.representative_point()
        except Exception:
            pass
    return Point(u.x, u.y)


def _clean(geom, boundary, min_area=SLIVER_M2):
    """One solid polygon: valid, clipped, no holes, no scraps."""
    if geom is None or geom.is_empty:
        return None
    if not geom.is_valid:
        geom = geom.buffer(0)
    geom = geom.intersection(boundary)
    if geom.is_empty:
        return None
    parts = list(getattr(geom, "geoms", [geom]))
    parts = [p for p in parts if isinstance(p, Polygon) and p.area >= min_area]
    if not parts:
        return None
    # Fill only the pinholes. Filling every hole swallows a neighbour that happens to sit
    # inside a ring-shaped catchment, which is where 7,283 m2 of overlap came from.
    filled = []
    for p in parts:
        keep_holes = [r for r in p.interiors if Polygon(r).area >= 2000.0]
        filled.append(Polygon(p.exterior, keep_holes))
    parts = filled
    out = unary_union(parts)
    return out if not out.is_empty else None


def _subnetworks(net, trunk_keys):
    """Split the network at the main pipe. Returns one record per subnetwork."""
    down = {r.up: r for r in net.reaches}
    up = collections.defaultdict(list)
    for r in net.reaches:
        up[r.dn].append(r)

    subs = []
    for r in net.reaches:
        if r.dn in trunk_keys and r.up not in trunk_keys:
            # everything upstream of this pipe, stopping if it touches the main pipe again
            seen, stack = set(), [r.up]
            while stack:
                k = stack.pop()
                if k in seen or k in trunk_keys:
                    continue
                seen.add(k)
                stack.extend(x.up for x in up.get(k, []))
            subs.append({"nodes": seen, "join_key": r.dn, "inlet": r})
    subs.sort(key=lambda s: -s["inlet"].n_props)
    return subs, down, up


def _pumped_downstream(net, start, down, trunk_keys):
    """Does anything between here and the outfall have to be lifted?"""
    k, hops = start, 0
    while k in down and hops < 10000:
        if net.chambers[k].is_station:
            return True
        k = down[k].dn
        hops += 1
    return net.chambers[k].is_station if k in net.chambers else False


def build(net, per_chamber, units, trunk_keys, boundary, stubs=None, crit=DEFAULT):
    """Returns a list of catchment records, each with a polygon and its numbers."""
    trunk_keys = set(trunk_keys) & set(net.chambers)
    subs, down, up = _subnetworks(net, trunk_keys)
    if not subs:
        return []

    # which subnetwork each chamber belongs to
    owner = {}
    for i, s in enumerate(subs):
        for k in s["nodes"]:
            owner[k] = i
    # chambers on the main pipe go to the nearest connection point, so nothing is orphaned
    joins = [(i, net.chambers[s["join_key"]]) for i, s in enumerate(subs)]
    for k in trunk_keys:
        c = net.chambers[k]
        owner[k] = min(joins, key=lambda j: (c.x - j[1].x) ** 2 + (c.y - j[1].y) ** 2)[0]

    # Write the subnetwork number onto the design itself, so a map can colour by it.
    # The main pipe is NOT a subnetwork — it is what they all drain into — so it keeps 0
    # and gets its own symbol on the map.
    for k, cid in owner.items():
        net.chambers[k].subnet = 0 if net.chambers[k].on_trunk else cid + 1
    for r in net.reaches:
        if r.on_trunk:
            r.subnet = 0
            continue
        cid = owner.get(r.up)
        if cid is None:
            cid = owner.get(r.dn)
        r.subnet = 0 if cid is None else cid + 1

    # ---- seeds: one point per plot, tagged with the subnetwork that collects it
    seeds, seed_cid, plots_of = [], [], collections.defaultdict(list)
    n_plots = collections.Counter()
    n_props = collections.Counter()
    n_trunk = collections.Counter()
    for k, us in per_chamber.items():
        cid = owner.get(k)
        if cid is None:
            continue
        on_trunk = k in trunk_keys
        for u in us:
            seeds.append(_rep_point(u))
            seed_cid.append(cid)
            n_plots[cid] += 1
            n_props[cid] += getattr(u, "n_props", 1.0)
            if on_trunk:
                n_trunk[cid] += getattr(u, "n_props", 1.0)
            g = getattr(u, "geom", None)
            if g is not None and not g.is_empty:
                plots_of[cid].append(g)

    # empty plots with a capped stub-out are collected too, once they are built
    n_stubs = collections.Counter()
    by_label = {c.label: c.key for c in net.chambers.values()}
    for s in (stubs or []):
        k = by_label.get(s.get("mh"))
        cid = owner.get(k)
        if cid is None:
            continue
        g = s.get("geom")
        if g is None or g.is_empty:
            continue
        seeds.append(Point(g.coords[0]))
        seed_cid.append(cid)
        n_stubs[cid] += 1

    if not seeds:
        return []

    # ---- divide the ground by nearest plot, then group the pieces by subnetwork
    env = boundary.buffer(50.0).envelope
    cells = voronoi_diagram(MultiPoint(seeds), envelope=env)
    tree = STRtree(seeds)
    pieces = collections.defaultdict(list)
    for cell in cells.geoms:
        hit = [j for j in tree.query(cell) if cell.contains(seeds[j])]
        if not hit:
            continue
        pieces[seed_cid[hit[0]]].append(cell)

    raw = {cid: unary_union(v) for cid, v in pieces.items()}

    # ---- give every catchment its own plots back, and take out anyone else's
    all_plot_tree, all_plot_cid, all_plots = None, [], []
    for cid, gs in plots_of.items():
        for g in gs:
            all_plots.append(g)
            all_plot_cid.append(cid)
    if all_plots:
        all_plot_tree = STRtree(all_plots)

    # Claim the ground in a fixed order and never hand the same piece out twice. Taking
    # each catchment's own plots back can otherwise push it into a neighbour's space, which
    # left 7,283 m2 of overlap on 20 Aug.
    order = sorted(raw.keys(), key=lambda c: -n_props[c])
    claimed = None
    for cid in order:
        geom = raw.get(cid)
        if geom is None:
            continue
        if claimed is not None and not claimed.is_empty:
            geom = geom.difference(claimed)
        mine = plots_of.get(cid) or []
        if mine:
            geom = unary_union([geom] + mine)
        if all_plots:
            theirs = [all_plots[j] for j in STRtree(all_plots).query(geom)
                      if all_plot_cid[j] != cid and all_plots[j].intersects(geom)]
            if theirs:
                geom = geom.difference(unary_union(theirs))
        raw[cid] = geom
        claimed = geom if claimed is None else unary_union([claimed, geom])

    out = []
    for cid, s in enumerate(subs):
        geom = _clean(raw.get(cid), boundary)
        if geom is None:
            continue

        r = s["inlet"]
        join = net.chambers[s["join_key"]]
        pipe_m = sum(x.length for x in net.reaches if x.up in s["nodes"])
        stations = [net.chambers[k].label for k in s["nodes"] if net.chambers[k].is_station]
        deepest = max((net.chambers[k].depth or 0) for k in s["nodes"])
        out.append({
            "cid": cid + 1,
            "geom": geom,
            "join_mh": join.label,
            "join_x": round(join.x, 2), "join_y": round(join.y, 2),
            "inlet_pipe": r.label,
            "inlet_dn": r.dn_mm,
            "n_chambers": len(s["nodes"]),
            "pipe_m": round(pipe_m, 1),
            "n_plots": int(n_plots[cid]),
            "n_props": round(n_props[cid], 1),
            "trunk_props": round(n_trunk[cid], 1),
            "n_stubs": int(n_stubs[cid]),
            "qadf_m3d": round(n_props[cid] * crit.PLOT_QADF_M3D, 2),
            "qpeak_ls": round(r.qpeak_ls, 2),
            "deepest_m": round(deepest, 2),
            "stations": ";".join(stations),
            "pumped": int(bool(stations) or _pumped_downstream(
                net, s["join_key"], down, trunk_keys)),
            "area_ha": round(geom.area / 10000.0, 2),
        })
    return out


def check(cats, units_total=None):
    """Cheap self-check so a bad tiling cannot pass unnoticed."""
    geoms = [c["geom"] for c in cats]
    overlap = 0.0
    tree = STRtree(geoms)
    for i, g in enumerate(geoms):
        for j in tree.query(g):
            if j <= i:
                continue
            inter = g.intersection(geoms[j])
            if not inter.is_empty:
                overlap += inter.area
    total = sum(g.area for g in geoms)
    rep = {"catchments": len(cats),
           "area_ha": round(total / 1e4, 1),
           "overlap_m2": round(overlap, 1),
           "properties": round(sum(c["n_props"] for c in cats), 1),
           "plots": sum(c["n_plots"] for c in cats)}
    if units_total is not None:
        rep["plots_expected"] = units_total
        rep["plots_missing"] = units_total - rep["plots"]
    return rep
