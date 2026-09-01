"""Figures for the two research notes. Every one is read back after export.

A figure with a layer switched off renders almost nothing while its legend still looks
complete, so nothing here is trusted until the exported PNG has been opened and checked
against what it was supposed to show.

Run:  python r9_figures.py
"""
import os
import sys
import warnings

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")
IMG = os.path.join(C.OUT, "img", "research")
RUN = os.path.join(C.OUT, "run")
os.makedirs(IMG, exist_ok=True)

SRC_COL = {"draft": "#1f5fa9", "auto_road": "#2e9b4f",
           "auto_block": "#e2711d", "auto_link": "#c1272d"}
SRC_ORD = ["draft", "auto_road", "auto_block", "auto_link"]


def frame(ax, bnd):
    bnd.boundary.plot(ax=ax, color="#444", lw=0.8, zorder=1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")


def scalebar(ax, bnd, m=10000):
    x0, y0, x1, y1 = bnd.total_bounds
    sx = x0 + 0.05 * (x1 - x0)
    sy = y0 + 0.05 * (y1 - y0)
    ax.plot([sx, sx + m], [sy, sy], color="black", lw=3, solid_capstyle="butt",
            zorder=6)
    ax.text(sx + m / 2, sy + 0.018 * (y1 - y0), f"{m/1000:.0f} km", ha="center",
            fontsize=9, zorder=6)


def fig1(cq, bnd):
    """The corridor network by source."""
    fig, ax = plt.subplots(figsize=(13.5, 10), dpi=115)
    frame(ax, bnd)
    for s in SRC_ORD:
        sub = cq[cq.SRC == s]
        sub.plot(ax=ax, color=SRC_COL[s], lw=0.45 if s == "draft" else 0.6, zorder=3)
    km = cq.groupby("SRC").LEN_M.sum() / 1000
    ax.legend(handles=[Line2D([], [], color=SRC_COL[s], lw=2.5,
                              label=f"{s}  {km[s]:,.0f} km "
                                    f"({100*km[s]/km.sum():.0f} %)")
                       for s in SRC_ORD],
              loc="upper left", fontsize=10, frameon=True, framealpha=0.9)
    scalebar(ax, bnd)
    ax.set_title(f"W10 corridor network by source — {km.sum():,.0f} km in "
                 f"{len(cq):,} lines", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "R_F1_corridors_by_source.png"), facecolor="white")
    plt.close(fig)


def fig2(cq, bnd):
    """Where the corridors cannot be built."""
    fig, axes = plt.subplots(1, 3, figsize=(19, 5.6), dpi=112)
    specs = [("F_WADI", "on wadi ground (hazard class 4-6)", "#0f7fb5",
              cq.WADI_M.sum() / 1000),
             ("F_PLOT", "through the body of a registered plot", "#b5290f",
              cq.PLOTIN_M.sum() / 1000),
             ("F_DUP", "duplicated by a parallel corridor within 8 m", "#7a3fb5",
              cq.DUP_M.sum() / 1000)]
    for ax, (col, lab, colr, km) in zip(axes, specs):
        frame(ax, bnd)
        cq.plot(ax=ax, color="#d8d8d8", lw=0.25, zorder=2)
        bad = cq[cq[col] > 0.25]
        bad.plot(ax=ax, color=colr, lw=0.9, zorder=4)
        ax.set_title(f"{lab}\n{km:,.1f} km affected · "
                     f"{len(bad):,} lines more than 25 % affected", fontsize=11)
    scalebar(axes[0], bnd)
    fig.suptitle("W10 corridor defects — the whole network in grey, the affected "
                 "corridors picked out", fontsize=13, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    fig.savefig(os.path.join(IMG, "R_F2_corridor_defects.png"), facecolor="white")
    plt.close(fig)


def fig3():
    """Two charts: is the ground built, and is there a street there."""
    b = pd.read_csv(os.path.join(RUN, "r4_built_status.csv"))
    c = pd.read_csv(os.path.join(RUN, "r4_street_contrast.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2), dpi=118)

    ax = axes[0]
    b = b.set_index("source").reindex(SRC_ORD)
    cols = ["km_0pct_built", "km_under25pct", "km_25to75pct", "km_over75pct"]
    labs = ["no plot built", "under 25 % built", "25-75 % built", "over 75 % built"]
    shades = ["#f2c8a0", "#e0954a", "#8fb98f", "#2e7d3a"]
    left = np.zeros(len(b))
    for col, lab, sh in zip(cols, labs, shades):
        ax.barh(b.index, b[col], left=left, color=sh, label=lab, height=0.62)
        left = left + b[col].to_numpy()
    ax.barh(b.index, b.km_no_plot_within_60m, left=left, color="#b8b8b8",
            label="no plot within 60 m", height=0.62)
    ax.set_xlabel("km of corridor")
    ax.set_xlim(0, 1560)
    ax.set_title("Test 1 — is the ground built?\nbuilt fraction of the plots each "
                 "corridor fronts (W3 BUILT_FIN)", fontsize=11)
    ax.legend(fontsize=8.5, loc="upper right")
    ax.grid(axis="x", alpha=0.3)

    ax = axes[1]
    order = ["open_ground", "auto_block", "auto_link", "draft", "auto_road"]
    c = c.set_index("set").reindex(order)
    colr = ["#999999", SRC_COL["auto_block"], SRC_COL["auto_link"],
            SRC_COL["draft"], SRC_COL["auto_road"]]
    ax.barh(c.index, c.pct_above_threshold, color=colr, height=0.6)
    for i, (n, r) in enumerate(c.iterrows()):
        ax.text(r.pct_above_threshold + 1, i, f"{r.pct_above_threshold:.0f} %  "
                f"(median contrast {r.median_abs:.1f})", va="center", fontsize=9)
    ax.axvline(25, color="#b5290f", ls="--", lw=1.2)
    ax.text(25.6, -0.45, "open-ground baseline", color="#b5290f", fontsize=9)
    ax.set_xlim(0, 88)
    ax.set_xlabel("% of samples brighter or darker than the ground 12 m either side")
    ax.set_title("Test 2 — is there a street there?\nimagery contrast at the corridor "
                 "against its own surroundings", fontsize=11)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "R_F3_ground_truth.png"), facecolor="white")
    plt.close(fig)


def fig4(bnd):
    """The pipe that collects nothing."""
    sp = gpd.read_file(os.path.join(C.OUT_SHP, "W10_pipe_surplus.shp"))
    lifts = gpd.read_file(os.path.join(C.OUT_SHP, "W10_lift_sized.shp"))
    fig, ax = plt.subplots(figsize=(13.5, 10), dpi=115)
    frame(ax, bnd)
    sp[sp.SURPLUS == 0].plot(ax=ax, color="#cfcfcf", lw=0.3, zorder=2)
    a = sp[(sp.SURPLUS == 1) & (sp.REMOVABLE == 0)]
    b = sp[sp.REMOVABLE == 1]
    a.plot(ax=ax, color="#e8a33d", lw=0.9, zorder=3)
    b.plot(ax=ax, color="#c1272d", lw=1.1, zorder=4)
    big = lifts[lifts.LIFT_M >= 20]
    big.plot(ax=ax, color="black", marker="^", markersize=34, zorder=6)
    ax.legend(handles=[
        Line2D([], [], color="#cfcfcf", lw=2.5,
               label=f"pipe fronting plots  {sp.loc[sp.SURPLUS==0,'LEN_M'].sum()/1000:,.0f} km"),
        Line2D([], [], color="#e8a33d", lw=2.5,
               label=f"collects nothing, but conveys flow  {a.LEN_M.sum()/1000:,.0f} km"),
        Line2D([], [], color="#c1272d", lw=2.5,
               label=f"collects nothing AND conveys nothing  {b.LEN_M.sum()/1000:,.0f} km"),
        Line2D([], [], color="black", marker="^", lw=0, markersize=8,
               label=f"depth breach needing over 20 m of lift  ({len(big)})")],
        loc="upper left", fontsize=10, framealpha=0.9)
    scalebar(ax, bnd)
    ax.set_title("W10 — pipe with no load-bearing plot within 60 m of it\n"
                 f"195.0 km of 1,882.9 km (10.4 %); 117.3 km of that carries under "
                 f"1 m³/d as well", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "R_F4_surplus_pipe.png"), facecolor="white")
    plt.close(fig)


def fig5():
    """Cost-effectiveness: the curve and the threshold sweep."""
    st = pd.read_csv(os.path.join(RUN, "r6_tranches.csv"))
    sw = pd.read_csv(os.path.join(RUN, "r5_marginal_sweep.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2), dpi=118)

    ax = axes[0]
    s = st[st.props > 0]
    bands = [(0, 20, "under 20"), (20, 40, "20 - 40"), (40, 80, "40 - 80"),
             (80, 150, "80 - 150"), (150, 400, "150 - 400"), (400, 1e9, "over 400")]
    lab, pp, kk, nn = [], [], [], []
    for lo, hi, name in bands:
        m = (s.m_per_property >= lo) & (s.m_per_property < hi)
        lab.append(name)
        pp.append(100 * s.loc[m, "props"].sum() / s.props.sum())
        kk.append(100 * s.loc[m, "pipe_km_exclusive"].sum() /
                  s.pipe_km_exclusive.sum())
        nn.append(int(m.sum()))
    y = np.arange(len(lab))
    ax.barh(y + 0.19, pp, height=0.36, color="#1f5fa9", label="% of all properties")
    ax.barh(y - 0.19, kk, height=0.36, color="#c1272d",
            label="% of all exclusive pipe")
    for i, (lo, hi, _) in enumerate(bands):
        m = (s.m_per_property >= lo) & (s.m_per_property < hi)
        ax.text(260, y[i],
                f"{nn[i]:>3d} settlements · {s.loc[m, 'props'].sum():>7,.0f} properties"
                f" · {s.loc[m, 'pipe_km_exclusive'].sum():>6,.1f} km",
                va="center", fontsize=8.5, family="monospace")
    ax.set_yticks(y)
    ax.set_yticklabels(lab)
    ax.set_ylabel("metres of exclusive pipe per property")
    ax.set_xlabel("% of the total (log scale)")
    ax.set_xscale("symlog", linthresh=0.1)
    ax.set_xlim(0, 40000)
    ax.set_xticks([0, 0.1, 1, 10, 100])
    ax.set_xticklabels(["0", "0.1", "1", "10", "100"])
    ax.axhline(0.5, color="black", ls="--", lw=1.2)
    ax.text(0.005, -0.42, "the break — below this line: 106 settlements holding\n"
                          "99.1 % of the properties, at 13.3 m per property",
            fontsize=8.5, va="center")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="x", alpha=0.3)
    ax.set_title("Cost-effectiveness by settlement\n187 settlements, exclusive pipe "
                 "only (log scale)", fontsize=11)

    ax = axes[1]
    ax.plot(sw.threshold_m3d, sw.pct_of_pipe, "o-", color="#c1272d",
            label="% of the pipe dropped")
    ax.plot(sw.threshold_m3d, sw.pct_of_flow, "s-", color="#1f5fa9",
            label="% of the flow lost")
    ax.plot(sw.threshold_m3d, sw.pct_of_lift, "^-", color="#2e9b4f",
            label="% of the pumping lift removed")
    ax.set_xscale("log")
    ax.set_xticks(sw.threshold_m3d)
    ax.set_xticklabels([f"{v:g}" for v in sw.threshold_m3d])
    ax.set_xlabel("drop branches carrying less than … m³/d")
    ax.set_ylabel("%")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9)
    ax.set_title("Pruning the marginal network\nwhat comes off against what is lost",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "R_F5_cost_effectiveness.png"), facecolor="white")
    plt.close(fig)


def fig6(bnd):
    """Settlements by tranche."""
    st = pd.read_csv(os.path.join(RUN, "r6_tranches.csv"))
    pl = gpd.read_file(os.path.join(C.OUT_SHP, "W10_plot_loads.gpkg"),
                       layer="plot_loads")
    sp = gpd.read_file(os.path.join(C.OUT_SHP, "W10_pipe_surplus.shp"))
    fig, ax = plt.subplots(figsize=(13.5, 10), dpi=115)
    frame(ax, bnd)
    sp.plot(ax=ax, color="#dedede", lw=0.25, zorder=2)
    cols = {"1 - sewer (core)": "#2e7d3a", "1 - sewer": "#7fc08a",
            "2 - economics decide": "#e8a33d", "3 - do not sewer": "#c1272d",
            "0 - no load to collect": "#9a9a9a"}
    sizes = {"1 - sewer (core)": 12, "1 - sewer": 26,
             "2 - economics decide": 70, "3 - do not sewer": 90,
             "0 - no load to collect": 18}
    g = st.copy()
    for t in ["1 - sewer (core)", "1 - sewer", "0 - no load to collect",
              "2 - economics decide", "3 - do not sewer"]:
        sub = g[g.TRANCHE == t]
        if not len(sub):
            continue
        ax.scatter(sub.km_to_core * 0 + _cx(sub, pl), _cy(sub, pl),
                   s=sizes[t], c=cols[t], edgecolors="black", linewidths=0.3,
                   zorder=5, label=f"{t}  ({len(sub)} settlements, "
                                   f"{sub.pipe_km_exclusive.sum():,.0f} km, "
                                   f"{sub.props.sum():,.0f} properties)")
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.92)
    scalebar(ax, bnd)
    ax.set_title("Settlements by tranche — should it be connected?\n"
                 "187 settlements, plots within 60 m of each other", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "R_F6_tranches.png"), facecolor="white")
    plt.close(fig)


_cent = {}


def _centroids(pl):
    if not _cent:
        from shapely.ops import unary_union
        blob = gpd.GeoDataFrame(geometry=[unary_union(pl.geometry.buffer(60.0))],
                                crs=C.EPSG).explode(index_parts=False).reset_index(drop=True)
        blob["SID"] = blob.index
        j = gpd.sjoin(pl, blob[["SID", "geometry"]], how="left", predicate="intersects")
        j = j[~j.index.duplicated(keep="first")]
        pl = pl.copy()
        pl["SID"] = j["SID"].values
        c = pl.dissolve("SID").centroid
        _cent["x"] = c.x
        _cent["y"] = c.y
    return _cent


def _cx(sub, pl):
    return _centroids(pl)["x"].reindex(sub.SID).to_numpy()


def _cy(sub, pl):
    return _centroids(pl)["y"].reindex(sub.SID).to_numpy()


def main():
    bnd = gpd.read_file(C.BOUNDARY).to_crs(C.EPSG)
    cq = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridor_quality.shp"))
    print("F1 corridors by source");        fig1(cq, bnd)
    print("F2 corridor defects");           fig2(cq, bnd)
    print("F3 ground truth charts");        fig3()
    print("F4 surplus pipe");               fig4(bnd)
    print("F5 cost-effectiveness");         fig5()
    print("F6 tranches");                   fig6(bnd)
    for f in sorted(os.listdir(IMG)):
        if f.startswith("R_F"):
            print("  ", f, os.path.getsize(os.path.join(IMG, f)) // 1024, "kB")


if __name__ == "__main__":
    main()
