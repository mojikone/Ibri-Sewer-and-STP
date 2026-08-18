"""sewnet.hydra — Colebrook-White pipe hydraulics (full and partial flow).

Deliberately PLAIN FUNCTIONS, not a class: this is pure maths with no state, it is the
most heavily tested part of the pipeline, and the Table-11 gate (tests/test_hydra.py)
proves it reproduces the guideline's own minimum gradients before anything is designed
with it. Every function takes an optional `crit` so a sensitivity run (tau = 2 Pa, say)
passes a different Criteria object instead of editing code.

Design basis: G203-p24 (CW mandated), ks = 1.5 mm (p24, p28), nu = 1.141e-6 m2/s (p25).
Geometry: capacity, d/D and velocity are computed on the TRUE internal bore via
criteria.internal_diameter() (review HYD-2); Table 11 itself was tabulated against DN,
so the gate keeps D = DN/1000 when reproducing the guideline table.
"""

import math

from .criteria import DEFAULT

INFEASIBLE = -1.0   # smax_for sentinel: no slope satisfies v <= V_MAX for this (dn, Q)


def v_cw_R(R, S, crit=DEFAULT):
    """CW mean velocity (m/s) from hydraulic radius R (m) and slope S (m/m).
    R-form so the same law serves full and partial flow; for a full circular pipe
    R = D/4 and this reduces to the familiar D-form."""
    if R <= 0 or S <= 0:
        return 0.0
    root = math.sqrt(8.0 * crit.G * R * S)
    arg = crit.KS / (14.8 * R) + 0.6275 * crit.NU / (R * root)
    return -2.0 * root * math.log10(arg)


def v_full(D, S, crit=DEFAULT):
    return v_cw_R(D / 4.0, S, crit)


def q_full(D, S, crit=DEFAULT):
    return v_full(D, S, crit) * math.pi * D * D / 4.0


def _segment(D, y):
    """Circular-segment geometry at proportional depth y = d/D -> (area, hydraulic radius)."""
    y = min(max(y, 1e-6), 1.0 - 1e-9)
    theta = 2.0 * math.acos(1.0 - 2.0 * y)
    A = D * D / 8.0 * (theta - math.sin(theta))
    P = D * theta / 2.0
    return A, A / P


def v_partial(D, S, y, crit=DEFAULT):
    A, R = _segment(D, y)
    return v_cw_R(R, S, crit)


def q_partial(D, S, y, crit=DEFAULT):
    A, R = _segment(D, y)
    return v_cw_R(R, S, crit) * A


def solve_dod(D, S, Q, crit=DEFAULT):
    """Proportional depth y and velocity carrying Q (m3/s) in bore D (m) at slope S.
    Bisection on the monotonic branch y in (0, 0.95]; (None, None) when the pipe cannot
    carry Q even at y = 0.95 (capacity exceeded)."""
    if Q <= 0:
        return 0.0, 0.0
    y_hi = 0.95                      # capacity peak of a circular section ~0.94-0.95
    if q_partial(D, S, y_hi, crit) < Q:
        return None, None
    lo, hi = 1e-4, y_hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if q_partial(D, S, mid, crit) < Q:
            lo = mid
        else:
            hi = mid
    y = 0.5 * (lo + hi)
    return y, v_partial(D, S, y, crit)


def pipe_state(dn, slope, q_peak, crit=DEFAULT):
    """(y, v) at the TRUE internal bore — the call every consumer should use."""
    return solve_dod(crit.internal_diameter(dn), slope, q_peak, crit)


def smin_tractive(Q, crit=DEFAULT):
    """Tractive-force minimum gradient (G203-p27 4.2.2.1, A9-corrected):
    Smin = 2.33e-4 * tau^1.23 * Q^-0.461, Q in m3/s, tau in Pa (GAP-9: tau = 1 Pa).
    Q floored at Mara's 1.5 L/s minimum design flow — the formula's own convention;
    unfloored it demands unbounded slope as Q -> 0."""
    q = max(Q, crit.TRACTIVE_QMIN)
    return crit.TRACTIVE_K * (crit.TAU_PA ** 1.23) * (q ** -0.461)


def smin_for(dn, q_peak, crit=DEFAULT):
    """Governing minimum gradient: the steeper of Table 11 (0.75 m/s CW basis) and the
    tractive-force minimum at the actual peak flow (G203-p27: steeper governs)."""
    t11 = crit.TABLE11.get(dn, crit.TABLE11_FLOOR)
    return max(t11, smin_tractive(q_peak, crit))


def smax_for(dn, q_peak, crit=DEFAULT):
    """Slope above which velocity at the design depth exceeds V_MAX (G203-p27/29).
    None when no cap applies, a slope when a valid cap exists, or INFEASIBLE when the
    pipe cannot carry q_peak at v <= V_MAX at ANY slope (caller must upsize).

    Review HYD-1: the feasible set {S : pipe carries Q and v <= 3} is an interval
    [S_cap, S*]; a single bisection treated 'cannot carry' and 'too fast' as the same
    side and collapsed to a garbage slope. Now: find S_cap, then bisect [S_cap, S_HI]."""
    D = crit.internal_diameter(dn)
    S_HI = 0.5
    y_hi, v_hi = solve_dod(D, S_HI, q_peak, crit)
    if y_hi is None:
        return INFEASIBLE                     # cannot carry even at 50 % slope
    if v_hi <= crit.V_MAX:
        return None                           # never reaches the cap
    lo, hi = 1e-5, S_HI                       # capacity slope first (monotone)
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
        return INFEASIBLE                     # already too fast at the capacity limit
    lo, hi = s_cap, S_HI                      # v rises monotonically on the feasible side
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        y, v = solve_dod(D, mid, q_peak, crit)
        if y is None or v > crit.V_MAX:
            hi = mid
        else:
            lo = mid
    return lo


def dod_limit(dn, crit=DEFAULT):
    return crit.DOD_MAX_SMALL if dn <= crit.DOD_DN_THRESHOLD else crit.DOD_MAX_LARGE


def size_pipe(q_peak, slope, crit=DEFAULT):
    """Smallest DN carrying q_peak (m3/s) at the given laid slope within its d/D limit
    (G203-p27 Tab 10), on the true bore. (None, None, None) if even the largest fails."""
    for dn in crit.DN_SERIES:
        y, v = pipe_state(dn, slope, q_peak, crit)
        if y is not None and y <= dod_limit(dn, crit):
            return dn, y, v
    return None, None, None
