"""W17 copy of W16/py/make_appraisal_figure.py: the three options are each costed under the three characters of the
guidelines, nine cases, and the appraisal recommends a case (engineer, 2026-10-03). Earlier: the W14 copy of
W9/py/make_appraisal_figure.py (W9 is frozen), where the STEP 9 label no longer overflows its box.
The options appraisal method for this project, drawn on a stated grid.

Left to right, because that is what reads: the three cost streams visibly
converge and the eye holds one direction. The FigJam draft had the same shape
but two faults — the options entered after the costing instead of governing it,
and steps 5 to 9 trailed off in a long horizontal tail that left a third of the
page empty. Here the options sit on the left and the tail wraps onto a second
band, so the figure fills an A3 landscape page at a legible box size.

Re-runnable; writes into W9/docs/img/ and W9/report/img/.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "report"))

from flow import Chart, render                       # noqa: E402

DOCS = os.path.join(HERE, "..", "docs", "img")
REPORT = os.path.join(HERE, "..", "report", "img")


def appraisal():
    # W17 R7 (engineer, 2026-10-04): the comparison as it was made: every option costed on one basis, discounted to its
    # whole-life cost, the 10 % band, then sustainability and operability; the characters at the preliminary design
    c = Chart(5, 4, cw=252, rh=118, gx=40, gy=40, pad=72,
              title="How each option is costed and compared")

    c.node("opt", 0, 0,
           "SEVEN OPTIONS|for where the flow|is treated.||"
           "Each is costed|on its own quantities,|at the same rates.",
           "start", height=2)

    # ---- what it costs to build ------------------------------------
    c.node("a1", 1, 0, "Gravity sewers by|diameter AND depth band")
    c.node("a2", 2, 0, "Manholes by type and depth;|pumping stations by power")
    c.node("a3", 3, 0, "Rising mains by diameter;|plants by capacity band")
    c.node("A", 4, 0, "STEP 1  CAPEX", "tint")

    # ---- what it costs to run --------------------------------------
    c.node("b1", 1, 1, "Maintenance and operation,|1 % of CAPEX a year")
    c.node("b2", 2, 1, "Power of the stations|and the plants")
    c.node("b3", 3, 1, "Land rent and staff|of the plants and stations")
    c.node("B", 4, 1, "STEP 2  OPEX|escalated 5 % a year", "tint")

    # ---- the money question, across the full width -----------------
    c.node("npv", 0, 2,
           "STEP 3   Discount 25 years of cost back to today at 5 %:  WHOLE-LIFE COST",
           "tint", span=5)

    # ---- the judgement ---------------------------------------------
    c.node("s4", 0, 3, "STEP 4|Options within 10 %|of the lowest go on")
    c.node("s5", 1, 3, "STEP 5|Within the band,|the greener option")
    c.node("s6", 2, 3, "STEP 6|Equal within concept|accuracy: operability")
    c.node("s7", 3, 3, "STEP 7|Weights set|by NWS")
    c.node("s8", 4, 3, "RECOMMENDED|OPTION", "accent")

    for a, b in (("opt", "a1"), ("opt", "b1"),
                 ("a1", "a2"), ("a2", "a3"), ("a3", "A"),
                 ("b1", "b2"), ("b2", "b3"), ("b3", "B"),
                 ("s4", "s5"), ("s5", "s6"), ("s6", "s7"), ("s7", "s8")):
        c.edge(a, b)

    for k in ("A", "B"):
        c.edge(k, "npv", side=("r", "r"))
    c.edge("npv", "s4", side=("l", "l"))

    render(c, "appraisal_method", DOCS)
    png = os.path.join(DOCS, "appraisal_method.png")
    shutil.copy(png, os.path.join(REPORT, "appraisal_method.png"))
    return png


if __name__ == "__main__":
    os.makedirs(DOCS, exist_ok=True)
    appraisal()
