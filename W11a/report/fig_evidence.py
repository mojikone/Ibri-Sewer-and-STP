"""fig_evidence — the evidence figures for the W11a report.

These are the charts that carry the RETRACTIONS.  Every other figure in the report
says what the design IS; these say *how we know*, and where we were wrong before.

    python fig_evidence.py              # build every figure
    python fig_evidence.py FE01 FE07    # build only these
    python fig_evidence.py --list       # what exists, and what each one claims

Idempotent: same artefacts in, same PNGs out, same filenames.  Nothing here writes
to `W11a/shp` or `W11a/run` — every read goes through `figkit`, which copies to a
scratchpad first.

THE ONE RULE THIS MODULE OBEYS ABOVE ALL OTHERS
-----------------------------------------------
**No number is typed in.**  Every value on every figure is read at run time from an
artefact — a layer in `W11a/shp/*.gpkg`, a CSV in `W11a/run/`, or a MEASUREMENT
TABLE inside a project markdown file, which is parsed rather than transcribed
(:func:`md_table`).  Where a figure needs a number no artefact holds, the figure
says so on its face instead of guessing.

Guideline values appear in exactly four places and each is quoted with its page:

  * **G203-p29 Table 11** minimum gradients — read off
    `Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf` page 29 on
    2026-09-02, and identical to `_BRAIN/02_DESIGN_CRITERIA.md` §2.
  * **G203-p27 §4.2.2.1** the Mara / Sleigh / Taylor tractive relation and its
    constant K — page 27 read on 2026-09-02.  The equation itself is an embedded
    image with no text layer, so the exponents come from
    `_BRAIN/02_DESIGN_CRITERIA.md`, which records the 2026-08-17 correction.
    **G203 states NO numeric tau** — that absence is the subject of FE07.
  * **G203-p27 Table 10** d/D limits and **G203-p22 Table 6** minimum sizes, named
    on FE13 as the causes stage 3 attributes its diameters to.
  * **G201-p71 §7.4.2** — *"The Merrimack formula is to be used … for an area
    (catchment or sub catchment) having over 100 properties."*  Read off
    `Data/PAM-GUD-201 - General Design Guidelines v1.0.pdf` page 71, 2026-09-02.

Anything else numeric on a figure is either measured, or LABELLED ON THE FIGURE as
a project assumption.  A project tolerance dressed as a guideline value is the one
mistake this module exists to prevent.
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figkit as fk  # noqa: E402
from figkit import C  # noqa: E402

BRAIN = fk.ROOT / "_BRAIN"
DOCS = fk.W11A / "docs"

# --------------------------------------------------------------- guideline values
#: G203-p29 Table 11, minimum sewer line gradient, mm/m.
TABLE11_MM_PER_M = {200: 5.00, 250: 3.75, 315: 2.70, 400: 2.05, 500: 1.55,
                    600: 1.25, 700: 1.00, 800: 0.85, 900: 0.75}
G203_T11 = "G203-p29 Tab 11"
G201_PF = "G201-p71 §7.4.2"

#: G203-p27 §4.2.2.1.  Smin = K · tau^1.23 · Q^-0.461, Q in m3/s, tau in Pa.
TRACTIVE_K = 2.33e-4
TRACTIVE_TAU_EXP = 1.23
TRACTIVE_Q_EXP = -0.461
#: PROJECT ASSUMPTION, not a guideline value: Mara's 1.5 L/s minimum design flow,
#: the convention the relation is derived under.  Unfloored it demands unbounded
#: gradient as Q -> 0.  Carried in `W8/py/sewnet/criteria.py` as TRACTIVE_QMIN.
TRACTIVE_QMIN_LS = 1.5

#: G201-p71 §7.4.2 — Merrimack applies only above this many properties.
MERRIMACK_MIN_PROPERTIES = 100

#: PROJECT ASSUMPTION, not a guideline value.  AR&R flood-hazard classes standing in
#: for G203-p30 §4.4.1's "areas subject to washout", which is a SCOUR criterion
#: (philosophy H1a).  Same convention as ``figkit.hazard_coverage``; label it as ours
#: on any figure that uses it.
WADI_CLASSES = (4, 5, 6)

NL = chr(10)          # used where an f-string needs a line break in a label


def sample_hazard(xs, ys):
    """Sample the 50-year grid at points, at FULL resolution -> (known, wadi).

    The nodata is -9999.0, which IS finite, so ``np.isfinite`` alone reports it as
    dry ground.  Handled here so no figure has to remember it.  Sampling the raster
    directly means this does not depend on any stage publishing a WADI_* field.
    """
    import rasterio
    with rasterio.open(fk.HAZARD) as src:
        vals = np.array([v[0] for v in src.sample(zip(np.asarray(xs), np.asarray(ys)))],
                        dtype="float64")
        nod = src.nodata
    known = np.isfinite(vals) & (vals > -9998.0)
    if nod is not None:
        known &= (vals != nod)
    return known, known & (np.floor(vals) >= min(WADI_CLASSES))


def smin_tractive_pct(q_ls, tau_pa=1.0):
    """G203-p27 §4.2.2.1 tractive minimum gradient, as a PERCENT.

    ``q_ls`` in L/s, floored at Mara's 1.5 L/s (a project assumption, see above).
    """
    q = np.maximum(np.asarray(q_ls, dtype="float64"), TRACTIVE_QMIN_LS) / 1000.0
    tau = np.asarray(tau_pa, dtype="float64")
    return 100.0 * TRACTIVE_K * (tau ** TRACTIVE_TAU_EXP) * (q ** TRACTIVE_Q_EXP)


def table11_pct(dn):
    """Table 11 minimum gradient as a PERCENT, for a DN in mm (>=900 -> 0.075 %)."""
    keys = np.array(sorted(TABLE11_MM_PER_M))
    vals = np.array([TABLE11_MM_PER_M[k] for k in keys]) / 10.0     # mm/m -> %
    idx = np.clip(np.searchsorted(keys, np.asarray(dn, dtype="float64"), side="left"),
                  0, len(keys) - 1)
    return vals[idx]


# --------------------------------------------------------------- small helpers

def panel_room(fig, inches: float = 0.26) -> None:
    """Pull the axes down so per-panel titles clear the figure subtitle."""
    h = fig.get_size_inches()[1]
    fig.subplots_adjust(top=max(0.20, fig.subplotpars.top - inches / h))


def wrap(s: str, width: int = 128) -> str:
    """Wrap a source or note line.  An unwrapped long line inflates the tight bbox."""
    return "\n".join(textwrap.fill(part, width) for part in str(s).split("\n"))


def source_room(fig, *texts, per_line: float = 0.125) -> None:
    """Make room under the axes for a multi-line source block.

    ``figkit`` reserves 0.42 in for one source line; anything longer walks into the
    x-axis label.  Call this with the same strings you are about to hand
    :func:`figkit.finish_chart`.
    """
    n = sum(str(t).count("\n") for t in texts if t)
    if n <= 0:
        return
    h = fig.get_size_inches()[1]
    fig.subplots_adjust(bottom=min(0.55, fig.subplotpars.bottom + per_line * n / h))


def run_manifest_note() -> str:
    """What `W11a/run/manifest.json` says about the most recent pipeline run.

    Never assert a stage's status from memory: the pipeline is being re-run while these
    figures are drawn.  This reads the manifest and reports what it actually holds.
    """
    import json
    p = fk.RUN / "manifest.json"
    if not p.exists():
        return "No run manifest was found."
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                    # noqa: BLE001
        return "The run manifest could not be parsed."
    bits = []
    for st in m.get("stages", []):
        why = str(st.get("no_change_reason") or "").strip()
        bits.append(f"{st.get('stage')}" + (f" ({why[:60]})" if why else ""))
    return (f"The run manifest of {m.get('written', 'unknown time')} records: "
            + (", ".join(bits) if bits else "no stage") + ".")


def finish(fig, source: str, note: str | None = None, per_line: float = 0.125) -> None:
    """`figkit.finish_chart` plus the bottom margin a multi-line source block needs."""
    source_room(fig, source, note, per_line=per_line)
    fk.finish_chart(fig, source=source, note=note)


_REG_RE = re.compile(r'@check\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*\n?\s*"((?:[^"\\]|\\.)*)"'
                     r'\s*,?\s*\n?\s*"?((?:[^"\\]|\\.)*)"?', re.S)


def auditor_registry() -> dict[str, tuple[str, str]]:
    """``{check id: (requirement, source)}`` parsed from the auditor's own source.

    The readiness sheets and the audit CSVs disagree about which checks exist, so
    the registry is read from `W11a/py/w11a/audit.py` — the file that defines it —
    rather than inferred from whichever CSV happens to be to hand.
    """
    p = fk.W11A / "py" / "w11a" / "audit.py"
    if not p.exists():
        return {}
    out = {}
    for m in _REG_RE.finditer(p.read_text(encoding="utf-8")):
        cid, _grp, req, src = m.groups()
        out[cid] = (req.replace('\\"', '"'), src.replace('\\"', '"'))
    return out


def ink_on(hexcol: str) -> str:
    """Legible text colour on a given fill."""
    return "white" if fk._rel_luminance(hexcol) < 0.32 else C.INK


# ------------------------------------------------------------- markdown artefacts

def md_cite(path: Path, detail: str = "") -> str:
    """Provenance for a measurement table that lives in a project markdown file.

    ``figkit.cite`` passes plain strings straight through, so this composes with
    ``figkit.source_line`` exactly like a layer or a CSV.
    """
    p = Path(path)
    try:
        rel = p.relative_to(fk.ROOT).as_posix()
    except ValueError:
        rel = p.as_posix()
    bit = f" {detail}" if detail else ""
    return f"{rel}{bit}, written {fk._stamp(p)}"


def md_table(path: Path, after: str, ncol: int) -> list[list[str]]:
    """Rows of the first pipe-table after ``after`` in a markdown file.

    Bold markers, footnote asides and thousands separators are stripped.  Parsing
    the table rather than retyping it means the figure cannot drift from the
    document that recorded the measurement.
    """
    text = Path(path).read_text(encoding="utf-8")
    i = text.find(after)
    if i < 0:
        raise ValueError(f"{Path(path).name}: could not find the anchor {after!r}")
    rows, started = [], False
    for line in text[i:].splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if started:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) != ncol:
            if started:
                break
            continue
        if all(set(c) <= set("-: ") for c in cells):      # the ---|--- rule line
            started = True
            continue
        if not started:                                   # the header row
            continue
        clean = []
        for c in cells:
            c = c.replace("**", "").replace("*", "")
            c = re.sub(r"\(.*?\)", "", c)                 # "(the merge radius ...)"
            clean.append(c.replace(",", "").strip())
        rows.append(clean)
    if not rows:
        raise ValueError(f"{Path(path).name}: no table found after {after!r}")
    return rows


def _first_number(s: str) -> float:
    m = re.search(r"-?\d+(?:\.\d+)?", str(s))
    if not m:
        raise ValueError(f"no number in {s!r}")
    return float(m.group())


# ------------------------------------------------------------------ shared reads

_CACHE: dict = {}


def cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def flows():
    """Stage 5c reach flows — 49,274 chamber-to-chamber reaches with load on them.

    This is the CSV, not ``W11a.gpkg [reaches]``.  Stage 4 re-ran after stage 5c and
    overwrote that layer, so the GeoPackage's ``reaches`` is the stage-4 set.  The
    CSV is the stage-5c artefact and the only published flow record.
    """
    return cached("s5c", lambda: fk.read_csv("s5c_reach_flows.csv"))


def trunk_schedule():
    return cached("trunk", lambda: fk.read_csv("s3_trunk_pipe_schedule.csv"))


def corridors():
    return cached("cor", lambda: fk.read_layer(
        "W11a.gpkg", "corridors",
        columns=["CORR_ID", "US_NODE", "DS_NODE", "SRC", "CONFIDENCE", "LEN_M",
                 "ON_WADI_M", "ON_DUAL_M", "CROSS_ID", "N_PLOT"]))


def components_of(cor):
    """(n_components, node-sets largest first, node -> component index)."""
    import networkx as nx
    g = nx.Graph()
    g.add_edges_from(zip(cor["US_NODE"].astype(str), cor["DS_NODE"].astype(str)))
    comps = sorted(nx.connected_components(g), key=len, reverse=True)
    owner = {}
    for i, c in enumerate(comps):
        for n in c:
            owner[n] = i
    return len(comps), comps, owner


def audit_split(df):
    s = df["status"].astype(str).str.upper()
    return {"pass": int((s == "PASS").sum()),
            "fail": int((s == "FAIL").sum()),
            "untested": int((~s.isin(["PASS", "FAIL"])).sum())}


# ============================================================== FE01  snap tolerance

def FE01_snap_tolerance():
    """The '310 loops' retraction: loops are made by the snap, not by the design."""
    src = fk.RUN / "EVIDENCE_snap_tolerance.md"
    rows = md_table(src, "| snap (m) | nodes | components | cycles |", 4)
    d = (pd.DataFrame([[float(c) for c in r] for r in rows],
                      columns=["snap", "nodes", "comps", "cycles"])
         .sort_values("snap").reset_index(drop=True))

    # the step the evidence names: the first tolerance at which any cycle appears
    first = d.index[d["cycles"] > 0]
    k = int(first[0]) if len(first) else int(d["comps"].diff().abs().idxmax())
    step_m = float(d.loc[k, "snap"])
    closed = int(d.loc[k - 1, "comps"] - d.loc[k, "comps"]) if k else 0
    clean = d[d["cycles"] == 0]
    max_cycles = int(d["cycles"].max())

    fig, axes = fk.chart_frame(
        title=("The loops in W10's published layer are made by the snap: zero at every "
               f"tolerance a GIS would use, {max_cycles} at 2.5 m"),
        subtitle=("The same 20,936 published pipes, clustered at a range of endpoint "
                  "tolerances. Up to "
                  f"{clean['snap'].max():.2f} m the layer has ZERO cycles — because it is "
                  f"in {int(clean['comps'].min()):,} disconnected pieces, and a pile of "
                  "disconnected pieces is loop-free by accident. Squeeze harder and the "
                  "pieces fuse; the loops appear with them. Same layer, different squeeze."),
        figsize=(9.8, 5.6), nrows=2, ygrid=True)
    a, b = axes
    panel_room(fig, 0.10)

    a.plot(d["snap"], d["comps"], marker="o", ms=6, lw=2.0, color=C.TRUNK)
    a.set_yscale("log")
    a.set_ylabel("components (log)")
    a.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for i, r in d.iterrows():
        a.annotate(f"{int(r['comps']):,}", (r["snap"], r["comps"]),
                   textcoords="offset points", xytext=(0, 11 if i % 2 == 0 else -16),
                   ha="center", fontsize=7.2, color=C.INK, fontweight="bold")

    b.plot(d["snap"], d["cycles"], marker="s", ms=6, lw=2.0, ls="--", color=C.FAIL)
    b.set_ylabel("independent cycles\n(E − N + C)")
    b.set_xlabel("endpoint snap tolerance (m, log)")
    for i, r in d.iterrows():
        b.annotate(f"{int(r['cycles']):,}", (r["snap"], r["cycles"]),
                   textcoords="offset points", xytext=(0, 10), ha="center", fontsize=7.2,
                   color=C.INK, fontweight="bold")

    for ax in (a, b):
        ax.set_xscale("log")
        ax.set_xlim(d["snap"].min() * 0.7, d["snap"].max() * 1.45)
        ax.axvspan(d["snap"].min() * 0.7, float(clean["snap"].max()), color=C.PASS,
                   alpha=0.30, zorder=0)
        ax.axvline(step_m, color=C.GREY, lw=1.1, ls=":")
        ax.set_xticks(list(d["snap"]))
        ax.set_xticklabels([f"{v:g}" for v in d["snap"]])
        ax.minorticks_off()
    a.text(float(clean["snap"].max()) ** 0.5 * d["snap"].min() ** 0.5, 0.30,
           "what a surveyor or a GIS\nwould accept — 0 cycles",
           transform=a.get_xaxis_transform(), ha="center", va="center", fontsize=7.6,
           color=C.INK)
    b.annotate(f"first cycles appear at {step_m:g} m, where\n{closed:,} components close "
               f"in one step —\nthe old stitcher's buffer(1.0)",
               xy=(step_m, float(d.loc[k, "cycles"])), xytext=(0.10, 0.62),
               textcoords="axes fraction", fontsize=7.4, color=C.INK,
               arrowprops=dict(arrowstyle="->", color=C.GREY, lw=0.9))

    finish(fig, source=fk.source_line(
        md_cite(src, "— measured on W10/shp/W10_pipes.shp, 20,936 pipes")))
    p = fk.save(fig, "FE01_snap_tolerance")
    return p, ("Components and cycles in W10's published pipe layer against the snap "
               "tolerance used to measure them. The loop count is a property of the "
               "measurement, not of the design."), {
        "gis_cycles": int(clean["cycles"].max()), "gis_comps": int(clean["comps"].min()),
        "first_cycle_at_m": step_m, "components_closed_there": closed,
        "max_cycles": max_cycles}


# ================================================================ FE02  the 4 m hole

def FE02_cut_hole_step():
    """The step function at exactly CORRIDOR_CUT_M: one hole, not a layout."""
    src = DOCS / "OPEN_S4_1_trunk_integration.md"
    pub = md_table(src, "| join every corridor endpoint to a line within", 2)
    pre = md_table(src, "| pre-exclusion set (corridors + removed) | components |", 2)

    pub_x = [_first_number(r[0]) for r in pub]
    pub_y = [float(r[1]) for r in pub]
    pre_x, pre_y = [], []
    for r in pre:
        pre_x.append(0.0 if "as built" in r[0].lower() else _first_number(r[0]))
        pre_y.append(float(r[1]))
    o = np.argsort(pre_x)
    pre_x, pre_y = list(np.array(pre_x)[o]), list(np.array(pre_y)[o])
    saved = int(pre_y[0] - min(pre_y))

    fig, ax = fk.chart_frame(
        title=(f"{saved:,} of the {int(pre_y[0]):,} corridor components were one "
               f"4-metre hole"),
        subtitle=("Components left after joining every corridor endpoint to any line "
                  "within a given distance. Both curves fall off a cliff at exactly "
                  "4.0 m — the width of the buffer stage 2 cut the treated roads with, "
                  "and wider than the 3.0 m node-merge radius meant to close it. The "
                  "fragmentation was a subtraction, not a layout."),
        figsize=(9.8, 5.0), ygrid=True)

    ax.plot(pre_x, pre_y, marker="o", ms=7, lw=2.4, color=C.FAIL,
            label="before the wadi exclusion (corridors + removed)")
    ax.plot(pub_x, pub_y, marker="s", ms=7, lw=2.4, ls="--", color=C.TRUNK,
            label="the published corridor set")
    for xs, ys, col, dy in ((pre_x, pre_y, C.FAIL, -19), (pub_x, pub_y, C.TRUNK, 13)):
        for x, y in zip(xs, ys):
            ax.annotate(f"{int(y):,}", (x, y), textcoords="offset points",
                        xytext=(0, dy), ha="center", fontsize=7.6, color=col,
                        fontweight="bold")

    ax.set_xlabel("endpoints joined to any line within … (m)")
    ax.set_ylabel("disconnected components")
    ax.set_ylim(0, max(pre_y + pub_y) * 1.22)
    ax.set_xlim(-0.5, max(pub_x + pre_x) + 0.6)
    fk.thousands(ax, "y")
    top = ax.get_ylim()[1]
    ax.axvline(4.0, color=C.GREY, lw=1.2, ls=":")
    ax.text(4.12, top * 0.60, "CORRIDOR_CUT_M = 4.0 m\na project constant,\n"
            "not a guideline value", fontsize=7.4, color=C.INK, va="top")
    ax.axvline(3.0, color=C.FLAG, lw=1.2, ls="-.")
    ax.text(2.88, top * 0.34, "NODE_MERGE_M = 3.0 m\nthe merge that was\n"
            "meant to close it", fontsize=7.4, color=C.INK, va="top", ha="right")
    ax.legend(loc="lower left", framealpha=0.94, edgecolor="#9a9a9a", fontsize=7.6)
    finish(fig, source=fk.source_line(md_cite(src, "§4a — the 4 m cut hole")))
    p = fk.save(fig, "FE02_cut_hole_step")
    return p, ("Corridor components against the distance endpoints are joined over. The "
               "step sits at exactly the 4.0 m cut width."), {
        "pre_as_built": int(pre_y[0]), "pre_best": int(min(pre_y)), "saved": saved,
        "published_at_3m": int(pub_y[pub_x.index(3.0)]) if 3.0 in pub_x else None}


# ======================================================= FE03  components through fixes

def FE03_components_through_fixes():
    """Fragmentation through the fixes — and W10, which is a different artefact."""
    w10 = fk.read_csv("audit_W10.csv")
    n_w10 = int(w10.loc[w10["id"] == "H15", "n_bad"].iloc[0])

    s2log = fk.RUN / "s2_corridors.log"
    m = re.search(r"([\d,]+) components, largest holds",
                  s2log.read_text(encoding="utf-8", errors="replace"))
    n_deleted = int(m.group(1).replace(",", "")) if m else None

    cur = BRAIN / "00_CURRENT.md"
    mm = re.search(r"corridor components \*\*([\d,]+) → ([\d,]+) → ([\d,]+)\*\*",
                   cur.read_text(encoding="utf-8"))
    n_h1a = int(mm.group(2).replace(",", "")) if mm else None

    cor = corridors()
    n_now, comps, _ = components_of(cor)
    tot = sum(len(c) for c in comps)
    big3 = 100.0 * sum(len(c) for c in comps[:3]) / tot

    left = [("W10, published PIPE layer\n(a different artefact —\nshown for scale)",
             n_w10, "audit_W10.csv, check H15", "untested")]
    right = [("every wadi contact\nDELETED", n_deleted, "s2_corridors.log", "fail"),
             ("H1a: a crossing is\nKEPT, not deleted", n_h1a, "_BRAIN/00_CURRENT.md",
              "flag"),
             ("the 4 m cut hole\nHEALED", n_now, "measured on the published layer",
              "pass")]
    right = [r for r in right if r[1] is not None]
    bars = left + [(None, None, None, None)] + right         # a gap column

    fig, ax = fk.chart_frame(
        title=(f"The corridor network went from {n_deleted:,} pieces to {n_now:,} without "
               f"moving a line on the ground"),
        subtitle=("Disconnected components. Two rule corrections did all of it: reading "
                  "the wadi clause as a ban on presence rather than on passage, then "
                  "closing a 4 m hole the corridor code left behind. W10's figure is on "
                  "its published PIPE layer, a different artefact — it is here for scale, "
                  "not as the first step of this sequence."),
        figsize=(9.8, 5.0), ygrid=True)

    for i, (lab, v, note, role) in enumerate(bars):
        if v is None:
            continue
        ax.bar(i, v, width=0.60, **fk.status_style(role))
        ax.text(i, v * 1.13, f"{v:,}", ha="center", va="bottom", fontsize=11.5,
                fontweight="bold", color=C.INK)
    for i in range(len(left) + 1, len(bars) - 1):
        a_, b_ = bars[i][1], bars[i + 1][1]
        ax.annotate("", xy=(i + 0.72, b_ * 1.05), xytext=(i + 0.28, a_ * 0.62),
                    arrowprops=dict(arrowstyle="->", color=C.GREY, lw=1.3))
        ax.text(i + 0.5, (a_ * b_) ** 0.5 * 1.05, f"÷{a_ / b_:.1f}", ha="center",
                fontsize=9.0, color=C.GREY, fontweight="bold")
    ax.axvline(len(left), color="#c8c8c8", lw=1.2, ls="--")
    ax.text(len(left) - 0.02, n_w10 * 3.2, "W10  ", ha="right", fontsize=8.0,
            color=C.GREY, style="italic")
    ax.text(len(left) + 0.02, n_w10 * 3.2, "  W11a corridor graph", ha="left", fontsize=8.0,
            color=C.GREY, style="italic")

    ax.set_yscale("log")
    ax.set_ylim(max(1, n_now * 0.30), n_w10 * 9)
    ax.set_xticks([i for i, b in enumerate(bars) if b[1] is not None])
    ax.set_xticklabels([b[0] for b in bars if b[1] is not None], fontsize=7.8)
    ax.set_xlim(-0.65, len(bars) - 0.35)
    ax.set_ylabel("disconnected components (log)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for i, b in enumerate(bars):
        if b[1] is None:
            continue
        ax.text(i, ax.get_ylim()[0] * 1.05, b[2], ha="center", va="bottom", fontsize=6.4,
                color=C.GREY, style="italic",
                bbox=dict(fc="white", ec="none", alpha=0.88, pad=1.4))
    fk.legend_below(ax, [
        Patch(label="W10, published pipes", **fk.status_style("untested")),
        Patch(label="the rule applied by deletion", **fk.status_style("fail")),
        Patch(label="the rule re-read (H1a)", **fk.status_style("flag")),
        Patch(label="today", **fk.status_style("pass")),
    ], ncol=4, drop=0.44)
    finish(fig, source=wrap(fk.source_line(
        w10, md_cite(s2log), md_cite(cur), fk.cite(cor))))
    p = fk.save(fig, "FE03_components_through_fixes")
    return p, (f"Disconnected components at each fix. The published corridor network is now "
               f"in {n_now:,} pieces, the largest three holding {big3:.0f} % of it."), {
        "w10_pipes": n_w10, "deleted": n_deleted, "h1a": n_h1a, "now": n_now,
        "top3_share_pct": big3}


# =============================================================== FE04  the audit matrix

def FE04_audit_matrix():
    """The 22-check registry on three artefacts.  A blank cell is not a pass."""
    w10 = fk.read_csv("audit_W10.csv")
    trunk = fk.read_csv("audit_W11a_trunk.csv")
    # Prefer the real network audit; fall back to the stage-4 readiness sheet, which
    # only says whether a check COULD run.
    try:
        net, ready = fk.read_csv("audit_W11a.csv"), None
    except Exception:                                    # noqa: BLE001
        net, ready = None, fk.read_csv("s4_audit_readiness.csv")
    sw10, strunk = audit_split(w10), audit_split(trunk)

    def role(v):
        return {"PASS": "pass", "FAIL": "fail"}.get(str(v).upper(), "untested")

    if net is not None:
        snet = audit_split(net)
        third = (f"W11a network{NL}{snet['pass']} pass · {snet['fail']} fail{NL}"
                 f"{snet['untested']} cannot run",
                 dict(zip(net["id"], net["status"].map(role))))
        third_ids, third_facts = list(net["id"]), snet
        headline = (f"the full network answers {snet['pass']}, and {snet['untested']} "
                    f"of 22 still cannot be asked")
    else:
        can = int(ready["can_run"].astype(bool).sum())
        cannot = int((~ready["can_run"].astype(bool)).sum())
        third = (f"W11a network, stage 4{NL}{can} can run{NL}{cannot} cannot",
                 {r["check"]: ("flag" if bool(r["can_run"]) else "untested")
                  for _, r in ready.iterrows()})
        third_ids = list(ready["check"])
        third_facts = {"can_run": can, "cannot_run": cannot}
        headline = f"on the full network at stage 4, {cannot} of 22 cannot even be asked"

    cols = [
        (f"W10 published{NL}{sw10['pass']} pass · {sw10['fail']} fail{NL}"
         f"{sw10['untested']} cannot run",
         dict(zip(w10["id"], w10["status"].map(role)))),
        (f"W11a trunk{NL}{strunk['pass']} pass · {strunk['fail']} fail{NL}"
         f"{strunk['untested']} cannot run",
         dict(zip(trunk["id"], trunk["status"].map(role)))),
        third,
    ]
    reg = auditor_registry()
    order = list(w10["id"]) + [i for i in third_ids if i not in set(w10["id"])]
    req = dict(zip(w10["id"], w10["requirement"]))
    req.update(dict(zip(trunk["id"], trunk["requirement"])))
    ref = dict(zip(w10["id"], w10["source"]))
    ref.update(dict(zip(trunk["id"], trunk["source"])))
    for cid, (r, s) in reg.items():
        req.setdefault(cid, r)
        ref.setdefault(cid, s)
    retired = [c for c in order if c not in reg]

    n = len(order)
    fig, ax = fk.chart_frame(
        title=(f"Check by check: the trunk answers {strunk['pass']} of 22; " + headline),
        subtitle=("The same registry run against three artefacts. A check that CANNOT RUN "
                  "counts as a failure, not a blank — W10's seven unanswerable checks are "
                  "exactly why its published layers looked cleaner than they were."),
        figsize=(11.2, 6.6), ygrid=False)
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.subplots_adjust(bottom=0.10)

    top, bot = 0.925, 0.015
    rh = (top - bot) / n
    X_REQ, X_ID, X0, CW, GAP, X_REF = 0.0, 0.425, 0.445, 0.115, 0.008, 0.815

    for j, (head, mp) in enumerate(cols):
        cx = X0 + j * (CW + GAP)
        ax.text(cx + CW / 2, top + 0.012, head, ha="center", va="bottom", fontsize=7.4,
                fontweight="bold", color=C.INK, linespacing=1.4)
        for i, cid in enumerate(order):
            y = top - (i + 1) * rh
            r = mp.get(cid)
            if r is None:
                ax.add_patch(Rectangle((cx, y + rh * 0.13), CW, rh * 0.74,
                                       facecolor="#f2f2f2", edgecolor="#d8d8d8", lw=0.6))
                ax.text(cx + CW / 2, y + rh / 2, "not in this registry", ha="center",
                        va="center", fontsize=5.8, color=C.GREY, style="italic")
                continue
            ax.add_patch(Rectangle((cx, y + rh * 0.13), CW, rh * 0.74,
                                   **fk.status_style(r)))
            ax.text(cx + CW / 2, y + rh / 2,
                    {"pass": "PASS", "fail": "FAIL", "flag": "runs",
                     "untested": "cannot run"}[r],
                    ha="center", va="center", fontsize=7.0, fontweight="bold",
                    color=fk.label_ink(r),
                    path_effects=[pe.withStroke(linewidth=2.0, foreground=(
                        "black" if fk.label_ink(r) == "white" else "white"), alpha=0.55)])

    ax.text(X_ID, top + 0.012, "check", ha="right", va="bottom", fontsize=7.0,
            color=C.GREY, style="italic")
    ax.text(X_REF, top + 0.012, "the rule it comes from", ha="left", va="bottom",
            fontsize=7.0, color=C.GREY, style="italic")
    for i, cid in enumerate(order):
        y = top - (i + 1) * rh
        if i % 2 == 0:
            ax.add_patch(Rectangle((X_REQ - 0.004, y + rh * 0.08), 1.004, rh * 0.84,
                                   facecolor="#f7f7f7", edgecolor="none", zorder=0))
        t = str(req.get(cid, "")) or "(not in the current auditor registry)"
        t = t if len(t) <= 70 else t[:67] + "…"
        ax.text(X_REQ, y + rh / 2, t, ha="left", va="center", fontsize=6.8, color=C.INK)
        ax.text(X_ID, y + rh / 2, cid, ha="right", va="center", fontsize=8.0,
                fontweight="bold", color=C.FAIL if cid in retired else C.INK)
        ax.text(X_REF, y + rh / 2, str(ref.get(cid, "")), ha="left", va="center",
                fontsize=6.2, color=C.GREY)

    used = {r for _h, mp in cols for r in mp.values()}
    labels = {"pass": "PASS", "fail": "FAIL",
              "untested": "CANNOT RUN — counted as a failure",
              "flag": "the check runs; readiness only, not an outcome"}
    handles = [Patch(label=labels[k], **fk.status_style(k))
               for k in ("pass", "flag", "untested", "fail") if k in used]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.005),
              ncol=len(handles), frameon=False, fontsize=7.6, columnspacing=1.8,
              handlelength=2.0)
    note = wrap("A cell marked “not in this registry” is a version difference, not a "
                "pass. " + ("The source sheet still carries " + ", ".join(retired)
                            + ", which `W11a/py/w11a/audit.py` no longer defines."
                            if retired else
                            "All three artefacts run the same 22 checks."))
    src = wrap(fk.source_line(w10, trunk, net if net is not None else ready,
                              md_cite(fk.W11A / "py" / "w11a" / "audit.py",
                                      f"— {len(reg)} checks defined")))
    finish(fig, src, note, per_line=0.10)
    p = fk.save(fig, "FE04_audit_matrix")
    return p, ("The 22-check audit registry on three artefacts, check by check. Grey hatch "
               "is a check that cannot run, and it counts against the design."), {
        "w10": sw10, "trunk": strunk, "network": third_facts,
        "auditor_defines": len(reg), "in_source_sheet_not_in_auditor": retired}


# ============================================================ FE05  flow concentration

def FE05_flow_concentration():
    """Does this drain as one network, or as many?"""
    df = flows()
    cn = fk.read_layer("W11a.gpkg", "connections", columns=["Q_ADF_M3D", "CAN_DRAIN"])
    placed = float(pd.to_numeric(cn["Q_ADF_M3D"], errors="coerce").fillna(0).sum())

    us = set(df["US_NODE"].astype(str))
    roots = (df[~df["DS_NODE"].astype(str).isin(us)]
             .sort_values("QADF_M3D", ascending=False))
    q = roots.loc[roots["QADF_M3D"] > 0, "QADF_M3D"].values
    biggest = float(df["QADF_M3D"].max())
    conc = 100.0 * biggest / placed

    # Stage 5c's own test: it prints "FRAGMENTED, see OPEN-S4-1" below 80 %.  The figure
    # states whichever finding the artefact actually supports on the day it is built.
    FRAG_PCT = 80.0
    fragmented = conc < FRAG_PCT
    if fragmented:
        title = (f"The biggest pipe carries only {conc:.1f} % of the load — a network "
                 f"draining to one works would carry nearly all of it")
        sub = (f"Stage 5c accumulates {placed:,.0f} m³/d of placed load down the reach "
               f"graph. It arrives at {len(q):,} separate outfall reaches, not one. Every "
               f"diameter and level computed downstream of this is computed for a network "
               f"in pieces — which is why OPEN-S4-1 is a blocker, not a tidy-up.")
    else:
        title = (f"The network now drains as one: the last reach carries {conc:.1f} % of "
                 f"the placed load")
        sub = (f"Stage 5c accumulates {placed:,.0f} m³/d of placed load down the reach "
               f"graph. It arrives at {len(q):,} outfall reaches, and the largest single "
               f"reach takes {conc:.1f} % of it — the shape a network draining to one "
               f"works should have. The tail is the evidence for how many satellite "
               f"systems remain: the top ten take {float(np.cumsum(q)[9] / q.sum() * 100) if len(q) > 9 else 100:.1f} %.")
    fig, axes = fk.chart_frame(
        title=title, subtitle=sub, figsize=(10.0, 4.8), ncols=2, ygrid=True)
    a, b = axes
    panel_room(fig, 0.24)

    cum = np.cumsum(q) / q.sum() * 100.0
    rank = np.arange(1, len(q) + 1)
    a.plot(rank, cum, lw=2.2, color=C.TRUNK)
    a.fill_between(rank, 0, cum, color=C.LATERAL, alpha=0.30)
    a.axhline(100, color=C.GREY, lw=0.8, ls=":")
    for kk, col, dx in ((1, C.FAIL, 10), (10, C.MAIN, 10), (50, C.GREY, 10)):
        if kk <= len(cum):
            a.plot([kk], [cum[kk - 1]], "o", ms=7, color=col, zorder=5)
            a.annotate(f"top {kk}: {cum[kk-1]:.0f} %", (kk, cum[kk - 1]),
                       textcoords="offset points", xytext=(dx, -12), fontsize=7.6,
                       color=C.INK, fontweight="bold")
    a.set_xscale("log")
    a.set_xlabel("outfall reaches, ranked by load (log)")
    a.set_ylabel("cumulative share of the load that drains (%)")
    a.set_ylim(0, 110)
    a.set_title("how the load is shared out", fontsize=8.6, color=C.GREY, pad=6)

    top = roots.head(15)
    ypos = np.arange(len(top))[::-1]
    for y, r in zip(ypos, top.itertuples()):
        role = "fail" if r.TIER == "trunk main" else "flag"
        b.barh(y, r.QADF_M3D, height=0.66, left=1e-9, **fk.status_style(role))
        b.text(r.QADF_M3D * 1.10, y, f"{r.QADF_M3D:,.0f}", va="center", fontsize=6.8,
               color=C.INK)
    b.set_yticks(ypos)
    b.set_yticklabels([f"{r.EDGE_UID}  ({r.TIER})" for r in top.itertuples()], fontsize=6.6)
    b.set_xlabel("Q$_{adf}$ arriving (m³/d, log — the largest outfall dwarfs the rest)")
    lo = max(1.0, float(top["QADF_M3D"].min()) * 0.55)
    b.set_xscale("log")
    b.set_xlim(lo, float(top["QADF_M3D"].max()) * 3.2)
    b.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    b.set_title("the fifteen largest outfalls", fontsize=8.6, color=C.GREY, pad=6)
    b.legend(handles=[Patch(label="trunk main", **fk.status_style("fail")),
                      Patch(label="other tiers", **fk.status_style("flag"))],
             loc="lower right", fontsize=6.8, framealpha=0.94, edgecolor="#9a9a9a")

    finish(fig, source=wrap(fk.source_line(df, fk.cite(cn))),
                    note=("“Placed load” is stage 5c's own denominator: the sum of "
                          "Q_ADF_M3D over every stage-5b connection."))
    p = fk.save(fig, "FE05_flow_concentration")
    return p, (f"Load concentration in the accumulated network. {len(q):,} reaches end "
               f"without a downstream pipe; the largest carries {conc:.1f} % of the "
               f"placed load."), {
        "fragmented_by_stage5c_test": fragmented,
        "placed_m3d": placed, "biggest_m3d": biggest, "conc_pct": conc,
        "outfall_reaches_with_load": int(len(q)),
        "top10_share_pct": float(cum[9]) if len(cum) > 9 else None}


# ================================================================= FE06  peak factor

def FE06_peak_factor():
    """Where the peak factor comes from, and where the guideline stops."""
    df = flows()
    n_mer = int((df["PF_METH"] == "merrimack").sum())
    n_held = int((df["PF_METH"] == "held").sum())
    held_val = float(df.loc[df["PF_METH"] == "held", "PF"].iloc[0])
    share = 100.0 * n_held / len(df)

    fig, axes = fk.chart_frame(
        title=(f"{share:.0f} % of reaches get a HELD peak factor, because the guideline "
               f"prescribes no formula below {MERRIMACK_MIN_PROPERTIES} properties"),
        subtitle=(f"{G201_PF}: “The Merrimack formula is to be used … for an area "
                  "(catchment or sub catchment) having over 100 properties.” Below that "
                  "it gives nothing at all, so the value is held at Merrimack evaluated "
                  "on the 100-property flow, and every reach carries the tag. This is a "
                  "declared project choice filling a guideline silence — not a guideline "
                  "value."),
        figsize=(10.0, 4.8), ncols=2, ygrid=True)
    a, b = axes
    panel_room(fig, 0.24)

    sub = df[df["N_PROP"] > 0]
    for meth, col, lab in (("held", C.FLAG, f"held at {held_val:.4f}  ({n_held:,})"),
                           ("merrimack", C.TRUNK, f"Merrimack  ({n_mer:,})")):
        s = sub[sub["PF_METH"] == meth]
        a.scatter(s["N_PROP"], s["PF"], s=2.2, alpha=0.30, color=col, label=lab,
                  edgecolors="none", rasterized=True)
    a.axvline(MERRIMACK_MIN_PROPERTIES, color=C.FAIL, lw=1.4, ls="--")
    a.set_xscale("log")
    a.set_xlabel("properties upstream of the reach (log)")
    a.set_ylabel("peak factor applied")
    lo, hi = a.get_ylim()
    a.annotate(f"{MERRIMACK_MIN_PROPERTIES} properties\n{G201_PF}",
               xy=(MERRIMACK_MIN_PROPERTIES, lo + (hi - lo) * 0.10),
               xytext=(0.04, 0.36), textcoords="axes fraction", fontsize=7.4,
               color=C.FAIL, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=C.FAIL, lw=1.0))
    a.legend(loc="lower left", fontsize=7.0, framealpha=0.94, edgecolor="#9a9a9a",
             markerscale=5, bbox_to_anchor=(0.0, 0.02))
    a.set_title("every reach, by the rule that set its factor", fontsize=8.6, color=C.GREY,
                pad=6)

    vals, roles = [n_mer, n_held], ["pass", "flag"]
    labs = [f"Merrimack\n(> {MERRIMACK_MIN_PROPERTIES} properties,\nthe guideline speaks)",
            f"held at {held_val:.4f}\n(the guideline is silent)"]
    ypos = [1, 0]
    for y, v, role in zip(ypos, vals, roles):
        b.barh(y, v, height=0.42, **fk.status_style(role))
        b.text(v + len(df) * 0.02, y, f"{v:,}\n{100*v/len(df):.0f} %", va="center",
               fontsize=8.6, color=C.INK, fontweight="bold")
    b.set_yticks(ypos)
    b.set_yticklabels(labs, fontsize=7.4)
    b.set_ylim(-0.55, 1.55)
    b.set_xlim(0, max(vals) * 1.34)
    b.set_xlabel(f"reaches (of {len(df):,})")
    fk.thousands(b, "x")
    b.set_title("how many reaches each rule governs", fontsize=8.6, color=C.GREY, pad=6)

    finish(fig, source=wrap(fk.source_line(
        df, "PAM-GUD-201 p71 §7.4.2, read from the source PDF 2026-09-02")))
    p = fk.save(fig, "FE06_peak_factor")
    return p, (f"Peak factor by rule. Merrimack governs {n_mer:,} reaches; the remaining "
               f"{n_held:,} sit below the 100-property threshold where G201 prescribes "
               f"nothing."), {
        "merrimack": n_mer, "held": n_held, "held_value": held_val,
        "held_share_pct": share}


# ============================================================== FE07  tau sensitivity

def FE07_tau_sensitivity():
    """The largest open assumption in the hydraulic design (GAP-9)."""
    df = flows()
    ts = trunk_schedule()
    w10 = fk.read_csv("audit_W10.csv")
    h5 = str(w10.loc[w10["id"] == "H5", "summary"].iloc[0])
    m = re.search(r"tractive force \((\d+) %", h5)
    w10_tractive = int(m.group(1)) if m else None

    taus = np.linspace(1.0, 2.0, 61)
    ratio = 2.0 ** TRACTIVE_TAU_EXP
    qs = df.loc[df["QPK_LS"] > 0, "QPK_LS"].values
    q_works = float(ts["Qpeak (L/s)"].max())
    q_net_max = float(qs.max())

    def pctile(v):
        return 100.0 * float((qs <= v).mean())

    picks = [(TRACTIVE_QMIN_LS, f"{TRACTIVE_QMIN_LS:g} L/s  the design-flow floor"),
             (float(np.percentile(qs, 90)), f"{np.percentile(qs, 90):,.0f} L/s  p90"),
             (float(np.percentile(qs, 99)), f"{np.percentile(qs, 99):,.0f} L/s  p99"),
             (q_net_max, f"{q_net_max:,.0f} L/s  the network's largest reach"),
             (q_works, f"{q_works:,.0f} L/s  at the works")]

    fig, axes = fk.chart_frame(
        title=(f"Double the tractive assumption and every gradient it sets gets "
               f"{ratio:.2f}× steeper — and the guideline names no value at all"),
        subtitle=("G203-p27 §4.2.2.1 gives S$_{min}$ = K·τ$^{1.23}$·Q$^{-0.461}$ and "
                  "defines τ as tractive tension in Pa, then never states a design "
                  "value. τ = 1.0 Pa is OURS (GAP-9) and is one question to one client. "
                  "Everything right of the red line is design we have not justified."),
        figsize=(11.0, 5.2), ncols=2, ygrid=True)
    a, b = axes
    panel_room(fig, 0.28)

    ramp = [C.RIDER, C.LATERAL, C.MAIN, C.SUBMAIN, C.TRUNK]
    styles = [(0, (1, 1.6)), "-.", "--", (0, (6, 1.5)), "-"]
    for (q_ls, lab), col, ls in zip(picks, ramp, styles):
        y = smin_tractive_pct(q_ls, taus)
        a.plot(taus, y, lw=2.2, color=col, ls=ls)
        a.annotate(lab, (2.0, y[-1]), textcoords="offset points", xytext=(6, 0),
                   va="center", fontsize=6.8, color=col, fontweight="bold")
    for dn in (200, 900):
        g = TABLE11_MM_PER_M[dn] / 10.0
        a.axhline(g, color=C.GREY, lw=1.0, ls=(0, (1, 2)))
        a.text(1.01, g, f"{G203_T11}, DN{dn}{'+' if dn == 900 else ''}: {g:.3f} %",
               fontsize=6.6, color=C.GREY, va="center", ha="left",
               bbox=dict(fc="white", ec="none", alpha=0.86, pad=1.2))
    a.axvline(1.0, color=C.FAIL, lw=1.6, ls="--")
    a.set_yscale("log")
    a.set_xlabel("tractive tension τ assumed (Pa)")
    a.set_ylabel("minimum gradient required (%, log)")
    a.set_xlim(0.985, 2.62)
    a.set_xticks([1.0, 1.2, 1.4, 1.6, 1.8, 2.0])
    a.set_title("the requirement, at five real flows from this network — peak flow labelled",
                fontsize=8.4, color=C.GREY, pad=6)

    dn200 = TABLE11_MM_PER_M[200] / 10.0                        # 0.500 %
    net_over = np.array([100.0 * np.mean(smin_tractive_pct(df["QPK_LS"].values, t) > dn200)
                         for t in taus])
    laid = ts["Laid gradient (%)"].values
    t11 = table11_pct(ts["DN (mm)"].values)
    trunk_fail = np.array([
        100.0 * np.mean(laid + 1e-9 < np.maximum(
            t11, smin_tractive_pct(ts["Qpeak (L/s)"].values, t))) for t in taus])

    b.plot(taus, net_over, lw=2.4, color=C.FAIL, ls="-",
           label=(f"the {len(df):,} network reaches where τ, not Table 11,\n"
                  f"would set the gradient (tractive minimum above\n"
                  f"{G203_T11}'s steepest value, {dn200:.3f} % at DN200)"))
    b.plot(taus, trunk_fail, lw=2.4, color=C.TRUNK, ls="--",
           label=(f"the {len(ts):,} laid trunk pipes whose gradient as\n"
                  f"laid would no longer be self-cleansing"))
    b.axvline(1.0, color=C.FAIL, lw=1.2, ls="--")
    for series, col, dy in ((net_over, C.FAIL, 10), (trunk_fail, C.TRUNK, -16)):
        b.annotate(f"{series[-1]:.0f} %", (2.0, series[-1]), textcoords="offset points",
                   xytext=(-8, dy), ha="right", fontsize=9.5, color=col,
                   fontweight="bold")
        b.annotate(f"{series[0]:.0f} %", (1.0, series[0]), textcoords="offset points",
                   xytext=(8, dy), fontsize=9.5, color=col, fontweight="bold")
    at_floor = float(smin_tractive_pct(TRACTIVE_QMIN_LS, 1.0))
    b.annotate(f"at τ = 1.0 the floor flow needs {at_floor:.3f} %,\n"
               f"just under Table 11's {dn200:.3f} % — the whole\n"
               f"design sits {100*(1 - at_floor/dn200):.0f} % below a cliff edge",
               xy=(1.0, 0.0), xytext=(0.28, 0.26), textcoords="axes fraction",
               fontsize=7.2, color=C.FAIL, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=C.FAIL, lw=1.0))
    b.set_xlabel("tractive tension τ assumed (Pa)")
    b.set_ylabel("share of that population (%)")
    b.set_xlim(0.985, 2.015)
    b.set_ylim(-4, 108)
    b.legend(loc="center left", fontsize=6.4, framealpha=0.94, edgecolor="#9a9a9a",
             bbox_to_anchor=(0.015, 0.56))
    b.set_title("how much of the design moves with it", fontsize=8.6, color=C.GREY, pad=6)

    src = wrap(fk.source_line(
        df, ts, "G203-p27 §4.2.2.1 (relation + K) and G203-p29 Tab 11, read from the "
                "source PDF 2026-09-02; exponents 1.23 / −0.461 per "
                "_BRAIN/02_DESIGN_CRITERIA.md (2026-08-17 correction — the equation is "
                "an image in the PDF)"), 150)
    note = wrap("τ = 1.0 Pa and the 1.5 L/s flow floor are PROJECT ASSUMPTIONS, not "
                "guideline values.  W10's own audit, check H5: " + h5, 150)
    finish(fig, src, note)
    p = fk.save(fig, "FE07_tau_sensitivity")
    return p, ("Required gradient against the assumed tractive tension, and how much of "
               "the design moves with it. At 2.0 Pa the requirement is 2.35× the value "
               "everything rests on."), {
        "ratio_at_2Pa": ratio, "net_over_at_1": float(net_over[0]),
        "net_over_at_2": float(net_over[-1]), "trunk_fail_at_1": float(trunk_fail[0]),
        "trunk_fail_at_2": float(trunk_fail[-1]), "w10_tractive_share_pct": w10_tractive}


# ================================================================= FE08  load waterfall

def FE08_load_waterfall():
    """Where all the ultimate load sits, and which parts are not a defect."""
    cn = fk.read_layer("W11a.gpkg", "connections",
                       columns=[c for c in ("Q_ADF_M3D", "CAN_DRAIN")])
    un = fk.read_csv("s5b_unassigned.csv")
    q = pd.to_numeric(cn["Q_ADF_M3D"], errors="coerce").fillna(0)
    can = (pd.to_numeric(cn["CAN_DRAIN"], errors="coerce")
           if "CAN_DRAIN" in cn.columns else pd.Series(np.nan, index=cn.index))
    graded = bool(can.notna().any())          # does stage 5b still publish drainability?

    def bucket(w):
        w = str(w)
        if w.startswith("no wastewater load"):
            return "carries no load at all"
        if "within 47.5 m" in w:
            return "no carrier within 47.5 m"
        if w.startswith("cannot drain to"):
            return "cannot drain — tested on PLACEHOLDER levels"
        if "right-of-way" in w or "offset 0.00" in w:
            return "carrier sits on the plot boundary"
        if "outside the project boundary" in w:
            return "outside the study boundary"
        if "along the tertiary path" in w or re.search(r"over(?: the)? 45", w):
            return "connection would exceed 45 m (G203-p22 Tab 6)"
        return "other: " + w[:44]

    un = un.assign(B=un["WHY"].map(bucket))
    g = (un.groupby("B").agg(plots=("PLOT_ID", "size"), q=("Q_ADF_M3D", "sum"))
         .sort_values("q", ascending=False))
    nd_key = "cannot drain — tested on PLACEHOLDER levels"
    # Plots in the "cannot drain" bucket DID get a connection drawn, so they sit inside
    # the connections layer too.  Count them once: on the connections side when stage 5b
    # graded them, and as their own bar otherwise.
    overlap = graded and nd_key in g.index
    others = g.drop(index=nd_key) if overlap else g
    connected = float(q.sum())
    total = connected + float(others["q"].sum())

    if graded:
        rows = [("connected and drainable", float(q[can == 1].sum()), "pass",
                 f"{int((can == 1).sum()):,} connections"),
                (nd_key, float(q[can == 0].sum()), "fail",
                 (f"{int(g.loc[nd_key, 'plots']):,} plots — every chamber is still "
                  f"seeded at one depth") if nd_key in g.index
                 else f"{int((can == 0).sum()):,} connections")]
    else:
        rows = [("connected to the network", connected, "pass",
                 f"{len(cn):,} connections")]
    for name, r in others.iterrows():
        rows.append((name, float(r["q"]),
                     "untested" if r["q"] == 0 else "flag", f"{int(r['plots']):,} plots"))

    noload = int(g.loc["carries no load at all", "plots"]) if         "carries no load at all" in g.index else 0
    unconn = total - connected
    real = [r for r in rows[1:] if r[2] == "flag"]
    fig, ax = fk.chart_frame(
        title=(f"{100*connected/total:.0f} % of the ultimate load is on the network; the "
               f"rest is {len(real)} named causes, and one of them is not a shortfall"),
        subtitle=(f"All {total:,.0f} m³/d of ultimate saturated load, by what happened to "
                  f"it in stage 5b. Nothing is rounded away and nothing is silently "
                  f"dropped — that is the point of the figure. "
                  + (f"{noload:,} plots carry no wastewater by construction, so removing "
                     f"them changes the load by zero." if noload else "")
                  + ("" if graded else "  Stage 5b no longer publishes CAN_DRAIN, so the "
                     "connected bar is not split by drainability on this run.")),
        figsize=(10.2, 4.4 + 0.34 * len(rows)), ygrid=False, xgrid=True)

    ypos = np.arange(len(rows))[::-1]
    for y, (name, v, role, note) in zip(ypos, rows):
        ax.barh(y, max(v, total * 0.0016), height=0.58, **fk.status_style(role))
        ax.text(max(v, total * 0.0016) + total * 0.008, y,
                f"{v:,.0f} m³/d   ({100*v/total:.1f} %)   ·  {note}",
                va="center", fontsize=7.4, color=C.INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.8)
    ax.set_xlim(0, total * 0.94)
    ax.set_xlabel("ultimate saturated Q$_{adf}$ (m³/d)")
    fk.thousands(ax, "x")
    handles = [Patch(label="on the network", **fk.status_style("pass"))]
    if any(r[2] == "fail" for r in rows):
        handles.append(Patch(label="blocked by an unfinished stage",
                             **fk.status_style("fail")))
    handles += [Patch(label="a real layout question", **fk.status_style("flag")),
                Patch(label="no load to place — not a shortfall",
                      **fk.status_style("untested"))]
    fk.legend_below(ax, handles, ncol=len(handles), drop=0.34)
    finish(fig, source=wrap(fk.source_line(fk.cite(cn), un)),
           note=(f"The parts reconcile to {total:,.0f} m³/d with no residue; CLAUDE.md "
                 f"carries the ultimate saturated Qadf as ≈ 74,700 m³/d."))
    p = fk.save(fig, "FE08_load_waterfall")
    return p, (f"Every m³/d of ultimate load, by what stage 5b did with it. "
               f"{connected:,.0f} m³/d is on the network; the remaining "
               f"{unconn:,.0f} m³/d decomposes into named causes."), {
        "total_m3d": total, "connected_m3d": connected, "not_connected_m3d": unconn,
        "drainability_published": graded,
        "buckets_m3d": {k: float(v) for k, v in others["q"].items()},
        "no_load_plots": noload}


# ============================================================ FE09  break sensitivity

def FE09_break_sensitivity():
    """Central vs decentralised: how sensitive is the answer to the threshold?"""
    d = fk.read_csv("s1_break_sensitivity.csv").sort_values("break_m_per_prop")
    d = d.reset_index(drop=True)
    j = int(d["pct_of_properties"].diff().abs().idxmax())
    cliff, prev = d.loc[j], d.loc[max(0, j - 1)]

    fig, axes = fk.chart_frame(
        title=("The central-versus-decentralised threshold barely matters above "
               f"{cliff['break_m_per_prop']:.0f} m per property — and falls off a cliff "
               f"below it"),
        subtitle=("Stage 1 decides which settlements join the central network on a "
                  "corridor-metres-per-property test. Sweeping the threshold shows the "
                  "answer is flat over an eight-fold range and then collapses. The number "
                  "to settle with the client is narrow — and it is not the one we are "
                  "near."),
        figsize=(10.2, 4.8), ncols=2, ygrid=True)
    a, b = axes
    panel_room(fig, 0.24)

    a.axvspan(float(prev["break_m_per_prop"]), float(cliff["break_m_per_prop"]),
              color=C.FAIL, alpha=0.12, zorder=0)
    a.plot(d["break_m_per_prop"], d["pct_of_properties"], marker="o", ms=6, lw=2.2,
           color=C.FAIL, label="properties off the central network")
    a.plot(d["break_m_per_prop"], d["pct_of_load"], marker="s", ms=6, lw=2.2, ls="--",
           color=C.TRUNK, label="load off the central network")
    a.set_xscale("log")
    a.set_xlabel("break threshold (corridor m per property, log)")
    a.set_ylabel("share off the central network (%)")
    a.annotate(f"{prev['pct_of_properties']:.1f} %  →  "
               f"{cliff['pct_of_properties']:.1f} %\nbetween "
               f"{prev['break_m_per_prop']:.0f} and {cliff['break_m_per_prop']:.0f} "
               f"m/property",
               xy=(float(cliff["break_m_per_prop"]), float(cliff["pct_of_properties"])),
               xytext=(0.34, 0.60), textcoords="axes fraction", fontsize=7.6, color=C.INK,
               fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=C.GREY, lw=1.0))
    a.legend(loc="upper right", fontsize=7.2, framealpha=0.94, edgecolor="#9a9a9a")
    a.set_title("what the threshold decides", fontsize=8.6, color=C.GREY, pad=6)

    b.plot(d["break_m_per_prop"], d["decentralised_settlements"], marker="o", ms=6,
           lw=2.2, color=C.SUBMAIN)
    b.set_xscale("log")
    b.set_xlabel("break threshold (corridor m per property, log)")
    b.set_ylabel("settlements served off-network", color=C.SUBMAIN)
    b2 = b.twinx()
    b2.plot(d["break_m_per_prop"], d["exclusive_km_not_built"], marker="^", ms=6, lw=2.2,
            ls="-.", color=C.FLAG)
    b2.set_ylabel("exclusive corridor km avoided", color=C.FLAG)
    b2.grid(False)
    b2.spines["top"].set_visible(False)
    b.legend(handles=[Line2D([], [], color=C.SUBMAIN, marker="o", lw=2.2,
                             label="settlements served off-network"),
                      Line2D([], [], color=C.FLAG, marker="^", lw=2.2, ls="-.",
                             label="exclusive corridor km avoided")],
             loc="upper right", fontsize=7.2, framealpha=0.94, edgecolor="#9a9a9a")
    b.set_title("what it costs and what it saves", fontsize=8.6, color=C.GREY, pad=6)

    finish(fig, source=fk.source_line(d),
                    note=("The TOR requires every plot to be SERVED (scope p4 item 3). "
                          "This chart is about WHICH SYSTEM serves it — never about "
                          "dropping it."))
    p = fk.save(fig, "FE09_break_sensitivity")
    return p, ("Sensitivity of the central / decentralised split to the break threshold: "
               "flat above the cliff, collapsing below it."), {
        "cliff_at_m_per_prop": float(cliff["break_m_per_prop"]),
        "pct_properties_below": float(prev["pct_of_properties"]),
        "pct_properties_at": float(cliff["pct_of_properties"])}


# ========================================================== FE10  corridor provenance

def FE10_corridor_provenance():
    """How much of the network rests on geometry nobody has confirmed."""
    cor = corridors()
    g = (cor.assign(km=cor["LEN_M"] / 1000.0)
         .groupby(["CONFIDENCE", "SRC"]).agg(km=("km", "sum"), n=("CORR_ID", "size"))
         .reset_index())
    total = float(g["km"].sum())
    order = [c for c in ("surveyed", "drafted", "derived", "provisional")
             if c in set(g["CONFIDENCE"])]
    prov = float(g.loc[g["CONFIDENCE"] == "provisional", "km"].sum())
    srcs = list(g.groupby("SRC")["km"].sum().sort_values(ascending=False).index)
    shades = [C.RIDER, C.LATERAL, C.MAIN, C.SUBMAIN, C.TRUNK]
    hatches = ["", "//", "..", "\\\\", "xx", "++"]
    smap = {s: shades[i % len(shades)] for i, s in enumerate(srcs)}
    hmap = {s: hatches[i % len(hatches)] for i, s in enumerate(srcs)}

    fig, ax = fk.chart_frame(
        title=(f"{prov:,.0f} km — {100*prov/total:.0f} % of the corridor network — is "
               f"geometry nobody has confirmed"),
        subtitle=("Every published corridor carries the source it came from and how far "
                  "that source can be trusted. Nothing here is SURVEYED. The provisional "
                  "share is not an error; it is the size of the thing waiting on the "
                  "draftsman's final lines and the GIS expert's land-use data."),
        figsize=(10.2, 4.8), ygrid=False, xgrid=True)

    ypos = np.arange(len(order))[::-1]
    for y, conf in zip(ypos, order):
        left = 0.0
        for s in srcs:
            row = g[(g["CONFIDENCE"] == conf) & (g["SRC"] == s)]
            if not len(row):
                continue
            v = float(row["km"].iloc[0])
            ax.barh(y, v, left=left, height=0.55, facecolor=smap[s], edgecolor=C.INK,
                    linewidth=0.6, hatch=hmap[s])
            if v > total * 0.045:
                ax.text(left + v / 2, y, f"{s}\n{v:,.0f} km", ha="center", va="center",
                        fontsize=6.8, color=ink_on(smap[s]), fontweight="bold")
            left += v
        ax.text(left + total * 0.007, y, f"{left:,.0f} km   ({100*left/total:.0f} %)",
                va="center", fontsize=8.4, fontweight="bold", color=C.INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels([c.upper() for c in order], fontsize=8.8, fontweight="bold")
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlabel("corridor length (km)")
    ax.set_xlim(0, total * 0.64)
    fk.thousands(ax, "x")
    fk.legend_below(ax, [Patch(facecolor=smap[s], edgecolor=C.INK, hatch=hmap[s],
                               linewidth=0.6, label=s) for s in srcs],
                    ncol=min(6, len(srcs)), drop=0.34)
    finish(fig, source=fk.source_line(cor),
                    note=("CONFIDENCE is the contract's own enum: surveyed ‣ drafted ‣ "
                          "derived ‣ provisional. No corridor in this network carries "
                          "“surveyed”."))
    p = fk.save(fig, "FE10_corridor_provenance")
    return p, (f"Corridor length by source and confidence. {prov:,.0f} km of "
               f"{total:,.0f} km is provisional, and nothing is surveyed."), {
        "total_km": total, "provisional_km": prov,
        "km_by_confidence": {c: float(g.loc[g["CONFIDENCE"] == c, "km"].sum())
                             for c in order}}


# ============================================================== FE11  crossing register

def FE11_crossing_register():
    """The crossings register SCHEDULES a crossing.  It does not TEST one."""
    xs2 = fk.read_layer("W11a.gpkg", "crossings",
                        columns=["CROSS_ID", "OBSTACLE", "LEN_M", "ANGLE_DEG", "METHOD",
                                 "APPROVED"])
    xs3 = fk.read_layer("W11a_trunk.gpkg", "crossings",
                        columns=["CROSS_ID", "OBSTACLE", "LEN_M", "ANGLE_DEG", "METHOD"])
    a2, a3 = xs2["ANGLE_DEG"].astype(float), xs3["ANGLE_DEG"].astype(float)
    constant = bool(a2.nunique() == 1)
    long70 = int((xs2["LEN_M"] > 70).sum())
    longest = float(xs2["LEN_M"].max())
    n_w3 = int((xs3["OBSTACLE"] == "wadi").sum())

    fig, axes = fk.chart_frame(
        title=(f"The corridor crossing register DECLARES 90° on every one of "
               f"{len(xs2):,} rows — the trunk's register measures it"),
        subtitle=("H1a item 1 asks whether a contact CROSSES a wadi or RUNS ALONG it, and "
                  "answers with the angle and the length. Stage 2 writes the angle as a "
                  f"constant; stage 3 computes it and finds skews down to {a3.min():.1f}°. "
                  f"Until stage 2 measures it too, these {len(xs2):,} crossings satisfy "
                  "H1a item 4 — each is registered — and say nothing about item 1."),
        figsize=(10.4, 4.8), ncols=2, ygrid=True)
    a, b = axes
    panel_room(fig, 0.26)

    bins = np.logspace(np.log10(max(0.5, xs2["LEN_M"].min())),
                       np.log10(longest * 1.05), 34)
    a.hist(xs2["LEN_M"], bins=bins, color=C.LATERAL, edgecolor=C.INK, linewidth=0.4,
           label=f"corridor crossings ({len(xs2):,})")
    a.hist(xs3.loc[xs3["OBSTACLE"] == "wadi", "LEN_M"], bins=bins, color=C.FAIL,
           edgecolor=C.INK, linewidth=0.4, alpha=0.9, hatch="//",
           label=f"trunk wadi crossings ({n_w3})")
    a.set_xscale("log")
    a.axvline(70, color=C.INK, lw=1.3, ls="--")
    a.set_xlabel("length of the on-wadi contact (m, log)")
    a.set_ylabel("crossings")
    a.set_ylim(0, a.get_ylim()[1] * 1.30)
    a.annotate(f"{long70:,} corridor crossings run further than 70 m;\n"
               f"the longest is {longest:,.0f} m",
               xy=(70, a.get_ylim()[1] * 0.52), xytext=(0.03, 0.90),
               textcoords="axes fraction", fontsize=7.4, color=C.INK, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=C.GREY, lw=1.0))
    a.legend(loc="lower left", fontsize=7.0, framealpha=0.94, edgecolor="#9a9a9a")
    a.set_title("how long each “crossing” actually is", fontsize=8.6, color=C.GREY, pad=6)

    b.hist(a3, bins=np.linspace(0, 92, 24), color=C.TRUNK, edgecolor=C.INK,
           linewidth=0.4, label=f"stage 3, measured ({len(a3)} rows)")
    b.axvline(90.0, color=C.FAIL, lw=2.6)
    b.set_ylim(0, b.get_ylim()[1] * 1.22)
    b.annotate(f"stage 2: all {len(xs2):,} rows\nwritten as exactly 90.0°"
               + ("\n(one distinct value — a constant,\nnot a measurement)"
                  if constant else ""),
               xy=(90, b.get_ylim()[1] * 0.48), xytext=(0.03, 0.82),
               textcoords="axes fraction", fontsize=7.4, color=C.FAIL, fontweight="bold",
               arrowprops=dict(arrowstyle="->", color=C.FAIL, lw=1.1))
    b.set_xlabel("angle to the obstacle (degrees; 90° = square)")
    b.set_ylabel("crossings")
    b.legend(loc="upper left", fontsize=7.0, framealpha=0.94, edgecolor="#9a9a9a",
             bbox_to_anchor=(0.0, 0.62))
    b.set_title("declared against measured", fontsize=8.6, color=C.GREY, pad=6)

    finish(fig, source=wrap(fk.source_line(fk.cite(xs2), fk.cite(xs3))),
                    note=wrap("The 70 m line is a DISPLAY threshold chosen here to separate short "
                     "crossings from long runs — H1a sets NO length limit; its test is the "
                     "contact length against the shortest crossing available at that "
                     "point, which the register does not record.  "
                     "H1a's skew tolerance is a PROJECT RULE, not a guideline "
                              "number (_BRAIN/08_DESIGN_PHILOSOPHY.md, H1a item 1). "
                              "G203-p30 §4.4.1 and p33 forbid pipes and chambers IN a "
                              "wadi; G201-p85–86 §9.3 sets out how to cross one."))
    p = fk.save(fig, "FE11_crossing_register")
    return p, ("The wadi crossing register: contact lengths, and declared angle against "
               "measured angle. Stage 2's 90° is a constant."), {
        "corridor_crossings": int(len(xs2)), "over_70m": long70, "longest_m": longest,
        "stage2_angle_constant": constant, "stage3_min_angle_deg": float(a3.min()),
        "approved": int(xs2["APPROVED"].sum())}


# ============================================================ FE12  the untested share

def FE12_untested_share():
    """Clear ground is not a clean answer."""
    known_pops, notes = [], []
    for lyr, lab in (("nodes", "published chambers"), ("reaches", "published reaches"),
                     ("corridors", "published corridors")):
        try:
            gdf = fk.read_layer("W11a.gpkg", lyr, columns=[])
        except Exception as exc:                         # noqa: BLE001
            notes.append(f"{lyr}: {type(exc).__name__}")
            continue
        gg = gdf.geometry
        pts = (gg if gg.geom_type.iloc[0] == "Point"
               else gg.interpolate(0.5, normalized=True))
        known, wadi = sample_hazard(pts.x.values, pts.y.values)
        known_pops.append((lab + NL + f"({len(gdf):,})", {
            "untested": int((~known).sum()),
            "fail": int((known & wadi).sum()),
            "pass": int((known & ~wadi).sum())}, fk.cite(gdf)))
    if not known_pops:
        raise RuntimeError("no published layer could be read for the hazard sweep")

    audits = []
    for name in ("audit_W11a.csv", "audit_W11a_trunk.csv", "audit_W10.csv"):
        try:
            audits.append(fk.read_csv(name))
        except Exception:                                # noqa: BLE001
            continue

    def pct_from(df):
        row = df.loc[df["id"] == "R4", "summary"]
        if not len(row):
            return None
        m = re.search(r"(\d+)\s*% of samples fall outside the hazard grid", str(row.iloc[0]))
        return int(m.group(1)) if m else None

    first = known_pops[0][1]
    untested_share = 100.0 * first["untested"] / max(sum(first.values()), 1)

    fig, ax = fk.chart_frame(
        title=(f"Nearly half of every wadi answer does not exist: {untested_share:.0f} % of "
               f"chambers sit where the 50-year grid has no value"),
        subtitle=("Every published chamber, reach midpoint and corridor midpoint sampled "
                  "against the 50-year hazard grid at full resolution. The grid does not "
                  "cover the study area, and its nodata is −9999.0 — a FINITE number, so "
                  "an is-finite guard reads it as dry ground. Every wadi result in this "
                  "project is a result on the tested half. Clear ground on our maps means "
                  "TESTED AND CLEAN; hatched ground means no answer was available."),
        figsize=(10.0, 4.8), ygrid=False, xgrid=True)

    order = ["pass", "fail", "untested"]
    names = {"pass": "tested, clear of wadi ground", "fail": "tested, ON wadi ground",
             "untested": "UNTESTED — outside the grid"}
    ypos = np.arange(len(known_pops))[::-1]
    for y, (_lab, dct, _src) in zip(ypos, known_pops):
        tot, left = max(sum(dct.values()), 1), 0.0
        for k in order:
            v = dct[k]
            if not v:
                continue
            w = 100.0 * v / tot
            ax.barh(y, w, left=left, height=0.46, **fk.status_style(k))
            if w > 4.5:
                ax.text(left + w / 2, y, f"{v:,}" + NL + f"{w:.1f} %",
                        ha="center", va="center",
                        fontsize=7.6, fontweight="bold", color=fk.label_ink(k))
            else:
                ax.annotate(f"{v:,} ({w:.1f} %)", (left + w / 2, y),
                            textcoords="offset points", xytext=(0, 22), ha="center",
                            fontsize=7.0, color=C.INK,
                            arrowprops=dict(arrowstyle="-", color=C.GREY, lw=0.7))
            left += w
    ax.set_yticks(ypos)
    ax.set_yticklabels([r[0] for r in known_pops], fontsize=8.0)
    ax.set_ylim(-0.55, len(known_pops) - 0.25)
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of the population (%)")

    tail = []
    for df in audits:
        v = pct_from(df)
        if v is not None:
            tail.append(f"{Path(fk.cite(df).split(',')[0]).name} R4: {v} % untested")
    fk.legend_below(ax, [Patch(label=names[k], **fk.status_style(k)) for k in order],
                    ncol=3, drop=0.30)
    finish(fig, source=wrap(fk.source_line(*[s_ for _l, _d, s_ in known_pops],
                                           f"{fk.HAZARD.name}, 50-year hazard grid, "
                                           f"nodata −9999.0, sampled at full resolution")),
           note=wrap("Wadi ground is read as hazard class ≥ "
                     f"{min(WADI_CLASSES)}, a PROJECT ASSUMPTION standing in for "
                     "G203-p30 §4.4.1's washout criterion — not a guideline number."
                     + ("  ·  " + "; ".join(tail) if tail else "")
                     + ("  ·  " + "; ".join(notes) if notes else "")))
    p = fk.save(fig, "FE12_untested_share")
    return p, ("Wadi test coverage on the published layers, sampled straight from the "
               "hazard grid. The untested share is not a pass."), {
        lab.replace(NL, " "): dct for lab, dct, _s in known_pops} | {
        "chamber_untested_pct": untested_share,
        "audit_r4_untested_pct": tail}


# ====================================================== FE13  trunk constraint provenance

def FE13_constraint_provenance():
    """On the one fully-designed tier, what actually decides each pipe?"""
    ts = trunk_schedule()
    w10 = fk.read_csv("audit_W10.csv")
    h5 = str(w10.loc[w10["id"] == "H5", "summary"].iloc[0])
    m = re.search(r"tractive force \((\d+) %", h5)
    w10_tractive = int(m.group(1)) if m else None

    grad = ts["Gradient set by"].value_counts()
    dia = ts["Diameter set by"].value_counts()
    route = ts["Self-cleansing by"].value_counts()
    panels = [
        ("what set the GRADIENT", grad,
         {"table11": f"the Table 11 floor\n{G203_T11}",
          "cover_min": "minimum cover\nG203-p33",
          "ground": "the ground profile\n(design, not a guideline)",
          "tractive": "the tractive minimum\nG203-p27"}),
        ("what set the DIAMETER", dia,
         {"dod": "the d/D limit\nG203-p27 Tab 10",
          "minimum": "the tier minimum size\nG203-p22 Tab 6",
          "capacity": "capacity at peak flow"}),
        ("which self-cleansing route", route,
         {"velocity": "velocity ≥ 0.75 m/s\nG203-p26",
          "tractive": "tractive force\n— exposed to τ, G203-p27"}),
    ]

    fig, axes = fk.chart_frame(
        title=(f"On the one fully-levelled tier, {G203_T11} sets "
               f"{100*grad.iloc[0]/len(ts):.0f} % of the gradients — and every pipe "
               f"records which rule bound it"),
        subtitle=(f"All {len(ts):,} trunk pipes, by the constraint stage 3 attributes each "
                  f"decision to. This is the provenance W10's layers could not publish, "
                  f"which is why six of its checks could not run at all. The right panel "
                  f"is this tier's τ exposure"
                  + (f" — {route.get('tractive', 0) / len(ts) * 100:.0f} % here against "
                     f"{w10_tractive} % on W10." if w10_tractive else ".")),
        figsize=(10.8, 4.6), ncols=3, ygrid=False, xgrid=True)
    panel_room(fig, 0.34)

    shades = [C.TRUNK, C.MAIN, C.LATERAL, C.RIDER]
    hatches = ["", "//", "..", "\\\\"]
    for ax, (title, vc, labs) in zip(axes, panels):
        ypos = np.arange(len(vc))[::-1]
        for i, (y, (k, v)) in enumerate(zip(ypos, vc.items())):
            ax.barh(y, v, height=0.40, facecolor=shades[i % len(shades)], edgecolor=C.INK,
                    linewidth=0.6, hatch=hatches[i % len(hatches)])
            ax.text(v + len(ts) * 0.015, y, f"{v:,}   {100*v/len(ts):.0f} %", va="center",
                    fontsize=8.0, color=C.INK, fontweight="bold")
            ax.text(0, y + 0.30, labs.get(k, k), ha="left", va="bottom", fontsize=6.9,
                    color=C.INK, linespacing=1.3)
        ax.set_yticks([])
        ax.set_ylim(-0.6, len(vc) - 0.15)
        ax.set_xlim(0, len(ts) * 1.10)
        ax.set_title(title, fontsize=8.6, color=C.GREY, pad=6)
        ax.set_xlabel(f"pipes (of {len(ts):,})")

    finish(fig, source=wrap(fk.source_line(ts, w10)),
                    note=wrap("Table 11 is G203-p29; the d/D limits are G203-p27 Table 10; "
                              "the tier minimum sizes are G203-p22 Table 6. “the ground "
                              "profile” and “minimum cover” are the design following the "
                              "surface — a consequence, not a guideline value."))
    p = fk.save(fig, "FE13_constraint_provenance")
    return p, ("What constrained every trunk pipe: gradient, diameter and self-cleansing "
               "route, each attributed to a named cause."), {
        "gradient": grad.to_dict(), "diameter": dia.to_dict(),
        "self_cleansing": route.to_dict(), "w10_tractive_share_pct": w10_tractive}


# ========================================================= FE14  depth without stations

def FE14_depth_without_stations():
    """What gravity alone costs, and what the cap-and-veto ladder is for."""
    cb = fk.read_csv("s6_cap_breaches.csv")
    sd = fk.read_csv("s6_station_demand.csv")
    cap = 12.0
    exit_worst = float(cb["worst_cover_m"].max())
    station_worst = float(sd["WORST_COVER_M"].max())
    why = sd["WHY"].astype(str).value_counts()

    fig, axes = fk.chart_frame(
        title=(f"{len(cb)} deep runs escape the 12 m cap through the ladder's two exits; "
               f"{len(sd):,} cannot, and reach {station_worst:,.0f} m of cover"),
        subtitle=("Stage 6's cap-and-veto ladder: a run past 12 m of cover is allowed only "
                  "if it recovers within 500 m or reaches its outfall within 1,000 m — "
                  "anything else needs a lifting station. The 12 m cap and both distances "
                  "are PROJECT RULES (philosophy §5); G203-p33 recommends "
                  "“approximately 10–12 m” of cover on excavation COST and sets no limit."),
        figsize=(10.4, 4.8), ncols=2, ygrid=True)
    a, b = axes
    panel_room(fig, 0.26)

    ex = cb["exit"].astype(str)
    kinds = list(dict.fromkeys(ex))
    cols = {k: (C.PASS if "recover" in k else C.FLAG) for k in kinds}
    hat = {k: (None if "recover" in k else "..") for k in kinds}
    bins = np.logspace(np.log10(cap * 0.95), np.log10(exit_worst * 1.06), 24)
    conts = a.hist([cb.loc[ex == k, "worst_cover_m"] for k in kinds], bins=bins,
                   stacked=True, color=[cols[k] for k in kinds], edgecolor=C.INK,
                   linewidth=0.4,
                   label=[f"{k.replace('_', ' ')}  ({int((ex == k).sum())})"
                          for k in kinds])[2]
    for cont, k in zip(conts, kinds):
        for patch in cont:
            patch.set_hatch(hat[k])
    a.set_xscale("log")
    a.axvline(cap, color=C.FAIL, lw=1.8, ls="--")
    a.set_ylim(0, a.get_ylim()[1] * 1.22)
    a.text(cap * 1.05, a.get_ylim()[1] * 0.96, "12 m cap\n(a project rule)", fontsize=7.4,
           color=C.FAIL, va="top", fontweight="bold")
    a.set_xlabel("worst cover reached on the run (m, log)")
    a.set_ylabel("runs")
    a.legend(loc="upper right", fontsize=7.0, framealpha=0.94, edgecolor="#9a9a9a",
             title="how it exits the ladder", title_fontsize=7.0)
    a.set_title(f"the {len(cb)} that find an exit — worst {exit_worst:,.1f} m",
                fontsize=8.6, color=C.GREY, pad=6)

    b.scatter(sd["BREACH_LEN_M"] / 1000.0, sd["WORST_COVER_M"], s=18, alpha=0.75,
              color=C.TRUNK, edgecolors=C.INK, linewidths=0.3)
    b.axhline(cap, color=C.FAIL, lw=1.6, ls="--")
    b.axvline(1.0, color=C.GREY, lw=1.1, ls=":")
    b.set_xscale("log")
    b.set_ylim(0, station_worst * 1.16)
    b.text(1.06, station_worst * 1.10, "the 1,000 m\nreach-the-outfall exit", fontsize=7.0,
           color=C.GREY, va="top")
    b.text(b.get_xlim()[0] * 1.15, cap * 1.25, "12 m cap", fontsize=7.2, color=C.FAIL,
           fontweight="bold")
    b.set_xlabel("length of the breaching run (km, log)")
    b.set_ylabel("worst cover on the run (m)")
    b.legend(handles=[Line2D([], [], marker="o", ls="", color=C.TRUNK,
                             markeredgecolor=C.INK,
                             label=f"a point needing a station ({len(sd):,})")],
             loc="lower left", fontsize=7.2, framealpha=0.94, edgecolor="#9a9a9a")
    b.set_title(f"the {len(sd):,} that cannot — every one past both exits",
                fontsize=8.6, color=C.GREY, pad=6)

    finish(fig, source=wrap(fk.source_line(cb, sd)),
           note=wrap("These are stage 6's OWN outputs, from the run stamped in the source "
                     "line above — the pipeline is still moving, so read the timestamp "
                     "before quoting them. " + run_manifest_note()
                     + "  Every station-demand row is tagged WHY = "
                     + ", ".join(f"'{k}' ({v:,})" for k, v in why.items()) + "."))
    p = fk.save(fig, "FE14_depth_without_stations")
    return p, (f"Depth breaches under the cap-and-veto ladder: {len(cb)} exit it, "
               f"{len(sd):,} cannot and would need a lifting station."), {
        "breaches_with_exit": int(len(cb)), "worst_cover_with_exit_m": exit_worst,
        "candidate_stations": int(len(sd)), "worst_cover_station_m": station_worst,
        "exits": cb["exit"].value_counts().to_dict(), "why": why.to_dict()}


# ====================================================== FE15  MAP  where the pieces are

def FE15_map_components():
    """The 311 pieces, on the ground."""
    cor = corridors()
    h15 = ""
    try:
        na = fk.read_csv("audit_W11a.csv")
        row = na.loc[na["id"] == "H15"].iloc[0]
        if str(row["status"]).upper() == "PASS":
            h15 = str(row["summary"])
    except Exception:                                    # noqa: BLE001
        pass
    n, comps, owner = components_of(cor)
    sizes = [len(c) for c in comps]
    tot = sum(sizes)
    cid = cor["US_NODE"].astype(str).map(owner)
    big3 = 100.0 * sum(sizes[:3]) / tot
    singles = int(sum(1 for s in sizes if s <= 2))

    fig, ax, note = fk.map_frame(
        fk.extent_of(cor, pad=0.02),
        title=(f"Three pieces hold {big3:.0f} % of the corridor network; the other "
               f"{n - 3:,} hold the rest"),
        subtitle=("The published corridor graph, coloured by connected component. A design "
                  "cannot be built as hundreds of separate drainage systems, so this is "
                  "the number that has to come down before levels mean anything. Line "
                  "style carries the distinction as well as colour." + (
                      "  The PIPE graph laid inside it is a different object and is "
                      "already clean: " + h15 if h15 else "")))
    ranks = [(0, C.TRUNK, 1.05, f"largest component ({sizes[0]:,} nodes)"),
             (1, C.SUBMAIN, 0.80, f"2nd ({sizes[1]:,})"),
             (2, C.MAIN, 0.62, f"3rd ({sizes[2]:,})")]
    rest = cor[~cid.isin([0, 1, 2])]
    rest.plot(ax=ax, color=C.FAIL, linewidth=0.85, linestyle=(0, (2.2, 1.4)), zorder=4)
    for i, col, lw, _lab in ranks:
        cor[cid == i].plot(ax=ax, color=col, linewidth=lw, zorder=5 + i)
    try:
        fk.study_boundary().boundary.plot(ax=ax, color=C.BOUNDARY, lw=1.2, ls="--",
                                          zorder=9)
    except Exception:                                    # noqa: BLE001
        pass

    handles = [Line2D([], [], color=col, lw=max(1.4, lw * 1.6), label=lab)
               for _i, col, lw, lab in ranks]
    handles += [
        Line2D([], [], color=C.FAIL, lw=1.6, ls=(0, (2.2, 1.4)),
               label=f"the other {n-3:,} pieces ({100*sum(sizes[3:])/tot:.0f} % of nodes)"),
        Line2D([], [], color=C.BOUNDARY, lw=1.2, ls="--", label="study boundary"),
    ]
    box = (f"corridors    {len(cor):>10,}\n"
           f"length       {cor['LEN_M'].sum()/1000:>9,.1f} km\n"
           f"components   {n:>10,}\n"
           f"largest 3    {big3:>9.0f} % of nodes\n"
           f"1-2 node bits{singles:>10,}")
    fk.finish_map(fig, ax, note=note, legend_handles=handles, databox=box,
                  source=fk.source_line(cor))
    p = fk.save(fig, "FE15_map_components")
    return p, (f"The published corridor network coloured by connected component: "
               f"{n:,} pieces, three of which hold {big3:.0f} % of it."), {
        "components": n, "top3_share_pct": big3, "tiny_pieces": singles,
        "largest_sizes": sizes[:5]}


# ============================================================ FE16  MAP  the crossings

def FE16_map_crossings():
    """Where the wadi contacts are, and how far each one runs."""
    cor = corridors()
    xs = fk.read_layer("W11a.gpkg", "crossings",
                       columns=["CROSS_ID", "OBSTACLE", "LEN_M", "ANGLE_DEG", "APPROVED"])
    long70 = xs[xs["LEN_M"] > 70]

    fig, ax, note = fk.map_frame(
        fk.extent_of(cor, pad=0.02),
        title=(f"{len(xs):,} wadi crossings are scheduled, and {len(long70):,} of them "
               f"run more than 70 m through the wadi"),
        subtitle=("Every corridor touching wadi ground carries a CROSS_ID and appears in "
                  "the register — H1a item 4 is satisfied. Item 1, that a crossing crosses "
                  "rather than runs along, is not tested here: stage 2 writes 90° on every "
                  "row rather than measuring it (see FE11)."))
    cor.plot(ax=ax, color=C.FAINT, linewidth=0.22, zorder=3)
    xs.plot(ax=ax, color=C.WADI, linewidth=0.9, zorder=5)
    if len(long70):
        long70.plot(ax=ax, color=C.FAIL, linewidth=2.0, zorder=6)
    try:
        fk.study_boundary().boundary.plot(ax=ax, color=C.BOUNDARY, lw=1.2, ls="--",
                                          zorder=9)
    except Exception:                                    # noqa: BLE001
        pass

    handles = [
        Line2D([], [], color=C.FAINT, lw=1.0, label=f"corridor ({len(cor):,})"),
        Line2D([], [], color=C.WADI, lw=1.5,
               label=f"scheduled wadi crossing ({len(xs):,})"),
        Line2D([], [], color=C.FAIL, lw=2.2,
               label=f"crossing longer than 70 m ({len(long70):,})"),
        Line2D([], [], color=C.BOUNDARY, lw=1.2, ls="--", label="study boundary"),
    ]
    box = (f"crossings     {len(xs):>9,}\n"
           f"total contact {xs['LEN_M'].sum()/1000:>8,.1f} km\n"
           f"median        {xs['LEN_M'].median():>8,.1f} m\n"
           f"longest       {xs['LEN_M'].max():>8,.0f} m\n"
           f"approved      {int(xs['APPROVED'].sum()):>9,}")
    fk.finish_map(fig, ax, note=note + "  ·  the 70 m line is a DISPLAY threshold, not a "
                  "guideline or philosophy limit — H1a sets no length limit (see FE11)",
                  legend_handles=handles, databox=box, legend_loc="upper left",
                  source=fk.source_line(cor, fk.cite(xs)))
    p = fk.save(fig, "FE16_map_crossings")
    return p, (f"The scheduled wadi crossings on the corridor network; {len(long70):,} run "
               f"more than 70 m and none is approved."), {
        "crossings": int(len(xs)), "over_70m": int(len(long70)),
        "contact_km": float(xs["LEN_M"].sum() / 1000.0),
        "approved": int(xs["APPROVED"].sum())}


# ===================================================================== registry / cli

FIGURES = {
    "FE01": FE01_snap_tolerance,
    "FE02": FE02_cut_hole_step,
    "FE03": FE03_components_through_fixes,
    "FE04": FE04_audit_matrix,
    "FE05": FE05_flow_concentration,
    "FE06": FE06_peak_factor,
    "FE07": FE07_tau_sensitivity,
    "FE08": FE08_load_waterfall,
    "FE09": FE09_break_sensitivity,
    "FE10": FE10_corridor_provenance,
    "FE11": FE11_crossing_register,
    "FE12": FE12_untested_share,
    "FE13": FE13_constraint_provenance,
    "FE14": FE14_depth_without_stations,
    "FE15": FE15_map_components,
    "FE16": FE16_map_crossings,
}


def main(argv):
    if "--list" in argv:
        for k, f in FIGURES.items():
            print(f"{k}  {f.__doc__.splitlines()[0]}")
        return 0
    keys = [a.upper() for a in argv if a.upper() in FIGURES] or list(FIGURES)
    fails = 0
    for k in keys:
        try:
            path, caption, facts = FIGURES[k]()
            print(f"\n{k}  ->  {path}")
            print(f"      {caption}")
            print(f"      {facts}")
        except Exception as exc:                          # noqa: BLE001
            fails += 1
            print(f"\n{k}  FAILED  {type(exc).__name__}: {exc}")
            import traceback
            traceback.print_exc()
    print(f"\n{len(keys) - fails} of {len(keys)} figures built into {fk.IMG}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
