"""The comparison itself is tested: W18's own files pass against themselves, and a planted error is caught."""
import os
import pandas as pd
from sewerapp import fixtures
from sewerapp.referee import golden


def golden_case(tmp_path, case="SC1-2056"):
    for rel in ("named/links.csv", "named/stations.csv", "products/quantities.json", f"exports/conduits_{case}a.csv"):
        fixtures.materialize(f"golden/{case}/{rel}", str(tmp_path / rel))
    return str(tmp_path)


def test_golden_against_itself_has_no_differences(tmp_path):
    assert golden.engineering_differences(golden_case(tmp_path), "SC1-2056") == []


def test_planted_errors_are_caught(tmp_path):
    d = golden_case(tmp_path); p = os.path.join(d, "named", "links.csv")
    k = pd.read_csv(p); k.loc[0, "dn_mm"] = 250; k.loc[5, "depth_up_m"] += 0.002; k.to_csv(p, index=False)
    q = os.path.join(d, "exports", "conduits_SC1-2056a.csv"); c = pd.read_csv(q); c.loc[3, "flow_m3d"] *= 1.002; c.to_csv(q, index=False)
    msgs = " ".join(golden.engineering_differences(d, "SC1-2056"))
    assert "size" in msgs and "depth_up_m" in msgs and "flow" in msgs
