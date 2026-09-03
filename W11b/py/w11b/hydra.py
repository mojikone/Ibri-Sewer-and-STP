"""w11b.hydra - the hydraulics. Colebrook-White on the TRUE INTERNAL BORE, Table 11, the
tractive minimum, the depth-of-flow limit, and pipe sizing.

W11b owns this file. It imports only `w11b.criteria`; nothing from W8, W10 or W11a.

PLAIN FUNCTIONS, NOT A CLASS. This is pure maths with no state, it is the most heavily
exercised code in the pipeline, and `verify_table11()` proves it reproduces the guideline's
OWN printed minimum gradients before a single pipe is designed with it. Every function takes
`crit=DEFAULT` so a sensitivity run passes a different Criteria object instead of editing
code:  `smin_for(200, q, crit=replace(DEFAULT, TAU_PA=2.0))`.

----------------------------------------------------------------------------------------
THE EQUATION, AND WHY THE R-FORM IS THE GUIDELINE'S FORM

G203-p24 sec 4.2.1 prints Colebrook-White in the DIAMETER form, for a pipe running full:

    V = -2 sqrt(2 g D S) log10[ ks / (3.7 D) + 2.51 v / (D sqrt(2 g D S)) ]

Everything here is written in the HYDRAULIC RADIUS form:

    V = -2 sqrt(8 g R S) log10[ ks / (14.8 R) + 0.6275 v / (R sqrt(8 g R S)) ]

They are the same equation. Substitute R = D/4, which is what a full circular pipe has:
    8 g R S      = 8 g (D/4) S       = 2 g D S
    ks / (14.8R) = ks / (14.8 D / 4) = ks / (3.7 D)
    0.6275 v / (R sqrt(8gRS)) = 0.6275 v / ((D/4) sqrt(2gDS)) = 2.51 v / (D sqrt(2gDS))
Term for term. The R-form is used because a sewer runs PART FULL and the d/D limit
(G203-p27 Table 10) is a part-full criterion; the D-form cannot express it, and 0.65 of a
DN200 has R = 0.0536 m, not 0.05.

    ks = 1.5 mm, all sizes and materials      G203-p24 sec 4.2.1, repeated p28 sec 4.2.4
    v  = 1.141e-6 m2/s at 15 C, "conservative" G203-p25 Table 9

----------------------------------------------------------------------------------------
WHAT WAS CARRIED FROM W8/W11a, AND WHAT CHANGED

carried  the R-form, the circular-segment geometry, the bisection on d/D, the two-stage
         smax_for() search (a single bisection treats "cannot carry" and "too fast" as the
         same side of the interval and collapses to a garbage slope), and sizing on the
         true bore rather than the nominal size.

changed  (1) THE TABLE 11 GATE IS A HARD IMPORT-TIME ASSERTION, not a test file somebody
             may not run. `verify_table11()` recomputes all nine of the guideline's printed
             gradients from the equation and `_self_test()` fails if any is out by more
             than TABLE11_TOL. Measured deviation is printed by `python -m w11b.hydra`.
         (2) d/D comes from `crit.dod_limit(dn)` - one function, one threshold - instead of
             a local `dod_limit()` reaching for one of two exported constants. That reach
             is how W11a shipped 168 trunk reaches over the limit.
         (3) `size_pipe()` returns WHY, not just a size: (dn, y, v, sized_by). The
             philosophy prohibits "depth" as an answer for a diameter (G203-p29, and Ten
             States sec 33.43 independently), and a size with no recorded reason cannot be
             checked against that prohibition. `SIZED_BY` on the layer now has a source.
         (4) `clean_route()` names which of the two self-cleansing routes a reach takes.
             G203-p27 offers them as ALTERNATIVES ("Steeper gradient calculated based on
             self-cleansing velocity and minimum tractive force methodology shall be adopted
             as minimum pipe gradient"), and philosophy H5 requires the route recorded,
             because the tractive share of the network rests on an assumed tau.
         (5) `smin_velocity()` exists: the slope at which the reach ACTUALLY reaches
             0.75 m/s at its own peak flow and depth. Table 11 is the guideline's tabulated
             stand-in for it; on a lightly loaded pipe the two are far apart, and reporting
             Table 11 as "the velocity route" hides that.
         (6) Every function that can fail returns a SENTINEL with a name, never a number
             that looks plausible. INFEASIBLE, and (None, None) from solve_dod.

NOTHING HERE KNOWS ABOUT DEPTH. Cover, invert and the 12 m cap are levels, not hydraulics;
they live in the levelling stage and read `criteria.cover()`. A hydraulics module that can
see depth is a hydraulics module that will eventually size on it.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from .criteria import DEFAULT, Criteria, CriteriaError, replace

HYDRA_VERSION = "W11b-hydra-1.0"

# Sentinels. Named, so a caller cannot mistake one for a slope.
INFEASIBLE = -1.0        # no slope satisfies v <= V_MAX for this (dn, Q): the pipe is too
                         # small at every gradient. The caller must upsize, never clamp.

# How close the equation has to come to G203-p29 Table 11 for this module to be allowed to
# design anything. The table is printed to 2 decimal places in mm/m, so it carries its own
# rounding; 5 % is the tolerance W8 used and it is kept so the two iterations are comparable.
TABLE11_TOL = 0.05


# ======================================================================================
# Colebrook-White
# ======================================================================================

def v_cw_R(R: float, S: float, crit: Criteria = DEFAULT) -> float:
    """Mean velocity, m/s, from hydraulic radius R (m) and hydraulic gradient S (m/m).

    G203-p24 sec 4.2.1 in hydraulic-radius form - see the module header for the term-by-term
    substitution that shows it is the guideline's own equation. ks and nu come from the
    criteria and are never passed in loose."""
    if R <= 0 or S <= 0:
        return 0.0
    root = math.sqrt(8.0 * crit.G * R * S)
    arg = crit.KS / (14.8 * R) + 0.6275 * crit.NU / (R * root)
    return -2.0 * root * math.log10(arg)


def v_full(D: float, S: float, crit: Criteria = DEFAULT) -> float:
    """Full-bore velocity, m/s. D is the INTERNAL bore in metres, not the nominal size."""
    return v_cw_R(D / 4.0, S, crit)


def q_full(D: float, S: float, crit: Criteria = DEFAULT) -> float:
    """Full-bore discharge, m3/s. G203-p24: Qo = V A."""
    return v_full(D, S, crit) * math.pi * D * D / 4.0


def segment(D: float, y: float) -> Tuple[float, float]:
    """Circular-segment geometry at proportional depth y = d/D -> (flow area m2,
    hydraulic radius m). The part-full geometry behind G203-p27 Figure 2 / Table 10."""
    y = min(max(y, 1e-9), 1.0 - 1e-9)
    theta = 2.0 * math.acos(1.0 - 2.0 * y)
    A = D * D / 8.0 * (theta - math.sin(theta))
    P = D * theta / 2.0
    return A, A / P


def v_partial(D: float, S: float, y: float, crit: Criteria = DEFAULT) -> float:
    _A, R = segment(D, y)
    return v_cw_R(R, S, crit)


def q_partial(D: float, S: float, y: float, crit: Criteria = DEFAULT) -> float:
    A, R = segment(D, y)
    return v_cw_R(R, S, crit) * A


def solve_dod(D: float, S: float, Q: float,
              crit: Criteria = DEFAULT) -> Tuple[Optional[float], Optional[float]]:
    """(proportional depth y, velocity v) carrying Q m3/s in bore D at gradient S.

    Returns (0.0, 0.0) for Q <= 0 and (None, None) when the pipe cannot carry Q even at
    y = 0.95 - i.e. it is SURCHARGED, which is a design failure and not a large number.
    W10 shipped five surcharged trunk reaches; nothing in it distinguished "full" from
    "over capacity".

    Bisection on the monotonic branch y in (0, 0.95]. The capacity of a circular section
    peaks near y = 0.94-0.95 and falls again to full bore, so 0.95 is the top of the branch
    that can be inverted."""
    if Q <= 0:
        return 0.0, 0.0
    if D <= 0 or S <= 0:
        return None, None
    y_hi = 0.95
    if q_partial(D, S, y_hi, crit) < Q:
        return None, None
    lo, hi = 1e-6, y_hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if q_partial(D, S, mid, crit) < Q:
            lo = mid
        else:
            hi = mid
    y = 0.5 * (lo + hi)
    return y, v_partial(D, S, y, crit)


def pipe_state(dn: int, slope: float, q_peak: float,
               crit: Criteria = DEFAULT) -> Tuple[Optional[float], Optional[float]]:
    """(d/D, velocity) for a NOMINAL size at a laid gradient and a peak flow.

    THE CALL EVERY CONSUMER SHOULD USE. It converts DN to the true internal bore via
    criteria.internal_diameter() before solving; using DN/1000 as the bore overstates the
    capacity of every pipe to DN315 by about 12 % of area."""
    return solve_dod(crit.internal_diameter(dn), slope, q_peak, crit)


# ======================================================================================
# The two minimum-gradient routes. G203-p27: ALTERNATIVES, and the steeper governs.
# ======================================================================================

def smin_table11(dn: int, crit: Criteria = DEFAULT) -> float:
    """G203-p29 Table 11, m/m. The guideline's tabulated velocity route."""
    return crit.table11(dn)


def smin_velocity(dn: int, q_peak: float, crit: Criteria = DEFAULT) -> float:
    """The gradient at which THIS reach actually reaches 0.75 m/s at THIS peak flow, m/m.

    G203-p26 states the criterion as a VELOCITY - "the minimum velocity in the pipe shall be
    above 0.75 m/s at peak flow" - and Table 11 is its tabulation, computed at a reference
    condition the guideline does not state. On a DN200 carrying 2 L/s the two are far apart,
    and quoting Table 11 as "the velocity route" hides the gap.

    Returns INFEASIBLE when no gradient up to 50 % reaches 0.75 m/s - which is the ordinary
    case at the head of a run, and exactly the case G203-p27 sends to the tractive route."""
    if q_peak <= 0:
        return INFEASIBLE
    D = crit.internal_diameter(dn)
    lo, hi = 1e-6, 0.5
    y_hi, v_hi = solve_dod(D, hi, q_peak, crit)
    if y_hi is None or v_hi < crit.V_SELF_CLEANSING:
        return INFEASIBLE
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        y, v = solve_dod(D, mid, q_peak, crit)
        if y is None or v < crit.V_SELF_CLEANSING:
            lo = mid
        else:
            hi = mid
    return hi


def smin_tractive(q_peak: float, crit: Criteria = DEFAULT) -> float:
    """Tractive-force minimum gradient, m/m. G203-p27 sec 4.2.2.1:

        Smin = K tau^1.23 Q^-0.461,  K = 2.33e-4 for Q in m3/s

    read directly off the source PDF on 2026-09-03 (the equation is an embedded image with
    no text layer, which is how it was miscopied once before - the tau^1.23 term was dropped
    and the simplified form is only valid at tau = 1 Pa).

    Q is floored at crit.TRACTIVE_QMIN (1.5 L/s, Mara's own minimum design flow, an
    ASSUMPTION): unfloored, Smin -> infinity as Q -> 0 and the head of every run demands an
    unbuildable gradient.

    THIS FUNCTION IS THE ONE EXPOSED TO GAP-9. crit.TAU_PA has no guideline value; at 2.0 Pa
    every result here rises by 2^1.23 = 2.346x. See crit.tau_banner()."""
    q = max(float(q_peak), crit.TRACTIVE_QMIN)
    return crit.TRACTIVE_K_M3S * (crit.TAU_PA ** crit.TRACTIVE_TAU_EXP) * \
        (q ** crit.TRACTIVE_Q_EXP)


def smin_for(dn: int, q_peak: float, crit: Criteria = DEFAULT) -> float:
    """THE GOVERNING MINIMUM GRADIENT, m/m - the steeper of Table 11 and the tractive
    minimum at this reach's own peak flow.

    G203-p27, verbatim: "Steeper gradient calculated based on self-cleansing velocity and
    minimum tractive force methodology shall be adopted as minimum pipe gradient."

    Table 11 is used for the velocity route rather than smin_velocity() because Table 11 is
    what the guideline PRINTS and what a reviewer will check against. smin_velocity() is
    reported beside it, not substituted for it."""
    return max(smin_table11(dn, crit), smin_tractive(q_peak, crit))


def clean_route(dn: int, slope: float, q_peak: float,
                crit: Criteria = DEFAULT) -> str:
    """Which self-cleansing route this reach actually satisfies: "velocity", "tractive" or
    "neither". Philosophy H5 requires it recorded on every reach.

    "velocity" means the reach reaches 0.75 m/s at peak flow - the primary criterion
    (G203-p26). "tractive" means it does not, but the laid gradient meets the tractive
    minimum, which is the route G203-p27 provides for exactly this case. "neither" is a
    failure and must never be written away as a small number.

    The share of a network on "tractive" is a REPORTED figure, because it is the share
    resting on an assumed tau."""
    y, v = pipe_state(dn, slope, q_peak, crit)
    if y is not None and v is not None and v >= crit.V_SELF_CLEANSING:
        return "velocity"
    if slope >= smin_tractive(q_peak, crit) - 1e-12:
        return "tractive"
    return "neither"


def smax_for(dn: int, q_peak: float, crit: Criteria = DEFAULT) -> Optional[float]:
    """Gradient above which velocity at the design depth exceeds V_MAX (G203-p27 sec 4.2.2.2,
    p29 sec 4.3.2: 3.0 m/s).

    Returns None when no cap applies, a slope when one does, and INFEASIBLE when the pipe
    cannot carry q_peak at v <= 3.0 m/s at ANY gradient - in which case the caller must
    upsize, and must not clamp to a number.

    The feasible set {S : the pipe carries Q and v <= V_MAX} is an INTERVAL [S_cap, S*].
    A single bisection treats "cannot carry" (below S_cap) and "too fast" (above S*) as the
    same side and collapses to a garbage slope, so this finds S_cap first and then bisects
    [S_cap, S_HI]."""
    D = crit.internal_diameter(dn)
    S_HI = 0.5
    y_hi, v_hi = solve_dod(D, S_HI, q_peak, crit)
    if y_hi is None:
        return INFEASIBLE                      # cannot carry even at a 50 % gradient
    if v_hi <= crit.V_MAX:
        return None                            # never reaches the cap
    lo, hi = 1e-6, S_HI                        # capacity gradient first (monotone)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        y, _v = solve_dod(D, mid, q_peak, crit)
        if y is None:
            lo = mid
        else:
            hi = mid
    s_cap = hi
    y_c, v_c = solve_dod(D, s_cap, q_peak, crit)
    if y_c is None or v_c > crit.V_MAX:
        return INFEASIBLE                      # already too fast at the capacity limit
    lo, hi = s_cap, S_HI                       # v rises monotonically on the feasible side
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        y, v = solve_dod(D, mid, q_peak, crit)
        if y is None or v > crit.V_MAX:
            hi = mid
        else:
            lo = mid
    return lo


# ======================================================================================
# Sizing
# ======================================================================================

def dod_ok(dn: int, y: Optional[float], crit: Criteria = DEFAULT) -> bool:
    """Is this depth of flow within G203-p27 Table 10 for this diameter?
    y is None means surcharged, which is never ok."""
    return y is not None and y <= crit.dod_limit(dn) + 1e-12


def size_pipe(q_peak: float, slope: float, crit: Criteria = DEFAULT,
              dn_min: Optional[int] = None
              ) -> Tuple[Optional[int], Optional[float], Optional[float], str]:
    """Smallest DN that carries q_peak (m3/s) at the given LAID gradient within its own d/D
    limit, on the true internal bore.

    Returns (dn, d/D, velocity, sized_by). `sized_by` is the fourth element on purpose:
    the philosophy prohibits "depth" as an answer for a diameter (G203-p29 "Sewers shall not
    be oversized to facilitate flatter slopes", and Ten States sec 33.43 independently), and a
    size with no recorded reason cannot be checked against that prohibition.

        "minimum"  the smallest size in the series already carries it - the size is the
                   guideline's floor (G203-p22 Table 6), not a hydraulic answer
        "dod"      the depth-of-flow limit chose it (G203-p27 Table 10)
        "capacity" the pipe below could not pass the flow at all - surcharged
        "velocity" carried, within d/D, but the pipe below exceeded 3.0 m/s

    (None, None, None, "infeasible") when even the largest size in the series fails, which
    means the design needs a station or a different route, NOT a bigger number.
    """
    series = [d for d in crit.DN_SERIES if dn_min is None or d >= dn_min]
    if not series:
        raise CriteriaError(f"no diameter in the series at or above DN{dn_min}")
    prev_fail = ""
    for i, dn in enumerate(series):
        y, v = pipe_state(dn, slope, q_peak, crit)
        if y is None:
            prev_fail = "capacity"
            continue
        if not dod_ok(dn, y, crit):
            prev_fail = "dod"
            continue
        if v is not None and v > crit.V_MAX:
            prev_fail = "velocity"
            continue
        why = prev_fail if i > 0 and prev_fail else "minimum"
        return dn, y, v, why
    return None, None, None, "infeasible"


def retention_min(length_m: float, velocity_ms: Optional[float]) -> Optional[float]:
    """Retention time in a reach, minutes. Philosophy sec 6: septicity is a design driver and
    retention time per route is a reported number - long flat lightly-loaded runs at Omani
    temperatures are the H2S combination. None when the velocity is unknown or zero."""
    if not velocity_ms or velocity_ms <= 0:
        return None
    return float(length_m) / float(velocity_ms) / 60.0


# ======================================================================================
# THE GATE. Reproduce the guideline's own Table 11 before designing anything with this.
# ======================================================================================

def verify_table11(crit: Criteria = DEFAULT) -> List[Dict]:
    """Recompute every printed G203-p29 Table 11 gradient from the Colebrook-White equation
    at 0.75 m/s and compare.

    Table 11 is headed "The minimum sewer line gradient based on the Colebrook-White equation
    and acceptable self-cleansing velocity of 0.75 m/s". The guideline does not state the
    DEPTH OF FLOW the table was computed at, so the reproduction is run FULL BORE on the
    NOMINAL diameter - the reading that reproduces the printed numbers. That choice is
    recorded here rather than buried: the DESIGN runs on the true internal bore part full
    (internal_diameter, solve_dod); this function exists only to prove the equation and the
    constants are the guideline's.

    Returns one row per tabulated size with the printed value, the computed value and the
    relative error. `_self_test()` fails if any row exceeds TABLE11_TOL.
    """
    rows = []
    for dn, printed in sorted(crit.TABLE11.items()):
        D = dn / 1000.0                       # NOMINAL - see the docstring
        lo, hi = 1e-6, 0.2
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            if v_full(D, mid, crit) < crit.V_SELF_CLEANSING:
                lo = mid
            else:
                hi = mid
        computed = hi
        rows.append(dict(DN=dn,
                         printed_mm_m=printed * 1000.0,
                         computed_mm_m=computed * 1000.0,
                         rel_err=(computed - printed) / printed))
    return rows


def table11_report(crit: Criteria = DEFAULT) -> str:
    """The gate as a printable table, for the report and for a reviewer who wants to see
    that our equation is the guideline's equation."""
    rows = verify_table11(crit)
    out = ["G203-p29 Table 11 reproduced from Colebrook-White at 0.75 m/s "
           f"(ks = {crit.KS * 1000:g} mm, nu = {crit.NU:g} m2/s, full bore, nominal D)",
           f"{'DN':>6} {'printed':>10} {'computed':>10} {'error':>8}",
           f"{'mm':>6} {'mm/m':>10} {'mm/m':>10} {'%':>8}"]
    for r in rows:
        out.append(f"{r['DN']:>6} {r['printed_mm_m']:>10.2f} {r['computed_mm_m']:>10.3f} "
                   f"{r['rel_err'] * 100:>+8.2f}")
    worst = max(abs(r["rel_err"]) for r in rows)
    out.append(f"worst deviation {worst * 100:.2f} % against a gate of {TABLE11_TOL * 100:.0f} %")
    return "\n".join(out)


def crossover_q(dn: int, crit: Criteria = DEFAULT) -> Tuple[Optional[float], str]:
    """(peak flow m3/s, verdict) at which the tractive minimum falls to Table 11's value for
    this diameter - below it the tractive route sets the minimum gradient, above it Table 11
    does.

    Verdict is one of:
        "crossover"      the flow is real; tractive governs below it, Table 11 above
        "table11_always" tractive is already flatter than Table 11 at the Q floor, so
                         Table 11 sets the minimum at every flow this size will ever see
        "tractive_always" tractive is steeper than Table 11 right across the range

    Returned as a PAIR because a bare None cannot tell those last two apart, and they are
    opposite answers. This is the quantity the tau assumption moves: it is the boundary
    between the part of the network whose gradient comes from a printed guideline table and
    the part whose gradient comes from a number nobody has confirmed (GAP-9)."""
    t11 = smin_table11(dn, crit)
    lo, hi = crit.TRACTIVE_QMIN, 10.0
    if smin_tractive(lo, crit) <= t11:
        return None, "table11_always"
    if smin_tractive(hi, crit) > t11:
        return None, "tractive_always"
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if smin_tractive(mid, crit) > t11:
            lo = mid
        else:
            hi = mid
    return hi, "crossover"


def tractive_exposure_report(crit: Criteria = DEFAULT) -> str:
    """Which diameters have their minimum gradient set by the ASSUMED tau, and up to what
    flow. Printed on every deliverable that carries a gradient (engineer, 2026-09-03).

    NOTE the distinction this report exists to keep straight, because two different
    "tractive shares" have been quoted on this project and they answer different questions:
      * which route SETS THE MINIMUM GRADIENT      - this table, smin_for()
      * which route the laid reach SATISFIES       - clean_route(), CLEAN_BY on the layer
    A DN200 at a Table-11 gradient carrying 2 L/s is governed by Table 11 and satisfies
    neither velocity nor - unless the gradient happens to clear it - tractive."""
    lines = [f"Minimum-gradient route by diameter at tau = {crit.TAU_PA:g} Pa "
             "(G203-p27 sec 4.2.2.1; the steeper of the two governs)",
             f"{'DN':>6} {'Table 11':>10}  route",
             f"{'mm':>6} {'mm/m':>10}"]
    for dn in sorted(crit.TABLE11):
        q, verdict = crossover_q(dn, crit)
        if verdict == "crossover":
            note = (f"tractive below {q * 1000:.2f} L/s, Table 11 above")
        elif verdict == "table11_always":
            note = "Table 11 at every flow - tau does not reach this size"
        else:
            note = "tractive at every flow - fully exposed to tau"
        lines.append(f"{dn:>6} {crit.table11(dn) * 1000:>10.2f}  {note}")
    return "\n".join(lines)


# ======================================================================================
# Self-test. `python -m w11b.hydra`
# ======================================================================================

def _self_test(verbose: bool = True) -> None:
    C = DEFAULT

    # ---- THE GATE. If this fails, nothing downstream is allowed to design anything.
    rows = verify_table11(C)
    worst = max(abs(r["rel_err"]) for r in rows)
    assert worst <= TABLE11_TOL, (
        f"the Colebrook-White implementation does not reproduce G203-p29 Table 11: worst "
        f"deviation {worst * 100:.2f} % against a gate of {TABLE11_TOL * 100:.0f} %. "
        "Nothing downstream may design a pipe until this passes.")

    # ---- the R-form IS the guideline's D-form: at R = D/4 they must agree exactly
    for D in (0.2, 0.5, 1.2):
        for S in (0.001, 0.01):
            root = math.sqrt(2.0 * C.G * D * S)
            v_guideline = -2.0 * root * math.log10(
                C.KS / (3.7 * D) + 2.51 * C.NU / (D * root))
            assert abs(v_full(D, S, C) - v_guideline) < 1e-12, (D, S)

    # ---- geometry sanity: half full has R = D/4, and area is half the circle
    A, R = segment(1.0, 0.5)
    assert abs(A - math.pi / 8.0) < 1e-12 and abs(R - 0.25) < 1e-12

    # ---- solve_dod inverts q_partial
    D = C.internal_diameter(400)
    q = q_partial(D, 0.004, 0.42, C)
    y, v = solve_dod(D, 0.004, q, C)
    assert y is not None and abs(y - 0.42) < 1e-4, y

    # ---- surcharge returns a SENTINEL, not a big number
    y, v = pipe_state(200, 0.005, 0.5)          # 500 L/s down a DN200
    assert y is None and v is None

    # ---- the tractive equation is the one in the image: a power law in tau and in Q
    q = 0.010
    assert abs(smin_tractive(q, C)
               - C.TRACTIVE_K_M3S * C.TAU_PA ** 1.23 * q ** -0.461) < 1e-15
    tau2 = replace(C, TAU_PA=2.0)
    assert abs(smin_tractive(q, tau2) / smin_tractive(q, C) - 2.0 ** 1.23) < 1e-12
    # G203-p27 prints TWO K values for one constant and they do not agree exactly:
    # K_LS should be K_M3S x 1000^0.461 = 5.628e-3, and the guideline prints 5.5e-3.
    # MEASURED 2026-09-03: the printed pair is 2.27 % apart, so working in L/s gives
    # gradients 2.27 % FLATTER than working in m3/s. It is rounding in the source (2.33 and
    # 5.5 are 3 and 2 significant figures), not an error of ours - but it is a real 2.27 %
    # and W11b works consistently in m3/s with the 3-significant-figure constant.
    ratio = C.TRACTIVE_K_LS / (C.TRACTIVE_K_M3S * 1000.0 ** 0.461)
    assert abs(ratio - 1.0) < 0.03, (
        f"G203-p27's two K values are {(1 - ratio) * 100:.2f} % apart, which is more than "
        "source rounding explains - re-read the page before designing with either")

    # the depth-of-flow limit is the criteria's, and sizing honours it exactly at 350
    assert dod_ok(350, 0.65) and not dod_ok(351, 0.65)
    # and the Q floor bites
    assert smin_tractive(1e-9, C) == smin_tractive(C.TRACTIVE_QMIN, C)

    # ---- the governing minimum is the STEEPER of the two (G203-p27)
    for dn, q in ((200, 0.002), (200, 0.05), (900, 0.4)):
        assert smin_for(dn, q, C) == max(smin_table11(dn, C), smin_tractive(q, C))

    # ---- d/D comes from the criteria, at the Table 10 threshold, and is enforced in sizing
    dn, y, v, why = size_pipe(0.150, 0.0020, C)          # 150 L/s, flat
    assert dn is not None and y <= C.dod_limit(dn) + 1e-12, (dn, y)
    assert why in ("minimum", "dod", "capacity", "velocity"), why
    # a flow that needs a big pipe must reach the sizes above DN1200 rather than fail
    dn, y, v, why = size_pipe(1.400, 0.00075, C)         # 1,400 L/s at the Table 11 floor
    assert dn is not None and dn >= 1400, (dn, why)
    assert y <= C.dod_limit(dn) + 1e-12
    # and an impossible ask returns the named sentinel, not the largest pipe
    dn, y, v, why = size_pipe(50.0, 0.0005, C)
    assert dn is None and why == "infeasible"
    # dn_min is honoured (a reach may not shrink below its upstream size)
    dn, *_ = size_pipe(0.002, 0.005, C, dn_min=400)
    assert dn == 400

    # ---- smax_for distinguishes "no cap", "a cap" and "impossible"
    assert smax_for(1200, 0.005, C) is None                    # big pipe, small flow
    s = smax_for(200, 0.010, C)
    assert s is not None and s != INFEASIBLE and s > 0
    y, v = pipe_state(200, s, 0.010, C)
    assert v is not None and abs(v - C.V_MAX) < 0.05, v        # the cap is where v = 3.0
    assert smax_for(200, 2.0, C) == INFEASIBLE                 # 2 m3/s down a DN200

    # ---- clean_route names one of exactly three routes, and "neither" is reachable
    assert clean_route(200, 0.030, 0.030, C) == "velocity"
    assert clean_route(200, C.table11(200), 0.0005, C) == "tractive"
    assert clean_route(200, 0.0001, 0.0005, C) == "neither"

    # ---- retention time
    assert abs(retention_min(120.0, 1.0) - 2.0) < 1e-12
    assert retention_min(120.0, 0.0) is None

    if verbose:
        print(f"{HYDRA_VERSION}: self-test PASSED (gate: Table 11 reproduced to "
              f"{worst * 100:.2f} %)")
        print()
        print(table11_report(C))
        print()
        print(tractive_exposure_report(C))
        print()
        print("Same table at the NWS downside, tau = 2.0 Pa:")
        print(tractive_exposure_report(replace(C, TAU_PA=2.0)))


if __name__ == "__main__":          # pragma: no cover
    _self_test()
