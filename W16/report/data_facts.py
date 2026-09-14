"""Measured facts about the received data, used by the report.

Every figure the report quotes about the received datasets is recorded here
with how it was obtained, so the report and the source stay in step and the
numbers can be reproduced.

Measurements were taken in the project QGIS session against the approved
project boundary (531.4 km2), all lengths computed in EPSG:32640.
"""

BOUNDARY_KM2 = 531.4

# The wastewater dataset holds two networks distinguished by OP_STATUE.
# Constructed assets carry an installation date of 1 January 2006, a source of
# drawings or CCTV, and project codes 5A-1 to 5A-5. Proposed assets carry no
# installation date, a source of Asset Planning, project code SUREKHA and a
# remark identifying them as the large urban area networks.

# asset, constructed features, constructed length, proposed features,
# proposed length  (all lengths within the study area)
WASTEWATER = [
    ("Gravity sewer", "3,267", "**111.6 km**", "129", "199.3 km"),
    ("Force main", "1", "**10.0 km**", "8", "23.2 km"),
    ("Treated effluent main", "none", "**none**", "8", "45.7 km"),
    ("Pumping station", "1", "**1**", "—", "—"),
    ("Treatment plant", "1", "**1,800 m3/d**", "1", "29,038 m3/d, shown as design"),
]

# constructed network only: what the attributes carry
CONSTRUCTED = [
    ("Installation date", "1 January 2006 on every constructed record"),
    ("Source", "drawings, and closed-circuit television on one length"),
    ("Project codes", "5A-1 to 5A-5"),
    ("Diameters", "not recorded on the constructed gravity network"),
    ("Levels", "not recorded"),
    ("Client remark on the records",
     "“Data is not reliable and must be used only for reference purpose”"),
]

WATER = [
    ("PAEW water mains", "6,156", "1,315.9 km", "647.8 km (49 %)",
     "adopted as the source for utility interfaces"),
    ("PAEW water laterals", "1,954", "12.7 km", "8.1 km (64 %)", "—"),
    ("PAEW system valves", "2,866", "2,866 points", "1,586", "—"),
    ("PAEW hydrants", "965", "965 points", "568", "—"),
    ("PAEW services", "318", "318 points", "—", "—"),
    ("PAEW facilities", "265", "265 points", "20", "—"),
    ("NAMA water mains extract", "90", "3.5 km", "none",
     "located near 55.80 E, 24.27 N, approximately 130 km north-west of the "
     "project area"),
]

OTHER = [
    ("Electricity accounts", "33,970 points",
     "Tariff, coordinates and governorate. No land use, floor area or "
     "consumption is recorded."),
    ("Ibri Bypass scheme", "13,404 placemarks",
     "A drawing export carrying 11,715 sublayers of blocks, hatches and "
     "dimensions. Suitable as a positional reference; conversion is required "
     "before it can be used as structured data."),
    ("Al Raybah pipelines", "3 files",
     "Pipeline alignments at 110, 180 and 225 mm, within the project area."),
    ("Rehabilitation packages", "6 archives",
     "Work-order submissions covering Al Sad, Khadil, Yanqul, Dhank and Hay "
     "Al Aqabah, comprising drawings, meter schedules and geodatabases."),
    ("House connection packages", "4 archives",
     "Contractor submissions dated May and June 2026."),
]

NOT_APPLICABLE = [
    ("Mudhaibi zone 6", "544 placemarks", "Wilayat of Mudhaibi, Ash Sharqiyah"),
    ("Mudhaibi zone 8", "461 placemarks", "Wilayat of Mudhaibi, Ash Sharqiyah"),
    ("Qabil Al Rukha", "5 placemarks", "Wilayat of Mudhaibi"),
    ("Qunaib", "4 placemarks", "Wilayat of Mudhaibi"),
    ("New location", "8 placemarks", "Approximately 30 km north of the project area"),
]

# requested, received, status
REGISTER = [
    ("Constructed sewer network, as-built", "Yes",
     "Geometry received, dated 2006. Levels and diameters not recorded; "
     "being surveyed"),
    ("Constructed force main", "Yes", "Received, dated 2006"),
    ("Treated effluent network", "Proposed only",
     "The dataset contains no constructed treated effluent asset"),
    ("Lifting station details", "Partial",
     "One station located; equipment and duty details being surveyed"),
    ("Treatment plant records", "Partial",
     "Location and nominal capacity received; operating data outstanding"),
    ("Electricity account data", "Yes", "Received"),
    ("Cadastral plot data", "Yes",
     "Received. Land use and missing plots being addressed"),
    ("Potable water network", "Yes",
     "Received as part of the PAEW dataset"),
    ("Topographic survey", "In progress", "Survey team mobilised"),
    ("Integrated Master Plan", "No", "Requested"),
    ("Plant inflow and tanker records", "No", "Requested"),
    ("Electricity, telecom and gas service records", "No",
     "To be requested from the respective owners"),
]
