"""ChamberPlacer — S3: chambers on the tree, reaches between them.

G203-p29-30: chambers at junctions, changes of grade/diameter/direction, the end of each
lateral, and at regular spacing on straight runs (Tab 12 maxima).

Spacing rule (user 2026-08-18): minimise chamber count first — the fewest reaches that
keep every length within the maximum — then split into ROUND lengths rather than an exact
equal division, never leaving a short stub. 330 m at a 100 m maximum becomes 80/80/80/90,
not 82.5 x 4 and not 100/100/100/30.
"""

import math

from shapely.geometry import LineString

from ..criteria import DEFAULT
from ..model import Network, key_of

MIN_REACH_M = 2.0         # chambers cannot sit closer than this along one run
# the bend threshold lives in Criteria (ROAD_BEND_DEG) so the audit and the placer can
# never disagree about what counts as a change of direction (review RT-6)


class ChamberPlacer:
    def __init__(self, sampler, crit=DEFAULT, round_spacing=True, plots=None):
        self.sampler = sampler
        self.crit = crit
        self.round_spacing = round_spacing
        self.plot_geoms = list(plots or [])       # plot outlines
        self.plots = None
        if self.plot_geoms:
            from shapely.strtree import STRtree
            self.plots = STRtree(self.plot_geoms)
        self.report = {}
        self.tight_corners = []       # corners where a chamber sits under 2 m from a plot

    # ---------------- bends ----------------
    def _corner_is_clear(self, x, y):
        """A chamber at a corner must sit in the road, not in someone's plot. Clear means
        at least BEND_CORNER_CLEAR_M from any plot outline (user rule 2026-08-19)."""
        if self.plots is None:
            return True
        from shapely.geometry import Point
        pt = Point(x, y)
        clear = self.crit.BEND_CORNER_CLEAR_M
        # the tree gives CANDIDATES by bounding box — the real distance still has to be
        # measured, or a plot 50 m away can block a perfectly good corner
        for j in self.plots.query(pt.buffer(clear)):
            if self.plot_geoms[j].distance(pt) < clear:
                return False
        return True

    def _bend_cuts(self, geom):
        """Where a bend needs chambers.

        A sharp turn at one point gets ONE chamber there, if that point is clear of the
        plots. A long sweeping bend gets 2 chambers, 3 at most, spaced so the pipe never
        sits more than ROAD_CHORD_DEV_M off the road line."""
        C = self.crit
        coords = list(geom.coords)
        if len(coords) < 3:
            return []
        cuts, run_turn, since_cut = [], 0.0, 0.0
        acc = 0.0
        for i in range(1, len(coords) - 1):
            acc += math.dist(coords[i - 1], coords[i])
            a1 = math.atan2(coords[i][1] - coords[i-1][1], coords[i][0] - coords[i-1][0])
            a2 = math.atan2(coords[i+1][1] - coords[i][1], coords[i+1][0] - coords[i][0])
            d = abs(math.degrees(a2 - a1)) % 360.0
            turn = min(d, 360.0 - d)
            run_turn += turn
            since_cut += turn
            sharp = turn > C.ROAD_BEND_DEG
            wide = since_cut >= 45.0
            if not (sharp or wide):
                continue
            # The chamber goes ON the corner. Whether that spot is 2 m clear of the plots
            # is an acceptability CHECK, not a reason to redesign the line — a corner too
            # tight for a chamber is flagged for the designer to nudge on the drawing
            # (user rule 2026-08-19).
            x, y = coords[i]
            cuts.append(acc)
            if sharp and not self._corner_is_clear(x, y):
                self.tight_corners.append((x, y))
            since_cut = 0.0
        # the "no more than 3 chambers" limit is PER BEND, not per street: a long road can
        # have several separate bends. So thin the cuts inside any 60 m stretch.
        out, window = [], 60.0
        for c in cuts:
            near = [x for x in out if abs(x - c) <= window]
            if len(near) >= C.BEND_MAX_CHAMBERS:
                continue
            out.append(c)
        return out

    # ---------------- spacing arithmetic ----------------
    def split_lengths(self, L, max_len):
        """Reach lengths covering L: fewest pieces, rounded, remainder on one piece."""
        n = max(1, int(math.ceil(L / max_len - 1e-9)))
        if n == 1:
            return [L]
        if not self.round_spacing:
            return [L / n] * n
        for step in (self.crit.MH_ROUND_STEP, self.crit.MH_ROUND_FALLBACK):
            base = math.floor((L / n) / step) * step
            if base <= 0:
                continue
            rem = L - base * n
            k = int(round(rem / step))
            if base + step > max_len + 1e-9:
                k = 0
            lens = [base + step if i < k else base for i in range(n)]
            odd = L - sum(lens)
            if abs(odd) > 1e-9:
                # the odd metres go on the reach with the most headroom, never on the
                # last one blindly — that could push a reach past the maximum spacing
                lens[lens.index(min(lens))] += odd
            if all(x > 0 for x in lens) and max(lens) <= max_len + 1e-6:
                return lens
        return [L / n] * n

    def _split_points(self, geom):
        """Chainages where a run must break: bends first, then spacing."""
        breaks = self._bend_cuts(geom)
        cuts = list(breaks)
        anchors = [0.0] + breaks + [geom.length]
        for a, b in zip(anchors[:-1], anchors[1:]):
            span = b - a
            if span <= self.crit.MH_SPLIT_LEN:
                continue
            run = a
            for piece in self.split_lengths(span, self.crit.MH_SPLIT_LEN)[:-1]:
                run += piece
                cuts.append(run)
        return sorted(set(round(c, 3) for c in cuts))

    @staticmethod
    def _cut(geom, chainages):
        """Split a LineString at chainages -> pieces covering it exactly end to end."""
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

    # ---------------- placement ----------------
    def run(self, Gd, outfall) -> Network:
        net = Network(outfall=outfall)
        for n, d in Gd.nodes(data=True):
            kind = "outfall" if n == outfall else ("head" if Gd.in_degree(n) == 0
                                                  else "junction")
            k = net.add_chamber(d["x"], d["y"], d["z"], kind)
            if d.get("trunk"):
                net.chambers[k].on_trunk = True

        for u, v, d in Gd.edges(data=True):
            geom = d["geom"]
            on_trunk = bool(d.get("trunk"))
            cuts = self._split_points(geom)
            pieces = self._cut(geom, cuts) if cuts else [geom]
            prev = u
            for i, piece in enumerate(pieces):
                if i == len(pieces) - 1:
                    nxt = v
                else:
                    p = piece.coords[-1]
                    nxt = net.add_chamber(p[0], p[1], self.sampler.z(p[0], p[1]), "spacing")
                    # a chamber cut into the main pipe is still ON the main pipe — without
                    # this the run looks like dozens of separate connections into it
                    net.chambers[nxt].on_trunk = on_trunk
                r = net.add_reach(prev, nxt, piece)
                r.on_trunk = on_trunk
                r.is_connector = bool(d.get("connector"))
                r.is_crossing = bool(d.get("crossing"))
                prev = nxt

        self._contract(net)
        self._resplit(net)
        self.report = {"chambers": len(net.chambers), "reaches": len(net.reaches)}
        return net

    def _contract(self, net: Network):
        """Chambers ~1.2 m across cannot sit 0.6 m apart: noding debris where several
        streets meet within a metre becomes ONE chamber."""
        changed = True
        while changed:
            changed = False
            for r in list(net.reaches):
                if r.length >= MIN_REACH_M:
                    continue
                u, v = r.up, r.dn
                net.remove_reach(r)
                changed = True
                if u == v:
                    break
                keep, drop = (u, v) if net.chambers[u].kind == "outfall" else (v, u)
                kx, ky = net.chambers[keep].x, net.chambers[keep].y
                for q in net.reaches:
                    if q.up == drop:
                        q.up = keep
                        q.geom = LineString([(kx, ky)] + list(q.geom.coords)[1:])
                    if q.dn == drop:
                        q.dn = keep
                        q.geom = LineString(list(q.geom.coords)[:-1] + [(kx, ky)])
                    q.length = q.geom.length
                if net.chambers[drop].kind == "junction" and net.chambers[keep].kind != "outfall":
                    net.chambers[keep].kind = "junction"
                del net.chambers[drop]
                break

    def enforce_spacing(self, net: Network, limit=None):
        """Final guard, run AFTER StructureResolver: merging chambers re-anchors reach
        endpoints, which can nudge a reach past its spacing class OR introduce a sharp
        bend. Split anything over-length or over-bent (review F2/chambers)."""
        limit = limit or self.crit.MH_SPLIT_LEN
        n_split = 0
        needs = [x for x in net.reaches
                 if x.length > limit + 0.005 or self._max_bend(x.geom) > self.crit.ROAD_BEND_DEG]
        for r in needs:
            net.remove_reach(r)
            cuts = self._split_points(r.geom)
            if not cuts:
                run = 0.0
                for piece in self.split_lengths(r.length, limit)[:-1]:
                    run += piece
                    cuts.append(run)
            prev = r.up
            pcs = self._cut(r.geom, cuts)
            for i, piece in enumerate(pcs):
                if i == len(pcs) - 1:
                    nxt = r.dn
                else:
                    nxt = net.add_chamber(piece.coords[-1][0], piece.coords[-1][1],
                                          self.sampler.z(*piece.coords[-1][:2]),
                                          "spacing")
                    net.chambers[nxt].on_trunk = r.on_trunk
                nr = net.add_reach(prev, nxt, piece)
                nr.on_trunk, nr.is_connector, nr.is_crossing = (
                    r.on_trunk, r.is_connector, r.is_crossing)
                prev = nxt
            n_split += 1
        return n_split

    @staticmethod
    def _max_bend(geom):
        """Largest interior deflection, measured on cleaned vertices — duplicate points
        otherwise read as a 180 degree bend."""
        cs = [geom.coords[0]]
        for p in list(geom.coords)[1:]:
            if math.dist(cs[-1], p) >= 0.5:
                cs.append(p)
        m = 0.0
        for i in range(1, len(cs) - 1):
            a1 = math.atan2(cs[i][1] - cs[i - 1][1], cs[i][0] - cs[i - 1][0])
            a2 = math.atan2(cs[i + 1][1] - cs[i][1], cs[i + 1][0] - cs[i][0])
            d = abs(math.degrees(a2 - a1)) % 360.0
            m = max(m, min(d, 360.0 - d))
        return m

    def _resplit(self, net: Network):
        """Endpoint re-anchoring can push a piece past the spacing limit; heal here so an
        unsplit reach can never ship."""
        for r in [x for x in net.reaches if x.length > self.crit.MH_SPLIT_LEN + 0.01]:
            net.remove_reach(r)
            cuts = self._split_points(r.geom)
            if not cuts:
                run, cuts = 0.0, []
                for piece in self.split_lengths(r.length, self.crit.MH_SPLIT_LEN)[:-1]:
                    run += piece
                    cuts.append(run)
            prev = r.up
            pcs = self._cut(r.geom, cuts)
            for i, piece in enumerate(pcs):
                if i == len(pcs) - 1:
                    nxt = r.dn
                else:
                    q = piece.coords[-1]
                    nxt = net.add_chamber(q[0], q[1], self.sampler.z(q[0], q[1]), "spacing")
                    net.chambers[nxt].on_trunk = r.on_trunk
                nr = net.add_reach(prev, nxt, piece)
                nr.on_trunk, nr.is_connector, nr.is_crossing = (
                    r.on_trunk, r.is_connector, r.is_crossing)
                prev = nxt


class Labeller:
    """Deterministic names: chambers numbered farthest-first by network distance."""

    @staticmethod
    def run(net: Network):
        import networkx as nx
        Gp = nx.Graph()
        for r in net.reaches:
            Gp.add_edge(r.up, r.dn, length=r.length)
        dist = nx.single_source_dijkstra_path_length(Gp, net.outfall, weight="length") \
            if net.outfall in Gp else {}
        order = sorted(net.chambers, key=lambda k: -dist.get(k, 0.0))
        seq = 1
        for k in order:
            if net.chambers[k].kind == "outfall":
                net.chambers[k].label = "OF-1"
            else:
                net.chambers[k].label = f"MH-{seq:04d}"
                seq += 1
        for i, r in enumerate(net.reaches):
            r.label = f"P-{i+1:04d}"
