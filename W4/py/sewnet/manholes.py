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
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from shapely.ops import substring

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


def resolve_structures(nodes, pipes, sampler, units=None,
                       snap_m=None, offset_m=None):
    """ONE PHYSICAL OUTLET PER STRUCTURE (user rule 2026-08-18).

    A spanning tree gives every NODE one outgoing pipe, but two nodes can sit at the
    same physical point (road noding + cross-street augmentation produce keys a few
    centimetres apart). Two chambers at one point, each with its own outlet, IS a
    two-outlet junction on the ground — the thing the rule forbids.

    Two steps:
      1. merge every cluster of manholes within `snap_m` into one chamber — this makes
         the hidden fan-outs visible as nodes with out_degree > 1;
      2. resolve each fan-out: the main pipe (steepest hydraulic drop) keeps the
         chamber; every other outgoing pipe is trimmed back so it STARTS clear of it —
         at the next house connection along its own alignment, or `offset_m` if that
         connection lies nearer. A loser too short to keep a clear start is dropped
         (its street is served from the other end) and reported, never silently.
    """
    snap_m = C.MH_SNAP_M if snap_m is None else snap_m
    offset_m = C.FANOUT_OFFSET_M if offset_m is None else offset_m
    rep = {"merged": 0, "fanouts": 0, "offset_branches": 0, "dropped_branches": 0,
           "offsets_m": []}

    # ---------- 1. merge coincident chambers ----------
    keys = list(nodes.keys())
    pts = np.array([[nodes[k]["x"], nodes[k]["y"]] for k in keys])
    parent = {k: k for k in keys}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, j in cKDTree(pts).query_pairs(snap_m):
        ra, rb = find(keys[i]), find(keys[j])
        if ra != rb:
            parent[ra] = rb

    clusters = {}
    for k in keys:
        clusters.setdefault(find(k), []).append(k)

    deg = {k: 0 for k in keys}
    for p in pipes:
        deg[p["up"]] = deg.get(p["up"], 0) + 1
        deg[p["dn"]] = deg.get(p["dn"], 0) + 1

    rep_of = {}
    for members in clusters.values():
        if len(members) == 1:
            rep_of[members[0]] = members[0]
            continue
        keep = next((m for m in members if nodes[m]["kind"] == "outfall"), None)
        if keep is None:
            keep = max(members, key=lambda m: deg.get(m, 0))
        for m in members:
            rep_of[m] = keep
        rep["merged"] += len(members) - 1

    for p in list(pipes):
        p["up"], p["dn"] = rep_of[p["up"]], rep_of[p["dn"]]
        if p["up"] == p["dn"]:
            pipes.remove(p)
            continue
        cs = list(p["geom"].coords)
        cs[0] = (nodes[p["up"]]["x"], nodes[p["up"]]["y"])
        cs[-1] = (nodes[p["dn"]]["x"], nodes[p["dn"]]["y"])
        p["geom"] = LineString(cs)
        p["length"] = p["geom"].length
    for k in keys:
        if rep_of[k] != k:
            nodes.pop(k, None)

    # ---------- 2. re-derive the tree on the merged pipe set ----------
    # Merging can leave a chamber with several outgoing pipes AND can close a loop
    # (two chambers at one point may also be linked by a path). Both rules are
    # restored constructively: shortest-path tree to the outfall gives every chamber
    # exactly one outlet and no loops; whatever is left over is a loop-closing pipe.
    outfall_key = next((k for k, d in nodes.items() if d["kind"] == "outfall"), None)
    Gu = nx.Graph()
    for idx, p in enumerate(pipes):
        if Gu.has_edge(p["up"], p["dn"]):
            if Gu[p["up"]][p["dn"]]["length"] <= p["length"]:
                continue
        Gu.add_edge(p["up"], p["dn"], length=p["length"], idx=idx)
    dist, paths = nx.single_source_dijkstra(Gu, outfall_key, weight="length")

    keep_edge, tree_parent = {}, {}
    for n, path in paths.items():
        if len(path) < 2:
            continue
        parent = path[-2]
        tree_parent[n] = parent
        keep_edge[frozenset((n, parent))] = True

    kept, extras = [], []
    seen_edges = set()
    for p in pipes:
        ek = frozenset((p["up"], p["dn"]))
        if keep_edge.get(ek) and ek not in seen_edges:
            seen_edges.add(ek)
            # orient toward the outfall: the parent end is downstream
            child = p["up"] if tree_parent.get(p["up"]) == p["dn"] else p["dn"]
            parent = tree_parent.get(child)
            if parent is None:
                extras.append(p)
                continue
            if p["up"] != child:
                p["up"], p["dn"] = child, parent
                p["geom"] = LineString(list(p["geom"].coords)[::-1])
            kept.append(p)
        else:
            extras.append(p)

    unit_tree = cKDTree(np.array([[u["x"], u["y"]] for u in units])) if units else None

    def start_chainage(geom):
        """Where an offset branch begins: the next house connection along this
        alignment, or the fixed offset when that connection sits nearer."""
        if unit_tree is None:
            return offset_m
        d = offset_m
        while d < min(geom.length - 2.0, 60.0):
            pt = geom.interpolate(d)
            if len(unit_tree.query_ball_point([pt.x, pt.y], 30.0)) > 0:
                return d
            d += 2.0
        return offset_m

    pipes[:] = kept
    for p in extras:
        rep["fanouts"] += 1
        # drain toward whichever end is nearer the outfall; trim the other end clear
        du, dv = dist.get(p["up"], 1e18), dist.get(p["dn"], 1e18)
        geom = p["geom"] if dv <= du else LineString(list(p["geom"].coords)[::-1])
        dn_key = p["dn"] if dv <= du else p["up"]
        if geom.length < offset_m + 5.0:
            rep["dropped_branches"] += 1              # street served from its far end
            continue
        off = min(start_chainage(geom), geom.length - 5.0)
        seg = substring(geom, off, geom.length)
        if seg is None or seg.geom_type != "LineString" or seg.length < 5.0:
            rep["dropped_branches"] += 1
            continue
        hk = (round(seg.coords[0][0], 2), round(seg.coords[0][1], 2))
        if hk in nodes:
            rep["dropped_branches"] += 1
            continue
        nodes[hk] = {"x": seg.coords[0][0], "y": seg.coords[0][1],
                     "z": sampler.z(seg.coords[0][0], seg.coords[0][1]), "kind": "head"}
        pipes.append({"up": hk, "dn": dn_key, "geom": seg, "length": seg.length})
        rep["offset_branches"] += 1
        rep["offsets_m"].append(round(off, 1))

    # ---------- 3. every branch start must stand clear of other chambers ----------
    # Generic guarantee for the offset rule, wherever the head came from (tree head,
    # crest split, offset loser): slide the head along its own pipe until it is at
    # least offset_m from any other chamber; drop the branch if its pipe is too short
    # to keep a clear start (that street is served from its far end).
    N_PASSES = 8          # sliding a head can bring it near a different chamber; iterate
    for _pass in range(N_PASSES):
        # heads derived from LIVE degrees: step 2 may have flipped pipe directions, so
        # the stored `kind` is stale until the refresh at the end of this function
        indeg_l, outdeg_l = {}, {}
        for p in pipes:
            outdeg_l[p["up"]] = outdeg_l.get(p["up"], 0) + 1
            indeg_l[p["dn"]] = indeg_l.get(p["dn"], 0) + 1
        heads = [k for k in nodes
                 if indeg_l.get(k, 0) == 0 and outdeg_l.get(k, 0) == 1
                 and nodes[k]["kind"] != "outfall"]
        if not heads:
            break
        allk = list(nodes.keys())
        allpts = np.array([[nodes[k]["x"], nodes[k]["y"]] for k in allk])
        kd = cKDTree(allpts)
        out_of = {}
        for p in pipes:
            out_of.setdefault(p["up"], []).append(p)
        moved = 0
        for h in heads:
            if h not in nodes:                         # already moved/dropped this pass
                continue
            ps = [q for q in out_of.get(h, []) if q in pipes]
            if len(ps) != 1:
                continue
            p = ps[0]
            near = [allk[j] for j in kd.query_ball_point([nodes[h]["x"], nodes[h]["y"]], offset_m)
                    if allk[j] in nodes and allk[j] != h and allk[j] != p["dn"]]
            if not near:
                continue
            worst = min(math.dist((nodes[h]["x"], nodes[h]["y"]),
                                  (nodes[k]["x"], nodes[k]["y"])) for k in near)
            need = offset_m - worst + 0.5
            if _pass == N_PASSES - 1:
                need = max(need, offset_m)   # final pass: clear the full offset or drop
            if p["length"] - need < 5.0:
                pipes.remove(p)                        # cannot keep a clear start
                del nodes[h]
                rep["dropped_branches"] += 1
                moved += 1
                continue
            seg = substring(p["geom"], need, p["length"])
            if seg is None or seg.geom_type != "LineString" or seg.length < 5.0:
                pipes.remove(p)
                del nodes[h]
                rep["dropped_branches"] += 1
                moved += 1
                continue
            hk = (round(seg.coords[0][0], 2), round(seg.coords[0][1], 2))
            if hk in nodes:
                pipes.remove(p)
                del nodes[h]
                rep["dropped_branches"] += 1
                moved += 1
                continue
            nodes[hk] = {"x": seg.coords[0][0], "y": seg.coords[0][1],
                         "z": sampler.z(seg.coords[0][0], seg.coords[0][1]), "kind": "head"}
            del nodes[h]
            p["up"], p["geom"], p["length"] = hk, seg, seg.length
            rep["offset_branches"] += 1
            rep["offsets_m"].append(round(need, 1))
            moved += 1
        if moved == 0:
            break

    # ---------- 4. tidy: drop orphan chambers, refresh kinds ----------
    used = set()
    for p in pipes:
        used.add(p["up"])
        used.add(p["dn"])
    for k in list(nodes.keys()):
        if k not in used and nodes[k]["kind"] != "outfall":
            del nodes[k]
    indeg = {k: 0 for k in nodes}
    outdeg = {k: 0 for k in nodes}
    for p in pipes:
        outdeg[p["up"]] = outdeg.get(p["up"], 0) + 1
        indeg[p["dn"]] = indeg.get(p["dn"], 0) + 1
    for k, d in nodes.items():
        if d["kind"] == "outfall":
            continue
        if indeg.get(k, 0) == 0:
            d["kind"] = "head"
        elif d["kind"] != "spacing":        # spacing chambers keep their identity
            d["kind"] = "junction"

    # hard guarantees: no loops, one outlet per chamber (the two user rules)
    Gchk = nx.DiGraph()
    for p in pipes:
        Gchk.add_edge(p["up"], p["dn"])
    assert nx.is_directed_acyclic_graph(Gchk), "loop survived structure resolution"
    bad = [n for n in Gchk.nodes if Gchk.out_degree(n) > 1]
    assert not bad, f"{len(bad)} chambers still have more than one outlet"
    return rep


def place(Gd, outfall, sampler, units=None):
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

    # post-contraction re-split: endpoint re-anchoring can push a piece past the
    # spacing limit, and any future geometry quirk must self-heal here rather than
    # ship an unsplit reach (defense for the spacing audit, which checks the raw rule)
    resplit = [p for p in pipes if p["length"] > C.MH_SPLIT_LEN + 0.01]
    for p in resplit:
        pipes.remove(p)
        cuts = _split_points(p["geom"])
        if not cuts:
            n = int(math.ceil(p["length"] / C.MH_SPLIT_LEN))
            cuts = [p["length"] * k / n for k in range(1, n)]
        prev_key = p["up"]
        pcs = _cut(p["geom"], cuts)
        for i, piece in enumerate(pcs):
            if i == len(pcs) - 1:
                nxt_key = p["dn"]
            else:
                q = piece.coords[-1]
                nxt_key = (round(q[0], 2), round(q[1], 2))
                nodes[nxt_key] = {"x": q[0], "y": q[1], "z": sampler.z(q[0], q[1]),
                                  "kind": "spacing"}
            pipes.append({"up": prev_key, "dn": nxt_key, "geom": piece,
                          "length": piece.length})
            prev_key = nxt_key

    # one physical outlet per structure (merge coincident chambers, offset extra outlets)
    struct_report = resolve_structures(nodes, pipes, sampler, units)

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
    return nodes, pipes, struct_report


def _label_order(nodes, pipes, outfall):
    """Farthest-first ordering by pipe-network distance to the outfall (donor naming idea)."""
    Gp = nx.Graph()
    for p in pipes:
        Gp.add_edge(p["up"], p["dn"], length=p["length"])
    dist = nx.single_source_dijkstra_path_length(Gp, outfall, weight="length")
    return sorted(nodes.keys(), key=lambda n: -dist.get(n, 0.0))
