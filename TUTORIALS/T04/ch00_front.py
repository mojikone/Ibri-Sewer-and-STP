"""T04 front matter: the cover, how to use the tutorial, and the chain at a glance.

Every Ibri number on these pages is read at build time from the W14 outputs
(facts_w14 and W14/analysis/design_flows.json). Nothing is typed in.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report"))   # after T04: its doc.py must not shadow ours
import doc as D
import omml as M
import facts_w14 as F
UP, R = M.up, M.r
IMG = os.path.join(HERE, "img")

import datetime
import json
import math

from docx.enum.text import WD_ALIGN_PARAGRAPH as AL

REPO = os.path.dirname(os.path.dirname(HERE))
FLOWS_JSON = os.path.join(REPO, "W14", "analysis", "design_flows.json")

# The concept-stage gradient rule (project rule, engineer 2026-09-11). Only the DN900-and-above
# row of G203 Table 11 is used on these pages, for the worked number of the summary.
T11_DN900 = 0.75                      # mm/m, DN900 and above (G203-p29 Tab 11)
STEP_SECONDARY = 0.50                 # mm/m = 0.05 %, secondary pipes
STEP_TRUNK = 0.25                     # mm/m = 0.025 %, primary trunks of DN500 and up
TOLERANCE_MM = 20.0                   # mm, line and level (G203-p29 §4.3.1)
CLASSES = ["velocity pass", "tractive pass", "needs washing"]   # the self-cleansing classes taught here

PROJ = "Consultancy Services for Design and Supervision for STP, Sewer and TE Networks Systems in Ibri"
TITLE = "From the Meter to the Pipe — Population, Flows, Sewer and Plant Design"
REV = "Revision 00"
MONTH = "September 2026"

# chapter number, title, one line for the summary, script, main output (field or sheet)
# scripts without a folder are in W14/py/
CHAPTERS = [
    ("1", "The data",
     "What was supplied, what each dataset is trusted for, and what the chain reads.",
     "`plots_meters_load.py` (run in QGIS); inventory `_BRAIN/03_DATA_INVENTORY.md`",
     "`W14/shp/PLOTS_load.shp`: `Name`, `Moh_Classi`, `Buiding_St`, `AREA_M2`; meters `ELE_meters_on_plots.shp`"),
    ("2", "From meter to plot, and the use of every plot",
     "Meters go onto plots; their mix sets the use.",
     "`plots_meters_load.py`, `ndvi_plots.py`, `plot_class_v2_apply.py`",
     "meter `PLACE`; plot `N_ACC`, `G_DOM` to `G_AGR`, `DERIVED`, `WHYC`, `GREEN_M2`"),
    ("3", "Properties per plot and the occupancy rate",
     "A home meter is a property; a rate per settlement.",
     "`plot_class_v2_apply.py`",
     "`G_DOM`, `PPP_S`, `OR_S`; `W14/analysis/occupancy_by_settlement.csv`"),
    ("4", "The empty land and its capacity",
     "The people the home-shaped empty plots can still house.",
     "`plot_class_v2_apply.py`",
     "`HOMESHAPE`, `HOMESH_S`, `FUT_CAP`, `SPREAD_W`; settlement `CAP_POP`"),
    ("5", "Growth, overflow and saturation",
     "Own growth until full, then overflow to neighbours.",
     "`growth_by_settlement.py`",
     "workbook sheets *Population by year*, *Overflow routes*, *Settlements*; `SAT_YEAR`, `POP_ULT`"),
    ("6", "Water demand",
     "Litres per person in the homes; shop and government shares landed on their own meters.",
     "`plot_class_v2_apply.py`",
     "`U_NDOM`, `U_GOV`, `W_DOM`, `W_NDOM`, `W_GOV`, `W_SPEC`, `W_TOT`"),
    ("7", "The sewage of every plot",
     "The return to sewer turns each plot's water into its average dry-weather flow.",
     "`plot_class_v2_apply.py`",
     "`S_DOM`, `S_NDOM`, `S_GOV`, `S_SPEC`, `QADF`"),
    ("8", "Flow through time and the two design cases",
     "Size on saturation; test self-cleansing on the low case.",
     "`growth_by_settlement.py`, `make_design_flows.py`",
     "`Q_2030`, `Q_2055`, `Q_ULT`; sheet *Qadf by year m3d*; `W14/analysis/design_flows.json`"),
    ("9", "Peak flow and infiltration",
     "Merrimack or Peltier by properties upstream; infiltration per km, on the sizing case only.",
     "`W13/py/sewnet/criteria.py`, `hydra.py`",
     "pipe `N_PROPS`, `QADF_M3D`, `PF`, `PF_PELT`, `QPEAK_LS`"),
    ("10", "The network and its tiers",
     "Primary, secondary and tertiary pipes, and the roads each may follow.",
     "`W13/py/sewnet/skeleton.py`, `pipeline.py`",
     "pipe `TIER`, `ON_TRUNK`, `IS_JOIN`"),
    ("11", "Gravity sewer hydraulics",
     "Diameter, depth of flow and velocity against their limits; the gradient laid at the G203 "
     "Table 11 minimum in round steps.",
     "`W13/py/sewnet/hydra.py`, `stages/hydraulic.py`; gradient step `SLOPE_STEP` in `criteria.py`",
     "pipe `DN_MM`, `SLOPE_PCT`, `VEL_MS`, `DOD`; chamber `DEPTH`"),
    ("12", "Self-cleansing and the early years",
     "The low case tested for velocity, then tractive force; three classes: velocity pass, "
     "tractive pass, needs washing.",
     "`W13/tmp3/py/sewnet/hydra.py` (`smin_tractive`), `stages/audit.py`",
     "the three classes are a rule, not yet a field: pipe `CLEANSE` is specified in "
     "`W14/docs/PROMPT_W13_SELFCLEANSING_AUDIT.md`"),
    ("13", "Lifting stations and force mains",
     "Where gravity would go too deep, and how the pumped main is sized.",
     "`W13/py/sewnet/pipeline.py`, `catchments.py`; limit `MAX_DEPTH` in `criteria.py`",
     "chamber `IS_PUMP`, `LIFT_M`; pipe `RISE_MAIN`, `QDUTY_LS`"),
    ("14", "Septicity and odour",
     "Retention, turbulence and the measures that keep hydrogen sulphide down.",
     "no script; method in report R2 §30 (`W14/report/rpt_gh.py`)",
     "none yet"),
    ("15", "Utilities and crossings",
     "Clearances, corridors, dual carriageways and wadis.",
     "no script; report R2 §33 (`W14/report/rpt_gh.py`)",
     "pipe `IS_XING` (crosses a dual carriageway)"),
    ("16", "Hydraulic modelling",
     "The SewerGEMS model as the independent check on the design calculation.",
     "`W13/py/sewnet/export_gems.py`",
     "`CONDUITS.shp`, `MANHOLES.shp`, `LOADS.xlsx`, `REFEREE_pipes.csv`"),
    ("17", "The existing network",
     "What the records show, what they cannot show, and how the network is assessed.",
     "`W13/py/export_existing.py`; report R2 §18 (`W14/report/rpt_ef.py`)",
     "NAMA KMZ records as shapefiles, indicative only; filter on `OP_STATUE` (built or proposed) before quoting a length"),
    ("18", "Treatment plant flows and loads",
     "Average, maximum-day and peak flows, margin and loads.",
     "`make_design_flows.py`; report R2 §25 (`W14/report/rpt_ef.py`)",
     "sheet *Qadf by year m3d*; `stp_ultimate_with_margin_m3d` in `design_flows.json`"),
    ("19", "Treated effluent",
     "How much the plant produces, how much reaches customers, and who takes it.",
     "no script; report R2 §17 and §24 (`rpt_cd.py`, `rpt_ef.py`)",
     "none yet"),
    ("20", "Sludge",
     "How much is produced and where it goes.",
     "no script; report R2 §27 (`W14/report/rpt_ef.py`)",
     "none yet"),
    ("21", "Cost estimation",
     "Capital and operating cost, on one basis for every option.",
     "no script; report R2 §35 (`W14/report/rpt_gh.py`)",
     "none yet"),
    ("22", "Financial appraisal",
     "Net present value and life cycle cost decide; payback is reported, not used.",
     "report R2 §35.4 (`rpt_gh.py`); `W9/analysis/W9_PIAD_financial_review.md`",
     "none yet"),
    ("23", "Options and the recommendation",
     "Three options per system, scored on the same criteria.",
     "report R2 §21, §22, §38 (`rpt_ef.py`, `rpt_gh.py`)",
     "none yet"),
    ("24", "Where the guidelines cannot be relied on",
     "Missing formulae and values, defects, departures.",
     "`_BRAIN/05_GAPS.md`, `_BRAIN/02_DESIGN_CRITERIA.md`; departures report R2 §10.1 (`rpt_cd.py`)",
     "the gap register"),
]
APPENDIX = ("A", "Equations, fields and the rerun order",
            "Every equation, every field, and what to rerun first.",
            "`make_design_flows.py`; the rerun order in Appendix A",
            "the fields listed in `design_flows.json`")


def _flows():
    with open(FLOWS_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def _plain(s):
    """Table cells show file and field names without the markdown backticks and asterisks."""
    return s.replace("`", "").replace("*", "")


def _laid(s_mmm, step):
    """A minimum gradient rounded UP to its step, mm/m: never flatter than the minimum."""
    return math.ceil(round(s_mmm / step, 6)) * step


def _rulings(js):
    """The engineer's confirmed rulings of 2026-09-11 as written into design_flows.json.
    The build stops if the file no longer says what these pages teach."""
    r = js["rules"]["rulings_confirmed"]
    assert r["status"].startswith("confirmed"), "design_flows.json: the rulings are no longer confirmed"
    assert r["classes"] == CLASSES, "design_flows.json no longer carries the three classes taught here"
    assert r["regrade_class"] == "none", "the pages say there is no regrade class"
    assert r["low_flow_threshold"] == "none", "the pages say there is no low-flow threshold"
    assert r["low_case_infiltration"] == "left out", "the pages say the low case carries no infiltration"
    assert "connected" in r["low_case_property_count"], "the pages count connected properties in the low case"
    assert float(r["tau_pa"]) == 1.0, "the pages decide the class at 1 Pa"
    assert "2.33e-4" in r["mara_constant"] and "m3/s" in r["mara_constant"], "the pages use K = 2.33e-4, Q in m3/s"
    assert r["tractive_sets_gradient"].startswith("no"), "the pages say the tractive force sets no gradient"
    return r


def _dn900():
    """The worked number of the gradient rule: a DN900 trunk on the trunk step and on one 0.05 % grid."""
    fine, coarse = _laid(T11_DN900, STEP_TRUNK), _laid(T11_DN900, STEP_SECONDARY)
    deeper_mm_km = (coarse - fine) * 1000.0            # mm/m over 1,000 m
    tenth_100m_mm = T11_DN900 / 10.0 * 100.0            # a tenth-of-minimum step over a 100 m pipe, mm
    assert abs(fine - T11_DN900) < 1e-9, "on the trunk step a DN900 must stay at its Table 11 minimum"
    assert coarse > fine, "on one 0.05 % grid a DN900 must be laid steeper than its minimum"
    assert tenth_100m_mm < TOLERANCE_MM, "a tenth-of-minimum step must be finer than the 20 mm tolerance"
    return fine, coarse, deeper_mm_km, tenth_100m_mm


# ------------------------------------------------------------------ cover
def cover(d):
    D.p(d, "", space_after=50)
    D.p(d, "Sultanate of Oman", align=AL.CENTER, bold=True, size=13)
    D.p(d, "Nama Water Services Company SAOC", align=AL.CENTER, bold=True, size=12)
    D.p(d, "", space_after=36)
    D.p(d, PROJ, align=AL.CENTER, bold=True, size=14, colour=D.GREY)
    D.p(d, "Tender No. T/2719110/2025", align=AL.CENTER, size=11, colour=D.GREY)
    D.p(d, "", space_after=30)
    D.p(d, "Tutorial T04", align=AL.CENTER, bold=True, size=13, colour=D.MID)
    D.p(d, TITLE, align=AL.CENTER, bold=True, size=22, colour=D.BLUE)
    D.p(d, f"{REV}  ·  {MONTH}", align=AL.CENTER, bold=True, size=13, colour=D.MID)
    D.p(d, "", space_after=30)
    D.p(d, "A teaching reference for the whole concept design method. Every step, from the "
           "electricity meter on a plot to a sized, self-cleansing sewer and a sized treatment "
           "plant, is given with its rule, its source page, a worked Ibri number and the script "
           "that does it.",
        align=AL.CENTER, size=10.5, italic=True)
    D.p(d, "It replaces Tutorials T01, T02 and T03 Revision 01 as the teaching reference. "
           "Those three stay unchanged as the record.",
        align=AL.CENTER, size=10, colour=D.GREY)
    D.p(d, "", space_after=60)
    D.p(d, "Renardet S.A. & Partners", align=AL.CENTER, bold=True, size=11)
    D.p(d, f"Project 2621   ·   {REV}   ·   {MONTH}", align=AL.CENTER, size=10, colour=D.GREY)
    D.pagebreak(d)


# ------------------------------------------------------------- how to use
def how_to_use(d):
    t = F.totals()
    js = _flows()
    today = datetime.date.today().isoformat()

    D.h(d, 1, "How to use this tutorial")

    D.p(d, "This tutorial teaches the concept design method of the Ibri sewerage scheme from end to "
           "end. It starts at the electricity meter on a plot and ends at a sized, self-cleansing "
           "gravity sewer, a sized treatment plant and the appraisal that chooses between options.")
    D.p(d, "It is written for the project's hydraulic engineer, and for anyone who has to check the "
           "work. The reader is assumed to know sewer design. What the tutorial adds is this "
           "project: every step made explicit, with its authority, a real Ibri number worked through "
           "it, and the place in the scripts where it is done.")
    D.p(d, "It is a reference, not a report. It is not addressed to the client. A number that goes "
           "to the client is taken from the current Concept Design Report, where the same method is "
           "stated in the client's terms.")

    # ---------------------------------------------------------- replaces
    D.h(d, 2, "What it replaces")
    D.p(d, "Tutorial T01 taught the sewage flow and load calculation, T02 the hydraulic design of a "
           "gravity sewer, and T03 Revision 01 the concept design methodology. T04 carries all "
           "three. The older tutorials stay unchanged as the record of what was taught at the time. "
           "Where one of them disagrees with T04, T04 governs, and the chapter concerned says in one "
           "sentence what changed. The changes a reader of the older tutorials will meet most often "
           "are these.")
    D.tab_caption(d, "What changed from the earlier tutorials")
    D.table(d, ["Topic", "T01 to T03 taught", "T04 teaches"],
            [["Occupancy rate", "One rate for the whole study area: 5 persons per property (T01, T02) "
                                "and 5.32 (Concept Design Report R1; T03 Revision 01 gives the method "
                                "but prints no value)",
              f"A rate for each settlement: its {F.BASE_YEAR} population divided by its counted "
              f"properties, never below {F.OR_FLOOR:.1f} (project rule)"],
             ["Load of a plot", "A flat load per property",
              f"The plot's own meters: homes at occupancy × {F.LPCD:.0f} l/d per person; shops and "
              "government at a unit rate per meter, from the settlement's "
              f"{F.R_ND * 100:.0f} % and {F.R_GOV * 100:.0f} % shares (G201-p60)"],
             ["The street pipe", "\"Lateral\"",
              "\"Secondary main sewer\" (G203-p17, p21). \"Lateral\" means only the tertiary pipe "
              "from the house connection to the main sewer (G203-p22 Tab 6)"],
             ["Connection ratio", "Applied along the projected series",
              f"Applied only to the {js['rules']['opening_year']} self-cleansing case. Pipes and "
              "plant are sized at 100 % connection (G201-p73)"],
             ["Minimum gradient",
              "The steeper of the G203 Table 11 gradient and the tractive-force gradient governs "
              "(G203-p27)",
              "At the concept stage, the Table 11 minimum (G203-p29; tertiary pipes G203-p18 Tab 5), "
              "rounded up to steps of 0.05 % on secondary pipes and 0.025 % on primary trunks of DN500 "
              "and up. The tractive force sets no gradient until NWS confirms τ (project rule, a "
              "declared departure)"],
             ["Self-cleansing check",
              "Both tests at the design peak flow; the opening years covered by a washing schedule, "
              "with no test naming the pipes that need it",
              f"Tested on the {js['rules']['opening_year']} × "
              f"{float(js['rules']['connection_ratio_2030']):.2f} low case, with no infiltration. "
              "Three classes: velocity pass, tractive pass at τ = 1 Pa, and needs washing, which is the "
              "flushing list (G203-p28). No regrade class and no low-flow threshold"]],
            widths=[3.2, 5.4, 8.0], font=9)

    # ----------------------------------------------------- reading paths
    D.h(d, 2, "Reading paths")
    D.table(d, ["If you want to", "Read"],
            [["See the whole chain in ten minutes", "The chain at a glance, which follows this section"],
             ["Carry out one step correctly", "The chapter for that step. Each is self-contained"],
             ["Check a number before it goes to the client",
              "The step's \"where it lives\" part, then the field in the layer, then the guideline page"],
             ["Know where the guidelines are silent, wrong or departed from",
              "Chapter 24, and the caution boxes throughout"],
             ["Rerun the chain after the data changes", "Appendix A"]],
            widths=[7.2, 9.4], font=9.5)

    # ------------------------------------------------------- five parts
    D.h(d, 2, "The five parts of every step")
    D.p(d, "Every step is written in the same five parts, in the same order, so the tutorial can be "
           "read by its shape.")
    D.numbered(d, "One or two sentences on why the step exists and what it feeds.",
               lead="What it is for. ", restart=True)
    D.numbered(d, "The equation, numbered and followed by a table of every symbol with its meaning "
                  "and unit; or the decision rule, stated exactly.", lead="The rule. ")
    D.numbered(d, "The guideline and page; or \"project rule\" with who decided it and when; or "
                  "\"outside assumption\" with where it comes from and its tag.", lead="The source. ")
    D.numbered(d, "A real number from the live data, carried through the rule so the arithmetic can "
                  "be followed by hand.", lead="A worked Ibri number. ")
    D.numbered(d, "The script that does the step and the field or sheet that holds the result, so "
                  "the number can be found in the layer and checked.", lead="Where it lives. ")
    D.p(d, "Each chapter ends with a short list headed \"Check it yourself\": what to open, what to "
           "sum or filter, and what the answer should be.")

    # ------------------------------------------------- where numbers come from
    D.h(d, 2, "Where the numbers come from")
    D.p(d, "Every Ibri number in this tutorial is read from the outputs of the load chain at the "
           "moment the document is built: the plot layer, the settlement layer, the growth workbook "
           "and the design-flow file. None is typed in. When the data changes and the chain is "
           "rerun, the tutorial is rebuilt and its numbers change with it. The method does not.")
    D.p(d, f"This copy read the data on {today}. On that reading the study area holds "
           f"{F.fmt(t['pop_today'])} people in {F.BASE_YEAR}, the sum of the population by year "
           "sheet of the growth workbook. A later copy may print a different figure for the same "
           "sentence.")
    D.p(d, "Two consequences follow. Quote the method from this tutorial, but quote a number only "
           "from the current report or from the layer itself. And a number that does not come from "
           "the data, such as a guideline constant or a value read from a table, carries its page "
           "beside it every time it appears.")
    D.p(d, "Numbers are rounded half up and printed with a thousands separator, so a total prints "
           "the same wherever it appears.")

    # ---------------------------------------------------------- page refs
    D.h(d, 2, "How guideline pages are cited")
    D.p(d, "A guideline value is cited by document and page, for example G203-p26. Where a table "
           "or section number helps to find it, that follows: G203-p27 Tab 10. The page is the one "
           "printed at the foot of the guideline, \"Page 26 of 201\". In G201 and G203 the printed "
           "page and the PDF page number are the same, so the page box of the viewer goes straight "
           "to it.")
    D.tab_caption(d, "Guideline page references")
    D.table(d, ["Written here", "Older project files", "Document"],
            [["G201-p##", "G1-p##", "PAM-GUD-201 General Design Guidelines v1.0, 152 pages"],
             ["G202-p##", "G2-p##", "PAM-GUD-202 Water and TSE Design Guidelines v1.0, 177 pages"],
             ["G203-p##", "p## (no prefix)", "PAM-GUD-203 Wastewater Design Guidelines v1.0, 201 pages"]],
            widths=[2.8, 3.4, 10.4], font=9)
    D.p(d, "The older shorthand survives in the scripts and the design criteria register. It points "
           "to the same pages.")
    D.callout(d, "Nothing is quoted from memory.",
              "Every guideline value in this tutorial was read from the page of the guideline. "
              "Equations were read from the page image, because the text layer of these PDFs mangles "
              "fraction bars, roots and exponents, and some equations exist only as pictures. The "
              "tractive-force equation of G203-p27 is one of them.",
              fill="EAF1F8", colour=D.MID)

    # ------------------------------------------------------ kinds of value
    D.h(d, 2, "Three kinds of value, and how to tell them apart")
    D.p(d, "Every value in the design is one of three kinds. The kind decides who may change it and "
           "what happens if it is wrong, so the source line of every step says which kind it is.")
    D.tab_caption(d, "The three kinds of value")
    D.table(d, ["Kind", "What it is", "How it is marked", "Ibri example", "Who can change it"],
            [["**Guideline value**", "A number or rule printed in G201, G202 or G203",
              "Document and page", "0.75 m/s minimum velocity at peak flow (G203-p26)",
              "NWS. Any departure is declared and needs NWS agreement"],
             ["**Project rule**",
              "A decision made for this project where the guideline is silent or leaves a choice",
              "\"Project rule\", with who decided it and the date",
              f"Size on saturation; check self-cleansing on {js['rules']['opening_year']} × "
              f"{js['rules']['connection_ratio_2030']:.2f}; lay each pipe at its G203 Table 11 "
              "minimum in 0.05 % or 0.025 % steps (engineer, 2026-09-11)",
              "The engineer, recorded in the design criteria register; shown to the client"],
             ["**Outside assumption**",
              "A value from outside the three guidelines, used because a guideline requires a "
              "method and gives no value for it",
              "\"Outside assumption\", its origin and its gap number",
              "Tractive tension τ = 1 Pa for the G203-p27 test (Mara; GAP-9)",
              "Carried as a parameter until NWS confirms it"]],
            widths=[2.6, 3.8, 3.1, 4.3, 2.8], font=8.5)
    D.p(d, "The three fail in different ways. A wrong guideline value is a compliance error, and a "
           "reviewer will find it. A project rule is a decision the client is entitled to challenge, "
           "so it must be visible. An outside assumption is the dangerous one: once its tag is lost "
           "it reads as a guideline value, and nobody asks for it to be confirmed.")
    D.p(d, "A fourth label, pending data, marks something held out of the calculation until data "
           "arrives. It is not a value. Tanker deliveries are the main example: no filling-station "
           "records are held, so no flow in this tutorial contains them.")
    D.callout(d, "Where a formula is not NWS's, it says so.",
              "Several formulae an engineer expects to find are not written anywhere in the three "
              "guidelines: net present value, life cycle cost, total dynamic head, pump power, and "
              "the friction equations in written form. Each is attributed in this tutorial to its "
              "real source. Citing NWS for them would be a false reference.",
              fill="EAF1F8", colour=D.MID)
    D.callout(d, "Where the guideline is wrong, it is printed and flagged.",
              "The guidelines contain printing and arithmetic errors. This tutorial prints what the "
              "guideline prints, then says plainly what is wrong with it. It does not silently "
              "correct the client's own standard. Chapter 24 lists them together.")

    # ---------------------------------------------------- where each step lives
    D.h(d, 2, "Where each step lives")
    D.p(d, "The table maps every chapter to the script that does the work and to the field or sheet "
           "where the result can be read. Scripts named without a folder are in W14/py. Where no "
           "script exists yet, the method lives in the section of the Concept Design Report named "
           "in the table.")
    D.tab_caption(d, "Where each step lives: the script and the field or sheet that holds the result")
    rows = [[c[0], c[1], _plain(c[3]), _plain(c[4])] for c in CHAPTERS]
    rows.append([APPENDIX[0], APPENDIX[1], _plain(APPENDIX[3]), _plain(APPENDIX[4])])
    D.table(d, ["Ch", "Step", "Script", "Main output: field or sheet"], rows,
            widths=[0.9, 4.0, 5.8, 5.9], font=8.5)
    D.callout(d, "The pipe-laying engine is behind the method in three places.",
              "Chapters 9 to 13 point to the network engine. First, it still loads every plot with "
              "one flat figure per property. Before any design run it has to read each plot's own "
              "saturation flow Q_ULT and opening-year flow Q_2030 from the plot layer. Second, it "
              "lays every gradient on a single 0.05 % grid (SLOPE_STEP = 0.0005 in criteria.py). The "
              "step has to be set by pipe size, 0.025 % for primary trunks of DN500 and up. Third, "
              "its self-cleansing audit tests the design flow and gives a pass or a fail. It has to "
              "test the low case, on the true flow without the 1.5 l/s floor of TRACTIVE_QMIN, and "
              "write one of the three classes on every pipe. Its layout results on the test boundary "
              "must still hold after these changes. Its flow results will be re-baselined.")

    # ------------------------------------------------------ abbreviations
    D.h(d, 2, "Abbreviations and symbols")
    D.table(d, ["Term", "Meaning"],
            [["Qadf", "Average daily dry-weather flow, m³/d (Ml/d in Merrimack, l/s in Peltier)"],
             ["QADF, Q_2030, Q_2055, Q_ULT",
              f"The plot's average sewage flow in {F.BASE_YEAR}, 2030, 2055 and at saturation, m³/d"],
             ["Qpdf, PF", "Peak flow, and the peak factor that turns an average flow into it"],
             ["OR", "Occupancy rate, persons per domestic property"],
             ["N_dom, N_nd, N_gov", "Domestic, non-domestic and governmental meters on a plot"],
             ["U_nd, U_gov", "Unit rate per non-domestic and per governmental meter, l/d"],
             ["d/D", "Proportional depth: depth of flow over pipe diameter"],
             ["DN", "Nominal diameter, mm"],
             ["τ", "Tractive tension on the pipe wall, Pa"],
             ["SLS", "Sewage lifting station"],
             ["TE, TSE", "Treated effluent (see the note below)"],
             ["NWS", "Nama Water Services, the client"],
             ["NCSI", "National Centre for Statistics and Information"],
             ["MoHUP", "Ministry of Housing and Urban Planning"],
             ["G201, G202, G203", "PAM-GUD-201 General Design, -202 Water and TSE, -203 Wastewater"]],
            widths=[4.2, 12.4], font=9)
    D.callout(d, "One term to be careful with.",
              "In G201 and G203, TE means trade effluent and TSE means treated sewage effluent. This "
              "project, its terms of reference and the tender use TE for treated effluent. Wherever "
              "this tutorial says TSE it means the treated product of the plant. Say so explicitly "
              "in anything sent to NWS, or a reviewer who knows the guidelines will read a trade "
              "effluent network into the design.")


# ---------------------------------------------------------------- summary
def summary(d):
    t = F.totals()
    js = _flows()
    fmt = F.fmt
    y0, ult = F.BASE_YEAR, t["ultimate"]
    y_open = int(js["rules"]["opening_year"])
    ratio = float(js["rules"]["connection_ratio_2030"])
    margin = float(js["rules"]["stp_margin"])
    props = js["properties"]
    ibri = next(r for r in F.settlement_table() if r["key"] == "IBRI")

    D.h(d, 1, "The chain at a glance", page_break=True)
    D.p(d, "The whole method on one page. Chapters 1 to 8 are one calculation, so an error in the "
           "count of properties or the occupancy rate reaches every flow downstream. Chapters 9 to 17 "
           "take the flow into the network, 18 to 20 to the plant, 21 to 23 decide what is built, and "
           "24 lists where the guidelines give no value.")
    D.picture(d, os.path.join(IMG, "D3_flow.png"), 9.5)
    D.fig_caption(d, "Derivation of the design flow, from the meters on a plot to the flow in each "
                     "pipe and at the plant")
    for c in CHAPTERS:
        D.numbered(d, c[2], lead=f"{c[1]}. ", restart=(c[0] == "1"))
    D.rich(d, ("Appendix A   ", {"bold": True}), (f"{APPENDIX[1]}. ", {"bold": True}),
           (APPENDIX[2], {}))

    # ---------------------------------------------------------- headline numbers
    D.h(d, 2, "The headline numbers")
    D.p(d, "The table gives the numbers the rest of the tutorial keeps returning to. They are "
           "average dry-weather flows summed over the study area, read from the growth workbook "
           "and the design-flow file on this build.")
    D.tab_caption(d, "Headline population and average flow, study area (concept stage)")
    rows = [
        ["Today", str(y0), fmt(t["pop"][y0]), fmt(t["q"][y0]), "The base year of the meters and the census"],
        ["Opening year", str(y_open), fmt(t["pop"][y_open]), fmt(t["q"][y_open]), "The first model year"],
        ["Opening year, low case", str(y_open),
         f"{fmt(t['pop'][y_open] * ratio)} connected", fmt(t["q"][y_open] * ratio),
         f"Self-cleansing only: {y_open} flow × {ratio:.2f} connected, no infiltration "
         "(project rule)"],
        ["Model year", "2055", fmt(t["pop"][2055]), fmt(t["q"][2055]), "Model year; plant phasing"],
        ["**Saturation**", f"**{ult}**", f"**{fmt(t['pop_ult'])}**", f"**{fmt(t['q_ult'])}**",
         "**Pipe size and capacity**, at 100 % connection (G201-p73)"],
        ["Plant at saturation", str(ult), "", fmt(t["q_ult"] * (1 + margin)),
         f"Saturation plus the {margin * 100:.0f} % margin for new plants (G201-p73)"],
        ["Capacity of the empty land", "", fmt(t["capacity"]), "",
         "The people the empty plots can still house"],
    ]
    D.table(d, ["Case", "Year", "People", "Qadf, m³/d", "Used for"], rows,
            widths=[4.1, 1.3, 3.0, 2.2, 6.0], font=9, align_right={1, 2, 3})

    if abs(t["pop_today"] + t["capacity"] - t["pop_ult"]) < 1.0:
        D.p(d, f"Saturation is today's population plus the capacity of the empty land: "
               f"{fmt(t['pop_today'])} + {fmt(t['capacity'])} = {fmt(t['pop_ult'])}. The growth rates "
               "decide the year the land is full. They do not decide how many people it finally holds; "
               "the land does.")
    else:
        D.p(d, f"Saturation holds {fmt(t['pop_ult'])} people against {fmt(t['pop_today'])} today and a "
               f"capacity of {fmt(t['capacity'])} on the empty land. The growth rates decide the year the "
               "land is full; the land decides how many people it finally holds.")
    D.p(d, f"The domestic properties number {fmt(props['y2024'])} in {y0}, {fmt(props['y2030'])} in "
           f"{y_open} and {fmt(props['ultimate'])} at saturation. Their count upstream of a pipe decides "
           f"which peak-factor formula applies to it. The sizing case counts the properties standing at "
           f"saturation. The low case counts only the connected ones, the {y_open} properties × "
           f"{ratio:.2f}, which is {fmt(props['y2030'] * ratio)} over the study area (project rule). "
           f"Ibri, the largest settlement, is full in "
           f"{ibri['sat_year']}; the last settlement fills in {ult}, and that year is saturation.")
    D.callout(d, "These are concept-stage figures.",
              "They are average dry-weather flows. They contain no peak and no infiltration. Both "
              "are added pipe by pipe in the design, the infiltration to the sizing case only and "
              "never to the low case. They contain no plant margin except in the plant row, and no "
              "tanker deliveries and no private wells, which are pending data. "
              f"{fmt(js['free_meters']['count'])} meters lie more than 15 m from any plot and carry no "
              "load in the plot table. Every figure here changes when the data changes. Quote the "
              "current report, not this page.")

    # ------------------------------------------------ how a pipe is laid and tested
    _rulings(js)
    fine, coarse, deeper, tenth = _dn900()
    f2 = lambda x: F.fmt(x, 2)
    D.h(d, 2, "How a pipe is laid and tested")
    D.p(d, "Two project rules govern the network at the concept stage. The first sets the gradient of "
           "every pipe. The second tests each pipe for self-cleansing on the low case and sorts it into "
           "one of three classes. Chapters 11 and 12 carry them in full.")
    D.numbered(d, "Every pipe is laid at its G203 Table 11 minimum gradient (G203-p29), and a tertiary "
                  "pipe at its Table 5 minimum (G203-p18). The gradient is rounded up to a step of "
                  "0.05 % (0.5 mm/m) on secondary pipes and 0.025 % (0.25 mm/m) on primary trunks of "
                  "DN500 and up. A round step can be built, and it can be read off a profile or a map. "
                  "The trunk step is finer because the trunk minimums are small. A DN900 trunk at its "
                  f"{f2(T11_DN900)} mm/m minimum (G203-p29 Tab 11) stays at {f2(fine)} mm/m on the "
                  f"0.025 % step. A single 0.05 % grid would lay it at {f2(coarse)} mm/m, "
                  f"{F.fmt(deeper)} mm deeper for every kilometre. A step of a tenth of each minimum is "
                  f"not used: on a DN900 it changes the fall of a 100 m pipe by {F.fmt(tenth, 1)} mm, "
                  f"well inside the {F.fmt(TOLERANCE_MM)} mm line-and-level tolerance of G203-p29.",
               lead="The gradient. ", restart=True)
    D.numbered(d, f"Each pipe is then tested, as laid, on the low case: the {y_open} flow of the plots "
                  f"upstream × {ratio:.2f}, peaked on the connected property count (Merrimack over 100 "
                  "properties, G201-p71; Peltier at 100 or fewer, G201-p72), with no infiltration. "
                  "Infiltration is left out because G201 §7.4.3 sets the allowance for new networks "
                  "and says nothing of the opening years (G201-p72), and §7.4.4 asks only that "
                  "self-cleaning velocities be ensured at the initial stage of operations (G201-p73). "
                  "The pipe falls in the first of these classes it meets.",
               lead="The self-cleansing audit. ")
    D.bullet(d, "The velocity at the low-case peak reaches 0.75 m/s (G203-p26). Nothing to do.",
             lead="Velocity pass. ", level=1)
    D.bullet(d, "The laid gradient is at least the Mara tractive slope Smin at τ = 1 Pa, with "
                "K = 2.33 × 10⁻⁴ for Q in m³/s, computed on the true low-case peak flow with no lower "
                "limit (G203-p27). Nothing to do.", lead="Tractive pass. ", level=1)
    D.bullet(d, "Everything else. The pipe goes on the flushing list for the operator (G203-p28, "
                "§4.2.6).", lead="Needs washing. ", level=1)
    D.p(d, "There is no regrade class. A pipe laid to the guideline gradient that still carries too "
           "little flow needs washing, not a steeper pipe. There is no low-flow threshold either. The "
           "1.5 l/s figure of the simplified-sewerage literature is not in G203 and is not used. The "
           "class is decided at τ = 1 Pa.")
    D.callout(d, "One of these rules departs from the guideline, and NWS is asked to confirm it.",
              "G203 §4.2.2.1 (G203-p25 to p27) says the self-cleansing velocity and the minimum "
              "tractive force shall both be used, and the steeper of the two gradients shall be the "
              "minimum. In this project the tractive force sets no gradient at the concept stage. It "
              "is used only as the second test of the audit. It will be applied to the gradients at "
              "the preliminary design, once NWS confirms the tractive tension τ, for which G203 gives "
              "no value (GAP-9). The departure is declared in Section 10.1 of the Concept Design "
              "Report R2.")
