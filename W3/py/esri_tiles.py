# -*- coding: utf-8 -*-
"""Download Esri World Imagery z17 tiles covering the project boundary; resumable."""
import os, math, time, json
import urllib.request
import shapefile
from shapely.geometry import shape, box
from shapely.ops import transform as shp_t
from rasterio.warp import transform as rio_transform
from concurrent.futures import ThreadPoolExecutor

Z = 17
OUTD = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_tiles"
os.makedirs(OUTD, exist_ok=True)
BND = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\Project_boundary.shp"
URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

# boundary (32640) -> WGS84
r = shapefile.Reader(BND)
g = shape(r.shape(0).__geo_interface__)
def to_wgs(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:32640", "EPSG:4326", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)
gw = to_wgs(g).buffer(0.002)  # ~200 m pad
minx, miny, maxx, maxy = gw.bounds
n = 2 ** Z
def lonlat_tile(lon, lat):
    x = int((lon + 180) / 360 * n)
    la = math.radians(lat)
    y = int((1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n)
    return x, y
def tile_bounds(x, y):
    lon0 = x / n * 360 - 180; lon1 = (x + 1) / n * 360 - 180
    def lat(yy):
        t = math.pi * (1 - 2 * yy / n)
        return math.degrees(math.atan(math.sinh(t)))
    return (lon0, lat(y + 1), lon1, lat(y))
x0, y1 = lonlat_tile(minx, miny)
x1, y0 = lonlat_tile(maxx, maxy)
tiles = []
for tx in range(min(x0, x1), max(x0, x1) + 1):
    for ty in range(min(y0, y1), max(y0, y1) + 1):
        b = tile_bounds(tx, ty)
        if gw.intersects(box(b[0], b[1], b[2], b[3])):
            tiles.append((tx, ty))
print("tiles to fetch:", len(tiles))
json.dump(tiles, open(os.path.join(OUTD, "_tilelist.json"), "w"))

def fetch(t):
    tx, ty = t
    fp = os.path.join(OUTD, f"{Z}_{tx}_{ty}.jpg")
    if os.path.exists(fp) and os.path.getsize(fp) > 500:
        return 0
    try:
        req = urllib.request.Request(URL.format(z=Z, x=tx, y=ty),
                                     headers={"User-Agent": "Mozilla/5.0 QGIS/3.44"})
        data = urllib.request.urlopen(req, timeout=30).read()
        with open(fp, "wb") as f:
            f.write(data)
        return 1
    except Exception as e:
        return -1

t0 = time.time()
done = 0; err = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    for i, res in enumerate(ex.map(fetch, tiles)):
        if res == -1: err += 1
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(tiles)}  err={err}  {time.time()-t0:.0f}s", flush=True)
print(f"DONE {done} tiles, errors {err}, {time.time()-t0:.0f}s")
