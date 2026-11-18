"""W18 final design (engineer, 2026-11-18): the final network of one case renamed into pumps and lifts.
- A station is a LIFT when its force main reaches a manhole within one standard manhole spacing (PAM-GUD-203 Table 12,
  p30: 100 / 120 / 150 / 200 m by the size of the sewer into it) - the client's "pumped to the next nearby manhole" -
  and a PUMP otherwise ("pumped to another location with a long force main"); a plant inlet is a pump too, the plant's
  inlet pumping station. (PAM-GUD-203 itself calls all of them pumping stations, Type 1 / 2 / 3 by design flow, p40.)
- Pumps are P1, P2 ... in the order of the previous numbering (old outfall numbers); a lift is P<n>L<k>, P<n> being the
  pump its flow reaches (through other lifts if need be), k in the order the previous rule meets it from the pump.
- Manholes: <section>-M<k>, numbered from the station up by the previous rule (trunk first - at every junction the
  branch with the most manholes upstream - then the branches); a pipe takes its upstream manhole's number, <section>-P<k>;
  a force main is <station>-RM.
Usage: python final_naming.py SC1-2056   (after the final split; imports py/split_deep_subnetworks.py with the fixed
stations). Writes results/final_0.75pc_SC1-SC4/<case>/named/ nodes.csv, links.csv, stations.csv, network.gpkg."""
import os, sys, io, json, tempfile, contextlib, collections, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
CASE = sys.argv[1]; NAME, YEAR = CASE.split("-")
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); OUT = os.path.join(R, CASE, "named"); os.makedirs(OUT, exist_ok=True)
sys.argv = ["split_deep_subnetworks.py", CASE, os.path.join(R, CASE, "exports"), os.path.join(tempfile.gettempdir(), f"w18_named_{CASE}"),
            "0.0075", "--fixed=" + os.path.join(R, "fixed_stations.json")]
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import split_deep_subnetworks as T
import geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import linemerge
sys.setrecursionlimit(100000)

act = set(T.best["active"]); L = T.links; lab = T.lab
dep = T.depths(T.best["inv"]); li = T.best["li"]
ups = {L[k]["up"] for k in act}; dns = {L[k]["dn"] for k in act}
terms = dns - ups                                            # every station and plant inlet of the final network
into = collections.defaultdict(list)
for k in act: into[L[k]["dn"]].append(k)
down = {L[k]["up"]: k for k in act}

# ------------------------------------------------------------------ where every station sends its flow
cut_of = {L[c["link"]]["up"]: c["link"] for c in T.best["cuts"]}       # lift stations made by the split
tr_of = {t["terminal"]: t for t in T.transfers}                        # existing outfalls pumped to a manhole
rm = pd.read_csv(os.path.join(W18, "results", "rising_mains.csv"))
sys.path.insert(0, HERE)
from routing import routing
_, plant_joins, _ = routing(NAME)


def last_nom(n):                                             # size of the largest sewer into a station
    return max((L[k]["nom"] for k in into[n]), default=200)


def terminal_of(n):                                           # the station a manhole drains to by gravity
    while n in down: n = L[down[n]]["dn"]
    return n


st = {}
for n in terms:
    if n in T.plants:
        st[n] = dict(kind="plant inlet", to=None, rm_m=0.0, receiver=None)
    elif n in cut_of:                                         # pumps to the next manhole of its own line: a lift by the
        k = cut_of[n]; st[n] = dict(kind="lift", to=L[k]["dn"], rm_m=L[k]["L"], receiver=L[k]["dn"])   # client's words
    elif n in tr_of:
        t = tr_of[n]; st[n] = dict(kind="lift" if t["length"] <= T.spacing(last_nom(n)) else "pump", to=t["receiver"], rm_m=t["length"], receiver=t["receiver"])
    else:                                                     # pumped straight to a plant
        src = lab[n]; dst = plant_joins[src]; m = rm[(rm.source == src) & (rm.dest == dst)]
        st[n] = dict(kind="pump", to=T.sub_terminal[dst], rm_m=float(m.length_m.iloc[0]), receiver=None, plant=dst)
# the system of every station: follow lifts until a pump or a plant inlet
def system(n):
    seen = set()
    while st[n]["kind"] == "lift":
        assert n not in seen; seen.add(n); n = terminal_of(st[n]["to"])
    return n


old_no = lambda n: int(lab[n][1:]) if lab[n][1:].isdigit() else 10 ** 6       # pumps keep the previous order
pumps = sorted([n for n in terms if st[n]["kind"] != "lift"], key=lambda n: (old_no(n), lab[n]))
assert all(lab[n][1:].isdigit() for n in pumps), [lab[n] for n in pumps if not lab[n][1:].isdigit()]
name = {n: f"P{i + 1}" for i, n in enumerate(pumps)}


def number(root, links_in):
    """The previous rule: from the root up, the branch with the most manholes upstream first, then the branches."""
    ch = collections.defaultdict(list)
    for k in links_in: ch[L[k]["dn"]].append(L[k]["up"])
    size = {}
    def sz(n):
        if n not in size: size[n] = 1 + sum(sz(c) for c in ch[n])
        return size[n]
    num, counter = {}, [0]
    def number_path(start):
        path, n = [], start
        while True:
            path.append(n); kids = sorted(ch[n], key=lambda c: (-sz(c), c))
            if not kids: break
            n = kids[0]
        side = []
        for n in path:
            counter[0] += 1; num[n] = counter[0]
            side += sorted(ch[n], key=lambda c: (-sz(c), c))[1:]
        for c in side: number_path(c)
    for c in sorted(ch[root], key=lambda c: (-sz(c), c)): number_path(c)
    return num


section_links = collections.defaultdict(set)                 # gravity links of each station's section
for k in act: section_links[terminal_of(L[k]["up"])].add(k)
# lift order inside a system: the previous rule over the whole system, lifts joined to where they pump
for p in pumps:
    lifts = [n for n in terms if st[n]["kind"] == "lift" and system(n) == p]
    if not lifts: continue
    virt, links_sys = {}, set()
    for n in [p] + lifts: links_sys |= section_links[n]
    vk = []
    for n in lifts:
        key = ("rm", n); L[key] = dict(up=n, dn=st[n]["to"], L=st[n]["rm_m"], nom=0, sub="", kind="rm", label=""); vk.append(key)
    num = number(p, links_sys | set(vk))
    for i, n in enumerate(sorted(lifts, key=lambda n: num[n])): name[n] = f"{name[p]}L{i + 1}"
    for key in vk: del L[key]

# ------------------------------------------------------------------ manholes and pipes of every section
nodes, links = [], []
for n in terms:
    sec = name[n]; num = number(n, section_links[n])
    nodes.append(dict(id=n, old=lab[n], new=sec, kind=st[n]["kind"], section=sec, x=T.xy[n][0], y=T.xy[n][1],
                      ground=T.ground.get(n), depth=dep.get(n)))
    for m, k in num.items():
        nodes.append(dict(id=m, old=lab[m], new=f"{sec}-M{k}", kind="manhole", section=sec, x=T.xy[m][0], y=T.xy[m][1],
                          ground=T.ground.get(m), depth=dep.get(m)))
    for k in section_links[n]:
        links.append(dict(key=str(k), old=L[k]["label"], new=f"{sec}-P{num[L[k]['up']]}", kind="gravity join" if L[k]["kind"] == "join" else "pipe",
                          section=sec, up=L[k]["up"], dn=L[k]["dn"]))
N = pd.DataFrame(nodes); K = pd.DataFrame(links)
assert N.id.is_unique and N.new.is_unique and K.new.is_unique, "names not unique"
new_of = N.set_index("id").new.to_dict()

# ------------------------------------------------------------------ attributes, stations, geometry
P = T.P.set_index("_k")
K["dn_mm"] = [int(L[int(k) if k.lstrip("-").isdigit() else eval(k)]["nom"]) for k in K.key]
for c in ("length_m", "s_laid_pc", "s_new_pc", "steepened", "v2031_ms", "v2056_ms", "under075", "over3", "depth_up_m", "depth_dn_m", "depth_max_m", "map_class"):
    K[c] = [P.at[int(k) if k.lstrip("-").isdigit() else eval(k), c] for k in K.key]
sc = pd.read_csv(os.path.join(R, CASE, "selfcleansing_pipes.csv")).set_index("label").v2036_ms
K["v2036_ms"] = K.old.map(sc)                                # only for the pipes that miss 0.75 m/s in 2031
K["from_mh"] = K.up.map(new_of); K["to_mh"] = K.dn.map(new_of)
qd = T.dy.flow_m3d.to_dict(); q31 = (T.dy.Q31 * 86400).to_dict()


def station_flow(n, q):                                       # peak flow into a station, L/s
    if n in cut_of: return q.get(cut_of[n], 0.0) / 86.4
    return sum(q.get(k, 0.0) for k in into[n] if L[k]["kind"] == "pipe") / 86.4 + \
        sum((t["flow_m3d"] if q is qd else t["flow31_m3d"]) for t in T.best["joins"] if t["receiver"] == n) / 86.4


S = []
for n in terms:
    q = station_flow(n, qd); s = st[n]
    S.append(dict(name=name[n], old=lab[n], kind=s["kind"], system=name[system(n)], depth_m=round(dep.get(n, np.nan), 2),
                  ground_m=round(T.ground.get(n, np.nan), 2), q_design_ls=round(q, 1), q_2031_ls=round(station_flow(n, q31), 1),
                  g203_type=1 if q <= 100 else 2 if q <= 300 else 3,
                  pumps_to=(new_of.get(s["receiver"]) if s.get("receiver") is not None else (f"STP at {name[T.sub_terminal[s['plant']]]}" if s.get("plant") else "plant")),
                  force_main_m=round(s["rm_m"], 1), x=T.xy[n][0], y=T.xy[n][1]))
S = pd.DataFrame(S).sort_values("name", key=lambda c: c.str.extract(r"P(\d+)")[0].astype(int) * 1000 +
                                 c.str.extract(r"L(\d+)")[0].fillna(0).astype(int))
N.to_csv(os.path.join(OUT, "nodes.csv"), index=False, float_format="%.3f")
K.drop(columns=["up", "dn"]).to_csv(os.path.join(OUT, "links.csv"), index=False, float_format="%.3f")
S.to_csv(os.path.join(OUT, "stations.csv"), index=False)


def oriented(g, a, b):                                        # a line drawn from a to b
    g = linemerge(g) if g.geom_type == "MultiLineString" else g
    if g.geom_type != "LineString": g = LineString([a, b])
    c = list(g.coords)
    return LineString(c) if math.dist(c[0], a) <= math.dist(c[-1], a) else LineString(c[::-1])


key_of = lambda k: int(k) if k.lstrip("-").isdigit() else eval(k)
GP = os.path.join(OUT, "network.gpkg")
if os.path.exists(GP): os.remove(GP)
gpd.GeoDataFrame(K.drop(columns=["up", "dn", "key"]), geometry=[oriented(T.geom(key_of(k)), T.xy[u], T.xy[d]) for k, u, d in zip(K.key, K.up, K.dn)],
                 crs="EPSG:32640").to_file(GP, layer="pipes", driver="GPKG")
gpd.GeoDataFrame(N[N.kind == "manhole"].drop(columns=["x", "y"]), geometry=[Point(a, b) for a, b in zip(N[N.kind == "manhole"].x, N[N.kind == "manhole"].y)],
                 crs="EPSG:32640").to_file(GP, layer="manholes", driver="GPKG")
gpd.GeoDataFrame(S.drop(columns=["x", "y"]), geometry=[Point(a, b) for a, b in zip(S.x, S.y)], crs="EPSG:32640").to_file(GP, layer="stations", driver="GPKG")
rmg = gpd.read_file(os.path.join(W18, "results", "rising_mains.gpkg"))
fm = []
for n in terms:
    s = st[n]
    if s["kind"] == "plant inlet": continue
    a = T.xy[n]
    if n in cut_of: g = oriented(T.geom(cut_of[n]), a, T.xy[s["to"]])
    else:
        dst = lab[s["receiver"]] if s.get("receiver") is not None else s["plant"]
        m = rmg[(rmg.source == lab[n]) & (rmg.dest == (T.lab[s["receiver"]] if s.get("receiver") is not None else s["plant"]))]
        b = T.xy[s["receiver"]] if s.get("receiver") is not None else T.xy[T.sub_terminal[s["plant"]]]
        g = oriented(m.geometry.iloc[0], a, b) if len(m) else LineString([a, b])
    fm.append(dict(name=f"{name[n]}-RM", station=name[n], kind=s["kind"], length_m=round(s["rm_m"], 1), geometry=g))
gpd.GeoDataFrame(fm, crs="EPSG:32640").to_file(GP, layer="force_mains", driver="GPKG")
summary = dict(case=CASE, pumps=int((S.kind == "pump").sum()), lifts=int((S.kind == "lift").sum()), plant_inlets=int((S.kind == "plant inlet").sum()),
               stations=[f"{r.name} ({r.old}, {r.kind}, {r.depth_m} m, {r.q_design_ls} L/s, type {r.g203_type})" for r in S.itertuples()])
json.dump(summary, open(os.path.join(OUT, "naming.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
