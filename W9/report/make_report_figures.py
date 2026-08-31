"""Process flowcharts for the Concept Design Report.

Drawn on a stated grid so each figure fits the text column and stays legible
at print size. Re-runnable; writes to img/.
"""
import os

from flow import Chart, render

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def d1_process():
    c = Chart(4, 4, cw=246, rh=104, gx=38, gy=34,
              title="Concept design process")
    c.node("d", 0, 0, "Data collection|and validation", "start")
    c.node("s", 1, 0, "Survey and|investigation", "start")

    c.node("b", 0, 1, "Design basis|and criteria")
    c.node("p", 1, 1, "Population|and land use")
    c.node("q", 2, 1, "Demand and|wastewater flow")
    c.node("f", 3, 1, "DESIGN FLOW", "accent")

    c.node("n", 0, 2, "Sewer network|options")
    c.node("t", 1, 2, "Treatment plant|options")
    c.node("e", 2, 2, "Treated effluent|network options")

    c.node("a", 1, 3, "Appraisal and|comparison", "pill")
    c.node("r", 2, 3, "Recommended|option", "accent")

    c.edge("d", "b")
    c.edge("s", "p")
    c.edge("b", "p")
    c.edge("p", "q")
    c.edge("q", "f")
    c.edge("f", "e")
    c.edge("f", "t")
    c.edge("f", "n")
    c.edge("n", "a")
    c.edge("t", "a")
    c.edge("e", "a")
    c.edge("a", "r")
    return render(c, "D1_process", IMG)


def d2_data():
    c = Chart(3, 4, cw=256, rh=110, gx=42, gy=34,
              title="Assessment of the data supplied")
    c.node("r", 1, 0, "Dataset received", "start")
    c.node("p", 1, 1, "Load, reproject and|check against the|project boundary")
    c.node("in", 0, 2, "Within the project area|and complete")
    c.node("part", 1, 2, "Within the area but|incomplete")
    c.node("out", 2, 2, "Outside the|project area")
    c.node("use", 0, 3, "Adopted for design", "accent")
    c.node("sur", 1, 3, "Completed by survey|or by request", "tint")
    c.node("rec", 2, 3, "Recorded, not used", "tint")

    c.edge("r", "p")
    c.edge("p", "in")
    c.edge("p", "part")
    c.edge("p", "out")
    c.edge("in", "use")
    c.edge("part", "sur")
    c.edge("out", "rec")
    return render(c, "D2_data", IMG)


def d3_flow():
    c = Chart(3, 5, cw=254, rh=100, gx=42, gy=30,
              title="Derivation of the design flow")
    c.node("pl", 0, 0, "Plots and counted|properties", "start")
    c.node("po", 1, 0, "Population")
    c.node("de", 2, 0, "Water demand|domestic, non-domestic|and governmental")
    c.node("rt", 2, 1, "Return rates|85 % and 54 %")
    c.node("ww", 2, 2, "Wastewater generated")
    c.node("cr", 1, 2, "Connection ratio|for the design year")
    c.node("pk", 0, 2, "Peak factor")
    c.node("inf", 0, 3, "Infiltration allowance")
    c.node("f", 1, 4, "DESIGN FLOW", "accent")
    c.node("tk", 2, 3, "Tanker deliveries", "tint")

    c.edge("pl", "po")
    c.edge("po", "de")
    c.edge("de", "rt")
    c.edge("rt", "ww")
    c.edge("ww", "cr")
    c.edge("cr", "pk")
    c.edge("pk", "inf")
    c.edge("inf", "f")
    c.edge("tk", "f")
    return render(c, "D3_flow", IMG)


def d4_network():
    c = Chart(3, 5, cw=254, rh=100, gx=42, gy=30,
              title="Network design approach")
    c.node("f", 1, 0, "Design flow at each point", "start")
    c.node("c", 1, 1, "Available corridors|dual carriageways excluded")
    c.node("g", 1, 2, "Gravity layout|laterals, sub-mains, trunk")
    c.node("q", 0, 3, "Excavation cost|prohibitive?", "tint")
    c.node("l", 0, 4, "Lifting station|and force main")
    c.node("k", 2, 3, "Check velocity, depth|of flow and cover")
    c.node("o", 2, 4, "Outfall to the|treatment plant", "accent")

    c.edge("f", "c")
    c.edge("c", "g")
    c.edge("g", "q")
    c.edge("g", "k")
    c.edge("q", "l", label="yes")
    c.edge("k", "o")
    c.edge("l", "o", side=("r", "l"))
    return render(c, "D4_network", IMG)


def d5_options():
    c = Chart(3, 4, cw=256, rh=108, gx=42, gy=34,
              title="Development and selection of options")
    c.node("a", 0, 0, "Sustainability-led|option", "start")
    c.node("b", 1, 0, "International|best practice", "start")
    c.node("c", 2, 0, "Established local|practice", "start")
    c.node("e", 1, 1, "Equivalent function,|reliability and redundancy")
    c.node("cost", 0, 2, "Capital and operating|cost, life cycle cost")
    c.node("sus", 2, 2, "Carbon, resource use|and in-country value")
    c.node("m", 1, 3, "Weighted comparison and|recommended option", "accent")

    c.edge("a", "e")
    c.edge("b", "e")
    c.edge("c", "e")
    c.edge("e", "cost")
    c.edge("e", "sus")
    c.edge("cost", "m")
    c.edge("sus", "m")
    return render(c, "D5_options", IMG)


if __name__ == "__main__":
    for fn in (d1_process, d2_data, d3_flow, d4_network, d5_options):
        fn()
