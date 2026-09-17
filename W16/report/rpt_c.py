"""Chapter 3 - basis of design.   Revision 3: the symbol lines, the gradient rule with the
tractive-force curve in the text, the 12 m rule, the flows and loads the plant is sized on."""
import os

import doc as D
import notes as N
import omml as M
import facts_w14 as F
import facts_basis as B
from basis_items import ask, adopt

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
IMG_B = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report_basis", "img")
UP, R = M.up, M.r
fmt = F.fmt


def part_c(d):
    D.chapter(d, "3.   Basis of design")
    D.p(d, "This chapter sets out the documents that govern the design and the "
           "departures from them, the level of service, and the design criteria for "
           "the collection network and the treatment plant.")

    # --------------------------------------------------------------- 10
    D.h(d, 2, "3.1.   Codes, standards and departures")
    D.p(d, "The design follows the Nama Water Services design guidelines and "
           "standard specifications. Where a value is taken from a guideline "
           "it is cited to the guideline and page.")

    D.tab_caption(d, "Governing documents")
    D.table(d, ["Reference", "Title"], [
        ["PAM-GUD-201", "General Design Guidelines, Revision 01, March 2026"],
        ["PAM-GUD-202", "Water and TSE Design Guidelines, Revision 01, March 2026"],
        ["PAM-GUD-203", "Wastewater Design Guidelines, Revision 01, March 2026"],
        ["MD 145/1993", "Ministerial Decision, treated effluent and sludge reuse"],
        ["MD 159/2005", "Ministerial Decision, discharge to the marine environment"],
        ["MD 41/2017", "Ministerial Decision, ambient air quality"],
    ], widths=[4.0, 12.5], font=9.5)

    D.h(d, 3, "3.1.1.   Departures")
    D.p(d, "The departures from the guidelines that arise from the data "
           "available, and the items that await data, are set out below with "
           "the reason and the position adopted. Those the guidelines do not "
           "settle are put to Nama Water Services as decisions in Section 1.5; "
           "the others are adopted and reported there.")

    D.tab_caption(d, "Departures from the design guidelines")
    D.table(d, ["Subject", "Guideline position", "Position adopted", "Reason"], [
        ["Occupancy rate",
         "Population divided by housing units, both from NCSI",
         "Settlement population divided by the domestic electricity meters "
         "counted in the settlement, with a floor and a cap (Decision 2)",
         "Housing units are not published at settlement level"],
        ["Non-domestic and governmental demand",
         "Unit rates per pupil, bed, employee and floor area where detailed "
         "land use allocation is available",
         "The published governorate ratios",
         "The quantities the unit rates require are not recorded in any "
         "dataset held"],
        ["Allocation of non-domestic demand",
         "Distributed across the served population",
         "Placed on the plots whose meters generate it",
         "A residential street generates no commercial flow; the total is "
         "unchanged and only its distribution differs"],
        ["Industrial estates",
         "Determined case by case with the developer",
         "An assumed workforce at the dry-industry unit rate",
         "No workforce or discharge record has been supplied; the assumption "
         "is stated and is to be replaced by the record"],
        ["Water supplied by tanker",
         "Assessed from the tanker filling station records",
         "Households on tanker supply carry the domestic rate like any other "
         "metered household; no separate tanker term",
         "No filling-station record is held; requested"],
        ["Other water sources",
         "Private wells and other non-network abstraction assessed",
         "Not assessed; every flow is on the network-accounted basis",
         "No record of private abstraction is held; requested"],
        ["Connection to the sewer",
         "Coverage rising to the whole served area by the end of the period",
         "Every metered property counted as connected; pipes and the STP are "
         "sized on the full load, and the early-year self-cleansing case takes "
         "the connection ratio of the Inception Report, 61 per cent in 2030",
         "Sizing on the full load is the safe side; the ratio is carried "
         "separately where over-estimation would be the risk"],
        ["Design flow standard",
         "Where detailed land use is available, design flows calculated to "
         "a stated international standard such as BS EN 752",
         "The planning ratios and return rates of the guideline, applied plot "
         "by plot",
         "The quantities a detailed method requires are not held; the "
         "standard will be stated when they are"],
        ["Minimum gradient",
         "The steeper of the self-cleansing and the minimum tractive force "
         "gradients",
         "Table 11 minimum gradients; the tractive force used at the concept "
         "stage only to list the pipes needing early washing, at a tractive "
         "tension of 1 Pa and with a floor of 1.5 l/s (Decision 7)",
         "The tractive tension is not stated in the guidelines; the method "
         "sets gradients at the preliminary design once it is confirmed"],
        ["Depth of cover",
         "About 10 to 12 m recommended as the point where excavation cost "
         "justifies pumping",
         "12 m applied as the limit at the concept stage, with a pumping "
         "station before it",
         "The excavation cost cannot be calculated without the detailed "
         "quantities"],
        ["Design horizon",
         "Completion plus twenty-five years, or the saturation of the area",
         "Both carried: 2055 and the saturation year 2070 (Decision 5)",
         "The Terms of Reference name both; the choice is for Nama Water "
         "Services"],
        ["Growth beyond the forecast",
         "Not extrapolated more than ten years beyond the available forecast",
         "The Inception Report series to 2100, used for its growth rates "
         "only (Decision 6)",
         "The land fills after 2050; the saturation year rests on the "
         "capacity of the cadastre, and the horizon to 2100 was instructed "
         "by Nama Water Services"],
    ], widths=[3.0, 5.0, 4.2, 4.3], font=8.5, keep_together=False)

    D.p(d, "")
    p = D.p(d, "The unit rates will be adopted for non-domestic and "
               "governmental demand as soon as the quantities they require "
               "become available.")
    N.add(p, "PAM-GUD-201, Table 12, page 61. The rates are expressed per "
             "pupil, per bed, per employee and per square metre of floor area.")

    # --------------------------------------------------------------- 11
    D.h(d, 2, "3.2.   Level of service and resilience")
    D.p(d, "The systems are designed to convey and treat the flows arising "
           "across the design horizon without surcharge in the collection "
           "network and without loss of treatment capacity at the STP.")
    D.bullet(d, "sufficient capacity is provided that the design peak flow can "
                "be achieved with any one unit out of service.",
             lead="Redundancy — ")
    D.bullet(d, "a margin of ten per cent is applied to the STP design flow, "
                "over and above redundancy.", lead="Design margin — ")
    D.bullet(d, "structures are sited and set above the flood levels described "
                "in Section 7.2, and the STP is to remain operational during "
                "floods.", lead="Flood resilience — ")
    D.bullet(d, "emergency provisions are described in Section 6.6.",
             lead="Failure — ")

    # --------------------------------------------------------------- 12
    D.h(d, 2, "3.3.   Design criteria: collection network")
    D.p(d, "The criteria below govern the gravity network. All are taken from "
           "the wastewater design guideline.")

    D.tab_caption(d, "Gravity sewer design criteria")
    D.table(d, ["Criterion", "Value", "Reference"], [
        ["Self-cleansing velocity", "not less than 0.75 m/s at peak flow",
         "PAM-GUD-203 p26"],
        ["Preferred velocity", "0.90 m/s at peak flow", "PAM-GUD-203 p26"],
        ["Maximum velocity", "3.0 m/s at the design depth of flow",
         "PAM-GUD-203 p27"],
        ["Depth of flow, up to 350 mm", "0.65 of the diameter at peak flow",
         "PAM-GUD-203 Table 10"],
        ["Depth of flow, above 350 mm", "0.50 of the diameter at peak flow",
         "PAM-GUD-203 Table 10"],
        ["Roughness, Colebrook-White", "1.5 mm for all sizes and materials",
         "PAM-GUD-203 p24"],
        ["Minimum cover", "1.3 m to the crown of the pipe",
         "PAM-GUD-203 p33"],
        ["Minimum cover with protection", "0.5 m", "PAM-GUD-203 p33"],
        ["Recommended maximum cover", "approximately 10 to 12 m",
         "PAM-GUD-203 p33"],
        ["Minimum diameter, laterals and mains", "200 mm outside diameter",
         "PAM-GUD-203 Table 6"],
        ["Maximum lateral length", "45 m", "PAM-GUD-203 Table 6"],
        ["Manhole spacing, 200 to 315 mm", "100 m", "PAM-GUD-203 Table 12"],
        ["Manhole spacing, 350 to 900 mm", "120 m", "PAM-GUD-203 Table 12"],
        ["Backdrop required", "where inverts differ by more than 600 mm",
         "PAM-GUD-203 p30"],
        ["Inlet angle at a manhole", "not less than 90 degrees to the flow",
         "PAM-GUD-203 p19 and p30"],
    ], widths=[6.2, 5.8, 4.5], font=9)

    D.p(d, "")
    D.h(d, 3, "3.3.1.   Hydraulic formulation")
    D.p(d, "Full-bore velocity is computed by the Colebrook-White equation.")
    eq = D.next_eq()
    M.display(d, M.seq(
        R("V"), M.EQ, R("−2"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S"))),
        M.sub(UP("log"), R("10")),
        M.delim(M.seq(
            M.frac(M.sub(R("k"), UP("s")), M.seq(R("3.7"), R("D"))), M.PLUS,
            M.frac(M.seq(R("2.51"), R("ν")),
                   M.seq(R("D"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S")))))),
            "[", "]")), number=eq)
    D.symbols(d, [
        ["V", "full-bore velocity", "m/s"],
        ["g", "acceleration due to gravity", "m/s²"],
        ["D", "internal diameter of the pipe", "m"],
        ["S", "hydraulic gradient", "m/m"],
        ["k s", "roughness coefficient, 1.5 mm", "m"],
        ["ν", "kinematic viscosity of the sewage", "m²/s"]])

    p = D.p(d, "Gradients are set so that the self-cleansing velocity is "
               "achieved at peak flow, and are checked against the minimum "
               "gradients tabulated in the guideline. The tabulated gradients "
               "correspond to a full-bore velocity of 0.75 m/s; the velocity "
               "at the design depth of flow is verified separately for each "
               "run.")
    N.add(p, "PAM-GUD-203, Table 11, page 29. The tabulated values have been "
             "reproduced using the Colebrook-White equation with a roughness "
             "of 1.5 mm at 15 degrees Celsius, and correspond to full-bore "
             "flow.")

    D.h(d, 3, "3.3.2.   Gradients and self-cleansing at the concept stage")
    p = D.p(d, "At the concept stage every pipe is laid at the guideline's "
               "minimum gradient for its size, rounded up to a step of 0.05 "
               "per cent, or 0.025 per cent for trunks of 500 mm and above. "
               "The steps are our rounding, so that the gradients are round "
               "figures on the drawings. The guideline asks for a second "
               "test, the minimum tractive force, and for the steeper of the "
               "two gradients to govern. At this stage that test is used only "
               "to list the pipes that will need washing in the early years, "
               "not to steepen them, because the tractive tension it needs is "
               "not given in the guideline. One pascal is used until Nama "
               "Water Services confirms a value. That is a departure from the "
               "guideline, stated here for approval.")
    N.add(p, "PAM-GUD-203, Table 11, page 29; Sections 4.2.2.1 and 4.3, pages "
             "25 to 29.")
    D.tab_caption(d, "Minimum gradients at the concept stage")
    D.table(d, ["Pipe size, mm", "200", "250", "315", "400", "500", "600", "700", "800", "900 and above"],
            [["Minimum gradient, mm/m"] + [f"{B.TABLE11[k]:.2f}" for k in (200, 250, 315, 400, 500, 600, 700, 800, 900)]],
            widths=[3.6] + [1.3] * 8 + [2.0], font=8.5)
    D.p(d, "")
    D.p(d, "The tractive-force test gives the minimum gradient that moves the "
           "deposited particle at a given flow.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("S"), UP("min")), M.EQ, R("K"),
                       M.sup(R("τ"), R("1.23")),
                       M.sup(R("Q"), R("−0.461"))), number=eq)
    D.symbols(d, [
        ["S min", "minimum gradient to move the deposited particle", "m/m"],
        ["τ", "tractive tension, 1 pascal at the concept stage", "Pa"],
        ["Q", "flow in the pipe", "m³/s"],
        ["K", "coefficient, 2.33 × 10⁻⁴ for the flow in m³/s", ""]])
    p = D.p(d, f"The chart on the next page shows what the test asks of a pipe. "
               f"It is a curve: the smaller the flow, the steeper the pipe must "
               f"be. A 200 mm pipe at its minimum gradient of 0.5 per cent "
               f"passes the test at {B.table11_points()[200]:.2f} l/s and "
               f"above. Below that, at the very head of a street, no practical "
               f"gradient passes; those pipes go on the washing list. A design "
               f"floor is proposed: a pipe carrying less than 1.5 l/s is "
               f"checked as if it carried 1.5, for which the curve asks "
               f"{B.mara_smin_pct(1.5):.2f} per cent, so a 200 mm pipe at the "
               f"Table 11 gradient always passes.")
    N.add(p, "The relationship of Mara, Sleigh and Taylor, PAM-GUD-203, page "
             "27. No value of tractive tension in pascals is stated in "
             "PAM-GUD-203 or PAM-GUD-201. The audit on the test area gave 70 "
             "per cent of the length as needing early washing, all of it "
             "200 mm pipe carrying under 1.3 l/s.")
    D.p(d, "At the meeting of 16 September 2026 Nama Water Services indicated "
           "that the gradient obtained from the tractive-force method is "
           "limited to a maximum of 4 per cent at the head pipes. How that "
           "limit is applied will be confirmed with Nama Water Services "
           "(Section 1.5.4).")
    ask(d, 7)
    D.wide_figure(d, os.path.join(IMG_B, "K01_mara_full.png"),
                  "The minimum gradient by tractive force at one pascal against the flow in the pipe, "
                  "with the Table 11 minimum of every size marked where it meets the curve, and the 1.5 l/s floor.",
                  size="A4")

    D.h(d, 3, "3.3.3.   Depth of cover and pumping")
    p = D.p(d, "A gravity sewer goes deeper the further it runs. The guideline "
               "recommends about 10 to 12 metres of cover as the point where "
               "the cost of excavation justifies a pumping station. That cost "
               "cannot be calculated without the detailed quantities, so 12 "
               "metres is applied as the limit at this stage: where a sewer "
               "would pass it, a station is placed before that point and the "
               "sewer restarts at normal cover. The preliminary design looks "
               "deeper where the quantities allow the cost to be calculated.")
    N.add(p, "PAM-GUD-203, Section 4.6.3, page 33.")
    p = D.p(d, "The station's duty flow is the peak flow of the catchment it "
               "drains plus the infiltration of its sewers, at saturation. The "
               "rising main is sized on that duty: at least 0.75 metres a "
               "second, 1.0 where the pumps start and stop, and at most 2.5 "
               "metres a second.")
    N.add(p, "PAM-GUD-203, Section 8.1, page 50. Which chamber the main "
             "discharges into, and whether neighbouring stations are joined, "
             "are layout decisions of the options (Section 6.3).")
    adopt(d, 6)

    # --------------------------------------------------------------- 13
    D.h(d, 2, "3.4.   Design criteria: treatment plant")
    D.tab_caption(d, "Treatment plant design criteria")
    D.table(d, ["Criterion", "Value", "Reference"], [
        ["Design horizon", "not less than 15 years", "PAM-GUD-203 p65"],
        ["Planning life cycle", "25 years", "PAM-GUD-201 p57"],
        ["Design margin", "10 per cent", "PAM-GUD-201 p73"],
        ["Size category", "large where 20,000 m³/d or above",
         "PAM-GUD-203 p65"],
        ["Organic load", "not less than 60 g BOD per person per day; the "
         "measured strength at the existing STP governs once received",
         "PAM-GUD-203 p74"],
        ["Solids load", "not less than 80 g suspended solids per person per day",
         "PAM-GUD-203 p74"],
        ["COD to BOD ratio, domestic", "1.8 to 2.2", "PAM-GUD-203 p74"],
        ["Effluent standard", "Class A of MD 145/1993", "PAM-GUD-203 p69"],
        ["Total nitrogen", "less than 15 mg/l as N", "PAM-GUD-203 p71"],
        ["Chlorine residual at the STP discharge", "0.3 to 1.0 mg/l",
         "PAM-GUD-203 p71"],
        ["Chlorine residual at the consumer", "more than 0.3 and less than 1.0 mg/l",
         "PAM-GUD-203 p130"],
        ["Treated effluent produced", "95 per cent of the inflow",
         "PAM-GUD-201 p73"],
        ["Sludge produced", "0.25 kg per cubic metre of inflow, indicative",
         "PAM-GUD-201 p78"],
    ], widths=[6.2, 5.8, 4.5], font=9)

    D.p(d, "")
    p = D.p(d, "The total nitrogen limit is the governing criterion for "
               "process selection. Class A of Ministerial Decision 145/1993 "
               "does not itself set a total nitrogen limit, and the individual "
               "nitrogen limits it does set would together permit a higher "
               "concentration than 15 mg/l. Full nitrification and "
               "denitrification are therefore required.")
    N.add(p, "Class A permits ammoniacal nitrogen at 5 mg/l, organic nitrogen "
             "at 5 mg/l and nitrate at 50 mg/l as NO3, equivalent to 11.3 mg/l "
             "as N.")

    D.h(d, 3, "3.4.1.   The flows and loads the plant is sized on")
    p = D.p(d, "The STP is sized on three flows, and the guideline names what "
               "each one sizes: the average annual flow for the biological "
               "treatment, with the load; the peak hourly flow for everything "
               "the flow passes through; and the maximum day flow, which the "
               "guideline defines but gives no factor for. The maximum day "
               "flow is read from a year of daily records at the existing STP, "
               "requested in Section 1.5.5.")
    N.add(p, "PAM-GUD-203, Table 29, page 65, and Section 10.2.2.1, page 66.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("AAF")), M.EQ, R("1.10"), M.delim(M.seq(M.sub(R("Q"), UP("avg")), M.PLUS, M.sub(R("Q"), UP("inf"))))), number=eq)
    D.symbols(d, [["Q AAF", "average annual flow, the design average of the STP", "m³/d"],
                  ["Q avg", "average flow of the settlements upstream", "m³/d"],
                  ["Q inf", "infiltration of the whole network upstream, 720 l/d per km", "m³/d"],
                  ["1.10", "the 10 per cent margin the guideline requires for a new STP, over and above any standby", ""]])
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("PHF")), M.EQ, R("1.10"), M.delim(M.seq(M.sub(R("Q"), UP("peak")), M.PLUS, M.sub(R("Q"), UP("inf"))))), number=eq)
    D.symbols(d, [["Q PHF", "peak hourly flow, for the structures the flow passes through", "m³/d"],
                  ["Q peak", "the Merrimack peak of the average flow of the settlements upstream (Section 4.2.6)", "m³/d"]])
    p = D.p(d, "The margin is applied to the peak as to the average. The "
               "guideline does not state the order, and this reading is for "
               "confirmation. Section 4.2.8 gives the flows by year.")
    N.add(p, "PAM-GUD-201, Section 7.4.5, page 73.")
    p = D.p(d, "The biological treatment is sized on the load, not only the "
               "flow. No laboratory data for Ibri's sewage is held. The "
               "guideline sets a minimum for a new STP of 60 grams of BOD and "
               "80 grams of suspended solids per person per day, and gives the "
               "strength of raw sewage below. The per-person loads are used "
               "until the laboratory results of the existing STP are received, "
               "and the sewage brought by tanker, which is far stronger, is "
               "provided for separately once its records arrive.")
    N.add(p, "PAM-GUD-203, Section 10.3.1, page 74, \"at least 60 g of BOD5 per "
             "capita per day and 80 g of suspended solids\"; Table 30, page "
             "67; Table 31, page 68. Peak factors for the aeration design at a "
             "large STP: 1.2 on BOD and COD, 1.5 on TKN (page 74).")
    D.tab_caption(d, "Raw sewage strength the guideline gives, for the network and for tankers, mg/l")
    D.table(d, ["Parameter", "Network sewage", "Sewage by tanker, average to maximum"], [
        ["BOD", "350 to 400", "350 to 1,050"], ["COD", "700 to 900", "1,350 to 5,000"],
        ["Suspended solids", "400 to 500", "900 to 4,300"], ["Total Kjeldahl nitrogen", "60 to 80", "115 to 265"],
        ["Ammonia as nitrogen", "40 to 50", "70 to 125"], ["Total phosphorus", "10 to 15", "16 to 35"],
    ], widths=[5.6, 4.6, 6.3], font=9)
    D.p(d, "")
    D.chart(d, "R06_strength", 14.5)
    D.fig_caption(d, "The strength of raw sewage the guideline gives: through the network, and by tanker. The tanker ranges run from the average to the maximum.")
    adopt(d, 7)
