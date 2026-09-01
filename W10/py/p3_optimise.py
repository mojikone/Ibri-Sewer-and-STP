"""Phase 3 optimisation - WITHDRAWN. The method this script implements is PROHIBITED.

    PAM-GUD-203 p29, section 4.3.1, verbatim:
        "Sewers shall not be oversized to facilitate flatter slopes.
         Uniform slopes must be maintained between successive manholes."

That is one unqualified sentence, "shall not", with no exception anywhere in the 201
pages. This script upsizes pipes for the express purpose of laying them flatter, which is
precisely the forbidden move. It is kept, not deleted, because the measurement it produced
is worth having and because a deleted mistake teaches nobody.

The guideline gives its reason on p167, listing the causes of hydrogen sulphide:
"a. Oversized lateral sewers and mains resulting in low sewage velocity in sewers causing
solids deposition and long retention times, promoting anaerobic conditions" - and p185
adds that "Gravity sewers with very low slopes are the ones with the greatest risk of H2S
formation". Upsizing to flatten triggers both at once, on long runs, at Omani temperatures.

Worse, the project already knew. TUTORIALS/T02 section 6.3 carries the p29 prohibition and
states the consequence plainly: "the design has no choice but to accept the depth, and pump
when the depth runs out." This was written without reading it.

The prohibition is on PURPOSE, not on size. A pipe may legitimately be large because the
d/D cap, the 3 m/s limit or the ultimate-flow horizon requires it, and the flatter Table 11
minimum then follows as a consequence. Choosing the diameter FROM the gradient you want is
what is forbidden. The audit question is "what set this diameter?" - and "the depth we
wanted" fails it.

WHAT IT MEASURED, for the record: 219 breaches to 184, total lift 2,815 m to 2,327 m, at a
cost of 291 km of pipe above DN200. It did not reduce the station count - that went UP,
21 to 25, because removing breaches from the middle of a cluster splits it in two.

The live optimisation study is `p3_variants.py` and `W10/docs/OPTIMISATION.md`.
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
from p2_depths import MIN_COVER_CROWN, MAX_DEPTH
from p2_sizing import assign_loads, accumulate
from sewnet import hydra
from sewnet.criteria import DEFAULT as CRIT

warnings.filterwarnings("ignore")

OD_ALLOW = 0.10          # m over nominal bore, for cover
MAX_PASSES = 8
EPS = 1e-4


def od(dn):
    return dn / 1000.0 + OD_ALLOW


def flattest_for(q_peak, dn_cap=1200):
    """The flattest gradient this flow can be laid at, and the diameter that delivers it.

    Bounded below by the tractive-force minimum, which no diameter can beat.
    """
    floor = hydra.smin_tractive(q_peak, CRIT)
    best = (None, None)
    for dn in CRIT.DN_SERIES:
        if dn > dn_cap:
            break
        y, v = hydra.pipe_state(dn, max(CRIT.TABLE11.get(dn, CRIT.TABLE11_FLOOR), floor),
                                q_peak, CRIT)
        if y is None or y > hydra.dod_limit(dn, CRIT):
            continue                                  # cannot carry it
        s = max(CRIT.TABLE11.get(dn, CRIT.TABLE11_FLOOR), floor)
        if best[1] is None or s < best[1] - EPS:
            best = (dn, s)
    return best


def size_network(G, nxt, qacc, lacc, dn_floor=None):
    """Diameter and gradient for every pipe. `dn_floor` forces a minimum diameter."""
    dn_floor = dn_floor or {}
    hold = CRIT.PF_HOLD_PROPERTIES * CRIT.PLOT_QADF_M3D / 1000.0
    out = {}
    for n, m in nxt.items():
        if not G.has_edge(n, m):
            continue
        qadf = qacc[n] + CRIT.INFILT_L_D_KM * (lacc[n] / 1000.0) / 1000.0
        pf = CRIT.pf_merrimack(max(qadf / 1000.0, hold))
        qpk = qadf * pf / 86400.0
        floor_dn = dn_floor.get((n, m), 0)
        dn = CRIT.DN_SERIES[0]
        for _ in range(6):
            s = hydra.smin_for(dn, qpk, CRIT)
            dn2, y, v = hydra.size_pipe(qpk, s, CRIT)
            if dn2 is None:
                dn = CRIT.DN_SERIES[-1]
                break
            if dn2 == dn:
                break
            dn = dn2
        if floor_dn > dn:
            dn = floor_dn
        s = max(CRIT.TABLE11.get(dn, CRIT.TABLE11_FLOOR), hydra.smin_tractive(qpk, CRIT))
        out[(n, m)] = {"DN": dn, "S": s, "QADF": qadf, "PF": pf, "QPK": qpk}
    return out


def lay(G, z, nxt, order, pipes):
    """Invert, depth, breaches - laid as shallow as the cover rule allows."""
    ups = defaultdict(list)
    for n, m in nxt.items():
        ups[m].append(n)
    # `predepth` is the depth BEFORE the station resets it. The depth recorded after a
    # reset is just the cover, about 2.4 m, so relieving a breach against that number gives
    # a negative excess and nothing is ever upsized - which is exactly what the first run
    # of this optimiser did.
    invert, lifts, at_cover, predepth = {}, {}, set(), {}
    for n in order:
        zn = z.get(n, np.nan)
        if not np.isfinite(zn):
            continue
        dn_here = max([pipes[(u, n)]["DN"] for u in ups.get(n, ()) if (u, n) in pipes]
                      + [pipes[(n, nxt[n])]["DN"]] if n in nxt and (n, nxt[n]) in pipes
                      else [200])
        shallow = zn - MIN_COVER_CROWN - od(dn_here)
        cand = [shallow]
        for u in ups.get(n, ()):
            p = pipes.get((u, n))
            if u in invert and p is not None and G.has_edge(u, n):
                cand.append(invert[u] - p["S"] * G[u][n]["len"])
        iv = min(cand)
        if iv >= shallow - EPS:
            at_cover.add(n)
        predepth[n] = zn - iv
        if zn - iv > MAX_DEPTH:
            lifts[n] = (zn - iv) - (zn - shallow)
            iv = shallow
            at_cover.add(n)
        invert[n] = iv
    depth = {n: z[n] - invert[n] for n in invert if np.isfinite(z.get(n, np.nan))}
    return invert, depth, lifts, at_cover, predepth


def controlling_run(G, nxt, invert, at_cover, node, ups):
    """The stretch that dug the hole: upstream from `node` to the last point at cover.

    Follows the deepest incoming branch at each step, because that is the one that set the
    invert here.
    """
    run, n, L = [], node, 0.0
    for _ in range(4000):
        best, bd = None, None
        for u in ups.get(n, ()):
            if u not in invert or not G.has_edge(u, n):
                continue
            if bd is None or invert[u] < bd:
                best, bd = u, invert[u]
        if best is None:
            break
        run.append((best, n))
        L += G[best][n]["len"]
        n = best
        if n in at_cover:
            break
    return run, L


def main():
    t0 = time.time()
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    cost, nxt, D = flow_tree(G, z, sink)
    q_node, _, _ = assign_loads(xy, list(G.nodes))
    qacc, lacc, order = accumulate(G, nxt, q_node)
    ups = defaultdict(list)
    for n, m in nxt.items():
        ups[m].append(n)

    q50 = 50 * 1.456 * 5.32 * 164.0 * 0.85 / 1000.0
    dn_floor, history = {}, []

    for p in range(MAX_PASSES):
        pipes = size_network(G, nxt, qacc, lacc, dn_floor)
        invert, depth, lifts, at_cover, predepth = lay(G, z, nxt, order, pipes)
        real = [n for n in lifts
                if qacc[n] + CRIT.INFILT_L_D_KM * (lacc[n] / 1000.0) / 1000.0 >= q50]
        km = sum(G[n][m]["len"] for n, m in pipes) / 1000
        upkm = sum(G[n][m]["len"] for (n, m), d in pipes.items()
                   if d["DN"] > 200) / 1000
        history.append({"pass": p, "breaches": len(lifts), "real_stations": len(real),
                        "km_over_DN200": round(upkm, 1),
                        "total_lift_m": round(sum(lifts.values()), 0)})
        print(f"pass {p}: {len(lifts):4d} breaches, {len(real):3d} real stations, "
              f"{upkm:7.1f} km above DN200, lift {sum(lifts.values()):8,.0f} m")
        if not lifts:
            break

        # ---- relieve every breach we can ----------------------------------
        changed = 0
        irreducible = 0
        for n in list(lifts):
            excess = predepth[n] - MAX_DEPTH
            if excess <= 0:
                continue
            run, L = controlling_run(G, nxt, invert, at_cover, n, ups)
            if L < 1.0 or not run:
                irreducible += 1
                continue
            for (u, v) in run:
                pp = pipes.get((u, v))
                if pp is None:
                    continue
                need = pp["S"] - excess / L
                dn_best, s_best = flattest_for(pp["QPK"])
                if dn_best is None:
                    continue
                # the smallest diameter that gets to `need`, else the flattest available
                pick = None
                for dn in CRIT.DN_SERIES:
                    s = max(CRIT.TABLE11.get(dn, CRIT.TABLE11_FLOOR),
                            hydra.smin_tractive(pp["QPK"], CRIT))
                    y, v_ = hydra.pipe_state(dn, s, pp["QPK"], CRIT)
                    if y is None or y > hydra.dod_limit(dn, CRIT):
                        continue
                    if s <= need + EPS:
                        pick = dn
                        break
                if pick is None:
                    pick = dn_best
                if pick > dn_floor.get((u, v), 0) and pick > pp["DN"]:
                    dn_floor[(u, v)] = pick
                    changed += 1
        print(f"          upsized {changed:,} reaches, {irreducible} breaches with no run "
              f"to relieve")
        if changed == 0:
            break

    # ---------------------------------------------------------------- outputs
    pipes = size_network(G, nxt, qacc, lacc, dn_floor)
    invert, depth, lifts, at_cover, predepth = lay(G, z, nxt, order, pipes)
    real = [n for n in lifts
            if qacc[n] + CRIT.INFILT_L_D_KM * (lacc[n] / 1000.0) / 1000.0 >= q50]
    dd = np.array(list(depth.values()))
    kms = defaultdict(float)
    for (n, m), d in pipes.items():
        kms[d["DN"]] += G[n][m]["len"] / 1000

    print(f"\nOPTIMISED: {len(lifts):,} breaches, {len(real)} real stations, "
          f"deepest {dd.max():.2f} m, median cover {np.median(dd):.2f} m")
    print("\n   DN        km")
    for dn in sorted(kms):
        print(f"   {dn:5d} {kms[dn]:9.1f}")

    rows = [{"DN": d["DN"], "SLOPE_PCT": round(100 * d["S"], 4),
             "QADF_M3D": round(d["QADF"], 2), "QPK_LS": round(d["QPK"] * 1000, 2),
             "LEN_M": round(G[n][m]["len"], 2),
             "US_DEPTH": round(float(depth.get(n, 0)), 2),
             "DS_DEPTH": round(float(depth.get(m, 0)), 2),
             "geometry": lines[G[n][m]["line"]]}
            for (n, m), d in pipes.items()]
    gpd.GeoDataFrame(rows, crs=C.EPSG).to_file(
        os.path.join(C.OUT_SHP, "W10_pipes_opt.shp"))
    if lifts:
        gpd.GeoDataFrame(
            [{"LIFT_M": round(v, 2), "GROUND": round(float(z[n]), 2),
              "QADF_M3D": round(qacc[n] + CRIT.INFILT_L_D_KM * (lacc[n]/1000.0)/1000.0, 1),
              "REAL": int(n in real), "geometry": Point(xy[n])}
             for n, v in lifts.items()], crs=C.EPSG).to_file(
            os.path.join(C.OUT_SHP, "W10_lift_opt.shp"))
    pd.DataFrame(history).to_csv(os.path.join(C.OUT_RUN, "p3_optimise_passes.csv"),
                                 index=False)
    pd.DataFrame([{"dn": dn, "km": round(kms[dn], 2)} for dn in sorted(kms)]).to_csv(
        os.path.join(C.OUT_RUN, "p3_optimise_diameters.csv"), index=False)
    print(f"\ntotal {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
