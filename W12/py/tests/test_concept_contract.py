"""The concept-stage contract - the fields and constants added on 2026-09-06.

WHAT THIS FILE IS FOR. `w12/contract.py` and `w12/criteria.py` grew seven groups of fields
and one switch so that the engineer's concept-stage rules could be CHECKED rather than
described. A rule with no check is decoration, and this project has lost the same finding
twice for exactly that reason (`_BRAIN/09_INHERITANCE.md`, five rows with no enforcement).

Every test below is written against a failure that has already happened here:

    naming          a published column that is constant where it should vary - ANGLE_DEG = 90
                    on all 3,290 crossings, called a declaration, measured minimum 0.00 deg
    drops           41 vortex shafts against the built network's 37 is the diagnostic for a
                    tree following the ground; a drop with no reason cannot be audited
    outfalls        42 components discharging with more than half their catchment BELOW the
                    outlet, 389.5 km, and nothing on the layer said so
    connections     CAN_DRAIN recorded as "cannot run" - and a check that cannot run is a
                    FAILURE, not a blank
    stations        15 of 47 with nothing draining into them; two station counts in
                    circulation (14 demanded, 47 designed)
    velocities      the 2.5 / 3.0 m/s conflation, made twice on this project
    infiltration    two allowances in G201-p72 and only one of them applies to a NEW network

NO TEST HERE INVENTS A DESIGN NUMBER. Thresholds come from `w12.criteria` (page-cited) or
from `w12.contract` (structural, and it says so).
"""
from __future__ import annotations

import re
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import LineString, Point

from w12 import contract as CT
from w12.contract import ContractError
from w12.criteria import DEFAULT as C, Criteria, CriteriaError, replace

W12_PY = Path(__file__).resolve().parent.parent


# ======================================================================================
# 1. The two velocity caps. Different pipes, different numbers, and they stay that way.
# ======================================================================================

def test_gravity_and_rising_main_velocity_caps_are_different_numbers():
    """G203-p27 sec 4.2.2.2 caps a GRAVITY sewer at 3.0 m/s; G203-p50 sec 8.1 caps a RISING
    MAIN at 2.5 m/s. Inheritance row 9 records that the two were conflated - rising mains
    capped at 3.0 - and it has been made twice on this project."""
    assert C.V_MAX == 3.0
    assert C.FM_V_MAX == 2.5
    assert C.FM_V_MAX < C.V_MAX, ("the rising-main cap is the LOWER of the two. Equal values "
                                  "mean one was copied from the other.")
    assert C.PS_PIPEWORK_V_MAX == 2.5          # G203-p41 Table 17, station pipework
    assert C.FM_V_MIN == 0.75                  # G203-p50, at the DESIGN MINIMUM flow


def test_the_rising_main_layer_is_checked_at_2_5_not_3_0():
    """The constant being right is not enough - the CHECK has to use it. A rising main at
    2.9 m/s is legal for a gravity sewer and illegal for itself."""
    rm = CT._demo_rising_mains()
    CT.validate(rm, "rising_mains")            # 1.59 m/s at duty - fine
    rm.loc[rm.index[0], "V_DUTY_MS"] = 2.9
    with pytest.raises(ContractError, match="G203-p50"):
        CT.validate(rm, "rising_mains")


# ======================================================================================
# 2. Infiltration. G201-p72 gives TWO allowances; W12 is a NEW network.
# ======================================================================================

def test_infiltration_uses_the_new_network_allowance():
    """G201-p72 sec 7.4.3: 720 L/d/km of sewer "for newly designed networks"; 10 % of
    wastewater flow (40 % in groundwater) for an EXISTING one. W12 designs a new network."""
    assert C.INFILT_L_D_KM == 720.0
    assert C.infiltration_ls(1000.0) == pytest.approx(720.0 / 86400.0, rel=0, abs=1e-15)
    # a per-LENGTH rule scales exactly with length. A percentage-of-flow rule could not.
    assert C.infiltration_ls(2500.0) == pytest.approx(2.5 * C.infiltration_ls(1000.0))
    assert C.infiltration_ls(0.0) == 0.0
    # the existing-network figures are STORED - a hydraulic assessment of NAMA's built
    # 95.45 km needs them - but they must not be reachable from the design path
    assert C.INFILT_EXISTING_INLAND == 0.10 and C.INFILT_EXISTING_GW == 0.40


def test_the_existing_network_percentages_are_not_wired_into_any_stage():
    """Declared is not the same as used. This reads the SOURCE of the whole package, because
    the failure being prevented - a design silently taking the existing-network allowance -
    would leave every other test passing."""
    hits = []
    for path in sorted(W12_PY.rglob("*.py")):
        rel = path.relative_to(W12_PY).as_posix()
        if rel.startswith("tests/") or rel.endswith("w12/criteria.py"):
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "INFILT_EXISTING" in line and not line.lstrip().startswith("#"):
                hits.append(f"{rel}:{i}: {line.strip()}")
    assert not hits, ("the EXISTING-network infiltration allowance is referenced outside "
                      "criteria.py:\n  " + "\n  ".join(hits) + "\nG201-p72 gives 720 L/d/km "
                      "for a NEW network and W12 designs one.")


# ======================================================================================
# 3. The concept-stage switch and its register (inheritance row 13)
# ======================================================================================

def test_concept_stage_is_on_and_the_register_is_complete():
    assert C.CONCEPT_STAGE is True
    off = C.CONCEPT_OFF
    # the seven the engineer named on 2026-09-05/06
    assert set(off) == {"house_connections", "motor_selection", "life_cycle_cost",
                        "excavation_vs_pumping", "phasing_packaging", "sewergems_export",
                        "swept_channel_detail"}
    for cap, pair in off.items():
        what, back = pair
        assert what.strip() and back.strip(), cap    # what it is, and what brings it back


def test_a_switched_off_capability_stops_a_stage_by_name():
    """Inheritance row 13: a stage may not silently no-op. W10's road treatment ran with
    three of nine steps doing nothing and 34 collapsed rings contained a registered plot."""
    for cap in C.CONCEPT_OFF:
        with pytest.raises(CriteriaError, match="SWITCHED OFF"):
            C.assert_enabled(cap)


def test_a_misspelled_capability_raises_rather_than_passing():
    """A guard that never fires still reads as a guard, which is worse than no guard."""
    with pytest.raises(CriteriaError, match="unknown capability"):
        C.assert_enabled("motor_seleciton")


def test_turning_the_concept_switch_off_re_enables_everything():
    """Nothing is deleted, so nothing has to be rebuilt when the concept is approved."""
    built = replace(C, CONCEPT_STAGE=False)
    for cap in C.CONCEPT_OFF:
        built.assert_enabled(cap)                    # must not raise
    assert isinstance(built, Criteria) and C.CONCEPT_STAGE is True   # DEFAULT untouched


def test_the_switched_off_capabilities_reach_the_deliverable_banner():
    """A reader who does not know what was switched off cannot tell a design decision from
    an omission."""
    txt = C.concept_banner()
    for cap in C.CONCEPT_OFF:
        assert cap in txt
    assert C.concept_banner() in CT.run_banner()


# ======================================================================================
# 4. Naming (concept rule 8)
# ======================================================================================

@pytest.mark.parametrize("kw,want", [
    (dict(town="I", kind="subnet", subnet="S03"), "I-S03"),
    (dict(town="I", kind="manhole", subnet="S03", tier="sub main", seq=12), "I-S03-SM-M012"),
    (dict(town="I", kind="manhole", subnet="S03", tier="trunk main", seq=7), "I-S03-TM-M007"),
    (dict(town="I", kind="manhole", subnet="S03", tier="lateral", seq=7), "I-S03-L-M007"),
    (dict(town="I", kind="conduit", subnet="S03", seq=12), "I-S03-C012"),
    (dict(town="I", kind="pump", seq=2), "I-PMP02"),
    (dict(town="I", kind="main", seq=2), "I-P02"),
])
def test_the_naming_grammar(kw, want):
    assert CT.concept_name(**kw) == want
    assert CT.parse_name(want) is not None, want


def test_a_pump_is_never_parsed_as_a_force_main():
    """PMP must be matched before P, or I-PMP02 reads as force main 'MP02'."""
    assert CT.parse_name("I-PMP02")["kind"] == "pump"
    assert CT.parse_name("I-P02")["kind"] == "main"


def test_zero_padding_is_a_minimum_width_not_a_fixed_one():
    """A network that outgrows its padding must not be renamed into an unparseable state."""
    assert CT.parse_name("I-S147-SM-M1234") is not None
    assert CT.concept_name("I", "manhole", subnet="S147", tier="sub main", seq=1234) == \
        "I-S147-SM-M1234"


@pytest.mark.parametrize("bad", ["MH-1", "I-S3-SM-M012", "S03-M012", "i-s03-sm-m012",
                                 "I-S03-XX-M012", "I-S03-M012", ""])
def test_names_outside_the_grammar_are_rejected(bad):
    assert CT.parse_name(bad) is None


def test_an_unknown_tier_cannot_be_defaulted_into_a_name():
    """The tier token is IN the name, so a silent default would put a lateral's label on a
    trunk chamber - and `criteria.materials_allowed()` raises on an unknown tier for the same
    reason."""
    with pytest.raises(ContractError, match="not one of"):
        CT.concept_name("I", "manhole", subnet="S03", tier="street", seq=1)


def test_a_gravity_element_always_carries_a_subnetwork_and_a_pump_never_does():
    """A station is a SEAM between subnetworks, not a member of one (concept rule 8)."""
    with pytest.raises(ContractError, match="not S##"):
        CT.concept_name("I", "conduit", seq=1)
    assert CT.parse_name(CT.concept_name("I", "pump", seq=1))["sub"] == ""


def test_the_town_letter_drops_the_article():
    """A PROJECT DECISION, not a guideline: 'Al Aqar' and 'Ad Dariz' would otherwise both be
    'A' and every town in the wilayat would collide on one letter."""
    assert CT.town_letter("Al Aqar") == "A"
    assert CT.town_letter("Ad Dariz") == "D"
    assert CT.town_letter("Ash Sharaijah") == "S"
    assert CT.town_letter("Ibri") == "I"
    assert CT.town_letter("Al Aqar", 2) == "AQ"          # letters only, never a space


def test_on_a_clash_both_towns_extend_and_neither_is_favoured():
    """The engineer's rule, and it is deliberately symmetric: 'the town with more served
    plots is not favoured - both extend'. Favouring the larger town would make the small
    town's code depend on a LOAD, so a plot count moving would rename half a network."""
    codes = CT.town_letters(["Al Aqar", "Al Ayn", "Ibri"])
    assert codes["Ibri"] == "I"
    assert codes["Al Aqar"] != codes["Al Ayn"]
    assert len(codes["Al Aqar"]) == len(codes["Al Ayn"]) == 2, codes
    # and the result does not depend on the order the towns arrive in
    assert CT.town_letters(["Ibri", "Al Ayn", "Al Aqar"]) == codes


def test_town_codes_are_unique_and_terminate_on_identical_names():
    """Two settlements whose de-articled names are identical cannot be separated by letters.
    The resolver must not loop, and must not silently merge them into one town."""
    codes = CT.town_letters(["Al Aqar", "Aqar", "Ibri"])
    assert len(set(codes.values())) == 3, codes
    dupes = CT.town_letters(["Al Hayl", "Ad Hayl"])
    assert len(set(dupes.values())) == 2, dupes


def test_every_naming_field_name_survives_a_shapefile():
    """The 10-character limit is on the FIELD NAME, not the value. NAME is 4 characters and
    the value 'I-S03-SM-M012' is a DBF string field with room to spare."""
    for layer in ("nodes", "reaches", "stations", "rising_mains", "connections"):
        spec = CT.LAYERS[layer]
        for f in ("NAME", "TOWN", "SUBNET"):
            assert spec.field(f) is not None, f"{layer} has no {f}"
            assert len(f) <= CT.SHP_FIELD_MAXLEN


def test_a_name_that_contradicts_its_own_columns_is_rejected():
    net = CT._demo_network()
    nodes = CT._demo_nodes(net)
    CT.validate(nodes, "nodes")

    bad = nodes.copy()
    bad.loc[bad.index[0], "NAME"] = "I-S01-TM-M001"       # TIER on the row says lateral
    with pytest.raises(ContractError, match="NAME and TIER disagree"):
        CT.validate(bad, "nodes")

    bad = nodes.copy()
    bad.loc[bad.index[0], "TOWN"] = "Q"
    with pytest.raises(ContractError, match="NAME and TOWN disagree"):
        CT.validate(bad, "nodes")

    bad = nodes.copy()
    bad["NAME"] = "I-S01-L-M001"                          # one name on every chamber
    with pytest.raises(ContractError, match="DUPLICATE NAME"):
        CT.validate(bad, "nodes")


def test_naming_may_be_blank_mid_pipeline_and_never_at_publication():
    """Two mechanisms, because they answer two different questions: 'can this be checked?'
    (the column must exist) and 'was it actually done?' (assert_named)."""
    net = CT._demo_network()
    nodes = CT._demo_nodes(net)
    blank = nodes.copy()
    blank["NAME"] = ""
    blank["TOWN"] = ""
    CT.validate(blank, "nodes")                            # legal before naming has run
    with pytest.raises(ContractError, match="NOT FULLY NAMED"):
        CT.assert_named(blank, "nodes")
    CT.assert_named(nodes, "nodes")
    # a station's blank SUBNET is the rule, not a gap - its name carries no S-token
    CT.assert_named(CT._demo_stations(), "stations")


# ======================================================================================
# 5. Drops carry their reason (concept rule 1)
# ======================================================================================

def _dropping_nodes():
    net = CT._demo_network()
    n = CT._demo_nodes(net)
    n["DROP_M"] = 1.20
    n["DROP_TYPE"] = "backdrop"
    n["MH_DIA"] = C.MH_DIA_INTERNAL_BACKDROP               # G203-p30, so only DROP_WHY is at issue
    return n


def test_a_drop_with_no_reason_is_refused():
    n = _dropping_nodes()
    with pytest.raises(ContractError, match="no DROP_WHY"):
        CT.validate(n, "nodes")
    n["DROP_WHY"] = "velocity_cap"
    CT.validate(n, "nodes")


def test_a_reason_for_a_drop_that_is_not_there_is_refused():
    net = CT._demo_network()
    n = CT._demo_nodes(net)                                 # DROP_M = 0 everywhere
    n["DROP_WHY"] = "cover_recovery"
    with pytest.raises(ContractError, match="DROP_M = 0"):
        CT.validate(n, "nodes")


def test_the_drop_vocabulary_is_closed():
    """Four causes, and they are the four the engineer named. Free text here would make the
    drop count unreadable exactly where it is the diagnostic."""
    assert set(CT.DROP_WHY) == {"", "velocity_cap", "tier_step", "cover_recovery",
                                "obstruction"}
    n = _dropping_nodes()
    n["DROP_WHY"] = "steep"
    with pytest.raises(ContractError, match="ILLEGAL VALUE in DROP_WHY"):
        CT.validate(n, "nodes")


def test_one_reason_for_every_drop_on_a_large_network_is_a_fabrication():
    """Inheritance row 22. Below VARY_MIN_ROWS it is a small sample; at or above it, a single
    repeated value is the ANGLE_DEG = 90 defect."""
    import pandas as pd
    small = _dropping_nodes()
    small["DROP_WHY"] = "velocity_cap"
    assert CT.constant_column_problem(small, "DROP_WHY", small.DROP_M > 0) is None

    big = pd.concat([small] * CT.VARY_MIN_ROWS, ignore_index=True)
    prob = CT.constant_column_problem(big, "DROP_WHY", big.DROP_M > 0)
    assert prob and "FABRICATION" in prob

    big.loc[big.index[0], "DROP_WHY"] = "tier_step"
    assert CT.constant_column_problem(big, "DROP_WHY", big.DROP_M > 0) is None


# ======================================================================================
# 6. The outfall joins at the low point, or says how far off it is (concept rule 2)
# ======================================================================================

def test_an_outfall_moved_off_the_low_point_must_say_why():
    net = CT._demo_network()
    n = CT._demo_nodes(net)
    assert (n.JOIN_MAIN == 1).sum() == 1, "the demo network meets the main pipe once"
    n.loc[n.IS_OUTFALL == 1, "JOIN_OFF_M"] = 210.0
    with pytest.raises(ContractError, match="no JOIN_WHY"):
        CT.validate(n, "nodes")
    n.loc[n.IS_OUTFALL == 1, "JOIN_WHY"] = "no street at the low point"
    CT.validate(n, "nodes")


def test_zero_offset_is_the_normal_answer_and_needs_no_explanation():
    """Concept rule 2 says 0.0 when it connects AT the low point - so an explanation there is
    an explanation of nothing, and a column of them would hide the real ones."""
    net = CT._demo_network()
    n = CT._demo_nodes(net)
    CT.validate(n, "nodes")                                 # offsets are 0.0, reasons blank
    n.loc[n.IS_OUTFALL == 1, "JOIN_WHY"] = "no street at the low point"
    with pytest.raises(ContractError, match="explain an offset of zero"):
        CT.validate(n, "nodes")


def test_an_offset_from_a_join_that_does_not_exist_is_refused():
    net = CT._demo_network()
    n = CT._demo_nodes(net)
    n.loc[n.index[0], "JOIN_OFF_M"] = 5.0                   # JOIN_MAIN is 0 on this row
    n.loc[n.index[0], "JOIN_WHY"] = "somewhere"
    with pytest.raises(ContractError, match="without JOIN_MAIN"):
        CT.validate(n, "nodes")


# ======================================================================================
# 7. Plot connectability (concept rules 5 and 7)
# ======================================================================================

def test_a_plot_that_cannot_connect_is_named_with_its_size():
    conns = CT._demo_connections(CT._demo_network())
    CT.validate(conns, "connections")
    assert (conns.CAN_CONN == 0).any() and (conns.CONN_NEED > 0).any()

    bad = conns.copy()
    bad["CONN_WHY"] = ""
    with pytest.raises(ContractError, match="no CONN_WHY"):
        CT.validate(bad, "connections")


def test_a_connectable_plot_carries_no_reason_and_needs_no_depth():
    conns = CT._demo_connections(CT._demo_network())
    bad = conns.copy()
    bad["CAN_CONN"] = 1
    with pytest.raises(ContractError, match="carry a reason why they cannot"):
        CT.validate(bad, "connections")

    bad = conns.copy()
    bad["CAN_CONN"] = 1
    bad["CONN_WHY"] = ""
    with pytest.raises(ContractError, match="still ask for"):
        CT.validate(bad, "connections")


def test_can_conn_and_can_drain_may_not_give_two_answers():
    """CAN_DRAIN is kept because s8 writes it; it asks the same question CAN_CONN asks, and
    two answers to one question is the defect that has cost this project most."""
    conns = CT._demo_connections(CT._demo_network())
    bad = conns.copy()
    bad["CAN_DRAIN"] = 1 - bad.CAN_CONN
    with pytest.raises(ContractError, match="CAN_CONN and CAN_DRAIN disagree"):
        CT.validate(bad, "connections")
    ok = conns.copy()
    ok["CAN_DRAIN"] = ok.CAN_CONN
    CT.validate(ok, "connections")


def test_the_connectability_check_can_actually_run():
    """The gap being closed: W11b published DRAIN_SHALLOW - a bound at minimum cover - and
    recorded CAN_DRAIN as 'cannot run'. Philosophy sec 8: a check that cannot run is a
    FAILURE, not a blank."""
    conns = CT._demo_connections(CT._demo_network())
    need = CT.AUDIT_NEEDS["C3"]["connections"]
    assert set(need) <= set(conns.columns)
    rd = CT.audit_readiness(connections=conns)
    assert bool(rd.set_index("check").loc["C3", "can_run"])


# ======================================================================================
# 8. A station's position is chosen, not triggered (concept rule 6)
# ======================================================================================

def test_a_station_with_nothing_draining_into_it_is_refused():
    """15 of W11b's 47 had nothing upstream. They were leftovers from a pass that could only
    ever ADD - inheritance row 4."""
    st = CT._demo_stations()
    CT.validate(st, "stations")
    st.loc[st.index[0], "N_SUBNET"] = 0
    with pytest.raises(ContractError, match="NOTHING DRAINS INTO THEM"):
        CT.validate(st, "stations")


def test_a_station_must_say_what_it_captures():
    """Station cost correlates 0.99 with power and 0.72 with head, and 86 % of life-cycle
    cost is manning - so 'how much does this one capture' is the question that decides
    whether it should exist. Neither number alone shows it."""
    st = CT._demo_stations()
    st.loc[st.index[0], "CATCH_KM"] = 0.0
    with pytest.raises(ContractError, match="captures no kilometres"):
        CT.validate(st, "stations")


def test_a_rising_main_declares_where_gravity_resumes():
    """Concept rule 6: a rising main lifts to the NEAREST point where gravity resumes, not
    to the works. The share ending at 'stp' is the number that says whether it was obeyed."""
    assert set(CT.DS_TYPE) == {"manhole", "stp"}
    rm = CT._demo_rising_mains()
    assert rm.DS_TYPE.iloc[0] == "manhole"
    rm.loc[rm.index[0], "DS_TYPE"] = "works"
    with pytest.raises(ContractError, match="ILLEGAL VALUE in DS_TYPE"):
        CT.validate(rm, "rising_mains")


def test_no_motor_size_or_life_cycle_cost_reaches_the_station_layer():
    """Both are SWITCHED OFF at concept. The field names are banned so the column cannot
    appear quietly as an undeclared extra - validate() allows extra columns by default."""
    assert CT.LAYERS["stations"].field("MOTOR_KW") is None
    st = CT._demo_stations()
    st["MOTOR_KW"] = 15.0
    with pytest.raises(ContractError, match="SWITCHED OFF"):
        CT.validate(st, "stations")


# ======================================================================================
# 9. The refused synonyms. One quantity, one name.
# ======================================================================================

@pytest.mark.parametrize("col,points_at", [
    ("HEAD_M", "LIFT_M"),
    ("Q_LS", "Q_DUTY_LS"),
    ("STOR_M3", "WELL_M3"),
    ("DIA_MM", "DN"),
    ("V_MS", "V_DUTY_MS"),
    ("US_PUMP", "US_NODE"),
    ("JOIN_OFFS_M", "JOIN_OFF_M"),
])
def test_a_synonym_is_refused_and_names_the_field_to_use_instead(col, points_at):
    """Six field names were proposed for the concept-stage pump schema on 2026-09-06 and all
    six were second names for quantities the contract already carried. An error that does not
    say what to use instead just gets worked around."""
    assert col in CT.BANNED_FIELDS
    assert points_at in CT.BANNED_FIELDS[col]
    st = CT._demo_stations()
    st[col] = 1.0
    with pytest.raises(ContractError, match=re.escape(points_at)):
        CT.validate(st, "stations")


def test_the_refusals_are_on_the_record_with_what_would_admit_them():
    """EXCLUDED is the register against schema regrowth: without it nobody remembers whether
    a field was refused or simply never proposed."""
    names = " ".join(e.name for e in CT.EXCLUDED)
    assert "HEAD_M" in names and "motor size" in names
    for e in CT.EXCLUDED:
        assert e.why_refused.strip() and e.would_admit.strip()


# ======================================================================================
# 10. Every concept rule has a check, and every check can run
# ======================================================================================

def test_every_concept_rule_has_a_declared_check():
    """Philosophy sec 8: one check per rule, 'generated from the tables above so a rule
    cannot exist without its check'."""
    for cid in ("C1", "C2", "C3", "C4", "C5"):
        assert cid in CT.AUDIT_NEEDS, cid
        assert CT.AUDIT_NEEDS[cid], cid


def test_a_missing_layer_makes_its_check_unrunnable_rather_than_passing():
    """A check that cannot run is a FAILURE, not a blank (inheritance row 2). W10's audit had
    no 'cannot run' state, so absent chambers read as compliance."""
    net = CT._demo_network()
    reaches, nodes = CT._demo_reaches(net), CT._demo_nodes(net)
    ext = ("roads", "hazard", "crossings", "existing", "manifest")

    partial = CT.audit_readiness(reaches, nodes, external=ext)
    assert set(partial[~partial.can_run].check) == {"C3", "C5"}

    full = CT.audit_readiness(reaches, nodes, external=ext,
                              connections=CT._demo_connections(net),
                              stations=CT._demo_stations(),
                              rising_mains=CT._demo_rising_mains())
    assert full.can_run.all(), full[~full.can_run].to_dict("records")


def test_the_concept_fields_reach_the_client_facing_schedules():
    """A flag that lives only in a GeoPackage column is a flag nobody outside this pipeline
    will ever see - and 'flag, do not solve' is only worth anything if the flag is read."""
    net = CT._demo_network()
    ch = CT.schedule_frame(CT._demo_nodes(net), "chambers")
    cn = CT.schedule_frame(CT._demo_connections(net), "connections")
    st = CT.schedule_frame(CT._demo_stations(), "stations")
    rm = CT.schedule_frame(CT._demo_rising_mains(), "rising_mains")
    assert {"Drop reason", "Joins main pipe", "Offset from low point (m)",
            "Offset reason"} <= set(ch.columns)
    assert {"Can connect", "If not, why",
            "Extra sewer depth needed (m)"} <= set(cn.columns)
    assert {"Subnetworks served", "Network captured (km)"} <= set(st.columns)
    assert "Discharges into" in rm.columns


def test_the_new_layers_round_trip_through_a_shapefile():
    """FIX 4's claim, applied to the fields added today: no name over 10 characters, so the
    DBF mirror and the GeoPackage carry ONE schema and a check can be pointed at either."""
    import tempfile
    net = CT._demo_network()
    frames = {"connections": CT._demo_connections(net),
              "stations": CT._demo_stations(),
              "rising_mains": CT._demo_rising_mains()}
    with tempfile.TemporaryDirectory() as tmp:
        for name, gdf in frames.items():
            CT.publish(gdf, name, tmp, stage="test")
            gp = gpd.read_file(CT.gpkg_path(tmp), layer=name)
            sh = gpd.read_file(f"{tmp}/shp/W12_{name}.shp")
            lost = set(gp.columns) - set(sh.columns)
            assert not lost, f"{name} lost {sorted(lost)} in the DBF"
            CT.validate(gp, name, stage="roundtrip")
            CT.validate(sh, name, stage="roundtrip-shp")


def test_the_module_self_tests_still_pass():
    """Both files prove their own claims rather than asserting them, and the suite is the
    thing that notices when they stop."""
    from w12 import criteria as CR
    CR._self_test(verbose=False)
    CT._self_test(verbose=False)
