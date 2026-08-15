# -*- coding: utf-8 -*-
"""Mosaic Esri z17 tiles into a single JPEG-compressed tiled GeoTIFF (EPSG:3857)."""
import os, math, json
import numpy as np
import rasterio
from rasterio.transform import from_origin
from PIL import Image

Z = 17
TD = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_tiles"
OUT = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
tiles = json.load(open(os.path.join(TD, "_tilelist.json")))
xs = [t[0] for t in tiles]; ys = [t[1] for t in tiles]
x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
W = (x1 - x0 + 1) * 256; H = (y1 - y0 + 1) * 256
ORIG = 2 * math.pi * 6378137 / 2.0
res = 2 * ORIG / (2 ** Z) / 256
west = x0 * 256 * res - ORIG
north = ORIG - y0 * 256 * res
print(f"mosaic {W}x{H} px, res {res:.3f} m/px")
prof = dict(driver="GTiff", width=W, height=H, count=3, dtype="uint8",
            crs="EPSG:3857", transform=from_origin(west, north, res, res),
            tiled=True, blockxsize=256, blockysize=256,
            compress="JPEG", photometric="YCBCR", jpeg_quality=85, BIGTIFF="IF_SAFER")
missing = 0
with rasterio.open(OUT, "w", **prof) as dst:
    for tx, ty in tiles:
        fp = os.path.join(TD, f"{Z}_{tx}_{ty}.jpg")
        if not os.path.exists(fp) or os.path.getsize(fp) < 500:
            missing += 1; continue
        try:
            a = np.asarray(Image.open(fp).convert("RGB"))
        except Exception:
            missing += 1; continue
        cx = (tx - x0) * 256; cy = (ty - y0) * 256
        dst.write(a.transpose(2, 0, 1), window=rasterio.windows.Window(cx, cy, 256, 256))
print("mosaic written:", OUT, "| missing tiles:", missing)
print("size MB:", round(os.path.getsize(OUT) / 1e6, 1))
