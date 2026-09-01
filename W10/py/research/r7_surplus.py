"""How much pipe serves nothing? Measured without relying on the load allocation.

r5 found 311.8 km of pipe with no load anywhere upstream of it. Checking that figure
against the cadastre showed it cannot be taken at face value: 48 % of it passes within 30 m
of a plot that DOES carry load. The cause is the allocation, not the pipe. Loads land on
the nearest corridor NODE within 160 m and nodes sit about 100 m apart, so a reach can show
zero accumulated flow at its upstream end while houses along it drained into the node at
the other end. The number is an upper bound, not a measurement.

This measures the same thing without the flow tree in the way: a reach is SURPLUS when no
load-bearing plot lies within a frontage distance of it. That is a statement about the pipe
and the cadastre only. The frontage distance is swept rather than picked, because the
answer moves with it and the reader should see by how much.

Two supporting cuts, because "serves nothing" is only interesting if you can say where it
came from and what it costs:
  * the corridor source of every surplus reach - which ties this back to Part A
  * the depth breaches and lift that sit on surplus pipe

Run:  python r7_surplus.py
"""
import os
import sys
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")
OUT_RUN = os.path.join(C.OUT, "run")
BANDS = (30.0, 45.0, 60.0, 80.0, 100.0)
HEADLINE = 60.0          # the project's own frontage distance (config.PLOT_SERVED_M)


def main():
    pipes = gpd.read_file(os.path.join(C.OUT_SHP, "W10_pipes.shp"))
    pipes = pipes.explode(index_parts=False).reset_index(drop=True)
    pipes = pipes[pipes.geometry.geom_type == "LineString"].reset_index(drop=True)
    pipes["LEN_M"] = pipes.length
    total = pipes.LEN_M.sum() / 1000
    print(f"pipe: {len(pipes):,} reaches, {total:,.1f} km")

    pl = gpd.read_file(os.path.join(C.OUT_SHP, "W10_plot_loads.gpkg"),
                       layer="plot_loads")
    load = pl[pl.Q_AVG_M3D > 0].reset_index(drop=True)
    print(f"load-bearing plots: {len(load):,} of {len(pl):,} "
          f"({load.Q_AVG_M3D.sum():,.0f} m3/d)")

    tree = STRtree(list(load.geometry))
    d = np.empty(len(pipes))
    for i, g in enumerate(pipes.geometry):
        j = tree.query_nearest(g)
        j = int(j[0]) if hasattr(j, "__len__") else int(j)
        d[i] = g.distance(load.geometry.iloc[j])
    pipes["D_LOAD"] = np.round(d, 1)

    print(f"\nsurplus pipe = no load-bearing plot within the frontage distance:")
    rows = []
    for b in BANDS:
        m = pipes.D_LOAD > b
        km = pipes.loc[m, "LEN_M"].sum() / 1000
        rows.append({"frontage_m": b, "surplus_reaches": int(m.sum()),
                     "surplus_km": round(km, 1),
                     "pct_of_pipe": round(100 * km / total, 1)})
        print(f"   frontage {b:5.0f} m: {int(m.sum()):6,d} reaches, {km:7.1f} km "
              f"({100*km/total:4.1f} % of the network)")
    pd.DataFrame(rows).to_csv(os.path.join(OUT_RUN, "r7_surplus_sweep.csv"),
                              index=False)

    # ---- source, and what the surplus costs in pumping ---------------------
    cq = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridor_quality.shp"))
    ct = STRtree(list(cq.geometry))
    src, dsrc = [], []
    for g in pipes.geometry:
        p = g.interpolate(0.5, normalized=True)
        j = ct.query_nearest(p)
        j = int(j[0]) if hasattr(j, "__len__") else int(j)
        src.append(cq.SRC.iloc[j])
        dsrc.append(p.distance(cq.geometry.iloc[j]))
    pipes["SRC"] = np.where(np.array(dsrc) > 5, "trunk/other", src)
    pipes["SURPLUS"] = (pipes.D_LOAD > HEADLINE).astype(int)

    print(f"\nat the project's own {HEADLINE:.0f} m frontage distance, by corridor source:")
    t = pipes.groupby("SRC").agg(
        km=("LEN_M", lambda s: round(s.sum() / 1000, 1)),
        surplus_km=("LEN_M", lambda s: 0.0))
    t["surplus_km"] = (pipes[pipes.SURPLUS == 1].groupby("SRC").LEN_M.sum() / 1000
                       ).reindex(t.index).fillna(0).round(1)
    t["surplus_pct"] = (100 * t.surplus_km / t.km).round(1)
    t["share_of_surplus"] = (100 * t.surplus_km / t.surplus_km.sum()).round(1)
    print(t.to_string())
    t.to_csv(os.path.join(OUT_RUN, "r7_surplus_by_source.csv"))

    lifts = gpd.read_file(os.path.join(C.OUT_SHP, "W10_lift_sized.shp"))
    sp = pipes[pipes.SURPLUS == 1]
    stree = STRtree(list(sp.geometry))
    on = 0
    lift_on = 0.0
    for _, r in lifts.iterrows():
        j = stree.query_nearest(r.geometry)
        j = int(j[0]) if hasattr(j, "__len__") else int(j)
        if r.geometry.distance(sp.geometry.iloc[j]) < 25:
            on += 1
            lift_on += float(r.LIFT_M)
    print(f"\ndepth breaches sitting on surplus pipe: {on} of {len(lifts)}, "
          f"{lift_on:,.0f} m of lift of {lifts.LIFT_M.sum():,.0f} "
          f"({100*lift_on/lifts.LIFT_M.sum():.1f} %)")

    pipes[["SRC", "DN", "LEN_M", "QADF_M3D", "D_LOAD", "SURPLUS", "geometry"]].to_file(
        os.path.join(C.OUT_SHP, "W10_pipe_surplus.shp"))
    print(f"\nwrote W10_pipe_surplus.shp "
          f"({int(pipes.SURPLUS.sum()):,} reaches flagged SURPLUS=1)")


if __name__ == "__main__":
    main()
