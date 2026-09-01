"""What should be sewered at all? The marginal network, measured branch by branch.

W10 sewers 60,085 of 61,272 plots. The optimisation study showed the aggregate: dropping
branches under 1 m3/d removes 333 km of pipe (18 %) that collects 151 m3/d (0.2 % of the
flow) and 22 % of the pumping. That is a headline, not a decision. A decision needs to know
WHICH branches, WHOSE houses, HOW FAR out, and what each one costs per property.

This script builds that. Method:

  1. the same graph, flow tree and load allocation the design itself uses - not a
     re-derivation, the identical `netlib` / `p1_subnetworks` / `p2_sizing` calls, so the
     numbers here and the numbers in the design cannot drift apart
  2. plots, properties and population accumulated down the same tree as the flow, so a
     branch's population is the population that would actually drain through it
  3. a branch = a connected set of edges whose ACCUMULATING flow is below a threshold.
     Working from the heads down means a branch is never cut off from something larger
     downstream of it
  4. per branch: length, plots, properties, people, flow, the lifting stations inside it,
     the depth breaches inside it, and the distance from its outlet to the retained network
  5. cost-effectiveness as metres of sewer per property and metres per m3/d, against the
     whole-network figure as the yardstick

Separately, settlements are found geometrically (plots within SETTLE_M of each other are
one settlement) because `VILLAGE_EN` is blank on 43,557 of 61,272 plots and cannot carry
the analysis. The G201 p80 remote-area test is then applied to each settlement.

Run:  python r5_marginal.py
"""
import os
import pickle
import sys
import time
import warnings
from collections import defaultdict

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.dirname(HERE)
sys.path.insert(0, PY)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(PY)), "W8", "py"))
import config as C
import netlib as N
from p1_subnetworks import flow_tree
from p2_sizing import accumulate

warnings.filterwarnings("ignore")

CACHE = os.path.join(
    r"C:\Users\mojtaba\AppData\Local\Temp\claude"
    r"\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude"
    r"\fdf9ca49-7b6f-48de-894a-607476504f95\scratchpad", "r5_tree.pkl")
OUT_RUN = os.path.join(C.OUT, "run")
ASSIGN_M = 160.0        # identical to p2_sizing.assign_loads
SETTLE_M = 60.0         # plots this close are one settlement. Swept: at 120 m the Ibri
                        # conurbation swallows 95.9 % of the plots and every outlying
                        # village disappears into it; at 60 m it holds 80.4 % and the
                        # 12,584 plots outside it separate into settlements you can name.
THRESHOLDS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0)
HEADLINE_T = 1.0        # the threshold the branch layer is written at

# G201 p80 sec 8.1 - a Remote Area meets ONE OR MORE of these. The two that can be
# measured from the data we hold are quoted verbatim in the report.
G201_MAX_POP = 500
G201_MAX_PLOTS = 100
G201_REMOTE_KM = 25.0


def assign_plot_attrs(xy, nodes):
    """Flow, plots, properties and population onto the corridor node each plot fronts.

    Deliberately the same join, the same layer and the same 160 m distance as
    `p2_sizing.assign_loads`, so the flow accumulated here is the flow the design used.
    """
    gpkg = os.path.join(C.OUT_SHP, "W10_plot_loads.gpkg")
    pl = gpd.read_file(gpkg, layer="plot_loads")
    pts = gpd.GeoDataFrame(geometry=[Point(xy[n]) for n in nodes],
                           data={"NODE": list(nodes)}, crs=C.EPSG)
    cols = ["Q_AVG_M3D", "N_PROP", "POP", "geometry"]
    j = gpd.sjoin_nearest(pl[cols], pts, how="left", max_distance=ASSIGN_M,
                          distance_col="D")
    j = j[~j.index.duplicated(keep="first")]
    j["PLOT_IDX"] = j.index
    q, npl, npr, pop = (defaultdict(float), defaultdict(int),
                        defaultdict(float), defaultdict(float))
    node_plots = defaultdict(list)
    for node, v, pr, po, pi in zip(j["NODE"], j["Q_AVG_M3D"], j["N_PROP"],
                                   j["POP"], j["PLOT_IDX"]):
        if node != node:
            continue
        node = int(node)
        q[node] += float(v) if v == v else 0.0
        npl[node] += 1
        npr[node] += float(pr) if pr == pr else 0.0
        pop[node] += float(po) if po == po else 0.0
        node_plots[node].append(int(pi))
    print(f"loads: {pl.Q_AVG_M3D.sum():,.0f} m3/d total, {sum(q.values()):,.0f} placed "
          f"({100*sum(q.values())/pl.Q_AVG_M3D.sum():.1f} %); "
          f"{sum(npl.values()):,} plots, {sum(npr.values()):,.0f} properties, "
          f"{sum(pop.values()):,.0f} people on {len(q):,} nodes")

    # Village names come from the cadastre, joined spatially rather than by row order:
    # plot_loads holds 64,071 records (61,272 plots plus 2,799 unparcelled buildings)
    # against MoH_Plots' 61,272, so positional indexing silently mismatches.
    mo = gpd.read_file(C.PLOTS_RAW).to_crs(C.EPSG)[["VILLAGE_EN", "geometry"]]
    reps = gpd.GeoDataFrame(geometry=pl.geometry.representative_point(), crs=C.EPSG)
    vj = gpd.sjoin_nearest(reps, mo, how="left", max_distance=200)
    vj = vj[~vj.index.duplicated(keep="first")]
    village = pd.Series(
        [("" if v is None or v != v or str(v).strip().lower() in ("nan", "none")
          else str(v).strip()) for v in vj["VILLAGE_EN"].reindex(pl.index)],
        index=pl.index, dtype=object)
    return q, npl, npr, pop, node_plots, pl, village


def build():
    if os.path.exists(CACHE):
        with open(CACHE, "rb") as f:
            return pickle.load(f)
    G, xy, lines, z = N.load_network()
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(comps[0]).copy()
    sink, d = N.nearest_node(xy, C.STP_EXISTING, nodes=comps[0])
    print(f"outlet node {d:.0f} m from the works")
    cost, nxt, _ = flow_tree(G, z, sink)
    obj = (G, xy, lines, z, sink, cost, nxt)
    with open(CACHE, "wb") as f:
        pickle.dump(obj, f)
    return obj


def main():
    t0 = time.time()
    G, xy, lines, z, sink, cost, nxt = build()
    nodes = list(G.nodes)
    q, npl, npr, pop, node_plots, pl, village = assign_plot_attrs(xy, nodes)

    qacc, lacc, order = accumulate(G, nxt, q)
    placc, _, _ = accumulate(G, nxt, {k: float(v) for k, v in npl.items()})
    pracc, _, _ = accumulate(G, nxt, npr)
    popacc, _, _ = accumulate(G, nxt, pop)

    # every edge that carries flow, i.e. every pipe the design lays
    edges = [(n, m) for n, m in nxt.items() if G.has_edge(n, m)]
    elen = {(n, m): G[n][m]["len"] for n, m in edges}
    total_km = sum(elen.values()) / 1000
    print(f"\nflow tree: {len(edges):,} laid reaches, {total_km:,.1f} km; "
          f"{qacc[sink]:,.0f} m3/d at the works")

    # lifting stations, matched to the nearest node - needed by the sweep as well as the
    # branch table, because the pumping is the reason the marginal network is expensive
    lifts = gpd.read_file(os.path.join(C.OUT_SHP, "W10_lift_sized.shp"))
    narr = np.array([xy[n] for n in nodes])
    lift_node = {}
    for _, r in lifts.iterrows():
        d = np.hypot(narr[:, 0] - r.geometry.x, narr[:, 1] - r.geometry.y)
        i_ = int(np.argmin(d))
        if d[i_] < 30:
            lift_node.setdefault(nodes[i_], []).append(float(r.LIFT_M))
    lift_total = sum(sum(v) for v in lift_node.values())
    print(f"lifting: {len(lifts):,} breaches placed on nodes, "
          f"{lift_total:,.0f} m of lift in total")

    # ------------------------------------------------------------ sweep
    print(f"\nthe marginal network as the threshold moves\n")
    rows = []
    for T in THRESHOLDS:
        m = [(n, mm) for n, mm in edges if qacc[n] < T]
        km = sum(elen[e] for e in m) / 1000
        heads = {n for n, _ in m}
        # a plot belongs to the marginal set if its node is a marginal head whose own
        # accumulated flow is below T - i.e. it is served only through marginal pipe
        pls = sum(npl.get(n, 0) for n in heads)
        prs = sum(npr.get(n, 0.0) for n in heads)
        pp = sum(pop.get(n, 0.0) for n in heads)
        qq = sum(q.get(n, 0.0) for n in heads)
        lm = sum(sum(v) for k, v in lift_node.items() if k in heads)
        ln_ = sum(len(v) for k, v in lift_node.items() if k in heads)
        rows.append({"threshold_m3d": T, "marginal_km": round(km, 1),
                     "pct_of_pipe": round(100 * km / total_km, 1),
                     "plots": int(pls), "properties": round(prs),
                     "people": round(pp), "flow_m3d": round(qq, 1),
                     "pct_of_flow": round(100 * qq / qacc[sink], 2),
                     "breaches_inside": ln_, "lift_m_inside": round(lm),
                     "pct_of_lift": round(100 * lm / lift_total, 1),
                     "m_per_property": round(km * 1000 / max(prs, 1), 1),
                     "m_per_m3d": round(km * 1000 / max(qq, 1e-9))})
        print(f"   under {T:5.1f} m3/d: {km:7.1f} km ({100*km/total_km:4.1f} %)  "
              f"{int(pls):6,d} plots  {prs:7,.0f} properties  {pp:8,.0f} people  "
              f"{qq:8.1f} m3/d ({100*qq/qacc[sink]:5.2f} %)  "
              f"lift {lm:6,.0f} m ({100*lm/lift_total:4.1f} %)  "
              f"{km*1000/max(prs,1):8.1f} m/property")
    sweep = pd.DataFrame(rows)
    sweep.to_csv(os.path.join(OUT_RUN, "r5_marginal_sweep.csv"), index=False)
    print(f"\n   whole network: {total_km:,.1f} km, "
          f"{sum(npl.values()):,} plots, {sum(npr.values()):,.0f} properties, "
          f"{qacc[sink]:,.0f} m3/d  ->  "
          f"{total_km*1000/sum(npr.values()):.1f} m/property, "
          f"{total_km*1000/qacc[sink]:.1f} m per m3/d")

    # ------------------------------------------------------------ branches at HEADLINE_T
    # A branch is a connected group of MARGINAL NODES - nodes whose accumulating flow is
    # below the threshold - plus the one reach that carries them out into the retained
    # network. Building the components on the EDGES instead pulls the retained outlet node
    # into the branch, which both double-counts the town behind it and welds two unrelated
    # branches together wherever they happen to join the network at the same chamber.
    T = HEADLINE_T
    M = {n for n in G.nodes if qacc[n] < T}
    H = nx.Graph()
    H.add_nodes_from(M)
    for n in M:
        m = nxt.get(n)
        if m in M and G.has_edge(n, m):
            H.add_edge(n, m)
    comps = list(nx.connected_components(H))
    print(f"\nat {T:.1f} m3/d the marginal network is {len(comps):,} separate branches")

    # lifting stations, matched to the nearest node
    lifts = gpd.read_file(os.path.join(C.OUT_SHP, "W10_lift_sized.shp"))
    narr = np.array([xy[n] for n in nodes])
    lift_node = {}
    for _, r in lifts.iterrows():
        d = np.hypot(narr[:, 0] - r.geometry.x, narr[:, 1] - r.geometry.y)
        i_ = int(np.argmin(d))
        if d[i_] < 30:
            lift_node.setdefault(nodes[i_], []).append(float(r.LIFT_M))

    # which corridor source each marginal reach was laid in - Part A and Part B joined up
    cq = gpd.read_file(os.path.join(C.OUT_SHP, "W10_corridor_quality.shp"))
    from shapely.strtree import STRtree
    ctree = STRtree(list(cq.geometry))

    out, brid, src_km = [], 0, defaultdict(float)
    for comp in comps:
        e = [(n, nxt[n]) for n in comp
             if nxt.get(n) is not None and G.has_edge(n, nxt[n])]
        if not e:
            continue
        brid += 1
        km = sum(elen[x] for x in e) / 1000
        pls = sum(npl.get(n, 0) for n in comp)
        prs = sum(npr.get(n, 0.0) for n in comp)
        pp = sum(pop.get(n, 0.0) for n in comp)
        qq = sum(q.get(n, 0.0) for n in comp)
        outn = [n for n in comp if nxt.get(n) is not None and nxt[n] not in comp]
        outn = outn[0] if outn else None
        lift_m = sum(sum(v) for k, v in lift_node.items() if k in comp)
        n_lift = sum(len(v) for k, v in lift_node.items() if k in comp)
        geoms = [LineString([xy[a], xy[b]]) for a, b in e]
        for g in geoms:
            mid = g.interpolate(0.5, normalized=True)
            k = ctree.query_nearest(mid)
            k = int(k[0]) if hasattr(k, "__len__") else int(k)
            src_km[cq.SRC.iloc[k]] += g.length / 1000
        pidx = [i2 for n in comp for i2 in node_plots.get(n, ())]
        vil = "-"
        if pidx:
            vv = [v for v in village.iloc[pidx].tolist() if v]
            if vv:
                vil = max(set(vv), key=vv.count)[:48]
        out.append({
            "BR_ID": brid, "KM": round(km, 3), "PLOTS": int(pls),
            "PROPS": round(prs, 1), "POP": round(pp), "Q_M3D": round(qq, 3),
            "M_PER_PRP": round(km * 1000 / prs, 1) if prs > 0.01 else -1.0,
            "M_PER_M3D": round(km * 1000 / qq, 1) if qq > 0.001 else -1.0,
            "SERVES": ("nothing" if prs <= 0.01 else
                       ("under_1_prop" if prs < 1 else "houses")),
            "N_LIFT": n_lift, "LIFT_M": round(lift_m, 1),
            "OUT_X": round(xy[outn][0], 1) if outn else None,
            "OUT_Y": round(xy[outn][1], 1) if outn else None,
            "OUT_Z": round(float(z.get(outn, np.nan)), 1) if outn else None,
            "ROUTE_KM": round(cost.get(outn, np.nan) / 1000, 2) if outn else None,
            "VILLAGE": vil,
            "geometry": MultiLineString(geoms) if len(geoms) > 1 else geoms[0]})
    br = gpd.GeoDataFrame(out, crs=C.EPSG).sort_values("KM", ascending=False)
    br.to_file(os.path.join(C.OUT_SHP, "W10_marginal_branches.shp"))
    br.drop(columns="geometry").to_csv(
        os.path.join(OUT_RUN, "r5_marginal_branches.csv"), index=False)
    print(f"   wrote W10_marginal_branches.shp: {len(br):,} branches, "
          f"{br.KM.sum():,.1f} km, {br.PLOTS.sum():,} plots, "
          f"{br.PROPS.sum():,.0f} properties, {br.Q_M3D.sum():,.1f} m3/d, "
          f"{br.LIFT_M.sum():,.0f} m of lift in {int(br.N_LIFT.sum())} stations")
    print("\n   what the marginal network SERVES:")
    print(br.groupby("SERVES").agg(
        branches=("KM", "size"), km=("KM", lambda s_: round(s_.sum(), 1)),
        plots=("PLOTS", "sum"), props=("PROPS", lambda s_: round(s_.sum())),
        people=("POP", "sum"), q=("Q_M3D", lambda s_: round(s_.sum(), 1)),
        lift_m=("LIFT_M", lambda s_: round(s_.sum())),
        n_lift=("N_LIFT", "sum")).to_string())

    print("\n   corridor source of the marginal pipe:")
    tot_src = sum(src_km.values())
    for k in sorted(src_km, key=lambda a: -src_km[a]):
        print(f"      {k:<12s} {src_km[k]:7.1f} km  "
              f"({100*src_km[k]/tot_src:4.1f} % of the marginal network)")

    print("\n   the branches with a lifting station in them, ranked by lift:")
    lb = br[br.N_LIFT > 0].sort_values("LIFT_M", ascending=False)
    print(lb.drop(columns="geometry").head(15).to_string(index=False))

    print("\n   largest 15 branches by length:")
    print(br.drop(columns="geometry").head(15).to_string(index=False))

    # ------------------------------------------------------------ settlements
    print(f"\nsettlements: plots within {SETTLE_M:.0f} m of each other")
    allp = gpd.read_file(os.path.join(C.OUT_SHP, "W10_plot_loads.gpkg"),
                         layer="plot_loads")
    blob = gpd.GeoDataFrame(
        geometry=[unary_union(allp.geometry.buffer(SETTLE_M))], crs=C.EPSG)
    blob = blob.explode(index_parts=False).reset_index(drop=True)
    blob["SID"] = blob.index
    j = gpd.sjoin(allp, blob[["SID", "geometry"]], how="left", predicate="intersects")
    j = j[~j.index.duplicated(keep="first")]
    allp["SID"] = j["SID"].values
    allp["VILLAGE_EN"] = village.values

    st = allp.groupby("SID").agg(
        plots=("PLOT_ID", "size"), props=("N_PROP", "sum"),
        people=("POP", "sum"), q=("Q_AVG_M3D", "sum")).reset_index()
    cen = allp.dissolve("SID").centroid
    st["x"] = cen.x.reindex(st.SID).values
    st["y"] = cen.y.reindex(st.SID).values
    nm = (allp.assign(V=lambda d: d.VILLAGE_EN.astype(str).str.strip())
          .query("V != ''").groupby("SID").V
          .agg(lambda s: s.value_counts().index[0]))
    st["village"] = st.SID.map(nm).fillna("-")

    # distance from each settlement to the EXISTING built network - the G201 p80 test
    ex = gpd.read_file(os.path.join(C.OUT_SHP, "W10_existing_built.shp"))
    exu = unary_union(ex.geometry.values)
    cenpt = allp.dissolve("SID").geometry.centroid
    st["km_to_built_net"] = [round(cenpt.loc[s].distance(exu) / 1000, 2)
                             for s in st.SID]
    # pipe length inside each settlement, from the design itself
    seg = gpd.GeoDataFrame(
        geometry=[LineString([xy[a], xy[b]]) for a, b in edges], crs=C.EPSG)
    seg["LEN_M"] = [elen[e] for e in edges]
    mid = gpd.GeoDataFrame(geometry=seg.geometry.interpolate(0.5, normalized=True),
                           data={"LEN_M": seg.LEN_M}, crs=C.EPSG)
    jm = gpd.sjoin(mid, blob[["SID", "geometry"]], how="left", predicate="within")
    jm = jm[~jm.index.duplicated(keep="first")]
    inside = jm.groupby("SID").LEN_M.sum() / 1000
    st["pipe_km_inside"] = st.SID.map(inside).fillna(0).round(2)
    outside_km = jm.loc[jm.SID.isna(), "LEN_M"].sum() / 1000
    # ---- the honest cost of serving each settlement: the pipe that exists ONLY for it
    # A reach belongs exclusively to a settlement when every drop of load upstream of it
    # comes from that one settlement. That is its internal streets PLUS its spur out, all
    # the way to the chamber where its flow first mixes with somebody else's - which is
    # exactly the pipe that disappears if the settlement is not sewered. Reaches with NO
    # load upstream at all belong to nobody and are the network's dead weight.
    sid_arr = allp["SID"].to_numpy()
    prop_arr = allp["N_PROP"].to_numpy()
    node_sid = {}
    for n, pidx in node_plots.items():
        sids = {int(sid_arr[i]) for i in pidx
                if prop_arr[i] > 0 and sid_arr[i] == sid_arr[i]}
        if sids:
            node_sid[n] = sids

    ups_of = defaultdict(list)
    for n, m in nxt.items():
        ups_of[m].append(n)
    upstream_sids = {}
    for n in order:                                          # topological, heads first
        s = set(node_sid.get(n, ()))
        for u in ups_of.get(n, ()):
            s |= upstream_sids.get(u, set())
        upstream_sids[n] = s

    excl_km = defaultdict(float)
    empty_km = shared_km = 0.0
    empty_edges = []
    for n, m in edges:
        s = upstream_sids.get(n, set())
        L = elen[(n, m)] / 1000
        if not s:
            empty_km += L
            empty_edges.append((n, m))
        elif len(s) == 1:
            excl_km[next(iter(s))] += L
        else:
            shared_km += L
    st["pipe_km_exclusive"] = st.SID.map(excl_km).fillna(0).round(2)
    st["m_per_property"] = (st.pipe_km_exclusive * 1000 /
                            st.props.clip(lower=1e-9)).round(1)
    st["m_per_m3d"] = (st.pipe_km_exclusive * 1000 / st.q.clip(lower=1e-9)).round(1)
    st["remote_G201"] = ((st.people < G201_MAX_POP) | (st.plots < G201_MAX_PLOTS))
    st = st.sort_values("props", ascending=False)
    st.round(3).to_csv(os.path.join(OUT_RUN, "r5_settlements.csv"), index=False)

    gpd.GeoDataFrame(
        geometry=[LineString([xy[a], xy[b]]) for a, b in empty_edges],
        data={"LEN_M": [round(elen[e], 2) for e in empty_edges]},
        crs=C.EPSG).to_file(os.path.join(C.OUT_SHP, "W10_pipe_no_load.shp"))
    print(f"\n   pipe attribution, whole network {total_km:,.1f} km:")
    print(f"      NO LOAD anywhere upstream : {empty_km:7.1f} km "
          f"({100*empty_km/total_km:4.1f} %)  -> W10_pipe_no_load.shp")
    print(f"      exclusive to ONE settlement: {sum(excl_km.values()):7.1f} km "
          f"({100*sum(excl_km.values())/total_km:4.1f} %)")
    print(f"      shared between settlements : {shared_km:7.1f} km "
          f"({100*shared_km/total_km:4.1f} %)")

    print(f"   {len(st):,} settlements; {outside_km:,.1f} km of pipe runs OUTSIDE every "
          f"settlement envelope (the links between them)")
    print(f"   meeting the G201 p80 size test (<{G201_MAX_POP} people OR "
          f"<{G201_MAX_PLOTS} plots): {int(st.remote_G201.sum()):,} settlements, "
          f"{st.loc[st.remote_G201, 'plots'].sum():,} plots, "
          f"{st.loc[st.remote_G201, 'props'].sum():,.0f} properties, "
          f"{st.loc[st.remote_G201, 'q'].sum():,.0f} m3/d, "
          f"{st.loc[st.remote_G201, 'pipe_km_inside'].sum():,.1f} km of pipe")
    print(f"   more than {G201_REMOTE_KM:.0f} km from the built network: "
          f"{int((st.km_to_built_net > G201_REMOTE_KM).sum()):,} settlements")
    print("\n   largest 12 settlements:")
    print(st.head(12)[["SID", "village", "plots", "props", "people", "q",
                       "pipe_km_inside", "m_per_property",
                       "km_to_built_net"]].round(1).to_string(index=False))
    print(f"\ntotal {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
