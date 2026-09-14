"""The zoom panels for the free meters: the 126 meters more than 15 m from any plot,
grouped so that every meter falls in one panel and no panel spans more than SPAN_M.

Writes shp/free_meter_panels.shp (one rectangle per panel, 4:3, padded) and
shp/free_meters.shp (the 126 points with their settlement and tariff), read by the
QGIS side (qgis_maps_basis.py) for the overview map and the panel renders.

    python make_panels.py
"""
import os
import sys

import geopandas as gpd
import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from shapely.geometry import box

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import facts_basis as B  # noqa: E402
import facts_w14 as F  # noqa: E402

SHP = os.path.join(HERE, "shp")
SPAN_M = 800.0            # a panel never spans more than this between its meters
MIN_W, MIN_H = 700.0, 525.0   # the smallest panel, m (4:3)
PAD_M = 100.0             # margin around the meters


def build():
    os.makedirs(SHP, exist_ok=True)
    m = F.meters()
    free = m[m.PLACE == "free"].copy()
    free["NAME"] = [F.NAME.get(s, str(s).title()) for s in free.SETTLE]
    free["DWELLING"] = (free.PROPERTY == 1).astype(int)
    xy = np.c_[free.geometry.x, free.geometry.y]
    lab = fcluster(linkage(xy, method="complete"), t=SPAN_M, criterion="distance")
    free["CLUSTER"] = lab
    # number the panels by settlement (largest first) then west to east
    order = {s: i for i, s in enumerate(free.NAME.value_counts().index)}
    groups = []
    for c in sorted(set(lab)):
        g = free[free.CLUSTER == c]
        groups.append((order[g.NAME.value_counts().index[0]], g.geometry.x.mean(), c))
    groups.sort()
    panel_of = {c: i + 1 for i, (_, _, c) in enumerate(groups)}
    free["PANEL"] = [panel_of[c] for c in lab]
    rows = []
    for c, n in panel_of.items():
        g = free[free.CLUSTER == c]
        x0, y0, x1, y1 = g.total_bounds
        w = max(x1 - x0 + 2 * PAD_M, MIN_W); h = max(y1 - y0 + 2 * PAD_M, MIN_H)
        if w / h > 4 / 3:
            h = w * 3 / 4
        else:
            w = h * 4 / 3
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rows.append(dict(PANEL=n, SETTLE=g.NAME.value_counts().index[0], N=len(g), N_DWELL=int(g.DWELLING.sum()),
                         WIDTH_M=round(w), geometry=box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)))
    panels = gpd.GeoDataFrame(rows, crs=free.crs).sort_values("PANEL")
    panels.to_file(os.path.join(SHP, "free_meter_panels.shp"))
    free[["TARIFF", "GUD", "SETTLE", "NAME", "DWELLING", "PANEL", "geometry"]].to_file(os.path.join(SHP, "free_meters.shp"))
    print(f"{len(free)} meters in {len(panels)} panels; widths {panels.WIDTH_M.min()} to {panels.WIDTH_M.max()} m")
    return panels


if __name__ == "__main__":
    build()
