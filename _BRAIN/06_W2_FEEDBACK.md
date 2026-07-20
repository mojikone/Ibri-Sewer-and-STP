# W2 FEEDBACK CONSTRAINTS (user review of W1, 2026-07-20) — binding for W2+

## Technical
1. **Elevation source = DTM** `Hydraulic/Terrain/DTM_terrain_mask.tif` (5 m, EPSG:32640, nodata -9999). User-patched from DSM around (449619, 2568352). DSM only as fallback.
2. **Dual carriageways: collapse to a single routing centerline.** Trunk must never run as two parallel pipes along a dual carriageway; connect across when needed.
3. **Coverage:** trunk/zones must serve ALL settlement areas in the boundary (W1 missed NW, NE, E, S satellite areas — user circled). Scope requires all plots serviced.
4. **Zones must be structured**: contiguous, smooth-boundary, realistic polygons (W1 ragged multipart plot-buffer dissolve rejected). One outlet each, road-and-density based.
5. **SLS must be consolidated**: one SLS per contiguous non-gravity pocket at its low point, minor pockets (<~30 plots) absorbed to detailed design; W1's 125 candidates rejected as "adding nonsense cost".
6. Roads in report/maps: show as provided (single style); do NOT present derived hierarchy as a deliverable.

## Maps
7. Background: Google satellite hybrid at the 30% opacity already set in project.
8. Land use display layer: **MoH_Plots** (not Landuse) for maps.
9. Scale bar: fix cramped labels (wider bar / fewer segments).
10. Bottom-right box on each map = table with data relevant to that map.
11. **Save layouts into the QGIS project** (layout manager) so user can adjust manually.

## Report (R1+)
12. Style strictly per `Data/sample report/Sample.docx` (cover, fonts, headers/footers, captions, page numbers, tables, TOC).
13. Client-facing: no meta-talk (no W-folders, no "user-provided data", no GAP tags visible as such — phrase as "data to be provided/confirmed").
14. Expanded: executive summary w/ real summary; scope + explicit deliverables list; criteria in depth with explanations; clear methodology narrative (W1 judged too terse/unclear); full data-request register (population, flow meters, billing, as-builts, LIMS, NCSI, IMP…).
