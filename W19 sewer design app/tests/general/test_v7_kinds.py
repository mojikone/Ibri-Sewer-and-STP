"""v7 (2026-11-24): every element kind SewerGEMS draws; catch basin inlets by HEC-22; gutters; the engines' view.

The engineer: "yes add them [catch basins], but carefully, and ensure you've assessed the properties, attributes,
calculations etc. very well from SewerGEMS. Add any other remaining elements you've missed." The inlet equations are
checked against HEC-22's own worked examples (3rd ed., chapter 4); docs/INLETS_HEC22.md has the sources."""
import os, shutil, sqlite3
import pytest
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.engine import inlets as I, steady, tools_v4, validate
from sewerapp.io import swmm_inp
from sewerapp.model.general import Project
from sewerapp.model import workspace as W, kinds as K

C = TestClient(app)
G848 = dict(inlet_type="catalog", location="on_grade", gutter_shape="conventional", road_cross_slope=0.025, n_gutter=0.016, long_slope=0.04)


# ------------------------------------------------------------------ HEC-22's examples
def test_hec22_example_4_8_gutter_and_grates():
    """T 3 m, SL 0.04, Sx 0.025, n 0.016: Q 0.19 m3/s, Eo 0.45, V 1.66 m/s; P-50 0.6 x 0.6: Rf 1.0, Rs 0.036, Qi 0.091;
    reticuline: Rf 0.9, Qi 0.082; 1.2 m grates: Rs 0.155, Qi 0.103 (HEC-22 p 4-44/45, read off its charts)."""
    g = I.Gutter(G848); d = g.depth_for(0.19); Q, A, T = g.flow(d)
    assert T == pytest.approx(3.0, abs=0.03) and g.frontal_ratio(d, 0.6) == pytest.approx(0.45, abs=0.005) and 0.19 / A == pytest.approx(1.66, abs=0.02)
    q, det = I.capture(0.19, dict(G848, inlet_class="grate", grate_type="p50", grate_length_m=0.6, grate_width_m=0.6))
    assert det["Rf"] == 1.0 and det["Rs"] == pytest.approx(0.036, abs=0.001) and q == pytest.approx(0.091, rel=0.03)
    q, det = I.capture(0.19, dict(G848, inlet_class="grate", grate_type="reticuline", grate_length_m=0.6, grate_width_m=0.6))
    assert det["Rf"] == pytest.approx(0.9, abs=0.025) and q == pytest.approx(0.082, rel=0.05)   # SWMM's Chart 5 fit, 4 % off the chart read
    for gr in ("p50", "reticuline"):
        q, det = I.capture(0.19, dict(G848, inlet_class="grate", grate_type=gr, grate_length_m=1.2, grate_width_m=0.6))
        assert det["Rs"] == pytest.approx(0.155, abs=0.002) and q == pytest.approx(0.103, rel=0.03)


def test_hec22_example_4_9_curb_opening():
    """Q 0.05, SL 0.01, Sx 0.02, n 0.016: LT 7.29 m; a 3 m opening E 0.61, Qi 0.031; continuously depressed (a 25 mm over
    W 0.6 m): LT about 4.4 m (HEC-22 p 4-47/48)."""
    c = dict(G848, road_cross_slope=0.02, long_slope=0.01, inlet_class="curb", curb_length_m=3.0, curb_height_m=0.15)
    q, det = I.capture(0.05, c)
    assert det["LT_m"] == pytest.approx(7.29, abs=0.01) and q / 0.05 == pytest.approx(0.61, abs=0.01) and q == pytest.approx(0.031, abs=0.0005)
    q, det = I.capture(0.05, dict(c, gutter_cross_slope=0.02 + 0.025 / 0.6, gutter_width_m=0.6))
    assert det["LT_m"] == pytest.approx(4.36, abs=0.1) and q == pytest.approx(0.0439, rel=0.02)


def test_chart5_example_and_splash_over():
    """Chart 5A's example: a reticuline grate 0.91 m long at 2.4 m/s gives Rf 0.8."""
    Rf = 1 - 0.295 * (2.4 - I.splash_velocity("reticuline", 0.91))
    assert Rf == pytest.approx(0.8, abs=0.02)
    assert I.splash_velocity("p50", 0.6) > I.splash_velocity("p30", 0.6) > I.splash_velocity("reticuline", 0.6)


def test_sag_inlets_pass_everything_at_a_depth():
    s = dict(G848, location="in_sag", inlet_class="grate", grate_type="p50", grate_length_m=1.2, grate_width_m=0.6)
    q, det = I.capture(0.1, s)
    assert q == 0.1 and det["mode"] == "weir"
    qw, _ = I.sag_capacity(det["depth_m"], s, I.Gutter(s)); assert qw == pytest.approx(0.1, rel=1e-6)
    curb = dict(G848, location="in_sag", inlet_class="curb", curb_length_m=2.0, curb_height_m=0.1)
    g = I.Gutter(curb)
    assert I.sag_capacity(0.05, curb, g) == (pytest.approx(1.60 * 2.0 * 0.05 ** 1.5), "weir")            # Eq. 4-30, undepressed
    assert I.sag_capacity(0.2, curb, g)[1] == "orifice"
    slot = dict(G848, location="in_sag", inlet_class="slot", slot_length_m=3.0, slot_width_m=0.045)
    assert I.sag_capacity(0.05, slot, I.Gutter(slot)) == (pytest.approx(1.4 * 3.0 * 0.05 ** 1.5), "weir")
    for t, p, want in (("percent_capture", dict(capture_pc=60), 0.06), ("max_capacity", dict(q_max_ls=40), 0.04), ("full_capture", {}, 0.1),
                       ("rating_curve", dict(rating=[[0, 0], [200, 50]]), 0.025)):
        assert I.capture(0.1, dict(inlet_type=t, **p))[0] == pytest.approx(want)


# ------------------------------------------------------------------ the model
def _net():
    """Two catch basins in a street, a gutter between them, into a manhole and an outfall headwall; a property connection's
    lateral taps the last conduit."""
    p = Project("k", crs=32640)
    add = lambda **e: W.apply(p, dict(op="add_node", **e))
    add(id="CB1", kind="catch_basin", x=0, y=0, ground=20, invert=18.5); add(id="CB2", kind="catch_basin", x=60, y=0, ground=19.5, invert=18)
    add(id="MH1", x=100, y=-20, ground=19, invert=17); add(id="HW", kind="headwall", x=200, y=-20, ground=18, invert=16)
    add(id="PC", kind="property_connection", x=150, y=20, ground=19, invert=18); add(id="T", kind="tap", x=150, y=-20, ground=18.5, invert=16.5)
    W.apply(p, dict(op="add_link", id="G1", kind="gutter", from_node="CB1", to_node="CB2"))
    for i, a, b in (("P1", "CB1", "MH1"), ("P2", "CB2", "MH1"), ("P3", "MH1", "HW")): W.apply(p, dict(op="add_link", id=i, from_node=a, to_node=b, dn_mm=300))
    W.apply(p, dict(op="add_link", id="L1", kind="lateral", from_node="PC", to_node="T", dn_mm=150))
    W.apply(p, dict(op="set_props", table="nodes", ids=["T"], values=dict(link="P3")))
    return p


def test_new_kinds_take_their_defaults_and_their_fields_are_checked():
    p = _net()
    assert p.props["nodes"]["CB1"] == dict(inlet_type="full_capture", location="on_grade", structure="circular")
    assert p.props["nodes"]["HW"] == dict(boundary="free") and p.props["links"]["G1"]["gutter_shape"] == "from_start_inlet"
    assert p.links.dn_mm["G1"] == 0 and p.links.up_inv["G1"] == 20 and p.links.dn_mm["L1"] == 150
    with pytest.raises(ValueError, match="one of"): W.apply(p, dict(op="set_props", table="nodes", ids=["CB1"], values=dict(inlet_type="magic")))
    with pytest.raises(ValueError, match="no field"): W.apply(p, dict(op="set_props", table="nodes", ids=["HW"], values=dict(grate_type="p50")))
    with pytest.raises(ValueError, match="0-100"): W.apply(p, dict(op="set_props", table="nodes", ids=["CB1"], values=dict(capture_pc=120)))
    with pytest.raises(ValueError, match="no conduit"): W.apply(p, dict(op="set_props", table="nodes", ids=["T"], values=dict(link="NOPE")))
    W.apply(p, dict(op="set_props", table="nodes", ids=["CB1"], values=dict(inlet_type="percent_capture", capture_pc=60)))
    assert p.props["nodes"]["CB1"]["capture_pc"] == 60
    # a morph keeps what the new kind has and takes its defaults; the old kind's inlet goes
    W.apply(p, dict(op="set", table="nodes", ids=["CB1"], field="kind", value="manhole")); assert p.props["nodes"]["CB1"] == dict(structure="circular")
    W.apply(p, dict(op="set", table="nodes", ids=["CB1"], field="kind", value="catch_basin")); assert p.props["nodes"]["CB1"]["inlet_type"] == "full_capture"
    W.apply(p, dict(op="delete", table="nodes", ids=["CB2"]))
    assert "CB2" not in p.props["nodes"] and "G1" not in p.props["links"]
    assert set(K.NODE_KINDS) >= {"catch_basin", "headwall", "transition", "cross_section", "air_valve", "property_connection", "tap"}


def test_engine_view_and_the_steady_run():
    p = _net(); p.load_sets["design"] = {"PC": 86.4}                      # 1 L/s from the property
    assert p.check() == []                                                # the gutter is surface flow, not a second outlet
    v = steady.engine_view(p)
    assert "G1" not in v.links.index and "T" not in v.nodes.index and v.links.to_node["L1"] == "MH1"   # the tap joins P3's upstream structure
    assert v.nodes.kind["HW"] == "outfall" and v.nodes.kind["CB1"] == "manhole" and v.links.kind["L1"] == "conduit"
    assert p.nodes.kind["CB1"] == "catch_basin"                           # the project itself is untouched
    res, s = steady.solve(p)
    assert res.q_ls["L1"] > 1.0 and res.q_ls["P3"] == pytest.approx(res.q_ls["L1"] + res.q_ls["P1"] + res.q_ls["P2"], abs=0.005)   # P3 adds its own infiltration
    assert "G1" not in res.index and steady.flows(p, "design")["G1"] == 0


def test_validate_knows_the_new_kinds():
    p = _net()
    W.apply(p, dict(op="set_props", table="nodes", ids=["CB2"], values=dict(inlet_type="catalog", inlet_class="grate")))
    W.apply(p, dict(op="set_props", table="nodes", ids=["HW"], values=dict(boundary="fixed")))
    msgs = {(m["id"], m["message"]) for m in validate.run(p)}
    assert any(i == "CB2" and "needs grate_type, grate_length_m, grate_width_m" in m for i, m in msgs)
    assert any(i == "HW" and "tailwater" in m for i, m in msgs)
    assert not any("no outfall" in m for _, m in msgs)                    # the terminal headwall is the outfall
    assert not any(i == "T" and "flow ends" in m for i, m in msgs)


def test_rational_run_with_inlets_and_a_gutter():
    """CB1 captures 60 % of its flow, the rest runs down G1 to CB2 (full capture): the pipes carry what the inlets take;
    a bypass with no gutter is lost and reported."""
    p = _net()
    for cid, cb in (("C1", "CB1"), ("C2", "CB2")):
        W.apply(p, dict(op="add_catchment", id=cid, outlet=cb, area_ha=1.0, coords=[[0, 0], [100, 0], [100, 100], [0, 100]]))
        W.apply(p, dict(op="set_hydrology", ids=[cid], C=0.9, tc_min=10))
    p.rain = dict(idf=dict(durations_min=[5, 10, 30, 60], intensities=[150.0, 120.0, 70.0, 45.0]))
    W.apply(p, dict(op="set_props", table="nodes", ids=["CB1"], values=dict(inlet_type="percent_capture", capture_pc=60)))
    inl = {}; rows, s = tools_v4.rational(p, inl)
    q_c = 0.9 * 120.0 * 1.0 / 360.0 * 1000.0                              # 300 L/s from each catchment
    assert inl["CB1"]["q_captured_ls"] == pytest.approx(0.6 * q_c) and inl["CB1"]["bypass_to"] == "CB2"
    assert inl["CB2"]["q_gutter_ls"] == pytest.approx(q_c + 0.4 * q_c) and inl["CB2"]["q_captured_ls"] == pytest.approx(1.4 * q_c)
    assert rows["P1"]["q_rational_ls"] == pytest.approx(0.6 * q_c) and rows["P2"]["q_rational_ls"] == pytest.approx(1.4 * q_c)
    assert 0.95 * 2.0 * q_c < rows["P3"]["q_rational_ls"] < 2.0 * q_c       # all of it, at the lower intensity of P3's longer time of concentration
    W.apply(p, dict(op="delete", table="links", ids=["G1"]))
    inl = {}; tools_v4.rational(p, inl); assert inl["CB1"]["bypass_to"] == "lost" and inl["CB1"]["q_bypass_ls"] == pytest.approx(0.4 * q_c)


def test_swmm_takes_every_kind():
    p = _net(); W.apply(p, dict(op="set_props", table="nodes", ids=["HW"], values=dict(boundary="fixed", tailwater_m=16.5)))
    p.rain = dict(idf=dict(durations_min=[5, 10, 30, 60], intensities=[150.0, 120.0, 70.0, 45.0]))
    t = swmm_inp.from_project(p)
    sec = lambda name: t.split(f"[{name}]")[1].split("\n[")[0]
    assert "CB1" in sec("JUNCTIONS") and "PC" in sec("JUNCTIONS") and "HW" in sec("OUTFALLS") and "FIXED" in sec("OUTFALLS")
    assert "L1" in sec("CONDUITS") and "\nG1 " not in t and "\nT " not in sec("JUNCTIONS")
    assert " -" not in sec("CONDUITS").split("\nL1", 1)[1].split("\n")[0]    # the lateral joins at the tapped conduit's structure, never below it


def test_api_gives_the_fields_and_sets_them():
    pid = C.post("/api/g/projects/new", json=dict(name="k", crs=32640)).json()["id"]
    info = C.get(f"/api/g/projects/{pid}").json()
    assert "catch_basin" in info["node_kinds"] and "gutter" in info["link_kinds"] and any(f["key"] == "grate_type" for f in info["kind_fields"]["catch_basin"])
    ed = lambda q="", **e: C.post(f"/api/g/projects/{pid}/scenarios/base/edit{q}", json=e)
    r = ed("?model=1&results=1", op="add_node", id="CB", kind="catch_basin", lon=56.5, lat=23.2)
    assert r.status_code == 200 and "model" in r.json() and "results" in r.json()
    assert r.json()["model"]["nodes"]["features"][0]["properties"]["props"]["inlet_type"] == "full_capture"
    r = ed(op="set_props", table="nodes", ids=["CB"], values=dict(inlet_type="catalog", inlet_class="curb", curb_length_m=3, curb_height_m=0.15))
    assert r.status_code == 200
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    assert m["nodes"]["features"][0]["properties"]["props"]["curb_length_m"] == 3
    assert ed(op="set_props", table="nodes", ids=["CB"], values=dict(curb_length_m=-1)).status_code == 400


MAJLAS = r"C:\Users\mojtaba\Desktop\Win10 shared folder\SewerGEMS Majlas\SewerGEMS Majlas.stsw.sqlite"


@pytest.mark.skipif(not os.path.exists(MAJLAS), reason="the engineer's Majlas model is on this computer only")
def test_reader_takes_catch_basins_with_their_inlets_and_headwalls(tmp_path):
    """No model on this computer holds a live catch basin, so a copy of Majlas has one manhole redeclared as a catch basin
    with a catalogue grate inlet in a sag, and its outfall as a headwall with a fixed tailwater, the way SewerGEMS stores
    them (the element's row in the kind's table, its physical row, the inlet catalogue entry)."""
    from sewerapp.io import sewergems_db, sewergems_export
    db = str(tmp_path / "m.stsw.sqlite"); shutil.copy(MAJLAS, db)
    c = sqlite3.connect(db)
    mh = c.execute("select DomainElementID from Manhole where DomainElementID in (select DomainElementID from HMIDomainElement where IsDeleted = 0 and IsPrototype = 0) limit 1").fetchone()[0]
    of = c.execute("select DomainElementID from Outfall where DomainElementID in (select DomainElementID from HMIDomainElement where IsDeleted = 0 and IsPrototype = 0) limit 1").fetchone()[0]
    alt = c.execute("select AlternativeID from GravityNode_Physical_Data where DomainElementID = ?", (mh,)).fetchone()[0]
    c.execute("delete from Manhole where DomainElementID = ?", (mh,)); c.execute("insert into CatchBasin (DomainElementID) values (?)", (mh,))
    cols = [r[1] for r in c.execute("pragma table_info('CatchBasin_Physical_Data')")]
    vals = dict(DomainElementID=mh, AlternativeID=alt, InletType=3, InletLocation=1, GutterShape=0, Physical_RoadCrossSlope=0.02, Physical_GutterCrossSlope=0.02,
                OnGradeType_LongitudinalSlope=0.01, OnGradeType_ManningsN=0.016, Physical_GrateLength=2.0, Physical_GrateCloggingFactor=50.0, Physical_DepressedGutter=0)
    c.execute(f"insert into CatchBasin_Physical_Data ({','.join(vals)}) values ({','.join('?' * len(vals))})", list(vals.values()))
    sid = 990001
    icols = [r[1] for r in c.execute("pragma table_info('Inlet')")]
    iv = dict(SupportElementID=sid, InletType=3, GrateType=6, InletType_GrateWidth=2.0, InletType_DefaultGrateLength=2.0)
    c.execute(f"insert into Inlet ({','.join(iv)}) values ({','.join('?' * len(iv))})", list(iv.values()))
    c.execute("insert into CatchBasin_Physical_InletType_CatalogInletType (DomainElementID, AlternativeID, CatalogInletType_InletID) values (?, ?, ?)", (mh, alt, sid))
    inv = c.execute("select Physical_InvertElevation from GravityNode_Physical_Data where DomainElementID = ?", (of,)).fetchone()
    c.execute("delete from Outfall where DomainElementID = ?", (of,)); c.execute("insert into Headwall (DomainElementID) values (?)", (of,))
    c.execute("insert into Headwall_Physical_Data (DomainElementID, AlternativeID, Physical_InvertElevation) values (?, ?, ?)", (of, alt, inv[0] if inv else 100.0))
    c.commit(); c.close()
    out = str(tmp_path / "x"); sewergems_db.export(db, out)
    p, scen, _ = sewergems_export.load(out)
    lab = lambda i: [k for k, v in p.nodes.kind.items()]
    cb = [n for n in p.nodes.index if p.nodes.kind[n] == "catch_basin"]; hw = [n for n in p.nodes.index if p.nodes.kind[n] == "headwall"]
    assert len(cb) == 1 and len(hw) == 1
    d = p.props["nodes"][cb[0]]
    assert d["inlet_type"] == "catalog" and d["location"] == "in_sag" and d["inlet_class"] == "grate" and d["grate_type"] == "reticuline"
    assert d["grate_length_m"] == pytest.approx(0.6096) and d["grate_width_m"] == pytest.approx(0.6096) and d["clogging_pc"] == 50.0
    assert p.props["nodes"][hw[0]]["boundary"] == "free" and p.nodes.invert[hw[0]] == p.nodes.invert[hw[0]]
    assert steady.engine_view(p).nodes.kind[hw[0]] == "outfall"


# ------------------------------------------------------------------ the storm run: catch basins on SWMM 5.2's streets
def _street_net(cb2):
    from sewerapp.model.general import Project as P_
    p = P_("s", crs=32640); add = lambda **e: W.apply(p, dict(op="add_node", **e))
    add(id="CB1", kind="catch_basin", x=0, y=0, ground=20, invert=18.5); add(id="CB2", kind="catch_basin", x=100, y=0, ground=16, invert=14.5)
    add(id="MH1", x=150, y=-20, ground=15, invert=13); add(id="O", kind="outfall", x=250, y=-20, ground=14, invert=11)
    W.apply(p, dict(op="add_link", id="G1", kind="gutter", from_node="CB1", to_node="CB2"))
    for i, a, b in (("P1", "CB1", "MH1"), ("P2", "CB2", "MH1"), ("P3", "MH1", "O")): W.apply(p, dict(op="add_link", id=i, from_node=a, to_node=b, dn_mm=450))
    street = dict(street_halfwidth_m=6, street_curb_m=0.15, road_cross_slope=0.025, n_gutter=0.016, long_slope=0.04)
    W.apply(p, dict(op="set_props", table="nodes", ids=["CB1"], values=dict(inlet_type="catalog", inlet_class="grate", grate_type="p50", grate_length_m=0.6, grate_width_m=0.6, **street)))
    W.apply(p, dict(op="set_props", table="nodes", ids=["CB2"], values=dict(cb2, **street)))
    for cid, cb in (("C1", "CB1"), ("C2", "CB2")):
        W.apply(p, dict(op="add_catchment", id=cid, outlet=cb, area_ha=1.0, coords=[[0, 0], [100, 0], [100, 100], [0, 100]]))
        W.apply(p, dict(op="set_hydrology", ids=[cid], C=0.9, tc_min=10))
    p.rain = dict(idf=dict(durations_min=[5, 10, 30, 60], intensities=[150.0, 120.0, 70.0, 45.0]), duration_min=60, step_min=5)
    return p


def test_storm_run_captures_at_the_inlets_as_the_steady_engine_does():
    """SWMM's own HEC-22 grate on the gutter street captures, at its peak, what engine/inlets.py captures of that flow
    (within half a point); the catchments drain to the street; the bypass runs down the gutter to the next inlet; a sag
    inlet that cannot take its flow floods its street, in both runs."""
    from sewerapp.engine import storm
    p = _street_net(dict(inlet_type="catalog", inlet_class="grate", grate_type="reticuline", grate_length_m=0.6, grate_width_m=0.6, location="in_sag"))
    t = swmm_inp.from_project(p)
    assert "[STREETS]" in t and "IN_CB1           GRATE" in t and "CB2_BYP" in t and "C1               RG1              CB1_STR" in t
    r = storm.run(p); a = r["inlets"]["CB1"]
    q = a["q_street_peak_ls"] / 1000.0
    assert abs(I.capture(q, p.props["nodes"]["CB1"])[0] / q * 100 - a["capture_at_peak_pc"]) < 0.5
    assert r["inlets"]["CB2"]["location"] == "on_sag" and r["summary"]["flooded_nodes"] >= 1
    inl = {}; tools_v4.rational(p, inl); assert inl["CB2"]["floods"] is True


def test_storm_run_custom_inlets_and_the_fallback():
    from sewerapp.engine import storm
    p = _street_net(dict(inlet_type="percent_capture", capture_pc=70))
    t = swmm_inp.from_project(p)
    assert "IN_CB2           CUSTOM           IC_CB2" in t and "IC_CB2           DIVERSION" in t
    r = storm.run(p)
    assert abs(r["inlets"]["CB2"]["capture_at_peak_pc"] - 70.0) < 1.0
    W.apply(p, dict(op="set_props", table="nodes", ids=["CB2"], values=dict(street_halfwidth_m=None)))
    assert "CB2_BYP" not in swmm_inp.from_project(p)
    assert any("no street" in m["message"] for m in validate.run(p))
