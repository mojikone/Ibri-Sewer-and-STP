"""Adversarial review of `w12.connectivity` - one test per defect found, 2026-09-06.

These are NOT a second copy of `test_connectivity.py`. Every test here was written by
building a case the module's own suite does not build, watching it produce a wrong answer,
and then fixing the module. They exist so the same answer cannot come back.

The four that were live defects, in the order they cost most:

  1. A BORE OF 0 WAS PUBLISHED AS AN ENGINEERING VERDICT. The vectorised check decided
     "is the bore missing?" by testing `isfinite(bore)`, and 0 and negative bores are
     finite. `arrival_allowance()` returns NaN for them, the row fell through to the LEVEL
     branch and came out as `route loses the fall` with ALLOW_M = NaN and CONN_NEED = 0.0
     - a fabricated verdict standing in for a missing input, and a verdict whose CONN_NEED
     is not the remedy it claims to be. On a 4,000-row fuzz, 735 rows (18 %) were wrong.
     DN = 0 is not hypothetical: NAMA's own asset GIS carries N_DIAMETER = 0 on every
     built record. The scalar `check_one()` had it right all along, so this was also the
     scalar/vector drift the suite claims to guard - the equality test only ever passes
     bores of 200 / 315 / 400 / 900.
  2. A LABELLED SERIES WAS RE-ATTACHED BY POSITION. `np.asarray()` on a pandas Series
     throws its index away, so an invert lookup handed in keyed by chamber - the shape
     `dn_at_node()` itself returns - silently gave every plot another plot's level.
  3. `recheck()` COMPARED ONLY THE INTERSECTION. Load units present before and gone after
     were dropped in silence by the one function written to stop flags being carried
     silently.
  4. A DUPLICATED NODE_UID SILENTLY TOOK THE FIRST INVERT. `recheck()` refuses a duplicated
     CONN_ID for exactly this reason; the chamber key did not.

Plus two smaller ones: a fractional bore was truncated to the next integer down (DN 350.9
crossed the G203-p27 Table 10 threshold the wrong way), and an empty result lost its basis
so `report()` printed "basis unknown" beside "nan %".
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from w12 import connectivity as CN
from w12.criteria import DEFAULT as C

DN = 200


@pytest.fixture
def hcc():
    return CN.basis_hcc(C)


def _one(grd=100.0, inv=97.0, route=10.0, dn=DN, **kw):
    return pd.DataFrame({"CONN_ID": ["C0"], "OUT_NODE": ["N0"], "GRD_PLOT": [grd],
                         "LEN_M": [route], "DN": [dn], **kw})


# ======================================================================================
# DEFECT 1 - a bore of zero is a MISSING INPUT, never a verdict
# ======================================================================================

@pytest.mark.parametrize("bad_dn", [0, 0.0, -200, -1])
def test_a_non_positive_bore_is_a_missing_input_not_a_level_verdict(hcc, bad_dn):
    """The bore is finite and unusable. Before the fix this came out as `route loses the
    fall` - an engineering verdict, on a row where no arrival level could be computed at
    all. Merging "cannot be served" with "we do not know" is the defect this module's own
    vocabulary exists to prevent, and CAN_DRAIN going blank in W11b is what it looks like
    when it ships."""
    res = CN.check_connections(_one(dn=bad_dn), chamber_inv=np.array([97.0]), crit=C,
                               basis=hcc)
    assert res.CONN_WHY.iloc[0] == CN.WHY_NO_DN, res.CONN_WHY.iloc[0]
    assert res.CONN_WHY.iloc[0] not in CN.WHY_IS_A_VERDICT
    assert int(res.CAN_CONN.iloc[0]) == 0
    assert float(res.CONN_NEED.iloc[0]) == 0.0, "an unknown is not a depth"


def test_a_non_positive_bore_is_counted_as_untestable_not_as_a_finding(hcc):
    """summary() must not report a missing bore under n_verdict_fail. "5,521 plots cannot
    be served" and "5,521 plots we could not test" are different sentences to send a
    client."""
    conn = pd.DataFrame({"CONN_ID": [f"C{i}" for i in range(4)],
                         "OUT_NODE": ["N0"] * 4, "GRD_PLOT": [100.0] * 4,
                         "LEN_M": [10.0] * 4, "DN": [200, 0, -200, 200]})
    res = CN.check_connections(conn, chamber_inv=np.array([99.5, 99.5, 99.5, 90.0]),
                               crit=C, basis=hcc)
    s = CN.summary(res)
    assert s["n_cannot_run"] == 2, s["by_reason"]
    assert s["n_verdict_fail"] == 1, s["by_reason"]
    assert s["n_can"] == 1, s


def test_the_two_implementations_agree_on_HOSTILE_input_not_only_on_tidy_input(hcc):
    """The suite's row-for-row equality test uses bores of 200 / 315 / 400 / 900 and
    finite everything. Two implementations of one rule only stay one rule if the test that
    compares them is allowed to feed them the values the real data actually holds: zero
    bores, negative bores, NaN, negative route lengths, chambers above the ground."""
    rng = np.random.default_rng(20260906)
    n = 1500
    grd = np.where(rng.random(n) < 0.06, np.nan, 100 + rng.normal(0, 5, n))
    inv = np.where(rng.random(n) < 0.06, np.nan, grd - rng.uniform(-2, 6, n))
    rte = np.where(rng.random(n) < 0.06, np.nan, rng.uniform(-10, 150, n))
    dns = rng.choice([200.0, 315.0, 900.0, 0.0, -200.0, np.nan], n)
    conn = pd.DataFrame({"CONN_ID": [f"C{i:05d}" for i in range(n)],
                         "OUT_NODE": ["N0"] * n, "GRD_PLOT": grd, "LEN_M": rte,
                         "DN": dns})
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    for i in range(n):
        one = CN.check_one(grd[i], inv[i], rte[i],
                           None if not np.isfinite(dns[i]) else dns[i],
                           basis=hcc, crit=C)
        assert res.CONN_WHY.iloc[i] == one.why, (i, dns[i])
        assert int(res.CAN_CONN.iloc[i]) == one.can_conn, i
        assert abs(float(res.CONN_NEED.iloc[i]) - round(one.need_m, 3)) < 2e-3, i


def test_every_verdict_failure_carries_a_need_that_is_actually_the_remedy(hcc):
    """The module's headline claim. It only holds if no row can reach a verdict without a
    computable arrival level - which is what defect 1 broke: 735 rows in a 4,000-row fuzz
    were verdict failures with CONN_NEED = 0.0 and no allowance at all."""
    rng = np.random.default_rng(11)
    n = 600
    grd = 100 + rng.normal(0, 4, n)
    inv = grd - rng.uniform(-1, 5, n)
    conn = pd.DataFrame({"CONN_ID": [f"C{i:04d}" for i in range(n)],
                         "OUT_NODE": ["N0"] * n, "GRD_PLOT": grd,
                         "LEN_M": rng.uniform(0, 130, n),
                         "DN": rng.choice([200.0, 400.0, 0.0, np.nan], n)})
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    verdict = res.CONN_WHY.isin(CN.WHY_IS_A_VERDICT)
    assert verdict.sum() > 30
    assert (res.loc[verdict, "CONN_NEED"] > 0).all(), "a verdict with no size is not a flag"
    assert res.loc[verdict, "ALLOW_M"].notna().all(), "a verdict with no arrival level"
    # and lowering by exactly that much connects the plot
    for i in np.flatnonzero(verdict.to_numpy())[:25]:
        need = float(res.CONN_NEED.iloc[i])
        assert CN.check_one(grd[i], inv[i] - need, conn.LEN_M.iloc[i], conn.DN.iloc[i],
                            basis=hcc, crit=C).can_conn == 1, i


# ======================================================================================
# DEFECT 2 - a labelled Series is aligned or refused, never re-ordered in silence
# ======================================================================================

def test_a_series_whose_index_is_not_the_frames_is_refused_not_reordered(hcc):
    """`dn_at_node()` returns a Series keyed by NODE_UID. Handing that straight back as
    `dn=` is the obvious caller mistake, and before the fix it attached one chamber's bore
    to another chamber's plot with nothing on the deliverable to show for it."""
    conn = pd.DataFrame({"CONN_ID": ["C0", "C1"], "OUT_NODE": ["NA", "NB"],
                         "GRD_PLOT": [100.0, 100.0], "LEN_M": [10.0, 10.0],
                         "DN": [200, 200]}, index=[7, 3])
    inv = pd.Series({"NB": 90.0, "NA": 99.5})     # a lookup, in its own order
    with pytest.raises(CN.ConnectivityError, match="index does not match"):
        CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)


def test_a_series_that_IS_aligned_is_used_by_label(hcc):
    conn = pd.DataFrame({"CONN_ID": ["C0", "C1"], "OUT_NODE": ["NA", "NB"],
                         "GRD_PLOT": [100.0, 100.0], "LEN_M": [0.0, 0.0],
                         "DN": [200, 200]}, index=[7, 3])
    inv = pd.Series([99.5, 90.0], index=[7, 3])
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    allow = CN.arrival_allowance(200, "flow_depth", C)
    assert abs(float(res.REQ_INV_M.iloc[0]) - (99.5 + allow)) < 1e-3
    assert abs(float(res.REQ_INV_M.iloc[1]) - (90.0 + allow)) < 1e-3


def test_a_wrong_length_override_is_refused(hcc):
    conn = pd.DataFrame({"CONN_ID": ["C0", "C1"], "OUT_NODE": ["N0", "N0"],
                         "GRD_PLOT": [100.0, 100.0], "LEN_M": [10.0, 10.0],
                         "DN": [200, 200]})
    with pytest.raises(CN.ConnectivityError, match="against 2 connections rows"):
        CN.check_connections(conn, chamber_inv=np.array([97.0]), crit=C, basis=hcc)


def test_a_scalar_override_still_broadcasts(hcc):
    """The convenience that must survive the fix - one ground level for a synthetic case."""
    conn = pd.DataFrame({"CONN_ID": ["C0", "C1"], "OUT_NODE": ["N0", "N0"],
                         "LEN_M": [0.0, 0.0], "DN": [200, 200]})
    res = CN.check_connections(conn, chamber_inv=np.array([90.0, 90.0]), grd_plot=100.0,
                               crit=C, basis=hcc)
    assert (res.OUT_INV_M == 98.8).all()


# ======================================================================================
# DEFECT 3 - recheck() names what vanished
# ======================================================================================

def test_recheck_names_the_load_units_that_vanished_between_the_two_runs():
    """Inheritance row 12, committed by the function written for row 4. Comparing only the
    intersection and publishing "2 failing -> 1 failing" while three load units disappeared
    is a silent drop of exactly the kind that cost W10 1,233 m3/d."""
    before = pd.DataFrame({"CONN_ID": [f"C{i}" for i in range(5)],
                           "CAN_CONN": [0, 0, 0, 1, 1],
                           "CONN_NEED": [1.0, 2.0, 0.5, 0.0, 0.0]})
    after = pd.DataFrame({"CONN_ID": ["C0", "C1", "C9"],
                          "CAN_CONN": [1, 0, 0], "CONN_NEED": [0.0, 2.0, 0.3]})
    rc = CN.recheck(before, after)
    assert rc["n_only_before"] == 3
    assert set(rc["only_before_ids"]) == {"C2", "C3", "C4"}
    assert rc["n_only_after"] == 1 and rc["only_after_ids"] == ["C9"]
    assert "GONE after" in rc["line"], rc["line"]
    assert rc["n_before"] == 5 and rc["n_after"] == 3


def test_recheck_says_nothing_extra_when_the_two_runs_hold_the_same_units():
    before = pd.DataFrame({"CONN_ID": ["A", "B"], "CAN_CONN": [0, 0],
                           "CONN_NEED": [1.0, 1.0]})
    after = pd.DataFrame({"CONN_ID": ["A", "B"], "CAN_CONN": [1, 0],
                          "CONN_NEED": [0.0, 1.0]})
    rc = CN.recheck(before, after)
    assert rc["n_only_before"] == 0 and rc["n_only_after"] == 0
    assert "GONE after" not in rc["line"]


def test_depth_recovered_does_not_count_an_input_that_was_lost():
    """A row that was `needs 2.00 m` and is now `chamber bore unknown` has recovered
    nothing - its CONN_NEED went to zero because an unknown is not a depth. Counting that
    as 2 m of recovered excavation is a stage congratulating itself for losing data."""
    before = pd.DataFrame({"CONN_ID": ["A", "B"], "CAN_CONN": [0, 0],
                           "CONN_NEED": [2.0, 1.0],
                           "CONN_WHY": [CN.WHY_ROUTE, CN.WHY_ROUTE]})
    after = pd.DataFrame({"CONN_ID": ["A", "B"], "CAN_CONN": [0, 1],
                          "CONN_NEED": [0.0, 0.0],
                          "CONN_WHY": [CN.WHY_NO_DN, ""]})
    rc = CN.recheck(before, after)
    assert rc["depth_recovered_qualified"] is True
    assert abs(rc["depth_recovered_m"] - 1.0) < 1e-9, rc["depth_recovered_m"]


def test_a_flag_cleared_because_an_input_arrived_is_counted_apart():
    """B was never a verdict - it was untestable. It "passing" now is an input arriving,
    not a later pass removing a flag, and row 4 is about the second thing."""
    before = pd.DataFrame({"CONN_ID": ["A", "B"], "CAN_CONN": [0, 0],
                           "CONN_NEED": [2.0, 0.0],
                           "CONN_WHY": [CN.WHY_ROUTE, CN.WHY_NO_INV]})
    after = pd.DataFrame({"CONN_ID": ["A", "B"], "CAN_CONN": [1, 1],
                          "CONN_NEED": [0.0, 0.0], "CONN_WHY": ["", ""]})
    rc = CN.recheck(before, after)
    assert rc["n_cleared"] == 2
    assert rc["n_became_testable"] == 1


def test_recheck_without_conn_why_says_its_depth_figure_is_unqualified():
    before = pd.DataFrame({"CONN_ID": ["A"], "CAN_CONN": [0], "CONN_NEED": [2.0]})
    after = pd.DataFrame({"CONN_ID": ["A"], "CAN_CONN": [0], "CONN_NEED": [0.0]})
    rc = CN.recheck(before, after)
    assert rc["depth_recovered_qualified"] is False


# ======================================================================================
# DEFECT 4 - a duplicated chamber key
# ======================================================================================

def test_two_chambers_with_one_uid_and_two_inverts_raise(hcc):
    """`recheck()` already refuses a duplicated CONN_ID because a duplicate makes its own
    question unanswerable. The chamber key deserves the same: keeping whichever row came
    first is a silent choice between a 99.5 and a 90.0 invert."""
    nodes = pd.DataFrame({"NODE_UID": ["N0", "N0"], "INV_M": [99.5, 90.0]})
    with pytest.raises(CN.ConnectivityError, match="DIFFERENT INV_M"):
        CN.check_connections(_one(), nodes, crit=C, basis=hcc, dn=np.array([200.0]))


def test_an_identical_duplicate_is_harmless_and_is_collapsed(hcc):
    nodes = pd.DataFrame({"NODE_UID": ["N0", "N0"], "INV_M": [99.5, 99.5]})
    res = CN.check_connections(_one(), nodes, crit=C, basis=hcc, dn=np.array([200.0]))
    assert len(res) == 1


# ======================================================================================
# DEFECT 5 - a fractional bore is not truncated to the next size down
# ======================================================================================

def test_a_fractional_bore_is_sized_as_itself_not_as_the_next_size_down():
    """G203-p27 Table 10 splits at 350 mm. Truncating DN 350.9 to 350 moved it across the
    threshold and gave it 0.65 D instead of 0.50 D - a 60 % larger allowance, from a cast
    that existed only to key a cache."""
    assert CN.arrival_allowance(350.9, "flow_depth", C) < \
        CN.arrival_allowance(350.0, "flow_depth", C)
    a = CN.arrival_allowance(315.4, "flow_depth", C)
    assert a > CN.arrival_allowance(315.0, "flow_depth", C)
    arr = CN.arrival_allowance(np.array([315.0, 315.4, 350.0, 350.9]), "flow_depth", C)
    assert len(set(np.round(arr, 6))) == 4, arr


# ======================================================================================
# DEFECT 6 - an empty answer keeps its basis and does not read as a broken run
# ======================================================================================

def test_an_empty_result_keeps_its_basis_and_does_not_print_nan_percent(hcc):
    conn = _one().iloc[:0]
    res = CN.check_connections(conn, chamber_inv=np.array([]), crit=C, basis=hcc)
    assert res.attrs.get("basis") is hcc
    assert CN.summary(res)["basis"] == "BASIS_HCC"
    txt = CN.report(res, C)
    assert "nan" not in txt.lower()
    assert "No plots were passed" in txt


# ======================================================================================
# THE ENGINEER'S OWN ADVERSARIAL CASES - built here, not inherited
# ======================================================================================

def test_the_steep_run_connects_and_the_surplus_is_flagged_for_a_drop(hcc):
    """A plot 8 m above its chamber over a 60 m route. It connects easily; the surplus
    beyond the G203-p18 Table 5 10 % maximum is a drop, and concept rule 1 says a drop is
    flagged with a reason rather than silently absorbed."""
    res = CN.check_connections(_one(grd=100.0, route=60.0), chamber_inv=np.array([92.0]),
                               crit=C, basis=hcc)
    assert int(res.CAN_CONN.iloc[0]) == 1
    assert int(res.CONN_STEEP.iloc[0]) == 1
    assert float(res.S_AVL_PCT.iloc[0]) > 10.0


def test_the_flat_run_fails_on_the_route_and_says_so(hcc):
    """Dead-flat ground, a 3.0 m deep chamber and a 200 m route. The plot clears the
    chamber on a level comparison and cannot reach it: 2.00 m of the 1.80 m it has is
    spent on the way. This is failure mode 3 at the scale it actually bites."""
    res = CN.check_connections(_one(grd=100.0, route=200.0), chamber_inv=np.array([97.0]),
                               crit=C, basis=hcc)
    assert res.CONN_WHY.iloc[0] == CN.WHY_ROUTE
    assert float(res.OUT_INV_M.iloc[0]) > float(res.REQ_INV_M.iloc[0])
    assert abs(float(res.FALL_M.iloc[0]) - 2.0) < 1e-6
    assert int(res.CONN_LONG.iloc[0]) == 1


def test_the_plot_on_a_knoll_connects_and_the_plot_in_the_hollow_does_not(hcc):
    """Same chamber, same route: 4 m of relief between the two plots is the whole answer,
    and the module must not flatten it."""
    conn = pd.DataFrame({"CONN_ID": ["knoll", "hollow"], "OUT_NODE": ["N0", "N0"],
                         "GRD_PLOT": [102.0, 98.0], "LEN_M": [40.0, 40.0],
                         "DN": [200, 200]})
    res = CN.check_connections(conn, chamber_inv=np.array([99.0, 99.0]), crit=C,
                               basis=hcc).set_index("CONN_ID")
    assert int(res.loc["knoll", "CAN_CONN"]) == 1
    assert int(res.loc["hollow", "CAN_CONN"]) == 0
    assert res.loc["hollow", "CONN_WHY"] == CN.WHY_LEVEL


def test_the_answer_is_monotone_in_the_sewer_depth(hcc):
    """A property no single hand-built case proves: lowering a sewer can never disconnect
    a plot, and raising it can never connect one. If this ever fails, the check has picked
    up a term that is not a level."""
    rng = np.random.default_rng(5)
    n = 400
    grd = 100 + rng.normal(0, 4, n)
    inv = grd - rng.uniform(0, 5, n)
    conn = pd.DataFrame({"CONN_ID": [f"C{i:04d}" for i in range(n)],
                         "OUT_NODE": ["N0"] * n, "GRD_PLOT": grd,
                         "LEN_M": rng.uniform(0, 120, n),
                         "DN": rng.choice([200, 400, 900], n)})
    base = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    for d in (0.25, 1.0, 3.0):
        lower = CN.check_connections(conn, chamber_inv=inv - d, crit=C, basis=hcc)
        higher = CN.check_connections(conn, chamber_inv=inv + d, crit=C, basis=hcc)
        assert (lower.CAN_CONN >= base.CAN_CONN).all(), d
        assert (higher.CAN_CONN <= base.CAN_CONN).all(), d
        assert (lower.CONN_NEED <= base.CONN_NEED + 1e-9).all(), d


def test_the_three_bases_are_ordered_on_every_row_not_only_in_total(hcc):
    """sensitivity() reports totals. A total can hide two rows moving in opposite
    directions, which would mean the "band" is not a band."""
    rng = np.random.default_rng(9)
    n = 500
    grd = 100 + rng.normal(0, 4, n)
    inv = grd - rng.uniform(0, 5, n)
    conn = pd.DataFrame({"CONN_ID": [f"C{i:04d}" for i in range(n)],
                         "OUT_NODE": ["N0"] * n, "GRD_PLOT": grd,
                         "LEN_M": rng.uniform(0, 120, n), "DN": [200] * n})
    hc = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=CN.basis_hcc(C))
    sh = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=CN.basis_shallow(C))
    st = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=CN.basis_strict(C))
    assert (sh.CAN_CONN >= hc.CAN_CONN).all(), "shallow must be generous on EVERY row"
    assert (st.CAN_CONN <= hc.CAN_CONN).all(), "strict must be harsh on EVERY row"
