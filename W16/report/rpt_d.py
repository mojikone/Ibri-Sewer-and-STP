"""Chapter 4 - demand and flows.   Revision 3: the content of the Design Basis Report in the
concept report's sections, from the same facts and the same decisions list."""
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


def _map(d, name, caption, folder=None):
    """A map goes on its own A4 landscape page."""
    return D.wide_figure(d, os.path.join(folder or IMG, name + ".png"), caption, size="A4")


def _chart(d, name, caption, width=14.5, folder=None):
    D.chart(d, name, width, img=folder or IMG)
    return D.fig_caption(d, caption)


def _gap(d):
    D.p(d, "", space_after=2)


def part_d(d):
    D.chapter(d, "4.   Demand and flows")
    D.p(d, "This chapter establishes the population, the use of the land and its growth "
           "to saturation, the wastewater flow that every element of the system is "
           "designed for, the non-domestic discharges and the treated effluent "
           "available.")
    t = F.totals(); ps = F.plot_summary(); mc = F.meter_counts(); st = F.settlement_table()
    ib = [r for r in st if r["key"] == "IBRI"][0]
    ult = t["ultimate"]; cls = ps["classes"]

    # --------------------------------------------------------------- 14
    D.h(d, 2, "4.1.   Population and land use")

    D.h(d, 3, "4.1.1.   Approach")
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

    D.h(d, 3, "4.1.2.   The settlements and their boundaries")
    D.p(d, "Every rule in this chapter is applied settlement by settlement: the "
           "persons per property, the share of empty land that becomes housing, "
           "the growth rate and the year the land is full are all set for each "
           "settlement. So every plot must belong to exactly one settlement.")
    p = D.p(d, "The Inception Report supplied twenty-six polygons for the "
               "twenty-five settlements, Al Aynayn being drawn as two. The "
               "polygons are drawn around the built cores. They do not touch, "
               "so the land between them belongs to nobody, and four of them, "
               "at Tanam, Satwah, Al Makhtibyah and Bat, miss part of the plots "
               "that carry the settlement's name. The map on the next page "
               "shows them in red.")
    N.add(p, "Final_Boundary_IBRI.kmz, issued with the Inception Report R0.")
    p = D.p(d, f"The boundaries were therefore redrawn. Each of the "
               f"{fmt(ps['total'])} plots was given the settlement whose "
               f"polygon contains it, or, where none does, the nearest one. The "
               f"land was then divided so that every point belongs to the "
               f"settlement of the nearest plot, and the shared edges were "
               f"smoothed. The result, in blue on the map, covers the whole "
               f"study area with twenty-five settlements and no gaps. Nothing "
               f"else changed: the names, the population series and the plots "
               f"are as received.")
    N.add(p, "A Voronoi division of the plot centroids by settlement, merged, "
             "clipped to the study area boundary and smoothed as a coverage so "
             "that neighbours share one line.")
    D.p(d, "The twenty-five settlements inside the study area carry 63.4 per "
           "cent of the wilayat's population in every year of the series. The "
           "other settlements of the wilayat lie outside the boundary and are "
           "not part of the design.")
    _map(d, "B01_boundaries", "The settlement boundaries as received (red, dashed) and as redrawn for the design (blue). "
                              "Every plot lies in one settlement and the boundaries meet without gaps.", IMG_B)
    ask(d, 1)            # after the map: ahead of it the box was stranded alone on a page

    D.h(d, 3, "4.1.3.   From the meters to the properties")
    p = D.p(d, f"Each domestic electricity meter is one property. Of the "
               f"{fmt(mc['total'])} meters, {fmt(mc['inside'])} fall inside a "
               f"plot. {fmt(mc['snapped'])} lie on a road or in a gap between "
               f"plots and were given the nearest plot within fifteen metres. "
               f"{fmt(mc['free'])} lie further than that from any plot and are "
               f"shown below. The plots hold {fmt(ps['properties'])} domestic "
               f"properties. Shop, office, government, farm and large-consumer "
               f"meters carry no people.")
    N.add(p, "The primary, subsidised primary and additional-account tariffs "
             "count as properties. The 499 large-consumer accounts were placed "
             "by public records; their use decides only where the shop and "
             "government water is placed, not how much there is.")

    D.sub(d, "Properties per home plot")
    D.p(d, "The number of properties on a built home plot is measured in each "
           "settlement over the plots that are homes and nothing else, "
           "excluding the few plots that carry fifteen or more domestic meters, "
           "which are blocks of flats and workers' housing and would distort "
           "the ratio. Plots that also carry shops, farms or offices are "
           "counted for their people but not for the ratio.")
    D.tab_caption(d, "Properties per home plot, the principal settlements")
    D.table(d, ["Settlement", "Domestic properties", "Home plots measured", "Properties per home plot"],
            [[r["name"], fmt(r["properties"]), fmt(r["home_plots"]), f"{r['ratio']:.2f}"] for r in st[:8]],
            widths=[4.6, 4.0, 4.0, 4.0], font=9)
    _gap(d)
    p = D.p(d, f"Ibri carries {ib['ratio']:.2f} properties per home plot; the "
               f"principal settlements lie between 1.1 and 1.4. Four small "
               f"settlements with institutional housing on a handful of plots "
               f"return two or more; the thirteen settlements under a thousand "
               f"people take one property per plot, as Section 4.1.4 sets out. "
               f"The full table is given in Appendix A.3.")
    N.add(p, f"{fmt(ps['pure_home_plots'])} home plots were measured across "
             f"the twenty-five settlements.")

    D.sub(d, "The 126 meters with no plot within 15 metres")
    fm = B.free_meters()
    p = D.p(d, f"{fm['count']} meters lie more than fifteen metres from any "
               f"plot. {fm['domestic']} of them are domestic meters, about "
               f"{fmt(round(fm['people'], -1))} people at their settlement's "
               f"occupancy; the rest are government, shop and farm meters. Some "
               f"stand on buildings the cadastre has not yet captured. Others "
               f"stand on nothing: a road reserve, open ground, a pumping "
               f"station. All of them are left out of the plot loads. The map "
               f"on the next page shows where they are, and the figure after "
               f"it shows nine of them close up, with the plots around them.")
    N.add(p, "By tariff: " + ", ".join(f"{k} {v}" for k, v in sorted(fm["by_tariff"].items(), key=lambda kv: -kv[1])) + ".")
    rows = sorted(fm["by_settle"].items(), key=lambda kv: -kv[1]); half = (len(rows) + 1) // 2
    D.tab_caption(d, "The 126 meters by settlement")
    D.table(d, ["Settlement", "Meters", "Settlement", "Meters"],
            [[F.NAME.get(rows[i][0], rows[i][0].title()), str(rows[i][1]),
              F.NAME.get(rows[i + half][0], rows[i + half][0].title()) if i + half < len(rows) else "",
              str(rows[i + half][1]) if i + half < len(rows) else ""] for i in range(half)],
            widths=[4.6, 2.0, 4.6, 2.0], font=9)
    _chart(d, "R07_free_meters", "The 126 meters by tariff and by settlement. Thirty are domestic meters.", 15.0)
    adopt(d, 1)
    D.wide_figures(d, [(os.path.join(IMG_B, "B05_free_meters.png"), "The 126 meters more than fifteen metres from any plot. Red: a domestic meter; blue: any other meter."),
                       (os.path.join(IMG_B, "B06_examples.png"), "Nine of the 126 meters close up: on a road, in open ground, at a pumping station, on a building the cadastre does not carry. The plots are outlined in yellow.")], size="A4")

    D.h(d, 3, "4.1.4.   Occupancy rate")
    D.p(d, "The occupancy rate of each settlement is its population in 2024, "
           "the year of the electricity data, divided by the domestic "
           "properties counted in it.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("OR"), M.EQ, M.frac(UP("Settlement population in 2024"), UP("Domestic properties"))), number=eq)
    D.symbols(d, [["OR", "occupancy rate", "persons per property"]])
    small = [r["name"] for r in st if r["small"]]; cap = max(r["or_used"] for r in st)
    p = D.p(d, f"Three rules bound the result. A floor of {F.OR_FLOOR:.1f}: "
               f"some settlements would otherwise return between one and four "
               f"persons per property, because their meters include the housing "
               f"of the police, the college and similar institutions, whose "
               f"occupants the census does not count as residents. Those "
               f"properties discharge to the sewer whatever the census says, so "
               f"the floor keeps them in. A cap of {cap:.2f}, the highest rate "
               f"among the settlements of two thousand people or more. And a "
               f"settlement of fewer than a thousand people takes "
               f"{F.OR_FLOOR:.1f} outright, one property per home plot and a "
               f"home share of 0.9 (Section 4.1.6), because it has too few "
               f"meters to measure on. That rule applies to {len(small)} "
               f"settlements.")
    N.add(p, f"{F.OR_FLOOR:.1f} is the rate measured at At Tayyib, 3,300 people, "
             f"the smallest settlement with a sample worth measuring. The cap "
             f"is Bat's. The thirteen small settlements: {', '.join(small)}.")
    p = D.p(d, f"Ibri returns {ib['or_used']:.2f} persons per property. Over "
               f"the whole study area the census gives {F.census_rate():.2f}. "
               f"The guideline derives occupancy from population and housing "
               f"units published by the statistics centre; housing units are "
               f"not published at settlement level, and the counted properties "
               f"are used in their place.")
    N.add(p, "PAM-GUD-201, Section 7.2, page 59. 116,452 divided by 22,559 "
             "properties gives the area-wide 5.16. Revision 1 of this report "
             "used a single rate of 5.32 for all settlements; the rate per "
             "settlement replaces it.")
    D.tab_caption(d, "Occupancy rate by settlement, 2024")
    D.table(d, ["Settlement", "Domestic properties", "Population 2024", "Rate calculated", "Rate adopted", "People in the design"],
            [[r["name"], fmt(r["properties"]), fmt(r["workbook_2024"]), f"{r['or_raw']:.2f}", f"{r['or_used']:.2f}", fmt(r["people_today"])] for r in st]
            + [["Total", fmt(sum(r["properties"] for r in st)), fmt(sum(r["workbook_2024"] for r in st)), "", "", fmt(t["pop_today"])]],
            widths=[3.8, 2.4, 2.8, 2.5, 2.4, 2.9], font=8.5, keep_together=False)
    _gap(d)
    D.p(d, f"With the floor and the cap the study area holds "
           f"{fmt(t['pop_today'])} people, against 116,452 in the official "
           f"series for the same settlements. The difference is the "
           f"institutional housing.")
    _chart(d, "C02_occupancy", "Occupancy rate by settlement: the value calculated from the census and the meters, and the value adopted after the floor and the cap.", 15.0)
    ask(d, 2)
    _chart(d, "C04_population", f"People in each settlement in 2024, from the domestic meters at the settlement's occupancy rate. "
                                f"Ibri holds {ib['people_today'] / t['pop_today'] * 100:.0f} per cent of the total.", 14.5)

    D.h(d, 3, "4.1.5.   Land use")
    p = D.p(d, f"The cadastral layer received in September 2026 holds "
               f"{fmt(ps['total'])} plots. Its own land-use field cannot be used "
               f"as it stands: it has no government class, it records whole "
               f"districts under codes that mean unclassified, and on the plots "
               f"that carry meters it disagrees with the meters on "
               f"{fmt(F.cadastre_disagreement() * 100)} per cent of them. The "
               f"use of every plot has therefore been determined from what is "
               f"on it, in a fixed order.")
    N.add(p, "MoH_Plots, 77,265 plots, Ministry of Housing and Urban Planning, received September 2026.")
    D.picture(d, os.path.join(IMG, "D6_landuse.png"), 14.5)
    D.fig_caption(d, "How the use of each plot is determined from the electricity meters, the satellite image and the plot itself.")
    D.numbered(d, "a plot inside one of the two industrial estates is industrial;", restart=True)
    D.numbered(d, "the 177 plots of the old quarter of Ibri, recorded as tourism in the cadastre, are heritage and carry no load;")
    D.numbered(d, "a plot with a farm meter is agricultural;")
    D.numbered(d, "a plot the satellite image shows as planted is agricultural, unless two thirds of its meters are shops or most are government;")
    D.numbered(d, "a plot whose industrial meters equal or outnumber its domestic meters is industrial;")
    D.numbered(d, "otherwise the meters decide by proportion: more than two thirds domestic makes it residential, two thirds or more "
                  "government makes it government, two thirds or more shops makes it commercial, and a mix is "
                  "residential-commercial, or government where the government meters are the more;")
    D.numbered(d, "a plot without a meter is empty.")
    p = D.p(d, "The satellite image is a cloud-free Sentinel-2 image of 9 "
               "September 2026. It is used for one purpose: to tell a planted "
               "plot, a date-palm plantation, from a bare one, because a farm "
               "meter alone misses the plantations that pump from elsewhere.")
    N.add(p, f"Sentinel-2 Level 2A, tile 40QDL, red and near-infrared bands at "
             f"10 m. {fmt(F.farm_bare_share() * 100)} per cent of the plots with "
             f"a farm meter show no planting: pump sites without a crop. The "
             f"treatment plant's own plot carries farm meters for its pumps and "
             f"is classed as a government site.")
    D.tab_caption(d, "Use of the plots")
    D.table(d, ["Use", "Plots", "How it was decided"], [
        ["Residential", fmt(cls.get("Residential", 0)), "more than two thirds of the meters are domestic"],
        ["Residential-Commercial", fmt(cls.get("Residential-Commercial", 0)), "a mix, with at least as many shop as government meters"],
        ["Commercial", fmt(cls.get("Commercial", 0)), "two thirds or more of the meters are shops"],
        ["Government", fmt(cls.get("Government", 0)), "two thirds or more government; or a mix with more government than shop meters; the treatment plant"],
        ["Agricultural", fmt(cls.get("Agricultural", 0)), f"a farm meter ({fmt(ps['farms_by'].get('AGR', 0))}) or planted on the satellite image ({fmt(ps['farms_by'].get('GRN', 0))})"],
        ["Industrial", fmt(cls.get("Industrial", 0)), "inside an industrial estate, or industrial meters that match the domestic meters"],
        ["Heritage", fmt(ps["heritage"]), "the old quarter of Ibri; no meter, no load"],
        ["Empty", fmt(ps["empty"]), "no meter"],
    ], widths=[4.0, 2.0, 10.5], font=9)
    _gap(d)
    D.p(d, "The use decides where the shop and government water is placed and "
           "which empty plots can become homes. It does not change the total: "
           "that comes from the people and the rates of Section 4.2.")
    _chart(d, "C07_landuse", f"Use of the built, metered plots. Residential plots are "
                             f"{fmt(cls.get('Residential', 0) / ps['metered'] * 100)} per cent of them; agricultural plots, "
                             f"{fmt(cls.get('Agricultural', 0) / ps['metered'] * 100)} per cent, are found by the meter or by the satellite image.", 14.0)
    ask(d, 3)
    _map(d, "B02_landuse", "The use of each plot. Coloured plots are built and metered; empty plots are shown by their outline only.", IMG_B)

    D.h(d, 3, "4.1.6.   Capacity of the empty land")
    _p0 = F.plots(); _homes = _p0[(_p0.DERIVED == "Residential") & (_p0.Buiding_St == "EXisting")]
    p = D.p(d, f"Of the {fmt(ps['total'])} plots, {fmt(ps['empty'])} carry no "
               f"meter. Not all of them will become homes. A future home plot "
               f"must look like the built ones: between 200 and 1,000 square "
               f"metres, compact, not a strip. Very small plots below 200 "
               f"square metres, odd shapes and everything above 1,000 square "
               f"metres are left out, as are plantations, industrial plots and "
               f"the heritage quarter. {fmt(ps['capacity_plots'])} empty plots "
               f"pass that test.")
    N.add(p, "Compactness is the plot's area against that of its smallest "
             "enclosing rectangle, not less than 0.6; the rectangle's sides "
             "may not differ by more than three to one. Built home plots have "
             f"a median area of {fmt(_homes.AREA_M2.median())} square metres and a median compactness of "
             f"{_homes.COMPACT.median():.2f}. Shapes above 2,000 square metres are whole future "
             "districts drawn as one plot and take nothing until they are "
             "subdivided.")
    hs = F.home_share_range()
    D.p(d, f"A district also needs mosques, shops and offices, so not every "
           f"home-shaped plot becomes a home. The share that does is measured "
           f"in each settlement over its built, metered, home-shaped plots: "
           f"residential plots divided by all. Ibri returns "
           f"{ib['home_share']:.2f}; among the settlements of a thousand people "
           f"or more the measured share runs from {hs[0]:.2f} in {hs[1]}, with "
           f"its workshops, to {hs[2]:.2f} in {hs[3]}.")
    D.p(d, "The capacity of a settlement is then its home-shaped empty plots, "
           "multiplied by its home share, by its properties per home plot and "
           "by its occupancy rate.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("Capacity"), M.EQ, UP("Empty home‑shaped plots"), M.TIMES, UP("Home share"), M.TIMES,
                       UP("Properties per plot"), M.TIMES, UP("OR")), number=eq)
    D.symbols(d, [["Capacity", "people the empty land of the settlement can hold", "persons"],
                  ["Home share", "share of the home-shaped plots that become homes", ""],
                  ["OR", "occupancy rate of the settlement", "persons per property"]])
    p = D.p(d, f"The empty land of the study area holds {fmt(t['capacity'])} "
               f"people on this basis, against {fmt(t['pop_today'])} living in "
               f"it in 2024.")
    N.add(p, "The thirteen settlements under a thousand people take a home "
             "share of 0.9 and one property per plot, as Section 4.1.4 sets out. "
             "Capacity by settlement: Appendix A.3.")

    gr = F.growth_rates(); no = B.no_overflow(); sy = {r["key"]: r["sat_year"] for r in st}
    D.h(d, 3, "4.1.7.   How fast each settlement grows")
    D.picture(d, os.path.join(IMG, "D7_saturation.png"), 14.5)
    D.fig_caption(d, "From the empty plot to the year each settlement is full.")
    p = D.p(d, f"The growth rate comes from the population series of the "
               f"Inception Report, and nothing else is taken from it. To 2040 "
               f"the series is the official forecast for the wilayat, from the "
               f"statistics centre and Nama Water Services; from 2041 to 2050 "
               f"it is the extension of that forecast in the Inception Report. "
               f"Both are the client's own figures. From 2051 the series rises "
               f"from {fmt(gr['r2051'], 1)} per cent a year to 2.40 by "
               f"{gr['year_240']} and stays there to 2100, the horizon Nama "
               f"Water Services instructed; that part goes beyond the ten years "
               f"of extension the guideline allows and is put to approval. "
               f"Every settlement carries the same annual rate, applied to its "
               f"counted population. The rate averages "
               f"{fmt(gr['d2024_2030'], 1)} per cent a year to 2030, "
               f"{fmt(gr['d2030s'], 1)} in the 2030s, {fmt(gr['d2040s'], 1)} in "
               f"the 2040s, {fmt(gr['d2050s'], 1)} in the 2050s and 2.4 after "
               f"2060.")
    N.add(p, "Inception Report R0, Section 6, and the demand workbook, sheets "
             "Pop_Wilayat and Project Pop Settlements. Wilayat population "
             "183,564 in 2024; the twenty-five settlements are 63.4 per cent of "
             "it in every year. PAM-GUD-201 allows an extrapolation of ten "
             "years beyond the available forecast.")
    D.p(d, "The series' total for 2100 is not a target. The land fills long before then.")
    _chart(d, "C12_growth_rate", "The annual growth rate of the series: the forecast to 2040, the extension to 2050, and the rise to a constant 2.40 per cent.", 14.0)
    ask(d, 6)

    D.h(d, 3, "4.1.8.   When a settlement is full: the overflow")
    D.p(d, "Each settlement grows at the rate of the series until its empty "
           "plots are built, its growth filling them together and in "
           "proportion. Then its further growth has to go somewhere. Two "
           "readings are possible, and the choice between them is the largest "
           "single decision in this report.")
    D.bullet(d, "when a settlement is full, its further growth moves to a "
                "neighbour with room. Ibri's goes in parallel to Al Araqi, Al "
                "Qurayn and Shalashil, in the proportions seventy, twenty and "
                "ten per cent, then to Ad Dariz, then to the nearest settlement "
                "with room. At Tayyib's goes first to Miayrid. Every other "
                "settlement overflows to its nearest neighbour with room.",
             lead="With the overflow: ")
    D.bullet(d, "each settlement grows on its own rate and stops when it is "
                "full. The growth it cannot house is lost to the study area.",
             lead="Without: ")
    p = D.p(d, f"The difference is large. With the overflow every settlement "
               f"fills by {ult} and the study area holds {fmt(t['pop_ult'])} "
               f"people. Without it, {len(no['never'])} settlements never fill "
               f"before 2100, the study area holds "
               f"{fmt(no['totals'][ult]['pop_own'])} people in {ult}, and "
               f"{fmt(t['pop_ult'] - no['totals'][ult]['pop_own'])} people of "
               f"the series have nowhere to go. A sewer in those settlements "
               f"sized on their own growth would be sized for land that never "
               f"fills.")
    N.add(p, "The settlements that never fill on their own growth: " + ", ".join(no["never"]) + ". "
             "The overflow routes reflect local knowledge of where Ibri's growth is taking place.")
    _chart(d, "K03_overflow_totals", "People in the study area by year, with the overflow and without it.", 14.5, IMG_B)
    _chart(d, "K04_overflow_settlements", "People at saturation in the ten settlements the choice affects most, with the overflow and without.", 14.5, IMG_B)
    D.tab_caption(d, f"Every settlement with and without the overflow: people in {ult} and the year it is full")
    rows = [[r["name"], fmt(r["capacity"]), fmt(r[ult]["pop_with"]), str(r["full_with"] or ""),
             fmt(r[ult]["pop_own"]), str(r["full_own"]) if r["full_own"] else "not before 2100"] for r in no["rows"]]
    tot = no["totals"][ult]
    rows.append(["Total", fmt(t["capacity"]), fmt(tot["pop_with"]), str(ult), fmt(tot["pop_own"]), ""])
    D.table(d, ["Settlement", "Capacity, people", f"With the overflow: people {ult}", "full in", f"Own growth only: people {ult}", "full in"],
            rows, widths=[3.6, 2.4, 2.9, 1.7, 2.9, 2.5], font=8.5, keep_together=False)
    _gap(d)
    rcv = F.ibri_receivers(0); ar = next((r for r in rcv if r["receiver"] == "AL ARAQI"), None); top = rcv[0]
    D.p(d, f"The rule sets the order; the land sets the result. Al Araqi fills "
           f"in {sy['AL ARAQI']}, a year after Ibri, so it takes only "
           f"{fmt(ar['people'] if ar else 0)} of Ibri's people, and most of "
           f"Ibri's overflow passes on: the largest route is to "
           f"{top['receiver_name']}, {fmt(top['people'])} people, and "
           f"{len(rcv)} settlements take some of Ibri's growth in all. The "
           f"routes carrying more than a thousand people are set out below; the "
           f"full list is in Appendix A.4.")
    D.tab_caption(d, "The main overflow routes")
    rts = [r for r in F.routes() if r["people"] >= 1000]
    D.table(d, ["From", "To", "People at saturation", "Donor full", "Receiver starts", "Receiver full"],
            [[r["donor_name"], r["receiver_name"], fmt(r["people"]), str(r["donor_full"] or ""),
              str(r["starts"] or ""), str(r["receiver_full"] or "")] for r in rts],
            widths=[3.2, 3.2, 2.6, 2.3, 2.6, 2.6], font=8.2)
    _gap(d)
    ask(d, 4)
    _map(d, "B04_overflow", "Where the growth goes once a settlement is full. Arrows show the routes carrying five hundred people "
                            "or more at saturation; the shading shows how much of each settlement's capacity is taken by its "
                            "neighbours' overflow.", IMG_B)
    _chart(d, "C10_fill_years", "The year each settlement's empty plots are full. Ibri and the settlements that take a thousand or more of its people are marked.", 14.5)

    D.h(d, 3, "4.1.9.   The design horizon: 2055, or the year the land is full")
    p = D.p(d, f"The Terms of Reference name a horizon of completion plus "
               f"twenty-five years. With the opening year taken as 2030, that "
               f"is 2055: {fmt(t['pop'][2055])} people and "
               f"{fmt(t['q'][2055])} cubic metres a day. The Terms of Reference "
               f"also ask for the saturation of the area. With the overflow, "
               f"Ibri fills in {sy['IBRI']}, Al Araqi in {sy['AL ARAQI']}, Ad "
               f"Dariz in {sy['AD DARIZ']}, and the last settlement in {ult}: "
               f"{fmt(t['pop_ult'])} people and {fmt(t['q_ult'])} cubic metres "
               f"a day, {fmt((t['q_ult'] / t['q'][2055] - 1) * 100)} per cent "
               f"more than in 2055.")
    N.add(p, "Terms of Reference, page 51 of the tender document. Average "
             "flows before infiltration and before the STP margin.")
    D.p(d, "The two horizons ask different things of the design. A network "
           "sized on 2055 is cheaper to build and reaches its capacity while "
           "the plots around it are still being built; the pipes under those "
           "streets would then need to be replaced or relieved. A network "
           "sized on the year the land is full is laid once, and its sewers run "
           "at low flow for longer, which the self-cleansing check of Section "
           "4.2.8 is there to catch. The STP is staged either way, on the "
           "series. The horizon is for Nama Water Services to decide.")
    D.tab_caption(d, "The study area in the design years")
    D.table(d, ["Year", "People", "Average sewage flow, m³/d", "What it is"], [
        ["2024", fmt(t["pop_today"]), fmt(t["q_today"]), "today, from the meters"],
        ["2030", fmt(t["pop"][2030]), fmt(t["q"][2030]), "opening year"],
        ["2055", fmt(t["pop"][2055]), fmt(t["q"][2055]), "opening year plus 25 years"],
        [f"{ult}", fmt(t["pop_ult"]), fmt(t["q_ult"]), "saturation: the land is full"],
    ], widths=[2.0, 3.0, 4.3, 7.2], font=9.5)
    _gap(d)
    _chart(d, "R01_horizon", "The two horizons side by side: people, average sewage flow, and the STP's average and peak-hour flow with the margin.", 15.0)
    ask(d, 5)
    _chart(d, "C08_growth", "People by year to saturation, the six largest settlements shown separately. The flat top of each band is the year that settlement fills.", 15.0)
    p = D.p(d, "The people of every settlement at five-year steps, to the year "
               "it is full. A cell is blank once the settlement is full.")
    N.add(p, "Totals are rounded from the unrounded values and may differ by "
             "one from the sum of the rows. A settlement's population after "
             "its saturation year is its capacity plus what it held in 2024; "
             "its growth beyond that is housed elsewhere or not at all.")
    cols, rows = F.five_year_rows("pop")
    hdr = ["Settlement"] + [str(c) for c in cols[1:-1]] + ["Full in", "At saturation"]
    D.tab_caption(d, "People by settlement at five-year intervals")
    D.table(d, hdr, rows, widths=[2.3] + [0.95] * (len(hdr) - 3) + [1.3, 1.65], font=6.4, cell_margin=0.08, keep_together=True)

    D.h(d, 3, "4.1.10.   Where the growth is placed")
    D.p(d, "For the network every empty plot matters, not only the ones "
           "counted as future homes, because the sewer that serves a street "
           "serves every plot on it. The people a settlement houses in a given "
           "year are therefore spread over all its empty plots up to 2,000 "
           "square metres, in proportion to plot area capped at 1,000 square "
           "metres. A very small plot takes its small share and a large plot "
           "takes no more than a full-sized home plot. The sum over the plots "
           "equals the settlement's housed population by construction, so the "
           "network total and the STP total are the same figure.")

    # --------------------------------------------------------------- 15
    D.h(d, 2, "4.2.   Wastewater generation and design flows", page_break=True)
    D.picture(d, os.path.join(IMG, "D3_flow.png"), 15.5)
    D.fig_caption(d, "Derivation of the design flow, from the plot to the pipe and the STP.")

    D.h(d, 3, "4.2.1.   Water demand")
    D.p(d, "Wastewater generation is derived from water demand. Four "
           "components are carried: domestic, non-domestic, governmental and "
           "special consumption. A household supplied by tanker is metered "
           "for electricity like any other and carries the domestic rate; the "
           "tanker volumes themselves are a data request and no separate "
           "term is carried (Section 3.1.1).")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("dom")), M.EQ, UP("Population"), M.TIMES, UP("LPCD")), number=eq)
    D.symbols(d, [["Q dom", "domestic water demand", "l/d"],
                  ["LPCD", "unit consumption, 164 for Adh Dhahirah", "l per person per day"]])
    D.p(d, "Non-domestic and governmental demand are established as proportions of domestic demand.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("ND")), M.EQ, R("0.22"), M.sub(R("Q"), UP("dom"))), number=eq)
    D.symbols(d, [["Q ND", "non-domestic water demand of the settlement: shops and offices", "l/d"]])
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("gov")), M.EQ, R("0.14"), M.sub(R("Q"), UP("dom"))), number=eq)
    D.symbols(d, [["Q gov", "governmental water demand of the settlement", "l/d"]])
    p = D.p(d, "The proportions are the values published for the Governorate "
               "of Adh Dhahirah. The guideline calls them distributed. They "
               "come from the governorate's water balance of 2021 to 2023, all "
               "the non-domestic water divided by all the domestic water, so "
               "they stand for the everyday shops, mosques, schools and "
               "offices that come with any population, and they are added "
               "whether or not a particular village has a shop today. They do "
               "not cover named projects such as economic zones, which are "
               "added separately. Per person they are 36 and 23 litres a day, "
               "and the three are applied as separate streams, never combined "
               "into one rate. Each settlement's non-domestic and governmental "
               "water is placed on its shop and government meters in "
               "proportion to their number.")
    N.add(p, "PAM-GUD-201, Table 11, page 60, and page 59: the ratios \"refer "
             "to spatially distributed non-domestic consumption that are to be "
             "added to the domestic consumption\" and \"do not apply to ... "
             "specific identified non-domestic projects such as economic "
             "zones\".")

    D.h(d, 3, "4.2.2.   Special consumption: the industrial estates")
    p = D.p(d, "Two industrial estates lie inside the study area, at Al Tayyeb "
               "in the north-east of the town and at Tanam beside the "
               "treatment plant. Their meters are recorded on the commercial "
               "tariff. The guideline places such estates outside the "
               "population ratios, and they are treated as special "
               "consumption: a workforce of 4,500 at Al Tayyeb and 1,800 at "
               "Tanam, spread over their industrial plots in proportion to "
               "area, at the dry-industry rate of 93 litres per employee per "
               "day. Their meters take no share of the settlement's "
               "non-domestic or governmental water: an estate plot carries its "
               "workers, and the few properties on the estates carry the "
               "domestic rate like any other. The workforce is an assumption "
               "from the number of workshop meters and is to be replaced by "
               "the estates' own records. Section 4.3 describes the estates and "
               "the other identified projects.")
    N.add(p, "PAM-GUD-201, Section 7.3.1, page 59, and Table 12, page 61, "
             "dry industry. Al Tayyeb: 94 hectares, 202 industrial plots, "
             "1,035 meters. Tanam: 61 hectares, 105 plots, 409 meters. About "
             "five meters per plot and three to six workers per workshop give "
             "the assumed figures.")
    adopt(d, 3)

    D.h(d, 3, "4.2.3.   Return to the sewer")
    D.p(d, "Not all supplied water reaches the sewer. The proportion that does is applied by category.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("ww")), M.EQ, R("0.85"), M.sub(R("Q"), UP("dom")), M.PLUS,
                       R("0.54"), M.delim(M.seq(M.sub(R("Q"), UP("ND")), M.PLUS, M.sub(R("Q"), UP("gov")), M.PLUS, M.sub(R("Q"), UP("special"))))), number=eq)
    D.symbols(d, [["Q ww", "wastewater generated, before infiltration", "l/d"],
                  ["Q dom", "domestic demand; tanker supply is added when its records are received", "l/d"],
                  ["Q special", "water of the special consumption, the guideline's term; in the study area the two industrial estates", "l/d"]])
    p = D.p(d, "Water supplied by tanker returns to the sewer at the same "
               "proportion as piped supply. The domestic rate of 164 litres a "
               "day measures network water only, so tanker supply is not "
               "inside the domestic stream; it is added when the "
               "filling-station records are received (Section 3.1.1).")
    N.add(p, "PAM-GUD-201, Table 19, page 71, which gives a single discharge "
             "ratio for domestic and tanker supply.")
    p = D.p(d, "Farm meters supply irrigation pumps and are taken to return "
               "nothing, and the estates' dry-industry demand is taken to "
               "return 54 per cent, as non-domestic supply does. Both are rules "
               "of this design, not of the guideline.")
    _pl = F.plots(); _farm = _pl[_pl.G_AGR > 0]
    N.add(p, f"On {fmt(int((_farm.G_DOM > 0).sum()))} of the {fmt(len(_farm))} plots with a farm meter a household is metered separately from the pump.")
    adopt(d, 2)

    D.h(d, 3, "4.2.4.   The flow from each plot")
    D.p(d, "Applied plot by plot, the rules above give every plot an average "
           "daily sewage flow for 2024. An existing plot is built from its "
           "meters and the rates of its settlement:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("plot")), M.EQ,
                       R("0.85"), M.TIMES, R("164"), M.TIMES, R("OR"), M.TIMES, M.sub(R("N"), UP("dom")), M.PLUS,
                       R("0.54"), M.TIMES, M.delim(M.seq(M.sub(R("U"), UP("nd")), M.sub(R("N"), UP("nd")), M.PLUS,
                                                        M.sub(R("U"), UP("gov")), M.sub(R("N"), UP("gov")), M.PLUS,
                                                        R("93"), M.sub(R("N"), UP("w"))))), number=eq)
    D.symbols(d, [
        ["Q plot", "average sewage flow of the plot in 2024", "l/d"],
        ["OR", "occupancy rate adopted for the settlement (Section 4.1.4)", "persons per property"],
        ["N dom", "domestic meters on the plot, one property each", ""],
        ["U nd", "non-domestic water per shop meter in the settlement", "l/d per meter"],
        ["N nd", "non-domestic meters on the plot; none counted on an estate plot", ""],
        ["U gov", "governmental water per government meter in the settlement", "l/d per meter"],
        ["N gov", "government meters on the plot; none counted on an estate plot", ""],
        ["N w", "workers on an industrial-estate plot", ""]])
    D.p(d, "The unit rates are the settlement's non-domestic and governmental "
           "shares, divided equally among the meters that carry them:")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("U"), UP("nd")), M.EQ,
                       M.frac(M.seq(R("0.22"), M.TIMES, R("164"), M.TIMES, M.sub(R("P"), UP("s"))), M.sub(R("N"), UP("nd,s")))), number=eq)
    D.symbols(d, [["P s", "people of the settlement in 2024", ""],
                  ["N nd,s", "shop meters of the settlement outside the industrial estates", ""]])
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("U"), UP("gov")), M.EQ,
                       M.frac(M.seq(R("0.14"), M.TIMES, R("164"), M.TIMES, M.sub(R("P"), UP("s"))), M.sub(R("N"), UP("gov,s")))), number=eq)
    D.symbols(d, [["N gov,s", "government meters of the settlement outside the industrial estates", ""]])
    p = D.p(d, "The estates' meters take no share of the pool; an estate plot "
               "carries its workers at 93 litres a day, and the properties on "
               "it, if any, at the domestic rate. A settlement with no shop or "
               "government meter outside the estates keeps that share on its "
               "houses, in proportion to their people. A future plot carries "
               "the people it houses in the year at 171.3 litres a day each, "
               "all three streams together, since where its shops will stand "
               "is not known.")
    N.add(p, "164 × 0.85 + 36 × 0.54 + 23 × 0.54 = 171.3 litres per person per "
             "day; 36 and 23 are 22 and 14 per cent of 164.")
    p = D.p(d, "The shares and the unit rates of every settlement are set out "
               "below. The sum of the plots equals the settlement in every column.")
    N.add(p, "The Tanam estate's plots lie across Tanam, Ad Dibayshi and Al "
             "Makhtibyah in the settlement partition, so its workforce appears "
             "under all three. Where a settlement has no shop or government "
             "meter outside the estates, the table shows that share as placed "
             "on the houses. Two plots outside the estates carry a special "
             "meter each, one on the industrial tariff and one large consumer "
             "identified as industrial; they are loaded through their shop "
             "meters, their own consumption being unknown. Totals are rounded "
             "from the unrounded values and may differ by one from the sum of "
             "the rows.")
    D.tab_caption(d, "Water shares and unit rates by settlement, 2024")
    D.table(d, ["Settlement", "People", "Domestic m³/d", "Non-domestic share m³/d", "Governmental share m³/d",
                "Shop meters", "Government meters", "l/d per shop meter", "l/d per government meter", "Estates m³/d", "Sewage m³/d"],
            F.unit_rate_rows(), widths=[2.3, 1.1, 1.2, 1.5, 1.7, 1.0, 1.6, 1.4, 1.6, 1.0, 1.2], font=6.8, cell_margin=0.08, keep_together=False)
    _gap(d)
    D.p(d, f"In 2024 the study area generates {fmt(t['q_today'])} cubic metres "
           f"a day, of which {fmt(ps['s_dom'])} is domestic, {fmt(ps['s_nd'])} "
           f"non-domestic, {fmt(ps['s_gov'])} governmental and "
           f"{fmt(ps['s_spec'])} from the two estates.")
    _chart(d, "C11_streams", "Average sewage flow in 2024 by stream.", 13.0)

    D.h(d, 3, "4.2.5.   Infiltration")
    p = D.p(d, "For newly constructed networks an allowance of 720 litres per "
               "day per kilometre of sewer is included. It is a property of "
               "the pipe, not of the plot, and is added along each run. "
               "Infiltration from stormwater is not considered.")
    N.add(p, "PAM-GUD-201, Section 7.4.3, page 72.")

    D.h(d, 3, "4.2.6.   Peak flow")
    D.p(d, "Peak flow belongs to the pipe, not to the plot: it is applied to "
           "the sum of the plots upstream of each pipe. Above 100 properties "
           "the Merrimack formula applies; at 100 or fewer, the Peltier "
           "formula.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("peak")), M.EQ, R("2.65"), M.sup(M.sub(R("Q"), UP("avg")), R("0.879"))), number=eq)
    D.symbols(d, [["Merrimack", "above 100 properties; both flows in Ml/d", ""],
                  ["Q peak", "peak flow: the guideline's peak daily flow, Qpdf, equal to its peak hourly flow", "Ml/d"],
                  ["Q avg", "average flow of the plots upstream, the guideline's Qadf", "Ml/d"]])
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("peak")), M.EQ, M.delim(M.seq(R("1.5"), M.PLUS, M.frac(R("1"), M.sqrt(M.sub(R("Q"), UP("m")))))), M.sub(R("Q"), UP("avg"))), number=eq)
    D.symbols(d, [["Peltier", "at 100 properties or fewer", ""],
                  ["Q m", "the average flow of the plots upstream", "l/s"]])
    p = D.p(d, "The guideline recommends that the hourly peak factor not "
               "exceed 5.0. It is a recommendation, applied as such.")
    N.add(p, "PAM-GUD-201, Section 7.4.2, pages 71 and 72. PAM-GUD-203, Table "
             "29, page 65, defines the peak hourly flow and gives it the "
             "symbol QPDF.")
    _chart(d, "R03_peak_factor", "The peak factor against the average flow of the plots upstream. The Peltier formula applies to the head of a street, "
                                 "the Merrimack formula beyond 100 properties; for the whole study area the factor is about 1.6.", 14.5)
    adopt(d, 5)

    D.h(d, 3, "4.2.7.   Projection through the design period")
    p = D.p(d, f"Flows are established annually and reported at five-year "
               f"intervals to saturation, as the Terms of Reference require. "
               f"The study area generates {fmt(t['q_today'])} cubic metres a "
               f"day in 2024, {fmt(t['q'][2030])} in 2030, "
               f"{fmt(t['q'][2055])} in 2055 and {fmt(t['q_ult'])} at "
               f"saturation in {ult}.")
    N.add(p, "Average daily flows before infiltration and before the STP "
             "margin. The ultimate flow of about 49,700 cubic metres a day "
             "stated in the Inception Report was built on the connected "
             "population and a single occupancy rate; the figures here "
             "supersede it.")
    cols, rows = F.five_year_rows("q")
    hdr = ["Settlement"] + [str(c) for c in cols[1:-1]] + ["Full in", "At saturation"]
    D.tab_caption(d, "Average sewage flow by settlement at five-year intervals, m³/d")
    D.table(d, hdr, rows, widths=[2.3] + [0.95] * (len(hdr) - 3) + [1.3, 1.65], font=6.4, cell_margin=0.08, keep_together=True)
    _gap(d)
    _chart(d, "C09_flow", "Average sewage flow of the study area by year, from today's plots and from the empty plots as they fill. "
                          "The points mark the five-year reporting intervals.", 15.0)
    D.p(d, "The first map below gives the average flow of every plot at "
           "saturation. The second gives every settlement's average flow in "
           "2055 and at saturation, and the four steps to an STP flow, so that "
           "any grouping of settlements into one or more plants can be "
           "calculated by hand. The table carries the same values.")
    q_ult_by = {r["key"]: r[ult]["q_with"] for r in no["rows"]}
    one = [[r["name"], fmt(r["q_2055"]), fmt(q_ult_by[r["key"]])] for r in sorted(st, key=lambda r: -r["q_2055"])]
    one.append(["Total", fmt(t["q"][2055]), fmt(t["q_ult"])])
    half = (len(one) + 1) // 2
    rows = [one[i] + (one[i + half] if i + half < len(one) else ["", "", ""]) for i in range(half)]
    D.tab_caption(d, "Average sewage flow by settlement in 2055 and at saturation, m³/d")
    D.table(d, ["Settlement", "2055", f"{ult}", "Settlement", "2055", f"{ult}"], rows,
            widths=[3.6, 2.2, 2.4, 3.6, 2.2, 2.4], font=8.5, keep_together=True)
    _gap(d)
    _chart(d, "R02_settlement_flows", "Average sewage flow of every settlement in 2055 and at saturation. Ibri is full before 2055; the growth after it lands on its neighbours.", 14.5)
    D.wide_figures(d, [(os.path.join(IMG, "M09_saturation.png"), "Average sewage flow of every plot at saturation."),
                       (os.path.join(IMG_B, "B03_saturation.png"), "Average sewage flow of each settlement in 2055 and at saturation, and the four steps from the settlements in a catchment to the flow of their STP.")], size="A4")

    pf = B.plant_flows(); pl = B.process_loads(); yrs = B.years()
    D.h(d, 3, "4.2.8.   The flow each element is designed for")
    D.p(d, "Every plot carries an average sewage flow for 2024, 2030, 2055 and "
           "the saturation year. What each element of the system is designed "
           "for follows from those plot flows by fixed rules. The rules are "
           "the same wherever the element sits, so any one of them can be "
           "checked.")
    D.sub(d, "The plot")
    D.p(d, "The plot carries the average flow of its people and meters, and "
           "nothing else: no peak, no infiltration, no tankers. Those belong "
           "to the pipe and the STP.")
    D.sub(d, "The pipe")
    D.p(d, "A pipe is checked twice, on two different flows, because the two "
           "checks fail in opposite directions.")
    D.bullet(d, "the flow at saturation of every plot upstream, added up, "
                "peaked, plus infiltration along the pipe. Under-estimating it "
                "surcharges the pipe.", lead="Size and capacity: ")
    D.bullet(d, "the flow in 2030 of the plots upstream, with 61 per cent of "
                "the properties connected, peaked, and no infiltration. "
                "Over-estimating it declares a pipe self-cleansing while it "
                "silts.", lead="Self-cleansing: ")
    p = D.p(d, "The 61 per cent is the connection ratio of the Inception "
               "Report, reached by 2028. It is never applied to the saturation "
               "flow: that would give a pipe in a new district most of its "
               "final flow in a year when it carries almost nothing.")
    N.add(p, f"Whole area: {fmt(t['q'][2030])} × 0.61 = {fmt(pf[2030]['low'])} m³/d in 2030, against "
             f"{fmt(t['q_ult'] * 0.61)} if the ratio were applied to saturation.")
    adopt(d, 4)
    D.sub(d, "The pumping station and its rising main")
    D.p(d, "A station's duty flow is the peak flow of the catchment it drains "
           "plus the infiltration of its sewers, at saturation. Section 3.3.3 "
           "gives the depth rule that places it and the velocities of its "
           "rising main.")
    D.sub(d, "The trunk sewers and the treatment plant")
    p = D.p(d, f"The trunk sewers and the STP carry the sum of the settlements "
               f"upstream. If the whole study area drains to one STP, the flows "
               f"are as in the table, on the definitions of Section 3.4.1. The "
               f"network has not yet been laid over the whole area, so its "
               f"infiltration cannot be totalled; each 100 kilometres of new "
               f"sewer adds {fmt(100 * pf['infil_per_km'])} cubic metres a day "
               f"with the margin. Tanker deliveries are added when their "
               f"records arrive.")
    N.add(p, "PAM-GUD-201, Section 7.4.5, page 73, the margin.")
    D.tab_caption(d, "Flows at one STP for the whole area, before infiltration and tankers, m³/d")
    D.table(d, ["Flow"] + [str(y) for y in yrs], [
        ["People"] + [fmt(pf[y]["people"]) for y in yrs],
        ["Average flow from the plots"] + [fmt(pf[y]["qadf"]) for y in yrs],
        ["Peak flow before the margin"] + [fmt(pf[y]["qpdf"]) for y in yrs],
        ["Merrimack peak factor"] + [f"{pf[y]['pf']:.2f}" for y in yrs],
        ["**Average annual flow with the margin**"] + [f"**{fmt(pf[y]['aaf'])}**" for y in yrs],
        ["**Peak hourly flow with the margin**"] + [f"**{fmt(pf[y]['phf'])}**" for y in yrs],
        ["Infiltration with the margin, to add to both", f"{pf['infil_per_km']:.2f} m³/d per km of sewer", "", "", ""],
        ["Maximum day flow", "from the existing STP's records", "", "", ""],
    ], widths=[6.2, 2.6, 2.6, 2.6, 2.6], font=9)
    _gap(d)
    _chart(d, "K05_plant_flows", "Average and peak-hour flow at one STP for the whole area, by year, with the margin.", 14.5, IMG_B)
    p = D.p(d, f"At the guideline's minimum loads per person the STP receives "
               f"the loads below. That is {fmt(pl[ult]['bod_mgl'])} milligrams "
               f"of BOD per litre at saturation, at the low end of the range "
               f"the guideline gives for raw sewage, 350 to 400.")
    N.add(p, "PAM-GUD-203, Section 10.3.1, page 74, and Table 30, page 67.")
    D.tab_caption(d, "Loads at one STP for the whole area, from the per-person minima")
    D.table(d, ["", *[str(y) for y in yrs]], [
        ["People"] + [fmt(pl[y]["people"]) for y in yrs],
        ["BOD, kg/d"] + [fmt(pl[y]["bod_kgd"]) for y in yrs],
        ["Suspended solids, kg/d"] + [fmt(pl[y]["tss_kgd"]) for y in yrs],
        ["BOD as a concentration at the average flow, mg/l"] + [fmt(pl[y]["bod_mgl"]) for y in yrs],
        ["Suspended solids as a concentration, mg/l"] + [fmt(pl[y]["tss_mgl"]) for y in yrs],
        ["BOD at the peak factor of 1.2, kg/d"] + [fmt(pl[y]["bod_peak_kgd"]) for y in yrs],
    ], widths=[6.6, 2.5, 2.5, 2.5, 2.5], font=9)
    _gap(d)
    _chart(d, "R04_loads", "BOD and suspended solids reaching one STP for the whole area, by year, at the guideline's minimum loads per person.", 13.5)

    # --------------------------------------------------------------- 16
    D.h(d, 2, "4.3.   Non-domestic discharges: industrial estates and identified projects", page_break=True)
    p = D.p(d, "Sewage from industry and commerce, called trade effluent in the "
               "guidelines, affects the STP's load and how treatable the sewage "
               "is. Where its chemical to biochemical oxygen demand is above "
               "the domestic range, a separate treatment line is needed if the "
               "volume is significant. In Ibri the two industrial estates are "
               "workshops on the commercial tariff; no wet industry has been "
               "found. The estates are carried at the dry-industry rate "
               "(Section 4.2.2), and no separate line is foreseen at this stage.")
    N.add(p, "PAM-GUD-203, page 74: a COD to BOD ratio of 1.8 to 2.2 is typical of domestic sewage.")

    D.h(d, 3, "4.3.1.   The large-consumer accounts")
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
               f"{use.get('Agricultural', 0)} farm pumps and "
               f"{use.get('Telecom/Utility', 0)} telecommunications or "
               f"utility; {use.get('Unresolved', 0)} stand more than eighty "
               f"metres from any recorded feature and are carried as "
               f"commercial. Appendix A.2 gives the result by use.")
    N.add(p, "The largest groups are the Bawadi shopping centre with twenty "
             "accounts, the commercial street of Al Murtafa with nineteen, "
             "the police headquarters, the college campus and the hospital.")

    D.h(d, 3, "4.3.2.   Identified projects")
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
         "no meter in the dataset", "Recorded; no load. Its occupancy and "
         "drainage are to be confirmed (Section 1.5.5)"],
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
    _gap(d)
    p = D.p(d, "Sewage delivered by tanker is materially stronger than sewage "
               "arriving through the network. It is to be provided for "
               "separately in the STP load once the delivery records are "
               "received.")
    N.add(p, "PAM-GUD-203, Table 31, page 68, gives tankered sewage at 350 to "
             "1,050 mg/l BOD against 350 to 400 mg/l for network sewage "
             "(Section 3.4.1).")
    _map(d, "M08_special", "The identified projects and special consumers: the industrial areas, the army camp, "
                           "the treatment plant and the hotel sites recorded in OpenStreetMap, the two estates among them.")

    # --------------------------------------------------------------- 17
    ts = B.tse()
    D.h(d, 2, "4.4.   Treated effluent demand and customers", page_break=True)
    p = D.p(d, "Treated effluent is produced at 95 per cent of the STP inflow. "
               "A further ten per cent is lost within the treated effluent "
               "distribution network, so 85.5 per cent of the inflow reaches "
               "the customers.")
    N.add(p, "PAM-GUD-201, Section 7.4.6.1, page 73, and Section 7.4.6.3 (b), "
             "page 76: \"a system loss of 10 percent of all produced TSE shall "
             "be assumed\".")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("delivered")), M.EQ, R("0.90"), M.TIMES, R("0.95"), M.TIMES, M.sub(R("Q"), UP("inflow"))), number=eq)
    D.symbols(d, [["Q delivered", "treated effluent available to customers", "m³/d"],
                  ["Q inflow", "flow entering the STP, the design average", "m³/d"]])
    D.tab_caption(d, "Treated effluent available, one STP for the whole area, m³/d")
    D.table(d, ["", *[str(y) for y in yrs]], [
        ["STP inflow, design average"] + [fmt(ts[y]["inflow"]) for y in yrs],
        ["Produced, 95 per cent"] + [fmt(ts[y]["produced"]) for y in yrs],
        ["Delivered, less 10 per cent in the network"] + [fmt(ts[y]["delivered"]) for y in yrs],
    ], widths=[6.6, 2.5, 2.5, 2.5, 2.5], font=9)
    _gap(d)
    _chart(d, "R05_tse", "STP inflow, treated effluent produced and treated effluent delivered to customers, by year.", 13.5)
    adopt(d, 8)

    D.p(d, "Customers are classified as public or private. Public consumers "
           "comprise the landscaping of highways, secondary roads, "
           "interchanges and roundabouts, and public parks. Private consumers "
           "comprise community parks, golf courses, private gardens, and "
           "nurseries and farms.")
    D.tab_caption(d, "Treated effluent demand for concept planning")
    D.table(d, ["Planting", "Summer demand", "Planting", "Summer demand"], [
        ["Shrubs", "20 to 40 l per plant per day", "Ground cover", "10 l/m²/d"],
        ["Palm trees", "120 to 165 l per plant per day", "Seasonal flowers", "10 l/m²/d"],
        ["Other trees", "40 to 80 l per plant per day", "Grass", "12 l/m²/d"],
        ["Hedges", "10 l per metre per day", "Roads and junctions", "10 l/m²/d"],
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
           "will be presented with the treated effluent network options.")
