import gzip, hashlib, os
import pytest
from sewerapp import fixtures

CASES = [f"{s}-{y}" for s in ("SC1", "SC2", "SC3", "SC4") for y in ("2051", "2056", "2061")]


def test_manifest_matches_every_file():
    man = fixtures.manifest()
    assert len(man["files"]) > 50
    for rel, meta in man["files"].items():
        raw = open(os.path.join(fixtures.FIX, rel), "rb").read()
        if rel.endswith(".gz"): raw = gzip.decompress(raw)
        assert hashlib.sha256(raw).hexdigest() == meta["sha256"], rel


@pytest.mark.parametrize("case", CASES)
def test_every_case_has_its_golden_outputs(case):
    for rel in (f"golden/{case}/named/links.csv", f"golden/{case}/named/stations.csv",
                f"golden/{case}/products/quantities.json", f"golden/{case}/split/cuts_{case}.csv",
                f"golden/{case}/exports/conduits_{case}a.csv"):
        assert os.path.exists(fixtures.path(rel)), rel


def test_read_csv_reads_gz():
    d = fixtures.read_csv("inputs/conduits_network.csv")
    assert (d.active == True).sum() == 19083
