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


def _energy_bars(ax, opts, year="2070", label_size=7):
    """Stacked bars: the stations' energy, then the lift at the plant inlets; the total above each bar."""
    st = [F.summary(o)[f"mwh_{year}"] for o in opts]
    il = [F.inlet_lift(o)["mwh"][year] for o in opts]
    x = range(len(opts))
    ax.bar(x, st, color=BLUE, width=0.6, label="pumping stations")
    ax.bar(x, il, bottom=st, color=PALE, width=0.6, label="lift at the plant inlets")
    top = max(a + b for a, b in zip(st, il))
    for i in x:                             # the totals in one fixed row above the tallest bar
        ax.text(i, top * 1.06, f"{st[i] + il[i]:,.0f}", ha="center", fontsize=label_size, color=BLUE)
    ax.set_ylim(0, top * 1.17)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    return x


def _option_ticks(ax, opts, ranked=False):
    """Option names under the bars; with ranked, the recommended options carry their priority."""
    rank = {o: ("1st", "2nd", "3rd")[i] for i, o in enumerate(F.RECOMMENDED)} if ranked else {}
    ax.set_xticks(range(len(opts)))
    ax.set_xticklabels([f"{o}\n{rank[o]}" if o in rank else o for o in opts], fontsize=8)
    for t, o in zip(ax.get_xticklabels(), opts):
        if o in rank:
            t.set_color(BLUE); t.set_fontweight("bold")


def w05_energy_total():
    """Pumping energy in 2070: the network's stations and the lift at each plant's inlet works, by option.
    Source: facts_w17.summary (stations) and facts_w17.inlet_lift (plants)."""
    opts = F.available()
    fig, ax = plt.subplots(figsize=(17 * CM, 6.6 * CM))
    _style(ax)
    _energy_bars(ax, opts)
    _option_ticks(ax, opts)
    ax.set_ylabel("Energy in 2070, MWh a year", fontsize=8, color=GREY)
    ax.legend(fontsize=7.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    return _save(fig, "W05_energy_total")


def w06_glance():
    """The options side by side for the executive summary: the plants and their 2070 flow, the pumping energy with
    the plant inlets, the trunk sewers of 1,000 mm and over, the pumping stations. The recommended options carry
    their priority. Source: facts_w17."""
    opts = F.available()
    fig, axes = plt.subplots(2, 2, figsize=(17 * CM, 12.4 * CM))
    (a1, a2), (a3, a4) = axes
    for ax in (a1, a2, a3, a4):
        _style(ax)
    x = range(len(opts))
    # (a) the plants, stacked in the colours of the maps; the count of plants above each bar
    seen = []
    for i, o in enumerate(opts):
        base = 0.0
        for z, v in F.plants(o).items():
            q = v["avg"]["2070"]
            a1.bar(i, q, bottom=base, color=ZONE[z], width=0.6, edgecolor="white", linewidth=0.6)
            base += q
            if z not in seen:
                seen.append(z)
    tot = max(sum(v["avg"]["2070"] for v in F.plants(o).values()) for o in opts)
    for i, o in enumerate(opts):
        a1.text(i, tot * 1.05, f"{len(F.plants(o))}", ha="center", fontsize=6.5, color=GREY)
    a1.set_ylim(0, tot * 1.16)
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:,.0f}k"))
    a1.set_title("Average flow at the plants in 2070, m³/d;\nnumber of plants", fontsize=8, color=BLUE,
                 fontweight="bold", loc="left")
    a1.legend(handles=[Patch(color=ZONE[z], label=F.name(z)) for z in sorted(seen, key=lambda s: int(s[1:]))],
              fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0), title="Plant at",
              title_fontsize=6.5, handlelength=1.0)
    # (b) energy
    _energy_bars(a2, opts, label_size=6.5)
    a2.set_title("Pumping energy in 2070, MWh a year;\nstations and plant inlets", fontsize=8, color=BLUE,
                 fontweight="bold", loc="left")
    a2.legend(fontsize=6.5, frameon=False, loc="upper right", bbox_to_anchor=(1.0, 0.93))
    # (c) the trunk sewers
    km = [F.km_od_at_least(o) for o in opts]
    a3.bar(x, km, color=MID, width=0.6)
    for i, o in enumerate(opts):
        a3.text(i, max(km) * 1.05, f"{km[i]:.0f} km", ha="center", fontsize=6.5, color=BLUE)
        a3.text(i, max(km) * 1.17, f"{F.largest_od(o)}", ha="center", fontsize=6.0, color=GREY)
    a3.set_ylim(0, max(km) * 1.3)
    a3.set_title("Sewers of 1,000 mm and over, km;\nlargest size, mm", fontsize=8, color=BLUE, fontweight="bold",
                 loc="left")
    # (d) the pumping stations and their rising mains
    nps = [F.summary(o)["pumping_stations"] for o in opts]
    rm = [F.summary(o)["rising_main_m"] / 1000 for o in opts]
    a4.bar(x, nps, color=MID, width=0.6)
    for i in x:
        a4.text(i, max(nps) * 1.05, f"{nps[i]}", ha="center", fontsize=6.5, color=BLUE)
        a4.text(i, max(nps) * 1.17, f"{rm[i]:.0f} km", ha="center", fontsize=6.0, color=GREY)
    a4.set_ylim(0, max(nps) * 1.3)
    a4.set_title("Pumping stations;\nrising mains, km", fontsize=8, color=BLUE, fontweight="bold", loc="left")
    for ax in (a1, a2, a3, a4):
        _option_ticks(ax, opts, ranked=True)
    fig.tight_layout(w_pad=2.2, h_pad=1.6)
    return _save(fig, "W06_glance")


# the hazard classes in the colours of the hazard maps of Section 1.2.7 (qgis_maps_area.HAZARD)
HAZARD_COLOURS = [("none", "#e6e6e6", "not flooded"), ("H1", "#0071ff", "H1"), ("H2", "#47c4ff", "H2"),
                  ("H3", "#00fff9", "H3"), ("H4", "#0eff00", "H4"), ("H5", "#fff200", "H5"), ("H6", "#f41f1f", "H6")]


def w07_flood():
    """The share of the sewer length and of the manholes in each flood hazard class, for the 10, 25, 50 and 100-year
    floods; the share in H4 to H6 in a fixed column at the right. Source: facts_w17.flood (py/flood_exposure.py)."""
    fl = F.flood(); L = fl["pipes"]["length_m"]; M = fl["manholes"]["count"]; periods = list(fl["periods"])
    fig, axes = plt.subplots(1, 2, figsize=(17 * CM, 5.6 * CM), sharey=True)
    for ax, (title, get, total) in zip(axes, (("Length of sewer", lambda p: p["pipe_length_m"], L),
                                              ("Manholes", lambda p: p["manholes"], M))):
        _style(ax, xgrid=True, ygrid=False)
        for i, T in enumerate(periods):
            v = get(fl["periods"][T]); left = 0.0
            for k, colour, _ in HAZARD_COLOURS:
                share = 100 * v[k] / total
                ax.barh(i, share, left=left, color=colour, height=0.62, edgecolor="white", linewidth=0.5)
                left += share
            high = 100 * sum(v[k] for k in ("H4", "H5", "H6")) / total
            ax.text(103, i, f"{high:.1f} %", va="center", fontsize=7.5, color=BLUE, fontweight="bold")
        ax.set_xlim(0, 100); ax.set_title(title, fontsize=8.5, color=GREY)
        ax.text(103, -0.75, "H4–H6", fontsize=7, color=GREY, va="center")
        ax.set_xlabel("per cent", fontsize=7.5, color=GREY)
    axes[0].set_yticks(range(len(periods)))
    axes[0].set_yticklabels([f"{T}-year" for T in periods], fontsize=8)
    axes[0].invert_yaxis()
    fig.legend(handles=[Patch(facecolor=c, edgecolor="#b8b8b8", linewidth=0.4, label=lab) for _, c, lab in HAZARD_COLOURS],
               loc="lower center", ncol=7, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout(w_pad=4.0, rect=(0, 0.06, 1, 1))
    return _save(fig, "W07_flood")


if __name__ == "__main__":
    print("options:", F.available())
    w01_plant_split(); w02_plant_years(); w03_pumping(); w04_depth(); w05_energy_total(); w06_glance(); w07_flood()
