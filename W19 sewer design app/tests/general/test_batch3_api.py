"""Batch 3 on the server: any SewerGEMS model can be exported through the bridge (the job is written by the app, opens a
copy, and reports its state), models are listed from the shared folders; an export with box or channel sections opens
with those conduits shown and marked not analysed instead of being solved as zero-bore pipes."""
import importlib, os
import pytest
from fastapi.testclient import TestClient
from sewerapp.api import general_api
from sewerapp.api.app import app

C = TestClient(app)


@pytest.fixture()
def bj(tmp_path, monkeypatch):
    root = tmp_path / "bridge"
    for d in ("jobs", "out", "done"): (root / d).mkdir(parents=True)
    (root / "out" / "_alive.txt").write_text("alive")
    share = tmp_path / "share"; (share / "Majlas").mkdir(parents=True); (share / "Majlas" / "Majlas.stsw").write_text("x")
    (share / "Majlas" / "Majlas.stsw.sqlite").write_bytes(b"x" * 2_000_000)
    (share / "Installer").mkdir(); (share / "Installer" / "skip.stsw").write_text("x")
    monkeypatch.setenv("W19_BRIDGE", str(root)); monkeypatch.setenv("W19_SG_EXPORTS", str(tmp_path / "exports"))
    monkeypatch.setenv("W19_MODEL_SHARES", f"{share}=\\\\VBOXSVR\\Share")
    from sewerapp.io import bridge_jobs
    B = importlib.reload(bridge_jobs)
    yield B, root, tmp_path / "exports"
    monkeypatch.delenv("W19_BRIDGE"); monkeypatch.delenv("W19_MODEL_SHARES"); monkeypatch.delenv("W19_SG_EXPORTS"); importlib.reload(bridge_jobs)


def test_models_listed_a_job_written_and_followed(bj):
    B, root, exports = bj
    assert B.watcher()["alive"]
    ms = B.models(); assert [m["name"] for m in ms] == ["Majlas.stsw"]                          # installers are skipped
    m = ms[0]; assert m["guest"] == "\\\\VBOXSVR\\Share\\Majlas\\Majlas.stsw" and m["mb"] == 2.0 and not m["exported"]
    j = B.submit(m["guest"], m["tag"]); body = open(os.path.join(root, "jobs", j["job"] + ".ps1"), encoding="utf-8").read()
    assert "$src = '\\\\VBOXSVR\\Share\\Majlas\\Majlas.stsw'" in body and "Copy-Item -LiteralPath $src" in body and "Open(\"$dir\\model.stsw\")" in body
    assert B.job(j["job"])["state"] == "queued"
    open(os.path.join(root, "out", j["job"] + ".txt"), "wb").write("started".encode("utf-16"))
    assert B.job(j["job"])["state"] == "running"
    os.makedirs(exports / "Majlas"); (exports / "Majlas" / "log.txt").write_text("  scenario 1 'Base' -> s001\n")
    with open(os.path.join(root, "out", j["job"] + ".txt"), "ab") as f: f.write(b"\r\n__EXIT__ 0\r\n")             # the watcher appends
    os.replace(os.path.join(root, "jobs", j["job"] + ".ps1"), os.path.join(root, "done", j["job"] + ".ps1"))
    assert B.job(j["job"])["state"] == "failed"                                                    # finished without scenarios.csv
    (exports / "Majlas" / "scenarios.csv").write_text('id,label,parent,file\n1,"Base",0,s001\n')
    s = B.job(j["job"]); assert s["state"] == "ready" and s["scenarios_done"] == 1
    with pytest.raises(ValueError): B.submit("relative\\path.stsw", None)
    with pytest.raises(ValueError): B.submit("C:\\models\\x.wtg", None)


def test_box_and_channel_sections_are_shown_not_analysed(tmp_path, monkeypatch):
    d = tmp_path / "Channels"; d.mkdir()
    (d / "scenarios.csv").write_text('id,label,parent,file\n1,"2 yr",0,s001\n')
    (d / "manholes_s001.csv").write_text("id,label,active,x,y,ground,rim,invert,diameter_m\n"
                                        "1,J1,True,500000,2600000,12,12,10,914.4\n2,J2,True,500100,2600000,11,11,9,914.4\n3,J3,True,500200,2600000,10,10,8,914.4\n4,O1,True,500300,2600000,9,9,7,\n")
    (d / "conduits_s001.csv").write_text("id,label,start,stop,active,length_m,diameter_mm,size_label,start_inv,stop_inv,flow_m3d,velocity_ms,depth_in_m,depth_out_m\n"
                                        "10,C1,1,2,True,100,0,\"2.5 x 10\",10,9,NaN,NaN,NaN,NaN\n11,C2,2,3,True,100,300,\"300 mm\",9,8,NaN,NaN,NaN,NaN\n"
                                        "12,C3,3,4,True,100,0,\"Trapezoid 4 x 1.5\",8,7,NaN,NaN,NaN,NaN\n")
    monkeypatch.setattr(general_api, "SG_EXPORTS", str(tmp_path))
    info = C.post("/api/g/projects/open_sewergems/Channels").json(); pid = info["id"]
    s = C.get(f"/api/g/projects/{pid}/scenarios/base/results").json()
    assert s["summary"]["not_analysed"] == 2 and s["summary"]["conduits"] == 1 and s["summary"]["km"] == pytest.approx(0.3)
    assert "C1" in s["links"] and s["links"]["C1"].get("v_ms") is None and not s["links"]["C1"]["over_limit"]
    L = {f["id"]: f["properties"] for f in C.get(f"/api/g/projects/{pid}/scenarios/base/model").json()["links"]["features"]}
    assert L["C1"]["section"] == "2.5 x 10" and L["C3"]["section"] == "Trapezoid 4 x 1.5" and "section" not in L["C2"]
    assert L["C1"]["dn_mm"] == 0 and L["C2"]["dn_mm"] == 300
    assert C.get(f"/api/g/projects/{pid}/scenarios/base/stored").json()["links"]["C1"]["q_ls"] is None


def test_the_page_and_its_script_are_always_revalidated():
    """After an update the browser must not pair a cached page with a new script (the editor would stop at start)."""
    for u in ("/", "/static/editor/editor.js", "/static/editor/editor.css"):
        assert C.get(u).headers.get("cache-control") == "no-cache", u
