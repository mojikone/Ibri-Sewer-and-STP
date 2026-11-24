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
    leave = L[~L.kind.isin(["orifice", "weir"])].from_node.value_counts()
    pumps_at = L[L.kind == "pump"].from_node.value_counts()
    for n, k in leave[leave > 1].items():
        if pumps_at.get(n, 0) > 1 and pumps_at.get(n, 0) == k:
            add("error", "nodes", n, f"{k} pumps leave it: draw one pump and give it the number of duty pumps (Properties > Pumps running)")
        else: add("error", "nodes", n, f"{k} links leave it (a sewer network is a tree)")
    s = p.settings; pk = (s.get("peaking") or {})
    if pk.get("method") in ("harmon", "ten_states", "babbitt") and not pk.get("pe_per_m3d"):
        units = {u["name"]: u for u in ((s.get("libraries") or {}).get("unit_loads") or [])}
        pop = any(units.get(nm, {}).get("type") == "population" or units.get(nm, {}).get("pe") for S in (getattr(p, "unit_rows", None) or {}).values() for rows in S.values() for nm, _ in rows)
        if not pop: add("warning", "nodes", "", "a population peaking method with no population: every factor is 1 (give unit loads of the population type, population equivalents, or people per m3/d in Settings > Peaking)")
    pm = (s.get("pressure") or {}).get("method", "hazen")
    for lid, o in (getattr(p, "ppipes", None) or {}).items():
        if o.get("method") and o["method"] != pm and lid in L.index: add("warning", "links", lid, f"its own friction method ({o['method']}) is written to SWMM as the project's ({pm}): SWMM takes one force-main equation")
    used = set(L.from_node) | set(L.to_node)
    for n, r in N.iterrows():
        if n not in used: add("warning", "nodes", n, "not connected to any pipe")
        if r.kind != "pressure_junction" and r.ground == r.ground and r.invert == r.invert and r.invert > r.ground: add("error", "nodes", n, f"invert {r.invert:.2f} above ground {r.ground:.2f}")
        if r.ground == 0 and r.invert in (-1.5, -3.0) and r.kind != "outfall": add("warning", "nodes", n, f"ground and invert still at the prototype's default (0 and {r.invert} m)")
    outs = set(N.index[N.kind == "outfall"])
    for n, k in L.to_node[L.to_node.isin(outs)].value_counts().items():
        if k > 1: add("warning", "nodes", n, f"{k} links reach this outfall: SWMM takes one (join them at a manhole first)")
    if len(L) and not outs: add("error", "nodes", "", "the network has no outfall")
    fr = set(L.from_node)
    for n in used:
        if n in ids and n not in fr and n not in outs and N.kind.get(n) not in ("storage",): add("warning", "nodes", n, "the flow ends here: it is not an outfall")
    for lid, r in L.iterrows():
        if r.kind in ("conduit", "pressure_pipe") and not (r.length_m > 0): add("error", "links", lid, "zero length")
        if r.kind == "conduit" and not (r.dn_mm > 0) and lid not in (p.sections or {}): add("error", "links", lid, "no size or section")
        if r.kind == "conduit" and r.length_m and r.up_inv == r.up_inv and r.dn_inv == r.dn_inv and r.up_inv <= r.dn_inv:
            add("warning", "links", lid, f"flat or adverse ({(r.up_inv - r.dn_inv) / r.length_m * 100:.3f} %)")
        if r.kind == "pressure_pipe" and not (r.inside_mm == r.inside_mm and r.inside_mm > 0): add("error", "links", lid, "a pressure pipe with no bore")
        if r.kind == "pump":
            pu = (getattr(p, "pumps", None) or {}).get(lid)
            if not pu: add("warning", "links", lid, "no definition or capacity: the steady run passes its inflow, the storm run pumps ideally")
            if N.kind.get(r.from_node) not in ("wetwell", "storage"): add("warning", "links", lid, f"draws from {r.from_node}, which is not a wet well")
        if r.kind in ("orifice", "weir") and not (getattr(p, "outlets", None) or {}).get(lid): add("warning", "links", lid, f"its {r.kind} geometry is not set: SWMM takes the defaults shown in Properties")
    out_kinds = L.groupby("from_node").kind.apply(set) if len(L) else {}
    for n, ks in (out_kinds.items() if len(L) else []):
        if ks and ks <= {"orifice", "weir"}: add("warning", "nodes", n, "its only outlets are orifices or weirs: the steady sanitary run passes nothing on from it (they act in the storm run)")
    if res is not None:
        for lid, r in res.iterrows():
            if r.get("cannot_lift") is True or r.get("cannot_lift") == 1.0: add("error", "links", lid, "the pump cannot lift: its shutoff head is below the static lift")
            elif r.get("short") is True or r.get("short") == 1.0: add("warning", "links", lid, f"the pump is short: {r.get('pump_head_m', float('nan')):.1f} m at the flow, {r.get('tdh_m', float('nan')):.1f} m needed")
            if r.get("negative_pressure") is True or r.get("negative_pressure") == 1.0: add("warning", "links", lid, "negative pressure along the force main (a high point)")
            if r.get("surcharged") is True and r.get("kind") == "conduit": add("warning", "links", lid, "surcharged in the steady run")
            if r.get("off_curve") is True or r.get("off_curve") == 1.0: add("warning", "links", lid, "the pump runs off the end of its curve against this main")
    if res is not None:                                                           # the GVF profile (when chosen)
        for n in res.attrs.get("flooding") or []: add("warning", "nodes", n, "the water level (GVF) is above the ground")
        if "surcharged_gvf" in res.columns:
            for lid in res.index[res.surcharged_gvf.fillna(False).astype(bool)]: add("warning", "links", lid, "surcharged at its upstream end (GVF)")
    k = 0.05                                                                      # coincident structures
    seen = {}
    for n, r in N.iterrows():
        if not (r.x == r.x and r.y == r.y): add("warning", "nodes", n, "no coordinates"); continue
        key = (round(r.x / k), round(r.y / k))
        if key in seen: add("warning", "nodes", n, f"on top of {seen[key]}")
        else: seen[key] = n
    xs, ys = N.x.to_dict(), N.y.to_dict()                                         # a drawn line that misses a structure
    for lid, c, a, b in zip(p.links.index, p.links.coords, p.links.from_node, p.links.to_node):
        if not (isinstance(c, list) and len(c) >= 2) or a not in xs or b not in xs: continue
        da, db = math.dist(c[0][:2], (xs[a], ys[a])), math.dist(c[-1][:2], (xs[b], ys[b]))
        if max(da, db) > 1.0:
            add("warning", "links", lid, f"its drawn line misses {'its upstream' if da >= db else 'its downstream'} structure by {max(da, db):.1f} m "
                                         f"(the line {sum(math.dist(c[i][:2], c[i + 1][:2]) for i in range(len(c) - 1)):.1f} m, the structures {math.dist((xs[a], ys[a]), (xs[b], ys[b])):.1f} m apart)")
    cop = [n for n, v in (getattr(p, "ground_src", None) or {}).items() if str(v).startswith("Copernicus") and n in ids]
    if cop:                                                                       # one line, not one per structure
        add("warning", "nodes", cop[0], f"{len(cop)} structure{'s take' if len(cop) > 1 else ' takes'} its ground level from the Copernicus 30 m surface model "
                                        f"(roofs and trees included, metres of error, EGM2008 heights): screening only, not design levels; replace them from a survey or a finer terrain")
    order = {"error": 0, "warning": 1}
    return sorted(out, key=lambda x: (order[x["level"]], x["table"], x["id"]))
