"""W18 check maps (engineer, 2026-11-16): the future residential plots that cannot be a house plot - under 200 m2, or
narrower than 10 m (short side of the plot's smallest enclosing rectangle) - against the rest, before growth is put on
every future residential plot except these. Groves (W14's satellite test) shown apart, as the open decision.
One vector PDF per settlement: overview with numbered sheet frames, then A3 sheets at 1:5,000 over the odd plots,
each odd plot labelled with its area (and its width when it is 200 m2 or more).
The small locator map is a raster image: drawn as vectors it repeated all of Ibri's plots on every page (45 MB). The maps
stay vector (Ibri 6 MB), and the labels are text, so a PDF search finds an area.
Usage: python map_odd_plots.py <settlement> [<settlement> ...]"""
import os, sys
import numpy as np, pandas as pd, pyogrio, shapely, openpyxl
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.backends.backend_pdf import PdfPages
plt.rcParams["pdf.fonttype"] = 42

names = [s.upper() for s in sys.argv[1:]]
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
MIN_AREA, MIN_WIDTH = 200.0, 10.0
SCALE, FS, PAGE, MAP, MINLAB = 5000, 5.0, (16.5, 11.7), [0.005, 0.005, 0.74, 0.95], 3
MW, MH = PAGE[0] * MAP[2] * 0.0254 * SCALE, PAGE[1] * MAP[3] * 0.0254 * SCALE

p = pyogrio.read_dataframe(os.path.join(W18, "gis", "W18_plots_2026_2100.shp"),
                           columns=["SETTLE", "STATUS", "AREA_M2", "MOH_USE", "IN_BOUND", "GROWTH"])
w14 = pyogrio.read_dataframe(os.path.join(W18, "..", "W14", "shp", "PLOTS_load.shp"), columns=["DERIVED"], read_geometry=False)
assert len(w14) == len(p)
p["S"] = p.SETTLE.str.strip().str.upper()
p["GROVE"] = (w14.DERIVED == "Agricultural").values
p["FUTRES"] = ((p.STATUS == "Future") & (p.IN_BOUND == 1) & p.MOH_USE.str.contains("Resid", case=False, na=False)).values
sb = pyogrio.read_dataframe(os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp"), columns=["SETTLE"])
sb["S"] = sb.SETTLE.str.strip().str.upper()
md = openpyxl.load_workbook(os.path.join(W18, "..", "..", "temp", "recent updates by the team", "New Calculation MH.xlsx"),
                            data_only=True)["MOHUP DATA - NA"]
team_c = {md.cell(r, 1).value.strip().upper(): md.cell(r, 3).value for r in range(2, md.max_row + 1)
          if md.cell(r, 1).value and md.cell(r, 1).value != "Total"}


def sides(g):
    """long side, short side and angle of the long side of the plot's smallest enclosing rectangle"""
    xs, ys = g.minimum_rotated_rectangle.exterior.coords.xy
    e = sorted([(np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]), np.degrees(np.arctan2(ys[i + 1] - ys[i], xs[i + 1] - xs[i]))) for i in (0, 1)],
               reverse=True)
    return e[0][0], e[1][0], (e[0][1] + 90) % 180 - 90


CATS = [("existing plot", "#d9d9d9"), ("future residential: takes growth", "#9ecae1"),
        ("future residential: grove", "#a1d99b"), ("ODD: under 200 m²", "#d62728"),
        ("ODD: narrower than 10 m", "#ff7f0e"), ("other: not residential / outside", "white")]
HAND = [Patch(fc=c, ec="#9e9e9e", label=l) for l, c in CATS] + [
    plt.Line2D([], [], ls="", marker="o", ms=9, mfc="none", mec="#d62728", mew=1.2, label="odd plot, circled (most are tiny)"),
    plt.Line2D([], [], color="black", ls="--", lw=1.2, label="settlement boundary"),
    plt.Line2D([], [], ls="", label="numbers: area m²; width m on\nplots of 200 m² or more")]


def draw(ax, v, s, b=None):
    for k, (_, c) in enumerate(CATS):
        m = v.CAT == k
        if m.any(): v[m].plot(ax=ax, color=c, edgecolor="#9e9e9e", linewidth=0.35, zorder=2 if k < 3 else 3)
    sb[sb.S == s].boundary.plot(ax=ax, color="black", linewidth=1.3, linestyle="--", zorder=4)
    o = v[v.CAT.isin([3, 4])]
    c = o.geometry.representative_point()   # a ring on every odd plot: a 40 m2 sliver is 1 mm across at 1:5,000
    ax.scatter(c.x, c.y, s=55 if b is not None else 10, facecolors="none", edgecolors=np.where(o.CAT == 3, "#d62728", "#ff7f0e"),
               linewidths=1.0 if b is not None else 0.6, zorder=4.7)
    n = 0
    if b is None: return n                     # the overview carries no labels
    for (_, r), pt in zip(o.iterrows(), c):
        if not (b[0] < pt.x < b[2] and b[1] < pt.y < b[3]): continue
        t = f"{r.AREA_M2:,.0f}" if r.AREA_M2 < MIN_AREA else f"{r.AREA_M2:,.0f} / {r.WIDTH:.1f} m"
        ax.annotate(t, (pt.x, pt.y), xytext=(0, 6.5), textcoords="offset points", ha="center", va="bottom", fontsize=FS,
                    zorder=5, annotation_clip=True, path_effects=[pe.withStroke(linewidth=1.6, foreground="white")])
        n += 1
    return n


def sheets(d):
    """greedy A3 sheets over the odd plots (as map_plot_flows.py); kept when they hold MINLAB odd plots or more"""
    c = d[d.CAT.isin([3, 4])].geometry.representative_point(); X = np.c_[c.x, c.y]
    left = np.ones(len(X), bool); out = []; alone = 0
    while left.any():
        best = (0, None)
        for i in np.where(left)[0]:
            for ox in (-0.35, 0, 0.35):
                for oy in (-0.35, 0, 0.35):
                    cx, cy = X[i, 0] + ox * MW, X[i, 1] + oy * MH
                    m = left & (abs(X[:, 0] - cx) < MW / 2 - 15) & (abs(X[:, 1] - cy) < MH / 2 - 15)
                    if m.sum() > best[0]: best = (m.sum(), m)
        n, m = best; left &= ~m
        if n < MINLAB: alone += n; continue
        cx, cy = (X[m, 0].min() + X[m, 0].max()) / 2, (X[m, 1].min() + X[m, 1].max()) / 2
        out.append((cx - MW / 2, cy - MH / 2, cx + MW / 2, cy + MH / 2))
    return sorted(out, key=lambda b: (-round((b[1] + b[3]) / 2 / MH), b[0])), alone


def locator(fig, d, tiles, k):
    loc = fig.add_axes([0.765, 0.02, 0.22, 0.30]); loc.set_axis_off()
    d.plot(ax=loc, color="#bdbdbd", linewidth=0, rasterized=True)
    for kk, bb in enumerate(tiles, 1):
        loc.add_patch(plt.Rectangle((bb[0], bb[1]), bb[2] - bb[0], bb[3] - bb[1], fill=(kk == k), fc="#d62728",
                                    alpha=0.35 if kk == k else 1, ec="#555555", lw=0.6))
        loc.text((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, str(kk), fontsize=5, ha="center", va="center")
    loc.set_aspect("equal")


os.makedirs(os.path.join(W18, "img"), exist_ok=True)
for s in names:
    d = p[p.S == s].copy(); assert len(d), s
    sd = np.array([sides(g) for g in d.geometry]); d["LONG"], d["WIDTH"], d["ANG"] = sd[:, 0], sd[:, 1], sd[:, 2]
    odd_small = d.FUTRES & (d.AREA_M2 < MIN_AREA)
    odd_narrow = d.FUTRES & ~odd_small & (d.WIDTH < MIN_WIDTH)
    grove = d.FUTRES & ~odd_small & ~odd_narrow & d.GROVE
    take = d.FUTRES & ~odd_small & ~odd_narrow & ~d.GROVE
    d["CAT"] = np.select([d.STATUS == "Existing", take, grove, odd_small, odd_narrow], [0, 1, 2, 3, 4], 5)
    tiles, alone = sheets(d)
    rows = [["Team's future residential plots", f"{team_c.get(s, 0):,}"],
            ["Future residential plots, in the layer", f"{int(d.FUTRES.sum()):,}"],
            ["Odd: under 200 m²", f"{int(odd_small.sum()):,}"],
            ["Odd: narrower than 10 m", f"{int(odd_narrow.sum()):,}"],
            ["Groves", f"{int(grove.sum()):,}"],
            ["Take growth: all but odd, groves out", f"{int(take.sum()):,}"],
            ["Take growth: all but odd, groves in", f"{int((take | grove).sum()):,}"],
            ["Take growth now (200-2,000 m², shape tests)", f"{int(d.GROWTH.sum()):,}"],
            ["Odd plots on no detail sheet (isolated)", f"{alone:,}"]]
    f = os.path.join(W18, "img", f"oddplots_{s.replace(' ', '_')}.pdf")
    with PdfPages(f) as pdf:
        fig = plt.figure(figsize=PAGE)
        ax = fig.add_axes(MAP); side = fig.add_axes([0.755, 0.005, 0.24, 0.95]); side.set_axis_off()
        core = d[(d.CAT < 5)].geometry.centroid
        xmin, xmax = np.percentile(core.x, [1, 99]); ymin, ymax = np.percentile(core.y, [1, 99]); pad = 150
        ax.set_xlim(xmin - pad, xmax + pad); ax.set_ylim(ymin - pad, ymax + pad)
        draw(ax, d, s)
        for k, b in enumerate(tiles, 1):
            ax.add_patch(plt.Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec="#555555", lw=0.8, ls="-.", zorder=6))
            ax.text(b[0] + 25, b[3] - 25, str(k), fontsize=9, weight="bold", color="#555555", ha="left", va="top", zorder=6, clip_on=True)
        ax.set_xlim(xmin - pad, xmax + pad); ax.set_ylim(ymin - pad, ymax + pad); ax.set_aspect("equal"); ax.set_axis_off()
        side.legend(handles=HAND, title="Future plots: can it be a house plot?", loc="upper left", fontsize=9, title_fontsize=11, frameon=False)
        tb = side.table(cellText=rows, bbox=[0, 0.02, 1, 0.45], colWidths=[0.75, 0.25], cellLoc="left")
        tb.auto_set_font_size(False); tb.set_fontsize(8.5)
        fig.suptitle(f"{s.title()}: odd-shaped future residential plots (under 200 m² or narrower than 10 m) - overview",
                     fontsize=14, x=0.01, ha="left", y=0.995)
        pdf.savefig(fig, bbox_inches="tight", dpi=130); plt.close(fig)
        for k, b in enumerate(tiles, 1):
            fig = plt.figure(figsize=PAGE)
            ax = fig.add_axes(MAP); side = fig.add_axes([0.755, 0.005, 0.24, 0.95]); side.set_axis_off()
            ax.set_xlim(b[0], b[2]); ax.set_ylim(b[1], b[3])
            v = d.iloc[d.sindex.query(shapely.box(*b), predicate="intersects")]
            n = draw(ax, v, s, b)
            ax.set_xlim(b[0], b[2]); ax.set_ylim(b[1], b[3]); ax.set_aspect("equal"); ax.set_axis_off()
            sx, sy = b[0] + 40, b[1] + 40
            for z, c in ((0, "black"), (100, "white")):
                ax.add_patch(plt.Rectangle((sx + z, sy), 100, 12, fc=c, ec="black", lw=0.8, zorder=7))
            for z in (0, 100, 200): ax.text(sx + z, sy + 20, f"{z}", fontsize=8, ha="center", va="bottom", zorder=7)
            ax.text(sx + 215, sy + 6, "m", fontsize=8, va="center", zorder=7)
            side.legend(handles=HAND, title="Future plots: can it be a house plot?", loc="upper left", fontsize=9, title_fontsize=11, frameon=False)
            side.text(0, 0.50, f"Sheet {k} of {len(tiles)}\nScale 1:{SCALE:,} at A3\n{n} odd plots labelled here", fontsize=11, va="top",
                      transform=side.transAxes)
            locator(fig, d, tiles, k)
            fig.suptitle(f"{s.title()}: odd-shaped future residential plots, sheet {k}", fontsize=14, x=0.01, ha="left", y=0.995)
            pdf.savefig(fig, dpi=130); plt.close(fig)
    print(f, "|", " | ".join(f"{a}: {b}" for a, b in rows), "| sheets", len(tiles))
