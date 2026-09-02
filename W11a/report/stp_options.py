"""stp_options — the measurements and figures behind `W11a/docs/STP_SITE_OPTIONS.md`.

The TOR asks for STP site options judged on distance from houses, connectivity and
inflow (scope p13: *"The Consultant shall prepare and submit minimum three option for
STP"*, and *"design report for STP location"*).  This module measures the candidates.
It decides nothing: no weighting, no ranking, no phasing.  It produces the numbers an
options appraisal needs and the two figures that carry them.

WHAT IT DOES NOT DO, deliberately
---------------------------------
It does **not** rebuild W10's weighted suitability surface (`W10/py/p4_stp_siting.py`,
`W10/docs/STP_SITING.md`).  That surface invented ten sites of its own and scored them
against weights it chose itself.  The four candidate sites that are actually in the
project data — `SHP/IBRI STP/IBRI STP.shp`, `SHP/Proposed STP/Proposed STP.shp` — were
never measured at all.  This module measures those, plus the existing works, plus W10's
own top-ranked cell so the two studies can be read against each other.

EVERY NUMBER COMES FROM AN ARTEFACT
-----------------------------------
Terrain          Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt      0.5 m, EPSG:32640
Hazard           Data/04 Lekhuwair/Hazard_T50y.tif            3 m, nodata -9999.0
Cadastre         Hydraulic/SHP/MoHUP_DATA/MoH_Plots.shp       61,272 plots
Plot class       W3/shp/MoH_Plots_class_v4.shp                B built / P planned / A agri
Load             W11a/shp/W11a.gpkg [servicing]               187 sets, Q_ADF_M3D
Trunk            W11a/shp/W11a_trunk.gpkg [reaches, nodes]    85.5 km, laid levels
Sites            Hydraulic/SHP/IBRI STP, SHP/Proposed STP     1 existing + 4 proposed
TE (proposed)    W7/shp/EXISTING_TE_LINE.shp                  49.4 km, all OP_STATUE=0
NWS concept STP  W7/shp/EXISTING_STP_PT.shp                   the 29,038 m3/d SUREKHA record

Both rasters carry nodata **-9999.0, which is finite**, so `np.isfinite` alone passes it.
Guarded in `_sample()` and in `hazard_stats()`.

GUIDELINE VALUES — quoted from the PDF, with the page
-----------------------------------------------------
G201-p43  Table 8   buffer, STP large        300 m - 1000 m, "Based on odour modelling
                                             (5 Odour Units OU contour)"
G201-p43  Table 8   buffer, STP small/medium 500 m, "Generic default based on Water
                                             Corporation practice"
G201-p44  Table 8   sewage pumping station   30 m to residential
G203-p63  Table 27  site selection criteria  fifteen headings, (m) is "Buffer area
                                             requirement from residential zones" - the
                                             guideline names the criterion and gives no
                                             number for it
G203-p64  Table 28  land area requirement    m2 per m3/d, by technology
G203-p65  s10.2.1   STP size classes         large >= 20,000 m3/d
G203-p65  Table 29  design flow              "+10% increment for STP design as
                                             operational safety flow allowance"
G203-p29  Table 11  minimum gradient         0.75 mm/m for DN900 and above
G203-p33  s4.6.3    minimum cover            1.30 m to the crown

PROJECT ASSUMPTIONS — ours, not the guideline's.  Labelled on every figure.
--------------------------------------------------------------------------
Wadi ground   = 50-year hazard class 4-6.  AR&R classes keyed on danger to people, used
                as a proxy for G203-p30 4.4.1 "areas subject to washout", which is a
                SCOUR criterion (philosophy H1a).
Collector invert 2.0 m below ground where a load enters the trunk system.
Works inlet   6.0 m below site ground as the base case; 9.0 m reported as sensitivity,
                because the W11a trunk actually arrives at the existing works 8.78 m
                below ground (measured, `W11a_trunk.gpkg [nodes]`).
Sinuosity     MEASURED on the W11a trunk, not assumed - see `measure_sinuosity()`.
                W10 used 1.30 and flagged it as uncalibrated.

Run:  python W11a/report/stp_options.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import figkit as fk  # noqa: E402

BASE = fk.BASE
HYD = fk.HYD
ROOT = fk.ROOT

TERRAIN = BASE / "Data" / "Terrain" / "Sat_0p5m" / "IBRI_0p5_VRT2.vrt"
#: The 5 m component OF THAT SAME VRT.  Used only for the 25 m mask grid, because the
#: 0.5 m blend carries no overviews and a decimated read of 48 x 27 km off it would
#: touch 5.2 billion source pixels.  Every point elevation quoted anywhere - candidate
#: ground levels, load-centre levels - is sampled from the 0.5 m VRT itself.
TERRAIN_5M = BASE / "Data" / "Terrain" / "Sat_0p5m" / "ibri_blend.tif"
PLOTS_CLASS = ROOT / "W3" / "shp" / "MoH_Plots_class_v4.shp"
PLOTS_RAW = HYD / "SHP" / "MoHUP_DATA" / "MoH_Plots.shp"
SITES_STP = HYD / "SHP" / "IBRI STP" / "IBRI STP.shp"
SITES_PROP = HYD / "SHP" / "Proposed STP" / "Proposed STP.shp"
TE_LINE = ROOT / "W7" / "shp" / "EXISTING_TE_LINE.shp"
STP_PT = ROOT / "W7" / "shp" / "EXISTING_STP_PT.shp"
ROADS = HYD / "SHP" / "Road centerline 2" / "Road_Centercline.shp"

NODATA = -9998.0  # anything at or below this is "no answer" in either raster

# ------------------------------------------------------------------ guideline values
SMIN_DN900_UP = 0.00075        # G203-p29 Table 11, "900 and above  0.75 mm/m"
MIN_COVER_M = 1.30             # G203-p33 4.6.3
MAX_COVER_M = 12.0             # G203-p33 (recommendation) + philosophy H4
OP_ALLOWANCE = 1.10            # G203-p65 Table 29
LARGE_STP_M3D = 20_000.0       # G203-p65 10.2.1
BUFFER_LARGE_LO, BUFFER_LARGE_HI = 300.0, 1000.0   # G201-p43 Table 8
BUFFER_SMALL_MED = 500.0                            # G201-p43 Table 8
FOOTPRINT_M2_PER_M3D = {       # G203-p64 Table 28
    "MBR": (0.45, 0.90),
    "MBBR": (0.90, 1.80),
    "SBR": (0.90, 1.80),
    "IFAS / hybrid fixed biofilm": (1.20, 2.50),
    "CAS / extended aeration": (1.80, 3.60),
    "Constructed wetland (reed bed)": (10.0, None),
}

# ------------------------------------------------------------- project assumptions
WADI_CLASSES = (4, 5, 6)       # PROJECT ASSUMPTION, philosophy H1a
COLLECTOR_INVERT_M = 2.0       # PROJECT ASSUMPTION
WORKS_INLET_M = 6.0            # PROJECT ASSUMPTION, base case
WORKS_INLET_DEEP_M = 9.0       # PROJECT ASSUMPTION, sensitivity
GRID_M = 500.0                 # load-centre aggregation cell
FREE_CELL_M = 25.0             # free-land raster cell
ROAD_CLEAR_M = 20.0            # PROJECT ASSUMPTION: land within this of a road is not free

# Arabic LANDUSE values in MoH_Plots that mean people are present.
RECEPTOR_LANDUSE = {
    "سكني",                     # residential
    "سكني/تجاري",   # residential / commercial
    "سكنى/زراعى",   # residential / agricultural
    "مسجد",                     # mosque
    "حكومي",               # government (school, clinic)
}
RECEPTOR_BIG_HA = 5.0   # a built plot this large counts only if its land use says people


# ===================================================================== raster helpers

def _sample(path, xy, band=1):
    """Sample a raster at (x, y) pairs.  Returns NaN where the raster has no answer."""
    import rasterio
    with rasterio.open(path) as src:
        v = np.array([r[0] for r in src.sample(xy, indexes=band)], dtype="float64")
    v[~np.isfinite(v)] = np.nan
    v[v <= NODATA] = np.nan           # the finite-nodata trap, both rasters
    return v


def _read_window(path, extent, cell):
    """Read a raster over ``extent`` decimated to ``cell`` metres.  NaN = no answer."""
    import rasterio
    from rasterio.windows import from_bounds
    x0, y0, x1, y1 = extent
    nx = max(2, int(round((x1 - x0) / cell)))
    ny = max(2, int(round((y1 - y0) / cell)))
    with rasterio.open(path) as src:
        win = from_bounds(x0, y0, x1, y1, src.transform)
        a = src.read(1, window=win, out_shape=(ny, nx), boundless=True,
                     fill_value=-9999.0).astype("float64")
    a[~np.isfinite(a)] = np.nan
    a[a <= NODATA] = np.nan
    return a, (x0, x1, y0, y1)


def _edt(mask_true, cell):
    """Distance in metres from every cell to the nearest True cell in ``mask_true``."""
    from scipy import ndimage as ndi
    if not mask_true.any():
        return np.full(mask_true.shape, np.inf)
    return ndi.distance_transform_edt(~mask_true, sampling=(cell, cell))


def _grid_index(x, y, extent, cell, shape):
    x0, x1, y0, y1 = extent
    ny, nx = shape
    col = np.clip(((x - x0) / cell).astype(int), 0, nx - 1)
    row = np.clip(((y1 - y) / cell).astype(int), 0, ny - 1)
    return row, col


# ===================================================================== the candidates

def candidates() -> pd.DataFrame:
    """The sites actually on the table, read from the project's own layers.

    `IBRI STP.shp` was one point when it arrived (2026-08-09 zip: the existing works at
    the superseded E444387 N2563353).  It now holds five, edited 2026-09-01.
    `Proposed STP.shp` arrived 2026-08-09 holding three proposed sites and has never
    been referenced by any script in this repo.  The north-east point differs between
    the two layers by 1.9 km, and both readings are carried.
    """
    import geopandas as gpd
    stp = gpd.read_file(SITES_STP)
    prop = gpd.read_file(SITES_PROP)
    rows = []

    def add(cid, name, g, provenance, note=""):
        rows.append({"CID": cid, "NAME": name, "X": float(g.x), "Y": float(g.y),
                     "PROV": provenance, "NOTE": note})

    for _, r in stp.iterrows():
        pass  # kept explicit below so the identity of each point is written down

    ex = stp[stp["Type"].astype(str).str.lower() == "existing"].iloc[0].geometry
    add("A", "Existing works (expand in place)", ex,
        "SHP/IBRI STP/IBRI STP.shp, Type='Existing'",
        "1,800 m3/d ASEA plant; NWS's own 29,038 m3/d SUREKHA concept sits 120 m south")

    pr = stp[stp["Type"].astype(str).str.lower() == "proposed"].copy()
    pr["x"] = pr.geometry.x
    pr["y"] = pr.geometry.y
    # name them by where they are, not by row order
    for _, r in pr.sort_values("y", ascending=False).iterrows():
        pass

    def nearest(gdf, x, y, tol=50.0):
        d = np.hypot(gdf.geometry.x - x, gdf.geometry.y - y)
        return gdf.iloc[int(d.idxmin())] if d.min() <= tol else None

    add("B", "Proposed south", pr[np.isclose(pr.y, 2558942, atol=200)].iloc[0].geometry,
        "SHP/IBRI STP/IBRI STP.shp, Type='Proposed'",
        "the site quoted in the brief as E442451.3 N2558941.8; the layer holds "
        "E442448.3 N2558942.0, 3.0 m away")
    add("C", "Proposed north-west",
        pr[np.isclose(pr.x, 440797, atol=200)].iloc[0].geometry,
        "SHP/IBRI STP + SHP/Proposed STP (identical point)", "")
    add("D", "Proposed east", pr[np.isclose(pr.x, 452432, atol=200)].iloc[0].geometry,
        "SHP/IBRI STP + SHP/Proposed STP (identical point)", "")
    ne = pr[pr.x > 456000].iloc[0].geometry
    add("E", "Proposed north-east", ne, "SHP/IBRI STP/IBRI STP.shp",
        "SHP/Proposed STP holds a second reading 1.9 km NE at E458738.6 N2577651.0")
    ne2 = prop[prop.geometry.x > 456000].iloc[0].geometry
    add("E2", "Proposed north-east (Aug-09 reading)", ne2,
        "SHP/Proposed STP/Proposed STP.shp", "the 2026-08-09 delivery's position")

    class _P:
        def __init__(self, x, y):
            self.x, self.y = x, y

    add("W10-S1", "W10 surface best cell", _P(443075.0, 2566675.0),
        "W10/run/p4_stp_candidates.csv, rank 1",
        "carried for comparison only - a 50 m cell centre from W10's weighted surface, "
        "not a site anybody has proposed")
    return pd.DataFrame(rows)


# ================================================================== load and sinuosity

def load_grid():
    """A 500 m load grid: published Q spread over the classified plots that carry it.

    Q comes from `W11a.gpkg [servicing]`, which is stage 1's published scope layer and
    sums to the ultimate saturated Q.  Its spatial distribution comes from
    `MoH_Plots_class_v4` classes B (built) and P (planned) — the plots that carry load.
    Nothing here re-derives a flow.
    """
    import geopandas as gpd
    sv = fk.read_layer("W11a.gpkg", "servicing")
    plots = gpd.read_file(PLOTS_CLASS, columns=["CLASS"], encoding="utf-8")
    if plots.crs is None or plots.crs.to_epsg() != fk.EPSG:
        plots = plots.set_crs(fk.CRS, allow_override=True)
    pl = plots[plots["CLASS"].isin(["B", "P"])].copy()
    pl["geometry"] = pl.geometry.representative_point()
    j = gpd.sjoin(pl, sv[["SET_ID", "SYSTEM", "Q_ADF_M3D", "geometry"]],
                  how="inner", predicate="within")
    n = j.groupby("SET_ID").size().rename("n_in_set")
    j = j.join(n, on="SET_ID")
    j["q"] = j["Q_ADF_M3D"] / j["n_in_set"]
    return sv, j


def measure_sinuosity(nodes, reaches):
    """Measured path-length / straight-line ratio, on the W11a trunk itself.

    W10's gravity screen used 1.30 and its own documentation flagged it as
    "not measured on this network".  The trunk gives the real answer: walk every node
    down its DS_NODE chain to the outfall, and compare that path length with the
    straight line.
    """
    ds = dict(zip(nodes.NODE_UID, nodes.DS_NODE))
    length = {}
    for _, r in reaches.iterrows():
        length[r.US_NODE] = length.get(r.US_NODE, 0.0) + float(r.LEN_M)
    outfall = nodes.loc[nodes.NODE_KIND == "outfall"].iloc[0]
    ox, oy = float(outfall.X), float(outfall.Y)
    rows = []
    for _, nd in nodes.iterrows():
        cur, path, guard = nd.NODE_UID, 0.0, 0
        while cur in ds and isinstance(ds[cur], str) and ds[cur]:
            path += length.get(cur, 0.0)
            cur = ds[cur]
            guard += 1
            if guard > 5000:
                break
        straight = float(np.hypot(nd.X - ox, nd.Y - oy))
        if straight > 500.0:
            rows.append((straight, path, path / straight))
    df = pd.DataFrame(rows, columns=["straight_m", "path_m", "ratio"])
    return df


# ======================================================================== measurement

def measure(verbose=True):
    import geopandas as gpd

    def log(*a):
        if verbose:
            print(*a, flush=True)

    cand = candidates()
    xy = list(zip(cand.X, cand.Y))

    # ---------------------------------------------------------------- ground level
    cand["GL_M"] = np.round(_sample(TERRAIN, xy), 2)

    bnd = fk.study_boundary()
    ext = tuple(bnd.total_bounds[[0, 1, 2, 3]])
    x0, y0, x1, y1 = ext
    pad = 1500.0
    ext = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    log(f"working extent {ext[2]-ext[0]:,.0f} x {ext[3]-ext[1]:,.0f} m")

    # ---------------------------------------------------------------- rasters
    dem, dext = _read_window(TERRAIN_5M, ext, FREE_CELL_M)
    haz, _ = _read_window(fk.HAZARD, ext, FREE_CELL_M)
    shape = dem.shape
    log(f"grid {shape[1]} x {shape[0]} at {FREE_CELL_M:.0f} m")
    haz_known = np.isfinite(haz)
    wadi = haz_known & (np.floor(haz) >= min(WADI_CLASSES))
    log(f"hazard grid: {100*haz_known.mean():.1f} % of the frame has an answer; "
        f"{100*wadi.sum()/max(haz_known.sum(),1):.1f} % of the tested part is class >= "
        f"{min(WADI_CLASSES)}")

    # ---------------------------------------------------------------- receptors
    cls = gpd.read_file(PLOTS_CLASS, columns=["CLASS", "LANDUSE", "AREA_M2"],
                        encoding="utf-8")
    if cls.crs is None or cls.crs.to_epsg() != fk.EPSG:
        cls = cls.set_crs(fk.CRS, allow_override=True)
    cls["ha"] = cls.geometry.area / 1e4
    built = cls[cls["CLASS"] == "B"]
    planned = cls[cls["CLASS"] == "P"]
    # W10's rule, reproduced: a built plot >= 5 ha counts as a receptor only if its land
    # use says people are on it.  Two of the eleven big unlabelled parcels ARE the works.
    keep = (built["ha"] < RECEPTOR_BIG_HA) | built["LANDUSE"].isin(RECEPTOR_LANDUSE)
    receptors = built[keep]
    log(f"receptors: {len(receptors):,} built plots kept of {len(built):,} "
        f"({int((~keep).sum())} large unlabelled parcels dropped)")
    plan_res = planned[planned["LANDUSE"].isin(RECEPTOR_LANDUSE)]
    log(f"planned plots with a residential/sensitive land use: {len(plan_res):,}")

    def dist_to(gdf, name):
        from rasterio.features import rasterize
        from rasterio.transform import from_origin
        tr = from_origin(dext[0], dext[3], FREE_CELL_M, FREE_CELL_M)
        m = rasterize(((g, 1) for g in gdf.geometry), out_shape=shape, transform=tr,
                      fill=0, all_touched=True).astype(bool)
        d = _edt(m, FREE_CELL_M)
        r, c = _grid_index(cand.X.values, cand.Y.values, dext, FREE_CELL_M, shape)
        cand[name] = np.round(d[r, c], 0)
        return m

    m_recept = dist_to(receptors, "D_RECEPT_M")
    dist_to(built, "D_BUILT_M")
    dist_to(plan_res, "D_PLANRES_M")
    dist_to(cls, "D_ANYPLOT_M")

    # ---------------------------------------------------------------- free land
    from rasterio.features import rasterize
    from rasterio.transform import from_origin
    tr = from_origin(dext[0], dext[3], FREE_CELL_M, FREE_CELL_M)
    m_plot = rasterize(((g, 1) for g in cls.geometry), out_shape=shape, transform=tr,
                       fill=0, all_touched=True).astype(bool)
    roads = gpd.read_file(ROADS)
    if roads.crs is None or roads.crs.to_epsg() != fk.EPSG:
        roads = roads.set_crs(fk.CRS, allow_override=True)
    m_road = rasterize(((g, 1) for g in roads.geometry), out_shape=shape, transform=tr,
                       fill=0, all_touched=True).astype(bool)
    d_road = _edt(m_road, FREE_CELL_M)
    free = (~m_plot) & (~wadi) & (d_road > ROAD_CLEAR_M) & np.isfinite(dem)
    log(f"free land in the frame: {free.sum()*FREE_CELL_M**2/1e6:,.1f} km2 "
        f"({100*free.mean():.1f} % of the frame)")

    # free area inside a square window, in hectares
    from scipy import ndimage as ndi
    for win_m in (600.0, 800.0):
        k = int(round(win_m / FREE_CELL_M))
        k += (k + 1) % 2                        # odd, so the window is centred
        s = ndi.uniform_filter(free.astype("float32"), size=k, mode="constant")
        ha = s * (k * FREE_CELL_M) ** 2 / 1e4
        r, c = _grid_index(cand.X.values, cand.Y.values, dext, FREE_CELL_M, shape)
        cand[f"FREE{int(win_m)}_HA"] = np.round(ha[r, c], 1)

    # ---------------------------------------------------------------- hazard
    d_wadi = _edt(wadi, FREE_CELL_M)
    r, c = _grid_index(cand.X.values, cand.Y.values, dext, FREE_CELL_M, shape)
    cand["D_WADI_M"] = np.round(d_wadi[r, c], 0)
    hz = _sample(fk.HAZARD, xy)
    cand["HAZ_CLASS"] = [("-" if not np.isfinite(v) else f"{int(np.floor(v))}") for v in hz]
    # untested share within 1 km of each site
    k1 = int(round(1000.0 / FREE_CELL_M))
    unt = ndi.uniform_filter((~haz_known).astype("float32"), size=2 * k1 + 1,
                             mode="constant")
    cand["UNTEST1K_PC"] = np.round(100.0 * unt[r, c], 1)

    # ---------------------------------------------------------------- load and gravity
    sv, jload = load_grid()
    central = sv[sv["SYSTEM"] == "central"]
    q_central = float(central["Q_ADF_M3D"].sum())
    q_all = float(sv["Q_ADF_M3D"].sum())
    log(f"published Q: all systems {q_all:,.0f} m3/d, central-STP sets "
        f"{q_central:,.0f} m3/d over {len(central)} of {len(sv)} sets")

    jc = jload[jload["SYSTEM"] == "central"].copy()
    gx = np.floor(jc.geometry.x / GRID_M).astype(int)
    gy = np.floor(jc.geometry.y / GRID_M).astype(int)
    jc["gx"], jc["gy"] = gx, gy
    cells = jc.groupby(["gx", "gy"]).agg(q=("q", "sum"),
                                         n=("q", "size")).reset_index()
    cells["cx"] = (cells.gx + 0.5) * GRID_M
    cells["cy"] = (cells.gy + 0.5) * GRID_M
    cells["z"] = _sample(TERRAIN, list(zip(cells.cx, cells.cy)))
    bad = ~np.isfinite(cells["z"])
    if bad.any():
        log(f"  {int(bad.sum())} of {len(cells)} load cells have no terrain answer "
            f"({100*cells.loc[bad,'q'].sum()/cells['q'].sum():.2f} % of the load) "
            f"- excluded from the gravity fraction and reported")
    cells = cells[~bad]
    log(f"load grid: {len(cells)} cells of {GRID_M:.0f} m carrying "
        f"{cells['q'].sum():,.0f} m3/d")

    # measured sinuosity
    tn = fk.read_layer("W11a_trunk.gpkg", "nodes")
    trk = fk.read_layer("W11a_trunk.gpkg", "reaches")
    sin = measure_sinuosity(tn, trk)
    SIN = float(np.median(sin.ratio))
    log(f"trunk sinuosity MEASURED on {len(sin)} nodes: median {SIN:.3f}, "
        f"p75 {np.percentile(sin.ratio,75):.3f}, p90 {np.percentile(sin.ratio,90):.3f} "
        f"(W10 assumed 1.30)")

    outf = tn.loc[tn.NODE_KIND == "outfall"].iloc[0]
    inv_works = float(outf.INV_M)
    gl_works = float(outf.GRD_M)
    log(f"trunk outfall: E{outf.X:,.1f} N{outf.Y:,.1f} GL {gl_works:.2f} "
        f"INV {inv_works:.2f} depth {gl_works-inv_works:.2f} m, "
        f"Q {outf.Q_ADF_M3D:,.0f} m3/d, {outf.Q_PK_LS:,.0f} L/s")

    qz = cells["q"].values
    cz = cells["z"].values
    cxx, cyy = cells["cx"].values, cells["cy"].values
    qtot = qz.sum()

    for tag, inlet in (("", WORKS_INLET_M), ("_D9", WORKS_INLET_DEEP_M)):
        frac, conv = [], []
        for _, s in cand.iterrows():
            d = np.hypot(cxx - s.X, cyy - s.Y) * SIN
            ok = (cz - COLLECTOR_INVERT_M) - SMIN_DN900_UP * d >= (s.GL_M - inlet)
            frac.append(100.0 * qz[ok].sum() / qtot)
            conv.append(float((qz * d).sum() / qtot / 1000.0))
        cand[f"GRAV_PC{tag}"] = np.round(frac, 1)
        if not tag:
            cand["CONV_KM"] = np.round(conv, 2)

    # load centroid
    lcx = float((qz * cxx).sum() / qtot)
    lcy = float((qz * cyy).sum() / qtot)
    log(f"load centroid (Q-weighted, central sets): E{lcx:,.0f} N{lcy:,.0f}")
    cand["D_LOADC_KM"] = np.round(np.hypot(cand.X - lcx, cand.Y - lcy) / 1000.0, 2)

    # ------------------------------------------------- extension of the built trunk
    # For a works downstream of the existing one the trunk is EXTENDED, not re-drawn.
    # Required invert at the site = GL - (min cover + OD).  OD is taken as DN, which
    # understates it by the wall thickness and is stated as such.
    dn_out = int(trk.iloc[-1].DN) if "DN" in trk else 1700
    dn_out = int(trk.sort_values("LEN_M").DN.iloc[-1]) if False else int(trk.DN.max())
    inv_needed = cand.GL_M - (MIN_COVER_M + dn_out / 1000.0)
    dpath = np.hypot(cand.X - float(outf.X), cand.Y - float(outf.Y)) * SIN
    cand["EXT_KM"] = np.round(dpath / 1000.0, 2)
    cand["FALL_REQ_M"] = np.round(SMIN_DN900_UP * dpath, 2)
    cand["FALL_AVAIL_M"] = np.round(inv_works - inv_needed, 2)
    cand["SURPLUS_M"] = np.round(cand.FALL_AVAIL_M - cand.FALL_REQ_M, 2)
    # The one number that reads the same way for every site: the COVER at the site if
    # the existing trunk were carried on from its outfall at the Table 11 minimum.
    # Negative = the pipe would daylight, i.e. there is surplus fall and it is laid
    # steeper.  Over MAX_COVER_M = the trunk cannot be extended there at all, and the
    # site can only be a works for load that is upstream of IT.
    # ENDPOINT TEST ONLY - it says nothing about cover on the ground in between.
    cand["COV_AT_SITE_M"] = np.round(MIN_COVER_M - cand.SURPLUS_M, 2)
    cand["EXT_OK"] = np.where(cand.COV_AT_SITE_M <= MAX_COVER_M, "yes", "NO")

    # ---------------------------------------------------------------- TE prospects
    agri = cls[cls["CLASS"] == "A"]
    dist_to(agri, "D_AGRI_M")
    tra = from_origin(dext[0], dext[3], FREE_CELL_M, FREE_CELL_M)
    m_agri = rasterize(((g, 1) for g in agri.geometry), out_shape=shape, transform=tra,
                       fill=0, all_touched=True).astype(bool)
    k5 = int(round(5000.0 / FREE_CELL_M))
    a5 = ndi.uniform_filter(m_agri.astype("float32"), size=2 * k5 + 1, mode="constant")
    cand["AGRI5K_HA"] = np.round(a5[r, c] * (2 * k5 + 1) ** 2 * FREE_CELL_M ** 2 / 1e4, 0)
    te = gpd.read_file(TE_LINE)
    if te.crs is None or te.crs.to_epsg() != fk.EPSG:
        te = te.set_crs(fk.CRS, allow_override=True)
    cand["D_TE_M"] = [round(float(te.distance(gpd.points_from_xy([s.X], [s.Y])[0]).min()), 0)
                      for _, s in cand.iterrows()]

    # ---------------------------------------------------------------- road access
    cand["D_ROAD_M"] = np.round(d_road[r, c], 0)
    dual = roads[roads.get("dual", pd.Series(0, index=roads.index)).fillna(0)
                 .astype(float) == 1] if "dual" in roads else roads.iloc[0:0]
    if len(dual):
        m_dual = rasterize(((g, 1) for g in dual.geometry), out_shape=shape,
                           transform=tr, fill=0, all_touched=True).astype(bool)
        cand["D_DUAL_M"] = np.round(_edt(m_dual, FREE_CELL_M)[r, c], 0)

    # ---------------------------------------------------------------- distances
    ax, ay = float(cand.loc[cand.CID == "A", "X"].iloc[0]), \
        float(cand.loc[cand.CID == "A", "Y"].iloc[0])
    cand["D_EXIST_KM"] = np.round(np.hypot(cand.X - ax, cand.Y - ay) / 1000.0, 2)
    tp = trk.geometry.union_all() if hasattr(trk.geometry, "union_all") else \
        trk.geometry.unary_union
    cand["D_TRUNK_M"] = [round(float(tp.distance(
        gpd.points_from_xy([s.X], [s.Y])[0])), 0) for _, s in cand.iterrows()]
    ps = (449899.59, 2567301.72)
    cand["D_PS_KM"] = np.round(np.hypot(cand.X - ps[0], cand.Y - ps[1]) / 1000.0, 2)
    inb = bnd.geometry.iloc[0]
    cand["IN_BOUND"] = [bool(inb.contains(gpd.points_from_xy([s.X], [s.Y])[0]))
                        for _, s in cand.iterrows()]

    # ------------------------------------------------- what a satellite would catch
    # A site that takes only part of the load by gravity is not a failed central works;
    # it is a candidate SATELLITE.  For each candidate, record the load that does reach
    # it and where that load sits, so the split option can be sized.
    sat = []
    for _, s in cand.iterrows():
        d = np.hypot(cxx - s.X, cyy - s.Y) * SIN
        ok = (cz - COLLECTOR_INVERT_M) - SMIN_DN900_UP * d >= (s.GL_M - WORKS_INLET_M)
        qq = qz[ok]
        sat.append({"CID": s.CID, "Q_GRAV_M3D": round(float(qq.sum()), 0),
                    "N_CELL": int(ok.sum()),
                    "X_MED": (round(float(np.median(cxx[ok])), 0) if ok.any() else np.nan),
                    "Y_MED": (round(float(np.median(cyy[ok])), 0) if ok.any() else np.nan),
                    "HAUL_KM": (round(float((qq * np.hypot(cxx[ok] - s.X,
                                                          cyy[ok] - s.Y)).sum()
                                            / max(qq.sum(), 1e-9) * SIN / 1000.0), 2)
                                if ok.any() else np.nan)})
    cand = cand.merge(pd.DataFrame(sat), on="CID", how="left")

    # spare head per load cell, for the figure: how much margin, not just yes/no
    spare = {}
    for _, s in cand.iterrows():
        d = np.hypot(cxx - s.X, cyy - s.Y) * SIN
        spare[s.CID] = (cz - COLLECTOR_INVERT_M) - SMIN_DN900_UP * d - (s.GL_M
                                                                        - WORKS_INLET_M)

    meta = {
        "spare": spare, "q_cells": qz,
        "q_all": q_all, "q_central": q_central,
        "q_design": q_central * OP_ALLOWANCE,
        "sinuosity": SIN, "sin_df": sin,
        "inv_works": inv_works, "gl_works": gl_works,
        "outfall_q": float(outf.Q_ADF_M3D), "outfall_qpk": float(outf.Q_PK_LS),
        "load_centroid": (lcx, lcy), "cells": cells,
        "dn_out": dn_out, "n_receptors": len(receptors),
        "n_planres": len(plan_res), "n_built": len(built),
        "haz_known_pc": 100.0 * float(np.isfinite(haz).mean()),
        "free_km2": free.sum() * FREE_CELL_M ** 2 / 1e6,
        "servicing": sv, "trunk": trk, "trunk_nodes": tn,
        "receptors": receptors, "planres": plan_res, "agri": agri,
        "free_mask": free, "wadi_mask": wadi, "haz_known": haz_known,
        "dext": dext, "cell": FREE_CELL_M, "boundary": bnd,
        "d_recept_grid": None,
    }
    return cand, meta


def land_requirement(q_design):
    rows = []
    for tech, (lo, hi) in FOOTPRINT_M2_PER_M3D.items():
        a_lo = lo * q_design / 1e4
        a_hi = (hi * q_design / 1e4) if hi else None
        rows.append({"technology": tech, "m2_per_m3d_lo": lo, "m2_per_m3d_hi": hi,
                     "ha_lo": round(a_lo, 1),
                     "ha_hi": (round(a_hi, 1) if a_hi else None)})
    return pd.DataFrame(rows)


# ============================================================================ figures

def fig_site_options(cand, meta, stem="F20_stp_site_options"):
    """Where the candidates are, what is near them, and what has no hazard answer."""
    import geopandas as gpd
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    bnd = meta["boundary"]
    ext = fk.extent_of(bnd, pad=0.05)
    n_large = int((cand.D_RECEPT_M < BUFFER_LARGE_HI).sum())
    fig, ax, note = fk.map_frame(
        ext,
        title=(f"{n_large} of {len(cand)} candidate STP sites sit inside the 1,000 m "
               f"upper bound of the large-STP buffer band"),
        subtitle=("Buffer band 300-1,000 m for a large STP, PAM-GUD-201 p43 Table 8, set "
                  "by odour modelling to the 5 OU contour - no model exists yet, so the "
                  "band cannot be closed. Hatched ground has no 50-year hazard answer. "
                  "Wadi = hazard class 4-6, a PROJECT ASSUMPTION standing in for "
                  "G203-p30 4.4.1 'areas subject to washout'."))
    known, wadi, rext = fk.hazard_coverage(ext)
    # The untested area is most of the frame, so it is drawn light: heavy shading over
    # two thirds of a map reads as "no data anywhere" and buries the receptors.
    fk.hatch_untested(ax, ~known, rext, face_alpha=0.07, zorder=1.5)

    meta["agri"].plot(ax=ax, color="#a8c79a", edgecolor="none", zorder=2, alpha=0.9)
    meta["receptors"].plot(ax=ax, color="#8c7a63", edgecolor="none",
                           linewidth=0.0, zorder=3)
    meta["trunk"].plot(ax=ax, **fk.tier_style("trunk main"), zorder=5)
    bnd.boundary.plot(ax=ax, color=fk.C.BOUNDARY, lw=1.2, ls="--", zorder=6)

    lcx, lcy = meta["load_centroid"]
    ax.plot([lcx], [lcy], marker="X", ms=11, mfc=fk.C.FLAG, mec=fk.C.INK, mew=1.0,
            zorder=9, ls="none")

    import matplotlib.patheffects as pe
    off = {"A": (9, -14), "B": (9, 6), "C": (9, 6), "D": (9, 6), "E": (-24, 6),
           "E2": (9, 6), "W10-S1": (9, -16)}
    for _, s in cand.iterrows():
        col = fk.C.OUTFALL if s.CID == "A" else fk.C.MAIN
        mk = "s" if s.CID == "A" else "o"
        if s.CID.startswith("W10"):
            col, mk = fk.C.GREY, "^"
        plt_circle(ax, s.X, s.Y, BUFFER_LARGE_HI, fk.C.STATION, ls=":")
        plt_circle(ax, s.X, s.Y, BUFFER_LARGE_LO, fk.C.FAIL, ls="-")
        ax.plot([s.X], [s.Y], marker=mk, ms=8.5, mfc=col, mec="white", mew=1.1,
                zorder=10, ls="none")
        ax.annotate(s.CID, (s.X, s.Y), fontsize=9.5, fontweight="bold",
                    color=fk.C.INK, zorder=11, xytext=off.get(s.CID, (9, 6)),
                    textcoords="offset points",
                    path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])

    handles = [
        Line2D([], [], marker="s", ls="none", mfc=fk.C.OUTFALL, mec="white",
               ms=8, label="A  existing works"),
        Line2D([], [], marker="o", ls="none", mfc=fk.C.MAIN, mec="white", ms=8,
               label="B–E  proposed sites already in the project data"),
        Line2D([], [], marker="^", ls="none", mfc=fk.C.GREY, mec="white", ms=8,
               label="W10-S1  best cell of W10's suitability surface"),
        Line2D([], [], color=fk.C.FAIL, lw=1.1, ls="-",
               label="300 m — bottom of the G201-p43 large-STP band"),
        Line2D([], [], color=fk.C.STATION, lw=1.0, ls=":",
               label="1,000 m — top of that band"),
        Line2D([], [], marker="X", ls="none", mfc=fk.C.FLAG, mec=fk.C.INK, ms=9,
               label="load centroid (Q-weighted, central sets)"),
        Line2D([], [], **fk.tier_style("trunk main"), label="W11a trunk, 85.5 km"),
        Patch(facecolor="#8c7a63", edgecolor="none",
              label=f"odour receptor — built plot ({meta['n_receptors']:,})"),
        Patch(facecolor="#a8c79a", edgecolor="none", label="agricultural plot (TE reuse)"),
        Line2D([], [], color=fk.C.BOUNDARY, lw=1.2, ls="--", label="study boundary"),
        fk.untested_handle("UNTESTED — no 50-year hazard answer"),
    ]
    box = ("site   GL m  dwell m  free ha  grav %\n" + "\n".join(
        f"{s.CID:<7}{s.GL_M:>5.1f}{s.D_RECEPT_M:>9,.0f}{s.FREE600_HA:>9.1f}"
        f"{s.GRAV_PC:>8.1f}" for _, s in cand.iterrows()))
    fk.finish_map(fig, ax, legend_handles=handles, legend_loc="upper left",
                  databox=box, note=note,
                  source=fk.source_line(
                      meta["trunk"],
                      "Hydraulic/SHP/IBRI STP/IBRI STP.shp + SHP/Proposed STP",
                      "W3/shp/MoH_Plots_class_v4.shp, 61,272 plots",
                      "Data/04 Lekhuwair/Hazard_T50y.tif, nodata -9999.0"))
    return fk.save(fig, stem)


def plt_circle(ax, x, y, r, color, ls=":"):
    import matplotlib.patches as mp
    c = mp.Circle((x, y), r, facecolor="none", edgecolor=color, lw=1.0, ls=ls,
                  zorder=8)
    ax.add_patch(c)
    return c


def fig_gravity(cand, meta, stem="F21_stp_gravity_reach"):
    """The gravity answer: how much load reaches each candidate, and with what margin."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    west = cand[cand.GRAV_PC >= 95]
    fig, axes = fk.chart_frame(
        title=(f"{len(west)} of the {len(cand)} candidates take essentially the whole "
               f"load by gravity; the two north-eastern sites take under 16 %"),
        subtitle=(f"Load = the ultimate Q published in W11a.gpkg [servicing], central-STP "
                  f"sets only, {meta['q_central']:,.0f} m3/d, spread over the built and "
                  f"planned plots that carry it. A load centre reaches a works when its "
                  f"collector invert (2.0 m below ground, PROJECT ASSUMPTION) laid at the "
                  f"G203-p29 Table 11 minimum gradient for DN900 and above (0.75 mm/m) "
                  f"still clears a works inlet 6.0 m below site ground (PROJECT "
                  f"ASSUMPTION). Path = straight line x {meta['sinuosity']:.3f}, MEASURED "
                  f"on the 85.5 km W11a trunk."),
        figsize=(11.4, 6.6), nrows=1, ncols=2, ygrid=False, xgrid=True)
    a0, a1 = axes
    fig.subplots_adjust(wspace=0.32, top=fig.subplotpars.top - 0.035)

    d = cand.sort_values("GRAV_PC")
    y = np.arange(len(d))
    for i, (_, s) in enumerate(d.iterrows()):
        role = "pass" if s.GRAV_PC >= 95 else ("flag" if s.GRAV_PC >= 50 else "fail")
        a0.barh(y[i], s.GRAV_PC, height=0.62, **fk.status_style(role))
        a0.text(s.GRAV_PC + 2.0, y[i], f"{s.GRAV_PC:.1f} %  {s.Q_GRAV_M3D:,.0f} m³/d",
                ha="left", va="center", fontsize=7.4, fontweight="bold", color=fk.C.INK)
    a0.set_yticks(y)
    a0.set_yticklabels([f"{s.CID}  {s.NAME}" for _, s in d.iterrows()], fontsize=7.4)
    a0.set_xlim(0, 168)
    a0.set_xticks([0, 20, 40, 60, 80, 100])
    a0.set_xlabel("share of the ultimate central load arriving by gravity, %")
    a0.text(0.0, 1.03, "How much of the load arrives by gravity", fontsize=9,
            transform=a0.transAxes, color=fk.C.GREY)
    a0.legend(handles=[
        Patch(label="≥ 95 % — central-works candidate", **fk.status_style("pass")),
        Patch(label="50–95 %", **fk.status_style("flag")),
        Patch(label="< 50 % — satellite catchment", **fk.status_style("fail"))],
        loc="upper right", bbox_to_anchor=(1.0, 0.62), fontsize=6.8, framealpha=0.95,
        edgecolor="#9a9a9a", handlelength=1.4)

    # right panel: load-weighted distribution of SPARE HEAD.  A 100 % site with 1 m of
    # margin everywhere is not the same site as a 100 % site with 15 m.
    qz = meta["q_cells"]
    order = ["A", "B", "C", "D", "E", "W10-S1"]
    ramp = [fk.C.TRUNK, fk.C.SUBMAIN, fk.C.MAIN, fk.C.LATERAL, fk.C.RIDER, fk.C.GREY]
    styles = ["-", "-", "-", "--", "--", ":"]
    for cid, col, ls in zip(order, ramp, styles):
        if cid not in meta["spare"]:
            continue
        sp = meta["spare"][cid]
        o = np.argsort(sp)
        cum = 100.0 * np.cumsum(qz[o]) / qz.sum()
        a1.plot(sp[o], cum, color=col, lw=1.8, ls=ls, label=cid, zorder=5)
    a1.axvline(0.0, color=fk.C.FAIL, lw=1.2, zorder=4)
    a1.annotate("must be pumped", xy=(-2, 52), fontsize=7.0, color=fk.C.FAIL,
                ha="right", va="center", rotation=90)
    a1.set_xlim(-120, 60)
    a1.set_ylim(0, 100)
    a1.set_xlabel("spare head at the works inlet, m  (negative = must be pumped)")
    a1.set_ylabel("share of the ultimate central load, %")
    a1.text(0.0, 1.03, "…and with how much margin", fontsize=9,
            transform=a1.transAxes, color=fk.C.GREY)
    a1.legend(frameon=False, fontsize=7.6, loc="upper left", ncol=2, title="site",
              title_fontsize=7.4)
    fk.style_axes(a1, xgrid=True, ygrid=True)

    fk.finish_chart(fig, source=fk.source_line(
        meta["servicing"], meta["trunk_nodes"],
        "W3/shp/MoH_Plots_class_v4.shp",
        "Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt, 0.5 m"),
        note=("HEAD SCREEN, NOT A DESIGN: it does not test the 12 m cover cap along the "
              "route, which is what put 3 lifting stations on the trunk that already "
              "reaches site A. A site can pass this test and still need pumping."))
    return fk.save(fig, stem)


# =============================================================================== main

def main(cache=True):
    """``--cache`` reuses the last measurement so a figure can be redrawn in seconds.

    The cache lives in the figkit scratchpad, outside the repo, and is only ever a
    convenience for redrawing: `measure()` is the authority and a fresh run re-reads
    every artefact.
    """
    import pickle
    cf = Path(fk.SCRATCH) / "stp_options_meta.pkl"
    if cache and "--cache" in sys.argv and cf.exists():
        cand, meta = pickle.loads(cf.read_bytes())
        print(f"[reused measurement cache {cf}]")
    else:
        cand, meta = measure()
        try:
            cf.write_bytes(pickle.dumps((cand, meta)))
        except Exception as exc:                       # noqa: BLE001
            print("cache not written:", exc)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 60)
    print("\n================ CANDIDATES ================")
    cols = ["CID", "NAME", "X", "Y", "GL_M", "IN_BOUND", "D_RECEPT_M", "D_BUILT_M",
            "D_PLANRES_M", "FREE600_HA", "FREE800_HA", "D_WADI_M", "HAZ_CLASS",
            "UNTEST1K_PC", "GRAV_PC", "GRAV_PC_D9", "Q_GRAV_M3D", "HAUL_KM",
            "CONV_KM", "D_LOADC_KM", "EXT_KM", "SURPLUS_M", "COV_AT_SITE_M", "EXT_OK",
            "D_TRUNK_M", "D_AGRI_M", "AGRI5K_HA", "D_TE_M", "D_ROAD_M", "D_DUAL_M",
            "D_EXIST_KM", "D_PS_KM"]
    cols = [c for c in cols if c in cand.columns]
    print(cand[cols].to_string(index=False))
    print("\n================ LAND REQUIREMENT, G203-p64 Table 28 ================")
    print(f"design flow = central Q {meta['q_central']:,.0f} x 1.10 (G203-p65 T29) = "
          f"{meta['q_design']:,.0f} m3/d")
    print(land_requirement(meta["q_design"]).to_string(index=False))
    print("\nfigures:")
    print(" ", fig_site_options(cand, meta))
    print(" ", fig_gravity(cand, meta))
    out = Path(fk.SCRATCH) / "stp_options_measurements.csv"
    cand.to_csv(out, index=False)
    print("\nmeasurements ->", out)
    return cand, meta


if __name__ == "__main__":
    main()
