"""PUMP SITING AS A SEARCH - the tests for s7_pumps' concept-stage revision.

THE DEFECT THIS FILE IS WRITTEN AGAINST, in one paragraph. W11b TRIGGERED a station wherever
a pipe crossed the depth cap. It designed 47, the levelling demanded 14, and 15 of the 47 had
NOTHING draining into them. Three separate faults: a trigger is not a decision; two functions
produced the count so the shipped file disagreed with itself; and nothing ever removed a
station once added.

Every test here runs on a SYNTHETIC graph built in this file - no terrain raster, no hazard
grid, no published GeoPackage - so the suite runs in milliseconds on a cold checkout and the
arithmetic can be checked by hand. The two networks are:

    _chain()   works - n1 - ... - n40, flat, 100 m spacing. The debt at node k is exactly
               k x S_min x 100, so the failure boundary is a closed form and the test asserts
               against the formula, not against a remembered number.

    _mesh()    the one that separates a SEARCH from a TRIGGER. Two branches leave the works,
               both fail at the same depth, and a single cross-link joins their far ends. The
               trigger rule promotes BOTH frontier nodes because it looks at the debt TREE,
               where the branches are strangers. The search places one, recomputes the field,
               and finds that the other branch now drains to it through the cross-link at a
               cost well inside the budget. One station instead of two - and on a real road
               network, which is meshed rather than a tree, that is the common case.

NO DESIGN NUMBER IS INVENTED HERE. The gradient is `criteria.table11(200)`, the budget is
`criteria.MAX_COVER - criteria.MIN_COVER_CROWN`, the rising-main cap is `criteria.FM_V_MAX`,
and the spacing and node counts are properties of the synthetic graph, chosen so the failure
boundary lands in the middle of it.
"""
from __future__ import annotations

import math

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, Point

import s7_pumps as S7
from w12 import contract
from w12.criteria import DEFAULT as C

CRS = "EPSG:32640"
SPACING_M = 100.0          # synthetic corridor length; a property of the test graph
FLAT_Z = 100.0             # flat ground, so the debt is exactly S_min x L per edge
BUDGET = C.MAX_COVER - C.MIN_COVER_CROWN          # G203-p33
S_MIN = C.table11(200)                            # G203-p29 Table 11, DN200


# ======================================================================================
# SYNTHETIC GRAPHS
# ======================================================================================

class _FlatTerrain:
    """The only thing `CorridorGraph` asks of a terrain: elevation at x, y."""

    def __init__(self, z=FLAT_Z):
        self.z = float(z)

    def elevation(self, x, y):
        return np.full(np.shape(x), self.z, dtype=float)


def _graph(nodes, edges, terrain=None):
    """Build a CorridorGraph from (id, x, y) nodes and (a, b) edges."""
    nd = gpd.GeoDataFrame(
        [{"NODE_ID": i, "X": float(x), "Y": float(y)} for i, x, y in nodes],
        geometry=[Point(float(x), float(y)) for _i, x, y in nodes], crs=CRS)
    pos = {i: (float(x), float(y)) for i, x, y in nodes}
    rows, geoms = [], []
    for a, b in edges:
        line = LineString([pos[a], pos[b]])
        rows.append({"US_NODE": a, "DS_NODE": b, "LEN_M": line.length, "Q_NEAR_M3D": 10.0})
        geoms.append(line)
    corr = gpd.GeoDataFrame(rows, geometry=geoms, crs=CRS)
    return S7.CorridorGraph(corr, nd, terrain or _FlatTerrain())


def _chain(n=40):
    """works at index 0, then a flat chain. debt(k) = k * S_MIN * SPACING_M."""
    nodes = [(f"n{k}", k * SPACING_M, 0.0) for k in range(n + 1)]
    edges = [(f"n{k}", f"n{k+1}") for k in range(n)]
    return _graph(nodes, edges)


def _mesh(arm=25):
    """Two PARALLEL streets from the works, joined by ONE short link at their far ends.

    a1..a{arm} and b1..b{arm} run side by side, SPACING_M apart, and a{arm}-b{arm} is a single
    SPACING_M cross-street. On the debt TREE the two arms never meet - each node's cheapest
    route is straight back to the works down its own street - so a frontier-trigger sees two
    independent failures and promotes both. In the GRAPH they are one loop, and a station on
    either arm is within a few hundred metres of every node on the other. That is an ordinary
    block of a road network, not a contrived case.
    """
    nodes = [("w", 0.0, SPACING_M / 2.0)]
    nodes += [(f"a{k}", k * SPACING_M, 0.0) for k in range(1, arm + 1)]
    nodes += [(f"b{k}", k * SPACING_M, SPACING_M) for k in range(1, arm + 1)]
    edges = [("w", "a1"), ("w", "b1")]
    edges += [(f"a{k}", f"a{k+1}") for k in range(1, arm)]
    edges += [(f"b{k}", f"b{k+1}") for k in range(1, arm)]
    edges += [(f"a{arm}", f"b{arm}")]
    return _graph(nodes, edges)


def _grid(n=24):
    """A grid town: n x n corridor nodes at SPACING_M centres, flat. The shape of Ibri's core,
    and the shape that separates a search from a trigger - a grid is MESHED, so a station
    placed on one street rescues the streets around it, which a debt tree cannot show."""
    nodes = [(f"n{i}_{j}", i * SPACING_M, j * SPACING_M)
             for i in range(n) for j in range(n)]
    edges = []
    for i in range(n):
        for j in range(n):
            if i + 1 < n:
                edges.append((f"n{i}_{j}", f"n{i+1}_{j}"))
            if j + 1 < n:
                edges.append((f"n{i}_{j}", f"n{i}_{j+1}"))
    return _graph(nodes, edges)


def _trigger_stations(g, terminals, s_min, budget, max_rounds=40):
    """W11b's rule, reproduced here so the comparison is against the real thing.

    It promotes the WHOLE frontier every round and never re-tests. This is not a strawman -
    it is `CorridorGraph.cascade()` as W11b shipped it, kept alive inside the test suite so
    the claim 'the search does better' has something to be better than.
    """
    sources = list(terminals)
    placed = []
    for _r in range(max_rounds):
        gf = S7.gravity_failure(g, sources, s_min, budget)
        if gf.n_failed == 0:
            break
        new = S7.frontier_candidates(g, gf)
        if not new:
            break
        placed.extend(new)
        sources = list(terminals) + placed
    return placed


# ======================================================================================
# 1. STEP (a) - WHERE GRAVITY GENUINELY FAILS, and nothing placed while finding out
# ======================================================================================

def test_the_failed_set_is_the_closed_form_and_no_station_is_placed():
    """On flat ground a pipe at the Table-11 minimum sinks S_MIN x L per span, so node k
    arrives with k x S_MIN x SPACING_M of debt. The boundary is arithmetic, not a memory."""
    g = _chain(40)
    gf = S7.gravity_failure(g, [g.idx["n0"]], S_MIN, BUDGET)
    k_fail = math.floor(BUDGET / (S_MIN * SPACING_M)) + 1
    for k in range(41):
        i = g.idx[f"n{k}"]
        assert gf.debt[i] == pytest.approx(k * S_MIN * SPACING_M, abs=1e-9)
        assert bool(gf.failed[i]) is (k >= k_fail), f"node {k}"
    assert gf.n_failed == 41 - k_fail
    # (a) is a statement about the ground. It contains no stations at all.
    assert gf.summary()["orphan"] == 0
    assert not hasattr(gf, "stations")


def test_a_node_with_no_route_to_a_terminal_is_an_orphan_not_a_pumping_problem():
    """Concept rule 7 - FLAG, DO NOT SOLVE. An unreachable component is a CONNECTIVITY
    finding with a size; rolling it into the station count would hide it."""
    nodes = [("w", 0.0, 0.0), ("a", 100.0, 0.0), ("x", 9000.0, 9000.0), ("y", 9100.0, 9000.0)]
    g = _graph(nodes, [("w", "a"), ("x", "y")])
    gf = S7.gravity_failure(g, [g.idx["w"]], S_MIN, BUDGET)
    assert gf.summary()["orphan"] == 2
    assert gf.n_failed == 0                      # orphans are NOT counted as failures
    assert S7.frontier_candidates(g, gf) == []   # and they generate no candidate site


# ======================================================================================
# 2. STEP (b) - A SEARCH, NOT A TRIGGER. The claim, measured.
# ======================================================================================

def test_the_search_needs_fewer_stations_than_the_trigger_on_a_meshed_network():
    """THE HEADLINE TEST. Same graph, same physics, same budget - two answers.

    The trigger promotes both frontier nodes because the debt TREE keeps the two arms apart.
    The search places one, RECOMPUTES, and discovers the far arm now drains to it across the
    cross-link. That rediscovery is the whole difference, and it is why one station per round
    is not merely a slower version of the same algorithm."""
    g = _mesh(25)
    t = [g.idx["w"]]
    trig = _trigger_stations(g, t, S_MIN, BUDGET)
    sites, gf, _trades, _rounds = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
    assert len(trig) == 2, f"the trigger should promote both frontier nodes, got {trig}"
    assert len(sites) == 1, f"the search should need one station, got {len(sites)}"
    assert gf.n_failed == 0, "and it must actually solve the problem, not just place fewer"


def test_the_search_covers_the_whole_failed_set_or_says_what_is_left():
    """A search that placed fewer stations and left nodes failing would not be better, it
    would be incomplete. Both networks: nothing left over."""
    for g in (_chain(40), _mesh(25)):
        t = [g.idx["n0"]] if "n0" in g.idx else [g.idx["w"]]
        sites, gf, _tr, _ro = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
        assert gf.n_failed == 0, f"{len(sites)} sites left {gf.n_failed} nodes failing"


def test_every_round_shrinks_the_failed_set_so_the_search_terminates():
    """Termination is structural, not a guess: the chosen site is itself failed and becomes a
    zero-debt source. The round log has to show it, or the guard is doing the work."""
    g = _chain(120)
    _sites, _gf, _tr, rounds = S7.search_sites(g, [g.idx["n0"]], S_MIN, BUDGET, [""] * g.n)
    real = [r for r in rounds if r["round"] != "GUARD"]
    assert real, "no rounds recorded"
    for r in real:
        assert r["failed_after"] < r["failed_before"], r
    assert all(r["round"] != "GUARD" for r in rounds), "the guard fired - that is a bug"


def test_the_round_guard_fires_only_when_something_is_still_failing():
    """A network that needs exactly `max_rounds` stations and gets them is SOLVED. Reporting
    that as a guard hit would be a false alarm on a real answer, and a guard that cries wolf
    is a guard people switch off."""
    g = _chain(120)
    t = [g.idx["n0"]]
    full, gf_full, _tr, rounds_full = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
    assert gf_full.n_failed == 0
    assert all(r["round"] != "GUARD" for r in rounds_full)
    # exactly enough rounds: solved, and still no guard row
    _s, gf_exact, _t2, rounds_exact = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n,
                                                      max_rounds=len(full))
    assert gf_exact.n_failed == 0
    assert all(r["round"] != "GUARD" for r in rounds_exact), (
        "the guard fired on a solved network - that is a false alarm")
    # one round short: NOT solved, and the run must say so rather than report a count
    _s2, gf_short, _t3, rounds_short = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n,
                                                       max_rounds=max(1, len(full) - 1))
    assert gf_short.n_failed > 0
    guard = [r for r in rounds_short if r["round"] == "GUARD"]
    assert guard and "FLOOR, not an answer" in guard[0]["NOTE"]


def test_a_candidate_is_scored_on_what_it_captures_not_on_where_the_cap_fell():
    """`subtree_within` is the capture score. On a chain a station at the frontier captures
    everything above it that is within one budget of it - countable by hand."""
    g = _chain(60)
    gf = S7.gravity_failure(g, [g.idx["n0"]], S_MIN, BUDGET)
    kids = g.children_of(gf.par)
    p = g.idx["n30"]
    nodes, km = g.subtree_within(kids, gf.par, gf.debt, p, BUDGET)
    span = math.floor(BUDGET / (S_MIN * SPACING_M))          # spans reachable from the site
    assert len(nodes) == span + 1, (len(nodes), span)        # the site plus `span` above it
    assert km == pytest.approx(span * SPACING_M / 1000.0, abs=1e-9)


def test_the_capture_score_never_over_counts():
    """It is computed on the debt TREE, so on a mesh it can only UNDER-count - the extra
    rescue is realised when the field is recomputed. Under-counting is the safe direction for
    a greedy that is comparing candidates; over-counting would let a site win on capture it
    does not have."""
    g = _mesh(25)
    gf = S7.gravity_failure(g, [g.idx["w"]], S_MIN, BUDGET)
    kids = g.children_of(gf.par)
    for p in S7.frontier_candidates(g, gf):
        nodes, _km = g.subtree_within(kids, gf.par, gf.debt, p, BUDGET)
        for i in nodes:
            assert gf.debt[i] - gf.debt[p] <= BUDGET + 1e-9


# ======================================================================================
# 3. (d) WHERE "FEWEST STATIONS" AND "SHORTEST MAIN" CONFLICT - both numbers, always
# ======================================================================================

def _site(node, cover_km, cover_n, main_m, lift_m):
    s = S7.Site(node, list(range(cover_n)), cover_km, set(), lift_m, main_m, node + 1, [1])
    return s


def test_a_trade_between_capture_and_main_length_is_recorded_with_both_numbers():
    """Philosophy sec 6: 'where they conflict - a big catchment whose nearest gravity point
    is far - state the trade with both numbers rather than resolving it silently.'"""
    big = _site(1, cover_km=10.0, cover_n=100, main_m=2000.0, lift_m=8.0)
    near = _site(2, cover_km=9.5, cover_n=95, main_m=300.0, lift_m=6.0)
    pick, trade = S7.choose_site([big, near], cover_tol=0.9)
    assert pick.node == 2, "inside the band, the shorter main wins"
    assert trade is not None, "and the trade must be RECORDED, not swallowed"
    assert trade["cover_km_given_up"] == pytest.approx(0.5)
    assert trade["cover_chambers_given_up"] == 5
    assert trade["main_m_saved"] == pytest.approx(1700.0)
    assert "FEWEST STATIONS vs SHORTEST MAIN" in trade["NOTE"]


def test_outside_the_band_capture_wins_and_there_is_nothing_to_trade():
    """A site capturing half as much cannot buy its way in with a short main - manning is
    86 % of the cost of a station and it does not care how far the main runs."""
    big = _site(1, cover_km=10.0, cover_n=100, main_m=2000.0, lift_m=8.0)
    small = _site(2, cover_km=2.0, cover_n=20, main_m=50.0, lift_m=1.0)
    pick, trade = S7.choose_site([big, small], cover_tol=0.9)
    assert pick.node == 1
    assert trade is None


def test_at_a_tolerance_of_one_the_rule_is_pure_maximum_coverage():
    """COVER_TOL = 1.0 removes the main length from the decision entirely. That is the end of
    the sensitivity the run publishes, and it must behave exactly that way."""
    big = _site(1, cover_km=10.0, cover_n=100, main_m=9000.0, lift_m=8.0)
    near = _site(2, cover_km=9.999, cover_n=99, main_m=10.0, lift_m=1.0)
    pick, trade = S7.choose_site([big, near], cover_tol=1.0)
    assert pick.node == 1 and trade is None


def test_the_tuned_number_is_published_as_a_sensitivity_not_chosen_quietly():
    """COVER_TOL is the only tuned number in the stage. The run reruns the whole search at
    each tolerance and publishes stations against total main length, so a reader can see what
    the choice bought."""
    g = _mesh(25)
    rows = S7.cover_tol_sensitivity(g, [g.idx["w"]], S_MIN, BUDGET, [""] * g.n)
    assert [r["cover_tol"] for r in rows] == list(S7.COVER_TOL_SCAN)
    for r in rows:
        assert r["failed_left"] == 0, "every tolerance must still solve the problem"
        assert {"stations", "total_main_m", "captured_km", "trades"} <= set(r)


# ======================================================================================
# 4. (c) THE PRUNE, AND THE ONE FUNCTION THAT COUNTS STATIONS
# ======================================================================================

def test_a_station_the_others_made_unnecessary_is_removed_and_counted():
    """INHERITANCE ROW 4. Hand the pruner the trigger's two-station answer on the mesh: one
    of them is redundant, and the stage must say so rather than publish both.

    W8 knew this on 2026-08-21 and cleared its pump flags every pass. W11b lost the line and
    published three stations where the built network has none."""
    g = _mesh(25)
    t = [g.idx["w"]]
    trig = _trigger_stations(g, t, S_MIN, BUDGET)
    assert len(trig) == 2
    gf = S7.gravity_failure(g, t, S_MIN, BUDGET)
    kids = g.children_of(gf.par)
    sites = []
    for p in trig:
        nodes, km = g.subtree_within(kids, gf.par, gf.debt, p, BUDGET)
        sites.append(S7.Site(p, nodes, km, set(), 0.0, 100.0, None, []))
    keep, removed = S7.prune_redundant(g, sites, t, S_MIN, BUDGET)
    assert len(keep) == 1, "one of the two was redundant"
    assert len(removed) == 1
    assert "REDUNDANT" in removed[0]["WHY"]
    # and the survivors still solve it - a prune that breaks the design is not a prune
    gf2 = S7.gravity_failure(g, t + [s.node for s in keep], S_MIN, BUDGET)
    assert gf2.n_failed == 0


def test_a_station_with_nothing_draining_into_it_is_removed_by_name():
    """15 of W11b's 47 had nothing draining into them. Blocking, not a warning: the pruner
    removes it with the reason on the row, and `contract.STATIONS.N_SUBNET` refuses it a
    second time if one ever reaches the layer."""
    g = _chain(40)
    t = [g.idx["n0"]]
    empty = S7.Site(g.idx["n5"], [g.idx["n5"]], 0.0, set(), 0.0, 100.0, None, [])
    real = S7.Site(g.idx["n22"], list(range(20)), 1.8, {"S01"}, 2.0, 100.0, None, [])
    keep, removed = S7.prune_redundant(g, [empty, real], t, S_MIN, BUDGET)
    whys = " ".join(r["WHY"] for r in removed)
    assert "NOTHING DRAINS INTO IT" in whys
    assert all(s.node != empty.node for s in keep)


def test_the_search_never_produces_a_station_with_an_empty_catchment():
    """The pruner is the belt; this is the brace. A site is only ever chosen because it
    captures failed catchment, so an empty one should never be born."""
    for g in (_chain(80), _mesh(25)):
        t = [g.idx["n0"]] if "n0" in g.idx else [g.idx["w"]]
        sites, _gf, _tr, _ro = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
        for s in sites:
            assert s.cover_n >= 1 and s.cover_km >= 0.0
            assert not (s.cover_n <= 1 and s.cover_km <= 0.0), (
                "a site capturing nothing but itself reached the design")


def test_one_function_produces_the_station_count_and_prints_its_funnel():
    """INHERITANCE ROW 10. W11b's levelling demanded 14 and its pump stage designed 47, and
    the shipped file carried both. W10 had SEVEN counts in circulation. There is exactly one
    funnel and it accounts for every station that leaves it."""
    f = S7.station_funnel(83, 14, 12, source="test", removed=69, refused=2)
    assert f["N0_considered"] == 83 and f["N1_demanded"] == 14 and f["N2_published"] == 12
    assert f["N0_considered"] - f["N1_demanded"] == f["pruned"], "pruning must account for N0-N1"
    assert f["N1_demanded"] - f["N2_published"] == f["refused"], "refusals must account for N1-N2"
    frame = S7.funnel_frame(f)
    assert set(frame.STEP) >= {"N0_considered", "N1_demanded", "N2_published", "pruned",
                               "refused"}


def test_the_funnel_is_the_only_place_a_station_count_is_computed():
    """A second counter is how the two numbers diverged. `build()` must READ the funnel for
    the count it returns rather than calling len() on the frame a second time."""
    import inspect
    src = inspect.getsource(S7.build)
    assert '"n_stations": funnel[' in src, (
        "build() must return the funnel's own number - `\"n_stations\": funnel[\"N2_published\"]"
        "` - not a fresh len(). Two counters is how 14 and 47 both reached the shipped file.")
    assert '"n_stations": len(' not in src


# ======================================================================================
# 5. (c/e) THE RISING MAIN - nearest gravity, and the 2.5 m/s cap that is not 3.0
# ======================================================================================

def test_the_rising_main_cap_is_the_force_main_number_and_not_the_gravity_one():
    """G203-p50 sec 8.1 for a rising main; G203-p27 sec 4.2.2.2 for a gravity sewer. They are
    different clauses about different pipes and this project has conflated them before -
    inheritance row 9 names it as a bug that shipped."""
    assert C.FM_V_MAX == 2.5
    assert C.V_MAX == 3.0
    assert C.FM_V_MAX < C.V_MAX
    src = __import__("inspect").getsource(S7.verify)
    assert "CRIT.FM_V_MAX" in src, "verify() must read the constant, never type the number"
    for typo in ("<= 3.0", "< 3.0", "> 3.0", ">= 3.0", "= 3.0", "V_MAX = 2.5"):
        assert typo not in src, (
            f"a velocity threshold is typed as a literal ({typo!r}) instead of read from "
            "criteria - that is inheritance row 9, which shipped once already")


def test_a_rising_main_over_the_cap_fails_verify(tmp_path):
    """The check has to BITE, not merely exist. A main at 2.9 m/s is legal for a gravity
    sewer and illegal for a force main, which is exactly the confusion the cap guards."""
    gpkg = tmp_path / "W12_pumps.gpkg"
    st = gpd.GeoDataFrame(
        [dict(NODE_UID="N0000001", Q_DUTY_LS=50.0, RM_EDGE="E0000001", ST_TYPE="Type 1",
              LAND_M2=60.0, FLOOD_LV=1.0, N_SUBNET=2, CATCH_KM=7.4, DS_TYPE="manhole")],
        geometry=[Point(0.0, 0.0)], crs=CRS)
    line = LineString([(0.0, 0.0), (0.0, 100.0)])
    rm = gpd.GeoDataFrame(
        [dict(EDGE_UID="E0000001", DN=200, LEN_M=line.length, V_DUTY_MS=2.9, V_MIN_MS=1.0,
              DS_TYPE="manhole")],
        geometry=[line], crs=CRS)
    st.to_file(gpkg, layer="stations", driver="GPKG")
    rm.to_file(gpkg, layer="rising_mains", driver="GPKG")
    v = S7.verify(gpkg)
    named = {c["check"]: c["pass"] for c in v["checks"]}
    cap = [k for k in named if "2.5 m/s" in k]
    assert cap and named[cap[0]] is False, "2.9 m/s must fail the FORCE MAIN cap"
    assert v["pass"] is False


def test_a_station_with_nothing_draining_into_it_fails_the_published_file(tmp_path):
    """Requirement (f): BLOCKING, not a warning. It should never be written - and if it is,
    the file must not pass."""
    gpkg = tmp_path / "W12_pumps.gpkg"
    st = gpd.GeoDataFrame(
        [dict(NODE_UID="N0000001", Q_DUTY_LS=50.0, RM_EDGE="E0000001", ST_TYPE="Type 1",
              LAND_M2=60.0, FLOOD_LV=1.0, N_SUBNET=0, CATCH_KM=0.0)],
        geometry=[Point(0.0, 0.0)], crs=CRS)
    line = LineString([(0.0, 0.0), (0.0, 100.0)])
    rm = gpd.GeoDataFrame(
        [dict(EDGE_UID="E0000001", DN=200, LEN_M=line.length, V_DUTY_MS=1.5, V_MIN_MS=1.0,
              DS_TYPE="manhole")],
        geometry=[line], crs=CRS)
    st.to_file(gpkg, layer="stations", driver="GPKG")
    rm.to_file(gpkg, layer="rising_mains", driver="GPKG")
    v = S7.verify(gpkg)
    named = {c["check"]: c["pass"] for c in v["checks"]}
    hit = [k for k in named if "nothing draining into it" in k]
    assert hit and named[hit[0]] is False
    assert v["pass"] is False
    # and the contract refuses it independently, so two mechanisms have to fail to ship one
    with pytest.raises(contract.ContractError, match="NOTHING DRAINS INTO"):
        contract.validate(st.drop(columns=["DS_TYPE"], errors="ignore"), "stations",
                          strict=True)


def test_the_discharge_type_is_measured_and_may_only_be_manhole_or_stp():
    """Concept rule 6 needs the share of mains ending at the works to be a NUMBER on the
    layer. The vocabulary is the contract's, so a third value cannot be invented here."""
    assert set(contract.DS_TYPE) == {"manhole", "stp"}


def test_the_discharge_candidates_never_include_the_stations_own_catchment():
    """THE LOOP GUARD. A node can be inside the budget precisely BECAUSE this station is
    there; discharging into it would send the flow straight back to the pump, and H15 makes
    the network a forest."""
    g = _chain(40)
    t = [g.idx["n0"]]
    sites, gf, _tr, _ro = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
    assert sites, "the chain must demand at least one station"
    nodes = [s.node for s in sites]
    owner = S7.serving_station(g, gf.par, nodes)
    n_series = S7.stations_in_series(g, gf.par, nodes)
    for s in sites:
        for c in S7._discharge_candidates(g, gf, s.node, owner, n_series):
            assert owner[c["node"]] != s.node, "a station discharging into its own catchment"
            assert bool(gf.served[c["node"]]), "and it must discharge where gravity resumes"


# ======================================================================================
# 6. (g) WHAT A STATION PUBLISHES - and what it must not
# ======================================================================================

def test_no_motor_size_and_no_life_cycle_cost_survive_the_publish():
    """Switched off at concept (criteria.CONCEPT_OFF). `w12.pumping` computes both inside its
    own blocking checks and s7 does not own that module, so the columns are dropped HERE, by
    name, with the capability recorded - a declared drop, not an omission."""
    row = {"Q_DUTY_LS": 50.0, "LIFT_M": 6.2, "MOTOR_KW": 15.0, "LCC_OMR": 400000.0,
           "HEAD_M": 8.1, "PCT_MAN": 86.0, "PCT_NRG": 0.4, "KWH_YR": 1000.0,
           "NPSHA_M": 9.0, "NPSHR_MAX": 4.0, "WELL_M3": 4.5}
    out = S7._drop_switched_off(row)
    assert set(out) == {"Q_DUTY_LS", "LIFT_M", "WELL_M3"}
    for col in ("MOTOR_KW", "LCC_OMR", "HEAD_M"):
        assert col in contract.BANNED_FIELDS, (
            f"{col} is dropped here AND banned by the contract - two mechanisms, because a "
            "validator catching it is not the same as the stage meaning it")


def test_every_dropped_column_names_a_real_capability_or_a_real_ban():
    """A drop register that pointed at a capability nobody declared would be decoration. Each
    entry has to resolve - to a `criteria.CONCEPT_OFF` key, or to `contract.BANNED_FIELDS`."""
    for col, (cap, why) in S7.CONCEPT_DROP.items():
        assert why.strip(), col
        assert cap in C.CONCEPT_OFF or cap == "contract.BANNED_FIELDS", (col, cap)
    tbl = S7.concept_off_table()
    assert list(tbl.columns) == ["COLUMN", "CAPABILITY", "WHY", "COMES_BACK"]
    assert len(tbl) == len(S7.CONCEPT_DROP)
    # every switched-off capability says what brings it back - deferred, not forgotten
    for _i, r in tbl.iterrows():
        if r.CAPABILITY in C.CONCEPT_OFF:
            assert r.COMES_BACK.strip(), r.COLUMN


def test_the_station_name_follows_the_one_grammar_and_a_pump_is_a_seam():
    """Concept rule 8. A station is NOT inside a subnetwork - it is a seam between them - so
    its name carries no S-token and SUBNET is blank by rule, not by omission."""
    n = contract.concept_name("I", "pump", seq=2)
    m = contract.concept_name("I", "main", seq=2)
    assert (n, m) == ("I-PMP02", "I-P02")
    for name, kind in ((n, "pump"), (m, "main")):
        p = contract.parse_name(name)
        assert p is not None and p["kind"] == kind and not p["sub"]


def test_a_station_takes_the_letter_of_the_first_town_downstream_of_it():
    """"Elements outside any town take the letter of the first town DOWNSTREAM of them, so
    naming runs AFTER connectivity is known." That is why the station's town comes from its
    discharge chamber and not from where it stands."""
    nodes = pd.DataFrame([
        {"NODE_UID": "N1", "TOWN": "", "DS_NODE": "N2"},
        {"NODE_UID": "N2", "TOWN": "", "DS_NODE": "N3"},
        {"NODE_UID": "N3", "TOWN": "D", "DS_NODE": ""},
    ])
    assert S7.town_of_node(nodes, "N1") == "D"
    assert S7.town_of_node(nodes, "N3") == "D"
    assert S7.town_of_node(None, "N1") == ""            # legal mid-pipeline; blank, not wrong


def test_a_rising_main_discharges_into_a_chamber_that_actually_exists():
    """`contract.RISING_MAINS.refs` points DS_NODE at `nodes.NODE_UID`. An id that resolves to
    no row schedules nothing - the CROSS_ID defect in another coat - and the corridor graph and
    the design use different id spaces, so the match has to be by coordinate."""
    g = _chain(5)
    node = g.idx["n3"]
    design = pd.DataFrame([
        {"NODE_UID": "N0000042", "X": float(g.x[node]) + 3.0, "Y": float(g.y[node])},
        {"NODE_UID": "N0000099", "X": float(g.x[node]) + 900.0, "Y": float(g.y[node])},
    ])
    assert S7._discharge_uid(g, design, node, 1) == "N0000042"
    # nothing within reach -> a MINTED placeholder, out of the station range, never a wrong id
    far = pd.DataFrame([{"NODE_UID": "N0000099", "X": 9e5, "Y": 9e5}])
    minted = S7._discharge_uid(g, far, node, 1)
    assert minted not in set(far.NODE_UID)
    assert minted == contract.NODE_UID_FMT.format(900001)
    assert S7._discharge_uid(g, None, node, 1) == minted
    # and the tolerance is short of half the built network's median chamber spacing (29.77 m),
    # so a match can never jump to the neighbouring chamber
    assert S7.DISCHARGE_MATCH_M < 29.77


def test_a_cycle_in_the_downstream_chain_cannot_hang_the_naming():
    """Defensive, and cheap: DS_NODE comes from another stage and a loop there must not turn
    a naming pass into an infinite one."""
    nodes = pd.DataFrame([
        {"NODE_UID": "N1", "TOWN": "", "DS_NODE": "N2"},
        {"NODE_UID": "N2", "TOWN": "", "DS_NODE": "N1"},
    ])
    assert S7.town_of_node(nodes, "N1") == ""


def test_the_catchment_is_measured_and_no_kilometre_is_counted_twice():
    """The catchment split partitions the network. Counting a corridor for two stations is
    the same defect that put 1,233 m3/d out of W10 and inflated an infiltration total by
    counting every upstream kilometre once per downstream reach."""
    g = _grid(24)
    t = [g.idx["n0_0"]]
    sites, _gf, _tr, _ro = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
    gf = S7.gravity_failure(g, t + [s.node for s in sites], S_MIN, BUDGET)
    cat = S7.catchment_of(g, gf, sites, [""] * g.n)
    total = sum(v["catch_km"] for v in cat.values())
    assert total <= g.L.sum() / 1000.0 + 1e-6, (
        f"the stations between them own {total:.2f} km of a {g.L.sum()/1000:.2f} km network")
    for v in cat.values():
        assert v["catch_km"] > 0.0 and v["n_subnet"] > 0
        assert v["subnet_basis"] == "upstream branches (no SUBNET yet)"


def test_the_subnet_count_says_which_basis_it_used():
    """N_SUBNET is 'how many subnetworks drain into this station'. With a SUBNET column it is
    the count of labels; without one it is the count of upstream branches - the same physical
    question asked of the data that exists. Which of the two was used is on the row, never
    left to be guessed (inheritance row 2: a check that cannot run is a failure, not a
    blank)."""
    g = _grid(24)
    t = [g.idx["n0_0"]]
    sites, _gf, _tr, _ro = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
    gf = S7.gravity_failure(g, t + [s.node for s in sites], S_MIN, BUDGET)
    labels = [f"S{(i % 4) + 1:02d}" for i in range(g.n)]
    cat = S7.catchment_of(g, gf, sites, labels)
    for v in cat.values():
        assert v["subnet_basis"] == "SUBNET labels"
        assert 1 <= v["n_subnet"] <= 4


def test_a_station_that_owns_nothing_after_the_measurement_is_still_removed():
    """The scored capture is computed on the debt TREE and the catchment is MEASURED once
    every station is in. On a mesh they can differ, so the measurement gets the last word -
    a second pass that can take away what a first pass added (inheritance row 4)."""
    d_ok = S7.StationDemand("PS001", 1, 0.0, 0.0, 100.0, 90.0, 20.0, 8.0, 100.0,
                            "cap", "terrain", "derived", "", n_subnet=2, catch_km=4.0)
    d_bad = S7.StationDemand("PS002", 2, 0.0, 0.0, 100.0, 90.0, 20.0, 8.0, 100.0,
                             "cap", "terrain", "derived", "", n_subnet=0, catch_km=0.0)
    keep, removed = S7.drop_empty_catchments([d_ok, d_bad])
    assert [d.ident for d in keep] == ["PS001"]
    assert len(removed) == 1 and "NOTHING DRAINS INTO IT" in removed[0]["WHY"]


def test_a_list_from_the_levels_stage_is_re_tested_and_pruned():
    """THE DIRECT FIX FOR 's7 READS A PRE-PRUNE LIST'. W11b's levelling demanded 14 and its
    pump stage designed 47. The design is the authority on DUTY FLOW; it is not the authority
    on whether the station is needed, and that is a statement about the ground this stage has
    just computed."""
    g = _chain(40)
    t = [g.idx["n0"]]
    gf = S7.gravity_failure(g, t, S_MIN, BUDGET)
    # one real demand at the frontier, one the ground does not need, and a duplicate of it
    def _d(ident, node):
        return S7.StationDemand(ident, g.idx[node], *[float(v) for v in
                                                      (g.x[g.idx[node]], g.y[g.idx[node]])],
                                100.0, 90.0, 20.0, 8.0, 100.0, "cap", "manual", "derived",
                                "levels stage")
    demands = [_d("PS001", "n22"), _d("PS002", "n30"), _d("PS003", "n30")]
    kept, removed = S7.demands_retested(g, gf, demands, [""] * g.n)
    whys = " ".join(r["WHY"] for r in removed)
    assert "DUPLICATE" in whys, "two stations at one node is one station"
    assert len(kept) < len(demands), "the list must be pruned, not passed through"
    for d in kept:
        assert d.catch_km > 0.0 and d.n_subnet > 0
        assert "re-tested by s7" in d.provenance


def test_only_a_cap_station_may_be_pruned_on_depth():
    """The mirror image of the defect this revision fixes. The cap-and-veto ladder has four
    rungs and this stage's depth-debt field can only see the first: a VETO station exists
    because a chamber cannot be maintained, a COMMISSIONING one because it makes a package
    independently buildable - NAMA's own 5A-1 is the measured example. Pruning either
    'because gravity reaches' would delete a decision made on evidence s7 does not hold."""
    g = _chain(40)
    t = [g.idx["n0"]]
    gf = S7.gravity_failure(g, t, S_MIN, BUDGET)

    def _d(ident, node, why):
        i = g.idx[node]
        return S7.StationDemand(ident, i, float(g.x[i]), float(g.y[i]), 100.0, 90.0,
                                20.0, 8.0, 100.0, why, "manual", "derived", "levels stage")

    demands = [_d("PS001", "n22", "cap"), _d("PS002", "n30", "cap"),
               _d("PS003", "n12", "commissioning")]
    kept, removed = S7.demands_retested(g, gf, demands, [""] * g.n)
    idents = {d.ident for d in kept}
    assert "PS003" in idents, "a commissioning station was pruned on depth grounds"
    assert any(r["node"] == g.idx["n30"] for r in removed), "the spare cap station survived"
    # and an EMPTY non-cap station is kept for the engineer to argue about, not deleted
    d_veto = S7.StationDemand("PS004", 1, 0.0, 0.0, 100.0, 90.0, 20.0, 8.0, 100.0,
                              "veto", "manual", "derived", "", n_subnet=0, catch_km=0.0)
    keep2, removed2 = S7.drop_empty_catchments([d_veto])
    assert [d.ident for d in keep2] == ["PS004"] and not removed2


def test_the_search_beats_the_trigger_by_the_measured_factor_on_a_grid_town():
    """SCALE, AND THE CLAIM STATED AS A NUMBER. A 24x24 grid at 100 m centres is 110 km of
    flat street - the shape of Ibri's core. Measured 2026-09-06: the trigger promotes 25
    stations and the search needs 4.

    The bound is a RATIO, not a station count, so the test survives a change to the graph and
    still fails if the search stops searching."""
    g = _grid(24)
    t = [g.idx["n0_0"]]
    trig = _trigger_stations(g, t, S_MIN, BUDGET)
    sites, gf, _tr, _ro = S7.search_sites(g, t, S_MIN, BUDGET, [""] * g.n)
    print(f"\n    [siting] {g.L.sum()/1000:.0f} km grid: trigger {len(trig)} stations, "
          f"search {len(sites)} - a factor of {len(trig)/max(len(sites),1):.1f}")
    assert gf.n_failed == 0
    assert len(sites) * 3 <= len(trig), (
        f"the search should need at most a third of the trigger's stations; got "
        f"{len(sites)} against {len(trig)}")


def test_the_search_runs_at_network_scale_inside_a_stated_bound():
    """A RUNTIME BOUND, with the measured time printed either way. The 26-minute defect was
    inside every bound anyone had written down, because nobody had written one down.

    10,000 nodes and 19,800 edges is the size of the real corridor network (9,599 nodes,
    1,819 km). Measured 2.0 s on this machine on 2026-09-06; the bound is 5x that."""
    from conftest import Budget
    g = _grid(100)
    with Budget("s7 search at network scale (10,000 nodes)", 10.0):
        sites, gf, _tr, _ro = S7.search_sites(g, [g.idx["n0_0"]], S_MIN, BUDGET, [""] * g.n)
    assert gf.n_failed == 0 and len(sites) > 0


# ======================================================================================
# 7. THE CONTRACT THE STAGE NOW HAS TO MEET
# ======================================================================================

def test_the_fields_the_stage_writes_are_the_fields_the_contract_asks_for():
    """Requirement (g), checked against the schema rather than against a memory of it."""
    st = {f.name for f in contract.STATIONS.fields}
    rm = {f.name for f in contract.RISING_MAINS.fields}
    assert {"NAME", "TOWN", "SUBNET", "GRD_M", "INV_M", "LIFT_M", "Q_DUTY_LS", "WELL_M3",
            "N_SUBNET", "CATCH_KM"} <= st
    assert {"NAME", "TOWN", "SUBNET", "DS_TYPE", "LEN_M", "RETENT_M"} <= rm
    # and the switched-off pair must NOT be in the schema at all
    assert not ({"MOTOR_KW", "LCC_OMR"} & (st | rm))


def test_a_station_row_assembled_the_way_build_assembles_it_passes_the_contract():
    """END TO END on the ROW, without the rasters. `w12.pumping` designs a station, s7 drops
    the switched-off columns and adds the ones the concept stage requires, and the result has
    to satisfy `contract.STATIONS` - because 'the stage fails its own contract' is an open
    defect on the export stage and it is not going to be one here.

    FLOOD_LV is given a value here ONLY so the rest of the row can be checked. In a real run
    it is NaN and that is the declared blocking gap: G203-p38 sec 7.2 needs a 1:50 flood
    LEVEL and this project holds hazard CLASSES. A check that cannot run is a failure, not a
    blank, and it is published as one."""
    from w12 import pumping

    S = pumping.design_station(
        ident="PS001", x=0.0, y=0.0, ground_m=330.0, invert_in_m=322.0,
        q_peak_ls=60.0, q_adf_ls=20.0, main_length_m=420.0, discharge_ground_m=333.0,
        n_prop=430.0, why="cap", n_summits=1, n_low_points=1, grids=None)
    row = S7._drop_switched_off(S.station_row())
    row.update({"NODE_UID": "N0000001", "NODE_REF": "PS001-PS",
                "NAME": "I-PMP01", "TOWN": "I", "SUBNET": "",
                "FLOOD_LV": 320.0, "INV_M": 322.0, "N_SUBNET": 2, "CATCH_KM": 7.4,
                "RM_EDGE": "E0000001", "COMM_PT": 1,
                "SRC": "dwg_road", "CONFIDENCE": "derived", "STAGE": "s7_pumps",
                "PACKAGE": "", "PHASE": 0})
    st = gpd.GeoDataFrame([row], geometry=[Point(0.0, 0.0)], crs=CRS)
    contract.validate(st, "stations", stage="test", strict=True)
    contract.assert_named(st, "stations", stage="test")

    mrow = S7._drop_switched_off(S.main_row())
    line = LineString([(0.0, 0.0), (0.0, 420.0)])
    mrow.update({"EDGE_UID": "E0000001", "US_NODE": "N0000001", "DS_NODE": "N0900001",
                 "STATION": "N0000001", "NAME": "I-P01", "TOWN": "I", "SUBNET": "",
                 "DS_TYPE": "manhole", "LEN_M": line.length,
                 "SRC": "dwg_road", "CONFIDENCE": "derived", "STAGE": "s7_pumps",
                 "PACKAGE": "", "PHASE": 0})
    rm = gpd.GeoDataFrame([mrow], geometry=[line], crs=CRS)
    contract.validate(rm, "rising_mains", stage="test", strict=False)   # structure complete
    contract.assert_named(rm, "rising_mains", stage="test")
    # The one VALUE check this row cannot pass is the KNOWN structural finding, and it is not
    # a defect in this stage: one main can only span a flow ratio of 2.5 / 0.75 = 3.33, and on
    # this project peak / design-minimum runs 8 to 13. No diameter fixes it; the resolutions
    # are G203's own (staged mains, twin mains, a scheduled flush). The test pins it so a
    # DIFFERENT failure cannot hide behind it.
    try:
        contract.validate(rm, "rising_mains", stage="test", strict=True)
    except contract.ContractError as e:
        msg = str(e)
        assert "DESIGN MINIMUM flow" in msg, msg
        assert msg.count("\n\n") <= 3, f"a second, unexplained problem is hiding here:\n{msg}"
    # and nothing switched off got through on either layer
    assert not (set(st.columns) & set(S7.CONCEPT_DROP))
    assert not (set(rm.columns) & set(S7.CONCEPT_DROP))


def test_the_stage_writes_every_new_required_column():
    """A required column the stage forgets is a layer the auditor cannot check, and
    `validate()` blocks on it. Read out of the source so it survives refactoring."""
    import inspect
    src = inspect.getsource(S7.build)
    for col in ("NAME", "TOWN", "SUBNET", "INV_M", "N_SUBNET", "CATCH_KM", "DS_TYPE"):
        assert f'"{col}"' in src, f"build() never writes {col}"
