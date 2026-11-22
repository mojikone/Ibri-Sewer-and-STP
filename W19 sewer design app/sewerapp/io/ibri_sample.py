"""Ibri's W18 final designs as general projects (a sample, verified against W18): one project per case, built from the
frozen named outputs. A lift made by a cut is modelled as SewerGEMS's referee build had it: station manhole -> stub
conduit (the cut pipe) -> wet well -> pump to the receiving manhole. An existing outfall station is a wet well with a
pump to its receiver (`pumps_to`); a pump to the plant goes to the plant inlet. Gravity joins are conduits marked
`transfer` (W18 and SewerGEMS carried them as transfers). Load sets: the design year, 2031 and 2036."""
import geopandas as gpd
import numpy as np, pandas as pd
from sewerapp import fixtures
from sewerapp.model.general import Project

CASES = [f"{s}-{y}" for s in ("SC1", "SC2", "SC3", "SC4") for y in ("2051", "2056", "2061")]
_S1 = None


def _lines():
    global _S1
    if _S1 is None:
        import os, tempfile
        p = os.path.join(tempfile.gettempdir(), "w19_S1.gpkg")
        if not os.path.exists(p): fixtures.materialize("geo/S1.gpkg", p)
        _S1 = gpd.read_file(p, layer="pipes").set_index("label").geometry
    return _S1


def build(case, w18_transfers=False):
    """w18_transfers: hold every existing station and gravity join at W18's own transfer (fixed flow per load set), to
    test the engine against W18 pipe by pipe; otherwise every station flow is computed (consistent with the lifts)."""
    year = case.split("-")[1]
    N = fixtures.read_csv(f"golden/{case}/named/nodes.csv")
    K = fixtures.read_csv(f"golden/{case}/named/links.csv")
    ST = fixtures.read_csv(f"golden/{case}/products/stations.csv").set_index("name")
    ST_N = fixtures.read_csv(f"golden/{case}/named/stations.csv").set_index("name")
    cuts = fixtures.read_csv(f"golden/{case}/split/cuts_{case}.csv")
    exp = fixtures.read_csv(f"golden/{case}/exports/conduits_{case}a.csv").set_index("label")
    loads = fixtures.read_csv("inputs/manhole_loads.csv", index_col="manhole_id")
    p = Project(name=f"Ibri {case} (W18 final design)", crs=32640)
    p.settings["design_load"] = year; p.settings["check_load"] = "2031"
    kind = {"manhole": "manhole", "pump": "wetwell", "lift": "wetwell", "plant inlet": "outfall"}
    nodes = pd.DataFrame(dict(kind=N.kind.map(kind).values, x=N.x.values, y=N.y.values, ground=N.ground.values,
                              invert=(N.ground - N.depth).values, inflow_m3d=0.0), index=pd.Index(N.new.values, name="id"))
    oid = dict(zip(N.new, N.id))
    cut_station = {}                                  # station node label -> (cut pipe label, size)
    for c in cuts.itertuples():
        st = N.loc[N.old == c.station, "new"]
        if len(st): cut_station[st.iloc[0]] = c.pipe
    for st in cut_station: nodes.at[st, "kind"] = "manhole"   # the station manhole keeps its load; the wet well is new
    rows, lines = [], _lines()
    xy = nodes[["x", "y"]]
    for r in K.itertuples():
        g = lines.get(r.old) if r.old in lines.index else None
        coords = [list(c) for c in g.coords] if g is not None else None
        Lx = float(exp.length_m[r.old]) if r.old in exp.index else r.length_m      # exact length (named files round to 0.1 m)
        rows.append(dict(id=r.new, kind="conduit", from_node=r.from_mh, to_node=r.to_mh, length_m=Lx, dn_mm=int(r.dn_mm),
                         inside_mm=float(p.inside_of(r.dn_mm)), up_inv=nodes.ground[r.from_mh] - r.depth_up_m,
                         # laid from the upstream invert at the published gradient: depths stored to the millimetre
                         # are too coarse to rebuild the gradient of a short pipe
                         dn_inv=nodes.ground[r.from_mh] - r.depth_up_m - r.s_new_pc / 100.0 * Lx,
                         transfer=r.kind == "gravity join", coords=coords))
    for name, s in ST.iterrows():
        if s.pumps_to == "plant": continue
        to = s.pumps_to if s.pumps_to in nodes.index else ST.index[0]      # "STP at P1" -> the plant inlet
        if to == name: continue                                             # the plant inlet itself
        src = name
        if name in cut_station:                       # station manhole -> stub (the cut pipe) -> wet well -> pump
            ww = f"{name}-WW"; e = exp.loc[cut_station[name]]
            nodes.loc[ww] = dict(kind="wetwell", x=nodes.x[name] + 1.0, y=nodes.y[name], ground=nodes.ground[name],
                                 invert=nodes.invert[name] - 0.1, inflow_m3d=0.0)
            dn = int(str(e.size_label).split()[0])
            rows.append(dict(id=f"{name}-ST", kind="conduit", from_node=name, to_node=ww, length_m=float(e.length_m), dn_mm=dn,
                             inside_mm=float(p.inside_of(dn)), up_inv=nodes.invert[name], dn_inv=nodes.invert[name] - 0.1,
                             transfer=False, coords=None))
            src = ww
        rows.append(dict(id=f"{name}-RM", kind="pump", from_node=src, to_node=to, length_m=float(s.force_main_m),
                         dn_mm=int(s.force_main_dn) if s.force_main_dn == s.force_main_dn else 0, inside_mm=np.nan,
                         up_inv=np.nan, dn_inv=np.nan, transfer=False, coords=None))
    p.nodes = nodes
    p.links = pd.DataFrame(rows).set_index("id")
    for y in sorted({year, "2031", "2036"}):
        q = loads[f"Q_{y}"]
        p.load_sets[y] = {n: float(q.get(i, 0.0)) for n, i in oid.items() if q.get(i, 0.0)}
    if w18_transfers:
        tr = fixtures.read_csv(f"golden/{case}/exports/transfers_{case}.csv")
        join_src = {r.new: r.old.split("->")[0] for r in K[K.kind == "gravity join"].itertuples()}
        for y in p.load_sets:
            t = tr[tr.year == int(y)].set_index("source").flow_m3d
            f = {f"{n}-RM": float(t[o]) for n, o in ST_N.old.items() if n not in cut_station and o in t.index and f"{n}-RM" in p.links.index}
            f.update({j: float(t[s]) for j, s in join_src.items() if s in t.index})
            p.fixed_flows[y] = f
    p.meta = dict(case=case, old_of_link=dict(zip(K.new, K.old)), station_old=ST_N.old.to_dict(),
                  cut_pipe=cut_station)
    return p
