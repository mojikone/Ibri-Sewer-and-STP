"""Corridor quality, measured per source.

W10's 2,211.8 km of corridor came from four places of very different provenance, and the
design was built on all of them without anyone measuring how buildable each one is. This
script measures five defects on every corridor line and writes them back as attributes, so
a defect can be argued with feature by feature rather than as a headline percentage.

The defects, and why each one is a defect:

  DUAL   distance to a `dual`=1 centre line. No pipe of any kind may run along a dual
         carriageway (rule 7, user 2026-08-19) because it cannot be dug up. Reported in
         bands, because a corridor 4 m from the centre line IS the carriageway while one
         12 m away is the verge or the service road beside it, which is normal.
  WADI   the 50-year hazard grid, classes 4/5/6. The grid is continuous float, so the test
         is floor(v) >= 4. No pipe and no chamber may sit on wadi ground.
  PLOT   the corridor crossing a registered plot. A street centre line should run between
         plots; one that runs through a plot is either a survey mismatch or a corridor
         invented across private land, and it cannot be built as drawn.
  GEOM   vertex density, segment length, stubs, dangles - whether the line is a drawn
         centre line or a raster artefact.
  DUP    near-duplicate parallel lines: a second corridor within 8 m of this one that does
         not connect to it. Two pipes in one street.

Nothing here changes the design. It measures it.

Run:  python r1_corridor_quality.py
"""
import os
import sys
import time
import warnings
from collections import defaultdict

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import config as C

warnings.filterwarnings("ignore")

DUAL_BANDS = (4.0, 6.0, 8.0, 12.0)
DUAL_VIOLATION_M = 6.0      # the band carried as the headline violation
WADI_MIN_CLASS = 4.0
PLOT_INSET_M = 3.0          # a corridor this far inside a plot boundary is not clipping it
SAMPLE_M = 10.0             # step along a line for the raster and duplicate tests
DUP_M = 8.0                 # another corridor this close, not connected, is a duplicate
SHORT_M = 15.0
NODE_SNAP_M = 0.5

OUT_RUN = os.path.join(C.OUT, "run")
DOC = os.path.join(C.OUT, "docs", "research")


# --------------------------------------------------------------------------- helpers
def explode_ls(gdf):
    """One LineString per row, index kept so attributes can be regrouped."""
    g = gdf.explode(index_parts=False)
    return g[g.geometry.geom_type == "LineString"]


def sample_points(lines, step=SAMPLE_M):
    """Points every `step` along every line, plus the line index each belongs to.

    Returns (xy array, owner array, weight array). The weight is the length of line each
    sample stands for, so summing weights over the samples that fail a test gives a length
    in metres rather than a count.
    """
    xs, ys, own, wt = [], [], [], []
    for i, ln in enumerate(lines):
        L = ln.length
        n = max(1, int(np.ceil(L / step)))
        w = L / n
        for k in range(n):
            p = ln.interpolate((k + 0.5) * w)
            xs.append(p.x)
            ys.append(p.y)
            own.append(i)
            wt.append(w)
    return (np.array(xs), np.array(ys), np.array(own, dtype=np.int64),
            np.array(wt, dtype=float))


def length_within(lines, cover_union):
    """Length of each line falling inside a (possibly huge) prepared union."""
    out = np.zeros(len(lines))
    for i, ln in enumerate(lines):
        try:
            out[i] = ln.intersection(cover_union).length
        except Exception:
            out[i] = 0.0
    return out


def length_within_tree(lines, polys, tree):
    """Length of each line inside any polygon, via an STRtree so the union is never built.

    Building a union of 61,272 plot polygons is slow and fragile; querying each line
    against a tree and unioning only its own candidates is both faster and exact.
    """
    out = np.zeros(len(lines))
    for i, ln in enumerate(lines):
        idx = tree.query(ln)
        if len(idx) == 0:
            continue
        tot = 0.0
        hits = []
        for j in idx:
            p = polys[int(j)]
            if p.is_empty:
                continue
            hits.append(p)
        if not hits:
            continue
        try:
            tot = ln.intersection(unary_union(hits)).length
        except Exception:
            for p in hits:
                try:
                    tot += ln.intersection(p).length
                except Exception:
                    pass
        out[i] = tot
    return out


def main():
    t0 = time.time()
    os.makedirs(DOC, exist_ok=True)

    cor = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridors.shp"))
    cor = explode_ls(cor).reset_index(drop=True)
    cor["LEN_M"] = cor.length
    lines = list(cor.geometry)
    print(f"corridors: {len(cor):,} lines, {cor.LEN_M.sum()/1000:,.1f} km")
    print(cor.groupby("SRC").LEN_M.agg(n="size", km=lambda s: s.sum() / 1000).round(1)
          .to_string())

    # ------------------------------------------------------------------ 1  dual
    t = time.time()
    roads = gpd.read_file(C.ROADS).set_crs(C.EPSG, allow_override=True)
    dual = roads[roads["dual"].astype(str) == "1"]
    print(f"\ndual carriageway centre lines: {len(dual):,}, "
          f"{dual.length.sum()/1000:,.1f} km")
    for band in DUAL_BANDS:
        buf = unary_union(dual.geometry.buffer(band))
        L = length_within(lines, buf)
        cor[f"DUAL{int(band)}_M"] = L
        print(f"   within {band:4.1f} m: {L.sum()/1000:7.2f} km on "
              f"{(L > 5).sum():,} lines")
    cor["ON_DUAL_M"] = cor[f"DUAL{int(DUAL_VIOLATION_M)}_M"]
    t = time.time() - t
    print(f"   ({t:.0f} s)")

    # ------------------------------------------------------------------ 2  wadi
    t = time.time()
    xs, ys, own, wt = sample_points(lines)
    print(f"\nsampling {len(xs):,} points at {SAMPLE_M:.0f} m along the corridors")
    with rasterio.open(C.HAZARD) as src:
        vals = np.array([v[0] for v in src.sample(zip(xs, ys))], dtype=float)
    bad = np.isfinite(vals) & (vals > -1000) & (np.floor(vals) >= WADI_MIN_CLASS)
    wadi_m = np.bincount(own[bad], weights=wt[bad], minlength=len(lines))
    cor["WADI_M"] = wadi_m
    print(f"   on wadi ground (floor >= {WADI_MIN_CLASS:.0f}): "
          f"{wadi_m.sum()/1000:,.1f} km")
    print(f"   ({time.time()-t:.0f} s)")

    # ------------------------------------------------------------------ 3  plots
    t = time.time()
    plots = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)
    plots = plots[plots.geometry.notna() & ~plots.geometry.is_empty]
    pg = list(plots.geometry)
    tree = STRtree(pg)
    cor["PLOT_M"] = length_within_tree(lines, pg, tree)
    print(f"\ninside a registered plot: {cor.PLOT_M.sum()/1000:,.1f} km")

    inset = [g.buffer(-PLOT_INSET_M) for g in pg]
    inset = [g if (g is not None and not g.is_empty) else Point(0, 0).buffer(1e-9)
             for g in inset]
    tree_in = STRtree(inset)
    cor["PLOTIN_M"] = length_within_tree(lines, inset, tree_in)
    print(f"   more than {PLOT_INSET_M:.0f} m inside a plot (not clipping the edge): "
          f"{cor.PLOTIN_M.sum()/1000:,.1f} km")
    print(f"   ({time.time()-t:.0f} s)")

    # ------------------------------------------------------------------ 4  geometry
    t = time.time()
    nvert, medseg, maxseg = [], [], []
    for ln in lines:
        c = np.asarray(ln.coords)[:, :2]
        d = np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1]))
        nvert.append(len(c))
        medseg.append(float(np.median(d)) if len(d) else 0.0)
        maxseg.append(float(d.max()) if len(d) else 0.0)
    cor["NVERT"] = nvert
    cor["MEDSEG_M"] = np.round(medseg, 2)
    cor["MAXSEG_M"] = np.round(maxseg, 1)
    cor["VPER100M"] = np.round(np.array(nvert) / np.maximum(cor.LEN_M.values, 1) * 100, 2)
    cor["SHORT"] = (cor.LEN_M < SHORT_M).astype(int)

    # Dangles. NOT measured by shared endpoints: these lines come from a DXF and from a
    # road layer, where lines CROSS one another without sharing a vertex, and the noding
    # step downstream is what splits them. An endpoint-only test called 1,364 drafted
    # lines free at both ends, which is a property of CAD drafting, not a defect. So the
    # test is whether ANY part of another line passes within NODE_SNAP_M of the endpoint.
    ends = np.array([p for ln in lines for p in (ln.coords[0][:2], ln.coords[-1][:2])])
    owner = np.repeat(np.arange(len(lines)), 2)
    ltree = STRtree(lines)
    epts = [Point(x, y) for x, y in ends]
    ai, bi = ltree.query(np.array(epts, dtype=object), predicate="dwithin",
                         distance=NODE_SNAP_M)
    touched = np.zeros(len(ends), dtype=bool)
    for a, b in zip(ai, bi):
        if owner[a] != b:
            touched[a] = True
    free = ~touched
    cor["DANGLES"] = free.reshape(-1, 2).sum(axis=1)
    print(f"\ngeometry: {int((cor.DANGLES == 2).sum()):,} lines free at both ends, "
          f"{int((cor.DANGLES == 1).sum()):,} at one, "
          f"{int(cor.SHORT.sum()):,} shorter than {SHORT_M:.0f} m")
    print(f"   ({time.time()-t:.0f} s)")

    # ------------------------------------------------------------------ 5  duplicates
    # A duplicate is a SECOND CORRIDOR IN THE SAME STREET, so proximity alone will not do:
    # every junction puts two lines within 8 m of each other. The test is proximity PLUS
    # near-parallel bearing - within 25 degrees, modulo 180 - which a crossing fails and a
    # doubled-up street passes. This is the defect the skeletoniser's block collars create:
    # a ring around a block whose two sides serve the same houses.
    t = time.time()
    seg_dir = []                       # unit bearing of every line, sampled at the point
    for i, ln in enumerate(lines):
        c = np.asarray(ln.coords)[:, :2]
        seg_dir.append(c)

    def bearing_at(li_, px, py):
        c = seg_dir[li_]
        if len(c) < 2:
            return np.nan
        a, b = c[:-1], c[1:]
        ab = b - a
        L2 = (ab ** 2).sum(axis=1)
        L2[L2 == 0] = 1e-12
        tt = np.clip(((px - a[:, 0]) * ab[:, 0] + (py - a[:, 1]) * ab[:, 1]) / L2, 0, 1)
        cx, cy = a[:, 0] + tt * ab[:, 0], a[:, 1] + tt * ab[:, 1]
        k = int(np.argmin((cx - px) ** 2 + (cy - py) ** 2))
        return np.arctan2(ab[k, 1], ab[k, 0])

    own_bear = np.array([bearing_at(own[i], xs[i], ys[i]) for i in range(len(xs))])
    pts_arr = np.array([Point(x, y) for x, y in zip(xs, ys)], dtype=object)
    pi, li = ltree.query(pts_arr, predicate="dwithin", distance=DUP_M)
    dup = np.zeros(len(xs), dtype=bool)
    for a, b in zip(pi, li):
        if own[a] == b or dup[a]:
            continue
        ob = bearing_at(b, xs[a], ys[a])
        if not np.isfinite(ob) or not np.isfinite(own_bear[a]):
            continue
        d = abs((own_bear[a] - ob + np.pi / 2) % np.pi - np.pi / 2)
        if d < np.deg2rad(25.0):
            dup[a] = True
    dup_m = np.bincount(own[dup], weights=wt[dup], minlength=len(lines))
    cor["DUP_M"] = dup_m
    print(f"\nwithin {DUP_M:.0f} m of a near-PARALLEL second corridor: "
          f"{dup_m.sum()/1000:,.1f} km")
    print(f"   ({time.time()-t:.0f} s)")

    # ------------------------------------------------------------------ flag
    # A corridor is UNBUILDABLE if a pipe may not be laid in it as drawn: on a dual
    # carriageway, on wadi ground, or through the body of a plot. SUSPECT if it is
    # duplicated or geometrically doubtful. OK otherwise.
    frac = lambda a: np.where(cor.LEN_M.values > 0, a / cor.LEN_M.values, 0.0)
    cor["F_DUAL"] = np.round(frac(cor.ON_DUAL_M.values), 3)
    cor["F_WADI"] = np.round(frac(cor.WADI_M.values), 3)
    cor["F_PLOT"] = np.round(frac(cor.PLOTIN_M.values), 3)
    cor["F_DUP"] = np.round(frac(cor.DUP_M.values), 3)

    bad = ((cor.F_DUAL > 0.25) | (cor.F_WADI > 0.25) | (cor.F_PLOT > 0.25))
    susp = ~bad & ((cor.F_DUAL > 0.05) | (cor.F_WADI > 0.05) | (cor.F_PLOT > 0.05) |
                   (cor.F_DUP > 0.5) | (cor.DANGLES == 2) | (cor.SHORT == 1))
    cor["QFLAG"] = np.where(bad, "unbuildable", np.where(susp, "suspect", "ok"))

    keep = ["SRC", "CORR_ID", "LEN_M", "DUAL4_M", "DUAL6_M", "DUAL8_M", "DUAL12_M",
            "ON_DUAL_M", "WADI_M", "PLOT_M", "PLOTIN_M", "DUP_M", "NVERT", "MEDSEG_M",
            "MAXSEG_M", "VPER100M", "DANGLES", "SHORT", "F_DUAL", "F_WADI", "F_PLOT",
            "F_DUP", "QFLAG", "geometry"]
    keep = [k for k in keep if k in cor.columns]
    out = cor[keep].copy()
    for c in ("LEN_M", "ON_DUAL_M", "WADI_M", "PLOT_M", "PLOTIN_M", "DUP_M",
              "DUAL4_M", "DUAL6_M", "DUAL8_M", "DUAL12_M"):
        if c in out:
            out[c] = out[c].round(2)
    dst = os.path.join(C.OUT_SHP, "W10_corridor_quality.shp")
    out.to_file(dst)
    print(f"\nwrote {dst}")

    # ------------------------------------------------------------------ summary
    rows = []
    for src, s in cor.groupby("SRC"):
        km = s.LEN_M.sum() / 1000
        rows.append({
            "source": src, "lines": len(s), "km": round(km, 1),
            "dual4_km": round(s.DUAL4_M.sum() / 1000, 2),
            "dual6_km": round(s.DUAL6_M.sum() / 1000, 2),
            "dual8_km": round(s.DUAL8_M.sum() / 1000, 2),
            "dual12_km": round(s.DUAL12_M.sum() / 1000, 2),
            "dual6_pct": round(100 * s.DUAL6_M.sum() / s.LEN_M.sum(), 2),
            "wadi_km": round(s.WADI_M.sum() / 1000, 1),
            "wadi_pct": round(100 * s.WADI_M.sum() / s.LEN_M.sum(), 1),
            "plot_km": round(s.PLOT_M.sum() / 1000, 1),
            "plotin_km": round(s.PLOTIN_M.sum() / 1000, 1),
            "plotin_pct": round(100 * s.PLOTIN_M.sum() / s.LEN_M.sum(), 1),
            "dup_km": round(s.DUP_M.sum() / 1000, 1),
            "dup_pct": round(100 * s.DUP_M.sum() / s.LEN_M.sum(), 1),
            "med_len_m": round(s.LEN_M.median(), 1),
            "med_seg_m": round(s.MEDSEG_M.median(), 2),
            "med_v100m": round(s.VPER100M.median(), 1),
            "short_n": int(s.SHORT.sum()),
            "short_km": round(s.loc[s.SHORT == 1, "LEN_M"].sum() / 1000, 2),
            "dangle2_n": int((s.DANGLES == 2).sum()),
            "dangle2_km": round(s.loc[s.DANGLES == 2, "LEN_M"].sum() / 1000, 1),
            "unbuildable_km": round(s.loc[cor.QFLAG == "unbuildable", "LEN_M"].sum() / 1000, 1),
            "suspect_km": round(s.loc[cor.QFLAG == "suspect", "LEN_M"].sum() / 1000, 1),
            "ok_km": round(s.loc[cor.QFLAG == "ok", "LEN_M"].sum() / 1000, 1),
        })
    summ = pd.DataFrame(rows)
    tot = {"source": "TOTAL", "lines": len(cor)}
    for c in summ.columns:
        if c in ("source", "lines"):
            continue
        if c.endswith("_pct") or c.startswith("med_"):
            tot[c] = np.nan
        else:
            tot[c] = round(summ[c].sum(), 2)
    tot["dual6_pct"] = round(100 * cor.DUAL6_M.sum() / cor.LEN_M.sum(), 2)
    tot["wadi_pct"] = round(100 * cor.WADI_M.sum() / cor.LEN_M.sum(), 1)
    tot["plotin_pct"] = round(100 * cor.PLOTIN_M.sum() / cor.LEN_M.sum(), 1)
    tot["dup_pct"] = round(100 * cor.DUP_M.sum() / cor.LEN_M.sum(), 1)
    summ = pd.concat([summ, pd.DataFrame([tot])], ignore_index=True)
    summ.to_csv(os.path.join(OUT_RUN, "r1_corridor_quality.csv"), index=False)
    print("\n" + summ.to_string(index=False))
    print(f"\ntotal {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
