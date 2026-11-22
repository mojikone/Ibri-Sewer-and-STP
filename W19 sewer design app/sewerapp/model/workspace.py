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
                             None to make them circular again, at size dn_mm (the smallest catalogue size if not given)"""
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
        g = float(e.get("ground", 0.0))
        p.nodes.loc[nid] = dict(kind=kind, x=float(e["x"]), y=float(e["y"]), ground=g,
                                invert=float(e.get("invert", g - DEFAULT_DEPTH)), inflow_m3d=float(e.get("inflow_m3d", 0.0)))
        return True
    if op == "add_link":
        a, b = str(e["from_node"]), str(e["to_node"])
        for n in (a, b):
            if n not in p.nodes.index: raise ValueError(f"no node {n}")
        if a == b: raise ValueError("a link needs two different nodes")
        lid = str(e.get("id") or _new_id(p.links, "P-" if e.get("kind", "conduit") == "conduit" else "PMP-"))
        if lid in p.links.index: raise ValueError(f"link {lid} exists")
        dn = int(e.get("dn_mm", p.catalogue().nominal_mm.iloc[0]))
        coords = e.get("coords")
        p.links.loc[lid] = dict(kind=e.get("kind", "conduit"), from_node=a, to_node=b,
                                length_m=float(e.get("length_m") or _length(p, a, b, coords)), dn_mm=dn,
                                inside_mm=p.inside_of(dn), up_inv=float(e.get("up_inv", p.nodes.invert[a])),
                                dn_inv=float(e.get("dn_inv", p.nodes.invert[b])), transfer=bool(e.get("transfer", False)),
                                coords=coords)
        return True
    if op == "add_catchment":
        cid = str(e.get("id") or _new_id(p.catchments, "CM-"))
        if e["outlet"] not in p.nodes.index: raise ValueError(f"no node {e['outlet']}")
        p.catchments.loc[cid] = dict(outlet=e["outlet"], area_ha=float(e["area_ha"]), imperv_pc=float(e.get("imperv_pc", 50)),
                                     width_m=float(e.get("width_m", 100)), slope_pc=float(e.get("slope_pc", 1.0)),
                                     n_imperv=float(e.get("n_imperv", 0.013)), n_perv=float(e.get("n_perv", 0.15)),
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
        keys = e["path"].split("."); d = p.settings
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
