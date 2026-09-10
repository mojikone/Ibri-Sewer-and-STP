# Vegetation fraction per plot of the 7 Sept MoH file, from the z17 RGB mosaic (excess-green index) — the W3 method (W3/py/vegfrac.py) on the new plots.
import numpy as np, rasterio, os, csv, time
from rasterio.windows import from_bounds
from rasterio.features import geometry_mask
from rasterio.warp import transform as rio_transform
from shapely.ops import transform as shp_t
import geopandas as gpd
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
MOS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
plots = gpd.read_file(f"{W13}/shp/PLOTS_load.shp", columns=['Name'])
ds = rasterio.open(MOS)
def to_3857(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]; ys = list(y) if hasattr(y, "__iter__") else [y]
        return rio_transform("EPSG:32640", "EPSG:3857", xs, ys)
    return shp_t(f, geom)
n = len(plots); veg = np.full(n, -1.0, dtype=np.float32); t0 = time.time()
for i, geom in enumerate(plots.geometry):
    try:
        g = to_3857(geom); b = g.bounds
        if (b[2] - b[0]) < 5 or (b[3] - b[1]) < 5: continue
        w = from_bounds(b[0] - 2, b[1] - 2, b[2] + 2, b[3] + 2, ds.transform)
        a = ds.read(window=w, boundless=True, fill_value=0).astype(np.float32)
        if a.shape[1] < 4 or a.shape[2] < 4: continue
        tr = ds.window_transform(w)
        m = geometry_mask([g.__geo_interface__], out_shape=a.shape[1:], transform=tr, invert=True)
        if m.sum() < 12: continue
        R, G, B = a[0][m], a[1][m], a[2][m]
        if np.all(G == 0): continue
        exg = 2 * G - R - B; dark = (R + G + B) / 3 < 90
        veg[i] = float(((exg > 18) | (dark & (G >= R))).mean())
    except Exception:
        pass
    if i % 10000 == 0: print(i, '...', round(time.time() - t0), 's', flush=True)
np.save(f"{W13}/analysis/vegfrac_plots.npy", veg)
with open(f"{W13}/analysis/vegfrac_plots.csv", 'w', newline='') as fh:
    cw = csv.writer(fh); cw.writerow(['fid', 'VEGFRAC']); cw.writerows((i, round(float(v), 3)) for i, v in enumerate(veg))
print('plots with vegfrac:', int((veg >= 0).sum()), 'of', n, '| DONE', round(time.time() - t0), 's')
