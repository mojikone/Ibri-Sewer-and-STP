"""Numbers for the study-area section of the concept report: ground levels, roads, climate, wind.

Reads the frozen W14 plot layer, the 0.5 m terrain, the road centrelines as supplied and the NASA
POWER record fetched by fetch_climate_power.py; writes study_area_stats.json, which the report
reads through report/facts_area.py. Nothing here changes a load.

    python study_area_stats.py
"""
import json, os, math
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))            # Hydraulic/Claude
HYD = os.path.dirname(REPO)                                              # Hydraulic
TERRAIN = os.path.join(HYD, "Terrain", "Sat_0p5m", "IBRI_0p5_clip.tif")
TERRAIN_ALL = os.path.join(HYD, "Terrain", "Sat_0p5m", "IBRI_0p5_VRT2.vrt")   # where the clip has no value
ROADS = os.path.join(HYD, "SHP", "Road centerline 2", "Road_Centercline.shp")
PLOTS = os.path.join(REPO, "W14", "shp", "PLOTS_load.shp")
STP = (444387.0, 2563352.0)


def sample(points):
    """Ground level at each point from the 0.5 m clip, from the full mosaic where the clip is empty."""
    z = np.full(len(points), np.nan)
    with rasterio.open(TERRAIN) as r:
        nod = r.nodata
        for i, v in enumerate(r.sample(points)):
            if v[0] != nod and np.isfinite(v[0]) and v[0] > -100:
                z[i] = float(v[0])
    miss = np.where(np.isnan(z))[0]
    if len(miss):
        with rasterio.open(TERRAIN_ALL) as r:
            nod = r.nodata
            for i, v in zip(miss, r.sample([points[k] for k in miss])):
                if v[0] != nod and np.isfinite(v[0]) and v[0] > -100:
                    z[i] = float(v[0])
    return z


def ground():
    import sys
    sys.path.insert(0, os.path.join(REPO, "W16", "report"))
    import facts_w14 as F
    g = gpd.read_file(PLOTS)
    c = g.geometry.representative_point()
    pts = list(zip(c.x, c.y))
    g["Z"] = sample(pts); g["X"] = c.x; g["Y"] = c.y
    built = g[(g["N_ACC"] > 0) & g["Z"].notna()]
    rows = []
    for key, s in built.groupby("SETTLE"):
        w = s["POP"].clip(lower=0) + 1e-6
        cx, cy = float(np.average(s["X"], weights=w)), float(np.average(s["Y"], weights=w))
        rows.append({"key": key, "name": F.NAME.get(key, key.title()), "built_plots": int(len(s)), "pop_2024": float(s["POP"].sum()),
                     "z_med": float(s["Z"].median()), "z_p10": float(s["Z"].quantile(0.10)), "z_p90": float(s["Z"].quantile(0.90)),
                     "dist_km": math.hypot(cx - STP[0], cy - STP[1]) / 1000.0,
                     # compass bearing from the STP to the settlement; the wind that carries odour
                     # from the STP to it blows FROM the opposite bearing
                     "bearing_deg": (math.degrees(math.atan2(cx - STP[0], cy - STP[1])) + 360.0) % 360.0})
    z_stp = float(sample([STP])[0])
    allz = g["Z"].dropna()
    return {"stp_ground": z_stp, "plots_sampled": int(allz.size), "plots_total": int(len(g)),
            "z_min": float(allz.min()), "z_max": float(allz.max()), "z_p01": float(allz.quantile(0.01)), "z_p99": float(allz.quantile(0.99)),
            "built_z_min": float(built["Z"].min()), "built_z_max": float(built["Z"].max()),
            "settlements": sorted(rows, key=lambda r: r["dist_km"])}


def roads():
    import glob
    r = gpd.read_file(ROADS)
    bnd = None
    for cand in glob.glob(os.path.join(HYD, "SHP", "**", "*oundary*updated*.shp"), recursive=True) + \
            glob.glob(os.path.join(REPO, "W16", "deliverables", "**", "*oundary*pdated*.shp"), recursive=True):
        bnd = gpd.read_file(cand).to_crs(r.crs); src = cand; break
    inside = gpd.clip(r, bnd) if bnd is not None else r
    inside = inside.assign(KM=inside.geometry.length / 1000.0)
    by = inside.groupby(inside["StrCls"].fillna("none"))["KM"].sum().to_dict()
    dual = float(inside.loc[inside["dual"] == 1, "KM"].sum())
    return {"boundary_used": os.path.relpath(src, HYD) if bnd is not None else None, "total_km": float(inside["KM"].sum()),
            "all_features_km": float(r.geometry.length.sum() / 1000.0), "by_class_km": {str(k): float(v) for k, v in by.items()},
            "dual_centreline_km": dual, "features": int(len(inside))}


def climate():
    d = pd.read_csv(os.path.join(HERE, "climate", "power_daily_2001_2024.csv"), parse_dates=["date"])
    d = d[(d["t_mean_c"] > -90) & (d["rain_mm"] > -90)]
    d["m"] = d["date"].dt.month; d["y"] = d["date"].dt.year
    # 2001 to 2020, the period of POWER's own climatology. The record after it is not used: it
    # carries 790 mm for August 2024 at this point (seven days of 65 to 113 mm), which did not
    # happen, while the storm of April 2024 shows as 59 mm. Checked 2026-09-17.
    d = d[d["y"] <= 2020]
    mon = d.groupby("m").agg(t_max=("t_max_c", "mean"), t_mean=("t_mean_c", "mean"), t_min=("t_min_c", "mean"))
    rain_my = d.groupby(["y", "m"])["rain_mm"].sum().groupby("m").mean()
    ann = d.groupby("y")["rain_mm"].sum()
    out = {"years": [int(d["y"].min()), int(d["y"].max())],
           "monthly": [{"m": int(m), "t_max": float(mon.loc[m, "t_max"]), "t_mean": float(mon.loc[m, "t_mean"]),
                        "t_min": float(mon.loc[m, "t_min"]), "rain": float(rain_my.loc[m])} for m in range(1, 13)],
           "t_mean_annual": float(d["t_mean_c"].mean()), "t_abs_max": float(d["t_max_c"].max()), "t_abs_min": float(d["t_min_c"].min()),
           "rain_annual_mean": float(ann.mean()), "rain_annual_min": float(ann.min()), "rain_annual_max": float(ann.max()),
           "rain_year_min": int(ann.idxmin()), "rain_year_max": int(ann.idxmax()),
           "days_over_40": float((d["t_max_c"] >= 40).groupby(d["y"]).sum().mean())}
    # Koeppen-Geiger, from these values: arid when annual rain is below the threshold, desert below half of it
    t = out["t_mean_annual"]; p = out["rain_annual_mean"]
    summer = sum(r["rain"] for r in out["monthly"] if r["m"] in (4, 5, 6, 7, 8, 9)) / max(p, 1e-9)
    thr = 20 * t + (280 if summer >= 0.7 else 140 if summer >= 0.3 else 0)
    out["koppen"] = {"threshold_mm": float(thr), "summer_share": float(summer), "class": "BWh" if (p < 0.5 * thr and t >= 18) else "check"}
    return out


def wind():
    h = pd.read_csv(os.path.join(HERE, "climate", "power_hourly_wind_2015_2024.csv"), parse_dates=["time_lst"])
    h = h[(h["ws10m_ms"] >= 0) & (h["wd10m_deg"] >= 0)]
    h["hour"] = h["time_lst"].dt.hour; h["m"] = h["time_lst"].dt.month
    sectors = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    h["sec"] = ((h["wd10m_deg"] + 11.25) // 22.5).astype(int) % 16
    bins = [0, 2, 4, 6, 8, 100]; labels = ["0-2", "2-4", "4-6", "6-8", ">8"]
    h["cls"] = pd.cut(h["ws10m_ms"], bins=bins, labels=labels, right=False)

    def rose(sub):
        n = len(sub)
        tab = sub.groupby(["sec", "cls"], observed=False).size().unstack(fill_value=0).reindex(range(16), fill_value=0)
        return {"hours": int(n), "mean_speed": float(sub["ws10m_ms"].mean()), "calm_share": float((sub["ws10m_ms"] < 1.0).mean()),
                "share": {sectors[i]: {c: float(tab.loc[i, c]) / n for c in labels} for i in range(16)},
                "sector_total": {sectors[i]: float(tab.loc[i].sum()) / n for i in range(16)}}
    night = h[(h["hour"] >= 20) | (h["hour"] < 6)]
    day = h[(h["hour"] >= 6) & (h["hour"] < 20)]
    return {"years": [int(h["time_lst"].dt.year.min()), int(h["time_lst"].dt.year.max())], "sectors": sectors, "classes": labels,
            "all": rose(h), "day": rose(day), "night": rose(night),
            "summer": rose(h[h["m"].isin([5, 6, 7, 8, 9])]), "winter": rose(h[h["m"].isin([11, 12, 1, 2, 3])]),
            "monthly_mean_speed": {int(m): float(v) for m, v in h.groupby("m")["ws10m_ms"].mean().items()},
            "p95_speed": float(h["ws10m_ms"].quantile(0.95)), "max_speed": float(h["ws10m_ms"].max())}


if __name__ == "__main__":
    import sys
    parts = sys.argv[1:] or ["ground", "roads", "climate", "wind"]
    path = os.path.join(HERE, "study_area_stats.json")
    out = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    for p in parts:
        print("..", p); out[p] = {"ground": ground, "roads": roads, "climate": climate, "wind": wind}[p]()
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1)
    print("wrote", path)
