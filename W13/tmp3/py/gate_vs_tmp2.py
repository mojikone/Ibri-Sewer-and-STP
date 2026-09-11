"""gate_vs_tmp2 — the layout check of W13 temp 3 against the accepted temp 2 (2026-09-11).

temp 2 is frozen as the network the engineer accepted. Every change in temp 3 is measured
against it: the subnetworks, the length by role, and how much of each network lies on the
other's pipes (within 1 m, same role). Reads temp 2's outputs, never writes to them.

    python gate_vs_tmp2.py            prints the table and writes run/gate_vs_tmp2.json
"""
import json
import os
import sys

import geopandas as gpd
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
T3 = os.path.dirname(HERE)
T2 = os.path.join(os.path.dirname(T3), "tmp2")
ROLES = ("trunk", "sub main", "lateral", "branch")


def role(gdf):
    return gdf["ROLE"] if "ROLE" in gdf.columns else gdf["TIER"]


def main():
    a = json.load(open(os.path.join(T2, "run", "stage_a.json")))
    b = json.load(open(os.path.join(T3, "run", "stage_a.json")))
    pa = gpd.read_file(os.path.join(T2, "shp", "W13_A_tree_pipes.shp"))
    pb = gpd.read_file(os.path.join(T3, "shp", "W13_A_tree_pipes.shp"))
    pa["R"], pb["R"] = role(pa), role(pb)
    out = {"subnetworks": [a["catchments"]["count"], b["catchments"]["count"]],
           "by_type": [a["catchments"]["by_type"], b["catchments"]["by_type"]],
           "deepest_m": [a["depth"]["depth_max_m"], b["depth"]["depth_max_m"]],
           "over_12m": [a["depth"]["over_limit"], b["depth"]["over_limit"]],
           "chambers": [a["depth"]["chambers"], b["depth"]["chambers"]],
           "roles": {}}
    all_a = unary_union(list(pa.geometry)).buffer(1.0)
    all_b = unary_union(list(pb.geometry)).buffer(1.0)
    for r in ROLES:
        ga, gb = pa[pa.R == r], pb[pb.R == r]
        ka, kb = ga.length.sum() / 1000, gb.length.sum() / 1000
        if ka == 0 and kb == 0:
            continue
        sa = unary_union(list(ga.geometry)).buffer(1.0) if len(ga) else None
        sb = unary_union(list(gb.geometry)).buffer(1.0) if len(gb) else None
        b_on_a = sum(g.intersection(sa).length for g in gb.geometry) / 1000 if sa is not None else 0.0
        a_on_b = sum(g.intersection(sb).length for g in ga.geometry) / 1000 if sb is not None else 0.0
        out["roles"][r] = {"km_tmp2": round(ka, 1), "km_tmp3": round(kb, 1),
                           "tmp3_on_tmp2_same_role_pct": round(100 * b_on_a / kb, 1) if kb else None,
                           "tmp2_on_tmp3_same_role_pct": round(100 * a_on_b / ka, 1) if ka else None}
    kb_all = pb.length.sum()
    out["tmp3_on_any_tmp2_pipe_pct"] = round(100 * sum(g.intersection(all_a).length for g in pb.geometry) / kb_all, 1)
    out["tmp2_on_any_tmp3_pipe_pct"] = round(100 * sum(g.intersection(all_b).length for g in pa.geometry) / pa.length.sum(), 1)
    with open(os.path.join(T3, "run", "gate_vs_tmp2.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"{'':28s}{'tmp2':>10s}{'tmp3':>10s}")
    for k in ("subnetworks", "chambers", "deepest_m", "over_12m"):
        print(f"{k:28s}{out[k][0]!s:>10s}{out[k][1]!s:>10s}")
    print("by type tmp2:", out["by_type"][0]); print("by type tmp3:", out["by_type"][1])
    for r, v in out["roles"].items():
        print(f"{r:10s} km {v['km_tmp2']:>6} -> {v['km_tmp3']:>6}   on the same role: "
              f"tmp3 on tmp2 {v['tmp3_on_tmp2_same_role_pct']} %, tmp2 on tmp3 {v['tmp2_on_tmp3_same_role_pct']} %")
    print(f"any pipe: tmp3 on tmp2 {out['tmp3_on_any_tmp2_pipe_pct']} %, tmp2 on tmp3 {out['tmp2_on_any_tmp3_pipe_pct']} %")


if __name__ == "__main__":
    sys.exit(main())
