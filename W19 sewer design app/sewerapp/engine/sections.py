"""Cross-sections other than the circle: a closed box, an open rectangle and an open trapezoid. Textbook open-channel
hydraulics (Manning's equation; critical depth where Q^2 T / (g A^3) = 1), the relations EPA SWMM 5 uses for its
RECT_CLOSED, RECT_OPEN and TRAPEZOIDAL shapes. Clean room: nothing here comes from SewerGEMS.

A section is {shape, rise_m, span_m, bottom_m, z_left, z_right, n, barrels}: `barrels` identical barrels side by side
(default 1) share the flow equally, as SWMM's barrels do:
  box        closed rectangle: rise (height) x span (width); flows full above the rise (surcharged)
  rect_open  open rectangle: span wide, rise = bank height (overtopped above it)
  trapezoid  open trapezoid: bottom width, side slopes z (horizontal per vertical) left and right, rise = bank height
All lengths in metres, flows in m3/s, n Manning's (s/m^1/3). Functions take numpy arrays, one value per conduit."""
import numpy as np

SHAPES = ("box", "rect_open", "trapezoid")
G = 9.81


def _arr(sec, key, n, default=0.0):
    return np.array([float(s.get(key, default) if s.get(key, default) is not None else default) for s in sec]) if n else np.zeros(0)


def unpack(sections):
    """A list of section dicts as arrays: shape code (0 box, 1 open rectangle, 2 trapezoid), rise, span/bottom, zl, zr, n."""
    k = len(sections)
    code = np.array([SHAPES.index(s["shape"]) for s in sections]) if k else np.zeros(0, int)
    rise = _arr(sections, "rise_m", k); span = _arr(sections, "span_m", k)
    bottom = np.where(code == 2, _arr(sections, "bottom_m", k), span)
    zl = np.where(code == 2, _arr(sections, "z_left", k), 0.0); zr = np.where(code == 2, _arr(sections, "z_right", k), 0.0)
    n = _arr(sections, "n", k, 0.013)
    return code, rise, bottom, zl, zr, np.where(n > 0, n, 0.013)


def barrels(sections):
    """The number of identical barrels of each section (at least 1)."""
    return np.array([max(int(s.get("barrels") or 1), 1) for s in sections]) if len(sections) else np.zeros(0, int)


def geometry(code, y, rise, bottom, zl, zr, full=False):
    """Area, wetted perimeter and top width at depth y (a closed box flowing full when `full`)."""
    sl = np.sqrt(1 + zl ** 2) + np.sqrt(1 + zr ** 2)
    A = bottom * y + 0.5 * (zl + zr) * y ** 2
    P = bottom + y * sl
    T = bottom + (zl + zr) * y
    if full: P = np.where(code == 0, 2 * (bottom + rise), P)
    return A, P, T


def manning(A, P, S, n):
    R = np.where(P > 0, A / np.where(P > 0, P, 1), 0.0)
    return np.where(S > 0, A * R ** (2 / 3) * np.sqrt(np.maximum(S, 0)) / n, 0.0)


def full_capacity(code, rise, bottom, zl, zr, n, S):
    """Manning's flow with the section full: a box at its full perimeter, an open section to the bank (rise)."""
    A, P, _ = geometry(code, rise, rise, bottom, zl, zr, full=True)
    return manning(A, P, S, n)


def normal_depth(q, S, code, rise, bottom, zl, zr, n, iters=60):
    """Depth at which Manning's equation carries q (open sections may rise above their bank: overtopped). Returns
    (depth, area, full): a box that cannot carry q with a free surface flows full (depth = rise, area = full area)."""
    q = np.asarray(q, float); S = np.asarray(S, float)
    top = np.where(code == 0, rise * (1 - 1e-9), np.maximum(rise, 1e-6) * 20)        # an open channel may overtop
    A_t, P_t, _ = geometry(code, top, rise, bottom, zl, zr)
    qmax = manning(A_t, P_t, S, n)
    full = (code == 0) & (q > qmax)
    lo, hi = np.zeros_like(q), top.copy()
    for _ in range(iters):
        mid = 0.5 * (lo + hi); A, P, _ = geometry(code, mid, rise, bottom, zl, zr)
        big = manning(A, P, S, n) >= q
        hi = np.where(big, mid, hi); lo = np.where(big, lo, mid)
    y = np.where(full, rise, 0.5 * (lo + hi))
    y = np.where((q <= 0) | (S <= 0), np.where(q > 0, np.nan, 0.0), y)
    A, _, _ = geometry(code, np.nan_to_num(y), rise, bottom, zl, zr, full=False)
    return y, A, full


def critical_depth(q, code, rise, bottom, zl, zr, iters=60):
    q = np.asarray(q, float)
    lo, hi = np.zeros_like(q), np.maximum(rise, 1e-6) * 20
    for _ in range(iters):
        mid = 0.5 * (lo + hi); A, _, T = geometry(code, mid, rise, bottom, zl, zr)
        sup = q ** 2 * T >= G * A ** 3                                                 # still supercritical below
        lo = np.where(sup, mid, lo); hi = np.where(sup, hi, mid)
    yc = 0.5 * (lo + hi)
    return np.where(code == 0, np.minimum(yc, rise), yc)


def label(s):
    k = int(s.get("barrels") or 1); pre = f"{k} x " if k > 1 else ""
    if s["shape"] == "box": return f"{pre}Box {s.get('span_m', 0):g} x {s.get('rise_m', 0):g} m"
    if s["shape"] == "rect_open": return f"{pre}Open rect. {s.get('span_m', 0):g} m, bank {s.get('rise_m', 0):g} m"
    return f"{pre}Trapezoid {s.get('bottom_m', 0):g} m, {s.get('z_left', 0):g}:{s.get('z_right', 0):g}, bank {s.get('rise_m', 0):g} m"
