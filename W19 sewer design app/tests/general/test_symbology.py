"""Symbology on the server: the named definitions are kept with the project (its session snapshot and its GeoPackage),
refused when malformed, and the KMZ export can take the map's own colouring and labels."""
import io, pickle, zipfile
from fastapi.testclient import TestClient
from sewerapp.api import general_api
from sewerapp.api.app import app

C = TestClient(app)
SYM = {"active": "Review", "defs": {"Default": {"links": {"codings": []}}, "Review": {"links": {"codings": [{"id": "c1", "field": "v_ms"}], "color": "c1"}}}}


def _project():
    pid = C.post("/api/g/projects/new", json=dict(name="sym", crs=32640)).json()["id"]
    ed = lambda **e: C.post(f"/api/g/projects/{pid}/scenarios/base/edit", json=e)
    for i, (x, g) in enumerate([(500000, 100.0), (500100, 99.5)]): ed(op="add_node", id=f"N{i}", kind="manhole", x=x, y=2600000, ground=g, invert=g - 2)
    ed(op="add_node", id="O", kind="outfall", x=500200, y=2600000, ground=99.0, invert=97.0)
    ed(op="add_link", from_node="N0", to_node="N1", dn_mm=200); ed(op="add_link", from_node="N1", to_node="O", dn_mm=200)
    return pid


def test_symbology_is_kept_with_the_project_and_its_file():
    pid = _project()
    assert C.get(f"/api/g/projects/{pid}/symbology").json() is None
    assert C.post(f"/api/g/projects/{pid}/symbology", json={"active": "x", "defs": {}}).status_code == 400
    assert C.post(f"/api/g/projects/{pid}/symbology", json={"active": "x", "defs": {"y": {}}}).status_code == 400
    assert C.post(f"/api/g/projects/{pid}/symbology", json=SYM).status_code == 200
    assert C.get(f"/api/g/projects/{pid}/symbology").json() == SYM
    s = general_api._s(pid); st = pickle.loads(pickle.dumps(s.state()))                    # the session snapshot
    assert type(s).from_state(st).symbology == SYM
    data = C.get(f"/api/g/projects/{pid}/save").content                                     # the GeoPackage
    pid2 = C.post("/api/g/projects/open", files={"file": ("p.gpkg", data, "application/octet-stream")}).json()["id"]
    assert C.get(f"/api/g/projects/{pid2}/symbology").json() == SYM


def test_kmz_takes_the_maps_colouring_and_labels():
    pid = _project()
    body = dict(sid="base", title="Velocity (m/s)", classes=[["below 0.75", "#2166ac"], ["over 0.75", "#a50026"]],
                links={"P-1": "#2166ac", "P-2": "#a50026"}, labels={"P-1": "DN200\nL=100 m"})
    r = C.post(f"/api/g/projects/{pid}/export.kmz", json=body); assert r.status_code == 200, r.text
    kml = zipfile.ZipFile(io.BytesIO(r.content)).read("doc.kml").decode()
    assert "<name>Velocity (m/s)</name>" in kml and "<name>below 0.75 (1)</name>" in kml and "<name>over 0.75 (1)</name>" in kml
    assert "<b>DN200<br>L=100 m</b>" in kml and 'id="c2166ac"' in kml
    assert kml.index("below 0.75 (1)") < kml.index("over 0.75 (1)")                      # legend order
    plain = zipfile.ZipFile(io.BytesIO(C.get(f"/api/g/projects/{pid}/export.kmz").content)).read("doc.kml").decode()
    assert "Pipes by size" in plain                                                        # the GET export is unchanged
