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
    """Split a LineString at given chainages -> pieces covering it EXACTLY end to end.
    Cuts closer than 0.5 m to either end or to each other are dropped (the cut, never
    the piece) — the chain from first to last vertex is always complete."""
    L = geom.length
    cuts = []
    for c in sorted(set(round(c, 3) for c in chainages)):
        if c <= 0.5 or c >= L - 0.5:
            continue
        if cuts and c - cuts[-1] < 0.5:
            continue
        cuts.append(c)
    coords = list(geom.coords)
    cum = [0.0]
    for i in range(1, len(coords)):
        cum.append(cum[-1] + math.dist(coords[i - 1], coords[i]))
    pieces = []
    anchors = [0.0] + cuts + [L]
    for a, b in zip(anchors[:-1], anchors[1:]):
        pa, pb = geom.interpolate(a), geom.interpolate(b)
        pts = [(pa.x, pa.y)]
        pts += [coords[i] for i, d in enumerate(cum) if a < d < b]
        pts.append((pb.x, pb.y))
        pieces.append(LineString(pts))
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

    # contract sub-2 m reaches: manholes ~1.2 m across cannot sit 0.6 m apart — noding
    # debris where several streets meet within a metre becomes ONE manhole (method choice)
    MIN_REACH = 2.0
    changed = True
    while changed:
        changed = False
        for p in list(pipes):
            if p["length"] >= MIN_REACH:
                continue
            u, v = p["up"], p["dn"]
            pipes.remove(p)
            changed = True
            if u == v:
                break
            keep, drop = (u, v) if nodes[u]["kind"] == "outfall" else (v, u)
            kx, ky = nodes[keep]["x"], nodes[keep]["y"]
            for q in pipes:
                if q["up"] == drop:
                    q["up"] = keep
                    cs = list(q["geom"].coords)
                    q["geom"] = LineString([(kx, ky)] + cs[1:])
                if q["dn"] == drop:
                    q["dn"] = keep
                    cs = list(q["geom"].coords)
                    q["geom"] = LineString(cs[:-1] + [(kx, ky)])
                q["length"] = q["geom"].length
            if nodes[drop]["kind"] == "junction" and nodes[keep]["kind"] != "outfall":
                nodes[keep]["kind"] = "junction"
            del nodes[drop]
            break

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
