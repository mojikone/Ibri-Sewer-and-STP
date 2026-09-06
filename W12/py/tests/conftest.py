"""W12 test suite - shared fixtures, path setup and markers.

WHY THIS SUITE EXISTS. There were zero test files in this project before 2026-09-03 and
eight confident numbers were retracted in three days. Every one of the five defects the
suite opens with was a CLASS of bug, not a one-off, and each cost hours:

    tests/test_constants.py    TWO CONSTANTS FOR ONE QUANTITY.  A wall/bedding allowance
                               was 0.10 in the auditor and 0.05 in the criteria, so every
                               reach failed a BLOCKING cover check by exactly 50 mm.
    tests/test_nodata.py       NO-DATA TREATED AS SAFE.  A flood grid's no-data is -9999,
                               which IS finite, so a finiteness guard passed it as dry
                               ground; it came back a second time through a probe that
                               reported an unfound riverbank as an 800 m channel.
    tests/test_columns.py      A FABRICATED COLUMN.  A crossing angle was published as 90
                               degrees on all 3,290 rows and called a declaration; the
                               measured minimum was 0.00 deg.
                               A COLUMN THAT DISAGREES WITH ITS OWN GEOMETRY.  A length
                               field differed from the shape it described by up to 87 m.
    tests/test_deadcode.py     DEAD CODE THAT COST 26 MINUTES - a set rebuilt inside a
                               loop to fill a variable nobody read.

Then the physics (tests/test_physics.py), which has textbook answers that can be checked
by hand and which nothing else in the pipeline would catch, and then the graph invariants
(tests/test_invariants.py), which are the properties every published network must have
whatever the design decides.

HOW IT IS ORGANISED. Three kinds of test, and they are marked so a cold start can run the
cheap ones first:

    (unmarked)   pure logic and physics.  No files, no data, milliseconds.
    @pytest.mark.published   reads the published GeoPackages under W12/shp/.  SKIPS, with
                             a message naming the missing file, when a stage has not run.
                             A skip is visible; a silent pass is not.
    @pytest.mark.slow        runtime-bounded smoke tests that import or exercise a stage.

NO TEST HERE INVENTS A DESIGN NUMBER.  Every threshold is either read from `w12.criteria`
(which cites its guideline page), read from `w12.contract` (a structural tolerance that
says so), or derived from first principles inside the test - in which case the derivation
is written out in the test body and the source is named.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pytest

# --- paths ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).resolve().parent
PY_DIR = TESTS_DIR.parent                    # .../W12/py
W12_ROOT = PY_DIR.parent                    # .../W12
REPO_ROOT = W12_ROOT.parent                 # .../Hydraulic/Claude
SHP_DIR = W12_ROOT / "shp"
RUN_DIR = W12_ROOT / "run"

# `w12` and the stage modules both live in W12/py. Inserted rather than appended so a
# same-named package elsewhere on the path cannot shadow ours.
if str(PY_DIR) not in sys.path:
    sys.path.insert(0, str(PY_DIR))


# --- markers -------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "published: reads the published GeoPackages; skips if a stage has not run")
    config.addinivalue_line(
        "markers", "slow: imports or exercises a stage; runtime-bounded")
    config.addinivalue_line(
        "markers", "audit: a check of the PUBLISHED DESIGN against the philosophy's hard "
                   "constraints, not of the code. `run_all.py` runs these last and reports "
                   "them as an audit table - philosophy sec 8: a breach of a 'shall' or of "
                   "a settled project rule is BLOCKING, and a check that cannot run is a "
                   "failure, not a blank.")


# --- the published files -------------------------------------------------------------
# One entry per stage. The name is what a skip message prints, so it says which stage to
# run, not which file is missing.
GPKGS: Dict[str, str] = {
    "roads": "W12_roads.gpkg",         # s1_roads.py
    "orient": "W12_orient.gpkg",       # s2_orient.py build
    "hier": "W12_hier.gpkg",           # s3_hierarchy.py build
    "chambers": "W12_chambers.gpkg",   # s4_chambers.py
    "flows": "W12_flows.gpkg",         # s5_flows.py
    "pumps": "W12_pumps.gpkg",         # s7_pumps.py
    "streams": "W12_streams.gpkg",     # w12.streams
    # ADDED 2026-09-06. THESE TWO WERE MISSING, AND THEY ARE THE DESIGN AND THE DELIVERABLE.
    # Without them the whole suite was blind to stages 6 and 8: the readiness probe reported
    # 29 of 34 audit checks "waiting on stage 6" AFTER stage 6 had run and published, because
    # no fixture could open what it published. That is not a check failing - it is 29 checks
    # never being asked, while the run produced a full set of drawings. Philosophy sec 8:
    # a check that cannot run is a FAILURE, not a blank.
    "w12": "W12.gpkg",                 # s6_levels.py - THE DESIGN: nodes, reaches, crossings
    "levels": "W12_levels.gpkg",       # s6_levels.py - its own working layers
    "export": "W12_export.gpkg",       # s8_export.py - THE DELIVERABLE
}

STAGE_FOR: Dict[str, str] = {
    "roads": "s1_roads.py", "orient": "s2_orient.py build", "hier": "s3_hierarchy.py build",
    "chambers": "s4_chambers.py", "flows": "s5_flows.py", "pumps": "s7_pumps.py",
    "streams": "python -m w12.streams",
    "w12": "s6_levels.py", "levels": "s6_levels.py", "export": "s8_export.py",
}


def gpkg_path(key: str) -> Path:
    return SHP_DIR / GPKGS[key]


def require_gpkg(key: str) -> Path:
    p = gpkg_path(key)
    if not p.is_file():
        pytest.skip(f"{p.name} not published - run {STAGE_FOR[key]} first")
    return p


_LAYER_CACHE: Dict[str, object] = {}


def layer(key: str, name: str):
    """Read one published layer, cached for the session.

    Cached because the same layer is read by several checks and `chambers` alone is 56,935
    rows; re-reading it per test turns a 20-second suite into a two-minute one.
    """
    import geopandas as gpd
    import fiona

    p = require_gpkg(key)
    ck = f"{key}:{name}"
    if ck not in _LAYER_CACHE:
        names = fiona.listlayers(str(p))
        if name not in names:
            pytest.skip(f"{p.name} has no layer '{name}' - run {STAGE_FOR[key]} again "
                        f"(it holds {len(names)} layers)")
        _LAYER_CACHE[ck] = gpd.read_file(str(p), layer=name)
    return _LAYER_CACHE[ck]


def layer_names(key: str) -> List[str]:
    import fiona
    return list(fiona.listlayers(str(require_gpkg(key))))


# --- fixtures ------------------------------------------------------------------------
@pytest.fixture(scope="session")
def crit():
    from w12.criteria import DEFAULT
    return DEFAULT


@pytest.fixture(scope="session")
def contract():
    import w12.contract as c
    return c


@pytest.fixture(scope="session")
def hydra():
    import w12.hydra as h
    return h


@pytest.fixture(scope="session")
def reaches():
    return layer("hier", "reaches")


@pytest.fixture(scope="session")
def hier_nodes():
    return layer("hier", "nodes")


@pytest.fixture(scope="session")
def flow_arcs():
    return layer("flows", "arcs")


@pytest.fixture(scope="session")
def flow_nodes():
    return layer("flows", "nodes")


@pytest.fixture(scope="session")
def chambers():
    return layer("chambers", "chambers")


@pytest.fixture(scope="session")
def segments():
    return layer("chambers", "segments")


@pytest.fixture(scope="session")
def connections():
    return layer("chambers", "connections")


@pytest.fixture(scope="session")
def stations():
    return layer("pumps", "stations")


@pytest.fixture(scope="session")
def rising_mains():
    return layer("pumps", "rising_mains")


@pytest.fixture(scope="session")
def corridors():
    return layer("roads", "corridors")


# --- a runtime bound that reports rather than only failing ----------------------------
class Budget:
    """A wall-clock bound with the measured time printed either way.

    A smoke test whose only output is pass/fail hides a regression that is still inside
    the bound. The 26-minute defect - a set rebuilt inside a loop to fill a variable
    nobody read - was inside every bound anyone had written down, because nobody had
    written one down.
    """

    def __init__(self, label: str, seconds: float):
        self.label, self.seconds = label, float(seconds)

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.dt = time.perf_counter() - self.t0
        if exc[0] is None:
            print(f"\n    [budget] {self.label}: {self.dt:.2f} s of {self.seconds:.0f} s "
                  f"({self.dt / self.seconds * 100:.0f} % used)")
            assert self.dt <= self.seconds, (
                f"{self.label} took {self.dt:.1f} s against a bound of {self.seconds:.0f} s. "
                "Either the work grew or something is being rebuilt that need not be. "
                "Do not raise the bound without finding out which.")
        return False


def approx_series_max_abs(a, b) -> float:
    """max |a - b| over two aligned pandas Series, NaN-safe."""
    import numpy as np
    d = (a.astype(float) - b.astype(float)).abs()
    d = d[np.isfinite(d)]
    return float(d.max()) if len(d) else 0.0
