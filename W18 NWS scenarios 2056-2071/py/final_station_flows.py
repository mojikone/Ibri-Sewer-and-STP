"""W18 final design: the people and the average flow at every pumping station, lift station and plant, every five years
2026-2061 (engineer, 2026-11-19: "for each STP, pump and lift ... the number of people and flow m3/day for each 5 year").

  own      the catchment that drains by gravity to the station (its section): residents of the connected plots
           (gis/W18_plots_2026_2100.shp, POP_yyyy, by the manhole each plot loads), their sewage (results/loads/
           manhole_loads.csv, Q_yyyy, which also carries shops, offices and the estates) and the infiltration of the
           section's sewers (0.72 m3/d per km). The catchments are the same in the four scenarios.
  through  what the station passes on: its own catchment and everything pumped into it, per scenario (the plant inlet
           stations carry the whole flow of their plant).
Usage: python final_station_flows.py     Writes results/final_0.75pc_SC1-SC4/station_flows.csv (long) and
       station_flows_wide.csv (one row per scenario and station, people and flow by year)."""
import os, collections
import pandas as pd, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
YEARS = [2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061]; INF = 0.72; SC = ["SC1", "SC2", "SC3", "SC4"]

plots = gpd.read_file(os.path.join(W18, "gis", "W18_plots_2026_2100.shp"), ignore_geometry=True)
plots = plots[plots.NETWORK == "connected"]
loads = pd.read_csv(os.path.join(R, "..", "loads", "manhole_loads.csv")).set_index("manhole_id")
rows = []
for sc in SC:
    c = f"{sc}-2056"
    N = pd.read_csv(os.path.join(R, c, "named", "nodes.csv")); K = pd.read_csv(os.path.join(R, c, "named", "links.csv"))
    S = pd.read_csv(os.path.join(R, c, "products", "stations.csv"))
    sec_of_id = N.set_index("id").section; sec_of = N.set_index("new").section
    km = K.groupby("section").length_m.sum() / 1000
    pop = {y: plots.assign(s=plots.MH_W18.map(sec_of_id)).groupby("s")[f"POP_{y}"].sum() for y in YEARS}
    q = {y: loads.assign(s=loads.index.map(sec_of_id))[["s", f"Q_{y}"]].groupby("s")[f"Q_{y}"].sum() for y in YEARS}
    into = collections.defaultdict(list)
    for r in S.itertuples():
        if r.kind == "plant inlet": continue
        tgt = r.pumps_to.split("STP at ")[1] if str(r.pumps_to).startswith("STP at ") else sec_of[r.pumps_to]
        into[tgt].append(r.name)

    def own(s, y): return float(pop[y].get(s, 0)), float(q[y].get(s, 0)) + float(km.get(s, 0)) * INF
    def through(s, y):
        p, f = own(s, y)
        for u in into[s]: pu, fu = through(u, y); p += pu; f += fu
        return p, f
    stp = {"P1": "STP-1" if sc in ("SC1", "SC3") else None, "P7": "STP-2" if sc in ("SC2", "SC4") else None, "P2": "STP-5" if sc in ("SC3", "SC4") else None}
    for r in S.itertuples():
        for y in YEARS:
            po, fo = own(r.name, y); pt, ft = through(r.name, y)
            rows.append(dict(scenario=sc, station=r.name, kind=r.kind, plant=stp.get(r.name) if r.kind == "plant inlet" else None,
                             discharges_to=r.pumps_to, year=y, people_own=round(po), flow_own_m3d=round(fo, 1), people_through=round(pt), flow_through_m3d=round(ft, 1)))
L = pd.DataFrame(rows); L.to_csv(os.path.join(R, "station_flows.csv"), index=False)
# checks: the plant inlets carry all the flow of their plant, equal to products/plants.csv
for sc in SC:
    pl = pd.read_csv(os.path.join(R, f"{sc}-2056", "products", "plants.csv"))
    for p in pl.itertuples():
        for y in (2031, 2056):
            v = L[(L.scenario == sc) & (L.station == p.plant) & (L.year == y)].flow_through_m3d.iloc[0]
            assert abs(v - getattr(p, f"avg_{y}_m3d")) < 2, (sc, p.plant, y, v, getattr(p, f"avg_{y}_m3d"))
W = L.pivot_table(index=["scenario", "station", "kind"], columns="year", values=["people_own", "flow_own_m3d", "people_through", "flow_through_m3d"])
W.columns = [f"{a}_{b}" for a, b in W.columns]; W.reset_index().to_csv(os.path.join(R, "station_flows_wide.csv"), index=False)
tot = L[(L.scenario == "SC1") & (L.year == 2056)]
print("checked: plant inflows equal products; SC1 2056 people at the stations", int(tot.people_own.sum()), "flow", round(tot.flow_own_m3d.sum()))
