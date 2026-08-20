"""RoadTreatment — turn raw road lines into sewer corridors.

Road lines describe how cars move. A sewer follows the street but joins at a point, so
the road file has to be cleaned first. Fed raw lines, the pipeline put a chamber wherever
the survey data happened to break: 576 of 2,137 chambers (27 %) sat on breaks in a
straight street, 465 of them under 2 degrees.

What this stage does, in order (rules agreed with the user 2026-08-18/19):

 1. tidy the points on each line (drop near-duplicates, smooth survey wobble)
 2. drop dual carriageways (`dual` = 1) — we cannot open them, not even for the trunk
 3. keep one side only of a two-lane pair (`dual` = 2)
 4. drop roundabouts — they collect no sewage
 5. drop traffic links (turning fillets, slip roads, diagonal connectors)
 6. join a straight street back into one line between its intersections
 7. drop short dead ends that serve no plot
 8. keep the road class on every corridor so the output can be checked in QGIS

Everything removed is written to the corridor file with a reason, so it can be reviewed
and overruled rather than quietly disappearing.
"""

import math

import networkx as nx
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

from ..criteria import DEFAULT
from ..model import key_of


def _turn_deg(a, b, c):
    d = abs(math.degrees(math.atan2(c[1] - b[1], c[0] - b[0])
                         - math.atan2(b[1] - a[1], b[0] - a[0]))) % 360.0
    return min(d, 360.0 - d)


def _total_turn(geom):
    cs = [geom.coords[0]]
    for p in list(geom.coords)[1:]:
        if math.dist(cs[-1], p) >= 0.5:
            cs.append(p)
    return sum(_turn_deg(cs[i - 1], cs[i], cs[i + 1]) for i in range(1, len(cs) - 1))


def _bearing(g):
    (x0, y0), (x1, y1) = g.coords[0], g.coords[-1]
    return math.degrees(math.atan2(y1 - y0, x1 - x0)) % 180.0


class RoadTreatment:
    def __init__(self, sampler=None, crit=DEFAULT, attrs=None, underpasses=()):
        self.sampler = sampler
        self.crit = crit
        self.attrs = attrs or {}          # id(geometry) -> {'dual':int, 'strcls':str}
        self.report = {}
        self.corridors = []
        self.removed = []                 # (geometry, reason) for the review layer
        self.underpasses = list(underpasses)
        self.crossings = []

    # ---------------- helpers ----------------
    def _attr(self, g, key, default=0):
        return self.attrs.get(id(g), {}).get(key, default)

    def _carry(self, new_geom, from_geom):
        """Keep the road class and dual value when a line is rebuilt."""
        if id(from_geom) in self.attrs:
            self.attrs[id(new_geom)] = dict(self.attrs[id(from_geom)])

    def _drop(self, g, reason):
        self.removed.append((g, reason))

    # ---------------- 1. tidy the points ----------------
    def _clean(self, segs):
        C = self.crit
        out, removed = [], 0
        for g in segs:
            cs = list(g.coords)
            keep = [cs[0]]
            for p in cs[1:-1]:
                if math.dist(keep[-1], p) >= C.ROAD_DEDUP_M:
                    keep.append(p)
                else:
                    removed += 1
            if math.dist(keep[-1], cs[-1]) < C.ROAD_DEDUP_M and len(keep) > 1:
                keep.pop()                # the near-duplicate goes, the end point stays
                removed += 1
            keep.append(cs[-1])
            line = LineString(keep).simplify(C.ROAD_SIMPLIFY_M, preserve_topology=False)
            if line.length > 0.5 and line.coords[0] != line.coords[-1]:
                self._carry(line, g)
                out.append(line)
        return out, removed

    # ---------------- 2-3. dual carriageways ----------------
    def _handle_duals(self, segs, units):
        """`dual` = 1: drop both sides — we cannot dig up a dual carriageway, not even for
        the trunk. `dual` = 2: a two-lane road drawn as a pair; keep ONE side for the whole
        length, never both and never swapping between them. The side kept is the one with
        more plots facing it, and the lower ground if that ties."""
        C = self.crit
        pts = [Point(u.x, u.y) for u in (units or [])]
        utree = STRtree(pts) if pts else None
        kept, n_excl, n_side = [], 0, 0

        twos = [g for g in segs if self._attr(g, "dual") == 2]
        drop_ids = set()
        if twos:
            tree = STRtree(twos)
            paired = set()
            for i, g in enumerate(twos):
                if id(g) in paired or g.length < 10:
                    continue
                for j in tree.query(g.buffer(45.0)):
                    o = twos[j]
                    if o is g or id(o) in paired or o.length < 10:
                        continue
                    db = abs(_bearing(g) - _bearing(o))
                    db = min(db, 180.0 - db)
                    if db > 12.0 or not (3.0 <= g.distance(o) <= 45.0):
                        continue
                    # keep the side with more plots facing it; tie -> lower ground
                    def score(ln):
                        n = len(utree.query(ln.buffer(C.CROSS_STREET_FRONTAGE))) if utree else 0
                        z = self.sampler.z(*ln.interpolate(0.5, normalized=True).coords[0]) \
                            if self.sampler else 0.0
                        return (n, -z)
                    loser = o if score(g) >= score(o) else g
                    drop_ids.add(id(loser))
                    paired.add(id(g))
                    paired.add(id(o))
                    n_side += 1
                    break

        for g in segs:
            d = self._attr(g, "dual")
            if d == 1:
                self._drop(g, "dual-carriageway")
                n_excl += 1
                continue
            if id(g) in drop_ids:
                self._drop(g, "two-lane-other-side")
                continue
            kept.append(g)
        return kept, {"dual_excluded": n_excl, "two_lane_side_dropped": n_side}

    # ---------------- 4. roundabouts ----------------
    def _collapse_roundabouts(self, segs, units=None):
        """A roundabout collects no sewage, so the ring goes and its arms meet at the
        middle. Telling a roundabout from a small block cannot be done on shape alone —
        a square scores higher on roundness than a real roundabout does. So the test is
        evidence: no plot inside the ring, small, with arms leaving it, and curved sides."""
        C = self.crit
        G = nx.MultiGraph()
        for i, g in enumerate(segs):
            G.add_edge(key_of(*g.coords[0]), key_of(*g.coords[-1]), idx=i, length=g.length)
        pts = [Point(u.x, u.y) for u in (units or [])]
        utree = STRtree(pts) if pts else None
        deg = {}
        for g in segs:
            for k in (key_of(*g.coords[0]), key_of(*g.coords[-1])):
                deg[k] = deg.get(k, 0) + 1

        drop, rings, slivers = set(), 0, 0
        rejected = {"plots_inside": 0, "too_big": 0, "no_arms": 0, "straight_sides": 0}
        remap = {}
        for cyc in nx.cycle_basis(nx.Graph(G)):
            if len(cyc) < 3:
                continue
            edges, perim, geoms, ok = [], 0.0, [], True
            for a, b in zip(cyc, cyc[1:] + [cyc[0]]):
                if not G.has_edge(a, b):
                    ok = False
                    break
                e = min(G[a][b].values(), key=lambda d: d["length"])
                edges.append(e["idx"])
                geoms.append(segs[e["idx"]])
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
            if utree is not None and any(poly.contains(pts[i]) for i in utree.query(poly)):
                rejected["plots_inside"] += 1
                continue
            if sum(1 for k in cyc if deg.get(k, 0) > 2) < 2:
                rejected["no_arms"] += 1
                continue
            curvy = len(cyc) >= 6
            if not curvy:
                turns = []
                for g in geoms:
                    cs = list(g.coords)
                    turns += [_turn_deg(cs[i - 1], cs[i], cs[i + 1]) for i in range(1, len(cs) - 1)]
                curvy = bool(turns) and sum(turns) / len(turns) > 5.0
            if not curvy:
                rejected["straight_sides"] += 1
                continue
            centre = key_of(sum(k[0] for k in cyc) / len(cyc), sum(k[1] for k in cyc) / len(cyc))
            for k in cyc:
                remap[k] = centre
            drop.update(edges)
            if r_eq < 5.0:
                slivers += 1
            else:
                rings += 1

        out = []
        for i, g in enumerate(segs):
            if i in drop:
                self._drop(g, "roundabout")
                continue
            a, b = key_of(*g.coords[0]), key_of(*g.coords[-1])
            na, nb = remap.get(a, a), remap.get(b, b)
            touched = (na != a) or (nb != b)
            if na == nb:
                continue
            cs = list(g.coords)
            if na != a:
                cs[0] = (na[0], na[1])
            if nb != b:
                cs[-1] = (nb[0], nb[1])
            line = LineString(cs)
            if touched and line.length <= 1.0:
                continue
            self._carry(line, g)
            out.append(line)
        return out, {"roundabouts": rings, "sliver_rings": slivers, "rings_rejected": rejected}

    # ---------------- 5. traffic links ----------------
    def _drop_traffic_links(self, segs, units):
        """Turning fillets, slip roads and the diagonal connectors between two roads exist
        so cars can turn. The sewer joins at a point instead, so these are dropped — but
        only when nothing is lost: no plot faces them, both ends are attached to other
        roads, and the way round is under 3x longer."""
        C = self.crit
        if not units:
            return segs, 0
        # "serves no plot" cannot mean "no plot within 40 m" — in a town every line has a
        # plot near it, so that test never fires. What matters is whether any plot would
        # actually USE this line: is it the closest line to anyone?
        seg_tree = STRtree(segs)
        used = set()
        for u in units:
            shape = u.geom if getattr(u, "geom", None) is not None else Point(u.x, u.y)
            best, best_d = None, 1e18
            for j in seg_tree.query(shape.buffer(120.0)):
                d = segs[j].distance(shape)
                if d < best_d:
                    best, best_d = j, d
            if best is not None:
                used.add(best)

        G = nx.MultiGraph()
        for i, g in enumerate(segs):
            G.add_edge(key_of(*g.coords[0]), key_of(*g.coords[-1]), idx=i, length=g.length)
        deg = {n: G.degree(n) for n in G.nodes}

        dropped = 0
        keep_flag = [True] * len(segs)
        order = sorted(range(len(segs)), key=lambda i: segs[i].length)
        for i in order:
            g = segs[i]
            a, b = key_of(*g.coords[0]), key_of(*g.coords[-1])
            if a == b:
                continue
            looks_like_link = (g.length <= C.LINK_MAX_LEN_M) or (_total_turn(g) >= C.LINK_MIN_TURN_DEG)
            if not looks_like_link:
                continue
            if deg.get(a, 0) < 3 or deg.get(b, 0) < 3:
                continue                                     # a dead end or a street head
            if i in used:
                continue                                     # some plot's nearest line — keep
            H = nx.Graph()
            for j, gg in enumerate(segs):
                if j == i or not keep_flag[j]:
                    continue
                ka, kb = key_of(*gg.coords[0]), key_of(*gg.coords[-1])
                if ka != kb:
                    H.add_edge(ka, kb, weight=gg.length)
            try:
                detour = nx.shortest_path_length(H, a, b, weight="weight")
            except Exception:
                continue                                     # removing it would cut the network
            if detour > C.LINK_DETOUR_RATIO * g.length:
                continue                                     # the way round is too far
            keep_flag[i] = False
            deg[a] -= 1
            deg[b] -= 1
            self._drop(g, "traffic-link")
            dropped += 1
        return [g for i, g in enumerate(segs) if keep_flag[i]], dropped

    # ---------------- 6. one line per straight street ----------------
    def _dissolve(self, segs, protect=None):
        C = self.crit
        protect = set(protect or ())
        changed, joined = True, 0
        while changed:
            changed = False
            ends = {}
            for i, g in enumerate(segs):
                ends.setdefault(key_of(*g.coords[0]), []).append((i, "s"))
                ends.setdefault(key_of(*g.coords[-1]), []).append((i, "e"))
            merged, consumed = [], set()
            for node, att in ends.items():
                if len(att) != 2 or node in protect:
                    continue
                (i, si), (j, sj) = att
                if i == j or i in consumed or j in consumed:
                    continue
                gi, gj = segs[i], segs[j]
                if self._attr(gi, "dual") != self._attr(gj, "dual"):
                    continue
                ci = list(gi.coords) if si == "e" else list(gi.coords)[::-1]
                cj = list(gj.coords) if sj == "s" else list(gj.coords)[::-1]
                if _turn_deg(ci[-2], ci[-1], cj[1]) > C.ROAD_COLLINEAR_DEG:
                    continue
                line = LineString(ci + cj[1:])
                self._carry(line, gi)
                merged.append(line)
                consumed.update({i, j})
                joined += 1
                changed = True
            segs = merged + [g for k, g in enumerate(segs) if k not in consumed]
        return segs, joined

    # ---------------- 7. dead ends with no plots ----------------
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
                self._drop(g, "empty-stub")
                dropped += 1
                continue
            out.append(g)
        return out, dropped

    # ---------------- 3b. the carriageway nobody tagged ----------------
    def _drop_dual_twins(self, segs):
        """Catch the second carriageway when the road file only tagged the first.

        A dual carriageway is two parallel lines and both should carry dual=1. Where only
        one does, the twin sails through the exclusion and a sewer gets laid down the other
        carriageway — which is exactly what the user saw: head chambers sitting on a dual
        (2026-08-20). Anything running within a few metres of an excluded carriageway, and
        roughly parallel to it, is that twin.

        A service road at a normal offset is nowhere near this test, so it is untouched."""
        C = self.crit
        duals = [g for g, why in self.removed if why == "dual-carriageway"]
        if not duals:
            return segs, 0
        tree = STRtree(duals)

        def bearing(g):
            c = list(g.coords)
            return math.degrees(math.atan2(c[-1][1] - c[0][1],
                                           c[-1][0] - c[0][0])) % 180.0

        out, dropped = [], 0
        for g in segs:
            mid = g.interpolate(0.5, normalized=True)
            hit = tree.query(mid.buffer(C.DUAL_TWIN_M))
            twin = False
            for i in hit:
                d = duals[i]
                if d.distance(mid) > C.DUAL_TWIN_M:
                    continue
                a = abs(bearing(g) - bearing(d))
                a = min(a, 180.0 - a)
                if a <= C.DUAL_TWIN_DEG:
                    twin = True
                    break
            if twin:
                self._drop(g, "dual-carriageway (twin, dual flag missing in the road file)")
                dropped += 1
                continue
            out.append(g)
        return out, dropped

    # ---------------- 6b. what the removals left behind ----------------
    def _drop_orphan_links(self, segs, units):
        """Take out what is left dangling once the duals and roundabouts have gone.

        A roundabout has approach arms; a dual carriageway has slip roads joining it. Once
        the ring and the carriageway are removed those pieces dead-end into nothing, serve
        no house, and would only add chambers. The user asked for all of them to go
        (2026-08-20, with drawings).

        It repeats, because removing one arm turns the next piece into a dead end."""
        C = self.crit
        tree = STRtree([Point(u.x, u.y) for u in units]) if units else None
        dropped = 0
        for _ in range(8):
            deg = {}
            for g in segs:
                for k in (key_of(*g.coords[0]), key_of(*g.coords[-1])):
                    deg[k] = deg.get(k, 0) + 1
            out, hit = [], 0
            for g in segs:
                a, b = key_of(*g.coords[0]), key_of(*g.coords[-1])
                ends = (deg.get(a, 0), deg.get(b, 0))
                dead = min(ends) <= 1
                serves = True
                if tree is not None:
                    serves = len(tree.query(g.buffer(C.CROSS_STREET_FRONTAGE))) > 0
                if dead and not serves and g.length < C.ORPHAN_LINK_M:
                    self._drop(g, "orphan-link (roundabout arm / dual slip road)")
                    hit += 1
                    continue
                out.append(g)
            segs = out
            dropped += hit
            if hit == 0:
                break
        return segs, dropped

    # ---------------- 6c. crossing a dual carriageway ----------------
    def _dual_crossings(self, segs, units):
        # NOTE: self.crossings collects (geom, free) so the router can price them

        """Let the two sides of a dual carriageway talk to each other.

        No pipe may run ALONG a dual carriageway, but a short one may cross it square-on.
        Joining the sides gives the gravity network routes it would not otherwise have, and
        that is worth having where it saves digging or a pumping station (user 2026-08-20).
        """
        C = self.crit
        duals = [g for g, why in self.removed if why.startswith("dual")]
        if not duals:
            return segs, 0
        ends = {}
        for g in segs:
            for c in (g.coords[0], g.coords[-1]):
                ends.setdefault(key_of(*c), (c[0], c[1]))
        made, used, free_made = 0, set(), 0
        dtree = STRtree(duals)
        pts = list(ends.items())
        ptree = STRtree([Point(xy) for _, xy in pts])
        for k, (x, y) in pts:
            if k in used:
                continue
            p = Point(x, y)
            near_d = dtree.query(p.buffer(C.DUAL_CROSS_MAX_M / 2.0))
            if not len(near_d):
                continue
            at_underpass = any(math.dist((x, y), u) < 120.0 for u in self.underpasses)
            dual = duals[near_d[0]]
            for j in ptree.query(p.buffer(C.DUAL_CROSS_MAX_M)):
                k2, (x2, y2) = pts[j]
                if k2 == k or k2 in used:
                    continue
                line = LineString([(x, y), (x2, y2)])
                if line.length < 5.0 or line.length > C.DUAL_CROSS_MAX_M:
                    continue
                if not line.crosses(dual):
                    continue                       # must actually get to the other side
                # square-on to the carriageway, or it is not a crossing
                chn = dual.project(p)
                a = dual.interpolate(max(0.0, chn - 5.0))
                b = dual.interpolate(min(dual.length, chn + 5.0))
                bd = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
                bl = math.degrees(math.atan2(y2 - y, x2 - x))
                off = abs(bd - bl) % 180.0
                off = min(off, 180.0 - off)
                if abs(90.0 - off) > C.DUAL_CROSS_SQUARE_DEG and not at_underpass:
                    continue
                segs = segs + [line]
                self.attrs[id(line)] = {"dual": 0, "StrCls": "crossing"}
                self.crossings.append((line, at_underpass))
                free_made += int(at_underpass)
                used.add(k)
                used.add(k2)
                made += 1
                break
        self._free_crossings = free_made
        return segs, made

    # ---------------- run ----------------
    def run(self, segs, units=None, out_path=None, protect=None):
        n0, km0 = len(segs), sum(g.length for g in segs) / 1000.0

        segs, dedup = self._clean(segs)
        segs, dual_rep = self._handle_duals(segs, units)
        segs, twins = self._drop_dual_twins(segs)
        segs, ring_rep = self._collapse_roundabouts(segs, units)
        segs, links = self._drop_traffic_links(segs, units)
        segs, orphans = self._drop_orphan_links(segs, units)
        segs, crossings = self._dual_crossings(segs, units)
        segs, joined = self._dissolve(segs, protect)
        segs, stubs = self._drop_stubs(segs, units)

        self.corridors = segs
        self.report = {"segments_in": n0, "segments_out": len(segs),
                       "km_in": round(km0, 2),
                       "km_out": round(sum(g.length for g in segs) / 1000.0, 2),
                       "points_tidied": dedup, "collinear_joins": joined,
                       "traffic_links_dropped": links, "empty_stubs_dropped": stubs,
                       "orphan_links_dropped": orphans, "dual_crossings_added": crossings,
                       "free_crossings_at_underpass": getattr(self, "_free_crossings", 0),
                       "dual_twins_dropped": twins}
        self.report.update(dual_rep)
        self.report.update(ring_rep)
        if out_path:
            self._write(out_path, segs)
        return segs

    def _write(self, path, segs):
        """The corridor file — what the sewer may use, plus everything removed and why."""
        import geopandas as gpd
        rows = [{"CORR_ID": f"C-{i+1:05d}", "LEN_M": round(g.length, 2),
                 "STR_CLS": self._attr(g, "strcls", ""), "DUAL": self._attr(g, "dual"),
                 "USE": 1, "EXCL_RSN": "", "geometry": g} for i, g in enumerate(segs)]
        rows += [{"CORR_ID": f"X-{i+1:05d}", "LEN_M": round(g.length, 2),
                  "STR_CLS": self._attr(g, "strcls", ""), "DUAL": self._attr(g, "dual"),
                  "USE": 0, "EXCL_RSN": rsn, "geometry": g}
                 for i, (g, rsn) in enumerate(self.removed)]
        gpd.GeoDataFrame(rows, crs="EPSG:32640").to_file(path, encoding="utf-8")
