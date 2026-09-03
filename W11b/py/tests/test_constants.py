"""DEFECT CLASS 1 - TWO CONSTANTS FOR ONE QUANTITY.

The bug: a wall/bedding allowance was 0.10 in the auditor and 0.05 in the criteria. Every
reach then failed a BLOCKING minimum-cover check by exactly 50 mm, at every diameter, and
the design was correct all along. Nothing in the pipeline could see it, because each file
was internally consistent.

Four independent ways of catching it, weakest to strongest:

  1  ROUND TRIP.      cover() and invert_depth_min() are inverses. If two allowances exist
                      the round trip does not close.
  2  SENSITIVITY.     Move the constant with `replace()`; every consumer must move with it.
                      A second copy does not move, so the derivative is wrong.
  3  CROSS-REGISTER.  This project transcribes the same guideline pages into THREE
                      independent registers - `criteria.Criteria`, `asbuilt.G203_*` and
                      `present.G`. Three transcriptions of one page is the best available
                      test of a transcription: any two that disagree means one is wrong.
  4  SOURCE SCAN.     No module-level constant name may carry two different values across
                      W11b, and no distinctive criteria value may appear as a bare literal
                      in executable code outside `criteria.py`.

Nothing here invents a number: every value compared is read from the modules themselves.
"""
from __future__ import annotations

import ast
import dataclasses
import math
from pathlib import Path

import pytest

from conftest import PY_DIR


# ======================================================================================
# 1. ROUND TRIP - the exact shape of the 0.05 / 0.10 defect
# ======================================================================================

def test_cover_and_invert_depth_are_exact_inverses(crit):
    """cover(dn, invert_depth_min(dn)) must return MIN_COVER_CROWN at EVERY diameter.

    This closes only if one allowance exists. G203-p33 sec 4.6.3.
    """
    for dn in crit.DN_SERIES:
        c = crit.cover(dn, crit.invert_depth_min(dn))
        assert abs(c - crit.MIN_COVER_CROWN) < 1e-12, (
            f"DN{dn}: the round trip closes at {c:.6f} m, not {crit.MIN_COVER_CROWN} m. "
            f"There is a second wall/bedding allowance somewhere.")


def test_contract_wrappers_are_the_criteria_functions(contract, crit):
    """`contract.min_invert_depth` / `contract.cover` must be thin wrappers, not copies.

    This is the exact pair that diverged in W11a: criteria carried WALL_ALLOW = 0.05 and
    the contract carried its own 0.10.
    """
    for dn in crit.DN_SERIES:
        assert contract.min_invert_depth(dn) == crit.invert_depth_min(dn), dn
        for d in (2.0, 5.0, 11.9):
            assert contract.cover(dn, d) == crit.cover(dn, d), (dn, d)


def test_no_second_wall_allowance_anywhere(crit, contract):
    """Move WALL_ALLOW and BOTH sides must move by the same amount.

    A second constant does not move, and the gap it opens is exactly the 50 mm that failed
    every reach.
    """
    from w11b.criteria import replace
    alt = replace(crit, WALL_ALLOW=crit.WALL_ALLOW + 0.037)
    for dn in crit.DN_SERIES:
        d_design = alt.invert_depth_min(dn) - crit.invert_depth_min(dn)
        d_check = crit.cover(dn, 5.0) - alt.cover(dn, 5.0)
        assert abs(d_design - 0.037) < 1e-12, (dn, d_design)
        assert abs(d_check - 0.037) < 1e-12, (dn, d_check)


def test_chamber_clearance_alias_follows_its_base(crit):
    """MH_MIN_CLEAR_M is documented as a read-only alias of MH_SNAP_M. Prove it."""
    from w11b.criteria import replace
    assert crit.MH_MIN_CLEAR_M == crit.MH_SNAP_M
    alt = replace(crit, MH_SNAP_M=2.0)
    assert alt.MH_MIN_CLEAR_M == 2.0, (
        "MH_MIN_CLEAR_M did not follow MH_SNAP_M - it is a second field again, and the "
        "layout stage and the audit stage will disagree about whether two chambers are "
        "one structure.")
    with pytest.raises(Exception):
        replace(crit, MH_MIN_CLEAR_M=2.0)          # a property, so this must not be settable


def test_depth_of_flow_limit_has_one_definition(crit):
    """dod_limit() is a FUNCTION, not two exported constants. W11a exported the pair and a
    caller reaching for the wrong one shipped 168 trunk reaches over the limit.
    G203-p27 Table 10, and the threshold is inclusive at 350 ("up to 350 mm")."""
    assert crit.dod_limit(350) == crit.DOD_MAX_SMALL
    assert crit.dod_limit(351) == crit.DOD_MAX_LARGE
    assert crit.dod_limit(200) == 0.65 and crit.dod_limit(400) == 0.50


# ======================================================================================
# 2. SENSITIVITY - every consumer of a constant must move when the constant moves
# ======================================================================================

def test_tau_moves_every_tractive_gradient(crit, hydra):
    """GAP-9. tau is assumed 1.0 Pa and NWS have not confirmed it. Every tractive-governed
    gradient must be a pure power law in tau (G203-p27 sec 4.2.2.1), so the ratio at 2 Pa
    is 2^1.23 at EVERY diameter and EVERY flow - if it is not, something has cached a
    gradient computed at the old tau."""
    from w11b.criteria import replace
    alt = replace(crit, TAU_PA=2.0)
    factor = 2.0 ** crit.TRACTIVE_TAU_EXP
    for q in (0.0015, 0.01, 0.1, 1.0):
        assert abs(hydra.smin_tractive(q, alt) / hydra.smin_tractive(q, crit) - factor) < 1e-12
    assert abs(crit.TAU_SLOPE_FACTOR_AT_2PA - factor) < 1e-12


def test_self_cleansing_velocity_moves_table11_reproduction(crit, hydra):
    """Table 11 is Colebrook-White at 0.75 m/s. Raise the velocity and every reproduced
    gradient must get steeper - proving verify_table11 reads the criteria value rather
    than a hard-coded 0.75."""
    from w11b.criteria import replace
    alt = replace(crit, V_SELF_CLEANSING=0.90)     # G203-p26's own "preferred" figure
    base = {r["DN"]: r["computed_mm_m"] for r in hydra.verify_table11(crit)}
    high = {r["DN"]: r["computed_mm_m"] for r in hydra.verify_table11(alt)}
    for dn in base:
        assert high[dn] > base[dn] * 1.2, dn


def test_dn_series_is_the_only_size_list(crit, hydra, contract):
    """One series. `size_pipe` may only return a size in it, and the contract range-checks
    DN against the same tuple. W11a stopped at DN1200 in one place and tabulated 1400-2400
    in another; 168 reaches breached d/D for want of a size the code could not emit."""
    for q in (0.005, 0.05, 0.5, 2.0):
        dn, _y, _v, _why = hydra.size_pipe(q, 0.005, crit)
        assert dn is None or dn in crit.DN_SERIES, (q, dn)
    # The contract enforces MEMBERSHIP of criteria.DN_SERIES, not a range - so the layer
    # and the sizing function cannot disagree about what sizes exist. The lo/hi on the
    # field is only a range guard and must bracket the series without narrowing it.
    spec = contract.LAYERS["reaches"].field("DN")
    assert spec.lo <= min(crit.DN_SERIES) and spec.hi >= max(crit.DN_SERIES), (
        f"the reach layer's DN guard [{spec.lo}, {spec.hi}] does not bracket "
        f"criteria.DN_SERIES [{min(crit.DN_SERIES)}, {max(crit.DN_SERIES)}]")
    src = (PY_DIR / "w11b" / "contract.py").read_text(encoding="utf-8")
    assert "C.DN_SERIES" in src, (
        "validate() no longer checks DN against criteria.DN_SERIES - a size the sizing "
        "function cannot emit could then be published, which is how W11a shipped 168 "
        "trunk reaches over the d/D limit for want of DN1400+")


def test_drop_ceiling_is_one_constant(crit, contract):
    """Philosophy sec 5: the drop ceiling is a PROJECT DECISION and 'design and validator
    read the same constant so they cannot drift'. Prove they do."""
    spec = contract.LAYERS["nodes"].field("DROP_M")
    assert spec.hi == crit.DROP_CEILING_M, (
        f"contract NODES.DROP_M.hi = {spec.hi} but criteria.DROP_CEILING_M = "
        f"{crit.DROP_CEILING_M}. This is the pair philosophy sec 5 names by hand.")


# ======================================================================================
# 3. CROSS-REGISTER - three transcriptions of the same guideline pages must agree
# ======================================================================================
# (criteria expression, asbuilt symbol or None, present key or None, page, tolerance)
# Every row is a value that appears in at least two of the three registers. Where a row
# needs a unit conversion the conversion is written into the lambda, in the open.

def _cross_rows(C, A, P):
    g = P.G
    return [
        # ---- G203-p22 Table 6, sizes ------------------------------------------------
        ("min rider / PC size, mm", C.DN_TERTIARY, A.G203_P22_OD_RIDER_MIN_MM,
         g["DN_MIN_CONNECTION"][0], "G203-p22 T6", 0),
        ("min lateral size, mm", C.DN_MIN_LATERAL, A.G203_P22_OD_LATERAL_MIN_MM,
         g["DN_MIN_LATERAL"][0], "G203-p22 T6", 0),
        ("max lateral length, m", C.LATERAL_MAX_LEN, A.G203_P22_LATERAL_MAX_LEN_M,
         g["LATERAL_MAX_LEN_M"][0], "G203-p22 T6", 0),
        ("min main size, mm", C.DN_MIN_MAIN, A.G203_P22_OD_MAIN_MIN_MM, None,
         "G203-p22 T6", 0),
        # ---- G203-p24/p26/p27, hydraulics -------------------------------------------
        ("Colebrook-White ks, mm", C.KS * 1000.0, A.G203_P28_KS_MM, None, "G203-p28", 1e-12),
        ("self-cleansing velocity, m/s", C.V_SELF_CLEANSING, A.G203_P26_V_MIN_MS,
         g["V_SELFCLEAN_MS"][0], "G203-p26", 1e-12),
        ("preferred velocity, m/s", C.V_PREFERRED, A.G203_P26_V_PREFERRED_MS,
         g["V_PREFERRED_MS"][0], "G203-p26", 1e-12),
        ("max gravity velocity, m/s", C.V_MAX, A.G203_P27_V_MAX_MS, g["V_MAX_MS"][0],
         "G203-p27", 1e-12),
        ("d/D limit at DN200", C.dod_limit(200), A.G203_P27_TAB10_DD_LE350,
         g["DOD_MAX_LE350"][0], "G203-p27 T10", 1e-12),
        ("d/D limit at DN400", C.dod_limit(400), A.G203_P27_TAB10_DD_GT350,
         g["DOD_MAX_GT350"][0], "G203-p27 T10", 1e-12),
        ("d/D diameter split, mm", C.DOD_DN_THRESHOLD, None, g["DOD_DN_SPLIT_MM"][0],
         "G203-p27 T10", 0),
        ("Mara K, Q in m3/s", C.TRACTIVE_K_M3S, A.G203_P27_MARA_K_M3S, None,
         "G203-p27 4.2.2.1", 1e-18),
        ("Mara K, Q in L/s", C.TRACTIVE_K_LS, A.G203_P27_MARA_K_LS, None,
         "G203-p27 4.2.2.1", 1e-18),
        ("tau exponent", C.TRACTIVE_TAU_EXP, None, g["TAU_EXPONENT"][0],
         "G203-p27 4.2.2.1", 1e-12),
        # ---- G203-p30, manholes and drops -------------------------------------------
        ("backdrop trigger, m", C.DROP_TRIGGER, A.G203_P30_BACKDROP_TRIGGER_M,
         g["DROP_BACKDROP_M"][0], "G203-p30", 1e-12),
        ("backdrop max, m", C.BACKDROP_MAX, A.G203_P30_BACKDROP_MAX_M,
         g["DROP_VORTEX_M"][0], "G203-p30", 1e-12),
        ("min inlet angle, deg", C.INLET_MIN_DEG, A.G203_P30_INLET_ANGLE_MIN_DEG,
         g["INLET_ANGLE_DEG"][0], "G203-p30", 1e-12),
        # ---- G203-p33, cover ---------------------------------------------------------
        ("min cover to crown, m", C.MIN_COVER_CROWN, A.G203_P33_MIN_COVER_M,
         g["MIN_COVER_CROWN_M"][0], "G203-p33 4.6.3", 1e-12),
        ("min cover, protected, m", C.MIN_COVER_PROTECTED, A.G203_P33_MIN_COVER_PROTECTED_M,
         g["MIN_COVER_PROT_M"][0], "G203-p33 4.6.3", 1e-12),
        ("max cover, m", C.MAX_COVER, A.G203_P33_MAX_COVER_M[1], g["MAX_COVER_M"][0],
         "G203-p33 4.6.3", 1e-12),
        ("utility clearance, m", C.UTILITY_CLEARANCE_M, None, g["CLEAR_UTILITY_M"][0],
         "G203-p33", 1e-12),
        # ---- G203-p35, the trunk ------------------------------------------------------
        ("trunk definition, mm", C.DN_TRUNK_MIN, None, g["DN_TRUNK_DEF_MM"][0],
         "G203-p35 sec 5", 0),
        # ---- G203-p40/p43, stations ---------------------------------------------------
        ("Type 1 ceiling, L/s", C.PS_TYPE1_MAX_LS, None, g["PS_TYPE1_MAX_LS"][0],
         "G203-p40 T17", 1e-12),
        ("Type 2 ceiling, L/s", C.PS_TYPE2_MAX_LS, None, g["PS_TYPE2_MAX_LS"][0],
         "G203-p40 T17", 1e-12),
        ("Type 1 land min, m2", C.PS_LAND_M2_MIN[0], None, g["PS_LAND_T1_M2"][0][0],
         "G203-p43 T21", 1e-12),
        ("Type 2 land min, m2", C.PS_LAND_M2_MIN[1], None, g["PS_LAND_T2_M2"][0][0],
         "G203-p43 T21", 1e-12),
        ("Type 3 land min, m2", C.PS_LAND_M2_MIN[2], None, g["PS_LAND_T3_M2"][0][0],
         "G203-p43 T21", 1e-12),
        # ---- G203-p50/p52, force mains ------------------------------------------------
        ("force main v min, m/s", C.FM_V_MIN, None, g["FM_V_MIN_MS"][0], "G203-p50", 1e-12),
        ("force main v max, m/s", C.FM_V_MAX, None, g["FM_V_MAX_MS"][0], "G203-p50", 1e-12),
        ("force main retention, min", C.FM_RETENTION_MIN, None, g["FM_RETENTION_MIN"][0],
         "G203-p50", 1e-12),
        ("wadi crossing cover, m", C.MIN_COVER_WADI_XING, None, g["FM_COVER_WADI_M"][0],
         "G203-p52 8.2.4", 1e-12),
        # ---- G201, loads --------------------------------------------------------------
        ("Merrimack coefficient", C.PF_MERRIMACK_A, A.G201_P71_MERRIMACK[0], None,
         "G201-p71 7.4.2", 1e-12),
        ("Merrimack exponent", C.PF_MERRIMACK_B, A.G201_P71_MERRIMACK[1], None,
         "G201-p71 7.4.2", 1e-12),
        ("Peltier constant", C.PF_PELTIER_A, A.G201_P72_PELTIER[0], None,
         "G201-p72", 1e-12),
        ("peak factor report threshold", C.PF_REPORT_ABOVE, A.G201_P72_PF_CAP_RECOMMENDED,
         None, "G201-p72", 1e-12),
        ("new-network infiltration, L/d/km", C.INFILT_L_D_KM, A.G201_P72_INFIL_NEW_L_D_KM,
         None, "G201-p72 7.4.3", 1e-12),
        ("existing inland infiltration", C.INFILT_EXISTING_INLAND,
         A.G201_P72_INFIL_EXISTING_INLAND, None, "G201-p72 7.4.3", 1e-12),
        # ---- project assumptions -------------------------------------------------------
        ("tractive stress tau, Pa (GAP-9)", C.TAU_PA, A.A_TAU_PA, None,
         "project assumption 2026-09-03", 1e-12),
        ("slope step, %", C.SLOPE_STEP * 100.0, None, g["SLOPE_STEP_PCT"][0],
         "project rule P1", 1e-12),
        ("steepest Table 11, %", C.table11(200) * 100.0, None, g["SMIN_STEEPEST_PCT"][0],
         "G203-p29 T11", 1e-12),
        ("flattest Table 11, %", C.TABLE11_FLOOR * 100.0, None, g["SMIN_FLATTEST_PCT"][0],
         "G203-p29 T11", 1e-12),
    ]


def test_three_registers_agree_value_by_value(crit):
    """criteria.py, asbuilt.py and present.py each transcribe the same guideline pages.
    Any disagreement means one of the three was mis-read from the PDF."""
    import w11b.asbuilt as A
    import w11b.present as P

    bad = []
    n = 0
    for label, c_val, a_val, p_val, page, tol in _cross_rows(crit, A, P):
        for other, who in ((a_val, "asbuilt"), (p_val, "present")):
            if other is None:
                continue
            n += 1
            if abs(float(c_val) - float(other)) > tol:
                bad.append(f"  {label} [{page}]: criteria {c_val!r} vs {who} {other!r}")
    print(f"\n    [cross-register] {n} paired values compared across three transcriptions")
    assert not bad, ("guideline values transcribed twice and differently:\n"
                     + "\n".join(bad))


def test_table11_transcribed_identically_in_two_registers(crit):
    """G203-p29 Table 11 is typed out in criteria (m/m) and in asbuilt (mm/m). Nine rows,
    two transcriptions - and the gradient table is the one a reviewer checks first."""
    import w11b.asbuilt as A
    a = A.G203_P29_TAB11_MIN_GRADIENT_MM_M
    assert set(a) == set(crit.TABLE11), (set(a) ^ set(crit.TABLE11))
    for dn, mm_m in a.items():
        assert abs(crit.TABLE11[dn] * 1000.0 - mm_m) < 1e-9, (
            f"DN{dn}: criteria {crit.TABLE11[dn] * 1000:.3f} mm/m vs asbuilt {mm_m} mm/m")


def test_manhole_spacing_bands_agree(crit):
    """G203-p30 Table 12 exists as bands in criteria, as a band list in asbuilt and as a
    per-DN dict in present. All three must give one answer for every size we can emit."""
    import w11b.asbuilt as A
    import w11b.present as P
    per_dn = P.G["MH_SPACING_M"][0]
    for dn in crit.DN_SERIES:
        c = crit.mh_max_spacing(dn)
        if dn in per_dn:
            assert c == per_dn[dn], f"DN{dn}: criteria {c} vs present {per_dn[dn]}"
        hit = [s for lo, hi, s in A.G203_P30_TAB12_MAX_MH_SPACING_M if lo <= dn <= hi]
        if hit:
            assert c == hit[0], f"DN{dn}: criteria {c} vs asbuilt {hit[0]}"


def test_force_main_roughness_is_not_the_gravity_roughness(crit):
    """G203-p50 sends force mains to G202-p104 Table 21; criteria.KS = 1.5 mm is the
    GRAVITY sewer value (G203-p24 / p28). Conflating them overstates force-main friction
    several-fold - the same class of error as the 2.5 / 3.0 m/s velocity conflation."""
    from w11b.pumping import PUMP
    di = PUMP.FM_EPS_M[("DI", PUMP.FM_DESIGN_AGE_YR)]
    assert di < crit.KS / 2.0, (
        f"ductile-iron epsilon {di * 1000:.3f} mm is not clearly distinct from the gravity "
        f"k_s {crit.KS * 1000:.1f} mm - check that the two clauses have not been merged")
    assert crit.NU == PUMP.NU if hasattr(PUMP, "NU") else True
    assert PUMP.FM_TEMP_C == 15.0                      # G203-p25 Table 9, the criteria.NU row


# ======================================================================================
# 4. SOURCE SCAN - mechanical, over every W11b python file
# ======================================================================================

def _w11b_sources():
    files = sorted(PY_DIR.glob("*.py")) + sorted((PY_DIR / "w11b").glob("*.py"))
    return [f for f in files if f.name != "__init__.py"]


def _module_constants():
    """{NAME: [(file, value), ...]} for every module-level UPPERCASE literal assignment."""
    out = {}
    for f in _w11b_sources():
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for tg in targets:
                if not (isinstance(tg, ast.Name) and tg.id.isupper() and len(tg.id) > 2):
                    continue
                v = node.value
                if isinstance(v, ast.Constant) and isinstance(v.value, (int, float, str, bool)):
                    out.setdefault(tg.id, []).append((f.name, v.value))
    return out


# Names that are deliberately per-module identity, not a quantity. Each is a label the
# module stamps on its own output, so two modules holding different values is the point.
_IDENTITY_NAMES = {"STAGE", "STAGE_ORDER", "STAGE_VERSION", "GPKG_NAME", "OUT_GPKG",
                   "OUT_KMZ", "REPORT_MD", "RUN_DIR", "OUT_DIR",
                   "CONTRACT_VERSION", "HYDRA_VERSION", "CRITERIA_VERSION",
                   "PRESENT_VERSION", "TERRAIN_VERSION", "HAZARD_VERSION"}

# ONE NAME, TWO VALUES, and both are real. Recorded rather than hidden: the test asserts
# this set has not GROWN, so the two known cases cannot multiply and cannot be forgotten.
# Neither is a live defect today; both are the exact SHAPE of the 0.05 / 0.10 defect.
_KNOWN_NAME_CLASHES = {
    "ENDPOINT_TOL_M": (
        "s1_roads.py 0.001 m (a WRITING tolerance: published geometry against the "
        "published US_NODE/DS_NODE) vs contract.py 0.005 m (HALF the 0.01 m graph snap, "
        "per endpoint). s1 is the stricter, so s1 passing implies the contract passes and "
        "nothing is wrong today. FIX: rename s1's to WRITE_TOL_M."),
    "PROFILE_STEP_M": (
        "s7_pumps.py 25.0 m (chainage along a rising main) vs terrain.py 5.0 m (chainage "
        "when sampling a line's terrain profile). Two genuinely different sampling steps "
        "under one name. FIX: rename to RM_PROFILE_STEP_M / DEM_PROFILE_STEP_M."),
}


def test_no_constant_name_carries_two_values():
    """A quantity has one definition. Where a name is defined twice with different values,
    it is either a defect or a naming collision, and both need saying out loud."""
    clashes = {}
    for name, defs in _module_constants().items():
        if name in _IDENTITY_NAMES or len(defs) < 2:
            continue
        if len({v for _f, v in defs}) > 1:
            clashes[name] = defs
    new = {k: v for k, v in clashes.items() if k not in _KNOWN_NAME_CLASHES}
    for k in sorted(set(_KNOWN_NAME_CLASHES) & set(clashes)):
        print(f"\n    [known clash] {k}: {_KNOWN_NAME_CLASHES[k]}")
    assert not new, (
        "a constant name now carries two different values in two files - this is the "
        "0.05 / 0.10 defect again:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(new.items())))


def test_same_value_duplicates_are_declared_not_accidental():
    """A name defined twice with the SAME value is a clash waiting to happen: change one
    and they diverge silently. Allowed only where the second definition says in a comment
    that it is a deliberate re-declaration, so a stage does not import another stage's
    internals."""
    dupes = {}
    for name, defs in _module_constants().items():
        if name in _IDENTITY_NAMES or len(defs) < 2:
            continue
        if len({v for _f, v in defs}) == 1:
            dupes[name] = sorted({f for f, _v in defs})
    # Each of these is re-declared on purpose and says so at the point of declaration.
    # Each is re-declared on purpose and says so at the point of declaration, or is a
    # unit conversion rather than a design number.
    declared = {"CRS", "CRS_EPSG", "GRID", "PLOT_LOADS_LAYER", "DUAL_BAND_M", "FRONTAGE_M",
                "SEC_PER_DAY", "MM_PER_M", "M_PER_KM", "L_PER_M3"}
    undeclared = {k: v for k, v in dupes.items() if k not in declared}
    print(f"\n    [same-value duplicates] {len(dupes)} names, "
          f"{len(undeclared)} not on the declared list")
    assert not undeclared, (
        "a value is defined twice under one name with no note saying the repeat is "
        "deliberate:\n" + "\n".join(f"  {k}: {v}" for k, v in sorted(undeclared.items())))


def _significant_digits(v: float) -> int:
    s = f"{abs(float(v)):.12g}".split("e")[0].replace(".", "").lstrip("0")
    return len(s.rstrip("0")) or 1


def test_no_distinctive_criteria_value_is_re_typed_as_a_literal(crit):
    """A criteria value with three or more significant figures cannot appear by accident.
    Where one is typed again as a bare literal in executable code, it is a second copy.

    Two legitimate exceptions, both narrow:
      * `w11b.asbuilt` and `w11b.present` are the deliberate second and third
        transcriptions the cross-register test above compares against.
      * a `_self_test` / `selftest` body may restate a constant, because restating it
        independently is what the check IS.
    """
    governed = {}
    for f in dataclasses.fields(crit):
        v = getattr(crit, f.name)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v != 0:
            if _significant_digits(v) >= 3:
                governed.setdefault(round(float(v), 12), []).append(f.name)
    for dn, s in crit.TABLE11.items():
        if _significant_digits(s) >= 3:
            governed.setdefault(round(float(s), 12), []).append(f"TABLE11[{dn}]")

    exempt_files = {"criteria.py", "asbuilt.py", "present.py"}
    hits = []
    for f in _w11b_sources():
        if f.name in exempt_files:
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"))
        selftest_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and "selftest" in node.name.replace("_", ""):
                selftest_lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant)
                    and isinstance(node.value, (int, float))
                    and not isinstance(node.value, bool)):
                k = round(float(node.value), 12)
                if k in governed and node.lineno not in selftest_lines:
                    hits.append(f"  {f.name}:{node.lineno}  {node.value!r} == "
                                f"criteria.{'/'.join(governed[k])}")
    # `pumping.py` writes 9.81 twice for hydraulic power where criteria.G already holds it.
    # Same value, so no live defect - but it is a second copy and it is named here rather
    # than waved through.
    known = [h for h in hits if h.strip().startswith("pumping.py") and "9.81" in h]
    for h in known:
        print(f"\n    [known re-typed literal]{h}  (criteria.G; same value, no live defect)")
    new = [h for h in hits if h not in known]
    assert not new, (
        "a criteria value has been typed again as a literal - it is now defined twice:\n"
        + "\n".join(new))


def test_no_governed_value_hides_in_a_default_argument():
    """The nastiest form of the defect: a design number as a function's default argument.
    It reads as a signature, never as a constant, and `replace(DEFAULT, ...)` cannot move
    it. Every default that is a design number must be `None` or come from `crit`."""
    from w11b.criteria import DEFAULT
    governed = {round(float(getattr(DEFAULT, f.name)), 12)
                for f in dataclasses.fields(DEFAULT)
                if isinstance(getattr(DEFAULT, f.name), (int, float))
                and not isinstance(getattr(DEFAULT, f.name), bool)
                and getattr(DEFAULT, f.name) != 0
                and _significant_digits(getattr(DEFAULT, f.name)) >= 3}
    bad = []
    for f in _w11b_sources():
        if f.name in {"criteria.py", "asbuilt.py", "present.py"}:
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for d in list(node.args.defaults) + list(node.args.kw_defaults):
                if (isinstance(d, ast.Constant) and isinstance(d.value, (int, float))
                        and not isinstance(d.value, bool)
                        and round(float(d.value), 12) in governed):
                    bad.append(f"  {f.name}:{node.lineno} def {node.name}(... = {d.value!r})")
    assert not bad, ("a design number is a function default - it cannot be moved by "
                     "replace() and it is invisible to a reviewer:\n" + "\n".join(bad))
