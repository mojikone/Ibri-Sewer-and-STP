"""Charts for Revision 2: population, land use, saturation and flows.

Every chart reads the same facts module the text reads (facts_w14), so the
picture and the words cannot drift apart. Re-runnable; writes PNG into img/.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

import facts_w14 as F
from charts import (_style, _save, _thousands, BLUE, MID, PALE, GREY, LIGHT,
                    RED, GREEN, AMBER, IMG)

BROWN = "#8d6e63"
PURPLE = "#6c4b8a"
ORANGE = "#d9853b"


# ---------------------------------------------------------------- C01 (R2)
def c01_accounts():
    """Electricity meters by the category adopted, after the large consumers
    were placed. Source: facts_w14.meter_counts (ELE_meters_on_plots.shp)."""
    mc = F.meter_counts()
    g = mc["gud"]
    data = [
        ("Domestic", g.get("domestic", 0), BLUE),
        ("Non-domestic", g.get("non_domestic", 0), MID),
        ("Governmental", g.get("government", 0), AMBER),
        ("Agricultural", g.get("agricultural", 0), GREEN),
        ("Special\n(industrial)", g.get("special", 0), PURPLE),
    ]
    names = [d[0] for d in data]; vals = [d[1] for d in data]; cols = [d[2] for d in data]
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    bars = ax.bar(names, vals, color=cols, width=0.62, edgecolor="white", linewidth=0.8)
    total = sum(vals)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + total * 0.012, f"{v:,}\n{v / total * 100:.1f} %",
                ha="center", va="bottom", fontsize=7.6, color=GREY, linespacing=1.35)
    ax.set_ylim(0, max(vals) * 1.24)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylabel("Meters", fontsize=8.5, color=GREY)
    _style(ax)
    plt.setp(ax.get_xticklabels(), fontsize=7.8)
    return _save(fig, "C01_accounts")


# ---------------------------------------------------------------- C02 (R2)
def c02_occupancy():
    """Occupancy per settlement: the raw value and the value adopted after the
    floor and the cap. Source: facts_w14.settlement_table."""
    rows = F.settlement_table()
    names = [r["name"] for r in rows]; raw = [r["or_raw"] for r in rows]; used = [r["or_used"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    x = range(len(names))
    ax.bar([i - 0.2 for i in x], raw, width=0.4, color=PALE, edgecolor="white", linewidth=0.6, label="raw: 2024 population / properties")
    ax.bar([i + 0.2 for i in x], used, width=0.4, color=MID, edgecolor="white", linewidth=0.6, label="adopted, after the floor of 4.0 and the cap")
    cap = max(used)
    ax.axhline(F.OR_FLOOR, color=RED, linewidth=1.0, linestyle="--", zorder=3)
    ax.axhline(cap, color=RED, linewidth=1.0, linestyle=":", zorder=3)
    ax.text(len(names) - 0.4, F.OR_FLOOR + 0.12, f"floor {F.OR_FLOOR:.1f}", ha="right", va="bottom", fontsize=7.6, color=RED)
    ax.text(len(names) - 0.4, cap + 0.12, f"cap {cap:.2f}", ha="right", va="bottom", fontsize=7.6, color=RED)
    ax.set_xticks(list(x)); ax.set_xticklabels(names)
    ax.set_ylabel("Persons per domestic property", fontsize=8.5, color=GREY)
    ax.set_ylim(0, max(max(raw), cap) * 1.15)
    _style(ax)
    plt.setp(ax.get_xticklabels(), rotation=55, ha="right", fontsize=7.2)
    ax.legend(loc="upper center", ncol=2, frameon=False, fontsize=7.8, bbox_to_anchor=(0.5, 1.13))
    return _save(fig, "C02_occupancy")


# ---------------------------------------------------------------- C04 (R2)
def c04_population():
    """People today by settlement, from the meters and the settlement occupancy."""
    rows = F.settlement_table()
    rows = sorted(rows, key=lambda r: -r["people_today"])
    total = sum(r["people_today"] for r in rows)
    names = [r["name"] for r in rows]; vals = [r["people_today"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    cols = [BLUE] + [MID] * 2 + [PALE] * (len(rows) - 3)
    bars = ax.barh(names, vals, color=cols, height=0.66, edgecolor="white", linewidth=0.7)
    for i, (b, v) in enumerate(zip(bars, vals)):
        txt = f"{v:,.0f}   ({v / total * 100:.0f} %)" if i < 3 else f"{v:,.0f}"
        ax.text(v + total * 0.005, b.get_y() + b.get_height() / 2, txt, ha="left", va="center",
                fontsize=7.2, color=GREY if i else BLUE, fontweight="bold" if i == 0 else "normal")
    ax.set_xlim(0, max(vals) * 1.22)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_xlabel(f"People, {F.BASE_YEAR}", fontsize=8.5, color=GREY)
    ax.invert_yaxis()
    _style(ax, xgrid=True, ygrid=False)
    plt.setp(ax.get_yticklabels(), fontsize=7.4)
    return _save(fig, "C04_population")


# ---------------------------------------------------------------- C07
def c07_landuse():
    """Use of the built, metered plots, as derived from the meters and the
    satellite. Source: facts_w14.plot_summary."""
    ps = F.plot_summary(); cls = ps["classes"]
    order = [("Residential", BLUE), ("Agricultural", GREEN), ("Commercial", RED), ("Residential-Commercial", ORANGE),
             ("Government", AMBER), ("Industrial", PURPLE)]
    names = [o[0].replace("Residential-Commercial", "Home and shop") for o in order]
    vals = [cls.get(o[0], 0) for o in order]; cols = [o[1] for o in order]
    total = sum(vals)
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    bars = ax.barh(names, vals, color=cols, height=0.6, edgecolor="white", linewidth=0.8)
    for b, v in zip(bars, vals):
        ax.text(v + total * 0.006, b.get_y() + b.get_height() / 2, f"{v:,}   ({v / total * 100:.1f} %)",
                ha="left", va="center", fontsize=7.8, color=GREY)
    ax.set_xlim(0, max(vals) * 1.3)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_xlabel("Built plots with meters", fontsize=8.5, color=GREY)
    ax.invert_yaxis()
    _style(ax, xgrid=True, ygrid=False)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    fb = ps["farms_by"]
    ax.text(0.99, 0.04, f"farms: {fb.get('AGR', 0):,} by a farm meter, {fb.get('GRN', 0):,} by the satellite",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.4, color=GREY)
    return _save(fig, "C07_landuse")


# ---------------------------------------------------------------- C08
def c08_growth():
    """People by year, the largest settlements stacked, to saturation."""
    g = F.growth()["Population by year"]
    years = [int(c) for c in g.columns]
    t = F.totals(); ult = t["ultimate"]
    keep = [y for y in years if y <= ult]
    top = list(g.loc[:, str(F.BASE_YEAR)].sort_values(ascending=False).index[:6]) if str(F.BASE_YEAR) in g.columns else list(g.iloc[:, 0].sort_values(ascending=False).index[:6])
    cols = [BLUE, MID, "#4f86c6", PALE, AMBER, GREEN]
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    bottom = [0.0] * len(keep)
    def col(y): return g[str(y)] if str(y) in g.columns else g[y]
    for s, c in zip(top, cols):
        vals = [float(col(y)[s]) for y in keep]
        ax.fill_between(keep, bottom, [b + v for b, v in zip(bottom, vals)], color=c, linewidth=0, label=F.NAME.get(s, s.title()))
        bottom = [b + v for b, v in zip(bottom, vals)]
    rest = [float(col(y).sum()) - b for y, b in zip(keep, bottom)]
    ax.fill_between(keep, bottom, [b + r for b, r in zip(bottom, rest)], color=LIGHT, linewidth=0, label="the other nineteen")
    for y in (2030, 2055, ult):
        v = float(col(y).sum()); ax.axvline(y, color=GREY, linewidth=0.6, linestyle=":")
        ax.text(y, v * 1.02, f"{y}\n{v:,.0f}", ha="center", va="bottom", fontsize=7.2, color=GREY)
    ax.set_xlim(keep[0], keep[-1] + 1); ax.set_ylim(0, max(bottom[i] + rest[i] for i in range(len(keep))) * 1.16)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylabel("People", fontsize=8.5, color=GREY)
    _style(ax)
    ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=7.4)
    return _save(fig, "C08_growth")


# ---------------------------------------------------------------- C09
def c09_flow():
    """Sewage by year: today's plots and the growth, to saturation, with the
    five-year points marked."""
    t = F.totals(); q = t["q"]; ult = t["ultimate"]
    years = [y for y in t["years"] if y <= ult]
    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    ax.fill_between(years, 0, [t["q_today"]] * len(years), color=PALE, linewidth=0, label=f"today's plots, {t['q_today']:,.0f} m³/d")
    ax.fill_between(years, [t["q_today"]] * len(years), [q[y] for y in years], color=MID, linewidth=0, label="empty plots as they fill")
    fy = [y for y in years if (y - 2025) % 5 == 0 or y == ult]
    ax.plot(fy, [q[y] for y in fy], "o", color=BLUE, markersize=3.5)
    for y in (2030, 2055, ult):
        ax.text(y, q[y] + 900, f"{q[y]:,.0f}", ha="center", va="bottom", fontsize=7.4, color=BLUE)
    ax.set_xlim(years[0], years[-1] + 1); ax.set_ylim(0, max(q[y] for y in years) * 1.18)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylabel("Average sewage flow, m³/d", fontsize=8.5, color=GREY)
    _style(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=7.8)
    return _save(fig, "C09_flow")


# ---------------------------------------------------------------- C10
def c10_fill_years():
    """The year each settlement fills, against its people today."""
    rows = [r for r in F.settlement_table() if r["sat_year"]]
    rows = sorted(rows, key=lambda r: r["sat_year"])
    names = [r["name"] for r in rows]; ys = [r["sat_year"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    big = {"Ibri", "Al Araqi", "Ad Dariz", "Al Qurayn", "Shalashil"}
    cols = [BLUE if n in big else PALE for n in names]
    ax.barh(names, [y - F.BASE_YEAR for y in ys], left=F.BASE_YEAR, color=cols, height=0.62, edgecolor="white", linewidth=0.6)
    for n, y in zip(names, ys):
        ax.text(y + 0.4, n, str(y), ha="left", va="center", fontsize=7.2, color=GREY)
    ax.set_xlim(F.BASE_YEAR, max(ys) + 6)
    ax.set_xlabel("Year the empty plots are full", fontsize=8.5, color=GREY)
    ax.invert_yaxis()
    _style(ax, xgrid=True, ygrid=False)
    plt.setp(ax.get_yticklabels(), fontsize=7.2)
    ax.legend(handles=[Patch(facecolor=BLUE, label="Ibri and the settlements that take its overflow"),
                       Patch(facecolor=PALE, label="other settlements")],
              loc="upper right", frameon=False, fontsize=7.4)
    return _save(fig, "C10_fill_years")


# ---------------------------------------------------------------- C11
def c11_streams():
    """Today's sewage by stream. Source: facts_w14.plot_summary."""
    ps = F.plot_summary()
    data = [("Domestic", ps["s_dom"], BLUE), ("Non-domestic", ps["s_nd"], MID), ("Governmental", ps["s_gov"], AMBER),
            ("Industrial estates", ps["s_spec"], PURPLE)]
    total = sum(d[1] for d in data)
    fig, ax = plt.subplots(figsize=(6.6, 1.55))
    left = 0
    for label, v, c in data:
        ax.barh([0], [v], left=left, color=c, height=0.5, edgecolor="white", linewidth=1.2)
        if v / total > 0.06:
            ax.text(left + v / 2, 0, f"{v:,.0f}", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        left += v
    ax.set_xlim(0, total); ax.set_ylim(-0.3, 0.48); ax.axis("off")
    ax.legend(handles=[Patch(facecolor=c, label=f"{l} {v / total * 100:.0f} %") for l, v, c in data],
              loc="lower center", ncol=4, frameon=False, fontsize=7.6, bbox_to_anchor=(0.5, -0.32))
    ax.text(0, 0.40, f"{total:,.0f} m³/d today", fontsize=8.5, color=GREY)
    return _save(fig, "C11_streams")


ALL = (c01_accounts, c02_occupancy, c04_population, c07_landuse, c08_growth, c09_flow, c10_fill_years, c11_streams)

if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    print("charts R2:")
    for fn in ALL:
        fn()
