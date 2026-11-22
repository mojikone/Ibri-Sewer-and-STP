import os, subprocess
import pytest
from sewerapp.w18port import run
from sewerapp.referee import golden

W19 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(W19)
W18 = os.path.join(REPO, "W18 NWS scenarios 2056-2071")


def w18_status():
    return subprocess.run(["git", "status", "--porcelain", "--", W18], cwd=REPO, capture_output=True, text=True).stdout


@pytest.mark.gate_p0
@pytest.mark.slow
def test_port_reproduces_w18_sc1_2056(tmp_path):
    before = w18_status()
    root = run.build_workroot(str(tmp_path), ["SC1-2056"])
    info = run.run_cases(root, ["SC1-2056"])
    diffs = golden.case_differences(os.path.join(root, run.SUB, "SC1-2056"), "SC1-2056")
    assert diffs == [], "\n".join(diffs[:30])
    assert info["passes"] == 1          # seeded with W18's converged cuts, nothing changes
    assert w18_status() == before       # the run wrote nothing into W18
    print("timing", info)
