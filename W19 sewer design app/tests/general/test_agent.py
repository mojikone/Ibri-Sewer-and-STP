"""The assistant as an agent (2026-11-23 v5, F21): registered folders only, local only, changes only to what it made."""
import json
import geopandas as gpd
import pytest
from shapely.geometry import Point, LineString
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.assistant import agent, gtools

C = TestClient(app)


@pytest.fixture
def folder(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "FOLDERS_FILE", str(tmp_path / "cfg" / "folders.json"))
    monkeypatch.setitem(agent.CTX, "remote", False)
    d = tmp_path / "data"; d.mkdir()
    gpd.GeoDataFrame(dict(mh=["A", "B", "O"], gl=[110.0, 109.5, 109.0], il=[108.0, 107.4, 106.8], typ=["manhole", "manhole", "outfall"]),
                     geometry=[Point(500000, 2600000), Point(500100, 2600000), Point(500200, 2600000)], crs=32640).to_file(d / "mh.gpkg")
    gpd.GeoDataFrame(dict(pid=["P1", "P2"], dia=[250, 250]), geometry=[LineString([(500000, 2600000), (500100, 2600000)]),
                     LineString([(500100, 2600000), (500200, 2600000)])], crs=32640).to_file(d / "pipes.gpkg")
    gpd.GeoDataFrame(dict(pop=[300.0, 200.0]), geometry=[Point(500005, 2600004), Point(500098, 2599996)], crs=32640).to_file(d / "plots.gpkg")
    (d / "notes.txt").write_text("line one\nline two\n", encoding="utf-8")
    return d


def T(tool, **a):
    return gtools.call(None, tool, a)


def test_folders_are_registered_locally_and_refused_over_the_link(folder):
    assert C.get("/api/g/assistant/folders").json()["folders"] == []
    assert C.post("/api/g/assistant/folders", json=dict(path=str(folder))).status_code == 200
    r = C.post("/api/g/assistant/folders", json=dict(path=str(folder)), headers={"cf-connecting-ip": "1.2.3.4"})
    assert r.status_code == 403
    assert C.get("/api/g/assistant/folders", headers={"cf-connecting-ip": "1.2.3.4"}).json()["folders"] == []
    assert [e["name"] for e in T("list_files", path=str(folder), ext=".gpkg")["entries"]] == ["mh.gpkg", "pipes.gpkg", "plots.gpkg"]
    assert T("read_text_file", path="notes.txt", start_line=2, max_lines=5)["lines"] == ["line two"]
    with pytest.raises(ValueError, match="outside"): T("list_files", path=str(folder.parent), ext="")
    with pytest.raises(ValueError, match="outside"): T("read_text_file", path="../cfg/folders.json", start_line=1, max_lines=5)
    agent.CTX["remote"] = True
    with pytest.raises(ValueError, match="shared web link"): T("list_files", path=str(folder), ext="")


def test_build_a_network_from_layers_load_it_and_check_it(folder):
    agent.add_folder(str(folder))
    lay = T("inspect_layer", path="mh.gpkg")
    assert lay["features"] == 3 and {f["name"] for f in lay["fields"]} == {"mh", "gl", "il", "typ"}
    r = T("import_network", nodes_path="mh.gpkg", links_path="pipes.gpkg", node_map=json.dumps(dict(id="mh", ground="gl", invert="il", kind="typ")),
          link_map=json.dumps(dict(id="pid", dn_mm="dia")), name="From folder", snap_m=1.0)
    pid = r["project"]; assert r["links"] == 2
    assert {"kind": "open_project", "project": pid} in gtools.ACTIONS
    prev = T("loads_from_layer", project=pid, scenario="base", path="plots.gpkg", field="pop", scale=0.2, target="load", unit="", apply=False)
    assert prev["report"]["total"] == pytest.approx(100.0) and "applied" not in prev
    T("loads_from_layer", project=pid, scenario="base", path="plots.gpkg", field="pop", scale=0.2, target="load", unit="", apply=True)
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    assert m["loads"]["design"] == {"A": pytest.approx(60.0), "B": pytest.approx(40.0)}
    v = T("run_analysis", project=pid, scenario="base", kind="validate"); assert "items" in v
    e = T("edit_model", project=pid, scenario="base", edits=[dict(op="set", args=json.dumps(dict(table="links", ids=["P2"], field="dn_mm", value=300)))])
    assert e["applied"] == 1
    C.post(f"/api/g/projects/{pid}/scenarios/base/undo")                                   # one undo step
    m = C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()
    assert {f["id"]: f["properties"]["dn_mm"] for f in m["links"]["features"]}["P2"] == 250


def test_the_engineers_scenarios_are_not_touched():
    pid = C.post("/api/g/projects/new", json=dict(name="mine", crs=32640)).json()["id"]
    with pytest.raises(ValueError, match="engineer's"):
        T("edit_model", project=pid, scenario="base", edits=[dict(op="add_node", args=json.dumps(dict(id="X", x=0, y=0, ground=10, invert=8)))])
    r = T("make_scenario", project=pid, scenario="base", name="agent copy", edits=[])
    T("edit_model", project=pid, scenario=r["scenario"], edits=[dict(op="add_node", args=json.dumps(dict(id="X", x=0, y=0, ground=10, invert=8)))])
    assert C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["nodes"]["features"] == []


def test_new_project_is_the_agents_and_a_remote_trex_path_is_refused(tmp_path):
    r = T("new_project", name="Built by the agent", crs=32640); pid = r["project"]
    T("edit_model", project=pid, scenario="base", edits=[dict(op="add_node", args=json.dumps(dict(id="A", x=500000, y=2600000, ground=110, invert=108))),
                                                       dict(op="add_node", args=json.dumps(dict(id="O", kind="outfall", x=500100, y=2600000, ground=109, invert=107))),
                                                       dict(op="add_link", args=json.dumps(dict(id="P1", from_node="A", to_node="O", dn_mm=250)))])
    assert T("run_analysis", project=pid, scenario="base", kind="steady")["summary"]["conduits"] == 1
    f = tmp_path / "x.tif"; f.write_bytes(b"0")
    r = C.post(f"/api/g/projects/{pid}/scenarios/base/trex?path={f}", headers={"cf-connecting-ip": "1.2.3.4"})
    assert r.status_code == 403


def test_at_most_twenty_strict_tools_and_upload_names_cannot_choose_the_folder(tmp_path):
    d = gtools.definitions(); assert sum(t["strict"] for t in d) <= 20 and len({t["name"] for t in d}) == len(d)
    target = tmp_path / "planted.txt"
    r = C.post("/api/g/gis/fields", files=dict(file=(str(target), b"not a layer", "application/octet-stream")))
    assert r.status_code == 400 and not target.exists()
    r = C.post("/api/g/gis/fields", files=dict(file=("..\\..\\x.gpkg", b"x", "application/octet-stream")))
    assert r.status_code == 400


def test_a_foreign_host_name_counts_as_remote(folder):
    assert C.get("/api/g/assistant/folders", headers={"host": "evil.example:8765"}).json()["remote"] is True
    assert C.post("/api/g/assistant/folders", json=dict(path=str(folder)), headers={"host": "evil.example"}).status_code == 403
    assert C.get("/api/g/assistant/folders", headers={"host": "127.0.0.1:8765"}).json()["remote"] is False


def _fake_qgis(monkeypatch, seen):
    """A stand-in for the QGIS MCP plugin's socket: records each command, answers success."""
    import socket, struct, threading
    from sewerapp.assistant import qgis_link
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(8); monkeypatch.setattr(qgis_link, "PORT", srv.getsockname()[1])
    def loop():
        while True:
            try: c, _ = srv.accept()
            except OSError: return
            n = struct.unpack(">I", c.recv(4))[0]; m = json.loads(c.recv(n)); seen.append(m["type"])
            res = {"id": "L1", "name": "x"} if m["type"].startswith("add_") else [{"id": "L1", "name": "Plots"}]
            body = json.dumps({"status": "success", "result": res}).encode(); c.sendall(struct.pack(">I", len(body)) + body); c.close()
    threading.Thread(target=loop, daemon=True).start()
    return srv


def test_qgis_link_reads_and_never_sends_code(folder, monkeypatch):
    from sewerapp.assistant import qgis_link
    seen = []; srv = _fake_qgis(monkeypatch, seen)
    try:
        assert T("qgis_layers", limit=10, offset=0)["layers"][0]["name"] == "Plots"
        assert seen[:2] == ["get_layers", "get_layer_tree"]
        with pytest.raises(ValueError, match="not a command"): qgis_link.call("execute_code", dict(code="print(1)"))
        with pytest.raises(ValueError, match="not a command"): qgis_link.call("save_project")
        agent.add_folder(str(folder))
        r = T("qgis_add_layer", path="mh.gpkg", name="Manholes"); assert r["group"] == "W19" and "add_vector_layer" in seen
        with pytest.raises(ValueError, match="outside"): T("qgis_add_layer", path=str(folder.parent / "x.gpkg"), name="")
        agent.CTX["remote"] = True
        with pytest.raises(ValueError, match="shared web link"): T("qgis_layers", limit=10, offset=0)
    finally:
        srv.close()
