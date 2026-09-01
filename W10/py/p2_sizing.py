"""Phase 2 proper - size every pipe, then re-solve the depths on the real gradients.

Phase 2's first pass swept an assumed minimum gradient and found the lifting-station count
ranged from 77 to 254 across 0.10 % to 0.50 %. That range is not a result, it is the
question restated: a gradient is a consequence of a diameter and a flow, so until the pipes
are sized nobody knows which end of it is real.

The loads are now allocated (Phase 1.3, 74,675 m3/d at saturation over 64,027 records), so
this closes the loop:

  1. each plot's average flow lands on the corridor node it fronts
  2. flows accumulate down the flow tree, with infiltration added per kilometre upstream
  3. the peaking factor is applied to the accumulated flow, held below 100 properties
     where the guideline prescribes no formula
  4. every pipe is sized: the smallest DN that carries its peak flow inside its d/D limit,
     at the steeper of Table 11 and the tractive-force minimum for that flow
  5. the depth solve runs again with each pipe's OWN minimum gradient instead of one
     assumed for all of them

Hydraulics are W8's `sewnet.hydra` - Colebrook-White on the true internal bore, with the
Table 11 gate that proves it reproduces the guideline's own minimum gradients. Not
reimplemented here.

Run:  python p2_sizing.py
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
from shapely.geometry import Point

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "W8", "py"))

import config as C
import netlib as N
from p1_subnetworks import flow_tree
from p2_depths import solve, edge_profiles, MIN_COVER_CROWN, MAX_DEPTH
from sewnet import hydra
from sewnet.criteria import DEFAULT as CRIT

warnings.filterwarnings("ignore")

# Corridor nodes sit about 100 m apart, so a plot can be 50 m from the corridor and
# still further than that from the nearest NODE. At 80 m only 90.2 % of the load found a
# node; the shortfall is a discretisation artefact, not unserved plots.
ASSIGN_M = 160.0


def assign_loads(xy, nodes):
    """Each plot's average flow onto the corridor node it fronts."""
    # The GeoPackage is canonical. The same layer as a shapefile is 67.8 MB against
    # 22.9 MB, because GDAL pads every string field to 80 characters and there are seven
    # of them over 64,071 records - and the layer is regenerated whenever the load basis
    # moves, so it would land in the history each time.
    gpkg = os.path.join(C.OUT_SHP, "W10_plot_loads.gpkg")
    pl = gpd.read_file(gpkg, layer="plot_loads") if os.path.exists(gpkg) else         gpd.read_file(os.path.join(C.OUT_SHP, "W10_plot_loads.shp"))
    qcol = "Q_AVG_M3D" if "Q_AVG_M3D" in pl.columns else "Q_AVG_M3"
    pts = gpd.GeoDataFrame(geometry=[Point(xy[n]) for n in nodes],
                           data={"NODE": list(nodes)}, crs=C.EPSG)
    j = gpd.sjoin_nearest(pl[[qcol, "geometry"]], pts, how="left",
                          max_distance=ASSIGN_M, distance_col="D")
    j = j[~j.index.duplicated(keep="first")]
    q = defaultdict(float)
    for node, v in zip(j["NODE"], j[qcol]):
        if node == node and v == v:
            q[int(node)] += float(v)
    placed = sum(q.values())
    total = float(pl[qcol].sum())
    print(f"loads: {total:,.0f} m3/d total, {placed:,.0f} m3/d placed "
          f"({100*placed/total:.1f} %), {len(q):,} nodes carry load")
    return q, total, placed


def accumulate(G, nxt, q_node):
    """Flow and upstream length at every node, working from the heads down."""
    ups = defaultdict(list)
    for n, m in nxt.items():
        ups[m].append(n)
    order, seen, stack = [], set(), [n for n in G if n not in nxt]
    # a proper topological order: repeatedly take nodes whose upstream is all done
    indeg = {n: len(ups.get(n, ())) for n in G}
    ready = [n for n in G if indeg[n] == 0]
    while ready:
        n = ready.pop()
        order.append(n)
        m = nxt.get(n)
        if m is not None:
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)

    qacc, lacc = defaultdict(float), defaultdict(float)
    for n in order:
        qacc[n] += q_node.get(n, 0.0)
        m = nxt.get(n)
        if m is None:
            continue
        L = G[n][m]["len"] if G.has_edge(n, m) else 0.0
        qacc[m] += qacc[n]
        lacc[m] += lacc[n] + L
    return qacc, lacc, order


def size_all(G, nxt, qacc, lacc):
    """Diameter and minimum laying gradient for every pipe."""
    hold_mld = CRIT.PF_HOLD_PROPERTIES * CRIT.PLOT_QADF_M3D / 1000.0
    out = {}
    for n, m in nxt.items():
        if not G.has_edge(n, m):
            continue
        qadf = qacc[n] + CRIT.INFILT_L_D_KM * (lacc[n] / 1000.0) / 1000.0
        pf = CRIT.pf_merrimack(max(qadf / 1000.0, hold_mld))
        qpk = qadf * pf / 86400.0                      # m3/s
        dn, s = CRIT.DN_SERIES[0], None
        for _ in range(6):
            s = hydra.smin_for(dn, qpk, CRIT)
            dn2, y, v = hydra.size_pipe(qpk, s, CRIT)
            if dn2 is None:
                dn = CRIT.DN_SERIES[-1]
                break
            if dn2 == dn:
                break
            dn = dn2
        out[(n, m)] = {"DN": dn, "SMIN": s, "QADF": qadf, "PF": pf, "QPK_LS": qpk * 1000}
    return out


def main():
    t0 = time.time()
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    cost, nxt, D = flow_tree(G, z, sink)

    q_node, total, placed = assign_loads(xy, list(G.nodes))
    qacc, lacc, order = accumulate(G, nxt, q_node)
    print(f"flow arriving at the works: {qacc[sink]:,.0f} m3/d "
          f"(+ infiltration {CRIT.INFILT_L_D_KM*(lacc[sink]/1000.0)/1000.0:,.0f})")

    t = time.time()
    pipes = size_all(G, nxt, qacc, lacc)
    print(f"sized {len(pipes):,} pipes ({time.time()-t:.0f} s)")
    dns = pd.Series([p["DN"] for p in pipes.values()])
    kms = defaultdict(float)
    for (n, m), p in pipes.items():
        kms[p["DN"]] += G[n][m]["len"] / 1000.0
    print("\n   DN     pipes      km")
    for dn in sorted(kms):
        print(f"   {dn:5d} {int((dns==dn).sum()):9,d} {kms[dn]:8.1f}")
    sm = pd.Series([p["SMIN"] for p in pipes.values()])
    print(f"\nminimum gradient required: median {100*sm.median():.3f} %, "
          f"p10 {100*sm.quantile(.1):.3f} %, p90 {100*sm.quantile(.9):.3f} %")

    # ---- depths on the REAL gradients --------------------------------------
    mid, midz = edge_profiles(G, lines)
    slope_of = {}
    for (n, m), p in pipes.items():
        slope_of[(n, m)] = p["SMIN"]
        slope_of[(m, n)] = p["SMIN"]

    ups = defaultdict(list)
    for n, m in nxt.items():
        ups[m].append(n)
    invert, lifts = {}, {}
    for n in order:
        zn = z.get(n, np.nan)
        if not np.isfinite(zn):
            continue
        shallow = zn - MIN_COVER_CROWN - 0.30
        cand = [shallow]
        for u in ups.get(n, ()):
            if u not in invert or not G.has_edge(u, n):
                continue
            s = slope_of.get((u, n), 0.003)
            cand.append(invert[u] - s * G[u][n]["len"])
        iv = min(cand)
        if zn - iv > MAX_DEPTH:
            lifts[n] = (zn - iv) - (zn - shallow)
            iv = shallow
        invert[n] = iv
    dep = {n: z[n] - invert[n] for n in invert if np.isfinite(z.get(n, np.nan))}
    dd = np.array(list(dep.values()))
    print(f"\nON THE REAL GRADIENTS: {len(lifts):,} depth breaches, "
          f"deepest {dd.max():.2f} m, median cover {np.median(dd):.2f} m, "
          f"total lift {sum(lifts.values()):,.0f} m")

    rows = []
    for (n, m), p in pipes.items():
        rows.append({"DN": p["DN"], "SLOPE_PCT": round(100 * p["SMIN"], 4),
                     "QADF_M3D": round(p["QADF"], 2), "PF": round(p["PF"], 3),
                     "QPK_LS": round(p["QPK_LS"], 2),
                     "LEN_M": round(G[n][m]["len"], 2),
                     "US_DEPTH": round(float(dep.get(n, 0)), 2),
                     "DS_DEPTH": round(float(dep.get(m, 0)), 2),
                     "geometry": lines[G[n][m]["line"]]})
    gp = gpd.GeoDataFrame(rows, crs=C.EPSG)
    gp.to_file(os.path.join(C.OUT_SHP, "W10_pipes.shp"))
    ls = gpd.GeoDataFrame(
        [{"LIFT_M": round(v, 2), "GROUND": round(float(z[n]), 2), "geometry": Point(xy[n])}
         for n, v in lifts.items()], crs=C.EPSG)
    if len(ls):
        ls.to_file(os.path.join(C.OUT_SHP, "W10_lift_sized.shp"))
    print(f"wrote W10_pipes.shp ({len(gp):,}, {gp.LEN_M.sum()/1000:,.1f} km) "
          f"and W10_lift_sized.shp ({len(ls):,})")

    # ---- breaches consolidated into stations (rule 9) ----------------------
    from shapely.ops import unary_union
    if len(ls):
        for r in (750, 1500):
            b = gpd.GeoDataFrame(
                geometry=[unary_union(ls.geometry.buffer(r / 2))],
                crs=C.EPSG).explode(index_parts=False)
            print(f"   consolidated at {r:,} m: {len(b):3d} stations")
        b = gpd.GeoDataFrame(geometry=[unary_union(ls.geometry.buffer(750))],
                             crs=C.EPSG).explode(index_parts=False).reset_index(drop=True)
        plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
        b["PLOTS"] = [int(plots.intersects(g).sum()) for g in b.geometry]
        b["BREACHES"] = [int(ls.intersects(g).sum()) for g in b.geometry]
        b["MAX_LIFT"] = [float(ls[ls.intersects(g)].LIFT_M.max()) for g in b.geometry]
        keep = b[b.PLOTS >= 50]
        print(f"   of {len(b)} consolidated stations, {len(keep)} serve 50+ plots "
              f"(rule 9 absorbs the other {len(b)-len(keep)})")
        gpd.GeoDataFrame(keep.drop(columns="geometry"),
                         geometry=keep.geometry.centroid,
                         crs=C.EPSG).to_file(
            os.path.join(C.OUT_SHP, "W10_stations_final.shp"))

    # corridor that carries no pipe: the graph has loops, a sewer is a tree
    unused = sum(d["len"] for u, v, d in G.edges(data=True)
                 if (u, v) not in pipes and (v, u) not in pipes) / 1000
    allkm = sum(d["len"] for *_, d in G.edges(data=True)) / 1000
    print(f"\ncorridor carrying no pipe (loop-closing alternatives): "
          f"{unused:,.1f} km of {allkm:,.1f} km")

    pd.DataFrame([{"dn": dn, "km": round(kms[dn], 2)} for dn in sorted(kms)]).to_csv(
        os.path.join(C.OUT_RUN, "p2_diameters.csv"), index=False)
    print(f"total {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
