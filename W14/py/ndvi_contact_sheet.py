# Contact sheet for the engineer: thumbnails of plots from the z17 mosaic, three groups, so the NDVI farm rule can be judged by eye.
import numpy as np, pandas as pd, geopandas as gpd, rasterio, sys
from rasterio.windows import from_bounds
from rasterio.warp import transform as rio_transform
from shapely.ops import transform as shp_t
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
MOS = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
T = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
p = gpd.read_file(f"{W13}/shp/PLOTS_load.shp"); nd = pd.read_csv(f"{W13}/analysis/ndvi_plots.csv").set_index('fid')
for c in ('NDVI_MEAN', 'NDVI_SHARE', 'GREEN_M2'): p[c] = nd[c].values
built = p.Buiding_St == 'EXisting'; tot = p.G_DOM + p.G_NDOM + p.G_GOV
override = (tot > 0) & ((p.G_NDOM / tot.replace(0, 1) >= 2 / 3) | (p.G_GOV / tot.replace(0, 1) >= 2 / 3))
M = 0.20
nf = (p.GREEN_M2 >= T) & (p.NDVI_MEAN >= M) & ~override & (p.G_AGR == 0)
groups = [
    ('A  farm meter on the plot (reference)', p[(p.G_AGR > 0) & built].sample(16, random_state=1)),
    (f'B  NDVI says farm (green >= {T} m2 and mean NDVI >= {M}), meters say home', p[nf & built & (p.DERIVED == 'Residential')].sample(16, random_state=2)),
    ('C  old RGB test said farm, NDVI says not', p[(p.GREEN_IMG == 1) & ~nf & (p.G_AGR == 0) & built].sample(16, random_state=3)),
    (f'D  empty plots NDVI calls farm', p[nf & ~built].sample(16, random_state=4)),
]
def to3857(g):
    def f(x, y, z=None):
        xs = list(x) if hasattr(x, '__iter__') else [x]; ys = list(y) if hasattr(y, '__iter__') else [y]
        return rio_transform('EPSG:32640', 'EPSG:3857', xs, ys)
    return shp_t(f, g)
ds = rasterio.open(MOS)
fig, axes = plt.subplots(len(groups) * 2, 8, figsize=(24, 6.4 * len(groups)), facecolor='black')
for gi, (title, sub) in enumerate(groups):
    for k, (fid, r) in enumerate(sub.iterrows()):
        ax = axes[gi * 2 + k // 8, k % 8]
        g = to3857(r.geometry); b = g.bounds; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        half = max(b[2] - b[0], b[3] - b[1]) * 0.75 + 15
        w = from_bounds(cx - half, cy - half, cx + half, cy + half, ds.transform)
        a = ds.read(window=w, boundless=True, fill_value=0)[:3]
        ax.imshow(np.moveaxis(a, 0, -1), extent=(cx - half, cx + half, cy - half, cy + half))
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        for pg in polys: ax.add_patch(MplPoly(np.array(pg.exterior.coords), fill=False, edgecolor='#00ff66', lw=1.6))
        ax.set_title(f"#{fid} {r.AREA_M2:.0f} m2 | NDVI {r.NDVI_MEAN:.2f} green {r.GREEN_M2:.0f} m2\nhome {int(r.G_DOM)} shop {int(r.G_NDOM)} gov {int(r.G_GOV)} farm {int(r.G_AGR)} | {r.SETTLE}", color='white', fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
    axes[gi * 2, 0].text(-0.02, 1.35, title, transform=axes[gi * 2, 0].transAxes, color='#ffd23b', fontsize=14, fontweight='bold', ha='left')
for ax in axes.flat:
    if not ax.images: ax.axis('off')
plt.tight_layout(h_pad=2.2)
out = f"{W13}/img/W14_ndvi_contact_sheet_T{T}.png"; plt.savefig(out, dpi=80, facecolor='black'); print('saved', out)
