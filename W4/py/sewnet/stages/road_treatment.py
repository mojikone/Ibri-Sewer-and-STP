"""RoadTreatment — S1b: raw road centrelines -> sewer corridors.

Why this stage exists (user 2026-08-18): fed raw centrelines, the pipeline put a chamber
wherever the road data happened to break. On the test area 576 of 2,137 chambers (27 %)
sat at near-collinear breaks — 465 of them at under 2 degrees. Those are artefacts of the
survey data, not design decisions, and each one costs a manhole.

Treatments, in order:
  1. de-duplicate vertices (ROAD_DEDUP_M) — the artefact that made 66 reaches read as
     "180 degree bends" in the first compliance check;
  2. simplify (ROAD_SIMPLIFY_M) — survey jitter, without moving the centreline;
  3. dissolve degree-2 nodes whose deflection is under ROAD_COLLINEAR_DEG — a straight
     street broken into three pieces becomes one corridor;
  4. collapse roundabouts — a small circular ring is not a sewer corridor; the ring is
     removed and its legs reattach to the centre;
  5. drop dangling stubs shorter than STUB_MIN_M with no plot frontage;
  6. classify main roads (excluded as LONGITUDINAL corridors, still crossable) — derived
     here because the road layer carries no class attribute; overridable by a user layer.

The output is written as a REVIEWABLE layer (corridors.shp) so the corridor decisions can
be inspected and hand-edited in QGIS before any design runs.
"""

import math

import networkx as nx
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import linemerge
from shapely.strtree import STRtree

from ..criteria import DEFAULT
from ..model import key_of


def _bearing(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _turn_deg(a, b, c):
    d = abs(math.degrees(_bearing(b, c) - _bearing(a, b))) % 360.0
    return min(d, 360.0 - d)


class RoadTreatment:
    def __init__(self, sampler=None, crit=DEFAULT, main_road_layer=None):
        self.sampler = sampler
        self.crit = crit
        self.main_road_layer = main_road_layer      # user-supplied classification, if any
        self.report = {}
        self.corridors = []
        self.excluded = []

    # ---------------- 1-2. vertex hygiene ----------------
    def _clean(self, segs):
        """De-duplicate interior vertices and simplify. The TERMINAL vertex is always
        preserved: dropping it moves the corridor endpoint beyond the 1 cm node key and
        detaches the segment from the road graph (review RT-5)."""
        C = self.crit
        out = []
        removed = 0
        for g in segs:
            cs = list(g.coords)
            keep = [cs[0]]
            for p in cs[1:-1]:
                if math.dist(keep[-1], p) >= C.ROAD_DEDUP_M:
                    keep.append(p)
                else:
                    removed += 1
            if math.dist(keep[-1], cs[-1]) < C.ROAD_DEDUP_M and len(keep) > 1:
                keep.pop()                      # the near-duplicate goes, the endpoint stays
                removed += 1
            keep.append(cs[-1])
            line = LineString(keep).simplify(C.ROAD_SIMPLIFY_M, preserve_topology=False)
            if line.length > 0.5 and line.coords[0] != line.coords[-1]:
                out.append(line)
        return out, removed

    # ---------------- 4. roundabouts ----------------
    def _collapse_roundabouts(self, segs, units=None):
        """Collapse roundabouts — and ONLY roundabouts.

        The first version tested circularity 4*pi*A/P^2 >= 0.60, which is vacuous: a
        square scores 0.785 and a triangle 0.605, so every small city block passed and 12
        of 15 'roundabouts' were residential blocks with plots inside them (review RT-2).
        Shape alone cannot tell a roundabout from a block. Evidence can:

          * NO cadastral load unit inside the ring — a roundabout encircles carriageway,
            a block encircles plots. This is the decisive test;
          * equivalent radius <= ROUNDABOUT_R_MAX — roundabouts are small;
          * every ring node carries a leg leaving the ring (an approach arm);
          * curved edges: mean absolute deflection per interior vertex above a threshold,
            or enough nodes that the ring is polygonal-round rather than a 4-corner block.
        """
        C = self.crit
        G = nx.MultiGraph()
        for i, g in enumerate(segs):
            G.add_edge(key_of(*g.coords[0]), key_of(*g.coords[-1]), idx=i, length=g.length)
        from shapely.geometry import Polygon
        unit_pts = [Point(u.x, u.y) for u in (units or [])]
        utree = STRtree(unit_pts) if unit_pts else None

        deg = {}
        for g in segs:
            for k in (key_of(*g.coords[0]), key_of(*g.coords[-1])):
                deg[k] = deg.get(k, 0) + 1

        drop, rings, slivers = set(), 0, 0
        rejected = {"plots_inside": 0, "too_big": 0, "no_legs": 0, "straight_edges": 0}
        remap = {}
        for cyc in nx.cycle_basis(nx.Graph(G)):
            if len(cyc) < 3:
                continue
            ring_edges, perim, ring_geoms = [], 0.0, []
            ok = True
            for a, b in zip(cyc, cyc[1:] + [cyc[0]]):
                if not G.has_edge(a, b):
                    ok = False
                    break
                e = min(G[a][b].values(), key=lambda d: d["length"])
                ring_edges.append(e["idx"])
                ring_geoms.append(segs[e["idx"]])
                perim += e["length"]
            if not ok or perim > C.ROUNDABOUT_PERIM_M:
                continue

            try:
                poly = Polygon([(k[0], k[1]) for k in cyc])
                if not poly.is_valid:
                    poly = poly.buffer(0)
            except Exception:
                continue
            if poly.is_empty or poly.area <= 0:
                continue

            r_eq = math.sqrt(poly.area / math.pi)
            if r_eq > C.ROUNDABOUT_R_MAX:
                rejected["too_big"] += 1
                continue
            # decisive test: a roundabout encircles carriageway, a block encircles plots
            if utree is not None and len(utree.query(poly)) > 0:
                inside = [p for p in utree.query(poly) if poly.contains(unit_pts[p])] \
                    if len(unit_pts) else []
                if inside:
                    rejected["plots_inside"] += 1
                    continue
            arms = sum(1 for k in cyc if deg.get(k, 0) > 2)   # approach arms leaving the ring
            if arms < 2:
                rejected["no_legs"] += 1
                continue
            # curved arcs, or enough nodes that it is round rather than a 4-corner block
            curvy = len(cyc) >= 6
            if not curvy:
                turns = []
                for g in ring_geoms:
                    cs = list(g.coords)
                    for i in range(1, len(cs) - 1):
                        turns.append(_turn_deg(cs[i - 1], cs[i], cs[i + 1]))
                curvy = bool(turns) and (sum(turns) / len(turns)) > 5.0
            if not curvy:
                rejected["straight_edges"] += 1
                continue

            centre = key_of(sum(k[0] for k in cyc) / len(cyc),
                            sum(k[1] for k in cyc) / len(cyc))
            for k in cyc:
                remap[k] = centre
            drop.update(ring_edges)
            # honest labelling: a ring a few metres across is noding debris (typically
            # where dual carriageways meet), not a roundabout. Both collapse to a point,
            # but the report must not call a 2 m triangle a roundabout
            if r_eq < 5.0:
                slivers += 1
            else:
                rings += 1

        out = []
        for i, g in enumerate(segs):
            if i in drop:
                continue
            a, b = key_of(*g.coords[0]), key_of(*g.coords[-1])
            na, nb = remap.get(a, a), remap.get(b, b)
            touched = (na != a) or (nb != b)
            if na == nb:
                continue                                   # leg entirely inside the ring
            cs = list(g.coords)
            if na != a:
                cs[0] = (na[0], na[1])
            if nb != b:
                cs[-1] = (nb[0], nb[1])
            line = LineString(cs)
            # the sub-metre filter applies ONLY to legs this step re-anchored. Applied to
            # every segment it silently deleted legitimate short connectors — one of them
            # the sole bridge to a 164-node sub-network (review RT-1)
            if touched and line.length <= 1.0:
                continue
            out.append(line)
        self.report_rejected = rejected
        self.report_slivers = slivers
        return out, rings

    # ---------------- 3. dissolve collinear breaks ----------------
    def _dissolve(self, segs, protect=None):
        """Join lines at every degree-2 node whose deflection is under the collinear
        threshold: a straight street broken into pieces becomes one corridor, so no
        chamber is placed there."""
        C = self.crit
        protect = set(protect or ())
        changed = True
        joined = 0
        while changed:
            changed = False
            ends = {}
            for i, g in enumerate(segs):
                ends.setdefault(key_of(*g.coords[0]), []).append((i, "s"))
                ends.setdefault(key_of(*g.coords[-1]), []).append((i, "e"))
            used = set()
            merged = []
            consumed = set()
            for node, att in ends.items():
                if len(att) != 2 or node in protect:
                    continue
                (i, si), (j, sj) = att
                if i == j or i in consumed or j in consumed:
                    continue
                gi, gj = segs[i], segs[j]
                ci = list(gi.coords) if si == "e" else list(gi.coords)[::-1]
                cj = list(gj.coords) if sj == "s" else list(gj.coords)[::-1]
                if _turn_deg(ci[-2], ci[-1], cj[1]) > C.ROAD_COLLINEAR_DEG:
                    continue
                merged.append(LineString(ci + cj[1:]))
                consumed.update({i, j})
                joined += 1
                changed = True
            segs = merged + [g for k, g in enumerate(segs) if k not in consumed]
        return segs, joined

    # ---------------- 5. stubs ----------------
    def _drop_stubs(self, segs, units):
        C = self.crit
        if not units:
            return segs, 0
        tree = STRtree([Point(u.x, u.y) for u in units])
        deg = {}
        for g in segs:
            for k in (key_of(*g.coords[0]), key_of(*g.coords[-1])):
                deg[k] = deg.get(k, 0) + 1
        out, dropped = [], 0
        for g in segs:
            a, b = key_of(*g.coords[0]), key_of(*g.coords[-1])
            dangling = deg.get(a, 0) == 1 or deg.get(b, 0) == 1
            if dangling and g.length < C.STUB_MIN_M and \
                    len(tree.query(g.buffer(C.CROSS_STREET_FRONTAGE))) == 0:
                dropped += 1
                continue
            out.append(g)
        return out, dropped

    # ---------------- 6. main roads ----------------
    def classify_main_roads(self, segs):
        """No class attribute exists in the road data (verified: the layer carries only ids,
        dates and a name populated for 13 % of features), so main-road status is DERIVED
        and written to the corridor layer for review. Longitudinal pipes are excluded from
        main roads; crossings remain allowed (G1-p85 trenchless).

        Signal used here: betweenness centrality on the corridor graph — the through-routes
        that carry the network. A user-supplied classification overrides it entirely.
        """
        if self.main_road_layer is not None:
            tree = STRtree(list(self.main_road_layer.geometry))
            flags = []
            for g in segs:
                hits = tree.query(g.buffer(5.0))
                flags.append(bool(len(hits)) and g.length > 30.0)
            return flags

        G = nx.Graph()
        for i, g in enumerate(segs):
            a, b = key_of(*g.coords[0]), key_of(*g.coords[-1])
            if a != b:
                G.add_edge(a, b, idx=i, length=g.length)
        if len(G) < 10:
            return [False] * len(segs)
        bt = nx.edge_betweenness_centrality(G, k=min(300, len(G)), weight="length", seed=42)
        vals = np.array(list(bt.values()))
        thr = np.quantile(vals, 0.97) if len(vals) else 1.0
        main_idx = {G[u][v]["idx"] for (u, v), b in bt.items() if b >= thr}
        return [i in main_idx for i in range(len(segs))]

    # ---------------- stage entry point ----------------
    def run(self, segs, units=None, out_path=None, protect=None):
        """protect: node keys that must survive dissolving (the outfall candidate — a
        degree-2 node would otherwise be dissolved away and the true low point lost,
        review RT-7)."""
        n0 = len(segs)
        km0 = sum(g.length for g in segs) / 1000.0

        segs, dedup = self._clean(segs)
        segs, rings = self._collapse_roundabouts(segs, units)
        segs, joined = self._dissolve(segs, protect)
        segs, stubs = self._drop_stubs(segs, units or [])
        main_flags = self.classify_main_roads(segs)

        self.corridors = segs
        self.report = {
            "segments_in": n0, "segments_out": len(segs),
            "km_in": round(km0, 2), "km_out": round(sum(g.length for g in segs) / 1000.0, 2),
            "duplicate_vertices_removed": dedup,
            "roundabouts_collapsed": rings,
            "sliver_rings_collapsed": getattr(self, "report_slivers", 0),
            "rings_rejected": getattr(self, "report_rejected", {}),
            "collinear_joins": joined,
            "stubs_dropped": stubs,
            "main_road_segments": int(sum(main_flags)),
        }
        if out_path:
            self._write(out_path, segs, main_flags)
        return segs

    def _write(self, path, segs, main_flags):
        """Reviewable corridor layer — open it in QGIS, edit, and freeze it as the input."""
        import geopandas as gpd
        gpd.GeoDataFrame({
            "CORR_ID": [f"C-{i+1:05d}" for i in range(len(segs))],
            "LEN_M": [round(g.length, 2) for g in segs],
            "MAIN_ROAD": [int(m) for m in main_flags],
            "ELIGIBLE": [0 if m else 1 for m in main_flags],
        }, geometry=segs, crs="EPSG:32640").to_file(path, encoding="utf-8")
