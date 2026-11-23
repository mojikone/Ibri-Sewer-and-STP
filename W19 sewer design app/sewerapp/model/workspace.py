"""Open projects and their scenarios, the way SewerGEMS keeps a model in memory: a scenario is its parent's model plus a
list of edits (by element id), with undo and redo. Every edit re-solves at once (instant re-run).

Edit ops (dicts with "op"):
  set        {table: nodes|links|catchments, ids: [...], field, value}         one field on one or many elements (bulk)
  set_values {table, field, values: {id: value}}                             one field, a value per element (imports)
  set_many   {table, field, values: {id: value}}                             as `set`, a value per element (a pasted column):
                                                                             node inverts carry link ends; one undo step
  set_loads  {set, values: {node: m3/d}}                                     unit loads of many nodes, one undo step
  add_node   {id?, kind, x, y, ground?, invert?}                               ground 0 and invert ground - 1.5 m by default
  add_link   {id?, kind, from_node, to_node, dn_mm?, length_m?, up_inv?, dn_inv?, coords?}
  add_catchment {id?, outlet, area_ha, imperv_pc, width_m, slope_pc, coords?}
  delete     {table, ids}                                                      deleting a node deletes its links
  move_node  {id, x, y}
  split_link {id, x, y}                                                        a new manhole on the link, two links
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
  set_infiltration {ids, rate}  a conduit's own infiltration rate (basis: settings.infiltration.method); None clears it
  set_storage {ids, area_m2 | curve [[depth, area]] | None}  a storage node's plan area for the storm run
  set_pump   {ids, q_ls, on_m, off_m | None}  a pump's capacity and its start/stop depths at the inlet (storm run)
  set_prototype {kind, values}  what a new element of that kind gets (manhole/outfall/wetwell: ground, depth;
                             conduit: dn_mm, section; catchment: imperv_pc, width_m, slope_pc, n_imperv, n_perv)
New elements take their prototype for every value the edit does not give."""
import copy, itertools, math
import numpy as np, pandas as pd
from sewerapp.engine import steady
from sewerapp.model.general import Project, NODE_KINDS, LINK_KINDS, LINK_COLS, NODE_COLS, CATCH_COLS

DEFAULT_DEPTH = 1.5


def _new_id(df, prefix):
    used = set(map(str, df.index))
    for k in itertools.count(len(df) + 1):
        if f"{prefix}{k}" not in used: return f"{prefix}{k}"


def _length(p, a, b, coords=None):
    if coords and len(coords) >= 2:
        return sum(math.dist(coords[i], coords[i + 1]) for i in range(len(coords) - 1))
    return math.dist((p.nodes.x[a], p.nodes.y[a]), (p.nodes.x[b], p.nodes.y[b]))


def apply(p, e):
    """Apply one edit to project p in place; returns True when the structure (elements, geometry) changed."""
    op = e["op"]
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
        if e["table"] == "nodes" and e["field"] in ("x", "y"): _relength(p, ids); return True
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
        return True
    if op == "move_node":
        p.nodes.loc[str(e["id"]), ["x", "y"]] = [float(e["x"]), float(e["y"])]; _relength(p, [str(e["id"])]); return True
    if op == "split_link":
        lid = str(e["id"]); L = p.links.loc[lid].copy()
        nid = _new_id(p.nodes, "MH-"); x, y = float(e["x"]), float(e["y"])
        f = _length(p, L.from_node, L.to_node) and math.dist((p.nodes.x[L.from_node], p.nodes.y[L.from_node]), (x, y)) / max(_length(p, L.from_node, L.to_node), 1e-9)
        inv = L.up_inv + (L.dn_inv - L.up_inv) * f; g = p.nodes.ground[L.from_node] + (p.nodes.ground[L.to_node] - p.nodes.ground[L.from_node]) * f
        p.nodes.loc[nid] = dict(kind="manhole", x=x, y=y, ground=g, invert=inv, inflow_m3d=0.0)
        p.links = p.links.drop(index=lid)
        for k, (a, b, ui, di) in enumerate(((L.from_node, nid, L.up_inv, inv), (nid, L.to_node, inv, L.dn_inv))):
            p.links.loc[f"{lid}-{'ab'[k]}"] = dict(kind=L.kind, from_node=a, to_node=b, length_m=_length(p, a, b), dn_mm=L.dn_mm,
                                                   inside_mm=L.inside_mm, up_inv=ui, dn_inv=di, transfer=L.transfer, coords=None)
        return True
    if op == "set_load":
        if e["node"] not in p.nodes.index: raise ValueError(f"no node {e['node']}")
        p.load_sets.setdefault(str(e["set"]), {})[str(e["node"])] = float(e["value"]); return False
    if op == "set_setting":
        keys = e["path"].split("."); p.setting(keys[0]); d = p.settings
        for k in keys[:-1]: d = d[k]
        if keys[-1] not in d: raise ValueError(f"no setting {e['path']}")
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
        xa, ya, xb, yb = p.nodes.x[a], p.nodes.y[a], p.nodes.x[b], p.nodes.y[b]; L = math.hypot(xb - xa, yb - ya)
        mx = e.get("max_spacing")
        if mx == "table12": mx = spacing.table12(dn)
        lens = spacing.split_lengths(L, float(mx)) if (mx and kind == "conduit" and L > float(mx) + 1e-6) else [L]
        mids = e.get("mid_ids") or []; chain = [a]; s = 0.0; depth = p.prototype("manhole").get("depth", DEFAULT_DEPTH)
        ga, gb = float(p.nodes.ground[a]), float(p.nodes.ground[b])
        for k, piece in enumerate(lens[:-1]):
            s += piece; f = s / L
            nid = mids[k] if k < len(mids) else _new_id(p.nodes, "MH-")
            g = ga + (gb - ga) * f
            apply(p, dict(op="add_node", id=nid, kind="manhole", x=xa + (xb - xa) * f, y=ya + (yb - ya) * f, ground=g, invert=g - float(depth)))
            chain.append(nid)
        chain.append(b); e["mid_ids"] = chain[1:-1]
        if rev: chain = chain[::-1]
        lids = e.get("link_ids") or []; made = []
        for k, (u, v) in enumerate(zip(chain[:-1], chain[1:])):
            lid = lids[k] if k < len(lids) else _new_id(p.links, "P-" if kind == "conduit" else "PMP-")
            apply(p, dict(op="add_link", id=lid, kind=kind, from_node=u, to_node=v, dn_mm=dn)); made.append(lid)
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
        if e.get("q_ls") is None:
            for i in ids: p.pumps.pop(i, None)
            return False
        q, on, off = float(e["q_ls"]), float(e.get("on_m") or 0), float(e.get("off_m") or 0)
        if not q > 0: raise ValueError("a pump's capacity is a positive flow")
        if on and off and off >= on: raise ValueError("a pump stops at a lower depth than it starts")
        for i in ids: p.pumps[i] = dict(q_ls=q, on_m=on, off_m=off)
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
    m = p.links.from_node.isin(node_ids) | p.links.to_node.isin(node_ids)
    for lid in p.links.index[m]:
        r = p.links.loc[lid]
        if not (isinstance(r.coords, list) and len(r.coords) >= 2):
            p.links.at[lid, "length_m"] = _length(p, r.from_node, r.to_node)


class Scenario:
    def __init__(self, sid, name, parent=None, edits=None):
        self.id, self.name, self.parent = sid, name, parent
        self.edits = list(edits or []); self.redo = []
        self.fixed = 0                          # leading edits that define the scenario (an opened model's): not undoable

    def to_dict(self):
        return dict(id=self.id, name=self.name, parent=self.parent, edits=len(self.edits), can_undo=len(self.edits) > self.fixed,
                    can_redo=bool(self.redo))


class Session:
    """One open project: the base model, its scenarios, and a cache of solved states."""

    def __init__(self, pid, project):
        self.id, self.base = pid, project
        self.scenarios = {"base": Scenario("base", "Base")}; self._cache = {}; self._n = 0
        self.external = {}                      # scenario id -> results another program computed (SewerGEMS), by link id
        self.refs = []                          # reference layers shown under the network: [{id, name, geojson, ...}]

    def model(self, sid):
        """The scenario's project (the base plus the parent chain's edits plus its own)."""
        chain, s = [], self.scenarios[sid]
        while s: chain.append(s); s = self.scenarios.get(s.parent) if s.parent else None
        key = tuple((c.id, len(c.edits)) for c in chain)
        if self._cache.get("model_key") == key: return self._cache["model"]
        p = self.base.copy()
        for c in reversed(chain):
            for e in c.edits: apply(p, e)
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
        if len(s.edits) > s.fixed: s.redo.append(s.edits.pop())

    def redo_(self, sid):
        s = self.scenarios[sid]
        if s.redo: s.edits.append(s.redo.pop())

    def state(self):
        """What a snapshot keeps: the base model, the scenarios as edit lists, results read from other programs and
        reference layers. The base is never changed in place (scenarios copy it), so this can be pickled outside the lock."""
        return dict(id=self.id, base=self.base, n=self._n, external=self.external, refs=getattr(self, "refs", []), routes=getattr(self, "routes", []),
                    symbology=getattr(self, "symbology", None),
                    scenarios=[(s.id, s.name, s.parent, list(s.edits), list(s.redo), s.fixed) for s in self.scenarios.values()])

    @classmethod
    def from_state(cls, st):
        s = cls(st["id"], st["base"]); s._n = st["n"]; s.external = st["external"]; s.refs = st.get("refs", []); s.routes = st.get("routes", []); s.symbology = st.get("symbology")
        s.scenarios = {}
        for sid, name, parent, edits, redo, fixed in st["scenarios"]:
            c = Scenario(sid, name, parent, edits); c.redo = redo; c.fixed = fixed; s.scenarios[sid] = c
        return s

    def copy_scenario(self, sid, name=None):
        self._n += 1; new = f"S{self._n}"
        self.scenarios[new] = Scenario(new, name or f"{self.scenarios[sid].name} copy {self._n}", parent=sid)
        return self.scenarios[new]
