"""Charts for the Concept Design Report.

Every chart is drawn from a figure that appears somewhere in the report text,
so the picture and the words cannot drift apart. The data sits at the top of
each function with its source named, and nothing is computed twice.

Re-runnable; writes PNG into img/.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

BLUE = "#1f3b63"
MID = "#2e629e"
PALE = "#a8c4e0"
GREY = "#5a5a5a"
LIGHT = "#d8dde3"
RED = "#a61b1b"
GREEN = "#1f7a4d"
AMBER = "#c8873a"

DPI = 200


def _style(ax, xgrid=False, ygrid=True):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#b8b8b8")
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=GREY, labelsize=8, length=3, width=0.8)
    if ygrid:
        ax.yaxis.grid(True, color="#e4e4e4", linewidth=0.8)
    if xgrid:
        ax.xaxis.grid(True, color="#e4e4e4", linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, name):
    path = os.path.join(IMG, name + ".png")
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   {name}")
    return path


def _thousands(x, _):
    return f"{int(x):,}"


# ---------------------------------------------------------------- C01
def c01_accounts():
    """Electricity accounts by guideline category.

    Source: W9/analysis/W9_ele_landuse.md, from ELE_accounts.shp (33,970).
    """
    data = [
        ("Domestic", 16_244, BLUE),
        ("Non-domestic", 9_392, MID),
        ("Domestic,\nadditional", 6_344, PALE),
        ("Governmental", 967, AMBER),
        ("Agricultural", 523, GREEN),
        ("Awaiting\nclassification", 500, LIGHT),
    ]
    names = [d[0] for d in data]
    vals = [d[1] for d in data]
    cols = [d[2] for d in data]

    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    bars = ax.bar(names, vals, color=cols, width=0.62,
                  edgecolor="white", linewidth=0.8)
    total = sum(vals)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + total * 0.012,
                f"{v:,}\n{v / total * 100:.1f} %", ha="center", va="bottom",
                fontsize=7.6, color=GREY, linespacing=1.35)
    ax.set_ylim(0, max(vals) * 1.24)
    ax.yaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_ylabel("Accounts", fontsize=8.5, color=GREY)
    _style(ax)
    plt.setp(ax.get_xticklabels(), fontsize=7.8)
    return _save(fig, "C01_accounts")


# ---------------------------------------------------------------- C02
def c02_occupancy():
    """Occupancy by settlement against the adopted rate.

    Source: W9/analysis/W9_ele_landuse.md. Population from NCSI 2024;
    domestic properties counted from the electricity accounts.
    """
    rows = [
        ("Ibri", 10_802, 6.21), ("Al Araqi", 2_425, 4.41),
        ("Ad Dariz", 2_380, 4.98), ("Al Aynayn", 856, 5.32),
        ("At Tayyib", 797, 4.20), ("Al Wahrah", 718, 4.67),
        ("Ad Dibayshi", 670, 3.60), ("Al Jibayyah", 526, 5.11),
        ("Sayh al Masarrat", 434, 1.07), ("Bat", 420, 6.09),
        ("Hijar", 330, 3.13), ("Tanam", 322, 6.57),
        ("Al Jahli", 320, 1.30), ("Suwayda al Ma", 297, 5.25),
        ("Al Qurayn", 137, 4.01), ("Al Ghubayrah", 126, 5.01),
        ("Al Akheedar", 121, 1.64), ("Al Makhtibyah", 63, 1.94),
        ("Al Qali", 54, 3.54), ("Satwah", 26, 10.12),
        ("Shalashil", 24, 5.42), ("Usaybuq", 17, 5.35),
        ("Ash Shiab", 12, 3.92), ("Wadi al Mankas", 8, 6.50),
        ("Miayrid", 4, 8.50),
    ]
    ADOPTED = 5.32
    # the four settlements whose boundaries are under review; the aggregate
    # rate includes them, they are marked so the reader can see which they are
    REVIEW = {"Sayh al Masarrat", "Al Jahli", "Al Akheedar", "Satwah"}
    rows = sorted(rows, key=lambda r: -r[1])
    names = [r[0] for r in rows]
    ors = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    cols = [AMBER if n in REVIEW else MID for n in names]
    ax.bar(names, ors, color=cols, width=0.66, edgecolor="white",
           linewidth=0.7)
    ax.axhline(ADOPTED, color=RED, linewidth=1.3, linestyle="--", zorder=3)
    # annotate clear of the bars, in the margin the xlim leaves for it
    ax.set_xlim(-0.7, len(names) + 3.0)
    ax.text(len(names) - 0.3, ADOPTED, f"adopted\nrate {ADOPTED:.2f}",
            ha="left", va="center", fontsize=8, color=RED,
            fontweight="bold", linespacing=1.3)
    ax.set_ylabel("Persons per domestic property", fontsize=8.5, color=GREY)
    ax.set_ylim(0, 11.2)
    _style(ax)
    plt.setp(ax.get_xticklabels(), rotation=55, ha="right", fontsize=7.2)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor=MID, label="settlement boundary accepted"),
        Patch(facecolor=AMBER, label="boundary under review"),
    ], loc="upper center", ncol=2, frameon=False, fontsize=7.8,
        bbox_to_anchor=(0.5, 1.13))
    return _save(fig, "C02_occupancy")


# ---------------------------------------------------------------- C03
def c03_coverage():
    """The check applied to the occupancy rate.

    Source: W9/analysis/W9_ele_landuse.md, coverage consistency check.
    """
    fig, ax = plt.subplots(figsize=(6.2, 2.5))
    labels = ["Population within the\nnamed settlements",
              "Domestic properties\ncounted"]
    vals = [63.4, 65.5]
    detail = ["116,456 of 183,564", "22,588 of 34,504 implied"]

    bars = ax.barh(labels, vals, color=[MID, PALE], height=0.5,
                   edgecolor="white", linewidth=0.8)
    ax.barh(labels, [100 - v for v in vals], left=vals, color="#f0f2f5",
            height=0.5, edgecolor="white", linewidth=0.8)
    for b, v, t in zip(bars, vals, detail):
        ax.text(v - 1.5, b.get_y() + b.get_height() / 2, f"{v:.1f} %",
                ha="right", va="center", fontsize=9, color="white",
                fontweight="bold")
        ax.text(101, b.get_y() + b.get_height() / 2, t, ha="left",
                va="center", fontsize=7.8, color=GREY)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of the wilayat, per cent", fontsize=8.5, color=GREY)
    ax.invert_yaxis()
    _style(ax, xgrid=True, ygrid=False)
    plt.setp(ax.get_yticklabels(), fontsize=8)
    return _save(fig, "C03_coverage")


# ---------------------------------------------------------------- C04
def c04_population():
    """Population by settlement, showing how concentrated the demand is.

    Source: NCSI 2024 population, joined to Towns.shp.
    """
    rows = [
        ("Ibri", 67_106), ("Ad Dariz", 11_850), ("Al Araqi", 10_696),
        ("Al Aynayn", 4_554), ("Al Wahrah", 3_351), ("At Tayyib", 3_348),
        ("Al Jibayyah", 2_686), ("Bat", 2_557), ("Ad Dibayshi", 2_411),
        ("Tanam", 2_116), ("Suwayda al Ma", 1_559), ("Hijar", 1_033),
        ("Al Ghubayrah", 631), ("Al Qurayn", 549),
        ("Sayh al Masarrat", 466), ("Al Jahli", 415), ("Satwah", 263),
        ("Al Akheedar", 198), ("Al Qali", 191), ("Shalashil", 130),
        ("Al Makhtibyah", 122), ("Usaybuq", 91), ("Wadi al Mankas", 52),
        ("Ash Shiab", 47), ("Miayrid", 34),
    ]
    total = sum(r[1] for r in rows)
    names = [r[0] for r in rows]
    vals = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    cols = [BLUE] + [MID] * 2 + [PALE] * (len(rows) - 3)
    bars = ax.barh(names, vals, color=cols, height=0.66,
                   edgecolor="white", linewidth=0.7)
    # every bar carries its number, so the small settlements stay readable
    # even where the bar itself is too short to see
    for i, (b, v) in enumerate(zip(bars, vals)):
        txt = f"{v:,}   ({v / total * 100:.0f} %)" if i < 3 else f"{v:,}"
        ax.text(v + total * 0.005, b.get_y() + b.get_height() / 2, txt,
                ha="left", va="center", fontsize=7.2,
                color=GREY if i else BLUE,
                fontweight="bold" if i == 0 else "normal")
    ax.set_xlim(0, max(vals) * 1.22)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_xlabel("Population, 2024", fontsize=8.5, color=GREY)
    ax.invert_yaxis()
    _style(ax, xgrid=True, ygrid=False)
    plt.setp(ax.get_yticklabels(), fontsize=7.4)
    return _save(fig, "C04_population")


# ---------------------------------------------------------------- C05
def c05_assets():
    """Wastewater asset length, constructed against proposed.

    Source: measured in the project GIS within the approved boundary,
    split on OP_STATUE. Recorded in data_facts.WASTEWATER.
    """
    rows = [
        ("Gravity sewer", 111.6, 199.3),
        ("Force / pumping main", 10.0, 23.2),
        ("Treated effluent main", 0.0, 45.7),
    ]
    names = [r[0] for r in rows]
    built = [r[1] for r in rows]
    prop = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(7.4, 2.5))
    ax.barh(names, built, color=BLUE, height=0.52,
                 edgecolor="white", linewidth=0.8, label="Constructed, 2006")
    ax.barh(names, prop, left=built, color=PALE, height=0.52,
            edgecolor="white", linewidth=0.8, hatch="///",
            label="Recorded as proposed")

    # labels sit in two fixed columns clear of the longest bar, so a short
    # segment never crowds its own text and the figures line up down the page
    COL_BUILT, COL_PROP = 328, 396
    for i, (b, p) in enumerate(zip(built, prop)):
        if b > 0:
            ax.text(COL_BUILT, i, f"{b:.1f} km", ha="left", va="center",
                    fontsize=8.4, color=BLUE, fontweight="bold")
        else:
            ax.text(COL_BUILT, i, "none built", ha="left", va="center",
                    fontsize=8.4, color=RED, fontweight="bold")
        ax.text(COL_PROP, i, f"+ {p:.1f} km proposed", ha="left",
                va="center", fontsize=8, color=GREY)

    ax.set_xlim(0, 520)
    ax.set_xticks([0, 50, 100, 150, 200, 250, 300])
    ax.set_xlabel("Length within the study area, kilometres", fontsize=8.5,
                  color=GREY)
    ax.invert_yaxis()
    _style(ax, xgrid=True, ygrid=False)
    plt.setp(ax.get_yticklabels(), fontsize=8.4)
    ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=8,
              bbox_to_anchor=(0.0, 1.22))
    return _save(fig, "C05_assets")


# ---------------------------------------------------------------- C06
def c06_register():
    """State of the data register at the date of issue.

    Source: data_facts.REGISTER, one entry per requested dataset.
    """
    import data_facts as F
    received = partial = outstanding = 0
    for _, got, _note in F.REGISTER:
        g = got.lower()
        if g.startswith("yes"):
            received += 1
        elif g.startswith("no"):
            outstanding += 1
        else:
            partial += 1

    data = [("Received and adopted", received, GREEN),
            ("Partly received, or in progress", partial, AMBER),
            ("Requested, outstanding", outstanding, RED)]
    total = received + partial + outstanding

    fig, ax = plt.subplots(figsize=(6.6, 1.55))
    left = 0
    for label, v, col in data:
        ax.barh([0], [v], left=left, color=col, height=0.5,
                edgecolor="white", linewidth=1.2)
        if v:
            ax.text(left + v / 2, 0, str(v), ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold")
        left += v
    ax.set_xlim(0, total)
    ax.set_ylim(-0.30, 0.48)
    ax.axis("off")

    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=c, label=f"{l}") for l, _, c in data],
              loc="lower center", ncol=3, frameon=False, fontsize=8,
              bbox_to_anchor=(0.5, -0.30))
    ax.text(0, 0.40, f"{total} datasets requested", fontsize=8.5, color=GREY)
    return _save(fig, "C06_register")


ALL = (c01_accounts, c02_occupancy, c03_coverage, c04_population,
       c05_assets, c06_register)


if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    print("charts:")
    for fn in ALL:
        fn()
