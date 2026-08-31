"""Cover, how-to-use, and the executive summary.

The summary is written to be the fast path: a reader who reads only these pages
should be able to carry out the concept report correctly and know which section
to open when they need the detail.
"""
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
import os

from docx.shared import Pt

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

import doc as D
import omml as M

PROJ = "Consultancy Services for Design and Supervision for STP, Sewer and TE Networks Systems in Ibri"
TITLE = "Concept Design — Methodology, Equations and Workflows"


def cover(d):
    D.p(d, "", space_after=50)
    D.p(d, "Sultanate of Oman", align=AL.CENTER, bold=True, size=13)
    D.p(d, "Nama Water Services Company SAOC", align=AL.CENTER, bold=True, size=12)
    D.p(d, "", space_after=36)
    D.p(d, PROJ, align=AL.CENTER, bold=True, size=14, colour=D.GREY)
    D.p(d, "Tender No. T/2719110/2025", align=AL.CENTER, size=11, colour=D.GREY)
    D.p(d, "", space_after=30)
    D.p(d, TITLE, align=AL.CENTER, bold=True, size=22, colour=D.BLUE)
    D.p(d, "Tutorial T03", align=AL.CENTER, bold=True, size=13, colour=D.MID)
    D.p(d, "", space_after=30)
    D.p(d, "A working reference for every calculation the Concept Design Report "
           "requires: what each step is for, how it is done, which equation "
           "applies, what every symbol means, and which page of which guideline "
           "it comes from.",
        align=AL.CENTER, size=10.5, italic=True)
    D.p(d, "", space_after=60)
    D.p(d, "Renardet S.A. & Partners", align=AL.CENTER, bold=True, size=11)
    D.p(d, "Project 2621   ·   Revision 0   ·   August 2026",
        align=AL.CENTER, size=10, colour=D.GREY)
    D.pagebreak(d)


def how_to_use(d):
    D.h(d, 1, "How to use this document")

    D.p(d, "This is a reference, not a report. It is written to be opened at "
           "the point of need: when a step of the concept design has to be "
           "carried out and the question is what exactly to calculate, with "
           "what, and on whose authority.")

    D.h(d, 2, "Reading paths")
    D.table(d,
            ["If you want to…", "Read"],
            [["Understand the whole chain in twenty minutes",
              "The executive summary that follows, and nothing else"],
             ["Carry out one calculation correctly",
              "The section for that step. Each is self-contained"],
             ["Check a number before it goes to the client",
              "The equation, then its source page in the guideline itself"],
             ["Know where the guidelines are wrong or silent",
              "Section 15, and the caution boxes throughout"]],
            widths=[7.5, 9.0], font=9.5)

    D.h(d, 2, "How each section is built")
    D.p(d, "Every calculation section follows the same five parts, so the "
           "document can be navigated by shape rather than by memory.")
    D.bullet(d, "why the step exists and what it feeds", lead="Purpose — ")
    D.bullet(d, "how it is done, in order", lead="Method — ")
    D.bullet(d, "as a native Word equation, numbered", lead="Equation — ")
    D.bullet(d, "every symbol, its meaning and its unit", lead="Parameters — ")
    D.bullet(d, "guideline and page, so any figure can be checked at source",
             lead="Source — ")

    D.h(d, 2, "Three conventions worth knowing before you start")

    D.callout(d, "Nothing here is quoted from memory.",
              "Every equation in this document was read from the guideline page "
              "itself, rendered as an image, because the text layer of the PDFs "
              "mangles fraction bars, roots and exponents. Three equations exist "
              "in the guidelines only as pictures and cannot be found by "
              "searching the text at all.",
              fill="EAF1F8", colour=D.MID)

    D.callout(d, "Where a formula is not NWS's, it says so.",
              "Several formulae every engineer expects to find — net present "
              "value, life cycle cost, total dynamic head, pump power, "
              "Darcy-Weisbach and Hazen-Williams in written form — do not appear "
              "anywhere in the three guidelines. Each is attributed here to its "
              "actual source. Citing NWS for them would be a fabricated "
              "reference.",
              fill="EAF1F8", colour=D.MID)

    D.callout(d, "Where the guideline is wrong, it is reproduced and flagged.",
              "The guidelines contain errors — a dimensionally impossible flow "
              "equation, a peak-factor formula that differs from the published "
              "original, a tanker ratio that cannot be arithmetically true. This "
              "document prints what the guideline prints, then says plainly what "
              "is wrong with it. It does not silently correct the client's own "
              "standard.")

    D.p(d, "")
    D.h(d, 2, "Abbreviations")
    D.table(d,
            ["Term", "Meaning"],
            [["AAF", "Average Annual Flow, the daily volume averaged over a year"],
             ["Qadf", "Average daily flow — the same quantity, the guideline's symbol"],
             ["MDF", "Maximum Day Flow"],
             ["PHF / Qpdf", "Peak Hour Flow, and peak daily flow"],
             ["Pf", "Peak factor, the ratio converting an average flow to a peak flow"],
             ["LPCD", "Litres per capita per day"],
             ["OR", "Occupancy rate, persons per housing unit"],
             ["d/D", "Proportional depth — flow depth divided by pipe diameter"],
             ["SRT", "Solids retention time, also called sludge age"],
             ["TN", "Total nitrogen"],
             ["OU", "Odour unit; 1 OU/m³ is the concentration half a panel can detect"],
             ["DS", "Dry solids"],
             ["NCSI", "National Centre for Statistics and Information"],
             ["MoHUP", "Ministry of Housing and Urban Planning"],
             ["APSR", "Authority for Public Services Regulation"],
             ["G201 / G202 / G203",
              "PAM-GUD-201 General Design, -202 Water and TSE, -203 Wastewater, "
              "all Revision 01 of March 2026"]],
            widths=[3.0, 13.5], font=9)

    D.callout(d, "One term to be careful with.",
              "In G201 and G203, TE means Trade Effluent and TSE means Treated "
              "Sewage Effluent. This project, the TOR and the tender all use TE "
              "to mean treated effluent. Wherever this document says TSE it means "
              "the treated product of the STP. Say so explicitly in anything sent "
              "to NWS, or a guideline-literate reviewer will read a trade "
              "effluent network into the report.")

    D.pagebreak(d)


def executive_summary(d):
    D.h(d, 1, "Executive summary")

    D.p(d, "The concept design turns a population into a set of pipe diameters, "
           "a plant capacity and a phasing plan. This document sets out how, in "
           "twelve steps, and fixes every number to a page of a guideline. What "
           "follows is the whole chain in short form. Anyone who reads only these "
           "few pages should be able to do the work and know where to look when "
           "a detail is needed.")

    # ---------------------------------------------------------------- chain
    D.h(d, 2, "The chain, in twelve steps")

    D.table(d,
            ["#", "Step", "What comes out", "Section"],
            [["1", "Prepare the data", "A clean plot layer with counted properties and a land use for each", "3"],
             ["2", "Population", "People, per settlement, per year", "4"],
             ["3", "Water demand", "Litres per day, by consumption category", "5"],
             ["4", "Wastewater generation", "The flow that reaches the sewer", "6"],
             ["5", "Project through time", "A flow for every year to saturation", "7"],
             ["6", "Peak and infiltration", "The flow the pipe is actually sized on", "8"],
             ["7", "Gravity network", "Diameters, gradients, depths, manholes", "9"],
             ["8", "Lifting stations", "Where gravity fails, and what pumps it", "10"],
             ["9", "STP sizing and phasing", "Plant capacity, by phase", "11"],
             ["10", "Treated effluent", "How much is produced, and who takes it", "12"],
             ["11", "Sludge", "How much, and where it goes", "13"],
             ["12", "Options and appraisal", "Three options, costed, and a recommendation", "14"]],
            widths=[1.0, 4.2, 8.3, 2.0], font=9)

    D.p(d, "")
    D.picture(d, os.path.join(IMG, "F1_chain.png"), 15.5)
    D.fig_caption(d, "The concept design calculation chain. The left column establishes the flow; the right sizes the works.")
    D.p(d, "Steps 1 to 6 are one continuous calculation: each is the input to "
           "the next, and an error early on propagates the whole way. Steps 7 to "
           "11 consume that flow independently of one another. Step 12 sits "
           "across all of them.")

    # ------------------------------------------------------------- the spine
    D.h(d, 2, "The spine of the calculation")

    D.p(d, "Stripped of detail, the flow chain is four multiplications and two "
           "additions. Everything else is refinement.")

    eq = D.next_eq()
    M.display(d, M.seq(
        M.up("Population"), M.EQ, M.up("Plots"), M.TIMES,
        M.up("Properties per plot"), M.TIMES, M.up("OR")), number=eq)

    eq = D.next_eq()
    M.display(d, M.seq(
        M.sub(M.r("Q"), M.up("demand")), M.EQ,
        M.up("Population"), M.TIMES, M.up("LPCD"), M.TIMES,
        M.delim(M.seq(M.r("1"), M.PLUS, M.r("0.22"), M.PLUS, M.r("0.14")))),
        number=eq)

    eq = D.next_eq()
    M.display(d, M.seq(
        M.sub(M.r("Q"), M.up("adf")), M.EQ,
        M.sub(M.r("Q"), M.up("dom")), M.TIMES, M.r("0.85"), M.PLUS,
        M.sub(M.r("Q"), M.up("ND")), M.TIMES, M.r("0.54"), M.PLUS,
        M.sub(M.r("Q"), M.up("inf"))), number=eq)

    eq = D.next_eq()
    M.display(d, M.seq(
        M.sub(M.r("Q"), M.up("design")), M.EQ,
        M.sub(M.r("Q"), M.up("adf")), M.TIMES, M.up("Pf")), number=eq)

    D.p(d, "The 22 % and 14 % are the non-domestic and governmental uplifts for "
           "Adh Dhahirah. The 85 % and 54 % are the proportions of supplied water "
           "that come back as sewage. The peak factor comes from Merrimack. Each "
           "is traced to its page in the sections that follow.")

    # --------------------------------------------------------- the numbers
    D.h(d, 2, "The numbers that govern Ibri")

    D.table(d,
            ["Quantity", "Value", "Where it comes from"],
            [["Domestic consumption", "164 l/c/d", "G201 Table 11, Adh Dhahirah"],
             ["Non-domestic uplift", "22 % of domestic", "G201 Table 11"],
             ["Governmental uplift", "14 % of domestic", "G201 Table 11"],
             ["Return to sewer, domestic and tanker", "85 %", "G201 Table 19"],
             ["Return to sewer, non-domestic", "54 %", "G201 Table 19"],
             ["Infiltration, new networks", "720 l/d per km of sewer", "G201 p72"],
             ["Peak factor", "Merrimack, over 100 properties", "G201 p71"],
             ["Minimum self-cleansing velocity", "0.75 m/s at peak flow", "G203 p26"],
             ["Maximum velocity", "3 m/s", "G203 p27"],
             ["Flow depth at peak", "0.65 up to 350 mm, 0.50 above", "G203 Table 10"],
             ["Minimum cover", "1.3 m to pipe crown", "G203 p33"],
             ["Recommended maximum cover", "approximately 10–12 m", "G203 p33"],
             ["STP design margin", "10 %", "G201 p73"],
             ["TSE produced", "95 % of plant inflow", "G201 p73"],
             ["TSE network loss", "10 % of TSE produced", "G201 p76"],
             ["Sludge", "0.25 kg per m³ of inflow", "G201 p78"],
             ["Total nitrogen in the effluent", "below 15 mg/l as N", "G203 p71"],
             ["Design horizon", "at least 15 years for the STP; 25 years for appraisal",
              "G203 p65, G201 p57"]],
            widths=[5.6, 4.6, 6.3], font=9)

    # ------------------------------------------------------- what to watch
    D.h(d, 2, "Six things that are easy to get wrong")

    D.p(d, "These are the places where a correct-looking calculation gives a "
           "wrong answer. Each is explained where it arises.")

    D.rich(d, ("Merrimack runs in megalitres per day. ", {"bold": True}),
           ("The formula has an exponent of 0.879, so feeding it cubic metres "
            "instead of megalitres does not scale the answer — it produces a "
            "different number entirely. Peltier, on the facing page, wants "
            "litres per second. The general peak-factor equation between them "
            "is in cubic metres per day.", {}))

    D.rich(d, ("The minimum gradient table is a full-bore table. ", {"bold": True}),
           ("Its gradients deliver 0.75 m/s when the pipe runs full. The "
            "guideline separately requires 0.75 m/s at peak flow. A pipe over "
            "350 mm laid at the table minimum sits exactly on the limit at its "
            "design depth, and every pipe falls below it in the opening years.",
            {}))

    D.rich(d, ("The depth rule is a recommendation about cover. ", {"bold": True}),
           ("Ten to twelve metres is not a limit and does not refer to invert "
            "depth. What triggers a pumping station is excavation cost becoming "
            "prohibitive, and the guideline attaches no depth figure to that.",
            {}))

    D.rich(d, ("Tankered water still becomes sewage. ", {"bold": True}),
           ("Water delivered by truck returns to the sewer at the same 85 % as "
            "piped water. Leaving it out understates the load, and in this "
            "governorate the tankered volume is large.", {}))

    D.rich(d, ("Accuracy points in opposite directions. ", {"bold": True}),
           ("For pipe and plant capacity, under-estimating is the danger. For "
            "the self-cleansing and washing schedule, over-estimating is the "
            "danger, because it declares the pipes self-scouring while they "
            "silt. One population figure cannot serve both.", {}))

    D.rich(d, ("Table 12 and the percentage uplifts are alternatives. ", {"bold": True}),
           ("Applying unit rates to commercial plots and then adding the 22 % "
            "and 14 % counts the same water twice. Use one or the other.", {}))

    # ------------------------------------------------ guideline reliability
    D.h(d, 2, "Where the guidelines cannot be relied on")

    D.p(d, "Three categories, each handled in full in Section 15.")

    D.rich(d, ("Formulae that are not there. ", {"bold": True}),
           ("Net present value, life cycle cost, carbon footprint, "
            "multi-criteria scoring, total dynamic head, pump power, and both "
            "friction equations in written form. The guidelines name them and "
            "tabulate their coefficients but never write them. They are "
            "attributed here to ISO 15686-5, the GHG Protocol, Metcalf and "
            "Eddy, or standard hydraulics.", {}))

    D.rich(d, ("A mandatory method that cannot be executed. ", {"bold": True}),
           ("The tractive force check is required, and the required value of "
            "shear stress in pascals appears nowhere in either guideline. Any "
            "value used has to come from outside and be agreed with NWS.", {}))

    D.rich(d, ("Twenty-eight printing and arithmetic defects. ", {"bold": True}),
           ("Including a flow equation that divides where it should multiply, a "
            "peak-factor formula that differs from its published original, and "
            "a tanker ratio that cannot be true. All are listed with their page "
            "numbers.", {}))

    D.pagebreak(d)
