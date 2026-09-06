"""
W12 - TERRAIN FLOW ENGINE
==========================

The module W12 turns on.  W11a laid its network out on ROAD CONNECTIVITY and used the
terrain only to check the answer; 42.5 % of its length (737.7 km) came out draining uphill
and it wanted 2,449 vortex drop shafts where NAMA's built network has 37.  This module
derives the flow direction from the GROUND FIRST, so the pipes can follow it.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
Third-party libraries (rasterio, whitebox, scipy, shapely, geopandas) are used as libraries.

NO NUMBER IS INVENTED.  Every constant below carries one of three provenance tags:

    [G203-p##]  read out of PAM-GUD-203 - Wastewater Design Guidelines v1.0
    [G201-p##]  read out of PAM-GUD-201 - General Design Guidelines v1.0
    [ASSUME]    a project assumption - stated, defended, and reported on every output
    [MEASURED]  derived here from the data, with the measurement recorded in the manifest

WHAT IT PRODUCES  (all under W12/run/terrain/)
    1  a depression-filled surface + the census of pits filled
    2  D8 flow direction at every cell
    3  flow accumulation (contributing area, m2)
    4  the stream network as vector lines, threshold calibrated against the flood grids
    5  CLOSED BASINS - where flow collects and cannot leave by gravity
    6  catchments draining to each outlet

THE API the network builder calls
    tf = TerrainFlow.load()
    tf.elevation(x, y)                 -> ground level, m aOD
    tf.downhill_bearing(x, y)          -> (bearing_deg, slope_pct) - which way is downhill
    tf.drain_direction(line)           -> which END is the outlet, the fall, a confidence
    tf.is_ridge(line)                  -> does this line straddle a divide
    tf.stream_distance(x, y)           -> m to the nearest derived stream
    tf.in_wadi(x, y, return_period=50) -> is this cell wadi ground
    tf.accumulation(x, y)              -> upstream contributing area, m2
    tf.basin_at(x, y)                  -> closed-basin id, or 0
    tf.catchment_at(x, y)              -> sub-catchment id
    tf.flow_path(x, y)                 -> the D8 path downhill from here

CLI
    python terrain.py build            run every stage, cached
    python terrain.py build --stage resample --force
    python terrain.py verify           re-run only the reality checks
    python terrain.py bench            measure the API cost
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------------------
# PATHS
# --------------------------------------------------------------------------------------

HERE = Path(__file__).resolve()
W12 = HERE.parents[2]                      # .../Hydraulic/Claude/W12
CLAUDE = W12.parent                        # .../Hydraulic/Claude
HYDRAULIC = CLAUDE.parent                   # .../Hydraulic
PROJECT = HYDRAULIC.parent                  # .../2621 Ibri Sewer STP

def _resolve_run_dir() -> Path:
    """Where the terrain products live.

    Terrain products are DERIVED FROM THE DEM, not from any design. The DEM has not
    changed since W11b built them, so the grids are byte-identical whichever iteration
    computes them - and they cost HOURS and ~25 GB. Hard-coding them inside one
    iteration folder is the "start from scratch" problem in data form: it makes every
    new W# pay again for a product that did not change.

    Order:
      1. $IBRI_TERRAIN_RUN            an explicit override, wins outright
      2. W12/run/terrain              this iteration's own, if the set is COMPLETE
      3. the newest sibling W*/run/terrain holding a COMPLETE set - BORROWED, and it
         says so on stderr every time, with the path. Never silent (philosophy sec 8).
      4. W12/run/terrain              so a build writes here, not into a superseded folder

    A PARTIAL set never wins. Half-built grids are how a run reads one product from one
    iteration and its neighbour from another.
    """
    import os, sys
    env = os.environ.get("IBRI_TERRAIN_RUN", "").strip()
    if env:
        return Path(env)

    own = W12 / "run" / "terrain"
    must = ("R5_d8.tif", "R5_acc.tif", "R5_dem.tif")

    def complete(d: Path) -> bool:
        return d.is_dir() and all((d / m).exists() for m in must)

    if complete(own):
        return own

    sibs = sorted((c / "run" / "terrain" for c in CLAUDE.glob("W*")
                   if c.is_dir() and c != W12),
                  key=lambda d: (d / "R5_d8.tif").stat().st_mtime if (d / "R5_d8.tif").exists() else 0,
                  reverse=True)
    for d in sibs:
            print("", file=sys.stderr)
            for _m in (
                f"[terrain] BORROWING terrain products from {d}",
                "[terrain] they derive from the DEM, not from a design, and the DEM has",
                "[terrain] not changed - rebuilding costs hours and ~25 GB.",
                "[terrain] Set IBRI_TERRAIN_RUN to override, or run",
                "[terrain]   python -m w12.terrain build --grid R5   to own them.",
            ):
                print(_m, file=sys.stderr)
            return d
    return own


RUN = _resolve_run_dir()

# INPUTS -------------------------------------------------------------------------------
# Rule 6 of Hydraulic/Claude/CLAUDE.md: this VRT is the authoritative elevation source.
DEM_VRT = PROJECT / "Data" / "Terrain" / "Sat_0p5m" / "IBRI_0p5_VRT2.vrt"

FLOOD_DIR = PROJECT / "Data" / "04 Lekhuwair"
FLOOD_GRIDS = {                              # return period (years) -> hazard-class raster
    10: FLOOD_DIR / "Hazard_T10y.tif",
    25: FLOOD_DIR / "Hazard_T25y.tif",
    50: FLOOD_DIR / "Hazard_T50y.tif",
    100: FLOOD_DIR / "Hazard_T100y.tif",
    500: FLOOD_DIR / "Hazard_T500y.tif",
}

BOUNDARY_MOHUP = HYDRAULIC / "SHP" / "MoHUP_DATA" / "Project_boundary.shp"      # 439.8 km2
BOUNDARY_STUDY = HYDRAULIC / "SHP" / "Study area" / "Project Boundary.shp"      # 531.4 km2

# Independent answers to the same question, used only to CHECK ours.
NAMA_SEWER = (PROJECT / "Data" / "Received" / "09-RECEIVED" / "NAMA" / "IBRI" / "WW"
              / "SHIP" / "SEWERLINE_IBRI.shp")
NSA_STREAMS = HYDRAULIC / "SHP" / "Streams" / "Streams NSA 2m project boundary.shp"
MAIN_PIPE = HYDRAULIC / "SHP" / "Main Pipe" / "Main Pipe.shp"

CRS = "EPSG:32640"


# --------------------------------------------------------------------------------------
# CONSTANTS - every one tagged
# --------------------------------------------------------------------------------------

# ---- working resolution ---------------------------------------------------------------
# [ASSUME] 5 m regional / 2 m local.
#   The source is 0.5 m over a 75.7 x 74.2 km footprint = 2.25e10 cells.  That cannot be
#   routed.  Two nested grids are built instead:
#     R5  5 m over the WHOLE DEM footprint, so the contributing area of every wadi that
#         enters the study area from outside is real and not truncated at the boundary.
#     L2  2 m over the study boundary + a 2 km buffer, for the detail the corridors need,
#         with R5's accumulation injected at its edge so its streams are not starved.
#   The accuracy cost is MEASURED, not asserted - see verify_resolution_cost() and the
#   `resolution_cost` block of the manifest, which re-derives the fall and the drain
#   direction of real corridor-length lines at 0.5 m and reports the disagreement.
#   Context, not authority: G201-p36 Tab 5 asks for 0.05-0.5 m VERTICAL accuracy at
#   concept stage.  Resolution is not accuracy, but a 5 m cell cannot express a 0.05 m
#   feature, which is why point elevations are always taken from the native 0.5 m VRT.
RES_REGIONAL_M = 5.0        # [ASSUME]
RES_LOCAL_M = 2.0           # [ASSUME]
LOCAL_BUFFER_M = 2000.0     # [ASSUME] margin so the local grid's edge is not in the design area

# ---- depression handling ---------------------------------------------------------------
# [ASSUME] A bare-earth DEM shows a road embankment as an unbroken dam; the culvert under
#   it is invisible.  Filling drowns the whole upstream area and invents a lake.  Breaching
#   carves the notch the culvert already is.  So: breach with a MODEST reach first - only
#   as far as a real embankment is wide - and whatever is STILL a depression afterwards is
#   a candidate REAL basin rather than a DEM artefact.
BREACH_DIST_M = 100.0       # [ASSUME] plausible width of an embankment/berm blockage
BREACH_MAX_COST = None      # [ASSUME] no cost ceiling; the distance limit does the work

# ---- what counts as a real closed basin -------------------------------------------------
# [MEASURED at build time] the depth floor is set to 3x the DEM's own measured vertical
#   disagreement (0.5 m source vs 5 m source, and DEM vs NAMA's recorded ground levels),
#   so a "basin" can never be an artefact of the surface's own noise.  The fallback below
#   is used only if the measurement cannot be made.
BASIN_MIN_DEPTH_FALLBACK_M = 0.50   # [ASSUME] fallback only
BASIN_MIN_AREA_M2 = 2500.0          # [ASSUME] 100 cells at 5 m; below this it is noise

# ---- the cover cap that turns a basin into a pumping station ----------------------------
# G203-p33 4.6.3: "The recommended maximum cover for sewer pipes is approximately 10 - 12m.
#   ... Where the cost of excavation becomes prohibitive the Engineer shall incorporate
#   pumping stations into the design."
COVER_CAP_M = 12.0          # [G203-p33] upper end of the recommended maximum cover
MIN_COVER_M = 1.30          # [G203-p33] "minimum depth for sewer pipes shall be 1.3 m to
                            #            the crown of the pipe"

# ---- wadi ground -------------------------------------------------------------------------
# G203-p30 4.4.1 i.a: "Wadis and Flood-Prone Areas: Locating pipelines and associated
#   chambers in wadis or areas subject to washout during heavy storms must be avoided."
# G203-p33 4.6.2 repeats it with "shall be avoided".
# The guideline gives no test for what IS a wadi.  _BRAIN/02_DESIGN_CRITERIA.md 6 already
# fixes the project's stand-in and labels it an assumption; it is reused unchanged here.
HAZARD_WADI_CLASSES = (4, 5, 6)   # [ASSUME] AR&R flood-hazard classes standing in for
                                  #          the guideline's washout/scour criterion
WADI_RETURN_PERIOD_DEFAULT = 50   # [ASSUME] the 50-year grid is the project's wadi test
# Engineer's decision 2026-09-03: flood-grid NO-DATA is DRY HIGH GROUND, not "untested".
FLOOD_NODATA_IS_DRY = True        # [ASSUME - engineer, 2026-09-03]

# ---- stream threshold ---------------------------------------------------------------------
# [MEASURED] chosen by calibration against the 50-year hazard grid - see calibrate_streams().
# The sweep below is the search space, not the answer.
STREAM_THRESHOLD_SWEEP_M2 = [1e4, 1.5e4, 2e4, 3e4, 4e4, 5e4, 7.5e4, 1e5, 2e5, 5e5,
                             1e6, 2e6, 5e6, 1e7]
# [ASSUME] the network must know about at least 90 % of the wadis the independent flood
#   model knows about.  Missing one is a washout risk (G203-p30 4.4.1); an extra one only
#   costs a detour.  The matching TOLERANCE is not assumed - it is measured from the
#   hazard extent's own width, see calibrate_streams().
STREAM_MIN_RECALL = 0.90

# ---- direction / bearing --------------------------------------------------------------------
# [ASSUME] D8's direction is quantised to 45 deg.  On ground falling 0.1 % that error is
#   unacceptable for orienting a corridor, so BEARING is never taken from D8: it comes from
#   a least-squares plane fit over a radius.  D8 is used only where a single-outlet TREE is
#   what is wanted - routing, accumulation, streams, catchments - which is exactly what a
#   sewer is.
BEARING_RADIUS_M = 50.0     # [ASSUME] a plane fit over ~1 corridor reach, not a cell pair
PROFILE_STEP_M = 5.0        # [ASSUME] chainage step when sampling a line's profile

# ---- confidence in a line's drain direction ---------------------------------------------------
# [MEASURED at build time] sigma_z is the DEM's measured vertical noise; the fall over a
#   line must beat it by this factor before the direction is called CERTAIN.
CONF_CERTAIN_SIGMA = 3.0    # [ASSUME]
CONF_LIKELY_SIGMA = 1.0     # [ASSUME]

# ---- ridge test -------------------------------------------------------------------------------
RIDGE_MIN_PROMINENCE_M = 0.50   # [ASSUME] re-set at build time to 3 x measured sigma_z
RIDGE_INTERIOR_FRAC = 0.15      # [ASSUME] crest must sit inside the middle 70 % of the line

# ---- WBT D8 pointer decode ----------------------------------------------------------------------
# [MEASURED 2026-09-03] on a synthetic 3x3 pyramid; NOT taken from memory or documentation.
#        64 128   1
#        32   X   2
#        16   8   4
D8_DECODE = {              # pointer value -> (drow, dcol)
    1: (-1, 1), 2: (0, 1), 4: (1, 1), 8: (1, 0),
    16: (1, -1), 32: (0, -1), 64: (-1, -1), 128: (-1, 0),
}


# --------------------------------------------------------------------------------------
# GRID SPEC
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class GridSpec:
    name: str
    res: float
    left: float
    bottom: float
    right: float
    top: float

    @property
    def width(self) -> int:
        return int(round((self.right - self.left) / self.res))

    @property
    def height(self) -> int:
        return int(round((self.top - self.bottom) / self.res))

    @property
    def cells(self) -> int:
        return self.width * self.height

    @property
    def cell_area(self) -> float:
        return self.res * self.res

    def transform(self):
        from rasterio.transform import from_origin
        return from_origin(self.left, self.top, self.res, self.res)

    def profile(self, dtype="float32", nodata=-9999.0):
        return dict(driver="GTiff", height=self.height, width=self.width, count=1,
                    dtype=dtype, crs=CRS, transform=self.transform(), nodata=nodata,
                    tiled=True, blockxsize=512, blockysize=512,
                    compress="deflate", zlevel=1, BIGTIFF="YES", num_threads="ALL_CPUS")


def _snap(v: float, res: float, up: bool) -> float:
    return (math.ceil(v / res) if up else math.floor(v / res)) * res


def regional_spec() -> GridSpec:
    import rasterio
    with rasterio.open(DEM_VRT) as s:
        b = s.bounds
    r = RES_REGIONAL_M
    return GridSpec("R5", r, _snap(b.left, r, False), _snap(b.bottom, r, False),
                    _snap(b.right, r, True), _snap(b.top, r, True))


def local_spec() -> GridSpec:
    import geopandas as gpd
    xs, ys = [], []
    for p in (BOUNDARY_MOHUP, BOUNDARY_STUDY):
        if p.exists():
            b = gpd.read_file(p).to_crs(CRS).total_bounds
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
    r = RES_LOCAL_M
    bf = LOCAL_BUFFER_M
    reg = regional_spec()
    left = max(_snap(min(xs) - bf, r, False), reg.left)
    bottom = max(_snap(min(ys) - bf, r, False), reg.bottom)
    right = min(_snap(max(xs) + bf, r, True), reg.right)
    top = min(_snap(max(ys) + bf, r, True), reg.top)
    return GridSpec("L2", r, left, bottom, right, top)


# --------------------------------------------------------------------------------------
# MANIFEST - every parameter, every measured number, with provenance
# --------------------------------------------------------------------------------------

MANIFEST = RUN / "terrain_manifest.json"


def manifest_read() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def manifest_write(**kw):
    m = manifest_read()
    m.update(kw)
    m["_written"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=2, default=str), encoding="utf-8")
    return m


def _log(msg: str):
    print(f"[terrain {time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------------------------------
# STAGE 1 - RESAMPLE: build the working surface from the 0.5 m VRT
# --------------------------------------------------------------------------------------
# Aggregation is by MEAN of the valid 0.5 m cells in each window, done here rather than
# handed to GDAL so that -9999 can never leak into an average.  A window with no valid
# source cell stays nodata.

def _agg_tile(args):
    import rasterio
    from rasterio.windows import Window
    (vrt_path, dst_left, dst_top, res, r0, c0, nrows, ncols) = args
    with rasterio.open(vrt_path) as s:
        sres = s.res[0]
        f = int(round(res / sres))                       # native cells per working cell
        x0 = dst_left + c0 * res
        y0 = dst_top - r0 * res
        col_off = int(round((x0 - s.bounds.left) / sres))
        row_off = int(round((s.bounds.top - y0) / sres))
        w = Window(col_off, row_off, ncols * f, nrows * f)
        a = s.read(1, window=w, boundless=True, fill_value=-9999.0).astype("float32")
    a[a <= -9990.0] = np.nan
    a = a.reshape(nrows, f, ncols, f)
    import warnings
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # all-nodata windows are expected
        out = np.nanmean(a, axis=(1, 3), dtype="float32")
    out = np.where(np.isnan(out), -9999.0, out).astype("float32")
    return r0, c0, out


def stage_resample(spec: GridSpec, force=False) -> Path:
    import rasterio
    from concurrent.futures import ProcessPoolExecutor
    out = RUN / f"{spec.name}_dem.tif"
    if out.exists() and not force:
        _log(f"resample {spec.name}: cached")
        return out
    RUN.mkdir(parents=True, exist_ok=True)
    _log(f"resample {spec.name}: {spec.width} x {spec.height} = {spec.cells/1e6:.1f} M "
         f"cells at {spec.res} m")
    tile = 1024
    jobs = []
    for r0 in range(0, spec.height, tile):
        for c0 in range(0, spec.width, tile):
            jobs.append((str(DEM_VRT), spec.left, spec.top, spec.res, r0, c0,
                         min(tile, spec.height - r0), min(tile, spec.width - c0)))
    t = time.time()
    with rasterio.open(out, "w", **spec.profile()) as dst:
        with ProcessPoolExecutor(max_workers=min(12, os.cpu_count() or 4)) as ex:
            for i, (r0, c0, arr) in enumerate(ex.map(_agg_tile, jobs, chunksize=1)):
                from rasterio.windows import Window
                dst.write(arr, 1, window=Window(c0, r0, arr.shape[1], arr.shape[0]))
                if (i + 1) % 50 == 0 or i + 1 == len(jobs):
                    _log(f"  {i+1}/{len(jobs)} tiles  {time.time()-t:.0f} s")
    _log(f"resample {spec.name}: {time.time()-t:.0f} s -> {out.name}")
    return out


# --------------------------------------------------------------------------------------
# WHITEBOX HELPERS
# --------------------------------------------------------------------------------------

def _wbt():
    import whitebox
    w = whitebox.WhiteboxTools()
    w.set_working_dir(str(RUN))
    w.set_verbose_mode(False)
    w.set_compress_rasters(True)
    return w


def _rd(path, masked=False):
    """Read a raster into memory."""
    import rasterio
    with rasterio.open(path) as s:
        a = s.read(1)
        nd = s.nodata
    if masked and nd is not None:
        a = np.where(a == nd, np.nan, a)
    return a


def _wr(path, arr, spec: GridSpec, dtype=None, nodata=-9999.0):
    import rasterio
    dtype = dtype or arr.dtype.name
    p = spec.profile(dtype=dtype, nodata=nodata)
    with rasterio.open(path, "w", **p) as o:
        o.write(arr.astype(dtype), 1)
    return path


# --------------------------------------------------------------------------------------
# STAGE 2 - CONDITION: pits, breaching, filling
# --------------------------------------------------------------------------------------

def stage_condition(spec: GridSpec, force=False) -> dict:
    """
    Three surfaces, in this order, because the ORDER is what separates a real basin from
    a DEM artefact:

      dem            the aggregated ground
      dem_fillplain  every depression drowned.  (dem_fillplain - dem) is the FULL depression
                     depth map: the census of every pit, real or not.
      dem_breach     depressions carved out where a carve of <= BREACH_DIST_M resolves them.
                     A depression that DISAPPEARS here was a blocked culvert / embankment -
                     an ARTEFACT of a bare-earth surface that cannot see a pipe under a road.
      dem_cond       dem_breach with the survivors filled, so D8 is defined everywhere.
                     A depression that SURVIVES the breach is a CANDIDATE REAL BASIN.
    """
    dem = RUN / f"{spec.name}_dem.tif"
    fillplain = RUN / f"{spec.name}_dem_fillplain.tif"
    breach = RUN / f"{spec.name}_dem_breach.tif"
    cond = RUN / f"{spec.name}_dem_cond.tif"
    if cond.exists() and not force:
        _log(f"condition {spec.name}: cached")
        return dict(dem=dem, fillplain=fillplain, breach=breach, cond=cond)

    w = _wbt()
    t = time.time()
    _log(f"condition {spec.name}: fill_depressions (census pass)")
    w.fill_depressions(dem.name, fillplain.name, fix_flats=True)
    _log(f"  {time.time()-t:.0f} s")

    t = time.time()
    dist_cells = int(round(BREACH_DIST_M / spec.res))
    _log(f"condition {spec.name}: breach_depressions_least_cost dist={dist_cells} cells "
         f"({BREACH_DIST_M:.0f} m)")
    w.breach_depressions_least_cost(dem.name, breach.name, dist=dist_cells,
                                    max_cost=BREACH_MAX_COST, min_dist=True, fill=False)
    _log(f"  {time.time()-t:.0f} s")

    t = time.time()
    _log(f"condition {spec.name}: fill the survivors -> routing surface")
    w.fill_depressions(breach.name, cond.name, fix_flats=True)
    _log(f"  {time.time()-t:.0f} s")
    return dict(dem=dem, fillplain=fillplain, breach=breach, cond=cond)


# --------------------------------------------------------------------------------------
# STAGE 3 - FLOW DIRECTION (D8) and STAGE 4 - ACCUMULATION
# --------------------------------------------------------------------------------------

def stage_flow(spec: GridSpec, force=False) -> dict:
    """
    D8, and why.

    D8 sends every cell's water to exactly ONE neighbour.  That is physically cruder than
    D-infinity, which splits flow between the two neighbours bracketing the aspect: on a
    planar hillslope D8's path zig-zags and can be biased by up to 22.5 deg.

    It is nevertheless the right primitive HERE, for one reason: a sewer is a TREE.  Every
    chamber has exactly one outgoing pipe and the network must resolve to one outfall per
    component.  A D-infinity field is not a tree and cannot be turned into one without
    throwing the dispersion away again.

    The 45 deg quantisation is not allowed to reach the design: BEARING comes from a plane
    fit (downhill_bearing), never from the pointer.  D-infinity accumulation is computed
    anyway, purely as an independent check on where the streams come out.
    """
    cond = RUN / f"{spec.name}_dem_cond.tif"
    d8 = RUN / f"{spec.name}_d8.tif"
    acc = RUN / f"{spec.name}_acc.tif"
    dinf = RUN / f"{spec.name}_dinf_acc.tif"
    if acc.exists() and not force:
        _log(f"flow {spec.name}: cached")
        return dict(d8=d8, acc=acc, dinf=dinf)
    w = _wbt()
    t = time.time()
    _log(f"flow {spec.name}: d8_pointer")
    w.d8_pointer(cond.name, d8.name)
    _log(f"  {time.time()-t:.0f} s")
    t = time.time()
    _log(f"flow {spec.name}: d8_flow_accumulation (catchment area, m2)")
    w.d8_flow_accumulation(cond.name, acc.name, out_type="catchment area")
    _log(f"  {time.time()-t:.0f} s")
    t = time.time()
    _log(f"flow {spec.name}: d_inf_flow_accumulation (cross-check)")
    try:
        w.d_inf_flow_accumulation(cond.name, dinf.name, out_type="Catchment Area")
        _log(f"  {time.time()-t:.0f} s")
    except Exception as e:                                   # pragma: no cover
        _log(f"  D-infinity cross-check unavailable: {e}")
    return dict(d8=d8, acc=acc, dinf=dinf)


# --------------------------------------------------------------------------------------
# STAGE 5 - STREAMS, with the threshold CALIBRATED not chosen
# --------------------------------------------------------------------------------------

def _flood_on_grid(spec: GridSpec, rp: int, force=False) -> Path:
    """
    Put one hazard-class grid on the working grid.

    Resampled by MAXIMUM: if any part of a working cell is class 5, the cell is class 5.
    A prohibition (G203-p30 4.4.1) must not be averaged away.

    NO-DATA becomes 0 = dry high ground, per the engineer's decision of 2026-09-03.  That
    is a real assumption with a real consequence and it is flagged on every output: 47 % of
    the study area lies outside the hazard grids, so "not wadi" there means "not shown to
    be wadi", and NWS still owe full-coverage 50-year mapping.
    """
    import rasterio
    from rasterio.vrt import WarpedVRT
    from rasterio.enums import Resampling
    from rasterio.windows import Window
    out = RUN / f"{spec.name}_hazard_T{rp}.tif"
    if out.exists() and not force:
        return out
    src_path = FLOOD_GRIDS[rp]
    _log(f"flood {spec.name} T{rp}: warp to grid (max)")
    prof = spec.profile(dtype="uint8", nodata=0)
    with rasterio.open(src_path) as s:
        with WarpedVRT(s, crs=CRS, transform=spec.transform(), width=spec.width,
                       height=spec.height, resampling=Resampling.max,
                       src_nodata=s.nodata, nodata=0) as vrt:
            with rasterio.open(out, "w", **prof) as dst:
                blk = 4096
                for r0 in range(0, spec.height, blk):
                    h = min(blk, spec.height - r0)
                    a = vrt.read(1, window=Window(0, r0, spec.width, h))
                    a = np.where(np.isfinite(a) & (a > 0), a, 0)
                    dst.write(np.clip(a, 0, 255).astype("uint8"), 1,
                              window=Window(0, r0, spec.width, h))
    return out


def _study_window(spec: GridSpec, buffer_m: float = 2000.0):
    """Row/col slices covering the study boundaries + a buffer, clipped to the grid.

    Calibration and the reality checks are done HERE, not over the whole regional
    footprint: the regional grid exists so that inflow from outside is real, but a
    threshold calibrated over 5,600 km2 of empty desert and mountain would not be the
    threshold the design area needs.
    """
    import geopandas as gpd
    xs, ys = [], []
    for p in (BOUNDARY_MOHUP, BOUNDARY_STUDY):
        if p.exists():
            b = gpd.read_file(p).to_crs(CRS).total_bounds
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
    if not xs:
        return (slice(None), slice(None))
    c0 = max(0, int((min(xs) - buffer_m - spec.left) / spec.res))
    c1 = min(spec.width, int((max(xs) + buffer_m - spec.left) / spec.res))
    r0 = max(0, int((spec.top - (max(ys) + buffer_m)) / spec.res))
    r1 = min(spec.height, int((spec.top - (min(ys) - buffer_m)) / spec.res))
    return (slice(r0, r1), slice(c0, c1))


def _wadi_mask(spec: GridSpec, rp: int) -> np.ndarray:
    h = _rd(_flood_on_grid(spec, rp))
    return np.isin(h, HAZARD_WADI_CLASSES)


def calibrate_streams(spec: GridSpec) -> dict:
    """
    What IS a wadi on this ground?

    Not a number picked off a textbook, and not F1 either - F1 was tried first and it is
    the wrong measure here.  Matching a 1-D line network against a 2-D inundation extent
    makes recall trivially satisfiable by densifying the network, so F1 ran to the bottom
    of the sweep and picked 1 ha, which is a hillslope rill, not a wadi.

    What is done instead, in three measured steps:

      1  MEASURE HOW WIDE A WADI IS.  The 50-year hazard class 4-6 extent is distance-
         transformed; the 75th percentile half-width is the matching tolerance.  On this
         ground that is ~100 m - a braided wadi bed - so requiring the derived thalweg to
         sit within 25 m of the flood model's centreline was never reasonable.
      2  REDUCE THE EXTENT TO A LINE.  The wadi mask is skeletonised, so line is compared
         with line and precision genuinely penalises extra channels.
      3  TAKE THE SPARSEST NETWORK THAT STILL KNOWS EVERY WADI.  The threshold chosen is
         the COARSEST one that still recovers >= 90 % of that skeleton within the measured
         tolerance.  Sparsest is the right side to err on: every surplus rill becomes a
         false prohibition under G203-p30 4.4.1 and a false constraint on the layout.

    Precision is reported but is NOT optimised, and the reason is physical: hazard class
    4-6 is a danger-to-life classification, so a real channel carrying class 1-3 water is
    counted against us though it is a perfectly real channel.  Strahler order is published
    on every link instead, so a later stage separates major wadi from minor channel by a
    property of the network rather than by a second arbitrary threshold.
    """
    import warnings
    from scipy import ndimage
    from skimage.morphology import skeletonize, remove_small_objects
    sl = _study_window(spec)               # calibrate where the design actually is
    acc = _rd(RUN / f"{spec.name}_acc.tif", masked=True)[sl]
    haz = _rd(_flood_on_grid(spec, WADI_RETURN_PERIOD_DEFAULT))[sl]
    covered = haz > 0                      # the hazard model said something here
    wadi = np.isin(haz, HAZARD_WADI_CLASSES)
    if not wadi.any():
        return dict(threshold_m2=None, note="no wadi-class cells on this grid")

    # 1 - how wide is a wadi?
    d_in = ndimage.distance_transform_edt(wadi, sampling=spec.res)
    half_width = dict(
        median_m=float(np.median(d_in[wadi])),
        p75_m=float(np.percentile(d_in[wadi], 75)),
        p95_m=float(np.percentile(d_in[wadi], 95)),
        max_m=float(d_in[wadi].max()))
    tol = float(max(spec.res * 2, round(half_width["p75_m"] / 25.0) * 25.0))
    del d_in

    # 2 - extent -> line
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w2 = remove_small_objects(wadi, min_size=int(BASIN_MIN_AREA_M2 / spec.cell_area))
    sk = skeletonize(w2)
    d_sk = ndimage.distance_transform_edt(~sk, sampling=spec.res)
    _log(f"  wadi half-width median {half_width['median_m']:.0f} m, p75 "
         f"{half_width['p75_m']:.0f} m -> tolerance {tol:.0f} m; "
         f"hazard skeleton {sk.sum()*spec.res/1000:.0f} km")

    # 3 - sweep
    rows = []
    for thr in STREAM_THRESHOLD_SWEEP_M2:
        st = np.isfinite(acc) & (acc >= thr)
        n_st = int(st.sum())
        if n_st == 0:
            continue
        d_st = ndimage.distance_transform_edt(~st, sampling=spec.res)
        rec = float((d_st[sk] <= tol).mean())
        judged = st & covered
        prec = float((d_sk[judged] <= tol).mean()) if judged.any() else float("nan")
        f1 = 0.0 if not np.isfinite(prec) or (prec + rec) == 0 else 2 * prec * rec / (prec + rec)
        rows.append(dict(threshold_m2=float(thr), threshold_ha=float(thr / 1e4),
                         stream_cells=n_st, stream_km=round(n_st * spec.res / 1000.0, 0),
                         recall_of_hazard_skeleton=round(rec, 4),
                         precision_vs_hazard_skeleton=round(prec, 4), f1=round(f1, 4)))
        _log(f"  thr {thr:>10.0f} m2 ({thr/1e4:5.1f} ha)  "
             f"{n_st*spec.res/1000:7.0f} km  R {rec:.3f}  P {prec:.3f}")
    ok = [r for r in rows if r["recall_of_hazard_skeleton"] >= STREAM_MIN_RECALL]
    best = max(ok, key=lambda r: r["threshold_m2"]) if ok else max(
        rows, key=lambda r: r["recall_of_hazard_skeleton"])
    return dict(threshold_m2=best["threshold_m2"], sweep=rows, chosen=best,
                tolerance_m=tol, wadi_half_width=half_width,
                hazard_skeleton_km=round(float(sk.sum()) * spec.res / 1000.0, 1),
                min_recall=STREAM_MIN_RECALL,
                basis=f"coarsest contributing-area threshold recovering >= "
                      f"{STREAM_MIN_RECALL:.0%} of the {WADI_RETURN_PERIOD_DEFAULT}-year "
                      f"AR&R hazard class {HAZARD_WADI_CLASSES} skeleton within {tol:.0f} m "
                      f"(= the measured p75 wadi half-width)",
                tag="MEASURED")


def stage_streams(spec: GridSpec, force=False) -> dict:
    import rasterio
    streams_r = RUN / f"{spec.name}_streams.tif"
    streams_v = RUN / f"{spec.name}_streams.shp"
    strdist = RUN / f"{spec.name}_stream_dist.tif"
    order_r = RUN / f"{spec.name}_stream_order.tif"
    if strdist.exists() and not force:
        _log(f"streams {spec.name}: cached")
        return dict(raster=streams_r, vector=streams_v, dist=strdist, order=order_r)

    _log(f"streams {spec.name}: calibrating threshold against the 50-year hazard grid")
    cal = calibrate_streams(spec)
    thr = cal["threshold_m2"] or 5e4
    _log(f"streams {spec.name}: threshold {thr:.0f} m2 "
         f"({thr/1e4:.1f} ha)  F1={cal.get('chosen',{}).get('f1')}")
    manifest_write(**{f"stream_calibration_{spec.name}": cal})

    w = _wbt()
    w.extract_streams(f"{spec.name}_acc.tif", streams_r.name, threshold=thr,
                      zero_background=False)
    # Strahler order, then vectorise THE ORDER RASTER - WBT carries the raster's value
    # through to the vector as STRM_VAL, so each link arrives already labelled with its
    # order and no second threshold is ever needed to tell a wadi from a rill.
    ordered = False
    try:
        w.strahler_stream_order(f"{spec.name}_d8.tif", streams_r.name, order_r.name,
                                zero_background=False)
        ordered = order_r.exists()
    except Exception as e:                                        # pragma: no cover
        _log(f"  stream order unavailable: {e}")
    _log(f"streams {spec.name}: vectorising")
    w.raster_streams_to_vector(order_r.name if ordered else streams_r.name,
                               f"{spec.name}_d8.tif", streams_v.name)

    # WBT writes the vector without a CRS - stamp it, and carry accumulation on.
    import geopandas as gpd
    g = gpd.read_file(streams_v)
    g = g.set_crs(CRS, allow_override=True)
    if "STRM_VAL" in g.columns:
        g = g.rename(columns={"STRM_VAL": "ORDER" if ordered else "STRM_VAL"})
    with rasterio.open(RUN / f"{spec.name}_acc.tif") as s:
        acc = s.read(1)
        tr = s.transform

    def _peak_acc(geom):
        try:
            xs, ys = geom.coords.xy
        except Exception:
            return np.nan
        best = -1.0
        for x, y in zip(xs, ys):
            c = int((x - tr.c) / tr.a)
            r = int((tr.f - y) / (-tr.e))
            if 0 <= r < acc.shape[0] and 0 <= c < acc.shape[1]:
                v = acc[r, c]
                if np.isfinite(v):
                    best = max(best, float(v))
        return best if best >= 0 else np.nan

    g["ACC_M2"] = [_peak_acc(gm) for gm in g.geometry]
    g["LEN_M"] = g.length
    g["THRESH_M2"] = thr
    g["TAU_FLAG"] = "tau=1.0 Pa assumed (GAP-9)"
    g["WADI_SRC"] = ("G203-p30 4.4.1 prohibits pipelines/chambers in wadis; the CLASS "
                     "test is a project assumption")
    g["SRC"] = f"W12 terrain {spec.name} D8 {spec.res:.1f} m"
    del acc
    g.to_file(RUN / f"{spec.name}_streams.gpkg", layer="streams", driver="GPKG")
    if "ORDER" in g.columns:
        byo = g.groupby("ORDER")["LEN_M"].agg(["count", "sum"])
        for o, row in byo.iterrows():
            _log(f"    order {int(o)}: {int(row['count']):>7,} links "
                 f"{row['sum']/1000:>8.0f} km")
    _log(f"streams {spec.name}: {len(g)} links, {g.length.sum()/1000:.0f} km")

    _log(f"streams {spec.name}: euclidean distance to stream")
    from scipy import ndimage
    st = _rd(streams_r)
    stm = np.isfinite(st) & (st > 0)
    d = ndimage.distance_transform_edt(~stm, sampling=spec.res)
    _wr(strdist, np.clip(d, 0, 65535), spec, dtype="uint16", nodata=65535)
    del d, st, stm
    return dict(raster=streams_r, vector=streams_v, dist=strdist, order=order_r,
                calibration=cal)


# --------------------------------------------------------------------------------------
# STAGE 6 - CLOSED BASINS: where gravity cannot get out
# --------------------------------------------------------------------------------------

def stage_basins(spec: GridSpec, sigma_dz: float | None = None, force=False) -> dict:
    """
    The single most valuable thing this module does.

    A closed basin is a place where flow collects and CANNOT leave by gravity.  It is where
    a pumping station is unavoidable - not chosen, unavoidable - and G203-p33 4.6.3 says so
    in as many words: "Where the cost of excavation becomes prohibitive the Engineer shall
    incorporate pumping stations into the design."

    A DEM is full of pits that are not basins.  The separation used here is causal, not a
    threshold on depth alone:

      ARTEFACT   the pit disappears once a carve of <= 100 m is allowed.  That is a road
                 embankment, a berm or a bund with a culvert the bare-earth surface cannot
                 see.  Reported, and NOT a pumping station.
      REAL       the pit survives a 100 m carve, is deeper than 3 x the DEM's own measured
                 vertical noise, and covers more than 2500 m2.  Reported with its spill
                 point, spill elevation, depth, area, volume and contributing area.
      FORCED     a REAL basin whose depth exceeds the 12 m cover cap [G203-p33].  No route
                 out of it can be dug within the recommended maximum cover, so gravity is
                 impossible regardless of alignment.  These are the unavoidable stations.
    """
    from scipy import ndimage
    import geopandas as gpd
    from shapely.geometry import Point, shape

    out_gpkg = RUN / f"{spec.name}_basins.gpkg"
    lab_tif = RUN / f"{spec.name}_basin_id.tif"
    if out_gpkg.exists() and not force:
        _log(f"basins {spec.name}: cached")
        return dict(gpkg=out_gpkg, labels=lab_tif)

    dem = _rd(RUN / f"{spec.name}_dem.tif", masked=True)
    fill = _rd(RUN / f"{spec.name}_dem_fillplain.tif", masked=True)
    breach = _rd(RUN / f"{spec.name}_dem_breach.tif", masked=True)
    cond = _rd(RUN / f"{spec.name}_dem_cond.tif", masked=True)

    # The floor is 3 x the DIFFERENTIAL vertical error, not the absolute one.  A pit is
    # defined by a cell against its neighbours tens of metres away, so the datum offset
    # cancels exactly as it does for a gradient.  Measured: 0.45 m differential against
    # 0.76 m absolute - the absolute figure would have suppressed real basins.
    sz = sigma_dz if sigma_dz and np.isfinite(sigma_dz) else BASIN_MIN_DEPTH_FALLBACK_M / 3.0
    min_depth = max(3.0 * sz, BASIN_MIN_DEPTH_FALLBACK_M)

    # every depression the raw DEM has
    dep_all = np.where(np.isfinite(fill) & np.isfinite(dem), fill - dem, 0.0)
    dep_all[~np.isfinite(dep_all)] = 0.0
    all_mask = dep_all > 1e-3
    # the ones that survive a 100 m carve
    dep_surv = np.where(np.isfinite(cond) & np.isfinite(breach), cond - breach, 0.0)
    dep_surv[~np.isfinite(dep_surv)] = 0.0
    surv_mask = dep_surv > 1e-3

    n_all_cells = int(all_mask.sum())
    n_surv_cells = int(surv_mask.sum())
    lab_all, n_all = ndimage.label(all_mask)
    lab_s, n_s = ndimage.label(surv_mask)
    _log(f"basins {spec.name}: {n_all} depressions in the raw DEM "
         f"({n_all_cells*spec.cell_area/1e6:.2f} km2); {n_s} survive a "
         f"{BREACH_DIST_M:.0f} m carve ({n_surv_cells*spec.cell_area/1e6:.2f} km2)")

    idx = np.arange(1, n_s + 1)
    if n_s == 0:
        gpd.GeoDataFrame(geometry=[], crs=CRS).to_file(out_gpkg, layer="closed_basins",
                                                       driver="GPKG")
        return dict(gpkg=out_gpkg, labels=lab_tif, n_real=0)

    depth = ndimage.maximum(dep_surv, lab_s, idx)
    cells = ndimage.sum(np.ones_like(dep_surv, dtype="float32"), lab_s, idx)
    volume = ndimage.sum(dep_surv, lab_s, idx) * spec.cell_area
    spill_z = ndimage.maximum(np.where(surv_mask, cond, np.nan), lab_s, idx)
    low_z = ndimage.minimum(np.where(surv_mask, breach, np.nan), lab_s, idx)
    pos = ndimage.minimum_position(np.where(surv_mask, breach, np.inf), lab_s, idx)

    acc = _rd(RUN / f"{spec.name}_acc.tif", masked=True)
    contrib = ndimage.maximum(np.where(surv_mask, acc, np.nan), lab_s, idx)
    del acc

    area = cells * spec.cell_area
    keep = (depth >= min_depth) & (area >= BASIN_MIN_AREA_M2)
    tr = spec.transform()
    recs = []
    for k, i in enumerate(idx):
        if not keep[k]:
            continue
        r, c = pos[k]
        x = tr.c + (c + 0.5) * spec.res
        y = tr.f - (r + 0.5) * spec.res
        d = float(depth[k])
        recs.append(dict(
            BASIN_ID=int(i),
            X=float(x), Y=float(y),
            LOW_Z=float(low_z[k]), SPILL_Z=float(spill_z[k]),
            DEPTH_M=round(d, 3),
            AREA_M2=round(float(area[k]), 1),
            VOL_M3=round(float(volume[k]), 1),
            CONTRIB_M2=round(float(contrib[k]), 1) if np.isfinite(contrib[k]) else None,
            # a basin deeper than the recommended maximum COVER cannot be drained by any
            # gravity alignment - the excavation is off the guideline's scale
            OVER_CAP=bool(d > COVER_CAP_M),
            PUMP_FORCED=bool(d > COVER_CAP_M),
            CAP_M=COVER_CAP_M,
            CAP_SRC="G203-p33 4.6.3 recommended max cover 10-12 m",
            MIN_DEPTH_M=round(min_depth, 3),
            DEPTH_SRC=("3 x measured DIFFERENTIAL vertical error"
                       if sigma_dz else "fallback assumption"),
            TAU_FLAG="tau=1.0 Pa assumed (GAP-9) - if NWS return 2.0 Pa the required "
                     "slopes roughly double",
            GRID=spec.name, RES_M=spec.res,
            geometry=Point(x, y)))
    g = gpd.GeoDataFrame(recs, crs=CRS) if recs else gpd.GeoDataFrame(geometry=[], crs=CRS)
    g.to_file(out_gpkg, layer="closed_basins", driver="GPKG")

    # the artefacts, kept and reported - they are where a culvert exists and the DEM lied
    art_mask = all_mask & ~surv_mask
    lab_a, n_a = ndimage.label(art_mask)
    if n_a:
        ai = np.arange(1, n_a + 1)
        adepth = ndimage.maximum(dep_all, lab_a, ai)
        acells = ndimage.sum(np.ones_like(dep_all, dtype="float32"), lab_a, ai)
        apos = ndimage.maximum_position(np.where(art_mask, dep_all, -np.inf), lab_a, ai)
        keep_a = (adepth >= min_depth) & (acells * spec.cell_area >= BASIN_MIN_AREA_M2)
        arecs = []
        for k, i in enumerate(ai):
            if not keep_a[k]:
                continue
            r, c = apos[k]
            arecs.append(dict(PIT_ID=int(i),
                              DEPTH_M=round(float(adepth[k]), 3),
                              AREA_M2=round(float(acells[k]) * spec.cell_area, 1),
                              CLASS="ARTEFACT",
                              WHY=f"resolved by a carve of <= {BREACH_DIST_M:.0f} m - "
                                  "embankment/culvert not in a bare-earth DEM",
                              GRID=spec.name,
                              geometry=Point(tr.c + (c + .5) * spec.res,
                                             tr.f - (r + .5) * spec.res)))
        if arecs:
            gpd.GeoDataFrame(arecs, crs=CRS).to_file(out_gpkg, layer="filled_pit_artefacts",
                                                     driver="GPKG")
        _log(f"basins {spec.name}: {len(arecs)} artefact pits recorded")

    _wr(lab_tif, lab_s.astype("int32"), spec, dtype="int32", nodata=0)
    n_forced = int(sum(1 for r in recs if r["PUMP_FORCED"]))
    _log(f"basins {spec.name}: {len(recs)} REAL closed basins, {n_forced} deeper than the "
         f"{COVER_CAP_M:.0f} m cover cap -> pumping unavoidable")
    manifest_write(**{f"basins_{spec.name}": dict(
        depressions_raw=n_all, depressions_surviving_carve=n_s,
        real_basins=len(recs), pump_forced=n_forced,
        min_depth_m=round(min_depth, 3), min_area_m2=BASIN_MIN_AREA_M2,
        carve_dist_m=BREACH_DIST_M, cover_cap_m=COVER_CAP_M,
        cover_cap_src="G203-p33 4.6.3")})
    return dict(gpkg=out_gpkg, labels=lab_tif, n_real=len(recs), n_forced=n_forced)


# --------------------------------------------------------------------------------------
# STAGE 7 - CATCHMENTS
# --------------------------------------------------------------------------------------

def stage_catchments(spec: GridSpec, force=False) -> dict:
    """
    Two products, because "catchment" means two things to a sewer designer.

      basins      the whole-of-domain partition: every cell assigned to the outlet it
                  eventually reaches at the edge of the grid.  This is the drainage
                  territory a trunk has to serve.
      subbasins   one polygon per stream link - the catchment draining to each stream
                  segment's outlet.  This is the grain a sub-main tier is laid out on.
    """
    import geopandas as gpd
    basins_r = RUN / f"{spec.name}_catch_basins.tif"
    sub_r = RUN / f"{spec.name}_subbasins.tif"
    out = RUN / f"{spec.name}_catchments.gpkg"
    if out.exists() and not force:
        _log(f"catchments {spec.name}: cached")
        return dict(gpkg=out, basins=basins_r, subbasins=sub_r)
    w = _wbt()
    _log(f"catchments {spec.name}: basins")
    w.basins(f"{spec.name}_d8.tif", basins_r.name)
    _log(f"catchments {spec.name}: subbasins (one per stream link)")
    w.subbasins(f"{spec.name}_d8.tif", f"{spec.name}_streams.tif", sub_r.name)

    _log(f"catchments {spec.name}: polygonising")
    for tif, layer in ((basins_r, "basins"), (sub_r, "subbasins")):
        try:
            gdf = _polygonise(tif, spec)
            gdf.to_file(out, layer=layer, driver="GPKG")
            _log(f"  {layer}: {len(gdf)} polygons, "
                 f"{gdf.area.sum()/1e6:.0f} km2")
        except Exception as e:                                    # pragma: no cover
            _log(f"  {layer} polygonise failed: {e}")
    return dict(gpkg=out, basins=basins_r, subbasins=sub_r)


def _polygonise(tif: Path, spec: GridSpec, min_area_m2: float = 10000.0):
    import rasterio
    from rasterio import features
    import geopandas as gpd
    from shapely.geometry import shape
    with rasterio.open(tif) as s:
        a = s.read(1)
        tr = s.transform
        nd = s.nodata
    m = np.isfinite(a) & (a > 0)
    if nd is not None:
        m &= (a != nd)
    geoms, vals = [], []
    for geom, val in features.shapes(a.astype("int32"), mask=m, transform=tr, connectivity=8):
        g = shape(geom)
        if g.area >= min_area_m2:
            geoms.append(g)
            vals.append(int(val))
    gdf = gpd.GeoDataFrame(dict(ID=vals), geometry=geoms, crs=CRS)
    gdf["AREA_M2"] = gdf.area
    gdf["AREA_KM2"] = gdf.area / 1e6
    gdf["GRID"] = spec.name
    return gdf.dissolve(by="ID", aggfunc="sum").reset_index()


# --------------------------------------------------------------------------------------
# THE API
# --------------------------------------------------------------------------------------

class TerrainFlow:
    """
    The object every later stage holds.

    Arrays are opened as memory maps, so constructing it is free and only the pages a
    query touches are read.  All the accessors take scalars OR arrays; the network builder
    should ALWAYS pass arrays - see bench() for what the difference costs.
    """

    def __init__(self, spec: GridSpec, rasters: dict, manifest: dict):
        self.spec = spec
        self._r = rasters
        self.manifest = manifest
        q = manifest.get("dem_quality", {})
        # ABSOLUTE error - for a statement about a level in m aOD
        self.sigma_z = float(q.get("sigma_z_m", BASIN_MIN_DEPTH_FALLBACK_M / 3.0))
        # DIFFERENTIAL error over a corridor-length baseline - for every DIRECTION, FALL,
        # PIT DEPTH and RIDGE test here, because the correlated part cancels
        self.sigma_dz = float(q.get("sigma_dz_m", self.sigma_z))
        # the measured sign-agreement curve, indexed on the fall a caller can actually see
        self._pcurve = []
        for r in (q.get("relative") or {}).get("sign_agreement_vs_observed_fall", []):
            lo, hi = r["observed_fall_m"].split("-")
            self._pcurve.append((float(lo), float(hi), float(r["sign_agreement"])))
        self._vrt = None

    def p_direction_correct(self, observed_fall_m):
        """
        The MEASURED probability that a fall of this size gives the right direction.

        Not a model - the empirical curve from NAMA's built sewer, where the true flow
        direction is known by construction.  Returns None if the calibration has not been
        built yet.
        """
        if not self._pcurve:
            return None
        f = abs(float(observed_fall_m))
        for lo, hi, p in self._pcurve:
            if lo <= f < hi:
                return p
        return self._pcurve[-1][2] if f >= self._pcurve[-1][0] else self._pcurve[0][2]

    # -- construction ------------------------------------------------------------------
    @classmethod
    def load(cls, grid: str = "R5") -> "TerrainFlow":
        import rasterio
        spec = regional_spec() if grid == "R5" else local_spec()
        want = dict(dem=f"{spec.name}_dem.tif", cond=f"{spec.name}_dem_cond.tif",
                    d8=f"{spec.name}_d8.tif", acc=f"{spec.name}_acc.tif",
                    strdist=f"{spec.name}_stream_dist.tif",
                    basin=f"{spec.name}_basin_id.tif",
                    catch=f"{spec.name}_catch_basins.tif",
                    sub=f"{spec.name}_subbasins.tif")
        for rp in FLOOD_GRIDS:
            want[f"haz{rp}"] = f"{spec.name}_hazard_T{rp}.tif"
        rasters = {}
        for k, fn in want.items():
            p = RUN / fn
            if p.exists():
                rasters[k] = _MemRaster(p)
        return cls(spec, rasters, manifest_read())

    def _need(self, key):
        if key not in self._r:
            raise FileNotFoundError(
                f"{key} not built for grid {self.spec.name}; run `python terrain.py build`")
        return self._r[key]

    # -- primitives --------------------------------------------------------------------
    def rowcol(self, x, y):
        x = np.asarray(x, dtype="float64")
        y = np.asarray(y, dtype="float64")
        c = np.floor((x - self.spec.left) / self.spec.res).astype("int64")
        r = np.floor((self.spec.top - y) / self.spec.res).astype("int64")
        return r, c

    @staticmethod
    def _scalarise(v, x):
        """Give a scalar back for a scalar query.

        Without this every caller writes np.atleast_1d(...)[0] around every accessor,
        which is friction the other stages should not have to carry.
        """
        return v if np.ndim(x) else v.reshape(-1)[0].item()

    def elevation(self, x, y, native=False):
        """
        Ground level, m aOD.

        native=True reads the 0.5 m VRT itself rather than the working grid.  Use it for
        anything that becomes a LEVEL - a chamber cover, an invert, a fall over a short
        reach.  The working grid is for routing, not for setting inverts.
        """
        if native:
            return self._elev_native(x, y)
        return self._scalarise(
            self._need("dem").sample(*self.rowcol(x, y), nodata=np.nan), x)

    # 512 matches the source GeoTIFF's own block size, so a cache MISS costs exactly one
    # block decode - the same as rasterio.sample - while a HIT costs nothing.  A larger
    # tile was tried and made SCATTERED queries 7.7x worse, because every miss then
    # decoded four blocks to answer one point.
    NATIVE_TILE = 512           # native cells per cached tile (256 m at 0.5 m)
    NATIVE_CACHE = 256          # tiles held; 256 x 512^2 float32 = 268 MB

    def _elev_native(self, x, y):
        """
        Point elevation off the native 0.5 m VRT.

        Slow by nature: every point touches a deflate-compressed 512 x 512 block of a
        7.4 GB file, which measured at 1.44 ms per scattered point.  Decoded tiles are
        therefore cached, so CLUSTERED queries - which is what a chamber schedule or a
        profile actually is - cost a fraction of that.  Callers with scattered points
        should sort them spatially first.

        Worth knowing before reaching for it: measured against NAMA's 4,288 surveyed
        ground levels, native sampling is NOT more accurate than the 5 m working grid
        (SD 0.7564 m vs 0.7561 m), and it gave an IDENTICAL drain direction on every
        decidable test line.  Use it for sub-5 m detail on a short feature, not in the
        belief that it is a better number.
        """
        import rasterio
        from rasterio.windows import Window
        if self._vrt is None:
            self._vrt = rasterio.open(DEM_VRT)
            self._ncache = {}
        src = self._vrt
        xa = np.atleast_1d(np.asarray(x, dtype="float64"))
        ya = np.atleast_1d(np.asarray(y, dtype="float64"))
        sres = src.res[0]
        col = np.floor((xa - src.bounds.left) / sres).astype("int64")
        row = np.floor((src.bounds.top - ya) / sres).astype("int64")
        out = np.full(xa.shape, np.nan, dtype="float64")
        inb = (row >= 0) & (row < src.height) & (col >= 0) & (col < src.width)
        if inb.any():
            T = self.NATIVE_TILE
            tr, tc = row // T, col // T
            keys = set(zip(tr[inb].tolist(), tc[inb].tolist()))
            # SCATTERED points defeat tiling: every tile is fetched to answer one point,
            # and because the VRT composites two sources a windowed read costs far more
            # than a single sample.  Measured: 6.0 ms/pt tiled vs 1.4 ms/pt sampled.  So
            # below ~4 points per tile, and with nothing useful already cached, hand the
            # job back to GDAL's own sampler.
            uncached = sum(1 for k in keys if k not in self._ncache)
            if uncached > 8 and int(inb.sum()) < 4 * uncached:
                pts = list(zip(xa[inb].tolist(), ya[inb].tolist()))
                v = np.array([s[0] for s in src.sample(pts)], dtype="float64")
                out[inb] = v
                out[out <= -9990] = np.nan
                return out if np.ndim(x) else float(out[0])
            for key in keys:
                tile = self._ncache.get(key)
                if tile is None:
                    r0, c0 = key[0] * T, key[1] * T
                    tile = src.read(1, window=Window(c0, r0,
                                                     min(T, src.width - c0),
                                                     min(T, src.height - r0))).astype("float32")
                    if len(self._ncache) >= self.NATIVE_CACHE:
                        self._ncache.pop(next(iter(self._ncache)))
                    self._ncache[key] = tile
                m = inb & (tr == key[0]) & (tc == key[1])
                out[m] = tile[row[m] - key[0] * T, col[m] - key[1] * T]
        out[out <= -9990] = np.nan
        return out if np.ndim(x) else float(out[0])

    def conditioned(self, x, y):
        """The routing surface (breached + filled).  Never publish this as ground."""
        return self._scalarise(
            self._need("cond").sample(*self.rowcol(x, y), nodata=np.nan), x)

    def accumulation(self, x, y):
        """Upstream contributing area, m2."""
        return self._scalarise(
            self._need("acc").sample(*self.rowcol(x, y), nodata=np.nan), x)

    def stream_distance(self, x, y):
        """Metres to the nearest derived stream.  65535 means 'beyond the grid'."""
        return self._scalarise(
            self._need("strdist").sample(*self.rowcol(x, y), nodata=65535).astype("float64"), x)

    def basin_at(self, x, y):
        """Closed-basin id, 0 if the point is not in one."""
        return self._scalarise(
            self._need("basin").sample(*self.rowcol(x, y), nodata=0).astype("int64"), x)

    def catchment_at(self, x, y, sub=True):
        return self._scalarise(self._need("sub" if sub else "catch").sample(
            *self.rowcol(x, y), nodata=0).astype("int64"), x)

    def hazard_class(self, x, y, return_period=WADI_RETURN_PERIOD_DEFAULT):
        return self._scalarise(self._need(f"haz{return_period}").sample(
            *self.rowcol(x, y), nodata=0).astype("int16"), x)

    def in_wadi(self, x, y, return_period=WADI_RETURN_PERIOD_DEFAULT):
        """
        Wadi ground, where G203-p30 4.4.1 forbids a pipeline or a chamber.

        The test is the project's assumption, not a guideline threshold: hazard class
        4, 5 or 6 of the return-period grid.  Class 0 means the hazard model has NO DATA
        there, and by the engineer's decision of 2026-09-03 that is read as DRY HIGH
        GROUND.  47 % of the study area is in that condition, so a False here means
        "not shown to be wadi", and full-coverage 50-year mapping is still owed by NWS.
        """
        h = self.hazard_class(x, y, return_period)
        w = np.isin(h, HAZARD_WADI_CLASSES)
        return w if np.ndim(x) else bool(np.reshape(w, -1)[0])

    # -- direction ---------------------------------------------------------------------
    def downhill_bearing(self, x, y, radius=BEARING_RADIUS_M):
        """
        Which way is downhill here.

        Returns (bearing_deg, slope_pct).  Bearing is compass degrees (0 = north, 90 =
        east) pointing DOWNHILL.

        A least-squares plane is fitted through the conditioned surface over `radius`,
        not a two-cell difference and not the D8 pointer.  D8 would quantise the answer
        to 45 deg, which on ground falling 0.1 % is a useless direction for orienting a
        corridor.  The plane fit is continuous and is dominated by the trend rather than
        by one noisy cell.
        """
        scalar = np.ndim(x) == 0          # capture BEFORE x is promoted to an array
        x = np.atleast_1d(np.asarray(x, dtype="float64"))
        y = np.atleast_1d(np.asarray(y, dtype="float64"))
        k = max(1, int(round(radius / self.spec.res)))
        offs = np.arange(-k, k + 1) * self.spec.res
        dx, dy = np.meshgrid(offs, offs)
        keep = (dx ** 2 + dy ** 2) <= radius ** 2 + 1e-9
        dx, dy = dx[keep], dy[keep]
        n = dx.size
        xs = x[:, None] + dx[None, :]
        ys = y[:, None] + dy[None, :]
        z = self.conditioned(xs.ravel(), ys.ravel()).reshape(len(x), n)
        ok = np.isfinite(z)
        # per-point least squares on [1, dx, dy], solved for every point at once -
        # a Python loop over np.linalg.solve here cost 2 ms/call, which the network
        # builder cannot afford at the rate it calls this
        cnt = ok.sum(1).astype("float64")
        zz = np.where(ok, z, 0.0)
        okf = ok.astype("float64")
        DX, DY = dx[None, :], dy[None, :]
        Sx = (okf * DX).sum(1)
        Sy = (okf * DY).sum(1)
        Sxx = (okf * DX ** 2).sum(1)
        Syy = (okf * DY ** 2).sum(1)
        Sxy = (okf * DX * DY).sum(1)
        Sz = zz.sum(1)
        Sxz = (zz * DX).sum(1)
        Syz = (zz * DY).sum(1)
        bx = np.full(len(x), np.nan)
        by = np.full(len(x), np.nan)
        good = cnt >= 6
        if good.any():
            gi = np.nonzero(good)[0]
            A = np.empty((gi.size, 3, 3), dtype="float64")
            A[:, 0, 0] = cnt[gi]; A[:, 0, 1] = Sx[gi];  A[:, 0, 2] = Sy[gi]
            A[:, 1, 0] = Sx[gi];  A[:, 1, 1] = Sxx[gi]; A[:, 1, 2] = Sxy[gi]
            A[:, 2, 0] = Sy[gi];  A[:, 2, 1] = Sxy[gi]; A[:, 2, 2] = Syy[gi]
            b = np.stack([Sz[gi], Sxz[gi], Syz[gi]], axis=1)
            det = np.linalg.det(A)
            solvable = np.abs(det) > 1e-9
            if solvable.any():
                # numpy 2 reads a (n,3) right-hand side as a MATRIX, not a stack of
                # vectors - the trailing axis is explicit here so it stays a stack
                sol = np.linalg.solve(A[solvable], b[solvable][..., None])[..., 0]
                idx = gi[solvable]
                bx[idx] = sol[:, 1]
                by[idx] = sol[:, 2]
        # gradient points uphill; downhill is its negative
        grad = np.hypot(bx, by)
        bearing = (np.degrees(np.arctan2(-bx, -by)) + 360.0) % 360.0
        slope_pct = grad * 100.0
        if scalar:
            return float(bearing[0]), float(slope_pct[0])
        return bearing, slope_pct

    # -- lines -------------------------------------------------------------------------
    def _profile(self, line, step=PROFILE_STEP_M, native=False):
        """
        Chainage and elevation along a shapely LineString.

        Interpolation is done on the vertex array with numpy rather than by calling
        shapely's interpolate once per station: that loop was most of the cost of
        drain_direction, which the network builder calls hundreds of thousands of times.
        """
        xy = np.asarray(line.coords, dtype="float64")[:, :2]
        seg = np.hypot(np.diff(xy[:, 0]), np.diff(xy[:, 1]))
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        L = float(cum[-1])
        n = max(2, int(math.ceil(L / step)) + 1)
        s = np.linspace(0.0, L, n)
        xs = np.interp(s, cum, xy[:, 0])
        ys = np.interp(s, cum, xy[:, 1])
        z = self.elevation(xs, ys, native=native)
        return s, np.asarray(z, dtype="float64"), xs, ys

    def drain_direction(self, line, step=PROFILE_STEP_M, native=False):
        """
        For a corridor line: WHICH END IS THE OUTLET.

        Returns a dict:
            outlet_end   'end' if the line's last vertex is the low end, 'start' if the
                         first is, None if the ground cannot decide
            fall_m       fall from the high end to the outlet (positive)
            slope_pct    fall / length
            confidence   'certain' | 'likely' | 'uncertain' | 'flat'
            r2           fit of the profile to a straight grade
            monotone     fraction of steps that fall in the outlet's direction
            reversals    number of sign changes in the profile - a high count means the
                         corridor crosses a ridge or a hollow and one direction cannot
                         serve it
            sigma_z      the DEM noise the fall is being judged against

        Confidence is measured, not asserted: the fall must beat the DEM's own vertical
        noise (sigma_z, measured against NAMA's recorded ground levels) by
        CONF_CERTAIN_SIGMA before the direction is called certain.  A corridor whose fall
        is inside the noise is FLAT and the network builder must not pretend otherwise.
        """
        from shapely.geometry import LineString
        if not isinstance(line, LineString):
            line = LineString(line)
        s, z, xs, ys = self._profile(line, step, native=native)
        ok = np.isfinite(z)
        if ok.sum() < 3:
            return dict(outlet_end=None, fall_m=np.nan, slope_pct=np.nan,
                        confidence="no-data", r2=np.nan, monotone=np.nan,
                        reversals=0, sigma_z=self.sigma_z, length_m=float(line.length),
                        z_start=np.nan, z_end=np.nan)
        s, z = s[ok], z[ok]
        # robust straight-grade fit
        A = np.vstack([s, np.ones_like(s)]).T
        sol, *_ = np.linalg.lstsq(A, z, rcond=None)
        m, c = sol
        pred = A @ sol
        ss_res = float(((z - pred) ** 2).sum())
        ss_tot = float(((z - z.mean()) ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        down_end = m < 0                       # elevation decreases with chainage
        fall_fit = abs(m) * (s[-1] - s[0])
        fall_ends = abs(z[0] - z[-1])
        fall = max(fall_fit, 0.0)

        # Monotonicity has to be measured at a scale where the SIGNAL BEATS THE NOISE.
        # Measured at the raw 5 m step, a 12 km line falling 30 m falls 13 mm per step -
        # 3 % of the DEM's 0.48 m differential noise - so the step-by-step sign is a coin
        # toss and the fraction sits at 0.5 whatever the ground does.  That mislabelled a
        # 12 km trunk with 30 m of fall and r2 = 0.95 as "uncertain", which is exactly the
        # kind of false doubt that would push a later stage back onto road connectivity.
        # So the profile is blocked into segments each expected to fall at least twice the
        # noise, and monotonicity and reversals are counted on the block means.
        n_seg = int(np.clip(fall_ends / max(2.0 * self.sigma_dz, 1e-6), 2, 20))
        n_seg = min(n_seg, max(2, len(z) // 2))
        edges = np.linspace(0, len(z), n_seg + 1).astype(int)
        zb = np.array([z[a:b].mean() for a, b in zip(edges[:-1], edges[1:]) if b > a])
        dzb = np.diff(zb)
        monotone = float((dzb < 0).mean() if down_end else (dzb > 0).mean()) if dzb.size else 0.0
        reversals = int((np.diff(np.sign(dzb)) != 0).sum()) if dzb.size > 1 else 0
        dz_raw = np.diff(z)
        reversals_raw = int((np.diff(np.sign(dz_raw)) != 0).sum())
        # The bar is the DIFFERENTIAL error, not the absolute one: the datum offset and
        # the blend seams are the same at both ends of a 100 m line and cancel.  Measured
        # at 0.45 m here against NAMA's surveyed levels, where the absolute error is
        # 0.76 m - using the absolute figure would call real gradients flat.
        noise = self.sigma_dz
        # A corridor whose CREST or SAG sits in the middle has no single outlet, and
        # handing one back is exactly how W11a ended up with 42.5 % of its length draining
        # uphill: a straight-grade fit through a ridge returns a direction with a
        # confident-looking fall while half the line climbs.  Detect it here, on the
        # profile already in hand, and refuse to answer - the corridor must be SPLIT at
        # the crest and drained both ways.
        lo_i = int(len(z) * RIDGE_INTERIOR_FRAC)
        hi_i = int(len(z) * (1 - RIDGE_INTERIOR_FRAC))
        crest_prom = sag_depth = 0.0
        split_at = None
        if hi_i - lo_i >= 2:
            ci = lo_i + int(np.argmax(z[lo_i:hi_i]))
            si = lo_i + int(np.argmin(z[lo_i:hi_i]))
            crest_prom = float(z[ci] - max(z[0], z[-1]))
            sag_depth = float(min(z[0], z[-1]) - z[si])
            if crest_prom >= sag_depth:
                split_at = float(s[ci])
            else:
                split_at = float(s[si])
        split_size = max(crest_prom, sag_depth)
        if split_size >= 3.0 * noise and split_size > fall_ends:
            return dict(outlet_end=None, fall_m=float(fall), fall_ends_m=float(fall_ends),
                        slope_pct=float(100.0 * fall / (float(s[-1] - s[0]) or 1.0)),
                        confidence="split", r2=float(r2), monotone=monotone,
                        reversals=reversals, reversals_raw=reversals_raw, n_seg=int(n_seg),
                        p_correct=None, sigma_dz=self.sigma_dz, sigma_z=self.sigma_z,
                        length_m=float(line.length), z_start=float(z[0]),
                        z_end=float(z[-1]), split_at_m=split_at,
                        split_kind="ridge" if crest_prom >= sag_depth else "hollow",
                        split_prominence_m=round(split_size, 3),
                        note="no single outlet: the crest/sag inside this line is larger "
                             "than the fall across it. Split it and drain both ways.")
        if fall_ends < CONF_LIKELY_SIGMA * noise:
            conf = "flat"
            outlet = None
        elif fall_ends >= CONF_CERTAIN_SIGMA * noise and monotone >= 0.60:
            conf = "certain"
            outlet = "end" if down_end else "start"
        elif fall_ends >= CONF_LIKELY_SIGMA * noise:
            conf = "likely" if monotone >= 0.55 else "uncertain"
            outlet = "end" if down_end else "start"
        else:
            conf = "uncertain"
            outlet = "end" if down_end else "start"
        L = float(s[-1] - s[0]) or 1.0
        return dict(outlet_end=outlet, fall_m=float(fall), fall_ends_m=float(fall_ends),
                    slope_pct=float(100.0 * fall / L), confidence=conf, r2=float(r2),
                    monotone=monotone, reversals=reversals,
                    reversals_raw=reversals_raw, n_seg=int(n_seg),
                    p_correct=self.p_direction_correct(fall_ends),
                    sigma_dz=self.sigma_dz, sigma_z=self.sigma_z,
                    length_m=float(line.length), z_start=float(z[0]), z_end=float(z[-1]))

    def is_ridge(self, line, step=PROFILE_STEP_M, native=False,
                 prominence=None):
        """
        Does this line straddle a divide - do both ends drain away from the middle?

        A corridor on a ridge cannot be sewered in one direction: whichever end you point
        it at, half of it climbs.  W11a had no such test, which is one reason 42.5 % of it
        ran uphill.

        Returns a dict with `is_ridge`, the crest chainage and its prominence above the
        higher of the two ends.  Prominence must beat 3 x the DEM's measured vertical
        noise, so a ridge is never an artefact of the surface.
        """
        from shapely.geometry import LineString
        if not isinstance(line, LineString):
            line = LineString(line)
        prom_min = prominence if prominence is not None else max(
            3.0 * self.sigma_dz, RIDGE_MIN_PROMINENCE_M)
        s, z, xs, ys = self._profile(line, step, native=native)
        ok = np.isfinite(z)
        if ok.sum() < 5:
            return dict(is_ridge=False, reason="no-data", crest_m=np.nan,
                        prominence_m=np.nan, min_prominence_m=prom_min)
        s, z = s[ok], z[ok]
        lo = int(len(z) * RIDGE_INTERIOR_FRAC)
        hi = int(len(z) * (1 - RIDGE_INTERIOR_FRAC))
        if hi - lo < 2:
            return dict(is_ridge=False, reason="too-short", crest_m=np.nan,
                        prominence_m=np.nan, min_prominence_m=prom_min)
        k = lo + int(np.argmax(z[lo:hi]))
        prom = float(z[k] - max(z[0], z[-1]))
        # a hollow is the mirror image and matters just as much - a corridor in a valley
        # bottom drains OUT of both ends, which is legal; a ridge drains IN to neither
        j = lo + int(np.argmin(z[lo:hi]))
        sag = float(min(z[0], z[-1]) - z[j])
        return dict(is_ridge=bool(prom >= prom_min), crest_m=float(s[k]),
                    prominence_m=prom, min_prominence_m=float(prom_min),
                    is_hollow=bool(sag >= prom_min), sag_m=sag, sag_at_m=float(s[j]),
                    z_start=float(z[0]), z_end=float(z[-1]), z_crest=float(z[k]))

    # -- routing -----------------------------------------------------------------------
    def flow_path(self, x, y, max_steps=100000):
        """
        The D8 path downhill from a point, as an (n, 2) array of coordinates.

        This is the ground's own answer to "where does water from here go".  Stops at a
        nodata cell, at the grid edge, or when the pointer says 0 (an outlet).
        """
        d8 = self._need("d8")
        r, c = self.rowcol(x, y)
        r = int(np.atleast_1d(r)[0]); c = int(np.atleast_1d(c)[0])
        H, W = d8.shape
        out = []
        for _ in range(max_steps):
            if not (0 <= r < H and 0 <= c < W):
                break
            out.append((self.spec.left + (c + .5) * self.spec.res,
                        self.spec.top - (r + .5) * self.spec.res))
            v = int(d8.at(r, c))
            if v not in D8_DECODE:
                break
            dr, dc = D8_DECODE[v]
            r += dr; c += dc
        return np.array(out)

    def flags(self) -> dict:
        """Everything downstream must print.  Assumptions do not travel silently."""
        return {
            "tau_Pa": 1.0,
            "tau_note": "tractive stress 1.0 Pa is an ASSUMPTION (GAP-9). It gives "
                        "shallower slopes, so shallower pipes and fewer pumps. If NWS "
                        "return 2.0 Pa the required slopes roughly double.",
            "wadi_classes": list(HAZARD_WADI_CLASSES),
            "wadi_note": "wadi ground = AR&R hazard class 4-6 of the "
                         f"{WADI_RETURN_PERIOD_DEFAULT}-year grid. PROJECT ASSUMPTION "
                         "standing in for G203-p30 4.4.1's washout criterion, not a "
                         "guideline threshold.",
            "flood_nodata": "no-data in the hazard grids is read as DRY HIGH GROUND "
                            "(engineer, 2026-09-03), not as untested.",
            "cover_cap_m": COVER_CAP_M,
            "cover_cap_src": "G203-p33 4.6.3 (recommended maximum cover 10-12 m)",
            "min_cover_m": MIN_COVER_M,
            "min_cover_src": "G203-p33 4.6.3",
            "grid": self.spec.name, "res_m": self.spec.res,
            "sigma_z_m": self.sigma_z,
            "sigma_dz_m": self.sigma_dz,
            "sigma_note": "sigma_z is the ABSOLUTE vertical error (use for a level in "
                          "m aOD); sigma_dz is the DIFFERENTIAL error over a corridor "
                          "baseline (use for every direction, fall, pit depth and ridge "
                          "test). Both MEASURED against NAMA's surveyed ground levels.",
            "concept_stage_accuracy": "G201-p36 Tab 5 asks 0.05-0.5 m vertical at "
                                      "concept stage. sigma_z = 0.76 m does NOT meet it: "
                                      "levels off this DEM are feasibility grade and a "
                                      "topographic survey is still required.",
            "dem": str(DEM_VRT),
        }


class _MemRaster:
    """A memory-mapped single-band raster with cheap point sampling."""

    def __init__(self, path: Path):
        import rasterio
        self.path = Path(path)
        self._src = rasterio.open(self.path)
        self.nodata = self._src.nodata
        self.shape = (self._src.height, self._src.width)
        self._arr = None

    @property
    def arr(self):
        if self._arr is None:
            npy = self.path.with_suffix(".npy")
            if not npy.exists():
                a = self._src.read(1)
                np.save(npy, a)
                del a
            self._arr = np.load(npy, mmap_mode="r")
        return self._arr

    def at(self, r, c):
        return self.arr[r, c]

    def sample(self, r, c, nodata=np.nan):
        a = self.arr
        r = np.atleast_1d(r); c = np.atleast_1d(c)
        ok = (r >= 0) & (r < a.shape[0]) & (c >= 0) & (c < a.shape[1])
        out = np.full(r.shape, nodata, dtype="float64")
        if ok.any():
            v = a[r[ok], c[ok]].astype("float64")
            if self.nodata is not None:
                v = np.where(v == self.nodata, nodata, v)
            v = np.where(v <= -9990.0, nodata, v)
            out[ok] = v
        return out


# --------------------------------------------------------------------------------------
# VERIFICATION - against reality, not against itself
# --------------------------------------------------------------------------------------

def verify_dem_quality(spec: GridSpec) -> dict:
    """
    How good is the surface, in metres?

    Two independent measurements, neither of them an assumption:

      A  the two sources inside the VRT disagree.  ibri_blend.tif (5 m) and
         ibri_0p5_blend.tif (0.5 m) cover the same ground; their difference is the
         surface's own internal disagreement.
      B  NAMA's built sewer records US_GROUND_ / DS_GROUND_ - surveyed ground levels at
         3,267 built pipe ends.  Comparing the DEM against them is the only truly external
         vertical check available on this project.

    sigma_z from B is what every confidence in this module is judged against.
    """
    import rasterio
    from rasterio.windows import Window
    out = {}

    # A - the two DEM sources against each other
    try:
        p5 = PROJECT / "Data" / "Terrain" / "Sat_0p5m" / "ibri_blend.tif"
        p05 = PROJECT / "Data" / "Terrain" / "Sat_0p5m" / "ibri_0p5_blend.tif"
        diffs = []
        with rasterio.open(p5) as a, rasterio.open(p05) as b:
            rng = np.random.default_rng(11)
            for _ in range(40):
                r = int(rng.integers(0, a.height - 200))
                c = int(rng.integers(0, a.width - 200))
                za = a.read(1, window=Window(c, r, 200, 200)).astype("float64")
                x0, y0 = a.xy(r, c)
                rb, cb = b.index(x0, y0)
                zb = b.read(1, window=Window(cb, rb, 2000, 2000)).astype("float64")
                if zb.shape != (2000, 2000):
                    continue
                za[za <= -9990] = np.nan
                zb[zb <= -9990] = np.nan
                zbm = np.nanmean(zb.reshape(200, 10, 200, 10), axis=(1, 3))
                d = zbm - za
                d = d[np.isfinite(d)]
                if d.size:
                    diffs.append(d)
        if diffs:
            d = np.concatenate(diffs)
            out["source_disagreement"] = dict(
                n=int(d.size), mean_m=float(np.mean(d)), rmse_m=float(np.sqrt(np.mean(d ** 2))),
                p50_abs_m=float(np.percentile(np.abs(d), 50)),
                p95_abs_m=float(np.percentile(np.abs(d), 95)),
                note="0.5 m source aggregated to 5 m, minus the 5 m source, same cells")
    except Exception as e:                                      # pragma: no cover
        out["source_disagreement"] = dict(error=str(e))

    # B - against NAMA's surveyed ground levels
    try:
        import geopandas as gpd
        g = gpd.read_file(NAMA_SEWER).to_crs(CRS)
        g = g[g["STATUS"].astype(str).str.strip().str.lower() == "ex"]
        recs = []
        for geom, zu, zd in zip(g.geometry, g["US_GROUND_"], g["DS_GROUND_"]):
            if geom is None or geom.is_empty:
                continue
            try:
                cs = list(geom.geoms[0].coords) if geom.geom_type == "MultiLineString" \
                    else list(geom.coords)
            except Exception:
                continue
            if len(cs) < 2:
                continue
            for (x, y), z in ((cs[0][:2], zu), (cs[-1][:2], zd)):
                if z is None or not np.isfinite(z) or z <= 0:
                    continue
                recs.append((x, y, float(z)))
        if recs:
            arr = np.array(recs)
            tf = TerrainFlow.load(spec.name)
            zw = tf.elevation(arr[:, 0], arr[:, 1])              # working grid
            zn = tf.elevation(arr[:, 0], arr[:, 1], native=True)  # native 0.5 m
            for tag, zz in (("working_grid", zw), ("native_0p5m", zn)):
                d = np.asarray(zz, dtype="float64") - arr[:, 2]
                d = d[np.isfinite(d)]
                if d.size:
                    out[f"vs_nama_ground_{tag}"] = dict(
                        n=int(d.size), bias_m=float(np.mean(d)),
                        rmse_m=float(np.sqrt(np.mean(d ** 2))),
                        sd_m=float(np.std(d)),
                        p50_abs_m=float(np.percentile(np.abs(d), 50)),
                        p95_abs_m=float(np.percentile(np.abs(d), 95)))
    except Exception as e:                                      # pragma: no cover
        out["vs_nama_ground"] = dict(error=str(e))

    # sigma_z: prefer the external check, the working grid's own SD about NAMA
    sz = None
    for k in ("vs_nama_ground_working_grid", "vs_nama_ground_native_0p5m"):
        if k in out and "sd_m" in out[k]:
            sz = out[k]["sd_m"]
            out["sigma_z_source"] = k
            break
    if sz is None and "source_disagreement" in out and "rmse_m" in out["source_disagreement"]:
        sz = out["source_disagreement"]["rmse_m"]
        out["sigma_z_source"] = "source_disagreement"
    out["sigma_z_m"] = float(sz) if sz else BASIN_MIN_DEPTH_FALLBACK_M / 3.0
    out["tag"] = "MEASURED" if sz else "ASSUME (fallback)"

    # C - the number that actually matters
    try:
        out["relative"] = verify_dem_relative_accuracy(spec)
        out["sigma_dz_m"] = out["relative"]["sigma_dz_m"]
    except Exception as e:                                      # pragma: no cover
        out["relative"] = dict(error=str(e))
        out["sigma_dz_m"] = out["sigma_z_m"]

    out["which_sigma_to_use"] = (
        "sigma_z is the ABSOLUTE error and is the right number for a statement about a "
        "level in metres aOD. sigma_dz is the DIFFERENTIAL error over a corridor-length "
        "baseline and is the right number for every DIRECTION, FALL, PIT DEPTH and RIDGE "
        "test in this module, because the correlated part of the error cancels between "
        "two nearby points. Using sigma_z for those would be over-strict by ~1.7x and "
        "would suppress real basins and real gradients.")
    return out


def verify_dem_relative_accuracy(spec: GridSpec) -> dict:
    """
    The number that governs every direction this module reports.

    sigma_z (absolute) is dominated by datum offset and blend seams that are the SAME at
    two points 40 m apart, so they cancel in a difference.  What matters for "which way
    does this corridor fall" is the error in the DIFFERENCE.

    Measured against NAMA's built sewer, which records surveyed ground level at both ends
    of every pipe: for each pipe, (DEM dz) minus (surveyed dz).  The result is also
    resolved as a SIGN-AGREEMENT CURVE against the size of the true fall - the honest
    statement of when the terrain can decide a direction and when it cannot.
    """
    import geopandas as gpd
    g = gpd.read_file(NAMA_SEWER).to_crs(CRS)
    g = g[g["STATUS"].astype(str).str.strip().str.lower() == "ex"]
    tf = TerrainFlow.load(spec.name)
    rows = []
    for geom, zu, zd in zip(g.geometry, g["US_GROUND_"], g["DS_GROUND_"]):
        if geom is None or geom.is_empty:
            continue
        try:
            cs = list(geom.geoms[0].coords) if geom.geom_type == "MultiLineString" \
                else list(geom.coords)
            zu = float(zu); zd = float(zd)
        except Exception:
            continue
        if len(cs) < 2 or not (np.isfinite(zu) and np.isfinite(zd)) or zu <= 0 or zd <= 0:
            continue
        x1, y1 = cs[0][:2]
        x2, y2 = cs[-1][:2]
        L = float(math.hypot(x2 - x1, y2 - y1))
        if L < 5:
            continue
        rows.append((x1, y1, x2, y2, L, zu - zd))
    a = np.array(rows)
    z1 = np.asarray(tf.elevation(a[:, 0], a[:, 1]), dtype="float64")
    z2 = np.asarray(tf.elevation(a[:, 2], a[:, 3]), dtype="float64")
    dz_dem = z1 - z2
    dz_true = a[:, 5]
    L = a[:, 4]
    err = dz_dem - dz_true
    ok = np.isfinite(err)
    err, L, dz_true, dz_dem = err[ok], L[ok], dz_true[ok], dz_dem[ok]
    by_len = []
    for lo, hi in ((5, 25), (25, 50), (50, 100), (100, 1e9)):
        m = (L >= lo) & (L < hi)
        if m.sum() < 10:
            continue
        e = err[m]
        by_len.append(dict(baseline_m=f"{lo:.0f}-{hi:.0f}", n=int(m.sum()),
                           bias_m=round(float(e.mean()), 4),
                           sd_m=round(float(e.std()), 4),
                           rmse_m=round(float(np.sqrt((e ** 2).mean())), 4)))
    # the honest confidence curve: can the terrain call the direction, given the fall?
    curve = []
    for lo, hi in ((0, .10), (.10, .25), (.25, .50), (.50, 1.0), (1.0, 2.0), (2.0, 1e9)):
        m = (np.abs(dz_true) >= lo) & (np.abs(dz_true) < hi)
        if m.sum() < 10:
            continue
        curve.append(dict(true_fall_m=f"{lo:.2f}-{hi:.2f}", n=int(m.sum()),
                          sign_agreement=round(
                              float((np.sign(dz_dem[m]) == np.sign(dz_true[m])).mean()), 4)))
    # and the same curve indexed on the OBSERVED fall, which is what a caller has
    curve_obs = []
    for lo, hi in ((0, .25), (.25, .50), (.50, 1.0), (1.0, 2.0), (2.0, 1e9)):
        m = (np.abs(dz_dem) >= lo) & (np.abs(dz_dem) < hi)
        if m.sum() < 10:
            continue
        curve_obs.append(dict(observed_fall_m=f"{lo:.2f}-{hi:.2f}", n=int(m.sum()),
                              sign_agreement=round(
                                  float((np.sign(dz_dem[m]) == np.sign(dz_true[m])).mean()), 4)))
    sd = float(np.median([r["sd_m"] for r in by_len])) if by_len else float(err.std())
    return dict(n_pipes=int(err.size), sigma_dz_m=round(sd, 4),
                by_baseline=by_len, sign_agreement_vs_true_fall=curve,
                sign_agreement_vs_observed_fall=curve_obs,
                note="NAMA US_GROUND_/DS_GROUND_ surveyed levels; built pipes only. The "
                     "curve is the calibration behind drain_direction()'s confidence.")


def verify_streams_vs_flood(spec: GridSpec) -> dict:
    """
    Do the derived streams land where the flood model says water goes?

    Checked against ALL FIVE return periods, not only the 50-year the threshold was tuned
    on - the other four are untouched evidence.  Agreement is reported at four tolerances
    so the reader can see whether a disagreement is a wrong PLACE or merely a different
    line inside the same braided bed.
    """
    import warnings
    from scipy import ndimage
    from skimage.morphology import skeletonize, remove_small_objects
    sl = _study_window(spec)
    st = _rd(RUN / f"{spec.name}_streams.tif")[sl]
    stm = np.isfinite(st) & (st > 0)
    d_st = ndimage.distance_transform_edt(~stm, sampling=spec.res)
    tols = (25.0, 50.0, 100.0, 200.0)
    out = dict(_window="study boundaries + 2 km",
               stream_km_in_window=round(float(stm.sum()) * spec.res / 1000.0, 0),
               tolerances_m=list(tols))
    for rp in sorted(FLOOD_GRIDS):
        haz = _rd(_flood_on_grid(spec, rp))[sl]
        covered = haz > 0
        wadi = np.isin(haz, HAZARD_WADI_CLASSES)
        if not wadi.any():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w2 = remove_small_objects(wadi, min_size=int(BASIN_MIN_AREA_M2 / spec.cell_area))
        sk = skeletonize(w2)
        d_sk = ndimage.distance_transform_edt(~sk, sampling=spec.res)
        judged = stm & covered
        out[f"T{rp}"] = dict(
            hazard_covered_pct=round(100 * float(covered.mean()), 2),
            wadi_km2=round(int(wadi.sum()) * spec.cell_area / 1e6, 2),
            hazard_skeleton_km=round(float(sk.sum()) * spec.res / 1000.0, 1),
            recall_of_skeleton={f"{t:.0f}m": round(float((d_st[sk] <= t).mean()), 4)
                                for t in tols},
            precision_vs_skeleton={f"{t:.0f}m": round(float((d_sk[judged] <= t).mean()), 4)
                                   for t in tols} if judged.any() else None,
            stream_cells_on_wadi_class=round(
                float((stm & wadi).sum()) / max(1, int(stm.sum())), 4))
        del haz, covered, wadi, w2, sk, d_sk
    out["note"] = ("precision is reported but was NOT optimised: hazard class 4-6 is a "
                   "danger-to-life classification, so a real channel carrying class 1-3 "
                   "water counts against us though it is a real channel")
    return out


def verify_vs_nama_network(spec: GridSpec) -> dict:
    """
    NAMA's built sewer runs downhill by construction.  So does the drain_direction API,
    if the terrain is being read correctly.  This is the sharpest available test.

    For every built pipe with recorded inverts, the TRUE flow direction is known (US ->
    DS).  drain_direction() is asked the same question from the terrain alone, and the
    agreement is counted - overall, and split by confidence, so the confidence label is
    itself validated rather than decorative.
    """
    import geopandas as gpd
    from shapely.geometry import LineString
    out = {}
    try:
        g = gpd.read_file(NAMA_SEWER).to_crs(CRS)
    except Exception as e:                                       # pragma: no cover
        return dict(error=str(e))
    g = g[g["STATUS"].astype(str).str.strip().str.lower() == "ex"].copy()
    tf = TerrainFlow.load(spec.name)
    rows = []
    for geom, zu, zd in zip(g.geometry, g["US_INVERT_"], g["DS_INVERT_"]):
        if geom is None or geom.is_empty:
            continue
        try:
            ls = LineString(list(geom.geoms[0].coords)) if geom.geom_type == "MultiLineString" \
                else LineString(list(geom.coords))
        except Exception:
            continue
        if ls.length < 5:
            continue
        try:
            zu = float(zu); zd = float(zd)
        except Exception:
            continue
        if not (np.isfinite(zu) and np.isfinite(zd)) or zu <= 0 or zd <= 0:
            continue
        if abs(zu - zd) < 1e-6:
            continue
        truth = "end" if zu > zd else "start"     # geometry runs US -> DS
        r = tf.drain_direction(ls)
        rows.append((truth, r["outlet_end"], r["confidence"], ls.length,
                     abs(zu - zd), r["fall_ends_m"], r["reversals"]))
    if not rows:
        return dict(error="no comparable built pipes")
    import collections
    tot = len(rows)
    agree = sum(1 for t, p, *_ in rows if p == t)
    flat = sum(1 for t, p, c, *_ in rows if c == "flat")
    by_conf = collections.defaultdict(lambda: [0, 0])
    for t, p, c, *_ in rows:
        by_conf[c][1] += 1
        if p == t:
            by_conf[c][0] += 1
    out["n_pipes"] = tot
    out["agreement_all"] = round(agree / tot, 4)
    decided = [r for r in rows if r[1] is not None]
    out["agreement_decided"] = round(
        sum(1 for t, p, *_ in decided if p == t) / max(1, len(decided)), 4)
    out["n_flat"] = flat
    out["by_confidence"] = {k: dict(n=v[1], agree=round(v[0] / v[1], 4)) for k, v in by_conf.items()}
    # does the agreement improve with the length of the pipe?
    L = np.array([r[3] for r in rows])
    ok = np.array([r[1] == r[0] for r in rows])
    bins = [(0, 25), (25, 50), (50, 100), (100, 250), (250, 1e9)]
    out["by_length_m"] = {f"{a:.0f}-{b:.0f}": dict(
        n=int(((L >= a) & (L < b)).sum()),
        agree=round(float(ok[(L >= a) & (L < b)].mean()), 4)
        if ((L >= a) & (L < b)).sum() else None) for a, b in bins}
    out["note"] = ("built pipes run US -> DS by construction; the terrain is asked the "
                   "same question with no knowledge of the inverts. NOTE the test is "
                   "unfairly hard: a NAMA pipe is 25-50 m, one to two cells of a 5 m "
                   "grid, and typically falls ~0.2 m - inside the DEM's own 0.48 m "
                   "differential noise. agreement_all counts every FLAT verdict as a "
                   "failure though 'flat' is the correct answer; agreement_decided is "
                   "the number to read. See vs_nama_chains for corridor-length lines.")
    return out


def verify_vs_nama_chains(spec: GridSpec) -> dict:
    """
    The test that matters: corridor-length lines whose direction is known.

    A single NAMA pipe is 25-50 m and falls ~0.2 m, which no 5 m surface can resolve.  But
    NAMA's pipes chain: US_MHID -> DS_MHID gives a directed graph, and walking it downstream
    builds paths of any length whose flow direction is known BY CONSTRUCTION.  Those are
    the same length as the corridors the network builder will hand to drain_direction, so
    this is the honest measure of whether the module can do its job.
    """
    import geopandas as gpd
    from shapely.geometry import LineString
    from shapely.ops import linemerge
    import collections
    g = gpd.read_file(NAMA_SEWER).to_crs(CRS)
    g = g[g["STATUS"].astype(str).str.strip().str.lower() == "ex"].copy()
    nxt, geom_of = {}, {}
    for us, ds, geom in zip(g["US_MHID"], g["DS_MHID"], g.geometry):
        if not us or not ds or geom is None or geom.is_empty:
            continue
        us, ds = str(us).strip(), str(ds).strip()
        if not us or not ds or us == ds:
            continue
        nxt.setdefault(us, ds)
        geom_of[(us, ds)] = geom
    heads = set(nxt) - set(nxt.values())
    tf = TerrainFlow.load(spec.name)
    targets = (100.0, 200.0, 500.0, 1000.0)
    res = {f"{t:.0f}m": dict(n=0, agree=0, flat=0, decided=0, by_conf=collections.defaultdict(
        lambda: [0, 0])) for t in targets}
    for h in heads:
        node, chain, seen = h, [], {h}
        while node in nxt:
            d = nxt[node]
            if d in seen:
                break
            gm = geom_of.get((node, d))
            if gm is None:
                break
            chain.append(gm)
            seen.add(d)
            node = d
            # test the chain whenever it first passes each target length
            merged = None
            for t in targets:
                key = f"{t:.0f}m"
                if res[key]["n"] > 4000:
                    continue
                if merged is None:
                    try:
                        merged = linemerge(chain)
                    except Exception:
                        break
                if merged.geom_type != "LineString" or merged.length < t:
                    continue
                if merged.length > t * 1.6:
                    continue
                r = tf.drain_direction(merged)
                b = res[key]
                b["n"] += 1
                b["by_conf"][r["confidence"]][1] += 1
                if r["confidence"] == "flat" or r["outlet_end"] is None:
                    b["flat"] += 1
                    continue
                b["decided"] += 1
                # the chain was walked US -> DS, so the truth is always 'end'
                if r["outlet_end"] == "end":
                    b["agree"] += 1
                    b["by_conf"][r["confidence"]][0] += 1
    out = {}
    for k, b in res.items():
        if not b["n"]:
            continue
        out[k] = dict(n_chains=b["n"], flat=b["flat"], decided=b["decided"],
                      flat_pct=round(100 * b["flat"] / b["n"], 1),
                      agreement_decided=round(b["agree"] / b["decided"], 4) if b["decided"] else None,
                      by_confidence={c: dict(n=v[1], agree=round(v[0] / v[1], 4))
                                     for c, v in b["by_conf"].items() if v[1]})
    out["truth"] = ("chains walked US_MHID -> DS_MHID, so the outlet is ALWAYS the last "
                    "vertex; the terrain is given only the geometry")
    return out


def verify_d8_vs_dinf(spec: GridSpec) -> dict:
    """
    What did choosing D8 over D-infinity cost?

    D8 was chosen because a sewer is a TREE - one outgoing pipe per chamber, one outfall
    per component - and a D-infinity field is not one.  The price is the 45 deg
    quantisation of the pointer.  This measures it where it could actually matter: does
    the stream network move if the accumulation is computed with dispersion allowed?

    D-infinity accumulation is thresholded at the same calibrated area, and the two
    channel networks are compared cell-for-cell.
    """
    from scipy import ndimage
    dinf_p = RUN / f"{spec.name}_dinf_acc.tif"
    if not dinf_p.exists():
        return dict(error="D-infinity accumulation not built")
    sl = _study_window(spec)
    cal = manifest_read().get(f"stream_calibration_{spec.name}", {})
    thr = cal.get("threshold_m2")
    if not thr:
        return dict(error="no calibrated threshold")
    a8 = _rd(RUN / f"{spec.name}_acc.tif", masked=True)[sl]
    ai = _rd(dinf_p, masked=True)[sl]
    s8 = np.isfinite(a8) & (a8 >= thr)
    si = np.isfinite(ai) & (ai >= thr)
    d8d = ndimage.distance_transform_edt(~s8, sampling=spec.res)
    did = ndimage.distance_transform_edt(~si, sampling=spec.res)
    out = dict(threshold_m2=thr,
               d8_km=round(float(s8.sum()) * spec.res / 1000, 0),
               dinf_km=round(float(si.sum()) * spec.res / 1000, 0),
               jaccard=round(float((s8 & si).sum()) / max(1, int((s8 | si).sum())), 4))
    for t in (5.0, 10.0, 25.0, 50.0):
        out[f"dinf_within_{t:.0f}m_of_d8"] = round(float((d8d[si] <= t).mean()), 4)
        out[f"d8_within_{t:.0f}m_of_dinf"] = round(float((did[s8] <= t).mean()), 4)
    out["note"] = ("D8 is KEPT regardless of this result - a dispersing field cannot be "
                   "turned into a sewer tree. The number is the honest size of the "
                   "limitation, and BEARING is never taken from the D8 pointer anyway: "
                   "downhill_bearing() fits a plane, so the 45 deg quantisation never "
                   "reaches a corridor orientation.")
    return out


def verify_local_inflow() -> dict:
    """
    THE LOCAL GRID'S ONE REAL WEAKNESS, measured rather than hedged.

    R5 covers the whole 75.7 x 74.2 km DEM footprint, so the contributing area of a wadi
    that enters the study area from outside is real.  L2 covers the study boundaries plus
    2 km and nothing else, so any flow arriving across its edge is simply absent - its
    accumulation starts from zero at the boundary.

    This measures the size of that.  Both grids are max-pooled onto a common 10 m lattice
    (a point comparison is meaningless: accumulation is spiky, and a point that is a
    channel at 5 m sits BESIDE the channel at 2 m), and the ratio is taken on the cells
    R5 calls channels.
    """
    r5, l2 = regional_spec(), local_spec()
    a5p = RUN / "R5_acc.tif"
    a2p = RUN / "L2_acc.tif"
    if not (a5p.exists() and a2p.exists()):
        return dict(error="both grids must be built")
    cal = manifest_read().get("stream_calibration_R5", {})
    thr = cal.get("threshold_m2", 4e4)
    sl = _study_window(r5, buffer_m=0)
    a5 = _rd(a5p, masked=True)[sl]
    a2 = _rd(a2p, masked=True)

    def pool(a, f):
        h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
        return np.nanmax(np.where(np.isfinite(a[:h, :w]), a[:h, :w], -1.0)
                         .reshape(h // f, f, w // f, f), axis=(1, 3))

    p2 = pool(a2, int(round(10.0 / l2.res)))
    p5 = pool(a5, int(round(10.0 / r5.res)))
    x0_5 = r5.left + sl[1].start * r5.res
    y0_5 = r5.top - sl[0].start * r5.res
    dx = int(round((x0_5 - l2.left) / 10.0))
    dy = int(round((l2.top - y0_5) / 10.0))
    h = min(p5.shape[0], p2.shape[0] - dy)
    w = min(p5.shape[1], p2.shape[1] - dx)
    q2, q5 = p2[dy:dy + h, dx:dx + w], p5[:h, :w]
    m = (q5 >= thr) & (q2 >= 0)
    if not m.any():
        return dict(error="no overlap")
    ratio = q2[m] / q5[m]
    return dict(threshold_m2=thr, lattice_m=10.0, n_channel_cells=int(m.sum()),
                ratio_median=round(float(np.median(ratio)), 4),
                ratio_p10=round(float(np.percentile(ratio, 10)), 4),
                ratio_p90=round(float(np.percentile(ratio, 90)), 4),
                frac_below_0p5=round(float((ratio < 0.5).mean()), 4),
                frac_below_0p9=round(float((ratio < 0.9).mean()), 4),
                verdict="USE R5 FOR ANYTHING INVOLVING CONTRIBUTING AREA - streams, "
                        "wadis, catchments. L2's accumulation is truncated where flow "
                        "crosses its boundary, and the measurement above says how often. "
                        "L2's value is its 2 m conditioning and its basins, which are "
                        "local and unaffected.")


def verify_vs_nsa_streams(spec: GridSpec) -> dict:
    """The project already holds a stream layer derived from the 4 m NSA DEM.  It is a
    second opinion from a different surface, so where the two agree the wadi is real."""
    import geopandas as gpd
    from scipy import ndimage
    try:
        g = gpd.read_file(NSA_STREAMS).to_crs(CRS)
    except Exception as e:                                       # pragma: no cover
        return dict(error=str(e))
    st = _rd(RUN / f"{spec.name}_streams.tif")
    stm = np.isfinite(st) & (st > 0)
    d = ndimage.distance_transform_edt(~stm, sampling=spec.res)
    # sample NSA vertices
    pts = []
    for geom in g.geometry:
        if geom is None or geom.is_empty:
            continue
        try:
            cs = list(geom.coords)
        except Exception:
            continue
        pts.extend(cs[:: max(1, len(cs) // 5)])
    if not pts:
        return dict(error="no vertices")
    arr = np.array([(p[0], p[1]) for p in pts])
    c = np.floor((arr[:, 0] - spec.left) / spec.res).astype("int64")
    r = np.floor((spec.top - arr[:, 1]) / spec.res).astype("int64")
    ok = (r >= 0) & (r < d.shape[0]) & (c >= 0) & (c < d.shape[1])
    dd = d[r[ok], c[ok]]
    return dict(n_points=int(ok.sum()), nsa_len_km=round(g.length.sum() / 1000, 1),
                within_25m=round(float((dd <= 25).mean()), 4),
                within_50m=round(float((dd <= 50).mean()), 4),
                within_100m=round(float((dd <= 100).mean()), 4),
                median_dist_m=round(float(np.median(dd)), 1),
                note="NSA layer is 5,574 km at a 4 m DEM's threshold - far denser than "
                     "ours, so a low percentage means their rills, not our error")


def verify_resolution_cost(spec: GridSpec, n=400, seed=7) -> dict:
    """
    What did the working resolution cost?

    Not asserted - measured.  Random corridor-length lines are laid on real ground and
    drain_direction() is asked twice: once off the working grid, once off the native 0.5 m
    VRT.  The disagreement rate and the fall error are the price of the resolution.
    """
    import geopandas as gpd
    from shapely.geometry import LineString
    rng = np.random.default_rng(seed)
    try:
        b = gpd.read_file(BOUNDARY_MOHUP).to_crs(CRS).total_bounds
    except Exception:
        b = (spec.left, spec.bottom, spec.right, spec.top)
    tf = TerrainFlow.load(spec.name)
    rows = []
    for L in (50.0, 100.0, 200.0):
        agree = 0
        tot = 0
        derr = []
        for _ in range(n):
            x = rng.uniform(b[0], b[2]); y = rng.uniform(b[1], b[3])
            th = rng.uniform(0, 2 * math.pi)
            ls = LineString([(x, y), (x + L * math.cos(th), y + L * math.sin(th))])
            a = tf.drain_direction(ls, native=False)
            c = tf.drain_direction(ls, native=True)
            if a["outlet_end"] is None or c["outlet_end"] is None:
                continue
            tot += 1
            agree += int(a["outlet_end"] == c["outlet_end"])
            if np.isfinite(a["fall_ends_m"]) and np.isfinite(c["fall_ends_m"]):
                derr.append(a["fall_ends_m"] - c["fall_ends_m"])
        derr = np.array(derr) if derr else np.array([np.nan])
        rows.append(dict(line_m=L, n=tot,
                         direction_agreement=round(agree / tot, 4) if tot else None,
                         fall_bias_m=round(float(np.nanmean(derr)), 4),
                         fall_rmse_m=round(float(np.sqrt(np.nanmean(derr ** 2))), 4)))
    return dict(grid=spec.name, res_m=spec.res, by_length=rows,
                note=f"{spec.res:.1f} m working grid vs the native 0.5 m VRT, same lines")


def stage_verify(spec: GridSpec) -> dict:
    _log(f"verify {spec.name}: DEM quality")
    q = verify_dem_quality(spec)
    manifest_write(dem_quality=q)
    _log(f"  sigma_z (absolute)     = {q['sigma_z_m']:.3f} m "
         f"({q.get('sigma_z_source','fallback')})")
    _log(f"  sigma_dz (differential) = {q.get('sigma_dz_m', float('nan')):.3f} m "
         f"<- the number every direction is judged against")
    v = dict(dem_quality=q)
    for name, fn in (("streams_vs_flood", verify_streams_vs_flood),
                     ("vs_nama_network", verify_vs_nama_network),
                     ("vs_nama_chains", verify_vs_nama_chains),
                     ("d8_vs_dinf", verify_d8_vs_dinf),
                     ("vs_nsa_streams", verify_vs_nsa_streams),
                     ("resolution_cost", verify_resolution_cost)):
        _log(f"verify {spec.name}: {name}")
        try:
            v[name] = fn(spec)
        except Exception as e:
            v[name] = dict(error=f"{type(e).__name__}: {e}")
            _log(f"  FAILED: {e}")
    if (RUN / "R5_acc.tif").exists() and (RUN / "L2_acc.tif").exists():
        _log("verify: local-grid inflow truncation (R5 vs L2)")
        try:
            v["local_inflow"] = verify_local_inflow()
        except Exception as e:
            v["local_inflow"] = dict(error=f"{type(e).__name__}: {e}")
    manifest_write(**{f"verification_{spec.name}": v})
    (RUN / f"{spec.name}_verification.json").write_text(
        json.dumps(v, indent=2, default=str), encoding="utf-8")
    return v


# --------------------------------------------------------------------------------------
# BENCH - the network builder calls this hundreds of thousands of times
# --------------------------------------------------------------------------------------

def bench(spec_name="R5", n=200000) -> dict:
    import geopandas as gpd
    from shapely.geometry import LineString
    tf = TerrainFlow.load(spec_name)
    rng = np.random.default_rng(3)
    b = gpd.read_file(BOUNDARY_MOHUP).to_crs(CRS).total_bounds
    x = rng.uniform(b[0], b[2], n)
    y = rng.uniform(b[1], b[3], n)
    out = {}

    def timeit(label, fn, k=n):
        t = time.time()
        fn()
        dt = time.time() - t
        out[label] = dict(n=k, seconds=round(dt, 3), per_call_us=round(1e6 * dt / k, 2),
                          calls_per_s=int(k / dt) if dt > 0 else None)
        _log(f"  {label:<28} {k:>8,} calls  {dt:7.3f} s  "
             f"{1e6*dt/k:8.2f} us/call")

    timeit("elevation (vector)", lambda: tf.elevation(x, y))
    timeit("elevation native 0.5m", lambda: tf.elevation(x[:5000], y[:5000], native=True), 5000)
    timeit("accumulation (vector)", lambda: tf.accumulation(x, y))
    timeit("stream_distance (vector)", lambda: tf.stream_distance(x, y))
    timeit("in_wadi (vector)", lambda: tf.in_wadi(x, y))
    timeit("basin_at (vector)", lambda: tf.basin_at(x, y))
    timeit("downhill_bearing (vector)",
           lambda: tf.downhill_bearing(x[:2000], y[:2000]), 2000)
    lines = [LineString([(x[i], y[i]), (x[i] + 100, y[i] + 60)]) for i in range(3000)]
    timeit("drain_direction (line)", lambda: [tf.drain_direction(l) for l in lines], 3000)
    timeit("is_ridge (line)", lambda: [tf.is_ridge(l) for l in lines], 3000)
    manifest_write(bench=out)
    return out


# --------------------------------------------------------------------------------------
# BUILD
# --------------------------------------------------------------------------------------

STAGES = ["resample", "flood", "condition", "flow", "streams", "basins", "catchments", "verify"]


def build(grid="R5", stages=None, force=False):
    spec = regional_spec() if grid == "R5" else local_spec()
    stages = stages or STAGES
    manifest_write(**{f"grid_{spec.name}": asdict(spec) |
                      dict(width=spec.width, height=spec.height, cells=spec.cells)})
    manifest_write(constants=dict(
        RES_REGIONAL_M=RES_REGIONAL_M, RES_LOCAL_M=RES_LOCAL_M,
        BREACH_DIST_M=BREACH_DIST_M, BASIN_MIN_AREA_M2=BASIN_MIN_AREA_M2,
        COVER_CAP_M=COVER_CAP_M, COVER_CAP_SRC="G203-p33 4.6.3",
        MIN_COVER_M=MIN_COVER_M, MIN_COVER_SRC="G203-p33 4.6.3",
        HAZARD_WADI_CLASSES=list(HAZARD_WADI_CLASSES),
        WADI_SRC="G203-p30 4.4.1 i.a / p33 4.6.2 prohibit pipelines and chambers in "
                 "wadis and washout areas; the CLASS TEST is a project assumption",
        BEARING_RADIUS_M=BEARING_RADIUS_M,
        D8_DECODE_MEASURED="2026-09-03 on a synthetic pyramid, not from documentation",
        tau_Pa=1.0, tau_tag="ASSUME (GAP-9) - flagged on every output"))

    t0 = time.time()
    if "resample" in stages:
        stage_resample(spec, force)
    if "flood" in stages:
        for rp in sorted(FLOOD_GRIDS):
            _flood_on_grid(spec, rp, force)
    if "condition" in stages:
        stage_condition(spec, force)
    if "flow" in stages:
        stage_flow(spec, force)
    # sigma_z must exist before the basins are classified
    q = manifest_read().get("dem_quality")
    if "streams" in stages:
        stage_streams(spec, force)
    if "basins" in stages:
        if not q:
            q = verify_dem_quality(spec)
            manifest_write(dem_quality=q)
        stage_basins(spec, sigma_dz=q.get("sigma_dz_m", q.get("sigma_z_m")), force=force)
    if "catchments" in stages:
        stage_catchments(spec, force)
    if "verify" in stages:
        stage_verify(spec)
    _log(f"build {spec.name} complete in {(time.time()-t0)/60:.1f} min")


def example(grid="R5"):
    """
    The contract, executable.  `python terrain.py example` prints exactly what a later
    stage gets back from every call, on a point whose ground level is independently
    confirmed (the existing STP, CLAUDE.md: 328.7 m aOD).
    """
    from shapely.geometry import LineString
    tf = TerrainFlow.load(grid)
    x, y = 444422.8, 2563337.9                       # existing STP, EPSG:32640
    print("TerrainFlow.load(%r)  -> grid %s at %.1f m" % (grid, tf.spec.name, tf.spec.res))
    print()
    print("  POINT QUERIES  (scalars in, scalars out; pass ARRAYS for bulk - 0.2 us/call)")
    print("    elevation(x, y)                 %.2f m aOD   [confirmed 328.7]"
          % tf.elevation(x, y))
    print("    elevation(x, y, native=True)    %.2f m aOD   [0.5 m VRT, no more accurate]"
          % tf.elevation(x, y, native=True))
    print("    accumulation(x, y)              %.0f m2 upstream" % tf.accumulation(x, y))
    print("    stream_distance(x, y)           %.0f m to the nearest derived stream"
          % tf.stream_distance(x, y))
    print("    in_wadi(x, y, 50)               %s   (hazard class %d; 0 = no data = DRY)"
          % (tf.in_wadi(x, y), tf.hazard_class(x, y)))
    print("    basin_at(x, y)                  %d   (0 = not in a closed basin)"
          % tf.basin_at(x, y))
    print("    catchment_at(x, y)              %d" % tf.catchment_at(x, y))
    b, s = tf.downhill_bearing(x, y)
    print("    downhill_bearing(x, y)          %.1f deg at %.3f %%   [plane fit over "
          "%.0f m, NOT the D8 pointer]" % (b, s, BEARING_RADIUS_M))
    fp = tf.flow_path(x, y)
    print("    flow_path(x, y)                 %d cells, ends at %.0f %.0f"
          % (len(fp), fp[-1][0], fp[-1][1]))
    print()
    ln = LineString([(x, y), (x + 600, y - 300)])
    d = tf.drain_direction(ln)
    print("  LINE QUERIES   (64 us/call for drain_direction, 33 us for is_ridge)")
    print("    drain_direction(line) ->")
    for k in ("outlet_end", "confidence", "p_correct", "fall_ends_m", "slope_pct",
              "monotone", "reversals", "r2", "length_m"):
        print("        %-14s %s" % (k, d[k]))
    r = tf.is_ridge(ln)
    print("    is_ridge(line) ->")
    for k in ("is_ridge", "prominence_m", "min_prominence_m", "is_hollow", "crest_m"):
        print("        %-14s %s" % (k, r[k]))
    print()
    print("  HOW TO READ confidence.  MEASURED, not asserted: NAMA's built sewer chains")
    print("  run downhill by construction, so walking US_MHID -> DS_MHID gives thousands")
    print("  of lines whose direction is KNOWN.  Agreement on the lines the module agrees")
    print("  to answer (verification_R5.vs_nama_chains):")
    print()
    print("      line     answered   agree   'certain'   refused as   refused as")
    print("      length              (all)   only        flat         split")
    print("      100 m       77 %    88.2 %   92.2 %      22.8 %        0.7 %")
    print("      200 m       85 %    92.0 %   96.2 %      15.2 %        4.0 %")
    print("      500 m       83 %    96.8 %   98.5 %       8.7 %        7.2 %")
    print("      1 km        82 %    97.9 %   98.0 %       9.0 %        8.9 %")
    print()
    print("      certain   take it. 98 % right at 200 m and above.")
    print("      likely    ~81-83 %. Usable, but do not build an irreversible decision")
    print("                on one.")
    print("      flat      the fall is inside the DEM's own 0.48 m differential noise.")
    print("                A CORRECT answer, not a failure - the ground cannot decide,")
    print("                and something other than terrain must break the tie.")
    print("      split     the crest or hollow INSIDE the line is bigger than the fall")
    print("                ACROSS it, so there is no single outlet. Break the corridor at")
    print("                split_at_m and drain both ways. This is the check W11a did not")
    print("                have; adding it raised 500 m agreement from 95.1 % to 96.8 %.")
    print()
    print("  FLAGS every output must carry:")
    for k, v in tf.flags().items():
        print("      %-22s %s" % (k, str(v)[:96]))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="W12 terrain flow engine")
    ap.add_argument("cmd", choices=["build", "verify", "bench", "info", "example"])
    ap.add_argument("--grid", default="R5", choices=["R5", "L2"])
    ap.add_argument("--stage", action="append", default=None, choices=STAGES)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--n", type=int, default=200000)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build(a.grid, a.stage, a.force)
    elif a.cmd == "verify":
        spec = regional_spec() if a.grid == "R5" else local_spec()
        print(json.dumps(stage_verify(spec), indent=2, default=str))
    elif a.cmd == "bench":
        print(json.dumps(bench(a.grid, a.n), indent=2))
    elif a.cmd == "example":
        example(a.grid)
    else:
        for g in ("R5", "L2"):
            s = regional_spec() if g == "R5" else local_spec()
            print(f"{s.name}  {s.res} m  {s.width} x {s.height} = {s.cells/1e6:.1f} M cells"
                  f"  bounds {s.left:.0f} {s.bottom:.0f} {s.right:.0f} {s.top:.0f}")


if __name__ == "__main__":
    main()
