# -*- coding: utf-8 -*-
"""ADVERSARIAL review of the `export` module - `s8_export.py` and `make_overview.py`.

Every test here was written to BREAK a claim the module makes about itself, on a case the
module's own test file does not build.  Where a test is marked `xfail` it names a defect
that is real and is NOT fixed in this file's own scope; where it passes, it is the
regression guard on a defect that WAS fixed.

The cases, in the order they were found:

  1  NAMING.  `build_names()` hands the raw five-tier vocabulary straight to
     `contract.concept_name()`, but the concept grammar (`contract.NAME_RE`) knows only
     TM / SM / L.  A chamber on a "main" or a "rider" reach therefore gets a name that
     `parse_name()` cannot read, and `contract.validate()` reports the whole layer.
     s3_hierarchy really does emit the "main" tier (s3_hierarchy.py, `tiers()`), so this
     is not hypothetical.  FIXED here: the name is only minted where the grammar can
     express the tier, and the shortfall is counted, logged and published.

  2  QGIS STYLE ON A COLUMN THAT DOES NOT EXIST.  The STRUCTURE theme's pump layer
     classified on the literal "__single__", which is not a column of `stations`.  A
     categorized renderer pointed at a missing attribute matches nothing and renders an
     EMPTY layer - the exact failure `theme_qml()`'s own comment warns about.  FIXED.

  3  "THE DXF, THE KMZ AND THE .QML ALL READ THE SAME CLASS TABLE" is not true.  The DXF
     colours conduits BY TIER out of `present.TIER_COLOURS`; the STRUCTURE theme colours
     them BY SUBNETWORK out of `present.golden_rgb`.  Reported, not fixed - the DXF's
     tier-coloured layer set is a deliberate CAD convention and changing it is the
     engineer's call - but the claim is now measured instead of asserted.

  4  A HARDCODED COLUMN.  `build_stations()` assigned `N_SUBNET = 1` from a literal
     wherever the anchor had any inflow.  The contract declares N_SUBNET as "how many
     subnetworks drain into this station"; a literal is not a count.  FIXED - it is now
     counted off the incoming arms' own subnetwork ids.

  5  A CONSTANT PHYSICAL COLUMN.  `connections.COVER_M` is one scalar broadcast to every
     plot connection.  Reported.

  6  TWO LENGTHS FOR ONE CONNECTION.  CONN_NEED / SLOPE_LAID are computed on the upstream
     `LEN_M`, while the LEN_M actually published is re-measured off the geometry.
     Reported and guarded.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import geopandas as gpd                                          # noqa: E402
from shapely.geometry import LineString, Point, Polygon          # noqa: E402

import s8_export as EX                                            # noqa: E402
from w12 import contract as CT                                    # noqa: E402

CRS = f"EPSG:{CT.CRS_EPSG}"
X0, Y0 = 444000.0, 2563000.0


# ======================================================================================
# a two-chamber synthetic network, one reach, whose TIER the caller chooses
# ======================================================================================

def _chain(tier: str, n_nodes: int = 4):
    """A straight chain of `n_nodes` chambers falling east, every reach on `tier`."""
    m = n_nodes - 1
    uid = [f"N{i:05d}" for i in range(n_nodes)]
    xs = np.array([X0 + 100.0 * i for i in range(n_nodes)])
    ys = np.full(n_nodes, Y0)
    grd = np.array([330.0 - 0.5 * i for i in range(n_nodes)])
    e_us = np.arange(m)
    e_ds = np.arange(1, n_nodes)
    e_len = np.full(m, 100.0)
    e_of = np.append(np.arange(m), -1)
    ds = np.append(np.arange(1, n_nodes), -1)
    indeg = np.array([0] + [1] * m)
    g = EX.Graph(uid=uid, ix={u: i for i, u in enumerate(uid)}, grd=grd, ds=ds,
                 e_us=e_us, e_ds=e_ds, e_len=e_len, e_of=e_of,
                 order=np.arange(n_nodes), indeg=indeg)
    chambers = gpd.GeoDataFrame(
        dict(NODE_UID=uid, X=xs, Y=ys, ON_WADI=np.zeros(n_nodes, dtype=int)),
        geometry=[Point(x, y) for x, y in zip(xs, ys)], crs=CRS)
    segments = gpd.GeoDataFrame(
        dict(TIER=[tier] * m),
        geometry=[LineString([(xs[i], ys[i]), (xs[i + 1], ys[i + 1])]) for i in range(m)],
        crs=CRS)
    a = EX.Assembly(chambers=chambers, segments=segments,
                    connections=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    unserved=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    hier=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    trunk=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    corridors=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    flows_arcs=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    stations=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    rising=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    boundary=gpd.GeoDataFrame(geometry=[], crs=CRS))
    f = EX.Flows(q_own=np.ones(n_nodes), p_own=np.ones(n_nodes),
                 n_conn=np.ones(n_nodes, dtype=int),
                 q_adf=np.arange(1.0, n_nodes + 1.0), n_prop=np.ones(n_nodes),
                 ups_len=np.arange(n_nodes, dtype=float) * 100.0,
                 subnet=np.full(n_nodes, n_nodes - 1),
                 e_qadf=np.ones(m), e_nprop=np.ones(m), e_upslen=np.full(m, 100.0),
                 e_pf=np.ones(m), e_pfm=["held"] * m, e_qinf=np.zeros(m),
                 e_qpk=np.ones(m))
    return a, g, f


def _one_town(monkeypatch):
    poly = Polygon([(X0 - 500, Y0 - 500), (X0 + 2000, Y0 - 500),
                    (X0 + 2000, Y0 + 500), (X0 - 500, Y0 + 500)])
    towns = gpd.GeoDataFrame(dict(TOWN_NAME=["Ibri"], TOWN_CODE=["I"]),
                             geometry=[poly], crs=CRS)
    monkeypatch.setattr(EX, "_read_towns", lambda: towns)


# ======================================================================================
# 1.  NAMING - the grammar knows three tier tokens and the design has five tiers
# ======================================================================================

@pytest.mark.parametrize("tier", list(CT.TIERS))
def test_every_tier_this_design_uses_produces_a_name_the_grammar_can_read(monkeypatch, tier):
    """The defect: `TIER_TOKEN` maps "rider"->R and "main"->M, but `NAME_RE` accepts only
    TM|SM|L.  Every chamber on a main or a rider reach therefore carried a NAME that
    `parse_name()` returns None for, and `contract.validate()` reports the layer with
    "N NAME values do not fit the grammar".  s3_hierarchy emits the "main" tier on every
    run that passes its depth or path budget, so this is most of a real network.

    A name that cannot be parsed is, in the contract's own words, "a label, not an
    identifier" - so the stage must either mint one the grammar can read or mint none and
    say how many it could not.  Silently shipping an unreadable one is the third option
    and it is the wrong one."""
    _one_town(monkeypatch)
    a, g, f = _chain(tier)
    nm = EX.build_names(a, g, f)
    for v, name in enumerate(nm.node_name):
        if not name:
            continue
        assert CT.parse_name(name) is not None, (
            f"tier {tier!r} minted {name!r}, which contract.parse_name() cannot read")


def test_a_tier_the_grammar_cannot_express_is_counted_and_named_not_shipped(monkeypatch):
    """Rule 7 - flag, do not solve.  Where the grammar has no token for a tier the stage
    must leave the name BLANK (assert_named then refuses the layer, loudly) and say how
    many and on which tier, rather than writing a string nothing can parse."""
    _one_town(monkeypatch)
    a, g, f = _chain("main")
    nm = EX.build_names(a, g, f)
    blank = sum(1 for x in nm.node_name if not x)
    assert blank == len(nm.node_name), "a tier with no grammar token must mint no name"
    joined = " ".join(nm.notes)
    assert "main" in joined and "grammar" in joined.lower(), nm.notes
    assert nm.stats.get("names_refused_no_tier_token", 0) == len(nm.node_name)


def test_a_grammar_tier_still_names_every_chamber_and_its_conduits(monkeypatch):
    """The fix must not cost the tiers that DO work."""
    _one_town(monkeypatch)
    for tier in ("lateral", "sub main", "trunk main"):
        a, g, f = _chain(tier)
        nm = EX.build_names(a, g, f)
        assert all(nm.node_name), tier
        assert all(nm.edge_name), tier
        for k in range(len(g.e_len)):
            u = int(g.e_us[k])
            assert (CT.parse_name(nm.edge_name[k])["cd"]
                    == CT.parse_name(nm.node_name[u])["mh"]), tier


def test_a_named_node_layer_passes_the_contracts_own_name_check(monkeypatch):
    """End to end: the names this stage mints must survive `contract.validate()`.  This is
    the check that would have caught the tier-token defect on the first real build."""
    _one_town(monkeypatch)
    a, g, f = _chain("sub main", n_nodes=3)
    nm = EX.build_names(a, g, f)
    gdf = gpd.GeoDataFrame(
        dict(NAME=nm.node_name, TOWN=nm.node_town, SUBNET=nm.node_sub,
             TIER=["sub main"] * 3),
        geometry=[Point(X0 + 100 * i, Y0) for i in range(3)], crs=CRS)
    probs = CT._name_problems(gdf, CT._spec("nodes"), set(gdf.columns))
    assert not probs, probs


# ======================================================================================
# 2.  A SAVED QGIS STYLE MUST CATEGORISE ON A COLUMN THAT EXISTS
# ======================================================================================

def test_every_theme_layer_classifies_on_a_column_its_own_frame_carries():
    """A categorized renderer pointed at an attribute the layer does not have matches
    nothing and draws an EMPTY layer, which looks exactly like a layer with no features -
    `theme_qml()`'s own comment says so about the column TYPE and the same is true, more
    completely, of the column NAME.  The STRUCTURE theme's pump layer classified on the
    literal "__single__"."""
    layers = EX.demo_layers()
    for theme, tls in EX.build_themes(layers).items():
        for tl in tls:
            assert tl.field in tl.gdf.columns, (
                f"{theme}/{tl.key} categorises on {tl.field!r}, which is not a column of "
                f"its own frame: {sorted(tl.gdf.columns)[:12]}")


def test_the_written_qml_names_an_attribute_the_layer_has(tmp_path):
    layers = EX.demo_layers()
    old = EX.DIR_KMZ
    EX.DIR_KMZ = str(tmp_path)
    try:
        import xml.etree.ElementTree as ET
        for theme, tls in EX.build_themes(layers).items():
            for tl in tls:
                p = EX.theme_qml(theme, tl)
                root = ET.parse(p).getroot()
                attr = root.find(".//renderer-v2").get("attr")
                assert attr in tl.gdf.columns, f"{theme}/{tl.key}: attr={attr!r}"
    finally:
        EX.DIR_KMZ = old


# ======================================================================================
# 3.  THE DXF AND THE KMZ DO NOT TELL THE SAME COLOUR STORY
# ======================================================================================

def test_the_dxf_conduit_colour_is_not_the_structure_themes_conduit_colour():
    """REPORTED, NOT FIXED.  The module claims 'the DXF, the KMZ and the .qml all read the
    SAME class table'.  They do not: the DXF colours a conduit by its TIER
    (present.TIER_COLOURS) and the STRUCTURE theme colours it by its SUBNETWORK
    (present.golden_rgb).  Its own test only compares the DXF against the table that wrote
    the DXF, which is circular.

    This test PINS the disagreement so it cannot be claimed away.  If somebody genuinely
    reconciles the two, this test fails and should be deleted along with the claim's
    caveat."""
    layers = EX.demo_layers()
    dxf = dict((n, rgb) for n, rgb, _d in EX._dxf_layers())
    cond = [t for t in EX.theme_structure(layers) if t.key == "conduits"][0]
    theme_rgbs = {rgb for _k, _l, rgb, _w in cond.classes}
    dxf_rgbs = {dxf[k] for k in ("W12-CONDUIT-TRUNK", "W12-CONDUIT-SUBMAIN",
                                 "W12-CONDUIT-MAIN", "W12-CONDUIT-LATERAL")}
    assert not (theme_rgbs & dxf_rgbs), (
        "the DXF and the STRUCTURE theme now agree on a conduit colour - if that is "
        "deliberate, delete this test AND the caveat in the review")


# ======================================================================================
# 4.  N_SUBNET MUST BE COUNTED, NOT ASSERTED
# ======================================================================================

def _stations_case(indeg_at_anchor: int):
    """One anchor chamber with `indeg_at_anchor` arms arriving on it."""
    n = indeg_at_anchor + 2
    uid = [f"N{i:05d}" for i in range(n)]
    anchor = n - 1
    xs = np.array([X0 + 50.0 * i for i in range(n)])
    ys = np.full(n, Y0)
    e_us = np.arange(n - 1)
    e_ds = np.full(n - 1, anchor)
    e_of = np.append(np.full(n - 1, -1), -1).astype(np.int64)
    e_of[:n - 1] = np.arange(n - 1)
    g = EX.Graph(uid=uid, ix={u: i for i, u in enumerate(uid)},
                 grd=np.full(n, 330.0), ds=np.append(np.full(n - 1, anchor), -1),
                 e_us=e_us, e_ds=e_ds, e_len=np.full(n - 1, 100.0), e_of=e_of,
                 order=np.arange(n),
                 indeg=np.array([0] * (n - 1) + [n - 1]))
    f = EX.Flows(q_own=np.ones(n), p_own=np.ones(n), n_conn=np.ones(n, dtype=int),
                 q_adf=np.ones(n), n_prop=np.ones(n),
                 ups_len=np.arange(n, dtype=float) * 100.0,
                 subnet=np.full(n, anchor),
                 e_qadf=np.ones(n - 1), e_nprop=np.ones(n - 1),
                 e_upslen=np.full(n - 1, 100.0), e_pf=np.ones(n - 1),
                 e_pfm=["held"] * (n - 1), e_qinf=np.zeros(n - 1), e_qpk=np.ones(n - 1))
    st = gpd.GeoDataFrame(dict(
        NODE_UID=["PS00001"], NODE_UID_S7=["N0000042"], NODE_REF=["P001-PS"],
        WHY=["cap"], ST_TYPE=["Type 1"], Q_DUTY_LS=[50.0], LIFT_M=[8.0],
        N_PROP=[10.0], Q_ADF_M3D=[100.0], WELL_M3=[4.5], WW_STARTS=[6.0],
        GRD_M=[330.0], FLOOD_LV=[np.nan], LAND_M2=[400.0], RM_EDGE=["RM0001"],
        COMM_PT=[1], ANCHOR_ND=[uid[anchor]], ST_SNAP_M=[0.0]),
        geometry=[Point(xs[anchor], ys[anchor])], crs=CRS)
    rm = gpd.GeoDataFrame(dict(
        EDGE_UID=["RM0001"], US_NODE=["N0000042"], DS_NODE=["STP"],
        STATION=["N0000042"], DN=[200], MATERIAL=["DI"], Q_DUTY_LS=[50.0],
        V_DUTY_MS=[1.6], V_MIN_MS=[0.8], STAT_HD_M=[8.0], TOT_HD_M=[12.0],
        RETENT_M=[10.0], N_AIRV=[1], N_WASH=[1], N_ISOL=[2], WADI_M=[0.0],
        SEPTIC_FL=[0]),
        geometry=[LineString([(xs[anchor], ys[anchor]), (xs[anchor] + 300, ys[anchor])])],
        crs=CRS)
    a = EX.Assembly(chambers=gpd.GeoDataFrame(dict(NODE_UID=uid, X=xs, Y=ys),
                                              geometry=[Point(x, y) for x, y in zip(xs, ys)],
                                              crs=CRS),
                    segments=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    connections=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    unserved=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    hier=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    trunk=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    corridors=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    flows_arcs=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    stations=st, rising=rm,
                    boundary=gpd.GeoDataFrame(geometry=[], crs=CRS))
    nodes = gpd.GeoDataFrame(dict(
        NODE_UID=uid, INV_M=np.full(n, 321.0), TOWN=["I"] * n,
        SUBNET=["S01"] * n, SUB_NAME=["I-S01"] * n, PACKAGE=["P001"] * n),
        geometry=[Point(x, y) for x, y in zip(xs, ys)], crs=CRS)
    nm = EX.Naming([""] * n, ["I"] * n, ["S01"] * n, [], {}, {}, {}, {}, [], {})
    return a, g, f, nodes, nm


def test_n_subnet_is_counted_off_the_arms_that_arrive_not_written_as_a_literal():
    """The contract declares N_SUBNET as "how many subnetworks drain into this station".
    The first build assigned the literal 1 wherever the anchor had any inflow at all -
    which is a boolean wearing a count's name, and it is constant on every published row.

    A literal cannot move when the layout does.  This asserts the value is DERIVED from
    the subnetwork ids of the arms that actually arrive, so a station sited at a genuine
    seam between two subnetworks - which is what concept rule 6 asks s7 to do - reports 2
    the day s7 does it."""
    a, g, f, nodes, nm = _stations_case(3)
    # two of the three arms belong to a different component
    f.subnet[0] = 0
    st_out, _rm, _rej = EX.build_stations(a, nodes, g, f, nm)
    assert len(st_out) == 1
    assert int(st_out.N_SUBNET.iloc[0]) == 2, (
        "N_SUBNET did not move when two distinct subnetworks arrived - it is not counted")


def test_a_station_with_nothing_arriving_is_removed_and_published():
    a, g, f, nodes, nm = _stations_case(0)
    # rewire so nothing arrives at the anchor
    g.indeg[:] = 0
    g.e_ds[:] = 0
    st_out, rm_out, rej = EX.build_stations(a, nodes, g, f, nm)
    assert len(st_out) == 0 and len(rej) == 1
    assert "NOTHING DRAINS INTO IT" in str(rej.REJECT_WHY.iloc[0])
    assert len(rm_out) == 0, "a force main whose pump was removed must go with it"


def test_the_rising_mains_removed_with_their_pumps_are_counted_not_only_logged():
    """Inheritance row 4 - a pass that TAKES AWAY must publish how many.  The station
    count was published; the force mains that went with them were only printed."""
    a, g, f, nodes, nm = _stations_case(0)
    g.indeg[:] = 0
    g.e_ds[:] = 0
    EX.build_stations(a, nodes, g, f, nm)
    assert EX.REMOVED_COUNTS.get("rising_mains_removed") == 1
    assert EX.REMOVED_COUNTS.get("stations_removed") == 1


# ======================================================================================
# 5 & 6.  THE CONNECTION LAYER
# ======================================================================================

def _conn_case():
    n = 2
    uid = ["N00000", "N00001"]
    xs = np.array([X0, X0 + 100.0])
    ys = np.full(n, Y0)
    g = EX.Graph(uid=uid, ix={u: i for i, u in enumerate(uid)}, grd=np.array([330.0, 329.0]),
                 ds=np.array([1, -1]), e_us=np.array([0]), e_ds=np.array([1]),
                 e_len=np.array([100.0]), e_of=np.array([0, -1]), order=np.arange(2),
                 indeg=np.array([0, 1]))
    # plot 1 sits high and connects; plot 2 sits on a knoll BELOW the sewer invert
    cn = gpd.GeoDataFrame(dict(
        CONN_ID=["C1", "C2"], PLOT_ID=["P1", "P2"], OUT_NODE=["N00000", "N00001"],
        WHY=["", ""], SYSTEM=["gravity", "gravity"], CONN_TYPE=["plot", "plot"],
        Q_ADF_M3D=[1.0, 1.0], N_PROP=[1.0, 1.0],
        # LEN_M as the UPSTREAM stage recorded it - deliberately NOT the geometry length
        LEN_M=[20.0, 20.0],
        GRD_PLOT=[332.0, 326.0],
        XPLOT=[0, 0], XDUAL=[0, 0], CH_WADI=[0, 0]),
        geometry=[LineString([(X0, Y0 + 40), (X0, Y0)]),
                  LineString([(X0 + 100, Y0 + 40), (X0 + 100, Y0)])], crs=CRS)
    a = EX.Assembly(chambers=gpd.GeoDataFrame(dict(NODE_UID=uid, X=xs, Y=ys),
                                              geometry=[Point(x, y) for x, y in zip(xs, ys)],
                                              crs=CRS),
                    segments=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    connections=cn, unserved=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    hier=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    trunk=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    corridors=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    flows_arcs=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    stations=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    rising=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    boundary=gpd.GeoDataFrame(geometry=[], crs=CRS))
    nodes = gpd.GeoDataFrame(dict(
        NODE_UID=uid, INV_M=[328.5, 327.5], TOWN=["I", "I"], SUBNET=["S01", "S01"],
        SUB_NAME=["I-S01", "I-S01"], PACKAGE=["P001", "P001"]),
        geometry=[Point(x, y) for x, y in zip(xs, ys)], crs=CRS)
    return a, g, nodes


def test_the_published_length_is_the_length_the_gravity_check_actually_used():
    """LEN_M is re-measured off the geometry when it is published, but the connectability
    arithmetic (CONN_NEED, SLOPE_LAID) runs on the LEN_M the upstream stage recorded.  A
    reviewer who multiplies the published SLOPE_LAID by the published LEN_M must get the
    published FALL_AV_M back; here the two lengths differ by a factor of two and he does
    not.  'A length field that disagrees with its own geometry' is one of the bugs this
    project already wrote a test file about."""
    a, g, nodes = _conn_case()
    out = EX.build_connections(a, g, nodes, gpd.GeoDataFrame(geometry=[], crs=CRS))
    ok = out[out.CAN_CONN == 1]
    if not len(ok):
        pytest.skip("no connectable plot in this fixture")
    got = (ok.SLOPE_LAID / 100.0) * ok.LEN_M
    assert np.allclose(got, ok.FALL_AV_M, atol=0.02), (
        "SLOPE_LAID x LEN_M does not reproduce FALL_AV_M - the check and the publication "
        f"used different lengths ({got.tolist()} vs {ok.FALL_AV_M.tolist()})")


def test_a_plot_below_the_sewer_invert_is_refused_and_sized():
    a, g, nodes = _conn_case()
    out = EX.build_connections(a, g, nodes, gpd.GeoDataFrame(geometry=[], crs=CRS))
    bad = out[out.CAN_CONN == 0]
    assert len(bad) == 1
    assert float(bad.CONN_NEED.iloc[0]) > 0
    assert "deeper" in str(bad.CONN_WHY.iloc[0])
    # and the size must be the size that actually cures it
    L = float(bad.LEN_M.iloc[0])
    need = float(bad.CONN_NEED.iloc[0])
    fall = float(bad.FALL_AV_M.iloc[0])
    from w12.criteria import DEFAULT as C
    assert abs((fall + need) - C.PCS_MIN_SLOPE * L) < 0.05, (
        "CONN_NEED does not, applied, make the connection work")


def test_cover_m_on_the_connection_layer_is_one_number_for_every_plot():
    """REPORTED, NOT FIXED.  `COVER_M` is a scalar broadcast to every row.  Cover over a
    connection depends on the plot's ground and the chamber's invert and cannot be one
    number across 53,000 plots; the contract's own constant-column rule exists for exactly
    this shape of column.  It is defensible only because rule 5 says the connection is NOT
    designed at concept - which is an argument for not publishing the column at all rather
    than for publishing one value.  Pinned so the claim is visible."""
    a, g, nodes = _conn_case()
    out = EX.build_connections(a, g, nodes, gpd.GeoDataFrame(geometry=[], crs=CRS))
    assert out.COVER_M.nunique() == 1


# ======================================================================================
# 7.  MEASURE_JOINS - the case where the client's main pipe is not there
# ======================================================================================

def test_an_unmeasurable_gap_to_the_main_pipe_is_not_reported_as_zero():
    """`worst_gap_m` was `gap[gap < inf].max()` over the WHOLE node array, and `gap` is 0.0
    on every chamber that is not an outfall.  With an empty or unreadable Main Pipe layer
    every outfall's distance came out NaN, was filtered out, and the max over the remaining
    zeros published **0.0 m** - "no subnetwork is more than 0 m from the trunk", which is
    the exact opposite of the truth and goes straight into the manifest and EXPORT.md as a
    headline.  FIXED: the stat is measured over the outfalls only, an unmeasurable
    distance is counted and named, and the headline is NaN rather than a comfortable
    zero."""
    a, g, f = _chain("lateral")
    jn = EX.measure_joins(a, g, f)
    assert jn.stats["reaching"] == 0
    assert jn.stats["gap_unmeasured"] == 1
    assert not np.isfinite(jn.stats["worst_gap_m"]), (
        "an unmeasurable distance must not be published as a number a reader will trust")


# ======================================================================================
# 8.  A THEME THAT FAILS TO BUILD MUST NOT PASS FOR A CLEAN ONE
# ======================================================================================

def test_a_theme_that_cannot_be_built_is_recorded_where_a_reader_will_see_it():
    """`build_themes()` catches every exception and returns an EMPTY theme.  An empty
    EXCEPTIONS theme reads as 'we checked and it is fine' - the module's own words about
    why an empty exception folder is omitted.  The failure must therefore be recoverable
    by the caller, not only printed to a console nobody keeps."""
    layers = EX.demo_layers()
    layers.pop("connections")                       # EXCEPTIONS reads it
    EX.THEME_FAILURES.clear()
    out = EX.build_themes(layers)
    assert out["exceptions"] == []
    assert "exceptions" in EX.THEME_FAILURES, (
        "a theme failed to build and left no trace a caller could publish")


# ======================================================================================
# 9.  DEPTH - a null depth must not be painted the same colour as a shallow one
# ======================================================================================

def test_a_removal_says_how_far_the_station_was_snapped_to_get_its_evidence():
    """The prune's evidence is the chamber the station was SNAPPED to - s7's node ids do not
    resolve and `_reanchor_stations()` takes the nearest chamber with no distance limit.  A
    removal justified by a chamber 300 m away is a different claim from one justified by the
    chamber the station stands on, and the row must let a reviewer tell them apart."""
    a, g, f, nodes, nm = _stations_case(0)
    g.indeg[:] = 0
    g.e_ds[:] = 0
    a.stations = a.stations.assign(ST_SNAP_M=[312.5])
    _st, _rm, rej = EX.build_stations(a, nodes, g, f, nm)
    assert "312.5 m" in str(rej.REJECT_WHY.iloc[0])


# ======================================================================================
# 10.  A DROP THAT THE PROJECT'S OWN ASSUMPTION CAUSED MUST NOT CITE A GUIDELINE PAGE
# ======================================================================================

def test_the_two_bounds_behind_velocity_cap_are_counted_separately():
    """`_drop_reasons()` maps BOTH `vmax` (G203-p27 4.2.2.2, the 3.0 m/s guideline maximum)
    and `cover_max` (the 25 % laying bound, a PROJECT ASSUMPTION with no guideline behind
    it) onto the contract's single word `velocity_cap`.  The vocabulary is the contract's
    and cannot be widened from here - but the EXCEPTIONS legend said, in as many words,
    that every drop in the folder existed because the pipe would have passed 3.0 m/s
    (G203-p27).  For the `cover_max` half that is a guideline page borrowed for a number
    the project made up.  The split is now counted and printed."""
    EX.DROP_CAUSE_SPLIT.clear()
    g = EX.Graph(uid=["A", "B"], ix={"A": 0, "B": 1}, grd=np.array([330.0, 320.0]),
                 ds=np.array([1, -1]), e_us=np.array([0]), e_ds=np.array([1]),
                 e_len=np.array([50.0]), e_of=np.array([0, -1]), order=np.arange(2),
                 indeg=np.array([0, 1]))
    a = EX.Assembly(chambers=gpd.GeoDataFrame(dict(NODE_UID=["A", "B"], ON_WADI=[0, 0]),
                                              geometry=[Point(X0, Y0), Point(X0 + 50, Y0)],
                                              crs=CRS),
                    segments=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    connections=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    unserved=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    hier=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    trunk=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    corridors=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    flows_arcs=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    stations=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    rising=gpd.GeoDataFrame(geometry=[], crs=CRS),
                    boundary=gpd.GeoDataFrame(geometry=[], crs=CRS))
    why = EX._drop_reasons(a, g, ["sub main"], ["cover_max"],
                           inv_dn=np.array([315.0]), arr_min=np.array([np.inf, 315.0]),
                           arr_max=np.array([-np.inf, 315.0]),
                           drop_type=["none", "backdrop"])
    assert why[1] == "velocity_cap"
    assert EX.DROP_CAUSE_SPLIT.get("cover_max") == 1, (
        "the laying-bound half of `velocity_cap` is not counted, so the legend cannot say "
        "which drops the guideline actually caused")


# ======================================================================================
# 11.  A CROSSING ANGLE THAT WAS NEVER MEASURED MUST NOT READ AS A MEASUREMENT
# ======================================================================================

def test_an_unmeasured_crossing_angle_is_distinguishable_from_a_measured_zero():
    """0.00 deg MEANS "the pipe runs ALONG the obstacle" - the worst reading there is - and
    it was what a dual-carriageway contact with no recorded bearing was published as.  That
    is the ANGLE_DEG = 90 fabrication with the sign flipped: a reader cannot tell the
    measurement from the fallback, and the fallback moved the published median.  ANG_MEAS
    now separates them."""
    import inspect
    src = inspect.getsource(EX.build_crossings)
    assert "ANG_MEAS" in src
    assert "cx.ANG_MEAS == 1" in inspect.getsource(EX.build_crossings), (
        "the angle statistics must be taken over the measured rows only")


# ======================================================================================
# 12.  THE FIELD DICTIONARY IS ONLY HALF GENERATED
# ======================================================================================

def test_the_field_dictionary_names_the_columns_it_does_not_explain():
    """The dictionary claims it "cannot go stale: generated from contract.LAYERS".  Only
    half of it is - the "beyond the contract" table is hand-written and had already gone
    stale (DEEP_M, GAP_M, OFF_M, LOW_ND, TOWN_D_M, OUT_NAME, N_CHAMBER, AREA_M2,
    REJECT_WHY, CAP_WHY and the six band columns were all published and none of them was
    in it).  A dictionary that is silently incomplete is worse than a short one, because a
    reader takes its silence for "there is nothing else".  It now sweeps the actual
    published columns and lists what it cannot explain."""
    layers = EX.demo_layers()
    layers["subnetworks"] = layers["subnetworks"].assign(A_NEW_COL=1)
    doc = EX.field_dictionary_md(layers)
    assert "does NOT yet explain" in doc
    assert "A_NEW_COL" in doc, "a column nothing explains must be named, not omitted"


def test_a_missing_depth_is_not_coloured_as_the_shallowest_band():
    """REPORTED, NOT FIXED.  `_depth_index()` sends NaN to band 0, which on the magma ramp
    is the palest colour and reads as 'shallow, nothing to see'.  A chamber whose depth is
    unknown is not a shallow chamber.  Pinned so the behaviour is a decision rather than
    an accident."""
    idx = EX._depth_index(pd.Series([np.nan, 0.5, 11.0]))
    assert idx[0] == idx[1], "if this changes, the legend must gain an 'unknown' class"
