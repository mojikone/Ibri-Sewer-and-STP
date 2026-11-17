"""W18 check maps (engineer, 2026-11-16): one settlement per map, plots filled by their average flow in a blue
gradient, existing plots outlined red, the area labelled on every plot over 1,000 m2 - to judge the shape and area
limits of the growth plots (200-1,000 m2, compact >= 0.6, aspect <= 3). Reads gis/W18_plots_2026_2100.shp.
Usage: python map_plot_flows.py <year> <settlement> [<settlement> ...]"""
import os, sys
import numpy as np, pandas as pd, pyogrio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

year, names = int(sys.argv[1]), [s.upper() for s in sys.argv[2:]]
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
q = f"Q_{year}"
p = pyogrio.read_dataframe(os.path.join(W18, "gis", "W18_plots_2026_2100.shp"),
                           columns=["SETTLE", "STATUS", "AREA_M2", "GROWTH", "IN_BOUND", "LANDUSE", q])
p["S"] = p.SETTLE.str.strip().str.upper()
sb = pyogrio.read_dataframe(os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp"), columns=["SETTLE"])
sb["S"] = sb.SETTLE.str.strip().str.upper()
BR = [0, 0.25, 0.5, 1, 2, 4, 8, 1e9]
LAB = ["up to 0.25", "0.25 to 0.5", "0.5 to 1", "1 to 2", "2 to 4", "4 to 8", "over 8"]
BLUES = plt.get_cmap("Blues")(np.linspace(0.18, 1.0, len(LAB)))
os.makedirs(os.path.join(W18, "img"), exist_ok=True)

# ---- detail sheets (engineer, 2026-11-16: "I said label the area of plots bigger than 1000 m2"): on the overview of
# a large settlement the 4.5 pt labels overlap and cannot be read, so each settlement also gets A3 sheets at 1:4,000,
# overview + sheets in one vector PDF (text searchable), every plot over 1,000 m2 labelled at 6 pt, the label
# turned along the plot when the plot is too narrow for it level ----
from matplotlib.backends.backend_pdf import PdfPages
import shapely
plt.rcParams["pdf.fonttype"] = 42
SCALE, FS, PAGE, MAP, MINLAB = 5000, 5.5, (16.5, 11.7), [0.005, 0.005, 0.74, 0.95], 5
MW, MH = PAGE[0] * MAP[2] * 0.0254 * SCALE, PAGE[1] * MAP[3] * 0.0254 * SCALE   # ground metres per sheet


def sheet_grid(d):
    """Sheets of MW x MH m placed greedily over the labelled plots (over 1,000 m2), each covering as many still
    unplaced labels as it can; a sheet is kept when it carries MINLAB labels or more - fewer labels are isolated
    and do not overlap on the overview. A fixed grid gave Suwayda al Ma 68 sheets over its 11 x 12 km."""
    c = d[d.AREA_M2 > 1000].geometry.representative_point(); X = np.c_[c.x, c.y]
    left = np.ones(len(X), bool); out = []
    while left.any():
        best = (0, None)
        for i in np.where(left)[0]:
            for ox in (-0.35, 0, 0.35):
                for oy in (-0.35, 0, 0.35):
                    cx, cy = X[i, 0] + ox * MW, X[i, 1] + oy * MH
                    m = left & (abs(X[:, 0] - cx) < MW / 2 - 15) & (abs(X[:, 1] - cy) < MH / 2 - 15)
                    if m.sum() > best[0]: best = (m.sum(), m)
        n, m = best; left &= ~m
        if n < MINLAB: continue
        cx, cy = (X[m, 0].min() + X[m, 0].max()) / 2, (X[m, 1].min() + X[m, 1].max()) / 2   # centred on its labels
        out.append((cx - MW / 2, cy - MH / 2, cx + MW / 2, cy + MH / 2))
    return sorted(out, key=lambda b: (-round((b[1] + b[3]) / 2 / MH), b[0]))   # north to south, then west to east


def label_angle(geom, txt):
    """0 if the label fits level, else the angle of the plot's long side (when the label fits along it)."""
    w = len(txt) * 0.6 * FS / 72 * 0.0254 * SCALE
    xs, ys = geom.minimum_rotated_rectangle.exterior.coords.xy
    e = [(np.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]), np.degrees(np.arctan2(ys[i + 1] - ys[i], xs[i + 1] - xs[i]))) for i in (0, 1)]
    (L, a), (S, _) = sorted(e, reverse=True)
    if S >= w or L < w: return 0.0
    return (a + 90) % 180 - 90


def detail_sheet(pdf, d, s, b, k, tiles, hand):
    fig = plt.figure(figsize=PAGE)
    ax = fig.add_axes(MAP); side = fig.add_axes([0.755, 0.005, 0.24, 0.95]); side.set_axis_off()
    v = d.iloc[d.sindex.query(shapely.box(*b), predicate="intersects")]
    zero = v[q] <= 0
    if zero.any(): v[zero].plot(ax=ax, color="white", edgecolor="#9e9e9e", linewidth=0.4, zorder=1)
    for i in range(len(LAB)):
        m = (~zero) & (v[q] > BR[i]) & (v[q] <= BR[i + 1])
        if m.any(): v[m].plot(ax=ax, color=BLUES[i], edgecolor="#9e9e9e", linewidth=0.4, zorder=2)
    ex = v.STATUS == "Existing"
    if ex.any(): v[ex].boundary.plot(ax=ax, color="#d62728", linewidth=1.0, zorder=3)
    sb[sb.S == s].boundary.plot(ax=ax, color="black", linewidth=1.4, linestyle="--", zorder=4)
    n = 0
    for _, r in v[v.AREA_M2 > 1000].iterrows():
        c = r.geometry.representative_point(); t = f"{r.AREA_M2:,.0f}"
        if not (b[0] < c.x < b[2] and b[1] < c.y < b[3]): continue
        ax.text(c.x, c.y, t, rotation=label_angle(r.geometry, t), rotation_mode="anchor", ha="center", va="center",
                fontsize=FS, zorder=5, clip_on=True, bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none", alpha=0.65))
        n += 1
    ax.set_xlim(b[0], b[2]); ax.set_ylim(b[1], b[3]); ax.set_aspect("equal"); ax.set_axis_off()
    sx, sy = b[0] + 40, b[1] + 40   # 200 m scale bar
    for z, c in ((0, "black"), (100, "white")):
        ax.add_patch(plt.Rectangle((sx + z, sy), 100, 12, fc=c, ec="black", lw=0.8, zorder=7))
    for z in (0, 100, 200): ax.text(sx + z, sy + 20, f"{z}", fontsize=8, ha="center", va="bottom", zorder=7)
    ax.text(sx + 215, sy + 6, "m", fontsize=8, va="center", zorder=7)
    side.legend(handles=hand, title=f"Average flow {year}, per plot", loc="upper left", fontsize=10, title_fontsize=11, frameon=False)
    side.text(0, 0.50, f"Sheet {k} of {len(tiles)}\nScale 1:{SCALE:,} at A3\n{n} plots over 1,000 m² labelled here",
              fontsize=11, va="top", transform=side.transAxes)
    loc = fig.add_axes([0.765, 0.02, 0.22, 0.30]); loc.set_axis_off()
    d.plot(ax=loc, color="#bdbdbd", linewidth=0)
    for kk, bb in enumerate(tiles, 1):
        loc.add_patch(plt.Rectangle((bb[0], bb[1]), bb[2] - bb[0], bb[3] - bb[1], fill=(kk == k), fc="#d62728", alpha=0.35 if kk == k else 1,
                                    ec="#555555", lw=0.6))
        loc.text((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, str(kk), fontsize=6, ha="center", va="center")
    loc.set_aspect("equal")
    fig.suptitle(f"{s.title()}: average flow per plot in {year}, sheet {k}", fontsize=14, x=0.01, ha="left", y=0.995)
    pdf.savefig(fig); plt.close(fig)
    return n


for s in names:
    d = p[p.S == s].copy(); assert len(d), s
    fig = plt.figure(figsize=(16.5, 11.7), dpi=200)
    ax = fig.add_axes([0.005, 0.005, 0.74, 0.95]); side = fig.add_axes([0.755, 0.005, 0.24, 0.95]); side.set_axis_off()
    zero = d[q] <= 0
    d[zero].plot(ax=ax, color="white", edgecolor="#9e9e9e", linewidth=0.3, zorder=1)
    for k in range(len(LAB)):
        m = (~zero) & (d[q] > BR[k]) & (d[q] <= BR[k + 1])
        if m.any(): d[m].plot(ax=ax, color=BLUES[k], edgecolor="#9e9e9e", linewidth=0.3, zorder=2)
    ex = d.STATUS == "Existing"
    d[ex].boundary.plot(ax=ax, color="#d62728", linewidth=0.8, zorder=3)
    sb[sb.S == s].boundary.plot(ax=ax, color="black", linewidth=1.2, linestyle="--", zorder=4)
    big = d[d.AREA_M2 > 1000]
    for _, r in big.iterrows():
        c = r.geometry.representative_point()
        ax.annotate(f"{r.AREA_M2:,.0f}", (c.x, c.y), ha="center", va="center", fontsize=4.5, color="black", zorder=5,
                    bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.6))
    # extent: the built and growth plots (1st-99th percentile of their centroids), so a settlement whose plots
    # straggle over kilometres still shows its town; plots beyond it are cut
    core = d[ex | (d.GROWTH == 1)].geometry.centroid
    xmin, xmax = np.percentile(core.x, [1, 99]); ymin, ymax = np.percentile(core.y, [1, 99]); pad = 150
    ax.set_xlim(xmin - pad, xmax + pad); ax.set_ylim(ymin - pad, ymax + pad)
    inview = d.geometry.intersects(__import__("shapely").box(xmin - pad, ymin - pad, xmax + pad, ymax + pad))
    ax.set_aspect("equal"); ax.set_axis_off()
    hand = [Patch(fc=c, ec="#9e9e9e", label=f"{l} m³/d") for c, l in zip(BLUES, LAB)] + [
        Patch(fc="white", ec="#9e9e9e", label="no flow"),
        Patch(fc="none", ec="#d62728", lw=1.5, label="existing plot"),
        plt.Line2D([], [], color="black", ls="--", lw=1.2, label="settlement boundary"),
        plt.Line2D([], [], ls="", label="numbers: area of plots over 1,000 m²")]
    side.legend(handles=hand, title=f"Average flow {year}, per plot", loc="upper left", fontsize=10, title_fontsize=11, frameon=False)
    fut = d.STATUS == "Future"
    rows = [["Plots: existing / empty", f"{int(ex.sum()):,} / {int(fut.sum()):,}"],
            ["Growth plots", f"{int(d.GROWTH.sum()):,}"],
            ["Empty > 1,000 m², no growth", f"{int((fut & (d.AREA_M2 > 1000)).sum()):,}"],
            ["Empty < 200 m², no growth", f"{int((fut & (d.AREA_M2 < 200)).sum()):,}"],
            ["Empty, outside boundary", f"{int((fut & (d.IN_BOUND == 0)).sum()):,}"],
            [f"Flow {year}: existing / growth", f"{d.loc[ex, q].sum():,.1f} / {d.loc[d.GROWTH == 1, q].sum():,.1f} m³/d"],
            [f"Flow per growth plot", f"{d.loc[d.GROWTH == 1, q].max():,.2f} m³/d"]]
    rows.append(["Plots beyond map edge", f"{int((~inview).sum()):,}"])
    tb = side.table(cellText=rows, bbox=[0, 0.02, 1, 0.42], colWidths=[0.6, 0.4], cellLoc="left")
    tb.auto_set_font_size(False); tb.set_fontsize(8.5)
    fig.suptitle(f"{s.title()}: average flow per plot in {year} (W18 loads)", fontsize=14, x=0.01, ha="left", y=0.995)
    tiles = sheet_grid(d)
    for k, b in enumerate(tiles, 1):   # the detail sheets, outlined on the overview
        ax.add_patch(plt.Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec="#555555", lw=0.9, ls="-.", zorder=6))
        ax.text(b[0] + 25, b[3] - 25, str(k), fontsize=11, weight="bold", color="#555555", ha="left", va="top", zorder=6, clip_on=True)
    f = os.path.join(W18, "img", f"plotflow_{year}_{s.replace(' ', '_')}.png")
    fig.savefig(f, bbox_inches="tight")
    with PdfPages(f[:-4] + ".pdf") as pdf:
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
        for k, b in enumerate(tiles, 1):
            nl = detail_sheet(pdf, d, s, b, k, tiles, hand)
            print(f"  sheet {k}/{len(tiles)}: {nl} labels")
    print(f, len(d), "plots,", len(big), "labelled,", len(tiles), "detail sheets")
