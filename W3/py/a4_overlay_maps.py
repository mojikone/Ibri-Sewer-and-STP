# -*- coding: utf-8 -*-
"""A4 — render Esri imagery + MoH plot outlines (black=built, white=planned) as PNG maps."""
import os
import numpy as np
import shapefile
import rasterio
from rasterio.windows import from_bounds
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely.ops import transform as shp_t
from rasterio.warp import transform as rio_transform

W3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
SHP = os.path.join(W3, "shp", "MoH_Plots_built_v2.shp")
ds = rasterio.open(MOS)

def to_3857(geom):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, "__iter__") else [x]
        ys = list(y) if hasattr(y, "__iter__") else [y]
        x2, y2 = rio_transform("EPSG:32640", "EPSG:3857", xs, ys)
        return (x2, y2)
    return shp_t(f, geom)

r = shapefile.Reader(SHP)
fields = [f[0] for f in r.fields[1:]]
i_b = fields.index("BUILT_FIN")
geoms = []
flags = []
for sr in r.iterShapeRecords():
    try:
        geoms.append(to_3857(shape(sr.shape.__geo_interface__)))
        flags.append(int(sr.record[i_b]))
    except Exception:
        geoms.append(None); flags.append(0)
flags = np.array(flags)
print("plots:", len(geoms), "built:", int(flags.sum()))

# view windows in EPSG:32640 -> 3857 (name, xmin, ymin, xmax, ymax)
VIEWS = [
    ("A4_overlay_IBRI_core", 447000, 2566000, 451500, 2570000),
    ("A4_overlay_AD_DARIZ", 459000, 2575700, 463200, 2579700),
    ("A4_overlay_AT_TAYYIB_edge", 452000, 2568500, 456500, 2572500),
]
for name, x0, y0, x1, y1 in VIEWS:
    (xs, ys) = rio_transform("EPSG:32640", "EPSG:3857", [x0, x1], [y0, y1])
    b = (xs[0], ys[0], xs[1], ys[1])
    w = from_bounds(*b, ds.transform)
    img = ds.read(window=w, boundless=True, fill_value=0).transpose(1, 2, 0)
    fig, ax = plt.subplots(figsize=(13, 13 * img.shape[0] / img.shape[1]))
    ax.imshow(img, extent=[b[0], b[2], b[1], b[3]], interpolation="bilinear")
    n_in = 0
    for g, fl in zip(geoms, flags):
        if g is None: continue
        gb = g.bounds
        if gb[2] < b[0] or gb[0] > b[2] or gb[3] < b[1] or gb[1] > b[3]: continue
        col = "black" if fl == 1 else "white"
        gs = g.geoms if hasattr(g, "geoms") else [g]
        for p in gs:
            if p.exterior is None: continue
            x, y = p.exterior.xy
            ax.plot(x, y, color=col, lw=0.7)
        n_in += 1
    ax.set_xlim(b[0], b[2]); ax.set_ylim(b[1], b[3])
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{name.replace('A4_overlay_', '').replace('_', ' ')} — black = built, white = planned ({n_in} plots)", fontsize=12)
    fig.savefig(os.path.join(W3, "img", name + ".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(name, "plots drawn:", n_in)
print("done")
