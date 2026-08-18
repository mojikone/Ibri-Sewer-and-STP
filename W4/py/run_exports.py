"""W4 exports: SHP + SewerGEMS package + DXF + PNG maps, from run/state.pkl."""

import os
import pickle
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_test as cfg
from shapely import wkt
from sewnet import export_shp, export_gems, export_dxf, maps

T0 = time.time()


def log(m):
    print(f"[{time.time()-T0:6.1f}s] {m}", flush=True)


def main():
    st = pickle.load(open(os.path.join(cfg.OUT_RUN, "state.pkl"), "rb"))
    nodes, pipes = st["nodes"], st["pipes"]
    boundary = wkt.loads(st["boundary_wkt"])
    summary = st["summary"]

    # rebuild per_mh with node keys (state stores label lists) — reconstruct from conn
    per_mh_units = {}
    for r in st["conn"]:
        per_mh_units.setdefault(r["mh_key"], []).append(r)

    log("SHP ...")
    export_shp.write_all(cfg.OUT_SHP, nodes, pipes, st["riders"], st["still_low"],
                         st["pockets"], boundary, st["of_rep"])
    log("SewerGEMS package ...")
    n_loads = export_gems.write_all(cfg.OUT_GEMS, nodes, pipes, per_mh_units,
                                    st["of_rep"], st["outfall"])
    log(f"  {n_loads} load rows")
    log("DXF ...")
    os.makedirs(cfg.OUT_DXF, exist_ok=True)
    export_dxf.write(os.path.join(cfg.OUT_DXF, "W4_test_boundary_design.dxf"),
                     nodes, pipes, st["riders"], st["pockets"], st["of_rep"])
    log("maps ...")
    os.makedirs(cfg.OUT_IMG, exist_ok=True)
    maps.network_map(os.path.join(cfg.OUT_IMG, "W4_M1_network_by_dn.png"),
                     nodes, pipes, st["pockets"], st["of_rep"], boundary, summary)
    maps.depth_map(os.path.join(cfg.OUT_IMG, "W4_M2_depth.png"), nodes, pipes, boundary, summary)
    maps.lowplot_map(os.path.join(cfg.OUT_IMG, "W4_M3_connectability.png"),
                     nodes, pipes, st["conn"], st["still_low"], boundary, summary)
    log("done")


if __name__ == "__main__":
    main()
