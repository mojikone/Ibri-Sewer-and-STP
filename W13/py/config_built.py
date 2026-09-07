"""Stage A settings for the BUILT AREA: the ground the 2006 network serves.

Paths and method settings only; design values live in sewnet/criteria.py.
The area is every street within AREA_BUFFER_M of a built 2006 sewer, holes filled
(engineer, 2026-09-07). Targets are the main pipe and the STP.
"""

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"

# the draftsman's road network (W13_DESIGN_LOGIC.md, Inputs)
ROADS_DXF = BASE + r"\Hydraulic\DWG\road network 03092026 eyeballed.dxf"
ROAD_LAYERS = {"piping center line": "existing",
               "piping center line-propo-01": "proposed"}

BUILT_SEWER = BASE + r"\Hydraulic\Claude\W7\shp\EXISTING_SEWERLINE.shp"
BUILT_FORCE = BASE + r"\Hydraulic\Claude\W7\shp\EXISTING_FORCELINE.shp"
MAIN_PIPE = BASE + r"\Hydraulic\SHP\Main Pipe\Main Pipe.shp"
STP = (444387.0185, 2563352.4576)          # existing Ibri STP
TERRAIN = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"
HAZARD = BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif"
PLOTS_CLASS = BASE + r"\Hydraulic\Claude\W3\shp\MoH_Plots_class_v4.shp"

OUT = BASE + r"\Hydraulic\Claude\W13"
OUT_SHP = OUT + r"\shp"
OUT_DXF = OUT + r"\dxf"
OUT_IMG = OUT + r"\img"
OUT_RUN = OUT + r"\run"
EPSG = 32640

# ---- the area
AREA_BUFFER_M = 60.0

# ---- rule 1: reading the ground
SNAP_M = 3.0            # line ends this close are one node (57 gaps of 0.3-3 m in the DXF)
GROUND_RES_M = 2.0      # the terrain is read once at this cell size over the area
PROFILE_STEP_M = 5.0    # sampling step along a run
CREST_M = 0.5           # an interior high or low this far above/below BOTH ends splits the run
MIN_SPLIT_M = 30.0      # never leave a piece shorter than this
FLAT_PCT = 0.5          # flatter than the DN200 minimum gradient (G203-p29 Table 11)
LEVEL_M = 0.10          # a fall below this is terrain noise, not a direction

# ---- rule 2: outlets
TARGET_M = 30.0         # a junction this close to the drawn main pipe is a join (the main
                        # pipe is an eyeballed line; a 24 km catchment ended 23 m short of
                        # it at 12 m — measured 2026-09-07)
STP_M = 250.0           # a junction this close to the STP drains to the STP
HOLLOW_M = 2.0          # a sink that spills with this much fill or less is a hollow the pipe
                        # crosses by depth, not an outlet; deeper stays a SINK (Stage A method
                        # choice, 2026-09-07 — Stage B decides what a real basin costs)

# ---- the guide picture: terrain streams
STREAM_RES_M = 4.0
STREAM_THRESHOLD_CELLS = 3000   # about 4.8 ha of contributing area at 4 m
STREAM_PAD_M = 1000.0           # read beyond the area so edge flow is not cut
