# Scripts: the reference implementation (Ibri W18)

Copied from the Ibri working folder `Hydraulic/Claude/W18 NWS scenarios 2056-2071/` on the day the skill was made. The
layout (`py/`, `gis/`, `report_final/`, `sewergems_api/`) is the same, so the imports resolve as they did there.

**Before reuse on another project:**
- the paths at the top of each script are Ibri's: move them into the project profile;
- the scenario, plant and year lists are Ibri's (SC1-SC4, STP-1/2/5, 2051/2056/2061);
- the cost rates in `final_boq.py` and `final_financial.py` are the Ibri team's;
- run the blind own-model test before trusting the design engine on a new network.

The source of record stays the project repo; this copy does not update itself.

| Stage | File | What it is (first line of its docstring) |
|---|---|---|
| 1 Loads | `py/nws_loads.py` | W18 plot loads on the NWS basis of November 2026. |
| 1 Loads | `py/audit_w18.py` | Independent audit of the W18 deliverables (engineer, 2026-11-17: "review all the excel and plot data"). Recomputes |
| 1 Loads | `py/plot_layer_2100.py` | W18 plot layer 2026-2100 (engineer, 2026-11-16): every plot with its electricity meters by category, land use, |
| 1 Loads | `py/map_not_carried.py` | W18: the plots whose flow does not enter the network, in the engineer's two categories (2026-11-16): |
| 1 Loads | `py/map_odd_plots.py` | W18 check maps: which future plots take growth, and why the others do not. The rule (engineer, 2026-11-17): a growth |
| 3 Own model = SewerGEMS | `py/own_design.py` | SC1 designed without SewerGEMS, to test whether the two give the same answer (engineer, 2026-11-18: "do you design |
| 3 Own model = SewerGEMS | `py/compare_own_sewergems.py` | SC1-2051 (engineer, 2026-11-18): my own design (py/own_design.py, run blind before SewerGEMS finished) against |
| 5 Design chain | `py/final_run_all.py` | W18 final design: the whole chain for the 12 cases (SC1-SC4 x 2051/2056/2061), repeated until the lift stations no |
| 5 Design chain | `py/final_design.py` | W18 final design (engineer, 2026-11-18): every scenario (SC1 STP 1 only, SC2 STP 16 only, SC3 STP 1 + STP 5, SC4 |
| 5 Design chain | `py/routing.py` | STP options S1-S7: where each subnetwork's outfall flow goes, and the transfers that follow from it. |
| 5 Design chain | `py/split_deep_subnetworks.py` | W18 (engineer, 2026-11-17): steepen the pipes above DN200 to reach 0.75 m/s at their 2031 peak flow, up to 1 %; where |
| 5 Design chain | `py/reduce_stations.py` | W18 (engineer, 2026-11-18): fewer pumping stations, by the logic the engineer applied himself at 0.50 % - O12 kept deep |
| 5 Design chain | `py/final_selfcleansing.py` | W18 final design (engineer, 2026-11-18): self-cleansing of every scenario and design year at 0.75 % - pipes above |
| 5 Design chain | `py/final_naming.py` | W18 final design (engineer, 2026-11-18): the final network of one case renamed into pumps and lifts. |
| 5 Design chain | `py/final_products.py` | W18 final design: the products of one case from its renamed network (py/final_naming.py) - the pumping stations and |
| 5 Design chain | `py/design_year_check.py` | Does a design carry the flow of its design life? Each scenario's 2051 and 2061 designs are run at the 2056 peak, by the design |
| 2, 6 SewerGEMS inputs and referee | `py/make_transfers.py` | Write the transfer rows of one option (all years) for the SewerGEMS job, and print the plant inflows. |
| 2, 6 SewerGEMS inputs and referee | `py/final_sg_inputs.py` | W18 final design: the inputs that turn the SewerGEMS model R4 into one case of the final design (job 079 onwards, |
| 2, 6 SewerGEMS inputs and referee | `py/final_sg_compare.py` | W18 final design: the SewerGEMS model of a case (build_final, jobs 080 on) against the own design, pipe by pipe, by |
| 7 Costs, TE, station flows | `py/final_boq.py` | W18 final design: the bill of quantities of the sewer network for the four scenarios and three design years, and the |
| 7 Costs, TE, station flows | `py/final_financial.py` | W18 final design: treatment capacity and phasing, treated effluent supply, and the CAPEX / OPEX of the four scenarios by |
| 7 Costs, TE, station flows | `py/te_sc4_network.py` | The treated effluent network of Scenario SC4 (STP-2 and STP-5), which the team's TE models do not have (R10, 2026-11-18): STP-5 |
| 7 Costs, TE, station flows | `py/final_station_flows.py` | W18 final design: the people and the average flow at every pumping station, lift station and plant, every five years |
| 8 Outputs | `py/final_dwg.py` | The design drawings of the four final scenarios as AutoCAD files (engineer, 2026-11-19: the client asks for DWG with |
| 8 Outputs | `py/diagram_png.py` | Draw the transfer diagrams of the STP options as PNG, locally, from results/diagrams.json: the same layout, the same |
| 8 Outputs | `py/diagram_layout.py` | Layout of the transfer diagram of every STP option, for Figma (drawn by explicit coordinates, no auto-layout). |
| 8 Outputs | `py/package_final.py` | W18 final design: one zip with everything the team receives (current names only): |
| 8 Outputs | `gis/final_maps.py` | W18 final design: the QGIS project of the four scenarios and three design years, and the report maps (2056, the base |
| 8 Outputs | `gis/make_w17_project.py` | Build the W17 QGIS project (network options S1-S7) from W17/Options 2026-10, with its print layouts cloned from |
| 8 Outputs | `report_final/flow_diagram.py` | Flow schematic of each final scenario in the form of the R7 transfer diagrams (engineer, 2026-11-19: "keep the same |
| 8 Outputs | `report_final/report_workbook.py` | The workbook that goes with the concept design report: the tables behind its charts and the people and flow at every |
| 8 Outputs | `report_final/facts_final.py` | Every figure the final-design report text uses, read once from the results (results/final_0.75pc_SC1-SC4/), so the |
| 9 Report tools | `report_final/word_finish.py` | Open the built report in a separate, hidden Word instance (never the user's own Word), update the caption numbers (not the team's |
| 9 Report tools | `report_final/qa_report.py` | Quality checks of a built report, run after word_finish.py and check_clean.py (R11-R12, 2026-11-19). Every check here found |
| 9 Report tools | `report_final/check_clean.py` | The clean-room gate for client reports: nothing internal reaches the reader, and a scan proves it, not a reading. |
| support | `gis/template_report_A3.qpt` | QGIS A3 layout template of every report map |
| support | `qgis/styles/manholes_depth.qml` | QML style: manholes by depth |
| support | `report_final/forbidden_terms.txt` | clean-gate forbidden regexes (Ibri's; replace per project) |
| support | `report_final/allowed_terms.txt` | clean-gate allowed regexes (Ibri's) |
| support | `sewergems_api/watcher.ps1` | VM bridge: runs the dropped jobs |
| support | `sewergems_api/compile_check.ps1` | VM bridge: compiles the C# helpers on the host, runs nothing |
| support | `sewergems_api/lib/CalcOpts.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Confirm.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Convert.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/DesignProbe.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/DesignProbe2.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/DesignTest.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/FinalBuild.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Flatten.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Friction.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Housekeeping.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Inventory.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/LoadsDiag.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/OneRow.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Peaking.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Probe.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/ProbeInflow.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/ResultFields.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Scenarios.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/SizeCheck.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/Transfer.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/YearLoads.cs` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/build_final.ps1` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/build_option.ps1` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/build_options.ps1` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/build_scenario.ps1` | VM bridge library: C# helper or build script |
| support | `sewergems_api/lib/load.ps1` | VM bridge library: C# helper or build script |
| support | `sewergems_api/jobs/071_w18_R3_years_capacity.ps1` | example job: set six year alternatives from manhole_loads.csv, check stored = file |
| support | `sewergems_api/jobs/072_w18_R4_years_2031_2091.ps1` | example job: add year alternatives by Copy(loaded id), 13 years |
| support | `sewergems_api/jobs/074_w18_R5_SC1_2056.ps1` | example job: a SewerGEMS design of one case (the calibration source for the own model) |
| support | `sewergems_api/jobs/078_w18_catalogue_and_alternatives.ps1` | example job: catalogue and alternatives set LOCAL |
| support | `sewergems_api/jobs/080_w18_final_SC1-2056.ps1` | example job: referee build of a final design (build_final.ps1) |
| support | `sewergems_api/jobs/086_w18_final_SC1-2051.ps1` | example job: referee build with the free-space check |
