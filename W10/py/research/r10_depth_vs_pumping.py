"""When is a lifting station actually cheaper than a deeper trench?

G203-p33 4.6.3 says only this: "Where the cost of excavation becomes prohibitive the
Engineer shall incorporate pumping stations into the design." It names the decision and
gives no number. The 12.00 m limit the W10 pipeline enforces is therefore a placeholder,
and every station count the project has published rests on it.

WHAT THIS SCRIPT MEASURES. For each of the 239 breaches in the sized run it builds the
counterfactual the design never looked at: what happens downstream if NO station goes in.

    invert_noPS[m] = min( shipped_invert[m], invert_noPS[prev] - s x L )

That single line is exact, not an approximation. The shipped invert at m is already the
minimum over the shallow-cover cap and every upstream branch WITH the station at b in
place. Deleting the station only adds one deeper candidate - the continuation of b's own
branch - and min() is monotone, so taking the min of the two reproduces the full re-solve
along the path. Walking downstream until the two inverts coincide gives the exact extent
and the exact extra depth of the excursion, with no re-solve of the whole network.

The measured quantity is the EXCURSION DEPTH-METRE INTEGRAL

    DM = integral over the excursion of (depth_noPS - depth_withPS) dL      [m2]

which is the extra trench cross-section-length the deep option buys. Multiply by a
marginal excavation rate in OMR per metre of trench per metre of depth and you have the
cost of digging through. Compare against the life-cycle cost of the station. That is the
whole rule, and DM is the only part of it that is a measurement rather than an assumption.

COSTS ARE PROVISIONAL. Renardet's priced BoQs have not arrived (W9 financial review,
"Awaiting: real project cost data"). Every absolute figure here is a placeholder with a
stated source; the STRUCTURE is the deliverable. Three depth laws are carried side by
side because the literature does not agree on one:

    b = 1.0   Maurer, Wolfram & Herlyn (2010), as coded by Duque et al. (2024): cost per
              metre is LINEAR in trench depth, (110 d + 127) h + (1200 d - 35) USD/m
    b = 1.5   Mansouri & Khanjani (1999), the function most sewer-optimisation papers use:
              0.812 E^1.53 + 0.437 E^1.47 d
    b = 2.0   Swamee & Sharma: unit excavation cost rises linearly with depth and the
              trench volume rises with depth, so the total is quadratic

All three are re-anchored to one calibration point - the marginal cost of depth at 4.0 m -
so they can be compared on equal terms, and that point is the only rate the answer needs.

Run:  python r10_depth_vs_pumping.py          (~2 min)
Outputs: W10/run/research_breakeven_*.csv
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
PY = os.path.dirname(HERE)
sys.path.insert(0, PY)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                                "W8", "py"))

import config as C                                    # noqa: E402
import netlib as N                                    # noqa: E402
from p1_subnetworks import flow_tree                  # noqa: E402
from p2_depths import MIN_COVER_CROWN, MAX_DEPTH, OD_DEFAULT   # noqa: E402
from p2_sizing import accumulate, size_all, ASSIGN_M  # noqa: E402
from p3_breach_diag import solve_with_gov             # noqa: E402
from sewnet.criteria import DEFAULT as CRIT           # noqa: E402

warnings.filterwarnings("ignore")

MIN_DEPTH = MIN_COVER_CROWN + OD_DEFAULT      # 1.60 m, the depth a station resets to
WALK_CAP_M = 8000.0                           # stop a look-ahead here; nothing needs it
CONVERGED_M = 0.005                           # inverts this close are the same invert

# ---------------------------------------------------------------------------
# COST BASIS - every line provisional, every line sourced. See DEPTH_VS_PUMPING.md.
# ---------------------------------------------------------------------------
OMR_USD = 0.3845          # pegged
OMR_AUD_2019 = 0.265      # AUD/USD 0.69 in 2019/20 x 0.3845

# Marginal cost of trench depth at the calibration depth, OMR per metre of trench per
# metre of extra depth. Central value from Central Coast Council (NSW) DSP 2019 depth-banded
# gravity sewer rates, median marginal across DN225-DN750 and the 2.25->5.25 m bands:
#   93 AUD/m per m of depth (2019/20) x 0.265 = 24.6 OMR, escalated ~25 % to 2026 = 31.
# Cross-checks: EPA-430/9-81-003 Table 4.3 >15 ft band gives ~36 OMR/m/m at 2024 prices;
# Maurer et al. (2010) DN200 gives 57 OMR/m/m at Swiss cost levels.
K_DEPTH_REF = 30.0        # OMR / m of trench / m of depth, AT d = D_REF
D_REF = 4.0               # m - the deepest depth at which published rate tables exist

# Manhole depth term. G203 chamber spacing is taken at 50 m; a chamber costs roughly
# K_MH OMR per metre of its depth (Mansouri & Khanjani's manhole term, order of magnitude).
MH_SPACING_M = 50.0
K_MH = 300.0              # OMR per m of chamber depth

# Lifting station capital: Cabral et al. (2018), 360 Portuguese stations, as reproduced by
# Duque et al. (2024) eq.2:   C = e^4.3184 * P^0.5329 (k EUR), P = total hydraulic power kW
PS_A = float(np.exp(4.3184))     # k EUR
PS_B = 0.5329
OMR_EUR = 0.42                   # provisional
PS_CAPEX_FACTOR = 1000.0 * OMR_EUR   # k EUR -> OMR

# Operating cost. NWS's own PIAD rules (W9/analysis/W9_PIAD_financial_review.md 2.2):
#   staff 1,000 OMR per month per pumping station; power 0.02 OMR/kWh;
#   mechanical and electrical plant repair and maintenance 1.0 % of M&E capital per year;
#   insurance 1.0 % of M&E capital per year.
STAFF_OMR_YR = 12000.0
ENERGY_OMR_KWH = 0.020
ME_SHARE = 0.45           # share of station capital that is M&E
ME_OM_PCT = 0.020         # 1 % maintenance + 1 % insurance
PUMP_ETA = 0.65           # wire-to-water
DISC = 0.05
YEARS = 25
PVAF = (1.0 - (1.0 + DISC) ** -YEARS) / DISC      # 14.0939


def pv_annuity():
    return PVAF


def station_lcc(q_adf_m3d, lift_m, staff=True):
    """Life-cycle cost of one in-line lifting station, OMR present value.

    Capital from the hydraulic power at PEAK flow, energy from the AVERAGE daily volume.
    """
    pf = CRIT.pf_merrimack(max(q_adf_m3d / 1000.0,
                               CRIT.PF_HOLD_PROPERTIES * CRIT.PLOT_QADF_M3D / 1000.0))
    q_pk_ls = q_adf_m3d * pf / 86.4                       # m3/d -> L/s
    p_kw = max(9.81 * (q_pk_ls / 1000.0) * lift_m, 0.05)  # hydraulic power
    capex = PS_A * p_kw ** PS_B * PS_CAPEX_FACTOR
    kwh_yr = 2.725e-3 * q_adf_m3d * 365.0 * lift_m / PUMP_ETA
    opex = (ENERGY_OMR_KWH * kwh_yr
            + ME_OM_PCT * ME_SHARE * capex
            + (STAFF_OMR_YR if staff else 0.0))
    return capex + PVAF * opex, capex, opex, p_kw, kwh_yr, q_pk_ls


def trench_cost_per_m(d, b, k_ref=K_DEPTH_REF, d_ref=D_REF):
    """Depth-dependent part of the cost of one metre of trench, OMR.

    Anchored so that d(cost)/d(depth) = k_ref at d = d_ref for every shape b, which is the
    only place published rate tables actually reach.
    """
    k = k_ref / (b * d_ref ** (b - 1.0))
    return k * d ** b


def dig_cost(d_hi, d_lo, length, b):
    """Extra cost of a reach dug at d_hi instead of d_lo, OMR. Trapezoid on the depths."""
    per_m = trench_cost_per_m(d_hi, b) - trench_cost_per_m(d_lo, b)
    mh = K_MH * (d_hi - d_lo) / MH_SPACING_M
    return (per_m + mh) * length


# ---------------------------------------------------------------------------
def build():
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, _ = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    cost, nxt, D = flow_tree(G, z, sink)

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

    qacc, lacc, order = accumulate(G, nxt, q_node)
    pacc, _, _ = accumulate(G, nxt, {k: float(v) for k, v in p_node.items()})
    pipes = size_all(G, nxt, qacc, lacc)

    slope_of, dn_of = {}, {}
    for (n, m), p in pipes.items():
        slope_of[(n, m)] = slope_of[(m, n)] = p["SMIN"]
        dn_of[(n, m)] = dn_of[(m, n)] = p["DN"]

    ups = defaultdict(list)
    for n, m in nxt.items():
        ups[m].append(n)
    invert, depth, lifts, gov = solve_with_gov(G, z, order, ups, slope_of)
    return dict(G=G, xy=xy, z=z, nxt=nxt, ups=ups, order=order, slope_of=slope_of,
                dn_of=dn_of, invert=invert, depth=depth, lifts=lifts, gov=gov,
                qacc=qacc, pacc=pacc, lacc=lacc)


def lookahead(S, b):
    """Walk downstream from breach b with the station DELETED. Exact, see module docstring.

    The walk STOPS at the first of three events, and which one it is decides the case:

      CONVERGED  the no-station invert rejoins the shipped invert. The station is
                 ELIMINATED and the only cost is the excursion.
      REBREACH   the no-station pipe passes 12.00 m again. The station is not saved, it
                 is DEFERRED to that node, and the excursion is a pure loss unless the
                 move consolidates two stations into one.
      OUTLET / CAPPED  neither happened. The station stands.

    GROUND_RECOV_M is a second, weaker measure kept only for comparison: the distance at
    which the GROUND alone has fallen by (depth - 12.00), i.e. what a look-ahead that
    ignores the pipe's own continued fall would call a recovery.
    """
    G, z, nxt, invert = S["G"], S["z"], S["nxt"], S["invert"]
    slope_of = S["slope_of"]
    iv = z[b] - MIN_DEPTH - S["lifts"][b]      # the invert the pipe ARRIVES at, unreset
    d_prev = z[b] - iv
    d_breach = d_prev
    zb = z[b]
    n = b
    dist = 0.0
    dm = 0.0                                    # depth-metre integral, m2
    cost_b = {1.0: 0.0, 1.5: 0.0, 2.0: 0.0}
    maxdepth = d_prev
    reaches = 0
    g_recov = np.nan        # ground alone has fallen by (depth - 12)
    g_full = np.nan         # ground alone has fallen by (depth - 1.60)
    status = "OUTLET"
    while True:
        m = nxt.get(n)
        if m is None or m not in invert or not G.has_edge(n, m):
            status = "OUTLET"
            break
        L = G[n][m]["len"]
        s = slope_of.get((n, m), 0.003)
        iv_free = iv - s * L
        iv_new = min(invert[m], iv_free)
        d_new = z[m] - iv_new
        d_ship = S["depth"][m]
        dd_us = max(d_prev - (z[n] - invert[n]), 0.0)
        dd_ds = max(d_new - d_ship, 0.0)
        dm += 0.5 * (dd_us + dd_ds) * L
        for bb in cost_b:
            cost_b[bb] += 0.5 * (dig_cost(d_prev, z[n] - invert[n], L, bb)
                                 + dig_cost(d_new, d_ship, L, bb))
        dist += L
        reaches += 1
        maxdepth = max(maxdepth, d_new)
        if not np.isfinite(g_recov) and (zb - z[m]) >= (d_breach - MAX_DEPTH):
            g_recov = dist
        if not np.isfinite(g_full) and (zb - z[m]) >= (d_breach - MIN_DEPTH):
            g_full = dist
        iv, d_prev, n = iv_new, d_new, m
        if abs(iv - invert[m]) <= CONVERGED_M:
            status = "CONVERGED"
            break
        if d_new > MAX_DEPTH:
            status = "REBREACH"
            break
        if dist >= WALK_CAP_M:
            status = "CAPPED"
            break
    return dict(status=status, dist=dist, dm=dm, maxdepth=maxdepth, reaches=reaches,
                g_recov=g_recov, g_full=g_full,
                c1=cost_b[1.0], c15=cost_b[1.5], c2=cost_b[2.0])


def main():
    t0 = time.time()
    S = build()
    lifts = S["lifts"]
    print(f"breaches reproduced: {len(lifts)}")
    ref = gpd.read_file(os.path.join(C.OUT_SHP, "W10_lift_sized.shp"))
    print(f"  W10_lift_sized.shp on disk: {len(ref)}; lift heights differ by at most "
          f"{abs(np.sort(list(lifts.values())) - np.sort(ref.LIFT_M.values)).max():.3f} m")

    rows = []
    for b, lift in lifts.items():
        r = lookahead(S, b)
        qadf = S["qacc"][b] + CRIT.INFILT_L_D_KM * (S["lacc"][b] / 1000.0) / 1000.0
        lcc_s, cap_s, ope_s, pkw, kwh, qpk = station_lcc(qadf, lift, staff=True)
        lcc_n, cap_n, ope_n, _, _, _ = station_lcc(qadf, lift, staff=False)
        rows.append(dict(
            NODE=b, X=S["xy"][b][0], Y=S["xy"][b][1], GROUND=round(S["z"][b], 2),
            DEPTH_M=round(S["z"][b] - (S["z"][b] - MIN_DEPTH - lift), 3),
            LIFT_M=round(lift, 3), PLOTS_UP=int(S["pacc"][b]),
            QADF_M3D=round(qadf, 2), QPK_LS=round(qpk, 3), P_KW=round(pkw, 3),
            EXC_M=round(r["dist"], 1), EXC_REACHES=r["reaches"], STATUS=r["status"],
            MAXDEPTH_NOPS=round(r["maxdepth"], 2),
            GROUND_RECOV_M=round(r["g_recov"], 1), GROUND_FULL_M=round(r["g_full"], 1),
            DM_M2=round(r["dm"], 1),
            DIG_B1=round(r["c1"], 0), DIG_B15=round(r["c15"], 0), DIG_B2=round(r["c2"], 0),
            PS_CAPEX=round(cap_s, 0), PS_OPEX_YR=round(ope_s, 0), PS_KWH_YR=round(kwh, 0),
            PS_LCC=round(lcc_s, 0), PS_LCC_NOSTAFF=round(lcc_n, 0)))
    df = pd.DataFrame(rows).sort_values("DM_M2", ascending=False)

    # ELIMINABLE means the no-station branch rejoins the shipped profile without ever
    # passing 12.00 m again. Only for these is "no station" an option at all; everywhere
    # else the station is deferred downstream, not saved.
    df["ELIMINABLE"] = (df.STATUS == "CONVERGED").astype(int)
    # The single most useful number per breach: the marginal excavation rate at which the
    # decision flips. Rate-free, so it survives every rate assumption we do not yet have.
    # Plausible range from the published depth-banded tables is 15-60 OMR/m/m; anything
    # far outside it is a decision no cost data can change.
    df["K_FLIP"] = (K_DEPTH_REF * df.PS_LCC / df.DIG_B15).round(1)
    df["K_FLIP_NOSTAFF"] = (K_DEPTH_REF * df.PS_LCC_NOSTAFF / df.DIG_B15).round(1)
    for tag, lcc in (("STAFFED", "PS_LCC"), ("UNSTAFFED", "PS_LCC_NOSTAFF")):
        for bb, col in ((1.0, "DIG_B1"), (1.5, "DIG_B15"), (2.0, "DIG_B2")):
            df[f"WIN_{tag}_B{bb}"] = ((df[col] > df[lcc]) | (df.ELIMINABLE == 0)).astype(int)
    out = os.path.join(C.OUT_RUN, "research_breakeven_breaches.csv")
    df.to_csv(out, index=False)
    print(f"wrote {out}  ({len(df)} rows)")

    # ------------------------------------------------------------------ headline
    print("\n--- what happens downstream when the station is deleted ---")
    print(df.STATUS.value_counts().to_string())
    el = df[df.ELIMINABLE == 1]
    print(f"\n--- excursion geometry of the {len(el)} that could be eliminated ---")
    for q in (0.10, 0.25, 0.50, 0.75, 0.90, 1.00):
        print(f"  p{int(q*100):>3}  length {el.EXC_M.quantile(q):7.0f} m   "
              f"DM {el.DM_M2.quantile(q):8.0f} m2   "
              f"max depth no-PS {el.MAXDEPTH_NOPS.quantile(q):6.2f} m   "
              f"dig(b=1.5) {el.DIG_B15.quantile(q):9.0f} OMR   "
              f"station {el.PS_LCC.quantile(q):9.0f} OMR")
    print("\n--- the weaker 'ground alone recovers' measure, for comparison ---")
    for lim in (100, 250, 500, 1000, 3000):
        a = int((df.GROUND_RECOV_M <= lim).sum())
        c = int(((df.EXC_M <= lim) & (df.STATUS == "CONVERGED")).sum())
        print(f"  within {lim:5d} m:  ground fall alone clears (depth - 12.00 m) "
              f"{a:3d} of {len(df)}   |   pipe truly rejoins the design profile {c:3d}")

    print("\n--- how many of the 239 justify a station ---")
    for tag in ("STAFFED", "UNSTAFFED"):
        s = "  ".join(f"b={bb}: {int(df[f'WIN_{tag}_B{bb}'].sum()):3d}"
                      for bb in (1.0, 1.5, 2.0))
        print(f"  {tag:<10} {s}")

    # ------------------------------------------------------------------ sensitivity
    sens = []
    for k in (10, 15, 20, 30, 45, 60, 90):
        for bb in (1.0, 1.5, 2.0):
            for staff in (True, False):
                col = {1.0: "DIG_B1", 1.5: "DIG_B15", 2.0: "DIG_B2"}[bb]
                scale = k / K_DEPTH_REF
                dig = df[col] * scale
                lcc = df["PS_LCC"] if staff else df["PS_LCC_NOSTAFF"]
                keep = (dig > lcc) | (df.ELIMINABLE == 0)
                drop = ~keep
                sens.append(dict(K_DEPTH=k, B=bb, STAFFED=int(staff),
                                 STATIONS=int(keep.sum()),
                                 PCT=round(100.0 * keep.mean(), 1),
                                 EXTRA_DIG_MOMR=round(float(dig[drop].sum()) / 1e6, 3),
                                 SAVED_MOMR=round(float(lcc[drop].sum()) / 1e6, 3)))
    sd = pd.DataFrame(sens)
    out2 = os.path.join(C.OUT_RUN, "research_breakeven_sensitivity.csv")
    sd.to_csv(out2, index=False)
    print(f"\nwrote {out2}")
    print(sd[sd.B == 1.5].to_string(index=False))

    # ------------------------------------------------------------------ clusters
    # 239 breaches are NOT 239 stations. Project rule 9 consolidates anything within
    # 1.5 km into one station, so the decision that matters is taken per cluster.
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree
    P = np.c_[df.X.values, df.Y.values]
    pr = list(cKDTree(P).query_pairs(1500.0))
    if pr:
        r = [a for a, _ in pr]; c2 = [b for _, b in pr]
        nc, lab = connected_components(
            coo_matrix((np.ones(len(r)), (r, c2)), shape=(len(P), len(P))), directed=False)
    else:
        nc, lab = len(P), np.arange(len(P))
    df["CLUSTER"] = lab
    cl = []
    for cid, g in df.groupby("CLUSTER"):
        allel = int((g.ELIMINABLE == 1).all())
        cl.append(dict(CLUSTER=cid, N_BREACH=len(g), ALL_ELIMINABLE=allel,
                       PLOTS_UP=int(g.PLOTS_UP.max()), QADF_M3D=round(g.QADF_M3D.max(), 1),
                       LIFT_M=round(g.LIFT_M.max(), 2),
                       DIG_B15=round(g.DIG_B15.sum(), 0),
                       PS_LCC=round(g.PS_LCC.max(), 0),
                       PS_LCC_NOSTAFF=round(g.PS_LCC_NOSTAFF.max(), 0)))
    cl = pd.DataFrame(cl)
    cl["KEEP_STAFFED"] = ((cl.ALL_ELIMINABLE == 0) | (cl.DIG_B15 > cl.PS_LCC)).astype(int)
    cl["KEEP_NOSTAFF"] = ((cl.ALL_ELIMINABLE == 0)
                          | (cl.DIG_B15 > cl.PS_LCC_NOSTAFF)).astype(int)
    out4 = os.path.join(C.OUT_RUN, "research_breakeven_clusters.csv")
    cl.to_csv(out4, index=False)
    df.to_csv(out, index=False)          # rewritten now CLUSTER is on it
    print(f"\nwrote {out4}")
    print(f"  {len(df)} breaches consolidate at 1.5 km into {len(cl)} clusters")
    print(f"  clusters where EVERY breach could be eliminated: {int(cl.ALL_ELIMINABLE.sum())}")
    print(f"  stations kept, NWS manning rule on : {int(cl.KEEP_STAFFED.sum())} of {len(cl)}")
    print(f"  stations kept, NWS manning rule off: {int(cl.KEEP_NOSTAFF.sum())} of {len(cl)}")

    # ------------------------------------------------------------------ break-even curve
    # For a given station life-cycle cost, the excursion DM at which digging costs the same.
    curve = []
    for lcc in (25e3, 50e3, 100e3, 150e3, 200e3, 300e3, 500e3):
        for bb in (1.0, 1.5, 2.0):
            for d0 in (13.0, 15.0, 18.0):
                # marginal cost per m2 of DM at a mid-excursion depth of d0/2 above min
                dmid = 0.5 * (d0 + MIN_DEPTH)
                k = K_DEPTH_REF / (bb * D_REF ** (bb - 1.0))
                marg = bb * k * dmid ** (bb - 1.0) + K_MH / MH_SPACING_M
                curve.append(dict(PS_LCC_OMR=lcc, B=bb, BREACH_DEPTH_M=d0,
                                  MARG_OMR_M2=round(marg, 1),
                                  BREAKEVEN_DM_M2=round(lcc / marg, 0),
                                  BREAKEVEN_LEN_M=round(lcc / marg / (d0 - MIN_DEPTH) * 2, 0)))
    cd = pd.DataFrame(curve)
    out3 = os.path.join(C.OUT_RUN, "research_breakeven_curve.csv")
    cd.to_csv(out3, index=False)
    print(f"wrote {out3}")
    print(cd[(cd.B == 1.5) & (cd.BREACH_DEPTH_M == 13.0)].to_string(index=False))

    # -------------------------------------------------- what p3_lookahead measured
    # p3_lookahead.csv was produced elsewhere; its script is not in the repository and its
    # node ids belong to a different graph build. Both files hold the same 239 breaches, so
    # they are joined on the breach depth. The claim tested: recover_m is NOT the distance
    # at which the depth recovers, it is the distance at which the un-stationed pipe passes
    # 12.00 m AGAIN - i.e. how far the station can be deferred.
    lap = os.path.join(C.OUT_RUN, "p3_lookahead.csv")
    if os.path.exists(lap):
        la = pd.read_csv(lap)
        o1 = df.sort_values("DEPTH_M").reset_index(drop=True)
        o2 = la.sort_values("depth").reset_index(drop=True)
        if len(o1) == len(o2):
            chk = pd.concat([o1[["NODE", "DEPTH_M", "EXC_M", "STATUS", "MAXDEPTH_NOPS"]],
                             o2[["depth", "recover_m", "best_depth", "q"]]], axis=1)
            chk["DIFF_M"] = (chk.recover_m.round(1) - chk.EXC_M).abs()
            out5 = os.path.join(C.OUT_RUN, "research_breakeven_lookahead_check.csv")
            chk.to_csv(out5, index=False)
            rb = chk[chk.STATUS == "REBREACH"]
            print(f"\nwrote {out5}")
            print(f"  p3_lookahead recover_m equals the distance at which the un-stationed "
                  f"pipe passes 12.00 m again on {int((rb.DIFF_M <= 0.2).sum())} of "
                  f"{len(rb)} re-breaching rows (median |diff| {rb.DIFF_M.median():.1f} m)")
            print(f"  read as a RECOVERY distance it gives "
                  f"{int((la.recover_m <= 100).sum())} within 100 m and "
                  f"{int((la.recover_m <= 500).sum())} within 500 m - which is what it is "
                  f"not measuring")

    print(f"\ndone in {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
