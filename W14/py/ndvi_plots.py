# Sentinel-2 NDVI per plot (engineer 2026-09-10: palms are evergreen, so one dry-season scene is enough).
# 1. read the Ibri window of red (B04) and near-infrared (B08) straight from the public Sentinel-2 COG bucket on AWS (no login)
# 2. NDVI raster, 10 m, saved OUTSIDE the repo under Hydraulic/Imagery (imagery is never pushed)
# 3. per plot: mean NDVI, share of pixels with NDVI >= 0.30, and the green area in m2
# 4. calibration: farm-meter plots (positives) vs pure home plots without a farm meter (negatives)
import json, os, sys, time, numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
IMG = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Imagery"
SC = "C:/Users/mojtaba/AppData/Local/Temp/claude/D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude/4c6c2c7b-00c3-4e9a-b8fc-2e647a78c88a/scratchpad/s2_scenes.json"
def _zonal(args):
    tif, geoms, green_t = args
    with rasterio.open(tif) as d:
        arr = d.read(1); tr = d.transform
    out = []
    for g in geoms:
        b = g.bounds
        w = from_bounds(b[0] - 10, b[1] - 10, b[2] + 10, b[3] + 10, tr).round_offsets().round_lengths()
        r0, c0 = int(w.row_off), int(w.col_off); r1, c1 = r0 + int(w.height), c0 + int(w.width)
        if r0 < 0 or c0 < 0 or r1 > arr.shape[0] or c1 > arr.shape[1]: out.append((np.nan, np.nan, 0.0, 0)); continue
        sub = arr[r0:r1, c0:c1]
        if sub.size == 0: out.append((np.nan, np.nan, 0.0, 0)); continue
        wt = from_origin(tr.c + c0 * tr.a, tr.f + r0 * tr.e, tr.a, -tr.e)
        m = geometry_mask([g.__geo_interface__], out_shape=sub.shape, transform=wt, invert=True, all_touched=True)
        v = sub[m]; v = v[np.isfinite(v)]
        if v.size == 0: out.append((np.nan, np.nan, 0.0, 0)); continue
        sh = float((v >= green_t).mean())
        out.append((float(v.mean()), sh, sh * min(g.area, v.size * 100.0), int(v.size)))
    return out


if __name__ == '__main__':
    scene_id = sys.argv[1] if len(sys.argv) > 1 else "S2B_40QDL_20260909_0_L2A"
    rows = json.load(open(SC)); sc = [r for r in rows if r[1] == scene_id][0]
    date, red_href, nir_href = sc[0], sc[5], sc[6]
    # window = project boundary bbox + 1 km, in the scene's CRS (UTM 40N, same as the plots)
    xmin, ymin, xmax, ymax = 430500, 2555400, 479100, 2583000
    out_tif = f"{IMG}/S2_NDVI_ibri_{date.replace('-', '')}.tif"
    t0 = time.time()
    if not os.path.exists(out_tif):
        os.environ.update({"GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR", "AWS_NO_SIGN_REQUEST": "YES", "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif"})
        with rasterio.open(red_href) as r, rasterio.open(nir_href) as n:
            assert r.crs.to_epsg() == 32640, r.crs
            w = from_bounds(xmin, ymin, xmax, ymax, r.transform)
            red = r.read(1, window=w).astype(np.float32); nir = n.read(1, window=w).astype(np.float32)
            tr = r.window_transform(w)
            nodata = (red == 0) & (nir == 0)
            print('window px', red.shape, 'nodata share %.3f' % nodata.mean(), 'fetched in', round(time.time() - t0), 's', flush=True)
            # L2A COGs are scaled reflectance (offset applied since 2022: value = 10000*R + 1000); NDVI is offset-free after subtracting 1000
            red = np.clip(red - 1000, 0, None); nir = np.clip(nir - 1000, 0, None)      # reflectance cannot be negative; without the clip NDVI ran above 1 on dark groves
            ndvi = np.where(nodata, np.nan, (nir - red) / np.maximum(nir + red, 1)).astype(np.float32)
            with rasterio.open(out_tif, 'w', driver='GTiff', height=ndvi.shape[0], width=ndvi.shape[1], count=1, dtype='float32', crs='EPSG:32640', transform=tr, nodata=np.nan, compress='deflate') as d:
                d.write(ndvi, 1)
        print('saved', out_tif, flush=True)
    with rasterio.open(out_tif) as d:
        ndvi = d.read(1); tr = d.transform
    print('NDVI valid %.3f, p50 %.2f p90 %.2f p99 %.2f' % (np.isfinite(ndvi).mean(), *np.nanpercentile(ndvi, [50, 90, 99])), flush=True)

    plots = gpd.read_file(f"{W13}/shp/PLOTS_load.shp")
    n = len(plots); GREEN_T = 0.30; t0 = time.time()
    from concurrent.futures import ProcessPoolExecutor
    NW = max(1, (os.cpu_count() or 4) - 1); CH = 2000
    chunks = [(out_tif, list(plots.geometry[i:i + CH]), GREEN_T) for i in range(0, n, CH)]
    res = []
    with ProcessPoolExecutor(NW) as ex:
        for k, part in enumerate(ex.map(_zonal, chunks)):
            res.extend(part)
            if k % 10 == 0: print(k * CH, '...', round(time.time() - t0), 's', NW, 'workers', flush=True)
    res = np.array(res, dtype=np.float64)
    mean, share, garea, npx = res[:, 0].astype(np.float32), res[:, 1].astype(np.float32), res[:, 2].astype(np.float32), res[:, 3].astype(np.int32)
    plots['NDVI_MEAN'] = mean.round(3); plots['NDVI_SHARE'] = share.round(3); plots['GREEN_M2'] = garea.round(0); plots['NDVI_PX'] = npx
    pd.DataFrame({'fid': range(n), 'NDVI_MEAN': plots.NDVI_MEAN, 'NDVI_SHARE': plots.NDVI_SHARE, 'GREEN_M2': plots.GREEN_M2, 'NDVI_PX': npx}).to_csv(f"{W13}/analysis/ndvi_plots.csv", index=False)
    print('plots with NDVI:', int(np.isfinite(mean).sum()), 'of', n, 'in', round(time.time() - t0), 's', flush=True)

    # ---------- calibration ----------
    built = plots.Buiding_St == 'EXisting'
    pos = built & (plots.G_AGR > 0)                                                   # farm meter on the plot
    neg = built & (plots.DERIVED == 'Residential') & (plots.G_AGR == 0) & (plots.HIGH == 0)
    print('positives (farm meter, built):', int(pos.sum()), '| negatives (pure home, no farm meter):', int(neg.sum()))
    for col in ('NDVI_MEAN', 'NDVI_SHARE', 'GREEN_M2'):
        print(col, 'farm p10/p25/p50/p75:', np.nanpercentile(plots.loc[pos, col], [10, 25, 50, 75]).round(3), '| home p50/p75/p90/p95:', np.nanpercentile(plots.loc[neg, col], [50, 75, 90, 95]).round(3))
    print('\nthreshold sweep on NDVI_MEAN (farm caught % | homes wrongly farm %):')
    for t in (0.15, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30, 0.35):
        tp = (plots.loc[pos, 'NDVI_MEAN'] >= t).mean() * 100; fp = (plots.loc[neg, 'NDVI_MEAN'] >= t).mean() * 100
        print(f'  {t:.2f}: {tp:5.1f} | {fp:5.1f}')
    print('\nthreshold sweep on GREEN_M2 (pixels >= 0.30) (farm caught % | homes wrongly farm %):')
    for t in (300, 500, 800, 1000, 1500, 2000, 3000):
        tp = (plots.loc[pos, 'GREEN_M2'] >= t).mean() * 100; fp = (plots.loc[neg, 'GREEN_M2'] >= t).mean() * 100
        print(f'  {t:5d}: {tp:5.1f} | {fp:5.1f}')
    print('\nby plot area, farm p50 NDVI_MEAN / home p90:')
    for lo, hi in ((0, 800), (800, 2000), (2000, 5000), (5000, 1e9)):
        a = (plots.AREA_M2 >= lo) & (plots.AREA_M2 < hi)
        print(f'  {lo:>5.0f}-{hi:<7.0f} farms {int((pos & a).sum()):4d} p50 {np.nanmedian(plots.loc[pos & a, "NDVI_MEAN"]) if (pos & a).any() else float("nan"):.3f} | homes {int((neg & a).sum()):5d} p90 {np.nanpercentile(plots.loc[neg & a, "NDVI_MEAN"], 90) if (neg & a).any() else float("nan"):.3f}')
    print('DONE')
