"""ADVERSARIAL REVIEW OF THE OUTFALL RULE - the five defects the first pass shipped.

Every test here reproduces a defect that was found by building the case rather than by
reading the code, and then locks the fix so it cannot come back.  None of them touches a
file or the terrain grid: the synthetic case is the only one where the right answer is
known in advance.

  1  A close approach `MEET_TOL_M` from a corridor END was dropped on the ALONG-distance,
     which is not the same quantity as the END NODE's distance to the trunk.  The two can
     differ by a factor of two, so a corridor could meet the trunk with NO outfall anywhere
     near it while `X_MAIN` reported zero offences.  Measured case: 2.6 m from the trunk,
     1.3 m along from an end node that is 3.4 m away.  Now counted and published.
  2  `subnets_joining_off_low` counted `JOIN_OFF_M > 0` - true of almost every sub-network,
     because it only says the low point is a DIFFERENT NODE - while `JOIN_WHY` was written
     only where the outlet is genuinely ABOVE that low point.  The manifest claimed every
     counted row carried a reason.  Most did not.
  3  The chain-depth, zone-density and hierarchy-ratio gates were scored arithmetically on
     a sub-network with NO lateral runs: "pass" on chain depth and "below" on the hierarchy
     ratio, off the same empty evidence.  A check that cannot run is not a pass
     (inheritance-ledger row 2), and the outfall rule makes small sub-networks the common
     case rather than a curiosity.
  4  A sub-network that does not reach the Main Pipe was graded against the trunk-share
     band it cannot meet, and read "below" - a failure manufactured by the apportionment.
  5  The cut asserted LENGTH only, while its own docstring claimed length, plot count and
     load.  Now all three are asserted.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import s2_orient as S
import s3_hierarchy as H
from w12 import asbuilt as AB
from w12 import criteria as CR

C = CR.DEFAULT


@pytest.fixture(scope="session", autouse=True)
def _one_asbuilt():
    """One as-built measurement for the file - it is read-only here and costs 78 s a call."""
    inst = AB.AsBuilt()
    tgt = inst.targets()
    inst.targets = lambda: tgt
    orig = AB.AsBuilt
    AB.AsBuilt = lambda *a, **k: inst
    try:
        yield inst
    finally:
        AB.AsBuilt = orig


# ==========================================================================================
# 1.  THE MEETING POINT NOBODY PICKS UP
# ==========================================================================================

def _orient_for_cut(corridors, main_coords=((0.0, 0.0), (1000.0, 0.0))):
    import geopandas as gpd
    from shapely.geometry import LineString, Point

    rows, geoms, node_geom = [], [], {}
    for cid, (us, ds, coords) in corridors.items():
        g = LineString(coords)
        geoms.append(g)
        rows.append(dict(CID=cid, US_NODE=us, DS_NODE=ds, LEN_M=g.length,
                         N_PLOT=10.0, Q_NEAR_M3D=5.0, Q_M3D=5.0,
                         SRC="test", CONFIDENCE="built"))
        node_geom[us] = Point(coords[0])
        node_geom[ds] = Point(coords[-1])
    cor = gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:32640")
    main = gpd.GeoDataFrame({"X": [1]}, geometry=[LineString(main_coords)],
                            crs="EPSG:32640")
    o = object.__new__(S.Orient)
    o.gpd, o.cor, o.main, o.node_geom, o.notes = gpd, cor, main, node_geom, []
    o.measure = lambda: None
    return o


def test_a_meeting_point_dropped_at_an_end_whose_node_is_off_the_trunk_is_named():
    """THE HOLE IN THE INVARIANT.

    The end-drop is stated on ALONG-distance.  A close approach can sit `tol` from the
    trunk AND `tol` along from the end, which puts the end node up to 2 x tol away - past
    the radius `find_roots` uses.  Here: the corridor passes 2.6 m from the trunk, 1.28 m
    along from a node that is 3.4 m from it.  Nothing is minted, that node is not an
    outfall, and `meets_without_a_node` reports 0 because it asks the same along-distance
    question.  A candidate outlet is lost, and it used to be lost in silence.
    """
    from shapely.ops import unary_union
    o = _orient_for_cut({"A": ("n1", "n2",
                               [(500.0, 3.4), (501.0, 2.6), (600.0, 100.0)])})
    o.meet_main_pipe()
    main = unary_union(list(o.main.geometry))

    # the corridor really does meet the trunk, by this stage's own definition
    assert o.cor.geometry.iloc[0].distance(main) < S.MEET_TOL_M
    # nothing was minted, and neither node is inside the radius find_roots uses
    assert o.meet_splits == 0
    assert o.node_geom["n1"].distance(main) > S.MAIN_SNAP_M
    # the old invariant still says "nothing wrong", which is exactly the divergence
    assert o.n_meet_off_node == 0
    # ...so the gap is NAMED instead
    assert o.n_meet_end_gap == 1
    r = o.meet_end_gap.iloc[0]
    assert r.NODE == "n1"
    assert r.KIND == "within_tol"
    assert r.NODE_DMAIN_M == pytest.approx(3.4, abs=1e-3)


def test_a_crossing_near_an_end_is_not_in_the_gap_because_it_cannot_be():
    """The divergence is only possible on a CLOSE APPROACH.

    A crossing lies ON the trunk, so an end within `tol` ALONG the line is within `tol` of
    the trunk itself and `find_roots` takes it as an outfall.  That is why the no-crossing
    rule survives the hole above, and it is worth a test rather than an argument.
    """
    from shapely.ops import unary_union
    o = _orient_for_cut({"A": ("n1", "n2", [(500.0, -2.0), (500.0, 200.0)])})
    o.meet_main_pipe()
    main = unary_union(list(o.main.geometry))
    assert o.meet_splits == 0, "the crossing is 2 m from the end, inside the merge radius"
    assert o.n_meet_end_gap == 0
    assert o.node_geom["n1"].distance(main) <= S.MAIN_SNAP_M, \
        "and that end node IS an outfall, so the flow discharges rather than crossing"


def test_the_gap_is_a_manifest_row_and_a_published_table():
    """A number that lives only in a console log is a number nobody can check next month."""
    src = open(S.__file__, encoding="utf-8").read()
    assert '("meet_points_lost_at_an_end"' in src
    assert "meet_cuts_end_gap=" in src, "the row-by-row list must be written out too"


def test_cutting_asserts_the_plot_count_and_the_load_not_only_the_length():
    """The docstring claimed all three were conserved; only the length was asserted.

    Proved by breaking it: prorating the plots by a factor that is not 1 must raise.
    """
    o = _orient_for_cut({"A": ("n1", "n2", [(500.0, -100.0), (500.0, 100.0)])})
    real_len = o.cor.LEN_M.copy()
    o.meet_main_pipe()
    assert abs(float(o.cor.N_PLOT.sum()) - 10.0) < 1e-9
    assert abs(float(o.cor.Q_M3D.sum()) - 5.0) < 1e-9
    assert abs(float(o.cor.LEN_M.sum()) - float(real_len.sum())) < 1e-6

    src = open(S.__file__, encoding="utf-8").read()
    body = src[src.index("def meet_main_pipe"):src.index("def meets_off_node")]
    assert "plot_before" in body and "q_before" in body, \
        "the cut must assert the plot count and the load, not only the length"


# ==========================================================================================
# 2.  THE COUNT AND THE REASON COLUMN ARE THE SAME SET OF ROWS
# ==========================================================================================

def _orient_for_subnets(z, edges, roots, relief=None):
    o = object.__new__(S.Orient)
    n = len(z)
    o.NV = n
    o.NZ = np.asarray(z, float)
    o.NX = np.arange(n, dtype=float) * 100.0
    o.NY = np.zeros(n, dtype=float)
    o.node_ids = [f"N{i:03d}" for i in range(n)]
    o.nid = {a: i for i, a in enumerate(o.node_ids)}
    o.u = np.array([e[0] for e in edges], np.int64)
    o.v = np.array([e[1] for e in edges], np.int64)
    o.L = np.array([float(e[2]) for e in edges], float)
    o.edge_in = np.ones(len(edges), bool)
    o.roots = np.asarray(roots, np.int64)
    o._idx = np.arange(len(edges), dtype=np.int64)
    o.weights_used = dict(wf=o.L.copy(), wb=o.L.copy())
    o.notes = []
    o.Q = np.full(len(edges), 10.0)
    o.d_main = np.array([0.0 if i in set(roots) else 500.0 for i in range(n)], float)
    o.trunk_relief = np.zeros(n) if relief is None else np.asarray(relief, float)
    return o


def _tree(o, parent):
    via = {}
    for child, par in parent.items():
        if par < 0:
            via[child] = -1
            continue
        cand = np.flatnonzero(((o.u == child) & (o.v == par)) |
                              ((o.u == par) & (o.v == child)))
        via[child] = int(cand[0])
    arcs = [e for e in via.values() if e >= 0]
    fwd = [bool(o.u[e] == c) for c, e in via.items() if e >= 0]
    return S.Tree(name="test", arc=np.asarray(arcs, np.int64),
                  fwd=np.asarray(fwd, bool), parent=dict(parent), via=via,
                  joins=np.asarray([c for c, p in parent.items() if p < 0], np.int64),
                  weight=0.0)


def test_a_low_point_500_m_away_but_level_with_the_outlet_is_not_counted_as_a_bad_join():
    """`JOIN_OFF_M > 0` only says the low point is a DIFFERENT NODE.

    The engineer's rule is on LEVEL - "the LOWEST POINT where it meets it" - so a
    sub-network whose lowest node is 500 m away and 10 mm lower joins AT its low point in
    every sense the DEM can resolve.  Counting it and then writing no reason on it made
    `subnets_joining_off_low` a number most of whose rows could not be explained.
    """
    o = _orient_for_subnets([100.00, 100.10, 99.99],
                            [(1, 0, 200.0), (2, 1, 300.0)], roots=[0])
    tr = _tree(o, {0: -1, 1: 0, 2: 1})
    o._paths(tr)
    sn, _ = o.subnetworks(tr)
    r = sn.iloc[0]
    assert r.LOW_NODE == "N002" and r.JOIN_OFF_M == pytest.approx(500.0)
    assert r.HEAD_M == pytest.approx(0.01)
    assert r.JOIN_WHY == ""
    assert o.n_join_offset == 0, "the count must be the rows that carry a reason"
    assert o.n_low_node_level == 1, "and the level ones are published, not folded in"


def test_every_counted_join_offset_carries_a_reason():
    """The invariant behind the fix, on a mixed table."""
    o = _orient_for_subnets([100.0, 92.0, 88.0],
                            [(1, 0, 100.0), (2, 1, 100.0)], roots=[0])
    tr = _tree(o, {0: -1, 1: 0, 2: 1})
    o._paths(tr)
    sn, _ = o.subnetworks(tr)
    assert o.n_join_offset == int((sn.JOIN_WHY.astype(str).str.len() > 0).sum())
    assert o.n_join_offset == 1
    for r in sn.itertuples():
        if r.JOIN_WHY:
            assert r.HEAD_M > S.ADVERSE_MIN_M and r.JOIN_OFF_M > 0.0


def test_the_level_low_point_count_has_its_own_manifest_row():
    src = open(S.__file__, encoding="utf-8").read()
    assert '("subnets_low_point_at_another_node"' in src


# ==========================================================================================
# 3.  AN OUTFALL WITH NO TREE ARC IS NOT THE SAME AS ONE THAT CARRIES NOTHING
# ==========================================================================================

def test_an_empty_outfall_that_a_head_still_reaches_is_reported_as_such():
    """`KM` sums the TREE arcs only.  A dead-end head is not a tree arc and can still
    discharge at an outfall, so `outfalls_with_no_catchment` is an UPPER bound on the joins
    that carry nothing - and the headline number is the one that gets quoted.

        node 2 is a root with no tree arc into it, but corridor (1, 2) is in play and not
        in the tree, so it becomes a head and can drain to it.
    """
    o = _orient_for_subnets([100.0, 92.0, 60.0],
                            [(1, 0, 100.0), (1, 2, 400.0)], roots=[0, 2])
    tr = _tree(o, {0: -1, 1: 0, 2: -1})
    o._paths(tr)
    sn, _ = o.subnetworks(tr)
    assert o.n_empty_outfall == 1
    assert o.n_empty_outfall_head == 1, \
        "the one empty outfall is touched by a corridor the tree did not use"


def test_the_head_qualified_count_has_its_own_manifest_row():
    src = open(S.__file__, encoding="utf-8").read()
    assert '("outfalls_with_no_catchment_but_a_head"' in src
    # and the row-4 gap is stated rather than claimed closed
    assert "INHERITANCE ROW 4 IS " in src


# ==========================================================================================
# 4.  A CHECK THAT CANNOT RUN IS NOT A PASS
# ==========================================================================================

def _cal_case(run_tier, len_out, arc_sub, run_next=(1, 2, 3, -1, 5, -1),
              root_kind=("main_pipe", "main_pipe"), node_subnet=("S001", "S002")):
    import geopandas as gpd
    from shapely.geometry import LineString
    n = len(run_tier)
    h = H.Hier.__new__(H.Hier)
    h.verbose = False
    h.n_runs = n
    h.run_next = np.asarray(run_next[:n], np.int64)
    h.run_tier = np.array(run_tier, dtype=object)
    h.run_order = H.topo_order(h.run_next, np.arange(n, dtype=np.int64), n)
    h.run_id = np.arange(n, dtype=np.int64)
    h.keep = np.ones(n, bool)
    h.len_out = np.asarray(len_out, float)
    h.arc_tier = h.run_tier.copy()
    h.arc_subnet = np.array(arc_sub, dtype=object)
    h.root_kind = np.array(root_kind, dtype=object)
    h.NX_out = np.array([0.0, 1000.0])
    h.NY_out = np.array([0.0, 0.0])
    h.node_subnet = np.array(node_subnet, dtype=object)
    h.main_pipe = gpd.GeoDataFrame({"X": [1]},
                                   geometry=[LineString([(0.0, 0.0), (1000.0, 0.0)])],
                                   crs="EPSG:32640")
    return h


def test_a_sub_network_with_no_lateral_runs_is_not_scored_pass_on_chain_depth():
    """INHERITANCE ROW 2, IN REVERSE.

    Chain depth, zone density and the hierarchy ratio are all computed OVER THE LATERAL
    RUNS.  A sub-network with none of them has nothing for them to measure, and scored
    arithmetically it reads CHAIN_MED = 0 -> "pass" and HIER_PCT = 0.0 -> "below": one
    silent pass and one false failure off the same empty evidence.  The outfall rule
    multiplies small sub-networks, so this is about to be a large share of the table.
    """
    h = _cal_case(["sub main"] * 4 + ["lateral", "sub main"],
                  [1000.0, 1000.0, 1000.0, 2000.0, 1000.0, 2000.0],
                  ["S001"] * 4 + ["S002"] * 2)
    h.subnet_calibration()
    c = h.subnet_cal.set_index("SUBNET")
    assert c.loc["S001"].N_LAT_RUNS == 0
    assert c.loc["S001"].V_CHAIN == "no lateral runs - cannot run"
    assert c.loc["S001"].V_ZONE == "no lateral runs - cannot run"
    assert c.loc["S001"].V_HIER == "no lateral runs - cannot run"
    row = h.cal_summary.set_index("GATE").loc[
        "chain depth lateral->main (med<=2, p90<=4, max 5)"]
    assert row.N_NA == 1
    assert row.N_IN == 1, "only the sub-network that HAS laterals is counted as a pass"
    assert row.N_BANDED == 1


def test_the_cannot_run_count_is_published():
    src = open(H.__file__, encoding="utf-8").read()
    assert '("subnets_with_no_lateral_runs"' in src
    assert '"N_NA"' in src, "every gate needs the third state, not two"


def test_a_sub_network_that_does_not_reach_the_trunk_is_not_graded_on_its_trunk_share():
    """`_apportion_trunk` gives an island no trunk, so the band reads its 0 % as "below" -
    a failure manufactured by the apportionment against a gate it cannot meet.

    `10_ASBUILT_CALIBRATION` rule T1 already settles that a terminal short of the works is
    legal where it ends at a designed station, so "does not reach the trunk" is a fact to
    be named, not a verdict.
    """
    h = _cal_case(["lateral", "lateral", "lateral", "sub main", "lateral", "sub main"],
                  [1000.0, 1000.0, 1000.0, 2000.0, 2000.0, 2000.0],
                  ["S001"] * 4 + ["ISL001"] * 2,
                  root_kind=("main_pipe", "island_low"),
                  node_subnet=("S001", "ISL001"))
    h.subnet_calibration()
    c = h.subnet_cal.set_index("SUBNET")
    assert c.loc["ISL001"].ENDS_AT == "island_low"
    assert c.loc["ISL001"].TRUNK_KM == 0.0
    assert c.loc["ISL001"].V_TRUNK == "no join onto the Main Pipe"
    assert c.loc["S001"].ENDS_AT == "main_pipe"
    assert c.loc["S001"].V_TRUNK in ("in band", "below", "above")
    row = h.cal_summary.set_index("GATE").loc["trunk share of a sub-network, %"]
    assert row.N_NA == 1 and row.N_BANDED == 1


def test_the_trunk_apportionment_still_conserves_length_with_an_island_present():
    """The island takes no trunk, so every metre must still land on a real join."""
    h = _cal_case(["lateral", "lateral", "lateral", "sub main", "lateral", "sub main"],
                  [1000.0] * 6, ["S001"] * 4 + ["ISL001"] * 2,
                  root_kind=("main_pipe", "island_low"),
                  node_subnet=("S001", "ISL001"))
    got = h._apportion_trunk()
    assert sum(got.values()) == pytest.approx(1.0, abs=1e-6)
    assert set(got) == {"S001"}


# ==========================================================================================
# 5.  THE GATE THAT CANNOT FAIL, STATED SO NOBODY READS IT AS EVIDENCE
# ==========================================================================================

def test_the_no_sub_main_gate_is_vacuous_by_construction_and_says_so():
    """`tiers()` names every component's outlet run a sub main, so `sm > 0` for every
    sub-network and `SM_ZERO` is a CONSTANT 0 column.  The gate can never report a failure.

    That is the right ENGINEERING - the calibration demands every catchment have a
    collector tier - but a gate that cannot fail is not evidence about the layout, and a
    reader must not be able to take the "0 out" row as if it were.
    """
    rng = np.random.default_rng(4)
    for _ in range(120):
        n = int(rng.integers(2, 9))
        nxt = np.full(n, -1, np.int64)
        for i in range(n - 1):
            nxt[i] = int(rng.integers(i + 1, n)) if rng.random() < 0.85 else -1
        h = H.Hier.__new__(H.Hier)
        h.submain_km, h.budget_runs, h.budget_path_m = 2.0, 3, 750.0
        h.n_runs, h.run_next = n, nxt
        h.run_sub_km = np.round(rng.uniform(0.0, 0.5, n), 3)   # all far below 2 km
        h.run_depth, h.run_path_m = np.ones(n), np.zeros(n)
        t = h.tiers()
        assert all(t[o] == "sub main" for o in np.flatnonzero(nxt == -1))

    src = open(H.__file__, encoding="utf-8").read()
    i = src.index('"GATE": "sub-networks with NO sub main at all"')
    assert "BY CONSTRUCTION" in src[i:i + 900], \
        "the gate row itself must say a 0 here is not evidence about the layout"
