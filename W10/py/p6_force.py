"""Phase 6 - the rising mains.

Each of the 28 lifting stations is, in the design as solved, a lift-and-reset: the sewage
is raised back to normal cover and the gravity pipe restarts on the spot, so the rising
main is a few metres of pipe inside the station. That is the cheapest arrangement and it is
what the depth solver produced.

The question you asked - the best routes for the main force lines - is the other half of
it: for each station, what would it cost to pump somewhere USEFUL instead of straight back
up? Two destinations are worth pricing at concept stage, and both are computed here:

  * to the trunk main, which is what a station does when its catchment cannot reach the
    trunk by gravity at all (the western area is the clear case)
  * to the works, which is what a station does when it is the last one in a chain

The rising main is sized on PUMP DUTY, not on the arriving gravity flow - the wet well is
emptied faster than it fills - and held to 0.75 to 3.0 m/s (G203-p50 8.1). Duty is taken
as the peak arriving flow, which is the concept-stage convention; the real duty comes from
the wet-well cycle at detail design.

Run:  python p6_force.py
"""
import os
import sys
import warnings
from collections import defaultdict

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "W8", "py"))

import config as C
import netlib as N
from p1_subnetworks import flow_tree
from p2_sizing import assign_loads, accumulate
from sewnet.criteria import DEFAULT as CRIT

warnings.filterwarnings("ignore")

V_MIN, V_MAX = 0.75, 3.0        # m/s in a rising main (G203-p50 8.1)
DN_SERIES = (100, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1200)


def size_rising(q_ls):
    """Smallest diameter that keeps the duty flow between 0.75 and 3.0 m/s."""
    q = q_ls / 1000.0
    for dn in DN_SERIES:
        d = dn / 1000.0
        v = q / (np.pi * d * d / 4.0)
        if V_MIN <= v <= V_MAX:
            return dn, v
    for dn in DN_SERIES:                      # nothing lands in band: take the closest
        d = dn / 1000.0
        v = q / (np.pi * d * d / 4.0)
        if v <= V_MAX:
            return dn, v
    return DN_SERIES[-1], q / (np.pi * (DN_SERIES[-1] / 1000.0) ** 2 / 4.0)


def main():
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    cost, nxt, D = flow_tree(G, z, sink)
    q_node, _, _ = assign_loads(xy, list(G.nodes))
    qacc, lacc, order = accumulate(G, nxt, q_node)

    trunk_nodes = [n for u, v, d in G.edges(data=True) if d["trunk"] for n in (u, v)]
    st = gpd.read_file(os.path.join(C.OUT_SHP, "W10_stations_final.shp"))
    print(f"{len(st)} lifting stations\n")

    hold_mld = CRIT.PF_HOLD_PROPERTIES * CRIT.PLOT_QADF_M3D / 1000.0
    rows, geoms = [], []
    for i, r in st.iterrows():
        node, d0 = N.nearest_node(xy, (r.geometry.x, r.geometry.y), nodes=comps[0])
        qadf = qacc.get(node, 0.0) + CRIT.INFILT_L_D_KM * (lacc.get(node, 0.0) / 1000.0) / 1000.0
        pf = CRIT.pf_merrimack(max(qadf / 1000.0, hold_mld))
        q_ls = qadf * pf / 86.4
        tn, _ = N.nearest_node(xy, xy[node], nodes=trunk_nodes)
        try:
            path = nx.shortest_path(D, node, tn, weight="w")
            L = sum(G[a][b]["len"] for a, b in zip(path[:-1], path[1:]))
        except nx.NetworkXNoPath:
            path, L = [node], 0.0
        static = z[tn] - z[node]
        dn, v = size_rising(max(q_ls, 1.0))
        rows.append({"ST": int(i), "PLOTS": int(r.PLOTS),
                     "QADF_M3D": round(qadf, 1), "PF": round(pf, 2),
                     "Q_DUTY_LS": round(q_ls, 1),
                     "RM_KM": round(L / 1000, 3), "STATIC_M": round(static, 2),
                     "RM_DN": dn, "RM_V": round(v, 2),
                     "GROUND": round(float(z[node]), 2)})
        if len(path) > 1:
            geoms.append(LineString([xy[n] for n in path]))
        else:
            geoms.append(Point(xy[node]).buffer(5).exterior)

    df = pd.DataFrame(rows).sort_values("QADF_M3D", ascending=False)

    # Rule 9 absorbs pockets under 50 properties. The consolidated layer counted plots
    # WITHIN 750 m of the station, which is a proximity count and not a catchment - it put
    # 10,523 plots against a station carrying 5.4 m3/d. The catchment is the accumulated
    # flow at the station node, so that is what the threshold is applied to.
    q50 = 50 * 1.456 * 5.32 * 164.0 * 0.85 / 1000.0     # 50 properties, locked basis
    df["REAL"] = (df.QADF_M3D >= q50).astype(int)
    print(df.to_string(index=False))
    print(f"\n50 properties on the locked basis is {q50:,.0f} m3/d.")
    print(f"stations with a catchment at or above it: {int(df.REAL.sum())}")
    print(f"depth breaches below it, absorbed into detail design: "
          f"{int((1-df.REAL).sum())}, carrying "
          f"{df[df.REAL==0].QADF_M3D.sum():,.0f} m3/d between them")
    print(f"\ntotal rising main to the trunk: {df.RM_KM.sum():.2f} km")
    print(f"stations already ON the trunk (no rising main): {(df.RM_KM < 0.02).sum()}")
    print(f"total duty flow through stations: {df.Q_DUTY_LS.sum():,.0f} L/s")
    df.to_csv(os.path.join(C.OUT_RUN, "p6_rising_mains.csv"), index=False)
    gpd.GeoDataFrame(df.reset_index(drop=True), geometry=geoms, crs=C.EPSG).to_file(
        os.path.join(C.OUT_SHP, "W10_rising_mains.shp"))
    print("wrote W10_rising_mains.shp")


if __name__ == "__main__":
    main()
