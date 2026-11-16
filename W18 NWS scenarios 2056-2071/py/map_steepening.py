"""W18: which pipes above DN200 are steepened to reach 0.75 m/s at the 2031 peak, and by how much over the laid
gradient, for gradient limits of 0.50, 0.75 and 1.00 % (engineer, 2026-11-16). One map per case, with the length in
each band of increase. Reads the check run of py/selfcleansing_slope.py.
Usage: python map_steepening.py <tag> <check-run dir> <label for the run>"""
import os, sys
import numpy as np, pandas as pd, pyogrio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

tag, run, runlab = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
st = pyogrio.read_dataframe(os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp"))
nodes = pd.read_csv(os.path.join(run, f"nodes_{tag}.csv")).set_index("id")
links = pd.read_csv(os.path.join(run, f"links_{tag}.csv"))
pipes = pd.read_csv(os.path.join(run, f"pipes_{tag}.csv")).set_index("label")
links = links.join(pipes[["V31_MODEL"]], on="label")
seg = np.stack([nodes.loc[links.UP, ["x", "y"]].values, nodes.loc[links.DN, ["x", "y"]].values], axis=1)
big = links.diameter_mm.values > 177
BANDS = [(1.0, 1.25, "#fdd49e", "steeper by up to 25 %"), (1.25, 1.5, "#fc8d59", "25 to 50 %"),
         (1.5, 2.0, "#d7301f", "50 to 100 %"), (2.0, 1e9, "#7f0000", "more than double")]
for T in (0.005, 0.0075, 0.01):
    ok_laid = big & (links.V31_MODEL.values >= 0.75)
    steep = big & (links.S_REQ.values > links.S_LAID.values) & (links.S_REQ.values <= T)
    fail = big & ~ok_laid & ~steep
    ratio = np.where(steep, links.S_REQ.values / links.S_LAID.values, np.nan)
    fig, ax = plt.subplots(figsize=(16.5, 11.7), dpi=150)
    st.boundary.plot(ax=ax, color="#9e9e9e", linewidth=0.5, zorder=1)
    ax.add_collection(LineCollection(seg[~big], colors="#e0e0e0", linewidths=0.3, zorder=1.5))
    ax.add_collection(LineCollection(seg[ok_laid], colors="#31a354", linewidths=1.2, zorder=2))
    ax.add_collection(LineCollection(seg[fail], colors="#7b3294", linewidths=1.4, zorder=3))
    rows = []
    for lo, hi, c, lab in BANDS:
        m = steep & (ratio > lo) & (ratio <= hi)
        ax.add_collection(LineCollection(seg[m], colors=c, linewidths=1.3, zorder=4))
        rows.append([f"Steepened, {lab}", f"{links.length_m[m].sum()/1000:.1f} km"])
    rows = [["Pipes above DN200", f"{links.length_m[big].sum()/1000:.1f} km"],
            ["Reach 0.75 m/s at the laid gradient", f"{links.length_m[ok_laid].sum()/1000:.1f} km"]] + rows + \
           [["Steepened, total", f"{links.length_m[steep].sum()/1000:.1f} km"],
            ["Still below 0.75 m/s at the limit", f"{links.length_m[fail].sum()/1000:.1f} km"]]
    for oid, o in nodes[nodes.label.isin(["O1"])].iterrows():
        ax.scatter(o.x, o.y, s=140, marker="s", color="#2ca02c", edgecolor="black", zorder=6)
        ax.annotate("STP at O1", (o.x, o.y), xytext=(-70, -30), textcoords="offset points", fontsize=11, weight="bold",
                    bbox=dict(boxstyle="round", fc="white", ec="#2ca02c"), zorder=7)
    ax.set_aspect("equal"); ax.set_axis_off()
    xmin, ymin, xmax, ymax = st.total_bounds; ax.set_xlim(xmin - 500, xmax + 500); ax.set_ylim(ymin - 500, ymax + 500)
    ax.legend(handles=[Line2D([], [], color=c, lw=3, label=f"Steepened: {lab}") for _, _, c, lab in BANDS]
              + [Line2D([], [], color="#31a354", lw=3, label="Reaches 0.75 m/s at the laid gradient"),
                 Line2D([], [], color="#7b3294", lw=3, label=f"Still below 0.75 m/s at {T*100:.2f} %"),
                 Line2D([], [], color="#e0e0e0", lw=2, label="DN200 (outside the rule)")],
              title="Pipes above DN200, increase over the laid gradient", loc="upper left", fontsize=10, title_fontsize=10)
    tb = ax.table(cellText=rows, loc="lower right", colWidths=[0.30, 0.09], cellLoc="left")
    tb.auto_set_font_size(False); tb.set_fontsize(9.5); tb.scale(1, 1.4)
    ax.set_title(f"{runlab}: pipes steepened to reach 0.75 m/s at the 2031 peak, gradient limited to {T*100:.2f} %", fontsize=13, loc="left")
    f = os.path.join(W18, "img", f"steepening_{tag}_{int(round(T*100*100)):03d}.png")
    fig.savefig(f, bbox_inches="tight"); plt.close(fig); print(f, "| steepened km", round(links.length_m[steep].sum()/1000, 1))
