"""THE HIERARCHY, MEASURED PER SUB-NETWORK - not as a network average.

`_BRAIN/10_ASBUILT_CALIBRATION.md` sec 1 gives the gates, and rule T2 gives the reason they
are applied per sub-network rather than to the whole design:

    T2 - "One package is one connected component with exactly one outlet."

A package is what a sub-network is here, so the band measured BETWEEN NAMA's packages is the
band a sub-network is held to.  The file is explicit about why an average will not do:

    "Tier length shares ... PER SUBNETWORK: trunk 1.5-13.5 %, sub-main 10.9-17.2 %.
     A subnetwork with 0 % sub-main FAILS even if the average passes."

That last sentence is why the tier rule changed.  `tiers()` had always CLAIMED, in its own
docstring, that "every catchment gets one by construction, because the run at the outfall
always drains the whole catchment" - and the code tested `run_sub_km >= submain_km` and
nothing else, so a sub-network smaller than the threshold got no collector tier at all.  The
outfall rule multiplies the number of small sub-networks, which turns a rare case into the
common one.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import s3_hierarchy as H
from w12 import asbuilt as AB
from w12 import criteria as CR

C = CR.DEFAULT


@pytest.fixture(scope="session", autouse=True)
def _one_asbuilt():
    """Build the as-built measurement ONCE for the whole file.

    `subnet_calibration` constructs `AsBuilt()` and calls `targets()` each time it runs,
    which is right in a stage that runs once and wrong in a test file that exercises it
    eight times - it took 78 s before this fixture and 5 s after.  The object is read-only
    here, so sharing it changes nothing but the clock.
    """
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
# 1.  EVERY CALIBRATION NUMBER TRACES TO THE MEASUREMENT
# ==========================================================================================

def test_the_band_floor_is_the_one_the_band_was_measured_above():
    """Applying a band measured only over packages of 3 km and more to a 400 m sub-network
    would be comparing against evidence that never contained anything that small."""
    assert H.SUBNET_MIN_KM_FOR_BAND == AB.A_PKG_MIN_KM_GEOM


def test_the_trunk_sampling_step_is_a_resolution_not_a_design_value():
    """The Main Pipe is sampled to apportion its length by nearest join.  The step is the
    node-merge radius because that is the finest distance the published topology can tell
    apart; a finer step measures below the resolution of the thing being measured."""
    assert H.TRUNK_SAMPLE_M == C.MH_SNAP_M


def test_the_hierarchy_band_uses_the_corrected_figure_and_names_the_retracted_one():
    """`asbuilt.py` still returns 87.69 % for the lateral-into-lateral share.
    `10_ASBUILT_CALIBRATION.md` sec 4 retracts it by name - "wrong twice; use 73.2 % on 272
    exits, banded 60-78 %".  Quoting the live code's figure would re-publish a number this
    project has already withdrawn, so the band is typed against the _BRAIN file and BOTH
    numbers are published side by side."""
    assert H.CAL_HIER_PCT == (60.0, 78.0)
    assert H.CAL_HIER_MEASURED_PCT == 73.2
    assert H.CAL_HIER_RETRACTED_PCT == 87.69
    assert H.CAL_HIER_PCT[0] <= H.CAL_HIER_MEASURED_PCT <= H.CAL_HIER_PCT[1]
    # and the retracted figure is still what asbuilt returns, so the two really do disagree
    live = float(AB.AsBuilt().m_tiers()["lateral_zone_into_lateral_pct"])
    assert abs(live - H.CAL_HIER_RETRACTED_PCT) < 0.01, (
        "asbuilt no longer returns 87.69 - if it has been corrected, delete "
        "CAL_HIER_RETRACTED_PCT and read the band from asbuilt instead")


def test_the_chain_and_zone_gates_are_the_measured_ones():
    """Built: chain depth median 2, p90 3, max 5; lateral zones 4.27/km, excl. 5A-1."""
    assert (H.CAL_CHAIN_MED_MAX, H.CAL_CHAIN_P90_MAX, H.CAL_CHAIN_ABS_MAX) == (2, 4, 5)
    assert H.CAL_ZONE_PER_KM_MAX == 7.0


def test_the_tier_share_bands_are_read_from_the_measurement_not_typed():
    """A number typed into two files drifts.  These come from `asbuilt.targets()` at run
    time, and they are the 1.5-13.5 / 10.9-17.2 the calibration file quotes."""
    src = open(H.__file__, encoding="utf-8").read()
    assert 'tgt["tier_share_trunk_pct"].lo' in src
    assert 'tgt["tier_share_submain_pct"].lo' in src
    t = AB.AsBuilt().targets()
    assert 1.4 < t["tier_share_trunk_pct"].lo < 1.6
    assert 13.4 < t["tier_share_trunk_pct"].hi < 13.5
    assert 10.8 < t["tier_share_submain_pct"].lo < 10.9
    assert 17.1 < t["tier_share_submain_pct"].hi < 17.2


# ==========================================================================================
# 2.  THE OUTLET GOVERNS
# ==========================================================================================

def _tier_case(run_next, run_sub_km, run_depth, run_path_m,
               submain_km=2.0, budget_runs=3, budget_path_m=750.0):
    h = H.Hier.__new__(H.Hier)
    h.submain_km, h.budget_runs, h.budget_path_m = submain_km, budget_runs, budget_path_m
    h.n_runs = len(run_next)
    h.run_next = np.asarray(run_next, np.int64)
    h.run_sub_km = np.asarray(run_sub_km, float)
    h.run_depth = np.asarray(run_depth, float)
    h.run_path_m = np.asarray(run_path_m, float)
    return h


def test_a_sub_network_under_the_threshold_still_has_a_sub_main():
    """THE BUG.  120 m of network against a 2 km threshold: `run_sub_km >= sk` alone gives
    it no collector tier, and the calibration calls that a failure however good the
    network average looks."""
    h = _tier_case([1, -1], [0.05, 0.12], [1, 2], [0.0, 60.0])
    t = h.tiers()
    assert t[1] == "sub main"
    assert (t == "sub main").sum() == 1


def test_every_component_gets_exactly_one_sub_main_outlet():
    """Three separate components in one array - the shape the outfall rule produces."""
    #  0->1(out) | 2->3->4(out) | 5(out, on its own)
    h = _tier_case([1, -1, 3, 4, -1, -1],
                   [0.1, 0.2, 0.1, 0.2, 0.3, 0.02],
                   [1, 2, 1, 2, 3, 1],
                   [0.0, 50.0, 0.0, 50.0, 100.0, 0.0])
    t = h.tiers()
    outlets = np.flatnonzero(h.run_next == -1)
    assert all(t[o] == "sub main" for o in outlets)
    assert len(outlets) == 3


def test_the_outlet_clause_cannot_invert_the_tier():
    """The outlet run has the LARGEST accumulated length in its component, so naming it a
    sub main can never put a sub main upstream of a lateral."""
    rank = {"lateral": 0, "main": 1, "sub main": 2, "trunk main": 3}
    rng = np.random.default_rng(5)
    for _ in range(30):
        n = int(rng.integers(3, 10))
        nxt = [i + 1 for i in range(n - 1)] + [-1]
        sub = np.sort(rng.uniform(0.05, 6.0, n))          # non-decreasing downstream
        dep = np.arange(1, n + 1, dtype=float)
        pth = np.cumsum(rng.uniform(0.0, 300.0, n))
        t = _tier_case(nxt, sub, dep, pth).tiers()
        for i in range(n - 1):
            assert rank[t[nxt[i]]] >= rank[t[i]]


# ==========================================================================================
# 3.  THE PER-SUB-NETWORK MEASUREMENT
# ==========================================================================================

def _cal_case():
    """Two sub-networks whose every figure can be worked out by hand.

        S001   r0 -> r1 -> r2 -> r3(outlet)      1+1+1 km of lateral, 2 km of sub main
        S002   r4 -> r5(outlet)                  1 km of lateral, 2 km of sub main
        trunk  a 1,000 m line with a join at each end -> 500 m each, by nearest join
    """
    import geopandas as gpd
    from shapely.geometry import LineString

    h = H.Hier.__new__(H.Hier)
    h.verbose = False
    h.n_runs = 6
    h.run_next = np.array([1, 2, 3, -1, 5, -1], np.int64)
    h.run_tier = np.array(["lateral", "lateral", "lateral", "sub main",
                           "lateral", "sub main"], dtype=object)
    h.run_order = H.topo_order(h.run_next, np.arange(6, dtype=np.int64), 6)
    h.run_id = np.arange(6, dtype=np.int64)
    h.keep = np.ones(6, bool)
    h.len_out = np.array([1000.0, 1000.0, 1000.0, 2000.0, 1000.0, 2000.0])
    h.arc_tier = h.run_tier.copy()
    h.arc_subnet = np.array(["S001"] * 4 + ["S002"] * 2, dtype=object)
    h.root_kind = np.array(["main_pipe", "main_pipe"], dtype=object)
    h.NX_out = np.array([0.0, 1000.0])
    h.NY_out = np.array([0.0, 0.0])
    h.node_subnet = np.array(["S001", "S002"], dtype=object)
    h.main_pipe = gpd.GeoDataFrame(
        {"X": [1]}, geometry=[LineString([(0.0, 0.0), (1000.0, 0.0)])], crs="EPSG:32640")
    return h


def test_the_trunk_apportionment_sums_exactly_to_the_trunk():
    """It is a PROJECT APPORTIONMENT, not a measurement - the trunk is one client input
    serving every sub-network.  The one thing it must do is conserve length, or the trunk
    share is being computed against a denominator that is not the trunk."""
    h = _cal_case()
    got = h._apportion_trunk()
    assert abs(sum(got.values()) - 1.0) < 1e-6, "1,000 m of trunk"
    assert got["S001"] == pytest.approx(0.5, abs=1e-3)
    assert got["S002"] == pytest.approx(0.5, abs=1e-3)


def test_the_apportionment_needs_no_flow_direction_on_the_trunk():
    """Nearest-join, so reversing the trunk's drawing order cannot change the answer.  This
    stage does not know which way the Main Pipe runs and must not invent it."""
    import geopandas as gpd
    from shapely.geometry import LineString
    h = _cal_case()
    a = h._apportion_trunk()
    h.main_pipe = gpd.GeoDataFrame(
        {"X": [1]}, geometry=[LineString([(1000.0, 0.0), (0.0, 0.0)])], crs="EPSG:32640")
    b = h._apportion_trunk()
    assert a == pytest.approx(b)


def test_chain_depth_counts_hops_to_the_first_non_lateral():
    """The as-built figure is "chain depth, lateral -> main: median 2, p90 3, max 5"."""
    h = _cal_case()
    h.subnet_calibration()
    #   r2 discharges into a sub main            -> 1 hop
    #   r1 discharges into r2, a lateral         -> 2
    #   r0 discharges into r1                    -> 3
    assert list(h.run_hops[:4]) == [3, 2, 1, 0]
    s1 = h.subnet_cal.set_index("SUBNET").loc["S001"]
    assert s1.CHAIN_MED == pytest.approx(2.0)
    assert s1.CHAIN_MAX == 3
    assert s1.V_CHAIN == "pass"


def test_a_chain_deeper_than_the_absolute_maximum_fails():
    """Five is the built absolute.  Six laterals in a row is a design nobody can rod."""
    h = _cal_case()
    h.n_runs = 8
    h.run_next = np.array([1, 2, 3, 4, 5, 6, 7, -1], np.int64)
    h.run_tier = np.array(["lateral"] * 7 + ["sub main"], dtype=object)
    h.run_order = H.topo_order(h.run_next, np.arange(8, dtype=np.int64), 8)
    h.run_id = np.arange(8, dtype=np.int64)
    h.keep = np.ones(8, bool)
    h.len_out = np.full(8, 1000.0)
    h.arc_tier = h.run_tier.copy()
    h.arc_subnet = np.array(["S001"] * 8, dtype=object)
    h.node_subnet = np.array(["S001", "S001"], dtype=object)
    h.subnet_calibration()
    s1 = h.subnet_cal.set_index("SUBNET").loc["S001"]
    assert s1.CHAIN_MAX == 7
    assert s1.V_CHAIN == "FAIL"


def test_the_tier_shares_are_measured_against_the_bands_not_just_reported():
    """S001: 3 km lateral + 2 km sub main + 0.5 km of apportioned trunk = 5.5 km."""
    h = _cal_case()
    h.subnet_calibration()
    s1 = h.subnet_cal.set_index("SUBNET").loc["S001"]
    assert s1.KM == pytest.approx(5.0)
    assert s1.TRUNK_KM == pytest.approx(0.5, abs=1e-3)
    assert s1.TRUNK_PCT == pytest.approx(100.0 * 0.5 / 5.5, abs=0.05)
    assert s1.SM_PCT == pytest.approx(100.0 * 2.0 / 5.5, abs=0.05)
    assert s1.LAT_PCT == pytest.approx(100.0 * 3.0 / 5.5, abs=0.05)
    assert abs(s1.TRUNK_PCT + s1.SM_PCT + s1.LAT_PCT - 100.0) < 0.1
    # 9.1 % of trunk is inside the built band; 36.4 % of sub main is well above it
    assert s1.V_TRUNK == "in band"
    assert s1.V_SM == "above"


def test_a_sub_network_below_the_band_floor_is_not_graded_against_it():
    """Saying "out of band" about a 400 m sub-network, when the band was measured only over
    packages of 3 km and more, is a verdict the evidence does not support."""
    h = _cal_case()
    h.len_out = np.array([100.0, 100.0, 100.0, 100.0, 1000.0, 2000.0])
    h.subnet_calibration()
    c = h.subnet_cal.set_index("SUBNET")
    assert c.loc["S001"].BANDED == 0
    assert c.loc["S001"].V_TRUNK == "too small to band"
    assert c.loc["S002"].BANDED == 1


def test_a_sub_network_with_no_sub_main_is_counted_not_averaged_away():
    """The gate that a network average hides, and the reason `tiers()` changed."""
    h = _cal_case()
    h.run_tier = np.array(["lateral"] * 6, dtype=object)
    h.arc_tier = h.run_tier.copy()
    h.subnet_calibration()
    assert int(h.subnet_cal.SM_ZERO.sum()) == 2
    row = h.cal_summary.set_index("GATE").loc["sub-networks with NO sub main at all"]
    assert row.N_OUT == 2
    assert row.KM_OUT == pytest.approx(8.0)


def test_zone_density_and_the_hierarchy_ratio_are_complements():
    """A lateral run either discharges into another lateral or it is a zone exit.  Stating
    that here means the two published numbers cannot silently disagree."""
    h = _cal_case()
    h.subnet_calibration()
    for r in h.subnet_cal.itertuples():
        if r.N_LAT_RUNS:
            assert r.ZONES + round(r.HIER_PCT * r.N_LAT_RUNS / 100.0) == r.N_LAT_RUNS
    s1 = h.subnet_cal.set_index("SUBNET").loc["S001"]
    assert s1.ZONES == 1                      # r0,r1,r2 are one cluster with one exit
    assert s1.HIER_PCT == pytest.approx(200.0 / 3.0, abs=0.01)
    assert s1.ZONE_PER_KM == pytest.approx(1.0 / 5.0, abs=1e-6)
    assert s1.V_ZONE == "pass"


def test_a_missing_main_tier_shows_up_as_zone_density():
    """"> 7/km means the main tier is missing - the single best structural symptom.\""""
    h = _cal_case()
    #   every lateral run is its own zone, on 100 m each: 3 zones in 0.5 km = 6/km, and
    #   with the two collectors also laterals it goes past the gate
    h.run_next = np.array([-1, -1, -1, -1, 5, -1], np.int64)
    h.run_order = H.topo_order(h.run_next, np.arange(6, dtype=np.int64), 6)
    h.len_out = np.array([100.0, 100.0, 100.0, 100.0, 1000.0, 2000.0])
    h.subnet_calibration()
    s1 = h.subnet_cal.set_index("SUBNET").loc["S001"]
    assert s1.ZONES == 3
    assert s1.ZONE_PER_KM > H.CAL_ZONE_PER_KM_MAX
    assert s1.V_ZONE.startswith("FAIL")


# ==========================================================================================
# 4.  NO REACH WITHOUT A SUB-NETWORK, AND NO CHECK THAT SILENTLY CANNOT RUN
# ==========================================================================================

def test_every_kept_reach_must_carry_a_sub_network_label():
    """s2 leaves SUBNET blank on every head, island and unused corridor - about a fifth of
    the published length.  A reach nobody can attribute cannot be calibrated, and the whole
    point of the outfall rule is that a sub-network is a catchment with ONE outlet."""
    src = open(H.__file__, encoding="utf-8").read()
    assert "def label_subnets" in src
    assert '"SUBNET": self.arc_subnet[idx]' in src, \
        "publish must use this stage's own labels, not s2's arc column"
    assert "ORPH-" in src, "a component draining nowhere is NAMED, not blanked"


def test_label_subnets_refuses_to_publish_a_blank_label():
    """It raises rather than shipping a blank, because a blank is indistinguishable from a
    reach that genuinely belongs to nothing - and no reach does."""
    h = H.Hier.__new__(H.Hier)
    h.verbose = False
    h.n_nodes = 3
    h.used = np.array([True, True, False])
    h.rootof = np.array([0, 0, 0], np.int64)
    h.nid_out = ["A", "B", "C"]
    h.keep = np.array([True])
    h.Uo = np.array([0], np.int64)
    h.arcs = pd.DataFrame({"SUBNET": [""]})
    h.onodes = pd.DataFrame({"NODE_ID": ["A"], "SUBNET": ["S001"]})
    h.island_report = pd.DataFrame()
    h.label_subnets()
    assert list(h.arc_subnet) == ["S001"]

    # now break it: the root is not in `used`, so `lab` stays blank on it
    h2 = H.Hier.__new__(H.Hier)
    h2.verbose = False
    h2.n_nodes = 2
    h2.used = np.array([False, False])
    h2.rootof = np.array([0, 0], np.int64)
    h2.nid_out = ["A", "B"]
    h2.keep = np.array([True])
    h2.Uo = np.array([0], np.int64)
    h2.arcs = pd.DataFrame({"SUBNET": [""]})
    h2.onodes = pd.DataFrame({"NODE_ID": ["A"], "SUBNET": ["S001"]})
    h2.island_report = pd.DataFrame()
    with pytest.raises(AssertionError, match="no sub-network label"):
        h2.label_subnets()


def test_an_island_keeps_its_island_identity():
    """"Drains to a local low point with no path to the trunk" is a different fact from
    "drains to the trunk at S042" and must not be dressed up as one."""
    h = H.Hier.__new__(H.Hier)
    h.verbose = False
    h.n_nodes = 2
    h.used = np.array([True, True])
    h.rootof = np.array([0, 0], np.int64)
    h.nid_out = ["A", "B"]
    h.keep = np.array([True])
    h.Uo = np.array([1], np.int64)
    h.arcs = pd.DataFrame({"SUBNET": [""]})
    h.onodes = pd.DataFrame({"NODE_ID": ["A"], "SUBNET": [""]})
    h.island_report = pd.DataFrame({"ROOT": ["A"], "COMP": ["ISL003"]})
    h.label_subnets()
    assert list(h.arc_subnet) == ["ISL003"]


def test_verify_reports_a_check_it_cannot_run_rather_than_skipping_it():
    """Inheritance row 2: a check that cannot run is a FAILURE, not a blank.  W10's audit
    had no such state, so absent chambers read as compliance."""
    src = open(H.__file__, encoding="utf-8").read()
    v = src[src.index("def verify()"):]
    assert "CANNOT RUN - the reaches layer has no SUBNET column" in v
    assert "CANNOT RUN - the reaches layer has no CHAIN column" in v
    assert "subnets_with_no_submain" in v


def test_every_calibration_number_has_a_manifest_row():
    """A number that lives only in a console log is a number nobody can check next month."""
    src = open(H.__file__, encoding="utf-8").read()
    for item in ("CAL_CHAIN_MED_MAX", "CAL_CHAIN_P90_MAX", "CAL_CHAIN_ABS_MAX",
                 "CAL_ZONE_PER_KM_MAX", "CAL_HIER_PCT_LO", "CAL_HIER_PCT_HI",
                 "CAL_HIER_MEASURED_PCT", "CAL_TRUNK_BAND_LO", "CAL_SUBMAIN_BAND_LO",
                 "SUBNET_MIN_KM_FOR_BAND", "TRUNK_SAMPLE_M", "subnets_n",
                 "subnets_no_submain", "subnets_chain_fail", "km_chain_fail",
                 "subnets_zone_density_fail", "subnets_hier_out_of_band",
                 "chain_max_all", "zone_per_km_all"):
        assert f'("{item}"' in src, f"{item} is not a manifest row"
