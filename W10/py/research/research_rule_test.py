"""W10 research part 3 — test the candidate rules, don't just state them.

Three things part 1 and 2 left open:

  1. Package 5A-1 carries NO TM/SM label at all — 1,123 pipes, 32.2 km, every zone
     parsed as a lateral. That is where W8's "91 % lateral-into-lateral, median chain 11"
     came from. If the promotion rule measured on 5A-2..5A-5 is real, applying it to 5A-1
     should produce a sensible trunk and a sensible set of sub mains. Test it.

  2. What is the REACH of a sub main — how far upstream does it collect from, and how far
     apart do sub mains sit?

  3. Does the A / B prefix inside 5A-1 mark two de-facto systems?

RESEARCH ONLY. Run:  python W10/py/research/research_rule_test.py
"""

from __future__ import annotations

import collections
import math
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from research_hierarchy import (               # noqa: E402
    ACCOUNTS, EPSG, RUN, SERVE_M, accumulate, build_parent, load_network, put, q)


def main():
    g = load_network()
    acc = gpd.read_file(ACCOUNTS).to_crs(EPSG)
    j = gpd.sjoin_nearest(acc[["geometry", "CATEGORY"]], g[["geometry"]], how="inner",
                          max_distance=SERVE_M, distance_col="d")
    g["PROPS"] = g.index.map(j.groupby("index_right").size()).fillna(0.0)
    parent = build_parent(g)
    up, _ = accumulate(g, parent, g.PROPS)
    g = pd.concat([g, up], axis=1)

    # ============================================ 1. calibrate on 5A-2..5A-5, apply to 5A-1
    print("\n1. calibrate the length rule, then apply it to the unlabelled package")
    lab = g[g.PKG != "5A-1"]
    rows = []
    for thr in [300, 500, 600, 700, 800, 821, 900, 1000, 1200, 1500, 2000, 3000]:
        pred = lab.UP_LEN >= thr
        act = lab.TIER2.isin(["sub_main", "trunk_main"])
        tp = int((pred & act).sum()); fp = int((pred & ~act).sum())
        fn = int((~pred & act).sum()); tn = int((~pred & ~act).sum())
        rows.append({"threshold_m": thr, "predicted_main_pipes": int(pred.sum()),
                     "actual_main_pipes": int(act.sum()),
                     "recall": round(tp / max(tp + fn, 1), 3),
                     "precision": round(tp / max(tp + fp, 1), 3),
                     "balanced_acc": round(0.5 * (tp / max(tp + fn, 1) + tn / max(tn + fp, 1)), 3),
                     "predicted_main_km": round(lab[pred].LEN_M.sum() / 1000, 2),
                     "actual_main_km": round(lab[act].LEN_M.sum() / 1000, 2)})
    put("rule_sweep_length", pd.DataFrame(rows))

    # two-level version: trunk above a second threshold
    rows2 = []
    for t_sm in [600, 800, 1000, 1500]:
        for t_tm in [3000, 5000, 8000, 12000, 16000]:
            if t_tm <= t_sm:
                continue
            pred = np.where(lab.UP_LEN >= t_tm, "trunk_main",
                            np.where(lab.UP_LEN >= t_sm, "sub_main", "lateral"))
            agree = (pred == lab.TIER2.to_numpy()).mean()
            rows2.append({"sm_threshold_m": t_sm, "tm_threshold_m": t_tm,
                          "exact_tier_agreement_pct": round(100 * agree, 1),
                          "pred_trunk_km": round(lab[pred == "trunk_main"].LEN_M.sum() / 1000, 2),
                          "pred_sub_km": round(lab[pred == "sub_main"].LEN_M.sum() / 1000, 2),
                          "actual_trunk_km": round(
                              lab[lab.TIER2 == "trunk_main"].LEN_M.sum() / 1000, 2),
                          "actual_sub_km": round(
                              lab[lab.TIER2 == "sub_main"].LEN_M.sum() / 1000, 2)})
    put("rule_sweep_two_level", pd.DataFrame(rows2).sort_values(
        "exact_tier_agreement_pct", ascending=False))

    # apply the best pair to 5A-1
    best = pd.DataFrame(rows2).sort_values("exact_tier_agreement_pct", ascending=False).iloc[0]
    t_sm, t_tm = float(best.sm_threshold_m), float(best.tm_threshold_m)
    p1 = g[g.PKG == "5A-1"].copy()
    p1["TIER_RULE"] = np.where(p1.UP_LEN >= t_tm, "trunk_main",
                               np.where(p1.UP_LEN >= t_sm, "sub_main", "lateral"))
    arows = []
    tot = p1.LEN_M.sum()
    for t in ["trunk_main", "sub_main", "lateral"]:
        s = p1[p1.TIER_RULE == t]
        arows.append({"package": "5A-1", "sm_threshold_m": t_sm, "tm_threshold_m": t_tm,
                      "tier": t, "pipes": len(s), "km": round(s.LEN_M.sum() / 1000, 2),
                      "share_pct": round(100 * s.LEN_M.sum() / tot, 1),
                      "labelled_zones_touched": s.ZONE2.nunique()})
    # and the same rule re-applied to the labelled packages, for the side-by-side
    lab2 = lab.copy()
    lab2["TIER_RULE"] = np.where(lab2.UP_LEN >= t_tm, "trunk_main",
                                 np.where(lab2.UP_LEN >= t_sm, "sub_main", "lateral"))
    tot2 = lab2.LEN_M.sum()
    for t in ["trunk_main", "sub_main", "lateral"]:
        s = lab2[lab2.TIER_RULE == t]
        a = lab2[lab2.TIER2 == t]
        arows.append({"package": "5A-2..5A-5", "sm_threshold_m": t_sm, "tm_threshold_m": t_tm,
                      "tier": t, "pipes": len(s), "km": round(s.LEN_M.sum() / 1000, 2),
                      "share_pct": round(100 * s.LEN_M.sum() / tot2, 1),
                      "labelled_zones_touched": s.ZONE2.nunique(),
                      "actual_km": round(a.LEN_M.sum() / 1000, 2),
                      "actual_share_pct": round(100 * a.LEN_M.sum() / tot2, 1)})
    put("rule_applied_to_5A1", pd.DataFrame(arows))

    # ============================================ 2. reach and spacing of a sub main
    print("\n2. reach of a sub main")
    # network distance from each lateral pipe to the first non-lateral pipe downstream
    n = len(g)
    tier = g.TIER2.to_numpy()
    length = g.LEN_M.to_numpy(float)
    dist_to_main = np.full(n, np.nan)
    for i in range(n):
        if tier[i] != "lateral":
            dist_to_main[i] = 0.0
            continue
        d, k, guard = 0.0, i, 0
        while k >= 0 and tier[k] == "lateral" and guard < 5000:
            d += length[k]
            k = parent[k]
            guard += 1
        dist_to_main[i] = d if (k >= 0 and tier[k] != "lateral") else np.nan
    g["DIST_TO_MAIN"] = dist_to_main

    rrows = []
    for scope, sub in [("all packages", g[g.TIER2 == "lateral"]),
                       ("5A-2..5A-5", g[(g.TIER2 == "lateral") & (g.PKG != "5A-1")]),
                       ("5A-1 only", g[(g.TIER2 == "lateral") & (g.PKG == "5A-1")])]:
        d = q(sub.DIST_TO_MAIN, ps=(5, 25, 50, 75, 90, 95))
        d["scope"] = scope
        d["reached_a_main_pct"] = round(100 * sub.DIST_TO_MAIN.notna().mean(), 1)
        rrows.append(d)
    put("reach_to_main", pd.DataFrame(rrows).round(1))

    # spacing between sub-main zones: nearest-neighbour distance between their centroids
    sm = g[g.TIER2 == "sub_main"].dissolve(by="ZONE2").reset_index()
    if len(sm) > 1:
        cent = sm.geometry.centroid
        sp = []
        for i in range(len(sm)):
            others = [cent.iloc[k].distance(cent.iloc[i]) for k in range(len(sm)) if k != i]
            sp.append({"zone": sm.ZONE2.iloc[i], "pkg": sm.ZONE2.iloc[i][:4],
                       "nearest_other_submain_m": round(min(others), 0),
                       "len_m": round(sm.geometry.iloc[i].length, 0)})
        put("submain_spacing", pd.DataFrame(sp))

    # how much of a package's area does one sub main serve?
    cov = []
    for z, s in g[g.TIER2 == "sub_main"].groupby("ZONE2"):
        # everything upstream of the sub main's outlet
        outlet = s.sort_values("UP_LEN").iloc[-1]
        cov.append({"zone": z, "pkg": s.PKG.iloc[0],
                    "own_len_m": round(s.LEN_M.sum(), 0),
                    "contributing_len_m": round(outlet.UP_LEN, 0),
                    "contributing_pipes": int(outlet.UP_PIPES),
                    "contributing_props": int(outlet.UP_PROPS),
                    "own_share_of_catchment_pct":
                        round(100 * s.LEN_M.sum() / outlet.UP_LEN, 1)})
    put("submain_catchments", pd.DataFrame(cov))

    # trunk: what joins it, and what does each joiner bring
    tm_nodes = set(g[g.TIER2 == "trunk_main"].US_MHID) | set(g[g.TIER2 == "trunk_main"].DS_MHID)
    inc = g[(g.DS_MHID.isin(tm_nodes)) & (g.TIER2 != "trunk_main")]
    put("trunk_joiners", inc[["FEATUREID", "PKG", "ZONE2", "TIER2", "DS_MHID",
                              "UP_PROPS", "UP_LEN", "UP_PIPES", "DIA_OUT",
                              "SLOPE_PCT", "DEP_DS"]].sort_values(
        "UP_PROPS", ascending=False).round(2))

    sm_nodes = set(g[g.TIER2 == "sub_main"].US_MHID) | set(g[g.TIER2 == "sub_main"].DS_MHID)
    inc2 = g[(g.DS_MHID.isin(sm_nodes)) & (~g.TIER2.isin(["sub_main"]))]
    put("submain_joiners", inc2[["FEATUREID", "PKG", "ZONE2", "TIER2", "DS_MHID",
                                 "UP_PROPS", "UP_LEN", "UP_PIPES"]].sort_values(
        "UP_PROPS", ascending=False).round(2))

    # ============================================ 3. the A / B split inside 5A-1
    print("\n3. A / B inside 5A-1")
    p1b = g[g.PKG == "5A-1"].copy()
    p1b["PREFIX"] = p1b.ZTOK.str.extract(r"^([A-Za-z]+)")[0].fillna("none")
    prows = []
    for pfx, s in p1b.groupby("PREFIX"):
        cent = s.geometry.union_all().centroid
        prows.append({"prefix": pfx, "pipes": len(s), "km": round(s.LEN_M.sum() / 1000, 2),
                      "zones": s.ZONE2.nunique(),
                      "props": int(s.PROPS.sum()),
                      "centroid_e": round(cent.x, 0), "centroid_n": round(cent.y, 0),
                      "max_up_len_m": round(s.UP_LEN.max(), 0),
                      "max_up_props": int(s.UP_PROPS.max())})
    put("pkg5A1_prefixes", pd.DataFrame(prows))

    # do A and B zones ever drain into each other?
    p1b["DS_PREFIX"] = p1b.DS_ZTOK.str.extract(r"^([A-Za-z]+)")[0].fillna("none")
    xt = p1b.groupby(["PREFIX", "DS_PREFIX"]).size().reset_index(name="pipes")
    put("pkg5A1_prefix_flow", xt)

    print("\nDone.")


if __name__ == "__main__":
    main()
