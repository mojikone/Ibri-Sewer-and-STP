"""The export publishes ONE set of levels, and they are the LEVELLER'S.

Written against the defect this task existed to close, not against the code that closed it.

    s8_export carried its own levels-and-sizes pass, inherited from W11b where there
    genuinely was no stage 6, AND s6_levels published its own inverts for the same
    chambers into W12.gpkg. Two solvers, one question - inheritance row 10, the defect
    class that put seven station counts into circulation in W10.

MEASURED on the 003 run, before the rewire, from the two published files themselves:

    chamber inverts     45,115 of 56,973 differed; 23,941 by more than a metre; worst
                        77.33 m. The stand-in produced an 85.96 m chamber against s6's
                        deepest of 20.23 m.
    laid gradients      29,633 of 56,522 differed
    diameters           1,824 differed
    peak factor         s6 applied Merrimack to all 56,525 reaches; the stand-in HELD
                        PF = 1.0 on 42,655 of them (below the 100-property threshold where
                        G201-p71 prescribes no formula)

Every test below fails if the export starts answering any of those questions a second time.

The five tests, and the bug each one is aimed at:

  1  the published inverts ARE s6's, to the millimetre, matched on the WRITTEN topology
  2  the join is on (US_NODE, DS_NODE) and never on EDGE_UID - s6 numbers reaches from
     E0000001 and s8 from E0000000, so an EDGE_UID join is off by one on every row and
     looks like it worked
  3  every published row says WHICH solver answered for it (LEVELS_BY)
  4  a route s6 did not level is NOT on the reaches layer wearing a made-up gradient
  5  nothing went missing between s4 and the export: levelled + unlevelled = segments
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.published

geopandas = pytest.importorskip("geopandas")
import geopandas as gpd                                              # noqa: E402

import s8_export as EX                                               # noqa: E402


def _need(path: str, what: str):
    if not os.path.exists(path):
        pytest.skip(f"{what} has not been published ({os.path.basename(path)}) - "
                    f"run the pipeline first. A skip is visible; a silent pass is not.")


@pytest.fixture(scope="module")
def pub():
    _need(EX.GPKG_OUT, "the export")
    return gpd.read_file(EX.GPKG_OUT, layer="nodes", ignore_geometry=True), \
        gpd.read_file(EX.GPKG_OUT, layer="reaches", ignore_geometry=True)


@pytest.fixture(scope="module")
def s6():
    _need(EX.GPKG_S6, "s6_levels")
    return gpd.read_file(EX.GPKG_S6, layer="nodes", ignore_geometry=True), \
        gpd.read_file(EX.GPKG_S6, layer="reaches", ignore_geometry=True)


def test_every_published_invert_is_the_levellers_own_number(pub, s6):
    """Not 'close to'. The SAME number, to the millimetre the layer publishes.

    A tolerance here would be the place a second solver hides: 'within 50 mm' passes a
    whole re-solve that happens to land nearby, and the 0.05-vs-0.10 wall allowance that
    failed a blocking cover check on every reach was 50 mm."""
    nd, _r = pub
    n6, _r6 = s6
    lut = pd.Series(pd.to_numeric(n6.INV_M, errors="coerce").values,
                    index=n6.NODE_UID.astype(str).values)
    want = nd.NODE_UID.astype(str).map(lut)
    got = pd.to_numeric(nd.INV_M, errors="coerce")
    both = want.notna() & got.notna()
    off = (want[both] - got[both]).abs() > 0.0015
    print(f"\n    [levels source] {int(both.sum()):,} of {len(nd):,} published chambers "
          f"have an invert in {os.path.basename(EX.GPKG_S6)}; "
          f"{int(off.sum()):,} of those differ")
    assert not off.any(), (
        f"{int(off.sum()):,} published chamber inverts are NOT the ones "
        f"{os.path.basename(EX.GPKG_S6)} holds for the same NODE_UID - worst "
        f"{float((want[both] - got[both]).abs().max()):.3f} m. Two solvers, one question: "
        f"inheritance row 10. Read s6's inverts, do not recompute them.")


def test_the_join_is_on_the_written_topology_not_on_edge_uid(pub, s6):
    """EDGE_UID is a per-file counter, not a shared identity, and the two files disagree
    about where the numbering starts. A join on it is silently off by one on every row.

    This test does not check the export's code path - it checks that the ASSUMPTION behind
    a naive join is false, so nobody re-introduces it believing it is harmless."""
    _nd, r = pub
    _n6, r6 = s6
    if "EDGE_UID" not in r.columns or "EDGE_UID" not in r6.columns:
        pytest.skip("one of the layers has no EDGE_UID")
    key8 = dict(zip(r.EDGE_UID.astype(str),
                    zip(r.US_NODE.astype(str), r.DS_NODE.astype(str))))
    key6 = dict(zip(r6.EDGE_UID.astype(str),
                    zip(r6.US_NODE.astype(str), r6.DS_NODE.astype(str))))
    shared = set(key8) & set(key6)
    if not shared:
        pytest.skip("the two files share no EDGE_UID at all")
    agree = sum(1 for k in shared if key8[k] == key6[k])
    print(f"\n    [edge uid] {len(shared):,} EDGE_UIDs appear in both files; on "
          f"{len(shared) - agree:,} of them the two files mean a DIFFERENT reach")
    assert agree < len(shared), (
        "every shared EDGE_UID happens to name the same reach in both files today. That "
        "makes an EDGE_UID join look correct, and it is not: the id is minted per file "
        "from a row counter. If this ever becomes true, keep joining on "
        "(US_NODE, DS_NODE) anyway - H16, topology is written down.")


def test_every_row_says_which_solver_levelled_it(pub):
    """A file-wide banner is not provenance. s6 answered for 56,521 of 56,696 reaches on
    the 003 run and not for the rest, so the answer differs BY ROW."""
    nd, r = pub
    for name, g in (("nodes", nd), ("reaches", r)):
        assert "LEVELS_BY" in g.columns, (
            f"the published {name} layer has no LEVELS_BY column, so a reader holding one "
            f"chamber cannot tell which solver produced its depth")
        blank = g.LEVELS_BY.astype(str).str.strip().isin(("", "nan", "None"))
        assert not blank.any(), (
            f"{int(blank.sum()):,} rows of {name} carry no levels provenance at all")
    got = sorted(set(r.LEVELS_BY.astype(str)) | set(nd.LEVELS_BY.astype(str)))
    print(f"\n    [provenance] LEVELS_BY holds {got}")
    assert any(EX.S6_TAG in v for v in got), (
        f"nothing on the published layers names {EX.S6_TAG} as its levels source. Either "
        f"s6 never published and the retired stand-in shipped - in which case the run is "
        f"not quotable - or the rewire has been undone.")


def test_a_route_nobody_levelled_is_not_published_as_a_gravity_reach(pub, s6):
    """s6 withdraws a reach when it replaces it with a pumped link. Giving that route the
    retired stand-in's gradient, laid between two of s6's inverts, describes no pipe - and
    it would be counted in the network length, the quantities and the pipe schedule."""
    _nd, r = pub
    _n6, r6 = s6
    have6 = set(zip(r6.US_NODE.astype(str), r6.DS_NODE.astype(str)))
    orphan = [k for k in zip(r.US_NODE.astype(str), r.DS_NODE.astype(str))
              if k not in have6]
    print(f"\n    [unlevelled] {len(orphan):,} of {len(r):,} published reaches have no "
          f"row in {os.path.basename(EX.GPKG_S6)}")
    assert not orphan, (
        f"{len(orphan):,} reaches are published with a gradient and a diameter that "
        f"{os.path.basename(EX.GPKG_S6)} never wrote, e.g. {orphan[:3]}. They belong on "
        f"`reaches_unlevelled` with the reason, not in the network length.")


def test_nothing_went_missing_between_the_chambers_and_the_export(pub):
    """Taking rows OFF a layer is legitimate (inheritance row 4) and losing them is not.
    Every segment s4 minted is either a published gravity reach or a published exception.

    Compared on the WRITTEN topology and not on a row count, because a count cannot tell
    "the export dropped 29 segments" from "s4 has been re-run since this export was built",
    and those two want opposite responses - fix the export, or re-run it."""
    _need(EX.GPKG_CHAMB, "the chamber stage")
    _nd, r = pub
    seg = gpd.read_file(EX.GPKG_CHAMB, layer="segments", ignore_geometry=True)
    import fiona
    have = set(fiona.listlayers(EX.GPKG_OUT))
    unl = (gpd.read_file(EX.GPKG_OUT, layer="reaches_unlevelled", ignore_geometry=True)
           if "reaches_unlevelled" in have else pd.DataFrame())
    k_seg = set(zip(seg.US_NODE.astype(str), seg.DS_NODE.astype(str)))
    k_pub = set(zip(r.US_NODE.astype(str), r.DS_NODE.astype(str)))
    if len(unl):
        k_pub |= set(zip(unl.US_NODE.astype(str), unl.DS_NODE.astype(str)))
    lost, extra = k_seg - k_pub, k_pub - k_seg
    print(f"\n    [ledger] {len(r):,} levelled + {len(unl):,} unlevelled = "
          f"{len(k_pub):,} against {len(k_seg):,} segments from s4; "
          f"{len(lost):,} unpublished, {len(extra):,} published that s4 no longer has")
    if extra:
        pytest.skip(f"the export is STALE - it publishes {len(extra):,} segments the "
                    f"current chamber layer does not have, so s4 has been re-run since. "
                    f"Re-run s8_export.py build; this test cannot judge a mixed pair.")
    assert not lost, (
        f"{len(lost):,} segments are on neither layer, e.g. {sorted(lost)[:3]}. A row a "
        f"pass removes must be published, not dropped - a silent drop is the worst defect "
        f"in this project's history.")


def test_the_stand_in_still_runs_and_still_publishes_nothing():
    """The retired solver is kept ON PURPOSE - it is the only way to have the size of the
    disagreement - so this asserts the two properties that make keeping it safe: it is
    still callable, and its tag is not what the export claims as its levels source."""
    assert hasattr(EX, "design_levels"), (
        "design_levels() has been deleted. It is retired, not removed: `levels_delta` is "
        "the measurement of what the swap changed and it cannot be computed without it.")
    assert hasattr(EX, "read_s6_levels") and hasattr(EX, "levels_delta")
    assert EX.S6_TAG != EX.LEVELS_TAG
    _need(EX.GPKG_OUT, "the export")
    r = gpd.read_file(EX.GPKG_OUT, layer="reaches", ignore_geometry=True)
    stale = r.LEVELS_BY.astype(str).eq(EX.LEVELS_TAG).sum() if "LEVELS_BY" in r else -1
    print(f"\n    [retired] {int(stale):,} published reaches carry the retired tag "
          f"{EX.LEVELS_TAG!r}")
    assert stale == 0, (
        f"{int(stale):,} published reaches were levelled by the retired stand-in. It "
        f"publishes nothing; if s6 has not run, the export is not quotable and says so "
        f"rather than shipping the other answer quietly.")
