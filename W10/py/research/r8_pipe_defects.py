"""The same defects, measured on the PIPE rather than on the corridor.

A defect in a corridor the solver never used costs nothing. 1,882.9 km of pipe was laid in
2,211.8 km of corridor, so the two sets are not the same and the corridor figures are an
upper bound on the problem. This re-measures wadi, dual carriageway and through-plot on the
reaches that actually carry pipe, split by the corridor source each was laid in.

It also reconciles the wadi number, which the project quotes three ways:
  170.5 km  netlib, on the NODED corridor network INCLUDING the 92.3 km trunk
  157.8 km  r1, on W10_corridors.shp, which excludes the trunk
  131.7 km  OPTIMISATION.md, on the pipe

Run:  python r8_pipe_defects.py
"""
import os
import sys
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")
OUT_RUN = os.path.join(C.OUT, "run")
SAMPLE_M = 10.0
DUAL_BAND = 6.0
PLOT_INSET_M = 3.0


def samples(lines, step=SAMPLE_M):
    xs, ys, own, wt = [], [], [], []
    for i, ln in enumerate(lines):
        n = max(1, int(np.ceil(ln.length / step)))
        w = ln.length / n
        for k in range(n):
            p = ln.interpolate((k + 0.5) * w)
            xs.append(p.x); ys.append(p.y); own.append(i); wt.append(w)
    return np.array(xs), np.array(ys), np.array(own, dtype=np.int64), np.array(wt)


def main():
    p = gpd.read_file(os.path.join(C.OUT_SHP, "W10_pipe_surplus.shp"))
    p = p.explode(index_parts=False).reset_index(drop=True)
    p = p[p.geometry.geom_type == "LineString"].reset_index(drop=True)
    p["LEN_M"] = p.length
    lines = list(p.geometry)
    total = p.LEN_M.sum() / 1000
    print(f"pipe: {len(p):,} reaches, {total:,.1f} km")

    xs, ys, own, wt = samples(lines)
    with rasterio.open(C.HAZARD) as src:
        v = np.array([a[0] for a in src.sample(zip(xs, ys))], dtype=float)
    bad = np.isfinite(v) & (v > -1000) & (np.floor(v) >= 4)
    p["WADI_M"] = np.bincount(own[bad], weights=wt[bad], minlength=len(lines))
    print(f"   on wadi ground: {p.WADI_M.sum()/1000:,.1f} km "
          f"({100*p.WADI_M.sum()/p.LEN_M.sum():.1f} %)")

    roads = gpd.read_file(C.ROADS).set_crs(C.EPSG, allow_override=True)
    dual = unary_union(roads[roads["dual"].astype(str) == "1"].geometry.buffer(DUAL_BAND))
    p["DUAL_M"] = [g.intersection(dual).length for g in lines]
    print(f"   within {DUAL_BAND:.0f} m of a dual carriageway centre line: "
          f"{p.DUAL_M.sum()/1000:,.2f} km "
          f"({100*p.DUAL_M.sum()/p.LEN_M.sum():.2f} %)")

    from shapely.strtree import STRtree
    plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
    pg = [g.buffer(-PLOT_INSET_M) for g in plots.geometry]
    pg = [g for g in pg if g is not None and not g.is_empty]
    tree = STRtree(pg)
    inp = np.zeros(len(lines))
    for i, ln in enumerate(lines):
        idx = tree.query(ln)
        if len(idx) == 0:
            continue
        try:
            inp[i] = ln.intersection(unary_union([pg[int(j)] for j in idx])).length
        except Exception:
            pass
    p["PLOTIN_M"] = inp
    print(f"   more than {PLOT_INSET_M:.0f} m inside a registered plot: "
          f"{p.PLOTIN_M.sum()/1000:,.1f} km "
          f"({100*p.PLOTIN_M.sum()/p.LEN_M.sum():.1f} %)")

    t = p.groupby("SRC").agg(
        km=("LEN_M", lambda s: round(s.sum() / 1000, 1)),
        wadi_km=("WADI_M", lambda s: round(s.sum() / 1000, 1)),
        dual_km=("DUAL_M", lambda s: round(s.sum() / 1000, 2)),
        plotin_km=("PLOTIN_M", lambda s: round(s.sum() / 1000, 1)),
        surplus_km=("SURPLUS", lambda s: 0.0))
    t["surplus_km"] = (p[p.SURPLUS == 1].groupby("SRC").LEN_M.sum() / 1000
                       ).reindex(t.index).fillna(0).round(1)
    t["removable_km"] = (p[p.REMOVABLE == 1].groupby("SRC").LEN_M.sum() / 1000
                         ).reindex(t.index).fillna(0).round(1)
    for c in ("wadi", "dual", "plotin", "surplus", "removable"):
        t[c + "_pct"] = (100 * t[c + "_km"] / t.km).round(1)
    print("\nby corridor source, on the pipe:")
    print(t.to_string())
    t.to_csv(os.path.join(OUT_RUN, "r8_pipe_defects.csv"))

    p[["SRC", "DN", "LEN_M", "QADF_M3D", "D_LOAD", "SURPLUS", "REMOVABLE",
       "WADI_M", "DUAL_M", "PLOTIN_M", "geometry"]].to_file(
        os.path.join(C.OUT_SHP, "W10_pipe_surplus.shp"))
    print("\nupdated W10_pipe_surplus.shp with the defect fields")


if __name__ == "__main__":
    main()
