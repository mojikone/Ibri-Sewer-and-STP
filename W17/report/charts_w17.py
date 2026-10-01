"""Charts of the sewer network options (Section 6.2 of Revision 4). Every value is read from
facts_w17, the module the text reads, so the chart and the words cannot disagree. The plant
colours are those of the maps and the transfer diagrams. Re-runnable; writes PNG into img/.

    python charts_w17.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from charts import _style, _save, _thousands, BLUE, MID, PALE, GREY, RED  # noqa: E402
import facts_w17 as F  # noqa: E402

ZONE = {"O1": "#2E75B6", "O4": "#C0504D", "O9": "#70AD47", "O3": "#7030A0", "O16": "#ED7D31", "O22": "#00A6D6"}
CM = 1 / 2.54


def w01_plant_split():
    """The 2070 average flow (with infiltration) arriving at each plant, by option.
    Source: facts_w17.plants (results/S#/S#_summary.json)."""
    opts = F.available()
    fig, ax = plt.subplots(figsize=(17 * CM, (2.2 + 1.05 * len(opts)) * CM))
    _style(ax, xgrid=True, ygrid=False)
    small = {}
    for i, o in enumerate(opts):
        left = 0.0
        pl = F.plants(o)
        total = sum(v["avg"]["2070"] for v in pl.values())
        for z, v in pl.items():
            q = v["avg"]["2070"]
            ax.barh(i, q, left=left, color=ZONE[z], height=0.62, edgecolor="white", linewidth=0.8)
            if q >= 0.09 * total:
                ax.text(left + q / 2, i, f"{z}\n{q:,.0f}", ha="center", va="center", fontsize=7, color="white",
                        fontweight="bold", linespacing=1.0)
            else:
                small.setdefault(o, []).append(f"{z} {q:,.0f}")
            left += q
    xmax = max(sum(v["avg"]["2070"] for v in F.plants(o).values()) for o in opts)
    for i, o in enumerate(opts):            # the small plants in one column clear of every bar
        if o in small:
            ax.text(xmax * 1.02, i, " · ".join(small[o]), va="center", fontsize=7, color=GREY)
    ax.set_yticks(range(len(opts)))
    ax.set_yticklabels([f"{o}" for o in opts], fontsize=8.5, color=BLUE, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlim(0, xmax * 1.36)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_xlabel("Average flow arriving at the plant in 2070, m³/d (small plants named at the right)", fontsize=8, color=GREY)
    return _save(fig, "W01_plant_split")


def w02_plant_years():
    """The average flow arriving at each plant, 2030 to 2070, one panel per option.
    Source: facts_w17.plants."""
    opts = F.available()
    cols = 4; rows = (len(opts) + 1 + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(17 * CM, 5.4 * rows * CM), sharey=True)
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]
    years = [int(y) for y in F.YEARS]
    seen = {}
    for ax, o in zip(axes, opts):
        _style(ax)
        pl = F.plants(o)
        base = [0.0] * len(years)
        for z, v in pl.items():
            vals = [v["avg"][str(y)] for y in years]
            top = [b + q for b, q in zip(base, vals)]
            ax.fill_between(years, base, top, color=ZONE[z], alpha=0.9, linewidth=0)
            base = top
            seen[z] = True
        ax.set_title(f"{o}: {len(pl)} plant{'s' if len(pl) > 1 else ''}", fontsize=8, color=BLUE, fontweight="bold", pad=3)
        ax.set_xticks([2030, 2050, 2070]); ax.set_xlim(2030, 2070)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1000:,.0f}k"))
    for ax in axes[len(opts):]:
        ax.axis("off")
    if len(axes) > len(opts):
        axes[len(opts)].legend(handles=[Patch(color=ZONE[z], label=f"plant at {F.name(z)}") for z in ZONE if z in seen],
                               loc="center", fontsize=7.5, frameon=False, title="Average flow, m³/d", title_fontsize=8)
    fig.tight_layout(w_pad=0.6, h_pad=0.8)
    return _save(fig, "W02_plant_years")


def w03_pumping():
    """Pumping stations: installed duty and the energy they use, 2030 and 2070, by option.
    Source: facts_w17.option_row (results/S#/S#_summary.json)."""
    opts = F.available()
    rows = [F.option_row(o) for o in opts]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17 * CM, 6.6 * CM))
    _style(a1); _style(a2)
    x = range(len(opts))
    kw = [r["kw"] for r in rows]
    a1.bar(x, kw, color=MID, width=0.6)
    top = max(kw)
    for i, r in enumerate(rows):            # value and station count in two fixed rows above the tallest bar
        a1.text(i, top * 1.08, f"{r['kw']:,.0f}", ha="center", fontsize=7, color=BLUE)
        a1.text(i, top * 1.19, f"{r['n_ps']} PS", ha="center", fontsize=7, color=GREY)
    a1.set_ylim(0, top * 1.3)
    a1.set_xticks(list(x)); a1.set_xticklabels(opts, fontsize=8)
    a1.set_ylabel("Installed duty, kW", fontsize=8, color=GREY)
    w = 0.36
    e30 = [r["mwh_2030"] for r in rows]; e70 = [r["mwh_2070"] for r in rows]
    a2.bar([i - w / 2 for i in x], e30, width=w, color=PALE, label="2030")
    a2.bar([i + w / 2 for i in x], e70, width=w, color=BLUE, label="2070")
    top2 = max(e70)
    for i in x:
        a2.text(i, top2 * 1.08, f"{e70[i]:,.0f}", ha="center", fontsize=7, color=BLUE)
    a2.set_ylim(0, top2 * 1.22)
    a2.set_xticks(list(x)); a2.set_xticklabels(opts, fontsize=8)
    a2.set_ylabel("Energy, MWh a year", fontsize=8, color=GREY)
    a2.yaxis.set_major_formatter(FuncFormatter(_thousands))
    a2.legend(fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    fig.tight_layout(w_pad=2.0)
    return _save(fig, "W03_pumping")


def w04_depth():
    """Manholes deeper than 9 m, split at the 12 m limit, by option.
    Source: facts_w17.summary manholes_by_band."""
    opts = F.available()
    fig, ax = plt.subplots(figsize=(17 * CM, 6.0 * CM))
    _style(ax)
    a = [F.summary(o)["manholes_by_band"].get("9-12 m", 0) for o in opts]
    b = [F.summary(o)["manholes_by_band"].get(">12 m", 0) for o in opts]
    x = range(len(opts))
    ax.bar(x, a, color=BLUE, width=0.6, label="9 to 12 m")
    ax.bar(x, b, bottom=a, color=RED, width=0.6, label="deeper than 12 m")
    top = max(p + q for p, q in zip(a, b))
    for i, o in enumerate(opts):            # the >12 m count and the deepest in fixed rows above the bars
        ax.text(i, top * 1.07, f"{b[i]} > 12 m", ha="center", fontsize=7, color=RED)
        ax.text(i, top * 1.17, f"deepest {F.summary(o)['deepest']['depth']:.1f} m", ha="center", fontsize=7, color=GREY)
    ax.set_ylim(0, top * 1.28)
    ax.set_xticks(list(x)); ax.set_xticklabels(opts, fontsize=8)
    ax.set_ylabel("Manholes", fontsize=8, color=GREY)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.12), ncol=2)
    return _save(fig, "W04_depth")


if __name__ == "__main__":
    print("options:", F.available())
    w01_plant_split(); w02_plant_years(); w03_pumping(); w04_depth()
