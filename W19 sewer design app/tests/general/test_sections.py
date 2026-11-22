"""Box and open-channel sections: the hydraulics against hand calculations, the edit op (validation, undo, back to a
circle), the SWMM shapes both ways, a SewerGEMS export with its sections file (shapes, SI results, the unit of the flow
column) and the check against SewerGEMS's normal and critical depth, the profile's crown, and save and open."""
import numpy as np, pytest
from fastapi.testclient import TestClient
from sewerapp.api import general_api
from sewerapp.api.app import app
from sewerapp.engine import sections as X
from sewerapp.io import swmm_inp

C = TestClient(app)
G = 9.81


def _bisect(f, q, hi):
    lo = 0.0
    for _ in range(80):
        m = (lo + hi) / 2; lo, hi = (m, hi) if f(m) < q else (lo, m)
    return (lo + hi) / 2


def test_normal_and_critical_depth_match_hand_calculations():
    S, n = 0.002, 0.015
    # box 3 x 1.5, open trapezoid b 2 z 1.5/2, open rectangle 4 wide
    secs = [dict(shape="box", rise_m=1.5, span_m=3, n=n), dict(shape="trapezoid", rise_m=2, bottom_m=2, z_left=1.5, z_right=2, n=n),
            dict(shape="rect_open", rise_m=1, span_m=4, n=n)]
    q = np.array([2.0, 3.0, 1.5])
    y, A, full = X.normal_depth(q, np.full(3, S), *X.unpack(secs))
    box = lambda y: 3 * y * (3 * y / (3 + 2 * y)) ** (2 / 3) * S ** .5 / n
    tz = lambda y: (2 * y + 1.75 * y * y) * ((2 * y + 1.75 * y * y) / (2 + y * (np.sqrt(1 + 1.5 ** 2) + np.sqrt(1 + 4)))) ** (2 / 3) * S ** .5 / n
    assert y[0] == pytest.approx(_bisect(box, 2.0, 1.5), abs=1e-6) and y[1] == pytest.approx(_bisect(tz, 3.0, 5), abs=1e-6)
    assert not full.any()
    yc = X.critical_depth(q, *X.unpack(secs)[:5])
    assert yc[0] == pytest.approx((2.0 ** 2 / (G * 9)) ** (1 / 3), rel=1e-6)          # rectangle: yc = (q^2 / g b^2)^(1/3)
    assert yc[2] == pytest.approx((1.5 ** 2 / (G * 16)) ** (1 / 3), rel=1e-6)
    cap = X.full_capacity(*X.unpack(secs[:1])[:5], np.array([n]), np.array([S]))[0]
    assert cap == pytest.approx(4.5 * (4.5 / 9) ** (2 / 3) * S ** .5 / n)               # a full box: perimeter 2 (b + h)
    yb, _, fb = X.normal_depth(np.array([cap * 1.25, cap * 1.5]), np.full(2, S), *X.unpack(secs[:1] * 2))   # free surface up to (9/6)^(2/3) = 1.31 x full
    assert not fb[0] and yb[0] < 1.5 and fb[1] and yb[1] == 1.5                        # beyond the free-surface maximum: full


def _drawn():
    pid = C.post("/api/g/projects/new", json=dict(name="sec")).json()["id"]
    ed = lambda **e: C.post(f"/api/g/projects/{pid}/scenarios/base/edit", json=e)
    for i, (x, g) in enumerate([(0, 100.0), (100, 99.5), (200, 99.0)]): ed(op="add_node", id=f"N{i}", kind="manhole", x=x, y=0, ground=g, invert=g - 2)
    ed(op="add_node", id="O", kind="outfall", x=300, y=0, ground=98.5, invert=96.5)
    for a, b in (("N0", "N1"), ("N1", "N2"), ("N2", "O")): ed(op="add_link", from_node=a, to_node=b, dn_mm=200)
    ed(op="set_load", set="design", node="N0", value=86400.0)
    ed(op="set_setting", path="peaking.method", value="constant"); ed(op="set_setting", path="peaking.constant", value=1.0)
    return pid, ed


def test_set_section_solves_validates_undoes_and_returns_to_a_circle():
    pid, ed = _drawn()
    assert ed(op="set_section", ids=["P-2"], section=dict(shape="box", rise_m=0, span_m=2, n=0.015)).status_code == 400
    assert ed(op="set_section", ids=["P-2"], section=dict(shape="egg", rise_m=1, span_m=2, n=0.015)).status_code == 400
    assert ed(op="set_section", ids=["P-2"], section=dict(shape="box", rise_m=1.0, span_m=2.0, n=0.015)).status_code == 200
    res = C.get(f"/api/g/projects/{pid}/scenarios/base/results").json(); L = res["links"]["P-2"]
    q = L["q_ls"] / 1000
    y = _bisect(lambda y: 2 * y * (2 * y / (2 + 2 * y)) ** (2 / 3) * 0.005 ** .5 / 0.015, q, 1)
    assert L["depth_m"] == pytest.approx(y, abs=1e-4) and L["v_ms"] == pytest.approx(q / (2 * y), abs=1e-3)
    assert not L["over_limit"] and not L["over_vmax"] and res["summary"]["not_analysed"] == 0
    f = {x["id"]: x["properties"] for x in C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["links"]["features"]}
    assert f["P-2"]["section"] == "Box 2 x 1 m" and f["P-2"]["sec"]["n"] == 0.015 and f["P-2"]["dn_mm"] == 0
    prof = C.get(f"/api/g/projects/{pid}/scenarios/base/profile", params=dict(start="N0")).json()
    row = [r for r in prof if r["link"] == "P-2"][0]
    assert row["crown0"] - row["inv0"] == pytest.approx(1.0) and row["section"] == "Box 2 x 1 m"
    assert row["water0"] - row["inv0"] == pytest.approx(L["depth_m"], abs=1e-3)
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo")
    f = {x["id"]: x["properties"] for x in C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["links"]["features"]}
    assert "sec" not in f["P-2"] and f["P-2"]["dn_mm"] == 200
    ed(op="set_section", ids=["P-2"], section=dict(shape="trapezoid", rise_m=1.5, bottom_m=1, z_left=1, z_right=1, n=0.02))
    ed(op="set_section", ids=["P-2"], section=None, dn_mm=300)
    f = {x["id"]: x["properties"] for x in C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["links"]["features"]}
    assert "sec" not in f["P-2"] and f["P-2"]["dn_mm"] == 300 and f["P-2"]["inside_mm"] > 0


def test_barrels_share_the_flow():
    pid, ed = _drawn()
    one = dict(shape="box", rise_m=1.0, span_m=1.0, n=0.015)
    ed(op="set_section", ids=["P-2"], section=dict(one, barrels=2))
    L2 = C.get(f"/api/g/projects/{pid}/scenarios/base/results").json()["links"]["P-2"]
    ed(op="set_section", ids=["P-2"], section=one)
    L1 = C.get(f"/api/g/projects/{pid}/scenarios/base/results").json()["links"]["P-2"]
    y, _, _ = X.normal_depth(np.array([L2["q_ls"] / 2000]), np.array([0.005]), *X.unpack([one]))
    assert L2["depth_m"] == pytest.approx(y[0], abs=1e-4) and L2["depth_m"] < L1["depth_m"]
    assert L2["q_full_ls"] == pytest.approx(2 * L1["q_full_ls"])
    assert ed(op="set_section", ids=["P-2"], section=dict(one, barrels=1.5)).status_code == 400
    p = swmm_inp.to_project(INP.replace("C1 RECT_CLOSED 1.5 3 0 0 1", "C1 RECT_CLOSED 1.5 3 0 0 3"))
    assert p.sections["C1"]["barrels"] == 3 and " 3" in [l for l in str(swmm_inp.from_project(p)).splitlines() if "RECT_CLOSED" in l][0]


def test_a_saved_project_keeps_its_sections(tmp_path):
    pid, ed = _drawn()
    ed(op="set_section", ids=["P-1"], section=dict(shape="rect_open", rise_m=1.2, span_m=3, n=0.025))
    from sewerapp.io import gpkg_project
    s = general_api._s(pid); p = s.model("base"); f = tmp_path / "x.gpkg"
    gpkg_project.save(p, str(f)); q = gpkg_project.load(str(f))
    q = q[0] if isinstance(q, tuple) else q
    assert q.sections == {"P-1": dict(shape="rect_open", rise_m=1.2, span_m=3.0, n=0.025)}


INP = """[OPTIONS]
FLOW_UNITS CMS
[JUNCTIONS]
J1 100 3 0 0 0
J2 99 3 0 0 0
J3 98.5 3 0 0 0
[OUTFALLS]
O1 98 FREE NO
[CONDUITS]
C1 J1 J2 100 0.015 0 0 0 0
C2 J2 J3 100 0.02 0 0 0 0
C3 J3 O1 100 0.013 0 0 0 0
[XSECTIONS]
C1 RECT_CLOSED 1.5 3 0 0 1
C2 TRAPEZOIDAL 2 4 1.5 2 1
C3 CIRCULAR 0.6 0 0 0 1
[COORDINATES]
J1 0 0
J2 100 0
J3 200 0
O1 300 0
"""


def test_swmm_shapes_in_and_out():
    p = swmm_inp.to_project(INP)
    assert p.sections == {"C1": dict(shape="box", rise_m=1.5, span_m=3.0, n=0.015),
                          "C2": dict(shape="trapezoid", rise_m=2.0, bottom_m=4.0, z_left=1.5, z_right=2.0, n=0.02)}
    assert p.links.dn_mm["C1"] == 0 and p.links.dn_mm["C3"] == 600
    p.sections["C1"]["n"] = 0.017; p.sections.pop("C2"); p.links.loc["C2", ["dn_mm", "inside_mm"]] = [800, 800.0]
    out = str(swmm_inp.from_project(p))
    rows = {l.split()[0] + l.split()[1][:4]: l.split() for l in out.splitlines() if l[:2] in ("C1", "C2", "C3")}
    assert rows["C1J1"][4] == "0.017" and rows["C1RECT"][2:4] == ["1.5", "3"]
    assert rows["C2CIRC"][2] == "0.8" and rows["C3CIRC"][2] == "0.6"


def _export(d, flow_unit_per_m3s):
    d.mkdir()
    (d / "scenarios.csv").write_text('id,label,parent,file\n1,"2 yr",0,s001\n')
    (d / "manholes_s001.csv").write_text("id,label,active,x,y,ground,rim,invert,diameter_m\n"
                                        "1,J1,True,500000,2600000,12,12,10,914.4\n2,J2,True,500100,2600000,11,11,9.8,914.4\n"
                                        "3,J3,True,500200,2600000,10,10,9.6,914.4\n4,O1,True,500300,2600000,9,9,9.4,\n")
    k = flow_unit_per_m3s
    (d / "conduits_s001.csv").write_text("id,label,start,stop,active,length_m,diameter_mm,size_label,start_inv,stop_inv,flow_m3d,velocity_ms,depth_in_m,depth_out_m\n"
                                        f"10,C1,1,2,True,100,0,\"Box - 3 x 1.5 m\",10,9.8,{2.0 * k},1,0.6,0.6\n"
                                        f"11,C2,2,3,True,100,300,\"300 mm\",9.8,9.6,{0.05 * k},0.9,0.1,0.1\n"
                                        f"12,C3,3,4,True,100,0,\"Trapezoid\",9.6,9.4,{2.0 * k},1,0.5,0.5\n")
    # SewerGEMS's own normal and critical depth, here from the textbook relations at its flow and the conduit's gradient
    S = 0.002; secs = [dict(shape="box", rise_m=1.5, span_m=3, n=0.015), dict(shape="trapezoid", rise_m=2, bottom_m=2, z_left=1.5, z_right=1.5, n=0.02)]
    yn, _, _ = X.normal_depth(np.array([2.0, 2.0]), np.full(2, S), *X.unpack(secs)); yc = X.critical_depth(np.array([2.0, 2.0]), *X.unpack(secs)[:5])
    (d / "sections_s001.csv").write_text("id,label,shape,rise_m,span_m,bottom_m,z_left,z_right,n,flow_m3s,velocity_ms,depth_in_m,depth_out_m,normal_depth_m,critical_depth_m,full_capacity_m3s\n"
                                        f"10,C1,box,1.5,3,,,,0.015,2.0,1.1,0.62,0.6,{yn[0] * 1.004},{yc[0]},5.0\n"
                                        f"12,C3,trapezoid,2,,2,1.5,1.5,0.02,2.0,1.0,0.5,0.52,{yn[1]},{yc[1]},9.0\n")


@pytest.mark.parametrize("unit", [1.0, 86400.0])                    # the conduit file in m3/s (a storm model) or m3/d
def test_a_sewergems_export_with_sections(tmp_path, monkeypatch, unit):
    _export(tmp_path / "Block", unit)
    monkeypatch.setattr(general_api, "SG_EXPORTS", str(tmp_path))
    pid = C.post("/api/g/projects/open_sewergems/Block").json()["id"]
    s = C.get(f"/api/g/projects/{pid}/scenarios/base/results").json()
    assert s["summary"]["not_analysed"] == 0 and s["summary"]["conduits"] == 3
    L = {f["id"]: f["properties"] for f in C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["links"]["features"]}
    assert L["C1"]["sec"] == dict(shape="box", rise_m=1.5, span_m=3.0, n=0.015) and L["C3"]["sec"]["shape"] == "trapezoid"
    st = C.get(f"/api/g/projects/{pid}/scenarios/base/stored").json()["links"]
    assert st["C1"]["q_ls"] == pytest.approx(2000) and st["C2"]["q_ls"] == pytest.approx(50)            # the unit is read right
    assert st["C1"]["d_over_D"] == pytest.approx(0.62 / 1.5, abs=1e-3)
    chk = C.get(f"/api/g/projects/{pid}/scenarios/base/section_check").json()
    assert chk["compared"] == 2 and chk["yn_within_1pc"] == 100 and chk["yn_max_diff_pc"] == pytest.approx(0.4, abs=0.01)
    assert chk["yc_max_diff_m"] < 1e-6
