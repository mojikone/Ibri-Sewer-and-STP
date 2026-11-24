"""Catch basin inlets and gutters (v7, 2026-11-24): what an inlet captures of the surface flow reaching it, and where the
rest goes, the way SewerGEMS's catch basin does it (docs/INLETS_HEC22.md has every equation with its HEC-22 number).

Inlet types (SewerGEMS's): full capture (all of it), percent capture, maximum capacity (up to a flow), inflow-capture
curve, and a catalogue inlet computed by FHWA HEC-22 (3rd ed., chapter 4): grate, curb opening, combination or slotted,
on grade or in a sag, in a conventional (optionally depressed), V-shaped or trapezoidal (ditch) gutter.

Gutter flow is Izzard's strip form of Manning, Q = (SL^0.5 / n) ∫ y(x)^(5/3) dx across the wetted width (Eq. 4-2 for a
triangle, and the same integral handles the depressed, V-shaped sections and any grate width), Manning on the whole
section for a ditch. A grate's splash-over velocity uses SWMM 5.2's cubic fits of HEC-22 Chart 5 (public domain,
src/solver/inlet.c), so the steady run and the storm run agree. Clogging reduces what the inlet captures by its factor.

Units: m, m3/s inside; the results in L/s and m."""
import math
import numpy as np

G = 9.81
FT = 0.3048
# splash-over velocity Vo = a + b L - c L^2 + d L^3 (L ft, Vo ft/s), SWMM 5.2 inlet.c SplashCoeffs (HEC-22 Chart 5B)
SPLASH = {"p50": (2.22, 4.03, 0.65, 0.06), "p50x100": (0.74, 2.44, 0.27, 0.02), "p30": (1.76, 3.12, 0.45, 0.03),
          "curved_vane": (0.30, 4.85, 1.31, 0.15), "tilt_bar_45": (0.99, 2.64, 0.36, 0.03), "tilt_bar_30": (0.51, 2.34, 0.20, 0.01),
          "reticuline": (0.28, 2.28, 0.18, 0.01)}
# grate opening ratios, HEC-22 Chart 9 (the 45-degree tilt bar: SWMM 5.2's assumed 0.17, HEC-22 gives none)
OPENING = {"p50": 0.90, "p50x100": 0.80, "p30": 0.60, "curved_vane": 0.35, "tilt_bar_45": 0.17, "tilt_bar_30": 0.34, "reticuline": 0.80}


def splash_velocity(grate, length_m):
    a, b, c, d = SPLASH[grate]; L = length_m / FT
    return (a + b * L - c * L * L + d * L ** 3) * FT


class Gutter:
    """A gutter section from a catch basin's fields: depth y(x) across it for a depth d at its low point."""

    def __init__(self, d):
        self.shape = d.get("gutter_shape") or "conventional"
        self.Sx = float(d.get("road_cross_slope") or 0.02); self.n = float(d.get("n_gutter") or d.get("n") or 0.016)
        self.SL = float(d.get("long_slope") or 0.0)
        self.Sw = float(d.get("gutter_cross_slope") or self.Sx); self.W = float(d.get("gutter_width_m") or 0.0)
        if self.Sw < self.Sx: self.Sw = self.Sx
        self.Sc = float(d.get("curb_cross_slope") or self.Sx)
        self.B = float(d.get("ditch_bottom_m") or 0.0); self.z1 = float(d.get("side_slope_l") or 0.0); self.z2 = float(d.get("side_slope_r") or 0.0)
        self.a = (self.Sw - self.Sx) * self.W if self.shape == "conventional" else 0.0      # the gutter depression, m

    def span(self, d):
        """The wetted width [x0, x1] at depth d (x from the curb, or from the low point of a V or the ditch's left toe)."""
        if self.shape == "conventional":
            if d <= self.Sw * self.W or self.W == 0: return 0.0, d / self.Sw
            return 0.0, self.W + (d - self.Sw * self.W) / self.Sx
        if self.shape == "v_shaped":
            left = min(self.W, d / self.Sc) if self.W > 0 else 0.0
            return -left, d / self.Sx
        return -self.z1 * d, self.B + self.z2 * d                                       # trapezoidal ditch

    def depth_at(self, d, x):
        x = np.asarray(x, float)
        if self.shape == "conventional":
            z = np.where(x <= self.W, self.Sw * x, self.Sw * self.W + self.Sx * (x - self.W))
        elif self.shape == "v_shaped":
            z = np.where(x < 0, self.Sc * -x, self.Sx * x)
        else:
            z = np.where(x < 0, -x / max(self.z1, 1e-9), np.where(x > self.B, (x - self.B) / max(self.z2, 1e-9), 0.0))
        return np.clip(d - z, 0.0, None)

    def _strips(self, d, x0=None, x1=None, k=600):
        a, b = self.span(d); a = a if x0 is None else max(a, x0); b = b if x1 is None else min(b, x1)
        if b <= a: return 0.0, 0.0
        x = np.linspace(a, b, k + 1); xm = (x[:-1] + x[1:]) / 2; y = self.depth_at(d, xm); dx = (b - a) / k
        return float((y ** (5.0 / 3.0)).sum() * dx), float(y.sum() * dx)

    def flow(self, d, slope=None):
        """Q (m3/s), area (m2) and spread (m) at depth d."""
        S = self.SL if slope is None else slope
        a, b = self.span(d); T = b - a
        if self.shape == "trapezoidal":                                                  # Manning on the whole section
            A = d * (self.B + (self.z1 + self.z2) * d / 2); P = self.B + d * (math.hypot(1, self.z1) + math.hypot(1, self.z2))
            return (A * (A / P) ** (2 / 3) * math.sqrt(S) / self.n if P > 0 else 0.0), A, T
        I, A = self._strips(d)
        return math.sqrt(S) / self.n * I, A, T

    def depth_for(self, Q, slope=None):
        """The depth at the low point that carries Q (on grade)."""
        if Q <= 0: return 0.0
        lo, hi = 0.0, 0.05
        while self.flow(hi, slope)[0] < Q and hi < 10: hi *= 2
        for _ in range(60):
            m = (lo + hi) / 2
            if self.flow(m, slope)[0] < Q: lo = m
            else: hi = m
        return (lo + hi) / 2

    def frontal_ratio(self, d, width):
        """Eo: the share of the gutter flow over the inlet's width (against the curb; centred on a V's or ditch's low point)."""
        I, _ = self._strips(d)
        if I <= 0: return 1.0
        if self.shape == "conventional": x0, x1 = 0.0, width
        elif self.shape == "v_shaped": x0, x1 = -width / 2, width / 2
        else: x0, x1 = (self.B - width) / 2, (self.B + width) / 2
        return min(1.0, self._strips(d, x0, x1)[0] / I)


def _curb_on_grade(Q, L, g, d):
    """HEC-22 Eq. 4-22 to 4-24: the curb opening's (or slot's) captured flow on grade."""
    Eo = g.frontal_ratio(d, g.W) if (g.shape == "conventional" and g.W > 0 and g.a > 0) else 0.0
    Se = g.Sx + (g.a / g.W) * Eo if g.W > 0 else g.Sx
    LT = 0.817 * Q ** 0.42 * g.SL ** 0.3 * (1.0 / (g.n * Se)) ** 0.6
    E = 1.0 if L >= LT else 1.0 - (1.0 - L / LT) ** 1.8
    return E * Q, dict(LT_m=LT)


def _grate_on_grade(Q, p, g, d, A):
    L, W = float(p["grate_length_m"]), float(p["grate_width_m"])
    V = Q / A if A > 0 else 0.0
    Vo = splash_velocity(p["grate_type"], L)
    Rf = min(1.0, max(0.0, 1.0 - 0.295 * (V - Vo)))                                      # Eq. 4-18
    Rs = 1.0 / (1.0 + 0.0828 * V ** 1.8 / (g.Sx * L ** 2.3))                            # Eq. 4-19
    Eo = g.frontal_ratio(d, W)
    E = Rf * Eo + Rs * (1.0 - Eo)                                                        # Eq. 4-20
    return E * Q, dict(V_ms=V, Vo_ms=Vo, Rf=Rf, Rs=Rs, Eo=Eo)


def _grate_sag(d, p, g):
    L, W = float(p["grate_length_m"]), float(p["grate_width_m"])
    Ag = L * W * float(p.get("opening_ratio") or OPENING[p["grate_type"]])
    if g.shape == "conventional": Wg = min(W, d / g.Sw) if g.Sw > 0 else W; di = d - Wg / 2 * g.Sw; P = L + 2 * Wg   # against a curb
    else: Wg = W; di = d; P = 2 * (L + W)
    di = max(di, 0.0)
    if d <= 1.79 * Ag / max(P, 1e-9): return 1.66 * P * di ** 1.5, "weir"                # Eq. 4-26
    return 0.67 * Ag * math.sqrt(2 * G * di), "orifice"                                  # Eq. 4-27


def _curb_orifice(d, h, L, throat):
    do = d - h / 2 if throat == "horizontal" else d - h / 2 * 0.7071 if throat == "inclined" else d
    return 0.67 * h * L * math.sqrt(2 * G * max(do, 0.0))                               # Eq. 4-31a


def _curb_sag(d, p, g):
    L, h, th = float(p["curb_length_m"]), float(p["curb_height_m"]), p.get("throat") or "vertical"
    dorif = 1.4 * h
    if d > dorif: return _curb_orifice(d, h, L, th), "orifice"
    if g.a <= 0 or L > 3.6: dweir, weir = h, lambda x: 1.60 * L * x ** 1.5               # Eq. 4-30
    else: dweir, weir = h + g.a, lambda x: 1.25 * (L + 1.8 * g.W) * x ** 1.5             # Eq. 4-28 (depressed)
    if d <= dweir or dorif <= dweir: return weir(d), "weir"
    r = (d - dweir) / (dorif - dweir)                                                    # between: weir to orifice, linearly
    return (1 - r) * weir(dweir) + r * _curb_orifice(dorif, h, L, th), "transition"


def _slot_sag(d, p):
    L, W = float(p["slot_length_m"]), float(p["slot_width_m"])
    if d <= 0.8 * math.sqrt(2 * G) / 1.4 * W: return 1.4 * L * d ** 1.5, "weir"         # Eq. 4-32, to where it meets 4-33
    return 0.8 * L * W * math.sqrt(2 * G * d), "orifice"                                 # Eq. 4-33


def sag_capacity(d, p, g):
    c = p["inlet_class"]
    if c == "grate": return _grate_sag(d, p, g)
    if c == "curb": return _curb_sag(d, p, g)
    if c == "slot": return _slot_sag(d, p)
    qg, mode = _grate_sag(d, p, g)                                                       # combination: the grate in weir flow,
    if mode == "weir": return qg, mode                                                   # grate plus curb opening as orifices
    return qg + _curb_orifice(d, float(p["curb_height_m"]), float(p["curb_length_m"]), p.get("throat") or "vertical"), "orifice"


def capture(Q, p):
    """What one inlet captures of Q (m3/s) reaching it. Returns (captured m3/s, detail dict)."""
    t = p.get("inlet_type") or "full_capture"; clog = 1.0 - float(p.get("clogging_pc") or 0.0) / 100.0
    if Q <= 0: return 0.0, dict(type=t)
    if t == "full_capture": return Q, dict(type=t)
    if t == "percent_capture": return Q * float(p.get("capture_pc", 100.0)) / 100.0, dict(type=t)
    if t == "max_capacity": return min(Q, float(p.get("q_max_ls") or 0.0) / 1000.0), dict(type=t)
    if t == "rating_curve":
        r = sorted(p.get("rating") or [])
        if len(r) < 2: return Q, dict(type=t)
        qi = float(np.interp(Q * 1000.0, [a for a, b in r], [b for a, b in r])) / 1000.0
        return min(Q, qi), dict(type=t)
    g = Gutter(p); c = p["inlet_class"]
    if (p.get("location") or "on_grade") == "in_sag":
        lo, hi = 0.0, 0.05                                                               # the depth that passes all of Q
        while sag_capacity(hi, p, g)[0] * clog < Q and hi < 10: hi *= 2
        for _ in range(60):
            m = (lo + hi) / 2
            if sag_capacity(m, p, g)[0] * clog < Q: lo = m
            else: hi = m
        d = (lo + hi) / 2; a, b = g.span(d)
        return Q, dict(type=t, location="in_sag", depth_m=d, spread_m=b - a, mode=sag_capacity(d, p, g)[1])
    d = g.depth_for(Q); _, A, T = g.flow(d)
    if c == "grate": qi, det = _grate_on_grade(Q, p, g, d, A)
    elif c in ("curb", "slot"): qi, det = _curb_on_grade(Q, float(p["curb_length_m" if c == "curb" else "slot_length_m"]), g, d)
    else:                                                                                # combination (HEC-22 p 4-52)
        Lg, Lc = float(p["grate_length_m"]), float(p["curb_length_m"])
        qc, det = _curb_on_grade(Q, Lc - Lg, g, d) if Lc > Lg else (0.0, {})           # a sweeper: the curb opening upstream first
        rest = Q - qc
        if rest > 0:
            d2 = g.depth_for(rest); _, A2, _ = g.flow(d2); qg, det2 = _grate_on_grade(rest, p, g, d2, A2); det.update(det2)
        else: qg = 0.0
        qi = qc + qg
    return min(Q, qi * clog), dict(det, type=t, location="on_grade", depth_m=d, spread_m=T)


def route(project, local_q):
    """Every catch basin's surface flow (its local flow m3/s, plus what the gutters bring and its own additional
    carryover), what its inlet captures, and where the rest goes (down its gutter to the next inlet, or lost when none
    leaves it). Returns {node: row} in L/s and m, in the order the gutters chain them."""
    N, L = project.nodes, project.links
    PN = ((getattr(project, "props", None) or {}).get("nodes") or {})
    cbs = [n for n in N.index if N.kind[n] == "catch_basin"]
    gut = L[L.kind == "gutter"]; nxt = dict(zip(gut.from_node, gut.to_node)); gid = dict(zip(gut.from_node, gut.index))
    indeg = {}
    for b in nxt.values(): indeg[b] = indeg.get(b, 0) + 1
    order, ready, seen = [], [n for n in cbs if indeg.get(n, 0) == 0], set()
    while ready:
        n = ready.pop(); order.append(n); seen.add(n); b = nxt.get(n)
        if b is not None and b in indeg:
            indeg[b] -= 1
            if indeg[b] == 0 and b in set(cbs): ready.append(b)
    if len(order) < len(cbs): raise ValueError(f"the gutters run in a loop through {[n for n in cbs if n not in seen][:3]}")
    carry, rows = {}, {}
    for n in order:
        p = PN.get(n) or {}
        q_loc = float(local_q.get(n, 0.0)); q_in = carry.get(n, 0.0) + float(p.get("carryover_ls") or 0.0) / 1000.0
        Q = q_loc + q_in
        qi, det = capture(Q, p)
        by = max(Q - qi, 0.0); to = nxt.get(n)
        if to is not None: carry[to] = carry.get(to, 0.0) + by
        r = dict(q_local_ls=q_loc * 1000, q_carry_in_ls=q_in * 1000, q_gutter_ls=Q * 1000, q_captured_ls=qi * 1000, q_bypass_ls=by * 1000,
                 efficiency=qi / Q if Q > 0 else None, bypass_to=(to if to is not None else ("lost" if by > 1e-9 else "")), gutter=gid.get(n, ""),
                 inlet=det.get("type"), location=det.get("location"), spread_m=det.get("spread_m"), depth_m=det.get("depth_m"))
        for k in ("V_ms", "Vo_ms", "Rf", "Rs", "Eo", "LT_m", "mode"):
            if k in det: r[k] = det[k]
        if p.get("max_spread_m") and r["spread_m"] is not None: r["spread_over"] = r["spread_m"] > float(p["max_spread_m"]) + 1e-9
        if p.get("max_gutter_depth_m") and r["depth_m"] is not None: r["depth_over"] = r["depth_m"] > float(p["max_gutter_depth_m"]) + 1e-9
        rows[n] = r
    return rows
