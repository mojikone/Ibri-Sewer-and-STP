"""THE PHYSICS. Textbook answers, checked against an independent derivation.

If these are wrong everything downstream is wrong and nothing else in the pipeline would
say so: a sewer sized on a broken Colebrook-White still publishes a diameter, still passes
every schema check, still draws.

The rule this file follows: A TEST THAT RESTATES THE IMPLEMENTATION PROVES NOTHING. So
each check derives its answer a different way from the code it is checking -

    Colebrook-White      solved IMPLICITLY for the Darcy friction factor and put through
                         Darcy-Weisbach, which is the textbook route; `hydra.v_cw_R` uses
                         the guideline's explicit rearrangement. They must agree to
                         machine precision, because they are the same equation.
    Table 11             recomputed from the equation and compared to the NINE PRINTED
                         NUMBERS in G203-p29. The guideline is the independent answer.
    the tractive minimum derived from first principles - tau = rho g R S with Manning at
                         d/D = 0.2 and n = 0.013, which is what G203-p27 says Mara, Sleigh
                         and Taylor assumed - and compared to the K and the two exponents
                         G203 prints.
    circular geometry    closed form AND numerical integration of the wetted section.
    sizing               brute force over the whole diameter series.

Sources: G203-p24 sec 4.2.1 and p28 sec 4.2.4 (Colebrook-White, k_s = 1.5 mm), p25 Table 9
(nu at 15 C), p26 sec 4.2.2.1 (0.75 m/s), p27 sec 4.2.2.1 (tractive) / 4.2.2.2 (3.0 m/s) /
Table 10 (d/D), p29 Table 11 (minimum gradients), G201-p71-72 (peaking, infiltration).
"""
from __future__ import annotations

import math

import pytest

from w12 import hydra as HY
from w12.criteria import DEFAULT as C
from w12.criteria import replace


# ======================================================================================
# 1. COLEBROOK-WHITE, against an independent implicit solve
# ======================================================================================

def _darcy_f(Re: float, ks_over_D: float) -> float:
    """Darcy friction factor from the IMPLICIT Colebrook-White equation, by fixed point:

        1/sqrt(f) = -2 log10( ks/(3.7 D) + 2.51 / (Re sqrt(f)) )

    This is the form in every textbook. `hydra` uses the guideline's explicit
    rearrangement for velocity; the two must agree exactly.
    """
    f = 0.02
    for _ in range(300):
        f_new = (-2.0 * math.log10(ks_over_D / 3.7 + 2.51 / (Re * math.sqrt(f)))) ** -2
        if abs(f_new - f) < 1e-16:
            return f_new
        f = f_new
    return f


def _v_darcy_weisbach(D: float, S: float) -> float:
    """Full-bore velocity by Darcy-Weisbach with an implicit Colebrook-White f."""
    V = 1.0
    for _ in range(300):
        f = _darcy_f(V * D / C.NU, C.KS / D)
        V_new = math.sqrt(2.0 * C.G * D * S / f)
        if abs(V_new - V) < 1e-14:
            return V_new
        V = V_new
    return V


@pytest.mark.parametrize("D", [0.200, 0.315, 0.500, 1.000, 2.400])
@pytest.mark.parametrize("S", [0.00075, 0.001, 0.005, 0.05])
def test_colebrook_white_matches_an_independent_darcy_weisbach_solve(D, S):
    """The guideline's explicit form and the textbook implicit form are one equation."""
    ours = HY.v_full(D, S)
    theirs = _v_darcy_weisbach(D, S)
    assert abs(ours - theirs) / theirs < 1e-9, (D, S, ours, theirs)


def test_the_r_form_is_the_guidelines_printed_d_form():
    """G203-p24 sec 4.2.1 prints the DIAMETER form. Everything in `hydra` is written in the
    HYDRAULIC RADIUS form so it can express a part-full pipe. At R = D/4 they must be term
    for term identical - if they are not, every part-full result is on a different
    equation from the one the guideline sanctions."""
    for D in (0.16, 0.2, 0.5, 1.2, 2.4):
        for S in (0.0005, 0.001, 0.01, 0.1):
            root = math.sqrt(2.0 * C.G * D * S)
            printed = -2.0 * root * math.log10(C.KS / (3.7 * D) + 2.51 * C.NU / (D * root))
            assert abs(HY.v_full(D, S) - printed) < 1e-12, (D, S)


def test_flow_is_fully_turbulent_across_the_design_range():
    """Colebrook-White is a turbulent-flow equation. If a design pipe ran at Re < 4000 the
    whole basis would be wrong, so check the smallest pipe at the flattest legal gradient."""
    D = C.internal_diameter(200)
    v = HY.v_full(D, C.TABLE11_FLOOR)
    Re = v * D / C.NU
    print(f"\n    [Re] DN200 bore {D * 1000:.1f} mm at the Table 11 floor "
          f"({C.TABLE11_FLOOR * 1000:.2f} mm/m): v = {v:.3f} m/s, Re = {Re:,.0f}")
    assert Re > 4000.0


def test_velocity_and_discharge_are_monotone():
    """Sanity, but the kind that catches a sign or a log base: velocity rises with
    gradient and with diameter, discharge rises with both."""
    for D in (0.2, 0.6, 1.2):
        vs = [HY.v_full(D, s) for s in (0.0005, 0.001, 0.005, 0.02)]
        assert vs == sorted(vs)
        qs = [HY.q_full(D, s) for s in (0.0005, 0.001, 0.005, 0.02)]
        assert qs == sorted(qs)
    for S in (0.001, 0.01):
        vs = [HY.v_full(d, S) for d in (0.2, 0.4, 0.8, 1.6)]
        assert vs == sorted(vs)


def test_manning_and_colebrook_white_agree_to_within_a_few_percent():
    """Not a rule - a smell test. G203-p23 Table 8 gives Manning n and the guideline uses
    n = 0.013 for the tractive derivation, so the two methods must land close at the
    self-cleansing condition. A 20 % gap would mean a units error somewhere."""
    worst = 0.0
    for dn in (200, 400, 900):
        D = dn / 1000.0
        S = C.table11(dn)
        v_manning = (1.0 / 0.013) * (D / 4.0) ** (2.0 / 3.0) * math.sqrt(S)
        v_cw = HY.v_full(D, S)
        worst = max(worst, abs(v_cw / v_manning - 1.0))
    print(f"\n    [Manning vs Colebrook-White] worst disagreement {worst * 100:.2f} % "
          f"at the Table 11 gradient, full bore, n = 0.013")
    assert worst < 0.05


# ======================================================================================
# 2. TABLE 11 - the guideline's own nine printed numbers
# ======================================================================================

def test_table11_is_reproduced_from_the_equation():
    """G203-p29 Table 11 is headed 'based on the Colebrook-White equation and acceptable
    self-cleansing velocity of 0.75 m/s'. If our equation and constants are the
    guideline's, we must be able to recompute the table it printed."""
    rows = HY.verify_table11(C)
    worst = max(abs(r["rel_err"]) for r in rows)
    at = max(rows, key=lambda r: abs(r["rel_err"]))
    print(f"\n    [Table 11] worst deviation {worst * 100:.2f} % at DN{at['DN']} "
          f"(printed {at['printed_mm_m']:.2f}, computed {at['computed_mm_m']:.3f} mm/m); "
          f"gate {HY.TABLE11_TOL * 100:.0f} %")
    assert worst <= HY.TABLE11_TOL
    assert len(rows) == 9


def test_dn200_at_table11_gradient_reaches_the_self_cleansing_velocity():
    """The single hand-checkable statement behind the whole table: a DN200 laid at
    5.00 mm/m runs at 0.75 m/s full bore."""
    v = HY.v_full(0.200, C.table11(200))
    assert abs(v - C.V_SELF_CLEANSING) < 0.01, v


def test_table11_lookup_never_interpolates_downwards(crit):
    """A size between two tabulated ones takes the SMALLER diameter's steeper value.
    Interpolating would hand a pipe a flatter gradient than the guideline prints."""
    assert crit.table11(350) == crit.TABLE11[315]
    assert crit.table11(1000) == crit.TABLE11_FLOOR
    assert crit.table11(2400) == crit.TABLE11_FLOOR
    with pytest.raises(Exception):
        crit.table11(160)          # below the table; G203-p18 Table 5 governs there


def test_table11_is_monotone_decreasing_in_diameter(crit):
    sizes = sorted(crit.TABLE11)
    vals = [crit.TABLE11[d] for d in sizes]
    assert vals == sorted(vals, reverse=True)


# ======================================================================================
# 3. THE TRACTIVE MINIMUM - derived from first principles
# ======================================================================================

def _mara_from_first_principles(tau_pa: float, q_m3s: float, n: float = 0.013,
                                y: float = 0.20):
    """Re-derive Smin = K tau^a Q^b from the physics G203-p27 says it rests on.

    The clause reads: 'Mara, Sleigh, and Taylor (2000) developed the following
    relationship for minimum slope based on the assumption of d/D = 0.2 and n = 0.013'.

        boundary shear      tau = rho g R S
        Manning             Q   = (1/n) A R^(2/3) S^(1/2)
        circular section    at d/D = 0.2, A = 7.6896 R^2   (geometry, below)

    Eliminating R and D gives S = K tau^(16/13) Q^(-6/13) with
    K = [ (A/R^2) / n * (rho g)^(-8/3) ] ^ (6/13). Nothing here is read from `criteria`
    except rho g, so the K and the two exponents come out of the physics, not the file.
    """
    theta = 2.0 * math.acos(1.0 - 2.0 * y)
    a_over_r2 = ((theta - math.sin(theta)) / 8.0) / (((theta - math.sin(theta)) / 8.0)
                                                     / (theta / 2.0)) ** 2
    rho_g = 1000.0 * C.G
    K = (a_over_r2 / n * rho_g ** (-8.0 / 3.0)) ** (6.0 / 13.0)
    return K, 16.0 / 13.0, -6.0 / 13.0, K * tau_pa ** (16.0 / 13.0) * q_m3s ** (-6.0 / 13.0)


def test_the_tractive_constant_is_derivable_from_the_physics():
    """G203-p27's equation is an EMBEDDED IMAGE with no text layer - it has been miscopied
    on this project once already. Deriving K and both exponents independently is the only
    way to know the transcription is right."""
    K, a_exp, q_exp, _ = _mara_from_first_principles(1.0, 0.010)
    print(f"\n    [Mara] derived K = {K:.4e} against G203-p27's printed "
          f"{C.TRACTIVE_K_M3S:.3e} ({(K / C.TRACTIVE_K_M3S - 1) * 100:+.2f} %); "
          f"exponents {a_exp:.4f} / {q_exp:.4f} against printed "
          f"{C.TRACTIVE_TAU_EXP} / {C.TRACTIVE_Q_EXP}")
    assert abs(K / C.TRACTIVE_K_M3S - 1.0) < 0.01, (
        "the transcribed K does not follow from tau = rho g R S with Manning at d/D = 0.2 "
        "and n = 0.013 - re-read the image on G203-p27")
    assert abs(a_exp - C.TRACTIVE_TAU_EXP) < 0.002        # 16/13 = 1.2308 vs printed 1.23
    assert abs(q_exp - C.TRACTIVE_Q_EXP) < 0.002          # -6/13 = -0.4615 vs -0.461


def test_the_tractive_gradient_delivers_the_target_shear():
    """The end-to-end check: lay a pipe at smin_tractive, run it at d/D = 0.2, and the
    boundary shear tau = rho g R S must come back as TAU_PA."""
    for q in (0.002, 0.010, 0.050):
        S = HY.smin_tractive(q, C)
        # find the bore that runs at d/D = 0.2 carrying q at that gradient
        lo, hi = 0.05, 5.0
        for _ in range(200):
            D = 0.5 * (lo + hi)
            if HY.q_partial(D, S, 0.20, C) < q:
                lo = D
            else:
                hi = D
        D = 0.5 * (lo + hi)
        _A, R = HY.segment(D, 0.20)
        tau = 1000.0 * C.G * R * S
        assert abs(tau / C.TAU_PA - 1.0) < 0.05, (q, tau)


def test_the_two_printed_k_values_are_consistent_to_source_rounding():
    """G203-p27 prints K = 2.33e-4 for Q in m3/s and 5.5e-3 for Q in L/s. They should
    differ by exactly 1000^0.461. MEASURED: they are 2.27 % apart, which is 3-significant
    against 2-significant rounding in the source - real, and worth knowing, because
    working in L/s would give gradients 2.27 % flatter."""
    ratio = C.TRACTIVE_K_LS / (C.TRACTIVE_K_M3S * 1000.0 ** 0.461)
    print(f"\n    [Mara K pair] L/s form is {(ratio - 1) * 100:+.2f} % from the m3/s form")
    assert abs(ratio - 1.0) < 0.03


def test_the_flow_floor_stops_the_gradient_running_away():
    """Smin -> infinity as Q -> 0, so the head of every run would demand an unbuildable
    gradient. TRACTIVE_QMIN (1.5 L/s, an ASSUMPTION) is the floor."""
    assert HY.smin_tractive(0.0, C) == HY.smin_tractive(C.TRACTIVE_QMIN, C)
    assert HY.smin_tractive(1e-12, C) == HY.smin_tractive(C.TRACTIVE_QMIN, C)
    assert HY.smin_tractive(0.100, C) < HY.smin_tractive(0.010, C)


def test_the_governing_minimum_is_the_steeper_of_the_two_routes():
    """G203-p27, verbatim: 'Steeper gradient calculated based on self-cleansing velocity
    and minimum tractive force methodology shall be adopted as minimum pipe gradient.'"""
    for dn in C.DN_SERIES:
        for q in (0.0015, 0.01, 0.1, 1.0):
            got = HY.smin_for(dn, q, C)
            assert got == max(HY.smin_table11(dn, C), HY.smin_tractive(q, C)), (dn, q)
            assert got >= C.TABLE11_FLOOR


def test_self_cleansing_route_is_named_and_neither_is_reachable():
    """H5 requires the route recorded on every reach, and 'neither' must be a real answer -
    a failure written away as a small number is how a network claims 100 % self-cleansing."""
    assert HY.clean_route(200, 0.030, 0.030, C) == "velocity"
    assert HY.clean_route(200, C.table11(200), 0.0005, C) == "tractive"
    assert HY.clean_route(200, 0.0001, 0.0005, C) == "neither"


# ======================================================================================
# 4. PART-FULL GEOMETRY
# ======================================================================================

def test_segment_area_and_radius_against_closed_form():
    """Half full: A = pi D^2 / 8 and R = D/4 exactly. Full: A = pi D^2 / 4, R = D/4."""
    A, R = HY.segment(1.0, 0.5)
    assert abs(A - math.pi / 8.0) < 1e-12
    assert abs(R - 0.25) < 1e-12
    # Full bore: `segment` clamps y to 1 - 1e-9 (theta -> 2 pi is a removable singularity),
    # so the tolerance here is the clamp's, not the geometry's.
    A, R = HY.segment(1.0, 1.0 - 1e-12)
    assert abs(A - math.pi / 4.0) < 1e-5
    assert abs(R - 0.25) < 1e-5


def test_segment_area_against_numerical_integration():
    """Independent of the closed form: integrate the chord width over the depth."""
    D = 1.0
    for y in (0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 0.95):
        A_closed, _R = HY.segment(D, y)
        n = 200_000
        h = y * D
        A_num = 0.0
        for i in range(n):                       # midpoint rule on chord width
            z = (i + 0.5) * h / n                # height above the invert
            r = D / 2.0
            A_num += 2.0 * math.sqrt(max(r * r - (r - z) ** 2, 0.0)) * (h / n)
        assert abs(A_closed - A_num) / A_closed < 2e-4, (y, A_closed, A_num)


def test_hydraulic_radius_peaks_above_half_full():
    """Textbook: R for a circular section peaks near d/D = 0.81, and discharge near 0.94 -
    which is why `solve_dod` inverts only on the branch up to 0.95."""
    ys = [i / 1000.0 for i in range(1, 1000)]
    y_R = max(ys, key=lambda y: HY.segment(1.0, y)[1])
    y_Q = max(ys, key=lambda y: HY.q_partial(1.0, 0.005, y, C))
    print(f"\n    [section] R peaks at d/D = {y_R:.3f}, Q at d/D = {y_Q:.3f}")
    assert 0.79 < y_R < 0.83
    assert 0.92 < y_Q < 0.96


def test_solve_dod_inverts_q_partial():
    D = C.internal_diameter(400)
    for y_true in (0.10, 0.25, 0.42, 0.60, 0.90):
        q = HY.q_partial(D, 0.004, y_true, C)
        y, v = HY.solve_dod(D, 0.004, q, C)
        assert y is not None and abs(y - y_true) < 1e-4, (y_true, y)
        assert abs(v - HY.v_partial(D, 0.004, y_true, C)) < 1e-6


def test_surcharge_returns_a_named_sentinel_not_a_large_number():
    """W10 shipped five surcharged trunk reaches and nothing in it distinguished 'full'
    from 'over capacity'."""
    y, v = HY.pipe_state(200, 0.005, 0.5)        # 500 L/s down a DN200
    assert y is None and v is None
    assert HY.dod_ok(200, None) is False


def test_hydraulics_run_on_the_true_bore_not_the_nominal_size(crit):
    """To DN315 the series is OD-designated (G203-p22 Table 6), so the bore is smaller than
    the nominal size by two wall thicknesses. Using DN/1000 overstates capacity."""
    assert crit.internal_diameter(200) < 0.200
    assert crit.internal_diameter(315) < 0.315
    assert crit.internal_diameter(400) == 0.400
    over = HY.q_full(0.200, 0.005) / HY.q_full(crit.internal_diameter(200), 0.005) - 1.0
    print(f"\n    [bore] treating DN200 as a 200 mm bore overstates its capacity by "
          f"{over * 100:.1f} %")
    assert over > 0.10


# ======================================================================================
# 5. SIZING
# ======================================================================================

def test_size_pipe_returns_the_smallest_workable_size_brute_forced():
    """Cross-checked against an exhaustive scan of the series - a different algorithm."""
    for q in (0.002, 0.02, 0.15, 0.6, 1.4):
        for s in (0.00075, 0.002, 0.010):
            dn, y, v, why = HY.size_pipe(q, s, C)
            workable = []
            for cand in C.DN_SERIES:
                yy, vv = HY.pipe_state(cand, s, q, C)
                if yy is None:
                    continue
                if yy <= C.dod_limit(cand) + 1e-12 and vv <= C.V_MAX:
                    workable.append(cand)
            if not workable:
                assert dn is None and why == "infeasible", (q, s, dn)
            else:
                assert dn == min(workable), (q, s, dn, workable)
                assert why in ("minimum", "dod", "capacity", "velocity"), why


def test_size_pipe_records_why_and_never_answers_depth():
    """Philosophy: 'depth' is not an admissible answer for a diameter (G203-p29, and Ten
    States sec 33.43 independently). The reason is returned as a fourth value so the
    prohibition is checkable."""
    for q in (0.001, 0.05, 0.5):
        _dn, _y, _v, why = HY.size_pipe(q, 0.005, C)
        assert why in ("minimum", "dod", "capacity", "velocity", "infeasible")
        assert "depth" not in why


def test_the_dod_limit_is_enforced_at_the_table_10_threshold():
    for q in (0.05, 0.3, 1.0):
        dn, y, _v, _w = HY.size_pipe(q, 0.003, C)
        assert dn is not None
        assert y <= C.dod_limit(dn) + 1e-12, (dn, y, C.dod_limit(dn))


def test_an_impossible_flow_returns_the_sentinel_not_the_biggest_pipe():
    dn, y, v, why = HY.size_pipe(50.0, 0.0005, C)
    assert dn is None and y is None and v is None and why == "infeasible"


def test_dn_min_is_honoured_so_a_reach_never_shrinks(crit):
    """A downstream reach may not be smaller than the one feeding it."""
    dn, *_ = HY.size_pipe(0.002, 0.005, C, dn_min=400)
    assert dn == 400
    dn, *_ = HY.size_pipe(0.002, 0.005, C, dn_min=1200)
    assert dn == 1200


def test_smax_is_where_velocity_reaches_three_metres_per_second():
    """G203-p27 sec 4.2.2.2 / p29 sec 4.3.2. The feasible set is an INTERVAL, so a single
    bisection collapses; this proves the returned slope really is the cap."""
    assert HY.smax_for(1200, 0.005, C) is None                 # big pipe, small flow
    s = HY.smax_for(200, 0.010, C)
    assert s is not None and s != HY.INFEASIBLE
    _y, v = HY.pipe_state(200, s, 0.010, C)
    assert abs(v - C.V_MAX) < 0.05, v
    assert HY.smax_for(200, 2.0, C) == HY.INFEASIBLE            # 2 m3/s down a DN200


def test_retention_time_is_length_over_velocity():
    """Septicity is a design driver (philosophy sec 6) and retention time is the reported
    quantity. 120 m at 1 m/s is 2 minutes."""
    assert abs(HY.retention_min(120.0, 1.0) - 2.0) < 1e-12
    assert HY.retention_min(120.0, 0.0) is None
    assert HY.retention_min(120.0, None) is None


# ======================================================================================
# 6. LOADS AND PEAKING - G201
# ======================================================================================

def test_merrimack_at_one_megalitre_per_day_is_the_printed_coefficient(crit):
    """G201-p71 sec 7.4.2: Qpdf = 2.65 Qadf^0.879, BOTH in Ml/day. At 1 Ml/d the peak
    factor is exactly 2.65, and the Ml/d conversion is the trap - 1,000 m3/d is 1 Ml/d."""
    assert abs(crit.pf_merrimack(1.0) - crit.PF_MERRIMACK_A) < 1e-12
    pf, meth = crit.peak_factor(1000.0, 500)
    assert meth == "merrimack" and abs(pf - crit.PF_MERRIMACK_A) < 1e-12


def test_merrimack_falls_as_the_catchment_grows(crit):
    pf = [crit.pf_merrimack(q) for q in (0.1, 1.0, 10.0, 100.0)]
    assert pf == sorted(pf, reverse=True)


def test_peak_factor_is_held_below_one_hundred_properties(crit):
    """G201-p71: Merrimack 'is to be used' above 100 properties and the guideline gives no
    formula below it. An honest hold beats a number nobody can reproduce."""
    pf, meth = crit.peak_factor(50.0, crit.PF_HOLD_PROPERTIES)
    assert meth == "held" and pf == 1.0
    _pf, meth = crit.peak_factor(50.0, crit.PF_HOLD_PROPERTIES + 1)
    assert meth == "merrimack"


def test_peltier_is_in_litres_per_second(crit):
    """G201-p72 puts the unit in a NOTE because it is the easy mistake:
    PfWW = 1.5 + 1/sqrt(Qm) with Qm in L/s. At 1 L/s that is 2.5."""
    assert abs(crit.pf_peltier(1.0) - 2.5) < 1e-12
    assert abs(crit.pf_peltier(100.0) - 1.6) < 1e-12


def test_infiltration_is_per_pipe_and_scales_linearly(crit):
    """G201-p72 sec 7.4.3: 720 L/d per km of sewer. Summing a per-reach value that already
    includes everything upstream counted every kilometre once per downstream reach - which
    is how 14.5 L/s was published as 1,259."""
    one_km = crit.infiltration_ls(1000.0)
    assert abs(one_km - crit.INFILT_L_D_KM / 86400.0) < 1e-15
    assert abs(crit.infiltration_ls(2000.0) - 2.0 * one_km) < 1e-15
    total = crit.infiltration_ls(1_819_400.0)
    print(f"\n    [infiltration] the whole 1,819.4 km network at 720 L/d/km = "
          f"{total:.2f} L/s")
    assert 14.0 < total < 16.0


def test_the_per_property_load_is_derived_not_asserted(crit):
    """OCCUPANCY x WWG_LCD / 1000. Both are stated with their sources; the product is not
    a separate constant that could drift from them."""
    assert abs(crit.PLOT_QADF_M3D - crit.OCCUPANCY * crit.WWG_LCD / 1000.0) < 1e-15
    alt = replace(crit, OCCUPANCY=6.0)
    assert abs(alt.PLOT_QADF_M3D - 6.0 * crit.WWG_LCD / 1000.0) < 1e-15


# ======================================================================================
# 7. GRADIENT ROUNDING - P1, and the trap in it
# ======================================================================================

def test_a_single_pipe_always_rounds_its_gradient_up(crit):
    """Rounding a single pipe DOWN would breach the minimum. 0.05 % steps, user rule
    2026-08-23."""
    for s in (0.0001, 0.00075, 0.0005, 0.005, 0.00051, 0.0123):
        up = crit.round_slope_up(s)
        assert up >= s - 1e-15
        assert abs(up / crit.SLOPE_STEP - round(up / crit.SLOPE_STEP)) < 1e-9
    assert crit.round_slope_up(0.0005) == pytest.approx(0.0005)
    assert crit.round_slope_up(0.00051) == pytest.approx(0.0010)
    assert crit.round_slope_down(0.00099) == pytest.approx(0.0005)


def test_the_table11_floor_is_not_a_round_slope_step(crit):
    """The trap P1 hides: the flattest legal gradient, 0.75 mm/m, is NOT a multiple of the
    0.05 % step, so rounding a DN900+ up to a step costs a third more fall than the
    guideline asks. Worth knowing, not worth fixing here."""
    steps = crit.TABLE11_FLOOR / crit.SLOPE_STEP
    assert abs(steps - round(steps)) > 1e-6
    rounded = crit.round_slope_up(crit.TABLE11_FLOOR)
    print(f"\n    [P1 vs Table 11] the 0.75 mm/m floor rounds up to "
          f"{rounded * 1000:.2f} mm/m - {(rounded / crit.TABLE11_FLOOR - 1) * 100:.0f} % "
          f"more fall than G203-p29 requires")
    assert rounded > crit.TABLE11_FLOOR
