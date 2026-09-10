"""Cover, contents, abbreviations and executive summary."""
import os

from docx.enum.text import WD_ALIGN_PARAGRAPH as AL

import doc as D
import notes as N

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

CLIENT = "Nama Water Services Company SAOC"
PROJECT = ("Consultancy Services for Design and Supervision for STP, Sewer "
           "and TE Networks Systems in Ibri")
TENDER = "Tender No. T/2719110/2025"
TITLE = "Concept Design Report"
REV = "Revision 1"
DATE = "August 2026"


def cover(d):
    D.p(d, "", space_after=54)
    D.p(d, "Sultanate of Oman", align=AL.CENTER, bold=True, size=13)
    D.p(d, CLIENT, align=AL.CENTER, bold=True, size=12)
    D.p(d, "", space_after=34)
    D.p(d, PROJECT, align=AL.CENTER, bold=True, size=13.5, colour=D.GREY)
    D.p(d, TENDER, align=AL.CENTER, size=11, colour=D.GREY)
    D.p(d, "", space_after=34)
    D.p(d, TITLE, align=AL.CENTER, bold=True, size=26, colour=D.BLUE)
    D.p(d, REV, align=AL.CENTER, bold=True, size=13, colour=D.MID)
    D.p(d, "", space_after=60)
    D.p(d, "Renardet S.A. & Partners Consulting Engineers", align=AL.CENTER,
        bold=True, size=11.5)
    D.p(d, f"Project 2621   ·   {DATE}", align=AL.CENTER, size=10,
        colour=D.GREY)
    D.pagebreak(d)


def contents(d):
    D.h(d, 1, "Contents")
    D.toc(d, levels="1-2")
    D.pagebreak(d)


def abbreviations(d):
    D.h(d, 1, "Abbreviations and definitions")
    D.table(d, ["Term", "Meaning"], [
        ["AAF", "Average annual flow"],
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
        ["PAEW", "Public Authority for Electricity and Water"],
        ["PE", "Population equivalent"],
        ["Qadf", "Average daily flow"],
        ["Qpdf", "Peak daily flow"],
        ["SRT", "Solids retention time"],
        ["STP", "Sewage treatment plant"],
        ["TKN", "Total Kjeldahl nitrogen"],
        ["TSS", "Total suspended solids"],
        ["UTM 40N", "Universal Transverse Mercator zone 40 North, WGS 84 datum"],
    ], widths=[3.0, 13.5], font=9.5)

    D.h(d, 2, "A note on the term TE")
    p = D.p(d, "The Terms of Reference and this report use TE to mean treated "
               "effluent, that is the treated product of the sewage treatment "
               "plant. The NAMA design guidelines define TE as trade effluent "
               "and use TSE for treated sewage effluent. To avoid ambiguity, "
               "this report uses the term treated effluent in full, and TSE "
               "where a guideline value is quoted.")
    N.add(p, "PAM-GUD-201, Table 1, page 16; PAM-GUD-203, page 13. "
             "Confirmation of the preferred convention is requested.")
    D.pagebreak(d)


def executive_summary(d):
    D.h(d, 1, "Executive summary")

    D.p(d, "This report presents the concept design for the wastewater and "
           "treated effluent systems serving Ibri, together with the sewage "
           "treatment plant that will receive the collected flow. It records "
           "the data collected to date, the checks applied to that data, the "
           "design basis adopted, and the state of the work at the date of "
           "issue.")

    D.picture(d, os.path.join(IMG, "D1_process.png"), 15.5)
    D.fig_caption(d, "The concept design process, from the data collected to the recommended option.")

    D.h(d, 2, "The project area")
    p = D.p(d, "The study area covers 531.4 square kilometres within the "
               "Wilayat of Ibri, Governorate of Adh Dhahirah, and contains "
               "twenty-five named settlements. All spatial work is carried out "
               "in UTM zone 40 North on the WGS 84 datum.")
    N.add(p, "Area measured from the project boundary supplied with the "
             "Inception Report. Two boundary versions were issued with that "
             "report; confirmation of the approved boundary is requested, and "
             "the item is listed in Section 5.")

    D.h(d, 2, "Data collected")
    D.p(d, "Data has been obtained from Nama Water Services covering the "
           "existing wastewater assets, the potable water network, electricity "
           "accounts and the cadastral plot layer. The datasets have been "
           "loaded into the project geographic information system, checked "
           "against the project boundary, and assessed for completeness. "
           "Section 7 records the outcome of those checks in full.")

    D.p(d, "Four points arise from that assessment and are carried through the "
           "report.")
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
    D.bullet(d, "33,970 accounts have been used to establish the number of "
                "properties on each plot and the category of use.",
             lead="Electricity accounts — ")
    D.bullet(d, "a topographic and utility survey covering the whole study "
                "area is in progress and will confirm levels, diameters and "
                "asset condition.", lead="Survey — ")

    D.h(d, 2, "Design basis")
    p = D.p(d, "Wastewater generation is derived from water demand in "
               "accordance with the NAMA design guidelines. For the "
               "Governorate of Adh Dhahirah the domestic consumption rate is "
               "164 litres per capita per day, with uplifts of 22 per cent for "
               "non-domestic and 14 per cent for governmental consumption. "
               "Return rates of 85 per cent for domestic and tanker supply and "
               "54 per cent for non-domestic supply are applied to obtain the "
               "wastewater flow.")
    N.add(p, "PAM-GUD-201, Table 11, page 60 and Table 19, page 71. The "
             "guideline states that the consumption values apply in the "
             "absence of updated figures and should be validated by NAMA "
             "before design.")

    p = D.p(d, "An occupancy rate of 5.32 persons per domestic property has "
               "been derived from the settlement populations and the counted "
               "domestic electricity accounts. Section 15 sets out the "
               "derivation and the checks applied to it.")
    N.add(p, "The guideline derives occupancy from population and housing "
             "units published by NCSI. Housing units are not published at "
             "settlement level, and counted domestic accounts have been used "
             "in their place. The departure is recorded in Section 10.")

    D.h(d, 2, "State of the work")
    D.p(d, "The design basis, the data assessment and the assessment "
           "framework are complete. The network design has been developed and "
           "tested over a representative area of the town and is being "
           "extended to the whole study area as the survey data becomes "
           "available. The options for the sewer network, the treated effluent "
           "network and the treatment plant are presented as a framework in "
           "Part F and will be completed in the next revision.")

    D.h(d, 2, "How the options are developed and compared")
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

    D.h(d, 2, "Deliverables")
    D.p(d, "The Terms of Reference set out forty numbered deliverables for the "
           "concept stage. This report issues the design basis, the assessment "
           "of the data, the design criteria and the framework for the options "
           "and their appraisal. The flow series, the options themselves, the "
           "cost estimate and the comparison follow in the next revision, once "
           "the design horizon is confirmed and the survey is complete. "
           "Section 3.1 lists each deliverable and its position.")

    D.h(d, 2, "Matters requiring confirmation")
    D.p(d, "Six matters require confirmation from Nama Water Services. They "
           "are set out in Section 5 with the relevant references, and are "
           "summarised here.")
    D.table(d, ["", "Matter"], [
        ["1", "The design horizon to be adopted"],
        ["2", "The approved project boundary"],
        ["3", "Georeferenced versions of the project figures"],
        ["4", "The hydraulic modelling software to be used"],
        ["5", "The timing of the environmental impact assessment"],
        ["6", "The convention for the term TE"],
    ], widths=[1.2, 15.3], font=9.5)

    D.pagebreak(d)
