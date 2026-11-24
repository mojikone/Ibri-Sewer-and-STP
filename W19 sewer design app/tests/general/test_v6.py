"""v6 (2026-11-24), the engineer's F30-F41 on the server: a model's link that cannot be guessed, the open projects
listed only on this computer, /env, background layers (a shapefile with its sidecars, colour, opacity, order), a
SewerGEMS model sent from any device, and the assistant's answer reported step by step."""
import importlib, io, json, os, re, time, zipfile
import pytest
from fastapi.testclient import TestClient
from sewerapp.api import general_api
from sewerapp.api.app import app
from sewerapp.model.general import Project
from sewerapp.model import workspace as W

C = TestClient(app)
REMOTE = {"cf-connecting-ip": "203.0.113.7"}


def _p():
    p = Project("t", crs=32640)
    for i, x in enumerate((445000, 445100)): W.apply(p, dict(op="add_node", id=f"N{i}", x=x, y=2565000, ground=10.0, invert=8.0))
    W.apply(p, dict(op="add_node", id="O", kind="outfall", x=445200, y=2565000, ground=9.0, invert=7.0))
    W.apply(p, dict(op="add_link", from_node="N0", to_node="N1")); W.apply(p, dict(op="add_link", from_node="N1", to_node="O"))
    return p


def test_a_models_link_cannot_be_guessed_and_the_list_is_local_only():
    a, b = general_api._open(_p()), general_api._open(_p())
    assert re.fullmatch(r"p[0-9a-f]{16}", a) and a != b
    assert any(x["id"] == a for x in C.get("/api/g/projects").json())
    assert C.get("/api/g/projects", headers=REMOTE).json() == []                       # a visitor sees only their own (in their browser)
    assert C.get(f"/api/g/projects/{a}", headers=REMOTE).status_code == 200            # ... and opens a model by its link
    assert C.get("/api/g/env").json()["local"] is True and C.get("/api/g/env", headers=REMOTE).json()["local"] is False


def test_background_layers_sidecars_style_and_order(tmp_path):
    import geopandas as gpd
    from shapely.geometry import LineString, Point
    pid = general_api._open(_p())
    g = gpd.GeoDataFrame(dict(name=["road"]), geometry=[LineString([(445000, 2565010), (445200, 2565010)])], crs="EPSG:32640"); g.to_file(tmp_path / "roads.shp")
    files = [("files", (f"roads.{e}", (tmp_path / f"roads.{e}").read_bytes(), "application/octet-stream")) for e in ("shp", "shx", "dbf", "prj")]
    r = C.post(f"/api/g/projects/{pid}/reference", files=files).json(); assert r["count"] == 1 and r["name"] == "roads"
    lone = C.post(f"/api/g/projects/{pid}/reference", files=[("file", ("roads.shp", (tmp_path / "roads.shp").read_bytes(), "application/octet-stream"))])
    assert lone.status_code == 400 and ".dbf" in lone.json()["detail"]
    gpd.GeoDataFrame(dict(n=[1]), geometry=[Point(445050, 2565000)], crs="EPSG:32640").to_file(tmp_path / "pts.geojson", driver="GeoJSON")
    r2 = C.post(f"/api/g/projects/{pid}/reference", files=[("file", ("pts.geojson", (tmp_path / "pts.geojson").read_bytes(), "application/json"))]).json()
    assert C.post(f"/api/g/projects/{pid}/reference/{r['id']}/style", json=dict(color="#112233", opacity=0.4, visible=False)).json()["ok"]
    assert C.post(f"/api/g/projects/{pid}/reference/{r['id']}/style", json=dict(color="red")).status_code == 400
    C.post(f"/api/g/projects/{pid}/reference/order", json=dict(ids=[r2["id"], r["id"]]))
    L = C.get(f"/api/g/projects/{pid}/reference").json()
    assert [x["id"] for x in L] == [r2["id"], r["id"]] and L[1]["color"] == "#112233" and L[1]["opacity"] == 0.4 and L[1]["visible"] is False


@pytest.fixture()
def bridge(tmp_path, monkeypatch):
    root = tmp_path / "bridge"
    for d in ("jobs", "out", "done", "models"): (root / d).mkdir(parents=True)
    (root / "out" / "_alive.txt").write_text("alive")
    monkeypatch.setenv("W19_BRIDGE", str(root)); monkeypatch.setenv("W19_SG_EXPORTS", str(tmp_path / "exports"))
    monkeypatch.setenv("W19_MODEL_SHARES", f"{root / 'models'}=\\\\VBOXSVR\\VBOX\\bridge\\models")
    from sewerapp.io import bridge_jobs
    B = importlib.reload(bridge_jobs)
    yield B, root, tmp_path / "exports"
    monkeypatch.delenv("W19_BRIDGE"); monkeypatch.delenv("W19_MODEL_SHARES"); monkeypatch.delenv("W19_SG_EXPORTS"); importlib.reload(bridge_jobs)


def test_a_sewergems_model_sent_from_any_device(bridge):
    B, root, exports = bridge
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w") as zz: zz.writestr("Town.stsw", "x"); zz.writestr("Town.stsw.sqlite", b"y" * 1000); zz.writestr("../evil.stsw.sqlite", "z")
    r = C.post("/api/g/sewergems/upload", files=[("files", ("Town.zip", z.getvalue(), "application/zip"))], headers=REMOTE).json()
    assert r["name"] == "Town.stsw" and re.fullmatch(r"Town_[0-9a-f]{6}", r["tag"])
    up = [d for d in os.listdir(root / "models" / "uploads")]; assert len(up) == 1
    assert sorted(os.listdir(root / "models" / "uploads" / up[0])) == ["Town.stsw", "Town.stsw.sqlite", "evil.stsw.sqlite"]   # nothing outside its folder
    body = open(root / "jobs" / (r["job"] + ".ps1"), encoding="utf-8").read(); assert "\\\\VBOXSVR\\VBOX\\bridge\\models\\uploads\\" in body
    alone = C.post("/api/g/sewergems/upload", files=[("files", ("Town.stsw", b"x", "application/octet-stream"))])
    assert alone.status_code == 400 and ".sqlite" in alone.json()["detail"]
    # a visitor sees only their own uploads; this computer's folders and paths stay here
    m = C.get(f"/api/g/sewergems/models?mine={r['tag']}", headers=REMOTE).json()
    assert m["remote"] and m["models"] == [] and m["shares"] == [] and [j["tag"] for j in m["jobs"]] == [r["tag"]]
    assert C.post("/api/g/sewergems/export", json=dict(guest="C:\\x\\a.stsw"), headers=REMOTE).status_code == 403
    assert C.post("/api/g/projects/open_sewergems/SC1-2056_final", headers=REMOTE).status_code == 403


def test_the_assistant_reports_its_steps_while_it_works(monkeypatch):
    from sewerapp.assistant import runner
    monkeypatch.setenv("W19_ASSISTANT_STUB", "1")
    pid = general_api._open(_p())
    j = C.post("/api/g/assistant/start", json=dict(project=pid, scenario="base", message="How many pipes?")).json()
    for _ in range(100):
        s = C.get(f"/api/g/assistant/job/{j['job']}").json()
        if s["state"] == "done": break
        time.sleep(0.05)
    assert s["state"] == "done" and not s["error"] and "Stub answer" in s["out"]["reply"]
    assert [x["name"] for x in s["steps"] if x["kind"] == "tool"] == ["project_summary"]
    assert C.get(f"/api/g/assistant/job/{j['job']}").status_code == 404                  # collected once
    assert runner.EFFORT["sonnet"] == "medium" and "Never show JSON" in runner.SYSTEM_GENERAL
