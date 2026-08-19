"""Auditor — independent re-check of every rule, as a REGISTRY of named checks.

The solver never grades its own homework: each check recomputes its constraint from the
designed values and the raw 0.5 m terrain. Because every check carries its id, page
reference and requirement, the compliance table is generated from this registry rather
than hand-written — run the pipeline, get the table.

A check returns a list of Finding(element, detail). Empty list = PASS.
Checks whose data is unavailable return NOT_CHECKABLE with the reason.
"""

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from .. import hydra as H
from ..criteria import DEFAULT
from ..model import Network


@dataclass
class Finding:
    element: str
    detail: str


@dataclass
class CheckResult:
    id: str
    group: str
    title: str
    reference: str
    requirement: str
    status: str                      # PASS | FAIL | NOT_CHECKABLE
    summary: str
    findings: List[Finding] = field(default_factory=list)


@dataclass
class Check:
    id: str
    group: str
    title: str
    reference: str
    requirement: str
    fn: Callable                     # (ctx) -> (status, summary, findings)


class AuditContext:
    """Everything a check may look at."""

    def __init__(self, net: Network, units=None, per_chamber=None, sampler=None,
                 crit=DEFAULT, load_stats=None, conn=None):
        self.net = net
        self.units = units or []
        self.per_chamber = per_chamber or {}
        self.sampler = sampler
        self.crit = crit
        self.load_stats = load_stats or {}
        self.conn = conn or []
        self.G = net.digraph()
        self.keys = list(net.chambers)
        self.pts = np.array([[net.chambers[k].x, net.chambers[k].y] for k in self.keys]) \
            if self.keys else np.empty((0, 2))
        self.kd = cKDTree(self.pts) if len(self.pts) else None
        self.idx = {k: i for i, k in enumerate(self.keys)}
        self.linked = {frozenset((self.idx[r.up], self.idx[r.dn])) for r in net.reaches}


# ============================ individual checks ============================
def _min_diameter(ctx):
    C = ctx.crit
    bad = [Finding(r.label, f"DN{r.dn_mm}") for r in ctx.net.reaches if r.dn_mm < C.DN_MIN_MAIN]
    smallest = min((r.dn_mm for r in ctx.net.reaches), default=0)
    return ("FAIL" if bad else "PASS", f"smallest DN used {smallest}", bad)


def _material(ctx):
    C = ctx.crit
    bad = [Finding(r.label, f"DN{r.dn_mm} as {r.material}") for r in ctx.net.reaches
           if r.material != C.material(r.dn_mm)]
    return ("FAIL" if bad else "PASS",
            f"materials {sorted(set(r.material for r in ctx.net.reaches))}", bad)


def _min_gradient(ctx):
    C = ctx.crit
    bad = [Finding(r.label, f"{r.slope*1000:.2f} < {H.smin_for(r.dn_mm, r.qpeak_m3s, C)*1000:.2f} mm/m")
           for r in ctx.net.reaches if r.slope < H.smin_for(r.dn_mm, r.qpeak_m3s, C) * 0.999]
    flat = min((r.slope for r in ctx.net.reaches), default=0) * 1000
    return ("FAIL" if bad else "PASS", f"flattest laid {flat:.2f} mm/m", bad)


def _max_velocity(ctx):
    C = ctx.crit
    bad = [Finding(r.label, f"v {r.vel:.2f} m/s") for r in ctx.net.reaches
           if r.vel is not None and r.vel > C.V_MAX + 0.01]
    vmax = max((r.vel or 0) for r in ctx.net.reaches) if ctx.net.reaches else 0
    return ("FAIL" if bad else "PASS", f"highest v {vmax:.2f} m/s", bad)


def _self_cleansing(ctx):
    """0.75 m/s is unattainable on small head branches — G203-p27 offers the tractive-force
    methodology exactly for that case. A violation needs BOTH criteria missed."""
    C = ctx.crit
    below = [r for r in ctx.net.reaches if r.vel is not None and r.vel < C.V_SELF_CLEANSING]
    bad = [Finding(r.label, f"v {r.vel:.2f} m/s and slope under the tractive minimum")
           for r in below if r.slope < H.smin_tractive(r.qpeak_m3s, C) * 0.999]
    n = len(ctx.net.reaches)
    return ("FAIL" if bad else "PASS",
            f"{len(below)}/{n} reaches below 0.75 m/s, all tractive-compliant at "
            f"tau={C.TAU_PA} Pa [GAP-9]", bad)


def _dod(ctx):
    """d/D limit AND capacity. A reach whose diameter cannot pass its peak flow at the
    laid slope returns dod None — that is a surcharged pipe, the worst failure there is,
    and it must never be silently skipped (review F1: the refactor dropped this branch)."""
    C = ctx.crit
    bad = []
    for r in ctx.net.reaches:
        if r.dod is None:
            bad.append(Finding(r.label, f"DN{r.dn_mm} CANNOT CARRY {r.qpeak_ls:.1f} L/s at "
                                        f"{r.slope*1000:.2f} mm/m — surcharged"))
        elif r.dod > H.dod_limit(r.dn_mm, C) + 0.005:
            bad.append(Finding(r.label, f"d/D {r.dod:.2f} > {H.dod_limit(r.dn_mm, C)}"))
    worst = max((r.dod or 0) for r in ctx.net.reaches) if ctx.net.reaches else 0
    n_sur = sum(1 for r in ctx.net.reaches if r.dod is None)
    return ("FAIL" if bad else "PASS",
            f"deepest flow d/D {worst:.3f}" + (f"; {n_sur} surcharged" if n_sur else ""), bad)


def _reverse_gradient(ctx):
    bad = [Finding(r.label, f"inv_up {r.inv_up:.3f} <= inv_dn {r.inv_dn:.3f}")
           for r in ctx.net.reaches if r.inv_up is not None and r.inv_up <= r.inv_dn]
    return ("FAIL" if bad else "PASS", f"{len(bad)} reversed reaches", bad)


def _fall_tolerance(ctx):
    C = ctx.crit
    bad = []
    for r in ctx.net.reaches:
        if r.fall >= C.FALL_TOLERANCE - 0.0005:
            continue
        smax = H.smax_for(r.dn_mm, r.qpeak_m3s, C)     # velocity-capped reaches are exempt
        if smax is None or smax == H.INFEASIBLE or r.slope < smax * 0.99:
            bad.append(Finding(r.label, f"fall {r.fall*1000:.0f} mm"))
    return ("FAIL" if bad else "PASS", f"{len(bad)} reaches under 40 mm fall", bad)


def _cover(ctx):
    C = ctx.crit
    bad, worst, worst_lab = [], 9e9, ""
    for r in ctx.net.reaches:
        D = C.internal_diameter(r.dn_mm)
        for chn, _x, _y, g in r.profile:
            cov = g - ((r.inv_up - r.slope * chn) + D)
            if cov < worst:
                worst, worst_lab = cov, r.label
            if cov < C.MIN_COVER_CROWN - 0.01:
                bad.append(Finding(r.label, f"cover {cov:.2f} m at chainage {chn:.0f}"))
                break
    return ("FAIL" if bad else "PASS", f"worst cover {worst:.2f} m ({worst_lab})", bad)


def _max_depth(ctx):
    C = ctx.crit
    bad = []
    for r in ctx.net.reaches:
        if ctx.net.chambers[r.up].sls_pocket or ctx.net.chambers[r.dn].sls_pocket:
            continue
        for chn, _x, _y, g in r.profile:
            if g - (r.inv_up - r.slope * chn) > C.MAX_DEPTH + 0.01:
                bad.append(Finding(r.label, f"depth {g-(r.inv_up-r.slope*chn):.2f} m"))
                break
    deepest = max((c.depth or 0) for c in ctx.net.chambers.values()) if ctx.net.chambers else 0
    return ("FAIL" if bad else "PASS", f"deepest chamber {deepest:.2f} m", bad)


def _spacing(ctx):
    C = ctx.crit
    bad = [Finding(r.label, f"{r.length:.1f} m > {C.mh_max_spacing(r.dn_mm)} m for DN{r.dn_mm}")
           for r in ctx.net.reaches if r.length > C.mh_max_spacing(r.dn_mm) + 0.01]
    longest = max((r.length for r in ctx.net.reaches), default=0)
    return ("FAIL" if bad else "PASS", f"longest reach {longest:.1f} m", bad)


def _clean_coords(coords, min_step=0.5):
    out = [coords[0]]
    for c in coords[1:]:
        if math.dist(out[-1], c) >= min_step:
            out.append(c)
    if len(out) == 1:
        out.append(coords[-1])
    return out


def _bends(ctx):
    """Deflection measured on cleaned vertices — duplicate points otherwise read as 180 deg."""
    bad = []
    worst = 0.0
    for r in ctx.net.reaches:
        c = _clean_coords(list(r.geom.coords))
        m = 0.0
        for i in range(1, len(c) - 1):
            a1 = math.atan2(c[i][1] - c[i-1][1], c[i][0] - c[i-1][0])
            a2 = math.atan2(c[i+1][1] - c[i][1], c[i+1][0] - c[i][0])
            d = abs(math.degrees(a2 - a1)) % 360.0
            m = max(m, min(d, 360.0 - d))
        worst = max(worst, m)
        if m > ctx.crit.ROAD_BEND_DEG + 0.5:
            bad.append(Finding(r.label, f"interior deflection {m:.0f} deg"))
    return ("FAIL" if bad else "PASS", f"largest interior deflection {worst:.0f} deg", bad)


def _drops(ctx):
    C = ctx.crit
    bad = []
    for k, ch in ctx.net.chambers.items():
        if ch.invert is None:
            continue
        recorded = {d["pipe"]: d for d in ch.drops}
        for u in ctx.G.predecessors(k):
            r = ctx.G[u][k]["reach"]
            h = r.inv_dn - ch.invert
            if h <= C.DROP_TRIGGER + 0.001:
                continue
            rec = recorded.get(r.label)
            if rec is None:
                bad.append(Finding(ch.label, f"inlet {r.label} arrives {h:.2f} m high, no record"))
            elif abs(rec["height"] - h) > 0.01 or (h > C.BACKDROP_MAX and rec["type"] != "vortex"):
                bad.append(Finding(ch.label, f"inlet {r.label} recorded {rec['height']:.2f} m "
                                             f"({rec['type']}) vs real {h:.2f} m"))
    total = sum(len(c.drops) for c in ctx.net.chambers.values())
    vortex = sum(1 for c in ctx.net.chambers.values() for d in c.drops if d["type"] == "vortex")
    return ("FAIL" if bad else "PASS", f"{total} drops ({vortex} vortex-class)", bad)


def _inlet_angle(ctx):
    """G203-p30 verbatim: 'No inlet pipe at manholes shall have an angle less than 90 deg
    to the direction of flow.'"""
    bad = []
    for k in ctx.G.nodes:
        outs = [ctx.G[k][v]["reach"] for v in ctx.G.successors(k)]
        if not outs:
            continue
        co = _clean_coords(list(outs[0].geom.coords))
        bo = math.atan2(co[1][1] - co[0][1], co[1][0] - co[0][0])
        for u in ctx.G.predecessors(k):
            r = ctx.G[u][k]["reach"]
            ci = _clean_coords(list(r.geom.coords))
            bi = math.atan2(ci[-1][1] - ci[-2][1], ci[-1][0] - ci[-2][0])
            turn = abs(math.degrees(bo - bi)) % 360.0
            turn = min(turn, 360.0 - turn)
            if turn > 91.0:
                bad.append(Finding(ctx.net.chambers[k].label,
                                   f"inlet {r.label} meets the outlet at {180-turn:.0f} deg"))
    n_in = sum(1 for _ in ctx.net.reaches)
    return ("FAIL" if bad else "PASS", f"{len(bad)} of {n_in} inlets under 90 deg", bad)


def _one_outlet(ctx):
    _, outd = ctx.net.degrees()
    bad = [Finding(ctx.net.chambers[k].label, f"{d} outlets") for k, d in outd.items() if d > 1]
    return ("FAIL" if bad else "PASS", f"{len(bad)} chambers with more than one outlet", bad)


def _no_loops(ctx):
    ok = nx.is_directed_acyclic_graph(ctx.G) and len(ctx.net.reaches) == len(ctx.net.chambers) - 1
    comps = nx.number_weakly_connected_components(ctx.G)
    return ("PASS" if ok else "FAIL",
            f"{len(ctx.net.chambers)} chambers / {len(ctx.net.reaches)} reaches, "
            f"{comps} component, acyclic={nx.is_directed_acyclic_graph(ctx.G)}", [])


def _clearance(ctx):
    C = ctx.crit
    if ctx.kd is None:
        return ("NOT_CHECKABLE", "no chambers", [])
    bad = []
    for i, j in ctx.kd.query_pairs(C.MH_MIN_CLEAR_M):
        if frozenset((i, j)) in ctx.linked:
            continue                     # consecutive chambers on one reach
        d = float(np.hypot(*(ctx.pts[i] - ctx.pts[j])))
        bad.append(Finding(f"{ctx.net.chambers[ctx.keys[i]].label}/"
                           f"{ctx.net.chambers[ctx.keys[j]].label}", f"{d:.2f} m apart"))
    return ("FAIL" if bad else "PASS", f"{len(bad)} pairs closer than "
            f"{C.MH_MIN_CLEAR_M} m", bad)


def _branch_offset(ctx):
    C = ctx.crit
    bad = []
    for h in ctx.net.heads():
        for j in ctx.kd.query_ball_point(ctx.pts[ctx.idx[h]], C.FANOUT_OFFSET_M):
            o = ctx.keys[j]
            if o == h or frozenset((ctx.idx[h], j)) in ctx.linked:
                continue
            if ctx.net.chambers[o].kind in ("junction", "outfall"):
                d = float(np.hypot(*(ctx.pts[ctx.idx[h]] - ctx.pts[j])))
                bad.append(Finding(ctx.net.chambers[h].label,
                                   f"starts {d:.1f} m from {ctx.net.chambers[o].label}"))
                break
    return ("FAIL" if bad else "PASS",
            f"{len(ctx.net.heads())-len(bad)}/{len(ctx.net.heads())} branch heads clear", bad)


def _pcs_length(ctx):
    C = ctx.crit
    bad = [Finding(str(r["id"]), f"{r['dist']:.0f} m to {r['mh']}") for r in ctx.conn
           if r["dist"] > C.PCS_MAX_LEN]
    longest = max((r["dist"] for r in ctx.conn), default=0)
    return ("FAIL" if bad else "PASS",
            f"{len(bad)}/{len(ctx.conn)} connections over {C.PCS_MAX_LEN} m; longest "
            f"{longest:.0f} m", bad)


def _mass_balance(ctx):
    C = ctx.crit
    net = ctx.net
    q_in = sum(ctx.G[u][net.outfall]["reach"].qadf_m3d for u in ctx.G.predecessors(net.outfall))
    expect = sum(getattr(u, "n_props", 1.0) for v in ctx.per_chamber.values()
                 for u in v) * C.PLOT_QADF_M3D
    ok = abs(q_in - expect) < 0.5
    return ("PASS" if ok else "FAIL",
            f"outfall receives {q_in:,.1f} m3/d vs {expect:,.1f} m3/d of unit loads",
            [] if ok else [Finding("OF-1", f"difference {abs(q_in-expect):.2f} m3/d")])


def _assignment(ctx):
    n_assigned = sum(len(v) for v in ctx.per_chamber.values())
    bad = []
    if n_assigned != len(ctx.units):
        bad.append(Finding("network", f"{len(ctx.units)-n_assigned} units unassigned"))
    if ctx.load_stats.get("class_other", 0):
        bad.append(Finding("plots", f"{ctx.load_stats['class_other']} plots with an "
                                    f"unexpected CLASS"))
    return ("FAIL" if bad else "PASS", f"{n_assigned}/{len(ctx.units)} units assigned", bad)


REGISTRY = [
    Check("A1", "Pipes & hydraulics", "Minimum main diameter", "G203-p22 Tab 6",
          "DN200 minimum", _min_diameter),
    Check("A2", "Pipes & hydraulics", "Material by diameter", "G203-p22/23 Tab 6-7",
          "PVC-U to DN315, GRP above", _material),
    Check("A3", "Pipes & hydraulics", "Minimum gradient", "G203-p29 Tab 11 + p27",
          "steeper of Table 11 and the tractive minimum", _min_gradient),
    Check("A4", "Pipes & hydraulics", "Maximum velocity", "G203-p27",
          "v <= 3.0 m/s at design depth", _max_velocity),
    Check("A5", "Pipes & hydraulics", "Self-cleansing at peak", "G203-p26-27",
          "v >= 0.75 m/s or the tractive-force minimum gradient", _self_cleansing),
    Check("A6", "Pipes & hydraulics", "Proportional depth d/D", "G203-p27 Tab 10",
          "<=0.65 (DN<=350), <=0.50 (DN>350)", _dod),
    Check("A7", "Pipes & hydraulics", "No reverse gradient", "G203-p29 4.3.1",
          "inv_up > inv_dn on every reach", _reverse_gradient),
    Check("A8", "Pipes & hydraulics", "Construction tolerance guard", "G203-p29 4.3.1 (A9)",
          "reach fall > 40 mm unless velocity-capped", _fall_tolerance),
    Check("B1", "Cover & depth", "Minimum cover to crown", "G203-p33 4.6.3",
          ">= 1.30 m along the whole profile", _cover),
    Check("B2", "Cover & depth", "Maximum depth", "G203-p33 + rule 9",
          "<= 12 m, deeper becomes an SLS pocket", _max_depth),
    Check("C1", "Chambers", "Maximum spacing", "G203-p30 Tab 12",
          "100 m (DN200-315) / 120 / 150 / 200", _spacing),
    Check("C2", "Chambers", "Chamber at change of direction", "G203-p30",
          "a bend sharper than the declared threshold breaks the reach", _bends),
    Check("C3", "Chambers", "Drop / backdrop bookkeeping", "G203-p30 4.4",
          "inlet drop > 600 mm recorded as backdrop; > 2 m as vortex shaft", _drops),
    Check("C4", "Chambers", "Inlet angle", "G203-p30",
          "no inlet at less than 90 deg to the direction of flow", _inlet_angle),
    Check("C5", "Chambers", "One outlet per chamber", "user rule / SWNETWROK",
          "exactly one outgoing reach", _one_outlet),
    Check("C6", "Chambers", "No loops", "user rule",
          "tree draining to a single outfall", _no_loops),
    Check("C7", "Chambers", "Chamber clearance", "layout convention (no PAM minimum exists)",
          "distinct chambers at least 3 m apart", _clearance),
    Check("C8", "Chambers", "Branch start offset", "user rule / SWNETWROK 10 m",
          "branch starts at the next house connection or 10 m clear", _branch_offset),
    Check("D1", "Tertiary", "Property connection length", "G203-p18 Tab 4 (A9)",
          "<= 50 m, else an intermediate chamber", _pcs_length),
    Check("E1", "Loads", "Mass balance", "bookkeeping",
          "unit loads arrive at the outfall", _mass_balance),
    Check("E2", "Loads", "Every unit assigned", "doctrine (zero silent drops)",
          "every loaded unit lands on exactly one chamber", _assignment),
]


class Auditor:
    def __init__(self, crit=DEFAULT):
        self.crit = crit
        self.results: List[CheckResult] = []

    def run(self, net, units=None, per_chamber=None, sampler=None, load_stats=None, conn=None):
        ctx = AuditContext(net, units, per_chamber, sampler, self.crit, load_stats, conn)
        self.results = []
        for chk in REGISTRY:
            try:
                status, summary, findings = chk.fn(ctx)
            except Exception as e:                     # a broken check must not hide the rest
                status, summary, findings = "NOT_CHECKABLE", f"{e.__class__.__name__}: {e}", []
            self.results.append(CheckResult(chk.id, chk.group, chk.title, chk.reference,
                                            chk.requirement, status, summary, findings))
        return self.results

    # ---------------- reporting ----------------
    @property
    def failures(self):
        """A check that could not run is NOT a pass — a crashing check would otherwise
        hide a real violation behind a quiet label (review F3)."""
        return [r for r in self.results if r.status in ("FAIL", "NOT_CHECKABLE")]

    @property
    def hard_failures(self):
        return [r for r in self.results if r.status == "FAIL"]

    def table(self):
        lines = [f"{'ID':4} {'STATUS':13} {'CHECK':38} {'REF':28} FOUND",
                 "-" * 150]
        for r in self.results:
            lines.append(f"{r.id:4} {r.status:13} {r.title[:38]:38} {r.reference[:28]:28} "
                         f"{r.summary}")
        n_f = len(self.hard_failures)
        n_x = sum(1 for r in self.results if r.status == "NOT_CHECKABLE")
        lines.append("-" * 150)
        lines.append(f"{len(self.results)} checks: {len(self.results)-n_f-n_x} pass, "
                     f"{n_f} fail, {n_x} could not run (counted as failures)")
        return "\n".join(lines)

    def as_dicts(self):
        return [{"id": r.id, "group": r.group, "check": r.title, "reference": r.reference,
                 "requirement": r.requirement, "status": r.status, "found": r.summary,
                 "findings": [{"element": f.element, "detail": f.detail}
                              for f in r.findings[:50]]} for r in self.results]


def start_year_selfclean(net: Network, per_chamber, crit=DEFAULT, pf_formula="merrimack"):
    """Operational flags: reaches below 0.75 m/s when only EXISTING structures load the
    network (CLASS=B built plots AND CLASS=U unparceled buildings — review F2). Doctrine
    §2.1 early-years check; not a design failure (G203-p28 §4.2.6)."""
    from copy import copy
    from .loads import LoadAllocator
    shadow = Network({k: c for k, c in net.chambers.items()},
                     [copy(r) for r in net.reaches], net.outfall)
    b_only = {k: [u for u in v if u.cls in ("B", "U")] for k, v in per_chamber.items()}
    LoadAllocator(crit, pf_formula).accumulate(shadow, b_only)
    flags = []
    for r in shadow.reaches:
        y, v = H.pipe_state(r.dn_mm, r.slope, r.qpeak_m3s, crit)
        if y is not None and v < crit.V_SELF_CLEANSING:
            flags.append({"pipe": r.label, "v_start": v, "dn": r.dn_mm,
                          "tractive_ok": r.slope >= H.smin_tractive(r.qpeak_m3s, crit)})
    return flags


def selfclean_stats(net: Network, crit=DEFAULT):
    """How much of the network leans on the tau assumption, and the tau=2 exposure."""
    n = len(net.reaches)
    below = [r for r in net.reaches if r.vel is not None and r.vel < crit.V_SELF_CLEANSING]
    tau2 = sum(1 for r in below
               if r.slope < H.smin_tractive(r.qpeak_m3s, crit) * (2.0 ** 1.23) * 0.999)
    return {"pipes": n, "below_075_at_peak": len(below),
            "share_below": round(len(below) / n, 3) if n else 0.0,
            "would_fail_at_tau2": tau2,
            "note": "0.75 m/s unattainable on small branches; compliance rests on the "
                    "tractive methodology at tau=1 Pa [GAP-9]"}
