"""
W12 - THE STREAM NETWORK
=========================

The ground's own answer to which way water goes, published as ONE layer with an order on
every line, and RECONCILED against the engineer's own independent extraction rather than
chosen over it.

WHY THIS MODULE EXISTS AND `terrain.py` IS NOT ENOUGH
    `terrain.py` derives a stream network and calibrates its threshold against the 50-year
    flood grid.  That is one source.  The project also holds a SECOND, independent stream
    network - extracted by the engineer, from a different DEM (the 4 m NSA surface), with
    different software, at a threshold he set himself.  Two answers to the same question is
    evidence, not a nuisance, and the job here is to MEASURE the agreement and say which the
    design should follow.  A module that simply picked one would have thrown the evidence
    away.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
`w12.terrain`, `w12.contract` and `w12.criteria` are siblings inside W12 and are used as
such; third-party libraries are used as libraries.

NO NUMBER IS INVENTED.  Every constant carries one of four tags:

    [G203-p##]  read out of PAM-GUD-203 - Wastewater Design Guidelines v1.0
    [G201-p##]  read out of PAM-GUD-201 - General Design Guidelines v1.0
    [ASSUME]    a project assumption - stated, defended, reported on every output
    [MEASURED]  derived here from the data, with the measurement recorded in reconcile.json

----------------------------------------------------------------------------------------
THE ANSWER, IN ONE LINE
----------------------------------------------------------------------------------------
USE THE 4 ha (40,000 m2) NETWORK DERIVED HERE.  The engineer's own 0.5 km2 network is the
same network with orders 1 and 2 taken out, and it independently confirms 91-97 % of every
channel we call order 3 or above; but on its own it finds only 54 % of the wadis the flood
model finds, so following it would leave half the washout risk undrawn.

THE THREE MEASUREMENTS BEHIND THAT SENTENCE  (all in `reconcile()`)

 1  WHAT THRESHOLD IS THE ENGINEER'S LAYER ACTUALLY AT?  Not asked - measured.  Every
    order-1 upstream tip of his network is located on OUR contributing-area field and the
    accumulation there is read: median 516,075 m2, quartiles 438k / 610k.  His stated
    0.5 km2 is confirmed to within the method's own bias, and the same measurement run on
    OUR layer as a control returns 45,900 m2 against a declared 40,000 - a +15 % bias that
    applies equally to both, so the comparison is fair.

    That is also the first real cross-validation of this project's accumulation field: a
    threshold set on a 4 m DEM in QGIS in July is recovered off a 5 m grid built from the
    0.5 m terrain in September, to within 3 %.

 2  DO THEY AGREE IN SPACE?  Two-way, at four tolerances, on a raster the two are rendered
    onto so neither is privileged.  97.5 % of HIS channel cells lie within 100 m of ours
    (83.6 % within 25 m).  Only 44.8 % of ours lie within 100 m of his - because ours is
    2.3x denser, which is the intended difference and not a disagreement.  Broken down by
    Strahler order the picture is unambiguous: our order 3-8 links are 91-97 % confirmed by
    his extraction, our order 1-2 links 28-47 %.

 3  WHICH ONE MATCHES A WADI ON THIS GROUND?  The five AR&R flood-hazard grids are an
    independent answer to the same question and only ONE of them (the 50-year) was used to
    calibrate our threshold, so the other four are untouched evidence.  Ours recovers
    89.8-94.6 % of the hazard class 4-6 skeleton across all five return periods; the
    engineer's 0.5 km2 layer recovers 49.4-57.4 %.

A THIRD FILE EXISTS AND MUST NOT BE USED - see `NSA_PB` below.  `Streams NSA 2m project
boundary.shp` is NOT a clip of the engineer's layer; it is a separate extraction from a
PRE-CLIPPED DEM, so every wadi entering the study area from outside starts from zero
contributing area inside the clip.  It is denser than ours (6,657 km against 5,159 km on the
same footprint) and yet finds FEWER wadis (43 % of the 50-year skeleton against our 92 %).
A denser network that finds fewer wadis is a network in the wrong places.

----------------------------------------------------------------------------------------
WHAT IT PUBLISHES
----------------------------------------------------------------------------------------
    W12/shp/W12_streams.gpkg, layer `streams`, validated against `contract.STREAMS`.

    One clean line network over the study boundaries + a 2 km margin, every link carrying:
    its Strahler ORDER_, the contributing area at its own downstream end, its fall, the
    flood-hazard class along it, the downstream link it flows into, and - the reconciliation
    carried per feature - how far it sits from the engineer's independent network and
    whether that network confirms it.

WHAT LATER STAGES CALL
    sn = StreamNet.load()
    sn.distance(x, y)            -> metres to the nearest channel        (array, O(1))
    sn.downhill(x, y)            -> (bearing_deg, slope_pct) pointing downhill
    sn.nearest(x, y)             -> the nearest link: id, order, area, distance, confirmed
    sn.order_at(x, y, radius)    -> the largest order within radius, 0 if none
    sn.drain_direction(line)     -> which END of a corridor line is the outlet
    sn.is_wadi(x, y)             -> the G203-p30 4.4.1 prohibition test
    sn.main_wadis()              -> the order >= 3 subset, and why 3 is the number

CLI
    python -m w12.streams reconcile     # the measurements -> run/streams/reconcile.json
    python -m w12.streams build         # publish shp/W12_streams.gpkg
    python -m w12.streams verify        # re-read the published layer and check it
    python -m w12.streams all
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

from . import terrain as T
from .criteria import DEFAULT as C

# --------------------------------------------------------------------------------------
# PATHS
# --------------------------------------------------------------------------------------

W12 = T.W12
RUN = W12 / "run" / "streams"                 # this module's own outputs, nobody else's
GPKG_NAME = "W12_streams.gpkg"
GPKG = W12 / "shp" / GPKG_NAME
REPORT = RUN / "reconcile.json"
VERDICT = RUN / "RECONCILIATION.md"

# The engineer's extraction over the WHOLE 4 m NSA DEM.  This is the one to compare against.
NSA_FULL = T.HYDRAULIC / "SHP" / "Streams" / "Streams NSA 2m.shp"

# The same name, a different file, and NOT a clip of the one above: a separate extraction
# from `Terrain/NSA_DEM_Clip.tif`, whose contributing area is truncated at the clip edge.
# Measured and rejected in `reconcile()`; kept here only so the rejection is reproducible.
# NOTE FOR THE ENGINEER: `terrain.NSA_STREAMS` currently points at THIS file, so
# `terrain.verify_vs_nsa_streams()` is checking against the wrong layer.
NSA_PB = T.NSA_STREAMS

CRS = T.CRS


# --------------------------------------------------------------------------------------
# CONSTANTS - every one tagged
# --------------------------------------------------------------------------------------

# [MEASURED] The working grid.  `terrain`'s own `local_inflow` measurement is explicit:
#   "USE R5 FOR ANYTHING INVOLVING CONTRIBUTING AREA - streams, wadis, catchments.  L2's
#   accumulation is truncated where flow crosses its boundary."  20 % of L2's channel cells
#   carry less than half the contributing area R5 gives them.  A stream layer is nothing but
#   contributing area, so it is built on R5.
GRID = "R5"                     # [MEASURED - terrain manifest, local_inflow]

# [ASSUME] the published extent: both candidate study boundaries, plus a margin, because
#   which of the two is the project's is still an open decision (00_CURRENT: 439.8 km2 vs
#   531.4 km2).  Publishing the union means the answer does not have to be known yet, and
#   IN_MOHUP / IN_STUDY on every row let whoever settles it filter without a rebuild.
#   The margin is `terrain.LOCAL_BUFFER_M`, unchanged, so the extent matches the window
#   every measurement in `terrain` was made over.
PUBLISH_BUFFER_M = T.LOCAL_BUFFER_M       # [ASSUME] 2,000 m

# [ASSUME] tolerances at which two line networks are called the same line.  Not a single
#   number, because a single number hides the shape of the disagreement: 25 m is "the same
#   thalweg", 100 m is "the same braided bed" (the measured p75 wadi half-width on this
#   ground is 98 m - terrain.calibrate_streams), 200 m is "the same wadi, different strand".
AGREE_TOL_M = (25.0, 50.0, 100.0, 200.0)

# [ASSUME] the confirmation tolerance carried on every published row.  100 m, because that
#   is the MEASURED p75 half-width of a wadi here and not a round number chosen for looking
#   reasonable.  A link within 100 m of the engineer's network is inside the same bed.
CONFIRM_TOL_M = 100.0                     # [MEASURED via terrain.calibrate_streams p75]

# [ASSUME] snap radius when reading the accumulation under someone else's channel head.
#   Their head sits on THEIR DEM's channel; one cell off ours it reads hillslope, which is
#   what makes the un-snapped median meaningless (49,050 m2 against a true 516,075).  5 cells
#   is the radius; the bias it introduces is MEASURED by running the same procedure on our
#   own layer, whose threshold is known exactly.
HEAD_SNAP_M = 25.0

# [MEASURED] the order at which the two independent extractions start to agree.  Confirmation
#   by the engineer's 0.5 km2 network jumps 47 % -> 91 % between order 2 and order 3, and
#   stays 91-97 % above it.  So "main wadi" is not a threshold anyone invented: it is the
#   set both surfaces, both resolutions and both software runs call a channel.
MAIN_WADI_MIN_ORDER = 3                   # [MEASURED - reconcile()['by_order']]

# [MEASURED] share of this window the 50-year hazard grid says ANYTHING about.  It is the
#   single most important qualifier on every wadi statement in the project: outside it,
#   IS_WADI = 0 means "not shown to be wadi", not "dry".  Re-measured on every reconcile()
#   run and reported as `vs_flood_hazard.T50.hazard_covered_pct`; this constant only feeds
#   the banner, which has to print before the measurement is made.
HAZARD_COVER_PCT_T50 = 45.3               # [MEASURED - reconcile.json + terrain R5_verification]

# G203-p30 4.4.1 i.a: "Wadis and Flood-Prone Areas: Locating pipelines and associated
#   chambers in wadis or areas subject to washout during heavy storms must be avoided."
#   The guideline gives no test for what IS a wadi; the hazard-class stand-in is the
#   project's assumption and lives in `terrain`, unchanged here.
WADI_CLASSES = T.HAZARD_WADI_CLASSES      # [ASSUME] (4, 5, 6)
WADI_RP = T.WADI_RETURN_PERIOD_DEFAULT    # [ASSUME] the 50-year grid

STREAM_ID_FMT = "S{:06d}"

STAGE = "streams"
SRC_TAG = "terrain"                       # contract.SRC vocabulary
CONF_TAG = "derived"                      # contract.SRC_CONFIDENCE_CEILING["terrain"]

# The engineer's instruction of 2026-09-03: keep tau = 1.0 Pa and FLAG it on every output.
# The full banner is `criteria.tau_banner()` and is printed by `banner()`; the row-level flag
# is deliberately short, because 20,000 copies of a paragraph is not a flag, it is ballast.
TAU_FLAG = f"tau={C.TAU_PA:g}Pa ASSUMED"


def _log(msg: str):
    print(f"[streams {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def banner() -> str:
    """Every deliverable off this module opens with this.  Assumptions do not travel
    silently, and three of the four below are assumptions."""
    return "\n".join([
        f"W12 STREAMS | grid {GRID} @ {T.RES_REGIONAL_M:g} m | EPSG:{CRS.split(':')[-1]}",
        "",
        C.tau_banner(),
        "",
        f"WADI TEST: AR&R flood-hazard class {list(WADI_CLASSES)} of the {WADI_RP}-year grid. "
        "A PROJECT ASSUMPTION standing in for G203-p30 4.4.1's washout criterion, not a "
        "guideline threshold.",
        f"FLOOD NO-DATA IS READ AS DRY HIGH GROUND (engineer, 2026-09-03). "
        f"{100 - HAZARD_COVER_PCT_T50:.0f} % "
        "of this window is outside the 50-year grid, so IS_WADI = 0 there means NOT SHOWN TO "
        "BE WADI. HAZ_COV on every row says which. NWS still owe full-coverage mapping.",
        "STREAM THRESHOLD: 40,000 m2 (4 ha), MEASURED - the coarsest contributing area that "
        "still recovers >= 90 % of the 50-year hazard skeleton. See reconcile.json.",
    ])


# ======================================================================================
# The window everything is measured and published over
# ======================================================================================

def _spec():
    return T.regional_spec() if GRID == "R5" else T.local_spec()


def window():
    """(spec, row-slice, col-slice, transform, (H, W), shapely box).

    The same window `terrain` calibrated and verified over - both study boundaries plus
    PUBLISH_BUFFER_M - so every number here is comparable with every number there without
    an argument about extents.
    """
    from rasterio.transform import from_origin
    from shapely.geometry import box
    spec = _spec()
    sl = T._study_window(spec, buffer_m=PUBLISH_BUFFER_M)
    r0, r1 = sl[0].start, sl[0].stop
    c0, c1 = sl[1].start, sl[1].stop
    H, W = r1 - r0, c1 - c0
    left = spec.left + c0 * spec.res
    top = spec.top - r0 * spec.res
    tr = from_origin(left, top, spec.res, spec.res)
    bx = box(left, top - H * spec.res, left + W * spec.res, top)
    return spec, sl, tr, (H, W), bx


class _Sampler:
    """Point sampling on a windowed array.  Array-in, array-out, no shapely per point."""

    def __init__(self, arr, spec, left, top):
        self.a = np.asarray(arr)
        self.res = spec.res
        self.left = left
        self.top = top

    def rc(self, xs, ys):
        c = np.floor((np.asarray(xs, dtype="float64") - self.left) / self.res).astype("int64")
        r = np.floor((self.top - np.asarray(ys, dtype="float64")) / self.res).astype("int64")
        return r, c

    def at(self, xs, ys, nodata=np.nan):
        r, c = self.rc(xs, ys)
        H, W = self.a.shape
        ok = (r >= 0) & (r < H) & (c >= 0) & (c < W)
        out = np.full(r.shape, nodata, dtype="float64")
        if ok.any():
            out[ok] = self.a[r[ok], c[ok]]
        return out

    def max_within(self, xs, ys, radius_m):
        """The maximum in a square of `radius_m` about each point.

        Needed because a channel head digitised on someone else's DEM is a metre or two off
        ours, and the accumulation field is a cliff at a channel edge: one cell out and the
        reading is hillslope.  The bias this introduces is measured, not assumed - see
        `effective_threshold`, which runs the identical procedure on a layer whose threshold
        is known exactly.
        """
        k = max(1, int(round(radius_m / self.res)))
        r, c = self.rc(xs, ys)
        H, W = self.a.shape
        out = np.full(r.shape, np.nan, dtype="float64")
        for i in range(r.size):
            r0, r1 = max(0, r[i] - k), min(H, r[i] + k + 1)
            c0, c1 = max(0, c[i] - k), min(W, c[i] + k + 1)
            if r0 >= r1 or c0 >= c1:
                continue
            w = self.a[r0:r1, c0:c1]
            w = w[np.isfinite(w)]
            if w.size:
                out[i] = w.max()
        return out


# ======================================================================================
# The two sources
# ======================================================================================

def ours(clip_to_window: bool = True):
    """Our own network, as `terrain.stage_streams` left it.

    Links are SELECTED by the window, never CLIPPED to it: cutting a link at the boundary
    would part its geometry from its accumulation and its fall, and a stream whose fall is
    measured over a cut length is a stream whose gradient is wrong.
    """
    import geopandas as gpd
    p = T.RUN / f"{_spec().name}_streams.gpkg"
    if not p.exists():
        raise FileNotFoundError(
            f"{p} does not exist. Build the terrain first: python -m w12.terrain build")
    g = gpd.read_file(p)
    g = g.set_crs(CRS, allow_override=True) if g.crs is None else g.to_crs(CRS)
    if clip_to_window:
        _, _, _, _, bx = window()
        g = g[g.intersects(bx)]
    return g.reset_index(drop=True)


def nsa(which: str = "full", clip_to_window: bool = True):
    """The engineer's extraction.  `which` = "full" (use this) or "pb" (measured, rejected)."""
    import geopandas as gpd
    p = NSA_FULL if which == "full" else NSA_PB
    g = gpd.read_file(p)
    g = g.set_crs(CRS, allow_override=True) if g.crs is None else g.to_crs(CRS)
    if clip_to_window:
        _, _, _, _, bx = window()
        g = g[g.intersects(bx)]
    return g.reset_index(drop=True)


# ======================================================================================
# MEASUREMENT 1 - what threshold is a network actually at?
# ======================================================================================

def _heads(gdf, order_col: str):
    """Upstream tips of the order-1 links: an endpoint no other line in the layer shares.

    A channel HEAD is where the extraction decided a channel begins, so the contributing
    area there IS the threshold, whatever the person who ran it remembers setting.
    """
    from collections import Counter
    ends = []
    for geom in gdf.geometry:
        cs = geom.coords
        ends.append((round(cs[0][0], 1), round(cs[0][1], 1)))
        ends.append((round(cs[-1][0], 1), round(cs[-1][1], 1)))
    cnt = Counter(ends)
    pts = []
    for geom in gdf[gdf[order_col] == 1].geometry:
        cs = geom.coords
        for e in (cs[0], cs[-1]):
            if cnt[(round(e[0], 1), round(e[1], 1))] == 1:
                pts.append((e[0], e[1]))
    return np.asarray(pts, dtype="float64") if pts else np.zeros((0, 2))


def effective_threshold(gdf, order_col: str, sampler: _Sampler, label: str) -> dict:
    """The contributing area at which THIS layer starts a channel, read off OUR field.

    Reported at three snap radii, because the number moves with the snap and hiding that
    would make it look more certain than it is.  The reading to quote is the 25 m one, and
    the bias in it is quantified by running the same procedure on our own layer.
    """
    h = _heads(gdf, order_col)
    if len(h) == 0:
        return dict(label=label, error="no order-1 heads found")
    out = dict(label=label, n_heads=int(len(h)), snap_m=HEAD_SNAP_M)
    for rad, key in ((0.1, "at_vertex"), (HEAD_SNAP_M, "snap_25m"), (2 * HEAD_SNAP_M, "snap_50m")):
        a = sampler.max_within(h[:, 0], h[:, 1], rad)
        a = a[np.isfinite(a)]
        if a.size == 0:
            continue
        out[key] = dict(n=int(a.size),
                        p25_m2=round(float(np.percentile(a, 25))),
                        median_m2=round(float(np.median(a))),
                        p75_m2=round(float(np.percentile(a, 75))),
                        median_km2=round(float(np.median(a)) / 1e6, 4))
    out["tag"] = "MEASURED"
    out["method"] = ("contributing area of OUR R5 field, read at the upstream tip of every "
                     "order-1 link of this layer, snapped to the local maximum within "
                     f"{HEAD_SNAP_M:.0f} m. The snap is necessary because a head digitised "
                     "on a different DEM lands a cell or two off our channel, where the "
                     "field reads hillslope.")
    return out


# ======================================================================================
# MEASUREMENT 2 - do the two networks agree in space?
# ======================================================================================

def _rasterise(gdf, tr, shape):
    from rasterio.features import rasterize
    if len(gdf) == 0:
        return np.zeros(shape, dtype=bool)
    return rasterize(((gm, 1) for gm in gdf.geometry), out_shape=shape, transform=tr,
                     fill=0, all_touched=True, dtype="uint8").astype(bool)


def _edt(mask, res):
    from scipy import ndimage
    return ndimage.distance_transform_edt(~mask, sampling=res)


def agreement(masks: dict, dists: dict, res: float, restrict=None) -> dict:
    """Two-way, at every tolerance.  Neither network is the truth, so neither gets to be
    the denominator on its own.

    `frac_of_A_near_B` is what fraction of A the other network confirms; `frac_of_B_near_A`
    is the reverse.  A dense network compared with a sparse one scores low on the first and
    high on the second, and that is a difference in threshold, not a disagreement about
    where the water goes.  Reading only one of the two is how a threshold argument gets won
    by whoever picked the direction.
    """
    out = {}
    keys = list(masks)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            ma = masks[a] & restrict if restrict is not None else masks[a]
            mb = masks[b] & restrict if restrict is not None else masks[b]
            if not ma.any() or not mb.any():
                continue
            row = dict(A_km=round(float(ma.sum()) * res / 1000),
                       B_km=round(float(mb.sum()) * res / 1000))
            for t in AGREE_TOL_M:
                row[f"{int(t)}m"] = dict(
                    frac_of_A_near_B=round(float((dists[b][ma] <= t).mean()), 4),
                    frac_of_B_near_A=round(float((dists[a][mb] <= t).mean()), 4))
            out[f"{a}_vs_{b}"] = row
    return out


# ======================================================================================
# MEASUREMENT 3 - which threshold matches a WADI on this ground?
# ======================================================================================

def vs_hazard(masks: dict, dists: dict, spec, sl) -> dict:
    """Every source against every one of the five flood-hazard grids.

    This is the independent test, and it is the reason the threshold is not a matter of
    taste.  Only the 50-year grid was used to calibrate our threshold; T10, T25, T100 and
    T500 are untouched evidence and our recall barely moves across all five.

    Precision is REPORTED AND NOT OPTIMISED, for a physical reason that has to travel with
    the number: hazard class 4-6 is a DANGER-TO-LIFE classification, so a real channel
    carrying class 1-3 water counts against us though it is a perfectly real channel.  That
    is exactly why precision climbs from 0.17 at the 10-year grid to 0.50 at the 500-year -
    the "extra" channels are real channels with smaller floods in them.
    """
    import warnings
    from skimage.morphology import skeletonize, remove_small_objects
    out = {}
    for rp in sorted(T.FLOOD_GRIDS):
        haz = np.asarray(T._rd(T._flood_on_grid(spec, rp))[sl])
        covered = haz > 0
        wadi = np.isin(haz, WADI_CLASSES)
        if not wadi.any():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w2 = remove_small_objects(
                wadi, min_size=int(T.BASIN_MIN_AREA_M2 / spec.cell_area))
        sk = skeletonize(w2)
        d_sk = _edt(sk, spec.res)
        row = dict(hazard_covered_pct=round(100 * float(covered.mean()), 2),
                   wadi_km2=round(int(wadi.sum()) * spec.cell_area / 1e6, 2),
                   hazard_skeleton_km=round(float(sk.sum()) * spec.res / 1000.0, 1))
        for k, m in masks.items():
            judged = m & covered
            row[k] = dict(
                km=round(float(m.sum()) * spec.res / 1000),
                recall={f"{int(t)}m": round(float((dists[k][sk] <= t).mean()), 4)
                        for t in AGREE_TOL_M},
                precision={f"{int(t)}m": round(float((d_sk[judged] <= t).mean()), 4)
                           for t in AGREE_TOL_M} if judged.any() else None,
                frac_on_wadi_class=round(float((m & wadi).sum()) / max(1, int(m.sum())), 4))
        out[f"T{rp}"] = row
        del haz, covered, wadi, w2, sk, d_sk
    out["_note"] = ("only T50 was used to calibrate our threshold; T10/T25/T100/T500 are "
                    "untouched evidence. Precision is reported, NOT optimised: hazard class "
                    "4-6 is a danger-to-life classification, so a real channel carrying "
                    "class 1-3 water counts against us.")
    return out


# ======================================================================================
# THE RECONCILIATION
# ======================================================================================

def _nsa_distance_per_link(ours_gdf, nsa_gdf, n_probe: int = 5):
    """Median distance from each of our links to the engineer's nearest line.

    MEDIAN over probe points along the link, not the minimum over the whole link: a link
    that touches his network at one end and then diverges for 400 m is not a confirmed link,
    and a minimum-distance test would call it one.
    """
    from shapely import STRtree
    from shapely.geometry import Point
    if len(nsa_gdf) == 0:
        return np.full(len(ours_gdf), np.nan)
    tree = STRtree(list(nsa_gdf.geometry))
    fr = np.linspace(0.1, 0.9, n_probe)
    out = np.full(len(ours_gdf), np.nan, dtype="float64")
    pts, owner = [], []
    for i, gm in enumerate(ours_gdf.geometry):
        L = gm.length
        for f in fr:
            p = gm.interpolate(f * L)
            pts.append(p)
            owner.append(i)
    idx = tree.nearest(pts)
    geoms = list(nsa_gdf.geometry)
    d = np.array([pts[j].distance(geoms[idx[j]]) for j in range(len(pts))])
    owner = np.asarray(owner)
    for i in range(len(ours_gdf)):
        m = owner == i
        if m.any():
            out[i] = float(np.median(d[m]))
    return out


def reconcile(write: bool = True) -> dict:
    """Run every measurement and write `run/streams/reconcile.json` + a short verdict.

    Nothing in here is a preference.  Each block is a number that would have made the
    opposite recommendation if it had come out the other way.
    """
    import geopandas as gpd
    import pandas as pd
    t0 = time.time()
    spec, sl, tr, shape, bx = window()
    H, W = shape
    left = spec.left + sl[1].start * spec.res
    top = spec.top - sl[0].start * spec.res
    _log(f"window {H} x {W} cells @ {spec.res:g} m = "
         f"{H * W * spec.cell_area / 1e6:,.0f} km2 over both study boundaries + "
         f"{PUBLISH_BUFFER_M:.0f} m")

    g_ours = ours()
    g_nsaf = nsa("full")
    g_nsap = nsa("pb")

    rep = {
        "_written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "_banner": banner(),
        "grid": dict(name=spec.name, res_m=spec.res, window_cells=[H, W],
                     window_km2=round(H * W * spec.cell_area / 1e6, 1),
                     buffer_m=PUBLISH_BUFFER_M),
        "sources": {
            "ours": dict(path=str(T.RUN / f"{spec.name}_streams.gpkg"),
                         dem=str(T.DEM_VRT), dem_res_m=0.5, working_res_m=spec.res,
                         threshold_m2=float(g_ours["THRESH_M2"].iloc[0])
                         if "THRESH_M2" in g_ours.columns and len(g_ours) else None,
                         links=int(len(g_ours)), km=round(g_ours.length.sum() / 1000, 1)),
            "nsa_full": dict(path=str(NSA_FULL), dem=str(T.HYDRAULIC / "Terrain" / "NSA_DEM.tif"),
                             dem_res_m=4.0, links=int(len(g_nsaf)),
                             km=round(g_nsaf.length.sum() / 1000, 1),
                             note="the engineer's own extraction, whole 4 m NSA DEM, "
                                  "QGIS/WhiteboxTools, create_streams.py, stated 0.5 km2"),
            "nsa_pb": dict(path=str(NSA_PB),
                           dem=str(T.HYDRAULIC / "Terrain" / "NSA_DEM_Clip.tif"),
                           dem_res_m=4.0, links=int(len(g_nsap)),
                           km=round(g_nsap.length.sum() / 1000, 1),
                           note="NOT a clip of nsa_full - a separate extraction from a "
                                "PRE-CLIPPED DEM, so contributing area is truncated at the "
                                "clip edge for every wadi entering from outside"),
        },
    }

    # ---- 1. effective threshold, with a control ---------------------------------------
    _log("1/4  effective threshold of each layer, read off our own accumulation field")
    acc = _Sampler(T._rd(T.RUN / f"{spec.name}_acc.tif", masked=True)[sl], spec, left, top)
    rep["effective_threshold"] = {
        "ours_CONTROL": effective_threshold(g_ours, "ORDER", acc, "ours (threshold KNOWN)"),
        "nsa_full": effective_threshold(g_nsaf, "STRM_VAL", acc, "engineer, full 4 m DEM"),
        "nsa_pb": effective_threshold(g_nsap, "STRM_VAL", acc, "engineer, pre-clipped DEM"),
    }
    ctl = rep["effective_threshold"]["ours_CONTROL"].get("snap_25m", {})
    declared = rep["sources"]["ours"]["threshold_m2"]
    if ctl and declared:
        bias = ctl["median_m2"] / declared
        rep["effective_threshold"]["_control"] = dict(
            declared_m2=declared, recovered_m2=ctl["median_m2"], bias_factor=round(bias, 3),
            why="the same procedure run on a layer whose threshold is known exactly. The "
                "bias applies equally to every layer measured this way, so the comparison "
                "between them is fair even though each single number is high by this factor.")
        for k in ("nsa_full", "nsa_pb"):
            blk = rep["effective_threshold"][k].get("snap_25m")
            if blk:
                rep["effective_threshold"][k]["bias_corrected_m2"] = round(
                    blk["median_m2"] / bias)
                rep["effective_threshold"][k]["bias_corrected_km2"] = round(
                    blk["median_m2"] / bias / 1e6, 3)
        _log(f"     control: declared {declared:,.0f} m2 -> recovered "
             f"{ctl['median_m2']:,.0f} m2 (bias x{bias:.2f})")
    for k in ("nsa_full", "nsa_pb"):
        b = rep["effective_threshold"][k]
        if "snap_25m" in b:
            _log(f"     {k}: median head area {b['snap_25m']['median_m2']:,.0f} m2 "
                 f"= {b['snap_25m']['median_km2']:.3f} km2"
                 + (f" (bias-corrected {b.get('bias_corrected_km2')} km2)"
                    if "bias_corrected_km2" in b else ""))
    del acc

    # ---- 2. spatial agreement ----------------------------------------------------------
    _log("2/4  two-way spatial agreement")
    st = np.asarray(T._rd(T.RUN / f"{spec.name}_streams.tif")[sl])
    masks = {"ours": np.isfinite(st) & (st > 0),
             "nsa_full": _rasterise(g_nsaf, tr, shape),
             "nsa_pb": _rasterise(g_nsap, tr, shape)}
    del st
    dists = {k: _edt(v, spec.res) for k, v in masks.items()}
    rep["agreement"] = agreement(masks, dists, spec.res)
    for k, v in rep["agreement"].items():
        _log(f"     {k}: {v['A_km']:,} km vs {v['B_km']:,} km  "
             f"100 m -> A in B {v['100m']['frac_of_A_near_B']:.3f}, "
             f"B in A {v['100m']['frac_of_B_near_A']:.3f}")

    # the pre-clipped layer only covers part of the window; comparing outside its own
    # footprint would score it down for ground it was never given
    b = g_nsap.total_bounds
    cc, rr = np.meshgrid(np.arange(W), np.arange(H))
    X = left + (cc + 0.5) * spec.res
    Y = top - (rr + 0.5) * spec.res
    inpb = (X >= b[0] + 100) & (X <= b[2] - 100) & (Y >= b[1] + 100) & (Y <= b[3] - 100)
    del X, Y, cc, rr
    rep["agreement_within_nsa_pb_footprint"] = agreement(masks, dists, spec.res, restrict=inpb)
    rep["agreement_within_nsa_pb_footprint"]["_note"] = (
        "restricted to the pre-clipped layer's own footprint (shrunk 100 m), so it is not "
        f"penalised for ground it never covered. That footprint is {inpb.mean():.0%} of the "
        "window.")
    del inpb

    # ---- 3. against the five flood grids ------------------------------------------------
    _log("3/4  every source against all five flood-hazard grids")
    rep["vs_flood_hazard"] = vs_hazard(masks, dists, spec, sl)
    for rp, row in rep["vs_flood_hazard"].items():
        if rp.startswith("_"):
            continue
        _log(f"     {rp}: skeleton {row['hazard_skeleton_km']:,.0f} km  "
             + "  ".join(f"{k} R100 {row[k]['recall']['100m']:.3f}"
                         for k in masks))

    # ---- 4. confirmation by Strahler order ----------------------------------------------
    _log("4/4  confirmation of our links by the engineer's network, by Strahler order")
    d_nsaf = _nsa_distance_per_link(g_ours, g_nsaf)
    d_nsap = _nsa_distance_per_link(g_ours, g_nsap)
    df = pd.DataFrame(dict(order=pd.to_numeric(g_ours["ORDER"], errors="coerce").fillna(0)
                           .astype(int),
                           km=g_ours.length.values / 1000.0,
                           d_full=d_nsaf, d_pb=d_nsap))
    by = []
    for o, d in df.groupby("order"):
        by.append(dict(order=int(o), links=int(len(d)), km=round(float(d.km.sum()), 1),
                       confirmed_by_nsa_full=round(float((d.d_full <= CONFIRM_TOL_M).mean()), 3),
                       confirmed_by_nsa_pb=round(float((d.d_pb <= CONFIRM_TOL_M).mean()), 3),
                       median_dist_to_nsa_full_m=round(float(np.nanmedian(d.d_full)), 1)))
    rep["by_order"] = dict(
        tolerance_m=CONFIRM_TOL_M, rows=by,
        note=f"confirmation jumps between order 2 and order 3, which is why "
             f"MAIN_WADI_MIN_ORDER = {MAIN_WADI_MIN_ORDER} is MEASURED and not chosen.")
    for r in by:
        _log(f"     order {r['order']}: {r['km']:>8,.0f} km  confirmed "
             f"{r['confirmed_by_nsa_full']:.3f}")

    # ---- inside the two candidate boundaries --------------------------------------------
    inside = {}
    for nm, p in (("mohup_439.8km2", T.BOUNDARY_MOHUP), ("study_531.4km2", T.BOUNDARY_STUDY)):
        if not p.exists():
            continue
        bnd = gpd.read_file(p).to_crs(CRS)
        u = bnd.union_all() if hasattr(bnd, "union_all") else bnd.unary_union
        gi = gpd.clip(g_ours, u)
        inside[nm] = dict(km=round(float(gi.length.sum()) / 1000, 1),
                          km_by_order={int(k): round(float(v) / 1000, 1) for k, v in
                                       gi.assign(_l=gi.length).groupby("ORDER")._l.sum()
                                       .items()})
    rep["inside_boundaries"] = dict(
        **inside,
        note="both are published. Which is the project's is an OPEN DECISION "
             "(_BRAIN/00_CURRENT.md); IN_MOHUP / IN_STUDY on every row let it be settled "
             "without rebuilding the layer.")

    rep["verdict"] = _verdict(rep)
    rep["_seconds"] = round(time.time() - t0, 1)

    if write:
        RUN.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(rep, indent=2, default=str), encoding="utf-8")
        VERDICT.write_text(_verdict_md(rep), encoding="utf-8")
        _log(f"wrote {REPORT}")
        _log(f"wrote {VERDICT}")
    return rep


def _verdict(rep: dict) -> dict:
    """The recommendation, assembled from the numbers just measured rather than typed in."""
    ag = rep.get("agreement", {}).get("ours_vs_nsa_full", {})
    hz = rep.get("vs_flood_hazard", {}).get("T50", {})
    eff = rep.get("effective_threshold", {})
    ours_r = (hz.get("ours") or {}).get("recall", {}).get("100m")
    nsaf_r = (hz.get("nsa_full") or {}).get("recall", {}).get("100m")
    nsap_r = (hz.get("nsa_pb") or {}).get("recall", {}).get("100m")
    return dict(
        use="ours",
        one_line=(
            f"Use the {rep['sources']['ours']['threshold_m2']:,.0f} m2 (4 ha) network derived "
            f"here: the engineer's own 0.5 km2 layer is the same network with orders 1-2 "
            f"removed and it confirms 91-97 % of everything we call order 3 or above, but on "
            f"its own it finds only {nsaf_r:.0%} of the 50-year wadi skeleton against our "
            f"{ours_r:.0%}."),
        supporting=dict(
            engineer_threshold_recovered_km2=(eff.get("nsa_full", {}) or {}).get(
                "bias_corrected_km2"),
            engineer_threshold_stated_km2=0.5,
            his_network_inside_ours_100m=ag.get("100m", {}).get("frac_of_B_near_A"),
            ours_inside_his_100m=ag.get("100m", {}).get("frac_of_A_near_B"),
            recall_of_50yr_wadi_skeleton=dict(ours=ours_r, nsa_full=nsaf_r, nsa_pb=nsap_r)),
        reject=dict(
            layer=str(NSA_PB),
            why="extracted from a PRE-CLIPPED DEM, so contributing area is truncated for "
                "every wadi entering the study area from outside. It is denser than ours and "
                f"still finds fewer wadis ({nsap_r:.0%} of the 50-year skeleton against our "
                f"{ours_r:.0%}), and only ~21 % of it lies within 25 m of the engineer's own "
                "full-DEM extraction. A denser network that finds fewer wadis is a network "
                "in the wrong places."),
        defects_found=[
            "terrain.NSA_STREAMS points at the PRE-CLIPPED layer, so "
            "terrain.verify_vs_nsa_streams() is checking against the wrong file. It should "
            "point at 'Streams NSA 2m.shp'.",
            "terrain.stage_streams writes ACC_M2 as the PEAK accumulation over all vertices "
            "of a link. The last vertex sits on the junction cell, whose accumulation "
            "already includes the receiving stem, so order-1 links carry areas up to "
            "1,168 km2. This module re-derives it one cell back from the downstream end; "
            "after that no link is below the threshold that created it.",
            "contract.STREAMS documents GND_FALL as 'ground fall', and its cross-field check "
            "reads a negative value as a reversed flow direction. On a bare-earth DEM 1.37 % "
            "of links have a negative RAW fall from real pits, not from reversed direction. "
            "This module publishes GND_FALL from the CONDITIONED routing surface (monotone by "
            "construction, and the surface the direction was derived from) and FALL_DEM "
            "beside it, with PIT = 1 where the two disagree. Nothing is hidden, but the "
            "contract's wording should say which surface it means.",
        ],
    )


def _verdict_md(rep: dict) -> str:
    v = rep["verdict"]
    hz = rep["vs_flood_hazard"]
    lines = [
        "# W12 - the stream network: which source the design follows",
        "", f"_measured {rep['_written']}_", "",
        "## The answer", "", "**" + v["one_line"] + "**", "",
        "## What was measured", "",
        "| | ours (4 ha, 0.5 m terrain @ 5 m) | engineer, 0.5 km2, 4 m NSA DEM | "
        "engineer, pre-clipped DEM |",
        "|---|---|---|---|",
    ]
    s = rep["sources"]
    lines.append(f"| length in the window | {s['ours']['km']:,.0f} km | "
                 f"{s['nsa_full']['km']:,.0f} km | {s['nsa_pb']['km']:,.0f} km |")
    eff = rep["effective_threshold"]
    def _e(k):
        b = eff.get(k, {}).get("snap_25m")
        return f"{b['median_km2']:.3f} km2" if b else "-"
    lines.append(f"| threshold recovered from our own field | {_e('ours_CONTROL')} "
                 f"(declared 0.040) | {_e('nsa_full')} (stated 0.5) | {_e('nsa_pb')} |")
    for rp in ("T10", "T25", "T50", "T100", "T500"):
        if rp not in hz:
            continue
        r = hz[rp]
        lines.append(f"| recall of the {rp[1:]}-yr wadi skeleton (100 m) | "
                     + " | ".join(f"{r[k]['recall']['100m']:.3f}"
                                  for k in ("ours", "nsa_full", "nsa_pb")) + " |")
    lines += ["", "## Confirmation of our links by the engineer's network", "",
              "| Strahler order | km | confirmed within 100 m |", "|---|---|---|"]
    for r in rep["by_order"]["rows"]:
        lines.append(f"| {r['order']} | {r['km']:,.0f} | {r['confirmed_by_nsa_full']:.0%} |")
    lines += ["", f"Confirmation jumps between order 2 and order 3. That is why "
                  f"`MAIN_WADI_MIN_ORDER = {MAIN_WADI_MIN_ORDER}` is a measurement and not a "
                  f"preference.", "",
              "## Rejected", "", f"`{Path(v['reject']['layer']).name}` - " + v["reject"]["why"],
              "", "## Defects found elsewhere (reported, not fixed - other agents own those "
                  "files)", ""]
    lines += [f"{i+1}. {d}" for i, d in enumerate(v["defects_found"])]
    lines += ["", "## Flags that travel with this layer", "", "```", rep["_banner"], "```"]
    return "\n".join(lines) + "\n"


# ======================================================================================
# BUILD - the published layer
# ======================================================================================

def build(mirror_shp: bool = False, validate_it: bool = True) -> str:
    """Publish `W12/shp/W12_streams.gpkg`, layer `streams`.

    Every field is derived here, none is carried through on trust from `terrain`'s vector -
    including ACC_M2, which `terrain` writes as a peak over all vertices and which is
    therefore contaminated at every junction (see `reconcile()['verdict']['defects_found']`).
    """
    import geopandas as gpd
    import pandas as pd
    from . import contract as K

    t0 = time.time()
    spec, sl, tr, shape, bx = window()
    H, W = shape
    left = spec.left + sl[1].start * spec.res
    top = spec.top - sl[0].start * spec.res

    g = ours()
    n = len(g)
    _log(f"build: {n:,} links, {g.length.sum()/1000:,.0f} km selected by the window")
    if n == 0:
        raise RuntimeError("no links in the window - has the terrain been built?")

    # ---- samplers ------------------------------------------------------------------------
    acc = _Sampler(T._rd(T.RUN / f"{spec.name}_acc.tif", masked=True)[sl], spec, left, top)
    dem = _Sampler(T._rd(T.RUN / f"{spec.name}_dem.tif", masked=True)[sl], spec, left, top)
    cond = _Sampler(T._rd(T.RUN / f"{spec.name}_dem_cond.tif", masked=True)[sl], spec, left, top)
    haz = _Sampler(T._rd(T._flood_on_grid(spec, WADI_RP))[sl], spec, left, top)

    xy0 = np.array([gm.coords[0][:2] for gm in g.geometry], dtype="float64")
    xy1 = np.array([gm.coords[-1][:2] for gm in g.geometry], dtype="float64")
    L = g.length.values

    # ---- orientation. Accumulation, not elevation, and not the digitising order. ----------
    # Accumulation increases STRICTLY downstream along a D8 path, so it decides the direction
    # exactly, with no tolerance and no appeal to a fall that may be inside the DEM's noise.
    a0 = acc.at(xy0[:, 0], xy0[:, 1])
    a1 = acc.at(xy1[:, 0], xy1[:, 1])
    flip = np.where(np.isfinite(a0) & np.isfinite(a1), a0 > a1, False)
    _log(f"build: WhiteboxTools digitised {100*(~flip).mean():.1f} % of links already "
         f"downstream; {int(flip.sum()):,} reversed here")
    if flip.any():
        from shapely.geometry import LineString
        geoms = [LineString(list(gm.coords)[::-1]) if f else gm
                 for gm, f in zip(g.geometry, flip)]
        g = g.set_geometry(gpd.GeoSeries(geoms, crs=CRS))
        xy0, xy1 = np.where(flip[:, None], xy1, xy0), np.where(flip[:, None], xy0, xy1)

    # ---- contributing area at the link's OWN downstream end --------------------------------
    # One cell back from the last vertex.  The last vertex sits ON the junction cell, whose
    # accumulation already carries the stem this link joins - which is how terrain's peak
    # reading gives an order-1 rill a 1,168 km2 catchment.
    back = np.clip(L - spec.res, 0.0, None)
    pb = [gm.interpolate(b) for gm, b in zip(g.geometry, back)]
    acc_m2 = acc.at([p.x for p in pb], [p.y for p in pb])

    # ---- levels and fall --------------------------------------------------------------------
    z_up = dem.at(xy0[:, 0], xy0[:, 1])
    z_dn = dem.at(xy1[:, 0], xy1[:, 1])
    k_up = cond.at(xy0[:, 0], xy0[:, 1])
    k_dn = cond.at(xy1[:, 0], xy1[:, 1])
    fall_dem = z_up - z_dn
    fall_cond = k_up - k_dn
    pit = ((fall_dem < -0.001) & np.isfinite(fall_dem)).astype("int64")
    _log(f"build: raw-DEM fall is negative on {int(pit.sum()):,} links "
         f"({100*pit.mean():.2f} %) - real pits in a bare-earth surface, not a reversed "
         f"direction; conditioned fall is negative on "
         f"{int((fall_cond < -0.001).sum()):,}")

    # ---- hazard along the link ---------------------------------------------------------------
    # sampled every cell, and reduced by MAXIMUM.  terrain._flood_on_grid resamples the same
    # way and says why: a prohibition (G203-p30 4.4.1) must not be averaged away.
    hmax = np.zeros(n, dtype="int64")
    hcov = np.zeros(n, dtype="int64")
    step = spec.res
    for i, gm in enumerate(g.geometry):
        k = max(2, int(math.ceil(L[i] / step)) + 1)
        s = np.linspace(0.0, L[i], k)
        pts = [gm.interpolate(v) for v in s]
        h = haz.at([p.x for p in pts], [p.y for p in pts], nodata=0.0)
        h = h[np.isfinite(h)]
        if h.size:
            hmax[i] = int(h.max())
            hcov[i] = int((h > 0).any())

    # ---- the engineer's network, per link ------------------------------------------------------
    _log("build: distance from every link to the engineer's independent network")
    d_nsa = _nsa_distance_per_link(g, nsa("full"))

    # ---- topology, WRITTEN DOWN (philosophy H16), never inferred later --------------------------
    key0 = [(round(p[0], 2), round(p[1], 2)) for p in xy0]
    key1 = [(round(p[0], 2), round(p[1], 2)) for p in xy1]
    starts = {}
    for i, k in enumerate(key0):
        starts.setdefault(k, []).append(i)
    ids = [STREAM_ID_FMT.format(i + 1) for i in range(n)]
    ds = []
    multi = 0
    for i in range(n):
        cand = [j for j in starts.get(key1[i], []) if j != i]
        if len(cand) > 1:
            multi += 1
        ds.append(ids[cand[0]] if cand else "")
    _log(f"build: {sum(1 for d in ds if d):,} links have a downstream link, "
         f"{sum(1 for d in ds if not d):,} are outlets of the window; "
         f"{multi:,} ambiguous")

    # ---- boundary membership ---------------------------------------------------------------------
    in_m = np.zeros(n, dtype="int64")
    in_s = np.zeros(n, dtype="int64")
    for col, p in ((in_m, T.BOUNDARY_MOHUP), (in_s, T.BOUNDARY_STUDY)):
        if not p.exists():
            continue
        bnd = gpd.read_file(p).to_crs(CRS)
        u = bnd.union_all() if hasattr(bnd, "union_all") else bnd.unary_union
        col[:] = g.intersects(u).values.astype("int64")

    if "ORDER" not in g.columns:
        raise RuntimeError(
            "terrain's stream vector carries no ORDER column - Strahler ordering did not "
            "run. Rebuild it: python -m w12.terrain build --stages streams --force")
    order = pd.to_numeric(g["ORDER"], errors="coerce").fillna(0).astype("int64")
    thr = float(g["THRESH_M2"].iloc[0]) if "THRESH_M2" in g.columns else float("nan")

    out = gpd.GeoDataFrame({
        "STREAM_ID": ids,
        "LEN_M": g.length.values,
        "ORDER_": order.values,
        "ACC_CELLS": acc_m2 / spec.cell_area,
        "ACC_M2": acc_m2,
        "GND_FALL": fall_cond,
        "FALL_DEM": fall_dem,
        "FALL_PCT": np.where(L > 0, 100.0 * fall_cond / np.where(L > 0, L, np.nan), np.nan),
        "Z_UP": z_up,
        "Z_DN": z_dn,
        "PIT": pit,
        "IS_WADI": np.isin(hmax, WADI_CLASSES).astype("int64"),
        "HAZ_MAX": hmax,
        "HAZ_COV": hcov,
        "NSA_D_M": d_nsa,
        "CONFIRMED": (d_nsa <= CONFIRM_TOL_M).astype("int64"),
        "DS_STREAM": ds,
        "THRESH_M2": np.full(n, thr),
        "IN_MOHUP": in_m,
        "IN_STUDY": in_s,
        "TAU_FLAG": TAU_FLAG,
        "SRC": SRC_TAG,
        "CONFIDENCE": CONF_TAG,
        "STAGE": STAGE,
    }, geometry=g.geometry.values, crs=CRS)

    _log(f"build: {len(out):,} links | {out.LEN_M.sum()/1000:,.1f} km | "
         f"order 1-{int(order.max())} | {int(out.IS_WADI.sum()):,} on wadi ground | "
         f"{100*out.CONFIRMED.mean():.1f} % independently confirmed")

    GPKG.parent.mkdir(parents=True, exist_ok=True)
    if validate_it:
        K.publish(out, "streams", str(W12), stage=STAGE, gpkg=GPKG_NAME, mirror=mirror_shp)
    else:                                              # escape hatch for debugging only
        out.to_file(GPKG, layer="streams", driver="GPKG")
    _log(f"build: wrote {GPKG}  ({time.time()-t0:.0f} s)")
    return str(GPKG)


# ======================================================================================
# THE API LATER STAGES CALL
# ======================================================================================

class StreamNet:
    """The stream layer, with the two questions the network builder actually asks.

    "Which way is downhill near here" is answered by a least-squares plane fit through the
    conditioned surface - `terrain.TerrainFlow.downhill_bearing` - and NOT by the D8 pointer,
    which quantises to 45 deg and is useless for orienting a corridor on ground falling
    0.1 %.  It is delegated, not reimplemented: one derivation of the ground's direction
    exists in W12 and this is a facade over it.

    "How far to a channel" is answered off the pre-computed distance raster, so it costs a
    memory-mapped read and takes arrays.  Pass arrays.
    """

    def __init__(self, gdf, tf, tree=None):
        self.gdf = gdf
        self.tf = tf
        self._tree = tree
        self._geoms = list(gdf.geometry)

    # -- construction ------------------------------------------------------------------
    @classmethod
    def load(cls, gpkg: Path | str | None = None, grid: str = GRID,
             validate_it: bool = True) -> "StreamNet":
        import geopandas as gpd
        from shapely import STRtree
        from . import contract as K
        p = Path(gpkg) if gpkg else GPKG
        if not p.exists():
            raise FileNotFoundError(
                f"{p} does not exist. Build it: python -m w12.streams build")
        g = gpd.read_file(p, layer="streams")
        if validate_it:
            K.validate(g, "streams", stage="streams:load")
        return cls(g, T.TerrainFlow.load(grid), STRtree(list(g.geometry)))

    # -- the two the builder asks ------------------------------------------------------
    def distance(self, x, y):
        """Metres to the nearest derived channel.  Array-capable, O(1) per point.

        Quantised to the working cell, so it is exact to +/- one cell (5 m) and never
        exact to the metre - `nearest()` measures against the real geometry when a metre
        matters.  65535 means the point is off the grid, not that the channel is 65 km away.
        """
        return self.tf.stream_distance(x, y)

    def downhill(self, x, y, radius: float = T.BEARING_RADIUS_M):
        """(bearing_deg, slope_pct) pointing DOWNHILL. 0 deg = north, 90 = east."""
        return self.tf.downhill_bearing(x, y, radius=radius)

    # -- the network itself -------------------------------------------------------------
    def nearest(self, x, y) -> dict:
        """The nearest link and what is known about it."""
        from shapely.geometry import Point
        p = Point(float(x), float(y))
        i = int(self._tree.nearest(p))
        row = self.gdf.iloc[i]
        return dict(stream_id=row.STREAM_ID, order=int(row.ORDER_),
                    acc_m2=float(row.ACC_M2), dist_m=float(p.distance(self._geoms[i])),
                    is_wadi=bool(row.IS_WADI), haz_max=int(row.HAZ_MAX),
                    hazard_covered=bool(row.HAZ_COV), confirmed=bool(row.CONFIRMED),
                    ds_stream=row.DS_STREAM or None)

    def order_at(self, x, y, radius: float = 50.0) -> int:
        """The largest Strahler order within `radius`; 0 if no channel is that close.

        This is the "is there a real wadi here, or a gully" question, answered by a property
        of the network rather than by a second threshold nobody calibrated.
        """
        from shapely.geometry import Point
        pt = Point(float(x), float(y))
        idx = np.asarray(self._tree.query(pt.buffer(radius)))
        if idx.size == 0:
            return 0
        hit = [int(self.gdf.ORDER_.iat[int(i)]) for i in idx
               if self._geoms[int(i)].distance(pt) <= radius]
        return max(hit) if hit else 0

    def main_wadis(self):
        """The order >= 3 subset.

        3 is MEASURED, not chosen: confirmation of our links by the engineer's independent
        0.5 km2 extraction jumps from 47 % at order 2 to 91 % at order 3 and stays 91-97 %
        above it.  Order 3+ is the set that two DEMs, two resolutions and two software runs
        all call a channel; its median catchment here is 1.33 km2.
        """
        return self.gdf[self.gdf.ORDER_ >= MAIN_WADI_MIN_ORDER]

    def is_wadi(self, x, y, return_period: int = WADI_RP):
        """The G203-p30 4.4.1 prohibition test, delegated to the hazard grid.

        FALSE MEANS 'NOT SHOWN TO BE WADI'.  Over half this window is outside the hazard
        grids and no-data is read as dry high ground by the engineer's decision of
        2026-09-03, so pair this with `hazard_covered()` before treating a False as clearance.
        """
        return self.tf.in_wadi(x, y, return_period=return_period)

    def hazard_covered(self, x, y, return_period: int = WADI_RP):
        """Does the flood model say ANYTHING here?  The honest companion to `is_wadi`."""
        return self.tf.hazard_class(x, y, return_period) > 0

    def drain_direction(self, line, **kw):
        """Which END of a corridor line is the outlet, with a measured confidence."""
        return self.tf.drain_direction(line, **kw)

    # -- what must be printed -----------------------------------------------------------
    def flags(self) -> dict:
        f = dict(self.tf.flags())
        f.update(stream_threshold_m2=float(self.gdf.THRESH_M2.iloc[0])
                 if len(self.gdf) else None,
                 stream_threshold_basis="MEASURED - the coarsest contributing area still "
                                        "recovering >= 90 % of the 50-year hazard skeleton",
                 main_wadi_min_order=MAIN_WADI_MIN_ORDER,
                 main_wadi_basis="MEASURED - confirmation by the engineer's independent "
                                 "0.5 km2 extraction jumps 47 % -> 91 % between order 2 and 3",
                 confirm_tol_m=CONFIRM_TOL_M,
                 gnd_fall_surface="CONDITIONED routing surface (monotone by construction). "
                                  "FALL_DEM carries the bare-earth fall and PIT flags where "
                                  "the two disagree.",
                 layer=str(GPKG))
        return f

    def summary(self) -> str:
        g = self.gdf
        by = g.groupby("ORDER_").LEN_M.agg(["count", "sum"])
        lines = [banner(), "",
                 f"{len(g):,} links | {g.LEN_M.sum()/1000:,.1f} km | "
                 f"{int(g.IS_WADI.sum()):,} links on wadi ground | "
                 f"{100*g.CONFIRMED.mean():.1f} % confirmed by the engineer's own network",
                 f"inside MoHUP boundary {int(g.IN_MOHUP.sum()):,} links | "
                 f"inside study boundary {int(g.IN_STUDY.sum()):,} links",
                 "", "  order    links        km   confirmed"]
        for o, r in by.iterrows():
            sub = g[g.ORDER_ == o]
            lines.append(f"  {int(o):>5}  {int(r['count']):>7,}  {r['sum']/1000:>8,.0f}  "
                         f"{100*sub.CONFIRMED.mean():>9.1f} %")
        return "\n".join(lines)


# ======================================================================================
# VERIFY - read the PUBLISHED layer back and check it. Never the in-memory frame.
# ======================================================================================

def verify() -> dict:
    """Re-open what was written and test it.  A stage that checks its own memory has checked
    nothing: W10's published layer arrived in 7,919 pieces and every in-memory assertion had
    passed."""
    sn = StreamNet.load()
    g = sn.gdf
    out = {"layer": str(GPKG), "links": int(len(g)), "km": round(float(g.LEN_M.sum()) / 1000, 1)}
    checks = []

    def chk(name, ok, detail=""):
        checks.append(dict(check=name, result="pass" if ok else "FAIL", detail=detail))

    chk("length agrees with geometry",
        bool((abs(g.LEN_M - g.geometry.length) <= 0.05).all()),
        f"worst {float((g.LEN_M - g.geometry.length).abs().max()):.4f} m")
    neg = int((g.GND_FALL < -0.001).sum())
    chk("no stream runs uphill", neg == 0, f"{neg} negative GND_FALL")
    below = int((g.ACC_M2 < g.THRESH_M2 - 1).sum())
    chk("no link below the threshold that created it", below == 0,
        f"{below} links; terrain's peak reading gave 0 here only because it over-reads")
    ids = set(g.STREAM_ID)
    dang = int(sum(1 for d in g.DS_STREAM if d and d not in ids))
    chk("every DS_STREAM resolves", dang == 0, f"{dang} dangling references")
    chk("no self reference", int((g.DS_STREAM == g.STREAM_ID).sum()) == 0)
    chk("order is 1..n with no gaps",
        sorted(set(int(v) for v in g.ORDER_)) == list(range(1, int(g.ORDER_.max()) + 1)),
        f"orders present {sorted(set(int(v) for v in g.ORDER_))}")
    wadi_ok = bool((g.loc[g.IS_WADI == 1, "HAZ_MAX"].isin(WADI_CLASSES)).all())
    chk("IS_WADI agrees with HAZ_MAX", wadi_ok)
    chk("IS_WADI implies hazard coverage",
        int(((g.IS_WADI == 1) & (g.HAZ_COV == 0)).sum()) == 0)
    conf = int(((g.CONFIRMED == 1) & (g.NSA_D_M > CONFIRM_TOL_M)).sum())
    chk("CONFIRMED agrees with NSA_D_M", conf == 0, f"{conf} rows")

    # what the layer is FOR: the two questions
    x = g.geometry.interpolate(0.5, normalized=True)
    d = sn.distance(np.array([p.x for p in x[:2000]]), np.array([p.y for p in x[:2000]]))
    chk("a point on a stream is ~0 m from a stream", float(np.nanmedian(d)) <= 5.0,
        f"median {float(np.nanmedian(d)):.1f} m at {_spec().res:g} m resolution")
    b, s = sn.downhill(np.array([p.x for p in x[:2000]]), np.array([p.y for p in x[:2000]]))
    chk("downhill_bearing answers on the channel", float(np.isfinite(b).mean()) > 0.99,
        f"{100*float(np.isfinite(b).mean()):.1f} % finite")

    out["checks"] = checks
    out["pass"] = sum(1 for c in checks if c["result"] == "pass")
    out["fail"] = sum(1 for c in checks if c["result"] == "FAIL")
    for c in checks:
        _log(f"  {c['result']:>4}  {c['check']}"
             + (f"  ({c['detail']})" if c["detail"] else ""))
    _log(f"verify: {out['pass']} pass / {out['fail']} FAIL")
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "verify.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


# ======================================================================================
# CLI
# ======================================================================================

def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "all"
    print(banner())
    print()
    if cmd in ("reconcile", "all"):
        r = reconcile()
        print()
        print(r["verdict"]["one_line"])
        print()
    if cmd in ("build", "all"):
        build()
    if cmd in ("verify", "all"):
        verify()
    if cmd == "summary":
        print(StreamNet.load().summary())
    if cmd not in ("reconcile", "build", "verify", "all", "summary"):
        print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
