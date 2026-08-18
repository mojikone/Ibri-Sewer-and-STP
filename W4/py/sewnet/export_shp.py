"""sewnet.export_shp — engineering shapefiles (geopandas, UTF-8 + .cpg, EPSG:32640).
Field names <= 10 chars (DBF)."""

import os
import geopandas as gpd
from shapely.geometry import Point, LineString

CRS = "EPSG:32640"


def _snap_pipe_ends(pipes, nodes):
    """Guarantee exact vertex coincidence pipe-end <-> manhole (SewerGEMS + CAD hygiene)."""
    for p in pipes:
        cs = list(p["geom"].coords)
        u, d = nodes[p["up"]], nodes[p["dn"]]
        cs[0] = (u["x"], u["y"])
        cs[-1] = (d["x"], d["y"])
        p["geom"] = LineString(cs)


def write_all(out_dir, nodes, pipes, riders, still_low, pockets, boundary, of_rep):
    os.makedirs(out_dir, exist_ok=True)
    _snap_pipe_ends(pipes, nodes)

    mh = gpd.GeoDataFrame({
        "LABEL": [n["label"] for n in nodes.values()],
        "KIND": [n["kind"] for n in nodes.values()],
        "GND": [round(n["z"], 3) for n in nodes.values()],
        "INVERT": [round(n["invert"], 3) if n.get("invert") is not None else None for n in nodes.values()],
        "DEPTH": [round(n["depth"], 2) if n.get("depth") is not None else None for n in nodes.values()],
        "N_DROPS": [len(n.get("drops", [])) for n in nodes.values()],
        "VORTEX": [int(any(d["type"] == "vortex" for d in n.get("drops", []))) for n in nodes.values()],
        "SLS_POCKET": [int(bool(n.get("sls_pocket"))) for n in nodes.values()],
    }, geometry=[Point(n["x"], n["y"]) for n in nodes.values()], crs=CRS)
    mh.to_file(os.path.join(out_dir, "W4_manholes.shp"), encoding="utf-8")

    pp = gpd.GeoDataFrame({
        "LABEL": [p["label"] for p in pipes],
        "ND_UP": [nodes[p["up"]]["label"] for p in pipes],
        "ND_DN": [nodes[p["dn"]]["label"] for p in pipes],
        "DN_MM": [p["dn_mm"] for p in pipes],
        "MAT": [p["material"] for p in pipes],
        "LEN_M": [round(p["length"], 2) for p in pipes],
        "SLOPE_PMIL": [round(p["slope"] * 1000, 3) for p in pipes],
        "INV_UP": [round(p["inv_up"], 3) for p in pipes],
        "INV_DN": [round(p["inv_dn"], 3) for p in pipes],
        "N_PROPS": [int(p["n_props"]) for p in pipes],
        "QADF_M3D": [round(p["qadf_m3d"], 2) for p in pipes],
        "PF": [round(p["pf"], 2) for p in pipes],
        "PF_PELT": [round(p["pf_peltier"], 2) for p in pipes],
        "QPEAK_LS": [round(p["qpeak_ls"], 2) for p in pipes],
        "VEL_MS": [round(p["vel"], 2) if p.get("vel") else None for p in pipes],
        "DOD": [round(p["dod"], 3) if p.get("dod") else None for p in pipes],
        "DROP_UP": [round(p.get("drop_up", 0.0), 2) for p in pipes],
    }, geometry=[p["geom"] for p in pipes], crs=CRS)
    pp.to_file(os.path.join(out_dir, "W4_pipes.shp"), encoding="utf-8")

    if riders:
        rd = gpd.GeoDataFrame({
            "MH": [r["mh"] for r in riders],
            "N_UNITS": [r["n_units"] for r in riders],
            "LEN_M": [round(r["length"], 1) for r in riders],
            "FLAG": [r["flag"] for r in riders],
        }, geometry=[r["geom"] for r in riders], crs=CRS)
        rd.to_file(os.path.join(out_dir, "W4_riders.shp"), encoding="utf-8")

    if still_low:
        lp = gpd.GeoDataFrame({
            "UNIT_ID": [str(r["id"]) for r in still_low],
            "MH": [r["mh"] for r in still_low],
            "MARGIN_M": [round(r["margin"], 2) for r in still_low],
        }, geometry=[Point(r["x"], r["y"]) for r in still_low], crs=CRS)
        lp.to_file(os.path.join(out_dir, "W4_lowplots.shp"), encoding="utf-8")

    if pockets:
        sls = gpd.GeoDataFrame({
            "SITE_MH": [nodes[p["site"]]["label"] for p in pockets],
            "N_NODES": [len(p["nodes"]) for p in pockets],
            "N_PROPS": [int(p["n_props"]) for p in pockets],
            "ABSORB": [int(p["absorb"]) for p in pockets],
        }, geometry=[Point(nodes[p["site"]]["x"], nodes[p["site"]]["y"]) for p in pockets], crs=CRS)
        sls.to_file(os.path.join(out_dir, "W4_sls_candidates.shp"), encoding="utf-8")

    of = gpd.GeoDataFrame({"LABEL": ["OF-1"], "GND": [round(of_rep["z"], 3)],
                           "DIST_EXP": [round(of_rep.get("dist_to_expected_m", -1), 1)]},
                          geometry=[Point(of_rep["x"], of_rep["y"])], crs=CRS)
    of.to_file(os.path.join(out_dir, "W4_outfall.shp"), encoding="utf-8")

    bd = gpd.GeoDataFrame({"NAME": ["test boundary (repaired)"]}, geometry=[boundary], crs=CRS)
    bd.to_file(os.path.join(out_dir, "W4_boundary.shp"), encoding="utf-8")
