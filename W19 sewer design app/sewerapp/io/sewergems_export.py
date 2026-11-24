"""A SewerGEMS model as exported through its documented OpenFlows API by bridge job 100 (referee/jobs/): one folder with
scenarios.csv (id, label, parent, file) and, per scenario, conduits_<file>.csv, manholes_<file>.csv (and geometry.tsv
once). The proprietary model file itself is never read (clean room).

Every SewerGEMS scenario becomes an app scenario whose edits carry what differs from the first scenario (sizes,
inverts, active), and which holds SewerGEMS's own results (flow, velocity, depth, d/D) for colouring, tables and
comparison with the app's engine. Flows are in the model's display units as exported (m3/d in the Ibri model).
Box and open-channel conduits come with sections_<file>.csv (helper Sections.cs): their shape, rise, span, bottom width,
side slopes and n become the project's sections, and SewerGEMS's results for them in m3/s and metres, normal and critical
depth included. Where both files carry a flow, their ratio gives the conduit file's unit (m3/s in a storm model), so the
stored flows of every conduit are read right."""
import os
import numpy as np, pandas as pd
from sewerapp.model.general import Project, LINK_COLS


def _read(folder, file):
    c = pd.read_csv(os.path.join(folder, f"conduits_{file}.csv"))
    m = pd.read_csv(os.path.join(folder, f"manholes_{file}.csv"))
    return c, m


SEC_KEYS = ("rise_m", "span_m", "bottom_m", "z_left", "z_right", "n")
# SewerGEMS catalogue shape codes, as measured (2026-11-22, Block 04): code 3 is an open rectangle of width = span and
# bank = rise (its critical and normal depth equal the open rectangle's to 0.1 %; the class's 0.5 side slopes and the
# conduit's typed "BoxPipe 10 x 2.5" do not apply). Other codes keep the conduit's typed shape until measured.
CATALOGUE_SHAPE = {"3": "rect_open"}


def _sections(folder, file):
    """The non-circular conduits of one scenario: ({label: section}, results by label), or ({}, None) with no file."""
    f = os.path.join(folder, f"sections_{file}.csv")
    if not os.path.exists(f): return {}, None
    t = pd.read_csv(f)
    if "catalogue_shape" in t:                             # the catalogue size decides the section (the typed shape can be stale)
        cs = t.catalogue_shape.map(lambda v: CATALOGUE_SHAPE.get(str(v).split(".")[0]))
        t["shape"] = cs.where(cs.notna(), t["shape"])
    t = t[t["shape"].isin(["box", "rect_open", "trapezoid"])]
    t.index = t.label.astype(str)
    secs = {}
    for lab, r in t.iterrows():
        s = dict(shape=r["shape"], rise_m=float(r.rise_m), n=float(r.n) if r.n == r.n and r.n > 0 else 0.013)
        if r["shape"] == "trapezoid": s.update(bottom_m=float(r.bottom_m), z_left=float(r.z_left), z_right=float(r.z_right))
        else: s["span_m"] = float(r.span_m)
        nb = r.get("barrels", 1)
        if nb == nb and int(nb) > 1: s["barrels"] = int(nb)
        secs[lab] = s
    return secs, t


def _flow_factor(c, t):
    """m3/d per unit of the conduit file's flow column, from the links whose flow both files hold (1 if none)."""
    if t is None or not len(t): return 1.0
    j = c.assign(label=c.label.astype(str)).set_index("label").flow_m3d.astype(float).to_frame().join(t.flow_m3s, how="inner")
    j = j[(j.flow_m3d.abs() > 1e-9) & (j.flow_m3s.abs() > 1e-9)]
    if not len(j): return 1.0
    k = float((j.flow_m3s * 86400.0 / j.flow_m3d).median())
    return 1.0 if abs(k - 1) < 0.01 else k


def load(folder, name="SewerGEMS model", crs=None):
    sc = pd.read_csv(os.path.join(folder, "scenarios.csv"))
    geo = {}
    g = os.path.join(folder, "geometry.tsv")
    if os.path.exists(g):
        for line in open(g, encoding="utf-8").read().splitlines()[1:]:
            if not line.strip(): continue
            i, lab, wkt = line.split("\t")
            geo[lab] = [[float(a) for a in pt.split()] for pt in wkt[wkt.index("(") + 1: wkt.rindex(")")].split(",")]
    first = sc.iloc[0]; c0, m0 = _read(folder, first.file)
    nodes_lab = dict(zip(m0.id, m0.label.astype(str)))
    p = Project(name=name, crs=crs); p.load_sets = {"design": {}}
    kinds = m0["kind"].astype(str).values if "kind" in m0.columns else ["outfall" if r.diameter_m != r.diameter_m else "manhole" for r in m0.itertuples()]
    p.nodes = pd.DataFrame(dict(kind=kinds,                     # the direct reading (io/sewergems_db.py) names wet wells too
                                x=m0.x.values, y=m0.y.values, ground=m0.ground.values, invert=m0.invert.values, inflow_m3d=0.0),
                           index=pd.Index(m0.label.astype(str).values, name="id"))
    p.nodes = p.nodes[~p.nodes.index.duplicated()]
    sections = {}

    def link_table(c):
        c = c[c.active == True]
        lk = c["kind"].fillna("conduit").astype(str).values if "kind" in c.columns else np.full(len(c), "conduit", dtype=object)
        # a conduit runs from its higher end; a gutter, a channel without levels or a lateral keeps its drawn direction (v7)
        hi = np.where(lk == "conduit", (c.start_inv >= c.stop_inv).values, ~(c.start_inv < c.stop_inv).values | (lk == "gutter"))
        a = np.where(hi, c.start, c.stop); b = np.where(hi, c.stop, c.start)
        circ = (c.diameter_mm.astype(float) > 0).values           # a box or an open channel has no diameter: kept, not analysed
        nom = c.size_label.astype(str).str.extract(r"(\d+)")[0].astype(float).fillna(c.diameter_mm).astype(int).values
        nom = np.where(circ, nom, 0); ins = np.where(circ, c.diameter_mm.astype(float).values, np.nan)
        sections.update({str(l): str(s) for l, s, k, t in zip(c.label, c.size_label, circ, lk) if not k and t not in ("gutter",)})
        return pd.DataFrame(dict(kind=lk, from_node=[nodes_lab.get(x, str(x)) for x in a], to_node=[nodes_lab.get(x, str(x)) for x in b],
                                 length_m=c.length_m.values, dn_mm=nom, inside_mm=ins,
                                 up_inv=c[["start_inv", "stop_inv"]].max(axis=1).values, dn_inv=c[["start_inv", "stop_inv"]].min(axis=1).values,
                                 transfer=False, coords=[geo.get(l) if l in geo and len(geo[l]) > 2 else None for l in c.label.astype(str)]),
                            index=pd.Index(c.label.astype(str).values, name="id"))[LINK_COLS]

    p.links = link_table(c0)
    _pressure(folder, sc, p, nodes_lab)
    secs0, _ = _sections(folder, first.file)
    p.sections = {k: v for k, v in secs0.items() if k in p.links.index}   # boxes and channels with their section: solved
    for k in p.sections: sections.pop(k, None)
    p.meta = dict(getattr(p, "meta", {}) or {}, sections=sections)       # other non-circular sections: shown, not analysed
    loads_found = _loads(folder, sc, p, nodes_lab)
    props0 = _props_file(folder, first.file)
    if props0: p.props = {t: {k: v for k, v in props0.get(t, {}).items() if k in getattr(p, t).index} for t in ("nodes", "links")}
    scenarios, results = [], {}
    for r in sc.itertuples():
        c, _ = _read(folder, r.file); L = link_table(c); edits = []
        secs, t = _sections(folder, r.file)
        for k in sorted(set(secs) | set(p.sections)):
            if k in L.index and secs.get(k) != p.sections.get(k):
                e = dict(op="set_section", ids=[k], section=secs.get(k))
                if secs.get(k) is None and L.dn_mm[k] > 0: e["dn_mm"] = int(L.dn_mm[k])
                edits.append(e)
        common = L.index.intersection(p.links.index)
        for field in ("dn_mm", "inside_mm", "up_inv", "dn_inv"):   # one vectorised edit per field that differs
            diff = common[(L.loc[common, field] - p.links.loc[common, field]).abs() > 1e-9]
            if len(diff): edits.append(dict(op="set_values", table="links", field=field,
                                            values={k: float(x) for k, x in L.loc[diff, field].items()}))
        act = c[c.active == True]
        D = act.diameter_mm.values / 1000.0
        res = pd.DataFrame(dict(q_ls=act.flow_m3d.values * _flow_factor(c, t) / 86.4, v_ms=act.velocity_ms.values,
                                depth_m=np.maximum(act.depth_in_m.values, act.depth_out_m.values),
                                d_over_D=np.maximum(act.depth_in_m.values, act.depth_out_m.values) / D),
                           index=act.label.astype(str).values)
        if t is not None and len(t):                       # boxes and channels: SewerGEMS's own values in SI
            k = res.index.intersection(t.index); tt = t.loc[k]
            res.loc[k, "q_ls"] = tt.flow_m3s.values * 1000.0; res.loc[k, "v_ms"] = tt.velocity_ms.values
            dep = np.fmax(tt.depth_in_m.values, tt.depth_out_m.values)
            res.loc[k, "depth_m"] = dep; res.loc[k, "d_over_D"] = dep / tt.rise_m.values
            res.loc[k, "yn_sg_m"] = tt.normal_depth_m.values; res.loc[k, "yc_sg_m"] = tt.critical_depth_m.values
            # SewerGEMS's typed full capacity is left out: on Block 04 it follows the stale typed box, not the catalogue size
        pr = _props_file(folder, r.file)                                   # each kind's own fields, where this scenario differs
        for t in ("nodes", "links"):
            base_p = (getattr(p, "props", None) or {}).get(t, {})
            for k, v in (pr.get(t, {}) if pr else {}).items():
                if k in getattr(p, t).index and v != base_p.get(k): edits.append(dict(op="set_props", table=t, ids=[k], clear=True)); edits.append(dict(op="set_props", table=t, ids=[k], values=v))
        scenarios.append(dict(sg_id=int(r.id), label=str(r.label), parent=int(r.parent) if r.parent == r.parent else None, edits=edits))
        results[str(r.label)] = res
    for sc_ in scenarios: sc_["has_loads"] = loads_found
    return p, scenarios, results


def _props_file(folder, file):
    import json
    f = os.path.join(folder, f"props_{file}.json")
    if not os.path.exists(f): return None
    with open(f, encoding="utf-8") as fh: return json.load(fh)


def _pressure(folder, sc, p, nodes_lab):
    """Pumps and force mains (the direct reading's pressure_<file>.csv): from the first scenario in which any runs (a
    station switched off in the first scenario is still part of the network); the pump library from pump_definitions.csv."""
    files = [r.file for r in sc.itertuples() if os.path.exists(os.path.join(folder, f"pressure_{r.file}.csv"))]
    if not files: return
    pick = None
    for f in files:
        t = pd.read_csv(os.path.join(folder, f"pressure_{f}.csv"))
        if len(t) and t.active.astype(bool).any(): pick = t; break
    dfile = os.path.join(folder, "pump_definitions.csv")
    if pick is None:                                   # switched off in every scenario: out of the network, as in SewerGEMS
        pick = pd.read_csv(os.path.join(folder, f"pressure_{files[0]}.csv")).iloc[0:0]
    pick = pick[pick.active.astype(bool)]
    if os.path.exists(dfile):
        lib = []
        for r in pd.read_csv(dfile).to_dict("records"):
            d = {k: v for k, v in r.items() if v == v and v != "" and k != "points"}
            if r.get("points") == r.get("points") and r.get("points"): d["points"] = [[float(a), float(b)] for a, b in (x.split(":") for x in str(r["points"]).split(";"))]
            lib.append(d)
        p.settings.setdefault("libraries", {})["pumps"] = lib
    rows = {}
    for r in pick.itertuples():
        a, b = nodes_lab.get(r.start, str(r.start)), nodes_lab.get(r.stop, str(r.stop))
        if a not in p.nodes.index or b not in p.nodes.index: continue
        lab = str(r.label)
        if r.kind == "pump":
            rows[lab] = dict(kind="pump", from_node=a, to_node=b, length_m=0.0, dn_mm=0, inside_mm=np.nan, up_inv=np.nan, dn_inv=np.nan, transfer=False, coords=None)
            pu = {k: float(v) for k, v in (("q_ls", r.q_ls), ("on_m", r.on_m), ("off_m", r.off_m)) if v == v}
            if isinstance(r.definition, str) and r.definition: pu["definition"] = r.definition
            n = getattr(r, "count", 1)
            if n == n and int(n) > 1: pu["count"] = int(n)                        # a battery: lead and lag pumps together
            tg = getattr(r, "vspb_target_m", np.nan)
            if tg == tg: pu["vspb"] = dict(target_m=float(tg), control=str(getattr(r, "vspb_control", "") or ""))
            if pu: p.pumps[lab] = pu
        else:
            d = float(r.diameter_mm) if r.diameter_mm == r.diameter_mm else np.nan
            rows[lab] = dict(kind="pressure_pipe", from_node=a, to_node=b, length_m=float(r.length_m), dn_mm=int(round(d)) if d == d else 0, inside_mm=d,
                             up_inv=float(p.nodes.invert[a]), dn_inv=float(p.nodes.invert[b]), transfer=False, coords=None)
            if r.C == r.C and r.C > 0: p.ppipes[lab] = dict(method="hazen", C=float(r.C))
    if rows: p.links = pd.concat([p.links, pd.DataFrame.from_dict(rows, orient="index")[LINK_COLS]])


M3D_PER_CFS = 2446.575545
LS_PER_CFS = 28.316846592


def _peaking(folder):
    """The Extreme Flow Setup's factor table (base load in cfs -> L/s, factor), from support_loads.csv."""
    f = os.path.join(folder, "support_loads.csv")
    if not os.path.exists(f): return None
    t = pd.read_csv(f, dtype=str)
    setup = t[(t.type == "ExtremeFlowSetup") & (t.field == "ExtremeFlowSetupCollection")].value
    if setup.empty: return None
    method = dict(kv.split("=", 1) for kv in setup.iloc[0].split(" ; ")[0].split("|")).get("ExtremeFlowSetupCollection_EffExtemeFlowMethod")
    curve = t[(t.type == "ExtremeFlowFactor") & (t.element_id == method) & (t.field == "EffTableCurve")].value
    if curve.empty: return None
    rows = []
    for item in curve.iloc[0].split(" ; "):
        d = dict(kv.split("=", 1) for kv in item.split("|"))
        rows.append([float(d["EffTableCurve_BaseLoad"]) * LS_PER_CFS, float(d["EffTableCurve_ExtremeFlowFactor"])])
    return sorted(rows)


def _loads(folder, sc, p, nodes_lab):
    """Each scenario's unit loads (load set) and pattern loads (inflow set, unpeaked) by its label; peaking table."""
    found = False
    for r in sc.itertuples():
        f = os.path.join(folder, f"loads_{r.file}.csv")
        if not os.path.exists(f): continue
        found = True; L = pd.read_csv(f)
        lab = str(r.label); ids = [nodes_lab.get(i, str(i)) for i in L.element_id]
        p.load_sets[lab] = {n: float(q) for n, q in zip(ids, L.unit_m3d) if q}
        p.inflow_sets[lab] = {n: float(q) for n, q in zip(ids, L.pattern_m3d) if q}
    tab = _peaking(folder)
    if tab:
        p.settings["peaking"]["method"] = "table"; p.settings["peaking"]["table"] = [[round(a, 9), b] for a, b in tab]
    p.settings["infiltration_m3d_per_km"] = 0.72      # not exported yet: the Ibri model's 720 L/day per km (G201 p72)
    return found
