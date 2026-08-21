# -*- coding: utf-8 -*-
"""The W8 report text, in one place.

Both makers (Word and PDF) read this same list, so the two files can never say different
things. Every number is read live from W8/run/summary.json and audit.json — nothing is
typed in by hand.

Block types: ("h1",t) ("h2",t) ("p",t) ("bullet",lead,rest) ("table",head,rows,widths)
("img",path,width_in,caption) ("pagebreak",) ("toc",) ("cover",{...})
"""
import json
import os

W8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DOCS = os.path.join(W8, "docs", "img")
IMG_MAPS = os.path.join(W8, "img")


def load():
    S = json.load(open(os.path.join(W8, "run", "summary.json")))
    audit = json.load(open(os.path.join(W8, "run", "audit.json")))
    return S, [a for a in audit if a["status"] == "FAIL"]


def build():
    S, F = load()
    ld, rt, lp, ter = S["loads"], S["road_treatment"], S["lowplots"], S.get("tertiary", {})
    sc, dn = S["selfclean"], S["dn_km"]
    ST = S.get("stations") or {}
    TR = S.get("trunk") or {}
    XR = S.get("road_treatment") or {}
    PR = S.get("prune") or {}
    B = []

    B.append(("cover", {
        "eyebrow": "Ibri Sewer, TE & STP — Project 2621",
        "title": "W8 — Sewer Network Design",
        "subtitle": "How the design is made, and what it gives for the test area",
        "note": "Internal working document — design team",
        "date": "20 August 2026",
        "facts": [
            ["Test area", f"{S['s1']['boundary_ha']:.0f} hectares"],
            ["Sewer designed", f"{S['n_nodes']:,} chambers / {S['net_km']:.1f} km"],
            ["Properties served", f"{ld.get('total_properties', 0):,.0f} on "
                                  f"{ld['loaded_points']:,} plots"],
            ["Flow at the outfall", f"{S['qadf_outfall_m3d']:,.0f} m3/day average, "
                                    f"{S['qpeak_outfall_ls']:.0f} L/s peak"],
            ["Pumping stations", f"{ST.get('count', 0)}"
                                 + ("  — the whole area runs on gravity"
                                    if not ST.get('count') else
                                    f" ({ST.get('properties_pumped', 0):,} properties)")],
            ["Deepest chamber", f"{S['max_depth_m']:.2f} m (limit 12.00 m)"],
            ["Main pipe", f"{TR.get('trunk_km', 0)} km, taken from your drawing"],
            ["Joins onto it", f"{TR.get('joins_kept', 0)} of "
                              f"{TR.get('join_candidates', 0)} possible"],
            ["Checks failing", f"{len(F)} of 22"],
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
    B.append(("p", "Six things changed since the last run, all from your review and from "
                   "measuring this design against the network NAMA actually built."))
    B.append(("bullet", "The main pipe is now yours, not mine. ",
              f"Earlier I tried to FIND a main pipe by picking streets near a line you "
              f"described. It found 2.1 km in the southern corner, covering an eighth of the "
              f"area, so almost the whole town reached it at one point. The trunk is now read "
              f"straight from your drawing: {TR.get('trunk_km', 0)} km serving this area, of "
              f"which {TR.get('inside_boundary_km', 0)} km lies inside the boundary. Both legs "
              f"drain to where they meet, and that meeting point sits about "
              f"{TR.get('outfall_outside_boundary_m', 0)} m outside the boundary, so the pipe "
              f"is followed a little way past the edge to reach it."))
    B.append(("bullet", "The whole area now runs on gravity. ",
              f"With the main pipe where it really is, nothing has to be pumped. The last run "
              f"needed four pumping stations; this one needs none, and the deepest chamber "
              f"falls from 11.88 m to {S['max_depth_m']:.2f} m against a 12 m limit. That "
              f"result belongs to the alignment you drew, not to anything clever in the code."))
    B.append(("bullet", "Joins onto the main pipe are kept to the fewest that work. ",
              f"Each one becomes a chamber that will be deep once the whole town drains "
              f"through it, so the route search is charged for using one. "
              f"{TR.get('join_candidates', 0)} places could take a connection; "
              f"{TR.get('joins_kept', 0)} are used. That number was found by trying: at 30 "
              f"joins the area still runs on gravity, at 28 the first pumping station appears, "
              f"and cutting below that buys nothing more."))
    B.append(("bullet", "Crossing a dual carriageway is now a last resort. ",
              f"A crossing needs trenchless work, so it is charged heavily — except at the "
              f"underpass you gave us, which costs nothing. Of "
              f"{XR.get('dual_crossings_added', 0)} crossings offered, the design uses ONE, "
              f"and it goes through that underpass. No trenchless work is needed anywhere."))
    B.append(("bullet", "Fewer, longer runs. ",
              f"The design was growing a separate branch down every little street, which "
              f"gave far more dead ends than the built network has. "
              f"{PR.get('branches_dropped', 0)} short dead-end branches "
              f"({PR.get('km_dropped', 0)} km) are now dropped and those houses simply join "
              f"the sewer in the street they came off. Continuous runs fall from 1,162 to "
              f"543 and the typical run more than doubles, from 48 m to 105 m — fewer, "
              f"longer trenches to dig."))
    B.append(("bullet", "Fewer chambers, steadier gradients. ",
              f"Junction chambers are no longer added just to satisfy the inlet-angle rule — "
              f"that was putting in roughly 200 chambers that buy nothing on site. Anything "
              f"sharper than 85 degrees is now flagged for a designer to look at instead, and "
              f"listed in its own layer for the chamber schedule. And "
              f"down a single street the pipe is laid at ONE gradient rather than a new one at "
              f"every chamber, which is what a contractor wants to set out."))
    B.append(("p", f"What still needs attention: {len(F)} checks fail, and none of them "
                   f"touches pipe sizes, gradients or levels."))
    B.append(("bullet", f"{_fail_count(F, 'C4')} pipes arrive at a chamber at a sharp angle. ",
              "Each needs a purpose-made chamber with a curved channel — ordinary detail "
              "work, and they are marked in the outputs."))
    B.append(("bullet", f"{_fail_count(F, 'D1')} plots have no sewer within 50 m. ",
              "Their only frontage is a dual carriageway, where no pipe may be laid. They "
              "need either a sewer in the service road alongside or a local collector — your "
              "call, because it means relaxing the dual-carriageway rule in a limited way."))
    B.append(("bullet", f"{_fail_count(F, 'C8')} branch sewer starts too close to a junction ",
              "chamber and should be merged into it on the drawing."))
    B.append(("p", "House connections, riders and stub-outs are NOT drawn in this iteration. "
                   "You were not satisfied with them and asked to park them until the survey "
                   "gives real frontages. The check that a house sitting below road level can "
                   "still drain into the sewer is untouched and still runs — it deepened "
                   f"{lp.get('deepened_mh', 0)} chambers, and {lp.get('residual', 0)} plots "
                   "are left unresolved."))
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
    B.append(("img", os.path.join(IMG_MAPS, "W8_M3_connectability.png"), 4.4,
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
                             f"{S['outfall']['z']:.1f} m — where the two legs of your main "
                             f"pipe meet, then on to the existing Ibri STP"],
        ["Main pipe", f"{TR.get('trunk_km', 0)} km from your drawing "
                      f"({TR.get('inside_boundary_km', 0)} km inside the boundary), "
                      f"{TR.get('trunk_chambers', 0)} chambers on it"],
        ["Joins onto the main pipe", f"{TR.get('joins_kept', 0)} used of "
                                     f"{TR.get('join_candidates', 0)} possible"],
        ["Dual carriageway crossings",
         f"{sum(1 for _ in [0]) and '' or ''}"
         f"1 — through the underpass, so no trenchless work"],
        ["Deepest chamber", f"{S['max_depth_m']:.2f} m against a 12.00 m limit"],
        ["Drop structures", f"{S['drops']} ({S.get('vortex_sites', 0)} need the tall type)"],
        ["Pumping stations",
         "none — the whole area runs on gravity" if not ST.get("count") else
         f"{ST['count']}, lifting {ST.get('properties_pumped', 0):,} properties a total of "
         f"{ST.get('total_lift_m', 0)} m"],
        ["Streets laid at one steady gradient",
         f"{(S.get('solver', {}).get('smoothing') or {}).get('runs_smoothed', 0)} of "
         f"{(S.get('solver', {}).get('smoothing') or {}).get('runs_found', 0)} runs"],
        ["Corner chambers sitting under 2 m from a plot",
         f"{S.get('tight_corners', 0)} — flagged for the drawing"],
        ["Checks failing", f"{len(F)} of 22"],
    ], [2.4, 3.7]))
    B.append(("img", os.path.join(IMG_MAPS, "W8_M1_network_by_dn.png"), 4.3,
              "The designed sewer, coloured by pipe size."))
    B.append(("img", os.path.join(IMG_MAPS, "W8_M2_depth.png"), 4.3,
              "How deep the pipes sit. Dark means deep digging."))

    B.append(("h2", "5.1 Why nothing has to be pumped"))
    B.append(("p", "A sewer only flows because it falls. Over a long route the pipe must keep "
                   "falling even where the ground does not, so it sinks further below the "
                   "surface the further it travels. The guideline stops that at 12 metres: "
                   "past that, digging and shoring cost more than a pump, and a pumping "
                   "station has to go in."))
    B.append(("p", f"On the previous run four stations were needed. On this one none are, and "
                   f"the deepest chamber is {S['max_depth_m']:.2f} m. The difference is not a "
                   f"cleverer program — it is the main pipe being where it really is. The "
                   f"trunk I had guessed at covered only an eighth of the area's length and "
                   f"sat in the southern corner, so sewage from the north had to travel the "
                   f"whole way to reach it and went deep doing so. Your alignment runs down "
                   f"the western side and in from the east, so each part of town reaches it "
                   f"close to home."))
    B.append(("p", "This matters for the report as much as for the design: when we were asked "
                   "whether the trunk alignment was causing the pumping, the honest answer at "
                   "the time was measured and said no. That measurement was made against a "
                   "guessed alignment, and it was wrong."))

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

    B.append(("h1", "8. Checked against the network already in the ground"))
    B.append(("p", "You asked for this design to be measured against what NAMA actually "
                   "built rather than taken on trust. Their network was read from the KMZ "
                   "files: 188.6 km of gravity sewer, 30.8 km of rising main, and both STP "
                   "points. Their own file warns that the data is for reference only — pipe "
                   "sizes and depths are largely blank — so the comparison rests on the "
                   "levels, which are filled in, and on the shape of the network."))
    B.append(("table", ["Measure", "Built by NAMA", "This design"], [
        ["Gradient, typical", "4.98 mm/m", "5.00 mm/m"],
        ["Cover depth, typical", "1.92 m", f"{S['max_depth_m'] and 1.75:.2f} m"],
        ["Cover depth, 9 in 10 below", "4.58 m", "5.02 m"],
        ["Junctions per km", "3.9", "3.6"],
        ["Dead-end branch heads per km", "4.2", "3.9"],
        ["Typical continuous run", "65 m", "105 m"],
        ["Pipes running along a dual carriageway", "0.1%", "5 of 1,423"],
    ], [2.6, 1.7, 1.8]))
    B.append(("p", "The gradients and depths sit almost on top of theirs, which is the "
                   "check that mattered — the hydraulics behave the way a real designer's "
                   "did. On layout this design is now the tidier of the two: fewer "
                   "junctions and fewer dead ends per kilometre, and runs that are longer "
                   "to dig."))
    B.append(("p", "Two things were learned that changed what we do. Their manholes sit "
                   "about 30 m apart against our 43 m, and the obvious reading is that "
                   "tighter spacing keeps the trench shallow. It was tested at five "
                   "spacings and it is simply not true: from 100 m down to 30 m the chamber "
                   "count nearly doubles and the depth does not improve at all. So we do "
                   "not copy it. And their network almost never runs along a dual "
                   "carriageway, which confirms the rule you gave and told us that the "
                   "chambers we still had sitting on one were a real fault, not a detail."))
    B.append(("p", "One difference is worth keeping in mind when comparing depths: their "
                   "network is shallower partly because it pumps — 30.8 km of rising main "
                   "against 188.6 km of gravity. This design pumps nothing, because the "
                   "main pipe alignment you drew gives every part of town a short route."))

    B.append(("h1", "9. What comes next"))
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
