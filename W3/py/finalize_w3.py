# -*- coding: utf-8 -*-
"""Finalize W3 analysis A1: merge capacity + built stats, write CSV, chart, QA map copy."""
import numpy as np, json, csv, shutil, os
import zipfile, xml.etree.ElementTree as ET
import shapefile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import transform as shp_t
from shapely.strtree import STRtree
from rasterio.warp import transform as rio_transform

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
W3 = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W3"
os.makedirs(os.path.join(W3, "analysis"), exist_ok=True)
os.makedirs(os.path.join(W3, "img"), exist_ok=True)

built = np.load(SCR + r"\built.npy")
cent = np.load(SCR + r"\plot_cent.npy")
zones = json.load(open(SCR + r"\zone_capacity.json"))
OR_ = 6.0

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

rows = []
for z in zones:
    nm = z["name"]
    if nm == "0" or nm not in zg: continue
    idx = tree.query(zg[nm], predicate="contains")
    nb = int(built[idx].sum())
    cov = "OK" if nb > 0 else "NO-COVERAGE"
    implied = (z["pop2024"] or 0) / OR_
    rows.append({
        "settlement": nm, "area_km2": z["area_km2"], "plots": z["plots"],
        "pop_basis_plots": z["pop_basis"], "ceiling_pop_OR6": round(z["ceiling"]),
        "built_MS": nb, "pct_built": round(100 * nb / max(z["plots"], 1), 1),
        "ms_coverage": cov, "implied_dwellings_2024": round(implied),
        "pop2024_R0": round(z["pop2024"] or 0), "pop2055_R0": round(z["pop2055"] or 0),
        "pop2100_R0": round(z["pop2100"] or 0),
        "util2055_pct": z["util2055_pct"], "ceiling_cross_year": z["cross_year"]})
rows.sort(key=lambda r: -r["ceiling_pop_OR6"])
with open(os.path.join(W3, "analysis", "A1_zone_capacity.csv"), "w", newline="") as f:
    wcsv = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    wcsv.writeheader(); wcsv.writerows(rows)

# capacity chart: top 8 settlements — ceiling vs pop2055 vs pop2100
top = rows[:8]
names = [r["settlement"] for r in top]
x = np.arange(len(top)); w = 0.27
fig, ax = plt.subplots(figsize=(9.5, 4.4))
ax.bar(x - w, [r["ceiling_pop_OR6"] / 1000 for r in top], w, color="#444444", label="land ceiling (plots × OR 6.0)")
ax.bar(x, [r["pop2055_R0"] / 1000 for r in top], w, color="#0072B2", label="R0 projection 2055")
ax.bar(x + w, [r["pop2100_R0"] / 1000 for r in top], w, color="#9CC7E4", label="R0 projection 2100")
for i, r in enumerate(top):
    if r["ceiling_cross_year"]:
        ax.text(i, r["ceiling_pop_OR6"] / 1000 + 6, f"cross {r['ceiling_cross_year']}", ha="center", fontsize=7.6, color="#C8342A")
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8, rotation=20, ha="right")
ax.set_ylabel("population (thousands)", fontsize=9)
ax.legend(fontsize=8.5, frameon=False)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#DDDDDD", lw=0.7, zorder=0)
ax.set_title("Land-capacity ceiling vs R0 projections — top settlements", fontsize=11)
fig.savefig(os.path.join(W3, "img", "A1_capacity_vs_projection.png"), dpi=170, bbox_inches="tight")

shutil.copy(SCR + r"\qa_built_map.png", os.path.join(W3, "img", "A1_qa_built_map.png"))
print("rows:", len(rows))
for r in rows[:8]:
    print(r["settlement"], r["pct_built"], r["ms_coverage"], r["ceiling_cross_year"])
print("W3 analysis files written")
