"""T04 chapters 21 to 24 and Appendix A: what the options cost, how they are appraised
and chosen, where the guidelines cannot be relied on, and the register of equations,
fields and the rerun order.

Every number about Ibri is read live from W14/report/facts_w14.py or from
W14/analysis/design_flows.json. A guideline value carries its page in the constant
block below; anything else is a dated project rule or a tagged outside assumption.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report"))   # after T04: its doc.py must not shadow ours
import doc as D
import omml as M
import facts_w14 as F
UP, R = M.up, M.r
IMG = os.path.join(HERE, "img")

import json  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
FLOWS = os.path.join(REPO, "W14", "analysis", "design_flows.json")

# ------------------------------------------------ guideline and project constants
RATE = 0.05             # discount rate, G201 p96 ("unless otherwise instructed by NWS")
YEARS = 25              # appraisal period, G201 p57 and p96
TIE = 0.10              # tie-break band on total lifetime cost, G201 p106
TSE_RATIO = 0.95        # treated effluent per m3 of plant inflow, G201 p73
SLUDGE_KG_M3 = 0.25     # indicative sludge per m3 of inflow, G201 p78
CO2_TSE = 1.17e-3       # NWS emission intensity, tCO2e per m3 of treated effluent, G201 p99
LARGE_STP = 20000.0     # m3/d, G203 p65
CW_M3D, CW_PE = 500.0, 4000   # constructed wetlands, "approximately up to", G203 p101
K_LS, K_M3S = 5.5e-3, 2.33e-4  # tractive-slope coefficient for Q in l/s and in m3/s, G203 p27
TAU_INTERIM = 1.0       # Pa: interim value tagged GAP-9 in _BRAIN/05_GAPS.md, NOT a guideline value
Q_MARA = 1.5            # l/s: Mara minimum peak flow, outside assumption, not in G203
S_DN200 = 5.00          # mm/m, minimum gradient of a DN200 sewer, G203 Table 11 p29


# --------------------------------------------------------------------- helpers
def _flows():
    with open(FLOWS, encoding="utf-8") as fh:
        return json.load(fh)


def _live():
    t = F.totals()
    st = F.settlement_table()
    ib = next(r for r in st if r["key"] == "IBRI")
    return t, _flows(), st, F.plot_summary(), ib


def _annuity(r=RATE, n=YEARS):
    return (1 - (1 + r) ** -n) / r


def _k_conv():
    """The m3/s tractive-slope constant restated for Q in l/s."""
    return K_M3S * 1000 ** 0.461


def _k_gap():
    """Per cent by which the printed l/s constant gives a flatter gradient than the m3/s one."""
    return (1 - K_LS / _k_conv()) * 100


K_M3S_TXT = f"{K_M3S * 1e4:.2f} × 10⁻⁴"
K_LS_TXT = f"{K_LS * 1e3:.1f} × 10⁻³"


def _plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def _lead(d, lead, text):
    return D.rich(d, (lead + "  ", {"bold": True}), (text, {}))


def _for(d, text):
    _lead(d, "What it is for.", text)


def _rule(d, text):
    _lead(d, "The rule.", text)


def _ibri(d, text):
    _lead(d, "Worked Ibri number.", text)


def _src(d, text):
    D.p(d, "Source: " + text, size=9, italic=True, colour=D.GREY, space_after=6)


def _where(d, text):
    D.rich(d, ("Where it lives.  ", {"bold": True, "size": 9.5}),
           (text, {"size": 9.5, "colour": D.GREY}), space_after=10)


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)
    D.p(d, "", space_after=2)


def _items(d, caption, rows):
    D.tab_caption(d, caption)
    D.table(d, ["Group", "Items"], rows, widths=[4.0, 12.5], font=9)
    D.p(d, "", space_after=2)


def _check(d, heading, items):
    D.h(d, 2, heading)
    for i, text in enumerate(items):
        D.numbered(d, text, restart=(i == 0))


# =================================================================== 21  COST
def c21_cost(d):
    t, j, st, ps, ib = _live()
    ult = t["ultimate"]
    margin = j["rules"]["stp_margin"]
    props = j["properties"]
    q30m, qum = t["q"][2030] * (1 + margin), t["q_ult"] * (1 + margin)
    ib_ult = next(s for s in j["settlements"] if s["key"] == "IBRI")["q_ult"]

    D.h(d, 1, "21   Cost estimation", page_break=True)
    D.p(d, "Three options per system are compared on cost, and the comparison "
           "decides which one is built. An estimate that leaves out a whole "
           "category of work does not merely understate the total. It distorts "
           "the ranking, because the omission usually falls harder on one option "
           "than on another. This chapter sets out the basis of the estimate, how "
           "a capital cost is built up, what it must contain and the lines that "
           "are usually missed. Chapter 22 turns the estimate into a decision.")
    D.picture(d, os.path.join(IMG, "F14_cost.png"), 15.5)
    D.fig_caption(d, "Building the estimate. Renewal and decommissioning sit inside "
                     "the twenty-five year horizon, not beyond it.")

    # ------------------------------------------------------------------ 21.1
    D.h(d, 2, "21.1   The basis of the estimate")
    _for(d, "The basis fixes the accuracy, the price date, the rates and the "
            "presentation before a single rate is written, so that every option "
            "is priced on the same footing.")
    _rule(d, "The estimate is built to the requirements in the table.")
    D.tab_caption(d, "Basis of the cost estimate")
    D.table(d, ["Item", "Requirement", "Source"], [
        ["Accuracy", "**± 20 %** at this stage, stated in the report; ± 30 % at "
                     "feasibility and ± 10 % at detailed design", "G201 p17–18"],
        ["Contingencies", "the stage accuracy is reached by reducing contingencies "
                          "and uncertainty, so the contingencies are stated lines, "
                          "not hidden in the rates", "G201 p18"],
        ["Unit rates", "the most recent market rates, preferably from NWS tender "
                       "or contract documents", "G201 p95"],
        ["Price basis", "capital and operating cost from the start of "
                        "construction, at current base prices", "G201 p96"],
        ["Format and method", "NWS advises the required format and methodology on "
                              "request, before the design phase", "G201 p96"],
        ["Presentation", "by asset category at feasibility; **by system element, "
                         "as a cost curve**, at preliminary design; a bill of "
                         "quantities at detailed design", "G201 Table 2, p21–22"],
        ["Method of measurement", "none is named in the three guidelines; CESMM3 is "
                                  "proposed, to be confirmed when NWS advises the "
                                  "format", "project proposal"],
    ], widths=[3.4, 10.3, 2.8], font=9)
    D.p(d, "", space_after=2)
    _src(d, "PAM-GUD-201 §1.6 pp 17–18, Table 2 pp 19–22, §12.2 pp 95–96. The "
            "guideline names three stages: feasibility, preliminary and detailed. "
            "It places the comparison and selection of options by multi-criteria "
            "analysis in the preliminary design (p18), which is the work of this "
            "concept stage, so ± 20 % applies. That reading is ours. T03 listed "
            "CESMM3 as a requirement; a search of all three guidelines finds no "
            "method of measurement, so it is carried here as a proposal.")
    _ibri(d, f"A cost curve for the plant must span the capacities its phases will "
             f"take. With the plant margin of {margin * 100:.0f} % (G201 p73) that "
             f"is at least {F.fmt(q30m)} m³/d, the {F.fmt(t['q'][2030])} m³/d of "
             f"2030 with the margin, up to {F.fmt(qum)} m³/d, the "
             f"{F.fmt(t['q_ult'])} m³/d of saturation in {ult} with the margin. "
             f"Both ends are a Large plant ({F.fmt(LARGE_STP)} m³/d or more, "
             f"G203 p65), so the curve is priced on large-plant rates throughout.")
    _where(d, "No cost model exists yet. The basis is stated in report R2 §35.1 "
              "(W14/report/rpt_gh.py). The accuracy row is in "
              "_BRAIN/02_DESIGN_CRITERIA.md, \"Cost/schedule accuracy by phase\". "
              "The flows and the margin: W14/analysis/design_flows.json, keys "
              "totals and stp_margin.")

    # ------------------------------------------------------------------ 21.2
    D.h(d, 2, "21.2   How a capital cost is built up")
    _for(d, "One structure for every option and every system, so that two "
            "estimates differ only where the designs differ.")
    _rule(d, "Each item is priced as a unit cost times a quantity, the items are "
             "summed, and preliminaries and the two contingencies are added as "
             "stated fractions of that sum.")
    eq = D.next_eq()
    M.display(d, M.seq(
        M.sub(R("C"), UP("cap")), M.EQ,
        M.delim(M.seq(R("1"), M.PLUS, M.sub(R("f"), UP("pre")), M.PLUS,
                      M.sub(R("f"), UP("phys")), M.PLUS, M.sub(R("f"), UP("price")))),
        M.TIMES,
        M.nary("∑", R("k"), R(""), M.seq(M.sub(R("c"), R("k")), M.sub(R("q"), R("k"))),
               hide_hi=True)), number=eq)
    _params(d, [
        ["C cap", "capital cost of the option", "OMR"],
        ["c k", "unit cost of item k: per metre of sewer by diameter and depth band, "
                "per chamber by depth band, per connection, per m³/d of plant "
                "capacity, per station by duty", "OMR per unit"],
        ["q k", "quantity of item k, taken from the design of that option", "m, no., m³/d"],
        ["f pre", "preliminaries, as a fraction of the sum", "—"],
        ["f phys", "physical contingency: quantity and scope the design does not "
                   "yet know; it shrinks as the design develops", "—"],
        ["f price", "price contingency: escalation from the base date to the middle "
                    "of construction", "—"]])
    D.p(d, "Two pricing rules follow from how a sewer network spends its money. "
           "A gravity sewer is priced by diameter and by depth band, because in a "
           "deep trench the excavation, the support and the dewatering cost more "
           "than the pipe; a flat rate per diameter prices a 9 m trench like a "
           "2 m one. And every option is costed as it is designed, with its own "
           "pumping stations, its own storage and the energy that follows from "
           "them, never as the preferred option with one quantity changed.")
    D.callout(d, "Contingency is not a single number.",
              "Keep the physical allowance, which covers what the design does not "
              "yet know, apart from the price allowance, which covers inflation "
              "between the estimate and construction. Merged, they hide which one "
              "drives the total, and only the first should shrink as the design "
              "develops.")
    _src(d, "the structure is adopted from the two NWS pre-investment appraisals, "
            "which price unit rate times quantity by diameter and material, then "
            "add preliminaries and contingency as percentages of the sub-total "
            "(one used 10 % and 20 %, so its total is 1.30 times the sub-total). "
            "The guidelines give no unit rates, no uplifts and no build-up. "
            "Project rule (engineer, 2026-09-01), which also sets depth-band "
            "pricing and costing each option as designed.")
    _ibri(d, f"The connection line shows why every quantity needs its year. The "
             f"saturation network serves {F.fmt(props['ultimate'])} domestic "
             f"properties. {F.fmt(props['y2024'])} exist in 2024 and "
             f"{F.fmt(props['y2030'])} by 2030; the other "
             f"{F.fmt(props['ultimate'] - props['y2030'])} are connected as the "
             f"empty plots fill, after the network opens. They are a cost in the "
             f"years they are made, and Chapter 22 discounts them there. Put in "
             f"year zero they would be charged at full value instead of their "
             f"present value.")
    D.callout(d, "The only NWS-sourced rates held are water-supply rates.",
              "The rates in the two NWS pre-investment appraisals are for water "
              "mains in polyethylene, ductile iron and steel, and for a concrete "
              "reservoir. They carry no sewer, chamber or treatment rate, and the "
              "2019 and 2023 sets are identical to the digit although both claim "
              "recent tender prices. Use them only as a cross-check, escalated to "
              "a stated base date. Priced bills of quantities from completed "
              "schemes have been requested; when they arrive they become the "
              "primary basis.", fill="EAF1F8", colour=D.MID)
    _where(d, "No script prices anything yet. The structure and the rate "
              "provenance: W9/analysis/W9_PIAD_financial_review.md §2.1, §6 and "
              "§6b; report R2 §35.1–35.2 (W14/report/rpt_gh.py). Connections by "
              "year: W14/analysis/design_flows.json, key properties, written by "
              "W14/py/make_design_flows.py as G_DOM + (POP_year − POP) / OR_S "
              "summed over the plots.")

    # ------------------------------------------------------------------ 21.3
    D.h(d, 2, "21.3   What the estimate must contain")
    _for(d, "The largest single risk in a sewerage estimate is that the pipe is "
            "priced carefully and everything around it is not. In urban work the "
            "trench, the reinstatement and the traffic usually cost more than the "
            "pipe. The tables below are the checklist against that.")
    _rule(d, "Every group below is priced for every option, or is stated as not "
             "applicable to it with the reason.")
    _items(d, "Sewer network items", [
        ["Earthworks", "Excavation by depth band; rock excavation priced separately; "
                       "dewatering where the water table is met; trench support by "
                       "depth; disposal of surplus and unsuitable material"],
        ["Pipework", "Pipe supply and lay by diameter and material; bedding and "
                     "surround; selected backfill and imported fill; jointing; "
                     "specials and fittings"],
        ["Chambers", "Manholes by depth band and diameter; backdrops where inverts "
                     "differ by more than 600 mm (G203 p30); drop shafts; benching "
                     "and channels; covers by loading class"],
        ["Tertiary sewers and connections",
         "Property connection sewers and connection chambers; rider and lateral "
         "sewers (a lateral no longer than 45 m, G203 Table 6); connections to the "
         "existing network; stubs and end caps for plots not yet built"],
        ["Surface", "**Road reinstatement by surface type**: asphalt, interlock, "
                    "kerb, footpath, unpaved; line marking; **traffic management "
                    "and diversions**"],
        ["Crossings", "Road, wadi and utility crossings; every dual-carriageway "
                      "crossing, which the layout allows only as a short "
                      "perpendicular pipe; trenchless drives where open cut is not "
                      "permitted; carrier and sleeve pipes; thrust and reception pits"],
        ["Enabling", "Trial pits; utility diversions and protection; temporary "
                     "works; site establishment"],
        ["Proving", "Water and air tightness testing; CCTV survey; compaction "
                    "testing; as-built survey"]])
    _items(d, "Lifting station items", [
        ["Land and site", "Land acquisition and Krooki fees; clearance and "
                          "levelling; access road and turning area; boundary wall "
                          "and gates; landscaping"],
        ["Civil", "Wet well by depth; dry well or valve chamber; base slab and "
                  "dewatering during construction; protective lining; "
                  "superstructure or cover slab; emergency storage or overflow "
                  "structure"],
        ["Mechanical", "Duty and standby pumps; screens or macerators; station "
                       "pipework, valves and non-return valves; lifting davit or "
                       "gantry; sump pump; ventilation"],
        ["Electrical and control", "Incoming supply and connection charges; "
                                   "transformer; motor control centre; standby "
                                   "generator and fuel storage; instrumentation, "
                                   "SCADA and telemetry; small power and lighting"],
        ["Odour and safety", "Odour control unit and ducting; gas detection; fire "
                             "detection where required; welfare facilities"],
        ["Commissioning", "Testing, commissioning, operator training, spares"]])
    _items(d, "Force main items", [
        ["Pipework", "Pipe supply and lay by diameter and material; excavation, "
                     "bedding and backfill as for gravity; thrust and anchor "
                     "blocks; restrained joints"],
        ["Appurtenances", "Air valves and their chambers; washouts at low points; "
                          "in-line isolation valves at about 500 m and never more "
                          "than 800 m apart (G203 p53–54); access every 500 m "
                          "(G203 p50); marker posts and warning tape"],
        ["Termination", "Receiving manhole; vent and odour control at the "
                        "discharge"],
        ["Proving", "Pressure testing; pigging or flushing provision; surge "
                    "protection identified by the transient study"]])
    _items(d, "Treatment plant items", [
        ["Land and site", "Land acquisition; site preparation and earthworks; "
                          "**protection against the 25-year and 100-year flood "
                          "levels, the plant to stay operational in a flood** "
                          "(G203 p63, Table 27); internal roads; fencing; buffer "
                          "planting; solar area if provided"],
        ["Inlet works", "Coarse and fine screens; screenings handling; grit "
                        "removal; fat, oil and grease removal; **tanker discharge "
                        "facility** with its screening, sampling, flow measurement "
                        "and equalisation; flow equalisation"],
        ["Biological treatment", "Reactor civils; aeration equipment and blowers; "
                                 "mixers; internal recycle pumps; membranes or "
                                 "media where used"],
        ["Separation and tertiary", "Clarifiers with scrapers; return and surplus "
                                    "sludge pumping; tertiary filtration; "
                                    "disinfection; treated effluent storage acting "
                                    "as contact tank"],
        ["Sludge line", "Thickening; digestion where provided; dewatering with a "
                        "standby unit; drying or composting; storage; **reception "
                        "of sludge from other plants**, because Ibri is the "
                        "governorate's designated sludge treatment centre (G203 "
                        "Table 67, p136)"],
        ["Chemical systems", "Coagulant, polymer, pH correction, carbon source and "
                             "disinfectant dosing; bulk storage and bunding"],
        ["Odour", "Covers and enclosures; extraction ducting; treatment units; "
                  "continuous monitoring"],
        ["Electrical and control", "Incoming supply and substation; motor control "
                                   "centres; standby generation; solar "
                                   "photovoltaic; instrumentation, control and "
                                   "SCADA"],
        ["Buildings", "Administration, laboratory, workshop, stores, welfare; "
                      "blower and dewatering buildings; guard house"],
        ["Emergency and disposal", "Emergency lagoon of 48 to 72 hours, only where "
                                   "NWS requires and approves it (G203 p73); raw "
                                   "sewage diversion; wadi outfall and its "
                                   "approvals; treated effluent filling station"],
        ["Commissioning", "Wet and dry commissioning; process proving to Class A; "
                          "operator training; initial spares"]])
    _items(d, "Treated effluent network items", [
        ["Distribution", "Pipework by diameter; excavation and reinstatement; "
                         "valves, air valves and washouts; crossings"],
        ["Storage and boosting", "Reservoirs; booster stations; chlorine top-up "
                                 "where the network is long"],
        ["Customers", "Customer connections and meters; filling stations with "
                      "their identification, metering and control systems"]])
    _items(d, "Costs outside the works", [
        ["Professional", "Design and supervision fees; topographic and utility "
                         "survey; geotechnical investigation; hydraulic modelling"],
        ["Consents", "Environmental impact assessment; NOCs and permits; land and "
                     "Krooki fees; municipality and roads authority approvals"],
        ["Provisions", "**Physical contingency**; **price contingency** to the "
                       "middle of construction; risk allowance carried from the "
                       "risk register"]])
    _src(d, "the stages of the life-cycle cost, from planning to disposal, G201 "
            "§12.4 p96; the item values as cited in the tables. The lists "
            "themselves are the designer's checklist, not a guideline table.")
    _ibri(d, f"At saturation the study area produces {F.fmt(t['q_ult'])} m³/d and "
             f"Ibri town alone {F.fmt(ib_ult)} m³/d. Either is a Large plant "
             f"(G203 p65), and a Large plant takes a residential buffer of 300 to "
             f"1,000 m set by odour modelling, the 5 OU contour, rather than a "
             f"fixed distance (G201 Table 8, p43). The land "
             f"line of the estimate therefore cannot be priced until the odour "
             f"contour is drawn, and it will differ between a process with covered "
             f"and treated air and one without.")
    _where(d, "Report R2 §35.2 (W14/report/rpt_gh.py) states the scope in client "
              "terms. The flows by settlement: W14/analysis/design_flows.json, key "
              "settlements.")

    # ------------------------------------------------------------------ 21.4
    D.h(d, 2, "21.4   Five lines that get missed")
    _for(d, "Each of these is routinely omitted, and each is large enough to move "
            "a ranking.")
    D.bullet(d, "priced as if the ground were soft. In this terrain it rarely is, "
                "and the difference is several times the rate.",
             lead="Rock excavation: ")
    D.bullet(d, "often the largest single line in urban sewerage, and sensitive to "
                "surface type in a way an average rate hides.",
             lead="Road reinstatement: ")
    D.bullet(d, "instrumentation and control lasts 15 years, mechanical plant 20 "
                "and electrical plant 15 to 50 (G201 Table 10, p57). A 25-year "
                "appraisal therefore contains at least one replacement of the "
                "first two. Leaving it out flatters every option heavy in plant, "
                "which is the decentralised one.",
             lead="Renewal inside the horizon: ")
    D.bullet(d, "not marginal here, because the plant is the governorate's "
                "designated sludge treatment centre and receives sludge from "
                "beyond its own catchment (G203 Table 67, p136).",
             lead="Sludge haulage: ")
    D.bullet(d, "named in the guideline's own life-cycle scope (G201 p96) and "
                "almost always left out.", lead="Decommissioning: ")
    _where(d, "Report R2 §35.3 (W14/report/rpt_gh.py) carries renewal as a cost "
              "in the year it occurs.")

    _check(d, "21.5   Check it yourself", [
        "Add the printed line items of any estimate and compare the sum with the "
        "printed total. In one of the NWS appraisals the printed sub-total, "
        "preliminaries and contingency sum to 32,637,940 OMR against a printed "
        "total of 33,066,420 OMR: the total had been refreshed and the lines had "
        "not (W9/analysis/W9_PIAD_financial_review.md, finding F7).",
        "Check that every rate carries its date and its escalation to the stated "
        "base date. A rate unchanged across two studies four years apart has been "
        "copied, not priced.",
        "Check that gravity sewer rates change with depth band as well as with "
        "diameter.",
        "Check that no option shares a structure, a station or a reservoir with "
        "another option, and that each carries the energy of its own pumping.",
        f"Check the connection quantity against the property count by year: "
        f"{F.fmt(props['y2030'])} by 2030 and {F.fmt(props['ultimate'])} at "
        f"saturation (design_flows.json, key properties).",
        "Check that the accuracy is stated as ± 20 % and that the physical and the "
        "price contingency are separate lines."])


# ============================================================ 22  FINANCIAL
def c22_financial(d):
    t, j, st, ps, ib = _live()
    ult = t["ultimate"]
    open_year = j["rules"]["opening_year"]
    conn = j["rules"]["connection_ratio_2030"]
    low = j["low_case_2030_m3d"]
    end_year = open_year + YEARS
    q_open, q_end, q_ult = t["q"][open_year], t["q"][end_year], t["q_ult"]
    a = _annuity()
    df_n = (1 + RATE) ** -YEARS
    pv_late = sum((1 + RATE) ** -k for k in range(4, YEARS + 1))
    tse_open, tse_ult = TSE_RATIO * q_open, TSE_RATIO * q_ult
    sl_open, sl_end = SLUDGE_KG_M3 * q_open, SLUDGE_KG_M3 * q_end

    D.h(d, 1, "22   Financial appraisal", page_break=True)
    D.p(d, "The estimate says what each option costs to build. The appraisal "
           "says what each costs to own for twenty-five years, in money of one "
           "date, so that options of different shapes can be compared. A scheme "
           "that is cheap to build and expensive to run can lose to one that is "
           "the reverse, and the appraisal is where that becomes visible.")
    D.picture(d, os.path.join(IMG, "appraisal_method.png"), 16.2)
    D.fig_caption(d, "The appraisal end to end. Each option is costed on three "
                     "streams, the streams are discounted together, and only then "
                     "are the options scored.")
    D.callout(d, "None of the formulae in this chapter comes from NWS.",
              "Net present value, life-cycle cost and carbon accounting are "
              "required by the general guideline, and none of them is written as "
              "an equation anywhere in it. Cite ISO 15686-5 for life-cycle cost and "
              "net present value, and ISO 14064 with the GHG Protocol for carbon "
              "(G201 p99). What NWS does fix is the discount rate, the period, the "
              "cost components and the decision rules.")

    # ------------------------------------------------------------------ 22.1
    D.h(d, 2, "22.1   The decision rule")
    _for(d, "One measure decides between options; the others inform. Saying which "
            "is which before any number exists stops the choice drifting toward "
            "whichever measure favours a preferred option.")
    _rule(d, f"Net present value and total life-cycle cost, at {RATE * 100:.0f} % "
             f"over {YEARS} years, decide. Payback is reported beside them and does "
             f"not decide. Total life-cycle cost is also the quantity the "
             f"{TIE * 100:.0f} % tie-break of Chapter 23 is measured on.")
    _src(d, "G201 §7.1 p57: the 25-year planning life is \"the period over which "
            "the NPV will be calculated for the purpose of comparing schemes for "
            "total lifetime cost analysis\". G201 §12.4 p96: NPV is applied to "
            "find the lowest total lifetime cost, at 5 % unless NWS instructs "
            "otherwise, calculated from the start of construction at current base "
            "prices. Payback reported but not deciding: project rule (engineer, "
            "2026-09-01).")
    _ibri(d, f"Even counted from the opening year {open_year}, the {YEARS}-year "
             f"window closes in {end_year}, when the study area generates "
             f"{F.fmt(q_end)} m³/d. The pipes are sized on the {F.fmt(q_ult)} m³/d "
             f"of saturation in {ult}, so inside the appraisal the network never "
             f"carries more than {q_end / q_ult * 100:.1f} % of its design flow. "
             f"Counted from the start of construction, as the guideline says, the "
             f"window closes earlier still. Capacity built for {ult} is partly idle "
             f"for the whole appraisal, which is why phasing moves the net present "
             f"value.")
    _where(d, "The rule: _BRAIN/07_PROJECT_STATE.md §2 item 1f; report R2 §35.4 "
              "(W14/report/rpt_gh.py). The flow by year: "
              "W14/analysis/W14_growth_by_settlement.xlsx, sheet \"Qadf by year "
              "m3d\".")

    # ------------------------------------------------------------------ 22.2
    D.h(d, 2, "22.2   Net present value and life-cycle cost")
    _for(d, "Capital, operating cost, renewal and benefit arise in different years. "
            "Discounting brings them to one date so they can be added.")
    _rule(d, "The net present value of an option is the sum of its net cash flows, "
             "each divided by the discount factor of its year:")
    eq = D.next_eq()
    M.display(d, M.seq(UP("NPV"), M.EQ,
                       M.nary("∑", M.seq(R("t"), M.EQ, R("0")), R("n"),
                              M.frac(M.sub(R("C"), R("t")),
                                     M.sup(M.delim(M.seq(R("1"), M.PLUS, R("r"))),
                                           R("t"))))), number=eq)
    _params(d, [
        ["NPV", "net present value of the option", "OMR"],
        ["C t", "net cash flow in year t: treated effluent income, charges and "
                "avoided cost, less capital, operating and renewal cost; residual "
                "value enters the final year as a credit", "OMR"],
        ["r", f"discount rate, {RATE:.2f} unless NWS instructs otherwise", "—"],
        ["t", "year, counted from the start of construction", "year"],
        ["n", f"appraisal period, {YEARS} years", "year"]])
    D.p(d, "Total life-cycle cost is the same sum taken over the cost streams "
           "alone: capital, operating, renewal and decommissioning, less residual "
           "value. It carries no benefit, so it can be compared between options "
           "whose benefits are the same, which is the case for options that meet "
           "the same functional requirement.")
    D.p(d, "A constant amount paid every year from year 1 to year n has a present "
           "value equal to the amount times the annuity factor:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("a"), R("n")), M.EQ,
                       M.frac(M.seq(R("1"), M.MINUS,
                                    M.sup(M.delim(M.seq(R("1"), M.PLUS, R("r"))),
                                          M.seq(R("−"), R("n")))), R("r"))),
              number=eq)
    _params(d, [["a n", "annuity factor: present value of one unit a year for n years", "year"]])
    _src(d, "neither equation is in PAM-GUD-201, -202 or -203; both are standard "
            "discounting as in ISO 15686-5. The rate and the period are G201 p96 "
            "and p57.")
    _ibri(d, f"At r = {RATE:.2f}, one rial spent in year {YEARS} is worth "
             f"{df_n:.3f} today, and a_{YEARS} = {a:.2f}. A flat operating cost of X "
             f"a year from year 1 is therefore worth {a:.2f} X, not {YEARS} X; "
             f"multiplying by {YEARS} overstates it {YEARS / a:.2f} times. If the "
             f"stream starts in year 4, after a construction period, its present "
             f"value is {pv_late:.2f} X and {YEARS} X overstates it "
             f"{YEARS / pv_late:.1f} times. And the Ibri stream is not flat: the "
             f"average flow grows from {F.fmt(q_open)} m³/d in {open_year} to "
             f"{F.fmt(q_end)} m³/d in {end_year}, {q_end / q_open:.2f} times, so "
             f"every cost that follows flow is built year by year, never as one "
             f"annual figure.")
    _where(d, "No appraisal model exists yet. The equation in client terms: report "
              "R2 §35.4 (W14/report/rpt_gh.py). The discounting arithmetic above "
              "is computed in this module from RATE and YEARS.")

    # ------------------------------------------------------------------ 22.3
    D.h(d, 2, "22.3   The cash flow to be built")
    _for(d, "The discounting is only as good as the cash flow it is applied to.")
    _rule(d, "For each option, a year-by-year cash flow across the appraisal "
             "period with the streams below.")
    D.tab_caption(d, "Streams of the cash flow")
    D.table(d, ["Stream", "Timing", "Note"], [
        ["Capital", "in the years each phase is built", "phased, never lumped at year zero"],
        ["Connections", "in the year each plot connects", "follows the property count by year"],
        ["Operating", "every year from commissioning", "follows the connected flow and grows with it"],
        ["Renewal", "instrumentation and control at 15 years, mechanical at 20, "
                    "electrical 15 to 50 (G201 Table 10, p57)",
         "at least one cycle falls inside the period"],
        ["Residual value", "final year, as a credit",
         "the life left beyond year 25 in civil works and pipework (50 years, "
         "G201 Table 10); ISO 15686-5 practice, to agree with NWS"],
        ["Decommissioning", "end of life", "named in the life-cycle scope (G201 p96)"],
        ["Benefits", "every year from commissioning", "treated effluent income, charges, avoided cost (22.5)"],
    ], widths=[3.2, 6.3, 7.0], font=9)
    D.p(d, "", space_after=2)
    D.callout(d, "Phasing is what makes the comparison honest.",
              "A central plant built in two phases and a set of local plants built "
              "as districts develop have very different cash-flow shapes, and "
              "discounting is sensitive to shape. Lumping the capital of both at "
              "year zero erases the difference the appraisal exists to reveal.",
              fill="EAF1F8", colour=D.MID)
    _src(d, "G201 §7.1 p57, Table 10 (the lives \"are used for financial asset "
            "depreciation calculations\"); G201 §12.4 p96 for the stages the "
            "life-cycle cost covers. Residual value is not named in the guideline.")
    _ibri(d, f"In the opening year {open_year} the fully connected flow would be "
             f"{F.fmt(q_open)} m³/d, but the early-year case carries the connection "
             f"ratio of {conn:.2f} and gives {F.fmt(low)} m³/d. The operating cost "
             f"and the benefits of the first years follow the connected flow, not "
             f"the full one.")
    _where(d, "The early-year flow: W14/analysis/design_flows.json, key "
              "low_case_2030_m3d, and rules.connection_ratio_2030.")

    # ------------------------------------------------------------------ 22.4
    D.h(d, 2, "22.4   Operating cost, built from duty")
    _for(d, "Operating cost is where options that look alike on capital come "
            "apart, so it has to be built from what each asset does.")
    _rule(d, "Each component is quantified from its driver. Operating cost is "
             "never taken as a percentage of capital: for a wastewater system "
             "energy and sludge dominate, and neither follows capital value.")
    D.tab_caption(d, "Operating cost components and their drivers")
    D.table(d, ["Component", "Driven by", "Basis and source"], [
        ["Power", "kWh a year: pump duty flow and head; aeration from oxygen demand",
         "**latest APSR tariff** (G201 p96)"],
        ["Labour and staffing", "posts and shift pattern", "per hour, day, month or year (G201 p96)"],
        ["Vehicles and equipment", "fleet", "per hour, day, month or year (G201 p96)"],
        ["Spare parts and consumables", "installed plant", "annual provision (G201 p96)"],
        ["Chemicals", "dose rate times flow treated", "where applicable (G201 p96)"],
        ["Maintenance and repairs", "asset type and condition", "annual provision (G201 p96)"],
        ["Sludge handling and disposal", "tonnes of dry solids a year", "treatment, haulage, gate fees (ours)"],
        ["Network cleansing", "pipes on the early-cleansing list", "jetting and CCTV by year (ours; Chapter 12)"],
        ["Monitoring", "sampling regime", "laboratory, odour, effluent compliance (ours)"],
    ], widths=[4.2, 6.2, 6.1], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "Power deserves attention twice. More than 80 % of NWS operational "
           "emissions come from electricity (G201 p99), so the energy line drives "
           "the operating cost and the carbon score together, and the two move in "
           "the same direction rather than trading off.")
    _src(d, "G201 §12.3 p96 lists the six components marked; the guideline says "
            "\"shall include, but not be limited to\". Duty-based, never a "
            "percentage of capital: project rule (engineer, 2026-09-01).")
    _ibri(d, f"At the indicative {SLUDGE_KG_M3} kg of sludge per m³ of inflow "
             f"(G201 p78) the plant makes {F.fmt(sl_open / 1000, 1)} t a day at the "
             f"{open_year} flow and {F.fmt(sl_end / 1000, 1)} t a day at the "
             f"{end_year} flow. The sludge line of the operating cost grows by the "
             f"same {q_end / q_open:.2f} times as the flow inside the window, and "
             f"the haulage is longer because the plant also receives other plants' "
             f"sludge.")
    _where(d, "Report R2 §35.3 (W14/report/rpt_gh.py). The early-cleansing list "
              "comes from the self-cleansing classes of the network run (Chapter "
              "12; W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §4).")

    # ------------------------------------------------------------------ 22.5
    D.h(d, 2, "22.5   Benefits: avoided cost comes first")
    _for(d, "A net present value needs the benefit side, and for a sewerage scheme "
            "that side is mostly money not spent.")
    _rule(d, "Three streams, each measured against a costed Option 0, do nothing:")
    D.numbered(d, "connection and sewerage charges, if NWS applies any, at the rate "
                  "it sets;", restart=True)
    D.numbered(d, "treated effluent sales: volume, offtaker and price set by NWS, "
                  "capped by irrigation demand and not by what the plant produces;")
    D.numbered(d, "avoided cost: tanker haulage of sewage to the plant, septic-tank "
                  "emptying, and the deferral of a new plant.")
    D.p(d, "For a sewerage scheme the third stream usually dominates, the opposite "
           "of a water-supply scheme where volumetric billing carries the case. "
           "Name each stream for what it is. A tariff margin or an avoided cost "
           "called revenue misleads every reader of the result. Option 0 is "
           "costed in full: continued tanker haulage to the existing plant, septic "
           "emptying, and the environmental and public-health consequences of no "
           "collection. Without it, an avoided cost has no baseline.")
    _src(d, "the guidelines carry no tariff, no revenue treatment and no "
            "avoided-cost rule. Treated effluent produced at 95 % of the inlet "
            "flow, G201 p73. The three streams and Option 0: project rule "
            "(engineer, 2026-09-01).")
    _ibri(d, f"At {TSE_RATIO * 100:.0f} % of the inflow the plant produces "
             f"{F.fmt(tse_open)} m³/d of treated effluent at the {open_year} flow "
             f"and {F.fmt(tse_ult)} m³/d at saturation. That is a ceiling on "
             f"effluent income, not a forecast of it; the sales volume comes from "
             f"the irrigation demand of Chapter 19. The avoided tanker haulage "
             f"cannot be put in figures yet: no filling-station or delivery record "
             f"is held, and no tanker flow is carried in any design flow.")
    _where(d, "The tanker status: design_flows.json, rules.tankers. The revenue "
              "problem for a sewerage scheme: W9/analysis/W9_PIAD_financial_review.md, "
              "last section.")

    # ------------------------------------------------------------------ 22.6
    D.h(d, 2, "22.6   Payback: reported, not deciding")
    _for(d, "NWS reads an investment case by its payback, so it is reported.")
    _rule(d, "Report the discounted payback: the first year in which the "
             "cumulative discounted net cash flow reaches zero. Do not rank options "
             "on it. It ignores everything after that year, and on a sewerage "
             "scheme a payback built on revenue alone leaves out most of the "
             "benefit.")
    _src(d, "project rule (engineer, 2026-09-01). Payback is not mentioned in "
            "G201 §12.")
    D.p(d, "Worked example from an NWS appraisal. The published paybacks of one "
           "water-supply appraisal were reproduced to the month by its own "
           "formula, yet it billed a peak-day volume that included losses, with "
           "the domestic and non-domestic split inverted: annual income was "
           "overstated 2.09 times, and the recommended option's 17 months became "
           "about 36 once corrected. A payback is exactly as good as the volume "
           "it is billed on.")
    _where(d, "W9/analysis/W9_PIAD_financial_review.md, findings F1 and F2.")

    # ------------------------------------------------------------------ 22.7
    D.h(d, 2, "22.7   Sensitivity")
    _for(d, "A ranking that flips under a plausible change of input is not a "
            "recommendation, and sensitivity is how that is found out.")
    _rule(d, "The multi-criteria analysis is rerun varying exactly three things:")
    D.numbered(d, "the weighting between the categories under evaluation;", restart=True)
    D.numbered(d, "the discount rate applied to calculate the net present value;")
    D.numbered(d, "the input design criteria, for example a reduction in demand.")
    _src(d, "G201 §12.8 pp 105–106.")
    _ibri(d, f"The third is the one that bites here. The early-year flow rests on "
             f"a connection ratio ({F.fmt(low)} m³/d in {open_year} against "
             f"{F.fmt(q_open)} fully connected), the saturation year rests on the "
             f"capacity of the empty plots ({F.fmt(t['capacity'])} people) rather "
             f"than on a forecast, and no tanker or private-well water is in any "
             f"flow. A sensitivity run that does not move the flow is not testing "
             f"the input most likely to be wrong.")
    _where(d, "The inputs: design_flows.json (low_case_2030_m3d, "
              "rules.connection_ratio_2030); the capacity: "
              "W14/analysis/settlements_today.csv, column FUT_CAP_POP.")

    # ------------------------------------------------------------------ 22.8
    D.h(d, 2, "22.8   Risk")
    D.p(d, "The designer identifies the risks, such as regulatory change, climate "
           "impact and technology obsolescence (G201 §12.8 p105), and carries a "
           "register from concept onward. For the appraisal each risk needs a "
           "likelihood, an impact in money or time, and an owner; the "
           "risk-adjusted cost then sits beside the base estimate. The NWS risk "
           "model scores likelihood and impact on a five-by-five matrix, "
           "separately for investment and delivery risk. Score every option, the "
           "recommended one included: in one NWS appraisal the recommended option "
           "scored zero because it was never assessed. Risks that fall on one "
           "option and not another are the ones that change the ranking.")
    _where(d, "W9/analysis/W9_PIAD_financial_review.md, finding F6 and §6; report "
              "R2 §36 (W14/report/rpt_gh.py).")

    # ------------------------------------------------------------------ 22.9
    D.h(d, 2, "22.9   How appraisals of this kind go wrong")
    D.p(d, "Two NWS pre-investment appraisals were read line by line against their "
           "own workbooks. The faults found are not unusual, and each is worth "
           "checking for deliberately.")
    D.tab_caption(d, "Faults found in two NWS appraisals, and what to do instead")
    D.table(d, ["Fault", "What to do instead"], [
        ["Revenue billed on a peak-day volume that includes losses",
         "Bill on the average day and on billable volume only; losses are "
         "non-revenue by definition"],
        ["The split between customer categories taken from the wrong place, so "
         "the high tariff falls on most of the volume",
         "Take the split from the land-use allocation that sized the network, and "
         "check it against the demand table"],
        ["Alternatives that differ from the preferred option in one quantity, "
         "sharing its structures and omitting their own pumping",
         "Cost each option as designed, with its own plant, storage and energy"],
        ["Operating cost as a percentage of capital, with energy and labour at zero",
         "Build operating cost from duty; for wastewater, energy and sludge dominate"],
        ["Annual operating cost multiplied by the period and called a lifetime cost",
         "Discount it; at 5 % the plain multiplication overstates a 25-year stream "
         "by a factor between about 1.8 and 2.2, depending on when it starts"],
        ["A tariff margin or an avoided cost described as revenue",
         "Name each stream, and state the baseline it is measured against"],
        ["Unit rates carried forward unchanged from an earlier study",
         "Escalate to a stated base date, and say which"],
        ["The recommended option left out of the risk assessment",
         "Score every option, the recommended one included"],
    ], widths=[7.4, 9.1], font=9)
    D.p(d, "", space_after=2)
    D.p(d, "None of these changed the ranking in the appraisals reviewed: rebuilt "
           "on the guideline basis, the recommended option still led on life-cycle "
           "cost by 27.8 % against its nearest rival. They would change it in a "
           "close case, and they change every absolute figure that a budget, a "
           "tariff submission or a board paper depends on.")
    _where(d, "W9/analysis/W9_PIAD_financial_review.md §3 and §4; "
              "_BRAIN/07_PROJECT_STATE.md §2 item 1g.")

    # ----------------------------------------------------------------- 22.10
    D.h(d, 2, "22.10   What the appraisal must produce")
    for line in ("capital cost by option and by phase",
                 "operating cost by option and by year",
                 f"net present value and total life-cycle cost of each option at "
                 f"{RATE * 100:.0f} % over {YEARS} years",
                 "discounted payback, reported as an indicator",
                 "carbon in tonnes of CO₂ equivalent a year and per cubic metre, "
                 "against the NWS benchmark (G201 p99)",
                 "in-country value, assessed at this stage in outline",
                 "the sensitivity results on all three variables",
                 "a risk register with costed impacts, every option scored",
                 "the input to the NWS pre-investment appraisal document"):
        D.bullet(d, line)

    _check(d, "22.11   Check it yourself", [
        f"Recompute a_{YEARS} at {RATE * 100:.0f} %: (1 − 1.05⁻²⁵) / 0.05 = "
        f"{a:.2f}. Any lifetime operating cost equal to {YEARS} times the annual "
        f"figure has not been discounted.",
        "Check that the cash flow starts at the start of construction, as G201 p96 "
        "requires, and that capital is spread over the construction years.",
        "Check that at least one replacement of mechanical plant and of "
        "instrumentation and control falls inside the period.",
        "Check that every benefit is named as income, charge or avoided cost, and "
        "that each avoided cost has its Option 0 line.",
        "Check that the sensitivity moves the flow, not only the weights and the "
        "rate.",
        f"Check the operating cost of the first years against the early-year flow, "
        f"{F.fmt(low)} m³/d in {open_year}, not against the fully connected "
        f"{F.fmt(q_open)} m³/d."])


# ============================================================== 23  OPTIONS
def c23_options(d):
    t, j, st, ps, ib = _live()
    ult = t["ultimate"]
    open_year = j["rules"]["opening_year"]
    ib_ult = next(s for s in j["settlements"] if s["key"] == "IBRI")["q_ult"]
    small = sorted([s for s in j["settlements"] if s["q_ult"] <= CW_M3D],
                   key=lambda s: -s["q_ult"])
    small_pop = sum(s["pop_ult"] for s in small)
    small_txt = ", ".join(f"{s['settlement']} ({F.fmt(s['q_ult'])})" for s in small)
    tse_open, tse_ult = TSE_RATIO * t["q"][open_year], TSE_RATIO * t["q_ult"]
    co2_open, co2_ult = tse_open * 365 * CO2_TSE, tse_ult * 365 * CO2_TSE

    D.h(d, 1, "23   Options and the recommendation", page_break=True)
    D.p(d, "The guideline requires the designer to present options and choose "
           "between them systematically. This chapter covers how many options, of "
           "what kind, the criteria they are scored on, who sets the weights, and "
           "the rule that decides between two options that cost nearly the same.")
    D.picture(d, os.path.join(IMG, "F9_options.png"), 15.5)
    D.fig_caption(d, "Options appraisal. Where total lifetime costs sit within ten "
                     "per cent, the greener option is adopted.")

    # ------------------------------------------------------------------ 23.1
    D.h(d, 2, "23.1   How many options")
    _for(d, "Enough genuinely different options that the recommendation is a "
            "choice, not a confirmation.")
    _rule(d, "At least three options for each system: the sewer network, the "
             "treated effluent network and the treatment plant, and three for each "
             "plant if more than one plant is proposed. Lifting stations are not a "
             "separate set; their number follows from the network layout, and "
             "they are compared inside it. Every option meets the same functional "
             "requirements and specification, with similar reliability and "
             "redundancy, so that the comparison is not biased by scope.")
    _src(d, "G201 §12 and §12.1, p95: \"a minimum of three (3) design options\" "
            "and \"equivalent functional requirements and specifications with "
            "similar levels of reliability and redundancy\". Three per system and "
            "per plant, and lifting stations inside the network options: project "
            "rule (engineer, 2026-08-31).")
    _ibri(d, f"At saturation the study area produces {F.fmt(t['q_ult'])} m³/d and "
             f"Ibri town alone {F.fmt(ib_ult)} m³/d, both at or above the "
             f"{F.fmt(LARGE_STP)} m³/d of a Large plant (G203 p65). Splitting the "
             f"load between plants therefore still leaves at least one Large plant, "
             f"and every plant proposed brings its own three options into the "
             f"comparison.")
    _where(d, "_BRAIN/07_PROJECT_STATE.md §2 item 1e; report R2 §21.1 "
              "(W14/report/rpt_ef.py); flows by settlement in design_flows.json.")

    # ------------------------------------------------------------------ 23.2
    D.h(d, 2, "23.2   Three archetypes")
    _for(d, "Three variants of one scheme are a sensitivity test, not an options "
            "appraisal. The archetypes force the options apart.")
    _rule(d, "The guideline names the kind of option to be included, as guidance:")
    D.numbered(d, "an option that pushes the environmental sustainability ambitions "
                  "of NWS and the Sultanate, including nature-based solutions;",
               restart=True)
    D.numbered(d, "an international best-in-class, state-of-the-art solution;")
    D.numbered(d, "a standard solution based on current practice and technology "
                  "established in Oman.")
    D.p(d, "The guideline names them and stops. What distinguishes them in design "
           "terms is ours, set out below and offered to NWS for comment; it is "
           "never presented as a guideline requirement.")
    D.tab_caption(d, "Proposed meaning of the three archetypes in design terms")
    D.table(d, ["", "Sustainability-led", "International best practice",
                "Established local practice"], [
        ["Network", "Gravity maximised, accepting deeper excavation to avoid pumping",
         "Layout optimised by model, pumping where it lowers whole-life cost",
         "Conventional layout, pumping where the ground requires"],
        ["Treatment", "Lower-energy process; nature-based polishing where the scale "
                      "permits", "Highest-performing process, smallest footprint",
         "Process established in Oman, simple to run and maintain"],
        ["Energy", "Generation on site, with a self-sufficiency target",
         "High-efficiency plant and advanced process control",
         "Grid supply with standby generation"],
        ["Reuse", "Reuse maximised, wadi discharge minimised",
         "High reuse at high effluent quality",
         "Reuse to the demand identified, surplus discharged"],
        ["Materials", "Low-carbon and locally sourced where performance permits",
         "Specified for performance and durability", "Standard specification"],
        ["Consequence", "Higher capital, lowest carbon and operating cost",
         "Highest capital, least land, best effluent",
         "Lowest capital, most land, highest operating cost"],
    ], widths=[2.4, 4.8, 4.7, 4.6], font=8.5)
    D.p(d, "", space_after=2)
    D.p(d, "One limit binds the first archetype. Constructed wetlands are "
           "recommended only for small plants in rural areas, approximately up to "
           f"{F.fmt(CW_M3D)} m³/d or {F.fmt(CW_PE)} population equivalent (G203 "
           "p101). Nature-based treatment therefore serves outlying settlements or "
           "polishing, never the main plant.")
    _src(d, "G201 §12.1 p95 for the archetypes; G203 §10.5 p101 for the wetland "
            "limit. The design-terms table: report R2 §21.2, our interpretation.")
    _ibri(d, f"{len(small)} of the {len(j['settlements'])} settlements stay at or "
             f"under {F.fmt(CW_M3D)} m³/d even at saturation: {small_txt} m³/d. "
             f"Together they house {F.fmt(small_pop)} people in {ult}, "
             f"{small_pop / t['pop_ult'] * 100:.1f} % of the study area, and each "
             f"is under {F.fmt(CW_PE)} people. That is the whole field on which a "
             f"wetland can treat a settlement's sewage outright; everywhere else "
             f"nature-based treatment can only polish.")
    _where(d, "design_flows.json, key settlements (q_ult, pop_ult); report R2 "
              "§21.2 (W14/report/rpt_ef.py).")

    # ------------------------------------------------------------------ 23.3
    D.h(d, 2, "23.3   Seven criteria, and who weights them")
    _for(d, "Cost alone does not choose. The criteria bring in what the money "
            "does not show.")
    _rule(d, "Each option is assessed on the parameters of G201 §12 (capital and "
             "operating cost, life-cycle cost, carbon over the lifetime, resource "
             "efficiency under a circular economy including decommissioning, "
             "in-country value, and the degree of nature-based solution), over 25 "
             "years. A weighted multi-criteria analysis then compares the options "
             "on seven criteria:")
    for k, c in enumerate(("total lifetime cost",
                           "sustainability: carbon footprint, circular economy, "
                           "nature-based solutions",
                           "social development and in-country value",
                           "adaptability and resilience",
                           "operability",
                           "constructability",
                           "environmental impact")):
        D.numbered(d, c, restart=(k == 0))
    D.p(d, "NWS sets the weights. The guideline specifies no scoring scale, no "
           "normalisation and no rule for combining the scores, so the method is "
           "proposed and agreed before any option is scored. The simplest form, "
           "and the one proposed, is a weighted sum:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("S"), R("j")), M.EQ,
                       M.nary("∑", M.seq(R("k"), M.EQ, R("1")), R("7"),
                              M.seq(M.sub(R("w"), R("k")), M.sub(R("s"), UP("jk")))),
                       R(",     "),
                       M.nary("∑", M.seq(R("k"), M.EQ, R("1")), R("7"), M.sub(R("w"), R("k"))),
                       M.EQ, R("1")), number=eq)
    _params(d, [
        ["S j", "weighted score of option j", "—"],
        ["w k", "weight of criterion k, set by NWS", "—"],
        ["s jk", "score of option j on criterion k, on a scale agreed with NWS", "—"]])
    D.p(d, "Carbon is expressed in tonnes of CO₂ equivalent a year and per cubic "
           "metre, with all Scope 1 and Scope 2 emissions and Scope 3 for the "
           "significant elements (G201 p99). Nature-based solutions are measured "
           "by the carbon of the conventional materials they avoid (G201 p104).")
    _src(d, "G201 §12 p95 (parameters, the 25 years, NWS weights), §12.6 pp "
            "104–105 (the seven criteria), p99 (carbon). The weighted-sum form is "
            "not in the guidelines; it is ours, to be agreed with NWS.")
    _ibri(d, f"The benchmark each option's carbon is set against: at "
             f"{CO2_TSE * 1000:.2f} × 10⁻³ t CO₂e per m³ of treated effluent "
             f"(G201 p99), the {F.fmt(tse_open)} m³/d produced at the {open_year} "
             f"flow corresponds to {F.fmt(co2_open)} t CO₂e a year, and the "
             f"{F.fmt(tse_ult)} m³/d at saturation to {F.fmt(co2_ult)} t CO₂e a "
             f"year. An option that beats those figures is better than the NWS "
             f"average; one that does not has to say why.")
    _where(d, "Report R2 §21.3–21.4 (W14/report/rpt_ef.py) and §34 "
              "(W14/report/rpt_gh.py). No scoring sheet exists yet.")

    # ------------------------------------------------------------------ 23.4
    D.h(d, 2, "23.4   Sensitivity of the ranking")
    D.p(d, "The ranking is rerun under each of the three sensitivity variables of "
           "Section 22.7: the weights, the discount rate and the design inputs. "
           "An option that wins under one set of weights only is a fragile "
           "recommendation, and the report says so. The weights are NWS's to set, "
           "so the sensitivity on weights is also the evidence NWS needs to set "
           "them knowingly.")

    # ------------------------------------------------------------------ 23.5
    D.h(d, 2, "23.5   The tie-break")
    _for(d, "Where two options cost nearly the same, the guideline decides for the "
            "greener one, which makes the sustainability work decisive rather than "
            "decorative.")
    _rule(d, "If equivalent options are within 10 % on total lifetime cost, the "
             "more sustainable option is adopted. The sentence leaves three things "
             "open, and each is fixed here as a proposal to NWS:")
    D.bullet(d, "the gap is measured against the lowest total lifetime cost, "
                "which gives the larger percentage and so the stricter test;",
             lead="Base: ")
    D.bullet(d, "the option with the better sustainability score of the "
                "multi-criteria analysis (carbon, circular economy, nature-based "
                "solutions);", lead="More sustainable: ")
    D.bullet(d, "inside the band the tie-break overrides the weighted score; "
                "outside it the weighted score decides.", lead="Order: ")
    eq = D.next_eq()
    M.display(d, M.seq(M.frac(M.seq(M.sub(UP("LCC"), R("j")), M.MINUS,
                                    M.sub(UP("LCC"), UP("min"))),
                              M.sub(UP("LCC"), UP("min"))),
                       R(" ≤ "), R(f"{TIE:.2f}")), number=eq)
    _params(d, [
        ["LCC j", "total lifetime cost of option j, present value", "OMR"],
        ["LCC min", "the lowest total lifetime cost among the equivalent options", "OMR"]])
    _src(d, "G201 §12.9 p106: \"If equivalent options are within 10% Total "
            "Lifetime Cost, the more sustainable option will be adopted.\" The "
            "base, the meaning of more sustainable and the order: ours, to agree "
            "with NWS.")
    D.p(d, f"The base matters only in a close case, and a close case is exactly "
           f"where the rule applies. Two options whose costs differ by a factor of "
           f"{1 + TIE:.2f} are {TIE * 100:.1f} % apart measured on the cheaper one "
           f"and {TIE / (1 + TIE) * 100:.1f} % apart measured on the dearer one. "
           f"Between those two figures the verdict depends on the base, so the "
           f"report states which base it used.")
    D.p(d, "Worked example from an NWS appraisal, rebuilt on the guideline basis: "
           "the winner's total lifetime cost was 34,047,919 OMR against 47,135,167 "
           "OMR for the nearest rival. That is 38.4 % above the winner, or 27.8 % "
           "below the rival; outside the band on either base, so cost decided. "
           "Three options costed over 25 years often land far closer than that, "
           "and then the sustainability scoring decides the outcome.")
    _where(d, "Report R2 §21.4 (W14/report/rpt_ef.py); _BRAIN/07_PROJECT_STATE.md "
              "§2 item 1e; the worked example: "
              "W9/analysis/W9_PIAD_financial_review.md §4.")

    # ------------------------------------------------------------------ 23.6
    D.h(d, 2, "23.6   Value engineering")
    D.p(d, "A project estimated under OMR 5 million takes a general value "
           "engineering review by the design team at concept. At OMR 5 million or "
           "more, a formal study by an independent certified consultant is "
           "required at concept and at preliminary design. The table's footnote "
           "lowers that threshold for any sewage treatment plant or pumping "
           "station worth more than OMR 2 million (G201 Table 27, p93).")
    D.callout(d, "Formal value engineering falls inside the concept programme.",
              f"A Large plant of the order of {F.fmt(t['q_ult'])} m³/d is expected to "
              f"clear the OMR 2 million footnote by a wide margin, so an independent certified value "
              f"engineering consultant is appointed within the concept stage, and "
              f"again at preliminary design. At concept the study reviews the "
              f"alternatives and builds agreement on the direction (G201 §11.3.2 "
              f"p93), so it belongs before the options are fixed, not after.")
    _where(d, "Report R2 §37 (W14/report/rpt_gh.py).")

    # ------------------------------------------------------------------ 23.7
    D.h(d, 2, "23.7   The recommendation and the roadmap")
    D.p(d, "The recommendation is the optimum solution on the whole analysis, with "
           "the tie-break applied (G201 §12.9 p106). For the recommended option "
           "the designer then prepares an implementation roadmap: the scope of the "
           "later design stages, the procurement strategy, in particular whether "
           "the works are designed by the designer or by an EPC contractor, the "
           "phasing, and a framework for monitoring performance.")
    _where(d, "Report R2 §38–39 (W14/report/rpt_gh.py); the appraisal figure: "
              "W9/py/make_appraisal_figure.py.")

    _check(d, "23.8   Check it yourself", [
        "Count the options per system and per plant. Fewer than three anywhere is "
        "non-compliant with G201 p95.",
        "Put the options side by side and check that their functional "
        "requirement, effluent standard and redundancy are the same. A cheaper "
        "option that delivers less is not an option.",
        "Check that no option is the preferred option with one quantity changed; "
        "each carries its own structures and pumping.",
        "Check that the weights came from NWS in writing, and that the scoring "
        "scale was agreed before the scoring.",
        "Recompute the gap between the two cheapest options against the cheaper "
        "one. If it is at or under 10 %, check that the greener option was "
        "adopted and that the report says why.",
        f"Check that any wetland option serves a settlement under "
        f"{F.fmt(CW_M3D)} m³/d at saturation (design_flows.json, q_ult)."])


# =============================================================== 24  LIMITS
def c24_limits(d):
    t, j, st, ps, ib = _live()
    ult = t["ultimate"]
    rules = j["rules"]
    conn = rules["connection_ratio_2030"]
    low = j["low_case_2030_m3d"]
    wrong = t["q_ult"] * conn
    q_dwell = F.RET_DOM * F.LPCD * ib["or_used"]            # l/d, one Ibri dwelling
    n_dwell = Q_MARA / (q_dwell / 86400.0)
    s_ls = K_LS * TAU_INTERIM ** 1.23 * Q_MARA ** -0.461 * 1000    # mm/m, l/s constant (comparison only)
    s_m3 = K_M3S * TAU_INTERIM ** 1.23 * (Q_MARA / 1000) ** -0.461 * 1000   # mm/m, the constant used
    k_conv, k_gap = _k_conv(), _k_gap()
    area_or = t["pop_today"] / ps["properties"]
    cap_or = max(r["or_used"] for r in st)
    n_small = sum(1 for r in st if r["small"])
    census = sum(r["workbook_2024"] for r in st)
    # the census-to-2024 difference, split by the rule that makes it
    dpop = [(r["small"], r["people_today"] - r["workbook_2024"]) for r in st]
    floor_up = [x for s, x in dpop if not s and x > 0.5]      # occupancy floor, 1,000 people or more
    cap_dn = [-x for s, x in dpop if not s and x < -0.5]      # occupancy cap, 1,000 people or more
    small_up = [x for s, x in dpop if s and x > 0.5]          # under-1,000 rule, occupancy set to the floor
    small_dn = [-x for s, x in dpop if s and x < -0.5]
    recon_pop = (f"{F.fmt(t['pop_today'])}: the floor adds {F.fmt(sum(floor_up))} in "
                 f"{_plural(len(floor_up), 'settlement')}; the under-1,000 rule adds "
                 f"{F.fmt(sum(small_up))} in {len(small_up)} and removes "
                 f"{F.fmt(sum(small_dn))} in {len(small_dn)}")
    if cap_dn:
        recon_pop += (f"; the cap removes {F.fmt(sum(cap_dn))} in "
                      f"{_plural(len(cap_dn), 'settlement')}")
    workers = sum(F.WORKERS.values())
    free = j["free_meters"]

    D.h(d, 1, "24   Where the guidelines cannot be relied on", page_break=True)
    D.p(d, "A reference that presents its source as flawless is not usable. "
           "Everything in this chapter was checked at the page. Where the "
           "guideline is wrong, this tutorial reproduces what it prints and says "
           "what is wrong with it; it never silently corrects the client's own "
           "standard. The chapter then sets out where this project departs from "
           "the guidelines, what is still waiting for data, and how the numbers "
           "compare with the Inception Report.")

    # ------------------------------------------------------------------ 24.1
    D.h(d, 2, "24.1   Formulae that are not in the guidelines")
    D.p(d, "Each of these is commonly assumed to be in the guidelines and is not. "
           "Citing NWS for any of them would be a fabricated reference.")
    D.tab_caption(d, "Formulae to cite elsewhere")
    D.table(d, ["Formula", "Cite instead", "What NWS does supply"], [
        ["Net present value", "ISO 15686-5", "5 % discount rate, 25-year period (G201 p96, p57)"],
        ["Life-cycle cost", "ISO 15686-5", "the list of cost stages (G201 p96)"],
        ["Carbon footprint", "ISO 14064, GHG Protocol", "units and benchmark values (G201 p99)"],
        ["Multi-criteria score", "designer's own, agreed with NWS", "the criteria and who weights them (G201 p95, p105)"],
        ["Payback", "standard finance", "nothing"],
        ["Total dynamic head", "standard hydraulics", "the component list, in prose"],
        ["Pump power", "standard hydraulics", "nothing; no efficiency assumption"],
        ["Darcy-Weisbach", "standard form", "roughness values only (G202 p104)"],
        ["Hazen-Williams", "standard form", "C values only"],
        ["Wave celerity", "Korteweg", "a qualitative description"],
        ["Mass load from flow and concentration", "standard", "loads and concentrations separately"],
        ["Oxygen demand, sludge age, clarifier area", "Metcalf and Eddy, or DWA", "ranges to land inside (G203 p75, p102)"],
        ["Surge vessel volume", "none", "a 20 % minimum allowance (G201 p147)"],
        ["Emergency storage at a pumping station", "none", "nothing; propose and obtain approval"],
        ["Roughness of a raw sewage force main", "none", "potable and treated effluent values only"],
        ["Minimum low flow for self-cleansing", "Mara, Sleigh and Taylor", "nothing (24.4)"],
        ["Aquifer recharge criteria", "none", "absent from all three documents"],
    ], widths=[5.2, 4.6, 6.7], font=8.5)
    D.p(d, "", space_after=2)
    _where(d, "TUTORIALS/T03_R01/EQUATION_REGISTER.md Part 2, updated; Appendix "
              "A.2 points back to this table rather than repeating it.")

    # ------------------------------------------------------------------ 24.2
    D.h(d, 2, "24.2   A mandatory method that cannot be completed: tractive force")
    _for(d, "At the head of a system the flow is too small to reach the "
            "self-cleansing velocity, and the tractive-force gradient is the only "
            "defence against silting.")
    _rule(d, "Two approaches shall be used for the sediment-carrying capacity of a "
             "sewer: the self-cleansing velocity and the minimum tractive force. "
             "The steeper of the two gradients is adopted as the minimum. At the "
             "head of a system, where the velocity cannot be reached, the gradient "
             "is set by the tractive force alone:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("S"), UP("min")), M.EQ, R("K"),
                       M.sup(R("τ"), R("1.23")), M.sup(R("Q"), R("−0.461"))),
              number=eq)
    _params(d, [
        ["S min", "minimum gradient", "m/m"],
        ["K", f"coefficient, {K_M3S_TXT} with Q in m³/s (G203 p27); the "
              f"guideline's second constant, for Q in l/s, is discussed below", "—"],
        ["τ", "tractive tension the flow must exert on the wall", "Pa"],
        ["Q", "peak flow in the pipe", "m³/s"]])
    D.callout(d, "The value of τ is not in the guidelines.",
              "The check is mandatory and the equation is given, but no value of "
              "tractive tension in pascals appears anywhere in the wastewater "
              "guideline's 201 pages or the general guideline's 152. Any value "
              "used comes from the literature and must be agreed with NWS in "
              "writing. This is the largest hole in the gravity design chain.")
    _src(d, "G203 §4.2.2.1 pp 25–27; the equation and K at p27, printed only as an "
            "image. No τ in G203 or G201: open item GAP-9. Interim handling: τ is "
            "a parameter; 1 Pa (Mara literature) is tagged [GAP-9] wherever it is "
            "used, never quoted as an NWS value.")
    _ibri(d, f"At τ = {TAU_INTERIM:.0f} Pa [GAP-9] and the {Q_MARA} l/s low flow "
             f"[outside assumption, 24.4], entered as {Q_MARA / 1000:.4f} m³/s with "
             f"K = {K_M3S_TXT}, S min = {s_m3:.2f} mm/m: flatter than the "
             f"{S_DN200:.2f} mm/m minimum for a DN200 sewer in G203 Table 11 (p29). "
             f"At that τ a DN200 laid at its G203 Table 11 minimum already meets "
             f"the tractive test; at a higher τ it may not. The exponent makes τ "
             f"decisive: doubling it multiplies S min by 2^1.23 = {2 ** 1.23:.2f}, "
             f"to {s_m3 * 2 ** 1.23:.1f} mm/m. The count of pipes in each "
             f"self-cleansing class swings with a number nobody has fixed, which "
             f"is why the classes are always reported against the τ used.")
    D.p(d, f"Two cautions on the formula itself. G203 p27 prints two coefficients, "
           f"{K_M3S_TXT} for Q in m³/s and {K_LS_TXT} for Q in l/s, and they agree "
           f"only to {k_gap:.1f} %: restated for Q in l/s, {K_M3S_TXT} becomes "
           f"{k_conv * 1000:.2f} × 10⁻³, not {K_LS_TXT}. The l/s constant therefore "
           f"gives gradients {k_gap:.1f} % flatter; in the example above it gives "
           f"{s_ls:.2f} mm/m instead of {s_m3:.2f}. This tutorial uses K = "
           f"{K_M3S_TXT} with Q in m³/s everywhere, which gives the steeper "
           f"gradient and so errs on the safe side. That choice is recommended in "
           f"the design-flow handoff, to be confirmed by the engineer. And the "
           f"formula assumes a flow depth of 0.2 D and n = 0.013; outside those it "
           f"is an approximation.")
    _where(d, "_BRAIN/05_GAPS.md, GAP-9; _BRAIN/02_DESIGN_CRITERIA.md, \"Min "
              "tractive force method\"; design_flows.json, "
              "rules.tractive_tension and rules.open_rulings_recommended.mara_constant; "
              "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §4 (the four classes) and §8 "
              "(the constant).")

    # ------------------------------------------------------------------ 24.3
    D.h(d, 2, "24.3   Errors of substance")
    D.p(d, "The defects below change a number or make a clause unusable. The full "
           "register of twenty-eight is in Appendix A.")
    D.tab_caption(d, "Errors of substance in the guidelines")
    D.table(d, ["Where", "What is wrong", "How to handle it"], [
        ["G203 p24", "full-bore flow printed as velocity divided by area, which is "
                     "dimensionally impossible", "use velocity times area; note the defect"],
        ["G201 p72", "Peltier printed with 1 in the numerator; the published form "
                     "carries 2.5", "reproduce as printed; query NWS"],
        ["G201 p62", "Adh Dhahirah tanker ratio of 333 % cannot be true; the "
                     "volumes are sound", "do not use the ratio; query NWS"],
        ["G201 p144", "pipeline emptying time evaluates to m^1.5·s², not seconds",
         "the guideline calls it a quick check; use a transient model"],
        ["G203 p25", "Manning constant 6.3448 against an exact 6.3496",
         "quote the guideline value; footnote the exact one"],
        ["G203 p40 / p42", "two tables disagree on duty pumps for the largest "
                           "station type", "take the conservative reading; flag"],
        ["G203 p146", "aerobic digestion text requires 45 days; its own table "
                      "gives 10 to 15", "the text governs; note the conflict"],
        ["G203 p124", "clarifier surface loading and overflow rate do not "
                      "reconcile, both at average flow", "reproduce both; do not pick one silently"],
        ["G203 p185", "hydrogen sulphide risk bands overlap and leave a gap",
         "reproduce verbatim; flag"],
        ["G203 p71", "chlorine residual worded as \"at least between\"",
         "0.3 to 1.0 at the consumer; up to 3.0 at the plant"],
    ], widths=[2.6, 8.0, 5.9], font=8.5)
    D.p(d, "", space_after=2)

    # ------------------------------------------------------------------ 24.4
    D.h(d, 2, "24.4   The 1.5 l/s low-flow threshold")
    _for(d, "A pipe whose flow is too small for either self-cleansing test is "
            "neither regraded nor upsized; it goes on the flushing list. Some "
            "threshold has to say when the flow is too small.")
    _rule(d, f"Below a peak flow of {Q_MARA} l/s on the early-year case, a pipe "
             f"that passes neither test is classed early cleansing and flagged for "
             f"flushing, not upsized; the DN200 minimum governs its size.")
    _src(d, "not in PAM-GUD-203: the whole document was searched on 2026-09-11. "
            "It is the minimum peak flow of the Mara simplified-sewerage "
            "literature, a WC flush, which G203 cites only for the tractive-slope "
            "formula (p27). G203 §4.2.6 p28 asks for more frequent inspection and "
            "cleansing of pipes that cannot self-cleanse and gives no threshold. "
            "Tagged outside assumption; to be confirmed with NWS.")
    _ibri(d, f"One Ibri dwelling at the settlement's occupancy of "
             f"{ib['or_used']:.2f} returns {F.RET_DOM} × {F.LPCD:.0f} × "
             f"{ib['or_used']:.2f} = {F.fmt(q_dwell)} l/d, or "
             f"{q_dwell / 86400:.4f} l/s. Unpeaked and fully connected, a pipe "
             f"needs about {F.fmt(n_dwell)} such dwellings upstream before its "
             f"average flow alone reaches {Q_MARA} l/s; peaking lowers that count, "
             f"the connection ratio of {conn:.2f} raises it. Either way, the "
             f"threshold decides how many pipe heads land on the flushing list.")
    _where(d, "design_flows.json, rules.low_flow_1_5_l_s; "
              "_BRAIN/02_DESIGN_CRITERIA.md, \"1.5 L/s is NOT in PAM-GUD-203\".")

    # ------------------------------------------------------------------ 24.5
    D.h(d, 2, "24.5   Cross-references that do not resolve")
    D.bullet(d, "the Terms of Reference cite item 2.1 of Section 05 of the "
                "wastewater manual, which no longer exists after the March 2026 "
                "renumbering; the content is now §10.1")
    D.bullet(d, "a package-plant peak factor of 3.0 is attributed to the general "
                "guideline, which nowhere prints 3.0 (G203 p97)")
    D.bullet(d, "two internal references to the tanker discharge section point to "
                "the wrong subsection; it is §10.6.2 (G203 p73, p83)")
    D.bullet(d, "the general guideline is cited as AM-GUD rather than PAM-GUD "
                "(G203 p51, p65)")
    D.bullet(d, "value engineering timing is concept in one table and detailed "
                "design only in another (G201 p93 against p20)")
    D.bullet(d, "environmental impact assessment timing is scoping at preliminary "
                "in one clause and a full assessment at concept in another (G201 "
                "p19 against p44)")

    # ------------------------------------------------------------------ 24.6
    D.h(d, 2, "24.6   Departures from the guidelines")
    _for(d, "Where the data held cannot support the guideline's method, the "
            "method used instead is declared, with the reason, so that NWS can "
            "confirm it rather than discover it.")
    _rule(d, "Every departure is stated in the report with the guideline position, "
             "the position adopted and the reason, and confirmation is requested.")
    D.tab_caption(d, "Departures and the positions adopted")
    D.table(d, ["Subject", "Guideline position", "Position adopted", "Reason"], [
        ["Occupancy rate (G201 p58–59)",
         "Population divided by housing units, both from NCSI",
         "Settlement population divided by the domestic electricity meters counted "
         "in the settlement, with a floor and a cap",
         "Housing units are not published at settlement level"],
        ["Non-domestic and governmental demand (G201 p60–61)",
         "Unit rates per pupil, bed, employee and floor area where detailed land "
         "use is available (G201 Table 12)",
         "The published governorate ratios", "The quantities G201 Table 12 needs are "
         "not recorded in any dataset held"],
        ["Allocation of non-domestic demand (G201 p59)",
         "Distributed across the served population",
         "Placed on the plots whose meters generate it",
         "A residential street generates no commercial flow; the total is unchanged"],
        ["Industrial estates (G201 p61)", "Determined case by case with the developer",
         "An assumed workforce at the dry-industry unit rate",
         "No workforce or discharge record supplied; to be replaced by the record"],
        ["Water supplied by tanker (G201 p62, p73)",
         "Assessed from the tanker filling-station records",
         "Tanker-supplied households carry the domestic rate like any metered "
         "household; no separate tanker term", "No filling-station record held; requested"],
        ["Other water sources (G201 p70)",
         "Private wells and other non-network abstraction assessed",
         "Not assessed; every flow is on the network-accounted basis",
         "No record of private abstraction held; requested"],
        ["Connection to the sewer (G201 p73)",
         "Coverage rising to the whole served area by the end of the period",
         "Every metered property connected from 2024 for sizing; the early-year "
         "self-cleansing case takes the Inception Report connection ratio",
         "Sizing on the full load is the safe side; the ratio is carried where "
         "over-estimating is the risk"],
        ["Design-flow standard (G201 p71)",
         "Where detailed land use exists, design flows to a stated international "
         "standard such as BS EN 752",
         "The planning ratios and return rates of the guideline, plot by plot",
         "The quantities a detailed method needs are not held"],
        ["Growth beyond the forecast (G201 p58)",
         "Not extrapolated more than ten years beyond the available forecast",
         "The Inception Report series to 2100, used for its growth rates only",
         "The saturation year rests on the capacity of the cadastre; the horizon "
         "to 2100 was instructed by NWS"],
    ], widths=[3.2, 4.3, 4.7, 4.3], font=8.3, keep_together=False)
    D.p(d, "", space_after=2)
    _src(d, "report R2 §10.1, Table \"Departures from the design guidelines\". "
            "Dated project rules behind the rows: load basis locked "
            "(engineer, 2026-08-30); occupancy per settlement with floor and cap "
            "(engineer, 2026-09-10); the estates (engineer, 2026-09-09 and -10); "
            "the two flow cases (engineer, 2026-09-11).")
    _ibri(d, f"The occupancy rows in figures: over the study area "
             f"{F.fmt(t['pop_today'])} people on {F.fmt(ps['properties'])} "
             f"domestic properties is {area_or:.2f} persons per property; Ibri "
             f"derives {ib['or_raw']:.2f}; the floor is {F.OR_FLOOR:.1f} and the cap "
             f"{cap_or:.2f}, and {n_small} settlements under a thousand people take "
             f"{F.OR_FLOOR:.1f} outright. The estates carry {F.fmt(workers)} "
             f"workers at {F.L_IND:.0f} l/d (G201 Table 12, p61), "
             f"{F.fmt(ps['s_spec'])} m³/d of sewage. The connection row matters in "
             f"the direction of the error: saturation times the connection ratio "
             f"would give {F.fmt(wrong)} m³/d for the early years, against the "
             f"{F.fmt(low)} m³/d really expected in 2030, and would declare pipes "
             f"self-cleansing while they silt.")
    _where(d, "W14/report/rpt_cd.py, part_c; W14/analysis/occupancy_by_settlement.csv; "
              "design_flows.json (low_case_2030_m3d, rules).")

    # ------------------------------------------------------------------ 24.7
    D.h(d, 2, "24.7   Items still waiting for data")
    D.p(d, "Each item below is either a missing value or a missing record. None is "
           "filled by a guess: each is a parameter, a tagged assumption or a flow "
           "left out and said to be left out.")
    D.tab_caption(d, "Pending items and what closes them")
    D.table(d, ["Item", "Status", "What closes it"], [
        ["Tractive tension τ (GAP-9)", "no value in G203 or G201; a parameter; 1 Pa "
         "tagged where used", "NWS confirms a value in writing"],
        ["1.5 l/s low-flow threshold", "not in G203; Mara, tagged", "NWS confirms or sets another"],
        ["Tanker supply and sewage tankers (GAP-19, GAP-20)",
         "not in any flow; the governorate tanker ratio is unusable (24.3)",
         "filling-station and delivery records"],
        ["Private wells and other sources (GAP-11)", "not assessed", "abstraction records, field survey"],
        ["G201 Table 12 quantities (GAP-10, GAP-15)", "not supplied; ratios used",
         "pupils, beds, employees, floor areas"],
        ["Existing plant capacity and inlet (GAP-7)", "unknown", "NWS operating data"],
        ["Infiltration basis, peaking formula, tanker catchment (GAP-23)",
         "guideline values used; differ from the Inception Report (24.8)",
         "NWS ruling"],
        ["Meters far from any plot", f"{F.fmt(free['count'])} meters more than 15 m "
         f"from a plot carry no load", "open with the engineer"],
    ], widths=[5.0, 6.5, 5.0], font=8.5)
    D.p(d, "", space_after=2)
    _where(d, "_BRAIN/05_GAPS.md; design_flows.json, keys rules and free_meters.")

    # ------------------------------------------------------------------ 24.8
    D.h(d, 2, "24.8   Reconciliation with the Inception Report")
    _for(d, "The Inception Report R0 carries its own demand workbook, and NWS "
            "has read its numbers. Every difference is explained here, so no "
            "figure in the concept report looks like a silent change.")
    D.p(d, "Two positions of the earlier flow tutorial have changed: occupancy is "
           "now derived per settlement rather than taken as a single 5, and "
           "Merrimack is the formula for any pipe serving more than 100 "
           "properties, with Peltier below that, rather than Peltier throughout.")
    D.tab_caption(d, "Reconciliation register against the Inception Report R0")
    D.table(d, ["Item", "Guideline", "Inception Report", "This method", "Status"], [
        ["Domestic consumption", "164 l/c/d (G201 Table 11, p60)",
         "163.5, computed from billing", f"{F.LPCD:.0f} l/c/d", "consistent"],
        ["Occupancy", "population ÷ housing units, NCSI (G201 p58)",
         "a single rate", f"per settlement, floor {F.OR_FLOOR:.1f}, cap "
         f"{cap_or:.2f}; Ibri {ib['or_used']:.2f}; {area_or:.2f} over the area",
         "departure (24.6)"],
        ["Population 2024, 25 settlements", "NCSI series (G201 p58)",
         f"{F.fmt(census)}", recon_pop, "explained"],
        ["Non-domestic and governmental", "22 % and 14 % (G201 Table 11, p60), or "
         "G201 Table 12 (p61)", "ratios", "ratios for the volume, placed on the meters",
         "departure (24.6)"],
        ["Return to sewer", "85 % and 54 % (G201 Table 19, p71)", "same",
         f"{F.RET_DOM * 100:.0f} % and {F.RET_ND * 100:.0f} %", "consistent"],
        ["Infiltration", "720 l/d/km, new network (G201 p72)", "10 % of the flow",
         f"{rules['infiltration_l_per_day_per_km']:.0f} l/d/km per pipe, never "
         f"on the plot", "confirm with NWS"],
        ["Peak", "Merrimack over 100 properties, Peltier alternative; hourly "
         "factor ≤ 5.0 recommended (G201 p71–72)", "Peltier plus a 20 % weekly peak",
         "Merrimack or Peltier per pipe; no weekly peak", "confirm: peaking twice"],
        ["Tanker flow", "coverage as for water (G201 p73)", "settlements within "
         "25 km", "not in any flow; records requested", "open"],
        ["Connection", "100 % by the end of the period (G201 p73)",
         "0.51 in 2024 rising to 0.61 by 2028", f"sizing at 100 %; early-year "
         f"case Q 2030 × {conn:.2f} = {F.fmt(low)} m³/d", "adopted for the low case"],
        ["Horizon", "no more than ten years beyond the forecast (G201 p58)",
         "series to 2100", f"rates only; saturation {ult} on the capacity of the "
         f"cadastre", "departure (24.6)"],
        ["Ultimate average flow", "none", "about 49,700 m³/d",
         f"{F.fmt(t['q_ult'])} m³/d in {ult}; {F.fmt(j['stp_ultimate_with_margin_m3d'])} "
         f"with the plant margin", "superseded"],
        ["Plant margin and effluent", "+10 %, 95 % (G201 p73)", "same", "same", "consistent"],
        ["Sludge", "0.25 kg/m³, indicative (G201 p78)", "0.25 kg/m³", "same",
         "consistent; also in G201"],
    ], widths=[2.8, 3.6, 2.9, 4.7, 2.5], font=8, keep_together=False)
    D.p(d, "", space_after=2)
    _src(d, "the guideline column from _BRAIN/02_DESIGN_CRITERIA.md with pages; "
            "the Inception Report column from its demand workbook as decoded in "
            "TUTORIALS/T01_Sewage_Flow_and_Load_Calculation.md, and its ultimate "
            "flow as footnoted in report R2 §15.7. T01 called the sludge rate an "
            "Inception-only value; it is also G201 p78.")
    _where(d, "The census figure: the demand workbook _CLIENT/Ibri Sewer Demand "
              "R0 2026 08 03.xlsx, sheet \"Project Pop Settlements\", read by "
              "facts_w14.settlement_table (workbook_2024). This method's figures: "
              "facts_w14.totals and design_flows.json.")

    # ------------------------------------------------------------------ 24.9
    D.h(d, 2, "24.9   What to do about all this")
    D.p(d, "Three rules keep the report defensible. Quote the guideline as it is "
           "printed, and say separately what is wrong with it; never publish a "
           "silently corrected version of the client's own standard. Where a "
           "formula is not NWS's, attribute it to whoever it belongs to. And where "
           "the guideline is silent on something it makes mandatory, propose a "
           "value, say where it came from, and obtain agreement in writing before "
           "the design depends on it.")

    _check(d, "24.10   Check it yourself", [
        "Pick any guideline value in the report and open the page it cites. If the "
        "value is not on that page, the citation is wrong, whatever the value.",
        "Search the report for τ. Every use must carry its value and the tag "
        "[GAP-9].",
        "Search the report for 1.5 l/s. It must never be attributed to PAM-GUD-203.",
        f"Recompute the early-year flow two ways: {F.fmt(t['q_ult'])} × {conn:.2f} = "
        f"{F.fmt(wrong)} m³/d is wrong; the sum of Q_2030 × {conn:.2f} over the "
        f"plots, {F.fmt(low)} m³/d, is right.",
        f"Add the settlement column WB_2024 of Settlements_merged.shp "
        f"({F.fmt(census)}) and compare it with POP_2024 ({F.fmt(t['pop_today'])}); "
        f"the difference is the floor and the small-settlement rule, nothing else.",
        "For each departure, check that the report states the guideline position, "
        "the position adopted and the reason, and asks for confirmation."])


# ============================================================= APPENDIX A
def appendix(d):
    t, j, st, ps, ib = _live()
    rules = j["rules"]
    conn = rules["connection_ratio_2030"]
    q_cap = F.LPCD * (F.RET_DOM + F.R_ND * F.RET_ND + F.R_GOV * F.RET_ND)
    cap_or = max(r["or_used"] for r in st)

    D.h(d, 1, "Appendix A   Equations, fields and the rerun order", page_break=True)
    D.p(d, "The reference half of the tutorial: every equation with its source, "
           "the defects in the guidelines, the fields of the two layers that carry "
           "the load, and the order in which the scripts are rerun after a change.")

    # ------------------------------------------------------------------ A.1
    D.h(d, 2, "A.1   Equations in the guidelines")
    D.p(d, "Guidelines PAM-GUD-201 (152 pages), -202 (177) and -203 (201), all "
           "Revision 01, March 2026; the file names say v1.0. The printed page "
           "equals the PDF page in all three. Every equation was re-rendered from "
           "the PDF and read visually: text extraction mangles fraction bars, "
           "radicals and exponents, and three equations exist only as images.")
    eqs = [
        ["1", "Population = plots × properties per plot × occupancy rate", "G201 p58", "one of three permitted approaches"],
        ["2", "Occupancy rate = population ÷ housing units", "G201 p58", "from NCSI data"],
        ["3", "LPCD = domestic water accounted ÷ (OR × active domestic accounts)", "G201 p60", "the derivation behind G201 Table 11"],
        ["4", "Q pdf = 2.65 Q adf^0.879 (Merrimack)", "G201 p71", "Ml/d both sides; over 100 properties"],
        ["5", "Pf = Q pdf ÷ Q adf", "G201 p71", "dimensionless"],
        ["6", "Q pdf = Q adf × Pf WW", "G201 p72", "m³/d, one page from eq. 4"],
        ["7", "Pf WW = 1.5 + 1 ÷ √Q m (Peltier)", "G201 p72", "Q m in l/s; defect D1"],
        ["8", "P HF = Q max hour ÷ Q avg", "G201 p63", "water side"],
        ["9", "P DF = Q max day ÷ Q avg", "G201 p63", "water side"],
        ["10", "V = −2 √(2gDS) log₁₀[k s ÷ 3.7D + 2.51ν ÷ (D √(2gDS))] (Colebrook-White)", "G203 p24", "k s = 1.5 mm; ν = 1.141 × 10⁻⁶ m²/s"],
        ["11", "Q o = V × A", "G203 p24", "printed V ÷ A; defect D2"],
        ["12", "Q p = Q ÷ Q o", "G203 p24", "proportional discharge"],
        ["13", "v = (1/n) R^(2/3) S^(1/2) (Manning)", "G203 p25", "permitted, not required"],
        ["14", "S = v² n² × 6.3448 ÷ D^1.333", "G203 p25", "full bore; defect D3"],
        ["15", "Q = (1/n) R^(2/3) S^(1/2) A", "G203 p25", ""],
        ["16", "τ = W sin θ ÷ (p L) (tractive tension)", "G203 p26", "image only"],
        ["17", "W = ρ g a L", "G203 p26", "companion to 16"],
        ["18", "S min = K τ^1.23 Q^−0.461", "G203 p27",
         f"image only; K printed as {K_M3S_TXT} (Q in m³/s) and {K_LS_TXT} (Q in l/s), "
         f"{_k_gap():.1f} % apart; this method uses {K_M3S_TXT} with Q in m³/s "
         f"(Section 24.2); no τ, defect D4"],
        ["19", "H L = β (w/b)^(4/3) h sin θ (Kirschmer)", "G203 p104", "exponent printed as 1.33"],
        ["20", "V = 0.25 Q T (wet well live volume)", "G203 p48", "T = 3600 ÷ starts per hour; 10 starts/h up to 30 kW"],
        ["21", "NPSHa = Ha − Hvpa − Hst − Hf", "G203 p47", "margin ≥ 1 m"],
        ["22", "ΔH = (c/g) Δv (Joukowsky)", "G201 p146", "not in G202 or G203"],
        ["23", "Pipeline emptying time", "G201 p144", "dimensionally inconsistent; defect D5"],
        ["24", "dS/dt = 3.23 M′ [EBOD] r⁻¹ − 2.1 N (s v)^0.375 [S] d m⁻¹ (Pomeroy-Parkhurst)", "G203 p186", "two of nine symbols carry units"],
        ["25", "EBOD = BOD × 1.07^(T−20)", "G203 p186", ""],
        ["26", "S = K s BOD₅ t f(T) (force mains)", "G203 p186", "unusable: K s and f(T) undefined"],
        ["27", "Q TSE = 0.95 × Q STP inlet", "G201 p73, p75", ""],
        ["28", "TSE network loss = 10 % of TSE produced", "G201 p76", "\"shall\""],
        ["29", "Sludge = 0.25 kg/m³ × inlet volume", "G201 p78", "indicative"],
        ["30", "Aerated biomass = total biomass × aerated fraction of the cycle", "G203 p94", ""],
        ["31", "Total N = Org-N + NH₃ + NH₄ + NO₂-N + NO₃-N", "G203 p71", ""],
    ]
    D.tab_caption(d, "Equations that exist in the guidelines")
    D.table(d, ["No.", "Equation", "Source", "Note"], eqs,
            widths=[1.0, 8.4, 2.4, 4.7], font=8, keep_together=False)
    D.p(d, "", space_after=2)

    D.h(d, 2, "A.2   Equations of this method")
    D.p(d, "The equations the load chain, the design flows and the appraisal add "
           "to the guideline set. Each is either built from guideline values, "
           "whose pages are given, or is a dated project rule.")
    D.tab_caption(d, "Equations added by this method")
    D.table(d, ["No.", "Equation", "Source", "Where it lives"], [
        ["M1", f"OR s = P s,2024 ÷ N dom,s; floor {F.OR_FLOOR:.1f}, cap {cap_or:.2f}; "
               f"{F.OR_FLOOR:.1f} outright under 1,000 people",
         "G201 p58 form; project rule 2026-09-10", "plot_class_v2_apply.py; field OR_S"],
        ["M2", "Capacity s = empty home-shaped plots × home share × properties per "
               "home plot × OR s", "project rule 2026-09-10",
         "plot_class_v2_apply.py; FUT_CAP, CAP_POP"],
        ["M3", "Q plot = 0.85 × 164 × OR × N dom + 0.54 × (U nd N nd + U gov N gov + 93 N w), l/d",
         "G201 Tables 11, 12, 19 (p60, p61, p71); project rule 2026-09-10",
         "plot_class_v2_apply.py; QADF"],
        ["M4", "U nd = 0.22 × 164 × P s ÷ N nd,s (meters outside the estates)",
         "G201 Table 11 p60; placement, project rule", "U_NDOM"],
        ["M5", "U gov = 0.14 × 164 × P s ÷ N gov,s (meters outside the estates)",
         "G201 Table 11 p60; placement, project rule", "U_GOV"],
        ["M6", f"Q future plot = people × {q_cap:.1f} l/d, where {q_cap:.1f} = 164 × "
               f"(0.85 + 0.22 × 0.54 + 0.14 × 0.54)", "G201 Tables 11, 19",
         "growth_by_settlement.py; Q_2030, Q_2055, Q_ULT"],
        ["M7", "Properties in year y = G_DOM + (POP y − POP) ÷ OR_S",
         "project rule", "make_design_flows.py; design_flows.json properties"],
        ["M8", f"Q low = Q 2030 × {conn:.2f}, summed per pipe, then peaked on the "
               f"connected count, properties of 2030 × {conn:.2f} (Merrimack over "
               f"100, Peltier at or under)",
         "project rule 2026-09-11; ratio from the Inception Report; the connected "
         "count recommended in the design-flow handoff, to be confirmed by the engineer",
         "design_flows.json low_case_2030_m3d"],
        ["M9", "Infiltration = 720 l/d/km × pipe length, added per pipe", "G201 p72",
         "the network engine, never the plot"],
        ["M10", "Plant capacity = (settlement total + network infiltration + "
                "tankers when known) × 1.10", "G201 p73",
         "design_flows.json stp_ultimate_with_margin_m3d (before infiltration)"],
        ["M11", "C cap = (1 + f pre + f phys + f price) × Σ c k q k",
         "NWS appraisal structure; project rule 2026-09-01", "Section 21.2"],
        ["M12", "NPV = Σ C t ÷ (1 + r)^t, t = 0 … n; r = 0.05, n = 25",
         "ISO 15686-5; r and n G201 p96, p57", "Section 22.2"],
        ["M13", "a n = [1 − (1 + r)^−n] ÷ r", "standard discounting", "Section 22.2"],
        ["M14", "S j = Σ w k s jk, Σ w k = 1", "ours, to agree with NWS", "Section 23.3"],
        ["M15", "(LCC j − LCC min) ÷ LCC min ≤ 0.10", "G201 p106; the base is ours",
         "Section 23.5"],
    ], widths=[1.1, 7.6, 4.0, 3.8], font=8, keep_together=False)
    D.p(d, "", space_after=2)
    D.p(d, "The formulae that are not in the guidelines, and what to cite instead, "
           "are the table of Section 24.1.")

    # ------------------------------------------------------------------ A.3
    D.h(d, 2, "A.3   Register of defects in the guidelines")
    D.p(d, "Each was verified at the page. Reproduce the guideline's value where it "
           "is quoted, and flag it; never repair it silently.")
    D.tab_caption(d, "Defects in PAM-GUD-201, -202 and -203")
    D.table(d, ["No.", "Defect", "Page", "Handling"], [
        ["D1", "Peltier numerator printed as 1, not the classical 2.5", "G201 p72", "print as printed; query NWS"],
        ["D2", "Q o = V ÷ A, dimensionally impossible", "G203 p24", "use V × A; note the typo"],
        ["D3", "Manning constant 6.3448 against exact 4^(4/3) = 6.3496", "G203 p25", "quote 6.3448; footnote"],
        ["D4", "no value of τ in pascals in G203 or G201", "G203 p26–27", "state the gap; GAP-9"],
        ["D5", "pipeline emptying time evaluates to m^1.5·s²", "G201 p144", "quote with the caveat"],
        ["D6", "Adh Dhahirah tanker ratio of 333 % impossible", "G201 p62", "volumes sound, ratio not; query"],
        ["D7", "G203 Tables 17 and 19 disagree on Type 3 duty pumps (3 against 2)", "G203 p40, p42", "G203 Table 17, the conservative one"],
        ["D8", "Fayoux H₂S risk bands overlap; nothing above 30", "G203 p185", "reproduce; flag"],
        ["D9", "aerobic digestion: text 45 days, G203 Table 77 10–15 days", "G203 p146", "text governs"],
        ["D10", "clarifier loading 1.0–1.4 m/h against overflow 16–28 m³/m²·d", "G203 p124", "reproduce both; flag"],
        ["D11", "chlorine residual \"at least between 0.3 and 1.0\"", "G203 p71, p130", "0.3–1.0 at consumer; to 3.0 at plant"],
        ["D12", "OSEC free chlorine \"> 0.06 mg/L\", orders of magnitude out", "G203 p132", "report, do not use"],
        ["D13", "air valve size bands overlap and leave a gap", "G203 p53", "reproduce as printed"],
        ["D14", "washout size bands overlap and leave gaps", "G203 p54", "reproduce as printed"],
        ["D15", "package plant peak factor 3.0 attributed to G201, not there", "G203 p97", "query NWS"],
        ["D16", "trunk main \"length above 1,000 mm without connexions\"", "G203 p35", "quote with [sic]; metres meant"],
        ["D17", "motor service factor \"1.15%\"", "G202 p96", "1.15 intended"],
        ["D18", "\"AM-GUD-201\" and \"AM-GUD-202\" for PAM-GUD", "G203 p65, p51", "typos"],
        ["D19", "G203 Table 63 preceded by an orphan caption \"Table 58\"", "G203 p124", "numbering defect"],
        ["D20", "tanker discharge references point to §10.6.4 and §10.6.3; it is §10.6.2", "G203 p73, p83", "two wrong references"],
        ["D21", "primary settler detention \"1.2\" with no unit", "G203 p119", "read as 1.2 h; state the inference"],
        ["D22", "G201 Table 2 header row collapsed to zero height", "G201 p19", "recovered by character extraction"],
        ["D23", "G201 Table 2 field investigations: detailed cell blank", "G201 p19", "reproduce as blank"],
        ["D24", "value engineering timing: G201 Table 27 concept, G201 Table 2 detailed only", "G201 p93, p20", "G201 §11.3.2 supports G201 Table 27"],
        ["D25", "EIA timing: scoping at preliminary against full EIA at concept", "G201 p19, p44", "query NWS"],
        ["D26", "two undefined asterisks: G201 Table 12 header and \"*Q_adf\"", "G201 p61, p71", "no footnote exists"],
        ["D27", "design life 20 years against pump service rating 15 years", "G203 p38, p40", "different things; state both"],
        ["D28", "\"nominal flow\" undefined for retention basin and relief sewer", "G203 p191", "query NWS"],
    ], widths=[1.0, 7.8, 2.6, 5.1], font=7.8, keep_together=False)
    D.p(d, "", space_after=2)

    # ------------------------------------------------------------------ A.4
    D.h(d, 2, "A.4   Fields of the plot layer")
    D.p(d, f"W14/shp/PLOTS_load.shp carries, for each of the {F.fmt(ps['total'])} "
           f"plots, the fields below. It is the load table of the design: the "
           f"network reads the flow of each plot from it, and every settlement "
           f"figure is a sum over it.")
    D.tab_caption(d, "Fields of the plot layer")
    D.table(d, ["Field", "Content"], [
        ["Name", "cadastral identifier, as received"],
        ["Moh_Classi, Classes", "class code and class name of the cadastre, as received"],
        ["Buiding_St", "built or future, as received"],
        ["SETTLE", "the settlement the plot belongs to"],
        ["AREA_M2", "plot area, m²"],
        ["N_ACC", "meters on the plot, all tariffs"],
        ["N_DOM, N_DOMADD", "meters on the primary and subsidised tariffs; on the additional-account tariff"],
        ["N_COM, N_GOV, N_AGR, N_CRT, N_IND", "meters on the commercial tariff (with fisheries and tourism), the government tariff (with defence), and the agricultural, large-consumer and industrial tariffs"],
        ["G_DOM", "domestic meters, one property each (primary, subsidised and additional tariffs)"],
        ["G_NDOM, G_GOV, G_SPEC, G_AGR", "non-domestic, governmental, special and agricultural meters, the large consumers placed by their identified use"],
        ["DERIVED", "use of the plot"],
        ["WHYC", "the rule that set the use"],
        ["ESTATE", "the industrial estate the plot lies in, if any"],
        ["WORKERS", "workers assigned to an estate plot, by area"],
        ["HOMESHAPE", "1 if the plot is home-shaped: 200 to 1,000 m², compact, not a strip"],
        ["COMPACT, ASPECT", "area against the smallest enclosing rectangle; that rectangle's aspect ratio"],
        ["NDVI_MEAN, NDVI_SHARE, GREEN_M2", "the satellite vegetation test: mean index, share of green pixels, green area in m²"],
        ["OR_S", "occupancy adopted for the settlement, persons per property"],
        ["PPP_S", "properties per home plot adopted for the settlement"],
        ["HOMESH_S", "home share adopted for the settlement"],
        ["U_NDOM, U_GOV", "non-domestic water per shop meter and governmental water per government meter in the settlement, l/d"],
        ["POP", "people in 2024: G_DOM × OR_S"],
        ["W_DOM, W_NDOM, W_GOV, W_SPEC, W_TOT", "water by stream and in total, m³/d, 2024"],
        ["S_DOM, S_NDOM, S_GOV, S_SPEC", "sewage by stream, m³/d: 0.85 of the domestic water, 0.54 of the rest"],
        ["QADF", "average dry-weather sewage flow of the plot in 2024, m³/d: the sum of the four streams"],
        ["FUT_CAP", "1 if an empty plot counts as a future home"],
        ["FUT_PROPS", "properties expected per counted plot: the settlement's ratio times its home share"],
        ["SPREAD_W", "weight for placing the settlement's growth: the plot's area capped at 1,000 m² on an empty plot of up to 2,000 m² that is not a grove, industrial or heritage; zero on every other plot"],
        ["POP_2030, POP_2055, POP_ULT", "people on the plot in 2030, 2055 and the saturation year"],
        ["Q_2030, Q_2055, Q_ULT", "average sewage flow in 2030, 2055 and the saturation year, m³/d; a future plot at the future-plot rate per person (M6)"],
        ["SAT_YEAR", "the year the plot's settlement is full"],
        ["ULT_YEAR", "the saturation year of the study area"],
    ], widths=[5.2, 11.3], font=8.2, keep_together=False)
    D.p(d, "", space_after=2)

    # ------------------------------------------------------------------ A.5
    D.h(d, 2, "A.5   Fields of the settlement layer")
    D.p(d, f"W14/shp/Settlements_merged.shp carries the same at settlement level "
           f"for the {len(st)} settlements, with the rates and the five-year steps. "
           f"The plots sum to it in every flow and population column.")
    D.tab_caption(d, "Fields of the settlement layer")
    D.table(d, ["Field", "Content"], [
        ["SETTLE, AREA_KM2", "name; area in km²"],
        ["WB_2024, WB_2100", "population of the Inception Report series in 2024 and 2100"],
        ["PROPS", "domestic properties (meters) in 2024"],
        ["OR_RAW, OR_S", "occupancy derived and adopted"],
        ["PPP_RAW, PPP_S", "properties per home plot derived and adopted"],
        ["HOMESH_RAW, HOMESH_S", "home share derived and adopted"],
        ["SMALL", "1 if under 1,000 people in 2024: the small-settlement rule applies"],
        ["BUILT_PL, EMPTY_PL, HOME_MEAS", "built plots; empty plots; home plots the ratio was measured on"],
        ["CAP_PLOTS, CAP_POP", "empty plots counted as future homes; the people they hold at saturation"],
        ["G_NDOM, NDOM_POOL, G_GOV, GOV_POOL, G_AGR, G_SPEC", "meters by category; of the shop and government meters, those outside the estates that share the pool"],
        ["WORKERS", "workers of the industrial estates in the settlement"],
        ["U_NDOM, U_GOV", "non-domestic water per shop meter, governmental water per government meter, l/d"],
        ["POP_2024", "people in 2024"],
        ["W_DOM, W_NDOM, W_GOV, W_SPEC, W_TOT", "water by stream and in total, m³/d, 2024"],
        ["S_DOM, S_NDOM, S_GOV, S_SPEC, Q_2024", "sewage by stream and in total, m³/d, 2024"],
        ["POP_2025 … POP_2070, Q_2025 … Q_2070", "people and average sewage flow at five-year steps to the saturation year"],
        ["POP_ULT, Q_ULT", "people and flow in the saturation year of the study area"],
        ["SAT_YEAR, SAT_POP, SAT_Q", "the year the settlement is full, and its people and flow then"],
        ["SAT_OWN", "the year it would fill on its own growth alone; 0 if not before 2100"],
        ["IN_PEOPLE, OUT_PEOPLE, MAIN_TO, INSHARE", "people received from and sent to other settlements by the saturation year; the main receiver; the share of capacity taken by overflow"],
        ["ULT_YEAR, UNHOUSED", "the saturation year of the study area; growth of the series to 2100 with nowhere to go"],
    ], widths=[5.2, 11.3], font=8.2)
    D.p(d, "", space_after=2)
    _where(d, "Both field lists are the ones delivered with report R2, Appendix "
              "A4 (W14/report/rpt_app.py).")

    # ------------------------------------------------------------------ A.6
    D.h(d, 2, "A.6   The rerun order")
    D.p(d, "Every number in this tutorial and in the concept report comes out of "
           "five steps, run in this order after any change to the data or a rule. "
           "Each step reads what the one before wrote; running one out of order "
           "leaves the layers disagreeing with each other.")
    D.tab_caption(d, "The rerun order and what each step writes")
    D.table(d, ["Step", "Script, and where it runs", "Reads", "Writes"], [
        ["1", "W14/py/plots_meters_load.py, inside QGIS with the project open",
         "the plots, the electricity meters, the identified large-consumer accounts "
         "and projects, the towns and the boundary, as layers of the QGIS project",
         "shp/ELE_meters_on_plots.shp (every meter, its plot and category); "
         "shp/PLOTS_load.shp (meters and today's load); shp/Settlements_merged.shp; "
         "analysis/plots_load_today.csv; analysis/settlements_today.csv"],
        ["2", "W14/py/plot_class_v2_apply.py, plain Python",
         "PLOTS_load.shp; analysis/ndvi_plots.csv and vegfrac_plots.npy; the "
         "Inception demand workbook",
         "PLOTS_load.shp (use, OR_S, U_NDOM, U_GOV, loads, FUT_CAP, SPREAD_W); "
         "analysis/plot_class_audit.csv; settlements_today.csv; "
         "occupancy_by_settlement.csv"],
        ["3", "W14/py/growth_by_settlement.py, plain Python",
         "settlements_today.csv; PLOTS_load.shp; Settlements_merged.shp; the "
         "Inception demand workbook",
         "analysis/W14_growth_by_settlement.xlsx (people and flow by settlement and "
         "year, the five-year tables, the overflow routes, the rules); "
         "PLOTS_load.shp (POP_ and Q_ fields, SAT_YEAR, ULT_YEAR); "
         "Settlements_merged.shp (five-year, saturation and overflow fields)"],
        ["4", "W14/py/make_design_flows.py, plain Python",
         "the outputs of steps 2 and 3, through facts_w14",
         "docs/DESIGN_FLOWS_FOR_NETWORK.md; analysis/design_flows.json"],
        ["5", "W14/report/build.py --pdf, plain Python with Word",
         "facts_w14 and the figures in W14/report/img",
         "report/R2/Ibri_Concept_Design_Report_R2.docx and .pdf (the REV constant "
         "selects the revision folder)"],
    ], widths=[1.0, 4.2, 5.0, 6.3], font=8.2)
    D.p(d, "", space_after=2)
    D.callout(d, "Never stop after step 1.",
              "The loader still carries the single occupancy rate of an earlier "
              "stage among its constants. The occupancy per settlement, the plot "
              "use and the loads are applied by step 2, which rewrites the plot "
              "layer. A plot layer read between steps 1 and 2 carries the old "
              "rate.")
    D.p(d, "Two inputs of step 2 are made once and rerun only when their source "
           "changes: the satellite vegetation index per plot "
           "(W14/py/ndvi_plots.py, writing analysis/ndvi_plots.csv) and the "
           "vegetation fraction per plot (W14/py/vegfrac_plots.py, writing "
           "analysis/vegfrac_plots.npy). After step 5 this tutorial is rebuilt "
           "with TUTORIALS/T04/build.py, which reads the same facts, so its "
           "numbers follow.")
    _check(d, "A.7   Check it yourself", [
        f"After step 3, sum QADF over the plot layer and compare it with Q_2024 "
        f"summed over the settlement layer: both should give "
        f"{F.fmt(t['q_today'])} m³/d.",
        f"After step 3, sum Q_ULT over the plots: {F.fmt(t['q_ult'])} m³/d in "
        f"{t['ultimate']}.",
        "After step 4, open design_flows.json and check that its totals match the "
        "workbook sheet \"Qadf by year m3d\" for 2024, 2030, 2055 and the "
        "saturation year.",
        "After step 5, read the exported report figures as images, not only the "
        "file list: a layer with its categories switched off still exports a "
        "complete-looking legend.",
        f"Check the future-plot rate by hand: 164 × (0.85 + 0.22 × 0.54 + 0.14 × "
        f"0.54) = {q_cap:.1f} l/d per person."])
