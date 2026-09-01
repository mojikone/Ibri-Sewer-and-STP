"""W10 research — what IS the sewer hierarchy, as generative RULES?

Mines NAMA's built 2006 network (`W10/shp/W10_existing_built.shp`, 3,266 true-gravity
pipes, 101.1 km) for the rules behind the three-tier decomposition its own manhole IDs
encode:

    5A-2-TM-MH185      package 5A-2, TRUNK MAIN, chamber 185
    5A-2-SM.2-MH391    package 5A-2, SUB MAIN 2
    5A-1-A49-MH3       package 5A-1, lateral zone A49

RESEARCH ONLY. Writes no design layer and touches no design code. Every table lands in
W10/run/research_hierarchy_*.csv so the numbers in
W10/docs/research/HIERARCHY_RULES.md are reproducible.

Run:  python W10/py/research/research_hierarchy.py
"""

from __future__ import annotations

import collections
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import MultiPoint, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BASE = os.path.abspath(os.path.join(CLAUDE, "..", ".."))

BUILT = os.path.join(CLAUDE, "W10", "shp", "W10_existing_built.shp")
ACCOUNTS = os.path.join(CLAUDE, "W4", "shp", "ELE_accounts.shp")
PLOTS = os.path.join(BASE, "Hydraulic", "SHP", "MoHUP_DATA", "MoH_Plots.shp")
ROADS = os.path.join(BASE, "Hydraulic", "SHP", "Road centerline 2", "Road_Centercline.shp")
STREAMS = os.path.join(BASE, "Hydraulic", "SHP", "Streams",
                       "Streams NSA 2m project boundary.shp")
RUN = os.path.join(CLAUDE, "W10", "run")

SERVE_M = 60.0        # project doctrine: a property within this of a sewer is served
EPSG = 32640

# G203-p29 Tab 11 minimum gradients (m/m) — quoted from W8/py/sewnet/criteria.py
TABLE11 = {200: 0.00500, 250: 0.00375, 315: 0.00270, 400: 0.00205, 500: 0.00155,
           600: 0.00125, 700: 0.00100, 800: 0.00085, 900: 0.00075}
OCCUPANCY = 5.32      # measured, PROJECT-STATE
WWG_LCD = 171.3       # l/c/d area-average wastewater generation (criteria.py)

NOTES: list[str] = []


def put(name: str, df: pd.DataFrame):
    path = os.path.join(RUN, f"research_hierarchy_{name}.csv")
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"  -> research_hierarchy_{name}.csv   ({len(df)} rows)")
    return df


def q(s, ps=(5, 25, 50, 75, 95)):
    s = pd.Series(s).dropna().astype(float)
    if not len(s):
        return {}
    d = {"n": len(s), "min": s.min(), "mean": s.mean(), "max": s.max()}
    for p in ps:
        d[f"p{p}"] = s.quantile(p / 100.0)
    return d


def tier_of(t: str) -> str:
    if t == "TM":
        return "trunk_main"
    if t.startswith("SM"):
        return "sub_main"
    if t == "FL":
        return "force_line"
    return "lateral"


# ---------------------------------------------------------------------------- 1. load
def load_network() -> gpd.GeoDataFrame:
    g = gpd.read_file(BUILT)
    g = g[g.IS_DUP == 0].copy()      # drop the 10.5 km rising main catalogued as gravity
    g = g.set_crs(EPSG, allow_override=True)

    tok = g.US_MHID.astype(str).str.split("-")
    g["PKG"] = tok.str[0] + "-" + tok.str[1]
    g["ZTOK"] = tok.str[2]
    g["MHNO"] = pd.to_numeric(tok.str[3].str.replace("MH", "", regex=False), errors="coerce")
    dtok = g.DS_MHID.astype(str).str.split("-")
    g["DS_ZTOK"] = dtok.str[2]
    g["DS_ZONE"] = dtok.str[0] + "-" + dtok.str[1] + "-" + dtok.str[2]

    g["TIER2"] = g.ZTOK.map(tier_of)
    g["DS_TIER"] = g.DS_ZTOK.map(tier_of)
    g["ZONE2"] = g.PKG + "-" + g.ZTOK
    g["LEN_M"] = g.geometry.length
    return g.reset_index(drop=True)


# ------------------------------------------------------------- 2. graph + accumulation
def build_parent(g: gpd.GeoDataFrame) -> np.ndarray:
    """parent[i] = index of the pipe that carries pipe i's flow onward, else -1.

    One node in the delivery (`5A-2-30-MH235`) carries TWO outgoing pipes with different
    upstream inverts, so the ID graph is not quite a forest. Where that happens the
    continuation is chosen as the outgoing pipe whose US invert matches the incoming
    pipe's DS invert most closely — the physically correct one.
    """
    idx_by_us = collections.defaultdict(list)
    for i, u in enumerate(g.US_MHID):
        idx_by_us[u].append(i)

    us_inv = g.US_INV.to_numpy(float)
    ds_inv = g.DS_INV.to_numpy(float)
    parent = np.full(len(g), -1, dtype=int)
    ambiguous = 0
    for i, d in enumerate(g.DS_MHID):
        cand = idx_by_us.get(d, [])
        if not cand:
            continue
        if len(cand) == 1:
            parent[i] = cand[0]
            continue
        ambiguous += 1
        di = ds_inv[i]
        if np.isnan(di):
            parent[i] = cand[0]
        else:
            parent[i] = min(cand, key=lambda c: abs(us_inv[c] - di)
                            if not np.isnan(us_inv[c]) else 1e9)
    if ambiguous:
        NOTES.append(f"{ambiguous} pipe(s) drained into a node with more than one "
                     f"outgoing pipe; continuation chosen on invert match")
    return parent


def accumulate(g: gpd.GeoDataFrame, parent: np.ndarray, direct: pd.Series):
    """Topological accumulation up->down. Totals are INCLUSIVE of the pipe itself."""
    n = len(g)
    indeg = np.zeros(n, dtype=int)
    for i in range(n):
        if parent[i] >= 0:
            indeg[parent[i]] += 1
    remaining = indeg.copy()
    stack = [i for i in range(n) if indeg[i] == 0]
    order = []
    while stack:
        i = stack.pop()
        order.append(i)
        p = parent[i]
        if p >= 0:
            remaining[p] -= 1
            if remaining[p] == 0:
                stack.append(p)
    if len(order) != n:
        NOTES.append(f"topological order covered {len(order)} of {n} pipes — a cycle exists")

    n_up = np.ones(n)
    l_up = g.LEN_M.to_numpy(float).copy()
    p_up = direct.to_numpy(float).copy()
    for i in order:
        p = parent[i]
        if p >= 0:
            n_up[p] += n_up[i]
            l_up[p] += l_up[i]
            p_up[p] += p_up[i]
    return pd.DataFrame({"UP_PIPES": n_up, "UP_LEN": l_up, "UP_PROPS": p_up},
                        index=g.index), indeg


def best_threshold(vals_lat, vals_main):
    """Single-threshold classifier: below -> lateral, at/above -> SM or TM.

    Returns (threshold, accuracy, recall_main, precision_main) maximising balanced
    accuracy. This is the honest test of "is promotion predictable from load alone".
    """
    v = np.concatenate([vals_lat, vals_main])
    y = np.concatenate([np.zeros(len(vals_lat)), np.ones(len(vals_main))])
    cands = np.unique(np.quantile(v, np.linspace(0, 1, 400)))
    best = (None, -1, 0, 0)
    for t in cands:
        pred = v >= t
        tp = ((pred == 1) & (y == 1)).sum()
        fp = ((pred == 1) & (y == 0)).sum()
        fn = ((pred == 0) & (y == 1)).sum()
        tn = ((pred == 0) & (y == 0)).sum()
        sens = tp / max(tp + fn, 1)
        spec = tn / max(tn + fp, 1)
        bal = 0.5 * (sens + spec)
        if bal > best[1]:
            best = (t, bal, sens, tp / max(tp + fp, 1))
    return best


def main():
    os.makedirs(RUN, exist_ok=True)
    print("Loading network ...")
    g = load_network()
    print(f"  {len(g)} true-gravity pipes, {g.LEN_M.sum()/1000:.2f} km")

    # ---------------------------------------------------------------- properties
    print("Assigning properties to pipes ...")
    acc = gpd.read_file(ACCOUNTS).to_crs(EPSG)
    j = gpd.sjoin_nearest(acc[["geometry", "CATEGORY"]], g[["geometry"]], how="inner",
                          max_distance=SERVE_M, distance_col="d")
    g["PROPS"] = g.index.map(j.groupby("index_right").size()).fillna(0.0)
    g["PROPS_DOM"] = g.index.map(
        j[j.CATEGORY == "domestic"].groupby("index_right").size()).fillna(0.0)
    print(f"  {int(g.PROPS.sum())} of {len(acc)} accounts within {SERVE_M:.0f} m of a "
          f"built sewer")

    parent = build_parent(g)
    up, indeg = accumulate(g, parent, g.PROPS)
    g = pd.concat([g, up], axis=1)
    g["FANIN"] = indeg

    # ============================================================ A. tier shares
    print("\nA. tier shares")
    rows = []
    for scope, sub in [("all packages", g),
                       ("5A-2..5A-5 (labelled)", g[g.PKG != "5A-1"]),
                       ("5A-1 only (unlabelled)", g[g.PKG == "5A-1"])]:
        tot = sub.LEN_M.sum()
        for t in ["trunk_main", "sub_main", "lateral"]:
            s = sub[sub.TIER2 == t]
            rows.append({"scope": scope, "tier": t, "pipes": len(s),
                         "km": round(s.LEN_M.sum() / 1000, 3),
                         "share_pct": round(100 * s.LEN_M.sum() / tot, 1) if tot else 0,
                         "zones": s.ZONE2.nunique(),
                         "median_pipe_m": round(s.LEN_M.median(), 1) if len(s) else None,
                         "props_direct": int(s.PROPS.sum())})
    put("tier_shares", pd.DataFrame(rows))

    # ============================================================ B. zone anatomy
    print("\nB. what a zone is")
    zrows = []
    for z, s in g.groupby("ZONE2"):
        heads = list(s.geometry.apply(lambda ln: ln.coords[0]))
        tails = list(s.geometry.apply(lambda ln: ln.coords[-1]))
        hull = MultiPoint(heads + tails).convex_hull
        inside_ds = collections.Counter(s.DS_MHID[s.DS_ZONE == z])
        internal_junc = sum(1 for v in inside_ds.values() if v >= 2)
        n_heads = int((~s.US_MHID.isin(set(s.DS_MHID))).sum())
        outp = s[s.DS_ZONE != z]
        ref = outp if len(outp) else s
        # straightness: end-to-end distance of the zone / its laid length
        pts = MultiPoint(heads + tails)
        mrr = pts.minimum_rotated_rectangle
        try:
            cx, cy = mrr.exterior.coords.xy
            e = [Point(cx[i], cy[i]).distance(Point(cx[i + 1], cy[i + 1])) for i in range(4)]
            long_side, short_side = max(e[0], e[1]), min(e[0], e[1])
        except Exception:
            long_side = short_side = float("nan")
        zrows.append({
            "zone": z, "pkg": s.PKG.iloc[0], "tier": s.TIER2.iloc[0],
            "pipes": len(s),
            "chambers": len(set(s.US_MHID) | set(s.DS_MHID[s.DS_ZONE == z])),
            "len_m": round(s.LEN_M.sum(), 1),
            "median_pipe_m": round(s.LEN_M.median(), 1),
            "props_direct": int(s.PROPS.sum()),
            "internal_junctions": internal_junc,
            "head_chambers": n_heads,
            "outlets": len(outp),
            "simple_path": int(internal_junc == 0 and n_heads <= 1),
            "hull_ha": round(hull.area / 1e4, 3),
            "long_side_m": round(long_side, 1),
            "short_side_m": round(short_side, 1),
            "elongation": round(long_side / short_side, 2) if short_side > 1 else None,
            "props_at_outlet": int(ref.UP_PROPS.max()),
            "len_at_outlet_m": round(ref.UP_LEN.max(), 1),
            "pipes_at_outlet": int(ref.UP_PIPES.max()),
            "ds_zone": outp.DS_ZONE.iloc[0] if len(outp) else "",
            "ds_tier": outp.DS_TIER.iloc[0] if len(outp) else "",
            "mh_lo": int(s.MHNO.min()) if s.MHNO.notna().any() else None,
            "mh_hi": int(s.MHNO.max()) if s.MHNO.notna().any() else None,
            "mh_span": int(s.MHNO.max() - s.MHNO.min() + 1) if s.MHNO.notna().any() else None,
            "has_levels": int(s.HAS_LVL.max()),
            "dia_max": s.DIA_OUT.max(),
        })
    zon = pd.DataFrame(zrows).sort_values(["pkg", "tier", "zone"]).reset_index(drop=True)
    zon["mh_contiguous"] = (zon.mh_span == zon.chambers).astype("Int64")
    put("zones", zon)

    zs = []
    for t in ["lateral", "sub_main", "trunk_main"]:
        s = zon[zon.tier == t]
        for col in ["pipes", "chambers", "len_m", "median_pipe_m", "props_direct",
                    "hull_ha", "long_side_m", "elongation", "props_at_outlet",
                    "len_at_outlet_m"]:
            d = q(s[col], ps=(5, 25, 50, 75, 90, 95))
            d.update({"tier": t, "metric": col})
            zs.append(d)
    cols = ["tier", "metric", "n", "min", "p5", "p25", "p50", "p75", "p90", "p95",
            "max", "mean"]
    put("zone_stats", pd.DataFrame(zs)[cols].round(3))

    # zone topology summary — the strongest structural finding
    trow = []
    for scope, sub in [("all zones", zon), ("lateral zones", zon[zon.tier == "lateral"]),
                       ("sub mains", zon[zon.tier == "sub_main"]),
                       ("trunk zones", zon[zon.tier == "trunk_main"])]:
        trow.append({"scope": scope, "zones": len(sub),
                     "simple_path": int(sub.simple_path.sum()),
                     "simple_path_pct": round(100 * sub.simple_path.mean(), 1),
                     "zero_internal_junctions": int((sub.internal_junctions == 0).sum()),
                     "one_outlet": int((sub.outlets <= 1).sum()),
                     "one_outlet_pct": round(100 * (sub.outlets <= 1).mean(), 1),
                     "one_head": int((sub.head_chambers <= 1).sum()),
                     "mh_numbers_contiguous_pct":
                         round(100 * sub.mh_contiguous.fillna(0).mean(), 1)})
    put("zone_topology", pd.DataFrame(trow))

    # ============================================================ C. chaining
    print("\nC. chaining")
    zmap = zon.set_index("zone")
    sys.setrecursionlimit(20000)
    memo = {}

    def depth(z, guard=()):
        if z in memo:
            return memo[z]
        if z in guard or z not in zmap.index:
            return 0
        row = zmap.loc[z]
        if row.tier != "lateral":
            memo[z] = 0
            return 0
        d = row.ds_zone
        v = 1 if (not d or d not in zmap.index) else 1 + depth(d, guard + (z,))
        memo[z] = v
        return v

    zon["chain_to_main"] = [depth(z) for z in zon.zone]
    zon.to_csv(os.path.join(RUN, "research_hierarchy_zones.csv"), index=False,
               encoding="utf-8")

    crows = []
    for scope, sub in [("all packages", zon[zon.tier == "lateral"]),
                       ("5A-2..5A-5", zon[(zon.tier == "lateral") & (zon.pkg != "5A-1")]),
                       ("5A-1 only", zon[(zon.tier == "lateral") & (zon.pkg == "5A-1")])]:
        d = q(sub.chain_to_main, ps=(5, 25, 50, 75, 90, 95))
        d["scope"] = scope
        crows.append(d)
    put("chain_depth", pd.DataFrame(crows).round(2))

    orows = []
    for scope, sub in [("all packages", zon[zon.tier == "lateral"]),
                       ("5A-2..5A-5", zon[(zon.tier == "lateral") & (zon.pkg != "5A-1")]),
                       ("5A-1 only", zon[(zon.tier == "lateral") & (zon.pkg == "5A-1")])]:
        vc = sub.ds_tier.replace("", "outside dataset").value_counts()
        for k, v in vc.items():
            orows.append({"scope": scope, "drains_into": k, "zones": int(v),
                          "share_pct": round(100 * v / len(sub), 1)})
    put("zone_outflow", pd.DataFrame(orows))

    lat = zon[zon.tier == "lateral"].copy()
    lat["joins"] = np.where(lat.ds_tier.isin(["sub_main", "trunk_main"]), "SM_or_TM",
                            "another_lateral")
    jrows = []
    for k, s in lat.groupby("joins"):
        for col in ["props_at_outlet", "len_at_outlet_m", "pipes_at_outlet",
                    "chain_to_main", "len_m", "props_direct"]:
            d = q(s[col], ps=(5, 25, 50, 75, 95))
            d.update({"group": k, "metric": col})
            jrows.append(d)
    put("chain_termination", pd.DataFrame(jrows).round(2))

    # Does the chain break at a load ceiling? Distribution of load carried by a lateral
    # at the point it hands over, vs the largest load any lateral ever carries.
    put("chain_ceiling", pd.DataFrame([{
        "measure": "largest load any LATERAL pipe carries (props)",
        "value": round(g[g.TIER2 == "lateral"].UP_PROPS.max(), 0)},
        {"measure": "largest load any lateral carries, 5A-2..5A-5",
         "value": round(g[(g.TIER2 == "lateral") & (g.PKG != "5A-1")].UP_PROPS.max(), 0)},
        {"measure": "p95 load on a lateral pipe (5A-2..5A-5)",
         "value": round(g[(g.TIER2 == "lateral") & (g.PKG != "5A-1")].UP_PROPS.quantile(.95), 0)},
        {"measure": "smallest load at a SUB MAIN head (props)",
         "value": round(g[g.TIER2 == "sub_main"].UP_PROPS.min(), 0)},
        {"measure": "largest laid LENGTH any lateral carries (m)",
         "value": round(g[g.TIER2 == "lateral"].UP_LEN.max(), 0)},
        {"measure": "largest laid length any lateral carries, 5A-2..5A-5 (m)",
         "value": round(g[(g.TIER2 == "lateral") & (g.PKG != "5A-1")].UP_LEN.max(), 0)},
        {"measure": "longest single lateral ZONE (m)",
         "value": round(zon[zon.tier == "lateral"].len_m.max(), 0)},
        {"measure": "most chambers in a lateral zone",
         "value": int(zon[zon.tier == "lateral"].chambers.max())},
    ]))

    # ============================================================ D. promotion
    print("\nD. promotion thresholds")
    prows = []
    for scope, sub in [("all packages", g), ("5A-2..5A-5", g[g.PKG != "5A-1"])]:
        for t in ["lateral", "sub_main", "trunk_main"]:
            s = sub[sub.TIER2 == t]
            for col in ["UP_PROPS", "UP_LEN", "UP_PIPES"]:
                d = q(s[col], ps=(1, 5, 25, 50, 75, 95, 99))
                d.update({"scope": scope, "tier": t, "metric": col})
                prows.append(d)
    put("accumulation_by_tier", pd.DataFrame(prows).round(2))

    heads = []
    for z, s in g[g.TIER2.isin(["sub_main", "trunk_main"])].groupby("ZONE2"):
        inside = set(s.DS_MHID)
        h = s[~s.US_MHID.isin(inside)]
        for _, r in h.iterrows():
            heads.append({"zone": z, "tier": r.TIER2, "pkg": r.PKG, "pipe": r.FEATUREID,
                          "props_at_head": int(r.UP_PROPS),
                          "len_at_head_m": round(r.UP_LEN, 1),
                          "pipes_at_head": int(r.UP_PIPES),
                          "dia_out_mm": r.DIA_OUT,
                          "slope_pct": round(r.SLOPE_PCT, 3) if pd.notna(r.SLOPE_PCT) else None,
                          "depth_us_m": r.DEP_US,
                          "zone_len_m": round(s.LEN_M.sum(), 1),
                          "zone_props_at_outlet":
                              int(s[s.DS_ZONE != z].UP_PROPS.max()) if (s.DS_ZONE != z).any()
                              else int(s.UP_PROPS.max())})
    put("tier_heads", pd.DataFrame(heads).sort_values(["tier", "zone"]))

    sep = []
    for scope, sub in [("all packages", g), ("5A-2..5A-5", g[g.PKG != "5A-1"])]:
        lt = sub[sub.TIER2 == "lateral"]
        sm = sub[sub.TIER2 == "sub_main"]
        tm = sub[sub.TIER2 == "trunk_main"]
        for col in ["UP_PROPS", "UP_LEN"]:
            sep.append({
                "scope": scope, "metric": col,
                "lateral_p50": round(lt[col].median(), 1),
                "lateral_p95": round(lt[col].quantile(.95), 1),
                "lateral_p99": round(lt[col].quantile(.99), 1),
                "lateral_max": round(lt[col].max(), 1),
                "submain_min": round(sm[col].min(), 1) if len(sm) else None,
                "submain_p50": round(sm[col].median(), 1) if len(sm) else None,
                "trunk_min": round(tm[col].min(), 1) if len(tm) else None,
                "trunk_p50": round(tm[col].median(), 1) if len(tm) else None,
                "pct_laterals_above_submain_min":
                    round(100 * (lt[col] > sm[col].min()).mean(), 1) if len(sm) else None})
    put("tier_separation", pd.DataFrame(sep))

    # can a single threshold on load reproduce the designer's tiering?
    crow = []
    lab = g[g.PKG != "5A-1"]          # only where the tiering is actually labelled
    for col in ["UP_PROPS", "UP_LEN", "UP_PIPES"]:
        vl = lab[lab.TIER2 == "lateral"][col].to_numpy(float)
        vm = lab[lab.TIER2.isin(["sub_main", "trunk_main"])][col].to_numpy(float)
        t, bal, sens, prec = best_threshold(vl, vm)
        crow.append({"metric": col, "best_threshold": round(t, 1),
                     "balanced_accuracy": round(bal, 3),
                     "recall_on_SM_TM": round(sens, 3),
                     "precision_on_SM_TM": round(prec, 3),
                     "n_lateral": len(vl), "n_main": len(vm)})
    put("threshold_classifier", pd.DataFrame(crow))

    # fan-in: how many things join a sub main / the trunk
    fan = []
    for t in ["sub_main", "trunk_main"]:
        s = g[g.TIER2 == t]
        inc = g[(g.DS_MHID.isin(set(s.US_MHID) | set(s.DS_MHID))) & (g.TIER2 != t)]
        by = inc.groupby("ZONE2").agg(props=("UP_PROPS", "max"),
                                      length=("UP_LEN", "max")).reset_index()
        fan.append({"tier": t, "joining_zones": len(by),
                    "joining_laterals": int((inc.TIER2 == "lateral").sum()),
                    "median_props_of_joiner": round(by.props.median(), 0) if len(by) else None,
                    "min_props_of_joiner": round(by.props.min(), 0) if len(by) else None,
                    "max_props_of_joiner": round(by.props.max(), 0) if len(by) else None,
                    "joiners_under_25_props": int((by.props < 25).sum()) if len(by) else None,
                    "joiners_over_100_props": int((by.props >= 100).sum()) if len(by) else None})
    put("fan_in", pd.DataFrame(fan))

    # ============================================================ E. diameters
    print("\nE. diameters")
    lv = g[(g.HAS_LVL == 1) & g.DIA_OUT.notna()].copy()
    drows = []
    for t, s in lv.groupby("TIER2"):
        for d_, ss in s.groupby("DIA_OUT"):
            drows.append({"tier": t, "dia_out_mm": d_, "pipes": len(ss),
                          "km": round(ss.LEN_M.sum() / 1000, 3),
                          "props_up_p50": round(ss.UP_PROPS.median(), 1),
                          "props_up_p95": round(ss.UP_PROPS.quantile(.95), 1),
                          "props_up_max": round(ss.UP_PROPS.max(), 1),
                          "len_up_p50_m": round(ss.UP_LEN.median(), 1),
                          "len_up_max_m": round(ss.UP_LEN.max(), 1)})
    put("diameter_by_tier", pd.DataFrame(drows))

    bands = [0, 25, 50, 100, 200, 400, 800, 1600, 1e9]
    labels = ["0-24", "25-49", "50-99", "100-199", "200-399", "400-799", "800-1599", "1600+"]
    lv["band"] = pd.cut(lv.UP_PROPS, bands, right=False, labels=labels)
    bt = lv.groupby(["band", "DIA_OUT"], observed=True).size().reset_index(name="pipes")
    piv = bt.pivot(index="band", columns="DIA_OUT", values="pipes").fillna(0).astype(int)
    piv.columns = [f"OD{int(c)}" for c in piv.columns]
    piv = piv.reset_index()
    # what our sizing would have called for at that load
    ctx = lv.groupby("band", observed=True).agg(
        pipes=("FEATUREID", "size"),
        props_p50=("UP_PROPS", "median"),
        qpk_ls_p50=("UP_PROPS", lambda s: round(
            (s.median() * OCCUPANCY * WWG_LCD / 1000.0) * 4.7 / 86.4, 2)),
        qpk_ls_max=("UP_PROPS", lambda s: round(
            (s.max() * OCCUPANCY * WWG_LCD / 1000.0) * 4.7 / 86.4, 2))).reset_index()
    put("diameter_by_load_band", piv.merge(ctx, on="band", how="left"))

    # diameter changes along the network: where does the designer step up?
    steps = []
    for i in range(len(g)):
        p = parent[i]
        if p < 0:
            continue
        a, b = g.DIA_OUT.iat[i], g.DIA_OUT.iat[p]
        if pd.notna(a) and pd.notna(b) and a != b:
            steps.append({"from_mm": a, "to_mm": b,
                          "props_at_step": int(g.UP_PROPS.iat[p]),
                          "len_at_step_m": round(g.UP_LEN.iat[p], 1),
                          "tier_from": g.TIER2.iat[i], "tier_to": g.TIER2.iat[p],
                          "pipe": g.FEATUREID.iat[p]})
    st = pd.DataFrame(steps)
    put("diameter_steps", st if len(st) else pd.DataFrame(
        [{"from_mm": None, "to_mm": None, "note": "no diameter change found"}]))

    # ============================================================ F. gradient / depth
    print("\nF. gradients and depths")
    lv["grad_mm_m"] = lv.SLOPE_PCT * 10.0
    lv["dep_mean"] = lv[["DEP_US", "DEP_DS"]].mean(axis=1)
    lv["ground_fall_mm_m"] = (lv.US_GRD - lv.DS_GRD) / lv.LEN_M * 1000.0
    grows = []
    for t, s in lv.groupby("TIER2"):
        for col, labn in [("grad_mm_m", "laid_gradient_mm_per_m"),
                          ("ground_fall_mm_m", "ground_fall_mm_per_m"),
                          ("dep_mean", "depth_to_invert_m"),
                          ("DEP_DS", "depth_downstream_m"),
                          ("LEN_M", "pipe_run_m")]:
            d = q(s[col], ps=(5, 25, 50, 75, 95))
            d.update({"tier": t, "metric": labn})
            grows.append(d)
    put("gradient_depth_by_tier", pd.DataFrame(grows).round(3))

    lv["req_mm"] = np.where(lv.DIA_OUT <= 200, TABLE11[200] * 1000,
                            lv.DIA_OUT.map(lambda d: TABLE11.get(int(d), TABLE11[200]) * 1000))
    lv["ratio"] = lv.grad_mm_m / lv.req_mm
    crow2 = []
    for t, s in lv.groupby("TIER2"):
        crow2.append({"tier": t, "pipes": len(s),
                      "flatter_than_T11_DN200": int((s.ratio < 1).sum()),
                      "pct_flatter": round(100 * (s.ratio < 1).mean(), 1),
                      "median_ratio": round(s.ratio.median(), 2),
                      "p5_ratio": round(s.ratio.quantile(.05), 2),
                      "p95_ratio": round(s.ratio.quantile(.95), 2),
                      "steeper_than_2x_pct": round(100 * (s.ratio > 2).mean(), 1),
                      "dead_flat": int((s.grad_mm_m <= 0.001).sum()),
                      "adverse": int((s.grad_mm_m < 0).sum()),
                      "follows_ground_pct":
                          round(100 * (abs(s.grad_mm_m - s.ground_fall_mm_m) <= 2).mean(), 1)})
    put("table11_compliance", pd.DataFrame(crow2))

    # gradient rounding: does the as-built lay round gradients like our 0.05 % steps?
    r = (lv.SLOPE_PCT * 100).round(0)          # slope in 0.01 % units
    rr = pd.DataFrame({
        "test": ["on a 0.05 % step (+/-0.005 %)", "on a 0.10 % step", "on a 1 mm/m step"],
        "pct_of_pipes": [
            round(100 * (abs(lv.SLOPE_PCT / 0.05 - (lv.SLOPE_PCT / 0.05).round()) < 0.1).mean(), 1),
            round(100 * (abs(lv.SLOPE_PCT / 0.10 - (lv.SLOPE_PCT / 0.10).round()) < 0.1).mean(), 1),
            round(100 * (abs(lv.grad_mm_m - lv.grad_mm_m.round()) < 0.1).mean(), 1)]})
    put("gradient_rounding", rr)

    # ============================================================ G. packages
    print("\nG. packages")
    prow, hulls = [], {}
    for p, s in g.groupby("PKG"):
        pts = [c for ln in s.geometry for c in ln.coords]
        hull = MultiPoint(pts).convex_hull
        hulls[p] = hull
        a = gpd.sjoin_nearest(acc[["geometry"]], s[["geometry"]], how="inner",
                              max_distance=SERVE_M, distance_col="d")
        prow.append({"pkg": p, "pipes": len(s), "km": round(s.LEN_M.sum() / 1000, 3),
                     "chambers": len(set(s.US_MHID) | set(s.DS_MHID)),
                     "zones": s.ZONE2.nunique(),
                     "lateral_zones": s[s.TIER2 == "lateral"].ZONE2.nunique(),
                     "sub_mains": s[s.TIER2 == "sub_main"].ZONE2.nunique(),
                     "trunk_zones": s[s.TIER2 == "trunk_main"].ZONE2.nunique(),
                     "accounts_within_60m": len(a),
                     "hull_km2": round(hull.area / 1e6, 3),
                     "km_per_km2": round((s.LEN_M.sum() / 1000) / (hull.area / 1e6), 2),
                     "m_per_account": round(s.LEN_M.sum() / max(len(a), 1), 1),
                     "has_levels_pct": round(100 * s.HAS_LVL.mean(), 1)})
    put("packages", pd.DataFrame(prow))

    ov = []
    ks = sorted(hulls)
    for i, a_ in enumerate(ks):
        for b_ in ks[i + 1:]:
            inter = hulls[a_].intersection(hulls[b_]).area
            ov.append({"pkg_a": a_, "pkg_b": b_, "overlap_km2": round(inter / 1e6, 3),
                       "pct_of_a": round(100 * inter / hulls[a_].area, 1),
                       "pct_of_b": round(100 * inter / hulls[b_].area, 1)})
    put("package_overlap", pd.DataFrame(ov))

    # do pipes ever cross a package boundary in the connectivity sense?
    xp = g[g.PKG != g.DS_MHID.str.split("-").str[0].add("-").add(
        g.DS_MHID.str.split("-").str[1])]
    put("package_crossings", xp[["FEATUREID", "PKG", "US_MHID", "DS_MHID", "TIER2",
                                 "UP_PROPS", "UP_LEN"]].round(1))

    # ============================================================ H. wadi crossings
    print("\nH. wadi crossings")
    try:
        st_ = gpd.read_file(STREAMS).to_crs(EPSG)
        u_all = unary_union(st_.geometry.values)
        hit_all = g[g.geometry.intersects(u_all)]
        wrows = [{"stream_set": "all NSA 2 m streams",
                  "stream_km": round(st_.length.sum() / 1000, 1),
                  "pipes_crossing": len(hit_all),
                  "pct_of_network": round(100 * len(hit_all) / len(g), 1),
                  "trunk": int((hit_all.TIER2 == "trunk_main").sum()),
                  "sub_main": int((hit_all.TIER2 == "sub_main").sum()),
                  "lateral": int((hit_all.TIER2 == "lateral").sum())}]
        for v, sub in st_.groupby("STRM_VAL"):
            u = unary_union(sub.geometry.values)
            hit = g[g.geometry.intersects(u)]
            wrows.append({"stream_set": f"STRM_VAL {v}",
                          "stream_km": round(sub.length.sum() / 1000, 2),
                          "pipes_crossing": len(hit),
                          "pct_of_network": round(100 * len(hit) / len(g), 2),
                          "trunk": int((hit.TIER2 == "trunk_main").sum()),
                          "sub_main": int((hit.TIER2 == "sub_main").sum()),
                          "lateral": int((hit.TIER2 == "lateral").sum())})
        put("wadi_crossings", pd.DataFrame(wrows))
        # what happens AT a crossing: depth and gradient vs the rest of that tier
        hl = hit_all[hit_all.HAS_LVL == 1]
        crows3 = []
        for t in ["trunk_main", "sub_main", "lateral"]:
            a_ = hl[hl.TIER2 == t]
            b_ = lv[lv.TIER2 == t]
            crows3.append({"tier": t, "crossing_pipes": len(a_),
                           "median_depth_crossing":
                               round(a_[["DEP_US", "DEP_DS"]].mean(axis=1).median(), 2)
                               if len(a_) else None,
                           "median_depth_elsewhere": round(b_.dep_mean.median(), 2),
                           "median_grad_crossing_mm_m":
                               round((a_.SLOPE_PCT * 10).median(), 2) if len(a_) else None,
                           "median_grad_elsewhere_mm_m": round(b_.grad_mm_m.median(), 2)})
        put("wadi_behaviour", pd.DataFrame(crows3))
    except Exception as e:                                    # pragma: no cover
        print(f"  ! stream analysis skipped: {e}")

    # ============================================================ I. roads
    print("\nI. road relationship")
    try:
        rd = gpd.read_file(ROADS).set_crs(EPSG, allow_override=True)
        rd["dual"] = pd.to_numeric(rd["dual"], errors="coerce").fillna(0)
        rrows = []
        for t, s in g.groupby("TIER2"):
            near = gpd.sjoin_nearest(s[["geometry"]], rd[["geometry", "dual"]], how="left",
                                     max_distance=250, distance_col="d")
            near = near.groupby(near.index).first()
            rrows.append({"tier": t, "pipes": len(s),
                          "median_dist_to_road_m": round(near.d.median(), 1),
                          "within_5m_pct": round(100 * (near.d <= 5).mean(), 1),
                          "within_15m_pct": round(100 * (near.d <= 15).mean(), 1),
                          "beyond_20m_pct": round(100 * (near.d > 20).mean(), 1),
                          "nearest_is_dual_pct": round(100 * (near.dual == 1).mean(), 1),
                          "on_dual_within_6m_pct":
                              round(100 * ((near.dual == 1) & (near.d <= 6)).mean(), 2)})
        put("road_relationship", pd.DataFrame(rrows))
    except Exception as e:                                    # pragma: no cover
        print(f"  ! road analysis skipped: {e}")

    # ============================================================ J. plots per zone
    # NOTE: MoH_Plots carries NO populated block number (BLOCK_NUMB is empty on every
    # record, VILLAGE_EN on 29 %), so "is a zone a block?" cannot be answered from the
    # cadastre. It is answered geometrically instead, in research_asbuilt_check.py.
    print("\nJ. how many plots front a lateral zone")
    try:
        pl = gpd.read_file(PLOTS, columns=["OBJECTID", "LANDUSE"]).to_crs(EPSG)
        latg = g[g.TIER2 == "lateral"]
        jj = gpd.sjoin_nearest(pl[["geometry", "LANDUSE"]], latg[["geometry", "ZONE2"]],
                               how="inner", max_distance=SERVE_M, distance_col="d")
        zb = jj.groupby("ZONE2").agg(plots=("LANDUSE", "size"),
                                     landuses=("LANDUSE", "nunique")).reset_index()
        zb = zb.merge(zon[["zone", "pkg", "len_m", "chambers", "props_direct"]],
                      left_on="ZONE2", right_on="zone", how="left").drop(columns="zone")
        put("zone_plots_fronting", zb)
        srows = []
        for col in ["plots", "landuses"]:
            d = q(zb[col], ps=(5, 25, 50, 75, 95)); d["metric"] = col; srows.append(d)
        put("zone_plots_fronting_stats", pd.DataFrame(srows).round(2))
    except Exception as e:                                    # pragma: no cover
        print(f"  ! plot analysis skipped: {e}")

    # ============================================================ K. sizing context
    print("\nK. our sizing rules against the as-built")
    lv2 = lv.copy()
    lv2["qadf_m3d"] = lv2.UP_PROPS * OCCUPANCY * WWG_LCD / 1000.0
    pop = lv2.UP_PROPS * OCCUPANCY
    lv2["pf"] = np.where(pop >= 1000, 4.7 * np.maximum(pop, 1e-9) ** -0.11 * 1000 ** 0.11, 4.7)
    lv2["qpk_ls"] = lv2.qadf_m3d * lv2.pf / 86.4
    put("sizing_context", lv2.groupby("TIER2").agg(
        pipes=("FEATUREID", "size"),
        props_up_p50=("UP_PROPS", "median"),
        props_up_max=("UP_PROPS", "max"),
        qadf_p50_m3d=("qadf_m3d", "median"),
        qpk_p50_ls=("qpk_ls", "median"),
        qpk_max_ls=("qpk_ls", "max"),
        dia_p50_mm=("DIA_OUT", "median"),
        dia_max_mm=("DIA_OUT", "max")).round(2).reset_index())

    # ============================================================ L. tier network position
    print("\nL. where each tier sits in the ground")
    grd = []
    for t, s in lv.groupby("TIER2"):
        d = q(s.DS_GRD, ps=(5, 25, 50, 75, 95)); d["tier"] = t; d["metric"] = "ground_level_m"
        grd.append(d)
    put("tier_ground_level", pd.DataFrame(grd).round(2))

    if NOTES:
        print("\nNotes:")
        for n in NOTES:
            print("  -", n)
        pd.DataFrame({"note": NOTES}).to_csv(
            os.path.join(RUN, "research_hierarchy_notes.csv"), index=False, encoding="utf-8")

    print("\nDone. Tables in", RUN)


if __name__ == "__main__":
    main()
