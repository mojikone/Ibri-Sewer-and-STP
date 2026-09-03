"""west - the measurements behind `W11a/docs/WEST_CONNECTIVITY.md`, and its three figures.

THE QUESTION.  The user flagged that the western leg of the main pipe is not connected to
the rest of it.  Stage 1 found that the west closed basin's low point at 442 092 E
2 569 064 N lies INSIDE the core conurbation (SID 18), so W10's research note "AL DIREZ is
the west leg" does not hold and the west may be a sub-catchment of the central system
rather than a separate one.  This module measures what the west carries, whether it can
reach a works by gravity and at what depth, what pumping it needs if not, and what the gap
at OPEN S3-1 actually is.

WHAT IT MEASURES, AND WHY EACH MEASUREMENT IS SHAPED THE WAY IT IS
-----------------------------------------------------------------
1.  THE CATCHMENT, TWO INDEPENDENT WAYS.  A network catchment on the stage-2 corridor graph
    (every plot to its nearest corridor node; every corridor node to whichever set of trunk
    chambers - west leg or the rest - is nearer along the graph), and stage 3's own
    nearest-trunk-chamber assignment read straight off the published trunk layer.  Two
    methods that share no code and no assumption beyond the plot loads.

2.  THE BOTTLENECK, ON THE GROUND AND ON THE CORRIDORS.  A minimax (bottleneck) search
    returns, for every point, the LOWEST elevation any route to the works must cross.  If
    that is above the point's own ground, no gravity route exists there and the difference
    is the minimum static lift - before cover, before gradient, before anything a designer
    can trade.  Run it on the DEM and it says what the GROUND allows.  Run it on the
    corridor graph and it says what the STREETS allow.  In the west the two disagree by a
    median of over 11 m, and that disagreement is the finding.

3.  WHETHER A GRAVITY ALIGNMENT EXISTS AT ALL.  Not "is there a low route" but "is there a
    route on which a DN900 at 0.100 % stays between 1.30 m and 12.00 m of cover the whole
    way".  Dijkstra by path length, with the cover window as an admissibility filter: the
    invert at a cell reached after d metres is inv0 - S*d, so keeping the path SHORT keeps
    the invert HIGH, which is exactly the profile that minimises the deepest cover.  Scan
    the starting cover; if any value connects, gravity works.

4.  THE GAP AT OPEN S3-1, measured from the input drawing itself, and the shortest route
    across it that stays on real street corridors.

WHAT IT DOES NOT DO.  It does not cost anything.  The Renardet unit-rate data is still
outstanding (`_BRAIN/00_CURRENT.md`), the PIAD rates are a potable-water scheme's and the
PIAD review catalogues them as defective, so a monetary comparison here would be an
invented number.  Pumping energy is reported as physics - rho*g*Q*H over an efficiency that
is LABELLED as an assumption - and the money is left to the options appraisal.

EVERY NUMBER TRACES TO ONE OF THESE ARTEFACTS
    W11a/shp/W11a.gpkg              corridors, corridor_nodes  (stage 2)
    W11a/shp/W11a_trunk.gpkg        reaches, nodes             (stage 3, audited)
    W11a/run/s3_trunk_stations.csv  the three stations         (stage 3)
    Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt                    the 0.5 m terrain
    Data/04 Lekhuwair/Hazard_T50y.tif                          the 50-year hazard grid
    W10/shp/W10_plot_loads.gpkg     plot loads, the stage-1 input
    Hydraulic/SHP/Main Pipe/Main Pipe.shp                      the drawn trunk, an INPUT
Anything else on a figure is a guideline value with its page, or a project assumption
labelled as one.

    python west.py            measure, print the table, draw FL01 / FL02 / FL03
    python west.py --figs     draw from the cache, skip the slow searches
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import figkit as fk                                         # noqa: E402

import geopandas as gpd                                     # noqa: E402
import rasterio                                             # noqa: E402
from matplotlib.lines import Line2D                         # noqa: E402
from matplotlib.patches import Patch                        # noqa: E402
from rasterio.enums import Resampling                       # noqa: E402
from rasterio.windows import from_bounds                    # noqa: E402
from scipy.spatial import cKDTree                           # noqa: E402
from shapely.geometry import LineString, Point              # noqa: E402
from shapely.ops import unary_union                         # noqa: E402
from shapely.strtree import STRtree                         # noqa: E402

# --------------------------------------------------------------------------- fixed points

#: user-confirmed 2026-09-01, CLAUDE.md.  Ground 328.7 m aOD there.
WORKS = (444422.8, 2563337.9)
#: the west closed basin's low point.  W10 Phase 5 / stage 1 `check_west_basin`.
WEST_LOW = (442092.0, 2569064.0)
#: OPEN S3-1.  Measured here from `Main Pipe.shp` itself, never taken from the build note.
GAP_FROM = (447084.1545968621, 2567523.0637987405)
GAP_TO = (447843.7257607772, 2567079.058588501)

MAIN_PIPE = fk.HYD / "SHP" / "Main Pipe" / "Main Pipe.shp"
PLOT_LOADS = fk.ROOT / "W10" / "shp" / "W10_plot_loads.gpkg"
STREAMS = fk.HYD / "SHP" / "Streams" / "Streams NSA 2m.shp"
DEM = fk.BASE / "Data" / "Terrain" / "Sat_0p5m" / "IBRI_0p5_VRT2.vrt"

CACHE = fk.SCRATCH / "west_cache"

# -------------------------------------------------------- design values, each with its page

DN = 900                    #: sized by hydra.size_pipe on stage 3's published peak flow
SLOPE = 0.0010              #: 0.100 % - the flattest gradient on the project's own 0.05 %
#                              laying step (criteria.SLOPE_STEP, user 2026-08-23) that
#                              clears Table 11's 0.75 mm/m floor at DN900 (G203-p29).
OD_ALLOW = DN / 1000.0 + 0.10       #: contract.cover(), the auditor's own arithmetic
COVER_MIN = 1.30            #: G203-p33 4.6.3, minimum cover to crown
COVER_CAP = 12.00           #: G203-p33, "approximately 10-12 m", the philosophy sec 5 cap
PUMP_ETA = 0.65             #: ASSUMPTION.  No project or guideline value exists for it.

GRID_RES = 10.0             #: DEM resample for the searches.  Checked against the raw
#                              0.5 m grid along the answer - see `dem_sensitivity()`.
BOX = (434000, 2560000, 452000, 2574000)
MAP_EXTENT = (432200, 2562000, 452500, 2577000)


# ==========================================================================================
# terrain
# ==========================================================================================

def load_dem(box=BOX, res=GRID_RES):
    """Resampled terrain over `box`, plus the cell<->coordinate helpers.

    The VRT is 0.5 m and 151 370 x 148 490; a bottleneck search on it would be pointless as
    well as impossible.  `dem_sensitivity()` proves the resample does not move the answer:
    along the alignment this module finds, the 10 m average and the raw 0.5 m grid differ
    by a mean of 0.000 m and a standard deviation of 0.021 m.
    """
    x0, y0, x1, y1 = box
    with rasterio.open(DEM) as src:
        win = from_bounds(x0, y0, x1, y1, src.transform)
        h, w = int((y1 - y0) / res), int((x1 - x0) / res)
        z = src.read(1, window=win, out_shape=(h, w),
                     resampling=Resampling.average).astype("float64")
    z = np.where(z <= -1000, np.nan, z)

    def rc(x, y):
        return int((y1 - y) / res), int((x - x0) / res)

    def xy(r, c):
        return x0 + c * res + res / 2, y1 - r * res - res / 2

    return z, rc, xy


def bottleneck_grid(z, src_rc):
    """For every cell: the lowest elevation a route from `src_rc` must cross.

    Minimax Dijkstra.  `best[cell] - z[cell]` is the static lift the GROUND demands, and it
    is a floor: no alignment, gradient or diameter can beat it.
    """
    import heapq
    h, w = z.shape
    big = np.where(np.isnan(z), 1e9, z)
    best = np.full(z.shape, np.inf)
    done = np.zeros(z.shape, bool)
    r0, c0 = src_rc
    best[r0, c0] = big[r0, c0]
    pq = [(best[r0, c0], r0, c0)]
    nbr = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
    while pq:
        v, r, c = heapq.heappop(pq)
        if done[r, c]:
            continue
        done[r, c] = True
        for dr, dc in nbr:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and not done[rr, cc]:
                nv = v if big[rr, cc] <= v else big[rr, cc]
                if nv < best[rr, cc]:
                    best[rr, cc] = nv
                    heapq.heappush(pq, (nv, rr, cc))
    return best


def gravity_alignment(z, rc, xy, src, tgt, *, dn=DN, slope=SLOPE,
                      cover_min=COVER_MIN, cover_cap=COVER_CAP):
    """Shortest alignment on which ONE gravity run stays inside the cover window.

    Cost is path length, so the search keeps the invert as high as the gradient allows; a
    cell is enterable only while its cover is within [cover_min, cover_cap].  Both bounds
    are G203-p33 (H3 and H4).  Returns the profile for the shallowest starting cover that
    connects, or None.
    """
    import heapq
    h, w = z.shape
    od = dn / 1000.0 + 0.10
    r0, c0 = src
    nbr = ((-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
           (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142))

    def run(inv0, want_path=False):
        cov0 = z[r0, c0] - inv0 - od
        if not (cover_min - 1e-9 <= cov0 <= cover_cap + 1e-9):
            return np.inf, None
        dist = np.full(z.shape, np.inf)
        done = np.zeros(z.shape, bool)
        prev = np.full(z.shape + (2,), -1, dtype=np.int32)
        dist[r0, c0] = 0.0
        pq = [(0.0, r0, c0)]
        while pq:
            dd, r, c = heapq.heappop(pq)
            if done[r, c]:
                continue
            done[r, c] = True
            if (r, c) == tgt:
                break
            for dr, dc, ln in nbr:
                rr, cc = r + dr, c + dc
                if not (0 <= rr < h and 0 <= cc < w) or done[rr, cc]:
                    continue
                nd = dd + ln * GRID_RES
                if nd >= dist[rr, cc]:
                    continue
                cov = z[rr, cc] - (inv0 - slope * nd) - od
                if np.isnan(cov) or cov < cover_min or cov > cover_cap:
                    continue
                dist[rr, cc] = nd
                prev[rr, cc] = (r, c)
                heapq.heappush(pq, (nd, rr, cc))
        d = dist[tgt]
        if not np.isfinite(d) or not want_path:
            return d, None
        p = [tgt]
        while prev[p[-1][0], p[-1][1]][0] >= 0:
            a, b = prev[p[-1][0], p[-1][1]]
            p.append((int(a), int(b)))
        return d, p[::-1]

    for start_cover in np.arange(cover_min, cover_cap + 0.001, 0.25):
        inv0 = z[src] - start_cover - od
        d, _ = run(inv0)
        if np.isfinite(d):
            _, path = run(inv0, want_path=True)
            pts = np.array([xy(*q) for q in path])
            grd = np.array([z[q] for q in path])
            ch = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(pts[:, 0]),
                                                           np.diff(pts[:, 1])))])
            inv = inv0 - slope * ch
            return dict(start_cover=float(start_cover), ch=ch, pts=pts, grd=grd,
                        inv=inv, cover=grd - inv - od)
    return None


def dual_check(pts):
    """Dual-carriageway contact on a candidate alignment.

    Project rule 7 excludes a pipe running ALONG a dual carriageway and allows a short
    perpendicular CROSSING.  `dual == 1` in `SHP/Road centerline 2` is the dual carriageway;
    `2` is a two-lane pair where only one side is used, so only `1` is tested here.  A count
    of centreline intersections is a count of CROSSINGS; contact inside the 6 m band is what
    would make it a run along one, and both are reported.
    """
    roads = gpd.read_file(fk.HYD / "SHP" / "Road centerline 2" / "Road_Centercline.shp")
    if roads.crs is None or roads.crs.to_epsg() != fk.EPSG:
        roads = roads.to_crs(fk.EPSG)
    if "dual" not in roads.columns:
        return dict(dual_crossings=-1, dual_band_samples=-1)
    dual = roads[roads["dual"] == 1]
    line = LineString(pts)
    hit = line.intersection(unary_union(dual.geometry.values))
    n = 0 if hit.is_empty else (1 if hit.geom_type == "Point"
                                else len(getattr(hit, "geoms", [])))
    tree = STRtree(dual.geometry.values)
    d = np.array([dual.geometry.values[tree.nearest(Point(p))].distance(Point(p))
                  for p in pts])
    return dict(dual_crossings=int(n), dual_band_samples=int((d < 6.0).sum()),
                dual_nearest_m=float(d.min()))


def dem_sensitivity(res):
    """Re-read the alignment's ground on the RAW 0.5 m grid.  Reported, not assumed."""
    with rasterio.open(DEM) as d:
        z05 = np.array([v[0] for v in d.sample([(x, y) for x, y in res["pts"]])],
                       dtype="float64")
    z05 = np.where(z05 <= -1000, np.nan, z05)
    cov = z05 - res["inv"] - OD_ALLOW
    diff = z05 - res["grd"]
    return dict(mean=float(np.nanmean(diff)), sd=float(np.nanstd(diff)),
                cover_min=float(np.nanmin(cov)), cover_max=float(np.nanmax(cov)),
                below_min=int(np.nansum(cov < COVER_MIN)),
                past_cap=int(np.nansum(cov > COVER_CAP)), n=int(len(cov)))


# ==========================================================================================
# the corridor graph
# ==========================================================================================

def corridor_graph():
    """Stage 2's published corridors as an undirected graph, with ground at every node."""
    cor = fk.read_layer("W11a.gpkg", "corridors",
                        columns=["CORR_ID", "US_NODE", "DS_NODE", "LEN_M", "SRC",
                                 "CONFIDENCE", "IS_STREET", "ON_WADI_M", "ON_DUAL_M"])
    cn = fk.read_layer("W11a.gpkg", "corridor_nodes",
                       columns=["NODE_UID", "NODE_KIND", "X", "Y", "DEGREE"])
    with rasterio.open(DEM) as d:
        z = np.array([v[0] for v in d.sample(list(zip(cn.X.values, cn.Y.values)))],
                     dtype="float64")
    cn["Z"] = np.where(z <= -1000, np.nan, z)
    adj = defaultdict(list)
    for u, v, L in zip(cor.US_NODE, cor.DS_NODE, cor.LEN_M):
        adj[u].append((v, float(L)))
        adj[v].append((u, float(L)))
    return cor, cn, adj


def bottleneck_graph(adj, Z, root):
    """Minimax Dijkstra on the corridor graph, with path length as the tie-break."""
    import heapq
    best = defaultdict(lambda: np.inf)
    dist = defaultdict(lambda: np.inf)
    best[root] = Z[root]
    dist[root] = 0.0
    pq = [(Z[root], 0.0, root)]
    done = set()
    while pq:
        b, d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        for v, L in adj[u]:
            if v in done:
                continue
            nb = b if Z[v] <= b else Z[v]
            nd = d + L
            if nb < best[v] - 1e-9 or (abs(nb - best[v]) <= 1e-9 and nd < dist[v]):
                best[v], dist[v] = nb, nd
                heapq.heappush(pq, (nb, nd, v))
    return best, dist


def shortest_path(adj, a, b):
    """Plain Dijkstra, returning (length, node path)."""
    import heapq
    D = defaultdict(lambda: np.inf)
    D[a] = 0.0
    pq = [(0.0, a)]
    done, prev = set(), {}
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        if u == b:
            break
        for v, L in adj[u]:
            if d + L < D[v]:
                D[v] = d + L
                prev[v] = u
                heapq.heappush(pq, (d + L, v))
    p = [b]
    while p[-1] in prev:
        p.append(prev[p[-1]])
    return D[b], p[::-1]


def multi_source(adj, sources):
    """Distance from the nearest of many sources."""
    import heapq
    D = defaultdict(lambda: np.inf)
    pq = []
    for s in sources:
        D[s] = 0.0
        heapq.heappush(pq, (0.0, s))
    done = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in done:
            continue
        done.add(u)
        for v, L in adj[u]:
            if v not in done and d + L < D[v]:
                D[v] = d + L
                heapq.heappush(pq, (d + L, v))
    return D


def trunk_west_nodes(tr, tn):
    """The trunk chambers WEST of the junction, from the published layer's own topology.

    The three stations split the published gravity layer into four components (contract
    OPEN-1).  The third and fourth by size are the western arm and the stretch through the
    S3-1 gap connector; together they are "the west leg".
    """
    adj = defaultdict(set)
    for u, v in zip(tr.US_NODE, tr.DS_NODE):
        adj[u].add(v)
        adj[v].add(u)
    seen, comps = set(), []
    for v in tn.NODE_UID:
        if v in seen:
            continue
        c, q = {v}, deque([v])
        seen.add(v)
        while q:
            x = q.popleft()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    c.add(y)
                    q.append(y)
        comps.append(c)
    comps.sort(key=len, reverse=True)
    return comps[2] | comps[3]


# ==========================================================================================
# the measurement run
# ==========================================================================================

def measure() -> dict:
    """Everything the document and the figures quote.  Cached, because it is slow."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out: dict = {}

    cor, cn, adj = corridor_graph()
    tr = fk.read_layer("W11a_trunk.gpkg", "reaches")
    tn = fk.read_layer("W11a_trunk.gpkg", "nodes")
    stn = fk.read_csv("s3_trunk_stations.csv")
    pl = fk.read_layer(str(PLOT_LOADS), "plot_loads",
                       columns=["PLOT_ID", "N_PROP", "POP", "Q_AVG_M3D", "IN_BND"])
    out["src"] = dict(cor=fk.cite(cor), tr=fk.cite(tr), tn=fk.cite(tn),
                      stn=fk.cite(stn), pl=fk.cite(pl))

    Z = dict(zip(cn.NODE_UID, cn.Z))
    cx, cy, cid = cn.X.values, cn.Y.values, cn.NODE_UID.values
    ctree = cKDTree(np.c_[cx, cy])

    def snap(x, y):
        d, i = ctree.query([x, y])
        return cid[i], float(d)

    # --- 1. the catchment, on the corridor graph -----------------------------------------
    west_trunk = trunk_west_nodes(tr, tn)
    sW, sR = set(), set()
    for _, r in tn.iterrows():
        s, _d = snap(r.X, r.Y)
        (sW if r.NODE_UID in west_trunk else sR).add(s)
    sW -= sW & sR
    DW, DR = multi_source(adj, sW), multi_source(adj, sR)
    cn["dW"] = [DW[u] for u in cn.NODE_UID]
    cn["dR"] = [DR[u] for u in cn.NODE_UID]
    cn["side"] = np.where(np.isinf(cn.dW) & np.isinf(cn.dR), "unreachable",
                          np.where(cn.dW < cn.dR, "west", "rest"))
    pc = pl.geometry.representative_point()
    _d, ii = ctree.query(np.c_[pc.x.values, pc.y.values])
    pl["cnode"] = cid[ii]
    side = dict(zip(cn.NODE_UID, cn.side))
    pl["side"] = [side[c] for c in pl.cnode]
    pw = pl[pl.side == "west"]
    out["catch"] = dict(plots=int(len(pw)), q=float(pw.Q_AVG_M3D.sum()),
                        prop=float(pw.N_PROP.sum()), pop=float(pw.POP.sum()),
                        q_total=float(pl.Q_AVG_M3D.sum()), plots_total=int(len(pl)))
    cor["su"] = [side.get(u) for u in cor.US_NODE]
    cor["sv"] = [side.get(v) for v in cor.DS_NODE]
    wc = cor[(cor.su == "west") & (cor.sv == "west")]
    out["catch"]["corridor_km"] = float(wc.LEN_M.sum() / 1000)
    out["catch"]["corridor_km_total"] = float(cor.LEN_M.sum() / 1000)
    out["catch"]["m_per_prop"] = float(wc.LEN_M.sum() / pw.N_PROP.sum())
    out["catch"]["m_per_prop_net"] = float(cor.LEN_M.sum() / pl.N_PROP.sum())

    # Stage 3's own, independent assignment: every in-boundary plot's ultimate Qadf to its
    # NEAREST TRUNK CHAMBER, then accumulated downstream.  The most-downstream west-leg
    # chamber therefore carries the whole west leg's load, and it is read straight off the
    # published node layer rather than recomputed here.
    wn_all = tn[tn.NODE_UID.isin(west_trunk)]
    wr_all = tr[tr.US_NODE.isin(west_trunk) & tr.DS_NODE.isin(west_trunk)]
    out["catch"]["s3_q"] = float(wn_all.Q_ADF_M3D.max())
    out["catch"]["s3_qpk"] = float(wn_all.Q_PK_LS.max())
    out["catch"]["s3_prop"] = float(wn_all.N_PROP.max())
    out["catch"]["s3_pf"] = float(wr_all.loc[wr_all.QADF_M3D.idxmax(), "PF"])
    out["catch"]["s3_dn"] = int(wr_all.loc[wr_all.QADF_M3D.idxmax(), "DN"])

    # --- 2. bottleneck: the ground vs the streets ----------------------------------------
    z, rc, xy = load_dem()
    tb = bottleneck_grid(z, rc(*WORKS))
    rr = np.clip(((BOX[3] - cn.Y.values) / GRID_RES).astype(int), 0, z.shape[0] - 1)
    cc = np.clip(((cn.X.values - BOX[0]) / GRID_RES).astype(int), 0, z.shape[1] - 1)
    inbox = ((cn.X.values > BOX[0]) & (cn.X.values < BOX[2])
             & (cn.Y.values > BOX[1]) & (cn.Y.values < BOX[3]))
    cn["terr_bott"] = np.where(inbox, tb[rr, cc], np.nan)
    cn["terr_lift"] = np.maximum(0.0, cn.terr_bott - cn.Z)

    root, _dr = snap(*WORKS)
    gb, gd = bottleneck_graph(adj, Z, root)
    cn["corr_bott"] = [gb[u] for u in cn.NODE_UID]
    cn["corr_lift"] = np.maximum(0.0, cn.corr_bott - cn.Z)
    cn["corr_dist"] = [gd[u] for u in cn.NODE_UID]

    w = cn[(cn.side == "west") & inbox]
    out["lift"] = dict(
        n=int(len(w)),
        terr_zero=int((w.terr_lift <= 0.01).sum()),
        terr_med=float(w.terr_lift.median()), terr_p90=float(w.terr_lift.quantile(0.9)),
        terr_max=float(w.terr_lift.max()),
        corr_zero=int((w.corr_lift <= 0.01).sum()),
        corr_med=float(w.corr_lift.median()), corr_p90=float(w.corr_lift.quantile(0.9)),
        corr_max=float(w.corr_lift.max()),
        penalty_med=float((w.corr_lift - w.terr_lift).median()))
    TL = dict(zip(cn.NODE_UID, cn.terr_lift))
    CL = dict(zip(cn.NODE_UID, cn.corr_lift))
    pl["terr_lift"] = [TL.get(c, np.nan) for c in pl.cnode]
    pl["corr_lift"] = [CL.get(c, np.nan) for c in pl.cnode]
    pw = pl[pl.side == "west"]
    bins = [(-1, 0.01), (0.01, 2), (2, 5), (5, 10), (10, 20), (20, 1e9)]
    out["lift"]["by_load"] = [
        dict(lo=max(lo, 0), hi=hi,
             q_terr=float(pw.loc[(pw.terr_lift > lo) & (pw.terr_lift <= hi),
                                 "Q_AVG_M3D"].sum()),
             q_corr=float(pw.loc[(pw.corr_lift > lo) & (pw.corr_lift <= hi),
                                 "Q_AVG_M3D"].sum()))
        for lo, hi in bins]

    # the corridor layer's own tearing, because it decides how much of the above to believe
    rng = np.random.default_rng(11)
    idx = np.where((cn.side == "west").values)[0]
    pick = rng.choice(idx, size=min(150, len(idx)), replace=False)
    ratios, unreach = [], 0
    xy_all = np.c_[cx, cy]
    for i in pick:
        d, j = ctree.query(xy_all[i], k=40)
        cand = [(dd, jj) for dd, jj in zip(d, j) if 300 < dd < 800]
        if not cand:
            continue
        dd, jj = cand[0]
        L, _p = shortest_path(adj, cid[i], cid[jj])
        if not np.isfinite(L) or L > 8000:
            unreach += 1
        else:
            ratios.append(L / dd)
    out["tear"] = dict(n=len(ratios) + unreach, med=float(np.median(ratios)),
                       over3=float(100 * np.mean(np.array(ratios) > 3)),
                       unreach=float(100 * unreach / max(len(ratios) + unreach, 1)))
    ci = cn.set_index("NODE_UID")
    a, _ = snap(442331, 2570165)
    b, _ = snap(*WEST_LOW)
    L, _p = shortest_path(adj, a, b)
    straight = float(np.hypot(ci.X[a] - ci.X[b], ci.Y[a] - ci.Y[b]))
    out["tear"]["worst_straight_m"] = straight
    out["tear"]["worst_corridor_m"] = float(L)

    # --- 3. does a gravity alignment exist ----------------------------------------------
    res = gravity_alignment(z, rc, xy, rc(*WEST_LOW), rc(*WORKS))
    out["w3"] = None
    if res is not None:
        out["w3"] = dict(len_km=float(res["ch"][-1] / 1000),
                         start_cover=res["start_cover"],
                         cover_max=float(res["cover"].max()),
                         cover_end=float(res["cover"][-1]),
                         inv_start=float(res["inv"][0]), inv_end=float(res["inv"][-1]),
                         grd_start=float(res["grd"][0]), grd_end=float(res["grd"][-1]))
        out["w3"]["dem"] = dem_sensitivity(res)
        np.save(CACHE / "w3_pts.npy", res["pts"])
        np.save(CACHE / "w3_prof.npy",
                np.vstack([res["ch"], res["grd"], res["inv"], res["cover"]]))
        line = LineString(res["pts"])
        with rasterio.open(fk.HAZARD) as h:
            hv = np.array([s[0] for s in h.sample([(x, y) for x, y in res["pts"]])],
                          dtype="float64")
        unt = hv <= -1000
        out["w3"]["hz_untested_pct"] = float(100 * unt.mean())
        out["w3"]["hz_wadi_pct"] = (float(100 * (hv[~unt] >= 4).mean())
                                    if (~unt).any() else float("nan"))
        st = gpd.read_file(STREAMS)
        if st.crs is None or st.crs.to_epsg() != fk.EPSG:
            st = st.to_crs(fk.EPSG)
        stree = STRtree(st.geometry.values)
        ds = np.array([st.geometry.values[stree.nearest(Point(p))].distance(Point(p))
                       for p in res["pts"]])
        out["w3"]["stream_med_m"] = float(np.median(ds))
        out["w3"]["stream_within25_pct"] = float(100 * (ds < 25).mean())
        dcorr, _ = ctree.query(res["pts"])
        out["w3"]["corr_med_m"] = float(np.median(dcorr))
        out["w3"]["corr_max_m"] = float(dcorr.max())
        out["w3"]["off_corridor_pct"] = float(100 * (dcorr > 50).mean())
        out["w3"]["plots_crossed"] = int(len(pl[pl.intersects(line)]))
        out["w3"].update(dual_check(res["pts"]))

    # --- 4. OPEN S3-1, from the drawing itself ------------------------------------------
    mp = gpd.read_file(MAIN_PIPE)
    lens = mp.length.values
    idx = int(np.argmin(np.abs(lens - 7865.87)))
    leg = mp.geometry.iloc[idx]
    rest = unary_union([g for i, g in enumerate(mp.geometry) if i != idx])
    out["gap"] = dict(leg_len_m=float(leg.length),
                      end_to_rest_m=float(Point(list(leg.coords)[-1]).distance(rest)),
                      closest_approach_m=float(leg.distance(rest)),
                      n_polylines=int(len(mp)), total_km=float(mp.length.sum() / 1000),
                      straight_m=float(Point(GAP_FROM).distance(Point(GAP_TO))))
    na, _ = snap(*GAP_FROM)
    nb, _ = snap(*GAP_TO)
    L, path = shortest_path(adj, na, nb)
    out["gap"]["corridor_route_m"] = float(L)
    out["gap"]["corridor_route_zmax"] = float(max(Z[p] for p in path))
    gsub = cor[cor.US_NODE.isin(path) & cor.DS_NODE.isin(path)]
    out["gap"]["street_share_pct"] = (float(100 * gsub.IS_STREET.mean())
                                      if len(gsub) else 0.0)
    out["gap"]["on_wadi_m"] = float(gsub.ON_WADI_M.sum())
    out["gap"]["on_dual_m"] = float(gsub.ON_DUAL_M.sum())
    np.save(CACHE / "gap_path.npy", np.array([[ci.X[p], ci.Y[p]] for p in path]))

    # --- 5. the west as drawn, and what it pumps ----------------------------------------
    wn = tn[tn.NODE_UID.isin(west_trunk)]
    st_w = stn[stn.x < 448000]
    rho, g = 1000.0, 9.81
    kwh = float(((rho * g * (st_w.q_adf_m3d / 86400.0) * st_w.static_lift_m) / PUMP_ETA
                 * 8760 / 1000.0).sum())
    out["drawn"] = dict(
        gravity_km=float(wr_all.LEN_M.sum() / 1000),
        prov_km=float(wr_all.loc[wr_all.CONFIDENCE == "provisional", "LEN_M"].sum() / 1000),
        cover_max=float(max(wr_all.COVER_US.max(), wr_all.COVER_DN.max())),
        n_station=int(len(st_w)), lift_sum=float(st_w.static_lift_m.sum()),
        rm_m=float(st_w.rm_len_m.sum()), kwh_yr=kwh,
        lifts=[float(v) for v in st_w.static_lift_m],
        grd_hi=float(wn.GRD_M.max()), grd_lo=float(wn.GRD_M.min()))

    cn.drop(columns="geometry").to_pickle(CACHE / "cn.pkl")
    cor.to_pickle(CACHE / "cor.pkl")
    pl.drop(columns="geometry").to_pickle(CACHE / "pl.pkl")
    (CACHE / "out.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def load_cache() -> dict:
    return json.loads((CACHE / "out.json").read_text())


# ==========================================================================================
# figures
# ==========================================================================================

def fig_catchment(out):
    """FL01 - where the west is, what it carries, and the two ways out of it."""
    cor = pd.read_pickle(CACHE / "cor.pkl")
    tr = fk.read_layer("W11a_trunk.gpkg", "reaches")
    tn = fk.read_layer("W11a_trunk.gpkg", "nodes")
    w3 = np.load(CACHE / "w3_pts.npy")

    west = cor[(cor.su == "west") & (cor.sv == "west")]
    rest = cor[~cor.index.isin(west.index)]
    fig, ax, note = fk.map_frame(
        MAP_EXTENT,
        title="The west is 11.5 % of the load, and the ground does not close it in",
        subtitle=("West catchment on the stage-2 corridor graph: every plot to its nearest "
                  "corridor node, every node to the nearer set of trunk chambers. The trunk "
                  "as drawn leaves the west UPHILL and needs two lifting stations; a "
                  "gravity alignment to the existing works exists on open ground and needs "
                  "none. Hazard classes 4/5/6 as the wadi test are a PROJECT ASSUMPTION "
                  "standing in for G203-p30 4.4.1 'washout', not a guideline threshold."))
    rest.plot(ax=ax, color=fk.C.FAINT, linewidth=0.25, zorder=3)
    west.plot(ax=ax, color=fk.C.LATERAL, linewidth=0.5, zorder=4)
    tr.plot(ax=ax, color=fk.C.TRUNK, linewidth=2.2, zorder=6)
    prov = tr[tr.CONFIDENCE == "provisional"]
    if len(prov):
        prov.plot(ax=ax, color=fk.C.FLAG, linewidth=3.0, linestyle=(0, (3, 1.6)), zorder=7)
    ax.plot(w3[:, 0], w3[:, 1], color=fk.C.FAIL, lw=2.2, ls=(0, (7, 2.5)), zorder=8)
    st = tn[tn.NODE_KIND == "station"]
    ax.scatter(st.X, st.Y, s=95, marker="v", facecolor=fk.C.STATION,
               edgecolor="white", linewidth=1.0, zorder=10)
    ax.scatter([WORKS[0]], [WORKS[1]], s=180, marker="*", facecolor=fk.C.OUTFALL,
               edgecolor="white", linewidth=1.0, zorder=10)
    ax.scatter([WEST_LOW[0]], [WEST_LOW[1]], s=80, marker="o", facecolor="white",
               edgecolor=fk.C.INK, linewidth=1.3, zorder=10)
    ax.annotate("west basin low point\n442 092 E  2 569 064 N,  332.5 m",
                WEST_LOW, xytext=(-10, 16), textcoords="offset points", fontsize=7.4,
                ha="right", color=fk.C.INK, zorder=11,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.88))
    ax.annotate("existing works, 328.7 m", WORKS, xytext=(-14, -3),
                textcoords="offset points", fontsize=7.4, ha="right",
                color=fk.C.INK, zorder=11,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.88))
    known, _wadi, hext = fk.hazard_coverage(MAP_EXTENT)
    fk.hatch_untested(ax, ~known, hext)

    c, l3, gp, dr = out["catch"], out["w3"], out["gap"], out["drawn"]
    box = ("WEST CATCHMENT  (stage-2 corridor graph)\n"
           "  plots                     %9s\n"
           "  properties                %9s\n"
           "  ultimate Qadf             %9s m3/d\n"
           "  share of the network      %9.1f %%\n"
           "  corridor                  %9s km\n"
           "  stage 3's own answer      %9s m3/d\n"
           "AS DRAWN  (stage 3, published)\n"
           "  lifting stations          %9d\n"
           "  static lift               %9.2f m\n"
           "  provisional line          %9.0f m   OPEN S3-1\n"
           "GRAVITY ALIGNMENT  (measured here)\n"
           "  length                    %9.3f km\n"
           "  DN%d at %.3f %%, deepest    %6.2f m\n"
           "  lifting stations          %9d\n"
           "  over 50 m off a corridor  %9.0f %%"
           % (f"{c['plots']:,}", f"{c['prop']:,.0f}", f"{c['q']:,.0f}",
              100 * c["q"] / c["q_total"], f"{c['corridor_km']:,.1f}",
              f"{c['s3_q']:,.0f}", dr["n_station"], dr["lift_sum"], gp["straight_m"],
              l3["len_km"], DN, SLOPE * 100, l3["cover_max"], 0,
              l3["off_corridor_pct"]))
    handles = [
        Line2D([], [], color=fk.C.TRUNK, lw=2.2, label="trunk main, as drawn (an INPUT)"),
        Line2D([], [], color=fk.C.FLAG, lw=3.0, ls=(0, (3, 1.6)),
               label="provisional line - OPEN S3-1, 879.8 m the draftsman has not drawn"),
        Line2D([], [], color=fk.C.FAIL, lw=2.2, ls=(0, (7, 2.5)),
               label="gravity alignment measured here - DN%d at %.3f %%, no station"
                     % (DN, SLOPE * 100)),
        Line2D([], [], color=fk.C.LATERAL, lw=1.3, label="corridor, west catchment"),
        Line2D([], [], color=fk.C.FAINT, lw=1.3, label="corridor, rest of the network"),
        Line2D([], [], color="none", marker="v", markerfacecolor=fk.C.STATION,
               markeredgecolor="white", markersize=8, label="lifting station (stage 3)"),
        Line2D([], [], color="none", marker="*", markerfacecolor=fk.C.OUTFALL,
               markeredgecolor="white", markersize=13, label="existing works"),
        fk.untested_handle("UNTESTED - no hazard-grid answer"),
    ]
    fk.finish_map(
        fig, ax, note=note, legend_handles=handles, legend_loc="upper left", databox=box,
        source=fk.source_line(cor, tr,
                              "Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt (0.5 m terrain)"))
    return fk.save(fig, "FL01_west_catchment")


def fig_profile(out):
    """FL02 - the two profiles side by side: as drawn, and on the alignment found here."""
    prof = np.load(CACHE / "w3_prof.npy")
    ch, grd, inv, cov = prof
    tr = fk.read_layer("W11a_trunk.gpkg", "reaches")
    tn = fk.read_layer("W11a_trunk.gpkg", "nodes").set_index("NODE_UID")
    stn = fk.read_csv("s3_trunk_stations.csv")
    dr = out["drawn"]

    fig, axes = fk.chart_frame(
        title="The trunk leaves the west uphill; the ground offers a way out that does not",
        subtitle=("Left: the western leg as drawn, on stage 3's published levels. Right: "
                  "one gravity run from the west low point to the existing works, DN%d at "
                  "%.3f %%. Cover window 1.30-12.00 m (H3/H4, G203-p33)."
                  % (DN, SLOPE * 100)),
        figsize=(13.4, 6.4), ncols=2)

    # ---- left: the west leg as drawn, each gravity run walked downstream from its head
    ax = axes[0]
    ds = dict(zip(tr.US_NODE, tr.DS_NODE))
    wt = trunk_west_nodes(tr, tn.reset_index())
    heads = [n for n in wt if int(tn.loc[n, "N_IN"]) == 0]
    seq, seen = [], set()
    for s0 in sorted(heads, key=lambda n: tn.loc[n, "X"]):
        u, run = s0, []
        while u in wt and u not in seen:
            seen.add(u)
            run.append(u)
            u = ds.get(u)
        if len(run) > 1:
            seq.append(run)
    seq.sort(key=lambda r: tn.loc[r[0], "X"])
    off, marks = 0.0, []
    for k, run in enumerate(seq[:2]):
        g = [float(tn.loc[n, "GRD_M"]) for n in run]
        iv = [float(tn.loc[n, "INV_M"]) for n in run]
        x = [0.0]
        for i in range(1, len(run)):
            a, b = tn.loc[run[i - 1]], tn.loc[run[i]]
            x.append(x[-1] + float(np.hypot(b.X - a.X, b.Y - a.Y)))
        x = np.array(x) + off
        ax.fill_between(x / 1000, g, min(iv) - 8, color="#efece6", zorder=1)
        ax.plot(x / 1000, g, color=fk.C.INK, lw=1.5, zorder=4,
                label="ground (0.5 m terrain)" if k == 0 else None)
        ax.plot(x / 1000, iv, color=fk.C.TRUNK, lw=2.0, zorder=5,
                label="invert, as laid by stage 3" if k == 0 else None)
        marks.append((x[0] / 1000, iv[0], x[-1] / 1000, iv[-1]))
        off = x[-1] + 300
    lifts = dr["lifts"]
    for i in range(len(marks)):
        _sx, _si, ex, ei = marks[i]
        if i + 1 < len(marks):
            nx, ni = marks[i + 1][0], marks[i + 1][1]
            ax.annotate("", xy=(nx, ni), xytext=(ex, ei), zorder=8,
                        arrowprops=dict(arrowstyle="-|>", color=fk.C.STATION, lw=1.9,
                                        shrinkA=0, shrinkB=0,
                                        connectionstyle="arc3,rad=-0.30"))
        if i < len(lifts):
            ax.scatter([ex], [ei], s=100, marker="v", facecolor=fk.C.STATION,
                       edgecolor="white", linewidth=1.0, zorder=9)
            ax.annotate("lifting station\n+%.2f m" % lifts[i], (ex, ei),
                        xytext=(-8, 30), textcoords="offset points", fontsize=7.4,
                        ha="right", color=fk.C.STATION, zorder=10)
    ax.set_xlabel("chainage along the western leg (km; the two gravity runs, west to east)")
    ax.set_ylabel("level (m aOD)")
    ax.text(0.0, 1.022, "AS DRAWN  -  east, over two lifts", transform=ax.transAxes,
            fontsize=9.6, fontweight="bold", va="bottom", color=fk.C.GREY)
    y0, y1 = ax.get_ylim()
    ax.set_ylim(y0 - 0.42 * (y1 - y0), y1)
    ax.legend(loc="upper right", frameon=False, fontsize=7.4)
    ax.text(0.012, 0.030,
            "gravity %.2f km, deepest cover %.2f m\n"
            "%d lifting stations, %.2f m of static lift, %.0f m of rising main\n"
            "%s kWh/yr of static-lift energy\n"
            "   (eta %.2f ASSUMED; friction excluded - no pump duty exists yet)\n"
            "%.0f m of the run is the OPEN S3-1 provisional line"
            % (dr["gravity_km"], dr["cover_max"], dr["n_station"], dr["lift_sum"],
               dr["rm_m"], f"{dr['kwh_yr']:,.0f}", PUMP_ETA, out["gap"]["straight_m"]),
            transform=ax.transAxes, ha="left", va="bottom", fontsize=7.0,
            color=fk.C.INK, family="monospace",
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a", alpha=0.95))

    # ---- right: the gravity alignment found here
    ax = axes[1]
    ax.fill_between(ch / 1000, grd, inv.min() - 10, color="#efece6", zorder=1)
    ax.plot(ch / 1000, grd, color=fk.C.INK, lw=1.5, zorder=4,
            label="ground (0.5 m terrain)")
    ax.plot(ch / 1000, grd - COVER_MIN - OD_ALLOW, color=fk.C.GREY, lw=0.9, ls=":",
            zorder=3, label="shallowest legal invert - 1.30 m cover (H3, G203-p33)")
    ax.plot(ch / 1000, grd - COVER_CAP - OD_ALLOW, color=fk.C.FLAG, lw=1.1, ls="--",
            zorder=3, label="deepest legal invert - 12.00 m cap (H4, G203-p33)")
    ax.plot(ch / 1000, inv, color=fk.C.FAIL, lw=2.2, zorder=5,
            label="invert as designed - DN%d at %.3f %%" % (DN, SLOPE * 100))
    ax.set_xlabel("chainage from the west basin low point (km)")
    ax.set_ylabel("level (m aOD)")
    ax.text(0.0, 1.022, "MEASURED HERE  -  south, on gravity alone",
            transform=ax.transAxes, fontsize=9.6, fontweight="bold", va="bottom",
            color=fk.C.GREY)
    y0, y1 = ax.get_ylim()
    ax.set_ylim(y0 - 0.22 * (y1 - y0), y1)
    ax.legend(loc="upper right", frameon=False, fontsize=7.4)
    d, l3 = out["w3"]["dem"], out["w3"]
    ax.text(0.012, 0.030,
            "%.3f km, ZERO lifting stations\n"
            "invert %.2f -> %.2f m aOD\n"
            "cover %.2f -> %.2f m, deepest %.2f m\n"
            "re-read on the raw 0.5 m grid: %.2f - %.2f m,\n"
            "   %d of %d points past the cap\n"
            "NOT ON A CORRIDOR - %.0f %% of it is over 50 m from one.\n"
            "   A new wayleave, not a street."
            % (l3["len_km"], inv[0], inv[-1], cov[0], cov[-1], cov.max(),
               d["cover_min"], d["cover_max"], d["past_cap"], d["n"],
               l3["off_corridor_pct"]),
            transform=ax.transAxes, ha="left", va="bottom", fontsize=7.0,
            color=fk.C.INK, family="monospace",
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a", alpha=0.95))
    fk.finish_chart(fig, source=fk.source_line(
        tr, stn, "Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt (0.5 m terrain)"))
    return fk.save(fig, "FL02_west_profiles")


def fig_lift(out):
    """FL03 - the load against the lift it needs: the ground's answer vs the streets'."""
    rows = out["lift"]["by_load"]
    labs = ["none", "0-2 m", "2-5 m", "5-10 m", "10-20 m", "over 20 m"]
    qt = [r["q_terr"] for r in rows]
    qc = [r["q_corr"] for r in rows]
    y = np.arange(len(labs))
    fig, ax = fk.chart_frame(
        title="The west's gravity problem is in the corridor layer, not in the ground",
        subtitle=("Ultimate average dry-weather flow in the west catchment, grouped by the "
                  "minimum static lift needed to reach the existing works. The lift is the "
                  "bottleneck elevation minus the plot's own ground - a floor no gradient, "
                  "diameter or alignment can beat. Measured twice on the same plots: over "
                  "the 0.5 m terrain, and over stage 2's published corridors."),
        figsize=(9.8, 5.0))
    ax.barh(y + 0.20, qt, height=0.38, **fk.status_style("pass"))
    ax.barh(y - 0.20, qc, height=0.38, **fk.status_style("fail"))
    ax.set_yticks(y, labs)
    ax.invert_yaxis()
    ax.set_xlabel("ultimate Qadf (m3/d)")
    ax.set_ylabel("minimum static lift to the existing works")
    fk.thousands(ax, "x")
    for i, (a, b) in enumerate(zip(qt, qc)):
        if a > 30:
            ax.text(a + 55, i + 0.20, f"{a:,.0f}", va="center", fontsize=7.2,
                    color=fk.C.INK)
        if b > 30:
            ax.text(b + 55, i - 0.20, f"{b:,.0f}", va="center", fontsize=7.2,
                    color=fk.C.INK)
    ax.set_xlim(0, max(max(qt), max(qc)) * 1.32)
    c = out["catch"]
    ax.text(0.985, 0.06,
            "west catchment %s m3/d over %s plots\n"
            "GROUND    : %.0f %% needs no lift at all, %.0f %% needs 2 m or less\n"
            "CORRIDORS : %.0f %% needs no lift; the network adds a median %.2f m\n"
            "corridor tearing in the west: median detour %.2f x between neighbours\n"
            "   300-800 m apart, %.0f %% of pairs over 3 x, %.0f %% unreachable in 8 km"
            % (f"{c['q']:,.0f}", f"{c['plots']:,}", 100 * qt[0] / c["q"],
               100 * (qt[0] + qt[1]) / c["q"], 100 * qc[0] / c["q"],
               out["lift"]["penalty_med"], out["tear"]["med"], out["tear"]["over3"],
               out["tear"]["unreach"]),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.2,
            family="monospace", color=fk.C.INK,
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a", alpha=0.95))
    fk.legend_below(ax, [Patch(label="what the GROUND demands", **fk.status_style("pass")),
                         Patch(label="what the CORRIDOR NETWORK demands",
                               **fk.status_style("fail"))], ncol=2, drop=0.30)
    fk.finish_chart(fig, source=("Source: " + out["src"]["cor"] + "  .  "
                                 + out["src"]["pl"]
                                 + "  .  Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt"))
    return fk.save(fig, "FL03_west_lift")


# ==========================================================================================

def report(out):
    c, l3, gp, dr, lf, te = (out["catch"], out["w3"], out["gap"], out["drawn"],
                             out["lift"], out["tear"])
    p = print
    p("\n=== WEST CATCHMENT =========================================================")
    p(f"  corridor-graph catchment : {c['plots']:,} plots, {c['prop']:,.0f} properties, "
      f"{c['q']:,.1f} m3/d ({100*c['q']/c['q_total']:.2f} % of {c['q_total']:,.1f})")
    p(f"  stage 3's own assignment : {c['s3_q']:,.1f} m3/d, {c['s3_qpk']:.1f} L/s peak, "
      f"{c['s3_prop']:,.0f} properties (PF {c['s3_pf']:.3f}, DN{c['s3_dn']})")
    p(f"  corridor                 : {c['corridor_km']:,.1f} km of "
      f"{c['corridor_km_total']:,.1f} ; {c['m_per_prop']:.1f} m/property vs "
      f"{c['m_per_prop_net']:.1f} network-wide")
    p("\n=== MINIMUM STATIC LIFT TO THE EXISTING WORKS ==============================")
    p(f"  {lf['n']} west corridor nodes")
    p(f"  GROUND   : zero lift on {lf['terr_zero']} ({100*lf['terr_zero']/lf['n']:.1f} %), "
      f"median {lf['terr_med']:.2f} m, p90 {lf['terr_p90']:.2f} m, "
      f"max {lf['terr_max']:.2f} m")
    p(f"  CORRIDORS: zero lift on {lf['corr_zero']} ({100*lf['corr_zero']/lf['n']:.1f} %), "
      f"median {lf['corr_med']:.2f} m, p90 {lf['corr_p90']:.2f} m, "
      f"max {lf['corr_max']:.2f} m")
    p(f"  the corridor network adds a median {lf['penalty_med']:.2f} m over the ground")
    p(f"  corridor tearing, west: median detour {te['med']:.2f}x between neighbours "
      f"300-800 m apart, {te['over3']:.0f} % over 3x, {te['unreach']:.0f} % unreachable "
      f"inside 8 km ({te['n']} pairs)")
    p(f"  worst named case: two nodes {te['worst_straight_m']:,.0f} m apart need "
      f"{te['worst_corridor_m']:,.0f} m of corridor "
      f"({te['worst_corridor_m']/te['worst_straight_m']:.1f}x)")
    p("\n=== A GRAVITY ALIGNMENT EXISTS =============================================")
    p(f"  {l3['len_km']:.3f} km, DN{DN} at {SLOPE*100:.3f} %, "
      f"west low point -> existing works")
    p(f"  invert {l3['inv_start']:.2f} -> {l3['inv_end']:.2f} m aOD ; cover "
      f"{l3['start_cover']:.2f} -> {l3['cover_end']:.2f} m, deepest {l3['cover_max']:.2f} m")
    d = l3["dem"]
    p(f"  re-read on the RAW 0.5 m grid: cover {d['cover_min']:.2f} - "
      f"{d['cover_max']:.2f} m, {d['below_min']} of {d['n']} points under 1.30 m, "
      f"{d['past_cap']} past 12.00 m")
    p(f"  hazard grid UNTESTED on {l3['hz_untested_pct']:.1f} % ; of the tested part "
      f"{l3['hz_wadi_pct']:.1f} % is class >= 4 (a PROJECT assumption, not a guideline)")
    p(f"  mapped streams a median {l3['stream_med_m']:.0f} m away ; "
      f"{l3['stream_within25_pct']:.1f} % of it within 25 m")
    p(f"  NOT a corridor: median {l3['corr_med_m']:.0f} m from one, max "
      f"{l3['corr_max_m']:.0f} m, {l3['off_corridor_pct']:.0f} % over 50 m ; crosses "
      f"{l3['plots_crossed']} registered plots")
    p(f"  dual carriageway: {l3.get('dual_crossings','?')} centreline crossings, "
      f"{l3.get('dual_band_samples','?')} of the 10 m samples inside the 6 m band "
      f"(rule 7 allows a crossing, never a run along)")
    p("\n=== OPEN S3-1, FROM THE DRAWING ITSELF =====================================")
    p(f"  {gp['n_polylines']} polylines, {gp['total_km']:.3f} km. The western leg is "
      f"{gp['leg_len_m']:,.2f} m")
    p(f"  its end is {gp['end_to_rest_m']:.2f} m from the rest of the drawing; the whole "
      f"line's closest approach is {gp['closest_approach_m']:.2f} m")
    p(f"  shortest route across it ON REAL STREET CORRIDORS: "
      f"{gp['corridor_route_m']:,.2f} m "
      f"({gp['corridor_route_m']/gp['straight_m']:.2f}x the straight line), rising to "
      f"{gp['corridor_route_zmax']:.2f} m")
    p(f"  that route: {gp['street_share_pct']:.0f} % built street, {gp['on_wadi_m']:.1f} m "
      f"on wadi ground, {gp['on_dual_m']:.1f} m on a dual carriageway")
    p("\n=== THE WEST AS DRAWN ======================================================")
    p(f"  {dr['gravity_km']:.3f} km of gravity ({dr['prov_km']:.3f} km of it provisional), "
      f"deepest cover {dr['cover_max']:.2f} m")
    p(f"  {dr['n_station']} lifting stations, {dr['lift_sum']:.2f} m of static lift, "
      f"{dr['rm_m']:.0f} m of rising main")
    p(f"  {dr['kwh_yr']:,.0f} kWh/yr of static-lift energy at eta {PUMP_ETA} (ASSUMED; "
      f"friction excluded - no pump duty exists yet)")


def main(argv):
    if "--figs" in argv and (CACHE / "out.json").exists():
        out = load_cache()
    else:
        out = measure()
    report(out)
    for f in (fig_catchment, fig_profile, fig_lift):
        print("  wrote", f(out))


if __name__ == "__main__":
    main(sys.argv[1:])
