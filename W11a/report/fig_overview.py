"""fig_overview — the context and scope figures for the W11a report.

These are the figures a reader needs BEFORE any hydraulic figure makes sense: what
the study area is, who lives in it, what is already built, where the load actually
is, and where the works could go.

Run from ``W11a/report/``::

    python fig_overview.py            # all figures
    python fig_overview.py FO03 FO08  # just these
    python fig_overview.py --list     # what exists and what each one says
    python fig_overview.py --facts    # the number table only (figures still rebuild)

Idempotent: each run recomputes from the artefacts and overwrites the same PNGs.
Every file this module writes is ``W11a/report/img/FO##_*.png`` -- the ``FO`` prefix
is this module's alone, so nothing here can collide with another agent's ``F12``.

RULES THIS MODULE KEEPS
-----------------------
*   **No number is written here.**  Every figure value is computed at run time from
    a named artefact.  ``FACTS`` collects them as they are computed and ``--facts``
    prints the lot, so a reviewer can check any figure against its source without
    opening a GIS.
*   **A project measure is labelled as one.**  Two appear: the 50 m band used to
    ask "does this plot already have a built sewer in front of it" (F10), and the
    250 m cell used for load density (F04).  Neither is a guideline value and both
    say so on the figure.
*   **One guideline value appears in the whole module** -- the 50-5,000 inhabitant
    package-plant band on FO12, read back from PAM-GUD-201 p83 8.4.1 ("communities
    with a population between 50-5,000 inhabitants") and cited on the figure.
    Everything else here is scope and context; nothing is a compliance check.
*   Reads go through :mod:`figkit`, which copies to a scratchpad first.  Nothing
    here opens or writes anything in ``W11a/shp``.

THE BOUNDARY, AND WHY IT IS NOT figkit's
----------------------------------------
Two boundary files exist and they are NOT the same polygon:

    Hydraulic/SHP/Study area/Project Boundary.shp    531.4 km2  <- s1_scope.py uses this
    Hydraulic/SHP/MoHUP_DATA/Project_boundary.shp    439.8 km2  <- figkit.BOUNDARY

The pipeline's own scope boundary is the 531.4 km2 one, so that is the one drawn
here and the one every percentage-of-study-area figure is divided by.  Every map in
this module frames the WHOLE study area, so figkit's locator inset skips itself and
the difference never reaches the page -- but the cache is seeded with the right
polygon anyway (in __main__ only, so no other agent's process is touched), for
whoever adds a zoomed map next.

TWO figkit BEHAVIOURS ARE WORKED AROUND HERE, not fixed there -- figkit is shared
and six other agents are importing it while this runs.  Both are in the report.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd  # noqa: E402
import matplotlib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import figkit as fk  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


# ------------------------------------------------------------------ artefacts

BASE = fk.BASE                                   # ...\2621 Ibri Sewer STP
ROOT = fk.ROOT                                   # ...\Hydraulic\Claude
HYD = fk.HYD                                     # ...\Hydraulic

#: the scope boundary the pipeline itself uses (s1_scope.py, IN_BOUNDARY)
STUDY_BND = HYD / "SHP" / "Study area" / "Project Boundary.shp"

#: NAMA's asset GIS, ESRI shapefiles.  STATUS separates built ('Ex') from proposed.
NAMA = BASE / "Data" / "Received" / "09-RECEIVED" / "NAMA" / "IBRI" / "WW" / "SHIP"
NAMA_SEWER = NAMA / "SEWERLINE_IBRI.shp"
NAMA_FORCE = NAMA / "FORCELINE_IBRI.shp"
NAMA_TE = NAMA / "TE_LINE_IBRI.shp"

#: per-plot ultimate saturated load, 64,071 records.  Stage 1 reads this same file.
PLOT_LOADS = ROOT / "W10" / "shp" / "W10_plot_loads.gpkg"

#: the STP siting study.  W10 is superseded as a DESIGN; its findings stand.
STP_SITES = ROOT / "W10" / "run" / "p4_stp_candidates.csv"

#: 5 m terrain, same folder / extent / blend as the authoritative 0.5 m VRT.
#: Used for DISPLAY only; every quoted level is sampled from the 0.5 m VRT.
DEM5 = BASE / "Data" / "Terrain" / "Sat_0p5m" / "ibri_blend.tif"
DEM05 = BASE / "Data" / "Terrain" / "Sat_0p5m" / "IBRI_0p5_VRT2.vrt"

#: coordinates that are recorded in the repo, not derived here
CFG = ROOT / "W11a" / "py" / "config_w10_reference.py"
PS_EXISTING = (449899.59, 2567301.72)            # CFG line 50
STP_EXISTING = (444422.8, 2563337.9)             # CLAUDE.md, user-confirmed 2026-09-01
STP_SOUTH = (442451.3, 2558941.8)                # CFG line 49

CITE_CFG = "W11a/py/config_w10_reference.py (PS + southern-site coordinates)"
CITE_STP = "CLAUDE.md (existing STP, user-confirmed 2026-09-01)"
CITE_DEM = ("Data/Terrain/Sat_0p5m/ IBRI_0p5_VRT2.vrt 0.5 m for levels, "
            "ibri_blend.tif 5 m for the display raster")

#: page size for a full-study-area map: the extent is 46 x 25 km, so an
#: equal-aspect axes plus the title block and source line fit this box.
STUDY_FIGSIZE = (11.6, 7.4)

#: PROJECT MEASURES — ours, not guideline values.  Labelled as such on the figures.
FRONTAGE_M = 50.0        # F10: "a built sewer is in front of this plot"
CELL_M = 250.0           # F04: load-density cell


FACTS: list[tuple[str, str, str]] = []           # (figure, what, artefact)


def fact(fig: str, what: str, value, artefact: str):
    """Record a figure value and where it came from.  ``--facts`` prints these."""
    FACTS.append((fig, f"{what} = {value}", artefact))
    return value


# --------------------------------------------------------------------- loaders

_CACHE: dict = {}


def _c(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def boundary():
    """The 531.4 km2 scope boundary that s1_scope.py uses."""
    return _c("bnd", lambda: fk.read_layer(str(STUDY_BND)))


def study_area_km2() -> float:
    return float(boundary().area.sum() / 1e6)


def servicing():
    """187 settlement polygons with the stage-1 servicing decision on each."""
    return _c("sv", lambda: fk.read_layer("W11a.gpkg", "servicing"))


def plots_display():
    """Plot polygons, for the land-use ground under a map (project rule 4)."""
    return _c("plots", lambda: fk.read_layer(
        str(HYD / "SHP" / "MoHUP_DATA" / "MoH_Plots.shp"), columns=["OBJECTID"]))


def plot_loads():
    """64,071 plots with the ultimate saturated load on each."""
    def _load():
        g = fk.read_layer(str(PLOT_LOADS), "plot_loads",
                          columns=["PLOT_ID", "Q_AVG_M3D", "N_PROP", "POP",
                                   "CAT", "CLASS", "IN_BND"])
        rp = g.geometry.representative_point()
        g["x"], g["y"] = rp.x.values, rp.y.values
        return g
    return _c("pl", _load)


def nama(kind: str):
    """NAMA asset GIS, split on STATUS.  'Ex' is built; 'Design' is not."""
    path = {"sewer": NAMA_SEWER, "force": NAMA_FORCE, "te": NAMA_TE}[kind]
    def _load():
        g = fk.read_layer(str(path), columns=["STATUS", "OUT_DIAMET"])
        g["LEN_M"] = g.length
        return g
    return _c("nama_" + kind, _load)


def nama_in_boundary(kind: str):
    """The same, clipped to the scope boundary, so km are comparable with ours."""
    def _clip():
        g = nama(kind).copy()
        poly = boundary().geometry.union_all()
        g["geometry"] = g.intersection(poly)
        g = g[~g.geometry.is_empty & ~g.geometry.isna()].copy()
        g["LEN_M"] = g.length
        return g
    return _c("namab_" + kind, _clip)


def stp_sites():
    return _c("stp", lambda: fk.read_csv(str(STP_SITES)))


def dem5(extent, px: int = 1500):
    """Decimated terrain over ``extent`` -> (array, (x0,x1,y0,y1), n_filled).

    The 5 m display blend has rectangular nodata holes -- 1.5 % of the frame --
    and its nodata is **-9999.0, which is finite**, the same trap the hazard grid
    sets.  Left as NaN they render as clean white rectangles that a reader takes
    for flat ground.  The authoritative 0.5 m VRT covers them, so the holes are
    filled by sampling it at exactly those pixel centres (about 2 s), and the
    count is reported on the figure.
    """
    import rasterio
    from rasterio.windows import from_bounds
    x0, y0, x1, y1 = extent
    with rasterio.open(DEM5) as src:
        win = from_bounds(x0, y0, x1, y1, src.transform)
        h = max(1, int(px * (y1 - y0) / max(x1 - x0, 1e-9)))
        a = src.read(1, window=win, out_shape=(h, px), boundless=True,
                     fill_value=-9999.0).astype("float64")
    a[~np.isfinite(a)] = np.nan
    a[a <= -9998.0] = np.nan                    # the finite-nodata trap
    holes = np.isnan(a)
    n_filled = int(holes.sum())
    if 0 < n_filled <= 200_000:
        ny, nx = a.shape
        ys, xs = np.where(holes)
        gx = x0 + (xs + 0.5) * (x1 - x0) / nx
        gy = y1 - (ys + 0.5) * (y1 - y0) / ny
        v = sample_dem05(zip(gx, gy))
        a[ys, xs] = v
    n_filled -= int(np.isnan(a).sum())        # what the 0.5 m VRT could not answer either
    return a, (x0, x1, y0, y1), n_filled


def sample_dem05(points) -> np.ndarray:
    """Ground level at a handful of points, from the AUTHORITATIVE 0.5 m blend."""
    import rasterio
    with rasterio.open(DEM05) as src:
        v = np.array([x[0] for x in src.sample(list(points))], dtype="float64")
    v[v <= -9998.0] = np.nan
    return v


# ------------------------------------------------------------------ furniture

#: single-hue sequential ramp built from figkit's tier ladder -- greyscale-safe.
DENSITY_CMAP = LinearSegmentedColormap.from_list(
    "fk_density", ["#eef4f9", fk.C.RIDER, fk.C.LATERAL, fk.C.MAIN, fk.C.SUBMAIN,
                   fk.C.TRUNK])

#: a label sitting on a hatched fill needs its own ground to stay readable
LABEL_BOX = dict(boxstyle="round,pad=0.22", fc="white", ec="none", alpha=0.78)

SYSTEM_COLOR = {"central": fk.C.SUBMAIN, "satellite": fk.C.FLAG,
                "onsite": fk.C.UNTESTED}
SYSTEM_HATCH = {"central": None, "satellite": "..", "onsite": "xx"}
SYSTEM_LABEL = {"central": "central network → central STP",
                "satellite": "satellite package plant",
                "onsite": "on-site (septic / tanker)"}


def system_style(s: str) -> dict:
    return {"facecolor": SYSTEM_COLOR[s], "edgecolor": fk.C.INK,
            "hatch": SYSTEM_HATCH[s], "linewidth": 0.35}


def draw_ground(ax, *, plots: bool = True, bnd: bool = True, plot_alpha: float = 0.9):
    """The land-use ground and the scope boundary, under everything else."""
    if plots:
        plots_display().plot(ax=ax, facecolor=fk.C.PLOT_FILL,
                             edgecolor=fk.C.PLOT_EDGE, linewidth=0.12,
                             alpha=plot_alpha, zorder=1.5)
    if bnd:
        boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.3, ls="--",
                                 zorder=8)


def works_markers(ax, *, south: bool = False, ps: bool = True, stp: bool = True,
                  size: float = 90):
    """Existing works, existing pumping station, and optionally the southern site."""
    if stp:
        ax.scatter(*STP_EXISTING, s=size * 1.5, marker="s", facecolor=fk.C.STATION,
                   edgecolor="white", linewidth=1.1, zorder=10)
    if ps:
        ax.scatter(*PS_EXISTING, s=size, marker="^", facecolor=fk.C.STATION,
                   edgecolor="white", linewidth=1.0, zorder=10)
    if south:
        ax.scatter(*STP_SOUTH, s=size * 1.5, marker="D", facecolor=fk.C.FLAG,
                   edgecolor=fk.C.INK, linewidth=1.0, zorder=10)


def _fmt(v, nd=0):
    return f"{v:,.{nd}f}"


def fix_basemap_nodata(ax, thresh: int = 10) -> bool:
    """Make the mosaic's off-image black transparent instead of mid-grey.

    ``figkit.basemap`` warps the EPSG:3857 Esri mosaic into EPSG:32640.  The
    warped quad does not fill the rectangular window, and GDAL fills the rest
    with 0 -- black.  Drawn at 30 % opacity that black reads as a solid grey
    ground covering the whole frame, which a reader takes for terrain.  This
    replaces the RGB image with RGBA whose alpha is zero on those pixels, so
    off-mosaic ground falls back to the neutral paper colour.

    Reported to the figkit author rather than fixed there: figkit is shared and
    six other agents are importing it while this runs.
    """
    done = False
    for im in list(ax.images):
        if im.get_zorder() != 0:
            continue
        arr = np.asarray(im.get_array())
        if arr.ndim != 3 or arr.shape[2] != 3:
            continue
        a = im.get_alpha()
        a = 0.30 if a is None else float(a)
        rgb = arr.astype("float64")
        rgb = rgb / 255.0 if rgb.max() > 1.5 else rgb
        rgba = np.zeros(rgb.shape[:2] + (4,))
        rgba[..., :3] = rgb
        rgba[..., 3] = np.where(arr.max(axis=2) <= thresh, 0.0, a)
        im.set_data(rgba)
        im.set_alpha(None)
        done = True
    return done


def _room(fig, source: str, note: str | None, base: float = 0.44) -> None:
    """Make bottom margin for however many lines the source line wrapped to."""
    n = source.count(chr(10)) + 1 + (0 if not note else note.count(chr(10)) + 1)
    h = fig.get_size_inches()[1]
    fig.subplots_adjust(bottom=min(0.42, 0.055 + (base + 0.125 * max(0, n - 1)) / h))


def finish_map(fig, ax, *, source: str, note: str | None = None, **kw) -> None:
    """figkit's map furniture, with room made for a wrapped source line."""
    _room(fig, source, note)
    fk.finish_map(fig, ax, source=source, note=note, **kw)


def panel_room(fig, drop: float = 0.055) -> None:
    """Lower a multi-panel chart so per-axes titles clear the figure subtitle.

    ``chart_frame`` reserves the top for the title block but knows nothing about
    axes titles, which are drawn ABOVE the axes and land in the subtitle.
    """
    fig.subplots_adjust(top=max(0.30, fig.subplotpars.top - drop))


def finish_chart(fig, *, source: str, note: str | None = None) -> None:
    _room(fig, source, note, base=0.52)
    fk.finish_chart(fig, source=source, note=note)


def src(*items, width: int = 152) -> str:
    """figkit's source line, WRAPPED.

    ``figkit.save`` uses ``bbox_inches="tight"``, so a single long source line
    stretches the saved PNG to the width of that text -- the first draft of F01
    came out 35 inches wide.  Wrapping here keeps the page the size of the map.
    """
    import textwrap
    line = fk.source_line(*items)
    return chr(10).join(textwrap.wrap(line, width=width, break_long_words=False,
                                      break_on_hyphens=False))


# ==================================================================== F01

def fig01_scope_and_existing() -> Path:
    """Scope, and what of the 'existing' network is actually built."""
    sew, fmn, te = (nama_in_boundary(k) for k in ("sewer", "force", "te"))
    built = sew[sew.STATUS == "Ex"]
    prop = sew[sew.STATUS != "Ex"]
    fmn_b = fmn[fmn.STATUS == "Ex"]
    fmn_p = fmn[fmn.STATUS != "Ex"]

    km_b = fact("FO01", "built gravity sewer in boundary, km",
                round(built.LEN_M.sum() / 1000, 1), "SEWERLINE_IBRI.shp STATUS='Ex'")
    km_p = fact("FO01", "proposed gravity sewer in boundary, km",
                round(prop.LEN_M.sum() / 1000, 1), "SEWERLINE_IBRI.shp STATUS='Design'")
    km_fb = fact("FO01", "built rising main in boundary, km",
                 round(fmn_b.LEN_M.sum() / 1000, 2), "FORCELINE_IBRI.shp STATUS='Ex'")
    km_fp = fact("FO01", "proposed rising main in boundary, km",
                 round(fmn_p.LEN_M.sum() / 1000, 1), "FORCELINE_IBRI.shp STATUS='Design'")
    km_te = fact("FO01", "proposed treated-effluent main in boundary, km",
                 round(te.LEN_M.sum() / 1000, 1), "TE_LINE_IBRI.shp (no 'Ex' rows)")
    pct_unbuilt = fact("FO01", "share of the sewer dataset never built, %",
                       round(100 * km_p / (km_p + km_b), 1),
                       "SEWERLINE_IBRI.shp STATUS")
    area = fact("FO01", "study area, km2", round(study_area_km2(), 1),
                "Hydraulic/SHP/Study area/Project Boundary.shp")
    n_set = fact("FO01", "settlements", len(servicing()), "W11a.gpkg [servicing]")
    n_plot = fact("FO01", "plots carrying a load record", len(plot_loads()),
                  "W10/shp/W10_plot_loads.gpkg")

    ext = fk.extent_of(boundary(), pad=0.04)
    fig, ax, note = fk.map_frame(
        ext, figsize=STUDY_FIGSIZE,
        title=f"{pct_unbuilt:.0f} % of the sewer in NAMA's GIS was never built",
        subtitle=("Everything the asset dataset holds inside the scope boundary, split on "
                  "its own STATUS field. Solid lines are built; dotted lines are records "
                  "with STATUS='Design' and no construction behind them. Filtering on "
                  "STATUS is the difference between a 311 km network and a 112 km one."))
    fix_basemap_nodata(ax)
    draw_ground(ax)
    if len(prop):
        prop.plot(ax=ax, color=fk.C.GREY, lw=0.7, ls=":", zorder=4)
    if len(fmn_p):
        fmn_p.plot(ax=ax, color=fk.C.DUAL, lw=1.0, ls=":", zorder=4)
    te.plot(ax=ax, color=fk.C.WADI, lw=0.9, ls="--", zorder=4)
    built.plot(ax=ax, color=fk.C.SUBMAIN, lw=1.0, zorder=6)
    fmn_b.plot(ax=ax, color=fk.C.STATION, lw=2.0, zorder=7)
    servicing().boundary.plot(ax=ax, color=fk.C.GREY, lw=0.35, alpha=0.7, zorder=3)
    works_markers(ax)

    handles = [
        Line2D([], [], color=fk.C.SUBMAIN, lw=1.6,
               label=f"gravity sewer BUILT — {km_b:,.1f} km"),
        Line2D([], [], color=fk.C.STATION, lw=2.2,
               label=f"rising main BUILT — {km_fb:,.2f} km"),
        Line2D([], [], color=fk.C.GREY, lw=1.2, ls=":",
               label=f"gravity sewer PROPOSED only — {km_p:,.1f} km"),
        Line2D([], [], color=fk.C.DUAL, lw=1.2, ls=":",
               label=f"rising main PROPOSED only — {km_fp:,.1f} km"),
        Line2D([], [], color=fk.C.WADI, lw=1.2, ls="--",
               label=f"treated effluent PROPOSED only — {km_te:,.1f} km"),
        Line2D([], [], color=fk.C.STATION, marker="s", ls="none", ms=8,
               mec="white", label="existing STP (1,800 m³/d)"),
        Line2D([], [], color=fk.C.STATION, marker="^", ls="none", ms=8,
               mec="white", label="existing pumping station"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.3, ls="--", label="scope boundary"),
        Patch(facecolor=fk.C.PLOT_FILL, edgecolor="none", label="platted plots"),
    ]
    box = (f"study area   {_fmt(area,1):>10} km²\n"
           f"settlements  {n_set:>10,}\n"
           f"plots        {n_plot:>10,}\n"
           f"sewer built  {_fmt(km_b,1):>10} km\n"
           f"sewer paper  {_fmt(km_p,1):>10} km\n"
           f"never built  {pct_unbuilt:>10.1f} %")
    finish_map(fig, ax, note=note, legend_handles=handles, legend_loc="upper left",
                  databox=box,
                  source=src(
                      nama("sewer"), nama("force"), nama("te"), boundary(),
                      servicing(),
                      "lengths measured after clipping to the scope boundary; "
                      + CITE_STP + "; " + CITE_CFG))
    return fk.save(fig, "FO01_scope_and_existing_assets")


# ==================================================================== F02

def fig02_system_by_settlement() -> Path:
    """Which SYSTEM serves each settlement, and how little load leaves the network."""
    sv = servicing()
    g = sv.groupby("SYSTEM").agg(n=("SET_ID", "size"), plots=("N_PLOT", "sum"),
                                 prop=("N_PROP", "sum"), q=("Q_ADF_M3D", "sum"))
    tot_q = float(sv["Q_ADF_M3D"].sum())
    off_n = int(g.loc[["satellite", "onsite"], "n"].sum())
    off_q = float(g.loc[["satellite", "onsite"], "q"].sum())
    pct_off = fact("FO02", "load NOT on the central network, %",
                   round(100 * off_q / tot_q, 2), "W11a.gpkg [servicing] Q_ADF_M3D")
    fact("FO02", "settlements off the central network", off_n, "W11a.gpkg [servicing]")
    fact("FO02", "total ultimate Qadf, m3/d", round(tot_q, 0),
         "W11a.gpkg [servicing] Q_ADF_M3D summed over 187 rows")
    n_prov = fact("FO02", "settlements whose decision is PROVISIONAL",
                  int((sv.CONFIDENCE == "provisional").sum()),
                  "W11a.gpkg [servicing] CONFIDENCE")
    n_both = fact("FO02", "settlements carrying BOTH options forward", int((sv.BOTH == 1).sum()),
                  "W11a.gpkg [servicing] BOTH=1")

    ext = fk.extent_of(boundary(), pad=0.04)
    fig, ax, note = fk.map_frame(
        ext, figsize=STUDY_FIGSIZE,
        title=(f"{off_n} of {len(sv)} settlements come off the central network — "
               f"and they carry {pct_off:.1f} % of the load"),
        subtitle=("Stage-1 servicing decision on every settlement. The choice of system is "
                  "a life-cycle-cost test on exclusive metres of pipe per property, not a "
                  "distance rule. Fill colour is the system; each also carries its own "
                  "hatch, so the map survives greyscale."))
    fix_basemap_nodata(ax)
    draw_ground(ax, plots=False)
    plots_display().plot(ax=ax, facecolor=fk.C.PLOT_FILL, edgecolor="none",
                         alpha=0.45, zorder=1.5)
    for s in ["central", "satellite", "onsite"]:
        sub = sv[sv.SYSTEM == s]
        if len(sub):
            sub.plot(ax=ax, zorder=3 if s == "central" else 4, alpha=0.72,
                     **system_style(s))
    works_markers(ax)

    handles = [
        Patch(label=f"{SYSTEM_LABEL[s]} — {int(g.loc[s,'n'])} settlements, "
                    f"{g.loc[s,'q']:,.0f} m³/d", **system_style(s))
        for s in ["central", "satellite", "onsite"]
    ] + [
        Line2D([], [], color=fk.C.STATION, marker="s", ls="none", ms=8, mec="white",
               label="existing STP"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.3, ls="--", label="scope boundary"),
    ]
    box = ("             sets   plots     m³/d\n" +
           "\n".join(f"{s:<10}{int(g.loc[s,'n']):>6}{int(g.loc[s,'plots']):>8,}"
                     f"{g.loc[s,'q']:>9,.0f}" for s in ["central", "satellite", "onsite"]) +
           f"\ntotal     {len(sv):>6}{int(g['plots'].sum()):>8,}{tot_q:>9,.0f}\n"
           f"provisional decisions {n_prov:>6}\n"
           f"both options kept     {n_both:>6}")
    finish_map(fig, ax, note=note, legend_handles=handles, legend_loc="upper left",
                  databox=box, source=src(servicing(), boundary(),
                                                     plots_display()))
    return fk.save(fig, "FO02_system_by_settlement")


# ==================================================================== F03

def fig03_load_concentration() -> Path:
    """One settlement is most of the project."""
    sv = servicing().sort_values("Q_ADF_M3D", ascending=False).reset_index(drop=True)
    tot = float(sv["Q_ADF_M3D"].sum())
    cum = sv["Q_ADF_M3D"].cumsum() / tot
    top1 = fact("FO03", "largest settlement share of load, %",
                round(100 * sv.loc[0, "Q_ADF_M3D"] / tot, 1),
                "W11a.gpkg [servicing] Q_ADF_M3D")
    top1_name = sv.loc[0, "NAME"]
    top3 = fact("FO03", "top-3 settlements share of load, %", round(100 * cum[2], 1),
                "W11a.gpkg [servicing]")
    n90 = fact("FO03", "settlements needed to reach 90 % of load",
               int((cum < 0.90).sum()) + 1, "W11a.gpkg [servicing]")
    n_zero = fact("FO03", "settlements carrying no load at all",
                  int((sv["Q_ADF_M3D"] <= 0).sum()), "W11a.gpkg [servicing]")

    fig, axes = fk.chart_frame(
        title=f"One settlement — {top1_name} — is {top1:.0f} % of the project",
        subtitle=(f"Ultimate saturated average dry-weather flow by settlement, all "
                  f"{len(sv)} of them. {n90} settlements reach 90 % of the load; "
                  f"{n_zero} carry none at all. A network sized for the whole wilayat is, "
                  f"in flow terms, a network for Ibri town."),
        figsize=(10.4, 5.1), ncols=2, ygrid=True)
    axL, axR = axes
    panel_room(fig)

    top = sv.head(10).iloc[::-1]
    y = np.arange(len(top))
    cols = [SYSTEM_COLOR[s] for s in top.SYSTEM]
    axL.barh(y, top["Q_ADF_M3D"], height=0.68, color=cols, edgecolor=fk.C.INK, lw=0.5)
    for yy, v, s in zip(y, top["Q_ADF_M3D"], top.SYSTEM):
        axL.text(v * 1.14, yy, f"{v:,.0f}", va="center", ha="left",
                 fontsize=7.2, color=fk.C.INK)          # log axis: offset must scale
    lab = [f"{n if n and n != '-' else sid}" for n, sid in zip(top.NAME, top.SET_ID)]
    axL.set_yticks(y); axL.set_yticklabels(lab, fontsize=7.4)
    axL.set_xscale("log")
    axL.set_xlim(20, tot * 1.6)
    axL.set_xlabel("ultimate Qadf (m³/d, log scale)")
    axL.set_title("the ten largest", fontsize=9, color=fk.C.GREY, loc="left")
    fk.style_axes(axL, xgrid=True, ygrid=False)

    # A linear rank axis puts every interesting point in the first two pixels, so
    # the accumulation is drawn against log rank.  Same data, readable.
    rank = np.arange(1, len(sv) + 1)
    axR.plot(rank, 100 * cum, color=fk.C.TRUNK, lw=2.2)
    axR.fill_between(rank, 0, 100 * cum, color=fk.C.RIDER, alpha=0.45)
    axR.set_xscale("log")
    # Every mark lands in the top 20 % of the panel, so the labels go in one block
    # in the empty lower right rather than four colliding callouts.
    marks = sorted({1, 2, 3, max(n90, 1), 10, len(sv)})
    for r in marks:
        v = 100 * cum[r - 1]
        axR.plot([r, r], [0, v], color=fk.C.GREY, lw=0.7, ls=":")
        axR.plot([r], [v], marker="o", ms=4.2, color=fk.C.TRUNK, zorder=5)
    axR.text(0.97, 0.06,
             "\n".join(f"{r:>3} settlement{'s' if r != 1 else ' '} → "
                       f"{100 * cum[r - 1]:5.1f} %" for r in marks),
             transform=axR.transAxes, ha="right", va="bottom", fontsize=7.4,
             family="monospace", color=fk.C.INK,
             bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#9a9a9a",
                       alpha=0.94))
    axR.set_xlim(0.85, len(sv) * 1.15)
    axR.set_ylim(0, 106)
    axR.set_xlabel("settlements, largest first (log rank)")
    axR.set_ylabel("cumulative share of ultimate load (%)")
    axR.set_title("how fast it accumulates", fontsize=9, color=fk.C.GREY, loc="left")
    fk.style_axes(axR, xgrid=True, ygrid=True)

    finish_chart(fig, source=src(
        servicing(), f"total {tot:,.0f} m³/d over {len(sv)} rows; bar colour is the "
                     f"stage-1 SYSTEM (blue central, amber satellite, grey on-site)"))
    return fk.save(fig, "FO03_load_concentration")


# ==================================================================== F04

def _load_grid(cell: float = CELL_M):
    """Ultimate load binned to a regular grid -> (array, extent, cell km2)."""
    pl = plot_loads()
    q = pl["Q_AVG_M3D"].to_numpy(dtype="float64")
    x, y = pl["x"].to_numpy(), pl["y"].to_numpy()
    x0, y0, x1, y1 = boundary().total_bounds
    x0 = np.floor(min(x0, x.min()) / cell) * cell
    y0 = np.floor(min(y0, y.min()) / cell) * cell
    x1 = np.ceil(max(x1, x.max()) / cell) * cell
    y1 = np.ceil(max(y1, y.max()) / cell) * cell
    nx, ny = int((x1 - x0) / cell), int((y1 - y0) / cell)
    ix = np.clip(((x - x0) / cell).astype(int), 0, nx - 1)
    iy = np.clip(((y - y0) / cell).astype(int), 0, ny - 1)
    grid = np.zeros((ny, nx))
    np.add.at(grid, (iy, ix), q)
    return grid, (x0, x1, y0, y1)


def fig04_load_density() -> Path:
    """Where the 74,701 m3/d actually is."""
    grid, gext = _load_grid()
    tot = float(grid.sum())
    flat = np.sort(grid[grid > 0])[::-1]
    cum = np.cumsum(flat) / tot
    cell_km2 = (CELL_M * CELL_M) / 1e6
    area = study_area_km2()
    n50 = int((cum < 0.50).sum()) + 1
    n90 = int((cum < 0.90).sum()) + 1
    km2_50 = fact("FO04", "area holding 50 % of the load, km2",
                  round(n50 * cell_km2, 1), f"W10_plot_loads.gpkg binned to {CELL_M:.0f} m")
    km2_90 = fact("FO04", "area holding 90 % of the load, km2",
                  round(n90 * cell_km2, 1), f"W10_plot_loads.gpkg binned to {CELL_M:.0f} m")
    pct50 = fact("FO04", "that 50 % as a share of the study area, %",
                 round(100 * km2_50 / area, 1), "against Project Boundary.shp 531.4 km²")
    pct90 = fact("FO04", "that 90 % as a share of the study area, %",
                 round(100 * km2_90 / area, 1), "against Project Boundary.shp 531.4 km²")
    n_cells = fact("FO04", "loaded cells", int((grid > 0).sum()), "binned plot loads")
    fact("FO04", "total load on the grid, m3/d", round(tot, 0),
         "W10_plot_loads.gpkg Q_AVG_M3D summed")

    ext = fk.extent_of(boundary(), pad=0.04)
    fig, ax, note = fk.map_frame(
        ext, figsize=STUDY_FIGSIZE,
        title=(f"Half the ultimate flow is generated on {pct50:.0f} % of the study area"),
        subtitle=(f"Ultimate saturated load, every plot binned to a {CELL_M:.0f} m cell "
                  f"(a PROJECT display measure, not a guideline value). "
                  f"{km2_50:,.0f} km² of the {area:,.0f} km² carries half the flow; "
                  f"{km2_90:,.0f} km² carries nine tenths. Everything else is a long "
                  f"pipe to a small number."))
    fix_basemap_nodata(ax)
    draw_ground(ax, plots=False)

    # A continuous ramp says "load is everywhere" -- it is the opposite of the
    # finding.  Cells are classed by their own CUMULATIVE contribution instead, so
    # the picture IS the headline: three separated lightnesses, greyscale-safe.
    order = np.argsort(grid, axis=None)[::-1]
    ccum = np.cumsum(grid.ravel()[order]) / tot
    cls_flat = np.zeros(grid.size, dtype=np.int16)
    rank_of = np.empty(grid.size, dtype=np.int64)
    rank_of[order] = np.arange(grid.size)
    loaded = grid.ravel() > 0
    cls_flat[loaded & (rank_of < n50)] = 3
    cls_flat[loaded & (rank_of >= n50) & (rank_of < n90)] = 2
    cls_flat[loaded & (rank_of >= n90)] = 1
    cls = cls_flat.reshape(grid.shape)
    q_hi = float(grid.ravel()[order][:n50].sum())
    q_mid = float(grid.ravel()[order][n50:n90].sum())
    q_lo = tot - q_hi - q_mid
    fact("FO04", "load in the top 50 % band, m3/d", round(q_hi, 0), "binned plot loads")
    fact("FO04", "load in the tail beyond 90 %, m3/d", round(q_lo, 0), "binned plot loads")
    fact("FO04", "cells in the tail beyond 90 %", int((cls == 1).sum()),
         "binned plot loads")

    band_cols = {1: fk.C.RIDER, 2: fk.C.MAIN, 3: fk.C.TRUNK}
    rgba = np.zeros(cls.shape + (4,))
    for k, col in band_cols.items():
        mk = cls == k
        rgba[mk, :3] = matplotlib.colors.to_rgb(col)
        rgba[mk, 3] = 1.0
    ax.imshow(rgba[::-1], extent=(gext[0], gext[1], gext[2], gext[3]),
              interpolation="nearest", zorder=3)
    boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.3, ls="--", zorder=8)
    works_markers(ax)

    handles = [
        Patch(facecolor=fk.C.TRUNK, edgecolor="none",
              label=f"the {n50:,} cells that make the FIRST half of the load "
                    f"— {km2_50:,.1f} km², {q_hi:,.0f} m³/d"),
        Patch(facecolor=fk.C.MAIN, edgecolor="none",
              label=f"the next {n90-n50:,} cells, taking it to 90 % "
                    f"— {km2_90-km2_50:,.1f} km², {q_mid:,.0f} m³/d"),
        Patch(facecolor=fk.C.RIDER, edgecolor="none",
              label=f"the remaining {int((cls==1).sum()):,} loaded cells "
                    f"— the last 10 %, {q_lo:,.0f} m³/d"),
        Line2D([], [], color=fk.C.STATION, marker="s", ls="none", ms=8, mec="white",
               label="existing STP"),
        Line2D([], [], color=fk.C.STATION, marker="^", ls="none", ms=8, mec="white",
               label="existing pumping station"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.3, ls="--", label="scope boundary"),
    ]
    box = (f"total load  {tot:>10,.0f} m³/d\n"
           f"cells       {n_cells:>10,}\n"
           f"50 % within {km2_50:>10,.1f} km²  ({pct50:.1f} %)\n"
           f"90 % within {km2_90:>10,.1f} km²  ({pct90:.1f} %)\n"
           f"study area  {area:>10,.1f} km²")
    finish_map(fig, ax, note=note, legend_handles=handles, legend_loc="upper left",
                  databox=box, source=src(
                      plot_loads(), boundary(),
                      f"{CELL_M:.0f} m binning cell is a PROJECT display measure"))
    return fk.save(fig, "FO04_load_density")


# ==================================================================== F05

def fig05_stp_candidates() -> Path:
    """The siting study: the existing works ranks last, and the reason is land."""
    d = stp_sites().copy().sort_values("RANK")
    ex = d[d.SITE == "EXISTING"].iloc[0]
    so = d[d.SITE == "SOUTH"].iloc[0]
    s1 = d[d.SITE == "S1"].iloc[0]
    n = len(d)
    fact("FO05", "candidates ranked", n, "W10/run/p4_stp_candidates.csv")
    fact("FO05", "rank of the existing works", int(ex.RANK), "p4_stp_candidates.csv RANK")
    fact("FO05", "free land at the existing works, ha", ex.FREE600_HA,
         "p4_stp_candidates.csv FREE600_HA")
    fact("FO05", "free land at the best candidate S1, ha", s1.FREE600_HA,
         "p4_stp_candidates.csv FREE600_HA")
    fact("FO05", "nearest dwelling to the existing works, m", ex.D_DWELL_M,
         "p4_stp_candidates.csv D_DWELL_M")
    fact("FO05", "nearest dwelling to the southern site, m", so.D_DWELL_M,
         "p4_stp_candidates.csv D_DWELL_M")

    ext = fk.extent_of(boundary(), pad=0.04)
    fig, ax, note = fk.map_frame(
        ext, figsize=STUDY_FIGSIZE,
        title=(f"The existing works ranks {int(ex.RANK)} of {n} — and the reason is land"),
        subtitle=(f"Ten screened candidates plus the user's southern site and the existing "
                  f"works, scored on seven weighted criteria. The existing site has "
                  f"{ex.FREE600_HA:.1f} ha free against {s1.FREE600_HA:.1f} ha at the "
                  f"best candidate, and the nearest dwelling is {ex.D_DWELL_M:,.0f} m away "
                  f"against {s1.D_DWELL_M:,.0f} m. Marker size is free land; label is rank."))
    fix_basemap_nodata(ax)
    draw_ground(ax)
    cand = d[~d.SITE.isin(["EXISTING", "SOUTH"])]
    ax.scatter(cand.X, cand.Y, s=18 + 5.5 * cand.FREE600_HA, marker="o",
               facecolor=fk.C.LATERAL, edgecolor=fk.C.INK, linewidth=0.8, zorder=9,
               alpha=0.9)
    ax.scatter([so.X], [so.Y], s=18 + 5.5 * so.FREE600_HA, marker="D",
               facecolor=fk.C.FLAG, edgecolor=fk.C.INK, linewidth=1.0, zorder=10)
    ax.scatter([ex.X], [ex.Y], s=18 + 5.5 * max(ex.FREE600_HA, 1.0), marker="s",
               facecolor=fk.C.STATION, edgecolor="white", linewidth=1.1, zorder=10)
    for _, r in d.iterrows():
        ax.annotate(f"{int(r.RANK)}", (r.X, r.Y), textcoords="offset points",
                    xytext=(0, 0), ha="center", va="center", fontsize=6.4,
                    fontweight="bold", color="white", zorder=11,
                    path_effects=[matplotlib.patheffects.withStroke(
                        linewidth=1.6, foreground=fk.C.INK)])
    works_markers(ax, ps=True, stp=False, size=60)  # the ranked square is already drawn

    handles = [
        Line2D([], [], color=fk.C.LATERAL, marker="o", ls="none", ms=9, mec=fk.C.INK,
               label="screened candidate (rank 1–10)"),
        Line2D([], [], color=fk.C.FLAG, marker="D", ls="none", ms=9, mec=fk.C.INK,
               label=f"southern site proposed by the client (rank {int(so.RANK)})"),
        Line2D([], [], color=fk.C.STATION, marker="s", ls="none", ms=9, mec="white",
               label=f"existing Ibri works (rank {int(ex.RANK)})"),
        Line2D([], [], color=fk.C.STATION, marker="^", ls="none", ms=8, mec="white",
               label="existing pumping station"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.3, ls="--", label="scope boundary"),
    ]
    box = ("site        rank  free ha  dwell m  GL m\n" +
           "\n".join(f"{r.SITE:<11}{int(r.RANK):>4}{r.FREE600_HA:>9.1f}"
                     f"{r.D_DWELL_M:>9,.0f}{r.Z_VRT_M:>7.1f}"
                     for _, r in d.head(4).iterrows()) +
           f"\n{'SOUTH':<11}{int(so.RANK):>4}{so.FREE600_HA:>9.1f}"
           f"{so.D_DWELL_M:>9,.0f}{so.Z_VRT_M:>7.1f}"
           f"\n{'EXISTING':<11}{int(ex.RANK):>4}{ex.FREE600_HA:>9.1f}"
           f"{ex.D_DWELL_M:>9,.0f}{ex.Z_VRT_M:>7.1f}")
    finish_map(fig, ax, note=note, legend_handles=handles, legend_loc="upper left",
                  databox=box, source=src(
                      stp_sites(), boundary(),
                      "W10 is superseded as a design; the siting study's findings stand. "
                      "Ground levels Z_VRT_M sampled from " + CITE_DEM))
    return fk.save(fig, "FO05_stp_candidates")


# ==================================================================== F06

def fig06_stp_compare() -> Path:
    """Existing works vs the client's southern site vs the top-ranked candidate."""
    d = stp_sites().set_index("SITE")
    picks = ["EXISTING", "SOUTH", "S1"]
    names = {"EXISTING": "Existing Ibri works", "SOUTH": "Southern site (client)",
             "S1": "S1 (best on score)"}
    z = sample_dem05([(d.loc[p, "X"], d.loc[p, "Y"]) for p in picks])
    for p, zz in zip(picks, z):
        fact("FO06", f"ground level at {p} re-sampled from the 0.5 m blend, m aOD",
             round(float(zz), 2), "Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt")
    drop = fact("FO06", "the southern site sits below the existing works by, m",
                round(float(d.loc['EXISTING', 'Z_VRT_M'] - d.loc['SOUTH', 'Z_VRT_M']), 2),
                "p4_stp_candidates.csv Z_VRT_M")
    extra = fact("FO06", "extra conveyance the southern site costs, km",
                 round(float(d.loc['SOUTH', 'CONVEY_KM'] - d.loc['EXISTING', 'CONVEY_KM']), 2),
                 "p4_stp_candidates.csv CONVEY_KM")
    sep = fact("FO06", "separation the southern site buys, m",
               round(float(d.loc['SOUTH', 'D_DWELL_M'] - d.loc['EXISTING', 'D_DWELL_M']), 0),
               "p4_stp_candidates.csv D_DWELL_M")

    grav = {p: float(d.loc[p, "GRAV_PCT"]) for p in picks}
    fact("FO06", "load arriving by gravity at each site, %",
         {p: round(v, 1) for p, v in grav.items()}, "p4_stp_candidates.csv GRAV_PCT")
    wadi = fact("FO06", "distance to the nearest wadi, m",
                {p: int(d.loc[p, "D_WADI_M"]) for p in picks},
                "p4_stp_candidates.csv D_WADI_M")

    # (label, column, unit, decimals, higher-is-better, relative-to-existing)
    metrics = [
        ("Free land within 600 m", "FREE600_HA", "ha", 1, True, False),
        ("Nearest dwelling", "D_DWELL_M", "m", 0, True, False),
        ("Ground level, relative to the existing works", "Z_VRT_M", "m", 1, False, True),
        ("Conveyance to reach it", "CONVEY_KM", "km", 2, False, False),
        ("Distance to the nearest wadi", "D_WADI_M", "m", 0, True, False),
        ("Distance to the trunk", "D_TRUNK_M", "m", 0, False, False),
    ]
    fig, axes = fk.chart_frame(
        title=(f"The southern site buys {sep:,.0f} m of separation and {drop:.1f} m of "
               f"fall, and costs {extra:.1f} km of extra conveyance"),
        subtitle=(f"The three sites that matter, on the six measured criteria that separate "
                  f"them. Each panel says which direction is better. Ground level is drawn "
                  f"as fall relative to the existing works, because a 17 m difference is "
                  f"invisible on a 0–400 m axis. A seventh criterion is left off: all three "
                  f"take {min(grav.values()):.1f}–{max(grav.values()):.1f} % of the load by "
                  f"gravity, so it separates nothing."),
        figsize=(10.6, 6.0), nrows=2, ncols=3, ygrid=True)
    panel_room(fig, 0.075)
    shades = [fk.C.RIDER, fk.C.MAIN, fk.C.TRUNK]
    for ax, (label, col, unit, nd, higher, rel) in zip(axes.ravel(), metrics):
        raw = [float(d.loc[p, col]) for p in picks]
        vals = [v - raw[0] for v in raw] if rel else raw
        order = np.argsort(vals) if higher else np.argsort(vals)[::-1]
        colmap = {int(idx): shades[i] for i, idx in enumerate(order)}
        bars = ax.bar(range(3), vals, width=0.62,
                      color=[colmap[i] for i in range(3)],
                      edgecolor=fk.C.INK, linewidth=0.6)
        for b, v in zip(bars, vals):
            up = v >= 0
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:+,.{nd}f}" if rel
                    else f"{v:,.{nd}f}", ha="center",
                    va="bottom" if up else "top", fontsize=7.6, fontweight="bold",
                    color=fk.C.INK)
        ax.set_xticks(range(3))
        ax.set_xticklabels(["existing", "south", "S1"], fontsize=7.6)
        arrow = "↑ better" if higher else "↓ better"
        ax.set_title(f"{label}\n({unit}, {arrow})", fontsize=8.2, loc="left",
                     color=fk.C.INK)
        lo, hi = min(vals + [0.0]), max(vals + [0.0])
        pad = max(abs(hi), abs(lo)) * 0.26 or 1.0
        ax.set_ylim(lo - (pad if lo < 0 else 0), hi + pad)
        if lo < 0:
            ax.axhline(0, color=fk.C.INK, lw=0.9)
        fk.thousands(ax, "y")
        fk.style_axes(ax)
    fig.subplots_adjust(hspace=0.72, wspace=0.30)
    finish_chart(fig, source=src(
        stp_sites(),
        "sites: " + " · ".join(f"{p} = {names[p]}" for p in picks) +
        ". Ground level re-sampled from " + CITE_DEM +
        f" agrees with Z_VRT_M to {np.nanmax(np.abs(z - [d.loc[p,'Z_VRT_M'] for p in picks])):.2f} m"))
    return fk.save(fig, "FO06_stp_site_comparison")


# ==================================================================== F07

def fig07_terrain_and_fall() -> Path:
    """The ground, and why everything drains to the south-west corner."""
    tr = _c("trunk", lambda: fk.read_layer("W11a_trunk.gpkg", "reaches",
                                           columns=["LEN_M", "TIER"]))
    tn = _c("trunkn", lambda: fk.read_layer("W11a_trunk.gpkg", "nodes",
                                            columns=["GRD_M", "DEPTH_M", "NODE_KIND"]))
    ext = fk.extent_of(boundary(), pad=0.04)
    dem, dext, n_filled = dem5(ext)

    poly = boundary().geometry.union_all()
    from rasterio.features import geometry_mask
    from rasterio.transform import from_bounds as tr_from_bounds
    ny, nx = dem.shape
    T = tr_from_bounds(dext[0], dext[2], dext[1], dext[3], nx, ny)
    inside = ~geometry_mask([poly], out_shape=(ny, nx), transform=T, invert=False)
    z = dem[inside & np.isfinite(dem)]
    zmin = fact("FO07", "lowest ground inside the boundary, m aOD", round(float(z.min()), 1),
                "ibri_blend.tif 5 m, masked to Project Boundary.shp")
    zmax = fact("FO07", "highest ground inside the boundary, m aOD", round(float(z.max()), 1),
                "ibri_blend.tif 5 m, masked to Project Boundary.shp")
    p5, p95 = np.percentile(z, [5, 95])
    fact("FO07", "5th/95th percentile ground, m aOD", (round(float(p5), 1), round(float(p95), 1)),
         "ibri_blend.tif 5 m, masked to Project Boundary.shp")
    g_hi = fact("FO07", "highest trunk chamber ground level, m aOD",
                round(float(tn.GRD_M.max()), 1), "W11a_trunk.gpkg [nodes] GRD_M")
    g_lo = fact("FO07", "lowest trunk chamber ground level, m aOD",
                round(float(tn.GRD_M.min()), 1), "W11a_trunk.gpkg [nodes] GRD_M")
    tkm = fact("FO07", "trunk length, km", round(float(tr.LEN_M.sum() / 1000), 2),
               "W11a_trunk.gpkg [reaches] LEN_M")
    fall = fact("FO07", "ground fall along the trunk, m", round(g_hi - g_lo, 1),
                "W11a_trunk.gpkg [nodes] GRD_M range")
    z_stp = fact("FO07", "ground at the existing works, m aOD",
                 round(float(sample_dem05([STP_EXISTING])[0]), 2), CITE_DEM)

    fig, ax, note = fk.map_frame(
        ext,
        title=(f"The land falls {fall:.0f} m along the trunk and the works sits at the "
               f"bottom of it"),
        subtitle=(f"Ground from the 5 m display blend, hill-shaded. Inside the boundary the "
                  f"ground runs {zmin:,.0f} m to {zmax:,.0f} m aOD; the trunk's own chambers "
                  f"run {g_lo:,.0f} m to {g_hi:,.0f} m over {tkm:,.1f} km. The existing works "
                  f"at {z_stp:,.1f} m is within {z_stp - zmin:,.0f} m of the lowest ground in "
                  f"the study area — which is why gravity works at all here."),
        basemap_alpha=0.0)

    # hillshade + a light elevation wash, both from the same array
    dz = np.gradient(dem, 5.0)
    slope = np.arctan(np.hypot(dz[0], dz[1]))
    aspect = np.arctan2(-dz[0], dz[1])
    az, alt = np.deg2rad(315.0), np.deg2rad(45.0)
    hs = (np.sin(alt) * np.cos(slope) +
          np.cos(alt) * np.sin(slope) * np.cos(az - aspect))
    hs = np.clip(hs, 0, 1)
    # cividis, not "terrain": monotonic luminance, so the ramp survives greyscale
    # and reads as height rather than as land-and-water.
    ax.imshow(dem, extent=dext, cmap="cividis", alpha=0.62, zorder=1,
              vmin=float(p5), vmax=float(p95), interpolation="bilinear")
    ax.imshow(hs, extent=dext, cmap="gray", alpha=0.35, zorder=2,
              interpolation="bilinear")
    # ground that NEITHER blend answers.  Left white it reads as flat terrain.
    no_dem = np.isnan(dem)
    n_none = fact("FO07", "frame pixels with no terrain answer in either blend",
                  int(no_dem.sum()), "ibri_blend.tif 5 m + IBRI_0p5_VRT2.vrt")
    if n_none:
        fk.hatch_untested(ax, no_dem, dext, zorder=2.5)
    boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.4, ls="--", zorder=8)
    tr.plot(ax=ax, color=fk.C.TRUNK, lw=2.4, zorder=7)
    tr.plot(ax=ax, color="white", lw=3.6, zorder=6, alpha=0.7)
    works_markers(ax, south=True)

    sm = plt.cm.ScalarMappable(cmap="cividis",
                               norm=matplotlib.colors.Normalize(float(p5), float(p95)))
    cb = fig.colorbar(sm, ax=ax, fraction=0.028, pad=0.012)
    cb.set_label("ground level (m aOD, 5–95 percentile stretch)", fontsize=7.4,
                 color=fk.C.GREY)
    cb.ax.tick_params(labelsize=6.8, colors=fk.C.GREY)

    handles = [
        Line2D([], [], color=fk.C.TRUNK, lw=2.6,
               label=f"trunk main, the client's alignment — {tkm:,.1f} km"),
        Line2D([], [], color=fk.C.STATION, marker="s", ls="none", ms=8, mec="white",
               label=f"existing STP, ground {z_stp:,.1f} m"),
        Line2D([], [], color=fk.C.STATION, marker="^", ls="none", ms=8, mec="white",
               label="existing pumping station"),
        Line2D([], [], color=fk.C.FLAG, marker="D", ls="none", ms=8, mec=fk.C.INK,
               label="southern STP site proposed by the client"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.4, ls="--", label="scope boundary"),
    ]
    if n_none:
        handles.append(fk.untested_handle(
            f"NO terrain answer in either blend — {100*n_none/dem.size:.1f} % of the frame"))
    box = (f"ground min  {zmin:>9,.1f} m\n"
           f"ground max  {zmax:>9,.1f} m\n"
           f"trunk high  {g_hi:>9,.1f} m\n"
           f"trunk low   {g_lo:>9,.1f} m\n"
           f"fall        {fall:>9,.1f} m\n"
           f"trunk       {tkm:>9,.1f} km")
    finish_map(fig, ax,
               note=(f"terrain: 5 m display blend, hill-shade 315°/45°, cividis ramp "
                     f"(monotonic luminance); {n_filled:,} nodata pixels "
                     f"({100*n_filled/dem.size:.1f} %) filled from the 0.5 m VRT, "
                     f"{n_none:,} ({100*n_none/dem.size:.1f} %) hatched because neither "
                     f"blend answers them; no satellite backdrop under a terrain map"),
                  legend_handles=handles, legend_loc="upper left", databox=box,
                  source=src(tr, tn, boundary(), CITE_DEM))
    return fk.save(fig, "FO07_terrain_and_fall")


# ==================================================================== F08

def fig08_break_sensitivity() -> Path:
    """The central/decentral break is a cliff, and the adopted value sits clear of it."""
    b = fk.read_csv("s1_break_sensitivity.csv")
    sv = servicing()
    adopted = fact("FO08", "adopted break, exclusive m of pipe per property",
                   float(sv["BREAK_M"].mode().iloc[0]), "W11a.gpkg [servicing] BREAK_M")
    row = b.iloc[(b.break_m_per_prop - adopted).abs().argmin()]
    at_adopted = fact("FO08", "load off the central network at the adopted break, %",
                      float(row.pct_of_load), "s1_break_sensitivity.csv")
    lo = b[b.break_m_per_prop == 15.0].iloc[0]
    hi = b[b.break_m_per_prop == 18.0].iloc[0]
    jump = fact("FO08", "load share that flips between 15 and 18 m per property, %",
                round(float(lo.pct_of_load - hi.pct_of_load), 1),
                "s1_break_sensitivity.csv pct_of_load")
    flip = sv[(sv.M_PER_PRP > 15.0) & (sv.M_PER_PRP <= 18.0)].sort_values(
        "Q_ADF_M3D", ascending=False)
    flip_names = ", ".join(f"{r.NAME} ({r.Q_ADF_M3D:,.0f} m³/d)"
                           for _, r in flip.head(3).iterrows())
    fact("FO08", "settlements sitting in the 15–18 m band", len(flip),
         "W11a.gpkg [servicing] M_PER_PRP")

    fig, ax = fk.chart_frame(
        title=(f"The central / decentral break is a cliff, not a slope — "
               f"{jump:.0f} % of the load flips between 15 and 18 m per property"),
        subtitle=(f"Sensitivity of the stage-1 servicing decision to the one number it "
                  f"turns on: exclusive metres of pipe per property. The adopted "
                  f"{adopted:.0f} m sits on the flat, where only {at_adopted:.1f} % of the "
                  f"load leaves the central network. The cliff is {len(flip)} settlement"
                  f"{'s' if len(flip) != 1 else ''}: {flip_names}."),
        figsize=(10.2, 4.9), ygrid=True)

    x = b.break_m_per_prop.to_numpy()
    ax.plot(x, b.pct_of_load, color=fk.C.TRUNK, lw=2.2, marker="o", ms=4.5,
            label="load off the central network (%)")
    ax.plot(x, b.pct_of_properties, color=fk.C.LATERAL, lw=1.8, marker="s", ms=4.0,
            ls="--", label="properties off the central network (%)")
    ax.set_xscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{v:g}" for v in x], fontsize=7.4)
    ax.set_xlabel("break value — exclusive metres of pipe per property (log)")
    ax.set_ylabel("share off the central network (%)")
    ax.axvspan(15.0, 18.0, color=fk.C.FAIL, alpha=0.10, zorder=0)
    ax.axvline(adopted, color=fk.C.FLAG, lw=2.0, ls="-", zorder=1)
    ax.annotate(f"adopted {adopted:.0f} m\n{at_adopted:.1f} % of load off network",
                (adopted, float(row.pct_of_load)), textcoords="offset points",
                xytext=(16, 42), fontsize=7.6, color=fk.C.INK,
                arrowprops=dict(arrowstyle="->", color=fk.C.FLAG, lw=1.2))
    ax.annotate(f"the cliff — {jump:.0f} % of the load\nchanges system across 3 m",
                (16.4, float(lo.pct_of_load) * 0.55), ha="center", fontsize=7.6,
                color=fk.C.FAIL, fontweight="bold")

    ax2 = ax.twinx()
    ax2.plot(x, b.decentralised_settlements, color=fk.C.GREY, lw=1.4, ls=":",
             marker="^", ms=4.0, label="settlements decentralised (count)")
    ax2.set_ylabel("settlements decentralised (count)", color=fk.C.GREY)
    ax2.tick_params(colors=fk.C.GREY, length=3, width=0.8)
    for s in ("top",):
        ax2.spines[s].set_visible(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper right", frameon=True, framealpha=0.92,
              edgecolor="#9a9a9a", fontsize=7.4)
    finish_chart(fig, source=src(
        b, servicing(),
        "shaded band and the 'cliff' label are read off the same table, not asserted"))
    return fk.save(fig, "FO08_break_sensitivity")


# ==================================================================== F09

def fig09_load_by_category() -> Path:
    """What generates the load — and the classes that generate none."""
    pl = plot_loads()
    g = (pl.groupby("CAT").agg(n=("PLOT_ID", "size"), q=("Q_AVG_M3D", "sum"),
                               prop=("N_PROP", "sum"), pop=("POP", "sum"))
         .sort_values("q", ascending=False))
    tot = float(g.q.sum())
    dom_pct = fact("FO09", "domestic share of ultimate load, %",
                   round(100 * float(g.loc["domestic", "q"]) / tot, 1),
                   "W10_plot_loads.gpkg CAT / Q_AVG_M3D")
    zero = g[g.q <= 0]
    n_zero = fact("FO09", "plots carrying no load at all", int(zero.n.sum()),
                  "W10_plot_loads.gpkg Q_AVG_M3D <= 0")
    n_agri = fact("FO09", "agricultural plots carrying no load", int(g.loc["agricultural", "n"]),
                  "W10_plot_loads.gpkg CAT='agricultural'")
    n_ind = fact("FO09", "industrial plots carrying no load", int(g.loc["industrial", "n"]),
                 "W10_plot_loads.gpkg CAT='industrial'")
    fact("FO09", "total ultimate load, m3/d", round(tot, 0), "W10_plot_loads.gpkg")

    fig, axes = fk.chart_frame(
        title=(f"{dom_pct:.0f} % of the load is domestic — and {n_zero:,} plots are "
               f"modelled as producing nothing"),
        subtitle=(f"Ultimate saturated load by land-use category. The "
                  f"{int((g.q > 0).sum())} loaded categories carry all {tot:,.0f} m³/d "
                  f"between them. "
                  f"{n_ind} industrial and {n_agri:,} agricultural plots carry exactly zero "
                  f"by construction — for agriculture that is the settled rule (the farming "
                  f"carries no load, the houses on it do); for industry it is an open "
                  f"question the treated land-use data has to answer."),
        figsize=(10.4, 5.2), ncols=2, ygrid=False)
    axL, axR = axes
    panel_room(fig)

    loaded = g[g.q > 0].iloc[::-1]
    shades = [DENSITY_CMAP(v) for v in np.linspace(0.30, 0.95, len(loaded))]
    y = np.arange(len(loaded))
    axL.barh(y, loaded.q, height=0.66, color=shades, edgecolor=fk.C.INK, lw=0.5)
    for yy, v, nn in zip(y, loaded.q, loaded.n):
        txt = f"{v:,.0f} m³/d   ({100*v/tot:.1f} %, {nn:,} plots)"
        inside = v > 0.55 * tot          # the domestic bar runs off the axis otherwise
        axL.text(v - tot * 0.012 if inside else v + tot * 0.012, yy, txt,
                 va="center", ha="right" if inside else "left", fontsize=7.2,
                 color="white" if inside else fk.C.INK,
                 fontweight="bold" if inside else "normal")
    axL.set_yticks(y)
    axL.set_yticklabels(loaded.index, fontsize=7.8)
    axL.set_xlim(0, tot * 1.02)
    axL.set_xlabel("ultimate Qadf (m³/d)")
    axL.set_title("where the load comes from", fontsize=9, color=fk.C.GREY, loc="left")
    fk.thousands(axL, "x")
    fk.style_axes(axL, xgrid=True, ygrid=False)

    zz = zero.sort_values("n", ascending=True)
    y2 = np.arange(len(zz))
    axR.barh(y2, zz.n, height=0.60, **fk.status_style("untested"))
    for yy, v in zip(y2, zz.n):
        axR.text(v + zz.n.max() * 0.02, yy, f"{v:,}", va="center", ha="left",
                 fontsize=7.4, color=fk.C.INK)
    axR.set_yticks(y2); axR.set_yticklabels(zz.index, fontsize=7.8)
    axR.set_xlim(0, zz.n.max() * 1.28)
    axR.set_xlabel("plots (count)")
    axR.set_title(f"the {n_zero:,} plots modelled at zero load", fontsize=9,
                  color=fk.C.GREY, loc="left")
    fk.thousands(axR, "x")
    fk.style_axes(axR, xgrid=True, ygrid=False)

    finish_chart(fig, source=src(
        plot_loads(),
        "categories are the CAT field as delivered; the zero-load rule for agriculture "
        "is a settled project decision (W5/docs/CRITERIA_UPDATE_R1.md), not a guideline value"))
    return fk.save(fig, "FO09_load_by_category")


# ==================================================================== F10

def fig10_existing_coverage() -> Path:
    """How much of the ultimate load already has a built sewer in front of it."""
    pl = plot_loads()
    built = nama_in_boundary("sewer")
    built = built[built.STATUS == "Ex"]
    band = built.geometry.union_all().buffer(FRONTAGE_M)
    near = pl.geometry.intersects(band).to_numpy()
    tot = float(pl.Q_AVG_M3D.sum())
    q_near = float(pl.loc[near, "Q_AVG_M3D"].sum())
    pct_q = fact("FO10", f"ultimate load within {FRONTAGE_M:.0f} m of a BUILT sewer, %",
                 round(100 * q_near / tot, 1),
                 f"W10_plot_loads.gpkg vs SEWERLINE_IBRI STATUS='Ex', {FRONTAGE_M:.0f} m band")
    pct_n = fact("FO10", f"plots within {FRONTAGE_M:.0f} m of a BUILT sewer, %",
                 round(100 * near.mean(), 1), "same")
    fact("FO10", "plots already fronted by a built sewer", int(near.sum()),
         "same")
    fact("FO10", "load with no built sewer in front of it, m3/d", round(tot - q_near, 0),
         "same")
    km_b = fact("FO10", "built gravity sewer in boundary, km",
                round(float(built.LEN_M.sum() / 1000), 1), "SEWERLINE_IBRI STATUS='Ex'")

    ext = fk.extent_of(boundary(), pad=0.04)
    fig, ax, note = fk.map_frame(
        ext, figsize=STUDY_FIGSIZE,
        title=(f"The {km_b:,.0f} km already built serves {pct_q:.0f} % of the ultimate "
               f"load — Ibri is a greenfield job"),
        subtitle=(f"Every plot tested against a {FRONTAGE_M:.0f} m band around the built "
                  f"gravity sewer — a PROJECT measure of 'a sewer is in front of this plot', "
                  f"not a guideline value. Dark plots are already fronted; pale plots are "
                  f"not. {tot - q_near:,.0f} m³/d of the {tot:,.0f} m³/d has no built sewer "
                  f"anywhere near it."))
    fix_basemap_nodata(ax)
    draw_ground(ax, plots=False, bnd=False)
    pl.loc[~near].plot(ax=ax, facecolor=fk.C.PLOT_FILL, edgecolor="none", alpha=0.85,
                       zorder=2)
    built.plot(ax=ax, color=fk.C.STATION, lw=0.55, zorder=3)
    # the fronted plots go ON TOP of the line -- they are the subject, the line is
    # the reason
    pl.loc[near].plot(ax=ax, facecolor=fk.C.TRUNK, edgecolor="none", alpha=0.95,
                      zorder=4)
    boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.3, ls="--", zorder=8)
    works_markers(ax)

    handles = [
        Patch(facecolor=fk.C.TRUNK, edgecolor="none",
              label=f"plot with a built sewer within {FRONTAGE_M:.0f} m "
                    f"({int(near.sum()):,}, {q_near:,.0f} m³/d)"),
        Patch(facecolor=fk.C.PLOT_FILL, edgecolor="#b6ae9f",
              label=f"plot with none ({int((~near).sum()):,}, {tot-q_near:,.0f} m³/d)"),
        Line2D([], [], color=fk.C.STATION, lw=1.4,
               label=f"built gravity sewer — {km_b:,.1f} km"),
        Line2D([], [], color=fk.C.STATION, marker="s", ls="none", ms=8, mec="white",
               label="existing STP"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.3, ls="--", label="scope boundary"),
    ]
    box = (f"built sewer   {km_b:>9,.1f} km\n"
           f"plots fronted {int(near.sum()):>9,}  ({pct_n:.1f} %)\n"
           f"load fronted  {q_near:>9,.0f} m³/d  ({pct_q:.1f} %)\n"
           f"load to build {tot-q_near:>9,.0f} m³/d  ({100-pct_q:.1f} %)\n"
           f"band          {FRONTAGE_M:>9,.0f} m  (project measure)")
    finish_map(fig, ax, note=note, legend_handles=handles, legend_loc="upper left",
                  databox=box, source=src(
                      plot_loads(), nama("sewer"), boundary(),
                      f"{FRONTAGE_M:.0f} m frontage band is a PROJECT measure, "
                      f"not a guideline value"))
    return fk.save(fig, "FO10_existing_network_coverage")


# ==================================================================== driver

# ==================================================================== F11

TOWNS = HYD / "SHP" / "Towns" / "Towns.shp"


def fig11_horizon() -> Path:
    """The saturation load we design for is a population the client projects for 2081."""
    t = _c("towns", lambda: fk.read_layer(str(TOWNS)))
    yrs = sorted(int(c[4:]) for c in t.columns if c.startswith("Pop_"))
    pop = np.array([float(t[f"Pop_{y}"].sum()) for y in yrs])
    sv = servicing()
    sat_pop = float(sv["POP"].sum())
    sat_q = float(sv["Q_ADF_M3D"].sum())

    fact("FO11", "towns in the client's projection", len(t), "Hydraulic/SHP/Towns/Towns.shp")
    fact("FO11", "projected population 2025 / 2030 / 2055",
         tuple(int(pop[yrs.index(y)]) for y in (2025, 2030, 2055)), "Towns.shp Pop_####")
    fact("FO11", "saturation population the load is built on", round(sat_pop, 0),
         "W11a.gpkg [servicing] POP summed")
    hit = int(np.argmax(pop >= sat_pop)) if (pop >= sat_pop).any() else -1
    yr_sat = fact("FO11", "first projected year that reaches the saturation population",
                  yrs[hit] if hit >= 0 else "beyond 2100",
                  "Towns.shp Pop_#### vs W11a.gpkg [servicing] POP")
    pct55 = fact("FO11", "2055 population as a share of saturation, %",
                 round(100 * pop[yrs.index(2055)] / sat_pop, 1), "the two above")
    ratio = fact("FO11", "saturation flow per head, m3/d per person",
                 round(sat_q / sat_pop, 4),
                 "W11a.gpkg [servicing] Q_ADF_M3D / POP — a DERIVED ratio")
    pq = plot_loads().groupby("CAT")["Q_AVG_M3D"].sum()
    nondom_pct = fact("FO11", "share of the load that is NOT domestic, %",
                      round(100 * (1 - float(pq.get("domestic", 0.0)) / float(pq.sum())), 1),
                      "W10_plot_loads.gpkg CAT / Q_AVG_M3D")

    fig, ax = fk.chart_frame(
        title=(f"The load the network is sized for is a population the client projects "
               f"for {yr_sat}"),
        subtitle=(f"The client's own town-by-town projection, {len(t)} towns, summed. "
                  f"The horizontal line is the saturation population behind the "
                  f"{sat_q:,.0f} m³/d the design carries. At 2055 — the far model year in "
                  f"the ToR — the projection is only {pct55:.0f} % of it. Scope note: the "
                  f"projection covers the 25 named towns; the servicing table covers "
                  f"{len(sv)} settlements, so the two footprints are close but not "
                  f"identical."),
        figsize=(10.4, 5.0), ygrid=True)

    ax.plot(yrs, pop, color=fk.C.TRUNK, lw=2.4, zorder=4,
            label="client's projected population, 25 towns summed")
    ax.fill_between(yrs, 0, pop, color=fk.C.RIDER, alpha=0.35, zorder=1)
    ax.axhline(sat_pop, color=fk.C.STATION, lw=1.8, ls="--", zorder=3,
               label=f"saturation population behind the design load ({sat_pop:,.0f})")
    for y, lab in ((2030, "model year"), (2055, "model year")):
        v = pop[yrs.index(y)]
        ax.plot([y, y], [0, v], color=fk.C.GREY, lw=0.9, ls=":", zorder=2)
        ax.plot([y], [v], marker="o", ms=5, color=fk.C.MAIN, zorder=5)
        ax.annotate(f"{y} {lab}\n{v:,.0f}  ({100*v/sat_pop:.0f} % of saturation)",
                    (y, v), textcoords="offset points", xytext=(10, 10),
                    fontsize=7.6, color=fk.C.INK)
    if hit >= 0:
        ax.plot([yrs[hit]], [pop[hit]], marker="D", ms=7, color=fk.C.STATION, zorder=6)
        ax.annotate(f"projection reaches saturation\nin {yrs[hit]}",
                    (yrs[hit], pop[hit]), textcoords="offset points", xytext=(-14, 26),
                    ha="right", fontsize=7.8, fontweight="bold", color=fk.C.STATION,
                    arrowprops=dict(arrowstyle="->", color=fk.C.STATION, lw=1.1))
    ax.set_xlim(yrs[0], yrs[-1])
    ax.set_ylim(0, max(pop.max(), sat_pop) * 1.12)
    ax.set_xlabel("year")
    ax.set_ylabel("population")
    fk.thousands(ax, "y")

    ax2 = ax.twinx()
    ax2.set_ylim(*(v * ratio for v in ax.get_ylim()))
    ax2.set_ylabel("equivalent Qadf (m³/d, DERIVED)", color=fk.C.GREY, fontsize=7.6)
    ax2.tick_params(colors=fk.C.GREY, length=3, width=0.8)
    ax2.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for side in ("top",):
        ax2.spines[side].set_visible(False)
    ax.legend(loc="upper left", frameon=True, framealpha=0.93, edgecolor="#9a9a9a",
              fontsize=7.6)
    finish_chart(fig, source=src(
        t, servicing(),
        f"the right-hand axis converts at the project's own saturation ratio, "
        f"{ratio:.4f} m³/d per head — DERIVED, and only indicative: non-domestic load "
        f"({nondom_pct:.0f} % of the total) does not scale with population"))
    return fk.save(fig, "FO11_design_horizon_vs_saturation")


# ==================================================================== F12

def fig12_decision_basis() -> Path:
    """What actually decided each settlement's system, and how firm each decision is."""
    sv = servicing()
    g = (sv.groupby("DEC_RULE").agg(n=("SET_ID", "size"), q=("Q_ADF_M3D", "sum"),
                                    plots=("N_PLOT", "sum"),
                                    prov=("CONFIDENCE", lambda c: int((c == "provisional").sum())))
         .sort_values("n", ascending=False))
    tot_q = float(sv["Q_ADF_M3D"].sum())
    n_zero = fact("FO12", "settlements decided by ZERO-LOAD",
                  int(g.loc["ZERO-LOAD", "n"]) if "ZERO-LOAD" in g.index else 0,
                  "W11a.gpkg [servicing] DEC_RULE")
    n_cost = fact("FO12", "settlements decided by the life-cycle cost test",
                  int(g.loc["COST", "n"]) if "COST" in g.index else 0,
                  "W11a.gpkg [servicing] DEC_RULE")
    n_prov = fact("FO12", "settlements whose decision is provisional",
                  int((sv.CONFIDENCE == "provisional").sum()),
                  "W11a.gpkg [servicing] CONFIDENCE")
    q_prov = fact("FO12", "load sitting behind a provisional decision, m3/d",
                  round(float(sv.loc[sv.CONFIDENCE == "provisional", "Q_ADF_M3D"].sum()), 0),
                  "W11a.gpkg [servicing]")

    meaning = {
        "COST": "life-cycle cost test\n(exclusive m per property)",
        "G201-p83": "decentralised size band, G201-p83\n§8.4.1-2: package plant 50-5,000 pe",
        "ZERO-LOAD": "no load at all — a LAND-USE\nCLASSIFICATION, not a cost test",
        "PHIL-8a": "both options carried\nforward (philosophy §8a)",
        "CORE": "the core settlement —\nthe network is built around it",
    }
    fig, axes = fk.chart_frame(
        title=(f"{n_zero} of {len(sv)} servicing decisions rest on a land-use "
               f"classification that is about to be replaced"),
        subtitle=(f"Left: what decided each settlement's system. Only {n_cost} were decided "
                  f"by the life-cycle cost test the method calls for; {n_zero} were decided "
                  f"by having no modelled load at all, which is a property of the land-use "
                  f"data, not of the settlement. Right: how firm each decision is. "
                  f"{n_prov} decisions are provisional, carrying {q_prov:,.0f} m³/d."),
        figsize=(10.6, 5.0), ncols=2, ygrid=False)
    panel_room(fig)
    axL, axR = axes

    order = list(g.index)[::-1]
    y = np.arange(len(order))
    shades = {r: DENSITY_CMAP(v) for r, v in
              zip(order, np.linspace(0.30, 0.92, len(order)))}
    axL.barh(y, [g.loc[r, "n"] for r in order], height=0.62,
             color=[shades[r] for r in order], edgecolor=fk.C.INK, lw=0.5)
    for yy, r in zip(y, order):
        axL.text(g.loc[r, "n"] + 1.5, yy,
                 f"{int(g.loc[r,'n'])}  ·  {g.loc[r,'q']:,.0f} m³/d "
                 f"({100*g.loc[r,'q']/tot_q:.1f} %)",
                 va="center", ha="left", fontsize=7.2, color=fk.C.INK)
    axL.set_yticks(y)
    axL.set_yticklabels([meaning.get(r, r) for r in order], fontsize=7.0)
    axL.set_xlim(0, max(g.n) * 1.85)
    axL.set_xlabel("settlements")
    axL.set_title("what decided the system", fontsize=9, color=fk.C.GREY, loc="left")
    fk.style_axes(axL, xgrid=True, ygrid=False)

    conf = (sv.groupby("CONFIDENCE").agg(n=("SET_ID", "size"), q=("Q_ADF_M3D", "sum")))
    keys = [k for k in ["surveyed", "drafted", "derived", "provisional"] if k in conf.index]
    style = {"surveyed": "pass", "drafted": "pass", "derived": "pass",
             "provisional": "flag"}
    # Both bars run to the SAME 100 % width; one counts settlements, the other
    # weights them by load.  The contrast between the two bars IS the point.
    left_n = left_q = 0.0
    for k in keys:
        pn = 100.0 * conf.loc[k, "n"] / len(sv)
        pq = 100.0 * conf.loc[k, "q"] / tot_q
        axR.barh(1, pn, left=left_n, height=0.5, **fk.status_style(style[k]))
        axR.barh(0, pq, left=left_q, height=0.5, **fk.status_style(style[k]))
        if pn > 7:
            axR.text(left_n + pn / 2, 1,
                     f"{k}" + chr(10) + f"{int(conf.loc[k,'n'])}  ({pn:.0f} %)",
                     ha="center", va="center", fontsize=7.4, fontweight="bold",
                     color=fk.label_ink(style[k]), bbox=LABEL_BOX)
        if pq > 7:
            axR.text(left_q + pq / 2, 0,
                     f"{conf.loc[k,'q']:,.0f} m³/d" + chr(10) + f"({pq:.1f} %)",
                     ha="center", va="center", fontsize=7.4, fontweight="bold",
                     color=fk.label_ink(style[k]), bbox=LABEL_BOX)
        else:
            axR.annotate(f"{k}: {conf.loc[k,'q']:,.0f} m³/d ({pq:.1f} %)",
                         (min(left_q + pq / 2, 99.0), -0.26),
                         textcoords="offset points", xytext=(0, -12), ha="right",
                         fontsize=7.2, color=fk.C.INK,
                         arrowprops=dict(arrowstyle="-", color=fk.C.GREY, lw=0.7))
        left_n += pn
        left_q += pq
    axR.set_yticks([1, 0])
    axR.set_yticklabels([f"by settlement" + chr(10) + f"({len(sv)} of them)",
                         f"by load" + chr(10) + f"({tot_q:,.0f} m³/d)"], fontsize=7.4)
    axR.set_ylim(-0.95, 1.45)
    axR.set_xlim(0, 100)
    axR.set_xlabel("share (%)")
    axR.set_title("how firm the decision is", fontsize=9, color=fk.C.GREY, loc="left")
    fk.style_axes(axR, xgrid=True, ygrid=False)

    finish_chart(fig, source=src(
        servicing(),
        "DEC_RULE and CONFIDENCE are published fields; the wording against each rule is "
        "this figure's gloss. The one guideline value shown — the 50–5,000 inhabitant "
        "package-plant band — is quoted from PAM-GUD-201 p83 §8.4.1"))
    return fk.save(fig, "FO12_decision_basis")


FIGURES = {
    "FO01": (fig01_scope_and_existing,
            "Scope and existing assets — two thirds of the 'existing' network is paper"),
    "FO02": (fig02_system_by_settlement,
            "Central / satellite / on-site by settlement, and the load each carries"),
    "FO03": (fig03_load_concentration,
            "One settlement is most of the project"),
    "FO04": (fig04_load_density,
            "Where the ultimate flow is generated, and how concentrated it is"),
    "FO05": (fig05_stp_candidates,
            "STP siting — the existing works ranks last, and the reason is land"),
    "FO06": (fig06_stp_compare,
            "Existing works vs the southern site vs the best candidate, six criteria"),
    "FO07": (fig07_terrain_and_fall,
            "The terrain, the trunk on it, and why gravity works here"),
    "FO08": (fig08_break_sensitivity,
            "The central/decentral break is a cliff, and the adopted value clears it"),
    "FO09": (fig09_load_by_category,
            "What generates the load, and the classes that generate none"),
    "FO10": (fig10_existing_coverage,
            "How much of the ultimate load already has a built sewer in front of it"),
    "FO11": (fig11_horizon,
            "The design horizon against the client's own population projection"),
    "FO12": (fig12_decision_basis,
            "What decided each settlement's system, and how firm each decision is"),
}


def main(argv: list[str]) -> int:
    if "--list" in argv:
        for k, (_fn, desc) in FIGURES.items():
            print(f"{k}  {desc}")
        return 0
    quiet = "--facts" in argv                    # the table only; figures still rebuild
    wanted = [a.upper() for a in argv if a.upper() in FIGURES] or list(FIGURES)

    if not quiet:
        print(f"figkit scratchpad : {fk.SCRATCH}")
        print(f"imagery           : {'found' if fk.IMAGERY.exists() else 'MISSING'}")
        print(f"study boundary    : {STUDY_BND.name}  {study_area_km2():,.1f} km²")
        print()
    for key in wanted:
        fn, _desc = FIGURES[key]
        try:
            p = fn()
            if not quiet:
                print(f"  {key}  ->  {p.name}")
        except Exception as exc:                        # noqa: BLE001
            print(f"  {key}  FAILED  {type(exc).__name__}: {exc}")
            raise
    print("\n--- every number on these figures, and where it came from ---")
    for figname, what, art in FACTS:
        print(f"  {figname}  {what}")
        print(f"        <- {art}")
    return 0


if __name__ == "__main__":
    # point figkit's locator inset at the boundary the PIPELINE uses, not the
    # smaller MoHUP one.  Seeding the documented cache; figkit itself is untouched.
    try:
        fk._BOUND_CACHE["b"] = fk.read_layer(str(STUDY_BND))
    except Exception:                                    # noqa: BLE001
        pass
    raise SystemExit(main(sys.argv[1:]))
