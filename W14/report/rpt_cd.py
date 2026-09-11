"""Part C - basis of design.   Part D - demand and flows.   Revision 2."""
import os

import doc as D
import notes as N
import omml as M
import facts_w14 as F

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
UP, R = M.up, M.r


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows,
            widths=[3.4, 9.6, 3.5], font=9)


def _fig(d, name, caption):
    """A map goes on its own A4 landscape page."""
    D.wide_figure(d, os.path.join(IMG, name + ".png"), caption, size="A4")


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
    D.p(d, "The departures from the guidelines that arise from the data "
           "available, and the items that await data, are set out below "
           "with the reason and the position adopted; confirmation is "
           "requested.")

    D.tab_caption(d, "Departures from the design guidelines")
    D.table(d, ["Subject", "Guideline position", "Position adopted", "Reason"], [
        ["Occupancy rate",
         "Population divided by housing units, both from NCSI",
         "Settlement population divided by the domestic electricity meters "
         "counted in the settlement, with a floor and a cap",
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
         "Every metered property counted as connected from 2024; pipes and "
         "the plant are sized on the full load, and the early-year "
         "self-cleansing case takes the connection ratio of the Inception "
         "Report",
         "Sizing on the full load is the safe side; the ratio is carried "
         "separately where under-estimation would be the risk"],
        ["Design flow standard",
         "Where detailed land use is available, design flows calculated to "
         "a stated international standard such as BS EN 752",
         "The planning ratios and return rates of the guideline, applied plot "
         "by plot",
         "The quantities a detailed method requires are not held; the "
         "standard will be stated when they are"],
        ["Growth beyond the forecast",
         "Not extrapolated more than ten years beyond the available forecast",
         "The Inception Report series to 2100, used for its growth rates "
         "only",
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
        M.sub(UP("log"), R("10")),
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
        ["Organic load", "not less than 60 g BOD per person per day; the "
         "measured strength of the existing works governs once received",
         "PAM-GUD-203 p74"],
        ["Solids load", "not less than 80 g suspended solids per person per day",
         "PAM-GUD-203 p74"],
        ["COD to BOD ratio, domestic", "1.8 to 2.2", "PAM-GUD-203 p74"],
        ["Effluent standard", "Class A of MD 145/1993", "PAM-GUD-203 p69"],
        ["Total nitrogen", "less than 15 mg/l as N", "PAM-GUD-203 p71"],
        ["Chlorine residual at the plant discharge", "0.3 to 1.0 mg/l",
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


# ===================================================== PART D
def part_d(d):
    D.part(d, "D", "Demand and flows")
    t = F.totals(); ps = F.plot_summary(); mc = F.meter_counts(); st = F.settlement_table()
    ib = [r for r in st if r["key"] == "IBRI"][0]
    ult = t["ultimate"]

    # --------------------------------------------------------------- 14
    D.h(d, 1, "14   Population and land use")

    D.h(d, 2, "14.1   Approach")
    D.p(d, "The population of the study area, its distribution and its growth "
           "are established by counting rather than by assumption. Every "
           "domestic electricity meter is a property. Every plot takes its use "
           "from the meters on it. Every empty plot takes its future from the "
           "built plots around it. The official population series supplies the "
           "growth rate of each settlement and nothing else. The result is a "
           "population and an average sewage flow for every plot, today and in "
           "every year to the year the land is full, which is the saturation "
           "the Terms of Reference ask for.")

    p = D.p(d, "The distribution of population across the study area is shown "
               "below from the Global Human Settlement population grid. The "
               "grid is a third-party product and is used to show where "
               "population lies, not how much of it there is.")
    N.add(p, "GHS-POP, European Commission Joint Research Centre, 2025 epoch "
             "at 100 m resolution, licensed under Creative Commons Attribution "
             "4.0. The grid distributes census counts across built-up surface "
             "and is therefore modelled rather than observed.")

    D.picture(d, os.path.join(IMG, "M06_population.png"), 16.0)
    D.fig_caption(d, "Where the population of the study area lies. Density is "
                     "concentrated in Ibri town and along the wadi corridors, "
                     "and falls away sharply beyond them.")

    D.h(d, 2, "14.2   Settlements")
    D.p(d, "Every rule in this Part is applied settlement by settlement: the "
           "properties per plot, the occupancy, the share of empty land that "
           "becomes housing, the growth rate and the year the land is full are "
           "all properties of a settlement, not of the study area. Every plot "
           "must therefore belong to exactly one settlement. The settlement "
           "boundaries supplied with the Inception Report are polygons drawn "
           "around the built cores; they do not touch one another and they "
           "leave the land between them unassigned. Each plot has been "
           "assigned to the settlement whose boundary contains it, or, where "
           "none does, to the nearest, and the twenty-five boundaries have "
           "been redrawn as a partition of the whole study area, so that every "
           "plot lies in one settlement and the boundaries meet without gaps.")
    _fig(d, "M05_settlements",
         "The twenty-five settlements as a partition of the study area, over "
         "the cadastral plots. Every plot belongs to one settlement, and the "
         "rates used in this Part are set for each.")

    D.h(d, 2, "14.3   Properties per plot")
    p = D.p(d, f"Each domestic electricity meter is one property. Of the "
               f"{F.fmt(mc['total'])} meters, {F.fmt(mc['inside'])} fall inside a "
               f"plot; {F.fmt(mc['snapped'])} lie on a road or in a gap between "
               f"plots and have been assigned to the nearest plot within fifteen "
               f"metres; {F.fmt(mc['free'])} lie further from any plot and are "
               f"listed with their settlement and carry no load in the plot table. The plot table holds "
               f"{F.fmt(ps['properties'])} domestic properties.")
    N.add(p, "The primary, subsidised primary and additional-dwelling tariffs "
             "are counted as properties. Shop, government, farm and "
             "large-consumer meters carry no people.")

    D.p(d, "The number of properties on a built home plot is measured in each "
           "settlement over the plots that are homes and nothing else, "
           "excluding the few plots that carry fifteen or more dwelling meters, "
           "which are blocks of flats and workers' housing and would distort "
           "the ratio. Plots that also carry shops, farms or offices are "
           "counted for their people but not for the ratio.")

    D.tab_caption(d, "Properties per home plot, the principal settlements")
    D.table(d, ["Settlement", "Domestic properties", "Home plots measured",
                "Properties per home plot"],
            [[r["name"], F.fmt(r["properties"]), F.fmt(r["home_plots"]), f"{r['ratio']:.2f}"] for r in st[:8]],
            widths=[4.6, 4.0, 4.0, 4.0], font=9)
    D.p(d, "")
    p = D.p(d, f"Ibri carries {ib['ratio']:.2f} properties per home plot; the "
               f"principal settlements lie between 1.1 and 1.4. Four small "
               f"settlements with institutional housing on a handful of plots "
               f"return two or more; the thirteen settlements under a "
               f"thousand people take one property per plot, as Section 14.4 "
               f"sets out. The full table is given in Appendix A3.")
    N.add(p, f"{F.fmt(ps['pure_home_plots'])} home plots were measured across "
             f"the twenty-five settlements.")

    D.h(d, 2, "14.4   Occupancy rate")
    D.p(d, "The occupancy rate of each settlement is its population in 2024, "
           "the year of the electricity data, divided by the domestic "
           "properties counted in it.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("OR"), M.EQ,
                       M.frac(UP("Settlement population in 2024"),
                              UP("Domestic properties"))), number=eq)
    _params(d, [
        ["OR", "occupancy rate", "persons per property"]])

    small = [r["name"] for r in st if r["small"]]
    p = D.p(d, f"Two rules bound the derived rate. A floor of {F.OR_FLOOR:.1f} "
               f"persons per property: some settlements would otherwise return "
               f"between one and four, because their properties include the "
               f"housing of the police headquarters, the college and similar "
               f"institutions, whose occupants the census does not count as "
               f"residents; those meters discharge to the sewer whatever the "
               f"census says, and the floor keeps them in the design. And a cap "
               f"at the highest rate among the settlements of two thousand or "
               f"more people, {max(r['or_used'] for r in st):.2f}.")
    N.add(p, f"With the floor and the cap the study area holds "
             f"{F.fmt(t['pop_today'])} people against 116,452 in the official "
             f"series for the same twenty-five settlements; the difference is "
             f"the institutional housing.")
    p = D.p(d, f"A settlement of fewer than a thousand people in 2024 is "
               f"treated by one rule for all its rates: an occupancy of 4.0, "
               f"one property per plot, and a home share of 0.9. It has too "
               f"few meters to measure on, and a village of that size does not "
               f"attract second dwellings on a plot. The rule applies to "
               f"{len(small)} settlements: {', '.join(small)}.")
    N.add(p, "4.0 is the rate measured at At Tayyib, 3,300 people, the "
             "smallest settlement with a sample worth measuring. The nine "
             "settlements of 800 to 5,000 people pool to 4.6.")

    D.tab_caption(d, "Occupancy rate by settlement")
    D.table(d, ["Settlement", "Domestic properties", "Census population 2024",
                "Rate derived", "Rate adopted", "People in the design, 2024"],
            [[r["name"], F.fmt(r["properties"]), F.fmt(r["workbook_2024"]),
              f"{r['or_raw']:.2f}", f"{r['or_used']:.2f}", F.fmt(r["people_today"])] for r in st],
            widths=[3.6, 2.6, 2.8, 2.3, 2.3, 2.9], font=8.5)
    D.p(d, "")
    p = D.p(d, f"Ibri returns {ib['or_used']:.2f} persons per property. Over "
               f"the study area as a whole the census gives {F.census_rate():.2f}. Revision 1 of this "
               f"report adopted a single rate of 5.32 for all settlements; it "
               f"was the same division over the properties then attributed to "
               f"a plot, before the meters on roads and in gaps were assigned. "
               f"The rate per settlement replaces it, and every population and "
               f"flow in this report follows from the rates in the table.")
    N.add(p, "116,452 divided by 22,559 properties. Revision 1 divided by "
             "21,889.")

    D.chart(d, "C02_occupancy", 15.0)
    D.fig_caption(d, "Occupancy by settlement: the derived value and the value "
                     "adopted after the floor and the cap.")

    D.chart(d, "C04_population", 14.5)
    D.fig_caption(d, f"People in each settlement in 2024, from the domestic "
                     f"meters at the settlement's occupancy. Ibri holds "
                     f"{ib['people_today'] / t['pop_today'] * 100:.0f} per cent "
                     f"of the total.")

    D.h(d, 2, "14.5   Land use", page_break=True)
    D.p(d, "The cadastral layer received in September 2026 holds 77,265 "
           "plots. Its land-use field does not carry a government class, "
           "records whole districts under codes that mean unclassified, and "
           "on the plots that carry meters disagrees with the meters on "
           f"{F.fmt(F.cadastre_disagreement() * 100)} per cent of them. The use of every plot has therefore been derived, in a "
           "fixed order, from what is on it.")
    D.picture(d, os.path.join(IMG, "D6_landuse.png"), 14.5)
    D.fig_caption(d, "How the use of each plot is derived from the "
                     "electricity meters, the satellite and the plot itself.")

    D.numbered(d, "a plot inside one of the two industrial estates is "
                  "industrial;", restart=True)
    D.numbered(d, "the 177 plots of the old quarter of Ibri, recorded as "
                  "tourism in the cadastre, are heritage and carry no load;")
    D.numbered(d, "a plot with an agricultural meter is a farm;")
    D.numbered(d, "a plot that the satellite shows as a grove is a farm, "
                  "unless two thirds of its meters are shops or a majority "
                  "are government;")
    D.numbered(d, "a plot whose industrial meters equal or outnumber its "
                  "dwellings is industrial;")
    D.numbered(d, "otherwise the meters decide by proportion: more than two "
                  "thirds home makes a home; two thirds or more government "
                  "makes a government plot; two thirds or more shop makes a "
                  "shop; between those, a home with a shop where the shop "
                  "meters are at least as many as the government meters, and "
                  "a government plot where they are fewer;")
    D.numbered(d, "a plot without a meter is empty.")

    p = D.p(d, "The satellite test uses one cloud-free Sentinel-2 scene of "
               "9 September 2026. Bare ground in the study area returns a "
               "vegetation index of 0.08 and a date grove 0.8, and the palms "
               "are evergreen, so a single scene separates the two. A plot is "
               "a grove where at least 1,000 square metres of it read above "
               "0.30 with a mean above 0.20, or, for a small plot, where it is "
               "at least sixty per cent green. The thresholds were set on the "
               "489 plots that carry a farm meter and checked by inspection "
               "against the aerial imagery.")
    N.add(p, "Sentinel-2 Level 2A, tile 40QDL, red and near-infrared bands "
             f"at 10 m, normalised difference vegetation index. "
             f"{F.fmt(F.farm_bare_share() * 100)} per cent of the plots with a "
             f"farm meter fail the grove test: pump sites without a crop. That "
             f"is why the meter alone under-counts farms.")

    D.tab_caption(d, "Use of the built plots that carry a meter, and the heritage quarter")
    cls = ps["classes"]
    D.table(d, ["Use", "Plots", "Basis"], [
        ["Home", F.fmt(cls.get("Residential", 0)), "more than two thirds of the meters domestic"],
        ["Home with a shop", F.fmt(cls.get("Residential-Commercial", 0)), "mixed, with at least as many shop as government meters"],
        ["Shop", F.fmt(cls.get("Commercial", 0)), "two thirds or more of the meters commercial"],
        ["Government", F.fmt(cls.get("Government", 0)), "two thirds or more governmental; mixed, with more government than shop meters; or a majority on a green plot"],
        ["Farm", F.fmt(cls.get("Agricultural", 0)),
         f"a farm meter ({F.fmt(ps['farms_by'].get('AGR', 0))}) or a grove by satellite ({F.fmt(ps['farms_by'].get('GRN', 0))})"],
        ["Industrial", F.fmt(cls.get("Industrial", 0)), "inside an industrial estate, or industrial meters that match the dwellings"],
        ["Heritage", F.fmt(ps["heritage"]), "the old quarter of Ibri; no meter, no load"],
    ], widths=[3.4, 2.2, 10.9], font=9)

    D.chart(d, "C07_landuse", 14.0)
    D.fig_caption(d, f"Use of the built, metered plots as derived. Homes are "
                     f"{F.fmt(cls.get('Residential', 0) / ps['metered'] * 100)} per cent "
                     f"of the plots; farms, {F.fmt(cls.get('Agricultural', 0) / ps['metered'] * 100)} "
                     f"per cent, are found by the meter or by the satellite.")

    _fig(d, "M07_landuse",
         "Use of each plot as derived from the meters and the satellite. "
         "Empty plots are shown in grey.")

    D.h(d, 2, "14.6   Capacity of the empty land")
    p = D.p(d, f"Of the {F.fmt(ps['total'])} plots, {F.fmt(ps['empty'])} carry "
               f"no meter. Not all of them will become homes. A future home "
               f"plot must look like the built ones: between 200 and 1,000 "
               f"square metres, compact, and not a strip. Slivers below 200 "
               f"square metres, odd shapes and everything above 1,000 square "
               f"metres are left out of the count, as are groves, industrial "
               f"plots and the heritage quarter. {F.fmt(ps['capacity_plots'])} "
               f"empty plots pass that test.")
    N.add(p, "Compactness is the plot's area against that of its smallest "
             "enclosing rectangle, not less than 0.6; the rectangle's sides "
             "may not differ by more than three to one. Built home plots have "
             "a median area of 717 square metres and a median compactness of "
             "0.98. Shapes above 2,000 square metres are whole future "
             "districts drawn as one plot and take nothing until they are "
             "subdivided.")

    hs = F.home_share_range()
    D.p(d, f"A district also needs mosques, shops and offices, so not every "
           f"home-shaped plot becomes a home. The share that does is measured "
           f"in each settlement over its built, metered, home-shaped plots: "
           f"pure homes divided by all. Ibri returns {ib['home_share']:.2f}; "
           f"among the settlements of a thousand people or more the measured "
           f"share runs from {hs[0]:.2f} in {hs[1]}, with its workshops, to "
           f"{hs[2]:.2f} in {hs[3]}.")

    D.p(d, "The capacity of a settlement is then its home-shaped empty plots, "
           "multiplied by its home share, by its properties per home plot and "
           "by its occupancy rate.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("Capacity"), M.EQ,
                       UP("Empty home\u2011shaped plots"), M.TIMES,
                       UP("Home share"), M.TIMES,
                       UP("Properties per plot"), M.TIMES, UP("OR")), number=eq)
    _params(d, [
        ["Capacity", "people the empty land of the settlement can hold", "persons"],
        ["Home share", "share of home-shaped plots that become homes", "—"],
        ["OR", "occupancy rate of the settlement", "persons per property"]])
    p = D.p(d, f"The empty land of the study area holds {F.fmt(t['capacity'])} "
               f"people on this basis, against {F.fmt(t['pop_today'])} living "
               f"in it in 2024.")
    N.add(p, "The thirteen settlements under a thousand people take a home "
             "share of 0.9 and one property per plot, as Section 14.4 sets out.")

    D.h(d, 2, "14.7   Growth and the year the land is full")
    D.picture(d, os.path.join(IMG, "D7_saturation.png"), 14.5)
    D.fig_caption(d, "From the empty plot to the year each settlement fills.")

    gr = F.growth_rates()
    D.h(d, 3, "The growth series")
    p = D.p(d, "The population series of the Inception Report is used for its "
               "growth rates. It is built in three parts. To 2040 it is the "
               "National Centre for Statistics and Information forecast for "
               "the Wilayat of Ibri, Omani and expatriate population "
               "separately. From 2041 to 2050 it is an extrapolation of that "
               "forecast, documented in the technical note on population "
               f"issued with the Inception Report. From 2051 it rises from "
               f"{F.fmt(gr['r2051'], 1)} per cent a year to 2.40 by "
               f"{gr['year_240']} and stays at 2.40 to 2100, the planning "
               f"horizon instructed by Nama Water Services. The wilayat "
               f"population is then split between settlements in fixed shares "
               f"from the census, so every settlement carries the same annual "
               f"rate. Over 2024 to 2030 that rate averages "
               f"{F.fmt(gr['d2024_2030'], 1)} per cent a year, over the 2030s "
               f"{F.fmt(gr['d2030s'], 1)}, over the 2040s "
               f"{F.fmt(gr['d2040s'], 1)}, over the 2050s "
               f"{F.fmt(gr['d2050s'], 1)} and 2.4 from 2060. The series is not "
               f"a saturation figure: the land fills long before 2100.")
    N.add(p, "Inception Report Revision 0, Section 6, and the demand workbook "
             "issued with it, sheets Pop_Wilayat and Project Pop Settlements. "
             "Wilayat population 183,564 in 2024; the twenty-five settlements "
             "are 63.4 per cent of it in every year. The workbook total for "
             "the settlements is 691,264 in 2100.")
    D.chart(d, "C12_growth_rate", 14.0)
    D.fig_caption(d, "The annual growth rate of the population series, by "
                     "year: the census forecast to 2040, the extrapolation to "
                     "2050, and the rise to a constant 2.40 per cent beyond.")

    sy0 = {r["key"]: r["sat_year"] for r in st}
    D.h(d, 3, "Filling the land")
    p = D.p(d, "Each settlement grows at the rate of the series, applied to "
               "its counted population, and its growth fills its empty plots "
               "together and in proportion. When a settlement is full, its further growth "
               "moves to a neighbour. Ibri's overflow goes in parallel to Al "
               "Araqi, Al Qurayn and Shalashil, in the proportions seventy, "
               "twenty and ten per cent, then to Ad Dariz when those are full, "
               "then to the nearest settlement with room. At Tayyib's "
               "overflow goes first to Miayrid, the small settlement beside "
               "it. Every other settlement overflows to its nearest neighbour "
               "with room. The "
               "year a settlement's empty plots are full is its saturation "
               "year; the study area is saturated when the last of them fills.")
    N.add(p, "Inception Report demand workbook, sheet Project Pop "
             "Settlements, 2024 to 2100. The series is used for its growth "
             "rates only. Its total for 2100 is not a target and is not a "
             "saturation figure: the land is full before it is reached. The "
             "overflow routes reflect local knowledge of where Ibri's growth "
             "is taking place.")
    rcv = F.ibri_receivers(0); ar = next((r for r in rcv if r["receiver"] == "AL ARAQI"), None)
    top = rcv[0]
    D.p(d, f"The rule sets the order; the land sets the result. Al Araqi fills "
           f"in {sy0['AL ARAQI']}, a year after Ibri, so it takes only "
           f"{F.fmt(ar['people'] if ar else 0)} of Ibri's people, and most of "
           f"Ibri's overflow passes on: the largest route is to "
           f"{top['receiver_name']}, {F.fmt(top['people'])} people, and "
           f"{len(rcv)} settlements take some of Ibri's growth in all.")

    D.tab_caption(d, "Population at five-year intervals to saturation")
    cols, rows = F.five_year_rows("pop")
    hdr = ["Settlement"] + [str(c) for c in cols[1:-1]] + ["Saturation year", "Saturation population"]
    D.table(d, hdr, rows, widths=[2.3] + [0.95] * (len(hdr) - 3) + [1.5, 1.65], font=6.4, cell_margin=0.08)
    D.p(d, "")
    sy = {r["key"]: r["sat_year"] for r in st}
    p = D.p(d, f"Ibri fills in {sy['IBRI']} and Al Araqi in {sy['AL ARAQI']}, "
               f"Al Qurayn in {sy['AL QURAYN']}, Shalashil in {sy['SHALASHIL']} "
               f"and Ad Dariz in {sy['AD DARIZ']}. The last settlement fills "
               f"in {ult}, which is the saturation year of the study area, "
               f"with {F.fmt(t['pop_ult'])} people. A cell in the table is "
               f"blank once the settlement is full.")
    N.add(p, "Totals are rounded from the unrounded values and may differ by "
             "one from the sum of the rows. A settlement's population after its saturation year is its "
             "capacity plus what it held in 2024; its growth beyond that is "
             "housed elsewhere or not at all.")

    D.p(d, "The routes the overflow takes, and when, are set out below for "
           "every route carrying more than a thousand people; the full list "
           "is in Appendix A5, and the year each settlement would fill on "
           "its own growth alone is in Appendix A6.")
    D.tab_caption(d, "The main overflow routes")
    rts = [r for r in F.routes() if r["people"] >= 1000]
    D.table(d, ["From", "To", "People at saturation", "Donor full", "Receiver starts", "Receiver full"],
            [[r["donor_name"], r["receiver_name"], F.fmt(r["people"]), str(r["donor_full"] or ""),
              str(r["starts"] or ""), str(r["receiver_full"] or "")] for r in rts],
            widths=[3.2, 3.2, 2.6, 2.3, 2.6, 2.6], font=8.2)
    D.p(d, "")
    own = F.own_growth_saturation(); never = [r["name"] for r in own if r["own"] is None]
    p = D.p(d, f"The overflow matters. On its own growth alone, "
               f"{len(never)} of the twenty-five settlements would not fill "
               f"before 2100; with the overflow, every settlement fills by "
               f"{ult}. A network in those settlements sized on their own "
               f"growth would be sized for land that never fills; sized on "
               f"the overflow, it serves the plots that Ibri's growth "
               f"actually occupies.")
    N.add(p, "The settlements that never fill on their own growth: " + ", ".join(never) + ".")
    _fig(d, "M10_overflow",
         "Where the growth goes once a settlement is full. Arrows show the "
         "routes carrying five hundred people or more at saturation; the "
         "shading shows how much of each settlement's capacity is taken by "
         "its neighbours' overflow.")

    D.chart(d, "C08_growth", 15.0)
    D.fig_caption(d, "People by year to saturation, the six largest "
                     "settlements shown separately. The flat top of each band "
                     "is the year that settlement fills.")

    D.chart(d, "C10_fill_years", 14.5)
    D.fig_caption(d, "The year each settlement's empty plots are full. Ibri "
                     "and the settlements that take a thousand or more of its "
                     "people are marked.")

    D.h(d, 2, "14.8   Where the growth is placed")
    D.p(d, "For the network every empty plot matters, not only the ones "
           "counted as future homes, because the sewer that serves a street "
           "serves every plot on it. The people a settlement houses in a "
           "given year are therefore spread over all its empty plots up to "
           "2,000 square metres, in proportion to plot area capped at 1,000 "
           "square metres. A sliver takes a sliver's share and a large plot "
           "takes no more than a full-sized home plot. The sum over the plots "
           "equals the settlement's housed population by construction, so "
           "the network total and the treatment plant total are the same "
           "figure.")

    # --------------------------------------------------------------- 15
    D.h(d, 1, "15   Wastewater generation and design flows", page_break=True)

    D.picture(d, os.path.join(IMG, "D3_flow.png"), 15.5)
    D.fig_caption(d, "Derivation of the design flow, from the plot to the "
                     "pipe and the treatment plant.")

    D.h(d, 2, "15.1   Water demand")
    D.p(d, "Wastewater generation is derived from water demand. Four "
           "components are carried: domestic, non-domestic, governmental and "
           "special consumption. A household supplied by tanker is metered "
           "for electricity like any other and carries the domestic rate; the "
           "tanker volumes themselves are a data request and no separate "
           "term is carried (Section 10.1).")

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
               "expressed against domestic consumption. Per person they are "
               "36 and 23 litres a day, and the three are applied as separate "
               "streams, never combined into one rate. Each settlement's "
               "non-domestic and governmental water is placed on its shop and "
               "government meters in proportion to their number.")
    N.add(p, "PAM-GUD-201, Table 11, page 60. The column headings describe the "
             "ratios as distributed, being governorate volumes recorded "
             "between 2021 and 2023.")

    D.h(d, 2, "15.2   Special consumption: the industrial estates")
    p = D.p(d, "Two industrial estates lie inside the study area, at Al Tayyeb "
               "in the north-east of the town and at Tanam beside the "
               "treatment plant. Their meters are recorded on the commercial "
               "tariff, which is why an earlier reading of the data found no "
               "industrial estate. The guideline places such estates outside "
               "the population ratios, and they are treated as special "
               "consumption: a workforce of 4,500 at Al Tayyeb and 1,800 at "
               "Tanam, spread over their industrial plots in proportion to "
               "area, at the dry-industry rate of 93 litres per employee per "
               "day. Their meters take no share of the settlement's non-domestic "
               "or governmental water: an estate plot carries its workers, and the few "
               "dwellings on the estates carry the domestic rate like any "
               "other. "
               "The workforce is an assumption from the number of "
               "workshop meters and is to be replaced by the estates' own "
               "records. Section 16 describes the estates and the other "
               "identified projects.")
    N.add(p, "PAM-GUD-201, Section 7.3.1, page 59, and Table 12, page 61, "
             "dry industry. Al Tayyeb: 94 hectares, 202 industrial plots, "
             "1,035 meters. Tanam: 61 hectares, 105 plots, 409 meters. About "
             "five meters per plot and three to six workers per workshop give "
             "the assumed figures.")

    D.h(d, 2, "15.3   Return to the sewer")
    D.p(d, "Not all supplied water reaches the sewer. The proportion that does "
           "is applied by category.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("ww")), M.EQ,
                       R("0.85"), M.sub(R("Q"), UP("dom+tanker")), M.PLUS,
                       R("0.54"), M.sub(R("Q"), UP("ND+gov+special"))), number=eq)
    _params(d, [
        ["Q ww", "wastewater generated, before infiltration", "m³/d"],
        ["Q dom+tanker", "domestic demand; tanker supply added when its records are received", "m³/d"],
        ["Q ND+gov+special", "non-domestic, governmental and special demand", "m³/d"]])
    p = D.p(d, "Water supplied by tanker returns to the sewer at the same "
               "proportion as piped supply. The domestic rate of 164 litres a "
               "day measures network water only, so tanker supply is not "
               "inside the domestic stream; it is added when the "
               "filling-station records are received (Section 10.1).")
    N.add(p, "PAM-GUD-201, Table 19, page 71, which gives a single discharge "
             "ratio for domestic and tanker supply.")
    D.p(d, "Agricultural meters supply irrigation pumps and are taken to "
           "return nothing, and the estates' dry-industry demand is taken to "
           "return 54 per cent, as non-domestic supply does. Both are rules of "
           "this design, not of the guideline.")

    D.h(d, 2, "15.4   The flow from each plot")
    D.p(d, "Applied plot by plot, the rules above give every plot an average "
           "daily sewage flow for 2024. An existing plot is built from its "
           "meters and the rates of its settlement:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("plot")), M.EQ,
                       R("0.85"), M.TIMES, R("164"), M.TIMES, R("OR"), M.TIMES, M.sub(R("N"), UP("dom")), M.PLUS,
                       R("0.54"), M.TIMES, M.delim(M.seq(M.sub(R("U"), UP("nd")), M.sub(R("N"), UP("nd")), M.PLUS,
                                                        M.sub(R("U"), UP("gov")), M.sub(R("N"), UP("gov")), M.PLUS,
                                                        R("93"), M.sub(R("N"), UP("w"))))), number=eq)
    _params(d, [
        ["Q plot", "average sewage flow of the plot in 2024", "l/d"],
        ["OR", "occupancy adopted for the settlement (Table 15)", "persons per property"],
        ["N dom", "domestic meters on the plot, one property each", "—"],
        ["U nd", "non-domestic water per shop meter in the settlement", "l/d per meter"],
        ["N nd", "non-domestic meters on the plot; none counted on an estate plot", "—"],
        ["U gov", "governmental water per government meter in the settlement", "l/d per meter"],
        ["N gov", "government meters on the plot; none counted on an estate plot", "—"],
        ["N w", "workers on an industrial-estate plot", "—"]])
    D.p(d, "The unit rates are the settlement's non-domestic and governmental "
           "shares, divided equally among the meters that carry them:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("U"), UP("nd")), M.EQ,
                       M.frac(M.seq(R("0.22"), M.TIMES, R("164"), M.TIMES, M.sub(R("P"), UP("s"))), M.sub(R("N"), UP("nd,s")))), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("U"), UP("gov")), M.EQ,
                       M.frac(M.seq(R("0.14"), M.TIMES, R("164"), M.TIMES, M.sub(R("P"), UP("s"))), M.sub(R("N"), UP("gov,s")))), number=eq)
    _params(d, [
        ["P s", "people of the settlement in 2024", "—"],
        ["N nd,s", "shop meters of the settlement outside the industrial estates", "—"],
        ["N gov,s", "government meters of the settlement outside the industrial estates", "—"]])
    p = D.p(d, "The estates' meters take no share of the pool; an estate plot "
               "carries its workers at 93 litres a day, and the dwellings on "
               "it, if any, at the domestic rate. A "
               "settlement with no shop or government meter outside the "
               "estates keeps that share on its dwellings, in proportion to "
               "their people. A future plot carries the people it houses in "
               "the year at 171 litres a day each, all three streams "
               "together, since where its shops will stand is not known.")
    N.add(p, "164 × 0.85 + 36 × 0.54 + 23 × 0.54 = 171.3 litres per person per day.")
    ex = F.example_plot()
    D.p(d, f"Worked for an illustrative plot in {ex['name']} with four domestic, two "
           f"commercial and one government meter, at the settlement's "
           f"occupancy of {ex['or_used']:.2f} and its unit rates of "
           f"{F.fmt(ex['u_nd'])} and {F.fmt(ex['u_gov'])} litres a day per meter:")
    D.tab_caption(d, "The flow of one plot, worked from its meters")
    D.table(d, ["Stream and meters", "Water, l/d", "Return", "Sewage, l/d"], ex["rows"],
            widths=[7.0, 2.6, 1.8, 5.0], font=8.5)
    D.p(d, "")
    p = D.p(d, "The shares and the unit rates of every settlement are set out "
               "below. The sum of the plots equals the settlement in every column.")
    N.add(p, "The Tanam estate's plots lie across Tanam, Ad Dibayshi and Al "
             "Makhtibyah in the settlement partition, so its workforce appears "
             "under all three. A settlement with no shop or government meter "
             "outside the estates keeps that share on its dwellings. Two plots "
             "outside the estates carry a special meter each, one on the "
             "industrial tariff and one large consumer identified as "
             "industrial; they are loaded through their shop meters, their own "
             "consumption being unknown. Totals are rounded from the "
             "unrounded values and may differ by one from the sum of the rows.")
    D.tab_caption(d, "Water shares and unit rates by settlement, 2024")
    D.table(d, ["Settlement", "People", "Domestic m³/d", "Non-domestic share m³/d", "Governmental share m³/d",
                "Shop meters", "Government meters", "l/d per shop meter", "l/d per government meter", "Estates m³/d", "Sewage m³/d"],
            F.unit_rate_rows(), widths=[2.3, 1.1, 1.2, 1.5, 1.7, 1.0, 1.6, 1.4, 1.6, 1.0, 1.2], font=6.8, cell_margin=0.08, keep_together=False)
    D.p(d, "")
    p = D.p(d, f"In 2024 the study area generates {F.fmt(t['q_today'])} cubic "
               f"metres a day, of which {F.fmt(ps['s_dom'])} is domestic, "
               f"{F.fmt(ps['s_nd'])} non-domestic, {F.fmt(ps['s_gov'])} "
               f"governmental and {F.fmt(ps['s_spec'])} from the two estates.")
    N.add(p, "The plot layer delivered with this report carries the meters, "
             "the people, the unit rates, the water and the sewage of every "
             "plot by stream, and the population and flow for 2030, 2055 and "
             "the saturation year; the settlement layer carries the same at "
             "settlement level with the five-year steps (Appendix A4).")
    D.chart(d, "C11_streams", 13.0)
    D.fig_caption(d, "Average sewage flow in 2024 by stream.")

    D.h(d, 2, "15.5   Infiltration")
    p = D.p(d, "For newly constructed networks an allowance of 720 litres per "
               "day per kilometre of sewer is included. It is a property of "
               "the pipe, not of the plot, and is added along each run. "
               "Infiltration from stormwater is not considered.")
    N.add(p, "PAM-GUD-201, Section 7.4.3, page 72.")

    D.h(d, 2, "15.6   Peak flow")
    D.p(d, "Peak flow is a property of the flow accumulated in a pipe, not of "
           "a plot. For catchments of more than one hundred properties the "
           "peak daily flow is established by the Merrimack formula, applied "
           "to the sum of the plots upstream of each pipe. For a head of one "
           "hundred properties or fewer the guideline's alternative, the "
           "Peltier formula, is applied.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("pdf")), M.EQ, R("2.65"),
                       M.sup(M.sub(R("Q"), UP("adf")), R("0.879"))), number=eq)
    _params(d, [
        ["Q pdf", "peak daily flow", "Ml/d"],
        ["Q adf", "average daily flow", "Ml/d"]])
    p = D.p(d, "Both flows are expressed in megalitres per day. The peaking "
               "factor is the ratio of the two. At the treatment plant the "
               "average, the maximum day and the peak hour are taken from the "
               "same accumulated flow, with the design margin added and, once "
               "their records are received, the tanker deliveries.")
    N.add(p, "PAM-GUD-201, Section 7.4.2, pages 71 and 72. The Peltier alternative is 1.5 + 1/√Q, with the average flow in litres per second. The guideline states that "
             "the formula is to be used for a catchment or sub-catchment "
             "having over 100 properties, and recommends that the hourly peak "
             "factor should not exceed 5.0.")

    D.h(d, 2, "15.7   Projection through the design period")
    p = D.p(d, f"Flows are established annually and reported at five-year "
               f"intervals to saturation, as the Terms of Reference require. "
               f"The study area generates {F.fmt(t['q_today'])} cubic metres a "
               f"day in 2024, {F.fmt(t['q'][2030])} in 2030, "
               f"{F.fmt(t['q'][2055])} in 2055 and {F.fmt(t['q_ult'])} at "
               f"saturation in {ult}. The network is sized on the saturation "
               f"flow; the treatment plant is staged on the series.")
    N.add(p, "Average daily flows before infiltration and before the plant "
             "margin. The ultimate flow of about 49,700 cubic metres a day "
             "stated in the Inception Report was built on the connected "
             "population and a single occupancy rate; the figures here "
             "supersede it.")

    D.tab_caption(d, "Average sewage flow at five-year intervals to saturation, m³/d")
    cols, rows = F.five_year_rows("q")
    hdr = ["Settlement"] + [str(c) for c in cols[1:-1]] + ["Saturation year", "Saturation flow"]
    D.table(d, hdr, rows, widths=[2.3] + [0.95] * (len(hdr) - 3) + [1.5, 1.65], font=6.4, cell_margin=0.08)
    D.p(d, "")
    D.chart(d, "C09_flow", 15.0)
    D.fig_caption(d, "Average sewage flow of the study area by year, from "
                     "today's plots and from the empty plots as they fill. "
                     "The points mark the five-year reporting intervals.")

    _fig(d, "M09_saturation",
         "Average sewage flow of every plot at saturation. The network is "
         "sized on these flows, accumulated pipe by pipe.")

    # --------------------------------------------------------------- 16
    D.h(d, 1, "16   Trade effluent, identified projects and special consumption")
    D.p(d, "Discharges other than domestic sewage affect both the load on the "
           "treatment plant and the treatability of the influent. Where the "
           "ratio of chemical to biochemical oxygen demand exceeds the "
           "domestic range, a separate treatment line for high-strength "
           "wastewater is required if the volumes concerned are significant.")

    D.h(d, 2, "16.1   The large-consumer accounts")
    cs = F.crt_summary(); use = cs["use"]
    p = D.p(d, f"The electricity dataset carries {cs['total']} accounts on the "
               f"Cost Reflective Tariff, which applies above a consumption "
               f"threshold and says nothing about use: a shopping centre, a "
               f"hospital, a mosque and a factory all fall in it. Each account "
               f"has been placed by public records: named features in "
               f"OpenStreetMap, reverse geocoding, the aerial imagery and the "
               f"press. {use.get('Commercial', 0)} are commercial, "
               f"{use.get('Government', 0) + use.get('Education', 0) + use.get('Health', 0) + use.get('Religious', 0)} "
               f"governmental, educational, medical or religious, "
               f"{use.get('Industrial', 0)} industrial, "
               f"{use.get('Agricultural', 0)} agricultural pumps and "
               f"{use.get('Telecom/Utility', 0)} telecommunications or "
               f"utility; {use.get('Unresolved', 0)} stand more than eighty "
               f"metres from any recorded feature and are carried as "
               f"commercial. Each account carries the evidence for its "
               f"placing and a confidence in the register delivered with this "
               f"report.")
    N.add(p, "The largest groups are the Bawadi shopping centre with twenty "
             "accounts, the commercial street of Al Murtafa with nineteen, "
             "the police headquarters, the college campus and the hospital.")

    D.h(d, 2, "16.2   Identified projects")
    D.p(d, "Beyond the accounts, the public record was searched for the "
           "projects the guideline keeps outside the population ratios: "
           "economic zones, camps and high-water users. Those found are "
           "listed below with the way each is treated.")
    D.tab_caption(d, "Identified projects and special consumption")
    D.table(d, ["Site", "What it is", "Treatment in the design"], [
        ["Al Tayyeb industrial area", "94 ha, 202 industrial plots, 1,035 meters, "
         "in the north-east of the town", "Special consumption, 4,500 workers at 93 l/d"],
        ["Tanam industrial area", "61 ha, 105 plots, 409 meters, beside the "
         "treatment plant", "Special consumption, 1,800 workers at 93 l/d"],
        ["Army camp, Northern Frontier Regiment", "296 ha, west of the town, "
         "no meter in the dataset", "Recorded; not connected to the network. Its "
         "occupancy and drainage are to be confirmed with the Ministry of Defence"],
        ["Ibri View resort", "A tourism development of 2 square kilometres at "
         "As Sulayf, announced, not yet in the cadastre", "Recorded; no load until "
         "its plan is issued"],
        ["Ibri Industrial City (Madayn)", "10 square kilometres, 8.6 km "
         "south-west of the boundary, first phase opened 2024 on a "
         "collection tank", "Outside the network; a source of tankered sewage "
         "to be confirmed from delivery records"],
        ["Power station and solar plants", "7.5 to 11 km north-west of the "
         "boundary, with a construction camp", "Outside the network; a source of "
         "tankered sewage to be confirmed"],
        ["Central slaughterhouse", "Announced; site not yet fixed", "High-"
         "strength discharge requiring pre-treatment; to be included when sited"],
    ], widths=[4.0, 6.2, 6.3], font=8.5)
    _fig(d, "M08_special",
         "The identified projects and special consumers: the industrial "
         "areas, the army camp, the treatment plant and the hotel sites "
         "recorded in OpenStreetMap, the two estates among them.")

    p = D.p(d, "Sewage delivered by tanker is materially stronger than sewage "
               "arriving through the network. It is to be provided for "
               "separately in the plant load once the delivery records are "
               "received.")
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
