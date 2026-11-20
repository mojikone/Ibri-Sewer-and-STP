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
| SewerGEMS models of the 12 designs (referee runs) | `py/final_sg_inputs.py`, `sewergems_api/` (VM file-drop bridge) |
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
- **Visual pass:**
  - contact sheets of every page (40 per sheet);
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

## 11. Inputs and correspondence

- **Outlook `.msg`:** `olefile` streams `__substg1.0_0037001F` (subject), `0C1A001F` (sender), `1000001F` (body), and the attachments' names.
- **Team data:** read their server layers where they live (`W:\...\10_TSE\SHP`). Never copy their raw TE data into the public repo.

## 12. Delivery

- **Package (`package_final.py`):**
  - Report (Word, PDF, Excel), Drawings, BOQ, Maps, QGIS with relative layer paths, SewerGEMS;
  - the report picked by exact name, because the user's own copies sit in the same folder.
- **Server:** unzip to `W:\...\04-Hydraulic\temp\<N> <package name>`. Never overwrite an earlier N; verify the file count and bytes against the zip.
- **WhatsApp (`wa.js`):**
  - one sender at a time: another session's send on the link fails both with 440;
  - wait for it, never kill it; resend anything that went out without an acknowledgement.
- **Chat:** SendUserFile for the PDF.

## 13. Working method that held

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
