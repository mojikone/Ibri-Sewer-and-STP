"""Engineering shapefiles (geopandas, UTF-8 + .cpg, EPSG:32640). Field names <=10 chars."""

import os

import geopandas as gpd
from shapely.geometry import LineString, Point

from .criteria import DEFAULT
from .model import Network

CRS = "EPSG:32640"


def _snap_ends(net: Network):
    """Exact vertex coincidence pipe-end <-> chamber (SewerGEMS + CAD hygiene)."""
    for r in net.reaches:
        cs = list(r.geom.coords)
        cs[0] = net.chambers[r.up].xy
        cs[-1] = net.chambers[r.dn].xy
        r.geom = LineString(cs)


def write_all(out_dir, net: Network, riders, still_low, pockets, boundary, of_rep,
              crit=DEFAULT, spurs=None, stubs=None, hazard=None, catchments=None,
              trunk_keys=None, trunk_wkt=None):
    os.makedirs(out_dir, exist_ok=True)
    _snap_ends(net)
    ch = list(net.chambers.values())

    gpd.GeoDataFrame({
        "LABEL": [c.label for c in ch],
        "KIND": [c.kind for c in ch],
        "GND": [round(c.z, 3) for c in ch],
        "INVERT": [round(c.invert, 3) if c.invert is not None else None for c in ch],
        "DEPTH": [round(c.depth, 2) if c.depth is not None else None for c in ch],
        "N_DROPS": [len(c.drops) for c in ch],
        "VORTEX": [int(any(d["type"] == "vortex" for d in c.drops)) for c in ch],
        "SLS_POCKET": [int(c.sls_pocket) for c in ch],
        "IS_PUMP": [int(c.is_station) for c in ch],
        "LIFT_M": [round(c.lift_m, 2) for c in ch],
        "ON_TRUNK": [int(c.on_trunk) for c in ch],      # sits on the main pipe
        "SUBNET": [c.subnet for c in ch],               # which subnetwork it drains through
        "SHARP_IN": [int(c.sharp_inlet) for c in ch],   # needs a curved-channel chamber
        "HAZ_CLASS": [hazard.klass(c.x, c.y) if hazard else 0 for c in ch],
        "IN_WADI": [int(hazard.is_wadi(c.x, c.y)) if hazard else 0 for c in ch],
    }, geometry=[Point(c.xy) for c in ch], crs=CRS).to_file(
        os.path.join(out_dir, "W7_manholes.shp"), encoding="utf-8")

    R = net.reaches
    gpd.GeoDataFrame({
        "LABEL": [r.label for r in R],
        "ND_UP": [net.chambers[r.up].label for r in R],
        "ND_DN": [net.chambers[r.dn].label for r in R],
        "DN_MM": [r.dn_mm for r in R],
        "MAT": [r.material for r in R],
        "LEN_M": [round(r.length, 2) for r in R],
        "SLOPE_PMIL": [round(r.slope * 1000, 3) for r in R],
        "INV_UP": [round(r.inv_up, 3) for r in R],
        "INV_DN": [round(r.inv_dn, 3) for r in R],
        "N_PROPS": [int(r.n_props) for r in R],
        "QADF_M3D": [round(r.qadf_m3d, 2) for r in R],
        "PF": [round(r.pf, 2) for r in R],
        "PF_PELT": [round(r.pf_peltier, 2) for r in R],
        "QPEAK_LS": [round(r.qpeak_ls, 2) for r in R],
        "VEL_MS": [round(r.vel, 2) if r.vel else None for r in R],
        "DOD": [round(r.dod, 3) if r.dod else None for r in R],
        "ON_TRUNK": [int(r.on_trunk) for r in R],       # this pipe IS the main pipe
        "SUBNET": [r.subnet for r in R],                # which subnetwork it belongs to
        "IS_JOIN": [int((not net.chambers[r.up].on_trunk)
                        and net.chambers[r.dn].on_trunk) for r in R],
        "IS_XING": [int(r.is_crossing) for r in R],     # crosses a dual carriageway
        "RISE_MAIN": [int(r.is_rising_main) for r in R],
        "QDUTY_LS": [round(r.q_duty_m3s * 1000.0, 2) for r in R],
        "DROP_UP": [round(r.drop_up, 2) for r in R],
        "DROP_DN": [round(max(r.drop_dn, 0.0), 2) for r in R],
    }, geometry=[r.geom for r in R], crs=CRS).to_file(
        os.path.join(out_dir, "W7_pipes.shp"), encoding="utf-8")

    # ---- house connections go in their OWN files, never mixed with the sewers, so
    # SewerGEMS never imports them as pipes and CAD can switch them off (user rule)
    if riders:
        gpd.GeoDataFrame({
            "MH": [r["mh"] for r in riders],
            "N_UNITS": [r["n_units"] for r in riders],
            "LEN_M": [round(r["length"], 1) for r in riders],
            "FLAG": [r["flag"] for r in riders],
        }, geometry=[r["geom"] for r in riders], crs=CRS).to_file(
            os.path.join(out_dir, "W7_tertiary_riders.shp"), encoding="utf-8")
    if spurs:
        gpd.GeoDataFrame({
            "PLOT": [s["plot"] for s in spurs], "MH": [s["mh"] for s in spurs],
            "CLS": [s["cls"] for s in spurs],
            "N_PROPS": [round(s["n_props"], 1) for s in spurs],
            "LEN_M": [round(s["len_m"], 1) for s in spurs],
            "FLAG": [s["flag"] for s in spurs],
        }, geometry=[s["geom"] for s in spurs], crs=CRS).to_file(
            os.path.join(out_dir, "W7_tertiary_connections.shp"), encoding="utf-8")
    if stubs:
        gpd.GeoDataFrame({
            "PLOT": [s["plot"] for s in stubs], "MH": [s["mh"] for s in stubs],
            "LEN_M": [round(s["len_m"], 1) for s in stubs],
        }, geometry=[s["geom"] for s in stubs], crs=CRS).to_file(
            os.path.join(out_dir, "W7_tertiary_stubouts.shp"), encoding="utf-8")

    if still_low:
        gpd.GeoDataFrame({
            "UNIT_ID": [str(r["id"]) for r in still_low],
            "MH": [r["mh"] for r in still_low],
            "MARGIN_M": [round(r["margin"], 2) for r in still_low],
        }, geometry=[Point(r["x"], r["y"]) for r in still_low], crs=CRS).to_file(
            os.path.join(out_dir, "W7_lowplots.shp"), encoding="utf-8")

    if catchments:
        # the ground each subnetwork collects from, one clean polygon per connection
        # into the main pipe (user 2026-08-20)
        gpd.GeoDataFrame({
            "CATCH_ID": [c["cid"] for c in catchments],
            "JOIN_MH": [c["join_mh"] for c in catchments],
            "INLET": [c["inlet_pipe"] for c in catchments],
            "INLET_DN": [c["inlet_dn"] for c in catchments],
            "AREA_HA": [c["area_ha"] for c in catchments],
            "N_PLOTS": [c["n_plots"] for c in catchments],
            "N_PROPS": [c["n_props"] for c in catchments],
            "TRUNK_PR": [c["trunk_props"] for c in catchments],
            "N_STUBS": [c["n_stubs"] for c in catchments],
            "QADF_M3D": [c["qadf_m3d"] for c in catchments],
            "QPEAK_LS": [c["qpeak_ls"] for c in catchments],
            "N_MH": [c["n_chambers"] for c in catchments],
            "PIPE_M": [c["pipe_m"] for c in catchments],
            "DEEPEST_M": [c["deepest_m"] for c in catchments],
            "PUMPED": [c["pumped"] for c in catchments],
            "STATIONS": [c["stations"] for c in catchments],
        }, geometry=[c["geom"] for c in catchments], crs=CRS).to_file(
            os.path.join(out_dir, "W7_catchments.shp"), encoding="utf-8")

    if trunk_wkt:
        # the main pipe exactly as drawn, so it can be checked against the source
        from shapely import wkt as _wkt
        gs = [_wkt.loads(w) for w in trunk_wkt]
        gpd.GeoDataFrame({"PART": list(range(1, len(gs) + 1)),
                          "LEN_M": [round(g.length, 1) for g in gs]},
                         geometry=gs, crs=CRS).to_file(
            os.path.join(out_dir, "W7_main_pipe.shp"), encoding="utf-8")

    sharp = [c for c in ch if c.sharp_inlet]
    if sharp:
        # every chamber where a pipe arrives at less than the inlet-angle rule allows.
        # These are NOT fixed by adding chambers (user 2026-08-20) — they go on the
        # chamber schedule for a purpose-made unit with a curved channel.
        gpd.GeoDataFrame({
            "LABEL": [c.label for c in sharp],
            "SUBNET": [c.subnet for c in sharp],
            "GND": [round(c.z, 2) for c in sharp],
            "DEPTH_M": [round(c.depth or 0, 2) for c in sharp],
            "NOTE": ["curved-channel chamber: inlet under "
                     f"{crit.INLET_MIN_DEG:.0f} deg" for _ in sharp],
        }, geometry=[Point(c.xy) for c in sharp], crs=CRS).to_file(
            os.path.join(out_dir, "W7_sharp_inlets.shp"), encoding="utf-8")

    stations = [c for c in ch if c.is_station]
    if stations:
        rm = {r.up: r for r in net.reaches if r.is_rising_main}
        gpd.GeoDataFrame({
            "LABEL": [c.label for c in stations],
            "GND": [round(c.z, 2) for c in stations],
            "DEPTH_M": [round(c.depth or 0, 2) for c in stations],
            "LIFT_M": [round(c.lift_m, 2) for c in stations],
            "RM_LEN_M": [round(rm[c.key].length, 1) if c.key in rm else 0 for c in stations],
            "RM_DN_MM": [rm[c.key].dn_mm if c.key in rm else 0 for c in stations],
            "QDUTY_LS": [round(rm[c.key].q_duty_m3s * 1000.0, 2) if c.key in rm else 0
                         for c in stations],
            "N_PROPS": [int(rm[c.key].n_props) if c.key in rm else 0 for c in stations],
            "DISCH_MH": [net.chambers[rm[c.key].dn].label if c.key in rm else ""
                         for c in stations],
        }, geometry=[Point(c.xy) for c in stations], crs=CRS).to_file(
            os.path.join(out_dir, "W7_pumping_stations.shp"), encoding="utf-8")

    if pockets:
        gpd.GeoDataFrame({
            "SITE_MH": [net.chambers[p["site"]].label for p in pockets],
            "N_NODES": [len(p["nodes"]) for p in pockets],
            "N_PROPS": [int(p["n_props"]) for p in pockets],
            "ABSORB": [int(p["absorb"]) for p in pockets],
        }, geometry=[Point(net.chambers[p["site"]].xy) for p in pockets],
            crs=CRS).to_file(os.path.join(out_dir, "W7_sls_candidates.shp"), encoding="utf-8")

    gpd.GeoDataFrame({"LABEL": ["OF-1"], "GND": [round(of_rep["z"], 3)],
                      "DIST_EXP": [round(of_rep.get("dist_to_expected_m", -1), 1)]},
                     geometry=[Point(of_rep["x"], of_rep["y"])], crs=CRS).to_file(
        os.path.join(out_dir, "W7_outfall.shp"), encoding="utf-8")

    gpd.GeoDataFrame({"NAME": ["test boundary (repaired)"]}, geometry=[boundary],
                     crs=CRS).to_file(os.path.join(out_dir, "W7_boundary.shp"),
                                      encoding="utf-8")
