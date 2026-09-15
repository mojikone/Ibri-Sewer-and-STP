# Ibri Sewer, TE Networks and STP: the data behind the Design Basis Report, Revision 0

Renardet project 2621, for Nama Water Services. Packaged 2026-09-15.

Every value is the one in the Design Basis Report R0: the settlement boundaries redrawn as a partition, the people, the use of each plot, the rates, the growth with the overflow, and the average sewage flow of every plot and settlement. Nothing here is re-derived; the report's decisions (Section 10) apply to all of it.

| Folder | Files | What it is |
|---|---|---|
| 01_boundaries | Project_boundary_received.kmz, .shp | the project boundary as received (Project_Boundary.kmz), 439.8 km2 |
| 01_boundaries | Project_boundary_updated.kmz, .shp | the project boundary as updated for the report maps, 531.4 km2 |
| 01_boundaries | Settlement_boundaries_received.kmz, .shp | the 25 settlement polygons as received with the Inception Report (Al Aynayn drawn as two parts, so 26 polygons), with the client's population series 2023 to 2100 |
| 02_settlements | Settlements.xlsx, .kmz, .shp | the 25 settlements: people and average sewage flow for 2024, 2025 and every five years to 2070, the saturation year and people, OR (persons per property), the peak flow for a trunk (2055 and saturation); coloured by the flow at saturation as the report's map |
| 03_meters | Electricity_meters.xlsx, .kmz, .shp | the 33,971 electricity meters as received (2024), with the tariff, the NAMA category it folds into, the plot and the settlement; the KMZ has a folder per category, only Domestic switched on, the 126 free meters in black |
| 04_plots | Plots.xlsx, .kmz, .shp | the 77,265 plots: meters by tariff group and the total, the use (eight classes), people and average sewage flow for 2024, 2030, 2055 and saturation, the saturation year; the KMZ has a folder per settlement and a subfolder per use, coloured as the report's land-use map, empty plots switched off |
| 05_identified_projects | Identified_projects.xlsx; Identified_projects_footprints.kmz, .shp | the register of identified projects and special consumption (the two estates, the army camp, the hospital, the college, the hotels, Ibri View, the tanker sources outside) with how each is treated; the footprints found in OpenStreetMap |

## Conventions

- Every folder holds SHP/ (the shapefile with its sidecars), KMZ/ (Google Earth) and XLS/ (Excel).
- KMZ files are in WGS 84 for Google Earth; the balloon of every feature carries its table. Shapefiles are in UTM zone 40 North, WGS 84 (EPSG:32640).
- Q is the average sewage flow in m³/d after the return ratios (85 % of domestic and tanker water, 54 % of the rest), without infiltration or the STP margin.
- People by year follow the series with the overflow: a settlement grows at the series' rate until its land is full, then its further growth moves to its neighbours (Decision 4).
- The plots carry the four stored years, 2024, 2030, 2055 and saturation; the settlements carry 2024, 2025 and every five years to 2070.
- OR is the persons per property adopted for the settlement (Decision 2).
- The peak flow of a settlement is its own average flow peaked: Merrimack (PAM-GUD-201 p71) where it has over 100 properties in that year, Peltier (p72) otherwise; add 720 l/d per km of sewer for infiltration. The study area's peak is Merrimack on the whole flow, not the sum of the settlements' peaks.
- The use of a plot is the one determined from the meters and the satellite image (Decision 3); the eight classes are Residential, Residential-Commercial, Commercial, Government, Agricultural, Industrial, Heritage and Empty (unmetered).
- The 126 meters more than 15 m from any plot carry no load (report Section 3.3).

Key figures: 2024 119,893.34000000001 people and 20,852 m³/d; 2055 244,914.25999999998 people and 42,266 m³/d; saturation 2070 349,029.33999999997 people and 60,099 m³/d.
