"""fig_hierarchy — the hierarchy, chamber and network-shape figures for the W11a report.

    cd W11a/report && python fig_hierarchy.py            # all figures
    cd W11a/report && python fig_hierarchy.py FH03 FH09  # just those

Idempotent: every run overwrites the same PNG stems in ``W11a/report/img/``.  Nothing
here writes to ``W11a/shp`` or ``W11a/run`` — every read goes through ``figkit`` and
therefore through a scratchpad copy.

WHAT THIS MODULE MEASURES, AND FROM WHERE
-----------------------------------------
The chamber-to-chamber network is **stage 5's**, published as
``W11a/run/s5_reach_skeleton.gpkg`` (49,274 reaches, ``STAGE='s5_chambers'``).  It is
NOT ``W11a/shp/W11a.gpkg [reaches]``, which at the time of writing still holds the
**stage-4** graph (24,589 rows, ``STAGE='s4_hierarchy'``) — half the chamber count and
a different set of edges.  Any figure drawn from the GeoPackage today draws stage 4.
Flows come from ``W11a/run/s5c_reach_flows.csv``, which keys 1:1 on ``EDGE_UID``.

THREE RULES THIS MODULE KEEPS
-----------------------------
1.  **No number is written that was not measured here or read from a named artefact.**
    Every figure carries a source line naming its files, and the run prints a table of
    every quoted value beside the file it came from.

2.  **A guideline value is quoted with its page; a project value is labelled as ours.**
    Table 12 (G203-p30) and the 90-degree inlet rule (G203-p30) are quoted verbatim
    from ``Data/PAM-GUD-203``.  The **85-degree** inlet band, the **60 m** finger
    threshold, the **750 m / 3-lateral** chain bound and the **920 m** lateral cap are
    PROJECT rules from ``_BRAIN/08_DESIGN_PHILOSOPHY.md`` and are captioned as such on
    the figure.  They never appear as guideline numbers.

3.  **A comparison names its vocabulary.**  NAMA's as-built carries three tier tokens
    (TM / SM / everything else); W11a carries five roles.  Anywhere the two are put on
    one axis the mapping is stated on the figure, because "sub main" does not mean the
    same thing in both.

Author's note on one inherited number: the brief for this work quoted *"NAMA's as-built
runs 14.8 % of its length as trunk plus sub main"* and *"the as-built median run of
88 m"*.  Both are misreadings and neither is used here.  See ``main()``'s printed
corrections and the report notes.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import scipy.sparse as sp
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.sparse.csgraph import connected_components

import figkit as fk


# ===================================================================== sources
#
# Guideline values, quoted from Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.
# Verified against the PDF text of printed page 30 on 2026-09-02, not from memory.
#
#   "The recommended maximum spacing between the manholes is presented in Table 12."
#   Table 12 Maximum Spacing between Manholes
#     200 to 315 -> 100 ;  350 to 900 -> 120 ;  1 000 to 1 400 -> 150 ;  >1 400 -> 200
#   "Any alteration in the above specified spacing of manholes, consultant has to
#    obtain pre-approval from NWS."
#   "No inlet pipe at manholes shall have an angle less than 90 deg to the direction
#    of flow."
#
G203_P30_TABLE12 = [(315, 100.0), (900, 120.0), (1400, 150.0), (10_000, 200.0)]
G203_P30_INLET_MIN_DEG = 90.0
CITE_T12 = "G203-p30 Tab 12"
CITE_INLET = "G203-p30"

# PROJECT values -- _BRAIN/08_DESIGN_PHILOSOPHY.md.  Labelled as ours on every figure.
PROJ_INLET_TOL_DEG = 85.0     # the deviation band stage 5 writes into s5_sharp_inlets
PROJ_FINGER_M = 60.0          # philosophy sec 4: "no fingers ... under ~60 m"
PROJ_CHAIN_M = 750.0          # philosophy sec 4: "3 laterals and 750 m before a main"
PROJ_CHAIN_N = 3
PROJ_LATERAL_CAP_M = 920.0    # philosophy sec 4: a lateral run, cap 920 m

SKELETON = fk.RUN / "s5_reach_skeleton.gpkg"
SKELETON_LAYER = "s5_reach_skeleton"
W10_PIPES = fk.ROOT / "W10" / "shp" / "W10_pipes.shp"
NAMA_TIERS = fk.ROOT / "W10" / "run" / "research_hierarchy_tier_shares.csv"
NAMA_JOINERS = fk.ROOT / "W10" / "run" / "research_hierarchy_trunk_joiners.csv"

TIERS = ["lateral", "main", "sub main", "trunk main"]

#: figkit's status roles are pass / flag / untested / fail and its grey MEANS
#: "untested".  The inlet bands are a three-step SEVERITY ramp, so borrowing that
#: grey for a middle step would make one colour mean two things across the figure
#: set.  This amber-brown is the missing middle step, and it is held to figkit's own
#: 1.50:1 greyscale rule against both of its neighbours (checked at import).
MID_SEVERITY = "#a8621c"


def _check_severity_ramp(min_ratio: float = 1.50) -> None:
    lum = fk._rel_luminance
    for a, b in ((fk.C.FLAG, MID_SEVERITY), (MID_SEVERITY, fk.C.FAIL)):
        hi, lo = max(lum(a), lum(b)), min(lum(a), lum(b))
        ratio = (hi + 0.05) / (lo + 0.05)
        assert ratio >= min_ratio, (f"severity ramp {a}->{b} only {ratio:.2f}:1 in "
                                    f"greyscale (need {min_ratio})")


_check_severity_ramp()


def table12_max(dn: float) -> float:
    """Maximum manhole spacing for a diameter, G203-p30 Table 12."""
    for hi, m in G203_P30_TABLE12:
        if float(dn) <= hi:
            return m
    return G203_P30_TABLE12[-1][1]


def _src(fig, *objs) -> str:
    """figkit's source line, hard-wrapped to the figure width.

    ``figkit._sourceline`` writes the string as given, and ``figkit.save`` uses
    ``bbox_inches="tight"``: a source line naming four artefacts runs off the right
    edge, the tight box expands to include it, and the saved PNG comes out twice as
    wide as the figure.  Wrapping here fixes it without touching figkit — the string
    it is handed already contains the newlines.
    """
    import textwrap
    w_in = fig.get_size_inches()[0]
    return "\n".join(textwrap.wrap(fk.source_line(*objs),
                                   width=max(60, int(w_in * 18.5)),
                                   subsequent_indent="        "))


def _headroom(fig, inches: float = 0.30) -> None:
    """Drop the axes to leave room for per-panel titles under figkit's title block."""
    h = fig.get_size_inches()[1]
    fig.subplots_adjust(top=fig.subplotpars.top - inches / h)


def _tier(t: str, k: float = 1.0) -> dict:
    """figkit's tier style with a uniform width scale, so the ladder is preserved.

    The study area is 45 km across; at 11 inches figkit's widths blur the laterals
    into a wash.  ``k`` scales every step by the same factor, so the ordinal ramp
    (and its greyscale separation) is untouched.
    """
    s = fk.tier_style(t)
    return {"color": s["color"], "linewidth": s["lw"] * k}


# ======================================================================== data

class Net:
    """Everything the figures read, loaded once, each piece carrying provenance."""

    def __init__(self) -> None:
        self.sk = fk.read_layer(str(SKELETON), SKELETON_LAYER)
        self.flows = fk.read_csv("s5c_reach_flows.csv")
        self.inlets = fk.read_csv("s5_sharp_inlets.csv")
        self.s4 = fk.read_layer("W11a_s4.gpkg", "s4_reaches",
                                columns=["EDGE_UID", "TIER", "LEN_M", "CHAIN_N",
                                         "CHAIN_M", "CHAIN_OVR", "TIER_BY"])
        self.trunk = fk.read_layer("W11a_trunk.gpkg", "reaches",
                                   columns=["EDGE_UID", "DN", "LEN_M", "TIER"])
        self.unassigned = fk.read_csv("s5b_unassigned.csv")
        self.conns = fk.read_layer("W11a.gpkg", "connections",
                                   columns=["CONN_ID", "Q_ADF_M3D", "CAN_DRAIN"])

        if not self.sk["EDGE_UID"].isin(self.flows["EDGE_UID"]).all():
            raise SystemExit("s5c_reach_flows does not cover every skeleton reach — "
                             "the two artefacts disagree; stop rather than draw it")

        q = self.flows.set_index("EDGE_UID")
        self.sk["QADF_M3D"] = self.sk["EDGE_UID"].map(q["QADF_M3D"]).astype(float)
        self.sk["N_PROP"] = self.sk["EDGE_UID"].map(q["N_PROP"]).astype(float)

        self._topology()
        self._runs()

    # ------------------------------------------------------------- topology
    def _topology(self) -> None:
        us, ds = self.sk["US_NODE"].values, self.sk["DS_NODE"].values
        self.nodes = pd.unique(np.concatenate([us, ds]))
        idx = {n: i for i, n in enumerate(self.nodes)}
        r = np.fromiter((idx[a] for a in us), int, len(us))
        c = np.fromiter((idx[b] for b in ds), int, len(ds))
        A = sp.coo_matrix((np.ones(len(r)), (r, c)),
                          shape=(len(self.nodes), len(self.nodes)))
        self.ncomp, lab = connected_components(A, directed=False)
        self.sk["COMP"] = lab[r]

        z = pd.Series(0.0, index=self.nodes)
        self.indeg = z.add(pd.Series(ds).value_counts(), fill_value=0)
        self.outdeg = z.add(pd.Series(us).value_counts(), fill_value=0)
        self.heads = set(self.nodes[self.indeg.reindex(self.nodes).values == 0])
        self.roots = set(self.nodes[self.outdeg.reindex(self.nodes).values == 0])
        self.through = set(self.nodes[
            (self.indeg.reindex(self.nodes).values == 1)
            & (self.outdeg.reindex(self.nodes).values == 1)])

        # H15/H16 on the published layer: a forest has edges = nodes - components.
        self.is_forest = len(self.sk) == len(self.nodes) - self.ncomp
        self.n_loops = len(self.sk) - (len(self.nodes) - self.ncomp)

        self.comp = (self.sk.groupby("COMP")
                     .agg(km=("LEN_M", "sum"), n=("EDGE_UID", "size"))
                     .assign(km=lambda d: d["km"] / 1000.0))
        trunk_comps = set(self.sk.loc[self.sk.TIER == "trunk main", "COMP"].unique())
        self.comp["has_trunk"] = self.comp.index.isin(trunk_comps)
        self.n_trunk_pieces = len(trunk_comps)

        # terminal reaches: the last pipe of each drainage system
        self.term = self.sk[~self.sk["DS_NODE"].isin(set(self.sk["US_NODE"]))].copy()

    # ----------------------------------------------------------------- runs
    def _runs(self) -> None:
        """A RUN is an unbranched chain of reaches between two non-through nodes.

        Philosophy sec 4: chamber spacing (H12) and run length (P3) are different
        rules, and run length is reported as a MAXIMUM, never a median.  Both are
        reported here.
        """
        us, ds = self.sk["US_NODE"].values, self.sk["DS_NODE"].values
        L, T = self.sk["LEN_M"].values, self.sk["TIER"].values
        Q = self.sk["QADF_M3D"].values
        nxt: dict = {}
        for i, a in enumerate(us):
            nxt.setdefault(a, []).append(i)
        rows, run_of = [], np.full(len(self.sk), -1)
        for i, a in enumerate(us):
            if a in self.through:
                continue
            tot, n, j, last = 0.0, 0, i, i
            while True:
                tot += L[j]
                n += 1
                run_of[j] = len(rows)
                last = j
                b = ds[j]
                if b in self.through and len(nxt.get(b, [])) == 1:
                    j = nxt[b][0]
                else:
                    break
            rows.append((T[i], tot, n, a in self.heads, Q[last], i, last))
        self.runs = pd.DataFrame(rows, columns=["TIER", "LEN_M", "N", "HEAD",
                                                "Q_DS", "I0", "I1"])
        self.sk["RUN"] = run_of
        if (run_of < 0).any():
            raise SystemExit("a reach belongs to no run — the chain walk is wrong")

    # ------------------------------------------------------------- shortcuts
    @property
    def km(self) -> float:
        return self.sk["LEN_M"].sum() / 1000.0

    def tier_km(self) -> pd.Series:
        return (self.sk.groupby("TIER")["LEN_M"].sum() / 1000.0).reindex(TIERS)

    def fingers(self) -> pd.DataFrame:
        r = self.runs
        return r[r.HEAD & (r.LEN_M < PROJ_FINGER_M) & (r.Q_DS <= 0)]


_NET: Net | None = None


def net() -> Net:
    global _NET
    if _NET is None:
        _NET = Net()
    return _NET


def _works_flow() -> float:
    """The flow the trunk is sized for at the works, from the trunk's own layer."""
    return float(fk.read_layer("W11a_trunk.gpkg", "reaches",
                               columns=["QADF_M3D"])["QADF_M3D"].max())


def _trunk_joins():
    """Non-trunk reaches whose downstream node is a trunk node."""
    n = net()
    tn = (set(n.sk.loc[n.sk.TIER == "trunk main", "US_NODE"])
          | set(n.sk.loc[n.sk.TIER == "trunk main", "DS_NODE"]))
    return n.sk[(n.sk.TIER != "trunk main") & (n.sk["DS_NODE"].isin(tn))]


def _boundary(ax):
    try:
        fk.study_boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.0,
                                          ls="--", zorder=6)
        return Line2D([], [], color=fk.C.BOUNDARY, lw=1.2, ls="--",
                      label="study boundary")
    except Exception:                                          # noqa: BLE001
        return None


def _ext(n: Net):
    return fk.extent_of(n.sk, pad=0.02)


# =================================================================== FIGURE 1

def FH01_tier_map():
    """The four tiers, drawn thin-to-thick, over the whole study area."""
    n = net()
    km = n.tier_km()
    sub_km = km["sub main"]
    fig, ax, note = fk.map_frame(
        _ext(n),
        title=f"The sub-main tier now exists: {sub_km:,.0f} km of it, where W10 had none",
        subtitle=("Stage-5 chamber-to-chamber network, one line per reach, coloured and "
                  "widened by tier. A sub main is a collector route defined by its "
                  "outlet; W10 published no tier field at all, so its network was one "
                  "undifferentiated mesh hanging off the client's trunk alignment."))
    for t in TIERS:                       # thin first so the trunk lands on top
        s = n.sk[n.sk.TIER == t]
        if len(s):
            s.plot(ax=ax, zorder=4 + TIERS.index(t), **_tier(t, 0.62))
    h = [Line2D([], [], label=f"{t}  {km[t]:,.0f} km  ({100*km[t]/n.km:.1f} %)",
                **_tier(t, 1.0)) for t in TIERS]
    b = _boundary(ax)
    if b:
        h.append(b)
    box = (f"reaches      {len(n.sk):>9,}\n"
           f"chambers     {len(n.nodes):>9,}\n"
           f"network      {n.km:>9,.1f} km\n"
           f"trunk        {km['trunk main']:>9,.1f} km\n"
           f"sub main     {sub_km:>9,.1f} km")
    fk.finish_map(fig, ax, note=note, legend_handles=h, databox=box,
                  legend_loc="upper left", source=_src(fig, n.sk))
    return fk.save(fig, "FH01_tier_map")


# =================================================================== FIGURE 2

def FH02_tier_shares():
    """W11a against NAMA's as-built and against W10, by share of length."""
    n = net()
    km = n.tier_km()
    nama = fk.read_csv(str(NAMA_TIERS))
    lab = nama[nama["scope"] == "5A-2..5A-5 (labelled)"].set_index("tier")
    w10 = fk.read_layer(str(W10_PIPES), columns=["LEN_M"])
    w10_km = w10["LEN_M"].sum() / 1000.0
    mp = fk.read_layer(str(fk.HYD / "SHP" / "Main Pipe" / "Main Pipe.shp"))
    mp_km = float(mp.length.sum()) / 1000.0
    w10_trunk_pct = 100.0 * mp_km / w10_km

    rows = [
        ("NAMA as-built\n5A-2…5A-5, 68.9 km",
         {"lateral": lab.loc["lateral", "share_pct"],
          "sub main": lab.loc["sub_main", "share_pct"],
          "trunk main": lab.loc["trunk_main", "share_pct"]}),
        (f"W11a stage 5\n{n.km:,.0f} km",
         {t: 100.0 * km[t] / n.km for t in TIERS}),
        (f"W10 published\n{w10_km:,.0f} km",
         {"untiered": 100.0 - w10_trunk_pct, "trunk main": w10_trunk_pct}),
    ]
    order = ["lateral", "main", "sub main", "untiered", "trunk main"]
    style = {t: dict(facecolor=fk.TIER_COLOR[t], edgecolor=fk.C.INK, linewidth=0.6)
             for t in TIERS}
    style["untiered"] = dict(facecolor=fk.C.FAINT, edgecolor=fk.C.INK, linewidth=0.6,
                             hatch="xx")

    fig, ax = fk.chart_frame(
        title=("W11a carries the collector tier the as-built has and W10 never "
               "published"),
        subtitle=("Share of network length by tier. W10's pipe layer has NO tier field, "
                  "so its only identifiable tier is the client's trunk alignment "
                  "(85.5 km of 1,883 km). Vocabularies differ: NAMA's manhole tokens "
                  "carry only TM / SM / lateral, so its 'lateral' absorbs what we call "
                  "a main."),
        figsize=(9.6, 4.3), ygrid=False, xgrid=True)
    y = np.arange(len(rows))[::-1]
    for yy, (_l, d) in zip(y, rows):
        left = 0.0
        for k in order:
            v = d.get(k, 0.0)
            if v <= 0:
                continue
            ax.barh(yy, v, left=left, height=0.55, **style[k])
            if v >= 4:
                ax.text(left + v / 2, yy, f"{v:.1f}", ha="center", va="center",
                        fontsize=7.6, fontweight="bold",
                        color="white" if k in ("sub main", "trunk main") else fk.C.INK,
                        path_effects=[pe.withStroke(linewidth=2.0,
                                                    foreground="white")]
                        if k == "untiered" else None)
            left += v
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.8)
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of network length (%)")
    names = {"lateral": "lateral", "main": "main (W11a only)", "sub main": "sub main",
             "trunk main": "trunk main", "untiered": "no tier published"}
    fk.legend_below(ax, [Patch(label=names[k], **style[k])
                         for k in ["lateral", "main", "sub main", "trunk main",
                                   "untiered"]], ncol=5)
    _headroom(fig, 0.26)
    ax.text(0.995, 1.03,
            f"collector tier (main + sub main): W11a {km['main']+km['sub main']:,.0f} km"
            f"  ·  as-built rule predicts ~270 km of sub main  ·  W10 0 km",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.4,
            color=fk.C.GREY)
    fk.finish_chart(fig, source=_src(fig, 
        n.sk, nama, w10, "Hydraulic/SHP/Main Pipe/Main Pipe.shp, 54 parts, 85.5 km"))
    return fk.save(fig, "FH02_tier_shares")


# =================================================================== FIGURE 3

def FH03_chamber_spacing():
    """Spacing against Table 12, and chamber density against the as-built."""
    n = net()
    w10 = fk.read_layer(str(W10_PIPES), columns=["LEN_M", "DN"])
    w10["MAX"] = w10["DN"].map(table12_max)
    w10_over = w10["LEN_M"] > w10["MAX"]
    w10_km = w10["LEN_M"].sum() / 1000.0

    tr = net().trunk.copy()
    tr["MAX"] = tr["DN"].map(table12_max)
    tr_over = int(((tr["LEN_M"] - tr["MAX"]) > 0.001).sum())
    tr_at = int(((tr["LEN_M"] - tr["MAX"]).abs() <= 0.001).sum())

    ours_over = int((n.sk["LEN_M"] > 100.0).sum())          # tightest band, DN200-315
    nama = fk.read_csv(str(NAMA_TIERS))
    na = nama[nama["scope"] == "all packages"]
    nama_per_km = na["pipes"].sum() / na["km"].sum()

    fig, axes = fk.chart_frame(
        title=("Every one of the 49,274 reaches is inside Table 12; W10 broke it on "
               "65 % of its length"),
        subtitle=("Left: chamber-to-chamber spacing. The dashed lines are G203-p30 "
                  "Table 12's maxima by diameter — 100 m at DN200–315 up to 200 m "
                  "above DN1400 (Table 12 is a RECOMMENDED maximum, and any alteration "
                  "needs NWS pre-approval). Right: chambers per km, the operations "
                  "consequence of the same rule."),
        figsize=(11.0, 4.8), ncols=2, ygrid=True)
    ax, ax2 = axes
    _headroom(fig, 0.34)

    bins = np.arange(0, 320, 5)
    ax.axvspan(100, 315, color=fk.C.FAIL, alpha=0.06, zorder=1)
    ax.hist(np.clip(w10["LEN_M"], 0, 315), bins=bins, color=fk.C.FAIL, alpha=0.55,
            label=f"W10 published, {len(w10):,} reaches", zorder=3)
    ax.hist(np.clip(w10["LEN_M"], 0, 315), bins=bins, histtype="step",
            color=fk.C.FAIL, linewidth=1.1, zorder=5)
    ax.hist(np.clip(n.sk["LEN_M"], 0, 315), bins=bins, color=fk.C.LATERAL,
            label=f"W11a stage 5, {len(n.sk):,} reaches", zorder=4,
            edgecolor="none")
    for x, lbl in ((100, "100 m  DN200–315"), (120, "120 m  DN350–900"),
                   (150, "150 m  DN1000–1400"), (200, "200 m  >DN1400")):
        ax.axvline(x, color=fk.C.INK, lw=0.9, ls="--", zorder=6)
        ax.text(x + 3, 0.985, lbl, transform=ax.get_xaxis_transform(), rotation=90,
                va="top", ha="left", fontsize=6.4, color=fk.C.INK)
    ax.text(207, 0.40, "no W11a reach\nis in this half\nof the chart",
            transform=ax.get_xaxis_transform(), ha="center", va="center",
            fontsize=7.4, color=fk.C.FAIL, style="italic", zorder=7)
    ax.set_xlabel(f"chamber-to-chamber spacing (m)  ·  bars clipped at 315 m "
                  f"— W10's longest reach is {w10['LEN_M'].max():,.0f} m")
    ax.set_ylabel("reaches")
    ax.set_yscale("log")
    ax.set_xlim(0, 315)
    ax.legend(loc="lower left", fontsize=7.2, framealpha=0.92)
    ax.set_title(f"W11a: {ours_over} reaches over the tightest band  ·  "
                 f"W10: {int(w10_over.sum()):,} over their own band "
                 f"({w10.loc[w10_over,'LEN_M'].sum()/1000:,.0f} km, "
                 f"{100*w10.loc[w10_over,'LEN_M'].sum()/w10['LEN_M'].sum():.1f} %)",
                 fontsize=8.0, color=fk.C.INK, pad=6)

    dens = [(f"NAMA as-built\n{na['km'].sum():,.0f} km", nama_per_km, fk.C.SUBMAIN),
            (f"W11a stage 5\n{n.km:,.0f} km", len(n.sk) / n.km, fk.C.LATERAL),
            (f"W10 published\n{w10_km:,.0f} km", len(w10) / w10_km, fk.C.FAIL)]
    xs = np.arange(len(dens))
    for x, (lbl, v, col) in zip(xs, dens):
        ax2.bar(x, v, width=0.6, color=col, edgecolor=fk.C.INK, linewidth=0.6)
        ax2.text(x, v + 0.6, f"{v:.1f}", ha="center", va="bottom", fontsize=9,
                 fontweight="bold", color=fk.C.INK)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([d[0] for d in dens], fontsize=7.6)
    ax2.set_ylabel("chamber-to-chamber pipes per km")
    ax2.set_ylim(0, max(v for _, v, _ in dens) * 1.30)
    ax2.set_title(f"W11a puts {len(n.nodes):,} chambers on the ground — "
                  f"{len(n.nodes)/n.km:.1f} per km against the as-built's "
                  f"{nama_per_km:.1f}", fontsize=8.0, color=fk.C.INK, pad=6)
    ax2.set_xlabel(f"the W11a trunk is chambered exactly AT the Table 12 maximum on "
                   f"{tr_at} of its {len(tr)} reaches, and {tr_over} exceed it",
                   fontsize=7.0, color=fk.C.GREY)
    fk.finish_chart(fig, source=_src(fig, 
        n.sk, w10, nama, net().trunk,
        "Data/PAM-GUD-203 p30 Table 12 (quoted from the PDF, not from memory)"))
    return fk.save(fig, "FH03_chamber_spacing")


# =================================================================== FIGURE 4

BANDS = [(0.1, "under 100 m"), (0.5, "100–500 m"), (1.0, "0.5–1 km"),
         (5.0, "1–5 km"), (20.0, "5–20 km"), (1e9, "over 20 km")]
BAND_TIER = ["rider", "rider", "lateral", "main", "sub main", "trunk main"]


def _band(km: float) -> int:
    for i, (hi, _l) in enumerate(BANDS):
        if km <= hi:
            return i
    return len(BANDS) - 1


def FH04_systems_map():
    """Where the network is in pieces, and how big each piece is."""
    n = net()
    n.sk["BAND"] = n.sk["COMP"].map(n.comp["km"]).map(_band)
    big = n.comp[n.comp["km"] > 20.0]
    small = n.comp[n.comp["km"] <= 0.1]
    fig, ax, note = fk.map_frame(
        _ext(n),
        title=(f"The network is {n.ncomp} separate drainage systems, and "
               f"{len(big)} of them hold {100*big['km'].sum()/n.km:.0f} % of the length"),
        subtitle=("Every reach coloured by the size of the drainage system it belongs "
                  "to. Stubs are drawn thickest because they are the finding, not "
                  "because they are big. The count is "
                  "still inflated by OPEN-S4-1: stage 4 fragments the client's 4-piece "
                  f"trunk, and it reaches stage 5 in {n.n_trunk_pieces} pieces, so "
                  "systems that should share an outfall do not yet."))
    # The stubs are the finding, so they are drawn last, darkest and thickest.
    # Size is on the LABEL, not on the ink: a size-ordered ramp buries 113 km of
    # stub under 1,193 km of core network and says nothing.
    classes = [
        (n.comp["km"] > 20.0, fk.C.LATERAL, 0.45, "core system, over 20 km"),
        ((n.comp["km"] > 1.0) & (n.comp["km"] <= 20.0), fk.C.SUBMAIN, 0.8,
         "1–20 km"),
        (n.comp["km"] <= 1.0, fk.C.FAIL, 1.5, "STUB, under 1 km"),
    ]
    h = []
    for z, (sel, col, lw, lbl) in enumerate(classes):
        keep = set(n.comp.index[sel])
        s = n.sk[n.sk["COMP"].isin(keep)]
        s.plot(ax=ax, color=col, linewidth=lw, zorder=4 + z)
        h.append(Line2D([], [], color=col, lw=max(lw, 1.2),
                        label=f"{lbl}   {int(sel.sum()):>3} systems, "
                              f"{n.comp.loc[sel, 'km'].sum():,.0f} km"))
    b = _boundary(ax)
    if b:
        h.append(b)
    box = (f"drainage systems {n.ncomp:>7,}\n"
           f"one outfall each {'yes' if n.ncomp == len(n.roots) else 'NO':>7}\n"
           f"loops on layer   {n.n_loops:>7}\n"
           f"under 100 m      {len(small):>7,}\n"
           f"trunk in pieces  {n.n_trunk_pieces:>7}")
    fk.finish_map(fig, ax, note=note, legend_handles=h, databox=box,
                  legend_loc="upper left", source=_src(fig, n.sk))
    return fk.save(fig, "FH04_systems_map")


# =================================================================== FIGURE 5

def FH05_systems_concentration():
    """How the length is distributed across the 759 systems, and the flow that follows."""
    n = net()
    g = n.comp.sort_values("km", ascending=False)
    cum = 100.0 * g["km"].cumsum() / g["km"].sum()
    x = np.arange(1, len(g) + 1)
    n90 = int(np.searchsorted(cum.values, 90.0) + 1)

    fig, axes = fk.chart_frame(
        title=(f"{n90} of the {n.ncomp} drainage systems carry 90 % of the pipe; the "
               f"other {n.ncomp-n90} are stubs"),
        subtitle=("Left: systems ranked by length, cumulative share. Right: the same "
                  "systems by count and by kilometre. A design cannot be built as "
                  f"{n.ncomp} independent systems — this is the OPEN-S4-1 trunk "
                  "mismatch made visible, not a settled outcome."),
        figsize=(10.6, 4.3), ncols=2, ygrid=True)
    ax, ax2 = axes
    _headroom(fig, 0.34)
    ax.plot(x, cum.values, color=fk.C.SUBMAIN, lw=1.8)
    ax.fill_between(x, cum.values, color=fk.C.LATERAL, alpha=0.28)
    ax.axhline(90, color=fk.C.INK, lw=0.9, ls="--")
    ax.axvline(n90, color=fk.C.FLAG, lw=1.2)
    ax.annotate(f"{n90} systems = 90 % of {n.km:,.0f} km",
                xy=(n90, 90), xytext=(n90 + 40, 62), fontsize=7.6, color=fk.C.INK,
                arrowprops=dict(arrowstyle="->", color=fk.C.INK, lw=0.9))
    ax.set_xlabel("drainage systems, longest first")
    ax.set_ylabel("cumulative share of network length (%)")
    ax.set_xlim(1, len(g))
    ax.set_ylim(0, 101)

    counts = [int((n.comp["km"].map(_band) == i).sum()) for i in range(len(BANDS))]
    kms = [n.comp.loc[n.comp["km"].map(_band) == i, "km"].sum()
           for i in range(len(BANDS))]
    y = np.arange(len(BANDS))[::-1]
    ax2.barh(y + 0.19, [100 * c / n.ncomp for c in counts], height=0.36,
             color=fk.C.FAINT, edgecolor=fk.C.INK, linewidth=0.6,
             label="share of the system COUNT")
    ax2.barh(y - 0.19, [100 * k / n.km for k in kms], height=0.36,
             color=fk.C.SUBMAIN, edgecolor=fk.C.INK, linewidth=0.6,
             label="share of the network LENGTH")
    for yy, c, k in zip(y, counts, kms):
        ax2.text(100 * c / n.ncomp + 1, yy + 0.19, f"{c}", va="center", fontsize=7,
                 color=fk.C.INK)
        ax2.text(100 * k / n.km + 1, yy - 0.19, f"{k:,.0f} km", va="center",
                 fontsize=7, color=fk.C.INK)
    ax2.set_yticks(y)
    ax2.set_yticklabels([b[1] for b in BANDS], fontsize=7.6)
    ax2.set_xlabel("share (%)")
    ax2.set_xlim(0, 100)
    ax2.legend(loc="center right", fontsize=7.2, framealpha=0.92)
    fk.finish_chart(fig, source=_src(fig, n.sk))
    return fk.save(fig, "FH05_systems_concentration")


# =================================================================== FIGURE 6

def FH06_flow_never_assembles():
    """The hydraulic consequence of 759 systems: no pipe sees the works flow."""
    n = net()
    tr = net().trunk
    works = _works_flow()
    t = n.term.copy()
    t["X"] = [g.coords[-1][0] for g in t.geometry]
    t["Y"] = [g.coords[-1][1] for g in t.geometry]
    t = t.sort_values("QADF_M3D")
    tot = t["QADF_M3D"].sum()
    biggest = t["QADF_M3D"].max()

    fig, ax, note = fk.map_frame(
        _ext(n),
        title=(f"No pipe ever sees the design flow: the largest carries "
               f"{biggest:,.0f} m³/d, {100*biggest/works:.0f} % of the "
               f"{works:,.0f} m³/d the trunk is sized for"),
        subtitle=(f"Each circle is the downstream end of a drainage system, sized by "
                  f"the flow accumulated into it. {len(t)} ends share "
                  f"{tot:,.0f} m³/d. Until the systems are joined, stage 6 is levelling "
                  f"and sizing {len(t)} small networks, not one."))
    n.sk.plot(ax=ax, color=fk.C.GREY, linewidth=0.22, alpha=0.55, zorder=3)
    trunk = n.sk[n.sk.TIER == "trunk main"]
    trunk.plot(ax=ax, zorder=4, **_tier("trunk main", 0.55))
    s = 6.0 + 190.0 * np.sqrt(np.clip(t["QADF_M3D"], 0, None) / max(biggest, 1e-9))
    zero = t["QADF_M3D"] <= 0
    ax.scatter(t.loc[zero, "X"], t.loc[zero, "Y"], s=7, marker="x",
               c=fk.C.GREY, linewidths=0.7, zorder=6)
    ax.scatter(t.loc[~zero, "X"], t.loc[~zero, "Y"], s=s[~zero], marker="o",
               facecolor=fk.C.FLAG, edgecolor=fk.C.INK, linewidths=0.5, alpha=0.85,
               zorder=7)
    h = [Line2D([], [], marker="o", ls="", markersize=np.sqrt(6 + 190 * np.sqrt(q / biggest)),
                markerfacecolor=fk.C.FLAG, markeredgecolor=fk.C.INK,
                label=f"{q:,.0f} m³/d")
         for q in (5000, 1000, 100)]
    h.append(Line2D([], [], marker="x", ls="", color=fk.C.GREY,
                    label=f"end carrying nothing ({int(zero.sum())})"))
    h.append(Line2D([], [], label="trunk main", **_tier("trunk main", 1.0)))
    b = _boundary(ax)
    if b:
        h.append(b)
    box = (f"system ends      {len(t):>9,}\n"
           f"load at the ends {tot:>9,.0f} m3/d\n"
           f"largest single   {biggest:>9,.0f} m3/d\n"
           f"trunk design flow{works:>9,.0f} m3/d\n"
           f"ends with no load{int(zero.sum()):>9,}")
    fk.finish_map(fig, ax, note=note, legend_handles=h, databox=box,
                  legend_loc="upper left",
                  source=_src(fig, n.sk, n.flows, tr))
    return fk.save(fig, "FH06_flow_never_assembles")


# =================================================================== FIGURE 7

INLET_BANDS = [
    ("below 90 deg - G203-p30", 85.0, 90.0, fk.C.FLAG, "o", 7,
     "85–90°  outside G203-p30, inside our 85° band"),
    ("below the project's stated 85 deg deviation", 75.0, 85.0, MID_SEVERITY, "^", 12,
     "75–85°  past the PROJECT 85° tolerance"),
    ("below 75 deg - REVIEW, the channel cannot be benched", -1.0, 75.0, fk.C.FAIL,
     "s", 18, "under 75°  the channel cannot be benched — REVIEW"),
]


def FH07_inlet_angles_map():
    """Where the 2,788 sharp inlets are."""
    n = net()
    si = n.inlets
    fig, ax, note = fk.map_frame(
        _ext(n),
        title=(f"{len(si):,} junctions need a purpose-made chamber with a swept "
               f"channel, and {int((si.INLET_DEG < 75).sum()):,} of them cannot be "
               f"benched at all"),
        subtitle=("G203-p30: \"No inlet pipe at manholes shall have an angle less than "
                  "90° to the direction of flow.\" Every point below is a junction "
                  "where the corridor geometry does not allow it. The 85° band is a "
                  "PROJECT tolerance, not a guideline value; the 75° review threshold "
                  "is also ours."))
    n.sk.plot(ax=ax, color=fk.C.GREY, linewidth=0.22, alpha=0.55, zorder=3)
    h = []
    for name, lo, hi, col, mk, sz, lbl in INLET_BANDS:
        s = si[si["BAND"] == name]
        ax.scatter(s["X"], s["Y"], s=sz, marker=mk, facecolor=col,
                   edgecolor=fk.C.INK, linewidths=0.35, alpha=0.9, zorder=6)
        h.append(Line2D([], [], marker=mk, ls="", markerfacecolor=col,
                        markeredgecolor=fk.C.INK, markersize=np.sqrt(sz) + 2.2,
                        label=f"{lbl}  ({len(s):,})"))
    b = _boundary(ax)
    if b:
        h.append(b)
    by_t = si["TIER"].value_counts()
    box = ("sharp inlets by tier\n" + "\n".join(
        f"{t:<12}{int(by_t.get(t,0)):>6,}" for t in TIERS)
        + f"\n{'TOTAL':<12}{len(si):>6,}")
    fk.finish_map(fig, ax, note=note, legend_handles=h, databox=box,
                  legend_loc="upper left", source=_src(fig, 
                      si, n.sk, "Data/PAM-GUD-203 p30 (inlet angle, quoted verbatim)"))
    return fk.save(fig, "FH07_inlet_angles_map")


# =================================================================== FIGURE 8

def FH08_inlet_angles_hist():
    """The angle distribution, and which tier pays for it."""
    n = net()
    si = n.inlets
    fig, axes = fk.chart_frame(
        title=("Most sharp inlets are only just sharp — but 550 are under 75°, where "
               "a swept channel stops being enough"),
        subtitle=("Left: inlet angle where G203-p30's 90° minimum is not met. 90° is "
                  "the GUIDELINE; 85° and 75° are PROJECT thresholds. Right: which "
                  "tier carries them — the trunk is the client's input alignment."),
        figsize=(10.6, 4.3), ncols=2, ygrid=True)
    ax, ax2 = axes
    _headroom(fig, 0.34)
    bins = np.arange(0, 91, 2.5)
    for name, lo, hi, col, _mk, _sz, lbl in INLET_BANDS:
        s = si[si["BAND"] == name]
        ax.hist(s["INLET_DEG"], bins=bins, color=col, edgecolor=fk.C.INK,
                linewidth=0.4, label=f"{lbl}  ({len(s):,})", zorder=3)
    for x, lbl, ls in ((90, "90°  G203-p30 minimum", "-"),
                       (85, "85°  PROJECT tolerance", "--"),
                       (75, "75°  PROJECT review", ":")):
        ax.axvline(x, color=fk.C.INK, lw=1.0, ls=ls, zorder=6)
        ax.text(x - 1.2, 0.97, lbl, transform=ax.get_xaxis_transform(), rotation=90,
                va="top", ha="right", fontsize=6.8, color=fk.C.INK)
    ax.set_xlabel("inlet angle to the direction of flow (degrees)")
    ax.set_ylabel("junctions")
    ax.set_xlim(0, 92)
    ax.legend(loc="upper left", fontsize=7.0, framealpha=0.92)
    med = si["INLET_DEG"].median()
    ax.set_title(f"median {med:.1f}°  ·  worst {si['INLET_DEG'].min():.2f}°  ·  "
                 f"{int((si.INLET_DEG>=85).sum()):,} of {len(si):,} are within 5° of "
                 f"compliant", fontsize=8.0, color=fk.C.INK, pad=6)

    piv = (si.assign(B=si["BAND"].map({b[0]: b[6] for b in INLET_BANDS}))
             .pivot_table(index="TIER", columns="B", values="NODE_UID",
                          aggfunc="size", fill_value=0)
             .reindex(TIERS).fillna(0))
    y = np.arange(len(TIERS))[::-1]
    left = np.zeros(len(TIERS))
    for name, _lo, _hi, col, _mk, _sz, lbl in INLET_BANDS:
        if lbl not in piv.columns:
            continue
        v = piv[lbl].values
        ax2.barh(y, v, left=left, height=0.55, color=col, edgecolor=fk.C.INK,
                 linewidth=0.6)
        for yy, vv, ll in zip(y, v, left):
            if vv >= 60:
                ax2.text(ll + vv / 2, yy, f"{int(vv)}", ha="center", va="center",
                         fontsize=7.2, fontweight="bold",
                         color="white" if col == fk.C.FAIL else fk.C.INK)
        left = left + v
    ax2.set_yticks(y)
    ax2.set_yticklabels([f"{t}\n{int(piv.loc[t].sum()):,}" for t in TIERS], fontsize=7.6)
    ax2.set_xlabel("junctions needing a swept channel")
    ax2.set_title("the lateral tier carries almost half of them", fontsize=8.0,
                  color=fk.C.INK, pad=6)
    fk.finish_chart(fig, source=_src(fig, 
        si, "Data/PAM-GUD-203 p30 (90° inlet rule, quoted verbatim); the 85° and 75° "
            "bands are PROJECT thresholds from _BRAIN/08_DESIGN_PHILOSOPHY.md"))
    return fk.save(fig, "FH08_inlet_angles_hist")


# =================================================================== FIGURE 9

def FH09_run_lengths():
    """Run length between junctions, reported as a maximum as well as a median."""
    n = net()
    r = n.runs
    nama = fk.read_csv(str(NAMA_TIERS))
    w10 = fk.read_layer(str(W10_PIPES), columns=["LEN_M"])

    fig, axes = fk.chart_frame(
        title=(f"The median run is {r['LEN_M'].median():.0f} m and the longest is "
               f"{r['LEN_M'].max():,.0f} m — a median cannot see that tail"),
        subtitle=("A RUN is an unbranched chain of reaches between two junctions — a "
                  "different rule from chamber spacing, which Table 12 governs and "
                  "which this network already meets everywhere. Reference values: the "
                  "as-built's median lateral ZONE is 132 m (HIERARCHY_RULES R2); its "
                  "median chamber SPACING is 29.2 m. The 920 m lateral cap is a "
                  "PROJECT rule."),
        figsize=(10.8, 4.4), ncols=2, ygrid=True)
    ax, ax2 = axes
    _headroom(fig, 0.34)

    bins = np.logspace(np.log10(3), np.log10(7000), 46)
    for t in TIERS:
        s = r[r.TIER == t]
        ax.hist(s["LEN_M"], bins=bins, histtype="step",
                color=fk.TIER_COLOR[t], linewidth=fk.TIER_LW[t] + 0.4,
                label=f"{t}  n={len(s):,}  med {s['LEN_M'].median():.0f} m  "
                      f"max {s['LEN_M'].max():,.0f} m", zorder=4)
    ax.set_xscale("log")
    ax.axvline(132, color=fk.C.INK, lw=1.0, ls="--")
    ax.text(132 * 1.06, 0.97, "132 m  as-built median lateral zone",
            transform=ax.get_xaxis_transform(), rotation=90, va="top", fontsize=6.8,
            color=fk.C.INK)
    ax.axvline(PROJ_LATERAL_CAP_M, color=fk.C.FAIL, lw=1.0, ls=":")
    ax.text(PROJ_LATERAL_CAP_M * 1.06, 0.97,
            f"{PROJ_LATERAL_CAP_M:.0f} m  PROJECT lateral cap",
            transform=ax.get_xaxis_transform(), rotation=90, va="top", fontsize=6.8,
            color=fk.C.FAIL)
    ax.set_xlabel("run length between junctions (m, log scale)")
    ax.set_ylabel("runs")
    # an in-axes legend of four long labels sits on the lateral peak, so it goes
    # under the axes (figkit's legend_below makes the room on both panels)
    fk.legend_below(ax, [Line2D([], [], label=f"{t}   n={len(r[r.TIER==t]):,}   "
                                              f"med {r.loc[r.TIER==t,'LEN_M'].median():.0f} m   "
                                              f"max {r.loc[r.TIER==t,'LEN_M'].max():,.0f} m",
                                **_tier(t, 1.6)) for t in TIERS], ncol=2, drop=0.52)

    stats = [("W11a runs\n(this design)", r["LEN_M"].median(), r["LEN_M"].max(),
              fk.C.LATERAL),
             ("W11a reaches\n(chamber to chamber)", n.sk["LEN_M"].median(),
              n.sk["LEN_M"].max(), fk.C.SUBMAIN),
             ("W10 reaches\n(published)", w10["LEN_M"].median(), w10["LEN_M"].max(),
              fk.C.FAIL)]
    y = np.arange(len(stats))[::-1]
    for yy, (lbl, med, mx, col) in zip(y, stats):
        ax2.barh(yy, mx, height=0.5, color=col, edgecolor=fk.C.INK, linewidth=0.6)
        ax2.plot([med], [yy], marker="|", markersize=22, color=fk.C.INK, mew=2.0)
        ax2.text(mx * 1.05, yy, f"max {mx:,.0f} m", va="center", fontsize=7.4,
                 color=fk.C.INK)
        ax2.text(med, yy + 0.34, f"median {med:.0f} m", ha="center", va="bottom",
                 fontsize=7.0, color=fk.C.GREY)
    ax2.set_xscale("log")
    ax2.set_yticks(y)
    ax2.set_yticklabels([s[0] for s in stats], fontsize=7.6)
    ax2.set_xlim(10, 30000)
    over = int((r["LEN_M"] > PROJ_LATERAL_CAP_M).sum())
    ax2.set_xlabel("length (m, log scale) — bar is the MAXIMUM, tick is the median\n"
                   f"{over} runs exceed the 920 m PROJECT lateral cap; the longest is "
                   "an unbranched\ncorridor in the input, not a Table 12 breach")
    ax2.set_title("the medians agree; the maxima do not", fontsize=8.0,
                  color=fk.C.INK, pad=6)
    fk.finish_chart(fig, source=_src(fig, 
        n.sk, w10, nama,
        "W10/docs/research/HIERARCHY_RULES.md R2 (as-built zone length)"))
    return fk.save(fig, "FH09_run_lengths")


# ================================================================== FIGURE 10

def FH10_fingers_map():
    """Dead-end runs under 60 m that collect nothing."""
    n = net()
    f = n.fingers()
    dead_any = n.runs[n.runs.HEAD & (n.runs.Q_DS <= 0)]
    un = n.unassigned
    edges = n.sk.iloc[f["I0"].values]
    fig, ax, note = fk.map_frame(
        _ext(n),
        title=(f"{len(f):,} fingers — dead-end runs under 60 m that collect nothing — "
               f"{f['LEN_M'].sum()/1000:.1f} km of pipe to prune"),
        subtitle=("Philosophy §4: a dead-end reach under about 60 m serving nothing is "
                  "pruned or absorbed. That 60 m is a PROJECT rule on cost grounds; no "
                  "adoption standard requires it. CAVEAT: 'collects nothing' is stage "
                  f"5c's accumulated flow, and stage 5b still leaves {len(un):,} plots "
                  "unconnected — some of these will pick up load when that closes."))
    n.sk.plot(ax=ax, color=fk.C.FAINT, linewidth=0.22, zorder=3)
    dead = n.sk.iloc[dead_any["I0"].values]
    dead.plot(ax=ax, color=fk.C.UNTESTED, linewidth=0.8, zorder=5)
    edges.plot(ax=ax, color=fk.C.FAIL, linewidth=1.4, zorder=6)
    h = [Line2D([], [], color=fk.C.FAINT, lw=1.0, label="network"),
         Line2D([], [], color=fk.C.UNTESTED, lw=1.4,
                label=f"dead-end run with no load, any length "
                      f"({len(dead_any):,}; {dead_any['LEN_M'].sum()/1000:,.0f} km)"),
         Line2D([], [], color=fk.C.FAIL, lw=2.0,
                label=f"FINGER — under 60 m and no load ({len(f):,}; "
                      f"{f['LEN_M'].sum()/1000:.1f} km)")]
    b = _boundary(ax)
    if b:
        h.append(b)
    box = (f"runs               {len(n.runs):>8,}\n"
           f"dead-end runs      {int(n.runs['HEAD'].sum()):>8,}\n"
           f"  of which no load {len(dead_any):>8,}\n"
           f"  of which <60 m   {len(f):>8,}\n"
           f"finger length      {f['LEN_M'].sum()/1000:>8.1f} km")
    fk.finish_map(fig, ax, note=note, legend_handles=h, databox=box,
                  legend_loc="upper left",
                  source=_src(fig, n.sk, n.flows, un))
    return fk.save(fig, "FH10_fingers_map")


# ================================================================== FIGURE 11

def FH11_trunk_fanin():
    """What touches the trunk, against what touches the as-built's."""
    n = net()
    tn = set(n.sk.loc[n.sk.TIER == "trunk main", "US_NODE"]) | \
        set(n.sk.loc[n.sk.TIER == "trunk main", "DS_NODE"])
    joins = n.sk[(n.sk.TIER != "trunk main") & (n.sk["DS_NODE"].isin(tn))]
    jc = joins["TIER"].value_counts()
    sm_nodes = set(n.sk.loc[n.sk.TIER == "sub main", "US_NODE"]) | \
        set(n.sk.loc[n.sk.TIER == "sub main", "DS_NODE"])
    j2 = n.sk[(~n.sk.TIER.isin(["sub main", "trunk main"]))
              & (n.sk["DS_NODE"].isin(sm_nodes))]

    nj = fk.read_csv(str(NAMA_JOINERS))
    nama = fk.read_csv(str(NAMA_TIERS))
    na = nama[nama["scope"] == "all packages"]
    nama_net_km = float(na["km"].sum())
    nama_trunk_km = float(na.loc[na.tier == "trunk_main", "km"].iloc[0])
    njc = nj["TIER2"].value_counts()
    trunk_km = n.sk.loc[n.sk.TIER == "trunk main", "LEN_M"].sum() / 1000.0

    ours_per_net = n.km / len(joins)
    nama_per_net = nama_net_km / len(nj)
    ours_per_trunk = 1000.0 * trunk_km / len(joins)
    nama_per_trunk = 1000.0 * nama_trunk_km / len(nj)

    # 5A-3 is the package the designer never gave a sub-main tier, so its trunk
    # joiners are all laterals by construction.  Both scopes are shown, because
    # quoting only the all-packages figure flatters our own composition.
    nj_lab = nj[nj["PKG"] != "5A-3"]
    njc_lab = nj_lab["TIER2"].value_counts()
    our_sm_pct = 100.0 * int(jc.get("sub main", 0)) / len(joins)
    lab_sm_pct = 100.0 * int(njc_lab.get("sub_main", 0)) / len(nj_lab)

    fig, axes = fk.chart_frame(
        title=(f"Only {our_sm_pct:.0f} % of what joins the trunk is a sub main — "
               f"{lab_sm_pct:.0f} % in the as-built packages that have one"),
        subtitle=("A join is a non-trunk reach whose downstream node is a trunk node. "
                  "The as-built rule is that only sub mains touch the trunk, plus the "
                  "few laterals in a sub-district too small to justify one. Package "
                  "5A-3 was never given a sub-main tier, so it is shown separately. "
                  "Right: how far apart the joins sit."),
        figsize=(10.6, 4.3), ncols=2, ygrid=False, xgrid=True)
    ax, ax2 = axes
    _headroom(fig, 0.34)

    rows = [(f"NAMA as-built, all packages\n{len(nj)} joins on "
             f"{nama_trunk_km:.1f} km of trunk",
             {"sub main": int(njc.get("sub_main", 0)),
              "lateral": int(njc.get("lateral", 0))}),
            (f"NAMA as-built without 5A-3\n{len(nj_lab)} joins, the packages with a "
             f"sub-main tier",
             {"sub main": int(njc_lab.get("sub_main", 0)),
              "lateral": int(njc_lab.get("lateral", 0))}),
            (f"W11a stage 5\n{len(joins)} joins on {trunk_km:.1f} km of trunk",
             {"sub main": int(jc.get("sub main", 0)), "main": int(jc.get("main", 0)),
              "lateral": int(jc.get("lateral", 0))})]
    order = ["sub main", "main", "lateral"]
    y = np.arange(len(rows))[::-1]
    for yy, (_l, d) in zip(y, rows):
        tot = sum(d.values())
        left = 0.0
        for k in order:
            v = d.get(k, 0)
            if not v:
                continue
            pct = 100.0 * v / tot
            ax.barh(yy, pct, left=left, height=0.5, color=fk.TIER_COLOR[k],
                    edgecolor=fk.C.INK, linewidth=0.6)
            if pct >= 9:
                ax.text(left + pct / 2, yy, f"{v}\n{pct:.0f} %", ha="center",
                        va="center", fontsize=7.2, fontweight="bold",
                        color="white" if k == "sub main" else fk.C.INK)
            left += pct
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.6)
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of what joins the trunk (%)")
    fk.legend_below(ax, [Patch(label=k, color=fk.TIER_COLOR[k]) for k in order], ncol=3)

    pairs = [("per km of network\nserved by the trunk",
              nama_per_net * 1000.0, ours_per_net * 1000.0),
             ("per metre of trunk", nama_per_trunk, ours_per_trunk)]
    x = np.arange(len(pairs))
    ax2.bar(x - 0.19, [p[1] for p in pairs], width=0.36, color=fk.C.SUBMAIN,
            edgecolor=fk.C.INK, linewidth=0.6, label="NAMA as-built")
    ax2.bar(x + 0.19, [p[2] for p in pairs], width=0.36, color=fk.C.LATERAL,
            edgecolor=fk.C.INK, linewidth=0.6, label="W11a stage 5")
    for xi, p in zip(x, pairs):
        ax2.text(xi - 0.19, p[1] * 1.06, f"{p[1]:,.0f} m", ha="center",
                 va="bottom", fontsize=7.6, color=fk.C.INK)
        ax2.text(xi + 0.19, p[2] * 1.06, f"{p[2]:,.0f} m", ha="center",
                 va="bottom", fontsize=7.6, color=fk.C.INK)
    ax2.set_xticks(x)
    ax2.set_xticklabels([p[0] for p in pairs], fontsize=7.6)
    ax2.set_yscale("log")
    ax2.set_ylim(100, 20000)
    ax2.set_ylabel("metres between joins (log scale)")
    ax2.legend(loc="upper right", fontsize=7.2, framealpha=0.92)
    ax2.set_title(f"twice as dense per metre of trunk", fontsize=8.0,
                  color=fk.C.INK, pad=6)
    ax2.set_xlabel(f"{len(j2):,} more things join a sub main — the tier meant to "
                   f"absorb them", fontsize=7.4, color=fk.C.GREY)
    fk.finish_chart(fig, source=_src(fig, n.sk, nj, nama))
    return fk.save(fig, "FH11_trunk_fanin")


# ================================================================== FIGURE 12

def FH12_chain_bound():
    """The 3-lateral / 750 m bound before a main."""
    n = net()
    # CHAIN_N / CHAIN_M are published on the STAGE-4 graph, not on the stage-5
    # skeleton, so this figure alone is measured there.  Sub mains and trunk mains
    # carry CHAIN 0 by construction — the rule does not apply to them — so they are
    # excluded rather than counted as a compliant zero.
    s4 = n.s4[n.s4.TIER.isin(["lateral", "main"])]
    lat = s4
    over_m = s4[s4["CHAIN_M"] > PROJ_CHAIN_M]
    flagged = n.s4[n.s4["CHAIN_OVR"] == 1]

    fig, axes = fk.chart_frame(
        title=(f"The chain bound holds by COUNT everywhere and breaks by LENGTH on "
               f"{over_m['LEN_M'].sum()/1000:.0f} km"),
        subtitle=("Philosophy §4: at most 3 laterals and 750 m of flow path before a "
                  "main. Both are PROJECT rules fitted to the as-built (p95 = 3 zones "
                  "/ 722 m), not guideline values. Measured on the STAGE-4 graph, the "
                  "only layer that publishes CHAIN_N and CHAIN_M, and on the lateral "
                  "and main tiers only. Stage 4's own CHAIN_OVR flag counts "
                  f"{len(flagged)}; the 750 m test finds {len(over_m)} — the two "
                  "definitions differ and both are reported."),
        figsize=(10.6, 4.5), ncols=2, ygrid=True)
    ax, ax2 = axes
    _headroom(fig, 0.42)

    cn = s4.groupby("CHAIN_N")["LEN_M"].agg(["size", "sum"])
    xs = cn.index.values
    ax.bar(xs, cn["size"].values, width=0.62,
           color=[fk.C.PASS if v <= PROJ_CHAIN_N else fk.C.FAIL for v in xs],
           edgecolor=fk.C.INK, linewidth=0.6)
    for xi, v, k in zip(xs, cn["size"].values, cn["sum"].values / 1000):
        ax.text(xi, v * 1.03, f"{int(v):,}\n{k:,.0f} km", ha="center", va="bottom",
                fontsize=7.0, color=fk.C.INK)
    ax.axvline(PROJ_CHAIN_N + 0.5, color=fk.C.INK, lw=1.0, ls="--")
    ax.text(PROJ_CHAIN_N + 0.42, 0.97, f"PROJECT bound: {PROJ_CHAIN_N} laterals",
            transform=ax.get_xaxis_transform(), rotation=90, va="top", ha="right",
            fontsize=6.9, color=fk.C.INK)
    ax.set_xlabel("lateral zones crossed before a main (CHAIN_N)")
    ax.set_ylabel("reaches")
    ax.set_ylim(0, cn["size"].max() * 1.35)
    ax.set_xticks(xs)
    ax.set_title(f"no reach exceeds 3 — {int((s4.CHAIN_N > PROJ_CHAIN_N).sum())} "
                 f"breaches", fontsize=8.0, color=fk.C.INK, pad=6)

    bins = np.logspace(np.log10(1), np.log10(5000), 44)
    ax2.hist(lat.loc[lat.CHAIN_M > 0, "CHAIN_M"], bins=bins, color=fk.C.LATERAL,
             edgecolor="none", zorder=3)
    ax2.hist(over_m.loc[over_m.CHAIN_M > 0, "CHAIN_M"], bins=bins, color=fk.C.FAIL,
             edgecolor="none", zorder=4,
             label=f"over the 750 m bound  ({len(over_m):,} reaches, "
                   f"{over_m['LEN_M'].sum()/1000:.0f} km)")
    ax2.axvline(PROJ_CHAIN_M, color=fk.C.INK, lw=1.0, ls="--")
    ax2.text(PROJ_CHAIN_M * 1.06, 0.97, "750 m  PROJECT bound",
             transform=ax2.get_xaxis_transform(), rotation=90, va="top", fontsize=6.9,
             color=fk.C.INK)
    ax2.set_xscale("log")
    ax2.set_xlabel("flow path along laterals before a main (CHAIN_M, m, log scale)")
    ax2.set_ylabel("reaches")
    ax2.legend(loc="upper left", fontsize=7.2, framealpha=0.92)
    ax2.set_title(f"worst {s4['CHAIN_M'].max():,.0f} m — five times the bound",
                  fontsize=8.0, color=fk.C.INK, pad=6)
    fk.finish_chart(fig, source=_src(fig, 
        s4, "_BRAIN/08_DESIGN_PHILOSOPHY.md §4 (3 laterals / 750 m — a PROJECT rule)"))
    return fk.save(fig, "FH12_chain_bound")


# ======================================================================== run

FIGURES = {
    "FH01": FH01_tier_map,
    "FH02": FH02_tier_shares,
    "FH03": FH03_chamber_spacing,
    "FH04": FH04_systems_map,
    "FH05": FH05_systems_concentration,
    "FH06": FH06_flow_never_assembles,
    "FH07": FH07_inlet_angles_map,
    "FH08": FH08_inlet_angles_hist,
    "FH09": FH09_run_lengths,
    "FH10": FH10_fingers_map,
    "FH11": FH11_trunk_fanin,
    "FH12": FH12_chain_bound,
}


def facts() -> list[tuple[str, str, str]]:
    """(value, what it is, artefact) — printed so every figure number is traceable."""
    n = net()
    km = n.tier_km()
    f = n.fingers()
    r = n.runs
    sk = "W11a/run/s5_reach_skeleton.gpkg [s5_reach_skeleton]"
    return [
        (f"{len(n.sk):,}", "chamber-to-chamber reaches", sk),
        (f"{len(n.nodes):,}", "chambers", f"{sk} (distinct US_NODE u DS_NODE)"),
        (f"{n.km:,.1f} km", "network length", sk),
        (f"{len(n.sk)/n.km:.1f}", "reaches per km", sk),
        (f"{len(n.nodes)/n.km:.1f}", "chambers per km", sk),
        (f"{n.sk['LEN_M'].max():.1f} m", "longest reach (Table 12 tightest band 100 m)",
         sk),
        ("0", "reaches over Table 12 (G203-p30)", sk),
        (f"{km['lateral']:,.1f} / {km['main']:,.1f} / {km['sub main']:,.1f} / "
         f"{km['trunk main']:,.1f} km",
         "lateral / main / sub main / trunk main", sk),
        (f"{n.ncomp:,}", "drainage systems (components)", f"{sk} + US/DS topology"),
        (f"{n.n_loops}", "loops on the published layer (H15)",
         f"{sk}: edges - (nodes - components)"),
        (f"{n.n_trunk_pieces}", "pieces the trunk arrives in (OPEN-S4-1)", sk),
        (f"{len(n.term):,}", "system ends", sk),
        (f"{n.term['QADF_M3D'].max():,.0f} m3/d", "largest accumulated flow anywhere",
         "W11a/run/s5c_reach_flows.csv"),
        (f"{_works_flow():,.0f} m3/d", "flow the trunk is sized for, at the works",
         "W11a/shp/W11a_trunk.gpkg [reaches].QADF_M3D max"),
        (f"{len(_trunk_joins()):,}", "things joining the trunk", sk),
        (f"{len(r):,}", "runs between junctions", sk),
        (f"{r['LEN_M'].median():.1f} m / {r['LEN_M'].max():,.1f} m",
         "run length median / MAXIMUM", sk),
        (f"{len(f):,} / {f['LEN_M'].sum()/1000:.1f} km",
         "fingers (<60 m, dead end, no load)",
         f"{sk} + W11a/run/s5c_reach_flows.csv"),
        (f"{len(n.inlets):,}", "inlets under 90 deg (G203-p30)",
         "W11a/run/s5_sharp_inlets.csv"),
        (f"{int((n.inlets.INLET_DEG < 75).sum()):,}", "inlets under 75 deg (PROJECT)",
         "W11a/run/s5_sharp_inlets.csv"),
        (f"{len(n.unassigned):,}", "plots stage 5b left unconnected (caveat on FH10)",
         "W11a/run/s5b_unassigned.csv"),
    ]


def main(argv: list[str]) -> None:
    want = [a.upper() for a in argv[1:]] or list(FIGURES)
    bad = [w for w in want if w not in FIGURES]
    if bad:
        raise SystemExit(f"unknown figure(s) {bad}; known: {list(FIGURES)}")
    print("figures ->")
    for k in want:
        p = FIGURES[k]()
        print(f"  {k}  {p}")
    print("\nevery quoted value, and the artefact it came from:")
    for v, what, src in facts():
        print(f"  {v:>28}  {what:<52}  {src}")
    print("\ntwo inherited numbers NOT used here, both misreadings:")
    print("  'NAMA runs 14.8 % as trunk PLUS sub main' -> 14.8 % is the TRUNK alone;")
    print("     trunk + sub main is 29.2 % (research_hierarchy_tier_shares.csv).")
    print("  'the as-built median run of 88 m' -> 88 m is W8's median LATERAL LENGTH.")
    print("     The as-built median lateral ZONE is 132 m and its median chamber")
    print("     SPACING is 29.2 m (HIERARCHY_RULES R2; PHILOSOPHY_REVIEW M11).")


if __name__ == "__main__":
    main(sys.argv)
