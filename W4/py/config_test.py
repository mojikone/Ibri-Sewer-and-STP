"""W4 test-boundary run configuration. Paths only — design values live in sewnet.criteria."""

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"

ROADS = BASE + r"\Hydraulic\Claude\W1\shp\roads_study.shp"
PLOTS_CLASS = BASE + r"\Hydraulic\Claude\W3\shp\MoH_Plots_class_v4.shp"   # read with encoding='utf-8'
UNPARCELED = BASE + r"\Hydraulic\Claude\W3\shp\Unparceled_Buildings.shp"
BOUNDARY = BASE + r"\Hydraulic\SHP\temp\Netwrok desing test boudary.shp"
TERRAIN = BASE + r"\Data\Terrain\Sat_0p5m\IBRI_0p5_VRT2.vrt"

OUT = BASE + r"\Hydraulic\Claude\W4"
OUT_SHP = OUT + r"\shp"
OUT_GEMS = OUT + r"\sewergems"
OUT_DXF = OUT + r"\dxf"
OUT_IMG = OUT + r"\img"
OUT_RUN = OUT + r"\run"          # audit CSVs, logs, intermediates

EPSG = 32640

# Outfall: auto-pick lowest boundary road node; user expectation for the cross-check REPORT
# (user 2026-08-18 — report only, never stop):
OUTFALL_EXPECTED = (449915.23, 2567618.10)
OUTFALL_OVERRIDE = None          # (x, y) to force a node; None = auto lowest

PF_FORMULA = "merrimack"         # 'merrimack' (default, G1-p71) | 'peltier' (comparison in report either way)

# prep tuning (method choices, not standards)
CLIP_SLIVER_M = 0.5              # drop clipped road fragments shorter than this
DUAL_MERGE_M = 35.0              # dual-carriageway node-cluster merge radius (W2 s3 value)
NODE_SNAP_M = 0.5                # road graph node snap
