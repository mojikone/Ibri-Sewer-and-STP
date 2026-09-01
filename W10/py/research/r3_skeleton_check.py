"""Is the skeleton finding real streets? Sample pockets rendered over satellite imagery.

`auto_block` is 319.9 km of corridor that nobody drew. It was recovered by rasterising the
free space between platted plots, reducing it to a one-pixel skeleton and tracing that back
to lines. The method reads where the plots left room for a street rather than guessing, but
it has never been checked against the ground, and it is the single biggest open question
about the corridor network: 97.4 % of it was converted to pipe.

This renders a stratified sample of skeleton pockets over the Esri imagery, bare on the
left and with the skeleton on the right, so the judgement is made on what is visible rather
than on the method's description of itself.

The imagery is LOCAL ONLY and is never copied into the repository. Only the rendered
figures are, and they are derived work at a scale that carries no basemap value.

Run:  python r3_skeleton_check.py            # the stratified sample
      python r3_skeleton_check.py 41 88 120  # named pockets, for follow-up
"""
import os
import sys
import warnings

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")

IMAGERY = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
IMG_DIR = os.path.join(C.OUT, "img", "research")
OUT_RUN = os.path.join(C.OUT, "run")
CLUSTER_GROW_M = 60.0      # skeleton lines within this of each other are one pocket
PAD_FRAC = 0.18
N_PER_STRATUM = 3
SEED = 20260901


def pockets():
    cor = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors.shp"))
    ab = cor[cor.SRC == "auto_block"].reset_index(drop=True)
    blob = gpd.GeoDataFrame(
        geometry=[unary_union(ab.geometry.buffer(CLUSTER_GROW_M))], crs=C.EPSG)
    blob = blob.explode(index_parts=False).reset_index(drop=True)
    j = gpd.sjoin(ab[["geometry"]], blob.reset_index()[["index", "geometry"]],
                  how="left", predicate="intersects")
    j = j[~j.index.duplicated(keep="first")]
    ab["POCKET"] = j["index"].values
    g = ab.groupby("POCKET").agg(lines=("geometry", "size"),
                                 km=("geometry", lambda s: s.length.sum() / 1000))
    g["cx"] = ab.groupby("POCKET").geometry.apply(lambda s: s.unary_union.centroid.x)
    g["cy"] = ab.groupby("POCKET").geometry.apply(lambda s: s.unary_union.centroid.y)
    return ab, g.sort_values("km", ascending=False)


def render(pid, ab, plots, other, dst, title):
    sub = ab[ab.POCKET == pid]
    minx, miny, maxx, maxy = sub.total_bounds
    w, h = maxx - minx, maxy - miny
    pad = max(PAD_FRAC * max(w, h), 60)
    minx, miny, maxx, maxy = minx - pad, miny - pad, maxx + pad, maxy + pad
    # keep the frame square so nothing is stretched
    cx, cy, s = (minx + maxx) / 2, (miny + maxy) / 2, max(maxx - minx, maxy - miny) / 2
    minx, maxx, miny, maxy = cx - s, cx + s, cy - s, cy + s

    bb = gpd.GeoDataFrame(geometry=[box(minx, miny, maxx, maxy)], crs=C.EPSG)
    bb3857 = bb.to_crs(3857).total_bounds
    with rasterio.open(IMAGERY) as src:
        win = from_bounds(*bb3857, transform=src.transform)
        arr = src.read(window=win, boundless=True, fill_value=255)
    img = np.transpose(arr, (1, 2, 0))
    ext3857 = (bb3857[0], bb3857[2], bb3857[1], bb3857[3])

    sub3 = sub.to_crs(3857)
    pl3 = plots[plots.intersects(box(minx, miny, maxx, maxy))].to_crs(3857)
    ot3 = other[other.intersects(box(minx, miny, maxx, maxy))].to_crs(3857)

    fig, axes = plt.subplots(1, 2, figsize=(17, 8.9), dpi=105)
    for k, ax in enumerate(axes):
        ax.imshow(img, extent=ext3857, interpolation="bilinear")
        if k == 1:
            if len(pl3):
                pl3.boundary.plot(ax=ax, color="#ffd400", lw=0.8, alpha=0.95)
            if len(ot3):
                ot3.plot(ax=ax, color="#00b0ff", lw=2.0, alpha=0.95)
            sub3.plot(ax=ax, color="#ff1e1e", lw=2.4)
        ax.set_xlim(ext3857[0], ext3857[1])
        ax.set_ylim(ext3857[2], ext3857[3])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("imagery only" if k == 0 else
                     "red = auto_block skeleton · blue = draft/auto_road · "
                     "yellow = plot boundaries", fontsize=11)
    # scale bar, drawn in 3857 but labelled in ground metres at this latitude
    span3857 = ext3857[1] - ext3857[0]
    span_m = maxx - minx
    for tgt in (1000, 500, 200, 100, 50):
        if tgt < 0.45 * span_m:
            break
    bar3857 = span3857 * tgt / span_m
    x0 = ext3857[0] + 0.06 * span3857
    y0 = ext3857[2] + 0.05 * (ext3857[3] - ext3857[2])
    for ax in axes:
        ax.plot([x0, x0 + bar3857], [y0, y0], color="white", lw=5,
                solid_capstyle="butt")
        ax.plot([x0, x0 + bar3857], [y0, y0], color="black", lw=2.5,
                solid_capstyle="butt")
        ax.text(x0 + bar3857 / 2, y0 + 0.018 * (ext3857[3] - ext3857[2]),
                f"{tgt} m", ha="center", color="white", fontsize=11,
                bbox=dict(fc="black", ec="none", alpha=0.55, pad=1.5))
    fig.suptitle(title, fontsize=13, y=0.975)
    fig.tight_layout(rect=[0, 0, 1, 0.955])
    fig.savefig(dst, facecolor="white")
    plt.close(fig)
    return span_m


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    ab, g = pockets()
    print(f"auto_block: {len(ab):,} lines, {ab.length.sum()/1000:.1f} km in "
          f"{len(g):,} pockets")
    print(f"   pocket length km: median {g.km.median():.3f}  p90 {g.km.quantile(.9):.3f} "
          f" max {g.km.max():.2f}")
    g.round(3).to_csv(os.path.join(OUT_RUN, "r3_pockets.csv"))

    cor = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors.shp"))
    other = cor[cor.SRC.isin(["draft", "auto_road"])].reset_index(drop=True)
    plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)

    ids = [int(x) for x in sys.argv[1:]]
    if not ids:
        # stratified by LENGTH, not by count: a random pocket is a 20 m fragment, and
        # sampling by count would check twelve fragments and none of the corridor that
        # actually carries the network.
        gg = g.sort_values("km")
        cum = gg.km.cumsum() / gg.km.sum()
        rng = np.random.default_rng(SEED)
        ids = []
        for lo, hi in ((0, .25), (.25, .5), (.5, .75), (.75, 1.0)):
            pool = gg.index[(cum > lo) & (cum <= hi)].to_numpy()
            take = rng.choice(pool, size=min(N_PER_STRATUM, len(pool)), replace=False)
            ids.extend(int(t) for t in take)
    print(f"\nrendering {len(ids)} pockets: {ids}")

    rows = []
    for k, pid in enumerate(ids, 1):
        r = g.loc[pid]
        near = plots[plots.distance(ab[ab.POCKET == pid].unary_union) < 60]
        t = (f"auto_block pocket {pid} — {r.km:.2f} km in {int(r.lines)} lines, "
             f"{len(near)} plots within 60 m   ({r.cx:.0f} E, {r.cy:.0f} N)")
        dst = os.path.join(IMG_DIR, f"R3_pocket_{pid:04d}.png")
        span = render(pid, ab, plots, other, dst, t)
        rows.append({"pocket": pid, "km": round(float(r.km), 3),
                     "lines": int(r.lines), "plots60m": len(near),
                     "x": round(float(r.cx)), "y": round(float(r.cy)),
                     "frame_m": round(span), "png": os.path.basename(dst)})
        print(f"   {k:2d}/{len(ids)}  pocket {pid:5d}  {r.km:7.3f} km  "
              f"{len(near):4d} plots  frame {span:.0f} m  -> {os.path.basename(dst)}")
    pd.DataFrame(rows).to_csv(os.path.join(OUT_RUN, "r3_sample.csv"), index=False)


if __name__ == "__main__":
    main()
