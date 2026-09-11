import os, sys; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report")); import doc as D; import omml as M; import facts_w14 as F; UP, R = M.up, M.r; IMG = os.path.join(HERE, "img")
"""T04 chapters 18 to 20: treatment plant flows and loads, treated effluent, sludge.

Every Ibri number is read from facts_w14 or W14/analysis/design_flows.json and
computed here; every guideline value carries its page, checked against the PDF
in Data/ (PAM-GUD-203 pp 65-74, 130, 135-137, 151, 155; PAM-GUD-201 pp 33, 53,
57, 72-78) on 2026-09-11.
"""
import json
import math
from functools import lru_cache

REPO = os.path.dirname(os.path.dirname(HERE))
JSON_PATH = os.path.join(REPO, "W14", "analysis", "design_flows.json")

# guideline constants, each with its page
BOD_PC, TSS_PC = 60.0, 80.0          # g per person per day, G203-p74
COD_BOD_LO, COD_BOD_HI = 1.8, 2.2    # G203-p74
PF_BOD_ML, PF_TKN_ML = 1.2, 1.5      # medium-large STP, G203-p74
TKN_LO, TKN_HI = 60.0, 80.0          # mg/l, G203-p67 Table 30
LARGE = 20000.0                      # m3/d, G203-p65
TSE_RATIO, TSE_LOSS = 0.95, 0.10     # G201-p73, G201-p76
SLUDGE = 0.25                        # kg/m3, G201-p78
INFIL_M3_KM = 0.72                   # 720 l/d/km, G201-p72
N_LINES = 6                          # illustration only (Section 18.8)


# ------------------------------------------------------------------ helpers
def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)


def _part(d, lead, text):
    return D.rich(d, (lead, {"bold": True, "colour": D.MID}), (text, {}))


def _small(d, lead, text):
    return D.rich(d, (lead, {"bold": True, "size": 9, "colour": D.GREY}),
                  (text, {"size": 9, "colour": D.GREY}), space_after=8)


def _source(d, text):
    return _small(d, "Source. ", text)


def _where(d, text):
    return _small(d, "Where it lives. ", text)


def _gap(d):
    D.p(d, "", space_after=2)


def merrimack(q_m3d):
    """Qpdf = 2.65 Qadf^0.879, both in Ml/d (G201-p71); returned in m3/d."""
    return 2.65 * (q_m3d / 1000.0) ** 0.879 * 1000.0


def peltier(q_m3d):
    """PF = 1.5 + 1/sqrt(Qm), Qm in l/s (G201-p72)."""
    return 1.5 + 1.0 / math.sqrt(q_m3d / 86.4)


@lru_cache(None)
def _n():
    """Every Ibri number the three chapters quote, computed once from F and the JSON."""
    t = F.totals()
    with open(JSON_PATH, encoding="utf-8") as fh:
        J = json.load(fh)
    cols, _ = F.five_year_rows("q")
    years5 = [int(c) for c in cols[1:-1]]
    ult = t["ultimate"]
    m = float(J["rules"]["stp_margin"])
    conn = float(J["rules"]["connection_ratio_2030"])
    open_y = int(J["rules"]["opening_year"])
    low = float(J["low_case_2030_m3d"])
    q, pop = t["q"], t["pop"]
    q_ult, pop_ult = t["q_ult"], t["pop_ult"]
    design = {y: q[y] * (1 + m) for y in t["years"]}
    line = q_ult * (1 + m) / N_LINES
    # the k-th line is needed in the first year the design flow passes (k - 1) lines
    need = {}
    for k in range(1, N_LINES + 1):
        need[k] = next((y for y in t["years"] if design[y] > (k - 1) * line + 1e-6), None)
    return dict(t=t, J=J, years5=years5, ult=ult, m=m, conn=conn, open_y=open_y, low=low, q=q, pop=pop,
                q_ult=q_ult, pop_ult=pop_ult, design=design, line=line, need=need,
                json_margin=float(J["stp_ultimate_with_margin_m3d"]), infil=float(J["rules"]["infiltration_l_per_day_per_km"]))


# ============================================================== 18. PLANT
def c18_plant(d):
    n = _n(); fmt = F.fmt
    ult, m, q, pop = n["ult"], n["m"], n["q"], n["pop"]
    y0, yo = F.BASE_YEAR, n["open_y"]
    q_ult, pop_ult = n["q_ult"], n["pop_ult"]
    d_ult, d_open = n["design"][ult], n["design"][yo]

    D.h(d, 1, "18   Treatment plant flows and loads", page_break=True)
    D.p(d, "The network is sized pipe by pipe on the saturation flow and laid once. The plant is sized "
           "differently. It takes the flow of the whole catchment year by year, with a margin, and the mass "
           "of organic matter and solids that flow carries, and it is built in steps that follow the "
           "series. This chapter turns the settlement totals into the plant flows, the loads, the size "
           "category and a phasing, and says where each rule comes from.")

    # ---------------------------------------------------------------- 18.1
    D.h(d, 2, "18.1   The incoming flow")
    _part(d, "What it is for. ", "The incoming flow is the average flow the plant must treat. The peak flows, "
          "the loads per cubic metre and the capacity of every phase are built on it.")
    _part(d, "The rule. ", "The average sewage flow of the served catchment, plus infiltration, plus a ten per "
          "cent design margin on the sum.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("in")), M.EQ, M.delim(M.seq(R("1"), M.PLUS, R("m"))), M.TIMES,
                       M.delim(M.seq(M.sub(R("Q"), UP("adf")), M.PLUS, M.sub(R("Q"), UP("inf"))))), number=eq)
    eq2 = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("inf")), M.EQ, R("0.72"), M.TIMES, M.sub(R("L"), UP("new")),
                       M.PLUS, R("0.10"), M.TIMES, M.sub(R("Q"), UP("adf,existing"))), number=eq2)
    _params(d, [
        ["Q in", "incoming flow, the plant's design average flow", "m³/d"],
        ["Q adf", "average sewage flow of the served catchment in the year, 100 % connected", "m³/d"],
        ["Q inf", "infiltration", "m³/d"],
        ["m", "design margin, 0.10", "—"],
        ["L new", "length of new sewer draining to the plant (720 l/d per km = 0.72 m³/d per km)", "km"],
        ["Q adf,existing", "the part of Q adf that drains through the existing network", "m³/d"]])
    D.p(d, "Tanker deliveries join the sum when their records are received (Section 18.4). The margin is "
           "applied to the sewage and the infiltration together, because the guideline says it covers "
           "fluctuations in population, consumption and infiltration alike. It is applied on top of duty and "
           "standby equipment and is never netted against them.")
    D.p(d, "The margin carries different force in the two guidelines. The general guideline says a ten per cent "
           "margin should be applied when designing new plants. The wastewater guideline, in G203 Table 29, "
           "says incoming flows shall be calculated with it. The stronger wording governs, so the margin is always "
           "applied.")
    D.p(d, "Infiltration also has two rates. New sewers take 720 l/d per kilometre. An existing network "
           "inland, outside the influence of groundwater, takes ten per cent of its wastewater flow. How much "
           "of the catchment drains through the existing network will be known from the as-built survey.")
    _source(d, "G203-p65 §10.2.2.1 Table 29 (incoming flows, \"shall\"); G201-p73 §7.4.5 (margin \"should be "
               "applied when designing new STPs\", \"over and above any redundancies\"); G201-p72 §7.4.3 "
               "(720 l/d/km new, 10 % existing inland); G203-p65 (capacity on the per-capita consumption of the "
               "Integrated Master Plan, which is the 164 l/d of G201-p60 Table 11).")
    _part(d, "Worked for Ibri. ", f"The 25 settlements generate {fmt(q_ult)} m³/d at saturation in {ult}. With "
          f"the margin, the design average flow is {fmt(q_ult)} × {1 + m:.2f} = {fmt(d_ult)} m³/d, which is the "
          f"figure the design-flow file carries ({fmt(n['json_margin'], 1)} m³/d). Infiltration is not yet in it, "
          f"because the network for the whole study area has not been laid. Its scale can be judged now. "
          f"Every 100 km of new sewer adds {fmt(100 * INFIL_M3_KM)} m³/d, and it takes "
          f"{fmt(0.01 * q_ult / INFIL_M3_KM)} km of new sewer before infiltration reaches one per cent of the "
          f"saturation flow.")
    _where(d, "Annual flow per settlement: W14/py/growth_by_settlement.py writes "
              "W14/analysis/W14_growth_by_settlement.xlsx, sheets \"Qadf by year m3d\" and \"Five-year Qadf\", read "
              "by facts_w14.totals(). Margin: W14/py/make_design_flows.py, constant MARGIN, key "
              "stp_ultimate_with_margin_m3d in W14/analysis/design_flows.json. Infiltration: added per pipe by "
              "length in the network engine (JSON rule infiltration_applies), summed at the plant.")
    D.p(d, "Tutorial T01 carried an ultimate flow of about 49,700 m³/d from the Inception Report. That figure "
           "rested on the connected population and a single occupancy rate, and the counted saturation flow "
           "above replaces it.", italic=True, size=9.5)

    # ---------------------------------------------------------------- 18.2
    D.h(d, 2, "18.2   The plant flows and what each one sizes")
    _part(d, "What it is for. ", "A plant is not sized on one flow. Its parts respond to different time "
          "scales, and the guideline names the flow for each.")
    D.tab_caption(d, "The design flows of a treatment plant")
    D.table(d, ["Flow", "Definition", "What it sizes", "Page"], [
        ["**Average annual flow (AAF)**", "the average of the daily volumes over a continuous 12 months",
         "biological treatment, with the design inlet load", "G203-p65, p66"],
        ["Maximum daily flow (MDF)", "the largest volume in a continuous 24 hours",
         "no rule attached, and no factor given in either guideline", "G203-p65"],
        ["**Peak hourly flow (PHF), also written QPDF**", "the largest volume in one hour",
         "hydraulic pass-through process structures", "G203-p65, p66"],
        ["Design peak instantaneous flow", "the instantaneous maximum flow rate",
         "defined only; no method or factor given", "G203-p66"],
    ], widths=[4.0, 5.2, 4.9, 2.4], font=9)
    _gap(d)
    _part(d, "The rule. ", "Except where the specification or NWS says otherwise, pass-through structures are "
          "sized on the peak hourly flow and biological treatment on the average annual flow and the design "
          "inlet load. Both the hydraulic and the load design include the recycled liquors and the received "
          "tanker volumes. The guideline gives the peak hourly flow the symbol QPDF, which is the peak flow of "
          "the general guideline. The whole catchment holds far more than 100 properties, so the Merrimack "
          "formula is the one to use.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("pdf")), M.EQ, R("2.65"), M.TIMES,
                       M.sup(M.sub(R("Q"), UP("adf")), R("0.879")),
                       R("     "), M.sub(R("P"), UP("f")), M.EQ,
                       M.frac(M.sub(R("Q"), UP("pdf")), M.sub(R("Q"), UP("adf")))), number=eq)
    _params(d, [
        ["Q pdf", "peak flow, taken as the plant's peak hourly flow", "Ml/d"],
        ["Q adf", "average daily flow of the catchment", "Ml/d"],
        ["P f", "peak factor", "—"]])
    D.p(d, "The margin applies to the peak as it does to the average, since both come from the same "
           "accumulated flow. Infiltration is added after peaking, without a daily pattern. The guideline does "
           "not state that order; it is the reading used here and is to be confirmed with NWS.")
    D.p(d, "The maximum daily flow cannot be computed from the guidelines, because neither gives a factor for it. "
           "It is read from a year of daily inflow records at the existing works. Until those arrive, it is not "
           "quoted.")
    _source(d, "G203-p65 Table 29 (the four definitions, \"PHF or QPDF\"); G203-p66 §10.2.2.1 (\"Hydraulic "
               "pass-through process structures are to be sized based on peak hourly flow\", \"Biological "
               "treatment systems ... based on the AAF and the design inlet load\", recycled liquors and tanker "
               "volumes \"shall\" be included); G201-p71 §7.4.2 (Merrimack, \"over 100 properties\"); G201-p72 "
               "(Peltier alternative, Qm in l/s; hourly factor \"recommended\" not above 5.0). Order of "
               "infiltration and peaking: _BRAIN/02_DESIGN_CRITERIA.md §11.4, GAP-23.")
    q_ml = q_ult / 1000.0
    pk_ult, pk_open = merrimack(q_ult), merrimack(q[yo])
    pf_ult, pf_open = pk_ult / q_ult, pk_open / q[yo]
    pel = peltier(q_ult)
    _part(d, "Worked for Ibri. ", f"At saturation Q adf = {q_ml:.3f} Ml/d, so Q pdf = 2.65 × {q_ml:.3f}^0.879 = "
          f"{pk_ult / 1000:.2f} Ml/d and the peak factor is {pf_ult:.3f}. With the margin, the design peak hourly "
          f"flow is {fmt(pk_ult * (1 + m))} m³/d. At opening in {yo} the factor is higher, {pf_open:.3f}, because "
          f"the formula peaks a smaller flow harder. The Peltier alternative gives {pel:.3f} at saturation "
          f"(Qm = {fmt(q_ult / 86.4, 1)} l/s), within {abs(pf_ult / pel - 1) * 100:.0f} per cent of Merrimack. At "
          f"plant scale the choice of formula barely matters, and the 5.0 ceiling never comes into play.")
    _where(d, "The same formulae run per pipe in the network engine (design_flows.json rules "
              "peak_over_100_properties and peak_100_properties_or_fewer). The plant peak is computed in this "
              "chapter from facts_w14.totals(); no pipeline script writes it yet.")

    # ---------------------------------------------------------------- 18.3
    D.h(d, 2, "18.3   The plant flows by year")
    _part(d, "What it is for. ", "The series says when capacity is needed. The network is laid once for "
          "saturation; the plant is built in step with this table.")
    _part(d, "The rule. ", "Each year's average flow is the sum of the 25 settlements, every metered property "
          "counted as connected. The design average and the design peak each carry the margin. The plant, like "
          "the pipes, is sized on the full load, because under-estimating the total undersizes the plant. The "
          "connection ratio is used only where over-estimating is the risk.")
    _source(d, "G201-p73 §7.4.4 (coverage \"100% by the end of the planning period\"); project rule, "
               "Concept Design Report R2 §10.1 row \"Connection to the sewer\" (W14/report/rpt_cd.py) and the "
               "directional-accuracy rule in _BRAIN/02_DESIGN_CRITERIA.md §11.1.")
    rows = []
    for y in n["years5"]:
        pk = merrimack(q[y])
        rows.append([f"**{y}**" if y in (yo, ult) else str(y), fmt(pop[y]), fmt(q[y]), fmt(q[y] * (1 + m)),
                     f"{pk / q[y]:.2f}", fmt(pk * (1 + m))])
    D.tab_caption(d, "Plant flows at five-year intervals to saturation, 100 % connected")
    D.table(d, ["Year", "People", "AAF, m³/d", "AAF + 10 %, m³/d", "Peak factor", "PHF + 10 %, m³/d"],
            rows, widths=[2.0, 2.9, 2.9, 3.1, 2.3, 3.4], font=9, align_right={1, 2, 3, 4, 5})
    _gap(d)
    D.picture(d, os.path.join(IMG, "C09_flow.png"), 15.0)
    D.fig_caption(d, "Average sewage flow of the study area by year, from today's plots and from the empty plots "
                     "as they fill. The plant is phased on this curve.")
    _part(d, "Worked for Ibri. ", f"The design average rises from {fmt(d_open)} m³/d at opening in {yo} to "
          f"{fmt(d_ult)} m³/d at saturation in {ult}, a factor of {d_ult / d_open:.2f}. If connection stood at the "
          f"Inception Report's {n['conn']:.2f} at opening, the network would deliver {fmt(n['low'])} m³/d in {yo}. "
          f"That is not a sizing figure. It is the load the first phase must treat stably, and the flow for the "
          f"network's early self-cleansing check.")
    _where(d, "facts_w14.totals() and facts_w14.five_year_rows(\"q\"); low case: design_flows.json key "
              "low_case_2030_m3d (W14/py/make_design_flows.py, CONNECT_2030). Chart: W14/report/charts_w14.py, "
              "C09_flow.")

    # ---------------------------------------------------------------- 18.4
    D.h(d, 2, "18.4   Tankers and septage reception")
    _part(d, "What it is for. ", "Sewage delivered by road bypasses the network and arrives at the plant. The "
          "guideline requires it in both the hydraulic and the load design, and it is much stronger than "
          "network sewage.")
    _part(d, "The rule. ", "Received tanker volumes are included in the flows and loads. Septage and "
          "leachate are accepted only through four provisions:")
    D.bullet(d, "a dedicated tanker discharge station with screening and oil and grease removal;", lead="Reception. ")
    D.bullet(d, "a flow equalisation tank for tanker discharge alone, so the main process sees no shock load;",
             lead="Equalisation. ")
    D.bullet(d, "an emergency lagoon of 48 to 72 hours of plant capacity, only in specific cases and under NWS "
                "requirement and approval, pumped back to the inlet when capacity allows;", lead="Lagoon. ")
    D.bullet(d, "sampling before acceptance, operating procedures, records for traceability, and contracts "
                "with tanker operators that fix acceptable characteristics.", lead="Operation. ")
    D.p(d, "Where the COD to BOD ratio of an influent is above 2.2, the guideline calls it not effectively "
           "treatable by biological means, and a separate line for high-strength wastewater is required if the "
           "volumes are significant. The guideline does not say what significant means.")
    t_tank = D.tab_caption(d, "Tankered sewage against network sewage, design values in mg/l")
    D.table(d, ["Parameter", "Tanker, average to maximum (G203 Table 31)", "Network sewage (G203 Table 30)"], [
        ["BOD₅", "350 – 1,050", "350 – 400"],
        ["COD", "1,350 – 5,000", "700 – 900"],
        ["Total suspended solids", "900 – 4,300", "400 – 500"],
        ["Total Kjeldahl nitrogen as N", "115 – 265", "60 – 80"],
        ["Ammonia nitrogen as N", "70 – 125", "40 – 50"],
        ["Total phosphorus", "16 – 35", "10 – 15"],
        ["Fat, oil and grease", "22 – 200", "50 – 100"],
    ], widths=[5.2, 6.0, 5.3], font=9)
    _gap(d)
    D.p(d, "G203 Table 31 is measured at Qurayyat plant from 2021 to 2024 and is a reference, not a design value "
           "for Ibri. Nor is the company-wide observation that yellow tankers brought about 17 per cent of the "
           "flow reaching NWS plants in 2024. It is a network average, and it says nothing about Ibri.")
    _source(d, "G203-p66 (tanker volumes \"shall\" be included); G203-p73 §10.3.1 (the four provisions, "
               "\"must be accounted for\"); G203-p74 (COD/BOD above 2.2, separate line \"if volumes are "
               "significant\"); G203-p67 Table 30, p68 Table 31; G201-p73 §7.4.4 (17 %, \"pollution loads of "
               "tankers are higher\").")
    bod_c_ult = pop_ult * BOD_PC / q_ult
    tss_c_ult = pop_ult * TSS_PC / q_ult
    _part(d, "Worked for Ibri. ", f"At the G203 Table 31 averages (Table {t_tank} here) the COD to BOD ratio of tankered sewage is "
          f"1,350 / 350 = {1350 / 350:.2f}, above the 2.2 limit. Every 1,000 m³/d of it brings 350 kg/d of BOD, "
          f"1,350 kg/d of COD and 900 kg/d of suspended solids. The same volume of Ibri network sewage at "
          f"saturation carries about {fmt(bod_c_ult)} kg of BOD, {fmt(COD_BOD_LO * bod_c_ult)} to "
          f"{fmt(COD_BOD_HI * bod_c_ult)} kg of COD and {fmt(tss_c_ult)} kg of suspended solids "
          f"(Section 18.5). An average tanker matches the network in BOD. It is the COD and the solids that it "
          f"adds out of proportion, and the G203 Table 31 maxima run from {1050 / 350:.0f} to nearly {4300 / 900:.0f} "
          f"times the averages. No tanker volume is in any "
          f"flow or load in this tutorial. The delivery records at the existing works (volume, origin and "
          f"strength) are requested, and the flow and load are added when they arrive. Known sources outside the "
          f"network include the Madayn industrial city and the power-station camp.")
    _where(d, "design_flows.json rule tankers (\"pending: ... not in any flow\"); Concept Design Report R2 §10.1, "
              "§16 and §26.1 (W14/report/rpt_cd.py, rpt_ef.py); _BRAIN/05_GAPS.md GAP-19 (camps tankered to the "
              "works) and GAP-20 (Ibri's own tanker share).")
    D.p(d, "Tutorial T01 wrote a tanker term into the plant inflow. It stays in the rule, but it carries no "
           "number until the delivery records are held.", italic=True, size=9.5)

    # ---------------------------------------------------------------- 18.5
    D.h(d, 2, "18.5   Organic loads")
    _part(d, "What it is for. ", "The biology is sized on the mass of organic matter and solids, not on the "
          "volume. A plant with the right flow and the wrong load will not meet the effluent standard.")
    _part(d, "The rule. ", "The load is the population times a per-person contribution. The concentration "
          "follows by dividing by the flow. The second relation is a mass balance that the guideline does not "
          "print.")
    eq = D.next_eq()
    M.display(d, M.seq(R("L"), M.EQ, M.frac(M.seq(R("P"), M.TIMES, R("l")), R("1000")),
                       R("     "), R("C"), M.EQ, M.frac(M.seq(R("1000"), M.TIMES, R("L")), R("Q"))), number=eq)
    _params(d, [
        ["L", "load of the determinand", "kg/d"],
        ["P", "resident population served", "persons"],
        ["l", "per-person contribution: at least 60 for BOD₅, 80 for suspended solids", "g/person/d"],
        ["C", "concentration", "mg/l"],
        ["Q", "average annual flow", "m³/d"]])
    D.p(d, "The per-person figures are floors, not typical values; the guideline's words are \"at least\". "
           "For a new plant, loads are projected from actual waste load data where it exists and compared "
           "with the per-person figures. For an existing works that is upgraded or extended, the organic "
           "design is based on the measured strength from the Client's laboratory, with an increment for "
           "growth. Ibri has an existing works on the same catchment, so its laboratory records govern once "
           "they are received. The 60 g and 80 g are then the check, not the basis.")
    D.p(d, "The margin of Section 18.1 is stated for flow. Whether it also applies to load is not stated, so the "
           "loads here carry none. The organic peak factors of Section 18.6 are the guideline's allowance "
           "on load.")
    _source(d, "G203-p74 §10.3.1 (\"at least 60 g of BOD5 per capita per day and 80 g of suspended solids\"; "
               "existing works \"shall be based upon the actual strength ... from the Client's laboratory\"; LIMS); "
               "G203-p73 (new works: projections from actual data, compared with per-capita contribution); "
               "G203-p67 Table 30 (network sewage ranges, used only after agreement with NWS).")
    rows = []
    for y in (y0, yo, 2055, ult):
        bod, tss = pop[y] * BOD_PC / 1000, pop[y] * TSS_PC / 1000
        rows.append([str(y), fmt(pop[y]), fmt(q[y]), fmt(bod), fmt(tss), fmt(bod * 1000 / q[y]),
                     fmt(tss * 1000 / q[y])])
    D.tab_caption(d, "Organic and solids loads at 60 g BOD and 80 g suspended solids per person")
    D.table(d, ["Year", "People", "AAF, m³/d", "BOD, kg/d", "TSS, kg/d", "BOD, mg/l", "TSS, mg/l"],
            rows, widths=[1.8, 2.5, 2.5, 2.4, 2.4, 2.4, 2.5], font=9, align_right={1, 2, 3, 4, 5, 6})
    _gap(d)
    _part(d, "Worked for Ibri. ", f"At saturation {fmt(pop_ult)} people × 60 g = {fmt(pop_ult * BOD_PC / 1000)} "
          f"kg/d of BOD, and × 80 g = {fmt(pop_ult * TSS_PC / 1000)} kg/d of suspended solids. Over "
          f"{fmt(q_ult)} m³/d that is {fmt(bod_c_ult)} mg/l of BOD and {fmt(tss_c_ult)} mg/l of solids, at the "
          f"lower edge of the G203 Table 30 ranges of 350 to 400 and 400 to 500 mg/l (Table {t_tank} here). It sits low for a reason. The "
          f"flow includes the non-domestic, governmental and industrial sewage, while the per-person load counts "
          f"residents only. The concentration is the cross-check on the whole chain. A figure near 200 mg/l would "
          f"mean the flow per person had been overstated.")
    _where(d, "Computed in this chapter from facts_w14.totals() (\"pop\" and \"q\"); no pipeline script carries "
              "plant loads yet. The laboratory (LIMS) records of the existing works are a data request.")

    # ---------------------------------------------------------------- 18.6
    D.h(d, 2, "18.6   COD, nitrogen and the organic peak factors")
    _part(d, "What it is for. ", "COD sets the oxygen demand and shows whether the influent is biologically "
          "treatable. The peak loads set the aeration capacity.")
    _part(d, "The rule. ", "Domestic COD lies between 1.8 and 2.2 times BOD. The peak load is the average "
          "load times a peak factor that depends on the plant size.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("L"), UP("COD")), M.EQ, R("r"), M.TIMES, M.sub(R("L"), UP("BOD")),
                       R("     "), M.sub(R("L"), UP("peak")), M.EQ, M.sub(R("f"), UP("L")), M.TIMES, R("L")),
              number=eq)
    _params(d, [
        ["L COD, L BOD", "average COD and BOD loads", "kg/d"],
        ["r", "COD to BOD ratio, 1.8 to 2.2 for domestic sewage", "—"],
        ["L peak", "peak load for aeration design", "kg/d"],
        ["f L", "organic peak factor: BOD and COD 1.5 small, 1.2 medium to large; TKN 2.0 small, 1.5 medium to "
                "large", "—"]])
    D.p(d, "The guideline gives no per-person figure for nitrogen. The G203 Table 30 range of 60 to 80 mg/l of "
           f"total Kjeldahl nitrogen (Table {t_tank} here), applied to the flow, is the only guideline basis. It may be used only after "
           "agreement with NWS. Where surge loads are critical, equalisation of flow and load is considered.")
    _source(d, "G203-p74 §10.3.1 (ratio 1.8 - 2.2; peak factors \"For small STPs = 1.5; For medium-large "
               "STPs = 1.2\", TKN \"2\" and \"1.5\"; equalisation); G203-p67 Table 30 (TKN 60 - 80 mg/l).")
    bod_ult = pop_ult * BOD_PC / 1000
    tkn_lo, tkn_hi = q_ult * TKN_LO / 1000, q_ult * TKN_HI / 1000
    _part(d, "Worked for Ibri. ", f"The plant is large (Section 18.7), so the medium-to-large factors apply. At "
          f"saturation, COD is {COD_BOD_LO} to {COD_BOD_HI} × {fmt(bod_ult)} = {fmt(COD_BOD_LO * bod_ult)} to "
          f"{fmt(COD_BOD_HI * bod_ult)} kg/d. The peak BOD load is {PF_BOD_ML} × {fmt(bod_ult)} = "
          f"{fmt(PF_BOD_ML * bod_ult)} kg/d, and the peak COD load is {fmt(PF_BOD_ML * COD_BOD_LO * bod_ult)} to "
          f"{fmt(PF_BOD_ML * COD_BOD_HI * bod_ult)} kg/d. Nitrogen on G203 Table 30 is {fmt(tkn_lo)} to {fmt(tkn_hi)} "
          f"kg/d of TKN, and at the factor of {PF_TKN_ML} the peak is {fmt(PF_TKN_ML * tkn_lo)} to "
          f"{fmt(PF_TKN_ML * tkn_hi)} kg/d. Nitrogen, not BOD, drives the process choice (Section 19.4).")
    _where(d, "Computed in this chapter from facts_w14.totals(); to be replaced by the measured strength when the "
              "laboratory records are received.")

    # ---------------------------------------------------------------- 18.7
    D.h(d, 2, "18.7   The size category, and why phasing is the pivotal decision")
    _part(d, "What it is for. ", "The category decides which rules apply to the plant. On this project it also "
          "decides whose scope the plant is.")
    D.tab_caption(d, "Treatment plant size categories")
    D.table(d, ["Category", "Capacity"], [
        ["Small", "below 500 m³/d"], ["Medium", "500 m³/d up to 20,000 m³/d"],
        ["**Large**", "**20,000 m³/d and above**"]], widths=[5.0, 11.5], font=9.5)
    _gap(d)
    _part(d, "The rule. ", "A large plant is held to four rules that a medium plant is not:")
    D.bullet(d, "computational fluid dynamics modelling is carried out unless the Terms of Reference say "
                "otherwise;", lead="Modelling. ")
    D.bullet(d, "the chlorine contact tank is replaced by a treated effluent storage tank that does its job "
                "(Section 19.5);", lead="Disinfection. ")
    D.bullet(d, "the residential buffer is set by odour dispersion modelling, between 300 and 1,000 m to the "
                "5 odour-unit contour, instead of a flat 500 m;", lead="Buffer. ")
    D.bullet(d, "the organic peak factors are 1.2 for BOD and COD and 1.5 for nitrogen (Section 18.6).",
             lead="Peak factors. ")
    D.p(d, "The Terms of Reference add a fifth rule, and it is the one that matters commercially. The preliminary "
           "design and the construction tender of the new plant are in the consultant's scope only if the "
           "design capacity of its Phase I is below 20,000 m³/d. Above that, they are not part of the scope "
           "unless NWS instructs otherwise.")
    _source(d, "G203-p65 §10.2.1 (categories); G203-p66 (CFD for large plants); G203-p135 §10.6.7.4 (TSE storage "
               "tank for large plants); G201-p43-44 Table 8 (buffer); G203-p74 (peak factors); Terms of Reference, "
               "Data/scope.pdf, PDF pages 3, 4, 5, 6, 16, 22, 27 and 30 (Phase I below 20,000 m³/d).")
    D.picture(d, os.path.join(IMG, "F8_stp.png"), 13.5)
    D.fig_caption(d, "Sizing and phasing the plant: the design flow and the loads set the category and the "
                     "process, and the category sets the buffer and the modelling.")
    need_open = d_open - LARGE
    d_15 = n["design"][yo + 15]
    low_d = n["low"] * (1 + m)
    _part(d, "Worked for Ibri. ", f"The study area already generates {fmt(q[y0])} m³/d in {y0}, above the "
          f"large-plant threshold before any margin. At opening in {yo} the full design average is "
          f"{fmt(d_open)} m³/d. For Phase I of a new plant to stay below 20,000 m³/d at opening, the existing "
          f"works would have to go on treating at least {fmt(need_open)} m³/d. With a fifteen-year horizon to "
          f"{yo + 15}, the design average is {fmt(d_15)} m³/d and the existing works would have to keep "
          f"{fmt(d_15 - LARGE)} m³/d. The capacity of the existing works is not yet known. Now take the Inception "
          f"connection ratio instead: {fmt(n['low'])} × {1 + m:.2f} = {fmt(low_d)} m³/d, below the threshold. "
          f"The category of Phase I therefore flips on two things nobody has measured yet: the connection path "
          f"and the capacity left in the existing works. That is why phasing, not process, is the pivotal plant "
          f"decision. The position adopted sizes on the full load; the choice of Phase I is NWS's.")
    _where(d, "facts_w14.totals(); _BRAIN/05_GAPS.md GAP-7 (existing works capacity and inlet level, requested "
              "from NWS); _BRAIN/07_PROJECT_STATE.md, project summary (phasing as the pivotal decision).")

    # ---------------------------------------------------------------- 18.8
    D.h(d, 2, "18.8   Phasing, worked")
    _part(d, "What it is for. ", "Capacity follows demand. A plant built for saturation on opening day would run "
          "at a fraction of its load for decades, with the capital spent before the sewage arrives and a "
          "biological process that is hard to keep stable.")
    _part(d, "The rule. ", "The plant is designed for a horizon of at least fifteen years. The planning life of "
          "twenty-five years is the ultimate design capacity and the period of the cost comparison. The plant "
          "is built as several process lines that add capacity for later horizons or phases. The number of "
          "lines in any year follows from the design average flow and the capacity of one line.")
    eq = D.next_eq()
    M.display(d, M.seq(R("N"), M.delim(R("y")), M.EQ,
                       M.delim(M.frac(M.seq(M.delim(M.seq(R("1"), M.PLUS, R("m"))), M.TIMES,
                                            M.sub(R("Q"), UP("adf")), M.delim(R("y"))),
                                      M.sub(R("C"), UP("line"))), "⌈", "⌉")), number=eq)
    _params(d, [
        ["N(y)", "number of duty process lines needed in year y", "—"],
        ["Q adf(y)", "average sewage flow in year y, 100 % connected", "m³/d"],
        ["m", "design margin, 0.10", "—"],
        ["C line", "treatment capacity of one line", "m³/d"]])
    D.p(d, "A modular plant adds one element on top: N elements meet the average day and N + 1 meet the peak. "
           "The margin sits on top of that standby element and is never counted as part of it. The guideline "
           "does not say whether a single phase may be shorter than fifteen years when the plant as a whole "
           "meets the horizon. It is read here as applying to the plant, with phases as the lines within it. "
           "This is to be confirmed with NWS.")
    _source(d, "G203-p65 §10.2.1 (horizon \"at least 15 years\"); G201-p57 §7.1 (planning life 25 years, "
               "\"ultimate design capacity\" and NPV period); G201-p53 §6.6.2 (\"shall be designed using several "
               "process lines\"); G201-p33 §4.3 (N + 1, \"should\"); G201-p73 §7.4.5 (margin over and above "
               "redundancy).")
    line = n["line"]; need = n["need"]
    rows = []
    for k in range(1, N_LINES + 1):
        y = need[k]
        when = f"already by {y0}" if y is not None and y <= y0 else str(y)
        rows.append([str(k), fmt(k * line), when, fmt(n["q"][y]) if y else "", fmt(n["design"][y]) if y else ""])
    D.tab_caption(d, f"Illustration: {N_LINES} equal lines of {fmt(line)} m³/d, and the year each is first needed")
    D.table(d, ["Line", "Capacity with this line, m³/d", "First needed", "AAF that year, m³/d",
                "AAF + 10 % that year, m³/d"], rows, widths=[1.6, 4.0, 3.2, 3.6, 4.1], font=9,
            align_right={1, 3, 4})
    _gap(d)
    n_open = math.ceil(d_open / line)
    n_15 = math.ceil(d_15 / line)
    n_25 = math.ceil(n["design"][yo + 25] / line)
    _part(d, "Worked for Ibri. ", f"Divide the saturation design average of {fmt(d_ult)} m³/d into {N_LINES} "
          f"equal lines of {fmt(line)} m³/d. A line is first needed in the year the design average passes the "
          f"lines already built. Three lines are needed already in {y0}, because {fmt(n['design'][y0])} m³/d "
          f"exceeds two lines. At opening, {n_open} lines ({fmt(n_open * line)} m³/d) run at "
          f"{d_open / (1 + m) / (n_open * line) * 100:.0f} per cent of their capacity on the full-connection flow, "
          f"and at {n['low'] / (n_open * line) * 100:.0f} per cent on the Inception connection ratio. The second "
          f"figure is the turndown the process must survive. A Phase I to the fifteen-year horizon of {yo + 15} "
          f"needs {n_15} lines. A second phase to the planning life of {yo + 25} needs {n_25}. Saturation needs "
          f"all {N_LINES}. The years in the table are when capacity must be in service, and each contract starts "
          f"one construction period earlier. The standby line of the N + 1 rule is added to every count.")
    D.callout(d, "This is an illustration, not the phasing.",
              f"The number and size of the lines, the part the existing works plays, the connection path and the "
              f"tanker volume are all decided in the plant options. The method does not change: read the year "
              f"each line is needed from the annual series, check the opening turndown on the low case, and check "
              f"Phase I against the 20,000 m³/d threshold of Section 18.7.",
              fill="EAF1F8", colour=D.MID)
    _where(d, "Annual series: W14/analysis/W14_growth_by_settlement.xlsx sheet \"Qadf by year m3d\" (every year to "
              "2100), through facts_w14.totals()[\"q\"]; the line years are computed in this chapter.")

    # ------------------------------------------------------------ check
    D.h(d, 2, "18.9   Check it yourself")
    D.numbered(d, f"Sum the {ult} column of sheet \"Qadf by year m3d\" in W14_growth_by_settlement.xlsx. It gives "
                  f"{fmt(q_ult)} m³/d. Multiply by 1.10 and compare with stp_ultimate_with_margin_m3d in "
                  f"design_flows.json.", restart=True)
    D.numbered(d, f"Recompute the plant peak: 2.65 × {q_ml:.3f}^0.879 in Ml/d. Divide by {q_ml:.3f} and check the "
                  f"factor of {pf_ult:.3f}.")
    D.numbered(d, f"Recompute the saturation BOD: {fmt(pop_ult)} × 60 / 1000 kg/d, then × 1000 / {fmt(q_ult)}. The "
                  f"concentration should sit near the G203 Table 30 range (Table {t_tank} here). If it does not, the flow per person is wrong.")
    D.numbered(d, f"Find the first year in the annual sheet whose flow × 1.10 exceeds three lines "
                  f"({fmt(3 * line)} m³/d). It should match the table for line 4.")
    D.numbered(d, "When the laboratory and tanker records arrive, replace the 60 g and 80 g with the measured "
                  "loads, add the tanker volume and load, and check the combined COD to BOD ratio against 2.2.")


# =========================================================== 19. EFFLUENT
def c19_effluent(d):
    n = _n(); fmt = F.fmt
    ult, m, q, yo = n["ult"], n["m"], n["q"], n["open_y"]
    q_ult = n["q_ult"]
    deliv = TSE_RATIO * (1 - TSE_LOSS)

    D.h(d, 1, "19   Treated effluent", page_break=True)
    D.p(d, "The plant's output is also a resource. This chapter sets how much treated effluent is produced "
           "and delivered, how the network that carries it is sized, which customers are studied one by one, "
           "and the quality and disinfection it must reach.")

    # ---------------------------------------------------------------- 19.1
    D.h(d, 2, "19.1   How much is produced and how much reaches customers")
    _part(d, "What it is for. ", "The volume of effluent available sets how many customers the treated effluent "
          "network can serve, and how much surplus has to be stored or discharged.")
    _part(d, "The rule. ", "Ninety-five per cent of the plant inflow becomes treated effluent. A further ten "
          "per cent of what is produced is lost in the distribution network.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("TSE")), M.EQ, R("0.95"), M.TIMES, M.sub(R("Q"), UP("inflow"))), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("delivered")), M.EQ, R("0.90"), M.TIMES, M.sub(R("Q"), UP("TSE")),
                       M.EQ, R("0.855"), M.TIMES, M.sub(R("Q"), UP("inflow"))), number=eq)
    _params(d, [
        ["Q inflow", "sewage actually arriving at the plant, without the design margin", "m³/d"],
        ["Q TSE", "treated effluent produced", "m³/d"],
        ["Q delivered", "treated effluent reaching the customers", "m³/d"]])
    D.p(d, "The missing five per cent is evaporation, sludge dewatering, process reuse and the plant's own "
           "landscaping and washing. The two ratios carry different force. The general guideline says the 95 "
           "per cent can be assumed, but the 10 per cent network loss shall be assumed. The margin is capacity, "
           "not sewage, so it is not in the inflow. Tanker volumes join the inflow when their records are "
           "received.")
    _source(d, "G201-p73 §7.4.6.1 (ratio \"Set at 95%\"); G201-p75 §7.4.6.3(a) (\"it can be assumed that 95 "
               "percent ... will be available as TSE\"); G201-p76 §7.4.6.3(b) (\"a system loss of 10 percent of "
               "all produced TSE shall be assumed\").")
    rows = []
    for label, qin in ((f"{yo}, at the Inception connection ratio of {n['conn']:.2f}", n["low"]),
                       (f"{yo}, fully connected", q[yo]), ("2055", q[2055]), (f"{ult}, saturation", q_ult)):
        rows.append([label, fmt(qin), fmt(TSE_RATIO * qin), fmt(deliv * qin)])
    D.tab_caption(d, "Treated effluent produced and delivered")
    D.table(d, ["Case", "Inflow, m³/d", "Produced, m³/d", "Delivered, m³/d"], rows,
            widths=[6.5, 3.3, 3.3, 3.4], font=9, align_right={1, 2, 3})
    _gap(d)
    _part(d, "Worked for Ibri. ", f"At saturation the plant receives {fmt(q_ult)} m³/d, produces "
          f"{fmt(TSE_RATIO * q_ult)} m³/d and delivers {fmt(deliv * q_ult)} m³/d. At opening on the Inception "
          f"connection ratio it delivers only {fmt(deliv * n['low'])} m³/d. The safe direction reverses here. The "
          f"treated effluent pipes are sized on the high case. Customer contracts must be written against the low "
          f"case, because effluent promised and not produced is the failure a customer sees.")
    _where(d, "Computed in this chapter from facts_w14.totals() and design_flows.json low_case_2030_m3d. The "
              "report carries the delivered equation in R2 §17 (W14/report/rpt_cd.py). No treated effluent demand "
              "script exists yet.")

    # ---------------------------------------------------------------- 19.2
    D.h(d, 2, "19.2   Summer-peak sizing and the seasonal factors")
    _part(d, "What it is for. ", "Irrigation demand swings with the season, while the plant's output is nearly "
          "flat. The network is sized on the worst month, and the difference between supply and demand has to "
          "go somewhere.")
    _part(d, "The rule. ", "The treated effluent system is sized for the summer peak demand. Monthly demand is a "
          "percentage of the summer demand:")
    t_season = D.tab_caption(d, "Annual variation of treated effluent demand, per cent of summer demand")
    D.table(d, ["Months", "Per cent of summer demand"], [
        ["December, January, February", "50"],
        ["March, April, May", "75"],
        ["June, July, August", "**100**"],
        ["September, October, November", "75"]], widths=[9.0, 7.5], font=9.5)
    _gap(d)
    D.p(d, "Within the day, demand bunches into the irrigation hours. It is modelled with daily patterns obtained "
           "from the authority or the customers; the guideline's own patterns are for reference only.")
    _source(d, "G201-p76 §7.4.6.4(a) Table 23 and (b) (\"The TSE system shall be sized to accommodate the peak "
               "demand experienced during the summer months\"); G201-p76 (c) and G201-p77 (f) (daily patterns).")
    mean = (3 * 50 + 6 * 75 + 3 * 100) / 12 / 100
    dv = deliv * q_ult
    _part(d, "Worked for Ibri. ", f"Averaged over the year, the G201 Table 23 profile (Table {t_season} here) is {mean * 100:.0f} per cent of "
          f"summer demand. Suppose customers are signed so that their summer demand equals the {fmt(dv)} m³/d "
          f"delivered at saturation. In December to February they take half of it, and {fmt(0.5 * dv)} m³/d is "
          f"surplus. Over the year the surplus averages {fmt((1 - mean) * dv)} m³/d. Suppose instead demand is "
          f"matched to the annual average. Then summer demand is {fmt(dv / mean)} m³/d and summer falls short by "
          f"{fmt(dv / mean - dv)} m³/d. Either way the gap is storage, or discharge to a wadi at Class A. That is "
          f"why the Terms of Reference ask for treated effluent discharge to wadis and emergency lagoons as well "
          f"as the network.")
    _where(d, "Computed in this chapter. Terms of Reference, Data/scope.pdf PDF page 22, item 8 (d) and (e).")

    # ---------------------------------------------------------------- 19.3
    D.h(d, 2, "19.3   Customers and the large consumers")
    _part(d, "What it is for. ", "The demand the network is sized on is the sum of its customers. The largest of "
          "them set the hydraulics on their own.")
    _part(d, "The rule. ", "Customers are public (landscaping of highways, secondary roads, interchanges and "
          "roundabouts, and public parks) or private (community parks, golf courses, private gardens, and "
          "nurseries and farms). Demand is built from summer planting rates. Any consumer averaging more than "
          "500 m³/d is studied individually, with an irrigation timing pattern that reflects its actual settings. "
          "A consumer with large storage has its demand spread evenly over the hours its storage covers.")
    t_irr = D.tab_caption(d, "Summer irrigation demand for concept design")
    D.table(d, ["Planting", "Summer demand", "Planting", "Summer demand"], [
        ["Shrubs", "20 – 40 l/plant/d", "Ground cover", "10 l/m²/d"],
        ["Palm trees", "120 – 165 l/plant/d", "Seasonal flowers", "10 l/m²/d"],
        ["Other trees", "40 – 80 l/plant/d", "Grass", "12 l/m²/d"],
        ["Hedges", "10 l/m/d", "Roads and junctions, mixed", "10 l/m²/d"]], widths=[3.6, 4.5, 4.4, 4.0], font=9)
    _gap(d)
    D.p(d, "Planting densities for concept design are 15 m spacing for trees and 3 m for shrubs. The road rate "
           "applies where the vegetation is unknown and needs the municipality's approval.")
    _source(d, "G201-p74 Table 20 (consumers); G201-p75 Tables 21 and 22 and item (j); G201-p76 §7.4.6.4 (d) "
               "(\"larger than 500 m3/day is to be studied individually\") and (e) (storage).")
    _part(d, "Worked for Ibri. ", f"A consumer of 500 m³/d is {500 / dv * 100:.1f} per cent of the effluent "
          f"delivered at saturation. On the G201 Table 21 rates (Table {t_irr} here), 500 m³/d is {fmt(500 / 12 * 1000 / 10000, 1)} ha of "
          f"grass in summer, or {fmt(500 * 1000 / 165)} to {fmt(500 * 1000 / 120)} palm trees. A golf course, a "
          f"large farm or the municipality's road landscaping each crosses that line, so each is modelled on its "
          f"own. The customer list is itself a deliverable of the Terms of Reference and is not yet held.")
    _where(d, "Terms of Reference, Data/scope.pdf PDF page 22, item 10 (list of treated effluent customers and "
              "their demands). No customer dataset is in W14.")

    # ---------------------------------------------------------------- 19.4
    D.h(d, 2, "19.4   Quality: Class A and total nitrogen")
    _part(d, "What it is for. ", "The effluent standard decides the treatment process. At Ibri the nitrogen "
          "limit, not the BOD limit, is the one that decides.")
    _part(d, "The rule. ", "The process must meet Class A or B of Ministerial Decision 145/1993, and any "
          "effluent discharged to a wadi must meet at least Class A, with the approval of the Environmental "
          "Authority and APSR. Separately, the technology selected must meet a combined total nitrogen below "
          "15 mg/l as N, where total nitrogen is organic nitrogen plus ammonia, ammonium, nitrite and nitrate.")
    D.tab_caption(d, "Class A limits that shape the process, mg/l unless stated")
    D.table(d, ["Parameter", "Class A", "Parameter", "Class A"], [
        ["BOD₅", "15", "Ammoniacal nitrogen as N", "5"],
        ["COD", "150", "Organic (Kjeldahl) nitrogen as N", "5"],
        ["Suspended solids", "15", "Nitrate as NO₃", "50"],
        ["Faecal coliforms", "200 per 100 ml", "Total phosphorus as P", "30"],
        ["Viable nematode ova", "fewer than 1 per l", "Total nitrogen (NWS)", "**below 15 as N**"]],
        widths=[3.8, 3.6, 5.2, 3.9], font=9)
    _gap(d)
    _source(d, "G203-p69 §10.2.4.1 and Table 34 (BOD, COD, SS), G203-p70 (nitrogen, phosphorus), G203-p71 "
               "(coliforms, ova; \"Total Nitrogen limit < 15 mg/L as N\"); G203-p73 §10.2.4.3 (wadi discharge at "
               "least Class A, EA and APSR approval).")
    no3n = 50 * 14.007 / 62.004
    _part(d, "Worked for Ibri. ", f"Add the three Class A nitrogen limits on one basis. Nitrate at 50 mg/l as "
          f"NO₃ is 50 × 14 / 62 = {no3n:.1f} mg/l as N. Ammoniacal 5 plus organic 5 plus nitrate {no3n:.1f} gives "
          f"{5 + 5 + no3n:.1f} mg/l, which Class A would allow. NWS allows 15. The plant therefore needs full "
          f"nitrification and denitrification, and that narrows the technologies before BOD or solids enter the "
          f"choice. The tighter limits of Decision 159/2005 apply only where the wadi reaches the sea at a "
          f"reasonable distance. Ibri's wadis are inland, so applying them would over-specify the plant.")
    _where(d, "Concept Design Report R2 §13 treatment plant criteria table and its footnote (W14/report/rpt_cd.py); "
              "_BRAIN/02_DESIGN_CRITERIA.md §9 (wadi row).")

    # ---------------------------------------------------------------- 19.5
    D.h(d, 2, "19.5   Chlorine residual: two requirements, one dose")
    _part(d, "What it is for. ", "The effluent must stay disinfected all the way to the furthest customer. "
          "Chlorine decays along the network, so one number at the plant is not enough.")
    _part(d, "The rule. ", "There are two requirements at two places, and the dose must satisfy both.")
    eq = D.next_eq()
    M.display(d, M.seq(R("0.3"), R(" ≤ "), M.sub(R("C"), UP("discharge")), R(" ≤ "), R("1.0"),
                       UP("   (up to 3.0 permitted for decay in the network)")), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(R("0.3"), R(" < "), M.sub(R("C"), UP("consumer")), R(" < "), R("1.0")), number=eq)
    _params(d, [
        ["C discharge", "total chlorine residual at the plant's point of discharge", "mg/l"],
        ["C consumer", "total chlorine residual at every consumer end", "mg/l"]])
    D.p(d, "The second requirement governs the first. The allowable maximum at the discharge depends on the "
           "length and character of the treated effluent network. The discharge set-point therefore comes out "
           "of the network model's water age, not out of the plant design. For a large plant, disinfection "
           "takes place in a treated effluent storage tank that works as the contact tank. It gives 30 minutes "
           "at peak flow, a residual of 0.5 mg/l and a contact value of at least 15 mg·min/l, with a baffling "
           "factor of 0.7 or more.")
    _source(d, "G203-p71 §10.2.4.1 (\"at least between 0.3 mg/L and 1.0 mg/L\" at the STP point of discharge, "
               "\"up to 3.0 mg/L are permitted\"); G203-p130 §10.6.7 (\"greater than 0.3 mg/L and less than "
               "1.0 mg/L at the consumer end\"; maximum at discharge \"depends on the length and characteristics "
               "of the TSE distribution network\"); G203-p135 §10.6.7.4 (large plants: TSE storage tank as "
               "contact tank; 30 min, 0.5 mg/l, CT 15 mg/L.min, T10/T 0.7).")
    pk = merrimack(q_ult) * (1 + m)
    _part(d, "Worked for Ibri. ", f"The three contact criteria are one condition. A residual of 0.5 mg/l held "
          f"for 30 minutes gives 0.5 × 30 = 15 mg·min/l, exactly the minimum, so neither may be relaxed "
          f"without raising the other. Take the design peak hourly flow at saturation, {fmt(pk)} m³/d, through "
          f"the tank without the five per cent process loss, which is the safe side. The effective contact volume "
          f"is {fmt(pk)} × 30 / 1,440 = {fmt(pk * 30 / 1440)} m³. The storage the tank must also provide for the "
          f"customers comes on top of that.")
    _where(d, "Computed in this chapter from facts_w14.totals(). The discharge set-point waits for the treated "
              "effluent network model.")

    D.h(d, 2, "19.6   Check it yourself")
    D.numbered(d, f"Multiply the saturation flow of {fmt(q_ult)} m³/d by 0.95 and then by 0.90, and compare with "
                  f"the table in Section 19.1.", restart=True)
    D.numbered(d, f"Average the twelve monthly percentages of G201 Table 23, reproduced here as Table {t_season}, "
                  f"\"Annual variation of treated effluent demand\". The result is {mean * 100:.0f}, and the ratio "
                  f"of summer demand to the annual average is 1 / {mean:.2f}.")
    D.numbered(d, "Convert the three Class A nitrogen limits to mg/l as N and add them. The sum exceeds 15, "
                  "which is why the plant must denitrify.")
    D.numbered(d, "When the network model is built, read the water age at the furthest customer and confirm "
                  "that the discharge residual still leaves more than 0.3 mg/l there.")


# ============================================================== 20. SLUDGE
def c20_sludge(d):
    n = _n(); fmt = F.fmt
    ult, q, yo = n["ult"], n["q"], n["open_y"]
    q_ult, pop_ult = n["q_ult"], n["pop_ult"]
    s_ult = SLUDGE * q_ult

    D.h(d, 1, "20   Sludge", page_break=True)
    D.p(d, "Sludge handling and disposal are an integral part of every treatment plant, and their plans and "
           "specifications are part of its design. This chapter sets the quantity, where the sludge goes, and "
           "what the disposal route forces on the dewatering and drying.")
    _source(d, "G203-p135 §10.6.8 (\"must be considered as an integral part of any complete treatment "
               "system\").")

    # ---------------------------------------------------------------- 20.1
    D.h(d, 2, "20.1   How much")
    _part(d, "What it is for. ", "The sludge quantity sizes the thickening, dewatering, drying and storage, and "
          "the vehicle traffic to the outlet.")
    _part(d, "The rule. ", "For planning, sludge is taken as a fixed yield per cubic metre of inflow.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("M"), UP("s")), M.EQ, R("0.25"), M.TIMES, M.sub(R("Q"), UP("inflow"))), number=eq)
    _params(d, [
        ["M s", "sludge produced, read as dry solids", "kg/d"],
        ["Q inflow", "plant inflow", "m³/d"]])
    D.p(d, "The figure is a master-plan baseline and a starting point for the sludge strategy, not a design "
           "value. The guideline says the quantity depends heavily on the influent quality and the process, "
           "and it does not say whether the 0.25 is dry solids or wet cake. It is read here as dry solids. The "
           "process design replaces it with a yield worked from the loads of Section 18.5.")
    _source(d, "G201-p78 §7.4.7 (\"a baseline value of 0.25 kg/m³ is used as a general guideline\"). Dry-solids "
               "reading: interpretation, to be confirmed with NWS.")
    rows = []
    for y in (yo, 2055, ult):
        s = SLUDGE * q[y]
        rows.append([str(y), fmt(q[y]), fmt(s), fmt(s * 365 / 1000)])
    D.tab_caption(d, "Sludge at 0.25 kg per cubic metre of inflow, 100 % connected")
    D.table(d, ["Year", "Inflow, m³/d", "Sludge, kg/d dry solids", "Sludge, t/year dry solids"], rows,
            widths=[2.5, 4.3, 4.9, 4.8], font=9, align_right={1, 2, 3})
    _gap(d)
    bod_ult = pop_ult * BOD_PC / 1000
    _part(d, "Worked for Ibri. ", f"At saturation, 0.25 × {fmt(q_ult)} = {fmt(s_ult)} kg/d, about "
          f"{fmt(s_ult / 1000, 1)} t/d of dry solids or {fmt(s_ult * 365 / 1000)} t a year. Against the "
          f"{fmt(bod_ult)} kg/d of BOD arriving (Section 18.5), that is {s_ult / bod_ult:.2f} kg of sludge per kg of "
          f"BOD. The guideline gives no yield per kilogram of BOD to check this against, which is why the process "
          f"model has to produce the design figure.")
    _where(d, "Computed in this chapter from facts_w14.totals(); no pipeline script carries sludge yet.")
    D.p(d, "Tutorial T01 called the 0.25 kg/m³ an Inception Report planning rate. It is the general guideline's "
           "own master-plan baseline.", italic=True, size=9.5)

    # ---------------------------------------------------------------- 20.2
    D.h(d, 2, "20.2   Where it goes")
    _part(d, "What it is for. ", "The outlet fixes the dryness the sludge must reach, and so the treatment line.")
    _part(d, "The rule. ", "Sludge is reused unless no form of reuse is possible. Its quality must meet the "
          "heavy-metal limits of Table 2 of Ministerial Decision 145/93, which the guideline cites but does not "
          "reproduce. Sludge above those limits goes to landfill only with the Ministry's prior approval, and on "
          "the landfill operator's terms.")
    D.callout(d, "Ibri is the governorate's sludge treatment centre.",
              "The national sludge plan, as the wastewater guideline records it, names composting at Ibri plant as "
              "the sludge treatment centre for Adh Dhahirah. The plant receives sludge from the governorate as "
              "well as producing its own, and that has to be carried into the land area, the odour buffer and "
              "the vehicle access. The quantity it will receive from other plants is not yet known.",
              fill="EAF1F8", colour=D.MID)
    D.tab_caption(d, "Landfill acceptance of sludge")
    D.table(d, ["Criterion", "Requirement"], [
        ["Solids content", "**at least 80 %, dried before disposal**"],
        ["pH", "neutral, for stability"],
        ["Temperature", "ambient, no heat generation"],
        ["Daily quantity", "not more than 60 t/d, depending on the landfill and its other waste"],
        ["Standing", "the operator may stop receiving sludge at any time"]], widths=[4.5, 12.0], font=9.5)
    _gap(d)
    _source(d, "G203-p136 Table 67 (\"Adh Dhahirah: STC - composting in Ibri STP\"), §10.6.8.1 (MD 145/93 reuse "
               "and heavy metals; landfill with prior Ministry approval; landfill criteria); G203-p137 (temperature, "
               "60 tons/day, right to stop).")

    # ---------------------------------------------------------------- 20.3
    D.h(d, 2, "20.3   Dewatering and drying")
    _part(d, "What it is for. ", "Dewatering turns liquid sludge into cake. Its capacity and the dryness it "
          "reaches decide whether the cake can leave the site.")
    _part(d, "The rule. ", "Dewatering is sized on the peak weekly average flow at 11 hours a day, 7 days a week. "
          "It has a standby unit, or else storage for at least four days of production. Solids recovery is at "
          "least 95 per cent. Cake exceeds 22 per cent dry solids, or 18 per cent for surplus activated sludge "
          "alone. Thermal dryers take cake of 20 to 25 per cent and produce more than 90 per cent.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("M"), UP("h")), M.EQ, M.frac(M.sub(R("M"), UP("s,week")), R("11")),
                       R("     "), M.sub(R("M"), UP("cake")), M.EQ, M.frac(M.sub(R("M"), UP("s")), R("DS"))),
              number=eq)
    _params(d, [
        ["M h", "dewatering throughput per operating hour", "kg DS/h"],
        ["M s,week", "daily sludge in the peak week", "kg DS/d"],
        ["M cake", "cake leaving the dewatering, wet mass", "kg/d"],
        ["DS", "dry-solids fraction of the cake", "—"]])
    _source(d, "G203-p151 §10.6.8.6 (peak weekly average flow, 11 h/d, 7 d/week, standby, 4 days storage, "
               "22 %DS and 18 %DS, recovery 95 %); G203-p155 (thermal dryers fed at 20 - 25 %DS, more than "
               "90 %DS out).")
    cake22, cake80 = s_ult / 0.22 / 1000, s_ult / 0.80 / 1000
    _part(d, "Worked for Ibri. ", f"The peak-week factor is not in the guideline and will come from the "
          f"existing works' records, so take the average week. At saturation, dewatering handles "
          f"{fmt(s_ult)} / 11 = {fmt(s_ult / 11)} kg DS per operating hour. At the 22 per cent minimum dryness "
          f"the cake is {fmt(s_ult)} / 0.22 = {fmt(cake22, 1)} t/d, above the landfill's 60 t/d on its own. Dried to "
          f"the landfill's 80 per cent it is {fmt(cake80, 1)} t/d. Mechanical dewatering alone cannot reach the "
          f"landfill criterion. Drying or composting is forced whichever outlet is used, and composting is "
          f"what the national plan already assigns to Ibri.")
    _where(d, "Computed in this chapter from facts_w14.totals(). The peak-week factor and the sludge the works "
              "already produces are requests to NWS, with the existing works data (_BRAIN/05_GAPS.md GAP-7).")

    D.h(d, 2, "20.4   Check it yourself")
    D.numbered(d, f"Multiply the saturation flow of {fmt(q_ult)} m³/d by 0.25 and compare with the table in "
                  f"Section 20.1.", restart=True)
    D.numbered(d, "Divide the dry solids by 0.22 and by 0.80 and set each against the landfill's 60 t/d.")
    D.numbered(d, "When the existing works' records arrive, compare their measured sludge per cubic metre with "
                  "0.25, and replace the baseline in the process model.")
