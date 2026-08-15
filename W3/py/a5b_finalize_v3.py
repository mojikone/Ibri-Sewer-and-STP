# -*- coding: utf-8 -*-
"""A5b — finalize BUILT v3: z18 flips (thr 0.6; agricultural plots 0.8), rewrite v3 shapefile, stats."""
import os, json, csv
import numpy as np
import shapefile
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.strtree import STRtree

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
W3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGRI = {"زراعى", "سكنى/زراعى"}

built_ms = np.load(SCR + r"\built.npy")
built_img = np.load(SCR + r"\built_img.npy")
prob18 = np.load(SCR + r"\prob18.npy")
cent = np.load(SCR + r"\plot_cent.npy")
built_fin2 = np.where(built_ms == 1, 1, np.where(built_img >= 0, built_img, 0))

r = shapefile.Reader(PLOTS)
fields = [f_[0] for f_ in r.fields[1:]]
i_id = fields.index("OBJECTID"); i_lu = fields.index("LANDUSE"); i_ve = fields.index("VILLAGE_EN")
lus = [str(rec[i_lu] or "").strip() for rec in r.iterRecords()]
thr = np.array([0.8 if lu in AGRI else 0.6 for lu in lus])
built_z18 = ((prob18 >= thr) & (prob18 >= 0)).astype(int)
flips = int(((built_fin2 == 0) & (built_z18 == 1)).sum())
built_v3 = np.where(built_fin2 == 1, 1, built_z18)
agri_blocked = int(((built_fin2 == 0) & (prob18 >= 0.6) & (prob18 < 0.8) & np.array([lu in AGRI for lu in lus])).sum())
print(f"flips: {flips} (agri-blocked {agri_blocked}); built v3 total: {int(built_v3.sum())} ({100*built_v3.mean():.1f}%)")

src = np.where(built_ms == 1, 1, np.where(built_img == 1, 2, np.where(built_z18 == 1, 3, 0)))
w = shapefile.Writer(os.path.join(W3, "shp", "MoH_Plots_built_v3"), shapeType=r.shapeType)
w.field("OBJECTID", "N", 12); w.field("LANDUSE", "C", 30); w.field("VILLAGE_EN", "C", 40)
w.field("BUILT_MS", "N", 1); w.field("BUILT_IMG", "N", 2); w.field("PROB18", "N", 6, 3)
w.field("BUILT_FIN", "N", 1); w.field("SRC", "N", 1)
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

# per-settlement stats
zones = json.load(open(SCR + r"\zones_utm.json"))
zcap = {z["name"]: z for z in json.load(open(SCR + r"\zone_capacity.json"))}
zs = {nm: (MultiPolygon([Polygon(c) for c in cs]) if len(cs) > 1 else Polygon(cs[0]))
      for nm, cs in zones.items() if nm != "0"}
pts = [Point(*c) for c in cent]
tree = STRtree(pts)
rows = []
for nm, g in zs.items():
    idx = np.array(list(tree.query(g, predicate="contains")))
    if len(idx) == 0: continue
    nt = len(idx); nb = int(built_v3[idx].sum())
    z = zcap.get(nm, {})
    imp = (z.get("pop2024") or 0) / 6.0
    rows.append({"settlement": nm, "plots": nt, "built_v3": nb,
                 "pct_built": round(100 * nb / nt, 1), "vacant": nt - nb,
                 "implied_dw_2024": round(imp),
                 "built_over_implied": round(nb / imp, 2) if imp > 5 else ""})
rows.sort(key=lambda x: -x["plots"])
with open(os.path.join(W3, "analysis", "A5_built_v3.csv"), "w", newline="") as f:
    wcsv = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wcsv.writeheader(); wcsv.writerows(rows)
print(f"{'settlement':<18}{'plots':>7}{'built':>7}{'%':>7}{'b/impl':>8}")
for x in rows[:10]:
    print(f"{x['settlement']:<18}{x['plots']:>7}{x['built_v3']:>7}{x['pct_built']:>7}{str(x['built_over_implied']):>8}")
