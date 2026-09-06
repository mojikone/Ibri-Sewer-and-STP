"""THE THREE CONTRACT DEFECTS OF 2026-09-06, each written against what actually happened.

A. THE WET-WELL EQUATION WAS FED THE WRONG Q. `contract.validate()` put `Q_DUTY_LS` - the
   STATION duty, every duty pump together - into G203-p48 sec 7.8's `V = 0.25 Q T`, where
   the clause says "Q = single pump capacity in m3/sec" under a preamble scoping it to "a
   single constant-speed pump". On a Type 2 that demands a wet well twice the size the
   clause asks for and on a Type 3 three times (G203-p40 Table 17: 1 / 2 / 3 duty pumps).
   Reported by s7_pumps, which could not fix it - it does not own contract.py - and
   verified against the PDF before the change.

   MEASURED ON THE 43 PUBLISHED STATIONS: the design was already right, because
   `pumping.wet_well()` takes `q_single_pump_ls`. NO STATION CHANGED SIZE. What changed is
   that the check stopped failing the two Type 2 stations - it had demanded 11.58 m3 where
   5.79 was published and 13.65 where 6.83 was, both exactly 2.00x.

B. A FABRICATED COLUMN, AND THREE THAT ARE CONSTANT FOR A REAL REASON. Five columns tripped
   the constancy check. Three are genuine and are declared in `contract.DECLARED_CONSTANT`
   WITH the reason; two - `pumps/sites.lift_m` and `pumps/pruned.lift_m` - are 0.0 on every
   row because `s7_pumps.Site` is built with a literal 0.0, and the same field on
   `pumps/search_sites` varies from 0.17 to 12.96 m. Those two are NOT declared. An
   exclusion list is how a fabricated column ships.

C. A PUBLISHED TOKEN THE VOCABULARY DID NOT NAME. `roads/corridors` and `hier/reaches`
   carried SRC in {draft_base, draft_propo} and CONFIDENCE including `corroborated`. The
   contract's sets had been written for the EXPORT layers while `validate()` runs on every
   layer, so two vocabularies existed and only one was declared. The tokens are now named
   with their meanings and the collapse is declared once in SRC_EXPORT / CONFIDENCE_EXPORT.
   Naming them must not let an unmapped token reach a deliverable, which is what
   `assert_export_vocabulary()` and the second half of this file are for.

Every number here comes from `w12.criteria` (which cites its page) or is measured from the
published layers in the test body. Nothing is typed from memory.
"""
from __future__ import annotations

import pytest

from conftest import layer


# ======================================================================================
# A. G203-p48: the Q in V = 0.25 Q T is ONE PUMP
# ======================================================================================

def test_the_single_pump_capacity_divides_by_the_duty_pump_count(crit):
    """G203-p40 Table 17 fixes 1 / 2 / 3 duty pumps by type, so the single-pump share of a
    station duty is the duty over that count - and it is ONE function, so no caller has to
    remember to do the division."""
    assert (crit.ps_duty_pumps("Type 1"), crit.ps_duty_pumps("Type 2"),
            crit.ps_duty_pumps("Type 3")) == crit.PS_DUTY_PUMPS == (1, 2, 3)
    # Type 1 is the case that hid the bug: with one duty pump the two flows coincide, so a
    # check fed the station duty passes on every Type 1 and only breaks on a Type 2.
    assert crit.q_single_pump_ls(50.0, "Type 1") == 50.0
    assert crit.q_single_pump_ls(200.0, "Type 2") == 100.0
    assert crit.q_single_pump_ls(600.0, "Type 3") == 200.0
    for bad in ("Type 4", "type 2", ""):
        with pytest.raises(Exception):
            crit.ps_duty_pumps(bad)          # never default to one pump


def test_the_wet_well_volume_is_the_clause_not_the_station(crit):
    """V = 0.25 Q T with Q = single pump capacity, T = 3600/starts (G203-p48 sec 7.8).

    The arithmetic is done here from first principles rather than by calling the same
    helper the code calls, so the test can disagree with the implementation."""
    q_station_ls, starts, n_duty = 128.664, 10.0, 2          # a real published Type 2
    t = 3600.0 / starts
    by_hand = 0.25 * (q_station_ls / n_duty / 1000.0) * t
    assert abs(by_hand - 5.78988) < 1e-5
    got = crit.well_volume_m3(
        crit.q_single_pump_ls(q_station_ls, "Type 2") / 1000.0, starts)
    assert abs(got - by_hand) < 1e-9
    # and the wrong reading is exactly n_duty times too big - the defect's signature
    wrong = crit.well_volume_m3(q_station_ls / 1000.0, starts)
    assert abs(wrong / got - n_duty) < 1e-9


def test_validate_rejects_a_wet_well_sized_on_the_whole_station_duty(contract, crit):
    """The regression itself: a Type 2 sized on the station duty must FAIL, and the same
    station sized on one pump must PASS. Before 2026-09-06 the two verdicts were swapped."""
    import w12.contract as K
    stns = K._demo_stations()
    q = 128.664
    stns["Q_DUTY_LS"] = q
    stns["ST_TYPE"] = crit.ps_type(q)
    assert stns.ST_TYPE.iloc[0] == "Type 2"
    stns["LAND_M2"] = crit.ps_land_m2("Type 2")[0]
    starts = float(stns.WW_STARTS.iloc[0])

    right = stns.copy()
    right["WELL_M3"] = crit.well_volume_m3(
        crit.q_single_pump_ls(q, "Type 2") / 1000.0, starts)
    contract.validate(right, "stations")                     # must not raise

    wrong = stns.copy()
    wrong["WELL_M3"] = crit.well_volume_m3(q / 1000.0, starts)
    with pytest.raises(contract.ContractError, match="(?i)single pump"):
        contract.validate(wrong, "stations")


def test_a_published_duty_pump_count_must_agree_with_its_type(contract, crit):
    """N_DUTY is not a contract field, but the cycle rule divides by it. Where a stage
    publishes one it must match G203-p40 Table 17, or the wet well and the pump schedule
    are sized off two different pump counts and only one of them is checkable."""
    import w12.contract as K
    stns = K._demo_stations()
    stns["Q_DUTY_LS"] = 128.664
    stns["ST_TYPE"] = "Type 2"
    stns["LAND_M2"] = crit.ps_land_m2("Type 2")[0]
    stns["WELL_M3"] = crit.well_volume_m3(
        crit.q_single_pump_ls(128.664, "Type 2") / 1000.0, 10.0)
    stns["N_DUTY"] = 2
    contract.validate(stns, "stations")
    stns["N_DUTY"] = 1
    with pytest.raises(contract.ContractError, match="N_DUTY contradicts ST_TYPE"):
        contract.validate(stns, "stations")


@pytest.mark.published
def test_every_published_station_satisfies_the_cycle_rule_on_one_pump(crit):
    """The published design, measured. Both readings are computed and printed so the
    difference between them is visible rather than asserted."""
    st = layer("pumps", "stations")
    n_duty = st.ST_TYPE.map(crit.ps_duty_pumps)
    t = 3600.0 / st.WW_STARTS
    right = 0.25 * (st.Q_DUTY_LS / n_duty / 1000.0) * t
    wrong = 0.25 * (st.Q_DUTY_LS / 1000.0) * t
    tol = 0.05 * right.abs() + 0.05
    off_right = int(((st.WELL_M3 - right).abs() > tol).sum())
    off_wrong = int(((st.WELL_M3 - wrong).abs() > (0.05 * wrong.abs() + 0.05)).sum())
    multi = st[n_duty > 1]
    print(f"\n    [wet well] {len(st)} stations, {len(multi)} with more than one duty pump. "
          f"Against G203-p48's single-pump Q: {off_right} disagree. Against the station "
          f"duty (the defect): {off_wrong} disagree.")
    for _, r in multi.iterrows():
        n = crit.ps_duty_pumps(r.ST_TYPE)
        print(f"      {r.ST_TYPE} duty {r.Q_DUTY_LS:.3f} L/s over {n} pumps -> "
              f"{r.Q_DUTY_LS / n:.3f} L/s each; well {r.WELL_M3:.2f} m3, "
              f"station-duty reading would demand "
              f"{0.25 * (r.Q_DUTY_LS / 1000.0) * (3600.0 / r.WW_STARTS):.2f} m3")
    assert off_right == 0, (
        f"{off_right} published stations breach G203-p48 sec 7.8 on the single-pump "
        "reading. The volume, the per-pump duty and the start rate are one equation.")


# ======================================================================================
# B. DECLARED_CONSTANT is a ratchet with a reason, and it does not name a fabrication
# ======================================================================================

def test_every_declared_constant_carries_a_real_reason(contract):
    """A register entry with no reason is an exclusion list wearing a coat."""
    assert contract.DECLARED_CONSTANT, "the register must not be empty"
    for key, why in contract.DECLARED_CONSTANT.items():
        assert len(key) == 3 and all(isinstance(p, str) and p for p in key), key
        assert len(why) > 80, f"{key}: the reason is too short to be one"
        assert any(w in why.lower() for w in
                   ("measured", "declared parameter", "by construction", "guideline")), (
            f"{key}: the reason must say WHY it is constant - measured and the design "
            "achieved it, a declared parameter, or a guideline constant")


def test_the_fabricated_lift_column_is_not_declared_constant(contract):
    """`pumps/sites.lift_m` and `pumps/pruned.lift_m` are 0.0 on every row because
    `s7_pumps.Site` is built with a literal 0.0 (s7_pumps.py:755, :1356), not because a
    pruned station has no lift. Declaring them would ship the fabrication, and lift is half
    the evidence that a station's position was CHOSEN - the half that says what it costs."""
    for lyr in ("sites", "pruned", "search_sites"):
        assert ("pumps", lyr, "lift_m") not in contract.DECLARED_CONSTANT


@pytest.mark.published
def test_the_declared_constants_really_are_constant_in_the_published_data(contract):
    """A stale register is worse than none: it silences a column that has started varying.
    Every entry that exists in the published data must still be constant, or be removed."""
    import fiona
    from conftest import gpkg_path
    checked = 0
    for (key, name, col), why in contract.DECLARED_CONSTANT.items():
        p = gpkg_path(key)
        if not p.is_file() or name not in fiona.listlayers(str(p)):
            continue
        g = layer(key, name)
        if col not in g.columns:
            continue
        s = g[col].dropna()
        if len(s) < 50:
            continue
        checked += 1
        print(f"\n    [declared constant] {key}/{name}.{col} = {s.iloc[0]!r} on "
              f"{len(g):,} rows\n        {why[:150]}...")
        assert s.nunique() == 1, (
            f"{key}/{name}.{col} now takes {s.nunique()} values, so the DECLARED_CONSTANT "
            "entry is stale and is silencing a real measurement. Remove it.")
    assert checked, "no declared-constant column was present to check"


# ======================================================================================
# C. one vocabulary, and a gate that keeps the deliverable tight
# ======================================================================================

def test_the_vocabulary_names_the_upstream_tokens_with_a_rank(contract):
    """`corroborated` is a real rung - drawn AND independently confirmed - between surveyed
    and drafted, so it must rank between them or the P6 ceiling check reads it as the worst
    grade there is (`_CONF_RANK.get(c, 99)`) and silently never fires."""
    assert {"draft_base", "draft_propo"} <= set(contract.SRC)
    assert "corroborated" in contract.CONFIDENCE
    r = contract._CONF_RANK
    assert r["surveyed"] < r["corroborated"] < r["drafted"] < r["provisional"]
    for src, ceiling in contract.SRC_CONFIDENCE_CEILING.items():
        assert src in contract.SRC and ceiling in contract.CONFIDENCE


def test_the_export_mapping_is_declared_once_and_lands_inside_the_deliverable_set(contract):
    """s6_levels and s8_export each carry a private copy of this mapping. Two declarations
    of one mapping is how the wall allowance came to be 0.05 in one file and 0.10 in
    another. Whatever it maps TO must itself be deliverable, or the collapse just moves the
    problem."""
    assert set(contract.SRC_EXPORT) <= set(contract.SRC)
    assert set(contract.CONFIDENCE_EXPORT) <= set(contract.CONFIDENCE)
    assert set(contract.SRC_EXPORT.values()) <= set(contract.SRC_DELIVERABLE)
    assert set(contract.CONFIDENCE_EXPORT.values()) <= set(contract.CONFIDENCE_DELIVERABLE)
    # the deliverable sets are the enum minus exactly the mapped-away tokens
    assert set(contract.SRC_DELIVERABLE) == set(contract.SRC) - set(contract.SRC_EXPORT)


def test_the_export_gate_refuses_an_upstream_token_and_names_its_mapping(contract):
    """Widening the enum must not weaken the deliverable. The gate is what stops it, and it
    must say what to map the offender to rather than only that it is wrong."""
    import geopandas as gpd
    from shapely.geometry import Point

    def one(src, conf):
        return gpd.GeoDataFrame([dict(SRC=src, CONFIDENCE=conf)],
                                geometry=[Point(0.0, 0.0)], crs=contract.CRS_EPSG)

    contract.assert_export_vocabulary(one("dwg_road", "drafted"), "ok")
    with pytest.raises(contract.ContractError, match="dwg_road"):
        contract.assert_export_vocabulary(one("draft_base", "drafted"), "corridors")
    with pytest.raises(contract.ContractError, match="drafted"):
        contract.assert_export_vocabulary(one("dwg_road", "corroborated"), "corridors")
    # a token in NO mapping is a different finding and must read differently
    with pytest.raises(contract.ContractError, match="invented"):
        contract.assert_export_vocabulary(one("made_up", "drafted"), "corridors")


@pytest.mark.published
def test_every_deliverable_layer_passes_the_export_gate(contract):
    """The other half: the widened enum has not let an upstream spelling reach a client
    deliverable. Measured on W12_export.gpkg, not asserted.

    THE PATH IS RESOLVED HERE RATHER THAN THROUGH `conftest.gpkg_path`, and that is itself
    a finding for conftest's owner: `conftest.GPKGS` names 7 GeoPackages and W12/shp holds
    9. The two it omits are `W12_export.gpkg` - the client deliverable - and
    `W12_levels.gpkg`. `_all_layers()` walks GPKGS, so EVERY published and audit test in
    this suite, the vocabulary check among them, has been running past the deliverable
    package without ever opening it."""
    import fiona
    import geopandas as gpd
    from conftest import SHP_DIR
    p = SHP_DIR / "W12_export.gpkg"
    if not p.is_file():
        pytest.skip("stage 8 has not published W12_export.gpkg")
    seen = 0
    for name in fiona.listlayers(str(p)):
        g = gpd.read_file(str(p), layer=name)
        if "SRC" not in g.columns:
            continue
        seen += 1
        contract.assert_export_vocabulary(g, f"export/{name}")
    print(f"\n    [export vocabulary] {seen} deliverable layer(s) carry only the "
          f"{len(contract.SRC_DELIVERABLE)}-token export SRC set")
    assert seen, "no deliverable layer carried an SRC column"


@pytest.mark.published
def test_no_published_layer_carries_a_token_outside_the_one_vocabulary(contract):
    """The audit failure that started this, kept as a standing check on both directions:
    upstream layers may use the upstream tokens, but nobody may invent a third set.

    Walks W12/shp directly rather than `conftest.GPKGS`, which names 7 of the 9 published
    GeoPackages - see the note in test_every_deliverable_layer_passes_the_export_gate."""
    import fiona
    import geopandas as gpd
    from conftest import SHP_DIR
    bad = []
    for p in sorted(SHP_DIR.glob("W12*.gpkg")):
        key = p.stem
        for name in fiona.listlayers(str(p)):
            g = gpd.read_file(str(p), layer=name)
            for col, allowed in (("SRC", contract.SRC),
                                 ("CONFIDENCE", contract.CONFIDENCE)):
                if col not in g.columns:
                    continue
                vals = set(g[col].dropna().astype(str).str.strip()) - {""}
                extra = sorted(vals - set(allowed))
                if extra:
                    bad.append(f"  {key}/{name}.{col}: {extra}")
    assert not bad, (
        "a published layer carries a provenance token the contract does not name. An "
        "unrecognised value is a SILENT SKIP in whatever check reads it. Name it in SRC / "
        "CONFIDENCE with its meaning, or stop publishing it:\n" + "\n".join(bad))
