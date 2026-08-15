# -*- coding: utf-8 -*-
"""A5a — buildings without any cadastral plot: MS footprints minus MoH_Plots.
Output: W3/shp/Unparceled_Buildings.shp (footprint polygons, area, settlement)."""
import gzip, json, glob, os
import numpy as np
import shapefile
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.strtree import STRtree
from shapely.ops import transform as shp_t
from rasterio.warp import transform as rio_transform

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
BND = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\Project_boundary.shp"
W3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def to_utm(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:4326", "EPSG:32640", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)

# footprints
fps = []
for f in glob.glob(os.path.join(SCR, "msfp", "*.csv.gz")):
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try:
                gj = json.loads(line)
                g = gj["geometry"] if "geometry" in gj else gj
                p = shape(g)
                b = p.bounds
                if b[2] < 56.05 or b[0] > 57.05 or b[3] < 22.75 or b[1] > 23.75: continue
                fps.append(to_utm(p))
            except Exception:
                pass
print("footprints:", len(fps))

bnd = shape(shapefile.Reader(BND).shape(0).__geo_interface__)
fps = [p for p in fps if bnd.intersects(p)]
print("inside boundary:", len(fps))

# plots tree
r = shapefile.Reader(PLOTS)
plot_geoms = []
for s in r.iterShapes():
    try: plot_geoms.append(shape(s.__geo_interface__))
    except Exception: pass
tree = STRtree(plot_geoms)

# settlement zones for attribution
zones = json.load(open(SCR + r"\zones_utm.json"))
zs = {nm: (MultiPolygon([Polygon(c) for c in cs]) if len(cs) > 1 else Polygon(cs[0]))
      for nm, cs in zones.items() if nm != "0"}

orphans = []
for p in fps:
    idx = tree.query(p, predicate="intersects")
    ov = 0.0
    for j in idx:
        try: ov += plot_geoms[j].intersection(p).area
        except Exception: pass
    if ov < 0.15 * p.area and p.area >= 25:   # <15% of roof inside any plot, ignore sheds <25 m2
        nm = ""
        for zn, zgm in zs.items():
            if zgm.contains(p.centroid): nm = zn; break
        orphans.append((p, p.area, nm))
print("unparceled buildings:", len(orphans))

w = shapefile.Writer(os.path.join(W3, "shp", "Unparceled_Buildings"), shapeType=5)
w.field("FID_", "N", 8); w.field("AREA_M2", "N", 10, 1); w.field("SETTLEMENT", "C", 30)
for i, (p, a, nm) in enumerate(orphans):
    gs = p.geoms if hasattr(p, "geoms") else [p]
    parts = [list(g.exterior.coords) for g in gs]
    w.poly(parts)
    w.record(i, round(a, 1), nm)
w.close()
import shutil
shutil.copy(os.path.join(W3, "shp", "MoH_Plots_built.prj"), os.path.join(W3, "shp", "Unparceled_Buildings.prj"))
from collections import Counter
c = Counter(nm for _, _, nm in orphans)
print("by settlement:", c.most_common(10))
print("total roof area (m2):", round(sum(a for _, a, _ in orphans)))
