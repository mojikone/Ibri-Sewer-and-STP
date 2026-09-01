"""Phase 3 - every strategy for reducing the station count, measured the same way.

Comparing station counts between runs turned out to be a trap. The upsize-to-flatten pass
cut breaches from 220 to 184 and then produced MORE consolidated stations, 38 against 33,
because removing breaches breaks up clusters that were previously merging. Fewer breaches
is not automatically fewer stations, so every variant here is measured through one
identical funnel:

    breaches -> consolidate within 1.5 km (rule 9) -> keep those whose CATCHMENT is 50
    properties or more (54 m3/d on the locked basis) -> that is the station count

and the cost of each strategy is reported beside it, because a station removed by laying
300 km of larger pipe is not free.

STRATEGIES
  base        smallest diameter that carries the flow, at its own Table 11 minimum
  flatten     upsize a run that is digging itself in, so it can be laid flatter
  climb-N     re-route: sweep the penalty charged per metre climbed in the flow direction
  avoid       re-route around the nodes that breached in the previous solve, the way W8
              did when it went from 6 stations to 3
  combined    the best routing found, then flatten on top of it

Run:  python p3_variants.py
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
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "W8", "py"))

import config as C
import netlib as N
from p1_subnetworks import flow_tree
from p2_depths import MIN_COVER_CROWN, MAX_DEPTH
from p2_sizing import assign_loads, accumulate
from p3_optimise import size_network, lay, controlling_run, flattest_for, od, EPS
from sewnet import hydra
from sewnet.criteria import DEFAULT as CRIT

warnings.filterwarnings("ignore")

Q50 = 50 * 1.456 * 5.32 * 164.0 * 0.85 / 1000.0     # 50 properties = 54 m3/d
CONSOLIDATE_M = 1500.0
CLIMB_PENALTIES = (100.0, 400.0, 1000.0, 2500.0, 6000.0)


def stations(lifts, qacc, lacc, xy):
    """The one funnel: breaches -> consolidate at 1.5 km -> keep real catchments."""
    if not lifts:
        return 0, 0, 0.0
    g = gpd.GeoDataFrame(
        [{"Q": qacc[n] + CRIT.INFILT_L_D_KM * (lacc[n] / 1000.0) / 1000.0,
          "L": v, "geometry": Point(xy[n])} for n, v in lifts.items()], crs=C.EPSG)
    b = gpd.GeoDataFrame(geometry=[unary_union(g.geometry.buffer(CONSOLIDATE_M / 2))],
                         crs=C.EPSG).explode(index_parts=False).reset_index(drop=True)
    real = sum(1 for x in b.geometry if float(g[g.intersects(x)].Q.max()) >= Q50)
    return len(b), real, float(g.L.sum())


def flatten_pass(G, z, nxt, order, qacc, lacc, ups, passes=8):
    """Iterate the upsize-to-flatten relief until it stops improving."""
    dn_floor = {}
    for _ in range(passes):
        pipes = size_network(G, nxt, qacc, lacc, dn_floor)
        invert, depth, lifts, at_cover, predepth = lay(G, z, nxt, order, pipes)
        if not lifts:
            break
        changed = 0
        for n in list(lifts):
            excess = predepth[n] - MAX_DEPTH
            if excess <= 0:
                continue
            run, L = controlling_run(G, nxt, invert, at_cover, n, ups)
            if L < 1.0:
                continue
            for (u, v) in run:
                pp = pipes.get((u, v))
                if pp is None:
                    continue
                need = pp["S"] - excess / L
                pick = None
                for dn in CRIT.DN_SERIES:
                    s = max(CRIT.TABLE11.get(dn, CRIT.TABLE11_FLOOR),
                            hydra.smin_tractive(pp["QPK"], CRIT))
                    y, _v = hydra.pipe_state(dn, s, pp["QPK"], CRIT)
                    if y is None or y > hydra.dod_limit(dn, CRIT):
                        continue
                    if s <= need + EPS:
                        pick = dn
                        break
                if pick is None:
                    pick = flattest_for(pp["QPK"])[0]
                if pick and pick > dn_floor.get((u, v), 0) and pick > pp["DN"]:
                    dn_floor[(u, v)] = pick
                    changed += 1
        if changed == 0:
            break
    return dn_floor


def evaluate(G, z, xy, nxt, order, qacc, lacc, dn_floor=None):
    pipes = size_network(G, nxt, qacc, lacc, dn_floor or {})
    invert, depth, lifts, at_cover, predepth = lay(G, z, nxt, order, pipes)
    clusters, real, lift = stations(lifts, qacc, lacc, xy)
    km = sum(G[n][m]["len"] for n, m in pipes) / 1000
    up = sum(G[n][m]["len"] for (n, m), d in pipes.items() if d["DN"] > 200) / 1000
    dd = np.array(list(depth.values()))
    return {"breaches": len(lifts), "clusters": clusters, "stations": real,
            "lift_m": round(lift), "pipe_km": round(km, 1),
            "km_over_DN200": round(up, 1), "deepest": round(float(dd.max()), 2)}, \
        pipes, lifts, depth


def main():
    t0 = time.time()
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    q_node, _, _ = assign_loads(xy, list(G.nodes))
    rows = []

    def run(tag, penalty=N.CLIMB_PENALTY, avoid=None, flatten=False):
        Gx = G
        if avoid:
            # charge heavily for passing through a node that breached last time, so the
            # router looks for another way before the depth solver has to dig
            Gx = G.copy()
            for u, v, d in Gx.edges(data=True):
                if u in avoid or v in avoid:
                    d["len"] = d["len"] + 3000.0
        cost, nxt, _ = flow_tree(Gx, z, sink, penalty=penalty)
        if avoid:                       # restore true lengths for the hydraulics
            for u, v, d in Gx.edges(data=True):
                if u in avoid or v in avoid:
                    d["len"] = d["len"] - 3000.0
        qacc, lacc, order = accumulate(Gx, nxt, q_node)
        ups = defaultdict(list)
        for n, m in nxt.items():
            ups[m].append(n)
        dn_floor = flatten_pass(Gx, z, nxt, order, qacc, lacc, ups) if flatten else None
        r, pipes, lifts, depth = evaluate(Gx, z, xy, nxt, order, qacc, lacc, dn_floor)
        r["strategy"] = tag
        rows.append(r)
        print(f"{tag:<28s} breaches {r['breaches']:4d}  clusters {r['clusters']:3d}  "
              f"STATIONS {r['stations']:3d}  lift {r['lift_m']:6,d} m  "
              f"pipe {r['pipe_km']:7.1f} km  >DN200 {r['km_over_DN200']:6.1f} km")
        return nxt, lifts, dn_floor

    print("routing and sizing strategies, all measured through the same funnel\n")
    nxt0, lifts0, _ = run("base")
    run("flatten", flatten=True)
    best_pen, best_st = N.CLIMB_PENALTY, None
    for p in CLIMB_PENALTIES:
        _, lf, _ = run(f"climb-{p:.0f}", penalty=p)
        st = rows[-1]["stations"]
        if best_st is None or st < best_st:
            best_pen, best_st = p, st
    run("avoid (1 round)", avoid=set(lifts0))
    _, lf2, _ = run(f"climb-{best_pen:.0f} + avoid", penalty=best_pen, avoid=set(lifts0))
    run(f"climb-{best_pen:.0f} + avoid + flatten", penalty=best_pen,
        avoid=set(lifts0), flatten=True)

    df = pd.DataFrame(rows)[["strategy", "breaches", "clusters", "stations", "lift_m",
                             "pipe_km", "km_over_DN200", "deepest"]]
    print(f"\n{df.to_string(index=False)}")
    df.to_csv(os.path.join(C.OUT_RUN, "p3_variants.csv"), index=False)
    print(f"\ntotal {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
