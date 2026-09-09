"""Build the Design Criteria document for the W13 sewer network design.

    python build.py          build the .docx
    python build.py --pdf    build and render to PDF through Word

Every value in this document comes from `_BRAIN/02_DESIGN_CRITERIA.md` (the
only permitted source of numeric design values), from the standing decisions
recorded in `_BRAIN/00_CURRENT.md`, or from the values the W13 pipeline
actually applies in `W13/py/sewnet/criteria.py`. Nothing is quoted from memory.

The document furniture (doc.py, notes.py, omml.py, to_pdf.py) is copied from
the W9 report build so this folder rebuilds on its own.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH as AL

import doc as D
import notes as N
import omml as M

REV = "R0"
DATE = "September 2026"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, REV, f"Ibri_Sewer_Design_Criteria_{REV}.docx")

# --------------------------------------------------------------- table shapes
W4 = [3.4, 6.6, 2.4, 4.2]        # item, guideline, reference, adopted in W13
W3 = [4.2, 9.6, 2.8]             # item, requirement, reference
H4 = ["Item", "Guideline requirement or value", "Reference", "Adopted in W13"]
H3 = ["Item", "Requirement or value", "Reference"]


def crit(d, rows, adopted=True, font=8.5):
    if adopted:
        return D.table(d, H4, rows, widths=W4, font=font)
    return D.table(d, H3, rows, widths=W3, font=font)


def params(d, rows):
    """Symbol table under an equation, kept in one piece: every row but the
    last keeps with the next, so the table cannot break after its header
    and leave the symbols on the following page."""
    from docx.oxml import OxmlElement
    t = D.table(d, ["Symbol", "Meaning", "Unit"], rows,
                widths=[2.4, 11.0, 3.2], font=8.5, header_fill="2E629E")
    for row in t.rows[:-1]:
        for cell in row.cells:
            for par in cell.paragraphs:
                par._p.get_or_add_pPr().insert(0, OxmlElement("w:keepNext"))
    return t


def note(d, text, foot=None):
    par = D.p(d, text)
    if foot:
        N.add(par, foot)
    return par


def eq(d, inner, number):
    """A numbered display equation kept on the same page as the parameter
    table that follows it, so a page break never strands the table alone."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    el = M.display(d, inner, number=number)
    ppr = el.find(qn("w:pPr"))
    ppr.insert(0, OxmlElement("w:keepNext"))
    return el


# ======================================================================= front
def cover(d):
    D.p(d, "", space_after=54)
    D.p(d, "Sultanate of Oman", align=AL.CENTER, bold=True, size=13)
    D.p(d, "Nama Water Services Company SAOC", align=AL.CENTER, bold=True,
        size=12)
    D.p(d, "", space_after=34)
    D.p(d, "Consultancy Services for Design and Supervision for STP, Sewer "
           "and TE Networks Systems in Ibri", align=AL.CENTER, bold=True,
        size=13.5, colour=D.GREY)
    D.p(d, "Tender No. T/2719110/2025", align=AL.CENTER, size=11,
        colour=D.GREY)
    D.p(d, "", space_after=34)
    D.p(d, "Design Criteria", align=AL.CENTER, bold=True, size=26,
        colour=D.BLUE)
    D.p(d, "Sewer Network Design, Iteration W13", align=AL.CENTER, bold=True,
        size=14, colour=D.MID)
    D.p(d, f"Revision {REV[1:]}", align=AL.CENTER, bold=True, size=13,
        colour=D.MID)
    D.p(d, "", space_after=60)
    D.p(d, "Renardet S.A. & Partners Consulting Engineers", align=AL.CENTER,
        bold=True, size=11.5)
    D.p(d, f"Project 2621   ·   {DATE}", align=AL.CENTER, size=10,
        colour=D.GREY)
    D.pagebreak(d)

    D.h(d, 1, "Document control")
    D.table(d, ["Revision", "Date", "Status", "Basis"], [
        ["0", "7 September 2026", "For design use",
         "Project design-criteria register, with the 12 m cover decision and "
         "the wadi rules checked against the guideline pages on 7 September "
         "2026; values applied by the W13 design pipeline read from its "
         "criteria module on the same date"],
    ], widths=[1.8, 3.2, 2.8, 8.8], font=9)
    D.p(d, "")
    D.p(d, "This document is rebuilt from source on every revision. A revision "
           "that has been issued is not overwritten; the next revision is "
           "written to its own folder.", size=9.5, colour=D.GREY)
    D.pagebreak(d)


def contents(d):
    D.h(d, 1, "Contents")
    D.toc(d, levels="1-2")
    D.pagebreak(d)


# ================================================================== section 1
def s1_purpose(d):
    D.h(d, 1, "1  Purpose, sources and how to read this document")

    D.p(d, "This document sets out the design criteria for the Ibri sewer "
           "network. Every numeric value is taken from one of the three Nama "
           "Water Services design guidelines and cited to its page, or is a "
           "stated project decision or assumption recorded in Sections 20 "
           "and 21. No value has been taken from memory or from general "
           "practice.")

    D.h(d, 2, "1.1  Sources")
    D.table(d, ["Code", "Document", "What it governs here"], [
        ["G203", "PAM-GUD-203 Wastewater Design Guidelines, 201 pages",
         "Gravity sewers, chambers, pumping stations, force mains, treatment "
         "plants, odour, surveys"],
        ["G1", "PAM-GUD-201 General Design Guidelines, 152 pages",
         "Population, demand and flow estimation, design life, options "
         "appraisal, wadi and road crossings, modelling"],
        ["G2", "PAM-GUD-202 Water and TSE Design Guidelines v1.0, 177 pages",
         "Treated effluent and water networks"],
        ["Scope", "Terms of Reference, Tender T/2719110/2025",
         "Design horizons, model years, deliverables, inverted siphons"],
        ["R0", "Inception Report Revision 0 and its demand workbook, "
               "August 2026",
         "Project values already adopted, reconciled against the guideline "
         "in Appendix A"],
    ], widths=[1.6, 6.5, 8.5], font=9)

    D.h(d, 2, "1.2  Citation convention")
    D.p(d, "A reference such as G203-p33 §4.6.3 means page 33, clause 4.6.3 "
           "of PAM-GUD-203. G1 and G2 refer to PAM-GUD-201 and PAM-GUD-202 in "
           "the same way. Page numbers are the printed page numbers of the "
           "guideline PDF.")
    D.p(d, "Where the guideline's wording decides how a rule applies, the "
           "phrase is quoted. Shall and must are requirements. Recommended "
           "and should are guidance the design follows unless a stated reason "
           "exists not to. A value marked as a project decision or a project "
           "assumption is ours, not the guideline's, and is listed in the "
           "registers at the end.")

    D.h(d, 2, "1.3  Precedence")
    p = D.p(d, "An NWS-approved demand calculation, if one exists, outranks the "
               "whole flow-estimation chain in Section 12. The domestic "
               "consumption values in the guideline are indicative and are to "
               "be validated by NWS before design. Where the guideline gives "
               "two methods, the one written as a requirement governs and the "
               "other is a labelled fallback; Section 12.1 sets this out.")
    N.add(p, "G1-p59 §7.3 and G1-p70 §7.4: \"In the absence of a "
             "developer-provided water demand calculation based on an approved "
             "methodology, the water demand shall be calculated in accordance "
             "with the methodology detailed below.\" G1-p60 Table 11: values "
             "\"should be validated by NWS as essential design criteria, "
             "before designing the project\".")

    D.h(d, 2, "1.4  The W13 design and the column \"Adopted in W13\"")
    p = D.p(d, "The network design is developed in iterations. Iteration W13 is "
               "the current design. It is calibrated on a 5.51 km² test area "
               "in Ibri town, where it produces 1,415 chambers, 71.6 km of "
               "sewer, a deepest cover of 10.45 m and no pumping station. The "
               "design must reproduce that result after every change before "
               "it is extended to the 531 km² study area.")
    N.add(p, "Test-area result of the W13 pipeline on 7 September 2026, "
             "identical to the W8 design it was copied from. The built Nama "
             "network on the same ground also needs no pumping station.")
    D.p(d, "Where a criterion is implemented in the design pipeline, the value "
           "applied is shown in the column \"Adopted in W13\". A blank cell "
           "means the criterion applies at a later stage or to a system the "
           "pipeline does not yet design. Sections 15 to 19 concern the "
           "treatment plant, the treated effluent system, odour, modelling "
           "and surveys, and carry no such column.")

    D.h(d, 2, "1.5  Vocabulary")
    D.p(d, "The guideline names the tertiary pipes property connection sewer, "
           "rider sewer and lateral sewer. The network hierarchy in the design "
           "uses Nama's as-built vocabulary of trunk main, sub main and "
           "lateral, read from the manhole identifiers of the built network. "
           "Where this document says lateral sewer it means the guideline's "
           "tertiary pipe; where it says lateral tier it means the lowest "
           "tier of the secondary network.")


# ================================================================== section 2
def s2_hydraulics(d):
    D.h(d, 1, "2  Gravity sewer hydraulics", page_break=True)
    D.tab_caption(d, "Hydraulic design criteria for gravity sewers "
                     "(G203 §4.2, pages 24 to 28)")
    crit(d, [
        ["Design method",
         "Colebrook-White or Manning; licensed software approved by NWS. The "
         "scope names SewerGEMS",
         "G203-p24",
         "Colebrook-White on the true internal bore; SewerGEMS as the "
         "referee model"],
        ["Roughness, Colebrook-White",
         "**ks = 1.5 mm**, all pipe sizes and materials",
         "G203-p24, p28", "1.5 mm"],
        ["Kinematic viscosity",
         "1.141 × 10⁻⁶ m²/s at 15 °C, conservative basic design",
         "G203-p25", "1.141 × 10⁻⁶ m²/s"],
        ["Self-cleansing velocity",
         "**0.75 m/s at peak flow**; 0.90 m/s preferred",
         "G203-p26",
         "0.75 m/s required at every pipe; 0.90 m/s reported"],
        ["Maximum velocity",
         "**3.0 m/s** at design depth of flow",
         "G203-p27, p29", "3.0 m/s"],
        ["Proportional depth at peak flow",
         "d/D ≤ **0.65** for D ≤ 350 mm; d/D ≤ **0.50** for D > 350 mm",
         "G203-p27 Table 10", "As guideline, threshold at 350 mm"],
        ["Manning n",
         "PVC and GRP 0.009 to 0.011; PE 0.009 to 0.015; cement-lined "
         "concrete 0.012",
         "G203-p23 Table 8",
         "0.013 as the ks-equivalent for the SewerGEMS export"],
        ["Minimum gradient method",
         "\"Steeper gradient calculated based on self-cleansing velocity and "
         "minimum tractive force methodology shall be adopted as minimum pipe "
         "gradient.\" The tractive-force method applies at network heads "
         "where 0.75 m/s cannot be reached",
         "G203-p27 §4.2.2.1",
         "The steeper of Table 11 (Section 3) and Equation 1"],
        ["Early-phase low flows",
         "Flow in the early development phases is below the design flow, "
         "with a clogging risk at low velocity; more frequent inspection and "
         "cleansing in that period",
         "G203-p28 §4.2.6",
         "Self-cleansing verified at start-year flows; see Section 12.3 on "
         "the direction of accuracy"],
    ])

    D.h(d, 2, "2.1  Minimum gradient by tractive force")
    p = D.p(d, "The guideline gives the tractive-force method of Mara, Sleigh "
               "and Taylor for the minimum gradient, with a proportional depth "
               "of 0.2 and a Manning n of 0.013 behind it. It gives no numeric "
               "design value of the tractive tension; that value is a project "
               "assumption to be confirmed with NWS.")
    N.add(p, "G203-p27 §4.2.2.1. The equation is printed in the guideline as "
             "an image. Its simplified form without the tension term is valid "
             "only at τ = 1 Pa.")
    n = D.next_eq()
    eq(d, M.seq(M.sub(M.r("S"), M.up("min")), M.EQ, M.r("K"), M.CDOT,
                       M.sup(M.r("τ"), M.r("1.23")), M.CDOT,
                       M.sup(M.r("Q"), M.r("−0.461"))), number=n)
    params(d, [
        ["Smin", "Minimum gradient", "m/m"],
        ["K", "2.33 × 10⁻⁴ with Q in m³/s; 5.5 × 10⁻³ with Q in L/s", "–"],
        ["τ", "Tractive tension; project assumption 1 Pa (Section 20)", "Pa"],
        ["Q", "Design flow, floored at 1.5 L/s, Mara's minimum design flow "
              "(Section 20)", "m³/s"],
    ])
    D.p(d, "")
    D.p(d, "At the 1.5 L/s floor the tractive-force gradient is close to the "
           "Table 11 value for DN200, so the two methods meet at the network "
           "head. If NWS sets the tension at 2 Pa rather than 1 Pa, a large "
           "share of the smallest pipes need a steeper gradient; the "
           "sensitivity is run by substituting the value, not by editing the "
           "design.")


# ================================================================== section 3
def s3_gradients(d):
    D.h(d, 1, "3  Minimum and maximum gradients", page_break=True)
    p = D.p(d, "Table 11 of the guideline gives the minimum gradient of the "
               "secondary network by diameter, computed with Colebrook-White "
               "at 0.75 m/s. The design pipeline reproduces these values from "
               "the Colebrook-White equation within 5 % before any design "
               "runs, as a check on the hydraulic code.")
    N.add(p, "G203-p29 §4.3.1 Table 11.")
    D.tab_caption(d, "Minimum gradients of the secondary network "
                     "(G203-p29 Table 11)")
    D.table(d, ["Nominal diameter (mm)", "Minimum gradient (mm/m)",
                "Minimum gradient (%)"], [
        ["200", "5.00", "0.500"], ["250", "3.75", "0.375"],
        ["315", "2.70", "0.270"], ["400", "2.05", "0.205"],
        ["500", "1.55", "0.155"], ["600", "1.25", "0.125"],
        ["700", "1.00", "0.100"], ["800", "0.85", "0.085"],
        ["900 and larger", "0.75", "0.075"],
    ], widths=[5.5, 5.5, 5.5], font=9, align_right={1, 2})

    D.p(d, "")
    D.tab_caption(d, "Rules on gradient (G203-p29 §4.3.1; G203-p18 Table 5)")
    crit(d, [
        ["Oversizing",
         "No oversizing of a pipe to obtain a flatter slope; uniform slope "
         "between chambers",
         "G203-p29", "Diameter chosen for the flow, never for the slope"],
        ["Maximum gradient",
         "Governed by the maximum velocity of 3.0 m/s",
         "G203-p29", "3.0 m/s"],
        ["Construction tolerance",
         "\"The lines and level of any pipeline shall not deviate from that "
         "described in the contract by more than 20 mm and combination of "
         "such deviation shall not create a reverse gradient.\" At DN900 and "
         "above the minimum gradient is 0.75 mm/m, so 20 mm over a 120 m "
         "spacing is about 22 % of the available fall",
         "G203-p29 §4.3.1",
         "A fall tolerance of 0.040 m, twice the 20 mm, is carried in the "
         "invert solver so a flat profile keeps its margin"],
        ["Round gradient values",
         "–", "Project decision",
         "Pipes are laid at round 0.05 % steps so the value on the drawing is "
         "the value the invert levels came from. A single pipe is rounded up; "
         "a whole run is eased down to the next round value, which leaves the "
         "far end slightly shallower and never deeper. Measured cost on the "
         "test area: 1.0 % more excavation, 0.12 m on the deepest chamber, "
         "no additional pumping station"],
        ["Tertiary slopes",
         "Property connection sewer **3 % to 10 %**; rider sewer **1 % to "
         "10 %**; lateral sewer **1 % to 10 %**. Table 11 applies to the "
         "secondary network only; its 0.5 % at DN200 is not a lateral-sewer "
         "value",
         "G203-p18 Table 5",
         "3 % minimum for property connections, 1 % for riders and lateral "
         "sewers, 10 % maximum"],
    ])


# ================================================================== section 4
def s4_pipes(d):
    D.h(d, 1, "4  Pipes", page_break=True)
    D.tab_caption(d, "Pipe diameters and materials (G203 §4.1 pages 21 to 23; "
                     "§5 page 35)")
    crit(d, [
        ["Minimum diameters",
         "Property connection OD160; lateral sewer OD200 with a maximum "
         "length of 45 m; main sewer OD200 minimum",
         "G203-p22 Table 6",
         "OD160 tertiary; DN200 minimum main; diameter series 200, 250, 315, "
         "400, 500, 600, 700, 800, 900, 1000, 1200"],
        ["Secondary network range",
         "200 to 400 mm typical; 400 mm is not a mandatory ceiling",
         "G203-p23", ""],
        ["Materials, main sewer 350 mm and larger",
         "GRP, HDPE or lined reinforced concrete in open trench; GRP or HDPE "
         "for trenchless installation",
         "G203-p22",
         "PVC-U through the OD series to 315 mm; GRP above"],
        ["PVC-U size series",
         "OD-designated series to 315 mm",
         "G203-p23 Table 7", "As guideline"],
        ["Trunk main definition",
         "Diameter over 800 mm, length over 1,000 m without connections, "
         "upstream of the treatment plant or a main pumping station",
         "G203-p35", ""],
        ["Trunk material above 600 mm",
         "GRP, lined reinforced concrete, profile-wall HDPE",
         "G203-p35 Table 14", ""],
        ["Internal bore for hydraulics",
         "Plastic mains are OD-designated, so the bore is smaller than the "
         "nominal size",
         "G203-p22 Table 6",
         "PVC-U taken as SDR34 (SN8): bore = OD × (1 − 2/34). GRP nominal "
         "size is the bore. The wall class is pending PAM-SPC-207 "
         "(Section 20)"],
        ["Crown-to-invert height",
         "–", "Project assumption",
         "Outside diameter used for the geometry, nominal for GRP; a 0.05 m "
         "allowance for wall and bedding below the crown cover"],
    ])


# ================================================================== section 5
def s5_cover(d):
    D.h(d, 1, "5  Depth, cover and corridors", page_break=True)
    D.tab_caption(d, "Cover and clearance (G203 §3.5 page 19; §4.6 pages 32 "
                     "and 33)")
    crit(d, [
        ["Minimum cover, gravity sewer",
         "\"The minimum depth for sewer pipes shall be 1.3 m to the crown\"",
         "G203-p33 §4.6.3", "1.3 m to crown"],
        ["Reduced cover",
         "\"If circumstances require installation of a pipe with depth less "
         "than 1.3 m above the crown, then concrete protection is required. "
         "The minimum cover above the pipe and its protection shall be "
         "0.5 m.\" The exception needs a stated circumstance, concrete "
         "protection, and the 0.5 m measured above the protection",
         "G203-p33 §4.6.3", "Not used"],
        ["Property connection cover", "600 mm minimum",
         "G203-p19", "0.60 m"],
        ["Maximum cover",
         "\"The recommended maximum cover for sewer pipes is approximately "
         "10 – 12 m. Depths with cover greater than this shall be "
         "investigated with pipe manufacturers … Where the cost of excavation "
         "becomes prohibitive the Engineer shall incorporate pumping stations "
         "into the design.\"",
         "G203-p33 §4.6.3",
         "**12.0 m of cover as a limit with no exception**, checked at every "
         "chamber and along the trench between chambers (Section 5.1)"],
        ["Horizontal clearance to other utilities", "3 m",
         "G203-p33", ""],
        ["Service corridor widths",
         "DN200 to 500: 2.0 m; 600 to 900: 2.8 m; 1000 to 1200: 3.2 m; "
         "1400 to 1700: 4.0 m; 1800: 4.1 m; 2000 to 2400: 4.4 m",
         "G203-p32 Table 13; p35 Table 15", ""],
        ["Position in the carriageway",
         "At least 1 m from the kerb line, stated for force mains",
         "G203-p51",
         "Applied to gravity sewers by inference; chambers at least 0.5 m "
         "from the kerb (Section 20)"],
    ])

    D.h(d, 2, "5.1  The 12 m limit")
    p = D.p(d, "The guideline makes the cost of excavation, not the depth "
               "itself, the trigger for a pumping station, and treats 10 to "
               "12 m of cover as a recommendation to be checked with pipe "
               "manufacturers. No cost analysis exists at concept stage, so "
               "the design applies 12 m of cover as a limit with no "
               "exception. Where a gravity sewer would pass 12 m, a pumping "
               "station is placed before that point, the sewage is lifted, "
               "and the sewer restarts at normal cover.")
    N.add(p, "Project decision of 7 September 2026. The limit binds nowhere "
             "on the test area, whose deepest cover is 10.45 m; it will bind "
             "when the design is extended to the whole study area, and that "
             "is where the cost question becomes real.")
    D.p(d, "The limit is revisited only when the cost analysis exists, and "
           "then for each excursion on its own economics, not as a blanket "
           "relaxation. Pumping stations are not removed by digging deeper: "
           "the route is searched again first, and whatever pumping remains "
           "is real.")


# ================================================================== section 6
def s6_chambers(d):
    D.h(d, 1, "6  Chambers", page_break=True)
    D.tab_caption(d, "Chamber criteria (G203 §4.4 pages 29 to 31)")
    crit(d, [
        ["Maximum spacing",
         "DN200 to 315: **100 m**; DN350 to 900: **120 m**; DN1000 to 1400: "
         "**150 m**; above DN1400: **200 m**. Deviation needs NWS "
         "pre-approval",
         "G203-p30 Table 12",
         "Runs split at 100 m, which satisfies every class; spacing rounded "
         "to 10 m, with 5 m as the fallback"],
        ["Locations",
         "Change of gradient or diameter, junctions, end of laterals, and at "
         "the regular spacing",
         "G203-p29", "As guideline"],
        ["Backdrop",
         "Required where the invert drop exceeds 600 mm; external; maximum "
         "height 2 m, beyond which a vortex drop shaft; internal only in a "
         "chamber of 1.5 m diameter or more",
         "G203-p30",
         "Drop trigger 0.60 m; backdrop maximum 2.0 m"],
        ["Inlet angle",
         "At least 90° to the direction of flow (\"shall\")",
         "G203-p30",
         "**85° minimum applied**; an inlet sharper than 75° is flagged for "
         "a purpose-made chamber with a curved channel and is never fixed by "
         "adding a chamber. Stated deviation, Section 21"],
        ["Minimum separation of chambers",
         "None stated in any of the three guidelines",
         "–",
         "3.0 m as a physical convention; two chambers closer than 3 m "
         "become one structure"],
        ["Chamber size",
         "\"Sufficient size\"; no table given",
         "G203 §4.4",
         "DN1000 to 3 m depth, DN1200 to 6 m, DN1500 deeper; no hydraulic "
         "effect at concept"],
        ["Prohibited locations",
         "Wadis and flood-prone or washout areas, for pipelines and chambers "
         "alike",
         "G203-p30 §4.4.1; p33",
         "Flood hazard classes 4, 5 and 6 excluded (Section 8)"],
        ["Outlets per structure",
         "–", "Project convention",
         "One physical outlet per chamber. A branch leaving a chamber that "
         "already has an outlet starts at the next house connection, or 10 m "
         "away"],
        ["Clearance from plots",
         "–", "Project decision",
         "Every chamber is checked against every plot boundary and slid "
         "clear; a corner chamber must be 2 m clear of any plot (Section 9)"],
    ])


# ================================================================== section 7
def s7_tertiary(d):
    D.h(d, 1, "7  Property connections, riders and lateral sewers",
        page_break=True)
    D.p(d, "The tertiary layer connects each property to the network. At "
           "concept stage its only hydraulic test is whether the property can "
           "drain by gravity to the sewer in its street; the pipes are not "
           "sized.")
    D.tab_caption(d, "Tertiary criteria (G203 §3, pages 17 to 22)")
    crit(d, [
        ["Property connection sewer",
         "OD160; slope 3 % to 10 %; cover 600 mm minimum; maximum length "
         "50 m",
         "G203-p22 Table 6; p18 Table 5; p19; p18 Table 4 note",
         "As guideline"],
        ["Rider sewer",
         "Slope 1 % to 10 %. \"Several HCC (usually up to 3) may be "
         "connected together by one or several Rider Sewers within the "
         "public ROW.\"",
         "G203-p18 Table 5; p19 §3.4",
         "Up to 3 house connections per rider; the rider runs along the "
         "frontage in the public right of way; a lone house connects by a "
         "lateral sewer without a rider"],
        ["Lateral sewer",
         "OD200; slope 1 % to 10 %; maximum length 45 m. Table 6 states the "
         "45 m on the lateral sewer row only, while §3.2 attaches it to "
         "rider and lateral alike",
         "G203-p22 Table 6; p17 §3.2",
         "45 m applied to riders and lateral sewers, the conservative "
         "reading, as a declared project cap"],
        ["Connection point",
         "–", "Project decision",
         "The perpendicular projection of the plot onto the corridor it "
         "fronts, never the plot centroid; the connection is a short "
         "perpendicular spur; the plot loads the reach it fronts"],
        ["Gravity viability check",
         "–", "Project assumption",
         "The house drain leaves the plot 0.60 m below plot ground and is "
         "checked against the pipe invert interpolated at the connection "
         "chainage, at a blended fall of 2 %"],
        ["Stub-outs",
         "–", "Project doctrine",
         "A capped connection at the frontage of every planned plot, sized "
         "for its saturation flow; DN200 minimum usually governs"],
        ["Output layers",
         "–", "Project decision",
         "House connections and riders sit in their own layers in every "
         "output, never in the mains layer"],
    ])


# ================================================================== section 8
def s8_wadis(d):
    D.h(d, 1, "8  Wadis, flood hazard and crossings", page_break=True)
    D.tab_caption(d, "Wadi rules (G203 pages 30, 33 and 52; G203 §11.5.3.1)")
    crit(d, [
        ["Pipelines and chambers in wadis",
         "\"Locating pipelines and associated chambers in wadis or areas "
         "subject to washout during heavy storms must be avoided.\" Page 33 "
         "repeats it as \"shall be avoided\"",
         "G203-p30 §4.4.1(a); p33",
         "The design avoids it. Where no other route exists, the presence is "
         "a recorded and justified exception carried to the deliverable, "
         "never a silent one (project decision, 7 September 2026)"],
        ["What counts as wadi ground",
         "Areas subject to washout during heavy storms",
         "G203-p30",
         "Classes 4, 5 and 6 of the 50-year flood hazard grid, which are "
         "flood-hazard classes keyed on danger to people and vehicles "
         "standing in for the washout criterion; classes 1 to 3 and cells "
         "with no value are dry. Project assumption, to be settled by a "
         "scour-depth check (Section 20)"],
        ["Cover at a wadi crossing",
         "**1.5 m to crown**, gravity sewer and force main alike. The clause "
         "opens \"As for gravitational sewer, the minimum cover should be…\" "
         "and lists 1.3 m unprotected, 0.5 m protected and 1.5 m at a wadi "
         "crossing",
         "G203-p52 §8.2.4", "1.5 m"],
        ["Reduced cover at a crossing",
         "Whether the 0.5 m protected exception is available at a wadi "
         "crossing is not stated",
         "G203-p33; p52",
         "Not available: the 1.5 m answers scour and concrete encasement "
         "answers external load. Project position, recorded as ours"],
        ["Twin pipelines at an obstacle crossing",
         "Allowed with a dedicated hydraulic justification: 0.75 m/s in all "
         "modes, mechanically independent restraint",
         "G203-p52 §8.2.3", ""],
        ["Inverted siphons",
         "\"Inverted siphons shall not be allowed.\" The scope says avoid, "
         "and only where no other feasible means exists",
         "G203-p182 §11.5.3.1(c); scope p12(60)",
         "None. Any siphon is a formal deviation needing justification"],
        ["Trenchless at major crossings",
         "An alternative subject to NWS approval; settlement is decisive",
         "G203-p21, p35",
         "Every dual-carriageway crossing is assumed trenchless (Section 9)"],
        ["Treated effluent discharge to a wadi",
         "Class A at least under MD 145/93; Environmental Authority and APSR "
         "approval",
         "G203-p73", ""],
    ])

    D.h(d, 2, "8.1  Crossing procedure")
    D.p(d, "Running along a wadi and crossing one are different questions. "
           "The general guideline sets the procedure for a crossing.")
    D.tab_caption(d, "Wadi, road and falaj crossings (G1 §9.3, pages 85 "
                     "and 86)")
    crit(d, [
        ["Data and approvals",
         "Wadi bed profiles and cross-sections, flood frequency at 1 in 20, "
         "1 in 50 and 1 in 100 years, bed material and bed-level change, "
         "from the Civil Aviation Authority and the Ministry of Agriculture, "
         "Fisheries and Water Resources; MoAFWR approval required",
         "G1-p85"],
        ["Pipe material",
         "Ductile iron over the crossing length plus 15 m each side, with "
         "mechanical or detachable joints",
         "G1-p86"],
        ["Protection",
         "NWS standard drawing PAM-STD-404; anti-flotation check with the "
         "pipe empty under flood or high groundwater",
         "G1-p86"],
        ["Cover in soft soil", "2.0 m minimum", "G1-p86"],
        ["Valves",
         "Isolation and air valves on both sides of an active or major "
         "crossing; washout at the low point on one side; no chambers or "
         "markers in the wadi bed or embankments; everything accessible "
         "during a flood",
         "G1-p86"],
        ["Road crossings",
         "Trenchless preferred; reinstatement to the Oman Highway Design "
         "Manual",
         "G1-p85"],
        ["Falaj crossings",
         "Buffer zones, protection and minimum safe excavation distances; "
         "no-objection certificates sought at the preliminary stage",
         "G1-p86; G203-p39"],
    ], adopted=False)


# ================================================================== section 9
def s9_layout(d):
    D.h(d, 1, "9  Layout rules for the network", page_break=True)
    p = D.p(d, "The guidelines fix the hydraulics and the cover. They say "
               "little about where a sewer may run through a town. The rules "
               "below were set for this project from the road data supplied "
               "and from the shape of Nama's built network, and each states "
               "its basis.")
    N.add(p, "The built network in the test area, traced through its own "
             "manhole identifiers, is one trunk main, six sub mains and 419 "
             "laterals; 91 % of laterals drain into another lateral and only "
             "about sixteen pipes touch the trunk. The built network runs "
             "along a dual carriageway on 0.1 % of its length.")
    D.tab_caption(d, "Layout rules and their basis")
    D.table(d, ["Rule", "Statement", "Basis"], [
        ["Road source",
         "Corridors come from the road centreline layer. The dual attribute "
         "decides exclusion: 1 is a dual carriageway, 2 is a two-lane pair "
         "of which one side is used. Road class serves preference only, not "
         "exclusion: 150 national and arterial roads are single "
         "carriageways",
         "Project decision, 19 August 2026"],
        ["Dual carriageways",
         "No pipe of any kind runs along a dual carriageway, the trunk "
         "included, because the carriageway cannot be opened. Both lines of "
         "the pair are removed with their links and ramps. A line within 6 m "
         "and 25° of an excluded carriageway is treated as its twin and "
         "excluded too",
         "Project decision, 19 and 20 August 2026"],
        ["Crossing a dual carriageway",
         "Only as a short perpendicular pipe: within 25° of square, no "
         "longer than 70 m, trenchless, no chamber on the carriageway. The "
         "route search is charged 2,500 m of equivalent route for every "
         "crossing, and nothing within 30 m of a known underpass, so a "
         "crossing is used only where it pays",
         "Project decision, 20 August 2026; trenchless per G1-p85"],
        ["Two-lane pairs",
         "One side only, held for the whole corridor: the side with more "
         "fronting plots, tie-broken by lower ground. Plots on the far side "
         "connect by a direct link at the road end",
         "Project decision, 19 August 2026"],
        ["Roundabouts",
         "Carry no sewer; the approach legs terminate at the ring. A ring is "
         "a roundabout only if no plot lies inside it, every node has an "
         "approach arm and the arcs are curved, with a perimeter under 150 m "
         "and an equivalent radius under 30 m",
         "Project decision, 19 August 2026"],
        ["Traffic links",
         "Turning fillets, slip roads and diagonal links between "
         "carriageways exist for vehicles; the sewer joins at a point. A "
         "link is dropped when it serves no plot within 40 m, both ends are "
         "attached, the way round is no more than three times its length, "
         "and it is short (120 m or less) or strongly curved (45° or more). "
         "Dead-ends serving no plot are removed, repeatedly",
         "Project decision, 19 and 20 August 2026"],
        ["One line per street",
         "A straight street between two intersections is one polyline; a "
         "break of less than 10° is dissolved",
         "Project decision"],
        ["Head of a run",
         "A run starts at the first house gate on the street, taken as the "
         "plot centroid dropped square onto the street and searched up to "
         "45 m, not at the street end",
         "Project decision, 20 August 2026"],
        ["Chambers at bends",
         "Up to 5°: none, the joint deflection absorbs it. 5° to 45°: one "
         "chamber at the bend. A sweeping curve over 45°: two or three "
         "chambers breaking it into chords, three only on a wide long bend. "
         "A corner chamber sits at the intersection of the tangents only if "
         "it is 2 m clear of every plot boundary; otherwise the curve is "
         "followed. The governing constraint is cleaning access, not pipe "
         "flexibility",
         "Project decision, 19 August 2026"],
        ["Hierarchy",
         "Trunk main, sub main and lateral, in Nama's as-built vocabulary; "
         "every pipe carries its tier. Each join onto the main pipe is "
         "charged 400 m of equivalent route, so only collectors reach it: "
         "20 joins on the test area, where fewer than 15 costs a pumping "
         "station and fewer than 8 starts crossing dual carriageways",
         "Learned from the built network, 23 August 2026"],
        ["Main pipe",
         "An input drawn by the engineer, not derived: both legs drain to "
         "their meeting point and on to the existing treatment plant",
         "Project input, 20 August 2026"],
        ["Pumping pockets",
         "A pocket of fewer than 50 plots is absorbed at detail design. The "
         "rules for cascading stations and for sizing a rising main on pump "
         "duty are not settled and will be decided when the design raises "
         "them",
         "Project position, 7 September 2026"],
    ], widths=[3.0, 10.0, 3.6], font=8.5)


# ================================================================= section 10
def s10_pumping(d):
    D.h(d, 1, "10  Pumping stations", page_break=True)
    D.p(d, "The test area needs no pumping station. The criteria below apply "
           "wherever the 12 m limit of Section 5.1 places one in the wider "
           "study area.")
    D.tab_caption(d, "Pumping station criteria (G203 §7, pages 38 to 49)")
    crit(d, [
        ["Siting",
         "Hydraulics-driven; flooded suction preferred; the force-main "
         "energy-economic study determines the optimal location. The site "
         "is approved in advance by NWS at concept or preliminary stage",
         "G203-p38 §7.2"],
        ["Flood protection",
         "Pump pedestal, building floor, transformers, substation and "
         "emergency generator above the maximum flood level; floors at "
         "least 300 mm above the 1 in 50 year flood level; surface and "
         "stormwater designed for a 1 in 50 year return period; sites under "
         "power lines avoided",
         "G203-p38 §7.2"],
        ["Station type",
         "Type 1 up to 100 L/s, one duty and one standby; Type 2 over 100 to "
         "300 L/s, two duty and one standby; Type 3 over 300 L/s, three duty "
         "and one standby. Pumps rotate duty each cycle; station pipework "
         "0.6 to 2.5 m/s (0.5 m/s with a grinder); motor speed at most "
         "1,450 rpm above 5 L/s and 2,800 rpm at or below; solids passage "
         "76 mm minimum, 65 mm with an upstream basket",
         "G203-p40 to 41 Table 17"],
        ["Small stations",
         "At least two identical pumps, duty and standby, each at 100 % of "
         "design flow; peak flow achievable with any one unit out",
         "G203-p39"],
        ["Land area",
         "Type 1: 50 to 100 m²; Type 2: 200 to 400 m²; Type 3: 900 m² or "
         "more; access with a turning circle at least 6 m wide and hard "
         "standing",
         "G203-p43 Table 21"],
        ["Design life",
         "Non-structural mechanical installations 20 years; Table 17 rates "
         "pumps at 15 years, which is the figure for pump replacement in the "
         "life-cycle cost",
         "G203-p38; p40 Table 17"],
        ["Minimum-flow factors",
         "Initial minimum flow = average flow × factor: 50 L/s → 0.25; "
         "500 L/s → 0.35; 2,500 L/s → 0.45; 5,000 L/s → 0.50. This flow, not "
         "the average, sizes the force main against deposition",
         "G203-p40 §7.4 Table 16"],
        ["Emergency overflow",
         "Every pumping station shall have one, with Environmental Authority "
         "approval; never at an upstream manhole; wet-well overflow with dip "
         "tube or baffle; storage above the start level of the last duty "
         "pump. Prevention by dual power supply, trunk or basin storage, "
         "emergency storage and emergency pumping",
         "G203-p46 to 47 §7.5"],
        ["Wet-well volume",
         "Minimum live volume per Equation 2, with successive start and stop "
         "levels 200 to 300 mm apart, a 5 to 10 s start delay, and CFD plus "
         "physical modelling for stations of 0.5 m³/s or more",
         "G203-p48 §7.8"],
        ["Net positive suction head",
         "Equation 3, with a margin of at least 1 m",
         "G203-p47 §7.6"],
        ["Hydrogen sulphide at the force-main outlet",
         "Where H₂S is expected and no field data exists, design for "
         "management and monitoring at 50 to 100 ppm average and 200 ppm "
         "peak at the pressure-main termination; monitoring at the "
         "termination manhole controls chemical injection at the force-main "
         "start",
         "G203-p47 §7.7; p55 §8.5"],
        ["Stakeholder approvals",
         "No-objection certificates, including falaj crossings, sought at "
         "the preliminary stage",
         "G203-p39"],
    ], adopted=False)

    D.p(d, "")
    n6 = D.next_eq()
    eq(d, M.seq(M.r("V"), M.EQ, M.r("0.25"), M.CDOT, M.r("Q"),
                       M.CDOT, M.r("T")), number=n6)
    params(d, [
        ["V", "Minimum live volume of the wet well", "m³"],
        ["Q", "Capacity of a single pump", "m³/s"],
        ["T", "Cycle time, 3600 divided by the starts per hour; at least 10 "
              "starts per hour for motors up to 30 kW", "s"],
    ])
    D.p(d, "")
    n7 = D.next_eq()
    eq(d, M.seq(M.sub(M.up("NPSH"), M.up("a")), M.EQ,
                       M.sub(M.r("H"), M.up("a")), M.MINUS,
                       M.sub(M.r("H"), M.up("vpa")), M.MINUS,
                       M.sub(M.r("H"), M.up("st")), M.MINUS,
                       M.sub(M.r("H"), M.up("f"))), number=n7)
    params(d, [
        ["NPSHa", "Net positive suction head available; margin of at least "
                  "1 m over the pump's requirement", "m"],
        ["Ha", "Atmospheric pressure head", "m"],
        ["Hvpa", "Vapour pressure head of the liquid", "m"],
        ["Hst", "Static suction lift", "m"],
        ["Hf", "Friction loss in the suction pipework", "m"],
    ])


# ================================================================= section 11
def s11_force_mains(d):
    D.h(d, 1, "11  Force mains", page_break=True)
    D.tab_caption(d, "Force main criteria (G203 §8, pages 50 to 55; G1 "
                     "Appendix III)")
    crit(d, [
        ["Minimum velocity",
         "0.75 m/s continuous, maintained at the design minimum flow of "
         "Table 16 under maximum static head; 1.0 m/s intermittent; 1.2 m/s "
         "in vertical pipework",
         "G203-p50 §8.1; p40 Table 16"],
        ["Maximum velocity", "2.5 m/s", "G203-p50"],
        ["Minimum diameter",
         "75 mm bore for non-clog pumps; 50 mm bore for grinder pumps",
         "G203-p50 §8.1"],
        ["Gradients",
         "At least 1 in 500 rising and 1 in 300 falling; never flatter than "
         "1 in 750",
         "G203-p50 §8.2.1"],
        ["Run full",
         "Designed to run full and remain full at all times",
         "G203-p51 §8.2.1"],
        ["Retention time",
         "Ideally 30 minutes or less; air valves at high points and washouts "
         "at low points",
         "G203-p50"],
        ["Access", "Every 500 m", "G203-p50"],
        ["Valve spacing",
         "In-line isolation valves at about 500 m and never more than "
         "800 m; washout valves at low points sized to empty a section in "
         "3 to 4 hours (main up to 400 mm: 100 mm; 500 to 800 mm: 150 mm; "
         "900 to 1,200 mm: 200 mm; 1,200 mm and larger: 300 mm); "
         "double-orifice air valves at high points with the approach no "
         "flatter than 1 in 500 and the departure no flatter than 1 in 300, "
         "each with its own geared isolation valve",
         "G203-p53 to 54 §8.4"],
        ["Separation from water mains",
         "3.0 m horizontal; crosses under the water main with 450 mm "
         "vertical clearance outside to outside; one full length of water "
         "pipe centred so both joints are as far from the force main as "
         "possible; structural support where required",
         "G203-p51 §8.2.2"],
        ["Layout",
         "Straight lines, sharp bends avoided, at least 1 m from the kerb "
         "line in a carriageway",
         "G203-p51"],
        ["Material, in the station",
         "Ductile iron recommended; stainless steel for stations under "
         "100 L/s",
         "G203-p52 §8.3"],
        ["Material, pressure main",
         "\"The recommended pipe material for the pressure main is Ductile "
         "Iron and HDPE\"",
         "G203-p53 §8.3"],
        ["Termination",
         "Discharge to the gravity system at a manhole, entering not more "
         "than 300 mm above the receiving flow line; water seal and forced "
         "venting through odour control where turbulent; corrosion-resistant "
         "or lined receiving manhole",
         "G203-p55 §8.5"],
        ["Surge analysis",
         "Transient analysis in NWS-approved software; simultaneous pump "
         "start and stop modelled to N+1; no vapour cavities or column "
         "separation; minimum pressure not below the manufacturer's limit or "
         "0.2 bar below atmospheric, whichever is higher; maximum not above "
         "the test pressure or the lowest component rating; a zero-roughness "
         "run first for the worst case",
         "G1-p146 to 147 Appendix III"],
    ], adopted=False)


# ================================================================= section 12
def s12_flows(d):
    D.h(d, 1, "12  Flow estimation", page_break=True)

    # ---- 12.1
    D.h(d, 2, "12.1  Two methods in the guideline, and which one governs")
    D.p(d, "The general guideline gives two methods for almost every demand "
           "and flow parameter. The first is for planning and forecasting "
           "across broad service areas. The second is written as a "
           "requirement wherever detailed land-use information exists.")
    D.table(d, ["Tier", "Applies when", "Method"], [
        ["A, planning and forecasting",
         "Broad service areas without land-use detail",
         "G1 Table 11 consumption per head with the distributed ratios of "
         "22 % and 14 %; G1 Table 19 return rates of 85 % and 54 %"],
        ["B, project-specific design",
         "\"where detailed land use information is available\"",
         "G1 Table 12 unit rates for non-domestic and governmental demand; "
         "design flows to BS EN 752 or a stated equivalent, supported by "
         "site-specific evidence"],
    ], widths=[3.8, 5.0, 7.8], font=9)
    p = D.p(d, "Three clauses carry the requirement. Non-domestic consumption "
               "\"shall be calculated using the reference values presented in "
               "the Table 12\" where the project provides detailed land use. "
               "Governmental consumption \"is to be calculated specifically "
               "for the project and not as a ratio of domestic consumption\". "
               "Design flows for project-specific designs \"shall be "
               "calculated in accordance with a relevant international "
               "standard such as BS EN 752\", and \"calculations shall clearly "
               "state which standard has been used\".")
    N.add(p, "G1-p60 §7.3.2; G1-p61 §7.3.3; G1-p71 §7.4.1. Table 19 describes "
             "its own figures as \"baseline figures [that] provide a general "
             "framework for planning and forecasting purposes across broader "
             "service areas\" (G1-p70).")
    D.p(d, "Every value from the planning tier that appears in a deliverable "
           "is labelled as a fallback pending the project-specific data, with "
           "the data request named. Section 12.3 records the load basis "
           "adopted and the reason the G1 Table 12 method cannot yet be "
           "applied.")

    # ---- 12.2
    D.h(d, 2, "12.2  Population and occupancy")
    D.tab_caption(d, "Population criteria (G1 §7.2, pages 58 and 59)")
    crit(d, [
        ["Official source",
         "NCSI population and housing data at governorate, wilayat and "
         "settlement level",
         "G1-p58 §7.2.1", "NCSI series carried in the Inception Report"],
        ["Wilayat to settlement",
         "Where forecasts exist only at wilayat level, distribution must "
         "follow the latest census settlement shares",
         "G1-p58", "As guideline"],
        ["Below settlement level",
         "Pro rata to the number of electricity accounts, supplied by NWS",
         "G1-p58", "33,970 electricity accounts, each counted as a property"],
        ["Extrapolation limit",
         "NCSI forecasts cover 20 to 25 years. Beyond them a polynomial "
         "regression, but \"it is not recommended to extrapolate more than "
         "ten years beyond the available forecast period\"",
         "G1-p58",
         "The 2055 and ultimate cases are defended on land capacity, not on "
         "the extrapolated curve"],
        ["Population from plots",
         "Equation 4. Occupancy rate = population ÷ housing units from NCSI, "
         "most recent data, at the geographic scale of the project",
         "G1-p58 to 59 §7.2.2",
         "Properties per plot counted from electricity accounts, 1.46 "
         "domestic per matched plot; additional-account entries are separate "
         "dwellings"],
        ["Occupancy rate",
         "Population ÷ housing units", "G1-p58",
         "**Project basis 5.32** people per domestic property, measured as "
         "2024 settlement population ÷ counted domestic properties over the "
         "same 25 settlements. **The W13 test-area run carries 5.0**, the "
         "value inherited from the design it was copied from; the full-area "
         "run is to apply 5.32 (Section 20)"],
        ["Build-out",
         "\"special care must be given in cases of plot subdivision … "
         "development speed must be considered through appropriate phasing "
         "assumptions … development percentages must be applied over the "
         "design period … particularly avoiding overestimation\"",
         "G1-p59 note",
         "Pipes and civil works sized on every plot at saturation; dated "
         "years use zone totals capped at the zone ceiling (Section 12.3)"],
    ])
    D.p(d, "")
    n2 = D.next_eq()
    eq(d, M.seq(M.up("Population"), M.EQ, M.sub(M.r("N"), M.up("plots")),
                       M.TIMES, M.sub(M.r("n"), M.up("prop")), M.TIMES,
                       M.up("OR")), number=n2)
    params(d, [
        ["Nplots", "Number of plots in the area", "–"],
        ["nprop", "Average properties per plot; counted from electricity "
                  "accounts, 1.0 only as the fallback for a plot with no "
                  "account", "–"],
        ["OR", "Occupancy rate, people per property", "–"],
    ])
    p = D.p(d, "The occupancy rate departs from the guideline's definition in "
               "one respect. Housing units are not published at settlement "
               "level, so properties counted from electricity accounts stand "
               "in for them. The figure was validated by coverage: the 25 "
               "settlements hold 63.4 % of the wilayat population, and at "
               "5.32 the wilayat implies 34,504 domestic properties against "
               "22,588 held, which is 65.5 %. The two agree within 2.0 "
               "points, so 5.32 is a measurement rather than a coverage "
               "artefact. It is listed as a deviation in Section 21.")
    N.add(p, "Ibri town alone measures 6.21. Five settlements are unusable "
             "pending boundary review: Sayh Al Masarrat, Al Jahli, Al "
             "Akheedar, Satwah and Al Qali. The figure is recomputed when the "
             "clean plot layer arrives.")

    # ---- 12.3
    D.h(d, 2, "12.3  The load basis")
    D.p(d, "The load basis was fixed on 30 August 2026 and is applied without "
           "variation. The planning-tier ratios set the volume; land use sets "
           "where that volume is placed. The two do not overlap, so the "
           "method neither mixes tiers nor double counts.")
    D.numbered(d, "Domestic load = counted domestic accounts × occupancy rate "
                  "× consumption per head × return rate.", restart=True)
    D.numbered(d, "Non-domestic and governmental volume = 22 % and 14 % of the "
                  "domestic volume, the distributed ratios for Adh Dhahirah "
                  "(G1-p60 Table 11).")
    D.numbered(d, "That volume is placed on the commercial and government "
                  "plots identified by account tariff. It is not spread across "
                  "the population, so a residential-only branch carries no "
                  "commercial flow.")
    D.numbered(d, "G1 Table 12 is not applied. It is priced in pupils, beds, "
                  "employees and floor area, and none of these have been "
                  "supplied, so the condition in §7.3.2 is unmet in substance. "
                  "It is adopted the day real quantities arrive, and never "
                  "together with the ratios.")
    p = D.p(d, "Four streams sit outside the ratios and are added separately, "
               "because the guideline excludes them by name: identified "
               "projects such as the industrial estate, special consumption "
               "such as labour camps, potable and sewage tankers, and private "
               "wells and other non-network abstraction. Tanker water "
               "generates sewage at the same 85 % return rate as domestic "
               "supply.")
    N.add(p, "G1-p59 §7.3.1: the ratios \"do not apply to the water "
             "consumption of specific identified non-domestic projects such "
             "as economic zones\". G1-p61 §7.3.4: special consumption \"must "
             "be provided by the developer … These needs are not covered by "
             "population forecasts\". G1-p70 §7.4 and §7.4.1: other water "
             "sources, binding. G1-p71 Table 19: tanker return rate.")

    D.tab_caption(d, "Rules within the load basis")
    D.table(d, ["Rule", "Statement", "Basis"], [
        ["Where the load goes",
         "Every plot, built, planned and unparceled buildings alike, carries "
         "its full saturation load in the pipe and civil design, accumulated "
         "with the peak factor and with no timing. Dated years use zone "
         "totals only: the projection capped at the zone ceiling, with the "
         "surplus spilled to adjacent zones in proportion to their vacancy. "
         "The two meet only at trunk nodes",
         "Project doctrine, 15 August 2026"],
        ["Phased elements",
         "Treatment trains, pumps and force-main duty equipment are phased "
         "on the dated years; buried civil works are built for saturation",
         "Project doctrine"],
        ["Agricultural plots",
         "An agricultural meter is an irrigation pump and generates no "
         "wastewater. On 172 of 319 agricultural plots Nama bills a "
         "household tariff alongside the farm tariff, so dwelling and pump "
         "are metered separately. An agricultural meter on a plot that "
         "already carries a domestic meter adds nothing; an agricultural-only "
         "plot carries no dwelling",
         "Project decision, 30 August 2026, from the account data"],
        ["Cost-reflective tariff accounts",
         "499 accounts on the cost-reflective tariff are a consumption class, "
         "not a land use. They are the largest consumers and cannot be "
         "classified by tariff alone; they are resolved against the plot "
         "layer or by site check before any ratio is applied",
         "Open item"],
        ["Direction of accuracy",
         "One population figure cannot serve every use. Pipe sizing and "
         "plant staging fail on an under-estimate. Self-cleansing and the "
         "early cleansing schedule fail on an over-estimate: a pipe assumed "
         "to scour itself while it silts. Capacity is sized on the high "
         "case, the cleansing schedule on the low case, and the connection "
         "ratio of 0.51 in 2024 rising to 0.61 by 2028 is carried "
         "explicitly",
         "G1-p72 §7.4.4 and the Inception Report"],
    ], widths=[3.2, 9.8, 3.6], font=8.5)

    # ---- 12.4
    D.h(d, 2, "12.4  Water demand")
    D.tab_caption(d, "Water demand criteria (G1 §7.3, pages 59 to 62)")
    crit(d, [
        ["Domestic consumption, Adh Dhahirah",
         "**164 L per head per day**. Table 11 values are \"indicative "
         "figures derived from the recent Integrated Master Plan (2024)\", "
         "apply \"in absence of any updated figures\", and \"should be "
         "validated by NWS as essential design criteria, before designing "
         "the project\"",
         "G1-p59 to 60 Table 11", "164 L/head/day"],
        ["What the figure measures",
         "Network-accounted domestic water ÷ (occupancy × active domestic "
         "accounts). Tanker and private-well supply are not in it",
         "G1-p60", "Tanker supply added separately (Section 12.5)"],
        ["Non-domestic, project-specific method",
         "G1 Table 12 unit rates: education 130 L/day per pupil and staff; "
         "hospitals 650 L/day per bed and staff; shopping 12.2 L/day per m²; "
         "hotels 200 to 500 L per guest per day; offices 93 L/day per "
         "employee; restaurants 7.4 L/day per m²; mosques 185 L/day per m²; "
         "dry industry 93 L/day per employee; army camps 185 L/day per "
         "occupant; prisons 185 L/day per prisoner and staff; wet industry "
         "not applicable, the developer supplies it",
         "G1-p61 Table 12",
         "Not applied until the quantities are supplied (Section 12.3)"],
        ["G1 Table 12 unit basis",
         "Keyed to floor area, pupils, beds and employees, never to plot "
         "area. Applied to cadastral plot area the mosque rate alone gives "
         "about four times the whole ultimate plant flow",
         "G1-p61", "Plot area is never substituted"],
        ["G1 Table 12 deviations",
         "\"The designer can provide additional details per category or data "
         "for his design and shall substantiate the use of an alternative "
         "value\"",
         "G1-p61 note", ""],
        ["Non-domestic, planning method",
         "22 % of domestic consumption; the column is headed \"Distributed "
         "Non-Domestic Ratio (% LPCD)\", a governorate water-balance volume "
         "spread over population. The ratio can be updated by the NWS "
         "planning department",
         "G1-p60 §7.3.2", "22 %, as the volume in Section 12.3"],
        ["Governmental",
         "Project-specific: \"not as a ratio of domestic consumption\". "
         "Planning fallback 14 %",
         "G1-p60 to 61 §7.3.3", "14 %, as the volume in Section 12.3"],
        ["Special consumption",
         "Labour camps and high-water industry must be provided by the "
         "developer; not covered by population forecasts",
         "G1-p61 §7.3.4", "Additive, outside the ratios"],
        ["Potable tanker demand",
         "Where a tanker filling station is in or near the project area its "
         "consumption must be assessed from NWS filling-station data and "
         "added. Table 13: Adh Dhahirah 5,145 m³/day in 2021 to 2023, which "
         "is 333 % of the 2023 network domestic consumption, the highest in "
         "Oman. The master plan holds tanker demand constant",
         "G1-p61 to 62 §7.3.5 Table 13", "Tier 1 data request"],
        ["Double counting",
         "G1 Table 12 or the ratios, never both",
         "G1-p60 to 61", "Ratios only, until G1 Table 12 quantities arrive"],
    ])

    # ---- 12.5
    D.h(d, 2, "12.5  Wastewater generation")
    D.tab_caption(d, "Wastewater generation (G1 §7.4, pages 70 and 71)")
    crit(d, [
        ["Return rate",
         "Table 19: domestic and tanker **85 %**; non-domestic, government "
         "and commercial, **54 %**",
         "G1-p70 to 71 §7.4.1", "0.85 domestic"],
        ["Project-specific design flows",
         "To BS EN 752 or an equivalent standard, stated in the "
         "calculations, supported by site-specific evidence; the British "
         "Water Code of Practice for Flows and Loads is named as a guide",
         "G1-p71 §7.4.1", ""],
        ["Other water sources",
         "\"the Designer shall carry out an assessment of other potential "
         "water sources within the project area, such as private wells, "
         "private water providers, or other non-network abstractions\"; "
         "\"A specific attention is to be taken for catchments covered with "
         "private wells\"",
         "G1-p70 §7.4, §7.4.1",
         "Tier 1 data request; with tanker water at 333 % of network "
         "consumption the network demand alone under-predicts the load"],
        ["Components",
         "Domestic, non-domestic, tanker discharges and special facilities",
         "G1-p70 §7.4", "As guideline"],
    ])

    # ---- 12.6
    D.h(d, 2, "12.6  Peak factors, infiltration and tankers")
    D.tab_caption(d, "Peaking and allowances (G1 §7.4.2 to §7.4.5, pages 71 "
                     "to 73)")
    crit(d, [
        ["Peak factor, primary",
         "Merrimack, Equation 5, \"is to be used\" for a catchment \"having "
         "over 100 properties\"; peak factor = Qpdf ÷ Qadf",
         "G1-p71 §7.4.2",
         "Merrimack above 100 properties; below 100 the guideline gives no "
         "formula and the 100-property factor is held"],
        ["Peak factor, alternative",
         "Peltier, Equation 6, \"the Average Daily Flow in this formula is "
         "in liters per second\"",
         "G1-p72", "Reported as a comparison; no decision rests on it"],
        ["Peak factor cap",
         "\"It is recommended that the hourly peak factor should not exceed "
         "5.0\", a recommendation rather than a limit",
         "G1-p72 note",
         "Reported above 5.0, never truncated"],
        ["Infiltration",
         "New networks **720 L/day per km of sewer**; existing inland "
         "networks 10 % of the wastewater flow; existing networks in "
         "groundwater or coastal zones up to 40 %. \"Infiltration due to "
         "storm water is not considered.\"",
         "G1-p72 §7.4.3",
         "720 L/day/km assigned to each pipe by length, without a diurnal "
         "pattern; the order of peaking and infiltration is to be confirmed "
         "with NWS (Section 20)"],
        ["Infiltration exemption",
         "\"Tanker or vacuum collection do not require to account for "
         "infiltration volume\"",
         "G1-p73", "Tanker flow carries none"],
        ["Sewage tankers",
         "\"In 2024, the yellow tanker represented approximately 17 % of the "
         "total flow reaching the STPs of Nama WS\", a company-wide "
         "observation. Collection capacity assumes the same coverage as the "
         "water supply, reaching 100 % by the end of the planning period; "
         "self-cleansing checked at initial operation. Tanker loads are "
         "higher than network effluent",
         "G1-p73 §7.4.4",
         "17 % is not used as a design allowance; the tanker stream is "
         "assessed from filling-station data"],
        ["Treatment plant margin",
         "10 % \"when designing new STPs\", applied \"over and above any "
         "redundancies in the design\"",
         "G1-p73 §7.4.5; G203-p65 Table 29", ""],
    ])
    D.p(d, "")
    n4 = D.next_eq()
    eq(d, M.seq(M.sub(M.r("Q"), M.up("pdf")), M.EQ, M.r("2.65"),
                       M.CDOT, M.sup(M.sub(M.r("Q"), M.up("adf")),
                                     M.r("0.879"))), number=n4)
    params(d, [
        ["Qpdf", "Peak daily flow", "ML/day"],
        ["Qadf", "Average daily flow", "ML/day"],
    ])
    D.p(d, "")
    n5 = D.next_eq()
    eq(d, M.seq(M.sub(M.up("PF"), M.up("WW")), M.EQ, M.r("1.5"),
                       M.PLUS, M.frac(M.r("1"), M.sqrt(M.sub(M.r("Q"),
                                                              M.up("m"))))),
              number=n5)
    params(d, [
        ["PFWW", "Wastewater peak factor, Peltier form from the 2024 "
                 "Integrated Master Plan", "–"],
        ["Qm", "Average daily flow", "L/s"],
    ])

    # ---- 12.7
    D.h(d, 2, "12.7  Values applied in the W13 pipeline")
    D.p(d, "The pipeline sizes every pipe on the saturation load of the plots "
           "that drain to it. The per-plot flow is Equation 7.")
    n3 = D.next_eq()
    eq(d, M.seq(M.sub(M.r("Q"), M.up("adf,plot")), M.EQ,
                       M.frac(M.seq(M.up("OR"), M.TIMES,
                                    M.sub(M.r("n"), M.up("prop")), M.TIMES,
                                    M.sub(M.r("q"), M.up("ww"))),
                              M.r("1000"))), number=n3)
    params(d, [
        ["Qadf,plot", "Average dry-weather flow of one plot at saturation",
         "m³/day"],
        ["OR", "Occupancy rate, people per property", "–"],
        ["nprop", "Properties on the plot, counted from electricity accounts",
         "–"],
        ["qww", "Wastewater generated per head per day", "L/head/day"],
    ])
    D.p(d, "")
    D.tab_caption(d, "Flow values carried by the W13 pipeline")
    D.table(d, ["Quantity", "Value", "Source"], [
        ["Domestic water consumption", "164 L/head/day",
         "G1-p59 to 60 Table 11"],
        ["Domestic return rate", "0.85", "G1-p70 to 71 Table 19"],
        ["Wastewater per head, area average", "171.3 L/head/day",
         "164 × 0.85 with the 22 % and 14 % uplifts; a residential-only "
         "branch generates 139.4 L/head/day"],
        ["Occupancy rate in the test-area run", "5.0",
         "Inherited value; project basis is 5.32 (Section 12.2)"],
        ["Properties per plot", "Counted from 33,970 electricity accounts; "
                                "1.0 only where a plot has no account",
         "Project data, 19 August 2026"],
        ["Infiltration", "720 L/day per km, unpeaked", "G1-p72 §7.4.3"],
        ["Peak factor", "Merrimack; held at the 100-property value below 100 "
                        "properties", "G1-p71 §7.4.2"],
        ["Peak factor above 5.0", "Reported, never truncated",
         "G1-p72 note"],
        ["Test-area result", "Qadf 3,620 m³/day; peak 96 L/s",
         "W13 pipeline, 7 September 2026"],
    ], widths=[5.0, 5.0, 6.6], font=9)


# ================================================================= section 13
def s13_life(d):
    D.h(d, 1, "13  Design life, horizons and climate", page_break=True)
    D.tab_caption(d, "Design life and horizons (G1 §7.1 and §7.5; scope)")
    crit(d, [
        ["Planning life",
         "**25 years**, which \"corresponds both to the ultimate design "
         "capacity of the project, as well as the period over which the NPV "
         "will be calculated for … comparing schemes\"",
         "G1-p57 §7.1"],
        ["Asset lifetimes",
         "Civil and structures 50 years; mechanical 20; electrical 15 to 50; "
         "instrumentation, control and automation 15; pipework 50. \"These "
         "asset lifetimes are used for financial asset depreciation "
         "calculations\"; technical life may differ",
         "G1-p57 Table 10"],
        ["Scope horizon",
         "Completion plus 25 years, or ultimate saturation; model years "
         "start, 2030, 2055 and ultimate; projections at five-year "
         "intervals",
         "Scope p3, p14 to 15"],
        ["Saturation",
         "No more developable plots. Zone ceilings bite inside the design "
         "horizon; the whole boundary saturates around 2062 to 2070",
         "Project doctrine"],
        ["Climatic design, inland",
         "Peak shade temperature 55 °C; maximum daily average 50 °C; maximum "
         "yearly average 35 °C; metal in sun 85 °C; relative humidity to "
         "100 %. \"All equipment shall be rated for continuous operation "
         "under [these] ambient conditions … and performance guarantees "
         "shall be given at these conditions\"",
         "G1-p78 to 79 §7.5 Table 24"],
        ["Climate resilience",
         "Assessed at a 50-year horizon even where the asset life is "
         "shorter, with an NWS-agreed climate model at both +2 °C and +4 °C "
         "scenarios, including changed flood frequency and intensity in site "
         "selection",
         "G1-p33 §4.4"],
    ], adopted=False)


# ================================================================= section 14
def s14_tse(d):
    D.h(d, 1, "14  Treated effluent", page_break=True)
    D.tab_caption(d, "Treated effluent criteria (G1 §7.4.6 and §7.4.7, pages "
                     "73 to 78)")
    crit(d, [
        ["Production ratio", "95 % of the plant inflow", "G1-p73"],
        ["Network loss",
         "\"For design purposes, a system loss of 10 percent of all produced "
         "TSE shall be assumed\", so the deliverable volume is about 85.5 % "
         "of the plant inflow, not 95 %",
         "G1-p76 §7.4.6.3(b)"],
        ["Sizing basis",
         "\"The TSE system shall be sized to accommodate the peak demand "
         "experienced during the summer months.\" Seasonal factors as a "
         "share of summer: December to February 50 %; March to May and "
         "September to November 75 %; June to August 100 %",
         "G1-p76 §7.4.6.4 Table 23"],
        ["Irrigation rates",
         "Summer planting rates: shrubs 20 to 40, palms 120 to 165, other "
         "trees 40 to 80 L per plant per day; hedges 10 L per m per day; "
         "ground cover and seasonal flowers 10 and grass 12 L per m² per "
         "day; densities of 15 m for trees and 3 m for shrubs. Roads and "
         "junctions with mixed vegetation and no data: 10 L per m² per day, "
         "subject to Municipality approval",
         "G1-p73 to 75 §7.4.6.2 Tables 21 and 22"],
        ["Large consumers",
         "\"Any consumer with an average daily demand larger than 500 m³/day "
         "is to be studied individually\", with an irrigation pattern "
         "reflecting its actual settings; consumers with storage spread "
         "their demand over the storage hours",
         "G1-p76 §7.4.6.4"],
        ["Sludge production",
         "0.25 kg per m³ treated, a master-plan baseline described as \"a "
         "general guideline\" and process-dependent",
         "G1-p78 §7.4.7"],
    ], adopted=False)


# ================================================================= section 15
def s15_stp(d):
    D.h(d, 1, "15  Sewage treatment plant", page_break=True)
    D.tab_caption(d, "Treatment plant criteria (G203 §10, pages 63 to 74; "
                     "G1 §4 and §6)")
    crit(d, [
        ["Size category",
         "Small under 500; medium 500 to 20,000; large 20,000 m³/day and "
         "above. The ultimate Ibri flow places the plant in the large "
         "category",
         "G203-p65"],
        ["Design horizon", "At least 15 years, projected population plus "
                           "industrial load", "G203-p65"],
        ["Capacity basis",
         "Average per-head consumption per the latest NWS Integrated Master "
         "Plan; a more realistic figure only as an NWS-accepted, "
         "designer-justified exception",
         "G203-p65 §10.2.2.1"],
        ["Site selection",
         "Table 27: accessibility, land and phasing, winds, geology and "
         "hydrology, topography to limit pumping, groundwater and flood "
         "protection at the 25 and 100 year levels, buffer from residential "
         "areas, life-cycle cost",
         "G203-p63 to 64"],
        ["Flood criteria", "25 and 100 year flood levels; the plant fully "
                           "operational during floods", "G203-p63 Table 27(i)"],
        ["Land footprint",
         "Per m³/day: MBR 0.45 to 0.9 m²; MBBR 0.9 to 1.8; SBR 0.9 to 1.8; "
         "IFAS 1.2 to 2.5; conventional and extended aeration 1.8 to 3.6; "
         "constructed wetland over 10 m²",
         "G203-p64 Table 28"],
        ["Built footprint",
         "Total footprint of all structures at most 35 % of the allocated "
         "land; boundary setbacks at least 5 m",
         "G1-p50 §6.4.2"],
        ["Buffer zones",
         "Small and medium plants 500 m to residential and industrial; "
         "large plants 300 to 1,000 m from odour modelling on the 5 odour "
         "unit contour; small plants under 150 population equivalent 10 to "
         "30 m; sewage pumping stations 30 m residential and 20 m "
         "industrial. Subject to NWS approval and the environmental and "
         "social impact assessment",
         "G1-p43 to 44 §6.1.3.3 Table 8"],
        ["Incoming flow",
         "Average sewage flow plus infiltration plus a 10 % operational "
         "allowance. Hydraulic pass-through sized on the peak hourly flow; "
         "biology on the annual average flow and load. \"The hydraulic and "
         "load design shall include recycled liquors and the received tanker "
         "volumes if applicable\"; a design peak instantaneous flow is also "
         "defined",
         "G203-p65 to 66 Table 29, §10.2.2.1"],
        ["Process lines",
         "\"Treatment plants shall be designed using several process lines "
         "allowing additional capacity for different design horizons or "
         "phases\"",
         "G1-p53 §6.6.2"],
        ["Redundancy",
         "Modular N+1 at site level: N elements meet average-day flows, N+1 "
         "meets peak capacity",
         "G1-p33 §4.3"],
        ["Organic load",
         "At least 60 g BOD₅ and 80 g TSS per head per day unless "
         "justified; COD to BOD 1.8 to 2.2 for domestic sewage",
         "G203-p74"],
        ["Existing works",
         "For the upgrade or expansion of an existing plant the organic "
         "design rests on the measured strength from the client's "
         "laboratory records, with a growth increment",
         "G203-p74 §10.3.1"],
        ["Raw sewage characteristics",
         "Primarily from NWS laboratory data for the catchment. Table 30 "
         "defaults, usable only by NWS agreement: BOD₅ 350 to 400, COD 700 "
         "to 900, TSS 400 to 500, TKN 60 to 80, ammonia nitrogen 40 to 50, "
         "total phosphorus 10 to 15 mg/L, 20 to 35 °C. Table 31 tanker "
         "sewage: BOD 350 to 1,050, COD 1,350 to 5,000, TSS 900 to 4,300 "
         "mg/L",
         "G203-p67 Table 30; p68 Table 31"],
        ["High-strength influent",
         "Above a COD to BOD ratio of 2.2 the influent is \"not effectively "
         "biologically treatable\" and a separate treatment line is required "
         "where the volume is significant; the tanker stream triggers this",
         "G203-p74 §10.3.1"],
        ["Organic peak factors",
         "BOD and COD 1.5 for a small plant and 1.2 for medium and large; "
         "TKN 2.0 and 1.5; equalisation considered where surge loads are "
         "critical",
         "G203-p74 §10.3.1"],
        ["Tanker reception",
         "A dedicated tanker discharge station with screening and oil and "
         "grease removal; a flow-equalisation tank specifically for tanker "
         "discharge; the 48 to 72 hour emergency lagoon where NWS requires "
         "it; pre-acceptance sampling, procedures, traceability and "
         "contractual limits. Pre-treatment selected for tanker and "
         "non-domestic sewage",
         "G203-p73 §10.3.1; G1-p55 §6.8"],
        ["Emergency lagoon",
         "48 to 72 hours of plant capacity \"in specific cases, under NWS "
         "requirement and approval\", for holding problematic influent or "
         "effluent and returning it to the inlet works; distinct from the "
         "scope's five-day storage lagoons",
         "G203-p73; scope p13(61)"],
        ["Effluent quality",
         "\"At least Class A\" under MD 145/93 for wadi discharge, subject "
         "to prior agreement with NWS and to Environmental Authority and "
         "APSR approval. The MD 159/2005 nitrogen and phosphorus limits "
         "apply only \"if the Wadi discharges to sea at a reasonable "
         "distance\"; Ibri's wadis are inland",
         "G203-p72 to 73 §10.2.4.3"],
        ["Nitrogen and chlorine",
         "Total nitrogen below 15 mg/L as N; chlorine residual at the plant "
         "outlet 0.3 to 1.0 mg/L, up to 3.0 mg/L permitted to allow decay "
         "along the treated effluent network",
         "G203-p71 §10.2.4.1"],
        ["Nature-based treatment",
         "Constructed wetlands are limited to works of about 500 m³/day",
         "G203-p101"],
    ], adopted=False)


# ================================================================= section 16
def s16_g202(d):
    D.h(d, 1, "16  Water and treated effluent networks", page_break=True)
    D.tab_caption(d, "Network criteria from the water and TSE guideline "
                     "(G2 §7 and §9)")
    crit(d, [
        ["Transmission velocity",
         "1.0 m/s or more and below 2.0 m/s; 1.5 m/s is the common practical "
         "peak over a 25-year horizon",
         "G2-p103 to 104"],
        ["Head loss equations",
         "Darcy-Weisbach for large pipes and high velocity, Hazen-Williams "
         "for small diameters; any other needs NWS hydraulic team approval",
         "G2-p104"],
        ["Roughness with age",
         "Ductile iron C 140 falling to 120 and ε 0.26 rising to 0.45 mm "
         "over 20 years; GRP C 150, ε 0.005 mm; HDPE C 150, ε 0.007 mm; PVC "
         "C 150, ε 0.0015 mm",
         "G2-p104 Table 21"],
        ["Treated effluent penalty",
         "Roughness 30 % higher and Hazen-Williams C 10 % lower than the "
         "potable values",
         "G2-p104 note"],
        ["Maximum linear head loss",
         "Transmission below 5.0 m/km; distribution below 3.0 m/km",
         "G2-p105, p136"],
        ["Distribution velocity",
         "0.4 m/s or more and below 1.5 m/s; below 0.4 m/s a water-quality "
         "or age model and proof of a 0.2 mg/L chlorine residual",
         "G2-p136"],
        ["Distribution pressure",
         "At least 1.5 bar at the worst point at peak hour; at most 4 bar; "
         "pressure stays positive under fire flow",
         "G2-p137"],
        ["Distribution pipe material",
         "PE100 up to 1,000 mm in the fixed outside-diameter series; ductile "
         "iron above 300 mm and at road and wadi crossings",
         "G2-p138"],
        ["Pumping, storage and surge",
         "Storage classes in §5, pumping station design with NPSH and "
         "transients in §6, surge analysis mandatory per §10",
         "G2-p53 onward, p70 onward, p144"],
        ["Tanker filling stations",
         "Peak-hour factor 1.5 to 2.0 on average flow; at least two "
         "concurrent bays; 20 % reserve; at least 1 m³ per minute per bay "
         "at 2 to 4 bar",
         "G2-p154"],
    ], adopted=False)


# ================================================================= section 17
def s17_odour(d):
    D.h(d, 1, "17  Odour and hydrogen sulphide", page_break=True)
    D.tab_caption(d, "Odour and hydrogen sulphide criteria (G203 §11, pages "
                     "162 to 191)")
    crit(d, [
        ["Designer deliverable",
         "Designers of sewage networks, pumping stations and force mains "
         "shall provide NWS a dedicated hydrogen sulphide management "
         "evaluation, preventive (re-sizing, chemical injection) and "
         "corrective (monitoring, flushing, coatings, odour treatment)",
         "G203-p162 §11.1"],
        ["Network design for odour",
         "Retention times minimised, turbulence avoided, no over-sizing of "
         "trunk sewers, which creates deposition",
         "G203-p166 §11.3.2; p168 §11.4.2"],
        ["Pumping and force mains",
         "Avoided wherever gravity is feasible and cost-effective; hydraulic "
         "detention minimised, with twinned force mains considered at low "
         "flow; force-main discharges submerged where possible; the main "
         "allowed to drain back to the wet well between cycles; a "
         "partially-full main avoided",
         "G203-p181 to 182 §11.5.3.1"],
        ["Risk assessment",
         "Qualitative Fayoux scoring on temperature, residence time, "
         "velocity and redox (0 to 5 no risk, 5 to 10 low, 10 to 30 "
         "significant or certain), evaluated at maximum temperature and "
         "night-time flow. Quantitative Pomeroy-Parkhurst, with effective "
         "BOD = BOD₅ × 1.07^(T − 20)",
         "G203-p185 Table 99; p186 §11.5.3.4"],
        ["Odour limits at the boundary",
         "Urban or near residential 3 to 5 odour units per m³; industrial "
         "10 to 15; rural or isolated 10 to 20. Compliance at the boundary "
         "wall: 5 odour units per m³ at sensitive receptors, 15 at "
         "industrial, with at least three continuous online electronic "
         "noses. MD 41/2017 and BS EN 13725:2022",
         "G203-p165 §11.3.1; p170 Table 90"],
        ["Odour treatment",
         "Abatement assessment and dispersion modelling to justify the odour "
         "unit or its absence; in most cases multi-stage, bio-trickling "
         "filter plus chemical scrubber with carbon where needed, removing "
         "99.95 % of hydrogen sulphide and 85 % of odour; N+1 redundancy on "
         "every odour control system",
         "G203-p170 to 176 §11.5.2"],
        ["Network emergency storage",
         "Retention basins sized for 24 hours of nominal flow, emptied by "
         "sewage tanker; relief sewers at 1.5 times nominal flow. Distinct "
         "from the plant's 48 to 72 hour emergency lagoon",
         "G203-p191 §12.1.1"],
        ["Trade effluent",
         "Non-domestic discharges to sewer comply with Appendix 3 of Royal "
         "Decree 115/2001, under a customer agreement with NWS and with "
         "NWS-validated pre-treatment where needed",
         "G203-p20 §3.10"],
    ], adopted=False)


# ================================================================= section 18
def s18_modelling(d):
    D.h(d, 1, "18  Modelling, options appraisal and project workflow",
        page_break=True)
    D.tab_caption(d, "Modelling and appraisal criteria (G1 §1.6, §11, §12 "
                     "and §13; Appendix III)")
    crit(d, [
        ["Hydraulic model method",
         "To the WaPUG/CIWEM Code of Practice and the US EPA SWMM manuals; "
         "modelled at design and again after construction; static, "
         "extended-period and surge models submitted to NWS after each "
         "design phase, including the final as-built model",
         "G1-p144; p109 §13.4.2"],
        ["Calibration acceptance",
         "Peak flow within 10 to 15 %; volume within 15 %; correct "
         "peak-arrival timing; pump run time within 10 %",
         "G1-p145 Table 32"],
        ["Options appraisal",
         "At least three options with equivalent function and reliability: "
         "one sustainability-led, one international best practice, one "
         "established local practice. Evaluated over 25 years at a 5 % "
         "discount rate unless NWS instructs otherwise; NWS sets the "
         "multi-criteria weights; options within 10 % on total cost are "
         "decided on sustainability",
         "G1-p95 to 96 §12; p99; p106"],
        ["Options per system",
         "Three for the sewer network, three for the treated effluent "
         "network, three for each treatment plant. Lifting stations are not "
         "a separate set: their number follows from each network layout. "
         "Seven criteria: total lifetime cost; sustainability; social "
         "development and in-country value; adaptability and resilience; "
         "operability; constructability; environmental impact. Sensitivity "
         "on the weighting, the discount rate and the input criteria",
         "Project doctrine, 31 August 2026, on G1-p95 to 106"],
        ["Financial method",
         "Net present value and life-cycle cost at 5 % over 25 years "
         "decide; payback is reported but does not decide. The guidelines "
         "state the requirement and not the method, so ISO 15686-5 is "
         "cited. Operating cost is built bottom-up from duty, never as a "
         "percentage of capital; gravity sewers are priced by diameter and "
         "depth band; every option, including a costed do-nothing baseline, "
         "carries its own pumping, storage and energy",
         "Project doctrine, 1 September 2026, on G1-p57 §7.1 and p95 to 96"],
        ["Value engineering",
         "A formal study by an independent certified consultant at concept "
         "and preliminary stages for projects of OMR 5 million or more; the "
         "footnote lowers the trigger to any treatment plant or pumping "
         "station over OMR 2 million",
         "G1-p93 §11.2 Table 27"],
        ["Cost and schedule accuracy",
         "Feasibility ±30 %; preliminary and concept ±20 %; detailed ±10 %. "
         "A flood protection assessment at all three phases",
         "G1-p17 to 20 §1.6 Table 2"],
        ["Remote areas",
         "About 25 km or more from a centralised network, or under 500 "
         "residents or 100 plots at the end of the design period: septic "
         "tanks to the Oman Private Sewage Disposal Code, holding tanks "
         "emptied by vacuum tanker, or package plants for 50 to 5,000 "
         "inhabitants with at least one day of effluent storage",
         "G1-p80 §8.1; p83 to 84 §8.4"],
    ], adopted=False)


# ================================================================= section 19
def s19_surveys(d):
    D.h(d, 1, "19  Surveys and investigations", page_break=True)
    D.tab_caption(d, "Survey criteria (G203 §13, pages 197 to 199; G1 §5)")
    crit(d, [
        ["Topographic survey",
         "Along the proposed routes with X, Y and Z on the Omani national "
         "datum in metric units; existing utilities and adjacent roads with "
         "cross-sections near the pipelines; grid, permanent benchmark and "
         "invert levels of existing drains on the maps; the designer selects "
         "the terrain model",
         "G203-p197"],
        ["Accuracy by stage",
         "At 95 % confidence: feasibility 1 to 5 m horizontal and 0.5 to "
         "2 m vertical, an existing DEM acceptable; preliminary and concept "
         "0.25 to 1.0 m horizontal and 0.05 to 0.5 m vertical, by UAV "
         "photogrammetry with ground control, LiDAR or GNSS RTK; detailed "
         "0.02 to 0.10 m horizontal and 0.01 to 0.05 m vertical. The 0.5 m "
         "terrain blend used for design is checked against this at the "
         "survey",
         "G1-p36 Table 5"],
        ["Control", "Benchmarks to ±0.05 m, at least Order C Class 3 GPS",
         "G203-p198 §13.3"],
        ["Underground services",
         "Detection covering oil, gas, water and effluent pipelines, cables "
         "and irrigation falaj, by trial pits, probes between manholes, "
         "ground radar and electro-location",
         "G203-p198 §13.3"],
        ["Existing assets",
         "CCTV to NF EN 13508-2, a designer obligation to carry out and to "
         "provide with the tender documents; CCTV, topographic and "
         "geotechnical surveys at the early design stage",
         "G203-p197 to 198"],
        ["Plant and station sites",
         "Full plot dimensions, GPS coordinates of every boundary corner, "
         "surface strata, coverage extending 10 m beyond the plot limits",
         "G203-p198 §13.2"],
        ["Geotechnical",
         "Boreholes to 5.0 m below the pipe invert for shallow pipelines. "
         "Secondary and tertiary gravity sewers: a trial trench to 3.0 m or "
         "a borehole beyond, at 100 m spacing; primary sewers and force "
         "mains at 500 m. Geophysical investigation at the earliest stage "
         "for plants, stations and major wadi, falaj and road crossings",
         "G203-p199 §13.4; G1-p40 to 41 Table 7"],
    ], adopted=False)


# ================================================================= section 20
def s20_register(d):
    D.h(d, 1, "20  Register of project decisions and assumptions",
        page_break=True)
    D.p(d, "Every value below is ours rather than the guideline's. A decision "
           "stands until the engineer changes it. An assumption is pending "
           "data and is replaced when the data arrives; each states what "
           "replaces it.")
    D.tab_caption(d, "Decisions and assumptions carried by the design")
    D.table(d, ["Item", "Value", "Status", "Basis and what replaces it"], [
        ["Maximum cover", "12.0 m, no exception, at chambers and along the "
                          "trench",
         "Decision, 7 September 2026",
         "The guideline's trigger is excavation cost; no costing exists at "
         "concept. Revisited per excursion when the cost analysis exists"],
        ["Tractive tension", "1 Pa",
         "Assumption, gap 9",
         "G203 gives no numeric value. Confirm with NWS; at 2 Pa a large "
         "share of DN200 pipes need a steeper gradient"],
        ["Minimum tractive design flow", "1.5 L/s",
         "Assumption",
         "Mara's minimum design flow; without a floor the equation demands "
         "unbounded slopes as the flow tends to zero"],
        ["PVC-U wall class", "SDR34, SN8",
         "Assumption",
         "Sets the true bore behind the hydraulics; the actual class per "
         "PAM-SPC-207 from NWS"],
        ["Occupancy rate", "5.32 project basis; 5.0 in the W13 test-area "
                           "run",
         "Decision, 30 August 2026; open item for W13",
         "Measured from settlement population and counted domestic "
         "properties; recomputed when the clean plot layer lands. The "
         "test-area gate figures were produced at 5.0 and the full-area run "
         "is to apply 5.32"],
        ["Properties per plot", "Counted; 1.0 fallback",
         "Data, 19 August 2026",
         "Electricity accounts; the fallback applies only to a plot with no "
         "account"],
        ["Wadi ground", "Flood hazard classes 4, 5 and 6 of the 50-year grid",
         "Assumption",
         "Stands in for the guideline's washout criterion; settled by a "
         "scour-depth check"],
        ["Reduced cover at a wadi crossing", "Not available",
         "Position",
         "The guideline is silent; the 1.5 m answers scour and the "
         "encasement answers load"],
        ["Lateral length cap", "45 m on riders and lateral sewers alike",
         "Decision",
         "The conservative reading of G203 Table 6 and §3.2"],
        ["Inlet angle", "85° applied; sharper than 75° flagged",
         "Decision, 20 August 2026; deviation",
         "Avoids about 200 bend chambers that served no construction "
         "purpose; see Section 21"],
        ["Gradient steps", "0.05 %",
         "Decision, 23 August 2026",
         "The drawing value is the design value"],
        ["Chamber spacing", "100 m split, rounded to 10 m, 5 m fallback",
         "Decision, 18 August 2026",
         "Satisfies every spacing class of G203 Table 12"],
        ["Chamber separation", "3.0 m",
         "Convention", "No minimum exists in the guidelines"],
        ["Chamber sizes", "DN1000 to 3 m, DN1200 to 6 m, DN1500 deeper",
         "Convention", "The guideline says only sufficient size"],
        ["Kerb clearances for gravity sewers", "1 m pipe, 0.5 m chamber",
         "Inference", "A force-main clause at G203-p51 applied to gravity"],
        ["House drain outlet", "0.60 m below plot ground; 2 % blended fall",
         "Method choice", "Concept-stage connectability test only"],
        ["Wall and bedding allowance", "0.05 m", "Assumption",
         "Below the crown cover in the invert-depth calculation"],
        ["Infiltration order", "Added unpeaked", "Assumption",
         "G1 does not state whether infiltration is peaked; confirm at "
         "kickoff"],
        ["Peak factor below 100 properties", "Held at the 100-property value",
         "Method choice", "The guideline prescribes no formula below 100"],
        ["G1 Table 12 drivers", "Not applied",
         "Decision, 30 August 2026",
         "Floor area, pupils, beds and employees are not supplied; adopt "
         "G1 Table 12 when real quantities arrive, never with the ratios"],
        ["Road corridor thresholds",
         "Collinear 10°, bend 30°, gate search 45 m, frontage 40 m",
         "Method choices", "Tuned on review"],
        ["Dual carriageway rules", "Excluded; crossings ≤ 70 m, within 25° "
                                   "of square, charged 2,500 m; underpass "
                                   "radius 30 m",
         "Decision, 19 to 21 August 2026", "Section 9"],
        ["Join charge onto the main pipe", "400 m equivalent",
         "Decision, 20 August 2026",
         "Fewer than 15 joins costs a pumping station on the test area"],
        ["Pumping pockets", "Under 50 plots absorbed",
         "Rule", "Detail design item"],
        ["Cascading stations; rising-main duty rule", "Not settled",
         "Open, 7 September 2026",
         "Decided when the design raises them"],
    ], widths=[3.4, 3.6, 3.0, 6.6], font=8.5)


# ================================================================= section 21
def s21_deviations(d):
    D.h(d, 1, "21  Deviations to be declared to NWS", page_break=True)
    D.p(d, "Each item below departs from the letter of a guideline clause. "
           "Each is stated in the deliverable and NWS agreement is sought.")
    D.tab_caption(d, "Deviations and the agreement sought")
    D.table(d, ["Deviation", "Guideline clause", "What the design does and why"], [
        ["Inlet angle of 85° rather than 90°",
         "G203-p30, \"shall\"",
         "Enforcing 90° at every street junction inserted about 200 bend "
         "chambers a few metres short of junctions for no construction "
         "benefit. The design applies 85°, flags any inlet sharper than 75° "
         "for a purpose-made chamber with a curved channel, and never adds a "
         "chamber to satisfy the rule"],
        ["Occupancy from electricity accounts",
         "G1-p58 defines the rate as population ÷ NCSI housing units",
         "Housing units are not published at settlement level, so counted "
         "domestic properties stand in for them. Validated by coverage "
         "within 2.0 points (Section 12.2)"],
        ["Spatial allocation of non-domestic flow",
         "G1-p59 §7.3.1 describes \"spatially distributed non-domestic "
         "consumption\" added to domestic consumption",
         "The uplift is concentrated on the commercial and government plots "
         "rather than spread across the population. The total is preserved; "
         "a residential-only branch generates no commercial flow. Measured "
         "effect: project total unchanged, zone totals move between −17 % "
         "and +127 %"],
        ["Planning-tier ratios in a project-specific design",
         "G1-p60 §7.3.2 and p61 §7.3.3, \"shall\" use G1 Table 12 where "
         "detailed land use exists",
         "The G1 Table 12 quantities have not been supplied, so the "
         "condition is unmet in substance. The 22 % and 14 % ratios set the "
         "volume as a labelled fallback and are replaced by G1 Table 12 when "
         "the data arrives"],
        ["Weekly peak of 20 % in the Inception Report",
         "G1 §7.4.2 gives Merrimack or Peltier only",
         "The Inception Report applied a water-side peak-week concept on top "
         "of Peltier. The two peak twice; an NWS ruling is sought "
         "(Appendix A)"],
        ["Infiltration at 10 % of flow in the Inception Report",
         "G1-p72 §7.4.3 gives 720 L/day/km for new networks",
         "The design applies 720 L/day/km per pipe; the Inception Report "
         "value is flagged for kickoff"],
        ["Presence in a wadi where no other route exists",
         "G203-p30 \"must be avoided\"; p33 \"shall be avoided\"",
         "The design avoids it; where it cannot, the presence is a recorded "
         "and justified exception carried in the deliverable"],
    ], widths=[3.6, 4.2, 8.8], font=8.5)


# ================================================================= appendix A
def appendix_a(d):
    D.h(d, 1, "Appendix A  Inception Report values against the guideline",
        page_break=True)
    D.p(d, "The Inception Report Revision 0 and its demand workbook adopted "
           "the values below. Each is reconciled against the guideline "
           "clause; where the two differ the item is carried to Section 21.")
    D.tab_caption(d, "Inception Report R0 adoptions reconciled")
    D.table(d, ["Item", "Inception Report value", "Against the guideline"], [
        ["Population basis",
         "NCSI wilayat series, Ibri 183,564 in 2024, growth about 2.4 to "
         "3.0 % a year, settlement disaggregation",
         "Consistent with G1-p58"],
        ["Domestic consumption, Adh Dhahirah",
         "163.5 L per head per day, computed from actual consumption 2021 "
         "to 2024",
         "Agrees with the 164 of G1 Table 11"],
        ["Return ratios",
         "Domestic and tanker 0.85; non-domestic and governmental 0.54",
         "Equal to G1-p71 Table 19"],
        ["Infiltration", "10 % of wastewater flow, settlement-conditional",
         "G1-p72 gives 720 L/day/km for new networks; flagged at kickoff"],
        ["Tanker catchment", "Settlements within 25 km of the plant",
         "The 25 km is in G1-p80 §8.1, which defines a remote area as "
         "\"approximately 25 km or more from existing centralized … "
         "networks\" or under 500 residents or 100 plots at the end of the "
         "design period. The report reused it as a tanker-catchment radius; "
         "the reading is confirmed with NWS"],
        ["Weekly peak", "+20 %",
         "Not in the G1 wastewater peaking chain. G1-p62 §7.3.6 defines a "
         "water-side peak day as \"the average day consumption in the peak "
         "week (7-days rolling) excluding leakage\"; the report appears to "
         "have carried it into the wastewater chain on top of Peltier. An "
         "NWS ruling is sought"],
        ["Plant margin, effluent ratio, sludge",
         "+10 %; treated effluent 95 % of inflow; sludge 0.25 kg/m³",
         "All three in G1-p73 and G1-p78 §7.4.7"],
        ["Treated effluent network loss", "Not applied",
         "G1-p76 requires a 10 % loss on produced effluent; the 95 % ratio "
         "alone overstates the deliverable volume by about 10 %"],
    ], widths=[3.4, 5.6, 7.6], font=8.5)


# ======================================================================= main
def main(render_pdf=False):
    os.makedirs(os.path.join(HERE, REV), exist_ok=True)
    d = D.new_document()
    N.reset()
    N.ensure_style(d)

    cover(d)
    contents(d)
    s1_purpose(d)
    s2_hydraulics(d)
    s3_gradients(d)
    s4_pipes(d)
    s5_cover(d)
    s6_chambers(d)
    s7_tertiary(d)
    s8_wadis(d)
    s9_layout(d)
    s10_pumping(d)
    s11_force_mains(d)
    s12_flows(d)
    s13_life(d)
    s14_tse(d)
    s15_stp(d)
    s16_g202(d)
    s17_odour(d)
    s18_modelling(d)
    s19_surveys(d)
    s20_register(d)
    s21_deviations(d)
    appendix_a(d)

    D.footer_pagenum(d, f"Ibri Sewer Network Design Criteria  ·  W13  ·  "
                        f"Revision {REV[1:]}  ·  Renardet Project 2621")

    out = OUT
    try:
        N.save(d, out)
    except PermissionError:
        out = OUT.replace(".docx", "_new.docx")
        N.save(d, out)
        print("NOTE: the target file is open in Word; wrote a copy instead.")
    print(f"wrote {out}")

    if render_pdf:
        import to_pdf
        pdf, pages = to_pdf.convert(out)
        print(f"wrote {pdf}  ({pages} pages)")


if __name__ == "__main__":
    main(render_pdf="--pdf" in sys.argv)
