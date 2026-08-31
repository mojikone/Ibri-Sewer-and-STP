"""Part C - basis of design.   Part D - demand and flows."""
import os

import doc as D
import notes as N
import omml as M

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
UP, R = M.up, M.r


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows,
            widths=[2.6, 10.4, 3.5], font=9)


# ===================================================== PART C
def part_c(d):
    D.part(d, "C", "Basis of design")

    # --------------------------------------------------------------- 10
    D.h(d, 1, "10   Codes, standards and departures")
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

    D.h(d, 2, "10.1   Departures")
    D.p(d, "Three departures from the guidelines arise from the data "
           "available. Each is set out below with the reason and the "
           "consequence, and confirmation is requested.")

    D.tab_caption(d, "Departures from the design guidelines")
    D.table(d, ["Subject", "Guideline position", "Position adopted", "Reason"], [
        ["Occupancy rate",
         "Population divided by housing units, both from NCSI",
         "Population divided by counted domestic electricity accounts",
         "Housing units are not published at settlement level"],
        ["Non-domestic and governmental demand",
         "Unit rates per pupil, bed, employee and floor area where detailed "
         "land use allocation is available",
         "The published governorate ratios",
         "The quantities the unit rates require are not recorded in any "
         "dataset held"],
        ["Allocation of non-domestic demand",
         "Distributed across the served population",
         "Placed on the plots that generate it",
         "A residential street generates no commercial flow; the total is "
         "unchanged and only its distribution differs"],
    ], widths=[3.0, 5.0, 4.2, 4.3], font=8.5)

    D.p(d, "")
    p = D.p(d, "The unit rates will be adopted for non-domestic and "
               "governmental demand as soon as the quantities they require "
               "become available.")
    N.add(p, "PAM-GUD-201, Table 12, page 61. The rates are expressed per "
             "pupil, per bed, per employee and per square metre of floor area.")

    # --------------------------------------------------------------- 11
    D.h(d, 1, "11   Level of service and resilience")
    D.p(d, "The systems are designed to convey and treat the flows arising "
           "across the design horizon without surcharge in the collection "
           "network and without loss of treatment capacity at the plant.")
    D.bullet(d, "sufficient capacity is provided that the design peak flow can "
                "be achieved with any one unit out of service.",
             lead="Redundancy — ")
    D.bullet(d, "a margin of ten per cent is applied to the treatment plant "
                "design flow, over and above redundancy.",
             lead="Design margin — ")
    D.bullet(d, "structures are sited and set above the flood levels described "
                "in Section 29, and the plant is to remain operational during "
                "floods.", lead="Flood resilience — ")
    D.bullet(d, "emergency provisions are described in Section 26.",
             lead="Failure — ")

    # --------------------------------------------------------------- 12
    D.h(d, 1, "12   Design criteria: collection network", page_break=True)
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
    D.h(d, 2, "12.1   Hydraulic formulation")
    D.p(d, "Full-bore velocity is computed by the Colebrook-White equation.")
    eq = D.next_eq()
    M.display(d, M.seq(
        R("V"), M.EQ, R("−2"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S"))),
        M.func("log", M.sub(R(""), R("10"))),
        M.delim(M.seq(
            M.frac(M.sub(R("k"), UP("s")), M.seq(R("3.7"), R("D"))), M.PLUS,
            M.frac(M.seq(R("2.51"), R("ν")),
                   M.seq(R("D"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S")))))),
            "[", "]")), number=eq)
    _params(d, [
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

    D.h(d, 2, "12.2   Sediment transport")
    D.p(d, "Two checks are applied together, and the steeper gradient "
           "resulting from them governs: the self-cleansing velocity above, "
           "and the minimum tractive force. At the head of the system, where "
           "the self-cleansing velocity cannot be achieved, the gradient is "
           "set by the tractive force method.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("S"), UP("min")), M.EQ, R("K"),
                       M.sup(R("τ"), R("1.23")),
                       M.sup(R("Q"), R("−0.461"))), number=eq)
    _params(d, [
        ["S min", "minimum gradient to move the deposited particle", "m/m"],
        ["τ", "tractive tension", "Pa"],
        ["Q", "flow", "m³/s or l/s, with K taken to suit"],
        ["K", "coefficient, 2.33 × 10⁻⁴ for Q in m³/s", "—"]])
    p = D.p(d, "The value of tractive tension to be adopted is not stated in "
               "the guidelines. A value will be proposed with its basis and "
               "confirmation requested before the gradients are fixed.")
    N.add(p, "The equation and its coefficient are given at PAM-GUD-203, "
             "page 27. No corresponding value of tractive tension in pascals "
             "is stated in PAM-GUD-203 or PAM-GUD-201.")

    # --------------------------------------------------------------- 13
    D.h(d, 1, "13   Design criteria: treatment plant", page_break=True)
    D.tab_caption(d, "Treatment plant design criteria")
    D.table(d, ["Criterion", "Value", "Reference"], [
        ["Design horizon", "not less than 15 years", "PAM-GUD-203 p65"],
        ["Planning life cycle", "25 years", "PAM-GUD-201 p57"],
        ["Design margin", "10 per cent", "PAM-GUD-201 p73"],
        ["Size category", "large where 20,000 m³/d or above",
         "PAM-GUD-203 p65"],
        ["Organic load", "not less than 60 g BOD per person per day",
         "PAM-GUD-203 p74"],
        ["Solids load", "not less than 80 g suspended solids per person per day",
         "PAM-GUD-203 p74"],
        ["COD to BOD ratio, domestic", "1.8 to 2.2", "PAM-GUD-203 p74"],
        ["Effluent standard", "Class A of MD 145/1993", "PAM-GUD-203 p69"],
        ["Total nitrogen", "less than 15 mg/l as N", "PAM-GUD-203 p71"],
        ["Chlorine residual at the plant", "0.3 to 1.0 mg/l at the consumer",
         "PAM-GUD-203 p71 and p130"],
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


# ===================================================== PART D
def part_d(d):
    D.part(d, "D", "Demand and flows")

    # --------------------------------------------------------------- 14
    D.h(d, 1, "14   Population and land use")

    D.h(d, 2, "14.1   Approach")
    D.p(d, "Population is established by two routes, as the guideline permits. "
           "The census route projects the official population series and "
           "distributes it to settlements. The plot route multiplies the "
           "number of plots by the properties on each and by the occupancy "
           "rate, and establishes the population at full development. The two "
           "answer different questions: the census route gives the population "
           "at a stated year, the plot route the ceiling that the land can "
           "hold.")

    D.h(d, 2, "14.2   Properties per plot")
    D.p(d, "The number of properties on each plot has been counted from the "
           "electricity accounts rather than assumed. Accounts falling within "
           "a plot are attributed to it. Accounts sharing a coordinate are "
           "counted individually, as each represents a separate connection.")

    D.tab_caption(d, "Domestic properties and plots")
    D.table(d, ["Quantity", "Value"], [
        ["Domestic accounts, including additional dwellings", "22,588"],
        ["Domestic accounts falling within a plot", "16,640"],
        ["Domestic accounts not falling within any plot", "5,948"],
        ["Plots carrying at least one domestic account", "11,425"],
        ["Mean domestic properties per plot", "1.46"],
    ], widths=[10.5, 6.0], font=9.5)

    D.p(d, "")
    p = D.p(d, "Approximately one quarter of domestic accounts do not fall "
               "within a mapped plot. This reflects the omissions in the "
               "cadastral layer described in Section 7.4. These accounts are "
               "held unattributed pending the corrected plot layer and the "
               "survey, and the mean above is computed only from accounts that "
               "are attributed.")
    N.add(p, "5,948 of 22,588 domestic accounts, being 26.3 per cent.")

    D.h(d, 2, "14.3   Occupancy rate")
    D.p(d, "The occupancy rate is derived by dividing the population of each "
           "settlement by the domestic properties counted within it. Both "
           "quantities are taken over the same ground.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("OR"), M.EQ,
                       M.frac(UP("Settlement population"),
                              UP("Domestic properties"))), number=eq)
    _params(d, [
        ["OR", "occupancy rate", "persons per property"]])

    D.tab_caption(d, "Occupancy rate")
    D.table(d, ["Quantity", "Value"], [
        ["Settlement population, 2024", "116,456"],
        ["Domestic properties within the settlements", "21,889"],
        ["**Occupancy rate adopted**", "**5.32 persons per property**"],
        ["Occupancy rate, Ibri settlement", "6.21 persons per property"],
    ], widths=[10.5, 6.0], font=9.5)

    D.p(d, "")
    p = D.p(d, "The derivation has been checked for consistency of coverage. "
               "The twenty-five settlements contain 63.4 per cent of the "
               "wilayat population. At the derived occupancy rate the wilayat "
               "as a whole would contain 34,504 domestic properties, of which "
               "the dataset holds 65.5 per cent. The two proportions agree "
               "within 2.1 percentage points, which confirms that the rate is "
               "a property of the data rather than an artefact of partial "
               "coverage.")
    N.add(p, "Wilayat population 183,564 in 2024, from the National Centre for "
             "Statistics and Information as reported in the Inception Report.")

    D.p(d, "Four settlements return values that are not consistent with the "
           "remainder and have been excluded from the derivation pending "
           "review of their boundaries against the account positions.")

    D.h(d, 2, "14.4   Land use")
    D.p(d, "Land use for each plot is established from the tariff carried by "
           "the accounts on it. The categories used are set out in Section 7.3. "
           "The dataset records the category of a connection but not its size, "
           "so it establishes which plots generate non-domestic demand but not "
           "how much each generates. The demand itself is therefore "
           "established as described in Section 15.")

    D.h(d, 3, "Agricultural plots")
    p = D.p(d, "An agricultural connection supplies an irrigation pump, and "
               "the water it lifts does not enter the sewer. Where a dwelling "
               "stands on an agricultural plot it carries its own domestic "
               "connection and is counted as a dwelling. Of 319 plots carrying "
               "an agricultural connection, 172 also carry domestic "
               "connections and are counted accordingly.")
    N.add(p, "Those 172 plots carry 428 domestic connections between them, an "
             "average of 2.49 per plot, against 1.46 for plots generally.")

    # --------------------------------------------------------------- 15
    D.h(d, 1, "15   Wastewater generation and design flows", page_break=True)

    D.picture(d, os.path.join(IMG, "D3_flow.png"), 15.5)
    D.fig_caption(d, "Derivation of the design flow, from counted properties to the flow the network is sized on.")

    D.h(d, 2, "15.1   Water demand")
    D.p(d, "Wastewater generation is derived from water demand. Demand "
           "comprises five components: domestic, non-domestic, governmental, "
           "special consumption, and consumption supplied by tanker.")

    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("dom")), M.EQ,
                       UP("Population"), M.TIMES, UP("LPCD")), number=eq)
    _params(d, [
        ["Q dom", "domestic water demand", "l/d"],
        ["LPCD", "unit consumption, 164 l/c/d for Adh Dhahirah", "l/c/d"]])

    D.p(d, "Non-domestic and governmental demand are established as "
           "proportions of domestic demand.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("ND")), M.EQ,
                       R("0.22"), M.sub(R("Q"), UP("dom"))), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("gov")), M.EQ,
                       R("0.14"), M.sub(R("Q"), UP("dom"))), number=eq)

    p = D.p(d, "The proportions are the values published for the Governorate "
               "of Adh Dhahirah. They represent the non-domestic and "
               "governmental volumes recorded in the governorate water balance "
               "expressed against domestic consumption. The total they produce "
               "is therefore a measured quantity; its distribution across the "
               "area is established from the land use in Section 14.4.")
    N.add(p, "PAM-GUD-201, Table 11, page 60. The column headings describe the "
             "ratios as distributed, being governorate volumes recorded "
             "between 2021 and 2023.")

    D.h(d, 2, "15.2   Return to the sewer")
    D.p(d, "Not all supplied water reaches the sewer. The proportion that does "
           "is applied by category.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("ww")), M.EQ,
                       R("0.85"), M.sub(R("Q"), UP("dom+tanker")), M.PLUS,
                       R("0.54"), M.sub(R("Q"), UP("ND+gov"))), number=eq)
    _params(d, [
        ["Q ww", "wastewater generated, before infiltration", "m³/d"],
        ["Q dom+tanker", "domestic demand and tanker supply", "m³/d"],
        ["Q ND+gov", "non-domestic and governmental demand", "m³/d"]])
    p = D.p(d, "Water supplied by tanker returns to the sewer at the same "
               "proportion as piped supply and is included accordingly.")
    N.add(p, "PAM-GUD-201, Table 19, page 71, which gives a single discharge "
             "ratio for domestic and tanker supply.")

    D.h(d, 2, "15.3   Infiltration")
    p = D.p(d, "For newly constructed networks an allowance of 720 litres per "
               "day per kilometre of sewer is included. Infiltration from "
               "stormwater is not considered.")
    N.add(p, "PAM-GUD-201, Section 7.4.3, page 72.")

    D.h(d, 2, "15.4   Peak flow")
    D.p(d, "For catchments of more than one hundred properties the peak daily "
           "flow is established by the Merrimack formula.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("pdf")), M.EQ, R("2.65"),
                       M.sup(M.sub(R("Q"), UP("adf")), R("0.879"))), number=eq)
    _params(d, [
        ["Q pdf", "peak daily flow", "Ml/d"],
        ["Q adf", "average daily flow", "Ml/d"]])
    p = D.p(d, "Both flows are expressed in megalitres per day. The peaking "
               "factor is the ratio of the two.")
    N.add(p, "PAM-GUD-201, Section 7.4.2, page 71. The guideline states that "
             "the formula is to be used for a catchment or sub-catchment "
             "having over 100 properties.")

    D.h(d, 2, "15.5   Projection through the design period")
    D.p(d, "Flows are established at five-year intervals across the design "
           "period, as required by the Terms of Reference. The calculation is "
           "carried out annually and reported at five-year intervals, so that "
           "the early years, in which the connected population is a fraction "
           "of the ultimate, are represented. The connection ratio applied in "
           "each year is taken from the demand model prepared at inception.")
    D.p(d, "The design horizon to be adopted is the subject of Section 5.1. "
           "The flow series will be issued in the next revision once the "
           "horizon is confirmed and the survey data is available.")

    # --------------------------------------------------------------- 16
    D.h(d, 1, "16   Trade effluent and industrial contributions")
    D.p(d, "Discharges other than domestic sewage affect both the load on the "
           "treatment plant and the treatability of the influent. Where the "
           "ratio of chemical to biochemical oxygen demand exceeds the "
           "domestic range, a separate treatment line for high-strength "
           "wastewater is required if the volumes concerned are significant.")
    D.p(d, "The electricity account dataset identifies 499 connections carrying "
           "the Cost Reflective Tariff, which is applied to consumers above a "
           "consumption threshold. These are being resolved against the plot "
           "layer to establish which represent industrial or other "
           "high-strength sources. A register of such sources, with the "
           "pre-treatment required, will be presented in the next revision.")
    p = D.p(d, "Sewage delivered by tanker is materially stronger than sewage "
               "arriving through the network and is accounted for separately "
               "in the plant load.")
    N.add(p, "PAM-GUD-203, Table 31, page 68, gives tankered sewage at 350 to "
             "1,050 mg/l BOD against 350 to 400 mg/l for network sewage.")

    # --------------------------------------------------------------- 17
    D.h(d, 1, "17   Treated effluent demand and customers", page_break=True)
    D.p(d, "Treated effluent is produced at 95 per cent of the plant inflow. A "
           "further ten per cent is lost within the distribution network.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("delivered")), M.EQ,
                       R("0.90"), M.TIMES, R("0.95"), M.TIMES,
                       M.sub(R("Q"), UP("inflow"))), number=eq)
    _params(d, [
        ["Q delivered", "treated effluent available to customers", "m³/d"],
        ["Q inflow", "flow entering the treatment plant", "m³/d"]])

    D.p(d, "Customers are classified as public or private. Public consumers "
           "comprise the landscaping of highways, secondary roads, "
           "interchanges and roundabouts, and public parks. Private consumers "
           "comprise community parks, golf courses, private gardens, and "
           "nurseries and farms.")

    D.tab_caption(d, "Treated effluent demand for concept planning")
    D.table(d, ["Planting", "Summer demand", "Planting", "Summer demand"], [
        ["Shrubs", "20 to 40 l per plant per day", "Ground cover", "10 l/m²/d"],
        ["Palm trees", "120 to 165 l per plant per day", "Seasonal flowers",
         "10 l/m²/d"],
        ["Other trees", "40 to 80 l per plant per day", "Grass", "12 l/m²/d"],
        ["Hedges", "10 l per metre per day", "Roads and junctions",
         "10 l/m²/d"],
    ], widths=[3.8, 4.4, 3.8, 4.5], font=9)

    D.p(d, "")
    p = D.p(d, "Demand varies seasonally, at 100 per cent from June to August, "
               "75 per cent in spring and autumn and 50 per cent from December "
               "to February. The system is sized for the summer peak. "
               "Consumers whose average demand exceeds 500 cubic metres per "
               "day are assessed individually.")
    N.add(p, "PAM-GUD-201, Tables 21 to 23, pages 75 and 76. The rate for "
             "roads and junctions applies in the absence of specific "
             "vegetation information and is subject to municipality approval.")

    D.p(d, "The identification of customers, their present and potential "
           "demand and their development plans is in progress. The register "
           "will be presented in the next revision.")
