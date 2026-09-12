"""sewnet.hydraulics — Colebrook-White for a circular pipe, full or part-full (stage B,
2026-09-12, engineer: the guideline's basis, ks = 1.5 mm for every size and material, G203
p24 and p28; kinematic viscosity 1.141e-6 m2/s at 15 degrees, Table 9 p25).

Everything here is in metres, seconds and m3/s. The pipe form of Colebrook-White is used
with the hydraulic diameter 4R, so a full pipe reads exactly as the textbook formula and a
part-full one reads through its wetted section.
"""
import math

G = 9.81
KS = 0.0015          # m, G203 p28
NU = 1.141e-6        # m2/s at 15 degrees, G203 Table 9
V_MAX = 3.0          # m/s at the design depth of flow, G203 p27
Y_MAX_SMALL = 0.65   # d/D up to DN350, G203 Table 10
Y_MAX_LARGE = 0.50   # d/D above DN350
Y_PEAK = 0.94        # the depth ratio where a circular pipe's flow is greatest

# G203 p29 Table 11: minimum gradient (m/m) by nominal diameter
T11 = {200: 0.005, 250: 0.00375, 315: 0.0027, 400: 0.00205, 500: 0.00155, 600: 0.00125,
       700: 0.001, 800: 0.00085, 900: 0.00075}
DN_LIST = sorted(T11)


def bore(dn):
    """Inside diameter, m: uPVC to DN315 (nominal outside diameter, wall 1/34 of it), GRP
    and larger by nominal inside diameter."""
    return dn / 1000.0 * (1.0 - 2.0 / 34.0) if dn <= 315 else dn / 1000.0


def outside(dn):
    """Outside diameter, m, for the cover to the crown."""
    return dn / 1000.0 if dn <= 315 else dn / 1000.0 + 0.02


def y_max(dn):
    return Y_MAX_SMALL if dn <= 350 else Y_MAX_LARGE


def section(D, y):
    """Wetted area and perimeter of a circular pipe at depth ratio y = d/D."""
    y = min(max(y, 1e-6), 1.0)
    th = 2.0 * math.acos(1.0 - 2.0 * y)
    return D * D / 8.0 * (th - math.sin(th)), D * th / 2.0


def velocity(D, S, y, ks=KS, nu=NU):
    """Colebrook-White velocity, m/s, at depth ratio y and gradient S."""
    if S <= 0.0:
        return 0.0
    A, P = section(D, y)
    dh = 4.0 * A / P
    root = math.sqrt(2.0 * G * dh * S)
    return -2.0 * root * math.log10(ks / (3.7 * dh) + 2.51 * nu / (dh * root))


def flow(D, S, y, ks=KS, nu=NU):
    A, _ = section(D, y)
    return velocity(D, S, y, ks, nu) * A


def capacity(dn, S, ks=KS, nu=NU):
    """Design capacity, m3/s, at gradient S and the guideline's depth ratio (Table 10)."""
    return flow(bore(dn), S, y_max(dn), ks, nu)


def depth_ratio(dn, S, q, ks=KS, nu=NU):
    """(d/D, velocity) of flow q at gradient S. Past the pipe's greatest part-full flow it is
    read as full, at the full-bore velocity of that flow."""
    D = bore(dn)
    if q <= 0.0 or S <= 0.0:
        return 0.0, 0.0
    if q >= flow(D, S, Y_PEAK, ks, nu):
        A, _ = section(D, 1.0)
        return 1.0, q / A
    lo, hi = 1e-4, Y_PEAK
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if flow(D, S, mid, ks, nu) < q:
            lo = mid
        else:
            hi = mid
    y = 0.5 * (lo + hi)
    return y, velocity(D, S, y, ks, nu)


def size_for(q, ks=KS, nu=NU):
    """The smallest size that carries q, m3/s, at its own Table 11 minimum gradient."""
    for dn in DN_LIST:
        if capacity(dn, T11[dn], ks, nu) >= q:
            return dn
    return DN_LIST[-1]


def slope_for_velocity(dn, q, v_target, ks=KS, nu=NU, lo=1e-4, hi=2.0):
    """The gradient at which flow q runs at v_target; infinite with no flow."""
    if q <= 0.0:
        return float("inf")
    if depth_ratio(dn, hi, q, ks, nu)[1] < v_target:
        return float("inf")
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if depth_ratio(dn, mid, q, ks, nu)[1] < v_target:
            lo = mid
        else:
            hi = mid
    return hi
