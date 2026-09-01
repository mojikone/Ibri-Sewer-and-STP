"""Build the Concept Design Report structure as a Word document.

The TOR requires the report structure to be approved before the report is
written, so this is a submission in its own right. Each section carries the
T03 Rev 01 section that gives the method, which is what makes the outline
checkable rather than just a list of headings.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "TUTORIALS", "T03_R01"))

from docx.enum.text import WD_ALIGN_PARAGRAPH as AL

import doc as D

OUT = os.path.join(ROOT, "W9", "docs",
                   "Concept_Design_Report_Structure.docx")

# section number, title, method reference in T03 Rev 01
SECTIONS = [
    ("Front matter", None, None),
    ("F1", "Document control", None),
    ("F2", "Authorship and discipline signatures", None),
    ("F3", "Abbreviations and definitions", "Front matter"),
    ("F4", "Executive summary", None),

    ("Part A", "Project, scope and process", None),
    ("1", "Introduction, background and RG Master Plan context", None),
    ("2", "Scope and boundaries", None),
    ("3", "Programme and design stage gates", None),
    ("4", "Meetings, consultation and decisions record", None),
    ("5", "Quality plan and HSE plan", None),

    ("Part B", "Data", None),
    ("6", "Data collection register", "3"),
    ("7", "Data validation and adequacy assessment", "3"),
    ("8", "Survey, geotechnical investigation and trial pits", "13"),
    ("9", "Existing systems — as-built and GIS", "15"),

    ("Part C", "Basis of design", None),
    ("10", "Codes, standards and the deviations register", "22"),
    ("11", "Level of service, resilience and contingency", "—"),
    ("12", "Design criteria — networks", "9, 11"),
    ("13", "Design criteria — STP and process", "16"),

    ("Part D", "Demand and flows", None),
    ("14", "Population and land use", "3, 4"),
    ("15", "Wastewater generation and design flows", "5, 6, 7, 8"),
    ("16", "Trade effluent and industrial contributions", "16.4"),
    ("17", "Treated effluent demand and customers", "17"),

    ("Part E", "Existing system", None),
    ("18", "Hydraulic assessment of existing networks", "14, 15"),
    ("19", "Rehabilitation and upgrading", "15"),
    ("20", "RG Master Plan verification", "4, 7"),

    ("Part F", "Options", None),
    ("21", "Options methodology", "21"),
    ("22", "Sewer network options", "9, 10"),
    ("23", "Pumping and lifting stations, force mains, surge", "11, 12"),
    ("24", "Treated effluent network options", "17"),
    ("25", "STP options — technology, siting, phasing", "16"),
    ("26", "Excess effluent, emergency provisions, tankers", "16.8"),
    ("27", "Sludge management strategy", "18"),

    ("Part G", "Assessment and appraisal", None),
    ("28", "Ground model and geotechnical report", "13"),
    ("29", "Flood protection assessment", "16.9"),
    ("30", "Odour assessment and buffer derivation", "12, 16.9"),
    ("31", "Climate resilience", "—"),
    ("32", "Environmental and social assessment, EIA scoping", "—"),
    ("33", "Utility interfaces and the NOC register", "13"),
    ("34", "Sustainability — carbon, circular economy, ICV", "20.5"),
    ("35", "Cost — CAPEX, OPEX, life cycle cost", "19, 20"),
    ("36", "Risk register", "20.6"),
    ("37", "Value engineering study", "21.5"),
    ("38", "Multi-criteria results and recommendation", "21.4"),

    ("Part H", "Delivery", None),
    ("39", "Implementation roadmap", "—"),
    ("40", "Contracting strategy and packaging", "—"),
    ("41", "Project Integration Plan", "—"),
    ("42", "Conclusions and recommendations", None),
    ("43", "Appendices", None),
]


def build():
    d = D.new_document()

    # ------------------------------------------------------------ cover
    D.p(d, "", space_after=60)
    D.p(d, "Nama Water Services Company SAOC", align=AL.CENTER, bold=True,
        size=12)
    D.p(d, "Consultancy Services for Design and Supervision for STP, Sewer and "
           "TE Networks Systems in Ibri", align=AL.CENTER, bold=True, size=13,
        colour=D.GREY)
    D.p(d, "Tender No. T/2719110/2025", align=AL.CENTER, size=11, colour=D.GREY)
    D.p(d, "", space_after=40)
    D.p(d, "Concept Design Report", align=AL.CENTER, bold=True, size=24,
        colour=D.BLUE)
    D.p(d, "Proposed Structure, submitted for approval", align=AL.CENTER,
        bold=True, size=14, colour=D.MID)
    D.p(d, "", space_after=40)
    D.p(d, "Renardet S.A. & Partners", align=AL.CENTER, bold=True, size=11)
    D.p(d, "Project 2621   ·   Revision 0   ·   August 2026",
        align=AL.CENTER, size=10, colour=D.GREY)
    D.pagebreak(d)

    # ------------------------------------------------------------ purpose
    D.h(d, 1, "1   Purpose of this submission")
    D.p(d, "The Terms of Reference require the structure of the Concept Design "
           "Report to be approved before the report itself is prepared: "
           "“The Consultant shall submit complete concept design report "
           "structure for approval according to that will submit comprehensive "
           "concept report” (Scope of Work, page 63 of 204).")
    D.p(d, "This document is that submission. It sets out the proposed "
           "structure, shows how it maps onto the forty numbered concept "
           "deliverables listed in the Scope of Work, and identifies the "
           "decisions required from Nama Water Services before the report can "
           "be completed.")

    D.h(d, 2, "1.1   Why the structure matters commercially")
    D.table(d, ["Provision", "Reference"],
            [["Concept Design is 60 days, plus a separate 21-day review",
              "Tender p147, and as a contract term p177"],
             ["15 to 20 per cent of the design fee is released on approval of "
              "the Concept Design", "Tender p153 and p154"],
             ["Delay is charged at 1 per cent of the Design Stage Contract "
              "Value per week", "Tender p151, p180, p193"],
             ["Preliminary Design begins only after STP concept approval",
              "Tender p148 and p178"],
             ["The concept fee certifies in three separable parts",
              "Bill of Quantities items A1, A2 and A3"]],
            widths=[10.0, 6.5], font=9.5)
    D.p(d, "")
    D.p(d, "The report must therefore be a self-contained, formally approvable "
           "document, and its sections must map cleanly onto the three "
           "certifiable parts so that each can be signed off independently.")

    # ------------------------------------------------------- terminology
    D.h(d, 1, "2   Two matters to settle before drafting", page_break=True)

    D.h(d, 2, "2.1   The meaning of TE")
    D.p(d, "PAM-GUD-201 and PAM-GUD-203 define TE as Trade Effluent and TSE as "
           "Treated Sewage Effluent. The Terms of Reference, the tender and "
           "this project use TE to mean treated effluent. A reader familiar "
           "with the guidelines will understand a trade effluent network "
           "wherever the report says TE network.")
    D.p(d, "We propose to adopt TSE throughout the report for the treated "
           "product of the plant, with an explicit note in the abbreviations, "
           "and invite confirmation.")

    D.h(d, 2, "2.2   A cross-reference in the Terms of Reference")
    D.p(d, "The Terms of Reference require the STP location report to follow "
           "“item 2.1 in WASTEWATER DESIGN MANUAL Section 05”. "
           "PAM-GUD-203 Revision 01 of March 2026 merged the former manuals "
           "into a single document and renumbered them; there is no Section 05 "
           "and no item 2.1. The equivalent content is now Section 10.1, Site "
           "Selection, at pages 63 and 64.")
    D.p(d, "We propose to follow Section 10.1 and invite confirmation.")

    # ------------------------------------------------------- structure
    D.h(d, 1, "3   Proposed structure", page_break=True)
    D.p(d, "The third column names the section of Tutorial T03 Revision 01 "
           "that sets out the method, the equations and their source pages for "
           "that part of the work. A dash indicates a section for which the "
           "methodology document does not yet carry a method.")

    rows = []
    for num, title, method in SECTIONS:
        if num.startswith("Part") or title is None:
            # a part heading: emphasise it so the groups read at a glance
            rows.append(["**" + num + "**", "**" + (title or "") + "**", ""])
        else:
            rows.append([num, title, method or ""])

    D.table(d, ["", "Section", "Method in T03 Rev 01"], rows,
            widths=[1.6, 11.0, 3.9], font=9)

    # ------------------------------------------------------- gaps
    D.h(d, 1, "4   Presentation conventions", page_break=True)
    D.p(d, "These conventions apply throughout the report and are stated here "
           "so that they form part of what is approved.")
    D.table(d, ["Element", "Convention"],
            [["Equations",
              "Native Word objects, editable in the equation editor. Each is "
              "numbered and followed by a table giving every symbol, its "
              "meaning and its unit"],
             ["Footnotes",
              "Footnotes restart at 1 on each page. They carry the guideline "
              "reference and page, the caveat and the derivation; matter "
              "belonging to the argument is in the body text"],
             ["Figures",
              "Maps, process flowcharts and data charts share one numbering "
              "sequence. The caption carries the number"],
             ["Tables",
              "A separate sequence, caption above the table. Header rows "
              "repeat across a page break and a row is not split"],
             ["Maps",
              "Produced from the project geographic information system, with "
              "a satellite background, a legend limited to the layers that "
              "map draws, and a box giving the quantities behind the figure"],
             ["Charts",
              "Drawn from the same measured values as the text. Where an "
              "asset is recorded as proposed rather than constructed it is "
              "shown distinctly and identified in the legend"],
             ["Revisions",
              "Each issued revision is retained unaltered; a revision is "
              "never overwritten"]],
            widths=[3.2, 13.3], font=9.5)

    D.h(d, 1, "5   The existing network comprises two networks",
        page_break=True)
    D.p(d, "This is recorded here because it determines what several sections "
           "of the report are able to state. The wastewater dataset supplied "
           "holds a constructed network and a proposed network, distinguished "
           "by the operational status field and confirmed by four further "
           "fields that agree with it on every record.")
    D.table(d, ["Asset", "Constructed", "Proposed"],
            [["Gravity sewer", "111.6 km, installed 2006", "199.3 km"],
             ["Force or pumping main", "10.0 km, installed 2006", "23.2 km"],
             ["Treated effluent main", "none", "45.7 km"]],
            widths=[5.0, 6.0, 5.5], font=9.5)
    D.p(d, "")
    D.p(d, "Neither diameter nor invert level is recorded on the constructed "
           "network, and the records carry a remark that the data is to be "
           "used for reference only. Section 18, the hydraulic assessment of "
           "the existing networks, therefore cannot be completed from the "
           "data supplied and waits on the survey now in progress.")

    D.h(d, 1, "6   Sections without a documented method", page_break=True)
    D.p(d, "Six sections of the report have no corresponding method in the "
           "current revision of the methodology document. They are listed here "
           "so that the gap is visible rather than discovered during drafting.")
    D.table(d, ["Section", "Why it is outstanding"],
            [["11  Level of service, resilience and contingency",
              "Requires the failure-mode analysis and criticality framework to "
              "be established with NWS"],
             ["31  Climate resilience",
              "The guideline sets a 50-year horizon at +2 °C and +4 °C; the "
              "method for applying it to site selection is not yet written"],
             ["32  Environmental and social assessment",
              "Depends on the ruling sought on EIA timing — see Section 7"],
             ["39  Implementation roadmap",
              "Follows from the recommended option, so it is written last"],
             ["40  Contracting strategy",
              "A separate workshop is required under the Terms of Reference"],
             ["41  Project Integration Plan",
              "A named deliverable in PAM-GUD-201 page 107; scope to be agreed"]],
            widths=[6.0, 10.5], font=9.5)
    D.p(d, "")
    D.p(d, "None of these is a blocker for the structure itself. Each will be "
           "added to the methodology document before the corresponding report "
           "section is drafted.")

    # ------------------------------------------------------- decisions
    D.h(d, 1, "7   Decisions required from Nama Water Services")
    D.p(d, "The following items either block the report or would make it wrong "
           "if left unresolved. They are set out in full, with the supporting "
           "references, in the accompanying register of decisions and "
           "clarifications.")
    D.table(d, ["", "Item"],
            [["1", "The design horizon. The Inception Report states that "
                   "planning extends to 2100 as instructed by NWS; the Terms "
                   "of Reference state completion plus 25 years or ultimate "
                   "saturated flow"],
             ["2", "Which programme governs, given that the kickoff "
                   "presentation and the Inception Report carry schedules "
                   "differing by approximately two weeks throughout"],
             ["3", "The approved project boundary, two versions of which were "
                   "issued in the same package, differing by 18 per cent "
                   "against a survey scope priced at approximately 450 km²"],
             ["4", "Georeferenced versions of Figures 1, 2 and 3, which define "
                   "the concept and as-built boundaries and are currently "
                   "supplied as images without coordinates"],
             ["5", "The modelling software, named as MIKE URBAN in the tender "
                   "staffing schedule and as SewerGEMS and WaterGEMS in the "
                   "Scope of Work"],
             ["6", "The timing of the Environmental Impact Assessment, placed "
                   "at scoping in one clause of PAM-GUD-201 and as a full "
                   "assessment at concept stage in another"]],
            widths=[1.2, 15.3], font=9.5)

    D.p(d, "")
    D.callout(d, "Sequencing.",
              "Items 1 to 4 determine work that would otherwise be done twice. "
              "We recommend they are resolved ahead of the remaining concept "
              "programme rather than alongside it.",
              fill="EAF1F8", colour=D.MID)

    D.footer_pagenum(d, "Concept Design Report — Proposed Structure  ·  "
                        "Project 2621")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    d.save(OUT)
    print(f"wrote {OUT}")
    return OUT


if __name__ == "__main__":
    path = build()
    if "--pdf" in sys.argv:
        import to_pdf
        pdf, pages = to_pdf.convert(path)
        print(f"wrote {pdf}  ({pages} pages)")
