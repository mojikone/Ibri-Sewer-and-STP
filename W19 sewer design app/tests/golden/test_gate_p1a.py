"""Gate P1A: the whole chain for all 12 cases against W18 at the spec's tolerances, and SC1-2056 against SewerGEMS's
saved export. Writes docs/GATE_P1A.json (the comparison, kept) and prints the timing."""
import json, os
import pytest
from sewerapp.referee import golden, sewergems
from sewerapp.w18port import run

W19 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def done(tmp_path_factory):
    root = run.build_workroot(str(tmp_path_factory.mktemp("p1a")), run.CASES)
    return root, run.run_cases(root, run.CASES)


@pytest.mark.gate_p1a
@pytest.mark.slow
@pytest.mark.parametrize("case", run.CASES)
def test_case_equals_w18(done, case):
    root, _ = done
    d = golden.engineering_differences(os.path.join(root, run.SUB, case), case)
    assert d == [], "\n".join(d)


@pytest.mark.gate_p1a
@pytest.mark.slow
def test_sc1_2056_against_sewergems(done):
    root, info = done
    m = sewergems.compare(os.path.join(root, run.SUB, "SC1-2056"))
    json.dump(dict(sewergems_SC1_2056=m, timing_12_cases=info), open(os.path.join(W19, "docs", "GATE_P1A.json"), "w"), indent=1)
    assert m["pipes_compared"] >= 19078 and m["pc_within_0_1"] == 100.0 and m["over_limit"] == 0
    assert -0.0015 <= m["dv_p05"] and m["dv_p95"] <= 0.0015
    assert abs(m["km_under_model"] - m["km_under_own"]) < 0.05
    print("sewergems", m, "timing", info)
