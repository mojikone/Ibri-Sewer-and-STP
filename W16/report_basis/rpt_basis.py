"""The Design Basis Report: settlement boundaries, population, flows and loads.

Every number is read from facts_w14 / facts_basis. The text is written in plain words
for approval: what was done, what value is used, why, and what is asked.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "report"))
sys.path.insert(0, HERE)

import doc as D  # noqa: E402
import notes as N  # noqa: E402
import omml as M  # noqa: E402
import facts_w14 as F  # noqa: E402
import facts_basis as B  # noqa: E402
from decisions import DECISIONS, DATA_REQUESTS  # noqa: E402

IMG = os.path.join(HERE, "img")
IMG_R = os.path.join(os.path.dirname(HERE), "report", "img")
UP, R = M.up, M.r
fmt = F.fmt


def _map(d, name, caption):
    return D.wide_figure(d, os.path.join(IMG, name + ".png"), caption, size="A4")


def _chart(d, name, caption, width=14.5, folder=None):
    D.chart(d, name, width, img=folder or IMG)
    return D.fig_caption(d, caption)


def _gap(d):
    D.p(d, "", space_after=2)


# ====================================================================== front
def front(d):
    t = F.totals(); ps = F.plot_summary()
    D.title(d, "Contents")
    D.toc(d, "1-2")
    D.p(d, "Figures", bold=True, colour=D.BLUE)
    D.list_of(d, "Figure")
    D.p(d, "Tables", bold=True, colour=D.BLUE)
    D.list_of(d, "Table")
    D.pagebreak(d)

    D.title(d, "What this report asks for")
    D.p(d, "This report sets out the ground on which the sewer network, the treated "
           "effluent network and the treatment plant for Ibri will be designed: where the "
           "settlements are, how many people live in them, how many the land can hold, "
           "and the sewage each part of the system must carry. All of it will be part of "
           "the Concept Design Report. It is issued now, on its own, so that Nama Water "
           "Services can confirm the foundation before the design is built on it.")
    p = D.p(d, f"The study area holds {fmt(t['pop_today'])} people in 2024 on the meters "
               f"counted, and generates {fmt(t['q_today'])} cubic metres of sewage a day. "
               f"Its empty land can hold {fmt(t['capacity'])} more. The last settlement fills "
               f"in {t['ultimate']}, with {fmt(t['pop_ult'])} people and {fmt(t['q_ult'])} "
               f"cubic metres a day. The network is sized on that figure; the plant is staged "
               f"on the years in between.")
    N.add(p, "Average flows before infiltration and before the plant margin. Sections 6 and 7 give the series.")
    D.p(d, "Nineteen points need a yes or a no. They are listed here, explained in the "
           "section named, and repeated in Section 10 with the answer sheet. Seven data "
           "requests follow in Section 9.")
    rows = [[str(i + 1), grp, title] for i, (grp, title, _) in enumerate(DECISIONS)]
    D.tab_caption(d, "The decisions asked for")
    D.table(d, ["", "Group", "Decision"], rows, widths=[0.9, 4.6, 10.9], font=9, keep_together=False)
    D.pagebreak(d)


# ====================================================================== 1
def s1_purpose(d):
    D.h(d, 1, "1   Purpose and how to read this report")
    D.p(d, "The concept design will be submitted as one document. Its later parts, the "
           "options for the network and the plant, rest on the numbers in this report. If "
           "a number here changes after the options are drawn, the options are drawn "
           "again. Confirming the foundation first avoids that.")
    D.p(d, "The report is written to be read in one sitting. Each section says what was "
           "done, what value is used, and why. Where a value is an assumption, it says so. "
           "Where the guideline gives a rule, the page is in a footnote. Section 8 collects "
           "every adopted value in one table; Section 10 is the answer sheet.")
    D.h(d, 2, "1.1   What it rests on")
    D.tab_caption(d, "Sources")
    D.table(d, ["Source", "What it gives"], [
        ["PAM-GUD-201, General Design Guidelines, rev. 01, March 2026", "water demand, return to the sewer, peak flow, infiltration, plant margin, treated effluent"],
        ["PAM-GUD-203, Wastewater Design Guidelines, rev. 01, March 2026", "self-cleansing, gradients, depth, plant flows, sewage strength"],
        ["Inception Report R0 and its demand workbook", "the population series to 2100, the settlement boundaries, the connection ratio"],
        ["Electricity accounts, 33,971 meters", "one dwelling per domestic meter; shops, offices, government and farm meters by tariff"],
        ["Cadastral plots, 77,265, Ministry of Housing and Urban Planning, September 2026", "the land: built or empty, and its area"],
        ["Sentinel-2 image of 9 September 2026", "which plots are groves"],
    ], widths=[7.0, 9.4], font=9)
    D.h(d, 2, "1.2   What it does not contain")
    D.p(d, "No network is laid here and no plant is sized. The report gives the flow that "
           "each element will be designed for and the rule for finding it. The layout of the "
           "sewers, the stations and the plant follow in the concept design, on these numbers.")


# ====================================================================== 2
def s2_boundaries(d):
    ps = F.plot_summary()
    D.h(d, 1, "2   The settlements and their boundaries", page_break=True)
    D.p(d, "Every rule in this report is applied settlement by settlement: the persons per "
           "property, the share of empty land that becomes housing, the growth rate and the "
           "year the land is full are all set for each settlement. So every plot must belong "
           "to exactly one settlement.")
    p = D.p(d, "The Inception Report supplied one polygon per settlement, drawn around the "
               "built core. The polygons do not touch, so the land between them belongs to "
               "nobody, and four of them, at Tanam, Satwah, Al Makhtibyah and Bat, miss "
               "part of the plots that carry the settlement's name. The map on the next page "
               "shows them in red.")
    N.add(p, "Final_Boundary_IBRI.kmz, issued with the Inception Report R0.")
    p = D.p(d, f"The boundaries were therefore redrawn. Each of the {fmt(ps['total'])} plots "
               f"was given the settlement whose polygon contains it, or, where none does, the "
               f"nearest one. The land was then divided so that every point belongs to the "
               f"settlement of the nearest plot, and the shared edges were smoothed. The "
               f"result, in blue on the map, covers the whole study area with twenty-five "
               f"settlements and no gaps. Nothing else changed: the names, the population "
               f"series and the plots are as received.")
    N.add(p, "A Voronoi division of the plot centroids by settlement, merged, clipped to the study area "
             "boundary and smoothed as a coverage so that neighbours share one line.")
    D.p(d, "The twenty-five settlements inside the study area carry 63.4 per cent of the "
           "wilayat's population in every year of the series. The other settlements of the "
           "wilayat lie outside the boundary and are not part of the design.")
    D.callout(d, "Decision 1.", "Adopt the redrawn boundaries as the settlement boundaries for the design.")
    _map(d, "B01_boundaries", "The settlement boundaries as received (red, dashed) and as redrawn for the design (blue). Every plot lies in one settlement and the boundaries meet without gaps.")


# ====================================================================== 3
def s3_people(d):
    t = F.totals(); ps = F.plot_summary(); mc = F.meter_counts(); st = F.settlement_table()
    ib = next(r for r in st if r["key"] == "IBRI"); cap = max(r["or_used"] for r in st)
    small = [r["name"] for r in st if r["small"]]
    D.h(d, 1, "3   People today", page_break=True)
    D.p(d, "The population is counted, not assumed. Every domestic electricity meter is a "
           "dwelling. The number of people in a dwelling is set for each settlement from the "
           "official population. The two together give the people on every plot in 2024, "
           "the year of the electricity data.")

    D.h(d, 2, "3.1   From the meters to the dwellings")
    p = D.p(d, f"The electricity dataset holds {fmt(mc['total'])} meters. {fmt(mc['inside'])} "
               f"of them fall inside a plot. {fmt(mc['snapped'])} lie on a road or in a gap "
               f"between plots and were given the nearest plot within fifteen metres. "
               f"{fmt(mc['free'])} lie further than that from any plot; Section 3.3 shows them. "
               f"Each meter on a household tariff is one dwelling: {fmt(ps['properties'])} "
               f"dwellings in all. Shop, office, government, farm and large-consumer meters "
               f"carry no people.")
    N.add(p, "The primary, subsidised primary and additional-dwelling tariffs count as dwellings. The "
             "499 large-consumer accounts were placed by public records; their use decides only where "
             "the shop and government water is placed, not how much there is.")

    D.h(d, 2, "3.2   Persons per dwelling")
    D.p(d, "The occupancy of each settlement is its population in 2024 divided by the "
           "dwellings counted in it.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("OR"), M.EQ, M.frac(UP("population of the settlement in 2024"), UP("dwellings counted in it"))), number=eq)
    D.symbols(d, [["OR", "occupancy, persons per dwelling", ""]])
    p = D.p(d, f"Three rules bound the result. A floor of {B.F.OR_FLOOR:.1f}: some settlements "
               f"would otherwise return between one and four persons per dwelling, because "
               f"their meters include the housing of the police, the college and similar "
               f"institutions, whose occupants the census does not count as residents. Those "
               f"dwellings discharge to the sewer whatever the census says, so the floor keeps "
               f"them in. A cap of {cap:.2f}, the highest rate among the settlements of two "
               f"thousand people or more. And a settlement of fewer than a thousand people "
               f"takes {B.F.OR_FLOOR:.1f} outright, one dwelling per home plot and a home share "
               f"of 0.9 (Section 6.1), because it has too few meters to measure on. That rule "
               f"applies to {len(small)} settlements.")
    N.add(p, f"{B.F.OR_FLOOR:.1f} is the rate measured at At Tayyib, 3,300 people, the smallest settlement with "
             f"a sample worth measuring. The cap is Bat's. The thirteen small settlements: {', '.join(small)}.")
    p = D.p(d, f"Ibri returns {ib['or_used']:.2f} persons per dwelling. Over the whole study "
               f"area the census gives {F.census_rate():.2f}. The guideline derives occupancy "
               f"from population and housing units published by the statistics centre; housing "
               f"units are not published at settlement level, and the counted dwellings are "
               f"used in their place.")
    N.add(p, "PAM-GUD-201, Section 7.2, page 59. The table below is the same as Table 15 of the Concept Design Report, Revision 2.")
    D.tab_caption(d, "Persons per dwelling by settlement, 2024")
    D.table(d, ["Settlement", "Dwellings", "Population 2024", "Rate worked out", "Rate adopted", "People in the design"],
            [[r["name"], fmt(r["properties"]), fmt(r["workbook_2024"]), f"{r['or_raw']:.2f}", f"{r['or_used']:.2f}", fmt(r["people_today"])] for r in st]
            + [["Total", fmt(sum(r["properties"] for r in st)), fmt(sum(r["workbook_2024"] for r in st)), "", "", fmt(t["pop_today"])]],
            widths=[3.8, 2.4, 2.8, 2.5, 2.4, 2.9], font=8.5, align_right={1, 2, 3, 4, 5}, keep_together=False)
    _gap(d)
    p = D.p(d, f"With the floor and the cap the study area holds {fmt(t['pop_today'])} people, "
               f"against 116,452 in the official series for the same settlements. The "
               f"difference is the institutional housing.")
    N.add(p, "116,452 divided by 22,559 dwellings gives the area-wide 5.16.")
    _chart(d, "C02_occupancy", "Persons per dwelling by settlement: the value worked out from the census and the meters, and the value adopted after the floor and the cap.", 15.0, IMG_R)
    D.callout(d, "Decision 2.", "Adopt the persons per dwelling of each settlement as in the table, with the floor, the cap and the rule for small settlements.")

    D.h(d, 2, "3.3   The 126 meters with no plot within 15 metres")
    fm = B.free_meters()
    p = D.p(d, f"{fm['count']} meters lie more than fifteen metres from any plot. {fm['domestic']} "
               f"of them are dwellings, about {fmt(round(fm['people'], -1))} people at their "
               f"settlement's occupancy; the rest are government, shop and farm meters. They "
               f"carry no load in the plot table today. The map on the next page shows where "
               f"they are, and Appendix A3 shows every one of them close up, with the plots "
               f"around it, so the reader can see why it did not snap: a meter on a road "
               f"reserve, at a pumping station, on a plot the cadastre does not carry.")
    N.add(p, "By tariff: " + ", ".join(f"{k} {v}" for k, v in sorted(fm["by_tariff"].items(), key=lambda kv: -kv[1])) + ".")
    D.callout(d, "Decision 3.", f"Leave these meters out of the plot loads, as now, or assign each to its nearest plot whatever the distance. About {fmt(round(fm['people'], -1))} people either way.")
    _map(d, "B05_free_meters", "The 126 meters more than fifteen metres from any plot, and the zoom panels of Appendix A3.")


# ====================================================================== 4
def s4_landuse(d):
    ps = F.plot_summary(); cls = ps["classes"]
    D.h(d, 1, "4   The use of each plot", page_break=True)
    p = D.p(d, f"The cadastre's own land-use field cannot be used as it stands: it has no "
               f"government class, it records whole districts under codes that mean "
               f"unclassified, and on the plots that carry meters it disagrees with the meters "
               f"on {fmt(F.cadastre_disagreement() * 100)} per cent of them. The use of every "
               f"plot has therefore been worked out from what is on it, in a fixed order.")
    N.add(p, "MoH_Plots, 77,265 plots, received September 2026.")
    D.numbered(d, "a plot inside one of the two industrial estates is industrial;", restart=True)
    D.numbered(d, "the 177 plots of the old quarter of Ibri, recorded as tourism, are heritage and carry no load;")
    D.numbered(d, "a plot with a farm meter is a farm;")
    D.numbered(d, "a plot the satellite shows as a grove is a farm, unless two thirds of its meters are shops or most are government;")
    D.numbered(d, "a plot whose industrial meters equal or outnumber its dwellings is industrial;")
    D.numbered(d, "otherwise the meters decide by proportion: more than two thirds dwellings makes a home, two thirds or more government makes a government plot, two thirds or more shops makes a shop, and a mix is a home with a shop, or a government plot where the government meters are the more;")
    D.numbered(d, "a plot without a meter is empty.")
    p = D.p(d, "The satellite test uses one cloud-free image. Bare ground in the study area "
               "reads 0.08 on the vegetation index and a date grove 0.8, so one image "
               "separates the two. A plot is a grove where at least 1,000 square metres of it "
               "read above 0.30 with a mean above 0.20, or, for a small plot, where at least "
               "sixty per cent of it is green.")
    N.add(p, f"Sentinel-2 Level 2A, tile 40QDL, 9 September 2026, red and near-infrared at 10 m. "
             f"{fmt(F.farm_bare_share() * 100)} per cent of the plots with a farm meter fail the grove "
             f"test: pump sites without a crop. That is why the meter alone under-counts farms.")
    D.tab_caption(d, "Use of the built plots that carry a meter")
    D.table(d, ["Use", "Plots", "How it was decided"], [
        ["Home", fmt(cls.get("Residential", 0)), "more than two thirds of the meters are dwellings"],
        ["Home with a shop", fmt(cls.get("Residential-Commercial", 0)), "a mix, with at least as many shop as government meters"],
        ["Shop", fmt(cls.get("Commercial", 0)), "two thirds or more of the meters are shops"],
        ["Government", fmt(cls.get("Government", 0)), "two thirds or more government; or a mix with more government than shop meters"],
        ["Farm", fmt(cls.get("Agricultural", 0)), f"a farm meter ({fmt(ps['farms_by'].get('AGR', 0))}) or a grove on the satellite ({fmt(ps['farms_by'].get('GRN', 0))})"],
        ["Industrial", fmt(cls.get("Industrial", 0)), "inside an industrial estate, or industrial meters that match the dwellings"],
        ["Heritage", fmt(ps["heritage"]), "the old quarter of Ibri; no meter, no load"],
        ["Empty", fmt(ps["empty"]), "no meter"],
    ], widths=[3.2, 2.0, 11.2], font=9, align_right={1})
    _gap(d)
    D.p(d, "The use decides where the shop and government water is placed and which empty "
           "plots can become homes. It does not change the total: that comes from the "
           "people and the rates of Section 5.")
    D.callout(d, "Decision 4.", "Adopt the use worked out from the meters and the satellite as the basis for placing the loads.")
    _map(d, "B02_landuse", "The use of each plot. Coloured plots are built and metered; empty plots are shown by their outline only.")


# ====================================================================== 5
def s5_demand(d):
    ps = F.plot_summary(); t = F.totals(); st = F.settlement_table()
    D.h(d, 1, "5   From water to sewage", page_break=True)
    D.p(d, "Sewage is worked out from water. Three streams are carried for every settlement: "
           "the water of its households, of its shops and offices, and of its government "
           "buildings. A fourth, the industrial estates, is added on its own. Each stream "
           "returns a fixed share to the sewer.")
    D.picture(d, os.path.join(IMG_R, "D3_flow.png"), 14.5)
    D.fig_caption(d, "From the plot to the pipe and the plant: what each step adds.")

    D.h(d, 2, "5.1   Water demand")
    p = D.p(d, "A person uses 164 litres a day at home. That is the value the guideline "
               "publishes for the Governorate of Adh Dhahirah, and it says the value applies "
               "until an updated figure is issued and should be validated by Nama Water "
               "Services before design.")
    N.add(p, "PAM-GUD-201, Table 11, page 60, and Section 7.3.1, page 59.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("dom")), M.EQ, UP("people"), M.TIMES, R("164")), number=eq)
    D.symbols(d, [["Q dom", "domestic water demand", "l/d"]])
    p = D.p(d, "Shops, offices and government buildings are added as shares of the domestic "
               "water: 22 per cent for shops and offices, 14 per cent for government. The "
               "guideline calls these shares distributed. They come from the governorate's "
               "water balance of 2021 to 2023, all the non-domestic water divided by all the "
               "domestic water, so they stand for the everyday shops, mosques, schools and "
               "offices that come with any population, and they are added whether or not a "
               "particular village has a shop today. They do not cover named projects such as "
               "economic zones, which are added separately.")
    N.add(p, "PAM-GUD-201, page 59: the ratios \"refer to spatially distributed non-domestic consumption that "
             "are to be added to the domestic consumption\" and \"do not apply to ... specific identified "
             "non-domestic projects such as economic zones\". Per person the shares are 36 and 23 litres a day.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("shops")), M.EQ, R("0.22"), M.sub(R("Q"), UP("dom")), R("        "),
                       M.sub(R("Q"), UP("gov")), M.EQ, R("0.14"), M.sub(R("Q"), UP("dom"))), number=eq)
    D.symbols(d, [["Q shops", "water of shops and offices in the settlement", "l/d"], ["Q gov", "water of government buildings in the settlement", "l/d"]])
    p = D.p(d, "The guideline prefers unit rates where detailed land use is known: so many "
               "litres per pupil, per hospital bed, per employee, per square metre of shop. "
               "None of those quantities is held for Ibri. Until they are, the ratios are used. "
               "They are not added on top of unit rates anywhere; it is one or the other.")
    N.add(p, "PAM-GUD-201, Table 12, page 61, and Sections 7.3.2 and 7.3.3, pages 60 and 61.")
    D.p(d, "The shares are placed where the water is used. Each settlement's shop water is "
           "divided equally among its shop meters, and its government water among its "
           "government meters, so the load sits on the shopping street and the school, not "
           "on the houses. A settlement with no shop or government meter keeps that share on "
           "its houses.")
    D.callout(d, "Decisions 5 and 7.", "Confirm 164 litres a day, 22 per cent and 14 per cent; and accept the ratios in place of unit rates until the quantities are supplied, with the shares placed on the shop and government meters.")

    D.h(d, 2, "5.2   Return to the sewer")
    p = D.p(d, "Not all water reaches the sewer. Households return 85 per cent, and so does "
               "water delivered by tanker; shops, offices, government buildings and the "
               "estates return 54 per cent. Farm meters feed irrigation pumps and return "
               "nothing.")
    N.add(p, "PAM-GUD-201, Table 19, page 71. The farm rule is a rule of this design: on 172 of 319 "
             "farm plots a household is metered separately from the pump.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("sewage")), M.EQ, R("0.85"), M.sub(R("Q"), UP("dom")), M.PLUS,
                       R("0.54"), M.delim(M.seq(M.sub(R("Q"), UP("shops")), M.PLUS, M.sub(R("Q"), UP("gov")), M.PLUS, M.sub(R("Q"), UP("estates"))))), number=eq)
    D.symbols(d, [["Q sewage", "average sewage flow, before infiltration", "l/d"], ["Q estates", "water of the industrial estates", "l/d"]])
    p = D.p(d, "For a person in a new home all three streams are added together: "
               "164 × 0.85 + 36 × 0.54 + 23 × 0.54 = 171.3 litres of sewage a day. That is "
               "the rate every future plot carries, because where its shops will stand is "
               "not known.")
    N.add(p, "36 and 23 are 22 and 14 per cent of 164.")
    D.callout(d, "Decision 6.", "Confirm 85 per cent for households and tanker supply and 54 per cent for the rest.")

    D.h(d, 2, "5.3   The industrial estates and other named sites")
    p = D.p(d, "Two industrial estates lie inside the study area, at Al Tayyeb in the "
               "north-east of the town and at Tanam beside the treatment plant. Their meters "
               "are on the commercial tariff. The guideline keeps such estates outside the "
               "ratios, so they are carried on their own: a workforce of 4,500 at Al Tayyeb "
               "and 1,800 at Tanam, at 93 litres a day each, the dry-industry rate. The "
               "workforce is an assumption from the number of workshop meters and is to be "
               "replaced by the estates' records.")
    N.add(p, "PAM-GUD-201, page 59 and Table 12, page 61. Al Tayyeb: 94 hectares, 202 plots, 1,035 meters. "
             "Tanam: 61 hectares, 105 plots, 409 meters. About five meters per plot and three to six "
             "workers per workshop give the figures.")
    D.tab_caption(d, "Named sites outside the ratios")
    D.table(d, ["Site", "What it is", "How it is carried"], [
        ["Al Tayyeb industrial area", "94 ha, 202 industrial plots", "4,500 workers at 93 l/d"],
        ["Tanam industrial area", "61 ha, 105 plots, beside the plant", "1,800 workers at 93 l/d"],
        ["Army camp", "296 ha west of the town, no meter", "recorded, no load; occupancy and drainage to be confirmed"],
        ["Ibri View resort", "2 km² at As Sulayf, announced", "recorded, no load until its plan is issued"],
        ["Ibri Industrial City (Madayn)", "10 km², 8.6 km outside the boundary", "outside the network; a source of tankered sewage to confirm"],
        ["Power station and solar plants", "7.5 to 11 km outside, with a camp", "outside the network; tankered sewage to confirm"],
    ], widths=[4.4, 5.6, 6.4], font=9)
    _gap(d)
    p = D.p(d, "Water delivered by tanker and water from private wells are in no flow. No "
               "filling-station or delivery record is held, and no record of private wells. "
               "Both are requested in Section 9. A household on tanker supply is metered for "
               "electricity like any other, so its people are counted; only the extra water "
               "is missing, and it can only raise the loads.")
    N.add(p, "PAM-GUD-201, Section 7.4, page 70: an assessment of private wells and other non-network sources is required.")
    D.callout(d, "Decision 8.", "Accept the assumed workforce of the two estates until their records are supplied.")

    D.h(d, 2, "5.4   The result for 2024")
    p = D.p(d, f"Applied plot by plot, the rules give {fmt(t['q_today'])} cubic metres of "
               f"sewage a day in 2024: {fmt(ps['s_dom'])} from households, {fmt(ps['s_nd'])} "
               f"from shops and offices, {fmt(ps['s_gov'])} from government buildings and "
               f"{fmt(ps['s_spec'])} from the two estates. The table gives the settlements.")
    N.add(p, "The sum of the plots equals the settlement in every column. The plot layer and the settlement "
             "layer are delivered with the Concept Design Report.")
    D.tab_caption(d, "Water and sewage by settlement, 2024, m³/d")
    rows = [[r["name"], fmt(r["people_today"]), fmt(r["w_dom"]), fmt(r["w_nd"]), fmt(r["w_gov"]),
             fmt(r["w_spec"]) if r["w_spec"] > 0 else "–", fmt(r["q_2024"])] for r in st]
    T = lambda k: sum(r[k] for r in st)
    rows.append(["Total", fmt(T("people_today")), fmt(T("w_dom")), fmt(T("w_nd")), fmt(T("w_gov")), fmt(T("w_spec")), fmt(T("q_2024"))])
    D.table(d, ["Settlement", "People", "Household water", "Shop and office water", "Government water", "Estates", "Sewage"],
            rows, widths=[3.6, 2.0, 2.4, 2.6, 2.4, 1.6, 1.8], font=8.5, align_right={1, 2, 3, 4, 5, 6}, keep_together=False)


# ====================================================================== 6
def s6_growth(d):
    t = F.totals(); ps = F.plot_summary(); st = F.settlement_table(); gr = F.growth_rates()
    ib = next(r for r in st if r["key"] == "IBRI"); hs = F.home_share_range(); no = B.no_overflow(); ult = t["ultimate"]
    D.h(d, 1, "6   How the land fills", page_break=True)
    D.p(d, "The population of 2024 is counted. The population at the end is set by the land: "
           "a settlement can only grow until its empty plots are built. Three things are "
           "needed: how many people the empty land can hold, how fast each settlement grows, "
           "and what happens when it is full.")
    D.picture(d, os.path.join(IMG_R, "D7_saturation.png"), 13.5)
    D.fig_caption(d, "From the empty plot to the year each settlement is full.")

    D.h(d, 2, "6.1   How many people the empty land can hold")
    p = D.p(d, f"Of the {fmt(ps['total'])} plots, {fmt(ps['empty'])} carry no meter. Not all "
               f"of them will become homes. A future home plot must look like the built ones: "
               f"between 200 and 1,000 square metres, compact, not a strip. Slivers below "
               f"200 square metres, odd shapes and everything above 1,000 square metres are "
               f"left out, as are groves, industrial plots and the heritage quarter. "
               f"{fmt(ps['capacity_plots'])} empty plots pass that test.")
    N.add(p, "Compactness is the plot's area against that of its smallest enclosing rectangle, not less than "
             "0.6, with the rectangle's sides no more than three to one. Built home plots have a median area "
             "of 717 square metres. Shapes above 2,000 square metres are whole future districts drawn as "
             "one plot; they take nothing until subdivided.")
    p = D.p(d, f"A district also needs mosques, shops and offices, so not every home-shaped "
               f"plot becomes a home. The share that does is measured in each settlement over "
               f"its built, metered, home-shaped plots. Ibri returns {ib['home_share']:.2f}; "
               f"among the settlements of a thousand people or more it runs from "
               f"{hs[0]:.2f} at {hs[1]} to {hs[2]:.2f} at {hs[3]}. The number of dwellings a "
               f"home plot carries is measured the same way; Ibri returns {ib['ratio']:.2f}.")
    N.add(p, "The settlements under a thousand people take 0.9 and one dwelling per plot, as in Section 3.2. "
             "The full table by settlement is in the Concept Design Report, Appendix A3.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("capacity"), M.EQ, UP("home‑shaped empty plots"), M.TIMES, UP("home share"), M.TIMES,
                       UP("dwellings per plot"), M.TIMES, UP("OR")), number=eq)
    D.symbols(d, [["capacity", "people the empty land of the settlement can hold", "persons"],
                  ["home share", "share of the home-shaped plots that become homes", ""],
                  ["OR", "persons per dwelling of the settlement", ""]])
    p = D.p(d, f"The empty land of the study area holds {fmt(t['capacity'])} people on this "
               f"basis, against {fmt(t['pop_today'])} living in it in 2024.")
    N.add(p, "Capacity by settlement: Appendix A2.")

    D.h(d, 2, "6.2   How fast each settlement grows")
    p = D.p(d, f"The growth rate comes from the population series of the Inception Report, "
               f"and nothing else is taken from it. To 2040 the series is the official forecast "
               f"for the wilayat; from 2041 to 2050 it is an extrapolation of that forecast; "
               f"from 2051 it rises from {fmt(gr['r2051'], 1)} per cent a year to 2.40 by "
               f"{gr['year_240']} and stays there to 2100, the horizon Nama Water Services "
               f"instructed. Every settlement carries the same annual rate, applied to its "
               f"counted population. The rate averages {fmt(gr['d2024_2030'], 1)} per cent a "
               f"year to 2030, {fmt(gr['d2030s'], 1)} in the 2030s, {fmt(gr['d2040s'], 1)} in "
               f"the 2040s, {fmt(gr['d2050s'], 1)} in the 2050s and 2.4 after 2060.")
    N.add(p, "Inception Report R0, Section 6, and the demand workbook, sheets Pop_Wilayat and Project Pop "
             "Settlements. The guideline allows an extrapolation of ten years beyond the available forecast; "
             "the series goes further, on the client's instruction, and the point is listed for confirmation.")
    D.p(d, "The series' total for 2100 is not a target. The land fills long before then.")
    _chart(d, "C12_growth_rate", "The annual growth rate of the series: the forecast to 2040, the extrapolation to 2050, and the rise to a constant 2.40 per cent.", 14.0, IMG_R)
    D.callout(d, "Decision 11.", "Accept the series as the source of the growth rates, including the constant 2.40 per cent a year after 2058.")

    D.h(d, 2, "6.3   What happens when a settlement is full: the overflow")
    p = D.p(d, "Each settlement grows at the rate of the series until its empty plots are "
               "built. Then its further growth has to go somewhere. Two readings are possible, "
               "and the choice between them is the largest single decision in this report.")
    D.bullet(d, "when a settlement is full, its further growth moves to a neighbour with "
                "room. Ibri's goes in parallel to Al Araqi, Al Qurayn and Shalashil, in the "
                "proportions seventy, twenty and ten per cent, then to Ad Dariz, then to the "
                "nearest settlement with room. At Tayyib's goes first to Miayrid. Every other "
                "settlement overflows to its nearest neighbour with room.", lead="With the overflow: ")
    D.bullet(d, "each settlement grows on its own rate and stops when it is full. The growth "
                "it cannot house is lost to the study area.", lead="Without: ")
    p = D.p(d, f"The difference is large. With the overflow every settlement fills by {ult} "
               f"and the study area holds {fmt(t['pop_ult'])} people. Without it, "
               f"{len(no['never'])} settlements never fill before 2100, the study area holds "
               f"{fmt(no['totals'][ult]['pop_own'])} people in {ult}, and "
               f"{fmt(t['pop_ult'] - no['totals'][ult]['pop_own'])} people of the series have "
               f"nowhere to go. A sewer in those settlements sized on their own growth would "
               f"be sized for land that never fills.")
    N.add(p, "The settlements that never fill on their own growth: " + ", ".join(no["never"]) + ". "
             "The overflow routes reflect local knowledge of where Ibri's growth is taking place.")
    _chart(d, "K03_overflow_totals", "People in the study area by year, with the overflow and without it.", 14.5)
    _chart(d, "K04_overflow_settlements", f"People at saturation in the ten settlements the choice affects most, with the overflow and without.", 14.5)
    D.tab_caption(d, f"Every settlement with and without the overflow: people in {ult} and the year it is full")
    rows = []
    for r in no["rows"]:
        rows.append([r["name"], fmt(r["capacity"]), fmt(r[ult]["pop_with"]), str(r["full_with"] or ""),
                     fmt(r[ult]["pop_own"]), str(r["full_own"]) if r["full_own"] else "not before 2100"])
    tot = no["totals"][ult]
    rows.append(["Total", fmt(t["capacity"]), fmt(tot["pop_with"]), str(ult), fmt(tot["pop_own"]), ""])
    D.table(d, ["Settlement", "Capacity, people", f"With the overflow: people {ult}", "full in", f"Own growth only: people {ult}", "full in"],
            rows, widths=[3.6, 2.4, 2.9, 1.7, 2.9, 2.5], font=8.5, align_right={1, 2, 3, 4}, keep_together=False)
    _gap(d)
    D.callout(d, "Decision 9.", "Adopt the overflow, or keep every settlement on its own growth.")
    _map(d, "B04_overflow", "Where the growth goes once a settlement is full. Arrows show the routes carrying five hundred people or more; the shading shows how much of each settlement's capacity is taken by its neighbours' overflow.")

    D.h(d, 2, "6.4   The year the land is full, and the design horizon")
    sy = {r["key"]: r["sat_year"] for r in st}
    p = D.p(d, f"With the overflow, Ibri fills in {sy['IBRI']}, Al Araqi in {sy['AL ARAQI']}, "
               f"Ad Dariz in {sy['AD DARIZ']}, and the last settlement in {ult}. That is the "
               f"saturation the Terms of Reference ask for: {fmt(t['pop_ult'])} people and "
               f"{fmt(t['q_ult'])} cubic metres of sewage a day. The Terms of Reference also "
               f"name a horizon of completion plus twenty-five years. The land fills later "
               f"than that, and a network sized on the earlier date would be full while the "
               f"plots around it were still being built. The saturation year is adopted.")
    N.add(p, "Concept Design Report R2, Section 14.7. The five-year series is in Appendix A1.")
    D.tab_caption(d, "The study area in the design years")
    D.table(d, ["Year", "People", "Average sewage flow, m³/d", "What it is"], [
        ["2024", fmt(t["pop_today"]), fmt(t["q_today"]), "today, from the meters"],
        ["2030", fmt(t["pop"][2030]), fmt(t["q"][2030]), "opening year"],
        ["2055", fmt(t["pop"][2055]), fmt(t["q"][2055]), "model year"],
        [f"{ult}", fmt(t["pop_ult"]), fmt(t["q_ult"]), "saturation: the land is full"],
    ], widths=[2.0, 3.0, 4.2, 7.2], font=9.5, align_right={1, 2})
    _gap(d)
    _chart(d, "C08_growth", "People by year to saturation, the six largest settlements shown separately. The flat top of each band is the year that settlement fills.", 15.0, IMG_R)
    D.callout(d, "Decision 10.", f"Adopt {ult}, the year the land is full, as the design horizon.")


# ====================================================================== 7
def s7_flows(d):
    t = F.totals(); ult = t["ultimate"]; pf = B.plant_flows(); pl = B.process_loads(); ts = B.tse()
    D.h(d, 1, "7   The flow each element is designed for", page_break=True)
    D.p(d, "Every plot now carries an average sewage flow for 2024, 2030, 2055 and the "
           "saturation year. What each element of the system is designed for follows from "
           "those plot flows by fixed rules, set out below element by element. The rules "
           "are the same wherever the element sits, so the client can check any one of them.")

    D.h(d, 2, "7.1   The plot")
    p = D.p(d, "The plot carries the average flow of its people and meters, and nothing else: "
               "no peak, no infiltration, no tankers. Those belong to the pipe and the plant. "
               "A new home carries 171.3 litres a day per person; an existing plot carries "
               "its own meters at the rates of Section 5.")
    N.add(p, "Fields QADF, Q_2030, Q_2055 and Q_ULT of the plot layer; POP and its years for the people.")

    D.h(d, 2, "7.2   The pipe")
    D.p(d, "A pipe is checked twice, on two different flows, because the two checks fail in "
           "opposite directions.")
    D.bullet(d, "the flow at saturation of every plot upstream, added up, peaked, plus "
                "infiltration along the pipe. Under-estimating it surcharges the pipe.",
             lead="Size and capacity: ")
    D.bullet(d, "the flow in 2030 of the plots upstream, with 61 per cent of the properties "
                "connected, peaked, and no infiltration. Over-estimating it declares a pipe "
                "self-cleansing while it silts.", lead="Self-cleansing: ")
    p = D.p(d, "The 61 per cent is the connection ratio of the Inception Report, reached by "
               "2028. It is never applied to the saturation flow: that would give a pipe in a "
               "new district most of its final flow in a year when it carries almost nothing.")
    N.add(p, f"Whole area: {fmt(t['q'][2030])} × 0.61 = {fmt(pf[2030]['low'])} m³/d in 2030, against "
             f"{fmt(t['q_ult'] * 0.61)} if the ratio were applied to saturation.")
    D.p(d, "Peak flow belongs to the pipe, not to the plot. Above 100 properties the Merrimack "
           "formula applies, at 100 or fewer the Peltier formula.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("peak")), M.EQ, R("2.65"), M.sup(M.sub(R("Q"), UP("avg")), R("0.879")),
                       R("        "), UP("or"), R("        "),
                       M.sub(R("Q"), UP("peak")), M.EQ, M.delim(M.seq(R("1.5"), M.PLUS, M.frac(R("1"), M.sqrt(M.sub(R("Q"), UP("m")))))), M.sub(R("Q"), UP("avg"))), number=eq)
    D.symbols(d, [["Q peak", "peak flow: the guideline's peak daily flow, equal to its peak hourly flow", "Ml/d"],
                  ["Q avg", "average flow of the plots upstream", "Ml/d"],
                  ["Q m", "the same average flow, in the Peltier formula", "l/s"]])
    p = D.p(d, "The guideline recommends that the hourly peak factor not exceed 5.0. It is a "
               "recommendation, applied as such. Infiltration is 720 litres a day per "
               "kilometre of new sewer, added along each pipe by its length; stormwater is "
               "not considered.")
    N.add(p, "PAM-GUD-201, Section 7.4.2, pages 71 and 72; Section 7.4.3, page 72. PAM-GUD-203, Table 29, "
             "page 65, defines the peak hourly flow and gives it the symbol QPDF.")
    p = D.p(d, "Gradients. At the concept stage every pipe is laid at the guideline's minimum "
               "gradient for its size, in steps of 0.05 per cent, or 0.025 per cent for trunks "
               "of 500 mm and above. The guideline asks for a second test, the minimum "
               "tractive force, and for the steeper of the two to govern. At this stage that "
               "test is used only to list the pipes that will need washing in the early years, "
               "not to steepen them, because the tractive tension it needs is not given in the "
               "guideline. One pascal is used until Nama Water Services confirms a value. "
               "That is a departure from the guideline, stated here for confirmation.")
    N.add(p, "PAM-GUD-203, Table 11, page 29; Sections 4.2.2.1 and 4.3, pages 25 to 29. The Mara, Sleigh and "
             "Taylor relationship on page 27, K = 2.33 × 10⁻⁴ with the flow in m³/s.")
    D.tab_caption(d, "Minimum gradients at the concept stage")
    D.table(d, ["Pipe size, mm", "200", "250", "315", "400", "500", "600", "700", "800", "900 and above"],
            [["Minimum gradient, mm/m"] + [f"{B.TABLE11[k]:.2f}" for k in (200, 250, 315, 400, 500, 600, 700, 800, 900)]],
            widths=[3.6] + [1.3] * 8 + [2.0], font=8.5)
    _gap(d)
    p = D.p(d, f"The chart shows what the tractive test asks of a pipe. It is a curve: the "
               f"smaller the flow, the steeper the pipe must be. A 200 mm pipe at its minimum "
               f"gradient of 0.5 per cent passes the test at {B.table11_points()[200]:.2f} litres "
               f"a second and above. Below that, at the very head of a street, no practical "
               f"gradient passes; those pipes go on the washing list. A design floor is "
               f"proposed: a pipe carrying less than 1.5 litres a second is checked as if it "
               f"carried 1.5, for which the curve asks {B.mara_smin_pct(1.5):.2f} per cent, so a "
               f"200 mm pipe at the Table 11 gradient always passes. The floor and the value of "
               f"one pascal are for Nama Water Services to confirm.")
    N.add(p, "The full curve with every size is in Appendix A4. The audit on the test area gave 70 per cent "
             "of the length as needing early washing, all of it 200 mm pipe carrying under 1.3 litres a second.")
    _chart(d, "K02_mara_minimal", "The minimum gradient the tractive-force test asks for, against the flow in the pipe, with the 200 mm line and the proposed 1.5 litres a second floor.", 14.0)
    D.callout(d, "Decisions 12 to 15.", "Confirm the connection ratio, the infiltration, the peak formulae, and the concept-stage rule for gradients and self-cleansing with its floor.")

    D.h(d, 2, "7.3   The pumping station and its rising main")
    p = D.p(d, "A gravity sewer goes deeper the further it runs. The guideline recommends "
               "about 10 to 12 metres of cover as the point where excavation cost justifies "
               "a pumping station. Nothing is costed at the concept stage, so 12 metres is "
               "applied as a hard limit: where a sewer would pass it, a station is placed "
               "before that point and the sewer restarts at normal cover. Each such pocket is "
               "a pumping station candidate.")
    N.add(p, "PAM-GUD-203, Section 4.6.3, page 33.")
    p = D.p(d, "The station's duty flow is the peak flow of the pocket it drains plus the "
               "infiltration of its sewers, at saturation. The rising main is sized on that "
               "duty: at least 0.75 metres a second, 1.0 where the pumps start and stop, and "
               "at most 2.5 metres a second.")
    N.add(p, "PAM-GUD-203, Section 8.1, page 50. Which chamber the main discharges into, and whether "
             "neighbouring stations are joined, are layout decisions of the concept design.")
    D.callout(d, "Decision 16.", "Accept 12 metres of cover as a hard limit at the concept stage.")

    D.h(d, 2, "7.4   The trunk sewers and the treatment plant")
    p = D.p(d, "The trunk sewers and the plant carry the sum of the settlements upstream. "
               "The plant is sized on three flows, and the guideline names what each one "
               "sizes: the average annual flow for the biological treatment, with the load; "
               "the peak hourly flow for everything the flow passes through; and the "
               "maximum day flow, which the guideline defines but gives no factor for.")
    N.add(p, "PAM-GUD-203, Table 29, page 65, and Section 10.2.2.1, page 66.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("AAF")), M.EQ, R("1.10"), M.delim(M.seq(M.sub(R("Q"), UP("avg")), M.PLUS, M.sub(R("Q"), UP("inf")))),
                       R("        "), M.sub(R("Q"), UP("PHF")), M.EQ, R("1.10"), M.delim(M.seq(M.sub(R("Q"), UP("peak")), M.PLUS, M.sub(R("Q"), UP("inf"))))), number=eq)
    D.symbols(d, [["Q AAF", "average annual flow, the design average of the plant", "m³/d"],
                  ["Q PHF", "peak hourly flow, for the structures the flow passes through", "m³/d"],
                  ["Q avg, Q peak", "average flow of the settlements upstream, and its Merrimack peak", "m³/d"],
                  ["Q inf", "infiltration of the whole network upstream, 720 l/d per km", "m³/d"],
                  ["1.10", "the 10 per cent margin the guideline requires for a new plant, over and above any standby", ""]])
    p = D.p(d, f"If the whole study area drains to one works, the flows are as in the table. "
               f"The network has not yet been laid over the whole area, so its infiltration "
               f"cannot be totalled; each 100 kilometres of new sewer adds "
               f"{fmt(100 * pf['infil_per_km'])} cubic metres a day with the margin. Tanker "
               f"deliveries are added when their records arrive. The maximum day flow is read "
               f"from a year of daily records at the existing works, requested in Section 9.")
    N.add(p, "PAM-GUD-201, Section 7.4.5, page 73, the margin. The margin is applied to the peak as to "
             "the average; the guideline does not state the order, and this reading is for confirmation.")
    yrs = B.years()
    D.tab_caption(d, "Flows at one works for the whole area, before infiltration and tankers, m³/d")
    D.table(d, ["Flow"] + [str(y) for y in yrs], [
        ["People"] + [fmt(pf[y]["people"]) for y in yrs],
        ["Average flow from the plots"] + [fmt(pf[y]["qadf"]) for y in yrs],
        ["Merrimack peak factor"] + [f"{pf[y]['pf']:.2f}" for y in yrs],
        ["Peak flow before the margin"] + [fmt(pf[y]["qpdf"]) for y in yrs],
        ["**Average annual flow with the margin**"] + [f"**{fmt(pf[y]['aaf'])}**" for y in yrs],
        ["**Peak hourly flow with the margin**"] + [f"**{fmt(pf[y]['phf'])}**" for y in yrs],
        ["Infiltration with the margin, to add to both", f"{pf['infil_per_km']:.2f} m³/d per km of sewer", "", "", ""],
        ["Maximum day flow", "from the existing plant's records", "", "", ""],
    ], widths=[6.2, 2.6, 2.6, 2.6, 2.6], font=9, align_right={1, 2, 3, 4})
    _gap(d)
    _chart(d, "K05_plant_flows", "Average and peak-hour flow at one works for the whole area, by year, with the margin.", 14.5)
    p = D.p(d, "The map on the next page gives every settlement's average flow at saturation "
               "and the four steps to a plant flow, so that any grouping of settlements into "
               "one or more works can be worked out by hand.")
    D.callout(d, "Decision 17.", "Confirm the plant flows as defined, and supply the existing plant's daily inflow records for the maximum day.")
    _map(d, "B03_saturation", "Average sewage flow of each settlement at saturation, and the four steps from the settlements in a catchment to the flow of its plant.")

    D.h(d, 2, "7.5   The load on the plant")
    p = D.p(d, f"The biological treatment is sized on the load, not only the flow. No "
               f"laboratory data for Ibri's sewage is held. The guideline sets a minimum for "
               f"a new plant: 60 grams of BOD and 80 grams of suspended solids per person per "
               f"day. At the flows above that is {fmt(pl[ult]['bod_mgl'])} milligrams of BOD "
               f"per litre at saturation, at the low end of the range the guideline gives for "
               f"raw sewage, 350 to 400. The per-person loads are adopted until the "
               f"laboratory results of the existing plant are supplied, and the sewage brought "
               f"by tanker, which is far stronger, is provided for separately once its records "
               f"arrive.")
    N.add(p, "PAM-GUD-203, Section 10.3.1, page 74, \"at least 60 g of BOD5 per capita per day and 80 g of "
             "suspended solids\"; Table 30, page 67; Table 31, page 68, tankered sewage at 350 to 1,050 mg/l "
             "BOD. Peak factors for the aeration design at a large plant: 1.2 on BOD and COD, 1.5 on TKN "
             "(page 74).")
    D.tab_caption(d, "Loads at one works for the whole area, from the per-person minima")
    D.table(d, ["", *[str(y) for y in yrs]], [
        ["People"] + [fmt(pl[y]["people"]) for y in yrs],
        ["BOD, kg/d"] + [fmt(pl[y]["bod_kgd"]) for y in yrs],
        ["Suspended solids, kg/d"] + [fmt(pl[y]["tss_kgd"]) for y in yrs],
        ["BOD as a concentration at the average flow, mg/l"] + [fmt(pl[y]["bod_mgl"]) for y in yrs],
        ["Suspended solids as a concentration, mg/l"] + [fmt(pl[y]["tss_mgl"]) for y in yrs],
        ["BOD at the peak factor of 1.2, kg/d"] + [fmt(pl[y]["bod_peak_kgd"]) for y in yrs],
    ], widths=[6.6, 2.5, 2.5, 2.5, 2.5], font=9, align_right={1, 2, 3, 4})
    _gap(d)
    D.tab_caption(d, "Raw sewage strength the guideline gives, for the network and for tankers, mg/l")
    D.table(d, ["Parameter", "Network sewage", "Sewage by tanker, average to maximum"], [
        ["BOD", "350 to 400", "350 to 1,050"], ["COD", "700 to 900", "1,350 to 5,000"],
        ["Suspended solids", "400 to 500", "900 to 4,300"], ["Total Kjeldahl nitrogen", "60 to 80", "115 to 265"],
        ["Ammonia as nitrogen", "40 to 50", "70 to 125"], ["Total phosphorus", "10 to 15", "16 to 35"],
    ], widths=[5.6, 4.6, 6.2], font=9)
    D.callout(d, "Decision 18.", "Accept 60 grams of BOD and 80 grams of suspended solids per person per day until the laboratory data of the existing plant are supplied.")

    D.h(d, 2, "7.6   Sewage other than domestic")
    p = D.p(d, "Sewage from industry and commerce, called trade effluent in the guidelines, "
               "affects the plant's load and how treatable the sewage is. Where its chemical "
               "to biochemical oxygen demand is above the domestic range, a separate line is "
               "needed if the volume is significant. In Ibri the two industrial estates are "
               "workshops on the commercial tariff; no wet industry has been found. The "
               "estates are carried at the dry-industry rate (Section 5.3), and no separate "
               "line is foreseen at this stage. A central slaughterhouse has been announced "
               "without a site; it will need pre-treatment and is added when sited.")
    N.add(p, "PAM-GUD-203, page 74: a COD to BOD ratio of 1.8 to 2.2 is typical of domestic sewage.")

    D.h(d, 2, "7.7   Treated effluent")
    p = D.p(d, "Treated effluent is produced at 95 per cent of the plant inflow, and a further "
               "10 per cent is lost in the treated effluent distribution network, so 85.5 per "
               "cent of the inflow reaches the customers. The customers, their demand and its "
               "seasonal pattern are being identified and will be presented in the concept "
               "design.")
    N.add(p, "PAM-GUD-201, Section 7.4.6.1, page 73, and Section 7.4.6.3 (b), page 76: \"a system loss of "
             "10 percent of all produced TSE shall be assumed\".")
    D.tab_caption(d, "Treated effluent available, one works for the whole area, m³/d")
    D.table(d, ["", *[str(y) for y in yrs]], [
        ["Plant inflow, design average"] + [fmt(ts[y]["inflow"]) for y in yrs],
        ["Produced, 95 per cent"] + [fmt(ts[y]["produced"]) for y in yrs],
        ["Delivered, less 10 per cent in the network"] + [fmt(ts[y]["delivered"]) for y in yrs],
    ], widths=[6.6, 2.5, 2.5, 2.5, 2.5], font=9, align_right={1, 2, 3, 4})
    D.callout(d, "Decision 19.", "Confirm 95 per cent produced and 10 per cent lost in the network.")


# ====================================================================== 8
def s8_assumptions(d):
    st = F.settlement_table(); cap = max(r["or_used"] for r in st)
    D.h(d, 1, "8   Every adopted value in one table", page_break=True)
    D.p(d, "The values below are the ones the design rests on. Where a value is the "
           "guideline's, its page is given. Where it is a choice of this design, the reason "
           "is given and the value is marked as such.")
    D.tab_caption(d, "Adopted values and assumptions")
    D.table(d, ["Value", "Adopted", "Why", "Source"], [
        ["Domestic water use", "164 l per person per day", "the published value for Adh Dhahirah; to be validated by NWS", "G201 Table 11, p60"],
        ["Shops and offices", "22 % of domestic", "the distributed ratio for the governorate", "G201 Table 11, p60"],
        ["Government", "14 % of domestic", "the distributed ratio; unit rates need quantities not held", "G201 Table 11, p60; §7.3.3, p61"],
        ["Return to the sewer", "85 % domestic and tanker; 54 % the rest", "the published discharge ratios", "G201 Table 19, p71"],
        ["Farm meters", "no sewage", "they feed irrigation pumps; the house on a farm is metered separately", "design rule"],
        ["Industrial estates", "4,500 and 1,800 workers at 93 l/d", "no record supplied; from the meter count", "assumption; G201 Table 12, p61"],
        ["Persons per dwelling", "per settlement; floor 4.0; cap " + f"{cap:.2f}", "institutional housing distorts the low ones; the cap is the highest large settlement", "design rule; G201 §7.2, p59"],
        ["Settlements under 1,000 people", "4.0, one dwelling per plot, home share 0.9", "too few meters to measure on", "design rule"],
        ["Future home plot", "200 to 1,000 m², compact", "the shape of the built home plots", "design rule"],
        ["Where the growth is placed", "all empty plots up to 2,000 m², by area capped at 1,000 m²", "the sewer serves every plot on its street", "design rule"],
        ["New home", "171.3 l of sewage per person per day", "164 × 0.85 + 36 × 0.54 + 23 × 0.54", "G201 Tables 11 and 19"],
        ["Growth rates", "the Inception Report series", "the official forecast and its extension; used for rates only", "Inception Report R0"],
        ["Overflow", "a full settlement's growth moves to its neighbours", "the land, not the series, sets the population", "design rule; Decision 9"],
        ["Design horizon", "saturation, 2070", "the year the last settlement fills", "TOR; Decision 10"],
        ["Connection in 2030", "61 % of properties", "the Inception Report ratio; used in the self-cleansing check only", "Inception Report R0"],
        ["Infiltration", "720 l/d per km, per pipe; none in the early-year check", "new networks", "G201 §7.4.3, p72"],
        ["Peak flow", "Merrimack above 100 properties; Peltier at or below", "the guideline's formulae", "G201 §7.4.2, p71 to 72"],
        ["Hourly peak factor ceiling", "5.0, a recommendation", "not applied silently", "G201 p72"],
        ["Minimum gradients", "Table 11, in 0.05 % steps; 0.025 % for trunks", "constructable and readable on drawings", "G203 Table 11, p29; design rule"],
        ["Tractive tension", "1 Pa; a 1.5 l/s floor", "no value in the guideline; for washing lists only at this stage", "G203 p27; Decision 15"],
        ["Self-cleansing velocity", "0.75 m/s at peak flow, 0.90 preferred", "the guideline", "G203 p26"],
        ["Depth of cover", "12 m hard limit; a station before it", "no costing at concept stage", "G203 §4.6.3, p33; Decision 16"],
        ["Rising main velocity", "0.75 to 2.5 m/s; 1.0 for start-stop pumping", "the guideline", "G203 §8.1, p50"],
        ["Plant margin", "10 % on average and peak", "new plants", "G201 §7.4.5, p73"],
        ["Plant loads", "60 g BOD, 80 g solids per person per day", "the guideline minimum; no laboratory data held", "G203 §10.3.1, p74"],
        ["Treated effluent", "95 % produced; 10 % lost in the network", "the guideline", "G201 p73, p76"],
        ["Tanker water, private wells", "not in any flow", "no records held; requested", "G201 §7.4, p70; §7.3.5, p61"],
    ], widths=[3.4, 4.4, 5.2, 3.4], font=7.8, keep_together=False, cell_margin=0.1)


# ====================================================================== 9
def s9_data(d):
    D.h(d, 1, "9   Data requested")
    D.p(d, "Seven items would improve or confirm the numbers in this report. None of them "
           "stops the concept design; each replaces an assumption with a record.")
    D.tab_caption(d, "Data requests")
    D.table(d, ["Item", "What is asked for", "Why"], [[a, b, c] for a, b, c in DATA_REQUESTS],
            widths=[3.6, 6.6, 6.2], font=9)


# ====================================================================== 10
def s10_decisions(d):
    D.h(d, 1, "10   Decisions requested", page_break=True)
    D.p(d, "Each line can be answered with a yes, a no, or one figure. A no on any line "
           "returns the report to the section named.")
    grp = None
    for i, (g, title, what) in enumerate(DECISIONS):
        if g != grp:
            D.p(d, g, bold=True, colour=D.MID, size=11, space_after=3)
            grp = g
        D.numbered(d, what, lead=f"{title}.  ", restart=(i == 0))
        d.paragraphs[-1].paragraph_format.space_after = D.Pt(6)


# ====================================================================== appendices
def appendices(d):
    t = F.totals(); ult = t["ultimate"]; no = B.no_overflow(); fm = B.free_meters()
    D.h(d, 1, "Appendix A1   People and sewage by settlement, five-year steps to saturation", page_break=True)
    D.p(d, "A cell is blank once the settlement is full. Totals are rounded from the "
           "unrounded values and may differ by one from the sum of the rows.")
    for kind, title in (("pop", "People"), ("q", "Average sewage flow, m³/d")):
        cols, rows = F.five_year_rows(kind)
        hdr = ["Settlement"] + [str(c) for c in cols[1:-1]] + ["Full in", "At saturation"]
        D.tab_caption(d, f"{title} at five-year intervals")
        D.table(d, hdr, rows, widths=[2.3] + [0.95] * (len(hdr) - 3) + [1.3, 1.65], font=6.4, cell_margin=0.08, keep_together=True)
        _gap(d)

    D.h(d, 1, "Appendix A2   Capacity and the overflow routes", page_break=True)
    st = F.settlement_table()
    D.tab_caption(d, "Capacity of the empty land by settlement")
    D.table(d, ["Settlement", "Empty plots", "of which home-shaped and counted", "Home share", "Dwellings per plot", "Persons per dwelling", "Capacity, people"],
            [[r["name"], fmt(r["empty_plots"]), fmt(r["cap_plots"]), f"{r['home_share']:.2f}", f"{r['ratio']:.2f}", f"{r['or_used']:.2f}", fmt(r["cap_people"])] for r in st]
            + [["Total", fmt(sum(r["empty_plots"] for r in st)), fmt(sum(r["cap_plots"] for r in st)), "", "", "", fmt(t["capacity"])]],
            widths=[3.4, 2.0, 3.0, 1.9, 2.2, 2.2, 2.3], font=8.2, align_right={1, 2, 3, 4, 5, 6}, keep_together=False)
    _gap(d)
    D.tab_caption(d, "The overflow routes carrying fifty people or more at saturation")
    D.table(d, ["From", "To", "People at saturation", "Donor full", "Receiver starts", "Receiver full"],
            [[r["donor_name"], r["receiver_name"], fmt(r["people"]), str(r["donor_full"] or ""), str(r["starts"] or ""), str(r["receiver_full"] or "")] for r in F.routes()],
            widths=[3.2, 3.2, 2.6, 2.3, 2.6, 2.6], font=8, align_right={2, 3, 4, 5}, keep_together=False)

    D.h(d, 1, "Appendix A3   The 126 meters with no plot within 15 metres, close up", page_break=True)
    D.p(d, f"Every one of the {fm['count']} meters, in {68} panels, each about 700 to 1,100 "
           f"metres across. A red dot is a dwelling meter, a blue dot any other meter; the "
           f"plots are outlined in yellow. The panel numbers are those of the map in Section 3.3.")
    D.tab_caption(d, "The meters by settlement")
    rows = sorted(fm["by_settle"].items(), key=lambda kv: -kv[1])
    half = (len(rows) + 1) // 2
    D.table(d, ["Settlement", "Meters", "Settlement", "Meters"],
            [[F.NAME.get(rows[i][0], rows[i][0].title()), str(rows[i][1]),
              F.NAME.get(rows[i + half][0], rows[i + half][0].title()) if i + half < len(rows) else "",
              str(rows[i + half][1]) if i + half < len(rows) else ""] for i in range(half)],
            widths=[4.6, 2.0, 4.6, 2.0], font=9, align_right={1, 3})
    pages = sorted(f for f in os.listdir(IMG) if f.startswith("B06_panels_p") and f.endswith(".png"))
    per = 9
    D.wide_figures(d, [(os.path.join(IMG, f), f"Panels {i * per + 1} to {min((i + 1) * per, 68)} of 68.") for i, f in enumerate(pages)], size="A4")

    D.page_section(d, "A4", "landscape", margin=1.5)
    D.h(d, 1, "Appendix A4   The tractive-force curve in full")
    D.p(d, "The same curve as in Section 7.2, with every pipe size's minimum gradient marked "
           "where it meets the curve, and three readings on the steep part.")
    D.picture(d, os.path.join(IMG, "K01_mara_full.png"), 21.0)
    D.fig_caption(d, "The minimum gradient by tractive force at one pascal, the Table 11 minima of every size, and the proposed 1.5 litres a second floor.")
    D.page_section(d, "A4", "portrait")

    D.h(d, 1, "Appendix A5   The fields of the plot layer")
    D.p(d, "The plot layer delivered with the Concept Design Report carries, for each of the "
           "77,265 plots, the fields below. It is the load table of the design.")
    D.tab_caption(d, "Fields of the plot layer that the design reads")
    D.table(d, ["Field", "Content"], [
        ["SETTLE", "the settlement the plot belongs to"],
        ["DERIVED", "use of the plot (Section 4)"],
        ["G_DOM", "dwellings on the plot, one per domestic meter"],
        ["OR_S", "persons per dwelling adopted for the settlement"],
        ["POP, POP_2030, POP_2055, POP_ULT", "people on the plot in 2024, 2030, 2055 and the saturation year"],
        ["QADF, Q_2030, Q_2055, Q_ULT", "average sewage flow, m³/d, in the same years; a future plot at 171.3 l/d per person"],
        ["S_DOM, S_NDOM, S_GOV, S_SPEC", "the 2024 sewage by stream: households, shops and offices, government, estates"],
        ["FUT_CAP", "1 if an empty plot counts as a future home"],
        ["SAT_YEAR", "the year the plot's settlement is full"],
    ], widths=[5.2, 11.2], font=9)
