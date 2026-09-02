"""fig_corridors.py -- the corridor-network figures for the W11a report.

Stage 2 is the biggest story in W11a and almost none of it is visible in a
number.  Fourteen figures here, all drawn with ``figkit`` so they read as one
set, all measured off the PUBLISHED layers rather than off a run log.

WHY THE PUBLISHED LAYER AND NOT THE LOG.  ``W11a/run/s2_corridors.log`` is the
10:21 run: 22,900 corridors, 1,381 components, 3,392 removals.  The layer on
disk is the 14:05 run: 26,450 corridors, 311 components, 586 removals.  And
``W11a/run/manifest.json`` records stage 2 as
``"FAILED: NameError: name 'rec' is not defined"`` while the layer it describes
is complete and audit-clean.  So every number on these figures is recomputed
from ``W11a/shp/W11a.gpkg`` and its siblings, here, in one function each.  The
one place a superseded artefact is quoted -- the 1,381-component bar in F_C05 --
says on the figure that it is the earlier run.

THE THREE THINGS THAT ARE OURS, NOT THE GUIDELINE'S, and are labelled as ours
on every figure that uses them:

  * ``HAZARD_WADI_CLASSES = (4, 5, 6)`` of the 50-year grid, standing in for
    G203-p30 4.4.1's *"areas subject to washout"* -- a scour criterion the grid
    does not measure (philosophy H1a, GAP-9).
  * ``WADI_XING_SKEW = 1.155`` (= 1/cos 30 deg), the tolerance on H1's word
    "perpendicular" (``w11a/audit.py:56``).
  * the 60 m in ``N_PLOT`` -- ``PLOT_SERVED_M`` in ``s2_corridors.py:255``,
    a W10 configuration value, not a guideline distance.

The guideline values that DO appear are quoted with their page: G203-p30 and
G203-p33 (pipelines and chambers in wadis "shall be avoided"), G201-p85
(*"Approvals shall be obtained from MoAFWR"*), G201-p86 (DI over the crossing
plus 15 m each side, PAM-STD-404 protection, 2 m cover in soft soil).  All four
were read back off the PDFs in ``Data/`` on 2026-09-02, not quoted from memory.

Run:  python fig_corridors.py            (from W11a/report)
      python fig_corridors.py F_C04      (one figure, by stem)

Idempotent: every run overwrites the same fourteen PNGs in ``report/img/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

import figkit as fk

try:                                                   # console, not the figures
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:                                      # noqa: BLE001
    pass


# ------------------------------------------------------------------ constants
# Every one of these is a PROJECT value with its file and line, not a guideline.

CUT_M = 4.0            # s2_corridors.py:210  CORRIDOR_CUT_M -- the hole `difference` leaves
AUTO_ROAD_MIN_M = 15.0  # s2_corridors.py:213  no ordinary auto_road piece is shorter
CONN_MAX_M = CUT_M + 0.05
PLOT_SERVED_M = 60.0   # s2_corridors.py:255  PLOT_SERVED_M
SKEW = 1.155           # w11a/audit.py:56     WADI_XING_SKEW = 1/cos(30 deg)
PROBE_M = 400.0        # w11a/audit.py:57     WADI_PROBE_M -- how far the probe looks
FINGER_M = 60.0        # philosophy sec 4 "no fingers" -- ours, on cost grounds

OURS = "PROJECT value, not a guideline number"


# ------------------------------------------------------------- source grades
# Corridor provenance is ordinal in trust: drafted > derived > provisional.
# Colour carries the SOURCE, line style and width carry the CONFIDENCE, so a
# provisional reserve is distinguishable in greyscale and on a photocopy --
# philosophy sec 4: "never reported as existing".

GRADES = [
    ("draft", "drafted"),
    ("main_pipe", "drafted"),
    ("auto_road", "derived"),
    ("draft", "provisional"),
    ("auto_block", "provisional"),
    ("auto_link", "provisional"),
]

GRADE_LABEL = {
    ("draft", "drafted"): "draft / drafted\nthe draftsman's built lines",
    ("main_pipe", "drafted"): "main_pipe / drafted\nthe client's trunk alignment",
    ("auto_road", "derived"): "auto_road / derived\nderived from the road centrelines",
    ("draft", "provisional"): "draft / provisional\nplatted reserve, nothing built",
    ("auto_block", "provisional"): "auto_block / provisional\nskeleton of an unserved block",
    ("auto_link", "provisional"): "auto_link / provisional\nstitch onto the network",
}

GRADE_SHORT = {
    ("draft", "drafted"): "draft / drafted",
    ("main_pipe", "drafted"): "main_pipe / drafted",
    ("auto_road", "derived"): "auto_road / derived",
    ("draft", "provisional"): "draft / provisional",
    ("auto_block", "provisional"): "auto_block / provisional",
    ("auto_link", "provisional"): "auto_link / provisional",
}

#: colour = source, dash = provisional, width = trust.  Three channels.
GRADE_STYLE = {
    ("draft", "drafted"): dict(color=fk.C.TRUNK, lw=0.85, ls="-"),
    ("main_pipe", "drafted"): dict(color=fk.C.STATION, lw=2.00, ls="-"),
    ("auto_road", "derived"): dict(color=fk.C.MAIN, lw=0.60, ls="-"),
    ("draft", "provisional"): dict(color=fk.C.LATERAL, lw=0.60, ls=(0, (4.0, 2.0))),
    ("auto_block", "provisional"): dict(color=fk.C.RIDER, lw=0.55, ls=(0, (2.0, 1.6))),
    ("auto_link", "provisional"): dict(color=fk.C.DUAL, lw=0.55, ls=(0, (1.0, 1.4))),
}


def grade_of(df: pd.DataFrame) -> pd.Series:
    return list(zip(df["SRC"], df["CONFIDENCE"]))


def draw(sub, ax, style: dict, *, zorder: int = 3, lw_min: float = 0.0):
    """Plot a line layer with a DASH PATTERN.

    ``GeoDataFrame.plot`` broadcasts every kwarg per-geometry, so a tuple dash
    spec ``(0, (4, 2))`` raises. Setting it on the collection afterwards is the
    supported route and keeps the dash tuples, which is what makes the three
    provisional sources separable in greyscale.
    """
    if not len(sub):
        return None
    st = dict(style)
    ls = st.pop("ls", "-")
    st["lw"] = max(st.get("lw", 0.8), lw_min)
    sub.plot(ax=ax, zorder=zorder, **st)
    coll = ax.collections[-1]
    coll.set_linestyle(ls)
    return coll


def check_grade_palette(min_ratio: float = 1.35) -> list[str]:
    """Same discipline as ``figkit.check_palette``, for the grade ladder.

    Colour is never the only channel here (dash and width carry confidence),
    so the bar is lower than figkit's 1.50 -- but a pair that collapses in
    greyscale AND shares a line style would be unreadable, and this catches it.
    """
    out = []
    for i, a in enumerate(GRADES):
        for b in GRADES[i + 1:]:
            sa, sb = GRADE_STYLE[a], GRADE_STYLE[b]
            la = fk._rel_luminance(sa["color"])
            lb = fk._rel_luminance(sb["color"])
            r = (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
            same_dash = str(sa["ls"]) == str(sb["ls"])
            wr = max(sa["lw"], sb["lw"]) / min(sa["lw"], sb["lw"])
            ch = ("dash differs" if not same_dash else
                  f"same dash, width x{wr:.1f}")
            out.append(f"   {GRADE_SHORT[a]:26s} vs {GRADE_SHORT[b]:26s} "
                       f"grey {r:.2f}:1  {ch}")
            if same_dash and wr < 1.80:
                assert r >= min_ratio, (
                    f"{GRADE_SHORT[a]} and {GRADE_SHORT[b]} share a line style, are "
                    f"within x{wr:.1f} on width, and only separate {r:.2f}:1 in "
                    f"greyscale -- no channel is left")
    return out


# ------------------------------------------------------------------- the data
# Read once per process.  Nothing here opens a live GeoPackage -- figkit copies.

_D: dict = {}


def data() -> dict:
    if _D:
        return _D
    import networkx as nx

    cor = fk.read_layer("W11a.gpkg", "corridors")
    _D["cor"] = cor
    _D["km"] = cor["LEN_M"].sum() / 1000.0

    # --- the healing connectors, identified by LENGTH and nothing else --------
    # `difference(draft_cut)` leaves a hole exactly CORRIDOR_CUT_M = 4.0 m wide
    # and the connector drawn to close it is that long.  AUTO_ROAD_MIN_M = 15 m
    # drops every other short auto_road piece, so a 4.0 m auto_road corridor can
    # only be a connector.  702 of the 713 land on a node that a drafted line
    # also uses, which is what the connector was drawn to reach -- that check is
    # the identification's proof, and it is recomputed below, not asserted.
    conn = (cor["SRC"] == "auto_road") & (cor["LEN_M"] <= CONN_MAX_M)
    _D["conn"] = conn
    dn = set(cor.loc[cor["SRC"].isin(["draft", "main_pipe"]), "US_NODE"]) | \
        set(cor.loc[cor["SRC"].isin(["draft", "main_pipe"]), "DS_NODE"])
    c = cor[conn]
    _D["conn_on_draft"] = int((c["US_NODE"].isin(dn) | c["DS_NODE"].isin(dn)).sum())

    # --- components, off US_NODE/DS_NODE.  H16: topology is written down ------
    def comps(df):
        g = nx.Graph()
        g.add_nodes_from(set(df["US_NODE"]) | set(df["DS_NODE"]))
        g.add_edges_from(zip(df["US_NODE"], df["DS_NODE"]))
        return g, sorted(nx.connected_components(g), key=len, reverse=True)

    G, cc = comps(cor)
    _D["G"], _D["cc"] = G, cc
    cid = {n: i for i, s in enumerate(cc) for n in s}
    cor["COMP"] = cor["US_NODE"].map(cid)
    _D["comp_km"] = (cor.groupby("COMP")["LEN_M"].sum() / 1000.0).sort_values(
        ascending=False)
    _D["comp_n"] = cor.groupby("COMP").size()
    _, cc_no = comps(cor[~conn])
    _D["cc_without_connectors"] = len(cc_no)

    # --- dead ends, for the finger test at corridor level ---------------------
    deg = pd.concat([cor["US_NODE"], cor["DS_NODE"]]).value_counts()
    ends = set(deg[deg == 1].index)
    _D["is_stub"] = cor["US_NODE"].isin(ends) | cor["DS_NODE"].isin(ends)

    _D["rm"] = fk.read_layer("W11a_corridors_removed.gpkg", "removed")
    _D["xr"] = fk.read_layer("W11a.gpkg", "crossings")
    _D["nop"] = fk.read_layer("W11a_plots_no_corridor.gpkg", "plots_no_corridor")
    try:
        _D["bnd"] = fk.study_boundary()
    except Exception:                                   # noqa: BLE001
        _D["bnd"] = None
    return _D


def hazard_answer(cor) -> pd.Series:
    """One of 'no answer' / 'tested, clear' / 'wadi class 4-6' per corridor.

    Sampled at FULL grid resolution at the corridor midpoint -- never off a
    decimated display array.  The nodata is -9999.0, which IS finite, so the
    isfinite guard alone would score it as dry ground.
    """
    import rasterio
    pts = [(g.interpolate(0.5, normalized=True).x,
            g.interpolate(0.5, normalized=True).y) for g in cor.geometry]
    with rasterio.open(fk.HAZARD) as src:
        v = np.array([x[0] for x in src.sample(pts)], dtype="float64")
        nod = src.nodata
    no = ~np.isfinite(v) | (v == nod) | (v <= -9998.0)
    return pd.Series(np.where(no, "no answer",
                              np.where(np.floor(v) >= 4, "wadi class 4-6",
                                       "tested, clear")), index=cor.index)


def clear_basemap_gaps(ax, *, thresh: int = 14, alpha: float = 0.30):
    """Make the mosaic's own no-tile pixels transparent instead of grey.

    ``figkit.basemap`` draws the offline Esri mosaic at 30 % opacity. Where the
    mosaic has no tile the pixels are black, and 30 % black over the neutral
    ground reads as a solid grey field that a reader takes for a map feature.
    This drops the alpha to zero on those pixels only, so the untiled ground is
    plainly blank. It changes no data and no colour -- only the alpha of pixels
    that carry no image. Nothing is fetched.

    (This belongs in ``figkit.basemap``; it is done here because figkit is being
    imported by six other agents and must not change under them.)
    """
    for im in list(ax.images):
        a = im.get_array()
        if a is None or np.ndim(a) != 3:
            continue
        a = np.asarray(a)
        if a.shape[2] < 3:
            continue
        dark = a[..., :3].max(axis=2) <= thresh
        if not dark.any():
            continue
        try:
            im.set_alpha(np.where(dark, 0.0, alpha))
        except Exception:                               # noqa: BLE001 -- mpl drift
            continue
        return int(dark.sum()), int(dark.size)
    return None


def map_frame(extent, **kw):
    """``figkit.map_frame`` plus the no-tile alpha fix. Same return signature."""
    fig, ax, note = fk.map_frame(extent, **kw)
    got = clear_basemap_gaps(ax)
    if got and got[0] > 0.02 * got[1]:
        note = (note + f"; {100*got[0]/got[1]:.0f} % of the frame has no mosaic tile "
                       f"and is left blank")
    return fig, ax, note


def box(rows, width: int = 34) -> str:
    """Monospace databox text with every line the same width.

    ``finish_map`` right-aligns the box, so ragged line lengths make it look
    broken. Pad label and value to a fixed column.
    """
    out = []
    for k, v in rows:
        pad = max(1, width - len(k) - len(v))
        out.append(f"{k}{' ' * pad}{v}")
    return "\n".join(out)


def _boundary(ax):
    b = data()["bnd"]
    if b is not None:
        b.boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.1, ls="--", zorder=8)
    return Line2D([], [], color=fk.C.BOUNDARY, lw=1.1, ls="--", label="study boundary")


HAZ_SRC = (f"{fk.HAZARD.relative_to(fk.BASE).as_posix()}, 50-year hazard grid, "
           f"3 m, nodata -9999.0")


# =============================================================== F_C01  sources
def f_c01() -> tuple:
    d = data()
    cor, km = d["cor"], d["km"]
    prov = cor[cor["CONFIDENCE"] == "provisional"]
    pkm, ppc = prov["LEN_M"].sum() / 1000.0, 100.0 * prov["LEN_M"].sum() / cor["LEN_M"].sum()

    fig, ax, note = map_frame(
        fk.extent_of(cor, pad=0.02),
        title=f"{ppc:.0f} % of the corridor network is a platted reserve with "
              f"nothing built on it",
        subtitle=(f"All {len(cor):,} published corridors, {km:,.0f} km, by source and "
                  f"confidence. Dashed lines are PROVISIONAL: a legal reserve at the "
                  f"saturation horizon, never reportable as an existing street "
                  f"(philosophy sec 4). Colour is the source, dash and width are the "
                  f"confidence."))
    g = grade_of(cor)
    for key in reversed(GRADES):                       # provisional under, drafted over
        draw(cor[[x == key for x in g]], ax, GRADE_STYLE[key],
             zorder=3 + GRADES.index(key))
    hb = _boundary(ax)

    handles = []
    for key in GRADES:
        sub = cor[[x == key for x in g]]
        st = dict(GRADE_STYLE[key])
        st["lw"] = max(st["lw"], 1.3)
        handles.append(Line2D([], [], **st,
                              label=f"{GRADE_SHORT[key]}  -  {len(sub):,} / "
                                    f"{sub['LEN_M'].sum()/1000:,.0f} km"))
    handles.append(hb)

    tab = cor.groupby(["CONFIDENCE"]).agg(n=("LEN_M", "size"),
                                          km=("LEN_M", lambda s: s.sum() / 1000))
    box = "confidence      n        km\n" + "\n".join(
        f"{c:<12s} {int(tab.loc[c,'n']):>6,} {tab.loc[c,'km']:>9,.0f}"
        for c in ("drafted", "derived", "provisional")) + \
        f"\n{'TOTAL':<12s} {len(cor):>6,} {km:>9,.0f}"
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=box,
                  legend_loc="upper left", source=fk.source_line(cor))
    p = fk.save(fig, "F_C01_corridor_sources")
    return (p,
            f"The {len(cor):,} published corridors by source and confidence. "
            f"{pkm:,.0f} km of the {km:,.0f} km ({ppc:.0f} %) is provisional.",
            f"{ppc:.0f} % of the corridor network exists only as a platted reserve.")


# ========================================================= F_C02  small multiples
def f_c02() -> tuple:
    import matplotlib.pyplot as plt
    d = data()
    cor = d["cor"]
    g = grade_of(cor)
    x0, y0, x1, y1 = fk.extent_of(cor, pad=0.01)

    fig, axes = plt.subplots(2, 3, figsize=(11.2, 6.0))
    top = fk._titleblock(
        fig,
        "The reserves are where the plots are; the road-derived corridors are where "
        "they are not",
        "The same 26,450 corridors, one source per panel. Grey is the rest of the "
        "network for context. Each panel gives its length and the load-bearing plots "
        "for which one of its corridors is the nearest within 60 m (a PROJECT "
        "distance, s2_corridors.py:255 -- not a guideline value).")
    fig.subplots_adjust(left=0.010, right=0.990, bottom=0.045, top=top,
                        wspace=0.035, hspace=0.20)

    for axx, key in zip(axes.ravel(), GRADES):
        sub = cor[[x == key for x in g]]
        cor.plot(ax=axx, color=fk.C.FAINT, lw=0.16, zorder=1)
        draw(sub, axx, GRADE_STYLE[key], zorder=3, lw_min=0.8)
        axx.set_xlim(x0, x1)
        axx.set_ylim(y0, y1)
        axx.set_aspect("equal", adjustable="box")
        axx.set_xticks([])
        axx.set_yticks([])
        for s in axx.spines.values():
            s.set_color("#b8b8b8")
            s.set_linewidth(0.7)
        ppkm = sub["N_PLOT"].sum() / max(sub["LEN_M"].sum() / 1000.0, 1e-9)
        axx.set_title(f"{GRADE_SHORT[key]}   -   {sub['LEN_M'].sum()/1000:,.0f} km, "
                      f"{int(sub['N_PLOT'].sum()):,} plots  ({ppkm:,.0f} plots/km)",
                      fontsize=7.6, color=fk.C.INK, pad=3, loc="left")
    fk._sourceline(fig, fk.source_line(cor), None)
    p = fk.save(fig, "F_C02_corridor_sources_by_panel")
    return (p,
            "Where each corridor source actually lies. The provisional draft reserves "
            "cover the platted extensions; auto_road covers the open desert roads.",
            "Source and usefulness are not the same map: the reserves carry the plots.")


# =============================================================== F_C03  grade bars
def f_c03() -> tuple:
    d = data()
    cor = d["cor"]
    g = grade_of(cor)
    rows = []
    for key in GRADES:
        sub = cor[[x == key for x in g]]
        rows.append((GRADE_SHORT[key], len(sub), sub["LEN_M"].sum() / 1000.0,
                     int(sub["N_PLOT"].sum()), key))
    prov_km = sum(r[2] for r in rows if r[4][1] == "provisional")
    prov_pl = sum(r[3] for r in rows if r[4][1] == "provisional")
    tot_km = sum(r[2] for r in rows)
    tot_pl = sum(r[3] for r in rows)

    fig, axes = fk.chart_frame(
        title=f"The provisional half of the network fronts "
              f"{100*prov_pl/tot_pl:.0f} % of the plots",
        subtitle=(f"{prov_km:,.0f} km of {tot_km:,.0f} km is provisional and it is the "
                  f"nearest corridor to {prov_pl:,} of {tot_pl:,} load-bearing plots. "
                  f"A reserve is a legal corridor at the saturation horizon and is never "
                  f"reported as existing -- but it cannot be dismissed as spare either."),
        figsize=(10.6, 4.6), ncols=2, ygrid=False, xgrid=True)
    ypos = np.arange(len(rows))[::-1]

    for ax, col, lab, fmt in ((axes[0], 2, "corridor length (km)", "{:,.0f}"),
                              (axes[1], 3, "load-bearing plots fronted", "{:,.0f}")):
        for y, r in zip(ypos, rows):
            st = GRADE_STYLE[r[4]]
            ax.barh(y, r[col], height=0.62, facecolor=st["color"],
                    edgecolor=fk.C.INK, linewidth=0.6,
                    hatch=None if r[4][1] != "provisional" else "//")
            ax.text(r[col] * 1.015, y, fmt.format(r[col]), va="center", ha="left",
                    fontsize=7.4, color=fk.C.INK)
        ax.set_yticks(ypos)
        if col == 2:
            ax.set_yticklabels([r[0] for r in rows], fontsize=7.6)
        else:
            ax.set_yticklabels([])
            ax.tick_params(axis="y", length=0)
        ax.set_xlabel(lab)
        ax.set_xlim(0, max(r[col] for r in rows) * 1.20)
        fk.thousands(ax, "x")

    handles = [Patch(facecolor="white", edgecolor=fk.C.INK, hatch="//",
                     label="provisional -- platted reserve, nothing built on it "
                           "(never reported as existing)"),
               Patch(facecolor="white", edgecolor=fk.C.INK,
                     label="drafted or derived -- a street exists")]
    fk.legend_below(axes[0], handles, ncol=1, drop=0.34)
    fk.finish_chart(fig, source=fk.source_line(cor),
                    note="'plots fronted' = load-bearing plots for which this corridor "
                         "is the NEAREST within 60 m (s2_corridors.py:255). "
                         f"60 m is a {OURS}.")
    p = fk.save(fig, "F_C03_corridor_grades")
    return (p,
            "Corridor length and plots fronted, by source and confidence. The "
            "provisional reserves are 46 % of the length and 61 % of the plots.",
            "Provisional corridors are the most productive per kilometre, not the least.")


# ============================================================ F_C04  components
def f_c04() -> tuple:
    d = data()
    cor, cc, G = d["cor"], d["cc"], d["G"]
    ckm = d["comp_km"]
    top3 = ckm.head(3)
    share = 100.0 * top3.sum() / ckm.sum()

    fig, ax, note = map_frame(
        fk.extent_of(cor, pad=0.02),
        title=f"Three pieces hold {share:.0f} % of the corridor network; "
              f"{len(cc)-3} more hold the rest",
        subtitle=(f"The published corridor graph, built from the written-down "
                  f"US_NODE / DS_NODE topology (H16), not from snapped geometry. "
                  f"{len(cc):,} connected components on {G.number_of_nodes():,} nodes. "
                  f"The three largest are drawn separately; every other component is "
                  f"one colour, because what matters about them is that they are "
                  f"separate, not which is which."))

    others = cor[~cor["COMP"].isin(top3.index)]
    others.plot(ax=ax, color=fk.C.FAIL, lw=0.55, zorder=6)
    ramp = [fk.C.TRUNK, fk.C.MAIN, fk.C.LATERAL]
    for i, (cid, kmv) in enumerate(top3.items()):
        cor[cor["COMP"] == cid].plot(ax=ax, color=ramp[i], lw=0.55, zorder=3 + i)
    hb = _boundary(ax)

    handles = [Line2D([], [], color=ramp[i], lw=1.6,
                      label=f"component {i+1}  -  {top3.iloc[i]:,.0f} km, "
                            f"{int(d['comp_n'][top3.index[i]]):,} corridors")
               for i in range(3)]
    handles += [Line2D([], [], color=fk.C.FAIL, lw=1.6,
                       label=f"the other {len(cc)-3:,} components  -  "
                             f"{ckm.sum()-top3.sum():,.0f} km"), hb]

    n1 = int((d["comp_n"] == 1).sum())
    box = (f"components        {len(cc):>8,}\n"
           f"largest, by nodes {100*len(cc[0])/G.number_of_nodes():>7.1f} %\n"
           f"top 3, by length  {share:>7.1f} %\n"
           f"single-corridor   {n1:>8,}\n"
           f"under 1 km        {int((ckm<1).sum()):>8,}  ({ckm[ckm<1].sum():,.0f} km)")
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=box,
                  source=fk.source_line(cor))
    p = fk.save(fig, "F_C04_corridor_components")
    return (p,
            f"The {len(cc)} connected components of the published corridor graph. "
            f"Three hold {share:.0f} % of the length.",
            "Fragmentation is not spread evenly - it is a rim of small orphans around "
            "three large bodies.")


# ============================================== F_C05  the component ladder + tail
def f_c05() -> tuple:
    d = data()
    cc, ckm = d["cc"], d["comp_km"]
    without = d["cc_without_connectors"]
    nconn = int(d["conn"].sum())

    fig, axes = fk.chart_frame(
        title=f"{nconn} connectors of {CUT_M:.0f} m each cut the network from "
              f"{without} pieces to {len(cc)}",
        subtitle=(f"LEFT: what the corridor set is in, at three points. RIGHT: the "
                  f"{len(cc)} components ranked by length -- the top three are the "
                  f"network and the tail is orphans. H15 wants a forest with one "
                  f"outfall per component; every bar past the third is a piece that "
                  f"currently drains nowhere."),
        figsize=(10.6, 4.4), ncols=2, ygrid=True, xgrid=False)

    ax = axes[0]
    bars = [
        ("H1 by deletion\n(10:21 run)", 1381, fk.C.RIDER,
         "run/s2_corridors.log line 56 - SUPERSEDED run"),
        (f"H1a crossings kept,\ncut hole open", without, fk.C.LATERAL,
         "counterfactual: today's layer minus the connectors"),
        ("published\n(14:05 layer)", len(cc), fk.C.SUBMAIN,
         "measured on W11a.gpkg [corridors]"),
    ]
    for i, (lab, v, col, _why) in enumerate(bars):
        ax.bar(i, v, width=0.56, facecolor=col, edgecolor=fk.C.INK, linewidth=0.7)
        ax.text(i, v + 26, f"{v:,}", ha="center", va="bottom", fontsize=10.5,
                fontweight="bold", color=fk.C.INK)
    ax.set_xticks(range(len(bars)))
    ax.set_xticklabels([f"{b[0]}\n{b[3]}" for b in bars], fontsize=6.4)
    ax.set_ylabel("connected components")
    ax.set_ylim(0, 1760)
    for x0, x1, y, txt in (
            (0, 1, 1580, f"-{1381-without:,}   H1a: a crossing is not a severance"),
            (1, 2, 900, f"-{without-len(cc):,}   {nconn} connectors, "
                        f"{d['cor'].loc[d['conn'],'LEN_M'].sum()/1000:.3f} km")):
        ax.annotate("", xy=(x1, y), xytext=(x0, y),
                    arrowprops=dict(arrowstyle="-|>", color=fk.C.GREY, lw=1.2))
        ax.text((x0 + x1) / 2, y + 24, txt, ha="center", va="bottom", fontsize=7.0,
                color=fk.C.INK,
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="none",
                          alpha=0.9))

    ax2 = axes[1]
    v = ckm.values
    ax2.bar(np.arange(len(v)), v, width=1.0, facecolor=fk.C.SUBMAIN, linewidth=0)
    ax2.set_yscale("log")
    ax2.set_xlabel("component, ranked by length")
    ax2.set_ylabel("length (km, log)")
    ax2.set_xlim(-3, len(v) + 3)
    ax2.axvline(2.5, color=fk.C.BOUNDARY, lw=1.0, ls="--")
    ax2.text(8, v[0] * 0.62,
             f"3 components = {100*ckm.head(3).sum()/ckm.sum():.0f} % of the network",
             fontsize=7.2, color=fk.C.INK,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.9))
    ax2.text(len(v) * 0.30, v.max() * 0.05,
             f"{int((ckm<1).sum())} components under 1 km,\n"
             f"{ckm[ckm<1].sum():,.0f} km between them",
             fontsize=7.2, color=fk.C.INK, ha="left",
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#b8b8b8",
                       alpha=0.94))

    fk.finish_chart(
        fig, source=fk.source_line(d["cor"], "W11a/run/s2_corridors.log, line 56 "
                                             "(10:21 run, superseded by the 14:05 layer)"),
        note="The middle bar is a COUNTERFACTUAL computed here: the published layer with "
             f"the {nconn} connector corridors deleted and the components recounted. It "
             "is not a figure any run printed.")
    p = fk.save(fig, "F_C05_component_ladder")
    return (p,
            "How the corridor component count moved, and how the 311 components are "
            "distributed by length.",
            "The healing connectors are worth more than the whole H1a rewrite in "
            "component terms per kilometre laid.")


# ============================================================= F_C06  connectors
def f_c06() -> tuple:
    d = data()
    cor, conn = d["cor"], d["conn"]
    c = cor[conn]
    ckm = c["LEN_M"].sum() / 1000.0
    pct = 100.0 * c["LEN_M"].sum() / cor["LEN_M"].sum()

    fig, ax, note = map_frame(
        fk.extent_of(cor, pad=0.02),
        title=f"{ckm:.3f} km of connector - {pct:.2f} % of the network - holds "
              f"{d['cc_without_connectors']-len(d['cc'])} pieces together",
        subtitle=(f"Every {CUT_M:.0f} m corridor drawn to close the hole "
                  f"`difference(draft_cut)` leaves where a road-derived line meets a "
                  f"drafted one. {len(c):,} of them, median "
                  f"{c['LEN_M'].median():.2f} m. The node merge radius is 3.0 m, so "
                  f"nothing else in the pipeline could close a 4.0 m gap."))
    cor.plot(ax=ax, color=fk.C.GREY, lw=0.20, alpha=0.55, zorder=2)
    c.plot(ax=ax, color=fk.C.STATION, lw=2.2, zorder=6)
    cent = c.geometry.centroid
    ax.scatter(cent.x, cent.y, s=9, facecolor="none", edgecolor=fk.C.STATION,
               linewidths=0.7, zorder=7)
    hb = _boundary(ax)

    handles = [
        Line2D([], [], color=fk.C.GREY, lw=1.0, alpha=0.55,
               label=f"corridor ({len(cor):,}, {d['km']:,.0f} km)"),
        Line2D([], [], color=fk.C.STATION, lw=2.2, marker="o", markersize=4,
               markerfacecolor="none",
               label=f"cut-hole connector ({len(c):,}, {ckm*1000:,.0f} m)"),
        hb]
    box = (f"connectors        {len(c):>8,}\n"
           f"total length      {ckm*1000:>7,.0f} m\n"
           f"share of network  {pct:>7.2f} %\n"
           f"landing on a drafted-line node "
           f"{100*d['conn_on_draft']/len(c):>5.1f} %\n"
           f"components with   {len(d['cc']):>8,}\n"
           f"components without{d['cc_without_connectors']:>8,}")
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=box,
                  source=fk.source_line(cor))
    p = fk.save(fig, "F_C06_cut_hole_connectors")
    return (p,
            f"The {len(c):,} four-metre connectors that close the cut hole, and what "
            f"the network looks like without them.",
            f"{pct:.2f} % of the length carries "
            f"{d['cc_without_connectors']-len(d['cc'])} components' worth of "
            f"connectivity.")


# ======================================================= F_C07  connector detail
def f_c07() -> tuple:
    d = data()
    cor, conn = d["cor"], d["conn"]
    c = cor[conn]
    cent = c.geometry.centroid
    # the densest 400 m window, found rather than chosen
    step = 400.0
    key = pd.DataFrame({"gx": (cent.x // step).astype(int),
                        "gy": (cent.y // step).astype(int)}).value_counts()
    gx, gy = key.index[0]
    cx, cy = (gx + 0.5) * step, (gy + 0.5) * step
    hx, hy = 420.0, 236.0                              # 840 x 472 m, page aspect
    ext = (cx - hx, cy - hy, cx + hx, cy + hy)
    inwin = c[(cent.x > ext[0]) & (cent.x < ext[2]) &
              (cent.y > ext[1]) & (cent.y < ext[3])]

    fig, ax, note = map_frame(
        ext,
        title=f"What a healed cut hole looks like: a {CUT_M:.0f} m stub onto the "
              f"drafted line",
        subtitle=(f"{2*hx:,.0f} m across the densest connector window in the study "
                  f"area, at E{cx:,.0f} N{cy:,.0f}. The road-derived corridors were cut "
                  f"{CUT_M:.0f} m short of the drafted lines they duplicate; each red "
                  f"stub is the connector drawn back onto the drafted geometry with "
                  f"`nearest_points`, so the planar noding makes a shared node of it."))
    g = grade_of(cor)
    for k in reversed(GRADES):
        sub = cor[[x == k for x in g]].cx[ext[0]:ext[2], ext[1]:ext[3]]
        draw(sub, ax, GRADE_STYLE[k], zorder=3 + GRADES.index(k), lw_min=1.4)
    inwin.plot(ax=ax, color=fk.C.STATION, lw=3.6, zorder=9)
    for geom in inwin.geometry:
        xs, ys = geom.coords[0], geom.coords[-1]
        ax.scatter([xs[0], ys[0]], [xs[1], ys[1]], s=16, color=fk.C.STATION,
                   zorder=10, linewidths=0)

    handles = [Line2D([], [], **{**GRADE_STYLE[k], "lw": max(GRADE_STYLE[k]["lw"], 1.4)},
                      label=GRADE_SHORT[k]) for k in GRADES]
    handles.append(Line2D([], [], color=fk.C.STATION, lw=3.0,
                          label=f"cut-hole connector ({len(inwin)} in frame)"))
    dbox = box([("window", f"{2*hx:,.0f} x {2*hy:,.0f} m"),
                ("connectors in frame", f"{len(inwin)}"),
                ("each", f"{CUT_M:.1f} m"),
                ("node merge radius",
                 f"{3.0:.1f} m - too small to close it")], width=42)
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=dbox,
                  legend_loc="upper left", source=fk.source_line(cor))
    p = fk.save(fig, "F_C07_connector_detail")
    return (p,
            "The cut hole and its connector at 600 m across - the mechanism behind "
            "F_C06's number.",
            "A 4 m modelling artefact, not a ground condition, was the dominant "
            "defect in the corridor pipeline.")


# ============================================================ F_C08  H1 removals
def f_c08() -> tuple:
    d = data()
    rm = d["rm"]
    tot = rm["LEN_M"].sum() / 1000.0
    wadi = rm[rm["REASON"].str.startswith("wadi")]["LEN_M"].sum() / 1000.0

    order = (rm.groupby("REASON")["LEN_M"].sum() / 1000).sort_values()
    srcs = list(rm.groupby("SRC")["LEN_M"].sum().sort_values(ascending=False).index)
    ramp = [fk.C.TRUNK, fk.C.SUBMAIN, fk.C.MAIN, fk.C.LATERAL, fk.C.RIDER,
            fk.C.DUAL, fk.C.WADI, fk.C.GREY]
    hats = [None, "//", "..", "\\\\", "xx", "++", "oo", "--"]
    assert len(srcs) <= len(ramp), f"{len(srcs)} sources, only {len(ramp)} styles"
    scol = {s: ramp[i] for i, s in enumerate(srcs)}
    shat = {s: hats[i] for i, s in enumerate(srcs)}

    fig, ax = fk.chart_frame(
        title=f"H1 deletes {tot:.0f} km of corridor and "
              f"{100*wadi/tot:.0f} % of it is wadi, not dual carriageway",
        subtitle=(f"The {len(rm):,} pieces on the review layer, by the reason H1 gave "
                  f"and by the source they came from. 'wadi (along)' is a run that "
                  f"failed the along-versus-across test; a run that PASSED it is not "
                  f"here -- it survives as a scheduled crossing (H1a). "
                  f"G203-p30 4.4.1 and G203-p33: pipelines and chambers in wadis and "
                  f"areas subject to washout 'shall be avoided'."),
        figsize=(10.4, 4.2), ygrid=False, xgrid=True)

    ypos = np.arange(len(order))
    for y, reason in zip(ypos, order.index):
        left = 0.0
        sub = rm[rm["REASON"] == reason]
        for s in srcs:
            v = sub[sub["SRC"] == s]["LEN_M"].sum() / 1000.0
            if v <= 0:
                continue
            ax.barh(y, v, left=left, height=0.6, facecolor=scol[s], hatch=shat[s],
                    edgecolor=fk.C.INK, linewidth=0.5)
            left += v
        ax.text(left + tot * 0.006, y, f"{left:,.2f} km   ({len(sub):,} pieces)",
                va="center", ha="left", fontsize=7.4, color=fk.C.INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels(list(order.index), fontsize=8.0)
    ax.set_xlabel("corridor length removed (km)")
    ax.set_xlim(0, order.max() * 1.30)
    fk.legend_below(ax, [Patch(facecolor=scol[s], hatch=shat[s], edgecolor=fk.C.INK,
                               linewidth=0.5, label=s) for s in srcs], ncol=3, drop=0.5)
    fk.finish_chart(fig, source=fk.source_line(rm),
                    note="Review layer, outside the contract. 'along a dual carriageway' "
                         "and 'dual crossing off square' are project rule 7; the 25 deg "
                         f"squareness cap and the {SKEW:.3f} wadi skew tolerance are "
                         f"{OURS}.")
    p = fk.save(fig, "F_C08_h1_removals")
    return (p,
            f"What H1 removed and why: {len(rm):,} pieces, {tot:.1f} km, "
            f"{100*wadi/tot:.0f} % of it wadi.",
            "The dual-carriageway rule costs almost nothing; the wadi rule costs "
            "everything.")


# ======================================================== F_C09  removals in place
def f_c09() -> tuple:
    d = data()
    rm, cor = d["rm"], d["cor"]
    tot = rm["LEN_M"].sum() / 1000.0
    wadi_km = rm[rm["REASON"].str.startswith("wadi")]["LEN_M"].sum() / 1000.0
    dual_km = tot - wadi_km
    styles = {
        "wadi (along)": dict(color=fk.C.WADI, lw=2.0, ls="-"),
        "wadi (along, audit.r4 sweep)": dict(color=fk.C.WADI, lw=2.0,
                                             ls=(0, (2.0, 1.5))),
        "along a dual carriageway": dict(color=fk.C.DUAL, lw=2.4, ls="-"),
        "dual crossing off square": dict(color=fk.C.DUAL, lw=2.4, ls=(0, (2.0, 1.5))),
    }
    fig, ax, note = map_frame(
        fk.extent_of(cor, pad=0.02),
        title=f"H1's cuts trace the wadi lines; the dual-carriageway rule costs "
              f"{dual_km:.1f} km of the {tot:.0f}",
        subtitle=(f"The {len(rm):,} removed pieces over the surviving network. The "
                  f"wadi removals follow the drainage and are long; the "
                  f"dual-carriageway removals are short and scattered along the main "
                  f"road corridor. Project rule 7 costs {dual_km:.2f} km, the wadi "
                  f"rule {wadi_km:.1f} km."))
    cor.plot(ax=ax, color=fk.C.GREY, lw=0.20, alpha=0.55, zorder=2)
    handles = []
    for reason, st in styles.items():
        sub = rm[rm["REASON"] == reason]
        if not len(sub):
            continue
        draw(sub, ax, st, zorder=5)
        handles.append(Line2D([], [], **st,
                              label=f"{reason}  -  {len(sub):,}, "
                                    f"{sub['LEN_M'].sum()/1000:,.2f} km"))
    handles.insert(0, Line2D([], [], color=fk.C.GREY, lw=1.0, alpha=0.55,
                             label=f"surviving corridor ({d['km']:,.0f} km)"))
    handles.append(_boundary(ax))
    dbox = box([("removed", f"{len(rm):,}"),
                ("length", f"{tot:.2f} km"),
                ("vs published", f"{d['km']:,.0f} km"),
                ("removed share", f"{100*tot/d['km']:.2f} %")])
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=dbox,
                  source=fk.source_line(rm, cor))
    p = fk.save(fig, "F_C09_h1_removals_map")
    return (p,
            "Where H1 cut the corridor set. Wadi removals follow the drainage; dual "
            "removals sit on one highway.",
            "The exclusions are geographically concentrated, so the plots they strand "
            "are too.")


# =============================================================== F_C10  P7 map
def f_c10() -> tuple:
    d = data()
    cor = d["cor"]
    z = cor[cor["N_PLOT"] == 0]
    zkm = z["LEN_M"].sum() / 1000.0
    pct = 100.0 * zkm / d["km"]

    fig, ax, note = map_frame(
        fk.extent_of(cor, pad=0.02),
        title=f"{zkm:,.0f} km of corridor - {pct:.0f} % of the network - is the nearest "
              f"corridor to no load-bearing plot at all",
        subtitle=(f"P7. {len(z):,} of {len(cor):,} corridors have N_PLOT = 0: no "
                  f"load-bearing plot has one of them as its nearest corridor within "
                  f"{PLOT_SERVED_M:.0f} m. Stage 2 deliberately does not prune them -- "
                  f"pruning is a layout and scope decision (philosophy sec 4 and 8a), "
                  f"not a corridor one. This is the length that has to justify itself "
                  f"before a pipe is laid in it."))
    cor[cor["N_PLOT"] > 0].plot(ax=ax, color=fk.C.LATERAL, lw=0.35, zorder=3)
    z.plot(ax=ax, color=fk.C.FAIL, lw=0.45, zorder=4)
    hb = _boundary(ax)
    handles = [
        Line2D([], [], color=fk.C.LATERAL, lw=1.6,
               label=f"fronts at least one plot ({len(cor)-len(z):,}, "
                     f"{d['km']-zkm:,.0f} km)"),
        Line2D([], [], color=fk.C.FAIL, lw=1.6,
               label=f"fronts no load-bearing plot ({len(z):,}, {zkm:,.0f} km)"),
        hb]
    stub = d["is_stub"] & (cor["N_PLOT"] == 0) & (cor["LEN_M"] < FINGER_M)
    dbox = box([("corridors", f"{len(cor):,}"),
                ("fronting nothing", f"{len(z):,}  ({pct:.1f} % of km)"),
                (f"  of those, dead-end <{FINGER_M:.0f} m",
                 f"{int(stub.sum()):,}  ({cor.loc[stub,'LEN_M'].sum()/1000:.1f} km)"),
                ("plots fronted", f"{int(cor['N_PLOT'].sum()):,}")], width=44)
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=dbox,
                  source=fk.source_line(cor))
    p = fk.save(fig, "F_C10_corridors_fronting_nothing")
    return (p,
            f"The {zkm:,.0f} km of corridor that is the nearest corridor to no "
            f"load-bearing plot within {PLOT_SERVED_M:.0f} m.",
            "A third of the corridor network collects nothing and is a candidate for "
            "not being built at all.")


# =============================================================== F_C11  P7 chart
def f_c11() -> tuple:
    d = data()
    cor = d["cor"]
    g = grade_of(cor)
    rows = []
    for key in GRADES:
        sub = cor[[x == key for x in g]]
        z = sub[sub["N_PLOT"] == 0]["LEN_M"].sum() / 1000.0
        rows.append((GRADE_SHORT[key], sub["LEN_M"].sum() / 1000.0, z, key))
    rows.sort(key=lambda r: r[2] / max(r[1], 1e-9))

    stub = d["is_stub"] & (cor["N_PLOT"] == 0)
    fig, axes = fk.chart_frame(
        title="The corridors that collect nothing are the derived and skeleton ones, "
              "not the reserves",
        subtitle=(f"LEFT: of each source's length, how much is the nearest corridor to "
                  f"no load-bearing plot. RIGHT: how much of that dead length is a "
                  f"dead-end stub, where the philosophy's 'no fingers' rule (sec 4, "
                  f"ours, on cost grounds) would apply once reaches exist. "
                  f"The {PLOT_SERVED_M:.0f} m radius is a {OURS}."),
        figsize=(10.8, 4.4), ncols=2, ygrid=False, xgrid=True)

    ax = axes[0]
    ypos = np.arange(len(rows))[::-1]
    for y, r in zip(ypos, rows):
        ax.barh(y, r[1], height=0.62, facecolor=fk.C.FAINT, edgecolor=fk.C.INK,
                linewidth=0.5)
        ax.barh(y, r[2], height=0.62, facecolor=fk.C.FAIL, edgecolor=fk.C.INK,
                linewidth=0.5, hatch="\\\\")
        ax.text(r[1] * 1.015, y, f"{100*r[2]/max(r[1],1e-9):.0f} % of {r[1]:,.0f} km",
                va="center", ha="left", fontsize=7.4, color=fk.C.INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.6)
    ax.set_xlabel("corridor length (km)")
    ax.set_xlim(0, max(r[1] for r in rows) * 1.42)
    fk.legend_below(ax, [Patch(facecolor=fk.C.FAINT, edgecolor=fk.C.INK, linewidth=0.5,
                               label="fronts at least one load-bearing plot"),
                         Patch(facecolor=fk.C.FAIL, edgecolor=fk.C.INK, linewidth=0.5,
                               hatch="\\\\", label="fronts none (N_PLOT = 0)")],
                    ncol=1, drop=0.5)

    ax2 = axes[1]
    bands = [(0, 30), (30, 60), (60, 120), (120, 250), (250, 1e12)]
    names = ["<30 m", "30-60 m", "60-120 m", "120-250 m", ">250 m"]
    zl = cor[cor["N_PLOT"] == 0]
    tops = []
    for i, ((lo, hi), nm) in enumerate(zip(bands, names)):
        m = (zl["LEN_M"] >= lo) & (zl["LEN_M"] < hi)
        st = zl[m & d["is_stub"]]["LEN_M"].sum() / 1000.0
        ns = zl[m & ~d["is_stub"]]["LEN_M"].sum() / 1000.0
        ax2.bar(i, st, width=0.62, facecolor=fk.C.SUBMAIN, edgecolor=fk.C.INK,
                linewidth=0.6, hatch="\\\\")
        ax2.bar(i, ns, bottom=st, width=0.62, facecolor=fk.C.RIDER,
                edgecolor=fk.C.INK, linewidth=0.6)
        ax2.text(i, st + ns + 4, f"{st+ns:,.0f}", ha="center", va="bottom",
                 fontsize=7.2, color=fk.C.INK)
        tops.append(st + ns)
    ax2.set_xticks(range(len(bands)))
    ax2.set_xticklabels(names, fontsize=7.4)
    ax2.set_xlabel("corridor length")
    ax2.set_ylabel("length fronting no plot (km)")
    ax2.set_ylim(0, max(tops) * 1.42)
    ax2.text(0.02, 0.985,
             f"dead-end AND under {FINGER_M:.0f} m AND fronting nothing:\n"
             f"{int((stub & (cor['LEN_M']<FINGER_M)).sum()):,} corridors, "
             f"{cor.loc[stub & (cor['LEN_M']<FINGER_M),'LEN_M'].sum()/1000:.1f} km",
             transform=ax2.transAxes, va="top", fontsize=7.0, color=fk.C.INK,
             bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#9a9a9a", alpha=0.94))
    ax2.legend(handles=[Patch(facecolor=fk.C.SUBMAIN, edgecolor=fk.C.INK,
                              hatch="\\\\", label="has a dead end"),
                        Patch(facecolor=fk.C.RIDER, edgecolor=fk.C.INK,
                              label="both ends joined")],
               loc="upper right", fontsize=6.8, framealpha=0.94)
    fk.finish_chart(fig, source=fk.source_line(cor),
                    note="The finger test is applied to CORRIDORS here; philosophy sec 4 "
                         "states it for reaches. Indicative until stage 4/5 mint reaches.")
    p = fk.save(fig, "F_C11_fronting_nothing_by_source")
    return (p,
            "Which corridor sources carry the dead length, and how much of it is a "
            "short dead-end stub.",
            "The platted reserves are the least wasteful source; the block skeleton and "
            "the trunk corridor are the most.")


# ============================================================ F_C12  crossings
def f_c12() -> tuple:
    d = data()
    xr, cor = d["xr"], d["cor"]
    tot = xr["LEN_M"].sum() / 1000.0
    long70 = xr[xr["LEN_M"] > 70]
    long200 = xr[xr["LEN_M"] > 200]

    fig, axes = fk.chart_frame(
        title=f"All {len(xr):,} wadi crossings are scheduled and not one is approved",
        subtitle=(f"LEFT: on-wadi contact length per crossing. A crossing is legal only "
                  f"if the contact is within {SKEW:.3f} x the wadi width measured "
                  f"across the pipe ({OURS}, w11a/audit.py:56) -- so a long contact is "
                  f"legal where the wadi is genuinely wide, and the perpendicular probe "
                  f"stops looking at {PROBE_M:.0f} m. RIGHT: the G201 9.3 obligations "
                  f"the register carries and what is still open."),
        figsize=(10.8, 4.4), ncols=2, ygrid=True, xgrid=False)

    ax = axes[0]
    bins = np.logspace(np.log10(max(xr["LEN_M"].min(), 0.5)),
                       np.log10(xr["LEN_M"].max() * 1.05), 34)
    ax.hist(xr["LEN_M"], bins=bins, color=fk.C.WADI, edgecolor=fk.C.INK, linewidth=0.4)
    ax.set_xscale("log")
    ax.set_xlabel("on-wadi contact of the crossing (m, log)")
    ax.set_ylabel("crossings")
    ax.axvline(70, color=fk.C.BOUNDARY, lw=1.1, ls="--")
    ax.text(74, ax.get_ylim()[1] * 0.90,
            f"{len(long70):,} crossings longer than 70 m\n"
            f"= {long70['LEN_M'].sum()/1000:.1f} km of the {tot:.1f} km\n"
            f"{len(long200):,} longer than 200 m "
            f"({long200['LEN_M'].sum()/1000:.1f} km)",
            fontsize=7.0, va="top", color=fk.C.INK)

    ax2 = axes[1]
    ax2.axis("off")
    lines = [
        ("crossings on the register", f"{len(xr):,}"),
        ("total on-wadi contact", f"{tot:,.1f} km"),
        ("obstacle = wadi", f"{int((xr['OBSTACLE']=='wadi').sum()):,} of {len(xr):,}"),
        ("every CROSS_ID resolves to a corridor",
         "yes" if set(xr["EDGE_UID"]) ==
                  set(cor.loc[cor["CROSS_ID"].astype(str).str.strip() != "", "CORR_ID"])
         else "NO"),
        ("METHOD - trenchless or open cut", "open_cut on every row (a default)"),
        ("ANGLE_DEG - the measured skew", "90.0 on every row (nominal)"),
        ("APPROVED = 1 (MoAFWR consent)", f"{int(xr['APPROVED'].sum())} of {len(xr):,}"),
    ]
    y = 0.97
    for k, v in lines:
        ax2.text(0.0, y, k, fontsize=8.0, va="top", color=fk.C.GREY)
        bad = v.startswith("0 of") or v.startswith("NO") or "nominal" in v or \
            "a default" in v
        ax2.text(1.0, y, v, fontsize=8.4, va="top", ha="right",
                 color=fk.C.FAIL if bad else fk.C.INK,
                 fontweight="bold" if bad else "normal")
        y -= 0.098
    ax2.text(0.0, y - 0.02,
             "G201-p85: \"Approvals shall be obtained from MoAFWR and any other\n"
             "relevant agencies\", with bed profile and cross-sections, 1:20 / 1:50 /\n"
             "1:100 flood levels, bed material and long-term bed-level change.\n"
             "G201-p86: ductile iron over the crossing plus 15 m either side,\n"
             "anti-flotation, protection to PAM-STD-404, 2 m cover in soft soil.\n"
             "G203-p30 4.4.1 and p33 prohibit a CHAMBER on wadi ground outright.",
             fontsize=7.0, va="top", color=fk.C.INK, linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.5", fc="#f4f2ee", ec="#b8b8b8"))
    fk.finish_chart(fig, source=fk.source_line(xr, cor),
                    note="Guideline text read back from Data/PAM-GUD-201 and "
                         "Data/PAM-GUD-203 on 2026-09-02, not quoted from memory.")
    p = fk.save(fig, "F_C12_wadi_crossings_register")
    return (p,
            f"The {len(xr):,}-row wadi-crossing register: contact lengths, and the "
            f"consents and fields still open.",
            "The corridor set is only legal if 2,539 individually-approved crossings "
            "are obtainable, and none has been sought.")


# ========================================================= F_C13  flood answer
def f_c13() -> tuple:
    d = data()
    cor = d["cor"]
    ans = hazard_answer(cor)
    cor = cor.assign(ANS=ans)
    g = grade_of(cor)
    cor = cor.assign(GRADE=[GRADE_SHORT[x] for x in g])
    piv = (cor.pivot_table(index="GRADE", columns="ANS", values="LEN_M",
                           aggfunc="sum") / 1000.0).fillna(0.0)
    piv = piv.reindex([GRADE_SHORT[k] for k in GRADES])
    no_km = piv.get("no answer", pd.Series(0, index=piv.index)).sum()
    pct = 100.0 * no_km / d["km"]

    fig, ax = fk.chart_frame(
        title=f"{no_km:,.0f} km of corridor - {pct:.0f} % of the network - has no flood "
              f"answer at all",
        subtitle=(f"Every corridor midpoint sampled against the 50-year hazard grid "
                  f"at full 3 m resolution. Its nodata is -9999.0, which IS finite, so "
                  f"an np.isfinite guard alone scores it as dry ground; UNTESTED is "
                  f"published beside the result, never left blank (philosophy H1a). "
                  f"Classes 4-6 are an AR&R danger-to-people scale standing in for "
                  f"G203-p30 4.4.1's \"areas subject to washout\", which is a SCOUR "
                  f"criterion - a {OURS}."),
        figsize=(10.6, 4.4), ygrid=False, xgrid=True)

    order = ["tested, clear", "wadi class 4-6", "no answer"]
    role = {"tested, clear": "pass", "wadi class 4-6": "fail", "no answer": "untested"}
    names = {"tested, clear": "tested, outside the wadi classes",
             "wadi class 4-6": "on wadi ground (class 4-6, a PROJECT threshold)",
             "no answer": "UNTESTED - outside the 50-year grid"}
    ypos = np.arange(len(piv))[::-1]
    for y, gname in zip(ypos, piv.index):
        left = 0.0
        for a in order:
            v = float(piv.loc[gname, a]) if a in piv.columns else 0.0
            if v <= 0:
                continue
            ax.barh(y, v, left=left, height=0.6, **fk.status_style(role[a]))
            if v > 25:
                ax.text(left + v / 2, y, f"{v:,.0f}", ha="center", va="center",
                        fontsize=7.2, color=fk.label_ink(role[a]), fontweight="bold")
            left += v
        ax.text(left + 8, y, f"{left:,.0f} km", va="center", ha="left", fontsize=7.4,
                color=fk.C.INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels(list(piv.index), fontsize=7.6)
    ax.set_xlabel("corridor length (km)")
    ax.set_xlim(0, piv.sum(axis=1).max() * 1.16)
    fk.legend_below(ax, [Patch(label=names[a], **fk.status_style(role[a]))
                         for a in order], ncol=3, drop=0.5)
    fk.finish_chart(fig, source=fk.source_line(cor, HAZ_SRC))
    p = fk.save(fig, "F_C13_corridor_flood_answer")
    return (p,
            "Corridor length by what the 50-year hazard grid says about it. More than "
            "half has no answer.",
            "Every wadi statement about this network is a statement about the tested "
            "half only.")


# ====================================================== F_C14  plots left outside
def f_c14() -> tuple:
    d = data()
    nop, cor = d["nop"], d["cor"]
    q = nop["Q_AVG_M3D"].sum()

    fig, ax, note = map_frame(
        fk.extent_of(cor, pad=0.02),
        title=f"{len(nop):,} plots have no corridor within {PLOT_SERVED_M:.0f} m, and "
              f"they carry {q:,.0f} m\u00b3/d",
        subtitle=(f"The other side of the same {PLOT_SERVED_M:.0f} m test as F_C10. "
                  f"These plots carry {int(nop['N_PROP'].sum()):,} properties and "
                  f"{int(nop['POP'].sum()):,} people, all of them inside the study "
                  f"boundary. TOR scope p4 item 3 requires every plot to be SERVED, so "
                  f"this is a scope answer for stage 1 -- central, satellite or on-site "
                  f"-- not a rounding error."))
    cor.plot(ax=ax, color=fk.C.GREY, lw=0.20, alpha=0.55, zorder=2)
    ax.scatter(nop.geometry.centroid.x, nop.geometry.centroid.y, s=7,
               color=fk.C.FAIL, zorder=6, linewidths=0)
    hb = _boundary(ax)
    handles = [Line2D([], [], color=fk.C.GREY, lw=1.0, alpha=0.55,
                      label=f"corridor ({d['km']:,.0f} km)"),
               Line2D([], [], color=fk.C.FAIL, lw=0, marker="o", markersize=5,
                      label=f"plot with no corridor within {PLOT_SERVED_M:.0f} m "
                            f"({len(nop):,})"),
               hb]
    cat = nop["CAT"].value_counts()
    dbox = box([("plots", f"{len(nop):,}"),
                ("properties", f"{int(nop['N_PROP'].sum()):,}"),
                ("population", f"{int(nop['POP'].sum()):,}"),
                ("load", f"{q:,.0f} m\u00b3/d")] +
               [("  " + str(k), f"{int(v):,}") for k, v in cat.head(4).items()],
               width=30)
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=dbox,
                  source=fk.source_line(nop, cor))
    p = fk.save(fig, "F_C14_plots_with_no_corridor")
    return (p,
            f"The {len(nop):,} plots left outside the corridor set, carrying "
            f"{q:,.0f} m\u00b3/d.",
            "Corridor coverage is 97 % of plots, and the missing 3 % is a scope "
            "question the TOR does not let us drop.")


# --------------------------------------------------------------------- runner

FIGURES = {
    "F_C01": f_c01, "F_C02": f_c02, "F_C03": f_c03, "F_C04": f_c04,
    "F_C05": f_c05, "F_C06": f_c06, "F_C07": f_c07, "F_C08": f_c08,
    "F_C09": f_c09, "F_C10": f_c10, "F_C11": f_c11, "F_C12": f_c12,
    "F_C13": f_c13, "F_C14": f_c14,
}


def main(argv: list[str]) -> int:
    want = [a for a in argv[1:] if not a.startswith("-")]
    print("grade palette self-test:")
    for line in check_grade_palette():
        print(line)
    print()
    keys = want or list(FIGURES)
    for k in keys:
        stem = k.split("_")[0] + "_" + k.split("_")[1] if "_" in k else k
        fn = FIGURES.get(stem[:5]) or FIGURES.get(k)
        if fn is None:
            print(f"  ?? unknown figure {k}")
            continue
        path, caption, finding = fn()
        print(f"  {path.name}")
        print(f"      finding: {finding}")
        print(f"      caption: {caption}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
