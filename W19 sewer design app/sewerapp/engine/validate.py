"""User notifications (SewerGEMS's validation list), 2026-11-23 v3: what is wrong or doubtful in a model before or after a
run, each with its element so the editor can take the engineer to it. Errors stop a solve; warnings do not."""
import math
import numpy as np


INLET_NEEDS = {"grate": ("grate_type", "grate_length_m", "grate_width_m"), "curb": ("curb_length_m", "curb_height_m"),
               "combination": ("grate_type", "grate_length_m", "grate_width_m", "curb_length_m", "curb_height_m"), "slot": ("slot_length_m", "slot_width_m")}


def _drops(p, add):
    """A gravity pipe that arrives below the pipe leaving its structure: the water cannot leave (v7, the engineer: a pipe
    reconnected to a manhole "simply sent the flow to the next manhole")."""
    L, N = p.links, p.nodes
    g = L[L.kind.isin(["conduit", "channel", "lateral"])]
    if not len(g): return
    leave = g.groupby("from_node").up_inv.min()
    for lid, r in g.iterrows():
        n = r.to_node
        if n not in leave.index or N.kind.get(n) in ("wetwell", "storage", "outfall") or not (r.dn_inv == r.dn_inv): continue
        out = leave[n]; gap = out - float(r.dn_inv)
        if gap > 0.02:                                                  # levels are kept to the centimetre: 2 cm is a real drop (the Ibri design has none over 1.03 cm)
            add("error", "links", lid, f"arrives at {n} {gap:.2f} m below the pipe that leaves it (invert {float(r.dn_inv):.2f} against {out:.2f}): "
                                       "the water cannot leave. Design the network (or this pipe with the ones below it) to lower them, or raise this pipe")


def _kinds(p, add):
    """The element kinds' own checks (v7): what each needs before the runs can use it."""
    N, L = p.nodes, p.links; P = (getattr(p, "props", None) or {}); PN, PL = P.get("nodes", {}), P.get("links", {})
    gut = L[L.kind == "gutter"]
    for n, k in gut.from_node.value_counts().items():
        if k > 1: add("error", "nodes", n, f"{k} gutters leave it: an inlet's bypass takes one path")
    for lid, r in gut.iterrows():
        if N.kind.get(r.from_node) != "catch_basin" or N.kind.get(r.to_node) != "catch_basin":
            add("warning", "links", lid, "a gutter carries the bypassed flow from one catch basin to the next: both its ends should be catch basins")
    cbs = N.index[N.kind == "catch_basin"]
    for n in cbs:
        d = PN.get(n) or {}; t = d.get("inlet_type", "full_capture")
        if t == "percent_capture" and d.get("capture_pc") is None: add("warning", "nodes", n, "percent capture with no capture efficiency: taken as 100 %")
        if t == "max_capacity" and not d.get("q_max_ls"): add("warning", "nodes", n, "maximum capacity with no flow: it captures nothing")
        if t == "rating_curve" and len(d.get("rating") or []) < 2: add("error", "nodes", n, "an inflow-capture curve needs two rows or more")
        if t == "catalog":
            c = d.get("inlet_class")
            if not c: add("error", "nodes", n, "a catalogue inlet with no inlet type (grate, curb opening, combination or slot)"); continue
            miss = [k for k in INLET_NEEDS[c] if d.get(k) in (None, 0)]
            if miss: add("error", "nodes", n, f"the {c} inlet needs {', '.join(miss)}")
            g = d.get("gutter_shape", "conventional")
            need = ["road_cross_slope", "n_gutter"] + (["long_slope"] if d.get("location", "on_grade") == "on_grade" else [])
            if g == "v_shaped": need.append("curb_cross_slope")
            if g == "trapezoidal": need += ["ditch_bottom_m", "side_slope_l", "side_slope_r"]
            miss = [k for k in need if not d.get(k)]
            if miss: add("error", "nodes", n, f"the inlet's gutter needs {', '.join(miss)}")
            if c in ("grate", "combination") and d.get("grate_type") == "tilt_bar_45" and d.get("location") == "in_sag" and not d.get("opening_ratio"):
                add("warning", "nodes", n, "HEC-22 gives no opening ratio for the 45-degree tilt-bar grate: 0.17 is assumed (as SWMM 5.2 does); set its own")
    if len(cbs): add("warning", "nodes", cbs[0], f"{len(cbs)} catch basin{'s' if len(cbs) > 1 else ''}: the rational run computes the inlet capture and the gutter bypass (HEC-22); "
                                              "the storm run (SWMM) takes all the surface inflow into the pipes")
    for n in N.index[N.kind == "headwall"]:
        d = PN.get(n) or {}
        if d.get("boundary") == "fixed" and d.get("tailwater_m") is None: add("warning", "nodes", n, "a fixed boundary with no tailwater elevation: taken as free")
    ends = set(L.to_node) | set(L.from_node)
    for n in N.index[N.kind == "tap"]:
        host = (PN.get(n) or {}).get("link")
        if not host or host not in L.index: add("error", "nodes", n, "a tap with no conduit: set the conduit it taps (Properties > Tapped conduit)")
        elif L.kind[host] not in ("conduit", "channel"): add("warning", "nodes", n, f"it taps {host}, which is not a gravity conduit")
        if n not in ends: add("warning", "nodes", n, "no lateral ends on it")


def run(p, res=None):
    N, L = p.nodes, p.links; out = []
    add = lambda level, table, eid, msg: out.append(dict(level=level, table=table, id=str(eid), message=msg))
    ids = set(N.index)
    for lid, r in L.iterrows():
        for end in (r.from_node, r.to_node):
            if end not in ids: add("error", "links", lid, f"its node {end} does not exist")
    leave = L[~L.kind.isin(["orifice", "weir", "gutter"])].from_node.value_counts()
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
        if r.kind not in ("pressure_junction", "air_valve", "tap") and r.ground == r.ground and r.invert == r.invert and r.invert > r.ground: add("error", "nodes", n, f"invert {r.invert:.2f} above ground {r.ground:.2f}")
        if r.ground == 0 and r.invert in (-1.5, -3.0, -1.0, -2.0) and r.kind not in ("outfall", "headwall", "tap"): add("warning", "nodes", n, f"ground and invert still at the prototype's default (0 and {r.invert} m)")
    piped = L[L.kind != "gutter"]
    outs = set(N.index[N.kind == "outfall"]) | {n for n in N.index[N.kind == "headwall"] if n not in set(piped.from_node)}   # a headwall nothing leaves: its network's outfall
    for n, k in L.to_node[L.to_node.isin(outs)].value_counts().items():
        if k > 1: add("warning", "nodes", n, f"{k} links reach this outfall: SWMM takes one (join them at a manhole first)")
    if len(piped) and not outs: add("error", "nodes", "", "the network has no outfall")
    fr = set(piped.from_node)
    for n in set(piped.from_node) | set(piped.to_node):
        if n in ids and n not in fr and n not in outs and N.kind.get(n) not in ("storage", "tap"): add("warning", "nodes", n, "the flow ends here: it is not an outfall")
    _kinds(p, add)
    _drops(p, add)
    for lid, r in L.iterrows():
        if r.kind in ("conduit", "pressure_pipe", "channel", "lateral") and not (r.length_m > 0): add("error", "links", lid, "zero length")
        if r.kind == "channel" and lid not in (p.sections or {}): add("error", "links", lid, "a channel with no section: give it its open section (Properties > Section)")
        if r.kind == "lateral" and not (r.dn_mm > 0): add("error", "links", lid, "a lateral with no bore")
        if r.kind == "conduit" and not (r.dn_mm > 0) and lid not in (p.sections or {}): add("error", "links", lid, "no size or section")
        if r.kind == "conduit" and r.length_m and r.up_inv == r.up_inv and r.dn_inv == r.dn_inv and r.up_inv <= r.dn_inv:
            add("warning", "links", lid, f"flat or adverse ({(r.up_inv - r.dn_inv) / r.length_m * 100:.3f} %)")
        if r.kind == "pressure_pipe" and not (r.inside_mm == r.inside_mm and r.inside_mm > 0): add("error", "links", lid, "a pressure pipe with no bore")
        if r.kind == "pump":
            pu = (getattr(p, "pumps", None) or {}).get(lid)
            if not pu: add("warning", "links", lid, "no definition or capacity: the steady run passes its inflow, the storm run pumps ideally")
            elif pu.get("vspb"): add("warning", "links", lid, f"a variable-speed battery in SewerGEMS (target head {pu['vspb'].get('target_m', 0):.2f} m"
                                                          f"{' at ' + pu['vspb']['control'] if pu['vspb'].get('control') else ''}): run here at full speed, {pu.get('count', 1)} pump(s) together")
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
