"""Culverts (v7, 2026-11-24): a conduit marked as a culvert gets the headwater it needs at its flow, under inlet control
(FHWA HDS-5, by its inlet type) and outlet control (full-barrel energy loss), and the larger governs; the storm run gives
SWMM the same inlet type (SWMM's culvert code), so SWMM checks inlet control in every time step.

Inlet types and constants: EPA SWMM 5.2's culvert.c (public domain), the 57 HDS-5 inlet types with their equation form
and K, M, c, Y; the equations as SWMM evaluates them, in US customary units (Ku = 1), converted here:
  unsubmerged (head below 0.95 D): Form 1  HW/D = Hc/D + K (Q / (A D^0.5))^M + scf   (Hc: specific head at critical depth)
                                   Form 2  HW/D = K (Q / (A D^0.5))^M
  submerged (head above D (16 c + Y - scf)): HW/D = c (Q / (A D^0.5))^2 + Y - scf
  between: linear in head; scf = 0.5 S (-7 S for the mitered inlets, codes 5, 37 and 46).
Outlet control (HDS-5): HW = ho + (1 + Ke + 2 g n^2 L / R^(4/3)) V^2 / 2g - L S, ho = the larger of the tailwater depth and
(dc + D) / 2, the barrel full. SewerGEMS holds a culvert as a conduit with Is Culvert?, Ke, Kr and its headwall's inlet
description (whose SWMM culvert code names the same row)."""
import math
import numpy as np

FT, G_US, G = 0.3048, 32.174, 9.81
# code: (form, K, M, c, Y, description)  (SWMM 5.2 culvert.c Params, codes 1-57)
TABLE = {
    1: (1, 0.0098, 2.00, 0.0398, 0.67, "Circular concrete, square edge with headwall"),
    2: (1, 0.0018, 2.00, 0.0292, 0.74, "Circular concrete, groove end with headwall"),
    3: (1, 0.0045, 2.00, 0.0317, 0.69, "Circular concrete, groove end projecting"),
    4: (1, 0.0078, 2.00, 0.0379, 0.69, "Circular CMP, headwall"),
    5: (1, 0.0210, 1.33, 0.0463, 0.75, "Circular CMP, mitered to slope"),
    6: (1, 0.0340, 1.50, 0.0553, 0.54, "Circular CMP, projecting"),
    7: (1, 0.0018, 2.50, 0.0300, 0.74, "Circular, beveled ring, 45 deg bevels"),
    8: (1, 0.0018, 2.50, 0.0243, 0.83, "Circular, beveled ring, 33.7 deg bevels"),
    9: (1, 0.026, 1.0, 0.0347, 0.81, "Box, flared wingwalls 30-75 deg"),
    10: (1, 0.061, 0.75, 0.0400, 0.80, "Box, flared wingwalls 90 or 15 deg"),
    11: (1, 0.061, 0.75, 0.0423, 0.82, "Box, flared wingwalls 0 deg (straight sides)"),
    12: (2, 0.510, 0.667, 0.0309, 0.80, "Box, 45 deg flare, 0.43D top edge bevel"),
    13: (2, 0.486, 0.667, 0.0249, 0.83, "Box, 18-33.7 deg flare, 0.083D top edge bevel"),
    14: (2, 0.515, 0.667, 0.0375, 0.79, "Box, 90 deg headwall, chamfered 3/4 in"),
    15: (2, 0.495, 0.667, 0.0314, 0.82, "Box, 90 deg headwall, beveled 1/2 in/ft at 45 deg"),
    16: (2, 0.486, 0.667, 0.0252, 0.865, "Box, 90 deg headwall, beveled 1 in/ft at 33.7 deg"),
    17: (2, 0.545, 0.667, 0.04505, 0.73, "Box, 3/4 in chamfer, 45 deg skewed headwall"),
    18: (2, 0.533, 0.667, 0.0425, 0.705, "Box, 3/4 in chamfer, 30 deg skewed headwall"),
    19: (2, 0.522, 0.667, 0.0402, 0.68, "Box, 3/4 in chamfer, 15 deg skewed headwall"),
    20: (2, 0.498, 0.667, 0.0327, 0.75, "Box, 45 deg beveled edge, 10-45 deg skewed headwall"),
    21: (2, 0.497, 0.667, 0.0339, 0.803, "Box, non-offset flared wingwalls 45 deg, 3/4 in chamfer"),
    22: (2, 0.493, 0.667, 0.0361, 0.806, "Box, non-offset flared wingwalls 18.4 deg, 3/4 in chamfer"),
    23: (2, 0.495, 0.667, 0.0386, 0.71, "Box, non-offset flared wingwalls 18.4 deg, 30 deg skew"),
    24: (2, 0.497, 0.667, 0.0302, 0.835, "Box, offset flared wingwalls 45 deg, 0.042D top bevel"),
    25: (2, 0.495, 0.667, 0.0252, 0.881, "Box, offset flared wingwalls 33.7 deg, 0.083D top bevel"),
    26: (2, 0.493, 0.667, 0.0227, 0.887, "Box, offset flared wingwalls 18.4 deg, 0.083D top bevel"),
    27: (1, 0.0083, 2.00, 0.0379, 0.69, "Corrugated metal box, 90 deg headwall"),
    28: (1, 0.0145, 1.75, 0.0419, 0.64, "Corrugated metal box, thick wall projecting"),
    29: (1, 0.0340, 1.50, 0.0496, 0.57, "Corrugated metal box, thin wall projecting"),
    30: (1, 0.0100, 2.00, 0.0398, 0.67, "Horizontal ellipse concrete, square edge with headwall"),
    31: (1, 0.0018, 2.50, 0.0292, 0.74, "Horizontal ellipse concrete, grooved end with headwall"),
    32: (1, 0.0045, 2.00, 0.0317, 0.69, "Horizontal ellipse concrete, grooved end projecting"),
    33: (1, 0.0100, 2.00, 0.0398, 0.67, "Vertical ellipse concrete, square edge with headwall"),
    34: (1, 0.0018, 2.50, 0.0292, 0.74, "Vertical ellipse concrete, grooved end with headwall"),
    35: (1, 0.0095, 2.00, 0.0317, 0.69, "Vertical ellipse concrete, grooved end projecting"),
    36: (1, 0.0083, 2.00, 0.0379, 0.69, "Pipe arch 18 in corner radius CMP, 90 deg headwall"),
    37: (1, 0.0300, 1.00, 0.0463, 0.75, "Pipe arch 18 in corner radius CMP, mitered to slope"),
    38: (1, 0.0340, 1.50, 0.0496, 0.57, "Pipe arch 18 in corner radius CMP, projecting"),
    39: (1, 0.0300, 1.50, 0.0496, 0.57, "Pipe arch 18 in corner radius CMP, projecting (2)"),
    40: (1, 0.0088, 2.00, 0.0368, 0.68, "Pipe arch 18 in corner radius CMP, no bevels"),
    41: (1, 0.0030, 2.00, 0.0269, 0.77, "Pipe arch 18 in corner radius CMP, 33.7 deg bevels"),
    42: (1, 0.0300, 1.50, 0.0496, 0.57, "Pipe arch 31 in corner radius CMP, projecting"),
    43: (1, 0.0088, 2.00, 0.0368, 0.68, "Pipe arch 31 in corner radius CMP, no bevels"),
    44: (1, 0.0030, 2.00, 0.0269, 0.77, "Pipe arch 31 in corner radius CMP, 33.7 deg bevels"),
    45: (1, 0.0083, 2.00, 0.0379, 0.69, "Arch CMP, 90 deg headwall"),
    46: (1, 0.0300, 1.00, 0.0473, 0.75, "Arch CMP, mitered to slope"),
    47: (1, 0.0340, 1.50, 0.0496, 0.57, "Arch CMP, thin wall projecting"),
    48: (2, 0.534, 0.555, 0.0196, 0.90, "Circular, smooth tapered inlet throat"),
    49: (2, 0.519, 0.640, 0.0210, 0.90, "Circular, rough tapered inlet throat"),
    50: (2, 0.536, 0.622, 0.0368, 0.83, "Elliptical inlet face, tapered inlet, beveled edges"),
    51: (2, 0.5035, 0.719, 0.0478, 0.80, "Elliptical inlet face, tapered inlet, square edges"),
    52: (2, 0.547, 0.800, 0.0598, 0.75, "Elliptical inlet face, tapered inlet, thin edge projecting"),
    53: (2, 0.475, 0.667, 0.0179, 0.97, "Rectangular, tapered inlet throat"),
    54: (2, 0.560, 0.667, 0.0446, 0.85, "Rectangular concrete, side tapered, less favourable edges"),
    55: (2, 0.560, 0.667, 0.0378, 0.87, "Rectangular concrete, side tapered, more favourable edges"),
    56: (2, 0.500, 0.667, 0.0446, 0.65, "Rectangular concrete, slope tapered, less favourable edges"),
    57: (2, 0.500, 0.667, 0.0378, 0.71, "Rectangular concrete, slope tapered, more favourable edges"),
}


def _area_width(shape, D, B, y):
    """Flow area and top width at depth y (ft): a circle of diameter D, or a box D high and B wide."""
    if shape == "box": return B * y, B
    y = min(max(y, 1e-9), D * 0.999999); r = D / 2; th = 2 * math.acos(1 - y / r)
    return r * r * (th - math.sin(th)) / 2, 2 * math.sqrt(y * (D - y))


def _inlet_q(h, code, shape, D, B, S):
    """SWMM's inlet-control flow (cfs) at head h (ft) above the upstream invert."""
    form, K, M, c, Y, _ = TABLE[code]
    scf = -7.0 * S if code in (5, 37, 46) else 0.5 * S
    A = _area_width(shape, D, B, D)[0] if shape == "box" else math.pi * D * D / 4
    AD = A * math.sqrt(D)

    def unsub(hh):
        if form == 2: return AD * (hh / D / K) ** (1.0 / M)
        hplus = hh / D + scf                                    # Form 1: solve for the critical depth that balances
        lo, hi = 1e-6 * D, min(hh, 0.999 * D)
        def f(yc):
            a, w = _area_width(shape, D, B, yc); yh = a / w; qc = a * math.sqrt(G_US * yh)
            return hplus - yc / D - yh / 2.0 / D - K * (qc / AD) ** M, qc
        if f(hi)[0] > 0: return f(hi)[1]
        for _ in range(80):
            m = (lo + hi) / 2
            if f(m)[0] > 0: lo = m
            else: hi = m
        return f((lo + hi) / 2)[1]

    def sub(hh):
        arg = (hh / D - Y + scf) / c
        return AD * math.sqrt(arg) if arg > 0 else 0.0
    h1, h2 = 0.95 * D, D * (16.0 * c + Y - scf)
    if h >= h2: return sub(h)
    if h <= h1: return unsub(h)
    q1, q2 = unsub(h1), sub(h2)
    return q1 + (q2 - q1) * (h - h1) / (h2 - h1)


def inlet_headwater(q_m3s, code, shape, D_m, B_m=None, S=0.0):
    """The headwater depth (m above the upstream invert) a culvert needs to pass Q under inlet control."""
    if q_m3s <= 0: return 0.0
    q = q_m3s / FT ** 3; D = D_m / FT; B = (B_m or D_m) / FT
    lo, hi = 1e-6, D
    while _inlet_q(hi, code, shape, D, B, S) < q and hi < 200 * D: hi *= 1.5
    for _ in range(80):
        m = (lo + hi) / 2
        if _inlet_q(m, code, shape, D, B, S) < q: lo = m
        else: hi = m
    return (lo + hi) / 2 * FT


def critical_depth(q, shape, D, B=None):
    """Critical depth (m) of Q (m3/s) in a circle of diameter D or a box D high and B wide."""
    if q <= 0: return 0.0
    lo, hi = 1e-6, 0.999 * D
    for _ in range(80):
        m = (lo + hi) / 2; a, w = _area_width(shape, D, B or D, m)
        if a ** 3 / w * G < q * q: lo = m
        else: hi = m
    return (lo + hi) / 2


def outlet_headwater(q, shape, D, B, L, S, n, ke, tailwater=None):
    """HDS-5 outlet control, the barrel full: HW = ho + (1 + Ke + 2 g n^2 L / R^(4/3)) V^2 / 2g - L S (m)."""
    if q <= 0: return 0.0
    A = (B or D) * D if shape == "box" else math.pi * D * D / 4
    P = 2 * ((B or D) + D) if shape == "box" else math.pi * D
    R = A / P; V = q / A
    H = (1.0 + ke + 2 * G * n * n * L / R ** (4.0 / 3.0)) * V * V / (2 * G)
    ho = max(tailwater or 0.0, (min(critical_depth(q, shape, D, B), D) + D) / 2)
    return ho + H - L * S


def check(q, code, shape, D, B, L, S, n, ke=0.0, tailwater=None):
    """The headwater (m above the upstream invert) and which control governs."""
    hi = inlet_headwater(q, code, shape, D, B, S); ho = outlet_headwater(q, shape, D, B, L, S, n, ke, tailwater)
    return dict(hw_m=max(hi, ho), hw_inlet_m=hi, hw_outlet_m=ho, control="inlet" if hi >= ho else "outlet")
