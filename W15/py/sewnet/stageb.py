"""sewnet.stageb — stage B, the hydraulic design of each subnetwork on stage A's layout
(engineer's rulings of 2026-09-12, W13/tmp4/docs/W13_TMP4_DESIGN_LOGIC.md).

Stage A's tree is taken as it is: the same pipes, the same sizes, the same outlets. Stage B
lays it for real, heads-down:

- one gradient per street run, junction to junction: the Table 11 minimum, or steeper where
  the cover along the run forces it (1.3 m to the crown, G203 p33; 1.5 m in a wadi, p52),
  rounded up to the grid; never steeper than the gradient at which the design peak runs at
  3 m/s (p27);
- where the ground falls faster than that, the run is laid at the 3 m/s gradient and the
  rest of the fall is taken as drops at the chambers, 2 m at most each (p30), the chambers
  closer where the drop would pass it;
- chambers at every junction, head and outlet, and along a run by G203 Table 12 spacing
  (100 m to DN315, 120 m to DN900) with W8's setting-out rule, the fewest chambers, evenly
  spaced, rounded to 10 m (5 m where 10 leaves an odd remainder); at a bend sharper than
  30 degrees, or where a curve has turned 45 degrees, never more than three on one bend;
- at a junction, an incoming pipe arriving more than 0.6 m above the outgoing invert gets a
  backdrop; a backdrop over 2 m is flagged (vortex drop shaft, p30);
- every reach is checked at its laid gradient with Colebrook-White (ks 1.5 mm): d/D within
  Table 10 and v within 3 m/s at the design peak, and the self-cleansing class on the low
  case (velocity, tractive, washing) as stage A's audit;
- a reach in a wadi is recorded, a reach crossing a dual carriageway is recorded.

Pumped inflows (stage B's pump candidates) enter through extra_inflow, {node: m3/s peak},
added to the accumulation below that node before sizing and laying.
"""
import collections
import math

import numpy as np
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

from . import hydraulics as H
from .cleansing import mara_slope, V_MIN as V_SELF, MARA_K, TAU_PA
from .ground import profile

SPACING = ((315, 100.0), (900, 120.0), (1400, 150.0))   # G203 p30 Table 12, by nominal size


def spacing_for(dn):
    for top, s in SPACING:
        if dn <= top:
            return s
    return 200.0


def split_lengths(L, max_len, step=10.0, fallback=5.0):
    """W8's setting-out rule (kept as the current rule, engineer 2026-09-12): the fewest
    reaches within max_len, evenly spaced, rounded to step (fallback where step leaves an
    odd remainder), the odd metres on the reach with the most room."""
    n = max(1, int(math.ceil(L / max_len - 1e-9)))
    if n == 1:
        return [L]
    for st in (step, fallback):
        base = math.floor((L / n) / st) * st
        if base <= 0:
            continue
        rem = L - base * n
        k = int(round(rem / st))
        if base + st > max_len + 1e-9:
            k = 0
        lens = [base + st if i < k else base for i in range(n)]
        odd = L - sum(lens)
        if abs(odd) > 1e-9:
            lens[lens.index(min(lens))] += odd
        if all(x > 0 for x in lens) and max(lens) <= max_len + 1e-6:
            return lens
    return [L / n] * n


def bend_cuts(geom, bend_deg=5.0, wide_deg=45.0, max_per_60m=3, sep_m=10.0):
    """Chainages where a bend needs a chamber (the engineer's rule 12, 2026-09-12): up to
    bend_deg none; every corner turning more gets its chamber, two consecutive corners both;
    a sweeping curve gets one chord chamber every wide_deg of turn, never more than
    max_per_60m inside 60 m and never closer than sep_m to the last. A corner within sep_m of
    an end keeps its chamber: the end chamber is not allowed to swallow it."""
    coords = list(geom.coords)
    L = geom.length
    if len(coords) < 3:
        return []
    cuts, acc, since = [], 0.0, 0.0
    for i in range(1, len(coords) - 1):
        acc += math.dist(coords[i - 1], coords[i])
        a1 = math.atan2(coords[i][1] - coords[i - 1][1], coords[i][0] - coords[i - 1][0])
        a2 = math.atan2(coords[i + 1][1] - coords[i][1], coords[i + 1][0] - coords[i][0])
        d = abs(math.degrees(a2 - a1)) % 360.0
        turn = min(d, 360.0 - d)
        since += turn
        if turn > bend_deg:
            cuts.append((acc, True))          # a corner: its own chamber, always
            since = 0.0
        elif since >= wide_deg:
            cuts.append((acc, False))         # a chord on a sweeping curve
            since = 0.0
    out = []
    for c, corner in cuts:
        if c < sep_m or c > L - sep_m:
            continue                          # the end chamber takes this bend
        if not corner:
            if out and c - out[-1] < sep_m:
                continue
            if len([x for x in out if abs(x - c) <= 60.0]) >= max_per_60m:
                continue
        elif out and c - out[-1] < 0.5:
            continue
        out.append(c)
    return out


def _cut(geom, chainages):
    """Split a LineString at chainages into pieces covering it end to end."""
    L = geom.length
    cuts = []
    for c in sorted(set(round(c, 3) for c in chainages)):
        if c <= 0.5 or c >= L - 0.5 or (cuts and c - cuts[-1] < 0.5):
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
        pts = [(pa.x, pa.y)] + [coords[i] for i, d in enumerate(cum) if a < d < b] + [(pb.x, pb.y)]
        pieces.append((a, b, LineString(pts)))
    return pieces


class StageB:
    def __init__(self, pipes, znode, ground, cfg, wadis=(), duals=(), extra_inflow=None,
                 log=print):
        self.pipes = pipes
        self.z = znode
        self.ground = ground
        self.cfg = cfg
        self.cover = float(getattr(cfg, "COVER_CROWN_M", 1.3))
        self.cover_wadi = float(getattr(cfg, "COVER_WADI_M", 1.5))
        self.drop_max = float(getattr(cfg, "DROP_MAX_M", 2.0))
        self.backdrop_min = float(getattr(cfg, "BACKDROP_MIN_M", 0.6))
        self.max_depth = float(getattr(cfg, "MAX_DEPTH_M", 12.0))
        self.step = float(getattr(cfg, "PROFILE_STEP_M", 5.0))
        self.grid = getattr(cfg, "SLOPE_GRID", (0.0005, 0.00025, 500))
        self.v_max = float(getattr(cfg, "V_MAX_MS", H.V_MAX))
        self.connected = float(getattr(cfg, "LOW_CASE_CONNECTED", 0.61))
        self.infil = float(getattr(cfg, "INFIL_L_D_KM", 720.0))
        self.wadis = list(wadis)
        self.wtree = STRtree(self.wadis) if self.wadis else None
        self.duals = list(duals)
        self.dtree = STRtree(self.duals) if self.duals else None
        self.extra = dict(extra_inflow or {})
        self.log = log
        self.reaches, self.chambers = [], []
        self.inv = {}
        self.flags = collections.Counter()
        self._caps = {}
        self.head_m = float(getattr(cfg, "HEAD_COVER_M", 10.0))

    # ------------------------------------------------------------------ helpers
    def _cap(self, dn):
        """The steepest gradient a pipe of this size may be laid at: 3 m/s at its Table 10
        design depth (G203 p27). Steeper ground is taken in drops at the chambers."""
        if dn not in self._caps:
            D, y = H.bore(dn), H.y_max(dn)
            lo, hi = 1e-4, 2.0
            for _ in range(60):
                mid = math.sqrt(lo * hi)
                if H.velocity(D, mid, y) < self.v_max:
                    lo = mid
                else:
                    hi = mid
            self._caps[dn] = hi
        return self._caps[dn]

    def _grid_up(self, s, dn):
        step = self.grid[1] if dn >= self.grid[2] else self.grid[0]
        return math.ceil(s / step - 1e-9) * step

    def _in_wadi(self, pt):
        if self.wtree is None:
            return False
        return any(self.wadis[k].contains(pt) for k in self.wtree.query(pt))

    def _crosses_dual(self, geom):
        if self.dtree is None:
            return False
        return any(self.duals[k].intersects(geom) for k in self.dtree.query(geom))

    # ------------------------------------------------------------------ the lay
    def run(self):
        pipes = self.pipes
        # a tree head trimmed to the first gate keeps the junction's key in stage A while its
        # geometry starts at the gate: here it gets its own node at the gate, at the level
        # stage A interpolated for it, so it starts at cover there and not at the junction
        self.pos = {}
        U = []
        sep = float(getattr(self.cfg, "CHAMBER_SEP_M", 10.0))
        self.heads_moved = 0
        n_in0 = collections.Counter(q["dn"] for q in pipes)
        junctions = [Point(q["dn"]) for q in pipes] + [Point(q["up"]) for q in pipes if n_in0[q["up"]] > 0]
        jtree = STRtree(junctions)
        self.dropped = []
        bend_deg = float(getattr(self.cfg, "BEND_DEG", 5.0))
        for i, q in enumerate(pipes):
            c0 = q["geom"].coords[0]
            if n_in0[q["up"]] == 0:
                # a head chamber: on the first bend if one lies within sep of the head (the
                # bend keeps its chamber, the head moves to it, engineer 2026-09-12); else at
                # the gate, but never closer than sep to a junction chamber, so it moves
                # along its own street to sep from that junction
                g = q["geom"]
                bends_here = bend_cuts(g, bend_deg, sep_m=0.0)
                first_bend = min([c for c in bends_here if 0.5 < c <= sep], default=None)
                pt = Point(c0)
                near = [junctions[int(j)] for j in jtree.query(pt.buffer(sep)) if junctions[int(j)].distance(pt) < sep]
                cut_at = 0.0
                if first_bend is not None:
                    cut_at = first_bend
                    q["head_at_bend"] = True
                elif near:
                    cut_at = sep - min(j_.distance(pt) for j_ in near)
                if cut_at > 0.0:
                    if g.length - cut_at < sep:
                        # what is left would be shorter than a chamber's separation: the pipe
                        # is not worth a chamber of its own, its plot connects at the foot
                        self.dropped.append(i)
                        q["dropped"] = "head pipe shorter than %.0f m after its head moved" % sep
                        U.append(q["up"])
                        continue
                    q["geom"] = self._piece(g, cut_at, g.length)
                    q["len"] = q["geom"].length
                    q["head_moved_m"] = cut_at
                    c0 = q["geom"].coords[0]
                    self.heads_moved += 1
            if math.dist(c0, q["up"]) > 1.0:
                key = ("H", i)
                self.z[key] = float(self.ground.z_node(c0[0], c0[1]))
                self.pos[key] = (c0[0], c0[1])
                U.append(key)
            else:
                U.append(q["up"])
        self.U = U
        live = [i for i in range(len(pipes)) if i not in set(self.dropped)]
        n_in = collections.Counter(pipes[i]["dn"] for i in live)
        out_of = collections.defaultdict(list)
        for i in live:
            out_of[U[i]].append(i)
        # heads-down order, every incoming pipe laid before the outgoing one
        arrived = collections.Counter()
        order = []
        queue = [i for i in live if n_in[U[i]] == 0]
        heads = set(U[i] for i in live if n_in[U[i]] == 0)
        while queue:
            i = queue.pop()
            q = pipes[i]
            order.append(i)
            arrived[q["dn"]] += 1
            if arrived[q["dn"]] == n_in[q["dn"]]:
                queue.extend(out_of[q["dn"]])
        # stage A already accumulated q_peak_ls / q_low_ls per pipe; a pumped inflow at a node
        # is added to every pipe downstream of it
        if self.extra:
            down = collections.defaultdict(set)
            par = {U[i]: i for i, q in enumerate(pipes)}
            for node, qx in self.extra.items():
                i = par.get(node)
                while i is not None:
                    pipes[i]["q_peak_ls"] = pipes[i].get("q_peak_ls", 0.0) + qx * 1000.0
                    pipes[i]["pumped_ls"] = pipes[i].get("pumped_ls", 0.0) + qx * 1000.0
                    i = par.get(pipes[i]["dn"])
        inv = self.inv
        arrivals = collections.defaultdict(list)     # node -> [(invert arriving, pipe index)]
        n_drop = n_backdrop = n_deep_drop = 0
        for i in order:
            p = pipes[i]
            u, d, L = U[i], p["dn"], p["len"]
            qd = p.get("q_peak_ls", 0.0) / 1000.0
            ql = p.get("q_low_ls", 0.0) / 1000.0
            dn = int(p.get("dn_mm") or H.size_for(qd))
            if p.get("pumped_ls"):
                dn = max(dn, H.size_for(qd))
            p["dn_mm"] = dn
            cov = self.cover + H.outside(dn)
            # the run's line starts and ends on its chambers: stage A noded the streets within
            # 3 m without moving the line ends, so the node could sit a metre off the pipe end
            pu = self.pos.get(u, u if not (isinstance(u, tuple) and u and u[0] == "H") else None)
            pd = d
            coords = list(p["geom"].coords)
            if pu is not None and math.dist(coords[0], pu) > 0.01:
                coords[0] = (float(pu[0]), float(pu[1]))
            if math.dist(coords[-1], pd) > 0.01:
                coords[-1] = (float(pd[0]), float(pd[1]))
            if coords != list(p["geom"].coords):
                p["geom"] = LineString(coords)
                p["len"] = p["geom"].length
                L = p["len"]
            # the ground along the run, the node levels at the ends
            ch, zg = profile(self.ground, p["geom"], self.step)
            zg = np.array(zg, dtype=float)
            zg[0], zg[-1] = self.z.get(u, zg[0]), self.z.get(d, zg[-1])
            if abs(zg[0] - float(zg[1] if len(zg) > 1 else zg[0])) > 5.0:
                zg[0] = float(np.asarray(profile(self.ground, p["geom"], self.step)[1])[0])   # a node level off its own street
            pts = [p["geom"].interpolate(c) for c in ch]
            wadi_k = np.array([self._in_wadi(pt) for pt in pts])
            covk = np.where(wadi_k, self.cover_wadi + H.outside(dn), cov)
            floor = zg - covk
            # upstream invert: the head at cover, or the junction's lowest arrival
            if u not in inv:
                inv[u] = floor[0]
            inv_u = min(inv[u], floor[0])
            inv[u] = inv_u
            s_min = H.T11[dn]
            # a dip within the first metres of the run deepens the chamber it starts from,
            # never the gradient of the whole run
            near = [k for k in range(1, len(ch)) if ch[k] <= self.head_m]
            need = max((inv_u - (floor[k] + s_min * ch[k]) for k in near), default=0.0)
            if need > 1e-6:
                inv_u -= need
                inv[u] = inv_u
                p["head_lowered_m"] = need
            # the run's gradient, junction to junction: the Table 11 minimum, or what the cover
            # at the far end asks for (parallel to the ground on a slope), rounded up to the
            # grid, never past the ceiling; a dip inside the run steepens only the reach that
            # holds it (the cover exception of the engineer's rule), and the reaches after it
            # go back to the run's gradient from the deeper invert the dip left them
            s_min = H.T11[dn]
            s_end = (inv_u - floor[-1]) / max(L, 1e-6)
            s_run = max(s_min, s_end)
            if s_run > s_min + 1e-12:
                s_run = max(s_min, self._grid_up(s_run, dn))
            s_max = min(H.slope_for_velocity(dn, qd, self.v_max), self._cap(dn))
            if s_max < s_min:
                s_max = s_min            # a pipe carrying more than its size should: reported by the check
            step = self.grid[1] if dn >= self.grid[2] else self.grid[0]
            s_ceiling = max(s_min, math.floor(s_max / step) * step)
            steep = s_run > s_max + 1e-12
            if steep:
                s_run = s_ceiling
            p["slope_b"] = s_run
            p["steep"] = steep
            spacing = spacing_for(dn)
            bends = bend_cuts(p["geom"], float(getattr(self.cfg, "BEND_DEG", 5.0)),
                              sep_m=float(getattr(self.cfg, "CHAMBER_SEP_M", 10.0)))
            sep = float(getattr(self.cfg, "CHAMBER_SEP_M", 10.0))
            cuts = list(bends)                      # every bend chamber stands where the bend is
            anchors = [0.0] + bends + [L]
            for a0, b0 in zip(anchors[:-1], anchors[1:]):
                if b0 - a0 <= spacing + 1e-6:
                    continue
                run_ = a0
                for piece in split_lengths(b0 - a0, spacing)[:-1]:
                    run_ += piece
                    if run_ > sep and run_ < L - sep and all(abs(run_ - x) >= sep for x in bends):
                        cuts.append(run_)           # a spacing chamber keeps clear of the ends and the bends
            pieces = _cut(p["geom"], cuts)
            inv_arr = inv_u
            k = 0
            queue_r = list(pieces)
            while queue_r:
                a0, b0, g = queue_r.pop(0)
                sel = [(c, f) for c, f in zip(ch, floor) if a0 < c <= b0 + 1e-6] or [(b0, float(np.interp(b0, ch, floor)))]
                need = max((inv_arr - f) / (c - a0) for c, f in sel)   # the gradient that keeps cover in this reach
                s = s_run if need <= s_run + 1e-12 else max(s_run, self._grid_up(need, dn))
                drop = 0.0
                if s > s_max + 1e-12:
                    # steeper than the pipe may be laid: the reach is laid at the ceiling and the
                    # rest of the fall is a drop at its head, 2 m at most, so the reach shortens
                    s = s_ceiling
                    inv_a = min(inv_arr, min(f + s * (c - a0) for c, f in sel))
                    drop = inv_arr - inv_a
                    if drop > self.drop_max + 1e-9 and b0 - a0 > 10.0 + 1e-6:
                        mid = a0 + max(10.0, math.floor((b0 - a0) / 2.0 / 10.0) * 10.0)
                        queue_r = [(a0, mid, self._piece(p["geom"], a0, mid)), (mid, b0, self._piece(p["geom"], mid, b0))] + queue_r
                        continue
                    if drop > self.drop_max + 1e-9:
                        self.flags["drop over 2 m"] += 1
                        n_deep_drop += 1
                    if drop > 1e-6:
                        n_drop += 1
                        if drop > self.backdrop_min:
                            n_backdrop += 1
                else:
                    inv_a = inv_arr
                inv_b = inv_a - s * (b0 - a0)
                kind = "drop" if drop > 1e-6 else ("bend" if any(abs(a0 - x) < 0.01 for x in bends) else ("spacing" if k > 0 else "start"))
                self._add_reach(p, i, k, a0, b0, g, inv_a, inv_b, s, dn, qd, ql, ch, zg, floor, wadi_k,
                                kind=kind, drop_at_start=drop)
                inv_arr, k = inv_b, k + 1
            arrival = inv_arr
            p["inv_up_b"], p["inv_dn_b"] = inv_u, arrival
            arrivals[d].append((arrival, i))
            inv[d] = min(inv.get(d, float("inf")), arrival)
        # junction backdrops: an incoming pipe arriving above the outgoing invert
        for node, arr in arrivals.items():
            base = inv[node]
            for a_inv, i in arr:
                drop = a_inv - base
                pipes[i]["drop_at_junction"] = drop
                if drop > self.backdrop_min:
                    n_backdrop += 1
                    n_drop += 1
                    if drop > self.drop_max + 1e-9:
                        n_deep_drop += 1
                        self.flags["junction drop over 2 m"] += 1
        # chambers at the nodes
        for node, level in inv.items():
            zg = self.z.get(node)
            if zg is None:
                continue
            outs = out_of.get(node) or []
            kind = "head" if node in heads else ("outlet" if not outs else "junction")
            drops = [pipes[i].get("drop_at_junction", 0.0) for i in [j for j, q in enumerate(pipes) if q["dn"] == node]]
            x_, y_ = self.pos.get(node, (node[0], node[1]) if not (isinstance(node, tuple) and node and node[0] == "H") else (0.0, 0.0))
            self.chambers.append({"node": node, "x": x_, "y": y_, "kind": kind, "z": zg,
                                  "invert": level, "depth": zg - level, "cap3ms": False,
                                  "pipe": (outs[0] if outs else None),
                                  "head_how": (pipes[outs[0]].get("head_how", "") if outs and kind == "head" else ""),
                                  "drop": max(drops) if drops else 0.0,
                                  "catch": (pipes[outs[0]]["catch"] if outs else
                                            next((q["catch"] for q in pipes if q["dn"] == node), ""))})
        self.summary = self._summary(n_drop, n_backdrop, n_deep_drop)
        return self.reaches, self.chambers, self.summary

    @staticmethod
    def _piece(geom, a, b):
        coords = list(geom.coords)
        cum = [0.0]
        for i in range(1, len(coords)):
            cum.append(cum[-1] + math.dist(coords[i - 1], coords[i]))
        pa, pb = geom.interpolate(a), geom.interpolate(b)
        pts = [(pa.x, pa.y)] + [coords[i] for i, d in enumerate(cum) if a < d < b] + [(pb.x, pb.y)]
        return LineString(pts)

    def _add_reach(self, p, i, k, a, b, g, inv_a, inv_b, s, dn, qd, ql, ch, zg, floor, wadi_k,
                   kind, drop_at_start):
        sel = [(c, z) for c, z in zip(ch, zg) if a - 1e-6 <= c <= b + 1e-6]
        depths = [z - (inv_a - s * (c - a)) for c, z in sel]
        za = float(np.interp(a, ch, zg)); zb = float(np.interp(b, ch, zg))
        trench = max(depths + [za - inv_a, zb - inv_b])
        y, v = H.depth_ratio(dn, s, qd)
        cap_ok = (y <= H.y_max(dn) + 1e-9) and (v <= self.v_max + 0.01)
        yl, vl = H.depth_ratio(dn, s, ql)
        sm = mara_slope(ql, TAU_PA, MARA_K)
        cleanse = "velocity" if vl >= V_SELF else ("tractive" if s >= sm else "washing")
        wadi = bool(any(w for c, w in zip(ch, wadi_k) if a - 1e-6 <= c <= b + 1e-6))
        cov_min = min(depths) - H.outside(dn) if depths else float("nan")
        short = max(((inv_a - s * (c - a)) - f for c, f in zip(ch, floor) if a - 1e-6 <= c <= b + 1e-6), default=0.0)
        r = {"pipe": i, "reach": k, "catch": p["catch"], "tier": p["tier"], "dn": dn, "geom": g,
             "cover_min": cov_min, "cover_short": max(0.0, short),
             "cap3ms": bool(p.get("steep", False)) or kind == "drop",
             "a": a, "b": b, "len": b - a, "slope": s, "inv_up": inv_a, "inv_dn": inv_b,
             "z_up": za, "z_dn": zb, "depth_up": za - inv_a, "depth_dn": zb - inv_b,
             "trench_max": trench, "q_peak_ls": qd * 1000.0, "yd": y, "v": v, "cap_ok": cap_ok,
             "q_low_ls": ql * 1000.0, "v_low": vl, "cleanse": cleanse, "kind": kind,
             "drop": drop_at_start, "wadi": wadi, "dual_x": self._crosses_dual(g),
             "steep": p.get("steep", False), "pumped_ls": p.get("pumped_ls", 0.0)}
        self.reaches.append(r)
        if a > 0.5:
            # an interior chamber at the reach's head
            self.chambers.append({"node": None, "x": g.coords[0][0], "y": g.coords[0][1], "kind": kind,
                                  "z": za, "invert": inv_a, "depth": za - inv_a, "drop": drop_at_start,
                                  "catch": p["catch"], "cap3ms": kind == "drop", "pipe": i})
        if trench > self.max_depth:
            self.flags["trench over 12 m"] += 1
        if not cap_ok:
            self.flags["capacity or 3 m/s failed"] += 1

    def _summary(self, n_drop, n_backdrop, n_deep_drop):
        R, C = self.reaches, self.chambers
        km = sum(r["len"] for r in R) / 1000.0
        by_catch = collections.defaultdict(lambda: {"km": 0.0, "reaches": 0, "chambers": 0, "deepest": 0.0,
                                                     "trench_max": 0.0, "over_12": 0, "drops": 0, "washing_km": 0.0,
                                                     "cap_fail": 0, "wadi": 0, "dual_x": 0})
        for r in R:
            d = by_catch[r["catch"]]
            d["km"] += r["len"] / 1000.0; d["reaches"] += 1
            d["trench_max"] = max(d["trench_max"], r["trench_max"])
            d["drops"] += 1 if r["drop"] > 1e-6 else 0
            d["washing_km"] += r["len"] / 1000.0 if r["cleanse"] == "washing" else 0.0
            d["cap_fail"] += 0 if r["cap_ok"] else 1
            d["wadi"] += 1 if r["wadi"] else 0
            d["dual_x"] += 1 if r["dual_x"] else 0
        for c in C:
            d = by_catch[c["catch"]]
            d["chambers"] += 1
            d["deepest"] = max(d["deepest"], c["depth"])
            d["over_12"] += 1 if c["depth"] > self.max_depth else 0
        depths = np.array([c["depth"] for c in C]) if C else np.zeros(1)
        cl = collections.defaultdict(float)
        for r in R:
            cl[r["cleanse"]] += r["len"] / 1000.0
        return {"km": round(km, 1), "reaches": len(R), "chambers": len(C),
                "short_head_pipes_removed": len(self.dropped),
                "heads_on_a_bend": int(sum(1 for p in self.pipes if p.get("head_at_bend"))),
                "chambers_by_kind": dict(collections.Counter(c["kind"] for c in C)),
                "depth_median_m": round(float(np.median(depths)), 2),
                "depth_max_m": round(float(depths.max()), 2),
                "chambers_over_12m": int((depths > self.max_depth).sum()),
                "trench_over_12m": int(sum(1 for r in R if r["trench_max"] > self.max_depth)),
                "drops": n_drop, "backdrops_over_0p6": n_backdrop, "drops_over_2m": n_deep_drop,
                "steep_runs": int(sum(1 for p in self.pipes if p.get("steep"))),
                "capacity_fail": int(sum(1 for r in R if not r["cap_ok"])),
                "km_at_table11": round(sum(r["len"] for r in R if abs(r["slope"] - H.T11[r["dn"]]) < 1e-9) / 1000.0, 1),
                "km_steeper_by_cover": round(sum(r["len"] for r in R if r["slope"] > H.T11[r["dn"]] + 1e-9 and not r["steep"]) / 1000.0, 1),
                "km_at_3ms_with_drops": round(sum(r["len"] for r in R if r["steep"]) / 1000.0, 1),
                "cleanse_km": {k: round(v, 1) for k, v in cl.items()},
                "wadi_reaches": int(sum(1 for r in R if r["wadi"])),
                "dual_crossings": int(sum(1 for r in R if r["dual_x"])),
                "flags": dict(self.flags),
                "by_catch": {c: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items()}
                             for c, d in by_catch.items()}}


def write_pipes(out_dir, prefix, pipes, catch_info, epsg=32640):
    """The pipes as stage B laid them: stage A's records with the head moved, the ends on the
    chambers, the short head pipes gone; the fields the pipe style reads."""
    import os
    import geopandas as gpd
    from .export_tree import TIER_NAME
    live = [(i, p) for i, p in enumerate(pipes) if not p.get("dropped")]
    gpd.GeoDataFrame({
        "PIPE_ID": [f"P{i + 1:05d}" for i, _ in live],
        "TIER": [TIER_NAME.get(p["tier"], p["tier"]) for _, p in live],
        "ROLE": [p["tier"] for _, p in live],
        "CATCH": [p["catch"] for _, p in live],
        "OUT_TYPE": [catch_info[p["catch"]]["type"] for _, p in live],
        "LEN_M": [round(p["len"], 1) for _, p in live],
        "DN_MM": [int(p.get("dn_mm", 0)) for _, p in live],
        "SLOPE_PCT": [round(p.get("slope_b", 0.0) * 100, 3) for _, p in live],
        "Q_PEAK_LS": [round(p.get("q_peak_ls", 0.0), 2) for _, p in live],
        "INV_UP": [round(p.get("inv_up_b", 0.0), 3) for _, p in live],
        "INV_DN": [round(p.get("inv_dn_b", 0.0), 3) for _, p in live],
        "DEPTH_DN": [round(p.get("z_dn", 0.0) - p.get("inv_dn_b", 0.0), 2) for _, p in live],
        "HEAD_MOVED": [round(p.get("head_moved_m", 0.0), 1) for _, p in live],
    }, geometry=[p["geom"] for _, p in live], crs=f"EPSG:{epsg}").to_file(os.path.join(out_dir, f"{prefix}_pipes.shp"))


def write_shapes(out_dir, prefix, reaches, chambers, epsg=32640):
    import os
    import geopandas as gpd
    from .export_tree import TIER_NAME
    crs = f"EPSG:{epsg}"
    gpd.GeoDataFrame({
        "PIPE_ID": [f"P{r['pipe'] + 1:05d}" for r in reaches],
        "REACH": [r["reach"] for r in reaches],
        "CATCH": [r["catch"] for r in reaches],
        "TIER": [TIER_NAME.get(r["tier"], r["tier"]) for r in reaches],
        "ROLE": [r["tier"] for r in reaches],
        "DN_MM": [r["dn"] for r in reaches],
        "LEN_M": [round(r["len"], 1) for r in reaches],
        "SLOPE_PCT": [round(r["slope"] * 100, 3) for r in reaches],
        "INV_UP": [round(r["inv_up"], 3) for r in reaches],
        "INV_DN": [round(r["inv_dn"], 3) for r in reaches],
        "DEPTH_UP": [round(r["depth_up"], 2) for r in reaches],
        "DEPTH_DN": [round(r["depth_dn"], 2) for r in reaches],
        "TRENCH_MAX": [round(r["trench_max"], 2) for r in reaches],
        "Q_PEAK_LS": [round(r["q_peak_ls"], 2) for r in reaches],
        "PUMPED_LS": [round(r["pumped_ls"], 2) for r in reaches],
        "YD": [round(r["yd"], 3) for r in reaches],
        "V_MS": [round(r["v"], 3) for r in reaches],
        "CAP_OK": [int(r["cap_ok"]) for r in reaches],
        "Q_LOW_LS": [round(r["q_low_ls"], 3) for r in reaches],
        "V_LOW": [round(r["v_low"], 3) for r in reaches],
        "CLEANSE": [r["cleanse"] for r in reaches],
        "KIND": [r["kind"] for r in reaches],
        "DROP_M": [round(r["drop"], 2) for r in reaches],
        "STEEP": [int(r["steep"]) for r in reaches],
        "CAP3MS": [int(r.get("cap3ms", False)) for r in reaches],
        "COVER_MIN": [round(r.get("cover_min", 0.0), 2) for r in reaches],
        "COV_SHORT": [round(r.get("cover_short", 0.0), 2) for r in reaches],
        "AGAINST": [int(r["z_dn"] > r["z_up"] + 0.05) for r in reaches],
        "LEN_OVER": [int(r["len"] > spacing_for(r["dn"]) + 0.05) for r in reaches],
        "WADI": [int(r["wadi"]) for r in reaches],
        "DUAL_X": [int(r["dual_x"]) for r in reaches],
    }, geometry=[r["geom"] for r in reaches], crs=crs).to_file(os.path.join(out_dir, f"{prefix}_reaches.shp"))
    gpd.GeoDataFrame({
        "CH_ID": [f"C{i + 1:05d}" for i in range(len(chambers))],
        "CATCH": [c["catch"] for c in chambers],
        "KIND": [c["kind"] for c in chambers],
        "Z_GROUND": [round(c["z"], 2) for c in chambers],
        "INVERT": [round(c["invert"], 3) for c in chambers],
        "DEPTH": [round(c["depth"], 2) for c in chambers],
        "DROP_M": [round(c["drop"], 2) for c in chambers],
        "BACKDROP": [int(c["drop"] > 0.6) for c in chambers],
        "OVER_12": [int(c["depth"] > 12.0) for c in chambers],
        "CAP3MS": [int(c.get("cap3ms", False)) for c in chambers],
        "HEAD_HOW": [c.get("head_how", "") for c in chambers],
    }, geometry=[Point(c["x"], c["y"]) for c in chambers], crs=crs).to_file(os.path.join(out_dir, f"{prefix}_chambers.shp"))


def find_issues(reaches, chambers, pipes, cfg, cover_crown=1.3, cover_wadi=1.5):
    """The eight checks the engineer asked for on 2026-09-12. Returns point issues
    (x, y, type, detail) and the counts by type."""
    import collections as _c
    close_m = float(getattr(cfg, "CLOSE_CHAMBER_M", 5.0))
    bend_deg = float(getattr(cfg, "BEND_DEG", 5.0))
    issues = []
    # 1. chambers closer than close_m
    pts = [Point(c["x"], c["y"]) for c in chambers]
    tree = STRtree(pts)
    seen = set()
    for i, pt in enumerate(pts):
        for j in tree.query(pt.buffer(close_m)):
            j = int(j)
            if j <= i or (i, j) in seen:
                continue
            d = pt.distance(pts[j])
            if d < close_m:
                seen.add((i, j))
                issues.append((pt.x, pt.y, "close chambers", f"{d:.1f} m apart ({chambers[i]['kind']} / {chambers[j]['kind']})"))
    # 2. a reach longer than its spacing
    for r in reaches:
        if r["len"] > spacing_for(r["dn"]) + 0.05:
            m = r["geom"].interpolate(0.5, normalized=True)
            issues.append((m.x, m.y, "reach over spacing", f"{r['len']:.0f} m, DN{r['dn']} allows {spacing_for(r['dn']):.0f}"))
    # 3. an invert rising along the flow, or a junction outlet above an inlet
    for r in reaches:
        if r["inv_dn"] > r["inv_up"] + 1e-6:
            m = r["geom"].interpolate(0.5, normalized=True)
            issues.append((m.x, m.y, "invert rises", f"{r['inv_up']:.2f} -> {r['inv_dn']:.2f}"))
    arr = _c.defaultdict(list)
    for p in pipes:
        if "inv_dn_b" in p:
            arr[p["dn"]].append(p["inv_dn_b"])
    for p in pipes:
        u = p["up"]
        if u in arr and "inv_up_b" in p and p["inv_up_b"] > min(arr[u]) + 1e-6:
            issues.append((u[0], u[1], "outlet above inlet", f"out {p['inv_up_b']:.2f} above in {min(arr[u]):.2f}"))
    # 4. a bend with no chamber
    ch_tree = STRtree(pts)
    for p in pipes:
        if p.get("dropped"):
            v = Point(p["geom"].coords[-1])
            issues.append((v.x, v.y, "short head pipe removed", p["dropped"]))
            continue
        coords = list(p["geom"].coords)
        acc = 0.0
        for i in range(1, len(coords) - 1):
            acc += math.dist(coords[i - 1], coords[i])
            a1 = math.atan2(coords[i][1] - coords[i - 1][1], coords[i][0] - coords[i - 1][0])
            a2 = math.atan2(coords[i + 1][1] - coords[i][1], coords[i + 1][0] - coords[i][0])
            d = abs(math.degrees(a2 - a1)) % 360.0
            turn = min(d, 360.0 - d)
            if turn > bend_deg:
                v = Point(coords[i])
                near = [int(j) for j in ch_tree.query(v.buffer(1.5)) if pts[int(j)].distance(v) < 1.5]
                sep = float(getattr(cfg, "CHAMBER_SEP_M", 10.0))
                taken = [int(j) for j in ch_tree.query(v.buffer(sep)) if pts[int(j)].distance(v) < sep
                         and chambers[int(j)]["kind"] in ("junction", "outlet", "head")]
                if not near and not taken:      # a bend within sep of an end chamber is that chamber's
                    issues.append((v.x, v.y, "bend without chamber", f"{turn:.0f} degrees"))
    # 4b. a gentle bend absorbed into the chamber at its end (within the separation)
    #     is not an issue; a sharp one is caught above. Nothing to add here.
    # 5. cover short along a trench, each point against its own requirement (1.5 m inside a wadi)
    for r in reaches:
        if r.get("cover_short", 0.0) > 0.05:
            m = r["geom"].interpolate(0.5, normalized=True)
            issues.append((m.x, m.y, "cover short in trench", f"short by {r['cover_short']:.2f} m"))
    # 6. a chamber shallower than cover plus pipe
    for c in chambers:
        dn = pipes[c["pipe"]]["dn_mm"] if c.get("pipe") is not None else 200
        need = cover_crown + H.outside(dn)
        if c["depth"] < need - 0.05:
            issues.append((c["x"], c["y"], "chamber shallower than cover", f"{c['depth']:.2f} m against {need:.2f}"))
    # 7. capacity or velocity failing
    for r in reaches:
        if not r["cap_ok"]:
            m = r["geom"].interpolate(0.5, normalized=True)
            issues.append((m.x, m.y, "capacity or 3 m/s failed", f"d/D {r['yd']:.2f}, v {r['v']:.2f} m/s"))
    # 8. a head not at a gate
    for c in chambers:
        if c["kind"] == "head" and c.get("head_how", "") not in ("gate", ""):
            issues.append((c["x"], c["y"], "head not at a gate", c.get("head_how", "")))
    counts = dict(_c.Counter(t for _, _, t, _ in issues))
    return issues, counts


def write_issues(out_dir, prefix, issues, epsg=32640):
    import os
    import geopandas as gpd
    crs = f"EPSG:{epsg}"
    gpd.GeoDataFrame({"TYPE": [t for _, _, t, _ in issues], "DETAIL": [d for _, _, _, d in issues]},
                     geometry=[Point(x, y) for x, y, _, _ in issues], crs=crs).to_file(
        os.path.join(out_dir, f"{prefix}_issues.shp"))
