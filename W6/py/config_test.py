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

OUT = BASE + r"\Hydraulic\Claude\W6"
OUT_SHP = OUT + r"\shp"
OUT_GEMS = OUT + r"\sewergems"
OUT_DXF = OUT + r"\dxf"
OUT_IMG = OUT + r"\img"
OUT_RUN = OUT + r"\run"

EPSG = 32640

# Outfall: the pipeline picks the lowest road point on the boundary. This is the point the
# user expects it near — reported for comparison, never used to force the choice.
OUTFALL_EXPECTED = (449915.23, 2567618.10)
OUTFALL_OVERRIDE = None

PF_FORMULA = "merrimack"

CLIP_SLIVER_M = 0.5
DUAL_MERGE_M = 35.0
NODE_SNAP_M = 0.5
