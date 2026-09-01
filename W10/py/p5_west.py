"""Phase 5 - the western leg, decided on corridors rather than on straight lines.

Phase 0.4 established the problem on the terrain model: the western leg of the given main
pipe is a separate 7.86 km component whose outlet invert sits ABOVE every invert on the
main trunk except at the works itself. Straight-line routes then suggested the southern
works site solved it by gravity and the existing works did not.

Straight lines are not routes. On the corridor network the same journeys are much longer -
13.2 km to the existing works against 6.2 km as the crow flies, 16.9 km to the southern
site against 10.1 km - and a longer route at the same fall is a flatter one.

Two corrections to the first attempt at this script, both worth recording:

  * The gradient must be SOLVED, not assumed. Laying the west at an assumed 0.30 % over
    13 km consumes 39.7 m of fall where the ground gives 4.2 m, so the pipe simply digs
    itself 37 m into the ground. That is not a finding about the route, it is arithmetic
    about the assumption. What matters is the gradient the route can actually support and
    whether that gradient still scours.
  * The west leg is part of the given main pipe, so it is tagged as trunk in the merged
    graph. "Pump to the nearest trunk node" therefore returned the west leg itself, zero
    metres away. The target has to be the MAIN body of the trunk, excluding the west
    component.

Options:
  A  gravity to the west's own low point, then pump into the main trunk
  B  gravity all the way to the existing works
  C  gravity all the way to the proposed southern works
  D  a local satellite works serving the west alone

Run:  python p5_west.py
"""
import os
import sys
import warnings

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C
import netlib as N
from p2_depths import MIN_COVER_CROWN, MAX_DEPTH, OD_DEFAULT

warnings.filterwarnings("ignore")

WEST_LOW = (442091.75, 2569063.87)     # the west leg's own low point, ground 332.36 m
MANNING_N = 0.013
V_MIN = 0.75                           # m/s self-cleansing (G203-p26-27)
DN_TEST = (400, 600, 800, 1000, 1200)


def velocity_full(dn_mm, slope, n=MANNING_N):
    """Manning velocity running full. R = D/4 for a full circular pipe."""
    d = dn_mm / 1000.0
    return (1.0 / n) * (d / 4.0) ** (2.0 / 3.0) * slope ** 0.5


def lay_route(G, xy, z, path, slope):
    """Lay one route at a fixed gradient and report the deepest point."""
    inv = z[path[0]] - MIN_COVER_CROWN - OD_DEFAULT
    deepest, breaches = 0.0, 0
    for a, b in zip(path[:-1], path[1:]):
        inv = min(inv - slope * G[a][b]["len"], z[b] - MIN_COVER_CROWN - OD_DEFAULT)
        dep = z[b] - inv
        deepest = max(deepest, dep)
        breaches += dep > MAX_DEPTH
    return deepest, breaches


def best_gradient(G, xy, z, path, lo=0.00005, hi=0.006, tol=1e-6):
    """The steepest gradient this route can be laid at without passing 12 m.

    Steeper is better - it is what makes the pipe scour - so the binary search looks for
    the most the route will take rather than the least it needs.
    """
    if lay_route(G, xy, z, path, lo)[1] > 0:
        return 0.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if lay_route(G, xy, z, path, mid)[1] == 0:
            lo = mid
        else:
            hi = mid
    return lo


def main():
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    D = N.sewer_cost(G, z)

    west, dw = N.nearest_node(xy, WEST_LOW, nodes=comps[0])
    works, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    south, ds = N.nearest_node(xy, C.STP_PROPOSED_SOUTH, nodes=comps[0])
    print(f"west low point : ground {z[west]:.2f} m")
    print(f"existing works : ground {z[works]:.2f} m")
    print(f"southern site  : ground {z[south]:.2f} m (nearest node {ds:.0f} m off)")

    # trunk nodes on the MAIN body only - the west leg is itself trunk, so it has to go
    mp = gpd.read_file(C.MAIN_PIPE).to_crs(C.EPSG)
    mp_lines = [g for geom in mp.geometry
                for g in (geom.geoms if geom.geom_type == "MultiLineString" else [geom])]
    Gm = nx.Graph()
    for i, ln in enumerate(mp_lines):
        Gm.add_edge(tuple(np.round(ln.coords[0][:2], 2)),
                    tuple(np.round(ln.coords[-1][:2], 2)))
    mcomps = sorted(nx.connected_components(Gm), key=len, reverse=True)
    main_body = unary_union([ln for ln in mp_lines
                             if tuple(np.round(ln.coords[0][:2], 2)) in mcomps[0]])
    trunk_main = [n for u, v, d in G.edges(data=True) if d["trunk"]
                  for n in (u, v) if main_body.distance(Point(xy[n])) < 5.0]
    tn, dt = N.nearest_node(xy, xy[west], nodes=trunk_main)
    print(f"nearest node on the MAIN trunk body: {dt:,.0f} m away, "
          f"ground {z[tn]:.2f} m\n")

    rows = []
    for tag, dst in (("B  to the existing works", works),
                     ("C  to the southern site", south),
                     ("A  to the main trunk", tn)):
        try:
            path = nx.shortest_path(D, west, dst, weight="w")
        except nx.NetworkXNoPath:
            print(f"{tag}: no route")
            continue
        L = sum(G[a][b]["len"] for a, b in zip(path[:-1], path[1:]))
        fall = z[path[0]] - z[path[-1]]
        s = best_gradient(G, xy, z, path)
        deepest, _ = lay_route(G, xy, z, path, s)
        vs = {dn: velocity_full(dn, s) for dn in DN_TEST} if s > 0 else {}
        ok = [dn for dn, v in vs.items() if v >= V_MIN]
        print(f"{tag}: {L/1000:6.2f} km, ground falls {fall:6.2f} m "
              f"({100*fall/L:6.3f} %)")
        if s <= 0:
            print("      cannot be laid at any gradient inside 12 m")
            verdict = "impossible"
        else:
            print(f"      steepest gradient that stays inside 12 m: {100*s:.3f} % "
                  f"(deepest {deepest:.2f} m)")
            print("      full-bore velocity: " +
                  "  ".join(f"DN{dn} {v:.2f}" for dn, v in vs.items()))
            verdict = (f"scours at DN{min(ok)}+" if ok
                       else f"FAILS {V_MIN} m/s at every diameter")
            print(f"      -> {verdict}")
        rows.append({"option": tag, "km": round(L / 1000, 2),
                     "ground_fall_m": round(fall, 2),
                     "max_grad_pct": round(100 * s, 4),
                     "deepest_m": round(deepest, 2),
                     "min_dn_that_scours": (min(ok) if ok else None),
                     "verdict": verdict})
        gpd.GeoDataFrame({"OPTION": [tag]},
                         geometry=[LineString([xy[n] for n in path])],
                         crs=C.EPSG).to_file(
            os.path.join(C.OUT_SHP, f"W10_west_{tag.split()[0]}.shp"))

    # ---- why every option came back impossible ------------------------------
    # A route that cannot be laid at ANY gradient is not a gradient problem. It means the
    # ground itself rises above the pipe somewhere, and the height it rises is the lift
    # that has to be paid whatever else is decided.
    print("\nthe saddle each route has to cross:")
    saddles = {}
    for tag, dst in (("existing works", works), ("southern site", south),
                     ("main trunk", tn)):
        p = nx.shortest_path(D, west, dst, weight="w")
        zz = np.array([z[n] for n in p])
        ll = np.cumsum([0] + [G[a][b]["len"] for a, b in zip(p[:-1], p[1:])])
        k = int(np.argmax(zz))
        climb = float((np.maximum.accumulate(zz) - zz[0]).max())
        saddles[tag] = climb
        print(f"   towards the {tag:<15s} highest {zz.max():7.2f} m at ch "
              f"{ll[k]/1000:5.2f} km = {climb:5.2f} m above the start")
    if len(set(round(v, 2) for v in saddles.values())) == 1:
        print("   -> the SAME saddle on every route. The western area is a closed basin,")
        print("      and which works it is sent to cannot change that.")

    # what the west carries, and what a local works would serve
    seg = gpd.read_file(os.path.join(C.OUT_SHP, "W10_subnet_segments.shp"))
    plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
    win = Point(xy[west]).buffer(6000)
    print(f"\nwithin 6 km of the west low point: "
          f"{seg[seg.intersects(win)].LEN_M.sum()/1000:,.1f} km of corridor, "
          f"{int(plots.intersects(win).sum()):,} plots")
    static = z[tn] - z[west]
    print(f"D  a local satellite works avoids all of it")
    print(f"\nIf the west is pumped instead: static lift to the main trunk "
          f"{static:.2f} m over {dt/1000:.2f} km of rising main")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(C.OUT_RUN, "p5_west_options.csv"), index=False)
    print(f"\n{df.to_string(index=False)}")


if __name__ == "__main__":
    main()
