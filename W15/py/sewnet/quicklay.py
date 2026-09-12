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
    """Design capacity at the Table 11 gradient with d/D 0.65 (<= 350) or 0.50 (> 350),
    Colebrook-White with ks 1.5 mm (engineer 2026-09-12; was Manning 0.013)."""
    from . import hydraulics as H
    return H.capacity(dn, T11[dn]) * 1000.0


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


def peak_flow_ls(qadf_m3d, props, km=0.0, infil_l_d_km=720.0):
    """The peak of an average dry-weather flow (temp 3, 2026-09-11, handoff 3): Merrimack
    for more than 100 properties, Qpdf = 2.65 Qadf^0.879 in Ml/d (G1-p71); Peltier for 100
    or fewer, PF = 1.5 + 1/sqrt(Qm), Qm in l/s (G1-p72), not capped; infiltration by the
    pipe length upstream, unpeaked (G1-p72). Returns (peak l/s, peak factor)."""
    if qadf_m3d <= 0.0:
        base, pf = 0.0, 0.0
    elif props > 100.0:
        base = 2.65 * (qadf_m3d / 1000.0) ** 0.879 * 1e6 / 86400.0
        pf = base / (qadf_m3d / 86.4)
    else:
        qm = qadf_m3d / 86.4
        pf = 1.5 + 1.0 / math.sqrt(qm)
        base = qm * pf
    return base + infil_l_d_km * km / 86400.0, pf


def loads_per_pipe(pipes, plots, loads, reach_m=45.0):
    """Every plot that carries flow loads its nearest pipe within reach_m with its own flows:
    Q_ULT and Q_2030 (m3/d) and its properties at saturation and in 2030. Returns the four
    per-pipe arrays and the plots loaded."""
    geoms = [q["geom"] for q in pipes]
    tree = STRtree(geoms)
    out = np.zeros((4, len(pipes)))
    n_plots = 0
    for g, ld in zip(plots, loads):
        c = g.centroid
        k = tree.nearest(c)
        if k is None or geoms[k].distance(c) > reach_m:
            continue
        out[:, k] += ld
        n_plots += 1
    return out, n_plots


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


def laid_gradient(g_needed, dn, grid=None):
    """temp 3 (2026-09-11, engineer): the Table 11 minimum is laid as it is; a gradient
    steeper than the minimum, where the ground forces it, is rounded UP to the grid, so no
    random value is laid: 0.05 % steps for secondary pipes, 0.025 % for DN500 and up. Up,
    never down, because down would lose the cover."""
    s = T11[dn]
    g = max(s, g_needed)
    if grid and g > s + 1e-7:
        step = grid[1] if dn >= grid[2] else grid[0]
        g = max(s, math.ceil(g / step - 1e-9) * step)
    return g


def lay(pipes, props, z, per_prop_m3d, cover_to_invert=1.55, floors=None, loads=None,
        infil_l_d_km=720.0, grid=None):
    """Accumulate properties down the tree, size, lay at each pipe's own Table 11 gradient.
    Writes dn, q_peak_ls, depth_up, depth_dn onto each pipe; returns node depths and the
    governing upstream pipe of every node. floors: node -> the invert the pipe must arrive
    above (the works inlet, a main pipe's invert); a pipe arriving under it is recorded in
    lay.under, which report() carries as a failure (2026-09-08)."""
    n_in = collections.Counter(q["dn"] for q in pipes)
    out_of = collections.defaultdict(list)
    for i, q in enumerate(pipes):
        out_of[q["up"]].append(i)
    up_props = np.zeros(len(pipes))
    up_km = np.zeros(len(pipes))
    node_props, node_km, arrived = collections.Counter(), collections.Counter(), collections.Counter()
    # temp 3: the plots' own flows, accumulated the same way (q_ult, q_2030, p_ult, p_2030)
    up_ld = np.zeros((4, len(pipes)))
    node_ld = collections.defaultdict(lambda: np.zeros(4))
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
        if loads is not None:
            up_ld[:, i] = node_ld[q["up"]] + loads[:, i]
            node_ld[q["dn"]] = node_ld[q["dn"]] + up_ld[:, i]
        arrived[q["dn"]] += 1
        if arrived[q["dn"]] == n_in[q["dn"]]:
            queue.extend(out_of[q["dn"]])
    invert = {n: z[n] - cover_to_invert for n in z}
    governs = {}
    for i in order:
        q = pipes[i]
        if loads is None:
            q["q_peak_ls"] = peak_ls(up_props[i], up_km[i], per_prop_m3d)
            q["props_up"] = float(up_props[i])
        else:
            q["q_ult_up"], q["q_2030_up"] = float(up_ld[0, i]), float(up_ld[1, i])
            q["props_up"], q["props_2030_up"] = float(up_ld[2, i]), float(up_ld[3, i])
            q["q_peak_ls"], q["pf"] = peak_flow_ls(q["q_ult_up"], q["props_up"], up_km[i],
                                                   infil_l_d_km)
        q["dn_mm"] = size_for(q["q_peak_ls"])
        L = max(q["len"], 1e-6)
        g = laid_gradient((invert[q["up"]] - (z[q["dn"]] - cover_to_invert)) / L, q["dn_mm"], grid)
        q["grad_laid"] = g
        idn = invert[q["up"]] - g * L
        if idn < invert[q["dn"]]:
            invert[q["dn"]] = idn
            governs[q["dn"]] = i
    depth = {n: z[n] - invert[n] for n in z}
    for q in pipes:
        q["depth_up"] = depth[q["up"]]
        q["depth_dn"] = depth[q["dn"]]
    lay.under = {}
    for n, fl in (floors or {}).items():
        if n in invert and invert[n] < fl - 1e-6:
            lay.under[n] = fl - invert[n]
    return depth, governs, len(order)


def report(pipes, depth, limit_m=12.0):
    d = np.array(list(depth.values()))
    by = collections.defaultdict(float)
    for q in pipes:
        by[q["catch"]] = max(by[q["catch"]], q["depth_dn"])
    over = {c: v for c, v in by.items() if v > limit_m}
    under = getattr(lay, "under", {}) or {}
    catch_of = {q["dn"]: q["catch"] for q in pipes}
    under_by = {}
    for n, v in under.items():
        c = catch_of.get(n)
        under_by[c] = max(under_by.get(c, 0.0), v)
    return {"chambers": int(len(d)), "depth_median_m": round(float(np.median(d)), 2),
            "depth_90pct_m": round(float(np.percentile(d, 90)), 2),
            "depth_max_m": round(float(d.max()), 2),
            "over_limit": int((d > limit_m).sum()), "over_8m": int((d > 8).sum()),
            "catchments_over_limit": {c: round(v, 1) for c, v in sorted(over.items(), key=lambda kv: -kv[1])},
            "arrives_under_level": {str(c): round(v, 2) for c, v in under_by.items()},
            "dn_km": {str(dn): round(sum(q["len"] for q in pipes if q["dn_mm"] == dn) / 1000, 1)
                      for dn in T11 if any(q["dn_mm"] == dn for q in pipes)}}
