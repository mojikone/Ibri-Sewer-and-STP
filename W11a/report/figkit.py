"""figkit — the shared figure toolkit for the W11a report.

Seven agents draw the W11a figures. This module is the only place where the map
furniture, the palette, the save path and the provenance line are decided, so the
figures read as one set and no two of them disagree about what a "trunk main" or a
"FAIL" looks like.

FOUR RULES THIS MODULE ENFORCES, because each one has already cost us something:

1.  **Reads are of a COPY.**  The stage scripts write `W11a/shp/*.gpkg` while the
    report is being drawn.  `snapshot()` copies to a scratchpad outside the repo,
    verifies the copy opens, and re-copies if the source moved under it.  Nothing
    here ever opens a live GeoPackage, and nothing here ever writes one.

2.  **Every number carries its artefact.**  `read_layer()` and `read_csv()` stamp
    the file, the feature count and the file's write time onto the object they
    return.  `source_line()` turns those stamps into the line that goes on the
    figure.  A figure with a number and no source line is not finished.

3.  **UNTESTED is drawn, never left blank.**  The 50-year hazard grid covers well
    under half the study area and its nodata is -9999.0, which IS finite -- so a
    `np.isfinite` guard passes it as "not a wadi".  `hazard_coverage()` handles
    that trap in one place, and `hatch_untested()` draws the answer-free ground as
    hatch.  Clear ground on a map means "tested and clean".

4.  **Colour is never the only channel.**  The tier ladder is a single-hue
    lightness ramp plus a line-width ramp, so it survives greyscale and every form
    of colour blindness.  The status roles pair colour with a hatch.  There is no
    red/green pair anywhere that is not also a light/dark pair.
    `python figkit.py --check-palette` proves the luminance separation.

WHAT THIS MODULE DOES NOT DO: it does not decide what a figure says.  It has no
project numbers in it.  Every figure caption, title and databox is built by the
agent drawing it, out of values it read from an artefact.

Run `python figkit.py` to rebuild the two worked examples in `W11a/report/img/`.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, MaxNLocator
import matplotlib.patheffects as pe

# --------------------------------------------------------------------- paths

HERE = Path(__file__).resolve().parent            # .../Claude/W11a/report
W11A = HERE.parent                                # .../Claude/W11a
ROOT = W11A.parent                                # .../Hydraulic/Claude   (git root)
HYD = ROOT.parent                                 # .../Hydraulic
BASE = HYD.parent                                 # .../2621 Ibri Sewer STP

SHP = W11A / "shp"
RUN = W11A / "run"
IMG = HERE / "img"

#: Everything read is copied here first.  Outside the repo, outside the project.
SCRATCH = Path(os.environ.get("W11A_FIGKIT_SCRATCH",
                              Path(tempfile.gettempdir()) / "w11a_figkit"))

#: Offline Esri mosaic, EPSG:3857.  Local only -- licensing forbids it in the repo.
IMAGERY = HYD / "Imagery" / "esri_z17_mosaic_3857.tif"

#: The 50-year flood-hazard grid.  EPSG:32640, 3 m, nodata -9999.0.
HAZARD = BASE / "Data" / "04 Lekhuwair" / "Hazard_T50y.tif"

#: Study-area boundary and the land-use display layer (project rule 4).
BOUNDARY = HYD / "SHP" / "MoHUP_DATA" / "Project_boundary.shp"
MOH_PLOTS = HYD / "SHP" / "MoHUP_DATA" / "MoH_Plots.shp"

EPSG = 32640
CRS = f"EPSG:{EPSG}"

DPI = 200


# --------------------------------------------------------------------- palette

class C:
    """Named colour roles.  Import the role, never the hex.

    The tier ladder is one hue at five separated lightnesses; paired with
    ``TIER_LW`` it is legible in greyscale and to every colour-vision type.
    The status roles pair colour with a hatch (``STATUS_HATCH``) so that pass /
    fail / untested never rest on red-versus-green.
    """

    # ink and furniture
    INK = "#1b1b1b"
    GREY = "#5a5a5a"
    FAINT = "#c9c9c9"
    PAPER = "#ffffff"
    GRID = "#e4e4e4"

    # network tiers -- light (small) to dark (big).  One hue, five separated
    # lightnesses: the ladder is ordinal, so a sequential ramp is the honest form.
    RIDER = "#add0e6"
    LATERAL = "#64a9d3"
    MAIN = "#2c7cba"
    SUBMAIN = "#08519c"
    TRUNK = "#08306b"

    # audit / test outcome.  Four separated lightnesses, each with its own hatch.
    PASS = "#a6d8be"
    FLAG = "#d9902f"
    UNTESTED = "#767676"
    FAIL = "#8c1d1f"

    # map features
    BOUNDARY = "#d35400"
    WADI = "#4a6f8a"
    DUAL = "#7b3f9d"
    STATION = "#8c1d1f"
    OUTFALL = "#8c1d1f"
    PLOT_FILL = "#e8e3d9"
    PLOT_EDGE = "#c8c0b2"


TIER_COLOR = {
    "rider": C.RIDER,
    "lateral": C.LATERAL,
    "main": C.MAIN,
    "sub main": C.SUBMAIN,
    "trunk main": C.TRUNK,
}
#: Width is the redundant channel for the tier ladder -- greyscale-proof.
TIER_LW = {
    "rider": 0.35,
    "lateral": 0.55,
    "main": 1.00,
    "sub main": 1.60,
    "trunk main": 2.60,
}
TIER_ORDER = ["rider", "lateral", "main", "sub main", "trunk main"]

STATUS_COLOR = {
    "pass": C.PASS,
    "flag": C.FLAG,
    "untested": C.UNTESTED,
    "fail": C.FAIL,
}
#: Hatch is the redundant channel for status.  UNTESTED is always "///".
STATUS_HATCH = {"pass": None, "flag": "..", "untested": "///", "fail": "\\\\"}
STATUS_ORDER = ["pass", "flag", "untested", "fail"]


def tier_style(tier: str) -> dict:
    """``ax.plot(**tier_style("sub main"))`` -- colour and width for one tier."""
    t = str(tier).strip().lower()
    return {"color": TIER_COLOR.get(t, C.GREY), "lw": TIER_LW.get(t, 0.8)}


def status_style(status: str, *, filled: bool = True) -> dict:
    """Colour + hatch for a pass / flag / untested / fail patch."""
    s = str(status).strip().lower()
    s = {"not_checkable": "untested", "cannot_run": "untested",
         "unknown": "untested", "flagged": "flag"}.get(s, s)
    col = STATUS_COLOR.get(s, C.GREY)
    return {"facecolor": col if filled else "none",
            "edgecolor": C.INK, "hatch": STATUS_HATCH.get(s), "linewidth": 0.6}


def _rel_luminance(hexcol: str) -> float:
    """WCAG relative luminance -- what a greyscale print keeps."""
    r, g, b = (int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def check_palette(min_ratio: float = 1.50) -> list[str]:
    """Prove the roles that share a figure stay apart in greyscale.

    Returns the report lines; raises AssertionError if any adjacent pair in a
    ladder falls below ``min_ratio`` of WCAG contrast.  This is the module's own
    self-test -- if someone edits a hex value, this is what catches it.
    """
    out = []
    for name, ladder in (("tier", [TIER_COLOR[t] for t in TIER_ORDER]),
                         ("status", [STATUS_COLOR[s] for s in STATUS_ORDER])):
        lum = [_rel_luminance(c) for c in ladder]
        out.append(f"{name}: " + "  ".join(f"{c} L={l:.3f}" for c, l in zip(ladder, lum)))
        for i in range(len(lum) - 1):
            hi, lo = max(lum[i], lum[i + 1]), min(lum[i], lum[i + 1])
            ratio = (hi + 0.05) / (lo + 0.05)
            out.append(f"   {ladder[i]} vs {ladder[i+1]}: greyscale contrast {ratio:.2f}")
            assert ratio >= min_ratio, (
                f"{name} ladder step {ladder[i]}->{ladder[i+1]} only {ratio:.2f}:1 "
                f"in greyscale (need {min_ratio})")
    return out


def use_style() -> None:
    """House rcParams.  Called at import; call again after any rcParams change."""
    plt.rcParams.update({
        "figure.facecolor": C.PAPER,
        "savefig.facecolor": C.PAPER,
        "axes.facecolor": C.PAPER,
        "font.size": 8.5,
        "axes.titlesize": 10,
        "axes.labelsize": 8.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5,
        "axes.edgecolor": "#b8b8b8",
        "axes.linewidth": 0.8,
        "hatch.linewidth": 0.7,
    })


use_style()


# ----------------------------------------------------------------- provenance

@dataclass(frozen=True)
class Src:
    """Where a number came from.  Attached to every object this module returns."""
    path: Path
    detail: str          # layer name, or "" for a flat file
    n: int               # features / rows
    written: str         # source file mtime, not the copy's

    def __str__(self) -> str:
        rel = self.path
        try:
            rel = self.path.relative_to(ROOT)
        except ValueError:
            try:
                rel = self.path.relative_to(BASE)
            except ValueError:
                pass
        bit = f" [{self.detail}]" if self.detail else ""
        return f"{rel.as_posix()}{bit}, {self.n:,} rows, written {self.written}"


def _stamp(p: Path) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))


def cite(obj) -> str:
    """The provenance string for anything ``read_layer`` / ``read_csv`` returned."""
    if isinstance(obj, str):
        return obj
    src = getattr(obj, "attrs", {}).get("fk_source")
    if src is None:
        raise ValueError("no provenance on this object -- read it with figkit, "
                         "or pass an explicit source string")
    return str(src)


def source_line(*items) -> str:
    """``source_line(corridors, "s4_tier_shares.csv")`` -> the figure's source line."""
    return "Source: " + "  ·  ".join(cite(i) for i in items)


# --------------------------------------------------------------------- loader

def snapshot(name: str, *, tries: int = 4) -> Path:
    """Copy ``W11a/shp/<name>`` (or any path) to the scratchpad and return the copy.

    The stage scripts are writing these files right now.  A copy is only accepted
    when the source's mtime and size are unchanged across the copy AND the result
    opens; otherwise it is taken again.  Re-uses an existing copy when the source
    has not moved, so ten reads cost one copy.
    """
    src = Path(name) if os.path.sep in str(name) or "/" in str(name) else SHP / name
    if not src.exists():
        raise FileNotFoundError(f"figkit.snapshot: {src} does not exist")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    dst = SCRATCH / src.name
    tag = SCRATCH / (src.name + ".src.json")
    # a shapefile is six files; copying only the .shp gives an unopenable copy
    family = (sorted(src.parent.glob(src.stem + ".*"))
              if src.suffix.lower() == ".shp" else [src])

    def sig(_p=None) -> dict:
        return {f.name: [f.stat().st_mtime_ns, f.stat().st_size] for f in family}

    if dst.exists() and tag.exists():
        try:
            if json.loads(tag.read_text()) == sig(src):
                return dst
        except Exception:
            pass

    last = None
    for attempt in range(tries):
        before = sig()
        tmps = []
        try:
            for f in family:                       # .shp brings .dbf .shx .prj ...
                t = SCRATCH / f"{f.name}.part{os.getpid()}"
                shutil.copy2(f, t)
                tmps.append((t, SCRATCH / f.name))
            if sig() != before:                    # a writer moved under us
                raise RuntimeError("source changed during copy")
            for t, final in tmps:
                os.replace(t, final)
            _verify(dst)
            tag.write_text(json.dumps(before))
            return dst
        except Exception as exc:                   # noqa: BLE001 -- retry, then report
            last = exc
            for t, _final in tmps:
                t.unlink(missing_ok=True)
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"figkit.snapshot: could not take a clean copy of {src.name} "
                       f"in {tries} tries -- a stage is still writing it. Last: {last}")


def _verify(p: Path) -> None:
    """Cheap proof the copy is readable, so a torn file fails here not mid-figure."""
    if p.suffix.lower() in (".gpkg", ".shp"):
        import pyogrio
        pyogrio.list_layers(str(p))


def layers(name: str) -> list[str]:
    """Layer names inside a GeoPackage (snapshotting it first)."""
    import pyogrio
    return [row[0] for row in pyogrio.list_layers(str(snapshot(name)))]


def read_layer(name: str, layer: str | None = None, *, columns=None, bbox=None,
               where: str | None = None):
    """Read one vector layer from a COPY, read-only, and stamp its provenance.

    ``fk.read_layer("W11a.gpkg", "corridors")`` -- the returned GeoDataFrame carries
    ``.attrs["fk_source"]``, which ``fk.cite()`` and ``fk.source_line()`` read.
    """
    import geopandas as gpd
    src = Path(name) if ("/" in str(name) or os.path.sep in str(name)) else SHP / name
    copy = snapshot(name)
    gdf = gpd.read_file(copy, layer=layer, columns=columns, bbox=bbox, where=where,
                        engine="pyogrio")
    if gdf.crs is not None and gdf.crs.to_epsg() != EPSG:
        raise ValueError(f"{src.name}[{layer}] is {gdf.crs.to_string()}, not {CRS}")
    gdf.attrs["fk_source"] = Src(src, layer or "", len(gdf), _stamp(src))
    return gdf


def read_csv(name: str, **kw):
    """Read a CSV from ``W11a/run/`` (or an explicit path) and stamp its provenance."""
    import pandas as pd
    src = Path(name) if ("/" in str(name) or os.path.sep in str(name)) else RUN / name
    df = pd.read_csv(src, **kw)
    df.attrs["fk_source"] = Src(src, "", len(df), _stamp(src))
    return df


# ------------------------------------------------------------------- extents

def extent_of(obj, pad: float = 0.03) -> tuple[float, float, float, float]:
    """(minx, miny, maxx, maxy) from a GeoDataFrame, geometry or 4-tuple, padded."""
    if hasattr(obj, "total_bounds"):
        x0, y0, x1, y1 = obj.total_bounds
    elif hasattr(obj, "bounds") and not isinstance(obj, (tuple, list)):
        x0, y0, x1, y1 = obj.bounds
    else:
        x0, y0, x1, y1 = obj
    dx, dy = (x1 - x0), (y1 - y0)
    return (x0 - dx * pad, y0 - dy * pad, x1 + dx * pad, y1 + dy * pad)


def study_boundary():
    """The project boundary polygon layer, EPSG:32640, with provenance."""
    return read_layer(str(BOUNDARY))


# ------------------------------------------------------------------- basemap

def basemap(ax, extent, *, alpha: float = 0.30, px: int = 1600) -> str:
    """Esri mosaic under the map at 30 % opacity (project rule 4).

    Returns a one-line note describing what was actually drawn.  Put that note on
    the figure: if no offline imagery is available the map says so rather than
    pretending the white ground is a cartographic choice.  Never fetches tiles.
    """
    x0, y0, x1, y1 = extent
    if not IMAGERY.exists():
        ax.set_facecolor("#f6f5f2")
        return ("no offline imagery available - neutral basemap "
                f"(expected {IMAGERY.name}; tiles are never fetched)")
    try:
        import rasterio
        from rasterio.vrt import WarpedVRT
        from rasterio.windows import Window, from_bounds
        from rasterio.windows import bounds as win_bounds
        with rasterio.open(IMAGERY) as src, WarpedVRT(src, crs=CRS) as vrt:
            # A WarpedVRT cannot read boundless, so clip to what the mosaic covers
            # and place the image at the CLIPPED bounds -- never stretched to fit.
            win = from_bounds(x0, y0, x1, y1, vrt.transform).intersection(
                Window(0, 0, vrt.width, vrt.height))
            if win.width < 2 or win.height < 2:
                raise ValueError("the offline mosaic does not cover this extent")
            bx0, by0, bx1, by1 = win_bounds(win, vrt.transform)
            h = max(1, int(px * (by1 - by0) / max(bx1 - bx0, 1e-9)))
            img = vrt.read([1, 2, 3], window=win, out_shape=(3, h, px))
        ax.set_facecolor("#f6f5f2")
        ax.imshow(np.transpose(img, (1, 2, 0)), extent=(bx0, bx1, by0, by1),
                  alpha=alpha, zorder=0, interpolation="bilinear")
        cov = 100.0 * ((bx1 - bx0) * (by1 - by0)) / max((x1 - x0) * (y1 - y0), 1e-9)
        tail = "" if cov > 99 else f", covering {cov:.0f} % of the frame"
        return (f"basemap: Esri World Imagery z17, offline mosaic, "
                f"{int(alpha * 100)} % opacity{tail}")
    except Exception as exc:                        # noqa: BLE001
        ax.set_facecolor("#f6f5f2")
        return f"no basemap drawn - neutral ground ({type(exc).__name__}: {exc})"


# ---------------------------------------------------------------- untested

def hazard_coverage(extent, *, px: int = 1400, wadi_classes=(4, 5, 6)):
    """Read the 50-year hazard grid over ``extent`` -> ``(known, wadi, extent)``.

    ``known`` is False where the grid has no answer.  The nodata is **-9999.0,
    which is finite**, so an ``np.isfinite`` guard alone reports it as dry ground;
    that trap is handled here, once, rather than in seven figures.  Arrays are
    decimated for display -- do not quote a percentage off them; sample the grid at
    full resolution for any number that goes in text.
    """
    import rasterio
    from rasterio.windows import from_bounds
    x0, y0, x1, y1 = extent
    with rasterio.open(HAZARD) as src:
        win = from_bounds(x0, y0, x1, y1, src.transform)
        h = max(1, int(px * (y1 - y0) / max(x1 - x0, 1e-9)))
        a = src.read(1, window=win, out_shape=(h, px), boundless=True,
                     fill_value=src.nodata if src.nodata is not None else -9999.0)
        nod = src.nodata
    a = np.asarray(a, dtype="float64")
    known = np.isfinite(a)
    if nod is not None:
        known &= (a != nod)
    known &= (a > -9998.0)                 # the finite-nodata trap, belt and braces
    wadi = known & (np.floor(a) >= min(wadi_classes))
    return known, wadi, (x0, x1, y0, y1)


def hatch_untested(ax, untested_mask, extent, *, color: str = C.UNTESTED,
                   hatch: str = "///", face_alpha: float = 0.16, zorder: int = 2):
    """Draw answer-free ground as hatch.  ``untested_mask`` True = no answer.

    Clear ground on a map reads as "tested and clean".  Where roughly half the
    study area has no hazard answer, leaving it clear is a lie, so it gets hatched
    and it gets a legend entry (:func:`untested_handle`).
    """
    m = np.asarray(untested_mask, dtype=bool)
    if not m.any():
        return None
    x0, x1, y0, y1 = extent
    ny, nx = m.shape
    xs = np.linspace(x0, x1, nx)
    ys = np.linspace(y1, y0, ny)                   # rows run north -> south
    rgba = np.zeros(m.shape + (4,))
    rgba[..., :3] = matplotlib.colors.to_rgb(color)
    rgba[..., 3] = np.where(m, face_alpha, 0.0)
    ax.imshow(rgba, extent=(x0, x1, y0, y1), zorder=zorder, interpolation="nearest")
    with plt.rc_context({"hatch.color": color, "hatch.linewidth": 0.7}):
        cs = ax.contourf(xs, ys, m.astype(float), levels=[0.5, 1.5],
                         colors="none", hatches=[hatch], zorder=zorder + 0.1)
    for setter in ("set_hatchcolor", "set_edgecolor"):
        try:
            getattr(cs, setter)(color)
            break
        except Exception:                           # noqa: BLE001 -- mpl version drift
            continue
    return cs


def untested_handle(label: str = "UNTESTED — no hazard-grid answer") -> Patch:
    """Legend swatch matching :func:`hatch_untested`."""
    return Patch(facecolor=C.UNTESTED, alpha=0.30, edgecolor=C.UNTESTED,
                 hatch="///", label=label)


# ------------------------------------------------------------------ map frame

def map_frame(extent, *, title: str, subtitle: str | None = None,
              figsize=None, basemap_alpha: float = 0.30, aspect_target: float = 1.0):
    """Open a map figure on ``extent``, EPSG:32640, basemap already drawn.

    Returns ``(fig, ax, note)`` -- ``note`` is the basemap note, which belongs on
    the figure.  Draw your layers, then call :func:`finish_map`.
    """
    x0, y0, x1, y1 = extent_of(extent, pad=0.0)
    if figsize is None:
        ar = (y1 - y0) / max(x1 - x0, 1e-9)
        w = 11.0
        figsize = (w, max(4.0, min(15.0, w * ar * aspect_target + 1.6)))
    fig, ax = plt.subplots(figsize=figsize)
    top = _titleblock(fig, title, subtitle)
    fig.subplots_adjust(left=0.065, right=0.985,
                        bottom=0.055 + 0.42 / figsize[1], top=top)
    note = basemap(ax, (x0, y0, x1, y1), alpha=basemap_alpha)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal", adjustable="box")
    ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.yaxis.set_major_locator(MaxNLocator(5))
    fmt = FuncFormatter(lambda v, _: f"{v:,.0f}")
    ax.xaxis.set_major_formatter(fmt)
    ax.yaxis.set_major_formatter(fmt)
    ax.tick_params(colors=C.GREY, length=3, width=0.8)
    ax.set_xlabel(f"Easting (m, {CRS})", color=C.GREY)
    ax.set_ylabel(f"Northing (m, {CRS})", color=C.GREY)
    return fig, ax, note


def finish_map(fig, ax, *, source: str, note: str | None = None,
               legend_handles=None, legend_loc: str = "upper left",
               databox: str | None = None, inset: bool = True,
               north: bool = True, scalebar: bool = True) -> None:
    """Add the furniture: north arrow, scale bar, legend, databox, inset, source."""
    if scalebar:
        _scalebar(ax)
    if north:
        _north(ax)
    if legend_handles:
        leg = ax.legend(handles=legend_handles, loc=legend_loc, framealpha=0.92,
                        edgecolor="#9a9a9a", borderpad=0.6, labelspacing=0.55)
        leg.set_zorder(12)
    if databox:
        ax.text(0.985, 0.018, databox, transform=ax.transAxes, fontsize=7.2,
                va="bottom", ha="right", zorder=12, family="monospace", color=C.INK,
                bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a",
                          alpha=0.93))
    if inset:
        _inset(ax)
    _sourceline(fig, source, note)


def _titleblock(fig, title: str, subtitle: str | None) -> float:
    """Title and subtitle placed in INCHES, so they never collide on a short figure.

    Returns the figure-fraction y below which the axes must sit.
    """
    import textwrap
    w_in, h_in = fig.get_size_inches()
    y = 1.0 - 0.26 / h_in
    fig.text(0.012, y, title, ha="left", va="top", fontsize=12.5,
             fontweight="bold", color=C.INK)
    y -= 0.30 / h_in
    if subtitle:
        lines = textwrap.wrap(subtitle, width=max(40, int(w_in * 14.5)))
        fig.text(0.012, y, "\n".join(lines), ha="left", va="top", fontsize=8.6,
                 color=C.GREY, linespacing=1.35)
        y -= (0.17 * len(lines) + 0.08) / h_in
    return max(0.30, y)


def _sourceline(fig, source: str, note: str | None) -> None:
    txt = source if not note else f"{source}\n{note}"
    fig.text(0.012, 0.006, txt, ha="left", va="bottom", fontsize=6.8, color=C.GREY)


_NICE = [50, 100, 200, 250, 500, 1000, 2000, 2500, 5000,
         10000, 20000, 25000, 50000, 100000]


def _scalebar(ax, frac: float = 0.22) -> None:
    """Two-tone bar with 0 / half / full labels, mid label dropped if it would crowd."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    target = (x1 - x0) * frac
    L = max(n for n in _NICE if n <= target) if target >= _NICE[0] else _NICE[0]

    bx = x0 + (x1 - x0) * 0.035
    by = y0 + (y1 - y0) * 0.045
    h = (y1 - y0) * 0.008
    for i, col in enumerate((C.INK, "white")):
        ax.add_patch(Rectangle((bx + i * L / 2, by), L / 2, h, facecolor=col,
                               edgecolor=C.INK, lw=0.8, zorder=11))

    # non-overlap guard: how wide is half the bar on the page, in points?
    p0 = ax.transData.transform((bx, by))
    p1 = ax.transData.transform((bx + L / 2, by))
    half_pts = abs(p1[0] - p0[0]) * 72.0 / ax.figure.dpi
    ticks = [0, L / 2, L] if half_pts >= 26 else [0, L]

    unit, div = ("km", 1000.0) if L >= 1000 else ("m", 1.0)
    for t in ticks:
        lab = f"{t/div:g}"
        ax.text(bx + t, by + h * 1.5, lab, ha="center", va="bottom", fontsize=6.8,
                color=C.INK, zorder=11,
                path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])
    ax.text(bx + L, by - h * 0.9, f" {unit}", ha="left", va="top", fontsize=6.8,
            color=C.INK, zorder=11,
            path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])


def _north(ax, x: float = 0.962, y: float = 0.885) -> None:
    ax.annotate("", xy=(x, y + 0.055), xytext=(x, y), xycoords="axes fraction",
                textcoords="axes fraction", zorder=11,
                arrowprops=dict(arrowstyle="-|>", color=C.INK, lw=1.5,
                                shrinkA=0, shrinkB=0))
    ax.text(x, y + 0.065, "N", transform=ax.transAxes, ha="center", va="bottom",
            fontsize=9, fontweight="bold", color=C.INK, zorder=11,
            path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])


_BOUND_CACHE = {}


def _inset(ax, loc=(0.012, 0.70, 0.16, 0.24)) -> None:
    """Locator: the study boundary with a box round the mapped extent."""
    try:
        if "b" not in _BOUND_CACHE:
            _BOUND_CACHE["b"] = study_boundary()
        b = _BOUND_CACHE["b"]
    except Exception:                               # noqa: BLE001
        return
    iax = ax.inset_axes(loc)
    b.boundary.plot(ax=iax, color=C.GREY, lw=0.7)
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    iax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="none",
                            edgecolor=C.BOUNDARY, lw=1.2))
    bx0, by0, bx1, by1 = b.total_bounds
    iax.set_xlim(min(bx0, x0), max(bx1, x1))
    iax.set_ylim(min(by0, y0), max(by1, y1))
    iax.set_aspect("equal")
    iax.set_xticks([]); iax.set_yticks([])
    for s in iax.spines.values():
        s.set_color("#9a9a9a"); s.set_linewidth(0.7)
    iax.patch.set_alpha(0.88)
    iax.set_title("study area", fontsize=6.2, color=C.GREY, pad=2)


# ---------------------------------------------------------------- chart frame

def chart_frame(*, title: str, subtitle: str | None = None, figsize=(8.6, 4.6),
                nrows: int = 1, ncols: int = 1, ygrid: bool = True,
                xgrid: bool = False):
    """Open a chart figure with the same title / source discipline as a map."""
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    top = _titleblock(fig, title, subtitle)
    fig.subplots_adjust(left=0.10, right=0.975,
                        bottom=0.10 + 0.42 / figsize[1], top=top)
    for a in (axes.ravel() if hasattr(axes, "ravel") else [axes]):
        style_axes(a, xgrid=xgrid, ygrid=ygrid)
    return fig, axes


def finish_chart(fig, *, source: str, note: str | None = None) -> None:
    """The source line.  Same rule as a map: no source line, not finished."""
    _sourceline(fig, source, note)


def style_axes(ax, *, xgrid: bool = False, ygrid: bool = True) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#b8b8b8")
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=C.GREY, length=3, width=0.8)
    for axis, on in ((ax.yaxis, ygrid), (ax.xaxis, xgrid)):
        axis.grid(on, **({"color": C.GRID, "linewidth": 0.8} if on else {}))
    ax.set_axisbelow(True)


def thousands(ax, axis: str = "y") -> None:
    getattr(ax, f"{axis}axis").set_major_formatter(
        FuncFormatter(lambda v, _: f"{v:,.0f}"))


def tier_legend(labels: dict | None = None) -> list[Line2D]:
    """Legend handles for the tier ladder, in order, thin to thick."""
    labels = labels or {t: t for t in TIER_ORDER}
    return [Line2D([], [], label=labels[t], **tier_style(t))
            for t in TIER_ORDER if t in labels]


def status_legend(labels: dict | None = None) -> list[Patch]:
    labels = labels or {s: s.upper() for s in STATUS_ORDER}
    return [Patch(label=labels[s], **status_style(s))
            for s in STATUS_ORDER if s in labels]


# ---------------------------------------------------------------------- save

def save(fig, stem: str, *, dpi: int = DPI, close: bool = True) -> Path:
    """Write ``W11a/report/img/<stem>.png`` at 200 dpi and return the path."""
    IMG.mkdir(parents=True, exist_ok=True)
    path = IMG / f"{stem}.png"
    fig.savefig(path, dpi=dpi, facecolor=C.PAPER, bbox_inches="tight", pad_inches=0.16)
    if close:
        plt.close(fig)
    return path


# ------------------------------------------------------------------- examples

def _demo_map() -> Path:
    """Worked example: corridors against hazard-grid coverage."""
    cor = read_layer("W11a.gpkg", "corridors",
                     columns=["CORR_ID", "LEN_M", "ON_WADI_M", "SRC"])
    ext = extent_of(cor, pad=0.02)
    known, _wadi, rext = hazard_coverage(ext)
    untested = ~known

    # the quoted number is sampled at FULL resolution, not off the display array
    import rasterio
    pts = [(g.interpolate(0.5, normalized=True).x, g.interpolate(0.5, normalized=True).y)
           for g in cor.geometry]
    with rasterio.open(HAZARD) as src:
        vals = np.array([v[0] for v in src.sample(pts)], dtype="float64")
        nod = src.nodata
    no_answer = ~np.isfinite(vals) | (vals == nod) | (vals <= -9998.0)
    pct = 100.0 * no_answer.mean()

    onwadi = cor[cor["ON_WADI_M"].fillna(0) > 0]
    fig, ax, note = map_frame(
        ext,
        title=f"{pct:.0f} % of the corridor network has no flood answer at all",
        subtitle=("Every corridor midpoint sampled against the 50-year hazard grid. "
                  "Hatched ground is outside the grid, where the wadi rule cannot be "
                  "tested — not ground that has been tested and found clear."))
    hatch_untested(ax, untested, rext)
    cor.plot(ax=ax, color=C.LATERAL, linewidth=0.30, zorder=4)
    if len(onwadi):
        onwadi.plot(ax=ax, color=C.FAIL, linewidth=0.9, zorder=5)
    try:
        study_boundary().boundary.plot(ax=ax, color=C.BOUNDARY, lw=1.2, ls="--",
                                       zorder=6)
    except Exception:                               # noqa: BLE001
        pass

    handles = [
        Line2D([], [], color=C.LATERAL, lw=1.2, label=f"corridor ({len(cor):,})"),
        Line2D([], [], color=C.FAIL, lw=1.6,
               label=f"corridor touching wadi ground ({len(onwadi):,})"),
        Line2D([], [], color=C.BOUNDARY, lw=1.2, ls="--", label="study boundary"),
        untested_handle("UNTESTED — outside the 50-year grid"),
    ]
    box = (f"corridors     {len(cor):>10,}\n"
           f"length        {cor['LEN_M'].sum()/1000:>9,.1f} km\n"
           f"wadi contact  {onwadi['ON_WADI_M'].sum()/1000:>9,.1f} km\n"
           f"no grid answer{pct:>9.1f} % of midpoints")
    finish_map(fig, ax, legend_handles=handles, databox=box, note=note,
               source=source_line(cor, f"{HAZARD.relative_to(BASE).as_posix()}, "
                                       f"50-year hazard grid, nodata -9999.0"))
    return save(fig, "FK_example_map_hazard_coverage")


def _demo_chart() -> Path:
    """Worked example: audit outcomes, three artefacts, pass / fail / untested."""
    w10 = read_csv("audit_W10.csv")
    trunk = read_csv("audit_W11a_trunk.csv")
    ready = read_csv("s4_audit_readiness.csv")

    def split(df):
        s = df["status"].str.upper()
        return {"pass": int((s == "PASS").sum()),
                "fail": int((s == "FAIL").sum()),
                "untested": int((~s.isin(["PASS", "FAIL"])).sum())}

    rows = [
        (f"W11a trunk\n({len(trunk)} checks)", split(trunk)),
        (f"W10 published\n({len(w10)} checks)", split(w10)),
        (f"W11a network,\nstage 4 ({len(ready)} checks)",
         {"pass": 0, "fail": 0, "untested": int((~ready["can_run"].astype(bool)).sum())}),
    ]
    # stage 4 publishes readiness only, so its 2 runnable checks are not an outcome
    rows[2][1]["flag"] = int(ready["can_run"].astype(bool).sum())

    fig, ax = chart_frame(
        title=("The trunk passes 17 of 22 checks; W10's published network passes 3"
               if split(trunk)["pass"] == 17 and split(w10)["pass"] == 3 else
               "Audit outcomes differ sharply between the trunk and W10"),
        subtitle=("A check that cannot run counts as a failure, not a blank. On the "
                  "full W11a network at stage 4 the fields most checks need are not "
                  "published yet, so almost nothing can be tested."),
        figsize=(9.0, 3.6), ygrid=False, xgrid=True)

    order = ["pass", "flag", "untested", "fail"]
    names = {"pass": "PASS", "flag": "runs, outcome not published",
             "untested": "cannot run — counted as failure", "fail": "FAIL"}
    ypos = np.arange(len(rows))[::-1]
    for y, (_lab, d) in zip(ypos, rows):
        left = 0.0
        for k in order:
            v = d.get(k, 0)
            if not v:
                continue
            ax.barh(y, v, left=left, height=0.55, **status_style(k))
            ax.text(left + v / 2, y, str(v), ha="center", va="center", fontsize=7.5,
                    color=C.INK if k in ("pass", "flag", "untested") else "white",
                    fontweight="bold")
            left += v
    ax.set_yticks(ypos)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.6)
    ax.set_xlabel("checks in the 22-check registry")
    ax.set_xlim(0, 22.6)
    ax.legend(handles=[Patch(label=names[k], **status_style(k)) for k in order],
              loc="lower right", ncol=2, framealpha=0.95, edgecolor="#9a9a9a")
    finish_chart(fig, source=source_line(trunk, w10, ready))
    return save(fig, "FK_example_chart_audit_outcomes")


def _demo() -> None:
    for line in check_palette():
        print("  " + line)
    print("\nscratchpad:", SCRATCH)
    print("imagery   :", "found" if IMAGERY.exists() else "MISSING", IMAGERY)
    print("hazard    :", "found" if HAZARD.exists() else "MISSING", HAZARD)
    print("\n  map   ->", _demo_map())
    print("  chart ->", _demo_chart())


if __name__ == "__main__":
    import sys
    if "--check-palette" in sys.argv:
        for line in check_palette():
            print(line)
    else:
        _demo()
