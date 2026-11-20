# Toolkit: how the W18 final design deliverables were produced (R10 to R12, 2026-11-18/20)

An inventory of every technique, tool and script used to take the final design from model results to an issued package, written
as the raw material for a reusable skill. Paths are relative to `Hydraulic/Claude/W18 NWS scenarios 2056-2071/` unless stated.

## 1. What came out

| Deliverable | Made by |
|---|---|
| Concept design report, Word and PDF, 240 pages, on the team's own Word file (R8-MH) | `report_final/build_report.py` + `r10_edits.py` + `r11_edits.py`, finished by `word_finish.py` |
| Excel workbook of the report's tables and charts, live formulas, charts built in Excel | `report_final/report_workbook.py` |
| Treatment, TE and financial workbook (team's cost method), all 12 designs | `py/final_financial.py` |
| People and flow at every pumping and lift station, 2026-2061 | `py/final_station_flows.py` |
| Report maps (A3, QGIS layouts) and the QGIS project | `gis/final_maps.py`, `gis/team_maps_redraw.py`, `gis/te_map_sc4.py` |
| Flow schematics, one per scenario and design year (R7 style) | `report_final/flow_diagram.py` driving `py/diagram_png.py` |
| DWG drawings, one per scenario, annotated for zoom-out and zoom-in | `py/final_dwg.py` |
| The 12 designs: design, split, self-cleansing check, naming, products, repeated until the lifts settle | `py/final_run_all.py` (runs `final_design.py`, `split_deep_subnetworks.py`, `final_selfcleansing.py`, `final_naming.py`, `final_products.py`) |
| Bill of quantities and network capital cost (`network_cost.json`) | `py/final_boq.py` |
| 2051/2061 designs at the 2056 peak (`design_year_check_2056.json`) | `py/design_year_check.py` (rebuilt 2026-11-20; reproduces the report's figures exactly) |
| SC4 TE network from the team's SC2 and SC3 models | `py/te_sc4_network.py` (rebuilt 2026-11-20; reproduces the stored network pipe for pipe) |
| SewerGEMS models of the 12 designs (referee runs) and the comparison | `py/final_sg_inputs.py`, `py/final_sg_compare.py`, `sewergems_api/` (VM file-drop bridge) |
| Drops-over-2-m study | `studies/drops over 2 m/drops_engine.py` |
| Package zip, server copy, WhatsApp delivery | `py/package_final.py`, `C:\Users\mojtaba\wa_link\wa.js` |

## 2. Tools

- **Python:**
  - python-docx and lxml, to edit the Word XML directly;
  - PyMuPDF (`fitz`), to read and render the PDF;
  - Pillow, for contact sheets and image sizes;
  - pandas, geopandas and fiona, for results and GIS layers;
  - openpyxl, for workbooks with formulas;
  - matplotlib, for the diagrams;
  - ezdxf, for DXF;
  - olefile, to read Outlook `.msg` files.
- **pywin32 COM (always `DispatchEx`, hidden, never the user's own window):**
  - Word: fields, tables of contents and figures, save, PDF;
  - Excel: native charts exported to PNG.
- **QGIS 3.44 standalone:** `& "C:\Program Files\QGIS 3.44.8\bin\python-qgis-ltr.bat" script.py`. It renders saved layout clones without the GUI.
- **AutoCAD 2026 `accoreconsole.exe`:** `/i file.dxf /s script.scr` with `_.SAVEAS 2018 "out.dwg"`. Real DWG, no window, about 10 s per drawing.
- **SewerGEMS 10.4 in the offline VM:** a job dropped in `D:\VBOX\bridge\jobs`, results read from `out\`. See the global CLAUDE.md.
- **Delivery:**
  - WhatsApp: `node wa.js send me <file> <caption>`, where `status: 2` means acknowledged;
  - SendUserFile, into the chat;
  - unzip to the W: temp folder (`N <package name>`).
- **Harness:**
  - background Bash and Monitor (until-loops) for runs longer than 10 minutes;
  - computer-use only to read a blocking Word dialog;
  - the `update_plan` / `wrap_up` task list.

## 3. Report on a team's Word template (python-docx)

- **Build pattern:**
  - copy the team's document and edit it in place. Never retype their chapters.
  - one module per revision (`r10_edits`, `r11_edits`), each with an `apply(globals())` run after the main build. The `REV` constant picks the output folder; an issued revision's folder is never overwritten.
- **Inserting content:** an `Out` writer inserts before a given element, with:
  - `p`, `h(level)`, `table`, `caption`, `figure`;
  - `maps`: A3 landscape pages, sized by the image's aspect so the caption fits;
  - `sect`: a section break that reuses an empty previous paragraph.
- **Finders:**
  - Locate a paragraph by its text and style, skipping the TOC and table-of-figures styles. A TOC entry once matched a heading and destroyed the table of contents.
  - `section(head)` returns the elements under a heading; `take()` copies a team subsection to move it.
- **`set_text` / `sub`:** rewrite a paragraph and keep the first run's format, the footnote references and the bookmarks. `sub` asserts that each old string exists, so a silent no-op is impossible.
- **Numbers from one source:**
  - `facts_final.case(sc, year)`, `financial.json` and `design_year_check_2056.json`;
  - text figures are computed, never typed. For example, 6.2.2 reads the not-conveyed flow from the sentence of 7.3.1 that the reconciliation writes.
- **Captions:**
  - native SEQ fields;
  - the chapter part written as text (STYLEREF gave wrong chapter numbers);
  - all captions normalised to "Table 8-1. Title" in the caption style.
- **Cross-references:**
  - REF fields written as their current numbers (`literal_refs`, `number_map`); dead ones unlinked to text;
  - hand-typed "Section n.n" checked against the TOC: once for existence, once for topic (the target title printed next to the citing sentence).
- **Whole-report layout pass (`r11_edits`):**
  - **Tables:** centred, cells centred, header row repeated, rows kept whole, 8.5 pt from 7 columns.
  - **Column widths:** sized by content. Never below the longest word, never past the page width. Rotated header cells (`textDirection`) don't count. Tables with a picture are skipped.
  - **Chapters:** start with `page_break_before` on the heading, not a page-break paragraph.
  - **No blank pages:** delete empty paragraphs before a section break or page break, and make the section-break paragraph 1 pt.
  - **Figures:** centred and kept with the caption.
  - **Body text:** flush (the team's chapters had two indents).
  - **Sections:** only the cover keeps "different first page"; copied sections had inherited the cover's blank header.
  - **Wording:** one term everywhere ("property", never "dwelling"), enforced by the clean gate.

## 4. Word finishing by COM (`word_finish.py`)

- **Steps:**
  1. Open hidden.
  2. Turn background pagination off; `Repaginate` once.
  3. Update SEQ/STYLEREF fields, then TOC and TOF, twice.
  4. Unlink REF fields whose bookmark no longer exists.
  5. `SaveAs2` to `*_finished.docx`.
  6. Turn pagination back on.
  7. `ExportAsFixedFormat` to `*_export.pdf`.
  8. Swap both into place after Word quits.
- **Retries:** every Word call is retried 4 times, 15 s apart, on "Command failed".
- **Traps paid for:**
  - On a 160-190 MB report, Save and TOF Update fail with "Command failed" while Word is still laying out pages.
  - Export with pagination off writes nothing, without an error.
  - Export over the existing PDF once silently kept the old file.
  - A killed run leaves a hidden `/Automation -Embedding` Word and a `~$` lock file, and the next run hangs. Kill only automation instances (check the command line) and delete the lock.
  - After a failed run, Word puts a visible "it caused a serious error, still open it?" dialog on the second screen. Find it by listing the process windows (EnumWindows) or with a screenshot, and answer Yes.
  - `Move-Item -Force` onto a file Word still holds deletes the target and then fails.

## 5. Report QA (all scripted, plus eyes on the render)

- **Clean-room gate:**
  - `check_clean.py <pdf> --terms forbidden_terms.txt --allow allowed_terms.txt`; the term files are regexes.
  - Pass them with the flags: positional arguments were ignored, and the risk IDs R01-R16 then failed the gate.
- **Page scan (PyMuPDF):**
  - near-empty pages;
  - a figure caption at the top of a page with no image above it;
  - footer and header present on every page but the cover.
- **Reference checks:**
  - caption sequences unbroken;
  - every "Table/Figure x-y" cited exists;
  - every "Section n.n" exists and points at the right topic;
  - stale wording regexes: old option names, "Error!", TBD, superseded terms.
- **All of the above in one tool:** `report_final/qa_report.py <pdf> --docx <docx> [--topics] [--sheets DIR]`. It exits 1 on any failure; `--topics` lists every section reference with its target's title.
- **Visual pass:**
  - contact sheets of every page (40 per sheet, `qa_report.py --sheets`);
  - close renders of each changed page;
  - every map and chart PNG opened and looked at before it goes in.
- **Numbers:** check the executive summary and the conclusions against the data; assert the claims in code (for example "SC3 and SC1 are the two lowest in every design year").

## 6. Excel workbook with live formulas and Excel-built charts (`report_workbook.py`)

- **Sheets (openpyxl):**
  - one sheet per report table, plus a Contents sheet with hyperlinks;
  - derived cells written as formulas (`"=D{r}-E{r}"`, `SUM`);
  - no stray cells: as a person would lay it out for an old-school client.
- **Charts (Excel COM):**
  - `Shapes.AddChart2` (51 clustered column, 52 stacked, 58 stacked bar, 65 line with markers);
  - series from ranges, colours set per series;
  - data labels: white labels inside the end of the bar for columns, above the marker for lines;
  - exported with `Chart.Export` to `img/` and placed beside their tables.
- **Trap:** a corrupted pywin32 `gen_py` cache breaks COM. Delete the `00020813-...x0x1x9` folder.

## 7. Maps (QGIS standalone, `final_maps.make_map`)

- **Layout:**
  - clone a saved layout per map;
  - filter the legend to the map's own layers;
  - semi-transparent legend, 7 pt text, wrapped with `~`;
  - two columns when the legend exceeds 20 % of the map height, three above 40 %.
- **Extent:** fit the study area, then raise it to the top of the frame (3 % margin) so the legend and data table at the foot cover only its edge.
- **Content:**
  - data box from the same results as the text;
  - Google background at 30 %;
  - colours: STP-1 blue, STP-2 orange, STP-5 green; one HLS lightness shade per pumping or lift catchment.
- **Flags:** `--other-years` renders only the 2051 and 2061 maps and leaves the QGIS project untouched.
- **Team maps redrawn on the final network** from their server layers (`Revised_STPs.shp`, TE register).
- **Trap:** the QGIS python exits with 139 (a crash on exit) after finishing. Check the outputs, not the exit code.

## 8. Flow schematics

- R7's own drawer (`py/diagram_png.py`), fed by `flow_diagram.py` with one layout per scenario and design year:
  - columns by steps to the plant;
  - red pumped arrows with the design peak;
  - a navy gravity arrow into the plant;
  - a plant card with 2031 → design-year inflow, peak and inlet depth.
- The drawer checks text overlaps itself.
- The engineer rejected a decorated version: keep R7 as it is. One schematic per design year, because the peaks change.

## 9. DWG drawings (`py/final_dwg.py`)

- ezdxf R2018 in UTM metres, then `accoreconsole` saves DWG 2018.
- **Layers:**
  - SEW-GRAV-DN bands, line weight 0.25 to 1.00 mm;
  - SEW-MH, -DEEP (over 12 m), -DROP (over 0.5 m);
  - SEW-RM-PUMP and -LIFT (dashed);
  - SEW-PS, LS, STP;
  - TXT-STP, PS, RM, PIPE, MH;
  - BND and SHEET-LEGEND.
- **Text tiers:**
  - plants 40 m and stations 25 m (read at 1:50,000);
  - rising mains 6 m;
  - pipes and manholes 1 m.
- **Annotation:**
  - pipe: name, DN, L, S, Q, V, and the inverts;
  - manhole: GL, IL, depth, drop;
  - station: duty, head, kW, rising main, wet well;
  - plant: modules, inflows, inlet pump, wet-well volume.
- **Traps and checks:**
  - The last pipe into a station has no downstream manhole: compute its invert from the gradient.
  - A "drop" means more than 0.5 m; smaller steps are crown matching.
  - Check zoomed windows with ezdxf's drawing add-on before handing over.

## 10. Design data behind the report

- **The 12 designs** (4 scenarios × 2051/2056/2061): `py/final_design.py`, results in `results/final_0.75pc_SC1-SC4/<SC>-<year>/products`. The design-year rule is checked at the 2031 and 2036 peaks; `design_year_check_2056.json` lists the pipes over their limit.
- **Costs:** the team's method, per design year (`financial.json["designs"]`). The 2056 results are kept key for key and checked when the model changes.
- **SewerGEMS referee:** every design rebuilt in the VM; flows within 0.1 %, no pipe over its depth-of-flow limit.

## 10a. How the network, the depth, the lifts and the pumps were set (the design chain)

`py/final_run_all.py` runs it for the 12 cases (SC1-SC4 × 2051/2056/2061), in parallel. It repeats until the lift stations no longer change.

1. **Design (`final_design.py SC1 2056 --lifts`).**
   - Flow at every pipe: the plot loads at its upstream manholes, peaked by the Peltier/Merrimack table that SewerGEMS's Extreme Flow Setup uses ("Peltier100-Merrimack", on the average flow in L/s).
   - Plus infiltration of 0.72 m³/d per km of sewer upstream.
   - Plus the pumped transfers of other systems. A pumped flow or a lift's flow is added as a transfer of its peak, never peaked again.
   - Size: the smallest catalogue size whose Colebrook-White capacity (ks 1.5 mm) at the d/D limit (0.65 to DN355, 0.50 above) carries the design-year peak at the Table 11 minimum gradient. Passes are repeated until no size changes.
   - Exports: conduits at the design year and at the 2031 and 2036 check peaks.
2. **Split (`split_deep_subnetworks.py <case> <exports> <split> 0.0075 --fixed=fixed_stations.json`).**
   - **Steepen** pipes above DN200 to reach 0.75 m/s at their 2031 peak, up to the gradient limit (0.75 %), with one gradient per street run.
   - **Re-lay:**
     - a pipe's upstream invert is the lower of the lowest arriving invert and the shallowest invert its cover allows (1.3 m over the soffit at both ends);
     - its downstream invert is the upstream invert minus gradient × length;
     - depth is ground minus invert.
   - **Cut:** where a subnetwork stays more than 12 m deep for good, the last manhole at 12 m or less becomes a pumping station. Its flow is lifted to the next manhole, which restarts at minimum cover. Dips that come back to 12 m are left alone. An outfall is never moved.
   - **Join by gravity:** an outfall at 12 m or less within one standard manhole spacing (G203 Table 12, p30: 100 / 120 / 150 / 200 m by size) of the manhole it pumps to. A join is kept only if the station count goes down.
   - Repeat until nothing changes; fewest stations wins.
3. **Fewer stations (`reduce_stations.py`, the engineer's logic, settled in `fixed_stations.json`).**
   - Drop a station, or merge two into one where both flows pass. A change is allowed while every added station is at most 14.65 m deep and the outfall at most 14.65 m; no manhole goes past 16.5 m.
   - Among the allowed changes: the shallowest outfall, then the shallowest deepest station.
   - Engineer, 2026-11-18: "we are trying to stick to 12 m depth, but at times a bit deeper can help reducing a pump or lift... I accepted up to 14.65 (~15 m)... some manholes go as deep as 16.5 m".
4. **Self-cleansing check (`final_selfcleansing.py`).** Pipes above DN200 at 0.75 m/s at the 2031 peak (the rule). Those that miss it are checked at the 2036 peak, and the rest go on the flushing list.
5. **Names (`final_naming.py`).**
   - A station is a lift when its force main reaches a manhole within one standard manhole spacing; otherwise it is a pump.
   - Pumps are P1, P2...; a lift is P<n>L<k>.
   - Manholes and pipes are <section>-M<k> / -P<k>; a force main is <station>-RM.
6. **Stations sized (`final_products.py`).**
   - Duty: the design-year peak, raised so the force main keeps 1.0 m/s (G203 p50).
   - Force main: the size from 75 mm with the least power at v ≤ 2.5 m/s.
   - Head: static + Hazen-Williams friction (C 120) + 10 % minor losses.
   - Wet well: 1.5 m below the incoming invert. Discharge: 0.3 m above the receiving invert, or 3.0 m above the ground at a plant.
   - Efficiency (wire to water): 0.65. Type 1/2/3 by duty (G203 p40).
   - Energy: power × the hours the duty takes to pass the year's average flow.
7. **Quantities and cost:** `final_boq.py` (BOQ and network cost at the team's rates), `final_financial.py` (plants, TE, CAPEX/OPEX).

## 10b. Design constraints and standard values used (source of each)

The register of every value, with its guideline page, is `_BRAIN/02_DESIGN_CRITERIA.md` (in the zip under `reference/`). It is the only permitted source of numeric design values in this project. The values the W18 chain uses:

| Value | Used as | Source |
|---|---|---|
| Colebrook-White, ks 1.5 mm, ν 1.141e-6 | sizing, velocity, depth of flow | G203 p24, p28 |
| d/D ≤ 0.65 (D ≤ 355 mm), ≤ 0.50 above | sizing limit; the design-year check, judged at two decimals | G203 p27 Table 10 |
| Minimum gradient by size | laid gradient before steepening | G203 p29 Table 11 |
| Self-cleansing 0.75 m/s at the 2031 peak, pipes above DN200 | steepening target; audit; 2036 recheck | G203 p26 + engineer (W18 brief) |
| Gradient limit 0.75 % | the most a pipe is steepened | engineer's decision after the 0.50 / 0.75 / 1.00 % study |
| Maximum velocity 3.0 m/s | checked; none over | G203 p27 |
| Minimum cover 1.3 m to the crown | head pipes and re-lay | G203 p33 §4.6.3 |
| Depth 12 m to the outfall | cut into a station | G203 p33 ("approximately 10-12 m") + engineer |
| 14.65 m for an added station or outfall; 16.5 m any manhole | caps when removing stations | engineer, 2026-11-18 |
| Manhole spacing 100 / 120 / 150 / 200 m by size | gravity joins; lift vs pump | G203 p30 Table 12 |
| Station types by flow (≤100, 100-300, >300 l/s) | station type | G203 p40-41 Table 17 |
| Force main 1.0 to 2.5 m/s | force main size and duty | G203 p50 |
| Hazen-Williams C 120, +10 % minor losses, efficiency 0.65 | head and power | the W17 R7 method (`scenario_results.py`), kept |
| Peaking: Peltier / Merrimack table | design peaks | the SewerGEMS model's Extreme Flow Setup |
| Infiltration 0.72 m³/d per km | added to every pipe and plant | the SewerGEMS model (720 L/km/day on the conduits) |
| Treatment: four modules on design-year inflow + 10 % | plant capacity | G203 p65 Table 29 (+10 % allowance) + the team's cost method |
| Design years 2051 / 2056 / 2061, 2056 adopted | the three designs | engineer + the design-year test (6.2.4) |

## 10c. SewerGEMS through the API (how it was used)

- **Where it runs:**
  - SewerGEMS CONNECT 10.4 in a VirtualBox Windows 10 guest with **no internet**: never add an adapter, NAT or download.
  - Host `D:\VBOX` is the guest's `\\VBOXSVR\VBOX`.
  - Drive the VM headless (`VBoxManage guestcontrol`); never click in its window. Logging on needs the engineer's password, so give him the command.
- **The bridge:**
  - The engineer starts `bridge\watcher.ps1` in the guest. It runs every `bridge\jobs\*.ps1` in name order and writes `bridge\out\<job>.txt`, which ends `__EXIT__ <code>`. It moves the job to `done\` and rewrites `out\_alive.txt` every 2 s.
  - Check that heartbeat before dropping a job. It stops while a job runs, so treat a job as hung only after about 35 min with no output.
- **Before a job:**
  - Run `bridge\compile_check.ps1` on the host. It compiles `lib\*.cs` against copies of the DLLs in `refs\` and executes nothing.
  - The source of record is the repo's `sewergems_api\`, copied into the bridge.
- **A job:**
  1. Check free space on C: (stop under 2 GB).
  2. Set the case variables and dot-source `\\VBOXSVR\VBOX\bridge\lib\load.ps1`. It resolves the OpenFlows/Haestad assemblies in the SewerGEMS folder and compiles the C# helpers with `Add-Type`.
  3. `StartSession`, then `Open` a **copy** under `C:\IbriWork\...`.
  4. Do the work and `SaveAs` a **new** file (R0, R1...). Never overwrite the modeller's file; only ADD files to the model share.
  5. Export CSVs to `\\VBOXSVR\VBOX\bridge\out\...`.
- **The final build (`lib\build_final.ps1` + `FinalBuild.cs`, jobs 080-094):**
  - inputs from `py/final_sg_inputs.py` in the model's own element ids;
  - every conduit's size and inverts set;
  - each lift built as station manhole → 1 m stub → outfall, with its pipe switched off and its flow pumped to the next manhole as a transfer;
  - gravity joins carried as transfers;
  - every element renamed;
  - transfers of the design year and the check years (2031, 2036);
  - then analysis only (no design run: the sizes are the design), exports and a read-back.
- **The check:** `py/final_sg_compare.py`, pipe by pipe. Flows at the design year agreed within 0.1 %, no pipe went over its depth-of-flow limit, and the 2031 velocities matched.
- **Traps already paid for:**
  - Set every scenario's alternatives and calculation options to LOCAL explicitly: an inherited DESIGN option re-sized the pipes in every analysis year.
  - Repeat a design until no pipe size changes, and fail the job if an analysis changes a size.
  - A new year's alternative must be created with `Copy(loaded alternative id)`; `Add(parent)` breaks the second year.
  - The typed API's diameter is stale for catalogue pipes: read the size reference.
  - The 10.4 API refuses text user fields: use the element Notes.
  - Stored flows are cfs while the typed API returns display units.
  - Colebrook-White runs about 8 times slower than Manning (about 44 min per option): drop long jobs and watch `out\` rather than waiting inside one command.
- **Records:**
  - the model history and every decision in `W17/README.md` (zip: `reference/W17_README_SewerGEMS.md`);
  - the bridge rules in the global CLAUDE.md (zip: `reference/global-CLAUDE.md`);
  - the memory notes `sewergems-new-year-alternative-copy`, `vm-headless-not-gui`.

## 11. Inputs and correspondence

- **Outlook `.msg`:** `_SETUP/tools/read_msg.py "<file.msg>" [--save-attachments DIR]`. It uses olefile streams `__substg1.0_0037001F` (subject), `0C1A001F` (sender), `1000001F` (body), and the attachment storages.
- **Team data:** read their server layers where they live (`W:\...\10_TSE\SHP`). Never copy their raw TE data into the public repo.
- **`te_customers.csv` is data, not a script output.** It consolidates the team's register:
  - coordinates from their model demand points (`Ibri_TE_Model_Demands.shp`);
  - 2070 demands and supply hours from `identified customers MH.shp`;
  - 2030 demands from the model points where they agree with the register (TE-02, TE-05 and TE-06 take the register's values);
  - flow = demand / (hours × 3.6).

  The one-off code that merged them was not kept, so the file is shipped as data.

## Toolkit zip

- `_SETUP/tools/make_toolkit_zip.py` packs this inventory, every script of the W18 `py`, `gis` and `report_final` folders, the templates, styles, tools, the report-writing skill and the project memory.
- `MANIFEST.txt` in the zip lists every file: size, purpose (first docstring line) and source.
- The zip holds team files, so it goes to `deliverables/` (ignored by git) and to the engineer only.

## 12. Delivery

- **Package (`package_final.py`):**
  - Report (Word, PDF, Excel), Drawings, BOQ, Maps, QGIS with relative layer paths, SewerGEMS;
  - the report picked by exact name, because the user's own copies sit in the same folder.
- **Server:** unzip to `W:\...\04-Hydraulic\temp\<N> <package name>`. Never overwrite an earlier N; verify the file count and bytes against the zip.
- **WhatsApp (`wa.js`):**
  - one sender at a time: another session's send on the link fails both with 440;
  - wait for it, never kill it; resend anything that went out without an acknowledgement.
- **Chat:** SendUserFile for the PDF.

## 13. Templates, styles and the look

| Item | File | Used by |
|---|---|---|
| Firm's report template (styles, cover, headers, captions) | `Data/sample report/Sample.docx` (outside git) | project rule 5; the report-writing skill |
| The team's report the build edits (styles, cover, chapters) | `Hydraulic/temp/recent updates by the team/Ibri_Concept_Design_Report_R8-MH.docx` (outside git) | `build_report.py` `SRC` |
| QGIS A3 layout template: title, subtitle, scale bar, north arrow, legend, data-table frame | `gis/template_report_A3.qpt` (extracted from `QGIS 2621 ibri sewer stp2.qgz`) | `make_w17_project.py` → `final_maps.make_map` |
| Map helpers: layout clone, data box, boundary, settlement, depth, deep-run and label styles, memory legend lines, Google background | `gis/make_w17_project.py` (imported as `M`) | every map script |
| Manholes by depth (QML) | `qgis/styles/manholes_depth.qml` | `final_maps.py` |
| Road centreline (QML) | `W17/Options 2026-10/_styles/Road_Centercline.qml` | `make_w17_project.py` |
| QGIS project of the final design: 156 layers, 33 saved layouts | `results/final_0.75pc_SC1-SC4/qgis/Ibri_sewer_concept_design.qgz` | written by `final_maps.py`; shipped in the package |
| Clean-gate term lists (regex) | `report_final/forbidden_terms.txt`, `allowed_terms.txt` | `check_clean.py` |

- **Background:** Google satellite XYZ (`M.GOOGLE`) at 30 % opacity, credit "Satellite image: Google" on the map.
- **Map export:** 200 dpi (`M.DPI`); the legend background is white at 200/255 (`M.LEGEND_ALPHA`), so the map shows through.
- **Map labels:** `clamp(7, 8*25000/@map_scale, 36)` pt with a 0.8 mm buffer; flow arrows at pipe centres from 1:15,000 in.
- **Colours:**
  - plants: STP-1 #1F6FB2, STP-2 #D9730D, STP-5 #2E8B57; shades per catchment by HLS lightness;
  - Excel charts: navy #1B2A4A, blue #1F6FB2, orange #D9730D, green #2E8B57, red #D7301F, purple #7B4FB0, light #9DC3E6;
  - schematics: R7 red #A61B1B pumped, navy #1F3B63 gravity, box fill = plant colour at 14 %.
- **Fonts:** Calibri in the report, schematics and Excel; Arial in the DWG (`arial.ttf` text style).
- **Excel table style:** navy header fill with white bold text, banded rows, thin box borders, frozen header, a Contents sheet with hyperlinks, a note line under each title.
- **DWG layers:** listed in section 9; colour and line weight are set by layer.

## 14. Working method that held

- **Before editing:**
  - a [PRESERVE-CHECK] before editing code;
  - [BROAD] waits for a go;
  - questions with recommended defaults when a request has open choices (the team's structure: treatment, TE, costs, maps).
- **Checking:**
  - check before claiming: grep the built document before calling anything missing;
  - under "go ahead", decide and act.
- **Records:**
  - one logical change per commit, pushed;
  - live docs (root README, W18 README, `_BRAIN/00_CURRENT`, `07_PROJECT_STATE`) checked by `_SETUP/check_live_docs.py`;
  - memory updated with each trap the day it was paid for.
- **Long runs:** in the background with a stall monitor (Word CPU unchanged means it is blocked on a dialog).
