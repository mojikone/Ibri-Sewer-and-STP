"""Gate G3: the general design engine against W18 (rules fixed before the run): the gradient-by-size rule gives W18's
table for every catalogue size; the general re-lay gives W18's design depth (`depth_design`, before any steepening)
at every node of SC1-2056 within 1 mm; the general sizing gives W18's sizes on every pipe."""
import os, tempfile
import geopandas as gpd
import numpy as np, pandas as pd, pytest
from sewerapp import fixtures
from sewerapp.engine import design as w18design, design_general as dg
from sewerapp.io import w18csv
from sewerapp.model.general import Project
from sewerapp.model.network import Network

IBRI_SLOPES = {"200": 0.0051, "250": 0.00375, "315": 0.0027, "400": 0.00205, "500": 0.00155, "600": 0.00125,
               "700": 0.001, "800": 0.00085, "900": 0.00075}   # Table 11 (G203 p29), DN200 at the Ibri model's 0.51 %


def ibri_settings(p):
    p.settings["design"]["slope_min"] = dict(IBRI_SLOPES)
    cat = fixtures.read_csv("inputs/catalogue.csv").sort_values("nominal_mm")
    p.settings["design"]["catalogue"] = cat[["nominal_mm", "inside_mm"]].values.tolist()
    return p


@pytest.mark.gate_g3
def test_gradient_rule_equals_w18_table():
    net = Network.from_w18(fixtures.read_csv("inputs/conduits_network.csv"), fixtures.read_csv("inputs/manholes_network.csv"))
    cat = fixtures.read_csv("inputs/catalogue.csv").nominal_mm.values
    w18 = w18design.table11_slopes(net, cat); p = ibri_settings(Project(name="t"))
    assert {n: dg.slope_for(p.settings, n) for n in cat} == {int(n): w18[int(n)] for n in cat}


def _export_project(case="SC1-2056"):
    """W18's design network of a case (before steepening and cuts) as a general project."""
    e = fixtures.read_csv(f"golden/{case}/exports/conduits_{case}a.csv"); e = e[e.active == True]
    mh = fixtures.read_csv("inputs/manholes_network.csv").set_index("id")
    hi = e.start_inv >= e.stop_inv
    up = np.where(hi, e.start, e.stop).astype(str); dn = np.where(hi, e.stop, e.start).astype(str)
    p = ibri_settings(Project(name=case, crs=32640))
    nid = sorted(set(up) | set(dn))
    ground = mh.ground.where(mh.ground > 100); ground.index = ground.index.astype(str)
    p.nodes = pd.DataFrame(dict(kind="manhole", x=0.0, y=0.0, ground=[ground.get(n, np.nan) for n in nid], invert=np.nan,
                                inflow_m3d=0.0), index=pd.Index(nid, name="id"))
    # an outfall's ground: the model's own outfall (W17 option GeoPackage), else the manhole above it (W18's rule)
    f = os.path.join(tempfile.gettempdir(), "w19_S1.gpkg")
    if not os.path.exists(f): fixtures.materialize("geo/S1.gpkg", f)
    go = gpd.read_file(f, layer="outfalls").set_index("label").ground
    sub = e.label.str.split("-").str[0].values
    for t in set(dn) - set(up):
        k = np.flatnonzero(dn == t)[0]
        p.nodes.at[t, "ground"] = float(go[sub[k]]) if sub[k] in go.index else p.nodes.ground.get(up[k], np.nan)
    S0 = ((e[["start_inv", "stop_inv"]].max(axis=1) - e[["start_inv", "stop_inv"]].min(axis=1)) / e.length_m).values
    nom = e.size_label.str.extract(r"(\d+)")[0].astype(int).values
    p.links = pd.DataFrame(dict(kind="conduit", from_node=up, to_node=dn, length_m=e.length_m.values, dn_mm=nom,
                                inside_mm=e.diameter_mm.values, up_inv=1000.0, dn_inv=1000.0 - S0 * e.length_m.values,
                                transfer=False, coords=None), index=pd.Index(e.label.values, name="id"))
    return p, pd.Series(S0, index=e.label.values), e


@pytest.mark.gate_g3
def test_relay_equals_w18_design_depth_at_every_node():
    p, S0, _ = _export_project()
    up, dn, inv = dg.relay(p, p.links, S0)
    gold = fixtures.read_csv("golden/SC1-2056/split/nodes_SC1-2056.csv").set_index("id")
    gold.index = gold.index.astype(str)
    depth = (p.nodes.ground - inv.reindex(p.nodes.index)).dropna()
    common = depth.index.intersection(gold.index[gold.depth_design.notna()])
    diff = (depth[common] - gold.depth_design[common]).abs()
    assert len(common) >= 19000 and diff.max() <= 0.0006, (len(common), diff.max(), diff.idxmax())


@pytest.mark.gate_g3
def test_sizing_equals_w18_sizes():
    p, _, e = _export_project()
    start = w18csv.start_sizes(fixtures.path("inputs/conduits_start_sizes.csv"), pd.Series(e.label.values))
    new, passes = dg.size(p, e.flow_m3d.values / 86400.0, start)
    assert (new == p.links.dn_mm.values).all(), int((new != p.links.dn_mm.values).sum())


def test_design_of_a_drawn_network_meets_its_constraints():
    from sewerapp.model.workspace import apply
    p = Project(name="drawn"); p.load_sets = {"design": {}}; p.settings["design_load"] = "design"
    for i, (x, g) in enumerate([(0, 100.0), (100, 99.8), (200, 99.6), (300, 99.4)]):
        apply(p, dict(op="add_node", id=f"N{i}", kind="manhole" if i < 3 else "outfall", x=x, y=0, ground=g))
    for a, b in (("N0", "N1"), ("N1", "N2"), ("N2", "N3")): apply(p, dict(op="add_link", from_node=a, to_node=b))
    apply(p, dict(op="set_load", set="design", node="N0", value=3000.0))     # big enough to need more than DN200
    q, rep = dg.design(p)
    from sewerapp.engine import steady as st
    r, s = st.solve(q)
    assert s["over_limit"] == 0 and rep["sizes_changed"] >= 1
    for i in q.links.index:                       # minimum cover 1.3 m over the crown at both ends (G203 p33)
        L = q.links.loc[i]; D = L.inside_mm / 1000
        assert q.nodes.ground[L.from_node] - (L.up_inv + D) >= 1.3 - 1e-9
        assert abs((L.up_inv - L.dn_inv) / L.length_m - dg.slope_for(q.settings, L.dn_mm)) < 1e-12
