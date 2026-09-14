"""Charts for the Design Basis Report. Every chart reads facts_basis / facts_w14, so the
picture and the words cannot drift apart. Re-runnable; writes PNG into report_basis/img/.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "report"))
sys.path.insert(0, HERE)
import facts_basis as B  # noqa: E402
import facts_w14 as F  # noqa: E402
from charts import _style, _thousands, BLUE, MID, PALE, GREY, RED, GREEN, AMBER, DPI  # noqa: E402

IMG = os.path.join(HERE, "img")


def _save(fig, name):
    os.makedirs(IMG, exist_ok=True)
    path = os.path.join(IMG, name + ".png")
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   " + name)
    return path


# ------------------------------------------------------- the self-cleansing curve
def _curve_axes(ax, qmin=0.05, qmax=40.0):
    import numpy as np
    q = np.logspace(np.log10(qmin), np.log10(qmax), 400)
    s = [B.mara_smin_pct(x) for x in q]
    ax.plot(q, s, color=MID, linewidth=2.2, label=f"minimum gradient by tractive force, τ = {B.TAU_PA:g} Pa (G203 p27)")
    ax.set_xscale("log")
    ax.set_xlim(qmin, qmax); ax.set_ylim(0, 2.0)
    ticks = [0.05, 0.1, 0.2, 0.5, 1, 1.5, 2, 3, 5, 10, 20, 40]
    ax.set_xticks(ticks); ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.set_xlabel("peak flow in the pipe, l/s (log scale)", fontsize=9, color=GREY)
    ax.set_ylabel("minimum gradient, %", fontsize=9, color=GREY)
    _style(ax, xgrid=True, ygrid=True)
    return q, s


def mara_curve_full():
    """The tractive curve against every Table 11 minimum and the 1.5 l/s floor: the full version."""
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    _curve_axes(ax)
    pts = B.table11_points()
    s_floor = B.mara_smin_pct(B.Q_FLOOR_LS)
    # Table 11: a horizontal line per size to the point where it meets the curve
    for dn, q in sorted(pts.items()):
        if q > 40:
            continue
        s = B.TABLE11[dn] / 10.0
        ax.plot([0.05, q], [s, s], color=GREEN, linewidth=0.8, linestyle="--", alpha=0.8)
        ax.plot([q], [s], marker="s", color=GREEN, markersize=4.5, zorder=4)
        off = {500: (6, 6), 600: (6, -13)}.get(dn, (6, 4))
        ax.annotate(f"DN{dn}  {s:.3g} %  ↔  {q:.1f} l/s", (q, s), xytext=off, textcoords="offset points",
                    fontsize=7.6, color=GREEN)
    # the floor
    ax.plot([B.Q_FLOOR_LS], [s_floor], marker="D", color=RED, markersize=7, zorder=5)
    ax.annotate(f"design floor {B.Q_FLOOR_LS:g} l/s → {s_floor:.2f} %\n"
                f"a pipe carrying less is checked as if it carried {B.Q_FLOOR_LS:g} l/s",
                (B.Q_FLOOR_LS, s_floor), xytext=(-250, 70), textcoords="offset points", fontsize=8, color=RED,
                fontweight="bold", arrowprops=dict(arrowstyle="-", color=RED, linewidth=0.8))
    # three readings on the steep part
    for q in (0.1, 0.3, 0.6):
        s = B.mara_smin_pct(q)
        ax.plot([q], [s], marker="o", color=BLUE, markersize=4.5, zorder=4)
        ax.annotate(f"{q:g} l/s → {s:.2g} %", (q, s), xytext=(7, 3), textcoords="offset points", fontsize=7.8, color=BLUE)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.set_title("Minimum gradient by tractive force against the Table 11 minima, with the 1.5 l/s design floor",
                 fontsize=9.5, color=BLUE, loc="left")
    return _save(fig, "K01_mara_full")


def mara_curve_minimal():
    """The same curve with only what the reader must see: the DN200 line, the floor, one reading."""
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    _curve_axes(ax, qmin=0.1, qmax=20.0)
    ax.set_ylim(0, 1.6)
    s200 = B.TABLE11[200] / 10.0; q200 = B.table11_points()[200]
    s_floor = B.mara_smin_pct(B.Q_FLOOR_LS)
    ax.axhline(s200, color=GREEN, linewidth=1.0, linestyle="--")
    ax.text(0.11, s200 + 0.03, f"DN200 laid at Table 11: {s200:.1f} %", fontsize=8, color=GREEN)
    ax.plot([q200], [s200], marker="s", color=GREEN, markersize=5, zorder=4)
    ax.annotate(f"{q200:.2f} l/s: the curve meets Table 11", (q200, s200), xytext=(8, 8), textcoords="offset points",
                fontsize=8, color=GREEN)
    ax.plot([B.Q_FLOOR_LS], [s_floor], marker="D", color=RED, markersize=7, zorder=5)
    ax.annotate(f"design floor {B.Q_FLOOR_LS:g} l/s → {s_floor:.2f} %, below the Table 11 line",
                (B.Q_FLOOR_LS, s_floor), xytext=(10, -26), textcoords="offset points", fontsize=8.2, color=RED,
                fontweight="bold", arrowprops=dict(arrowstyle="-", color=RED, linewidth=0.8))
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    return _save(fig, "K02_mara_minimal")


# ------------------------------------------------------- with and without the overflow
def overflow_totals():
    """Study-area people by year, with the overflow and on each settlement's own growth."""
    rows = B.series_totals()
    yrs = [r[0] for r in rows]; own = [r[1] for r in rows]; withp = [r[2] for r in rows]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.plot(yrs, withp, color=BLUE, linewidth=2.2, label="with the overflow: a full settlement's growth moves to its neighbours")
    ax.plot(yrs, own, color=AMBER, linewidth=2.2, linestyle="--", label="without: each settlement on its own growth, capped when full")
    ult = yrs[-1]
    ax.annotate(f"{withp[-1]:,.0f}", (ult, withp[-1]), xytext=(-46, 6), textcoords="offset points", fontsize=8.5, color=BLUE, fontweight="bold")
    ax.annotate(f"{own[-1]:,.0f}", (ult, own[-1]), xytext=(-46, -14), textcoords="offset points", fontsize=8.5, color=AMBER, fontweight="bold")
    ax.annotate("", (ult, own[-1]), (ult, withp[-1]), arrowprops=dict(arrowstyle="<->", color=GREY, linewidth=0.9))
    ax.text(ult - 0.6, (withp[-1] + own[-1]) / 2, f"{withp[-1] - own[-1]:,.0f} people\nwith nowhere to go",
            ha="right", va="center", fontsize=8, color=GREY)
    ax.set_xlim(yrs[0], ult + 1)
    ax.set_ylim(0, max(withp) * 1.15)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylabel("People in the study area", fontsize=8.5, color=GREY)
    _style(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=7.8)
    return _save(fig, "K03_overflow_totals")


def overflow_settlements():
    """People at saturation per settlement, with and without the overflow, the ten most affected."""
    no = B.no_overflow(); ult = B.years()[-1]
    rows = sorted(no["rows"], key=lambda r: -(r[ult]["pop_with"] - r[ult]["pop_own"]))[:10]
    names = [r["name"] for r in rows]
    withp = [r[ult]["pop_with"] for r in rows]; own = [r[ult]["pop_own"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    x = range(len(names))
    ax.bar([i - 0.2 for i in x], withp, width=0.4, color=BLUE, label=f"with the overflow, {ult}")
    ax.bar([i + 0.2 for i in x], own, width=0.4, color=AMBER, label=f"own growth only, {ult}")
    for i, (a, b) in enumerate(zip(withp, own)):
        ax.text(i - 0.2, a + max(withp) * 0.01, f"{a:,.0f}", ha="center", va="bottom", fontsize=6.6, color=BLUE, rotation=90)
        ax.text(i + 0.2, b + max(withp) * 0.01, f"{b:,.0f}", ha="center", va="bottom", fontsize=6.6, color=AMBER, rotation=90)
    ax.set_xticks(list(x)); ax.set_xticklabels(names)
    ax.set_ylim(0, max(withp) * 1.3)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylabel("People at saturation", fontsize=8.5, color=GREY)
    _style(ax)
    plt.setp(ax.get_xticklabels(), rotation=40, ha="right", fontsize=7.6)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    return _save(fig, "K04_overflow_settlements")


# ------------------------------------------------------- the plant flows by year
def plant_flows():
    """Average and peak-hour flow at one works for the whole area, by year, with the margin."""
    t = F.totals(); yrs = [y for y in t["years"] if y <= t["ultimate"]]
    aaf = [t["q"][y] * (1 + B.MARGIN) for y in yrs]
    phf = [B.merrimack(t["q"][y]) * (1 + B.MARGIN) for y in yrs]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.plot(yrs, phf, color=RED, linewidth=2.0, label=f"peak hourly flow, Merrimack, with the {B.MARGIN * 100:.0f} % margin")
    ax.plot(yrs, aaf, color=BLUE, linewidth=2.2, label=f"average flow with the {B.MARGIN * 100:.0f} % margin")
    for y in B.years()[1:]:
        i = yrs.index(y)
        ax.plot([y, y], [0, phf[i]], color="#cccccc", linewidth=0.7, zorder=1)
        ax.text(y, phf[i] + max(phf) * 0.02, f"{y}\n{aaf[i]:,.0f}\n{phf[i]:,.0f}", ha="center", va="bottom", fontsize=7.4, color=GREY)
    ax.set_xlim(yrs[0], yrs[-1] + 1); ax.set_ylim(0, max(phf) * 1.3)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylabel("m³/d, before infiltration and tankers", fontsize=8.5, color=GREY)
    _style(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    return _save(fig, "K05_plant_flows")


ALL = (mara_curve_full, mara_curve_minimal, overflow_totals, overflow_settlements, plant_flows)

if __name__ == "__main__":
    print("charts, basis report:")
    for fn in ALL:
        fn()
