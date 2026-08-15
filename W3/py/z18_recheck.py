# -*- coding: utf-8 -*-
"""z18 recheck: re-classify BUILT_FIN=0 plots at 0.6 m/px. Writes v3 shapefile + stats."""
import os, math, json, time
import urllib.request
import numpy as np
import shapefile
from shapely.geometry import shape, Polygon, MultiPolygon, Point
from shapely.strtree import STRtree
from shapely.ops import transform as shp_t
from rasterio.warp import transform as rio_transform
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

Z = 18
TD = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z18_tiles"
SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
W3 = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W3"
URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
n = 2 ** Z
ORIG = 2 * math.pi * 6378137 / 2.0
RES = 2 * ORIG / n / 256

built_ms = np.load(SCR + r"\built.npy")
built_img = np.load(SCR + r"\built_img.npy")
built_fin = np.where(built_ms == 1, 1, np.where(built_img >= 0, built_img, 0))
cent = np.load(SCR + r"\plot_cent.npy")

def m2t(x, y):
    return int((x + ORIG) / (2 * ORIG) * n), int((ORIG - y) / (2 * ORIG) * n)

_cache = {}
def get_tile(tx, ty):
    k = (tx, ty)
    if k in _cache: return _cache[k]
    fp = os.path.join(TD, f"{Z}_{tx}_{ty}.jpg")
    a = None
    if os.path.exists(fp) and os.path.getsize(fp) > 500:
        try: a = np.asarray(Image.open(fp).convert("L"), dtype=np.float32)
        except Exception: a = None
    if len(_cache) > 4000: _cache.clear()
    _cache[k] = a
    return a

def crop(b3857):
    x0, y0, x1, y1 = b3857
    tx0, ty1 = m2t(x0, y0); tx1, ty0 = m2t(x1, y1)
    rows = []
    for ty in range(min(ty0, ty1), max(ty0, ty1) + 1):
        cols = []
        for tx in range(min(tx0, tx1), max(tx0, tx1) + 1):
            t = get_tile(tx, ty)
            cols.append(t if t is not None else np.zeros((256, 256), np.float32))
        rows.append(np.hstack(cols))
    mos = np.vstack(rows)
    ox = min(tx0, tx1) * 256 * RES - ORIG
    oy = ORIG - min(ty0, ty1) * 256 * RES
    c0 = int((x0 - ox) / RES); c1 = int((x1 - ox) / RES)
    r0 = int((oy - y1) / RES); r1 = int((oy - y0) / RES)
    r0, c0 = max(r0, 0), max(c0, 0)
    return mos[r0:r1, c0:c1], from_origin(ox + c0 * RES, oy - r0 * RES, RES, RES)

def to_3857(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:32640", "EPSG:3857", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)

def feats(g):
    b = g.bounds
    if (b[2] - b[0]) < 5 or (b[3] - b[1]) < 5: return None
    try:
        gray, tr = crop((b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3))
    except Exception:
        return None
    if gray.shape[0] < 8 or gray.shape[1] < 8 or gray.max() == 0: return None
    try:
        m = geometry_mask([g.__geo_interface__], out_shape=gray.shape, transform=tr, invert=True)
    except Exception:
        return None
    if m.sum() < 30: return None
    v = gray[m]
    gx = np.abs(np.diff(gray, axis=1)); gy = np.abs(np.diff(gray, axis=0))
    em = np.zeros_like(gray); em[:, :-1] += gx; em[:-1, :] += gy
    e = em[m]
    med = np.median(v)
    return [np.std(v), np.mean(e), float((v < med - 35).mean()),
            float((v > med + 35).mean()), float((e > 40).mean())]

# ---- geometries ----
r = shapefile.Reader(PLOTS)
geoms = []
for s in r.iterShapes():
    try: geoms.append(to_3857(shape(s.__geo_interface__)))
    except Exception: geoms.append(None)

# ---- training sets ----
zones = json.load(open(SCR + r"\zones_utm.json"))
zs = {nm: (MultiPolygon([Polygon(c) for c in cs]) if len(cs) > 1 else Polygon(cs[0]))
      for nm, cs in zones.items() if nm != "0"}
pts = [Point(*c) for c in cent]
tree = STRtree(pts)
ibri = np.array(list(tree.query(zs["IBRI"], predicate="contains")))
tayy = np.array(list(tree.query(zs["AT TAYYIB"], predicate="contains")))
rng = np.random.default_rng(3)
pos = rng.choice(ibri[built_ms[ibri] == 1], 2500, replace=False)
neg = rng.choice(tayy[built_fin[tayy] == 0], 3000, replace=False)

# fetch tiles for training positives (not in the z18 tile list)
need = set()
for i in np.concatenate([pos, neg]):
    g = geoms[i]
    if g is None: continue
    b = g.bounds
    tx0, ty1 = m2t(b[0] - 3, b[1] - 3); tx1, ty0 = m2t(b[2] + 3, b[3] + 3)
    for tx in range(min(tx0, tx1), max(tx0, tx1) + 1):
        for ty in range(min(ty0, ty1), max(ty0, ty1) + 1):
            fp = os.path.join(TD, f"{Z}_{tx}_{ty}.jpg")
            if not (os.path.exists(fp) and os.path.getsize(fp) > 500):
                need.add((tx, ty))
print("extra training tiles to fetch:", len(need))
def fetch(t):
    tx, ty = t
    fp = os.path.join(TD, f"{Z}_{tx}_{ty}.jpg")
    try:
        req = urllib.request.Request(URL.format(z=Z, x=tx, y=ty),
                                     headers={"User-Agent": "Mozilla/5.0 QGIS/3.44"})
        open(fp, "wb").write(urllib.request.urlopen(req, timeout=30).read())
        return 1
    except Exception:
        return -1
with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(fetch, sorted(need)))
print("training tiles fetched")

def featset(idxs):
    F = []
    keep = []
    for i in idxs:
        g = geoms[i]
        if g is None: continue
        ft = feats(g)
        if ft: F.append(ft); keep.append(i)
    return np.array(F), np.array(keep)

Fp, _ = featset(pos)
Fn, _ = featset(neg)
print("train pos/neg feats:", len(Fp), len(Fn))
X = np.vstack([Fp, Fn]); y = np.concatenate([np.ones(len(Fp)), np.zeros(len(Fn))])
mu, sd = X.mean(0), X.std(0) + 1e-6
Xb = np.hstack([(X - mu) / sd, np.ones((len(X), 1))])
wts = np.zeros(6)
for it in range(4000):
    p = 1 / (1 + np.exp(-Xb @ wts))
    wts -= 0.5 * (Xb.T @ (p - y) / len(y))
p = 1 / (1 + np.exp(-Xb @ wts))
print("z18 train acc:", round(float(((p > 0.5) == y).mean()), 3))

# ---- reclassify all BUILT_FIN==0 ----
targets = np.where(built_fin == 0)[0]
print("recheck targets:", len(targets))
prob18 = np.full(len(geoms), -1.0)
t0 = time.time()
for k, i in enumerate(targets):
    g = geoms[i]
    if g is None: continue
    ft = feats(g)
    if ft is None: continue
    xb = np.append((np.array(ft) - mu) / sd, 1.0)
    prob18[i] = 1 / (1 + np.exp(-xb @ wts))
    if k % 5000 == 0: print(k, f"{time.time()-t0:.0f}s", flush=True)
np.save(SCR + r"\prob18.npy", prob18)
THR = 0.6   # slightly conservative flip threshold
built_z18 = (prob18 >= THR).astype(int)
flipped = int(((built_fin == 0) & (built_z18 == 1)).sum())
built_v3 = np.where(built_fin == 1, 1, built_z18)
print(f"flipped planned->built: {flipped}; total built v3: {int(built_v3.sum())} ({100*built_v3.mean():.1f}%)")

# ---- v3 shapefile ----
w = shapefile.Writer(os.path.join(W3, "shp", "MoH_Plots_built_v3"), shapeType=r.shapeType)
w.field("OBJECTID", "N", 12); w.field("LANDUSE", "C", 30); w.field("VILLAGE_EN", "C", 40)
w.field("BUILT_MS", "N", 1); w.field("BUILT_IMG", "N", 2); w.field("PROB18", "N", 6, 3)
w.field("BUILT_FIN", "N", 1); w.field("SRC", "N", 1)
fields = [f_[0] for f_ in r.fields[1:]]
i_id = fields.index("OBJECTID"); i_lu = fields.index("LANDUSE"); i_ve = fields.index("VILLAGE_EN")
src = np.where(built_ms == 1, 1, np.where(built_img == 1, 2, np.where(built_z18 == 1, 3, 0)))
for i, sr in enumerate(r.iterShapeRecords()):
    w.shape(sr.shape)
    w.record(sr.record[i_id], str(sr.record[i_lu])[:30], str(sr.record[i_ve])[:40],
             int(built_ms[i]), int(built_img[i]), round(float(prob18[i]), 3),
             int(built_v3[i]), int(src[i]))
w.close()
import shutil
shutil.copy(os.path.join(W3, "shp", "MoH_Plots_built.prj"), os.path.join(W3, "shp", "MoH_Plots_built_v3.prj"))
shutil.copy(os.path.join(W3, "shp", "MoH_Plots_built_v2.qml"), os.path.join(W3, "shp", "MoH_Plots_built_v3.qml"))
np.save(SCR + r"\built_v3.npy", built_v3)
print("v3 shapefile written")
