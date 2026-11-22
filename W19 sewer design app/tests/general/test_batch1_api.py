"""Batch 1 on the server: a pasted column is one undoable edit that keeps the rules of a single edit (a node's invert
carries the pipe ends that sat at it); loads of many nodes in one edit; an open project survives a restart through its
snapshot; reference GIS layers come back in map coordinates (a projected layer, a layer with no CRS, a DXF)."""
import json, os
import pytest
from fastapi.testclient import TestClient
from sewerapp.api import general_api
from sewerapp.api.app import app

C = TestClient(app)


def ed(pid, sid="base", **e):
    r = C.post(f"/api/g/projects/{pid}/scenarios/{sid}/edit", json=e); assert r.status_code == 200, r.text; return r.json()


def links(pid, sid="base"):
    return {f["id"]: f["properties"] for f in C.get(f"/api/g/projects/{pid}/scenarios/{sid}/model").json()["links"]["features"]}


@pytest.fixture()
def net():
    pid = C.post("/api/g/projects/new", json=dict(name="Batch 1", crs=32640)).json()["id"]
    for i, (x, g) in enumerate([(444000, 330.0), (444100, 329.5), (444200, 329.0)]):
        ed(pid, op="add_node", id=f"MH{i+1}", kind="manhole", x=x, y=2563000, ground=g, invert=g - 2.0)
    for a, b in (("MH1", "MH2"), ("MH2", "MH3")): ed(pid, op="add_link", from_node=a, to_node=b, dn_mm=200)
    return pid


def test_a_pasted_column_is_one_edit_and_carries_pipe_ends(net):
    before = links(net)
    r = ed(net, op="set_many", table="nodes", field="invert", values={"MH1": 327.6, "MH2": 327.2, "MH3": 326.7})
    L = links(net)
    assert L["P-1"]["up_inv"] == pytest.approx(327.6) and L["P-1"]["dn_inv"] == pytest.approx(327.2) and L["P-2"]["dn_inv"] == pytest.approx(326.7)
    assert r["scenario"]["edits"] == 6                        # 3 nodes + 2 links drawn, then the whole paste as one edit
    C.post(f"/api/g/projects/{net}/scenarios/base/undo")
    assert links(net) == before                              # one undo takes the whole paste back
    ed(net, op="set_many", table="links", field="dn_mm", values={"P-1": 250, "P-2": 315})
    L = links(net); assert (L["P-1"]["dn_mm"], L["P-2"]["dn_mm"]) == (250, 315) and L["P-2"]["inside_mm"] > L["P-1"]["inside_mm"]
    ed(net, op="set_loads", set="design", values={"MH1": 50.0, "MH2": 25.0})
    m = C.get(f"/api/g/projects/{net}/scenarios/base/model").json()
    assert m["loads"]["design"]["MH1"] == 50.0 and m["loads"]["design"]["MH2"] == 25.0
    bad = C.post(f"/api/g/projects/{net}/scenarios/base/edit", json=dict(op="set_loads", set="design", values={"XX": 1}))
    assert bad.status_code == 400 and "XX" in bad.text


def test_an_open_project_survives_a_restart(net, tmp_path, monkeypatch):
    monkeypatch.setattr(general_api, "AUTOSAVE", str(tmp_path))
    sc = C.post(f"/api/g/projects/{net}/scenarios/base/copy", json=dict(name="bigger")).json()["created"]
    ed(net, sc, op="set", table="links", ids=["P-2"], field="dn_mm", value=315)
    res0 = C.get(f"/api/g/projects/{net}/scenarios/{sc}/results").json()["links"]
    assert os.path.exists(general_api.snapshot(net))
    del general_api.SESSIONS[net]                            # the app restarts: nothing in memory
    info = C.get(f"/api/g/projects/{net}").json()
    assert [s["name"] for s in info["scenarios"]] == ["Base", "bigger"] and info["crs"] == 32640
    assert C.get(f"/api/g/projects/{net}/scenarios/{sc}/results").json()["links"] == res0
    C.post(f"/api/g/projects/{net}/scenarios/{sc}/undo")     # its history came back too
    assert links(net, sc)["P-2"]["dn_mm"] == 200
    assert C.get("/api/g/projects/p99999").status_code == 404


def _upload(pid, path):
    with open(path, "rb") as f:
        r = C.post(f"/api/g/projects/{pid}/reference", files={"file": (os.path.basename(path), f)})
    assert r.status_code == 200, r.text; return r.json()


def test_reference_layers_in_map_coordinates(net, tmp_path):
    import geopandas as gpd
    from shapely.geometry import LineString, Polygon
    from pyproj import Transformer
    g = gpd.GeoDataFrame(dict(name=["road", "plot"], area=[0.0, 400.0]),
                         geometry=[LineString([(444000, 2563010), (444200, 2563010)]), Polygon([(444050, 2563020), (444070, 2563020), (444070, 2563040), (444050, 2563040)])], crs=32640)
    f = str(tmp_path / "plots.geojson"); g.to_file(f, driver="GeoJSON")
    ref = _upload(net, f)
    assert ref["name"] == "plots" and ref["count"] == 2 and set(ref["fields"]) == {"name", "area"}
    lon, lat = ref["geojson"]["features"][0]["geometry"]["coordinates"][0]
    elon, elat = Transformer.from_crs(32640, 4326, always_xy=True).transform(444000, 2563010)
    assert abs(lon - elon) < 1e-7 and abs(lat - elat) < 1e-7
    assert [r["id"] for r in C.get(f"/api/g/projects/{net}/reference").json()] == [ref["id"]]
    # a DXF with no CRS is taken in the project's own coordinates
    import ezdxf
    doc = ezdxf.new(); doc.modelspace().add_line((444000, 2563000), (444100, 2563050)); fd = str(tmp_path / "survey.dxf"); doc.saveas(fd)
    d = _upload(net, fd); assert d["count"] >= 1 and d["crs"] is None
    x0, y0 = d["geojson"]["features"][0]["geometry"]["coordinates"][0]
    assert abs(x0 - elon) < 0.01 and abs(y0 - elat) < 0.01
    C.post(f"/api/g/projects/{net}/reference/{ref['id']}/delete")
    assert [r["id"] for r in C.get(f"/api/g/projects/{net}/reference").json()] == [d["id"]]
    bad = C.post(f"/api/g/projects/{net}/reference", files={"file": ("x.geojson", b"not json")})
    assert bad.status_code == 400
