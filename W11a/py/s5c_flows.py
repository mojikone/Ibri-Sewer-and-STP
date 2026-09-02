"""W11a stage 5c - flow accumulation, and the ground each reach sits on.

THE STAGE THAT WAS MISSING. Stages 1-5b build the graph and put a load at every chamber;
stage 6 levels and sizes each reach and needs to know what it carries. Nothing joined the
two, so stage 6 stopped with `reaches missing: QPK_LS, QADF_M3D, QINF_LS, PF, PF_METH,
ON_DUAL_M, ON_WADI_M, CROSS_ID` and the chain ended there. The ten stages were built in
parallel against the contract and this step fell between two of them.

WHAT IT DOES, and where every number comes from:

  1. Reads `connections` (one row per plot, Q_ADF_M3D and N_PROP at an OUT_NODE), `reaches`
     (chamber-to-chamber, split by stage 5) and `nodes` from W11a.gpkg.
  2. Builds the directed graph US_NODE -> DS_NODE and accumulates load, properties and
     upstream length down it in topological order.
  3. Peak factor: Merrimack `Qpdf = 2.65 Qadf^0.879` in Ml/d above 100 properties
     (G201-p71, mandatory). BELOW 100 properties G201 prescribes no formula at all, so the
     value is HELD at Merrimack evaluated on the 100-property flow and tagged PF_METH =
     'held'. This is stage 3's method, called from stage 3's own criteria object - not a
     second implementation of it.
  4. Infiltration 720 L/d/km on the accumulated upstream length (G201-p72-73), unpeaked.
  5. Measures ON_WADI_M and ON_DUAL_M on the REACH's own geometry and mints a CROSS_ID for
     every reach that crosses a wadi (philosophy H1a item 4). Measured, never inherited: a
     flag carried down from a corridor is a claim about stage 2, not a fact about this line.

WHAT IT DELIBERATELY DOES NOT DO. It does not size, level, or move anything. Diameter and
gradient are stage 6's, and a stage that quietly sized a pipe while claiming to add a flow
column would be the hardest kind of defect to find.

WHY IT USED TO HANG (2026-09-02, measured, not guessed). Three runs were killed at 10+ min.
The hazard raster was the suspect and it was innocent: the 8,606 x 15,204 window reads in
0.73 s and the 49,274-reach sampling loop runs in 1.0 s. The real cost was two lines that had
nothing to do with rasters, and both are fixed below where they occur:

  * the flow-balance section built `set(reaches.DS_NODE.astype(str))` INSIDE a comprehension
    over 50,033 nodes, so the set was rebuilt 50,033 times at 23 ms each - 19 to 26 minutes
    measured - to fill a variable nothing ever read;
  * the dual band was intersected against all 49,274 reaches one at a time against a single
    26,299-vertex polygon: 35.5 s, where only 59 reaches can possibly touch it.

Nothing about the arithmetic changed. The dual figures are bit-identical (max abs difference
0.0 m over all 49,274 reaches, 59 non-zero, 709.248497 m in total) because the filter only
skips reaches whose intersection is provably empty. Whole stage now runs in about 10 s.
"""
from __future__ import annotations

import os
import sys
import time
import warnings
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import shapely
from shapely.ops import substring, unary_union

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
W11A = os.path.dirname(HERE)
REPO = os.path.dirname(W11A)
BASE = os.path.dirname(os.path.dirname(REPO))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "W8", "py"))

from sewnet.criteria import DEFAULT as C            # noqa: E402
from w11a import audit                              # noqa: E402

GPKG = os.path.join(W11A, "shp", "W11a.gpkg")
RUN = os.path.join(W11A, "run")
P_ROADS = os.path.join(BASE, "Hydraulic", "SHP", "Road centerline 2", "Road_Centercline.shp")
P_HAZARD = os.path.join(BASE, "Data", "04 Lekhuwair", "Hazard_T50y.tif")
STAGE = "s5c_flows"

# Infiltration is charged on the accumulated upstream LENGTH. Stage 3 adds a small
# flow-proportional term for the reaches upstream of the trunk that it does not model
# individually; here every reach is modelled, so the term is zero and is not invented.
KM_PER_M3D = 0.0

DUAL_BAND_M = 6.0        # audit.h1's band, so the number this stage publishes is the number
                         # the auditor will read back


def say(m=""):
    print(m, flush=True)


def load() -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    import fiona
    have = set(fiona.listlayers(GPKG))
    need = {"reaches", "nodes", "connections"}
    if not need <= have:
        say("\nWAITING ON AN UPSTREAM STAGE - nothing computed, nothing written.")
        say(f"  needs {sorted(need - have)} in W11a.gpkg (present: {sorted(have)})")
        say("  run s4_hierarchy.py, then s5_chambers.py, then s5b_tertiary.py")
        raise SystemExit(0)
    r = gpd.read_file(GPKG, layer="reaches")
    n = gpd.read_file(GPKG, layer="nodes")
    c = gpd.read_file(GPKG, layer="connections")
    return r, n, c


def accumulate(reaches: gpd.GeoDataFrame, conns: gpd.GeoDataFrame
               ) -> Tuple[Dict, Dict, Dict, int]:
    """Sum load, properties and upstream length down the graph. Returns dicts by node."""
    G = nx.DiGraph()
    lens = {}
    for u, v, L in zip(reaches.US_NODE.astype(str), reaches.DS_NODE.astype(str),
                       reaches.geometry.length):
        # Parallel reaches between one pair of chambers would collapse in a DiGraph, so the
        # length carried is the LONGEST - infiltration is charged on pipe in the ground.
        if G.has_edge(u, v):
            lens[(u, v)] = max(lens[(u, v)], float(L))
        else:
            G.add_edge(u, v)
            lens[(u, v)] = float(L)

    q0: Dict[str, float] = {}
    n0: Dict[str, float] = {}
    for node, q, npr in zip(conns.OUT_NODE.astype(str),
                            pd.to_numeric(conns.Q_ADF_M3D, errors="coerce").fillna(0.0),
                            pd.to_numeric(conns.N_PROP, errors="coerce").fillna(0.0)):
        q0[node] = q0.get(node, 0.0) + float(q)
        n0[node] = n0.get(node, 0.0) + float(npr)

    # H15 says the network is a forest. Where it is not, break the cycles EXPLICITLY - a
    # topological sort on a cyclic graph raises, and silently dropping the flow instead
    # would be worse than either. nx.find_cycle returns ONE cycle in O(V+E); nx.simple_cycles
    # enumerates EVERY cycle and is exponential - it was tried here first and never returned
    # on 49,274 edges.
    n_cyc = 0
    while True:
        try:
            cyc = nx.find_cycle(G, orientation="original")
        except nx.NetworkXNoCycle:
            break
        a, b = cyc[0][0], cyc[0][1]
        G.remove_edge(a, b)
        n_cyc += 1
        if n_cyc > 5000:
            raise RuntimeError("over 5,000 cycles - this is not a forest and not a "
                               "roundable error; fix the topology upstream")

    q = {u: q0.get(u, 0.0) for u in G.nodes}
    npr = {u: n0.get(u, 0.0) for u in G.nodes}
    km = {u: 0.0 for u in G.nodes}
    for u in nx.topological_sort(G):
        for v in G.successors(u):
            q[v] += q[u]
            npr[v] += npr[u]
            km[v] += km[u] + lens[(u, v)] / 1000.0
    return q, npr, km, n_cyc


def ground(reaches: gpd.GeoDataFrame):
    """ON_WADI_M, ON_DUAL_M, CROSS_ID and the crossing SUB-GEOMETRY.

    The sub-geometry matters: contract.validate checks LEN_M against the row's own
    geometry, and a register carrying the crossing LENGTH against the whole REACH's
    geometry disagreed on 1,319 rows - so stage 9 refused to export, correctly. A
    crossing row describes the crossing, so it carries the crossing.
    """
    on_dual = np.zeros(len(reaches))
    dual_geom = [None] * len(reaches)
    if os.path.exists(P_ROADS):
        roads = gpd.read_file(P_ROADS).set_crs(32640, allow_override=True)
        dual = roads[roads["dual"].astype(str) == "1"]
        if len(dual):
            bufs = dual.geometry.buffer(DUAL_BAND_M).values
            band = unary_union(list(bufs))
            # Intersect only the reaches that CAN touch the band. The union is one polygon of
            # 26,299 vertices, so running it against all 49,274 reaches took 35.5 s to find
            # the 59 that hit it. An STRtree over the reaches, queried with the 289 individual
            # buffers, returns exactly those 59 in 0.04 s: a reach meets the union iff it
            # meets at least one part, and every reach the query drops has an empty
            # intersection and therefore a length of 0 - which is what the array already
            # holds. The intersection itself is still taken against the UNION, so overlapping
            # buffers on adjacent dual segments are not counted twice. Verified against the
            # old line over the whole layer: max absolute difference 0.0 m.
            hit = np.unique(shapely.STRtree(reaches.geometry.values)
                            .query(bufs, predicate="intersects")[1])
            if len(hit):
                # Keep the clipped geometry, not just its length. The crossings register
                # needs the portion that is actually inside the band - a row describing a
                # crossing must carry the crossing, or LEN_M and the geometry disagree and
                # the contract refuses the export.
                clipped = shapely.intersection(reaches.geometry.values[hit], band)
                on_dual[hit] = shapely.length(clipped)
                for k, i in enumerate(hit):
                    dual_geom[int(i)] = clipped[k]

    on_wadi = np.zeros(len(reaches))
    cross = [""] * len(reaches)
    xgeo = [None] * len(reaches)         # the portion actually on an obstacle
    # NOT named `sub`: the strip-reading loop below already binds that to a
    # rasterio Window, and the shadow only surfaced at the assignment.
    if os.path.exists(P_HAZARD):
        import rasterio
        from rasterio.windows import from_bounds
        step = audit.WADI_SAMPLE_M
        # Read the hazard grid ONCE into a windowed boolean mask and index it, instead of
        # calling rasterio.sample per reach. Sampling 49,274 reaches one at a time is about
        # 1.2 million point reads through the driver and did not finish in ten minutes;
        # this is the same arithmetic in a few seconds. Stage 2 already does it this way.
        # Read in STRIPS and keep only the boolean, never the float. The window over the
        # network is about 45 x 25 km at 3 m - some 124 million cells - and reading it in
        # one call holds a 500 MB float32 array plus two copies, which thrashes rather than
        # computes. Stage 2 reads the same grid this way for the same reason.
        l, b, r_, t = reaches.total_bounds
        with rasterio.open(P_HAZARD) as src:
            ND = src.nodata
            win = from_bounds(l - 50, b - 50, r_ + 50, t + 50,
                              src.transform).round_offsets().round_lengths()
            tr = src.window_transform(win)
            H, W = int(win.height), int(win.width)
            mask = np.zeros((H, W), dtype=bool)
            for r0 in range(0, H, 2000):
                r1 = min(H, r0 + 2000)
                sub = rasterio.windows.Window(win.col_off, win.row_off + r0, W, r1 - r0)
                a = src.read(1, window=sub)
                ok = np.isfinite(a)
                if ND is not None:
                    ok &= (a != ND)
                mask[r0:r1] = ok & (a >= 4)
                del a, ok

        def at(xs, ys):
            col = ((np.asarray(xs) - tr.c) / tr.a).astype(np.int64)
            row = ((np.asarray(ys) - tr.f) / tr.e).astype(np.int64)
            ok = (row >= 0) & (col >= 0) & (row < H) & (col < W)
            out = np.zeros(len(col), bool)
            if ok.any():
                out[ok] = mask[row[ok], col[ok]]
            return out

        for i, g in enumerate(reaches.geometry):
            L = g.length
            k = max(2, int(L / step) + 1)
            xy = shapely.get_coordinates(
                shapely.line_interpolate_point(g, np.linspace(0.0, L, k)))
            on = at(xy[:, 0], xy[:, 1])
            if on.any():
                on_wadi[i] = float(on.mean()) * L
                # First and last sample on the obstacle bound the crossing. Sampled at
                # WADI_SAMPLE_M, so the bound is that coarse - stated, not hidden.
                idx = np.where(on)[0]
                a0 = float(idx[0]) / (k - 1) * L
                b0 = float(idx[-1] + 1) / (k - 1) * L
                seg = substring(g, max(0.0, a0), min(L, b0))
                if not seg.is_empty and seg.geom_type == "LineString" and seg.length > 0:
                    xgeo[i] = seg
                    on_wadi[i] = seg.length
        k = 0
        for i in np.where(on_wadi > 0)[0]:
            k += 1
            cross[i] = f"W11a-XG{k:05d}"

    # A DUAL-CARRIAGEWAY crossing is scheduled too. H1 forbids running ALONG one - no pipe of
    # any kind, trunk included, because it cannot be dug up - but permits a short square
    # crossing, and the contract refuses to publish a reach that touches one with no CROSS_ID
    # (W10 shipped 47 unscheduled). Stage 5c measured ON_DUAL_M and scheduled nothing, so the
    # publish failed on 51 reaches that are all genuine crossings: the longest single contact
    # is 62.1 m against criteria.DUAL_CROSS_MAX_M of 70 m.
    #
    # Where a reach crosses BOTH, the wadi id wins: it carries the heavier obligations
    # (G201 9.3 - bed profile, flood levels, MoAFWR approval). Nothing is lost, because
    # ON_DUAL_M stays published on the reach and audit.h1 reads it independently of any id.
    k = 0
    for i in np.where((on_dual > 0) & np.array([c == "" for c in cross]))[0]:
        k += 1
        cross[i] = f"W11a-XD{k:05d}"
    # A dual-only crossing carries the clipped band portion; take the longest part where the
    # clip came back multi-part, because a register row is one crossing.
    for i in range(len(reaches)):
        if xgeo[i] is None and on_dual[i] > 0 and dual_geom[i] is not None:
            gg = dual_geom[i]
            if gg.geom_type == "MultiLineString":
                gg = max(gg.geoms, key=lambda q: q.length)
            if gg.geom_type == "LineString" and gg.length > 0:
                xgeo[i] = gg
    return on_wadi, on_dual, cross, xgeo


def main() -> int:
    t0 = time.time()
    say("=" * 88)
    say("W11a  STAGE 5c - FLOW ACCUMULATION")
    say("      the step between 'a load sits at every chamber' and 'this pipe carries X'")
    say("=" * 88)

    reaches, nodes, conns = load()
    say(f"\n  reaches {len(reaches):,}  ({reaches.geometry.length.sum() / 1000:,.1f} km)"
        f"   nodes {len(nodes):,}   connections {len(conns):,}")

    q, npr, km, n_cyc = accumulate(reaches, conns)
    if n_cyc:
        say(f"  WARNING: {n_cyc} edge(s) removed to break cycles - H15 says the network is "
            f"a forest, so this is a topology defect, not a modelling choice")

    root_q = max(q.values()) if q else 0.0
    root_n = max(npr.values()) if npr else 0.0
    q_per_prop = root_q / max(root_n, 1.0)
    PF_HELD = C.pf_merrimack(C.PF_HOLD_PROPERTIES * q_per_prop / 1000.0)

    us = reaches.US_NODE.astype(str).values
    qadf = np.array([q.get(u, 0.0) for u in us])
    nprop = np.array([npr.get(u, 0.0) for u in us])
    upkm = np.array([km.get(u, 0.0) for u in us])

    qinf = (C.INFILT_L_D_KM / 86400.0) * (upkm + KM_PER_M3D * qadf)
    big = nprop > C.PF_HOLD_PROPERTIES
    pf = np.where(big, [C.pf_merrimack(x / 1000.0) if x > 0 else 1.0 for x in qadf], PF_HELD)
    qpk = qadf * 1000.0 / 86400.0 * pf + qinf

    on_wadi, on_dual, cross, xsub = ground(reaches)

    out = reaches.copy()
    out["QADF_M3D"] = np.round(qadf, 4)
    out["N_PROP"] = np.round(nprop, 3)
    out["QINF_LS"] = np.round(qinf, 6)
    out["PF"] = np.round(pf, 4)
    out["PF_METH"] = np.where(big, "merrimack", "held")
    out["QPK_LS"] = np.round(qpk, 6)
    out["UPSTR_KM"] = np.round(upkm, 4)
    out["ON_WADI_M"] = np.round(on_wadi, 3)
    out["ON_DUAL_M"] = np.round(on_dual, 3)
    out["CROSS_ID"] = cross
    out["STAGE"] = STAGE

    # ---- the checks this stage owes -----------------------------------------------------
    say("\nFLOW BALANCE  (nothing created, nothing lost)")
    total_conn = float(pd.to_numeric(conns.Q_ADF_M3D, errors="coerce").fillna(0).sum())
    outfalls = set(nodes.loc[nodes.NODE_KIND.astype(str) == "outfall", "NODE_UID"].astype(str)) \
        if "NODE_KIND" in nodes.columns else set()
    at_out = sum(q.get(u, 0.0) for u in outfalls)
    # A head-node list used to be built here as
    #     heads = [u for u in q if u not in set(reaches.DS_NODE.astype(str))]
    # and it was the reason this stage never finished. `set(reaches.DS_NODE.astype(str))` sits
    # in the comprehension's CONDITION, so it was rebuilt once per key in q - 50,033 times at
    # 23 ms, 19 to 26 minutes measured - and no line below ever read the result. Removed
    # rather than made O(n): it published nothing, so nothing published changes. If a head
    # count is wanted in the balance, hoist the set out of the loop first.
    say(f"    load placed by stage 5b        {total_conn:12,.1f} m3/d")
    say(f"    arriving at an outfall node    {at_out:12,.1f} m3/d "
        f"({100 * at_out / max(total_conn, 1e-9):.1f} %)")
    say(f"    largest single reach           {qadf.max():12,.1f} m3/d "
        f"({qpk.max():,.0f} L/s peak)")
    say(f"    reaches carrying nothing       {int((qadf <= 0).sum()):12,}   "
        f"({out.geometry.length[qadf <= 0].sum() / 1000:,.1f} km - a pipe that conveys "
        f"nothing and collects nothing is a stage 2/4 question, not a sizing one)")
    say(f"    peak factor                    merrimack on {int(big.sum()):,} reaches, "
        f"held at {PF_HELD:.3f} on {int((~big).sum()):,} (G201-p71: no formula below "
        f"{C.PF_HOLD_PROPERTIES:.0f} properties)")
    # The SYSTEM total is the rate times the NETWORK length. Summing the per-reach values
    # instead counts every upstream kilometre once per downstream reach - it printed
    # 1,259 L/s against a true 14.5, an 87x overstatement. The per-reach numbers were right;
    # only this total was wrong. Every accumulated quantity has this trap in it.
    net_km = (float(out["LEN_M"].sum()) / 1000.0 if "LEN_M" in out.columns
              else float(out.geometry.length.sum()) / 1000.0)
    say(f"    infiltration                   {C.INFILT_L_D_KM:.0f} L/d/km (G201-p72-73) on "
        f"{net_km:,.1f} km = {C.INFILT_L_D_KM * net_km / 86400.0:,.1f} L/s for the SYSTEM; "
        f"charged per reach on ITS upstream length, worst reach {qinf.max():,.1f} L/s")

    # Does this drain as one network, or as many? In a network draining to a single works the
    # last trunk reach carries essentially the whole load. Far below that is fragmentation
    # showing up in the HYDRAULICS - and every size and level downstream is then computed for
    # a network nobody intends to build.
    conc = 100.0 * qadf.max() / max(total_conn, 1e-9)
    say(f"    biggest pipe carries           {conc:5.1f} % of the placed load"
        f"{'' if conc > 80 else '   <-- FRAGMENTED, see OPEN-S4-1'}")

    say("\nGROUND, MEASURED ON THESE REACHES  (not inherited from a corridor flag)")
    nw = int((on_wadi > 0).sum()); nd = int((on_dual > 0).sum())
    say(f"    touching wadi ground           {nw:,} reaches, {on_wadi.sum() / 1000:,.2f} km"
        f" - each scheduled with a CROSS_ID (H1a item 4)")
    say(f"    inside the {DUAL_BAND_M:.0f} m dual band        {nd:,} reaches, "
        f"{on_dual.sum() / 1000:,.2f} km")

    out.to_file(GPKG, layer="reaches", driver="GPKG")

    # The crossings REGISTER, at REACH level. Stage 2 publishes a corridor-level one, but
    # audit.r4 reads `reaches` and joins CROSS_ID against this register - so a corridor-level
    # register leaves every reach-level id pointing at nothing, and nothing counts as
    # scheduled however many ids exist. The register is what carries the obligations forward.
    _sch = out[out["CROSS_ID"].astype(str) != ""].copy()
    if len(_sch):
        _pos = {u: k for k, u in enumerate(out["EDGE_UID"])}
        _geo = [xsub[_pos[u]] for u in _sch["EDGE_UID"]]
        _keep = [g is not None and not g.is_empty for g in _geo]
        _sch, _geo = _sch[_keep], [g for g, k in zip(_geo, _keep) if k]
        _wadi = _sch["ON_WADI_M"] > 0
        _reg = gpd.GeoDataFrame(dict(
            CROSS_ID=_sch["CROSS_ID"].values,
            EDGE_UID=_sch["EDGE_UID"].values,
            OBSTACLE=np.where(_wadi, "wadi", "dual"),
            LEN_M=np.round([g.length for g in _geo], 3),
            # Square by construction: stage 2 deleted everything that was not, and H1's own
            # band test re-checks it on the published layer. Published as 90 rather than
            # measured per reach, and that is a DECLARATION - audit.h1 is the measurement.
            ANGLE_DEG=[90.0] * len(_sch),
            METHOD=["open_cut"] * len(_sch),
            # APPROVED = 0 until a third-party consent exists. G201-p85 requires MoAFWR
            # approval for a wadi crossing; an open item should never be a silent one.
            APPROVED=[0] * len(_sch),
            SRC=_sch["SRC"].values, CONFIDENCE=_sch["CONFIDENCE"].values,
            STAGE=[STAGE] * len(_sch)),
            geometry=_geo, crs=out.crs)
        _reg.to_file(GPKG, layer="crossings", driver="GPKG")
        say(f"    crossings registered            {int(_wadi.sum()):,} wadi and "
            f"{int((~_wadi).sum()):,} dual, all APPROVED = 0 until consent exists")

    os.makedirs(RUN, exist_ok=True)
    cols = [c for c in out.columns if c != "geometry"]
    out[cols].to_csv(os.path.join(RUN, "s5c_reach_flows.csv"), index=False)
    say(f"\n  written  {GPKG}  (layer 'reaches', {len(out):,} rows, "
        f"{len([c for c in out.columns if c != 'geometry'])} fields)")
    say(f"           {os.path.join(RUN, 's5c_reach_flows.csv')}")
    say(f"\ntotal {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
