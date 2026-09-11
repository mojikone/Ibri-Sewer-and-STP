"""T04 chapters 9 and 10: peak flow and infiltration; the network and its tiers.

Every Ibri number is computed at build time from the live outputs: the plot layer
(W14/shp/PLOTS_load.shp, through facts_w14), the design-flow handoff
(W14/analysis/design_flows.json) and the test-area network (W8/shp, W8/run).
Guideline constants are typed with their page.
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

import json
import math
from functools import lru_cache
from collections import Counter

REPO = os.path.dirname(os.path.dirname(HERE))
W8 = os.path.join(REPO, "W8")
with open(os.path.join(REPO, "W14", "analysis", "design_flows.json"), encoding="utf-8") as _fh:
    FLOWS = json.load(_fh)
with open(os.path.join(W8, "run", "summary.json"), encoding="utf-8") as _fh:
    W8RUN = json.load(_fh)
with open(os.path.join(REPO, "W13", "run", "summary.json"), encoding="utf-8") as _fh:
    W13RUN = json.load(_fh)
import re as _re
_CRIT = os.path.join(REPO, "W13", "tmp3", "py", "sewnet", "criteria.py")
with open(_CRIT, encoding="utf-8") as _fh:
    ENGINE_STEP = float(_re.search(r"^\s*SLOPE_STEP\s*:\s*float\s*=\s*([0-9.eE+-]+)", _fh.read(), _re.M).group(1))

CONN = float(FLOWS["rules"]["connection_ratio_2030"])          # Inception R0, reached by 2028
INF = float(FLOWS["rules"]["infiltration_l_per_day_per_km"])   # G201-p72
MARGIN = float(FLOWS["rules"]["stp_margin"])                   # G201-p73; G203-p65 Tab 29
OPEN_YEAR = int(FLOWS["rules"]["opening_year"])
MK_C, MK_E = 2.65, 0.879      # Merrimack, G201-p71
PT_A, PT_B = 1.5, 1.0         # Peltier as printed, G201-p72
PF_REC = 5.0                  # hourly peak factor recommendation, G201-p72
N_THRESH = 100                # properties, G201-p71
TAB11_MIN = {200: 5.00, 250: 3.75, 315: 2.70, 400: 2.05, 500: 1.55,
             600: 1.25, 700: 1.00, 800: 0.85, 900: 0.75}   # minimum gradient, mm/m, G203-p29 Table 11 (DN900 and over)
STEP_SEC, STEP_TRUNK, TRUNK_DN = 0.5, 0.25, 500   # gradient steps, mm/m: 0.05 % for secondary pipes, 0.025 % for
                                                  # primary trunks of DN500 and up (project rule, engineer 2026-09-11)
TOL_MM = 20.0                 # line and level of a laid pipe, G203-p29 section 4.3.1
V_SC = 0.75                   # m/s at the peak, G203-p26
KS, NU, GRAV = 0.0015, 1.141e-6, 9.81   # Colebrook-White roughness, m (G203-p24, p28); viscosity at 15 C, m2/s (G203-p25 Table 9)
PVC_SDR = 34.0                # PVC-U SN8 bore up to DN315, as the design engine (W8 criteria.internal_diameter)
K_M3S = 2.33e-4               # Mara, Sleigh and Taylor constant with Q in m3/s, G203-p27 (engineer, 2026-09-11)
TAU = float(FLOWS["rules"]["rulings_confirmed"]["tau_pa"])   # Pa; none in G203 (GAP-9); NWS to confirm
LS = 86.4                     # m3/d per l/s
MK_M3D = MK_C * 1000 ** (1 - MK_E)   # Merrimack constant when both flows are in m3/d
Q_FUT = F.RET_DOM * F.LPCD + F.RET_ND * (F.R_ND + F.R_GOV) * F.LPCD   # l/d per future resident


# ------------------------------------------------------------------ helpers
def _lead(d, lead, text):
    return D.rich(d, (lead, {"bold": True}), (text, {}))


def _src(d, text):
    return D.rich(d, ("Source.  ", {"bold": True, "colour": D.MID, "size": 9.5}), (text, {"size": 9.5}))


def _where(d, text):
    return D.rich(d, ("Where it lives.  ", {"bold": True, "colour": D.MID, "size": 9.5}), (text, {"size": 9.5}))


def _sym(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)
    D.p(d, "", space_after=2)


def _eq(d, *parts):
    M.display(d, M.seq(*parts), number=D.next_eq())


def Qs(s):
    return M.sub(R("Q"), UP(s))


def f(x, nd=0):
    return F.fmt(x, nd)


# ------------------------------------------------------------- the formulas
def merrimack(q):
    """Peak flow, m3/d, from an average flow in m3/d. The formula itself works in Ml/d."""
    return 1000.0 * MK_C * (q / 1000.0) ** MK_E


def peltier_pf(q):
    """Peak factor from an average flow in m3/d. The formula itself works in l/s."""
    return PT_A + PT_B / math.sqrt(q / LS)


def peak(q, props):
    """The project rule: Merrimack over 100 properties, Peltier at or under 100."""
    if q <= 0:
        return 0.0, 0.0, "none"
    if props > N_THRESH:
        qp = merrimack(q)
        return qp, qp / q, "Merrimack"
    pf = peltier_pf(q)
    return q * pf, pf, "Peltier"


def inf_m3d(length_m):
    return INF * (length_m / 1000.0) / 1000.0


# ------------------------------------------ gradients and the self-cleansing audit
def grid_step(dn):
    """Gradient step, mm/m, by pipe size: 0.25 from DN500 (the primary trunks), 0.5 below."""
    return STEP_TRUNK if dn >= TRUNK_DN else STEP_SEC


def on_grid(s_mmm, step):
    """A gradient in mm/m rounded UP to the step: never flatter than the minimum."""
    return math.ceil(s_mmm / step - 1e-9) * step


def _bore(dn):
    """True bore, m, as the design engine: PVC-U is OD-designated to DN315, GRP is ID-designated."""
    return dn / 1000.0 * (1.0 - 2.0 / PVC_SDR) if dn <= 315 else dn / 1000.0


def _v_cw(r_m, s):
    """Colebrook-White velocity, m/s, part full (the diameter replaced by 4R)."""
    k = math.sqrt(8.0 * GRAV * r_m * s)
    return -2.0 * k * math.log10(KS / (14.8 * r_m) + 2.51 * NU / (4.0 * r_m * k))


def velocity(dn, s_mmm, q_ls):
    """Velocity, m/s, of q_ls running part full in dn laid at s_mmm; None if the pipe cannot carry it."""
    D_m, s = _bore(dn), s_mmm / 1000.0

    def ar(y):
        th = 2.0 * math.acos(1.0 - 2.0 * y)
        a = D_m * D_m / 8.0 * (th - math.sin(th))
        return a, a / (D_m * th / 2.0)

    def q_at(y):
        a, r = ar(y)
        return a * _v_cw(r, s) * 1000.0
    if q_at(0.93) < q_ls:
        return None
    lo, hi = 1e-7, 0.93
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if q_at(mid) < q_ls else (lo, mid)
    return _v_cw(ar(0.5 * (lo + hi))[1], s)


def smin_mara(q_ls, tau=TAU):
    """Mara, Sleigh and Taylor minimum gradient, mm/m, on the true flow (no floor), Q in m3/s (G203-p27)."""
    return K_M3S * tau ** 1.23 * (q_ls / 1000.0) ** -0.461 * 1000.0


def audit_class(dn, s_mmm, q_ls, tau=TAU):
    """The three classes of the self-cleansing audit (engineer, 2026-09-11), on the low-case peak."""
    v = velocity(dn, s_mmm, q_ls)
    if v is not None and v >= V_SC:
        return "velocity pass", v
    if s_mmm >= smin_mara(q_ls, tau):
        return "tractive pass", v
    return "needs washing", v


# ------------------------------------------------------ the test-area network
@lru_cache(None)
def _net():
    """Every plot of the test area allocated to its nearest street pipe of the test-area
    design, then summed downstream through the tree. Returns the upstream totals per pipe."""
    import geopandas as gpd
    import networkx as nx
    import pandas as pd
    pl = F.plots()
    pipes = gpd.read_file(os.path.join(W8, "shp", "W8_pipes.shp"))
    bnd = gpd.read_file(os.path.join(W8, "shp", "W8_boundary.shp"))
    keep = ["Name", "Buiding_St", "SETTLE", "QADF", "Q_2030", "Q_ULT", "POP", "POP_2030", "POP_ULT", "G_DOM", "OR_S"]
    pts = gpd.GeoDataFrame(pl[keep].copy(), geometry=pl.representative_point(), crs=pl.crs)
    pts = gpd.sjoin(pts, bnd[["geometry"]], predicate="within").drop(columns="index_right")
    pts = pts[~pts.index.duplicated()]
    street = pipes[pipes.TIER != "trunk main"].copy()
    near = gpd.sjoin_nearest(pts, street[["LABEL", "geometry"]], how="left", distance_col="DIST")
    near = near[~near.index.duplicated()]
    near["PR_ULT"] = near.G_DOM + (near.POP_ULT - near.POP) / near.OR_S
    near["PR_30"] = near.G_DOM + (near.POP_2030 - near.POP) / near.OR_S
    near["FUT"] = (near.Buiding_St == "Future").astype(int)
    near["ONE"] = 1
    cols = ["ONE", "FUT", "G_DOM", "QADF", "Q_2030", "Q_ULT", "PR_30", "PR_ULT"]
    own = near.groupby("LABEL")[cols].sum().reindex(street.LABEL).fillna(0.0)
    own["LEN"] = street.set_index("LABEL").LEN_M
    G = nx.DiGraph()
    for r in street.itertuples():
        G.add_edge(r.ND_UP, r.ND_DN, label=r.LABEL)
    outdeg = max(k for _, k in G.out_degree())
    inflow, acc = {}, {}
    for n in nx.topological_sort(G):
        base = inflow.get(n, 0.0)
        for _, dn, e in G.out_edges(n, data=True):
            v = own.loc[e["label"]].values + base
            acc[e["label"]] = v
            inflow[dn] = inflow.get(dn, 0.0) + v
    up = pd.DataFrame.from_dict(acc, orient="index", columns=list(own.columns))
    meta = street.set_index("LABEL")[["TIER", "DN_MM", "SLOPE_PCT", "ND_UP", "ND_DN", "IS_JOIN", "LEN_M"]]
    up = up.join(meta)
    up["Q_LOW"] = up.Q_2030 * CONN
    # low-case property count: the connected count, properties of 2030 x CONN
    # (engineer, 2026-09-11; design_flows.json rules.rulings_confirmed.low_case_property_count)
    up["PR_LOW"] = up.PR_30 * CONN
    # the worked pipe: the street main sewer with most properties at saturation that is not itself a join
    mains = up[(up.TIER == "lateral") & (up.IS_JOIN == 0)].copy()
    mains["LBL"] = mains.index
    worked = mains.sort_values(["PR_ULT", "LBL"], ascending=[False, True]).index[0]
    joins = up[up.IS_JOIN == 1]
    header = joins.sort_values("Q_ULT", ascending=False).index[0]
    # formula and cap statistics over every street pipe
    stats = {}
    for case, qcol, pcol in (("ult", "Q_ULT", "PR_ULT"), ("low", "Q_LOW", "PR_LOW"),
                             ("low_standing", "Q_LOW", "PR_30")):
        loaded = up[up[qcol] > 0]
        res = [peak(q, p) for q, p in zip(loaded[qcol], loaded[pcol])]
        how = [x[2] for x in res]
        stats[case] = dict(loaded=len(loaded), merr=how.count("Merrimack"), pelt=how.count("Peltier"),
                           over5=sum(1 for x in res if x[1] > PF_REC), peaks=[x[0] for x in res],
                           how=how)
    # pipes whose low-case formula depends on the count: standing over 100, connected 100 or fewer
    a, b = stats["low_standing"], stats["low"]
    flip = [(pa, pb) for pa, pb, ha, hb in zip(a["peaks"], b["peaks"], a["how"], b["how"]) if ha != hb]
    stats["flip"] = dict(n=len(flip), lower=sum(1 for pa, pb in flip if pb < pa))
    # the audit class of every pipe whose uncapped low-case factor passes 5.0, on its laid gradient,
    # and again with the factor held to 5.0
    lo = up[up.Q_LOW > 0]
    o5 = []
    for dn, s_pct, q, pr in zip(lo.DN_MM, lo.SLOPE_PCT, lo.Q_LOW, lo.PR_LOW):
        qp, pf, _ = peak(q, pr)
        if pf > PF_REC:
            o5.append((int(dn), s_pct * 10.0, audit_class(int(dn), s_pct * 10.0, qp / LS)[0],
                       audit_class(int(dn), s_pct * 10.0, q * PF_REC / LS)[0]))
    stats["over5_cls"] = Counter(x[2] for x in o5)
    stats["over5_cls_capped"] = Counter(x[3] for x in o5)
    stats["over5_dn"] = sorted({x[0] for x in o5})
    # the test-area design raised the tractive flow to 1.5 l/s (its TRACTIVE_QMIN), so its tractive slope
    # never passed the DN200 Table 11 minimum: its DN200 gradients are the concept-stage gradients
    assert smin_mara(1.5, 1.0) < TAB11_MIN[200]
    assert all(s >= on_grid(TAB11_MIN[dn], grid_step(dn)) - 1e-9
               and abs(s / grid_step(dn) - round(s / grid_step(dn))) < 1e-6 for dn, s, _, _ in o5), \
        "a pipe of the Section 9.6 group is off its Table 11 step: rewrite Section 9.6"
    jp = [peak(q, p)[0] for q, p in zip(joins.Q_ULT, joins.PR_ULT)]
    return dict(up=up, worked=worked, header=header, stats=stats, outdeg=outdeg,
                plots_in=len(pts), q_ult_in=float(pts.Q_ULT.sum()), q_today_in=float(pts.QADF.sum()),
                fut_in=int((pts.Buiding_St == "Future").sum()), dist_med=float(near.DIST.median()),
                n_street=len(street), n_joins=len(joins), join_peaks_sum=float(sum(jp)),
                join_total=float(joins.Q_ULT.sum()), join_tiers=joins.TIER.value_counts().to_dict())


@lru_cache(None)
def _plotwide():
    """Study-area and Ibri figures read from the plot layer."""
    p = F.plots()
    q = p.Q_ULT[p.Q_ULT > 0]
    pf = PT_A + PT_B / (q / LS) ** 0.5
    ib = p[p.SETTLE == "IBRI"]
    ib_props = float((ib.G_DOM + (ib.POP_ULT - ib.POP) / ib.OR_S).sum())
    return dict(sum_plot_peaks=float((q * pf).sum()), sum_plot_peaks_cap=float((q * pf.clip(upper=PF_REC)).sum()),
                n_loaded=int(len(q)), ib_plots=len(ib), ib_future=int((ib.Buiding_St == "Future").sum()),
                ib_q_ult=float(ib.Q_ULT.sum()), ib_props_ult=ib_props, ib_or=float(ib.OR_S.iloc[0]),
                all_future=int((p.Buiding_St == "Future").sum()), all_plots=len(p))


def _case(q, props, length_m=None):
    qp, pf, how = peak(q, props)
    qi = inf_m3d(length_m) if length_m else 0.0
    return dict(q=q, props=props, qp=qp, pf=pf, how=how, qi=qi)


def _how(c):
    return f"{c['how']} (over 100)" if c["how"] == "Merrimack" else f"{c['how']} (100 or fewer)"


# =====================================================================  9
def c09_peak(d):
    t = F.totals()
    N = _net()
    PW = _plotwide()
    up = N["up"]
    w = up.loc[N["worked"]]
    hd = up.loc[N["header"]]
    ult = t["ultimate"]
    st = N["stats"]
    tot = FLOWS["totals"]

    D.h(d, 1, "9   Peak flow and infiltration", page_break=True)
    D.p(d, "The chapters before this one end with an average daily flow on every plot, for 2024, "
           f"{OPEN_YEAR}, 2055 and saturation. A sewer is not sized on an average. It must carry the "
           "peak of the flow that reaches it, plus the groundwater that leaks in through its joints, "
           "and it must also run fast enough to clean itself while the flow is still small. This "
           "chapter takes the plot averages to those two design flows, pipe by pipe, and then to the "
           "flows at the treatment plant.")

    # ---------------------------------------------------------------- 9.1
    D.h(d, 2, "9.1   The plot carries average flow only")
    _lead(d, "What it is for.  ", "To keep each quantity where it belongs. The plot knows how much "
          "sewage it makes on an average day. It does not know how that flow combines with its "
          "neighbours', so it cannot know its own peak.")
    _lead(d, "The rule.  ", "Every plot stores four average dry-weather flows in m³/d and nothing "
          "else: 2024, the opening year, 2055 and saturation. Peak factor, infiltration and the plant "
          "margin are applied later, to flows that have been summed along the network. Tanker "
          "deliveries and private wells are in no flow until their records arrive.")
    D.p(d, "The reason is attenuation. Each house discharges in short bursts. A pipe serving a few "
           "houses sees those bursts almost one at a time, so its peak is many times its average. A "
           "pipe serving thousands sees them overlap and smooth out, so its peak is a small multiple "
           "of its average. The peak factor therefore falls as the flow accumulates, and peaks do not "
           "add. Summing the plot peaks, or the peaks of the pipes arriving at a junction, always "
           "overstates the peak downstream.")
    _lead(d, "Ibri number.  ", f"At saturation {f(PW['n_loaded'])} plots carry a flow, "
          f"{f(t['q_ult'])} m³/d in all. Peaked plot by plot with the small-catchment formula of "
          f"Section 9.5 and added, they would ask the plant for {f(PW['sum_plot_peaks'])} m³/d; even "
          f"with every plot held to a factor of 5.0 it is {f(PW['sum_plot_peaks_cap'])} m³/d. The "
          f"Merrimack formula applied once to the area's accumulated flow gives "
          f"{f(merrimack(t['q_ult']))} m³/d. The 5.51 km² test area shows the same effect at a smaller "
          f"scale: the {N['n_joins']} pipes that join the main pipe carry {f(N['join_total'])} m³/d "
          f"between them at saturation; their own peaks add to {f(N['join_peaks_sum'] / LS, 1)} l/s, "
          f"while the peak of their combined flow is {f(merrimack(N['join_total']) / LS, 1)} l/s.")
    _src(d, "PAM-GUD-201 §7.4.2, G201-p71: the peak factor is defined for an area, a catchment or "
            "sub-catchment, not for a property. G201-p72: infiltration is a rate per length of sewer. "
            "Project rule (engineer, 2026-09-11): the plot stores average flow only, "
            "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §1 and §8.")
    _where(d, "W14/shp/PLOTS_load.shp, fields QADF (2024), Q_2030, Q_2055, Q_ULT, all m³/d. The rules "
              "in machine form: W14/analysis/design_flows.json, key \"rules\".")
    D.picture(d, os.path.join(IMG, "D3_flow.png"), 15.0)
    D.fig_caption(d, "From the plot's average flow to the design flow in each pipe and at the plant.")

    # ---------------------------------------------------------------- 9.2
    D.h(d, 2, "9.2   Summing upstream and counting properties")
    _lead(d, "What it is for.  ", "To give each pipe the two numbers the peak formulas need: the "
          "average flow of everything upstream, and the number of properties that make it.")
    _lead(d, "The rule.  ", "The average flow of a pipe is the sum of the flows of every plot that "
                            "drains through it, in the year of the case being checked.")
    _eq(d, Qs("pipe,y"), M.EQ, M.nary("∑", M.seq(R("i"), R(" ∈ "), UP("up")), "",
                                       M.sub(R("q"), R("i,y")), hide_hi=True))
    D.p(d, "The number of properties upstream is counted per plot and summed the same way. For an "
           "existing plot it is the domestic properties counted from the electricity meters. Growth "
           "adds properties at the settlement's occupancy, so a future plot, or a built plot that "
           "gains people, adds its extra people divided by the occupancy.")
    _eq(d, M.sub(R("N"), UP("y")), M.EQ, M.nary("∑", M.seq(R("i"), R(" ∈ "), UP("up")), "",
        M.delim(M.seq(M.sub(R("G"), UP("dom,i")), M.PLUS,
                      M.frac(M.seq(M.sub(R("P"), UP("y,i")), M.MINUS, M.sub(R("P"), UP("2024,i"))),
                             M.sub(UP("OR"), UP("s"))))), hide_hi=True))
    _sym(d, [["Q pipe,y", "average dry-weather flow in the pipe in year y", "m³/d"],
             ["q i,y", "average flow of plot i in year y (QADF, Q_2030, Q_2055 or Q_ULT)", "m³/d"],
             ["N y", "properties upstream in year y", "—"],
             ["G dom,i", "domestic properties counted on plot i in 2024 (G_DOM)", "—"],
             ["P y,i ; P 2024,i", "people on plot i in year y (POP_2030, POP_ULT) and in 2024 (POP)", "persons"],
             ["OR s", "occupancy of the plot's settlement (OR_S)", "persons per property"],
             ["up", "the set of plots draining through the pipe", "—"]])
    D.p(d, "The count is fractional, because future people are spread across plots by capacity rather "
           "than by whole houses. The threshold in Section 9.3 compares the sum with 100; the total is "
           "not rounded before the comparison.")
    pr = FLOWS["properties"]
    _lead(d, "Ibri number.  ", f"Over the whole study area the count gives {f(pr['y2024'])} "
          f"properties in 2024, {f(pr['y2030'])} in {OPEN_YEAR} and {f(pr['ultimate'])} at saturation. "
          f"Ibri's occupancy is {PW['ib_or']:.2f}, so every {PW['ib_or']:.2f} people added to an Ibri "
          f"plot count as one more property.")
    _src(d, "Project rule (engineer, 2026-09-11), W14/analysis/design_flows.json, "
            "rules.properties_per_plot_in_year. Occupancy by settlement: report R2 §14.4.")
    _where(d, "Per plot: G_DOM, POP, POP_2030, POP_ULT, OR_S in W14/shp/PLOTS_load.shp. The pipe "
              "summation is the design engine's job; the engine does not read these fields yet "
              "(DESIGN_FLOWS_FOR_NETWORK.md §6). The worked pipe below is summed by this chapter's "
              "build script, TUTORIALS/T04/ch04_peak_tiers.py, function _net.")

    # ---------------------------------------------------------------- 9.3
    D.h(d, 2, "9.3   Which peak formula")
    _lead(d, "What it is for.  ", "To pick, for each pipe and each flow case, the formula that turns "
                                  "its average into its peak.")
    _lead(d, "The rule.  ", "More than 100 properties upstream: the Merrimack formula. 100 "
          "properties or fewer: the Peltier formula. The choice is made again for each case, because "
          "the same pipe can have more than 100 properties at saturation and fewer in the opening year.")
    D.p(d, "The guideline makes Merrimack obligatory for an area of over 100 properties and gives no "
           "method for smaller ones. It then offers Peltier as an alternative, the method of NWS's 2024 "
           "Integrated Master Plan. Using Peltier for the small heads is the project's reading of that "
           "gap. The two formulas do not meet at 100 properties; Section 9.5 shows the jump.")
    _src(d, "G201-p71 §7.4.2 (Merrimack, over 100 properties); G201-p72 (Peltier, introduced as the "
            "alternative). Project rule for the split (engineer, 2026-09-11), design_flows.json "
            "rules.peak_over_100_properties and rules.peak_100_properties_or_fewer.")
    _lead(d, "Ibri number.  ", f"Of the {f(st['ult']['loaded'])} loaded street pipes of the test-area "
          f"design, {f(st['ult']['merr'])} carry more than 100 properties at saturation and take "
          f"Merrimack; {f(st['ult']['pelt'])} take Peltier. In the {OPEN_YEAR} low case, counting the "
          f"connected properties (Section 9.9), {f(st['low']['merr'])} take Merrimack and "
          f"{f(st['low']['pelt'])} Peltier; counted on the properties standing it would be "
          f"{f(st['low_standing']['merr'])} and {f(st['low_standing']['pelt'])}. Most pipes of a "
          "street network are small heads, so Peltier is the formula most pipes use.")
    _where(d, "design_flows.json rules. The choice per pipe will be a field of the engine's pipe "
              "output; the test-area design stored both factors, PF and PF_PELT, side by side.")

    # ---------------------------------------------------------------- 9.4
    D.h(d, 2, "9.4   Merrimack")
    _lead(d, "What it is for.  ", "The peak of a pipe or area serving more than 100 properties.")
    _lead(d, "The rule.  ", "The formula gives the peak flow directly; the peak factor is the ratio.")
    _eq(d, Qs("pdf"), M.EQ, R("2.65"), M.TIMES, M.sup(Qs("adf"), R("0.879")))
    _eq(d, UP("Pf"), M.EQ, M.frac(Qs("pdf"), Qs("adf")))
    _sym(d, [["Q pdf", "peak flow (the guideline calls it the peak daily flow)", "**Ml/d**"],
             ["Q adf", "average daily flow", "**Ml/d**"],
             ["Pf", "peak factor", "—"]])
    D.callout(d, "Both flows are in megalitres per day.",
              "The exponent is 0.879, not 1, so the formula is not unit-free. Feeding it m³/d gives a "
              "different peak factor, not a scaled one. Divide m³/d by 1,000 before using it, or use "
              f"the m³/d form in Section 9.7, whose constant is {MK_M3D:.3f}, not 2.65.")
    _src(d, "G201-p71 §7.4.2: the formula, its units and the definition Pf = Qpdf / Qadf.")
    rows = [["The 5.51 km² test area at saturation", N["q_ult_in"]],
            ["Ibri town at saturation", PW["ib_q_ult"]],
            [f"The study area in {OPEN_YEAR}", t["q"][OPEN_YEAR]],
            [f"The study area at saturation, {ult}", t["q_ult"]]]
    out = [[name, f(q, 1), f"{q / 1000:.3f}", f(merrimack(q)), f"{merrimack(q) / q:.2f}"] for name, q in rows]
    _lead(d, "Ibri number.  ", "The factor falls steadily as the area grows. The table applies "
                               "Merrimack to real accumulated flows from the plot layer.")
    D.tab_caption(d, "Merrimack peak factor at four scales of Ibri flow")
    D.table(d, ["Area", "Average, m³/d", "Average, Ml/d", "Peak, m³/d", "Pf"], out,
            widths=[6.6, 2.6, 2.4, 2.6, 1.6], font=9, align_right={1, 2, 3, 4})
    D.p(d, "", space_after=2)
    _where(d, "Totals: facts_w14.totals() and the plot layer (Ibri: SETTLE = IBRI; test area: plots "
              "inside W8/shp/W8_boundary.shp). Formula: function merrimack in this chapter's script.")

    # ---------------------------------------------------------------- 9.5
    D.h(d, 2, "9.5   Peltier")
    _lead(d, "What it is for.  ", "The peak of a pipe serving 100 properties or fewer, which is most "
                                  "of the pipes in a street network.")
    _lead(d, "The rule.  ", "The formula gives a peak factor from the average flow in litres per "
                            "second; the peak is the average times the factor.")
    _eq(d, M.sub(UP("Pf"), UP("ww")), M.EQ, R("1.5"), M.PLUS, M.frac(R("1"), M.sqrt(M.sub(R("Q"), UP("m")))))
    _eq(d, Qs("pdf"), M.EQ, Qs("adf"), M.TIMES, M.sub(UP("Pf"), UP("ww")))
    _sym(d, [["Pf ww", "peak factor for wastewater flows", "—"],
             ["Q m", "average daily flow", "**l/s**"],
             ["Q adf ; Q pdf", "average and peak flow in the second line", "m³/d"]])
    D.callout(d, "The guideline prints 1 in the numerator.",
              "The Peltier relation as usually published carries 2.5 over the root. The guideline's "
              "page prints 1; its text layer reads 1, and the page was also checked as a high-resolution "
              "render and a glyph-level dump when the previous tutorial was written. This tutorial uses "
              "the formula as printed. The printed form gives lower peaks than the published one: on the "
              "self-cleansing side that is the cautious direction, and on these small pipes the minimum "
              "diameter, not the peak, sets the size. Whether NWS meant 2.5 is a question for NWS.",
              fill="EAF1F8", colour=D.MID)
    qpp = PW["ib_q_ult"] / PW["ib_props_ult"]
    q100 = N_THRESH * qpp
    pm, pp = merrimack(q100) / q100, peltier_pf(q100)
    _lead(d, "Ibri number.  ", f"An Ibri property at saturation makes {qpp:.3f} m³/d on average "
          f"({f(PW['ib_q_ult'])} m³/d over {f(PW['ib_props_ult'])} properties, shops and offices "
          f"included). A catchment of exactly 100 such properties makes {f(q100, 1)} m³/d, which is "
          f"{q100 / LS:.3f} l/s. Peltier gives 1.5 + 1/√{q100 / LS:.3f} = {pp:.2f}. One more property "
          f"moves the pipe to Merrimack, which gives {pm:.2f}: the peak jumps by "
          f"{(pm / pp - 1) * 100:.0f} % at the threshold. The jump belongs to the two formulas, not to "
          "the calculation, and it is why the formula is recorded with every peak.")
    _src(d, "G201-p72 §7.4.2: the formula, the note that Qm is in litres per second, and its IMP2024 origin.")
    _where(d, "Function peltier_pf in this chapter's script; the test-area design stored the Peltier "
              "factor as PF_PELT in W8/shp/W8_pipes.shp, on its earlier flat loads.")

    # ---------------------------------------------------------------- 9.6
    D.h(d, 2, "9.6   The hourly peak factor of 5.0")
    _lead(d, "What it is for.  ", "To limit the factor at the very top of the network, where Peltier "
                                  "grows without bound as the flow goes to zero.")
    qcap = LS * (PT_B / (PF_REC - PT_A)) ** 2
    _lead(d, "The rule.  ", "The guideline recommends that the hourly peak factor should not exceed "
          "5.0. It is a recommendation, not a limit. The design computes the factor uncapped, and "
          "where it applies 5.0 instead it says so for that pipe; it never truncates silently. With "
          f"the printed Peltier, the factor passes 5.0 below an average of {qcap / LS:.4f} l/s, which "
          f"is {qcap:.2f} m³/d.")
    _src(d, "G201-p72, the second note under the Peltier formula. The factor it limits is the hourly "
            "one, which is the sense in which the network uses the peak (Section 9.11).")
    _lead(d, "Ibri number.  ", f"On the test area, {f(st['ult']['over5'])} loaded street pipes have an "
          f"uncapped factor above 5.0 at saturation and {f(st['low']['over5'])} in the {OPEN_YEAR} low "
          f"case. They are the first pipes below a head. A single Ibri plot at saturation makes about "
          f"one cubic metre a day, and Peltier gives it a factor of {peltier_pf(1.0):.1f}. The capacity "
          "test on these pipes is not affected, because the minimum diameter governs them.")
    oc, occ = st["over5_cls"], st["over5_cls_capped"]
    assert oc["velocity pass"] == 0 and st["over5_dn"] == [200], "the Section 9.6 group has changed: rewrite it"
    D.p(d, f"The self-cleansing audit of Chapter 12 judges these pipes on their uncapped low-case peak, "
           f"at τ = {TAU:g} Pa, on the gradients the test-area design laid. All {f(st['low']['over5'])} are "
           f"DN200 secondary main sewers, at the G203 Table 11 minimum or steeper, on the {STEP_SEC / 10:g} % "
           f"step. None reaches 0.75 m/s. {f(oc['tractive pass'])} are laid at or above their tractive "
           f"minimum and pass on the second test; the other {f(oc['needs washing'])} need washing and go "
           "on the flushing list. Held to a factor of 5.0 the peak would be smaller, and "
           f"{f(occ['needs washing'] - oc['needs washing'])} more pipes would need washing.")
    _where(d, "Peak factor per pipe: function peak in this chapter's script, uncapped. The class of each "
              "pipe: function audit_class in the same script. The class rule: "
              "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §4 and design_flows.json rules.rulings_confirmed.classes.")

    # ---------------------------------------------------------------- 9.7
    D.h(d, 2, "9.7   Units")
    _lead(d, "What it is for.  ", "The two formulas sit on facing pages and want different units. "
          "Every mistake in this chapter that is not arithmetic is a unit mistake.")
    _lead(d, "The rule.  ", "Store plot flows in m³/d. Convert at the formula, and convert back.")
    D.tab_caption(d, "Conversions used in the peak and infiltration steps")
    D.table(d, ["From", "To", "Operation"],
            [["m³/d", "Ml/d (Merrimack)", "÷ 1,000"],
             ["m³/d", "l/s (Peltier, pipe hydraulics)", "÷ 86.4"],
             ["l/d per km, length in m", "m³/d", "× length ÷ 1,000 ÷ 1,000"],
             ["Merrimack in Ml/d", "Merrimack in m³/d", f"Qpdf = {MK_M3D:.3f} × Qadf^0.879, both in m³/d"]],
            widths=[5.0, 5.0, 6.5], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "The m³/d form of Merrimack follows from the first: 1,000 × 2.65 × (Q/1,000)^0.879 equals "
           f"2.65 × 1,000^0.121 × Q^0.879, and 1,000^0.121 is {1000 ** (1 - MK_E):.4f}.")
    _eq(d, Qs("pdf"), M.EQ, R(f"{MK_M3D:.3f}"), M.TIMES, M.sup(Qs("adf"), R("0.879")),
        R("     "), UP("(both in m³/d)"))
    _src(d, "G201-p71 (Ml/d), G201-p72 (l/s). The constant is derived here, it is not a guideline value.")
    _lead(d, "Ibri number.  ", f"The saturation flow of the study area, {f(t['q_ult'])} m³/d, is "
          f"{t['q_ult'] / 1000:.3f} Ml/d or {f(t['q_ult'] / LS)} l/s. Merrimack gives "
          f"{f(merrimack(t['q_ult']))} m³/d by either form.")
    _where(d, "Constants LS and MK_M3D in this chapter's script.")

    # ---------------------------------------------------------------- 9.8
    D.h(d, 2, "9.8   Infiltration")
    _lead(d, "What it is for.  ", "Groundwater enters a sewer through joints, cracks, connections "
          "and chambers. It takes capacity, adds pumping and treatment, and has to be designed for.")
    _lead(d, "The rule.  ", f"A new sewer carries {INF:.0f} litres a day per kilometre of its own "
          "length. The allowance belongs to the pipe, not to the plot: each pipe adds it for its own "
          "length and passes it downstream, so a pipe carries the allowance of all the sewer above "
          "it. It is added after the peak and is not peaked itself, because a steady leak does not "
          "follow the daily cycle. Storm water is not considered. Flow collected by tanker or vacuum "
          "truck carries no infiltration.")
    _eq(d, Qs("inf"), M.EQ, M.frac(M.seq(R("i"), M.TIMES, R("L")), M.sup(R("10"), R("6"))))
    _eq(d, M.sub(R("Q"), UP("design")), M.EQ, Qs("pdf"), M.PLUS, Qs("inf"))
    _sym(d, [["Q inf", "infiltration carried by the pipe", "m³/d"],
             ["i", f"infiltration rate for a new sewer, {INF:.0f}", "l/d per km"],
             ["L", "length of sewer upstream of the pipe's lower end, the pipe included", "m"],
             ["Q design", "flow the pipe is sized on", "m³/d, then l/s"]])
    D.tab_caption(d, "Infiltration allowances in the guideline")
    D.table(d, ["Network", "Allowance"],
            [["**Newly designed network**", f"**{INF:.0f} l/d per km of sewer**"],
             ["Existing network, inland or outside groundwater influence", "10 % of the wastewater flow"],
             ["Existing network in a groundwater zone or coastal area", "up to 40 % of the wastewater flow"],
             ["Tanker or vacuum collection", "none"]],
            widths=[10.5, 6.0], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "Two of the allowances are shares of flow and one is a rate per length, so they are not "
           "interchangeable. The 10 % and 40 % apply only where an existing network is kept in "
           "service, and choosing between them needs groundwater evidence for that network. The "
           "guideline does not say whether infiltration is added before or after peaking; adding it "
           "after is the project's practice.")
    km = W8RUN["net_km"]
    _lead(d, "Ibri number.  ", f"The test-area design has {f(km, 2)} km of sewer. At {INF:.0f} l/d per "
          f"km that is {f(inf_m3d(km * 1000), 1)} m³/d, against {f(N['q_ult_in'])} m³/d of saturation "
          f"sewage from the same plots: {inf_m3d(km * 1000) / N['q_ult_in'] * 100:.1f} %. Infiltration "
          "is small in a new, inland network. It still matters at the plant, where it arrives every "
          "hour of the year.")
    _src(d, "G201-p72 §7.4.3 (the three allowances; the volume must be accounted for; storm water not "
            "considered); G201-p73 (tanker or vacuum collection needs none). Added after peaking: "
            "project practice, the guideline is silent on the order.")
    _where(d, "design_flows.json rules.infiltration_l_per_day_per_km and rules.infiltration_applies; "
              "pipe lengths LEN_M in W8/shp/W8_pipes.shp; total length net_km in W8/run/summary.json.")

    # ---------------------------------------------------------------- 9.9
    D.h(d, 2, "9.9   Two flow cases in every pipe")
    _lead(d, "What it is for.  ", "One flow cannot serve two tests. The capacity test fails on an "
          "under-estimate of flow. The self-cleansing test fails on an over-estimate, because a pipe "
          "credited with flow it does not get is declared self-cleansing while it silts.")
    _lead(d, "The rule.  ", f"Size on the saturation flow, Q_ULT, fully connected. Check "
          f"self-cleansing on the opening-year flow, Q_{OPEN_YEAR}, times the connection ratio "
          f"{CONN:.2f}. Sum each case upstream, count its properties and peak it by its own formula. "
          f"In the low case the properties counted are the connected ones, those standing in "
          f"{OPEN_YEAR} times {CONN:.2f}, and no infiltration is added. The low-case peak feeds the two "
          "tests of the self-cleansing audit, velocity first and tractive force second (Chapter 12), "
          "which put every pipe in one of three classes: velocity pass, tractive pass or needs washing. "
          "Never use saturation times the ratio.")
    _eq(d, M.sub(R("Q"), UP("low")), M.EQ, R(f"{CONN:.2f}"), M.TIMES,
        M.nary("∑", M.seq(R("i"), R(" ∈ "), UP("up")), "", M.sub(R("q"), UP(f"{OPEN_YEAR},i")), hide_hi=True))
    _sym(d, [["Q low", "low-case average flow for the self-cleansing test", "m³/d"],
             [f"q {OPEN_YEAR},i", f"average flow of plot i in {OPEN_YEAR} (Q_{OPEN_YEAR})", "m³/d"],
             [f"{CONN:.2f}", "share of properties connected, reached by 2028 in the Inception Report", "—"]])
    wrong = tot[str(ult)]["qadf_m3d"] * CONN
    _lead(d, "Ibri number.  ", f"For the whole study area the low case is "
          f"{f(tot[str(OPEN_YEAR)]['qadf_m3d'])} × {CONN:.2f} = {f(FLOWS['low_case_2030_m3d'])} m³/d. "
          f"Saturation times the ratio would give {f(wrong)} m³/d, "
          f"{wrong / FLOWS['low_case_2030_m3d']:.1f} times as much. The error concentrates in the new "
          f"districts: a pipe in an empty district would be credited with {CONN * 100:.0f} % of its "
          f"saturation flow in {OPEN_YEAR}, when it carries almost nothing.")
    _src(d, "Project rule (engineer, 2026-09-11), _BRAIN/02_DESIGN_CRITERIA.md §1, the two-flow-case "
            "row. Coverage 100 % by the end of the planning period: G201-p73 §7.4.4. The opening year "
            "is the construction year or 2030 (Terms of Reference). The self-cleansing tests: G203 "
            "§4.2.2.1, pp 25–27; early phases: G203 §4.2.6, p28. The connected count, no infiltration "
            "in the low case and the three classes: project rules (engineer, 2026-09-11), "
            "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §8. G201 §7.4.3 (p72) sets the infiltration allowance "
            "and says nothing of the early years; G201 §7.4.4 (p73) asks only that the early flow be "
            "considered at the initial stage of operations, to ensure self-cleaning velocities.")
    fl = st["flip"]
    band_hi = N_THRESH / CONN
    fl_dir = ("every one of them gets a lower low-case peak" if fl["lower"] == fl["n"]
              else f"{f(fl['lower'])} of them get a lower low-case peak")
    D.callout(d, "Why the connected count, and no infiltration.",
              "A property that is not yet connected sends nothing down the pipe, so counting it would "
              "choose the formula for flow the pipe does not carry. Near the threshold the count "
              "decides the formula. A pipe with more than 100 "
              f"and up to about {band_hi:.1f} properties standing ({N_THRESH + 1} to "
              f"{math.floor(band_hi)} in whole properties) has 100 or fewer connected, so it takes "
              f"Peltier instead of Merrimack. On the test area {f(fl['n'])} pipes sit in that band and "
              f"{fl_dir}, which is the cautious direction for this test. Counted on the properties "
              f"standing, {f(st['low_standing']['merr'])} pipes would take Merrimack in the low case "
              f"instead of {f(st['low']['merr'])}. Infiltration is left out for the same reason: a "
              "steady leak credited to the pipe would count as flow that cleans it, and adding flow is "
              "the unsafe direction for this test.",
              fill="EAF1F8", colour=D.MID)
    _where(d, f"W14/shp/PLOTS_load.shp fields Q_ULT and Q_{OPEN_YEAR}; design_flows.json keys "
              "rules.size_on, rules.self_cleansing_on, rules.connection_ratio_2030, low_case_2030_m3d and "
              "rules.rulings_confirmed (low_case_property_count, low_case_infiltration, classes).")

    # ---------------------------------------------------------------- 9.10
    D.h(d, 2, "9.10   A worked pipe in Ibri")
    ww = N["worked"]
    cu = _case(w.Q_ULT, w.PR_ULT, w.LEN)
    cl = _case(w.Q_LOW, w.PR_LOW)
    cl_inf = inf_m3d(w.LEN)
    _lead(d, "What it is for.  ", "To run Sections 9.2 to 9.9 once, end to end, on a real street "
                                  "sewer with real plots.")
    D.p(d, f"The pipe is {ww} of the test-area design, a secondary main sewer (Chapter 10) of "
           f"DN{int(w.DN_MM)} laid at {w.SLOPE_PCT:.2f} %, from chamber {w.ND_UP} to {w.ND_DN}. It is "
           "the street main sewer that carries the most properties at saturation without itself "
           f"joining the main pipe. Above its lower end are {int(round(w.ONE))} plots on "
           f"{f(w.LEN)} m of sewer: {int(round(w.ONE - w.FUT))} built and {int(round(w.FUT))} empty, "
           f"with {int(round(w.G_DOM))} domestic properties counted today. Each plot of the test "
           "area is given to its nearest street pipe, and the sums run down the design's own tree.")
    ql_u, ql_l = cu["q"] / LS, cl["q"] / LS
    rows = [
        ["Plots upstream", f(w.ONE), f(w.ONE)],
        ["Average flow of the year, Σ plots, m³/d", f"{f(w.Q_ULT, 2)} (Q_ULT)", f"{f(w.Q_2030, 2)} (Q_{OPEN_YEAR})"],
        ["Connection ratio", "1.00", f"{CONN:.2f}"],
        ["**Average flow of the case, m³/d**", f"**{f(cu['q'], 2)}**", f"**{f(cl['q'], 2)}**"],
        ["   in Ml/d", f"{cu['q'] / 1000:.4f}", f"{cl['q'] / 1000:.4f}"],
        ["   in l/s", f"{ql_u:.3f}", f"{ql_l:.3f}"],
        ["Properties upstream, Σ (G_DOM + ΔP / OR_S)", f"{w.PR_ULT:.1f}", f"{w.PR_30:.1f} standing"],
        ["Properties counted for the formula", f"{w.PR_ULT:.1f}",
         f"{w.PR_LOW:.1f} connected (× {CONN:.2f})"],
        ["Formula", _how(cu), _how(cl)],
        ["Peak factor", f"{cu['pf']:.2f}", f"{cl['pf']:.2f}"],
        ["Peak flow, l/s", f"{cu['qp'] / LS:.2f}", f"{cl['qp'] / LS:.2f}"],
        [f"Infiltration, {f(w.LEN)} m at {INF:.0f} l/d per km, l/s", f"{cu['qi'] / LS:.4f}", "not added"],
        ["**Design flow, l/s**", f"**{(cu['qp'] + cu['qi']) / LS:.2f}**", f"**{cl['qp'] / LS:.2f}**"],
        ["Used for", "capacity: d/D and maximum velocity", "the audit: velocity, then tractive force"],
    ]
    D.tab_caption(d, f"Design flows of {ww}, a secondary main sewer in Ibri")
    D.table(d, ["Step", "Sizing case, saturation", f"Low case, {OPEN_YEAR}"], rows,
            widths=[7.3, 4.6, 4.6], font=9)
    D.p(d, "", space_after=2)
    alt_u = peltier_pf(cu["q"]) if cu["how"] == "Merrimack" else merrimack(cu["q"]) / cu["q"]
    alt_l = merrimack(cl["q"]) / cl["q"] if cl["how"] == "Peltier" else peltier_pf(cl["q"])
    D.p(d, f"Read the table step by step. At saturation the {int(round(w.ONE))} plots make "
           f"{f(cu['q'], 2)} m³/d, which is {cu['q'] / 1000:.4f} Ml/d. They hold {w.PR_ULT:.1f} "
           f"properties, so {cu['how']} applies"
           + (f": {MK_C} × {cu['q'] / 1000:.4f}^{MK_E} = {cu['qp'] / 1000:.4f} Ml/d, a factor of "
              if cu["how"] == "Merrimack" else f": 1.5 + 1/√{ql_u:.3f}, a factor of ")
           + f"{cu['pf']:.2f} and a peak of {cu['qp'] / LS:.2f} l/s. Infiltration on {f(w.LEN)} m is "
           f"{f(cu['qi'] * 1000)} l/d, or {cu['qi'] / LS:.4f} l/s, which brings the design flow to "
           f"{(cu['qp'] + cu['qi']) / LS:.2f} l/s. In the low case the same plots make "
           f"{f(w.Q_2030, 2)} m³/d in {OPEN_YEAR}; {CONN:.2f} of that is {f(cl['q'], 2)} m³/d, or "
           f"{ql_l:.3f} l/s. In {OPEN_YEAR} {w.PR_30:.1f} properties stand and {w.PR_LOW:.1f} of them "
           f"are connected, so {cl['how']} applies"
           + (f": 1.5 + 1/√{ql_l:.3f} = {cl['pf']:.2f}" if cl["how"] == "Peltier"
              else f", a factor of {cl['pf']:.2f}")
           + f", and the peak is {cl['qp'] / LS:.2f} l/s.")
    D.p(d, f"This pipe sits on the threshold, which is why it makes a good example. With the other "
           f"formula the saturation factor would be {alt_u:.2f} instead of {cu['pf']:.2f}, and the "
           f"low-case factor {alt_l:.2f} instead of {cl['pf']:.2f}. The low-case figure is the one "
           f"that matters: the self-cleansing tests on this pipe are judged on {cl['qp'] / LS:.2f} "
           f"l/s, and the other formula would have credited it with {alt_l * cl['q'] / LS:.2f} l/s.")
    D.p(d, f"The low case is taken without infiltration (Section 9.9). Here the allowance would add "
           f"{cl_inf / LS:.4f} l/s to {cl['qp'] / LS:.2f} l/s and could not change the result; on a long "
           "pipe with very little flow it could.")
    dn_w, s_w, q_w = int(w.DN_MM), w.SLOPE_PCT * 10.0, cl["qp"] / LS
    cls_w, v_w = audit_class(dn_w, s_w, q_w)
    sm_w = {t: smin_mara(q_w, t) for t in (TAU, 1.5, 2.0)}
    assert abs(s_w - on_grid(TAB11_MIN[dn_w], grid_step(dn_w))) < 1e-9, f"{ww} is no longer at its Table 11 step"
    assert cls_w == "tractive pass" and audit_class(dn_w, s_w, q_w, 1.5)[0] == "needs washing", \
        f"{ww} has moved out of its stated class ({cls_w}): rewrite Section 9.10"
    D.p(d, f"The audit then judges {q_w:.2f} l/s on the gradient the pipe is laid at, {w.SLOPE_PCT:.2f} % "
           f"or {s_w:.1f} mm/m: the G203 Table 11 minimum for DN{dn_w}, on the {grid_step(dn_w) / 10:g} % "
           f"step of Section 10.6. Part full at that flow it runs at {v_w:.2f} m/s, short of 0.75 m/s, so "
           f"it is not a velocity pass. Its tractive minimum at τ = {TAU:g} Pa, with Q in m³/s, is "
           f"{K_M3S * 1e4:.2f} × 10⁻⁴ × {TAU:g}^1.23 × {q_w / 1000:.6f}^−0.461 = {sm_w[TAU] / 1000:.5f}, "
           f"or {sm_w[TAU]:.2f} mm/m. The pipe is laid steeper than that, so it is a tractive pass. The "
           f"margin is thin: at 1.5 Pa it would need {sm_w[1.5]:.2f} mm/m, and at 2 Pa {sm_w[2.0]:.2f} "
           f"mm/m, and would go on the flushing list. The class is decided at {TAU:g} Pa, the value NWS "
           "is asked to confirm.")
    hu = _case(hd.Q_ULT, hd.PR_ULT, hd.LEN)
    hl = _case(hd.Q_LOW, hd.PR_LOW)
    D.p(d, f"For scale, the same steps on {N['header']}, the header at the largest join of the test "
           f"area (DN{int(hd.DN_MM)}), which collects {f(hd.ONE)} plots from {f(hd.LEN / 1000, 2)} km "
           "of sewer:")
    D.tab_caption(d, f"Design flows of {N['header']}, a secondary header at its join to the main pipe")
    D.table(d, ["Case", "Average, m³/d", "Properties", "Formula", "Pf", "Peak, l/s", "Infiltration, l/s", "Design, l/s"],
            [["Saturation", f(hu["q"], 1), f(hd.PR_ULT), hu["how"], f"{hu['pf']:.2f}", f"{hu['qp'] / LS:.2f}",
              f"{hu['qi'] / LS:.3f}", f"**{(hu['qp'] + hu['qi']) / LS:.2f}**"],
             [f"Low, {OPEN_YEAR} × {CONN:.2f}", f(hl["q"], 1), f"{f(hd.PR_LOW)} connected", hl["how"],
              f"{hl['pf']:.2f}",
              f"{hl['qp'] / LS:.2f}", "not added", f"**{hl['qp'] / LS:.2f}**"]],
            widths=[2.9, 2.0, 1.8, 2.0, 1.2, 1.9, 2.4, 2.1], font=8.5, align_right={1, 2, 4, 5, 6, 7})
    D.p(d, "", space_after=2)
    D.p(d, f"The header's factor is {hu['pf']:.2f} against {cu['pf']:.2f} for the street sewer, on "
           f"{hu['q'] / cu['q']:.0f} times the flow. Its infiltration, {hu['qi'] / LS:.3f} l/s, is "
           f"{hu['qi'] / hu['qp'] * 100:.1f} % of its peak.")
    _src(d, "Formulas G201-p71–72; infiltration G201-p72; cases and threshold as in Sections 9.3 and 9.9. "
            "Self-cleansing velocity 0.75 m/s G203-p26; tractive minimum G203-p27, with K for Q in m³/s "
            f"and τ = {TAU:g} Pa by project rule (engineer, 2026-09-11), τ for NWS to confirm; minimum "
            "gradient G203-p29 Table 11.")
    _where(d, f"Pipes {ww} and {N['header']} in W8/shp/W8_pipes.shp (fields LABEL, ND_UP, ND_DN, "
              "DN_MM, SLOPE_PCT, LEN_M, TIER, IS_JOIN); plots in W14/shp/PLOTS_load.shp; the "
              "allocation and summation in _net() of this chapter's script. The test-area design's own "
              "flow fields (N_PROPS, QADF_M3D, PF, QPEAK_LS) were built on the earlier flat load per "
              "property and do not match this table.")

    # ---------------------------------------------------------------- 9.11
    D.h(d, 2, "9.11   The flows at the treatment plant")
    _lead(d, "What it is for.  ", "The plant is sized on three flows, not one. Structures the flow "
          "passes through are sized on the peak hour; biological treatment is sized on the annual "
          "average with the inlet load.")
    _lead(d, "The rule.  ", "The incoming flow is the average sewage flow plus the infiltration of the "
          f"network, increased by {MARGIN * 100:.0f} % as an operational safety allowance. The "
          "allowance sits on top of any duty and standby redundancy and is never netted against it. "
          "The peak hour is the Merrimack peak of the accumulated flow at the plant: the guideline "
          "equates the design peak hourly flow with Qpdf, the quantity Merrimack returns.")
    _eq(d, Qs("AAF"), M.EQ, M.delim(M.seq(R("1"), M.PLUS, R("m"))), M.TIMES,
        M.delim(M.seq(Qs("adf"), M.PLUS, Qs("inf"))))
    _eq(d, Qs("PHF"), M.EQ, M.delim(M.seq(R("1"), M.PLUS, R("m"))), M.TIMES,
        M.delim(M.seq(Qs("pdf"), M.PLUS, Qs("inf"))))
    _sym(d, [["Q AAF", "average annual flow, the design average flow", "m³/d"],
             ["Q PHF", "peak hourly flow", "m³/d"],
             ["Q adf ; Q pdf", "average and Merrimack peak of the sewage reaching the plant", "m³/d"],
             ["Q inf", f"infiltration of the whole network upstream, {INF:.0f} l/d per km", "m³/d"],
             ["m", f"design margin, {MARGIN:.2f}", "—"]])
    D.p(d, "The maximum day flow, the largest 24-hour volume, is defined by the guideline, but no "
           "factor for it is given anywhere in PAM-GUD-201 or PAM-GUD-203. It stays open until NWS "
           "supplies inflow records for its plants or confirms the standard to be used for design flows "
           "(the guideline names BS EN 752 and the British Water Code of Practice for Flows and Loads). "
           "The margin is carried on the peak hour as well as on the average; that is a reading of "
           "Table 29, which applies it to the incoming flows.")
    yrs = [OPEN_YEAR, 2055, ult]
    qa = [t["q"][y] for y in yrs]
    rows = [["Average sewage from the plots, m³/d"] + [f(x) for x in qa],
            ["Merrimack peak factor"] + [f"{merrimack(x) / x:.2f}" for x in qa],
            ["Peak hour before margin, m³/d"] + [f(merrimack(x)) for x in qa],
            ["   in l/s"] + [f(merrimack(x) / LS) for x in qa],
            [f"**Average annual flow with {MARGIN * 100:.0f} %, m³/d**"] + [f"**{f(x * (1 + MARGIN))}**" for x in qa],
            [f"**Peak hourly flow with {MARGIN * 100:.0f} %, m³/d**"] + [f"**{f(merrimack(x) * (1 + MARGIN))}**" for x in qa],
            ["Infiltration with margin, add to both", f"+ {INF * (1 + MARGIN) / 1000:.3f} m³/d per km of network", "", ""],
            ["Maximum day flow", "no factor in the guidelines", "", ""]]
    D.tab_caption(d, "Flows at the plant if the whole study area drains to one works, before infiltration and tankers")
    D.table(d, ["Flow", str(OPEN_YEAR), "2055", f"Saturation, {ult}"], rows,
            widths=[7.0, 3.2, 3.0, 3.3], font=9, align_right={1, 2, 3})
    D.p(d, "", space_after=2)
    _lead(d, "Ibri number.  ", f"At saturation the plant average before infiltration is "
          f"{f(t['q_ult'])} × {1 + MARGIN:.2f} = {f(FLOWS['stp_ultimate_with_margin_m3d'])} m³/d, the "
          f"figure in the design-flow handoff. The peak hour is {f(merrimack(t['q_ult']) * (1 + MARGIN))} "
          f"m³/d, a factor of {merrimack(t['q_ult']) / t['q_ult']:.2f} on the average. The full-area "
          "network has not been laid, so its infiltration cannot be totalled yet; each 100 km of new "
          f"sewer will add {f(inf_m3d(100000) * (1 + MARGIN), 1)} m³/d with the margin. Tanker "
          "deliveries are added when their records arrive. The table assumes one works for the whole "
          "area; the plant options decide how the flow is split.")
    _src(d, "G203-p65 Table 29 (incoming flow; AAF, MDF and PHF defined, PHF = QPDF), G203-p66 "
            "(pass-through structures on PHF, biology on AAF and load), G201-p73 §7.4.5 (10 % margin "
            "for new STPs, over and above redundancy), G201-p71 (BS EN 752 and British Water named for "
            "project-specific design flows).")
    _where(d, "Totals by year: W14/analysis/W14_growth_by_settlement.xlsx, sheet Qadf by year m3d, "
              "through facts_w14.totals(); design_flows.json stp_ultimate_with_margin_m3d.")

    # ---------------------------------------------------------------- 9.12
    D.h(d, 2, "9.12   Check it yourself")
    ibri = next(s for s in FLOWS["settlements"] if s["key"] == "IBRI")
    D.numbered(d, "In QGIS, open W14/shp/PLOTS_load.shp, filter SETTLE = 'IBRI' and sum Q_ULT. You "
                  f"should get {f(PW['ib_q_ult'], 1)} m³/d, which matches the Ibri row of "
                  f"design_flows.json, {f(ibri['q_ult'], 1)}, within its rounding.", restart=True)
    D.numbered(d, "In the same layer, compute \"G_DOM\" + (\"POP_ULT\" - \"POP\") / \"OR_S\" with the "
                  "field calculator and sum it over the whole layer. It should be close to "
                  f"{f(FLOWS['properties']['ultimate'])} properties.")
    D.numbered(d, "In a spreadsheet, enter =1000*2.65*(Q/1000)^0.879 with Q the study-area saturation "
                  f"flow, {f(t['q_ult'])}. You should get {f(merrimack(t['q_ult']))} m³/d. Then drop "
                  "the two factors of 1,000 and see how far the answer moves.")
    D.numbered(d, f"Select pipe {ww} in W8/shp/W8_pipes.shp and every pipe upstream of chamber "
                  f"{w.ND_UP}, then the plots of the test area whose nearest street pipe is in that set. "
                  f"You should find {int(round(w.ONE))} plots and {f(w.Q_ULT, 2)} m³/d of Q_ULT.")
    D.numbered(d, f"For the same pipe, enter ={K_M3S:g}*{TAU:g}^1.23*{q_w / 1000:.6f}^-0.461*1000 in a "
                  f"spreadsheet. You should get {sm_w[TAU]:.2f} mm/m, below the {s_w:.1f} mm/m it is laid "
                  f"at: a tractive pass at {TAU:g} Pa.")
    D.numbered(d, f"Check that the low case of the study area is {f(tot[str(OPEN_YEAR)]['qadf_m3d'])} × "
                  f"{CONN:.2f} = {f(FLOWS['low_case_2030_m3d'])} m³/d, and that no calculation uses "
                  f"{f(wrong)} m³/d instead.")
    D.numbered(d, "Re-read G201 pages 71 to 73 and G203 pages 65 and 66 against Sections 9.3 to 9.11. "
                  "Every constant here is on those pages, except the connection ratio, which comes from "
                  "the Inception Report.")


# ===================================================================== 10
def c10_tiers(d):
    import geopandas as gpd
    N = _net()
    PW = _plotwide()
    pipes = gpd.read_file(os.path.join(W8, "shp", "W8_pipes.shp"))
    by = pipes.groupby("TIER").LEN_M.agg(["count", "sum"])
    tot_m = float(by["sum"].sum())
    tr = W8RUN["trunk"]

    D.h(d, 1, "10   The network and its tiers", page_break=True)
    D.p(d, "A sewer network is a hierarchy. Houses drain into short connecting pipes, those into the "
           "street sewers, the street sewers into a few collecting mains, and only the collecting mains "
           "reach the trunk to the plant. This chapter sets out the guideline's names for those tiers, "
           "the names this project uses from now on, what the built network teaches about how the "
           "tiers connect, and the fixed inputs every layout starts from.")

    # ---------------------------------------------------------------- 10.1
    D.h(d, 2, "10.1   What the tiers are for")
    _lead(d, "What it is for.  ", "The tier of a pipe decides its minimum diameter, the gradient "
          "table it follows, what it may connect to, and what it is called in the drawings and the "
          "model. A layout without tiers is a set of branches; a layout with them can be built.")
    _lead(d, "The rule.  ", "Every pipe carries one tier, named in the guideline's words.")
    _src(d, "G203 §3.2, p17; G203 §4, p21; G203 §5, p35.")
    _lead(d, "Ibri number.  ", f"Every one of the {f(len(pipes))} pipes of the test-area design carries "
          "a tier value; Section 10.4 shows how those values translate.")
    _where(d, "Field TIER of the pipe layer of every design run.")

    # ---------------------------------------------------------------- 10.2
    D.h(d, 2, "10.2   The guideline's three tiers")
    _lead(d, "What it is for.  ", "To use the same words as NWS, so that a pipe called a lateral in "
                                  "our drawings is what NWS means by a lateral.")
    _lead(d, "The rule.  ", "The guideline divides the gravity network into three tiers.")
    D.tab_caption(d, "The tiers of a gravity sewer network in PAM-GUD-203")
    D.table(d, ["Tier", "Pipes", "What it does", "Size", "Gradient", "Page"],
            [["**Primary**", "Trunk mains", "Carries the wastewater of the catchments to the main pumping "
              "station or the plant. NWS applies the term to pipes above 800 mm, over 1,000 without "
              "connections (the page prints mm), upstream of the plant or main station.",
              "Material table from 600 mm", "G203 Table 11", "G203-p35"],
             ["**Secondary**", "Headers and main sewers", "The headers or main sewers laid under the streets, "
              "serving the watersheds and taking the tertiary network's flow to the trunk mains.",
              "Main sewer OD200 minimum; typically 200 to 400 mm, the 400 not mandatory",
              "G203 Table 11: DN200 5.00 mm/m, flatter for larger pipes", "G203-p21, p22, p23, p29"],
             ["**Tertiary**", "Rider sewers and lateral sewers, with the property connection sewers often "
              "counted in", "Collects from the house connection chambers and discharges into a main sewer.",
              "Rider OD160, lateral OD200 minimum; lateral at most 45 m long",
              "G203 Table 5: 1 % to 10 %", "G203-p17, p18, p22"]],
            widths=[1.9, 2.6, 5.4, 2.9, 2.2, 1.6], font=8.5)
    D.p(d, "", space_after=2)
    D.p(d, "Two things in this table catch people out. First, the guideline's lateral is a short pipe, "
           "at most 45 m, from a house connection chamber or a rider to the main sewer. It is not a "
           "street pipe. Second, the tertiary gradients are separate from G203 Table 11 and much steeper: a "
           "lateral needs at least 1 %, while G203 Table 11 lets a DN200 main sewer run at 0.5 %. Laying a "
           "lateral at the main sewer's minimum is a design error.")
    _src(d, "G203-p17 §3.2 (the tiers named, the 45 m lateral), G203-p18 Table 5 (tertiary slopes), "
            "G203-p21 §4 (secondary and tertiary defined), G203-p22 Table 6 (minimum sizes), G203-p23 "
            "(secondary range), G203-p29 Table 11 (via _BRAIN/02_DESIGN_CRITERIA.md §2), G203-p35 §5 "
            "(trunk mains).")
    _lead(d, "Ibri number.  ", f"On the test area, {f(by.loc['lateral', 'count'])} street pipes, "
          f"{f(by.loc['lateral', 'sum'] / 1000, 1)} km, are secondary main sewers. Not one of them is a "
          "guideline lateral: the tertiary layer has not been drawn yet (Section 10.9).")
    _where(d, "_BRAIN/02_DESIGN_CRITERIA.md §2 (tier names read from the PDF on 2026-09-11) and §3 "
              "(minimum sizes, trunk definition).")

    # ---------------------------------------------------------------- 10.3
    D.h(d, 2, "10.3   From the house to the main sewer")
    _lead(d, "What it is for.  ", "The tertiary layer is where the network meets the plot. Its "
                                  "rules decide how deep the street sewer must be to take a house.")
    _lead(d, "The rule.  ", "The wastewater of a property passes, in order, through the property "
          "connection chamber inside the plot at its boundary, the property connection sewer, the "
          "house connection chamber in the public right of way, sometimes a rider sewer, and a lateral "
          "sewer into the main sewer.")
    D.tab_caption(d, "The tertiary chain and its limits")
    D.table(d, ["Element", "Where", "Limit", "Page"],
            [["Property connection chamber", "inside the property, at the boundary", "—", "G203-p17"],
             ["Property connection sewer", "chamber to house connection chamber",
              "150 mm minimum (OD160 in G203 Table 6); at most 50 m long; slope 3 % to 10 %", "G203-p18, p22"],
             ["House connection chamber", "usually 2.5 m from the property boundary, in the right of way",
              "usually 1.2 m to 2.0 m deep; stubs or plugged ports for future connections", "G203-p17, p19"],
             ["Rider sewer", "links house connection chambers, usually up to 3", "OD160 minimum; slope 1 % to 10 %",
              "G203-p17, p18, p22"],
             ["Lateral sewer", "house connection chamber or rider to the main sewer",
              "OD200 minimum; at most 45 m; slope 1 % to 10 %", "G203-p17, p18, p22"]],
            widths=[3.6, 5.0, 6.0, 1.9], font=8.5)
    D.p(d, "", space_after=2)
    _src(d, "G203 §3.2 to §3.4, pp 17–19; G203 Table 6, p22.")
    _lead(d, "Ibri number.  ", f"The test area holds {f(N['plots_in'])} plots. The median distance from "
          f"a plot's representative point to its nearest street pipe is {f(N['dist_med'], 1)} m, inside "
          "the 45 m a lateral may run. The plots far from any street pipe are the ones the tertiary "
          "layer will have to test one by one.")
    _where(d, "Not in the design engine yet: the current scope is street sewers only (Section 10.9).")

    # ---------------------------------------------------------------- 10.4
    D.h(d, 2, "10.4   The old tier values and the names used from now on")
    _lead(d, "What it is for.  ", "To remove a clash of words. The design engine and NAMA's as-built "
          "data both say lateral for the street pipe, which the guideline calls a main sewer.")
    _lead(d, "The rule.  ", "From now on the street pipe is a secondary main sewer, the collecting "
          "main of a district is a secondary header, and the trunk is primary. The word lateral is "
          "kept for the tertiary pipe alone. Outputs made before the change keep their old values as "
          "the record and are read through the mapping below.")
    rows = []
    for old, later, new, what in (
            ("trunk main", "trunk", "Primary: trunk main", "the pipe to the plant, including the main pipe"),
            ("sub main", "sub main", "Secondary: header", "the collecting main of a district; the only pipe that joins the trunk"),
            ("lateral", "lateral, branch", "Secondary: main sewer", "the street sewer every plot connects to")):
        rows.append([old, later, f"**{new}**", what, f(by.loc[old, "count"]), f(by.loc[old, "sum"] / 1000, 2)])
    rows.append(["—", "—", "**Tertiary: rider, lateral**", "house connection chamber to main sewer, at most 45 m", "0", "0"])
    D.tab_caption(d, "Tier values in the engine outputs and the names used from now on")
    D.table(d, ["Test-area design", "Later engine", "Guideline name", "What it is", "Pipes", "km"],
            rows, widths=[2.4, 2.1, 3.4, 5.6, 1.3, 1.4], font=8.5, align_right={4, 5})
    D.p(d, "", space_after=2)
    _src(d, "_BRAIN/02_DESIGN_CRITERIA.md §2, the tier-names row (engineer, 2026-09-11); "
            "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §5 and §8: the engine values lateral and branch are "
            "both secondary main sewers. Guideline wording G203-p17, p21.")
    _lead(d, "Ibri number.  ", f"The test-area design is {f(tot_m / 1000, 2)} km of pipe: "
          f"{by.loc['lateral', 'sum'] / tot_m * 100:.1f} % main sewers, "
          f"{by.loc['sub main', 'sum'] / tot_m * 100:.1f} % headers and "
          f"{by.loc['trunk main', 'sum'] / tot_m * 100:.1f} % trunk.")
    _where(d, "Field TIER in W8/shp/W8_pipes.shp (values trunk main, sub main, lateral) and in the "
              "later engine's shapefile and DXF exports (trunk, sub main, lateral, branch). The renaming is "
              "applied in the engine copy from W13/tmp3 on.")

    # ---------------------------------------------------------------- 10.5
    D.h(d, 2, "10.5   The hierarchy learned from the built network")
    _lead(d, "What it is for.  ", "To give the layout the shape a contractor builds. Matching the "
          "built network's average gradient, depth and chamber spacing shows the hydraulics are right. "
          "It shows nothing about whether the layout can be built, because the hierarchy is invisible "
          "in every one of those averages.")
    _lead(d, "The rule.  ", "Properties feed the tertiary pipes, the tertiary pipes feed a main sewer, "
          "main sewers feed other main sewers, and only headers reach the trunk. A design in which "
          "every catchment finds its own way to the trunk is a set of branches no contractor would "
          "build.")
    D.p(d, "The rule was read from NAMA's own manhole identifiers inside the test area, 2,101 pipes "
           "and 78.6 km. An identifier such as 5A-2-TM-MH185 is package 5A-2, trunk main, manhole 185; "
           "5A-2-SM.2-MH391 is sub main 2; 5A-1-A49-MH3 is street-sewer zone A49. The designer's own "
           "upstream and downstream manhole fields then show where each zone drains.")
    D.tab_caption(d, "Where the 419 street-sewer zones of the built network drain")
    D.table(d, ["Drains into", "Zones", "Share"],
            [["another street sewer", "381", "**91 %**"], ["a sub main (header)", "27", "6 %"],
             ["the trunk main", "10", "2 %"]], widths=[7.0, 3.0, 3.0], font=9, align_right={1, 2})
    D.p(d, "", space_after=2)
    D.p(d, "Sewage crosses a median of 11 street sewers before it reaches a header. All six headers "
           "drain to the trunk, so only about 16 things touch the trunk: 6 headers and 10 street "
           "sewers. An earlier design with no header tier had 30 things touching the trunk, 14 of them "
           "carrying under 100 properties and one carrying 3.")
    D.p(d, "The number of joins was then swept on the test-area design to see where it stops working:")
    D.tab_caption(d, "Joins to the main pipe against pumping and dual-carriageway crossings, test area")
    D.table(d, ["Cap on joins", "Joins built", "Pumping stations", "Deepest chamber, m", "Dual crossings"],
            [["none", "31", "0", "9.12", "1"], ["20", "19", "0", "10.33", "1"], ["16", "14", "1", "11.79", "1"],
             ["12", "11", "3", "11.97", "2"], ["8", "8", "3", "11.97", "2"], ["6", "6", "2", "11.90", "15"]],
            widths=[3.0, 3.0, 3.3, 3.6, 3.1], font=9, align_right={1, 2, 3, 4})
    D.p(d, "", space_after=2)
    D.p(d, "Below about 14 joins the network starts buying pumping stations, and below 8 it starts "
           "crossing dual carriageways to consolidate. Around 20 is the tightest structure that still "
           "runs entirely on gravity without cutting across carriageways, close to the built "
           "network's 16.")
    _src(d, "Project doctrine, _BRAIN/07_PROJECT_STATE.md §2 item 4 (learned from the as-built, "
            "2026-08-23); measurements in W8/docs/LEARNING_FROM_ASBUILT.md (2026-08-21).")
    jt = N["join_tiers"]
    _lead(d, "Ibri number.  ", f"The test-area design kept {tr['joins_kept']} joins out of "
          f"{tr['join_candidates']} candidates, from {tr['streets_facing_the_main_pipe']} streets facing "
          f"the main pipe, with {W8RUN['stations']['count']} pumping stations. In its pipe layer "
          f"{jt.get('sub main', 0)} of the pipes flagged as joins are headers and "
          f"{jt.get('lateral', 0)} are street main sewers. The rule adopted since then (Section 10.6) "
          "lets only headers join, so those street sewers will run into the nearest header instead.")
    _where(d, "W8/run/summary.json key trunk; field IS_JOIN in W8/shp/W8_pipes.shp; the as-built in "
              "W7/shp/EXISTING_SEWERLINE.shp (OP_STATUE = 1), fields US_MHID and DS_MHID.")

    # ---------------------------------------------------------------- 10.6
    D.h(d, 2, "10.6   How the layout is made")
    _lead(d, "What it is for.  ", "To make a layout that is good, not only legal. The guideline "
          "says whether a pipe complies; these rules say how the network is arranged.")
    _lead(d, "The rule.  ", "Twelve rules, agreed as the reasoning the design engine is built against:")
    rules = (
            ("Sewage runs downhill. ", "Read the ground along every street and point each street downhill."),
            ("Follow the arrows. ", "Where the falling streets stop is an outlet. A basin is not an outlet: "
             "a sub-network connects to the main pipe or the plant, never to a local sink."),
            ("One spine per outlet. ", "From each outlet, the gravity path to the main pipe is the spine; "
             "the ground sets the number of joins, not a cap."),
            ("Headers first. ", "The headers are the long, straight, low streets of each catchment, cut "
             "only at a crest. They earn their diameter from the houses they collect."),
            ("Then hang the rest off them. ", "Every street drains to the header below it, every house "
             "to the street it fronts. One outlet per junction and no loops. A street that touches the "
             "main pipe does not join it; only headers join."),
            ("A ridge is a boundary. ", "A street on a ridge drains whole to the lower side; a long one "
             "splits at its crest."),
            ("Gradient follows the ground in three bands. ", "Flatter than the minimum: lay at the minimum. "
             "Between the minimum and the velocity limit: parallel to the ground at cover. Steeper than "
             "3 m/s at peak: hold the gradient and take the rest as drops."),
            ("Gradients in steps. ", "Where a pipe is laid at its minimum, the minimum is G203-p29 Table 11 "
             "(G203-p18 Table 5 for a tertiary pipe). Every gradient is rounded up to a step of "
             f"{STEP_SEC / 10:g} % ({STEP_SEC:g} mm/m) for a secondary pipe and {STEP_TRUNK / 10:g} % "
             f"({STEP_TRUNK:g} mm/m) for a primary trunk of DN{TRUNK_DN} and up. One gradient per run until "
             "the cover runs out. The diameter comes from the flow, never chosen to flatten a gradient."),
            ("Lay from the heads. ", "That is the shallowest the route can ever be."),
            ("Over 12 m: reroute first. ", "A different join, a helpful street, or the neighbouring "
             "catchment. Then cut for a pumping station where the pipe would pass 12 m, and restart at "
             "cover. Never dig past 12 m to avoid a pump; never pump to avoid a reroute."),
            ("A closed hollow is a real pump. ", "So is a ridge between a pocket and every neighbour."),
            ("Chambers by the guideline. ", "At every junction, head and change of gradient or diameter, "
             "spaced by G203-p30 Table 12, evenly divided and rounded, and clear of every plot."))
    for i, (lead, text) in enumerate(rules):
        D.numbered(d, text, lead=lead, restart=(i == 0))
    r_step = 1 + [lead for lead, _ in rules].index("Gradients in steps. ")
    D.p(d, "The rules speak of sub-mains and laterals in the engine's old words; read them as headers "
           "and main sewers. The 12 m is a limit on depth, ground to invert, at every chamber and "
           "along every trench, with no exceptions: where a gravity sewer would pass it, a pumping "
           "station goes in before that point.")
    ex_dn = (200, 315, TRUNK_DN, 900)
    rows = [[f"DN{dn}", "secondary" if dn < TRUNK_DN else "primary trunk", f"{TAB11_MIN[dn]:.2f}",
             f"{grid_step(dn):g}", f"**{on_grid(TAB11_MIN[dn], grid_step(dn)):.2f}**",
             f"{on_grid(TAB11_MIN[dn], grid_step(dn)) / 10:.3f}",
             f"{on_grid(TAB11_MIN[dn], STEP_SEC):.2f}", f"{TAB11_MIN[dn] / 10:.3f}"] for dn in ex_dn]
    tn = D.tab_caption(d, "Minimum gradients laid on their steps, mm/m")
    D.table(d, ["Pipe", "Tier", "G203 Table 11 minimum", "Step", "Laid at", "Laid at, %",
                "On one 0.05 % grid", "A tenth of the minimum (old step)"], rows,
            widths=[1.5, 2.3, 2.2, 1.3, 1.6, 1.7, 2.3, 3.0], font=8.5, align_right={2, 3, 4, 5, 6, 7})
    D.p(d, "", space_after=2)
    s9, s9_one = on_grid(TAB11_MIN[900], grid_step(900)), on_grid(TAB11_MIN[900], STEP_SEC)
    D.p(d, f"Rule {r_step} was amended on 2026-09-11; it used to step each pipe by a tenth of its own "
           "minimum. The steps are chosen so that a gradient can be built and read: the number on a "
           "profile or a map is a number a setting-out engineer can use. A tenth of the minimum is finer "
           f"than the construction can hold. On DN900 it is {TAB11_MIN[900] / 10:g} mm/m, which is "
           f"{TAB11_MIN[900] / 10 * 100:g} mm of fall over 100 m, while the guideline lets the line and "
           f"level of a laid pipe deviate by {TOL_MM:g} mm. One 0.05 % grid for every size is too coarse "
           f"at the other end: DN900, whose minimum is {TAB11_MIN[900]:.2f} mm/m, would go in at "
           f"{s9_one:.2f} mm/m instead of {s9:.2f}, {(s9_one - s9) * 1000:.0f} mm deeper for every "
           f"kilometre of trunk. Table {tn} lays the minimums on their steps.")
    D.p(d, "The tractive force sets no gradient at this stage. It is the audit's second test (Chapter "
           "12), and it is applied to the gradients at the preliminary design, once NWS confirms the "
           "tractive tension. G203 §4.2.2.1 says the steeper gradient of the two methods shall be adopted "
           "as the minimum, so this is a departure: it is recorded in report R2 §10.1 for NWS to confirm.")
    big = pipes[pipes.DN_MM >= TRUNK_DN]
    assert sorted(big.DN_MM.unique()) == [TRUNK_DN] and \
        (abs(big.SLOPE_PCT * 10 - on_grid(TAB11_MIN[TRUNK_DN], STEP_SEC)) < 1e-6).all(), \
        "the test area's large pipes have changed: rewrite the engine paragraph of Section 10.6"
    s_old, s_new = on_grid(TAB11_MIN[TRUNK_DN], STEP_SEC), on_grid(TAB11_MIN[TRUNK_DN], STEP_TRUNK)
    D.p(d, f"The design engine still lays every pipe on one grid of {ENGINE_STEP * 100:.2f} % "
           f"(SLOPE_STEP = {ENGINE_STEP:g}) whatever its size, and that is how the test-area design was "
           f"laid. The setting is to be made by pipe size: {STEP_SEC / 1000:g} below DN{TRUNK_DN} and "
           f"{STEP_TRUNK / 1000:g} from DN{TRUNK_DN}. On the test area it changes one thing. The "
           f"{f(len(big))} trunk pipes of DN{TRUNK_DN}, {f(big.LEN_M.sum() / 1000, 2)} km, are laid at "
           f"their minimum on the single grid, {s_old / 10:.2f} %; on the trunk step they go in at "
           f"{s_new / 10:.3f} %, which is {f(big.LEN_M.sum() * (s_old - s_new) / 1000, 2)} m less fall "
           "along that length.")
    _src(d, "Project rules, W13/docs/W13_DESIGN_LOGIC.md (agreed 2026-09-07, with dated amendments to "
            "2026-09-08). 12 m: project doctrine of 2026-09-07 in the context of G203-p33 §4.6.3, which "
            "recommends a cover of about 10 to 12 m and makes excavation cost the trigger for pumping. "
            "Gradient steps and the concept-stage minimum: project rule (engineer, 2026-09-11), "
            f"_BRAIN/02_DESIGN_CRITERIA.md §1, superseding rule {r_step} of W13_DESIGN_LOGIC.md as agreed "
            "on 2026-09-07. Minimum gradients G203-p29 Table 11; tertiary G203-p18 Table 5; construction "
            "tolerance G203-p29 §4.3.1; the steeper-governs clause G203-p27 §4.2.2.1, the departure for "
            "NWS to confirm. Chamber spacing: G203-p30 Table 12.")
    _lead(d, "Ibri number.  ", f"The test-area design is the benchmark every change must still meet on "
          f"its {W8RUN['s1']['boundary_ha'] / 100:.2f} km²: {f(W8RUN['net_km'], 1)} km of sewer, "
          f"{f(W8RUN['n_nodes'])} chambers and {W8RUN['stations']['count']} pumping stations, deepest "
          f"chamber {W8RUN['max_depth_m']:.2f} m. The network NAMA built there needs no pumping either.")
    _where(d, "W13/docs/W13_DESIGN_LOGIC.md; the benchmark run is W13/py/run_test_boundary.py "
              "(about 26 seconds), which reproduces W8/run/summary.json. The engine's gradient grid: "
              "SLOPE_STEP in W13/tmp3/py/sewnet/criteria.py, applied by rounding up in "
              "W13/tmp3/py/sewnet/stages/hydraulic.py. Pipe gradients: SLOPE_PCT in W8/shp/W8_pipes.shp.")

    # ---------------------------------------------------------------- 10.7
    D.h(d, 2, "10.7   The main pipe is an input")
    _lead(d, "What it is for.  ", "To separate what is designed from what is given. The route of "
          "the main pipe to the plant is fixed by the engineer; the design connects the districts to it.")
    _lead(d, "The rule.  ", "The main pipe is read from its drawn line and never derived. Sub-networks "
          "join it only through headers, at join points spaced apart; a street beside it runs into the "
          "nearest header. Its levels are set after the sub-networks are laid, because a join cannot "
          "sit below the pipe it feeds and the main pipe's profile depends on where the joins are.")
    _src(d, "Project doctrine (2026-08-23; W13/docs/W13_DESIGN_LOGIC.md rules 3 and 5, 2026-09-07 and "
            "2026-09-08). Its tier is primary by function (G203-p35); whether it also meets NWS's 800 mm "
            "condition is known only once it is sized.")
    _lead(d, "Ibri number.  ", f"On the test area the main pipe runs {tr['trunk_km']:.2f} km, "
          f"{tr['inside_boundary_km']:.2f} km of it inside the boundary, and both legs drain to their "
          f"meeting point {tr['outfall_outside_boundary_m']} m outside the boundary before continuing "
          f"to the existing plant. The design found {tr['join_candidates']} candidate joins, kept "
          f"{tr['joins_kept']}, and reached them with connectors of median length "
          f"{tr['median_connector_m']:.1f} m.")
    _where(d, f"Hydraulic/SHP/Main Pipe/Main Pipe.shp; W8/run/summary.json key trunk (source recorded "
              f"there as \"{tr['source']}\").")

    # ---------------------------------------------------------------- 10.8
    D.h(d, 2, "10.8   Dual carriageways are excluded")
    _lead(d, "What it is for.  ", "A dual carriageway cannot be dug up for a sewer, and a sewer under "
                                  "one cannot be maintained without closing it.")
    _lead(d, "The rule.  ", "No pipe of any tier runs along a dual carriageway, the trunk included. A "
          "dual carriageway is crossed only by a short pipe at right angles, at an underpass or by "
          "trenchless work. The two carriageways are drawn as two parallel lines: they are excluded, "
          "not merged into one corridor. Where the road data carry the flag, dual = 1 marks a dual "
          "carriageway and dual = 2 a two-lane pair of which only one side is used. The street drawing "
          "used as the corridor source since 2026-09-07 already leaves the dual carriageways out. The "
          "design engine then adds its own short crossings at right angles between the two sides, "
          "which the route search may use at a cost where they save depth or a pumping station.")
    _src(d, "Project rule (engineer, 2026-08-19), CLAUDE.md rule 7; W13/docs/W13_DESIGN_LOGIC.md, "
            "Inputs. Trenchless crossings and road settlement: G203-p21 §4.1, on NWS approval.")
    rt = W8RUN["road_treatment"]
    _lead(d, "Ibri number.  ", f"Of the 3,267 pipes NAMA built, 4 run within 4 m of a dual "
          f"carriageway, 0.1 %: practice confirms the rule. On the test area {rt['dual_excluded']} "
          f"dual-carriageway segments were excluded, taking the street corridors from "
          f"{rt['km_in']:.1f} km to {rt['km_out']:.1f} km. The engine then added "
          f"{W13RUN['road_treatment']['dual_crossings_added']} perpendicular dual-carriageway crossings "
          "on the test area.")
    _where(d, "Hydraulic/SHP/Road centerline 2 (field dual); Hydraulic/DWG/road network 03092026 "
              "eyeballed.dxf (the corridor source); W8/run/summary.json key road_treatment; the crossings "
              "added: W13/run/summary.json key road_treatment.dual_crossings_added, made by "
              "_dual_crossings in W13/py/sewnet/stages/road_treatment.py; the as-built "
              "check in W7/docs/CALIBRATION_vs_EXISTING.md.")

    # ---------------------------------------------------------------- 10.9
    D.h(d, 2, "10.9   Stub-outs and the tertiary layer")
    _lead(d, "What it is for.  ", "A plot that is empty today will connect later. The network built "
          "now must carry its flow and leave it a way in, so the street is not opened again.")
    _lead(d, "The rule.  ", "Chambers carry stubs or plugged ports for future connections. A stub-out "
          "is a capped connection at the frontage of a future plot, sized for that area's saturation "
          "flow; usually the minimum diameter, DN200, governs. The flow of a future plot is already "
          f"inside Q_ULT, at its people times {Q_FUT:.1f} l/d, so no separate allowance is added.")
    _src(d, "G203-p19 §3.4 (stubs or plugged ports on chambers); project doctrine, "
            "_BRAIN/07_PROJECT_STATE.md §2 item 7. Future-plot rate: 0.85 × 164 + 0.54 × (0.22 + 0.14) "
            "× 164 l/d per person, G201-p60 Table 11 and G201-p71 Table 19, report R2 §15.4.")
    _lead(d, "Ibri number.  ", f"{f(PW['ib_future'])} of Ibri's {f(PW['ib_plots'])} plots are empty "
          f"today, and {f(PW['all_future'])} of the study area's {f(PW['all_plots'])}. On the test area "
          f"{f(N['fut_in'])} of {f(N['plots_in'])} plots are empty. The street sewers already carry "
          "their saturation flow. The stub-outs, house connections and riders are not drawn yet: the "
          f"test-area design recorded {W8RUN['tertiary']['stub_outs']} stub-outs, and the engine's scope "
          "is street sewers only. The consequence to remember is that there is no house-by-house check "
          "yet: where a house sits below its road, the chamber that would have been deepened for it is "
          "not.")
    _where(d, "W8/run/summary.json key tertiary; scope in W13/docs/W13_DESIGN_LOGIC.md, section Scope "
              "at this stage; plot status Buiding_St = Future in W14/shp/PLOTS_load.shp.")

    # ---------------------------------------------------------------- 10.10
    D.h(d, 2, "10.10   Check it yourself")
    D.numbered(d, "Open G203 at page 17 and read the last paragraph of §3.2; then G203 Table 5 on page "
                  "18 and G203 Table 6 on page 22. Confirm the 45 m, the 1 % and the OD200.", restart=True)
    D.numbered(d, "Load W8/shp/W8_pipes.shp in QGIS, style it by TIER and sum LEN_M per value. You "
                  f"should get {f(by.loc['lateral', 'sum'] / 1000, 2)} km of lateral, "
                  f"{f(by.loc['sub main', 'sum'] / 1000, 2)} km of sub main and "
                  f"{f(by.loc['trunk main', 'sum'] / 1000, 2)} km of trunk main; read them as main "
                  "sewer, header and primary.")
    D.numbered(d, "Pick any street main sewer head in the same layer and follow it down to the main "
                  "pipe. Count the street sewers it passes through before it reaches a header.")
    D.numbered(d, "Load W7/shp/EXISTING_SEWERLINE.shp, filter OP_STATUE = 1, and read the manhole "
                  "identifiers: TM, SM.n and the zone codes are the built network's tiers.")
    D.numbered(d, "Filter Road centerline 2 on dual = 1, buffer it by 4 m and intersect it with the "
                  "design's pipes. Only short crossings at right angles may remain.")
    D.numbered(d, f"In the same pipe layer filter DN_MM = {TRUNK_DN} and read SLOPE_PCT. Every pipe is at "
                  f"{s_old / 10:.2f} %, the minimum on the single grid; on the trunk step of rule {r_step} "
                  f"it would be {s_new / 10:.3f} %.")
    D.numbered(d, "Run python W13/py/run_test_boundary.py. It must still give about "
                  f"{f(W8RUN['net_km'], 1)} km, {f(W8RUN['n_nodes'])} chambers and "
                  f"{W8RUN['stations']['count']} pumping stations.")
