# Study area: the data behind Section 1.2 of the Concept Design Report R3

Added 2026-09-17 on the engineer's review. Nothing here changes a load; the loads stay frozen in `W14/shp`.

| File | What it does |
|---|---|
| `fetch_admin_osm.py` | Downloads the 11 governorates of Oman and the Wilayat of Ibri from OpenStreetMap (Nominatim) into `admin/*.geojson`, with the date of download. Used for the locator inset of the location map |
| `fetch_climate_power.py` | Downloads the NASA POWER (MERRA-2) record at the existing STP into `climate/`: daily temperature and rainfall 2001 to 2024, hourly wind at 10 m 2015 to 2024 |
| `study_area_stats.py` | Writes `study_area_stats.json`: ground level of every settlement from the 0.5 m terrain, road lengths by class, monthly climate, wind roses by sector and speed class. `python study_area_stats.py [ground roads climate wind]` |
| `study_area_stats.json` | The one file the report reads, through `W16/report/facts_area.py`: text, charts and map boxes cannot disagree |

## Choices worth knowing

- **Outlines from OpenStreetMap, not geoBoundaries.** geoBoundaries (checked 2026-09-17) still carries Oman as the 7 regions of 2010;
  the country has had 11 governorates since 2011. The Overpass servers timed out that day, so the relations are found by name through
  Nominatim and only an administrative boundary at `admin_level` 4 is accepted. Licence ODbL: credit "© OpenStreetMap contributors".
- **Climate from NASA POWER, because no station record has been supplied.** It is a reanalysis on a grid of about 50 km: good for the
  monthly regime and the prevailing wind, not for odour dispersion modelling, which needs the station. A reanalysis also smooths out
  calm hours, so the calm share is a lower bound. The report says both.
- **Rainfall after 2020 is rejected.** At this grid point POWER carries 790 mm for August 2024 (seven days of 65 to 113 mm), which did
  not happen, while the storm of April 2024 shows as 59 mm. The statistics use 2001 to 2020, the period of POWER's own climatology:
  80 mm a year. The wind uses 2015 to 2024.
- **Ground level of a settlement** = the median of the 0.5 m terrain at its built plots (plots with a meter); distance and bearing are
  from the existing STP (E444387 N2563352) to the population-weighted centre of those plots. The terrain gives 329.0 m at the STP.
- **Wind and odour.** The bearing from the STP to a settlement, turned by 180 degrees, is the sector the wind must blow from to carry
  air from the STP to it. The shares of all hours and of night hours (20:00 to 06:00) are in `facts_area.downwind()`.
- **The main pipe is not shown on any map of this section: it is not client data** (engineer, 2026-09-17).
- **Flood hazard** is the Oman Flood Mapping project of MAFWR (Renardet project 2331), the rasters in the meeting folder
  (`W16/Meeting 2026-09-16/04_Hydrology`, not in git). Classes H1 to H6 are the Australian classification, AIDR Guideline 7-3 (2017).
