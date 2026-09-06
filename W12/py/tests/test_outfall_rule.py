"""THE OUTFALL RULE - tests written against the defect that actually shipped.

Engineer, 2026-09-05/06 (philosophy sec 9):

    "A subnetwork joins the main pipe at the LOWEST POINT WHERE IT MEETS it.
     NO SUBNETWORK CROSSES THE MAIN PIPE AND GROWS PAST IT."

WHAT WENT WRONG, MEASURED ON W11b's OWN SHIPPED `arcs` LAYER (2026-09-06):

    214 arcs, 48.49 km, physically CROSS the Main Pipe and keep going
    397 arcs come within 3 m of it, where only 193 NODES did
     39 sub-networks discharge with more than half their catchment BELOW the outlet,
        517.9 km, and the worst outfall sits 26.34 m above its own low point

The cause is that the question was asked of the wrong object.  `find_roots` asks whether a
NODE is near the trunk; a 200 m street crossing the trunk at its midpoint has both of its
nodes 100 m away, so it crossed and grew past it.

Every test below is pure logic on a hand-built graph - no files, no terrain, milliseconds -
because the synthetic case is the only one where the right answer is known in advance.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

import s2_orient as S
from w12 import criteria as CR

C = CR.DEFAULT


# ==========================================================================================
# 1.  THE TOLERANCE IS DERIVED, NOT INVENTED
# ==========================================================================================

def test_the_meets_tolerance_is_the_node_merge_radius_and_nothing_else():
    """"Meets" needs a distance and the project already has exactly one.

    `criteria.MH_SNAP_M` is the node-merge radius `s1_roads` used to node the whole corridor
    graph.  Two positions closer than that are ONE node in the published topology, so a
    corridor within it of the trunk already shares a node with it in every sense the graph
    can express.  If this ever drifts to a number of its own, the tolerance that decides
    where a network discharges has been invented, which is the thing the rule forbids.
    """
    assert S.MEET_TOL_M == C.MH_SNAP_M
    assert S.MAIN_SNAP_M == S.MEET_TOL_M
    assert S.MEET_TOL_M != 5.0, ("5.0 m was the old project number chosen by eye; the "
                                 "tolerance must come from the merge radius")


def test_the_detour_bound_comes_from_the_built_network():
    """10_ASBUILT_CALIBRATION.md sec 1: detour ratio median 1.23, p90 2.26, <= 5 % above 4.0.

    A re-root that buys a lower outlet with a flow path past that bound is buying it with
    pipe nobody would build, so the bound is the built network's own and not a preference.
    """
    assert S.DETOUR_RATIO_MAX == 4.0


def test_the_below_outlet_threshold_is_the_engineers_own_words():
    """The defect is stated as "MORE THAN HALF their catchment BELOW the outlet"."""
    assert S.BELOW_OUTLET_FAIL_PCT == 50.0


# ==========================================================================================
# 2.  CUTTING THE CORRIDORS WHERE THEY MEET THE TRUNK
# ==========================================================================================

def _orient_for_cut(corridors, main_coords=((0.0, 0.0), (1000.0, 0.0))):
    """An `Orient` with just enough on it for `meet_main_pipe` to run.

    Built with `object.__new__` on purpose: `__init__` reads four files and a 5 m terrain
    grid, none of which says anything about whether a corridor is cut in the right place.
    """
    import geopandas as gpd
    from shapely.geometry import LineString, Point

    rows = []
    geoms = []
    node_geom = {}
    for cid, (us, ds, coords) in corridors.items():
        g = LineString(coords)
        geoms.append(g)
        rows.append(dict(CID=cid, US_NODE=us, DS_NODE=ds, LEN_M=g.length,
                         N_PLOT=10.0, Q_NEAR_M3D=5.0, Q_M3D=5.0,
                         SRC="test", CONFIDENCE="built"))
        node_geom[us] = Point(coords[0])
        node_geom[ds] = Point(coords[-1])
    cor = gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:32640")
    main = gpd.GeoDataFrame(
        {"X": [1]}, geometry=[LineString(main_coords)], crs="EPSG:32640")

    o = object.__new__(S.Orient)
    o.gpd = gpd
    o.cor = cor
    o.main = main
    o.node_geom = node_geom
    o.notes = []
    o.measure = lambda: None            # terrain resampling is not what is under test
    return o


def test_a_corridor_crossing_the_main_pipe_is_cut_at_the_crossing():
    """THE DEFECT ITSELF.  Both nodes are 100 m from the trunk; W11b would see neither."""
    o = _orient_for_cut({"A": ("n1", "n2", [(500.0, -100.0), (500.0, 100.0)])})
    o.meet_main_pipe()

    assert o.meet_splits == 1
    assert len(o.meet_nodes) == 1
    assert len(o.cor) == 2, "the crossing corridor must become two"
    assert set(o.meet_rows.KIND) == {"crosses"}
    # the node is ON the trunk
    nid = o.meet_nodes[0]
    assert abs(o.node_geom[nid].y - 0.0) < 1e-6
    assert abs(o.node_geom[nid].x - 500.0) < 1e-6
    # and the two halves meet there
    ends = set(o.cor.US_NODE) | set(o.cor.DS_NODE)
    assert nid in ends
    # NOTHING CROSSES ANY MORE
    from shapely.ops import unary_union
    main = unary_union(list(o.main.geometry))
    assert int(o.cor.geometry.crosses(main).sum()) == 0


def test_cutting_loses_no_length_no_plot_and_no_load():
    """ZERO SILENT DROPS.  A cut is a re-partition, not a deletion."""
    o = _orient_for_cut({
        "A": ("n1", "n2", [(500.0, -100.0), (500.0, 100.0)]),
        "B": ("n3", "n4", [(200.0, -40.0), (200.0, 60.0)]),
    })
    km0 = float(o.cor.LEN_M.sum())
    p0 = float(o.cor.N_PLOT.sum())
    q0 = float(o.cor.Q_M3D.sum())
    o.meet_main_pipe()
    assert abs(float(o.cor.LEN_M.sum()) - km0) < 1e-6
    assert abs(float(o.cor.N_PLOT.sum()) - p0) < 1e-6
    assert abs(float(o.cor.Q_M3D.sum()) - q0) < 1e-6
    # and the geometry still adds up to the same thing
    assert abs(float(o.cor.geometry.length.sum()) - km0) < 1e-6


def test_a_corridor_that_never_touches_but_passes_within_tolerance_is_still_cut():
    """397 arcs came within 3 m of the trunk where only 193 nodes did.

    Running a metre from the trunk and discharging somewhere else is the same defect as
    crossing it; the merge radius says the two positions are one node.
    """
    off = S.MEET_TOL_M / 2.0
    o = _orient_for_cut({"A": ("n1", "n2",
                               [(200.0, 50.0), (500.0, off), (800.0, 50.0)])})
    o.meet_main_pipe()
    assert o.meet_splits == 1
    assert set(o.meet_rows.KIND) == {"within_tol"}
    nid = o.meet_nodes[0]
    assert abs(o.node_geom[nid].x - 500.0) < 1.0, "cut at the point of CLOSEST approach"


def test_a_corridor_clear_of_the_main_pipe_is_left_alone():
    """The rule must not touch what it has no business touching."""
    o = _orient_for_cut({"A": ("n1", "n2", [(200.0, 50.0), (800.0, 50.0)])})
    o.meet_main_pipe()
    assert o.meet_splits == 0
    assert len(o.cor) == 1
    assert list(o.meet_nodes) == []


def test_a_meeting_point_on_a_corridor_end_mints_no_new_node():
    """The end node ALREADY meets the trunk; a second node inside the merge radius is
    exactly the duplicate chamber MH_SNAP_M exists to forbid."""
    o = _orient_for_cut({"A": ("n1", "n2", [(500.0, 0.0), (500.0, 200.0)])})
    o.meet_main_pipe()
    assert o.meet_splits == 0
    assert len(o.cor) == 1


def test_two_crossings_on_one_corridor_give_two_nodes():
    """A street that crosses the trunk twice discharges twice; one node would let half of
    it cross and grow past."""
    o = _orient_for_cut(
        {"A": ("n1", "n2", [(100.0, -50.0), (100.0, 50.0), (400.0, 50.0),
                            (400.0, -50.0), (700.0, -50.0)])})
    o.meet_main_pipe()
    assert len(o.meet_nodes) == 2
    assert len(o.cor) == 3
    from shapely.ops import unary_union
    assert int(o.cor.geometry.crosses(unary_union(list(o.main.geometry))).sum()) == 0


def test_a_corridor_running_along_the_trunk_is_cut_at_the_ENDS_not_shredded():
    """Collinear overlap is a real case - a street laid over the trunk alignment.

    A node at the MIDDLE of the overlap leaves half the stretch on the trunk on either side
    of it, and the next round cuts those in half again: the first draft of this shredded a
    708 m street into 16 pieces over 4 rounds.  Nodes at the two ENDS isolate the on-trunk
    stretch as one corridor whose two nodes are both outfalls, which is what it is.
    """
    o = _orient_for_cut({"A": ("n1", "n2", [(100.0, 40.0), (300.0, 0.0),
                                            (600.0, 0.0), (800.0, 40.0)])})
    o.meet_main_pipe()
    assert len(o.meet_nodes) == 2, "one node at each end of the collinear stretch"
    assert set(o.meet_rows.KIND) == {"along"}
    assert len(o.cor) == 3
    # and it converged: the middle piece is on the trunk with a node at each end
    assert int(o.meet_rounds.corridors_cut.sum()) == 1
    assert o.n_meet_off_node == 0


# ==========================================================================================
# 3.  RE-ROOTING TO THE LOWEST MEETING POINT
# ==========================================================================================

def _orient_for_reroot(z, edges, roots):
    """A bare `Orient` carrying only the arrays the re-rooting pass reads.

    `z` is the ground level per node; `edges` is a list of (u, v, length); `roots` the node
    indices that meet the Main Pipe.  Coordinates are laid out on a line at 100 m centres so
    the detour bound has something real to measure against.
    """
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
    # the solver's weights are only read to re-sum a tree's cost; length is enough here
    o.weights_used = dict(wf=o.L.copy(), wb=o.L.copy())
    o.notes = []
    return o


def _tree(o, parent):
    """A `Tree` from a parent map, using the corridor that joins each pair."""
    via = {}
    for child, par in parent.items():
        if par < 0:
            via[child] = -1
            continue
        cand = np.flatnonzero(((o.u == child) & (o.v == par)) |
                              ((o.u == par) & (o.v == child)))
        assert cand.size, f"no corridor between {child} and {par}"
        via[child] = int(cand[0])
    arcs = [e for e in via.values() if e >= 0]
    fwd = [bool(o.u[e] == c) for c, e in via.items() if e >= 0]
    return S.Tree(name="test", arc=np.asarray(arcs, np.int64),
                  fwd=np.asarray(fwd, bool), parent=dict(parent), via=via,
                  joins=np.asarray([c for c, p in parent.items() if p < 0], np.int64),
                  weight=0.0)


def test_below_outlet_km_measures_the_quantity_the_defect_is_stated_in():
    """Two nodes below their outfall, one above it; only the two count."""
    #   0 = the outfall at 100 m; 1 sits at 90 (below), 2 at 95 (below), 3 at 110 (above)
    o = _orient_for_reroot([100.0, 90.0, 95.0, 110.0],
                           [(1, 0, 100.0), (2, 1, 100.0), (3, 2, 100.0)], roots=[0])
    tr = _tree(o, {0: -1, 1: 0, 2: 1, 3: 2})
    o._paths(tr)
    km = o._below_outlet_km(tr, o._outfall)
    assert km == pytest.approx(0.200, abs=1e-9), \
        "the two arcs leaving nodes 1 and 2, 100 m each"


def test_a_branch_below_its_outfall_is_re_pointed_to_a_lower_one():
    """THE RULE.  A high outfall with a low catchment beside a low outfall it can reach."""
    #   node 0  root, ground 100  (the HIGH outfall the branching happened to pick)
    #   node 1  ground 90   drains to 0 today - it CLIMBS 10 m to get out
    #   node 2  ground 85   drains to 1
    #   node 3  root, ground 80  (the LOW outfall, one corridor away from node 2)
    z = [100.0, 90.0, 85.0, 80.0]
    edges = [(1, 0, 100.0), (2, 1, 100.0), (2, 3, 100.0)]
    o = _orient_for_reroot(z, edges, roots=[0, 3])
    tr = _tree(o, {0: -1, 1: 0, 2: 1, 3: -1})
    o._paths(tr)
    before = o._below_outlet_km(tr, o._outfall)
    assert before > 0

    tr2 = o.reroot_below_outfall(tr)
    o._paths(tr2)
    after = o._below_outlet_km(tr2, o._outfall)

    assert o.reroot_moved >= 1
    assert after < before
    assert after == pytest.approx(0.0, abs=1e-9)
    # node 2 now discharges at the LOW outfall, and node 1 follows it
    assert o._outfall[2] == 3 and o._outfall[1] == 3
    # and the pass published what it took away
    assert int(o.reroot_hist.moved.sum()) == o.reroot_moved


def test_re_rooting_can_only_take_away_never_make_it_worse():
    """The monotonicity argument, exercised on 40 random graphs rather than asserted.

    A move is legal only when the new outfall is at or below the moved node, and the node
    was below its old outfall - so the new outfall is strictly lower, and every arc in the
    subtree that was below its outlet is below the new one or better.
    """
    rng = np.random.default_rng(17)
    for trial in range(40):
        n = int(rng.integers(6, 14))
        z = np.round(rng.uniform(0.0, 40.0, n), 2)
        # a path graph plus a few chords, so there is always something to re-point onto
        edges = [(i, i + 1, 100.0) for i in range(n - 1)]
        for _ in range(int(rng.integers(1, 4))):
            a, b = sorted(rng.choice(n, 2, replace=False))
            if b - a > 1:
                edges.append((int(a), int(b), float(100.0 * (b - a))))
        roots = sorted(set(int(x) for x in rng.choice(n, 2, replace=False)))
        o = _orient_for_reroot(z, edges, roots)
        # a spanning in-tree by breadth-first search from the roots
        import collections
        adj = collections.defaultdict(list)
        for k, (a, b, _l) in enumerate(edges):
            adj[a].append(b)
            adj[b].append(a)
        parent = {r: -1 for r in roots}
        dq = collections.deque(roots)
        while dq:
            x = dq.popleft()
            for y in adj[x]:
                if y not in parent:
                    parent[y] = x
                    dq.append(y)
        if len(parent) < n:
            continue
        tr = _tree(o, parent)
        o._paths(tr)
        before = o._below_outlet_km(tr, o._outfall)
        tr2 = o.reroot_below_outfall(tr)
        o._paths(tr2)
        after = o._below_outlet_km(tr2, o._outfall)
        assert after <= before + 1e-9, f"trial {trial}: {before} -> {after}"
        # and it is still a forest
        assert o._cycle(tr2.parent) == []
        # and every node still has exactly one outlet
        assert len(tr2.via) == len(tr2.parent)


def test_a_lower_outfall_is_refused_when_the_detour_is_past_the_built_ratio():
    """A lower outlet 20 km away is not an answer; the built network's p90 detour is 2.26."""
    z = [100.0, 90.0, 85.0, 80.0]
    #   the corridor to the low root is 20,000 m long against a ~200 m straight line
    edges = [(1, 0, 100.0), (2, 1, 100.0), (2, 3, 20000.0)]
    o = _orient_for_reroot(z, edges, roots=[0, 3])
    tr = _tree(o, {0: -1, 1: 0, 2: 1, 3: -1})
    tr2 = o.reroot_below_outfall(tr)
    assert o.reroot_moved == 0
    o._paths(tr2)
    assert o._outfall[2] == 0, "it stays where it was, and the deficit is flagged not hidden"


def test_an_outfall_is_never_re_pointed():
    """An outfall IS the join onto the trunk.  Moving one would move the connection."""
    z = [100.0, 99.0, 80.0]
    edges = [(0, 1, 100.0), (1, 2, 100.0), (0, 2, 100.0)]
    o = _orient_for_reroot(z, edges, roots=[0, 2])
    tr = _tree(o, {0: -1, 1: 0, 2: -1})
    tr2 = o.reroot_below_outfall(tr)
    assert tr2.parent[0] == -1 and tr2.via[0] == -1
    assert set(int(x) for x in tr2.joins) == {0, 2}


def test_the_forest_survives_a_move_that_would_close_a_loop():
    """`_cycle` is the guard.  H15 is a forest and this pass may not be what breaks it."""
    # a two-cycle by hand: 1 -> 2 and 2 -> 1
    parent = {0: -1, 1: 2, 2: 1}
    cyc = S.Orient._cycle(parent)
    assert set(cyc) == {1, 2}
    # a clean tree has none
    assert S.Orient._cycle({0: -1, 1: 0, 2: 1, 3: 1}) == []
    # a long chain does not blow the stack
    long_chain = {0: -1}
    long_chain.update({i: i - 1 for i in range(1, 20000)})
    assert S.Orient._cycle(long_chain) == []


def test_rebuild_re_sums_the_weight_rather_than_carrying_it():
    """A weight that no longer matches its own tree is a number nobody can check."""
    z = [10.0, 9.0, 8.0]
    edges = [(1, 0, 100.0), (2, 1, 250.0)]
    o = _orient_for_reroot(z, edges, roots=[0])
    tr = _tree(o, {0: -1, 1: 0, 2: 1})
    tr.weight = 999999.0
    tr2 = o._rebuild(tr, dict(tr.parent), dict(tr.via))
    assert tr2.weight == pytest.approx(100.0 + 250.0 + S.JOIN_COST_M)
    assert tr2.arc.size == 2 and tr2.fwd.size == 2


def test_the_arc_direction_survives_a_rebuild():
    """`fwd` says the flow runs US_NODE -> DS_NODE as drawn.  Getting it backwards publishes
    a fall with the wrong sign, which is the class of quiet error W12 exists to stop."""
    z = [10.0, 9.0]
    edges = [(0, 1, 100.0)]                 # drawn 0 -> 1
    o = _orient_for_reroot(z, edges, roots=[1])
    tr = _tree(o, {1: -1, 0: 1})            # flow runs 0 -> 1, i.e. AS DRAWN
    assert bool(tr.fwd[0]) is True
    tr_rev = _tree(o, {0: -1, 1: 0})        # flow runs 1 -> 0, against the drawing
    assert bool(tr_rev.fwd[0]) is False


# ==========================================================================================
# 3b.  THE SUB-NETWORK TABLE - the low point, the connection, the offset, the share below
# ==========================================================================================

def _orient_for_subnets(z, edges, roots, d_main=None, relief=None):
    o = _orient_for_reroot(z, edges, roots)
    n = len(z)
    o.Q = np.full(len(edges), 10.0)
    # every root literally touches the trunk; everything else is far from it
    o.d_main = np.array([0.0 if i in set(roots) else 500.0 for i in range(n)], float)
    if d_main is not None:
        o.d_main = np.asarray(d_main, float)
    o.trunk_relief = np.zeros(n) if relief is None else np.asarray(relief, float)
    return o


def test_the_subnetwork_table_names_the_low_point_the_offset_and_the_share_below():
    """W11b published none of these, so nothing in the pipeline could say that 42 components
    discharged above their own catchment.

        node 0  root, ground 100   - the outfall
        node 1  ground 92, 100 m upstream of it
        node 2  ground 88, another 100 m up - THE TRUE LOW POINT, 200 m from the outlet
    """
    o = _orient_for_subnets([100.0, 92.0, 88.0],
                            [(1, 0, 100.0), (2, 1, 100.0)], roots=[0])
    tr = _tree(o, {0: -1, 1: 0, 2: 1})
    o._paths(tr)
    sn, nb = o.subnetworks(tr)

    assert len(sn) == 1
    r = sn.iloc[0]
    assert r.OUTFALL == "N000"
    assert r.LOW_NODE == "N002"
    assert r.LOW_Z == pytest.approx(88.0)
    assert r.HEAD_M == pytest.approx(12.0), "the outlet sits 12 m above its own low point"
    assert r.JOIN_OFF_M == pytest.approx(200.0), "along its own flow path, not as the crow flies"
    assert r.JOIN_MAIN == 1
    assert r.JOIN_WHY != "", "an offset that big has to say why"
    # both arcs leave a node below the outfall, so the whole catchment drains up to it
    assert r.BELOW_KM == pytest.approx(0.200)
    assert r.BELOW_PCT == pytest.approx(100.0)
    assert o.n_below_half == 1
    assert o.worst_head_m == pytest.approx(12.0)


def test_a_subnetwork_joining_AT_its_low_point_carries_no_explanation():
    """A column of reasons on every row hides the ones that matter."""
    o = _orient_for_subnets([80.0, 92.0, 96.0],
                            [(1, 0, 100.0), (2, 1, 100.0)], roots=[0])
    tr = _tree(o, {0: -1, 1: 0, 2: 1})
    o._paths(tr)
    sn, _nb = o.subnetworks(tr)
    r = sn.iloc[0]
    assert r.LOW_NODE == "N000" and r.HEAD_M == pytest.approx(0.0)
    assert r.JOIN_OFF_M == 0.0
    assert r.JOIN_WHY == ""
    assert r.BELOW_PCT == 0.0
    assert o.n_below_half == 0
    assert o.n_join_offset == 0


def test_the_reason_distinguishes_no_corridor_from_no_gravity():
    """Two different facts, and one of them is not fixable by moving the connection: a low
    point BELOW the trunk beside it cannot reach the trunk there at any offset."""
    o = _orient_for_subnets([100.0, 92.0, 88.0],
                            [(1, 0, 100.0), (2, 1, 100.0)], roots=[0],
                            relief=[0.0, 0.0, -4.0])          # the low point is under it
    tr = _tree(o, {0: -1, 1: 0, 2: 1})
    o._paths(tr)
    sn, _ = o.subnetworks(tr)
    assert "BELOW the Main Pipe" in sn.iloc[0].JOIN_WHY

    o2 = _orient_for_subnets([100.0, 92.0, 88.0],
                             [(1, 0, 100.0), (2, 1, 100.0)], roots=[0])
    tr2 = _tree(o2, {0: -1, 1: 0, 2: 1})
    o2._paths(tr2)
    sn2, _ = o2.subnetworks(tr2)
    assert "no corridor meets the Main Pipe" in sn2.iloc[0].JOIN_WHY


def test_an_outfall_with_nothing_draining_into_it_is_published_not_dropped():
    """W11b shipped 15 stations with nothing upstream and said nothing.  A sub-network of
    one node is a real fact about the layout and it goes on the table with KM = 0."""
    o = _orient_for_subnets([100.0, 92.0, 60.0],
                            [(1, 0, 100.0), (0, 2, 400.0)], roots=[0, 2])
    tr = _tree(o, {0: -1, 1: 0, 2: -1})
    o._paths(tr)
    sn, _ = o.subnetworks(tr)
    assert len(sn) == 2
    empty = sn[sn.KM <= 0]
    assert len(empty) == 1 and empty.iloc[0].OUTFALL == "N002"
    assert o.n_empty_outfall == 1


def test_more_smaller_subnetworks_is_the_intended_result():
    """"More subnetworks worth keeping the work clean, rather than monster useless
    subnetworks."  Two outfalls on the same chain split it in two."""
    z = [100.0, 95.0, 90.0, 85.0]
    edges = [(1, 0, 100.0), (2, 1, 100.0), (3, 2, 100.0)]
    one = _orient_for_subnets(z, edges, roots=[0])
    t1 = _tree(one, {0: -1, 1: 0, 2: 1, 3: 2})
    one._paths(t1)
    sn1, _ = one.subnetworks(t1)

    two = _orient_for_subnets(z, edges, roots=[0, 2])
    t2 = _tree(two, {0: -1, 1: 0, 2: -1, 3: 2})
    two._paths(t2)
    sn2, _ = two.subnetworks(t2)

    assert len(sn1) == 1 and len(sn2) == 2
    assert set(sn2.SUBNET) == {"S001", "S002"}
    # every node still belongs to exactly one sub-network - the split re-partitions, it
    # does not discard
    assert int(sn2.N_NODES.sum()) == int(sn1.N_NODES.sum()) == 4
    # the corridor from node 2 down to node 1 is no longer IN THE TREE, because node 2 now
    # discharges into the trunk instead of continuing past it.  That is the outfall rule
    # working: the corridor is not lost, it becomes a HEAD, which `heads()` publishes.
    assert sn1.KM.sum() - sn2.KM.sum() == pytest.approx(0.100)
    assert set(t1.arc) - set(t2.arc) != set(), \
        "exactly the corridor that used to cross the join has left the tree"


# ==========================================================================================
# 4.  THE DEFECT IS REPORTED EVERY RUN, WHATEVER THE ANSWER IS
# ==========================================================================================

def test_every_outfall_rule_number_has_a_manifest_row():
    """W11b had 42 badly-placed outfalls and nothing in the pipeline said so.  A number that
    is only in a console log is a number nobody can check next month."""
    src = open(S.__file__, encoding="utf-8").read()
    for item in ("MEET_TOL_M", "meet_corridors_cut", "meet_nodes_minted",
                 "arcs_crossing_main", "km_crossing_main", "reroot_branches_moved",
                 "subnets_below_half", "km_below_half", "km_below_outlet",
                 "worst_outlet_above_low_m", "subnets_joining_off_low",
                 "outfalls_with_no_catchment", "DETOUR_RATIO_MAX",
                 "BELOW_OUTLET_FAIL_PCT", "REROOT_PASSES"):
        assert f'("{item}"' in src, f"{item} is not a manifest row"


def test_the_subnetwork_table_carries_the_join_columns():
    """Per subnetwork: the low point, the connection point, the offset, and the share of the
    catchment lying BELOW the outlet.  All four, by name."""
    src = open(S.__file__, encoding="utf-8").read()
    for col in ("LOW_NODE", "LOW_Z", "LOW_DMAIN", "HEAD_M", "JOIN_OFF_M", "JOIN_WHY",
                "JOIN_MAIN", "BELOW_KM", "BELOW_PCT"):
        assert f"{col}=" in src, f"the subnets table does not publish {col}"


def test_join_off_m_fits_a_dbf_field_name():
    """s8 writes shapefiles and a name over 10 characters is silently truncated, which makes
    a field the auditor cannot find.  JOIN_OFFS_M, as first drafted, is 11."""
    for col in ("LOW_NODE", "LOW_Z", "LOW_DMAIN", "HEAD_M", "JOIN_OFF_M", "JOIN_WHY",
                "JOIN_MAIN", "BELOW_KM", "BELOW_PCT", "BELOW_OUT", "MEET_MAIN", "X_MAIN",
                "D_MAIN_M"):
        assert len(col) <= 10, f"{col} is {len(col)} characters"


def test_the_crossing_count_is_measured_from_geometry_not_read_back_from_its_own_column():
    """`verify` re-derives the crossing count from the shapes against the client's own Main
    Pipe file.  A check that reads back the column the build wrote is not a check."""
    src = open(S.__file__, encoding="utf-8").read()
    v = src[src.index("def verify()"):]
    assert "meets_without_a_node(g, main, buf, MEET_TOL_M)" in v
    assert "read_file(MAIN_PIPE)" in v
    assert "cannot run" in v, "an unrunnable below-outlet check must FAIL, not blank"
