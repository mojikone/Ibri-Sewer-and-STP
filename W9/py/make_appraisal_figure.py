"""The options appraisal method for this project, drawn on a stated grid.

The portrait alternative, for when the figure has to fit a report column.

The left-to-right version reads more easily — the three streams visibly
converge and the eye holds one direction — so that one is the reference copy.
This one folds the same content into an aspect near 1.0 by turning the flow
downwards, which costs some of that legibility. Use it only where the page
shape demands it.

Re-runnable; writes into W9/docs/img/.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "report"))

from flow import Chart, render                       # noqa: E402

OUT = os.path.join(HERE, "..", "docs", "img")


def appraisal():
    c = Chart(4, 7, cw=252, rh=112, gx=40, gy=38,
              title="How the options are compared")

    # ---- the options come first, not after the costing --------------
    c.node("opt", 0, 0,
           "THREE OPTIONS for each system, plus OPTION 0, do nothing.|"
           "Every one is costed separately, on the same basis.",
           "start", span=4)

    # ---- stream 1, what it costs to build ---------------------------
    # two lines per box: three overflows the frame at this wrap width
    c.node("a1", 0, 1, "Gravity sewers by|diameter AND depth band")
    c.node("a2", 1, 1, "Manholes, house connections,|force mains, lifting stations")
    c.node("a3", 2, 1, "STP per m3/day, TE network,|land, NOCs, diversions")
    c.node("A", 3, 1, "STEP 1  CAPEX|phased over the build", "tint")

    # ---- stream 2, what it costs to run -----------------------------
    c.node("b1", 0, 2, "Energy: pumping, and|aeration at the plant")
    c.node("b2", 1, 2, "Sludge, chemicals, labour,|jetting and CCTV")
    c.node("b3", 2, 2, "Replacing M and E plant|inside the 25 years")
    c.node("B", 3, 2, "STEP 2  OPEX|built bottom-up", "tint")

    # ---- stream 3, what comes in ------------------------------------
    c.node("c1", 0, 3, "Treated effluent sold,|capped by irrigation demand")
    c.node("c2", 1, 3, "Sewerage and connection|charges, if NWS levies them")
    c.node("c3", 2, 3, "Avoided cost: tankers, septic|emptying, deferring a plant")
    c.node("C", 3, 3, "STEP 3  Revenue and|avoided cost", "tint")

    # ---- the money question -----------------------------------------
    c.node("npv", 0, 4,
           "STEP 4   Discount every flow back to today at 5 % over 25 years:|"
           "NET PRESENT VALUE and LIFE-CYCLE COST.|"
           "Payback is reported, but it does not decide.",
           "tint", span=4)

    # ---- the judgement half, given equal weight ---------------------
    c.node("s5", 0, 5, "STEP 5|Score the seven criteria")
    c.node("s6", 1, 5, "STEP 6|Apply the weights NWS sets")
    c.node("s7", 2, 5, "STEP 7|Sensitivity: weights,|discount rate, criteria")
    c.node("s8", 3, 5, "STEP 8|Within 10 % on cost,|the greener option wins")

    c.node("rec", 0, 6,
           "STEP 9   RECOMMENDED OPTION, one for each system:|"
           "the sewer network, the treated effluent network and the plant",
           "accent", span=4)

    # ---- edges -------------------------------------------------------
    for a, b in (("a1", "a2"), ("a2", "a3"), ("a3", "A"),
                 ("b1", "b2"), ("b2", "b3"), ("b3", "B"),
                 ("c1", "c2"), ("c2", "c3"), ("c3", "C")):
        c.edge(a, b)
    for k in ("A", "B", "C"):
        c.edge(k, "npv")
    c.edge("npv", "s5")
    for a, b in (("s5", "s6"), ("s6", "s7"), ("s7", "s8")):
        c.edge(a, b)
    c.edge("s8", "rec")

    return render(c, "appraisal_method_portrait", OUT)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    appraisal()
