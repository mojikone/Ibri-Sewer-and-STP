"""W11a Design Review - the Word report.

An INTERNAL engineering report for the design team, not a client deliverable: it says what
was found wrong, what was changed, and what I would do next. It reuses W9/report/doc.py so
it looks like the rest of the project's documents.

Every number in here is measured and is traceable to a run in W11a/run/ or to a stage's own
printed output. Where a number is an assumption it says so, and where a rule is ours rather
than a guideline's it says that too.

    python build_review.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W11A = os.path.dirname(HERE)
REPO = os.path.dirname(W11A)
sys.path.insert(0, os.path.join(REPO, "W9", "report"))

import doc as D                                                        # noqa: E402
from docx.shared import Pt                                             # noqa: E402

OUT = os.path.join(HERE, "W11a_Design_Review_R1.docx")
REV = "R1"
DATE = "2 September 2026"


def title_page(d):
    for _ in range(5):
        D.p(d, "", space_after=0)
    D.p(d, "2621 IBRI SEWERAGE, TREATED EFFLUENT AND STP", bold=True, size=11,
        colour=D.MID, space_after=2)
    D.p(d, "Design Review and Recommendations", bold=True, size=26, colour=D.BLUE,
        space_after=4)
    D.p(d, "W11a - the redesign of the whole network", size=13, colour=D.GREY,
        space_after=18)
    D.table(d, ["", ""], [
        ["Revision", REV],
        ["Date", DATE],
        ["Status", "Internal engineering review - NOT for issue to NWS"],
        ["Prepared for", "Renardet design team"],
        ["Supersedes", "nothing; this is the first review of W11a"],
        ["Reads with", "_BRAIN/08_DESIGN_PHILOSOPHY.md and _BRAIN/02_DESIGN_CRITERIA.md"],
    ], widths=[4.0, 12.0], font=9.5)
    D.p(d, "")
    D.callout(
        d, "What this document is.",
        "An honest account of the state of the W11a design pipeline: the rules that turned "
        "out to be wrong, the defects found in our own auditor, the numbers that are now "
        "trustworthy, and my recommendations. It is written for engineers who will "
        "disagree with parts of it. Nothing here is client-facing register.",
        fill="EEF3FA", colour=D.MID)
    D.pagebreak(d)


def summary(d):
    D.h(d, 1, "Summary")
    D.p(d, "The single most useful thing to come out of this round is that our own rule, "
           "not the ground, was the biggest constraint on the design.", bold=True)
    D.p(d,
        "W10 was audited against twenty-two checks. Three passed, twelve failed, and seven "
        "could not run at all because the published layers did not carry the fields the "
        "checks read. That result held up. What did not hold up was the diagnosis. Two of "
        "the headline defects we had been carrying since W10 were artefacts of how we "
        "measured, and one whole class of failure was created by a rule we wrote "
        "ourselves.")
    D.p(d, "")

    D.h(d, 2, "The five findings that matter")
    for lead, txt in [
        ("A wadi crossing is legal, and forbidding it cost us the network.",
         "PAM-GUD-203 p30 §4.4.1 and p33 forbid pipes and chambers IN a wadi because of "
         "washout. They do not forbid crossing one - PAM-GUD-201 §9.3 sets out a full "
         "procedure for doing exactly that, and G203-p52 §8.2.4 gives the cover to use. "
         "Our rule deleted every wadi contact, which severed the corridor network into "
         "1,381 pieces and the trunk into 108, against 2 when the same alignment is noded "
         "on its own. Distinguishing along from across took the corridor network to 784 "
         "pieces and kept 2,428 scheduled crossings."),
        ("W10 never had 310 loops.",
         "It has zero at any tolerance a surveyor or a GIS would use. The loop count is an "
         "artefact of how hard the endpoints are snapped: 7,919 pieces and 0 cycles at "
         "10 mm, 105 pieces and 311 cycles at 2.5 m - the same file. The step at exactly "
         "1.00 m is a buffer(1.0) in the corridor stitcher closing 3,255 gaps at once. "
         "Disconnection and loops were never two defects; they were one, and it is that "
         "the layer publishes no node identity."),
        ("The auditor had six defects of its own, one of them a build-stopper.",
         "It demanded 50 mm more cover than the criteria function lays, at every diameter, "
         "so a design built correctly failed a blocking check on every reach. It sampled "
         "wadi ground at the midpoint only and missed 40 % of the contact. It scored the "
         "hazard grid's nodata as a pass. And it required the network to be a single "
         "connected component, which no compliant design with a satellite works can be."),
        ("Half the network has no flood answer at all.",
         "The 50-year hazard grid covers 47-49 % of the corridor samples. Every statement "
         "we make about wadis is a statement about the tested half. This is now published "
         "beside every wadi result instead of being silently scored as a pass, and it is "
         "the single largest data gap in the layout."),
        ("A whole pipeline stage was missing.",
         "Nothing accumulated the chamber loads down the graph, so no reach knew what it "
         "carried and the chain stopped before levels and sizes. The ten stages were built "
         "in parallel against a shared contract and this step fell between two of them - "
         "which is a fair warning about how that kind of parallel build fails."),
    ]:
        D.bullet(d, txt, lead=lead)


def part_a(d):
    D.part(d, "A", "What was wrong with the rules")

    D.h(d, 1, "The wadi rule")
    D.p(d, "This is the most consequential change in W11a, so it is worth stating "
           "precisely what was wrong and why the new rule is defensible.")
    D.h(d, 2, "What the guidelines actually say")
    D.table(d, ["Source", "What it says"], [
        ["G203-p30 §4.4.1, p33", "Pipelines AND chambers are prohibited in wadis and "
                                 "flood-prone / washout areas."],
        ["G201-p85 §9.3", "A wadi crossing requires bed profiles and cross-sections, "
                          "1:20 / 1:50 / 1:100 flood frequency, bed material and bed-level "
                          "change, from CAA and MoAFWR, with MoAFWR approval."],
        ["G201-p86", "DI over the crossing plus 15 m each side; protection to PAM-STD-404; "
                     "anti-flotation check; isolation and air valves both sides of an active "
                     "or major crossing. Also: no VALVE CHAMBERS or MARKER POSTS in the bed "
                     "or on the embankments - a force-main clause about those structures, "
                     "and NOT the authority for a gravity manhole."],
        ["G203-p52 §8.2.4", "1.5 m to crown at a wadi crossing - but this sits in the FORCE "
                            "MAIN section. G203 gives no special cover for a GRAVITY sewer "
                            "at a wadi; G201-p86 raises it to 2.0 m in soft soil."],
    ], widths=[4.2, 11.8], font=9)
    D.p(d, "")
    D.callout(
        d, "Two citations in H1a were wrong, and I corrected them on 2 September.",
        "H1a item 2 cited G201-p86 for the prohibition on chambers. That clause is about "
        "valve chambers and marker posts on a force-main crossing. The authority for a "
        "gravity manhole is G203-p30 §4.4.1 and p33, whose word is \"avoided\" - and reading "
        "\"avoided\" as \"prohibited\" is our project decision, now recorded as one. H1a item 3 "
        "applied the 1.5 m cover to gravity sewers; that figure is the force-main one. We "
        "keep 1.5 m as a conservative PROJECT rule pending a scour-depth check, which is "
        "what actually governs - so a gravity reach at 1.30 m over a crossing is short of "
        "OUR rule, not of the guideline's, and stage 3's 35 such reaches must be reported "
        "that way. This is exactly the failure the project already has a rule against: "
        "quote from the source, never from memory.")
    D.p(d, "")
    D.p(d, "A guideline that prints a four-item procedure for building a wadi crossing is "
           "not a guideline that forbids one. We were reading a prohibition on PRESENCE as "
           "a prohibition on PASSAGE.", bold=True)

    D.h(d, 2, "What it cost")
    D.table(d, ["Measure", "Deleting every crossing", "H1a: along deleted, across kept"], [
        ["Corridor components", "1,381", "784"],
        ["Trunk components as stage 4 sees it", "108", "74"],
        ["Wadi length deleted", "170 km", "67 km"],
        ["Crossings scheduled", "0", "2,428"],
        ["Load-bearing plots with a corridor", "97.4 %", "98.0 %"],
        ["Load with no corridor", "1,812 m³/d", "1,426 m³/d"],
        ["Drainage systems out of stage 4", "1,257", "773"],
    ], widths=[6.4, 4.8, 4.8], font=9, align_right={1, 2})
    D.p(d, "")
    D.p(d, "The design cannot be built as 1,257 separate drainage systems. That number was "
           "never a finding about Ibri; it was a finding about our rule.")

    D.h(d, 2, "The new rule, and the one number in it that is ours")
    D.p(d, "Philosophy H1a makes a crossing legal when four things hold: the contact is a "
           "single contiguous run and square within a stated skew tolerance; no chamber "
           "sits on wadi ground or the embankment; cover is 1.5 m to crown; and it is "
           "entered in the crossings schedule with a CROSS_ID carrying the G201 §9.3 "
           "obligations. Anything else on wadi ground is prohibited.")
    D.p(d, "The along/across test is geometric rather than a length threshold. At the "
           "middle of the on-wadi run we probe perpendicular to the pipe until both banks "
           "are found. A pipe crossing square has a contact no longer than the band is "
           "wide across it; a pipe running down the band has a long contact and a narrow "
           "perpendicular extent. The ratio is the measurement.")
    D.callout(
        d, "Declared as ours, not theirs.",
        "H1 says a crossing is \"perpendicular\". The tolerance on that word - 1/cos 30° - "
        "is a PROJECT rule, declared in w11a.audit and read from there by every stage. The "
        "guidelines give the cover at a crossing and the procedure for one, but never say "
        "how square it must be, and inventing a guideline number is prohibited. An earlier "
        "70 m crossing-length assumption has been withdrawn: it was borrowed from the "
        "dual-carriageway rule and had no basis at all.")

    D.h(d, 1, "Topology, and two numbers we had been quoting wrongly")
    D.h(d, 2, "The loop count moves with the tolerance")
    D.table(d, ["Snap (m)", "Nodes", "Components", "Cycles"], [
        ["0.01", "28,855", "7,919", "0"],
        ["0.10", "28,833", "7,897", "0"],
        ["0.25", "28,815", "7,879", "0"],
        ["0.50", "28,792", "7,856", "0"],
        ["1.00", "25,519", "4,601", "18"],
        ["2.50", "20,730", "105", "311"],
    ], widths=[3.0, 4.0, 4.0, 4.0], font=9, align_right={0, 1, 2, 3})
    D.p(d, "")
    D.p(d, "Measured on W10's 20,936 published pipes. The 311 loops we have been quoting "
           "exist only when the layer is squeezed hard enough to hide the fact that it is "
           "in 7,919 pieces. The step at exactly 1.00 m is our own stitcher: 91.4 % of its "
           "links stop 1.000 m short of what they join.")
    D.p(d, "The rule that follows is H16: every pipe publishes US_NODE and DS_NODE, and "
           "the declared graph must match the drawn geometry. Topology is written down, "
           "never inferred from geometry, because a tolerance is a guess about intent.",
        bold=True)

    D.h(d, 2, "H15 forbade a design the TOR requires")
    D.p(d, "The auditor required exactly one connected component. Philosophy §8a "
           "contemplates satellite works and on-site systems, and the TOR requires every "
           "plot to be served - not that one network serve them. A correct design with a "
           "satellite works therefore failed a blocking check. H15 now reads: zero loops, "
           "and each component terminates at exactly one outfall. A satellite works is "
           "legal; a piece that drains nowhere never was.")

    D.h(d, 1, "The auditor's own defects")
    D.table(d, ["#", "Defect", "Consequence"], [
        ["1", "Outside-diameter allowance hardcoded at 0.10 m while criteria lay to 0.05 m",
         "Every reach 50 mm short of H3 at every diameter - a BLOCKING failure caused "
         "entirely by the auditor. W10's cover failure falls from 45.92 km to 34.78 km."],
        ["2", "GRADIENT_BY is 11 characters; a shapefile truncates at 10",
         "The check demanded a field that could never exist. Renamed GRAD_BY."],
        ["3", "Diameter floors keyed with spaces (\"sub main\")",
         "A dictionary miss returned None and the pipe was silently skipped. An "
         "unclassifiable tier now fails rather than passing quietly."],
        ["4", "Graph builder took geoms[0] of a MultiLineString",
         "A layer could look connected because half of it was invisible."],
        ["5", "R4 sampled the midpoint only",
         "Found 1,089 reaches on wadi ground where full-length sampling finds 1,766. It "
         "was missing 40 % of them."],
        ["6", "R4 scored nodata as a pass",
         "The grid's nodata is -9999.0, which IS finite, so even the finiteness guard let "
         "it through. Read properly, 51 % of samples have no answer."],
    ], widths=[1.0, 6.2, 8.8], font=8.5)
    D.p(d, "")
    D.callout(
        d, "The lesson worth keeping.",
        "Every one of these was found by two things disagreeing, never by review. The "
        "auditor and the criteria disagreed about wall thickness; the stage and the "
        "auditor disagreed about which reaches were on a wadi; the declared topology and "
        "the drawn geometry disagreed about connectivity. Where a stage now needs the "
        "auditor's answer it CALLS the auditor rather than re-implementing it, and where "
        "two samplers still differed at the boundary the stage asks the auditor which rows "
        "fail and removes exactly those.",
        fill="EEF3FA", colour=D.MID)


def part_b(d, flows):
    D.part(d, "B", "Where the design stands")

    D.h(d, 1, "What runs, and what it produces")
    D.table(d, ["Stage", "Status", "Result"], [
        ["1 scope", "runs", "187 settlements, every one on the central system. The G201-p80 "
                            "25 km fall-back never fires - the furthest zero-load "
                            "settlement is 6.34 km from the core."],
        ["2 corridors", "runs", "25,122 corridors, 2,232.9 km, 784 components. 2,428 wadi "
                                "crossings scheduled, 475 along-wadi runs deleted. 98.0 % "
                                "of load-bearing plots have a corridor within 60 m."],
        ["3 trunk", "runs", "85.55 km gravity, 758 chambers, DN200-1700, 73,442 m³/d and "
                            "1,350 L/s at the works, 3 pumping stations, deepest cover "
                            "11.86 m with nothing past the 12 m cap."],
        ["4 hierarchy", "runs", "773 drainage systems. Trunk arrives in 74 pieces - a "
                                "defect, see below."],
        ["5 chambers", "runs", "50,033 chambers, 27.5 per km, 36 m mean spacing. 2,788 "
                               "inlets under 90°."],
        ["5b tertiary", "runs", "52,188 m³/d reaches a chamber (70 %); 22,513 m³/d over "
                                "24,554 plots does not."],
        ["5c flows", "NEW", flows],
        ["6 levels and sizes", "blocked", "waits on stage 5c."],
        ["7 stations, 8 packages, 9 export", "blocked", "wait on stage 6."],
    ], widths=[3.4, 2.0, 10.6], font=8.5)

    D.h(d, 1, "The trunk, measured rather than argued about")
    D.p(d, "Stage 4 had been reporting the trunk's fragmentation as one defect. Noding the "
           "same 85.5 km at 10 mm from each available source separates it into two:")
    D.table(d, ["Source", "Features", "Length", "Components"], [
        ["The user's drawing, as given", "54", "85.5 km", "3"],
        ["Stage 3's designed trunk", "754", "85.5 km", "4"],
        ["Stage 2 corridors, SRC = main_pipe", "667", "80.5 km", "58"],
    ], widths=[7.0, 3.0, 3.0, 3.0], font=9, align_right={1, 2, 3})
    D.p(d, "")
    D.bullet(d, "the corridor treatment shreds the trunk from 3 pieces to 58 and loses "
                "5.0 km of it, which is a stage 2 defect and not an alignment one;",
             lead="First,")
    D.bullet(d, "stage 4 then takes a 4-piece trunk to 74, because the trunk's chamber "
                "coordinates do not coincide with the corridor node set it is matched "
                "into. Raised as OPEN-S4-1.", lead="Second,")
    D.p(d, "")
    D.p(d, "Until one of those is fixed, the drainage-system count is an artefact of the "
           "mismatch and not a design result. The report says so rather than letting 773 "
           "stand as a finding.", bold=True)

    D.h(d, 1, "Defects that are real and still open")
    D.table(d, ["What", "Size", "Why it matters"], [
        ["Chambers on wadi ground", "2,354 of 50,033",
         "H1a item 2 admits no exemption for a chamber (G203-p30 §4.4.1, p33). Only 48.2 % "
         "of chambers sit on a valid hazard cell, so this is the tested half. Sliding them "
         "clear fixes only 319: the corridors run DOWN the wadis, 100.4 km of them, and "
         "587 chambers have no non-wadi ground within 250 m."],
        ["Plots not connected by stage 5b", "24,554 plots, 22,513 m³/d",
         "30.1 % of the load - but the 45 m rule owns only 8.59 % of it. The largest single "
         "group, 9.63 %, is a drainability test run against PLACEHOLDER levels. See Part C."],
        ["Inlets under 90°", "2,788",
         "H10 / G203-p30. Each needs a purpose-made chamber with a swept channel."],
        ["Network reaching no trunk", "729 km, 40 %",
         "Drains to a provisional outfall. Mostly a consequence of the trunk "
         "fragmentation above."],
        ["Trunk on a dual carriageway", "535 m over 10 reaches",
         "A defect of the INPUT alignment. The main pipe is an input, so this needs the "
         "client's decision, not a re-route by us."],
        ["Trunk on wadi ground", "10.98 km over 152 reaches",
         "Measured before H1a. Most is likely to classify as legal crossings once stage 3 "
         "applies the same test - it does not yet."],
    ], widths=[4.6, 3.4, 8.0], font=8.5)


def part_c(d):
    D.part(d, "C", "What I would do, and why")

    D.h(d, 1, "On BAT: do not choose, carry both")
    D.p(d, "2,231 properties and 1,752 m³/d sit 22-25 km from the core, above every "
           "decentralised ceiling in the guidelines and below the density that makes "
           "conveyance obviously right. My recommendation is to carry BOTH a conveyance "
           "option and a satellite works into the options appraisal rather than deciding "
           "here.", bold=True)
    D.p(d, "The reasoning is not indecision. The options doctrine already requires three "
           "options per system appraised over seven criteria on a 25-year life-cycle cost "
           "at 5 %, with NWS setting the weights. Choosing between conveyance and a "
           "satellite works on engineering judgement now would pre-empt exactly the "
           "comparison that process exists to make, and it would do so before we have the "
           "two inputs that decide it: a confirmed treated-effluent demand near those "
           "settlements, and the operating-cost basis NWS want used.")
    D.p(d, "There is also a specific reason to distrust an early decision here. Manning is "
           "roughly 86 % of a pumping station's life-cycle cost and energy about 0.4 %. "
           "Any comparison that ranks options on energy or on capital alone will get this "
           "question wrong, and a satellite works adds an operating point - which is the "
           "expensive kind of cost, not the cheap kind.")
    D.callout(
        d, "The trap to avoid.",
        "A satellite works looks cheap on a spreadsheet that counts pipe and pumps and "
        "does not count an operator visiting a second site for twenty-five years. Price "
        "the visits, or the comparison is decided by whichever cost we forgot.")

    D.h(d, 1, "The recommendations, ranked by what they change")
    for n, (lead, txt) in enumerate([
        ("Get full-coverage flood mapping.",
         "51 % of the network has no wadi answer either way. Every layout decision we make "
         "about wadis today is provisional on half the area. This is a data request to "
         "NWS / MoAFWR, it is cheap relative to what it de-risks, and nothing else on this "
         "list unblocks as much."),
        ("Get NWS to confirm the design tractive stress.",
         "97 % of the network's self-cleansing rests on the tractive route because no legal "
         "gradient makes a lightly loaded DN200 reach 0.75 m/s. The guideline gives no "
         "value for τ; we assume 1.0 Pa (GAP-9). At 2.0 Pa the required gradient rises by "
         "a factor of 2.35, which changes depths, changes pumping, and changes the cost of "
         "the whole scheme. This is the largest single hydraulic assumption in the design "
         "and it is one question to one client."),
        ("Get the existing works inlet invert.",
         "H14 says an existing structure's invert is fixed and the design yields to it, "
         "soffit to soffit. Without it the trunk is laid to its own level - currently "
         "319.94 m aOD, 8.78 m below ground at the works - and that level is published for "
         "confirmation rather than agreed. If it is wrong, it is wrong at the deepest and "
         "most expensive end of the scheme."),
        ("Make stage 3 design on the corridor graph.",
         "The trunk is the one alignment where fragmentation is fatal rather than untidy, "
         "and it is currently designed on one geometry and consumed on another. Either "
         "stage 3 designs on the corridor node set or stage 4 snaps the trunk into it. "
         "Until then the drainage-system count is not a design result."),
        ("Solve the 45 m tertiary problem deliberately, not by adding chambers everywhere.",
         "30 % of the load currently has no compliant connection. Mean chamber spacing is "
         "already 36 m, so the failures are not caused by coarse spacing in general - they "
         "are plots whose offset to the carrier eats most of the 45 m budget before the "
         "run along the carrier starts. The honest options are a chamber placed for the "
         "plot rather than for the run, a shared connection where G203 allows it, or a "
         "recorded decision that a particular frontage is not served. Adding chambers "
         "uniformly would buy compliance with maintenance cost we do not need."),
        ("Do not try to re-site the 2,354 chambers on wadi ground - re-route the corridors.",
         "I had this wrong. Sliding chambers clear fixes only 319 of them; 587 have no "
         "non-wadi ground within 250 m in any direction, because the corridors run DOWN the "
         "wadis rather than across them - 100.4 km of on-wadi corridor with contiguous runs "
         "up to 789 m. That is a stage 2 routing problem wearing a chamber-placement "
         "costume, and 1,272 of the chambers need the crossing redesigned rather than the "
         "chamber moved. Separately, 72 sit on the TRUNK, which is the client's own drawn "
         "alignment running about 500 m down a class-5/6 wadi - one decision for NWS, not "
         "seventy-two for us."),
        ("Extend the diameter series, once, with NWS confirmation.",
         "criteria.DN_SERIES stops at DN1200 and the trunk needs more. The sizes above it "
         "used here - 1400 / 1700 / 1800 / 2000 / 2400 - are the ones G203-p32 Table 13, "
         "p35 Table 15 and p30 Table 12 print, so this is a confirmation rather than a "
         "derivation. Change it in one place."),
        ("Do not oversize to lay flatter, whatever the depth savings look like.",
         "G203-p29 says sewers shall not be oversized to facilitate flatter slopes, and Ten "
         "States §33.43 says the same independently. This was tested as an optimisation in "
         "W10, it is the single largest lever available on depth and pumping, and it is "
         "prohibited. It will be proposed again by someone looking at the depth histogram; "
         "the answer is no."),
    ], start=1):
        D.numbered(d, txt, lead=lead, restart=(n == 1))

    D.h(d, 1, "Two things I would not do")
    D.bullet(d, "Station count is a poor objective. A STRICTER depth limit can produce "
                "FEWER stations, because the solver resets shallower and the next breach "
                "arrives later. Total lift is the honest measure, and it is what the "
                "life-cycle cost reads.",
             lead="Do not optimise for the number of pumping stations.")
    D.bullet(d, "Their gradients and depths match ours closely, and that agreement says "
                "the hydraulics are right and nothing at all about whether the layout is "
                "buildable. The hierarchy is invisible in gradient and depth statistics. "
                "Copy the as-built's shape and its packaging; do not copy its sizing - a "
                "significant fraction of its pipes cannot pass today's peak flow.",
             lead="Do not treat agreement with the as-built averages as validation.")


def part_d(d):
    D.part(d, "D", "What is needed from others")
    D.h(d, 1, "Data requests, in the order they unblock work")
    D.table(d, ["From", "What", "Blocks"], [
        ["NWS / MoAFWR", "50-year flood mapping covering the whole study area",
         "Every wadi decision on 51 % of the network"],
        ["NWS", "Design tractive stress τ, or confirmation of 1.0 Pa",
         "Gradients, depths and pumping across 97 % of the network"],
        ["NWS", "Existing works inlet invert level",
         "The trunk's outfall level and the deepest excavation in the scheme"],
        ["NWS", "Confirmation of DN1400-2400 in the pipe series",
         "Trunk sizing above DN1200"],
        ["NWS", "Decision on 236 plots whose only frontage is a dual carriageway",
         "Their connection, and whether they are served at all"],
        ["Draftsman", "Final treated road centrelines",
         "A re-run of the whole pipeline on final geometry"],
        ["GIS expert", "Clean land-use data",
         "Load placement, and Table 12 drivers"],
    ], widths=[3.0, 7.0, 6.0], font=8.5)
    D.p(d, "")
    D.p(d, "The first two are worth pressing hardest. They are single questions with short "
           "answers that change the design more than anything we can do ourselves.",
        bold=True)


def part_e(d):
    D.part(d, "E", "Next steps")
    D.h(d, 1, "In order")
    for n, t in enumerate([
        "Finish stage 5c and let the chain reach stages 6 to 9, so there is a levelled, "
        "sized network to audit rather than a graph.",
        "Run the auditor over W11a and publish the failing table. The philosophy is "
        "explicit that a failing table is the specification, not an embarrassment.",
        "Fix OPEN-S4-1 (the trunk / corridor node mismatch) before reading anything into "
        "the drainage-system count.",
        "Re-site the chambers on wadi ground, and apply the H1a classification inside "
        "stage 3 so the trunk's 10.98 km is separated into crossings and defects.",
        "Re-run everything when the draftsman's final lines and the clean land-use data "
        "arrive. The scripts are being purified so both drop straight in.",
        "Only then build the three concept options per system and take them through the "
        "seven-criteria appraisal, with BAT carried as two options rather than one answer.",
    ], start=1):
        D.numbered(d, t, restart=(n == 1))

    D.p(d, "")
    D.callout(
        d, "One thing to hold on to.",
        "Every defect in this report was found by making two things that should agree "
        "disagree in public - the auditor against the criteria, a stage against the "
        "auditor, the declared graph against the drawn one. None was found by reading the "
        "code carefully. That is the method worth keeping when the final data arrives and "
        "the pressure is to get a network out.",
        fill="EEF3FA", colour=D.MID)


def main():
    d = D.new_document()
    title_page(d)
    D.h(d, 1, "Contents")
    D.toc(d, "1-2")
    D.pagebreak(d)

    flows = "written this run - see W11a/run/s5c_reach_flows.csv"
    csv = os.path.join(W11A, "run", "s5c_reach_flows.csv")
    if os.path.exists(csv):
        import pandas as pd
        f = pd.read_csv(csv)
        flows = (f"{len(f):,} reaches carry an accumulated flow; peak "
                 f"{pd.to_numeric(f.QPK_LS, errors='coerce').max():,.0f} L/s")
    else:
        flows = "written by s5c_flows.py; re-run this build after it completes"

    summary(d)
    part_a(d)
    part_b(d, flows)
    part_c(d)
    part_d(d)
    part_e(d)
    D.footer_pagenum(d, f"2621 Ibri - W11a Design Review {REV} - internal")
    os.makedirs(HERE, exist_ok=True)
    d.save(OUT)
    print(f"written {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
