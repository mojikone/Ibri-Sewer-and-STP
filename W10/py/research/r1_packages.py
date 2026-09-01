"""r1_packages — what a NAMA construction package actually IS, measured.

The built network (W10/shp/W10_existing_built.shp, 2006, project codes 5A-1 .. 5A-5)
is the only local evidence of how a sewer of this kind was cut into contracts. This
script measures it so W11a can partition 1,883 km on evidence rather than on taste.

It answers, per package:
  size        pipes, length, footprint area, plots and properties inside the footprint
  cleanliness do the packages overlap on the ground, or are they interleaved?
  hydraulics  is a package a complete drainage unit with ONE outlet, or an arbitrary
              slice of somebody else's catchment?
  data        do the levels exist, and what tiers are in it?

Topology comes from NAMA's own manhole IDs (US_MHID -> DS_MHID), which encode the
package, the zone and the tier: 5A-2-TM-MH185 = package 5A-2, trunk main, MH 185.

Outputs (W10/run/):
  research_packages_summary.csv     one row per package
  research_packages_overlap.csv     pairwise footprint overlap
  research_packages_topology.csv    cross-package pipe connections
  research_packages_outlets.csv     every package outlet, with its receiving package

Re-runnable:  python W10/py/research/r1_packages.py
"""

from __future__ import annotations

import os
import sys
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))          # .../W10
REPO = os.path.abspath(os.path.join(ROOT, ".."))                # .../Claude
SHP = os.path.join(ROOT, "shp")
RUN = os.path.join(ROOT, "run")

BUILT = os.path.join(SHP, "W10_existing_built.shp")
PLOTS = os.path.join(SHP, "W10_plot_loads.shp")

# how far from a pipe a plot is taken to be served by it. G203-p17 puts the House
# Connection Chamber 2.5 m inside the public right of way and G203-p22 Tab 6 caps a
# lateral at 45 m, so a plot more than ~50 m from any sewer is not on that sewer.
SERVE_M = 50.0
# footprint = the pipes buffered by half a typical block. Not a legal boundary, a
# measurable stand-in for "the ground this contract dug up".
FOOT_M = 100.0


def load():
    g = gpd.read_file(BUILT)
    g = g[g["IS_DUP"] == 0].copy() if "IS_DUP" in g.columns else g
    g["PKG"] = g["PROJECTCOD"].astype(str)
    return g


def footprints(g):
    out = {}
    for pkg, sub in g.groupby("PKG"):
        buf = unary_union(sub.geometry.buffer(FOOT_M))
        hull = unary_union(sub.geometry).convex_hull
        out[pkg] = {"buffer": buf, "hull": hull}
    return out


def summary(g, foot, plots):
    rows = []
    for pkg, sub in g.groupby("PKG"):
        f = foot[pkg]
        sel = plots[plots.geometry.representative_point().within(f["buffer"])]
        near = gpd.sjoin_nearest(
            plots[["geometry", "N_PROP", "Q_AVG_M3D"]],
            sub[["geometry", "PKG"]],
            max_distance=SERVE_M, how="inner")
        lev = sub["HAS_LVL"].mean() * 100 if "HAS_LVL" in sub.columns else np.nan
        dia = sub.loc[sub["DIA_OUT"] > 0, "DIA_OUT"]
        rows.append({
            "package": pkg,
            "pipes": len(sub),
            "length_km": round(sub["LEN_M"].sum() / 1000.0, 2),
            "zones": sub["ZONE"].nunique(),
            "tiers": "+".join(sorted(sub["TIER"].unique())),
            "trunk_km": round(sub.loc[sub.TIER == "trunk_main", "LEN_M"].sum() / 1e3, 2),
            "submain_km": round(sub.loc[sub.TIER == "sub_main", "LEN_M"].sum() / 1e3, 2),
            "lateral_km": round(sub.loc[sub.TIER == "lateral", "LEN_M"].sum() / 1e3, 2),
            "hull_area_km2": round(f["hull"].area / 1e6, 2),
            "footprint_km2": round(f["buffer"].area / 1e6, 2),
            "km_per_km2": round((sub["LEN_M"].sum() / 1e3) / max(f["buffer"].area / 1e6, 1e-9), 1),
            "plots_in_footprint": len(sel),
            "plots_within_50m": int(len(near)),
            "properties_within_50m": round(float(near["N_PROP"].sum()), 0),
            "qadf_within_50m_m3d": round(float(near["Q_AVG_M3D"].sum()), 0),
            "pct_with_levels": round(float(lev), 1),
            "dia_min_mm": int(dia.min()) if len(dia) else None,
            "dia_max_mm": int(dia.max()) if len(dia) else None,
            "median_pipe_m": round(float(sub["LEN_M"].median()), 1),
        })
    return pd.DataFrame(rows).sort_values("package")


def overlap(foot):
    pkgs = sorted(foot)
    rows = []
    for i, a in enumerate(pkgs):
        for b in pkgs[i + 1:]:
            ib = foot[a]["buffer"].intersection(foot[b]["buffer"])
            ih = foot[a]["hull"].intersection(foot[b]["hull"])
            aa, ab = foot[a]["buffer"].area, foot[b]["buffer"].area
            ha, hb = foot[a]["hull"].area, foot[b]["hull"].area
            rows.append({
                "a": a, "b": b,
                "buffer_overlap_km2": round(ib.area / 1e6, 3),
                "pct_of_a_buffer": round(100 * ib.area / aa, 1) if aa else 0,
                "pct_of_b_buffer": round(100 * ib.area / ab, 1) if ab else 0,
                "hull_overlap_km2": round(ih.area / 1e6, 2),
                "pct_of_a_hull": round(100 * ih.area / ha, 1) if ha else 0,
                "pct_of_b_hull": round(100 * ih.area / hb, 1) if hb else 0,
                "min_pipe_gap_m": round(float(foot[a]["hull"].distance(foot[b]["hull"])), 1),
            })
    return pd.DataFrame(rows)


def pkg_of_mh(mh):
    """5A-2-TM-MH185 -> 5A-2 ; 5A-1-FL-STP -> 5A-1."""
    if not isinstance(mh, str) or not mh:
        return None
    parts = mh.split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else parts[0]


def topology(g):
    """Which package does each pipe discharge into, per NAMA's own manhole IDs."""
    have = g["US_MHID"].astype(str).str.len() > 0
    t = g[have & (g["US_MHID"] != "None")].copy()
    t["us_pkg"] = t["US_MHID"].map(pkg_of_mh)
    t["ds_pkg"] = t["DS_MHID"].map(pkg_of_mh)
    t["cross"] = t["us_pkg"] != t["ds_pkg"]

    # a node is inside the package if it appears as an upstream ID anywhere in it
    us_ids = set(t["US_MHID"])
    rows = []
    for pkg, sub in t.groupby("us_pkg"):
        internal = set(sub["US_MHID"])
        outs = sub[~sub["DS_MHID"].isin(internal)]
        rows.append({
            "package": pkg,
            "pipes_with_ids": len(sub),
            "cross_package_pipes": int(sub["cross"].sum()),
            "outlets": len(outs),
            "outlets_to_other_pkg": int((outs["ds_pkg"] != pkg).sum()),
            "receives_from": ",".join(sorted(set(
                t.loc[(t.ds_pkg == pkg) & (t.us_pkg != pkg), "us_pkg"].dropna())) ) or "-",
            "discharges_to": ",".join(sorted(set(outs["ds_pkg"].dropna()) - {pkg})) or "-",
            "ds_node_absent_from_own_pkg": int((~outs["DS_MHID"].isin(us_ids)).sum()),
        })
    topo = pd.DataFrame(rows).sort_values("package")

    outlets = t[~t.apply(lambda r: r["DS_MHID"] in set(
        t.loc[t.us_pkg == r["us_pkg"], "US_MHID"]), axis=1)][
        ["FEATUREID", "us_pkg", "TIER", "US_MHID", "DS_MHID", "ds_pkg",
         "DIA_OUT", "DS_INV", "LEN_M"]].copy()
    outlets.columns = ["feature", "package", "tier", "us_mh", "ds_mh", "ds_package",
                       "dia_mm", "ds_invert_m", "len_m"]
    return topo, outlets.sort_values(["package", "tier"])


def interleave(g, foot):
    """How much of a package sits inside another package's convex hull.

    A clean partition scores ~0. Anything large means the contracts were sliced
    through one another and a package is not a territory."""
    rows = []
    for pkg, sub in g.groupby("PKG"):
        rep = sub.geometry.representative_point()
        for other, f in foot.items():
            if other == pkg:
                continue
            inside = rep.within(f["hull"]).sum()
            if inside:
                rows.append({"package": pkg, "inside_hull_of": other,
                             "pipes": int(inside),
                             "pct_of_package": round(100 * inside / len(sub), 1)})
    return pd.DataFrame(rows)


def proximity(g):
    """How far is each package's pipe from the NEAREST pipe of another package?

    Hull overlap can be an artefact of a concave network. This is the honest test of
    interleaving: if half of a package's pipes have a foreign pipe within a street
    width, the two contracts were working the same streets."""
    rows = []
    for pkg, sub in g.groupby("PKG"):
        other = g[g.PKG != pkg]
        if other.empty:
            continue
        j = gpd.sjoin_nearest(sub[["geometry", "PKG"]], other[["geometry", "PKG"]],
                              how="left", distance_col="d")
        d = j["d"].groupby(j.index).min()
        near = j.loc[d[d < 60].index, "PKG_right"] if len(d) else []
        rows.append({
            "package": pkg,
            "pipes": len(sub),
            "median_dist_to_other_pkg_m": round(float(d.median()), 0),
            "pipes_within_60m_of_other_pkg": int((d < 60).sum()),
            "pct_within_60m": round(100 * float((d < 60).mean()), 1),
            "nearest_other_pkg": (pd.Series(near).value_counts().idxmax()
                                  if len(near) else "-"),
        })
    return pd.DataFrame(rows)


def components(g):
    """Is a package ONE connected drainage tree, or several unrelated fragments?"""
    import networkx as nx
    rows = []
    for pkg, sub in g.groupby("PKG"):
        G = nx.Graph()
        for _, r in sub.iterrows():
            u, v = str(r["US_MHID"]), str(r["DS_MHID"])
            if u and v and u != "None":
                G.add_edge(u, v)
        if G.number_of_nodes() == 0:
            continue
        comps = sorted(nx.connected_components(G), key=len, reverse=True)
        rows.append({"package": pkg, "nodes": G.number_of_nodes(),
                     "components": len(comps),
                     "largest_component_pct": round(100 * len(comps[0]) / G.number_of_nodes(), 1)})
    return pd.DataFrame(rows)


def main():
    g = load()
    plots = gpd.read_file(PLOTS)
    foot = footprints(g)

    s = summary(g, foot, plots)
    ov = overlap(foot)
    topo, outlets = topology(g)
    il = interleave(g, foot)
    pr = proximity(g)
    cm = components(g)
    pr.to_csv(os.path.join(RUN, "research_packages_proximity.csv"), index=False)
    cm.to_csv(os.path.join(RUN, "research_packages_components.csv"), index=False)

    os.makedirs(RUN, exist_ok=True)
    s.to_csv(os.path.join(RUN, "research_packages_summary.csv"), index=False)
    ov.to_csv(os.path.join(RUN, "research_packages_overlap.csv"), index=False)
    topo.to_csv(os.path.join(RUN, "research_packages_topology.csv"), index=False)
    outlets.to_csv(os.path.join(RUN, "research_packages_outlets.csv"), index=False)
    il.to_csv(os.path.join(RUN, "research_packages_interleave.csv"), index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    print("=== SUMMARY ===");   print(s.to_string(index=False))
    print("\n=== OVERLAP ===");  print(ov.to_string(index=False))
    print("\n=== TOPOLOGY ==="); print(topo.to_string(index=False))
    print("\n=== INTERLEAVE ==="); print(il.to_string(index=False))
    print("\n=== PROXIMITY ==="); print(pr.to_string(index=False))
    print("\n=== COMPONENTS ==="); print(cm.to_string(index=False))
    print("\n=== OUTLETS (%d) ===" % len(outlets))
    print(outlets.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
