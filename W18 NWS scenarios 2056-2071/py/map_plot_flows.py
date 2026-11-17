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
    f = os.path.join(W18, "img", f"plotflow_{year}_{s.replace(' ', '_')}.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); print(f, len(d), "plots,", len(big), "labelled")
