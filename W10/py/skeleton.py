"""Street centre lines from the space between platted blocks.

In a planned subdivision MoHUP has platted the plots but the road layer often has no
centre line at all: 10,823 plots in this study area have no road within 60 m. The street
reserve is not missing, though — it is the negative space between the plot blocks, and it
is drawn precisely, because the plot boundaries define it.

So the corridor is recovered rather than invented: rasterise the gap between blocks,
reduce it to a one-pixel skeleton, and trace that skeleton back to lines. Nothing here
guesses where a street runs; it reads where the plots left room for one.

The one judgement is what counts as a street rather than a gap between two houses, and
that is `MAX_STREET_M` — a gap wider than this is open desert, not a street reserve, and
is closed off before skeletonising so the skeleton does not wander across it.
"""
import math

import numpy as np
import networkx as nx
from scipy import ndimage
from shapely.geometry import LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree
from skimage.morphology import skeletonize, remove_small_objects

PIX_M = 1.0            # raster cell size
PLOT_GROW_M = 0.6      # plots grown by this before the gap is taken, closing survey slivers
MAX_STREET_M = 45.0    # a gap wider than this is not a street reserve
MIN_STREET_M = 3.0     # a gap narrower than this is a party boundary, not a street
SPUR_MIN_M = 20.0      # dead-end skeleton branch shorter than this is a rasterising artefact
SIMPLIFY_M = 1.5


def _rasterise(geoms, transform_origin, shape, pix=PIX_M):
    """Burn polygons into a boolean array. rasterio is not needed for this — the shapes
    are simple and a direct scan is faster than building a dataset."""
    from rasterio.features import rasterize
    from rasterio.transform import from_origin
    x0, y1 = transform_origin
    tr = from_origin(x0, y1, pix, pix)
    arr = rasterize([(g, 1) for g in geoms], out_shape=shape, transform=tr,
                    fill=0, dtype="uint8", all_touched=True)
    return arr.astype(bool), tr


def _skeleton_to_lines(skel, tr, simplify_m=SIMPLIFY_M):
    """Trace a one-pixel skeleton into LineStrings.

    Pixels become graph nodes with 8-connectivity. Every pixel whose degree is not 2 is a
    junction or an end; the runs between them are the lines.
    """
    ys, xs = np.nonzero(skel)
    if len(ys) == 0:
        return []
    idx = {(int(y), int(x)): i for i, (y, x) in enumerate(zip(ys, xs))}
    G = nx.Graph()
    G.add_nodes_from(idx.values())
    for (y, x), i in idx.items():
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                j = idx.get((y + dy, x + dx))
                if j is not None and j > i:
                    G.add_edge(i, j, w=math.hypot(dy, dx))

    inv = {i: (y, x) for (y, x), i in idx.items()}
    ends = [n for n in G if G.degree(n) != 2]
    lines, seen = [], set()

    def to_xy(n):
        y, x = inv[n]
        # cell centre
        return tr * (x + 0.5, y + 0.5)

    for s in ends:
        for nb in list(G.neighbors(s)):
            if (s, nb) in seen:
                continue
            path = [s, nb]
            seen.add((s, nb))
            seen.add((nb, s))
            prev, cur = s, nb
            while G.degree(cur) == 2:
                nxt = next(n for n in G.neighbors(cur) if n != prev)
                seen.add((cur, nxt))
                seen.add((nxt, cur))
                prev, cur = cur, nxt
                path.append(cur)
            pts = [to_xy(n) for n in path]
            if len(pts) >= 2:
                ln = LineString(pts).simplify(simplify_m, preserve_topology=False)
                if ln.length > 1.0:
                    lines.append(ln)

    # closed rings carry no degree!=2 pixel, so they are never entered above
    for comp in nx.connected_components(G):
        if all(G.degree(n) == 2 for n in comp) and len(comp) > 8:
            cyc = nx.cycle_basis(G.subgraph(comp))
            for c in cyc:
                pts = [to_xy(n) for n in c] + [to_xy(c[0])]
                ln = LineString(pts).simplify(simplify_m, preserve_topology=False)
                if ln.length > 1.0:
                    lines.append(ln)
    return lines


def prune_to_cover(lines, plots, frontage_m=40.0):
    """Cut the skeleton down to the least corridor that still serves every plot.

    The raw skeleton draws a loop right around every block, because the free space around
    an isolated block is a collar and the centre line of a collar is a ring. Both sides of
    that ring reach the same houses, so one of them is pipe nobody needs.

    So each line is tested: if every plot it serves is also served by another line, and
    removing it does not break the network in two, it goes. Longest first, because the
    expensive ones should have to justify themselves first. What survives is a connected
    network with every plot still within `frontage_m` of a corridor.
    """
    if not lines:
        return []
    tree = STRtree(lines)
    cover = {}                       # line index -> plots it serves
    served_by = {}                   # plot index -> line indices that serve it
    for pi, p in enumerate(plots):
        hits = [int(j) for j in tree.query(p.buffer(frontage_m))
                if lines[int(j)].distance(p) <= frontage_m]
        served_by[pi] = set(hits)
        for j in hits:
            cover.setdefault(j, set()).add(pi)

    # endpoints as graph nodes, so connectivity can be tested
    def node(pt):
        return (round(pt[0], 1), round(pt[1], 1))

    G = nx.MultiGraph()
    for i, ln in enumerate(lines):
        G.add_edge(node(ln.coords[0]), node(ln.coords[-1]), key=i, w=ln.length)

    alive = set(range(len(lines)))
    order = sorted(range(len(lines)), key=lambda i: -lines[i].length)
    for i in order:
        if i not in alive:
            continue
        # would any plot lose its last corridor?
        if any(len(served_by[pi] & alive) <= 1 for pi in cover.get(i, ())):
            continue
        u, v = None, None
        for a, b, k in G.edges(keys=True):
            if k == i:
                u, v = a, b
                break
        if u is None:
            continue
        G.remove_edge(u, v, key=i)
        # a self-loop or a parallel edge never disconnects anything; otherwise check
        if u != v and not nx.has_path(G, u, v):
            G.add_edge(u, v, key=i, w=lines[i].length)
            continue
        # dropping an edge can strand a node that carried nothing else
        for n in (u, v):
            if G.degree(n) == 0:
                G.remove_node(n)
        alive.discard(i)

    return [lines[i] for i in sorted(alive)]


def street_lines(plots, envelope, pix=PIX_M, max_street_m=MAX_STREET_M,
                 min_street_m=MIN_STREET_M, spur_min_m=SPUR_MIN_M):
    """Centre lines of the street space inside `envelope` and outside `plots`.

    plots    : iterable of polygons (the platted blocks)
    envelope : one polygon bounding the area to look inside
    """
    minx, miny, maxx, maxy = envelope.bounds
    pad = 4 * pix
    minx, miny, maxx, maxy = minx - pad, miny - pad, maxx + pad, maxy + pad
    w = int(math.ceil((maxx - minx) / pix))
    h = int(math.ceil((maxy - miny) / pix))
    if w * h > 60_000_000 or w < 4 or h < 4:
        return []

    env, tr = _rasterise([envelope], (minx, maxy), (h, w), pix)
    blk, _ = _rasterise([g.buffer(PLOT_GROW_M) for g in plots], (minx, maxy), (h, w), pix)

    gap = env & ~blk
    if not gap.any():
        return []

    # A gap wider than a street reserve is open ground. Erode by half the maximum street
    # width: anything that survives is too wide to be a street, and is taken out.
    r_max = max(1, int(round((max_street_m / 2.0) / pix)))
    wide = ndimage.binary_erosion(gap, ndimage.generate_binary_structure(2, 1),
                                  iterations=r_max)
    wide = ndimage.binary_dilation(wide, ndimage.generate_binary_structure(2, 1),
                                  iterations=r_max + 1)
    street = gap & ~wide

    # a gap narrower than a person is a boundary line, not a street
    r_min = max(1, int(round((min_street_m / 2.0) / pix)))
    street = ndimage.binary_opening(street, ndimage.generate_binary_structure(2, 1),
                                    iterations=r_min)
    street = remove_small_objects(street, min_size=int(40 / (pix * pix)))
    if not street.any():
        return []

    skel = skeletonize(street)
    lines = _skeleton_to_lines(skel, tr)

    # prune the short dead ends the rasterising leaves at every junction
    if lines:
        ends = {}
        for i, ln in enumerate(lines):
            for p in (ln.coords[0], ln.coords[-1]):
                ends.setdefault((round(p[0], 1), round(p[1], 1)), []).append(i)
        keep = []
        for i, ln in enumerate(lines):
            a = ends[(round(ln.coords[0][0], 1), round(ln.coords[0][1], 1))]
            b = ends[(round(ln.coords[-1][0], 1), round(ln.coords[-1][1], 1))]
            dangling = len(a) == 1 or len(b) == 1
            if dangling and ln.length < spur_min_m:
                continue
            keep.append(ln)
        lines = keep
    return lines
