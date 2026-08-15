# -*- coding: utf-8 -*-
"""A3 — per-settlement built statistics from the final classification (MS + imagery)."""
import numpy as np, json, csv, os
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.strtree import STRtree

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
W3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
built_ms = np.load(SCR + r"\built.npy")
built_img = np.load(SCR + r"\built_img.npy")
built_fin = np.where(built_ms == 1, 1, np.where(built_img >= 0, built_img, 0))
cent = np.load(SCR + r"\plot_cent.npy")
zones = json.load(open(SCR + r"\zones_utm.json"))
zcap = {z["name"]: z for z in json.load(open(SCR + r"\zone_capacity.json"))}
zs = {nm: (MultiPolygon([Polygon(c) for c in cs]) if len(cs) > 1 else Polygon(cs[0]))
      for nm, cs in zones.items() if nm != "0"}
pts = [Point(*c) for c in cent]
tree = STRtree(pts)
OR_ = 6.0
rows = []
for nm, g in zs.items():
    idx = np.array(list(tree.query(g, predicate="contains")))
    if len(idx) == 0: continue
    nt = len(idx); nb = int(built_fin[idx].sum())
    z = zcap.get(nm, {})
    imp = (z.get("pop2024") or 0) / OR_
    rows.append({"settlement": nm, "plots": nt, "built_fin": nb,
                 "pct_built": round(100 * nb / nt, 1), "vacant": nt - nb,
                 "implied_dw_2024": round(imp),
                 "built_over_implied": round(nb / imp, 2) if imp > 5 else ""})
rows.sort(key=lambda r: -r["plots"])
with open(os.path.join(W3, "analysis", "A3_built_final.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f"{'settlement':<18}{'plots':>7}{'built':>7}{'%':>7}{'impl.dw24':>10}{'b/impl':>8}")
for r in rows[:14]:
    print(f"{r['settlement']:<18}{r['plots']:>7}{r['built_fin']:>7}{r['pct_built']:>7}{r['implied_dw_2024']:>10}{str(r['built_over_implied']):>8}")
print("total built:", int(built_fin.sum()), "/", len(built_fin),
      f"({100*built_fin.mean():.1f}%)")
