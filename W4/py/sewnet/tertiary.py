"""sewnet.tertiary — S3b: schematic riders/house connections + the plot-connectability
elevation check (user mandate 2026-08-18).

Roads are locally elevated (flood protection, underpasses), so a house can sit BELOW
the sewer in the road. For every loaded unit:

    available head = plot ground (0.5 m terrain) - PLOT_OUTLET_DEPTH
    required invert at the manhole <= available head - CONN_CHECK_SLOPE * distance

Failing units are LOW_PLOT flags. Manholes with failing units get a deepening
requirement (node_min_depth) and the invert solver re-runs; units that STILL fail
after deepening (12 m cap) are reported as local-solution candidates — never dropped.

Schematic rider layer: per manhole, its assigned units grouped <=3 per rider
(G203-p19 §3.4), rider drawn unit->...->manhole; PCS length > 50 m flagged (p18 Tab 4).
Concept grade — hydraulic design stays at collector level.
"""

import math
from shapely.geometry import LineString

from . import criteria as C


def connectability(units_by_mh, nodes, sampler):
    """Check every unit can gravity-connect to its manhole's designed invert.
    Returns (results, deepen) where deepen = {node: extra_required_invert_depth}."""
    results = []
    deepen = {}
    for mh, units in units_by_mh.items():
        node = nodes[mh]
        if node.get("invert") is None:
            continue
        for u in units:
            zu = sampler.z(u["x"], u["y"])
            dist = max(u["dist"], 5.0)
            head = zu - C.PLOT_OUTLET_DEPTH
            need = node["invert"] + C.CONN_CHECK_SLOPE * dist
            margin = head - need
            rec = {"id": u["id"], "mh": nodes[mh]["label"], "mh_key": mh, "cls": u["cls"],
                   "x": u["x"], "y": u["y"],
                   "plot_z": zu, "dist": dist, "margin": margin, "ok": margin >= 0.0}
            results.append(rec)
            if margin < 0.0:
                # manhole must sit deeper by the deficit for this unit to connect;
                # capped 0.5 m short of the 12 m limit so mid-span depth between the
                # deepened node and rising ground cannot breach MAX_DEPTH
                req_depth = node["z"] - (head - C.CONN_CHECK_SLOPE * dist)
                cap = C.MAX_DEPTH - 0.5
                deepen[mh] = min(max(deepen.get(mh, 0.0), req_depth), cap)
    return results, deepen


def recheck(results, nodes):
    """Re-evaluate stored results against (re-solved) node inverts."""
    still = []
    for r in results:
        node = nodes[r["mh_key"]]
        need = node["invert"] + C.CONN_CHECK_SLOPE * r["dist"]
        r["margin"] = (r["plot_z"] - C.PLOT_OUTLET_DEPTH) - need
        r["ok"] = r["margin"] >= 0.0
        if not r["ok"]:
            still.append(r)
    return still


def riders(units_by_mh, nodes):
    """Schematic rider/PCS geometry: <=3 units chain to one rider into the manhole.
    Returns list of {geom, mh, n_units, length, flag}."""
    out = []
    for mh, units in units_by_mh.items():
        node = nodes[mh]
        units_sorted = sorted(units, key=lambda u: u["dist"])
        for i in range(0, len(units_sorted), C.MAX_HCC_PER_RIDER):
            grp = units_sorted[i:i + C.MAX_HCC_PER_RIDER]
            pts = [(u["x"], u["y"]) for u in grp] + [(node["x"], node["y"])]
            geom = LineString(pts)
            flag = ""
            if any(u["dist"] > C.PCS_MAX_LEN for u in grp):
                flag = "PCS>50m"
            out.append({"geom": geom, "mh": node.get("label", ""), "n_units": len(grp),
                        "length": geom.length, "flag": flag})
    return out
