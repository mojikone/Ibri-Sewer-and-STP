# -*- coding: utf-8 -*-
"""T04 chapter 11: gravity sewer hydraulics.

Ports T02 (every constraint with its page) and T03_R01 section 9 onto the settled rules:
guideline tier words, the two flow cases, the 12 m hard limit, and the concept-stage rulings of
2026-09-11 (gradients at the G203 Table 11 minimum on 0.05 % / 0.025 % steps; the tractive force a
check, never a gradient; three self-cleansing classes on the true low-case flow).

Every guideline value below was read back from PAM-GUD-203 / PAM-GUD-201 (printed page
numbers) on 2026-09-11, or taken from _BRAIN/02_DESIGN_CRITERIA.md. Every Ibri number is
computed here at build time from the plot layer (facts_w14), design_flows.json and the W8
design outputs; none is typed.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report"))   # after T04: its doc.py must not shadow ours
import doc as D
import omml as M
import facts_w14 as F
UP, R = M.up, M.r
IMG = os.path.join(HERE, "img")

import io
import json
import math
from functools import lru_cache

REPO = os.path.dirname(os.path.dirname(HERE))
W8SHP = os.path.join(REPO, "W8", "shp")
FLOWS_JSON = os.path.join(REPO, "W14", "analysis", "design_flows.json")

# ------------------------------------------------------------ guideline constants
G = 9.81
KS = 0.0015                       # m, all sizes and materials (G203-p24, p28)
NU15, NU25, NU35 = 1.141e-6, 0.897e-6, 0.727e-6   # m2/s, Table 9 (G203-p25)
V_MIN, V_PREF, V_MAX = 0.75, 0.90, 3.0            # m/s (G203-p26, p26, p27)
DOD_SMALL, DOD_LARGE, DOD_DN = 0.65, 0.50, 350    # Table 10 (G203-p27)
TABLE11 = {200: 5.00, 250: 3.75, 315: 2.70, 400: 2.05, 500: 1.55,
           600: 1.25, 700: 1.00, 800: 0.85, 900: 0.75}   # mm/m (G203-p29)
TABLE12 = [("200 to 315", 100), ("350 to 900", 120), ("1 000 to 1 400", 150),
           ("More than 1 400", 200)]                     # m (G203-p30)
K_M3S, K_LS = 2.33e-4, 5.5e-3     # Mara constants (G203-p27); K_M3S used for every slope
K_GAP = 1.0 - K_LS / (K_M3S * 1000.0 ** 0.461)   # the l/s constant gives slopes this much flatter
TOL = 0.020                       # m line and level (G203-p29)
MIN_COVER = 1.3                   # m to crown (G203-p33)
DROP_BACK, DROP_VORTEX = 0.600, 2.0   # m (G203-p30)
# ------------------------------------------------------------ project values (tagged in text)
MAX_DEPTH = 12.0                  # m, hard limit, no exceptions (PROJECT_STATE 2 item 3)
STEP = 0.0005                     # m/m, 0.05 %: secondary pipes (engineer 2026-09-11); also the single
                                  # grid W8 was laid on at every size, the engine's SLOPE_STEP today
STEP_TRUNK = 0.00025              # m/m, 0.025 %: primary trunks of DN500 and up (engineer 2026-09-11)
DN_TRUNK_STEP = 500               # mm, the size from which the trunk step applies (the engine sets it by size)
STEP_FRAC_OLD = 0.1               # superseded W13 rule 8 (a tenth of the minimum); only to show why it went
TAU = 1.0                         # Pa, concept-stage value (engineer 2026-09-11); GAP-9, NWS to confirm
TAUS = (1.0, 1.5, 2.0)            # Pa, the information table; the class is decided at TAU
Q_MARA = 1.5                      # l/s, Mara's minimum flow: not in G203 and NOT used (engineer 2026-09-11)
SDR = 34.0                        # PVC-U SN8 wall class behind the true bore, assumption
WALL = 0.05                       # m pipe wall and bedding below crown cover, method choice
SERIES = [200, 250, 315, 400, 500, 600, 700, 800, 900]


# ================================================================== hydraulics
def bore(dn):
    """True internal diameter, m: PVC-U is OD-designated up to 315, GRP is ID-designated."""
    return dn / 1000.0 * (1.0 - 2.0 / SDR) if dn <= 315 else dn / 1000.0


def v_cw_R(Rh, S, nu=NU15):
    if Rh <= 0 or S <= 0:
        return 0.0
    root = math.sqrt(8.0 * G * Rh * S)
    return -2.0 * root * math.log10(KS / (14.8 * Rh) + 0.6275 * nu / (Rh * root))


def v_full(Dm, S, nu=NU15):
    return v_cw_R(Dm / 4.0, S, nu)


def q_full(Dm, S):
    return v_full(Dm, S) * math.pi * Dm * Dm / 4.0


def _seg(Dm, y):
    y = min(max(y, 1e-6), 1.0 - 1e-9)
    th = 2.0 * math.acos(1.0 - 2.0 * y)
    A = Dm * Dm / 8.0 * (th - math.sin(th))
    return A, A / (Dm * th / 2.0)


def v_part(Dm, S, y):
    return v_cw_R(_seg(Dm, y)[1], S)


def q_part(Dm, S, y):
    A, Rh = _seg(Dm, y)
    return v_cw_R(Rh, S) * A


def solve(Dm, S, Q):
    """(d/D, v) carrying Q m3/s at slope S; (None, None) if it cannot carry Q."""
    if q_part(Dm, S, 0.95) < Q:
        return None, None
    lo, hi = 1e-4, 0.95
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if q_part(Dm, S, mid) < Q:
            lo = mid
        else:
            hi = mid
    y = 0.5 * (lo + hi)
    return y, v_part(Dm, S, y)


def smin_tractive(q_ls, tau=TAU):
    """Mara minimum slope, m/m, at the TRUE flow q_ls (no floor), K in m3/s (G203-p27)."""
    if q_ls <= 0:
        return float("inf")
    return K_M3S * tau ** 1.23 * (q_ls / 1000.0) ** -0.461


def q_at_smin(s, tau=TAU):
    """Flow, l/s, at which the Mara slope equals s: a pipe laid at s passes the tractive test above it."""
    return (s / (K_M3S * tau ** 1.23)) ** (-1.0 / 0.461) * 1000.0


def spacing(dn):
    """G203 Table 12 maximum manhole spacing, m, for the sizes of TABLE11."""
    return 100 if dn <= 315 else 120


def s_vmax(dn, q_ls):
    """Gradient at which the velocity at the design flow reaches 3.0 m/s; None if not below 100 %."""
    Dm = bore(dn)
    y, v = solve(Dm, 1.0, q_ls / 1000.0)
    if y is None or v < V_MAX:
        return None
    lo, hi = 1e-5, 1.0
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        y, v = solve(Dm, mid, q_ls / 1000.0)
        if y is None or v < V_MAX:
            lo = mid
        else:
            hi = mid
    return hi


def dod_limit(dn):
    return DOD_SMALL if dn <= DOD_DN else DOD_LARGE


def round_up(s):
    """Round up on the single 0.05 % grid the W8 design was laid on at every size (the engine's
    SLOPE_STEP today)."""
    return math.ceil(round(s / STEP, 6)) * STEP


def step_for(dn):
    """Project gradient step for a size, m/m (engineer 2026-09-11): 0.025 % for trunks of DN500
    and up, 0.05 % below."""
    return STEP_TRUNK if dn >= DN_TRUNK_STEP else STEP


def round_up_step(s, dn):
    """Round up to the next project step of that size."""
    st = step_for(dn)
    return math.ceil(round(s / st, 6)) * st


def step_old(dn):
    """Superseded W13 rule 8 step, m/m: a tenth of the size's G203 Table 11 minimum."""
    return TABLE11[dn] / 1000.0 * STEP_FRAC_OLD


# ================================================================== flows
@lru_cache(None)
def _json():
    with open(FLOWS_JSON, encoding="utf-8") as f:
        return json.load(f)


def peak(q_m3d, props):
    """(method, PF, peak l/s): Merrimack over 100 properties (G201-p71), else Peltier (G201-p72)."""
    if props > 100:
        mld = q_m3d / 1000.0
        pf = 2.65 * mld ** 0.879 / mld
        return "Merrimack", pf, pf * q_m3d / 86.4
    qm = q_m3d / 86.4
    pf = 1.5 + 1.0 / math.sqrt(qm)
    return "Peltier", pf, pf * qm


@lru_cache(None)
def _w8():
    import geopandas as gpd
    return (gpd.read_file(os.path.join(W8SHP, "W8_pipes.shp")),
            gpd.read_file(os.path.join(W8SHP, "W8_manholes.shp")),
            gpd.read_file(os.path.join(W8SHP, "W8_catchments.shp")))


@lru_cache(None)
def _catchment_flows():
    """W14 plot flows summed inside each W8 catchment (plot representative point)."""
    import geopandas as gpd
    _, _, cat = _w8()
    pl = F.plots()[["G_DOM", "POP", "POP_2030", "POP_ULT", "Q_2030", "Q_ULT", "OR_S",
                    "geometry"]].copy()
    pl["geometry"] = pl.geometry.representative_point()
    pl["PR_ULT"] = pl.G_DOM + (pl.POP_ULT - pl.POP) / pl.OR_S
    pl["PR_2030"] = pl.G_DOM + (pl.POP_2030 - pl.POP) / pl.OR_S
    j = gpd.sjoin(pl, cat[["INLET", "geometry"]].to_crs(pl.crs), predicate="within")
    return j.groupby("INLET").agg(n=("Q_ULT", "size"), qult=("Q_ULT", "sum"),
                                  q30=("Q_2030", "sum"), prnow=("G_DOM", "sum"),
                                  prult=("PR_ULT", "sum"), pr30=("PR_2030", "sum"))


def _classify(v_low, s_laid, q_low_ls, tau=TAU):
    """Three classes on the low-case peak (engineer 2026-09-11): the velocity first, then the
    tractive slope at the true flow, with no floor and no low-flow threshold; everything else
    needs washing. There is no regrade class: the tractive force sets no gradient at concept."""
    if v_low is not None and v_low >= V_MIN:
        return "velocity pass"
    if s_laid >= smin_tractive(q_low_ls, tau):
        return "tractive pass"
    return "needs washing"


@lru_cache(None)
def example(inlet):
    pipes, mh, cat = _w8()
    p = pipes.set_index("LABEL").loc[inlet]
    c = cat[cat.INLET == inlet].iloc[0]
    a = _catchment_flows().loc[inlet]
    J = _json()["rules"]
    conn, inf = J["connection_ratio_2030"], J["infiltration_l_per_day_per_km"]
    out = dict(inlet=inlet, tier=p.TIER, dn=int(p.DN_MM), s=float(p.SLOPE_PMIL) / 1000.0,
               length=float(p.LEN_M), join=p.ND_DN, n_plots=int(a.n), pr_now=float(a.prnow),
               pr_ult=float(a.prult), pr_30=float(a.pr30), q_ult=float(a.qult),
               q_30=float(a.q30), sewer_m=float(c.PIPE_M), deepest=float(c.DEEPEST_M),
               area_ha=float(c.AREA_HA), w8_props=float(c.N_PROPS), w8_qadf=float(c.QADF_M3D),
               drop=float(p.DROP_DN), conn=conn, inf=inf)
    m_u, pf_u, pk_u = peak(out["q_ult"], out["pr_ult"])
    inf_ls = inf * out["sewer_m"] / 1000.0 / 86400.0
    out.update(m_ult=m_u, pf_ult=pf_u, pk_ult=pk_u, inf_ls=inf_ls, q_des=pk_u + inf_ls)
    # the low case: Q_2030 x 0.61, no infiltration, and the formula chosen on the CONNECTED count,
    # properties of 2030 x 0.61 (engineer 2026-09-11; design_flows.json rules.rulings_confirmed)
    out["q_low"] = out["q_30"] * conn
    out["pr_30c"] = out["pr_30"] * conn
    m_l, pf_l, pk_l = peak(out["q_low"], out["pr_30c"])
    out.update(m_low=m_l, pf_low=pf_l, pk_low=pk_l)
    out["m_low_standing"] = peak(out["q_low"], out["pr_30"])[0]
    # concept-stage gradient (engineer 2026-09-11): the G203 Table 11 minimum rounded up to the
    # project step of the size; the tractive force sets no gradient. W8 laid every size on one
    # 0.05 % grid: where it sat on that grid's minimum the pipe is at its minimum, otherwise it
    # follows the ground and keeps its gradient, on the project step.
    dn, S_w8 = out["dn"], out["s"]
    s_req = TABLE11[dn] / 1000.0
    out["at_min"] = S_w8 <= round_up(s_req) + 1e-9
    S = round_up_step(s_req if out["at_min"] else S_w8, dn)
    out.update(s=S, s_w8=S_w8, s_req=s_req, step=step_for(dn))
    out["y"], out["v"] = solve(bore(dn), S, out["q_des"] / 1000.0)
    out["y_low"], out["v_low"] = solve(bore(dn), S, pk_l / 1000.0)
    # the audit's tractive test on the true low-case peak: decided at TAU, shown at every TAUS
    out["smin_tau"] = {t: smin_tractive(pk_l, t) for t in TAUS}
    out["cls_tau"] = {t: _classify(out["v_low"], S, pk_l, t) for t in TAUS}
    out["smin_t"], out["smin_t2"] = out["smin_tau"][TAU], out["smin_tau"][2.0]
    out["cls"], out["cls2"] = out["cls_tau"][TAU], out["cls_tau"][2.0]
    out["q_pass"] = q_at_smin(S)
    out["s_vmax"] = s_vmax(dn, out["q_des"])
    j = mh.set_index("LABEL").loc[p.ND_DN]
    out.update(j_depth=float(j.DEPTH), j_gnd=float(j.GND), j_inv=float(j.INVERT))
    # trial sizing at the laid gradient, never below each size's laid minimum
    trials = []
    for d_ in SERIES:
        s_use = max(S, round_up_step(TABLE11[d_] / 1000.0, d_))
        y, v = solve(bore(d_), s_use, out["q_des"] / 1000.0)
        ok = y is not None and y <= dod_limit(d_)
        trials.append((d_, s_use, y, v, ok))
        if ok:
            break
    out["trials"] = trials
    return out


@lru_cache(None)
def w8_stats():
    pipes, mh, cat = _w8()
    dmax = pipes.groupby("ND_DN").DROP_DN.max()
    tiers = pipes.TIER.value_counts().to_dict()
    by_dn = {int(k): (int(len(g)), float(g.LEN_M.max()), float(g.SLOPE_PMIL.min()))
             for k, g in pipes.groupby("DN_MM")}
    big = pipes[pipes.DN_MM >= DN_TRUNK_STEP]        # the sizes the 0.025 % step applies to
    big_at_min = int(sum(abs(r.SLOPE_PMIL / 1000.0 - round_up(TABLE11[int(r.DN_MM)] / 1000.0)) < 1e-9
                         for r in big.itertuples() if int(r.DN_MM) in TABLE11))
    big_trunk = int((big.TIER == "trunk main").sum())
    return dict(km=float(pipes.LEN_M.sum()) / 1000.0, chambers=len(mh),
                pumps=int(mh.IS_PUMP.sum()), deepest=float(mh.DEPTH.max()),
                grads=int(pipes.SLOPE_PMIL.round(3).nunique()),
                at_min=int((pipes.SLOPE_PMIL.round(3) == 5.0).sum()),
                n_pipes=len(pipes), med_grad=float(pipes.SLOPE_PMIL.median()),
                vmax=float(pipes.VEL_MS.max()), dodmax=float(pipes.DOD.max()),
                drops_back=int((dmax > DROP_BACK).sum()),
                drops_vortex=int((dmax > DROP_VORTEX).sum()),
                vortex_field=int((mh.VORTEX == 1).sum()),
                vortex_extra=sorted((str(r.LABEL), float(dmax.get(r.LABEL, 0.0)))
                                    for r in mh[mh.VORTEX == 1].itertuples()
                                    if not dmax.get(r.LABEL, 0.0) > DROP_VORTEX),
                sharp=int(mh.SHARP_IN.sum()), tiers=tiers, by_dn=by_dn,
                dn200=int((pipes.DN_MM == 200).sum()), n_500=len(big), n_500_at_min=big_at_min,
                n_500_trunk=big_trunk)


@lru_cache(None)
def _ch9(inlet):
    """The same pipe as chapter 9 works it: each plot to its nearest street pipe, summed down the tree."""
    import ch04_peak_tiers as c04
    r = c04._net()["up"].loc[inlet]
    c = c04._case(r.Q_ULT, r.PR_ULT, r.LEN)
    return dict(n=int(round(r.ONE)), q_ult=float(r.Q_ULT), pr_ult=float(r.PR_ULT), length=float(r.LEN),
                q_des=(c["qp"] + c["qi"]) / c04.LS)


def _f(x, nd=2):
    return F.fmt(x, nd)


def _sgn(x, nd=1):
    """Signed value with a true minus sign (U+2212)."""
    return ("+" if x >= 0 else "−") + _f(abs(x), nd)


def _caption_no(d, kind, fragment):
    """Number of a caption already in the document whose text holds fragment; None when absent
    (the chapter built on its own)."""
    for par in d.paragraphs:
        t = par.text
        if t.startswith(kind + " ") and fragment in t:
            return t.split()[1]
    return None


# ================================================================== text helpers
def _part(d, lead, text):
    D.rich(d, (lead, {"bold": True}), (text, {}))


def _for(d, t):
    _part(d, "What it is for. ", t)


def _rule(d, t):
    _part(d, "The rule. ", t)


def _src(d, t):
    D.p(d, "Source: " + t, size=9, italic=True, colour=D.GREY, space_after=6)


def _num(d, t):
    _part(d, "Worked Ibri number. ", t)


def _lives(d, t):
    _part(d, "Where it lives. ", t)


def _sym(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)
    D.p(d, "", space_after=2)


def _eq(d, inner):
    n = D.next_eq()
    M.display(d, inner, number=n)
    return n


def _partfull_png():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    Dm, S = bore(200), TABLE11[200] / 1000.0
    Qf, Vf = q_full(Dm, S), v_full(Dm, S)
    ys = [i / 200.0 for i in range(1, 199)]
    qq = [q_part(Dm, S, y) / Qf for y in ys]
    vv = [v_part(Dm, S, y) / Vf for y in ys]
    fig, ax = plt.subplots(figsize=(6.2, 4.4), dpi=200)
    ax.plot(qq, ys, color="#1F3B63", lw=2.0, label="q/Q  (flow ratio)")
    ax.plot(vv, ys, color="#2E629E", lw=1.8, ls="--", label="v/V  (velocity ratio)")
    for lim, txt in ((DOD_SMALL, "d/D 0.65: limit up to 350 mm"),
                     (DOD_LARGE, "d/D 0.50: limit above 350 mm")):
        ax.axhline(lim, color="#8A9BB0", lw=0.9, ls=":")
        ax.text(0.02, lim + 0.012, txt, fontsize=7.5, color="#5A5A5A")
    ax.set_xlim(0, 1.2)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Ratio to the pipe-full value", fontsize=9)
    ax.set_ylabel("Proportional depth d/D", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(color="#E3E8EF", lw=0.6)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ================================================================== the chapter
def c11_gravity(d):
    st = w8_stats()
    T = F.totals()
    J = _json()
    conn = J["rules"]["connection_ratio_2030"]
    low_total = J["low_case_2030_m3d"]
    e1, e2 = example("P-0042"), example("P-0741")
    # The text states each worked pipe's gradient, size and class. A data change that moves one of
    # them out of what the text says fails the build here instead of printing a wrong sentence.
    assert e1["at_min"] and e2["at_min"], "both worked pipes are written as laid at their minimum"
    assert e1["dn"] == 200 and e2["dn"] < DN_TRUNK_STEP, "P-0042 is DN200; both are on the 0.05 % step"
    assert e1["cls"] == "needs washing" and e1["v_low"] < V_MIN and e1["s"] < e1["smin_t"], \
        "P-0042 is written as needs washing at 1 Pa, neither test met: rebuild the example"
    assert all(c == "needs washing" for c in e1["cls_tau"].values()), "P-0042: needs washing at every tau"
    assert e2["cls"] == "tractive pass" and e2["v_low"] < V_MIN, \
        "P-0741 is written as a tractive pass at 1 Pa, velocity not reached: rebuild the example"
    assert e2["cls_tau"][1.5] == "tractive pass" and e2["cls_tau"][2.0] == "needs washing", \
        "P-0741: the text says the class moves at 2 Pa and not at 1.5 Pa"
    assert len(e1["trials"]) == 1 and len(e2["trials"]) > 1 and e2["trials"][-1][4], \
        "sizing: P-0042 is set by the minimum size, P-0741 by the flow"
    # 11.11: every project step is more fall than the 20 mm tolerance over a full-length pipe; a tenth
    # of the minimum is less from DN500 up and more below it
    assert all(step_for(k) * spacing(k) > TOL for k in TABLE11), "11.11: a project step under the tolerance"
    assert all((step_old(k) * spacing(k) < TOL) == (k >= DN_TRUNK_STEP) for k in TABLE11), \
        "11.11 says a tenth of the minimum falls under the 20 mm tolerance exactly from DN500 up"

    D.h(d, 1, "11   Gravity sewer hydraulics", page_break=True)
    D.p(d, "This chapter turns a design flow into a pipe: its diameter, its gradient, its depth and "
           "the chambers along it. It carries every constraint the guideline sets on a gravity "
           "sewer, each with the page it comes from, and it ends with two Ibri pipes sized and "
           "checked rule by rule. Where this project has chosen a value the guideline does not "
           "give, the chapter says so in the same sentence.")
    D.p(d, "Read the force words as the guideline writes them. \"Shall\" is a requirement. \"Should\" "
           "and \"recommended\" are advice. The difference decides what the designer may do when a "
           "rule cannot be met, so it is kept in every table below.")

    # ------------------------------------------------------------------ 11.1
    D.h(d, 2, "11.1   The names of the pipes, and the two flows every pipe carries")
    _for(d, "A rule attaches to a kind of pipe, so the kind has to be named the way the guideline "
            "names it. The minimum gradient of a street sewer and of a lateral sewer differ by a "
            "factor of two, and using the wrong word applies the wrong one.")
    _rule(d, "The guideline has three tiers. The primary network is the trunk mains, which carry "
             "the districts to the plant. The secondary network is the headers and main sewers laid "
             "under the streets: the main sewer is the street pipe every plot connects to, and the "
             "header collects main sewers across a district. The tertiary network is the rider "
             "sewers and lateral sewers, the short pipes from the house connection chamber to the "
             "main sewer, with a lateral no longer than 45 m. A trunk main is further defined as "
             "larger than 800 mm, more than 1,000 m long without connections, upstream of a plant "
             "or main pumping station.")
    D.tab_caption(d, "Pipe tiers in the guideline's words, with the pipes of the test-area design")
    D.table(d, ["Guideline tier", "What it is", "Pipes in the test area"], [
        ["Primary: trunk main", "Carries the districts to the plant",
         F.fmt(st["tiers"].get("trunk main", 0))],
        ["Secondary: header", "Collects main sewers across a district",
         F.fmt(st["tiers"].get("sub main", 0))],
        ["Secondary: main sewer", "The street sewer every plot connects to",
         F.fmt(st["tiers"].get("lateral", 0) + st["tiers"].get("branch", 0))],
        ["Tertiary: rider and lateral sewers", "House connection chamber to the main sewer, "
         "lateral at most 45 m", "not modelled"],
    ], widths=[4.4, 8.6, 3.5], font=9)
    D.p(d, "", space_after=2)
    t_tier = _caption_no(d, "Table", "Tier values in the engine outputs")
    ref_tier = f"Table {t_tier} in section 10.4" if t_tier else "the tier table of section 10.4"
    D.p(d, "The design outputs still carry the older engine's TIER values. The mapping from those "
           f"values to the guideline's names is {ref_tier}, and the pipe counts above are read "
           "through it; it is not repeated here.")
    _rule(d, "Every pipe is checked against two flows. Its size and capacity are set on the "
             "saturation flow Q_ULT of the plots upstream, 100 % connected, peaked and with "
             "infiltration added. Its self-cleansing is checked on the opening-year flow Q_2030 of "
             f"the same plots multiplied by the connection ratio {conn}, peaked per pipe with the "
             "peak formula chosen on the connected property count, and with no infiltration. The two "
             "cases fail in opposite directions: an under-estimate surcharges the pipe, an "
             "over-estimate declares a silting pipe self-cleansing.")
    _src(d, "G203-p17 and p21 (tiers), G203-p22 Table 6 (45 m), G203-p35 via _BRAIN/02 section 3 "
            "(trunk main definition); two flow cases, the connected count and no infiltration in "
            "the low case: project rule (engineer, 2026-09-11), G201-p73 for 100 % coverage at the end "
            "of the period.")
    _num(d, f"Across the study area the sizing case is {F.fmt(T['q_ult'])} m³/d at saturation in "
            f"{T['ultimate']}, and the self-cleansing case is {F.fmt(low_total)} m³/d. Multiplying "
            f"saturation by {conn} instead would give {F.fmt(T['q_ult'] * conn)} m³/d, "
            f"{_f(T['q_ult'] * conn / low_total, 1)} times the flow really expected in 2030, which "
            "is why that shortcut is not used.")
    _lives(d, "Guideline mapping: _BRAIN/02_DESIGN_CRITERIA.md section 2, W14/docs/"
              "DESIGN_FLOWS_FOR_NETWORK.md section 5. Pipe counts: field TIER in W8/shp/W8_pipes.shp. "
              "Flows: fields Q_ULT and Q_2030 in W14/shp/PLOTS_load.shp; the ratio and the totals in "
              "W14/analysis/design_flows.json.")
    D.picture(d, os.path.join(IMG, "F6_gravity.png"), 13.5)
    D.fig_caption(d, "Sizing a gravity run as the guideline sets it: both self-cleansing approaches, "
                     "the steeper gradient governing, then capacity and depth. At the concept stage "
                     "the project lays the G203 Table 11 minimum and uses the tractive force only as "
                     "a check (section 11.7).")

    # ------------------------------------------------------------------ 11.2
    D.h(d, 2, "11.2   Colebrook-White, the design formula")
    _for(d, "It gives the velocity and the capacity of a pipe at a given gradient. Every sizing "
            "check in this chapter, and the guideline's own minimum-gradient table, rests on it.")
    _rule(d, "Gravity sewers shall be designed with a recognised formula, and the guideline names "
             "Colebrook-White and Manning. For Colebrook-White it fixes the roughness at "
             "ks = 1.5 mm for all pipe sizes and materials. The pipe-full velocity is")
    n_cw = _eq(d, M.seq(
        R("V"), M.EQ, R("−2"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S"))), R(" "),
        M.sub(UP("log"), R("10")),
        M.delim(M.seq(
            M.frac(M.sub(R("k"), UP("s")), M.seq(R("3.7"), R("D"))), M.PLUS,
            M.frac(M.seq(R("2.51"), R("ν")),
                   M.seq(R("D"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S")))))), "[", "]")))
    D.p(d, "and the pipe-full flow is velocity times area:")
    n_q = _eq(d, M.seq(M.sub(R("Q"), UP("o")), M.EQ, R("V"), M.TIMES, R("A"), M.EQ, R("V"),
                       M.TIMES, M.frac(M.seq(R("π"), M.sup(R("D"), R("2"))), R("4"))))
    _sym(d, [
        ["V", "pipe-full velocity", "m/s"],
        ["Q o", "pipe-full flow", "m³/s"],
        ["g", "acceleration due to gravity, 9.81", "m/s²"],
        ["D", "pipe internal diameter", "m"],
        ["S", "hydraulic gradient; equal to the pipe gradient in uniform flow", "m/m"],
        ["k s", "roughness, **1.5 mm for all sizes and materials**", "m"],
        ["ν", "kinematic viscosity, **1.141 × 10⁻⁶ at 15 °C**", "m²/s"],
        ["A", "pipe internal cross-sectional area", "m²"]])
    D.p(d, "For a part-full pipe the same law is written on the hydraulic radius, because the "
           "flow no longer fills the circle. With R = D/4 running full, equation "
           f"({n_cw}) becomes")
    n_cwr = _eq(d, M.seq(
        R("V"), M.EQ, R("−2"), M.sqrt(M.seq(R("8"), R("g"), R("R"), R("S"))), R(" "),
        M.sub(UP("log"), R("10")),
        M.delim(M.seq(
            M.frac(M.sub(R("k"), UP("s")), M.seq(R("14.8"), R("R"))), M.PLUS,
            M.frac(M.seq(R("0.6275"), R("ν")),
                   M.seq(R("R"), M.sqrt(M.seq(R("8"), R("g"), R("R"), R("S")))))), "[", "]")))
    D.p(d, "with the geometry of the wetted segment at proportional depth y = d/D:")
    n_seg = _eq(d, M.seq(
        R("θ"), M.EQ, R("2"), M.func("arccos", M.delim(M.seq(R("1"), M.MINUS, R("2"), R("y")))),
        R(",     "), R("A"), M.EQ, M.frac(M.sup(R("D"), R("2")), R("8")),
        M.delim(M.seq(R("θ"), M.MINUS, M.func("sin", R("θ")))),
        R(",     "), R("P"), M.EQ, M.frac(M.seq(R("D"), R("θ")), R("2")),
        R(",     "), R("R"), M.EQ, M.frac(R("A"), R("P"))))
    _sym(d, [
        ["R", "hydraulic radius, flow area over wetted perimeter", "m"],
        ["y", "proportional depth of flow d/D", "—"],
        ["θ", "angle subtended at the centre by the water surface", "rad"],
        ["A, P", "flow area and wetted perimeter at depth d", "m², m"]])
    nu_v = [v_full(0.2, 0.005, nu) for nu in (NU15, NU25, NU35)]
    D.p(d, "Viscosity comes from G203 Table 9, which gives three temperatures and "
           "asks for the 15 °C value in basic design as the conservative one:")
    D.tab_caption(d, "Kinematic viscosity (G203 Table 9, p25), and what it does to one pipe")
    D.table(d, ["Temperature", "ν (m²/s × 10⁻⁶)", "DN200 at 5.00 mm/m, pipe-full velocity"], [
        ["15 °C (design)", "1.141", f"{_f(nu_v[0], 3)} m/s"],
        ["25 °C", "0.897", f"{_f(nu_v[1], 3)} m/s"],
        ["35 °C", "0.727", f"{_f(nu_v[2], 3)} m/s"]], widths=[4.0, 4.5, 8.0], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "The velocity barely moves with temperature. At a roughness of 1.5 mm a sewer runs "
           "almost fully rough, the first term inside the bracket dominates and viscosity hardly "
           "matters. The roughness is the number that carries the design; it is not the roughness "
           "of new plastic but an allowance for slime, grit and age over the life of the sewer.")
    D.callout(d, "Three printing slips in G203 section 4.2.",
              "The pipe-full flow on p24 is printed as velocity divided by area, which has no "
              "meaning as a flow; it is velocity times area, as in equation "
              f"({n_q}). The text on p27 sends the reader to G203 Figure 4 for the d/D against q/Q "
              "relation; that figure is G203 Figure 2 on p28, G203 Figure 4 being air flow. The two "
              f"tractive-force constants on p27 differ by {_f(K_GAP * 100, 1)} % once the units are "
              "converted; section 11.7 says which one this tutorial uses. "
              "None changes a design; each will surface if a calculation is audited against the "
              "page.", fill="EAF1F8", colour=D.MID)
    _src(d, "G203-p24 section 4.2.1 (formula, ks, licensed software), p25 Table 9 (viscosity), "
            "p28 section 4.2.4 (ks repeated).")
    Db = bore(200)
    _num(d, f"A DN200 PVC-U main sewer has a true bore of {_f(Db * 1000, 1)} mm. At the G203 Table 11 "
            f"minimum of 5.00 mm/m, equation ({n_cw}) gives V = {_f(v_full(Db, 0.005), 3)} m/s "
            f"and equation ({n_q}) Q o = {_f(q_full(Db, 0.005) * 1000, 1)} l/s running full. "
            f"On the nominal 200 mm the same gradient gives {_f(v_full(0.2, 0.005), 3)} m/s and "
            f"{_f(q_full(0.2, 0.005) * 1000, 1)} l/s.")
    _lives(d, "W13/py/sewnet/hydra.py, functions v_cw_R, v_full, q_full and solve_dod (the R-form "
              "with the segment geometry); constants KS and NU in W13/py/sewnet/criteria.py; the "
              "true bore in criteria.internal_diameter (PVC-U SN8 taken as SDR 34 up to 315 mm, "
              "GRP nominal above: an assumption until the pipe class is fixed). Results: fields "
              "VEL_MS, DOD and QPEAK_LS in W8/shp/W8_pipes.shp.")

    # ------------------------------------------------------------------ 11.3
    D.h(d, 2, "11.3   Manning, and why the project designs by Colebrook-White")
    _for(d, "Manning is the other formula the guideline accepts, and the hydraulic model exports "
            "use it. The designer needs to know what roughness makes it agree with Colebrook-White.")
    _rule(d, "Manning's formula, as printed, in its velocity, full-bore gradient and flow forms:")
    n_man = _eq(d, M.seq(R("v"), M.EQ, M.frac(R("1"), R("n")),
                         M.sup(R("R"), M.frac(R("2"), R("3"))),
                         M.sup(R("S"), M.frac(R("1"), R("2"))),
                         R(",     "), R("Q"), M.EQ, R("v"), R(" "), R("A")))
    n_mans = _eq(d, M.seq(R("S"), M.EQ, M.frac(M.seq(M.sup(R("v"), R("2")), R(" "),
                                                     M.sup(R("n"), R("2")), R(" "),
                                                     M.delim(R("6.3448"))),
                                               M.sup(R("D"), R("1.333")))))
    _sym(d, [
        ["v", "mean velocity", "m/s"],
        ["n", "Manning roughness coefficient", "—"],
        ["R", "hydraulic radius", "m"],
        ["S", "slope of the energy grade line", "m/m"],
        ["D", "pipe diameter (full-bore form only)", "m"],
        ["Q, A", "flow and flow area", "m³/s, m²"]])
    D.p(d, f"Equation ({n_mans}) is equation ({n_man}) solved for S with R = D/4 running full. The "
           "constant is 4 to the power 4/3, which is 6.350; the printed 6.3448 is a rounding slip "
           "worth under 0.1 %.")
    D.p(d, "G203 Table 8 gives n = 0.009 for plastic, 0.009 to 0.011 for PVC-U and "
           "fibreglass, 0.009 to 0.015 for polyethylene and 0.012 for cement-lined concrete. Those "
           "are clean-pipe values. Colebrook-White at ks = 1.5 mm is an aged-sewer value, and the "
           "guideline makes it mandatory for Colebrook-White. The two only agree if Manning is "
           "given the roughness of an aged sewer, not the roughness of the pipe as delivered.")
    man = {n_: 1.0 / n_ * (0.05 ** (2.0 / 3.0)) * math.sqrt(0.005) for n_ in (0.009, 0.011, 0.013)}
    D.tab_caption(d, "DN200 at 5.00 mm/m running full: Manning against Colebrook-White")
    D.table(d, ["Formula and roughness", "Pipe-full velocity", "Against Colebrook-White"], [
        ["Colebrook-White, ks 1.5 mm", f"{_f(v_full(0.2, 0.005), 3)} m/s", "—"],
        ["Manning, n 0.009 (G203 Table 8, plastic)", f"{_f(man[0.009], 3)} m/s",
         f"{_sgn((man[0.009] / v_full(0.2, 0.005) - 1) * 100, 0)} %"],
        ["Manning, n 0.011", f"{_f(man[0.011], 3)} m/s",
         f"{_sgn((man[0.011] / v_full(0.2, 0.005) - 1) * 100, 0)} %"],
        ["Manning, n 0.013", f"{_f(man[0.013], 3)} m/s",
         f"{_sgn((man[0.013] / v_full(0.2, 0.005) - 1) * 100, 1)} %"]],
        widths=[7.0, 4.5, 5.0], font=9)
    D.p(d, "", space_after=2)
    _src(d, "G203-p24 and p25 (Manning's forms), p23 Table 8 (n), p24 and p28 (ks 1.5 mm for "
            "Colebrook-White).")
    _num(d, f"Manning with the plastic n of 0.009 overstates the DN200 velocity by "
            f"{_f((man[0.009] / v_full(0.2, 0.005) - 1) * 100, 0)} % against the mandated "
            "Colebrook-White basis. A model built that way would pass pipes that silt. The project "
            "designs by Colebrook-White and exports n = 0.013 to Manning-based software, which "
            f"agrees within {_f(abs(man[0.013] / v_full(0.2, 0.005) - 1) * 100, 1)} % at this size.")
    _lives(d, "W13/py/sewnet/criteria.py, MANNING_N_EXPORT = 0.013 (project choice, documented as "
              "the ks-equivalent for the SewerGEMS export); W13/py/sewnet/export_gems.py.")

    # ------------------------------------------------------------------ 11.4
    D.h(d, 2, "11.4   How full a pipe may run, and the part-full relation")
    _for(d, "Capacity is held back at peak flow so that an unusual flow has somewhere to go and "
            "air can move over the water. This is the test that sets the diameter once flows grow.")
    _rule(d, "At peak flow the proportional depth should not exceed the G203 Table 10 value. The "
             "guideline calls these recommended design criteria and defines d/D against the "
             "nominal diameter.")
    D.tab_caption(d, "Recommended depth of flow at peak flow (G203 Table 10, p27)")
    D.table(d, ["Sewer", "Maximum d/D at peak flow"], [
        ["Pipe diameter up to 350 mm", "0.65"], ["Pipe diameter above 350 mm", "0.50"]],
        widths=[8.2, 8.3], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "The flow and velocity a pipe delivers at a given depth follow from equations "
           f"({n_cwr}) and ({n_seg}). The guideline shows the relation as a curve (G203 Figure 2, p28). "
           "Recomputed here with Colebrook-White:")
    Qf, Vf = q_full(Db, 0.005), v_full(Db, 0.005)
    rows = []
    for y in (0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.65, 0.70, 0.80, 0.90, 0.94):
        rows.append([_f(y, 2), _f(q_part(Db, 0.005, y) / Qf, 3), _f(v_part(Db, 0.005, y) / Vf, 3),
                     _f(v_part(Db, 0.005, y), 3)])
    D.tab_caption(d, "Part-full ratios for DN200 PVC-U at 5.00 mm/m, Colebrook-White, ks 1.5 mm")
    D.table(d, ["d/D", "q/Q o", "v/V", "Velocity (m/s)"], rows, widths=[3.5, 4.3, 4.3, 4.4], font=9)
    D.p(d, "", space_after=2)
    D.picture(d, _partfull_png(), 12.5)
    D.fig_caption(d, "Part-full flow and velocity in a circular sewer, recomputed with "
                     "Colebrook-White for DN200 PVC-U at 5.00 mm/m, with the G203 Table 10 limits.")
    y6 = 0.65
    D6 = 0.6
    D.p(d, "Three things to take from the curve. At half depth the flow is exactly half the "
           "pipe-full flow and the velocity equals the pipe-full velocity. The velocity peaks "
           f"near d/D = 0.8, about {_f(max(v_part(Db, 0.005, y / 100) for y in range(60, 95)) / Vf, 2)} "
           "times the full-bore value. The flow peaks near d/D = 0.94 at about "
           f"{_f(q_part(Db, 0.005, 0.94) / Qf, 2)} times, because the last part of the circle adds "
           "more wetted wall than area. The shape hardly depends on size: at DN600 and 1.25 mm/m "
           f"the ratio at d/D 0.65 is {_f(q_part(D6, 0.00125, y6) / q_full(D6, 0.00125), 3)} "
           f"against {_f(q_part(Db, 0.005, y6) / Qf, 3)} here.")
    _src(d, "G203-p27 section 4.2.3 and Table 10; p28 Figure 2.")
    _num(d, f"At d/D 0.65 a DN200 PVC-U pipe at 5.00 mm/m carries {_f(q_part(Db, 0.005, 0.65) * 1000, 1)} "
            "l/s. That is the largest peak it may take at its minimum gradient. In the test area "
            f"the fullest pipe runs at d/D {_f(st['dodmax'], 3)} at the flat-load design flow.")
    _lives(d, "W13/py/sewnet/hydra.py, dod_limit and size_pipe (the smallest diameter whose d/D "
              "at the laid gradient is within the limit); DOD_MAX_SMALL, DOD_MAX_LARGE and "
              "DOD_DN_THRESHOLD in criteria.py. d/D is computed on the true bore, which is the "
              "stricter reading of a limit the guideline states on the nominal diameter.")

    # ------------------------------------------------------------------ 11.5
    D.h(d, 2, "11.5   Velocity: the self-cleansing minimum and the maximum")
    _for(d, "A slow sewer lets solids settle and turn septic; a fast one erodes the pipe, "
            "releases hydrogen sulphide and makes chambers unsafe.")
    _rule(d, "The minimum velocity shall be above 0.75 m/s at peak flow, with 0.90 m/s preferred. "
             "The maximum shall not exceed 3 m/s at the design depth of flow, and the maximum "
             "gradient is the one that respects it. The guideline does not say which year's peak "
             "the minimum applies to. The project tests it on the low case, the opening-year flow "
             f"Q_2030 × {conn}, because that is when silting happens; the maximum is tested on the "
             "sizing flow Q_ULT, because that is when the pipe runs fastest.")
    D.tab_caption(d, "Velocity criteria")
    D.table(d, ["Criterion", "Value", "Condition", "Force", "Source"], [
        ["Self-cleansing velocity", "above 0.75 m/s", "at peak flow", "shall", "G203-p26"],
        ["Preferred velocity", "0.90 m/s", "at peak flow", "preferred", "G203-p26"],
        ["Maximum velocity", "3 m/s", "at the design depth of flow", "shall", "G203-p27"],
        ["Maximum gradient", "the one giving 3.0 m/s", "", "should", "G203-p29"],
        ["Flow for the minimum", f"Q_2030 × {conn}, peaked", "per pipe", "project rule",
         "engineer 2026-09-11"],
        ["Flow for the maximum", "Q_ULT, peaked, with infiltration", "per pipe", "project rule",
         "engineer 2026-09-11"]], widths=[3.6, 3.6, 3.4, 2.4, 3.5], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "The guideline asks for two approaches to self-cleansing together, the velocity and the "
           "minimum tractive force, and the steeper gradient they give governs. At the head of a "
           "system, where 0.75 m/s cannot be reached at all, the tractive force alone sets the "
           "gradient. At the concept stage this project lays the G203 Table 11 gradient and uses the "
           "tractive force only as a check on it; section 11.7 gives the rule and the reason. In the "
           "early years the actual flow is below the design flow; the guideline's answer is more "
           "frequent inspection and cleansing by the operator, and it sets no flow threshold, "
           "frequency or duration.")
    _src(d, "G203-p25 to p27 section 4.2.2.1 (two approaches, steeper governs, head of system), "
            "p27 section 4.2.2.2 (maximum), p28 section 4.2.6 (early low flows), p29 section 4.3.2 "
            "(maximum gradient); flow cases and the concept-stage use of the tractive force: project "
            "rule (engineer, 2026-09-11), the latter a departure recorded in report R2 section 10.1 "
            "for NWS confirmation.")
    _num(d, f"In the test-area design the fastest pipe runs at {_f(st['vmax'], 2)} m/s, a third of "
            "the maximum. On flat ground the maximum never binds; it binds on a steep hillside "
            "street, where the surplus fall is taken as a drop at a chamber instead (section 11.14).")
    _lives(d, "V_SELF_CLEANSING, V_PREFERRED and V_MAX in W13/py/sewnet/criteria.py; hydra.smax_for "
              "(the gradient cap at the design flow). Low-case flows: W14/docs/"
              "DESIGN_FLOWS_FOR_NETWORK.md sections 2 to 4.")

    # ------------------------------------------------------------------ 11.6
    D.h(d, 2, "11.6   Minimum gradient from the self-cleansing velocity: G203 Table 11")
    _for(d, "It gives each diameter the flattest gradient at which it may be laid. On Ibri's flat "
            "ground this table sets most of the network.")
    _rule(d, "The gradient shall be enough to keep the design minimum of 0.75 m/s. G203 Table 11 turns "
             "that velocity into a gradient for each size using Colebrook-White. Sewers shall not "
             "be oversized to allow flatter slopes, and the slope must be uniform between "
             "successive manholes.")
    D.tab_caption(d, "Minimum sewer gradient (G203 Table 11, p29), with the Colebrook-White check")
    rows = []
    for dn, s in TABLE11.items():
        rows.append([("900 and above" if dn == 900 else str(dn)), _f(s, 2), _f(s / 10, 3),
                     F.fmt(1000 / s), _f(v_full(dn / 1000, s / 1000), 3),
                     _f(v_full(bore(dn), s / 1000), 3)])
    D.table(d, ["DN (mm)", "mm/m", "%", "1 in", "V full, nominal D (m/s)",
                "V full, true bore (m/s)"], rows, widths=[2.4, 1.8, 1.8, 1.8, 4.3, 4.4], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "The mm/m column is the guideline's. The next two are the same number in other units. "
           "The last two are equation "
           f"({n_cw}) evaluated at each gradient: on the nominal diameter every row returns "
           f"{_f(min(v_full(dn / 1000, s / 1000) for dn, s in TABLE11.items()), 2)} to "
           f"{_f(max(v_full(dn / 1000, s / 1000) for dn, s in TABLE11.items()), 2)} m/s, so the "
           "table is Colebrook-White at 0.75 m/s running full, on the nominal size.")
    D.callout(d, "G203 Table 11 is a pipe-full gradient, and that matters.",
              "The velocity rule is stated at peak flow, not running full. At the G203 Table 11 gradient "
              f"a pipe reaches {_f(v_part(0.2, 0.005, 0.65), 2)} m/s at d/D 0.65, "
              f"{_f(v_part(0.2, 0.005, 0.50), 2)} m/s at d/D 0.50 and "
              f"{_f(v_part(0.2, 0.005, 0.20), 2)} m/s at d/D 0.20 (DN200, nominal). A residential "
              "main sewer runs near d/D 0.2 for most of its life, so laying to G203 Table 11 is not "
              "compliance by itself; the velocity at the actual flow is what is tested. On the "
              f"true bore of PVC-U the DN200 row gives only {_f(v_full(Db, 0.005), 2)} m/s even "
              "running full.")
    D.p(d, "The ban on oversizing closes the obvious escape on flat ground. A larger pipe has a "
           "flatter minimum, 1.25 mm/m at DN600 against 5.00 mm/m at DN200, so upsizing would keep "
           "a sewer shallow. The guideline forbids it: on flat ground the design accepts the depth "
           "and, when the depth runs out, pumps.")
    _src(d, "G203-p29 section 4.3.1 and Table 11.")
    _num(d, f"{F.fmt(st['at_min'])} of the {F.fmt(st['n_pipes'])} pipes in the test-area design "
            f"are laid at exactly 5.00 mm/m, the DN200 minimum, and the median laid gradient is "
            f"{_f(st['med_grad'], 2)} mm/m. The minimum is the design on this ground.")
    _lives(d, "TABLE11 and TABLE11_FLOOR in W13/py/sewnet/criteria.py; hydra.smin_for still takes "
              "the steeper of G203 Table 11 and the tractive minimum, which the concept stage does not "
              "do (section 11.7), and is to be aligned. The engine's gate reproduces G203 "
              f"Table 11 from equation ({n_cw}) within ±5 % before any design runs. Laid gradient: fields "
              "SLOPE_PMIL and SLOPE_PCT in W8/shp/W8_pipes.shp.")

    # ------------------------------------------------------------------ 11.7
    D.h(d, 2, "11.7   The tractive force: the guideline's second approach, and its use at the concept stage")
    _for(d, "Near the head of a network the flow is too small for any realistic gradient to reach "
            "0.75 m/s. The tractive force asks a different question: does the water drag on the "
            "invert hard enough to move the sediment?")
    _rule(d, "The tractive tension is the weight of the water along the slope divided by the "
             "wetted area it acts on:")
    n_tau = _eq(d, M.seq(R("τ"), M.EQ, M.frac(M.seq(R("W"), R(" "), M.func("sin", R("θ"))),
                                              M.seq(R("p"), R(" "), R("L"))),
                         R(",     "), R("W"), M.EQ, R("ρ"), R("g"), R("a"), R("L"),
                         R("     ⇒     "), R("τ"), M.EQ, R("ρ"), R("g"), R("R"), R(" "),
                         M.func("sin", R("θ")), R(" ≈ "), R("ρ"), R("g"), R("R"), R("S")))
    D.p(d, "Mara, Sleigh and Taylor (2000), cited by the guideline, derived the minimum slope that "
           "moves particles, assuming d/D = 0.2 and n = 0.013:")
    n_mara = _eq(d, M.seq(M.sub(R("S"), UP("min")), M.EQ, R("K"), R(" "),
                          M.sup(R("τ"), R("1.23")), R(" "), M.sup(R("Q"), R("−0.461"))))
    _sym(d, [
        ["τ", "tractive tension (boundary shear stress); 1 Pa at the concept stage", "Pa"],
        ["W", "weight of the water in the length L", "N"],
        ["θ", "angle of the pipe to the horizontal", "rad"],
        ["p, a", "wetted perimeter and flow area", "m, m²"],
        ["L", "length of pipe", "m"],
        ["ρ", "density of the sewage", "kg/m³"],
        ["S min", "minimum slope to move particles", "m/m"],
        ["K", "2.33 × 10⁻⁴, with Q in m³/s: the constant used for every tractive slope here", "—"],
        ["Q", "peak flow in the pipe, the true flow with no floor", "m³/s"]])
    q1 = e1["pk_low"]
    D.p(d, "G203 prints the relation on p27 with two constants, 2.33 × 10⁻⁴ for Q in m³/s and "
           "5.5 × 10⁻³ for Q in l/s. Converted to the same units they are not the same number: the "
           f"l/s constant gives slopes {_f(K_GAP * 100, 1)} % flatter "
           f"({_f(K_LS * q1 ** -0.461 * 1000, 2)} against {_f(smin_tractive(q1) * 1000, 2)} mm/m at "
           f"{_f(q1, 2)} l/s and 1 Pa, the low-case peak of the pipe worked in section 11.16). The "
           "project uses K = 2.33 × 10⁻⁴ with Q in m³/s, the steeper of the two.")
    D.p(d, "The guideline makes the two approaches one rule. Two approaches shall be used, the "
           "self-cleansing velocity and the minimum tractive force, and the steeper gradient the two "
           "give shall be adopted as the minimum pipe gradient. At the head of a system, where "
           "0.75 m/s may not be attainable, the minimum gradient shall be calculated by the tractive "
           "force alone. Read as written, the tractive slope at each pipe's peak flow is a design "
           "gradient, not a check.")
    _rule(d, "At the concept stage this project departs from that. The tractive force sets no "
             "gradient. Every pipe is laid at its G203 Table 11 minimum (G203 Table 5 for a tertiary "
             "pipe, section 11.8), rounded up to the steps of section 11.11, or steeper where the "
             "ground falls faster. The tractive force is used only as the second test of the "
             "self-cleansing audit below. It is applied to the gradients at the preliminary design, "
             "once NWS has confirmed the value of τ. The departure is recorded for NWS confirmation "
             "in section 10.1 of the Concept Design Report, Revision 2.")
    q_tiny = 0.1
    D.p(d, "The reason is that the rule, used to set a gradient, rests on two numbers the guideline "
           "does not give. It gives no design value of τ anywhere in its 201 pages, and the slope "
           "moves with τ to the power 1.23: from 1 to 2 Pa every tractive slope becomes "
           f"{_f(2.0 ** 1.23, 2)} times steeper. And the relation has no floor. As the flow at the "
           "head of a network tends to zero, the slope it asks for grows without bound: "
           f"{_f(smin_tractive(q_tiny) * 1000, 1)} mm/m at {_f(q_tiny, 1)} l/s and 1 Pa, against the "
           f"DN200 minimum of {_f(TABLE11[200], 2)} mm/m. The low-flow threshold of {_f(Q_MARA, 1)} l/s "
           "often quoted with the method would bound it, but it is not in G203: it is the minimum "
           "peak flow of the Mara simplified-sewerage literature, a single WC flush, and the project "
           "does not use it. A gradient set on those two numbers would put the depth of every head "
           "of the network on values NWS has not agreed. And a pipe laid to the guideline's gradient "
           "that still carries too little flow needs washing, not a steeper pipe.")
    D.p(d, "On the low case every pipe takes one of three classes, tested in this order on its true "
           "low-case peak, with no threshold and no floor on the flow.")
    t_cls = D.tab_caption(d, "The three self-cleansing classes, tested on the low-case peak flow")
    D.table(d, ["Class", "Test at the low-case peak", "Action"], [
        ["**Velocity pass**", "at least 0.75 m/s", "none"],
        ["**Tractive pass**", "velocity not reached; laid gradient at least S min of equation "
         f"({n_mara}) at τ = 1 Pa, K 2.33 × 10⁻⁴, Q in m³/s", "none"],
        ["**Needs washing**", "everything else",
         "on the flushing list for the early years (G203 section 4.2.6, p28); not regraded, not "
         "upsized"]], widths=[3.2, 7.3, 6.0], font=9)
    D.p(d, "", space_after=2)
    D.p(d, f"Table {t_cls} has no regrade class, because at this stage no gradient is steepened for "
           "self-cleansing. The class is decided at 1 Pa. How it would move at 1.5 and 2 Pa is shown "
           "for each worked pipe in sections 11.16 and 11.17, for information only.")
    _src(d, "G203-p25 to p27 section 4.2.2.1 (two approaches shall be used, the steeper governs, the "
            "head of a system by tractive force alone), p26 (tractive force, W = ρgaL), p27 (Mara "
            "relation and both constants), p28 section 4.2.6 (more frequent inspection and cleansing "
            "in the early years). Concept-stage rule, the three classes, K in m³/s and no low-flow "
            "threshold: project rule (engineer, 2026-09-11); the concept-stage rule departs from "
            "section 4.2.2.1 and is recorded in report R2 section 10.1 for NWS confirmation. τ = 1 Pa: "
            f"GAP-9, no value in G203, NWS to confirm. {_f(Q_MARA, 1)} l/s: Mara, Sleigh and Taylor "
            "(2000), not in G203, not used.")
    qp1, qp2 = q_at_smin(TABLE11[200] / 1000.0, 1.0), q_at_smin(TABLE11[200] / 1000.0, 2.0)
    _num(d, f"At τ = 1 Pa, equation ({n_mara}) with K = 2.33 × 10⁻⁴ and Q in m³/s equals the DN200 "
            f"minimum of {_f(TABLE11[200], 2)} mm/m at a peak flow of {_f(qp1, 2)} l/s. A DN200 main "
            "sewer laid at its minimum therefore passes the tractive test for any low-case peak above "
            "that flow, and needs washing below it unless it reaches 0.75 m/s. At τ = 2 Pa the same "
            f"gradient needs {_f(qp2, 2)} l/s. τ is the single most sensitive number in the "
            "self-cleansing check, which is why NWS is asked to confirm it and why the class is shown "
            "at three values.")
    _lives(d, "hydra.smin_tractive in W13/tmp3/py/sewnet/hydra.py (the same in W13/py/sewnet/); "
              "TRACTIVE_K = 2.33e-4 and TAU_PA = 1.0 in criteria.py. The engine still floors the flow "
              "at TRACTIVE_QMIN = 0.0015 m³/s, and its smin_for still lays the steeper of G203 Table 11 "
              "and the tractive slope; neither is used at the concept stage, and both are to be "
              "aligned. The classes: W14/docs/DESIGN_FLOWS_FOR_NETWORK.md section 4 and "
              "_BRAIN/02_DESIGN_CRITERIA.md; computed in this chapter by smin_tractive, q_at_smin and "
              "_classify in TUTORIALS/T04/ch05_gravity.py.")

    # ------------------------------------------------------------------ 11.8
    D.h(d, 2, "11.8   Tertiary slopes: G203 Table 5 is not G203 Table 11")
    _for(d, "The short pipes from the property to the main sewer carry almost nothing and are "
            "never self-cleansing by velocity, so the guideline gives them their own, much steeper "
            "range.")
    _rule(d, "G203 Table 5 sets typical slopes for the house connection, rider and lateral sewers.")
    D.tab_caption(d, "Typical pipe slopes for house connection, rider and lateral sewers "
                     "(G203 Table 5, p18)")
    D.table(d, ["Category of sewer", "Network", "Minimum", "Maximum"], [
        ["Property connection sewer", "property connection", "3 %", "10 %"],
        ["Rider sewer", "tertiary", "1 %", "10 %"],
        ["Lateral sewer", "tertiary", "1 %", "10 %"]], widths=[5.0, 4.5, 3.5, 3.5], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "The trap is the DN200 lateral sewer. It is the same size as a main sewer, and G203 Table 11 "
           "would let it lie at 0.5 %. It belongs to the tertiary network, so its minimum is 1 %, "
           "twice as steep. The property connection sewer is at least 150 mm, should not exceed "
           "50 m, and needs 600 mm of cover.")
    _src(d, "G203-p18 Table 4 (property connection sewer, 150 mm, 50 m) and Table 5 (slopes), "
            "p19 section 3.5 (600 mm cover).")
    _num(d, "At concept stage the tertiary network is not laid: each plot is taken to connect to "
            "the main sewer in front of it. The rule enters the design as a depth check, since a "
            "main sewer must be deep enough for a 1 % lateral and a 3 % connection to reach it from "
            "the plot.")
    _lives(d, "PCS_MIN_SLOPE = 0.03, RIDER_MIN_SLOPE = 0.01, PCS_MAX_LEN = 50 m, PCS_MIN_COVER = "
              "0.60 m and LATERAL_MAX_LEN = 45 m in W13/py/sewnet/criteria.py; the connectability "
              "stage, W13/py/sewnet/stages/connectability.py.")

    # ------------------------------------------------------------------ 11.9
    D.h(d, 2, "11.9   Maximum gradient")
    _for(d, "It stops a steep street from producing a pipe that runs faster than 3 m/s.")
    _rule(d, "The maximum gradient should be the one at which the velocity at the design depth of "
             "flow reaches 3.0 m/s. Where the ground falls faster than that, the pipe is laid at or "
             "below the cap and the surplus fall is taken at a chamber as a drop.")
    _src(d, "G203-p27 section 4.2.2.2, p29 section 4.3.2.")
    sv1 = s_vmax(200, e1["q_des"])
    sv2 = s_vmax(e2["dn"], e2["q_des"])

    def _cap(sv):
        return ("is not reached at any gradient below 100 %" if sv is None
                else f"is reached at a gradient of {_f(sv * 100, 1)} %")
    _num(d, f"For the secondary main sewer worked in section 11.16, carrying "
            f"{_f(e1['q_des'], 2)} l/s in DN200, the 3.0 m/s cap {_cap(sv1)}. For the header of "
            f"section 11.17, {_f(e2['q_des'], 1)} l/s in DN{e2['dn']}, it {_cap(sv2)}. Small flows "
            "in small pipes need very steep gradients to reach 3 m/s, so on Ibri's ground the cap "
            "matters mainly for the tertiary pipes, whose 10 % maximum in G203 Table 5 is far below it.")
    _lives(d, "hydra.smax_for in W13/py/sewnet/hydra.py, which also reports when no gradient "
              "satisfies the cap and the pipe must be upsized.")

    # ------------------------------------------------------------------ 11.10
    D.h(d, 2, "11.10   Construction tolerance, and what it does at flat gradients")
    _for(d, "A pipe is set out from its two ends. The design has to leave enough fall that the "
            "contractor's tolerance cannot turn it into a reverse gradient.")
    _rule(d, "Line and level shall not deviate from the contract by more than 20 mm, and the "
             "deviations combined shall not create a reverse gradient. If both ends can be 20 mm "
             "out in opposite directions, a pipe needs more than 40 mm of fall to be sure of "
             "falling:")
    n_tol = _eq(d, M.seq(R("S"), R(" ≥ "), M.frac(M.seq(R("2"), R("δ")), R("L")),
                         R(",     "), R("δ"), M.EQ, R("0.020"), R(" m")))
    _sym(d, [["S", "laid gradient", "m/m"], ["δ", "line and level tolerance, 20 mm", "m"],
             ["L", "pipe length between chambers", "m"]])
    rows = []
    for dn in (200, 315, 400, 600, 900):
        s = TABLE11[dn] / 1000
        L = 100 if dn <= 315 else 120
        rows.append([str(dn), _f(s * 1000, 2), str(L), F.fmt(s * L * 1000), _f(TOL / (s * L) * 100, 1),
                     _f(2 * TOL / s, 1)])
    D.tab_caption(d, "The 20 mm tolerance against the fall of a full-length pipe at its minimum gradient")
    D.table(d, ["DN (mm)", "G203 Table 11 (mm/m)", "Maximum spacing (m)", "Fall over it (mm)",
                "20 mm as share of fall (%)", "Shortest pipe with 40 mm fall (m)"],
            rows, widths=[1.8, 2.4, 2.6, 2.6, 3.4, 3.7], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "On a DN200 street pipe the tolerance is a small share of the fall. At trunk sizes it "
           "is not: a DN900 at 0.75 mm/m falls 90 mm in 120 m, and 20 mm is more than a fifth of "
           "it. Short pipes at flat trunk gradients carry the real risk, which is why any pipe whose "
           "fall would be under 40 mm is steepened until it passes, whatever its minimum. The "
           "gradient steps of section 11.11 are chosen against the same tolerance.")
    _src(d, "G203-p29 section 4.3.1.")
    _num(d, "The rule matters most at the joins onto the main pipe and on any future primary trunk "
            "main, where gradients are near 1 mm/m. In the local network it is almost never "
            "binding: a DN200 pipe at 5.00 mm/m has 40 mm of fall after 8 m.")
    _lives(d, "FALL_TOLERANCE = 0.040 m (two times 20 mm) in W13/py/sewnet/criteria.py; "
              "stages/hydraulic.py steepens any pipe whose fall would be below it, and "
              "stages/audit.py checks every pipe.")

    # ------------------------------------------------------------------ 11.11
    D.h(d, 2, "11.11   Gradient steps: 0.05 % for secondary pipes, 0.025 % for trunks")
    _for(d, "The gradient on the drawing must be the gradient the invert levels came from, and one "
            "a contractor can set out. A computed 6.911 mm/m is neither.")
    _rule(d, "Every pipe is laid at a whole number of gradient steps. The step is 0.05 % (0.5 mm/m) "
             "for secondary pipes and 0.025 % (0.25 mm/m) for primary trunks of DN500 and above. The "
             "design engine sets the step by size, which comes to the same thing: the secondary "
             "network usually runs from 200 to 400 mm (section 11.12), so a pipe of DN500 or more "
             "is a trunk. At the concept stage the required gradient is the G203 Table 11 minimum "
             "of the size (G203 Table 5 for a tertiary pipe), or the fall of the ground where it is "
             "steeper, and it is rounded up to the next step, since rounding down would breach the "
             "minimum. Along a street run one gradient is held until the cover is no longer enough; "
             "it changes only at a junction, or where holding it would breach the minimum cover or "
             "the maximum depth. The diameter is earned by the flow; it is never chosen to flatten "
             "the gradient.")
    n_round = _eq(d, M.seq(M.sub(R("S"), UP("laid")), M.EQ,
                           M.delim(M.frac(M.sub(R("S"), UP("req")), R("ΔS")), "⌈", "⌉"),
                           R(" "), R("ΔS")))
    _sym(d, [["S laid", "gradient laid and drawn", "m/m"],
             ["S req", "gradient required: the G203 Table 11 minimum of the size at the concept "
                       "stage, or the fall of the ground where it is steeper", "m/m"],
             ["ΔS", f"gradient step: {_f(STEP, 4)} (0.05 %) below DN{DN_TRUNK_STEP}, "
                    f"{_f(STEP_TRUNK, 5)} (0.025 %) at DN{DN_TRUNK_STEP} and above", "m/m"]])
    rows = []
    for dn, s in TABLE11.items():
        g = round_up_step(s / 1000, dn) * 1000
        rows.append([("900 and above" if dn == 900 else str(dn)), _f(s, 2), _f(step_for(dn) * 1000, 2),
                     _f(g, 2), _f((g / s - 1) * 100, 0), str(spacing(dn)),
                     F.fmt(step_for(dn) * spacing(dn) * 1000)])
    t_steps = D.tab_caption(d, "G203 Table 11 minima laid on the project's gradient steps")
    D.table(d, ["DN (mm)", "G203 Table 11 (mm/m)", "Step (mm/m)", "Laid minimum (mm/m)",
                "Extra fall (%)", "Maximum spacing (m)", "One step over it (mm)"],
            rows, widths=[2.3, 2.6, 2.0, 2.6, 2.1, 2.5, 2.4], font=9)
    D.p(d, "", space_after=2)
    exact = [k for k in TABLE11 if k >= DN_TRUNK_STEP
             and abs(round_up_step(TABLE11[k] / 1000, k) * 1000 - TABLE11[k]) < 1e-9]
    up = [k for k in TABLE11 if k >= DN_TRUNK_STEP and k not in exact]
    D.p(d, f"Table {t_steps} applies equation ({n_round}) to every size at its minimum. Below "
           f"DN{DN_TRUNK_STEP} one step is {_f(STEP * 1000, 1)} mm/m, {F.fmt(STEP * 100 * 1000)} mm of "
           f"fall over a full 100 m pipe; from DN{DN_TRUNK_STEP} up it is {_f(STEP_TRUNK * 1000, 2)} "
           f"mm/m, {F.fmt(STEP_TRUNK * 120 * 1000)} mm over 120 m. Both are more than the 20 mm line and "
           "level tolerance of section 11.10, so every step is a gradient the contractor can "
           "actually build. At trunk sizes "
           + (", ".join(f"DN{k}" for k in exact[:-1]) + " and " if len(exact) > 1 else "")
           + f"DN{exact[-1]} lie exactly on their minimum, and "
           + " and ".join(f"DN{k} rounds up to {_f(round_up_step(TABLE11[k] / 1000, k) * 1000, 2)}"
                          for k in up) + " mm/m.")
    rows = []
    for dn in [k for k in TABLE11 if k >= DN_TRUNK_STEP]:
        g, gw, so = round_up_step(TABLE11[dn] / 1000, dn) * 1000, round_up(TABLE11[dn] / 1000) * 1000, \
            step_old(dn) * 1000
        rows.append([("900 and above" if dn == 900 else str(dn)), _f(g, 2), _f(gw, 2),
                     F.fmt((gw - g) * 1000), _f(so, 3), _f(so * spacing(dn), 1)])
    t_alt = D.tab_caption(d, "The trunk sizes on the two steps not adopted: one 0.05 % grid for every "
                             "size, and a tenth of each size's minimum")
    D.table(d, ["DN (mm)", "Laid minimum, project step (mm/m)", "On one 0.05 % grid (mm/m)",
                "Extra depth per km on the grid (mm)", "A tenth of the minimum (mm/m)",
                "That step over 120 m (mm)"], rows, widths=[2.2, 3.0, 2.7, 3.0, 2.8, 2.8], font=9)
    D.p(d, "", space_after=2)
    g900 = round_up(TABLE11[900] / 1000) * 1000
    so900 = step_old(900) * 1000
    D.p(d, f"Table {t_alt} shows the two ways of stepping that this rule replaced. One 0.05 % grid for "
           f"every size is the project step below DN{DN_TRUNK_STEP}, but at trunk sizes it lays a "
           f"DN900 at {_f(g900, 2)} instead of {_f(TABLE11[900], 2)} mm/m, which sinks the DN900 "
           f"{F.fmt((g900 - TABLE11[900]) * 1000)} mm deeper per kilometre on flat ground. A step of a "
           "tenth of each size's minimum lays every size exactly on G203 Table 11, but from "
           f"DN{DN_TRUNK_STEP} up one such step changes the fall of a full-length pipe by less than the "
           f"20 mm tolerance, {_f(so900 * spacing(900), 1)} mm at DN900, so two neighbouring gradients "
           "cannot be told apart once built, and the profiles fill with values such as "
           f"{_f(TABLE11[900] + so900, 3)} mm/m that nobody reads off a drawing.")
    _src(d, "project rule (engineer, 2026-09-11): 0.05 % steps for secondary pipes and 0.025 % for "
            "primary trunks of DN500 and above, laid at the G203 Table 11 minimum at the concept "
            "stage. It replaced a step of a tenth of each size's minimum (W13 design-logic rule 8, "
            "2026-09-07, superseded) and a single 0.05 % grid for all sizes (engineer, 2026-08-23). "
            "G203-p29 (20 mm tolerance; uniform slope between manholes), p30 Table 12 (spacing), "
            "p23 (secondary network 200 to 400 mm); the guideline sets no rounding.")
    bd = st["by_dn"]
    diff = "; ".join(f"DN{k} at {_f(bd[k][2], 2)} mm/m, which the project step lays at "
                     f"{_f(round_up_step(TABLE11[k] / 1000, k) * 1000, 2)}"
                     for k in sorted(bd) if k >= DN_TRUNK_STEP and k in TABLE11)
    on_trunk = ("all of them on the trunk" if st["n_500_trunk"] == st["n_500"] else
                f"{F.fmt(st['n_500_trunk'])} of them on the trunk")
    _num(d, f"The test-area design was laid on one 0.05 % grid for every size and has {st['grads']} "
            f"distinct gradients across {F.fmt(st['n_pipes'])} pipes. Below DN{DN_TRUNK_STEP} the grid "
            f"is the project step, so its {F.fmt(st['n_pipes'] - st['n_500'])} pipes below "
            f"DN{DN_TRUNK_STEP} are already laid as the rule asks. It has {F.fmt(st['n_500'])} pipes of "
            f"DN{DN_TRUNK_STEP} and above, {on_trunk}, and {F.fmt(st['n_500_at_min'])} sit on the grid's "
            f"minimum ({diff}). When the grid was introduced its cost was measured at 1.0 % more "
            "excavation, 0.12 m on the deepest chamber and no extra pumping station, with 448 "
            "distinct gradients reduced to 103.")
    _lives(d, "The rule: _BRAIN/02_DESIGN_CRITERIA.md (gradients at the concept stage) and "
              "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md section 4; W13/docs/W13_DESIGN_LOGIC.md rule 8 "
              "keeps the superseded step with the note that replaced it. The engine still lays one "
              "0.05 % step for every size: SLOPE_STEP = 0.0005 in W13/tmp3/py/sewnet/criteria.py (the "
              "same in W13/py/sewnet/criteria.py), applied in stages/hydraulic.py, with the grid's "
              "measured cost in its ASSUMPTIONS register; it is to be set by pipe size, 0.00025 at "
              "DN500 and above. The steps in this chapter are computed by step_for and round_up_step "
              "in TUTORIALS/T04/ch05_gravity.py. Fields SLOPE_PMIL and SLOPE_PCT on every pipe output "
              "carry the laid gradient.")

    # ------------------------------------------------------------------ 11.12
    D.h(d, 2, "11.12   Pipe sizes and materials")
    _for(d, "It sets the smallest pipe each tier may use, and what it may be made of.")
    _rule(d, "G203 Table 6 sets minimum sizes by outside diameter and the materials for open trench and "
             "trenchless work. The secondary network usually runs from 200 to 400 mm, and the "
             "guideline states that 400 mm is not a mandatory ceiling.")
    D.tab_caption(d, "Minimum sizes and materials (G203 Table 6, p22)")
    D.table(d, ["Category", "Size", "Open trench", "Trenchless"], [
        ["Rider sewer, property connection sewer", "OD 160 mm minimum", "PVC-U, HDPE",
         "GRP, HDPE, PVC-U"],
        ["Lateral sewer, maximum length 45 m", "OD 200 mm minimum", "PVC-U, HDPE, GRP",
         "GRP, HDPE, PVC-U"],
        ["Main sewer", "OD 200 mm minimum to 300 mm", "PVC-U (up to 250 mm), HDPE, GRP",
         "GRP, HDPE, PVC-U"],
        ["Main sewer", "350 mm and above", "GRP, HDPE, GRP/PVC, lined RCC", "GRP, HDPE"]],
        widths=[4.6, 3.6, 4.4, 3.9], font=9)
    D.p(d, "", space_after=2)
    D.bullet(d, "G203 Table 6 puts the 45 m limit in the row heading of the lateral sewer; G203 section 3.2 "
                "on p17 attaches it to riders and laterals together. The project takes the "
                "conservative reading and applies 45 m to both.", lead="The 45 m limit is easy to miss. ")
    D.bullet(d, "PVC-U is named by its outside diameter, GRP by its inside. A DN200 PVC-U pipe "
                f"passes water through about {_f(Db * 1000, 0)} mm. Sizing on the name overstates "
                f"the capacity of every plastic pipe: {_f(q_full(0.2, 0.005) * 1000, 1)} against "
                f"{_f(q_full(Db, 0.005) * 1000, 1)} l/s running full at 5.00 mm/m.",
             lead="The name is not the bore. ")
    D.bullet(d, "Trenchless work is used only where a trench is not feasible, with NWS approval; "
                "at major road crossings possible settlement can decide the method.",
             lead="Trenchless is the exception. ")
    _src(d, "G203-p17 section 3.2, p21 section 4.1, p22 Table 6, p23 (secondary range).")
    _num(d, f"In the test-area design {F.fmt(st['dn200'])} of {F.fmt(st['n_pipes'])} pipes are "
            "DN200: in a residential network the size is set by the minimum, not by the flow.")
    _lives(d, "DN_SERIES, DN_MIN_MAIN = 200, DN_TERTIARY = 160, internal_diameter and material in "
              "W13/py/sewnet/criteria.py; field MAT on every pipe.")

    # ------------------------------------------------------------------ 11.13
    D.h(d, 2, "11.13   Cover and the maximum depth")
    _for(d, "Minimum cover protects the pipe and keeps it clear of other services. Maximum depth "
            "is what ends a gravity system: past it, the sewage is pumped.")
    _rule(d, "The minimum depth shall be 1.3 m to the crown. Where circumstances force less, "
             "concrete protection is required and the cover over pipe and protection together "
             "shall be at least 0.5 m; the 0.5 m is a conditional exception, not a floor. A 3 m "
             "horizontal clearance from other utilities is required. For the maximum, the "
             "guideline recommends approximately 10 to 12 m of cover, requires deeper pipes to be "
             "investigated with the manufacturer, and tells the Engineer to incorporate pumping "
             "stations where excavation cost becomes prohibitive.")
    D.p(d, "This project holds 12 m as a hard limit with no exceptions. It applies to every "
           "chamber and to the trench between chambers, and it is measured from ground to invert, "
           "which is stricter than cover by the pipe's outside diameter. Where a gravity sewer "
           "would pass 12 m, a pumping station goes in before that point: the sewage is lifted "
           "and the pipe restarts at normal cover. Pumps are not removed by digging deeper, and no "
           "area is exempted by calling it a pumping pocket. The guideline's real trigger is cost, "
           "and until the options are costed the project does not claim the licence the cost test "
           "would give. The rising main from each station is sized on the pump duty, not on the "
           "arriving gravity flow: at least 0.75 m/s at design minimum flow (1.0 m/s for "
           "intermittent, start-stop pumping; 1.2 m/s in a vertical main) and at most 2.5 m/s "
           "(G203-p50 section 8.1). The 3.0 m/s maximum of section 11.5 belongs to the gravity "
           "sewer, not to the rising main.")
    D.p(d, "Depth accumulates wherever the ground falls more slowly than the pipe must. Starting "
           "at minimum depth, the distance a sewer can travel before it reaches the limit is")
    n_depth = _eq(d, M.seq(M.sub(R("L"), UP("max")), M.EQ,
                           M.frac(M.seq(M.sub(R("h"), UP("max")), M.MINUS, M.sub(R("h"), UP("0"))),
                                  M.seq(R("S"), M.MINUS, M.sub(R("i"), UP("g"))))))
    _sym(d, [["L max", "distance to the depth limit", "m"],
             ["h max", "depth limit, ground to invert: 12 m", "m"],
             ["h 0", "starting depth: 1.3 m cover + outside diameter + bedding", "m"],
             ["S", "laid gradient", "m/m"],
             ["i g", "ground fall along the route (zero on flat ground, negative uphill)", "m/m"]])
    h0 = MIN_COVER + 0.200 + WALL
    Lmax = (MAX_DEPTH - h0) / 0.005
    _src(d, "G203-p33 section 4.6.3 (1.3 m, 0.5 m with protection, 3 m, approximately 10 to 12 m, "
            "manufacturer, pumping on cost); 12 m hard limit: project doctrine (PROJECT_STATE "
            "section 2 item 3, settled 2026-08-19; standing decision 2026-09-07 until costing "
            "exists); rising main velocity G203-p50 section 8.1.")
    _num(d, f"A DN200 main sewer starting at {_f(h0, 2)} m to invert and laid at 5.00 mm/m across "
            f"flat ground reaches 12 m after {F.fmt(Lmax)} m. On a rising street it gets there "
            f"sooner, by the rise. The test-area design stays inside the limit with its deepest "
            f"chamber at {_f(st['deepest'], 2)} m and {st['pumps']} pumping stations, over "
            f"{_f(st['km'], 1)} km and {F.fmt(st['chambers'])} chambers.")
    _lives(d, "MIN_COVER_CROWN = 1.3, MAX_DEPTH = 12.0, WALL_ALLOW = 0.05 and invert_depth_min in "
              "W13/py/sewnet/criteria.py; the hard limit in stages/hydraulic.py and the check of "
              "every chamber and every trench in stages/audit.py; fields DEPTH and IS_PUMP in "
              "W8/shp/W8_manholes.shp.")

    # ------------------------------------------------------------------ 11.14
    D.h(d, 2, "11.14   Manholes: where, how far apart, drops and the inlet angle")
    _for(d, "Chambers give access for cleaning and control every change in the flow. Their "
            "spacing, their drops and the angle at which pipes enter them decide whether the "
            "network can be maintained and whether solids drop out at the junctions.")
    _rule(d, "Manholes shall be provided at every change of gradient, every change of diameter, "
             "every junction of two or more pipes, at regular spacing on straight lines, and at "
             "the end of each lateral sewer. G203 Table 12 gives the recommended maximum spacing, and "
             "any alteration needs NWS pre-approval.")
    D.tab_caption(d, "Maximum spacing between manholes (G203 Table 12, p30)")
    D.table(d, ["Pipe diameter (mm)", "Maximum spacing (m)"],
            [[a, str(b)] for a, b in TABLE12], widths=[8.2, 8.3], font=9)
    D.p(d, "", space_after=2)
    _rule(d, "Where a pipe arrives more than 600 mm above the outgoing invert, a backdrop is "
             "required and shall be built outside the manhole. Internal backdrops are allowed only "
             "for new connections to existing manholes where an external one is not practicable, "
             "and never in a manhole under 1.5 m in diameter. A backdrop should be no higher than "
             "2 m; beyond that a vortex drop shaft should be used. At a property connection, falls "
             "over 600 mm are not permitted and a backdrop goes outside the manhole.")
    D.tab_caption(d, "Drops at a chamber (G203 p30 and p19)")
    D.table(d, ["Invert difference", "What is required", "Force"], [
        ["Up to 600 mm", "within the chamber, by benching and channels", "—"],
        ["More than 600 mm", "a backdrop, built outside the manhole", "shall"],
        ["More than 2 m", "a vortex drop shaft", "should"]], widths=[4.0, 9.0, 3.5], font=9)
    D.p(d, "", space_after=2)
    _rule(d, "Benching and channels shall give smooth transitions, and no inlet pipe shall have an "
             "angle less than 90° to the direction of flow. The project reads the angle between "
             "the incoming and the outgoing pipe at the chamber: 180° is straight through, 90° a "
             "square junction, and less than 90° means the incoming flow is turned back on itself, "
             "where solids drop out. Where a street meets at a bad angle, a bend chamber goes a few "
             "metres short of the junction so the turn is made in two halves; where there is no "
             "room (2 m clear of plots, 3 m between chambers) the junction is flagged for a "
             "purpose-made chamber with a curved channel.")
    _src(d, "G203-p29 and p30 section 4.4 (locations, drops, inlet angle, Table 12); p19 section "
            "3.6 (property connections); practice at bad angles: PROJECT_STATE section 2 item 6.")
    lens = st["by_dn"]
    worst = max(((k, v[1]) for k, v in lens.items()), key=lambda kv: kv[1] / (100 if kv[0] <= 315 else 120))
    _num(d, f"In the test-area design the longest pipe is {_f(worst[1], 1)} m at DN{worst[0]}, "
            f"within G203 Table 12. {F.fmt(st['drops_back'])} chambers receive a pipe more than 600 mm "
            f"above the outgoing invert and so need an external backdrop; "
            f"{F.fmt(st['drops_vortex'])} of those drops exceed 2 m and need a vortex drop shaft"
            + (f" (the engine's VORTEX field flags {F.fmt(st['vortex_field'])}; the extra one, "
               + ", ".join(f"{lab}, drops exactly {dr:.2f} m" for lab, dr in st['vortex_extra'])
               + ")" if st['vortex_field'] != st['drops_vortex'] else "") + ". "
            f"{F.fmt(st['sharp'])} chambers are flagged for a curved-channel chamber because an "
            "inlet arrives under 85°.")
    D.callout(d, "The inlet angle is a stated deviation in the engine.",
              "The guideline says 90°. The engine accepts 85°, because "
              "enforcing 90° exactly added roughly 200 chambers purely to turn the flow, with no "
              "construction benefit; anything sharper is flagged for a curved-channel chamber, "
              "never fixed by adding a chamber. The deviation has to be carried to the "
              "deliverable as a deviation, not presented as compliance.")
    _lives(d, "mh_max_spacing, MH_SPLIT_LEN = 100 m, DROP_TRIGGER = 0.60 m, BACKDROP_MAX = 2.0 m "
              "and INLET_MIN_DEG = 85 (stated deviation, engineer 2026-08-20, recorded in the "
              "ASSUMPTIONS register) in W13/py/sewnet/criteria.py; fields N_DROPS and VORTEX in "
              "W8/shp/W8_manholes.shp, DROP_DN on each pipe, and the flagged chambers in "
              "W8/shp/W8_sharp_inlets.shp.")

    # ------------------------------------------------------------------ 11.15
    D.h(d, 2, "11.15   What NAMA's built network confirms")
    _for(d, "A rule set can be self-consistent and still produce a network no designer would draw. "
            "The as-built network inside the test area is the check against real practice.")
    _rule(d, "Compare the design with the as-built on the measures the rules control, and read "
             "the result for what it can and cannot show.")
    D.tab_caption(d, "Design against the as-built network, test area")
    D.table(d, ["Measure", "NAMA as-built", "Design run compared", "Reading"], [
        ["Median laid gradient", "4.98 mm/m", "5.00 mm/m", "matches"],
        ["Median depth", "1.92 m", "1.75 m", "matches"],
        ["90th percentile depth", "4.58 m", "5.02 m", "matches"],
        ["Share deeper than 6 m", "1.4 %", "6.1 %", "the design digs deeper more often"],
        ["Median manhole spacing", "29.8 m", "43.4 m", "the design is wider"]],
        widths=[4.4, 3.4, 3.4, 5.3], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "The gradients and depths say the minimum-gradient and cover rules behave the way a "
           "real designer's did. Two further lessons came out of the comparison. Tighter manhole "
           "spacing was tested as a way to keep trenches shallower and it does not: the depth is "
           "set by the gradient, not by the chambers. And the averages are blind to the layout: "
           "in the built network most street sewers drain into another street sewer and only "
           "about sixteen pipes touch the trunk, a hierarchy none of these statistics can see. "
           "Matching the hydraulics says nothing about whether the layout is buildable.")
    _src(d, "W7/docs/CALIBRATION_vs_EXISTING.md (3,267 as-built pipes with levels); "
            "W8/docs/LEARNING_FROM_ASBUILT.md (hierarchy).")
    _num(d, f"The live test-area design has a median laid gradient of {_f(st['med_grad'], 2)} mm/m "
            "against 4.98 mm/m as built.")
    _lives(d, "The calibration and the hierarchy study are the two documents above; the design "
              "figures in the table are the run they record, and the median gradient is read "
              "from W8/shp/W8_pipes.shp.")

    # ------------------------------------------------------------------ 11.16
    _worked(d, "11.16", "Worked example 1: a secondary main sewer", e1, first=True,
            n_mara=n_mara, n_cwr=n_cwr)
    # ------------------------------------------------------------------ 11.17
    _worked(d, "11.17", "Worked example 2: a header", e2, first=False,
            n_mara=n_mara, n_cwr=n_cwr)

    # ------------------------------------------------------------------ 11.18
    D.h(d, 2, "11.18   Every constraint in one place")
    D.p(d, "Requirements of the guidelines, with the page each comes from and the force of its "
           "wording. Project decisions follow in a separate table so the two can never be "
           "confused.")
    D.tab_caption(d, "Guideline constraints on a gravity sewer")
    D.table(d, ["Constraint", "Value", "Force", "Source"], [
        ["Design formula", "Colebrook-White or Manning; licensed software", "shall", "G203-p24"],
        ["Colebrook-White roughness", "ks 1.5 mm, all sizes and materials", "shall", "G203-p24, p28"],
        ["Kinematic viscosity", "1.141 × 10⁻⁶ m²/s at 15 °C", "should", "G203-p25 Tab 9"],
        ["Manning n", "0.009 to 0.015 by material", "typical", "G203-p23 Tab 8"],
        ["Self-cleansing velocity", "above 0.75 m/s at peak flow", "shall", "G203-p26"],
        ["Preferred velocity", "0.90 m/s", "preferred", "G203-p26"],
        ["Two approaches", "velocity and tractive force; steeper governs", "shall", "G203-p25 to p27"],
        ["Head of system", "tractive force alone", "shall", "G203-p27"],
        ["Tractive relation", "S min = K τ^1.23 Q^−0.461; K 2.33 × 10⁻⁴ (Q in m³/s) or "
         f"5.5 × 10⁻³ (Q in l/s), {_f(K_GAP * 100, 1)} % apart", "method", "G203-p27"],
        ["Maximum velocity", "3 m/s at the design depth of flow", "shall", "G203-p27"],
        ["Maximum gradient", "the one giving 3.0 m/s", "should", "G203-p29"],
        ["Depth of flow at peak", "d/D 0.65 up to 350 mm, 0.50 above", "recommended", "G203-p27 Tab 10"],
        ["Part-full relation", "d/D against q/Q", "figure", "G203-p28 Fig 2"],
        ["Early low flows", "more frequent inspection and cleansing", "should", "G203-p28"],
        ["Minimum gradient by size", "G203 Table 11, 5.00 to 0.75 mm/m", "shall", "G203-p29 Tab 11"],
        ["No oversizing for flatter slopes", "prohibited", "shall", "G203-p29"],
        ["Uniform slope between manholes", "required", "must", "G203-p29"],
        ["Line and level tolerance", "20 mm, never a reverse gradient", "shall", "G203-p29"],
        ["Tertiary slopes", "connection 3 to 10 %; rider, lateral 1 to 10 %", "typical", "G203-p18 Tab 5"],
        ["Property connection sewer", "150 mm minimum, 50 m maximum", "should", "G203-p18 Tab 4"],
        ["Property connection cover", "600 mm minimum", "required", "G203-p19"],
        ["Minimum sizes", "OD 160 rider and connection; OD 200 lateral and main", "table", "G203-p22 Tab 6"],
        ["Lateral sewer length", "45 m maximum", "table", "G203-p17, p22 Tab 6"],
        ["Secondary network size", "200 to 400 mm, 400 not mandatory", "usual", "G203-p23"],
        ["Minimum cover", "1.3 m to crown", "shall", "G203-p33"],
        ["Shallower than 1.3 m", "concrete protection, 0.5 m over pipe and protection", "shall", "G203-p33"],
        ["Horizontal clearance", "3 m", "required", "G203-p33"],
        ["Maximum cover", "approximately 10 to 12 m", "recommended", "G203-p33"],
        ["Beyond it", "investigate with manufacturer; pump where excavation cost is prohibitive",
         "shall", "G203-p33"],
        ["Manhole locations", "gradient, diameter, junction, regular spacing, end of lateral",
         "shall", "G203-p29, p30"],
        ["Manhole spacing", "G203 Table 12: 100, 120, 150, 200 m", "recommended", "G203-p30 Tab 12"],
        ["Altering the spacing", "NWS pre-approval", "has to", "G203-p30"],
        ["Backdrop", "above 600 mm, outside the manhole", "shall", "G203-p30"],
        ["Backdrop height", "2 m, then vortex drop shaft", "should", "G203-p30"],
        ["Internal backdrops", "not in manholes under 1.5 m diameter", "not permitted", "G203-p30"],
        ["Inlet angle", "not less than 90° to the direction of flow", "shall", "G203-p19, p30"],
        ["Wadis and washout areas", "pipes and chambers avoided", "must, shall", "G203-p30, p33"],
        ["Access", "24 hours, 7 days to pipes and chambers", "shall", "G203-p33"],
        ["Corridor width", "2.00 m for 200 to 500 mm; 2.80 m for 600 to 900 mm", "indicative",
         "G203-p32, p33 Tab 13"],
        ["Peak factor, over 100 properties", "Merrimack, Q pdf = 2.65 Q adf^0.879 (Ml/d)", "is to be used",
         "G201-p71"],
        ["Peak factor, alternative", "Peltier, 1.5 + 1/√Q m (l/s)", "method", "G201-p72"],
        ["Peak factor ceiling", "5.0", "recommended", "G201-p72"],
        ["Infiltration, new networks", "720 l/d per km of sewer", "should", "G201-p72"],
        ["Coverage at end of period", "100 %", "assumed", "G201-p73"]],
        widths=[4.2, 6.6, 2.3, 3.4], font=8.5)
    D.p(d, "", space_after=2)
    D.tab_caption(d, "Project decisions the guideline does not make")
    D.table(d, ["Question", "Guideline gives", "Project decision", "Source"], [
        ["Which flow sizes the pipe", "nothing", "Q_ULT, saturation, 100 % connected", "engineer 2026-09-11"],
        ["Which flow tests self-cleansing", "\"at peak flow\"", f"Q_2030 × {conn}, peaked per pipe",
         "engineer 2026-09-11"],
        ["Peak factor at 100 properties or fewer", "no formula stated for that range",
         "Peltier", "engineer 2026-09-11"],
        ["Property count that picks the low-case formula", "nothing",
         f"connected: properties of 2030 × {conn}", "engineer 2026-09-11"],
        ["Infiltration in the low case", "silent (G201-p72); self-cleaning at the initial stage of "
         "operations (G201-p73)", "left out", "engineer 2026-09-11"],
        ["Minimum gradient at the concept stage", "the steeper of velocity and tractive force, "
         "\"shall\"", "G203 Table 11 (Table 5 for tertiary pipes); the tractive force only checks it",
         "engineer 2026-09-11; departure, report R2 section 10.1, NWS to confirm"],
        ["Self-cleansing classes", "nothing", "velocity pass, tractive pass, needs washing; no regrade",
         "engineer 2026-09-11"],
        ["Tractive constant", f"two, {_f(K_GAP * 100, 1)} % apart", "K = 2.33 × 10⁻⁴ with Q in m³/s",
         "engineer 2026-09-11"],
        ["Tractive tension τ", "method and constant only", "1 Pa at the concept stage; the class is "
         "decided at 1 Pa and shown at 1.5 and 2 Pa", "GAP-9; NWS to confirm"],
        ["Low-flow threshold", "nothing", f"none: {_f(Q_MARA, 1)} l/s is not in G203 and is not used",
         "engineer 2026-09-11"],
        ["Maximum depth", "approximately 10 to 12 m cover, recommended",
         "12 m ground to invert, hard, no exceptions", "PROJECT_STATE 2 item 3"],
        ["Gradient steps", "nothing", "0.05 % for secondary pipes, 0.025 % for trunks of DN500 and "
         "above; the test-area design and the engine lay 0.05 % at every size, to be set by size",
         "engineer 2026-09-11"],
        ["Engine TIER values lateral and branch", "—", "secondary main sewer", "engineer 2026-09-11"],
        ["Inlet angle in the engine", "90°", "85°, stated deviation, sharper flagged", "engineer 2026-08-20"],
        ["Rider length", "45 m on the lateral row", "45 m on riders as well", "02 section 6"],
        ["True bore of PVC-U", "OD-designated sizes", "SDR 34 (SN8) until the pipe class is fixed",
         "assumption"]],
        widths=[4.0, 4.0, 5.2, 3.3], font=8.5)
    D.p(d, "", space_after=2)

    # ------------------------------------------------------------------ 11.19
    D.h(d, 2, "11.19   Check it yourself")
    D.numbered(d, f"Evaluate equation ({n_cw}) at D = 0.200 m and S = 0.005 with ks 1.5 mm and ν "
                  "1.141 × 10⁻⁶. You should get 0.75 m/s: that is G203 Table 11's first row. Repeat for "
                  "DN900 at 0.75 mm/m.", restart=True)
    big_min = "; ".join(f"DN{k} at {_f(st['by_dn'][k][2], 2)} mm/m, where the 0.025 % step lays it at "
                        f"{_f(round_up_step(TABLE11[k] / 1000, k) * 1000, 2)}"
                        for k in sorted(st["by_dn"]) if k >= DN_TRUNK_STEP and k in TABLE11)
    D.numbered(d, "Open W8/shp/W8_pipes.shp. Check that no pipe has SLOPE_PMIL below the G203 Table 11 "
                  "value for its DN_MM, that every value is a multiple of 0.5 (the 0.05 % step the file "
                  f"was laid on, which is the project step below DN{DN_TRUNK_STEP}), that the pipes of "
                  f"DN{DN_TRUNK_STEP} and above sit on the grid's minimum ({big_min}; Table {t_steps}), "
                  "and that LEN_M never exceeds the G203 Table 12 spacing for its size.")
    D.numbered(d, "Open W8/shp/W8_manholes.shp. Check that no DEPTH exceeds 12 m and that IS_PUMP "
                  "sums to zero. Then look at a deep chamber and confirm the pipes either side "
                  "stay under 12 m along their whole length, not only at the ends.")
    D.numbered(d, "Select the plots of W14/shp/PLOTS_load.shp whose centre lies inside catchment 23 "
                  "of W8/shp/W8_catchments.shp. Sum Q_ULT and Q_2030 and compare with section "
                  "11.17; then compare the plot count with the nearest-pipe allocation of section 9.10.")
    D.numbered(d, "Recompute the header's d/D by hand: take its design peak, divide by the "
                  f"pipe-full flow of DN{e2['dn']} at {_f(e2['s'] * 1000, 2)} mm/m, its laid gradient, on "
                  "the true bore, and read d/D from the part-full table in section 11.4.")
    D.numbered(d, f"Take any DN200 main sewer at {_f(TABLE11[200], 2)} mm/m and its low-case peak. Below "
                  f"{_f(q_at_smin(TABLE11[200] / 1000.0), 2)} l/s, and short of 0.75 m/s, it needs washing; "
                  "above that flow it is a tractive pass at 1 Pa. Confirm that no pipe is given a "
                  "steeper gradient for self-cleansing.")
    D.numbered(d, "Change τ from 1 to 2 Pa and redo the tractive test of both worked examples. Note "
                  "which class changes, and that the gradient does not: at the concept stage the class "
                  "is decided at 1 Pa, and the confirmed τ is applied to the gradients only at the "
                  "preliminary design.")
    D.numbered(d, "In W8/shp/W8_pipes.shp, list every pipe with DROP_DN above 0.6 m and above 2 m. "
                  "Each needs an external backdrop or a vortex drop shaft at its downstream "
                  "chamber.")
    D.numbered(d, "Read G203 pages 17 to 33 and G201 pages 71 to 73 against the constraint table of "
                  "section 11.18, row by row. Every value should be found on the page given, with "
                  "the force word shown.")


TIER_WORD = {"lateral": "secondary main sewer", "branch": "secondary main sewer",
             "sub main": "secondary header", "trunk main": "primary trunk main"}


def _worked(d, num, title, e, first, n_mara, n_cwr):
    tier_word = TIER_WORD[e["tier"]]          # an unknown engine TIER fails the build
    D.h(d, 2, f"{num}   {title}")
    if first:
        _for(d, "To take one real street pipe through every rule in order, from the plots it "
                "serves to its class on the self-cleansing test. It replaces the earlier worked "
                "pipe, which was loaded at a flat five people per property and peaked by holding "
                "Merrimack below 100 properties; both of those have been superseded.")
    else:
        _for(d, "To size a pipe where the flow, not the minimum, sets the diameter, and to show "
                "the self-cleansing test passing on the tractive force when the velocity is not "
                "reached.")
    _rule(d, "Sum the plots upstream; peak by Merrimack above 100 properties and by Peltier at or "
             "below; add infiltration by the length of sewer upstream; choose the smallest "
             "diameter whose d/D at the laid gradient is within G203 Table 10, laying each size at its "
             "G203 Table 11 minimum rounded up to its step (section 11.11); check the maximum velocity; "
             "then take the low case through the velocity and tractive tests and give the pipe its "
             "class. The tractive test is a check: it never raises the gradient at this stage.")
    eq_m = eq_p = None
    if first:
        eq_p = _eq(d, M.seq(R("PF"), M.EQ, R("1.5"), M.PLUS,
                            M.frac(R("1"), M.sqrt(M.sub(R("Q"), UP("m"))))))
        eq_m = _eq(d, M.seq(M.sub(R("Q"), UP("pdf")), M.EQ, R("2.65"), R(" "),
                            M.sup(M.sub(R("Q"), UP("adf")), R("0.879"))))
        eq_i = _eq(d, M.seq(M.sub(R("Q"), UP("inf")), M.EQ, R("i"), R(" "), R("L")))
        _sym(d, [["PF", "Peltier peak factor, 100 properties or fewer", "—"],
                 ["Q m", "average daily flow", "l/s"],
                 ["Q pdf, Q adf", "peak and average daily flow, over 100 properties", "Ml/d"],
                 ["i", "infiltration allowance, 720", "l/d per km"],
                 ["L", "length of sewer upstream", "km"]])
    _src(d, "Peaks G201-p71 (Merrimack) and G201-p72 (Peltier, ceiling 5.0); infiltration G201-p72; "
            "sizing G203-p27 to p30; flow cases, classes and the property count per year: "
            "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md sections 2 to 4; the connected count and no "
            "infiltration in the low case, K in m³/s, the three classes and the gradient steps: "
            "project rule (engineer, 2026-09-11); τ = 1 Pa: GAP-9, NWS to confirm.")

    s8, sw, t11 = _f(e["s"] * 1000, 2), _f(e["s_w8"] * 1000, 2), _f(TABLE11[e["dn"]], 2)
    stp = _f(e["step"] * 1000, 2)
    if e["at_min"]:
        on = (f"which is already a whole number of {stp} mm/m steps" if abs(e["s"] - e["s_req"]) < 1e-12
              else f"rounded up to the next {stp} mm/m step")
        lay = f"It is laid at {s8} mm/m, its G203 Table 11 minimum of {t11} mm/m {on}. "
    else:
        lay = f"It is laid at {s8} mm/m, steeper than its minimum because the ground falls faster. "
    lay += ("The test-area design laid it at the same gradient." if abs(e["s"] - e["s_w8"]) < 1e-9
            else f"The test-area design, on one 0.05 % grid for every size, laid it at {sw} mm/m.")
    D.p(d, f"The pipe is {e['inlet']}, a DN{e['dn']} {tier_word} {_f(e['length'], 2)} m long. "
           f"{lay} It is the last pipe of its catchment, "
           f"{_f(e['area_ha'], 1)} ha and {F.fmt(e['sewer_m'])} m of sewer, so everything the "
           f"catchment produces passes through it into chamber {e['join']} on the main pipe.")
    D.tab_caption(d, f"{e['inlet']}: the plots it serves")
    D.table(d, ["Quantity", "Value", "How it is obtained"], [
        ["Plots", F.fmt(e["n_plots"]), "plot centre inside the catchment"],
        ["Domestic properties 2024", _f(e["pr_now"], 0), "sum of G_DOM"],
        ["Properties at saturation", _f(e["pr_ult"], 1), "G_DOM + (POP_ULT − POP) / OR_S, summed"],
        ["Properties in 2030", _f(e["pr_30"], 1), "G_DOM + (POP_2030 − POP) / OR_S, summed"],
        ["Connected properties in 2030", _f(e["pr_30c"], 1), f"properties in 2030 × {e['conn']}"],
        ["Q_ULT, average", f"{_f(e['q_ult'], 1)} m³/d", "sum of Q_ULT"],
        ["Q_2030, average", f"{_f(e['q_30'], 1)} m³/d", "sum of Q_2030"],
        ["Low case, average", f"{_f(e['q_low'], 1)} m³/d", f"Q_2030 × {e['conn']}"],
        ["Sewer upstream", f"{_f(e['sewer_m'] / 1000, 3)} km", "all pipe in the catchment"]],
        widths=[4.6, 3.4, 8.5], font=9)
    D.p(d, "", space_after=2)

    # the flows
    def _pk_text(method, pf, q_m3d, pk):
        if method == "Merrimack":
            return (f"Merrimack: Q adf = {_f(q_m3d / 1000, 4)} Ml/d, Q pdf = 2.65 × "
                    f"{_f(q_m3d / 1000, 4)}^0.879 = {_f(pf * q_m3d / 1000, 4)} Ml/d, PF = {_f(pf, 2)}, "
                    f"peak = {_f(pk, 2)} l/s")
        return (f"Peltier: Q m = {_f(q_m3d, 1)} / 86.4 = {_f(q_m3d / 86.4, 3)} l/s, PF = 1.5 + "
                f"1/√{_f(q_m3d / 86.4, 3)} = {_f(pf, 2)}, peak = {_f(pk, 2)} l/s")
    D.tab_caption(d, f"{e['inlet']}: the two design flows")
    D.table(d, ["Step", "Working", "Result"], [
        ["Sizing case: method", f"{_f(e['pr_ult'], 1)} properties "
         f"{'over' if e['pr_ult'] > 100 else 'at or under'} 100", e["m_ult"]],
        ["Sizing case: peak", _pk_text(e["m_ult"], e["pf_ult"], e["q_ult"], e["pk_ult"]),
         f"{_f(e['pk_ult'], 2)} l/s"],
        ["Infiltration", f"{F.fmt(e['inf'])} l/d/km × {_f(e['sewer_m'] / 1000, 3)} km = "
         f"{F.fmt(e['inf'] * e['sewer_m'] / 1000)} l/d", f"{_f(e['inf_ls'], 3)} l/s"],
        ["Design flow", "peak + infiltration", f"**{_f(e['q_des'], 2)} l/s**"],
        ["Low case: method", f"{_f(e['pr_30c'], 1)} connected properties in 2030 "
         f"{'over' if e['pr_30c'] > 100 else 'at or under'} 100", e["m_low"]],
        ["Low case: peak", _pk_text(e["m_low"], e["pf_low"], e["q_low"], e["pk_low"]),
         f"**{_f(e['pk_low'], 2)} l/s**"]],
        widths=[3.3, 10.2, 3.0], font=9)
    D.p(d, "", space_after=2)
    D.p(d, f"Both peak factors are below the recommended ceiling of 5.0. The low case carries no "
           "infiltration. G201 gives the 720 l/d per km as a design allowance and says nothing of it "
           "in the early years (section 7.4.3, p72); for those years it asks only that self-cleaning "
           "velocities be ensured at the initial stage of operations (section 7.4.4, p73). Adding "
           f"the {_f(e['inf_ls'], 3)} l/s allowance would only flatter the self-cleansing test, "
           "which is the direction to avoid. The layout itself was drawn "
           f"with a flat five people per property, which gave this catchment "
           f"{_f(e['w8_qadf'], 1)} m³/d; on the counted plot loads it is {_f(e['q_ult'], 1)} m³/d.")
    D.p(d, f"The low-case formula is chosen on the connected count, {_f(e['pr_30c'], 1)} properties "
           f"({_f(e['pr_30'], 1)} standing in 2030 × {e['conn']}), because the flow it peaks is the "
           "connected flow. "
           + (f"Counted on the properties standing, the formula here would still be {e['m_low']}."
              if e["m_low_standing"] == e["m_low"] else
              f"Counted on the properties standing, the formula here would be "
              f"{e['m_low_standing']} instead."))
    if not first:
        c9 = _ch9(e["inlet"])
        dpl = c9["n"] - e["n_plots"]
        y9, _v9 = solve(bore(e["dn"]), e["s"], c9["q_des"] / 1000.0)
        why = (f"which draws in a net {F.fmt(dpl)} more plots whose centres lie just outside this "
               "catchment's polygon" if dpl > 0 else
               f"which leaves out a net {F.fmt(-dpl)} plots that lie inside this polygon but nearer "
               "a pipe of another tree" if dpl < 0 else "which here gives the same count")
        same_len = abs(c9["length"] - e["sewer_m"]) < 1.0
        D.p(d, f"Section 9.10 works the same header with {F.fmt(c9['n'])} plots and a design flow "
               f"of {_f(c9['q_des'], 2)} l/s, against {F.fmt(e['n_plots'])} plots and "
               f"{_f(e['q_des'], 2)} l/s here. The difference is the allocation of plots, not the "
               "method. Chapter 9 gives each plot to its nearest street pipe and sums down the tree, "
               f"{why}; here a plot counts only if its centre lies inside the catchment. "
               + (f"The sewer upstream is the same, {_f(e['sewer_m'] / 1000, 3)} km, so the "
                  "infiltration is the same. " if same_len else
                  f"The sewer upstream is {_f(c9['length'] / 1000, 3)} km there and "
                  f"{_f(e['sewer_m'] / 1000, 3)} km here. ")
               + (f"At {_f(c9['q_des'], 2)} l/s the same DN{e['dn']} at {_f(e['s'] * 1000, 2)} mm/m "
                  f"runs at d/D {_f(y9, 3)}, also within the limit, so either allocation gives the "
                  "same pipe." if y9 is not None and y9 <= dod_limit(e["dn"]) else
                  f"At {_f(c9['q_des'], 2)} l/s the same DN{e['dn']} would run over its d/D limit, "
                  "so the allocation decides the size and has to be settled before the design is "
                  "fixed."))

    # sizing
    rows = []
    for dn_, s_use, y, v, ok in e["trials"]:
        t11_ = TABLE11[dn_]
        if y is None:
            res, ytxt, vtxt = "cannot carry the flow", "above 0.95", "—"
        else:
            ytxt, vtxt = _f(y, 3), _f(v, 2)
            res = "**smallest that passes**" if ok else "d/D over the limit"
        rows.append([f"DN{dn_}", _f(t11_, 2), _f(s_use * 1000, 2), ytxt, _f(dod_limit(dn_), 2),
                     vtxt, res])
    D.tab_caption(d, f"{e['inlet']}: choosing the diameter for {_f(e['q_des'], 2)} l/s, each size at "
                     "its laid minimum or the laid gradient, whichever is steeper")
    D.table(d, ["Size", "G203 Table 11 (mm/m)", "Laid at (mm/m)", "d/D", "Limit", "v (m/s)",
                "Result"],
            rows, widths=[1.7, 2.3, 2.3, 1.8, 1.6, 1.8, 5.0], font=9)
    D.p(d, "", space_after=2)
    if len(e["trials"]) > 1:
        D.p(d, "A smaller pipe laid steeper does not rescue it: at its own minimum gradient, "
               "rounded up to its step, it either cannot carry the flow or runs too full. The "
               "size is set by the flow, and laying the chosen size at its flatter minimum is exactly "
               "what G203 Table 11 allows. Choosing a larger size to lay it flatter still would be the "
               "oversizing the guideline forbids.")
    else:
        D.p(d, "The minimum size carries the flow with a large margin. The diameter is set by "
               "G203 Table 6, not by the flow, which is the normal case for a residential street sewer.")

    # checks
    s_lim = spacing(e["dn"])
    D.tab_caption(d, f"{e['inlet']}: every check, at the laid gradient; depths and drop as laid in "
                     "the test-area design")
    D.table(d, ["Check", "Value", "Limit", "Result", "Source"], [
        ["d/D at design flow", _f(e["y"], 3), f"≤ {_f(dod_limit(e['dn']), 2)}",
         "pass" if e["y"] <= dod_limit(e["dn"]) else "FAIL", "G203-p27 Tab 10"],
        ["Velocity at design flow", f"{_f(e['v'], 2)} m/s", "≤ 3.0 m/s",
         "pass" if e["v"] <= V_MAX else "FAIL", "G203-p27"],
        ["Laid gradient against G203 Table 11", f"{_f(e['s'] * 1000, 2)} mm/m",
         f"≥ {_f(TABLE11[e['dn']], 2)} mm/m", "pass" if e["s"] * 1000 >= TABLE11[e["dn"]] - 1e-9 else "FAIL",
         "G203-p29"],
        ["Gradient on its step", f"{_f(e['s'] * 1000, 2)} mm/m",
         f"multiple of {_f(e['step'] * 1000, 2)} mm/m",
         "pass" if abs(e["s"] / e["step"] - round(e["s"] / e["step"])) < 1e-6 else "FAIL",
         "project rule"],
        ["Fall against tolerance", f"{F.fmt(e['s'] * e['length'] * 1000)} mm", "> 40 mm",
         "pass" if e["s"] * e["length"] > 2 * TOL else "FAIL", "G203-p29"],
        ["Length against G203 Table 12", f"{_f(e['length'], 2)} m", f"≤ {s_lim} m",
         "pass" if e["length"] <= s_lim else "FAIL", "G203-p30"],
        ["Depth at the downstream chamber", f"{_f(e['j_depth'], 2)} m", "≤ 12 m",
         "pass" if e["j_depth"] <= MAX_DEPTH else "FAIL", "project, G203-p33"],
        ["Deepest chamber in the catchment", f"{_f(e['deepest'], 2)} m", "≤ 12 m",
         "pass" if e["deepest"] <= MAX_DEPTH else "FAIL", "project, G203-p33"],
        ["Drop into the downstream chamber", f"{_f(e['drop'], 2)} m", "0.6 m backdrop; 2 m vortex",
         ("vortex drop shaft" if e["drop"] > DROP_VORTEX else
          "external backdrop" if e["drop"] > DROP_BACK else "none needed"), "G203-p30"],
        ["Low case: velocity", f"{_f(e['v_low'], 2)} m/s at d/D {_f(e['y_low'], 3)}", "≥ 0.75 m/s",
         "pass" if e["v_low"] >= V_MIN else "not reached", "G203-p26"],
        ["Low case: tractive, τ = 1 Pa, K 2.33 × 10⁻⁴ (Q in m³/s), true flow",
         f"S min {_f(e['smin_t'] * 1000, 2)} mm/m",
         f"laid {_f(e['s'] * 1000, 2)} mm/m", "pass" if e["s"] >= e["smin_t"] else "not met",
         "G203-p27"],
        ["Class", f"**{e['cls']}**", "", "", "project rule"]],
        widths=[4.4, 3.6, 3.3, 2.7, 2.5], font=9)
    D.p(d, "", space_after=2)
    t_tau = D.tab_caption(d, f"{e['inlet']}: the tractive test at three values of τ, for information; "
                             "the class is decided at 1 Pa")
    D.table(d, ["τ (Pa)", "S min at the low-case peak (mm/m)", "Laid (mm/m)", "Class"],
            [[_f(t, 1), _f(e["smin_tau"][t] * 1000, 2), _f(e["s"] * 1000, 2),
              (f"**{e['cls_tau'][t]}**" if t == TAU else e["cls_tau"][t])] for t in TAUS],
            widths=[2.5, 5.5, 3.5, 5.0], font=9)
    D.p(d, "", space_after=2)
    if e["cls"] == "needs washing":
        _num(d, f"The pipe is sized by the minimum and carries {_f(e['q_des'], 2)} l/s at "
                f"saturation, d/D {_f(e['y'], 2)}. In the opening year it carries "
                f"{_f(e['pk_low'], 2)} l/s at peak and reaches {_f(e['v_low'], 2)} m/s, so the "
                f"velocity test is not met. Equation ({n_mara}) at τ = 1 Pa, with K = 2.33 × 10⁻⁴ and "
                f"Q in m³/s, asks for {_f(e['smin_t'] * 1000, 2)} mm/m at that flow against "
                f"{_f(e['s'] * 1000, 2)} mm/m laid, so the tractive test is not met either: the pipe "
                "needs washing. It goes on the flushing list for the early years (G203-p28). It is not "
                "upsized, since DN200 is already the smallest main sewer, and it is not regraded: it is "
                "laid at the guideline's gradient, and what it lacks is flow, not fall. At its laid "
                "gradient it would pass the tractive test once its low-case peak reached "
                f"{_f(e['q_pass'], 2)} l/s. Table {t_tau} shows that a larger τ only moves that flow "
                "further away. "
                f"The drop of {_f(e['drop'], 2)} m into the main-pipe chamber exceeds 2 m, so the "
                "join needs a vortex drop shaft rather than a backdrop.")
    else:
        _num(d, f"The header runs at d/D {_f(e['y'], 2)} at saturation, inside the "
                f"{_f(dod_limit(e['dn']), 2)} limit, at {_f(e['v'], 2)} m/s. In the opening year it "
                f"carries {_f(e['pk_low'], 2)} l/s at peak and reaches only {_f(e['v_low'], 2)} m/s, so "
                f"the velocity test is not met. The tractive minimum at that flow, equation ({n_mara}) "
                f"at τ = 1 Pa with K = 2.33 × 10⁻⁴ and Q in m³/s, is {_f(e['smin_t'] * 1000, 2)} mm/m "
                f"against {_f(e['s'] * 1000, 2)} mm/m laid, so it is a {e['cls']}. The gradient came "
                f"from G203 Table 11 alone: {_f(TABLE11[e['dn']], 2)} mm/m for DN{e['dn']}, rounded up "
                f"to the next {_f(e['step'] * 1000, 2)} mm/m step. The tractive slope checked it and did "
                "not set it; at this stage it never does.")
        s_pd = round_up_step(e["smin_t2"], e["dn"])
        D.callout(d, "The class of this pipe depends on a number the guideline does not give.",
                  f"Table {t_tau} shows it. At τ = 1.5 Pa the pipe is still a "
                  f"{e['cls_tau'][1.5]}. At τ = 2 Pa the tractive minimum at the same flow, same K, "
                  f"rises to {_f(e['smin_t2'] * 1000, 2)} mm/m, above the {_f(e['s'] * 1000, 2)} mm/m "
                  f"laid, and the class becomes \"{e['cls2']}\". At the concept stage that changes the "
                  "class, not the gradient. At the preliminary design, once NWS confirms τ, the "
                  "tractive slope is applied to the gradients: at 2 Pa this header would be laid at "
                  f"{_f(s_pd * 1000, 2)} mm/m, and the extra fall goes into depth downstream, where "
                  f"the join chamber already sits at {_f(e['j_depth'], 2)} m.")
    _lives(d, f"Computed in this chapter (TUTORIALS/T04/ch05_gravity.py, function example) from "
              f"W14/shp/PLOTS_load.shp (Q_ULT, Q_2030, G_DOM, POP, POP_2030, POP_ULT, OR_S), "
              f"W14/analysis/design_flows.json (connection ratio, infiltration) and the W8 design: "
              f"catchment polygon and PIPE_M in W8/shp/W8_catchments.shp, pipe {e['inlet']} in "
              f"W8_pipes.shp, chamber {e['join']} in W8_manholes.shp. The engine itself still loads "
              "the flat per-plot figure until it reads PLOTS_load.shp (DESIGN_FLOWS_FOR_NETWORK.md "
              "section 6). The laid gradient is computed by step_for and round_up_step, and the class "
              "by _classify, in the same script; the assertions at the top of c11_gravity stop the "
              "build if the data move a worked pipe out of the class written here"
              + ("; the nearest-pipe allocation of section 9.10 is _net() in "
                 "TUTORIALS/T04/ch04_peak_tiers.py." if not first else "."))
