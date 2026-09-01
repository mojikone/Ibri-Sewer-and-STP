"""W10 full-area run settings. Paths and site coordinates only.

Design values live in W8/py/sewnet/criteria.py, which W10 imports rather than copies.
W10 is the GREENFIELD design: the whole study area laid out as if the existing network
were not there. W11 will be the brownfield run that includes it.
"""

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"

# ---------------------------------------------------------------- corridors
# The draftsman's treated centre lines, delivered as DWG and DXF. Two layers, and both
# are design input (user 2026-09-01):
#   "piping center line"          - treated centre lines on EXISTING roads
#   "piping center line-propo-01" - roads that are missing from the road layer, and roads
#                                   in future developments. Every plot must be served, so
#                                   these are corridors in their own right, not proposals.
# He is still working, so anything we generate ourselves is tagged SRC=auto and kept in a
# separate layer, and his delivery re-merges without overwriting.
DXF_TREATED = BASE + r"\Hydraulic\DWG\treated roads partially 01092026.dxf"
DXF_LAYER_EXISTING = "piping center line"
DXF_LAYER_FUTURE = "piping center line-propo-01"

# raw road centre lines: `dual` says 1 = dual carriageway (no pipe of any kind may run
# along it), 2 = two-lane pair where only one side is used. The .prj is hand-written, so
# the CRS is set in code.
ROADS = BASE + r"\Hydraulic\SHP\Road centerline 2\Road_Centercline.shp"

# ---------------------------------------------------------------- area and cadastre
BOUNDARY = BASE + r"\Hydraulic\SHP\Study area\Project Boundary.shp"      # 531.4 km2
PLOTS_RAW = BASE + r"\Hydraulic\SHP\MoHUP_DATA\MoH_Plots.shp"            # 61,272 plots
PLOTS_CLASS = BASE + r"\Hydraulic\Claude\W3\shp\MoH_Plots_class_v4.shp"  # read as utf-8
UNPARCELED = BASE + r"\Hydraulic\Claude\W3\shp\Unparceled_Buildings.shp"
ACCOUNTS = BASE + r"\Hydraulic\Claude\W4\shp\ELE_accounts.shp"           # 33,970 properties

# ---------------------------------------------------------------- terrain and hazard
TERRAIN = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"             # 0.5 m, authoritative
HAZARD = BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif"                    # 50-year flood grid

# ---------------------------------------------------------------- the trunk
# Given by the user, not derived. 85.5 km in 54 pieces, and it falls in TWO disconnected
# components (measured 2026-09-01): the main body, and a western leg the user says is cut
# off by topography. W10 decides in Phase 5 whether the west leg is used, pumped or
# replaced by a satellite works.
MAIN_PIPE = BASE + r"\Hydraulic\SHP\Main Pipe\Main Pipe.shp"

# ---------------------------------------------------------------- known works
# All confirmed by the user 2026-09-01 and checked against the NAMA data the same day.
STP_EXISTING = (444422.8, 2563337.9)       # ground 328.7 m; 47 m from the 1,800 m3/d record
STP_PROPOSED_SOUTH = (442451.3, 2558941.8)  # ground 311.7 m; 4.8 km south, 17.3 m lower
PS_EXISTING = (449899.59, 2567301.72)      # ground 351.1 m; head of the built 10.0 km rising main

# ---------------------------------------------------------------- existing network
# Rebuilt from the NAMA KMZ. OP_STATUE splits it: '1' = built 2006, '0' = proposed SUREKHA.
# No diameter and no invert level is recorded on any built gravity segment, and NAMA's own
# remark reads "Data is not reliable and must be used only for reference purpose".
EXISTING_KMZ_DIR = BASE + r"\Data\Received\09-RECEIVED\NAMA\IBRI\WW\KMZ"
EXISTING_SHP_DIR = BASE + r"\Hydraulic\Claude\W7\shp"    # EXISTING_SEWERLINE / FORCELINE / STP_PT / TE_LINE

# ---------------------------------------------------------------- outputs
OUT = BASE + r"\Hydraulic\Claude\W10"
OUT_SHP = OUT + r"\shp"
OUT_DXF = OUT + r"\dxf"
OUT_IMG = OUT + r"\img"
OUT_RUN = OUT + r"\run"
OUT_DOCS = OUT + r"\docs"

EPSG = 32640

# ---------------------------------------------------------------- tolerances
CLIP_SLIVER_M = 0.5      # anything shorter than this after clipping is a clip artefact
NODE_SNAP_M = 0.5        # endpoints within this distance are the same node
CORRIDOR_MATCH_M = 25.0  # a drafted line this close to a road counts as covering it
PLOT_SERVED_M = 60.0     # a plot with no corridor within this distance is unserved
