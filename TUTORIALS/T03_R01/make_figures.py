"""Draw every flowchart in the tutorial. Re-runnable; writes to img/."""
import os

from flow import Chart, render

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def f1_chain():
    c = Chart(4, 6, cw=260, rh=112, gx=40, gy=34,
              title="The concept design calculation chain")
    c.node("a", 0, 0, "MoHUP plots|+ electricity accounts", "start")
    c.node("b", 0, 1, "Clean plot layer|properties counted, land use assigned")
    c.node("c", 0, 2, "Population")
    c.node("d", 0, 3, "Water demand")
    c.node("e", 0, 4, "Wastewater generation")
    c.node("f", 0, 5, "Series to saturation|connection ratio applied")

    c.node("g", 1, 5, "Peak factor|and infiltration")
    c.node("h", 2, 5, "DESIGN FLOW", "accent")

    c.node("i", 2, 3, "Gravity network|diameter, gradient, depth")
    c.node("j", 2, 1, "Treatment plant|capacity and phasing")
    c.node("k", 3, 3, "Lifting stations|only where gravity fails")
    c.node("l", 3, 1, "Treated effluent|95 % of inflow")
    c.node("m", 3, 0, "Sludge|0.25 kg per m3")
    c.node("n", 2, 0, "Three options,|life cycle cost,|appraisal", "pill", span=1)

    for a, b in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "f")]:
        c.edge(a, b)
    c.edge("f", "g")
    c.edge("g", "h")
    c.edge("h", "i")
    c.edge("i", "k")
    c.edge("i", "j", side=("t", "b"))
    c.edge("j", "l")
    c.edge("l", "m", side=("t", "b"))
    c.edge("m", "n")
    return render(c, "F1_chain", IMG)


def f2_data():
    c = Chart(3, 4, cw=262, rh=114, gx=46, gy=36,
              title="Building the plot layer from electricity accounts")
    c.node("p", 0, 0, "MoHUP plot layer|geometry only", "start")
    c.node("e", 2, 0, "Electricity accounts|tariff and coordinate", "start")
    c.node("j", 1, 1, "Spatial join")
    c.node("in", 0, 2, "Inside a plot|assign to that plot")
    c.node("out", 2, 2, "Inside no plot|leave unassigned")
    c.node("gis", 2, 3, "Wait for the corrected|plot layer, then assign|nearest empty plot", "tint")
    c.node("res", 0, 3, "Properties per plot|and land use", "accent")

    c.edge("p", "j")
    c.edge("e", "j")
    c.edge("j", "in")
    c.edge("j", "out")
    c.edge("in", "res")
    c.edge("out", "gis")
    c.edge("gis", "res", side=("l", "r"))
    return render(c, "F2_data", IMG)


def f3_population():
    c = Chart(3, 4, cw=260, rh=114, gx=46, gy=36,
              title="Two routes to population, and what each is for")
    c.node("n", 0, 0, "NCSI census series", "start")
    c.node("p", 2, 0, "Counted plots and|properties", "start")
    c.node("d", 0, 1, "Disaggregate to settlement|by census share")
    c.node("o", 2, 1, "Occupancy rate|population / housing units")
    c.node("y", 0, 2, "Population at|a dated year")
    c.node("s", 2, 2, "Saturation population|the ceiling")
    c.node("stp", 0, 3, "Sizes the plant|built in phases", "tint")
    c.node("pipe", 2, 3, "Sizes the pipes|laid once, for 50 years", "tint")

    c.edge("n", "d")
    c.edge("d", "y")
    c.edge("y", "stp")
    c.edge("p", "o")
    c.edge("o", "s")
    c.edge("s", "pipe")
    c.note(1, 3, "Both routes are required, and the guideline asks that they be "
                 "reconciled with NWS where they disagree", span=1)
    return render(c, "F3_population", IMG)


def f4_demand():
    c = Chart(3, 5, cw=260, rh=108, gx=46, gy=32,
              title="Assembling water demand, and choosing the tier")
    c.node("pop", 1, 0, "Population", "start")
    c.node("dom", 1, 1, "Domestic|population x 164 l/c/d")
    c.node("q", 1, 2, "Is detailed land use|available with quantities?", "tint")
    c.node("a", 0, 3, "Tier A|+22 % non-domestic|+14 % government")
    c.node("b", 2, 3, "Tier B|Table 12 unit rates|per pupil, bed, m2")
    c.node("add", 1, 4, "Add separately: identified projects, special|"
                        "consumption, tankers, private wells", "accent", span=1)

    c.edge("pop", "dom")
    c.edge("dom", "q")
    c.edge("q", "a", label="no")
    c.edge("q", "b", label="yes")
    c.edge("a", "add")
    c.edge("b", "add")
    c.note(0, 4, "Never both. Applying|unit rates and the uplifts|counts the "
                 "same water twice", span=1)
    c.note(2, 4, "Ibri is Tier A: no floor|areas, pupil counts or bed|numbers "
                 "exist in any dataset", span=1)
    return render(c, "F4_demand", IMG)


def f5_flow():
    c = Chart(3, 4, cw=262, rh=112, gx=46, gy=36,
              title="From demand to the flow the pipe is sized on")
    c.node("d", 0, 0, "Water demand|by category", "start")
    c.node("r", 0, 1, "Apply return rates|85 % domestic and tanker|54 % other")
    c.node("w", 0, 2, "Wastewater generated")
    c.node("c", 1, 2, "Apply connection ratio|for the year in question")
    c.node("p", 2, 2, "Apply peak factor|Merrimack, in Ml/d")
    c.node("i", 2, 1, "Add infiltration|720 l/d per km")
    c.node("f", 2, 0, "DESIGN FLOW", "accent")

    c.edge("d", "r")
    c.edge("r", "w")
    c.edge("w", "c")
    c.edge("c", "p")
    c.edge("p", "i")
    c.edge("i", "f")
    c.note(0, 3, "Infiltration is added after peaking, not before: a steady "
                 "leak does not peak with the diurnal cycle", span=3)
    return render(c, "F5_flow", IMG)


def f6_gravity():
    c = Chart(3, 5, cw=258, rh=108, gx=46, gy=32,
              title="Sizing a gravity sewer run")
    c.node("q", 1, 0, "Design flow for the run", "start")
    c.node("d", 1, 1, "Choose diameter|200 mm minimum")
    c.node("s", 1, 2, "Set gradient|not below the Table 11 minimum")
    c.node("c1", 0, 3, "Velocity above 0.75 m/s|AT PEAK FLOW")
    c.node("c2", 2, 3, "Tractive force|steeper of the two governs")
    c.node("ok", 1, 4, "Check d/D, maximum velocity,|cover and manhole spacing",
           "accent")

    c.edge("q", "d")
    c.edge("d", "s")
    c.edge("s", "c1")
    c.edge("s", "c2")
    c.edge("c1", "ok")
    c.edge("c2", "ok")
    c.note(0, 0, "Table 11 gradients deliver|0.75 m/s FULL BORE. The rule is|"
                 "at peak flow. Check both.", span=1)
    c.note(2, 0, "No value of shear stress|in pascals exists in any|"
                 "NWS guideline. Agree one.", span=1)
    return render(c, "F6_gravity", IMG)


def f7_pumping():
    c = Chart(3, 4, cw=260, rh=112, gx=46, gy=36,
              title="When a lifting station is required")
    c.node("g", 1, 0, "Gravity route considered first", "start")
    c.node("q", 1, 1, "Is excavation cost|becoming prohibitive?", "tint")
    c.node("no", 0, 2, "Stay in gravity|re-search the route")
    c.node("yes", 2, 2, "Lifting station|+ force main to the|nearest gravity point")
    c.node("out", 1, 3, "Continue by gravity to the outfall", "accent")

    c.edge("g", "q")
    c.edge("q", "no", label="no")
    c.edge("q", "yes", label="yes")
    c.edge("no", "out")
    c.edge("yes", "out")
    c.note(0, 0, "The trigger is COST,|not depth. 10 to 12 m is|a recommendation "
                 "about cover.", span=1)
    c.note(2, 0, "The guideline requires|pumping be avoided wherever|"
                 "gravity is feasible.", span=1)
    return render(c, "F7_pumping", IMG)


def f8_stp():
    c = Chart(3, 5, cw=258, rh=108, gx=46, gy=32,
              title="Sizing and phasing the treatment plant")
    c.node("f", 1, 0, "Design flow + 10 % margin", "start")
    c.node("l", 1, 1, "Influent load|60 g BOD, 80 g SS per person|plus tankers")
    c.node("s", 0, 2, "Size category|large at 20,000 m3/d")
    c.node("q", 2, 2, "Effluent standard|Class A, and TN below 15")
    c.node("t", 1, 3, "Technology selection|multicriteria, land area per m3/d")
    c.node("p", 1, 4, "Phasing, land take, buffer from|odour modelling", "accent")

    c.edge("f", "l")
    c.edge("l", "s")
    c.edge("l", "q")
    c.edge("s", "t")
    c.edge("q", "t")
    c.edge("t", "p")
    c.note(0, 4, "Large plant: CFD required,|buffer 300 to 1000 m from|"
                 "the 5 OU contour", span=1)
    c.note(2, 4, "Total nitrogen, not BOD,|drives the process. Full|"
                 "denitrification is forced.", span=1)
    return render(c, "F8_stp", IMG)


def f9_options():
    c = Chart(3, 4, cw=262, rh=112, gx=46, gy=36,
              title="Options appraisal and the recommendation")
    c.node("a", 0, 0, "Nature-based|option", "start")
    c.node("b", 1, 0, "International|best in class", "start")
    c.node("c", 2, 0, "Standard Omani|practice", "start")
    c.node("e", 1, 1, "Equivalent function,|reliability and redundancy")
    c.node("cost", 0, 2, "CAPEX, OPEX|life cycle cost at 5 %|over 25 years")
    c.node("carb", 2, 2, "Carbon, circular economy|in-country value")
    c.node("m", 1, 3, "Weighted appraisal, NWS sets the weights|"
                      "Within 10 % on cost, the greener option wins", "accent")

    c.edge("a", "e")
    c.edge("b", "e")
    c.edge("c", "e")
    c.edge("e", "cost")
    c.edge("e", "carb")
    c.edge("cost", "m")
    c.edge("carb", "m")
    return render(c, "F9_options", IMG)




def f10_selfcleansing():
    c = Chart(3, 5, cw=258, rh=108, gx=46, gy=32,
              title="Setting the maintenance washing schedule")
    c.node("y", 1, 0, "Year-by-year flow series", "start")
    c.node("c", 1, 1, "Apply connection ratio|for that year")
    c.node("v", 1, 2, "Compute velocity in each pipe|at that year's peak flow")
    c.node("q", 0, 3, "Below 0.75 m/s?", "tint")
    c.node("w", 0, 4, "Pipe needs scheduled washing|until the year it passes")
    c.node("o", 2, 3, "At or above 0.75 m/s")
    c.node("n", 2, 4, "Self-cleansing from|the opening year")
    c.node("s", 1, 4, "Schedule by pipe and by year", "accent")

    c.edge("y", "c")
    c.edge("c", "v")
    c.edge("v", "q")
    c.edge("v", "o")
    c.edge("q", "w")
    c.edge("o", "n")
    c.note(0, 0, "Over-estimating early flow|is the dangerous error here.|"
                 "Use the LOW growth case.", span=1)
    c.note(2, 0, "Yellow tankers still|discharging add early flow|and shorten "
                 "the washing period.", span=1)
    return render(c, "F10_selfcleansing", IMG)


def f11_utilities():
    c = Chart(3, 5, cw=258, rh=108, gx=46, gy=32,
              title="Handling a clash with an existing utility")
    c.node("r", 1, 0, "Proposed alignment", "start")
    c.node("d", 1, 1, "Superimpose on each utility|owner's service drawings")
    c.node("t", 1, 2, "Trial pit at the critical|crossings and intersections")
    c.node("q", 1, 3, "Can the sewer be re-routed|within the corridor?", "tint")
    c.node("y", 0, 4, "Re-route|and re-check clearances")
    c.node("n", 2, 4, "Compare cost of moving|ours against moving theirs|"
                      "and obtain the owner's NOC", "accent")

    c.edge("r", "d")
    c.edge("d", "t")
    c.edge("t", "q")
    c.edge("q", "y", label="yes")
    c.edge("q", "n", label="no")
    c.note(0, 0, "We hold electricity METER|POINTS, not cable routes.|"
                 "Telecom and gas are absent.", span=1)
    c.note(2, 0, "Sewer crosses UNDER a water|main, 450 mm clear, and 3 m|"
                 "horizontal separation.", span=1)
    return render(c, "F11_utilities", IMG)


def f12_modelling():
    c = Chart(3, 4, cw=262, rh=112, gx=46, gy=36,
              title="Building and proving the hydraulic model")
    c.node("n", 0, 0, "Network geometry|levels, diameters, gradients", "start")
    c.node("l", 2, 0, "Loads at manholes|from the plot layer", "start")
    c.node("b", 1, 1, "Build in SewerGEMS")
    c.node("r", 1, 2, "Run design year and|early year scenarios")
    c.node("c", 0, 3, "Calibrate against|measured flow where it exists")
    c.node("o", 2, 3, "Check velocity, d/D,|surcharge, pump run time", "accent")

    c.edge("n", "b")
    c.edge("l", "b")
    c.edge("b", "r")
    c.edge("r", "c")
    c.edge("r", "o")
    c.note(1, 3, "Model files are a contract deliverable in native editable "
                 "format, updated after construction", span=1)
    return render(c, "F12_modelling", IMG)


def f13_existing():
    c = Chart(3, 4, cw=260, rh=112, gx=46, gy=36,
              title="Assessing the existing network")
    c.node("g", 0, 0, "NWS asset GIS|declared inaccurate by NWS", "start")
    c.node("s", 2, 0, "Survey and CCTV|levels, sizes, condition", "start")
    c.node("a", 1, 1, "As-built and GIS|to NWS specification")
    c.node("h", 1, 2, "Hydraulic assessment|against future flows")
    c.node("u", 0, 3, "Adequate|retain and integrate")
    c.node("r", 2, 3, "Inadequate|upgrade, rehabilitate|or replace", "accent")

    c.edge("g", "a")
    c.edge("s", "a")
    c.edge("a", "h")
    c.edge("h", "u")
    c.edge("h", "r")
    c.note(1, 3, "Rehabilitation is a separately priced concept deliverable, "
                 "not an afterthought", span=1)
    return render(c, "F13_existing", IMG)


def f14_cost():
    c = Chart(4, 5, cw=232, rh=104, gx=36, gy=30,
              title="Building the cost estimate")
    c.node("q", 0, 0, "Quantities from the design|lengths, depths, counts", "start")
    c.node("r", 0, 1, "Unit rates|from NWS tenders")
    c.node("cap", 0, 2, "CAPEX by element", "tint")
    c.node("o", 2, 2, "OPEX by year|power, labour, chemicals,|sludge disposal", "tint")
    c.node("re", 1, 3, "M&E renewal|electrical at 15 yr|mechanical at 20 yr")
    c.node("dec", 2, 3, "Decommissioning")
    c.node("con", 0, 3, "Contingency|physical and price")
    c.node("npv", 1, 4, "Discount at 5 % over 25 years", "accent", span=2)
    c.node("soft", 3, 2, "Soft costs|design, survey, NOCs,|land, EIA", "tint")

    c.edge("q", "r")
    c.edge("r", "cap")
    c.edge("cap", "con")
    c.edge("o", "re")
    c.edge("con", "npv")
    c.edge("re", "npv")
    c.edge("dec", "npv")
    c.edge("soft", "o", side=("l", "r"))
    c.note(3, 4, "Road reinstatement and|rock excavation are the|two most "
                 "underestimated lines", span=1)
    return render(c, "F14_cost", IMG)

if __name__ == "__main__":
    for fn in (f1_chain, f2_data, f3_population, f4_demand, f5_flow,
               f6_gravity, f7_pumping, f8_stp, f9_options,
               f10_selfcleansing, f11_utilities, f12_modelling,
               f13_existing, f14_cost):
        fn()
