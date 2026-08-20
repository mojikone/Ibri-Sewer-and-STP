"""W7 exports: SHP + SewerGEMS package + DXF + PNG maps, from run/state.pkl."""

import os
import pickle
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config_test as cfg
from shapely import wkt
from sewnet import catchments, export_shp, export_gems, export_dxf, maps

T0 = time.time()


def log(m):
    print(f"[{time.time()-T0:6.1f}s] {m}", flush=True)


def main():
    st = pickle.load(open(os.path.join(cfg.OUT_RUN, "state.pkl"), "rb"))
    net = st["network"]
    boundary = wkt.loads(st["boundary_wkt"])
    summary = st["summary"]
    per_mh_units = st["per_chamber"]

    log("catchment boundaries ...")
    cats = catchments.build(net, per_mh_units, st["units"], st.get("trunk_keys", []),
                            boundary, stubs=st.get("stubs"))
    rep = catchments.check(cats, units_total=len(st["units"]))
    log(f"  {rep}")

    log("SHP ...")
    export_shp.write_all(cfg.OUT_SHP, net, st["riders"], st["still_low"],
                         st["pockets"], boundary, st["of_rep"],
                         spurs=st.get("spurs"), stubs=st.get("stubs"), catchments=cats,
                         trunk_keys=set(st.get("trunk_keys", [])),
                         trunk_wkt=st.get("trunk_wkt"))
    log("SewerGEMS package ...")
    n_loads = export_gems.write_all(cfg.OUT_GEMS, net, per_mh_units, st["of_rep"])
    log(f"  {n_loads} load rows")
    log("DXF ...")
    os.makedirs(cfg.OUT_DXF, exist_ok=True)
    export_dxf.write(os.path.join(cfg.OUT_DXF, "W7_test_boundary_design.dxf"),
                     net, st["riders"], st["pockets"], st["of_rep"], catchments=cats)
    log("maps ...")
    os.makedirs(cfg.OUT_IMG, exist_ok=True)
    maps.network_map(os.path.join(cfg.OUT_IMG, "W7_M1_network_by_dn.png"),
                     net, st["pockets"], st["of_rep"], boundary, summary)
    maps.depth_map(os.path.join(cfg.OUT_IMG, "W7_M2_depth.png"), net, boundary, summary)
    maps.lowplot_map(os.path.join(cfg.OUT_IMG, "W7_M3_connectability.png"),
                     net, st["conn"], st["still_low"], boundary, summary)
    maps.catchment_map(os.path.join(cfg.OUT_IMG, "W7_M4_catchments.png"),
                       net, cats, boundary, summary)
    log("done")


if __name__ == "__main__":
    main()
