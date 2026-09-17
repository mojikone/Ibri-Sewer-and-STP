"""Charts added for Revision 3 of the Concept Design Report: one for each block of data the
revision brought in, so the numbers can be read at a glance. Every value comes from the
facts modules the text reads. Re-runnable; writes PNG into img/.

    python charts_r3.py
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "report_basis"))
from charts import _style, _save, _thousands, BLUE, MID, PALE, GREY, RED, GREEN, AMBER  # noqa: E402
import facts_w14 as F  # noqa: E402
import facts_basis as B  # noqa: E402

fmt = F.fmt


def _bar_labels(ax, bars, vals, dy, size=7.4, colour=GREY, decimals=0):
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy, f"{v:,.{decimals}f}", ha="center", va="bottom", fontsize=size, color=colour)


# ---------------------------------------------------------------- R01 the two horizons
def r01_horizon():
    """2055 against the saturation year: people, and the three flows. Source: F.totals, B.plant_flows."""
    t = F.totals(); ult = t["ultimate"]; pf = B.plant_flows()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.0), gridspec_kw={"width_ratios": [1, 2.4]})
    years = ["2055", str(ult)]; cols = [MID, BLUE]
    vals = [t["pop"][2055], t["pop_ult"]]
    bars = a1.bar(years, vals, color=cols, width=0.55); _bar_labels(a1, bars, vals, max(vals) * 0.012)
    a1.set_title("People", fontsize=9, color=GREY); a1.yaxis.set_major_formatter(FuncFormatter(_thousands)); a1.set_ylim(0, max(vals) * 1.15); _style(a1)
    groups = ["Average sewage flow", "STP average\nwith the margin", "STP peak hour\nwith the margin"]
    v55 = [t["q"][2055], pf[2055]["aaf"], pf[2055]["phf"]]; vs = [t["q_ult"], pf[ult]["aaf"], pf[ult]["phf"]]
    x = range(len(groups)); w = 0.36
    b1 = a2.bar([i - w / 2 for i in x], v55, w, color=MID, label="2055, opening year plus 25")
    b2 = a2.bar([i + w / 2 for i in x], vs, w, color=BLUE, label=f"{ult}, the land is full")
    _bar_labels(a2, b1, v55, max(vs) * 0.012); _bar_labels(a2, b2, vs, max(vs) * 0.012)
    a2.set_xticks(list(x)); a2.set_xticklabels(groups, fontsize=8); a2.set_title("Flow, m³/d", fontsize=9, color=GREY)
    a2.yaxis.set_major_formatter(FuncFormatter(_thousands)); a2.set_ylim(0, max(vs) * 1.15); _style(a2)
    a2.legend(frameon=False, fontsize=7.8, loc="upper left")
    fig.tight_layout()
    return _save(fig, "R01_horizon")


# ---------------------------------------------------------------- R02 settlement flows
def r02_settlement_flows():
    """Average sewage flow of every settlement in 2055 and at saturation. Source: F.settlement_table, B.no_overflow."""
    t = F.totals(); ult = t["ultimate"]; st = F.settlement_table()
    q_ult = {r["key"]: r[ult]["q_with"] for r in B.no_overflow()["rows"]}
    rows = sorted(st, key=lambda r: q_ult[r["key"]])
    names = [r["name"] for r in rows]; v55 = [r["q_2055"] for r in rows]; vs = [q_ult[r["key"]] for r in rows]
    fig, ax = plt.subplots(figsize=(7.4, 6.2)); y = range(len(rows)); h = 0.38
    ax.barh([i + h / 2 for i in y], v55, h, color=MID, label="2055")
    ax.barh([i - h / 2 for i in y], vs, h, color=BLUE, label=f"{ult}, saturation")
    for i, (a, b) in enumerate(zip(v55, vs)):
        ax.text(max(a, b) + max(vs) * 0.008, i, f"{a:,.0f}  /  {b:,.0f}", va="center", fontsize=6.8, color=GREY)
    ax.set_yticks(list(y)); ax.set_yticklabels(names, fontsize=7.6); ax.set_xlim(0, max(vs) * 1.2)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands)); ax.set_xlabel("Average sewage flow, m³/d  (2055 / saturation)", fontsize=8.5, color=GREY)
    _style(ax, xgrid=True, ygrid=False); ax.legend(frameon=False, fontsize=8, loc="lower right")
    return _save(fig, "R02_settlement_flows")


# ---------------------------------------------------------------- R03 the peak factor
def r03_peak_factor():
    """Peak factor against the average flow: Merrimack above 100 properties, Peltier at or below.
    Source: B.merrimack, B.peltier_pf; the switch at 100 properties on the new-home rate."""
    t = F.totals(); ult = t["ultimate"]
    st = F.settlement_table(); or_mean = t["pop_today"] / sum(r["properties"] for r in st)
    q100 = 100 * or_mean * B.NEW_HOME_LPD / 1000.0 if hasattr(B, "NEW_HOME_LPD") else 100 * or_mean * 171.3 / 1000.0   # m3/d of 100 properties
    qs = [10 ** (k / 40.0) for k in range(0, 40 * 5 + 1)]           # 1 to 100,000 m3/d
    mer = [B.merrimack(q) / q for q in qs]; pel = [B.peltier_pf(q) for q in qs]
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    lo = [q for q in qs if q <= q100]; hi = [q for q in qs if q >= q100]
    ax.plot(lo, [B.peltier_pf(q) for q in lo], color=AMBER, lw=2.2, label="Peltier, 100 properties or fewer")
    ax.plot(hi, [B.merrimack(q) / q for q in hi], color=BLUE, lw=2.2, label="Merrimack, over 100 properties")
    ax.plot(hi, [B.peltier_pf(q) for q in hi], color=AMBER, lw=1.0, ls=":", alpha=0.8)
    ax.plot(lo, [B.merrimack(q) / q for q in lo], color=BLUE, lw=1.0, ls=":", alpha=0.8)
    ax.axvline(q100, color=GREY, lw=0.8, ls="--"); ax.text(q100 * 1.08, 4.55, f"100 properties\n≈ {q100:,.0f} m³/d", fontsize=7.4, color=GREY, va="top")
    ax.axhline(5.0, color=RED, lw=0.8, ls="--"); ax.text(1.2, 5.06, "5.0, the ceiling the guideline recommends", fontsize=7.4, color=RED, va="bottom")
    for label, q, dy, va in ((f"whole area, {ult}", t["q_ult"], -0.18, "top"), ("whole area, 2055", t["q"][2055], 0.2, "bottom")):
        ax.plot([q], [B.merrimack(q) / q], "o", color=BLUE, ms=4)
        ax.text(q, B.merrimack(q) / q + dy, f"{label}: {B.merrimack(q) / q:.2f}", fontsize=7.2, color=BLUE, ha="right", va=va)
    ax.set_xscale("log"); ax.set_xlim(1, 1e5); ax.set_ylim(1.0, 5.6)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands)); ax.set_xlabel("Average flow of the plots upstream, m³/d (log scale)", fontsize=8.5, color=GREY)
    ax.set_ylabel("Peak factor", fontsize=8.5, color=GREY); _style(ax, xgrid=True); ax.legend(frameon=False, fontsize=7.8, loc="upper right", bbox_to_anchor=(1.0, 0.86))
    return _save(fig, "R03_peak_factor")


# ---------------------------------------------------------------- R04 loads
def r04_loads():
    """BOD and suspended solids at one STP for the whole area, by year. Source: B.process_loads."""
    pl = B.process_loads(); yrs = B.years()
    fig, ax = plt.subplots(figsize=(6.8, 3.0)); x = range(len(yrs)); w = 0.36
    bod = [pl[y]["bod_kgd"] for y in yrs]; tss = [pl[y]["tss_kgd"] for y in yrs]
    b1 = ax.bar([i - w / 2 for i in x], bod, w, color=BLUE, label="BOD, 60 g per person per day")
    b2 = ax.bar([i + w / 2 for i in x], tss, w, color=PALE, label="Suspended solids, 80 g per person per day")
    _bar_labels(ax, b1, bod, max(tss) * 0.012); _bar_labels(ax, b2, tss, max(tss) * 0.012)
    ax.set_xticks(list(x)); ax.set_xticklabels([str(y) for y in yrs], fontsize=8.5); ax.set_ylabel("Load, kg/d", fontsize=8.5, color=GREY)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands)); ax.set_ylim(0, max(tss) * 1.18); _style(ax); ax.legend(frameon=False, fontsize=7.8, loc="upper left")
    return _save(fig, "R04_loads")


# ---------------------------------------------------------------- R05 treated effluent
def r05_tse():
    """STP inflow, treated effluent produced and delivered, by year. Source: B.tse."""
    ts = B.tse(); yrs = B.years()
    fig, ax = plt.subplots(figsize=(6.8, 3.0)); x = range(len(yrs)); w = 0.26
    series = [("STP inflow, design average", "inflow", BLUE), ("Produced, 95 per cent", "produced", MID), ("Delivered, less 10 per cent in the network", "delivered", GREEN)]
    top = max(ts[y]["inflow"] for y in yrs)
    for k, (lab, key, col) in enumerate(series):
        vals = [ts[y][key] for y in yrs]
        bars = ax.bar([i + (k - 1) * w for i in x], vals, w, color=col, label=lab); _bar_labels(ax, bars, vals, top * 0.012, size=6.6)
    ax.set_xticks(list(x)); ax.set_xticklabels([str(y) for y in yrs], fontsize=8.5); ax.set_ylabel("m³/d", fontsize=8.5, color=GREY)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands)); ax.set_ylim(0, top * 1.2); _style(ax); ax.legend(frameon=False, fontsize=7.6, loc="upper left")
    return _save(fig, "R05_tse")


# ---------------------------------------------------------------- R06 sewage strength
STRENGTH = [  # PAM-GUD-203 Table 30 (p67) network, Table 31 (p68) tanker average to maximum, mg/l
    ("BOD", (350, 400), (350, 1050)), ("COD", (700, 900), (1350, 5000)), ("Suspended solids", (400, 500), (900, 4300)),
    ("Total Kjeldahl nitrogen", (60, 80), (115, 265)), ("Ammonia as nitrogen", (40, 50), (70, 125)), ("Total phosphorus", (10, 15), (16, 35))]


def r06_strength():
    """The range of raw sewage strength the guideline gives: through the network, and by tanker."""
    fig, ax = plt.subplots(figsize=(7.0, 3.1)); h = 0.34
    for i, (name, net, tank) in enumerate(reversed(STRENGTH)):
        ax.barh(i + h / 2, net[1] - net[0], h, left=net[0], color=BLUE)
        ax.barh(i - h / 2, tank[1] - tank[0], h, left=tank[0], color=AMBER)
        ax.text(net[1] * 1.06, i + h / 2, f"{net[0]:,} to {net[1]:,}", va="center", fontsize=6.8, color=BLUE)
        ax.text(tank[1] * 1.06, i - h / 2, f"{tank[0]:,} to {tank[1]:,}", va="center", fontsize=6.8, color="#a87413")
    ax.set_yticks(range(len(STRENGTH))); ax.set_yticklabels([s[0] for s in reversed(STRENGTH)], fontsize=8)
    ax.set_xscale("log"); ax.set_xlim(8, 14000); ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_xlabel("mg/l (log scale)", fontsize=8.5, color=GREY); _style(ax, xgrid=True, ygrid=False)
    ax.legend(handles=[Patch(facecolor=BLUE, label="Sewage through the network"), Patch(facecolor=AMBER, label="Sewage by tanker, average to maximum")],
              frameon=False, fontsize=7.8, loc="lower right")
    return _save(fig, "R06_strength")


# ---------------------------------------------------------------- R07 the 126 meters
def r07_free_meters():
    """The meters more than 15 m from any plot, by tariff and by settlement. Source: B.free_meters."""
    fm = B.free_meters()
    tar = sorted(fm["by_tariff"].items(), key=lambda kv: kv[1]); sett = sorted(fm["by_settle"].items(), key=lambda kv: kv[1])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.6), gridspec_kw={"width_ratios": [1.25, 1]})
    dom = ("Primary Account Tariff", "Primary Account Tariff (with National Subsidy)", "Additional Account Tariff")
    a1.barh([k.replace(" (with National Subsidy)", ", subsidised").replace(" Tariff", "") for k, _ in tar], [v for _, v in tar],
            color=[RED if k in dom else MID for k, _ in tar], height=0.62)
    for i, (_, v) in enumerate(tar):
        a1.text(v + 0.6, i, str(v), va="center", fontsize=7.4, color=GREY)
    a1.set_title(f"By tariff ({fm['count']} meters)", fontsize=9, color=GREY); _style(a1, xgrid=True, ygrid=False); a1.tick_params(labelsize=7.4)
    a1.legend(handles=[Patch(facecolor=RED, label=f"domestic: {fm['domestic']}"), Patch(facecolor=MID, label="other")], frameon=False, fontsize=7.6, loc="lower right")
    a2.barh([F.NAME.get(k, k.title()) for k, _ in sett], [v for _, v in sett], color=PALE, height=0.62)
    for i, (_, v) in enumerate(sett):
        a2.text(v + 0.3, i, str(v), va="center", fontsize=7.0, color=GREY)
    a2.set_title("By settlement", fontsize=9, color=GREY); _style(a2, xgrid=True, ygrid=False); a2.tick_params(labelsize=6.8)
    fig.tight_layout()
    return _save(fig, "R07_free_meters")


# ---------------------------------------------------------------- R08 deliverables
def r08_deliverables():
    """The concept-stage deliverables by position. Source: deliverables.DELIVERABLES."""
    from deliverables import DELIVERABLES, CATEGORIES
    cols = {"issued": GREEN, "progress": MID, "survey": AMBER, "confirm": RED, "next": "#9aa5b1"}
    counts = [(lab, sum(1 for d in DELIVERABLES if d[2] == key), cols[key]) for key, lab in CATEGORIES]
    total = sum(c for _, c, _ in counts)
    fig, ax = plt.subplots(figsize=(6.8, 1.6)); left = 0
    for lab, v, col in counts:
        ax.barh([0], [v], left=left, color=col, height=0.5, edgecolor="white", linewidth=1.2)
        if v:
            ax.text(left + v / 2, 0, str(v), ha="center", va="center", fontsize=10, color="white", fontweight="bold")
        left += v
    ax.set_xlim(0, total); ax.set_ylim(-0.30, 0.48); ax.axis("off")
    ax.legend(handles=[Patch(facecolor=c, label=l) for l, _, c in counts], loc="lower center", ncol=5, frameon=False, fontsize=7.4, bbox_to_anchor=(0.5, -0.34))
    ax.text(0, 0.40, f"{total} groups of deliverables at the concept stage", fontsize=8.5, color=GREY)
    return _save(fig, "R08_deliverables")


if __name__ == "__main__":
    for fn in (r01_horizon, r02_settlement_flows, r03_peak_factor, r04_loads, r05_tse, r06_strength, r07_free_meters, r08_deliverables):
        fn()
