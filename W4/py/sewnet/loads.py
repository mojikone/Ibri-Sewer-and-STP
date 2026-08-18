"""sewnet.loads — S4: saturation loads per plot, assignment to manholes, tree accumulation.

Doctrine (PROJECT-STATE §2, binding): EVERY plot — built (B) + planned (P) + unparceled
buildings — carries full saturation load; CLASS=A farms carry NO sewage load (TE
customers). Zero silent drops: every loaded plot must land on exactly one manhole or
appear in the unassigned report.

Peak factor applied to the ACCUMULATED domestic flow at each pipe (not per plot);
infiltration = 720 L/d/km of upstream network, added UNPEAKED (G1-p72-73; add-order
[Likely], kickoff item).
"""

import numpy as np
import geopandas as gpd
import networkx as nx
from scipy.spatial import cKDTree

from . import criteria as C


def load_plots(plots_path, unparceled_path, boundary):
    """Loaded points inside the boundary: plot representative points (CLASS B/P) +
    unparceled buildings. Farms (CLASS=A) excluded with count reported."""
    plots = gpd.read_file(plots_path, encoding="utf-8")
    plots = plots[plots.geometry.notna()]
    inside = plots[plots.geometry.representative_point().within(boundary)].copy()
    farms = inside[inside["CLASS"] == "A"]
    loaded = inside[inside["CLASS"].isin(("B", "P"))].copy()
    loaded["src"] = "plot"
    # review F4: a CLASS outside A/B/P must surface, never vanish
    n_other = len(inside) - len(farms) - len(loaded)

    unp = gpd.read_file(unparceled_path)
    unp = unp[unp.geometry.notna()]
    unp_in = unp[unp.geometry.representative_point().within(boundary)].copy()
    unp_in["src"] = "unparceled"
    unp_in["CLASS"] = "U"

    pts = list(loaded.geometry.representative_point()) + list(unp_in.geometry.representative_point())
    classes = list(loaded["CLASS"]) + list(unp_in["CLASS"])
    srcs = list(loaded["src"]) + list(unp_in["src"])
    oids = list(loaded.get("OBJECTID", range(len(loaded)))) + [f"U{i}" for i in range(len(unp_in))]

    stats = {"plots_inside": len(inside), "built": int((inside["CLASS"] == "B").sum()),
             "planned": int((inside["CLASS"] == "P").sum()), "farms_excluded": len(farms),
             "class_other": n_other, "unparceled": len(unp_in), "loaded_points": len(pts)}
    units = [{"id": oids[i], "x": p.x, "y": p.y, "cls": classes[i], "src": srcs[i]}
             for i, p in enumerate(pts)]
    return units, stats


def assign_to_manholes(units, nodes):
    """Nearest-manhole assignment (rider discharge point assumption — criteria.ASSUMPTIONS).
    No distance cutoff: every unit is assigned; distances reported so outliers surface
    in the audit instead of disappearing (fixes the W2 400 m silent-drop shortcut)."""
    keys = [k for k, n in nodes.items() if n["kind"] != "outfall"]
    arr = np.array([[nodes[k]["x"], nodes[k]["y"]] for k in keys])
    tree = cKDTree(arr)
    pts = np.array([[u["x"], u["y"]] for u in units])
    dists, idx = tree.query(pts)
    per_mh = {}
    for u, d, i in zip(units, dists, idx):
        u["mh"] = keys[i]
        u["dist"] = float(d)
        per_mh.setdefault(keys[i], []).append(u)
    return per_mh, float(np.max(dists)) if len(dists) else 0.0


def accumulate(pipes, per_mh, pf_formula="merrimack"):
    """Per-pipe accumulated properties, Qadf, infiltration, PF and Qpeak.

    Sets on each pipe dict: n_props, qadf_m3d, infil_m3d, pf, qpeak_m3s (+peltier
    comparison). Uses the pipe tree (up->dn) to accumulate: each pipe carries
    everything landing at its upstream node and everything its upstream pipes carry."""
    G = nx.DiGraph()
    for p in pipes:
        G.add_edge(p["up"], p["dn"], obj=p)

    node_props = {n: sum(1 for _ in per_mh.get(n, [])) for n in G.nodes}

    order = list(nx.topological_sort(G))
    carry_props = {n: 0.0 for n in G.nodes}
    carry_len = {n: 0.0 for n in G.nodes}
    for n in order:
        local = node_props.get(n, 0)
        total_props = carry_props[n] + local
        for _, dn, d in G.out_edges(n, data=True):
            p = d["obj"]
            p["n_props"] = total_props
            p["uplen_m"] = carry_len[n] + p["length"]
            carry_props[dn] += total_props
            carry_len[dn] += p["uplen_m"]
            # NOTE: carry_len accumulation must merge branches: handled because each
            # in-edge adds its own uplen; junction node sums arrivals.

    for p in pipes:
        qadf = p["n_props"] * C.PLOT_QADF_M3D                       # m3/d
        infil = C.INFILT_L_D_KM * (p["uplen_m"] / 1000.0) / 1000.0  # m3/d
        qadf_mld = qadf / 1000.0
        hold_mld = C.PF_HOLD_PROPERTIES * C.PLOT_QADF_M3D / 1000.0
        pf_m = C.pf_merrimack(max(qadf_mld, hold_mld))
        qm_ls = qadf * 1000.0 / 86400.0
        # Peltier held at its 100-property flow, same convention as Merrimack
        # (review F3; criteria.ASSUMPTIONS PF_COMPARISON_HOLD — comparison column only)
        hold_qm = C.PF_HOLD_PROPERTIES * C.PLOT_QADF_LS
        pf_p = C.pf_peltier(max(qm_ls, hold_qm))
        pf = pf_m if pf_formula == "merrimack" else pf_p
        p["qadf_m3d"] = qadf
        p["infil_m3d"] = infil
        p["pf"] = pf
        p["pf_merrimack"] = pf_m
        p["pf_peltier"] = pf_p
        p["qpeak_m3s"] = (pf * qadf + infil) / 86400.0
        p["qpeak_ls"] = p["qpeak_m3s"] * 1000.0
    return pipes
