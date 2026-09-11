"""T04 chapters 13 to 17: lifting stations and force mains, septicity and odour,
utilities and crossings, hydraulic modelling, and the existing network.

Ported from T03_R01 body2.s10_pumping and body3.s12_septicity, s13_utilities,
s14_modelling and s15_existing, updated to the settled rules. Every Ibri number
is read at build time: facts_w14, W14/analysis/design_flows.json, the test
boundary gate run (W13/run/summary.json), W14/report/data_facts.py and the
built-network attribute table. Guideline values carry their page.
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

import data_facts as DF

REPO = os.path.dirname(os.path.dirname(HERE))
RM_LENGTH_M = 1500.0          # illustrative rising main length, taken from the cascade distance
EXAMPLE = "HIJAR"              # a settlement whose flows are a realistic size for one station
FUT_LPD = F.LPCD * (F.RET_DOM + F.RET_ND * (F.R_ND + F.R_GOV))     # 171.3 l/d per future person


# ------------------------------------------------------------------ helpers
def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)


def _part(d, lead, text):
    D.rich(d, (lead + ".  ", {"bold": True}), (text, {}))


def _for(d, text):
    _part(d, "What it is for", text)


def _rule(d, text):
    _part(d, "The rule", text)


def _ibri(d, text):
    _part(d, "Worked Ibri number", text)


def _src(d, text):
    D.rich(d, ("Source.  ", {"bold": True, "colour": D.GREY, "size": 9.5}),
           (text, {"italic": True, "colour": D.GREY, "size": 9.5}))


def _where(d, text):
    D.rich(d, ("Where it lives.  ", {"bold": True, "colour": D.GREY, "size": 9.5}),
           (text, {"colour": D.GREY, "size": 9.5}), space_after=10)


def _fig(d, name, caption, w=15.5):
    D.picture(d, os.path.join(IMG, name + ".png"), w)
    D.fig_caption(d, caption)


def f0(x):
    return F.fmt(x, 0)


def f1(x):
    return F.fmt(x, 1)


def f2(x):
    return F.fmt(x, 2)


# --------------------------------------------------------------------- data
@lru_cache(None)
def _flows():
    with open(os.path.join(REPO, "W14", "analysis", "design_flows.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _sett(key):
    return next(s for s in _flows()["settlements"] if s["key"] == key)


def _row(key):
    return next(r for r in F.settlement_table() if r["key"] == key)


@lru_cache(None)
def _gate():
    """The test boundary gate run, written by W13/py/run_test_boundary.py."""
    with open(os.path.join(REPO, "W13", "run", "summary.json"), encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(None)
def _w8_drops():
    """Backdrops of the test-area design: field N_DROPS of W8/shp/W8_manholes.shp."""
    import geopandas as gpd
    m = gpd.read_file(os.path.join(REPO, "W8", "shp", "W8_manholes.shp"), ignore_geometry=True)
    return dict(drops=int(m.N_DROPS.sum()), chambers=int((m.N_DROPS > 0).sum()))


def _table_ref(d, caption, where):
    """Point to a table of this tutorial already written into d: 'Table N in <where>' from the
    live caption counter, or the caption text itself when the chapter is built alone."""
    for par in d.paragraphs:
        t = par.text
        if t.startswith("Table ") and caption in t:
            return f"Table {t.split()[1]} in {where}"
    return f"the table ‘{caption}’ in {where}"


def _ww(asset):
    """One row of the received wastewater table, bold markers removed."""
    r = next(x for x in DF.WASTEWATER if x[0] == asset)
    return [str(c).replace("**", "").replace("m3/d", "m³/d") for c in r]


def _register(item):
    r = next(x for x in DF.REGISTER if x[0] == item)
    return r[1], r[2]


def _merrimack_mld(q_m3d):
    """Qpdf = 2.65 Qadf^0.879, both in Ml/d (G201 p71)."""
    return 2.65 * (q_m3d / 1000.0) ** 0.879


def _ls(m3d):
    return m3d / 86.4


@lru_cache(None)
def _asbuilt():
    """Attribute count on the built gravity network (OP_STATUE = 1)."""
    import geopandas as gpd
    g = gpd.read_file(os.path.join(REPO, "W7", "shp", "EXISTING_SEWERLINE.shp"), ignore_geometry=True)
    b = g[g.OP_STATUE.astype(str).str.strip() == "1"]
    empty = {"", "0", "0.0", "None", "nan"}

    def filled(c):
        return int((~b[c].astype(str).str.strip().isin(empty)).sum())

    od = b.OUT_DIAMET.astype(str).str.strip()
    od = od[~od.isin(empty)].value_counts().to_dict()
    mat = b.MATERIAL.astype(str).str.strip()
    mat = mat[~mat.isin(empty)].value_counts().to_dict()
    mh = (set(b.US_MHID.astype(str).str.strip()) | set(b.DS_MHID.astype(str).str.strip())) - empty
    return dict(n=len(b), km=float(b.LEN_M.sum()) / 1000.0, nominal=filled("N_DIAMETER"),
                invert=filled("US_INVERT_"), ground=filled("US_GROUND_"), od=filled("OUT_DIAMET"),
                od_values=od, material=mat, manholes=len(mh),
                proposed_in_file=int((g.OP_STATUE.astype(str).str.strip() == "0").sum()),
                remark=str(b.REMARKS.iloc[0]).strip())


@lru_cache(None)
def _station():
    """The worked station: the example settlement's flows lifted by one station."""
    s, r = _sett(EXAMPLE), _row(EXAMPLE)
    q_ult, q_low = s["q_ult"], s["q_2030_low"]
    props = s["pop_ult"] / r["or_used"]
    qp_mld = _merrimack_mld(q_ult)
    duty = qp_mld * 1000.0 / 86.4                      # l/s
    pf = qp_mld / (q_ult / 1000.0)
    typ = 1 if duty <= 100 else (2 if duty <= 300 else 3)
    V = 0.25 * duty / 1000.0 * 360.0                    # m3
    cands = []
    for idmm in (100, 125, 150, 200):
        A = math.pi * (idmm / 1000.0) ** 2 / 4.0
        v = duty / 1000.0 / A
        vol = A * RM_LENGTH_M
        cands.append(dict(id=idmm, A=A, v=v, vol=vol,
                          t_ult=vol / (q_ult / 86400.0) / 60.0,
                          t_low=vol / (q_low / 86400.0) / 60.0,
                          vavg=(q_low / 86400.0) / A,
                          ok=(1.0 <= v <= 2.5)))
    passing = [c for c in cands if c["ok"]]
    pick = passing[0] if passing else min(cands, key=lambda c: abs(c["v"] - 1.5))
    q_low_ls = _ls(q_low)
    qmin = 0.25 * q_low_ls
    fill = V / (qmin / 1000.0) / 60.0
    return dict(name=r["name"], q_ult=q_ult, q_low=q_low, q_ult_ls=_ls(q_ult), q_low_ls=q_low_ls,
                props=props, qp_mld=qp_mld, duty=duty, pf=pf, typ=typ, V=V, cands=cands,
                passing=passing, pick=pick, qmin=qmin, fill=fill)


def _fayoux(temp_c, t_h, v_avg, v_inst):
    """Table 99 (G203 p185), read on the unfavourable side between columns."""
    s_t = 20 if temp_c > 20 else next(sc for tt, sc in ((5, 0), (10, 2), (15, 4), (20, 10)) if temp_c <= tt)
    s_r = next((sc for h, sc in ((1, 0), (3, 1), (6, 4), (12, 6), (24, 15)) if t_h <= h), 15)
    cols = [1.0, 0.8, 0.6, 0.4, 0.2]
    ci = next((i for i, c in enumerate(cols) if v_avg >= c), 4)
    rows = {0.6: [15, 15, 15, 10, 15], 1.0: [0, 1, 2, 6, 10], 1.5: [0, 0, 0, 2, 6]}
    rk = max([k for k in rows if k <= v_inst], default=0.6)
    s_v = rows[rk][ci]
    total = s_t + s_r + s_v
    if total <= 5:
        band = "no risk"
    elif total <= 10:
        band = "low risk"
    elif total < 20:
        band = "significant risk"
    else:
        band = "significant to certain risk"
    return dict(s_t=s_t, s_r=s_r, s_v=s_v, col=cols[ci], row=rk, total=total, band=band)


# =================================================================== 13
def c13_pumping(d):
    D.h(d, 1, "13   Lifting stations and force mains", page_break=True)
    D.p(d, "A lifting station takes sewage that gravity can no longer carry, raises it, and "
           "pushes it through a pressure pipe, the rising main or force main, to a chamber from "
           "which gravity takes over again. Every station is land to acquire, a power supply, a "
           "running cost for the life of the scheme and one more way for the network to fail. "
           "This chapter sets out when a station goes in, how many there are, and how the pumps, "
           "the wet well and the rising main are sized.")
    D.callout(d, "The guideline's position.",
              "Pumping stations and pressure mains shall be avoided whenever gravity sewer "
              "designs are feasible and cost effective (G203 p181, §11.5.3.1(a)). A network "
              "with no station is the outcome the guideline asks for, not an exception to "
              "defend.", fill="EAF1F8", colour=D.MID)

    g = _gate()
    area = g["s1"]["boundary_ha"] / 100.0
    st = g["stations"]
    S = _station()

    # ------------------------------------------------------------- 13.1
    D.h(d, 2, "13.1   When a station goes in")
    _for(d, "To decide, chamber by chamber, whether the sewer may carry on by gravity or must "
            "be lifted.")
    _rule(d, "No chamber, and no point of the trench between two chambers, may lie more than "
             "12 m below the ground. Where a gravity sewer would pass that depth, a station goes "
             "in before that point: the sewage is lifted and the sewer restarts at normal cover, "
             "so the next stretch runs by gravity again. Before a station is accepted, the route "
             "is searched again for a shallower way, and only the pumping that survives that "
             "search is real. A station is never removed by digging past 12 m, and depth past "
             "12 m is never excused by calling the area a pumping pocket.")
    D.p(d, "The guideline states the depth as a recommendation, not a limit. It recommends a "
           "maximum cover of approximately 10 to 12 m, sends deeper cover to the pipe "
           "manufacturers, and requires pumping stations where the cost of excavation becomes "
           "prohibitive. Its trigger for a station is cost. The project holds 12 m as a hard "
           "limit because the network has not been costed yet, and the cost test is the only "
           "thing that could justify going deeper. Once costs exist, each excursion past 12 m "
           "becomes an economic question of its own, never a general relaxation. The earlier "
           "concept methodology taught the guideline's wording, that the trigger is cost and "
           "not depth; until costs exist the depth check decides.")
    _src(d, "G203 p33 §4.6.3 (recommended maximum cover, manufacturer check, pumping where "
            "excavation cost is prohibitive); G203 p181 §11.5.3.1(a). Project rule: 12 m with "
            "no exceptions (engineer, 2026-08-19), a hard limit until the cost analysis exists "
            "(engineer, 2026-09-07).")
    n_st = st["count"]
    st_txt = "needs no lifting station" if n_st == 0 else f"needs {n_st} lifting stations"
    _ibri(d, f"On the {f2(area)} km² test boundary the design lays {f0(g['n_nodes'])} chambers "
             f"over {f1(g['net_km'])} km of sewer. The deepest chamber is {f2(g['max_depth_m'])} m, "
             f"{f2(12.0 - g['max_depth_m'])} m inside the limit, and the network {st_txt}. The "
             f"network NWS built on the same ground has no station either.")
    _where(d, "W13/py/sewnet/criteria.py, MAX_DEPTH = 12.0. The depth test on every chamber and "
              "on the trench between chambers is in W13/py/sewnet/stages/audit.py; a chamber past "
              "the limit is gathered into a pocket by _pockets in stages/hydraulic.py. The gate "
              "figures are keys n_nodes, net_km, max_depth_m and stations of W13/run/summary.json, "
              "written by W13/py/run_test_boundary.py.")

    # ------------------------------------------------------------- 13.2
    D.h(d, 2, "13.2   One station per pocket, and cascades")
    _for(d, "To keep the number of stations as low as the ground allows. The count, more than "
            "the size, is what costs land, power connections and operators.")
    _rule(d, "Four steps, in this order.")
    D.numbered(d, "Chambers that fail the 12 m test and touch one another form one non-gravity "
                  "pocket. A pocket gets one station, at its lowest chamber, never one per "
                  "failing branch.")
    D.numbered(d, "A pocket serving fewer than 50 plots is not given a station at concept "
                  "stage. It stays in the concept design with its 12 m failure flagged, and "
                  "detail design resolves it by re-routing, by regrading within 12 m, or by a "
                  "station, never by going past 12 m. It is listed, never dropped.")
    D.numbered(d, "Two stations within about 1.5 km of each other are examined together: "
                  "whether the upstream one can discharge into the gravity sewer that feeds the "
                  "downstream one, so the two work in cascade on one outlet, or whether a single "
                  "station placed lower can serve both pockets. The arrangement with fewer "
                  "stations is preferred, because the count drives land acquisition.")
    D.numbered(d, "Every station site is approved by NWS in advance, at concept or preliminary "
                  "stage. The pump floor, transformer and generator sit above the maximum flood "
                  "level, with floors at least 300 mm above the 1:50-year flood, and sites under "
                  "overhead power lines are avoided.")
    _src(d, "Project rule: one station per contiguous non-gravity pocket, cascade within about "
            "1.5 km, pockets under 50 plots to detail design (CLAUDE.md rule 9; doctrine §2 item "
            "3). Siting and approval: G203 p38 §7.2. Land: G203 p43 Table 21.")
    _ibri(d, f"On the test boundary the station report is empty: {n_st} stations, "
             f"{len(st['small_enough_to_absorb'])} pockets small enough to absorb and "
             f"{len(st['close_enough_to_cascade'])} pairs close enough to cascade. Each station "
             f"avoided saves a site of 50 to 100 m² for the smallest type and at least 900 m² for "
             f"the largest (G203 p43 Table 21), plus its access and its power supply.")
    _where(d, "W13/py/sewnet/stages/hydraulic.py, _pockets: contiguous failing chambers, site at "
              "the lowest chamber, flagged absorb below SLS_MIN_PLOTS = 50 (the code counts "
              "properties where the rule says plots). W13/py/sewnet/pipeline.py, _station_report: "
              "pairs within SLS_CASCADE_M = 1500 m. Output: summary.json key stations, fields "
              "small_enough_to_absorb and close_enough_to_cascade.")

    # ------------------------------------------------------------- 13.3
    D.h(d, 2, "13.3   How many pumps, and of what type")
    _for(d, "To fix the flow the station must deliver and the number of pumps it carries.")
    _rule(d, "The pumps shall be capable of handling the design peak flow, and there shall be "
             "enough of them that the design peak can still be delivered with any one pump out "
             "of service. A station serving a small area has at least two identical units, duty "
             "and standby, either one able to carry the design flow. The station type follows "
             "the design flow (table below). At site level the guideline asks for a modular "
             "N + 1: N elements to meet the average day, the extra one to meet the peak. Pumps "
             "rotate duty after each start and stop so running hours even out.")
    D.p(d, "The design peak is taken at saturation, on the plots' Q_ULT, because that is the "
           "flow the civil works must pass. Pumps are mechanical plant with a 15-year service "
           "rating, so the pump sets themselves are phased: the first set is chosen for the "
           "flows of its own life, while the wet well, the rising main and the site are built "
           "for saturation.")
    t_types = D.tab_caption(d, "Pumping station types (G203 p40 Table 17; land from p43 Table 21)")
    D.table(d, ["Type", "Design flow", "Duty pumps, minimum", "Standby", "Land, minimum"],
            [["Type 1", "up to 100 l/s", "1", "1", "50 to 100 m²"],
             ["Type 2", "over 100 to 300 l/s", "2", "1", "200 to 400 m²"],
             ["Type 3", "over 300 l/s", "3", "1", "900 m² or more"]],
            widths=[2.4, 3.8, 3.6, 2.4, 4.4], font=9.5)
    D.callout(d, "Two tables disagree on Type 3.",
              "G203 Table 17 on p40 gives a Type 3 station three duty pumps and one standby. The "
              "dry-arrangement table on p42 gives it two duty and one standby. Types 1 and 2 "
              "agree in both. The three-pump reading is the conservative one and is used here.")
    _src(d, "G203 p39 §7.3 (identical duty and standby units; peak with any one pump out), p40 "
            "§7.4 and Table 17 (types, 15-year pump rating, duty rotation), p42 (dry "
            "arrangement), p38 §7.1 (20-year life for non-structural mechanical installations); "
            "G201 p33 (N + 1 at site level). Project rule: pumps phased, buried civil works at "
            "saturation (doctrine §2 item 1).")
    pf_note = ("under the 5.0 the guideline recommends as a ceiling for the hourly factor"
               if S["pf"] <= 5.0 else "over the 5.0 the guideline recommends, which must be said")
    _ibri(d, f"Take the flows of {S['name']} as a station-sized example. No station is proposed "
             f"there; its flows are simply a realistic size for one. At saturation {S['name']} "
             f"produces {f1(S['q_ult'])} m³/d on average, {f2(S['q_ult_ls'])} l/s. It serves about "
             f"{f0(S['props'])} properties, well over 100, so the peak is Merrimack's: "
             f"2.65 × {S['q_ult'] / 1000:.3f}^0.879 = {S['qp_mld']:.3f} Ml/d, {f1(S['duty'])} l/s, a "
             f"peak factor of {f2(S['pf'])}, {pf_note}. Each kilometre of sewer upstream adds "
             f"720 l/d of infiltration, {720 / 86400:.4f} l/s, which moves the duty only in the "
             f"third figure. The duty is therefore {f1(S['duty'])} l/s: a Type {S['typ']} station "
             f"with one duty and one standby pump, each delivering {f1(S['duty'])} l/s. One pump "
             f"covers both the average day and the peak, so N = 1 and N + 1 = 2, the same two "
             f"pumps.")
    _where(d, "Not yet in the pipe-laying code, whose station report gives the count, the "
              "properties served, the lift and the rising main length (stages/hydraulic.py, "
              "fields n_props, lift_m, rising_main_m). Duty and type are set by hand from the "
              "pocket's upstream Q_ULT in W14/shp/PLOTS_load.shp. Example flows: "
              "W14/analysis/design_flows.json, settlement HIJAR (q_ult, q_2030_low, pop_ult).")

    # ------------------------------------------------------------- 13.4
    D.h(d, 2, "13.4   The wet well")
    _for(d, "To give the pump enough volume between its start and stop levels that the motor is "
            "not started more often than it can stand, and enough suction head to run without "
            "cavitating.")
    _rule(d, "The minimum live volume, between the start and stop levels of a single "
             "constant-speed pump, is")
    eq = D.next_eq()
    M.display(d, M.seq(R("V"), M.EQ, R("0.25"), R(" "), R("Q"), R(" "), R("T"), R(",   "),
                       R("T"), M.EQ, M.frac(R("3600"), R("n"))), number=eq)
    _params(d, [["V", "live volume between pump start and stop levels", "m³"],
                ["Q", "capacity of a single pump", "m³/s"],
                ["T", "shortest allowed on-off cycle", "s"],
                ["n", "starts per hour allowed by the motor maker; at least 10 up to 30 kW", "1/h"]])
    D.p(d, "The factor 0.25 comes from the pump cycle. With an inflow q into a well of live "
           "volume V and a pump of capacity Q, one cycle lasts V/q to fill and V/(Q − q) to "
           "empty. That sum is shortest when the inflow is half the pump capacity:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("t"), UP("c")), M.EQ, M.frac(R("V"), R("q")), M.PLUS,
                       M.frac(R("V"), M.seq(R("Q"), M.MINUS, R("q"))), R("   ≥   "),
                       M.frac(M.seq(R("4"), R("V")), R("Q")), R("   at   "), R("q"), M.EQ,
                       M.frac(R("Q"), R("2"))), number=eq)
    D.p(d, "Requiring that shortest cycle to be no shorter than T gives V = QT/4. The formula "
           "is for a single constant-speed pump; the guideline gives nothing for variable-speed "
           "or duty-assist operation. Successive start and stop levels are 200 to 300 mm apart, "
           "starts are delayed 5 to 10 s, and computational and physical modelling is to be "
           "considered for stations of 0.5 m³/s and more. Storage for the emergency overflow "
           "sits above the start level of the last duty pump. Larger motors take their starts "
           "per hour from the manufacturer and NEMA MG 1. The pumps also need suction head, "
           "with a margin of at least 1 m over what the pump requires:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(UP("NPSH"), UP("a")), M.EQ, M.sub(R("H"), UP("a")), M.MINUS,
                       M.sub(R("H"), UP("vpa")), M.MINUS, M.sub(R("H"), UP("st")), M.MINUS,
                       M.sub(R("H"), UP("f"))), number=eq)
    _params(d, [["H a", "absolute pressure on the liquid surface", "m"],
                ["H vpa", "vapour pressure", "m"],
                ["H st", "static head", "m"],
                ["H f", "friction head", "m"]])
    D.p(d, "The guideline prints this without units or a sign convention. As printed it is a "
           "suction lift; with the flooded suction the guideline prefers, the static term adds.")
    _src(d, "G203 p48 §7.8 (live volume, starts, level spacing, modelling); p47 §7.5 (storage "
            "above the last duty start) and §7.6 (NPSH, 1 m margin); p38 §7.2 (flooded suction "
            "preferred). The cycle derivation is standard pump-sump theory, not in the guideline.")
    _ibri(d, f"For the example duty of {f1(S['duty'])} l/s and 10 starts an hour, T = 360 s and "
             f"V = 0.25 × {S['duty'] / 1000:.4f} × 360 = {f2(S['V'])} m³ of live volume. That is "
             f"the minimum between two levels; the well is deeper by the pump submergence and the "
             f"overflow storage.")
    _where(d, "Not in the code; a hand calculation at concept stage, repeated in the pump "
              "maker's selection at preliminary design.")

    # ------------------------------------------------------------- 13.5
    D.h(d, 2, "13.5   Sizing the rising main")
    _for(d, "To choose the bore of the pressure pipe so that solids keep moving at the lowest "
            "delivery and the pipe is neither scoured nor surged at the highest.")
    _rule(d, "The rising main is sized on the pump duty, not on the flow arriving by gravity. "
             "A pump does not run at the arrival rate: it fills the well and empties it at its "
             "own rate, so the main carries the duty flow whenever it carries anything. The duty "
             "can never be less than the design peak arriving, or the well would never empty.")
    D.bullet(d, "at the design minimum flow, meaning the pump's delivery at maximum static "
                "head, at least 0.75 m/s for raw sewage; at least 1.0 m/s where the flow is "
                "intermittent, as it is with fixed-speed pumps that start and stop; at least "
                "1.2 m/s in a vertical main.", lead="Lowest velocity: ")
    D.bullet(d, "not greater than 2.5 m/s in the worst case.", lead="Highest velocity: ")
    D.bullet(d, "75 mm internal for non-clog pumps, 50 mm with grinder pumps.",
             lead="Smallest bore: ")
    D.bullet(d, "where several bores satisfy the velocities, a cost comparison shall find the "
                "size with the lowest whole-life cost of main and pumping together. Where early "
                "flows are far below later ones, two or more rising mains may be warranted.",
             lead="Choice: ")
    eq = D.next_eq()
    M.display(d, M.seq(R("v"), M.EQ, M.frac(M.seq(R("4"), R(" "), M.sub(R("Q"), UP("d"))),
                                           M.seq(R("π"), R(" "), M.sup(R("D"), R("2"))))), number=eq)
    _params(d, [["v", "mean velocity in the main while the pump runs", "m/s"],
                ["Q d", "pump duty, the delivery at the operating point", "m³/s"],
                ["D", "internal diameter of the main", "m"]])
    D.p(d, "The minimum flow of G203 Table 16 (p40) is the other half of the check. The initial minimum "
           "flow is the average flow times a factor: 0.25 at 50 l/s, 0.35 at 500, 0.45 at 2,500 "
           "and 0.50 at 5,000 l/s. The guideline names it as the flow for sizing the main "
           "against deposition. With fixed-speed pumps the main still sees the full duty "
           "whenever a pump runs, and what the minimum flow changes is how long sewage waits "
           "between cycles. With variable-speed pumps the delivery turns down toward the "
           "inflow, and then the minimum flow itself must still meet the velocity floor. That "
           "split is our reading of p40 against p50; the guideline does not spell it out. The "
           "time sewage spends in the main is")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("t"), UP("r")), M.EQ,
                       M.frac(M.seq(R("π"), R(" "), M.sup(R("D"), R("2")), R(" "), R("L")),
                              M.seq(R("4"), R(" "), M.bar(R("q"))))), number=eq)
    _params(d, [["t r", "mean retention time in the main", "s"],
                ["L", "length of the main", "m"],
                ["q̄", "average inflow to the station", "m³/s"]])
    D.p(d, "The guideline asks for a main short enough to hold sewage no longer than half an "
           "hour, and admits in the same sentence that this is very rarely achieved. Retention "
           "is the link to the next chapter.")
    D.callout(d, "3.0 m/s is the gravity sewer's limit, not the rising main's.",
              "An earlier project note and the pipe-laying code both give the rising main a "
              "window of 0.75 to 3.0 m/s and cite G203 p50. That page says 2.5 m/s. The 3.0 m/s "
              "figure belongs to the gravity sewer at its design depth of flow (G203 p27 "
              "§4.2.2.2; p29 §4.3.2). The code also takes 0.75 m/s as the floor where start-stop "
              "pumping requires 1.0 m/s, and it bores the main as a gravity plastic pipe from "
              "OD160. For a rising main fed by fixed-speed pumps use 1.0 to 2.5 m/s; 0.75 m/s is "
              "the floor only where delivery at the design minimum flow is continuous, and a "
              "vertical main needs 1.2 m/s.")
    _src(d, "G203 p50 §8 and §8.1 (velocities, smallest bore, cost comparison, two mains); p50 "
            "§8.2.1 (half-hour retention); p40 §7.4 and Table 16 (minimum flow); p41 Table 17 "
            "(station pipework 2.5 m/s at maximum flow, 0.6 m/s at minimum, 0.5 m/s with grinder "
            "pumps). Project rule: the main is sized on the pump duty (doctrine §2 item 3).")
    c = S["cands"]
    ids = [str(x["id"]) for x in S["passing"]]
    passing = (" and ".join([", ".join(ids[:-1]), ids[-1]]) if len(ids) > 1 else (ids[0] if ids else "none"))
    _ibri(d, f"For the example duty of {f1(S['duty'])} l/s, four internal bores give the "
             f"velocities in the table below. Bores of {passing} mm pass the 1.0 to 2.5 m/s "
             f"window. The retention columns assume a main of {f0(RM_LENGTH_M)} m, a length taken "
             f"from the cascade distance and not from any route; the saturation average is "
             f"{f2(S['q_ult_ls'])} l/s and the 2030 low-case average {f2(S['q_low_ls'])} l/s.")
    D.tab_caption(d, f"Rising main candidates for the example station, duty {f1(S['duty'])} l/s, "
                     f"assumed length {f0(RM_LENGTH_M)} m")
    D.table(d, ["Internal bore, mm", "Velocity at duty, m/s", "1.0 to 2.5 m/s", "Volume, m³",
                "Retention at saturation, min", "Retention 2030 low case, min"],
            [[str(x["id"]), f2(x["v"]), "**pass**" if x["ok"] else "fail", f1(x["vol"]),
              f0(x["t_ult"]), f0(x["t_low"])] for x in c],
            widths=[2.4, 2.8, 2.4, 2.2, 3.2, 3.4], font=9, align_right={1, 3, 4, 5})
    D.p(d, "")
    D.p(d, f"Every candidate holds sewage well past the half hour, and longest in the opening "
           f"years. G203 Table 16 starts at 50 l/s, so below it the lowest factor, 0.25, is taken "
           f"(our reading; the table gives no value there): a minimum inflow of "
           f"{f2(S['qmin'])} l/s, at which the {f2(S['V'])} m³ well takes {f0(S['fill'])} "
           f"minutes to fill once. The smallest passing bore, {S['pick']['id']} mm, keeps "
           f"retention lowest and is carried into the next chapter as the example main; the "
           f"final choice waits for the whole-life cost comparison.")
    _where(d, "W13/py/sewnet/stages/hydraulic.py, _size_rising_mains: takes the first DN of "
              "DN_SERIES from OD160 whose bore passes the arriving peak at V_MAX = 3.0 m/s and "
              "sets the duty to at least 0.75 m/s times the bore area. It must be corrected to "
              "the G203 p50 window (at least 1.0 m/s for start-stop pumping, at most 2.5 m/s) "
              "and a pressure-pipe bore before any station is designed with it. "
              "Rising main length per station: summary.json, stations.rising_main_m.")

    # ------------------------------------------------------------- 13.6
    D.h(d, 2, "13.6   Profile, valves and termination")
    _for(d, "To lay the main so that it stays full, can be isolated, emptied and vented, and "
            "hands its sewage to the gravity system without releasing gas.")
    _rule(d, "The main follows these requirements.")
    D.bullet(d, "laid at predetermined gradients, recommended minimum 1:500 rising and 1:300 "
                "falling, never flatter than 1:750, ideally rising all the way to the discharge; "
                "air valves at high points, washouts at low points. It is designed to run full "
                "and remain full at all times.", lead="Profile: ")
    D.bullet(d, "in the public right of way, in straight lines, with pre-formed and anchored "
                "bends; on a highway in the carriageway, at least 1 m from the kerb line.",
             lead="Layout: ")
    D.bullet(d, "an access point every 500 m; in-line isolation valves at about 500 m and never "
                "more than 800 m apart; washouts sized to empty a section in 3 to 4 hours, 100 mm "
                "for a main up to 400 mm, 150 mm to 800 mm, 200 mm to 1,200 mm and 300 mm above; "
                "double-orifice air valves at high points.", lead="Access and valves: ")
    D.bullet(d, "1.3 m to the crown without protection, 0.5 m with protection, 1.5 m at a wadi "
                "crossing, the same as for a gravity sewer.", lead="Cover: ")
    D.bullet(d, "ductile iron and HDPE for the pressure main.", lead="Material: ")
    D.bullet(d, "at a manhole, entering no more than 300 mm above the receiving flow line; a "
                "water seal and forced venting through odour control where the discharge is "
                "turbulent; a lined or corrosion-resistant receiving manhole; hydrogen sulphide "
                "monitoring there to control dosing at the start of the main; the main kept "
                "primed, ideally with a vertical bell-mouth.", lead="Termination: ")
    D.bullet(d, "only with a dedicated hydraulic study that keeps 0.75 m/s in every operating "
                "mode, each pipe restrained independently.", lead="Twin mains: ")
    _src(d, "G203 p50 §8 (access every 500 m) and §8.2.1 (profile); p51 §8.2.1 (run full) and "
            "§8.2.2 (layout); p52 §8.2.3 (twin mains) and §8.2.4 (cover); p53 §8.3 (material); "
            "pp 53 to 54 §8.4 (valves); p55 §8.5 (termination).")
    n_int = max(0, math.ceil(RM_LENGTH_M / 500.0) - 1)
    _ibri(d, f"The example main of {f0(RM_LENGTH_M)} m needs {n_int} intermediate access points "
             f"and {n_int} intermediate isolation valves at the 500 m spacing, and, being under "
             f"400 mm, 100 mm washouts. At 1:500 rising over its whole length it would climb "
             f"{RM_LENGTH_M / 500:.1f} m; the profile has to fit that inside the ground and the "
             f"cover rules.")
    _where(d, "Not in the code at concept stage. The route and profile of a rising main are "
              "drawn by hand along the street network and checked against these rules.")

    # ------------------------------------------------------------- 13.7
    D.h(d, 2, "13.7   Surge")
    _for(d, "To check that a pump trip or start does not burst the main or pull a vacuum in it.")
    _rule(d, "The pressure change from a sudden change of velocity is")
    eq = D.next_eq()
    M.display(d, M.seq(R("Δ"), R("H"), M.EQ, M.frac(R("c"), R("g")), R(" "), R("Δ"), R("v")),
              number=eq)
    _params(d, [["ΔH", "change in pressure head", "m"],
                ["c", "wave propagation speed in the pipe", "m/s"],
                ["g", "acceleration due to gravity, 9.81", "m/s²"],
                ["Δv", "change in flow velocity", "m/s"]])
    D.p(d, "The equation is for checking; the analysis itself is done in NWS-approved licensed "
           "software. The number of simultaneous pump starts and stops modelled follows N + 1, "
           "N being the pumps at the station, so that waves reflected from earlier events can "
           "combine into the true worst case. The model is run first with roughness near zero "
           "for the largest swing, then with realistic roughness. No vapour cavities and no "
           "column separation are allowed; the minimum pressure may not fall below the pipe "
           "maker's limit or 0.2 bar below atmospheric, whichever is higher; the maximum may not "
           "exceed the test pressure or the weakest component's rating. On a wastewater force "
           "main, air admitted at an air valve can be acceptable if the protection is designed "
           "for it. The wave speed is described only as depending on the pipe and the liquid; "
           "no formula is given, so it comes from the pipe maker's data or standard theory.")
    _src(d, "G201 pp 145 to 147 (Appendix III, Joukowsky, N + 1, criteria, force-main "
            "concession); scope p25 (final SewerGEMS model including surge).")
    v_pick = S["pick"]["v"]
    _ibri(d, f"A pump trip on the example main stops a flow moving at {f2(v_pick)} m/s. Each "
             f"100 m/s of wave speed gives ΔH = 100 / 9.81 × {f2(v_pick)} = "
             f"{f1(100 / 9.81 * v_pick)} m of head swing. The swing is set almost wholly by the "
             f"wave speed, and the wave speed by the pipe material and wall chosen, so the "
             f"material decision and the surge protection are one decision.")
    _where(d, "Not modelled yet; one SewerGEMS transient run per station at preliminary design.")

    # ------------------------------------------------------------- 13.8
    D.h(d, 2, "13.8   Emergency overflow")
    _for(d, "To decide in advance where sewage goes when a station fails, so that it does not "
            "go into houses.")
    _rule(d, "Every station shall have an emergency overflow, approved by the Environmental "
             "Authority, and only extreme events should use it. The overflow is never placed at "
             "an upstream manhole, where closing the inlet penstock for maintenance could spill "
             "by accident; the wet-well overflow carries a dip tube or baffle board. A method to "
             "prevent or minimise overflows is submitted for approval, chosen on least cost and "
             "least operational complexity from four: power from two independent sources or a "
             "generator; storage in trunk sewers and basins that drains back; emergency storage; "
             "and emergency pumping. For the network, retention basins are sized for 24 hours of "
             "nominal flow and emptied by tanker, and relief sewers for 1.5 times the nominal "
             "flow.")
    D.callout(d, "No station storage duration is given in the station chapter.",
              "G203 section 7.5 names emergency storage and stops. The 24-hour figure comes from the "
              "network overflow section and is applied to a station here by analogy; the 48 to "
              "72-hour figure elsewhere belongs to a lagoon at a treatment plant and is not "
              "transplanted. The design proposes, NWS approves.")
    _src(d, "G203 pp 46 to 47 §7.5; p191 §12.1.1 (retention basin 24 h, relief sewer 1.5 times).")
    _ibri(d, f"Twenty-four hours of nominal flow is one day's average flow: for the example "
             f"station at saturation, {f0(S['q_ult'])} m³, against a live volume of "
             f"{f2(S['V'])} m³. The emergency store is a separate structure, not a deeper wet "
             f"well. A relief sewer at 1.5 times the nominal flow would carry "
             f"{f1(1.5 * S['q_ult_ls'])} l/s.")
    _where(d, "Not in the code; a site-layout item for each station.")

    # ------------------------------------------------------------- 13.9
    D.h(d, 2, "13.9   Check it yourself")
    D.numbered(d, "After a gate run, open W13/run/summary.json: stations.count is 0 and "
                  "max_depth_m is under 12.0. If a station appears, check it sits at the lowest "
                  "chamber of its pocket and that the route was searched again before it was "
                  "accepted.")
    D.numbered(d, "For any station, sum Q_ULT of the plots upstream in W14/shp/PLOTS_load.shp, "
                  "peak it by Merrimack when more than 100 properties are served, and confirm the "
                  f"duty is at least that peak and the type follows G203 Table 17 (Table "
                  f"{t_types} here, the pumping station types).")
    D.numbered(d, "Recompute V = 0.25 Q T with the duty in m³/s and T = 360 s.")
    D.numbered(d, "For the chosen bore, confirm 1.0 m/s ≤ 4Q/πD² ≤ 2.5 m/s at the pump's delivery "
                  "with fixed-speed, start-stop pumps; 0.75 m/s is the floor only for continuous "
                  "delivery at the design minimum flow, and 1.2 m/s in a vertical main (G203 p50 "
                  "§8.1). A bore justified against 3.0 m/s has been checked against the wrong limit.")
    D.numbered(d, "Compute πD²L/4q̄ on the 2030 low-case average and carry the retention to the "
                  "odour assessment.")
    D.numbered(d, "List every pair of stations within 1,500 m and confirm each was examined for a "
                  "cascade or a merge.")


# =================================================================== 14
def c14_septicity(d):
    D.h(d, 1, "14   Septicity and odour", page_break=True)
    D.p(d, "Sewage that stands without oxygen turns septic. Sulphate-reducing bacteria in the "
           "slime on the pipe wall produce sulphide. Where the flow is turbulent, it leaves the "
           "water as hydrogen sulphide gas, which is toxic, smells at very low concentrations "
           "and oxidises on the pipe crown to sulphuric acid that attacks concrete and corrodes "
           "metal. Heat speeds every step, so in Ibri this is a design matter, not an operating "
           "one.")
    ib = _sett("IBRI")
    S = _station()
    g = _gate()
    w8 = _w8_drops()
    pick = S["pick"]

    # ------------------------------------------------------------- 14.1
    D.h(d, 2, "14.1   What the designer owes")
    _for(d, "To know what the guideline requires on odour and where in the network the risk "
            "sits.")
    _rule(d, "The designer of the sewers, stations and rising mains shall give NWS a dedicated "
             "hydrogen sulphide management evaluation, covering prevention (sizing, chemical "
             "injection) and correction (monitoring, flushing, coatings, odour treatment). The "
             "network is to be designed to minimise the conditions that generate odour: short "
             "retention, little turbulence, and no over-sized trunk sewers, which let solids "
             "settle. The risk concentrates in three places: rising mains, where sewage sits "
             "without air; very flat gravity sewers; and every drop, where turbulence strips the "
             "gas out of the water.")
    _src(d, "G203 p162 §11.1 (the evaluation); p166 §11.3.2 and p168 §11.4.2 (retention, "
            "turbulence, no over-sizing of trunk sewers); p185 (very flat sewers carry the "
            "greatest risk).")
    pct = ib["q_2030_low"] / ib["q_ult"] * 100.0
    _ibri(d, f"Some over-sizing is built into the design basis by necessity: pipes are sized on "
             f"saturation and cleansed on the opening year. Ibri produces {f0(ib['q_ult'])} m³/d "
             f"at saturation and {f0(ib['q_2030_low'])} m³/d in the 2030 low case, "
             f"{f0(pct)} % of it. A pipe sized for saturation runs at about {f0(pct)} % of its "
             f"design average in its first years, which is when deposits and septic slime form. That is "
             f"why the early-cleansing list of the self-cleansing check exists.")
    _where(d, "W14/analysis/design_flows.json, settlements, fields q_ult and q_2030_low. The "
              "evaluation is a report deliverable, not yet written.")

    # ------------------------------------------------------------- 14.2
    D.h(d, 2, "14.2   The three levers")
    _for(d, "To know what the designer can actually change.")
    _rule(d, "Three things decide how much sulphide forms and how much escapes.")
    D.bullet(d, "long retention lets sulphide build. A force main should ideally hold sewage no "
                "more than half an hour. Stations and mains are designed to minimise detention, "
                "and twin mains are considered to keep low flows moving.", lead="Retention. ")
    D.bullet(d, "low velocity means deposition and long retention together. Gravity sewers at "
                "very low slopes carry the greatest risk.", lead="Velocity. ")
    D.bullet(d, "every drop, jump and free discharge strips dissolved sulphide into the air, "
                "which is where the smell and the corrosion happen. Discharges are submerged "
                "where possible, and a backdrop (required where the invert drops more than "
                "600 mm, external, up to 2 m high, a vortex shaft beyond) is a turbulence point.",
             lead="Turbulence. ")
    _src(d, "G203 p50 §8.2.1 (half hour); pp 181 to 182 §11.5.3.1 (b), (c), (d), (f); p185 "
            "(flat sewers); p30 §4.4 (backdrops).")
    _ibri(d, f"The example rising main of the last chapter, {pick['id']} mm over "
             f"{f0(RM_LENGTH_M)} m, holds sewage for {f0(pick['t_low'])} minutes in the 2030 low "
             f"case, {pick['t_low'] / 30:.1f} times the half-hour ideal, before any wait in the wet "
             f"well. On the test boundary the gravity design has {f0(w8['drops'])} drops of more "
             f"than 600 mm, entering {f0(w8['chambers'])} chambers that need an external "
             f"backdrop. The test-boundary gate run counts {f0(g['vortex_sites'])} drops of more "
             f"than 2 m, beyond a backdrop, that need a vortex shaft. Each is a place where "
             f"dissolved sulphide leaves the water.")
    _where(d, f"Drops and backdrop chambers: field N_DROPS of W8/shp/W8_manholes.shp, summed, and "
              f"counted where above zero (the gate run's W13/run/summary.json key drops gives "
              f"{f0(g['drops'])}). Vortex drops: summary.json key vortex_sites, the drops of type "
              f"vortex (W13/py/run_test_boundary.py; W13/py/sewnet/stages/hydraulic.py).")

    # ------------------------------------------------------------- 14.3
    D.h(d, 2, "14.3   Screening by the Fayoux score")
    _for(d, "A quick qualitative ranking of where hydrogen sulphide will form.")
    _rule(d, "Score four factors from the table and add the scores. As printed: 0 to 5 no risk, "
             "5 to 10 low risk, 10 to 30 significant risk, and 20 to 30 certain risk. The last "
             "two bands overlap in the guideline and the scale stops at 30. The inputs are the "
             "maximum possible temperature, and the residence time and minimum average velocity "
             "at night-time flow. Where a value falls between columns, the less favourable "
             "column is taken; that is our reading, as is treating a sum above 30 as certain.")
    t_fay = D.tab_caption(d, "Fayoux qualitative risk of hydrogen sulphide formation (G203 p185 Table 99)")
    D.table(d, ["Factor", "", "", "", "", ""],
            [["**Temperature**", "5 °C", "10 °C", "15 °C", "20 °C", "> 20 °C"],
             ["score", "0", "2", "4", "10", "20"],
             ["**Residence time**", "1 h", "3 h", "6 h", "12 h", "24 h"],
             ["score", "0", "1", "4", "6", "15"],
             ["**Average velocity over 24 h**", "1 m/s", "0.8 m/s", "0.6 m/s", "0.4 m/s", "0.2 m/s"],
             ["score, instantaneous 0.6 m/s", "–", "–", "–", "10", "15"],
             ["score, instantaneous 1.0 m/s", "0", "1", "2", "6", "10"],
             ["score, instantaneous 1.5 m/s", "0", "0", "0", "2", "6"],
             ["**Redox potential Eh**", "+200 mV", "+100 mV", "0 mV", "−100 mV", "−200 mV"],
             ["score", "0", "3", "15", "30", "> 30"]],
            widths=[5.4, 2.2, 2.2, 2.2, 2.2, 2.4], font=9)
    _src(d, "G203 p185 Table 99 (after Fayoux, 1988). Temperature: inland climate, maximum "
            "yearly average 35 °C (G201 p78 Table 24); the guidelines give no sewage "
            "temperature.")
    fy = _fayoux(35.0, pick["t_low"] / 60.0, pick["vavg"], pick["v"])
    _ibri(d, f"For the example main, with the 2030 low-case daily average standing in for the "
             f"night-time flow (night flow is lower, so the result is a lower bound): temperature "
             f"above 20 °C scores {fy['s_t']}; a residence of {pick['t_low'] / 60:.1f} h scores "
             f"{fy['s_r']}; a 24-hour average velocity of {f2(pick['vavg'])} m/s falls in the "
             f"{fy['col']:.1f} m/s column and, with {f2(pick['v'])} m/s while pumping, in the "
             f"{fy['row']:.1f} m/s row, scoring {fy['s_v']}. No redox record is held, so that "
             f"factor is not scored. The sum is at least {fy['total']}: {fy['band']}. The "
             f"lesson is the temperature term. Every sewer in Ibri starts at 20, inside the "
             f"significant band before anything else is counted, so the method cannot tell a "
             f"good option from a bad one here. Computed retention and velocity do that.")
    _where(d, "A hand calculation, with inputs from the rising main sizing in 13.5.")

    # ------------------------------------------------------------- 14.4
    D.h(d, 2, "14.4   The Pomeroy–Parkhurst equations")
    _for(d, "A quantitative estimate of sulphide build-up in gravity sewers and rising mains.")
    _rule(d, "For a gravity sewer the rate of change of sulphide is a generation term less a "
             "loss term:")
    eq = D.next_eq()
    M.display(d, M.seq(
        M.frac(R("dS"), R("dt")), M.EQ, R("3.23"), R(" "), M.sup(R("M"), R("′")), R(" "),
        M.delim(UP("EBOD"), "[", "]"), R(" "), M.sup(R("r"), R("−1")), M.MINUS,
        R("2.1"), R(" "), R("N"), R(" "), M.sup(M.delim(M.seq(R("s"), R(" "), R("v"))), R("0.375")),
        R(" "), M.delim(R("S"), "[", "]"), R(" "), M.sup(M.sub(R("d"), UP("m")), R("−1"))),
        number=eq)
    _params(d, [["[S]", "sulphide concentration", "mg/l"],
                ["t", "retention time", "not stated"],
                ["M′", "effective sulphide flux in gravity sewers", "not stated"],
                ["[EBOD]", "effective BOD", "mg/l"],
                ["r", "hydraulic radius", "not stated"],
                ["N", "empirical factor for loss of sulphide", "not stated"],
                ["s", "slope of the energy grade", "not stated"],
                ["v", "mean velocity", "not stated"],
                ["d m", "mean hydraulic depth, area over top width", "not stated"]])
    D.p(d, "The effective BOD corrects the 20 °C BOD to the sewage temperature:")
    eq = D.next_eq()
    M.display(d, M.seq(M.delim(UP("EBOD")), M.EQ, M.sub(UP("BOD"), R("5")), R(" "),
                       M.sup(M.delim(R("1.07")), M.seq(R("T"), M.MINUS, R("20")))), number=eq)
    _params(d, [["EBOD", "effective BOD", "mg/l"],
                ["BOD5", "five-day BOD at 20 °C", "mg/l"],
                ["T", "sewage temperature", "°C"]])
    D.p(d, "For rising mains the guideline gives a modified form:")
    eq = D.next_eq()
    M.display(d, M.seq(R("S"), M.EQ, M.sub(R("K"), UP("s")), R(" "), M.sub(UP("BOD"), R("5")),
                       R(" "), R("t"), R(" "), R("f"), M.delim(R("T"))), number=eq)
    _params(d, [["K s", "sulphide generation rate constant", "not stated"],
                ["t", "retention time", "not stated"],
                ["f(T)", "temperature function", "form not stated"]])
    D.callout(d, "The equations cannot be evaluated from the guideline.",
              "No value is given for M′ or N, and most symbols carry no units. The rising main "
              "form gives K s neither a value nor a unit and f(T) no form. Both establish that "
              "sulphide rises with retention and temperature; neither yields a number without "
              "going to the original Pomeroy and Parkhurst work, and every coefficient taken from "
              "there is an outside assumption, tagged as such.")
    _src(d, "G203 pp 185 to 186 §11.5.3 (Pomeroy–Parkhurst, EBOD correction, rising-main form).")
    fac = {t: 1.07 ** (t - 20) for t in (25, 30, 35)}
    _ibri(d, f"The temperature factor 1.07^(T − 20) is {f2(fac[25])} at 25 °C, {f2(fac[30])} at "
             f"30 °C and {f2(fac[35])} at 35 °C, the inland maximum yearly average. Whatever the "
             f"coefficients turn out to be, the generation term in Ibri runs at two to three "
             f"times its rate at 20 °C, and it scales straight into sulphide per minute of "
             f"retention.")
    _where(d, "Not in the code; used only if the evaluation of 14.1 needs a number the "
              "design values of 14.5 do not give.")

    # ------------------------------------------------------------- 14.5
    D.h(d, 2, "14.5   Design concentrations at the end of a rising main")
    _for(d, "To size monitoring and management where no field data exists.")
    _rule(d, "Where hydrogen sulphide generation is expected (long retention, septic "
             "conditions) and no field data is available, management and monitoring at the "
             "termination of the pressure main, at the treatment plant or in the network, are "
             "designed for an average concentration of 50 to 100 ppm and a peak of no more than "
             "200 ppm. The termination manhole is studied for a monitoring system that controls "
             "chemical injection at the start of the main, and is sealed, force-vented through "
             "odour control where the discharge is turbulent, and lined or built of "
             "corrosion-resistant material.")
    _src(d, "G203 p47 §7.7; p55 §8.5.")
    fm = _ww("Force main")
    ps = _ww("Pumping station")
    _ibri(d, f"The example main scores {fy['band']} and holds sewage for about "
             f"{f0(pick['t_low'])} minutes in its first years, so the 50 to 100 ppm and 200 ppm "
             f"values apply at its termination. The test-boundary design has "
             f"{f0(g['stations']['rising_main_m'])} m of rising main and no termination to treat. "
             f"The existing network has {fm[2]} of built force main behind {ps[2]} station, "
             f"whose termination is the same design case if it is kept.")
    _where(d, "W14/report/data_facts.py, WASTEWATER, for the existing force main and station; "
              "summary.json stations.rising_main_m for the design.")

    # ------------------------------------------------------------- 14.6
    D.h(d, 2, "14.6   Design measures, in the order the guideline prefers them")
    _for(d, "To act on the risk in order of permanence and cost, treatment last.")
    _rule(d, "Work down the list; go to the next measure only when the one before is exhausted.")
    D.numbered(d, "Avoid pumping wherever gravity is feasible and cost-effective.")
    D.numbered(d, "Where pumping stays, minimise detention: twin or dual mains to keep low flows "
                  "moving, the main draining back to the well between cycles where it can, no "
                  "partly full sections.")
    D.numbered(d, "Discharge submerged to absorb energy. Inverted siphons shall not be allowed.")
    D.numbered(d, "Bring gravity sewers into stations with the least free fall and turbulence.")
    D.numbered(d, "Keep air moving: wet-well levels that do not block air in the sewer, and vents "
                  "no smaller than 150 mm and 6 m above ground, with a UV-resistant cap.")
    D.numbered(d, "Do not over-size trunk sewers.")
    D.numbered(d, "Only then treat. Vapour-phase odour treatment comes first and liquid-phase "
                  "dosing (metal salts, oxidants and the like) supplements it. Every odour "
                  "control system is N + 1, and an integrated system removes 99.95 % of hydrogen "
                  "sulphide and 85 % of odour. The guideline gives no dose rates, so any dosing "
                  "proposal is the designer's to substantiate.")
    _src(d, "G203 pp 181 to 182 §11.5.3.1 (a) to (j) and §11.5.3.2; p183 (dosing chemicals); "
            "p32 §4.5 (vents); pp 166, 168 (no over-sizing); p175 (N + 1, 99.95 % and 85 %).")
    _ibri(d, f"Measure 1 is met on the test boundary: {g['stations']['count']} stations and "
             f"{f0(g['stations']['rising_main_m'])} m of rising main. The measures that remain "
             f"there are 5 and 6: ventilation at the {f0(w8['chambers'])} backdrop chambers, and "
             f"pipes sized on saturation and nothing larger.")
    _where(d, "summary.json keys stations and vortex_sites; W8/shp/W8_manholes.shp, field N_DROPS.")

    # ------------------------------------------------------------- 14.7
    D.h(d, 2, "14.7   Check it yourself")
    D.numbered(d, "For each rising main compute πD²L/4q̄ on the 2030 low-case average and flag "
                  "any retention over 30 minutes.")
    D.numbered(d, f"Score each main and each very flat gravity reach with G203 Table 99, the "
                  f"Fayoux table (Table {t_fay} here), at night-time flow; record the band and "
                  f"which factor drove it.")
    D.numbered(d, "Recompute 1.07^(T − 20) at the temperature used, and write down where that "
                  "temperature came from.")
    D.numbered(d, "Check every rising main enters its receiving manhole no more than 300 mm "
                  "above the flow line and carries a monitoring point.")
    D.numbered(d, "Count the backdrop chambers (N_DROPS above zero in W8/shp/W8_manholes.shp) "
                  "and the vortex drops (vortex_sites in summary.json) and confirm each is "
                  "ventilated.")


# =================================================================== 15
def c15_utilities(d):
    D.h(d, 1, "15   Utilities and crossings", page_break=True)
    D.p(d, "A sewer shares its corridor with water mains, power cables, telecom ducts and, in "
           "places, fuel lines and aflaj. A clash found on site costs a redesign under traffic; "
           "found at concept stage it is a routing choice. This chapter covers what we hold, "
           "how the clashes are found, the separations the guideline sets, and the three kinds "
           "of crossing: roads, wadis and aflaj.")
    g = _gate()
    area = g["s1"]["boundary_ha"] / 100.0
    rt = g["road_treatment"]
    mc = F.meter_counts()
    paew = next(x for x in DF.WATER if x[0] == "PAEW water mains")
    paew_in = paew[3].split(" (")[0]

    # ------------------------------------------------------------- 15.1
    D.h(d, 2, "15.1   What we hold, and what we do not")
    _for(d, "To know which clashes can be checked now and which wait for the owners' records.")
    _rule(d, "Only a record of an asset's route, and ideally its depth, can be used for a clash "
             "check. A customer point locates a customer, not the cable that feeds it.")
    _src(d, "Received-data register of the Concept Design Report, Part B.")
    el_st = _register("Electricity, telecom and gas service records")
    _ibri(d, f"The electricity file holds {f0(mc['total'])} meters: points with a tariff and a "
             f"coordinate, no cable route and no depth. The potable water network is the PAEW "
             f"dataset, {paew_in} of mains inside the study area, the one utility whose routes "
             f"are held. Electricity, telecom and gas service records: {el_st[1].lower()}.")
    _where(d, "W14/report/data_facts.py, lists OTHER, WATER and REGISTER; "
              "facts_w14.meter_counts().")

    # ------------------------------------------------------------- 15.2
    D.h(d, 2, "15.2   Finding the clashes")
    _for(d, "To find every clash before the alignment is fixed.")
    _rule(d, "Six steps.")
    D.numbered(d, "Obtain service drawings from every owner with assets in the area: electricity "
                  "distribution, telecom operators, gas and fuel operators, the municipality, "
                  "the roads authority and the falaj owners.")
    D.numbered(d, "Superimpose the proposed alignment on each set.")
    D.numbered(d, "Choose the trial-pit sites: road intersections, crossings of major services, "
                  "and the routes of primary sewers and rising mains.")
    D.numbered(d, "Agree the pit programme with NWS, obtain the municipal excavation permit and "
                  "notify the owners.")
    D.numbered(d, "Where a clash cannot be avoided, price moving our asset against moving theirs, "
                  "and obtain the owner's agreement for the cheaper one.")
    D.numbered(d, "Show every crossing with another underground utility on the sewer's hydraulic "
                  "profile; the scope requires the profile to highlight them.")
    D.p(d, "The scope provides fifty trial pits at critical locations the consultant proposes. "
           "The formal utility survey belongs to the preliminary stage, but the concept design "
           "must already show that each route can be built, so the desk study and the critical "
           "pits start now. Detection covers oil, gas, water and effluent pipelines, cables and "
           "irrigation aflaj, by trial pits, probing, ground radar and electro-location.")
    _src(d, "Scope p7 items 7 and 13 (trial pits, fifty); p11 item 2 (profile highlighting "
            "crossings); p18 §4.1.2.2 (utility surveys, re-routing); G203 p198 §13.3 "
            "(underground services detection).")
    _ibri(d, f"On the {f2(area)} km² test boundary alone the design crosses dual carriageways at "
             f"{rt['dual_crossings_added']} places, each a trial-pit candidate. Over a "
             f"{F.fmt(DF.BOUNDARY_KM2, 1)} km² study area, fifty pits go to the crossings that "
             f"decide a route, not to confirm what the records already show.")
    _where(d, "W13/run/summary.json, road_treatment.dual_crossings_added "
              "(W13/py/sewnet/stages/road_treatment.py).")

    # ------------------------------------------------------------- 15.3
    D.h(d, 2, "15.3   Clearances")
    _for(d, "To keep enough distance from other services to build, maintain and repair each "
            "without disturbing the other.")
    _rule(d, "The separations below apply; beyond them, the owning authority's own requirement "
             "governs.")
    D.tab_caption(d, "Separation from other services")
    D.table(d, ["Situation", "Requirement", "Source"],
            [["Gravity sewer to other utilities", "**3 m** minimum horizontal clearance", "G203 p33 §4.6.3"],
             ["Another utility in the same trench", "on a separate bench on undisturbed soil", "G203 p33"],
             ["Shallow sewer beneath a major road or highway", "a proper design check", "G203 p33"],
             ["Force main to water main, horizontal", "**3.0 m** minimum", "G203 p51 §8.2.2"],
             ["Force main crossing a water main",
              "**under** it, **450 mm** outside to outside; one full water pipe length centred "
              "on the crossing", "G203 p51"],
             ["Force main on a highway", "in the carriageway, at least 1 m from the kerb line; "
              "manholes at least 0.5 m from it", "G203 p51"],
             ["Sewer in a private area", "at least 3 m between buildings and sewer; manholes "
              "accessible 24 hours a day", "G203 p51"],
             ["Service corridor, DN200 to DN500", "2.0 m reservation", "G203 p32 Table 13"]],
            widths=[5.4, 7.6, 3.6], font=9)
    _src(d, "As in the table.")
    _ibri(d, f"The {paew_in} of PAEW water main inside the study area is the one set against "
             f"which these separations can be checked now. Every rising main must keep 3.0 m from "
             f"it and pass under it with 450 mm clear.")
    _where(d, "W14/report/data_facts.py, WATER; the PAEW layer in the RECEIVED DATA group of the "
              "project QGIS file.")

    # ------------------------------------------------------------- 15.4
    D.h(d, 2, "15.4   Roads and dual carriageways")
    _for(d, "To keep sewers out of roads that cannot be dug up, and to cross roads with the least "
            "disruption.")
    _rule(d, "No sewer of any kind runs along a dual carriageway, primary sewer included, "
             "because it cannot be dug up for maintenance. A dual carriageway is crossed only by "
             "a short pipe at right angles to it. Dual carriageways are read from the dual "
             "column of the road centrelines: 1 is a dual carriageway and is excluded; 2 is a "
             "two-lane pair of which only one side is used. Existing roads are crossed by "
             "trenchless methods wherever possible; where a road is cut, it is reinstated to the "
             "Oman Highway Design Manual, and pressure mains get valves on both sides of a major "
             "road crossing.")
    _src(d, "Project rule (engineer, 2026-08-19; CLAUDE.md rule 7); G201 p85 §9.1 (trenchless "
            "crossing, reinstatement to the Oman Highway Design Manual) and §9.2 (valves either "
            "side of a major road crossing); G203 p21 and p35 (trenchless, subject to NWS "
            "approval).")
    _ibri(d, f"On the {f2(area)} km² test boundary, {rt['dual_excluded']} of the "
             f"{f0(g['s1']['segs_raw'])} road segments are dual carriageway and carry no sewer; the "
             f"design crosses them at {rt['dual_crossings_added']} places. The network built in "
             f"2006 agrees with the rule in practice: 4 of its 3,267 pipes, 0.1 %, run within "
             f"4 m of a dual carriageway.")
    _where(d, "W13/py/sewnet/stages/road_treatment.py; summary.json keys s1.dual_1, "
              "road_treatment.dual_excluded and road_treatment.dual_crossings_added. The as-built "
              "count: W7/docs/CALIBRATION_vs_EXISTING.md.")

    # ------------------------------------------------------------- 15.5
    D.h(d, 2, "15.5   Wadis and aflaj")
    _for(d, "To keep pipes out of ground that floods and scours, and to cross it safely where it "
            "cannot be avoided.")
    _rule(d, "Pipes and chambers are not laid in wadis or in ground subject to washout: the "
             "guideline says this must be avoided and shall be avoided. The design avoids it; "
             "where it finds no other way, the presence is a recorded and justified exception "
             "carried into the deliverable, never a silent one. Crossing a wadi is a separate "
             "matter with its own rules.")
    D.bullet(d, "1.5 m to the crown at a wadi crossing, gravity sewer and force main alike; "
                "2.0 m in soft soil.", lead="Cover: ")
    D.bullet(d, "ductile iron over the crossing and 15 m either side, with mechanical or "
                "detachable joints; protection to NWS drawing PAM-STD-404, checked against "
                "flotation of the empty pipe.", lead="Pipe: ")
    D.bullet(d, "isolation and air valves on both sides of an active or major crossing and a "
                "washout at the low point on one side; no chamber or marker post in the bed or on "
                "the banks, and every valve reachable while the wadi is in flood.",
             lead="Valves: ")
    D.bullet(d, "bed profiles, flood frequency (1 in 20, 50 and 100 years), bed material and "
                "bed-level change from the agencies, and MoAFWR approval.",
             lead="Data and approval: ")
    D.bullet(d, "buffer zones around each falaj, minimum safe distances for excavation, and "
                "protection written into the contractor's environmental plan.", lead="Aflaj: ")
    _src(d, "G203 p30 §4.4.1(a) and p33 (avoid wadis); G203 p52 §8.2.4 (1.5 m); G201 pp 85 to 86 "
            "§9.3 (wadi crossings, 2.0 m in soft soil) and §9.4 (aflaj). Project rule: recorded "
            "exception (engineer, 2026-09-07). Wadi ground is taken as classes 4 to 6 of the "
            "50-year flood-hazard grid, a project assumption pending a scour check.")
    _ibri(d, "A DN200 sewer, the smallest street pipe, has its invert at least 1.5 + 0.2 = 1.7 m "
             "under the wadi bed at a crossing, and 2.2 m in soft soil, before any allowance for "
             "scour. On flat ground that extra depth has to be found upstream and recovered "
             "downstream, so a wadi crossing can deepen the chambers on either side.")
    _where(d, "W13/py/sewnet/criteria.py, HAZARD_WADI_CLASSES = (4, 5, 6); the flood grid is "
              "RunConfig.hazard in pipeline.py.")

    # ------------------------------------------------------------- 15.6
    D.h(d, 2, "15.6   Check it yourself")
    D.numbered(d, "List every utility owner in the area and the date each set of service "
                  "drawings was requested and received.")
    D.numbered(d, "Overlay the rising mains on the PAEW mains and measure the closest approach; "
                  "anything under 3.0 m is a clash.")
    D.numbered(d, "Filter the road centrelines on dual = 1 and confirm no design pipe runs along "
                  "one; every pipe touching one must cross it at right angles.")
    D.numbered(d, "Overlay the network on flood-hazard classes 4 to 6; every chamber inside is a "
                  "recorded exception with its reason.")
    D.numbered(d, "At each wadi crossing check the crown cover is 1.5 m, or 2.0 m in soft soil, "
                  "on the long section.")


# =================================================================== 16
def c16_modelling(d):
    D.h(d, 1, "16   Hydraulic modelling", page_break=True)
    D.p(d, "The model is not a check run after the design; it is a contract deliverable in its "
           "own right, submitted in native editable format and updated after construction. On "
           "this project it has a second job: it is the independent referee of a network that "
           "the project's own code lays and sizes.")
    _fig(d, "F12_modelling", "Building and proving the model. The early-year run matters as much "
                             "as the design-year run.")
    fl = _flows()
    tot = fl["totals"]
    g = _gate()
    ib = _sett("IBRI")
    ibr = _row("IBRI")

    # ------------------------------------------------------------- 16.1
    D.h(d, 2, "16.1   The model is a contract deliverable")
    _for(d, "To know what model is owed, in what software, and when.")
    _rule(d, "The concept hydraulic calculations for the wastewater network are prepared on "
             "SewerGEMS, and those for the treated effluent network on WaterGEMS. Models are "
             "submitted for the design years start (to be agreed), 2030, 2055 and ultimate, and "
             "the final models include surge. Static, extended-period and surge models go to NWS "
             "after each design phase, and again after construction. The method follows the "
             "WaPUG and CIWEM codes of practice and the US EPA SWMM manuals, and the calculations "
             "run in licensed software approved by NWS.")
    D.callout(d, "The tender names two packages.",
              "The scope names SewerGEMS and WaterGEMS, or other software agreed during the "
              "project. The staffing schedule asks the network design engineer for proficiency "
              "in Mike Urban. The modelling software is one of the matters put to NWS for "
              "confirmation.")
    _src(d, "Scope p8 item 19, p14, p17 and p25; tender p123 (staffing); G201 p109 §13.4.2 and "
            "p144 (submissions, method); G203 p24 §4.2.1 (licensed software).")
    _ibri(d, "The flows the model years carry, whole study area, are in the table below.")
    D.tab_caption(d, "Model-year flows, average dry weather, whole study area")
    rows = [["2024", "today, from the meters", f0(tot["2024"]["people"]), f0(tot["2024"]["qadf_m3d"])],
            ["2030", "opening year", f0(tot["2030"]["people"]), f0(tot["2030"]["qadf_m3d"])],
            ["2055", "model year", f0(tot["2055"]["people"]), f0(tot["2055"]["qadf_m3d"])],
            [str(F.totals()["ultimate"]), "saturation, the sizing case", f0(tot["2070"]["people"]),
             f0(tot["2070"]["qadf_m3d"])]]
    D.table(d, ["Year", "Role", "People", "Qadf, m³/d"], rows, widths=[2.4, 6.4, 3.8, 4.0],
            font=9.5, align_right={2, 3})
    _where(d, "W14/analysis/design_flows.json, totals; generated by W14/py/make_design_flows.py.")

    # ------------------------------------------------------------- 16.2
    D.h(d, 2, "16.2   SewerGEMS as the referee")
    _for(d, "To prove the design with software nobody on the project wrote.")
    _rule(d, "The network is laid and sized by the project's own code. SewerGEMS then re-solves "
             "the same network, and two gates stand between the code and a design called "
             "verified.")
    D.numbered(d, "The code's partly-full Colebrook-White solver reproduces the minimum gradients "
                  "of G203 Table 11 within 5 %.", lead="Solver gate. ")
    D.numbered(d, "Every pipe's discharge, velocity and d/D from SewerGEMS agrees with the code "
                  "within 5 %. A pipe outside that is investigated before the design is "
                  "accepted. Small differences are expected from junction losses, which the code "
                  "ignores at concept stage, and from SewerGEMS's gradually-varied flow against "
                  "the code's normal depth.", lead="Referee gate. ")
    D.p(d, "Three import traps have cost time before. Levels go in as elevations, never depths. "
           "After the build, every conduit's Set Invert to Start Node and Set Invert to Stop "
           "Node must be set to False, or the mapped inverts are overwritten and every drop "
           "manhole is lost. A loads import replaces each manhole's whole load collection, so the "
           "full table is always imported, never a part. The exported base flow is an average: "
           "the model must apply the same peak as the code, Merrimack or Peltier per pipe, or the "
           "comparison compares two different flows. Check it on three pipes of different size "
           "before comparing the rest.")
    _src(d, "Project rule: the verification regime (engineer, 2026-08-18; W4/docs/PLAN.md §3b); "
            "G203 p29 Table 11; G203 p24 §4.2.1.")
    _ibri(d, f"The test-boundary package carries {f0(g['n_nodes'])} manholes, "
             f"{f0(g['n_pipes'])} conduits and one outfall, with the code's discharge, velocity "
             f"and d/D beside empty SewerGEMS columns for every conduit.")
    _where(d, "W13/py/sewnet/export_gems.py writes MANHOLES, CONDUITS and OUTFALL shapefiles, "
              "LOADS.xlsx and REFEREE_pipes.csv; the import walk-through is "
              "W8/sewergems/IMPORT_PROCEDURE.md. The exported loads are still the old flat figure "
              "per property (criteria.PLOT_QADF_LS) under a Fixed pattern; they are replaced by "
              "the plots' Q_ULT before the referee run.")

    # ------------------------------------------------------------- 16.3
    D.h(d, 2, "16.3   What is loaded, and where")
    _for(d, "To put the right flow on every pipe.")
    _rule(d, "Each plot carries its average dry-weather flow for 2024, 2030, 2055 and "
             "saturation, and nothing else. The model adds the rest, per pipe.")
    D.numbered(d, "Sum the flow of the plots upstream of the pipe, in m³/d, and count the "
                  "properties upstream.")
    D.numbered(d, f"Peak it. Over 100 properties, Merrimack, with both flows in Ml/d; 100 or "
                  f"fewer, Peltier, with the average in l/s. The hourly peak factor should not "
                  f"exceed 5.0; that is a recommendation, not a cap to apply silently. In the "
                  f"self-cleansing case the count that chooses the formula is the connected one, "
                  f"the 2030 properties × {fl['rules']['connection_ratio_2030']:.2f}, as "
                  f"recommended in the design-flow handoff, to be confirmed by the engineer.")
    D.numbered(d, "Add infiltration of 720 l/d per km of new sewer, by each pipe's own length, "
                  "accumulated downstream. It is added unpeaked; the guideline does not state "
                  "the order, so that is our reading, to be confirmed. Storm water is not "
                  "considered.")
    D.numbered(d, "Load each plot at the manhole it drains to, from the plot layer, never spread "
                  "evenly over the network.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("pdf")), M.EQ, R("2.65"), R(" "),
                       M.sup(M.sub(R("Q"), UP("adf")), R("0.879"))), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(UP("PF"), M.EQ, R("1.5"), M.PLUS,
                       M.frac(R("1"), M.sqrt(M.sub(R("Q"), UP("m"))))), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("inf")), M.EQ, R("720"), R(" "), R("L")), number=eq)
    _params(d, [["Q pdf", "peak dry-weather flow, Merrimack", "Ml/d"],
                ["Q adf", "average dry-weather flow upstream", "Ml/d"],
                ["PF", "peak factor, Peltier", "—"],
                ["Q m", "average flow upstream, Peltier", "l/s"],
                ["Q inf", "infiltration", "l/d"],
                ["L", "length of sewer upstream", "km"]])
    _src(d, "G201 p71 §7.4.2 (Merrimack, over 100 properties), p72 (Peltier, 5.0 "
            "recommendation, §7.4.3 infiltration), p73 (100 % coverage by the end of the "
            "period). Project rule: size on Q_ULT, infiltration per pipe and never per plot "
            "(engineer, 2026-09-11).")
    qp = _merrimack_mld(ib["q_ult"])
    ql = _merrimack_mld(ib["q_2030_low"])
    n_head = 60
    ppl = n_head * ibr["or_used"]
    qm = ppl * FUT_LPD / 86400.0
    pfp = 1.5 + 1.0 / math.sqrt(qm)
    km_txt = f2(g["net_km"])
    inf = 720.0 * float(km_txt.replace(",", ""))     # from the printed length, so the product holds
    _ibri(d, f"Ibri at saturation: Qadf = {f1(ib['q_ult'])} m³/d, {ib['q_ult'] / 1000:.3f} Ml/d, so "
             f"Qpdf = 2.65 × {ib['q_ult'] / 1000:.3f}^0.879 = {qp:.2f} Ml/d, {f0(qp * 1000 / 86.4)} l/s, "
             f"a peak factor of {f2(qp / (ib['q_ult'] / 1000))}. At the head of a system, a pipe "
             f"serving {n_head} future properties at Ibri's occupancy of {ibr['or_used']:.2f} "
             f"carries {f0(ppl)} people × {f1(FUT_LPD)} l/d = {f2(qm)} l/s on average; Peltier "
             f"gives PF = 1.5 + 1/√{f2(qm)} = {f2(pfp)} and a peak of {f2(qm * pfp)} l/s. The "
             f"{km_txt} km of the test-boundary network takes 720 × {km_txt} = "
             f"{f0(inf)} l/d of infiltration, {f1(inf / 1000)} m³/d or {f2(inf / 86400)} l/s at "
             f"its outfall.")
    _where(d, "W14/shp/PLOTS_load.shp, fields QADF, Q_2030, Q_2055, Q_ULT, G_DOM, POP, "
              "POP_ULT and OR_S; W14/docs/DESIGN_FLOWS_FOR_NETWORK.md; "
              "W13/py/sewnet/stages/loads.py (INFILT_L_D_KM = 720 on upstream length, "
              "unpeaked). The code still reads the flat load until it is joined to PLOTS_load.")

    # ------------------------------------------------------------- 16.4
    D.h(d, 2, "16.4   Which runs")
    _for(d, "To run each check on the flow that can make it fail.")
    _rule(d, "Accuracy is directional. Capacity fails on an under-estimate; the self-cleansing "
             "check fails on an over-estimate, because a pipe credited with more early flow than "
             "it gets is declared self-cleansing while it silts. So capacity is run on the high "
             "case and cleansing on the low one, and saturation × 0.61 is never used: it mixes "
             "2070 people with a 2028 connection share.")
    D.tab_caption(d, "The model runs")
    D.table(d, ["Run", "Load", "What it decides"],
            [["Capacity", "Q_ULT upstream, peaked per pipe, plus infiltration",
              "pipe size; depth of flow and 3.0 m/s maximum (G203 p27)"],
             ["Self-cleansing", "Q_2030 × 0.61 upstream, peaked per pipe",
              "velocity test (0.75 m/s at peak) and tractive-slope test; the four classes"],
             ["Model years", "Q_2030 and Q_2055, peaked", "pump staging, surcharge in between"],
             ["Plant", "settlement totals by year, plus network infiltration and 10 %",
              "plant capacity and phasing"],
             ["Surge", "pump trips and starts, N + 1 events", "rising main protection"]],
            widths=[3.0, 6.6, 7.0], font=9)
    _src(d, "Project rule: two flow cases (engineer, 2026-09-11); accuracy is directional "
            "(doctrine §2 item 1d). G201 p73 (coverage 100 % by the end of the period, plant "
            "+10 %); G203 pp 25 to 27 §4.2.2.1; scope p14 (design years).")
    q_ult, q30 = tot["2070"]["qadf_m3d"], tot["2030"]["qadf_m3d"]
    low = fl["low_case_2030_m3d"]
    wrong = q_ult * fl["rules"]["connection_ratio_2030"]
    _ibri(d, f"Whole area: {f0(q_ult)} m³/d at saturation; {f0(q30)} m³/d in 2030, × 0.61 = "
             f"{f0(low)} m³/d. Saturation × 0.61 would give {f0(wrong)} m³/d, "
             f"{f2(wrong / low)} times the flow expected in 2030, and would pass as self-cleansing "
             f"pipes that silt. Ibri alone peaks at {f0(ql * 1000 / 86.4)} l/s in the 2030 low case "
             f"against {f0(qp * 1000 / 86.4)} l/s at saturation. The plant case is "
             f"{f0(fl['stp_ultimate_with_margin_m3d'])} m³/d with the 10 % margin.")
    _where(d, "W14/analysis/design_flows.json: rules, totals, low_case_2030_m3d, "
              "stp_ultimate_with_margin_m3d.")

    # ------------------------------------------------------------- 16.5
    D.h(d, 2, "16.5   Calibration")
    _for(d, "To make the model reproduce what the network actually does before it is trusted "
            "to predict.")
    _rule(d, "Where measured flow exists, the model is calibrated against it to the acceptance "
             "below. The existing network enters the model only after it has been verified by "
             "survey, because NWS itself declares its records inaccurate.")
    D.tab_caption(d, "Wastewater model calibration acceptance (G201 p145 Table 32)")
    D.table(d, ["Parameter", "Typical acceptance"],
            [["Peak flow", "± 10 to 15 %"], ["Volume", "± 15 %"],
             ["Timing", "correct peak arrival"], ["Pump runtime", "± 10 %"]],
            widths=[8.3, 8.3], font=9.5)
    _src(d, "G201 p145 Table 32; tender p201 (existing layout inaccurate, as-built in scope).")
    pl = _register("Plant inflow and tanker records")
    stp = _ww("Treatment plant")
    _ibri(d, f"No measured flow is held. Plant inflow and tanker records: {pl[1].lower()}. The "
             f"concept model is therefore uncalibrated and says so. The existing plant's nominal "
             f"capacity on record is {stp[2]}, against {f0(tot['2024']['qadf_m3d'])} m³/d the "
             f"study area generates today on the network-accounted basis.")
    _where(d, "W14/report/data_facts.py, REGISTER and WASTEWATER.")

    # ------------------------------------------------------------- 16.6
    D.h(d, 2, "16.6   Check it yourself")
    D.numbered(d, "Run the solver gate: the code's minimum gradients against G203 Table 11, "
                  "every row within 5 %.")
    D.numbered(d, "Import the package, set both Set Invert flags to False, run steady state and "
                  "paste discharge, velocity and d/D into REFEREE_pipes.csv; list every pipe "
                  "outside 5 %.")
    D.numbered(d, "Pick three pipes of different size and check the model's peak equals "
                  "Merrimack or Peltier on the upstream flow.")
    D.numbered(d, "Sum the manhole loads and compare with the sum of Q_ULT over the plots inside "
                  "the boundary; they must match before infiltration.")
    D.numbered(d, "Confirm the self-cleansing run uses Q_2030 × 0.61 per plot, not saturation × "
                  "0.61.")


# =================================================================== 17
def c17_existing(d):
    D.h(d, 1, "17   The existing network", page_break=True)
    D.p(d, "Ibri already has sewers. The concept design has to say what happens to them: what is "
           "kept, what is upgraded, what is replaced, and how the new network joins the old. "
           "That is a priced deliverable in its own right, not a preface to the new design.")
    _fig(d, "F13_existing", "Assessing the existing network. Rehabilitation is a priced "
                            "deliverable in its own right.")
    ab = _asbuilt()
    gs, fm, te, ps, stp = (_ww(a) for a in ("Gravity sewer", "Force main", "Treated effluent main",
                                            "Pumping station", "Treatment plant"))
    tot = F.totals()

    # ------------------------------------------------------------- 17.1
    D.h(d, 2, "17.1   Two networks in one dataset")
    _for(d, "To know what is actually in the ground before measuring anything.")
    _rule(d, "The wastewater asset dataset holds a built network and a proposed one, told apart "
             "by the operational status field OP_STATUE and confirmed by four more fields that "
             "agree with it on every record: installation date, source, project code and remark. "
             "Built assets carry 1 January 2006, a drawing or CCTV source and project codes 5A-1 "
             "to 5A-5. Proposed ones carry no date, an asset-planning source, the project code "
             "SUREKHA and a remark naming them as large-urban-area networks. Filter on status "
             "first, then measure, and quote the two separately wherever either is quoted.")
    D.tab_caption(d, "The wastewater dataset inside the study area, split on status")
    D.table(d, ["Asset", "Built, features", "Built, length or size", "Proposed, features",
                "Proposed, length or size"],
            [[r[0], r[1], "**" + r[2] + "**", r[3], r[4]] for r in (gs, fm, te, ps, stp)],
            widths=[3.8, 2.4, 3.4, 2.6, 4.4], font=9)
    km_b = float(gs[2].split()[0].replace(",", ""))
    km_p = float(gs[4].split()[0].replace(",", ""))
    D.callout(d, "Never quote a combined length.",
              f"Adding the two gravity figures gives {F.fmt(km_b + km_p, 1)} km, a figure that "
              f"has been quoted for this dataset before and is wrong: {gs[4]} of it is a plan, "
              f"not a pipe. A proposed alignment has no capacity, no condition and no connection. "
              f"State built and proposed separately, every time.")
    _src(d, f"Measured in the project GIS against the {F.fmt(DF.BOUNDARY_KM2, 1)} km² boundary, "
            f"EPSG:32640 (2026-08-30); tender p201.")
    _ibri(d, f"Built: {gs[2]} of gravity sewer in {gs[1]} segments, {fm[2]} of force main, "
             f"{ps[2]} pumping station, a treatment plant of {stp[2]}, and no treated effluent "
             f"main. Proposed: {gs[4]} of gravity sewer, {fm[4]} of pumping main and {te[4]} of "
             f"treated effluent main.")
    _where(d, "W14/report/data_facts.py, WASTEWATER and CONSTRUCTED; field OP_STATUE in the "
              "received asset dataset.")

    # ------------------------------------------------------------- 17.2
    D.h(d, 2, "17.2   What the built records carry")
    _for(d, "To know what may be taken from the records and what must be surveyed.")
    _rule(d, "Nothing in the built records is used as a design value. The owner's own remark on "
             "every built record is that the data is not reliable and must be used only for "
             "reference. Levels, sizes and condition come from the survey and the CCTV.")
    _src(d, "Attribute count on the built gravity layer; remark field of the dataset.")
    od_txt = " and ".join(f"OD{k} on {f0(v)}" for k, v in
                          sorted(ab["od_values"].items(), key=lambda kv: -kv[1]))
    mat_txt = ", ".join(f"{k} on {f0(v)}" for k, v in ab["material"].items()) or "no segment"
    nom_txt = ("is empty on every one" if ab["nominal"] == 0 else f"is filled on {f0(ab['nominal'])}")
    _ibri(d, f"Of the {f0(ab['n'])} built gravity segments ({f1(ab['km'])} km), the nominal "
             f"diameter field {nom_txt}. Upstream invert and ground levels "
             f"are filled on {f0(ab['invert'])} ({f0(ab['invert'] / ab['n'] * 100)} %), an outside "
             f"diameter on {f0(ab['od'])} ({od_txt}), and a material ({mat_txt}). The segments "
             f"join {f0(ab['manholes'])} manholes by ID. The partly filled fields are leads for "
             f"the survey, not data: they may be design values rather than measurements, and the "
             f"remark covers them too.")
    D.callout(d, "Say it in those words.",
              "The received-data register reads that levels and diameters are not recorded. "
              "That is exact for the nominal diameter and loose for the rest: level and "
              "outside-diameter fields are filled on about two-thirds of the segments. The "
              "conclusion stands, because the owner disowns every value, but the reason is the "
              "remark, not an empty table.", fill="EAF1F8", colour=D.MID)
    _where(d, "W7/shp/EXISTING_SEWERLINE.shp, OP_STATUE = 1: fields N_DIAMETER, OUT_DIAMET, "
              "IN_DIAMETE, US_INVERT_, DS_INVERT_, US_GROUND_, MATERIAL, REMARKS, US_MHID and "
              f"DS_MHID. The file also holds {ab['proposed_in_file']} proposed segments "
              "(OP_STATUE = 0); filter before any count.")

    # ------------------------------------------------------------- 17.3
    D.h(d, 2, "17.3   What the built network is still good for")
    tier_ref = _table_ref(d, "Tier values in the engine outputs and the names used from now on",
                          "section 10.4")
    _for(d, "Calibrating the layout, not the hydraulics.")
    _rule(d, "Unreliable levels still carry a pattern. Read in bulk, the built network shows "
             "how the owner's own contractors laid a sewer on this ground, and a new design that "
             "departs far from that pattern should be able to say why. The manhole IDs encode "
             "the tier: 5A-2-TM-MH185 is a manhole on a trunk main and 5A-2-SM.2-MH391 is on "
             "sub main 2. The as-built uses the older engine's three words, trunk main, sub main "
             f"and lateral, and is read through the same mapping, {tier_ref}. Matching averages "
             "of gradient and depth says the hydraulics are plausible and nothing about whether "
             "the layout can be built; the hierarchy does.")
    _src(d, "Manhole IDs and US_MHID/DS_MHID traced inside the test boundary; tier words G203 "
            "p21; the tier mapping of section 10.4.")
    _ibri(d, "Inside the test boundary, 381 of the 419 street-sewer zones, 91 %, drain into "
             "another street sewer, and only about 16 connections reach the trunk main: 6 sub "
             "mains and 10 street sewers. A design with thirty things joining the trunk is "
             "laid unlike anything a contractor has built here.")
    D.callout(d, "Check the basis before quoting an as-built comparison.",
              f"The earlier gradient calibration (median 4.98 mm/m as built against 5.00 mm/m "
              f"designed) was measured on an extract of 3,322 segments and 188.6 km, which "
              f"includes the {ab['proposed_in_file']} proposed segments. Repeat it on "
              f"OP_STATUE = 1 before quoting it.")
    _where(d, "W8/docs/LEARNING_FROM_ASBUILT.md (hierarchy); W7/docs/CALIBRATION_vs_EXISTING.md "
              "(gradient, dual carriageway).")

    # ------------------------------------------------------------- 17.4
    D.h(d, 2, "17.4   Method")
    _for(d, "The order of work for the existing network.")
    _rule(d, "Seven steps.")
    D.numbered(d, "Separate built from proposed on the status field and confirm the split on the "
                  "date, source and project code before any quantity is taken.")
    D.numbered(d, "Survey cover and invert levels, diameters, materials, gradients, house "
                  "connections, riders, lifting and pumping stations and rising mains.")
    D.numbered(d, "Inspect condition by CCTV to NF EN 13508-2, early in design rather than at "
                  "detailed design.")
    D.numbered(d, "Build the as-built and GIS to NWS specification and upload it, subject to NWS "
                  "acceptance.")
    D.numbered(d, "Model the verified network against the design flows to find where capacity "
                  "runs out, and when.")
    D.numbered(d, "Classify each asset: adequate and kept; adequate after rehabilitation; or "
                  "replaced.")
    D.numbered(d, "Design the integration points between old and new networks, and between the "
                  "old plant and the new one.")
    _src(d, "Tender p201 (layout inaccurate; as-built and GIS in scope; integrate, upgrade and "
            "rehabilitate); scope p12 and p15 (as-built content, upload); scope p14 (integrity of "
            "existing networks against the identified flows); G203 p197 (CCTV to NF EN 13508-2, "
            "early).")
    lsd = _register("Lifting station details")
    _ibri(d, f"The survey starts from {f0(ab['manholes'])} manholes on {f1(ab['km'])} km of built "
             f"gravity sewer, plus {fm[2]} of force main and its station, for which the register "
             f"reads: {lsd[1].lower()}.")
    _where(d, "W14/report/data_facts.py, REGISTER; W7/shp/EXISTING_SEWERLINE.shp.")

    # ------------------------------------------------------------- 17.5
    D.h(d, 2, "17.5   What the assessment must produce")
    _for(d, "To carry the existing network into the options on equal terms with the new works.")
    _rule(d, "A hydraulic verdict on every existing asset against the design flows; a "
             "rehabilitation and replacement schedule with quantities; the integration design; "
             "and the cost of all of it, carried into the options appraisal beside the new "
             "works. An option that reuses more of the old network is cheaper to build and may "
             "cost more to run, and only the whole-life comparison over 25 years at 5 % settles "
             "it. A costed do-nothing option is the baseline.")
    _src(d, "Scope p14 and p25 (integration, hydraulic assessment and rehabilitation of the "
            "existing systems); G201 p57 and pp 95 to 96 (25 years, 5 %). Project rule: "
            "financial method (engineer, 2026-09-01).")
    cap = float(stp[2].split()[0].replace(",", ""))
    _ibri(d, f"None of the verdicts can be computed yet: with no reliable diameter or level, the "
             f"capacity of the {f1(ab['km'])} km is unknown until the survey reports. The scale "
             f"of the question is known. The existing plant's nominal {stp[2]} is "
             f"{f1(cap / tot['q_today'] * 100)} % of the {f0(tot['q_today'])} m³/d the study area "
             f"generates today, and the study area reaches {f0(tot['q_ult'])} m³/d at saturation "
             f"in {tot['ultimate']}.")
    _where(d, "W14/report/data_facts.py, WASTEWATER; facts_w14.totals().")

    # ------------------------------------------------------------- 17.6
    D.h(d, 2, "17.6   Check it yourself")
    D.numbered(d, "Filter the dataset on OP_STATUE and confirm every built record carries "
                  "1/1/2006, a dwg or cctv source, a 5A project code and the reference-only "
                  "remark.")
    D.numbered(d, "Measure built and proposed lengths separately in EPSG:32640 inside the "
                  "boundary and compare them with the table in 17.1.")
    D.numbered(d, "Count the filled diameter and level fields on the built segments.")
    D.numbered(d, "Before quoting any comparison with the as-built, confirm it was measured on "
                  "OP_STATUE = 1 alone.")
    D.numbered(d, "Trace a few TM and SM manhole IDs through US_MHID and DS_MHID and draw the "
                  "hierarchy they encode.")
