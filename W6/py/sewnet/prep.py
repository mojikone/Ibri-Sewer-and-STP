"""sewnet.prep — S1: boundary repair, road clip/node, dual-carriageway collapse, terrain sampler.

Data defects handled here (phaseA_data.md): invalid boundary ring, zero-length clip
slivers, class_v4 UTF-8 encoding. Dual collapse ports W2 s3:37-83 and ADDS the
geometry re-anchoring W2 never had: collapsed edges are re-drawn onto the merged
node coordinates so manholes land on the actual corridor.
"""

import math
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from shapely.validation import make_valid
from scipy.spatial import cKDTree


def load_boundary(path):
    """Single valid Polygon from the (defective) boundary shapefile."""
    gdf = gpd.read_file(path)
    geom = gdf.geometry.iloc[0]
    if not geom.is_valid:
        geom = make_valid(geom)
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        geom = unary_union(polys)
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda g: g.area)
    return geom


def clip_roads(roads_path, boundary, sliver_m=0.5, crs_epsg=32640):
    """Roads clipped to the boundary, split into single lines, tiny bits dropped.

    Keeps the columns the treatment stage needs: `dual` (0 normal, 1 dual carriageway,
    2 two-lane one-side-only) and `StrCls` (road class). The file's own .prj is a
    hand-written UTM description rather than an EPSG code, so the CRS is set explicitly
    (user confirmed EPSG:32640)."""
    roads = gpd.read_file(roads_path)
    roads = roads.set_crs(crs_epsg, allow_override=True)
    roads = roads[roads.geometry.notna() & ~roads.geometry.is_empty]
    keep = [c for c in ("dual", "StrCls", "TYPE", "Name_Engli") if c in roads.columns]
    roads = roads[keep + ["geometry"]]
    clipped = gpd.clip(roads, boundary).explode(index_parts=False)
    clipped = clipped[clipped.geometry.geom_type == "LineString"]
    clipped = clipped[clipped.geometry.length > sliver_m]
    return clipped.reset_index(drop=True)


class HazardSampler:
    """Reads the 50-year flood hazard grid. Classes 4/5/6 mean wadi — no pipes or
    chambers there. 1/2/3 are safe. No value at all means dry (user 2026-08-19)."""

    def __init__(self, path, bounds, pad=200.0):
        self.ok = False
        try:
            self.ds = rasterio.open(path)
            l, b, r, t = bounds
            self.window = from_bounds(l - pad, b - pad, r + pad, t + pad, self.ds.transform)
            self.arr = self.ds.read(1, window=self.window)
            self.tr = self.ds.window_transform(self.window)
            self.ok = True
        except Exception as e:                       # missing file must not stop a design run
            print(f"  (hazard grid unavailable: {e})")

    def klass(self, x, y):
        """Hazard class at a point; 0 where there is no value (dry)."""
        if not self.ok:
            return 0
        col = int((x - self.tr.c) / self.tr.a)
        row = int((y - self.tr.f) / self.tr.e)
        if row < 0 or col < 0 or row >= self.arr.shape[0] or col >= self.arr.shape[1]:
            return 0
        v = self.arr[row, col]
        return 0 if (v is None or v < 0 or v != v) else int(v)

    def is_wadi(self, x, y, wadi_classes=(4, 5, 6)):
        return self.klass(x, y) in wadi_classes


def node_roads(lines, min_len=0.1):
    """unary_union noding: every crossing becomes a shared endpoint (donor roads.py pattern)."""
    merged = unary_union(list(lines.geometry))
    if merged.geom_type == "LineString":
        segs = [merged]
    else:
        segs = [g for g in merged.geoms if g.geom_type == "LineString"]
    return [s for s in segs if s.length > min_len]


class TerrainSampler:
    """Windowed VRT sampler — never loads the 0.5 m raster whole (it is tens of GB).
    Loads one window covering the AOI bounds (+pad) into memory once; bilinear lookup.
    HARD-FAILS on nodata/out-of-window (PLAN §3: no silent 0.0 elevations)."""

    def __init__(self, vrt_path, bounds, pad=200.0):
        self.ds = rasterio.open(vrt_path)
        l, b, r, t = bounds
        self.window = from_bounds(l - pad, b - pad, r + pad, t + pad, self.ds.transform)
        self.arr = self.ds.read(1, window=self.window).astype(np.float64)
        self.tr = self.ds.window_transform(self.window)
        self.nodata = self.ds.nodata if self.ds.nodata is not None else -9999.0

    def z(self, x, y):
        """Bilinear elevation. Raises on nodata under the sample point."""
        col = (x - self.tr.c) / self.tr.a - 0.5
        row = (y - self.tr.f) / self.tr.e - 0.5
        r0, c0 = int(math.floor(row)), int(math.floor(col))
        if r0 < 0 or c0 < 0 or r0 + 1 >= self.arr.shape[0] or c0 + 1 >= self.arr.shape[1]:
            raise ValueError(f"terrain sample outside window at ({x:.1f}, {y:.1f})")
        block = self.arr[r0:r0 + 2, c0:c0 + 2]
        if np.any(block == self.nodata) or np.any(~np.isfinite(block)):
            raise ValueError(f"terrain NODATA under sample at ({x:.1f}, {y:.1f})")
        fr, fc = row - r0, col - c0
        return float(block[0, 0] * (1 - fr) * (1 - fc) + block[0, 1] * (1 - fr) * fc
                     + block[1, 0] * fr * (1 - fc) + block[1, 1] * fr * fc)

    def profile(self, line, step=5.0):
        """(chainage, x, y, z) along a shapely line every `step` m incl. both ends."""
        n = max(2, int(math.ceil(line.length / step)) + 1)
        out = []
        for i in range(n):
            d = min(line.length, i * step) if i < n - 1 else line.length
            p = line.interpolate(d)
            out.append((d, p.x, p.y, self.z(p.x, p.y)))
        return out


def detect_duals(segs, min_len=40.0, max_bearing_diff=12.0, off_lo=6.0, off_hi=45.0):
    """Flag parallel-offset dual-carriageway segments (W1 s1:64-97 logic)."""
    def bearing(g):
        (x0, y0), (x1, y1) = g.coords[0], g.coords[-1]
        return math.degrees(math.atan2(y1 - y0, x1 - x0)) % 180.0

    cands = [i for i, g in enumerate(segs) if g.length >= min_len]
    mids = np.array([[segs[i].interpolate(0.5, normalized=True).x,
                      segs[i].interpolate(0.5, normalized=True).y] for i in cands]) if cands else np.empty((0, 2))
    dual = set()
    if len(cands) > 1:
        tree = cKDTree(mids)
        for a_idx, i in enumerate(cands):
            for b_idx in tree.query_ball_point(mids[a_idx], off_hi):
                if b_idx <= a_idx:
                    continue
                j = cands[b_idx]
                db = abs(bearing(segs[i]) - bearing(segs[j]))
                db = min(db, 180.0 - db)
                dist = segs[i].distance(segs[j])
                if db <= max_bearing_diff and off_lo <= dist <= off_hi:
                    dual.add(i); dual.add(j)
    return dual


def collapse_duals(segs, dual_idx, merge_m=35.0):
    """Merge dual-carriageway twin corridors into one (W2 s3:37-83 + NEW re-anchoring).

    Union-find clusters nodes touched by dual segments within merge_m; every cluster
    maps to its centroid; segment endpoints re-anchored to the mapped coordinates and
    twin duplicates (same mapped endpoints) keep only the shortest representative.
    Interior vertices of re-anchored segments are blended so the line actually ends
    at the new endpoints (the W2 caveat fixed)."""
    def key(pt):
        return (round(pt[0], 2), round(pt[1], 2))

    dual_nodes = []
    for i in dual_idx:
        dual_nodes.append(segs[i].coords[0]); dual_nodes.append(segs[i].coords[-1])
    parent = {}

    def find(a):
        while parent.get(a, a) != a:
            parent[a] = parent.get(parent[a], parent[a])
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    keys = [key(p) for p in dual_nodes]
    for k in keys:
        parent.setdefault(k, k)
    if keys:
        arr = np.array([list(k) for k in keys])
        tree = cKDTree(arr)
        for a, b in tree.query_pairs(merge_m):
            union(keys[a], keys[b])

    clusters = {}
    for k in keys:
        clusters.setdefault(find(k), []).append(k)
    remap = {}
    for root, members in clusters.items():
        cx = sum(m[0] for m in members) / len(members)
        cy = sum(m[1] for m in members) / len(members)
        for m in members:
            remap[m] = (cx, cy)

    def anchored(g):
        a, b = key(g.coords[0]), key(g.coords[-1])
        na, nb = remap.get(a, a), remap.get(b, b)
        coords = list(g.coords)
        if (na, nb) == (a, b):
            return LineString(coords), a, b
        # blend interior vertices toward the moved endpoints (linear taper)
        n = len(coords)
        out = []
        for idx, (x, y) in enumerate(coords):
            t = idx / (n - 1) if n > 1 else 0.0
            dxa, dya = na[0] - a[0], na[1] - a[1]
            dxb, dyb = nb[0] - b[0], nb[1] - b[1]
            out.append((x + dxa * (1 - t) + dxb * t, y + dya * (1 - t) + dyb * t))
        return LineString(out), key(out[0]), key(out[-1])

    seen = {}
    result = []
    for i, g in enumerate(segs):
        line, ka, kb = anchored(g)
        if ka == kb:                       # twin cross-link collapsed to a point
            continue
        ekey = tuple(sorted((ka, kb)))
        if ekey in seen:                   # parallel twin: keep shortest
            j = seen[ekey]
            if line.length < result[j].length:
                result[j] = line
            continue
        seen[ekey] = len(result)
        result.append(line)
    return result


def prepare(roads_path, boundary_path, terrain_path, sliver_m=0.5, dual_merge_m=35.0,
            hazard_path=None):
    """Stage 1: read everything in and hand back clean road lines.

    The road lines keep their `dual` and `StrCls` values, because the treatment stage
    decides what to exclude from those. Dual carriageways are NO LONGER merged into one
    line here — from W5 they are removed entirely, so merging them would be wasted work
    (user 2026-08-19)."""
    boundary = load_boundary(boundary_path)
    clipped = clip_roads(roads_path, boundary, sliver_m)
    attrs = {}
    pieces = []
    for _, row in clipped.iterrows():
        pieces.append(row.geometry)
        attrs[id(row.geometry)] = {"dual": int(row.get("dual", 0) or 0),
                                   "strcls": str(row.get("StrCls", "") or "")}
    sampler = TerrainSampler(terrain_path, boundary.bounds)
    hazard = HazardSampler(hazard_path, boundary.bounds) if hazard_path else None
    stats = {"boundary_ha": boundary.area / 1e4, "segs_raw": len(pieces),
             "len_km": sum(s.length for s in pieces) / 1000.0,
             "dual_1": sum(1 for a in attrs.values() if a["dual"] == 1),
             "dual_2": sum(1 for a in attrs.values() if a["dual"] == 2)}
    return pieces, attrs, boundary, sampler, hazard, stats
