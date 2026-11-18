# W18 — the NWS scenarios 2056–2071 (opened 2026-11-16)

**A copy of W17's scripts, data, docs and results.** W17's report builds, deck and deliverable folder stay in W17 as the record: the report is now the team's `Ibri_Concept_Design_Report_R8-MH.docx`, edited in Word.

## The basis (team, 8 November 2026, after the NWS meeting of 2 November; engineer's rulings 16 November)

| Item | Value |
|---|---|
| Population | the team's settlement series: mean of NCSI, domestic meters x 4.8 and the APSR master plan (`temp/recent updates by the team/New Calculation MH.xlsx`, sheet `Average`; server `06-WORKING/04-Hydraulic/7- Demand`) |
| Cap | each settlement grows until its empty plots are full, no overflow; capacity = 2026 population + growth plots × the team's properties per plot × 4.8 (sheet `MOHUP DATA - NA`, column D; engineer 2026-11-17, in place of the team's column G, which counted the existing properties at 4.8 people); Bat (2057), Ibri (2063, 144,537 people), Hijar (2067) and Al Araqi (2071) fill by 2071 |
| Rate | 171.03 L/person/day (sheet `Base Demand` H4); infiltration 720 L/day/km added by the model |
| Plots | the model's plot layer (`14 IBRI_W17/SHP/Plots/Plots.shp`, row for row the W14 plots); the new MoHUP plots were too messy to use |
| Placement | the 2026 flow on the existing plots in their 2024 pattern, fixed every year; growth above 2026 shared equally by the settlement's growth plots |
| Design years | 2056, 2061, 2066, 2071: design for 2056 and check it at 2031 (every pipe above DN200 at 0.75 m/s); if it passes, move on to the next year; if 2056 fails, step back to 2051. Tolerance not settled |
| Gradients | Table 11, no tractive force |
| Scenarios | SC1 STP-1 (O1) = S1 · SC2 STP-2 (O16) = S2 · SC3 STP-1 + STP-5 (O4) = S3 · **SC4 STP-2 + STP-5, new** |

## Loads (`py/nws_loads.py` -> `results/loads/`)

`plot_loads.csv` (per plot, every five years 2026–2071), `manhole_loads.csv` (per manhole id), `settlement_flows.csv`, `check.md`. Plot flow before infiltration: 2031 23,084 · 2056 39,020 · 2061 43,197 · 2066 46,075 · 2071 48,224 m³/d. Against the team's scenario sheet less its 1,099 m³/d of infiltration it is 316 m³/d higher in 2031 and 2056 (the two estates, which the team's sheet does not carry); 2061, 2066 and 2071 are 234 higher, 1,616 and 4,715 lower, because settlements stop at their capacity (Bat from 2057, Ibri 2063, Hijar 2067, Al Araqi 2071).

## Plot layer 2026–2100 (`py/plot_layer_2100.py` -> `gis/W18_plots_2026_2100.zip`)

Each of the 77,265 plots carries:
- its meters by category (domestic, commercial, government, special, farm);
- its land use (and MoH's planned use) and its status, Existing or Future;
- its properties: existing properties (the 2024 domestic meters) and the properties added by 2100 at the team's 4.8 persons each;
- its residents and average flow (m³/d, unpeaked, no infiltration) for every year from 2026 to 2100;
- its handling: inside its boundary, growth plot, network status (connected / inactive manhole / over 200 m) and the manhole it loads.

The fields are listed in `gis/W18_plots_2026_2100_fields.md`, and the checks are in `results/loads/plot_layer_check.md`:
- **Model years:** the flows of the ten model years match `plot_loads.csv` to 5e-7 m³/d.
- **Totals:** residents and flow sum to the settlements every year. The file keeps 5 decimals, because every growth plot in a settlement carries the same share and rounding errors pile up instead of cancelling (2 decimals were 100 people out). The file is within 0.1 person and 0.13 m³/d of the totals.
- **Residents are not flow ÷ 171:** on an existing plot the flow also carries shops, offices and estate workers, who are not residents.
- **Size:** the raw shapefile (a 145 MB .dbf) is over GitHub's limit, so the repo holds the 9 MB zip. Rebuild with `python py/plot_layer_2100.py`.

The results:
- **Totals in 2100:** 322,220 residents and 55,425 m³/d, of which 53,478 m³/d is carried.
- **Full years:** 12 settlements fill by 2100 (Bat 2057, Ibri 2063, Hijar 2067, Al Araqi 2071, Ad Dariz 2072, Ash Shiab 2075, Al Aynayn 2076, Satwah 2079, Al Wahrah 2086, Usaybuq 2095, Al Akheedar 2096, Suwayda al Ma 2100); on the team's capacity 8 did, all later. The other 13 do not fill by 2100.
- **Properties per growth plot:** a full settlement puts exactly the team's properties per plot on each growth plot (Ibri 1.48, Al Akheedar 3.10, Ash Shiab 1.09), because the capacity is built from the growth plots themselves. (On the team's capacity, which counts their 13,120 future residential plots in Ibri against our 11,053, it was 1.51 in Ibri, 3.46 in Al Akheedar and 2.31 in Ash Shiab.)
- Check maps of plot flow, five settlements (2056): `img/plotflow_2056_*.png`, with A3 detail sheets at 1:5,000 so every plot over 1,000 m² has a readable area label, in `img/plotflow_2056_*.pdf` (`py/map_plot_flows.py`), for the engineer to judge the growth-plot shape and area limits.
- QGIS project of the plot flows: `qgis/W18_plot_flows.qgz` (`py/qgis_plot_flows_project.py`, built headless with QGIS 3.44). Plots filled by average flow in a blue gradient (2031, 2056 shown, 2071, 2100; no flow = empty), existing plots outlined by land use in the LBCS colours (residential yellow, mixed orange, commercial red, government blue, industrial purple, agricultural green), proposed plots outlined light grey, settlement boundaries, Google satellite hybrid at 30 %. The plot shapefile it reads is local (not in git): rebuild it with `py/plot_layer_2100.py`. Settlement layer 2026–2100: `gis/W18_settlements_2026_2100.shp` (`py/settlements_2100.py`, fields in `_fields.md`): the 25 W14 boundaries with W18 attributes, summed from the plot layer (checked to it every year): population and flow every year, OR (W14 measured) and OR_2026 (team's 2026 population / meters), properties per growth plot at saturation and 2100 against the team's, capacity and full years, area, plot counts inside the boundary, existing plots by land use and by Nama meter category, empty plots by count and by area, growth plots, flow not carried 2031/2056/2071. In the QGIS project and its zip. W14's `Settlements_merged` keeps its old attributes as the record. Packaged with its layers, to open anywhere: `gis/W18_plot_flows_QGIS.zip` (`py/package_qgis_plot_flows.py`, 8.8 MB, with the workbook below).
- **The team's MH workbook with the capacity (2026-11-17):** `results/New Calculation MH - capacity.xlsx` (`py/mh_workbook_capacity.py`, edited in Excel so the chart sheet and their formulas survive; not in git, it carries the team's raw data). `MOHUP DATA - NA`: Existing Population 2026, Existing Residential Plots, Future Plots (growth plots, blue) and Future Population inserted; their Future Residential Plots kept in grey, unused; properties per plot = MAX(1, B/D); capacity = C + J; saturation year by COUNTIF. `WW Generation`: MIN(average, capacity) × 171.03 + infiltration, plus a row for the estates (316.4); 2071 49,323 m³/d = model 46,810 + not carried 1,414 + infiltration 1,099. The other eight sheets identical to theirs, cell for cell. One package with QGIS, the plot shapefile, this workbook and the SewerGEMS R4 model with its 13 results: `deliverables/W18_package_<date>.zip` (`py/package_w18_deliverable.py`, 168 MB, not in git), sent to the engineer.
- The capacity on the engineer's rule (2026-11-17): `results/W18_MOHUP_DATA_NA_growth_plots.xlsx` (`py/mohup_sheet_growth_plots.py`). Sheet 'MOHUP DATA - NA' rebuilt with live formulas: existing population = the team's 2026 average; future population = our growth plots × the team's properties per plot (existing residential properties ÷ existing residential plots) × 4.8; capacity = the two added (the team's own capacity, (existing + future properties) × 4.8, counted the existing properties at 4.8 people while the 2026 population puts 5.98 on them in Ibri). The team's count, capacity and year alongside; their sheet unchanged on 'Team original'; 4.8 in one input cell. Result: 403,668 people against the team's 443,102 (Ibri 144,537 against 146,116, full in 2063 against 2064; Bat 2057 against 2074). **Applied the same day** (engineer: the team's average population is untouched, the capacity only sets the year a settlement stops) to the loads, the plot layer and the settlement layer (`CAPACITY`; the team's in `CAP_TEAM`): 2026–2056 unchanged on every plot, 2061 −82, 2066 −448, 2071 −634 and 2100 −3,245 m³/d. SewerGEMS's 2056 loads are not affected by it. Audit: `py/audit_w18.py` (44 checks from the raw sources, all pass, `results/loads/audit.md`); run it after any change to the loads, layers or workbook. The workbook's saturation years use COUNTIF, so they compute in any spreadsheet app (the first build's array formula showed 'Not Fully Occupied' everywhere on a phone).
- Growth-plot check maps: `img/oddplots_*.pdf` (`py/map_odd_plots.py`), Ibri and the five settlements, overview plus A3 sheets at 1:5,000: every future plot coloured by why it takes growth or not (agricultural, under 200 m², odd shape, over 3,000 m²), the small and odd ones circled and labelled with their area. Ibri: 13,331 future plots (any zoning but agricultural, heritage, industrial); out 1,257 under 200 m², 216 odd-shaped, 340 over 3,000 m², 465 groves; 11,053 take growth.

## Earlier rules kept (checked 2026-11-16 at the engineer's request)

- **W14 rule 4: the industrial estates are additive.** 6,300 workers × 93 L/d × 0.54 = **316.4 m³/d**, on their plots, outside the per-capita volume (doctrine 1b). The plot flow is the team's sheet plus 316.4.
- **The growth plots (engineer, 2026-11-17: "the limit is 200 to 3000 m2; proposed agriculture lands out; all odd shape plots out"):** a future plot of **any zoning** (the planning layer's proposed uses are not trusted, so residential, commercial and proposed plots count alike), inside its settlement boundary, **200–3,000 m²**, **not odd-shaped** (compact ≥ 0.6, length ≤ 3 × width), and **not agricultural** (zoned so, or a grove on the satellite test), heritage (zoned Tourism), industrial or an estate. There are **43,230** (Ibri 11,053; 656 of them zoned commercial), shared equally per plot (8 Nov). This replaces W14's spread set, which stopped at 2,000 m².
  - The same day the rule first required residential zoning (42,567 plots); the engineer dropped it: "I am not sure the proposed plot use are correct ... treat all receiving plots the same."
  - Before (2026-11-16): W14's home-shaped plots, 200–1,000 m², then 200–2,000 m² (43,238 plots).
  - **The 2,000 m² step (2026-11-16, superseded the next day)** It adds 1,838 growth plots. Of the 2,815 empty plots of 1,000–2,000 m², 1,983 pass; 456 are groves, 268 fail the shape test, and 108 are industrial or unmetered. Most large empty plots are over 2,000 m² (Bat 271 over 1,000 m², 106 of them up to 2,000).
  - W14's wider spread set of plots up to 2,000 m² would have put a house plot's share on 7,483 slivers and strips (median 80 m², 5,194 m³/d in 2071).
  - Existing plots keep their metered flow whatever their shape.
- **The inactive network (R7 §6.2.5):** branches in planted areas, where ground levels are unreliable until the survey, and three small outlying catchments proposed for on-site treatment (absorption wells).

## Flow that does not enter the network (engineer, 2026-11-16)

These plots are not carried, and their flow stays in the settlement totals:
- **Inactive network (bad terrain):** a plot whose nearest manhole is inactive, as in W17 (558 plots with flow in 2071, the largest group in central Ibri).
- **Farther than 200 m from the network:** a plot whose edge is more than 200 m from an active sewer, measured straight between manholes (1,796 plots with flow in 2071).
- **Outside its settlement boundary (no flow at all):** 5,907 plots lie outside their redrawn settlement boundary, which sits inside the project boundary. They take no flow, and the settlement's flow is shared by the plots inside it (engineer, 2026-11-16). Ibri's future home plots come to 13,119, against 13,120 in the team's count.

| m³/d | 2031 | 2056 | 2071 |
|---|---|---|---|
| Inactive network | 520 | 658 | 708 |
| Farther than 200 m | 172 | 470 | 706 |
| Not carried | 693 | 1,128 | 1,414 |
| Carried (before infiltration) | 22,391 | 37,892 | 46,810 |

With the 1,000 m² limit these were 684 / 1,064 / 1,336 not carried and 22,400 / 37,957 / 47,522 carried; job 069 and the SC1 run (job 070) hold those loads.

**These values go into the report, with a map of the plots in the two categories.**
- Layer: `gis/not_carried_plots.gpkg`.
- Draft map: `img/not_carried_plots.png` (`py/map_not_carried.py`).
- The report figure is a QGIS layout, made with the report's other maps.

Model loading:
- Plots without a manhole (HMINNODE 0, 6,499 plots that carried no flow in W14) go to the nearest manhole that has a load row.
- The six year alternatives of the model carry 2031, 2051, 2056, 2061, 2066 and 2071.
- New year alternatives failed in jobs 060–066; the cause was a load on a manhole without a load row. Job 067 proved the loading, and job 069 has the final loads.

## SC1 designed for 2056 (final loads) and the slope check

**Model reloaded (job 071, 2026-11-17): `C:\IbriWork\W18\IBRI_W18_R3.stsw`** = W17 R8 with the six year alternatives (W18-2031, -2051, -2056, -2061, -2066, -2071) set from the final loads (growth plots 200–3,000 m², any zoning but agricultural / heritage / industrial; capacity = 2026 population + growth plots × properties per plot × 4.8): stored = file in every year (2031 22,391.33, 2056 37,892.16, 2071 46,809.56 m³/d carried; 14,989 manholes loaded). Outfall flows for the transfers in `bridge\out\w18\f0` (R0's archived in `f0_R0`): 2056 −0.2 %, 2071 −1.4 % against R0. R0 and the SC1 design R2 (below, on R0) are kept as the record; **SC1 is not yet redesigned on R3.**

**Thirteen years in the model (job 072, 2026-11-17): `C:\IbriWork\W18\IBRI_W18_R4.stsw`** = R3 + seven year alternatives for 2036, 2041, 2046, 2076, 2081, 2086 and 2091, every 5 years from 2031 to 2091 now (engineer). They were made with `IModelingElementManager.Copy(14)`, a copy of the loaded 2070 alternative with its own records - the way round the trap of jobs 060-065, where a new child alternative (`Add(parent)`) could not be read once a sibling held records. All 13 set from `manhole_loads.csv` (now 2026-2091, `py/nws_loads.py`), stored = file in every year (2036 24,951.78 · 2076 48,047.82 · 2091 51,304.93 m³/d carried); a scenario W18-yyyy and outfall flows for every year (`bridge\out\w18\f0`), every outfall rising from one year to the next. Confirmed in the model (job 073, read only, `lib/Confirm.cs`, `bridge\out\w18\confirm_R4.txt`): in W18-2031, -2056 and -2091 every load row is the unit load 'Plot average flow (1 m³/d per unit)', discharge-based, 1 m³/d per unit (15,711 manholes, 14,989 above zero), and there are no pattern loads; the calculation options (279786) use Extreme Flow Setup 277433, which peaks that unit load with 'Peltier100-Merriamck'; the infiltration-and-inflow alternative every W18 scenario inherits (11) puts 0.000294289 cfs per km = 720 L/km/day on 19,285 conduits (one has none).

**SC1 designed for 2056 (job 070), on the loads with the 1,000 m² growth limit** (the 2,000 m² loads carry 42 m³/d less in 2056; the model is not yet reloaded):
- **The design:** it converged in 4 passes; every pipe is laid at its Table 11 floor; the plant inlet at O1 is 10.0 m deep; 316 manholes are over 12 m.
- **The 2031 check:** of the pipes above DN200 (151.8 km), 9.7 % reach 0.75 m/s.
- **Steepening to reach 0.75 m/s, by slope limit** (check run `W18…/py/selfcleansing_slope.py`, maps `img/depth_SC1-2056_*.png`):
  - **0.50 %:** 26.6 km of the length above DN200 stays below 0.75 m/s (17.5 %), 352 manholes are over 12 m, and the O9 station goes to 22.2 m (+5.4) and O3 to 10.8 m.
  - **0.75 %:** 9.5 km stays below (6.3 %), 426 manholes are over 12 m, and O3 goes to 15.8 m.
  - **1.00 %:** 3.1 km stays below (2.1 %), 458 manholes are over 12 m, and O3 goes to 23.8 m.
  - **In every case:** the plant depth does not change, and all 1,346 km of DN200 stay below 0.75 m/s.
- **Recommended to NWS:** a 0.50 % limit (the DN200 minimum of Table 11), with about 17 % of the length above DN200 on a flushing list.

Results: `results/SC1-2056_final/`, `results/selfcleansing_slope/SC1-2056_final/`; the provisional run is kept in the `_provisional` folders.

## SC1 redesigned on the R4 loads (job 074, 2026-11-17) and the split of the deep subnetworks

**R5 = `C:\IbriWork\W18\IBRI_W18_R5_SC1_2056.stsw`** (job `074_w18_R5_SC1_2056.ps1`, `lib/build_scenario.ps1` on R4): SC1 designed for 2056, checked at 2031, transfers from R4's outfall flows (`py/make_transfers.py SC1 2056 2031`, same 20 routes as R2, 469 m³/d less in 2056). Converged in 4 passes (1,867 / 757 / 124 / 0 sizes changed), the analyses changed no size. The depth is R2's: 318 manholes over 12 m, deepest 21.97 m. Exports `results/SC1-2056_R5/`; 2031 slope check `results/selfcleansing_slope/SC1-2056_R5/` (1 %: 98.1 % of the length above DN200 reaches 0.75 m/s, 458 manholes over 12 m, deepest 29.25 m). R2's exports archived in `bridge\out\w18\scen\SC1-2056_R2`.

*Superseded on 2026-11-18 by "SC1 in four conditions" below (outfalls never moved, one gradient per street run, SewerGEMS velocity, outfall ground from the model).* **Split of the deep subnetworks (engineer, 2026-11-17), mapped, NOT yet in the model** (`py/split_deep_subnetworks.py` -> `results/split/SC1-2056_R5*/`: SUMMARY, cuts, joins, nodes, map PNG, GeoPackage):
- Pipes above DN200 steepened to 0.75 m/s at the 2031 peak, up to the limit; every subnetwork.
- A subnetwork deeper than 12 m for good - every manhole from there to its OWN outfall deeper than 12 m - is cut at the last manhole at 12 m or less: a pumping station lifting to the next manhole, which restarts at minimum cover. Dips that come back to 12 m or less within their own subnetwork are left alone. (Recovery is confined to the subnetwork: otherwise a gravity join let 25 m sewer run for kilometres into the next subnetwork.)
- A cut on the last pipe into a pumped outfall moves that station one manhole up (not a new station).
- An outfall at 12 m or less within one manhole spacing (G203 Table 12, p30: DN200-315 100 m, 350-900 120 m, 1000-1400 150 m, over 1400 200 m) of the manhole it pumps to is joined by gravity, kept only if the stations in all go down; the join re-lays the receiving subnetwork, which may be cut again. One cut per round, re-laid after each, until nothing changes.
- Re-lay = the SewerGEMS design rule, checked on all 19,083 pipes (99 % to 0.000 m, largest 0.16 m): upstream invert = the lowest of the lowest arriving invert, the lowest arriving crown less the pipe's diameter (crowns matched) and the shallowest the cover allows (1.3 m over the soffit at both ends; every head pipe sits exactly there).

| gradient limit | length above DN200 at 0.75 m/s (2031) | stations (plant inlet not counted) | new | moved up | joined by gravity | deepest manhole left |
|---|---|---|---|---|---|---|
| none (the design) | 9.3 % | 21 | 6 | 2 | 9 | 21.97 m |
| 0.50 % | 82.6 % | 27 | 9 | 2 | 6 | 16.47 m |
| 0.75 % | 93.9 % | 29 | 11 | 2 | 6 | 16.17 m |
| **1.00 %** | **98.1 %** | **31** | **13** | **2** | **6** | **16.17 m** |

Today 23 stations. At 1 %: new stations in O3 (2), O9 (7), O11, O12 (2) and O14, 4.9-29.7 L/s in 2056, 11.0-12.0 m deep, each lifting over one pipe length (62-117 m); O20 and O23 move one manhole up; O2, O3, O5, O6, O7 and O14 join the next subnetwork by gravity. 241 manholes stay deeper than 12 m in dips that come back (176 at 12-14 m, 63 at 14-16 m, 1 at 16.2 m). Next: the engineer's choice of limit, then the cuts, joins and minimum gradients in SewerGEMS (R6).

## SC1 in four conditions, re-laid from R5, maps in the QGIS project (engineer, 2026-11-18)

**Live; supersedes `results/split/` (2026-11-17).** `py/split_deep_subnetworks.py` revised on the engineer's rulings of 2026-11-18, run on R5's exports into `results/sc1_conditions/<condition>/` (SUMMARY.md, summary json, pipes/nodes/cuts/joins csv, GeoPackage); `py/qgis_sc1_conditions.py` adds the four maps to the QGIS project the engineer was sent (`qgis/W18_plot_flows.qgz`, group "SC1 sewer conditions", one condition at a time, saved layouts `SC1 C0`...`C3`, exported to `results/sc1_conditions/maps/`); `py/package_qgis_plot_flows.py` packs them into `gis/W18_plot_flows_QGIS.zip` (28 MB). Map style, engineer 2026-11-18: label size by the map scale `clamp(7, 8*25000/@map_scale, 36)` pt with a 0.8 mm buffer; on C0 an arrowhead at each pipe's centre in the flow direction from 1:15,000 in (field `flow_rev` in the C0 GeoPackage, from the R5 inverts); both built by `py/qgis_sc1_conditions.py`.
- **An outfall is never moved:** a cut is a split of the network, so no cut is made on the last pipe into an outfall that is still one (pumping station or plant inlet); it keeps its depth. (The 2026-11-17 run moved O20 and O23 one manhole up: withdrawn.)
- **One gradient per street run:** a run follows, at each manhole, the arriving pipe of the same size within 30 degrees of the leaving pipe's line (68 % of pipe-to-pipe deflections are under 30 degrees, the rest are corners); its gradient is the steepest any of its pipes above DN200 needs for 0.75 m/s at the 2031 peak within the limit; each pipe takes the steeper of that and its laid gradient. Checked: no spread of gradient within any steepened run; median 3-4 pipes per run, longest 58.
- **Velocity is SewerGEMS's own** (2031 and 2056 analyses of R5), scaled by the Colebrook-White ratio where the gradient changes; the required gradient is the one at which that scaled velocity reaches 0.75 m/s. **Maximum 3.0 m/s at the design flow (G203 p27) checked on every pipe at the 2056 peak: none over, highest 1.07 m/s in every condition.**
- **Outfall ground and position from the model's own outfalls** (W17 `S1.gpkg`, same labels), no longer the manhole above: the re-lay now reproduces SewerGEMS's inverts exactly (0.000 m on all 19,083 pipes).

| condition | length above DN200 under 0.75 m/s (2031) | steepened | stations | new | joined by gravity | manholes > 12 m | deepest |
|---|---|---|---|---|---|---|---|
| C0 as designed | 137.6 of 151.8 km (91 %) | - | 23 | - | - | 318 | 21.97 m |
| C1 up to 0.50 % | 26.4 km (17.4 %) | 115.8 km, 189 runs | 25 | 7 | 5 | 235 | 16.47 m |
| C2 up to 0.75 % | 9.2 km (6.1 %) | 130.4 km, 231 runs | 27 | 9 | 5 | 274 | 16.19 m |
| C3 up to 1.00 % | 2.9 km (1.9 %) | 136.2 km, 244 runs | 29 | 11 | 5 | 275 | 16.19 m |

As designed, four outfalls are deeper than 12 m: O9 16.78, O12 14.56, O14 12.73, O11 12.13 m; all DN200 (1,346 km) is under 0.75 m/s at 2031. Joined by gravity in C1-C3: O2, O3, O5, O6, O7. **O14 and O11 are kept deep, uncut (engineer, 2026-11-18):** their cuts sat next to the outfall (O14-M2 left one 62 m pipe to O14, which then joined O9 by gravity - in effect the station two manholes up; O11-M6 left 365 m and one branch - an extra station only because O11 is 12.13 m deep as designed). They stay stations at 12.73 m (O14) and 12.39 m (O11, steepened); dropping O11's cut saves a station, O14's does not (its cut came with the gravity join). **A join may not deepen an outfall kept uncut:** O12 -> O11-M96 (66 m) would save one more station but takes O11 from 12.4 to 15.0 m with 25 O11 pipes deeper than 12 m (to 16.0 m), so O12 stays a station. Every other cut leaves 0.9-9.2 km of network with 2-35 branches below it. Not yet in SewerGEMS.

**One package with everything (2026-11-18):** `deliverables/W18_package_SC1_2026-11-17.zip` (203 MB, not in git; `py/package_w18_deliverable.py`): QGIS/ (the project above with the plot and settlement layers, the SC1 condition layers, layouts and maps), Excel/ (the team's MH workbook with the capacity), SewerGEMS/ (`IBRI_W18_R5_SC1_2056` copied out of the VM by job 075, with the results of its 3 SC1 and 13 year scenarios). Sent to the engineer; the 2026-11-17 package with R4 is kept as it was.

## SC1 designed for 2051, steepened to 0.50 % (team's review, engineer 2026-11-18)

The team found that 1 % adds many lifts at short distances and asked for 0.50 % with SC1 designed for 2051: how many stations, and what length of pipe above DN200 stays under 0.75 m/s at the 2031 peak. **Job 076** (`IBRI_W18_R6_SC1_2051.stsw`, from R4 with the same builder as job 074; transfers `py/make_transfers.py SC1 2051 2031 2056`, plant 929.7 L/s in 2051 against 1,018.8 in 2056) designed SC1 for 2051 in four passes and analysed it at 2031 and 2056; exports in `results/SC1-2051_R6/`, model copied out by job 077 (`bridge\out\w18\model_R6`, 573 MB). `py/split_deep_subnetworks.py` ran unchanged on it (`results/sc1_2051/sewergems/`; its text says "2056" where it means the design year, here 2051). Comparison: `results/sc1_2051/COMPARISON.md` (`py/compare_own_sewergems.py`).

| design year, gradient limit | stations | new | joined by gravity | above DN200 under 0.75 m/s at 2031 | manholes > 12 m | deepest |
|---|---|---|---|---|---|---|
| 2051 as designed | 23 | - | - | 122.3 of 144.4 km (84.7 %) | 318 | 22.64 m |
| **2051, up to 0.50 %** | **25** | 7 | 5 | **19.1 of 144.3 km (13.2 %)** | 228 | 16.49 m |
| 2056, up to 0.50 % (C1 above) | 25 | 7 | 5 | 26.4 of 151.7 km (17.4 %) | 235 | 16.47 m |

- **2051 saves no station** against 2056 at 0.50 %; it leaves 7.3 km less pipe under 0.75 m/s and makes 689 pipes (59.2 km) one size smaller (none larger; DN1200 appears on 27 pipes of O2's main). All DN200 (1,353 km) stays under 0.75 m/s, as in every condition (not checked, engineer's rule).
- **The cost is in 2056:** the 2051 pipes run over the d/D limit (0.65 up to DN355, 0.50 above) on 601 pipes, 51.8 km, as designed (SewerGEMS, SC1-2051-at-2056); about 270 pipes, 22.5 km, once steepened to 0.50 % (Colebrook-White normal depth; 95 DN200, never steepened, and 93 DN1200-1600 trunk pipes that already reach 0.75 m/s); largest d/D 0.75, none full, highest velocity 1.07 m/s.

**Own design against SewerGEMS (engineer: "if you do yourself for 2051 and with SewerGEMS, the results will be the same?").** `py/own_design.py` designs SC1 without SewerGEMS on rules read from its 2056 design and checked on it: flow = PF ('Peltier100-Merriamck' on the cumulative unit load) x load + 720 L/km/day + transfers (all 19,083 pipes to 0.00 %); gradient = the Table 11 minimum of the size (all pipes); size = the smallest whose Colebrook-White capacity at d/D 0.65 (to DN355) / 0.50 carries the flow at the gradient of the pipe's CURRENT size, pass after pass from the modeller's sizes until none changes (all 19,083 sizes of 2056 in 3 passes; sizing each candidate at its own gradient instead gives 63 pipes one size smaller, so SewerGEMS's answer depends on its starting sizes there); inverts by the re-lay (0.000 m). **Run blind for 2051 before job 076 finished:** flows identical (largest 0.004 %), sizes identical on 19,056 of 19,083 pipes - the 27 others are the DN1200 pipes, a size in SewerGEMS's catalogue but on no 2056 pipe, so missing from the catalogue read off the 2056 design; with it added, identical on all pipes in 2051 and 2056. Through the 0.50 % split both give the same 25 stations at the same manholes and 19.1 km under 0.75 m/s; 2031 velocities agree to +/-0.001 m/s (5-95 %). Valid for these design options (fixed Table 11 gradients, steady peaked flows, Colebrook-White, these d/D limits); SewerGEMS stays the model of record. Not covered: a SewerGEMS redesign with the steepened gradients as minimum slopes may choose a smaller size on some steepened pipes (2056 at 0.50 %: 48 pipes, 3.9 km could drop one size), which the re-lay keeps.

## SC1-2056 at 0.50 %: fewer stations in O12 and O9 (engineer, 2026-11-18)

The engineer, on the C1 map: the new stations are only in O12 and O9; without O12-M26 and O12-M193, how deep is O12, can they merge? O9-M103 and O9-M89 are close, one after the other, and both go deep. `py/whatif_merge_stations.py` runs `py/split_deep_subnetworks.py` unchanged on R5 at 0.50 % (checks it gives C1: 25 stations, 26.4 km), then on its final network, all other cuts and joins kept, removes the pair's stations, keeps one, or tries one station at every manhole that both flows pass. Results: `results/sc1_conditions/whatif_C1_O12_O9/` (WHATIF.md, single_station_sites.csv).

| case | stations | station | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| O12 as mapped | 25 | M26 11.9 m, M193 11.9 m | 8.7 m | M284 14.8 m (a dip) | 2 |
| O12 without both | 23 | - | **14.6 m** | M5 15.4 m | 39 (3.9 km of pipe) |
| O12, one station where the branches meet (M2) | 24 | 14.4 m | 8.7 m | M5 15.4 m | 37 |
| O9 as mapped | 25 | M103 12.0 m, M89 11.9 m | 10.1 m | M48 16.5 m (a dip) | 101 |
| O9 without both | 23 | - | **17.0 m** | M48 23.3 m | 159 |
| **O9, one station at O9-M101** (200 m below M103) | **24** | **12.6 m** (M102 above it 12.2 m) | 10.1 m | M48 16.5 m | 103 |

- **O12's two stations are not caused by the steepening:** O12 is 14.56 m deep as designed (SewerGEMS) and 14.63 m steepened; only one 54 m pipe below the stations is steepened. They are the 12 m rule on the design's own depth, like O11 and O14. They sit on two DN200 branches (7.2 and 5.1 L/s) about 1.1 km apart, 2.3 km and 1.1 km of sewer above O12-M2, where they meet just above the outfall; one station at M2 is 14.4 m deep, no better than keeping O12 deep.
- **O9-M103 and O9-M89 are in series, 1,263 m of sewer apart (1.1 km crow-fly).** One station at O9-M101 (a branch joins there; 6.2 L/s) replaces both at 12.6 m, with O9-M102 above it at 12.2 m; everything downstream as mapped. Any other single site is deeper or leaves more of the line deep. Leaving the 5.1 km of steepened trunk below them at the design gradient also removes both stations, but leaves 5.1 km under 0.75 m/s and 14.2 km of pipe deeper than 12 m.
- **O9-M773 and O9-M728 (engineer's follow-up) cannot merge:** in series, 4,091 m of sewer apart (3.4 km crow-fly). Only O9-M773 leaves O9 at 14.3 m with 47 manholes deeper than 12 m for good; only O9-M728 puts it at 19.7 m; no single site of 92 clears the line. None of the pipes between them is steepened: O9-M728 is there because the steepened run below it goes deep. Leaving the first 14 steepened pipes below it (1.25 km, to O9-P709) at the design gradient removes O9-M728: 24 stations (23 with the O9-M101 merge), O9 outfall 11.9 m, but 1.25 km more under 0.75 m/s at 2031 (26.4 -> 27.7 km, 18.2 %), manholes over 12 m 101 -> 125 and pipe over 12 m 9.4 -> 11.6 km (dips that come back).
- **Engineer's decisions (2026-11-18), 0.50 %, 2056:** O12 keeps no new station (outfall 14.6 m accepted); O9-M103 and O9-M89 become one station at O9-M101 (12.6 m accepted); O9-M728 is removed and O9-M773 kept (station 12.0 m, O9 outfall 14.3 m accepted; he wrote "only O9-M728" with the numbers of this case - keeping only O9-M728 would put it at 19.7 m). Result (`WHATIF.md`, last section): **21 stations** (C1 25), new ones left O9-M101 12.6 m, O9-M166 12.0 m, O9-M773 12.0 m; manholes deeper than 12 m 321 (C1 235), pipe deeper than 12 m 29.1 km (C1 21.5 km), deepest 16.5 m. **Self-cleansing unchanged** (gradients are set before the split): 26.4 of 151.7 km above DN200 under 0.75 m/s at 2031 (17.4 %), 331 pipes, 21.3 km of it DN250 (69 % of the DN250 length) at about 7 L/s; 17.2 km would reach it at 0.50-0.75 %, 0.8 km needs over 2 %; O3 holds 11.8 km. List: `under_075_engineer_choice.csv`. Not yet in the split tool, the maps or SewerGEMS.

## Final design at 0.75 %, SC1-SC4, design years 2051 / 2056 / 2061 (engineer's brief, 2026-11-18) - in progress

**Live.** The engineer chose 0.75 % and asked for every scenario (SC1 STP 1 only, SC2 STP 16 only, SC3 STP 1 + STP 5, SC4 STP 16 + STP 5) designed for 2051, 2056 (base: 2031 + 25) and 2061, self-cleansing checked at the 2031 peak and, for what misses it, at 2036; stations reduced by his logic (a pump, a lift or an added station up to 14.65 m, manholes up to 16.5 m); pumps renamed P#, lifts P#L#; own code first, SewerGEMS after; the R7 maps, QGIS, BOQ, SewerGEMS projects and the team's R8-MH report. Brief in memory `w18-final-design-brief`.

- `py/final_design.py <SC> <year>`: the design without SewerGEMS (rules of `py/own_design.py`, the full catalogue DN200-DN3000 read from R4 by job 078; on SC1-2056 every one of the 19,083 sizes equals SewerGEMS's, flows within 0.004 %). The gravity network is the same in every scenario; `py/routing.py` sets the plants and transfers. Inputs in `results/final_0.75pc_SC1-SC4/inputs/`.
- `py/reduce_stations.py 0.0075 <case> ...`: his logic with the 14.65 / 14.65 / 16.5 m limits, plus two rules from his rulings: no station may hand its flow to less than 400 m of sewer above its outfall (an outfall is never moved; his O11 case, 365 m), and O12 kept deep as he decided (14.71 m at 0.75 %, 6 cm over the limit). Station sets in `fixed_stations.json`, read by `split_deep_subnetworks.py --fixed=`.
- `py/final_selfcleansing.py`: 2031 and 2036 check.

| case | stations (new) | above DN200 | under 0.75 m/s at 2031 | still under at 2036 | manholes > 12 m | deepest |
|---|---|---|---|---|---|---|
| SC1 / SC2 2051 | 23 (5) | 144-148 km | 4.5 km (3 %) | 4.2 km | 308-311 | 16.0 m |
| SC1 / SC2 2056 | 23 (5) | 151-155 km | 9.3 km (6 %) | 8.3 km | 333-336 | 16.2 m |
| SC1 / SC2 2061 | 23 (5) | 159-163 km | 14.3 km (9 %) | 13.1 km | 359-362 | 16.3 m |
| SC3 / SC4 2051-2061 | 22 (5) | 141-160 km | 4.5 / 9.3 / 14.3 km | 4.2 / 8.3 / 13.1 km | 308-362 | 16.0-16.3 m |

New stations in every case: O9 four (O9-M166/M167, O9-M72, O9-M763 13.6 m, O9-M89 13.7 m; from six), O3 one (2051: O3-M1446 12.8 m, two merged); O12 none. Highest velocity 1.14 m/s. The 2036 flow cures little (9.3 -> 8.3 km at 2056): the shortfall is low-flow DN250 laterals. Per case `results/final_0.75pc_SC1-SC4/<case>/` (design.json, reduce/REDUCE.md, split/SUMMARY.md, selfcleansing_pipes.csv); exports and GeoPackages are rebuilt in seconds and not kept in git.

**Since then (2026-11-18):**
- **Lifts as transfers:** the design now carries every lift's peak to the next manhole as a transfer, not re-peaked (the rule for anything pumped); 99 pipes (8.9 km) of SC1-2056 one size larger; `py/final_run_all.py` repeats design and split until the lifts stop changing (2 passes). Stations unchanged; above DN200 under 0.75 m/s at 2031: 4.5 / 9.3 / 14.5 km.
- **Naming** (`py/final_naming.py`): pumps P1-P15 in the old outfall order (P1 = O1 ... P15 = O24), lifts P#L# (a station whose force main reaches a manhole within one Table 12 spacing; a new station always), plant inlets are pumps; SC1/SC2 14 pumps + 9 lifts, SC3/SC4 13 + 9. Plants named as the team does: STP-1 (O1, P1), STP-2 (O16, P7), STP-5 (O4, P2) - the engineer's "STP 16" is STP-2.
- **Products** (`py/final_products.py`): stations sized by the R7 method; SC1-2056 plant inflow 1,018.8 L/s, equal to SewerGEMS's. Maps (`gis/final_maps.py`, 17 report maps in `report_final/img/`), QGIS project of the 12 cases (`results/final_0.75pc_SC1-SC4/qgis/`), BOQ and network cost at the team's rates (`py/final_boq.py`, `report_final/deliverables/`): 2056 network SC1 125.7, SC2 132.5, SC3 118.5, SC4 125.0 M OMR (STP, TE, OPEX left to the team).
- **SewerGEMS** (`py/final_sg_inputs.py`, `sewergems_api/lib/FinalBuild.cs` + `build_final.ps1`, jobs 079-084): a case put into a copy of R4 - sizes and inverts of every conduit, a lift as its station manhole -> 1 m stub -> new outfall with its pipe switched off and its flow a transfer to the next manhole, every element renamed, transfers for 2056 / 2031 / 2036, analyses (no design run). Job 080 (SC1-2056): flows equal to the own design on 97.8 % of pipes; but the two large gravity joins created through the API (P1-P92, P1-P151) were not solved (0.305 m depth, 5-7 m/s), and their headloss backed water up 20 pipes (175 full pipes). **Joins are therefore carried as transfers in the model** (as the design sized them); the short join sewers stay in GIS and the BOQ. Jobs 081-084: the four scenarios 2056. Comparison `py/final_sg_compare.py` -> `<case>/sewergems/COMPARE.md`. SewerGEMS models of SC1-SC4 2056 (jobs 081-084) checked against the own design: flows within 0.1 % on every pipe, no pipe over the depth-of-flow limit, the same 9.0 km above DN200 under 0.75 m/s at 2031 (the 265 steepened pipes show 0.749-0.750 m/s in the model); package `deliverables/Ibri_Sewer_Final_Design_SC1-SC4_2026-11-18.zip` (651 MB: report draft, BOQ, maps, QGIS, the four models with their final scenarios only) sent to the engineer's WhatsApp on 2026-11-18.
- **Report R9** (`report_final/build_report.py` + `word_finish.py` on a copy of the team's R8-MH; outputs not in git): Chapter 3 gradients and the 0.75 % limit (SC1-2056 at 0.50 / 0.75 / 1.00 %: 21 / 23 / 25 stations, 82.9 / 93.9 / 98.0 % self-cleansing), depth and pumping (lift and pumping stations), station sizing on the design-year peak; Chapter 6 rewritten for SC1-SC4 (method, design year with the 2051 / 2056 / 2061 table and the reasoning for 2056, network, plants, stations, maps, comparison, the team's TE subsections kept for SC1-SC3); Appendix D depth maps and tables; glossary naming. Captions renumbered in a hidden Word; 26 cross-references whose targets no longer exist kept as text. Clean gate: 13 hits, all in the team's chapters (pp. 82, 145, 157, 165, 174, 193), so the outputs carry FAILED-CLEAN-CHECK. **Still the team's:** SC4's TE network, the executive summary, STP chapter, financial analysis, appraisal and conclusions (they still describe the seven options).
- **SewerGEMS of the 2051 and 2061 designs** (jobs 086-093, the same build as 081-084; copy-out job 094): all eight match the own design as the 2056 ones do - flows within 0.1 % on every pipe, no pipe over the depth-of-flow limit, the same length under 0.75 m/s at 2031 at two decimals (2051: 4.2 km, 2061: 14.1 km in both). `<case>/sewergems/COMPARE.md`.
- **Treatment, TE and financial analysis** (`py/final_financial.py` -> `results/final_0.75pc_SC1-SC4/financial.json`, `report_final/deliverables/Ibri_Treatment_TE_and_Financial_SC1-SC4.xlsx`): the team's cost method (`W:/.../11_Finacial/2621 - Options Cost Estimation-MH 14-10-2026.xlsx`: STP rate and land by capacity band, 0.025 kW per m3/d, 1 % M&O, power x flow share, land 1 OMR/m2/month, staff ROUNDUP(stations/5)x2 + 20 or 28, chemicals) on the final flows; four modules per plant on 2056 inflow + 10 % (SC1 STP-1 4 x 11,000; SC3 STP-1 4 x 9,500 and STP-5 4 x 1,750); 2031 prices, 5 % escalation; present value at 5 % over 2031-2055. 25-year escalated total SC1 364.3, SC3 374.5, SC2 377.8, SC4 390.9 M OMR; present value SC3 214.9, SC1 217.3, SC4 225.4, SC2 226.3. TE: every plant meets its customers' demand from 2031 (team's register; SC3 split read from their TE model); SC4 = SC3's STP-5 network + SC2's main pruned to STP-2's customers, 89.4 km, 826 kW (pro rata), map `gis/te_map_sc4.py`. The team's TE data stays out of git (`results/.../te/`, from W:/.../10_TSE).
- **Report R10** (`report_final/r10_edits.py` on top of the R9 build, outputs in `report_final/R10/`, not in git; the engineer: "review the entire report and update all parts"): executive summary, Chapters 5, 7-17 and Appendices A, B, C.3, F, H brought to SC1-SC4 and the 2056 design; Chapter 4's flows reconciled to the plant inflow (Table 4-13 + estates 316 - infiltration allowance 1,099 - not conveyed + 1,079 modelled infiltration, exact to 2061); SC1 recommended, SC3 alternative (SC2/SC4 not). Every cross-reference written as its current number (the team's printed 'Section 0'), caption chapter parts as text, 213 team highlights removed. Clean gate extended with regexes for review notes and option names, and PASSED (204 pages). Sent to the engineer's WhatsApp (Word and PDF) 2026-11-18. **Still the team's to confirm:** the STP-5 footprint (mosque at 349 m < 500 m) on which SC3/SC4 depend; Chapter 7 says STP-2 passes separation while Chapter 9 reports a dwelling at about 380 m.

## Fewer stations: the engineer's decisions at 0.50 %, his logic at 0.75 and 1.00 % (2026-11-18)

**Live; C1-C3 in the QGIS project are these runs since 2026-11-18. The first-searched splits stay in `results/sc1_conditions/C#_limit_*pc/` as the record.** The engineer decided O12 and O9 at 0.50 % (section above) and asked for his logic to be learnt and applied to every subnetwork at 0.75 and 1.00 %. `py/reduce_stations.py <limit>` does it on the split as searched: per subnetwork with new stations, repeatedly drop one station or replace two by one at any manhole both flows pass (not on the last pipe into an outfall), while every new station stays at or under 12.65 m, the outfall at or under 14.65 m and no manhole deeper than 16.5 m - the deepest he accepted (O9-M101 12.63 m, O12 14.63 m, O9-M48 16.47 m); shallowest outfall first. At 0.50 % it gives exactly his choice. Without the third limit, dropping O9-M72 (0.75 %) or O9-M69 (1.00 %) passed the other two but left a 21 m manhole. The station sets go into `FIXED` in `py/split_deep_subnetworks.py` (keyed by scenario and limit; `--no-fixed` gives the split as searched; a gravity join may not deepen a fixed outfall), run into `results/sc1_conditions/C#_limit_*pc_fewer_stations/`; the search reports in `results/sc1_conditions/reduce_*pc/REDUCE.md`.

| gradient limit | stations | new stations | manholes > 12 m | pipe > 12 m | above DN200 under 0.75 m/s at 2031 |
|---|---|---|---|---|---|
| 0.50 % | 25 -> **21** | O9-M773, O9-M166, O9-M101 (12.6 m) | 235 -> 321 | 21.5 -> 29.1 km | 26.4 of 151.7 km (17.4 %) |
| 0.75 % | 27 -> **23** | + O9-M72, O3-M1443 | 274 -> 360 | 24.5 -> 32.1 km | 9.2 of 151.4 km (6.1 %) |
| 1.00 % | 29 -> **25** | O9-M773, O9-M166, O9-M101, O9-M2805, O9-M69 (12.6 m), O3-M1434, O3-M1463 | 275 -> 364 | 24.6 -> 32.5 km | 2.9 of 151.3 km (1.9 %) |

- Outfalls kept deeper than 12 m: O9 14.25 m, O12 14.63 m (0.50 %) / 14.71 m (0.75 and 1.00 %: 8 cm over the limit, kept deep as he decided at 0.50 %), O11 12.39 m, O14 12.73 m; deepest manhole 16.5 / 16.2 / 16.2 m, unchanged.
- O3's stations (0.75 and 1.00 %) cannot be dropped or merged: without them O3 is 18-26 m deep. O9-M728 goes at every limit (O9 14.25 m), O9-M103 + O9-M89 merge at O9-M101 at every limit.
- The station choice does not move a gradient, so self-cleansing is that of the limit; with fewer stations 0.75 % needs 23 stations, the number of the design as laid, for 9.2 km under 0.75 m/s against 26.4 km at 0.50 %.
- Every split GeoPackage now has a `manholes` layer (label, ground, depth_design, depth_after); the QGIS project shows it with the engineer's style (`qgis/styles/manholes_depth.qml`: from 1:15,000, labels name and depth from 1:10,000). Maps: `results/sc1_conditions/maps/SC1_C#_*_fewer_stations.png`. The project file and the engineer's open QGIS agree (checked on the plugin socket, 2026-11-18); a second QGIS window holding the old project overwrote the rebuild once on save and was restored from git - after a script rebuild, reload the project in every open QGIS before saving.

## Expected difficulty with the design-year rule

In the W17 S1 run (2070 design), the share of pipes above DN200 reaching 0.75 m/s is 37 % at the 2070 flow, 16 % at the 2055 flow and 6 % at the 2030 flow (`D:/VBOX/bridge/out/scen/S1/conduits_S1-*.csv`). Table 11 gives 0.75 m/s only to a pipe running at least half full, so SC1 at 2056 is run first to measure the real pass rate before the other runs.

---

*Inherited from W17 (kept unchanged below):*

# W17 — the modeller's SewerGEMS model, driven through the API (opened 2026-10-01)

W17 works on the SewerGEMS model the modeller designed (`13 IBRI_29092026 12M`), not on the W15 engine.
SewerGEMS (CONNECT 10.4) runs in a VirtualBox Windows 10 guest with **no network adapter but an internal one,
no gateway and no internet**; nothing here changes that. The link is a file drop: `sewergems_api/watcher.ps1`
runs in a PowerShell window inside the guest and executes every script dropped into the shared folder
`D:\VBOX\bridge\jobs`, writing the output to `D:\VBOX\bridge\out`. The scripts load the OpenFlows and Haestad
libraries that ship with SewerGEMS; nothing is installed or downloaded. `compile_check.ps1` compiles the C#
helpers on the host against copies of those libraries before a job is sent.

## Where the model is

| Copy | Path | State |
|---|---|---|
| Modeller's original | `Desktop\Win10 shared folder\IBRI Sewer\13 IBRI_29092026 12M(7.12 PM )\` and `Hydraulic\Model\temp\…` | untouched |
| W17 R0 (housekeeping) | `Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\IBRI_W17_R0.stsw` | superseded, kept as the record |
| W17 R1 (physical flattened) | `…\14 IBRI_W17\IBRI_W17_R1.stsw` | superseded by R2, kept as the record |
| W17 R2 (loads peaked) | `…\14 IBRI_W17\IBRI_W17_R2.stsw` | superseded by R3, kept as the record |
| W17 R3 (one load per manhole) | `…\14 IBRI_W17\IBRI_W17_R3.stsw` | superseded; **the shared-folder copy was saved again from SewerGEMS at 10:18 before the engineer's Save As, so the R3 record is the guest copy `C:\IbriWork\W17\IBRI_W17_R3.stsw`** |
| R4_loads (engineer's LoadBuilder reload) | `…\14 IBRI_W17\IBRI_W17_R4_loads.stsw` | the engineer's input to R4, kept |
| W17 R4 (years reloaded) | `…\14 IBRI_W17\IBRI_W17_R4.stsw` | the loads every option builds on |
| W17 R5, R6 (first S1 builds) | `…\14 IBRI_W17\IBRI_W17_R5/R6.stsw` | **DO NOT USE** — see the section below |
| W17 R7 (option S1, Manning) | `…\14 IBRI_W17\IBRI_W17_R7.stsw` | superseded by R9: designed with Manning's n (0.013 catalogue), before the friction decision |
| W17 R8 (Colebrook-White) | guest only, `C:\IbriWork\W17\IBRI_W17_R8.stsw` | R4 with the gravity friction switched to Colebrook-White, ks 1.5 mm |
| **W17 R9 (options S1–S7)** | `…\14 IBRI_W17\IBRI_W17_R9.stsw` (also in `Options 2026-10/12_SewerGEMS/`) | **live**: all seven options on Colebrook-White, delivered 2026-10-01 17:44 |

Each revision is a new file, so the engineer can keep an older one open in SewerGEMS while the next is built: the
scripts work on copies inside the guest (`C:\IbriWork\W17`) and only add new files to the shared folder.

The model files are not in git (300 MB). `data/` holds the renaming maps, the before/after inventories and the log.

## R0 — housekeeping (2026-10-01), as instructed by the engineer

- Calculation options "Base Calculation Options" → **DESIGN** (calculation type design); ANALYSIS kept.
- Physical "Physical Alternative - F" → **2070**. It still inherits through the chain of 32 "Property Inference"
  physical alternatives, so those alternatives are kept; their 33 scenarios are deleted.
- Sanitary "Base Sanitary Loading" (the 2070 loads) → **2070**; the empty, unused alternative already called 2070 deleted.
- Scenario "Scenario - 34" → **2070**.
- System flows dropped: the six year alternatives deleted, the 19 known flows of the base alternative cleared.
- The inactive test pump station (W-2, PMP-1, J-1, J-2, P-1…P-4) deleted.
- **Outfalls renamed O1…O24** in the engineer's order (O-1 first; towards O-4; towards O-19; south from O-8;
  west from O-6). The three deactivated outfalls keep O-56, O-67, O-78.
- **Manholes `O#-M#`, pipes `O#-P#`**: each subnetwork's trunk first (at every junction the branch with more
  manholes upstream), then each branch in full, downstream branch first; a pipe takes its upstream manhole's number.
  All 24 subnetworks are trees (no loops), so the numbering is unambiguous.
- **OLD_ID**: the 10.4 API refuses text user fields ("Invalid data FieldType"), so the old label is written into
  each element's native **Notes** as `OLD_ID=MH-18013` (38,593 elements), and `data/rename_*.csv` keeps the map.

| Old | New | Old | New | Old | New | Old | New |
|---|---|---|---|---|---|---|---|
| O-1 | O1 | O-20 | O5 | O-16 | O10 | O-8 | O16 |
| O-21 | O2 | O-13 | O6 | O-17 | O11 | O-23 | O17 |
| O-2 | O3 | O-4 | O7 | O-9 | O12 | O-24 | O18 |
| O-7 | O4 | O-10 | O8 | O-19 | O13 | O-11 | O19 |
| O-3 | O9 | O-12 | O14 | O-18 | O15 | O-22 | O20 |
| O-6 | O21 | O-14 | O22 | O-15 | O23 | O-5 | O24 |

## R1 — the 2070 design as the base physical alternative (2026-10-01)

The modeller's design ("F", renamed 2070 in R0) sat at the end of a chain of 32 inference alternatives. R1 merges it
down the chain into Base Physical (`Flatten.cs`: scenarios moved to the parent before each merge, one unused side
branch deleted first), names the base **2070** and adds seven empty children **S1-2070 … S7-2070**, one per STP
option, to hold each option's design. Check: every scalar physical field of every manhole, pipe and outfall read
before and after — **1,980,581 values, none of the design values changed**; the 1,520 that read differently are
unused fields (weir, cutoff, curve counts, surface storage) that were 0 and are now not stored, on 157 pipes and
132 manholes. Log: `data/r1_log.txt`.

## R2 — the plot loads peaked (2026-10-01, engineer's yes)

- The unit load "Unit Sanitary (Dry Weather) Loads - 1" (the one row of the Extreme Flow Setup) is now
  **"Plot average flow (1 m3/d per unit)"**, discharge-based, 1 m³/d per unit.
- Every pattern-load row in the six sanitary alternatives became a unit-load row with loading units = its flow in
  m³/d (2070: 18,002 rows; 2030–2060: 16,980–16,994). Totals read back identical to the m³/d.
- **Check** (scratch copy, 2030 and 2070 run as ANALYSIS): the outfall flow equals PF × base + infiltration
  (PF from "Peltier100-Merriamck", linear between table rows, on the pipe's cumulative upstream unit load;
  infiltration 720 L/day/km) to **0.0 % at 19 of 24 outfalls**; the 5 others (O3, O10, O11, O15, O20) have two
  incoming pipes, each peaked on its own flow. `data/r2/peak_check_r2.txt`.
- **Transfer** as a pattern load: +100 L/s at O13-M1 gives +100.000 L/s at O13 and no change anywhere else — not
  re-peaked, and it does not change the peaking of the receiving network's own loads.
- The peaking table "Peltier100-Merriamck" is Peltier to 1 L/s and Merrimack from the next row (1.5 L/s); between
  1 and 1.5 L/s SewerGEMS interpolates (2.50 → 3.39). Kept as the modeller set it (engineer, 2026-10-01).

## R3 — one sanitary load per manhole; a hard Peltier/Merrimack step (2026-10-01, engineer's decision)

- **Each manhole carries one sanitary load** (engineer: only a manhole receiving an upstream outfall carries a second,
  the transfer). The 2–4 rows on 2,023 manholes are summed into one row in all six years, totals unchanged to the m³/d
  (2070: 2,224 rows removed; 2030–2060: 2,043–2,056).
- "Peltier100-Merriamck" gets a row **1.001 L/s → 3.56** (Merrimack at 1 L/s), so the switch is a step at 1 L/s instead
  of a ramp to 1.5 L/s. Only outfalls in that band moved: 2030 O14 4.69→4.94, O15 3.31→4.33, O19 4.23→4.68 L/s;
  2070 O23 4.91→5.05 L/s.
- *Correction (R4):* the extra rows are **not** from *Append* runs, as first written here — a single fresh LoadBuilder run with *Override* writes the same 2–4 rows on 2,022 manholes. LoadBuilder splits them itself; the merge after every reload is the fix.

## The year loads are short (found 2026-10-01, not yet corrected)

2070 carries the plot layer's saturation flow (60,355 against 60,099 m³/d, +0.4 %, and every subnetwork within
noise), but **the five year alternatives are 7–10 % below the plot layer**: 2030 21,789 against 24,216; 2040 28,160
against 30,938; 2050 34,675 against 37,814; 2055 38,904 against 42,266; 2060 44,034 against 47,523 m³/d. The
shortfall sits in almost every subnetwork (O3 the largest, 830–990 m³/d) and in no single plot status or use, so the
year loads were most likely built from another version of the plot layer or another LoadBuilder setup than 2070.
Nearest-manhole re-assignment and the breakdown: `py/loads_vs_plots.py`, `data/loads_vs_plots.txt`.
Several rows on one manhole (2,023 manholes, up to 4 rows) are separate plot batches, not duplicates.
About 86–118 m³/d sits on the inactive manholes of the three deactivated subnetworks (the absorption-well areas).

## What the tests found (scratch copies, nothing saved)

1. **The plot loads are not peaked.** All 16,980 rows (2030) are *pattern loads*; the Extreme Flow Setup has one row,
   for the unit load "Unit Sanitary (Dry Weather) Loads - 1", so it never touches them. The 2030 run gives O1
   50.7 L/s for 49.0 L/s of base; the 1.7 L/s difference is the 720 L/day/km infiltration. The plot flows are
   average flows (`W14/docs/DESIGN_FLOWS_FOR_NETWORK.md`), so **the network is analysed and designed near average flow**.
2. **The fix is proven:** converted to unit loads (load definition 1, unit load 1 per unit, units = the plot flow),
   O12 gives 10.95 L/s for 3.42 L/s of base — the Merrimack hand figure (PF 3.07) plus infiltration.
   The model's curve "Peltier100-Merriamck" switches from Peltier to Merrimack at 1.5 L/s of flow; the guideline
   switches at 100 properties (G1-p71, p72) — about 1 L/s here, to be confirmed.
3. **Transfers:** a pattern load and a fixed inflow each add exactly what is put in (+100 L/s in, +100 L/s out) and
   add to, not override, the loads already at the manhole. With the plot loads as unit loads, a transfer entered as
   a pattern load is **not peaked again**, so the engineer's method (outfall peak flow → pattern load on the
   receiving manhole) works, upstream subnetworks first.
4. In the units: stored flows are cfs; the typed API returns the display unit, m³/d.

## Decided by the engineer (2026-10-01)

- O-21 (now O2) drains to **MH-8112** (O1 subnetwork; OLD_ID in Notes).
- Transfers in the analysis years use **each year's own upstream peak**, so every year runs upstream first.

**Tested 2026-10-01 — not the deactivated areas.** Plots whose nearest manhole is one of the 197 inactive ones carry
539–719 m³/d (2030–2060), a fifth of the gap, and the inactive manholes do carry loads in every year. At 783 manholes
the 2030 gap is exactly one plot: those plots are 4.3 km (median) from any inactive manhole, in every settlement, 548
of them existing plots (mostly residential, agricultural, commercial). `py/year_gap_check.py`, `data/year_gap_check.txt`.

## R4 — the year loads reloaded by the engineer (2026-10-01)

The engineer re-ran LoadBuilder for all six sanitary alternatives from the current `Plots.shp` (`Q_2030` … `Q_2060`,
`Q_SAT`) with *Override* and saved `IBRI_W17_R4_loads.stsw`. *Override* replaces loads only on the manholes it writes to:
**70 old 2070 rows (259.4 m³/d, 162 of it on 11 manholes of O12) survived on manholes the new run did not load** — the
same +256 m³/d the old 2070 carried over the plot layer. They were removed, then the loads converted to the peaked unit
load and merged to one row per manhole. **Every year now equals the plot layer to the decimal**: 2030 24,216.31; 2040
30,938.43; 2050 37,814.53; 2055 42,265.79; 2060 47,523.06; 2070 60,098.79 m³/d, on 15,708–15,711 manholes. The full plot
layer is loaded, so plots in unpiped land and the military area are carried at their nearest manhole in every year.
Peak outfall flow, sum of the 24 outfalls: 2030 613.9 → 674.0 L/s; 2070 1,541.5 → 1,535.2 L/s. `data/r4/`.

## 2026-10-02 — the report reviewed, the recommendation, the BOQ workbook and the deck

- **Report build R5** (`report/R5/Ibri_Concept_Design_Report_R4.docx` + `.pdf`, 159 pages): `build.py` has `REV = "R5"`
  (the folder) and `DOC_REV = "R4"` (what the cover, footers and file name print); the engineer: none of the revisions is
  issued, R5 is internal and never appears in the report. Read end to end against itself; fixed: the plant flow tied
  through (Table 1, 4.2.8, 4.4, 6.2.7, 8.4: 60,099 from the plots, 60,456 at the plants, 66,502 with the margin), the
  structure (1.1, 1.1.2, 8.5 with Appendix B, Chapter 6 intro, 6.1.1, 6.1.2, 6.2.1, 6.2.4, 6.3, 6.5.1), footnotes without
  "Revision 1" or "test area", the 12 m cover sentence removed from 6.2.7 (engineer: state how many and how deep only),
  6.2.8's flows stated (model flows, all connected, infiltration in), Decision 7 pointing to 6.2.8, G203 p50's 30 min in
  Table 45, Appendix B's lengths from the unrounded pipes (one total, 1,498,295 m, in every option).
- **Plant-inlet lift** (`report/facts_w17.inlet_lift`): depth of the arriving sewer + 1.5 m wet well + 3 m, 65 %, the
  stations' own values. 2070: 1,172–1,371 MWh/yr, S1's equal to its 23 stations; the order of the options is unchanged.
  Table 44 and chart W05 in 6.2.7; chart W06 (the options side by side) in the executive summary.
- **Recommendation** (`facts_w17.RECOMMENDED`, the engineer's priority 2026-10-02): **S1, S4, S6**, one of each character;
  S2 not recommended (+57 % energy on S1); S3, S5, S7 between. In the executive summary, 7.11, 8.4 and 8.4.1, 6.1.1, 6.4
  and the deliverables register. The TE network is designed on the three.
- **BOQ workbook** `Options 2026-10/BOQ/Ibri_Sewer_Options_BOQ_Quantities.xlsx` (`py/boq_workbook.py`): Read me, Summary,
  A sewers by OD and depth (0.5 m bands to 4 m, then 1 m), B manholes by the largest pipe and depth (model rim − invert,
  not the GeoPackage's 0.01 m rounding, which moves the minimum-cover manholes across 1.5 m), C pumping stations (G203
  Table 17 type and pumps, Table 21 land), D rising mains, E plants. Checked against the report: 1,498,295 m, 19,083
  manholes, the same bands. Excluded until the survey: house connections, crossings, excavation volumes, reinstatement.
- **Deck** `Options 2026-10/Presentation/Ibri_Concept_Design_Presentation_2026-10.pptx` (`presentation/build_deck_w17.py`,
  51 slides): the engineer's deck "- 2-1" (WeTransfer, 2026-10-02; byte-identical to his Downloads copy of 16 September)
  with only the cover's title, date and revision changed; section 03 (the model, the flow to the plants, the seven options
  with diagram and map each, depth, the options side by side, energy, two matters, self-cleansing, the recommendation)
  cloned from his own slides; placeholders 04 TE network and 05 Cost analysis. The bottom strip of all 44 content
  slides and the cover's row of icons show the five sections (01 Progress, 02 Design basis, 03 Sewer network, 04 TE
  network, 05 Cost analysis), the slide's own lit; his topic detail stays in the top-left tab (engineer's option A,
  `section_strip`, `cover_row`; the cost icon is a banknote drawn on the Tabler grid). **PowerPoint pitfall:** opening, SaveAs,
  editing and saving again re-reads his pictures lazily by their old part names and swaps maps for logos and icons; copy
  the file, open it, edit, save once (tested clean). His slides 2–22 compared pixel by pixel with the base render.
- Open for the engineer: the GeoPackages in `11_Network_options` still carry an `old_id` field with the modeller's labels.

## 2026-10-12 — own flow of the 24 subnetworks at every five years

- **`results/subnetwork_flows_by_year.xlsx`** (`py/subnetwork_flows.py`), asked for by the team: sheet *Flow m3d* = each subnetwork's own average dry-weather flow at 2024, 2025, 2030 … 2065 and 2070 (saturation), no transfer from upstream subnetworks, no peaking, so the same for every option; sewer length and infiltration (720 L/d/km, G201 p72) as separate columns; sheet *Population* the same grouping in people.
- **Source and check:** the model's plot layer (`14 IBRI_W17/SHP/Plots/Plots.shp` on the model share) carries `Q_2024 … Q_2065`, `Q_SAT`, the population columns and `HMINNODE`, the id of the manhole each plot loads; the node inventory (`bridge/out/inv_w17/nodes.csv`) maps the id to the label and the label to O1–O24. The sums equal the model's sanitary loads (`bridge/out/r4/diag/rows_<year>.csv`) to 0.01 m³/d in every subnetwork and year the model runs, asserted on every build. 7,318 plots load inactive manholes (the three deactivated absorption-well areas): one row "outside the 24", 539 m³/d in 2030 to 722 in 2070, so the total is the report's 60,099.

## 2026-10-04 — report build R7, final for issue

- **Live: `report/R7/Ibri_Concept_Design_Report_R7.docx` + `.pdf`** (174 pages), copied to `Options 2026-10/Reports/`.
- **Cost:** the team's estimate `data/finance/2621 - Options Cost Estimation.xlsx` (copied read-only from the server's `06-WORKING/04-Hydraulic/11-Finacial`), read by `report/facts_cost.py` with its parts checked against its totals. CAPEX by element (sewers by OD and depth band, manholes, stations per kW, rising mains, plants per m³/d by band); OPEX year 1 = maintenance 1 % of CAPEX + installed power 24 h at 0.02 OMR/kWh + land 1 OMR/m²/month + staff 2,500 OMR × 13; escalated 5 %/yr; discounted at 5 % over 25 years, so whole-life = CAPEX + 25 × OPEX1. Section 7.8 rebuilt on it, chart `W08_costs`; constant-price check (factor 14.8) keeps the order.
- **Recommendation (engineer, 2026-10-04): S1, S3, S7.** S1 lowest (232.5 M OMR); S3 +3.8 %, S2 +5.4 %, S7 +5.6 % within 10 %; S2 set aside (+57 % energy); S3/S7 save 1–2 % of system energy, equal on cost and sustainability within ±20 %; S1 first on operability. `facts_w17.RECOMMENDED`; `rpt_options` (`_why`, `recommendation`, `appraisal`, `conclusions`, `recommendations`, `summary_block`) rewritten; characters at the preliminary design; the TE network not linked to the options.
- **Existing networks:** designed as if unsewered; existing lifting station and STP not credited; `py/existing_overlap.py` → `results/existing_overlap.json`: 63.9 km of new sewer within 15 m of an existing one.
- **Context from the server (read-only):** NWS's comments of 24 Sept on the Design Basis Report (quality, criteria justification, 2024 base year, no consultant recommendation, coverage of Al Aqariyah, As Subaykhi, Madayn); the TE stakeholder meeting of 23 Sept (minutes, customer data); MoHUP planning maps (4 Oct); NWS GIS specifications; wellfield protection zones. The 2024 base year is justified in 4.1.1; coverage stays out of the report (managers); the horizon stays open (engineer).
- **Also new:** risk register (7.9), roadmap (8.1), packaging (8.2), phasing table (6.5.1), sludge quantities (6.7), TE customers table (4.4), three data requests, register rows, Appendix C (`rpt_appcd.py`, from the W13 criteria document's guideline columns) and D (drawings), `doc.wide_figures(last=True)` so the report ends on its last drawing, D5 and appraisal flowcharts redrawn (`py/make_appraisal_figure.py`).
- **Deliverable folder:** `Options 2026-10/Cost/` holds the cost estimate the report's Section 7.8 is built on.
- **Deck:** recommendation slide for S1, S3, S7; 04 TE (customers, the TE availability chart) and 05 cost (table and chart) filled; his slides unchanged.

## 2026-10-03 — report build R6 on the engineer's comments, manholes in QGIS

- **Live: `report/R6/Ibri_Concept_Design_Report_R6.docx` + `.pdf`** (162 pages; copied to `Options 2026-10/Reports/`,
  replacing the R4-named copies of the R5 build, which stay in `report/R5/`). `build.py`: `REV = "R6"` names the folder
  and the file only; **the document prints no revision anywhere** (engineer: none has been issued; a client-commented
  issue would be the first to carry one). His 35 Word comments are in his copy
  `Options 2026-10/Reports/Ibri_Concept_Design_Report_R4 - Copy.docx` (not touched; he will comment the rest).
- **Front matter:** `rpt_front.project_control` (document control: project, client, tender, contract, consultant,
  document, date; prepared / checked / approved with the names, signatures and dates blank); the abbreviations table
  checked against every token the built document uses (S1–S7, O1–O24 and the station names, H1–H6, NWS, MAFWR, CRT, MD,
  MOD, NPV, OMR, EPSG, ISO, BS EN, PAM-GUD, units).
- **Headings:** `report/headings.py` maps every chapter, section, summary title and minor heading to an official title
  (the client's comment on the Design Basis Report); `doc.h`, `doc.chapter`, `doc.title` and `doc.sub` pass every title
  through `official()`, so the modules keep their own wording and the table is the before/after list for review.
  **Justify Low** on every body paragraph, list and box (`doc.BODY_ALIGN`).
- **Decisions:** `report/basis_items.py` builds this report's register from W16's `decisions.py` without touching it:
  "Persons per property" → **Occupancy rate**, "The growth beyond 2050" → **Growth rate beyond 2050**, "Use of each plot"
  → the adopted **Land-use layer** (after the 126 meters). **6 decisions, 9 adopted values**; `ask()`/`adopt()` keep the
  basis report's numbers in the chapter modules and print this report's; `number(title)` writes "Decision N" in the text.
- **Executive summary:** the 16 September sentence and "this revision" gone; the existing networks are not relied on
  (the network carries all sewage to the plants; the existing system is assessed once the as-built survey lands, also in
  5.1.2); tankered sewage from outside the study area requested so the plant is designed for it (also 6.6.1); "4" for
  the floor; the empty-land sentence and the 722 m³/d not-carried sentence removed; Table 1 at 2024, 2030, 2040, 2050,
  2055, 2060, 2070; "State of the work" removed; Deliverables points to 1.3.1.
- **Chapter 1:** the programme paragraph and its 1.5.4 row removed; 1.3.1 maps each deliverable to its section
  (`report/deliverables.py`), the position chart R08 withdrawn (`charts_r3.py`); the meeting outcome reads "Progress
  reported; the Design Basis Report presented"; the wadi sentence of 1.2.7 removed. Every "next revision" and every
  pending line removed (5, 6.4, 6.5, 6.7, 7.1, 7.3, 7.4, 7.8, 7.11, 8.1, 8.4, 8.5): the team completes the report before
  submission.
- **The recommendation** (engineer's comment, 2026-10-03): the characters are not tied to an option. S1, S4 and S6 are
  selected because they span one, three and six plants; each is designed and costed under the three characters on the
  same network model, changing process, energy with solar, reuse and materials: **nine costed cases**, the 10 % rule
  between cases. `facts_w17.CHARACTERS` replaces the old one-per-option map; 6.1.1, 6.1.2 (the "Network" row dropped from
  the approach table), 6.1.4, 7.11 (no Character row), 8.4, 8.4.1 and the summary rewritten; figures D5 (options
  development, `make_report_figures.d5_options`) and the appraisal method (`py/make_appraisal_figure.py`, carried from
  W16) redrawn; "760 m from the existing STP" and "near the existing STP" removed everywhere; S1 adds 2055 (42,635 m³/d).
- **7.2 flood exposure** (`py/flood_exposure.py` → `results/flood_exposure.json`, chart `W07_flood`): the pipes and
  manholes are the same in all seven options (checked), sampled every metre and at each manhole on the MAFWR grids; the
  whole network lies inside the mapped basin, so no data means not flooded. In H4–H6: pipes 23.9 / 47.2 / 85.8 /
  150.8 km = 1.6 / 3.1 / 5.7 / **10.1 %** of 1,498 km; manholes 305 / 580 / 1,037 / 1,839 = 1.6 / 3.0 / 5.4 / **9.6 %**
  of 19,083 for the 10 / 25 / 50 / 100-year floods. H4–H6 as the washout ground is this design's measure (G203 p30 sets
  none), to be confirmed by a scour check. Plants, stations and rising mains are assessed once sited.
- **Deck and BOQ:** the cover's "Revision 4" now reads "Concept Design Report"; "760 m" removed; the recommendation
  slide shows one / three / six plants instead of a character and states the nine cases; the BOQ's Read me likewise.
  His slides 2–22 compared with the base render, unchanged.
- **QGIS:** `gis/make_w17_project.py --no-render` adds a styled, labelled `Manholes` layer to each of the seven option
  groups (depth bands, visible from 1:25,000, labels from 1:5,000), no layout changed and no PNG re-exported.

## R9 — the seven options on Colebrook-White (done 2026-10-01, 17:45)

Job `055_make_R9_all_options.ps1` built S1–S7 in one file from R8, ~44 min an option at Colebrook speed, and delivered
`IBRI_W17_R9.stsw` to the shared folder (exit 0); `py/process_options.py` followed it and processed each option as its
last run was exported. **Every option:** the design converged in four passes; the 2070 analysis and every year kept
the 2070 sizes and inverts (guard, both in the VM and on the host); no pipe over 3.0 m/s or the d/D limit in any year;
the flow check 0.0000 %. Side by side (`results/options_comparison.md`, the workbook in the deliverable folder):

| Option | STPs | Sewer at the STPs, m deep | Stations | kW | MWh/yr 2030 / 2070 | Rising mains km |
|---|---|---|---|---|---|---|
| S1 | O1 | 10.3 | 23 | 422 | 465 / 1,367 | 43.9 |
| S2 | O16 | 5.9 | 23 | 884 | 1,311 / 3,337 | 37.3 |
| S3 | O1, O4 | 10.1 / 6.9 | 22 | 361 | 367 / 1,148 | 43.2 |
| S4 | O1, O4, O9 | 10.0 / 6.9 / 8.8 | 21 | 319 | 339 / 974 | 43.0 |
| S5 | O1, O3, O4, O9 | 9.8 / 5.8 / 6.9 / 8.8 | 20 | 277 | 259 / 797 | 43.0 |
| S6 | O1, O3, O4, O9, O16, O22 | 9.8 / 5.8 / 6.9 / 8.8 / 4.9 / 1.5 | 18 | 198 | 220 / 616 | 28.7 |
| S7 | O1, O16, O22 | 10.3 / 4.9 / 1.5 | 21 | 343 | 426 / 1,186 | 29.5 |

- **Depth does not separate the options:** 40 manholes over 12 m, 3.2 km of sewer over 12 m and the deepest manhole at
  15.0–15.1 m (O21-M21) in every option; the deep sewers are set by the ground inside the subnetworks.
- **S2 doubles the pumping** (884 kW): all of O1's 1,450 L/s is pumped 3.0 km to O16 (DN1200, 24 m).
- **O23** lifts 5 L/s against 220–300 m of head in every option (9.5 km to O21, or to the O22 plant in S6/S7) —
  to be reconsidered; **retention** over 30 min in 2030 at 10–14 stations, up to 73 h (O18 to the plant).
- **S1 (first, 13:25):** plant O1 24,756 → 60,456 m³/d, peak 674 → 1,535 L/s. `results/S#/` for every option.
- **d/D is compared at three decimals**, the design's own precision: O2-P203 sat at 0.65006 against 0.65 (0.06 mm).
- **8,712 of 19,083 pipes are drawn against the flow** (start node downstream). By the tree none falls the wrong way;
  the exported gradient is now absolute, the GeoPackage swaps their end depths, and the self-cleansing scripts take the
  upstream end from the inverts. The self-cleansing year table did not change (29 % in 2030, 46 % in 2070).
- **Outputs:**
  - **Concept Design Report R4**, `report/R4/` (153 pages): R3 + 6.2.5–6.2.8 and Appendix B from
    `report/facts_w17.py`, executive summary and deliverables updated. **Client register (engineer, 2026-10-01): current
    names only (O1–O24, never the modeller's O-#), no file, field, sheet or folder names, no internal steps** — nine R3
    footnotes reworded; the depth of the sewer arriving at each STP given everywhere.
  - **Transfer diagrams** drawn locally by `py/diagram_png.py` (approved by the engineer) from `py/diagram_layout.py`;
    the Figma code (`diagram_js.py`, file `rm7tdwnSGW5HefJlXQPWDW`) is current but unused — the Starter plan's MCP
    limit blocks it; the `EXPORT2X …` frames left on that canvas carry old names and can be deleted.
  - **Maps** (`gis/make_w17_project.py`, engineer's notes 2026-10-01): one overview of the 24 subnetworks and three per
    option (zones, network, depth), Google satellite at 50 % (rendered per map: the standalone exporter crashes on web
    tiles), legend bottom-left kept clear of the network, labels "O21 8.3m 4,519 m3/d / PMP 15m 126L/s".
  - **Deliverable folder** `Options 2026-10/` (not in git): QGIS project (86 layers, 22 layouts), GeoPackages on the
    true pipe geometry (job 056), maps, `W17_network_options_tables.xlsx`, R4, the R9 model; the downloaded Esri
    mosaic removed.
- **Report build trap, fixed:** `W16/report_basis/facts_basis.py` puts `W16/report` at the head of the import path, so
  every chapter imported after it came from R3; `build.py` and `charts_r3.py` now put `W17/report` back in front.

## R8 — Colebrook-White friction (engineer's decision, 2026-10-01)

G203 p24 and p28: *"Gravity sewerage systems shall be designed by using the recognised hydraulic formulas such as
Colebrook-White, or Manning's Formula"* and *"Colebrook-White ... shall be designed using a ks value of 1.5 mm for all pipe
sizes and materials"*; p25 Table 9: viscosity 1.141 × 10⁻⁶ m²/s at 15 °C, *"the conservative value of 15°C should be used"*;
p23 Table 8 gives typical Manning's n by material (plastic 0.009, PVC 0.009–0.011, PE 0.009–0.015). **Table 11 (p29) is
Colebrook-White at ks 1.5 mm**: every row gives 0.74–0.76 m/s full bore at 15 °C (`py` check in the session; Manning
equivalent n 0.0128–0.0133). The client asked for Colebrook-White. R8 = R4 with *Gravity Friction Method* = Darcy-Weisbach,
*Friction Factor Method* = Colebrook-White, viscosity 1.141 × 10⁻⁶ m²/s on both calculation options, e = 1.5 mm on all
19,286 conduits and every catalogue size (catalogue Manning's n left at 0.010, unused). Flows unchanged; velocities a
median 13 % lower than with the old Manning roughness (2030, modeller's pipes). A Colebrook run takes ~8 times longer.

## Self-cleansing — for information (the audit waits for the client's decision)

`results/S1/selfcleansing_info.md` (S1, R7 flows; required gradients by Colebrook-White ks 1.5 mm): **no year has every
pipe at 0.75 m/s at its peak** — 1.0 % of pipes in 2030, 5.8 % in 2070; 1 to 5 of 3,612 head pipes. The median gradient
a head pipe would need is 35 % (2030) / 19 % (2070); 1 % of head pipes could do it within the client's 4 %. A DN200 needs
**0.93 L/s** of peak flow to reach 0.75 m/s at 4 %. The tractive gradient at 1 Pa (Mara, G203 p27) is a median 2.5 % (2030)
/ 1.3 % (2070) for head pipes; it passes 4 % only below 0.0135 L/s (1,272 head pipes in 2030, 372 in 2070 — pipes carrying
little more than their infiltration).

## R7 — option S1, centralised STP at O-1 (2026-10-01)

- **Structure** (the same for every option): sanitary children `S1-2030` … `S1-2070` under the shared year
  alternatives, holding only the transfer rows (pattern loads, 120 rows = 20 transfers × 6 years); physical `S1-2070`
  (child of the modeller's 2070); scenarios `S1-2070` (DESIGN), `S1-2070A` (the same 2070 run as an analysis, the
  check on the design), `S1-2030` … `S1-2060` (ANALYSIS, own year's transfers) — every alternative and calculation
  option set local. Catalogue Manning's n set to 0.013 (the modeller's value on 18,750 pipes; the catalogue had 0.010).
- **Transfers** = each outfall's own peak + everything transferred into its subnetwork (additive, tested), upstream
  first, per year: `py/routing.py` (S1–S7 routing), `py/make_transfers.py`. Flow check: SewerGEMS outfall flows equal
  the computed transfers to 0.0000 %.
- **Design** converged in four passes (2,627, 1,538, 210, 0 sizes changed). 2070 analysis and every year: **no pipe over
  3.0 m/s, none over the d/D limit**; 42 pipes break the 12 m cover limit; **40 manholes deeper than 12 m** (modeller's
  design: 260), deepest 15.10 m (O21-M21). 1,498 km of pipe; length by size and depth band in`results/S1/S1_summary.md`.
- **Plant O1:** 24,756 m³/d (2030) → 60,456 m³/d (2070) average with infiltration; peak 674 → 1,535 L/s.
- **Pumping:** 23 stations, 431 kW duty, 0.48 GWh/yr (2030), 1.39 GWh/yr (2070) — with the assumptions tagged in the
  table (straight-line main × 1.25, C = 120, efficiency 0.65). Long small mains (O-23, O-24 to the plant 7–9 km; O-15
  to MH-18772 9.2 km lifting 45 m) give 2–3 days' retention in 2030: H2S risk (G203 §7.7), to be weighed in the appraisal.
- **Not yet run:** the self-cleansing audit on 2030 × 0.61 with no infiltration (project rule); 17,977 of 19,083 pipes
  are below 0.75 m/s at their 2070 peak — mostly DN200 heads, where G203 lets tractive force govern.

## R5, R6 — first S1 builds: DO NOT USE (2026-10-01)

Both are kept only as the record of a fault. The year scenarios S1-2030 … S1-2060 were created with calculation
options equal to their parent's, so they stayed **inherited**; switching S1-2070 to DESIGN made every year run a
design too, each re-sizing the shared S1 pipes for its own year (O9-P715: 450 mm after 2030, 560 mm after 2060, 900 mm
after the 2070 design). The pipes saved in R5 and R6 are therefore a 2060 design. Also found on the way: the typed
API's diameter field is stale for catalogue pipes (the size reference holds the real size), and one design pass is
not converged (R6: 1,429, 545, 49, 0 sizes changed over four passes). Fixed in R7: scenario alternatives and
calculation options are set *local* explicitly, exports read the catalogue size, the design repeats until no size
changes, and the job fails if an analysis run changes any pipe size.

## Open

- Confirm that the plots in unpiped land are meant to be carried at their nearest manhole (the reload loads the whole layer).
