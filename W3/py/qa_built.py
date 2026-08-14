# -*- coding: utf-8 -*-
"""QA of BUILT_MS: per-settlement built fractions vs implied dwellings; visual map."""
import numpy as np, json, shapefile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
built = np.load(SCR + r"\built.npy")
_r = shapefile.Reader(r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp")
cent = np.array([[(s.bbox[0] + s.bbox[2]) / 2, (s.bbox[1] + s.bbox[3]) / 2] for s in _r.iterShapes()])
np.save(SCR + r"\plot_cent.npy", cent)
zones = json.load(open(SCR + r"\zone_capacity.json"))

# settlement polygons again (reuse zone_capacity parsing quickly via saved json? need geometry -> reparse kmz)
import zipfile, xml.etree.ElementTree as ET
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import transform as shp_t
from shapely.strtree import STRtree
from rasterio.warp import transform as rio_transform
KMZ = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\Received\2621\inception report - R0\Final_Boundary_IBRI.kmz"
ns = {"k": "http://www.opengis.net/kml/2.2"}
root = ET.fromstring(zipfile.ZipFile(KMZ).read("doc.kml").decode("utf-8", errors="replace"))
zg = {}
for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
    nm_el = pm.find("k:name", ns)
    if nm_el is None: continue
    nm = nm_el.text.strip().upper()
    polys = []
    for poly in pm.iter("{http://www.opengis.net/kml/2.2}Polygon"):
        co = poly.find(".//k:outerBoundaryIs/k:LinearRing/k:coordinates", ns)
        if co is None: continue
        pts = [(float(t.split(",")[0]), float(t.split(",")[1])) for t in co.text.split() if len(t.split(",")) >= 2]
        if len(pts) >= 4: polys.append(Polygon(pts))
    if polys:
        g = MultiPolygon(polys) if len(polys) > 1 else polys[0]
        zg[nm] = zg[nm].union(g) if nm in zg else g
def to_utm(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:4326", "EPSG:32640", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)
zg = {n: to_utm(g) for n, g in zg.items()}

pts = [Point(*c) for c in cent]
tree = STRtree(pts)
OR_ = 6.0
print(f"{'settlement':<18}{'plots':>7}{'built':>7}{'%built':>8}{'implied dw 2024':>16}{'built/implied':>14}")
rows = []
for z in zones:
    nm = z["name"]
    if nm not in zg or nm == "0": continue
    idx = tree.query(zg[nm], predicate="contains")
    nb = int(built[idx].sum()); nt = len(idx)
    implied = (z["pop2024"] or 0) / OR_
    rows.append((nm, nt, nb, implied))
    if nt > 400 or implied > 300:
        print(f"{nm:<18}{nt:>7}{nb:>7}{100*nb/max(nt,1):>7.1f}%{implied:>16.0f}{(nb/implied if implied else 0):>14.2f}")

# map: IBRI + AT TAYYIB area, built vs vacant
fig, ax = plt.subplots(figsize=(11, 10))
m = (cent[:, 0] > 440000) & (cent[:, 0] < 462000) & (cent[:, 1] > 2558000) & (cent[:, 1] < 2576000)
b = built.astype(bool)
ax.scatter(cent[m & ~b, 0], cent[m & ~b, 1], s=1.1, c="#BBBBBB", label="vacant (no footprint)")
ax.scatter(cent[m & b, 0], cent[m & b, 1], s=1.4, c="#0072B2", label="built (MS footprint)")
for nm in ["IBRI", "AT TAYYIB", "AL WAHRAH", "AL AYNAYN"]:
    if nm in zg:
        g = zg[nm]
        gs = g.geoms if hasattr(g, "geoms") else [g]
        for p in gs:
            x, y = p.exterior.xy
            ax.plot(x, y, color="#C8342A", lw=1.2)
        c = g.centroid
        ax.annotate(nm, (c.x, c.y), fontsize=11, color="#C8342A", fontweight="bold", ha="center")
ax.set_xlim(440000, 462000); ax.set_ylim(2558000, 2576000)
ax.set_aspect("equal"); ax.legend(loc="lower right", fontsize=10, markerscale=8)
ax.set_title("QA — BUILT_MS classification, Ibri town area", fontsize=13)
fig.savefig(SCR + r"\qa_built_map.png", dpi=150, bbox_inches="tight")
print("map saved")
