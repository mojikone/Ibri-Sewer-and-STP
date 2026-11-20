# Outputs and delivery: maps, schematics, DWG, workbook, package

## Contents
1. Maps (QGIS, standalone)
2. Flow schematics
3. DWG drawings
4. Excel workbook
5. The package and delivery
6. The look

## 1. Maps (QGIS, standalone)

Reference: `scripts/gis/final_maps.py` (`make_map`), helpers in `gis/make_w17_project.py` (imported as `M`), layout template
`gis/template_report_A3.qpt`, styles in `qgis/styles/`.

- **Run without the GUI:** `& "C:\Program Files\QGIS 3.44.8\bin\python-qgis-ltr.bat" script.py`. It renders saved layout
  clones.
  - QGIS's python exits with code 139 (a crash on exit) after finishing. Check the outputs, not the exit code.
- **Layout:**
  - clone a saved layout per map;
  - filter the legend to the map's own layers;
  - semi-transparent legend, 7 pt text, wrapped with `~`;
  - two legend columns when the legend exceeds 20 % of the map height, three above 40 %.
- **Extent:** fit the area, then raise it toward the top of the frame (3 % margin), so the legend and the data table at the
  foot cover only its edge.
- **Content:**
  - the data box from the same results as the report text;
  - a Google satellite background at 30 %;
  - one colour per plant, and one lightness shade per pumping or lift catchment.
- **Labels:** `clamp(7, 8*25000/@map_scale, 36)` pt with a 0.8 mm buffer; flow arrows at pipe centres from 1:15,000 in.
- **Save the layouts into the QGIS project**, not only the exports. Ship the project with relative layer paths.
- **Open every exported PNG and look at it.** A layer with categories switched off renders almost nothing while its legend
  still looks complete.
- **PyQGIS through MCP:** never chain `renderer().categories()[i].symbol()`. Bind names, or style through QML; the chained
  form crashed QGIS.

## 2. Flow schematics

Reference: `scripts/report_final/flow_diagram.py`, driving `py/diagram_png.py` (matplotlib), with layout rules in
`py/diagram_layout.py`.

- Draw one schematic per scenario **and per design year**: the peaks change with the year.
- Columns by steps to the plant.
- Pumped arrows in red with the design peak; a navy gravity arrow into the plant.
- A plant card with the opening → design-year inflow, the peak and the inlet depth.
- The drawer checks text overlaps itself. Keep the style plain; at Ibri the engineer rejected a decorated version.

## 3. DWG drawings

Reference: `scripts/py/final_dwg.py`.

- **Build:** ezdxf R2018 in UTM metres. Then AutoCAD's `accoreconsole.exe /i file.dxf /s script.scr` with
  `_.SAVEAS 2018 "out.dwg"` writes a real DWG, with no window, in about 10 s per drawing.
- **Layers:**
  - SEW-GRAV-DN bands, line weight 0.25 to 1.00 mm;
  - SEW-MH, -DEEP (over 12 m), -DROP (over 0.5 m);
  - SEW-RM-PUMP and -LIFT (dashed);
  - SEW-PS, LS, STP;
  - TXT-STP, PS, RM, PIPE, MH;
  - BND and SHEET-LEGEND.
- **Text tiers:** plants 40 m and stations 25 m (readable at 1:50,000), rising mains 6 m, pipes and manholes 1 m.
- **Annotation:**
  - pipe: name, DN, L, S, Q, V, inverts;
  - manhole: GL, IL, depth, drop;
  - station: duty, head, kW, rising main, wet well;
  - plant: modules, inflows, inlet pump, wet-well volume.
- **Traps:**
  - the last pipe into a station has no downstream manhole, so compute its invert from the gradient;
  - a "drop" means more than 0.5 m, and smaller steps are crown matching;
  - render zoomed windows with ezdxf's drawing add-on and look at them before handing over.

## 4. Excel workbook

Reference: `scripts/report_final/report_workbook.py`.

- **Sheets (openpyxl):** one per report table, plus a Contents sheet with hyperlinks. Derived cells are formulas
  (`"=D{r}-E{r}"`, `SUM`). Lay it out as a person would: no stray cells.
- **Charts (Excel COM, `DispatchEx`, hidden):**
  - `Shapes.AddChart2`: 51 clustered column, 52 stacked, 58 stacked bar, 65 line with markers;
  - series from ranges, with colours set per series;
  - labels inside the end of the bar for columns, above the marker for lines;
  - `Chart.Export` to PNG.
- **Trap:** a corrupted pywin32 `gen_py` cache breaks COM. Delete its `00020813-...` folder.

## 5. The package and delivery

Reference: `scripts/py/package_final.py`.

- **Package contents:** Report (Word, PDF, Excel), Drawings, BOQ, Maps, QGIS (relative paths), SewerGEMS.
- **Pick files by exact name.** The user's own copies sit in the same folders.
- **Server copy:** unzip into a new numbered folder (`<N> <package name>`). Never overwrite an earlier N, and check the file
  count and bytes against the zip.
- **WhatsApp:** the user's linked sender (`node wa.js send me <file> <caption>`; `status: 2` means acknowledged).
  - Only one sender at a time; another session's send fails both with 440. Wait for it, and never kill it.
  - Ask the user before every send.
- **Chat:** files up to 30 MiB for the Remote Control viewer. For anything larger, send a copy without the heavy file, or use
  WhatsApp.

## 6. The look (Ibri's, as an example)

- Plants: STP-1 #1F6FB2, STP-2 #D9730D, STP-5 #2E8B57.
- Excel: navy #1B2A4A, blue #1F6FB2, orange #D9730D, green #2E8B57, red #D7301F, purple #7B4FB0, light #9DC3E6.
- Schematics: red #A61B1B pumped, navy #1F3B63 gravity; box fill = the plant colour at 14 %.
- Fonts: Calibri in the report, schematics and Excel; Arial in the DWG.
- Maps: 200 dpi, legend background white at 200/255.
