# Changes for the Concept Design Report, Revision 3

Everything below was done for the Design Basis Report R0 (2026-09-14) at the engineer's
request and is to be carried into the concept report's next revision. R2 (`W14/report/R2/`)
stays as issued. R3 builds in `W16/report/` on the same furniture the basis report uses.

## Format

| # | Change | Where it is done |
|---|---|---|
| 1 | The firm's template: cover with the two logos and the swoosh, header, footer with the contract number and page number, Century Gothic navy headings, **no indent, no automatic numbering** | `W16/report/template/`, `doc.new_document()` |
| 2 | Captions are Word-native `SEQ` fields in the Caption style, so a figure added in Word takes the next number; lists of figures and tables as `TOC \c` fields | `doc.fig_caption`, `doc.tab_caption`, `doc.list_of` |
| 3 | The symbols under an equation are **lines** (`symbol; description, unit`), not a table | `doc.symbols` replaces `_params` in `rpt_cd.py` and the others |
| 4 | Tables: navy header row, white body, light rules; the sample's blue banding is not used | `doc.table` |
| 5 | Every map with a satellite background at **50 % opacity** (was 30 %) | `qgis_maps_basis.basemap()`; apply the same copy-layer method in `qgis_maps.py` |
| 6 | The land-use map: coloured uses **without an outline**, only the empty plots outlined (Figure 16 of R2) | `qgis_maps_basis.layers()`, layer "Use of the plot" |
| 7 | Consecutive landscape figures in one section, no blank pages; a heading at the start of a section adds no page break | `doc.wide_figures`, `doc.h`, `doc.page_section` |
| 8 | Chart and flowchart palette moved to the template's colours | `charts.py`, `flow.py` |
| 9 | **No worked example** in the concept report either: remove the worked plot of §15.4 (`F.example_plot`) and any "worked for Ibri" passage | `rpt_cd.py` |
| 10 | Plain words throughout; every adopted value in one table with its reason; a numbered decisions register at the end, each line a yes or no | pattern in `rpt_basis.py` §8 and §10 |

## Content and wording

| # | Change | Reason |
|---|---|---|
| 11 | "Peak daily flow" (§15.6, the abbreviations table, the symbol lines) becomes **peak flow, the guideline's Qpdf, equal to the peak hourly flow** of G203 Table 29 | the guideline's label is a misnomer and misled the engineer (Q&A 2026-09-13) |
| 12 | The footnote "164 × 0.85 + 36 × 0.54 + 23 × 0.54 = 171.3" names the 36 and the 23 as 22 % and 14 % of 164 | a reader could not tell where they came from |
| 13 | The "on dwellings" cells of the settlement rates table (R2 Table 20) become "no meter, share on the houses", with a footnote to the §15.4 rule | it read as a category, not a placeholder |
| 14 | §17: "lost within the distribution network" becomes "lost within the **treated effluent** distribution network" | it read as the sewer |
| 15 | §16 heading "Trade effluent, identified projects and special consumption" becomes "Non-domestic discharges: industrial estates and identified projects"; **TSE** for treated effluent throughout with the one-line definition kept | "Trade" and "Treated" a page apart were misread |
| 16 | New in §14.2: the boundary map with the received polygons and the redrawn partition (`B01_boundaries`), the four corrected settlements named, and the decision line | the engineer wants the boundaries approved |
| 17 | New in §14.7: **with and without the overflow** as a decision — the chart of the two series (`K03`), the ten most affected settlements (`K04`), the table by settlement, the seven that never fill alone, the 75,414 people with nowhere to go | the largest single decision of the basis |
| 18 | New: the free-meters map (`B05_free_meters`) and the 68 zoom panels (`B06_panels_p01..08`) as an appendix, and the decision (assign or leave) | 126 meters carry no load |
| 19 | New in §15.7: the saturation flow map with the four-step recipe box (`B03_saturation`) | lets the client compute a plant flow by hand |
| 20 | New in §12: the self-cleansing curve, the full version in an appendix (`K01_mara_full`) and the minimal one in the text (`K02_mara_minimal`), the 1.5 l/s floor and τ = 1 Pa stated for NWS | the tractive rule needs the picture |
| 21 | New in §13: the plant flows by year with the margin (AAF, PHF; MDF from records), the process loads from 60/80 g per person with the Table 30 check, the tanker strength (Table 31), the LIMS data request | the plant section of R2 had no loads |
| 22 | New in §10.1 departures: the connection ratio 0.61, the constant 2.40 % growth beyond 2058, the concept-stage gradient rule with its floor, the 12 m hard limit, the horizon (saturation against completion + 25) | each is a decision line in the basis report |
| 23 | §14.4 and A3: the occupancy table headed "Rate worked out / Rate adopted" and the small-settlement rule stated in one sentence | plain words |
| 24 | The assumptions table (basis §8) and the data-request table (§9) reproduced in R3 §10 and §5 | one place for every adopted value |

## Not changed

- The numbers: R3 reads the same `facts_w14.py` as R2 and the basis report; nothing was re-derived.
- The load layers: `W14/shp` is frozen; the 126 meters stay out of the loads until Decision 3 is answered.
