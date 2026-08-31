"""Sections 10 to 15 - pumping, plant, effluent, sludge, appraisal, and the
places where the guidelines cannot be relied upon."""
import doc as D
import omml as M

UP = M.up
R = M.r


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows,
            widths=[2.6, 10.4, 3.5], font=9)


def _source(d, text):
    D.p(d, "Source: " + text, size=9, italic=True, colour=D.GREY, space_after=10)


# ======================================================= 10. PUMPING
def s10_pumping(d):
    D.h(d, 1, "10   Lifting stations and force mains", page_break=True)

    D.h(d, 2, "10.1   Purpose")
    D.p(d, "Where gravity cannot carry the flow onward, it is lifted and pushed "
           "through a pressure pipe to the next point at which gravity can take "
           "over again. Every such station is a permanent operating cost and a "
           "permanent failure mode, which is why the guideline treats them as a "
           "last resort.")

    D.callout(d, "The guideline's position is unambiguous.",
              "\"The use of pumping stations and pressure mains shall be avoided "
              "whenever gravity sewer designs are feasible and cost effective.\" "
              "A design that reaches zero pumping stations is not an unusual "
              "outcome to be defended; it is the outcome the guideline asks for.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "10.2   When a station is required")
    D.p(d, "There is exactly one trigger in the entire guideline set, and it is "
           "a cost trigger. Where the cost of excavation becomes prohibitive, a "
           "pumping station is to be incorporated. No depth figure is attached "
           "to that obligation. The ten to twelve metre figure discussed in "
           "Section 9.6 is a separate recommendation about cover, and exceeding "
           "it obliges consultation with pipe manufacturers rather than a pump.")

    D.h(d, 2, "10.3   Station classification")
    D.table(d, ["Type", "Design flow", "Minimum duty pumps", "Standby"],
            [["Type 1", "up to 100 l/s", "1", "1"],
             ["Type 2", "100 to 300 l/s", "2", "1"],
             ["Type 3", "above 300 l/s", "3", "1"]],
            widths=[3.0, 5.0, 4.3, 4.2], font=9.5)
    D.p(d, "")
    D.callout(d, "Two tables in the guideline disagree here.",
              "One gives a Type 3 station three duty pumps; another, two pages "
              "later, gives it two. Both are printed in the same section of the "
              "same document. The three-pump reading is the conservative one, "
              "and the two tables agree for Types 1 and 2, so the discrepancy is "
              "confined to the largest stations.")

    D.p(d, "Above the table sits the governing rule, which is independent of "
           "type: sufficient pumps must be provided that the design peak flow "
           "can still be achieved with any one pump out of service.")

    D.h(d, 2, "10.4   Wet well volume")
    D.p(d, "The volume between the start and stop levels is set by how often the "
           "motor may be started, not by storage in any general sense.")
    eq = D.next_eq()
    M.display(d, M.seq(R("V"), M.EQ, R("0.25"), R(" "), R("Q"), R(" "), R("T")),
              number=eq)
    _params(d, [
        ["V", "live volume, between pump start and stop levels", "m³"],
        ["Q", "capacity of a single pump", "m³/s"],
        ["T", "on-off cycle time, 3600 divided by permitted starts per hour", "s"]])
    D.p(d, "The guideline sets a minimum of ten starts per hour for motors up to "
           "30 kW, and refers larger motors to the manufacturer and to NEMA MG 1. "
           "At ten starts per hour the cycle time is 360 seconds and the live "
           "volume becomes ninety times the pump capacity in cubic metres per "
           "second.")
    D.p(d, "The equation applies to a single constant-speed pump. The guideline "
           "gives no equivalent for variable-speed or duty-assist arrangements.")
    _source(d, "G203 §7.8 p48.")

    D.h(d, 2, "10.5   Suction conditions")
    eq = D.next_eq()
    M.display(d, M.seq(UP("NPSH"), M.sub(R(""), UP("a")), M.EQ,
                       M.sub(R("H"), UP("a")), M.MINUS,
                       M.sub(R("H"), UP("vpa")), M.MINUS,
                       M.sub(R("H"), UP("st")), M.MINUS,
                       M.sub(R("H"), UP("f"))), number=eq)
    _params(d, [
        ["H a", "absolute pressure on the liquid surface", "m (not stated in source)"],
        ["H vpa", "vapour pressure", "m"],
        ["H st", "static head", "m"],
        ["H f", "friction head", "m"]])
    D.p(d, "A margin of at least one metre over the pump's required suction head "
           "is to be provided. The guideline gives no units and no sign "
           "convention; the form as printed assumes a suction lift, and for a "
           "flooded suction the static term is additive.")

    D.h(d, 2, "10.6   Force mains")
    D.tab_caption(d, "Force main velocity and gradient criteria")
    D.table(d, ["Criterion", "Value", "Force"],
            [["Minimum velocity, raw sewage", "0.75 m/s at minimum flow", "shall"],
             ["Minimum velocity, intermittent flow", "1.0 m/s", "shall"],
             ["Minimum velocity, vertical mains", "1.2 m/s", "shall"],
             ["Maximum velocity", "2.5 m/s", "shall"],
             ["Minimum internal diameter", "75 mm; 50 mm with grinder pumps", "shall"],
             ["Gradient rising", "1:500 recommended", "recommended"],
             ["Gradient falling", "1:300 recommended", "recommended"],
             ["Gradient, absolute floor", "never below 1:750", "in all cases"],
             ["Retention time", "ideally under half an hour", "ideally"]],
            widths=[6.4, 6.0, 4.1], font=9)

    D.p(d, "")
    D.p(d, "Diameter is not selected by a formula. The guideline requires that "
           "alternative diameters producing velocities across the permitted "
           "range be considered, and that a cost comparison determine which "
           "gives the optimum whole life cost. Where initial flows are far below "
           "future flows, two mains may be warranted rather than one.")

    D.callout(d, "The friction equations are named but never written.",
              "Head loss is to be calculated by Darcy-Weisbach for larger pipes "
              "and higher velocities, or Hazen-Williams for smaller diameters, "
              "with any other equation needing NWS approval. Neither formula is "
              "printed anywhere in the three guidelines — only their "
              "coefficients are tabulated. Cite the standard form, not NWS. "
              "There is also no roughness value published for a raw sewage "
              "force main; the coefficient table covers potable water and "
              "treated effluent only.")

    D.p(d, "There is likewise no total dynamic head equation and no pump power "
           "equation in the guidelines. The components NWS names are static "
           "lift, friction loss, fitting losses and the velocity head "
           "difference; assembling them is standard hydraulics and should be "
           "cited as such.")
    _source(d, "G203 §8 p50-55; head loss cross-referenced to G202 §7.1.3.2 p104.")

    D.h(d, 2, "10.7   Surge")
    eq = D.next_eq()
    M.display(d, M.seq(R("Δ"), R("H"), M.EQ, M.frac(R("c"), R("g")), R("Δ"),
                       R("v")), number=eq)
    _params(d, [
        ["ΔH", "change in pressure", "m"],
        ["c", "wave propagation speed", "m/s"],
        ["g", "acceleration due to gravity", "m/s²"],
        ["Δv", "change in flow velocity", "m/s"]])
    D.p(d, "The wave speed is described qualitatively as depending on the "
           "properties of the pipe and the liquid. No celerity equation is given "
           "anywhere in the guidelines, so it must come from standard theory.")

    D.p(d, "Transient analysis must be carried out in NWS-approved licensed "
           "software; the equation is for checking, not for design. The number "
           "of simultaneous pump startups and shutdowns modelled follows N+1, "
           "so that reflected waves from earlier events can combine and reveal "
           "the true worst case. Models are first run with roughness set to "
           "near zero to capture the maximum swing, then re-run with realistic "
           "roughness.")

    D.p(d, "One concession applies uniquely to wastewater: negative pressure, "
           "with air entering at an air valve, can be acceptable on a force main "
           "provided the protection and equipment are adapted to it.")
    _source(d, "G201 Appendix III p145-147. G202 §10 is a one-line "
               "cross-reference to it and contains no surge content of its own.")

    D.h(d, 2, "10.8   Emergency provision")
    D.p(d, "Every pumping station must have an emergency overflow to prevent "
           "flooding of the station or of connected dwellings, and overflows "
           "require Environmental Authority approval. Only extreme events should "
           "result in one, and a method to prevent or minimise overflows must be "
           "submitted for approval — chosen on least cost and least operational "
           "complexity.")

    D.callout(d, "No emergency storage duration is specified.",
              "Emergency storage is named as one of four permitted methods, with "
              "no duration and no sizing method attached. The 48 to 72 hour "
              "figure that appears elsewhere in the guidelines applies to a "
              "lagoon at a treatment plant, not to a pumping station, and should "
              "not be transplanted. The designer proposes and NWS approves.")


# ======================================================= 11. STP
def s11_stp(d):
    D.h(d, 1, "11   Treatment plant sizing and phasing", page_break=True)

    D.h(d, 2, "11.1   Purpose")
    D.p(d, "Converting flows and loads into a plant capacity, a technology, a "
           "land area and a phasing plan.")

    D.h(d, 2, "11.2   Size categories, and why they matter")
    D.table(d, ["Category", "Capacity"],
            [["Small", "below 500 m³/d"],
             ["Medium", "500 up to 20,000 m³/d"],
             ["**Large**", "**20,000 m³/d and above**"]],
            widths=[6.0, 10.5], font=9.5)

    D.p(d, "")
    D.callout(d, "The large-plant classification changes four separate rules.",
              "The residential buffer stops being a flat 500 m and becomes 300 "
              "to 1000 m, set by the distance to the 5 odour-unit contour from a "
              "dispersion model. Computational fluid dynamics modelling becomes "
              "mandatory unless the TOR excludes it. The chlorine contact tank is "
              "replaced by a treated effluent storage tank performing the same "
              "function. And the organic peak factors fall to 1.2 for BOD and "
              "COD and 1.5 for nitrogen.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "11.3   Design horizon and margin")
    D.p(d, "A plant is designed for a horizon of at least fifteen years and must "
           "meet the projected population, with anticipated industrial and "
           "institutional needs taken into account. Separately, the corporate "
           "planning life cycle is twenty-five years, which is also the period "
           "over which options are compared.")
    D.p(d, "A ten per cent margin is applied to the design flow as an "
           "operational safety allowance, over and above any redundancy in the "
           "design rather than instead of it.")

    D.h(d, 2, "11.4   Influent characterisation")
    D.p(d, "Design is to be on the basis of at least 60 g of BOD and 80 g of "
           "suspended solids per person per day. Those are floors, not typical "
           "values — the guideline's word is \"at least\".")

    D.tab_caption(d, "Design raw sewage characteristics, where site data is absent")
    D.table(d, ["Parameter", "Design value", "Parameter", "Design value"],
            [["BOD₅", "350 – 400 mg/l", "Ammoniacal N", "40 – 50 mg/l"],
             ["COD", "700 – 900 mg/l", "Total Kjeldahl N", "60 – 80 mg/l"],
             ["Suspended solids", "400 – 500 mg/l", "Total phosphorus", "10 – 15 mg/l"],
             ["Inert solids", "20 %", "Alkalinity as CaCO₃", "200 – 400 mg/l"],
             ["Fat, oil and grease", "50 – 100 mg/l", "pH", "6.5 – 8.0"],
             ["", "", "Temperature", "20 / 35 °C"]],
            widths=[4.1, 4.2, 4.1, 4.2], font=9)
    D.p(d, "")
    D.p(d, "These values are indicative and are to be used after agreement with "
           "NWS, in preference to which come the specific character of the "
           "catchment and NWS's own laboratory database. Sludge liquor returns, "
           "side streams and tanker loads are not included in them and must be "
           "added.")

    D.h(d, 3, "Tankered sewage is far stronger")
    D.p(d, "Sewage arriving by tanker carries BOD from 350 up to 1050 mg/l, COD "
           "from 1350 to 5000, and suspended solids from 900 to 4300. Septic "
           "tank contents are described as much more concentrated than network "
           "sewage. Where tankers form a significant share of the inflow, this "
           "drives the load calculation rather than the network figures.")

    D.callout(d, "The trigger for a separate treatment line.",
              "Domestic sewage has a COD to BOD ratio between 1.8 and 2.2. Above "
              "that, the guideline states the influent is not effectively "
              "treatable biologically, and a separate line for high-strength "
              "wastewater is required if the volumes are significant. What "
              "counts as significant is not quantified and needs NWS agreement.")

    D.h(d, 2, "11.5   Load, and an equation the guideline does not print")
    D.p(d, "The guideline gives per-capita loads, design concentrations and peak "
           "factors, but nowhere prints the relation converting a flow and a "
           "concentration into a mass load. It is standard, and is stated here "
           "as a derivation rather than a citation.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("Load"), M.EQ,
                       M.frac(M.seq(R("Q"), M.TIMES, R("C")), R("1000"))), number=eq)
    _params(d, [
        ["Load", "mass load of the determinand", "kg/d"],
        ["Q", "flow", "m³/d"],
        ["C", "concentration", "mg/l"]])

    D.p(d, "Hydraulic pass-through structures are sized on peak hourly flow. "
           "Biological treatment is sized on average annual flow and the design "
           "inlet load. Both must include recycled liquors and tanker volumes.")

    D.h(d, 2, "11.6   Process sizing")
    D.callout(d, "The guidelines give ranges, not equations.",
              "No oxygen demand, sludge yield, solids retention time or "
              "clarifier area equation is printed anywhere. At concept and "
              "preliminary stage the guideline directs the designer to empirical "
              "methods — Metcalf and Eddy, or DWA, formerly ATV. At detailed "
              "design it requires verification in accredited software using IWA "
              "models. The tables in the guideline are ranges to land inside, "
              "and they are the enforceable part.")

    D.tab_caption(d, "Activated sludge configurations")
    D.table(d, ["Mode", "F:M (kg BOD/kg MLSS/d)", "MLSS (mg/l)", "Minimum SRT (d)"],
            [["High rate", "above 1.0", "below 2000", "1"],
             ["Conventional, 20 mg/l BOD", "0.25 – 0.4", "2000 – 3000", "2 – 4"],
             ["Conventional, 10 mg/l BOD", "0.15 – 0.25", "2500 – 3000", "4 – 6"],
             ["Conventional with nitrification", "0.15", "3000 – 4000", "above 6"],
             ["Extended aeration / MLE", "0.05 – 0.15", "2000 – 4000", "above 10"]],
            widths=[5.4, 4.2, 3.5, 3.4], font=9)

    D.h(d, 2, "11.7   Land area")
    D.p(d, "Footprint is indicative and is used for early planning, not as a "
           "compliance limit. It must cover process units, sludge handling, "
           "buffer zones and — the guideline is explicit — the land needed for "
           "energy-efficient solutions such as a solar farm inside the plant "
           "perimeter.")
    D.tab_caption(d, "Indicative footprint by technology, m² per m³/d")
    D.table(d, ["Technology", "Footprint", "Technology", "Footprint"],
            [["Membrane bioreactor", "0.45 – 0.9", "Sequencing batch reactor", "0.9 – 1.8"],
             ["Moving bed biofilm reactor", "0.9 – 1.8", "Conventional activated sludge", "1.8 – 3.6"],
             ["Integrated fixed film", "1.2 – 2.5", "Constructed wetland", "above 10"]],
            widths=[4.8, 3.5, 4.8, 3.4], font=9)
    D.p(d, "")
    D.p(d, "Built structures may not occupy more than 35 % of the allocated "
           "land, with a minimum five-metre setback from site boundaries.")

    D.h(d, 2, "11.8   Effluent quality")
    D.p(d, "The process must be capable of meeting Class A or Class B of "
           "Ministerial Decision 145/1993. The headline Class A values are 15 "
           "mg/l BOD, 150 COD, 15 suspended solids, 200 MPN per 100 ml faecal "
           "coliforms and fewer than one nematode ovum per litre.")

    D.callout(d, "Total nitrogen is the parameter that actually drives the "
                 "process.",
              "NWS overlays a limit of below 15 mg/l total nitrogen, which "
              "Ministerial Decision 145/93 does not contain. Class A on its own "
              "would permit around 21 mg/l once organic nitrogen, ammonia and "
              "nitrate are added. Full nitrification and denitrification are "
              "therefore mandatory in practice, and nitrogen rather than BOD or "
              "solids governs technology selection and sludge age.")

    D.callout(d, "If discharge to a wadi is contemplated, the standard tightens "
                 "sharply.",
              "Effluent to a wadi must meet Class A, and where the wadi reaches "
              "the sea, ammonia, nitrogen and phosphorus instead take the values "
              "of Decision 159/2005. Total phosphorus falls from 30 to 2 mg/l "
              "and ammoniacal nitrogen from 5 to 1. That forces enhanced "
              "biological phosphorus removal with chemical polishing. Any wadi "
              "discharge is subject to Environmental Authority and APSR "
              "approval.")

    D.h(d, 2, "11.9   Siting and buffer")
    D.p(d, "Site selection is assessed against fifteen criteria grouped under "
           "accessibility, physical characteristics, environmental and climate "
           "impact, social impact and cost. Two carry hard numbers: the site "
           "must consider the 25 and 100 year flood levels, and plants must be "
           "fully operational during floods.")
    D.p(d, "For a large plant the residential buffer is not a fixed figure. It "
           "is the distance to the 5 odour-unit contour from a dispersion model, "
           "bounded between 300 and 1000 m. Odour modelling therefore has to "
           "precede siting, not follow it.")
    _source(d, "G203 §10.2 p63-67, §10.3 p74-77, Table 27 p63, Table 28 p64; "
               "G201 Table 8 p43-44.")


# ======================================================= 12. TSE
def s12_tse(d):
    D.h(d, 1, "12   Treated effluent", page_break=True)

    D.h(d, 2, "12.1   How much is produced")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("TSE")), M.EQ, R("0.95"),
                       M.sub(R("Q"), UP("inlet"))), number=eq)
    D.p(d, "The missing five per cent covers evaporation, reuse within the "
           "process, and the plant's own consumption for landscaping and dust "
           "control.")

    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("delivered")), M.EQ, R("0.90"),
                       M.sub(R("Q"), UP("TSE")), M.EQ, R("0.855"),
                       M.sub(R("Q"), UP("inlet"))), number=eq)
    D.p(d, "A further ten per cent is lost in the distribution network, chiefly "
           "at joints and connections. Note the difference in force: the 95 % "
           "production ratio is an assumption the guideline permits, while the "
           "10 % network loss is one it requires.")
    _source(d, "G201 §7.4.6.1 p73 and §7.4.6.3 p75-76.")

    D.h(d, 2, "12.2   Who takes it")
    D.p(d, "The TOR does not name customers. Identifying them is the "
           "consultant's task, and the guideline classifies them in two groups.")
    D.table(d, ["Public consumers", "Private consumers"],
            [["Beautification of highways and main roads", "Community parks"],
             ["Beautification of secondary roads", "Golf courses"],
             ["Beautification of interchanges and roundabouts", "Private gardens"],
             ["Public parks", "Nurseries and farms"]],
            widths=[8.2, 8.3], font=9.5)

    D.h(d, 2, "12.3   How much each needs")
    D.tab_caption(d, "Summer irrigation demand, for concept planning")
    D.table(d, ["Planting", "Demand", "Planting", "Demand"],
            [["Shrubs", "20 – 40 l/plant/d", "Ground cover", "10 l/m²/d"],
             ["Palm trees", "120 – 165 l/plant/d", "Seasonal flowers", "10 l/m²/d"],
             ["Other trees", "40 – 80 l/plant/d", "Grass", "12 l/m²/d"],
             ["Hedges", "10 l/m/d", "Roads and junctions", "10 l/m²/d"]],
            widths=[4.3, 4.0, 4.3, 3.9], font=9)
    D.p(d, "")
    D.p(d, "Planting densities are 15 m for trees and 3 m for shrubs. The rate "
           "for roads and junctions applies where the vegetation type is unknown "
           "and is subject to the municipality's approval.")

    D.h(d, 2, "12.4   Seasonality and sizing")
    D.p(d, "Demand runs at 100 % from June to August, 75 % in spring and autumn, "
           "and 50 % from December to February. The system is sized on the "
           "summer peak. Any consumer averaging more than 500 m³/d is to be "
           "studied individually with its own irrigation timing pattern. "
           "Reservoirs are designed for a minimum of 24 hours storage.")
    _source(d, "G201 §7.4.6 p73-77, Tables 20 to 23.")


# ======================================================= 13. SLUDGE
def s13_sludge(d):
    D.h(d, 1, "13   Sludge", page_break=True)

    D.h(d, 2, "13.1   Purpose")
    D.p(d, "Sludge handling and disposal must be considered an integral part of "
           "the treatment system, and plans and specifications for it must be "
           "incorporated into the design of every plant. It is not an appendix "
           "to the process design.")

    D.h(d, 2, "13.2   How much")
    eq = D.next_eq()
    M.display(d, M.seq(UP("Sludge"), M.EQ, R("0.25"), M.TIMES,
                       M.sub(R("Q"), UP("inlet"))), number=eq)
    _params(d, [
        ["Sludge", "sludge produced, dry solids", "kg/d"],
        ["Q inlet", "plant inflow", "m³/d"]])
    D.p(d, "This is a master-plan baseline and an explicit starting point, not a "
           "design figure. It is a volumetric yield tied to inflow rather than "
           "the conventional yield per kilogram of BOD removed, and the "
           "guideline does not state whether it is dry solids or wet cake — read "
           "as dry solids. The wastewater guideline gives no yield factor at "
           "all; sludge production is instead a required output of the process "
           "model.")

    D.h(d, 2, "13.3   Where it goes")
    D.callout(d, "Ibri is named as the governorate's sludge treatment centre.",
              "NWS's own sludge management plan lists, for Adh Dhahirah, a "
              "sludge treatment centre performing composting at Ibri STP. The "
              "plant is a receiver for the governorate, not merely a producer of "
              "its own sludge. That has consequences for land area, odour "
              "buffer, and vehicle access which must be carried into the site "
              "selection and the footprint.",
              fill="EAF1F8", colour=D.MID)

    D.p(d, "Reuse is the default: Ministerial Decision 145/93 requires sludge to "
           "be reused unless no form of reuse is possible, and quality must "
           "comply with its heavy metal limits — which are referenced by the "
           "guideline but not reproduced in it, and must be obtained from the "
           "Decision itself. Sludge exceeding those limits may go to landfill "
           "only with prior ministerial approval.")

    D.tab_caption(d, "Be'ah landfill acceptance criteria")
    D.table(d, ["Criterion", "Requirement"],
            [["Solids content", "**minimum 80 %, dried before disposal**"],
             ["pH", "neutral"],
             ["Temperature", "ambient"],
             ["Daily quantity", "not exceeding 60 tonnes per day"],
             ["Standing", "Be'ah may stop receiving sludge at any time"]],
            widths=[5.5, 11.0], font=9.5)

    D.p(d, "")
    D.callout(d, "The 80 % threshold rules out mechanical dewatering alone.",
              "The best performance in the guideline's own tables is a plate "
              "filter press at 40 to 45 % dry solids. Drying beds reach 60 to "
              "75 %, still short. Thermal or solar drying, or composting, is "
              "therefore effectively forced if landfill is the outlet — which "
              "aligns with the composting centre already designated for Ibri.")

    D.p(d, "Onsite dewatering facilities are required at all plants unless NWS "
           "states otherwise, sized on peak weekly average flow at eleven hours "
           "a day, seven days a week, with a standby unit and solids recovery of "
           "at least 95 %.")
    _source(d, "G201 §7.4.7 p78; G203 §10.6.8 p135-137 and p151-155.")


# ======================================================= 14. APPRAISAL
def s14_appraisal(d):
    D.h(d, 1, "14   Options and appraisal", page_break=True)

    D.h(d, 2, "14.1   How many options, and of what kind")
    D.p(d, "A minimum of three options is required, and separately for the "
           "sewer network, the treated effluent network and the plant. The "
           "guideline also states what kind they should be.")
    D.numbered(d, "an option that pushes environmental sustainability, including "
                  "nature-based solutions")
    D.numbered(d, "an internationally best-in-class, state-of-the-art solution")
    D.numbered(d, "a standard solution using practice and technology already "
                  "established in Oman")
    D.p(d, "The three-option minimum is mandatory; the archetypes are offered as "
           "guidance. Each option must present equivalent functional "
           "requirements and comparable reliability and redundancy, so that the "
           "comparison is unbiased.")

    D.h(d, 2, "14.2   The appraisal parameters")
    D.p(d, "Capital and operating cost; life cycle cost; carbon footprint over "
           "the project lifetime; resource efficiency under a circular economy "
           "approach including decommissioning; in-country value; and the degree "
           "of nature-based solution. The evaluation horizon is twenty-five "
           "years for every parameter, and NWS sets the weighting.")

    D.h(d, 2, "14.3   Net present value")
    D.callout(d, "No formula for this exists in the guidelines.",
              "Net present value, life cycle cost, carbon footprint and the "
              "multi-criteria score are all named and specified in scope, and "
              "none is written as an equation anywhere in the three documents. "
              "This was verified by full-text search and by checking every page "
              "for equations dropped as images. Cite ISO 15686-5 for life cycle "
              "cost and the GHG Protocol and ISO 14064 for carbon. What the "
              "guideline does fix is the discount rate and the horizon.")

    eq = D.next_eq()
    M.display(d, M.seq(UP("NPV"), M.EQ,
                       M.nary("∑", M.seq(R("t"), R("=1")), R("n"),
                              M.frac(M.sub(R("C"), R("t")),
                                     M.sup(M.delim(M.seq(R("1"), M.PLUS, R("i"))),
                                           R("t"))))), number=eq)
    _params(d, [
        ["C t", "net cash flow in year t", "OMR"],
        ["i", "discount rate — **5 %, unless NWS instructs otherwise**", "fraction"],
        ["n", "evaluation period — **25 years**", "years"]])
    D.p(d, "The equation above is the standard form, given for completeness. It "
           "is not a guideline citation.")

    D.h(d, 2, "14.4   Operating cost")
    D.p(d, "The guideline lists what operating cost must include: labour and "
           "staffing, vehicles and equipment, power and utilities at the current "
           "APSR tariff, spare parts and consumables, chemicals, and general "
           "maintenance and repair. The tariff itself is not in the guideline "
           "and must be obtained.")

    D.h(d, 2, "14.5   Carbon")
    D.p(d, "Carbon footprint is to be evaluated for construction and operation "
           "in accordance with ISO 14064 and the GHG Protocol, expressed in "
           "tonnes of carbon dioxide equivalent per year and per cubic metre "
           "produced. Scopes 1 and 2 are counted in full; Scope 3 is counted for "
           "significant elements where information is available or can be "
           "reasonably estimated. The benchmark for treated effluent is "
           "1.17 × 10⁻³ tonnes per cubic metre.")
    D.p(d, "One of the options must include a carbon reduction plan comparing a "
           "conventional base case with an optimised scenario, against NWS "
           "targets of 52 % reduction by 2030 and 96 % by 2050. Since more than "
           "eighty per cent of NWS operational emissions come from electricity, "
           "the levers that matter are gravity flow, minimised lift, efficient "
           "equipment and renewable generation.")

    D.h(d, 2, "14.6   Choosing")
    D.p(d, "A weighted multi-criteria analysis compares the options against "
           "total lifetime cost, sustainability (carbon, circular economy and "
           "nature-based solutions), social development and in-country value, "
           "adaptability and resilience, operability, constructability, and "
           "environmental impact. No scoring scale or normalisation rule is "
           "specified, so the method must be proposed and agreed.")

    D.p(d, "Sensitivity analysis varies exactly three things: the weighting "
           "between categories, the discount rate, and the input design criteria.")

    D.callout(d, "The tie-break rule.",
              "Where options fall within ten per cent of each other on total "
              "lifetime cost, the more sustainable option is to be adopted. This "
              "makes the sustainability assessment decisive rather than "
              "decorative whenever the costs are close.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "14.7   Cost accuracy and value engineering")
    D.p(d, "Concept-stage estimates carry an accuracy of plus or minus twenty "
           "per cent, and the report must state its accuracy class. Measurement "
           "follows CESMM3.")
    D.callout(d, "Formal value engineering is triggered at concept for this "
                 "project.",
              "The threshold table places a general value engineering study at "
              "concept stage, led by the design team, for projects below five "
              "million rials. Its footnote overrides that for treatment plants "
              "and pumping stations above two million, which require a formal "
              "study by an independent certified consultant at both concept and "
              "preliminary stage. The Ibri plant clears that threshold, so an "
              "external appointment falls inside the concept programme.")
    _source(d, "G201 §11 p92-94 and §12 p95-106.")


# ======================================================= 15. RELIABILITY
def s15_defects(d):
    D.h(d, 1, "15   Where the guidelines cannot be relied on", page_break=True)

    D.p(d, "This section exists because a reference document that presents its "
           "source as flawless is not usable. Everything below was verified at "
           "the page. Where the guideline is wrong, this document reproduces "
           "what it prints and says what is wrong with it; it does not silently "
           "correct the client's own standard.")

    D.h(d, 2, "15.1   Formulae that do not exist in the guidelines")
    D.p(d, "Each of these is commonly assumed to be in the guidelines and is "
           "not. Citing NWS for any of them would be a fabricated reference.")
    D.table(d, ["Formula", "Cite instead", "What NWS does supply"],
            [["Net present value", "ISO 15686-5", "5 % discount rate, 25 year horizon"],
             ["Life cycle cost", "ISO 15686-5", "the cost-stage scope list"],
             ["Carbon footprint", "ISO 14064, GHG Protocol", "units and benchmark values"],
             ["Multi-criteria score", "designer's own, agreed with NWS", "the criteria and who weights them"],
             ["Total dynamic head", "standard hydraulics", "the component list, in prose"],
             ["Pump power", "standard hydraulics", "nothing; no efficiency assumption"],
             ["Darcy-Weisbach", "standard form", "roughness coefficients only"],
             ["Hazen-Williams", "standard form", "C values only"],
             ["Wave celerity", "Korteweg", "a qualitative description"],
             ["Mass load from flow and concentration", "standard", "loads and concentrations separately"],
             ["Oxygen demand, SRT, clarifier area", "Metcalf and Eddy, or DWA", "ranges to land inside"],
             ["Surge vessel volume", "—", "a 20 % minimum allowance"],
             ["Emergency storage at a pumping station", "—", "nothing; propose and get approval"],
             ["Roughness for a raw sewage force main", "—", "potable and treated effluent only"],
             ["Aquifer recharge criteria", "—", "absent from all three documents"]],
            widths=[5.6, 4.8, 6.1], font=8.5)

    D.h(d, 2, "15.2   A mandatory method that cannot be completed")
    D.callout(d, "Tractive force.",
              "The check is required, the equation is given, and the required "
              "value of shear stress in pascals appears nowhere in the "
              "wastewater guideline's 201 pages or the general guideline's 152. "
              "Any value used must come from the literature and be agreed with "
              "NWS in writing. This is the single largest hole in the gravity "
              "design chain.")

    D.h(d, 2, "15.3   Errors of substance")
    D.table(d, ["Where", "What is wrong", "How to handle it"],
            [["G203 p24", "full-bore flow printed as velocity divided by area, "
                          "which is dimensionally impossible",
              "use velocity multiplied by area; note the defect"],
             ["G201 p72", "Peltier printed with 1 in the numerator; the published "
                          "form carries 2.5",
              "reproduce as printed; query NWS"],
             ["G201 p62", "Adh Dhahirah tanker ratio of 333 % cannot be "
                          "arithmetically true; the volumes are sound",
              "do not use the ratio; query NWS"],
             ["G201 p144", "pipeline emptying time evaluates to metres to the "
                           "power one and a half times seconds squared",
              "the guideline calls it a quick check; use a transient model"],
             ["G203 p25", "Manning constant 6.3448 against an exact 6.3496",
              "quote the guideline value; footnote the exact one"],
             ["G203 p40 / p42", "two tables disagree on duty pumps for the "
                                "largest station type",
              "take the conservative reading; flag"],
             ["G203 p146", "aerobic digestion text requires 45 days retention; "
                           "its own table gives 10 to 15",
              "the text governs; note the conflict"],
             ["G203 p124", "clarifier surface loading and overflow rate do not "
                           "reconcile, both stated at average flow",
              "reproduce both; do not silently pick one"],
             ["G203 p185", "hydrogen sulphide risk bands overlap and leave a gap",
              "reproduce verbatim; flag"],
             ["G203 p71", "chlorine residual worded as \"at least between\"",
              "0.3 to 1.0 at the consumer; up to 3.0 at the plant"]],
            widths=[2.6, 8.0, 5.9], font=8.5)

    D.h(d, 2, "15.4   Cross-references that do not resolve")
    D.bullet(d, "the TOR cites item 2.1 of Section 05 of the wastewater manual, "
                "which no longer exists after the March 2026 renumbering; the "
                "equivalent content is now §10.1")
    D.bullet(d, "a package-plant peak factor of 3.0 is attributed to the general "
                "guideline, which nowhere prints 3.0")
    D.bullet(d, "two internal references to the tanker discharge section point to "
                "the wrong subsection")
    D.bullet(d, "the general guideline is cited twice as AM-GUD rather than "
                "PAM-GUD")
    D.bullet(d, "value engineering timing is given as concept in one table and "
                "detailed design only in another")
    D.bullet(d, "environmental impact assessment timing is scoping-at-preliminary "
                "in one clause and full-assessment-at-concept in another")

    D.h(d, 2, "15.5   What to do about all this")
    D.p(d, "Three rules keep the report defensible. Quote the guideline as it is "
           "printed, and separately say what is wrong with it — never publish a "
           "silently corrected version of the client's own standard. Where a "
           "formula is not NWS's, attribute it to whoever it belongs to. And "
           "where the guideline is silent on something it makes mandatory, "
           "propose a value, say where it came from, and obtain agreement in "
           "writing before the design depends on it.")


def build_part2(d):
    s10_pumping(d)
    s11_stp(d)
    s12_tse(d)
    s13_sludge(d)
    s14_appraisal(d)
    s15_defects(d)
