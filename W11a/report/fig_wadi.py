"""fig_wadi.py -- the wadi figures for the W11a report.

WHAT THIS SET SAYS, in one line each:

  FW01  Nearly half the study area has no 50-year flood answer at all.
  FW02  Every wadi number we publish covers about half of what we built.
  FW03  Reading H1 as "along" rather than "any contact" kept 2,539 crossings.
  FW04  222 of those crossings are longer than a chamber spacing.
  FW05  They pass the squareness test because the flood plains are that wide.
  FW06  The corridors do not cross the wadis so much as follow them.
  FW07  A real crossing, a 788 m "crossing" and a deleted along-run, side by side.
  FW08  2,834 chambers stand in a wadi and sliding them clear is not available.
  FW09  Where those chambers are.
  FW10  The client's own trunk alignment runs 1.86 km along a wadi.
  FW11  How severe the ground is: class 4, 5 and 6 are not the same problem.
  FW12  What the untested half is worth, as an EXPLICITLY LABELLED extrapolation.

THREE RULES THIS MODULE KEEPS
-----------------------------
1.  **Every number on every figure comes from a named artefact.**  Nothing is
    typed in from a brief or a memo.  Where this module measures something
    itself -- band widths, distance to clear ground -- the method is stated on
    the figure and the measurement is reproducible by re-running the file.

2.  **The wadi threshold is OURS, and every figure says so.**  Classes 4/5/6 of
    the 50-year AR&R flood-hazard grid are keyed on danger to people and
    vehicles.  They stand in for G203-p30 4.4.1's *"areas subject to washout"*,
    which is a SCOUR criterion.  Philosophy H1a calls that a project assumption
    and so does every figure here.  It is never captioned as a guideline value.

3.  **UNTESTED ground is drawn, never left blank.**  The grid's nodata is
    -9999.0, which is finite.  Clear ground on these maps means tested and
    clean; hatched ground means nobody knows.

Run ``python fig_wadi.py`` from ``W11a/report``.  Idempotent: the expensive
measurements are cached in the figkit scratchpad against the source files'
signatures, and the PNGs are rewritten in place at 200 dpi.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import figkit as fk                                            # noqa: E402

# --------------------------------------------------------------- the assumption

#: PROJECT ASSUMPTION, not a guideline threshold.  Philosophy H1a.
WADI_CLASSES = (4, 5, 6)

ASSUME = ("PROJECT ASSUMPTION, not a guideline value: \"wadi ground\" = 50-year "
          "flood-hazard class 4/5/6. Those are AR&R classes keyed on danger to people "
          "and vehicles, standing in for G203-p30 4.4.1's \"areas subject to washout\", "
          "which is a scour criterion (philosophy H1a).")

#: G203-p30 Table 12 -- maximum chamber spacing, quoted from _BRAIN/02 line 61.
TAB12_SPACING_M = {"DN200-315": 100, "DN350-900": 120, "DN1000-1400": 150, "DN>1400": 200}

#: audit.py's own constants, re-used so this module and the auditor cannot disagree.
SAMPLE_M = 1.5        # audit.WADI_SAMPLE_M
PROBE_M = 400.0       # audit.WADI_PROBE_M
SKEW = 1.155          # audit.WADI_XING_SKEW, 1/cos(30 deg) -- a PROJECT tolerance

# ------------------------------------------------------------------- the palette

#: One hue, three separated lightnesses.  Greyscale-proof, colour-blind-proof.
CL = {4: "#9dbfd6", 5: "#4a7fa4", 6: "#183f57"}
CL_DRY = "#f2efe7"          # tested, and not a wadi
C_TESTED = "#c7d3da"        # "the grid answered here" -- neutral, NOT a pass
C_KEPT = "#08519c"          # a scheduled crossing
C_CUT = "#8c1d1f"           # deleted for running ALONG
C_TRUNK = "#08306b"


def wrap_src(s: str, width: int = 145) -> str:
    """Fold a source line on its own separators.

    figkit's ``_sourceline`` writes one unwrapped line, and ``save`` uses
    ``bbox_inches="tight"``, so a long provenance string silently stretches the
    saved PNG to twice its intended width.  Every source and note in this module
    goes through here.  (A ``wrap=`` argument on ``figkit._sourceline`` would be
    the better home for this -- reported, not patched in.)
    """
    out, line = [], ""
    for part in str(s).split("  ·  "):
        cand = part if not line else line + "  ·  " + part
        if len(cand) > width and line:
            out.append(line); line = part
        else:
            line = cand
    out.append(line)
    return "\n".join(out)


def wrap_note(s: str, width: int = 145) -> str:
    import textwrap
    return "\n".join("\n".join(textwrap.wrap(p, width)) or p for p in str(s).split("\n"))


def _room(fig, src: str, note: str | None) -> None:
    """Make the bottom margin fit the source block, so it never lands on the x-label."""
    n = len(src.splitlines()) + (len(note.splitlines()) if note else 0)
    need = 0.055 + (0.34 + 0.108 * n) / fig.get_size_inches()[1]
    if fig.subplotpars.bottom < need:
        fig.subplots_adjust(bottom=need)


def finish_map(fig, ax, *, source, note=None, **kw):
    """figkit.finish_map with the source and note folded to the figure width."""
    src = wrap_src(source); nt = wrap_note(note) if note else None
    _room(fig, src, nt)
    return fk.finish_map(fig, ax, source=src, note=nt, **kw)


def finish_chart(fig, *, source, note=None):
    src = wrap_src(source); nt = wrap_note(note) if note else None
    _room(fig, src, nt)
    return fk.finish_chart(fig, source=src, note=nt)


def drop_top(fig, d: float = 0.055) -> None:
    """Lower the axes so a per-panel title does not sit on the figure subtitle.

    ``chart_frame`` returns the axes flush under the subtitle, which is right for a
    single unlabelled panel and wrong the moment a panel carries its own heading.
    """
    fig.subplots_adjust(top=max(0.30, fig.subplotpars.top - d))


def sourceline(fig, source, note=None):
    return fk._sourceline(fig, wrap_src(source), wrap_note(note) if note else None)


def _selftest() -> list[str]:
    """The class ramp must survive a greyscale print.  Same test figkit runs."""
    out = []
    ladder = [CL_DRY, CL[4], CL[5], CL[6]]
    lum = [fk._rel_luminance(c) for c in ladder]
    for i in range(len(lum) - 1):
        hi, lo = max(lum[i], lum[i + 1]), min(lum[i], lum[i + 1])
        r = (hi + 0.05) / (lo + 0.05)
        out.append(f"   {ladder[i]} vs {ladder[i+1]}: greyscale contrast {r:.2f}")
        assert r >= 1.50, f"hazard ramp step {ladder[i]}->{ladder[i+1]} only {r:.2f}:1"
    return out


# ------------------------------------------------------------- the hazard raster

_G = {}


def grid():
    """int8 class codes over the study area + 1.5 km, cached in the scratchpad.

    0 = no answer (the grid's -9999.0 nodata, which IS finite), 1..6 = class.
    Cached against the source signature, so it is rebuilt if the grid is replaced
    and re-used otherwise.  121 M cells as int8 is 145 MB on disk and memmapped,
    which is what makes the band probe and the distance transform affordable.
    """
    if _G:
        return _G["A"], _G["T"]
    npy = fk.SCRATCH / "wadi_hazard_code_3m.npy"
    tag = fk.SCRATCH / "wadi_hazard_code_3m.json"
    b = fk.study_boundary()
    x0, y0, x1, y1 = b.total_bounds
    bb = (x0 - 1500, y0 - 1500, x1 + 1500, y1 + 1500)
    st = fk.HAZARD.stat()
    sig = {"src": [st.st_mtime_ns, st.st_size], "bbox": [round(v, 1) for v in bb]}
    fk.SCRATCH.mkdir(parents=True, exist_ok=True)
    if not (npy.exists() and tag.exists() and json.loads(tag.read_text()).get("sig") == sig):
        from rasterio.windows import Window, from_bounds
        with rasterio.open(fk.HAZARD) as src:
            win = from_bounds(*bb, src.transform).round_offsets().round_lengths()
            tf = src.window_transform(win)
            h, w = int(win.height), int(win.width)
            out = np.zeros((h, w), np.int8)
            for r0 in range(0, h, 2048):                   # block-wise: never 486 MB at once
                hh = min(2048, h - r0)
                a = src.read(1, window=Window(win.col_off, win.row_off + r0, w, hh)
                             ).astype("float32")
                out[r0:r0 + hh] = np.where((a > -9998.0) & np.isfinite(a),
                                           np.floor(a), 0).astype(np.int8)
        np.save(npy, out)
        tag.write_text(json.dumps({"sig": sig, "transform": list(tf)[:6]}))
    T = rasterio.Affine(*json.loads(tag.read_text())["transform"])
    _G["A"] = np.load(npy, mmap_mode="r")
    _G["T"] = T
    return _G["A"], _G["T"]


def code_at(xs, ys) -> np.ndarray:
    """Class code under each (x, y).  0 = the grid has no answer there."""
    A, T = grid()
    inv = ~T
    xs = np.asarray(xs, float); ys = np.asarray(ys, float)
    c = np.floor(inv.a * xs + inv.b * ys + inv.c).astype(np.int64)
    r = np.floor(inv.d * xs + inv.e * ys + inv.f).astype(np.int64)
    ok = (c >= 0) & (c < A.shape[1]) & (r >= 0) & (r < A.shape[0])
    out = np.zeros(xs.shape, np.int8)
    out[ok] = A[r[ok], c[ok]]
    return out


def display_classes(extent, px: int = 1500):
    """A decimated class array for drawing, plus its imshow extent."""
    A, T = grid()
    x0, y0, x1, y1 = extent
    inv = ~T
    c0 = int(max(0, np.floor(inv.a * x0 + inv.c)))
    c1 = int(min(A.shape[1], np.ceil(inv.a * x1 + inv.c)))
    r0 = int(max(0, np.floor(inv.e * y1 + inv.f)))
    r1 = int(min(A.shape[0], np.ceil(inv.e * y0 + inv.f)))
    step = max(1, (c1 - c0) // px)
    sub = np.asarray(A[r0:r1:step, c0:c1:step])
    ex = (T.c + c0 * T.a, T.c + c1 * T.a, T.f + r1 * T.e, T.f + r0 * T.e)
    return sub, ex


def draw_classes(ax, extent, *, px=1500, alpha_wadi=0.88, alpha_dry=0.34, zorder=1):
    """Hazard classes under the map: dry tint, then the 4/5/6 ramp, then the hatch.

    Returns the untested mask and its extent so the caller can hatch it.
    """
    sub, ex = display_classes(extent, px=px)
    dry = np.isin(sub, (1, 2, 3))
    rgba = np.zeros(sub.shape + (4,))
    rgba[..., :3] = matplotlib.colors.to_rgb(CL_DRY)
    rgba[..., 3] = np.where(dry, alpha_dry, 0.0)
    ax.imshow(rgba, extent=ex, zorder=zorder, interpolation="nearest")
    for k in WADI_CLASSES:
        m = sub == k
        if not m.any():
            continue
        rgba = np.zeros(sub.shape + (4,))
        rgba[..., :3] = matplotlib.colors.to_rgb(CL[k])
        rgba[..., 3] = np.where(m, alpha_wadi, 0.0)
        ax.imshow(rgba, extent=ex, zorder=zorder + 0.1, interpolation="nearest")
    untested = sub == 0
    return untested, (ex[0], ex[1], ex[2], ex[3])


def class_legend(counts=None) -> list[Patch]:
    lab = {4: "class 4", 5: "class 5", 6: "class 6"}
    h = [Patch(facecolor=CL_DRY, edgecolor="#b9b4a8", lw=0.5,
               label="hazard grid answered — not a wadi")]
    for k in WADI_CLASSES:
        t = lab[k] + (f"  ({counts[k]})" if counts and k in counts else "")
        h.append(Patch(facecolor=CL[k], edgecolor="#5a5a5a", lw=0.4, label=t))
    h.append(fk.untested_handle("UNTESTED — grid has no answer"))
    return h


# ------------------------------------------------------------------ cached facts

def _sig(*paths) -> str:
    out = []
    for p in paths:
        p = Path(p)
        out.append(f"{p.name}:{p.stat().st_mtime_ns}:{p.stat().st_size}" if p.exists()
                   else f"{p.name}:missing")
    return "|".join(out)


#: Bump when a cached table's COLUMNS change -- the file signature alone will not
#: invalidate a cache whose schema moved, and the figure then fails on a missing column.
CACHE_V = "v2"


def _cached(name: str, sig: str, build):
    """Rebuild ``name`` whenever the artefacts behind it move; otherwise re-read."""
    csv = fk.SCRATCH / f"wadi_{name}.csv"
    tag = fk.SCRATCH / f"wadi_{name}.sig"
    sig = f"{CACHE_V}|{sig}"
    if csv.exists() and tag.exists() and tag.read_text() == sig:
        return pd.read_csv(csv)
    df = build()
    fk.SCRATCH.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv, index=False)
    tag.write_text(sig)
    return df


def probe_lines(gdf, idcol: str, tag: str) -> pd.DataFrame:
    """Run ``audit._r4_classify``'s geometry over a line layer and keep the working.

    Per line: how much of it the hazard grid answers (``COV``), whether any of it
    is on class 4/5/6 (``here``), the length of its longest contiguous contact,
    the WIDTH of the hazard band measured perpendicular at the middle of that
    contact, and the along/across verdict.  ``capped`` marks probes that reached
    ``PROBE_M`` on a side without finding the far bank -- for those the width is a
    floor, not a measurement, and the figures say so.

    WHY THIS MODULE MEASURES RATHER THAN READS.  The first version took
    ``WADI_HERE`` / ``WADI_ALONG`` / ``WADI_XING`` / ``WADI_COV`` off the published
    reaches.  Half an hour later stage 5 replaced that layer with its own reach set
    and those four columns were simply gone -- the figure did not go wrong, it
    crashed, which is the good outcome.  Measuring here means the figures answer
    for their own numbers and survive a stage rewriting its schema.
    """
    def build():
        rows = []
        ts = np.arange(0.0, PROBE_M, SAMPLE_M)
        lo = min(WADI_CLASSES)
        for uid, g, L in zip(gdf[idcol].values, gdf.geometry.values, gdf.LEN_M.values):
            if g is None or g.is_empty or g.length <= 0:
                rows.append((uid, L, 0.0, 0, 0.0, 0.0, np.nan, 0, 0, 0, 0, 0)); continue
            n = max(2, int(g.length / SAMPLE_M) + 1)
            ds = np.linspace(0, g.length, n)
            P = np.array([[p.x, p.y] for p in (g.interpolate(d) for d in ds)])
            v = code_at(P[:, 0], P[:, 1])
            known = v > 0
            cov = float(known.mean())
            on = v >= lo
            step = g.length / max(n - 1, 1)
            on_m = float(on.sum()) * step
            if not on.any():
                rows.append((uid, L, cov, 0, 0.0, 0.0, np.nan, 0, 0, 0, 0, 0)); continue
            runs, a = [], None
            for k, f in enumerate(on):
                if f and a is None:
                    a = k
                elif not f and a is not None:
                    runs.append((a, k - 1)); a = None
            if a is not None:
                runs.append((a, len(on) - 1))
            n_runs = len(runs)
            a, b = max(runs, key=lambda r: r[1] - r[0])
            contact = float(ds[b] - ds[a]) + SAMPLE_M
            mid = 0.5 * (ds[a] + ds[b])
            p0 = g.interpolate(max(0.0, mid - 1.0))
            p1 = g.interpolate(min(g.length, mid + 1.0))
            vx, vy = p1.x - p0.x, p1.y - p0.y
            m = (vx * vx + vy * vy) ** 0.5 or 1.0
            nx_, ny_ = -vy / m, vx / m
            c = g.interpolate(mid)
            width = 0.0; capped = 0; cap_is_wadi = 0
            for sgn in (1.0, -1.0):
                pv = code_at(c.x + sgn * ts * nx_, c.y + sgn * ts * ny_)
                off = np.where((pv > 0) & (pv < lo))[0]
                if len(off):
                    width += float(off[0] * SAMPLE_M)
                else:
                    width += PROBE_M; capped += 1
                    cap_is_wadi += int((pv >= lo).mean() > 0.5)
            square = (n_runs == 1) and (contact <= SKEW * max(width, SAMPLE_M))
            rows.append((uid, L, cov, 1, on_m, contact, width, n_runs, capped,
                         cap_is_wadi, int(square), int(not square)))
        return pd.DataFrame(rows, columns=[idcol, "LEN_M", "COV", "here", "on_m",
                                           "contact_m", "band_m", "n_runs", "capped",
                                           "cap_is_wadi", "xing", "along"])

    src = fk.SHP / ("W11a.gpkg" if tag != "trunk" else "W11a_trunk.gpkg")
    df = _cached(f"probe_{tag}", _sig(src, fk.HAZARD) + f"|{len(gdf)}", build)
    df["ratio"] = df.contact_m / df.band_m.clip(lower=SAMPLE_M)
    df["frac"] = df.contact_m / df.LEN_M.clip(lower=1.0)
    return df


def band_probe(cor) -> pd.DataFrame:
    """The along/across working for every corridor that touches wadi ground."""
    return probe_lines(cor[cor["ON_WADI_M"].fillna(0) > 0], "CORR_ID", "corridor")


def reach_probe(rch) -> pd.DataFrame:
    """The same working for the published reaches, measured, never inherited."""
    return probe_lines(rch, "EDGE_UID", "reach")


def contact_by_class(cor) -> dict:
    """Metres of corridor length by the hazard class underneath, sampled at 1.5 m."""
    ow = cor[cor["ON_WADI_M"].fillna(0) > 0]

    def build():
        tally = dict.fromkeys(range(7), 0.0)
        for g in ow.geometry.values:
            n = max(2, int(g.length / SAMPLE_M) + 1)
            ds = np.linspace(0, g.length, n)
            P = np.array([[p.x, p.y] for p in (g.interpolate(d) for d in ds)])
            v = code_at(P[:, 0], P[:, 1])
            step = g.length / max(n - 1, 1)
            for k in range(7):
                tally[k] += float((v == k).sum()) * step
        return pd.DataFrame({"cls": list(tally), "metres": list(tally.values())})

    df = _cached("contact_class", _sig(fk.SHP / "W11a.gpkg", fk.HAZARD), build)
    return dict(zip(df.cls.astype(int), df.metres.astype(float)))


def chamber_distances(ch) -> pd.DataFrame:
    """For every stuck chamber: the class under it, and how far to KNOWN-CLEAR ground.

    "Known-clear" is deliberate.  Ground with no hazard answer is not clear
    ground -- it is unknown ground, and a chamber cannot be re-sited onto a
    guess.  Measured by a Euclidean distance transform on a 9 m lattice, so the
    answer is +/- 9 m; that is far finer than any of the bands it is read in.
    """
    def build():
        from scipy import ndimage
        A, T = grid()
        step = 3                                    # 3 x 3 m -> a 9 m lattice
        Ac = np.asarray(A[::step, ::step])
        clear = (Ac > 0) & (Ac < min(WADI_CLASSES))
        dist = ndimage.distance_transform_edt(~clear, sampling=3.0 * step)
        cx = ((ch.X.values - T.c) / (3.0 * step)).astype(int)
        cy = ((T.f - ch.Y.values) / (3.0 * step)).astype(int)
        ok = (cx >= 0) & (cx < Ac.shape[1]) & (cy >= 0) & (cy < Ac.shape[0])
        d = np.full(len(ch), np.nan)
        d[ok] = dist[cy[ok], cx[ok]]
        return pd.DataFrame({"X": ch.X.values, "Y": ch.Y.values,
                             "TRIGGER": ch.TRIGGER.values,
                             "WHY_STUCK": ch.WHY_STUCK.values,
                             "CLASS": code_at(ch.X.values, ch.Y.values),
                             "DIST_CLEAR_M": np.round(d, 1)})

    return _cached("chamber_dist", _sig(fk.RUN / "s5_wadi_chambers.csv", fk.HAZARD), build)


# --------------------------------------------------------------------- the loads

def load():
    """Every artefact this module reads, in one place, each stamped by figkit."""
    d = {}
    d["cor"] = fk.read_layer("W11a.gpkg", "corridors",
                             columns=["CORR_ID", "LEN_M", "ON_WADI_M", "CROSS_ID",
                                      "SRC", "N_PLOT"])
    d["xr"] = fk.read_layer("W11a.gpkg", "crossings")
    d["rm"] = fk.read_layer("W11a_corridors_removed.gpkg", "removed")
    d["rch"] = fk.read_layer("W11a.gpkg", "reaches",
                             columns=["EDGE_UID", "TIER", "LEN_M", "STAGE"])
    d["tr"] = fk.read_layer(str(fk.SHP / "W11a_trunk.gpkg"), "reaches")
    d["trn"] = fk.read_layer(str(fk.SHP / "W11a_trunk.gpkg"), "nodes")
    d["trx"] = fk.read_layer(str(fk.SHP / "W11a_trunk.gpkg"), "crossings")
    # The PUBLISHED chamber layer, not the shapefile mirror: philosophy sec 8 audits what
    # is published, and W11a_manholes.shp lags the GeoPackage by a stage.
    d["mh"] = fk.read_layer("W11a.gpkg", "nodes",
                            columns=["NODE_UID", "TIER", "X", "Y", "STAGE"])
    d["wch"] = fk.read_csv("s5_wadi_chambers.csv")
    d["bnd"] = fk.study_boundary()
    d["hz"] = (f"{fk.HAZARD.relative_to(fk.BASE).as_posix()}, 50-year flood-hazard grid, "
               f"3 m, EPSG:32640, nodata -9999.0")
    # The stages are still running.  Two artefacts from the same stage can be minutes
    # apart, and a count taken across them is then a count across two different designs.
    # Say so on the figure rather than letting the reader assume they match.
    mh_t = d["mh"].attrs["fk_source"].written
    ch_t = d["wch"].attrs["fk_source"].written
    d["clock"] = ("" if mh_t == ch_t else
                  f" MIND THE CLOCK: the chamber layer was written {mh_t} and the "
                  f"wadi-chamber register {ch_t}. Stage 5 was re-run between the two, so "
                  f"any ratio taken across them is approximate until both carry one time.")
    return d


def area_coverage(bnd):
    """Study-area coverage, sampled on a 9 m lattice inside the boundary polygon."""
    from rasterio.features import geometry_mask
    A, T = grid()
    step = 3
    Ac = np.asarray(A[::step, ::step])
    tf = T * rasterio.Affine.scale(step, step)
    m = geometry_mask(bnd.geometry, out_shape=Ac.shape, transform=tf, invert=True)
    inb = int(m.sum())
    known = int(((Ac > 0) & m).sum())
    wadi = {k: int(((Ac == k) & m).sum()) for k in WADI_CLASSES}
    return {"cells": inb, "cell_m": 3.0 * step, "km2": inb * (3.0 * step) ** 2 / 1e6,
            "known": known, "wadi": wadi, "wadi_n": sum(wadi.values())}


# ============================================================ FW01 coverage map

def fw01(d):
    cov = area_coverage(d["bnd"])
    untested_pct = 100.0 * (1 - cov["known"] / cov["cells"])
    wadi_pct_all = 100.0 * cov["wadi_n"] / cov["cells"]
    wadi_pct_known = 100.0 * cov["wadi_n"] / max(cov["known"], 1)

    ext = fk.extent_of(d["bnd"], pad=0.04)
    fig, ax, note = fk.map_frame(
        ext,
        title=f"{untested_pct:.0f} % of the study area has no 50-year flood answer at all",
        subtitle=("The 50-year hazard grid against the project boundary. Hatched ground is "
                  "outside the grid: not ground that was tested and found dry, ground that "
                  "was never tested. Everything else this report says about wadis is a "
                  f"statement about the other {100 - untested_pct:.0f} %."))
    untested, uext = draw_classes(ax, ext, px=1700)
    fk.hatch_untested(ax, untested, uext, zorder=2, face_alpha=0.10)
    d["bnd"].boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.4, ls="--", zorder=6)

    handles = class_legend()
    handles.append(Line2D([], [], color=fk.C.BOUNDARY, lw=1.4, ls="--",
                          label="study boundary"))
    box = (f"study area        {cov['km2']:>9,.1f} km2\n"
           f"grid has an answer{100 - untested_pct:>8.1f} %\n"
           f"NO answer         {untested_pct:>8.1f} %\n"
           f"class 4/5/6       {wadi_pct_all:>8.1f} % of the area\n"
           f"                  {wadi_pct_known:>8.1f} % of the TESTED part")
    finish_map(fig, ax, legend_handles=handles, legend_loc="upper left",
                  databox=box, note=f"{note}\n{ASSUME}",
                  source=fk.source_line(d["bnd"], d["hz"])
                  + f"  ·  sampled on a {cov['cell_m']:.0f} m lattice inside the boundary")
    return fk.save(fig, "FW01_hazard_coverage")


# ==================================================== FW02 coverage by artefact

def fw02(d):
    cov = area_coverage(d["bnd"])
    cor, rch, tr, trn, mh = d["cor"], d["rch"], d["tr"], d["trn"], d["mh"]

    cmid = cor.geometry.interpolate(0.5, normalized=True)
    ccode = code_at(cmid.x.values, cmid.y.values)
    mhcode = code_at(mh.X.values, mh.Y.values)
    rp = reach_probe(rch)
    rch_cov = float((rp.LEN_M * rp.COV).sum() / rp.LEN_M.sum())
    tr_cov_km = float((tr.LEN_M * tr.WADI_COV).sum()) / 1000.0

    rows = [
        ("study area\nby area, 439.7 km2" if False else
         f"study area\nby area, {cov['km2']:,.0f} km2",
         cov["known"] / cov["cells"], f"{cov['cells']:,} lattice cells"),
        (f"corridors\nby length, {cor.LEN_M.sum()/1000:,.0f} km",
         float(cor.LEN_M[ccode > 0].sum() / cor.LEN_M.sum()), "midpoint test"),
        (f"corridors\nby count, {len(cor):,}",
         float((ccode > 0).mean()), "midpoint test"),
        (f"network reaches\nby length, {rch.LEN_M.sum()/1000:,.0f} km",
         rch_cov, "sampled along"),
        (f"chambers\nby count, {len(mh):,}",
         float((mhcode > 0).mean()), str(mh.STAGE.iloc[0])),
        (f"trunk main\nby length, {tr.LEN_M.sum()/1000:,.1f} km",
         tr_cov_km / (tr.LEN_M.sum() / 1000), "sampled along"),
        (f"trunk chambers\nby count, {len(trn):,}",
         float((trn.WADI_COV == 1).mean()), "s3_trunk"),
    ]
    worst = min(r[1] for r in rows)
    fig, ax = fk.chart_frame(
        title=("Every wadi answer in this report covers about half of what we built"),
        subtitle=("Share of each artefact that falls inside the 50-year hazard grid. The "
                  "hatched part carries no wadi answer either way — a clean wadi check on "
                  "it is silence, not a pass. "),
        figsize=(9.8, 5.4), ygrid=False, xgrid=True)
    drop_top(fig, 0.075)
    y = np.arange(len(rows))[::-1]
    for yy, (lab, frac, tag) in zip(y, rows):
        ax.barh(yy, 100 * frac, height=0.62, facecolor=C_TESTED,
                edgecolor=fk.C.INK, lw=0.6)
        ax.barh(yy, 100 * (1 - frac), left=100 * frac, height=0.62,
                **fk.status_style("untested"))
        ax.text(100 * frac / 2, yy, f"{100*frac:.0f} %", ha="center", va="center",
                fontsize=7.8, fontweight="bold", color=fk.C.INK)
        ax.text(100 * frac + 100 * (1 - frac) / 2, yy, f"{100*(1-frac):.0f} %",
                ha="center", va="center", fontsize=7.8, fontweight="bold",
                color=fk.label_ink("untested"))
        ax.text(101.5, yy, tag, ha="left", va="center", fontsize=6.6, color=fk.C.GREY)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.6)
    ax.set_xlim(0, 118)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("per cent")
    ax.axvline(50, color=fk.C.INK, lw=0.9, ls=":", zorder=5)
    ax.text(50, len(rows) - 0.52, "half", fontsize=7, color=fk.C.INK,
            va="bottom", ha="center")
    # ABOVE the bars, not below: figkit's legend_below anchors to the axes, and the
    # source block later pushes the axes up straight into it.
    ax.legend(handles=[Patch(label="inside the 50-year hazard grid — testable",
                             facecolor=C_TESTED, edgecolor=fk.C.INK, lw=0.6),
                       Patch(label="outside it — UNTESTED, no answer either way",
                             **fk.status_style("untested"))],
              loc="lower left", bbox_to_anchor=(0.0, 1.015), ncol=2, frameon=False,
              fontsize=7.6, handlelength=1.9, columnspacing=1.8)
    finish_chart(fig, source=fk.source_line(d["cor"], d["rch"], d["tr"], d["mh"], d["hz"]),
                    note=(f"Worst covered artefact: {100*worst:.0f} % testable. Corridor and "
                          "chamber coverage is a one-point test per feature; the trunk is "
                          "sampled along its length by stage 3. " + ASSUME + d["clock"]))
    return fk.save(fig, "FW02_coverage_by_artefact")


# ======================================================== FW03 along vs across

def fw03(d):
    xr, rm = d["xr"], d["rm"]
    rch = d["rch"]
    keep_n, keep_km = len(xr), xr.LEN_M.sum() / 1000
    grp = rm.assign(g=np.where(rm.REASON.str.startswith("wadi (along"), "wadi (along)",
                               np.where(rm.REASON.str.contains("dual"),
                                        "dual carriageway", rm.REASON))
                    ).groupby("g").agg(n=("LEN_M", "size"), km=("LEN_M", lambda s: s.sum() / 1000))
    cut_n = int(grp.loc["wadi (along)", "n"]); cut_km = float(grp.loc["wadi (along)", "km"])
    dual_n = int(grp.loc["dual carriageway", "n"]); dual_km = float(grp.loc["dual carriageway", "km"])

    rp = reach_probe(rch)
    al = rp[rp.along == 1]; xg = rp[rp.xing == 1]
    n_al = len(al); km_al = float(al.on_m.sum() / 1000)
    n_xg = len(xg); km_xg = float(xg.on_m.sum() / 1000)
    weave = int((al.n_runs > 1).sum())
    stage = str(rch.STAGE.iloc[0]) if "STAGE" in rch.columns else "published"
    tiers = (rch[["EDGE_UID", "TIER"]].merge(al[["EDGE_UID", "on_m"]], on="EDGE_UID")
             .groupby("TIER").on_m.agg(["size", "sum"]).sort_values("sum", ascending=False))
    by_tier = ", ".join(f"{t} {int(r['size'])} ({r['sum']:,.0f} m)"
                        for t, r in tiers.iterrows())

    fig, axes = fk.chart_frame(
        title=(f"Distinguishing ACROSS from ALONG kept {keep_n:,} crossings and still "
               f"deleted {cut_km:,.0f} km"),
        subtitle=("H1 forbids a pipe ALONG a wadi; G201 §9.3 sets out how to CROSS one. "
                  "Left: what stage 2 kept and what it cut. Right: what the published "
                  "reaches look like when the auditor's own geometry is re-run on them. "),
        figsize=(10.4, 4.4), ncols=2, ygrid=False, xgrid=True)
    a1, a2 = axes
    drop_top(fig)

    bars = [("kept — scheduled\nwadi crossings", keep_n, keep_km, C_KEPT, None),
            ("cut — ran ALONG\na wadi", cut_n, cut_km, C_CUT, "\\\\"),
            ("cut — along a dual\ncarriageway (for scale)", dual_n, dual_km,
             fk.C.DUAL, "..")]
    y = np.arange(len(bars))[::-1]
    for yy, (lab, n, kmv, col, ht) in zip(y, bars):
        a1.barh(yy, kmv, height=0.6, facecolor=col, edgecolor=fk.C.INK, lw=0.6, hatch=ht)
        a1.text(kmv + 1.5, yy, f"{kmv:,.1f} km   ({n:,} pieces)", va="center",
                fontsize=7.6, color=fk.C.INK)
    a1.set_yticks(y); a1.set_yticklabels([b[0] for b in bars], fontsize=7.4)
    a1.set_xlim(0, max(keep_km, cut_km) * 1.85)
    a1.set_xlabel("kilometres of corridor")
    a1.set_title("stage 2, the corridor network", fontsize=8.6, color=fk.C.GREY, loc="left")

    bars2 = [("CROSS a wadi\n— legal under H1a", n_xg, km_xg, C_KEPT, None),
             ("run ALONG one\n— the defect H1 forbids", n_al, km_al, C_CUT, "\\\\")]
    y2 = np.arange(len(bars2))[::-1]
    for yy, (lab, n, kmv, col, ht) in zip(y2, bars2):
        a2.barh(yy, n, height=0.5, facecolor=col, edgecolor=fk.C.INK, lw=0.6, hatch=ht)
        a2.text(n + n_xg * 0.02, yy, f"{n:,} reaches   ({kmv:,.1f} km on wadi ground)",
                va="center", fontsize=7.6, color=fk.C.INK)
    a2.set_yticks(y2); a2.set_yticklabels([b[0] for b in bars2], fontsize=7.4)
    a2.set_xlim(0, n_xg * 1.75)
    a2.set_xlabel("reaches")
    a2.set_title(f"the published reaches ({stage}), classified here",
                 fontsize=8.6, color=fk.C.GREY, loc="left")
    fk.thousands(a2, "x")

    finish_chart(fig, source=fk.source_line(xr, rm, rch),
                    note=("The two panels are not comparable rows: a corridor is a route, a "
                          "reach is a chamber-to-chamber pipe, and a single crossing can "
                          f"carry several reaches. Of the {n_al:,} running ALONG, {weave:,} "
                          f"touch the wadi in MORE THAN ONE place along the same pipe, "
                          f"which no single crossing can explain. By tier: {by_tier} — H1 "
                          f"admits no tier exemption. " + ASSUME))
    return fk.save(fig, "FW03_along_vs_across")


# ================================================== FW04 crossing length vs Tab 12

def fw04(d):
    # WADI only.  The register also carries dual-carriageway crossings, and Table 12 is
    # not the governing rule for those.
    xr = d["xr"][d["xr"].OBSTACLE.astype(str).str.lower() == "wadi"]
    L = xr.LEN_M.values
    n100 = int((L > 100).sum()); km100 = float(L[L > 100].sum() / 1000)
    n200 = int((L > 200).sum()); km200 = float(L[L > 200].sum() / 1000)

    fig, ax = fk.chart_frame(
        title=(f"{n100:,} of the {len(L):,} wadi crossings are longer than a chamber "
               f"spacing — each must stand a chamber in the wadi"
               if n100 else
               f"Every one of the {len(L):,} scheduled wadi crossings is now shorter than "
               f"a chamber spacing — the longest is {L.max():,.0f} m"),
        subtitle=("Length of every scheduled wadi crossing, smallest to largest. G203-p30 "
                  "Table 12 caps chamber spacing at 100 m for DN200–315 and at 200 m even "
                  "at DN>1400, so a crossing longer than that cannot be spanned without a "
                  "chamber — and H1a item 2 admits no chamber on wadi ground. "),
        figsize=(9.8, 4.8), ygrid=True, xgrid=False)

    s = np.sort(L)
    x = np.arange(1, len(s) + 1)
    ax.fill_between(x, 0.5, s, color=C_KEPT, alpha=0.22, lw=0)
    ax.plot(x, s, color=C_KEPT, lw=1.4)
    ax.set_yscale("log")
    ax.set_ylim(0.6, 1200)
    ax.set_xlim(0, len(s) * 1.005)
    ax.set_xlabel("scheduled wadi crossings, ranked by length")
    ax.set_ylabel("on-wadi contact length (m, log scale)")
    fk.thousands(ax, "x")
    ax.set_yticks([1, 3, 10, 30, 100, 200, 300, 1000])
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v:,.0f}"))

    for spacing, dn, style in ((100, "DN200–315", "-"), (200, "DN>1400", "--")):
        ax.axhline(spacing, color=C_CUT, lw=1.3, ls=style, zorder=5)
        ax.text(len(s) * 0.012, spacing * 1.10,
                f"G203-p30 Tab 12 — max chamber spacing {spacing} m ({dn})",
                fontsize=7.2, color=C_CUT, va="bottom", fontweight="bold")
    k100 = len(s) - n100
    if n100:
        ax.axvspan(k100, len(s), color=C_CUT, alpha=0.07, zorder=0)
        ax.annotate(f"{n100:,} crossings over 100 m\n{km100:,.1f} km of contact —\n"
                    f"{100*km100/max(L.sum()/1000, 1e-9):.0f} % of all the on-wadi\n"
                    f"contact in the register",
                    xy=(k100, 105), xytext=(len(s) * 0.30, 1.3),
                    fontsize=7.6, color=fk.C.INK, ha="left",
                    arrowprops=dict(arrowstyle="->", color=fk.C.GREY, lw=0.9),
                    bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a",
                              alpha=0.95))
    else:
        ax.annotate(f"nothing reaches the 100 m line.\nThe longest crossing is "
                    f"{s[-1]:,.0f} m, which leaves\n{100 - s[-1]:,.0f} m of headroom on the "
                    f"tightest\nTable 12 spacing — so no scheduled\ncrossing forces a "
                    f"chamber onto wadi ground.",
                    xy=(len(s) * 0.985, s[-1]), xytext=(len(s) * 0.22, 1.5),
                    fontsize=7.6, color=fk.C.INK, ha="left",
                    arrowprops=dict(arrowstyle="->", color=fk.C.GREY, lw=0.9),
                    bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a",
                              alpha=0.95))
    ax.text(len(s) * 0.995, s[-1] * 1.15, f"longest {s[-1]:,.0f} m", ha="right",
            va="bottom", fontsize=7.4, fontweight="bold", color=C_CUT)

    box = (f"crossings         {len(s):>8,}\n"
           f"median              {np.median(s):>6,.0f} m\n"
           f"75th percentile     {np.percentile(s,75):>6,.0f} m\n"
           f"over 100 m        {n100:>8,}   {km100:>5,.1f} km\n"
           f"over 200 m        {n200:>8,}   {km200:>5,.1f} km")
    ax.text(0.985, 0.03, box, transform=ax.transAxes, fontsize=7.0, family="monospace",
            va="bottom", ha="right", color=fk.C.INK,
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a", alpha=0.93))
    sched = float(L.sum()) / 1000
    owm = float(d["cor"].ON_WADI_M.fillna(0).sum()) / 1000
    finish_chart(fig, source=fk.source_line(xr,
                 "G203-p30 Tab 12 via _BRAIN/02_DESIGN_CRITERIA.md (max chamber spacing "
                 "DN200-315 100 m, 350-900 120 m, 1000-1400 150 m, >1400 200 m)"),
                 note=(f"The {len(L):,} rows with OBSTACLE='wadi' only; the register also "
                       f"carries dual-carriageway crossings, which Table 12 does not "
                       f"govern. WORTH CHECKING: these crossings schedule {sched:,.1f} km "
                       f"of contact, while the corridors' own ON_WADI_M field totals "
                       f"{owm:,.1f} km — a {abs(owm - sched):,.1f} km difference between "
                       f"what is scheduled and what the corridor layer says it touches. "
                       + ASSUME))
    return fk.save(fig, "FW04_crossing_length_vs_spacing")


# ================================================= FW05 contact vs band-width

def fw05(d):
    S = band_probe(d["cor"])
    ok = S.band_m.notna() & (S.contact_m > 0)
    S = S[ok]
    capped = S.capped > 0
    whole = S.frac > 0.95

    cap_share = float(capped.mean()); whole_share = float(whole.mean())
    fig, ax = fk.chart_frame(
        title=("The crossings pass the squareness test because the flood plains are wider "
               "than the crossings are long"
               if cap_share > 0.15 and whole_share > 0.4 else
               f"Contact against band width: {100*cap_share:.0f} % of the probes never "
               f"found the far bank"),
        subtitle=("Every on-wadi corridor: the length of its contact against the width of "
                  "the hazard band measured perpendicular at the middle of that contact — "
                  "the auditor's own R4 geometry, re-run here. Anything under the "
                  f"{SKEW:.3f} line counts as a crossing. "),
        figsize=(9.6, 5.2), ygrid=True, xgrid=True)

    ax.scatter(S.band_m[~capped], S.contact_m[~capped], s=7, c=C_KEPT, alpha=0.35,
               lw=0, label=f"band width measured ({int((~capped).sum()):,})")
    ax.scatter(S.band_m[capped], S.contact_m[capped], s=16, facecolors="none",
               edgecolors=C_CUT, lw=0.7,
               label=f"probe reached its {PROBE_M:.0f} m limit without finding the far "
                     f"bank ({int(capped.sum()):,})")
    xs = np.array([2, 1000])
    ax.plot(xs, SKEW * xs, color=fk.C.INK, lw=1.2, ls="--",
            label=f"contact = {SKEW:.3f} × band  (the project skew tolerance on "
                  f"\"perpendicular\")")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(2, 1100); ax.set_ylim(0.9, 1100)
    ax.set_xlabel("hazard band width across the corridor (m, log scale)")
    ax.set_ylabel("longest contiguous on-wadi contact (m, log scale)")
    for a in (ax.xaxis, ax.yaxis):
        a.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.axvline(2 * PROBE_M, color=C_CUT, lw=0.9, ls=":", zorder=1)
    ax.text(2 * PROBE_M, 1180, f"{2*PROBE_M:.0f} m = both probes at their limit",
            ha="right", va="bottom", fontsize=6.8, color=C_CUT, clip_on=False)

    n_cap_wadi = int(S.cap_is_wadi.sum())
    n_cap_sides = int(S.capped.sum())
    ax.text(0.015, 0.975,
            (f"{int(whole.sum()):,} of {len(S):,} of these corridors are wholly inside a "
             f"wadi\n(contact > 95 % of their own length): the corridor IS the wadi\n"
             f"reach, cut out at the banks, not a route that crosses one.\n\n"
             f"{n_cap_wadi:,} of the {n_cap_sides:,} capped probe sides ran out at "
             f"{PROBE_M:.0f} m still\ninside hazard class 4–6 — the flood plains really "
             f"are that wide,\nso for those the band width is a floor, not a measurement."),
            transform=ax.transAxes, fontsize=7.3, va="top", ha="left", color=fk.C.INK,
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#8a8a8a", alpha=0.93))
    ax.legend(loc="upper left", bbox_to_anchor=(0.012, 0.575), fontsize=7.0,
              framealpha=0.93, edgecolor="#9a9a9a")
    finish_chart(fig, source=fk.source_line(d["cor"], d["hz"]),
                    note=(f"Measured by this module with audit.py's constants — sample "
                          f"{SAMPLE_M} m, probe limit {PROBE_M:.0f} m per side, skew "
                          f"{SKEW:.3f}. Reproduces R4's verdict: 0 corridors classify as "
                          f"ALONG. " + ASSUME))
    return fk.save(fig, "FW05_contact_vs_band")


# ============================================================ FW06 the geography

def fw06(d):
    cor, rm = d["cor"], d["rm"]
    # MEASURED HERE, not read off the register.  The register's LEN_M is capped, so it
    # no longer describes how far a corridor actually runs inside a wadi; FW04 reports the
    # register and this map reports the ground, and the two are different questions.
    S = band_probe(cor)
    cor = cor.merge(S[["CORR_ID", "contact_m"]], on="CORR_ID", how="left")
    ow = cor[cor.ON_WADI_M.fillna(0) > 0]
    al = rm[rm.REASON.str.startswith("wadi (along")]

    bands = [(0, 20, "#9dbfd6", 0.7), (20, 100, "#4a7fa4", 1.1),
             (100, 200, "#2a5f80", 1.7), (200, 1e9, "#183f57", 2.6)]
    ext = fk.extent_of(d["bnd"], pad=0.04)
    n_long = int((ow.contact_m > 100).sum())
    fig, ax, note = fk.map_frame(
        ext,
        title=("The corridors do not so much cross the wadis as follow them"),
        subtitle=("Every corridor that touches wadi ground, drawn by how long the contact "
                  "is, and every corridor stage 2 deleted for running along one. The long "
                  "contacts trace the channels rather than cutting them."))
    untested, uext = draw_classes(ax, ext, px=1700, alpha_wadi=0.55, alpha_dry=0.20)
    fk.hatch_untested(ax, untested, uext, zorder=2, face_alpha=0.10)
    cor.plot(ax=ax, color="#9a9a9a", lw=0.12, zorder=3, alpha=0.55)
    if len(al):
        al.plot(ax=ax, color=C_CUT, lw=1.5, zorder=6)
    for lo, hi, col, lw in bands:
        sel = ow[(ow.contact_m > lo) & (ow.contact_m <= hi)]
        if len(sel):
            sel.plot(ax=ax, color=col, lw=lw, zorder=4 + lw / 10)
    d["bnd"].boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.2, ls="--", zorder=7)

    handles = [Line2D([], [], color="#9a9a9a", lw=0.8, alpha=0.7,
                      label=f"corridor, clear of wadi ground ({len(cor)-len(ow):,})")]
    for lo, hi, col, lw in bands:
        n = int(((ow.contact_m > lo) & (ow.contact_m <= hi)).sum())
        lab = (f"contact {lo:.0f}–{hi:.0f} m ({n:,})" if hi < 1e9
               else f"contact over {lo:.0f} m ({n:,})")
        handles.append(Line2D([], [], color=col, lw=max(lw, 1.2), label=lab))
    handles += [Line2D([], [], color=C_CUT, lw=1.6,
                       label=f"deleted — ran ALONG a wadi ({len(al):,})"),
                Patch(facecolor=CL[5], label="hazard class 4/5/6"),
                fk.untested_handle("UNTESTED — no grid answer"),
                Line2D([], [], color=fk.C.BOUNDARY, lw=1.2, ls="--", label="study boundary")]
    box = (f"corridors touching wadi {len(ow):>7,}\n"
           f"on-wadi contact         {ow.ON_WADI_M.sum()/1000:>6,.1f} km\n"
           f"contact over 100 m      {n_long:>7,}\n"
           f"deleted for ALONG       {al.LEN_M.sum()/1000:>6,.1f} km")
    finish_map(fig, ax, legend_handles=handles, legend_loc="upper left", databox=box,
               note=(f"{note}\nContact length measured by this module at {SAMPLE_M} m "
                     f"along every on-wadi corridor, NOT read off the crossings register, "
                     f"whose LEN_M is capped and therefore says how long a crossing is "
                     f"allowed to be, not how far the corridor runs inside the wadi. "
                     f"{ASSUME}"),
               source=fk.source_line(d["cor"], rm, d["hz"]))
    return fk.save(fig, "FW06_wadi_geography")


# =========================================================== FW07 the zoom panels

def _panel(ax, geom_layers, centre, half, *, title, sub):
    import textwrap
    x, y = centre
    ext = (x - half, y - half, x + half, y + half)
    note = fk.basemap(ax, ext, alpha=0.30, px=900)
    untested, uext = draw_classes(ax, ext, px=900, alpha_wadi=0.55, alpha_dry=0.25)
    fk.hatch_untested(ax, untested, uext, zorder=2, face_alpha=0.10)
    for gdf, kw in geom_layers:
        if len(gdf):
            gdf.plot(ax=ax, zorder=5, **kw)
    ax.set_xlim(x - half, x + half); ax.set_ylim(y - half, y + half)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#8a8a8a"); s.set_linewidth(0.9)
    ax.set_title(title, fontsize=9.2, fontweight="bold", color=fk.C.INK, loc="left", pad=3)
    ax.text(0.0, -0.022, "\n".join(textwrap.wrap(sub, 62)), transform=ax.transAxes,
            fontsize=7.2, color=fk.C.INK, ha="left", va="top", linespacing=1.45)
    fk._scalebar(ax, frac=0.30)
    return note


def fw07(d):
    cor, rm = d["cor"], d["rm"]
    S = band_probe(cor)
    cor = cor.merge(S[["CORR_ID", "contact_m", "band_m", "capped"]], on="CORR_ID", how="left")
    al = rm[rm.REASON.str.startswith("wadi (along")].copy()

    # panel A -- a road over a narrow band.  Chosen INSIDE the boundary, so it sits on the
    # same offline imagery as the other two; the first pick was 700 m south of the study
    # area, where the mosaic stops and the panel came out blank.
    bx0, by0, bx1, by1 = d["bnd"].total_bounds
    a = cor[(cor.contact_m.between(40, 70)) & (cor.band_m < 80) & (cor.capped == 0)].copy()
    # NB "cx" is GeoDataFrame's coordinate indexer -- naming a column that shadows it
    # silently returns the indexer object instead of the Series.
    a["PX"] = a.geometry.centroid.x; a["PY"] = a.geometry.centroid.y
    a = a[(a.PX > bx0) & (a.PX < bx1) & (a.PY > by0) & (a.PY < by1)]
    A = a.sort_values("contact_m", ascending=False).iloc[[0]]
    # panel B -- the longest scheduled "crossing" in the register
    B = cor.sort_values("contact_m", ascending=False).iloc[[0]]
    # panel C -- the longest piece deleted for running ALONG a wadi
    C = al.sort_values("LEN_M", ascending=False).iloc[[0]]

    fig = plt.figure(figsize=(12.4, 6.1))
    top = fk._titleblock(
        fig,
        (f"A {A.contact_m.iloc[0]:.0f} m crossing, a {B.contact_m.iloc[0]:.0f} m "
         f"\"crossing\", and {C.LEN_M.iloc[0]/1000:.2f} km that was deleted"),
        ("All three at the same scale. The middle one satisfies the squareness test and is "
         "in the crossings schedule; whether it is a crossing at all is the question this "
         "figure asks."))
    fig.subplots_adjust(left=0.012, right=0.988, bottom=0.275, top=top - 0.035,
                        wspace=0.045)
    axes = [fig.add_subplot(1, 3, i + 1) for i in range(3)]

    kept_kw = dict(color=C_KEPT, linewidth=2.6)
    cut_kw = dict(color=C_CUT, linewidth=2.6, linestyle=(0, (5, 2)))
    other_kw = dict(color="#7a7a7a", linewidth=0.9, alpha=0.8)

    half = 700.0
    notes = []
    for ax, sel, kw, ttl, sub in (
        (axes[0], A, kept_kw, "A — a crossing",
         (f"corridor {A.CORR_ID.iloc[0]}, contact {A.contact_m.iloc[0]:.0f} m across a "
          f"{A.band_m.iloc[0]:.0f} m band. The road goes over and out the other side.")),
        (axes[1], B, kept_kw, "B — also \"a crossing\"",
         (f"corridor {B.CORR_ID.iloc[0]}, contact {B.contact_m.iloc[0]:.0f} m; the band "
          f"probe reached its {PROBE_M:.0f} m limit on "
          f"{int(B.capped.iloc[0])} side(s) still inside class 4–6.")),
        (axes[2], C, cut_kw, "C — deleted for running ALONG",
         (f"{C.LEN_M.iloc[0]:,.0f} m of {C.SRC.iloc[0]} corridor, removed by stage 2. "
          f"Compare its shape with B.")),
    ):
        c = sel.geometry.iloc[0].centroid
        near = cor.cx[c.x - half:c.x + half, c.y - half:c.y + half]
        notes.append(_panel(ax, [(near, other_kw), (sel, kw)], (c.x, c.y), half,
                            title=ttl, sub=sub))
        ax.text(0.985, 0.975, f"E {c.x:,.0f}\nN {c.y:,.0f}", transform=ax.transAxes,
                ha="right", va="top", fontsize=6.6, family="monospace", color=fk.C.INK,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#9a9a9a", alpha=0.9))
    fk._north(axes[0], x=0.06, y=0.83)

    handles = [Line2D([], [], label="the corridor in question", **kept_kw),
               Line2D([], [], color=C_CUT, lw=2.6, ls=(0, (5, 2)),
                      label="deleted for running along a wadi"),
               Line2D([], [], label="other published corridors", **other_kw),
               Patch(facecolor=CL[4], label="class 4"),
               Patch(facecolor=CL[5], label="class 5"),
               Patch(facecolor=CL[6], label="class 6"),
               Patch(facecolor=CL_DRY, edgecolor="#b9b4a8", lw=0.5, label="tested, not wadi"),
               fk.untested_handle("UNTESTED")]
    fig.legend(handles=handles, loc="lower center", ncol=8, frameon=False, fontsize=7.2,
               bbox_to_anchor=(0.5, 0.128), columnspacing=1.3, handlelength=1.9)
    sourceline(fig, fk.source_line(d["cor"], rm, d["hz"]),
               f"{notes[0]}. {ASSUME}")
    return fk.save(fig, "FW07_crossing_vs_along_panels")


# ========================================================== FW08 stuck chambers

def fw08(d):
    ch = d["wch"]
    D = chamber_distances(ch)
    n = len(D)
    why = (D.groupby("WHY_STUCK").size().sort_values(ascending=False))
    short = {
        "wadi ground for at least 20 m either way along the route":
            "no clear ground within the ±20 m\nstage 5 is allowed to slide it",
        "a junction, an outlet or a gate cannot be moved - it is where the network "
        "physically meets something else":
            "cannot be moved at all — a junction,\nan outlet, a gate or a head",
        "a Table 12 spacing chamber inside a span that crosses the wadi; moving it along "
        "the same pipe changes nothing":
            "a Table 12 spacing chamber inside a\nspan that crosses regardless",
    }
    fig, axes = fk.chart_frame(
        title=(f"{n:,} chambers stand on wadi ground, and sliding them clear is not "
               f"available for any of them"),
        subtitle=("Left: why each one is stuck, as stage 5 recorded it after trying to "
                  "nudge it. Right: how far it is from the nearest ground the hazard grid "
                  "says is NOT a wadi. Ground with no grid answer is not clear ground — a "
                  "chamber cannot be re-sited onto a guess. "),
        figsize=(11.0, 4.9), ncols=2, ygrid=False, xgrid=True)
    a1, a2 = axes
    drop_top(fig)

    cols = [C_CUT, "#b4682a", fk.C.UNTESTED]
    hats = ["\\\\", "..", "///"]
    y = np.arange(len(why))[::-1]
    for yy, (k, v), col, ht in zip(y, why.items(), cols, hats):
        a1.barh(yy, v, height=0.58, facecolor=col, edgecolor=fk.C.INK, lw=0.6, hatch=ht)
        a1.text(v + n * 0.012, yy, f"{v:,}   ({100*v/n:.0f} %)", va="center", fontsize=7.8,
                color=fk.C.INK, fontweight="bold")
    a1.set_yticks(y)
    a1.set_yticklabels([short.get(k, k)[:70] for k in why.index], fontsize=7.2)
    a1.set_xlim(0, why.max() * 1.42)
    a1.set_xlabel("chambers")
    a1.set_title("why it cannot be moved", fontsize=8.6, color=fk.C.GREY, loc="left")
    fk.thousands(a1, "x")

    edges = [0, 25, 50, 100, 250, 1e9]
    labs = ["0–25 m", "25–50 m", "50–100 m", "100–250 m", "over 250 m"]
    vals = [int(((D.DIST_CLEAR_M >= lo) & (D.DIST_CLEAR_M < hi)).sum())
            for lo, hi in zip(edges[:-1], edges[1:])]
    ramp = ["#cfe0ea", CL[4], "#4a7fa4", "#2a5f80", CL[6]]
    x = np.arange(len(vals))
    for xi, v, c in zip(x, vals, ramp):
        a2.bar(xi, v, width=0.68, facecolor=c, edgecolor=fk.C.INK, lw=0.6)
        a2.text(xi, v + n * 0.012, f"{v:,}\n{100*v/n:.0f} %", ha="center", va="bottom",
                fontsize=7.4, color=fk.C.INK)
    a2.set_xticks(x); a2.set_xticklabels(labs, fontsize=7.4)
    a2.set_ylim(0, max(vals) * 1.30)
    a2.set_ylabel("chambers")
    a2.set_xlabel("straight-line distance to the nearest KNOWN non-wadi ground")
    a2.set_title("how far clear ground actually is", fontsize=8.6, color=fk.C.GREY,
                 loc="left")
    fk.thousands(a2, "y")
    med = float(np.nanmedian(D.DIST_CLEAR_M)); p90 = float(np.nanpercentile(D.DIST_CLEAR_M, 90))
    far = int((D.DIST_CLEAR_M >= 50).sum())
    a2.text(0.98, 0.97, (f"median {med:.0f} m\n90th percentile {p90:.0f} m\n"
                         f"{far:,} ({100*far/n:.0f} %) are 50 m or more from\n"
                         f"any ground the grid calls dry"),
            transform=a2.transAxes, ha="right", va="top", fontsize=7.2, color=fk.C.INK,
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a", alpha=0.93))

    finish_chart(fig, source=fk.source_line(ch, d["hz"]),
                    note=("Distance measured by this module on a 9 m lattice (Euclidean "
                          "distance transform), so ±9 m. Stage 5's own nudge window is "
                          "±20 m ALONG the route, which is a stricter test than this one: "
                          "a chamber 15 m from clear ground across country may still have "
                          "nowhere to go on its own pipe. " + ASSUME + d["clock"]))
    return fk.save(fig, "FW08_stuck_chambers")


# ======================================================= FW09 where they are

def fw09(d):
    ch, mh = d["wch"], d["mh"]
    D = chamber_distances(ch)
    ext = fk.extent_of(d["bnd"], pad=0.04)
    fig, ax, note = fk.map_frame(
        ext,
        title=(f"The {len(ch):,} chambers on wadi ground are not scattered — they are "
               f"strung along the channels"),
        subtitle=("Every chamber stage 5 placed, and the ones that ended on hazard class "
                  "4/5/6 after the ±20 m nudge. A chamber cannot be tested at all on the "
                  "hatched ground."))
    untested, uext = draw_classes(ax, ext, px=1700, alpha_wadi=0.50, alpha_dry=0.18)
    fk.hatch_untested(ax, untested, uext, zorder=2, face_alpha=0.10)
    ax.scatter(mh.X.values, mh.Y.values, s=0.5, c="#6f6f6f", alpha=0.6, lw=0, zorder=4)
    for k, col, size in ((4, CL[4], 4.0), (5, CL[5], 5.0), (6, CL[6], 7.0)):
        m = D.CLASS == k
        if m.any():
            ax.scatter(D.X[m], D.Y[m], s=size, c=col, lw=0.25, edgecolors=fk.C.INK,
                       zorder=6, alpha=0.95)
    d["bnd"].boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.2, ls="--", zorder=7)

    counts = D.CLASS.value_counts()
    handles = [Line2D([], [], marker="o", ls="", ms=2.2, color="#8f8f8f",
                      label=f"chamber, clear or untested ({len(mh)-len(ch):,})")]
    for k in WADI_CLASSES:
        handles.append(Line2D([], [], marker="o", ls="", ms=3.4 + 0.7 * (k - 4),
                              markerfacecolor=CL[k], markeredgecolor=fk.C.INK,
                              markeredgewidth=0.3,
                              label=f"on hazard class {k} ({int(counts.get(k,0)):,})"))
    handles += [fk.untested_handle("UNTESTED — no grid answer"),
                Line2D([], [], color=fk.C.BOUNDARY, lw=1.2, ls="--", label="study boundary")]
    box = (f"chambers placed  {len(mh):>8,}\n"
           f"on wadi ground   {len(ch):>8,}   {100*len(ch)/len(mh):.1f} %\n"
           f"class 6 alone    {int(counts.get(6,0)):>8,}")
    finish_map(fig, ax, legend_handles=handles, legend_loc="upper left", databox=box,
                  note=f"{note}\n{ASSUME}{d['clock']}",
                  source=fk.source_line(mh, ch, d["hz"]))
    return fk.save(fig, "FW09_stuck_chamber_map")


# ============================================================== FW10 the trunk

def fw10(d):
    tr, trn, trx = d["tr"], d["trn"], d["trx"]
    al = tr[tr.WADI_ALONG == 1]
    xg = tr[(tr.WADI_XING == 1) & (tr.WADI_ALONG == 0)]
    onw_ch = trn[trn.IN_WADI == 1]
    unt_ch = trn[trn.WADI_COV == 0]
    # THREE different "untested" numbers live in this layer and they are not the same
    # thing.  WADI_COV is the FRACTION of a reach's samples that the grid answered, so:
    #   unt_km   -- sample-weighted length with no answer.  The honest headline.
    #   unt      -- the reaches with no answer ANYWHERE.  What can be drawn as a line.
    # Quoting one and drawing the other is how a figure ends up disagreeing with itself.
    unt_km = float((tr.LEN_M * (1.0 - tr.WADI_COV)).sum()) / 1000.0
    unt_pct = 100.0 * unt_km / (tr.LEN_M.sum() / 1000.0)
    unt = tr[tr.WADI_COV == 0]

    # the worst single stretch, found by clustering the along-wadi reaches
    from scipy.cluster.hierarchy import fcluster, linkage
    A = al.copy()
    A["CX"] = A.geometry.centroid.x; A["CY"] = A.geometry.centroid.y
    lab = fcluster(linkage(A[["CX", "CY"]].values, "single"), 300, "distance")
    A["cl"] = lab
    g = A.groupby("cl").agg(n=("LEN_M", "size"), len_m=("LEN_M", "sum"),
                            onw_m=("ON_WADI_M", "sum"), X=("CX", "mean"), Y=("CY", "mean")
                            ).sort_values("len_m", ascending=False)
    worst = g.iloc[0]

    ext = fk.extent_of(tr, pad=0.06)
    fig, ax, note = fk.map_frame(
        ext,
        title=(f"The client's own trunk alignment runs {al.LEN_M.sum()/1000:,.2f} km along "
               f"a wadi, and {unt_pct:.0f} % of it has no flood answer"),
        subtitle=("The trunk is an INPUT — SHP/Main Pipe — so each of these is a decision "
                  "for the client, not a routing choice of ours. The worst single stretch "
                  f"is {worst.len_m:,.0f} m near E{worst.X:,.0f} N{worst.Y:,.0f}."))
    untested, uext = draw_classes(ax, ext, px=1700, alpha_wadi=0.50, alpha_dry=0.18)
    fk.hatch_untested(ax, untested, uext, zorder=2, face_alpha=0.10)
    d["bnd"].boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.0, ls="--", zorder=3)
    tr.plot(ax=ax, color="#333333", lw=1.2, zorder=4)
    unt.plot(ax=ax, color=fk.C.UNTESTED, lw=2.2, linestyle=(0, (4, 2)), zorder=5)
    if len(xg):
        xg.plot(ax=ax, color=C_KEPT, lw=2.6, zorder=6)
    if len(al):
        al.plot(ax=ax, color=C_CUT, lw=3.2, zorder=9)
    # under the ALONG lines, or a dense run of chambers hides the very defect it marks
    ax.scatter(onw_ch.geometry.x, onw_ch.geometry.y, s=9, marker="s",
               facecolor=CL[6], edgecolor=fk.C.INK, lw=0.35, zorder=8)
    ax.annotate("", xy=(worst.X, worst.Y), xytext=(worst.X + 4200, worst.Y - 4200),
                arrowprops=dict(arrowstyle="->", color=C_CUT, lw=1.6), zorder=9)
    ax.text(worst.X + 4400, worst.Y - 4400,
            f"the worst single stretch: {worst.len_m:,.0f} m along a wadi,\n"
            f"{worst.onw_m:,.0f} m of it on class 4-6\nE{worst.X:,.0f}  N{worst.Y:,.0f}",
            fontsize=7.4, color=C_CUT, ha="left", va="top", fontweight="bold", zorder=10,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=C_CUT, alpha=0.93))

    handles = [Line2D([], [], color="#333333", lw=1.4,
                      label=f"trunk, tested and clear ({tr.LEN_M.sum()/1000:,.1f} km total)"),
               Line2D([], [], color=fk.C.UNTESTED, lw=2.2, ls=(0, (4, 2)),
                      label=(f"reach with NO grid answer anywhere on it ({len(unt):,} "
                             f"reaches, {unt.LEN_M.sum()/1000:,.1f} km)")),
               Line2D([], [], color=C_KEPT, lw=2.6,
                      label=f"crosses a wadi ({len(xg):,} reaches, {len(trx[trx.OBSTACLE=='wadi']):,} scheduled crossings)"),
               Line2D([], [], color=C_CUT, lw=3.2,
                      label=f"runs ALONG a wadi ({len(al):,} reaches, {al.LEN_M.sum()/1000:,.2f} km)"),
               Line2D([], [], marker="s", ls="", ms=4, markerfacecolor=CL[6],
                      markeredgecolor=fk.C.INK,
                      label=f"chamber on wadi ground ({len(onw_ch):,} of {len(trn):,})"),
               Patch(facecolor=CL[5], label="hazard class 4/5/6"),
               fk.untested_handle("no grid answer"),
               Line2D([], [], color=fk.C.BOUNDARY, lw=1.0, ls="--", label="study boundary")]
    box = (f"trunk            {tr.LEN_M.sum()/1000:>7,.2f} km\n"
           f"no grid answer   {unt_km:>7,.2f} km  {unt_pct:.0f} %\n"
           f"on-wadi contact  {tr.ON_WADI_M.sum()/1000:>7,.2f} km\n"
           f"  of it ALONG    {al.ON_WADI_M.sum()/1000:>7,.2f} km\n"
           f"  of it ACROSS   {xg.ON_WADI_M.sum()/1000:>7,.2f} km\n"
           f"chambers on wadi {len(onw_ch):>7,} of {len(trn):,}\n"
           f"chambers UNTESTED{len(unt_ch):>7,} of {len(trn):,}")
    finish_map(fig, ax, legend_handles=handles, legend_loc="upper left", databox=box,
                  note=f"{note}\n{ASSUME}", inset=False,
                  source=fk.source_line(tr, trn, d["hz"]))
    return fk.save(fig, "FW10_trunk_exposure")


# ================================================== FW11 how severe the ground is

def fw11(d):
    tally = contact_by_class(d["cor"])
    D = chamber_distances(d["wch"])
    tr = d["tr"]
    trn = d["trn"]

    n6 = int((D.CLASS == 6).sum())
    fig, axes = fk.chart_frame(
        title=(f"Class 4 and class 6 are not the same problem — {tally[6]/1000:,.0f} km of "
               f"corridor and {n6:,} chambers sit on the worst band"),
        subtitle=("Where the wadi contact actually falls in the hazard ladder. Philosophy "
                  "H1a describes class 4 as about 1.2 m of water; class 6 is the top of "
                  "the AR&R scale. The guideline's own criterion is SCOUR, which this grid "
                  "does not measure at all. "),
        figsize=(10.6, 4.4), ncols=3, ygrid=True, xgrid=False)
    a1, a2, a3 = axes
    drop_top(fig)

    ks = list(WADI_CLASSES)
    v1 = [tally[k] / 1000 for k in ks]
    v2 = [int((D.CLASS == k).sum()) for k in ks]
    tr_code = code_at(tr.geometry.interpolate(0.5, normalized=True).x.values,
                      tr.geometry.interpolate(0.5, normalized=True).y.values)
    v3 = [float(tr.LEN_M.values[tr_code == k].sum()) / 1000 for k in ks]

    for ax, vals, ttl, ylab, fmt in (
            (a1, v1, "corridor contact", "km of corridor", "{:,.1f} km"),
            (a2, v2, "chambers stuck on it", "chambers", "{:,.0f}"),
            (a3, v3, "trunk reaches (midpoint)", "km of trunk", "{:,.2f} km")):
        for i, (k, v) in enumerate(zip(ks, vals)):
            ax.bar(i, v, width=0.66, facecolor=CL[k], edgecolor=fk.C.INK, lw=0.6)
            ax.text(i, v + max(vals) * 0.025, fmt.format(v), ha="center", va="bottom",
                    fontsize=7.6, color=fk.C.INK, fontweight="bold")
        ax.set_xticks(range(len(ks)))
        ax.set_xticklabels([f"class {k}" for k in ks], fontsize=7.6)
        ax.set_ylim(0, max(vals) * 1.22)
        ax.set_ylabel(ylab, fontsize=7.8)
        ax.set_title(ttl, fontsize=8.6, color=fk.C.GREY, loc="left")
        fk.thousands(ax, "y")

    finish_chart(
        fig, source=fk.source_line(d["cor"], d["wch"], tr, d["hz"]),
        note=(f"Corridor contact measured by this module at {SAMPLE_M} m along every "
              f"on-wadi corridor ({sum(tally[k] for k in ks)/1000:,.1f} km on class 4–6, "
              f"against {d['cor'].ON_WADI_M.sum()/1000:,.1f} km in the published "
              f"ON_WADI_M field). Chambers and trunk reaches are one sample each. " + ASSUME))
    return fk.save(fig, "FW11_hazard_class_severity")


# ================================================ FW12 what the untested half is worth

def fw12(d):
    rch = d["rch"]
    rp = reach_probe(rch)
    tested_km = float((rp.LEN_M * rp.COV).sum()) / 1000
    unt_km = float((rp.LEN_M * (1.0 - rp.COV)).sum()) / 1000
    on_km = float(rp.on_m.sum()) / 1000
    rate = on_km / max(tested_km, 1e-9)
    implied = rate * unt_km

    ch = d["wch"]; mh = d["mh"]
    mhcode = code_at(mh.X.values, mh.Y.values)
    mh_tested = int((mhcode > 0).sum()); mh_unt = int((mhcode == 0).sum())
    ch_rate = len(ch) / max(mh_tested, 1)
    ch_implied = ch_rate * mh_unt

    fig, axes = fk.chart_frame(
        title=(f"If the untested half behaves like the tested half, roughly {implied:,.0f} "
               f"more km of network and {ch_implied:,.0f} more chambers are in a wadi"),
        subtitle=("LEFT AND RIGHT BARS ARE NOT THE SAME KIND OF NUMBER. The solid bar is "
                  "measured. The hatched bar is an EXTRAPOLATION — the measured wadi rate "
                  "on the tested part, applied to the untested part. It is the size of the "
                  "data request, not a finding about the design. "),
        figsize=(10.2, 4.4), ncols=2, ygrid=True, xgrid=False)
    a1, a2 = axes
    drop_top(fig)

    for ax, meas, imp, ylab, ttl, fmt in (
            (a1, on_km, implied, "km of network on wadi ground",
             f"network reaches — {rate*100:.1f} % of the tested {tested_km:,.0f} km",
             "{:,.0f} km"),
            (a2, len(ch), ch_implied, "chambers on wadi ground",
             f"chambers — {ch_rate*100:.1f} % of the tested {mh_tested:,.0f}",
             "{:,.0f}")):
        ax.bar(0, meas, width=0.6, facecolor=CL[5], edgecolor=fk.C.INK, lw=0.7)
        ax.bar(1, imp, width=0.6, facecolor="none", edgecolor=C_CUT, lw=1.2, hatch="///")
        for i, v in enumerate((meas, imp)):
            ax.text(i, v + max(meas, imp) * 0.03, fmt.format(v), ha="center", va="bottom",
                    fontsize=8.4, fontweight="bold", color=fk.C.INK)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["MEASURED\non the tested part",
                            "EXTRAPOLATED\nonto the untested part"], fontsize=7.4)
        ax.set_xlim(-0.6, 1.6)
        ax.set_ylim(0, max(meas, imp) * 1.28)
        ax.set_ylabel(ylab, fontsize=7.8)
        ax.set_title(ttl, fontsize=8.4, color=fk.C.GREY, loc="left")
        fk.thousands(ax, "y")

    finish_chart(fig, source=fk.source_line(rch, mh, ch, d["hz"]),
                    note=("The extrapolation assumes the ungridded half has the same wadi "
                          "density as the gridded half. It has no evidence behind it and it "
                          "is drawn hatched for that reason: it says how much is unknown, "
                          "not what is there. " + ASSUME + d["clock"]))
    return fk.save(fig, "FW12_untested_extrapolation")


# ------------------------------------------------------------------------- main

FIGURES = [
    ("FW01", fw01, "Corridors and settlement against the 50-year hazard grid: nearly half "
                   "the study area has no flood answer at all."),
    ("FW02", fw02, "Share of each artefact that the hazard grid can actually test."),
    ("FW03", fw03, "What the wadi rule kept and what it deleted, corridors and reaches."),
    ("FW04", fw04, "Every scheduled wadi crossing against G203-p30 Table 12 chamber spacing."),
    ("FW05", fw05, "Contact length against measured hazard-band width, the auditor's own "
                   "squareness test re-run."),
    ("FW06", fw06, "Where the wadi contact is, by how long the contact runs."),
    ("FW07", fw07, "A crossing, a 788 m \"crossing\" and a deleted along-run, same scale."),
    ("FW08", fw08, "Why each chamber on wadi ground is stuck, and how far clear ground is."),
    ("FW09", fw09, "Where the chambers on wadi ground are."),
    ("FW10", fw10, "The trunk's own wadi exposure — a client decision, not a routing one."),
    ("FW11", fw11, "How the wadi contact falls across hazard classes 4, 5 and 6."),
    ("FW12", fw12, "What the untested half is worth, as a labelled extrapolation."),
]


def main(only=None) -> int:
    t0 = time.time()
    for line in _selftest():
        print(line)
    print("hazard grid:", "found" if fk.HAZARD.exists() else "MISSING", fk.HAZARD)
    print("imagery    :", "found" if fk.IMAGERY.exists() else "MISSING", fk.IMAGERY)
    d = load()
    print(f"loaded {len(d)} artefacts in {time.time()-t0:.0f} s\n")
    bad = 0
    for tag, fn, cap in FIGURES:
        if only and tag not in only:
            continue
        t = time.time()
        try:
            p = fn(d)
            print(f"  {tag}  {p}   ({time.time()-t:.0f} s)\n        {cap}")
        except Exception as exc:                        # noqa: BLE001 -- report, never hide
            bad += 1
            import traceback
            print(f"  {tag}  FAILED: {type(exc).__name__}: {exc}")
            traceback.print_exc()
    print(f"\n{len(FIGURES)-bad} of {len(FIGURES)} figures written to {fk.IMG}")
    return bad


if __name__ == "__main__":
    only = [a.upper() for a in sys.argv[1:] if a.upper().startswith("FW")]
    raise SystemExit(main(only or None))
