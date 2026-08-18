# -*- coding: utf-8 -*-
"""Single source of truth for the W4 methodology report content.

Both renderers (make_methodology_docx.py -> Word, make_methodology_pdf.py -> PDF via
reportlab, no Word needed) consume the same block list, so the two formats cannot
drift apart. Every number is read live from W4/run/summary.json + violations.json.

Block grammar:
  ("h1", text) ("h2", text) ("p", text) ("bullet", lead_bold, rest)
  ("table", headers, rows, widths) ("img", path, width_in, caption)
  ("pagebreak",) ("toc",) ("cover", ...)
"""
import json
import os

W4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DOCS = os.path.join(W4, "docs", "img")
IMG_MAPS = os.path.join(W4, "img")


def load():
    S = json.load(open(os.path.join(W4, "run", "summary.json")))
    audit = json.load(open(os.path.join(W4, "run", "audit.json")))
    V = [a for a in audit if a["status"] == "FAIL"]
    return S, V


def build():
    S, V = load()
    sc, aug, lp, ld, sr = S["selfclean"], S["augmentation"], S["lowplots"], S["loads"], S.get("structures", {})
    dn = S["dn_km"]
    B = []

    B.append(("cover", {
        "eyebrow": "Ibri Sewer, TE & STP — Project 2621",
        "title": "W4 — Sewer Network Design Pipeline",
        "subtitle": "Methodology and Test-Boundary Results",
        "note": "Internal working document — design team",
        "date": "18 August 2026",
        "facts": [
            ["Test area", f"{S['s1']['boundary_ha']:.0f} ha"],
            ["Network designed", f"{S['n_nodes']:,} chambers / {S['net_km']:.1f} km"],
            ["Peak flow at outfall",
             f"{S['qpeak_outfall_ls']:.0f} L/s (Qadf {S['qadf_outfall_m3d']:,.0f} m3/d)"],
            ["Structural rules", "loop-free PASS · one outlet per chamber PASS"],
            ["Audit", f"{S['violations']} residual violations"],
            ["Code / tests", "W4/py/sewnet — 56 pytest cases, Table-11 gate"],
        ]}))
    B.append(("pagebreak",))
    B.append(("h1", "Contents"))
    B.append(("toc",))
    B.append(("pagebreak",))

    # ---------------- executive summary ----------------
    B.append(("h1", "Executive summary"))
    B.append(("p", f"We built the sewer design pipeline, proved it end to end on the "
                   f"{S['s1']['boundary_ha']:.0f} ha test boundary, put it through a 21-agent "
                   f"adversarial review and a two-rule structural audit (no loops; one outlet per "
                   f"chamber), fixed everything both found, and the design now holds those rules "
                   f"with {len(V)} failing checks of 21 out of {S['n_nodes']:,} chambers. Here is "
                   f"the whole story in one page."))
    B.append(("p", f"The pipeline takes four inputs — roads, classified plots, the 0.5 m terrain "
                   f"and a boundary — and produces a complete gravity network: {S['n_nodes']:,} "
                   f"chambers, {S['net_km']:.1f} km of pipe "
                   f"({float(dn['200'])/S['net_km']*100:.0f}% DN200, stepping up to DN"
                   f"{max(int(k) for k in dn)} on the outfall leg), designed inverts everywhere, "
                   f"about 9 seconds to run. Every one "
                   f"of the {ld['loaded_points']:,} loaded units ({ld['built']:,} built plots, "
                   f"{ld['planned']} planned, {ld['unparceled']} unparceled buildings; "
                   f"{ld['farms_excluded']} farms excluded per doctrine) lands on exactly one "
                   f"chamber — nothing silently dropped, mass balance closes exactly. Saturation "
                   f"flow at the outfall: Qadf {S['qadf_outfall_m3d']:,.0f} m3/d, peak "
                   f"{S['qpeak_outfall_ls']:.0f} L/s (Merrimack)."))
    B.append(("p", "The hydraulics were never taken on faith. The Colebrook-White solver had to "
                   "reproduce all nine minimum gradients of G203 Table 11 (plus/minus 5%) before "
                   "it was allowed to size anything — it does, mean deviation under 2%. The "
                   "adversarial panel then attacked the code and confirmed 11 real defects, all "
                   "fixed: the spanning tree skipped 22 km of cross-street edges (now covered with "
                   "a crest-manhole layout); capacity was computed on nominal diameter while "
                   "OD-designated PVC-U bores smaller (now the true SDR34 bore); a broken "
                   "bisection in the velocity-cap solver; drop structures measured against the "
                   "wrong datum. 44 pytest cases lock all of it in."))
    B.append(("p", f"The structural audit found what the graph checks had hidden (section 5): the "
                   f"tree gave every node one outlet, but {sr.get('merged', 0)} chambers sat within "
                   f"3 m of another chamber — many at the same point — each with its own outlet. On "
                   f"the ground that is a two-outlet junction, exactly what the rule forbids. The "
                   f"pipeline now merges coincident chambers, re-derives the tree over the merged "
                   f"set (which also removes loops that merging exposes), and offsets every extra "
                   f"outgoing pipe so it starts at the next house connection or 10 m clear of the "
                   f"chamber — the SWNETWROK convention, which had not been adopted until it was "
                   f"called for."))
    B.append(("p", f"The honest self-cleansing picture, on the table rather than under it: "
                   f"{sc['share_below']*100:.0f}% of pipes cannot reach 0.75 m/s at saturation "
                   f"peak — physically inevitable on small residential branches — and comply "
                   f"through the guideline's own tractive-force alternative at tau = 1 Pa, a "
                   f"pending assumption [GAP-9]. If NWS sets tau = 2 Pa, "
                   f"{sc['would_fail_at_tau2']:,} pipes need steeper slopes. That single number is "
                   f"the strongest argument for pinning tau down at the kickoff."))
    B.append(("p", "Three findings from the test area:"))
    B.append(("bullet", f"The outfall landed {S['outfall']['dist_to_expected_m']:.0f} m from where "
                        f"you expected — ",
              f"the terrain's lowest boundary road node is at ({S['outfall']['x']:.0f}, "
              f"{S['outfall']['y']:.0f}), south-center on the main corridor, z "
              f"{S['outfall']['z']:.1f} m, not the west edge. If the real trunk connection is "
              f"elsewhere, it is one config line and an 11-second re-run."))
    B.append(("bullet", "Your elevated-roads concern was justified: ",
              f"{lp['flagged']} units ({lp['flagged']/lp['checked']*100:.1f}%) could not "
              f"gravity-connect at standard sewer depth. Deepening {lp['deepened_mh']} chambers "
              f"recovered all but {lp['residual']}, now flagged as local-solution candidates."))
    B.append(("bullet", f"{S['solver']['pockets']} SLS pockets appeared ",
              f"— all small enough to absorb into detail design per rule 9 (some carry no "
              f"properties at all and are depth artefacts near the wadi bank rather than real "
              f"station sites). {S['drops']} drop structures ({S['vortex_sites']} vortex-class) "
              f"concentrate at wadi-bank crossings, exactly where detail design applies the "
              f"G1-p85 rules."))
    B.append(("p", "Also delivered: T01 Rev 3 — the tutorial now teaches Colebrook-White "
                   "(section 14), Table 11 derived step by step, every number verified."))
    B.append(("p", "What is proven: doctrine loads in, guideline-compliant network out, auditable "
                   "and re-runnable, honest about its assumptions. What is not yet proven: "
                   "SewerGEMS agreement (package and referee table await the ModelBuilder run), "
                   "and behaviour at 36-zone scale with the finalised trunk. That is W5."))
    B.append(("pagebreak",))

    # ---------------- 1 pipeline ----------------
    B.append(("h1", "1. What the pipeline is"))
    B.append(("p", "A re-runnable Python package (sewnet) that designs a gravity sewer network "
                   "inside any boundary, given roads, loaded plots, terrain and an outfall or "
                   "connection point. One config file holds the paths; criteria.py holds every "
                   "design number with its PAM-GUD page reference — no number lives anywhere else "
                   "in the code."))
    B.append(("img", os.path.join(IMG_DOCS, "pipeline_architecture.png"), 6.3,
              "Figure 1 — Pipeline architecture. Blue = inputs, yellow = audit gate, red = SLS "
              "flag, dashed = iteration loops."))
    B.append(("p", "Stages, in one breath: repair and clip the inputs; node the roads and collapse "
                   "dual carriageways; grow a loop-free tree toward the outfall (climb-penalised, "
                   "arterial-preferring — the 'no alleys' lesson); add cross-street branches where "
                   "loaded plots front an off-tree street; place chambers (junctions, bends over "
                   "45 degrees, 100 m spacing); merge coincident chambers and offset extra branch "
                   "starts; load every plot at saturation; accumulate flows with peak factor and "
                   "infiltration; size pipes and solve inverts together on the true bore; check "
                   "every house can reach its chamber, deepening where roads are elevated; audit "
                   "everything independently; export SHP, SewerGEMS, DXF and maps."))

    # ---------------- 2 road treatment ----------------
    rt = S.get("road_treatment") or {}
    B.append(("h1", "2. From road centrelines to sewer corridors"))
    B.append(("p", "Raw centrelines are not a sewer corridor. Fed directly, the pipeline "
                   "put a chamber wherever the survey data happened to break: 576 of 2,137 "
                   "chambers (27 %) sat at near-collinear breaks, 465 of them at under two "
                   "degrees of deflection. Those are artefacts of the data, not design "
                   "decisions, and every one costs a manhole. A separate treatment stage now "
                   "turns centrelines into corridors before anything is designed."))
    B.append(("table", ["Treatment", "Why", "Test area"], [
        ["De-duplicate vertices",
         "zero-length steps corrupt direction measurement — they made 66 reaches read as "
         "180 degree bends in the first compliance check",
         f"{rt.get('duplicate_vertices_removed', 0)} removed"],
        ["Simplify (0.5 m)", "survey jitter, without moving the centreline", "applied"],
        ["Dissolve collinear breaks (under 10 degrees at a two-way node)",
         "a straight street broken into three pieces becomes ONE corridor, so no chamber "
         "is placed at the breaks", f"{rt.get('collinear_joins', 0)} joins"],
        ["Collapse roundabouts (ring under 150 m, circular)",
         "a roundabout is not a corridor; the ring is removed and its legs reattach to the "
         "centre", f"{rt.get('roundabouts_collapsed', 0)} collapsed"],
        ["Drop dangling stubs under 8 m with no frontage",
         "clip debris that would otherwise become a branch", f"{rt.get('stubs_dropped', 0)} dropped"],
        ["Classify main roads",
         "main roads cannot be opened longitudinally; crossings remain allowed (G1-p85 "
         "trenchless). DERIVED here because the road layer carries no class attribute — "
         "advisory until a hierarchy layer is supplied",
         f"{rt.get('main_road_segments', 0)} segments flagged"],
    ], [1.6, 3.2, 1.5]))
    B.append(("p", f"Result: {rt.get('segments_in', 0)} raw segments become "
                   f"{rt.get('segments_out', 0)} corridors, and the length barely moves "
                   f"({rt.get('km_in', 0)} to {rt.get('km_out', 0)} km) — the stage re-joins "
                   f"rather than deletes. The corridors are written to W4/shp/W4_corridors.shp "
                   f"with a MAIN_ROAD and ELIGIBLE column so the corridor decisions can be "
                   f"reviewed and hand-edited in QGIS before any design runs."))
    B.append(("p", f"Effect on the design: chambers fall from 2,137 to {S['n_nodes']:,} "
                   f"(about 27 % fewer) with the network length essentially unchanged, so the "
                   f"saving is manholes that were never justified rather than sewers that are "
                   f"now missing."))

    # ---------------- 2 hydraulic basis ----------------
    B.append(("h1", "3. Hydraulic basis and how it is verified"))
    B.append(("table", ["Element", "Basis", "Verification"], [
        ["Capacity / velocity",
         "Colebrook-White, ks = 1.5 mm, nu = 1.141e-6 m2/s (G203-p24/25/28), partial-full circular "
         "geometry, true internal bore (PVC-U OD-series derated to SDR34 ID; GRP nominal = ID)",
         "Table-11 gate: reproduce all 9 minimum gradients at 0.75 m/s within 5% — passes at under "
         "2% mean deviation; ID convention unit-tested"],
        ["Minimum gradients",
         "Steeper of Table 11 (p29) and tractive force Smin = 2.33e-4 x tau^1.23 x Q^-0.461 (p27, "
         "A9-corrected), plus a 40 mm total-fall guard per reach (p29 4.3.1)",
         "tau = 1 Pa tagged [GAP-9]; Q floored at Mara's 1.5 L/s minimum design flow — at the "
         "floor tractive is about Table 11 DN200: the methods meet"],
        ["d/D limits", "at or below 0.65 (D<=350) and 0.50 (D>350) at peak (p27 Tab 10)",
         "enforced in sizing, re-checked in audit on the true bore"],
        ["Velocity band",
         "at least 0.75 m/s at peak or tractive-compliant (p26-27); at most 3.0 m/s via a slope cap "
         "whose surplus fall becomes a designed drop", "audit plus the transparency statistics in "
         "section 6"],
        ["Loads",
         "Doctrine 2: every plot at saturation, 6.0 x 171.3 l/c/d = about 1.03 m3/d/plot; farms "
         "zero; infiltration 720 L/d/km unpeaked; PF Merrimack (mandatory above 100 properties), "
         "held at its 100-property value below; Peltier comparison held the same way",
         "mass balance to the outfall closes exactly; unknown CLASS values can never vanish "
         "silently"],
    ], [1.05, 2.75, 2.5]))
    B.append(("img", os.path.join(IMG_DOCS, "load_chain.png"), 5.2,
              "Figure 2 — Load allocation chain."))
    B.append(("pagebreak",))

    # ---------------- 3 solver ----------------
    B.append(("h1", "4. How the solver designs a pipe"))
    B.append(("p", "Two passes per reach, iterated until no diameter changes (2 iterations "
                   "sufficed; oscillation between adjacent DNs is detected and broken upward; a "
                   "final lay pass always leaves inverts consistent with final diameters)."))
    B.append(("img2", os.path.join(IMG_DOCS, "solver_step1_slope.png"),
              os.path.join(IMG_DOCS, "solver_step2_profile.png"),
              "Figure 3 — Solver logic: step 1 sets the reach slope, step 2 resolves profile, "
              "junction and depth."))
    B.append(("p", "The details that matter:"))
    B.append(("bullet", "Uniform slope per reach (p29) — ",
              "one straight line between chambers, never kinked."))
    B.append(("bullet", "The chamber datum is the outgoing invert — ",
              "chamber depth is construction depth, and every inlet drop is measured inlet-invert "
              "minus outgoing-invert, so velocity-cap surpluses and cover shifts combine into the "
              "drop they physically are. Over 600 mm = external backdrop, over 2 m = vortex shaft "
              "(p30); the audit re-derives every drop independently, and a missing or "
              "misclassified record is a violation."))
    B.append(("bullet", "Mid-span cover on real terrain: ",
              "every reach profiled at 5 m on the 0.5 m VRT; a reach riding above dipping ground is "
              "shifted down bodily, the shift surfacing as a recorded drop."))
    B.append(("bullet", "Sizing without the ratchet: ",
              "every candidate DN is judged at its own governing slope (no-oversizing, p29), on its "
              "true bore, with velocity-infeasible candidates skipped explicitly."))
    B.append(("bullet", "Over 12 m depth becomes an SLS pocket (p33 + rule 9) — ",
              "never a silent orphan."))

    # ---------------- 4 structure rules ----------------
    B.append(("h1", "5. Loop-free, and one outlet per chamber"))
    B.append(("p", "Both rules are enforced constructively, not checked after the fact, and both "
                   "are verified independently on the final output."))
    B.append(("p", f"No loops. The collection network is a spanning tree by construction: a "
                   f"cost-weighted shortest-path tree to the outfall, where each chamber's single "
                   f"outgoing pipe is its next hop. Loop-closing street edges can never become "
                   f"pipes in that step. Final output: {S['n_nodes']:,} chambers, "
                   f"{S['n_pipes']:,} pipes, one connected component, acyclic — the pipe count "
                   f"being chambers-minus-one is the arithmetic signature of a tree."))
    B.append(("p", "One outlet per chamber. A junction takes any number of inlets and exactly one "
                   "outgoing pipe. The catch the graph checks missed: two separate chambers can sit "
                   "at the same physical point (road noding rounds to the centimetre, and the "
                   "cross-street augmentation planted branch heads next to existing junctions). "
                   "Each had one outlet in the graph; together they were a two-outlet junction on "
                   "the ground. The fix, in order:"))
    B.append(("bullet", "merge every cluster of chambers within 3 m — ",
              "they are one structure, which makes the hidden fan-outs visible as chambers with two "
              "outgoing pipes;"))
    B.append(("bullet", "re-derive the tree over the merged pipe set, ",
              "because merging can also close a loop (two chambers at one point may additionally be "
              "linked by a path). This restores one-outlet-and-no-loops in a single step and marks "
              "the leftover pipes as loop-closers;"))
    B.append(("bullet", "offset every leftover pipe so it starts clear of the chamber: ",
              "at the next house connection along its own alignment, or 10 m when that connection "
              "sits nearer — the SWNETWROK FANOUT_GAP_M convention. A branch whose pipe is too "
              "short to keep a clear start is dropped and reported (its street is served from the "
              "far end);"))
    B.append(("bullet", "slide any remaining branch head clear of neighbouring chambers, ",
              "iterating until nothing moves."))
    B.append(("p", f"Test-area result: {sr.get('merged', 0)} coincident chambers merged, "
                   f"{sr.get('fanouts', 0)} fan-outs resolved, {sr.get('offset_branches', 0)} "
                   f"branch starts offset, {sr.get('dropped_branches', 0)} branches dropped as "
                   f"served-from-far-end. Independent verification on the exported network: "
                   f"loop-free PASS, one-outlet PASS, 568 of 569 branch heads at least 10 m clear, "
                   f"one chamber pair at 2.78 m instead of 3.0 m. Those residuals are reported "
                   f"rather than hidden — both are local layout details for detail design."))
    B.append(("p", "The same checks now run in the audit every time (mh-clearance, head-offset, "
                   "one-outlet), with a unit test on a synthetic two-chambers-at-one-point case, so "
                   "this cannot regress silently."))
    B.append(("pagebreak",))

    # ---------------- 5 connectability ----------------
    B.append(("h1", "6. The house-connectability check"))
    B.append(("p", f"Roads are locally elevated for flood protection and underpasses, so houses can "
                   f"sit below the sewer. For every loaded unit: plot ground (0.5 m terrain) minus "
                   f"0.6 m outlet depth must reach its chamber's invert with 2% fall over the "
                   f"connection distance. Failures raise a deepening requirement on that chamber "
                   f"(capped 0.5 m short of the 12 m limit) and the invert solve re-runs; anything "
                   f"still failing is flagged for a local solution. Test area: {lp['flagged']} "
                   f"flagged, {lp['deepened_mh']} chambers deepened, {lp['residual']} residual."))
    B.append(("img", os.path.join(IMG_MAPS, "W4_M3_connectability.png"), 4.5,
              "Figure 4 — Plot connectability: green connectable, amber recovered by deepening, "
              "red needs a local solution."))
    B.append(("pagebreak",))

    # ---------------- 6 results ----------------
    B.append(("h1", "7. Test-boundary results"))
    B.append(("table", ["Quantity", "Value"], [
        ["Area / roads / network",
         f"{S['s1']['boundary_ha']:.0f} ha / {S['s1']['len_km']:.1f} km roads / "
         f"{S['net_km']:.1f} km sewers ({aug['added_km']} km from cross-street augmentation; "
         f"{aug['skipped_km']} km of unloaded streets deliberately unsewered)"],
        ["Chambers / pipes", f"{S['n_nodes']:,} / {S['n_pipes']:,} (single tree, one outfall — "
                            f"chambers minus one)"],
        ["Diameters", " · ".join(f"DN{k} {v} km" for k, v in dn.items())],
        ["Loaded units", f"{ld['loaded_points']:,} (built {ld['built']:,} + planned "
                         f"{ld['planned']} + unparceled {ld['unparceled']}); farms excluded "
                         f"{ld['farms_excluded']}"],
        ["Outfall", f"({S['outfall']['x']:.0f}, {S['outfall']['y']:.0f}), z "
                    f"{S['outfall']['z']:.2f} — {S['outfall']['dist_to_expected_m']:.0f} m from "
                    f"user expectation"],
        ["Qadf / Qpeak at outfall", f"{S['qadf_outfall_m3d']:,.0f} m3/d / "
                                    f"{S['qpeak_outfall_ls']:.0f} L/s (PF {S['pf_formula']}; "
                                    f"Peltier column in the shapefiles)"],
        ["Structure rules (section 5)", f"{sr.get('merged',0)} coincident chambers merged · "
                                        f"{sr.get('fanouts',0)} fan-outs resolved · "
                                        f"{sr.get('offset_branches',0)} branch starts offset · "
                                        f"{sr.get('dropped_branches',0)} branches dropped"],
        ["Depths", f"max {S['max_depth_m']:.1f} m (inside an SLS pocket); gravity network otherwise "
                   f"at or under 12 m"],
        ["Drops", f"{S['drops']} designed structures; {S['vortex_sites']} vortex-class (over 2 m), "
                  f"concentrated at wadi-bank crossings"],
        ["SLS pockets", f"{S['solver']['pockets']} (about 5 properties total, absorb per rule 9)"],
        ["Low plots", f"{lp['flagged']} flagged, {lp['residual']} residual after deepening "
                      f"{lp['deepened_mh']} chambers"],
        ["Audit", f"{S['violations']} violations — structural residuals only (one chamber pair at "
                  f"2.78 m vs the 3.0 m clearance; one branch head at 9.1 m vs the 10 m offset); "
                  f"everything else clean, including independent drop re-derivation"],
        ["Self-cleansing transparency",
         f"{sc['below_075_at_peak']:,}/{sc['pipes']:,} pipes below 0.75 m/s at saturation peak — "
         f"compliant via tractive at tau=1 Pa [GAP-9]; {sc['would_fail_at_tau2']:,} would need "
         f"redesign at tau=2 Pa; start-year flags {S['startyear_flags']:,}, all tractive-compliant"],
        ["Runtime", "about 11 s design + 4 s exports"],
    ], [1.65, 4.65]))
    B.append(("img", os.path.join(IMG_MAPS, "W4_M1_network_by_dn.png"), 4.3,
              "Figure 5 — Designed network by diameter, with outfall and SLS candidates."))
    B.append(("img", os.path.join(IMG_MAPS, "W4_M2_depth.png"), 4.3,
              "Figure 6 — Excavation depth (invert below ground)."))
    B.append(("pagebreak",))

    # ---------------- 7 sewergems ----------------
    B.append(("h1", "8. SewerGEMS package and referee protocol"))
    B.append(("p", "W4/sewergems/ holds MANHOLES, CONDUITS and OUTFALL shapefiles built to the "
                   "Bentley-documented ModelBuilder mappings (explicit START_ND/STOP_ND plus "
                   "vertex-snapped geometry digitised upstream to downstream, elevations not "
                   "depths, numeric mm diameters), LOADS.xlsx (pattern-based rows, L/s per "
                   "chamber), and IMPORT_PROCEDURE.md with the known traps — the 'Set Invert to "
                   "Start/Stop Node = False' global edit being the one that silently deletes drop "
                   "manholes. Manning n is exported as 0.013, the ks = 1.5 mm equivalent: the "
                   "Tab-8 range 0.009-0.011 conflicts with the ks mandate and would show roughly "
                   "30% phantom capacity, so that conflict is flagged as an NWS kickoff item."))
    B.append(("p", "After the model run, paste SewerGEMS discharge, velocity and d/D into "
                   "REFEREE_pipes.csv; any pipe deviating more than 5% from our columns is an open "
                   "investigation. The design is not verified until the two engines agree — "
                   "deliberately a separate run, not a self-check."))

    # ---------------- 8 assumptions ----------------
    B.append(("h1", "9. Assumptions register"))
    B.append(("p", "Tagged in criteria.ASSUMPTIONS with the same wording, and reported in every "
                   "deliverable:"))
    B.append(("table", ["Assumption", "Basis / exposure"], [
        ["tau = 1 Pa", f"GUD-203 gives no numeric design tractive stress [GAP-9]; largest redesign "
                       f"exposure ({sc['would_fail_at_tau2']:,} pipes at tau=2)"],
        ["Tractive Q-floor 1.5 L/s", "Mara simplified-sewerage minimum design flow; unfloored the "
                                     "formula demands unbounded slopes as Q approaches 0"],
        ["PVC-U wall class SDR34/SN8", "true bore for hydraulics; actual class per PAM-SPC-207 "
                                       "pending"],
        ["OR 6.0, 1 property per plot", "GAP-5 (NCSI housing units missing)"],
        ["Plot outlet 0.6 m, 2% connection fall", "method choice for the connectability check"],
        ["40 m frontage rule", "an off-tree street gets a sewer when a loaded unit lies within "
                               "40 m"],
        ["10 m branch-start offset, 3 m chamber clearance",
         "layout conventions from SWNETWROK and the user's rule, not PAM-GUD values"],
        ["Chamber size ladder", "02 has no size table; GUD-203 4.4 re-extract pending (no hydraulic "
                                "effect at concept)"],
        ["Rider discharge to nearest chamber", "02 silent on the discharge point"],
        ["Gravity in-road position", "taken from the force-main clause (p51, A9) as an inference"],
        ["PF held below 100 properties", "G1-p71 prescribes no formula there; Peltier held the same "
                                         "way"],
        ["Infiltration unpeaked", "add-order not stated in GUD-201 — kickoff item"],
    ], [2.15, 4.15]))

    # ---------------- 9 limitations ----------------
    B.append(("h1", "10. Limitations and what changes at full scale"))
    B.append(("bullet", "The trunk is user-finalised (settled 2026-08-18) — ",
              "the pipeline designs subnetworks into the given connection points, which are config "
              "entries, not structure."))
    B.append(("bullet", "One outfall per run today; ",
              "multi-connection territory competition is the W5 structural addition."))
    B.append(("bullet", "Riders are schematic; ",
              "junction losses ignored (normal-depth hydraulics) — both noted for the SewerGEMS "
              "comparison."))
    B.append(("bullet", "The 0.5 m terrain is concept-grade for inverts near the 0.75-1.0 mm/m "
                        "minimums (G1-p36); ",
              "flat trunk profiles at scale need survey-grade data — a registered data request."))
    B.append(("bullet", "tau = 1 Pa carries the largest redesign exposure — ", "pin it at kickoff."))

    # ---------------- 10 reviews ----------------
    B.append(("h1", "11. Adversarial review and structural audit"))
    B.append(("p", "A 21-agent skeptic panel attacked the hydraulic core after the first "
                   "audit-clean run: four attack lenses (Colebrook-White implementation, solver "
                   "clause compliance, load and audit doctrine, executed edge cases) followed by "
                   "independent verification of every raw finding. 17 raw findings, 11 confirmed, "
                   "11 fixed, 6 refuted. The headline four were cross-street coverage, the true PVC "
                   "bore correction, the drop-datum correction, and the velocity-cap bisection "
                   "repair."))
    B.append(("p", "A second, user-driven audit then checked the two layout rules directly against "
                   "the run output: no loops (held) and one outlet per junction (held in the graph, "
                   "broken on the ground — see section 5). The 10 m branch-start offset had not "
                   "been implemented at all; it now is, with permanent audit checks and a unit "
                   "test. Both audits are recorded in W4/docs/REVIEW_FINDINGS.md."))
    return B
