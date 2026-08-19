"""SweepEntry — make branch pipes enter a chamber going WITH the flow.

G203-p30 says plainly: "No inlet pipe at manholes shall have an angle less than 90 deg to
the direction of flow." A branch that arrives pointing backwards would turn the sewage back
on itself inside the chamber, and solids drop out where that happens.

Street corners do not care about that rule, so a branch laid straight down its street can
arrive at a bad angle. The fix is what a designer draws: turn the branch in two smaller
steps instead of one sharp one. A bend chamber goes in a few metres short of the junction,
so the flow turns half the angle there and half at the junction — and half of anything up
to 180 degrees is never more than 90.

The bend chamber has to sit in the road, at least 2 m clear of any plot, so where there is
no room the junction is listed for the chamber schedule as needing a special swept channel
instead.
"""

import math

from shapely.geometry import LineString

from ..criteria import DEFAULT
from ..model import key_of


class SweepEntry:
    def __init__(self, sampler, crit=DEFAULT, setbacks=(3.0, 4.5, 6.0, 8.0)):
        self.sampler = sampler
        self.crit = crit
        self.setbacks = setbacks
        self.report = {}

    @staticmethod
    def _clean(coords):
        out = [tuple(coords[0])]
        for p in coords[1:]:
            p = tuple(p)
            if p != out[-1]:
                out.append(p)
        return out

    @staticmethod
    def _bearing(a, b):
        return math.atan2(b[1] - a[1], b[0] - a[0])

    @staticmethod
    def _turn(b1, b2):
        d = abs(math.degrees(b2 - b1)) % 360.0
        return min(d, 360.0 - d)

    def _worst_interior(self, coords):
        m = 0.0
        for i in range(1, len(coords) - 1):
            m = max(m, self._turn(self._bearing(coords[i - 1], coords[i]),
                                  self._bearing(coords[i], coords[i + 1])))
        return m

    def run(self, net, clear_fn=None, passes=3):
        sharp = swept = 0
        blocked = []
        for _ in range(passes):
            rep = self._one_pass(net, clear_fn)
            sharp, blocked = rep["sharp_inlets"], rep["blocked"]
            swept += rep["bend_chambers_added"]
            if rep["bend_chambers_added"] == 0:
                break
        for r in net.reaches:
            r.profile = []                          # geometry moved: re-sample the ground
        self.report = {"sharp_inlets": sharp, "bend_chambers_added": swept,
                       "needs_special_chamber": len(set(blocked))}
        return self.report

    def _one_pass(self, net, clear_fn=None):
        C = self.crit
        G = net.digraph()
        heads = set(net.heads())
        others = [(c.x, c.y) for c in net.chambers.values()]
        sharp, swept, blocked = 0, 0, []
        jobs = []
        for k in list(G.nodes):
            succ = list(G.successors(k))
            if not succ:
                continue
            co = self._clean(list(G[k][succ[0]]["reach"].geom.coords))
            bo = self._bearing(co[0], co[1])
            for u in list(G.predecessors(k)):
                r = G[u][k]["reach"]
                ci = self._clean(list(r.geom.coords))
                if len(ci) < 2:
                    continue
                bi = self._bearing(ci[-2], ci[-1])
                if self._turn(bi, bo) <= 91.0:
                    continue
                jobs.append((r, ci, bi, bo, k))

        for r, ci, bi, bo, k in jobs:
            sharp += 1
            # signed turn, so the bend chamber goes on the side the branch comes from
            s = math.atan2(math.sin(bo - bi), math.cos(bo - bi))
            bm = bi + s / 2.0                       # halfway between the two directions
            kx, ky = ci[-1]
            placed = False
            for L in self.setbacks:
                if L > 0.45 * r.length:
                    continue
                vx, vy = kx - L * math.cos(bm), ky - L * math.sin(bm)
                if clear_fn is not None and not clear_fn(vx, vy):
                    continue
                # a new chamber must not crowd an existing one, nor sit so close to the
                # start of a branch that the two read as the same structure
                if any((vx - ox) ** 2 + (vy - oy) ** 2 < C.MH_MIN_CLEAR_M ** 2
                       for ox, oy in others):
                    continue
                if any((vx - net.chambers[h].x) ** 2 + (vy - net.chambers[h].y) ** 2
                       < C.FANOUT_OFFSET_M ** 2 for h in heads):
                    continue
                head = self._clean(ci[:-1] + [(vx, vy)])
                if len(head) < 2 or LineString(head).length < 1.0:
                    continue
                if self._worst_interior(head) > C.ROAD_BEND_DEG:
                    continue                        # the branch itself would kink
                if self._turn(self._bearing(head[-2], head[-1]),
                              self._bearing((vx, vy), (kx, ky))) > 89.0:
                    continue                        # bend chamber still too sharp
                if self._turn(self._bearing((vx, vy), (kx, ky)), bo) > 89.0:
                    continue                        # junction still too sharp
                vk = key_of(vx, vy)
                if vk in net.chambers:
                    continue
                up = r.up
                net.remove_reach(r)
                net.add_chamber(vx, vy, float(self.sampler.z(vx, vy)), kind="bend")
                net.add_reach(up, vk, LineString(head))
                net.add_reach(vk, key_of(kx, ky), LineString([(vx, vy), (kx, ky)]))
                others.append((vx, vy))
                swept += 1
                placed = True
                break
            if not placed:
                blocked.append(net.chambers[k].label)
                net.chambers[k].swept_entry = True

        return {"sharp_inlets": sharp, "bend_chambers_added": swept, "blocked": blocked}
