# -*- coding: utf-8 -*-
"""T02 — Hydraulic Design of a Gravity Sewer Network. Content in one place.

Both makers (Word and PDF) read this list, so the two files can never say different things.

EVERY guideline number here was read back out of the source PDF before being written down,
not recalled: PAM-GUD-203 pages 21, 22, 27, 28, 29, 30 and 33, and PAM-GUD-201 pages 71 and
72. Page numbers are the document's own printed page numbers. Where a value is a project
decision or an assumption rather than something the guideline states, it says so in the
line itself — those are never presented as requirements.

Block types: ("h1",t) ("h2",t) ("p",t) ("bullet",lead,rest) ("table",head,rows,widths)
("pagebreak",) ("toc",) ("cover",{...})
"""


def build():
    B = []

    B.append(("cover", {
        "eyebrow": "Ibri Sewer, TE & STP — Project 2621",
        "title": "T02 — Hydraulic Design of a Gravity Sewer Network",
        "subtitle": "From demand to the constraints that govern every pipe",
        "note": "Tutorial — design team",
        "date": "23 August 2026",
        "facts": [
            ["Follows on from", "T01 — Sewage Flow and Pollution Load Calculation"],
            ["Sources", "PAM-GUD-203 (wastewater), PAM-GUD-201 (general)"],
            ["Every number", "read back from the source PDF, with its page"],
            ["Scope", "the rules themselves, not any one scheme"],
        ]}))
    B.append(("pagebreak",))
    B.append(("h1", "Contents"))
    B.append(("toc",))
    B.append(("pagebreak",))

    # ---------------------------------------------------------------- 1
    B.append(("h1", "1. What this tutorial is for"))
    B.append(("p", "T01 takes you from people to a flow: how many live in an area, how much "
                   "water they use, how much of it comes back as sewage, and what the peak "
                   "of that flow is. It stops at a number in litres per second."))
    B.append(("p", "This tutorial starts there. It sets out every rule that governs turning "
                   "that flow into a real sewer: where the pipe may go, how big it is, how "
                   "steeply it falls, how deep it sits, where the manholes go, and when "
                   "gravity stops working and a pump becomes unavoidable."))
    B.append(("p", "It is written to be used on any scheme, not one particular design. Every "
                   "requirement is quoted from the guideline with its page, so it can be "
                   "checked. Where this project has chosen a value the guideline does not "
                   "give — or has departed from one it does — that is marked plainly rather "
                   "than blended in with the requirements."))
    B.append(("bullet", "A word on how to read the numbers. ",
              "“Shall” is a requirement. “Should” and "
              "“recommended” are the guideline's own words for advice, and this "
              "tutorial keeps the distinction, because it changes what you are allowed to "
              "do when a design cannot meet it."))

    # ---------------------------------------------------------------- 2
    B.append(("h1", "2. Words used in this tutorial"))
    B.append(("table", ["Word", "What it means"], [
        ["Invert", "The inside bottom of the pipe. Levels are quoted to the invert because "
                   "that is what sets whether water will flow."],
        ["Crown", "The inside top of the pipe — the opposite of the invert."],
        ["Cover", "The thickness of ground above the crown of the pipe."],
        ["Depth", "How far down the pipe sits. In this tutorial, measured from ground level "
                  "to the invert unless it says otherwise."],
        ["Gradient (or slope)", "How steeply the pipe falls, as a fraction: metres of fall "
                                "per metre of pipe. 0.005 m/m = 5 mm/m = 0.5 % = 1 in 200."],
        ["Fall", "The drop in level along a pipe: gradient x length."],
        ["d/D", "How full the pipe runs. d is the depth of water, D the pipe diameter. "
                "d/D = 0.65 means the water is 65 % of the way up the pipe."],
        ["Self-cleansing", "Flowing fast enough to carry solids along instead of letting "
                           "them settle and block the pipe."],
        ["Tractive force", "The drag the flowing water exerts on the pipe wall, in pascals "
                           "(Pa). An alternative to a velocity rule for keeping solids "
                           "moving, and the one that works when flows are small."],
        ["Qadf", "Average daily flow — the everyday flow, averaged over 24 hours."],
        ["Qpdf / peak flow", "The flow at the busiest time of day. Pipes are sized for this, "
                             "not the average."],
        ["Peak factor", "Peak flow divided by average flow."],
        ["Infiltration", "Groundwater leaking INTO the sewer through joints and cracks. It "
                         "is not sewage, but the pipe still has to carry it."],
        ["Backdrop", "A vertical pipe at a manhole that lets a high incoming sewer drop down "
                     "to the level of the outgoing one, outside the chamber."],
        ["Vortex drop shaft", "A drop structure for very large falls, shaped so the water "
                              "spirals down instead of crashing to the bottom."],
        ["Rising main (force main)", "A pipe that carries pumped sewage. It runs full and "
                                     "under pressure, so none of the gravity rules apply."],
        ["Trunk main", "The large primary sewer that everything else eventually drains into."],
        ["Rider sewer", "A short sewer serving a handful of properties, upstream of a "
                        "lateral."],
        ["HCC", "House Connection Chamber — the small chamber where a property joins the "
                "public sewer."],
    ], [1.5, 4.6]))

    # ---------------------------------------------------------------- 3
    B.append(("pagebreak",))
    B.append(("h1", "3. What a gravity sewer has to do"))
    B.append(("p", "A gravity sewer has no moving parts. Everything it does, it does because "
                   "the pipe falls. That single fact produces four requirements that pull "
                   "against each other, and the whole of the rest of this tutorial is about "
                   "holding all four at once."))
    B.append(("table", ["The job", "What it demands", "What it fights against"], [
        ["Carry the peak flow", "A pipe big enough, and not running more than part full",
         "Bigger pipes cost more and run slower"],
        ["Keep itself clean", "Enough fall to keep solids moving",
         "More fall means the pipe dives away from the surface"],
        ["Stay safely buried", "Enough ground above it, and not too much",
         "Cover and fall pull in opposite directions on flat land"],
        ["Be buildable", "Steady gradients, sensible manholes, pipes under streets",
         "The neatest hydraulic answer is often the worst trench"],
    ], [1.5, 2.6, 2.0]))
    B.append(("p", "The tension worth understanding before anything else is the third one. A "
                   "sewer must keep falling even where the ground is flat, so it gets deeper "
                   "the further it goes. Depth is what eventually ends a gravity system, and "
                   "it is why pumping stations exist."))

    # ---------------------------------------------------------------- 4
    B.append(("h1", "4. From demand to flow — the short version"))
    B.append(("p", "T01 covers this chain in full. What matters here is which number arrives "
                   "at each pipe, and the values the guideline fixes along the way."))
    B.append(("table", ["Step", "What happens", "Guideline value"], [
        ["People", "Population, now and at the design horizon", "T01 Section 5"],
        ["Water demand", "Litres per person per day", "T01 Section 6"],
        ["Return to sewer", "Only part of the water supplied comes back",
         "Domestic and tanker 85 %, non-domestic 54 % (G201 Table 19, p71)"],
        ["Infiltration", "Groundwater leaking in, added to the sewage",
         "New networks: 720 L/day per km of sewer (G201 p72)"],
        ["Average daily flow", "Qadf — everything above, averaged over the day", "—"],
        ["Peak flow", "What the pipe is actually sized for", "See below"],
    ], [1.2, 2.4, 2.5]))
    B.append(("h2", "4.1 Peak factor"))
    B.append(("p", "The guideline gives two methods and is specific about when the first "
                   "applies."))
    B.append(("bullet", "Merrimack — the one to use. ",
              "“The Merrimack formula is to be used for calculating the peak factors "
              "for wastewater discharge for an area (catchment or sub catchment) having over "
              "100 properties” (G201 p71). Qpdf = 2.65 x Qadf raised to the power "
              "0.879, with both flows in megalitres per day. The peak factor is then Qpdf "
              "divided by Qadf."))
    B.append(("bullet", "Peltier — the alternative. ",
              "Peak factor = 1.5 + 1 / square root of Qm, where Qm is the average daily flow "
              "in LITRES PER SECOND, not megalitres per day (G201 p72). Mixing the units is "
              "the easiest mistake to make here."))
    B.append(("bullet", "A ceiling on the result. ",
              "“It is recommended that the hourly peak factor should not exceed "
              "5.0” (G201 p72). Note the word recommended — it is advice, not a limit "
              "to truncate against silently."))
    B.append(("p", "Below 100 properties the guideline prescribes no formula. That is a real "
                   "gap at the head of a network, where most pipes are, and it has to be "
                   "handled by an explicit project decision rather than by extending "
                   "Merrimack past its stated range."))
    B.append(("bullet", "Where detailed land use exists. ",
              "G201 p71 requires that design flows then be calculated to a relevant "
              "international standard such as BS EN 752, stating clearly which standard was "
              "used, supported by site-specific evidence."))

    # ---------------------------------------------------------------- 5
    B.append(("pagebreak",))
    B.append(("h1", "5. How the network is organised"))
    B.append(("p", "The guideline names the parts of a sewer network, and the names carry "
                   "meaning — they say what each part is for and what rules attach to it "
                   "(G203 p21)."))
    B.append(("table", ["Part", "What it is"], [
        ["Trunk mains (primary)", "The large sewers that receive the districts and carry "
                                  "flow onward to treatment."],
        ["Secondary network", "“the headers or main sewers usually laid under the "
                              "streets and deserving the watersheds” — the collectors "
                              "that gather a district."],
        ["Tertiary network", "“collects the wastewater from the properties, generally "
                             "through the House Connection Chambers (HCC), before "
                             "discharging into the secondary sewage network. It includes the "
                             "rider sewers and lateral sewers.”"],
    ], [1.7, 4.4]))
    B.append(("p", "The practical point is that a network is a hierarchy, not a flat set of "
                   "branches all reaching for the trunk. Properties feed riders, riders feed "
                   "laterals, laterals feed main sewers, and only the collectors reach the "
                   "trunk. Designing it as a hierarchy is what makes it buildable: fewer, "
                   "longer trenches instead of many short ones, and few connections into the "
                   "trunk rather than many."))

    # ---------------------------------------------------------------- 6
    B.append(("h1", "6. Pipe size"))
    B.append(("h2", "6.1 Minimum sizes and materials"))
    B.append(("p", "G203 Table 6 (p22) sets the smallest pipe allowed for each part of the "
                   "network, and the materials that may be used. Sizes are quoted as OD — "
                   "outside diameter."))
    B.append(("table", ["Category", "Minimum size", "Open trench", "Trenchless"], [
        ["Rider sewer, property connection", "OD 160 mm", "PVC-U, HDPE",
         "GRP, HDPE, PVC-U"],
        ["Lateral sewer (maximum length 45 m)", "OD 200 mm", "PVC-U, HDPE, GRP",
         "GRP, HDPE, PVC-U"],
        ["Main sewer, up to 300 mm", "OD 200 mm", "PVC-U (up to 250 mm), HDPE, GRP",
         "GRP, HDPE, PVC-U"],
        ["Main sewer, 350 mm and above", "—",
         "GRP, HDPE, GRP/PVC, lined RCC", "GRP, HDPE"],
    ], [1.9, 1.0, 1.8, 1.4]))
    B.append(("bullet", "The 45 m lateral limit is easy to miss. ",
              "Table 6 carries it in the row heading rather than in the text: a lateral "
              "sewer has a maximum length of 45 m. It is a size-and-material table, so the "
              "rule tends to be read past."))
    B.append(("bullet", "Nominal size is not the bore. ",
              "PVC-U pipe is named by its OUTSIDE diameter, so a DN200 PVC-U pipe carries "
              "water through something smaller than 200 mm once the wall thickness is taken "
              "off. GRP is named by its inside diameter. Sizing a pipe on its name rather "
              "than its true bore overstates the capacity of every plastic pipe in the "
              "network."))
    B.append(("h2", "6.2 How full a pipe may run"))
    B.append(("p", "A sewer is never designed to run full. Capacity is held back so there is "
                   "somewhere for an unusual flow to go, and so air can move above the water "
                   "(G203 Table 10, p27)."))
    B.append(("table", ["Pipe diameter", "Maximum d/D at peak flow"], [
        ["Up to 350 mm", "0.65"],
        ["Greater than 350 mm", "0.50"],
    ], [2.6, 2.6]))
    B.append(("h2", "6.3 The rule that removes the easy way out"))
    B.append(("p", "G203 p29 states plainly: “Sewers shall not be oversized to "
                   "facilitate flatter slopes.”"))
    B.append(("p", "This matters more than it first appears. A bigger pipe has a lower "
                   "minimum gradient — DN600 needs 1.25 mm/m where DN200 needs 5.00 — so "
                   "upsizing is the obvious trick for keeping a sewer shallow on flat "
                   "ground. The guideline forbids it. On flat ground the design has no "
                   "choice but to accept the depth, and pump when the depth runs out."))

    # ---------------------------------------------------------------- 7
    B.append(("pagebreak",))
    B.append(("h1", "7. Gradient"))
    B.append(("p", "Gradient is set by two separate requirements, and the guideline is "
                   "explicit that the steeper of the two governs (G203 p27): "
                   "“Steeper gradient calculated based on self-cleansing velocity and "
                   "minimum tractive force methodology shall be adopted as minimum pipe "
                   "gradient.”"))
    B.append(("h2", "7.1 Self-cleansing velocity — Table 11"))
    B.append(("p", "“The gravity sewer pipe gradients shall be sufficient to maintain "
                   "the design minimum velocity of 0.75 m/s to ensure sewer cleansing and "
                   "avoid sedimentation and limit H2S formation” (G203 p29). Table 11 "
                   "is that velocity turned into a gradient for each pipe size, using "
                   "Colebrook-White."))
    B.append(("table", ["Pipe diameter (mm)", "mm/m", "%", "m/m", "1 in"], [
        ["200", "5.00", "0.500", "0.00500", "200"],
        ["250", "3.75", "0.375", "0.00375", "267"],
        ["315", "2.70", "0.270", "0.00270", "370"],
        ["400", "2.05", "0.205", "0.00205", "488"],
        ["500", "1.55", "0.155", "0.00155", "645"],
        ["600", "1.25", "0.125", "0.00125", "800"],
        ["700", "1.00", "0.100", "0.00100", "1 000"],
        ["800", "0.85", "0.085", "0.00085", "1 176"],
        ["900 and above", "0.75", "0.075", "0.00075", "1 333"],
    ], [1.8, 1.0, 1.0, 1.2, 1.0]))
    B.append(("p", "The mm/m column is the guideline's own. The other three are the same "
                   "number in the units people commonly use, given here so nothing has to be "
                   "converted by hand."))
    B.append(("h2", "7.2 Tractive force — for the small flows at the head of a network"))
    B.append(("p", "Near the top of a network the flow is tiny, and no realistic gradient "
                   "will make it travel at 0.75 m/s. The guideline anticipates this: "
                   "“At the head of the sewerage systems, the flow velocity based on "
                   "the minimum self-cleansing may not be attainable. In these "
                   "circumstances, the minimum pipe gradient for the sewer shall be "
                   "calculated based on the hydraulic design approach of minimum tractive "
                   "force” (G203 p27)."))
    B.append(("p", "The relationship is from Mara, Sleigh and Taylor (2000), derived at "
                   "d/D = 0.2 and n = 0.013:"))
    B.append(("table", ["Term", "Meaning"], [
        ["Smin", "Minimum slope to move particles"],
        ["tau", "Tractive tension, in pascals (Pa)"],
        ["Q", "Flow"],
        ["K", "2.33 x 10⁻⁴ with Q in m³/s, or 5.5 x 10⁻³ with Q in L/s"],
    ], [1.2, 4.6]))
    B.append(("bullet", "The guideline gives no value for tau. ",
              "It defines the method and the constant, but not the tractive tension to "
              "design to. That number has to come from the project, and it matters: the "
              "required gradient rises steeply with tau, so doubling it can put a large part "
              "of a network below its minimum gradient. Any design using this method must "
              "state the value it assumed and test what happens if it is wrong."))
    B.append(("h2", "7.3 Maximum gradient"))
    B.append(("p", "“The maximum gradient should be determined to comply the maximum "
                   "velocity of 3.0 m/s” (G203 p29), and “the maximum velocity "
                   "shall not exceed 3 m/s at the design depth of flow” (G203 p27). "
                   "Note the qualifier: the check is made at the design depth of flow, not "
                   "running full."))
    B.append(("p", "Where the ground falls faster than 3 m/s allows, the surplus fall is not "
                   "thrown away — it is taken as a drop at a manhole, which is what Section "
                   "9 is about."))
    B.append(("h2", "7.4 Uniform gradients, and construction tolerance"))
    B.append(("p", "Two requirements from G203 p29 that are easy to overlook and both matter "
                   "on site:"))
    B.append(("bullet", "“Uniform slopes must be maintained between successive "
                        "manholes.” ",
              "One gradient from chamber to chamber. A pipe is set out from its two ends, so "
              "a gradient that changes along the way cannot be built."))
    B.append(("bullet", "“The lines and level of any pipeline shall not deviate from "
                        "that described in the contract by more than 20mm and combination of "
                        "such deviation shall not create a reverse gradient.” ",
              "Two consequences. Setting out is accurate to about 20 mm, so a pipe designed "
              "with only a few millimetres of fall cannot be built reliably. And a reverse "
              "gradient — any length where the pipe rises in the direction of flow — is "
              "never acceptable, not even within tolerance."))

    # ---------------------------------------------------------------- 8
    B.append(("pagebreak",))
    B.append(("h1", "8. Depth and cover"))
    B.append(("h2", "8.1 The minimum"))
    B.append(("p", "“The minimum depth for sewer pipes shall be 1.3 m to the crown of "
                   "the pipe. This is required to provide pipe protection from external "
                   "loads and to avoid interference with other utilities” (G203 p33)."))
    B.append(("p", "The guideline provides a way out where that cannot be met: “If "
                   "circumstances require installation of a pipe with depth less than 1.3 m "
                   "above the crown, then concrete protection is required. The minimum cover "
                   "above the pipe and its protection shall be 0.5 m.” It also requires "
                   "a design check for shallow pipes beneath major roads or highways, and a "
                   "minimum horizontal clearance of 3 m."))
    B.append(("h2", "8.2 The maximum, and what it really says"))
    B.append(("p", "“The recommended maximum cover for sewer pipes is approximately "
                   "10 - 12 m. Depths with cover greater than this shall be investigated "
                   "with pipe manufacturers to identify any special requirements that may be "
                   "necessary. Where the cost of excavation becomes prohibitive the Engineer "
                   "shall incorporate pumping stations into the design” (G203 p33)."))
    B.append(("p", "Read that carefully, because it is more subtle than it is often quoted:"))
    B.append(("bullet", "It is a recommendation, not a prohibition. ",
              "Going deeper is not forbidden. What is required is that it be investigated "
              "with the pipe manufacturer, because the pipe and the trench have to carry the "
              "load."))
    B.append(("bullet", "It is a range, not a number. ",
              "“approximately 10 - 12 m”. Turning that into a single figure is a "
              "project decision, and it should be stated as one."))
    B.append(("bullet", "It is COVER, not depth to invert. ",
              "Cover is measured to the crown. Depth to the invert is greater by the "
              "diameter of the pipe. Applying the limit to the invert instead is the "
              "stricter reading, and a defensible one, but it is not the same rule."))
    B.append(("bullet", "The trigger for a pump is cost, not depth. ",
              "“Where the cost of excavation becomes prohibitive”. Depth is the "
              "symptom the guideline points at, but the decision it describes is an economic "
              "one — deep trench against pumping station, for the life of the scheme."))
    B.append(("h2", "8.3 Why depth accumulates"))
    B.append(("p", "On flat ground the pipe must keep falling at its minimum gradient while "
                   "the ground does not fall at all. The difference goes into the trench. A "
                   "DN200 sewer at 5 mm/m sinks 5 m below the surface for every kilometre it "
                   "travels across level ground. That arithmetic, and nothing else, is what "
                   "sets how far a gravity network can reach before it needs a pump."))
    B.append(("p", "It also explains why a sewer cannot recover: going downstream the invert "
                   "can only fall. Where the ground rises over a hill, the pipe carries "
                   "straight on underneath and the cover grows by the full height of the "
                   "rise."))

    # ---------------------------------------------------------------- 9
    B.append(("h1", "9. Manholes"))
    B.append(("h2", "9.1 Where they are required"))
    B.append(("p", "The guideline requires a manhole at every change in the sewer — changes "
                   "of direction, gradient, size, at junctions, and at the end of each "
                   "lateral sewer (G203 p30)."))
    B.append(("h2", "9.2 Spacing"))
    B.append(("p", "Table 12 (G203 p30) sets the maximum spacing. It is a maximum, not a "
                   "target — and any departure from it needs permission: “Any "
                   "alteration in the above specified spacing of manholes, consultant has to "
                   "obtain pre-approval from NWS.”"))
    B.append(("table", ["Pipe diameter (mm)", "Maximum spacing (m)"], [
        ["200 to 315", "100"],
        ["350 to 900", "120"],
        ["1 000 to 1 400", "150"],
        ["More than 1 400", "200"],
    ], [2.6, 2.6]))
    B.append(("h2", "9.3 Drops, backdrops and vortex shafts"))
    B.append(("p", "Where a sewer arrives higher than the one it joins, the difference has "
                   "to be handled deliberately (G203 p30):"))
    B.append(("table", ["Difference in invert level", "What is required"], [
        ["Up to 600 mm", "Handled within the chamber by benching and channels"],
        ["More than 600 mm", "A backdrop, constructed EXTERNAL to the manhole"],
        ["More than 2 m", "“specific devices like vortex drop shafts should be used”"],
    ], [2.2, 3.9]))
    B.append(("bullet", "Internal backdrops are restricted. ",
              "They are permissible only for new connections to existing manholes where an "
              "external connection is not practicable, and are not permitted at all on "
              "manholes less than 1.5 m in diameter, because they would block access."))
    B.append(("h2", "9.4 Inlet angle"))
    B.append(("p", "“No inlet pipe at manholes shall have an angle less than 90° "
                   "to the direction of flow” (G203 p30). The purpose is in the "
                   "sentence before it: benching and channels are to be formed “to "
                   "maximise hydraulic efficiency”, with smooth transitions between "
                   "inlet and outlet. A pipe arriving against the flow turns the sewage back "
                   "on itself, and solids drop out where that happens."))
    B.append(("p", "This is one of the hardest rules to satisfy in practice, because street "
                   "junctions are laid out for traffic, not for sewers. Where the geometry "
                   "cannot give 90 degrees, the answer is a purpose-made chamber with a "
                   "curved channel — not a pipe brought in at a slant, and not extra "
                   "chambers added purely to turn the flow."))

    # ---------------------------------------------------------------- 10
    B.append(("pagebreak",))
    B.append(("h1", "10. The design formulas"))
    B.append(("p", "“Gravity sewerage systems shall be designed by using the recognised "
                   "hydraulic formulas such as Colebrook-White, Manning's”, and for "
                   "Colebrook-White the guideline fixes the roughness: “Gravity "
                   "sewerage systems shall be designed using a ks value of 1.5 mm for all "
                   "pipe sizes and materials” (G203 p28)."))
    B.append(("bullet", "One roughness for every material. ",
              "1.5 mm applies to plastic and concrete alike. It is not the roughness of new "
              "pipe — it is a design value that allows for slime, grit and age over the life "
              "of the sewer."))
    B.append(("p", "Sewers run part full, so the full-bore formula is only the starting "
                   "point. The proportion of the full-bore capacity in use at a given depth "
                   "is read from the d/D against q/Q relationship (G203 Figure 2, p28), "
                   "where q is the flow at depth d and Q the flow running full."))
    B.append(("bullet", "A part-full pipe can carry more than a full one. ",
              "Capacity peaks at roughly 94 % of the diameter, not at 100 %, because the "
              "last part of the pipe adds more wetted wall — and therefore friction — than "
              "it adds area. This is why d/D limits are expressed the way they are."))

    # ---------------------------------------------------------------- 11
    B.append(("h1", "11. When gravity runs out"))
    B.append(("p", "Sooner or later a long, flat catchment drives the sewer deeper than it "
                   "is sensible to dig. The guideline's instruction at that point is quoted "
                   "in Section 8.2: investigate with the manufacturer, and where excavation "
                   "cost becomes prohibitive, incorporate pumping stations."))
    B.append(("p", "What a pumping station does hydraulically is simple: it takes the "
                   "sewage from a deep pipe and lifts it, so the sewer downstream can start "
                   "again near the surface and run by gravity once more."))
    B.append(("table", ["Point", "What changes"], [
        ["Upstream of the pump", "An ordinary gravity sewer, at its deepest"],
        ["The station", "A wet well that fills, and pumps that empty it"],
        ["The rising main", "Runs FULL and under pressure. Gradient, d/D and cover-to-fall "
                            "rules do not apply to it"],
        ["Downstream", "A new gravity sewer starting at minimum cover"],
    ], [1.7, 4.4]))
    B.append(("bullet", "A rising main is sized on the pump duty, not the incoming flow. ",
              "The pump does not run at the rate sewage arrives; it fills a wet well and "
              "empties it faster. Sizing the pipe on the arriving flow gives a main that is "
              "far too slow and silts up."))
    B.append(("bullet", "Every pump is a permanent liability. ",
              "It needs land, power, standby plant, an overflow arrangement and maintenance "
              "for the life of the scheme. A pumping station is not a design detail — it is "
              "a commitment, and the count of them is a headline number for any option."))

    # ---------------------------------------------------------------- 12
    B.append(("h1", "12. Where a pipe may be laid"))
    B.append(("p", "Hydraulics decides how a sewer behaves; the street decides where it can "
                   "exist at all. Two requirements from the guideline bear directly on this "
                   "(G203 p33):"))
    B.append(("bullet", "Access, permanently. ",
              "“Location of Sewerage and pipelines shall allow adequate (24 hours per "
              "day x 7 days per week) access to the pipelines and associated chambers for "
              "operation and maintenance purposes.”"))
    B.append(("bullet", "Keep out of wadis. ",
              "“Locating pipelines and associated chambers in wadis and areas subject "
              "to washout during heavy storms shall be avoided.”"))
    B.append(("p", "Beyond the guideline, the corridor a scheme may use is a project "
                   "constraint set with the client and the roads authority. Typical "
                   "constraints, all of which change the design rather than merely the "
                   "drawing:"))
    B.append(("table", ["Constraint", "Why it binds"], [
        ["A road that cannot be opened", "A dual carriageway or highway may be impossible to "
                                         "trench. The sewer must go elsewhere, or cross at "
                                         "right angles by trenchless methods."],
        ["Trenchless crossings", "Expensive and slow. Their number is a cost driver, so "
                                 "crossings should be counted and justified, not scattered."],
        ["Existing underpasses and culverts", "A ready-made crossing at no extra cost. Worth "
                                              "finding before designing around a road."],
        ["Private land", "A chamber or pipe inside a plot is a wayleave problem for the "
                         "life of the asset. Everything belongs in the public corridor."],
        ["Service reservation width", "G203 p33 tabulates corridor widths by pipe size — for "
                                      "example 2.80 m for 600-900 mm, rising to 4.40 m for "
                                      "2 000-2 400 mm."],
    ], [1.9, 4.2]))

    # ---------------------------------------------------------------- 13
    B.append(("pagebreak",))
    B.append(("h1", "13. Worked example — one real pipe, rule by rule"))
    B.append(("p", "This is pipe P-0058 from the Ibri test-area design: a real sewer, with "
                   "its real numbers, worked through every rule in order. Each figure below "
                   "was taken from the design and checked by hand."))
    B.append(("h2", "13.1 What is given"))
    B.append(("table", ["Item", "Value"], [
        ["Pipe", "P-0058, between chambers MH-1093 and MH-1133"],
        ["Length", "63.55 m"],
        ["Properties draining through it", "58"],
        ["Sewer network upstream of it", "822 m"],
        ["Ground at the upper chamber", "354.97 m"],
        ["Ground at the lower chamber", "354.41 m"],
        ["Ground fall along the pipe", "0.56 m, i.e. 8.81 mm/m"],
    ], [2.4, 3.7]))
    B.append(("h2", "13.2 The flow"))
    B.append(("p", "Two project values enter here, neither of them from the guideline: five "
                   "people per property, and 171.3 litres per person per day of wastewater "
                   "generation. Both are project decisions and are recorded as such."))
    B.append(("table", ["Step", "Working", "Result"], [
        ["People", "58 properties x 5 people", "290 people"],
        ["Average daily flow", "290 x 171.3 L/day", "49.68 m³/day"],
        ["Infiltration", "720 L/day/km x 0.822 km (G201 p72)", "0.592 m³/day"],
        ["Peak factor", "See below", "3.57"],
        ["Peak flow", "49.68 x 3.57 + 0.592 = 177.8 m³/day", "2.06 L/s"],
    ], [1.5, 2.9, 1.7]))
    B.append(("bullet", "Where the peak factor comes from, and why it needed a decision. ",
              "Merrimack is stated for catchments of over 100 properties (G201 p71); this "
              "pipe serves 58. Evaluating Merrimack at exactly 100 properties gives "
              "Qadf = 85.65 m³/day = 0.08565 Ml/day, so Qpdf = 2.65 x 0.08565^0.879 = "
              "0.3056 Ml/day and the peak factor is 3.57. That value is then HELD for "
              "anything smaller, rather than extending the formula below the range the "
              "guideline gives it. That holding rule is a project decision, not a "
              "requirement, and a different one would change the answer."))
    B.append(("h2", "13.3 The pipe size"))
    B.append(("table", ["Test", "Result"], [
        ["Smallest main sewer allowed", "OD 200 mm (G203 Table 6, p22)"],
        ["Flow depth at peak", "d/D = 0.218 — the pipe runs about a fifth full"],
        ["Limit", "0.65 for pipes up to 350 mm (G203 Table 10, p27)"],
        ["Governs?", "No. Capacity is nowhere near the limit"],
        ["Could a larger pipe be used to flatten the gradient?",
         "No — prohibited by G203 p29"],
    ], [2.6, 3.5]))
    B.append(("p", "This is the normal case in a residential network: the pipe is at the "
                   "smallest size allowed and runs a fifth full. Size is set by the minimum "
                   "in the guideline, not by the flow."))
    B.append(("h2", "13.4 The gradient"))
    B.append(("table", ["Test", "Result"], [
        ["Table 11, DN200", "5.00 mm/m (G203 p29)"],
        ["Tractive force at 2.06 L/s", "Depends on the tau assumed; at this flow it is of "
                                       "the same order as Table 11"],
        ["Which governs", "The steeper of the two (G203 p27)"],
        ["Adopted", "5.00 mm/m = 0.50 % = 1 in 200"],
        ["Ground offers", "8.81 mm/m — more than enough"],
    ], [2.6, 3.5]))
    B.append(("p", "Fall along the pipe is 0.005 x 63.55 = 0.32 m, which is far more than "
                   "the 20 mm setting-out tolerance of G203 p29, so the pipe can be built "
                   "to the design. Velocity at peak is 0.46 m/s — below the 0.75 m/s "
                   "self-cleansing figure, which is exactly the situation the tractive-force "
                   "method exists for (G203 p27)."))
    B.append(("h2", "13.5 The levels"))
    B.append(("table", ["Level", "Value", "Check"], [
        ["Ground, upper chamber", "354.97 m", ""],
        ["Invert, upper chamber", "352.64 m", "depth 2.33 m"],
        ["Invert, lower chamber", "352.33 m", "0.31 m of fall over 63.55 m"],
        ["Ground, lower chamber", "354.41 m", "depth 2.08 m"],
        ["Minimum cover to crown", "1.30 m required (G203 p33)", "satisfied at both ends"],
    ], [2.0, 2.1, 2.0]))
    B.append(("h2", "13.6 The lesson in the last two numbers"))
    B.append(("p", "The pipe got SHALLOWER along its length, from 2.33 m to 2.08 m. That is "
                   "not luck. The ground here falls at 8.81 mm/m while the pipe only has to "
                   "fall at 5.00 mm/m, so the surface drops away faster than the sewer does "
                   "and the trench gets shallower by the difference — 3.81 mm/m over "
                   "63.55 m, which is the 0.25 m recovered."))
    B.append(("p", "Reverse that relationship and you have the central problem of gravity "
                   "sewerage. Where the ground falls SLOWER than the minimum gradient, the "
                   "difference goes into the trench instead, and it never comes back — going "
                   "downstream the invert can only fall."))
    B.append(("h2", "13.7 What that means over a longer run"))
    B.append(("p", "Take the same DN200 sewer across a kilometre of genuinely flat ground. "
                   "It must still fall at 5 mm/m, so it drops 5 m while the ground drops "
                   "nothing. Starting at 1.5 m deep it arrives 6.5 m deep. A second "
                   "kilometre and it is 11.5 m deep — at the edge of the 10 to 12 m "
                   "recommended maximum cover of G203 p33."))
    B.append(("p", "So on flat ground a DN200 gravity sewer reaches roughly two kilometres "
                   "before depth forces the question of a pumping station. Everything about "
                   "network layout — where the trunk runs, how many collectors gather the "
                   "laterals, how far sewage travels before it reaches one — is ultimately "
                   "about managing that arithmetic."))

    # ---------------------------------------------------------------- 14
    B.append(("pagebreak",))
    B.append(("h1", "14. Every constraint in one place"))
    B.append(("p", "Requirements from the guidelines, with the page each comes from. Nothing "
                   "in this table is a project value."))
    B.append(("table", ["Constraint", "Value", "Source"], [
        ["Minimum main sewer size", "OD 200 mm", "G203 Table 6, p22"],
        ["Minimum rider / property connection", "OD 160 mm", "G203 Table 6, p22"],
        ["Maximum lateral sewer length", "45 m", "G203 Table 6, p22"],
        ["Maximum d/D at peak, up to 350 mm", "0.65", "G203 Table 10, p27"],
        ["Maximum d/D at peak, over 350 mm", "0.50", "G203 Table 10, p27"],
        ["Minimum self-cleansing velocity", "0.75 m/s", "G203 p29"],
        ["Maximum velocity, at design depth", "3.0 m/s", "G203 p27 and p29"],
        ["Minimum gradient by size", "Table 11", "G203 p29"],
        ["Tractive force method", "Smin = K x tau^1.23 x Q^-0.461", "G203 p27"],
        ["Tractive constant K", "2.33e-4 (Q in m³/s) or 5.5e-3 (Q in L/s)", "G203 p27"],
        ["Which minimum governs", "The steeper of the two", "G203 p27"],
        ["No oversizing for flatter slopes", "Prohibited", "G203 p29"],
        ["Uniform slope between manholes", "Required", "G203 p29"],
        ["Line and level tolerance", "20 mm, and never a reverse gradient", "G203 p29"],
        ["Colebrook-White roughness ks", "1.5 mm, all sizes and materials", "G203 p28"],
        ["Minimum cover to crown", "1.3 m", "G203 p33"],
        ["Shallower than 1.3 m", "Concrete protection, 0.5 m cover over it", "G203 p33"],
        ["Minimum horizontal clearance", "3 m", "G203 p33"],
        ["Recommended maximum cover", "approximately 10 - 12 m", "G203 p33"],
        ["Beyond that", "Investigate with manufacturer; pump where excavation cost is "
                        "prohibitive", "G203 p33"],
        ["Maximum manhole spacing", "Table 12: 100 / 120 / 150 / 200 m", "G203 p30"],
        ["Altering manhole spacing", "Pre-approval from NWS", "G203 p30"],
        ["Backdrop required above", "600 mm, constructed external", "G203 p30"],
        ["Maximum backdrop height", "2 m, then vortex drop shaft", "G203 p30"],
        ["Internal backdrops", "Not permitted on manholes under 1.5 m diameter", "G203 p30"],
        ["Minimum inlet angle at a manhole", "90° to the direction of flow", "G203 p30"],
        ["24/7 access to pipes and chambers", "Required", "G203 p33"],
        ["Wadis and washout areas", "Shall be avoided", "G203 p33"],
        ["Wastewater return, domestic and tanker", "85 %", "G201 Table 19, p71"],
        ["Wastewater return, non-domestic", "54 %", "G201 Table 19, p71"],
        ["Peak factor, over 100 properties", "Merrimack: Qpdf = 2.65 Qadf^0.879 (Ml/d)",
         "G201 p71"],
        ["Peak factor, alternative", "Peltier: 1.5 + 1/sqrt(Qm), Qm in L/s", "G201 p72"],
        ["Recommended peak factor ceiling", "5.0", "G201 p72"],
        ["Infiltration, new networks", "720 L/day per km of sewer", "G201 p72"],
        ["Infiltration, existing, groundwater or coastal", "up to 40 % of wastewater flow",
         "G201 p72"],
        ["Infiltration, existing, inland", "10 %", "G201 p72"],
        ["Where detailed land use exists", "Design to BS EN 752 or equivalent, stated",
         "G201 p71"],
    ], [2.5, 2.2, 1.4]))

    # ---------------------------------------------------------------- 15
    B.append(("pagebreak",))
    B.append(("h1", "15. Where the guideline does not decide for you"))
    B.append(("p", "Some things a design needs are not in the guidelines. They have to be "
                   "decided, written down, and tested — and they must never be presented as "
                   "though the guideline required them."))
    B.append(("table", ["Question", "What the guideline gives", "What has to be decided"], [
        ["Tractive tension, tau", "The method and the constant K, but no value",
         "A design value in Pa, and a test of what happens if it is higher"],
        ["Peak factor under 100 properties", "Merrimack, stated for over 100 properties",
         "How the head of the network is peaked, where most pipes are"],
        ["Maximum depth", "“approximately 10 - 12 m” cover, recommended",
         "A single working figure, and whether it applies to cover or to invert"],
        ["People per property", "Nothing", "An occupancy figure, from census or client data"],
        ["Inlet angle in practice", "90°, as a requirement",
         "What to do where street geometry cannot give it, and whether a departure is "
         "recorded as a deviation"],
        ["Gradient rounding", "Nothing",
         "Whether pipes are laid at arbitrary gradients or rounded to a set a contractor "
         "can set out"],
    ], [1.7, 2.2, 2.2]))
    B.append(("bullet", "Say which is which, every time. ",
              "A design that mixes requirements with assumptions cannot be reviewed. The "
              "reviewer cannot tell which numbers are open to challenge and which are not, "
              "and a checker reading a compliance table sees a pass where there was really a "
              "choice."))

    # ---------------------------------------------------------------- 16
    B.append(("h1", "16. Checking the design"))
    B.append(("p", "Every rule in Section 14 is checkable against a finished design, and a "
                   "design should be checked mechanically rather than by eye. Two principles "
                   "make the difference between a check that protects you and one that does "
                   "not."))
    B.append(("bullet", "Check every element, not a sample. ",
              "A rule that holds on 99 % of pipes has failed. The one that breaks it is the "
              "one that will be built wrong."))
    B.append(("bullet", "Never let a check carry an exemption. ",
              "The moment a check is allowed to skip an element — because it is flagged, or "
              "special, or expected to fail — the rule is gone, and the result reads as a "
              "pass. If a design genuinely cannot meet a rule, the honest outcome is a "
              "recorded failure with a reason, not a silent exclusion."))
    B.append(("p", "The same applies to what a check measures. A rule about cover must be "
                   "checked along the whole pipe, not only at the two manholes: ground rises "
                   "between chambers, and the shallowest point is rarely at either end."))

    # ---------------------------------------------------------------- 17
    B.append(("h1", "17. References"))
    B.append(("table", ["Document", "Used for"], [
        ["PAM-GUD-203 Wastewater Design Guidelines v1.0",
         "Network definitions (p21), materials and minimum sizes (Table 6, p22), depth of "
         "flow (Table 10, p27), tractive force and maximum velocity (p27), design formulas "
         "and ks (p28), minimum gradients (Table 11, p29), uniform slope and tolerance "
         "(p29), manholes, spacing, drops and inlet angle (Table 12 and text, p30), cover, "
         "clearance, corridor widths and maximum depth (p33)"],
        ["PAM-GUD-201 General Design Guidelines v1.0",
         "Wastewater return ratios (Table 19, p71), Merrimack peak factor and the "
         "100-property threshold (p71), BS EN 752 requirement (p71), Peltier peak factor and "
         "the recommended ceiling (p72), infiltration allowances (p72)"],
        ["Tutorial T01", "Population, water demand, wastewater return, loads and the full "
                         "flow chain that feeds this tutorial"],
        ["Mara, Sleigh and Taylor (2000)",
         "The tractive-force minimum-slope relationship, as cited in G203 p27"],
    ], [2.2, 4.0]))
    B.append(("p", "Page numbers are the printed page numbers of each guideline, and every "
                   "quoted sentence in this tutorial was read back from the source document "
                   "rather than recalled."))

    return B
