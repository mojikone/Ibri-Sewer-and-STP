"""The treated effluent network of Scenario SC4 (STP-2 and STP-5), which the team's TE models do not have (R10, 2026-11-18): STP-5
supplies the north-eastern customers through its network of the team's SC3 model, and STP-2 supplies the rest through the SC2
network reduced to the mains that reach them. Rebuilt 2026-11-20 as a script; it reproduces the stored network pipe for pipe.

    python te_sc4_network.py            checks the rule against results/final_0.75pc_SC1-SC4/te/SC4_TE_network.gpkg
    python te_sc4_network.py --write    also writes the network, its lengths by diameter and the customers by source

Rule:
  - STP-5: every pipe of the team's S3/TE_STP5.shp that has a geometry.
  - STP-2: from the team's S2/P-2.shp (pipes with a geometry; ends within 1 m joined), the pipe that leaves the plant plus, for every
    customer STP-2 supplies in SC4, the shortest path (by length) from the main network's node nearest the plant to the node nearest
    the customer.
  - Which plant supplies a customer: SC3's source, with STP-1 replaced by STP-2 (te_customers.csv, column sc3_source).
Inputs on the team's server (W: 10_TSE/SHP/Scenarios) and results/final_0.75pc_SC1-SC4/te/te_customers.csv, which consolidates the
team's register: coordinates from their model demand points (Ibri_TE_Model_Demands.shp), 2070 demands and supply hours from
'identified customers MH.shp', 2030 demands from the model points where they agree with the register, flow = demand / (hours x 3.6).
The te/ folder holds the team's raw data and is kept out of the public repo."""
import os, sys
import geopandas as gpd, networkx as nx, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
TE = os.path.join(W18, "results", "final_0.75pc_SC1-SC4", "te"); OUT = os.path.join(TE, "SC4_TE_network.gpkg")
S = r"W:\2621 Design and Supervision for STP, Sewer & TE Networks System in Ibri_NAMA\06-WORKING\04-Hydraulic\10_TSE\SHP\Scenarios"

p5 = gpd.read_file(os.path.join(S, "S3", "TE_STP5.shp")); p5 = p5[p5.geometry.notna()].assign(source="STP-5")
p2 = gpd.read_file(os.path.join(S, "S2", "P-2.shp")); p2 = p2[p2.geometry.notna()].reset_index(drop=True)
stp2 = gpd.read_file(os.path.join(S, "S2", "S2_STP_2.shp")).geometry.iloc[0]
C = pd.read_csv(os.path.join(TE, "te_customers.csv"))
C["sc4_source"] = C.sc3_source.str.replace(" (no location)", "", regex=False).map(lambda s: "STP-2" if s == "STP-1" else s)
cu = gpd.GeoDataFrame(C[C.x.notna()][["id", "site", "d2030", "d2070", "sc4_source"]], geometry=gpd.points_from_xy(C.x.dropna(), C.y.dropna()), crs=32640)

ends = []                                                   # pipe ends within 1 m are one node
for g_ in p2.geometry: cs = list(g_.coords); ends += [cs[0], cs[-1]]
E = np.array(ends); lab = -np.ones(len(E), int); k = 0
for i in range(len(E)):
    if lab[i] < 0: m = (np.hypot(*(E - E[i]).T) <= 1.0) & (lab < 0); lab[m] = k; k += 1
G = nx.Graph()
for j, r in enumerate(p2.itertuples()): G.add_edge(lab[2 * j], lab[2 * j + 1], id=r.ID, L=r.L)
comps = sorted(nx.connected_components(G), key=len); main = comps[-1]
keep = {G.edges[e]["id"] for c in comps[:-1] for e in G.subgraph(c).edges}       # the pipe leaving the plant
idx = [i for i in range(len(E)) if lab[i] in main]
near = lambda x, y: lab[idx[int(np.argmin(np.hypot(*(E[idx] - [x, y]).T)))]]
root = near(stp2.x, stp2.y)
for r in cu[cu.sc4_source == "STP-2"].itertuples():
    path = nx.shortest_path(G, root, near(r.geometry.x, r.geometry.y), weight="L")
    keep |= {G.edges[a, b]["id"] for a, b in zip(path, path[1:])}
net = pd.concat([p2[p2.ID.isin(keep)].assign(source="STP-2"), p5], ignore_index=True)
lengths = net.groupby(net.D.astype(int)).L.sum().reset_index()
print(f"STP-2 {len(keep)} pipes {net[net.source == 'STP-2'].L.sum():,.0f} m | STP-5 {len(p5)} pipes {p5.L.sum():,.0f} m | total {net.L.sum():,.0f} m")

if os.path.exists(OUT):                                     # the rule must reproduce what the report used
    old = gpd.read_file(OUT, layer="SC4_TE_network")
    same = {s: set(old[old.source == s].ID) == set(net[net.source == s].ID) for s in ("STP-2", "STP-5")}
    old_l = pd.read_csv(os.path.join(TE, "SC4_TE_lengths.csv"))
    same_l = old_l.set_index("D").L.round(0).to_dict() == lengths.set_index("D").L.round(0).to_dict()
    print("stored network reproduced:", same, "| lengths by diameter identical:", same_l)
    assert all(same.values()) and same_l, "the rule no longer reproduces the stored SC4 TE network"
if "--write" in sys.argv:
    net.to_file(OUT, layer="SC4_TE_network", driver="GPKG")
    net[["source", "D", "L", "geometry"]].rename(columns={"D": "dn"}).to_file(OUT, layer="te_mains", driver="GPKG")
    cu.to_file(OUT, layer="customers", driver="GPKG")
    lengths.to_csv(os.path.join(TE, "SC4_TE_lengths.csv"), index=False); print("wrote", OUT)
