"""ConnectabilityStage — S3b: schematic riders plus the house-connection elevation check.

User mandate 2026-08-18: roads are locally elevated (flood protection, underpasses), so a
house can sit BELOW the sewer in the road. For every loaded unit:

    available head = plot ground (0.5 m terrain) - PLOT_OUTLET_DEPTH
    required at the chamber = chamber invert + CONN_CHECK_SLOPE x distance

Failures raise a deepening requirement on that chamber and the invert solve re-runs; units
that still fail after deepening (capped short of the 12 m limit) are reported as
local-solution candidates — never dropped.

Rider layer is schematic: units grouped <=3 per rider (G203-p19 §3.4), drawn to the
chamber, PCS length >50 m flagged (p18 Tab 4). Hydraulic design stays at collector level.
"""

from shapely.geometry import LineString

from ..criteria import DEFAULT
from ..model import Network


class ConnectabilityStage:
    def __init__(self, sampler, crit=DEFAULT):
        self.sampler = sampler
        self.crit = crit
        self.report = {}

    def check(self, net: Network, per_chamber):
        """-> (results, deepen) where deepen = {chamber key: required invert depth}."""
        C = self.crit
        results, deepen = [], {}
        for k, units in per_chamber.items():
            ch = net.chambers.get(k)
            if ch is None or ch.invert is None:
                continue
            for u in units:
                zu = self.sampler.z(u.x, u.y)
                dist = max(u.dist, 5.0)
                head = zu - C.PLOT_OUTLET_DEPTH
                margin = head - (ch.invert + C.CONN_CHECK_SLOPE * dist)
                results.append({"id": u.id, "mh": ch.label, "mh_key": k, "cls": u.cls,
                                "x": u.x, "y": u.y, "plot_z": zu, "dist": dist,
                                "margin": margin, "ok": margin >= 0.0})
                if margin < 0.0:
                    # chamber must sit deeper; capped 0.5 m short of the 12 m limit so the
                    # mid-span depth toward rising ground cannot breach MAX_DEPTH
                    req = ch.z - (head - C.CONN_CHECK_SLOPE * dist)
                    deepen[k] = min(max(deepen.get(k, 0.0), req), C.MAX_DEPTH - 0.5)
        return results, deepen

    @staticmethod
    def recheck(results, net: Network, crit=DEFAULT):
        still = []
        for r in results:
            ch = net.chambers[r["mh_key"]]
            r["margin"] = (r["plot_z"] - crit.PLOT_OUTLET_DEPTH) - \
                (ch.invert + crit.CONN_CHECK_SLOPE * r["dist"])
            r["ok"] = r["margin"] >= 0.0
            if not r["ok"]:
                still.append(r)
        return still

    def riders(self, net: Network, per_chamber):
        C = self.crit
        out = []
        for k, units in per_chamber.items():
            ch = net.chambers.get(k)
            if ch is None:
                continue
            for i in range(0, len(units), C.MAX_HCC_PER_RIDER):
                grp = sorted(units, key=lambda u: u.dist)[i:i + C.MAX_HCC_PER_RIDER]
                geom = LineString([(u.x, u.y) for u in grp] + [ch.xy])
                out.append({"geom": geom, "mh": ch.label, "n_units": len(grp),
                            "length": geom.length,
                            "flag": "PCS>50m" if any(u.dist > C.PCS_MAX_LEN for u in grp) else ""})
        return out

    def apply_deepening(self, net: Network, deepen):
        for k, d in deepen.items():
            if k in net.chambers:
                net.chambers[k].min_depth_req = d
