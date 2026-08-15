# -*- coding: utf-8 -*-
"""A6 — 3-class layer (BUILT / AGRI / PLANNED) + empty-LANDUSE characterization.
AGRI rule: vegfrac>=0.55 & area>=2000 m2, or vegfrac>=0.85 & area>=800 m2 (calibrated on
known agri vs residential distributions). Output: MoH_Plots_class_v4.shp + QML + stats."""
import os, csv
import numpy as np
import shapefile

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
W3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

veg = np.load(SCR + r"\vegfrac.npy")
built_v3 = np.load(SCR + r"\built_v3.npy")
prob18 = np.load(SCR + r"\prob18.npy")
built_ms = np.load(SCR + r"\built.npy")

r = shapefile.Reader(PLOTS)
fields = [f_[0] for f_ in r.fields[1:]]
i_id = fields.index("OBJECTID"); i_lu = fields.index("LANDUSE"); i_ve = fields.index("VILLAGE_EN")
i_ar = fields.index("SHAPE_Area")
recs = list(r.iterRecords())
lus = np.array([str(rec[i_lu] or "").strip() for rec in recs])
areas = np.array([float(rec[i_ar] or 0) for rec in recs])

agri_est = ((veg >= 0.55) & (areas >= 2000)) | ((veg >= 0.85) & (areas >= 800))
# known agri landuse always agri (explicit attribute wins)
agri_est = agri_est | np.isin(lus, ["زراعى", "سكنى/زراعى"])
CLASS = np.where(agri_est, "A", np.where(built_v3 == 1, "B", "P"))

# validation
known_agri = lus == "زراعى"
res = lus == "سكني"
print("capture of known agri:", round(100 * float(agri_est[known_agri].mean()), 1), "%")
print("false-agri on residential:", round(100 * float(agri_est[res].mean()), 1), "%")
empty = lus == ""
n_e = int(empty.sum())
print(f"empty-LANDUSE plots: {n_e}")
for c, lab in [("A", "agriculture (est.)"), ("B", "built"), ("P", "planned/vacant")]:
    k = int((CLASS[empty] == c).sum())
    print(f"  {lab}: {k} ({100*k/n_e:.1f}%)")
print("overall:", {c: int((CLASS == c).sum()) for c in "ABP"})

# write v4
w = shapefile.Writer(os.path.join(W3, "shp", "MoH_Plots_class_v4"), shapeType=r.shapeType)
w.field("OBJECTID", "N", 12); w.field("LANDUSE", "C", 30); w.field("VILLAGE_EN", "C", 40)
w.field("CLASS", "C", 1); w.field("BUILT_FIN", "N", 1); w.field("VEGFRAC", "N", 6, 3)
w.field("PROB18", "N", 6, 3); w.field("AREA_M2", "N", 12, 1)
for i, sr in enumerate(r.iterShapeRecords()):
    w.shape(sr.shape)
    w.record(sr.record[i_id], str(sr.record[i_lu])[:30], str(sr.record[i_ve])[:40],
             str(CLASS[i]), int(built_v3[i]), round(float(veg[i]), 3),
             round(float(prob18[i]), 3), round(float(areas[i]), 1))
w.close()
import shutil
shutil.copy(os.path.join(W3, "shp", "MoH_Plots_built.prj"), os.path.join(W3, "shp", "MoH_Plots_class_v4.prj"))
np.save(SCR + r"\class_v4.npy", CLASS)

# per-settlement class stats
import json
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.strtree import STRtree
cent = np.load(SCR + r"\plot_cent.npy")
zones = json.load(open(SCR + r"\zones_utm.json"))
zs = {nm: (MultiPolygon([Polygon(c) for c in cs]) if len(cs) > 1 else Polygon(cs[0]))
      for nm, cs in zones.items() if nm != "0"}
pts = [Point(*c) for c in cent]; tree = STRtree(pts)
rows = []
for nm, g in zs.items():
    idx = np.array(list(tree.query(g, predicate="contains")))
    if len(idx) == 0: continue
    d = {"settlement": nm, "plots": len(idx)}
    for c, lab in [("B", "built"), ("A", "agri"), ("P", "planned")]:
        d[lab] = int((CLASS[idx] == c).sum())
    rows.append(d)
rows.sort(key=lambda x: -x["plots"])
with open(os.path.join(W3, "analysis", "A6_class_v4.csv"), "w", newline="") as f:
    wcsv = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wcsv.writeheader(); wcsv.writerows(rows)
for x in rows[:8]:
    print(x)
print("v4 written")
