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

BEND_ANGLE_DEG = 45.0     # split a run at interior vertices deflecting more than this
MIN_REACH_M = 2.0         # chambers cannot sit closer than this along one run


class ChamberPlacer:
    def __init__(self, sampler, crit=DEFAULT, round_spacing=True):
        self.sampler = sampler
        self.crit = crit
        self.round_spacing = round_spacing
        self.report = {}

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
        """Chainages where a run must break: sharp bends first, then rounded spacing."""
        coords = list(geom.coords)
        breaks, acc = [], 0.0
        for i in range(1, len(coords) - 1):
            acc += math.dist(coords[i - 1], coords[i])
            a1 = math.atan2(coords[i][1] - coords[i - 1][1], coords[i][0] - coords[i - 1][0])
            a2 = math.atan2(coords[i + 1][1] - coords[i][1], coords[i + 1][0] - coords[i][0])
            d = abs(math.degrees(a2 - a1)) % 360.0
            if min(d, 360.0 - d) > BEND_ANGLE_DEG:
                breaks.append(acc)
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
            net.add_chamber(d["x"], d["y"], d["z"], kind)

        for u, v, d in Gd.edges(data=True):
            geom = d["geom"]
            cuts = self._split_points(geom)
            pieces = self._cut(geom, cuts) if cuts else [geom]
            prev = u
            for i, piece in enumerate(pieces):
                if i == len(pieces) - 1:
                    nxt = v
                else:
                    p = piece.coords[-1]
                    nxt = net.add_chamber(p[0], p[1], self.sampler.z(p[0], p[1]), "spacing")
                net.add_reach(prev, nxt, piece)
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
        endpoints, which can nudge a reach past its spacing class. Split anything over."""
        limit = limit or self.crit.MH_SPLIT_LEN
        n_split = 0
        for r in [x for x in net.reaches if x.length > limit + 0.005]:
            net.remove_reach(r)
            run, cuts = 0.0, []
            for piece in self.split_lengths(r.length, limit)[:-1]:
                run += piece
                cuts.append(run)
            prev = r.up
            pcs = self._cut(r.geom, cuts)
            for i, piece in enumerate(pcs):
                nxt = r.dn if i == len(pcs) - 1 else \
                    net.add_chamber(piece.coords[-1][0], piece.coords[-1][1],
                                    self.sampler.z(*piece.coords[-1][:2]), "spacing")
                net.add_reach(prev, nxt, piece)
                prev = nxt
            n_split += 1
        return n_split

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
                net.add_reach(prev, nxt, piece)
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
