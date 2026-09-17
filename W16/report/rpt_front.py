"""Contents, abbreviations and executive summary. The cover is the template's."""
import os

import doc as D
import notes as N
import facts_w14 as F
import facts_basis as B
from basis_items import APPROVALS, INFORMED, DATA_REQUESTS

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
fmt = F.fmt


def contents(d):
    D.title(d, "Contents")
    D.toc(d, "1-2")
    D.pagebreak(d)
    D.title(d, "Figures")
    D.list_of(d, "Figure")
    D.title(d, "Tables", space_before=10)
    D.list_of(d, "Table")
    D.pagebreak(d)


def abbreviations(d):
    D.title(d, "Abbreviations and definitions")
    D.table(d, ["Term", "Meaning"], [
        ["AAF", "Average annual flow: the design average of the treatment plant"],
        ["APSR", "Authority for Public Services Regulation"],
        ["BOD", "Biochemical oxygen demand"],
        ["CAPEX / OPEX", "Capital expenditure / operating expenditure"],
        ["CESMM3", "Civil Engineering Standard Method of Measurement, third edition"],
        ["COD", "Chemical oxygen demand"],
        ["EIA", "Environmental impact assessment"],
        ["GIS", "Geographic information system"],
        ["LPCD", "Litres per capita per day"],
        ["MoHUP", "Ministry of Housing and Urban Planning"],
        ["NCSI", "National Centre for Statistics and Information"],
        ["NOC", "No objection certificate"],
        ["OR", "Occupancy rate: persons per property"],
        ["PAEW", "Public Authority for Electricity and Water"],
        ["PE", "Population equivalent"],
        ["PHF", "Peak hourly flow"],
        ["Property", "A household connection: one domestic electricity meter"],
        ["Qadf", "Average daily flow"],
        ["Qpdf", "Peak flow: the guideline's peak daily flow, equal to its peak hourly flow"],
        ["SRT", "Solids retention time"],
        ["STP", "Sewage treatment plant"],
        ["TKN", "Total Kjeldahl nitrogen"],
        ["TSE", "Treated sewage effluent, the guidelines' term for treated effluent"],
        ["TSS", "Total suspended solids"],
        ["UTM 40N", "Universal Transverse Mercator zone 40 North, WGS 84 datum"],
    ], widths=[3.0, 13.5], font=9.5)

    D.title(d, "A note on the term TE", size=12, space_before=8)
    p = D.p(d, "The Terms of Reference and this report use TE to mean treated "
               "effluent, the treated product of the sewage treatment plant. The "
               "NAMA design guidelines define TE as trade effluent and use TSE "
               "for treated sewage effluent. To avoid ambiguity this report "
               "writes treated effluent in full, and TSE where a guideline value "
               "is quoted.")
    N.add(p, "PAM-GUD-201, Table 1, page 16; PAM-GUD-203, page 13. "
             "Confirmation of the preferred convention is requested (Section 5.3).")
    D.pagebreak(d)


def executive_summary(d):
    t = F.totals(); ps = F.plot_summary(); ult = t["ultimate"]
    st = F.settlement_table(); ib = [r for r in st if r["key"] == "IBRI"][0]
    pf = B.plant_flows(); pl = B.process_loads(); no = B.no_overflow()
    D.h(d, 1, "Executive summary")

    D.p(d, "This report presents the concept design for the wastewater and "
           "treated effluent systems serving Ibri, together with the sewage "
           "treatment plant that will receive the collected flow. It records "
           "the data collected, the checks applied to it, the design basis "
           "adopted and the state of the work at the date of issue. The design "
           "basis was issued on its own as the Design Basis Report and presented "
           "to Nama Water Services on 16 September 2026; this revision carries "
           "it in full.")

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
    N.add(p, "Areas measured in the project geographic information system. "
             "Confirmation of the updated boundary is requested (Section 5.3).")

    D.title(d, "Data collected", size=12, space_before=8)
    D.p(d, "Data has been obtained from Nama Water Services covering the "
           "existing wastewater assets, the potable water network, electricity "
           "accounts and the cadastral plot layer. The datasets have been "
           "loaded into the project geographic information system, checked "
           "against the project boundary and assessed for completeness. "
           "Section 7 records the outcome in full. Four points are carried "
           "through the report.")
    D.bullet(d, "the wastewater dataset holds two networks. The constructed "
                "network, dated 2006, comprises 111.6 kilometres of gravity "
                "sewer and 10.0 kilometres of force main. A further 199.3 "
                "kilometres of gravity sewer, 23.2 kilometres of pumping main "
                "and the whole of the 45.7 kilometre treated effluent main are "
                "recorded as proposed. No treated effluent asset has been "
                "built.", lead="Existing assets — ")
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
               "54 per cent for the rest give the wastewater flow.")
    N.add(p, "PAM-GUD-201, Table 11, page 60 and Table 19, page 71. The "
             "guideline states that the consumption values apply in the "
             "absence of updated figures and should be validated by NAMA "
             "before design.")
    p = D.p(d, f"The occupancy rate is set for each settlement as its 2024 "
               f"population divided by the domestic electricity meters counted "
               f"in it, with a floor of four persons per property, a cap of "
               f"{max(r['or_used'] for r in st):.2f}, the highest rate among the "
               f"larger settlements, and four for a settlement of fewer than a "
               f"thousand people. Ibri returns {ib['or_used']:.2f}. Section 14 "
               f"sets out the derivation.")
    N.add(p, "The guideline derives occupancy from population and housing "
             "units published by NCSI. Housing units are not published at "
             "settlement level, and counted domestic meters have been used "
             "in their place. The departure is recorded in Section 10.")

    D.title(d, "Population and flows", size=12, space_before=8)
    p = D.p(d, f"Every plot in the study area carries a population and an "
               f"average sewage flow, for 2024 and for every year to the year "
               f"its settlement is full. The use of each plot is determined from "
               f"the meters on it and from a satellite image of September 2026; "
               f"the capacity of the empty land is read from the built plots "
               f"around it; each settlement grows at the rate of the official "
               f"series and fills its own land before its growth moves to its "
               f"neighbours. The study area holds {fmt(t['pop_today'])} people "
               f"in 2024 and generates {fmt(t['q_today'])} cubic metres of "
               f"sewage a day. Ibri's land is full in {ib['sat_year']}; the "
               f"last settlement fills in {ult}, with {fmt(t['pop_ult'])} "
               f"people and {fmt(t['q_ult'])} cubic metres a day.")
    N.add(p, "Average flows before infiltration and before the STP margin. The "
             "five-year series for every settlement is in Sections 14.9 and 15.7.")
    D.tab_caption(d, "The study area in the design years")
    D.table(d, ["Year", "People", "Average sewage flow, m³/d", "STP average with the margin, m³/d", "STP peak hour with the margin, m³/d"], [
        ["2024, base", fmt(t["pop_today"]), fmt(t["q_today"]), "", ""],
        ["2030, opening year", fmt(t["pop"][2030]), fmt(t["q"][2030]), fmt(pf[2030]["aaf"]), fmt(pf[2030]["phf"])],
        ["2055, opening year plus 25", fmt(t["pop"][2055]), fmt(t["q"][2055]), fmt(pf[2055]["aaf"]), fmt(pf[2055]["phf"])],
        [f"{ult}, saturation", fmt(t["pop_ult"]), fmt(t["q_ult"]), fmt(pf[ult]["aaf"]), fmt(pf[ult]["phf"])],
    ], widths=[4.4, 2.4, 3.2, 3.3, 3.2], font=9)
    D.p(d, "")
    p = D.p(d, f"If the whole area drains to one STP, its design average in "
               f"{ult} is {fmt(pf[ult]['aaf'])} cubic metres a day and its peak "
               f"hour {fmt(pf[ult]['phf'])}, with the ten per cent margin and "
               f"before infiltration and tankers. At the guideline's minimum "
               f"loads of 60 grams of BOD and 80 grams of suspended solids per "
               f"person per day the plant receives {fmt(pl[ult]['bod_kgd'])} "
               f"kilograms of BOD a day at saturation.")
    N.add(p, "Sections 13.1 and 15.8. The loads are replaced by the laboratory "
             "results of the existing STP once received.")
    p = D.p(d, "Two industrial estates inside the town, at Al Tayyeb and "
               "Tanam, were found under the commercial tariff and are treated "
               "as special consumption. The army camp, a planned resort and "
               "two sources of tankered sewage outside the boundary are "
               "recorded in Section 16.")
    N.add(p, "The workforce of the two estates is an assumption, to be "
             "replaced by the estates' records.")

    D.title(d, "Decisions requested", size=12, space_before=8)
    D.p(d, f"Only what the guidelines do not settle is put to Nama Water "
           f"Services for approval: {len(APPROVALS)} decisions, listed below and "
           f"explained in the sections named. {len(INFORMED)} further values are "
           f"the guidelines' own or stated assumptions; they are adopted and "
           f"reported. No decision had been taken at the date of this report. "
           f"The largest of them is the overflow: without it "
           f"{len(no['never'])} settlements never fill, and "
           f"{fmt(t['pop_ult'] - no['totals'][ult]['pop_own'])} people of the "
           f"series have nowhere to go by {ult}. Section 5 gives the decisions, "
           f"the adopted values, the other matters awaiting confirmation and "
           f"the {len(DATA_REQUESTS)} data requests.")
    D.tab_caption(d, "The decisions requested from Nama Water Services")
    D.table(d, ["", "Decision", "Section"],
            [[str(i + 1), title, what.rsplit("(Section", 1)[1].strip("s ).")] for i, (_, _, title, what) in enumerate(APPROVALS)],
            widths=[1.0, 11.5, 4.0], font=9.5)
    D.p(d, "")

    D.title(d, "State of the work", size=12, space_before=8)
    D.p(d, "The design basis, the data assessment, the population and flow "
           "series and the assessment framework are complete. The concept "
           "hydraulic calculations for the sewer network have been completed "
           "on the basis set out here, and those for the treated effluent "
           "network and the treatment plant have begun. The topographic and "
           "utility survey is in progress; the hydraulic assessment of the "
           "existing networks follows it. The options for the sewer network, "
           "the treated effluent network and the treatment plant are presented "
           "as a framework in Part F and will be completed once the decisions "
           "of Section 5 are taken.")

    D.title(d, "How the options are developed and compared", size=12, space_before=8)
    D.p(d, "Three options are developed for each of the sewer network, the "
           "treated effluent network and the treatment plant. Each set follows "
           "the character the guidelines describe: one advancing "
           "sustainability, one representing international best practice, and "
           "one based on practice already established in Oman. Every option "
           "meets the same functional requirement and the same effluent "
           "standard, so that the difference between them lies in how the "
           "result is achieved. Section 21 sets out what distinguishes them in "
           "design terms.")
    D.p(d, "The options are compared over a twenty-five year period against "
           "seven criteria: total lifetime cost; sustainability, comprising "
           "carbon, circular economy and nature-based solutions; social "
           "development and in-country value; adaptability and resilience; "
           "operability; constructability; and environmental impact. Costs are "
           "discounted at five per cent. Nama Water Services sets the weight "
           "given to each criterion.")
    p = D.p(d, "Where two options fall within ten per cent of one another on "
               "total lifetime cost they are treated as equivalent in cost, "
               "and the more sustainable of the two is adopted. Sensitivity is "
               "tested by varying the weighting between criteria, the discount "
               "rate, and the input design criteria.")
    N.add(p, "PAM-GUD-201, Sections 12.6 to 12.9, pages 104 to 106.")

    D.title(d, "Deliverables", size=12, space_before=8)
    D.p(d, "The Terms of Reference set out forty numbered deliverables for the "
           "concept stage. This report issues the design basis, the assessment "
           "of the data, the design criteria, the population and flow series "
           "to saturation and the framework for the options and their "
           "appraisal. The options themselves, the cost estimate and the "
           "comparison follow once the design horizon is decided and the "
           "survey is complete. Section 3.1 lists each deliverable and its "
           "position.")
