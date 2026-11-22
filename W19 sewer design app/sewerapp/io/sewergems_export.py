"""A SewerGEMS model as exported through its documented OpenFlows API by bridge job 100 (referee/jobs/): one folder with
scenarios.csv (id, label, parent, file) and, per scenario, conduits_<file>.csv, manholes_<file>.csv (and geometry.tsv
once). The proprietary model file itself is never read (clean room).

Every SewerGEMS scenario becomes an app scenario whose edits carry what differs from the first scenario (sizes,
inverts, active), and which holds SewerGEMS's own results (flow, velocity, depth, d/D) for colouring, tables and
comparison with the app's engine. Flows are in the model's display units as exported (m3/d in the Ibri model)."""
import os
import numpy as np, pandas as pd
from sewerapp.model.general import Project, LINK_COLS


def _read(folder, file):
    c = pd.read_csv(os.path.join(folder, f"conduits_{file}.csv"))
    m = pd.read_csv(os.path.join(folder, f"manholes_{file}.csv"))
    return c, m


def load(folder, name="SewerGEMS model", crs=None):
    sc = pd.read_csv(os.path.join(folder, "scenarios.csv"))
    geo = {}
    g = os.path.join(folder, "geometry.tsv")
    if os.path.exists(g):
        for line in open(g, encoding="utf-8").read().splitlines()[1:]:
            i, lab, wkt = line.split("\t")
            geo[lab] = [[float(a) for a in pt.split()] for pt in wkt[wkt.index("(") + 1: wkt.rindex(")")].split(",")]
    first = sc.iloc[0]; c0, m0 = _read(folder, first.file)
    nodes_lab = dict(zip(m0.id, m0.label.astype(str)))
    p = Project(name=name, crs=crs); p.load_sets = {"design": {}}
    p.nodes = pd.DataFrame(dict(kind=["outfall" if r.diameter_m != r.diameter_m else "manhole" for r in m0.itertuples()],
                                x=m0.x.values, y=m0.y.values, ground=m0.ground.values, invert=m0.invert.values, inflow_m3d=0.0),
                           index=pd.Index(m0.label.astype(str).values, name="id"))
    p.nodes = p.nodes[~p.nodes.index.duplicated()]
    sections = {}

    def link_table(c):
        c = c[c.active == True]
        hi = (c.start_inv >= c.stop_inv).values
        a = np.where(hi, c.start, c.stop); b = np.where(hi, c.stop, c.start)
        circ = (c.diameter_mm.astype(float) > 0).values           # a box or an open channel has no diameter: kept, not analysed
        nom = c.size_label.astype(str).str.extract(r"(\d+)")[0].astype(float).fillna(c.diameter_mm).astype(int).values
        nom = np.where(circ, nom, 0); ins = np.where(circ, c.diameter_mm.astype(float).values, np.nan)
        sections.update({str(l): str(s) for l, s, k in zip(c.label, c.size_label, circ) if not k})
        return pd.DataFrame(dict(kind="conduit", from_node=[nodes_lab.get(x, str(x)) for x in a], to_node=[nodes_lab.get(x, str(x)) for x in b],
                                 length_m=c.length_m.values, dn_mm=nom, inside_mm=ins,
                                 up_inv=c[["start_inv", "stop_inv"]].max(axis=1).values, dn_inv=c[["start_inv", "stop_inv"]].min(axis=1).values,
                                 transfer=False, coords=[geo.get(l) if l in geo and len(geo[l]) > 2 else None for l in c.label.astype(str)]),
                            index=pd.Index(c.label.astype(str).values, name="id"))[LINK_COLS]

    p.links = link_table(c0)
    p.meta = dict(getattr(p, "meta", {}) or {}, sections=sections)       # non-circular sections by link: shown, not analysed
    loads_found = _loads(folder, sc, p, nodes_lab)
    scenarios, results = [], {}
    for r in sc.itertuples():
        c, _ = _read(folder, r.file); L = link_table(c); edits = []
        common = L.index.intersection(p.links.index)
        for field in ("dn_mm", "inside_mm", "up_inv", "dn_inv"):   # one vectorised edit per field that differs
            diff = common[(L.loc[common, field] - p.links.loc[common, field]).abs() > 1e-9]
            if len(diff): edits.append(dict(op="set_values", table="links", field=field,
                                            values={k: float(x) for k, x in L.loc[diff, field].items()}))
        act = c[c.active == True]
        D = act.diameter_mm.values / 1000.0
        res = pd.DataFrame(dict(q_ls=act.flow_m3d.values / 86.4, v_ms=act.velocity_ms.values,
                                depth_m=np.maximum(act.depth_in_m.values, act.depth_out_m.values),
                                d_over_D=np.maximum(act.depth_in_m.values, act.depth_out_m.values) / D),
                           index=act.label.astype(str).values)
        scenarios.append(dict(sg_id=int(r.id), label=str(r.label), parent=int(r.parent) if r.parent == r.parent else None, edits=edits))
        results[str(r.label)] = res
    for sc_ in scenarios: sc_["has_loads"] = loads_found
    return p, scenarios, results


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
