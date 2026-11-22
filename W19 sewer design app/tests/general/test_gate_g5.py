"""Gate G5 (import and export): a network written to plain GIS layers with foreign field names, imported back with a
field mapping (and with ends snapped to nodes when no from/to fields exist), equals the original; DXF and CSV exports
open; SWMM .inp round trip is gate G4."""
import io, json, os, zipfile
import ezdxf, geopandas as gpd, pandas as pd, pytest
from fastapi.testclient import TestClient
from shapely.geometry import LineString, Point
from sewerapp.api.app import app

C = TestClient(app)


def _network(tmp):
    n = gpd.GeoDataFrame(dict(MH_ID=["A", "B", "C", "OUT"], GL=[100.0, 99.5, 99.0, 98.5], IL=[98.0, 97.4, 96.8, 96.2],
                              TYPE=["manhole", "manhole", "manhole", "outfall"]),
                         geometry=[Point(0, 0), Point(100, 0), Point(200, 0), Point(300, 0)], crs=32640)
    l = gpd.GeoDataFrame(dict(PIPE=["P1", "P2", "P3"], DIA=[200, 250, 315]),
                         geometry=[LineString([(0, 0), (100, 0)]), LineString([(100, 0), (150, 10), (200, 0)]),
                                   LineString([(200, 0.4), (300, -0.3)])], crs=32640)
    fn, fl = os.path.join(tmp, "nodes.gpkg"), os.path.join(tmp, "links.gpkg"); n.to_file(fn); l.to_file(fl)
    z = os.path.join(tmp, "links_shp.zip"); d = os.path.join(tmp, "shp"); os.makedirs(d); l.to_file(os.path.join(d, "links.shp"))
    with zipfile.ZipFile(z, "w") as zz:
        for f in os.listdir(d): zz.write(os.path.join(d, f), f)
    return fn, fl, z


@pytest.mark.gate_g5
def test_gis_import_with_mapping_and_snapping(tmp_path):
    fn, fl, z = _network(str(tmp_path))
    f = C.post("/api/g/gis/fields", files=dict(file=("nodes.gpkg", open(fn, "rb").read()))).json()
    assert set(f["fields"]) >= {"MH_ID", "GL", "IL"} and f["crs"] == 32640
    mapping = dict(nodes=dict(id="MH_ID", ground="GL", invert="IL", kind="TYPE"), links=dict(id="PIPE", dn_mm="DIA"))
    for links_file, fname in ((fl, "links.gpkg"), (z, "links_shp.zip")):
        r = C.post("/api/g/projects/import_gis", files=dict(nodes=("nodes.gpkg", open(fn, "rb").read()), links=(fname, open(links_file, "rb").read())),
                   params=dict(mapping=json.dumps(mapping), snap_m=1.0))
        assert r.status_code == 200, r.text
        m = C.get(f"/api/g/projects/{r.json()['id']}/scenarios/base/model").json()
        L = {x["id"]: x["properties"] for x in m["links"]["features"]}
        assert {k: (v["from_node"], v["to_node"], v["dn_mm"]) for k, v in L.items()} == \
               {"P1": ("A", "B", 200), "P2": ("B", "C", 250), "P3": ("C", "OUT", 315)}      # P3's ends snapped within 1 m
        assert abs(L["P2"]["length_m"] - (2 * (50 ** 2 + 10 ** 2) ** 0.5)) < 1e-9 and L["P1"]["up_inv"] == 98.0
        res = C.get(f"/api/g/projects/{r.json()['id']}/scenarios/base/results").json()
        assert res["summary"]["problems"] == [] and len(res["links"]) == 3
    bad = C.post("/api/g/projects/import_gis", files=dict(nodes=("nodes.gpkg", open(fn, "rb").read()), links=("links.gpkg", open(fl, "rb").read())),
                 params=dict(mapping=json.dumps(mapping), snap_m=0.1))
    assert bad.status_code == 400 and "tolerance" in bad.json()["detail"]


@pytest.mark.gate_g5
def test_dxf_and_csv_exports(tmp_path):
    fn, fl, _ = _network(str(tmp_path))
    mapping = dict(nodes=dict(id="MH_ID", ground="GL", invert="IL", kind="TYPE"), links=dict(id="PIPE", dn_mm="DIA"))
    pid = C.post("/api/g/projects/import_gis", files=dict(nodes=("n.gpkg", open(fn, "rb").read()), links=("l.gpkg", open(fl, "rb").read())),
                 params=dict(mapping=json.dumps(mapping))).json()["id"]
    doc = ezdxf.read(io.StringIO(C.get(f"/api/g/projects/{pid}/export.dxf").text))
    assert {"CONDUIT_DN200", "CONDUIT_DN250", "CONDUIT_DN315", "NODE"} <= {l.dxf.name for l in doc.layers}
    t = pd.read_csv(io.StringIO(C.get(f"/api/g/projects/{pid}/export.csv").text))
    assert list(t.id) == ["P1", "P2", "P3"] and "v_ms" in t.columns
