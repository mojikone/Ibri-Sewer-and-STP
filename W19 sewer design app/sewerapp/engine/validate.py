"""User notifications (SewerGEMS's validation list), 2026-11-23 v3: what is wrong or doubtful in a model before or after a
run, each with its element so the editor can take the engineer to it. Errors stop a solve; warnings do not."""
import math
import numpy as np


def run(p, res=None):
    N, L = p.nodes, p.links; out = []
    add = lambda level, table, eid, msg: out.append(dict(level=level, table=table, id=str(eid), message=msg))
    ids = set(N.index)
    for lid, r in L.iterrows():
        for end in (r.from_node, r.to_node):
            if end not in ids: add("error", "links", lid, f"its node {end} does not exist")
    leave = L[~L.kind.isin(["pump", "orifice", "weir"])].from_node.value_counts()
    for n, k in leave[leave > 1].items(): add("error", "nodes", n, f"{k} pipes leave it (a sewer network is a tree)")
    used = set(L.from_node) | set(L.to_node)
    for n, r in N.iterrows():
        if n not in used: add("warning", "nodes", n, "not connected to any pipe")
        if r.kind != "pressure_junction" and r.ground == r.ground and r.invert == r.invert and r.invert > r.ground: add("error", "nodes", n, f"invert {r.invert:.2f} above ground {r.ground:.2f}")
        if r.ground == 0 and r.invert == -1.5 and r.kind == "manhole": add("warning", "nodes", n, "ground and invert still at the prototype's default (0 and -1.5 m)")
    outs = set(N.index[N.kind == "outfall"])
    for n, k in L.to_node[L.to_node.isin(outs)].value_counts().items():
        if k > 1: add("warning", "nodes", n, f"{k} links reach this outfall: SWMM takes one (join them at a manhole first)")
    if len(L) and not outs: add("error", "nodes", "", "the network has no outfall")
    fr = set(L.from_node)
    for n in used:
        if n in ids and n not in fr and n not in outs and N.kind.get(n) not in ("storage",): add("warning", "nodes", n, "the flow ends here: it is not an outfall")
    for lid, r in L.iterrows():
        if not (r.length_m > 0): add("error", "links", lid, "zero length")
        if r.kind == "conduit" and not (r.dn_mm > 0) and lid not in (p.sections or {}): add("error", "links", lid, "no size or section")
        if r.kind == "conduit" and r.length_m and r.up_inv == r.up_inv and r.dn_inv == r.dn_inv and r.up_inv <= r.dn_inv:
            add("warning", "links", lid, f"flat or adverse ({(r.up_inv - r.dn_inv) / r.length_m * 100:.3f} %)")
        if r.kind == "pressure_pipe" and not (r.inside_mm == r.inside_mm and r.inside_mm > 0): add("error", "links", lid, "a pressure pipe with no bore")
        if r.kind == "pump":
            pu = (getattr(p, "pumps", None) or {}).get(lid)
            if not pu: add("warning", "links", lid, "no definition or capacity: the steady run passes its inflow, the storm run pumps ideally")
            if N.kind.get(r.from_node) not in ("wetwell", "storage"): add("warning", "links", lid, f"draws from {r.from_node}, which is not a wet well")
    if res is not None:
        for lid, r in res.iterrows():
            if r.get("cannot_lift") is True or r.get("cannot_lift") == 1.0: add("error", "links", lid, "the pump cannot lift: its shutoff head is below the static lift")
            elif r.get("short") is True or r.get("short") == 1.0: add("warning", "links", lid, f"the pump is short: {r.get('pump_head_m', float('nan')):.1f} m at the flow, {r.get('tdh_m', float('nan')):.1f} m needed")
            if r.get("negative_pressure") is True or r.get("negative_pressure") == 1.0: add("warning", "links", lid, "negative pressure along the force main (a high point)")
            if r.get("surcharged") is True and r.get("kind") == "conduit": add("warning", "links", lid, "surcharged in the steady run")
    k = 0.05                                                                      # coincident structures
    seen = {}
    for n, r in N.iterrows():
        key = (round(r.x / k), round(r.y / k))
        if key in seen: add("warning", "nodes", n, f"on top of {seen[key]}")
        else: seen[key] = n
    order = {"error": 0, "warning": 1}
    return sorted(out, key=lambda x: (order[x["level"]], x["table"], x["id"]))
