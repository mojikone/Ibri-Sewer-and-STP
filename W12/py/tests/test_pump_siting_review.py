"""ADVERSARIAL REVIEW OF THE PUMP-SITING REWRITE - the five defects it shipped with.

`test_pump_siting.py` is the author's own suite and it passes. This file is the review: each
test below is a case the author's suite does not build, and each one FAILED against
`s7_pumps.py` as first written on 2026-09-06. They are kept so the same five cannot come back.

    1. THE PRUNE COULD NOT FIRE.  `prune_redundant()` removed a station only when deleting it
       left the network with NOTHING failing. That is true of a search that has just solved
       the network and false of everything else - in particular false of the list the LEVELS
       stage hands over, which was built against the design's own diameters while this stage
       charges the DN200 minimum to all 1,819 km. Two adjacent, plainly redundant stations
       survived the prune untouched. The prune is the whole of the "s7 reads a pre-prune list"
       fix, so a prune that cannot fire is the defect wearing the fix's clothes.

    2. A REMOVAL THAT STRANDED A CATCHMENT SAID NOTHING.  The "nothing drains into it" pass
       deleted a station with no re-test at all, so a failed cul-de-sac that the search HAD
       covered went back to failing and the funnel counted the deletion as a prune - which
       reads as "a neighbour absorbed it". Inheritance row 4 licenses a later pass to TAKE
       AWAY; it does not license a removal that is never re-tested.

    3. THE OUTFALL FILTER BROKE ON A DTYPE.  `legal_terminals()` compared IS_OUTFALL as
       TEXT ('1.0' != '1'), so a float column - what pandas gives the moment one row is null -
       matched nothing, the function fell through to the WORKS-ALONE degraded basis, and the
       run reported a station count built on 0.31 % of the network while saying "no published
       outfall layer was readable". That is inheritance row 13, on the one input that decides
       every number in the stage.

    4. `stations_in_series()` RETURNED ZERO FOR THE WHOLE NETWORK.  A station is a zero-debt
       SOURCE, so its `par` is -1 and a station is never a member of the walked chain; the
       root was scored 0 whatever it was. On a 120-node chain with five stations the function
       said 0 at every node, including nodes whose flow passes four of them. Rung 1 of
       `pumping.DISCHARGE_LADDER` - "fewest stations in series", which the stage says it
       MINIMISES FIRST - was ranking on a constant, and COMM_PT shipped 1 on every row. A
       published column constant where it should vary is inheritance row 22.

    5. A MOVED STATION KEPT SOMEBODY ELSE'S INVERT.  A wet site is moved up to SITE_SEARCH_M
       to dry ground and X, Y and GRD_M move with it - INV_M did not. INV_M is the bottom of
       LIFT_M, so a station published a ground level from one place and an invert from a
       point up to 500 m away, and the difference went into the head, the pump and everything
       downstream of them.

Everything here runs on the synthetic graphs in `test_pump_siting.py` - no raster, no hazard
grid, no published GeoPackage - so it stays a millisecond suite on a cold checkout.
"""
from __future__ import annotations

import inspect

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

import s7_pumps as S7
from w12.criteria import DEFAULT as C

from test_pump_siting import _graph, BUDGET, S_MIN, SPACING_M       # noqa: E402

CRS = "EPSG:32640"


# ======================================================================================
# helpers - two shapes the author's suite does not build
# ======================================================================================

def _two_arms(n=40):
    """Two long flat streets out of the works. A station on one arm can never rescue the
    other, so a set covering only ONE arm leaves the network failing - which is the ordinary
    state of any list this stage did not itself produce."""
    nodes = [("w", 0.0, 0.0)]
    nodes += [(f"a{k}", k * SPACING_M, 0.0) for k in range(1, n + 1)]
    nodes += [(f"b{k}", 0.0, k * SPACING_M) for k in range(1, n + 1)]
    edges = [("w", "a1"), ("w", "b1")]
    edges += [(f"a{k}", f"a{k+1}") for k in range(1, n)]
    edges += [(f"b{k}", f"b{k+1}") for k in range(1, n)]
    return _graph(nodes, edges)


def _spur():
    """A short solved street with one long dead-end spur off its end. The spur is a failed
    LEAF: a station there captures itself and nothing else, which is exactly the shape the
    'nothing drains into it' pass deletes."""
    nodes = [(f"n{k}", k * SPACING_M, 0.0) for k in range(6)]
    nodes += [("spur", 5 * SPACING_M, 4000.0)]
    edges = [(f"n{k}", f"n{k+1}") for k in range(5)] + [("n5", "spur")]
    return _graph(nodes, edges)


def _sites_at(g, gf, nodes):
    kids = g.children_of(gf.par)
    out = []
    for nd in nodes:
        cn, km = g.subtree_within(kids, gf.par, gf.debt, nd, gf.budget)
        out.append(S7.Site(nd, cn, km, set(), 0.0, 100.0, None, []))
    return out


# ======================================================================================
# 1. THE PRUNE MUST FIRE ON A NETWORK THAT IS NOT FULLY SOLVED
# ======================================================================================

def test_a_redundant_station_is_pruned_even_when_the_network_is_not_fully_solved():
    """Two stations one chamber apart on the same arm; the OTHER arm is left unsolved.

    The second station is redundant on any reading - deleting it changes nothing about which
    nodes fail. The original test ('nothing fails after the deletion') could never be met
    here, because the second arm fails whatever you do, so the prune removed NOTHING. That is
    the state of every design run: the levels stage's list is not this stage's search answer.
    """
    g = _two_arms()
    term = [g.idx["w"]]
    gf = S7.gravity_failure(g, term, S_MIN, BUDGET)
    assert gf.n_failed > 0, "the test graph must have failing nodes for this to mean anything"

    sites = _sites_at(g, gf, [g.idx["a20"], g.idx["a21"]])
    keep, removed = S7.prune_redundant(g, sites, term, S_MIN, BUDGET)

    assert len(removed) == 1, (
        "a station one chamber from another on the same arm is redundant and must be removed "
        "even though the second arm is still failing. Removed: " + repr(removed))
    assert "REDUNDANT" in removed[0]["WHY"]
    assert len(keep) == 1


def test_the_prune_never_removes_a_station_that_is_carrying_something():
    """The other half of the same rule: a removal that would strand a node is refused.

    One station per arm, both needed. Neither may go, and the fact that the network as a whole
    is NOT solved (both arms run past the reach of one station) must not tempt the looser test
    into deleting one."""
    g = _two_arms()
    term = [g.idx["w"]]
    gf = S7.gravity_failure(g, term, S_MIN, BUDGET)
    sites = _sites_at(g, gf, [g.idx["a21"], g.idx["b21"]])
    base = S7.gravity_failure(g, term + [s.node for s in sites], S_MIN, BUDGET)

    keep, removed = S7.prune_redundant(g, sites, term, S_MIN, BUDGET)
    assert removed == [], "both stations carry catchment; neither is redundant"
    after = S7.gravity_failure(g, term + [s.node for s in keep], S_MIN, BUDGET)
    assert not bool((after.failed & ~base.failed).any()), (
        "the prune introduced a failure that was not there before it ran")


def test_the_prune_still_solves_a_network_the_search_solved():
    """The old behaviour, kept: where the search DID reach zero failures, pruning may not
    put any back."""
    g = _two_arms()
    term = [g.idx["w"]]
    sites, gf, _tr, _rd = S7.search_sites(g, term, S_MIN, BUDGET, [""] * g.n)
    assert gf.n_failed == 0
    keep, _removed = S7.prune_redundant(g, sites, term, S_MIN, BUDGET)
    after = S7.gravity_failure(g, term + [s.node for s in keep], S_MIN, BUDGET)
    assert after.n_failed == 0, "pruning re-broke a network the search had solved"


# ======================================================================================
# 2. A REMOVAL THAT STRANDS A CATCHMENT SAYS SO
# ======================================================================================

def test_removing_a_station_that_captures_nothing_names_what_it_strands():
    """The failed cul-de-sac. The search covers it; the 'nothing drains into it' pass deletes
    it, because a station serving one chamber cannot be published (N_SUBNET = 0 is refused by
    `contract.STATIONS`). Deleting it is defensible. Deleting it SILENTLY is not - concept
    rule 7 is flag, do not solve, and the funnel would otherwise book it as a prune, which
    reads as 'a neighbour absorbed it'."""
    g = _spur()
    term = [g.idx["n0"]]
    sites, gf, _tr, _rd = S7.search_sites(g, term, S_MIN, BUDGET, [""] * g.n)
    assert gf.n_failed == 0 and len(sites) == 1
    assert sites[0].cover_n == 1 and sites[0].cover_km == 0.0

    keep, removed = S7.prune_redundant(g, sites, term, S_MIN, BUDGET)
    assert keep == [] and len(removed) == 1
    r = removed[0]
    assert "NOTHING DRAINS INTO IT" in r["WHY"]
    assert r["stranded_nodes"] == 1, (
        "the removal leaves one corridor node with no gravity route and no station, and the "
        "row must carry that number: " + repr(r))
    assert "LEFT WITH NO GRAVITY ROUTE" in r["WHY"]

    after = S7.gravity_failure(g, term, S_MIN, BUDGET)
    assert after.n_failed == 1, "and `nodes_still_failing` is where the reader finds it again"


def test_every_removal_row_carries_a_stranded_count():
    """Not one row, every row: a `pruned` table where the column is sometimes absent cannot
    be read as a funnel."""
    g = _two_arms()
    term = [g.idx["w"]]
    sites, _gf, _tr, _rd = S7.search_sites(g, term, S_MIN, BUDGET, [""] * g.n)
    sites = sites + _sites_at(g, S7.gravity_failure(g, term, S_MIN, BUDGET), [g.idx["a21"]])
    _keep, removed = S7.prune_redundant(g, sites, term, S_MIN, BUDGET)
    assert removed, "the duplicated site must be removed"
    for r in removed:
        assert "stranded_nodes" in r, repr(r)


# ======================================================================================
# 3. THE OUTFALL FILTER AND THE DTYPE IT WAS WRITTEN AGAINST
# ======================================================================================

@pytest.mark.parametrize("cast,label", [(float, "float64"), (int, "int64"), (bool, "bool")])
def test_the_outfall_filter_survives_the_dtype_the_writer_used(tmp_path, cast, label):
    """IS_OUTFALL = 1 must be found whether the column arrives as 1, 1.0 or True.

    A float column is not exotic: pandas produces one from a single null, and a GeoPackage
    written from a float frame gives one every time. The text comparison the stage shipped
    with matched none of them, and the failure is SILENT - it degrades to the works-only
    basis, which the module itself says makes the station count meaningless."""
    from test_pump_siting import _chain
    g = _chain(10)
    rows = [{"NODE_ID": str(n), "IS_OUTFALL": cast(k == 5),
             "X": float(g.x[k]), "Y": float(g.y[k])}
            for k, n in enumerate(g.nodes.NODE_ID.values)]
    df = gpd.GeoDataFrame(pd.DataFrame(rows),
                          geometry=[Point(g.x[k], g.y[k]) for k in range(g.n)], crs=CRS)
    p = tmp_path / f"design_{label}.gpkg"
    df.to_file(p, layer="nodes", driver="GPKG")

    term, basis = S7.legal_terminals(g, design_gpkg=p, orient_gpkg=tmp_path / "absent.gpkg")
    assert g.idx["n5"] in term, (
        f"the IS_OUTFALL=1 row was not found with the column stored as {label}. basis: {basis}")
    assert "DEGRADED" not in basis, (
        "the stage fell through to the works-only basis with a perfectly readable outfall "
        "layer in front of it: " + basis)


def test_the_degraded_basis_is_still_reached_when_there_really_is_no_outfall_layer(tmp_path):
    """The fallback must stay - a fix that makes the filter always match would hide the case
    it exists for."""
    from test_pump_siting import _chain
    g = _chain(10)
    term, basis = S7.legal_terminals(g, design_gpkg=tmp_path / "a.gpkg",
                                     orient_gpkg=tmp_path / "b.gpkg")
    assert len(term) == 1 and "DEGRADED" in basis


# ======================================================================================
# 4. STATIONS IN SERIES - the rung the ladder minimises first
# ======================================================================================

def _long_chain(n=120):
    nodes = [(f"n{k}", k * SPACING_M, 0.0) for k in range(n + 1)]
    return _graph(nodes, [(f"n{k}", f"n{k+1}") for k in range(n)])


def test_stations_in_series_counts_the_station_a_chain_ends_at():
    """A station is a zero-debt SOURCE, so it is a ROOT of the debt tree and never a member
    of the walked chain. Scoring the root 0 made the answer 0 everywhere - a constant, on the
    quantity that is supposed to keep one station from pumping into another."""
    g = _long_chain()
    term = [g.idx["n0"]]
    sites, gf, _tr, _rd = S7.search_sites(g, term, S_MIN, BUDGET, [""] * g.n)
    st = [s.node for s in sites]
    assert len(st) >= 3, "the chain must need several stations for this test to bite"

    owner = S7.serving_station(g, gf.par, st)
    ns = S7.stations_in_series(g, gf.par, st)

    # every node owned by a STATION passes at least that station on the way out
    for i in range(g.n):
        if owner[i] >= 0 and owner[i] != i and bool(np.isin(owner[i], st)):
            assert ns[i] >= 1, (
                f"node {g.nodes.NODE_ID.values[i]} drains into station "
                f"{g.nodes.NODE_ID.values[owner[i]]} and the function says it passes "
                f"{ns[i]} stations")
    # a node draining straight to the works passes none
    assert ns[g.idx["n1"]] == 0
    # and a station does not count itself
    for i in st:
        assert ns[i] == 0


def test_stations_in_series_is_not_a_constant():
    """The bug's signature, tested directly. Inheritance row 22: a published quantity that is
    constant where it should vary is a fabrication - and COMM_PT on the stations layer is
    exactly `stations_in_series == 0`."""
    g = _long_chain()
    term = [g.idx["n0"]]
    sites, gf, _tr, _rd = S7.search_sites(g, term, S_MIN, BUDGET, [""] * g.n)
    ns = S7.stations_in_series(g, gf.par, [s.node for s in sites])
    assert len(set(ns.tolist())) > 1, (
        "stations_in_series returned one value for the whole network on a chain that needs "
        f"{len(sites)} stations. Rung 1 of DISCHARGE_LADDER is then ranking on a constant.")


def test_a_discharge_into_another_stations_catchment_is_ranked_below_a_clean_one():
    """The consequence, on the ladder itself. `pumping.rank_discharge` sorts on
    stations_in_series FIRST; with the count stuck at zero it could not tell a clean discharge
    from one that lands in a cascade. Philosophy sec 6 (2026-09-06): a station never pumps
    into another station, and a cascade is a symptom of bad siting at every separation."""
    from w12 import pumping
    g = _long_chain()
    term = [g.idx["n0"]]
    sites, gf, _tr, _rd = S7.search_sites(g, term, S_MIN, BUDGET, [""] * g.n)
    st = [s.node for s in sites]
    owner = S7.serving_station(g, gf.par, st)
    ns = S7.stations_in_series(g, gf.par, st)

    top = sites[-1]
    cands = S7._discharge_candidates(g, gf, top.node, owner, ns, k_targets=12)
    assert cands
    ranked = pumping.rank_discharge(cands)
    series = [c["stations_in_series"] for c in ranked]
    assert series == sorted(series), (
        "rank_discharge must put the candidates that pass fewest stations first: " +
        repr(series))


# ======================================================================================
# 5. A MOVED STATION AND ITS INVERT
# ======================================================================================

def test_a_moved_station_charges_the_extra_gravity_run_to_its_invert():
    """Source-level, deliberately, and the reason is stated. The move lives inside `build()`,
    which needs the corridor GeoPackage, the 0.5 m terrain VRT and the hazard grids - none of
    which exist on a cold checkout - so there is no honest way to exercise it as a unit here.
    What CAN be held is the invariant: the three lines that move a station must move its
    invert with them. INV_M is the bottom of LIFT_M (`pumping.design_station` sets
    stop_level = invert_in_m - live_depth - 0.30), so a station whose ground came from one
    node and whose invert came from another up to SITE_SEARCH_M away publishes a head that is
    wrong by the ground difference between the two."""
    src = inspect.getsource(S7.build)
    i = src.find("d.x, d.y, d.ground_m = float(g.x[j]), float(g.y[j]), float(g.z[j])")
    assert i > 0, "the move block has been rewritten - re-read this test before deleting it"
    window = src[i:i + 1600]
    assert "d.invert_in_m" in window, (
        "a station is moved to dry ground and its X, Y and GRD_M follow, but INV_M does not. "
        "It is the bottom of LIFT_M.")
    assert "s_min * moved_m" in window, (
        "the extra gravity run must be charged at the Table 11 minimum for its bore "
        "(G203-p29), the same arithmetic depth_debt() charges every corridor - not left to a "
        "reader to notice from MOVED_M")


def test_the_screen_arrival_invert_is_a_declared_assumption():
    """`demands_from_sites` writes INV_M = ground - MAX_COVER on every screen station, which
    makes GRD_M - INV_M a CONSTANT 12.00 m. That is defensible as a screen and indefensible
    as an undeclared one, so it belongs in the stage's own ASSUMPTIONS registry beside
    SCREEN_DN - the reader has to be able to see that the depth is asserted, not measured."""
    tbl = S7._assumption_table()
    assert "SCREEN_ARRIVAL_INVERT" in set(tbl.ITEM), sorted(tbl.ITEM)
    note = tbl.loc[tbl.ITEM == "SCREEN_ARRIVAL_INVERT", "NOTE"].iloc[0]
    assert "MAX_COVER" in note and "CONSTANT" in note


# ======================================================================================
# 6. THE CASCADE IS COUNTED RATHER THAN ASSUMED AWAY
# ======================================================================================

def test_the_cascade_count_is_a_published_number():
    """Philosophy sec 6 was revised on 2026-09-06 to refuse a station pumping into another
    station, and it REVERSED the standing 'cascade within 1.5 km' rule. `contract` refuses
    only a main whose DS_TYPE is a station, so a main that discharges to a manhole whose flow
    still passes a station satisfies the letter and not the substance. The stage may not
    resolve that silently in either direction: it counts them."""
    g = _long_chain(40)
    term = [g.idx["n0"]]
    gf = S7.gravity_failure(g, term, S_MIN, BUDGET, "test")
    empty = gpd.GeoDataFrame(columns=["NODE_UID"], geometry=[], crs=CRS)
    prov = S7._provenance("test", g, gf, empty, empty, [], (), None, (),
                          [{"IDENT": "PS001", "STATIONS_IN_SERIES_AT_LEAST": 2,
                            "MAIN_M": 900.0}])
    row = prov[prov.ITEM == "mains_landing_in_a_cascade"]
    assert len(row) == 1, sorted(prov.ITEM)
    assert int(row.VALUE.iloc[0]) == 1
    assert "LOWER BOUND" in row.NOTE.iloc[0], (
        "the count cannot see past the first station, and a number whose limitation is not "
        "on the row will be quoted as though it had none")


def test_the_cascade_table_is_printed_by_report():
    """A table written into the GeoPackage and never printed is a table nobody reads."""
    src = inspect.getsource(S7.report)
    assert '"cascades"' in src, "add `cascades` to the tables --report walks"


# ======================================================================================
# 7. UNITS - N_PROP and the constant whose name lies about it
# ======================================================================================

def test_the_property_count_uses_the_per_property_flow_and_does_not_double_it():
    """`criteria.PLOT_QADF_M3D` is named for a PLOT and is defined per PROPERTY -
    OCCUPANCY x WWG_LCD / 1000, unit published by s5_flows as m3/d/property, and
    `contract`'s own example builds a plot's load as PLOT_QADF_M3D x PROPS_PER_PLOT. So a
    measured m3/d divided by it is already a property count, and the inherited
    `* PROPS_PER_PLOT` (W11b s7_pumps:475) inflated N_PROP by 45.6 % on every screen station.

    N_PROP is not decoration: `criteria.peak_factor` holds the factor at 1.0 below
    PF_HOLD_PROPERTIES and switches to Merrimack above it, so an inflated count can change a
    station's peak flow, its ST_TYPE, its pump count and its G203-p43 land band.
    """
    g = _two_arms(20)
    term = [g.idx["w"]]
    sites, gf, _tr, _rd = S7.search_sites(g, term, S_MIN, BUDGET, [""] * g.n)
    cat = S7.catchment_of(g, gf, sites, [""] * g.n)
    for s in sites:
        c = cat[s.node]
        expect = c["q_adf_m3d"] / C.PLOT_QADF_M3D
        assert abs(c["n_prop"] - expect) < 1e-9, (
            f"N_PROP is {c['n_prop']:.1f} where the per-property flow gives {expect:.1f} - "
            f"a factor of {c['n_prop'] / max(expect, 1e-9):.3f}")


def test_the_per_property_constant_really_is_per_property():
    """The premise of the test above, asserted against criteria itself so that a change
    there fails HERE rather than silently re-introducing the factor."""
    assert abs(C.PLOT_QADF_M3D - C.OCCUPANCY * C.WWG_LCD / 1000.0) < 1e-12
    assert C.PROPS_PER_PLOT > 1.0, (
        "if properties per plot were ever 1.0 this test would pass with the bug in place")
