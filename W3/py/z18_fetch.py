# -*- coding: utf-8 -*-
"""Download z18 Esri tiles covering all BUILT_FIN=0 plots (resumable)."""
import os, math, time, json
import urllib.request
import numpy as np
import shapefile
from shapely.geometry import shape
from concurrent.futures import ThreadPoolExecutor
from rasterio.warp import transform as rio_transform

Z = 18
OUTD = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z18_tiles"
os.makedirs(OUTD, exist_ok=True)
SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

built_ms = np.load(SCR + r"\built.npy")
built_img = np.load(SCR + r"\built_img.npy")
built_fin = np.where(built_ms == 1, 1, np.where(built_img >= 0, built_img, 0))
n = 2 ** Z
ORIG = 2 * math.pi * 6378137 / 2.0

def m2t(x, y):  # EPSG:3857 -> tile xy
    tx = int((x + ORIG) / (2 * ORIG) * n)
    ty = int((ORIG - y) / (2 * ORIG) * n)
    return tx, ty

r = shapefile.Reader(PLOTS)
tiles = set()
for i, s in enumerate(r.iterShapes()):
    if built_fin[i] != 0: continue
    b = s.bbox
    xs, ys = rio_transform("EPSG:32640", "EPSG:3857", [b[0] - 3, b[2] + 3], [b[1] - 3, b[3] + 3])
    tx0, ty1 = m2t(xs[0], ys[0]); tx1, ty0 = m2t(xs[1], ys[1])
    for tx in range(min(tx0, tx1), max(tx0, tx1) + 1):
        for ty in range(min(ty0, ty1), max(ty0, ty1) + 1):
            tiles.add((tx, ty))
tiles = sorted(tiles)
print("z18 tiles needed:", len(tiles))
json.dump(tiles, open(os.path.join(OUTD, "_tilelist.json"), "w"))

def fetch(t):
    tx, ty = t
    fp = os.path.join(OUTD, f"{Z}_{tx}_{ty}.jpg")
    if os.path.exists(fp) and os.path.getsize(fp) > 500: return 0
    try:
        req = urllib.request.Request(URL.format(z=Z, x=tx, y=ty),
                                     headers={"User-Agent": "Mozilla/5.0 QGIS/3.44"})
        data = urllib.request.urlopen(req, timeout=30).read()
        with open(fp, "wb") as f: f.write(data)
        return 1
    except Exception:
        return -1

t0 = time.time(); done = 0; err = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    for res in ex.map(fetch, tiles):
        if res == -1: err += 1
        done += 1
        if done % 2000 == 0: print(f"{done}/{len(tiles)} err={err} {time.time()-t0:.0f}s", flush=True)
print(f"DONE {done} tiles, errors {err}, {time.time()-t0:.0f}s")
