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
MAIN_PIPE = BASE + r"\Hydraulic\SHP\Main Pipe\Main Pipe.shp"   # the new main pipe (redrawn 2026-09-08)
STP = (444387.0185, 2563352.4576)          # existing Ibri STP
STP_INVERT_M = 323.0     # the inlet manhole 5A-1-FL-STP: both built trunks end there with a
                         # downstream invert of 322.7-323.0 m and ground 325.0 m (as-built,
                         # 2026-09-07). The terrain at the STP point reads 329.0 m; gravity is
                         # judged against the invert, not the ground.
TERRAIN = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"
HAZARD = BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif"
PLOTS_CLASS = BASE + r"\Hydraulic\Claude\W3\shp\MoH_Plots_class_v4.shp"

OUT = BASE + "/Hydraulic/Claude/W13/tmp1"   # this temporary folder only
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
HOLLOW_M = 2.0          # a dip needing this much fill or less is not even marked; deeper ones
                        # are MARKED as basins with their extra depth, but still drain over
                        # their rim into the neighbouring sub-network (engineer, 2026-09-07:
                        # a sub-network is what connects to the main pipe, not a local sink)
BASIN_MAX_M = 10.0      # a basin needing more than this stays a pocket for a pump or a cut:
                        # with 1.3 m of cover it would pass the 12 m limit (rule 10)
CORRIDOR_ENTRY_M = 600.0  # a direct link may reach NAMA's built trunk corridor within this
                          # distance and follow it to the STP (rule 3, 2026-09-07)
CORRIDOR_MIN_GRAD = 0.00125  # a trunk along the corridor is DN600 class: Table 11 minimum
CORRIDOR_MAX_M = 6500.0      # NAMA's own western trunk runs 5.65 km along its corridor

# ---- rules 3-5: the tree (Stage A rerun, 2026-09-07)
JOIN_SPACING_M = 150.0    # a join is kept only this far from a bigger one (NAMA: median 167 m)
STEM_MIN_M = 600.0        # (heaviest-stem method, superseded 2026-09-07 by street chains)
SIDE_STEM_MIN_M = 1500.0  # (idem)
STRAIGHT_DEG = 25.0       # a street continues through a junction within this deflection
CHAIN_MIN_M = 250.0       # a sub-main is a straight street chain at least this long that
                          # attaches to the outlet or to a sub-main already chosen (engineer,
                          # 2026-09-07: "long run with less bends")
DEPTH_WEIGHT = 500.0      # route cost per metre of trench depth a street forces (W8)
SMIN_PROXY = 0.005        # the DN200 minimum gradient the depth cost is measured against
GATE_SEARCH_M = 45.0      # how far off a street a house gate may sit (W8)
FANOUT_OFFSET_M = 10.0    # a head with no gate starts this far from the junction (W8)
BRANCH_MIN_M = 15.0       # a leftover street shorter than this cannot carry a head; reported
LINK_MIN_GRAD = 0.002     # a direct link (rule 3) is a large pipe; feasible by gravity when the
                          # outlet's ground falls to the target at this gradient over the straight
                          # distance (DN400 class, G203-p29 Table 11; Stage A method choice)
MP_INVERT_DEPTH_M = 3.0   # the main pipe is a trunk laid at least this deep, so a link is measured
                          # against its invert, not the ground at its foot (stated allowance)
LINK_MAX_M = 4000.0       # no direct link longer than NAMA's own trunk from the west settlement
                          # to the STP; anything further is Stage B's routed spine
LINK_MP_MAX_M = 150.0     # a direct link to the main pipe is for a sub-network VERY close to it
                          # with no road between (engineer, 2026-09-07); farther, or with a
                          # street across the line, the water goes by the streets
LINK_PLOT_PAD_M = 5000.0  # how far round the area plots are loaded for the no-plot-in-the-way test

# ---- the guide picture: terrain streams
STREAM_RES_M = 4.0
STREAM_THRESHOLD_CELLS = 3000   # about 4.8 ha of contributing area at 4 m
STREAM_PAD_M = 1000.0           # read beyond the area so edge flow is not cut
