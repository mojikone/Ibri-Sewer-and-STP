# -*- coding: utf-8 -*-
"""BUILT_IMG classification from Esri mosaic texture, calibrated on BUILT_MS labels.
Features per plot (grayscale, 1.19 m/px): intensity std, edge density, shadow fraction, bright-structure fraction.
Train: positives = BUILT_MS=1 plots in IBRI; negatives = BUILT_MS=0 plots in AT TAYYIB.
Output: W3/shp/MoH_Plots_built_v2.shp with BUILT_MS, BUILT_IMG, BUILT_FIN, SRC."""
import os, json
import numpy as np
import shapefile
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from shapely.geometry import shape
from shapely.ops import transform as shp_t
from rasterio.warp import transform as rio_transform

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
MOS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
W3 = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W3"

built_ms = np.load(SCR + r"\built.npy")
cent = np.load(SCR + r"\plot_cent.npy")

ds = rasterio.open(MOS)

def to_3857(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:32640", "EPSG:3857", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)

def feats(g3857):
    b = g3857.bounds
    if (b[2] - b[0]) < 6 or (b[3] - b[1]) < 6: return None
    try:
        w = from_bounds(b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3, ds.transform)
        a = ds.read(window=w, boundless=True, fill_value=0).astype(np.float32)
    except Exception:
        return None
    if a.shape[1] < 5 or a.shape[2] < 5: return None
    gray = 0.299 * a[0] + 0.587 * a[1] + 0.114 * a[2]
    try:
        tr = ds.window_transform(w)
        m = geometry_mask([g3857.__geo_interface__], out_shape=gray.shape, transform=tr, invert=True)
    except Exception:
        return None
    if m.sum() < 16: return None
    v = gray[m]
    if np.all(v == 0): return None
    gx = np.abs(np.diff(gray, axis=1)); gy = np.abs(np.diff(gray, axis=0))
    em = np.zeros_like(gray); em[:, :-1] += gx; em[:-1, :] += gy
    e = em[m]
    med = np.median(v)
    return [np.std(v),                       # intensity variety
            np.mean(e),                      # edge energy
            float((v < med - 35).mean()),    # shadow fraction
            float((v > med + 35).mean()),    # bright structure fraction
            float((e > 40).mean())]          # strong-edge density

r = shapefile.Reader(PLOTS)
n = len(r)
F = np.full((n, 5), np.nan, dtype=np.float32)
geoms3857 = []
for i, s in enumerate(r.iterShapes()):
    try:
        g = to_3857(shape(s.__geo_interface__))
        ft = feats(g)
        if ft: F[i] = ft
    except Exception:
        pass
    if i % 5000 == 0: print(i, "...", flush=True)
np.save(SCR + r"\img_feats.npy", F)
ok = ~np.isnan(F[:, 0])
print("plots with features:", int(ok.sum()), "/", n)

# ---- training sets from zone membership ----
zones_geo = json.load(open(SCR + r"\zones_utm.json"))  # name -> wkt-ish coords, prepared earlier
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.strtree import STRtree
zs = {}
for nm, coords in zones_geo.items():
    polys = [Polygon(c) for c in coords]
    zs[nm] = MultiPolygon(polys) if len(polys) > 1 else polys[0]
pts = [Point(*c) for c in cent]
tree = STRtree(pts)
def zone_idx(nm):
    return list(tree.query(zs[nm], predicate="contains"))
ibri = np.array(zone_idx("IBRI"))
tayy = np.array(zone_idx("AT TAYYIB"))
pos = ibri[(built_ms[ibri] == 1) & ok[ibri]]
neg = tayy[(built_ms[tayy] == 0) & ok[tayy]]
print("train pos/neg:", len(pos), len(neg))

X = F[np.concatenate([pos, neg])]
y = np.concatenate([np.ones(len(pos)), np.zeros(len(neg))])
mu, sd = np.nanmean(X, 0), np.nanstd(X, 0) + 1e-6
Xn = (X - mu) / sd
# simple logistic regression (gradient descent)
wts = np.zeros(6)
Xb = np.hstack([Xn, np.ones((len(Xn), 1))])
for it in range(3000):
    p = 1 / (1 + np.exp(-Xb @ wts))
    grad = Xb.T @ (p - y) / len(y)
    wts -= 0.5 * grad
p = 1 / (1 + np.exp(-Xb @ wts))
acc = ((p > 0.5) == y).mean()
print("train acc:", round(float(acc), 3), "weights:", np.round(wts, 2))

# apply to all
Fa = (F - mu) / sd
Pa = 1 / (1 + np.exp(-(np.hstack([Fa, np.ones((n, 1))]) @ wts)))
built_img = np.where(ok, (Pa > 0.5).astype(int), -1)
np.save(SCR + r"\built_img.npy", built_img)
# combined: MS positive wins; else image; -1 = unclassified
built_fin = np.where(built_ms == 1, 1, np.where(built_img >= 0, built_img, 0))
src = np.where(built_ms == 1, 1, np.where(built_img >= 0, 2, 0))  # 1=MS,2=IMG,0=none
print("BUILT_FIN=1:", int((built_fin == 1).sum()), f"({100*(built_fin==1).mean():.1f}%)")

# holdout check: covered zones with plausible MS (AD DIBAYSHI etc.) — agreement img vs ms
for nm in ["AD DIBAYSHI", "AL JIBAYYAH", "HIJAR", "SUWAYDA AL MA"]:
    zi = np.array(zone_idx(nm))
    zi = zi[ok[zi]]
    if len(zi) == 0: continue
    agree = (built_img[zi] == built_ms[zi]).mean()
    print(f"agreement img-vs-MS in {nm}: {100*agree:.1f}%  (n={len(zi)})")

# write v2 shapefile
w = shapefile.Writer(os.path.join(W3, "shp", "MoH_Plots_built_v2"), shapeType=r.shapeType)
w.field("OBJECTID", "N", 12); w.field("LANDUSE", "C", 30); w.field("VILLAGE_EN", "C", 40)
w.field("BUILT_MS", "N", 1); w.field("BUILT_IMG", "N", 2); w.field("BUILT_FIN", "N", 1); w.field("SRC", "N", 1)
fields = [f[0] for f in r.fields[1:]]
i_id = fields.index("OBJECTID"); i_lu = fields.index("LANDUSE"); i_ve = fields.index("VILLAGE_EN")
for i, sr in enumerate(r.iterShapeRecords()):
    w.shape(sr.shape)
    w.record(sr.record[i_id], str(sr.record[i_lu])[:30], str(sr.record[i_ve])[:40],
             int(built_ms[i]), int(built_img[i]), int(built_fin[i]), int(src[i]))
w.close()
import shutil
shutil.copy(os.path.join(W3, "shp", "MoH_Plots_built.prj"), os.path.join(W3, "shp", "MoH_Plots_built_v2.prj"))
print("v2 shapefile written")
