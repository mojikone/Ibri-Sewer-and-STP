"""Charts of the study-area section (1.2) of the Concept Design Report, Revision 3.
Every value comes from facts_area, the module the text reads. Re-runnable; writes PNG into img/.

    python charts_area.py
"""
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from charts import _style, _save, BLUE, MID, PALE, GREY, RED, GREEN, AMBER  # noqa: E402
import facts_area as A  # noqa: E402


# ---------------------------------------------------------------- S01 ground level against distance
def s01_ground():
    """Ground level of the built plots of each settlement, the settlements in order of their distance from the
    existing STP. Source: A.ground() - the 0.5 m terrain at the built plots; bar = 10th to 90th percentile;
    dot area = people 2024. One row a settlement: ten of them lie within 8 km and 25 m of one another, and
    on a distance axis their names cannot be kept apart."""
    g = A.ground(); rows = g["settlements"]; z0 = g["stp_ground"]; n = len(rows)
    fig, ax = plt.subplots(figsize=(7.6, 5.2))      # short enough to share a page with the text of 1.2.1 to 1.2.4
    y = np.arange(n)[::-1]
    for yi in y[::2]:
        ax.axhspan(yi - 0.5, yi + 0.5, color="#F5F7FA", zorder=0)
    ax.axvline(z0, color=RED, lw=1.0, ls=(0, (5, 3)), zorder=1)
    ax.text(z0 + 2.5, n - 0.35, f"ground at the existing STP, {z0:.0f} m", color=RED, fontsize=7.6, ha="left", va="bottom")
    for yi, r in zip(y, rows):
        low = r["z_med"] < z0; c = RED if low else BLUE
        ax.plot([r["z_p10"], r["z_p90"]], [yi, yi], color=c, lw=2.2, alpha=0.45, zorder=2, solid_capstyle="round")
        ax.scatter([r["z_med"]], [yi], s=16 + 300 * math.sqrt(r["pop_2024"] / 67106.0), color=c, alpha=0.9, edgecolor="white", linewidth=0.6, zorder=3)
        ax.text(r["z_p90"] + 4.5 + 3.5 * math.sqrt(r["pop_2024"] / 67106.0), yi, f"{r['z_med']:.0f} m", fontsize=6.8, color=c, va="center", ha="left")
        ax.text(551, yi, f"{r['dist_km']:.1f} km", fontsize=7.2, color=GREY, va="center", ha="right")
    ax.text(551, n - 0.35, "from the STP", fontsize=7.2, color=GREY, va="bottom", ha="right")
    ax.set_yticks(y); ax.set_yticklabels([r["name"] for r in rows], fontsize=7.8)
    for lab, r in zip(ax.get_yticklabels(), rows):
        if r["z_med"] < z0:
            lab.set_color(RED)
    ax.set_ylim(-0.7, n + 0.6); ax.set_xlim(300, 553); ax.set_xticks(range(300, 501, 25))
    ax.set_xlabel("ground level of the built plots, m", fontsize=8.2, color=GREY)
    _style(ax); ax.grid(axis="x", color="#E3E3E3", lw=0.6); ax.grid(axis="y", visible=False); ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    handles = [Line2D([], [], marker="o", ls="", color=BLUE, ms=6, label="median, above the STP"),
               Line2D([], [], marker="o", ls="", color=RED, ms=6, label="median, below the STP"),
               Line2D([], [], color=BLUE, lw=2.2, alpha=0.45, label="10th to 90th percentile of the built plots"),
               Line2D([], [], marker="o", ls="", color="#9A9A9A", ms=9, label="dot area: people in 2024")]
    ax.legend(handles=handles, frameon=False, fontsize=7.1, loc="upper center", bbox_to_anchor=(0.42, -0.075), ncol=4, columnspacing=1.0, handletextpad=0.3)
    fig.tight_layout()
    return _save(fig, "S01_ground_levels")


# ---------------------------------------------------------------- S02 temperature and rainfall
def s02_climate():
    """Monthly temperature and rainfall at the existing STP. Source: A.climate() - NASA POWER (MERRA-2), 2001-2020."""
    c = A.climate(); m = c["monthly"]; x = np.arange(12)
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    ax2 = ax.twinx()
    bars = ax2.bar(x, [r["rain"] for r in m], width=0.55, color=PALE, zorder=1, label="rainfall, mm a month (right axis)")
    for b, r in zip(bars, m):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.6, f"{r['rain']:.0f}", ha="center", va="bottom", fontsize=6.8, color=MID)
    ax2.set_ylim(0, 60); ax2.set_ylabel("rainfall, mm", fontsize=8, color=GREY)
    ax2.tick_params(axis="y", labelsize=7.5, colors=GREY, length=0)
    for sp in ("top", "left", "right", "bottom"):
        ax2.spines[sp].set_visible(False)
    series = (("t_max", RED, "mean daily maximum"), ("t_mean", GREY, "daily mean"), ("t_min", BLUE, "mean daily minimum"))
    for key, col, lab in series:
        v = [r[key] for r in m]
        ax.plot(x, v, color=col, lw=1.6, marker="o", ms=3.2, label=lab, zorder=3)
        if key != "t_mean":
            for xi, vi in zip(x, v):
                ax.text(xi, vi + 1.6, f"{vi:.0f}", ha="center", fontsize=6.8, color=col)   # above both lines: the rain labels sit below
    ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
    ax.set_xticks(x); ax.set_xticklabels(A.MONTHS, fontsize=8); ax.set_ylim(0, 52)
    ax.set_ylabel("air temperature at 2 m, °C", fontsize=8, color=GREY)
    _style(ax)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7.4, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4)
    fig.tight_layout()
    return _save(fig, "S02_climate")


# ---------------------------------------------------------------- S03 wind roses
_SPEED_COLOURS = ["#C6D6EA", "#8FADD1", "#4F81BD", "#1F497D", "#C0504D"]


def _rose(ax, rose, classes, sectors, title, rmax):
    n = len(sectors); theta = np.deg2rad(np.arange(n) * 360.0 / n); width = 2 * np.pi / n * 0.86
    bottom = np.zeros(n)
    for c, col in zip(classes, _SPEED_COLOURS):
        v = np.array([100.0 * rose["share"][s][c] for s in sectors])
        ax.bar(theta, v, width=width, bottom=bottom, color=col, edgecolor="white", linewidth=0.3, zorder=3)
        bottom += v
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.set_xticks(np.deg2rad(np.arange(0, 360, 45))); ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=7.6, color="#404040")
    ticks = list(range(4, int(rmax) + 1, 4))
    ax.set_ylim(0, rmax); ax.set_yticks(ticks); ax.set_yticklabels([f"{t} %" for t in ticks], fontsize=6.2, color="#7A7A7A")
    ax.set_rlabel_position(78); ax.grid(color="#D9D9D9", lw=0.5); ax.spines["polar"].set_color("#BFBFBF")
    ax.set_title(f"{title}\nmean {rose['mean_speed']:.1f} m/s, below 1 m/s {100 * rose['calm_share']:.0f} % of hours", fontsize=8, color="#404040", pad=10)


def s03_windrose():
    """Wind roses at 10 m at the existing STP: the direction the wind blows FROM, share of hours by speed class.
    Source: A.wind() - NASA POWER (MERRA-2), hourly, 2015-2024."""
    w = A.wind(); cl = w["classes"]; sec = w["sectors"]
    panels = (("all", "All hours"), ("night", "Night, 20:00 to 06:00"), ("summer", "Summer, May to September"), ("winter", "Winter, November to March"))
    rmax = 4 * math.ceil(max(100 * max(w[k]["sector_total"].values()) for k, _ in panels) / 4.0)
    fig, axes = plt.subplots(2, 2, figsize=(7.6, 7.9), subplot_kw={"projection": "polar"})
    for ax, (k, title) in zip(axes.ravel(), panels):
        _rose(ax, w[k], cl, sec, title, rmax)
    names = {"0-2": "under 2 m/s", "2-4": "2 to 4", "4-6": "4 to 6", "6-8": "6 to 8", ">8": "over 8 m/s"}
    fig.legend(handles=[Patch(color=c, label=names[k]) for k, c in zip(cl, _SPEED_COLOURS)], frameon=False, fontsize=7.8,
               loc="lower center", ncol=5, title="wind speed at 10 m; a bar points to where the wind comes from", title_fontsize=7.8)
    fig.tight_layout(rect=(0, 0.06, 1, 1), h_pad=2.2)
    return _save(fig, "S03_windrose")


# ---------------------------------------------------------------- S04 road length by class
def s04_roads():
    """Length of road centreline by the class code supplied. Source: A.roads(); colours as on the map."""
    rd = A.roads(); by = rd["by_class_km"]; tot = rd["total_km"]
    codes = ["01", "02", "04", "05"]; cols = {"01": "#d7191c", "02": "#fdae61", "04": "#ffffbf", "05": "#abdda4"}
    fig, ax = plt.subplots(figsize=(7.6, 1.9))
    y = np.arange(len(codes))[::-1]
    bars = ax.barh(y, [by[c] for c in codes], color=[cols[c] for c in codes], edgecolor="#5A5A5A", linewidth=0.5, height=0.6)
    for b, c in zip(bars, codes):
        ax.text(b.get_width() + tot * 0.012, b.get_y() + b.get_height() / 2, f"{by[c]:,.0f} km   {100 * by[c] / tot:.0f} %", va="center", fontsize=7.8, color=GREY)
    ax.set_yticks(y); ax.set_yticklabels([f"Class {c}" for c in codes], fontsize=8)
    ax.set_xlim(0, by["05"] * 1.22); ax.set_xlabel("length of road centreline inside the study area, km", fontsize=8, color=GREY)
    _style(ax)
    fig.tight_layout()
    return _save(fig, "S04_roads")


if __name__ == "__main__":
    for fn in (s01_ground, s02_climate, s03_windrose, s04_roads):
        print(fn())
