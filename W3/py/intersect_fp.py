# -*- coding: utf-8 -*-
"""Intersect MS Building Footprints with MoH plots -> BUILT flag per plot.
Output: W3/shp/MoH_Plots_built.shp (plot polygons + BUILT_MS, FOOTP_M2, N_FOOTP)."""
import gzip, json, glob, os
import numpy as np
import shapefile
from shapely.geometry import shape, Polygon
from shapely.strtree import STRtree
from rasterio.warp import transform as rio_transform

SCR = r"C:\Users\mojtaba\AppData\Local\Temp\claude\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude\413b098f-38f9-4a93-9820-2b7c34af7f5e\scratchpad"
PLOTS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\MoHUP_DATA\MoH_Plots.shp"
W3 = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W3"
os.makedirs(os.path.join(W3, "shp"), exist_ok=True)
os.makedirs(os.path.join(W3, "analysis"), exist_ok=True)

# ---- load footprints (lon/lat geojsonl) ----
feats = []
for f in glob.glob(os.path.join(SCR, "msfp", "*.csv.gz")):
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try:
                gj = json.loads(line)
                g = gj["geometry"] if "geometry" in gj else gj
                feats.append(g)
            except Exception:
                pass
print("footprints loaded:", len(feats))

# bbox filter to project area (lon 56.1-57.0, lat 22.8-23.7) then transform
fps = []
for g in feats:
    try:
        p = shape(g)
        b = p.bounds
        if b[2] < 56.05 or b[0] > 57.05 or b[3] < 22.75 or b[1] > 23.75: continue
        fps.append(p)
    except Exception:
        pass
print("in-region footprints:", len(fps))

def to_utm(geom):
    from shapely.ops import transform as shp_t
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:4326", "EPSG:32640", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)

fps = [to_utm(p) for p in fps]
tree = STRtree(fps)

# ---- plots ----
r = shapefile.Reader(PLOTS)
n = len(r)
built = np.zeros(n, dtype=int)
farea = np.zeros(n)
nfp = np.zeros(n, dtype=int)
geoms = []
MIN_OVL = 12.0  # m2 of roof inside plot to count as built
for i, s in enumerate(r.iterShapes()):
    try:
        g = shape(s.__geo_interface__)
    except Exception:
        geoms.append(None); continue
    geoms.append(g)
    idx = tree.query(g, predicate="intersects")
    a = 0.0; c = 0
    for j in idx:
        try:
            ov = fps[j].intersection(g).area
        except Exception:
            ov = 0.0
        if ov > 1.0: c += 1
        a += ov
    farea[i] = a; nfp[i] = c
    built[i] = 1 if a >= MIN_OVL else 0
    if i % 10000 == 0: print(i, "...")
print("BUILT=1:", int(built.sum()), f"({100*built.mean():.1f}%)  BUILT=0:", int((built == 0).sum()))

# ---- write output shapefile (copy key attrs + new fields) ----
w = shapefile.Writer(os.path.join(W3, "shp", "MoH_Plots_built"), shapeType=r.shapeType)
w.field("OBJECTID", "N", 12)
w.field("LANDUSE", "C", 30)
w.field("VILLAGE_EN", "C", 40)
w.field("BUILT_MS", "N", 1)
w.field("FOOTP_M2", "N", 12, 1)
w.field("N_FOOTP", "N", 5)
fields = [f[0] for f in r.fields[1:]]
i_id = fields.index("OBJECTID"); i_lu = fields.index("LANDUSE"); i_ve = fields.index("VILLAGE_EN")
for i, sr in enumerate(r.iterShapeRecords()):
    w.shape(sr.shape)
    w.record(sr.record[i_id], str(sr.record[i_lu])[:30], str(sr.record[i_ve])[:40],
             int(built[i]), round(float(farea[i]), 1), int(nfp[i]))
w.close()
open(os.path.join(W3, "shp", "MoH_Plots_built.prj"), "w").write(
    'PROJCS["WGS_1984_UTM_Zone_40N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",57.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]')
np.save(os.path.join(SCR, "built.npy"), built)
np.save(os.path.join(SCR, "farea.npy"), farea)
print("shapefile written: W3/shp/MoH_Plots_built.shp")
