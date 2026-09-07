"""sewnet.ground — Stage A, rule 1: read the ground along the streets.

Streets come from the draftsman's DXF. The terrain is read once, at a coarse cell, over the
area. Every street run (junction to junction) gets the fall between its ends and is pointed
downhill. A run with an interior crest or sag deeper than CREST_M is split there, so a ridge
street becomes two heads back to back (rule 6) and a hollow inside a street becomes an outlet
(rule 2) instead of being hidden between two junctions.
"""
import math

import ezdxf
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import linemerge, substring, unary_union
from shapely.strtree import STRtree


def key(pt, nd=2):
    return (round(float(pt[0]), nd), round(float(pt[1]), nd))


# ------------------------------------------------------------------ inputs
def read_dxf_lines(path, layers):
    """(LineString, tag) for every line on the named layers. Arcs become chords."""
    doc = ezdxf.readfile(path)
    out = []
    for e in doc.modelspace():
        lay = e.dxf.layer
        if lay not in layers:
            continue
        t = e.dxftype()
        if t == "LWPOLYLINE":
            raw = e.get_points()
            if any(abs(p[4]) > 1e-9 for p in raw):          # arcs -> chords
                from ezdxf import path as _path
                pts = [(v.x, v.y) for v in _path.make_path(e).flattening(0.5)]
            else:
                pts = [(p[0], p[1]) for p in raw]
        elif t == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif t == "POLYLINE":
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        else:
            continue
        pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 0.01]
        if len(pts) >= 2:
            out.append((LineString(pts), layers[lay]))
    return out


def built_envelope(sewer_shp, buffer_m):
    """The ground the built 2006 network serves: a buffer round every built line, holes
    filled. Returns the polygon and the built lines."""
    g = gpd.read_file(sewer_shp)
    g = g[g["OP_STATUE"].astype(str).isin(["1", "1.0"])]
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    env = unary_union([geom.buffer(buffer_m) for geom in g.geometry])
    parts = list(env.geoms) if hasattr(env, "geoms") else [env]
    filled = unary_union([Polygon(p.exterior) for p in parts])
    return filled, g


def clip_lines(lines, poly):
    out = []
    for g, lay in lines:
        if not g.intersects(poly):
            continue
        c = g.intersection(poly)
        parts = [c] if c.geom_type == "LineString" else \
            [p for p in getattr(c, "geoms", []) if p.geom_type == "LineString"]
        out += [(p, lay) for p in parts if p.length > 0.5]
    return out


# --------------------------------------------------------------- the graph
def snap_and_node(lines, snap_m=3.0, touch_m=0.3):
    """Close small gaps and node the streets.

    1. A line end that stops short of another line (0.3 to snap_m) is moved onto it and
       that line is split there.
    2. Line ends within snap_m of each other become one point.
    3. Everything is unioned, which nodes every crossing and touching point.
    Returns the noded pieces and the snapped source lines with their tags."""
    geoms = [g for g, _ in lines]
    lays = [l for _, l in lines]
    tree = STRtree(geoms)
    moved = [list(g.coords) for g in geoms]
    splits = {}
    for i, g in enumerate(geoms):
        for end in (0, -1):
            p = Point(g.coords[end])
            best = None
            for j in tree.query(p.buffer(snap_m)):
                if j == i:
                    continue
                d = geoms[j].distance(p)
                if d <= snap_m and (best is None or d < best[0]):
                    best = (d, j)
            if best and best[0] > touch_m:
                j = best[1]
                h = geoms[j]
                ch = h.project(p)
                q = h.interpolate(ch)
                if (q.distance(Point(h.coords[0])) > touch_m
                        and q.distance(Point(h.coords[-1])) > touch_m):
                    splits.setdefault(j, []).append(ch)
                moved[i][end] = (q.x, q.y)

    pieces = []
    for i, coords in enumerate(moved):
        g = LineString(coords)
        chs = sorted(set(round(c, 3) for c in splits.get(i, [])
                         if 0.05 < c < g.length - 0.05))
        if chs:
            prev = 0.0
            for c in chs + [g.length]:
                seg = substring(g, prev, c)
                prev = c
                if seg.length > 0.05:
                    pieces.append((seg, lays[i]))
        else:
            pieces.append((g, lays[i]))

    ends = []
    for k, (g, _) in enumerate(pieces):
        ends.append((k, 0, g.coords[0]))
        ends.append((k, -1, g.coords[-1]))
    xy = np.array([e[2] for e in ends], dtype=float)
    kd = cKDTree(xy)
    parent = list(range(len(ends)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in kd.query_pairs(snap_m):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups = {}
    for idx in range(len(ends)):
        groups.setdefault(find(idx), []).append(idx)
    new_xy = xy.copy()
    merged_groups = 0
    for members in groups.values():
        if len(members) > 1:
            new_xy[members] = xy[members].mean(axis=0)
            merged_groups += 1
    coords = [list(g.coords) for g, _ in pieces]
    for (k, end, _), p in zip(ends, new_xy):
        coords[k][end] = (float(p[0]), float(p[1]))
    snapped = []
    for (g, lay), cs in zip(pieces, coords):
        ls = LineString(cs)
        if ls.length > 0.05:
            snapped.append((ls, lay))

    merged = unary_union([g for g, _ in snapped])
    noded = [merged] if merged.geom_type == "LineString" else \
        [p for p in merged.geoms if p.geom_type == "LineString"]
    report = {"lines_in": len(lines), "ends_moved_onto_a_line": sum(len(v) for v in splits.values()),
              "end_clusters_merged": merged_groups, "noded_pieces": len(noded)}
    return noded, snapped, report


def build_runs(noded):
    """Chains of pieces between junctions (degree != 2). Returns (a, b, geom) with the
    geometry running from a to b, plus the degree of every node."""
    adj = {}
    for i, g in enumerate(noded):
        a, b = key(g.coords[0]), key(g.coords[-1])
        adj.setdefault(a, []).append(i)
        adj.setdefault(b, []).append(i)
    degree = {n: len(v) for n, v in adj.items()}
    junction = {n for n, d in degree.items() if d != 2}
    used = [False] * len(noded)

    def other_end(i, n):
        g = noded[i]
        a, b = key(g.coords[0]), key(g.coords[-1])
        return b if a == n else a

    chains = []
    for start in sorted(junction):
        for i in adj[start]:
            if used[i]:
                continue
            used[i] = True
            chain = [i]
            n = other_end(i, start)
            while n not in junction:
                nxt = [j for j in adj[n] if not used[j]]
                if not nxt:
                    break
                j = nxt[0]
                used[j] = True
                chain.append(j)
                n = other_end(j, n)
            chains.append((start, n, chain))
    for i in range(len(noded)):            # rings with no junction on them
        if used[i]:
            continue
        start = key(noded[i].coords[0])
        used[i] = True
        chain = [i]
        n = other_end(i, start)
        while n != start:
            nxt = [j for j in adj[n] if not used[j]]
            if not nxt:
                break
            j = nxt[0]
            used[j] = True
            chain.append(j)
            n = other_end(j, n)
        chains.append((start, n, chain))
        junction.add(start)

    runs = []
    for a, b, chain in chains:
        if len(chain) == 1:
            geom = noded[chain[0]]
        else:
            geom = linemerge(MultiLineString([noded[i] for i in chain]))
            if geom.geom_type != "LineString":
                geom = max(geom.geoms, key=lambda g: g.length)
        if key(geom.coords[0]) != a:
            geom = LineString(geom.coords[::-1])
        runs.append((a, b, geom))
    return runs, degree


# ---------------------------------------------------------------- terrain
class Ground:
    """The terrain read once over the area at a coarse cell, no-data filled from the
    nearest valid cell, sampled bilinearly."""

    def __init__(self, vrt_path, bounds, res=2.0, pad=100.0):
        ds = rasterio.open(vrt_path)
        l, b, r, t = bounds
        l, b, r, t = l - pad, b - pad, r + pad, t + pad
        w = from_bounds(l, b, r, t, ds.transform)
        f = res / ds.res[0]
        h, wd = int(w.height / f), int(w.width / f)
        arr = ds.read(1, window=w, out_shape=(h, wd),
                      resampling=Resampling.average).astype("float32")
        nod = ~np.isfinite(arr) | (arr < -1000)
        if ds.nodata is not None:
            nod |= arr == ds.nodata
        self.nodata_cells = int(nod.sum())
        if nod.any():
            idx = ndimage.distance_transform_edt(nod, return_distances=False,
                                                 return_indices=True)
            arr = arr[tuple(idx)]
        self.z = arr
        self.x0, self.y0 = ds.transform * (w.col_off, w.row_off)
        self.rx = (w.width / wd) * ds.res[0]
        self.ry = (w.height / h) * ds.res[1]
        self.res = res
        self.bounds = (l, b, r, t)
        self.transform = rasterio.transform.from_origin(self.x0, self.y0, self.rx, self.ry)
        self.crs = ds.crs

    def z_at(self, xs, ys):
        xs = np.asarray(xs, dtype=float)
        ys = np.asarray(ys, dtype=float)
        col = (xs - self.x0) / self.rx - 0.5
        row = (self.y0 - ys) / self.ry - 0.5
        return ndimage.map_coordinates(self.z, [row, col], order=1, mode="nearest")

    def z_node(self, x, y, r=4.0):
        """Median of the ground on a small disc, so a kerb or a hump at the junction does
        not set the level of the whole street."""
        ang = np.linspace(0, 2 * math.pi, 9)[:-1]
        xs = np.concatenate([[x], x + r * np.cos(ang)])
        ys = np.concatenate([[y], y + r * np.sin(ang)])
        return float(np.median(self.z_at(xs, ys)))


def profile(ground, geom, step):
    n = max(2, int(math.ceil(geom.length / step)) + 1)
    ch = np.linspace(0, geom.length, n)
    pts = [geom.interpolate(c) for c in ch]
    z = ground.z_at([p.x for p in pts], [p.y for p in pts])
    return ch, z


def split_at_extrema(ground, runs, crest_m, min_split_m, step):
    """Split a run at an interior crest or sag deeper than crest_m relative to BOTH ends.
    Returns runs as (a, b, geom, how) and the list of new nodes with their kind."""
    out = []
    new_nodes = []
    stack = [(a, b, g, "") for a, b, g in runs]
    while stack:
        a, b, g, how = stack.pop()
        if g.length < 2 * min_split_m:
            out.append((a, b, g, how))
            continue
        ch, z = profile(ground, g, step)
        if len(z) < 3:
            out.append((a, b, g, how))
            continue
        zi = z[1:-1]
        imax = int(np.argmax(zi)) + 1
        imin = int(np.argmin(zi)) + 1
        endmax, endmin = max(z[0], z[-1]), min(z[0], z[-1])
        cand = None
        if z[imax] - endmax > crest_m and min_split_m <= ch[imax] <= g.length - min_split_m:
            cand = (imax, "crest")
        elif endmin - z[imin] > crest_m and min_split_m <= ch[imin] <= g.length - min_split_m:
            cand = (imin, "sag")
        if cand is None:
            out.append((a, b, g, how))
            continue
        i, kind = cand
        g1 = substring(g, 0, ch[i])
        g2 = substring(g, ch[i], g.length)
        m = key(g1.coords[-1])
        g2 = LineString([g1.coords[-1]] + list(g2.coords)[1:])
        new_nodes.append((m, kind))
        stack.append((a, m, g1, kind))
        stack.append((m, b, g2, kind))
    return out, new_nodes


def orient(runs, znode, flat_pct, level_m):
    """Point every run downhill and classify it."""
    recs = []
    for a, b, g, how in runs:
        za, zb = znode[a], znode[b]
        if za < zb or (za == zb and a > b):
            a, b = b, a
            g = LineString(g.coords[::-1])
            za, zb = zb, za
        fall = za - zb
        L = g.length
        grad = 100.0 * fall / L if L > 0 else 0.0
        cls = "LEVEL" if fall < level_m else ("FLAT" if grad < flat_pct else "NORMAL")
        recs.append({"up": a, "dn": b, "geom": g, "z_up": za, "z_dn": zb, "fall": fall,
                     "len": L, "grad": grad, "cls": cls, "split": how})
    return recs


def tag_layers(runs, source_lines):
    """Which DXF layer a run came from: the nearest source line at its midpoint."""
    geoms = [g for g, _ in source_lines]
    tags = [t for _, t in source_lines]
    tree = STRtree(geoms)
    for r in runs:
        m = r["geom"].interpolate(0.5, normalized=True)
        idx = tree.nearest(m)
        r["layer"] = tags[idx] if idx is not None else ""
    return runs
