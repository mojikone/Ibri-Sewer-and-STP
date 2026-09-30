# Ibri Sewer, TE Networks and STP: the meeting folder, 16 September 2026

Everything for the Design Basis meeting in one place: the latest data, the reports, the
tables, the package delivered to NWS, and a QGIS project that loads it all, styled as in
the working project (stp2.qgz) and as the report maps. Open `Ibri_meeting_2026-09-16.qgz`;
every path is relative, so the folder can be copied anywhere as a whole.

| Folder | Content | Source |
|---|---|---|
| `01_Boundaries` | project boundary received (Project_Boundary.kmz, 440 km²) and updated (531 km²); the 25 settlement polygons received (Al Aynayn in two parts) | Inception Report package; the report maps |
| `02_Settlements` | `Settlements.shp` (delivered: people and Q by year, saturation, OR, peak); `Settlements_full_W14.shp` (69 fields, the load chain); `Overflow_routes.shp` (the arrows of concept Fig. 19) | W14 load chain, frozen |
| `03_Plots_meters` | `Plots.shp` (the delivered layer, extended on 30 September 2026 with every five-year step: see below) and `Electricity_meters.shp` (delivered); `Plots_full_W14.shp` (56 fields); `free_meters.shp` (the 126 meters of basis Fig. 3) | W14, W16 |
| `04_Hydrology` | streams (NSA 2 m, project boundary); upstream catchments; flood hazard T10, T25, T50, T100, T500 clipped to the boundary + 2 km | the 2331 flood-hazard study (Lekhuwair area) |
| `05_Roads` | road centrelines with the dual-carriageway flag | received |
| `06_Population` | GHS population 2025 | GHSL |
| `07_Terrain` | the 0.5 m terrain resampled to 2 m (417 MB) and its hillshade | Terrain/Sat_0p5m/IBRI_0p5_clip.tif (24 GB, not copied) |
| `08_Existing_network` | main pipe, sub-main guide, Ibri STP; NAMA wastewater assets as received (gravity sewer, force mains, treated effluent main, pumping station, STP) | received |
| `09_PAEW` | PAEW_MAIN.kmz and the three Al Raybah KMZs | received |
| `10_Identified_projects` | the footprints (delivered) and the labelled sites of concept Fig. 26 | W14 |
| `11_Network_design_W15` | W15 pipes, outlets and catchment groups; the W15 subnetworks KMZ (for Google Earth; not loaded in QGIS, it holds hundreds of folders) | W15 |
| `Reports` | Design Basis Report R0 (Word, PDF); Concept Design Report R2 as issued and **R3, the latest build** (Word, PDF); the meeting deck | W16, W14 |
| `Tables` | tariff to NAMA category workbook; growth by settlement workbook | W16, W14 |
| `Delivered` | the zip sent to NWS and its unpacked copy | W16/deliverables |
| `_styles` | the QML styles taken from stp2.qgz and the report maps; the check renders | |

## The plot layer, `03_Plots_meters/Plots.shp`

77,265 plots, 40 fields. The meters, the use and the geometry are as delivered to NWS; the people and
flow columns were rewritten on 30 September 2026.

| Fields | Meaning |
|---|---|
| `POP_2024`, `POP_2025`, `POP_2030` … `POP_2065`, `POP_SAT` | people on the plot in that year; `POP_SAT` is 2070, the year the study area is full. Two decimals |
| `Q_2024`, `Q_2025`, `Q_2030` … `Q_2065`, `Q_SAT` | average sewage flow of the plot, m³/d: not peaked, no infiltration, no design margin. Four decimals |
| `FULL_YEAR`, `POP_FULL`, `Q_FULL` | the year the plot's settlement is full, and the plot's people and flow in that year ("Full in" and "At saturation" of the report's five-year tables) |
| `SAT_YEAR` | the same year as `FULL_YEAR`, kept under its delivered name so that existing styles keep working |

How to read them:

- A built plot keeps its 2024 people and flow in every year. An empty plot takes its share of the people its
  settlement has housed by that year, by plot area capped at 1,000 m². **A value on an empty plot is a share,
  not a forecast of which plot is built first.**
- A plot stops changing once its settlement is full, so `POP_FULL` and `Q_FULL` equal `POP_SAT` and `Q_SAT`.
- The values are rounded together, settlement by settlement: every column of a settlement sums to the
  settlement's figure, each plot is within 0.01 person and 0.0001 m³/d of its value, and no plot goes down from
  one year to the next.
- **Against the Concept Design Report R3**: the people columns reproduce all 287 printed cells of the five-year
  table of people, and the totals of both tables. The flow columns reproduce 272 of the 287 printed cells of the
  five-year table of flow; the other 15 are printed 1 m³/d higher in the report, which rounds a figure already
  rounded to one decimal (Ibri 2040: 17,139.45 m³/d here, 17,139.5 in the series, 17,140 in the report).
  `python W16/meeting/plot_years.py --check-only` repeats the comparison.

## The QGIS project

Groups, top to bottom: **Report maps** (the copies asked for the meeting: settlements labelled
with people 2055 / at saturation; flow 2055 / at saturation in the saturation-map style;
capacity taken by overflow with the arrows, concept Fig. 19; average sewage flow of every plot
at saturation, concept Fig. 25; identified projects, concept Fig. 26; the 126 meters, basis
Fig. 3; use of the plot), **Boundaries**, **Plots and meters**, **Hydrology**, **Roads**,
**Population**, **Terrain**, **Existing network**, **PAEW**, **Network design W15**,
**Identified projects**, and Google Satellite at 50 %. Only the first map of each kind is
switched on; the others are ready in the tree. Hazard rasters share the T50 style and classes.

Built by `W16/meeting/make_meeting_folder.py`, `plot_years.py` and `make_meeting_project.py` (in the
repository; this folder is not).
