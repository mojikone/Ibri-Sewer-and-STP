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
    """Revision 2: from the plot to the pipe. The plot carries an average
    flow for each year; peaking belongs to the pipe and the plant."""
    c = Chart(3, 5, cw=254, rh=100, gx=42, gy=30,
              title="Derivation of the design flow")
    c.node("pl", 0, 0, "Plot: dwelling meters|x occupancy = people", "start")
    c.node("de", 1, 0, "Water per person|164, 36 and 23 l/d")
    c.node("rt", 2, 0, "Return rates|85 % and 54 %")
    c.node("sp", 2, 1, "Industrial estates|workers x 93 l/d", "tint")
    c.node("ww", 1, 1, "Average sewage|per plot, each year")
    c.node("gr", 0, 1, "Growth: empty plots|fill to saturation")
    c.node("su", 1, 2, "Sum of the plots|upstream of each pipe")
    c.node("inf", 0, 2, "Infiltration|720 l/d per km")
    c.node("pk", 2, 2, "Peak factor|Merrimack")
    c.node("f", 1, 3, "DESIGN FLOW|in each pipe", "accent")
    c.node("tk", 2, 3, "Tanker deliveries", "tint")
    c.node("st", 1, 4, "Treatment plant: average,|maximum day, peak hour", "accent")

    c.edge("pl", "de")
    c.edge("de", "rt")
    c.edge("rt", "ww")
    c.edge("sp", "ww")
    c.edge("gr", "ww")
    c.edge("ww", "su")
    c.edge("inf", "su")
    c.edge("su", "pk")
    c.edge("pk", "f")
    c.edge("f", "st")
    c.edge("tk", "st")
    return render(c, "D3_flow", IMG)


def d6_landuse():
    """Revision 2: from the electricity meter to the use of the plot."""
    c = Chart(3, 5, cw=256, rh=104, gx=40, gy=32,
              title="From the electricity meter to the use of each plot")
    c.node("m", 0, 0, "33,971 electricity|meters, tariff only", "start")
    c.node("cat", 1, 0, "Tariff to category|domestic, non-domestic,|governmental, farm")
    c.node("crt", 2, 0, "499 large consumers|placed by public data", "tint")
    c.node("snap", 1, 1, "Meter to plot|inside, or nearest|within 15 m")
    c.node("est", 0, 2, "Inside an industrial|estate: industrial", "tint")
    c.node("farm", 1, 2, "Farm meter, or a grove|by satellite: farm")
    c.node("her", 2, 2, "Old quarter:|heritage, no load", "tint")
    c.node("prop", 1, 3, "Two thirds of the meters|decide: home, shop|or government")
    c.node("lu", 1, 4, "USE OF THE PLOT|seven classes", "accent")
    c.node("none", 2, 4, "No meter:|empty plot", "tint")

    c.edge("m", "cat")
    c.edge("crt", "cat")
    c.edge("cat", "snap")
    c.edge("snap", "est")
    c.edge("snap", "farm")
    c.edge("snap", "her")
    c.edge("farm", "prop")
    c.edge("prop", "lu")
    c.edge("est", "lu")
    c.edge("her", "lu")
    return render(c, "D6_landuse", IMG)


def d7_saturation():
    """Revision 2: from the empty plot to the saturation year."""
    c = Chart(3, 5, cw=256, rh=104, gx=40, gy=32,
              title="From the empty plot to the saturation year")
    c.node("b", 0, 0, "Built home plots|of the settlement", "start")
    c.node("r", 0, 1, "Properties per|home plot")
    c.node("hs", 1, 1, "Home share among|home-shaped plots")
    c.node("o", 2, 1, "Occupancy|2024 people / properties")
    c.node("e", 2, 0, "Empty plots|200 to 1,000 m2, compact", "start")
    c.node("cap", 1, 2, "CAPACITY|plots x share x ratio|x occupancy", "accent")
    c.node("g", 0, 3, "Growth rate|per settlement")
    c.node("fill", 1, 3, "Fill to capacity;|overflow to the|nearest neighbour")
    c.node("sat", 2, 3, "Year each|settlement fills", "accent")
    c.node("spr", 1, 4, "People spread over|all empty plots|by capped area")

    c.edge("b", "r")
    c.edge("b", "hs")
    c.edge("e", "hs")
    c.edge("e", "o")
    c.edge("r", "cap")
    c.edge("hs", "cap")
    c.edge("o", "cap")
    c.edge("g", "fill")
    c.edge("cap", "fill")
    c.edge("fill", "sat")
    c.edge("fill", "spr")
    return render(c, "D7_saturation", IMG)


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
    for fn in (d1_process, d2_data, d3_flow, d4_network, d5_options,
               d6_landuse, d7_saturation):
        fn()
