# -*- coding: utf-8 -*-
"""Per-plot vegetation fraction from z17 RGB mosaic (excess-green index)."""
import numpy as np, shapefile, rasterio, os
from rasterio.windows import from_bounds
from rasterio.features import geometry_mask
from shapely.geometry import shape
from shapely.ops import transform as shp_t
from rasterio.warp import transform as rio_transform

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
MOS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
ds = rasterio.open(MOS)

def to_3857(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:32640", "EPSG:3857", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)

r = shapefile.Reader(PLOTS)
n = len(r)
veg = np.full(n, -1.0, dtype=np.float32)
for i, s in enumerate(r.iterShapes()):
    try:
        g = to_3857(shape(s.__geo_interface__))
        b = g.bounds
        if (b[2] - b[0]) < 5 or (b[3] - b[1]) < 5: continue
        w = from_bounds(b[0] - 2, b[1] - 2, b[2] + 2, b[3] + 2, ds.transform)
        a = ds.read(window=w, boundless=True, fill_value=0).astype(np.float32)
        if a.shape[1] < 4 or a.shape[2] < 4: continue
        tr = ds.window_transform(w)
        m = geometry_mask([g.__geo_interface__], out_shape=a.shape[1:], transform=tr, invert=True)
        if m.sum() < 12: continue
        R, G, B = a[0][m], a[1][m], a[2][m]
        if np.all(G == 0): continue
        exg = 2 * G - R - B                      # excess green
        dark = (R + G + B) / 3 < 90              # groves are dark
        veg[i] = float(((exg > 18) | (dark & (G >= R))).mean())
    except Exception:
        pass
    if i % 10000 == 0: print(i, "...", flush=True)
np.save(SCR + r"\vegfrac.npy", veg)
ok = veg >= 0
print("plots with vegfrac:", int(ok.sum()))
# calibration read-out: distribution by known landuse
lus = [str(rec.as_dict().get("LANDUSE") or "").strip() for rec in r.iterRecords()]
lus = np.array(lus)
for lab, mask in [("agri", lus == "زراعى"), ("residential", lus == "سكني"), ("empty", lus == "")]:
    v = veg[mask & ok]
    if len(v):
        print(lab, "n=", len(v), "p25/p50/p75/p90:", [round(float(np.percentile(v, q)), 2) for q in (25, 50, 75, 90)])
