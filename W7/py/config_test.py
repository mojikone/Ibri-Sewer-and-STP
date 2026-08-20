"""W5 test-boundary run settings. Paths only — design values live in sewnet/criteria.py."""

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"

# roads: the categorised layer. `dual` says 1 = dual carriageway (never used),
# 2 = two-lane pair (one side only). Its .prj is hand-written, so the CRS is set in code.
ROADS = BASE + r"\Hydraulic\SHP\Road centerline 2\Road_Centercline.shp"

PLOTS_CLASS = BASE + r"\Hydraulic\Claude\W3\shp\MoH_Plots_class_v4.shp"   # read as utf-8
PLOTS_RAW = BASE + r"\Hydraulic\SHP\MoHUP_DATA\MoH_Plots.shp"            # land use, plot cover
UNPARCELED = BASE + r"\Hydraulic\Claude\W3\shp\Unparceled_Buildings.shp"
BOUNDARY = BASE + r"\Hydraulic\SHP\temp\Netwrok desing test boudary.shp"
TERRAIN = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"
HAZARD = BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif"                    # 50-year flood grid
ACCOUNTS = BASE + r"\Hydraulic\Claude\W4\shp\ELE_accounts.shp"           # counted properties

OUT = BASE + r"\Hydraulic\Claude\W7"
OUT_SHP = OUT + r"\shp"
OUT_GEMS = OUT + r"\sewergems"
OUT_DXF = OUT + r"\dxf"
OUT_IMG = OUT + r"\img"
OUT_RUN = OUT + r"\run"

EPSG = 32640

# Outfall: the pipeline picks the lowest road point on the boundary. This is the point the
# user expects it near — reported for comparison, never used to force the choice.
# The main pipe is GIVEN, not derived (user 2026-08-20). Both legs drain to where they
# meet, and from there a 7.6 km trunk runs to the existing Ibri STP.
MAIN_PIPE = BASE + r"\Hydraulic\SHP\Main Pipe\Main Pipe.shp"
CONFLUENCE = (449124.6, 2567769.4)     # where the west and east legs meet = the outfall
STP = (444387.0185, 2563352.4576)      # existing Ibri STP, 7.6 km further on
MAIN_PIPE_LEAD_M = 1200.0              # how far outside the boundary to follow the trunk

# Crossing a dual carriageway normally needs trenchless work, which is expensive. At this
# underpass the pipe can go through in the open, so a crossing there costs nothing extra
# (user 2026-08-20).
UNDERPASSES = [(450375.24, 2568397.64)]

# Every join onto the main pipe becomes a chamber that will be deep once the whole town
# drains through it, so they are kept to the fewest that still works. Measured 2026-08-20:
# 30 joins is the floor for an all-gravity design; 28 or fewer costs a pumping station.
MAX_TRUNK_JOINS = 30

OUTFALL_EXPECTED = CONFLUENCE
OUTFALL_OVERRIDE = None

PF_FORMULA = "merrimack"

CLIP_SLIVER_M = 0.5
DUAL_MERGE_M = 35.0
NODE_SNAP_M = 0.5
