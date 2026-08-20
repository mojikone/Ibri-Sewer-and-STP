"""House connections — where each property joins the sewer, and whether it can.

What was wrong before: the joining point was the middle of the plot, and the line ran
from there to whichever chamber was nearest in a straight line. That drew pipes across
blocks and through other people's plots. Sewers do not do that.

How it works now (rules agreed 2026-08-19):

  * the joining point sits on the ROAD — the plot is projected straight out to the
    nearest sewer line, so the connection is a short spur at right angles
  * the plot loads the pipe it actually faces, not the nearest chamber in a straight line
  * up to 3 house chambers share one rider (the small pipe along the plot frontage);
    a house on its own gets its own lateral straight to the sewer
  * empty plots still get a capped stub-out, ready for when they are built
  * the level check uses the invert (inside bottom of the pipe) AT THE JOINING POINT,
    worked out along the pipe, not the invert at the far chamber

Everything here is schematic. The one thing that must be right is the level check: can
the house actually drain into the sewer by gravity, given the road may sit higher than
the plot.
"""

import math

import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

from ..criteria import DEFAULT
from ..model import Network


class ConnectabilityStage:
    def __init__(self, sampler, crit=DEFAULT):
        self.sampler = sampler
        self.crit = crit
        self.report = {}

    # ---------------- where each plot joins the sewer ----------------
    def attach(self, net: Network, units):
        """Project every property out to the nearest sewer line and remember the spot.

        Returns per_chamber, keyed by the chamber at the DOWNSTREAM end of the pipe the
        plot joins, because that is where its flow ends up."""
        reaches = net.reaches
        if not reaches:
            return {}, 0.0
        mids = np.array([[r.geom.interpolate(0.5, normalized=True).x,
                          r.geom.interpolate(0.5, normalized=True).y] for r in reaches])
        tree = cKDTree(mids)
        per_chamber = {}
        worst = 0.0
        for u in units:
            # measure from the plot EDGE (its gate side), not the middle of the plot —
            # a big plot's centre can be 200 m from the road while its gate is on it
            shape = u.geom if u.geom is not None else Point(u.x, u.y)
            best, best_d = None, 1e18
            k = min(25, len(reaches))
            for idx in tree.query([u.x, u.y], k=k)[1].ravel():
                r = reaches[int(idx)]
                d = r.geom.distance(shape)
                if d < best_d:
                    best, best_d = r, d
            if best is None:
                continue
            gate, join = nearest_points(shape, best.geom)     # gate -> joining point
            u.x, u.y = gate.x, gate.y                         # the connection starts here
            ch = best.geom.project(join)                      # how far along the pipe
            p = best.geom.interpolate(ch)
            u.conn_x, u.conn_y = p.x, p.y
            u.conn_reach = id(best)
            u.conn_chainage = ch
            u.dist = best_d                                  # the spur length
            u.chamber = best.dn
            per_chamber.setdefault(best.dn, []).append(u)
            worst = max(worst, best_d)
        return per_chamber, worst

    # ---------------- can it drain? ----------------
    def check(self, net: Network, per_chamber):
        """Compare the house outlet level with the pipe invert at the joining point."""
        C = self.crit
        by_id = {id(r): r for r in net.reaches}
        results, deepen = [], {}
        for k, units in per_chamber.items():
            ch = net.chambers.get(k)
            if ch is None:
                continue
            for u in units:
                r = by_id.get(u.conn_reach)
                if r is None or r.inv_up is None:
                    continue
                # invert at the joining point, worked out along the pipe
                inv_here = r.inv_up - r.slope * min(u.conn_chainage, r.length)
                zu = self.sampler.z(u.x, u.y)
                spur = max(u.dist, 3.0)
                head = zu - C.PLOT_OUTLET_DEPTH
                margin = head - (inv_here + C.CONN_CHECK_SLOPE * spur)
                results.append({"id": u.id, "mh": ch.label, "mh_key": k, "cls": u.cls,
                                "x": u.x, "y": u.y, "cx": u.conn_x, "cy": u.conn_y,
                                "plot_z": zu, "dist": spur, "inv_here": inv_here,
                                "margin": margin, "ok": margin >= 0.0,
                                "n_props": getattr(u, "n_props", 1.0)})
                if margin < 0.0:
                    need = ch.z - (head - C.CONN_CHECK_SLOPE * spur)
                    deepen[k] = min(max(deepen.get(k, 0.0), need), C.MAX_DEPTH - 0.5)
        return results, deepen

    @staticmethod
    def recheck(results, net: Network, crit=DEFAULT):
        by_id = {id(r): r for r in net.reaches}
        still = []
        for res in results:
            ch = net.chambers.get(res["mh_key"])
            if ch is None or ch.invert is None:
                continue
            res["margin"] = (res["plot_z"] - crit.PLOT_OUTLET_DEPTH) - \
                (ch.invert + crit.CONN_CHECK_SLOPE * res["dist"])
            res["ok"] = res["margin"] >= 0.0
            if not res["ok"]:
                still.append(res)
        return still

    # ---------------- the drawn connections ----------------
    def connections(self, net: Network, per_chamber):
        """Three separate things, kept in separate output layers:

        spurs   — the short line from the plot out to its joining point on the sewer
        riders  — the line along the frontage joining up to 3 house chambers
        stubs   — capped connections left for empty plots, ready for when they are built
        """
        C = self.crit
        spurs, riders, stubs = [], [], []
        for k, units in per_chamber.items():
            ch = net.chambers.get(k)
            if ch is None:
                continue
            # sort along the street so a rider joins NEIGHBOURS, not scattered plots
            us = sorted(units, key=lambda u: u.conn_chainage)
            group = []
            for u in us:
                line = LineString([(u.x, u.y), (u.conn_x, u.conn_y)])
                rec = {"geom": line, "mh": ch.label, "plot": str(u.id), "cls": u.cls,
                       "n_props": getattr(u, "n_props", 1.0), "len_m": line.length,
                       "flag": "PCS>50m" if line.length > C.PCS_MAX_LEN else ""}
                if u.cls == "P":
                    rec["kind"] = "stub-out"          # empty plot: capped, waiting
                    stubs.append(rec)
                else:
                    rec["kind"] = "spur"
                    spurs.append(rec)
                group.append(u)
                if len(group) == C.MAX_HCC_PER_RIDER:
                    riders.append(self._rider(group, ch))
                    group = []
            if len(group) > 1:                        # 2 or 3 neighbours share a rider
                riders.append(self._rider(group, ch))
            # a lone house gets no rider — its spur is its lateral (G203 wording)
        return spurs, [r for r in riders if r], stubs

    @staticmethod
    def _rider(group, ch):
        pts = [(u.conn_x, u.conn_y) for u in group]
        if len(pts) < 2:
            return None
        return {"geom": LineString(pts), "mh": ch.label, "n_units": len(group),
                "length": LineString(pts).length, "kind": "rider",
                "flag": "" if len(group) <= 3 else ">3 HCC"}

    def apply_deepening(self, net: Network, deepen):
        for k, d in deepen.items():
            if k in net.chambers:
                net.chambers[k].min_depth_req = d
