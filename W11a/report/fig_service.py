"""fig_service — WHO IS SERVED, WHO IS NOT, AND WHY.

Twelve figures for the W11a report, all drawn through ``figkit`` so they read as one set
with every other figure in the document.

    cd W11a/report
    python fig_service.py                # rebuild all twelve, idempotent
    python fig_service.py S01 S04        # rebuild only those
    python fig_service.py --check        # palette + provenance self-test, draws nothing
    python fig_service.py --numbers      # print every figure value with its artefact

The command-line keys are S01..S12; the files they write are ``img/FS01_*.png`` ..
``img/FS12_*.png``, following the report's F<group><nn> naming.

WHY THIS SET EXISTS
-------------------
The TOR requires every plot to be served (scope p4 item 3, p6 item 2, p8 item 17), so
"24,554 plots are unconnected" is the number the client reads hardest — and on its own it
is misleading in three separate ways, each of which one of these figures corrects:

  * it is 30.1 % of the LOAD but the 45 m tertiary rule (G203-p22 Tab 6, Lateral Sewer row)
    owns only 8.59 % of it — S01;
  * the largest single share, 9.63 %, is a drainability test run against chamber levels
    that do not exist yet: all 50,033 chambers sit at DEPTH_M 1.600 — S06;
  * three fifths of the unconnected load sits on plots with nothing built on them — S10.

NUMBER DISCIPLINE
-----------------
Every value on every figure is computed here, in this file, from one of these artefacts,
and nothing is carried in from a briefing note:

    W11a/shp/W11a.gpkg [connections]         45,232 published property connections
    W11a/shp/W11a.gpkg [servicing]           187 settlements, one servicing decision each
    W11a/shp/W11a_manholes.shp               the stage-5 chamber seeds (for S06's premise)
    W11a/run/s5b_unassigned.csv              24,554 plots named, each with its own reason
    W11a/run/s5b_chamber_requests.csv        5,867 actionable chamber / corridor requests
    W11a/run/s1_plot_system.csv              64,071 plot records -> settlement -> system
    W11a/run/s1_break_sensitivity.csv        the servicing split swept over the cost break
    W11a/run/manifest_s5b_tertiary.json      stage 5b's own printed metrics
    W10/shp/W10_plot_loads.gpkg              the plot polygons and their loads

    The reason buckets are re-derived from the WHY text on every run (:func:`_bucket`), so
    if stage 5b is re-run under us the figures move with it instead of quoting a stale
    decomposition.  ``--numbers`` prints what they currently are.

GUIDELINE VALUES ON THESE FIGURES — all four re-read from the PDF on 2026-09-02
------------------------------------------------------------------------------
    45 m    G203-p22 Table 6, Lateral Sewer row: "Maximum Length 45 m"
    2.5 m   G203-p17 sec 3.2: "The HCC is usually installed 2.5 m from the property
            boundary in the public right-of-way (ROW)"
    100 m   G203-p30 Table 12, 200-315 mm row: maximum spacing between manholes
    1 %     G203-p18 Table 5, Lateral / Rider Sewer: gradient minimal
    25 km   G201-p80 sec 8.1, second bullet: "Settlements located approximately 25 km or
            more from existing centralized water or wastewater networks"
    50-5,000 pe   G201-p83 sec 8.4.1: package plants "for communities with a population
            between 50-5,000 inhabitants"

PROJECT VALUES, LABELLED AS OURS WHEREVER THEY APPEAR
-----------------------------------------------------
    20 m/property  the cost break between a central connection and an on-site system.
                   NOT a guideline number: G201-p80's fourth remote-area test is worded
                   "geographical barriers preventing economical connection", and this is
                   our operationalisation of it, read off the distribution of the 187
                   settlements.  S08 exists to show how much the answer depends on it.
    47.5 m         the carrier search radius = 45 m + the 2.5 m HCC offset.  Arithmetic on
                   two guideline numbers, not a guideline number itself.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import figkit as fk                                    # noqa: E402
import matplotlib                                      # noqa: E402
import matplotlib.pyplot as plt                        # noqa: E402
import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D                    # noqa: E402
from matplotlib.patches import Patch                   # noqa: E402

PLOT_LOADS = fk.ROOT / "W10" / "shp" / "W10_plot_loads.gpkg"
MANHOLES = fk.SHP / "W11a_manholes.shp"
MANIFEST_S5B = fk.RUN / "manifest_s5b_tertiary.json"

# --------------------------------------------------------------------------- palette
#
# A warm single-hue ladder for the five reasons a plot is not connected, ordered by the
# load each holds.  One hue at six separated lightnesses plus a hatch each: it survives a
# greyscale print and it does not rest on red-versus-green.  ``--check`` proves the
# separation the same way figkit proves its own.

REASONS = [
    "cannot drain",
    "no carrier in range",
    "leg over 45 m",
    "corridor through plot",
    "outside boundary",
    "no load",
]
REASON_COLOR = {
    "cannot drain": "#381c05",
    "no carrier in range": "#68350c",
    "leg over 45 m": "#9a5313",
    "corridor through plot": "#cc8025",
    "outside boundary": "#e6b163",
    "no load": "#fdf6e8",
}
REASON_HATCH = {
    "cannot drain": "\\\\",
    "no carrier in range": "xx",
    "leg over 45 m": "//",
    "corridor through plot": "..",
    "outside boundary": "--",
    "no load": None,
}
#: Short axis tick, for a waterfall where the full wording will not fit.
REASON_TICK = {
    "cannot drain": "cannot\ndrain",
    "no carrier in range": "no carrier\nwithin 47.5 m",
    "leg over 45 m": "leg over\n45 m",
    "corridor through plot": "corridor\nthrough plot",
    "outside boundary": "outside\nboundary",
    "no load": "no\nload",
}
#: What each reason says, in the words a reader needs rather than the code's words.
REASON_LABEL = {
    "cannot drain": "cannot drain to its chamber",
    "no carrier in range": "no carrier within 47.5 m",
    "leg over 45 m": "leg over the 45 m limit",
    "corridor through plot": "corridor through the plot",
    "outside boundary": "outside the study boundary",
    "no load": "carries no wastewater load",
}
CONNECTED = "#e8e3d9"        # fk.C.PLOT_FILL — the neutral the project uses for plots
CONNECTED_INK = fk.C.GREY

#: Sequential ramp for the share-unconnected grid.  Monotone in luminance by construction.
SHARE_CMAP = LinearSegmentedColormap.from_list(
    "unconn", ["#fdf6e8", "#e6b163", "#cc8025", "#9a5313", "#68350c", "#381c05"])


def reason_style(reason: str, *, filled: bool = True) -> dict:
    """Colour + hatch for one unconnected-reason patch."""
    return {"facecolor": REASON_COLOR.get(reason, fk.C.GREY) if filled else "none",
            "edgecolor": fk.C.INK, "hatch": REASON_HATCH.get(reason), "linewidth": 0.5}


def reason_legend(counts=None, loads=None) -> list[Patch]:
    """Legend handles, darkest (worst) first, with counts and loads if given."""
    out = []
    for r in REASONS:
        lab = REASON_LABEL[r]
        if counts is not None:
            lab += f"  ({counts.get(r, 0):,})"
        if loads is not None:
            lab += f"  {loads.get(r, 0.0):,.0f} m3/d"
        out.append(Patch(label=lab, **reason_style(r)))
    return out


def check_palette(min_ratio: float = 1.50) -> list[str]:
    """Prove the reason ladder holds apart in greyscale.  Mirrors fk.check_palette."""
    lad = [REASON_COLOR[r] for r in REASONS]
    lum = [fk._rel_luminance(c) for c in lad]
    out = ["reason ladder (dark = most load): "
           + "  ".join(f"{c} L={l:.3f}" for c, l in zip(lad, lum))]
    for i in range(len(lum) - 1):
        hi, lo = max(lum[i], lum[i + 1]), min(lum[i], lum[i + 1])
        ratio = (hi + 0.05) / (lo + 0.05)
        out.append(f"   {lad[i]} vs {lad[i+1]}: greyscale contrast {ratio:.2f}")
        assert ratio >= min_ratio, (
            f"reason ladder step {lad[i]}->{lad[i+1]} only {ratio:.2f}:1 in greyscale")
    # the neutral used for CONNECTED sits beside the ladder on the maps
    for c in (REASON_COLOR["outside boundary"], REASON_COLOR["corridor through plot"]):
        lc, ln = fk._rel_luminance(CONNECTED), fk._rel_luminance(c)
        ratio = (max(lc, ln) + 0.05) / (min(lc, ln) + 0.05)
        out.append(f"   connected {CONNECTED} vs {c}: greyscale contrast {ratio:.2f}")
        assert ratio >= min_ratio, f"connected vs {c} only {ratio:.2f}:1"
    return out


# ----------------------------------------------------------------------- the artefacts

def _bucket(why: str) -> str:
    """One reason string -> one of the six buckets.

    Derived from the WHY text every run rather than hard-coded counts, because stage 5b is
    still being worked on: if its wording changes the bucket falls through to OTHER and the
    figures say so loudly instead of quietly dropping rows.
    """
    w = str(why)
    if w.startswith("no wastewater load"):
        return "no load"
    if "outside the project boundary" in w:
        return "outside boundary"
    if w.startswith("cannot drain to"):
        return "cannot drain"
    if "no lateral/main/sub main reach within" in w:
        return "no carrier in range"
    if "the 45 m limit" in w or "past the 45 m limit" in w or "45 m limit (G203" in w:
        return "leg over 45 m"
    if "the carrier runs through or along the plot" in w:
        return "corridor through plot"
    return "OTHER"


class Data:
    """Everything the ten figures read, loaded once, each object carrying provenance."""

    def __init__(self) -> None:
        self.plots = fk.read_layer(
            str(PLOT_LOADS),
            columns=["PLOT_ID", "CLASS", "CAT", "Q_AVG_M3D", "N_PROP", "AREA_M2", "IN_BND"])
        self.plots["PID"] = self.plots.PLOT_ID.astype(str).str.strip()

        self.conn = fk.read_layer(
            "W11a.gpkg", "connections",
            columns=["CONN_ID", "PLOT_ID", "WHY", "SYSTEM", "CONN_TYPE", "Q_ADF_M3D",
                     "N_PROP", "LEN_M", "SLOPE_LAID", "COVER_M", "CAN_DRAIN",
                     "CONFIDENCE", "STAGE"])
        self.conn["PID"] = self.conn.PLOT_ID.astype(str).str.strip()

        self.unas = fk.read_csv("s5b_unassigned.csv", dtype={"PLOT_ID": str})
        self.unas["PID"] = self.unas.PLOT_ID.astype(str).str.strip()
        self.unas["BUCKET"] = self.unas.WHY.map(_bucket)
        bad = int((self.unas.BUCKET == "OTHER").sum())
        if bad:
            raise SystemExit(
                f"fig_service: {bad:,} rows of s5b_unassigned.csv no longer match any "
                "reason bucket — stage 5b has changed its WHY wording. Fix _bucket() "
                "before drawing, or the decomposition silently loses a group.\n  e.g. "
                + self.unas.loc[self.unas.BUCKET == "OTHER", "WHY"].iloc[0][:160])

        self.req = fk.read_csv("s5b_chamber_requests.csv", dtype={"PLOT_ID": str})
        self.psys = fk.read_csv("s1_plot_system.csv", dtype={"PLOT_ID": str})
        self.brk = fk.read_csv("s1_break_sensitivity.csv")
        self.flows = fk.read_csv("s5c_reach_flows.csv",
                                 usecols=["EDGE_UID", "TIER", "LEN_M"])
        self.serv = fk.read_layer("W11a.gpkg", "servicing")
        self.checks = fk.read_csv("s1_checks.csv")

        # stage 5b's own printed metrics — the offset percentiles live only here
        man = json.loads(MANIFEST_S5B.read_text())
        st = next(s for s in man["stages"] if s["stage"] == "s5b_tertiary")
        self.m5b = st["metrics"]
        self.m5b_notes = list(st.get("notes", []))
        self.s5b_reads = list(st.get("reads", []))
        # figkit.cite() takes a stamped frame or a plain string, not a bare Src, so the
        # two artefacts figkit has no reader for are cited as strings in its own format.
        self.m5b_src = str(fk.Src(MANIFEST_S5B, "s5b_tertiary metrics", len(self.m5b),
                                  time.strftime("%Y-%m-%d %H:%M",
                                                time.localtime(MANIFEST_S5B.stat().st_mtime))))

        # the premise behind S06: every chamber is still sitting on its stage-5 seed
        mh = fk.read_layer(str(MANHOLES), columns=["NODE_UID", "DEPTH_M", "STAGE"])
        self.mh_n = len(mh)
        self.mh_depth_unique = sorted(pd.unique(mh.DEPTH_M.round(3)))
        self.mh_stage = sorted(pd.unique(mh.STAGE.astype(str)))
        self.mh_src = str(mh.attrs["fk_source"])

        # ---- derived, once ----------------------------------------------------------
        un_ids = set(self.unas.PID)
        self.plots["UNSERVED"] = self.plots.PID.isin(un_ids)
        # pandas drops .attrs across a merge, so the provenance stamp is re-attached by
        # hand -- a figure drawn off this frame must still be able to cite its artefact.
        plots_src = self.plots.attrs["fk_source"]
        self.plots = self.plots.merge(
            self.unas[["PID", "BUCKET"]], on="PID", how="left")
        self.plots["BUCKET"] = self.plots.BUCKET.fillna("connected")
        self.plots.attrs["fk_source"] = plots_src

        self.q_total = float(self.psys.Q_AVG_M3D.sum())
        self.n_total = int(len(self.psys))
        self.q_unas = float(self.unas.Q_ADF_M3D.sum())
        self.n_unas = int(len(self.unas))
        self.q_conn = self.q_total - self.q_unas
        self.n_conn = self.n_total - self.n_unas

        g = self.unas.groupby("BUCKET").agg(n=("PID", "size"), q=("Q_ADF_M3D", "sum"),
                                            prop=("N_PROP", "sum"))
        self.by_reason = g.reindex(REASONS).fillna(0.0)

        # plots that have a drawn connection AND a name in the unassigned file
        self.n_drawn_nodrain = len(set(self.conn.PID) & un_ids)

        self._pipeline_state()

    # -- is the set of artefacts I am about to draw self-consistent? -------------------

    def _pipeline_state(self) -> None:
        """Compare what stage 5b READ against what stage 5 PUBLISHED, and say so.

        The stages are being worked on by other agents while these figures are drawn.  A
        run of stage 5b against a stage-4 carrier network produces a perfectly internally
        consistent set of numbers that mean something quite different from the same
        numbers off the stage-5 chamber set — chambers twice as far apart, so tertiary
        legs twice as long.  Nothing in the layers themselves says which happened; the
        manifest's own ``reads`` block does, so it is checked here and the answer is put
        on every figure that depends on the tertiary assignment.
        """
        self.reads = {r["name"]: int(r["n"]) for r in self.s5b_reads}
        self.carriers_read = self.reads.get("reaches")
        self.chambers_read = self.reads.get("nodes")
        pend = self.conn.WHY.str.contains("LEVELS PENDING", regex=False)
        self.n_levels_pending = int(pend.sum())
        self.levels_pending = self.n_levels_pending == len(self.conn) and len(self.conn) > 0

        bits = []
        if self.chambers_read is not None and self.mh_n and self.chambers_read < self.mh_n:
            bits.append(
                f"stage 5b read {self.chambers_read:,} chamber nodes and "
                f"{self.carriers_read:,} carrier reaches, while stage 5 published "
                f"{self.mh_n:,} chambers — the chamber set has been overwritten by a "
                f"stage-4 re-run, so every distance from a plot to its chamber is "
                f"measured against roughly half the carriers the design has")
        if self.levels_pending:
            bits.append(
                f"all {len(self.conn):,} connections carry \"LEVELS PENDING\": the "
                f"gradient is the G203-p18 Table 5 minimum declared, not solved, and the "
                f"arrival at the chamber is unchecked")
        self.warn = ("PIPELINE STATE, from the stage's own manifest: "
                     + "; and ".join(bits) + ".") if bits else ""

    def caveat(self, sub: str) -> str:
        """Append the pipeline-state warning to a subtitle, when there is one."""
        return f"{sub}  {self.warn}" if self.warn else sub

    # -- small helpers used by more than one figure ----------------------------------

    def pct_load(self, q: float) -> float:
        return 100.0 * q / self.q_total

    def leg_lengths(self) -> pd.DataFrame:
        """The 'leg over 45 m' plots with the leg length parsed out of their own WHY."""
        s = self.unas[self.unas.BUCKET == "leg over 45 m"].copy()
        s["LEG_M"] = s.WHY.str.extract(r"nearest chamber ([\d.]+) m away")[0].astype(float)
        return s.dropna(subset=["LEG_M"])

    def drain_shortfall(self) -> pd.DataFrame:
        """The 'cannot drain' plots with the arrival shortfall parsed out of their WHY."""
        s = self.unas[self.unas.BUCKET == "cannot drain"].copy()
        s["SHORT_M"] = s.WHY.str.extract(r"arrives ([\d.]+) m below")[0].astype(float)
        return s.dropna(subset=["SHORT_M"])

    def grid(self, cell: float = 500.0):
        """Load and unconnected load on a square grid.  Returns (tot, unc, extent)."""
        c = self.plots.geometry.representative_point()
        x0, y0, x1, y1 = self.plots.total_bounds
        nx = int(np.ceil((x1 - x0) / cell)) + 1
        ny = int(np.ceil((y1 - y0) / cell)) + 1
        ix = np.clip(((c.x.values - x0) // cell).astype(int), 0, nx - 1)
        iy = np.clip(((c.y.values - y0) // cell).astype(int), 0, ny - 1)
        flat = iy * nx + ix
        q = self.plots.Q_AVG_M3D.fillna(0.0).values
        tot = np.bincount(flat, weights=q, minlength=nx * ny).reshape(ny, nx)
        unc = np.bincount(flat, weights=q * self.plots.UNSERVED.values,
                          minlength=nx * ny).reshape(ny, nx)
        return tot, unc, (x0, x0 + nx * cell, y0, y0 + ny * cell)


# ------------------------------------------------------------------------------ S01

def S01(d: Data):
    """The decomposition — where the unconnected load actually goes."""
    r = d.by_reason
    q45 = float(r.loc["leg over 45 m", "q"])
    pct45 = d.pct_load(q45)
    top = str(r.q.idxmax())
    pct_top = d.pct_load(float(r.loc[top, "q"]))

    fig, axes = fk.chart_frame(
        title=(f"{d.pct_load(d.q_conn):.1f} % of the ultimate load reaches a chamber; the "
               f"largest single gap is “{REASON_LABEL[top]}” at {pct_top:.2f} %"),
        subtitle=d.caveat(
            f"Every one of the {d.n_total:,} plot records ends in exactly one place: at a "
            f"chamber, or named in s5b_unassigned.csv with the reason it did not get "
            f"there. The 45 m tertiary rule (G203-p22 Table 6, Lateral Sewer row) owns "
            f"{pct45:.2f} % of the load, against the {d.pct_load(d.q_unas):.1f} % that is "
            f"unconnected in total — the headline and the rule are not the same number. "
            f"Left: the ultimate average day flow. Right: the same split by plot count — "
            f"the two disagree, which is the point."),
        figsize=(12.2, 5.6), ncols=2, ygrid=True)

    for ax, key, unit, tot, conn in (
            (axes[0], "q", "m3/d", d.q_total, d.q_conn),
            (axes[1], "n", "plots", float(d.n_total), float(d.n_conn))):
        steps = [("all\nplots", tot, fk.C.GREY, None)]
        for rr in REASONS:
            steps.append((REASON_TICK[rr], -float(r.loc[rr, key]),
                          REASON_COLOR[rr], REASON_HATCH[rr]))
        steps.append(("connected", conn, fk.C.PASS, None))

        run = 0.0
        xs = np.arange(len(steps))
        for i, (lab, v, col, hat) in enumerate(steps):
            head_tail = i == 0 or i == len(steps) - 1
            if head_tail:
                bot, h = 0.0, (tot if i == 0 else conn)
                run = tot if i == 0 else run
            else:
                h = -v
                bot = run - h
                run = bot
            ax.bar(i, h, bottom=bot, width=0.66, facecolor=col, edgecolor=fk.C.INK,
                   linewidth=0.6, hatch=hat, zorder=3)
            if i and i < len(steps) - 1:
                ax.plot([i - 0.33, i + 0.33], [bot + h, bot + h], color=fk.C.GREY,
                        lw=0.7, ls=":", zorder=2)
            val = tot if i == 0 else conn if i == len(steps) - 1 else -v
            share = 100.0 * val / tot
            txt = f"{val:,.0f}" if (val >= 100 or key == "n") else f"{val:,.1f}"
            pct = f"{share:.1f} %" if head_tail else f"{share:.2f} %"
            ax.text(i, bot + h + tot * 0.014, f"{txt}\n{pct}", ha="center",
                    va="bottom", fontsize=7.0, color=fk.C.INK,
                    fontweight="bold" if head_tail else "normal")
        ax.set_xticks(xs)
        ax.set_xticklabels([st[0] for st in steps], fontsize=6.9)
        ax.set_ylim(0, tot * 1.20)
        fk.thousands(ax, "y")
        ax.set_ylabel("ultimate average day flow (m3/d)" if key == "q"
                      else "plot records")

    axes[0].annotate(
        "G203-p22 Tab 6,\nLateral Sewer:\n\"Maximum Length 45 m\"",
        xy=(3, d.q_total - float(r.loc["cannot drain", "q"])
            - float(r.loc["no carrier in range", "q"]) - q45 / 2),
        xytext=(2.6, d.q_total * 0.38), fontsize=6.8, color=fk.C.INK,
        arrowprops=dict(arrowstyle="-", color=fk.C.GREY, lw=0.7),
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#9a9a9a", alpha=0.92))

    fk.finish_chart(fig, source=fk.source_line(d.unas, d.psys, d.conn))
    path = fk.save(fig, "FS01_service_decomposition")
    return (path,
            f"Where the unconnected load goes. {d.pct_load(d.q_unas):.1f} % of the "
            f"ultimate flow reaches no chamber; the 45 m tertiary rule owns "
            f"{pct45:.2f} % of the total and the largest single gap is "
            f"“{REASON_LABEL[top]}” at {pct_top:.2f} %.",
            f"{d.pct_load(d.q_conn):.1f} % of the load connects; largest gap is "
            f"'{REASON_LABEL[top]}' at {pct_top:.2f} %, and the 45 m rule owns "
            f"{pct45:.2f} %")


# ------------------------------------------------------------------------------ S02

def S02(d: Data):
    """Where the unconnected load is — full study area, 500 m grid."""
    cell = 500.0
    tot, unc, ext = d.grid(cell)
    floor = 5.0                                    # m3/d in the cell, ours, stated below
    share = np.where(tot >= floor, 100.0 * unc / np.maximum(tot, 1e-9), np.nan)
    hidden = float(unc[(tot > 0) & (tot < floor)].sum())
    live = int((tot >= floor).sum())

    # Is it concentrated, or is it everywhere?  Both measures, because the honest answer
    # here turned out to be the second one and the first alone would have flattered it.
    flat = np.sort(unc[tot > 0].ravel())[::-1]
    n_half = int(np.searchsorted(np.cumsum(flat), 0.5 * flat.sum()) + 1)
    cells_with_load = int((tot > 0).sum())
    cells_hit = int((unc > 0).sum())
    med_share = float(np.median(share[np.isfinite(share)]))
    q1 = float(np.percentile(share[np.isfinite(share)], 25))
    q3 = float(np.percentile(share[np.isfinite(share)], 75))
    top10 = 100.0 * float(np.cumsum(flat)[max(int(0.1 * len(flat)) - 1, 0)] / flat.sum())

    n10 = max(int(np.ceil(0.1 * len(flat))), 1)
    # Which story the map tells is decided by the data, not by the caption I want: if the
    # worst tenth of cells hold about half the shortfall it is a concentration, otherwise
    # it is a spread, and the title says whichever is true of the layers on the day.
    concentrated = top10 >= 45.0

    x0, x1, y0, y1 = ext
    fig, ax, note = fk.map_frame(
        fk.extent_of((x0, y0, x1, y1), pad=0.02),
        title=(f"The shortfall is concentrated: the worst {n10:,} cells of "
               f"{cells_with_load:,} hold {top10:.0f} % of the unconnected load"
               if concentrated else
               f"There is no bad corner to fix: {cells_hit:,} of {cells_with_load:,} "
               f"populated cells carry unconnected load, median share {med_share:.0f} %"),
        subtitle=d.caveat(
                  f"{cell:.0f} m cells over the whole study area, shaded by the share of "
                  f"the cell's ultimate flow that reaches no chamber. "
                  f"{cells_hit:,} of the {cells_with_load:,} populated cells carry some; "
                  f"the middle half sit between {q1:.0f} % and {q3:.0f} % unconnected, "
                  f"and the worst tenth ({n10:,} cells) hold {top10:.0f} % of the total"
                  + (" — so a short list of corridors reaches most of it."
                     if concentrated else
                     " — so no short list of corridors reaches most of it.")
                  + f" Cells carrying under {floor:.0f} m3/d are left blank (a PROJECT "
                    f"display floor, not a guideline value): {cells_with_load - live:,} "
                    f"such cells hold {hidden:,.0f} m3/d."))

    im = ax.imshow(np.ma.masked_invalid(share), extent=(x0, x1, y0, y1), origin="lower",
                   cmap=SHARE_CMAP, vmin=0, vmax=100, zorder=3, alpha=0.92,
                   interpolation="nearest")
    try:
        fk.study_boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.1, ls="--",
                                          zorder=6)
    except Exception:                                        # noqa: BLE001
        pass

    # colour bar in the empty top-centre; the lower-left corner belongs to the scale bar
    cax = ax.inset_axes([0.30, 0.935, 0.26, 0.020])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.set_label("% of the cell's flow unconnected", fontsize=6.6, color=fk.C.INK,
                 labelpad=2)
    cb.ax.tick_params(labelsize=6.2, colors=fk.C.INK, length=2)
    cb.outline.set_linewidth(0.6)

    handles = [Line2D([], [], color=fk.C.BOUNDARY, lw=1.2, ls="--",
                      label="study boundary"),
               Patch(facecolor="white", edgecolor="#9a9a9a", lw=0.6,
                     label=f"blank = under {floor:.0f} m3/d, or no plots")]
    box = (f"plots               {d.n_total:>10,}\n"
           f"ultimate flow       {d.q_total:>9,.0f} m3/d\n"
           f"unconnected         {d.q_unas:>9,.0f} m3/d  "
           f"{d.pct_load(d.q_unas):>4.1f} %\n"
           f"populated cells     {cells_with_load:>10,}\n"
           f"cells with a gap    {cells_hit:>10,}\n"
           f"cells holding half  {n_half:>10,}")
    fk.finish_map(fig, ax, legend_handles=handles, legend_loc="upper left", databox=box,
                  note=note, source=fk.source_line(d.plots, d.unas))
    path = fk.save(fig, "FS02_unconnected_load_map")
    return (path,
            f"Unconnected load on a {cell:.0f} m grid. {cells_hit:,} of "
            f"{cells_with_load:,} populated cells carry some, at a median share of "
            f"{med_share:.0f} %, and the worst {n10:,} cells hold {top10:.0f} % of it.",
            f"{cells_hit:,} of {cells_with_load:,} populated cells carry unconnected "
            f"load (median share {med_share:.0f} %); the worst {n10:,} hold "
            f"{top10:.0f} % of it")


# ------------------------------------------------------------------------------ S03

def S03(d: Data):
    """The five reasons, at a scale where they can be seen."""
    cell = 500.0
    tot, unc, ext = d.grid(cell)
    # 3x3 window = 1.5 km, the densest block of unconnected load
    k = np.ones((3, 3))
    from numpy.lib.stride_tricks import sliding_window_view
    if unc.shape[0] >= 3 and unc.shape[1] >= 3:
        win = sliding_window_view(unc, (3, 3)).sum(axis=(2, 3))
        iy, ix = np.unravel_index(int(np.argmax(win)), win.shape)
    else:                                                    # pragma: no cover
        iy = ix = 0
    x0 = ext[0] + ix * cell
    y0 = ext[2] + iy * cell
    win_q = float(unc[iy:iy + 3, ix:ix + 3].sum())
    pad = 120.0
    extent = (x0 - pad, y0 - pad, x0 + 3 * cell + pad, y0 + 3 * cell + pad)

    sel = d.plots.cx[extent[0]:extent[2], extent[1]:extent[3]]
    cn = d.conn.cx[extent[0]:extent[2], extent[1]:extent[3]]
    rq = d.req[(d.req.X.between(extent[0], extent[2]))
               & (d.req.Y.between(extent[1], extent[3]))]

    n_un = int(sel.UNSERVED.sum())
    q_un = float(sel.loc[sel.UNSERVED, "Q_AVG_M3D"].sum())
    q_all = float(sel.Q_AVG_M3D.sum())

    fig, ax, note = fk.map_frame(
        fk.extent_of(extent, pad=0.0),
        title=(f"The densest 1.5 km of the problem: {q_un:,.0f} m3/d unconnected out of "
               f"{q_all:,.0f} on {len(sel):,} plots"),
        subtitle=d.caveat(
                  "The five reasons drawn where they occur, over the published property "
                  "connections. Every shaded plot is named in s5b_unassigned.csv; the "
                  "crosses are the chamber and corridor requests stage 5b raised against "
                  "them. Window chosen automatically as the 3x3 grid block holding the "
                  "most unconnected load."),
        figsize=(9.4, 9.6))

    conn_sel = sel[~sel.UNSERVED]
    if len(conn_sel):
        conn_sel.plot(ax=ax, facecolor=CONNECTED, edgecolor=CONNECTED_INK, lw=0.18,
                      zorder=3)
    for rr in reversed(REASONS):                    # light first, dark on top
        part = sel[sel.BUCKET == rr]
        if len(part):
            part.plot(ax=ax, zorder=4, **reason_style(rr))
    if len(cn):
        # blue against the warm plot fills — a hue AND a lightness apart, so the fabric
        # of the tertiary network reads over the reasons instead of vanishing into them
        cn.plot(ax=ax, color=fk.C.MAIN, lw=0.45, alpha=0.85, zorder=5)
    if len(rq):
        ax.scatter(rq.X, rq.Y, s=13, marker="x", linewidths=0.9, color=fk.C.STATION,
                   zorder=7)

    counts = sel[sel.UNSERVED].BUCKET.value_counts().to_dict()
    loads = sel[sel.UNSERVED].groupby("BUCKET").Q_AVG_M3D.sum().to_dict()
    handles = [Patch(facecolor=CONNECTED, edgecolor=CONNECTED_INK,
                     label=f"connected  ({len(conn_sel):,})")]
    handles += [h for h, rr in zip(reason_legend(counts, loads), REASONS)
                if counts.get(rr, 0)]
    handles += [Line2D([], [], color=fk.C.MAIN, lw=1.1,
                       label=f"published property connection ({len(cn):,})"),
                Line2D([], [], color=fk.C.STATION, marker="x", ls="none", ms=5,
                       label=f"chamber / corridor request ({len(rq):,})")]
    box = (f"plots in frame   {len(sel):>8,}\n"
           f"unconnected      {n_un:>8,}  {100*n_un/max(len(sel),1):>4.1f} %\n"
           f"flow in frame    {q_all:>8,.0f} m3/d\n"
           f"unconnected flow {q_un:>8,.0f} m3/d  {100*q_un/max(q_all,1e-9):>4.1f} %")
    fk.finish_map(fig, ax, legend_handles=handles, legend_loc="upper left", databox=box,
                  note=note, source=fk.source_line(d.plots, d.unas, d.conn, d.req))
    path = fk.save(fig, "FS03_reasons_zoom")
    return (path,
            "The five reasons a plot is not connected, drawn at 1.5 km where they can be "
            f"told apart. This frame holds {q_un:,.0f} m3/d of unconnected load, "
            f"{100*q_un/max(q_all,1e-9):.0f} % of everything in it.",
            f"in the densest 1.5 km, {100*q_un/max(q_all,1e-9):.0f} % of the flow is "
            f"unconnected ({q_un:,.0f} of {q_all:,.0f} m3/d in the frame; the 3x3 grid "
            f"block it was chosen on holds {win_q:,.0f})")


# ------------------------------------------------------------------------------ S04

def S04(d: Data):
    """What the 45 m rule actually costs, and by how little most plots miss it."""
    s = d.leg_lengths()
    legs = s.LEG_M.values
    q = s.Q_ADF_M3D.values
    if not len(s):
        raise SystemExit("S04: no plot is over the 45 m limit in the current layers — "
                         "nothing to draw, and nothing invented in its place.")
    med = float(np.median(legs))
    short = legs - 45.0
    frac10 = 100.0 * float((short <= 10.0).mean())
    # The tail runs to hundreds of metres whenever the carrier set is thin, so the axis
    # is cut at the 97th percentile and the remainder is stated rather than squashed.
    cap = float(max(60.0, np.ceil(np.percentile(legs, 97) / 5.0) * 5.0))
    n_beyond = int((legs > cap).sum())
    q_beyond = float(q[legs > cap].sum())

    fig, axes = fk.chart_frame(
        title=(f"{frac10:.0f} % of the plots past the 45 m limit miss it by 10 m or less "
               f"— median tertiary path {med:.0f} m against a 45 m allowance"),
        subtitle=d.caveat(
            "Left: the tertiary path length to the nearest chamber, for every plot stage "
            "5b could not connect on that ground. Right: the load that comes back if the "
            "tertiary allowance were longer. The 45 m is a guideline value (G203-p22 "
            "Table 6, Lateral Sewer row) and is NOT ours to relax — the curve prices the "
            "rule, it does not propose changing it."),
        figsize=(12.2, 4.9), ncols=2)

    ax = axes[0]
    step = 2.5 if cap <= 120 else 5.0
    bins = np.arange(45, cap + step, step)
    ax.hist(np.clip(legs, 45, cap), bins=bins, color=REASON_COLOR["leg over 45 m"],
            edgecolor=fk.C.INK, linewidth=0.4, zorder=3)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.18)
    ax.axvline(45.0, color=fk.C.FAIL, lw=1.3, zorder=4)
    ax.text(45 + (cap - 45) * 0.03, ax.get_ylim()[1] * 0.985,
            "45 m — G203-p22 Tab 6,\nLateral Sewer row", fontsize=7.0, color=fk.C.FAIL,
            va="top")
    if med <= cap:
        ax.axvline(med, color=fk.C.INK, lw=1.0, ls="--", zorder=4)
        ax.text(med + (cap - 45) * 0.02, ax.get_ylim()[1] * 0.70, f"median {med:.1f} m",
                fontsize=7.0, color=fk.C.INK, va="top")
    ax.set_xlabel(f"tertiary path to the nearest chamber (m), clipped at {cap:.0f}")
    ax.set_ylabel(f"plots  (n = {len(s):,})")
    fk.thousands(ax, "y")
    if n_beyond:
        ax.text(0.985, 0.62,
                f"{n_beyond:,} plots ({q_beyond:,.0f} m3/d)\nlie beyond {cap:.0f} m, worst "
                f"{legs.max():,.0f} m", transform=ax.transAxes, ha="right", fontsize=6.9,
                color=fk.C.INK,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#c9c9c9"))

    ax = axes[1]
    grid = np.arange(45.0, cap + 1.0, 1.0)
    rec_q = np.array([q[legs <= g].sum() for g in grid])
    ax.plot(grid, rec_q, color=REASON_COLOR["leg over 45 m"], lw=2.0, zorder=4)
    ax.fill_between(grid, 0, rec_q, color=REASON_COLOR["leg over 45 m"], alpha=0.18,
                    zorder=2)
    marks = [g for g in (50.0, 60.0, 75.0, 100.0, 150.0) if 45 < g <= cap][:3]
    for g in marks:
        v = float(q[legs <= g].sum())
        ax.plot([g, g], [0, v], color=fk.C.GREY, lw=0.7, ls=":", zorder=3)
        ax.annotate(f"{g:.0f} m -> {v:,.0f} m3/d\n({100*v/d.q_total:.2f} % of ultimate,"
                    f" {int((legs<=g).sum()):,} plots)",
                    xy=(g, v), xytext=(g + (cap - 45) * 0.02, v * 0.60), fontsize=6.6,
                    color=fk.C.INK,
                    arrowprops=dict(arrowstyle="-", color=fk.C.GREY, lw=0.6))
    ax.set_xlabel("tertiary allowance if it were relaxed to (m)")
    ax.set_ylabel("unconnected load recovered (m3/d)")
    ax.set_xlim(45, cap)
    ax.set_ylim(0, max(rec_q.max(), q.sum()) * 1.22)
    fk.thousands(ax, "y")
    ax.text(0.985, 0.06,
            f"the whole group is {q.sum():,.0f} m3/d, "
            f"{100*q.sum()/d.q_total:.2f} % of ultimate flow;\n{rec_q[-1]:,.0f} m3/d of it "
            f"is inside {cap:.0f} m",
            transform=ax.transAxes, ha="right", fontsize=6.8, color=fk.C.GREY)

    fk.finish_chart(fig, source=fk.source_line(d.unas, d.psys))
    path = fk.save(fig, "FS04_45m_rule_cost")
    return (path,
            f"How far past 45 m the unreachable plots sit, and what the rule costs: "
            f"{frac10:.0f} % miss by 10 m or less, and the whole group is "
            f"{100*q.sum()/d.q_total:.2f} % of ultimate flow.",
            f"{frac10:.0f} % of the over-45 m plots miss the limit by 10 m or less; "
            f"median tertiary path {med:.0f} m, worst {legs.max():,.0f} m")


# ------------------------------------------------------------------------------ S05

def S05(d: Data):
    """Why the 45 m rule bites: the offset, not chamber spacing."""
    m = d.m5b
    o50, o90 = float(m["offset_p50_m"]), float(m["offset_p90_m"])
    s50, s90 = float(m["chamber_spacing_p50_m"]), float(m["chamber_spacing_p90_m"])
    T12 = 100.0        # G203-p30 Table 12, 200-315 mm: maximum spacing between manholes
    LIM = 45.0         # G203-p22 Table 6, Lateral Sewer: "Maximum Length 45 m"
    HCC = 2.5          # G203-p17 sec 3.2: HCC 2.5 m into the ROW

    fig, axes = fk.chart_frame(
        title=("The 45 m allowance is spent getting off the plot, not walking to the "
               "chamber"),
        subtitle=d.caveat(
                  f"Left: how much of the 45 m tertiary allowance the boundary-to-carrier "
                  f"offset takes at the median plot and at the 90th percentile. Right: "
                  f"the chamber spacing that leaves, S = 2 x (45 - offset), against the "
                  f"100 m maximum G203-p30 Table 12 allows for a 200-315 mm sewer. "
                  f"Chamber spacing is not the binding constraint at the median and "
                  f"cannot be made one at the tail."),
        figsize=(12.2, 4.6), ncols=2)

    ax = axes[0]
    rows = [(f"median plot\noffset {o50:.2f} m", o50),
            (f"90th percentile\noffset {o90:.2f} m", o90)]
    y = np.arange(len(rows))[::-1]
    for yy, (lab, off) in zip(y, rows):
        ax.barh(yy, min(off, LIM), height=0.44, facecolor=REASON_COLOR["no carrier in range"],
                edgecolor=fk.C.INK, lw=0.6, hatch="xx", zorder=3)
        ax.barh(yy, max(LIM - off, 0.0), left=min(off, LIM), height=0.44,
                facecolor=REASON_COLOR["outside boundary"], edgecolor=fk.C.INK, lw=0.6,
                zorder=3)
        ax.text(min(off, LIM) / 2, yy, f"{off:.1f} m", ha="center", va="center",
                fontsize=7.4, color="white", fontweight="bold")
        ax.text(min(off, LIM) + max(LIM - off, 0.0) / 2, yy,
                f"{max(LIM-off,0.0):.1f} m left", ha="center", va="center", fontsize=7.4,
                color=fk.C.INK)
    ax.axvline(LIM, color=fk.C.FAIL, lw=1.3, zorder=5)
    ax.text(LIM - 0.6, 1.42, "45 m — G203-p22 Tab 6", fontsize=7.0, color=fk.C.FAIL,
            ha="right")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.4)
    ax.set_xlim(0, LIM * 1.06)
    ax.set_ylim(-0.6, 1.7)
    ax.set_xlabel("the 45 m tertiary allowance (m)")
    fk.legend_below(ax, [
        Patch(facecolor=REASON_COLOR["no carrier in range"], edgecolor=fk.C.INK,
              hatch="xx", label="plot boundary to carrier centreline"),
        Patch(facecolor=REASON_COLOR["outside boundary"], edgecolor=fk.C.INK,
              label="left for the run along the carrier"),
    ], ncol=2, drop=0.42)

    ax = axes[1]
    bars = [(f"at the median\noffset {o50:.2f} m", s50, REASON_COLOR["corridor through plot"]),
            (f"at the 90th pct\noffset {o90:.2f} m", s90, REASON_COLOR["cannot drain"])]
    xs = np.arange(len(bars))
    for x, (lab, v, col) in zip(xs, bars):
        ax.bar(x, v, width=0.5, facecolor=col, edgecolor=fk.C.INK, lw=0.6, zorder=3)
        ax.text(x, v + 2.5, f"{v:.1f} m", ha="center", fontsize=8.4, fontweight="bold",
                color=fk.C.INK)
    ax.axhline(T12, color=fk.C.FAIL, lw=1.3, zorder=4)
    ax.text(-0.42, T12 + 2.5, "100 m — G203-p30 Table 12 maximum, 200-315 mm",
            fontsize=7.0, color=fk.C.FAIL, ha="left")
    ax.set_xticks(xs)
    ax.set_xticklabels([b[0] for b in bars], fontsize=7.4)
    ax.set_ylim(0, T12 * 1.55)
    ax.set_xlim(-0.55, len(bars) - 0.45)
    ax.set_ylabel("chamber spacing the allowance leaves (m)", labelpad=1)
    ax.text(0.5, 0.90,
            f"The HCC sits {HCC:.1f} m into the ROW (G203-p17 sec 3.2), so the 45 m is "
            f"spent as offset\nfirst and run-along second. At the median plot the spacing "
            f"the rule allows is {s50:.0f} m —\nwell inside Table 12's maintenance "
            f"maximum. At the 90th percentile it is {s90:.0f} m, which no\nmaintenance "
            f"rule ever asked for: the tail is a corridor problem, not a chamber problem.",
            transform=ax.transAxes, ha="center", va="center", fontsize=6.9,
            color=fk.C.INK,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#c9c9c9"))

    fk.finish_chart(fig, source=fk.source_line(d.m5b_src))
    path = fk.save(fig, "FS05_offset_not_spacing")
    return (path,
            f"The offset from the plot boundary to the carrier spends {o50:.1f} m of the "
            f"45 m allowance at the median plot and {o90:.1f} m at the 90th percentile; "
            "chamber spacing is not what makes the rule bite.",
            f"offset p50 {o50:.2f} m / p90 {o90:.2f} m spends the 45 m, not spacing")


# ------------------------------------------------------------------------------ S06

def S06(d: Data):
    """Whether the drainability test ran at all, and what it said when it did.

    Two states, and the figure draws whichever is true rather than assuming one:

    * the chambers carry inverts, so every connection was solved against a real level —
      the figure is the distribution of the shortfall on the ones that failed;
    * the chambers carry no inverts, so nothing was solved — the figure says every
      connection is UNTESTED, which is the project's own doctrine (a check that cannot
      run is a failure, not a blank) and not a pass.
    """
    s = d.drain_shortfall()
    if not len(s):
        return _S06_untested(d)
    v = s.SHORT_M.values
    q = s.Q_ADF_M3D.values
    under = 0.50
    p_under = 100.0 * float((v < under).mean())
    q_under = float(q[v < under].sum())
    q_all = float(q.sum())

    seed_ok = (len(d.mh_depth_unique) == 1)
    seed = d.mh_depth_unique[0] if seed_ok else None

    fig, axes = fk.chart_frame(
        title=(f"The biggest single reason is a levelling artefact: {p_under:.0f} % miss "
               f"the invert by under {under*100:.0f} cm"),
        subtitle=(f"{len(s):,} plots carrying {q_all:,.0f} m3/d "
                  f"({d.pct_load(q_all):.2f} % of ultimate flow) were failed because the "
                  f"connection arrives below the chamber's discharge invert at the 1 % "
                  f"minimum (G203-p18 Table 5, Lateral / Rider Sewer). "
                  + (f"But all {d.mh_n:,} chambers still sit at the stage-5 seed "
                     f"DEPTH_M {seed:.3f} m — no level has been solved yet, so this test "
                     f"was run against a placeholder and the group will move."
                     if seed_ok else
                     f"Chamber depths on the stage-5 mirror are no longer a single seed "
                     f"({len(d.mh_depth_unique)} distinct values) — re-read before "
                     f"quoting this figure.")),
        figsize=(12.2, 4.8), ncols=2)

    ax = axes[0]
    bins = np.linspace(0, 2.0, 41)
    ax.hist(np.clip(v, 0, 2.0), bins=bins, color=REASON_COLOR["cannot drain"],
            edgecolor=fk.C.INK, linewidth=0.35, zorder=3)
    ax.axvline(under, color=fk.C.FAIL, lw=1.3, zorder=4)
    ax.text(under + 0.03, ax.get_ylim()[1] * 0.92,
            f"{under:.2f} m\n{p_under:.1f} % of plots are left of this",
            fontsize=7.0, color=fk.C.FAIL, va="top")
    ax.set_xlabel("how far the connection arrives below the discharge invert (m), "
                  "clipped at 2.0")
    ax.set_ylabel(f"plots  (n = {len(s):,})")
    ax.text(0.98, 0.60, f"median {np.median(v):.2f} m\n90th pct {np.percentile(v,90):.2f} m"
                        f"\nworst {v.max():.2f} m",
            transform=ax.transAxes, ha="right", fontsize=7.2, color=fk.C.INK,
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#c9c9c9"))

    ax = axes[1]
    grid = np.linspace(0, min(2.0, float(v.max())), 120)
    cum = np.array([q[v <= g].sum() for g in grid])
    ax.plot(grid, cum, color=REASON_COLOR["cannot drain"], lw=2.0, zorder=4)
    ax.fill_between(grid, 0, cum, color=REASON_COLOR["cannot drain"], alpha=0.16, zorder=2)
    ax.axvline(under, color=fk.C.FAIL, lw=1.3, zorder=5)
    ax.annotate(f"{q_under:,.0f} m3/d "
                f"({d.pct_load(q_under):.2f} % of ultimate)\nturns on {under*100:.0f} cm "
                f"of chamber invert",
                xy=(under, q_under), xytext=(under + 0.22, q_under * 0.52), fontsize=7.0,
                color=fk.C.INK,
                arrowprops=dict(arrowstyle="->", color=fk.C.GREY, lw=0.8),
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#9a9a9a"))
    ax.set_xlabel("shortfall allowed for (m)")
    ax.set_ylabel("load that would connect (m3/d)")
    ax.set_ylim(0, q_all * 1.12)
    fk.thousands(ax, "y")
    beyond = float(q[v > grid.max()].sum())
    ax.text(0.985, 0.035,
            f"all {len(s):,} have a connection DRAWN and published —\ncounted "
            f"unconnected, not omitted. A further {beyond:,.0f} m3/d\nneeds more than "
            f"{grid.max():.1f} m and is off the right of this axis.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.8,
            color=fk.C.GREY)

    fk.finish_chart(fig, source=fk.source_line(d.unas, d.mh_src, d.psys))
    path = fk.save(fig, "FS06_drainability_state")
    return (path,
            f"The 'cannot drain' group, {d.pct_load(q_all):.2f} % of ultimate flow, "
            f"measured against chambers that are all still at their stage-5 seed depth: "
            f"{p_under:.0f} % of it turns on less than {under*100:.0f} cm of invert.",
            f"{p_under:.0f} % of the cannot-drain group misses by under {under*100:.0f} cm, "
            "against placeholder levels")


def _S06_untested(d: Data):
    """No plot failed on drainability — because nothing was tested.  Say exactly that."""
    cn = d.conn
    n = len(cn)
    pend = int(d.n_levels_pending)
    solved = n - pend
    q_pend = float(cn.loc[cn.WHY.str.contains("LEVELS PENDING", regex=False),
                          "Q_ADF_M3D"].sum())
    seed_ok = len(d.mh_depth_unique) == 1
    seed = d.mh_depth_unique[0] if seed_ok else None

    fig, axes = fk.chart_frame(
        title=(f"Zero plots fail on drainability — because none of the {n:,} connections "
               f"was tested"),
        subtitle=(
            f"Every published connection carries \"LEVELS PENDING\": its gradient is the "
            f"G203-p18 Table 5 minimum DECLARED, not solved, and the arrival at the "
            f"chamber is unchecked. "
            + (f"The chamber layer agrees — all {d.mh_n:,} chambers sit at the stage-5 "
               f"seed DEPTH_M {seed:.3f} m, the shallowest legal invert at 1.30 m cover "
               f"(G203-p33). " if seed_ok else "")
            + "An empty failure list here is the absence of a test, not a clean result, "
              "and the auditor's own rule is that a check which cannot run is a failure."),
        figsize=(12.2, 3.8), ncols=2)

    ax = axes[0]
    for i, (lab, val, role) in enumerate((
            ("levels SOLVED\nagainst a chamber invert", solved, "pass"),
            ("levels PENDING\ngradient declared at the minimum", pend, "untested"))):
        ax.barh(1 - i, val, height=0.5, zorder=3, **fk.status_style(role))
        ax.text(max(val, n * 0.02) + n * 0.015, 1 - i,
                f"{val:,} connections   {100*val/max(n,1):.1f} %", va="center",
                fontsize=7.6, color=fk.C.INK)
    ax.set_yticks([1, 0])
    ax.set_yticklabels(["levels SOLVED\nagainst a chamber invert",
                        "levels PENDING\ngradient declared, arrival unchecked"],
                       fontsize=7.2)
    ax.set_xlim(0, n * 1.55)
    ax.set_xlabel(f"published property connections (of {n:,})")
    fk.thousands(ax, "x")

    ax = axes[1]
    rows = [("drains — checked and passed", 0.0, "pass"),
            ("does not drain — checked and failed", 0.0, "fail"),
            ("NOT CHECKED — no chamber invert exists", q_pend, "untested")]
    y = np.arange(len(rows))[::-1]
    for yy, (lab, val, role) in zip(y, rows):
        ax.barh(yy, val, height=0.5, zorder=3, **fk.status_style(role))
        ax.text(max(val, d.q_conn * 0.02) + d.q_conn * 0.02, yy,
                f"{val:,.0f} m3/d   {100*val/max(d.q_conn,1e-9):.1f} % of the connected "
                f"load", va="center", fontsize=7.4, color=fk.C.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.2)
    ax.set_xlim(0, d.q_conn * 1.85)
    ax.set_xlabel("ultimate average day flow reaching a chamber (m3/d)")
    fk.thousands(ax, "x")

    fk.finish_chart(fig, source=fk.source_line(cn, d.mh_src))
    path = fk.save(fig, "FS06_drainability_state")
    return (path,
            f"The drainability of the tertiary network is currently UNTESTED: all {n:,} "
            f"connections carry declared gradients, not solved ones, and the chambers "
            f"carry no inverts. An empty failure list here is not a pass.",
            f"0 plots fail on drainability because all {n:,} connections are untested — "
            f"levels pending, chambers still at their stage-5 seed")


# ------------------------------------------------------------------------------ S07

def S07(d: Data):
    """Which RULE decided each settlement, and the fall-back that never fires.

    NOT a map of which system serves what — ``fig_overview.py`` already draws that as
    ``FO02_system_by_settlement.png`` and draws it better. This answers the question that
    map cannot: which decision RULE each settlement was decided by, and what happens to
    the settlements the cost test cannot touch because they carry no load at all.
    """
    sv = d.serv
    RULE_NOTE = {
        "CORE": "the core itself — no exclusive sewer to price",
        "COST": "priced: exclusive m per property against the project break",
        "G201-p83": "on-site or package plant — G201-p83 sec 8.4.1",
        "PHIL-8a": "BOTH options carried — philosophy sec 8a",
        "ZERO-LOAD": "no load, so the cost test has NO DENOMINATOR",
    }
    g = sv.groupby("DEC_RULE").agg(n=("SET_ID", "size"), q=("Q_ADF_M3D", "sum"),
                                   plots=("N_PLOT", "sum"), kmax=("KM_CORE", "max"))
    order = [k for k in ("CORE", "COST", "G201-p83", "PHIL-8a", "ZERO-LOAD")
             if k in g.index]

    zl = sv[sv.DEC_RULE == "ZERO-LOAD"]
    G201_REMOTE_KM = 25.0        # G201-p80 sec 8.1, second bullet — quoted from the page
    far = float(zl.KM_CORE.max()) if len(zl) else float("nan")
    fires = int((zl.KM_CORE >= G201_REMOTE_KM).sum()) if len(zl) else 0

    fig, axes = fk.chart_frame(
        title=(f"The zero-load fall-back never fires: the furthest of the {len(zl)} "
               f"load-free settlements is {far:.2f} km from the core, against a 25 km test"),
        subtitle=(f"Left: which rule decided each of the {len(sv)} settlements, and the "
                  f"load behind it. Right: a settlement carrying no wastewater load has "
                  f"no denominator for the cost test, so stage 1 falls back to the only "
                  f"NUMERIC distance test G201-p80 sec 8.1 offers — \"approximately 25 km "
                  f"or more from existing centralized water or wastewater networks\". On "
                  f"this data it selects nothing, so all {len(zl)} connect at no marginal "
                  f"cost. Whether they carry load at all is a data question for the GIS "
                  f"expert's treated land-use file, not a design one."),
        figsize=(12.2, 4.8), ncols=2)
    fig.subplots_adjust(left=0.185)

    ax = axes[0]
    cols = {"CORE": fk.C.SUBMAIN, "COST": REASON_COLOR["leg over 45 m"],
            "G201-p83": REASON_COLOR["outside boundary"],
            "PHIL-8a": REASON_COLOR["corridor through plot"],
            "ZERO-LOAD": fk.C.UNTESTED}
    hats = {"CORE": None, "COST": "//", "G201-p83": "..", "PHIL-8a": "xx",
            "ZERO-LOAD": "\\\\"}
    y = np.arange(len(order))[::-1]
    nmax = float(g.n.max())
    for yy, k in zip(y, order):
        ax.barh(yy, g.loc[k, "n"], height=0.55, facecolor=cols[k], edgecolor=fk.C.INK,
                lw=0.6, hatch=hats[k], zorder=3)
        nk = int(g.loc[k, "n"])
        ax.text(g.loc[k, "n"] + nmax * 0.02, yy,
                f"{nk} settlement{'' if nk == 1 else 's'}   {g.loc[k,'q']:,.0f} m3/d   "
                f"({d.pct_load(float(g.loc[k,'q'])):.2f} % of load)",
                va="center", fontsize=7.2, color=fk.C.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{k}\n{RULE_NOTE.get(k,'')}" for k in order], fontsize=6.9)
    ax.set_xlim(0, nmax * 2.5)
    ax.set_xlabel(f"settlements decided by that rule (of {len(sv)})")

    ax = axes[1]
    if len(zl):
        v = np.sort(zl.KM_CORE.values)
        ax.scatter(v, np.arange(len(v)) + 1, s=26, marker="o",
                   facecolor=fk.C.UNTESTED, edgecolor=fk.C.INK, linewidth=0.5,
                   zorder=4, label=f"the {len(zl)} zero-load settlements")
        ax.axvline(G201_REMOTE_KM, color=fk.C.FAIL, lw=1.4, zorder=5)
        ax.text(G201_REMOTE_KM - 0.5, len(v) * 0.55,
                "25 km — G201-p80 sec 8.1:\n\"approximately 25 km or more from\nexisting "
                "centralized … networks\"", ha="right", fontsize=7.0, color=fk.C.FAIL,
                va="center")
        ax.annotate(f"furthest {far:.2f} km", xy=(far, len(v)), xytext=(6, -10),
                    textcoords="offset points", fontsize=7.0, color=fk.C.INK)
        ax.set_xlim(0, G201_REMOTE_KM * 1.16)
        ax.set_ylim(0, len(v) * 1.16)
        ax.set_xlabel("envelope distance from the settlement to the core (km)")
        ax.set_ylabel(f"zero-load settlements, ranked  (n = {len(zl)})")
        ax.text(0.985, 0.06,
                f"{fires} of {len(zl)} meet the 25 km test, so {len(zl)-fires} are held on "
                f"the central network\nat 0 exclusive metres. They carry "
                f"{zl.Q_ADF_M3D.sum():,.1f} m3/d and {int(zl.N_PLOT.sum()):,} plots.",
                transform=ax.transAxes, ha="right", fontsize=6.9, color=fk.C.INK,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#c9c9c9"))
    fk.finish_chart(fig, source=fk.source_line(
        sv, "PAM-GUD-201 p80 sec 8.1, second bullet, quoted from the page"))
    path = fk.save(fig, "FS07_decision_rules")
    return (path,
            f"Which rule decided each of the {len(sv)} settlements. The {len(zl)} that "
            f"carry no load cannot be priced at all, so they fall back to G201-p80's 25 km "
            f"distance test — which selects {fires} of them, the furthest being "
            f"{far:.2f} km out.",
            f"the zero-load fall-back never fires: furthest of {len(zl)} load-free "
            f"settlements is {far:.2f} km from core against a 25 km test")

# ------------------------------------------------------------------------------ S08

def S08(d: Data):
    """How much the servicing split depends on where the cost break is drawn."""
    b = d.brk.sort_values("break_m_per_prop")
    sv = d.serv
    chosen = float(sv.BREAK_M.iloc[0])
    band = (18.0, 25.0)

    # which settlement flips between the two lowest breaks that straddle the cliff?
    diffs = b.properties_off_network.diff(-1)
    icliff = int(np.nanargmax(diffs.values)) if len(b) > 1 else 0
    lo, hi = float(b.break_m_per_prop.iloc[icliff]), float(b.break_m_per_prop.iloc[icliff + 1])
    flips = sv[(sv.M_PER_PRP >= lo) & (sv.M_PER_PRP < hi)].nlargest(1, "N_PROP")

    fig, axes = fk.chart_frame(
        title=(f"The servicing split is stable from {band[0]:.0f} to "
               f"{b.break_m_per_prop.max():.0f} m per property, and falls off a cliff "
               f"below {hi:.0f}"),
        subtitle=(f"The cost break is a PROJECT threshold, not a guideline value: G201-p80 "
                  f"sec 8.1 asks for \"geographical barriers preventing economical "
                  f"connection\" and gives no number. It is set at {chosen:.0f} m of "
                  f"exclusive sewer per property. This is the sweep that says how much "
                  f"the answer depends on that choice."),
        figsize=(12.2, 4.8), ncols=2)

    for ax, col, lab, colr in (
            (axes[0], "pct_of_properties", "properties off the central network (%)",
             REASON_COLOR["no carrier in range"]),
            (axes[1], "pct_of_load", "ultimate load off the central network (%)",
             REASON_COLOR["cannot drain"])):
        ax.plot(b.break_m_per_prop, b[col], color=colr, lw=2.0, marker="o", ms=4,
                zorder=4)
        ax.axvspan(band[0], band[1], color=fk.C.PASS, alpha=0.35, zorder=1)
        ax.axvline(chosen, color=fk.C.INK, lw=1.2, ls="--", zorder=5)
        ax.set_xscale("log")
        ax.set_xticks([10, 15, 20, 30, 50, 100, 150])
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.set_xlabel("cost break (m of exclusive sewer per property)")
        ax.set_ylabel(lab)
        ax.set_ylim(0, max(b[col]) * 1.25)
        for i, (_, r) in enumerate(b.iterrows()):
            ax.annotate(f"{r[col]:.2f}", xy=(r.break_m_per_prop, r[col]),
                        xytext=(0, 7 if i % 2 == 0 else 16), textcoords="offset points",
                        ha="center", fontsize=6.2, color=fk.C.GREY)

    axes[0].text(chosen * 1.06, max(b.pct_of_properties) * 1.12,
                 f"chosen break {chosen:.0f} m/property\n"
                 f"(PROJECT threshold, not a guideline value)",
                 fontsize=6.9, color=fk.C.INK, ha="left", va="top")
    axes[0].text(band[0] * 1.03, max(b.pct_of_properties) * 0.30,
                 f"{band[0]:.0f}-{band[1]:.0f} m: the flip band.\nA settlement decided in "
                 f"here is\npublished PROVISIONAL", fontsize=6.6, color=fk.C.INK)
    if len(flips):
        f = flips.iloc[0]
        axes[0].annotate(
            f"the cliff is one settlement:\n{f.SET_ID} {str(f.NAME).strip()} at "
            f"{f.M_PER_PRP:.2f} m/property,\n{f.N_PROP:,.0f} properties and "
            f"{f.Q_ADF_M3D:,.0f} m3/d",
            xy=(lo, float(b.pct_of_properties.iloc[icliff])),
            xytext=(34.0, max(b.pct_of_properties) * 0.66), fontsize=6.8,
            color=fk.C.INK, ha="left",
            arrowprops=dict(arrowstyle="->", color=fk.C.FAIL, lw=0.9),
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=fk.C.FAIL, alpha=0.94))

    fk.finish_chart(fig, source=fk.source_line(d.brk, d.serv))
    path = fk.save(fig, "FS08_breakeven_sensitivity")
    return (path,
            "How much the central-versus-on-site split moves with the cost break. Flat "
            f"from {band[0]:.0f} m upward; below {hi:.0f} m one large settlement flips "
            "and takes a sixth of the properties with it.",
            f"the split is flat above {band[0]:.0f} m/property and collapses below "
            f"{hi:.0f} m on one settlement")


# ------------------------------------------------------------------------------ S09

def S09(d: Data):
    """Only one of G201-p80's four remote-area tests discriminates on this data."""
    sv = d.serv
    n = len(sv)
    size = int(((sv.POP < 500) | (sv.N_PLOT < 100)).sum())
    far = int((sv.KM_BUILT >= 25.0).sum())
    econ = int((sv.SYSTEM != "central").sum())

    # The first criterion is NOT measured here, and it is drawn as UNTESTED rather than
    # asserted: nothing in the published layers records which settlements are connected to
    # the existing 2006 network today.  A bar of 187 would have been an invention.
    rows = [("\"Not connected to existing centralised\nwater or wastewater networks\"",
             None, "NOT MEASURABLE from the published layers — no connection status "
                   "is recorded"),
            ("\"Communities with population less than 500\nresidents or fewer than 100 "
             "plots\"", size, "selects almost everything — the cadastre fragments into "
                              "one- and two-plot pieces"),
            ("\"Settlements located approximately 25 km or\nmore from existing "
             "centralized networks\"", far, "selects almost nothing — Ibri is compact"),
            ("\"Areas with geographical barriers preventing\neconomical connection\" — "
             "read as m of exclusive sewer per property", econ,
             "THE OPERATIVE TEST — and its threshold is OURS")]

    fig, ax = fk.chart_frame(
        title=("Only one of G201's four remote-area tests can decide anything here — and "
               "it is the one with no number in it"),
        subtitle=(f"G201-p80 sec 8.1 defines a Remote Area by four ALTERNATIVE criteria, "
                  f"so meeting any one is enough. Measured against the {n} settlements in "
                  f"this study, the size test selects {size} of them and the distance test "
                  f"{far}; neither separates the study area. The fourth criterion carries "
                  f"no number at all, so the metres of exclusive sewer per property stands "
                  f"in for it — that ratio, and the 20 m break applied to it, are PROJECT "
                  f"choices, not guideline values (see S08 for how much they matter)."),
        figsize=(11.4, 4.6), ygrid=False, xgrid=True)
    fig.subplots_adjust(left=0.255, right=0.995)

    y = np.arange(len(rows))[::-1]
    cols = [None, REASON_COLOR["corridor through plot"],
            REASON_COLOR["outside boundary"], REASON_COLOR["cannot drain"]]
    for yy, (lab, v, note), col in zip(y, rows, cols):
        if v is None:
            # full-width band, so it reads as "no answer on this row" and never as a count
            ax.barh(yy, n * 1.95, height=0.52, zorder=3, **fk.status_style("untested"))
            ax.text(n * 0.975, yy, f"NOT MEASURED — {note.split('—')[1].strip()}",
                    ha="center", va="center", fontsize=7.6,
                    color=fk.label_ink("untested"), fontweight="bold")
            continue
        ax.barh(yy, v, height=0.52, facecolor=col, edgecolor=fk.C.INK, lw=0.6, zorder=3)
        ax.text(v + n * 0.015, yy, f"{v} of {n}   —   {note}", va="center", fontsize=7.2,
                color=fk.C.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.0)
    ax.set_xlim(0, n * 1.95)
    ax.set_xlabel(f"settlements meeting the test (of {n})")
    fk.finish_chart(fig, source=fk.source_line(
        sv, "PAM-GUD-201 p80 sec 8.1, four remote-area criteria, quoted from the page"))
    path = fk.save(fig, "FS09_remote_area_tests")
    return (path,
            f"G201-p80's four remote-area tests measured against the {n} settlements. Two "
            "cannot separate them, one cannot be measured from the published layers at "
            "all, and the fourth — the one the servicing decision actually rests on — "
            "carries no number in the guideline.",
            f"of G201's 4 remote-area tests, the size test takes {size} of {n} and the "
            f"25 km test {far}; the operative one has no number and its threshold is ours")


# ------------------------------------------------------------------------------ S10

def S10(d: Data):
    """How much of the unconnected load belongs to plots that do not exist yet."""
    p = d.plots
    CLASS_LABEL = {"B": "built", "P": "platted, nothing built", "A": "agricultural",
                   "U": "unparceled building"}
    order = ["B", "P", "A", "U"]
    conn = p[~p.UNSERVED].groupby("CLASS").Q_AVG_M3D.sum().reindex(order).fillna(0.0)
    unc = p[p.UNSERVED].groupby("CLASS").Q_AVG_M3D.sum().reindex(order).fillna(0.0)
    q_future_unc = float(unc.get("P", 0.0))
    q_today_unc = float(unc.sum() - q_future_unc)

    cats = (d.unas.groupby("CAT").Q_ADF_M3D.sum().sort_values(ascending=False))
    cats_n = d.unas.CAT.value_counts()

    fig, axes = fk.chart_frame(
        title=(f"{100*q_future_unc/d.q_unas:.0f} % of the unconnected load is on plots "
               f"with nothing built on them — today's shortfall is "
               f"{q_today_unc:,.0f} m3/d"),
        subtitle=d.caveat(
                  "Left: connected and unconnected load by plot class. 'P' is a platted "
                  "reserve at the saturation horizon — philosophy sec 4 requires it to be "
                  "identified separately and never reported as existing. Right: the "
                  "unconnected load by land-use category; the categories carrying none of "
                  "it are still thousands of plots."),
        figsize=(12.2, 4.9), ncols=2)

    ax = axes[0]
    x = np.arange(len(order))
    ax.bar(x, conn.values, width=0.60, facecolor=fk.C.PASS, edgecolor=fk.C.INK, lw=0.6,
           label="connected", zorder=3)
    ax.bar(x, unc.values, bottom=conn.values, width=0.60,
           facecolor=REASON_COLOR["no carrier in range"], edgecolor=fk.C.INK, lw=0.6,
           hatch="xx", label="unconnected", zorder=3)
    for xx, c, u in zip(x, conn.values, unc.values):
        ax.text(xx, c + u + d.q_total * 0.008,
                f"{100*u/max(c+u,1e-9):.0f} % unconnected", ha="center", fontsize=6.9,
                color=fk.C.INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{CLASS_LABEL[k]}\n({int((p.CLASS==k).sum()):,} plots)"
                        for k in order], fontsize=7.2)
    ax.set_ylabel("ultimate average day flow (m3/d)")
    ax.set_ylim(0, max(conn.values + unc.values) * 1.22)
    fk.thousands(ax, "y")
    ax.legend(loc="upper right", fontsize=7.2, framealpha=0.92, edgecolor="#9a9a9a")

    ax = axes[1]
    y = np.arange(len(cats))[::-1]
    ax.barh(y, cats.values, height=0.62,
            facecolor=REASON_COLOR["leg over 45 m"], edgecolor=fk.C.INK, lw=0.6, zorder=3)
    for yy, k, v in zip(y, cats.index, cats.values):
        ax.text(max(v, 0) + cats.max() * 0.015, yy,
                f"{v:,.0f} m3/d   ({int(cats_n[k]):,} plots)", va="center", fontsize=7.0,
                color=fk.C.INK)
    ax.set_yticks(y)
    ax.set_yticklabels(list(cats.index), fontsize=7.4)
    ax.set_xlim(0, cats.max() * 1.55)
    ax.set_xlabel(f"unconnected load by land-use category (m3/d), total "
                  f"{d.q_unas:,.0f}")
    fk.thousands(ax, "x")

    fk.finish_chart(fig, source=fk.source_line(d.plots, d.unas))
    path = fk.save(fig, "FS10_future_plots_and_landuse")
    return (path,
            f"The unconnected load split by whether the plot exists yet. "
            f"{100*q_future_unc/d.q_unas:.0f} % of it is on platted reserves; the load on "
            f"ground that is built today is {q_today_unc:,.0f} m3/d, "
            f"{100*q_today_unc/d.q_total:.1f} % of ultimate flow.",
            f"{100*q_future_unc/d.q_unas:.0f} % of the unconnected load is on plots not "
            "yet built")


# ------------------------------------------------------------------------------ S11

def S11(d: Data):
    """What the 45,232 published connections actually are — and who checks them."""
    cn = d.conn
    km_tert = float(cn.LEN_M.sum()) / 1000.0
    km_grav = float(d.flows.LEN_M.sum()) / 1000.0
    by = cn.groupby("CONN_TYPE").agg(n=("LEN_M", "size"),
                                     km=("LEN_M", lambda s: s.sum() / 1000.0),
                                     q=("Q_ADF_M3D", "sum"))
    # CONN_TYPE is set to "stub" exactly when the plot is a future (platted) plot; the
    # other two are the G203-p17 sec 3.2 chain, rider or straight to the chamber
    order = [t for t in ("stub", "lateral", "rider") if t in by.index]
    lab = {"stub": "capped stub — plot not built\n(G203-p19 sec 3.4)",
           "lateral": "lateral — plot stands at a chamber",
           "rider": "rider — grouped, then one lateral"}
    stub_km = float(by.loc["stub", "km"]) if "stub" in by.index else 0.0
    stub_n = int(by.loc["stub", "n"]) if "stub" in by.index else 0

    gap = next((n for n in d.m5b_notes if n.startswith("AUDIT GAP")), "")

    fig, axes = fk.chart_frame(
        title=(f"{stub_km:,.0f} km of the {km_tert:,.0f} km tertiary network is capped "
               f"stub-out for plots that are not built"),
        subtitle=d.caveat(
                  f"{len(cn):,} property connections, OD160 throughout (G203-p22 Table 6 "
                  f"minimum). Left: what they are. Right: the gradient each was laid at "
                  f"against the 1-10 % band G203-p18 Table 5 sets for a rider or lateral "
                  f"sewer — or, while the levels are pending and every gradient is the "
                  f"same declared minimum, the confidence grade instead. "
                  f"The tertiary is {100*km_tert/(km_tert+km_grav):.0f} % of every "
                  f"metre of pipe published so far ({km_tert:,.0f} km against "
                  f"{km_grav:,.0f} km of gravity reaches)."),
        figsize=(12.2, 4.9), ncols=2)

    ax = axes[0]
    cols = {"stub": REASON_COLOR["outside boundary"], "lateral": fk.C.SUBMAIN,
            "rider": fk.C.LATERAL}
    hat = {"stub": "..", "lateral": None, "rider": "//"}
    y = np.arange(len(order))[::-1]
    for yy, t in zip(y, order):
        ax.barh(yy, by.loc[t, "km"], height=0.55, facecolor=cols[t],
                edgecolor=fk.C.INK, lw=0.6, hatch=hat[t], zorder=3)
        ax.text(by.loc[t, "km"] + km_tert * 0.012, yy,
                f"{by.loc[t,'km']:,.0f} km   {int(by.loc[t,'n']):,} connections   "
                f"{by.loc[t,'q']:,.0f} m3/d", va="center", fontsize=7.2, color=fk.C.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([lab[t] for t in order], fontsize=7.2)
    ax.set_xlim(0, km_tert * 1.02)
    ax.set_xlabel("length of OD160 tertiary sewer (km)")
    if "stub" in by.index:
        ax.text(stub_km / 2, y[order.index("stub")],
                f"{100*stub_n/len(cn):.0f} % of the connections\n"
                f"{100*stub_km/km_tert:.0f} % of the length",
                ha="center", va="center", fontsize=7.4, color=fk.C.INK,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.85))

    ax = axes[1]
    s = cn.SLOPE_LAID.astype(float)
    if s.nunique() > 3:
        ax.hist(s, bins=np.arange(0.0, 10.6, 0.25), color=REASON_COLOR["leg over 45 m"],
                edgecolor=fk.C.INK, linewidth=0.35, zorder=3)
        for x in (1.0, 10.0):
            ax.axvline(x, color=fk.C.FAIL, lw=1.3, zorder=4)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.30)
        ax.text(1.25, ax.get_ylim()[1] * 0.97,
                f"G203-p18 Table 5, Rider / Lateral Sewer: 1 % to 10 %.\n"
                f"{int(((s >= 1.0) & (s <= 10.0)).sum()):,} of {len(cn):,} are inside it, "
                f"median {s.median():.2f} %.", fontsize=7.0, color=fk.C.INK, va="top")
        ax.set_xlabel("laid gradient of the tertiary leg (%)")
        ax.set_ylabel(f"connections  (n = {len(cn):,})")
        fk.thousands(ax, "y")
    else:
        # Every connection carries the same gradient, so a histogram would be one spike
        # dressed up as a distribution.  Show what IS varying — the confidence grade —
        # and say plainly that the gradient is declared rather than solved.
        conf = cn.CONFIDENCE.value_counts()
        role = {"provisional": "untested", "drafted": "flag", "derived": "pass",
                "surveyed": "pass"}
        yy = np.arange(len(conf))[::-1]
        for j, (k, v) in zip(yy, conf.items()):
            r = role.get(k, "flag")
            ax.barh(j, v, height=0.55, zorder=3, **fk.status_style(r))
            # inside the bar when it fits, so the right half stays free for the finding
            wide = v >= 0.42 * float(conf.max())
            ax.text(v * 0.97 if wide else v * 1.04, j,
                    f"{v:,}   {100*v/len(cn):.1f} %", ha="right" if wide else "left",
                    va="center", fontsize=7.4, zorder=4, fontweight="bold",
                    color=fk.label_ink(r) if wide else fk.C.INK)
        ax.set_yticks(yy)
        ax.set_yticklabels(list(conf.index), fontsize=7.4)
        ax.set_xlim(0, float(conf.max()) * 2.35)
        ax.set_xlabel(f"connections by CONFIDENCE (of {len(cn):,})")
        fk.thousands(ax, "x")
        ax.text(0.5, 0.03,
                f"every gradient is exactly {s.iloc[0]:.2f} % — the G203-p18 Table 5 "
                f"minimum DECLARED, not solved,\nso there is no distribution to show "
                f"until stage 6 runs",
                transform=ax.transAxes, ha="center", va="bottom", fontsize=7.0,
                color=fk.C.FAIL)
    if gap:
        import textwrap
        body = gap.split(". ")[0].replace("AUDIT GAP: ", "")
        msg = ("AUDIT GAP, in stage 5b's own words:\n\""
               + "\n".join(textwrap.wrap(body, 52)) + ".\"\n"
               + "\n".join(textwrap.wrap(
                   "Verified independently here: audit.py's 22 checks read only the "
                   "gravity reaches, the chamber nodes, the crossings, the roads and the "
                   "hazard grid — never this layer.", 52)))
        ax.text(0.72 if s.nunique() <= 3 else 0.5, 0.42, msg,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=6.6, color=fk.C.INK,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=fk.C.FAIL))

    fk.finish_chart(fig, source=fk.source_line(cn, d.flows, d.m5b_src))
    path = fk.save(fig, "FS11_connection_anatomy")
    grad_bit = (f"every one is laid inside G203-p18 Table 5's 1-10 % band"
                if s.nunique() > 3 else
                f"every gradient is still the declared {s.iloc[0]:.2f} % minimum rather "
                f"than a solved one")
    return (path,
            f"What the {len(cn):,} published property connections are: "
            f"{100*stub_n/len(cn):.0f} % are capped stubs for plots that do not exist, "
            f"{grad_bit}, and no audit check reads the layer.",
            f"{stub_km:,.0f} of {km_tert:,.0f} km of tertiary is stub-out for unbuilt "
            f"plots, and none of the 22 audit checks reads this layer")


# ------------------------------------------------------------------------------ S12

def S12(d: Data):
    """Why the cost break sits where it does — the distribution behind it."""
    sv = d.serv
    m = sv[sv.M_PER_PRP >= 0].copy()          # -1 is the zero-load sentinel, not a ratio
    sent = int((sv.M_PER_PRP < 0).sum())
    brk = float(sv.BREAK_M.iloc[0])
    band = (18.0, 25.0)
    below = m[m.M_PER_PRP < brk]
    above = m[m.M_PER_PRP >= brk]
    p_above = 100.0 * float(above.N_PROP.sum()) / float(m.N_PROP.sum())
    km_above = float(above.EXCL_KM.sum())
    m_per_below = 1000.0 * float(below.EXCL_KM.sum()) / max(float(below.N_PROP.sum()), 1)
    n_zero = int((m.M_PER_PRP == 0).sum())
    q_zero = float(m.loc[m.M_PER_PRP == 0, "Q_ADF_M3D"].sum())
    # A log axis has no place for zero, and 95 settlements genuinely need NO exclusive
    # sewer at all.  They get their own labelled strip left of a break rather than being
    # nudged onto the axis at a made-up small value.
    x_zero = 0.30
    lo_pos = float(m.loc[m.M_PER_PRP > 0, "M_PER_PRP"].min()) if (m.M_PER_PRP > 0).any() \
        else 1.0

    sys_color = {"central": fk.C.SUBMAIN, "satellite": REASON_COLOR["leg over 45 m"],
                 "onsite": REASON_COLOR["outside boundary"]}
    sys_marker = {"central": "o", "satellite": "^", "onsite": "s"}

    fig, ax = fk.chart_frame(
        title=(f"Above the break, {len(above)} settlements hold {p_above:.2f} % of the "
               f"properties on {km_above:,.0f} km of sewer that serves nobody else"),
        subtitle=(f"Every settlement that carries load, plotted by the metres of "
                  f"EXCLUSIVE sewer its connection would need per property. "
                  f"{n_zero} of the {len(m)} need NONE at all — they sit on shared "
                  f"corridors and are drawn in the strip at the far left, off the log "
                  f"axis rather than nudged onto it. Below the {brk:.0f} m break, "
                  f"{len(below)} settlements average {m_per_below:.1f} m each and hold "
                  f"{100-p_above:.2f} % of the properties. The {brk:.0f} m is a PROJECT "
                  f"threshold read off this distribution, not a guideline value; {sent} "
                  f"zero-LOAD settlements have no ratio at all and are not plotted."),
        figsize=(11.6, 5.6), xgrid=True)

    for s in ("central", "satellite", "onsite"):
        p = m[m.SYSTEM == s]
        if not len(p):
            continue
        x = np.where(p.M_PER_PRP.values <= 0, x_zero, p.M_PER_PRP.values)
        ax.scatter(x, p.N_PROP.clip(lower=1.0),
                   s=18 + 90 * np.sqrt(p.Q_ADF_M3D / max(m.Q_ADF_M3D.max(), 1e-9)),
                   marker=sys_marker[s], facecolor=sys_color[s], edgecolor=fk.C.INK,
                   linewidth=0.5, alpha=0.85, zorder=4,
                   label=f"{s}  ({len(p)})")
    ax.axvspan(band[0], band[1], color=fk.C.PASS, alpha=0.35, zorder=1)
    ax.axvline(brk, color=fk.C.INK, lw=1.3, ls="--", zorder=5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(x_zero / 1.7, 2000)
    ax.axvline(np.sqrt(x_zero * lo_pos), color=fk.C.GREY, lw=1.0, ls=(0, (2, 3)),
               zorder=5)
    ax.set_xlabel("metres of EXCLUSIVE sewer per property (log scale; 0 shown separately)")
    ax.set_ylabel("properties in the settlement (log scale)")
    ax.set_xticks([x_zero, 1, 10, 20, 100, 1000])
    ax.set_xticklabels(["0", "1", "10", "20", "100", "1000"])
    ax.text(x_zero, ax.get_ylim()[1] * 0.55,
            f"{n_zero} settlements need\nno exclusive sewer\n({q_zero:,.0f} m3/d)",
            ha="center", va="top", fontsize=6.8, color=fk.C.INK,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c9c9c9", alpha=0.92))

    for i, (_, r) in enumerate(m.nlargest(3, "N_PROP").iterrows()):
        ax.annotate(f"{r.SET_ID} {str(r.NAME).strip() or '-'}\n"
                    f"{r.N_PROP:,.0f} properties, {r.M_PER_PRP:.2f} m/prop",
                    xy=(r.M_PER_PRP if r.M_PER_PRP > 0 else x_zero, max(r.N_PROP, 1.0)),
                    xytext=(-95, 0), textcoords="offset points",
                    fontsize=6.8, color=fk.C.INK, ha="right", va="center",
                    arrowprops=dict(arrowstyle="-", color=fk.C.GREY, lw=0.6),
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#9a9a9a",
                              alpha=0.92))
    ax.annotate(f"{brk:.0f} m break\nPROJECT threshold",
                xy=(brk, 4e2), xytext=(9, 0), textcoords="offset points",
                ha="left", va="center", fontsize=7.0, color=fk.C.INK)
    ax.text(band[0] * 1.05, ax.get_ylim()[0] * 1.4,
            f"{band[0]:.0f}-{band[1]:.0f} m\nflip band", fontsize=6.8, color=fk.C.INK)
    ax.legend(loc="lower left", fontsize=7.2, framealpha=0.92, edgecolor="#9a9a9a",
              title="marker area = load", title_fontsize=6.8)

    fk.finish_chart(fig, source=fk.source_line(sv))
    path = fk.save(fig, "FS12_break_distribution")
    return (path,
            "The distribution the cost break was read off. The settlements above it are "
            f"small: {len(above)} of them hold {p_above:.2f} % of the properties but need "
            f"{km_above:,.0f} km of sewer serving nobody else, while {n_zero} of "
            f"{len(m)} need no exclusive sewer at all.",
            f"{len(above)} settlements above the {brk:.0f} m break hold {p_above:.2f} % of "
            f"properties on {km_above:,.0f} exclusive km; {n_zero} of {len(m)} need zero "
            f"exclusive sewer")


# --------------------------------------------------------------------------------- run

FIGURES = {"S01": S01, "S02": S02, "S03": S03, "S04": S04, "S05": S05,
           "S06": S06, "S07": S07, "S08": S08, "S09": S09, "S10": S10,
           "S11": S11, "S12": S12}

#: What a bare ``python fig_service.py`` draws.  S08 is EXCLUDED: fig_overview.py already
#: publishes the same break sweep as FO08_break_sensitivity.png and publishes it better —
#: one panel, three series, all three cliff settlements named.  S08 stays callable
#: (``python fig_service.py S08``) so the coverage is not lost if FO08 is ever withdrawn,
#: and S12 carries the part FO08 does not show: the distribution the break was read off.
DEFAULT = [k for k in FIGURES if k != "S08"]


def numbers(d: Data) -> None:
    """Print every headline value with the artefact it came from.  Draws nothing."""
    r = d.by_reason
    print(f"\nTOTALS   {fk.cite(d.psys)}")
    print(f"  plot records          {d.n_total:>10,}")
    print(f"  ultimate flow         {d.q_total:>10,.1f} m3/d")
    print(f"\nCONNECTED   {fk.cite(d.conn)}")
    print(f"  connections published {len(d.conn):>10,}   plots {d.conn.PID.nunique():,}")
    print(f"  plots connected       {d.n_conn:>10,}   {d.q_conn:,.1f} m3/d  "
          f"{d.pct_load(d.q_conn):.2f} %")
    print(f"  drawn but not draining{d.n_drawn_nodrain:>10,}   (counted unconnected)")
    print(f"\nUNCONNECTED   {fk.cite(d.unas)}")
    print(f"  {'reason':<26}{'plots':>8}{'m3/d':>12}{'% of ultimate':>15}")
    for k in REASONS:
        print(f"  {REASON_LABEL[k]:<26}{int(r.loc[k,'n']):>8,}{r.loc[k,'q']:>12,.1f}"
              f"{d.pct_load(float(r.loc[k,'q'])):>14.2f} %")
    print(f"  {'TOTAL':<26}{d.n_unas:>8,}{d.q_unas:>12,.1f}"
          f"{d.pct_load(d.q_unas):>14.2f} %")
    print(f"\nOFFSET (stage 5b's own metrics)   {d.m5b_src}")
    for k in ("offset_p50_m", "offset_p90_m", "chamber_spacing_p50_m",
              "chamber_spacing_p90_m", "shortfall_median_m", "shortfall_max_m",
              "tertiary_km", "qadf_m3d_to_chamber", "cannot_drain"):
        print(f"  {k:<26}{d.m5b[k]}")
    print(f"\nCHAMBER SEEDS   {d.mh_src}")
    print(f"  chambers {d.mh_n:,}   distinct DEPTH_M {d.mh_depth_unique}   "
          f"STAGE {d.mh_stage}")
    print(f"\nSERVICING   {fk.cite(d.serv)}")
    print(d.serv.groupby("SYSTEM").agg(n=("SET_ID", "size"), plots=("N_PLOT", "sum"),
                                       q=("Q_ADF_M3D", "sum")).to_string())
    print(d.serv.groupby("DEC_RULE").agg(n=("SET_ID", "size"), q=("Q_ADF_M3D", "sum"),
                                         kmax=("KM_CORE", "max")).to_string())
    print(f"\nBREAK SWEEP   {fk.cite(d.brk)}")
    print(d.brk.to_string(index=False))


def main(argv: list[str]) -> int:
    if "--check" in argv:
        for line in check_palette():
            print("  " + line)
        for line in fk.check_palette():
            print("  " + line)
        d = Data()
        gap = d.q_total - d.q_conn - d.q_unas
        print(f"\n  load balance: {d.q_total:,.3f} in, {d.q_conn:,.3f} connected, "
              f"{d.q_unas:,.3f} named unconnected, gap {gap:,.3f} m3/d")
        assert abs(gap) < 0.5, "the decomposition does not close on load"
        assert d.n_conn + d.n_unas == d.n_total, "the decomposition does not close on count"
        print("  OK — palette separates in greyscale and the decomposition closes")
        return 0

    d = Data()
    if "--numbers" in argv:
        numbers(d)
        return 0

    want = [a.upper() for a in argv[1:] if not a.startswith("-")] or DEFAULT
    unknown = [w for w in want if w not in FIGURES]
    if unknown:
        print(f"unknown figure(s): {unknown}.  Known: {list(FIGURES)}")
        return 2

    print(f"artefacts:\n  {fk.cite(d.plots)}\n  {fk.cite(d.conn)}\n  {fk.cite(d.unas)}\n"
          f"  {fk.cite(d.serv)}\n  {d.m5b_src}\n")
    for name in want:
        t0 = time.time()
        path, caption, finding = FIGURES[name](d)
        print(f"{name}  {path}")
        print(f"      finding : {finding}")
        print(f"      caption : {caption}")
        print(f"      ({time.time()-t0:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
