"""The options appraisal method for this project, drawn on a stated grid.

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
    c = Chart(5, 5, cw=252, rh=118, gx=40, gy=40, pad=72,
              title="How each option is costed and compared")

    # the options govern the costing, so they sit to the left of it
    c.node("opt", 0, 0,
           "THREE OPTIONS|for each system,|plus OPTION 0,|do nothing.||"
           "Each is costed|separately, on|the same basis.",
           "start", height=3)

    # ---- stream 1, what it costs to build ---------------------------
    c.node("a1", 1, 0, "Gravity sewers by|diameter AND depth band")
    c.node("a2", 2, 0, "Manholes, house connections,|force mains, lifting stations")
    c.node("a3", 3, 0, "STP per m3/day, TE network,|land, NOCs, diversions")
    c.node("A", 4, 0, "STEP 1  CAPEX|phased over the build", "tint")

    # ---- stream 2, what it costs to run -----------------------------
    c.node("b1", 1, 1, "Energy: pumping, and|aeration at the plant")
    c.node("b2", 2, 1, "Sludge, chemicals, labour,|jetting and CCTV")
    c.node("b3", 3, 1, "Replacing M and E plant|inside the 25 years")
    c.node("B", 4, 1, "STEP 2  OPEX|built bottom-up", "tint")

    # ---- stream 3, what comes in ------------------------------------
    c.node("c1", 1, 2, "Treated effluent sold,|capped by irrigation demand")
    c.node("c2", 2, 2, "Sewerage and connection|charges, if NWS levies them")
    c.node("c3", 3, 2, "Avoided cost: tankers, septic|emptying, deferring a plant")
    c.node("C", 4, 2, "STEP 3  Revenue and|avoided cost", "tint")

    # ---- the money question, across the full width ------------------
    c.node("npv", 0, 3,
           "STEP 4   Discount every flow back to today at 5 % over 25 years:  "
           "NET PRESENT VALUE and LIFE-CYCLE COST|"
           "Payback is reported alongside them, but it does not decide.",
           "tint", span=5)

    # ---- the judgement, wrapped onto its own band -------------------
    c.node("s5", 0, 4, "STEP 5|Score the|seven criteria")
    c.node("s6", 1, 4, "STEP 6|Apply the weights|NWS sets")
    c.node("s7", 2, 4, "STEP 7|Sensitivity: weights,|discount rate, criteria")
    c.node("s8", 3, 4, "STEP 8|Within 10 % on cost,|the greener option wins")
    c.node("s9", 4, 4, "STEP 9|RECOMMENDED OPTION,|one for each system",
           "accent")

    for a, b in (("opt", "a1"), ("opt", "b1"), ("opt", "c1"),
                 ("a1", "a2"), ("a2", "a3"), ("a3", "A"),
                 ("b1", "b2"), ("b2", "b3"), ("b3", "B"),
                 ("c1", "c2"), ("c2", "c3"), ("c3", "C"),
                 ("s5", "s6"), ("s6", "s7"), ("s7", "s8"), ("s8", "s9")):
        c.edge(a, b)

    # the three streams collect on a bus down the right edge and enter step 4
    # from its right end; step 4 leaves from its left and drops into step 5.
    # The page then reads as one continuous line that turns at each edge,
    # instead of three arrows cutting back through the middle of the figure.
    for k in ("A", "B", "C"):
        c.edge(k, "npv", side=("r", "r"))
    c.edge("npv", "s5", side=("l", "l"))

    render(c, "appraisal_method", DOCS)
    png = os.path.join(DOCS, "appraisal_method.png")
    shutil.copy(png, os.path.join(REPORT, "appraisal_method.png"))
    return png


if __name__ == "__main__":
    os.makedirs(DOCS, exist_ok=True)
    appraisal()
