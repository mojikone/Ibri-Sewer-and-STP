"""Two objective tests for the visual impression the pocket renders give.

Reading a dozen images tells you what you saw. These two measurements tell you how far it
generalises, over all 2,211.8 km rather than the twelve frames.

TEST 1 - BUILT OR NOT. W3 classified every plot as built or not (`BUILT_FIN`, 20,399 of
61,272 built). If the skeletoniser is drawing streets in subdivisions that exist only on
the cadastre, its corridors will sit almost entirely among unbuilt plots while the
draftsman's sit among built ones. This measures the built fraction of the plots each
corridor fronts.

TEST 2 - IS THERE A STREET THERE? A street in this landscape reads on the imagery: graded
earth is brighter than the desert beside it, asphalt darker. So for every sample point the
brightness at the corridor is compared with the brightness 12 m either side of it,
perpendicular. A corridor lying in a real street reserve produces a contrast; one lying
across undisturbed ground produces none.

The control is what makes this a measurement rather than a threshold: the same statistic is
computed on `draft` corridors, which are traced from streets that exist, and on random
points in open ground, which are not streets at all. The skeleton is then read against both.

Imagery is LOCAL ONLY and never enters the repository.

Run:  python r4_ground_truth.py
"""
import os
import sys
import time
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import Point, box

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")

IMAGERY = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
OUT_RUN = os.path.join(C.OUT, "run")
FRONT_M = 60.0
STEP_M = 25.0
OFFSET_M = 12.0     # perpendicular distance to the control samples
TILE_M = 4000.0     # imagery read block, in UTM metres


def line_samples(gdf, step=STEP_M):
    """Sample points along every line with the local bearing, for the offset controls."""
    xs, ys, nx_, ny_, own = [], [], [], [], []
    for i, ln in enumerate(gdf.geometry):
        L = ln.length
        n = max(1, int(np.ceil(L / step)))
        for k in range(n):
            d = (k + 0.5) * L / n
            p = ln.interpolate(d)
            a = ln.interpolate(max(0.0, d - 5.0))
            b = ln.interpolate(min(L, d + 5.0))
            dx, dy = b.x - a.x, b.y - a.y
            m = np.hypot(dx, dy)
            if m < 1e-6:
                continue
            xs.append(p.x)
            ys.append(p.y)
            nx_.append(-dy / m)     # unit normal
            ny_.append(dx / m)
            own.append(i)
    return (np.array(xs), np.array(ys), np.array(nx_), np.array(ny_),
            np.array(own, dtype=np.int64))


def brightness(xs, ys):
    """Mean of the three bands at each point, read in blocks so the mosaic is not
    hit once per point. Returns NaN where the mosaic has no tile."""
    pts = gpd.GeoSeries([Point(x, y) for x, y in zip(xs, ys)], crs=C.EPSG).to_crs(3857)
    px = np.array([p.x for p in pts])
    py = np.array([p.y for p in pts])
    out = np.full(len(xs), np.nan)
    with rasterio.open(IMAGERY) as src:
        b = src.bounds
        gx = np.floor((px - b.left) / (TILE_M * 1.85)).astype(int)
        gy = np.floor((py - b.bottom) / (TILE_M * 1.85)).astype(int)
        for key in np.unique(np.stack([gx, gy], 1), axis=0):
            m = (gx == key[0]) & (gy == key[1])
            if not m.any():
                continue
            x0, x1 = px[m].min() - 30, px[m].max() + 30
            y0, y1 = py[m].min() - 30, py[m].max() + 30
            if x1 < b.left or x0 > b.right or y1 < b.bottom or y0 > b.top:
                continue
            win = from_bounds(max(x0, b.left), max(y0, b.bottom),
                              min(x1, b.right), min(y1, b.top), src.transform)
            arr = src.read(window=win, boundless=True, fill_value=0).astype(float)
            tr = src.window_transform(win)
            inv = ~tr
            cc, rr = inv * (px[m], py[m])
            cc = np.clip(cc.astype(int), 0, arr.shape[2] - 1)
            rr = np.clip(rr.astype(int), 0, arr.shape[1] - 1)
            v = arr[:, rr, cc].mean(axis=0)
            v[v <= 1] = np.nan          # mosaic hole
            out[m] = v
    return out


def contrast_test(gdf, label):
    xs, ys, nx_, ny_, own = line_samples(gdf)
    c = brightness(xs, ys)
    a = brightness(xs + OFFSET_M * nx_, ys + OFFSET_M * ny_)
    b = brightness(xs - OFFSET_M * nx_, ys - OFFSET_M * ny_)
    side = np.nanmean(np.stack([a, b]), axis=0)
    d = c - side
    ok = np.isfinite(d)
    print(f"   {label:<12s} {ok.sum():7,d} usable samples of {len(d):,}  "
          f"median |contrast| {np.nanmedian(np.abs(d[ok])):5.2f}  "
          f"p75 {np.nanpercentile(np.abs(d[ok]), 75):5.2f}  "
          f"p90 {np.nanpercentile(np.abs(d[ok]), 90):5.2f}")
    return d[ok], own[ok]


def main():
    t0 = time.time()
    q = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridor_quality.shp"))
    print(f"corridors {len(q):,}, {q.LEN_M.sum()/1000:,.1f} km")

    # ------------------------------------------------------- TEST 1  built or not
    cls = gpd.read_file(os.path.join(
        os.path.dirname(C.OUT), "W3", "shp", "MoH_Plots_class_v4.shp"))
    cls = cls[["BUILT_FIN", "geometry"]].to_crs(C.EPSG)
    print(f"\nplots: {len(cls):,}, built {int(cls.BUILT_FIN.sum()):,} "
          f"({100*cls.BUILT_FIN.mean():.1f} %)")

    buf = q[["geometry"]].copy()
    buf["geometry"] = buf.geometry.buffer(FRONT_M)
    j = gpd.sjoin(cls, buf, how="inner", predicate="intersects")
    agg = j.groupby("index_right").BUILT_FIN.agg(["size", "sum"])
    q["NPLOT"] = agg["size"].reindex(q.index).fillna(0).astype(int)
    q["NBUILT"] = agg["sum"].reindex(q.index).fillna(0).astype(int)
    q["BUILTFRAC"] = np.where(q.NPLOT > 0, q.NBUILT / q.NPLOT.clip(lower=1), np.nan)

    print(f"\nbuilt fraction of the plots each corridor fronts (within {FRONT_M:.0f} m):")
    rows = []
    for src, s in q.groupby("SRC"):
        km = s.LEN_M.sum() / 1000
        noplot = s.loc[s.NPLOT == 0, "LEN_M"].sum() / 1000
        withp = s[s.NPLOT > 0]
        r = {"source": src, "km": round(km, 1),
             "km_no_plot_within_60m": round(noplot, 1),
             "plots_fronted": int(s.NPLOT.sum()),
             "built_pct_of_fronted": round(100 * s.NBUILT.sum() /
                                           max(s.NPLOT.sum(), 1), 1)}
        for lo, hi, name in ((0, 0.001, "km_0pct_built"),
                             (0.001, 0.25, "km_under25pct"),
                             (0.25, 0.75, "km_25to75pct"),
                             (0.75, 1.01, "km_over75pct")):
            m = (withp.BUILTFRAC >= lo) & (withp.BUILTFRAC < hi)
            r[name] = round(withp.loc[m, "LEN_M"].sum() / 1000, 1)
        rows.append(r)
    t1 = pd.DataFrame(rows)
    print(t1.to_string(index=False))
    t1.to_csv(os.path.join(OUT_RUN, "r4_built_status.csv"), index=False)

    # ------------------------------------------------------- TEST 2  is a street there
    print(f"\nbrightness contrast at the corridor vs {OFFSET_M:.0f} m either side")
    rng = np.random.default_rng(7)
    res = {}
    for src in ("draft", "auto_road", "auto_block", "auto_link"):
        sub = q[q.SRC == src]
        if len(sub) > 2500:
            sub = sub.sample(2500, random_state=7)
        res[src] = contrast_test(sub, src)[0]

    # negative control: random points in open ground, at least 100 m from any corridor
    b = q.total_bounds
    pts, tries = [], 0
    allbuf = q.geometry.buffer(100).union_all() if hasattr(q.geometry, "union_all") \
        else q.geometry.buffer(100).unary_union
    while len(pts) < 3000 and tries < 60000:
        x = rng.uniform(b[0], b[2])
        y = rng.uniform(b[1], b[3])
        tries += 1
        p = Point(x, y)
        if not allbuf.contains(p):
            pts.append((x, y))
    pts = np.array(pts)
    ang = rng.uniform(0, np.pi, len(pts))
    c = brightness(pts[:, 0], pts[:, 1])
    a = brightness(pts[:, 0] + OFFSET_M * np.cos(ang), pts[:, 1] + OFFSET_M * np.sin(ang))
    bb = brightness(pts[:, 0] - OFFSET_M * np.cos(ang), pts[:, 1] - OFFSET_M * np.sin(ang))
    dn = c - np.nanmean(np.stack([a, bb]), axis=0)
    dn = dn[np.isfinite(dn)]
    print(f"   {'open ground':<12s} {len(dn):7,d} usable samples          "
          f"median |contrast| {np.nanmedian(np.abs(dn)):5.2f}  "
          f"p75 {np.nanpercentile(np.abs(dn), 75):5.2f}  "
          f"p90 {np.nanpercentile(np.abs(dn), 90):5.2f}")
    res["open_ground"] = dn

    # the threshold is set by the controls, not chosen: the level that 75 % of open
    # ground stays below is what "no street visible" means here.
    thr = float(np.nanpercentile(np.abs(dn), 75))
    print(f"\n   threshold = p75 of open ground = {thr:.2f} brightness units")
    rows = []
    for k, v in res.items():
        rows.append({"set": k, "n": len(v),
                     "median_abs": round(float(np.nanmedian(np.abs(v))), 2),
                     "p90_abs": round(float(np.nanpercentile(np.abs(v), 90)), 2),
                     "pct_above_threshold":
                         round(100 * float(np.mean(np.abs(v) > thr)), 1)})
    t2 = pd.DataFrame(rows)
    print(t2.to_string(index=False))
    t2.to_csv(os.path.join(OUT_RUN, "r4_street_contrast.csv"), index=False)

    q.to_file(os.path.join(C.OUT_SHP, "W10_corridor_quality.shp"))
    print(f"\nBUILTFRAC/NPLOT/NBUILT written back into W10_corridor_quality.shp")
    print(f"total {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
