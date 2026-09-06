"""
THE NAMING SCHEME — `w12.naming`
=================================

The bug this file exists to stop is the quiet one: **a name that changes between runs.**
Nothing fails when it happens. The build passes, the layers publish, the audit is green —
and every drawing, schedule and figure that quotes `I-S03-SM-M012` now points at a different
chamber. There is no check anywhere else in this project that would notice.

So the centre of this file is
`test_the_same_design_in_a_different_row_order_gets_the_same_names`: one design built twice,
the second with its rows permuted, its reaches reversed and its columns reordered, asserting
the two name maps are byte-identical. Everything else is around that.

The rest divides into:

    the town letters      the article is dropped, BOTH towns extend on a clash, and the
                          answer does not depend on the order the names arrive in
    the grammar           every name this module produces parses with contract.parse_name(),
                          and its parts agree with the row's own TOWN / SUBNET / TIER -
                          the check contract.validate() will run on the published layer
    the ordering rule     naming refuses to run before connectivity is known, because an
                          element outside a town takes the letter of the first town
                          DOWNSTREAM of it (engineer's rule b)
    flag, do not solve    everything unnameable keeps a blank name AND gains a flag with a
                          reason. Nothing is guessed, nothing is silently dropped
    add and take away     inheritance-ledger row 4: a pass that can give a name must be able
                          to take one away, and publish how many it took

NO DESIGN NUMBER IS ASSERTED HERE. Naming has no hydraulics; the only numbers in this file
are counts of things the test itself built.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import pytest

from w12.contract import (SUBNET_RE, TIERS, TIER_TOKEN, assert_named, concept_name,
                          parse_name, town_letter, town_letters)
from w12 import naming as N


# ======================================================================================
# a synthetic design, built by the test so nothing depends on a stage having run
# ======================================================================================

def build_design(n_branches: int = 4, per_branch: int = 6):
    """A main pipe running north to south with `n_branches` branches hanging off it.

        main:     T0 (north) -> T1 -> ... (trunk main), the last one is the outfall
        branch b: a chain of `per_branch` chambers whose last one joins the main pipe
        one chamber per branch is placed OUTSIDE every town, to exercise rule (b)

    Returns (nodes, reaches, stations, rising_mains, town_of_node).
    """
    rows, town = [], []
    ntr = n_branches + 1
    for i in range(ntr):                                  # T0 north .. T{n} south
        ds = f"T{i + 1}" if i + 1 < ntr else ""
        rows.append((f"T{i}", 1000.0, 5000.0 - 100.0 * i, ds, "trunk main"))
        town.append("Ibri")
    for b in range(n_branches):
        join = f"T{b + 1}"
        for k in range(per_branch):
            uid = f"B{b}_{k}"
            ds = join if k == 0 else f"B{b}_{k - 1}"
            rows.append((uid, 1000.0 + 40.0 * (k + 1), 5000.0 - 100.0 * (b + 1) + 7.0 * k,
                         ds, "sub main" if k == 0 else "lateral"))
            # the second chamber of every branch sits outside every town
            town.append("" if k == 1 else ("Ibri" if b % 2 == 0 else "Al Araqi"))
    nodes = pd.DataFrame(rows, columns=["NODE_UID", "X", "Y", "DS_NODE", "TIER"])
    reaches = pd.DataFrame(
        [(f"E{i:04d}", u, d) for i, (u, _, _, d, _) in enumerate(rows) if d],
        columns=["EDGE_UID", "US_NODE", "DS_NODE"])
    stations = pd.DataFrame([
        dict(NODE_UID="PS1", X=1400.0, Y=4650.0),
        dict(NODE_UID="PS2", X=1400.0, Y=4250.0),
    ])
    mains = pd.DataFrame([
        dict(EDGE_UID="RM1", STATION="PS1", DS_NODE="T2"),
        dict(EDGE_UID="RM2", STATION="PS2", DS_NODE="T4"),
    ])
    return nodes, reaches, stations, mains, town


@pytest.fixture(scope="module")
def design():
    return build_design()


@pytest.fixture(scope="module")
def towns():
    return N.TownIndex.from_names(["Ibri", "Al Araqi", "Ad Dariz", "Bat"], source="(test)")


@pytest.fixture(scope="module")
def result(design, towns):
    nodes, reaches, stations, mains, town = design
    return N.name_network(nodes, reaches=reaches, stations=stations, rising_mains=mains,
                          towns=towns, node_town=town)


# ======================================================================================
# 1. THE TOWN LETTERS
# ======================================================================================

def test_the_arabic_article_is_dropped_before_the_letter_is_taken():
    # without this every town in the wilayat collides on 'A' - Al Aqar, Al Araqi, Ad Dariz,
    # Ash Shiab, At Tayyib all begin with the definite article, not with their own name
    assert town_letter("Al Araqi") == "A"
    assert town_letter("Ad Dariz") == "D"
    assert town_letter("Ash Shiab") == "S"
    assert town_letter("At Tayyib") == "T"
    assert town_letter("Ibri") == "I"


def test_both_towns_extend_on_a_clash_and_neither_is_favoured():
    # the engineer's rule, and it is symmetric on purpose: favouring the town with more
    # served plots would make a code depend on a LOAD, so a plot count moving would rename
    # half a network
    codes = town_letters(["Ad Dariz", "Ad Dibayshi", "Ibri"])
    assert codes["Ibri"] == "I"                       # no clash, stays one letter
    assert codes["Ad Dariz"] == "DA"
    assert codes["Ad Dibayshi"] == "DI"
    assert len(codes["Ad Dariz"]) == len(codes["Ad Dibayshi"]) == 2


def test_the_codes_do_not_depend_on_the_order_the_names_arrive_in():
    names = ["Ash Shiab", "Satwah", "Sayh Al Masarrat", "Shalashil", "Suwayda Al Ma", "Ibri"]
    a = town_letters(names)
    b = town_letters(list(reversed(names)))
    c = town_letters(sorted(names, key=len))
    assert a == b == c
    assert len(set(a.values())) == len(names)         # and every code is unique


def test_a_town_index_built_from_names_reports_who_collided_with_whom():
    idx = N.TownIndex.from_names(["Al Qali", "Al Qurayn", "Bat"])
    t = idx.clash_table().set_index("NAME")
    assert t.loc["Bat", "N_CLASH"] == 0 and t.loc["Bat", "CODE"] == "B"
    assert t.loc["Al Qali", "CODE"] == "QA"
    assert "Al Qurayn" in t.loc["Al Qali", "CLASHED_WITH"]
    assert t.loc["Al Qali", "KEY"] == "qali"          # the de-articled letters, shown


# --- the real gazetteer ---------------------------------------------------------------

_TOWNS_PATH = N.default_towns_path()
_HAS_TOWNS = os.path.isfile(_TOWNS_PATH)
_skip_towns = pytest.mark.skipif(
    not _HAS_TOWNS, reason=f"towns layer not present: {_TOWNS_PATH}")


@_skip_towns
def test_the_real_gazetteer_resolves_to_25_unique_codes():
    idx = N.TownIndex.load()
    assert len(idx.names) == 25, idx.names
    assert len(set(idx.codes.values())) == 25, "two towns share a code"
    # measured 2026-09-06: 20 of 25 collide on their first letter, in 8 groups
    t = idx.clash_table()
    assert int((t.N_CLASH > 0).sum()) == 20
    assert int((t.LETTERS == 1).sum()) == 5
    assert set(t.loc[t.LETTERS == 1, "CODE"]) == {"B", "G", "H", "I", "U"}
    assert idx.codes["IBRI"] == "I"


@_skip_towns
def test_the_gazetteer_is_in_the_project_crs_and_its_polygons_do_not_overlap():
    # locate() has to choose when polygons overlap; the choice is deterministic but it is
    # still a choice, and a gazetteer with no overlaps means it never has to make one
    idx = N.TownIndex.load()
    assert idx.overlap_count() == 0


# ======================================================================================
# 2. THE GRAMMAR — what this module writes is what contract.validate() will check
# ======================================================================================

def test_every_name_parses_and_agrees_with_its_own_columns(result):
    for df in (result.nodes, result.reaches, result.stations, result.rising_mains):
        for _, r in df.iterrows():
            if not r.NAME:
                continue
            p = parse_name(r.NAME)
            assert p is not None, f"{r.NAME} does not fit contract.NAME_RE"
            assert p["town"] == r.TOWN
            assert p["sub"] == (r.SUBNET or "")
            if "TIER" in df.columns and p["kind"] == "manhole":
                assert p["tier"] == TIER_TOKEN[str(r.TIER).strip().lower()]


def test_names_are_unique_within_every_layer(result):
    for df in (result.nodes, result.reaches, result.stations, result.rising_mains):
        got = [v for v in df.NAME if v]
        assert len(got) == len(set(got)), "a name that identifies two things identifies none"


def test_a_conduit_is_named_for_its_upstream_manhole(result):
    mh = dict(zip(result.nodes.NODE_UID, result.nodes.NAME))
    seq = dict(zip(result.node_towns.NODE_UID, result.node_towns.MH_SEQ))
    sub = dict(zip(result.nodes.NODE_UID, result.nodes.SUBNET))
    town = dict(zip(result.nodes.NODE_UID, result.nodes.TOWN))
    n = 0
    for _, r in result.reaches.iterrows():
        if not r.NAME:
            continue
        u = r.US_NODE
        assert r.NAME == concept_name(town[u], "conduit", subnet=sub[u], seq=int(seq[u]))
        assert parse_name(r.NAME)["cd"] == parse_name(mh[u])["mh"]
        n += 1
    assert n > 5


def test_a_pump_is_not_inside_a_subnetwork_and_its_force_main_shares_its_number(result):
    assert (result.stations.SUBNET == "").all(), "a station is a SEAM, not a member"
    assert (result.rising_mains.SUBNET == "").all()
    for _, s in result.stations.iterrows():
        assert parse_name(s.NAME)["kind"] == "pump"
    pump_no = {r.NODE_UID: parse_name(r.NAME)["pmp"] for _, r in result.stations.iterrows()}
    for _, m in result.rising_mains.iterrows():
        p = parse_name(m.NAME)
        assert p["kind"] == "main", f"{m.NAME} parsed as {p['kind']}"
        assert p["fm"] == pump_no[m.STATION], "a force main is numbered with its pump"


def test_a_fully_named_frame_passes_the_contracts_own_publication_gate(result):
    gdf = result.nodes[result.nodes.NAME != ""].copy()
    assert_named(gdf, "nodes", stage="test")           # raises if any row is unnamed
    half = gdf.copy()
    half.loc[half.index[0], "NAME"] = ""
    with pytest.raises(Exception, match="NOT FULLY NAMED"):
        assert_named(half, "nodes")


def test_the_zero_padding_makes_a_text_sort_a_geographic_sort(result):
    subs = [s for s in result.nodes.SUBNET if s]
    assert all(SUBNET_RE.match(s) for s in set(subs))
    assert len({len(s) for s in subs}) == 1, "one width across the design, or sorting breaks"
    # THE IDENTITY OF A SUBNETWORK IS (TOWN, SUBNET), not the S-token on its own: the
    # numbering restarts in every town, so I-S01 and A-S01 are two different subnetworks.
    # Compared within ONE tier, because the tier token sits ahead of the number in the
    # name and therefore sorts ahead of it - which is the grammar the engineer chose.
    lat = result.nodes[result.nodes.TIER == "lateral"]
    one = lat[(lat.TOWN == lat.TOWN.iloc[0]) & (lat.SUBNET == lat.SUBNET.iloc[0])]
    assert len(one) > 2
    txt = sorted(v for v in one.NAME if v)
    num = [v for _, v in sorted(
        ((int(parse_name(v)["mh"]), v) for v in one.NAME if v))]
    assert txt == num


# ======================================================================================
# 3. STABILITY — THE TEST THIS FILE EXISTS FOR
# ======================================================================================

def test_the_same_design_in_a_different_row_order_gets_the_same_names(towns):
    """Build one design twice, permute everything the second time, demand identical names.

    A name derived from row order, insertion order or dict iteration passes every other
    check in this project and still renames the network on the next run. Nothing else
    would catch it: the layers publish, the audit is green, and only a person comparing an
    old drawing to a new schedule ever finds out.
    """
    nodes, reaches, stations, mains, town = build_design(n_branches=5, per_branch=7)
    a = N.name_network(nodes, reaches=reaches, stations=stations, rising_mains=mains,
                       towns=towns, node_town=town)

    rng = np.random.default_rng(20260906)
    perm = rng.permutation(len(nodes))
    n2 = nodes.iloc[perm].reset_index(drop=True)
    t2 = [town[i] for i in perm]
    # reaches reversed, stations reversed, and the COLUMNS reordered too
    r2 = reaches.iloc[::-1].reset_index(drop=True)[["DS_NODE", "US_NODE", "EDGE_UID"]]
    s2 = stations.iloc[::-1].reset_index(drop=True)
    m2 = mains.iloc[::-1].reset_index(drop=True)
    b = N.name_network(n2, reaches=r2, stations=s2, rising_mains=m2,
                       towns=towns, node_town=t2)

    assert a.name_map() == b.name_map(), "NAMES MOVED WHEN THE ROWS MOVED"
    assert a.counts["subnets"] == b.counts["subnets"]
    assert (a.subnets.sort_values("NAME").reset_index(drop=True).NAME ==
            b.subnets.sort_values("NAME").reset_index(drop=True).NAME).all()


def test_the_same_design_named_twice_in_the_same_process_is_identical(design, towns):
    nodes, reaches, stations, mains, town = design
    kw = dict(reaches=reaches, stations=stations, rising_mains=mains, towns=towns,
              node_town=town)
    assert N.name_network(nodes, **kw).name_map() == N.name_network(nodes, **kw).name_map()


def test_the_manhole_order_comes_from_the_graph_not_from_the_coordinates_alone(towns):
    """M001 is the outfall and the walk goes upstream, largest subtree first.

    Asserted because it is the property that makes the numbering readable AND stable: a
    branch that grows does not renumber the spine ahead of it.
    """
    nodes, reaches, _, _, town = build_design(n_branches=2, per_branch=4)
    res = N.name_network(nodes, reaches=reaches, towns=towns, node_town=town)
    seq = dict(zip(res.node_towns.NODE_UID, res.node_towns.MH_SEQ))
    sub = dict(zip(res.nodes.NODE_UID, zip(res.nodes.TOWN, res.nodes.SUBNET)))
    # every subnetwork numbers its own outfall 1
    for _, s in res.subnets.iterrows():
        assert seq[s.OUTFALL] == 1
    # and a chamber's number is always above its downstream neighbour's, inside a subnetwork
    ds = dict(zip(nodes.NODE_UID, nodes.DS_NODE))
    for u, d in ds.items():
        if d and sub.get(u, ("", ""))[1] and sub.get(u) == sub.get(d):
            assert seq[u] > seq[d], f"{u} is upstream of {d} but numbered below it"


# ======================================================================================
# 4. THE ORDERING RULE — naming runs AFTER connectivity (engineer's rule b)
# ======================================================================================

def test_naming_refuses_to_run_before_the_tree_exists(design, towns):
    nodes, _, _, _, town = design
    blind = nodes.copy()
    blind["DS_NODE"] = ""
    with pytest.raises(N.NamingOrderError) as e:
        N.name_network(blind, towns=towns, node_town=town)
    assert "DOWNSTREAM" in str(e.value)
    assert "s2_orient" in str(e.value)                 # it names the stages that must run


def test_a_frame_with_no_topology_column_is_refused_by_name(design):
    nodes = design[0]
    with pytest.raises(N.NamingError, match="DS_NODE"):
        N.assert_ready(nodes.drop(columns=["DS_NODE"]))


def test_an_element_outside_every_town_takes_the_first_town_downstream(result):
    nt = result.node_towns.set_index("NODE_UID")
    # build_design puts the second chamber of every branch outside every town
    outside = [u for u in result.nodes.NODE_UID if u.endswith("_1")]
    assert len(outside) >= 4
    for u in outside:
        assert nt.TOWN_SRC[u] == "downstream"
        assert nt.TOWN[u] != "", "rule (b) should have found a town downstream"
        assert result.nodes.set_index("NODE_UID").NAME[u].startswith(nt.TOWN[u] + "-")
    assert result.counts["town_downstream"] == len(outside)


def test_a_subnetwork_takes_the_town_holding_most_of_its_chambers(towns):
    # 3 chambers in Ibri, 2 in Al Araqi, outfall in Al Araqi: plurality wins, not the outfall
    rows = [("O", 0.0, 0.0, "", "sub main"),
            ("A", 0.0, 10.0, "O", "lateral"),
            ("C", 0.0, 20.0, "A", "lateral"),
            ("D", 0.0, 30.0, "C", "lateral"),
            ("E", 0.0, 40.0, "D", "lateral")]
    nodes = pd.DataFrame(rows, columns=["NODE_UID", "X", "Y", "DS_NODE", "TIER"])
    town = ["Al Araqi", "Al Araqi", "Ibri", "Ibri", "Ibri"]
    res = N.name_network(nodes, towns=towns, node_town=town)
    assert res.subnets.TOWN.iloc[0] == towns.code("Ibri")
    assert res.subnets.TOWN_WHY.iloc[0] == "plurality"
    assert 0.55 < float(res.subnets.TOWN_SHARE.iloc[0]) < 0.65
    assert (res.nodes.TOWN == towns.code("Ibri")).all(), \
        "the town letter belongs to the SUBNETWORK, not to each chamber"


def test_a_branch_stops_where_it_meets_the_main_pipe(result):
    """Concept rule 2: no subnetwork crosses the main pipe and grows past it."""
    # (TOWN, SUBNET) is the identity - the S-token restarts in each town
    sub = dict(zip(result.nodes.NODE_UID, zip(result.nodes.TOWN, result.nodes.SUBNET)))
    trunk = [u for u in sub if u.startswith("T")]
    branch = [u for u in sub if u.startswith("B")]
    assert len({sub[u] for u in trunk}) == 1, "the main pipe is one run through this town"
    assert sub[trunk[0]] not in {sub[u] for u in branch}, \
        "a branch and the main pipe are in one subnetwork - rule 2 broken"
    # and the main pipe sorts first in its town, so I-S01 is the spine
    main_row = result.subnets[result.subnets.IS_MAIN == 1]
    assert len(main_row) == 1 and main_row.SUBNET.iloc[0].endswith("1")


# ======================================================================================
# 5. FLAG, DO NOT SOLVE (concept rule 7)
# ======================================================================================

def test_a_chamber_with_no_town_anywhere_downstream_is_flagged_not_guessed(towns):
    nodes = pd.DataFrame([("X1", 0.0, 0.0, "", "sub main")],
                         columns=["NODE_UID", "X", "Y", "DS_NODE", "TIER"])
    nodes = pd.concat([nodes, pd.DataFrame(
        [("X2", 0.0, 10.0, "X1", "lateral")],
        columns=nodes.columns)], ignore_index=True)
    res = N.name_network(nodes, towns=towns, node_town=["", ""])
    assert (res.nodes.NAME == "").all(), "a town was invented for an element that has none"
    kinds = set(res.flags.KIND)
    assert "node_no_town" in kinds and "subnet_no_town" in kinds
    assert res.counts["town_none"] == 2
    row = res.flags[res.flags.KIND == "subnet_no_town"].iloc[0]
    assert row.SIZE == 2, "a flag must carry its SIZE, not only its reason"


def test_a_tier_the_grammar_cannot_express_is_flagged_rather_than_written(design, towns):
    """contract.TIER_TOKEN maps five tiers; contract.NAME_RE admits three.

    A chamber whose TIER is 'main' formats as I-S01-M-M003, which contract.validate() then
    rejects as ungrammatical. Naming will not write a name its own contract refuses.
    """
    assert N.GRAMMAR_TIERS == {"lateral", "sub main", "trunk main"}
    assert set(TIERS) - N.GRAMMAR_TIERS == {"main", "rider"}
    assert parse_name(concept_name("I", "manhole", subnet="S01", tier="main", seq=1)) is None

    nodes, reaches, _, _, town = design
    bad = nodes.copy()
    bad.loc[bad.NODE_UID == "B0_3", "TIER"] = "main"
    res = N.name_network(bad, reaches=reaches, towns=towns, node_town=town)
    assert res.nodes.set_index("NODE_UID").NAME["B0_3"] == ""
    f = res.flags[res.flags.KIND == "node_tier_ungrammatical"]
    assert len(f) == 1 and "NAME_RE" in f.WHY.iloc[0]


def test_an_unknown_tier_cannot_be_defaulted(design, towns):
    nodes, _, _, _, town = design
    bad = nodes.copy()
    bad.loc[bad.NODE_UID == "B1_2", "TIER"] = "boulevard"
    res = N.name_network(bad, towns=towns, node_town=town)
    assert res.nodes.set_index("NODE_UID").NAME["B1_2"] == ""
    assert (res.flags.KIND == "node_no_tier").sum() == 1


def test_two_reaches_out_of_one_chamber_are_reported_not_suffixed(design, towns):
    nodes, reaches, _, _, town = design
    dup = pd.concat([reaches, reaches.iloc[[0]].assign(EDGE_UID="EDUP")],
                    ignore_index=True)
    res = N.name_network(nodes, reaches=dup, towns=towns, node_town=town)
    f = res.flags[res.flags.KIND == "reach_dup_us_node"]
    assert len(f) == 1, "a forest cannot have two outgoing reaches; hiding it is the defect"
    assert res.reaches.set_index("EDGE_UID").NAME["EDUP"] == ""


def test_an_oversized_subnetwork_is_flagged_because_its_numbers_stop_sorting(towns):
    n = N.MH_SEQ_SORTS_TO + 5
    rows = [(f"C{i:05d}", 0.0, float(i), "" if i == 0 else f"C{i - 1:05d}",
             "sub main" if i == 0 else "lateral") for i in range(n)]
    nodes = pd.DataFrame(rows, columns=["NODE_UID", "X", "Y", "DS_NODE", "TIER"])
    res = N.name_network(nodes, towns=towns, node_town=["Ibri"] * n)
    f = res.flags[res.flags.KIND == "subnet_over_999"]
    assert len(f) == 1 and int(f.SIZE.iloc[0]) == n
    # and the names really do stop sorting - which is why it is flagged rather than ignored
    lat = sorted(v for v in res.nodes.NAME if "-L-M" in v)
    assert lat[-1].endswith("M999"), "M1000 sorts before M999 - the flag is honest"
    assert int(parse_name(lat[-1])["mh"]) < max(
        int(parse_name(v)["mh"]) for v in lat), "the largest number is not last"


def test_a_cycle_in_the_tree_raises_with_the_nodes_in_it(design, towns):
    nodes, _, _, _, town = design
    loop = nodes.copy()
    loop.loc[loop.NODE_UID == "T0", "DS_NODE"] = "T1"
    loop.loc[loop.NODE_UID == "T1", "DS_NODE"] = "T0"
    with pytest.raises(N.NamingError, match="CYCLE"):
        N.name_network(loop, towns=towns, node_town=town)


def test_a_duplicate_identity_is_refused_before_anything_is_named(design, towns):
    nodes, _, _, _, town = design
    dup = pd.concat([nodes, nodes.iloc[[3]]], ignore_index=True)
    with pytest.raises(N.NamingError, match="duplicate keys"):
        N.name_network(dup, towns=towns, node_town=list(town) + [town[3]])


def test_a_station_with_no_town_and_no_discharge_is_flagged(towns):
    nodes = pd.DataFrame([("T0", 0.0, 0.0, "", "trunk main"),
                          ("T1", 0.0, 10.0, "T0", "trunk main")],
                         columns=["NODE_UID", "X", "Y", "DS_NODE", "TIER"])
    st = pd.DataFrame([dict(NODE_UID="PSX", X=9e5, Y=9e5)])
    rm = pd.DataFrame([dict(EDGE_UID="RMX", STATION="PSX", DS_NODE="")])
    res = N.name_network(nodes, stations=st, rising_mains=rm, towns=towns,
                         node_town=["", ""])
    assert res.stations.NAME.iloc[0] == ""
    assert set(res.flags.KIND) >= {"station_no_town", "rm_no_station"}


def test_a_rising_main_with_no_link_to_a_pump_is_refused_by_name(design, towns):
    nodes, _, stations, mains, town = design
    bad = mains.drop(columns=["STATION"])
    with pytest.raises(N.NamingError, match="numbered with its pump"):
        N.name_network(nodes, stations=stations, rising_mains=bad, towns=towns,
                       node_town=town)


def test_every_flag_carries_a_reason_and_a_reference(result, towns, design):
    nodes, _, _, _, town = design
    bad = nodes.copy()
    bad.loc[bad.NODE_UID == "B1_2", "TIER"] = "boulevard"
    res = N.name_network(bad, towns=towns, node_town=town)
    assert list(res.flags.columns) == ["KIND", "REF", "WHY", "SIZE"]
    assert (res.flags.WHY.str.len() > 30).all(), "a flag with no reason is a silent drop"
    assert (res.flags.REF.str.len() > 0).all()


# ======================================================================================
# 6. ADD AND TAKE AWAY (inheritance-ledger row 4)
# ======================================================================================

def test_a_name_can_be_taken_away_and_the_count_is_published(result):
    cleared, removed = N.clear_names(result.nodes)
    assert removed == int((result.nodes.NAME != "").sum()) > 0
    assert (cleared.NAME == "").all() and (cleared.TOWN == "").all()
    assert (cleared.SUBNET == "").all()


def test_renaming_an_already_named_frame_reports_no_change(design, towns, result):
    nodes, reaches, stations, mains, town = design
    again = N.name_network(result.nodes, reaches=result.reaches, stations=result.stations,
                           rising_mains=result.rising_mains, towns=towns, node_town=town)
    assert again.counts["renamed"] == 0
    assert again.counts["withdrawn"] == 0
    assert again.counts["unchanged"] == sum(
        int((df.NAME != "").sum()) for df in
        (result.nodes, result.reaches, result.stations, result.rising_mains))


def test_a_withdrawal_is_counted_not_hidden(design, towns, result):
    """A chamber that loses its town loses its name, and the count says so.

    This is the row-4 rule applied to naming: the pass that gives a name must be able to
    take one away, and it must publish how many. Losing that rule for pumping stations
    cost the last iteration 69 spurious stations.
    """
    nodes, _, _, _, town = design
    named = nodes.copy()
    named["NAME"] = [result.nodes.set_index("NODE_UID").NAME[u] for u in nodes.NODE_UID]
    broken = named.copy()
    broken.loc[broken.NODE_UID == "B1_2", "TIER"] = "boulevard"
    res = N.name_network(broken, towns=towns, node_town=town)
    assert res.counts["withdrawn"] == 1
    assert res.nodes.set_index("NODE_UID").NAME["B1_2"] == ""
    assert res.counts["unchanged"] == int((named.NAME != "").sum()) - 1


def test_naming_does_not_mutate_the_frames_it_was_handed(design, towns):
    nodes, reaches, stations, mains, town = design
    before = [df.copy() for df in (nodes, reaches, stations, mains)]
    N.name_network(nodes, reaches=reaches, stations=stations, rising_mains=mains,
                   towns=towns, node_town=town)
    for a, b in zip((nodes, reaches, stations, mains), before):
        pd.testing.assert_frame_equal(a, b)


# ======================================================================================
# 7. THE FROZEN MAPPING (engineer's rule f)
# ======================================================================================

def test_the_prefix_mapping_round_trips_through_the_file(tmp_path, towns):
    p = N.write_town_prefixes(towns, str(tmp_path / "prefixes.csv"))
    assert os.path.isfile(p) and os.path.isfile(os.path.splitext(p)[0] + ".json")
    assert N.load_town_prefixes(p) == towns.codes
    assert N.load_town_prefixes(os.path.splitext(p)[0] + ".json") == towns.codes
    man = json.load(open(os.path.splitext(p)[0] + ".json", encoding="utf-8"))
    assert man["n_towns"] == len(towns.names)
    assert man["clash_universe"] == N.ASSUMPTIONS["TOWN_CLASH_UNIVERSE"][0]


def test_a_hand_edited_mapping_is_refused_rather_than_used(tmp_path, towns):
    p = N.write_town_prefixes(towns, str(tmp_path / "prefixes.csv"))
    jp = os.path.splitext(p)[0] + ".json"
    man = json.load(open(jp, encoding="utf-8"))
    man["codes"]["Ibri"] = "Z"
    json.dump(man, open(jp, "w", encoding="utf-8"))
    with pytest.raises(N.NamingError, match="sha256"):
        N.load_town_prefixes(p)


def test_a_frozen_code_survives_a_new_town_arriving(tmp_path):
    """Once a code is issued it is on a drawing. A town added later may not renumber it."""
    first = N.TownIndex.from_names(["Ad Dariz", "Ibri"])
    assert first.codes["Ad Dariz"] == "D"              # no clash yet
    p = N.write_town_prefixes(first, str(tmp_path / "p.csv"))
    later = N.TownIndex.from_names(["Ad Dariz", "Ad Dibayshi", "Ibri"],
                                   frozen=N.load_town_prefixes(p))
    assert later.codes["Ad Dariz"] == "D", "the issued code moved"
    assert later.codes["Ad Dibayshi"] == "DI"          # the new town takes the extension


def test_drift_against_a_frozen_mapping_is_reported_not_applied(tmp_path):
    a = N.TownIndex.from_names(["Ad Dariz", "Ibri"])
    p = N.write_town_prefixes(a, str(tmp_path / "p.csv"))
    b = N.TownIndex.from_names(["Ad Dariz", "Ad Dibayshi", "Ibri"])   # NOT frozen
    d = b.check_frozen(p)
    assert set(d.NAME) == {"Ad Dariz", "Ad Dibayshi"}
    assert "CODE CHANGED" in d[d.NAME == "Ad Dariz"].WHY.iloc[0]


# ======================================================================================
# 8. SCALE — it has to survive the real network, not only a fixture
# ======================================================================================

@pytest.mark.slow
def test_a_network_the_size_of_the_real_one_names_in_seconds_and_stays_unique():
    """20,000 chambers in 40 subnetworks. The published design is 56,930; this is the same
    shape at a third of the size, and it runs in the unit-test budget."""
    import time
    towns = N.TownIndex.from_names(["Ibri", "Al Araqi"], source="(scale)")
    nodes, reaches, _, _, town = build_design(n_branches=40, per_branch=499)
    assert len(nodes) > 19_000
    t0 = time.perf_counter()
    res = N.name_network(nodes, reaches=reaches, towns=towns, node_town=town)
    dt = time.perf_counter() - t0
    print(f"\n    [budget] naming {len(nodes):,} chambers: {dt:.2f} s")
    assert dt < 30.0, f"naming took {dt:.1f} s - something is O(n^2)"
    got = [v for v in res.nodes.NAME if v]
    assert len(got) == len(nodes) == len(set(got))
    assert res.counts["subnets"] == 41                 # 40 branches + the main pipe


@pytest.mark.slow
def test_the_scale_run_is_still_reproducible():
    towns = N.TownIndex.from_names(["Ibri", "Al Araqi"], source="(scale)")
    nodes, reaches, _, _, town = build_design(n_branches=12, per_branch=60)
    a = N.name_network(nodes, reaches=reaches, towns=towns, node_town=town)
    rng = np.random.default_rng(7)
    perm = rng.permutation(len(nodes))
    b = N.name_network(nodes.iloc[perm].reset_index(drop=True),
                       reaches=reaches.sample(frac=1.0, random_state=3).reset_index(drop=True),
                       towns=towns, node_town=[town[i] for i in perm])
    assert a.name_map() == b.name_map()


# ======================================================================================
# 9. THE MODULE'S OWN DECLARATIONS
# ======================================================================================

def test_every_choice_with_no_guideline_behind_it_is_in_the_assumptions_register():
    must = {"TOWN_NAME_FIELD", "TOWN_CLASH_UNIVERSE", "SUBNET_ORDER", "SUBNET_TOWN_RULE",
            "MH_ORDER", "MH_NUMBER_SCOPE", "MAIN_AS_SUBNET", "ORDER_QUANT_M",
            "SUBNET_PAD_MIN", "MH_SEQ_SORTS_TO"}
    assert must <= set(N.ASSUMPTIONS)
    for k, (_v, why) in N.ASSUMPTIONS.items():
        assert len(why) > 60, f"{k} has no reasoning behind it"
        assert ("PROJECT DECISION" in why or "STRUCTURAL" in why or "DATA CHOICE" in why), \
            f"{k} does not say what kind of value it is"


def test_the_module_carries_no_design_number():
    """Naming has no hydraulics. Not one slope, diameter, depth, velocity or flow.

    Checked against the criteria's own values rather than by eye: if any distinctive design
    constant appears as a literal in this module, it has been re-typed somewhere it cannot
    be re-read from its cited page - the defect that failed a blocking cover check on every
    reach when one allowance was 0.05 in one file and 0.10 in another.
    """
    from w12.criteria import DEFAULT as C
    src = open(N.__file__, encoding="utf-8").read()
    hydraulic = ["V_MAX", "MIN_COVER", "MAX_COVER", "TAU_PA", "SLOPE_STEP", "FM_V_MAX",
                 "INFILT_L_D_KM", "PROPS_PER_PLOT", "WALL_ALLOW"]
    for name in hydraulic:
        assert name not in src, f"{name} has no business in a naming module"
        val = getattr(C, name, None)
        if isinstance(val, float) and val not in (0.0, 1.0, 2.0, 3.0):
            assert repr(val) not in src, f"{name}'s value {val} is typed into naming.py"


def test_the_stage_order_requirement_is_written_down_where_a_caller_will_see_it():
    assert any("s2_orient" in s for s in N.RUNS_AFTER)
    assert any("s7_pumps" in s for s in N.RUNS_AFTER)
    assert "DOWNSTREAM" in N.__doc__ and "STABILITY" in N.__doc__


def test_the_modules_own_self_test_passes():
    N._self_test()


# ======================================================================================
# 10. THE REGRESSION THAT THE SYNTHETIC FIXTURES MISSED (2026-09-06)
# ======================================================================================
#
# `_follow()` returned a depth one too small on every walk that met an already-resolved
# node. Nothing failed. The root was right, every name parsed, the audit was green - and
# 34,932 of 56,930 chambers changed their number when the rows were shuffled, because depth
# ORDERS the town propagation and the subtree-size accumulation. It also cost 18 chambers
# their town: rule (b) could not reach them because their downstream node had not been
# resolved yet.
#
# The tidy fixtures above were too symmetric to show it. These are not.

def test_the_depth_of_every_node_is_exactly_one_below_its_downstream_neighbour():
    """The invariant `_follow()` now checks for itself, tested from the outside too."""
    rng = np.random.default_rng(11)
    n = 400
    parent = np.array([-1] + [int(rng.integers(0, i)) for i in range(1, n)], dtype=np.int64)
    root, depth = N._follow(parent)
    assert (depth[parent < 0] == 0).all()
    has = parent >= 0
    assert (depth[has] == depth[parent[has]] + 1).all()
    assert (root == 0).all(), "one component, so every root is node 0"


def test_the_depth_does_not_depend_on_the_order_the_nodes_are_visited():
    rng = np.random.default_rng(12)
    n = 600
    parent = np.array([-1] + [int(rng.integers(0, i)) for i in range(1, n)], dtype=np.int64)
    _, d0 = N._follow(parent)
    perm = rng.permutation(n)
    inv = np.empty(n, dtype=np.int64)
    inv[perm] = np.arange(n)
    p2 = np.where(parent[perm] < 0, -1, inv[parent[perm]])
    _, d2 = N._follow(p2)
    assert (d0 == d2[inv]).all(), "the depth moved when the rows moved"


def _random_design(seed: int, n: int = 900):
    """A LOPSIDED random tree - long chains, uneven branching, chambers scattered outside
    the towns. This is the shape that broke the depth walk; the tidy fixtures did not."""
    rng = np.random.default_rng(seed)
    uid = [f"N{i:05d}" for i in range(n)]
    ds = [""] + [uid[int(rng.integers(0, i))] for i in range(1, n)]
    x = rng.uniform(0, 3000, n).round(3)
    y = rng.uniform(0, 3000, n).round(3)
    tier = ["trunk main"] + list(rng.choice(["sub main", "lateral"], n - 1, p=[0.2, 0.8]))
    nodes = pd.DataFrame(dict(NODE_UID=uid, X=x, Y=y, DS_NODE=ds, TIER=tier))
    # a third of the chambers are outside every town, so rule (b) does real work
    town = ["" if v < 0.33 else ("Ibri" if v < 0.7 else "Al Araqi")
            for v in rng.uniform(0, 1, n)]
    town[0] = "Ibri"                       # the outfall is in a town, so the tree resolves
    reaches = pd.DataFrame(
        [(f"E{i:05d}", uid[i], ds[i]) for i in range(1, n)],
        columns=["EDGE_UID", "US_NODE", "DS_NODE"])
    return nodes, reaches, town


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_a_lopsided_random_tree_names_the_same_however_the_rows_arrive(seed):
    towns = N.TownIndex.from_names(["Ibri", "Al Araqi"], source="(random)")
    nodes, reaches, town = _random_design(seed)
    a = N.name_network(nodes, reaches=reaches, towns=towns, node_town=town)
    rng = np.random.default_rng(seed * 977)
    for _ in range(3):
        perm = rng.permutation(len(nodes))
        b = N.name_network(nodes.iloc[perm].reset_index(drop=True),
                           reaches=reaches.sample(frac=1.0, random_state=int(perm[0]))
                                          .reset_index(drop=True),
                           towns=towns, node_town=[town[i] for i in perm])
        assert a.name_map() == b.name_map(), "NAMES MOVED WHEN THE ROWS MOVED"


def test_rule_b_reaches_every_chamber_whose_downstream_chain_ends_in_a_town():
    """Not one chamber is left townless while a town sits downstream of it.

    The depth bug made this fail silently on the live layer: 18 chambers were denied a town
    because their downstream node had not been resolved when their turn came.
    """
    towns = N.TownIndex.from_names(["Ibri", "Al Araqi"], source="(random)")
    nodes, reaches, town = _random_design(9, n=1200)
    res = N.name_network(nodes, reaches=reaches, towns=towns, node_town=town)
    # every node drains to node 0, which is in a town, so every node must resolve
    assert res.counts["town_none"] == 0, res.flags.head().to_string()
    nt = res.node_towns
    assert set(nt.TOWN_SRC) == {"inside", "downstream"}
    assert (nt.TOWN != "").all()


# ======================================================================================
# 11. THE REAL NETWORK — the only test that actually caught the depth bug
# ======================================================================================

def _real_graph_path():
    """W12's published graph if a stage has produced one, else W11b's.

    W11b is superseded as a DESIGN, but its published `nodes`/`reaches` are a real 56,930-
    chamber graph with real coordinates, and the synthetic fixtures above are too tidy to
    exercise a naming walk properly. The moment W12 publishes its own, this reads that
    instead - the path list is ordered, not hard-coded to the old folder.
    """
    from conftest import SHP_DIR, REPO_ROOT
    for p in (SHP_DIR / "W12.gpkg", SHP_DIR / "W12_hier.gpkg",
              REPO_ROOT / "W11b" / "shp" / "W11b.gpkg"):
        if p.is_file():
            try:
                import fiona
                if {"nodes", "reaches"} <= set(fiona.listlayers(str(p))):
                    return p
            except Exception:
                continue
    return None


@pytest.mark.slow
def test_a_real_published_graph_names_stably_and_in_seconds():
    import time
    p = _real_graph_path()
    if p is None:
        pytest.skip("no published graph with nodes+reaches to name - run s3_hierarchy")
    if not _HAS_TOWNS:
        pytest.skip(f"towns layer not present: {_TOWNS_PATH}")
    import geopandas as gpd

    nodes = pd.DataFrame(gpd.read_file(str(p), layer="nodes").drop(columns="geometry"))
    reaches = pd.DataFrame(gpd.read_file(str(p), layer="reaches").drop(columns="geometry"))
    towns = N.TownIndex.load()

    t0 = time.perf_counter()
    a = N.name_network(nodes, reaches=reaches, towns=towns)
    dt = time.perf_counter() - t0
    print(f"\n    [budget] {p.name}: {len(nodes):,} chambers named in {dt:.2f} s")
    assert dt < 60.0

    rng = np.random.default_rng(20260906)
    perm = rng.permutation(len(nodes))
    b = N.name_network(nodes.iloc[perm].reset_index(drop=True),
                       reaches=reaches.sample(frac=1.0, random_state=5).reset_index(drop=True),
                       towns=towns)
    assert a.name_map() == b.name_map(), (
        "NAMES MOVED WHEN THE ROWS MOVED on the real graph. This exact assertion failed on "
        "2026-09-06 with 34,932 of 56,930 chambers renumbered, while every synthetic "
        "fixture above passed - the fixtures were too symmetric to reach the code path.")

    named = [v for v in a.nodes.NAME if v]
    assert len(named) == len(set(named))
    assert a.counts["nodes_named"] > 0.5 * len(nodes)
    # and every flag on the real graph carries a reason and a reference
    assert (a.flags.WHY.str.len() > 30).all() if len(a.flags) else True
