"""W18 final design: the products of one case from its renamed network (py/final_naming.py) - the pumping stations and
lifts sized, the average flow at every plant by year, the quantities, and the layers the maps and QGIS read.

Stations, by the method of py/scenario_results.py (W17 R7 report): duty = the design-year peak (raised so the force main
keeps 1.0 m/s, G203 p50); force main the size from 75 mm with the least power at v <= 2.5 m/s; head = static + Hazen-
Williams friction (C 120, minor losses +10 %); wet well 1.5 m below the incoming invert; discharge 0.3 m above the
receiving manhole's invert, or 3.0 m above the ground at a plant; wire-to-water efficiency 0.65; G203 p40 type by duty.
A plant inlet station lifts the arriving sewer to 3.0 m above the ground (no force main). Energy per year = power x the
hours the duty takes to pass that year's average flow through the station (its own catchment, the infiltration of its
sewers, and the average flow of every station pumping into it).
Usage: python final_products.py SC1-2056   Writes <case>/products/ stations.csv, plants.csv, quantities.json, map.gpkg."""
import os, sys, json, math, collections
import numpy as np, pandas as pd
import geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
CASE = sys.argv[1]; NAME, YEAR = CASE.split("-")
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); NM = os.path.join(R, CASE, "named")
OUT = os.path.join(R, CASE, "products"); os.makedirs(OUT, exist_ok=True)
YEARS = ["2026", "2031", "2036", "2041", "2046", "2051", "2056", "2061"]
STP_NAME = {"O1": "STP-1", "O16": "STP-2", "O4": "STP-5"}   # the treatment sites by the outfall they sit on
INF = 0.72                                                   # m3/day per km of sewer (the design's infiltration)
DN_FM = [75, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200]

N = pd.read_csv(os.path.join(NM, "nodes.csv")); K = pd.read_csv(os.path.join(NM, "links.csv"))
S = pd.read_csv(os.path.join(NM, "stations.csv"))
loads = pd.read_csv(os.path.join(W18, "results", "loads", "manhole_loads.csv"), index_col="manhole_id")
sec_of = N.set_index("new").section.to_dict(); node = N.set_index("new")
km_sec = K.groupby("section").length_m.sum() / 1000
avg_own = {y: N.assign(q=N.id.map(loads[f"Q_{y}"]).fillna(0)).groupby("section").q.sum() for y in YEARS}
into_sec = collections.defaultdict(list)                       # stations that pump into a section
plant_target = {}
for r in S.itertuples():
    if r.kind == "plant inlet": continue
    if str(r.pumps_to).startswith("STP at "):
        tgt = r.pumps_to.split("STP at ")[1]; into_sec[tgt].append(r.name)
    else:
        into_sec[sec_of[r.pumps_to]].append(r.name)


def avg(st, y, seen=()):
    """Average flow through a station, m3/d."""
    assert st not in seen
    return float(avg_own[y].get(st, 0.0)) + km_sec.get(st, 0.0) * INF + sum(avg(u, y, seen + (st,)) for u in into_sec[st])


def plant_of(st):
    r = S.set_index("name").loc[st]
    while r["kind"] != "plant inlet":
        st = r.pumps_to.split("STP at ")[1] if str(r.pumps_to).startswith("STP at ") else sec_of[r.pumps_to]
        r = S.set_index("name").loc[st]
    return st


rows = []
for r in S.itertuples():
    inv_in = r.ground_m - r.depth_m; z_in = inv_in - 1.5
    if r.kind == "plant inlet":
        z_out, L = r.ground_m + 3.0, 0.0
    elif str(r.pumps_to).startswith("STP at "):
        p = node.loc[r.pumps_to.split("STP at ")[1]]; z_out, L = p.ground + 3.0, r.force_main_m
    else:
        m = node.loc[r.pumps_to]; z_out, L = (m.ground - m.depth) + 0.3, r.force_main_m
    q = r.q_design_ls / 1000.0
    if r.kind == "plant inlet":                               # plus the stations that pump straight to the plant
        q += S[S.pumps_to == f"STP at {r.name}"].q_design_ls.sum() / 1000.0
    best = None
    for d in (DN_FM if L > 0 else [0]):
        if d == 0: qd, hf, v = q, 0.0, float("nan")
        else:
            a = math.pi / 4 * (d / 1000) ** 2; qd = max(q, a * 1.0)
            if qd / a > 2.5: continue
            hf = 1.1 * 10.67 * L * qd ** 1.852 / (120 ** 1.852 * (d / 1000) ** 4.87); v = qd / a
        kw = 9.81 * qd * (max(z_out - z_in, 0) + hf) / 0.65
        if best is None or kw < best[0]: best = (kw, d, qd, hf, v)
    kw, dn, qd, hf, v = best
    e = {y: kw * (avg(r.name, y) / (qd * 3600) if qd > 0 else 0) * 365 / 1000 for y in YEARS}      # MWh/yr
    rows.append(dict(name=r.name, kind=r.kind, system=r.system, plant=plant_of(r.name), g203_type=1 if qd <= 0.1 else 2 if qd <= 0.3 else 3,
                     outfall_depth_m=r.depth_m, wet_well_depth_m=round(r.depth_m + 1.5, 2), ground_m=r.ground_m,
                     q_design_ls=r.q_design_ls, duty_ls=round(qd * 1000, 1), q_2031_ls=r.q_2031_ls, pumps_to=r.pumps_to,
                     force_main_m=L, force_main_dn=dn or None, fm_velocity_ms=round(v, 2) if v == v else None,
                     static_m=round(z_out - z_in, 2), head_m=round(max(z_out - z_in, 0) + hf, 2), kw=round(kw, 1),
                     avg_2031_m3d=round(avg(r.name, "2031"), 1), avg_design_m3d=round(avg(r.name, YEAR), 1),
                     mwh_2031=round(e["2031"], 1), mwh_design=round(e[YEAR], 1),
                     wet_well_live_m3=round(90 * qd / (1 if qd <= 0.1 else 2 if qd <= 0.3 else 3), 1), x=r.x, y=r.y))
ST = pd.DataFrame(rows)
ST.to_csv(os.path.join(OUT, "stations.csv"), index=False)
plants = {p: {y: round(avg(p, y), 0) for y in YEARS} for p in ST[ST.kind == "plant inlet"].name}
pl = pd.DataFrame([dict(plant=p, stp=STP_NAME[S.set_index("name").at[p, "old"]], inlet_depth_m=float(ST.set_index("name").at[p, "outfall_depth_m"]), **{f"avg_{y}_m3d": v for y, v in plants[p].items()},
                        peak_design_ls=float(ST.set_index("name").at[p, "duty_ls"])) for p in plants])
pl.to_csv(os.path.join(OUT, "plants.csv"), index=False)

# ------------------------------------------------------------------ quantities
band = lambda d: "up to 3 m" if d <= 3 else "3 to 6 m" if d <= 6 else "6 to 9 m" if d <= 9 else "9 to 12 m" if d <= 12 else "12 to 15 m" if d <= 15 else "over 15 m"
K["depth_band"] = K.depth_max_m.map(band)
mh = N[N.kind == "manhole"].copy(); mh["depth_band"] = mh.depth.map(band)
Q = dict(case=CASE, sewer_km=round(K.length_m.sum() / 1000, 2), manholes=int(len(mh)),
         pumps=int((ST.kind == "pump").sum()), lifts=int((ST.kind == "lift").sum()), plant_inlets=int((ST.kind == "plant inlet").sum()),
         stations=int((ST.kind != "plant inlet").sum()), force_main_km=round(ST.force_main_m.sum() / 1000, 2),
         kw_network=round(ST[ST.kind != "plant inlet"].kw.sum(), 0), kw_plant_inlets=round(ST[ST.kind == "plant inlet"].kw.sum(), 0),
         mwh_2031=round(ST.mwh_2031.sum(), 0), mwh_design=round(ST.mwh_design.sum(), 0),
         km_by_size={int(k): round(v / 1000, 2) for k, v in K.groupby("dn_mm").length_m.sum().items()},
         km_by_depth={b: round(v / 1000, 2) for b, v in K.groupby("depth_band").length_m.sum().items()},
         manholes_by_depth={b: int(v) for b, v in mh.groupby("depth_band").size().items()},
         deepest=dict(name=mh.loc[mh.depth.idxmax(), "new"], depth=round(float(mh.depth.max()), 2)),
         plants={p: dict(stp=STP_NAME[S.set_index("name").at[p, "old"]], avg_m3d=plants[p], inlet_depth_m=float(ST.set_index("name").at[p, "outfall_depth_m"])) for p in plants},
         km_big=round(K[K.dn_mm > 200].length_m.sum() / 1000, 2),
         km_big_under075_2031=round(K[(K.dn_mm > 200) & (K.under075 == 1)].length_m.sum() / 1000, 2),
         km_big_under075_2036=round(K[(K.dn_mm > 200) & (K.v2036_ms < 0.75)].length_m.sum() / 1000, 2))
json.dump(Q, open(os.path.join(OUT, "quantities.json"), "w"), indent=1)

# ------------------------------------------------------------------ map layers (current names only)
GP = os.path.join(OUT, "map.gpkg")
if os.path.exists(GP): os.remove(GP)
p = gpd.read_file(os.path.join(NM, "network.gpkg"), layer="pipes")
p["plant"] = p.section.map(lambda s: plant_of(s)); p["stp"] = p.plant.map(lambda x: STP_NAME[S.set_index("name").at[x, "old"]]); p["depth_band"] = p.depth_max_m.map(band)


def sc_class(r):                                             # self-cleansing class for the maps (a gravity join is a sewer)
    if r.dn_mm <= 200: return "DN200 (rule: above DN200 only)"
    if r.under075 == 1:
        return "Under 0.75 m/s in 2031, reaches it by 2036" if r.v2036_ms >= 0.75 else "Under 0.75 m/s in 2031 and in 2036"
    return r.map_class if str(r.map_class).startswith("Steepened") else "Above DN200, 0.75 m/s as laid"


p["sc_class"] = [sc_class(r) for r in p.itertuples()]
p.rename(columns={"new": "label", "dn_mm": "od_mm"}).to_file(GP, layer="pipes", driver="GPKG")
m = gpd.read_file(os.path.join(NM, "network.gpkg"), layer="manholes")
m["depth_band"] = m.depth.map(band)
m.rename(columns={"new": "label", "depth": "depth_m"}).to_file(GP, layer="manholes", driver="GPKG")
s = gpd.read_file(os.path.join(NM, "network.gpkg"), layer="stations")[["name", "geometry"]].merge(ST.drop(columns=["x", "y"]), on="name")
stp_of = {r.name: STP_NAME.get(r.old, "") for r in S.itertuples()}
s["map_label"] = [f"{a} {d:.1f} m" if k != "plant inlet" else f"{stp_of[a]} inlet ({a}), {d:.1f} m" for a, k, d in zip(s.name, s.kind, s.outfall_depth_m)]
s["duty_label"] = [f"{a} {d:.1f} m | {q:.0f} L/s, head {h:.0f} m" for a, d, q, h in zip(s.name, s.outfall_depth_m, s.duty_ls, s.head_m)]
s.to_file(GP, layer="stations", driver="GPKG")
gpd.read_file(os.path.join(NM, "network.gpkg"), layer="force_mains").to_file(GP, layer="force_mains", driver="GPKG")
# the deepest manhole of every run of sewer deeper than 12 m (pipes joined where they share a manhole)
deep = K[K.depth_max_m > 12]; parent = {}
def find(a):
    while parent.setdefault(a, a) != a: a = parent[a]
    return a
for a, b in zip(deep.from_mh, deep.to_mh): parent[find(a)] = find(b)
runs = collections.defaultdict(set)
for a, b in zip(deep.from_mh, deep.to_mh): runs[find(a)] |= {a, b}
dr = []
for nodes_ in runs.values():
    cand = [n for n in nodes_ if n in node.index and node.at[n, "kind"] == "manhole"]
    if not cand: continue
    n = max(cand, key=lambda n: node.at[n, "depth"])
    dr.append(dict(label=n, depth_m=round(float(node.at[n, "depth"]), 2), map_label=f"{n} {node.at[n, 'depth']:.1f} m",
                   run_km=round(deep[deep.from_mh.isin(nodes_) | deep.to_mh.isin(nodes_)].length_m.sum() / 1000, 2), x=node.at[n, "x"], y=node.at[n, "y"]))
if dr:
    D_ = pd.DataFrame(dr)
    gpd.GeoDataFrame(D_.drop(columns=["x", "y"]), geometry=gpd.points_from_xy(D_.x, D_.y), crs="EPSG:32640").to_file(GP, layer="deep_runs", driver="GPKG")
print(json.dumps({k: Q[k] for k in ("case", "pumps", "lifts", "stations", "force_main_km", "kw_network", "mwh_2031", "mwh_design", "deepest")}))
