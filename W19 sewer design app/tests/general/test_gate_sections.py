"""Gate: the app's box and channel hydraulics against SewerGEMS on a real model. Block 04 (Batinah flood channels, 212
open rectangular channels, n 0.03), its 2-year storm run by SewerGEMS's GVF-Rational solver in the VM (bridge job 108,
on a copy) and exported with each channel's catalogue size and SewerGEMS's normal and critical depth. At SewerGEMS's
own flow in each channel, the app's normal depth must be within 1 % of SewerGEMS's and the critical depth within 1 mm.
Skipped where the export is not on this machine."""
import os
import pytest
from fastapi.testclient import TestClient
from sewerapp.api import general_api
from sewerapp.api.app import app

ROOT = os.environ.get("W19_SG_EXPORTS", os.path.join("D:" + os.sep, "VBOX", "bridge", "out", "w19", "export"))
HERE = os.path.exists(os.path.join(ROOT, "Block04_2yr_check", "sections_s001.csv"))


@pytest.mark.gate_sections
@pytest.mark.skipif(not HERE, reason="the Block 04 section export (bridge job 108) is not on this machine")
def test_block04_channels_match_sewergems(monkeypatch):
    monkeypatch.setattr(general_api, "SG_EXPORTS", ROOT)
    C = TestClient(app)
    pid = C.post("/api/g/projects/open_sewergems/Block04_2yr_check").json()["id"]
    j = C.get(f"/api/g/projects/{pid}/scenarios/base/section_check").json()
    assert j["compared"] >= 180 and j["full_or_flat"] == 0
    assert j["yn_within_1pc"] == 100 and j["yn_max_diff_pc"] < 0.1 and j["yc_max_diff_m"] < 0.001
    s = C.get(f"/api/g/projects/{pid}/scenarios/base/results").json()["summary"]
    assert s["not_analysed"] == 0 and s["conduits"] == 212
