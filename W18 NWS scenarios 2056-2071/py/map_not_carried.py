"""W18: the plots whose flow does not enter the network, in the engineer's two categories (2026-11-16):
inactive network (bad terrain) and farther than 200 m from an active sewer. Writes gis/not_carried_plots.gpkg (for the
QGIS report layout) and a draft map img/not_carried_plots.png with the flows of each category.
Reads results/loads/plot_loads.csv and not_carried.csv from nws_loads.py."""
import os
import numpy as np, pandas as pd, pyogrio
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
PLOTS = r"C:\Users\mojtaba\Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\SHP\Plots\Plots.shp"
SETTLE = os.path.join(W18, "..", "W14", "shp", "Settlements_merged.shp")
os.makedirs(os.path.join(W18, "gis"), exist_ok=True); os.makedirs(os.path.join(W18, "img"), exist_ok=True)
CAT = {"inactive manhole": "Inactive network (bad terrain)", "over 200 m from a sewer": "Farther than 200 m from the network"}
COL = {"Inactive network (bad terrain)": "#8e44ad", "Farther than 200 m from the network": "#d62728"}

g = pyogrio.read_dataframe(PLOTS, columns=["SETTLE", "STATUS"])
t = pd.read_csv(os.path.join(W18, "results", "loads", "plot_loads.csv"))
assert len(t) == len(g)
g["CATEGORY"] = t.WHY_OUT.fillna("").map(CAT).fillna("")
# only plots that carry flow; plots outside their settlement boundary carry none (engineer, 2026-11-16)
g.loc[t.Q_2071.values <= 0, "CATEGORY"] = ""
for c in ("Q_2031", "Q_2056", "Q_2071"): g[c] = t[c].values
g["D_PIPE_M"] = t.D_PIPE.values.round(1)
nc = g[g.CATEGORY != ""].copy()
pyogrio.write_dataframe(nc, os.path.join(W18, "gis", "not_carried_plots.gpkg"), layer="not_carried_plots")

nodes = pd.read_csv(r"D:\VBOX\bridge\out\inv_w17\nodes.csv").set_index("id")
cd = pd.read_csv(r"D:\VBOX\bridge\out\scen\S1\conduits_S1-2070.csv")
segs = np.stack([nodes.loc[cd.start, ["x", "y"]].values, nodes.loc[cd.stop, ["x", "y"]].values], axis=1)
act = cd.active.values == True

fig, ax = plt.subplots(figsize=(16.5, 11.7), dpi=150)
st = pyogrio.read_dataframe(SETTLE) if os.path.exists(SETTLE) else None
if st is not None:
    st.boundary.plot(ax=ax, color="#7f7f7f", linewidth=0.6, zorder=1)
flow = g.Q_2071.values > 0
g[(g.CATEGORY == "") & flow].plot(ax=ax, color="#c8c8c8", linewidth=0, zorder=2)
g[~flow].plot(ax=ax, color="#f2f2f2", edgecolor="#d9d9d9", linewidth=0.2, zorder=1.5)
ax.add_collection(LineCollection(segs[act], colors="#1f4e79", linewidths=0.35, zorder=3))
ax.add_collection(LineCollection(segs[~act], colors="#b07cc6", linewidths=0.35, linestyles="dotted", zorder=3))
for cat, col in COL.items():
    nc[nc.CATEGORY == cat].plot(ax=ax, color=col, linewidth=0, zorder=4)
ax.set_aspect("equal"); ax.set_axis_off()
xmin, ymin, xmax, ymax = g.total_bounds; ax.set_xlim(xmin - 500, xmax + 500); ax.set_ylim(ymin - 500, ymax + 500)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend(handles=[Patch(color=COL["Inactive network (bad terrain)"], label="Plot on the inactive network (bad terrain)"),
                   Patch(color=COL["Farther than 200 m from the network"], label="Plot farther than 200 m from the network"),
                   Patch(color="#c8c8c8", label="Plot served by the network"),
                   Patch(facecolor="#f2f2f2", edgecolor="#d9d9d9", label="Plot with no sewage flow (non-residential vacant, or outside its settlement boundary)"),
                   Line2D([], [], color="#1f4e79", lw=1, label="Sewer network"),
                   Line2D([], [], color="#b07cc6", lw=1, ls=":", label="Inactive network")],
          loc="upper left", frameon=True, fontsize=10)
# data box, bottom right
rows = [("", "2031", "2056", "2071")]
for cat in COL:
    s = nc[nc.CATEGORY == cat]
    rows.append((f"{cat} ({len(s):,} plots)", *(f"{s[c].sum():,.0f}" for c in ("Q_2031", "Q_2056", "Q_2071"))))
rows.append((f"Total not carried ({len(nc):,} plots)", *(f"{nc[c].sum():,.0f}" for c in ("Q_2031", "Q_2056", "Q_2071"))))
tb = ax.table(cellText=rows[1:], colLabels=rows[0], loc="lower right", colWidths=[0.30, 0.06, 0.06, 0.06], cellLoc="right")
tb.auto_set_font_size(False); tb.set_fontsize(9); tb.scale(1, 1.4)
ax.text(0.99, 0.175, "Average sewage flow not entering the network, m³/d", transform=ax.transAxes, ha="right", fontsize=10, weight="bold")
ax.set_title("Plots whose sewage does not enter the network", fontsize=14, loc="left")
fig.savefig(os.path.join(W18, "img", "not_carried_plots.png"), bbox_inches="tight")
print(nc.groupby("CATEGORY")[["Q_2031", "Q_2056", "Q_2071"]].sum().round(1).to_string()); print("plots", len(nc))
