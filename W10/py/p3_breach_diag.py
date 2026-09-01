"""Phase 3 diagnosis - WHY each of the 220 depth breaches happens, one by one.

The sized run (p2_sizing) puts 220 points on the network where cover would pass 12.00 m.
Consolidated at 1.5 km they are 33 stations and 11 of those carry 50+ properties. Before
anything is optimised away we need to know what each one IS, because the levers are
different: a long flat run can be laid flatter by upsizing, a route that climbs cannot be
laid flatter at all, and a corridor that should never have been drawn should be deleted
rather than pumped.

THE PHYSICS, which the whole file rests on. In the lay-shallow construction the invert at
a node is the LOWER of (upstream invert - gradient x length) and (ground - cover - OD). So
a run starts at minimum cover and thereafter the depth is bookkeeping:

    depth at node k  =  cover + OD  +  (pipe fall from the head to k)  -  (ground fall)

Nothing else enters it. A breach is therefore always the same statement - the pipe fell
further than the ground did - and the only question is which term did it. That gives the
classes:

    A LONG FLAT RUN   ground falls, but slower than the pipe must, for kilometres
    B ADVERSE GROUND  the route climbs; ground fall is negative
    C LOCAL RIDGE     the ground spikes near the breach and falls again after it
    D INHERITED       the run head is itself a breach: this is a cascade, not a new cause
    E ARTEFACT        the corridor should not be there - an auto_link across open ground,
                      a skeleton fragment, or a route down a wadi

THE RELIEF CALCULATION. Rearranging the same identity, the run does not breach if at EVERY
node k on it

    s  <=  (allowance + ground fall to k) / (length to k),    allowance = 12.00 - cover - OD

so the relieving gradient is the minimum of that over the run, and Table 11 says which
diameter would deliver it (DN200 0.500 % ... DN900 0.075 %). Every breach is tested against
the gradient it could ACTUALLY be laid at,

    s_floor(reach) = max(0.075 %, tractive minimum at that reach's peak flow)

because the tractive-force minimum (G203-p27 4.2.2.1) depends on FLOW and not on size: at
the 1.5 L/s design floor it is 0.467 %, so a branch carrying nothing cannot be laid flat
however big the pipe.

*** THIS IS A MEASUREMENT, NOT A RECOMMENDATION. ***

Upsizing a sewer in order to lay it flatter is PROHIBITED - G203-p29 4.3.1, one unqualified
sentence with no exception in 201 pages: "Sewers shall not be oversized to facilitate flatter
slopes. Uniform slopes must be maintained between successive manholes." p167 lists oversized
mains as a cause of hydrogen sulphide and p185 says the lowest-gradient gravity sewers carry
the greatest H2S risk. TUTORIALS/T02 6.3 already carries the clause.

RED_SEQ therefore reads "would have cleared had it been allowed" and sizes what the
prohibition costs. Under the guideline as written every breach stands. See
docs/BREACH_DIAGNOSIS.md and docs/OPTIMISATION.md.

Nothing is designed here and no output of p2_sizing is modified. This reads the network,
re-solves it exactly as p2_sizing does (recording which upstream node governed each invert,
which p2_sizing does not keep), and writes the diagnosis.

Run:  python p3_breach_diag.py
"""
import os
import sys
import time
import warnings
from collections import defaultdict

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import rasterio
from scipy.spatial import cKDTree
from shapely.geometry import Point

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "W8", "py"))

import config as C
import netlib as N
from p1_subnetworks import flow_tree, trace_joins
from p2_depths import MIN_COVER_CROWN, MAX_DEPTH, OD_DEFAULT
from p2_sizing import accumulate, size_all, ASSIGN_M
from sewnet import hydra
from sewnet.criteria import DEFAULT as CRIT

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------- classification thresholds
# Method choices, not guideline values. Every underlying number is also written to the CSV
# so a reader can re-cut the classes without re-running the solve.
RIDGE_RISE_M = 1.0       # a rise this far above the run's low point counts as a ridge
RIDGE_GIVEBACK = 0.5     # ...and it is LOCAL only if the ground gives back this share of
DS_LOOK_M = 1500.0       #    the rise within this distance downstream of the breach
ARTEFACT_LINK_PCT = 40.0 # a run this much on auto_link is a stitched route, not a street
ARTEFACT_WADI_PCT = 40.0 # a run this much inside flood class 4-6 is down a wadi
LOW_FLOW_LS = 5.0        # "empty branch" threshold, peak L/s
MID_STEP_M = 20.0        # terrain sampled this often along each reach of a breach run
ALT_SEARCH_DZ = 1.0      # an untaken edge falling this much is a candidate alternative

# The 50-year hazard grid is CONTINUOUS float, not integer classes - 1.00, 1.01, 1.02 ...
# with -9999 outside the modelled basin. p4_stp_siting reads it as floor(value) >= 4 and so
# does this; testing membership of {4, 5, 6} matches almost nothing and silently reports no
# wadi anywhere.
WADI_MIN = float(min(CRIT.HAZARD_WADI_CLASSES))     # 4 -> classes 4, 5, 6 (G203, user rule)
HAZ_NODATA = -1000.0
T11 = dict(CRIT.TABLE11)
DN_ORDER = sorted(T11)                       # 200 ... 900, gradient falling


def dn_for_slope(s):
    """Smallest DN whose Table 11 minimum is no steeper than s. None if even DN900 is."""
    for dn in DN_ORDER:
        if T11[dn] <= s + 1e-12:
            return dn
    return None


def s_floor_for(qpk_m3s):
    """The flattest gradient a reach carrying qpk can actually be laid at.

    Diameter can buy Table 11 down to 0.075 %; nothing buys the tractive-force minimum
    down, because it is a function of flow (G203-p27 4.2.2.1). The larger governs.
    """
    return max(CRIT.TABLE11_FLOOR, hydra.smin_tractive(qpk_m3s, CRIT))


# ---------------------------------------------------------------- rebuild the sized run
def solve_with_gov(G, z, order, ups, slope_of):
    """p2_sizing's depth solve, keeping the upstream node that GOVERNED each invert.

    Identical arithmetic to p2_sizing (same candidate set, same tie handling: `min` keeps
    the shallow candidate on a tie and so does `<`), plus the one thing it discards - which
    upstream branch produced the lowest invert. That is what makes a run traceable.
    """
    invert, lifts, gov = {}, {}, {}
    for n in order:
        zn = z.get(n, np.nan)
        if not np.isfinite(zn):
            continue
        shallow = zn - MIN_COVER_CROWN - OD_DEFAULT
        best, g = shallow, None
        for u in ups.get(n, ()):
            if u not in invert or not G.has_edge(u, n):
                continue
            s = slope_of.get((u, n), 0.003)
            cand = invert[u] - s * G[u][n]["len"]
            if cand < best:
                best, g = cand, u
        iv = best
        if zn - iv > MAX_DEPTH:
            lifts[n] = (zn - iv) - (zn - shallow)
            iv = shallow
        invert[n] = iv
        gov[n] = g
    depth = {n: z[n] - invert[n] for n in invert if np.isfinite(z.get(n, np.nan))}
    return invert, depth, lifts, gov


def trace_run(b, gov, lifts):
    """Head-to-breach chain of nodes whose inverts set this breach.

    Stops at the first node whose stored invert is minimum cover - either because the
    shallow candidate governed there, or because a lifting station reset it.
    """
    run = [b]
    n = b
    while True:
        u = gov.get(n)
        if u is None:
            break
        run.append(u)
        if u in lifts:
            break
        n = u
    run.reverse()
    return run


def trace_full(b, gov):
    """The whole path back to the true network head, ignoring every lifting-station reset.

    A cascade of breaches is ONE hydraulic problem: relieving the top one removes its reset,
    so the pipe arrives at the next one deeper than the reset left it. Asking whether a
    chained breach can be upsized away therefore has to be asked of the entire path, not of
    the stretch between two stations.
    """
    path, n, seen = [b], b, {b}
    while True:
        u = gov.get(n)
        if u is None or u in seen:
            break
        path.append(u)
        seen.add(u)
        n = u
    path.reverse()
    return path


def downstream(b, nxt, G, limit=DS_LOOK_M):
    """Nodes below the breach, out to `limit` metres - does the ground fall again?"""
    path, n, L = [b], b, 0.0
    while L < limit:
        m = nxt.get(n)
        if m is None or not G.has_edge(n, m):
            break
        L += G[n][m]["len"]
        path.append(m)
        n = m
    return path


# ---------------------------------------------------------------- per-run geometry
def run_profile(run, G, xy, z, lines, slope_of, step=MID_STEP_M):
    """Chainage, ground and laid gradient along one run, nodes plus mid-reach samples.

    The sized solve checks depth at nodes only - p2_depths sampled between them, p2_sizing
    dropped that. Corridor nodes sit about 100 m apart, so a ridge halfway along a reach is
    invisible to the run as solved. Both are carried: the node-only numbers reconcile with
    the 220, the sampled ones say whether the relief is real on the ground.
    """
    ch, gr, is_node, pts = [0.0], [z[run[0]]], [True], []
    seg = []                                        # (u, v, length, slope)
    L = 0.0
    for u, v in zip(run[:-1], run[1:]):
        d = G[u][v]
        ln = lines[d["line"]]
        s = slope_of.get((u, v), 0.003)
        seg.append((u, v, d["len"], s))
        # walk the reach in the direction of flow
        fwd = (np.hypot(ln.coords[0][0] - xy[u][0], ln.coords[0][1] - xy[u][1]) <
               np.hypot(ln.coords[-1][0] - xy[u][0], ln.coords[-1][1] - xy[u][1]))
        nmid = max(0, int(ln.length / step) - 1)
        for t in np.linspace(0, 1, nmid + 2)[1:-1]:
            p = ln.interpolate(t if fwd else 1.0 - t, normalized=True)
            pts.append((p.x, p.y))
            ch.append(L + t * d["len"])
            gr.append(np.nan)                       # filled by the caller in one raster pass
            is_node.append(False)
        L += d["len"]
        ch.append(L)
        gr.append(z[v])
        is_node.append(True)
    # chainage is built in increasing order, so the arrays are already in profile order
    return np.array(ch), np.array(gr), np.array(is_node), pts, seg, L


def main():
    t0 = time.time()
    os.makedirs(C.OUT_RUN, exist_ok=True)
    os.makedirs(C.OUT_DOCS, exist_ok=True)

    # ---- the network, exactly as p2_sizing built it -------------------------
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    cost, nxt, D = flow_tree(G, z, sink)

    # ---- loads, with plot COUNTS as well as flow ----------------------------
    gpkg = os.path.join(C.OUT_SHP, "W10_plot_loads.gpkg")
    pl = (gpd.read_file(gpkg, layer="plot_loads") if os.path.exists(gpkg)
          else gpd.read_file(os.path.join(C.OUT_SHP, "W10_plot_loads.shp")))
    qcol = "Q_AVG_M3D" if "Q_AVG_M3D" in pl.columns else "Q_AVG_M3"
    npts = gpd.GeoDataFrame(geometry=[Point(xy[n]) for n in G.nodes],
                            data={"NODE": list(G.nodes)}, crs=C.EPSG)
    j = gpd.sjoin_nearest(pl[[qcol, "geometry"]], npts, how="left",
                          max_distance=ASSIGN_M, distance_col="D")
    j = j[~j.index.duplicated(keep="first")]
    q_node, p_node = defaultdict(float), defaultdict(int)
    for node, v in zip(j["NODE"], j[qcol]):
        if node == node and v == v:
            q_node[int(node)] += float(v)
            p_node[int(node)] += 1
    print(f"loads: {sum(q_node.values()):,.0f} m3/d on {len(q_node):,} nodes, "
          f"{sum(p_node.values()):,} plots placed")

    qacc, lacc, order = accumulate(G, nxt, q_node)
    pacc, _, _ = accumulate(G, nxt, {k: float(v) for k, v in p_node.items()})

    pipes = size_all(G, nxt, qacc, lacc)
    print(f"sized {len(pipes):,} pipes")

    slope_of, qpk_of, dn_of = {}, {}, {}
    for (n, m), p in pipes.items():
        slope_of[(n, m)] = slope_of[(m, n)] = p["SMIN"]
        qpk_of[(n, m)] = qpk_of[(m, n)] = p["QPK_LS"] / 1000.0      # m3/s
        dn_of[(n, m)] = dn_of[(m, n)] = p["DN"]

    ups = defaultdict(list)
    for n, m in nxt.items():
        ups[m].append(n)
    invert, depth, lifts, gov = solve_with_gov(G, z, order, ups, slope_of)
    print(f"breaches reproduced: {len(lifts):,}")

    # ---- prove it is the same run as the one on disk ------------------------
    ref = gpd.read_file(os.path.join(C.OUT_SHP, "W10_lift_sized.shp"))
    here = np.array([xy[n] for n in lifts])
    there = np.array([[g.x, g.y] for g in ref.geometry])
    dd, _ = cKDTree(there).query(here)
    print(f"check against W10_lift_sized.shp: {len(ref)} on disk, {len(lifts)} rebuilt, "
          f"worst position difference {dd.max():.3f} m, "
          f"lift heights differ by at most "
          f"{abs(np.sort([lifts[n] for n in lifts]) - np.sort(ref.LIFT_M.values)).max():.3f} m")

    # ---- subnetwork per node, matched to the published join ids -------------
    trunk_nodes = {n for u, v, d in G.edges(data=True) if d["trunk"] for n in (u, v)}
    join = trace_joins(cost, nxt, trunk_nodes)
    jn = gpd.read_file(os.path.join(C.OUT_SHP, "W10_joins.shp"))
    jtree = cKDTree(np.c_[jn.JOIN_X.values, jn.JOIN_Y.values])

    # ---- corridor provenance on every graph edge ----------------------------
    cor = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors.shp"))
    mids = gpd.GeoDataFrame(
        geometry=[lines[d["line"]].interpolate(0.5, normalized=True)
                  for *_, d in G.edges(data=True)], crs=C.EPSG)
    mids["KEY"] = [(u, v) for u, v, _ in G.edges(data=True)]
    sj = gpd.sjoin_nearest(mids, cor[["SRC", "geometry"]], how="left",
                           max_distance=25.0, distance_col="DD")
    sj = sj[~sj.index.duplicated(keep="first")]
    src_of = {}
    for k, s in zip(sj["KEY"], sj["SRC"]):
        src_of[k] = src_of[(k[1], k[0])] = (s if isinstance(s, str) else "trunk")
    print(f"corridor source tagged on {len(sj):,} edges")

    # ---- edges the flow tree did NOT use ------------------------------------
    used = set()
    for (n, m) in pipes:
        used.add((n, m))
        used.add((m, n))

    # ---- trace and diagnose every breach ------------------------------------
    runs = {b: trace_run(b, gov, lifts) for b in lifts}
    fulls = {b: trace_full(b, gov) for b in lifts}
    dss = {b: downstream(b, nxt, G) for b in lifts}
    print(f"runs traced: median {np.median([len(r) for r in runs.values()]):.0f} nodes, "
          f"longest {max(len(r) for r in runs.values())} nodes; "
          f"full paths to the network head median "
          f"{np.median([len(r) for r in fulls.values()]):.0f} nodes")

    # one raster pass for every mid-reach sample on every run and its downstream look
    prof, dprof, allpts = {}, {}, []
    for b in runs:
        ch, gr, isn, pts, seg, L = run_profile(runs[b], G, xy, z, lines, slope_of)
        prof[b] = [ch, gr, isn, seg, L, len(allpts)]
        allpts.extend(pts)
        if len(dss[b]) > 1:
            ch2, gr2, isn2, pts2, seg2, L2 = run_profile(dss[b], G, xy, z, lines, slope_of)
            dprof[b] = [ch2, gr2, isn2, L2, len(allpts)]
            allpts.extend(pts2)
        else:
            dprof[b] = None
    print(f"mid-reach terrain: {len(allpts):,} samples at {MID_STEP_M:.0f} m")
    with rasterio.open(C.TERRAIN) as src:
        mz = np.array([v[0] for v in src.sample(allpts)], dtype=float) if allpts else np.array([])
    mz[~np.isfinite(mz)] = np.nan
    mz[mz <= 0] = np.nan
    with rasterio.open(os.path.join(C.HAZARD)) as src:
        hz = np.array([v[0] for v in src.sample(allpts)], dtype=float) if allpts else np.array([])

    rows, resid = [], []
    for b, run in runs.items():
        ch, gr, isn, seg, L, off = prof[b]
        fill = np.full(len(ch), np.nan)
        haz = np.full(len(ch), np.nan)
        k = 0
        for i, flag in enumerate(isn):
            if not flag:
                fill[i] = mz[off + k]
                haz[i] = hz[off + k]
                k += 1
        gr = np.where(isn, gr, fill)
        zh = gr[0]
        gf = zh - gr                                  # ground fall from the head, per point
        node_gf = gf[isn]
        node_ch = ch[isn]

        # laid gradient, cumulative, at every point
        dn_now = [dn_of.get((u, v), 0) for u, v, *_ in seg]
        seg_s = np.array([s for *_, s in seg])
        seg_L = np.array([ln_ for _u, _v, ln_, _s in seg])
        seg_q = np.array([qpk_of.get((u, v), 0.0) for u, v, *_ in seg])
        seg_sf = np.array([s_floor_for(q) for q in seg_q])
        bounds = np.concatenate([[0.0], np.cumsum(seg_L)])

        def cumfall(slopes):
            c = np.concatenate([[0.0], np.cumsum(slopes * seg_L)])
            # linear inside the reach the point falls in
            idx = np.clip(np.searchsorted(bounds, ch, side="right") - 1, 0, len(seg) - 1)
            return c[idx] + slopes[idx] * (ch - bounds[idx])

        fall = cumfall(seg_s)
        fall_f = cumfall(seg_sf)

        od_now = OD_DEFAULT
        allow_now = MAX_DEPTH - MIN_COVER_CROWN - od_now              # 10.40 m

        # ---- what the run IS -----------------------------------------------
        gfall = float(zh - gr[isn][-1])                               # head to breach
        pfall = float((seg_s * seg_L).sum())
        dpt = float(lifts[b]) + MIN_COVER_CROWN + OD_DEFAULT
        margin = dpt - MAX_DEPTH
        # independent check of the whole construction: depth = cover + pipe fall - ground fall
        resid.append(abs((MIN_COVER_CROWN + OD_DEFAULT + pfall - gfall) - dpt))
        gmin = float(np.nanmin(gr))
        imin = int(np.nanargmin(gr))
        ridge = float(gr[isn][-1] - gmin)
        ridge_d = float(L - ch[imin])

        # ---- the relieving gradient ----------------------------------------
        with np.errstate(divide="ignore", invalid="ignore"):
            lim_node = (allow_now + node_gf[1:]) / node_ch[1:]
            lim_all = (allow_now + gf[1:]) / ch[1:]
        s_req = float(np.nanmin(lim_node)) if lim_node.size else np.nan
        s_req_mid = float(np.nanmin(lim_all)) if lim_all.size else np.nan
        dn_req = dn_for_slope(s_req) if s_req > 0 else None
        s_tract = float(seg_sf.max())

        # ---- can upsizing alone remove it? ---------------------------------
        # every reach laid at the flattest gradient its own flow permits, and the head
        # cover corrected for the diameter that gradient implies
        dn_head = dn_for_slope(seg_sf[0]) or DN_ORDER[-1]
        allow_ex = MAX_DEPTH - MIN_COVER_CROWN - dn_head / 1000.0
        worst_node = float(np.nanmax((fall_f - gf)[isn])) if isn.any() else np.nan
        worst_all = float(np.nanmax(fall_f - gf))
        slack = allow_ex - worst_node
        reducible = int(slack >= 0.0)
        slack_mid = allow_ex - worst_all

        # MINIMUM relief, not maximum: lay each reach at the relieving gradient the run
        # needs, or at its own floor if that is steeper - never flatter than it has to be.
        # Upsizing to the floor everywhere would price a DN900 where a DN250 clears 12 m.
        s_tgt = np.maximum(seg_sf, s_req if np.isfinite(s_req) else seg_sf)
        dn_needed = np.array([dn_for_slope(s) or DN_ORDER[-1] for s in s_tgt])
        dn_cur = np.array(dn_now)
        up = dn_needed > dn_cur
        upsize_km = float(seg_L[up].sum() / 1000.0)
        dn_up = int(dn_needed[up].max()) if up.any() else 0

        # ---- the same question asked of the WHOLE cascade -------------------
        # relieving an upstream breach removes its reset, so a chained breach can only be
        # judged on the entire path back to the true network head
        full = fulls[b]
        fseg = [(u, v, G[u][v]["len"]) for u, v in zip(full[:-1], full[1:])]
        fL = np.array([l_ for *_, l_ in fseg]) if fseg else np.array([0.0])
        fsf = np.array([s_floor_for(qpk_of.get((u, v), 0.0)) for u, v, _ in fseg]) \
            if fseg else np.array([CRIT.TABLE11_FLOOR])
        fgf = np.array([z[full[0]] - z[k] for k in full])
        fcum = np.concatenate([[0.0], np.cumsum(fsf * fL)])
        dnf_head = dn_for_slope(fsf[0]) or DN_ORDER[-1]
        allow_full = MAX_DEPTH - MIN_COVER_CROWN - dnf_head / 1000.0
        slack_full = allow_full - float(np.max(fcum - fgf))
        red_full = int(slack_full >= 0.0)

        # the SAME full path laid at 0.075 % throughout - the flattest gradient any diameter
        # permits, with the self-cleansing rule set aside. tau = 1 Pa is an ASSUMPTION
        # (GAP-9: GUD-203 gives no numeric value), so what the GROUND alone forbids has to be
        # countable separately from what the tractive rule forbids. This is the hard floor.
        fcum11 = np.concatenate([[0.0], np.cumsum(
            np.full(len(fL), CRIT.TABLE11_FLOOR) * fL)])
        slack_t11 = (MAX_DEPTH - MIN_COVER_CROWN - DN_ORDER[-1] / 1000.0) - \
            float(np.max(fcum11 - fgf))
        red_t11 = int(slack_t11 >= 0.0)

        # ---- is the run carrying a gradient it should not be? ---------------
        # p2_sizing's size_all iterates diameter and gradient together, and when size_pipe
        # returns None it forces DN to the top of the series and BREAKS - leaving `s` at
        # the value from the previous iteration, which is DN200's 0.500 %. The reach is then
        # written as a large pipe laid at a small pipe's minimum. Detected exactly: the laid
        # gradient is not smin_for(its own DN, its own peak flow).
        seg_true = np.array([hydra.smin_for(int(dn_of.get((u, v), 200)),
                                            qpk_of.get((u, v), 0.0), CRIT)
                             for u, v, *_ in seg])
        art = np.abs(seg_s - seg_true) > 1e-9
        art_fall = float(((seg_s - seg_true) * seg_L)[art].sum())
        empty_km = float(seg_L[seg_q < 0.001].sum() / 1000.0)     # reaches under 1 L/s peak

        # ---- provenance and hazard along the run ---------------------------
        src_l = defaultdict(float)
        for (u, v, ln_, _s) in seg:
            src_l[src_of.get((u, v), "trunk")] += ln_
        link_pct = 100.0 * src_l.get("auto_link", 0.0) / max(L, 1e-9)
        auto_pct = 100.0 * sum(v for k_, v in src_l.items()
                               if k_.startswith("auto")) / max(L, 1e-9)
        hv = haz[np.isfinite(haz) & (haz > HAZ_NODATA)]
        wadi_pct = 100.0 * float((np.floor(hv) >= WADI_MIN).mean()) if hv.size else 0.0
        haz_cov = 100.0 * float(hv.size) / max(int(np.isfinite(haz).sum()), 1)

        # ---- an alternative the router did not take ------------------------
        # a corridor edge touching the run that carries no pipe, and falls. Weak evidence
        # on its own - the router may have skipped it because it is a dead end - but it
        # says whether a re-route is even geometrically possible.
        alt_n, alt_dz = 0, 0.0
        rs = set(run)
        for n in run:
            for m in G[n]:
                if (n, m) in used or m in rs:
                    continue
                dz = float(z.get(n, np.nan) - z.get(m, np.nan))
                if np.isfinite(dz) and dz >= ALT_SEARCH_DZ:
                    alt_n += 1
                    alt_dz = max(alt_dz, dz)

        # ---- does the ground fall again below the breach? -------------------
        if dprof[b] is None:
            dsfall, dsdist = 0.0, np.nan
        else:
            ch2, gr2, isn2, L2, off2 = dprof[b]
            f2 = np.full(len(ch2), np.nan)
            k2 = 0
            for i, flag in enumerate(isn2):
                if not flag:
                    f2[i] = mz[off2 + k2]
                    k2 += 1
            gr2 = np.where(isn2, gr2, f2)
            i2 = int(np.nanargmin(gr2))
            dsfall = float(gr2[0] - gr2[i2])
            dsdist = float(ch2[i2])

        # ---- classes --------------------------------------------------------
        gpipe = pipes.get((gov[b], b), {})
        head = run[0]
        chained = head in lifts
        local = ridge >= RIDGE_RISE_M and dsfall >= RIDGE_GIVEBACK * ridge
        if art_fall >= margin:
            phys, ereason = "E", "SIZING"      # the excess gradient alone explains it
        elif link_pct >= ARTEFACT_LINK_PCT:
            phys, ereason = "E", "LINK"
        elif wadi_pct >= ARTEFACT_WADI_PCT:
            phys, ereason = "E", "WADI"
        elif local:
            phys, ereason = "C", "-"
        elif gfall < 0:
            phys, ereason = "B", "-"
        else:
            phys, ereason = "A", "-"
        cause = "E" if phys == "E" else ("D" if chained else phys)

        # BLOCKER and FIX are NOT decided here. Whether a breach can be upsized away depends
        # on whether the station above it survives, and that is only known once the chains
        # have been walked from the top down - see the sequential pass after this loop.

        jnode = join.get(b)
        if jnode is None:
            subnet, jdist = -1, np.nan
        else:
            jdist, ji = jtree.query(np.array(xy[jnode]))
            subnet = int(jn.SUBNET.iloc[int(ji)]) if jdist <= 5.0 else -1

        rows.append({
            "BID": 0, "NODE": int(b), "CAUSE": cause, "CAUSE_PHY": phys,
            "CHAINED": int(chained),
            "DEPTH_M": round(dpt, 2), "MARGIN_M": round(margin, 2),
            "LIFT_M": round(float(lifts[b]), 2), "GROUND": round(float(z[b]), 2),
            "RUN_M": round(L, 1), "RUN_N": len(run),
            "GFALL_M": round(gfall, 2), "PFALL_M": round(pfall, 2),
            "GGRAD_PCT": round(100.0 * gfall / max(L, 1e-9), 4),
            "PGRAD_PCT": round(100.0 * pfall / max(L, 1e-9), 4),
            "RIDGE_M": round(ridge, 2), "RIDGE_D": round(ridge_d, 1),
            "DSFALL_M": round(dsfall, 2),
            "DSDIST_M": round(dsdist, 1) if np.isfinite(dsdist) else -1.0,
            "MAXREACH": round(float(seg_L.max()), 1),
            "QADF_M3D": round(float(qacc.get(b, 0.0)), 1),
            "QPK_LS": round(float(gpipe.get("QPK_LS", 0.0)), 2),
            "PLOTS_UP": int(round(pacc.get(b, 0.0))),
            "SUBNET": subnet,
            "SREQ_PCT": round(100.0 * s_req, 4) if np.isfinite(s_req) else -1.0,
            "SREQM_PCT": round(100.0 * s_req_mid, 4) if np.isfinite(s_req_mid) else -1.0,
            "DN_REQ": int(dn_req) if dn_req else 0,
            "DN_NOW": int(max(dn_now)) if dn_now else 0,
            "STRACT_PCT": round(100.0 * s_tract, 4),
            "REDUCIBLE": reducible, "SLACK_M": round(float(slack), 2),
            "SLACKMID_M": round(float(slack_mid), 2),
            "RED_FULL": red_full, "SLACKFUL_M": round(float(slack_full), 2),
            "FULL_M": round(float(fL.sum()), 1), "FULL_N": len(full),
            "RED_T11": red_t11, "SLACK_T11": round(float(slack_t11), 2),
            "UPSIZE_KM": round(upsize_km, 3), "DN_UP": dn_up,
            "LINK_PCT": round(link_pct, 1), "AUTO_PCT": round(auto_pct, 1),
            "WADI_PCT": round(wadi_pct, 1), "HAZ_COV": round(haz_cov, 1),
            "E_REASON": ereason, "ARTFALL_M": round(art_fall, 2),
            "EMPTY_KM": round(empty_km, 3),
            "ALT_N": alt_n, "ALT_DZ_M": round(alt_dz, 2),
            "LOWFLOW": int(float(gpipe.get("QPK_LS", 0.0)) < LOW_FLOW_LS),
            "HEAD": int(head),
            "geometry": Point(xy[b]),
        })

    df = gpd.GeoDataFrame(rows, crs=C.EPSG)
    print(f"depth identity (cover + pipe fall - ground fall = depth): "
          f"worst residual over the 220 runs {max(resid):.6f} m")

    # ---- chains: attribute every D to the breach that started it ------------
    head_of = {int(r["NODE"]): int(r["HEAD"]) for _, r in df.iterrows()}
    lifts_set = set(int(n) for n in lifts)
    root, pos = {}, {}
    for n in head_of:
        seen, cur_, p = [], n, 0
        while head_of.get(cur_) in lifts_set and head_of[cur_] != cur_:
            seen.append(cur_)
            cur_ = head_of[cur_]
            p += 1
            if p > 500:
                break
        root[n] = cur_
        pos[n] = p
    df["CHAIN_RT"] = [root[int(n)] for n in df.NODE]
    df["CHAIN_POS"] = [pos[int(n)] for n in df.NODE]

    # ---- the honest cascade answer, resolved from the top down --------------
    # RED_FULL asks whether the path from the true network head works, which is right only
    # if every station above is removed too. RED (isolated) asks whether the stretch below
    # the station above works, which is right only if that station stays. Neither is the
    # answer on its own: the station above stays or goes, and that decides which stretch
    # the one below has to swallow. So walk the chains top down and let each decision set
    # the next one's starting point.
    def slack_of(path, waive_tractive=False):
        if len(path) < 2:
            return np.inf
        seg_l = np.array([G[u][v]["len"] for u, v in zip(path[:-1], path[1:])])
        sf = np.full(len(seg_l), CRIT.TABLE11_FLOOR) if waive_tractive else \
            np.array([s_floor_for(qpk_of.get((u, v), 0.0))
                      for u, v in zip(path[:-1], path[1:])])
        cum = np.concatenate([[0.0], np.cumsum(sf * seg_l)])
        gfp = np.array([z[path[0]] - z[k] for k in path])
        od = (dn_for_slope(sf[0]) or DN_ORDER[-1]) / 1000.0
        return (MAX_DEPTH - MIN_COVER_CROWN - od) - float(np.max(cum - gfp))

    def sequential(waive_tractive=False):
        removed, slk = set(), {}
        for b in df.sort_values("CHAIN_POS").NODE.astype(int):
            path, n = [b], b
            while True:
                u = gov.get(n)
                if u is None:
                    break
                path.append(u)
                if u in lifts and u not in removed:
                    break                      # a station that survives: the run starts here
                n = u
            path.reverse()
            s_ = slack_of(path, waive_tractive)
            slk[b] = s_
            if s_ >= 0.0:
                removed.add(b)
        return removed, slk

    removed, slk = sequential(False)
    removed_t11, _ = sequential(True)
    df["RED_SEQ"] = [int(int(n) in removed) for n in df.NODE]
    df["SLACKSEQ"] = [round(float(min(slk[int(n)], 99.0)), 2) for n in df.NODE]
    df["RED_SEQT11"] = [int(int(n) in removed_t11) for n in df.NODE]
    df["BLOCKER"] = np.where(df.RED_SEQ == 1, "-",
                             np.where(df.RED_T11 == 1, "TRACTIVE", "GROUND"))
    df["FIX"] = np.where(df.CAUSE_PHY == "E", "DELETE CORRIDOR",
                         np.where(df.RED_SEQ == 1, "UPSIZE",
                                  np.where((df.BLOCKER == "TRACTIVE") &
                                           (df.LOWFLOW == 1), "NO SEWER / RETHINK",
                                           "STATION")))
    df = df.sort_values(["CHAIN_RT", "CHAIN_POS", "NODE"]).reset_index(drop=True)
    df["BID"] = np.arange(1, len(df) + 1)

    out_shp = os.path.join(C.OUT_SHP, "W10_breach_diagnosis.shp")
    df.to_file(out_shp)
    out_csv = os.path.join(C.OUT_RUN, "W10_breach_diagnosis.csv")
    df.drop(columns="geometry").to_csv(out_csv, index=False)
    print(f"\nwrote {out_shp} and {out_csv} ({len(df)} breaches)")

    # ---- the summary the document is written from ---------------------------
    print("\ncause class (D takes precedence for a chained breach):")
    print(df.groupby("CAUSE").agg(
        n=("BID", "size"), margin_med=("MARGIN_M", "median"),
        margin_max=("MARGIN_M", "max"), run_km=("RUN_M", lambda s: s.median() / 1000),
        gfall_med=("GFALL_M", "median"), qpk_med=("QPK_LS", "median"),
        reducible=("RED_SEQ", "sum")).round(2).to_string())
    print("\nphysical cause, ignoring the chain:")
    print(df.groupby("CAUSE_PHY").agg(
        n=("BID", "size"), reducible=("RED_SEQ", "sum")).to_string())
    print("\nwhat blocks the ones that cannot be upsized away:")
    print(df.groupby("BLOCKER").agg(
        n=("BID", "size"), qpk_med=("QPK_LS", "median"),
        plots_med=("PLOTS_UP", "median")).round(2).to_string())
    print("\nrecommended action:")
    print(df.FIX.value_counts().to_string())
    print(f"\nREDUCIBLE, run judged in isolation (upper bound): {int(df.REDUCIBLE.sum())}")
    print(f"REDUCIBLE, whole path from the network head    : {int(df.RED_FULL.sum())}")
    print(f"REDUCIBLE, cascades resolved top down          : "
          f"{int(df.RED_SEQ.sum())}    <-- the answer")
    print(f"IRREDUCIBLE                                    : "
          f"{int((1-df.RED_SEQ).sum())}    <-- the true station count")
    print(f"   of which blocked by the GROUND        : "
          f"{int((df.BLOCKER=='GROUND').sum())}")
    print(f"   of which blocked by TRACTIVE FORCE    : "
          f"{int((df.BLOCKER=='TRACTIVE').sum())}")
    print(f"GROUND-LIMITED (whole path at 0.075 %, self-cleansing set aside):")
    print(f"   still breaches                          : {int((1-df.RED_T11).sum())}")
    print(f"   same test run as a cascade              : {int((1-df.RED_SEQT11).sum())}")
    print(f"independent chains                       : {df.CHAIN_RT.nunique()}")
    print(f"chains with at least one irreducible member: "
          f"{df[df.RED_SEQ==0].CHAIN_RT.nunique()}")
    print(f"under {LOW_FLOW_LS:.0f} L/s peak                      : {int(df.LOWFLOW.sum())}")
    print(f"   of those, irreducible                 : "
          f"{int(((df.LOWFLOW==1)&(df.RED_SEQ==0)).sum())}")
    print(f"total upsize length if every reducible run is relieved: "
          f"{df[df.RED_SEQ==1].UPSIZE_KM.sum():,.1f} km")

    # ---- breaches are not stations: consolidate the survivors the same way ---
    # Rule 9 exactly as the published run applies it - p2_sizing merges anything within
    # 1.5 km, and p6_force then keeps a station only where the flow ARRIVING at it reaches
    # 50 properties on the locked load basis. The proximity count p2_sizing writes into
    # W10_stations_final.shp is not the catchment: it put 10,523 plots against a station
    # carrying 5.4 m3/d. Same threshold here, so 220 -> 33 -> 11 reproduces.
    from shapely.ops import unary_union
    Q50 = 50 * 1.456 * 5.32 * 164.0 * 0.85 / 1000.0     # m3/d, per p6_force.py

    def stations(sub, radius=1500.0):
        if not len(sub):
            return 0, 0
        blobs = gpd.GeoDataFrame(
            geometry=[unary_union(sub.geometry.buffer(radius / 2))],
            crs=C.EPSG).explode(index_parts=False).reset_index(drop=True)
        keep = 0
        for g in blobs.geometry:
            m = sub.intersects(g)
            if m.any() and sub.loc[m, "QADF_M3D"].max() >= Q50:
                keep += 1
        return len(blobs), keep

    # How many of the clusters AS SOLVED disappear entirely? Consolidating the survivors and
    # comparing counts is not the right question: 1.5 km chaining is transitive, so taking
    # away the breaches in the middle of a cluster SPLITS it and the count can rise even as
    # the problem shrinks. The monotone question is which of today's clusters is left with
    # no breach at all.
    cl = gpd.GeoDataFrame(geometry=[unary_union(df.geometry.buffer(750.0))],
                          crs=C.EPSG).explode(index_parts=False).reset_index(drop=True)
    gone = surv = 0
    for g in cl.geometry:
        m = df.intersects(g)
        if not m.any():
            continue
        if df.loc[m, "QADF_M3D"].max() < Q50:
            continue
        surv += 1
        if df.loc[m, "RED_SEQ"].all():
            gone += 1
    print(f"\nof the {surv} stations as solved, {gone} lose every breach to upsizing "
          f"and {surv - gone} keep at least one")

    n_all, k_all = stations(df)
    n_irr, k_irr = stations(df[df.RED_SEQ == 0])
    n_gnd, k_gnd = stations(df[df.RED_T11 == 0])
    print(f"\nSTATIONS after rule 9 (1.5 km, 50 properties draining through):")
    print(f"   all 220 breaches as solved      : {n_all:3d} consolidated -> {k_all:3d} stations")
    print(f"   the {int((1-df.RED_SEQ).sum()):3d} left after upsizing     : "
          f"{n_irr:3d} consolidated -> {k_irr:3d} stations")
    print(f"   the {int((1-df.RED_T11).sum()):3d} the GROUND alone forbids: "
          f"{n_gnd:3d} consolidated -> {k_gnd:3d} stations")
    pd.DataFrame([
        {"set": "as solved", "breaches": len(df), "consolidated": n_all, "stations": k_all},
        {"set": "after upsizing", "breaches": int((1 - df.RED_SEQ).sum()),
         "consolidated": n_irr, "stations": k_irr},
        {"set": "ground-limited floor", "breaches": int((1 - df.RED_T11).sum()),
         "consolidated": n_gnd, "stations": k_gnd},
    ]).to_csv(os.path.join(C.OUT_RUN, "W10_breach_stations.csv"), index=False)
    print(f"\ntotal {time.time()-t0:.0f} s")
    return df


if __name__ == "__main__":
    main()
