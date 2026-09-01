"""Do the corridor sources agree where they overlap, and which one carries the pipe?

Three questions the quality measurement cannot answer on its own:

  1. AGREEMENT. `auto_road` was cut wherever the draftsman already covered the same
     street, so by construction the two barely overlap in the output. That hides the
     interesting number: where BOTH sources describe the same street, how far apart do
     they put its centre line? A large offset means one of them is wrong about where the
     street is, and the design was laid on whichever won.

  2. CONNECTIVITY. The endpoint test in r1 found every `auto_link` endpoint sitting
     exactly 1.0 m short of the corridor it is meant to join - the `buffer(1.0)` inside
     `p0_auto.stitch`. This measures whether the topology phase recovers it and at what
     cost, so the finding is reported as what it is rather than as a broken network.

  3. WHICH SOURCE CARRIES PIPE. 1,883.6 km of pipe was laid in 2,211.8 km of corridor.
     The pipes carry no source tag, so each reach is attributed to the nearest corridor
     and the defect rates are re-read on the pipe rather than on the corridor. A defect
     in a corridor the solver never used costs nothing.

Run:  python r2_agreement.py
"""
import os
import sys
import time
import warnings

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")

MATCH_M = 25.0        # the coverage test p0_auto used
SAMPLE_M = 20.0
OUT_RUN = os.path.join(C.OUT, "run")


def samples(ln, step=SAMPLE_M):
    n = max(1, int(np.ceil(ln.length / step)))
    return [ln.interpolate((k + 0.5) * ln.length / n) for k in range(n)]


def main():
    t0 = time.time()
    draft = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors_drafted.shp"))
    draft = draft.explode(index_parts=False)
    draft = draft[draft.geometry.geom_type == "LineString"].reset_index(drop=True)
    tre = gpd.read_file(os.path.join(C.OUT_SHP, "W10_road_treatment.shp"))
    tre = tre[tre.USE == 1].reset_index(drop=True)
    print(f"draft {len(draft):,} lines {draft.length.sum()/1000:,.1f} km · "
          f"treated roads kept {len(tre):,} lines {tre.length.sum()/1000:,.1f} km")

    # ------------------------------------------------------------ 1  agreement
    dbuf = unary_union(draft.geometry.buffer(MATCH_M))
    cov = np.array([g.intersection(dbuf).length / max(g.length, 1e-9)
                    for g in tre.geometry])
    tre["COVER"] = cov
    same = tre[cov > 0.75]
    print(f"\nstreets described by BOTH sources (treated road >75 % inside the "
          f"draft's {MATCH_M:.0f} m band): {len(same):,} lines, "
          f"{same.length.sum()/1000:,.1f} km")

    dtree = STRtree(list(draft.geometry))
    rows = []
    for _, r in same.iterrows():
        for p in samples(r.geometry):
            j = dtree.query_nearest(p)
            j = int(j[0]) if hasattr(j, "__len__") else int(j)
            rows.append({"STR_CLS": r.STR_CLS, "d": p.distance(draft.geometry.iloc[j])})
    off = pd.DataFrame(rows)
    print(f"   {len(off):,} sample points at {SAMPLE_M:.0f} m spacing")
    q = off.d.quantile([0.5, 0.75, 0.9, 0.95, 0.99]).round(2)
    print(f"   offset draft-to-road, m:  median {q[0.5]}  p75 {q[0.75]}  "
          f"p90 {q[0.9]}  p95 {q[0.95]}  p99 {q[0.99]}  max {off.d.max():.1f}")
    for band in (2, 5, 10, 15, 20):
        print(f"      within {band:2d} m: {100*(off.d <= band).mean():5.1f} %")
    by = off.groupby("STR_CLS").d.agg(n="size", median="median",
                                      p90=lambda s: s.quantile(0.9),
                                      max="max").round(2)
    print("\n   by street class (01 = widest, 05 = local):")
    print(by.to_string())
    off.to_csv(os.path.join(OUT_RUN, "r2_offsets.csv"), index=False)

    # ------------------------------------------------------------ 2  connectivity
    print("\nconnectivity of the noded corridor network")
    nod = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors_noded.shp"))
    tot = nod.LEN_M.sum() / 1000
    byp = nod.groupby("PART").LEN_M.sum().sort_values(ascending=False) / 1000
    print(f"   {len(nod):,} noded lines, {tot:,.1f} km in {len(byp):,} pieces; "
          f"largest {byp.iloc[0]:,.1f} km ({100*byp.iloc[0]/tot:.1f} %)")
    print(f"   pieces under 0.5 km: {(byp < 0.5).sum():,} holding "
          f"{byp[byp < 0.5].sum():.2f} km")

    # ------------------------------------------------------------ 3  pipe by source
    print("\nattributing pipe to the corridor source it was laid in")
    q = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridor_quality.shp"))
    pipes = gpd.read_file(os.path.join(C.OUT_SHP, "W10_pipes.shp"))
    pipes = pipes.explode(index_parts=False)
    pipes = pipes[pipes.geometry.geom_type == "LineString"].reset_index(drop=True)
    ctree = STRtree(list(q.geometry))
    src, dist = [], []
    for g in pipes.geometry:
        p = g.interpolate(0.5, normalized=True)
        j = ctree.query_nearest(p)
        j = int(j[0]) if hasattr(j, "__len__") else int(j)
        src.append(q.SRC.iloc[j])
        dist.append(p.distance(q.geometry.iloc[j]))
    pipes["SRC"] = src
    pipes["D_CORR"] = np.round(dist, 2)
    pipes["LEN_M"] = pipes.length
    far = pipes.D_CORR > 5
    print(f"   {far.sum():,} reaches ({pipes.loc[far,'LEN_M'].sum()/1000:.1f} km) "
          f"further than 5 m from any corridor - these are the trunk, which is a "
          f"separate input")
    pipes.loc[far, "SRC"] = "trunk/other"
    tab = pipes.groupby("SRC").LEN_M.agg(reaches="size",
                                         km=lambda s: round(s.sum() / 1000, 1))
    tab["pct_of_pipe"] = (100 * tab.km / tab.km.sum()).round(1)
    corr_km = q.groupby("SRC").LEN_M.sum() / 1000
    tab["corridor_km"] = corr_km.reindex(tab.index).round(1)
    tab["used_pct"] = (100 * tab.km / tab.corridor_km).round(1)
    print(tab.to_string())
    tab.to_csv(os.path.join(OUT_RUN, "r2_pipe_by_source.csv"))
    pipes[["SRC", "D_CORR", "DN", "LEN_M", "QADF_M3D", "geometry"]].to_file(
        os.path.join(C.OUT_SHP, "W10_pipes_bysource.shp"))
    print(f"\ntotal {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
