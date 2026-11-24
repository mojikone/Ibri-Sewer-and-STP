"""A SewerGEMS model read directly from its database (io/sewergems_db.py, 2026-11-24) against SewerGEMS's own API export
of the same model: the Ibri SC1-2056 final model, its Base and its "SC1-2056 design" scenario. On this computer only
(the model and the export are not in the repository)."""
import os
import numpy as np, pandas as pd
import pytest
from sewerapp.io import sewergems_db, sewergems_export

DB = r"D:\VBOX\bridge\out\w18\final_models\IBRI_SC1-2056_final.stsw.sqlite"
API = r"D:\VBOX\bridge\out\w19\export\SC1-2056_final"
pytestmark = pytest.mark.skipif(not (os.path.exists(DB) and os.path.isdir(API)), reason="the Ibri model and its export are on the engineer's computer only")


def test_direct_reading_equals_sewergems_export(tmp_path):
    out = str(tmp_path / "m")
    sc = sewergems_db.export(DB, out, only={1, 279818})
    assert [s["label"] for s in sc] == ["Base", "SC1-2056 design"]
    api = pd.read_csv(os.path.join(API, "scenarios.csv")).set_index("id")
    for s in sc:
        f_api = api.file[s["id"]]
        for kind, cols in (("manholes", ["x", "y", "ground", "invert"]), ("conduits", ["start", "stop", "length_m", "diameter_mm", "start_inv", "stop_inv"])):
            A = pd.read_csv(os.path.join(API, f"{kind}_{f_api}.csv")).set_index("id"); B = pd.read_csv(os.path.join(out, f"{kind}_{s['file']}.csv")).set_index("id")
            assert set(A.index) == set(B.index), kind
            for c in cols: assert float((A[c] - B.loc[A.index, c]).abs().max()) < 1e-4, (kind, c)
            assert (A.active.astype(bool) == B.loc[A.index, "active"].astype(bool)).all()
        A = pd.read_csv(os.path.join(API, f"loads_{f_api}.csv")).set_index("element_id"); B = pd.read_csv(os.path.join(out, f"loads_{s['file']}.csv")).set_index("element_id")
        k = A.index.union(B.index)
        assert float((A.unit_m3d.reindex(k).fillna(0) - B.unit_m3d.reindex(k).fillna(0)).abs().max()) < 1e-6
    p, scen, res = sewergems_export.load(out, "direct", 32640)                  # and it opens as the export does
    assert len(p.nodes) == 19312 and (p.nodes.kind == "outfall").sum() == 32 and p.settings["peaking"]["method"] == "table"
