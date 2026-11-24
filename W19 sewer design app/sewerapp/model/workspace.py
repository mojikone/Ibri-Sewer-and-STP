"""Open projects and their scenarios, the way SewerGEMS keeps a model in memory: a scenario is its parent's model plus a
list of edits (by element id), with undo and redo. Every edit re-solves at once (instant re-run).

Edit ops (dicts with "op"):
  set        {table: nodes|links|catchments, ids: [...], field, value}         one field on one or many elements (bulk)
  set_values {table, field, values: {id: value}, source?}                    one field, a value per element (imports); for nodes'
                             ground, `source` records where the levels came from (TRex), otherwise the record is cleared
  set_many   {table, field, values: {id: value}}                             as `set`, a value per element (a pasted column):
                                                                             node inverts carry link ends; one undo step
  set_loads  {set, values: {node: m3/d}}                                     unit loads of many nodes, one undo step
  add_node   {id?, kind, x, y, ground?, invert?}                               ground 0 and invert ground - 1.5 m by default
  add_link   {id?, kind, from_node, to_node, dn_mm?, length_m?, up_inv?, dn_inv?, coords?}
  add_catchment {id?, outlet, area_ha, imperv_pc, width_m, slope_pc, coords?}
  delete     {table, ids}                                                      deleting a node deletes its links
  move_node  {id, x, y}
  split_link {id, x, y, node_id?, kind?}                                       a new node on the link (the tool's kind), two links
  set_load   {set, node, value}                                                unit load, m3/d
  set_setting {path: "a.b.c", value}
  set_rain   {rain: {step_min, duration_min, series [[min, intensity]] or idf {durations_min, intensities}}}
  design     {load_set?, only?}   automated design of every conduit, or of `only` (the rest kept); locked ones kept; undoable
  lock       {ids, locked}  lock or unlock conduits for the design (settings design.locked)
  set_section {ids, section, dn_mm}  give conduits a box, open-rectangle or trapezoid section (engine/sections.py), or
                             None to make them circular again, at size dn_mm (the smallest catalogue size if not given)
  batch      {ops: [...]}    several edits as ONE undo step (a run drawn with the layout tool: its manholes and pipes)
  reconnect  {id, end: from|to, node, invert?}  move one end of a link to another node, keeping the link's id and
                             properties; the end's invert follows the new node (or takes `invert`), the length is re-measured
  add_run    {from_node, to_node | x, y, kind?, max_spacing?, dn_mm?, link_kind?}  the layout tool: a pipe to an existing
                             node or a new one, split by manholes at the engineer's spacing rule (engine/spacing.py)
  reverse    {ids}           turn links round (from and to, their end inverts and vertices swapped)
  set_coords {id, coords}    a pipe's drawn line: its bends (the ends snap to its structures; under three points: straight)
  set_infiltration {ids, rate}  a conduit's own infiltration rate (basis: settings.infiltration.method); None clears it
  set_storage {ids, area_m2 | curve [[depth, area]] | None}  a storage node's plan area for the storm run
  set_unit_rows {set, ids, rows [[unit load, count]]}  nodes' unit-load rows (library settings.libraries.unit_loads)
  set_outlet {ids, values}   an orifice's or a weir's geometry (Project.outlets)
  set_tailwater {ids, level | None}  a fixed water level at outfalls
  set_hydrology {ids, C, tc_min, cn}  catchments' rational C, time of concentration and SCS curve number
  set_controls {rules}       the storm run's control rules [{link, if node|time, node, op, value, then, else}]
  set_ppipe  {ids, method, C, e_mm, n, K, check | clear}  a pressure pipe's own friction and minor loss
  set_pump   {ids, q_ls, on_m, off_m, definition | None}  a pump's capacity and its start/stop depths at the inlet (storm run)
  set_prototype {kind, values}  what a new element of that kind gets (manhole/outfall/wetwell: ground, depth;
                             conduit: dn_mm, section; catchment: imperv_pc, width_m, slope_pc, n_imperv, n_perv)
New elements take their prototype for every value the edit does not give."""
import copy, itertools, math
import numpy as np, pandas as pd
from sewerapp.engine import steady
from sewerapp.model.general import Project, NODE_KINDS, LINK_KINDS, LINK_COLS, NODE_COLS, CATCH_COLS

DEFAULT_DEPTH = 1.5


def _ground_src(p, ids, source):
    """Where these structures' ground levels came from: `source` (TRex), or cleared by any other write or a move."""
    g = p.__dict__.setdefault("ground_src", {})
    for i in ids:
        if source: g[str(i)] = str(source)[:200]
        else: g.pop(str(i), None)


def _new_id(df, prefix):
    used = set(map(str, df.index))
    for k in itertools.count(len(df) + 1):
        if f"{prefix}{k}" not in used: return f"{prefix}{k}"


def _length(p, a, b, coords=None):
    if coords and len(coords) >= 2:
        return sum(math.dist(coords[i], coords[i + 1]) for i in range(len(coords) - 1))
    return math.dist((p.nodes.x[a], p.nodes.y[a]), (p.nodes.x[b], p.nodes.y[b]))


CATEGORIES = [("physical", "Physical"), ("loading", "Sanitary loading"), ("infiltration", "Infiltration"), ("hydrology", "Hydrology and rain"),
              ("boundary", "Boundary conditions"), ("operational", "Operational"), ("options", "Calculation options")]
CAT_ORDER = [c for c, _ in CATEGORIES]
_OP_CAT = dict(set_load="loading", set_loads="loading", set_unit_rows="loading", set_infiltration="infiltration", set_hydrology="hydrology",
               set_rain="hydrology", set_tailwater="boundary", set_pump="operational", set_controls="operational", set_setting="options")


def category(e):
    """The alternative category of an edit (a batch: its first edit's; batches are split by category before routing)."""
    op = e.get("op")
    if op == "batch": return category(e["ops"][0]) if e.get("ops") else "physical"
    if op in ("set", "set_many", "set_values") and e.get("field") == "inflow_m3d": return "loading"
    return _OP_CAT.get(op, "physical")


def split_by_category(e):
    """An edit as (category, edit) parts: a batch of mixed categories becomes one batch per category."""
    if e.get("op") != "batch": return [(category(e), e)]
    parts = {}
    for x in e.get("ops") or []: parts.setdefault(category(x), []).append(x)
    return [(c, ops[0] if len(ops) == 1 else dict(op="batch", ops=ops)) for c, ops in sorted(parts.items(), key=lambda kv: CAT_ORDER.index(kv[0]))]


def apply(p, e):
    """Apply one edit to project p in place; returns True when the structure (elements, geometry) changed."""
    op = e["op"]
    if op == "_alt":                                     # the parts of an edit that went into alternatives live there;
        return apply(p, e["own"]) if e.get("own") else False     # the scenario's own part (if any) is here
    if op == "set":
        t = getattr(p, e["table"]); ids = [str(i) for i in e["ids"]]
        missing = [i for i in ids if i not in t.index]
        if missing: raise ValueError(f"no {e['table'][:-1]} {missing[:3]}")
        if e["field"] not in t.columns: raise ValueError(f"{e['table']} has no field {e['field']}")
        v = e["value"]
        if e["table"] == "links" and e["field"] == "dn_mm":
            ins = p.inside_of(v)                       # a size not in the catalogue (an imported model) is its own bore
            t.loc[ids, "dn_mm"] = int(v); t.loc[ids, "inside_mm"] = ins if ins == ins else float(v)
        elif e["table"] == "nodes" and e["field"] == "invert":
            # link ends that sat at a node's old invert follow it (a deliberately offset end keeps its level)
            for nid in ids:
                old = t.invert[nid]
                for col, end in (("up_inv", "from_node"), ("dn_inv", "to_node")):
                    m = (p.links[end] == nid) & ((p.links[col] - old).abs() < 1e-9)
                    p.links.loc[m, col] = float(v)
            t.loc[ids, "invert"] = float(v)
        else:
            if e["field"] in ("kind",):
                allowed = NODE_KINDS if e["table"] == "nodes" else LINK_KINDS
                if v not in allowed: raise ValueError(f"kind must be one of {allowed}")
            t.loc[ids, e["field"]] = v
        if e["table"] == "nodes" and e["field"] == "ground": _ground_src(p, ids, e.get("source"))
        if e["table"] == "nodes" and e["field"] in ("x", "y"): _ground_src(p, ids, None); _relength(p, ids); return True
        return False
    if op == "set_many":
        structural = False
        for i, v in e["values"].items():
            structural = apply(p, dict(op="set", table=e["table"], ids=[str(i)], field=e["field"], value=v)) or structural
        return structural
    if op == "set_loads":
        missing = [n for n in e["values"] if str(n) not in p.nodes.index]
        if missing: raise ValueError(f"no node {missing[:3]}")
        ls = p.load_sets.setdefault(str(e["set"]), {})
        for n, v in e["values"].items(): ls[str(n)] = float(v)
        return False
    if op == "set_values":
        t = getattr(p, e["table"]); v = pd.Series(e["values"], dtype=float if e["field"] != "kind" else object)
        missing = v.index.difference(t.index)
        if len(missing): raise ValueError(f"no {e['table'][:-1]} {list(missing[:3])}")
        if e["field"] not in t.columns: raise ValueError(f"{e['table']} has no field {e['field']}")
        t.loc[v.index, e["field"]] = v.values
        if e["table"] == "nodes" and e["field"] == "ground": _ground_src(p, list(v.index), e.get("source"))
        if e["table"] == "links" and e["field"] == "dn_mm":
            ins = [p.inside_of(x) for x in v.values]
            t.loc[v.index, "inside_mm"] = [a if a == a else float(x) for a, x in zip(ins, v.values)]
        return False
    if op == "add_node":
        nid = str(e.get("id") or _new_id(p.nodes, {"outfall": "O-", "wetwell": "WW-"}.get(e.get("kind", "manhole"), "MH-")))
        if nid in p.nodes.index: raise ValueError(f"node {nid} exists")
        kind = e.get("kind", "manhole")
        if kind not in NODE_KINDS: raise ValueError(f"kind must be one of {NODE_KINDS}")
        pr = p.prototype(kind); g = float(e["ground"] if e.get("ground") is not None else pr.get("ground", 0.0))
        inv = e.get("invert"); inv = float(inv) if inv is not None else g - float(pr.get("depth", DEFAULT_DEPTH))
        p.nodes.loc[nid] = dict(kind=kind, x=float(e["x"]), y=float(e["y"]), ground=g,
                                invert=inv, inflow_m3d=float(e.get("inflow_m3d", 0.0)))
        return True
    if op == "add_link":
        a, b = str(e["from_node"]), str(e["to_node"])
        for n in (a, b):
            if n not in p.nodes.index: raise ValueError(f"no node {n}")
        if a == b: raise ValueError("a link needs two different nodes")
        lid = str(e.get("id") or _new_id(p.links, "P-" if e.get("kind", "conduit") == "conduit" else "PMP-"))
        if lid in p.links.index: raise ValueError(f"link {lid} exists")
        pr = p.prototype("conduit") if e.get("kind", "conduit") == "conduit" else {}
        dn = int(e.get("dn_mm") or pr.get("dn_mm") or p.catalogue().nominal_mm.iloc[0])
        coords = e.get("coords")
        p.links.loc[lid] = dict(kind=e.get("kind", "conduit"), from_node=a, to_node=b,
                                length_m=float(e.get("length_m") or _length(p, a, b, coords)), dn_mm=dn,
                                inside_mm=p.inside_of(dn), up_inv=float(e.get("up_inv", p.nodes.invert[a])),
                                dn_inv=float(e.get("dn_inv", p.nodes.invert[b])), transfer=bool(e.get("transfer", False)),
                                coords=coords)
        if coords: p.orient_lines({lid})                    # a line drawn from the downstream end runs with the flow
        sec = e.get("section", pr.get("section"))
        if sec: apply(p, dict(op="set_section", ids=[lid], section=dict(sec)))
        return True
    if op == "add_catchment":
        cid = str(e.get("id") or _new_id(p.catchments, "CM-"))
        if e["outlet"] not in p.nodes.index: raise ValueError(f"no node {e['outlet']}")
        pr = p.prototype("catchment"); g = lambda k: float(e[k] if e.get(k) is not None else pr[k])
        p.catchments.loc[cid] = dict(outlet=e["outlet"], area_ha=float(e["area_ha"]), imperv_pc=g("imperv_pc"),
                                     width_m=g("width_m"), slope_pc=g("slope_pc"), n_imperv=g("n_imperv"), n_perv=g("n_perv"),
                                     gauge=e.get("gauge", "RG1"), coords=e.get("coords"))
        return True
    if op == "delete":
        ids = [str(i) for i in e["ids"]]
        if e["table"] == "nodes":
            p.links = p.links[~(p.links.from_node.isin(ids) | p.links.to_node.isin(ids))]
            p.catchments = p.catchments[~p.catchments.outlet.isin(ids)]
            for s in p.load_sets.values():
                for i in ids: s.pop(i, None)
        t = getattr(p, e["table"]); setattr(p, e["table"], t.drop(index=[i for i in ids if i in t.index]))
        live_l, live_n = set(p.links.index), set(p.nodes.index)
        for dct in (p.pumps, p.ppipes, p.outlets, p.infil, p.sections):
            for k in [k for k in dct if k not in live_l]: dct.pop(k)
        for dct in (p.storage, p.tailwater, p.ground_src):
            for k in [k for k in dct if k not in live_n]: dct.pop(k)
        for S in p.unit_rows.values():
            for k in [k for k in S if k not in live_n]: S.pop(k)
        p.controls = [r for r in (p.controls or []) if r.get("link") in live_l and (r.get("if") != "node" or r.get("node") in live_n)]
        return True
    if op == "move_node":
        p.nodes.loc[str(e["id"]), ["x", "y"]] = [float(e["x"]), float(e["y"])]; _ground_src(p, [str(e["id"])], None); _relength(p, [str(e["id"])]); return True
    if op == "split_link":
        lid = str(e["id"]); L = p.links.loc[lid].copy()
        pres = L.kind == "pressure_pipe"
        # node_id names the new node (the editor sends it); without it the node takes the link's id, as edits saved before
        # 2026-11-23 did, so they replay to the same ids
        nid = str(e.get("node_id") or e.get("id") or _new_id(p.nodes, "J-" if pres else "MH-")); x, y = float(e["x"]), float(e["y"])
        if nid in p.nodes.index: raise ValueError(f"node {nid} exists")
        kind = e.get("kind") or ("pressure_junction" if pres else "manhole")         # morph: the tool's kind
        if kind not in NODE_KINDS: raise ValueError(f"kind must be one of {NODE_KINDS}")
        c0 = L.coords if isinstance(L.coords, list) and len(L.coords) >= 3 else None
        if c0:                                                           # a line with bends: split where clicked, each half keeps its bends
            k, (x, y), s = _along(c0, x, y); f = s / max(_length(p, None, None, c0), 1e-9)
            halves = ([list(v)[:2] for v in c0[:k + 1]] + [[x, y]], [[x, y]] + [list(v)[:2] for v in c0[k + 1:]])
        else:
            halves = (None, None)
            f = _length(p, L.from_node, L.to_node) and math.dist((p.nodes.x[L.from_node], p.nodes.y[L.from_node]), (x, y)) / max(_length(p, L.from_node, L.to_node), 1e-9)
        inv = L.up_inv + (L.dn_inv - L.up_inv) * f; g = p.nodes.ground[L.from_node] + (p.nodes.ground[L.to_node] - p.nodes.ground[L.from_node]) * f
        p.nodes.loc[nid] = dict(kind=kind, x=x, y=y, ground=g, invert=inv, inflow_m3d=0.0)
        p.links = p.links.drop(index=lid)
        for dct in (p.ppipes, p.infil, p.sections):                      # the halves keep the pipe's own values
            if lid in dct:
                v = dct.pop(lid)
                for half in ("a", "b"): dct[f"{lid}-{half}"] = copy.deepcopy(v)
        for k, (a, b, ui, di) in enumerate(((L.from_node, nid, L.up_inv, inv), (nid, L.to_node, inv, L.dn_inv))):
            p.links.loc[f"{lid}-{'ab'[k]}"] = dict(kind=L.kind, from_node=a, to_node=b, length_m=_length(p, a, b, halves[k]), dn_mm=L.dn_mm,
                                                   inside_mm=L.inside_mm, up_inv=ui, dn_inv=di, transfer=L.transfer, coords=halves[k])
        return True
    if op == "set_load":
        if e["node"] not in p.nodes.index: raise ValueError(f"no node {e['node']}")
        p.load_sets.setdefault(str(e["set"]), {})[str(e["node"])] = float(e["value"]); return False
    if op == "set_setting":
        from sewerapp.model.general import DEFAULT_SETTINGS
        keys = e["path"].split("."); p.setting(keys[0]); d = p.settings; dd = DEFAULT_SETTINGS
        for k in keys[:-1]:
            dd = dd.get(k, {}) if isinstance(dd, dict) else {}
            if k not in d and k in dd: d[k] = copy.deepcopy(dd[k])           # a sub-setting added since the project was made
            d = d[k]
        if keys[-1] not in d and not (isinstance(dd, dict) and keys[-1] in dd): raise ValueError(f"no setting {e['path']}")
        if e["path"] == "libraries.pumps":
            from sewerapp.engine import pressure
            names = set()
            for x in e["value"] or []:
                if x.get("name") in names: raise ValueError(f"two pump definitions are called {x.get('name')}")
                names.add(x.get("name")); pressure.curve(x)                     # raises on an incomplete curve
            used = sorted({v["definition"] for v in p.pumps.values() if v.get("definition")} - names)
            if used: raise ValueError(f"pump definition {used[0]} is used by a pump: give that pump another definition first")
        if e["path"] == "pressure" and isinstance(e["value"], dict):
            for k in ("C", "n"):
                if k in e["value"] and not (isinstance(e["value"][k], (int, float)) and e["value"][k] > 0): raise ValueError(f"{k} must be above 0")
        d[keys[-1]] = e["value"]; return False
    if op == "set_rain":
        p.rain = dict(e["rain"]); return False
    if op == "design":
        from sewerapp.engine import design_general
        q, rep = design_general.design(p, e.get("load_set"), e.get("only"))
        p.links, p.nodes = q.links, q.nodes; e["report"] = rep
        return True
    if op == "set_section":
        from sewerapp.engine.sections import SHAPES
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.links.index]
        if missing: raise ValueError(f"no link {missing[:3]}")
        s = e.get("section")
        if s is not None:
            if s.get("shape") not in SHAPES: raise ValueError(f"shape must be one of {SHAPES}")
            keys = ["rise_m", "span_m", "n"] + (["bottom_m", "z_left", "z_right"] if s["shape"] == "trapezoid" else [])
            if s["shape"] == "trapezoid": keys.remove("span_m")
            bad = [k for k in keys if not (isinstance(s.get(k), (int, float)) and s[k] >= 0) or (k in ("rise_m", "n") and not s[k] > 0)]
            if "barrels" in s and not (isinstance(s["barrels"], (int, float)) and s["barrels"] >= 1 and float(s["barrels"]).is_integer()): bad.append("barrels (a whole number)")
            if bad: raise ValueError(f"a {s['shape']} needs positive {', '.join(bad)}")
            for i in ids:
                p.sections[i] = {k: (int(v) if k == "barrels" else float(v) if isinstance(v, (int, float)) else v) for k, v in s.items()
                                 if not (k == "barrels" and v == 1)}
                p.links.loc[i, ["dn_mm", "inside_mm"]] = [0, np.nan]
        else:
            dn = int(e.get("dn_mm") or p.catalogue().nominal_mm.iloc[0]); ins = p.inside_of(dn)
            for i in ids:
                if p.sections.pop(i, None) is not None or not p.links.loc[i, "dn_mm"] > 0:
                    p.links.loc[i, ["dn_mm", "inside_mm"]] = [dn, ins if ins == ins else float(dn)]
        return False
    if op == "lock":
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.links.index]
        if missing: raise ValueError(f"no link {missing[:3]}")
        cur = set(p.settings["design"].get("locked", []))
        p.settings["design"]["locked"] = sorted(cur | set(ids)) if e.get("locked", True) else sorted(cur - set(ids))
        return False
    if op == "batch":
        structural = False
        for x in e["ops"]:
            if x.get("op") == "batch": raise ValueError("a batch cannot hold a batch")
            structural = apply(p, x) or structural
        return structural
    if op == "add_run":
        # the layout tool's click: a pipe from `from_node` to `to_node` (or to a new node of `kind` at x, y); with
        # `max_spacing` (metres, or "table12" for G203 Table 12 at the pipe's size) manholes go in between at the
        # engineer's rounded spacing (engine/spacing.py). The ids it made are written into the edit, so a replay
        # (undo, redo, reopening) makes the same ones.
        from sewerapp.engine import spacing
        a = str(e["from_node"])
        if a not in p.nodes.index: raise ValueError(f"no node {a}")
        kind = e.get("link_kind", "conduit")
        if e.get("to_node"):
            b = str(e["to_node"])
            if b not in p.nodes.index: raise ValueError(f"no node {b}")
        else:
            b = e.get("end_id") or _new_id(p.nodes, {"outfall": "O-", "wetwell": "WW-"}.get(e.get("kind", "manhole"), "MH-"))
            apply(p, dict(op="add_node", id=b, kind=e.get("kind", "manhole"), x=e["x"], y=e["y"], ground=e.get("ground")))
            e["end_id"] = b
        if a == b: raise ValueError("a link needs two different nodes")
        if kind == "conduit" and (p.links.from_node == a).any():
            # drawn from a manhole that already drains: the new branch drains INTO it (a sewer network is a tree)
            if (p.links.from_node == b).any(): raise ValueError(f"{a} and {b} both already have a leaving pipe (a sewer network is a tree)")
            e["drains_into_start"] = True
        rev = bool(e.get("drains_into_start"))
        dn = int(e.get("dn_mm") or p.prototype("conduit").get("dn_mm") or p.catalogue().nominal_mm.iloc[0])
        xa, ya, xb, yb = p.nodes.x[a], p.nodes.y[a], p.nodes.x[b], p.nodes.y[b]
        path = [(float(xa), float(ya))] + [tuple(map(float, v[:2])) for v in (e.get("via") or [])] + [(float(xb), float(yb))]   # bends on the way
        L = sum(math.dist(path[k], path[k + 1]) for k in range(len(path) - 1))
        mx = e.get("max_spacing")
        if mx == "table12": mx = spacing.table12(dn)
        lens = spacing.split_lengths(L, float(mx)) if (mx and kind == "conduit" and L > float(mx) + 1e-6) else [L]
        mids = e.get("mid_ids") or []; chain = [a]; s = 0.0; depth = p.prototype("manhole").get("depth", DEFAULT_DEPTH)
        ga, gb = float(p.nodes.ground[a]), float(p.nodes.ground[b])
        cuts = [0.0]
        for k, piece in enumerate(lens[:-1]):
            s += piece; f = s / L
            nid = mids[k] if k < len(mids) else _new_id(p.nodes, "MH-")
            g = ga + (gb - ga) * f; (mxx, myy), _ = _path_at(path, s)
            apply(p, dict(op="add_node", id=nid, kind="manhole", x=mxx, y=myy, ground=g, invert=g - float(depth)))
            chain.append(nid); cuts.append(s)
        chain.append(b); e["mid_ids"] = chain[1:-1]; cuts.append(L)
        bent = len(path) > 2

        def piece_line(s0, s1):                                         # the part of the bent path between two distances
            (x0, y0), k0 = _path_at(path, s0); (x1, y1), k1 = _path_at(path, s1)
            return [[x0, y0]] + [list(path[j]) for j in range(k0 + 1, k1 + 1)] + [[x1, y1]]
        lines = [piece_line(cuts[k], cuts[k + 1]) if bent else None for k in range(len(chain) - 1)]
        if rev: chain = chain[::-1]; lines = [ln[::-1] if ln else None for ln in lines[::-1]]
        lids = e.get("link_ids") or []; made = []
        for k, (u, v) in enumerate(zip(chain[:-1], chain[1:])):
            lid = lids[k] if k < len(lids) else _new_id(p.links, "P-" if kind == "conduit" else "PMP-")
            extra = {"coords": lines[k]} if lines[k] and len(lines[k]) > 2 else {}
            apply(p, dict(op="add_link", id=lid, kind=kind, from_node=u, to_node=v, dn_mm=dn, **extra)); made.append(lid)
        e["link_ids"] = made
        return True
    if op == "reconnect":
        lid, end, nid = str(e["id"]), e.get("end"), str(e["node"])
        if lid not in p.links.index: raise ValueError(f"no link {lid}")
        if nid not in p.nodes.index: raise ValueError(f"no node {nid}")
        if end not in ("from", "to"): raise ValueError("end must be 'from' or 'to'")
        r = p.links.loc[lid]; other = r.to_node if end == "from" else r.from_node
        if nid == other: raise ValueError("a link needs two different nodes")
        if end == "from" and ((p.links.from_node == nid) & (p.links.index != lid)).any():
            raise ValueError(f"node {nid} already has a leaving link (a sewer network is a tree)")
        col, inv = ("from_node", "up_inv") if end == "from" else ("to_node", "dn_inv")
        p.links.at[lid, col] = nid
        p.links.at[lid, inv] = float(e["invert"]) if e.get("invert") is not None else float(p.nodes.invert[nid])
        c = p.links.at[lid, "coords"]
        if isinstance(c, list) and len(c) >= 2:                      # a drawn polyline keeps its bends, its end moves
            c = [list(v) for v in c]; c[0 if end == "from" else -1] = [float(p.nodes.x[nid]), float(p.nodes.y[nid])]
            p.links.at[lid, "coords"] = c
        p.links.at[lid, "length_m"] = _length(p, p.links.at[lid, "from_node"], p.links.at[lid, "to_node"], p.links.at[lid, "coords"])
        return True
    if op == "set_coords":
        # a pipe's drawn line (its bends): the ends are its structures, the length follows the line; fewer than three
        # points make it straight again
        lid = str(e["id"])
        if lid not in p.links.index: raise ValueError(f"no link {lid}")
        r = p.links.loc[lid]; c = [list(map(float, v[:2])) for v in (e.get("coords") or [])]
        if len(c) > 5000: raise ValueError("at most 5000 points on one pipe")
        a, b = [float(p.nodes.x[r.from_node]), float(p.nodes.y[r.from_node])], [float(p.nodes.x[r.to_node]), float(p.nodes.y[r.to_node])]
        c = [a] + c[1:-1] + [b] if len(c) >= 3 else None
        p.links.at[lid, "coords"] = c; p.links.at[lid, "length_m"] = _length(p, r.from_node, r.to_node, c)
        return True
    if op == "reverse":
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.links.index]
        if missing: raise ValueError(f"no link {missing[:3]}")
        for lid in ids:
            r = p.links.loc[lid]
            p.links.loc[lid, ["from_node", "to_node", "up_inv", "dn_inv"]] = [r.to_node, r.from_node, r.dn_inv, r.up_inv]
            if isinstance(r.coords, list) and len(r.coords) >= 2: p.links.at[lid, "coords"] = [list(c) for c in r.coords[::-1]]
        return True
    if op == "set_infiltration":
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.links.index]
        if missing: raise ValueError(f"no link {missing[:3]}")
        v = e.get("rate")
        if v is not None and not (isinstance(v, (int, float)) and v >= 0): raise ValueError("an infiltration rate is a number, 0 or more")
        for i in ids:
            if v is None: p.infil.pop(i, None)
            else: p.infil[i] = float(v)
        return False
    if op == "set_storage":
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.nodes.index]
        if missing: raise ValueError(f"no node {missing[:3]}")
        if e.get("area_m2") is None and e.get("curve") is None:
            for i in ids: p.storage.pop(i, None)
            return False
        if e.get("curve") is not None:
            c = sorted([float(a), float(b)] for a, b in e["curve"])
            if len(c) < 2 or any(a < 0 or b < 0 for a, b in c): raise ValueError("a depth-area table needs two or more rows of depth and area, 0 or more")
            v = dict(curve=c)
        else:
            a = float(e["area_m2"])
            if not a > 0: raise ValueError("a storage area is a positive number of m2")
            v = dict(area_m2=a)
        for i in ids: p.storage[i] = dict(v)
        return False
    if op == "set_pump":
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.links.index or p.links.kind[i] != "pump"]
        if missing: raise ValueError(f"not a pump: {missing[:3]}")
        d = e.get("definition")
        if e.get("q_ls") is None and not d:
            for i in ids: p.pumps.pop(i, None)
            return False
        if d and d not in {x["name"] for x in ((p.settings.get("libraries") or {}).get("pumps") or [])}: raise ValueError(f"no pump definition {d}")
        q, on, off = (float(e["q_ls"]) if e.get("q_ls") is not None else None), float(e.get("on_m") or 0), float(e.get("off_m") or 0)
        if q is not None and not q > 0: raise ValueError("a pump's capacity is a positive flow")
        if e.get("on_m") is not None and e.get("off_m") is not None and off >= on: raise ValueError("a pump stops at a lower depth than it starts")
        cnt = int(e.get("count") or 1)
        if cnt < 1: raise ValueError("the number of pumps running is 1 or more")
        for i in ids: p.pumps[i] = {k: v for k, v in dict(q_ls=q, on_m=on, off_m=off, definition=d, count=cnt if cnt > 1 else None).items() if v is not None}
        return False
    if op == "set_unit_rows":                                            # a node's unit-load rows in a load set
        units = {u["name"] for u in ((p.settings.get("libraries") or {}).get("unit_loads") or [])}
        rows = [[str(a), float(b)] for a, b in (e.get("rows") or [])]
        bad = [a for a, _ in rows if a not in units]
        if bad: raise ValueError(f"no unit load {bad[:3]} in the library")
        if any(b < 0 for _, b in rows): raise ValueError("a count is 0 or more")
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.nodes.index]
        if missing: raise ValueError(f"no node {missing[:3]}")
        S = p.unit_rows.setdefault(str(e["set"]), {})
        for i in ids:
            if rows: S[i] = [list(r) for r in rows]
            else: S.pop(i, None)
        return False
    if op == "set_outlet":                                               # an orifice's or a weir's geometry
        ids = [str(i) for i in e["ids"]]; bad = [i for i in ids if i not in p.links.index or p.links.kind[i] not in ("orifice", "weir")]
        if bad: raise ValueError(f"not an orifice or a weir: {bad[:3]}")
        v = {k: x for k, x in (e.get("values") or {}).items() if x is not None}
        for k, x in v.items():
            if k not in ("shape", "type", "gated") and not (isinstance(x, (int, float)) and x >= 0): raise ValueError(f"{k} is a number, 0 or more")
        for i in ids: p.outlets[i] = dict(v)
        return False
    if op == "set_inverts":                                              # many structures' inverts at once; pipe ends that sat on them follow
        v = pd.Series({str(k): float(x) for k, x in e["values"].items()}, dtype=float)
        missing = v.index.difference(p.nodes.index)
        if len(missing): raise ValueError(f"no node {list(missing[:3])}")
        old = p.nodes.invert.reindex(v.index)
        for col, end in (("up_inv", "from_node"), ("dn_inv", "to_node")):
            o = p.links[end].map(old); nw = p.links[end].map(v)
            m = nw.notna() & ((p.links[col] - o).abs() < 1e-9)
            p.links.loc[m, col] = nw[m]
        p.nodes.loc[v.index, "invert"] = v.values
        return False
    if op == "set_hydrology":                                            # a catchment's C, Tc and curve number
        ids = [str(i) for i in e["ids"]]; bad = [i for i in ids if i not in p.catchments.index]
        if bad: raise ValueError(f"no catchment {bad[:3]}")
        v = {k: e[k] for k in ("C", "tc_min", "cn") if k in e}
        if v.get("C") is not None and not (0 < float(v["C"]) <= 1): raise ValueError("a runoff coefficient C is above 0 and at most 1")
        if v.get("tc_min") is not None and not float(v["tc_min"]) > 0: raise ValueError("a time of concentration is above 0 minutes")
        if v.get("cn") is not None and not (0 < float(v["cn"]) <= 100): raise ValueError("a curve number is above 0 and at most 100")
        for i in ids:
            o = p.hydrology.setdefault(i, {})
            for k, x in v.items():
                if x is None: o.pop(k, None)
                else: o[k] = float(x)
        return False
    if op == "set_controls":                                             # the storm run's control rules
        rules = list(e.get("rules") or [])
        for k, r in enumerate(rules):
            if r.get("link") not in p.links.index or p.links.kind[r["link"]] not in ("pump", "orifice", "weir"): raise ValueError(f"rule {k + 1}: {r.get('link')} is not a pump, orifice or weir")
            if r.get("if") == "node" and r.get("node") not in p.nodes.index: raise ValueError(f"rule {k + 1}: no node {r.get('node')}")
            if r.get("if") not in ("node", "time"): raise ValueError(f"rule {k + 1}: the condition is on a node's depth or the time")
            if r.get("op") not in (">", "<", ">=", "<="): raise ValueError(f"rule {k + 1}: the comparison is >, <, >= or <=")
            float(r["value"])
            for side in ("then", "else"):
                a = r.get(side)
                if a in (None, "") and side == "else": continue
                if p.links.kind[r["link"]] == "pump":
                    if str(a).upper() not in ("ON", "OFF"): raise ValueError(f"rule {k + 1}: a pump is switched ON or OFF")
                    r[side] = str(a).upper()
                else:
                    try: x = float(a)
                    except (TypeError, ValueError): raise ValueError(f"rule {k + 1}: an orifice or weir is set to a number from 0 to 1")
                    if not 0 <= x <= 1: raise ValueError(f"rule {k + 1}: an orifice or weir is set to a number from 0 to 1")
        p.controls = rules
        return False
    if op == "set_tailwater":
        ids = [str(i) for i in e["ids"]]; bad = [i for i in ids if i not in p.nodes.index or p.nodes.kind[i] != "outfall"]
        if bad: raise ValueError(f"not an outfall: {bad[:3]}")
        for i in ids:
            if e.get("level") is None: p.tailwater.pop(i, None)
            else: p.tailwater[i] = float(e["level"])
        return False
    if op == "set_ppipe":
        ids = [str(i) for i in e["ids"]]; missing = [i for i in ids if i not in p.links.index or p.links.kind[i] != "pressure_pipe"]
        if missing: raise ValueError(f"not a pressure pipe: {missing[:3]}")
        vals = {k: e[k] for k in ("method", "C", "e_mm", "n", "K", "check") if k in e and e[k] is not None}
        if vals.get("method") not in (None, "hazen", "darcy", "manning"): raise ValueError("friction method: hazen, darcy or manning")
        for k in ("C", "e_mm", "n", "K"):
            if k in vals and not (isinstance(vals[k], (int, float)) and vals[k] >= 0): raise ValueError(f"{k} is a number, 0 or more")
        for k in ("C", "n"):
            if k in vals and not vals[k] > 0: raise ValueError(f"{'Hazen-Williams C' if k == 'C' else 'Manning n'} must be above 0")
        for i in ids:
            if e.get("clear"): p.ppipes.pop(i, None); continue
            o = p.ppipes.setdefault(i, {}); o.update(vals)
            for k in ("method", "C", "e_mm", "n", "K"):                  # a value sent as None goes back to the project's
                if k in e and e[k] is None: o.pop(k, None)
            if not o: p.ppipes.pop(i, None)
        return False
    if op == "set_prototype":
        from sewerapp.model.general import DEFAULT_SETTINGS
        kind = e.get("kind"); allowed = DEFAULT_SETTINGS["prototypes"]
        if kind not in allowed: raise ValueError(f"no prototype for {kind}; one of {list(allowed)}")
        vals = dict(e.get("values") or {}); bad = [k for k in vals if k not in allowed[kind]]
        if bad: raise ValueError(f"a {kind} prototype has no {bad}")
        if kind == "conduit" and vals.get("section") and vals["section"].get("shape") is None: raise ValueError("a section needs a shape")
        p.setting("prototypes").setdefault(kind, {}).update(vals)
        return False
    raise ValueError(f"unknown edit op {op}")


def _relength(p, node_ids):
    """After structures move: a drawn line's end follows its structure (its bends stay) and the length follows the line."""
    m = p.links.from_node.isin(node_ids) | p.links.to_node.isin(node_ids)
    for lid in p.links.index[m]:
        r = p.links.loc[lid]
        if isinstance(r.coords, list) and len(r.coords) >= 2:
            c = [list(v)[:2] for v in r.coords]
            if r.from_node in node_ids: c[0] = [float(p.nodes.x[r.from_node]), float(p.nodes.y[r.from_node])]
            if r.to_node in node_ids: c[-1] = [float(p.nodes.x[r.to_node]), float(p.nodes.y[r.to_node])]
            p.links.at[lid, "coords"] = c; p.links.at[lid, "length_m"] = _length(p, r.from_node, r.to_node, c)
        else:
            p.links.at[lid, "length_m"] = _length(p, r.from_node, r.to_node)


def _along(c, x, y):
    """Where (x, y) falls on polyline c: (segment index, the point on it, distance along the line from its start)."""
    best = (float("inf"), 0, (c[0][0], c[0][1]), 0.0); run = 0.0
    for k in range(len(c) - 1):
        (ax, ay), (bx, by) = c[k][:2], c[k + 1][:2]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = 0.0 if not L2 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py = ax + t * dx, ay + t * dy; d = math.hypot(x - px, y - py)
        if d < best[0]: best = (d, k, (px, py), run + t * math.sqrt(L2))
        run += math.sqrt(L2)
    return best[1], best[2], best[3]


def _path_at(pts, s):
    """The point at distance s along polyline pts, and the index of the segment it lies on."""
    for k in range(len(pts) - 1):
        L = math.dist(pts[k], pts[k + 1])
        if s <= L or k == len(pts) - 2:
            f = 0.0 if not L else min(1.0, s / L)
            return (pts[k][0] + (pts[k + 1][0] - pts[k][0]) * f, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * f), k
        s -= L


class Scenario:
    def __init__(self, sid, name, parent=None, edits=None):
        self.id, self.name, self.parent = sid, name, parent
        self.edits = list(edits or []); self.redo = []
        self.fixed = 0                          # leading edits that define the scenario (an opened model's): not undoable
        self.alts = {}                          # {category: alternative id}: the alternatives this scenario takes

    def to_dict(self):
        return dict(id=self.id, name=self.name, parent=self.parent, edits=len(self.edits), can_undo=len(self.edits) > self.fixed,
                    can_redo=bool(self.redo), alts=dict(getattr(self, "alts", {}) or {}))


class Session:
    """One open project: the base model, its scenarios, and a cache of solved states."""

    def __init__(self, pid, project):
        self.id, self.base = pid, project
        self.scenarios = {"base": Scenario("base", "Base")}; self._cache = {}; self._n = 0
        self.external = {}                      # scenario id -> results another program computed (SewerGEMS), by link id
        self.refs = []                          # reference layers shown under the network: [{id, name, geojson, ...}]
        self.alternatives = {}                  # {category: {alternative id: {name, parent, edits}}}
        self._seq = 0                           # the session's edit clock: every new edit gets the next number
        self._alt_n = 0                         # alternative ids A1, A2 ... never reused

    def _tick(self):
        self._seq = int(getattr(self, "_seq", 0)) + 1; return self._seq

    def _rescan(self):
        """The clocks after a reload: past the largest number in use."""
        seqs = [e.get("_seq", 0) for c in self.scenarios.values() for e in c.edits + c.redo] + \
               [e.get("_seq", 0) for A in self.alternatives.values() for a in A.values() for e in a["edits"]]
        self._seq = max([int(x or 0) for x in seqs] + [int(getattr(self, "_seq", 0) or 0)])
        ns = [int(k[1:]) for A in self.alternatives.values() for k in A if k[:1] == "A" and k[1:].isdigit()]
        self._alt_n = max(ns + [int(getattr(self, "_alt_n", 0) or 0)])

    def new_alternative(self, cat, name, parent=None, edits=None):
        self._alt_n = int(getattr(self, "_alt_n", 0)) + 1
        while f"A{self._alt_n}" in self.alternatives.get(cat, {}): self._alt_n += 1
        aid = f"A{self._alt_n}"
        self.alternatives.setdefault(cat, {})[aid] = dict(name=name, parent=parent, edits=list(edits or [])); self._cache = {}
        return aid

    def fork_alts(self, sid):
        """Give a scenario a private child of every alternative it takes, so its edits change no other scenario."""
        sc = self.scenarios[sid]; sc.alts = dict(getattr(sc, "alts", {}) or {})
        for cat, aid in self.alts_of(sid).items():
            sc.alts[cat] = self.new_alternative(cat, f"{self.alternatives[cat][aid]['name']} ({sc.name})", parent=aid)
        self._cache = {}

    # ---- alternatives (F14)
    def alts_of(self, sid):
        """The alternatives a scenario takes: its own choices over its parents' (a child inherits them)."""
        chain, s = [], self.scenarios[sid]
        while s: chain.append(s); s = self.scenarios.get(s.parent) if s.parent else None
        out = {}
        for c in reversed(chain): out.update(getattr(c, "alts", {}) or {})
        return {k: v for k, v in out.items() if v and v in (getattr(self, "alternatives", {}) or {}).get(k, {})}

    def alt_chain(self, cat, aid):
        A = self.alternatives.get(cat, {}); out, k = [], aid
        while k and k in A and len(out) < 1000: out.append(k); k = A[k].get("parent")
        return list(reversed(out))

    def alt_edits(self, cat, aid):
        return [e for k in self.alt_chain(cat, aid) for e in self.alternatives[cat][k]["edits"]]

    def _key(self, sid):
        chain, s = [], self.scenarios[sid]
        while s: chain.append(s); s = self.scenarios.get(s.parent) if s.parent else None
        alts = self.alts_of(sid)
        return chain, tuple((c.id, len(c.edits)) for c in chain) + tuple(sorted((k, a, len(self.alt_edits(k, a))) for k, a in alts.items())), alts

    def model(self, sid):
        """The scenario's project: the base plus the parent chain's edits plus its own. With alternatives: the chain's
        own edits less the kinds taken from alternatives, and the alternatives' edits, merged in the order they were
        made (the session's edit clock), so the history replays as it happened."""
        chain, key, alts = self._key(sid)
        if self._cache.get("model_key") == key: return self._cache["model"]
        p = self.base.copy()
        if not alts:
            for c in reversed(chain):
                for e in c.edits: apply(p, e)
        else:
            items, k = [], 0
            for c in reversed(chain):
                last = -1
                for e in c.edits:
                    last = e.get("_seq", last)                        # an edit older than the clock keeps its place
                    own = e.get("own") if e.get("op") == "_alt" else e
                    if not own: continue
                    for cat, part in split_by_category(own):
                        if cat not in alts: items.append((last, CAT_ORDER.index(cat), k, part)); k += 1
            for cat, aid in alts.items():
                for e in self.alt_edits(cat, aid): items.append((e.get("_seq", -1), CAT_ORDER.index(cat), k, e)); k += 1
            skipped = 0
            for *_, e in sorted(items, key=lambda t: t[:3]):
                try: apply(p, e)
                except (ValueError, KeyError): skipped += 1           # an edit naming an element this scenario does not have
            p.meta = dict(getattr(p, "meta", {}) or {}, alternatives_skipped=skipped)
        self._cache = dict(model_key=key, model=p)
        return p

    def solve(self, sid):
        p = self.model(sid)
        key = ("solve", self._cache["model_key"])
        if self._cache.get("solve_key") != key:
            problems = p.check()
            if problems or not len(p.links):
                res, summ = None, dict(links=len(p.links), problems=problems[:20], seconds=0.0)
            else:
                res, summ = steady.solve(p); summ["problems"] = []
            self._cache.update(solve_key=key, solved=(res, summ))
        return self._cache["solved"]

    def edit(self, sid, e):
        s = self.scenarios[sid]; trial = self.model(sid).copy()
        structural = apply(trial, e)                               # validates: raises before anything is recorded
        alts = self.alts_of(sid); seq = self._tick()
        flat = e["ops"] if e.get("op") == "batch" else [e]
        if alts and any(category(x) in alts for x in flat):        # the parts of a kind taken from an alternative go there;
            items = []                                             # the scenario keeps one entry: one undo step
            for cat, part in split_by_category(e):
                if cat in alts:
                    self.alternatives[cat][alts[cat]]["edits"].append(dict(part, _seq=seq)); items.append([cat, alts[cat], seq])
            own = [x for x in flat if category(x) not in alts]    # its own part in the order given
            s.edits.append(dict(op="_alt", items=items, own=(own[0] if len(own) == 1 else dict(op="batch", ops=own)) if own else None, _seq=seq))
            s.redo = []; self._cache = {}; self.model(sid)
            return structural
        e["_seq"] = seq                                            # the validated dict itself (a design's report is in it)
        s.edits.append(e); s.redo = []
        chain, c = [], s                                           # the validated copy is the new state: no replay
        while c: chain.append(c); c = self.scenarios.get(c.parent) if c.parent else None
        self._cache = dict(model_key=tuple((c.id, len(c.edits)) for c in chain), model=trial)
        return structural

    def edit_many(self, sid, edits, fixed=False):
        """Several edits validated on ONE copy (opening a model with many scenarios), each still its own undo step;
        fixed=True makes them the scenario's definition, which undo never removes."""
        if not edits: return False
        s = self.scenarios[sid]; trial = self.model(sid).copy(); structural = False
        for e in edits: structural = apply(trial, e) or structural
        s.edits.extend(edits); s.redo = []
        if fixed: s.fixed = len(s.edits)
        chain, c = [], s
        while c: chain.append(c); c = self.scenarios.get(c.parent) if c.parent else None
        self._cache = dict(model_key=tuple((c.id, len(c.edits)) for c in chain), model=trial)
        return structural

    def undo(self, sid):
        s = self.scenarios[sid]
        if len(s.edits) > s.fixed:
            e = s.edits.pop()
            if e.get("op") == "_alt":                              # its parts leave their alternatives: exactly those edits
                taken = []
                for cat, aid, seq in e.get("items", []):
                    A = self.alternatives.get(cat, {}).get(aid)
                    for i, x in enumerate(A["edits"] if A else []):
                        if x.get("_seq") == seq: taken.append([cat, aid, A["edits"].pop(i)]); break
                e = dict(e, taken=taken)
            s.redo.append(e); self._cache = {}

    def redo_(self, sid):
        s = self.scenarios[sid]
        if s.redo:
            e = dict(s.redo.pop())
            if e.get("op") == "_alt":
                lost = []
                for cat, aid, x in e.pop("taken", []):
                    A = self.alternatives.get(cat, {}).get(aid)
                    if A is None: lost.append({k: v for k, v in x.items() if k != "_seq"}); continue
                    i = next((j for j, y in enumerate(A["edits"]) if y.get("_seq", -1) > x.get("_seq", -1)), len(A["edits"]))
                    A["edits"].insert(i, x)                       # back in its place in time
                if lost:                                           # its alternative is gone: the edit stays with the scenario
                    own = ([e["own"]] if e.get("own") else []) + lost
                    e["own"] = own[0] if len(own) == 1 else dict(op="batch", ops=own)
                    e["items"] = [it for it in e.get("items", []) if self.alternatives.get(it[0], {}).get(it[1]) is not None]
            s.edits.append(e); self._cache = {}

    def state(self):
        """What a snapshot keeps: the base model, the scenarios as edit lists, results read from other programs and
        reference layers. The base is never changed in place (scenarios copy it), so this can be pickled outside the lock."""
        import copy as _copy
        return dict(id=self.id, base=self.base, n=self._n, external=self.external, refs=getattr(self, "refs", []), routes=getattr(self, "routes", []),
                    symbology=getattr(self, "symbology", None), alternatives=_copy.deepcopy(getattr(self, "alternatives", {})),
                    seq=getattr(self, "_seq", 0), alt_n=getattr(self, "_alt_n", 0),
                    scenario_alts={s.id: dict(getattr(s, "alts", {}) or {}) for s in self.scenarios.values()},
                    scenarios=[(s.id, s.name, s.parent, list(s.edits), list(s.redo), s.fixed) for s in self.scenarios.values()])

    @classmethod
    def from_state(cls, st):
        if hasattr(st["base"], "orient_lines"): st["base"].orient_lines()   # autosaves made before 2026-11-23 kept the source's direction
        s = cls(st["id"], st["base"]); s._n = st["n"]; s.external = st["external"]; s.refs = st.get("refs", []); s.routes = st.get("routes", []); s.symbology = st.get("symbology")
        s.scenarios = {}
        for sid, name, parent, edits, redo, fixed in st["scenarios"]:
            c = Scenario(sid, name, parent, edits); c.redo = redo; c.fixed = fixed; s.scenarios[sid] = c
        s.alternatives = st.get("alternatives", {}) or {}
        for sid, a in (st.get("scenario_alts") or {}).items():
            if sid in s.scenarios: s.scenarios[sid].alts = dict(a)
        s._seq, s._alt_n = st.get("seq", 0), st.get("alt_n", 0); s._rescan()
        return s

    def copy_scenario(self, sid, name=None):
        self._n += 1; new = f"S{self._n}"
        self.scenarios[new] = Scenario(new, name or f"{self.scenarios[sid].name} copy {self._n}", parent=sid)
        return self.scenarios[new]
