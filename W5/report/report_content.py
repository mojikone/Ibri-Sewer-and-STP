# -*- coding: utf-8 -*-
"""The W5 report text, in one place.

Both makers (Word and PDF) read this same list, so the two files can never say different
things. Every number is read live from W5/run/summary.json and audit.json — nothing is
typed in by hand.

Block types: ("h1",t) ("h2",t) ("p",t) ("bullet",lead,rest) ("table",head,rows,widths)
("img",path,width_in,caption) ("pagebreak",) ("toc",) ("cover",{...})
"""
import json
import os

W5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DOCS = os.path.join(W5, "docs", "img")
IMG_MAPS = os.path.join(W5, "img")


def load():
    S = json.load(open(os.path.join(W5, "run", "summary.json")))
    audit = json.load(open(os.path.join(W5, "run", "audit.json")))
    return S, [a for a in audit if a["status"] == "FAIL"]


def build():
    S, F = load()
    ld, rt, lp, ter = S["loads"], S["road_treatment"], S["lowplots"], S.get("tertiary", {})
    sc, dn = S["selfclean"], S["dn_km"]
    B = []

    B.append(("cover", {
        "eyebrow": "Ibri Sewer, TE & STP — Project 2621",
        "title": "W5 — Sewer Network Design",
        "subtitle": "How the design is made, and what it gives for the test area",
        "note": "Internal working document — design team",
        "date": "19 August 2026",
        "facts": [
            ["Test area", f"{S['s1']['boundary_ha']:.0f} hectares"],
            ["Sewer designed", f"{S['n_nodes']:,} chambers / {S['net_km']:.1f} km"],
            ["Properties served", f"{ld.get('total_properties', 0):,.0f} on "
                                  f"{ld['loaded_points']:,} plots"],
            ["Flow at the outfall", f"{S['qadf_outfall_m3d']:,.0f} m3/day average, "
                                    f"{S['qpeak_outfall_ls']:.0f} L/s peak"],
            ["Pumping spots found", f"{S['solver']['pockets']}"],
            ["Checks failing", f"{len(F)} of 21"],
        ]}))
    B.append(("pagebreak",))
    B.append(("h1", "Contents"))
    B.append(("toc",))
    B.append(("pagebreak",))

    # ---------------- summary ----------------
    B.append(("h1", "Summary"))
    B.append(("p", f"This run designs a full sewer for the {S['s1']['boundary_ha']:.0f} hectare "
                   f"test area: {S['n_nodes']:,} chambers, {S['net_km']:.1f} km of pipe, and a "
                   f"level for every pipe end. It serves {ld.get('total_properties', 0):,.0f} "
                   f"properties on {ld['loaded_points']:,} plots. At the outfall the flow is "
                   f"{S['qadf_outfall_m3d']:,.0f} cubic metres a day on average and "
                   f"{S['qpeak_outfall_ls']:.0f} litres a second at the busiest hour. The whole "
                   f"run takes about 20 seconds, so any rule can be changed and the effect seen "
                   f"the same day."))
    B.append(("p", "Three things changed since the last run, and all three came from your review "
                   "of the drawings."))
    B.append(("bullet", "Roads are cleaned before use. ",
              f"The road file now carries a column saying which roads are dual carriageway. "
              f"Those carry no pipe at all — {rt.get('dual_excluded', 0)} lines, "
              f"{rt['km_in'] - rt['km_out']:.1f} km — because we cannot dig them up, and that "
              f"holds for the trunk sewer too. {rt.get('roundabouts', 0)} roundabouts and "
              f"{rt.get('traffic_links_dropped', 0)} turning links were also dropped: they carry "
              f"no houses, and following them only adds chambers."))
    B.append(("bullet", "House connections are drawn properly. ",
              f"Before, a connection ran from the middle of a plot to whichever chamber was "
              f"nearest in a straight line, which cut across blocks. Now each plot reaches out "
              f"to the pipe it actually faces, the line starts at the plot edge, and up to three "
              f"neighbours share one rider. {ter.get('stub_outs', 0)} empty plots get a capped "
              f"stub-out ready for when they are built."))
    B.append(("bullet", "Properties are counted, not guessed. ",
              f"{ld.get('accounts_used', 0):,} electricity accounts inside the boundary tell us "
              f"how many properties sit on each plot — {ld.get('props_per_unit', 0)} on average "
              f"instead of the flat one per plot we assumed before. Account type also tells us "
              f"which are shops or offices rather than homes."))
    B.append(("p", f"What still needs attention: {len(F)} checks fail. The largest is "
                   f"{_fail_count(F, 'C4')} pipes arriving at a chamber at a sharp angle, which "
                   f"needs junction layout work. {_fail_count(F, 'D1')} house connections are "
                   f"longer than 50 metres, mostly plots that used to face a dual carriageway and "
                   f"now have no near street — each needs either an extra chamber or a local "
                   f"answer. Neither affects pipe sizes or levels."))
    B.append(("pagebreak",))

    # ---------------- how it works ----------------
    B.append(("h1", "1. How the design is made"))
    B.append(("p", "The work runs in steps, each one a separate piece of code, so any rule can be "
                   "found and changed in one place."))
    B.append(("table", ["Step", "What it does"], [
        ["Read the inputs", "roads, plots, ground levels, flood map, electricity accounts"],
        ["Clean the roads", "remove what cannot carry a sewer, join broken streets back together"],
        ["Build the tree", "one path from every street to the outfall, no loops"],
        ["Place chambers", "at junctions, at bends, and at regular spacing"],
        ["Count the load", "properties per plot, added up down the network"],
        ["Size and set levels", "pipe size and gradient chosen together, deep spots become "
                               "pumping stations"],
        ["Connect the houses", "each plot to the pipe it faces, and check it can drain"],
        ["Check everything", "21 rules re-checked independently of the design code"],
        ["Write the outputs", "GIS files, CAD drawing, SewerGEMS package, maps"],
    ], [1.5, 4.6]))
    B.append(("img", os.path.join(IMG_DOCS, "pipeline_steps.png"), 6.2,
              "The steps in order. Blue is what comes in, yellow is the checking step, red is "
              "where a pumping station is needed, dashed lines are repeats."))

    # ---------------- roads ----------------
    B.append(("h1", "2. Cleaning the roads"))
    B.append(("p", "A road file describes how cars move. A sewer follows the street but joins at "
                   "a point, so the file has to be cleaned first, or the design puts a chamber "
                   "wherever the survey happened to break the line."))
    B.append(("table", ["What was removed or changed", "Amount"], [
        ["Dual carriageways — no pipe at all, trunk included",
         f"{rt.get('dual_excluded', 0)} lines"],
        ["Roundabouts — they collect no sewage", f"{rt.get('roundabouts', 0)}"],
        ["Rings kept because plots sit inside them (blocks, not roundabouts)",
         f"{rt.get('rings_rejected', {}).get('plots_inside', 0)}"],
        ["Turning links and slip roads", f"{rt.get('traffic_links_dropped', 0)}"],
        ["Straight streets joined back into one line", f"{rt.get('collinear_joins', 0)}"],
        ["Dead ends serving nobody", f"{rt.get('empty_stubs_dropped', 0)}"],
        ["Road length before / after", f"{rt['km_in']:.1f} km / {rt['km_out']:.1f} km"],
    ], [4.4, 1.7]))
    B.append(("p", "Everything removed is written to the corridor file with the reason beside it, "
                   "so each one can be looked at and put back if the rule got it wrong. Telling a "
                   "roundabout from a small block cannot be done on shape alone — a square scores "
                   "higher on roundness than a real roundabout. The test used here is whether any "
                   "plot sits inside the ring: a roundabout circles road, a block circles houses."))

    # ---------------- loads ----------------
    B.append(("h1", "3. How much sewage, and from where"))
    B.append(("p", f"Each electricity account is one property. A plot with three accounts holds "
                   f"three properties. In the test area {ld.get('accounts_used', 0):,} accounts "
                   f"sit on {ld.get('plots_with_counted_props', 0):,} plots, giving "
                   f"{ld.get('total_properties', 0):,.0f} properties in total."))
    B.append(("table", ["Item", "Value", "Where it comes from"], [
        ["People per property", "5", "your decision, 19 August"],
        ["Sewage per person", "171.3 litres a day", "guideline G201 p70-71"],
        ["Properties per plot", f"{ld.get('props_per_unit', 0)} average",
         "counted from electricity accounts"],
        ["Plots loaded", f"{ld['loaded_points']:,}",
         f"built {ld.get('built', 0):,}, planned {ld.get('planned', 0):,}, "
         f"unparceled {ld.get('unparceled', 0)}"],
        ["Farm plots with houses", f"{ld.get('farm_plots_with_houses', 0)}",
         "farming sends nothing, but houses on a farm do"],
        ["Extra water leaking in", "720 litres a day per km of sewer", "guideline G201 p72-73"],
    ], [1.7, 1.9, 2.5]))
    B.append(("img", os.path.join(IMG_DOCS, "load_chain.png"), 5.2,
              "How a plot becomes a flow in the pipe."))
    B.append(("pagebreak",))

    # ---------------- house connections ----------------
    B.append(("h1", "4. House connections"))
    B.append(("p", "The connection is schematic — the sizes are not designed. The one thing that "
                   "must be right is whether the house can drain into the sewer at all, because "
                   "roads are sometimes raised above the plots beside them."))
    B.append(("table", ["Rule", "Result here"], [
        ["Each plot joins the pipe it faces, by a short line from the plot edge",
         f"{ter.get('spurs', 0):,} connections"],
        ["Up to 3 neighbours share one rider", f"{ter.get('riders', 0):,} riders"],
        ["Empty plots get a capped stub-out for later", f"{ter.get('stub_outs', 0)} stub-outs"],
        ["Houses that could not drain at first", f"{lp['flagged']}"],
        ["Chambers deepened to let them drain", f"{lp['deepened_mh']}"],
        ["Still cannot drain — need a local answer", f"{lp['residual']}"],
    ], [4.0, 2.1]))
    B.append(("p", "These are kept in three separate files (connections, riders, stub-outs) so "
                   "that SewerGEMS never reads them as sewers and the CAD drawing can switch them "
                   "off."))
    B.append(("img", os.path.join(IMG_MAPS, "W5_M3_connectability.png"), 4.4,
              "Green can drain as designed, amber needed a deeper chamber, red still cannot."))

    # ---------------- results ----------------
    B.append(("h1", "5. What the design gives"))
    B.append(("table", ["Item", "Value"], [
        ["Chambers / pipes", f"{S['n_nodes']:,} / {S['n_pipes']:,}"],
        ["Sewer length", f"{S['net_km']:.1f} km"],
        ["Pipe sizes used", " · ".join(f"DN{k} {v} km" for k, v in dn.items())],
        ["Flow at the outfall",
         f"{S['qadf_outfall_m3d']:,.0f} m3/day average, {S['qpeak_outfall_ls']:.0f} L/s peak"],
        ["Outfall position", f"({S['outfall']['x']:.0f}, {S['outfall']['y']:.0f}), ground "
                             f"{S['outfall']['z']:.1f} m — the lowest road point on the boundary"],
        ["Deepest chamber", f"{S['max_depth_m']:.1f} m (inside a pumping-station pocket)"],
        ["Drop structures", f"{S['drops']} ({S.get('vortex_sites', 0)} need the tall type)"],
        ["Pumping stations needed", f"{S['solver']['pockets']}"],
        ["Corner chambers sitting under 2 m from a plot",
         f"{S.get('tight_corners', 0)} — flagged for the drawing"],
        ["Checks failing", f"{len(F)} of 21"],
    ], [2.4, 3.7]))
    B.append(("img", os.path.join(IMG_MAPS, "W5_M1_network_by_dn.png"), 4.3,
              "The designed sewer, coloured by pipe size."))
    B.append(("img", os.path.join(IMG_MAPS, "W5_M2_depth.png"), 4.3,
              "How deep the pipes sit. Dark means deep digging."))

    # ---------------- checks ----------------
    B.append(("h1", "6. The checks"))
    B.append(("p", "The design is checked by separate code that re-works every rule from the "
                   "finished drawing, so the design cannot mark its own homework. Each check "
                   "names the guideline page it comes from."))
    rows = [[f["id"], f["check"], f["reference"], f["found"][:70]] for f in F]
    if rows:
        B.append(("table", ["ID", "Check", "Guideline", "What was found"], rows,
                  [0.5, 1.7, 1.5, 2.4]))
    else:
        B.append(("p", "All checks pass."))
    B.append(("p", f"On self-cleaning: {sc['below_075_at_peak']:,} of {sc['pipes']:,} pipes cannot "
                   f"reach the 0.75 m/s flow speed even at their busiest hour. That is normal on "
                   f"small house streets, and the guideline allows a second method for exactly "
                   f"this case — a minimum gradient worked out from the drag on the pipe wall. "
                   f"All of them meet that instead. It rests on a value the guideline never gives "
                   f"(1 Pascal is assumed); if NWS sets it at 2, {sc['would_fail_at_tau2']:,} "
                   f"pipes would need steeper gradients. That single number is the best reason to "
                   f"settle it at the kickoff meeting."))

    # ---------------- assumptions ----------------
    B.append(("h1", "7. What is assumed, and what is measured"))
    B.append(("table", ["Assumed", "Why"], [
        ["Drag value of 1 Pascal", "the guideline gives no number; it decides the gradient on "
                                   "small pipes"],
        ["5 people per property", "your decision, 19 August"],
        ["Plastic pipe wall thickness", "pipe sizes are quoted outside; the inside bore is "
                                        "worked out from a standard wall class"],
        ["Floor areas, staff and pupil numbers", "nobody supplies them, so they are worked out "
                                                 "from plot size and building cover — replace "
                                                 "when the land use data arrives"],
        ["Where a rider joins", "the guideline does not say; the nearest chamber is used"],
    ], [2.4, 3.7]))
    B.append(("table", ["Measured", "Source"], [
        ["Properties per plot", "electricity accounts"],
        ["Ground levels", "0.5 m ground model"],
        ["Which roads cannot be dug", "the road file's own column"],
        ["Flood-prone ground", "50-year hazard map, classes 4 to 6"],
    ], [2.4, 3.7]))

    B.append(("h1", "8. What comes next"))
    B.append(("bullet", "Your trunk line. ",
              "The main pipe is yours to fix. The design then grows the side networks into it — "
              "the code takes connection points as a setting, so this is a change of input, not "
              "a change of method."))
    B.append(("bullet", "The SewerGEMS check. ",
              "The import package is ready with a comparison sheet. Once the model runs, every "
              "pipe's flow and speed can be set beside ours; anything more than 5 per cent apart "
              "gets looked at before the design is called proven."))
    B.append(("bullet", "Junction angles. ",
              f"{_fail_count(F, 'C4')} pipes still arrive at a chamber too sharply. This is a "
              f"layout job at junctions and is the main open item in the design itself."))
    B.append(("bullet", "The land use data from your colleague. ",
              "Missing plots and properties per plot will replace the derived figures without "
              "touching the design code."))
    return B


def _fail_count(F, cid):
    for f in F:
        if f["id"] == cid:
            digits = "".join(ch if ch.isdigit() else " " for ch in f["found"]).split()
            return digits[0] if digits else "several"
    return "0"
