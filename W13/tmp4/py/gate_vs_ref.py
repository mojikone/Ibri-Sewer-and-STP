"""gate_vs_ref — the layout check of this temp folder against the last accepted one (2026-09-12).

The accepted folders are frozen (temp 2 on 2026-09-09, temp 3 on 2026-09-12). Every change
here is measured against the last of them, or against any of them by name: the subnetworks, the length by role, and how much of each network lies on the
other's pipes (within 1 m, same role). Reads temp 2's outputs, never writes to them.

    python gate_vs_ref.py [tmp3]      prints the table and writes run/gate_vs_<ref>.json
"""
import json
import os
import sys

import geopandas as gpd
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
T3 = os.path.dirname(HERE)
REF = sys.argv[1] if len(sys.argv) > 1 else "tmp3"
T2 = os.path.join(os.path.dirname(T3), REF)
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
        out["roles"][r] = {"km_ref": round(ka, 1), "km_this": round(kb, 1),
                           "this_on_ref_same_role_pct": round(100 * b_on_a / kb, 1) if kb else None,
                           "ref_on_this_same_role_pct": round(100 * a_on_b / ka, 1) if ka else None}
    kb_all = pb.length.sum()
    out["this_on_any_ref_pipe_pct"] = round(100 * sum(g.intersection(all_a).length for g in pb.geometry) / kb_all, 1)
    out["ref_on_any_this_pipe_pct"] = round(100 * sum(g.intersection(all_b).length for g in pa.geometry) / pa.length.sum(), 1)
    with open(os.path.join(T3, "run", f"gate_vs_{REF}.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"{'':28s}{REF:>10s}{'this':>10s}")
    for k in ("subnetworks", "chambers", "deepest_m", "over_12m"):
        print(f"{k:28s}{out[k][0]!s:>10s}{out[k][1]!s:>10s}")
    print(f"by type {REF}:", out["by_type"][0]); print("by type this:", out["by_type"][1])
    for r, v in out["roles"].items():
        print(f"{r:10s} km {v['km_ref']:>6} -> {v['km_this']:>6}   on the same role: "
              f"this on {REF} {v['this_on_ref_same_role_pct']} %, {REF} on this {v['ref_on_this_same_role_pct']} %")
    print(f"any pipe: this on {REF} {out['this_on_any_ref_pipe_pct']} %, {REF} on this {out['ref_on_any_this_pipe_pct']} %")


if __name__ == "__main__":
    sys.exit(main())
