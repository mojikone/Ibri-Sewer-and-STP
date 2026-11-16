"""W18: depth of the sewers when the pipes above DN200 are steepened to reach 0.75 m/s at the 2031 peak, up to a
threshold gradient of 0.50, 0.75 and 1.00 % (engineer, 2026-11-16). One map per case: pipes by depth to invert (the
deeper end), the STP labelled with the depth of the arriving sewer, the pumping-station outfalls that go more than
1 m deeper labelled too, and a box with the case's figures.
Reads the check run of py/selfcleansing_slope.py.
Usage: python map_depth_cases.py <tag, e.g. SC1-2056> <check-run dir> <plant outfalls, e.g. O1> <label for the run>"""
import os, sys
import numpy as np, pandas as pd, pyogrio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

tag, run, plants, runlab = sys.argv[1], sys.argv[2], sys.argv[3].split(","), sys.argv[4]
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
SETTLE = os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp")
nodes = pd.read_csv(os.path.join(run, f"nodes_{tag}.csv")).set_index("id")
links = pd.read_csv(os.path.join(run, f"links_{tag}.csv"))
th = pd.read_csv(os.path.join(run, f"thresholds_{tag}.csv")).set_index("threshold_pct")
BANDS = [(0, 3, "#c6dbef", "up to 3 m"), (3, 6, "#6baed6", "3 to 6 m"), (6, 9, "#2171b5", "6 to 9 m"),
         (9, 12, "#08306b", "9 to 12 m"), (12, 1e9, "#d62728", "over 12 m")]
st = pyogrio.read_dataframe(SETTLE)
xy = nodes[["x", "y"]]
seg = np.stack([xy.loc[links.UP].values, xy.loc[links.DN].values], axis=1)
outfalls = nodes[nodes.label.str.match(r"^O\d+$", na=False)]
os.makedirs(os.path.join(W18, "img"), exist_ok=True)

for col, T in (("inv_0.50", 0.50), ("inv_0.75", 0.75), ("inv_1.00", 1.00)):
    depth = nodes.ground - nodes[col]
    d_pipe = np.fmax(depth.reindex(links.UP).values, depth.reindex(links.DN).values)
    fig, ax = plt.subplots(figsize=(16.5, 11.7), dpi=150)
    st.boundary.plot(ax=ax, color="#9e9e9e", linewidth=0.5, zorder=1)
    for lo, hi, c, lab in BANDS:
        m = (d_pipe > lo) & (d_pipe <= hi)
        ax.add_collection(LineCollection(seg[m], colors=c, linewidths=0.5 if hi <= 9 else 1.1, zorder=2 if hi <= 9 else 3))
    deep_mh = nodes[(depth > 12) & ~nodes.index.isin(outfalls.index)]
    ax.scatter(deep_mh.x, deep_mh.y, s=4, color="#d62728", zorder=4)
    d0 = nodes.ground - nodes.inv_laid
    for oid, o in outfalls.iterrows():
        dnew, dold = depth[oid], d0[oid]
        if o.label in plants:
            ax.scatter(o.x, o.y, s=140, marker="s", color="#2ca02c", edgecolor="black", zorder=6)
            ax.annotate(f"STP at {o.label}\nsewer arriving {dnew:.1f} m deep" + (f" (+{dnew-dold:.1f} m)" if dnew - dold > 0.05 else " (unchanged)"),
                        (o.x, o.y), xytext=(-150, -55), textcoords="offset points", fontsize=11, weight="bold",
                        bbox=dict(boxstyle="round", fc="white", ec="#2ca02c"), arrowprops=dict(arrowstyle="-", color="#2ca02c"), zorder=7)
        elif dnew - dold > 1.0:
            ax.scatter(o.x, o.y, s=50, marker="^", color="#ff7f0e", edgecolor="black", zorder=6)
            ax.annotate(f"{o.label} station {dnew:.1f} m (+{dnew-dold:.1f})", (o.x, o.y), xytext=(8, 8), textcoords="offset points",
                        fontsize=9, bbox=dict(boxstyle="round", fc="white", ec="#ff7f0e", alpha=0.9), zorder=7)
    ax.set_aspect("equal"); ax.set_axis_off()
    xmin, ymin, xmax, ymax = st.total_bounds; ax.set_xlim(xmin - 500, xmax + 500); ax.set_ylim(ymin - 500, ymax + 500)
    ax.legend(handles=[Line2D([], [], color=c, lw=2.5, label=lab) for _, _, c, lab in BANDS]
              + [Line2D([], [], marker="o", ls="", color="#d62728", ms=4, label="manhole deeper than 12 m"),
                 Line2D([], [], marker="s", ls="", color="#2ca02c", mec="black", ms=9, label="STP"),
                 Line2D([], [], marker="^", ls="", color="#ff7f0e", mec="black", ms=7, label="pumping-station outfall more than 1 m deeper")],
              title="Depth to invert (deeper end of each pipe)", loc="upper left", fontsize=10, title_fontsize=10)
    r = th.loc[T]
    rows = [["Length above DN200 reaching 0.75 m/s at the 2031 peak", f"{r.pass_len_pct:.0f} %"],
            ["Pipes steepened", f"{int(r.steepened_n):,} ({r.steepened_km:.0f} km)"],
            ["Manholes deeper than 12 m (design as laid)", f"{int(r.mh_over_12m):,} ({int(r.mh_over_12m_before):,})"],
            ["Deepest manhole", f"{r.deepest_m:.1f} m"],
            ["Largest added depth", f"{r.max_added_m:.1f} m"]]
    tb = ax.table(cellText=rows, loc="lower right", colWidths=[0.36, 0.10], cellLoc="left")
    tb.auto_set_font_size(False); tb.set_fontsize(9.5); tb.scale(1, 1.45)
    ax.set_title(f"{runlab}: sewer depth with the pipes above DN200 steepened to reach 0.75 m/s at the 2031 peak, gradient limited to {T:.2f} %",
                 fontsize=13, loc="left")
    f = os.path.join(W18, "img", f"depth_{tag}_{int(round(T*100)):03d}.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); print(f)
