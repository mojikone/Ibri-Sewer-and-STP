# W16 — the reports (opened 2026-09-14)

W16 is the report folder: a copy of W14's scripts, analysis, docs and figures, revised
for two documents. **The load chain itself did not change**: the plot and settlement
layers stay frozen in `W14/shp` and are read from there (`report/facts_w14.py`,
`REPO/W14`). When a decision changes the loads, W16 gets its own `shp/` and the path
moves.

| Folder | What it is |
|---|---|
| `report_basis/` | **The Design Basis Report: Settlement Boundaries, Population, Flows and Loads — Revision 0** (`R0/Ibri_Design_Basis_Report_R0.docx` + `.pdf`, 49 pages). Issued ahead of the concept report so NWS can approve the foundation: the boundaries, the people, the use of each plot, the rates, the growth and the overflow, the flow for every element, the plant loads. Nineteen decisions and seven data requests, each a yes or no. Built by `build.py` |
| `report/` | The concept report build carried from W14 (R0 to R2 stay in `W14/report/`; **R3 builds here**), plus the shared furniture every report uses: `doc.py`, `notes.py`, `omml.py`, `flow.py`, `charts.py`, `qgis_maps.py`, `facts_w14.py`, `to_pdf.py`, and the Word template in `template/` |
| `docs/` | W14's notes, plus **`CHANGES_FOR_CONCEPT_R3.md`**: every change made for the basis report that the concept report's next revision must carry |
| `py/`, `analysis/`, `img/` | the load chain and its outputs, as in W14 |

## The Word furniture (shared by both reports since W16)

- **Template** `report/template/Renardet_A4.docx`, built by `template/make_template.py` from
  the firm's monthly report sample (`Data/sample report/2621_MPR_AUG_00.docx`, outside the
  repository): the cover with the two logos and the swoosh, the header and footer, the heading
  look (Century Gothic, navy, no indent, no automatic numbering). Placeholders `{TITLE_1..3}`
  and `{FOOTER}` are filled by the build.
- **Captions are Word-native** (`SEQ Figure`, `SEQ Table` in the Caption style), so a figure
  added in Word takes the next number; the lists of figures and tables are `TOC \c` fields.
- **Symbols under an equation are lines**, `symbol; description, unit`, not a table.
- **Tables**: navy header row, white body, light horizontal rules, no banding.
- **Landscape pages** for maps (A4 landscape, 1.5 cm sides); consecutive figures share one
  section (`wide_figures`), and a heading never adds a page break at the start of a section.
- **Colours**: navy 1F497D, accent 4F81BD, red C0504D, gold E5A32B, in the charts and the
  flowcharts too (`charts.py`, `flow.py`).

## Rebuilding the basis report

```
cd W16/report_basis
python facts_basis.py          # the numbers on top of facts_w14: plant flows, loads, no-overflow, free meters
python charts_basis.py         # K01 to K05
python make_panels.py          # shp/free_meters.shp, shp/free_meter_panels.shp
# in QGIS (project stp2.qgz open): exec qgis_maps_basis.py and call run()  -> img/B01..B05, img/panels/, layouts kept
python compose_panels.py       # img/B06_panels_p01..08
python build.py --pdf --pages  # R0/*.docx, *.pdf, and R0/check/ contact sheets to look at
```

The maps are clones of the layout `W2 M1 Study Area` (imported into `stp2.qgz` from the older
project on 2026-09-14) and are **kept in the project** as `RPT B01_boundaries` … `RPT
B05_free_meters`, with `RPT B05 free-meter panels (atlas)` over the 68 panels; the free
meters and the panels are in the group `Claude W16 basis`. The satellite image is a copy of
the project's layer at 50 % opacity; the project's own layer is untouched.

## What the basis report asks for

Section 10 of the report: nineteen decisions in five groups (settlements and people; water and
sewage rates; growth; the network; the plant and the effluent) and seven data requests. The
list lives in `report_basis/decisions.py`, read by the front summary and the register alike.
