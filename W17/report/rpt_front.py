"""Contents, abbreviations and executive summary. The cover is the template's."""
import os

import doc as D
import notes as N
import facts_w14 as F
import facts_basis as B
from basis_items import APPROVALS, INFORMED, DATA_REQUESTS

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
fmt = F.fmt


def project_control(d):
    """The document control page, ahead of the contents: the project, the document, and who prepared, checked and
    approved it. The names, signatures and dates are filled in by hand on issue (engineer, 2026-10-03)."""
    D.title(d, "Document Control")
    D.table(d, ["Item", "Detail"], [
        ["Project", "Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri"],
        ["Client", "Nama Water Services"],
        ["Tender No.", "T/2719110/2025"],
        ["Contract No.", "OWWSCT/2719110/2025/C1499/2026"],
        ["Consultant", "Renardet S.A. & Partners"],
        ["Document", "Concept Design Report"],
        ["Date", "October 2026"],
    ], widths=[4.0, 12.5], font=10, first_col_bold=True)
    D.p(d, "")
    t = D.table(d, ["", "Name", "Signature", "Date"], [
        ["Prepared by", "", "", ""],
        ["Checked by", "", "", ""],
        ["Approved by", "", "", ""],
    ], widths=[3.4, 5.6, 4.6, 2.9], font=10, first_col_bold=True)
    for row in t.rows[1:]:
        row.height = D.Cm(1.4)
    D.pagebreak(d)


def contents(d):
    D.title(d, "Contents")
    D.toc(d, "1-3")
    D.pagebreak(d)
    D.title(d, "Figures")
    D.list_of(d, "Figure")
    D.title(d, "Tables", space_before=10)
    D.list_of(d, "Table")
    D.pagebreak(d)


def abbreviations(d):
    D.title(d, "Abbreviations and definitions")
    # every abbreviation the report uses, checked against the built document (engineer, 2026-10-03)
    D.table(d, ["Term", "Meaning"], [
        ["AAF", "Average annual flow: the design average of the treatment plant"],
        ["APSR", "Authority for Public Services Regulation"],
        ["BOD, BOD5", "Biochemical oxygen demand; BOD5 is measured over five days"],
        ["BS EN", "British Standard adopting a European Standard"],
        ["BWh", "Hot desert climate, in the Köppen-Geiger classification"],
        ["CAPEX / OPEX", "Capital expenditure / operating expenditure"],
        ["CESMM3", "Civil Engineering Standard Method of Measurement, third edition"],
        ["COD", "Chemical oxygen demand"],
        ["CRT", "Cost Reflective Tariff: the electricity tariff of the large consumers"],
        ["DN, OD", "Nominal diameter; outside diameter"],
        ["EIA", "Environmental impact assessment"],
        ["EPSG:32640", "The code of the coordinate system used: UTM zone 40 North on the WGS 84 datum"],
        ["GHS-POP", "Global Human Settlement population grid of the European Commission Joint Research Centre"],
        ["GIS", "Geographic information system"],
        ["GRP", "Glass-reinforced plastic"],
        ["H1 to H6", "The six flood hazard classes of the Australian classification (Section 1.2.7)"],
        ["HDPE", "High-density polyethylene"],
        ["ISO", "International Organization for Standardization"],
        ["kW, MWh", "Kilowatt; megawatt hour"],
        ["l/s, m³/d", "Litres a second; cubic metres a day"],
        ["LPCD", "Litres per capita per day"],
        ["MAFWR", "Ministry of Agriculture, Fisheries and Water Resources"],
        ["MD", "Ministerial Decision"],
        ["MOD", "Ministry of Defence: a tariff of the electricity dataset"],
        ["MoHUP", "Ministry of Housing and Urban Planning"],
        ["NAMA", "Nama Water Services, in the name of its design guidelines"],
        ["NASA POWER", "The climate data of the United States National Aeronautics and Space Administration, from the "
                       "MERRA-2 reanalysis, used for the climate and the wind (Section 1.2.5)"],
        ["NCSI", "National Centre for Statistics and Information"],
        ["NF EN", "French adoption of a European Standard"],
        ["NOC", "No objection certificate"],
        ["NPV", "Net present value"],
        ["NWS", "Nama Water Services"],
        ["O1 to O24", "The outfalls of the twenty-four subnetworks, the lowest point of each; a treatment plant takes the "
                      "name of the outfall at which it sits. A pumping station is named by its subnetwork and the manhole "
                      "at which it sits, as O1-M445"],
        ["OMR", "Omani rial"],
        ["OR", "Occupancy rate: persons per property"],
        ["PAEW", "Public Authority for Electricity and Water"],
        ["PAM-GUD-201, 202, 203", "The Nama Water Services design guidelines: general; water and TSE; wastewater"],
        ["PAM-STD", "Nama Water Services standard drawing"],
        ["PE", "Population equivalent"],
        ["PHF", "Peak hourly flow"],
        ["Property", "A household connection: one domestic electricity meter"],
        ["Qadf", "Average daily flow"],
        ["Qpdf", "Peak flow: the guideline's peak daily flow, equal to its peak hourly flow"],
        ["S1 to S7", "The sewer network options, by where the flow is treated (Section 6.2.6)"],
        ["SewerGEMS, WaterGEMS", "The sewer and the water network modelling software of the Terms of Reference"],
        ["SRT", "Solids retention time"],
        ["STP", "Sewage treatment plant"],
        ["TE", "Treated effluent, as the Terms of Reference use the term (see the note below)"],
        ["TKN", "Total Kjeldahl nitrogen"],
        ["TSE", "Treated sewage effluent, the guidelines' term for treated effluent"],
        ["TSS", "Total suspended solids"],
        ["UTM 40N", "Universal Transverse Mercator zone 40 North, WGS 84 datum"],
        ["WaPUG, CIWEM", "Wastewater Planning Users Group of the Chartered Institution of Water and Environmental "
                         "Management"],
    ], widths=[3.6, 12.9], font=9.5, keep_together=False)

    D.title(d, "A note on the term TE", size=12, space_before=8)
    p = D.p(d, "The Terms of Reference and this report use TE to mean treated "
               "effluent, the treated product of the sewage treatment plant. The "
               "NAMA design guidelines define TE as trade effluent and use TSE "
               "for treated sewage effluent. To avoid ambiguity this report "
               "writes treated effluent in full, and TSE where a guideline value "
               "is quoted.")
    N.add(p, "PAM-GUD-201, Table 1, page 16; PAM-GUD-203, page 13. "
             "Confirmation of the preferred convention is requested (Section 1.5.4).")
    D.pagebreak(d)


def executive_summary(d):
    t = F.totals(); ps = F.plot_summary(); ult = t["ultimate"]
    st = F.settlement_table(); ib = [r for r in st if r["key"] == "IBRI"][0]
    pf = B.plant_flows(); pl = B.process_loads(); no = B.no_overflow()
    D.h(d, 1, "Executive summary")

    D.p(d, "This report presents the concept design for the wastewater and "
           "treated effluent systems serving Ibri, together with the sewage "
           "treatment plant that will receive the collected flow. It records "
           "the data collected and the checks applied to it, sets out the "
           "design basis and the flows to saturation, and presents seven "
           "options for the sewer network with their cost, three of which are "
           "recommended in order of priority. The design basis was issued on "
           "its own as the Design Basis Report and presented to Nama Water "
           "Services.")

    D.picture(d, os.path.join(IMG, "D1_process.png"), 15.5)
    D.fig_caption(d, "The concept design process, from the data collected to the recommended option.")

    D.title(d, "The project area", size=12, space_before=8)
    p = D.p(d, "The study area covers 531.4 square kilometres within the "
               "Wilayat of Ibri, Governorate of Adh Dhahirah, and contains "
               "twenty-five named settlements. The project boundary received "
               "covers 439.8 square kilometres; it has been extended so that "
               "every cadastral plot of the twenty-five settlements, the planned "
               "ones included, lies inside it. All spatial work is carried out "
               "in UTM zone 40 North on the WGS 84 datum.")
    import facts_area as FA
    ga = FA.ground(); top = max(ga["settlements"], key=lambda r: r["z_med"]); low = FA.below_stp()
    D.p(d, f"The ground falls from the north-east to the south-west, from {top['z_med']:.0f} metres at {top['name']} to "
           f"{ga['stp_ground']:.0f} metres at the existing STP, and the wadis follow it. "
           f"{' and '.join(r['name'] for r in low)} lie below the existing STP and cannot drain to it by gravity. The "
           f"climate is hot desert, and the wind blows along one axis, north-west to south-east, across the line from "
           f"the existing STP to Ibri town. Section 1.2 describes the ground, the climate, the roads and the flood "
           f"hazard of the study area.")
    N.add(p, "Areas measured in the project geographic information system. "
             "Confirmation of the updated boundary is requested (Section 1.5.4).")

    D.title(d, "Data collected", size=12, space_before=8)
    D.p(d, "Data has been obtained from Nama Water Services covering the "
           "existing wastewater assets, the potable water network, electricity "
           "accounts and the cadastral plot layer. The datasets have been "
           "loaded into the project geographic information system, checked "
           "against the project boundary and assessed for completeness. "
           "Section 2.2 records the outcome in full. Four points are carried "
           "through the report.")
    D.bullet(d, "the wastewater dataset holds two networks. The constructed "
                "network, dated 2006, comprises 111.6 kilometres of gravity "
                "sewer and 10.0 kilometres of force main. A further 199.3 "
                "kilometres of gravity sewer, 23.2 kilometres of pumping main "
                "and the whole of the 45.7 kilometre treated effluent main are "
                "recorded as proposed. No treated effluent asset has been "
                "built. As the diameters and levels of the existing networks are "
                "not recorded, the areas they serve are designed as if they had "
                "no sewer: the new network carries all the sewage to the new "
                "treatment plants, which carry the full flow. The existing system "
                "is assessed as soon as the as-built survey is available, and "
                "where an existing sewer can be kept the new pipe in that street "
                "is not needed (Chapter 5).", lead="Existing assets — ")
    D.bullet(d, "the PAEW dataset provides 647.8 kilometres of water mains "
                "within the study area, and is adopted as the source for "
                "utility interfaces.", lead="Potable water — ")
    D.bullet(d, "33,971 meters have been placed on the plots to establish "
                "the number of properties on each and its use.",
             lead="Electricity accounts — ")
    D.bullet(d, "a topographic and utility survey covering the whole study "
                "area is in progress and will confirm levels, diameters and "
                "asset condition.", lead="Survey — ")

    D.title(d, "Design basis", size=12, space_before=8)
    p = D.p(d, "Wastewater generation is derived from water demand in "
               "accordance with the NAMA design guidelines. For the "
               "Governorate of Adh Dhahirah the domestic consumption rate is "
               "164 litres per person per day, with 22 per cent added for "
               "non-domestic and 14 per cent for governmental consumption. "
               "Return rates of 85 per cent for domestic and tanker supply and "
               "54 per cent for the rest give the wastewater flow. Sewage brought "
               "to the treatment plant by tanker from outside the study area is "
               "not in these flows; its volumes and sources are requested from "
               "Nama Water Services, so that the plant is designed to receive it "
               "(Sections 1.5.5 and 6.6.1).")
    N.add(p, "PAM-GUD-201, Table 11, page 60 and Table 19, page 71. The "
             "guideline states that the consumption values apply in the "
             "absence of updated figures and should be validated by NAMA "
             "before design.")
    p = D.p(d, f"The occupancy rate is set for each settlement as its 2024 "
               f"population divided by the domestic electricity meters counted "
               f"in it, with a floor of 4 persons per property, a cap of "
               f"{max(r['or_used'] for r in st):.2f}, the highest rate among the "
               f"larger settlements, and 4 for a settlement of fewer than a "
               f"thousand people. Ibri returns {ib['or_used']:.2f}. Section 4.1 "
               f"sets out the derivation.")
    N.add(p, "The guideline derives occupancy from population and housing "
             "units published by NCSI. Housing units are not published at "
             "settlement level, and counted domestic meters have been used "
             "in their place. The departure is recorded in Section 3.1.")

    D.title(d, "Population and flows", size=12, space_before=8)
    p = D.p(d, f"Every plot in the study area carries a population and an "
               f"average sewage flow, for 2024 and for every year to the year "
               f"its settlement is full. The use of each plot is determined from "
               f"the meters on it and from a satellite image of September 2026; "
               f"each settlement grows at the rate of the official "
               f"series and fills its own land before its growth moves to its "
               f"neighbours. The study area holds {fmt(t['pop_today'])} people "
               f"in 2024 and generates {fmt(t['q_today'])} cubic metres of "
               f"sewage a day. Ibri's land is full in {ib['sat_year']}; the "
               f"last settlement fills in {ult}, with {fmt(t['pop_ult'])} "
               f"people and {fmt(t['q_ult'])} cubic metres a day.")
    N.add(p, "Average flows before infiltration and before the STP margin. The "
             "five-year series for every settlement is in Sections 4.1.9 and 4.2.7.")
    import facts_w17 as FW         # Revision 4: the flow at the plants, from the network model
    ch = {y: FW.flow_chain(y) for y in ("2030", "2040", "2050", "2055", "2060", str(ult))}
    D.tab_caption(d, "The study area in the design years: from the plots to the treatment plants")
    D.table(d, ["Year", "People", "Average sewage flow from the plots, m³/d", "Average flow at the plants, with infiltration, m³/d",
                "Plant design average, with the 10 % margin, m³/d"], [
        ["2024, base", fmt(t["pop_today"]), fmt(t["q_today"]), "", ""],
        ["2030, opening year", fmt(t["pop"][2030]), fmt(t["q"][2030]), fmt(ch["2030"]["at_plants"]), fmt(ch["2030"]["design"])],
        ["2040", fmt(t["pop"][2040]), fmt(t["q"][2040]), fmt(ch["2040"]["at_plants"]), fmt(ch["2040"]["design"])],
        ["2050", fmt(t["pop"][2050]), fmt(t["q"][2050]), fmt(ch["2050"]["at_plants"]), fmt(ch["2050"]["design"])],
        ["2055, opening year plus 25", fmt(t["pop"][2055]), fmt(t["q"][2055]), fmt(ch["2055"]["at_plants"]), fmt(ch["2055"]["design"])],
        ["2060", fmt(t["pop"][2060]), fmt(t["q"][2060]), fmt(ch["2060"]["at_plants"]), fmt(ch["2060"]["design"])],
        [f"{ult}, saturation", fmt(t["pop_ult"]), fmt(t["q_ult"]), fmt(ch[str(ult)]["at_plants"]), fmt(ch[str(ult)]["design"])],
    ], widths=[4.4, 2.4, 3.2, 3.6, 2.9], font=9)
    D.p(d, "")
    c = ch[str(ult)]; L = FW.loads()
    p = D.p(d, f"The plants receive the flow the network carries plus its "
               f"infiltration, {fmt(c['infiltration'])} cubic metres a day over "
               f"the {fmt(L['active_sewer_km'])} km of sewer, whichever option is "
               f"chosen. The plants are designed with the guideline's ten "
               f"per cent margin. At the guideline's minimum loads of 60 grams of "
               f"BOD and 80 grams of suspended solids per person per day they "
               f"receive {fmt(pl[ult]['bod_kgd'])} kilograms of BOD a day at "
               f"saturation.")
    N.add(p, "Sections 3.4.1, 4.2.8 and 6.2.7, where the peak flows are also "
             "given. The loads are replaced by the laboratory results of the "
             "existing STP once received.")
    p = D.p(d, "Two industrial estates inside the town, at Al Tayyeb and "
               "Tanam, were found under the commercial tariff and are treated "
               "as special consumption. The army camp, a planned resort and "
               "two sources of tankered sewage outside the boundary are "
               "recorded in Section 4.3.")
    N.add(p, "The workforce of the two estates is an assumption, to be "
             "replaced by the estates' records.")

    D.title(d, "Decisions requested", size=12, space_before=8)
    D.p(d, f"Only what the guidelines do not settle is put to Nama Water "
           f"Services for approval: {len(APPROVALS)} decisions, listed below and "
           f"explained in the sections named. {len(INFORMED)} further values are "
           f"the guidelines' own, methods of this design or stated assumptions; "
           f"they are adopted and reported. No decision had been taken at the "
           f"date of this report. "
           f"The largest of them is the overflow: without it "
           f"{len(no['never'])} settlements never fill, and "
           f"{fmt(t['pop_ult'] - no['totals'][ult]['pop_own'])} people of the "
           f"series have nowhere to go by {ult}. Section 1.5 gives the decisions, "
           f"the adopted values, the other matters awaiting confirmation and "
           f"the {len(DATA_REQUESTS)} data requests.")
    D.tab_caption(d, "The decisions requested from Nama Water Services")
    D.table(d, ["", "Decision", "Section"],
            [[str(i + 1), title, what.rsplit("(Section", 1)[1].strip("s ).")] for i, (_, _, title, what) in enumerate(APPROVALS)],
            widths=[1.0, 11.5, 4.0], font=9.5)
    D.p(d, "")

    D.title(d, "How the options are developed and compared", size=12, space_before=8)
    p = D.p(d, "The guidelines ask for not fewer than three options, developed "
               "to the same functional requirement and the same effluent "
               "standard, and describe three characters for them: one advancing "
               "sustainability, one representing international best practice, "
               "and one based on practice already established in Oman. For the "
               "sewer network seven options have been modelled for where the "
               "flow is treated, from one plant to six. The characters are not "
               "tied to an option: they change the treatment process, the energy "
               "supply, solar generation included, and the reuse, not the "
               "network, and are costed at the preliminary design, where the "
               "treatment process is selected (Section 6.1).")
    N.add(p, "PAM-GUD-201, Section 12.1, page 95.")
    p = D.p(d, "The options are compared on their whole-life cost: the capital "
               "cost and twenty-five years of operating cost, discounted at five "
               "per cent. Where options fall within ten per cent of one another "
               "they are treated as equivalent in cost, and the more sustainable "
               "is adopted; where they are also equal on sustainability within "
               "the accuracy of a concept estimate, operability decides. Nama "
               "Water Services sets the weight given to each criterion of the "
               "full multi-criteria analysis, which the preliminary design "
               "completes with the characters.")
    N.add(p, "PAM-GUD-201, Sections 12.6 to 12.9, pages 104 to 106.")

    import rpt_options             # the network options, their cost and the recommendation
    rpt_options.summary_block(d)

    D.title(d, "Deliverables", size=12, space_before=8)
    D.p(d, "The Terms of Reference set out forty numbered deliverables for the "
           "concept stage. Section 1.3.1 lists them, with the section of this "
           "report that carries each.")
