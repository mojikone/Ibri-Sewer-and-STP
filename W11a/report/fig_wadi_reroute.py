"""fig_wadi_reroute — the figures for `W11a/docs/WADI_CORRIDOR_REROUTE.md`.

WHAT THIS MODULE ARGUES, IN ONE LINE
The along/across test that stage 2 and `audit.r4` both apply measures the hazard band
PERPENDICULAR TO THE PIPE.  Philosophy H1a item 1 says the contact must be within the
skew tolerance of *"the shortest crossing available at that point"*.  Those are not the
same measurement, and on the published corridors they disagree by 72 km.

EVERY NUMBER IS MEASURED HERE, from artefacts, at draw time:
  * `W11a/shp/W11a.gpkg` [corridors]        — read through `figkit.read_layer` (a COPY)
  * `Data/04 Lekhuwair/Hazard_T50y.tif`     — the 50-year AR&R flood-hazard grid
  * `W10/shp/W10_plot_loads.gpkg`           — Q_AVG_M3D, the project's only load field
Nothing is read from a manifest and nothing is typed in from a previous run.  The cached
arrays under `figkit.SCRATCH` are derived products of the two rasters and are rebuilt
whenever they are missing.

THE ONE PROJECT TOLERANCE ON THE FIGURES, LABELLED AS OURS
`WADI_XING_SKEW = 1.155` (= 1/cos 30°) is `audit.WADI_XING_SKEW`, a PROJECT tolerance on
H1's word "perpendicular" — declared in the philosophy, not quoted from a guideline.  So
is `HAZARD_WADI_CLASSES = (4, 5, 6)`, which is a flood-SAFETY classification standing in
for G203-p30 4.4.1's *"areas subject to washout"*, a SCOUR criterion.  Both are captioned
as project assumptions on every figure that uses them.  The guideline values that DO
appear are quoted with their page: G203-p29 Table 11 (DN200 = 5.00 mm/m), G203-p30
4.4.1(i)(a) and G203-p33 4.6.2 (wadis "must be"/"shall be avoided"), G203-p32 Table 13
(DN200-500 corridor width 2.00 m).

Run:  python fig_wadi_reroute.py            (draws FR01..FR04 into report/img)
      python fig_wadi_reroute.py --numbers  (prints the measurement table only)
      python fig_wadi_reroute.py --patch    (also simulates the proposed s2 patch:
                                             delete the ALONG set, heal the severances,
                                             and report what is recovered)
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import figkit as fk                                        # noqa: E402
import geopandas as gpd                                    # noqa: E402
import networkx as nx                                      # noqa: E402
import rasterio                                            # noqa: E402
import shapely                                             # noqa: E402
from matplotlib.lines import Line2D                        # noqa: E402
from matplotlib.patches import Patch                       # noqa: E402
from rasterio.windows import Window, from_bounds           # noqa: E402
from scipy import ndimage                                  # noqa: E402
from scipy.sparse import coo_matrix                        # noqa: E402
from scipy.sparse.csgraph import connected_components      # noqa: E402
from shapely.geometry import LineString                    # noqa: E402
from shapely.ops import nearest_points, unary_union        # noqa: E402

# ----------------------------------------------------------------- the constants,
# every one lifted from a named source, none chosen here
WADI_SAMPLE_M = 1.5        # audit.WADI_SAMPLE_M   — half the grid's 3.0 m cell
WADI_XING_SKEW = 1.155     # audit.WADI_XING_SKEW  — PROJECT tolerance, 1/cos(30 deg)
WADI_PROBE_M = 400.0       # audit.WADI_PROBE_M
WADI_CLASSES = (4, 5, 6)   # criteria.HAZARD_WADI_CLASSES — a PROJECT assumption
PLOT_SERVED_M = 60.0       # s2_corridors.PLOT_SERVED_M
TABLE11_DN200 = 0.00500    # criteria.TABLE11[200] -> G203-p29 Table 11, 5.00 mm/m
NODE_MERGE_M = 3.0         # contract.NODE_MERGE_M / criteria.MH_SNAP_M

PLOT_LOADS = fk.ROOT / "W10" / "shp" / "W10_plot_loads.gpkg"
CACHE = fk.SCRATCH / "reroute"


# ===================================================================== the hazard grid

class Haz:
    """The 50-year hazard grid over an extent, with BOTH masks and a distance field.

    `wadi`  hazard class >= 4 on a cell that HAS data
    `known` the cell has data at all.  nodata is -9999.0 and np.isfinite(-9999.0) is
            True, so `known` cannot come from a finiteness test — the same trap
            `figkit.hazard_coverage` documents.
    `dist`  metres to the nearest KNOWN NON-WADI cell.  This is what H1a item 1's
            "shortest crossing available at that point" needs and what the
            perpendicular probe does not measure.
    """

    def __init__(self, bounds, pad=600.0, strip=2000):
        l, b, r, t = bounds
        ds = rasterio.open(fk.HAZARD)
        win = from_bounds(l - pad, b - pad, r + pad, t + pad, ds.transform)
        win = win.round_offsets().round_lengths()
        self.tr = ds.window_transform(win)
        h, w = int(win.height), int(win.width)
        self.h, self.w, self.cell = h, w, abs(self.tr.a)
        self.wadi = np.zeros((h, w), bool)
        self.known = np.zeros((h, w), bool)
        lo = min(WADI_CLASSES) - 0.5
        nod = ds.nodata
        for r0 in range(0, h, strip):
            r1 = min(h, r0 + strip)
            a = ds.read(1, window=Window(win.col_off, win.row_off + r0, w, r1 - r0))
            k = np.isfinite(a) & (a != nod) & (a > -1000.0)
            self.known[r0:r1] = k
            self.wadi[r0:r1] = k & (a > lo)
        ds.close()
        self.dist = self._dist_to_dry()

    def _dist_to_dry(self, halo_m=500.0, strip=2000):
        dry = self.known & ~self.wadi
        halo = int(halo_m / self.cell)
        out = np.full((self.h, self.w), np.inf, np.float32)
        for r0 in range(0, self.h, strip):
            r1 = min(self.h, r0 + strip)
            a, b = max(0, r0 - halo), min(self.h, r1 + halo)
            sub = dry[a:b]
            d = (ndimage.distance_transform_edt(~sub, sampling=self.cell)
                 if sub.any() else np.full(sub.shape, np.inf))
            out[r0:r1] = d[r0 - a:r1 - a]
        return out

    def _rc(self, xs, ys):
        col = ((np.asarray(xs, float) - self.tr.c) / self.tr.a).astype(np.int64)
        row = ((np.asarray(ys, float) - self.tr.f) / self.tr.e).astype(np.int64)
        ok = (row >= 0) & (col >= 0) & (row < self.h) & (col < self.w)
        return row, col, ok

    def at(self, xs, ys):
        """(on_wadi, known).  Off the grid is UNKNOWN, never dry."""
        row, col, ok = self._rc(xs, ys)
        n = len(np.atleast_1d(col))
        on = np.zeros(n, bool); kn = np.zeros(n, bool)
        if ok.any():
            on[ok] = self.wadi[row[ok], col[ok]]
            kn[ok] = self.known[row[ok], col[ok]]
        return on, kn

    def d_dry(self, xs, ys):
        row, col, ok = self._rc(xs, ys)
        out = np.full(len(np.atleast_1d(col)), np.inf)
        if ok.any():
            out[ok] = self.dist[row[ok], col[ok]]
        return out


def _sample(g, step=WADI_SAMPLE_M):
    L = g.length
    n = max(2, int(math.ceil(L / step)) + 1)
    d = np.linspace(0.0, L, n)
    xy = shapely.get_coordinates(shapely.line_interpolate_point(g, d))
    return d, xy[:, 0], xy[:, 1]


def _runs(flag, d):
    out, a = [], None
    for k, f in enumerate(flag):
        if f and a is None:
            a = k
        elif not f and a is not None:
            out.append((float(d[a]), float(d[k - 1]), a, k - 1)); a = None
    if a is not None:
        out.append((float(d[a]), float(d[-1]), a, len(flag) - 1))
    return out


def _probe_width(g, haz, mid_ch):
    """The band width ACROSS the pipe — what s2._square_crossing and audit._r4_classify
    actually measure.  Unknown ground scores DRY here, exactly as `s2.WadiMask.at` has
    it, so the reproduction is of the code as written and not of a corrected version."""
    L = g.length
    p0 = g.interpolate(max(0.0, mid_ch - 1.0)); p1 = g.interpolate(min(L, mid_ch + 1.0))
    vx, vy = p1.x - p0.x, p1.y - p0.y
    m = math.hypot(vx, vy) or 1.0
    nx_, ny_ = -vy / m, vx / m
    c = g.interpolate(mid_ch)
    ts = np.arange(0.0, WADI_PROBE_M, WADI_SAMPLE_M)
    width, capped = 0.0, False
    for sgn in (1.0, -1.0):
        on, kn = haz.at(c.x + sgn * ts * nx_, c.y + sgn * ts * ny_)
        off = np.where(~on)[0]
        if len(off):
            width += float(off[0] * WADI_SAMPLE_M)
        else:
            width += WADI_PROBE_M; capped = True
    return width, capped


# ===================================================================== the measurement

def measure(force=False):
    """Everything the figures and the document quote.  Returns a dict of frames."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cor = fk.read_layer("W11a.gpkg", "corridors")
    src_cor = fk.cite(cor)
    haz = Haz(cor.total_bounds)

    # ---- coverage over the WHOLE corridor set, sample level ---------------------------
    tot = unk = 0
    for g in cor.geometry.values:
        d, xs, ys = _sample(g)
        on, kn = haz.at(xs, ys)
        tot += len(d); unk += int((~kn).sum())
    cover = dict(samples=tot, unknown=unk, pct_unknown=100.0 * unk / max(tot, 1))

    # ---- one row per contiguous on-wadi run -------------------------------------------
    rows = []
    for r in cor[cor.ON_WADI_M > 0].itertuples():
        g = r.geometry
        d, xs, ys = _sample(g)
        on, kn = haz.at(xs, ys)
        dd = haz.d_dry(xs, ys)
        for k, (a, b, i0, i1) in enumerate(_runs(on, d)):
            contact = (b - a) + WADI_SAMPLE_M
            # THE STATISTIC IS THE MAXIMUM, and this is not a taste.  On a perfect
            # perpendicular crossing of a band of width W the distance to dry ground ramps
            # 0 -> W/2 -> 0 along the pipe, so 2 x MEDIAN recovers W/2 and 2 x MAX recovers
            # W.  With the median, skew = contact / (W/2) = 2.00 on a PERFECT crossing -
            # over the 1.155 tolerance - and every square crossing in the network is
            # condemned.  With the max, skew = 1/cos(deviation) exactly, so 1.155 means
            # 30 deg off square, which is what audit.WADI_XING_SKEW is defined to be.
            # Measured on the published layers, the choice is worth 24.64 km: median
            # flags 1,008 runs / 71.78 km, max flags 561 / 47.27 km, and the max set is a
            # strict subset of the median set.
            seg = dd[i0:i1 + 1]; seg = seg[np.isfinite(seg)]
            med = float(np.median(seg)) if seg.size else np.nan
            mx = float(seg.max()) if seg.size else np.nan
            wpr, cap = _probe_width(g, haz, 0.5 * (a + b))
            c = g.interpolate(0.5 * (a + b))
            rows.append(dict(CORR_ID=r.CORR_ID, SRC=r.SRC, CONFIDENCE=r.CONFIDENCE,
                             LEN_M=r.LEN_M, N_PLOT=r.N_PLOT, US_NODE=r.US_NODE,
                             DS_NODE=r.DS_NODE, CONTACT_M=contact, MID_X=c.x, MID_Y=c.y,
                             W_PROBE_M=wpr, PROBE_CAPPED=cap,
                             SKEW_PROBE=contact / max(wpr, WADI_SAMPLE_M),
                             D_DRY_MED=med, D_DRY_MAX=mx,
                             XING_M=2.0 * mx if np.isfinite(mx) else np.nan,
                             SKEW_MED=(contact / (2.0 * med)
                                       if (np.isfinite(med) and med > 0) else np.inf),
                             SKEW_H1A=(contact / (2.0 * mx)
                                       if (np.isfinite(mx) and mx > 0) else np.inf)))
    R = pd.DataFrame(rows)
    R["ALONG"] = R.SKEW_H1A > WADI_XING_SKEW
    along_ids = set(R.loc[R.ALONG, "CORR_ID"])
    cor["ALONG"] = cor.CORR_ID.isin(along_ids)

    # ---- chains ------------------------------------------------------------------------
    GA = nx.Graph()
    for r in cor[cor.ALONG].itertuples():
        GA.add_edge(r.US_NODE, r.DS_NODE)
    cid = {}
    for k, cc in enumerate(nx.connected_components(GA)):
        for n in cc:
            cid[n] = k
    cor["CHAIN"] = np.where(cor.ALONG, cor.US_NODE.map(cid), -1)
    n_chain = int(cor.CHAIN.max()) + 1

    # ---- load pinned to its nearest corridor ------------------------------------------
    pl = fk.read_layer(str(PLOT_LOADS), "plot_loads", columns=["Q_AVG_M3D"])
    src_pl = fk.cite(pl)
    pl["Q"] = pd.to_numeric(pl.Q_AVG_M3D, errors="coerce").fillna(0.0)
    lb = pl[pl.Q > 0][["Q", "geometry"]]
    j = gpd.sjoin_nearest(lb, cor[["CORR_ID", "geometry"]], how="left",
                          max_distance=PLOT_SERVED_M, distance_col="D")
    j = j[~j.index.duplicated(keep="first")]
    q_total = float(pl.Q.sum())
    emap = pd.Series(np.arange(len(cor)), index=cor.CORR_ID)
    load_edge = np.zeros(len(cor))
    hit = j.CORR_ID.notna()
    np.add.at(load_edge, emap.reindex(j.loc[hit, "CORR_ID"]).values.astype(int),
              j.loc[hit, "Q"].values)

    # ---- trunk connectivity, with and without the ALONG set ---------------------------
    nodes = pd.Index(sorted(set(cor.US_NODE) | set(cor.DS_NODE)))
    u = nodes.get_indexer(cor.US_NODE); v = nodes.get_indexer(cor.DS_NODE); N = len(nodes)
    trunk_edge = (cor.SRC == "main_pipe").values

    def trunk_load(mask):
        A = coo_matrix((np.ones(int(mask.sum())), (u[mask], v[mask])), shape=(N, N))
        nc, lab = connected_components(A, directed=False)
        ec = lab[u[mask]]
        good = set(ec[trunk_edge[mask]])
        keep = np.isin(ec, list(good))
        # nc counts every node in the published node set, so a node left with no corridor
        # at all counts as a component of one.  `live` counts only the pieces that still
        # carry a corridor, which is the number a person means by "the network is in N
        # pieces".  Both are reported; they differ and the difference is not a defect.
        live = len(set(ec) | set(lab[v[mask]]))
        return float(load_edge[mask][keep].sum()), nc, live, lab

    base_q, base_nc, base_live, _ = trunk_load(np.ones(len(cor), bool))
    keep_mask = ~cor.ALONG.values
    kept_q, kept_nc, kept_live, kept_lab = trunk_load(keep_mask)

    # ---- marginal cost of each chain --------------------------------------------------
    mrows = []
    for c in range(n_chain):
        m = ~(cor.CHAIN.values == c)
        q, nc, _lv, _ = trunk_load(m)
        e = cor[cor.CHAIN == c]
        cen = e.geometry.iloc[0].interpolate(0.5, normalized=True)
        mrows.append(dict(CHAIN=c, N_EDGES=len(e), KM=e.LEN_M.sum() / 1000,
                          SRC=e.SRC.mode().iat[0], X=cen.x, Y=cen.y,
                          N_PLOT=int(e.N_PLOT.sum()), MARGINAL_M3D=base_q - q))
    M = pd.DataFrame(mrows)
    con = R[R.ALONG].groupby("CORR_ID").CONTACT_M.sum()
    cor["CONTACT_M"] = cor.CORR_ID.map(con).fillna(0.0)
    M = M.merge(cor[cor.ALONG].groupby("CHAIN")
                .agg(CONTACT_KM=("CONTACT_M", lambda s: s.sum() / 1000)).reset_index(),
                on="CHAIN", how="left")

    # ---- can each severance be healed by a short link? --------------------------------
    hrows = []
    for r in M[M.MARGINAL_M3D > 0].itertuples():
        m = ~(cor.CHAIN.values == r.CHAIN)
        _q, _nc, _lv, lab = trunk_load(m)
        s = cor[m].copy(); s["CMP"] = lab[u[m]]
        good = set(s.loc[s.SRC == "main_pipe", "CMP"])
        s["TRUNKED"] = s.CMP.isin(good)
        ch = cor[cor.CHAIN == r.CHAIN]
        ends = nodes.get_indexer(list(set(ch.US_NODE) | set(ch.DS_NODE)))
        orph = [c for c in set(lab[ends]) if c not in good]
        if not orph:
            hrows.append(dict(CHAIN=r.CHAIN, HEAL="nothing orphaned", GAP_M=np.nan,
                              CONTACT_M=np.nan, LX0=np.nan, LY0=np.nan,
                              LX1=np.nan, LY1=np.nan)); continue
        A_g = unary_union(s.loc[s.CMP.isin(orph), "geometry"].values)
        near = s[s.TRUNKED & s.intersects(A_g.buffer(1500.0))]
        if not len(near):
            hrows.append(dict(CHAIN=r.CHAIN, HEAL="no trunk-connected corridor within 1.5 km",
                              GAP_M=np.inf, CONTACT_M=np.nan, LX0=np.nan, LY0=np.nan,
                              LX1=np.nan, LY1=np.nan)); continue
        p, q2 = nearest_points(A_g, unary_union(near.geometry.values))
        link = LineString([(p.x, p.y), (q2.x, q2.y)])
        gap = link.length
        if gap < 0.5:
            lab_ = "already touching (a noding gap)"
            ct = 0.0
        else:
            d, xs, ys = _sample(link)
            on, kn = haz.at(xs, ys)
            ct = float(on.sum()) / max(len(on), 1) * gap
            mid = link.interpolate(0.5, normalized=True)
            dd = float(haz.d_dry([mid.x], [mid.y])[0])
            xing = 2.0 * dd if np.isfinite(dd) else np.inf
            lab_ = ("clear of the wadi" if ct <= 1e-6 else
                    ("square crossing" if ct <= WADI_XING_SKEW * max(xing, WADI_SAMPLE_M)
                     else "still along a wadi"))
        hrows.append(dict(CHAIN=r.CHAIN, HEAL=lab_, GAP_M=gap, CONTACT_M=ct,
                          LX0=link.coords[0][0], LY0=link.coords[0][1],
                          LX1=link.coords[1][0], LY1=link.coords[1][1]))
    H = pd.DataFrame(hrows).merge(M, on="CHAIN", how="left")

    # ---- the street-network detour, for completeness ----------------------------------
    Gk = nx.MultiGraph()
    for r in cor[~cor.ALONG].itertuples():
        Gk.add_edge(r.US_NODE, r.DS_NODE, key=r.CORR_ID, weight=float(r.LEN_M))
    Gk.add_nodes_from(set(cor.US_NODE) | set(cor.DS_NODE))
    kc = {}
    for k, cc in enumerate(nx.connected_components(Gk)):
        for n in cc:
            kc[n] = k
    det = []
    for r in cor[cor.ALONG].itertuples():
        if r.US_NODE == r.DS_NODE or kc.get(r.US_NODE) != kc.get(r.DS_NODE):
            det.append(np.inf); continue
        det.append(nx.shortest_path_length(Gk, r.US_NODE, r.DS_NODE, weight="weight"))
    DET = pd.DataFrame(dict(CORR_ID=cor.loc[cor.ALONG, "CORR_ID"].values,
                            LEN_M=cor.loc[cor.ALONG, "LEN_M"].values,
                            ALT_M=det))
    DET["EXTRA_M"] = DET.ALT_M - DET.LEN_M
    DET["EXTRA_DEPTH_M"] = DET.EXTRA_M * TABLE11_DN200

    # hazard class under each ALONG contact, read from the raster itself
    with rasterio.open(fk.HAZARD) as _src:
        _v = np.array([w[0] for w in _src.sample(zip(R.MID_X.values, R.MID_Y.values))],
                      float)
    R["HAZ_CLASS"] = np.floor(_v)
    haz_class = {int(c): (int((R.ALONG & (R.HAZ_CLASS == c)).sum()),
                          float(R.loc[R.ALONG & (R.HAZ_CLASS == c), "CONTACT_M"].sum()))
                 for c in sorted(R.loc[R.ALONG, "HAZ_CLASS"].dropna().unique())}

    # frontage: what loses every corridor within PLOT_SERVED_M if the ALONG set goes
    j2 = gpd.sjoin_nearest(lb, cor.loc[~cor.ALONG, ["CORR_ID", "geometry"]], how="left",
                           max_distance=PLOT_SERVED_M, distance_col="D")
    j2 = j2[~j2.index.duplicated(keep="first")]
    b_ok = j.CORR_ID.notna(); a_ok = j2.CORR_ID.notna()
    lost = b_ok & ~a_ok
    front = b_ok & j.CORR_ID.isin(along_ids)

    out = dict(cor=cor, R=R, M=M, H=H, DET=DET, haz=haz, cover=cover,
               haz_class=haz_class, lb=lb, load_edge=load_edge,
               lost_plots=int(lost.sum()), lost_q=float(j.loc[lost, "Q"].sum()),
               front_plots=int(front.sum()),
               front_p50=float(j2.loc[front, "D"].median()),
               base_q=base_q, base_nc=base_nc, base_live=base_live,
               kept_q=kept_q, kept_nc=kept_nc, kept_live=kept_live,
               q_total=q_total, src_cor=src_cor, src_pl=src_pl)
    return out


# ===================================================================== the numbers

def numbers(D):
    R, M, H, DET, cor = D["R"], D["M"], D["H"], D["DET"], D["cor"]
    A = R[R.ALONG]
    L = []
    p = L.append
    p("CORRIDORS            %8d   %10.2f km" % (len(cor), cor.LEN_M.sum() / 1000))
    p("  hazard samples     %8d   %9.2f %% UNTESTED (nodata or off the grid)"
      % (D["cover"]["samples"], D["cover"]["pct_unknown"]))
    p("  touching wadi      %8d   %10.2f km of contact over %d contiguous runs"
      % (int((cor.ON_WADI_M > 0).sum()), R.CONTACT_M.sum() / 1000, len(R)))
    p("")
    p("ALONG / ACROSS, the two tests")
    p("  perpendicular probe (what s2 and audit.r4 apply): %d of %d runs fail, %.3f km"
      % (int((R.SKEW_PROBE > WADI_XING_SKEW).sum()), len(R),
         R.loc[R.SKEW_PROBE > WADI_XING_SKEW, "CONTACT_M"].sum() / 1000))
    p("  shortest crossing available (H1a item 1 as written): %d of %d runs fail, %.2f km"
      % (len(A), len(R), A.CONTACT_M.sum() / 1000))
    p("  probe hit its %.0f m cap on %d runs" % (WADI_PROBE_M, int(R.PROBE_CAPPED.sum())))
    p("  the same clause with 2 x MEDIAN instead of 2 x MAX (WRONG - it scores a perfect "
      "crossing at 2.00): %d runs, %.2f km"
      % (int((R.SKEW_MED > WADI_XING_SKEW).sum()),
         R.loc[R.SKEW_MED > WADI_XING_SKEW, "CONTACT_M"].sum() / 1000))
    p("  sensitivity of the ALONG set to the skew tolerance:")
    for t in (1.0, 1.155, 1.5, 2.0, 3.0, 4.0):
        m = R.SKEW_H1A > t
        p("     tol %.3f  (%2.0f deg off square)  %5d runs  %7.2f km"
          % (t, 90 - math.degrees(math.asin(min(1.0, 1.0 / t))), int(m.sum()),
             R.loc[m, "CONTACT_M"].sum() / 1000))
    p("")
    p("WHAT RUNNING ALONG COSTS")
    p("  along corridors    %8d   %10.2f km, %d load-bearing plots front them"
      % (int(cor.ALONG.sum()), cor.loc[cor.ALONG, "LEN_M"].sum() / 1000,
         int(cor.loc[cor.ALONG, "N_PLOT"].sum())))
    p("  they form %d chains" % len(M))
    p("  corridor components  %d -> %d if every one is deleted (pieces still carrying a "
      "corridor); %d -> %d counting every node in the published node set"
      % (D["base_live"], D["kept_live"], D["base_nc"], D["kept_nc"]))
    p("  load with a route to the trunk  %.1f -> %.1f m3/d  (loss %.1f = %.2f %% of %.1f)"
      % (D["base_q"], D["kept_q"], D["base_q"] - D["kept_q"],
         100.0 * (D["base_q"] - D["kept_q"]) / D["q_total"], D["q_total"]))
    p("")
    p("  marginal cost of deleting ONE chain")
    for lo, hi, lab in ((-1, 1e-9, "nothing at all"), (1e-9, 10, "under 10 m3/d"),
                        (10, 100, "10 - 100"), (100, 500, "100 - 500"),
                        (500, 1e18, "over 500")):
        m = (M.MARGINAL_M3D > lo) & (M.MARGINAL_M3D <= hi)
        p("     %-16s %4d chains  %7.2f km contact  %5d plots"
          % (lab, int(m.sum()), M.loc[m, "CONTACT_KM"].sum(), int(M.loc[m, "N_PLOT"].sum())))
    p("")
    p("REPLACING THE LINK")
    g = H.groupby("HEAL").agg(n=("CHAIN", "size"), m3d=("MARGINAL_M3D", "sum"),
                              gap=("GAP_M", "median"))
    for k, r in g.iterrows():
        p("  %-38s %4d chains  %9.1f m3/d  median gap %s"
          % (k, int(r["n"]), r["m3d"],
             ("%.1f m" % r["gap"]) if np.isfinite(r["gap"]) else "n/a"))
    p("")
    p("WHAT THE FLAGGED GROUND IS")
    haz_cls = D["haz_class"]
    for c in sorted(haz_cls):
        p("  hazard class %d : %5d ALONG runs  %7.2f km of contact"
          % (c, haz_cls[c][0], haz_cls[c][1] / 1000))
    p("  local wadi width where a corridor runs ALONG (2 x max distance to dry ground)")
    wid = 2.0 * A.D_DRY_MAX
    for lo, hi in ((0, 10), (10, 20), (20, 40), (40, 80), (80, 1e18)):
        m = (wid >= lo) & (wid < hi)
        p("     %4d - %-6s m : %4d runs  %7.2f km  contact p50 %5.0f m"
          % (lo, hi, int(m.sum()), A.loc[m, "CONTACT_M"].sum() / 1000,
             A.loc[m, "CONTACT_M"].median() if m.any() else 0))
    p("  median local width %.1f m; median contact %.1f m"
      % (float(wid.median()), float(A.CONTACT_M.median())))
    p("")
    p("THE CROSSINGS THAT SURVIVE BOTH TESTS")
    K = R[~R.ALONG]
    p("  %d runs, %.2f km of contact; contact p50 %.1f m  p90 %.1f m  max %.1f m"
      % (len(K), K.CONTACT_M.sum() / 1000, K.CONTACT_M.quantile(.5),
         K.CONTACT_M.quantile(.9), K.CONTACT_M.max()))
    p("")
    p("THE ALONG SET BY SOURCE")
    t = cor[cor.ALONG].groupby(["SRC", "CONFIDENCE"]).agg(
        n=("LEN_M", "size"), km=("LEN_M", lambda x: x.sum() / 1000),
        plots=("N_PLOT", "sum"))
    for (sc, cf), r in t.iterrows():
        p("  %-10s %-12s %4d corridors  %7.2f km  %4d plots"
          % (sc, cf, int(r["n"]), r["km"], int(r["plots"])))
    p("  of which the trunk alignment (SRC=main_pipe, the user's own drawing): "
      "%d corridors, %.2f km"
      % (int(((cor.SRC == "main_pipe") & cor.ALONG).sum()),
         cor.loc[(cor.SRC == "main_pipe") & cor.ALONG, "LEN_M"].sum() / 1000))
    p("")
    p("FRONTAGE LOST IF THE ALONG SET IS SIMPLY DELETED")
    p("  %d plots lose every corridor within %.0f m: %.1f m3/d (%.2f %% of %.1f)"
      % (D["lost_plots"], PLOT_SERVED_M, D["lost_q"],
         100.0 * D["lost_q"] / D["q_total"], D["q_total"]))
    p("  (%d plots front an along-wadi corridor; the other %d have another within "
      "%.0f m, median %.1f m away)"
      % (D["front_plots"], D["front_plots"] - D["lost_plots"], PLOT_SERVED_M,
         D["front_p50"]))
    p("")
    p("THE STREET-NETWORK DETOUR (rejected)")
    fin = np.isfinite(DET.ALT_M)
    p("  %d of %d along-corridors have any alternative path at all" % (int(fin.sum()), len(DET)))
    p("  replacing those %d costs %.2f km of extra corridor and %.2f m of extra invert "
      "at the DN200 Table 11 minimum (G203-p29)"
      % (int(fin.sum()), DET.loc[fin, "EXTRA_M"].clip(lower=0).sum() / 1000,
         DET.loc[fin, "EXTRA_DEPTH_M"].max()))
    return "\n".join(L)


# ===================================================================== the figures

def _wadi_cmap():
    from matplotlib.colors import ListedColormap
    return ListedColormap([fk.C.WADI])


def _proj_note():
    return ("PROJECT ASSUMPTIONS, not guideline values: wadi = AR&R flood-hazard class "
            "4/5/6 of the 50-year grid (criteria.HAZARD_WADI_CLASSES), standing in for "
            "G203-p30 4.4.1's \"areas subject to washout\", which is a SCOUR criterion; "
            "skew tolerance 1.155 = 1/cos 30 deg (audit.WADI_XING_SKEW) is our tolerance "
            "on H1's word \"perpendicular\".")


def fr01(D):
    """Map — where the along-wadi corridors are, against the crossings that are legal."""
    cor, R = D["cor"], D["R"]
    ext = fk.extent_of(cor)
    A = cor[cor.ALONG]
    X = cor[(cor.ON_WADI_M > 0) & ~cor.ALONG]
    fig, ax, note = fk.map_frame(
        ext,
        title="%.0f km of published corridor runs ALONG a wadi, and the audit passes it"
              % (cor.loc[cor.ALONG, "LEN_M"].sum() / 1000),
        subtitle="Every corridor still touching hazard class 4/5/6 is scheduled as a "
                 "crossing. Tested the way H1a item 1 is written — contact against the "
                 "SHORTEST crossing available at that point — %d of %d contiguous "
                 "contacts are not crossings at all."
                 % (int(R.ALONG.sum()), len(R)))
    known, wadi, wext = fk.hazard_coverage(ext)
    ax.imshow(np.where(wadi, 1.0, np.nan), extent=wext, cmap=_wadi_cmap(),
              interpolation="nearest", zorder=1.5, alpha=0.45, vmin=0, vmax=1)
    cor.plot(ax=ax, color=fk.C.GREY, linewidth=0.3, alpha=0.55, zorder=3)
    X.plot(ax=ax, color=fk.C.FLAG, linewidth=0.9, zorder=4)
    A.plot(ax=ax, color=fk.C.FAIL, linewidth=1.7, zorder=5)
    fk.hatch_untested(ax, ~known, wext)
    try:
        fk.study_boundary().boundary.plot(ax=ax, color=fk.C.BOUNDARY, linewidth=1.0,
                                          zorder=6)
    except Exception:
        pass
    h = [Line2D([], [], color=fk.C.GREY, lw=1.2, label="corridor, clear of the hazard grid"),
         Line2D([], [], color=fk.C.FLAG, lw=1.6,
                label="on wadi, and a crossing on either test (%.1f km)"
                      % (R.loc[~R.ALONG, "CONTACT_M"].sum() / 1000)),
         Line2D([], [], color=fk.C.FAIL, lw=2.4,
                label="on wadi, and running ALONG it by H1a item 1 (%.1f km)"
                      % (R.loc[R.ALONG, "CONTACT_M"].sum() / 1000)),
         Patch(facecolor=fk.C.WADI, alpha=0.45, label="hazard class 4/5/6 (50-yr)"),
         fk.untested_handle()]
    box = ("corridors            %6d   %8.1f km\n"
           "touching wadi        %6d   %8.2f km\n"
           "  crossings kept     %6d   %8.2f km\n"
           "  running ALONG      %6d   %8.2f km\n"
           "hazard samples UNTESTED       %5.1f %%"
           % (len(cor), cor.LEN_M.sum() / 1000,
              int((cor.ON_WADI_M > 0).sum()), R.CONTACT_M.sum() / 1000,
              int((~R.ALONG).sum()), R.loc[~R.ALONG, "CONTACT_M"].sum() / 1000,
              int(R.ALONG.sum()), R.loc[R.ALONG, "CONTACT_M"].sum() / 1000,
              D["cover"]["pct_unknown"]))
    fk.finish_map(fig, ax, source=fk.source_line(D["src_cor"]) + "  ·  hazard grid "
                  "Data/04 Lekhuwair/Hazard_T50y.tif",
                  note=(note or "") + "  " + _proj_note(),
                  legend_handles=h, databox=box, legend_loc="lower left")
    return fk.save(fig, "FR01_along_wadi_corridors")


def fr02(D):
    """Chart — the two along/across tests, and how the answer moves with the tolerance."""
    R = D["R"]
    fig, ax = fk.chart_frame(
        title="The test in the code measures the wrong width",
        subtitle="Kilometres of on-wadi corridor contact that each test calls "
                 "\"running along a wadi\", out of %.1f km in total. The perpendicular "
                 "probe finds %.2f km; the same tolerance against the shortest crossing "
                 "available finds %.2f km. The greyed bar is the same clause with the "
                 "MEDIAN distance to dry ground instead of the maximum - it scores a "
                 "PERFECT perpendicular crossing at 2.00 and is wrong by a factor of two."
                 % (R.CONTACT_M.sum() / 1000,
                    R.loc[R.SKEW_PROBE > WADI_XING_SKEW, "CONTACT_M"].sum() / 1000,
                    R.loc[R.ALONG, "CONTACT_M"].sum() / 1000),
        figsize=(8.8, 5.0))
    labs, vals, cols = [], [], []
    labs.append("probe perpendicular to the pipe\n(s2._square_crossing / audit.r4)")
    vals.append(R.loc[R.SKEW_PROBE > WADI_XING_SKEW, "CONTACT_M"].sum() / 1000)
    cols.append(fk.C.PASS)
    labs.append("same clause, 2 x MEDIAN not MAX\n(condemns a perfect crossing)")
    vals.append(R.loc[R.SKEW_MED > WADI_XING_SKEW, "CONTACT_M"].sum() / 1000)
    cols.append(fk.C.UNTESTED)
    for t in (4.0, 3.0, 2.0, 1.5, 1.155, 1.0):
        deg = 90 - math.degrees(math.asin(min(1.0, 1.0 / t)))
        labs.append("shortest crossing, tol %.3f\n(%.0f deg off square)" % (t, deg))
        vals.append(R.loc[R.SKEW_H1A > t, "CONTACT_M"].sum() / 1000)
        cols.append(fk.C.FAIL if abs(t - WADI_XING_SKEW) < 1e-6 else fk.C.FLAG)
    y = np.arange(len(labs))
    for i, (yy, vv, cc) in enumerate(zip(y, vals, cols)):
        ax.barh(yy, vv, color=cc, edgecolor=fk.C.INK, linewidth=0.6,
                hatch=("///" if cc == fk.C.FAIL else None), height=0.68)
        ax.text(vv + 1.0, yy, "%.2f km" % vv, va="center", fontsize=8.4, color=fk.C.INK)
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.0)
    ax.invert_yaxis()
    ax.set_xlabel("kilometres of on-wadi corridor contact judged to run ALONG")
    ax.set_xlim(0, max(vals) * 1.22)
    fk.style_axes(ax, xgrid=True, ygrid=False)
    ax.axhline(1.5, color=fk.C.GREY, lw=0.8, ls=":")
    fk.finish_chart(fig, source=fk.source_line(D["src_cor"]) + "  ·  hazard grid "
                    "Data/04 Lekhuwair/Hazard_T50y.tif",
                    note="1.155 is the philosophy's own tolerance (audit.WADI_XING_SKEW, "
                         "1/cos 30 deg) and is a PROJECT value. " + _proj_note())
    return fk.save(fig, "FR02_two_tests")


def fr03(D):
    """Chart — the cost is not frontage, it is the link; and 21 chains carry all of it."""
    M, H = D["M"], D["H"]
    fig, ax = fk.chart_frame(
        title="%d along-wadi chains; %d of them carry the whole problem"
              % (len(M), int((M.MARGINAL_M3D > 100).sum())),
        subtitle="Load that loses its route to the trunk when ONE chain is deleted and "
                 "every other corridor is kept. %d chains cost nothing. Marginal costs "
                 "do NOT add - chains in " % int((M.MARGINAL_M3D <= 1e-9).sum()) +
                 "series on one route each carry the same load - so the joint loss when "
                 "all %d go is %.0f m3/d (%.1f %% of %.0f), less than the bands below "
                 "sum to." % (len(M), D["base_q"] - D["kept_q"],
                              100.0 * (D["base_q"] - D["kept_q"]) / D["q_total"],
                              D["q_total"]),
        figsize=(9.4, 6.4))
    bands = [(-1, 1e-9, "nothing"), (1e-9, 10, "under 10 m3/d"), (10, 100, "10 - 100"),
             (100, 500, "100 - 500"), (500, 1e18, "over 500 m3/d")]
    n = [int(((M.MARGINAL_M3D > lo) & (M.MARGINAL_M3D <= hi)).sum()) for lo, hi, _ in bands]
    km = [M.loc[(M.MARGINAL_M3D > lo) & (M.MARGINAL_M3D <= hi), "CONTACT_KM"].sum()
          for lo, hi, _ in bands]
    q = [M.loc[(M.MARGINAL_M3D > lo) & (M.MARGINAL_M3D <= hi), "MARGINAL_M3D"].sum()
         for lo, hi, _ in bands]
    y = np.arange(len(bands))
    cols = [fk.C.PASS, fk.C.PASS, fk.C.FLAG, fk.C.FAIL, fk.C.FAIL]
    for yy, nn, kk, qq, cc, lab in zip(y, n, km, q, cols, [b[2] for b in bands]):
        ax.barh(yy, nn, color=cc, edgecolor=fk.C.INK, linewidth=0.6, height=0.66,
                hatch=("///" if cc == fk.C.FAIL else None))
        ax.text(nn + 6, yy, "%d chains · %.1f km of contact · %s"
                % (nn, kk, ("nothing stranded" if qq < 0.5
                            else "%.0f m3/d stranded" % qq)),
                va="center", fontsize=8.2, color=fk.C.INK)
    ax.set_yticks(y)
    ax.set_yticklabels(["deleting the chain strands\n" + b[2] for b in bands], fontsize=8.4)
    ax.invert_yaxis()
    ax.set_xlabel("number of along-wadi chains")
    ax.set_xlim(0, max(n) * 1.65)
    fk.style_axes(ax, xgrid=True, ygrid=False)
    heal = H[H.MARGINAL_M3D > 0].groupby("HEAL").agg(n=("CHAIN", "size"),
                                                    m3d=("MARGINAL_M3D", "sum"),
                                                    gap=("GAP_M", "median"))
    txt = ["Replacing the link, not the route:"]
    for k, r in heal.sort_values("m3d", ascending=False).iterrows():
        txt.append("  %-38s %3d chains, median gap %s"
                   % (k, int(r["n"]),
                      ("%.1f m" % r["gap"]) if np.isfinite(r["gap"]) else "n/a"))
    ax.text(0.985, 0.03, "\n".join(txt), transform=ax.transAxes, fontsize=7.4,
            ha="right", va="bottom", family="monospace",
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="#8a8a8a", alpha=0.94))
    fk.finish_chart(fig, source=fk.source_line(D["src_cor"], D["src_pl"]),
                    note="Load is W10_plot_loads Q_AVG_M3D pinned to the nearest corridor "
                         "within %.0f m (s2_corridors.PLOT_SERVED_M). "
                         % PLOT_SERVED_M + _proj_note())
    return fk.save(fig, "FR03_chain_marginal_cost")


def fr04(D):
    """Map — the cluster that carries most of the stranded load, and its 4.5-21.6 m heals."""
    cor, H, M = D["cor"], D["H"], D["M"]
    top = H[np.isfinite(H.GAP_M) & (H.MARGINAL_M3D >= 500)]
    if not len(top):
        top = H[np.isfinite(H.GAP_M) & (H.MARGINAL_M3D >= 100)]
    if not len(top):
        return None
    # one cluster, not a study-area view: at 46 km wide a 13 m link is invisible, and the
    # finding IS the size of the link.  The chains over 500 m3/d all fall in one place.
    pad = 450.0
    x0 = min(top.X.min(), top.LX0.min(), top.LX1.min()) - pad
    x1 = max(top.X.max(), top.LX0.max(), top.LX1.max()) + pad
    y0 = min(top.Y.min(), top.LY0.min(), top.LY1.min()) - pad
    y1 = max(top.Y.max(), top.LY0.max(), top.LY1.max()) + pad
    ext = (x0, y0, x1, y1)
    win = cor.cx[x0:x1, y0:y1]
    fig, ax, note = fk.map_frame(
        ext,
        title="The severance is metres wide, not kilometres — %d links of %.1f-%.1f m "
              "restore %.0f m3/d" % (len(top), top.GAP_M.min(), top.GAP_M.max(),
                                     top.MARGINAL_M3D.sum()),
        subtitle="Every chain here strands more than 500 m3/d on its own. Deleting it "
                 "leaves a gap to corridor that is already in the set, and on this "
                 "cluster that gap is clear of the hazard grid.")
    known, wadi, wext = fk.hazard_coverage(ext)
    ax.imshow(np.where(wadi, 1.0, np.nan), extent=wext, cmap=_wadi_cmap(),
              interpolation="nearest", zorder=1.5, alpha=0.45, vmin=0, vmax=1)
    win[~win.ALONG].plot(ax=ax, color=fk.C.GREY, linewidth=0.7, zorder=3)
    win[win.ALONG].plot(ax=ax, color=fk.C.FAIL, linewidth=2.0, zorder=5)
    fk.hatch_untested(ax, ~known, wext)
    for r in top.itertuples():
        ax.plot([r.LX0, r.LX1], [r.LY0, r.LY1], color=fk.C.SUBMAIN, lw=3.4,
                zorder=7, solid_capstyle="round")
        mx, my = 0.5 * (r.LX0 + r.LX1), 0.5 * (r.LY0 + r.LY1)
        ax.annotate("%.1f m" % r.GAP_M, (mx, my), textcoords="offset points",
                    xytext=(6, 6), fontsize=7.0, color=fk.C.SUBMAIN, zorder=9,
                    fontweight="bold")
        ax.plot([r.LX0, r.LX1], [r.LY0, r.LY1], marker="o", ms=3.0, ls="none",
                color=fk.C.SUBMAIN, zorder=8)
    h = [Line2D([], [], color=fk.C.FAINT, lw=1.2, label="corridor kept"),
         Line2D([], [], color=fk.C.FAIL, lw=2.4, label="corridor running ALONG a wadi"),
         Line2D([], [], color=fk.C.SUBMAIN, lw=2.6,
                label="link that restores the route (%.1f-%.1f m)"
                      % (top.GAP_M.min(), top.GAP_M.max())),
         Patch(facecolor=fk.C.WADI, alpha=0.45, label="hazard class 4/5/6 (50-yr)"),
         fk.untested_handle()]
    box = ("chains shown          %4d\n"
           "load they strand   %7.0f m3/d\n"
           "link length      %4.1f - %4.1f m\n"
           "node merge radius     %4.1f m"
           % (len(top), top.MARGINAL_M3D.sum(), top.GAP_M.min(), top.GAP_M.max(),
              NODE_MERGE_M))
    fk.finish_map(fig, ax, source=fk.source_line(D["src_cor"], D["src_pl"]),
                  note=(note or "") + "  " + _proj_note(),
                  legend_handles=h, databox=box, legend_loc="upper right")
    return fk.save(fig, "FR04_severance_heal")



# ============================================================ the proposed patch, simulated

HEAL_CAP_M = 50.0          # PROJECT value, swept below.  s2.stitch already reaches 400 m
                           # for a skeleton pocket; a severance heal is a much smaller job
                           # and the cap is what keeps it one.


def _link_legal(link, haz):
    """Is a generated link itself legal under H1/H1a?  (clear, or a square crossing)

    The shortest crossing is 2 x the MAXIMUM distance to dry ground over the link's ON-WADI
    samples - the same statistic Change B uses for a corridor run, and for the same reason:
    on a square crossing the distance ramps 0 -> W/2 -> 0, so the max recovers the band
    width and the median recovers half of it.  Taking it at the link's midpoint instead is
    worse again: on a 4 m link the midpoint often lands on a dry cell and returns 0.
    """
    d, xs, ys = _sample(link)
    on, kn = haz.at(xs, ys)
    ct = float(on.sum()) / max(len(on), 1) * link.length
    if ct <= 1e-6:
        return True, "clear of the wadi", ct
    ct += WADI_SAMPLE_M                       # audit._r4_classify's contact definition
    dd = haz.d_dry(xs[on], ys[on])
    dd = dd[np.isfinite(dd)]
    xing = 2.0 * float(dd.max()) if dd.size else np.inf
    ok = ct <= WADI_XING_SKEW * max(xing, WADI_SAMPLE_M)
    return ok, ("square crossing" if ok else "still along a wadi"), ct


def _heal(D, cap):
    """Delete the ALONG set, then join each severed piece to something that reaches the
    trunk with a link that is itself legal and no longer than `cap`."""
    from shapely.strtree import STRtree
    cor, haz = D["cor"], D["haz"]
    keep = cor[~cor.ALONG].copy().reset_index(drop=True)
    G = nx.Graph()
    for r in keep.itertuples():
        G.add_edge(r.US_NODE, r.DS_NODE)
    links, extra = [], []
    for _ in range(60):
        comp = {}
        for k, cc in enumerate(nx.connected_components(G)):
            for n in cc:
                comp[n] = k
        keep["CMP"] = keep.US_NODE.map(comp)
        good = set(keep.loc[keep.SRC == "main_pipe", "CMP"])
        keep["TR"] = keep.CMP.isin(good)
        if keep.TR.all():
            break
        tr = keep[keep.TR]
        if not len(tr):
            break
        tree = STRtree(tr.geometry.values)
        made = 0
        order = keep[~keep.TR].groupby("CMP").LEN_M.sum().sort_values(ascending=False)
        for c in order.index:
            g = unary_union(keep.loc[keep.CMP == c, "geometry"].values)
            idx = np.atleast_1d(tree.query_nearest(g, all_matches=False))
            if not idx.size:
                continue
            p_, q_ = nearest_points(g, tr.geometry.values[int(idx[0])])
            link = LineString([(p_.x, p_.y), (q_.x, q_.y)])
            if link.length < 1e-9 or link.length > cap:
                continue
            ok, why, ct = _link_legal(link, haz)
            if not ok:
                continue
            na = keep.loc[keep.CMP == c, "US_NODE"].iloc[0]
            nb = tr.US_NODE.iloc[int(idx[0])]
            G.add_edge(na, nb)
            extra.append((na, nb, float(link.length)))
            links.append(dict(LEN_M=link.length, WHY=why, CONTACT_M=ct,
                              X0=p_.x, Y0=p_.y, X1=q_.x, Y1=q_.y,
                              ORPHAN_KM=float(order[c]) / 1000.0))
            made += 1
        if not made:
            break
    comp = {}
    for k, cc in enumerate(nx.connected_components(G)):
        for n in cc:
            comp[n] = k
    keep["CMP"] = keep.US_NODE.map(comp)
    good = set(keep.loc[keep.SRC == "main_pipe", "CMP"])
    keep["TR"] = keep.CMP.isin(good)
    emap = pd.Series(np.arange(len(D["cor"])), index=D["cor"].CORR_ID)
    ei = emap.reindex(keep.CORR_ID).values.astype(int)
    q = float(D["load_edge"][ei][keep.TR.values].sum())
    return q, int(keep.CMP.nunique()), pd.DataFrame(links), keep, extra


def _dist_to_trunk(edges, extra=()):
    G = nx.Graph()
    for r in edges.itertuples():
        w = float(r.LEN_M)
        if G.has_edge(r.US_NODE, r.DS_NODE):
            G[r.US_NODE][r.DS_NODE]["weight"] = min(G[r.US_NODE][r.DS_NODE]["weight"], w)
        else:
            G.add_edge(r.US_NODE, r.DS_NODE, weight=w)
    for a, b, w in extra:
        G.add_edge(a, b, weight=w)
    roots = (set(edges.loc[edges.SRC == "main_pipe", "US_NODE"])
             | set(edges.loc[edges.SRC == "main_pipe", "DS_NODE"]))
    G.add_node("__T__")
    for r in roots:
        if G.has_node(r):
            G.add_edge("__T__", r, weight=0.0)
    d = nx.single_source_dijkstra_path_length(G, "__T__", weight="weight")
    return {r.CORR_ID: min(d.get(r.US_NODE, np.inf), d.get(r.DS_NODE, np.inf))
            for r in edges.itertuples()}


def simulate_patch(D, caps=(10.0, 25.0, 50.0, 100.0, 200.0, 400.0)):
    """What the patch would recover.  Returned as text."""
    L = []; p = L.append
    p("THE PATCH, SIMULATED - delete every ALONG corridor, then heal the severance")
    p("  baseline: %d corridors, %.2f km, trunk-connected load %.1f m3/d, %d pieces"
      % (len(D["cor"]), D["cor"].LEN_M.sum() / 1000, D["base_q"], D["base_live"]))
    p("  %6s %7s %10s %8s %12s %10s" % ("cap m", "links", "link km", "pieces",
                                        "trunk m3/d", "vs base"))
    best = None
    for cap in caps:
        q, live, LK, keep, extra = _heal(D, cap)
        p("  %6.0f %7d %10.3f %8d %12.1f %+10.1f"
          % (cap, len(LK), LK.LEN_M.sum() / 1000 if len(LK) else 0.0, live, q,
             q - D["base_q"]))
        if abs(cap - HEAL_CAP_M) < 1e-9:
            best = (LK, keep, extra)
    if best is None:
        return "\n".join(L)
    LK, keep, extra = best
    p("")
    p("  at the %.0f m cap: %s; median link %.1f m"
      % (HEAL_CAP_M, ", ".join("%d %s" % (v, k) for k, v in
                               LK.WHY.value_counts().items()), LK.LEN_M.median()))
    try:
        plots = gpd.read_file(str(fk.MOH_PLOTS))
        if plots.crs is not None and plots.crs.to_epsg() != fk.EPSG:
            plots = plots.to_crs(fk.EPSG)
        gl = gpd.GeoDataFrame(LK.copy(), crs="EPSG:%d" % fk.EPSG, geometry=[
            LineString([(r.X0, r.Y0), (r.X1, r.Y1)]) for r in LK.itertuples()])
        jj = gpd.sjoin(gl, plots[["geometry"]], how="left", predicate="intersects")
        gl["N_PLOT_CROSS"] = jj.groupby(level=0).index_right.apply(
            lambda x: x.notna().sum())
        p("  right of way: %d of %d links cross no registered plot (%.3f km); "
          "%d cross one (%.3f km, median %.1f m) and need a ROW answer"
          % (int((gl.N_PLOT_CROSS == 0).sum()), len(gl),
             gl.loc[gl.N_PLOT_CROSS == 0, "LEN_M"].sum() / 1000,
             int((gl.N_PLOT_CROSS > 0).sum()),
             gl.loc[gl.N_PLOT_CROSS > 0, "LEN_M"].sum() / 1000,
             gl.loc[gl.N_PLOT_CROSS > 0, "LEN_M"].median()))
    except Exception as e:                                   # noqa: BLE001
        p("  right-of-way check could not run: %s" % e)
    before = _dist_to_trunk(D["cor"])
    after = _dist_to_trunk(keep, extra=extra)
    T = pd.DataFrame(dict(Q=pd.Series(D["load_edge"], index=D["cor"].CORR_ID)))
    T["B"] = pd.Series(before); T["A"] = pd.Series(after)
    T = T[(T.Q > 0) & np.isfinite(T.B) & np.isfinite(T.A)].copy()
    T["E"] = (T.A - T.B).clip(lower=0)
    w = T.Q / T.Q.sum()
    p("")
    p("  DEPTH - screening only, stage 6 has not run.  Extra flow-path length to the")
    p("  trunk x the minimum gradient for the diameter (G203-p29 Table 11):")
    p("    extra path: p50 %.0f m  p90 %.0f m  max %.0f m; load-weighted mean %.0f m"
      % (T.E.quantile(.5), T.E.quantile(.9), T.E.max(), float((T.E * w).sum())))
    for g, lab in ((0.00500, "DN200  5.00 mm/m (steepest minimum, worst case)"),
                   (0.00125, "DN600  1.25 mm/m"),
                   (0.00075, "DN900+ 0.75 mm/m (Table 11 floor)")):
        d = T.E * g
        p("    %-42s mean %.2f m  p90 %.2f m  max %.2f m  load past the 12 m cap %.0f m3/d"
          % (lab, float((d * w).sum()), d.quantile(.9), d.max(),
             T.loc[d > 12.0, "Q"].sum()))
    return "\n".join(L)


def main(argv):
    fk.use_style()
    D = measure()
    txt = numbers(D)
    print(txt)
    if "--patch" in argv:
        pt = simulate_patch(D)
        print(); print(pt)
        txt = txt + "\n\n" + pt
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "numbers.txt").write_text(txt, encoding="utf-8")
    if "--numbers" in argv or "--patch" in argv:
        return 0
    for f in (fr01, fr02, fr03, fr04):
        p = f(D)
        print("  wrote", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
