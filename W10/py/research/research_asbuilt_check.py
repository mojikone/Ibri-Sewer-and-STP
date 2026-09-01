"""W10 research part 2 — run OUR design rules over NAMA's as-built geometry.

Part 1 (`research_hierarchy.py`) established what the as-built hierarchy IS. This part
asks the harder question: where does the as-built DISAGREE with the criteria this project
designs to? It re-sizes every levelled built pipe with the project's own hydraulics
(`W8/py/sewnet/hydra.py`, `criteria.py` — no re-derivation) at the load actually standing
on it today, and compares diameter, gradient, d/D and velocity against what was laid.

Also settles three geometric questions part 1 left open:
  * is a lateral zone a street? (bearing spread, road count, elongation)
  * does the trunk sit low in the ground relative to its own neighbourhood?
  * what does the as-built do at a wadi, using the project's own T50 hazard grid?

RESEARCH ONLY. Run:  python W10/py/research/research_asbuilt_check.py
"""

from __future__ import annotations

import collections
import math
import os
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import MultiPoint

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BASE = os.path.abspath(os.path.join(CLAUDE, "..", ".."))
sys.path.insert(0, os.path.join(CLAUDE, "W8", "py"))

from sewnet import hydra                       # noqa: E402
from sewnet.criteria import DEFAULT as C       # noqa: E402

sys.path.insert(0, HERE)
from research_hierarchy import (               # noqa: E402
    ACCOUNTS, EPSG, PLOTS, ROADS, RUN, SERVE_M, accumulate, build_parent,
    load_network, put, q)

HAZARD = os.path.join(BASE, "Data", "04 Lekhuwair", "Hazard_T50y.tif")
WADI_CLASSES = C.HAZARD_WADI_CLASSES           # (4, 5, 6) — user rule 2026-08-19


def bearing(ln):
    (x0, y0), (x1, y1) = ln.coords[0], ln.coords[-1]
    return math.degrees(math.atan2(y1 - y0, x1 - x0)) % 180.0


def ang_spread(bs):
    """Spread of a set of undirected bearings, in degrees (0-90)."""
    bs = np.asarray(bs, dtype=float)
    if len(bs) < 2:
        return 0.0
    a = np.radians(2 * bs)                     # double angle: 0 and 180 are the same line
    r = math.hypot(np.cos(a).mean(), np.sin(a).mean())
    return math.degrees(math.acos(max(min(r, 1.0), -1.0))) / 2.0


def main():
    print("Loading ...")
    g = load_network()
    acc = gpd.read_file(ACCOUNTS).to_crs(EPSG)
    j = gpd.sjoin_nearest(acc[["geometry", "CATEGORY"]], g[["geometry"]], how="inner",
                          max_distance=SERVE_M, distance_col="d")
    g["PROPS"] = g.index.map(j.groupby("index_right").size()).fillna(0.0)
    parent = build_parent(g)
    up, _ = accumulate(g, parent, g.PROPS)
    g = pd.concat([g, up], axis=1)

    # =================================================== 1. our rules on their geometry
    print("\n1. our sizing rules on the as-built")
    lv = g[(g.HAS_LVL == 1) & g.DIA_OUT.notna() & (g.SLOPE_PCT > 0)].copy()
    hold_mld = C.PF_HOLD_PROPERTIES * C.PLOT_QADF_M3D / 1000.0

    rows = []
    for _, r in lv.iterrows():
        qadf = r.UP_PROPS * C.PLOT_QADF_M3D + C.INFILT_L_D_KM * (r.UP_LEN / 1000.0) / 1000.0
        pf = C.pf_merrimack(max(qadf / 1000.0, hold_mld))
        qpk = qadf * pf / 86400.0                                   # m3/s
        laid = r.SLOPE_PCT / 100.0

        # what the as-built ACTUALLY runs at, on its true bore
        od = int(r.DIA_OUT)
        y_as, v_as = hydra.pipe_state(od, laid, qpk, C)

        # what our rules would have called for
        dn = C.DN_SERIES[0]
        s_req = None
        for _ in range(6):
            s_req = hydra.smin_for(dn, qpk, C)
            dn2, _y, _v = hydra.size_pipe(qpk, s_req, C)
            if dn2 is None:
                dn = C.DN_SERIES[-1]
                break
            if dn2 == dn:
                break
            dn = dn2
        s_req = max(C.TABLE11.get(dn, C.TABLE11_FLOOR), hydra.smin_tractive(qpk, C))

        rows.append({
            "FEATUREID": r.FEATUREID, "PKG": r.PKG, "TIER": r.TIER2,
            "props_up": r.UP_PROPS, "len_up_m": round(r.UP_LEN, 1),
            "qadf_m3d": round(qadf, 2), "pf": round(pf, 2),
            "qpk_ls": round(qpk * 1000, 2),
            "od_built_mm": od, "dn_our_rules": dn,
            "slope_built_pct": round(r.SLOPE_PCT, 3),
            "slope_req_pct": round(s_req * 100, 3),
            "slope_ratio": round(r.SLOPE_PCT / (s_req * 100), 2),
            "dod_built": round(y_as, 3) if y_as is not None else None,
            "v_built_ms": round(v_as, 3) if v_as is not None else None,
            "surcharged": int(y_as is None),
            "dod_limit": hydra.dod_limit(od, C),
            "over_dod": int(y_as is not None and y_as > hydra.dod_limit(od, C)),
            "under_self_cleansing": int(v_as is not None and v_as < C.V_SELF_CLEANSING),
            "over_vmax": int(v_as is not None and v_as > C.V_MAX),
            "depth_ds_m": r.DEP_DS,
        })
    chk = pd.DataFrame(rows)
    put("asbuilt_vs_rules", chk)

    srow = []
    for t, s in chk.groupby("TIER"):
        srow.append({
            "tier": t, "pipes": len(s),
            "od_built": "/".join(str(int(x)) for x in sorted(s.od_built_mm.unique())),
            "dn_our_rules_p50": int(s.dn_our_rules.median()),
            "dn_our_rules_max": int(s.dn_our_rules.max()),
            "our_DN_bigger_pct": round(100 * (s.dn_our_rules > s.od_built_mm).mean(), 1),
            "slope_ratio_p50": round(s.slope_ratio.median(), 2),
            "flatter_than_required_pct": round(100 * (s.slope_ratio < 1).mean(), 1),
            "surcharged_pct": round(100 * s.surcharged.mean(), 1),
            "over_dod_limit_pct": round(100 * s.over_dod.mean(), 1),
            "below_0p75_ms_pct": round(100 * s.under_self_cleansing.mean(), 1),
            "over_3ms_pct": round(100 * s.over_vmax.mean(), 1),
            "dod_p50": round(s.dod_built.median(), 3),
            "dod_p95": round(s.dod_built.quantile(.95), 3),
            "v_p50_ms": round(s.v_built_ms.median(), 2),
        })
    put("asbuilt_vs_rules_summary", pd.DataFrame(srow))

    # the same summary restricted to the zones nearest their outlet (the loaded end)
    worst = chk.sort_values("qpk_ls", ascending=False).head(40)
    put("asbuilt_worst_loaded", worst)

    # =================================================== 2. is a lateral zone a street?
    print("\n2. street test")
    try:
        rd = gpd.read_file(ROADS).set_crs(EPSG, allow_override=True)
        rd = rd.reset_index(names="RID")
        near = gpd.sjoin_nearest(g[["geometry"]], rd[["geometry", "RID", "dual"]],
                                 how="left", max_distance=40, distance_col="rd_d")
        near = near.groupby(near.index).first()
        g["RID"] = near.RID
        g["RD_D"] = near.rd_d
    except Exception as e:                                   # pragma: no cover
        print("  ! roads unavailable:", e)
        g["RID"], g["RD_D"] = np.nan, np.nan

    g["BEAR"] = g.geometry.apply(bearing)
    srows = []
    for z, s in g.groupby("ZONE2"):
        pts = MultiPoint([c for ln in s.geometry for c in ln.coords])
        hull = pts.convex_hull
        ends = [s.geometry.iloc[0].coords[0], s.geometry.iloc[-1].coords[-1]]
        e2e = math.dist(ends[0], ends[1])
        srows.append({"zone": z, "tier": s.TIER2.iloc[0], "pkg": s.PKG.iloc[0],
                      "pipes": len(s), "len_m": round(s.LEN_M.sum(), 1),
                      "bearing_spread_deg": round(ang_spread(s.BEAR), 1),
                      "road_features": int(s.RID.nunique()) if s.RID.notna().any() else 0,
                      "median_road_dist_m": round(s.RD_D.median(), 1)
                      if s.RD_D.notna().any() else None,
                      "hull_ha": round(hull.area / 1e4, 3),
                      "end_to_end_m": round(e2e, 1),
                      "sinuosity": round(s.LEN_M.sum() / e2e, 2) if e2e > 1 else None})
    stz = pd.DataFrame(srows)
    put("zone_street_test", stz)

    agg = []
    for t, s in stz.groupby("tier"):
        for col in ["bearing_spread_deg", "road_features", "median_road_dist_m",
                    "sinuosity", "hull_ha"]:
            d = q(s[col], ps=(5, 25, 50, 75, 95)); d.update({"tier": t, "metric": col})
            agg.append(d)
        agg.append({"tier": t, "metric": "pct_bearing_spread_under_10deg",
                    "n": len(s), "p50": round(100 * (s.bearing_spread_deg < 10).mean(), 1)})
        agg.append({"tier": t, "metric": "pct_on_one_road_feature",
                    "n": len(s), "p50": round(100 * (s.road_features <= 1).mean(), 1)})
        agg.append({"tier": t, "metric": "pct_on_two_or_fewer_road_features",
                    "n": len(s), "p50": round(100 * (s.road_features <= 2).mean(), 1)})
    put("zone_street_stats", pd.DataFrame(agg).round(2))

    # =================================================== 3. does the trunk sit low?
    print("\n3. relative elevation of each tier")
    lvl = g[g.HAS_LVL == 1].copy()
    lvl["mid"] = lvl.geometry.interpolate(0.5, normalized=True)
    mid = gpd.GeoDataFrame(lvl[["TIER2", "US_GRD", "DS_GRD", "PKG"]],
                           geometry=lvl["mid"], crs=EPSG)
    mid["grd"] = lvl[["US_GRD", "DS_GRD"]].mean(axis=1).values
    sidx = mid.sindex
    rel = []
    for radius in (150.0, 300.0):
        vals = []
        for i, geom in enumerate(mid.geometry):
            idx = list(sidx.query(geom.buffer(radius)))
            if len(idx) < 5:
                vals.append(np.nan)
                continue
            nb = mid.grd.iloc[idx]
            vals.append(mid.grd.iat[i] - nb.median())
        mid[f"rel_{int(radius)}"] = vals
        for t, s in mid.groupby("TIER2"):
            d = q(s[f"rel_{int(radius)}"], ps=(5, 25, 50, 75, 95))
            d.update({"tier": t, "radius_m": radius,
                      "metric": "ground level minus local median (m)"})
            rel.append(d)
    put("tier_relative_elevation", pd.DataFrame(rel).round(3))

    # =================================================== 4. wadi, on the project's grid
    print("\n4. wadi behaviour on the T50 hazard grid")
    try:
        with rasterio.open(HAZARD) as src:
            hz_crs = src.crs
            gg = g.to_crs(hz_crs) if hz_crs and hz_crs.to_epsg() != EPSG else g
            samples = []
            for geom in gg.geometry:
                n = max(3, min(20, int(geom.length // 10) + 1))
                pts = [geom.interpolate(t, normalized=True) for t in np.linspace(0, 1, n)]
                vals = [v[0] for v in src.sample([(p.x, p.y) for p in pts])]
                vals = [v for v in vals if v is not None]
                samples.append(vals)
        g["hz_max"] = [max(v) if len(v) else np.nan for v in samples]
        g["hz_wadi_frac"] = [np.mean([x in WADI_CLASSES for x in v]) if len(v) else np.nan
                             for v in samples]
        g["in_wadi"] = (g.hz_wadi_frac > 0).astype(int)
        g["wadi_crossing"] = ((g.hz_wadi_frac > 0) & (g.hz_wadi_frac < 1)).astype(int)
        g["wadi_along"] = (g.hz_wadi_frac >= 0.99).astype(int)

        wrows = []
        for t, s in g.groupby("TIER2"):
            sl = s[s.HAS_LVL == 1]
            wrows.append({
                "tier": t, "pipes": len(s),
                "touching_wadi": int(s.in_wadi.sum()),
                "touching_wadi_pct": round(100 * s.in_wadi.mean(), 1),
                "wholly_in_wadi": int(s.wadi_along.sum()),
                "wholly_in_wadi_pct": round(100 * s.wadi_along.mean(), 2),
                "km_in_wadi": round(s[s.in_wadi == 1].LEN_M.sum() / 1000, 2),
                "median_depth_in_wadi":
                    round(sl[sl.in_wadi == 1][["DEP_US", "DEP_DS"]].mean(axis=1).median(), 2)
                    if (sl.in_wadi == 1).any() else None,
                "median_depth_outside":
                    round(sl[sl.in_wadi == 0][["DEP_US", "DEP_DS"]].mean(axis=1).median(), 2)
                    if (sl.in_wadi == 0).any() else None,
                "median_grad_in_wadi_mm_m":
                    round((sl[sl.in_wadi == 1].SLOPE_PCT * 10).median(), 2)
                    if (sl.in_wadi == 1).any() else None,
                "median_grad_outside_mm_m":
                    round((sl[sl.in_wadi == 0].SLOPE_PCT * 10).median(), 2)
                    if (sl.in_wadi == 0).any() else None,
                "median_run_in_wadi_m":
                    round(s[s.in_wadi == 1].LEN_M.median(), 1) if (s.in_wadi == 1).any() else None,
                "median_run_outside_m":
                    round(s[s.in_wadi == 0].LEN_M.median(), 1) if (s.in_wadi == 0).any() else None,
            })
        put("wadi_hazard", pd.DataFrame(wrows))

        cls = g.groupby(pd.cut(g.hz_max, [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
                               labels=["0", "1", "2", "3", "4", "5", "6"]),
                        observed=True).agg(
            pipes=("FEATUREID", "size"), km=("LEN_M", lambda x: round(x.sum() / 1000, 2)),
            trunk=("TIER2", lambda s: int((s == "trunk_main").sum())),
            sub_main=("TIER2", lambda s: int((s == "sub_main").sum())),
            lateral=("TIER2", lambda s: int((s == "lateral").sum()))).reset_index()
        cls.columns = ["hazard_class_max"] + list(cls.columns[1:])
        put("wadi_hazard_classes", cls)
    except Exception as e:                                   # pragma: no cover
        print("  ! hazard analysis skipped:", e)

    # =================================================== 5. drop connections
    print("\n5. drop connections at chambers")
    rows = []
    for i in range(len(g)):
        p = parent[i]
        if p < 0:
            continue
        a, b = g.DS_INV.iat[i], g.US_INV.iat[p]
        if pd.isna(a) or pd.isna(b):
            continue
        rows.append({"drop_m": a - b, "tier_in": g.TIER2.iat[i],
                     "tier_out": g.TIER2.iat[p], "pkg": g.PKG.iat[i],
                     "in_wadi": int(g.get("in_wadi", pd.Series(0, index=g.index)).iat[p])})
    dp = pd.DataFrame(rows)
    drows = []
    for t, s in dp.groupby("tier_out"):
        drows.append({
            "receiving_tier": t, "connections_with_levels": len(s),
            "drop_ge_0p10m": int((s.drop_m >= 0.10).sum()),
            "drop_ge_0p60m_backdrop_G203p30": int((s.drop_m >= 0.60).sum()),
            "pct_ge_0p60m": round(100 * (s.drop_m >= 0.60).mean(), 1),
            "drop_ge_2p00m_needs_vortex": int((s.drop_m >= 2.00).sum()),
            "max_drop_m": round(s.drop_m.max(), 2),
            "adverse_connections": int((s.drop_m < -0.01).sum())})
    drows.append({
        "receiving_tier": "ALL", "connections_with_levels": len(dp),
        "drop_ge_0p10m": int((dp.drop_m >= 0.10).sum()),
        "drop_ge_0p60m_backdrop_G203p30": int((dp.drop_m >= 0.60).sum()),
        "pct_ge_0p60m": round(100 * (dp.drop_m >= 0.60).mean(), 1),
        "drop_ge_2p00m_needs_vortex": int((dp.drop_m >= 2.00).sum()),
        "max_drop_m": round(dp.drop_m.max(), 2),
        "adverse_connections": int((dp.drop_m < -0.01).sum())})
    put("drop_connections", pd.DataFrame(drows))

    print("\nDone.")


if __name__ == "__main__":
    main()
