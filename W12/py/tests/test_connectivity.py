"""THE PLOT CONNECTABILITY CHECK - `w12.connectivity`.

WHAT THESE TESTS ARE FOR. The naive connectability test - ground level at the plot centroid
against the sewer invert at the nearest perpendicular point on a pipe - is wrong three ways,
and the engineer said so in one sentence on 2026-09-05:

    "of course a plot will connect to the network under ground. so be careful not just
     compare the ground level at plot with the pipe level normal to plot's elevation
     normal to plot's centroid."

Every mode is optimistic, so the naive test PASSES plots that in fact cannot connect:

    1. it starts at GROUND, where the real connection starts at an invert below it
    2. it aims at the nearest point on a PIPE, where the real one runs to a CHAMBER
    3. it spends no fall, where the real one loses route length x its own minimum gradient

The first three test classes below build one plot for each mode and assert that
`naive_can_connect()` says yes where `check_one()` says no. That is the whole point of the
module and it is the whole point of this file.

THE HISTORY THIS CLOSES. W11b published `DRAIN_SHALLOW` on 90.9 % of connections - a bound
at MINIMUM COVER, which is not the question - and recorded its real test, `CAN_DRAIN`, as
"cannot run - no designed invert exists at stage 4". Philosophy sec 8 and inheritance row 2
make a check that cannot run a FAILURE, not a blank. W11a ran a version that COULD run and
rejected 5,715 plots for nothing, because it tested against a seeded sewer depth rather
than a designed one. So there are two ways to get this wrong and both have been taken:
refuse to answer, or answer from an invented input.

NO TEST HERE INVENTS A DESIGN NUMBER. Every level is either read from `w12.criteria` (which
cites its guideline page) or is a ground/invert level chosen by hand for a synthetic plot,
in which case the arithmetic is written out in the test body so it can be followed with a
calculator.
"""
from __future__ import annotations

import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from conftest import PY_DIR

from w12 import connectivity as CN
from w12.criteria import DEFAULT as C
from w12.criteria import replace


# The one bore used through the level tests. DN200 is G203-p22 Table 6's minimum for a
# lateral or a main, so it is the pipe a house connection actually meets, and its arrival
# allowance is dod_limit x internal bore = 0.65 x 0.18824 = 0.12235 m (G203-p27 Table 10).
DN = C.DN_MIN_LATERAL
ALLOW = C.dod_limit(DN) * C.internal_diameter(DN)


@pytest.fixture(scope="module")
def hcc():
    return CN.basis_hcc(C)


# ======================================================================================
# MODE 1 - THE CONNECTION LEAVES BELOW GROUND, NOT AT IT
# ======================================================================================

def test_mode_1_a_plot_that_clears_the_sewer_at_ground_does_not_clear_it_at_its_outlet(hcc):
    """Ground 100.00. Chamber invert 99.20, so the connection must arrive at
    99.20 + 0.122 = 99.322. Route 0 m, so no fall is lost and mode 3 plays no part.

        naive:  100.00 (GROUND)          >  99.20   ->  yes
        real:   100.00 - 1.20 = 98.80    <  99.322  ->  no, by 0.522 m

    The 1.20 m is the shallowest house connection chamber the guideline states, G203-p19
    sec 3.4 ("ranges between 1.2 m and 2.0 m"). The whole difference between the two
    answers is that one of them remembers the connection is a pipe."""
    assert CN.naive_can_connect(100.00, 99.20)
    r = CN.check_one(100.00, 99.20, 0.0, DN, basis=hcc, crit=C)
    assert r.can_conn == 0
    assert r.why == CN.WHY_LEVEL
    assert abs(r.outlet_inv - (100.00 - C.HCC_DEPTH_MIN)) < 1e-9
    assert abs(r.required_inv - (99.20 + ALLOW)) < 1e-9
    assert abs(r.need_m - 0.522) < 5e-4, r.need_m


def test_mode_1_the_outlet_depth_is_the_whole_of_the_difference(hcc):
    """Same plot, moved down by exactly the outlet depth: it now passes. Proves the mode 1
    failure is caused by the outlet depth and by nothing else in the calculation."""
    r = CN.check_one(100.00 + C.HCC_DEPTH_MIN, 99.20, 0.0, DN, basis=hcc, crit=C)
    assert r.can_conn == 1 and r.why == "" and r.need_m == 0.0


def test_a_basis_may_not_leave_the_plot_shallower_than_the_guideline_allows(hcc):
    """G203-p19 sec 3.5 requires 600 mm of cover on a property connection and G203-p22
    Table 6 makes the pipe OD160, so 0.76 m is the shallowest legal outlet. A basis that
    leaves the plot at ground level - the naive test dressed as a parameter - is refused."""
    with pytest.raises(CN.ConnectivityError, match="shallower than"):
        CN._check_basis(CN.Basis(**{**hcc.__dict__, "outlet_depth_m": 0.0}), C)
    floor = C.PCS_MIN_COVER + C.outside_diameter(C.DN_TERTIARY)
    ok = CN.basis_shallow(C)
    assert abs(ok.outlet_depth_m - floor) < 1e-12


# ======================================================================================
# MODE 2 - IT RUNS TO A CHAMBER, NOT TO THE NEAREST POINT ON A PIPE
# ======================================================================================

def test_mode_2_the_nearest_point_on_the_pipe_connects_and_the_chamber_does_not(hcc):
    """Ground 100.00. The nearest point on the sewer is 5 m away at invert 97.80. The
    CHAMBER the connection must actually run to is 55 m away, UPSTREAM, at invert 98.30 -
    the sewer rises 0.50 m over the 50 m between them, about 1 %, which is an ordinary
    lateral gradient.

        against the nearest point:  98.80 - 0.05 = 98.75  >  97.80 + 0.122  ->  yes
        against the chamber:        98.80 - 0.55 = 98.25  <  98.30 + 0.122  ->  no

    Both halves of the difference are real and a perpendicular-distance test sees neither:
    the route is 50 m longer AND the invert is 0.50 m higher."""
    assert CN.naive_can_connect(100.00, 97.80)
    near = CN.check_one(100.00, 97.80, 5.0, DN, basis=hcc, crit=C)
    real = CN.check_one(100.00, 98.30, 55.0, DN, basis=hcc, crit=C)
    assert near.can_conn == 1, near
    assert real.can_conn == 0, real
    assert real.why == CN.WHY_ROUTE
    assert abs(real.need_m - 0.172) < 5e-4, real.need_m


def test_mode_2_the_module_refuses_to_run_without_a_chamber(hcc):
    """Concept rule 5 is that the connection runs TO A CHAMBER. A frame with no OUT_NODE
    cannot express that, so the check refuses rather than falling back to the nearest
    point - which is the naive test, arrived at by politeness."""
    conn = pd.DataFrame({"CONN_ID": ["C1"], "GRD_PLOT": [100.0], "LEN_M": [20.0],
                         "DN": [DN]})
    with pytest.raises(CN.ConnectivityError, match="no OUT_NODE"):
        CN.check_connections(conn, chamber_inv=np.array([98.0]), crit=C, basis=hcc)


# ======================================================================================
# MODE 3 - IT LOSES FALL OVER ITS OWN ROUTE LENGTH
# ======================================================================================

def test_mode_3_a_plot_that_clears_the_chamber_spends_the_clearance_on_the_way(hcc):
    """Ground 100.00, chamber invert 98.50, so the connection must arrive at 98.622. The
    outlet at 98.80 is ABOVE that, so a pure LEVEL comparison - even one that correctly
    starts below ground and correctly aims at the chamber - says yes.

    But the route is 40 m and G203-p18 Table 5 gives a rider or lateral a 1 % minimum, so
    0.40 m of fall is spent getting there. It arrives at 98.40, 0.222 m short."""
    r = CN.check_one(100.00, 98.50, 40.0, DN, basis=hcc, crit=C)
    assert r.outlet_inv > r.required_inv, "the level comparison alone must say yes"
    assert r.can_conn == 0
    assert r.why == CN.WHY_ROUTE
    assert abs(r.fall_m - C.LATERAL_MIN_SLOPE * 40.0) < 1e-12
    assert abs(r.need_m - 0.222) < 5e-4, r.need_m


def test_mode_3_a_zero_length_route_spends_nothing_and_the_same_plot_passes(hcc):
    """The same plot and the same chamber, with the route taken away. It passes. The route
    length is the whole of mode 3."""
    r = CN.check_one(100.00, 98.50, 0.0, DN, basis=hcc, crit=C)
    assert r.can_conn == 1 and r.fall_m == 0.0


def test_the_route_length_is_not_optional(hcc):
    """A frame with no route length, no LEN_M and no geometry raises. Running the check
    without it is the level comparison this module exists to replace, and doing that
    silently is worse than not running at all."""
    conn = pd.DataFrame({"CONN_ID": ["C1"], "OUT_NODE": ["N1"], "GRD_PLOT": [100.0],
                         "DN": [DN]})
    with pytest.raises(CN.ConnectivityError, match="FAILURE MODE 3"):
        CN.check_connections(conn, chamber_inv=np.array([98.0]), crit=C, basis=hcc)


# ======================================================================================
# THE THREE MODES ARE INDEPENDENT
# ======================================================================================

def test_the_three_modes_are_three_different_defects_not_one(hcc):
    """Each mode is built so that the OTHER two are switched off, and each still fails.
    If they were one defect wearing three hats, at least one of these would pass."""
    mode1 = CN.check_one(100.00, 99.20, 0.0, DN, basis=hcc, crit=C)     # no route at all
    mode3 = CN.check_one(100.00, 98.50, 40.0, DN, basis=hcc, crit=C)    # clears the level
    assert mode1.can_conn == 0 and mode1.fall_m == 0.0
    assert mode3.can_conn == 0 and mode3.outlet_inv > mode3.required_inv
    assert mode1.why != mode3.why, (
        "mode 1 and mode 3 must be reported as different reasons - one is unfixable by "
        "shortening the route and the other is exactly that")


# ======================================================================================
# CONN_NEED IS A SIZE, AND THE SIZE IS THE REMEDY
# ======================================================================================

@pytest.mark.parametrize("grd,inv,route", [(100.0, 99.20, 0.0), (100.0, 98.50, 40.0),
                                           (100.0, 98.30, 55.0), (95.5, 94.9, 12.0)])
def test_conn_need_is_exactly_what_it_would_take(grd, inv, route, hcc):
    """Concept rule 7: FLAG, DO NOT SOLVE - but a flag with no SIZE cannot be priced,
    ranked or argued about. So CONN_NEED must be the real remedy: lower the sewer at that
    chamber by exactly CONN_NEED and the plot connects, and by a hair less and it does
    not."""
    bad = CN.check_one(grd, inv, route, DN, basis=hcc, crit=C)
    assert bad.can_conn == 0 and bad.need_m > 0
    just = CN.check_one(grd, inv - bad.need_m, route, DN, basis=hcc, crit=C)
    assert just.can_conn == 1, (bad, just)
    short = CN.check_one(grd, inv - bad.need_m + 0.05, route, DN, basis=hcc, crit=C)
    assert short.can_conn == 0, "CONN_NEED is not enough depth"


def test_a_connectable_plot_carries_no_reason_and_needs_no_depth(hcc):
    """contract.CONNECTIONS refuses CAN_CONN = 1 with a CONN_WHY, and refuses
    CAN_CONN = 1 with CONN_NEED > 0. The module must not produce either."""
    r = CN.check_one(100.0, 96.0, 20.0, DN, basis=hcc, crit=C)
    assert r.can_conn == 1 and r.why == "" and r.need_m == 0.0


def test_an_untestable_plot_gets_a_reason_and_a_need_of_zero(hcc):
    """An unknown is not a depth. Where the check could not run, CONN_NEED is 0.0 and
    CONN_WHY says which input was missing - the pair contract.CONNECTIONS allows, and the
    honest one. Publishing a fabricated depth for a plot nobody measured is the same
    defect as publishing a fabricated crossing angle (inheritance row 22)."""
    for r in (CN.check_one(float("nan"), 96.0, 20.0, DN, basis=hcc, crit=C),
              CN.check_one(100.0, float("nan"), 20.0, DN, basis=hcc, crit=C),
              CN.check_one(100.0, 96.0, float("nan"), DN, basis=hcc, crit=C),
              CN.check_one(100.0, 96.0, 20.0, None, basis=hcc, crit=C)):
        assert r.can_conn == 0
        assert r.why in CN.CONN_WHY_VOCAB and r.why not in CN.WHY_IS_A_VERDICT
        assert r.need_m == 0.0


# ======================================================================================
# THE VOCABULARY IS CLOSED, AND EVERY WORD IN IT IS REACHABLE
# ======================================================================================

def test_every_reason_in_the_vocabulary_can_actually_happen(hcc):
    """A vocabulary with an unreachable word is a vocabulary that lies about what the
    check tests. All seven, each from a case built for it."""
    got = {
        CN.check_one(100.0, 99.2, 0.0, DN, basis=hcc, crit=C).why,
        CN.check_one(100.0, 98.5, 40.0, DN, basis=hcc, crit=C).why,
        CN.check_one(float("nan"), 96.0, 20.0, DN, basis=hcc, crit=C).why,
        CN.check_one(100.0, float("nan"), 20.0, DN, basis=hcc, crit=C).why,
        CN.check_one(100.0, 96.0, float("nan"), DN, basis=hcc, crit=C).why,
        CN.check_one(100.0, 96.0, 20.0, None, basis=hcc, crit=C).why,
    }
    conn = pd.DataFrame({"CONN_ID": ["C1"], "OUT_NODE": [""], "GRD_PLOT": [100.0],
                         "LEN_M": [20.0], "DN": [DN]})
    got.add(CN.check_connections(conn, chamber_inv=np.array([96.0]), crit=C,
                                 basis=hcc).CONN_WHY.iloc[0])
    assert got == set(CN.CONN_WHY_VOCAB), sorted(set(CN.CONN_WHY_VOCAB) - got)


def test_a_verdict_and_a_missing_input_are_counted_apart(hcc):
    """"This plot cannot be served on gravity" and "we do not know whether this plot can
    be served" are different findings with different remedies. summary() must not merge
    them - merging them is how W11b's `CAN_DRAIN cannot run` became a blank."""
    conn = pd.DataFrame({
        "CONN_ID": [f"C{i}" for i in range(4)],
        "OUT_NODE": ["N1", "N1", "", "N1"],
        "GRD_PLOT": [100.0, 100.0, 100.0, float("nan")],
        "LEN_M": [0.0, 20.0, 20.0, 20.0], "DN": [DN] * 4})
    res = CN.check_connections(conn, chamber_inv=np.array([99.2, 90.0, 90.0, 90.0]),
                               crit=C, basis=hcc)
    s = CN.summary(res)
    assert s["n_verdict_fail"] == 1, s
    assert s["n_cannot_run"] == 2, s
    assert s["n_can"] == 1, s


# ======================================================================================
# THE ARRIVAL ALLOWANCE - it varies with the bore, and it is never defaulted
# ======================================================================================

def test_the_arrival_allowance_is_the_guidelines_own_depth_of_flow():
    """G203-p27 Table 10 caps the depth of flow at 0.65 D to DN350 and 0.50 D above, so
    that is where the water surface sits and a connection arriving below it is drowned at
    peak. The RULE is this module's assumption and says so in ASSUMPTIONS; the NUMBER is
    the guideline's."""
    for dn in (200, 315, 400, 900, 1200):
        assert abs(CN.arrival_allowance(dn, "flow_depth", C)
                   - C.dod_limit(dn) * C.internal_diameter(dn)) < 1e-12
    assert CN.arrival_allowance(200, "soffit", C) == C.internal_diameter(200)
    assert CN.arrival_allowance(200, "invert", C) == 0.0
    assert "ARRIVAL_ALLOWANCE_RULE" in CN.ASSUMPTIONS


def test_the_allowance_is_not_constant_across_the_bores():
    """Inheritance row 22 - a published column that is constant where it should vary is a
    fabrication. ALLOW_M is a physical quantity that depends on the receiving pipe, and a
    DN1200 trunk carries five times the flow depth of a DN200 lateral."""
    a = CN.arrival_allowance(np.array([200.0, 315.0, 400.0, 900.0, 1200.0]), "flow_depth", C)
    assert len(set(np.round(a, 6))) == len(a)
    assert a[-1] > a[0] * 4


def test_a_missing_bore_refuses_rather_than_substituting_a_diameter(hcc):
    """A default diameter would make ALLOW_M identical on every row - the fabrication
    above, arrived at by being helpful. The module raises and names the escape."""
    conn = pd.DataFrame({"CONN_ID": ["C1"], "OUT_NODE": ["N1"], "GRD_PLOT": [100.0],
                         "LEN_M": [20.0]})
    with pytest.raises(CN.ConnectivityError, match="RECEIVING BORE"):
        CN.check_connections(conn, chamber_inv=np.array([98.0]), crit=C, basis=hcc)
    loose = CN.basis_hcc(C, arrival_rule="invert")
    r = CN.check_connections(conn, chamber_inv=np.array([98.0]), crit=C, basis=loose)
    assert float(r.ALLOW_M.iloc[0]) == 0.0


def test_dn_at_node_reads_the_outgoing_pipe_and_never_invents_one():
    """The connection joins the pipe LEAVING the chamber - that is the water surface it
    must clear. An outfall has no outgoing pipe, so the largest incoming bore stands in.
    A node with neither is NaN, which becomes a named reason, never a default."""
    reaches = pd.DataFrame({"US_NODE": ["N0", "N1"], "DS_NODE": ["N1", "N2"],
                            "DN": [200, 300]})
    nodes = pd.DataFrame({"NODE_UID": ["N0", "N1", "N2", "N3"], "INV_M": [0.0] * 4})
    dn = CN.dn_at_node(nodes, reaches)
    assert dn["N0"] == 200 and dn["N1"] == 300 and dn["N2"] == 300
    assert not np.isfinite(dn["N3"])


# ======================================================================================
# THE FRAME VERSION IS THE SCALAR VERSION
# ======================================================================================

def _synthetic(n: int = 300, seed: int = 20260906):
    rng = np.random.default_rng(seed)
    grd = 100.0 + rng.normal(0, 3, n)
    inv = grd - rng.uniform(0.4, 4.0, n)
    conn = pd.DataFrame({
        "CONN_ID": [f"C{i:04d}" for i in range(n)],
        "PLOT_ID": [f"P{i:04d}" for i in range(n)],
        "OUT_NODE": [f"N{i % 30:03d}" for i in range(n)],
        "GRD_PLOT": grd,
        "LEN_M": rng.uniform(0, 110, n),
        "DN": rng.choice([200, 315, 400, 900], n)})
    return conn, inv


def test_the_vectorised_check_agrees_with_the_scalar_one_row_for_row(hcc):
    """Two implementations of one rule is how a project ends up with two answers. The
    scalar form exists to be hand-checked; if the frame form drifts from it, the readable
    version is no longer a description of what runs."""
    conn, inv = _synthetic()
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    for i in range(len(conn)):
        one = CN.check_one(conn.GRD_PLOT.iloc[i], inv[i], conn.LEN_M.iloc[i],
                           conn.DN.iloc[i], basis=hcc, crit=C)
        assert int(res.CAN_CONN.iloc[i]) == one.can_conn, i
        assert res.CONN_WHY.iloc[i] == one.why, i
        assert abs(float(res.CONN_NEED.iloc[i]) - round(one.need_m, 3)) < 2e-3, i


def test_a_dangling_chamber_reference_raises_instead_of_becoming_an_unserved_plot(hcc):
    """H16: topology is written down. An OUT_NODE that is not in the nodes frame is a
    wiring bug, and filing it under "plots that cannot connect" is how a real number gets
    buried in a list of 5,521."""
    conn, _ = _synthetic(20)
    nodes = pd.DataFrame({"NODE_UID": ["N000", "N001"], "INV_M": [90.0, 90.0]})
    with pytest.raises(CN.ConnectivityError, match="not in the nodes frame"):
        CN.check_connections(conn, nodes, crit=C, basis=hcc, dn=conn.DN.to_numpy())


def test_an_empty_frame_returns_the_columns_and_not_a_crash(hcc):
    conn, _ = _synthetic(5)
    res = CN.check_connections(conn.iloc[:0], chamber_inv=np.array([]), crit=C, basis=hcc)
    assert len(res) == 0
    assert set(CN.CONTRACT_COLS).issubset(res.columns)
    assert set(CN.DIAG_COLS).issubset(res.columns)


# ======================================================================================
# ADD, THEN TAKE AWAY - inheritance row 4
# ======================================================================================

def test_a_deeper_sewer_clears_flags_and_the_number_cleared_is_published(hcc):
    """The row whose loss cost W11b 69 spurious pumping stations. A CAN_CONN = 0 raised
    against a stage-4 sewer is not a verdict on a stage-6 sewer, and a flag that is only
    ever added is a decision that is never re-examined. recheck() returns the count and
    the ids, so the stage can publish what it removed."""
    conn, inv = _synthetic()
    before = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    after = CN.check_connections(conn, chamber_inv=inv - 1.5, crit=C, basis=hcc)
    rc = CN.recheck(before, after)
    assert rc["n_before_fail"] > 0
    assert rc["n_cleared"] > 0
    assert rc["n_after_fail"] == rc["n_before_fail"] - rc["n_cleared"] + rc["n_raised"]
    assert rc["n_raised"] == 0, "lowering every sewer cannot break a connection"
    assert rc["cleared_ids"], "a cleared flag with no id cannot be checked"
    assert rc["depth_recovered_m"] > 0


def test_raising_a_sewer_raises_flags_and_that_is_counted_too(hcc):
    """The mirror. A stage that only ever reports what it cleared is as blind as one that
    only ever adds."""
    conn, inv = _synthetic()
    before = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    after = CN.check_connections(conn, chamber_inv=inv + 1.5, crit=C, basis=hcc)
    rc = CN.recheck(before, after)
    assert rc["n_raised"] > 0 and rc["n_cleared"] == 0


# ======================================================================================
# WHAT IT CANNOT DECIDE, AS A NUMBER
# ======================================================================================

def test_the_outlet_depth_the_guideline_does_not_settle_is_reported_as_a_band(hcc):
    """G203-p19 gives the HCC a depth RANGE (1.2 - 2.0 m) and a property connection a
    minimum COVER (600 mm) and does not say which governs where a connection leaves a
    plot. The two readings differ by 0.390 m and they move the answer. sensitivity()
    publishes how many plots move, so the modelling choice is a number in the report
    rather than a default argument nobody sees."""
    conn, inv = _synthetic()
    sens = CN.sensitivity(conn, chamber_inv=inv, crit=C)
    assert list(sens.basis) == ["BASIS_HCC", "BASIS_SHALLOW", "BASIS_STRICT"]
    assert sens.n_flip_vs_first.iloc[0] == 0
    assert sens.n_flip_vs_first.iloc[1] > 0, "the readings must actually differ"
    assert sens.n_can.iloc[1] > sens.n_can.iloc[0], "shallow is the generous reading"
    assert sens.n_can.iloc[2] < sens.n_can.iloc[0], "strict is the harsh one"
    gap = (CN.basis_hcc(C).outlet_depth_m + CN.basis_hcc(C).fall(C.HCC_OFFSET_M)
           - CN.basis_shallow(C).outlet_depth_m - CN.basis_shallow(C).fall(C.HCC_OFFSET_M))
    assert abs(gap - 0.390) < 1e-9, gap


def test_the_minimum_gradient_is_the_generous_reading_and_a_zero_is_therefore_firm(hcc):
    """The check lays the connection at its MINIMUM legal gradient, which loses the least
    fall. That makes a 0 firm - no legal gradient would have connected it - and a 1 weak,
    which is why ASSUMPTIONS says so out loud. Charging the whole route the 3 % property
    connection minimum instead can only ever reject MORE plots, never fewer."""
    conn, inv = _synthetic()
    loose = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    tight = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=CN.basis_strict(C))
    assert int(tight.CAN_CONN.sum()) < int(loose.CAN_CONN.sum())
    assert (tight.CAN_CONN <= loose.CAN_CONN).all(), (
        "a steeper connection can never connect a plot the flatter one could not")
    assert "MINIMUM_GRADIENT_IS_THE_TEST" in CN.ASSUMPTIONS


def test_every_assumption_says_what_would_settle_it():
    """A declared assumption with no route to closure is a permanent excuse. Each entry is
    (what it is, what settles it), and the two that move the answer must both name
    something outside this repository."""
    assert len(CN.ASSUMPTIONS) >= 5
    for k, v in CN.ASSUMPTIONS.items():
        assert isinstance(v, tuple) and len(v) == 2, k
        assert len(v[0]) > 80 and len(v[1]) > 30, k
    for k in ("OUTLET_DEPTH", "ARRIVAL_ALLOWANCE_RULE"):
        assert "PENDING" in CN.ASSUMPTIONS[k][1], k


# ======================================================================================
# WHAT IT WOULD TAKE IS NOT ALWAYS "DIG DEEPER"
# ======================================================================================

def test_best_of_prefers_a_chamber_that_works_over_one_that_does_not(hcc):
    """Sometimes the plot is on the wrong side of a junction and the chamber 50 m the
    other way works today. A schedule that only ever says "dig deeper" spends money a
    re-assignment would not."""
    cand = pd.DataFrame({
        "CONN_ID": ["C0", "C0", "C1", "C1"],
        "OUT_NODE": ["A", "B", "A", "B"],
        "GRD_PLOT": [100.0] * 4,
        "LEN_M": [10.0, 60.0, 10.0, 60.0],
        "DN": [DN] * 4})
    best = CN.best_of(cand, chamber_inv=np.array([99.5, 96.0, 99.5, 99.4]), crit=C,
                      basis=hcc).set_index("CONN_ID")
    assert len(best) == 2
    assert best.loc["C0", "OUT_NODE"] == "B", "the chamber that connects must win"
    assert int(best.loc["C0", "CAN_CONN"]) == 1
    assert int(best.loc["C1", "CAN_CONN"]) == 0, "neither candidate works for C1"


def test_where_nothing_works_best_of_returns_the_cheapest_remedy(hcc):
    """Two candidates, neither connecting. The one needing the least extra depth is the
    one the schedule should carry, because the schedule is ranked by what it would take."""
    cand = pd.DataFrame({
        "CONN_ID": ["C0", "C0"], "OUT_NODE": ["A", "B"], "GRD_PLOT": [100.0, 100.0],
        "LEN_M": [10.0, 10.0], "DN": [DN, DN]})
    best = CN.best_of(cand, chamber_inv=np.array([99.5, 99.9]), crit=C, basis=hcc)
    assert int(best.CAN_CONN.iloc[0]) == 0
    assert best.OUT_NODE.iloc[0] == "A", "the shallower shortfall is the cheaper remedy"


# ======================================================================================
# THE PUBLISHED FIELDS SATISFY THE CONTRACT
# ======================================================================================

def test_the_output_passes_the_connections_contract(contract, hcc):
    """The three deliverable fields are contract.CONNECTIONS fields and the contract has
    five cross-field rules about them. Proving the module's own output satisfies them here
    means the wiring stage meets a schema it has already been shown to meet."""
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import LineString

    conn, inv = _synthetic(60)
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    n = len(conn)
    rows = []
    for i in range(n):
        rows.append(dict(
            CONN_ID=conn.CONN_ID.iloc[i], PLOT_ID=conn.PLOT_ID.iloc[i],
            OUT_NODE=f"N{i:05d}", WHY="assigned", SYSTEM="central", CONN_TYPE="PCS",
            Q_ADF_M3D=round(C.PLOT_QADF_M3D * C.PROPS_PER_PLOT, 4),
            N_PROP=C.PROPS_PER_PLOT, LEN_M=10.0,
            SLOPE_LAID=C.PCS_MIN_SLOPE * 100.0, COVER_M=C.PCS_MIN_COVER,
            CAN_CONN=int(res.CAN_CONN.iloc[i]), CONN_WHY=res.CONN_WHY.iloc[i],
            CONN_NEED=float(res.CONN_NEED.iloc[i]),
            NAME=contract.concept_name("I", "manhole", subnet="S01", tier="lateral",
                                       seq=i + 1),
            TOWN="I", SUBNET="S01", SRC="dwg_road", CONFIDENCE="drafted", STAGE="T",
            PACKAGE="", PHASE=0))
    g = gpd.GeoDataFrame(
        rows, crs=contract.CRS_EPSG,
        geometry=[LineString([(i * 20.0, 30.0), (i * 20.0, 20.0)]) for i in range(n)])
    g["LEN_M"] = g.geometry.length
    contract.validate(g, "connections", stage="test_connectivity")


def test_conn_why_is_not_one_reason_repeated(hcc):
    """contract.constant_column_problem() refuses a reason column that is CONSTANT across
    every row where it applies - inheritance row 22. On real ground both level verdicts
    occur, and the module must produce both rather than labelling everything the same."""
    conn, inv = _synthetic(400)
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    bad = res[res.CAN_CONN == 0]
    assert len(bad) >= 30, "too few failures to say anything about constancy"
    assert bad.CONN_WHY.nunique() > 1, (
        "every failure carries the same reason - either the ground is uniform or the "
        "classification is not reading its own input")
    assert set(bad.CONN_WHY) <= set(CN.CONN_WHY_VOCAB)


def test_the_diagnostics_are_measured_quantities_not_declarations(hcc):
    """Every diagnostic column must VARY over a mixed network. A constant one is either
    not being computed or is a declaration wearing a measurement's name."""
    conn, inv = _synthetic(400)
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    for col in ("OUT_INV_M", "ARR_INV_M", "REQ_INV_M", "ALLOW_M", "ROUTE_M", "FALL_M",
                "MARGIN_M", "S_AVL_PCT"):
        assert res[col].nunique(dropna=True) > 1, f"{col} is constant"
    for col in CN.CONTRACT_COLS + CN.DIAG_COLS:
        assert len(col) <= 10, f"{col} would be truncated by a DBF"


def test_the_schedule_is_ranked_by_what_it_would_take(hcc):
    """A list nobody can rank is a list nobody acts on. 5,521 plots is a number nobody can
    act on until it is 5,521 plots needing this much depth on these runs."""
    conn, inv = _synthetic(200)
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    sch = CN.schedule(res, conn)
    assert len(sch) == int((res.CAN_CONN == 0).sum())
    assert sch.CONN_NEED.is_monotonic_decreasing
    assert {"CONN_ID", "OUT_NODE", "CONN_WHY", "CONN_NEED", "PLOT_ID"} <= set(sch.columns)


def test_the_report_reads_from_summary_so_the_text_cannot_disagree_with_the_layer(hcc):
    """Inheritance row 10 - one published quantity, one function. Seven station counts
    reached circulation in W10 because each was computed where it was printed."""
    conn, inv = _synthetic(200)
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    s = CN.summary(res)
    txt = CN.report(res, C)
    assert f"{s['n_can']:,} of {s['n']:,}" in txt
    assert f"**{s['n_verdict_fail']:,} cannot**" in txt
    assert "cannot run is a FAILURE" in txt
    assert s["n_can"] + s["n_cannot"] == len(res)


# ======================================================================================
# THE CONCEPT SWITCH, AND THE SENSITIVITY THE PROJECT ALREADY CARRIES
# ======================================================================================

def test_house_connection_design_is_switched_off_and_this_module_says_so():
    """criteria.CONCEPT_OFF['house_connections'] names this check as the ONLY question the
    concept stage asks of a plot. If the capability is ever switched back on, the register
    entry is where the switch lives, and this module's banner points at it."""
    assert C.CONCEPT_STAGE is True
    what, back = C.CONCEPT_OFF["house_connections"]
    assert "CAN_CONN" in what and "CONN_NEED" in what
    assert "house_connections" in CN.assumptions_banner()
    with pytest.raises(Exception):
        C.assert_enabled("house_connections")


def test_the_check_does_not_move_with_tau():
    """tau is the project's largest open assumption (GAP-9) and it moves 1,124 gradients.
    It must not move THIS answer: a house connection's minimum gradient is G203-p18
    Table 5, a fixed percentage, and has nothing to do with tractive stress. If this test
    ever fails, the connection is being levelled with the secondary network's rules."""
    conn, inv = _synthetic(100)
    a = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=CN.basis_hcc(C))
    c2 = replace(C, TAU_PA=2.0)
    b = CN.check_connections(conn, chamber_inv=inv, crit=c2, basis=CN.basis_hcc(c2))
    assert (a.CAN_CONN.to_numpy() == b.CAN_CONN.to_numpy()).all()
    assert np.allclose(a.CONN_NEED.to_numpy(), b.CONN_NEED.to_numpy())


# ======================================================================================
# THE MODULE'S OWN SELF-TEST RUNS
# ======================================================================================

@pytest.mark.slow
def test_the_module_self_test_passes():
    """`python -m w12.connectivity` proves the guards BITE rather than asserting they
    exist. Running it from the suite means a self-test nobody remembers to run still gets
    run - the same argument test_deadcode.py makes for the other modules."""
    r = subprocess.run([sys.executable, "-m", "w12.connectivity"], capture_output=True,
                       text=True, cwd=str(PY_DIR), timeout=120)
    assert r.returncode == 0, f"{r.stdout[-3000:]}\n{r.stderr[-3000:]}"
    assert "self-test PASSED" in r.stdout


# ======================================================================================
# THE GUARDS THAT KEEP THE ANSWER ANSWERABLE
# ======================================================================================

def test_recheck_refuses_a_duplicated_load_unit(hcc):
    """contract.CONNECTIONS keys on CONN_ID: one load unit is one row. With a duplicate,
    "how many failures did this pass clear" has no answer - and that number is the whole
    of inheritance row 4."""
    conn, inv = _synthetic(10)
    res = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=hcc)
    dup = pd.concat([res, res.iloc[:1]], ignore_index=True)
    with pytest.raises(CN.ConnectivityError, match="duplicated CONN_ID"):
        CN.recheck(dup, res)


def test_the_invert_rule_never_asks_for_a_bore_it_does_not_use(hcc):
    """'invert' is the documented escape for a stage that has no reach layer yet - it is
    also what W11b's s8_export effectively did, so the two iterations stay comparable. It
    must never produce WHY_NO_DN, and it must be the loosest of the three rules."""
    conn, inv = _synthetic(200)
    conn = conn.drop(columns=["DN"])
    answers = {}
    for rule in CN.ARRIVAL_RULES:
        b = CN.basis_hcc(C, arrival_rule=rule)
        kw = {} if rule == "invert" else {"dn": np.full(len(conn), DN)}
        r = CN.check_connections(conn, chamber_inv=inv, crit=C, basis=b, **kw)
        assert CN.WHY_NO_DN not in set(r.CONN_WHY), rule
        answers[rule] = int(r.CAN_CONN.sum())
    assert answers["invert"] >= answers["flow_depth"] >= answers["soffit"], answers


def test_a_long_route_is_flagged_and_not_failed(hcc):
    """G203-p18 caps the property connection sewer at 50 m "in order to allow maintenance.
    If necessary, a manhole will be added" - so a long route needs a manhole, not a
    rejection. Concept rule 7 is FLAG, DO NOT SOLVE; failing it would be solving it, and
    wrongly."""
    conn = pd.DataFrame({"CONN_ID": ["short", "long"], "OUT_NODE": ["N1", "N1"],
                         "GRD_PLOT": [100.0, 100.0],
                         "LEN_M": [C.PCS_MAX_LEN - 1.0, C.PCS_MAX_LEN + 1.0],
                         "DN": [DN, DN]})
    r = CN.check_connections(conn, chamber_inv=np.array([95.0, 95.0]), crit=C,
                             basis=hcc).set_index("CONN_ID")
    assert int(r.loc["short", "CONN_LONG"]) == 0
    assert int(r.loc["long", "CONN_LONG"]) == 1
    assert int(r.loc["long", "CAN_CONN"]) == 1, "a long route is a flag, not a failure"
    assert r.loc["long", "CONN_WHY"] == ""
