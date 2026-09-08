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
STP_INVERT_M = 323.0     # the inlet manhole 5A-1-FL-STP: both built trunks end there with a
                         # downstream invert of 322.7-323.0 m and ground 325.0 m (as-built,
                         # 2026-09-07). The terrain at the STP point reads 329.0 m; gravity is
                         # judged against the invert, not the ground.
TERRAIN = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"
HAZARD = BASE + r"\Data\04 Lekhuwair\Hazard_T50y.tif"
PLOTS_CLASS = BASE + r"\Hydraulic\Claude\W3\shp\MoH_Plots_class_v4.shp"
ACCOUNTS = BASE + r"\Hydraulic\Claude\W4\shp\ELE_accounts.shp"   # counted properties

# ---- rule 9, the depth check done on every run (quicklay.py)
PER_PROPERTY_M3D = 0.911   # 5.32 people x 171.3 L/c/d, the locked load basis
MAX_DEPTH_M = 12.0         # the hard limit (standing decision 2026-09-07)
TRUNK_COVER_M = 1.55       # cover to invert a trunk starts with at its pocket (Stage A proxy)
TRUNK_MAX_M = 8000.0       # no designed trunk longer than this (NAMA's own is 6.2 km)
TRUNK_TRY = 0              # targets tried per pocket, cheapest first; 0 = every target
TRUNK_VIOLATION_MAX_M = 10.0  # ... but not past this many metres of depth excess plus arrival
                           # shortfall: beyond it no gravity story is credible and the pocket
                           # stays a pocket for a pump (a 177-property pocket took a 19 m
                           # violation over the west's trunk and dragged it to 26.8 m, 2026-09-08)
TRUNK_TAKE_SHORTFALL = True  # a pocket takes the route with the smallest arrival shortfall
                           # when none clears its target's level, within 12 m everywhere
                           # (engineer, 2026-09-08: everything on gravity, show the depth)
REROUTE_ROUNDS = 12        # (engineer, 2026-09-08: whatever reaches an outlet within 12 m connects,
                           # the rest is a pump candidate) rounds after the lay in which the basin
                           # behind each chamber past 12 m becomes a pump candidate and the rest is
                           # laid again. Was 0: rule 10's rounds of reroute after the lay.
REROUTE_MODE = "cut"      # "cut": no trunk is built for the basin, it becomes a pump candidate;
                           # "trunk": W13's way, a designed trunk is tried first
                           # 0 since 2026-09-08 (engineer): the gravity layout first, pumps later;
                           # rule 10's rounds planted eight short DN200 trunks across the west
REROUTE_BASINS = 1         # basins per failing catchment per round, largest fill first

OUT = BASE + r"\Hydraulic\Claude\W14"
OUT_SHP = OUT + r"\shp"
OUT_DXF = OUT + r"\dxf"
OUT_IMG = OUT + r"\img"
OUT_RUN = OUT + r"\run"
EPSG = 32640

# ---- the area
AREA_SHP = BASE + r"\Hydraulic\SHP\temp\W13 test boundary.shp"   # the engineer's test
                        # boundary (2026-09-08): 21.4 km2 in two parts, holding the two
                        # settlements, the STP and the roads to it. None: the built envelope.
AREA_BUFFER_M = 60.0    # the built envelope: every street within this of a 2006 sewer; now
                        # the comparison layer, not the area
NAMA_ROW_M = 1500.0     # NAMA's built trunk within this of the works is a right-of-way the
                        # network may use for its last kilometre (engineer, 2026-09-08): the
                        # road into the plant dips to 324.2 m, NAMA's line never below 325.2
MP_PROFILE_GRAD = None     # (set aside 2026-09-08, engineer: sub-networks first, their levels at
                        # the main pipe later; was 0.00125) the main pipe's own gravity profile
                        # back from the inlet, a DN600
                        # class trunk (G203-p29 Table 11); a join cannot sit below it. An
                        # optimistic floor: a bigger main pipe is flatter and the floor higher
USE_CORRIDOR = False    # NAMA's built trunk to the STP was a route with no design (engineer,
                        # 2026-09-08); the STP is reached by a pipe designed along the roads

# streets the engineer adds by hand, as (x, y) pairs, UTM 40N (2026-09-08: a 187 m link that
# may let the low ground west of the settlement, C06, drain by gravity)
EXTRA_LINES = []   # the 187 m link tried for C06 on 2026-09-08 did not help; withdrawn by the engineer

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
ASSIGN_BY_DEPTH = True  # kept from later (2026-09-09): with the low ground west of the settlement
                        # inside the boundary, the flood sends the whole west into that low and
                        # the 12 m rule pumps 112 km; the least-depth choice routes it to the works.
                        # Outlets by rule 5's least-depth cost (DEPTH_WEIGHT, SMIN_PROXY) rather
                        # than by the priority flood, which gives a whole slope to its lowest
                        # join (2026-09-07). False restores the flood.
BASIN_MAX_M = 10.0      # a basin needing more than this becomes a pocket, and a pocket is
                        # offered a designed trunk (rule 3) before it is allowed to drain
                        # anywhere else; with everything on gravity (engineer, 2026-09-08) the
                        # trunk is taken even when it arrives under the target's level, and
                        # the shortfall is reported. Tried without the cap the same day: the
                        # west went 6 km east to a ridge join at 37 m. Was: a pocket for a
                        # pump or a cut:
                        # with 1.3 m of cover it would pass the 12 m limit (rule 10)
CORRIDOR_ENTRY_M = 600.0  # a direct link may reach NAMA's built trunk corridor within this
                          # distance and follow it to the STP (rule 3, 2026-09-07)
CORRIDOR_MIN_GRAD = 0.00125  # a trunk along the corridor is DN600 class: Table 11 minimum
CORRIDOR_MAX_M = 6500.0      # NAMA's own western trunk runs 5.65 km along its corridor

# ---- W14 trial (2026-09-08): sub-mains first, then hang the rest off them
RECIPE = "7 September evening"  # the layout the engineer approved (commit 3897c0e): the flood
                         # gives every street one outlet, a street is a whole sub-main cut only
                         # at a crest, attached where it touches the outlet or a sub-main; no
                         # connectors, no per-node outlet choice, no rule 10 trunks (2026-09-09)
SAG_OUTLET_CUTS = False  # the cuts at a sag or a change of outlet (off in that recipe)
TRUNK_FROM_EXIT = False  # (tried 2026-09-09, misfired: picked the south-east tip and sent the west to a ridge join at 24 m) a pocket's trunk starts at its exit, the member nearest the works in
                         # depth terms, not at its lowest hollow (the 7 September picture)
CHAIN_ORIENT = "fall"    # ("outlet" tried 2026-09-09: fewer sub-mains, 12 pumps; the theory that it restored the cross streets was wrong) a street's lower end is the end nearer the outlet along the flood
                         # tree (the recipe); "fall" = the end its own decided runs fall to
SKELETON_FIRST = False   # the long straight streets are attached to an outlet or to a bigger
                         # street first, longest first; every other street drains to the
                         # nearest skeleton node; catchments follow the skeleton. False = W13's
                         # way: every node picks its outlet first
POCKET_BY_DEPTH = True   # a basin is a pocket when its fill plus the fall at 0.5 % from its low
                         # to its rim, plus cover, passes 12 m (the engineer's line, 2026-09-08)
SKEL_LINK_M = 300.0      # how far a street's foot may travel along other streets to reach the
                         # skeleton (the connector becomes sub-main)

# ---- rules 3-5: the tree (Stage A rerun, 2026-09-07)
JOIN_SPACING_M = 150.0    # a join is kept only this far from a bigger one (NAMA: median 167 m)
STEM_MIN_M = 600.0        # (heaviest-stem method, superseded 2026-09-07 by street chains)
SIDE_STEM_MIN_M = 1500.0  # (idem)
STRAIGHT_DEG = 25.0       # a street continues through a junction within this deflection
CHAIN_MIN_M = 250.0       # a sub-main is a straight street chain at least this long that
                          # attaches to the outlet or to a sub-main already chosen (engineer,
                          # 2026-09-07: "long run with less bends")
CHAIN_LINK_M = 0.0        # (off in the 7 September recipe; was 250) a chain whose foot is within this of a sub-main along the flood
                          # tree attaches through that connector, which becomes sub-main too
SUBMAIN_DISCOUNT = 0.5    # a sub-main run costs this fraction of a lateral run in the route
                          # search: the collector is preferred, its length still counts
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
