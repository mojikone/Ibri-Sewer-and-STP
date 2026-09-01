"""W10 Phase 4.3 - STP site suitability surface and candidate shortlist.

Builds a weighted multi-criteria surface over the whole 531.4 km2 study boundary,
applies the hard exclusions that come from PAM-GUD-201/-203, and extracts a
shortlist of candidate sites. The two sites already on the table - the existing
works and the user's proposed southern site - are scored against exactly the same
surface so the comparison is like for like.

Every guideline number in here is read back from the PDF with its page. See
W10/docs/STP_SITING.md for the citations and the reasoning.

Outputs
    shp/W10_stp_suitability.tif    50 m scored surface, 0..1, -1 = outside boundary
    shp/W10_stp_criteria.tif       7-band stack, one band per criterion (same grid)
    shp/W10_stp_candidates.shp     shortlist + the two known sites, all attributes
    img/W10_P4_stp_suitability.png the map
    run/p4_stp_candidates.csv      the same table as CSV

Re-run:  python W10/py/p4_stp_siting.py
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.windows import from_bounds
from scipy import ndimage as ndi
from shapely.geometry import Point, box

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C  # noqa: E402

# --------------------------------------------------------------------------- #
# design constants - every one of these is defended in docs/STP_SITING.md
# --------------------------------------------------------------------------- #

# flows (established, PROJECT-STATE; not re-derived here)
Q_ULT = 49_700.0          # m3/d ultimate saturated design flow, whole study area
Q_DESIGN = Q_ULT * 1.10   # 54,670 m3/d - the capacity the land must be sized for

# land requirement, G203 p64 Table 28 "Land Area Requirement", m2 per m3/d
FOOTPRINT_M2_PER_M3D = {
    "MBR": (0.45, 0.90),
    "SBR": (0.90, 1.80),
    "MBBR": (0.90, 1.80),
    "IFAS": (1.20, 2.50),
    "CAS/EA": (1.80, 3.60),
    "Reed bed": (10.0, None),
}
LAND_MIN_HA = 20.0   # CAS/EA upper bound 3.6 m2/(m3/d) x 54,670 = 19.7 ha -> 20 ha
LAND_GOOD_HA = 30.0  # +50% for phasing, sludge, TSE storage and the solar farm G203 p64
LAND_WINDOW_M = 650.0  # the moving window free area is measured in: 13 cells = 42.25 ha

# odour / amenity buffer, G201 p43 Table 8 "Minimum buffer zone requirements"
#   STP (small/medium)  500 m to residential / sensitive uses
#   STP (large)         300 m - 1000 m, from odour modelling (5 OU contour)
# 49,700 m3/d is unambiguously "large", so the band is the governing rule.
DWELL_HARD_M = 300.0     # below this the site is out
DWELL_FULL_M = 1000.0    # at or beyond this the criterion is fully satisfied
DWELL_GENERIC_M = 500.0  # the small/medium generic default, reported as a flag

# Which plots count as odour receptors. W3 CLASS='B' means "there are structures on
# it", not "people live on it". Eleven built plots are 5 ha or larger with no land
# use attribute - the largest is 899 ha, 14,000x the median built plot (0.064 ha) -
# and two of them ARE the existing works compound (6.6 ha + 29.0 ha). Left in, the
# 899 ha parcel alone throws a 300 m exclusion and a 1 km buffer ring across 20 km2
# of the west, and it put three sites in the first shortlist. Left in, the existing
# works is also its own odour receptor and scores 0 m to a dwelling. So a built plot
# of 5 ha or more counts as a receptor only if its land use says people are on it.
RECEPTOR_BIG_HA = 5.0
RECEPTOR_LANDUSE = {           # Arabic values in MoH_Plots.LANDUSE
    "سكني",                          # residential
    "سكني/تجاري",   # residential / commercial
    "سكنى/زراعى",   # residential / agricultural
    "مسجد",                          # mosque
    "حكومي",                    # government (schools, clinics - kept)
}

# flood. G203 p63 Table 27 (i) requires 25 and 100 year flood compliance and that
# the STP stay fully operational during floods. NO numeric wadi setback exists in
# G201/G203 - the only wadi distance in either book is 15 m either side of a pipe
# crossing (G201 p86), which is a pipeline rule. 100 m below is engineering
# judgement, stated as such in the doc.
WADI_CLASS_MIN = 4.0     # hazard grid: floor(value) >= 4 is wadi, 1-3 is safe
WADI_HARD_M = 100.0
WADI_FULL_M = 500.0

# gravity screening. S_MIN is the gradient the given trunk is actually laid at
# (DN1000 at 0.10 %, established in Phase 4.2). SINUOSITY converts a straight line
# into a plausible built pipe length on a street network.
S_MIN = 0.0010
SINUOSITY = 1.30
D_COLLECT = 2.0   # invert below ground where the load enters the collector, m
D_INLET = 6.0     # deepest acceptable inlet invert at the works, m below ground

# conveyance / access
TRUNK_FULL_M = 0.0
TRUNK_ZERO_M = 5000.0
ROAD_FULL_M = 200.0
ROAD_ZERO_M = 2000.0
MAJOR_FULL_M = 1000.0
MAJOR_ZERO_M = 5000.0
AGRI_FULL_M = 500.0
AGRI_ZERO_M = 5000.0
AGRI_RADIUS_M = 5000.0

# weights - sum to 1.00
WEIGHTS = {
    "C2_GRAVITY": 0.25,
    "C1_DWELL": 0.20,
    "C4_LAND": 0.15,
    "C5_PIPE": 0.15,
    "C7_TSE": 0.10,
    "C6_ROAD": 0.08,
    "C3_FLOOD": 0.07,
}

# grids
CELL = 50.0        # scoring grid
FINE = 10.0        # rasterising / distance grid
LOADCELL = 500.0   # load centres are aggregated onto this grid

# candidate extraction
N_CANDIDATES = 10
MIN_SEPARATION_M = 2500.0

KNOWN_SITES = [
    ("EXISTING", "Existing Ibri works", C.STP_EXISTING),
    ("SOUTH", "User proposed southern site", C.STP_PROPOSED_SOUTH),
]

# the 5 m component of the authoritative terrain VRT. IBRI_0p5_VRT2.vrt is two
# stacked sources; this is the lower one, and it covers the whole extent. Sampling
# the 0.5 m VRT at 474k grid centres takes ~16 min, reading this takes 3 s, and
# the two agree to mean +0.06 m / std 0.46 m over 2000 random points inside the
# boundary. Point values reported for candidates still come off the full VRT.
TERRAIN_5M = C.BASE + r"\Data\Terrain\Sat_0p5m\ibri_blend.tif"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ramp(x, lo, hi):
    """0 below lo, 1 at or above hi, linear between. hi may be below lo."""
    if hi > lo:
        return np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return np.clip((lo - x) / (lo - hi), 0.0, 1.0)


def block_reduce(a, f, how="mean", nodata=None):
    """Aggregate a 2-D array by an integer factor."""
    ny, nx = a.shape
    a = a[: ny // f * f, : nx // f * f]
    b = a.reshape(a.shape[0] // f, f, a.shape[1] // f, f)
    if how == "mean":
        if nodata is not None:
            m = np.isclose(b, nodata)
            bb = np.where(m, np.nan, b)
            with np.errstate(invalid="ignore"):
                return np.nanmean(bb, axis=(1, 3))
        return b.mean(axis=(1, 3))
    if how == "max":
        return b.max(axis=(1, 3))
    if how == "min":
        return b.min(axis=(1, 3))
    raise ValueError(how)


def window_sum(a, half_cells):
    """Sum of a over a square window of (2*half+1) cells, edges handled by
    zero padding (a site on the boundary edge legitimately has less land)."""
    k = 2 * half_cells + 1
    return ndi.uniform_filter(a.astype(np.float32), size=k, mode="constant", cval=0.0) * k * k


# --------------------------------------------------------------------------- #
def main():
    t0 = time.time()
    os.makedirs(C.OUT_SHP, exist_ok=True)
    os.makedirs(C.OUT_IMG, exist_ok=True)
    os.makedirs(C.OUT_RUN, exist_ok=True)
    os.makedirs(C.OUT_DOCS, exist_ok=True)

    # ------------------------------------------------------------------ input
    log("reading vectors")
    bnd = gpd.read_file(C.BOUNDARY).to_crs(C.EPSG)
    bpoly = bnd.union_all()
    minx, miny, maxx, maxy = bpoly.bounds
    # snap the grid outward to a whole CELL
    minx = np.floor(minx / CELL) * CELL
    miny = np.floor(miny / CELL) * CELL
    maxx = np.ceil(maxx / CELL) * CELL
    maxy = np.ceil(maxy / CELL) * CELL
    nx = int((maxx - minx) / CELL)
    ny = int((maxy - miny) / CELL)
    tr50 = from_origin(minx, maxy, CELL, CELL)
    fx, fy = int((maxx - minx) / FINE), int((maxy - miny) / FINE)
    trF = from_origin(minx, maxy, FINE, FINE)
    log(f"  grid {ny} x {nx} at {CELL:.0f} m  ({ny*nx:,} cells), fine {fy} x {fx} at {FINE:.0f} m")

    plots = gpd.read_file(C.PLOTS_CLASS, encoding="utf-8").to_crs(C.EPSG)
    plots_raw = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
    roads = gpd.read_file(C.ROADS).set_crs(C.EPSG, allow_override=True)
    trunk = gpd.read_file(C.MAIN_PIPE).to_crs(C.EPSG)
    corr = gpd.read_file(C.OUT_SHP + r"\W10_corridors_noded.shp").to_crs(C.EPSG)
    log(f"  plots {len(plots):,} classified / {len(plots_raw):,} raw, roads {len(roads):,},"
        f" trunk {trunk.geometry.length.sum()/1000:.1f} km, corridors {corr.geometry.length.sum()/1000:.0f} km")

    built = plots[plots["CLASS"] == "B"]
    planned = plots[plots["CLASS"] == "P"]
    agri = plots[plots["CLASS"] == "A"]
    log(f"  built {len(built):,}  planned {len(planned):,}  agricultural {len(agri):,}")

    # odour receptors: built plots, minus the oversized unattributed parcels that
    # hold no dwellings (see RECEPTOR_BIG_HA above)
    lu = plots_raw.set_index("OBJECTID")["LANDUSE"]
    b_lu = built["OBJECTID"].map(lu)
    b_ha = built.geometry.area / 1e4
    is_big_nonres = (b_ha >= RECEPTOR_BIG_HA) & (~b_lu.isin(RECEPTOR_LANDUSE))
    recept = built[~is_big_nonres.values]
    log(f"  odour receptors {len(recept):,} plots / {recept.geometry.area.sum()/1e4:,.0f} ha "
        f"(dropped {int(is_big_nonres.sum())} built parcels >= {RECEPTOR_BIG_HA:.0f} ha with no "
        f"residential land use, {b_ha[is_big_nonres.values].sum():,.0f} ha, largest "
        f"{b_ha[is_big_nonres.values].max():,.0f} ha)")

    # ------------------------------------------------------------- fine masks
    log("rasterising masks at 10 m")

    def burn(gdf, buf=0.0):
        g = gdf.geometry
        if buf:
            g = g.buffer(buf)
        return rasterize(((geom, 1) for geom in g if geom is not None and not geom.is_empty),
                         out_shape=(fy, fx), transform=trF, fill=0,
                         dtype="uint8", all_touched=True).astype(bool)

    m_bnd_F = rasterize([(bpoly, 1)], out_shape=(fy, fx), transform=trF,
                        fill=0, dtype="uint8", all_touched=False).astype(bool)
    m_plot_F = burn(plots_raw)            # every registered plot, whatever its class
    m_built_F = burn(built)          # for the map only
    m_recept_F = burn(recept)        # what the odour buffer is measured from
    m_agri_F = burn(agri)
    m_road_F = burn(roads, buf=FINE)
    m_major_F = burn(roads[roads["dual"].isin([1, 2])], buf=FINE)
    m_trunk_F = burn(trunk, buf=FINE)
    log(f"  boundary {m_bnd_F.sum()*FINE*FINE/1e6:.1f} km2, plots {m_plot_F.sum()*FINE*FINE/1e6:.1f} km2,"
        f" built {m_built_F.sum()*FINE*FINE/1e6:.1f} km2, agri {m_agri_F.sum()*FINE*FINE/1e6:.1f} km2")

    # ------------------------------------------------------------------ flood
    log("reading 50-year flood hazard")
    with rasterio.open(C.HAZARD) as ds:
        w = from_bounds(minx, miny, maxx, maxy, ds.transform)
        haz = ds.read(1, window=w, out_shape=(fy, fx),
                      resampling=Resampling.max, boundless=True, fill_value=-9999.0)
    m_wadi_F = np.floor(np.where(haz <= -1000, 0.0, haz)) >= WADI_CLASS_MIN
    log(f"  wadi (class >= {WADI_CLASS_MIN:.0f}) {m_wadi_F.sum()*FINE*FINE/1e6:.1f} km2 in the bbox,"
        f" {(m_wadi_F & m_bnd_F).sum()*FINE*FINE/1e6:.1f} km2 inside the boundary")

    # -------------------------------------------------------------- distances
    log("distance transforms")

    def edt_to(mask):
        """metres from every fine cell to the nearest True cell of mask"""
        if not mask.any():
            return np.full(mask.shape, 1e6, np.float32)
        return (ndi.distance_transform_edt(~mask) * FINE).astype(np.float32)

    d_built_F = edt_to(m_recept_F)          # governs C1 and the hard exclusion
    d_allbuilt_F = edt_to(m_built_F)        # reported alongside, uncorrected
    d_wadi_F = edt_to(m_wadi_F)
    d_road_F = edt_to(m_road_F)
    d_major_F = edt_to(m_major_F)
    d_trunk_F = edt_to(m_trunk_F)
    d_agri_F = edt_to(m_agri_F)

    # ---------------------------------------------------------- free land 10 m
    # free = inside the boundary, off every registered plot, out of the wadi and
    # clear of a road centreline. Ownership is NOT in this - see the doc.
    free_F = m_bnd_F & ~m_plot_F & ~m_wadi_F & ~m_road_F
    log(f"  free land {free_F.sum()*FINE*FINE/1e6:.1f} km2"
        f" ({100*free_F.sum()/max(m_bnd_F.sum(),1):.1f} % of the study area)")

    # ------------------------------------------------------------ to the 50 m grid
    log("aggregating to the 50 m scoring grid")
    f = int(CELL / FINE)
    m_bnd = block_reduce(m_bnd_F.astype(np.float32), f, "mean") > 0.5
    plot_frac = block_reduce(m_plot_F.astype(np.float32), f, "mean")
    wadi_frac = block_reduce(m_wadi_F.astype(np.float32), f, "mean")
    d_built = block_reduce(d_built_F, f, "min")
    d_wadi = block_reduce(d_wadi_F, f, "min")
    d_road = block_reduce(d_road_F, f, "min")
    d_major = block_reduce(d_major_F, f, "min")
    d_trunk = block_reduce(d_trunk_F, f, "min")
    d_agri = block_reduce(d_agri_F, f, "min")
    ny, nx = m_bnd.shape

    # free area inside a LAND_WINDOW_M square, in hectares
    free50_area = block_reduce(free_F.astype(np.float32), f, "mean") * (CELL * CELL)  # m2 free per cell
    half = int(round((LAND_WINDOW_M / CELL - 1) / 2))
    free_win_ha = window_sum(free50_area, half) / 1e4
    log(f"  free area window {(2*half+1)*CELL:.0f} m square, max {free_win_ha.max():.1f} ha")

    # agricultural area within AGRI_RADIUS_M, in hectares
    agri50_area = block_reduce(m_agri_F.astype(np.float32), f, "mean") * (CELL * CELL)
    halfa = int(round(AGRI_RADIUS_M / CELL))
    agri_win_ha = window_sum(agri50_area, halfa) / 1e4

    # ----------------------------------------------------------------- terrain
    log("reading terrain")
    with rasterio.open(TERRAIN_5M) as ds:
        w = from_bounds(minx, miny, maxx, maxy, ds.transform)
        z5 = ds.read(1, window=w, out_shape=(ny * 10, nx * 10),
                     resampling=Resampling.bilinear, boundless=True, fill_value=-9999.0)
    z50 = block_reduce(z5, 10, "mean", nodata=-9999.0).astype(np.float32)
    del z5
    z50 = np.where(np.isfinite(z50), z50, np.nan)
    log(f"  ground {np.nanmin(z50[m_bnd]):.1f} - {np.nanmax(z50[m_bnd]):.1f} m over the boundary")

    # --------------------------------------------------------- load centres
    # Every plot that will be connected is one unit of load. Built and planned
    # count; agricultural does not (project doctrine - the farming carries no
    # load, the houses on it do, and those are separately classified B).
    log("building load centres")
    conn = pd.concat([built, planned])
    cen = conn.geometry.representative_point()
    lx = np.floor((cen.x.values - minx) / LOADCELL).astype(int)
    ly = np.floor((maxy - cen.y.values) / LOADCELL).astype(int)
    lny = int((maxy - miny) / LOADCELL) + 1
    lnx = int((maxx - minx) / LOADCELL) + 1
    ok = (lx >= 0) & (lx < lnx) & (ly >= 0) & (ly < lny)
    key = ly[ok] * lnx + lx[ok]
    cnt = np.bincount(key, minlength=lny * lnx)
    occ = np.nonzero(cnt)[0]
    lcy, lcx = occ // lnx, occ % lnx
    LX = minx + (lcx + 0.5) * LOADCELL
    LY = maxy - (lcy + 0.5) * LOADCELL
    LW = cnt[occ].astype(np.float64)
    LW = LW / LW.sum()
    # elevation of each load centre off the SAME 50 m grid the cells use
    li = np.clip(((maxy - LY) / CELL).astype(int), 0, ny - 1)
    lj = np.clip(((LX - minx) / CELL).astype(int), 0, nx - 1)
    LZ = z50[li, lj]
    good = np.isfinite(LZ)
    LX, LY, LW, LZ = LX[good], LY[good], LW[good] / LW[good].sum(), LZ[good]
    log(f"  {len(LX):,} load centres on a {LOADCELL:.0f} m grid, {len(conn):,} connectable plots,"
        f" ground {LZ.min():.1f} - {LZ.max():.1f} m")

    # ------------------------------------------------- C2 gravity reachability
    # A load centre k reaches a works at cell c by gravity when
    #     (z_k - D_COLLECT) - S_MIN * SINUOSITY * dist  >=  (z_c - D_INLET)
    # C2 is the share of the ultimate load for which that holds.
    log("C2 - gravity reachability (this is the slow one)")
    cx = minx + (np.arange(nx) + 0.5) * CELL
    cy = maxy - (np.arange(ny) + 0.5) * CELL
    CX, CY = np.meshgrid(cx, cy)
    idx = np.nonzero(m_bnd & np.isfinite(z50))
    px, py, pz = CX[idx], CY[idx], z50[idx]
    n = len(px)
    C2 = np.zeros(n, np.float32)
    Lw = np.zeros(n, np.float32)          # load-weighted mean straight distance, m
    head = (LZ - D_COLLECT).astype(np.float32)
    grad = np.float32(S_MIN * SINUOSITY)
    CH = 4000
    for s in range(0, n, CH):
        e = min(s + CH, n)
        dx = px[s:e, None] - LX[None, :]
        dy = py[s:e, None] - LY[None, :]
        d = np.sqrt(dx * dx + dy * dy, dtype=np.float64).astype(np.float32)
        need = pz[s:e, None].astype(np.float32) - np.float32(D_INLET) + grad * d
        C2[s:e] = ((head[None, :] >= need) * LW[None, :]).sum(1)
        Lw[s:e] = (d * LW[None, :]).sum(1)
    log(f"  done in {time.time()-t0:.0f} s, C2 range {C2.min():.3f} - {C2.max():.3f},"
        f" conveyance distance {Lw.min()/1000:.1f} - {Lw.max()/1000:.1f} km")

    g_C2 = np.zeros((ny, nx), np.float32)
    g_C2[idx] = C2
    g_Lw = np.full((ny, nx), np.nan, np.float32)
    g_Lw[idx] = Lw
    lw_min = np.nanmin(g_Lw)
    lw_p90 = np.nanpercentile(g_Lw[m_bnd], 90)

    # ----------------------------------------------------------- the criteria
    log("scoring")
    C1 = ramp(d_built, DWELL_HARD_M, DWELL_FULL_M)
    C3 = ramp(d_wadi, WADI_HARD_M, WADI_FULL_M)
    C4 = ramp(free_win_ha, LAND_MIN_HA, LAND_GOOD_HA)
    C5 = 0.5 * ramp(d_trunk, TRUNK_ZERO_M, TRUNK_FULL_M) + \
         0.5 * ramp(np.nan_to_num(g_Lw, nan=lw_p90), lw_p90, lw_min)
    C6 = 0.5 * ramp(d_road, ROAD_ZERO_M, ROAD_FULL_M) + \
         0.5 * ramp(d_major, MAJOR_ZERO_M, MAJOR_FULL_M)
    ag90 = np.nanpercentile(agri_win_ha[m_bnd], 90)
    C7 = 0.5 * ramp(d_agri, AGRI_ZERO_M, AGRI_FULL_M) + \
         0.5 * ramp(agri_win_ha, 0.0, max(ag90, 1.0))

    crit = {"C1_DWELL": C1, "C2_GRAVITY": g_C2, "C3_FLOOD": C3,
            "C4_LAND": C4, "C5_PIPE": C5, "C6_ROAD": C6, "C7_TSE": C7}

    # -------------------------------------------------------- hard exclusions
    ex_wadi = (wadi_frac > 0.0) | (d_wadi < WADI_HARD_M)
    ex_dwell = d_built < DWELL_HARD_M
    ex_plot = plot_frac > 0.10
    ex_land = free_win_ha < LAND_MIN_HA
    allowed = m_bnd & np.isfinite(z50) & ~ex_wadi & ~ex_dwell & ~ex_plot & ~ex_land
    tot = int(m_bnd.sum())
    log(f"  exclusions inside the boundary ({tot:,} cells, {tot*CELL*CELL/1e6:.0f} km2):")
    expc = {}
    for nm, key, m in [("flood / wadi + 100 m", "flood", ex_wadi),
                       (f"< {DWELL_HARD_M:.0f} m to a receptor", "dwell", ex_dwell),
                       ("on a registered plot", "plot", ex_plot),
                       (f"< {LAND_MIN_HA:.0f} ha free in {LAND_WINDOW_M:.0f} m", "land", ex_land)]:
        k = int((m & m_bnd).sum())
        expc[key] = 100 * k / tot
        log(f"    {nm:38s} {k:8,} cells  {100*k/tot:5.1f} %")
    expc["pass_pct"] = 100 * allowed.sum() / tot
    expc["pass_km2"] = allowed.sum() * CELL * CELL / 1e6
    expc["n_load"] = len(LX)
    expc["n_plots"] = len(conn)
    log(f"    {'PASS all four':38s} {int(allowed.sum()):8,} cells  "
        f"{expc['pass_pct']:5.1f} %  = {expc['pass_km2']:.1f} km2")

    raw = np.zeros((ny, nx), np.float32)
    for k, w in WEIGHTS.items():
        raw += np.float32(w) * crit[k].astype(np.float32)
    # SCORE_RAW keeps the weighted sum with NO hard mask, so a site that fails an
    # exclusion can still be compared on merit. The existing works needs it: it
    # fails "on a registered plot" only because the plot IS its own compound.
    score = np.where(allowed, raw, 0.0).astype(np.float32)
    score = np.where(m_bnd, score, -1.0).astype(np.float32)
    log(f"  best score {score.max():.3f} (raw, unmasked, best {raw[m_bnd].max():.3f})")

    # -------------------------------------------------------------- write TIFs
    prof = dict(driver="GTiff", height=ny, width=nx, count=1, dtype="float32",
                crs=f"EPSG:{C.EPSG}", transform=tr50, nodata=-1.0,
                compress="deflate", tiled=True)
    p_suit = os.path.join(C.OUT_SHP, "W10_stp_suitability.tif")
    with rasterio.open(p_suit, "w", **prof) as ds:
        ds.write(score, 1)
        ds.update_tags(1, DESC="STP site suitability 0-1, 0 = excluded, -1 = outside boundary")
    log(f"  wrote {p_suit}")

    order = list(WEIGHTS.keys())
    prof2 = dict(prof); prof2["count"] = len(order); prof2["nodata"] = -1.0
    p_crit = os.path.join(C.OUT_SHP, "W10_stp_criteria.tif")
    with rasterio.open(p_crit, "w", **prof2) as ds:
        for i, k in enumerate(order, 1):
            ds.write(np.where(m_bnd, crit[k], -1.0).astype(np.float32), i)
            ds.set_band_description(i, f"{k} w={WEIGHTS[k]:.2f}")
    log(f"  wrote {p_crit} ({len(order)} bands)")

    # ------------------------------------------------------ candidate picking
    log("picking candidates")
    sep = int(round(MIN_SEPARATION_M / CELL))
    sc = score.copy()
    picks = []
    while len(picks) < N_CANDIDATES:
        k = int(np.argmax(sc))
        i, j = divmod(k, nx)
        if sc[i, j] <= 0:
            break
        picks.append((i, j, float(score[i, j])))
        i0, i1 = max(0, i - sep), min(ny, i + sep + 1)
        j0, j1 = max(0, j - sep), min(nx, j + sep + 1)
        sc[i0:i1, j0:j1] = -1.0
    log(f"  {len(picks)} candidates at >= {MIN_SEPARATION_M/1000:.1f} km separation")

    # contiguous free-land components and the largest inscribed circle, on 10 m
    lab, nlab = ndi.label(free_F, structure=np.ones((3, 3), int))
    comp_area_ha = np.bincount(lab.ravel()) * FINE * FINE / 1e4
    comp_area_ha[0] = 0.0
    insc_F = (ndi.distance_transform_edt(free_F) * FINE).astype(np.float32)

    # ----------------------------------------------------- assemble the table
    def at(fine_arr, x, y):
        j = int((x - minx) / FINE); i = int((maxy - y) / FINE)
        i = min(max(i, 0), fy - 1); j = min(max(j, 0), fx - 1)
        return fine_arr[i, j]

    def at50(arr, x, y):
        j = int((x - minx) / CELL); i = int((maxy - y) / CELL)
        i = min(max(i, 0), ny - 1); j = min(max(j, 0), nx - 1)
        return arr[i, j]

    plots_raw = plots_raw.copy()
    plots_raw["_HA"] = plots_raw.geometry.area / 1e4
    _psi = plots_raw.sindex

    def plot_ha_at(x, y):
        """area of the registered plot the point falls in, 0 if it falls on none"""
        p = Point(x, y)
        for k in _psi.query(p, predicate="intersects"):
            return float(plots_raw["_HA"].iloc[k])
        return 0.0

    trunk_u = trunk.union_all()
    corr_u = corr.union_all()
    built_u = built.geometry
    sidx_built = built.sindex

    rows, geoms = [], []
    listing = [(f"S{n+1}", f"Candidate S{n+1}",
                (minx + (j + 0.5) * CELL, maxy - (i + 0.5) * CELL))
               for n, (i, j, s) in enumerate(picks)]
    listing += [(t, n, xy) for t, n, xy in KNOWN_SITES]

    with rasterio.open(C.TERRAIN) as tds:
        for tag, name, (x, y) in listing:
            pt = Point(x, y)
            zv = float(next(tds.sample([(x, y)]))[0])
            zv = np.nan if zv < -1000 else zv
            comp = int(at(lab, x, y))
            sc_i = {k: float(at50(crit[k], x, y)) for k in order}
            rows.append(dict(
                SITE=tag, NAME=name, X=round(x, 1), Y=round(y, 1),
                Z_VRT_M=round(zv, 2) if np.isfinite(zv) else None,
                Z_50M_M=round(float(at50(z50, x, y)), 2),
                SCORE=round(float(at50(score, x, y)), 4),
                SCORE_RAW=round(float(at50(raw, x, y)), 4),
                ALLOWED=int(bool(at50(allowed, x, y))),
                EX_FLOOD=int(bool(at50(ex_wadi, x, y))),
                EX_DWELL=int(bool(at50(ex_dwell, x, y))),
                EX_PLOT=int(bool(at50(ex_plot, x, y))),
                EX_LAND=int(bool(at50(ex_land, x, y))),
                PLOT_HA=round(float(plot_ha_at(x, y)), 2),
                **{k: round(v, 4) for k, v in sc_i.items()},
                D_DWELL_M=round(float(at(d_built_F, x, y)), 0),
                D_BUILT_M=round(float(at(d_allbuilt_F, x, y)), 0),
                CLR_500=int(at(d_built_F, x, y) >= DWELL_GENERIC_M),
                D_WADI_M=round(float(at(d_wadi_F, x, y)), 0),
                IN_WADI=int(bool(at(m_wadi_F, x, y))),
                ON_PLOT=int(bool(at(m_plot_F, x, y))),
                FREE600_HA=round(float(at50(free_win_ha, x, y)), 1),
                COMP_HA=round(float(comp_area_ha[comp]) if comp else 0.0, 1),
                INSCR_M=round(float(at(insc_F, x, y)) * 2, 0),
                D_TRUNK_M=round(pt.distance(trunk_u), 0),
                D_CORR_M=round(pt.distance(corr_u), 0),
                D_ROAD_M=round(float(at(d_road_F, x, y)), 0),
                D_MAJOR_M=round(float(at(d_major_F, x, y)), 0),
                D_AGRI_M=round(float(at(d_agri_F, x, y)), 0),
                AGRI5K_HA=round(float(at50(agri_win_ha, x, y)), 0),
                CONVEY_KM=round(float(at50(g_Lw, x, y)) / 1000, 2),
                GRAV_PCT=round(100 * sc_i["C2_GRAVITY"], 1),
                D_EXIST_KM=round(pt.distance(Point(*C.STP_EXISTING)) / 1000, 2),
            ))
            geoms.append(pt)

    cand = gpd.GeoDataFrame(rows, geometry=geoms, crs=f"EPSG:{C.EPSG}")
    cand.insert(1, "RANK", cand["SCORE"].rank(ascending=False, method="min").astype(int))
    p_cand = os.path.join(C.OUT_SHP, "W10_stp_candidates.shp")
    cand.to_file(p_cand, encoding="utf-8")
    cand.drop(columns="geometry").to_csv(
        os.path.join(C.OUT_RUN, "p4_stp_candidates.csv"), index=False)
    log(f"  wrote {p_cand} and run/p4_stp_candidates.csv")

    with pd.option_context("display.width", 250, "display.max_columns", 60):
        print(cand[["SITE", "SCORE", "ALLOWED", "GRAV_PCT", "D_DWELL_M", "FREE600_HA",
                    "COMP_HA", "D_TRUNK_M", "Z_VRT_M", "CONVEY_KM", "D_AGRI_M"]].to_string(index=False))

    # ------------------------------------------------------------------- map
    log("drawing the map")
    make_map(score, m_bnd, tr50, (minx, miny, maxx, maxy), bnd, recept, agri,
             m_wadi_F & m_bnd_F, trF, trunk, cand, allowed, expc)

    log(f"DONE in {time.time()-t0:.0f} s")
    return cand


# --------------------------------------------------------------------------- #
def make_map(score, m_bnd, tr50, extent, bnd, recept, agri, m_wadi, trF,
             trunk, cand, allowed, expc):
    """Layout: wide map top-left, method panels underneath, shortlist table right.
    The boundary is 46.4 x 25.5 km (aspect 1.82) so the map axes have to be wide
    and short, or two thirds of the figure comes out white."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Rectangle, Patch
    from matplotlib.lines import Line2D

    minx, miny, maxx, maxy = extent
    ext = (minx, maxx, miny, maxy)

    fig = plt.figure(figsize=(20.0, 12.0), dpi=140)
    ax = fig.add_axes([0.030, 0.335, 0.700, 0.585])

    def flat(mask, colour, z, alpha=1.0):
        ax.imshow(np.where(mask, 1.0, np.nan), extent=ext,
                  cmap=LinearSegmentedColormap.from_list("c", [colour, colour]),
                  vmin=0, vmax=1, interpolation="nearest", zorder=z, alpha=alpha)

    flat(m_bnd, "#f4efe4", 1)                       # study area ground
    flat(m_bnd & ~allowed, "#d9d9d1", 2, 0.88)      # excluded
    flat(m_wadi, "#7fb8e0", 3)                      # 50-yr wadi - drawn OVER the grey,
    #   because every wadi cell is also excluded and the grey buries it completely

    su = np.where(allowed & (score > 0), score, np.nan)
    vmin = float(np.nanpercentile(su, 2)) if np.isfinite(su).any() else 0.0
    vmax = float(np.nanmax(su)) if np.isfinite(su).any() else 1.0
    cmap = LinearSegmentedColormap.from_list(
        "suit", ["#7a1f1f", "#c25a2a", "#e8b83b", "#a8cf4b", "#2f8f3e", "#0d5c2a"])
    im = ax.imshow(su, extent=ext, cmap=cmap, vmin=vmin, vmax=vmax,
                   interpolation="nearest", zorder=4)

    agri.plot(ax=ax, facecolor="none", edgecolor="#2f6b23", linewidth=0.16, zorder=5, alpha=0.8)
    recept.plot(ax=ax, facecolor="#585858", edgecolor="none", linewidth=0, zorder=6, alpha=0.9)
    trunk.plot(ax=ax, color="#111111", linewidth=2.0, zorder=7)
    bnd.boundary.plot(ax=ax, color="#222222", linewidth=1.5, zorder=8)

    kn = cand[cand["SITE"].isin(["EXISTING", "SOUTH"])]
    sh = cand[~cand["SITE"].isin(["EXISTING", "SOUTH"])]
    ax.scatter(sh.geometry.x, sh.geometry.y, s=190, marker="*", c="#ffffff",
               edgecolors="#111111", linewidths=1.4, zorder=11)
    for _, r in sh.iterrows():
        ax.annotate(r["SITE"], (r.geometry.x, r.geometry.y), xytext=(10, 8),
                    textcoords="offset points", fontsize=10, fontweight="bold",
                    color="#111111", zorder=12,
                    bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="#111111",
                              lw=0.6, alpha=0.93))
    for _, r in kn.iterrows():
        mk = "s" if r["SITE"] == "EXISTING" else "^"
        cc = "#111111" if r["SITE"] == "EXISTING" else "#c0208a"
        lb = "Existing works" if r["SITE"] == "EXISTING" else "Proposed south site"
        # the south site sits ~1.5 km from S9, so its label goes left, not right
        off = (13, 17) if r["SITE"] == "EXISTING" else (-142, -4)
        ax.scatter([r.geometry.x], [r.geometry.y], s=210, marker=mk, c=cc,
                   edgecolors="white", linewidths=1.6, zorder=11)
        ax.annotate(lb, (r.geometry.x, r.geometry.y), xytext=off,
                    textcoords="offset points", fontsize=10, fontweight="bold",
                    color=cc, zorder=12,
                    bbox=dict(boxstyle="round,pad=0.18", fc="white", ec=cc, lw=0.9, alpha=0.95))

    ax.set_xlim(minx, maxx); ax.set_ylim(miny, maxy)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, EPSG:32640)", fontsize=9)
    ax.set_ylabel("Northing (m)", fontsize=9)
    ax.tick_params(labelsize=8)

    # scale bar and north arrow go bottom RIGHT - the bottom left is where the
    # proposed south site and S9 sit, and the labels collide with the bar there
    sb = 5000.0
    x0 = maxx - 0.395 * (maxx - minx); y0 = miny + 0.075 * (maxy - miny)
    for k in range(3):
        ax.add_patch(Rectangle((x0 + k * sb, y0), sb, 340,
                               facecolor="#111111" if k % 2 == 0 else "#ffffff",
                               edgecolor="#111111", lw=0.8, zorder=13))
    for k in range(4):
        ax.text(x0 + k * sb, y0 - 950, f"{int(k*5)}", ha="center", fontsize=8, zorder=13)
    ax.text(x0 + 3 * sb + 700, y0 + 40, "km", fontsize=8.5, zorder=13)

    nx_, ny_ = maxx - 0.035 * (maxx - minx), miny + 0.055 * (maxy - miny)
    ax.annotate("", xy=(nx_, ny_ + 2400), xytext=(nx_, ny_),
                arrowprops=dict(facecolor="#111111", width=3.2, headwidth=11), zorder=13)
    ax.text(nx_, ny_ + 2750, "N", ha="center", fontsize=12, fontweight="bold", zorder=13)

    fig.text(0.030, 0.963,
             "W10 Phase 4.3   |   Sewage treatment plant site suitability, Ibri study area (531.4 km$^2$)",
             fontsize=16, fontweight="bold", ha="left")
    fig.text(0.030, 0.939,
             "Weighted multi-criteria surface on a 50 m grid with the hard exclusions of PAM-GUD-201 "
             "Table 8 (p43) and PAM-GUD-203 Tables 27-28 (p63-64) applied.   Grey = excluded;  "
             f"colour = score among the {expc['pass_km2']:.0f} km$^2$ ({expc['pass_pct']:.0f} %) that passes all four.",
             fontsize=10, ha="left", color="#333333")

    cax = fig.add_axes([0.7385, 0.450, 0.0105, 0.290])
    cb = fig.colorbar(im, cax=cax, orientation="vertical")
    cb.set_label("suitability score", fontsize=8.5, labelpad=4)
    cb.ax.yaxis.set_label_position("left")     # right side is the table, label clips
    cb.ax.yaxis.set_ticks_position("left")
    cb.ax.tick_params(labelsize=7.5)

    leg = [Patch(fc="#d9d9d1", ec="#999", label="excluded (buffer / flood / plot / land)"),
           Patch(fc="#8fbfe0", ec="none", label="50-yr flood hazard class 4-6 (wadi)"),
           Patch(fc="#585858", ec="none", label="odour receptors (built plots)"),
           Patch(fc="none", ec="#2f6b23", label="agricultural plots (TSE customers)"),
           Line2D([], [], color="#111111", lw=2.0, label="given trunk main"),
           Line2D([], [], marker="*", ls="none", mfc="#fff", mec="#111", ms=14, label="candidate site"),
           Line2D([], [], marker="s", ls="none", mfc="#111", mec="#fff", ms=9, label="existing works"),
           Line2D([], [], marker="^", ls="none", mfc="#c0208a", mec="#fff", ms=10, label="proposed south site")]
    ax.legend(handles=leg, loc="upper right", fontsize=8.8, framealpha=0.94, ncols=2,
              facecolor="white", edgecolor="#666").set_zorder(14)

    # ---------------------------------------------------- shortlist table, right
    axt = fig.add_axes([0.762, 0.335, 0.226, 0.585]); axt.axis("off")
    cols = ["SITE", "SCORE", "GRAV\n%", "DWELL\nm", "FREE\nha", "TRUNK\nm", "GL\nm", "CONV\nkm"]
    body = [[("EXIST." if r["SITE"] == "EXISTING" else r["SITE"]),
             f"{r['SCORE']:.3f}", f"{r['GRAV_PCT']:.0f}", f"{r['D_DWELL_M']:.0f}",
             f"{r['FREE600_HA']:.0f}", f"{r['D_TRUNK_M']:.0f}",
             f"{r['Z_VRT_M']:.1f}" if r["Z_VRT_M"] is not None else "-",
             f"{r['CONVEY_KM']:.1f}"]
            for _, r in cand.iterrows()]
    tb = axt.table(cellText=body, colLabels=cols, loc="upper center", cellLoc="center")
    tb.auto_set_font_size(False); tb.set_fontsize(8.6); tb.scale(1.0, 1.60)
    for (r, c), cell in tb.get_celld().items():
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_facecolor("#26415e"); cell.set_text_props(color="white", fontweight="bold")
        elif body[r - 1][0] in ("EXIST.", "SOUTH"):
            cell.set_facecolor("#f7dcef"); cell.set_text_props(fontweight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f2f2ee")
    axt.text(0.5, 1.005, "SHORTLIST AND THE TWO KNOWN SITES", ha="center", va="bottom",
             transform=axt.transAxes, fontsize=10, fontweight="bold")
    axt.text(0.0, 0.28,
             "GRAV %  share of the ultimate load reaching\n"
             "        the site by gravity at 0.10 %\n"
             "DWELL   metres to the nearest odour receptor\n"
             "FREE    free land in a 650 m square, ha\n"
             "TRUNK   metres to the given trunk main\n"
             "GL      ground level, 0.5 m terrain, m\n"
             "CONV    load-weighted conveyance distance",
             transform=axt.transAxes, fontsize=7.9, family="monospace", va="top", ha="left",
             color="#333333")

    # ------------------------------------------------- method panels, under the map
    panels = [
        (0.030, "CRITERIA AND WEIGHTS",
         "C2  gravity reachability of the load  0.25\n"
         "C1  separation from dwellings         0.20\n"
         "C4  land available, 30 ha target      0.15\n"
         "C5  conveyance cost, trunk + popultn  0.15\n"
         "C7  treated-effluent reuse proximity  0.10\n"
         "C6  road access                       0.08\n"
         "C3  flood margin beyond the exclusion 0.07\n"
         "                                      ----\n"
         "                                      1.00"),
        (0.215, "HARD EXCLUSIONS",
         f"flood hazard class 4-6, plus 100 m      {expc['flood']:4.1f} %\n"
         "  G203 p63 Tab 27(i); the 100 m is ours\n"
         f"under 300 m to an odour receptor        {expc['dwell']:4.1f} %\n"
         "  G201 p43 Tab 8, large STP 300-1000 m\n"
         f"on a registered MoHUP plot              {expc['plot']:4.1f} %\n"
         f"under 20 ha free in a 650 m square      {expc['land']:4.1f} %\n"
         "(they overlap, so these do not add up)\n"
         f"{expc['pass_km2']:.1f} km2 = {expc['pass_pct']:.1f} % passes all four"),
        (0.420, "LAND REQUIREMENT   G203 p64 Table 28",
         "49,700 m3/d ultimate, +10 % = 54,700 m3/d\n"
         "MBR      0.45-0.90 m2/(m3/d)  2.5 -  4.9 ha\n"
         "SBR/MBBR 0.90-1.80            4.9 -  9.8 ha\n"
         "IFAS     1.20-2.50            6.6 - 13.7 ha\n"
         "CAS/EA   1.80-3.60            9.8 - 19.7 ha\n"
         "adopted 20 ha minimum (CAS/EA upper bound),\n"
         "30 ha target with +50 % for phasing, sludge,\n"
         "TSE storage and the solar farm G203 p64 asks\n"
         "the designer to assess"),
        (0.610, "NOT SCORED - NO DATA EXISTS YET",
         "land ownership and acquisition\n"
         "geotechnical / bearing capacity  G201 p40\n"
         "groundwater depth, vulnerability G201 p43\n"
         "prevailing wind direction        G203 p63(e)\n"
         "odour dispersion model, 5 OU     G201 p43\n"
         "EIA                              G201 p44\n"
         "wellfield and falaj protection zones\n"
         "archaeology, power supply, MoHUP consent"),
    ]
    for x, head, txt in panels:
        axp = fig.add_axes([x, 0.045, 0.190, 0.250]); axp.axis("off")
        axp.text(0.0, 1.0, head, transform=axp.transAxes, fontsize=9.2,
                 fontweight="bold", va="top", ha="left", color="#26415e")
        axp.text(0.0, 0.86, txt, transform=axp.transAxes, fontsize=7.5,
                 family="monospace", va="top", ha="left")

    axg = fig.add_axes([0.800, 0.045, 0.190, 0.250]); axg.axis("off")
    axg.text(0.0, 1.0, "GRAVITY SCREENING TEST (C2)", transform=axg.transAxes, fontsize=9.2,
             fontweight="bold", va="top", ha="left", color="#26415e")
    axg.text(0.0, 0.86,
             "load centre k reaches a works at c when\n"
             "  (zk - 2.0) - 0.0013 d >= zc - 6.0\n"
             "0.0010 laid gradient (the trunk's own\n"
             "DN1000 grade), 1.30 sinuosity, 2.0 m\n"
             "collector invert, 6.0 m deepest inlet.\n"
             f"{expc['n_load']:,} load centres on a 500 m grid\n"
             f"carry the {expc['n_plots']:,} built + planned plots.\n"
             "C2 is the share of that load for which\n"
             "the test holds. A screen, not a design:\n"
             "it does not check the 12 m cover limit\n"
             "at intermediate chambers.",
             transform=axg.transAxes, fontsize=7.5, family="monospace", va="top", ha="left")

    fig.text(0.030, 0.014,
             "2621 Ibri Sewer & STP   |   Renardet / Nama Water Services   |   W10 greenfield run, Phase 4.3   |   "
             "terrain IBRI_0p5_VRT2 (0.5 m bare earth)   |   flood Hazard_T50y (50-yr)   |   plots MoHUP + W3 class v4   |   EPSG:32640",
             fontsize=7.8, color="#555555")

    out = os.path.join(C.OUT_IMG, "W10_P4_stp_suitability.png")
    fig.savefig(out, dpi=140, facecolor="white")
    plt.close(fig)
    log(f"  wrote {out}")


if __name__ == "__main__":
    main()
