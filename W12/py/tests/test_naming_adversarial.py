"""
ADVERSARIAL REVIEW OF `w12.naming` — the cases the module's own tests do not build
==================================================================================

`tests/test_naming_scheme.py` is the module author's file and it passes. This one holds the
cases an attacker builds, each written after the behaviour was OBSERVED, not guessed. Six of
them failed when they were first written:

    the station's town came from the ROW ORDER of the rising-mains frame. The author's
    headline stability test shuffles `nodes` and `reaches` and never touches `rising_mains`,
    so reversing two rows renamed the pump from I-PMP01 to A-PMP01 and both its force mains
    with it - the exact property rule (e) says this module does not have

    a DS_NODE naming a chamber that is not in the frame was silently promoted to an OUTFALL,
    inventing a subnetwork around a broken link, with no flag anywhere

    two force mains on one pump were both written I-P01. contract.validate() refuses a
    duplicate NAME at publication, so the layer could not have shipped - but naming's job
    (concept rule 7) is to FLAG it, not to hand a duplicate downstream

    a duplicate EDGE_UID went unchecked, and `name_map()` - the oracle the stability test
    compares - collapses two rows into one key, so a name that moved between runs could hide
    inside the very check written to catch it

    `main_tier="trunk_main"` - the spelling contract.TIER_ALIASES exists for - matched NO
    chamber, so concept rule 2 (a subnetwork stops where it MEETS the main pipe) quietly
    stopped being applied and every branch merged into one subnetwork

    a NaN coordinate was cast to INT64_MIN behind a RuntimeWarning and the element was named
    as though it had a position

NO DESIGN NUMBER IS ASSERTED HERE either. Every number below is a count of something this
file built.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from w12 import naming as N

COLS = ["NODE_UID", "X", "Y", "DS_NODE", "TIER"]


def mk(rows):
    return pd.DataFrame(rows, columns=COLS)


@pytest.fixture(scope="module")
def towns():
    return N.TownIndex.from_names(["Ibri", "Al Araqi", "Ad Dariz"], source="(adversarial)")


def _two_town_trunks():
    """Two separate trunk runs, one in each town, so a station between them has a genuine
    choice of downstream town."""
    nodes = mk([
        ("I0", 0.0, 100.0, "I1", "trunk main"),
        ("I1", 0.0, 0.0, "", "trunk main"),
        ("A0", 5000.0, 100.0, "A1", "trunk main"),
        ("A1", 5000.0, 0.0, "", "trunk main"),
    ])
    return nodes, ["Ibri", "Ibri", "Al Araqi", "Al Araqi"]


# ======================================================================================
# 1. STABILITY — the frame the author's shuffle never touched
# ======================================================================================

def test_a_station_name_does_not_depend_on_the_row_order_of_the_rising_mains(towns):
    """THE REGRESSION. One station, two mains, two towns, rows reversed.

    `ds_of_station.setdefault(a, b)` iterated the frame in row order, so the station took
    the letter of whichever main happened to be listed first. Observed 2026-09-06:
    I-PMP01 / I-P01 with the rows as given, A-PMP01 / A-P01 with the rows reversed, and
    every other test in the project green.
    """
    nodes, town = _two_town_trunks()
    st = pd.DataFrame([dict(NODE_UID="PS1", X=2500.0, Y=1000.0)])
    fwd = pd.DataFrame([dict(EDGE_UID="RM_a", STATION="PS1", DS_NODE="I1"),
                        dict(EDGE_UID="RM_b", STATION="PS1", DS_NODE="A1")])
    rev = fwd.iloc[::-1].reset_index(drop=True)

    a = N.name_network(nodes, stations=st, rising_mains=fwd, towns=towns, node_town=town)
    b = N.name_network(nodes, stations=st, rising_mains=rev, towns=towns, node_town=town)

    assert a.stations.NAME.iloc[0] == b.stations.NAME.iloc[0], \
        "the pump was renamed by reversing two rows of a frame it does not live in"
    assert a.name_map() == b.name_map()
    assert sorted(a.flags.KIND) == sorted(b.flags.KIND)


def test_a_station_whose_mains_reach_two_towns_is_flagged_not_just_sorted(towns):
    """Deterministic is not the same as decided. Rule (b) has two answers here and which
    town owns the station is the engineer's call, so the choice is published."""
    nodes, town = _two_town_trunks()
    st = pd.DataFrame([dict(NODE_UID="PS1", X=2500.0, Y=1000.0)])
    rm = pd.DataFrame([dict(EDGE_UID="RM_a", STATION="PS1", DS_NODE="I1"),
                       dict(EDGE_UID="RM_b", STATION="PS1", DS_NODE="A1")])
    res = N.name_network(nodes, stations=st, rising_mains=rm, towns=towns, node_town=town)
    f = res.flags[res.flags.KIND == "station_town_ambiguous"]
    assert len(f) == 1 and f.REF.iloc[0] == "PS1"
    assert f.SIZE.iloc[0] == 2, "the flag must say how many towns were in play"


# ======================================================================================
# 2. NOTHING IS SILENTLY DROPPED (concept rule 7)
# ======================================================================================

def test_a_ds_node_that_names_a_missing_chamber_is_a_broken_link_not_an_outfall(towns):
    """A1 says it drains to GHOST. GHOST is not in the frame.

    Before the fix A1 was made a root, given its own subnetwork and named I-S02-SM-M001 -
    a name that asserts it discharges here - with zero flags. The link is BROKEN, and a
    broken link that reads as a design decision is the worst defect class in this project.
    """
    nodes = mk([
        ("T1", 100.0, 500.0, "T2", "trunk main"),
        ("T2", 100.0, 400.0, "", "trunk main"),
        ("A1", 150.0, 400.0, "GHOST", "sub main"),
        ("A2", 200.0, 420.0, "A1", "lateral"),
    ])
    res = N.name_network(nodes, towns=towns, node_town=["Ibri"] * 4)
    f = res.flags[res.flags.KIND == "node_ds_missing"]
    assert len(f) == 1 and f.REF.iloc[0] == "A1"
    assert f.SIZE.iloc[0] == 2, "the flag must carry how many chambers the break orphaned"
    assert "GHOST" in f.WHY.iloc[0]


def test_two_force_mains_on_one_pump_are_flagged_not_given_the_same_name(towns):
    """'I-P02, numbered with its pump' has no token for a twin main."""
    nodes = mk([("T1", 0.0, 0.0, "T2", "trunk main"), ("T2", 0.0, -10.0, "", "trunk main")])
    st = pd.DataFrame([dict(NODE_UID="P1", X=0.0, Y=-20.0)])
    rm = pd.DataFrame([dict(EDGE_UID="RM1", STATION="P1", DS_NODE="T2"),
                       dict(EDGE_UID="RM2", STATION="P1", DS_NODE="T2")])
    res = N.name_network(nodes, stations=st, rising_mains=rm, towns=towns,
                         node_town=["Ibri"] * 2)
    named = [v for v in res.rising_mains.NAME if v]
    assert len(named) == len(set(named)) == 1
    f = res.flags[res.flags.KIND == "rm_dup_station"]
    assert len(f) == 1 and f.REF.iloc[0] in set(res.rising_mains.EDGE_UID)


def test_the_two_causes_of_an_unnamed_conduit_are_different_flags(towns):
    """One kind for two causes cannot be filtered.

    `reach_no_us_node` documented 'US_NODE is not in the nodes frame' and was also raised
    for 'the upstream chamber is unnamed'. On the live 56,930-chamber graph that put 830
    rows of the second cause under the name of the first.
    """
    nodes = mk([("T1", 0.0, 0.0, "", "trunk main"),
                ("Q1", 0.0, 10.0, "T1", "lateral")])
    reaches = pd.DataFrame([dict(EDGE_UID="E1", US_NODE="Q1"),     # parent exists, unnamed
                            dict(EDGE_UID="E2", US_NODE="NOPE")])  # parent does not exist
    # both chambers sit outside every town and nothing downstream is in one, so their
    # subnetwork has no letter and neither chamber can be named
    res = N.name_network(nodes, reaches=reaches, towns=towns, node_town=["", ""])
    assert (res.nodes.NAME == "").all()
    kinds = dict(zip(res.flags.REF, res.flags.KIND))
    assert kinds["E1"] == "reach_us_unnamed"
    assert kinds["E2"] == "reach_no_us_node"


def test_a_conduit_is_still_named_when_its_upstream_manhole_could_not_be(towns):
    """NOT A FIX - a MEASUREMENT of an inconsistency the author's own numbers contain.

    A conduit takes its upstream chamber's NUMBER, and the number survives even when the
    chamber's NAME does not: a tier the grammar cannot express blanks the manhole name and
    leaves the conduit named for it. On the live 56,930-chamber graph 7,619 chambers are
    unnamed for that reason while their outgoing conduits are named, so a schedule keyed on
    'the conduit's upstream manhole' has thousands of blank cells against filled ones.
    Defensible - a C-name carries no tier token, so the grammar is not the obstacle - but it
    is a decision, and it should be a stated one rather than a side effect.
    """
    nodes = mk([("T1", 0.0, 0.0, "", "trunk main"),
                ("Q1", 0.0, 10.0, "T1", "boulevard")])   # tier the grammar refuses
    reaches = pd.DataFrame([dict(EDGE_UID="E1", US_NODE="Q1")])
    res = N.name_network(nodes, reaches=reaches, towns=towns, node_town=["Ibri"] * 2)
    assert res.nodes.set_index("NODE_UID").NAME["Q1"] == ""
    assert res.reaches.NAME.iloc[0] != "", "recorded behaviour, not an endorsement"
    assert "reach_us_unnamed" not in set(res.flags.KIND)


def test_every_flag_carries_a_size_of_at_least_one_element(towns):
    """SIZE was 0.0 on every per-element flag, so 'flagged with its size' meant a blank on
    all but two of the eight kinds."""
    nodes = mk([("Z1", 0.0, 0.0, "", "sub main"),
                ("Z2", 0.0, 10.0, "Z1", "boulevard"),
                ("Z3", 0.0, 20.0, "GHOST", "lateral"),
                ("Z4", 0.0, 30.0, "Z3", "lateral")])
    res = N.name_network(nodes, towns=towns, node_town=["Ibri"] * 4)
    assert len(res.flags) >= 2
    assert (res.flags.SIZE >= 1.0).all(), "a flag with SIZE 0 says nothing about the harm"
    assert len(set(res.flags.SIZE)) > 1, "SIZE must vary, or it is a constant column"


# ======================================================================================
# 3. IDENTITY IS UNIQUE BEFORE ANYTHING IS NAMED BY IT
# ======================================================================================

@pytest.mark.parametrize("layer", ["reaches", "stations", "rising_mains"])
def test_a_duplicate_key_is_refused_on_every_layer_not_only_on_the_nodes(towns, layer):
    """`name_map()` is the stability oracle and it is a dict keyed on the UID: a duplicate
    key collapses two rows into one, so a name that MOVED between runs could hide inside
    the one check written to catch it. Nodes were checked; nothing else was."""
    nodes = mk([("T1", 0.0, 0.0, "T2", "trunk main"), ("T2", 0.0, -10.0, "", "trunk main")])
    kw = dict(towns=towns, node_town=["Ibri"] * 2)
    if layer == "reaches":
        kw["reaches"] = pd.DataFrame([dict(EDGE_UID="E1", US_NODE="T1"),
                                      dict(EDGE_UID="E1", US_NODE="T2")])
    elif layer == "stations":
        kw["stations"] = pd.DataFrame([dict(NODE_UID="P1", X=0.0, Y=1.0),
                                       dict(NODE_UID="P1", X=1.0, Y=2.0)])
    else:
        kw["stations"] = pd.DataFrame([dict(NODE_UID="P1", X=0.0, Y=1.0)])
        kw["rising_mains"] = pd.DataFrame([dict(EDGE_UID="RM1", STATION="P1", DS_NODE="T2"),
                                           dict(EDGE_UID="RM1", STATION="P1", DS_NODE="T2")])
    with pytest.raises(N.NamingError, match="duplicate keys"):
        N.name_network(nodes, **kw)


# ======================================================================================
# 4. A GUARD THAT MATCHES NOTHING IS NOT A GUARD
# ======================================================================================

def test_the_main_pipe_tier_spelled_with_an_underscore_still_finds_the_main_pipe(towns):
    """`main_tier='trunk_main'` produced an EMPTY mask, so concept rule 2 stopped being
    applied and every branch merged into one subnetwork - with `main_nodes: 0` published
    and nothing saying the rule had been switched off. contract.TIER_ALIASES exists
    precisely because that spelling occurs in the data."""
    nodes = mk([("T1", 100.0, 500.0, "T2", "trunk main"),
                ("T2", 100.0, 400.0, "", "trunk main"),
                ("A1", 150.0, 400.0, "T2", "sub main")])
    kw = dict(towns=towns, node_town=["Ibri"] * 3)
    canon = N.name_network(nodes, **kw)
    for spelling in ("trunk_main", "trunkmain", "TRUNK MAIN", "trunk-main"):
        alt = N.name_network(nodes, main_tier=spelling, **kw)
        assert alt.counts["main_nodes"] == canon.counts["main_nodes"] == 2
        assert alt.counts["subnets"] == canon.counts["subnets"] == 2
        assert alt.name_map() == canon.name_map()


def test_an_unknown_main_tier_is_refused_rather_than_matching_nothing(towns):
    nodes = mk([("T1", 0.0, 0.0, "", "trunk main"),
                ("A1", 1.0, 1.0, "T1", "sub main")])
    with pytest.raises(N.NamingError, match="concept rule 2"):
        N.name_network(nodes, towns=towns, node_town=["Ibri"] * 2, main_tier="boulevard")


def test_a_coordinate_that_is_not_a_number_is_refused_not_cast(towns):
    """np.nan.astype(int64) is INT64_MIN behind a RuntimeWarning. Every element with no
    coordinate sorted to one extreme and was named as though it had a position."""
    nodes = mk([("T1", 100.0, 500.0, "T2", "trunk main"),
                ("T2", 100.0, 400.0, "", "trunk main"),
                ("A1", np.nan, np.nan, "", "sub main")])
    with pytest.raises(N.NamingError, match="SORT KEY"):
        N.name_network(nodes, towns=towns, node_town=["Ibri"] * 3)


# ======================================================================================
# 5. PUBLISHED COUNTS AND COLUMNS MUST MEAN WHAT THEY SAY
# ======================================================================================

def test_the_published_pump_pad_is_the_width_that_was_actually_written(towns):
    """It was computed from a value_counts() that INCLUDED the blank code, so a run with
    120 unnamed stations published pump_pad=3 while every name written was two digits -
    and it was never applied to anything."""
    nodes = mk([("T1", 0.0, 0.0, "T2", "trunk main"), ("T2", 0.0, -10.0, "", "trunk main")])
    st = pd.DataFrame([dict(NODE_UID=f"P{i:03d}", X=float(i), Y=float(1000 - i))
                       for i in range(30)])
    rm = pd.DataFrame([dict(EDGE_UID=f"RM{i:03d}", STATION=f"P{i:03d}", DS_NODE="T2")
                       for i in range(30)])
    res = N.name_network(nodes, stations=st, rising_mains=rm, towns=towns,
                         node_town=["Ibri"] * 2)
    widths = {len(v.split("PMP")[1]) for v in res.stations.NAME if v}
    assert res.counts["stations_named"] == 30
    assert widths == {res.counts["pump_pad"]}


def test_node_towns_separates_the_chambers_own_town_from_the_one_in_its_name(towns):
    """`nodes.TOWN` is the SUBNETWORK's town (the plurality of its members); the TOWN column
    of `node_towns` is the CHAMBER's own. On a subnetwork that straddles a boundary they
    differ, and one column name for both is how SLOPE_PCT got itself banned."""
    rows = [("T1", 0.0, 0.0, "", "trunk main"),
            ("C1", 0.0, 10.0, "T1", "sub main"),      # stands in Ibri
            ("C2", 0.0, 20.0, "C1", "lateral"),
            ("C3", 0.0, 30.0, "C2", "lateral"),
            ("C4", 0.0, 40.0, "C3", "lateral")]
    res = N.name_network(mk(rows), towns=towns,
                         node_town=["Ibri", "Ibri", "Al Araqi", "Al Araqi", "Al Araqi"])
    nt = res.node_towns.set_index("NODE_UID")
    assert nt.TOWN["C1"] == "I", "C1 stands in Ibri"
    assert nt.TOWN_NAMED["C1"] == "A", "but its name carries its subnetwork's letter"
    assert res.nodes.set_index("NODE_UID").NAME["C1"].startswith("A-")
    published = res.nodes.set_index("NODE_UID").TOWN
    assert (nt.TOWN_NAMED.reindex(published.index).to_numpy()
            == published.to_numpy()).all(), \
        "TOWN_NAMED must be exactly what the published layer carries"


# ======================================================================================
# 6. THE FREEZE — the checksum only ever guarded one of the two files
# ======================================================================================

def test_a_hand_edited_csv_is_caught_even_though_the_json_still_checksums(tmp_path, towns):
    """The CSV is the sheet a PERSON reads, so it is the sheet a person edits - and it was
    ignored entirely whenever the manifest was present. The manifest passed its own sha256,
    the codes came back from the manifest, and the issued sheet on disk said something else
    with nothing reporting the disagreement."""
    p = N.write_town_prefixes(towns, str(tmp_path / "pref.csv"))
    txt = open(p, encoding="utf-8").read().replace(",I,", ",Z,")
    open(p, "w", encoding="utf-8").write(txt)
    with pytest.raises(N.NamingError, match="disagree"):
        N.load_town_prefixes(p)


def test_a_csv_with_no_manifest_is_refused_rather_than_trusted(tmp_path, towns):
    """Delete the manifest and the tamper the manifest exists to refuse walks in through
    the CSV door: before the fix, an edited CSV with no JSON beside it loaded silently and
    Ibri came back as 'Z'."""
    p = N.write_town_prefixes(towns, str(tmp_path / "pref.csv"))
    import os as _os
    _os.remove(_os.path.splitext(p)[0] + ".json")
    with pytest.raises(N.NamingError, match="no checksum"):
        N.load_town_prefixes(p)


# ======================================================================================
# 7. THE KNOWN, UNFIXED ONE — recorded so it cannot be forgotten
# ======================================================================================

def test_one_town_crossing_99_subnetworks_renames_every_subnetwork_in_the_design(towns):
    """NOT A FIX - a MEASUREMENT, kept so the size of the exposure is on the record.

    The S-token width is recomputed from the design (the town with the most subnetworks),
    so the day one town crosses 99 every gravity name in EVERY town changes. Rule (e) - the
    same design rebuilt gets the same names - still holds; a design that GROWS does not.
    The manhole number takes the opposite choice: fixed at three digits, and a subnetwork
    past 999 is FLAGGED rather than repadded. The two want reconciling, and that is the
    engineer's call, not a reviewer's.

    Measured on the live 56,930-chamber graph 2026-09-06: 278 subnetworks, busiest town 58.
    Forty-two more subnetworks in that one town renames the whole design.
    """
    def build(n_branch):
        rows = [("T0", 0.0, 0.0, "", "trunk main")]
        rows += [(f"S{i:03d}", 10.0 + i, 1000.0 - i, "T0", "sub main")
                 for i in range(n_branch)]
        return mk(rows)

    a = build(98)
    b = build(99)
    ra = N.name_network(a, towns=towns, node_town=["Ibri"] * len(a))
    rb = N.name_network(b, towns=towns, node_town=["Ibri"] * len(b))
    assert ra.counts["subnet_pad"] == 2 and rb.counts["subnet_pad"] == 3
    ma, mb = ra.name_map(), rb.name_map()
    moved = [k for k in ma if ma[k] != mb.get(k)]
    assert len(moved) == len(ma), "adding one branch renamed every element already there"
    assert ma["S000"] == "I-S02-SM-M001" and mb["S000"] == "I-S002-SM-M001"
