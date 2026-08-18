"""sewnet.manholes — S3: manholes on the directed tree, pipe reaches between them.

G203-p29-30: manholes at junctions, changes of grade/diameter/direction, end of each
lateral (tree heads), and regular spacing on straight runs. Initial split length
MH_SPLIT_LEN = 100 m satisfies every Tab-12 spacing class (100/120/150/200), so the
post-sizing spacing audit can only pass — conservative on manhole count at concept
stage, safe on compliance.

Output model:
  nodes:  {label, x, y, z_ground, kind}   kind in {outfall, junction, head, spacing, bend}
  pipes:  {label, up, dn, geom, length}   digitized up->dn (flow direction)
"""

import math
import networkx as nx
from shapely.geometry import LineString

from . import criteria as C


BEND_ANGLE_DEG = 45.0   # split a reach at interior vertices deflecting more than this
                        # (G203-p30: MH at change of direction; gentler kinks stay in-pipe
                        #  at concept stage — method choice, reported)


def _deflection(p0, p1, p2):
    a1 = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    a2 = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    d = abs(math.degrees(a2 - a1)) % 360.0
    return min(d, 360.0 - d)


def _split_points(geom):
    """Chainages where a reach must break: sharp bends first, then 100 m spacing."""
    coords = list(geom.coords)
    breaks = []
    acc = 0.0
    for i in range(1, len(coords) - 1):
        acc += math.dist(coords[i - 1], coords[i])
        if _deflection(coords[i - 1], coords[i], coords[i + 1]) > BEND_ANGLE_DEG:
            breaks.append(acc)
    # spacing splits between consecutive breaks (and ends)
    anchors = [0.0] + breaks + [geom.length]
    out = []
    for a, b in zip(anchors[:-1], anchors[1:]):
        span = b - a
        n = int(math.ceil(span / C.MH_SPLIT_LEN))
        for k in range(1, n):
            out.append(a + span * k / n)
    return sorted(set(round(c, 3) for c in (breaks + out)))


def _cut(geom, chainages):
    """Split a LineString at given chainages -> list of LineStrings covering it exactly."""
    pieces = []
    prev = 0.0
    for c in list(chainages) + [geom.length]:
        if c - prev < 0.5:
            prev = max(prev, c)
            continue
        seg_pts = []
        # walk vertices between prev and c, with interpolated endpoints
        seg_pts.append(geom.interpolate(prev))
        d = 0.0
        coords = list(geom.coords)
        for i in range(1, len(coords)):
            d += math.dist(coords[i - 1], coords[i])
            if prev < d < c:
                seg_pts.append(type(seg_pts[0])(coords[i]))
        seg_pts.append(geom.interpolate(c))
        pieces.append(LineString([(p.x, p.y) for p in seg_pts]))
        prev = c
    return pieces


def place(Gd, outfall, sampler):
    """Manholes + pipe reaches from the directed tree. Returns (nodes, pipes) dicts."""
    kind = {}
    for n in Gd.nodes:
        if n == outfall:
            kind[n] = "outfall"
        elif Gd.in_degree(n) == 0:
            kind[n] = "head"
        elif Gd.in_degree(n) > 1:
            kind[n] = "junction"
        else:
            kind[n] = "junction"   # single in + single out: grade/direction node kept

    nodes, pipes = {}, []
    for n, d in Gd.nodes(data=True):
        nodes[n] = {"x": d["x"], "y": d["y"], "z": d["z"], "kind": kind[n]}

    for u, v, d in Gd.edges(data=True):
        geom = d["geom"]
        cuts = _split_points(geom)
        pieces = _cut(geom, cuts) if cuts else [geom]
        prev_key = u
        acc = 0.0
        for i, piece in enumerate(pieces):
            acc += piece.length
            if i == len(pieces) - 1:
                nxt_key = v
            else:
                p = piece.coords[-1]
                nxt_key = (round(p[0], 2), round(p[1], 2))
                nodes[nxt_key] = {"x": p[0], "y": p[1], "z": sampler.z(p[0], p[1]),
                                  "kind": "spacing"}
            pipes.append({"up": prev_key, "dn": nxt_key, "geom": piece,
                          "length": piece.length})
            prev_key = nxt_key

    # deterministic labels: MH-#### upstream-to-downstream by network distance to outfall
    order = _label_order(nodes, pipes, outfall)
    labels = {}
    seq = 1
    for n in order:
        if nodes[n]["kind"] == "outfall":
            labels[n] = "OF-1"
        else:
            labels[n] = f"MH-{seq:04d}"
            seq += 1
    for n, lab in labels.items():
        nodes[n]["label"] = lab
    for i, p in enumerate(pipes):
        p["label"] = f"P-{i+1:04d}"
    return nodes, pipes


def _label_order(nodes, pipes, outfall):
    """Farthest-first ordering by pipe-network distance to the outfall (donor naming idea)."""
    Gp = nx.Graph()
    for p in pipes:
        Gp.add_edge(p["up"], p["dn"], length=p["length"])
    dist = nx.single_source_dijkstra_path_length(Gp, outfall, weight="length")
    return sorted(nodes.keys(), key=lambda n: -dist.get(n, 0.0))
