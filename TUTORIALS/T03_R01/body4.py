"""Revision 01: cost estimation and financial appraisal, built out properly."""
import os

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

import doc as D
import omml as M

UP = M.up
R = M.r


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows,
            widths=[2.6, 10.4, 3.5], font=9)


def _source(d, text):
    D.p(d, "Source: " + text, size=9, italic=True, colour=D.GREY, space_after=10)


def _items(d, caption, rows):
    D.tab_caption(d, caption)
    D.table(d, ["Group", "Items"], rows, widths=[4.0, 12.5], font=9)
    D.p(d, "")


# ================================================== 19  COST ESTIMATION
def s19_cost(d):
    D.h(d, 1, "19   Cost estimation", page_break=True)

    D.h(d, 2, "19.1   Purpose")
    D.p(d, "Three options per system have to be compared on cost, and the "
           "comparison decides which one is built. An estimate that omits a "
           "whole category of work does not merely understate the total — it "
           "distorts the ranking, because the omission usually falls harder on "
           "one option than another. This section is a checklist against that.")

    D.picture(d, os.path.join(IMG, "F14_cost.png"), 15.5)
    D.fig_caption(d, "Building the estimate. Renewal and decommissioning sit "
                     "inside the twenty-five year horizon, not beyond it.")

    D.h(d, 2, "19.2   Basis")
    D.table(d, ["Item", "Requirement"],
            [["Accuracy at concept stage", "**± 20 %**, and the report must state it"],
             ["Measurement", "CESMM3"],
             ["Unit rates", "most recent market rates, preferably from NWS tender "
                            "or contract documents"],
             ["Format", "NWS will advise the required format and methodology "
                        "before the design phase, on request"],
             ["Basis of prices", "current base prices, from the start of construction"],
             ["Presentation", "by asset category at feasibility; **by system "
                              "element, as a cost curve, at this stage**"]],
            widths=[4.6, 11.9], font=9)
    D.p(d, "")

    D.h(d, 2, "19.3   Cost breakdown — sewer network")
    D.p(d, "The largest single risk in a sewerage estimate is that the pipe is "
           "priced carefully and everything around it is not. In urban work the "
           "trench, the reinstatement and the traffic usually cost more than the "
           "pipe.")

    _items(d, "Sewer network items", [
        ["Earthworks",
         "Excavation by depth band; rock excavation priced separately; "
         "dewatering where the water table is met; trench support and shoring "
         "by depth; disposal of surplus and unsuitable material"],
        ["Pipework",
         "Pipe supply and lay by diameter and material; bedding and surround; "
         "selected backfill and imported fill; jointing; specials and fittings"],
        ["Chambers",
         "Manholes by depth band and diameter; backdrops; drop shafts; "
         "benching and channels; covers by loading class"],
        ["Connections",
         "Property connection sewers; connection chambers; riders; "
         "connections to the existing network; future connection stubs and end caps"],
        ["Surface",
         "**Road reinstatement by surface type** — asphalt, interlock, kerb, "
         "footpath, unpaved; line marking; **traffic management and diversions**"],
        ["Crossings",
         "Road, wadi and utility crossings; trenchless drives where open cut is "
         "not permitted; carrier and sleeve pipes; thrust and reception pits"],
        ["Enabling",
         "Trial pits; utility diversions and protection; temporary works; "
         "site establishment"],
        ["Proving",
         "Water and air tightness testing; CCTV survey; compaction testing; "
         "as-built survey"]])

    D.h(d, 2, "19.4   Cost breakdown — lifting stations and force mains")
    _items(d, "Lifting station items", [
        ["Land and site",
         "Land acquisition and Krooki fees; site clearance and levelling; "
         "access road and turning area; boundary wall and gates; landscaping"],
        ["Civil",
         "Wet well by depth; dry well or valve chamber; base slab and "
         "dewatering during construction; protective lining; superstructure or "
         "cover slab; emergency storage or overflow structure"],
        ["Mechanical",
         "Duty and standby pumps; screens or macerators; station pipework, "
         "valves and non-return valves; lifting davit or gantry; sump pump; "
         "ventilation"],
        ["Electrical and control",
         "Incoming supply and connection charges; transformer and substation; "
         "motor control centre; standby generator and fuel storage; "
         "instrumentation, SCADA and telemetry; small power and lighting"],
        ["Odour and safety",
         "Odour control unit and ducting; gas detection; fire detection where "
         "required; welfare facilities"],
        ["Commissioning",
         "Testing, commissioning, operator training, spares holding"]])

    _items(d, "Force and rising main items", [
        ["Pipework",
         "Pipe supply and lay by diameter and material; excavation, bedding and "
         "backfill as for gravity; thrust blocks and anchor blocks; "
         "restrained joints"],
        ["Appurtenances",
         "Air valves and their chambers; washout valves, chambers and discharge "
         "points; isolation valves at 500 to 800 m; flow meters and access "
         "chambers every 500 m; marker posts and warning tape"],
        ["Termination",
         "Receiving manhole with water seal; vent and odour control at the "
         "discharge; bell-mouth termination"],
        ["Proving",
         "Pressure testing; pigging or flushing provision; surge protection "
         "equipment identified by the transient study"]])

    D.h(d, 2, "19.5   Cost breakdown — treatment plant")
    _items(d, "Treatment plant items", [
        ["Land and site",
         "Land acquisition; site preparation and earthworks; **flood "
         "protection to the 100 year level**; internal roads and hardstanding; "
         "fencing; landscaping and buffer planting; solar farm area if provided"],
        ["Inlet works",
         "Coarse and fine screens; screenings handling, washing, pressing and "
         "containers; grit removal, classification and washing; FOG removal; "
         "**tanker discharge facility** with screening, sampling and flow "
         "measurement; flow equalisation"],
        ["Biological treatment",
         "Reactor civils; aeration equipment and blowers; mixers; internal "
         "recycle pumps; membranes or media where used; swing zone provision"],
        ["Separation and tertiary",
         "Primary and final clarifiers with scrapers; RAS and WAS pumping; "
         "tertiary filtration; disinfection; TSE storage acting as contact tank"],
        ["Sludge line",
         "Thickening; digestion where provided; dewatering with standby unit; "
         "drying or composting; sludge storage; **external sludge reception** "
         "given the governorate role; conveyors and skips"],
        ["Chemical systems",
         "Coagulant, polymer, pH correction, carbon source and disinfectant "
         "dosing; bulk storage and bunding; dosing pumps and mixers"],
        ["Odour",
         "Covers and enclosures; extraction ducting; treatment units with N+1 "
         "redundancy; continuous monitoring with electronic noses"],
        ["Electrical and control",
         "Incoming supply and substation; motor control centres; standby "
         "generation; solar photovoltaic; ICA, SCADA and instrumentation; "
         "power factor correction"],
        ["Buildings",
         "Administration, laboratory, workshop, stores, welfare; blower and "
         "dewatering buildings; guard house"],
        ["Emergency and disposal",
         "Emergency lagoon at 48 to 72 hours; raw sewage diversion provision; "
         "wadi discharge outfall and its approvals; TSE filling station"],
        ["Commissioning",
         "Wet and dry commissioning; process proving to Class A; operator "
         "training; initial spares"]])

    D.h(d, 2, "19.6   Cost breakdown — treated effluent network")
    _items(d, "Treated effluent items", [
        ["Distribution",
         "Pipework by diameter; excavation and reinstatement; valves, air "
         "valves and washouts; crossings"],
        ["Storage and boosting",
         "Reservoirs at 24 hours minimum; booster stations; chlorine residual "
         "top-up where the network is long"],
        ["Customers",
         "Customer connections and meters; filling stations with their "
         "identification, metering and control systems; driver facilities"]])

    D.h(d, 2, "19.7   Costs outside the works")
    _items(d, "Soft costs and provisions", [
        ["Professional",
         "Design and supervision fees; topographic and utility survey; "
         "geotechnical investigation and trial pits; hydraulic modelling"],
        ["Consents",
         "Environmental impact assessment; NOCs and permits; land acquisition "
         "and Krooki fees; municipality and roads authority approvals"],
        ["Provisions",
         "**Physical contingency** for quantity and scope growth; "
         "**price contingency** for escalation to the midpoint of construction; "
         "risk allowance carried from the risk register"]])

    D.callout(d, "Contingency is not a single number.",
              "The guideline requires the estimate to include contingencies and "
              "to state the degree of accuracy. Keep the physical allowance, "
              "which covers what the design does not yet know, separate from "
              "the price allowance, which covers inflation between the estimate "
              "and construction. Merging them hides which one is driving the "
              "total, and only the first should shrink as the design develops.")

    D.h(d, 2, "19.8   Five lines that get missed")
    D.p(d, "Each of these is routinely omitted, and each is large.")
    D.bullet(d, "priced as if it were soft ground. In this terrain it rarely "
                "is, and the difference is several times the rate.",
             lead="Rock excavation — ")
    D.bullet(d, "frequently the single largest line in urban sewerage, and "
                "sensitive to surface type in a way a single average rate hides.",
             lead="Road reinstatement — ")
    D.bullet(d, "electrical assets last fifteen years and mechanical twenty, so "
                "a twenty-five year appraisal contains at least one full "
                "replacement of both. Omitting it flatters every option that is "
                "mechanically heavy — which is exactly the decentralised case.",
             lead="Renewal inside the horizon — ")
    D.bullet(d, "not a marginal line here, because the plant is the "
                "governorate's designated composting centre and will receive "
                "sludge from beyond its own catchment.",
             lead="Sludge haulage — ")
    D.bullet(d, "named in the guideline's own life cycle cost scope and almost "
                "always left out.", lead="Decommissioning — ")


# ================================== 20  FINANCIAL AND ECONOMIC APPRAISAL
def s20_financial(d):
    D.h(d, 1, "20   Financial and economic appraisal", page_break=True)

    D.h(d, 2, "20.1   Purpose")
    D.p(d, "The estimate says what each option costs to build. The appraisal "
           "says what each costs to own for twenty-five years, in money of one "
           "date, so that options with different shapes can be compared. A "
           "scheme that is cheap to build and expensive to run can lose to one "
           "that is the reverse, and the appraisal is where that becomes "
           "visible.")

    D.picture(d, os.path.join(IMG, "appraisal_method.png"), 16.2)
    D.fig_caption(d, "The appraisal, end to end. Each option is costed on "
                     "three streams, the streams are discounted together, and "
                     "only then are the options scored.")

    D.callout(d, "None of the formulae in this section comes from NWS.",
              "Net present value, life cycle cost and carbon accounting are all "
              "specified in scope by the guideline and none is written as an "
              "equation anywhere in it. Cite ISO 15686-5 for life cycle cost "
              "and the GHG Protocol with ISO 14064 for carbon. What NWS does "
              "fix is the discount rate, the horizon, the cost components and "
              "the decision rules.")

    D.h(d, 2, "20.2   The cash flow to be built")
    D.p(d, "For each option, a year-by-year cash flow across the appraisal "
           "period, containing five streams.")
    D.table(d, ["Stream", "Timing", "Note"],
            [["Capital expenditure", "in the years each phase is built",
              "phased, not lumped at year zero"],
             ["Operating expenditure", "every year from commissioning",
              "grows as connections and flow grow"],
             ["Renewal", "electrical at 15 years, mechanical at 20",
              "at least one cycle falls inside the horizon"],
             ["Residual value", "final year, negative cost",
              "credit for asset life remaining beyond year 25"],
             ["Decommissioning", "end of life",
              "named in the guideline's life cycle scope"]],
            widths=[4.0, 6.0, 6.5], font=9)
    D.p(d, "")

    D.callout(d, "Phasing is what makes the comparison honest.",
              "A centralised plant built in two phases and a set of "
              "decentralised plants built as districts develop have very "
              "different cash-flow shapes, and discounting is sensitive to "
              "shape. Lumping capital at year zero for both erases the "
              "difference the appraisal exists to reveal.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "20.3   Operating cost build-up")
    D.p(d, "The guideline names the components. Quantifying them is the "
           "designer's task, and each has a natural driver.")
    D.table(d, ["Component", "Driven by", "Basis"],
            [["Power", "kWh per year", "**latest APSR tariff**"],
             ["Labour and staffing", "posts and shift pattern",
              "per hour, day, month or year"],
             ["Chemicals", "dose rate times flow",
              "coagulant, polymer, pH correction, disinfectant, carbon source"],
             ["Spares and consumables", "installed plant value", "annual provision"],
             ["Vehicles and equipment", "fleet size", "per hour, day, month or year"],
             ["Maintenance and repairs", "asset value and type", "annual provision"],
             ["Sludge handling and disposal", "tonnes of dry solids per year",
              "treatment, haulage and gate fees"],
             ["Monitoring", "sampling regime",
              "laboratory, odour monitoring, effluent compliance"],
             ["Network washing", "pipes below self-cleansing velocity",
              "from the schedule in Section 10"]],
            widths=[4.6, 4.6, 7.3], font=9)
    D.p(d, "")
    D.p(d, "Power deserves particular attention: more than eighty per cent of "
           "NWS operational emissions come from electricity, so the energy line "
           "drives both the operating cost and the carbon score, and the two "
           "move together rather than trading off.")

    D.h(d, 2, "20.4   Discounting")
    eq = D.next_eq()
    M.display(d, M.seq(UP("NPV"), M.EQ,
                       M.nary("∑", M.seq(R("t"), R("=0")), R("n"),
                              M.frac(M.sub(R("C"), R("t")),
                                     M.sup(M.delim(M.seq(R("1"), M.PLUS, R("i"))),
                                           R("t"))))), number=eq)
    _params(d, [
        ["C t", "net cost in year t — capital, operating, renewal, residual",
         "OMR"],
        ["i", "discount rate, **5 % unless NWS instructs otherwise**", "fraction"],
        ["n", "appraisal period, **25 years**", "years"],
        ["t", "year, counted from the start of construction", "—"]])

    D.p(d, "The period is twenty-five years even where the technical life of "
           "the civil works is fifty, which is why the residual value line "
           "matters: without it, an option built of long-lived concrete is "
           "penalised against one built of short-lived plant.")

    D.h(d, 2, "20.5   Sensitivity")
    D.p(d, "The guideline names exactly three variables to test, and only "
           "three.")
    D.numbered(d, "the weighting between the appraisal categories")
    D.numbered(d, "the discount rate")
    D.numbered(d, "the input design criteria, for example a reduction in demand")
    D.p(d, "For this project the third is the one that bites. The flow estimate "
           "carries real uncertainty — the design horizon is unsettled, the "
           "existing plant capacity is unverified, and the tanker share is "
           "unknown — and the Phase I capacity sits close to a contractual "
           "threshold. A sensitivity run that does not move the flow is not "
           "testing the thing most likely to be wrong.")

    D.h(d, 2, "20.6   Risk")
    D.p(d, "A risk register is carried from concept stage onward and updated "
           "through the project. For appraisal purposes each risk needs a "
           "likelihood, an impact in money, and an owner; the risk-adjusted "
           "cost then feeds the comparison alongside the base estimate. Risks "
           "that fall on one option and not another are the ones that change "
           "the ranking.")

    D.h(d, 2, "20.7   How appraisals of this kind go wrong")
    D.p(d, "Two Nama Water Services pre-investment appraisals were reviewed "
           "line by line against their own calculation workbooks. The faults "
           "found there are not unusual, and each is worth checking for "
           "deliberately.")
    D.table(d, ["Fault", "What to do instead"], [
        ["Revenue billed on a peak-day volume, and on volume that includes "
         "losses",
         "Bill on the average day, and on billable volume only. Losses are "
         "non-revenue by definition"],
        ["The split between customer categories taken from the wrong place, so "
         "the high tariff is applied to most of the volume",
         "Derive the split from the land-use allocation that sized the network, "
         "and check it against the demand table"],
        ["Alternatives that differ from the preferred option in one quantity, "
         "sharing its structures and omitting their own pumping",
         "Cost each option as it is designed, including its own plant, its own "
         "storage and the energy that follows from them"],
        ["Operating cost taken as a percentage of capital, with energy and "
         "labour entered as zero",
         "Build operating cost from duty. For a wastewater system energy and "
         "sludge dominate, and neither follows capital value"],
        ["Annual operating cost multiplied by the horizon and called a "
         "lifetime cost",
         "Discount it. An undiscounted multiplication overstates the present "
         "value of a 25-year stream by about a factor of two at 5 per cent"],
        ["A tariff margin, or an avoided cost, described as revenue",
         "Name each stream for what it is, and state the baseline it is "
         "incremental to"],
        ["Unit rates carried forward unchanged from an earlier study",
         "Escalate to a stated base date, and say which date"],
        ["The recommended option left out of the risk assessment",
         "Score every option, including the one you intend to recommend"],
    ], widths=[7.4, 9.1], font=9)

    D.p(d, "")
    p = D.p(d, "None of these changed the ranking in the appraisals reviewed, "
               "because the options were far apart on cost. They would change "
               "it in a close case, and they change every absolute figure that "
               "a budget, a tariff submission or a board paper depends on.")
    _source(d, "Review of two NWS pre-investment appraisal documents, "
               "Seeb Package 3 Phase 2 and Al Amerat Package 3.")

    D.h(d, 2, "20.8   What the appraisal must produce")
    D.bullet(d, "capital cost by option and by phase")
    D.bullet(d, "operating cost by option and by year")
    D.bullet(d, "net present value of each option at 5 % over 25 years")
    D.bullet(d, "carbon in tonnes of carbon dioxide equivalent per year and per "
                "cubic metre, against the benchmark")
    D.bullet(d, "in-country value, assessed holistically at this stage")
    D.bullet(d, "sensitivity results on all three variables")
    D.bullet(d, "a risk register with costed impacts")
    D.bullet(d, "input to the Pre-Investment Appraisal Document")

    D.callout(d, "The tie-break makes sustainability decisive, not decorative.",
              "Where options fall within ten per cent of one another on total "
              "lifetime cost, the more sustainable option is to be adopted. "
              "Since three options compared on twenty-five year cost will often "
              "land inside ten per cent of each other, the carbon and circular "
              "economy work frequently decides the outcome — and it has to be "
              "done to a standard that can carry that weight.")
    _source(d, "G201 §12.2 to §12.9 p95-106; §7.1 p57 for asset lives; "
               "Table 2 p19-22 for the concept-stage cost deliverable.")
