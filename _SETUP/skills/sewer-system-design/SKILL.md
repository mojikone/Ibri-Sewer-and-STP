---
name: sewer-system-design
description: Design a wastewater (sewer) network under Oman's NWS guidelines (PAM-GUD-201/202/203) from population and plot loads to a SewerGEMS-checked design - loads on plots and manholes, design years and self-cleansing, pipe sizing and gradients, depth limits, lift and pumping stations, SewerGEMS driven through its API as the referee, treatment-plant and treated-effluent capacity, BOQ and CAPEX/OPEX, maps, DWG drawings, flow schematics and the delivery package. Use it whenever the work is sewer or wastewater network design or a sewer concept design, even when only one step is named - putting loads on plots, choosing a design year, why SewerGEMS sizes a pipe differently from your own calculation, how many lifts a gradient limit costs, station duty and head, STP modules, TE supply, sewer quantities and costs, sewer maps or drawings. Not for storm drainage or flood channels, and not for writing report prose (use report-writing for that).
---

# Sewer system design (NWS, PAM-GUD-201 / 202 / 203)

This is the method that produced the Ibri concept design (Renardet 2621, W18, November 2026): four plant scenarios × three
design years, 19,083 pipes each, every design rebuilt in SewerGEMS and matched pipe for pipe. It is written for any sewer
project under the NWS guidelines. Ibri is the worked example (`references/ibri_profile.md`), and `scripts/` holds the code
that ran it, as the reference implementation.

The one idea underneath everything: **SewerGEMS is the referee, and your own model must give its answer before you trust
it.** A design chain in Python runs in seconds where a SewerGEMS design takes about 44 minutes, so you iterate in your own
code, but only after a blind test has shown that the two agree on every pipe. Without that test, every later number is a
guess with decimals.

## Start: the project profile and the decisions

1. Copy `profile_template.md` into the project's working folder and fill it: the inputs, the plants and scenarios, the
   design years, and the decisions below. Everything project-specific lives there, not in your head or in the scripts.
2. Read the project's design-criteria register if it has one. Otherwise use `references/design_values.md`. **Every numeric
   value traces to a guideline page or to a recorded decision.** A value with no source cannot be defended at review, and
   it spreads silently into every pipe.
3. Ask the engineer for the decisions the guidelines leave open, **in one batch, each with a recommended default**
   (Ibri's choice is a reasonable default). Do not stop for each one separately:

| Decision | Ibri's answer (the default to offer) |
|---|---|
| Population basis per settlement | the team's mean of three series, capped at the settlement's capacity, no overflow |
| Per-capita rate, occupancy | 171.03 L/person/day, 4.8 people per property (the client's figures) |
| Where growth goes (growth plots) | future plots of 200–3,000 m², home-shaped, any zoning but agricultural, heritage and industrial |
| Plots the network does not carry | plots on the inactive network, or more than 200 m from an active sewer: reported, not modelled |
| Opening year and design years | opening 2031; design years 2051 / 2056 / 2061, with 2056 = opening + 25 adopted |
| Self-cleansing rule | pipes above DN200 at 0.75 m/s at the opening-year peak, rechecked five years later |
| Gradient limit for steepening | 0.75 %, chosen from a 0.50 / 0.75 / 1.00 % study |
| Depth caps | 12 m to an outfall; up to 14.65 m for an added station or outfall where that saves a station; 16.5 m for any manhole |
| Scenarios | the plant combinations to compare (Ibri: four, SC1–SC4) |

## The chain at a glance

| # | Stage | Output | Gate before the next stage | Read |
|---|---|---|---|---|
| 1 | Loads on plots, then manholes | `manhole_loads.csv` per year | an independent audit recomputes every total from the raw sources | `references/loads.md` |
| 2 | Loads into SewerGEMS | one year alternative per year | stored loads = file loads, every year | `references/sewergems_api.md` |
| 3 | Own model made to give SewerGEMS's answer | own design engine | blind test: the same size on every pipe, flows within 0.1 % | `references/network_design.md` §1 |
| 4 | Studies for the decisions | tables and maps for the engineer | the engineer decides the design years and the gradient limit | `references/network_design.md` §2 |
| 5 | The design chain, per case | named network, stations, products | no pipe over its d/D limit; repeat until no station changes | `references/network_design.md` §3 |
| 6 | SewerGEMS referee, per case | one model per case | pipe-by-pipe comparison passes | `references/sewergems_api.md` |
| 7 | Treatment, treated effluent, costs | `financial.json`, BOQ | totals tie back to the design flows | `references/costs_and_te.md` |
| 8 | Station flows, maps, schematics, DWG, workbook, package | the deliverables | every image opened and looked at; package counts checked | `references/outputs_and_delivery.md` |
| 9 | Report | Word and PDF | clean-room gate and QA pass | `references/report.md`, then the report-writing skill |

## The rules that matter most, and why

**Loads (stage 1).**
- **Volume:** each settlement's volume is its adopted population × the per-capita rate. It stops growing at its capacity:
  base population + growth plots × properties per plot × occupancy.
- **Placement:** existing plots keep the pattern of their metered flow; the growth is shared equally among the growth plots.
- **Special loads** such as industrial estates are added on their own plots, outside the per-capita volume.
- **Infiltration goes in once.** If the model adds 720 L/day per km on the conduits (G201 p72), keep it out of the plot
  loads; doing both double-counts it.
- **Flow the network does not carry stays visible.** It remains in the settlement totals, is reported with a map, and is
  left out of the plant inflow; it does not just disappear.

**Loads in SewerGEMS (stage 2).**
- **Use unit sanitary loads, not pattern loads.** The Extreme Flow Setup peaks unit loads and never peaks pattern loads,
  so a pattern-loaded model under-sizes every pipe without any error.
- Keep one sanitary load per manhole; merge LoadBuilder's duplicate rows.
- A pumped flow arriving from another system is an *additional* load, never peaked again.

**Own model = SewerGEMS (stage 3).** Read the rules off a SewerGEMS design of the same network, then prove them blind:
- flow = peak factor (the model's own Peltier/Merrimack table) × the upstream unit loads + infiltration on the upstream
  conduits + the transfers;
- size = the smallest catalogue size whose Colebrook-White capacity (ks 1.5 mm) at the d/D limit carries the flow **at the
  gradient of the pipe's current size**, repeated pass after pass from the modeller's sizes until nothing changes. Sizing
  each candidate at its own gradient gives a different answer (63 pipes one size smaller at Ibri);
- use the **full** catalogue. One missing size (DN1200) was the only difference in Ibri's blind test.

**Decisions from studies (stage 4).** Don't guess a gradient limit or a design year; run the study and show it.
- **Gradient limit:** each limit costs stations and lifts and buys self-cleansing length. At Ibri SC1-2056, 0.50 % left
  82.6 % of pipe above DN200 self-cleansing at the opening year, 0.75 % gave 93.9 % and 1.00 % gave 98.1 %.
- **Design year:** design for opening + 25, then design the years either side. The client may accept the year whose
  self-cleansing at the opening year is acceptable.

**The design chain (stage 5).** Size → steepen pipes above DN200 to 0.75 m/s at the opening-year peak (up to the limit, one
gradient per street run) → re-lay (crowns matched, 1.3 m minimum cover, G203 p33) → cut where a subnetwork stays deeper than
the depth limit for good (the last manhole within the limit becomes a station, lifting to the next manhole) → join by
gravity where an outfall is within one manhole spacing of its receiver (G203 Table 12) → remove stations where the caps
allow → self-cleansing check → names → stations sized. Repeat until the lift stations stop changing: each cut changes the
flows downstream.

**Referee (stage 6).** Rebuild each case in SewerGEMS with your sizes and inverts, run analysis only (the sizes *are* the
design), and compare every pipe. A design run inside SewerGEMS at this point would quietly re-size pipes, and the two would
no longer be the same network.

## Working habits that held

- **Show drawings early.** A light KMZ, DXF or map in front of the engineer finds by eye what the checks miss.
- **Check before claiming.** Search the built output before calling anything missing, and assert every claim in code:
  "SC3 is cheapest in every design year" becomes an `assert` on the cost table, not a sentence someone typed.
- **Work on copies.** Never overwrite the modeller's SewerGEMS file; each revision is a new file (R0, R1 ...).
- **Run long jobs detached.** Drop them, then watch their output folder with a stall monitor, rather than waiting inside
  one command.
- **One number, one source.** Report text, tables, maps and the workbook all read the same results files.

## Traps already paid for

The full list is in `references/traps.md`. These ten cost the most:

1. **Pattern loads are never peaked** by SewerGEMS's Extreme Flow Setup. Use unit loads.
2. **Inherited DESIGN calculation options re-size the pipes in every analysis year.** Set every scenario's alternatives and
   options LOCAL explicitly, and fail the job if an analysis changes a size.
3. **A new year alternative must be a Copy of a loaded one.** `Add(parent)` breaks the second year.
4. **The typed API's diameter is stale for catalogue pipes.** Read the size reference.
5. **A lift's flow is pumped flow.** It goes to the next manhole as a transfer of its peak; peaking it again undersized 99
   pipes.
6. **Gravity joins can't be built as new sewers through the 10.4 API** (it solves them at 0.305 m depth and 5–7 m/s).
   Carry each join as a transfer.
7. **A conduit's start and stop need not follow the flow.** Check both end nodes when reconnecting.
8. **Never write a PowerShell path through Python or a bash heredoc.** `\f` and `\b` become control characters. Write job
   files with a file-writing tool and grep for `\\VBOXSVR` before dropping them.
9. **The 12 m depth is a recommended maximum** (G203 p33, "approximately 10–12 m", with excavation cost as the real
   trigger). Treat it as a hard limit until a cost study licenses an exception; an "exit" around it once let 1,362
   chambers through to 19.98 m.
10. **A guideline "lateral" is the tertiary pipe** (G203 p17, p22: at most 45 m). The street pipe is a secondary main
    sewer, laid to Table 11; Table 5's 1 % applies to laterals and riders only.

## Scripts: the reference implementation

`scripts/` mirrors the Ibri working folder (`py/`, `gis/`, `report_final/`, `sewergems_api/`), so the imports resolve as
they did there. The paths at the top of each script are Ibri's. Move them into the project profile before reuse.
`scripts/README.md` maps every script to its stage.

| Stage | Scripts |
|---|---|
| 1 Loads | `py/nws_loads.py`, `py/audit_w18.py`, `py/plot_layer_2100.py`, `py/map_not_carried.py`, `py/map_odd_plots.py` |
| 3 Own model | `py/own_design.py`, `py/compare_own_sewergems.py` |
| 5 Design chain | `py/final_run_all.py` runs `final_design.py`, `split_deep_subnetworks.py`, `final_selfcleansing.py`, `final_naming.py`, `final_products.py`; `reduce_stations.py`, `design_year_check.py`, `routing.py` |
| 2, 6 SewerGEMS | `sewergems_api/` (the VM bridge, C# helpers, example jobs), `py/make_transfers.py`, `py/final_sg_inputs.py`, `py/final_sg_compare.py` |
| 7 Costs | `py/final_boq.py`, `py/final_financial.py`, `py/te_sc4_network.py` |
| 8 Outputs | `py/final_station_flows.py`, `gis/final_maps.py` + `gis/make_w17_project.py` + `gis/template_report_A3.qpt`, `report_final/flow_diagram.py` + `py/diagram_png.py`, `py/final_dwg.py`, `report_final/report_workbook.py`, `py/package_final.py` |
| 9 Report tools | `report_final/word_finish.py`, `report_final/qa_report.py`, `report_final/check_clean.py` |
