"""forcemains — the force-main (rising main) route study for W11a.

Draws the four figures behind `W11a/docs/FORCE_MAIN_ROUTES.md` and prints every
number they carry, so the document and the figures cannot drift apart.

    python W11a/report/forcemains.py            # measure, print, draw
    python W11a/report/forcemains.py --numbers  # measure and print only

WHAT THIS MODULE MAY AND MAY NOT DO
-----------------------------------
It reads.  It never writes into `W11a/shp` or `W11a/run` — figkit takes the copies.
Every figure number comes from one of:

  * `W11a/shp/W11a_trunk.gpkg`      (stage 3, the published trunk: nodes, reaches)
  * `W11a/shp/W11a_trunk_pumped.shp` (stage 3, the drawn rising-main routes)
  * `W11a/run/s3_trunk_stations.csv` (stage 3, the three stations)
  * `Data/Received/.../FORCELINE_IBRI.shp` (NAMA asset GIS — the built 2006 main)
  * `Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt` (the designated 0.5 m terrain)
  * `Data/04 Lekhuwair/Hazard_T50y.tif` (the 50-year hazard grid, nodata -9999.0)

GUIDELINE VALUES ARE QUOTED, NOT REMEMBERED.  Each constant below carries the page
it was read from.  Where a value is OURS rather than the guideline's, the name says
so and the figure labels it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figkit as fk                                          # noqa: E402
from matplotlib.lines import Line2D                          # noqa: E402
from matplotlib.patches import Patch                         # noqa: E402

# --------------------------------------------------------------- guideline values
# PAM-GUD-203 section 8, "Force Mains", pages 50-55.  Read from the source 2026-09-02.
V_MAX_RISING = 2.5      # G203-p50 8.1 "The maximum allowable velocity (worst case
                        # scenario) in the pipe shall be not greater than 2.5 m/s"
V_MIN_RISING = 0.75     # G203-p50 8.1 "At design minimum flow ... a velocity of at
                        # least 0.75 m/s shall be maintained for raw sewage"
V_MIN_INTERMITTENT = 1.0   # G203-p50 8.1, intermittent flow
V_MAX_GRAVITY = 3.0     # G203-p27 4.2.2.2 - the GRAVITY maximum.  NOT the rising-main
                        # cap.  Carrying 3.0 onto a pressure main is a known defect here.
RETENTION_IDEAL_MIN = 30.0   # G203-p50 8.2.1 "short enough to produce a retention
                             # period no longer than half an hour"
GRAD_MIN_RISING = 1/500.     # G203-p50 8.2.1, rising; 1:300 falling; never below 1:750
COVER_MIN_M = 1.30           # G203-p52 8.2.4 / p33 4.6.3, without protection
COVER_PROTECTED_M = 0.50     # G203-p52 8.2.4, with protection
COVER_WADI_M = 1.50          # G203-p52 8.2.4 "At Wadi crossing: 1.5 m (depth to crown)"
COVER_WADI_SOFT_M = 2.00     # G201-p86 "Wadi crossings in soft soil ... minimum cover
                             # of 2 meters"
DI_EITHER_SIDE_M = 15.0      # G201-p86 "Ductile Iron pipes and fittings ... over the
                             # length of wadi crossings plus 15 m on either side"
ACCESS_EVERY_M = 500.0       # G203-p50 "Provision shall be included to access pipe
                             # every 500 m"
ISO_TARGET_M, ISO_MAX_M = 500.0, 800.0   # G203-p54 8.4.3
SEP_WATER_MAIN_M = 3.0       # G203-p51 8.2.2, horizontal, force main to water main
CLEAR_VERT_MM = 450          # G203-p51 8.2.2, force main crosses UNDER the water main
STATION_FREEBOARD_M = 0.30   # G203-p38 7.2, floors 300 mm above the 1:50 year flood
WELL_STARTS_PER_H = 10.0     # G203-p48 7.8, minimum for motors up to 30 kW
TYPE_BANDS = ((100.0, 1), (300.0, 2))    # G203-p40, Type 1 <=100 L/s, 2 <=300, 3 >300
DUTY_PUMPS = {1: 1, 2: 2, 3: 3}          # G203-p40 Table 17, minimum duty pumps
HW_C_DI_20YR = 120.0    # G202-p104 Table 21, ductile iron at 20 years
HW_C_DI_NEW = 140.0     # G202-p104 Table 21, ductile iron at t = 0
HW_C_HDPE = 150.0       # G202-p104 Table 21, HDPE, all ages

# ------------------------------------------------------------- project assumptions
# These are OURS.  Every figure that uses one says so on its face.
PROJ_WADI_CLASSES = (4, 5, 6)   # figkit default; AR&R hazard classes standing in for
                                # G203-p30 4.4.1's "areas subject to washout"
PROJ_OFFROAD_M = 25.0           # further than this from any mapped road centreline is
                                # read as "cross-country" (G203-p51 wants the ROW)
PROJ_PUMP_EFF = 0.75            # wire-to-water, screening only
PROJ_SMOOTH_M = 50.0            # metres of rolling mean before summits are counted
PROJ_PROMINENCE_M = 0.30        # a summit smaller than this is ground noise, not an
                                # air-valve location.  OURS: G203-p53 8.4.1 says
                                # "air valves are required at high points" and "the
                                # number of air valves shall be kept to a minimum",
                                # and gives no threshold, so we declare one.

DEM = fk.BASE / "Data" / "Terrain" / "Sat_0p5m" / "IBRI_0p5_VRT2.vrt"
FORCELINE = (fk.BASE / "Data" / "Received" / "09-RECEIVED" / "NAMA" / "IBRI" / "WW"
             / "SHIP" / "FORCELINE_IBRI.shp")
ROADS = fk.HYD / "SHP" / "Road centerline 2" / "Road_Centercline.shp"

DN_SERIES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800,
             900, 1000, 1200, 1400)

# The 2006 station and the works, both user-confirmed and recorded in CLAUDE.md.
EX_PS = (449899.59, 2567301.72)
WORKS = (444422.8, 2563337.9)


# ------------------------------------------------------------------------ helpers

def _sample(path, pts):
    """Raster values at pts, with the finite-nodata trap handled once."""
    import rasterio
    with rasterio.open(path) as src:
        v = np.array([x[0] for x in src.sample(pts)], dtype="float64")
        nod = src.nodata
    bad = ~np.isfinite(v)
    if nod is not None:
        bad |= (v == nod)
    bad |= (v <= -9998.0)
    v[bad] = np.nan
    return v


def _chainage(geom, step):
    n = max(2, int(np.ceil(geom.length / step)) + 1)
    ch = np.linspace(0.0, geom.length, n)
    return ch, [(geom.interpolate(c).x, geom.interpolate(c).y) for c in ch]


def _turning_points(z, step, smooth_m=PROJ_SMOOTH_M, prom=PROJ_PROMINENCE_M):
    """Prominent summits and lows on a smoothed profile -> air valves and washouts.

    A raw DEM profile has a turning point every few metres; counting those would
    put an air valve every 50 m.  The profile is smoothed over ``smooth_m`` and only
    turning points with at least ``prom`` metres of prominence are kept.  Both
    numbers are OURS and declared in the constants above.
    """
    from scipy.signal import find_peaks
    win = max(3, int(round(smooth_m / max(step, 1e-6))))
    zs = pd.Series(z).rolling(win, center=True, min_periods=1).mean().to_numpy()
    hi, _ = find_peaks(zs, prominence=prom)
    lo, _ = find_peaks(-zs, prominence=prom)
    return list(hi), list(lo), zs


def _runs(mask, ch, step):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            out.append((ch[i], ch[j], ch[j] - ch[i] + step))
            i = j + 1
        else:
            i += 1
    return out


def hazen_williams_hf(L_m, Q_m3s, D_m, C):
    """Head loss, m.  G202-p104 7.1.3.2 names Hazen-Williams for smaller diameters."""
    return 10.67 * L_m * Q_m3s ** 1.852 / (C ** 1.852 * D_m ** 4.87)


def station_type(q_pk_ls):
    """G203-p40: Type 1 up to 100 L/s, Type 2 to 300 L/s, Type 3 above."""
    for cap, t in TYPE_BANDS:
        if q_pk_ls <= cap:
            return t
    return 3


def size_window(q_pk_ls, n_duty):
    """Internal-diameter window, mm, from G203-p50 8.1 alone.

    The main must pass every duty pump at once without exceeding 2.5 m/s, and must
    still make 0.75 m/s with ONE pump running (the design-minimum-flow case the
    clause names).  With n duty pumps the two bounds are a factor n apart, so
    2.5 / 0.75 = 3.33 caps a single main at THREE duty pumps.  ASSUMPTION, ours:
    the duty point is taken to scale linearly with the number of pumps running,
    which a system curve will not do exactly - a screening window, not a selection.
    """
    Q = q_pk_ls / 1000.0
    d_lo = np.sqrt(4 * Q / (np.pi * V_MAX_RISING))
    d_hi = np.sqrt(4 * Q / (np.pi * n_duty * V_MIN_RISING))
    return d_lo * 1000.0, d_hi * 1000.0


def wet_well_m3(q_one_pump_ls, starts_per_h=WELL_STARTS_PER_H):
    """G203-p48 7.8: V = 0.25 Q T, T = 3600 / starts per hour."""
    return 0.25 * (q_one_pump_ls / 1000.0) * (3600.0 / starts_per_h)


# ------------------------------------------------------------------------- reading

def works_leg(nodes, reaches, start="N0000699", stop="N0000758"):
    """The published trunk reaches from the junction near the 2006 station to the works."""
    by_us = {r.US_NODE: i for i, r in reaches.iterrows()}
    seq, cur = [], start
    while cur != stop and cur in by_us:
        seq.append(by_us[cur])
        cur = reaches.at[by_us[cur], "DS_NODE"]
    return reaches.loc[seq].reset_index(drop=True)


def alignment_report(name, geom, step=10.0):
    """Everything a route comparison needs, measured off the raster and the roads."""
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.ops import unary_union

    ch, pts = _chainage(geom, step)
    z = _sample(DEM, pts)
    h = _sample(fk.HAZARD, pts)
    known = np.isfinite(h)
    wadi = known & (np.floor(h) >= min(PROJ_WADI_CLASSES))

    rd = gpd.read_file(ROADS, engine="pyogrio").set_crs(fk.EPSG, allow_override=True)
    dual = unary_union(rd[rd["dual"] == 1].geometry.values)
    every = unary_union(rd.geometry.values)
    d_dual = np.array([dual.distance(Point(p)) for p in pts])
    d_road = np.array([every.distance(Point(p)) for p in pts])

    hi, lo, _ = _turning_points(z, step)
    wruns = _runs(wadi, ch, step)
    return dict(
        name=name, geom=geom, ch=ch, z=z, h=h,
        len_m=float(geom.length),
        z_start=float(z[0]), z_end=float(z[-1]),
        net_fall_m=float(z[0] - z[-1]),
        summit_above_start_m=float(np.nanmax(z) - z[0]),
        cum_rise_m=float(np.nansum(np.diff(z)[np.diff(z) > 0])),
        tested_pct=float(100 * known.mean()),
        untested_pct=float(100 * (~known).mean()),
        wadi_m=float(wadi.sum() * step), wadi_runs=len(wruns),
        wadi_longest_m=float(max((r[2] for r in wruns), default=0.0)),
        wadi_runs_detail=[(int(a), int(b), int(c)) for a, b, c in wruns],
        wadi_in_first_km_m=float(wadi[ch <= 1000.0].sum() * step),
        dual_min_m=float(d_dual.min()), dual_within6_m=float((d_dual < 6).sum() * step),
        offroad_pct=float(100 * (d_road > PROJ_OFFROAD_M).mean()),
        road_median_m=float(np.median(d_road)),
        summits=len(hi), lows=len(lo),
        access_pts=int(np.ceil(geom.length / ACCESS_EVERY_M)),
        iso_min=int(np.ceil(geom.length / ISO_MAX_M)),
        iso_max=int(np.ceil(geom.length / ISO_TARGET_M)),
    )


# ------------------------------------------------------------------- the study

def measure():
    """Every number in the document and the figures, in one dict."""
    import geopandas as gpd
    from shapely.geometry import LineString
    from shapely.ops import linemerge

    out = {}
    nodes = fk.read_layer("W11a_trunk.gpkg", "nodes")
    reaches = fk.read_layer("W11a_trunk.gpkg", "reaches")
    pumped = fk.read_layer("W11a_trunk_pumped.shp")
    stations = fk.read_csv("s3_trunk_stations.csv")
    built_all = fk.read_layer(str(FORCELINE))
    out["src"] = dict(nodes=nodes, reaches=reaches, pumped=pumped,
                      stations=stations, built=built_all)

    # ---- what force mains the design actually has -------------------------------
    roots = nodes[(nodes.DS_NODE.isna()) | (nodes.DS_NODE == "")]
    out["roots"] = roots[["NODE_UID", "NODE_KIND", "X", "Y", "GRD_M", "INV_M",
                          "DEPTH_M", "Q_ADF_M3D", "Q_PK_LS"]].copy()
    outf = roots[roots.NODE_KIND == "outfall"].iloc[0]
    out["outfall"] = dict(x=float(outf.X), y=float(outf.Y), grd=float(outf.GRD_M),
                          inv=float(outf.INV_M), depth=float(outf.DEPTH_M),
                          q_adf=float(outf.Q_ADF_M3D), q_pk=float(outf.Q_PK_LS))

    # ---- the works leg, and how high it could possibly arrive -------------------
    leg = works_leg(nodes, reaches)
    ni = nodes.set_index("NODE_UID")
    grd_us = ni.loc[leg.US_NODE.values, "GRD_M"].to_numpy()
    grd_dn = ni.loc[leg.DS_NODE.values, "GRD_M"].to_numpy()
    od = float(np.median(grd_us - leg.COVER_US.to_numpy() - leg.INV_UP.to_numpy()))
    ch_end = np.cumsum(leg.LEN_M.to_numpy())
    ch_start = ch_end - leg.LEN_M.to_numpy()
    L = float(ch_end[-1])
    s_min = float(leg.SLOPE_MIN.max()) / 100.0     # DN1700 throughout, Table 11
    ceil_node = (grd_dn - COVER_MIN_M - od) - (L - ch_end) * s_min
    ceil_head = (grd_us[0] - COVER_MIN_M - od) - L * s_min
    arrival_ceiling = float(min(ceil_node.min(), ceil_head))
    # independent re-read of the ground, from the raw terrain
    dem_us = _sample(DEM, list(zip(ni.loc[leg.US_NODE.values, "X"].to_numpy(),
                                   ni.loc[leg.US_NODE.values, "Y"].to_numpy())))
    out["leg"] = dict(
        gdf=leg, ch_start=ch_start, ch_end=ch_end, grd_us=grd_us, grd_dn=grd_dn,
        od_m=od, len_m=L, s_min=s_min,
        n_reach=len(leg), dn=sorted(set(leg.DN.tolist())),
        inv_us0=float(leg.INV_UP.iloc[0]), inv_dn1=float(leg.INV_DN.iloc[-1]),
        grd0=float(grd_us[0]), grd1=float(grd_dn[-1]),
        fall_inv=float(leg.INV_UP.iloc[0] - leg.INV_DN.iloc[-1]),
        fall_grd=float(grd_us[0] - grd_dn[-1]),
        slope_pct=float(100 * (leg.INV_UP.iloc[0] - leg.INV_DN.iloc[-1]) / L),
        cover_min=float(min(leg.COVER_US.min(), leg.COVER_DN.min())),
        cover_max=float(max(leg.COVER_US.max(), leg.COVER_DN.max())),
        cover_mean=float(pd.concat([leg.COVER_US, leg.COVER_DN]).mean()),
        on_wadi_m=float(leg.ON_WADI_M.sum()), on_dual_m=float(leg.ON_DUAL_M.sum()),
        ret_min=float(leg.RET_MIN.sum()), v_lo=float(leg.V_PK_MS.min()),
        v_hi=float(leg.V_PK_MS.max()),
        arrival_ceiling=arrival_ceiling,
        headroom=float(arrival_ceiling - leg.INV_DN.iloc[-1]),
        binding_ch=float(ch_end[int(np.argmin(ceil_node))]),
        ground_check_max_abs=float(np.nanmax(np.abs(dem_us - grd_us))),
    )

    # ---- the three alignments PS -> works ---------------------------------------
    built = built_all[built_all.STATUS == "Ex"].geometry.iloc[0]
    legline = linemerge(list(leg.geometry))
    if legline.geom_type != "LineString":
        legline = max(legline.geoms, key=lambda g: g.length)
    # A and B do NOT share an upstream endpoint: B starts at the trunk junction the
    # client's Main Pipe alignment defines, not at the 2006 station.  Comparing the
    # raw lengths would flatter B by exactly that offset, so A is trimmed to its own
    # closest approach to the junction and BOTH numbers are published.
    from shapely.geometry import Point as _P
    from shapely.ops import substring
    j = _P(legline.coords[0])
    j_off = float(built.distance(j))
    j_ch = float(built.project(j))
    built_trim = substring(built, j_ch, built.length)
    straight = LineString([built.coords[0], built.coords[-1]])
    out["align"] = [
        alignment_report("A  built 2006 rising main", built, 10.0),
        alignment_report("B  W11a trunk corridor", legline, 10.0),
        alignment_report("C  straight line (no legal corridor)", straight, 10.0),
    ]
    out["align_trim"] = alignment_report("A' built main, trimmed to B's start",
                                         built_trim, 10.0)
    out["junction_offset"] = dict(
        dist_junction_to_A_m=j_off, chainage_on_A_m=j_ch,
        dist_junction_to_PS_m=float(_P(legline.coords[0]).distance(_P(*EX_PS))),
        A_trimmed_len_m=float(built_trim.length),
        B_len_m=float(legline.length),
        B_minus_A_trimmed_m=float(legline.length - built_trim.length))
    out["built_row"] = built_all[built_all.STATUS == "Ex"].iloc[0]

    # ---- the three drawn rising mains -------------------------------------------
    groups = {"FM-1": [0, 1, 2, 3], "FM-2": [4], "FM-3": [5, 6, 7]}
    fms = []
    for i, (nm, idx) in enumerate(groups.items()):
        g = linemerge([pumped.geometry.iloc[k] for k in idx])
        if g.geom_type != "LineString":
            g = max(g.geoms, key=lambda z: z.length)
        rep = alignment_report(nm, g, 2.0)
        s = stations.iloc[i]
        q_pk, q_adf = float(s.q_pk_ls), float(s.q_adf_m3d)
        t = station_type(q_pk)
        nd = DUTY_PUMPS[t]
        lo, hi = size_window(q_pk, nd)
        inside = [d for d in DN_SERIES if lo <= d <= hi]
        # SCREENING PICK, ours: the LARGEST standard diameter inside the window.
        # It minimises friction and therefore pump duty, and on mains this short the
        # retention stays far inside the half-hour ideal at either end of the window.
        # G203-p50 requires a whole-life cost comparison before this is a selection.
        pick = inside[-1] if inside else None
        rep.update(station_node=str(s.node), st_x=float(s.x), st_y=float(s.y),
                   grd=float(s.grd_m), inv=float(s.inv_m), cover=float(s.cover_m),
                   why=str(s.why), static_lift=float(s.static_lift_m),
                   rm_len=float(s.rm_len_m), q_pk_ls=q_pk, q_adf=q_adf,
                   n_prop=float(s.n_prop), st_type=t, n_duty=nd,
                   d_lo_mm=lo, d_hi_mm=hi, DN=pick, dn_window=inside)
        if pick:
            A = np.pi / 4 * (pick / 1000.0) ** 2
            rep["v_all"] = q_pk / 1000.0 / A / nd * nd
            rep["v_one"] = q_pk / 1000.0 / nd / A
            rep["ret_all_min"] = rep["rm_len"] / rep["v_all"] / 60.0
            rep["ret_one_min"] = rep["rm_len"] / rep["v_one"] / 60.0
            rep["hf_all_m"] = hazen_williams_hf(rep["rm_len"], q_pk / 1000.0,
                                                pick / 1000.0, HW_C_DI_20YR)
            rep["tot_head_m"] = rep["static_lift"] + rep["hf_all_m"]
            rep["well_m3"] = wet_well_m3(q_pk / nd)
            rep["kw"] = (1000 * 9.81 * (q_pk / 1000.0) * rep["tot_head_m"]
                         / PROJ_PUMP_EFF / 1000.0)
        # hazard at the station itself - G203-p38 7.2 needs the 1:50 level here
        rep["haz_at_station"] = float(_sample(fk.HAZARD, [(rep["st_x"], rep["st_y"])])[0])
        fms.append(rep)
    out["fms"] = fms

    # ---- the conditional terminal main at the works ------------------------------
    q_pk = out["outfall"]["q_pk"]
    t = station_type(q_pk)
    nd = DUTY_PUMPS[t]
    lo, hi = size_window(q_pk, nd)
    out["terminal"] = dict(q_pk_ls=q_pk, q_adf=out["outfall"]["q_adf"], st_type=t,
                           n_duty=nd, d_lo_mm=lo, d_hi_mm=hi,
                           standard_in_window=[d for d in DN_SERIES if lo <= d <= hi],
                           well_m3=wet_well_m3(q_pk / nd))

    # ---- the pumped alternative to the whole 9 km works leg ----------------------
    Q = q_pk / 1000.0
    rows = []
    for D in (600, 700, 800, 850, 900, 1000, 1100, 1200, 1400):
        A = np.pi / 4 * (D / 1000.0) ** 2
        v = Q / A
        hf = hazen_williams_hf(L, Q, D / 1000.0, HW_C_DI_20YR)
        head = hf - out["leg"]["fall_grd"]            # static is NEGATIVE downhill
        rows.append(dict(DN=D, v_ms=v, hf_m=hf, head_m=head,
                         kw=1000 * 9.81 * Q * max(head, 0.0) / PROJ_PUMP_EFF / 1000.0,
                         v_one_ms=v / nd,
                         ok_vmax=v <= V_MAX_RISING, ok_vmin=v / nd >= V_MIN_RISING))
    out["pumped_alt"] = pd.DataFrame(rows)
    return out


# ------------------------------------------------------------------------ figures

def fig_route_map(M):
    from shapely.geometry import Point
    import geopandas as gpd

    A, B, C = M["align"]
    geoms = gpd.GeoSeries([A["geom"], B["geom"], C["geom"]], crs=fk.CRS)
    ext = fk.extent_of(geoms.total_bounds, pad=0.10)
    known, _wadi, rext = fk.hazard_coverage(ext, wadi_classes=PROJ_WADI_CLASSES)

    J = M["junction_offset"]
    At = M["align_trim"]
    fig, ax, note = fk.map_frame(
        ext,
        title=(f"The corridor already settles the route — A and B differ by "
               f"{abs(J['B_minus_A_trimmed_m']):.0f} m. What is open is gravity or "
               f"pumping"),
        subtitle=(f"Three alignments to the works. B is the W11a trunk corridor, "
                  f"carried here as a force-main route for comparison; the design uses "
                  f"it as a DN{M['leg']['dn'][0]} gravity main. B starts at the trunk "
                  f"junction, {J['dist_junction_to_PS_m']:.0f} m from the 2006 station, "
                  f"so the like-for-like pair is B {B['len_m']/1000:.2f} km against A' "
                  f"= A trimmed to that start, {At['len_m']/1000:.2f} km. On that pair "
                  f"B is flatter ({B['cum_rise_m']:.1f} m of cumulative rise against "
                  f"{At['cum_rise_m']:.1f}) and clear of the dual carriageway A runs "
                  f"within {At['dual_min_m']:.2f} m of. Wadi contact is scored on "
                  f"hazard classes {PROJ_WADI_CLASSES}, a PROJECT ASSUMPTION standing "
                  f"in for G203-p30 4.4.1's \"areas subject to washout\", not a "
                  f"guideline threshold — and {B['untested_pct']:.0f} % of B has no "
                  f"answer at all."))
    fk.hatch_untested(ax, ~known, rext)
    try:
        cor = fk.read_layer("W11a.gpkg", "corridors", columns=["LEN_M"],
                            bbox=tuple(ext))
        cor.plot(ax=ax, color=fk.C.FAINT, linewidth=0.25, zorder=3)
    except Exception:                                        # noqa: BLE001
        cor = None
    gpd.GeoSeries([C["geom"]], crs=fk.CRS).plot(ax=ax, color=fk.C.GREY, lw=1.2,
                                                ls=":", zorder=5)
    gpd.GeoSeries([A["geom"]], crs=fk.CRS).plot(ax=ax, color=fk.C.FAIL, lw=2.0,
                                                zorder=6)
    gpd.GeoSeries([B["geom"]], crs=fk.CRS).plot(ax=ax, color=fk.C.TRUNK, lw=2.6,
                                                zorder=7)
    for (x, y), lab, col in ((EX_PS, "2006 pumping station", fk.C.STATION),
                             (WORKS, "existing works / outfall", fk.C.OUTFALL)):
        ax.plot([x], [y], marker="s", ms=8, mfc=col, mec="white", mew=1.2, zorder=9)
        ax.annotate(lab, (x, y), xytext=(9, 9), textcoords="offset points",
                    fontsize=7.4, zorder=9, color=fk.C.INK,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none",
                              alpha=0.82))
    for fmr in M["fms"]:
        if ext[0] <= fmr["st_x"] <= ext[2] and ext[1] <= fmr["st_y"] <= ext[3]:
            ax.plot([fmr["st_x"]], [fmr["st_y"]], marker="^", ms=8,
                    mfc=fk.C.FLAG, mec=fk.C.INK, mew=0.8, zorder=9)
            ax.annotate(f"{fmr['name']}  {fmr['q_pk_ls']:.0f} L/s",
                        (fmr["st_x"], fmr["st_y"]), xytext=(8, -12),
                        textcoords="offset points", fontsize=7.0, zorder=9)

    handles = [
        Line2D([], [], color=fk.C.TRUNK, lw=2.6,
               label=f"B  W11a trunk corridor — {B['len_m']/1000:.2f} km"),
        Line2D([], [], color=fk.C.FAIL, lw=2.0,
               label=(f"A  built 2006 rising main — {A['len_m']/1000:.2f} km "
                      f"({At['len_m']/1000:.2f} km from B's start)")),
        Line2D([], [], color=fk.C.GREY, lw=1.2, ls=":",
               label=f"C  straight line — {C['len_m']/1000:.2f} km (not a corridor)"),
        Line2D([], [], color=fk.C.STATION, marker="s", ls="", ms=7,
               label="pumping station / works"),
        Line2D([], [], color=fk.C.FLAG, marker="^", ls="", ms=7,
               label="W11a trunk lifting station"),
        fk.untested_handle("UNTESTED — outside the 50-year grid"),
    ]
    box = ("alignment            A     A'      B      C\n"
           f"length        km  {A['len_m']/1000:5.2f}  {At['len_m']/1000:5.2f}  "
           f"{B['len_m']/1000:5.2f}  {C['len_m']/1000:5.2f}\n"
           f"wadi contact   m  {A['wadi_m']:5.0f}  {At['wadi_m']:5.0f}  "
           f"{B['wadi_m']:5.0f}  {C['wadi_m']:5.0f}\n"
           f"within 6 m of dual{A['dual_within6_m']:5.0f}  {At['dual_within6_m']:5.0f}  "
           f"{B['dual_within6_m']:5.0f}  {C['dual_within6_m']:5.0f}\n"
           f"cross-country  %  {A['offroad_pct']:5.0f}  {At['offroad_pct']:5.0f}  "
           f"{B['offroad_pct']:5.0f}  {C['offroad_pct']:5.0f}\n"
           f"summits (air v.)  {A['summits']:5d}  {At['summits']:5d}  "
           f"{B['summits']:5d}  {C['summits']:5d}\n"
           f"lows (washouts)   {A['lows']:5d}  {At['lows']:5d}  {B['lows']:5d}  "
           f"{C['lows']:5d}\n"
           f"cumulative rise m {A['cum_rise_m']:5.1f}  {At['cum_rise_m']:5.1f}  "
           f"{B['cum_rise_m']:5.1f}  {C['cum_rise_m']:5.1f}\n"
           f"no hazard answer %{A['untested_pct']:5.0f}  {At['untested_pct']:5.0f}  "
           f"{B['untested_pct']:5.0f}  {C['untested_pct']:5.0f}\n"
           "A' = A trimmed to B's upstream start")
    src = [M["src"]["built"], M["src"]["reaches"],
           f"{DEM.relative_to(fk.BASE).as_posix()}, 0.5 m terrain",
           f"{fk.HAZARD.relative_to(fk.BASE).as_posix()}, 50-year grid, nodata -9999.0",
           f"{ROADS.relative_to(fk.HYD).as_posix()}, dual column"]
    fk.finish_map(fig, ax, legend_handles=handles, databox=box, note=note,
                  legend_loc="lower left", source=fk.source_line(*src))
    return fk.save(fig, "FM01_force_main_route_options")


def fig_long_section(M):
    leg = M["leg"]
    g = leg["gdf"]
    ch = np.concatenate([[0.0], leg["ch_end"]])
    grd = np.concatenate([[leg["grd_us"][0]], leg["grd_dn"]])
    inv = np.concatenate([[g.INV_UP.iloc[0]], g.INV_DN.to_numpy()])
    crown = inv + leg["od_m"]
    A = M["align"][0]

    fig, axes = fk.chart_frame(
        title=(f"The works inlet decides whether Ibri pumps: the trunk cannot arrive "
               f"higher than {leg['arrival_ceiling']:.2f} m aOD"),
        subtitle=(f"Long section of the published trunk over its last "
                  f"{leg['len_m']/1000:.2f} km, junction N0000699 to the works. The "
                  f"ceiling is the highest invert the reach could be laid to and still "
                  f"hold {COVER_MIN_M:.2f} m of cover (G203-p33 4.6.3) at every node "
                  f"and the Table 11 minimum gradient of {leg['s_min']*100:.3f} % "
                  f"(G203-p29) below it. Head-room over the laid invert is "
                  f"{leg['headroom']:.2f} m."),
        figsize=(11.0, 6.4), nrows=2, ygrid=True)
    ax, ax2 = axes

    ax.fill_between(ch, crown, grd, color=fk.C.FAINT, alpha=0.55, lw=0,
                    label="cover over the crown", zorder=2)
    ax.plot(ch, grd, color=fk.C.INK, lw=1.4, label="ground (0.5 m terrain)", zorder=4)
    ax.plot(ch, inv, color=fk.C.TRUNK, lw=2.0,
            label=f"trunk invert, DN{leg['dn'][0]} gravity", zorder=5)
    ax.axhline(leg["arrival_ceiling"], color=fk.C.FLAG, lw=1.3, ls="--", zorder=6)
    ax.annotate(f"highest legal arrival invert {leg['arrival_ceiling']:.2f} m aOD",
                (leg["len_m"] * 0.02, leg["arrival_ceiling"]), xytext=(0, 5),
                textcoords="offset points", fontsize=7.4, color=fk.C.FLAG,
                fontweight="bold")
    ax.plot([leg["len_m"]], [leg["inv_dn1"]], marker="o", ms=7, mfc=fk.C.OUTFALL,
            mec="white", zorder=8)
    ax.annotate(f"arrives {leg['inv_dn1']:.2f} m aOD,\n"
                f"{leg['grd1'] - leg['inv_dn1']:.2f} m below ground",
                (leg["len_m"], leg["inv_dn1"]), xytext=(-14, 12),
                textcoords="offset points", ha="right", va="bottom", fontsize=7.4,
                color=fk.C.OUTFALL, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.85))
    # the band a works inlet may NOT sit in without a terminal pumping station
    ytop = float(np.nanmax(grd))
    ax.axhspan(leg["arrival_ceiling"], ytop, xmin=0.86, xmax=1.0,
               facecolor=fk.C.FAIL, alpha=0.13, lw=0, zorder=1)
    ax.annotate("a works inlet anywhere in this band\nneeds a terminal pumping station",
                (leg["len_m"] * 0.985, (leg["arrival_ceiling"] + ytop) / 2),
                ha="right", va="center", fontsize=7.2, color=fk.C.FAIL, zorder=7)
    ax.axvline(leg["binding_ch"], color=fk.C.FLAG, lw=0.9, ls=":", zorder=3)
    ax.annotate("binding node", (leg["binding_ch"], grd.max()), xytext=(4, -10),
                textcoords="offset points", fontsize=6.8, color=fk.C.FLAG)
    ax.set_ylabel("level (m aOD)")
    ax.set_xlim(0, leg["len_m"])
    ax.legend(loc="upper right", fontsize=7.2, framealpha=0.92, ncol=2)
    ax.set_title(f"Gravity, as designed — {leg['n_reach']} reaches, "
                 f"{leg['fall_inv']:.2f} m of invert fall at {leg['slope_pct']:.3f} %, "
                 f"cover {leg['cover_min']:.2f}–{leg['cover_max']:.2f} m",
                 fontsize=8.6, color=fk.C.GREY, loc="left", pad=4)

    # lower panel: the pumped alternative on the same task
    alt = M["pumped_alt"]
    ok = alt[(alt.ok_vmax) & (alt.ok_vmin)]
    pick = ok.iloc[0] if len(ok) else alt.iloc[(alt.v_ms - 2.0).abs().idxmin()]
    hgl_start = leg["grd0"] + float(pick.head_m)
    ax2.plot(A["ch"], A["z"], color=fk.C.GREY, lw=1.1,
             label=f"ground along alignment A ({A['len_m']/1000:.2f} km)", zorder=4)
    ax2.plot([0, leg["len_m"]], [hgl_start, leg["grd1"]], color=fk.C.FAIL, lw=2.0,
             label=(f"hydraulic grade, DN{int(pick.DN)} force main at "
                    f"{M['outfall']['q_pk']:,.0f} L/s"), zorder=5)
    ax2.plot(ch, grd, color=fk.C.INK, lw=1.0, ls="--",
             label="ground along alignment B", zorder=3)
    ax2.annotate(f"{pick.hf_m:.0f} m of friction against {leg['fall_grd']:.0f} m of "
                 f"ground fall\npump head {pick.head_m:.0f} m, "
                 f"{pick.kw:,.0f} kW at the shaft",
                 (leg["len_m"] * 0.30, hgl_start), xytext=(0, -6),
                 textcoords="offset points", fontsize=7.6, color=fk.C.FAIL,
                 fontweight="bold", va="top")
    ax2.set_ylabel("level (m aOD)")
    ax2.set_xlabel("chainage from the junction / 2006 station (m)")
    ax2.set_xlim(0, max(leg["len_m"], A["len_m"]))
    ax2.legend(loc="upper right", fontsize=7.2, framealpha=0.92)
    ax2.set_title("The same task pumped — the alternative if the works inlet cannot "
                  "be set low enough", fontsize=8.6, color=fk.C.GREY, loc="left", pad=4)
    fk.thousands(ax2, "x")
    fk.thousands(ax, "x")

    fk.finish_chart(
        fig, source=fk.source_line(
            M["src"]["reaches"], M["src"]["built"],
            f"{DEM.relative_to(fk.BASE).as_posix()}, 0.5 m terrain"),
        note=(f"Friction by Hazen-Williams, C = {HW_C_DI_20YR:.0f} for ductile iron at "
              f"20 years (G202-p104 Table 21); pump efficiency {PROJ_PUMP_EFF:.2f} "
              f"wire-to-water is OURS, a screening figure. The static head on this "
              f"route is NEGATIVE — the ground falls {leg['fall_grd']:.1f} m — so the "
              f"whole pump head is friction, forced by the "
              f"{V_MIN_RISING:.2f}–{V_MAX_RISING:.1f} m/s window of G203-p50 8.1."))
    return fk.save(fig, "FM02_works_inlet_long_section")


def fig_diameter_window(M):
    alt = M["pumped_alt"]
    term = M["terminal"]
    fig, axes = fk.chart_frame(
        title=("The guideline's own velocity window is what makes pumping this flow "
               "expensive"),
        subtitle=(f"A force main carrying the works flow of {M['outfall']['q_pk']:,.0f} "
                  f"L/s over the {M['leg']['len_m']/1000:.2f} km leg. G203-p50 8.1 "
                  f"caps it at {V_MAX_RISING:.1f} m/s with every duty pump running and "
                  f"holds {V_MIN_RISING:.2f} m/s with one — and G203-p40 Table 17 puts "
                  f"a Type {term['st_type']} station on {term['n_duty']} duty pumps. "
                  f"Those three clauses together admit only "
                  f"{term['d_lo_mm']:.0f}–{term['d_hi_mm']:.0f} mm."),
        figsize=(10.4, 4.6), ncols=2, ygrid=True)
    axL, axR = axes

    axL.axvspan(term["d_lo_mm"], term["d_hi_mm"], color=fk.C.PASS, alpha=0.45,
                lw=0, zorder=1, label="admissible window")
    axL.plot(alt.DN, alt.v_ms, color=fk.C.TRUNK, lw=1.8, marker="o", ms=4,
             label="velocity, all duty pumps", zorder=4)
    axL.plot(alt.DN, alt.v_one_ms, color=fk.C.MAIN, lw=1.5, marker="s", ms=3.6,
             ls="--", label="velocity, one duty pump", zorder=4)
    axL.axhline(V_MAX_RISING, color=fk.C.FAIL, lw=1.2, ls="--", zorder=5)
    axL.axhline(V_MIN_RISING, color=fk.C.FAIL, lw=1.2, ls="--", zorder=5)
    axL.annotate(f"{V_MAX_RISING:.1f} m/s max — G203-p50 8.1", (alt.DN.max(),
                 V_MAX_RISING), xytext=(-4, 4), textcoords="offset points",
                 ha="right", fontsize=7.0, color=fk.C.FAIL)
    axL.annotate(f"{V_MIN_RISING:.2f} m/s min at design minimum flow — G203-p50 8.1",
                 (alt.DN.max(), V_MIN_RISING), xytext=(-4, -12),
                 textcoords="offset points", ha="right", fontsize=7.0, color=fk.C.FAIL)
    axL.axhline(V_MAX_GRAVITY, color=fk.C.GREY, lw=1.0, ls=":", zorder=3)
    axL.annotate(f"{V_MAX_GRAVITY:.1f} m/s is the GRAVITY maximum, G203-p27 4.2.2.2 — "
                 "not this pipe", (alt.DN.min(), V_MAX_GRAVITY), xytext=(4, 3),
                 textcoords="offset points", fontsize=6.8, color=fk.C.GREY)
    axL.set_xlabel("nominal diameter (mm)")
    axL.set_ylabel("velocity (m/s)")
    axL.legend(loc="upper right", fontsize=7.0)

    axR.axvspan(term["d_lo_mm"], term["d_hi_mm"], color=fk.C.PASS, alpha=0.45, lw=0,
                zorder=1)
    axR.plot(alt.DN, alt.head_m, color=fk.C.FAIL, lw=1.8, marker="o", ms=4,
             label="pump head required (m)", zorder=4)
    ax2 = axR.twinx()
    ax2.plot(alt.DN, alt.kw, color=fk.C.FLAG, lw=1.5, marker="^", ms=4, ls="--",
             label="shaft power (kW)", zorder=4)
    ax2.set_ylabel("shaft power (kW)", color=fk.C.FLAG)
    ax2.tick_params(axis="y", colors=fk.C.FLAG)
    axR.axhline(0.0, color=fk.C.GREY, lw=0.9)
    neg = alt[alt.head_m < 0]
    if len(neg):
        axR.axvspan(float(neg.DN.min()), float(alt.DN.max()), color=fk.C.FAIL,
                    alpha=0.09, lw=0, zorder=0)
        axR.annotate(f"at DN{int(neg.DN.min())} and above the head goes negative:\n"
                     "the main would drain and could not be kept full,\n"
                     "which G203-p51 8.2.2 forbids",
                     (float(alt.DN.max()), 0.0), xytext=(-6, 18),
                     textcoords="offset points", ha="right", va="bottom",
                     fontsize=6.9, color=fk.C.FAIL)
    axR.annotate("gravity needs none of this", (alt.DN.min(), 0.0), xytext=(6, 6),
                 textcoords="offset points", ha="left", fontsize=7.4,
                 color=fk.C.TRUNK, fontweight="bold")
    axR.set_xlabel("nominal diameter (mm)")
    axR.set_ylabel("pump head (m)", color=fk.C.FAIL)
    axR.tick_params(axis="y", colors=fk.C.FAIL)
    h1, l1 = axR.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axR.legend(h1 + h2 + [Patch(facecolor=fk.C.PASS, alpha=0.45,
                                label="window admitted by G203")],
               l1 + l2 + ["window admitted by G203"], loc="upper right", fontsize=7.0)

    note = ("No standard diameter falls inside the window"
            if not term["standard_in_window"] else
            "standard diameters in the window: " +
            ", ".join(f"DN{d}" for d in term["standard_in_window"]))
    fk.finish_chart(
        fig, source=fk.source_line(M["src"]["reaches"], M["src"]["nodes"]),
        note=(f"{note}. Head = Hazen-Williams friction (C = {HW_C_DI_20YR:.0f}, "
              f"G202-p104 Table 21) less the {M['leg']['fall_grd']:.1f} m the ground "
              f"falls. Power at {PROJ_PUMP_EFF:.2f} wire-to-water is OURS. The linear "
              f"scaling of duty with pump count is OURS and a screening assumption — "
              f"parallel pumps on a common main deliver less."))
    return fk.save(fig, "FM03_diameter_velocity_window")


def fig_retention(M):
    fig, axes = fk.chart_frame(
        title=(f"Past {V_MAX_RISING*RETENTION_IDEAL_MIN*60/1000:.1f} km no force main "
               f"can meet the guideline's own half-hour retention, at any diameter"),
        subtitle=(f"G203-p50 8.2.1 wants a retention period no longer than "
                  f"{RETENTION_IDEAL_MIN:.0f} minutes; G203-p50 8.1 fixes velocity "
                  f"between {V_MIN_RISING:.2f} and {V_MAX_RISING:.1f} m/s. Length "
                  f"= velocity x time, so the two clauses together are a ceiling on "
                  f"LENGTH, and diameter never enters it. Retention drives H2S: "
                  f"G203-p47 7.7 asks for 50–100 ppm average and <= 200 ppm peak to be "
                  f"designed for wherever long retention is expected."),
        figsize=(10.4, 4.8), ncols=2, ygrid=True)
    axL, axR = axes

    v = np.linspace(V_MIN_RISING, V_MAX_RISING, 120)
    axL.fill_between(v, 0, v * RETENTION_IDEAL_MIN * 60 / 1000.0,
                     color=fk.C.PASS, alpha=0.5, lw=0,
                     label=f"retention <= {RETENTION_IDEAL_MIN:.0f} min")
    axL.plot(v, v * RETENTION_IDEAL_MIN * 60 / 1000.0, color=fk.C.INK, lw=1.6)
    for vv in (1.0, 1.5, 2.0):
        axL.annotate(f"{vv:.1f} m/s -> {vv*RETENTION_IDEAL_MIN*60:,.0f} m",
                     (vv, vv * RETENTION_IDEAL_MIN * 60 / 1000.0), xytext=(4, -12),
                     textcoords="offset points", fontsize=7.0, color=fk.C.GREY)
    pts = [(f["name"], f["rm_len"] / 1000.0, f.get("v_all", np.nan)) for f in M["fms"]]
    for nm, Lkm, vv in pts:
        axL.plot([vv], [Lkm], marker="o", ms=7, mfc=fk.C.PASS, mec=fk.C.INK, zorder=6)
        axL.annotate(f"{nm}  {Lkm*1000:,.0f} m", (vv, Lkm), xytext=(6, 4),
                     textcoords="offset points", fontsize=7.2)
    bl = M["align"][0]["len_m"] / 1000.0
    axL.plot([V_MIN_RISING, V_MAX_RISING], [bl, bl], color=fk.C.FAIL, lw=2.0, zorder=6)
    axL.annotate(f"built 2006 main — {bl:.2f} km, outside the window at every velocity",
                 (V_MIN_RISING + 0.05, bl), xytext=(0, 6),
                 textcoords="offset points", fontsize=7.4, color=fk.C.FAIL,
                 fontweight="bold")
    axL.set_xlabel("velocity in the main (m/s)")
    axL.set_ylabel("force-main length (km)")
    axL.set_ylim(0, bl * 1.22)
    axL.legend(loc="lower right", fontsize=7.2)

    names = [f["name"] for f in M["fms"]] + ["built 2006 main"]
    ret_lo = [f["ret_all_min"] for f in M["fms"]] + [
        M["align"][0]["len_m"] / V_MAX_RISING / 60.0]
    ret_hi = [f["ret_one_min"] for f in M["fms"]] + [
        M["align"][0]["len_m"] / V_MIN_RISING / 60.0]
    y = np.arange(len(names))[::-1]
    for yy, a, b, nm in zip(y, ret_lo, ret_hi, names):
        role = "fail" if b > RETENTION_IDEAL_MIN else "pass"
        axR.barh(yy, b - a, left=a, height=0.5, **fk.status_style(role))
        axR.annotate(f"{a:.1f}–{b:.1f} min", (b, yy), xytext=(6, 0),
                     textcoords="offset points", va="center", fontsize=7.2)
    axR.axvline(RETENTION_IDEAL_MIN, color=fk.C.FAIL, lw=1.4, ls="--", zorder=6)
    axR.annotate(f"{RETENTION_IDEAL_MIN:.0f} min — G203-p50 8.2.1",
                 (RETENTION_IDEAL_MIN, y.max() + 0.45), xytext=(4, 0),
                 textcoords="offset points", fontsize=7.2, color=fk.C.FAIL)
    axR.set_yticks(y)
    axR.set_yticklabels(names, fontsize=7.6)
    axR.set_xscale("log")
    axR.set_xlabel("retention time (minutes, log scale) — one duty pump to all duty pumps")
    fk.legend_below(axR, fk.status_legend({"pass": "within the half-hour ideal",
                                           "fail": "beyond it — a septicity design"}),
                    ncol=2, drop=0.35)
    fk.finish_chart(
        fig, source=fk.source_line(M["src"]["pumped"], M["src"]["stations"],
                                   M["src"]["built"]),
        note=("Retention is length / velocity. The band is one duty pump running to "
              "every duty pump running; the diameters are those in the FM-1/2/3 table, "
              "and the built main's band is the guideline velocity window because its "
              "diameter is not recorded (OUT_DIAMET = 0 on that row)."))
    return fk.save(fig, "FM04_retention_ceiling")


# ---------------------------------------------------------------------- reporting

def report(M):
    L = []
    p = L.append
    o, leg = M["outfall"], M["leg"]
    p("=" * 78)
    p("WHAT FORCE MAINS THIS DESIGN ACTUALLY HAS")
    p("=" * 78)
    p(M["roots"].to_string(index=False))
    p(f"\nThe outfall carries {o['q_adf']:,.0f} m3/d and {o['q_pk']:,.1f} L/s to the "
      f"works BY GRAVITY, arriving at {o['inv']:.3f} m aOD, {o['depth']:.2f} m below "
      f"ground ({o['grd']:.2f} m).")
    p("\n" + "=" * 78)
    p("THE WORKS LEG")
    p("=" * 78)
    for k in ("n_reach", "len_m", "dn", "fall_inv", "fall_grd", "slope_pct",
              "cover_min", "cover_mean", "cover_max", "on_wadi_m", "on_dual_m",
              "ret_min", "v_lo", "v_hi", "od_m", "s_min", "arrival_ceiling",
              "headroom", "binding_ch", "ground_check_max_abs"):
        p(f"  {k:>22} : {leg[k]}")
    p("\n" + "=" * 78)
    p("ALIGNMENT COMPARISON, 2006 STATION TO THE WORKS")
    p("=" * 78)
    keys = ["len_m", "z_start", "z_end", "net_fall_m", "summit_above_start_m",
            "cum_rise_m", "tested_pct", "untested_pct", "wadi_m", "wadi_runs",
            "wadi_longest_m", "dual_min_m", "dual_within6_m", "offroad_pct",
            "road_median_m", "summits", "lows", "access_pts", "iso_min", "iso_max"]
    p(pd.DataFrame({a["name"]: {k: a[k] for k in keys}
                    for a in M["align"] + [M["align_trim"]]}).round(2).to_string())
    p("\n  endpoint honesty — A and B do not start at the same place:")
    for k, v in M["junction_offset"].items():
        p(f"    {k:>26} : {v:,.1f}")
    p("\n  where the wadi contact sits on each alignment (chainage start, end, length):")
    for a in M["align"] + [M["align_trim"]]:
        p(f"    {a['name']:<38} first km {a['wadi_in_first_km_m']:6.0f} m   "
          f"{a['wadi_runs_detail']}")
    p("\n" + "=" * 78)
    p("THE THREE RISING MAINS THE DESIGN NEEDS")
    p("=" * 78)
    fk_keys = ["station_node", "st_x", "st_y", "grd", "inv", "cover", "why",
               "q_adf", "q_pk_ls", "n_prop", "st_type", "n_duty", "d_lo_mm",
               "d_hi_mm", "DN", "rm_len", "static_lift", "v_all", "v_one",
               "ret_all_min", "ret_one_min", "hf_all_m", "tot_head_m", "well_m3",
               "kw", "summits", "lows", "wadi_m", "untested_pct", "dual_min_m",
               "haz_at_station", "summit_above_start_m", "net_fall_m"]
    p(pd.DataFrame({f["name"]: {k: f.get(k) for k in fk_keys}
                    for f in M["fms"]}).to_string())
    p("\n" + "=" * 78)
    p("CONDITIONAL TERMINAL MAIN AT THE WORKS")
    p("=" * 78)
    for k, v in M["terminal"].items():
        p(f"  {k:>22} : {v}")
    p("\n" + "=" * 78)
    p("THE PUMPED ALTERNATIVE TO THE 9 KM GRAVITY LEG")
    p("=" * 78)
    p(M["pumped_alt"].round(3).to_string(index=False))
    p("\n" + "=" * 78)
    p("RETENTION CEILING (G203-p50 8.2.1 with 8.1)")
    p("=" * 78)
    for v in (0.75, 1.0, 1.5, 2.0, 2.5):
        p(f"  at {v:.2f} m/s a {RETENTION_IDEAL_MIN:.0f}-minute retention caps a "
          f"force main at {v*RETENTION_IDEAL_MIN*60:,.0f} m")
    bl = M["align"][0]["len_m"]
    p(f"  the built 2006 main is {bl:,.0f} m -> {bl/V_MIN_RISING/3600:.2f} h at "
      f"{V_MIN_RISING} m/s, {bl/V_MAX_RISING/3600:.2f} h at {V_MAX_RISING} m/s")
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    M = measure()
    print(report(M))
    if "--numbers" in argv:
        return M
    print("\nFIGURES")
    for fn in (fig_route_map, fig_long_section, fig_diameter_window, fig_retention):
        try:
            print("  ->", fn(M))
        except Exception as exc:                              # noqa: BLE001
            print(f"  !! {fn.__name__} failed: {type(exc).__name__}: {exc}")
            raise
    return M


if __name__ == "__main__":
    main()
