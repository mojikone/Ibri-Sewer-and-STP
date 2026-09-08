"""sewnet.quicklay — rule 9 applied early: size every pipe on the plots it serves and lay the
tree from the heads down at each pipe's own minimum gradient, so every Stage A run reports
its depth and where the 12 m limit is threatened.

This is not the Stage C design: no drops, no chamber spacing, no rounded gradients, cover
taken as a flat allowance to invert, Manning capacity at the Table 11 gradient with the
proportional-depth limit. It is honest enough to say which streets dig too deep.
"""
import collections
import math

import numpy as np
from shapely.strtree import STRtree

# G203-p29 Table 11, minimum gradient (m/m) by nominal diameter
T11 = {200: 0.005, 250: 0.00375, 315: 0.0027, 400: 0.00205, 500: 0.00155, 600: 0.00125,
       700: 0.001, 800: 0.00085, 900: 0.00075}
MANNING_N = 0.013


def bore(dn):
    return dn / 1000.0 * (1.0 - 2.0 / 34.0) if dn <= 315 else dn / 1000.0


def capacity_ls(dn):
    """Design capacity at the Table 11 gradient with d/D 0.65 (<= 350) or 0.50 (> 350)."""
    D = bore(dn)
    A = math.pi * D * D / 4.0
    q_full = (1.0 / MANNING_N) * A * (D / 4.0) ** (2.0 / 3.0) * T11[dn] ** 0.5
    return q_full * (0.735 if dn <= 350 else 0.5) * 1000.0


def size_for(q_ls):
    for dn in T11:
        if capacity_ls(dn) >= q_ls:
            return dn
    return 900


def peak_ls(n_prop, km, per_prop_m3d, pf_hold=100.0, infil_l_d_km=720.0):
    """Merrimack peak on the saturation flow, held at the 100-property factor below 100
    properties; infiltration unpeaked."""
    n = max(n_prop, pf_hold)
    qadf = n * per_prop_m3d / 1000.0                      # ML/d
    qp = 2.65 * qadf ** 0.879 * (n_prop / n if n_prop < pf_hold else 1.0)
    return qp * 1e6 / 86400.0 + infil_l_d_km * km / 86400.0


def properties_per_pipe(pipes, plots, acc_points, reach_m=60.0):
    """Every built or planned plot loads its nearest pipe within reach_m with the accounts
    counted on it, or one property at saturation where it has none."""
    geoms = [q["geom"] for q in pipes]
    tree = STRtree(geoms)
    atree = STRtree(acc_points) if acc_points else None
    props = np.zeros(len(pipes))
    n_plots = 0
    for g in plots:
        c = g.centroid
        k = tree.nearest(c)
        if k is None or geoms[k].distance(c) > reach_m:
            continue
        n_acc = 0
        if atree is not None:
            n_acc = sum(1 for j in atree.query(g) if g.contains(acc_points[j]))
        props[k] += max(n_acc, 1)
        n_plots += 1
    return props, n_plots


def lay(pipes, props, z, per_prop_m3d, cover_to_invert=1.55):
    """Accumulate properties down the tree, size, lay at each pipe's own Table 11 gradient.
    Writes dn, q_peak_ls, depth_up, depth_dn onto each pipe; returns node depths and the
    governing upstream pipe of every node."""
    n_in = collections.Counter(q["dn"] for q in pipes)
    out_of = collections.defaultdict(list)
    for i, q in enumerate(pipes):
        out_of[q["up"]].append(i)
    up_props = np.zeros(len(pipes))
    up_km = np.zeros(len(pipes))
    node_props, node_km, arrived = collections.Counter(), collections.Counter(), collections.Counter()
    order = []
    queue = [i for i, q in enumerate(pipes) if n_in[q["up"]] == 0]
    while queue:
        i = queue.pop()
        q = pipes[i]
        order.append(i)
        up_props[i] = node_props[q["up"]] + props[i]
        up_km[i] = node_km[q["up"]] + q["len"] / 1000.0
        node_props[q["dn"]] += up_props[i]
        node_km[q["dn"]] += up_km[i]
        arrived[q["dn"]] += 1
        if arrived[q["dn"]] == n_in[q["dn"]]:
            queue.extend(out_of[q["dn"]])
    invert = {n: z[n] - cover_to_invert for n in z}
    governs = {}
    for i in order:
        q = pipes[i]
        q["q_peak_ls"] = peak_ls(up_props[i], up_km[i], per_prop_m3d)
        q["dn_mm"] = size_for(q["q_peak_ls"])
        q["props_up"] = float(up_props[i])
        s = T11[q["dn_mm"]]
        idn = min(invert[q["up"]] - s * q["len"], z[q["dn"]] - cover_to_invert)
        if idn < invert[q["dn"]]:
            invert[q["dn"]] = idn
            governs[q["dn"]] = i
    depth = {n: z[n] - invert[n] for n in z}
    for q in pipes:
        q["depth_up"] = depth[q["up"]]
        q["depth_dn"] = depth[q["dn"]]
    return depth, governs, len(order)


def report(pipes, depth, limit_m=12.0):
    d = np.array(list(depth.values()))
    by = collections.defaultdict(float)
    for q in pipes:
        by[q["catch"]] = max(by[q["catch"]], q["depth_dn"])
    over = {c: v for c, v in by.items() if v > limit_m}
    return {"chambers": int(len(d)), "depth_median_m": round(float(np.median(d)), 2),
            "depth_90pct_m": round(float(np.percentile(d, 90)), 2),
            "depth_max_m": round(float(d.max()), 2),
            "over_limit": int((d > limit_m).sum()), "over_8m": int((d > 8).sum()),
            "catchments_over_limit": {c: round(v, 1) for c, v in sorted(over.items(), key=lambda kv: -kv[1])},
            "dn_km": {str(dn): round(sum(q["len"] for q in pipes if q["dn_mm"] == dn) / 1000, 1)
                      for dn in T11 if any(q["dn_mm"] == dn for q in pipes)}}
