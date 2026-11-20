---
name: w18-r11-report-brief
description: "Engineer's brief of 2026-11-19 for report R11 and its deliverables: flow schematics, Excel charts, DWG drawings, map colours, layout and table QA, per-station population/flow, team maps redrawn"
metadata:
  node_type: memory
  type: project
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-19T14:42:48.369Z
---

The engineer's brief of 2026-11-19, given before a PC restart: "keep these in mind; when I'm back I will ask you to continue". On "continue", list the tasks and wait for go (see [[list-tasks-before-multistep-work]]). The report is R10, built by `W18.../report_final/build_report.py` + `r10_edits.py`; the next revision is R11 in its own folder.

**What the engineer asked for:**
1. **Flow schematics per scenario.** R7 drew how each subnetwork connects to the STP (`W17/py/diagram_*.py`, `W17/report/img/W17_S#_transfer_diagram.png`). A colleague redecorated them with ChatGPT, and R8-MH showed them as "OPTION n- Flow Schematic". My R9/R10 Chapter 6 dropped them. Redo them for SC1-SC4 (P#, P#L#, STP-1/2/5) and show them the way R8-MH did.
2. **More charts, but only useful ones.** Build each in Excel first (an attractive chart, live formulas) and ship the workbook with the report. The client is an old-school engineer who always asks for Excel. Keep the data clean, as a person would lay it out: no stray cells or text. R8-MH's Chapter 6 ended with "Concept Options Comparison", "WW and TE duty pump power by option" and "Total TE network length by option" charts, and tables of combined duty power and advantages/trade-offs. Those were dropped too; consider redoing them.
3. **Read the report as a person would.** A smooth, logical flow that can be skimmed; informative and conclusive when read in depth. Don't repeat things; put each item where a reader would look for it.
4. **DWG drawings.** All scenarios, subnetworks and labels:
   - pumps and lifts in a large font, readable when zoomed out;
   - zoomed in, manholes and pipes show label, depth, invert level, drop(s), length, velocity, slope and flow;
   - pumps show flow, head, rising main length and DN, and velocity;
   - each STP shows volume, depth and its inlet pump characteristics.
   Propose the layers, colours, line weights and number of drawings.
5. **List the useful visuals and ideas from R7 and R8-MH** that could be added.
6. **Keep QGIS and the other deliverables consistent** with the report.
7. **Map colours.** Where a scenario has two STPs, use two clearly different colours. Where one colour shows a network, use shades of it to tell apart the catchments draining to each lift.
8. **Layout QA across the whole report:**
   - no caption on the next page and no empty pages;
   - figures, tables and text centred;
   - a full-page figure uses the whole page with its caption on it;
   - where the study area shrank to clear the legend (Figure 6-14), use a smaller legend font with wrapped lines and let the semi-transparent legend overlap the map.
9. **Redraw the team's maps** on the new network from the layers on the server. Figure 6-2 (STP locations) still shows the old subnetworks, and the TE customers map is the same.
10. **Tables at a consulting firm's standard:** content centred and fitted to the cells (Table 6-6 was untidy), header rows repeated on every page, across the whole report.
11. **For every STP, pump and lift:** people and flow in m³/d every 5 years from 2026 to 2065, also in Excel. Use one table where the scenarios differ only slightly, separate tables where they differ. Put them where a reader would look.
12. **If requests overlap, merge them** so the reader isn't confused.

**Also proposed before this brief, not yet approved:**
- Move the 0.50/0.75/1.00 % gradient comparison from Chapter 3 to 6.2, and say why SC1 stands for all four.
- Make 6.2.3 decisive with one table of the twelve designs, including the pipes over their depth limit by 2056 if designed for 2051. State the rule and conclude "2056 in all four".
- Put the 2051 and 2061 self-cleansing maps in Appendix D.
- Order each scenario by the flow: network → stations → treatment → TE.

**Done in R11 (2026-11-19), and the decisions taken along the way:**
- The flow schematics are the R7 transfer diagrams, re-fed with SC1-SC4 (`report_final/flow_diagram.py` drives `py/diagram_png.py`). The engineer rejected the decorated matplotlib version: "the graphic is not good; keep the same as R7, later the team will check it". Don't redesign them unless asked.
- DWG: `py/final_dwg.py` writes DXF with ezdxf, then saves DWG through `accoreconsole.exe` (AutoCAD 2026, no window, about 10 s each). There is one drawing per scenario, at true UTM coordinates. A "drop" means a step of more than 0.5 m; the smaller steps are crown matching.
- Layout traps:
  - An empty paragraph after a full table or chapter spills onto a blank page. Remove it and shrink the section-break paragraph to 1 pt (`r11_edits`).
  - Team captions carried their own font size and no full stop. Normalise them.
  - The team's chapters had two different body indents, so make all body text flush.
  - Size table columns by their content.
  - `check_clean.py` takes `--terms`/`--allow` as flags. Passing the files positionally fails on the risk IDs R01-R16.
  - Stuck hidden Word instances (`/Automation -Embedding`) hang `word_finish`. Kill only those.
  - After a killed or failed run, Word puts a VISIBLE dialog on the second screen: "The last time you opened '...R12.docx', it caused a serious error. Do you still want to open it?" It blocks the hidden instance. List the process's windows (EnumWindows) or take a screenshot, and answer Yes.
  - On the ~190 MB report, Word answers "Command failed" to Save and TOF Update when background repagination is on. `word_finish` turns pagination off for the updates, retries, and uses SaveAs2 to a new name then swaps. Pagination must be back ON before ExportAsFixedFormat, or it silently writes nothing.
  - Never Move-Item -Force onto a file Word may still hold: it deleted the target before failing.
  - A new A4 section copied from the cover's sectPr inherits `titlePg`, so its first page shows the cover's blank header and footer. `r11_edits` strips `titlePg` from every section but the cover.
  - Flow schematics go one per design year (peaks, plant card and inlet depth change with the year; the engineer, 2026-11-19). The zones map stays once per scenario.
  - Table sizing: rotated header cells (`textDirection`) need no width; a picture table (the cover) must be skipped; cap needs at the page width. A negative width gave Table 4-9 letter-by-letter names over eight pages.

Related: [[w18-final-design-brief]], [[report-detail-team-level]], [[qgis-label-and-arrow-style]], [[show-drawings-not-tables]].
