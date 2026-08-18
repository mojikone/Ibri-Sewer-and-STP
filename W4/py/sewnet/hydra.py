"""sewnet.hydra — Colebrook-White pipe hydraulics (full and partial flow).

Design basis: G203-p24 (CW mandated), ks = 1.5 mm all sizes/materials (p24, p28),
nu = 1.141e-6 m2/s (p25). The Table-11 gate test (tests/test_hydra.py) proves this
module reproduces the guideline's own minimum gradients before anything is designed
with it — if that test fails, the module is wrong, not the table.

Geometry convention (review HYD-2): capacity, d/D and velocity are computed on the
TRUE internal bore via criteria.internal_diameter(dn) — PVC-U mains are OD-designated
(OD200 SN8 -> ID 188.2 mm), GRP nominal = ID. Table 11 itself was tabulated against
DN, so the gate test keeps D = DN/1000 when reproducing the guideline's table; every
design-facing helper here (smin/smax/size/state) uses the physical bore.
"""

import math
from . import criteria as C

INFEASIBLE = -1.0   # smax_for sentinel: no slope satisfies v <= V_MAX for this (dn, Q)
                    # (the pipe is capacity-bound above the velocity limit) -> upsize


def v_cw_R(R, S):
    """CW mean velocity (m/s) from hydraulic radius R (m) and slope S (m/m).
    R-form so the same law serves full and partial flow; for a full circular pipe
    R = D/4 and this reduces to the familiar D-form."""
    if R <= 0 or S <= 0:
        return 0.0
    root = math.sqrt(8.0 * C.G * R * S)
    arg = C.KS / (14.8 * R) + 0.6275 * C.NU / (R * root)
    return -2.0 * root * math.log10(arg)


def v_full(D, S):
    return v_cw_R(D / 4.0, S)


def q_full(D, S):
    return v_full(D, S) * math.pi * D * D / 4.0


def _segment(D, y):
    """Circular-segment geometry at proportional depth y = d/D. Returns (area, hydraulic radius)."""
    y = min(max(y, 1e-6), 1.0 - 1e-9)
    theta = 2.0 * math.acos(1.0 - 2.0 * y)
    A = D * D / 8.0 * (theta - math.sin(theta))
    P = D * theta / 2.0
    return A, A / P


def v_partial(D, S, y):
    A, R = _segment(D, y)
    return v_cw_R(R, S)


def q_partial(D, S, y):
    A, R = _segment(D, y)
    return v_cw_R(R, S) * A


def solve_dod(D, S, Q):
    """Proportional depth y and velocity carrying Q (m3/s) in pipe D (m) at slope S.
    Bisection on the monotonic branch y in (0, 0.95]; returns (y, v) or (None, None)
    if the pipe cannot carry Q even at y = 0.95 (capacity exceeded)."""
    if Q <= 0:
        return 0.0, 0.0
    y_hi = 0.95                      # capacity peak of a circular section ~0.94-0.95
    if q_partial(D, S, y_hi) < Q:
        return None, None
    lo, hi = 1e-4, y_hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if q_partial(D, S, mid) < Q:
            lo = mid
        else:
            hi = mid
    y = 0.5 * (lo + hi)
    return y, v_partial(D, S, y)


def smin_tractive(Q):
    """Tractive-force minimum gradient (G203-p27 §4.2.2.1, A9-corrected):
    Smin = 2.33e-4 * tau^1.23 * Q^-0.461, Q in m3/s, tau in Pa (GAP-9: tau = 1 Pa assumed).
    Q floored at Mara's 1.5 L/s minimum design flow (criteria.TRACTIVE_QMIN) — the
    formula's own literature convention; unfloored it demands unbounded slope as Q -> 0."""
    q = max(Q, C.TRACTIVE_QMIN)
    return C.TRACTIVE_K * (C.TAU_PA ** 1.23) * (q ** -0.461)


def smin_for(dn, q_peak):
    """Governing minimum gradient for a pipe: the steeper of Table 11 (0.75 m/s CW basis)
    and the tractive-force minimum at the actual peak flow (G203-p27: steeper governs)."""
    t11 = C.TABLE11.get(dn, C.TABLE11_FLOOR)
    return max(t11, smin_tractive(q_peak))


def smax_for(dn, q_peak):
    """Slope above which velocity at the design depth of flow exceeds V_MAX = 3.0 m/s
    (G203-p27/29). Returns None when no cap applies (v never reaches 3.0), a slope
    when a valid cap exists, or INFEASIBLE when the pipe cannot carry q_peak at
    v <= 3.0 at ANY slope (capacity-bound — caller must upsize).

    Review HYD-1 fix: the feasible set {S : pipe carries Q and v <= 3} is an interval
    [S_cap, S*]; the old single bisection treated 'cannot carry' and 'too fast' as the
    same side and collapsed. Now: (1) find S_cap (capacity bisection, monotone),
    (2) if v(S_cap) already > V_MAX -> INFEASIBLE, (3) else bisect [S_cap, S_HI] on v."""
    D = C.internal_diameter(dn)
    S_HI = 0.5
    y_hi, v_hi = solve_dod(D, S_HI, q_peak)
    if y_hi is None:
        return INFEASIBLE                     # cannot carry even at 50% slope
    if v_hi <= C.V_MAX:
        return None                           # never reaches 3 m/s — no cap
    # capacity slope: smallest S at which the pipe carries q_peak (y not None)
    lo, hi = 1e-5, S_HI
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        y, _v = solve_dod(D, mid, q_peak)
        if y is None:
            lo = mid
        else:
            hi = mid
    s_cap = hi
    y_c, v_c = solve_dod(D, s_cap, q_peak)
    if y_c is None or v_c > C.V_MAX:
        return INFEASIBLE                     # already too fast at the capacity limit
    lo, hi = s_cap, S_HI                      # v monotone rising in S on the feasible side
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        y, v = solve_dod(D, mid, q_peak)
        if y is None or v > C.V_MAX:
            hi = mid
        else:
            lo = mid
    return lo


def dod_limit(dn):
    return C.DOD_MAX_SMALL if dn <= C.DOD_DN_THRESHOLD else C.DOD_MAX_LARGE


def pipe_state(dn, slope, q_peak):
    """(y, v) at the TRUE internal bore — the one call every consumer should use."""
    return solve_dod(C.internal_diameter(dn), slope, q_peak)


def size_pipe(q_peak, slope):
    """Smallest DN in the series carrying q_peak (m3/s) at the given laid slope within
    its d/D limit (G203-p27 Tab 10), evaluated on the true internal bore. Returns
    (dn, y, v) or (None, None, None) if even the largest DN fails (caller must
    flatten/split upstream — reported, never silent)."""
    for dn in C.DN_SERIES:
        y, v = pipe_state(dn, slope, q_peak)
        if y is not None and y <= dod_limit(dn):
            return dn, y, v
    return None, None, None
