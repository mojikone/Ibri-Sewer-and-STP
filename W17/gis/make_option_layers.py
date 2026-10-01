"""One GeoPackage per STP option, built from the SewerGEMS exports of R9, for the W17 QGIS project and the maps.

    python make_option_layers.py            all options with exports
    python make_option_layers.py S1 S3      only these

Layers: pipes (size, depth, flows, plant zone), manholes (depth band), pumping_stations (outfall depth, wet-well depth,
pump head and duty, with the map label), plants (average and peak flow by year), rising_mains (routed along roads and
streets), zones (one outline per plant, from the pipes buffered 60 m), subnetworks (outline per subnetwork).
Depth bands follow the agreed map scheme: up to 12 m on a green-to-navy ramp, beyond 12 m (the hard limit) in red.
"""
import csv, os, sys, collections
import geopandas as gpd, pandas as pd
from shapely import wkt
from shapely.geometry import LineString, Point
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "py"))
from routing import SCENARIOS, YEARS, routing, plant_of, OLD

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
SCEN = r"D:\VBOX\bridge\out\scen"
GEOM = r"D:\VBOX\bridge\out\gis\conduit_geometry.tsv"
RENAME = r"D:\VBOX\bridge\out\inv"
OUT = os.path.join(W17, "Options 2026-10", "11_Network_options")
CRS = "EPSG:32640"
BANDS = [(0, 3, "up to 3 m"), (3, 6, "3 to 6 m"), (6, 9, "6 to 9 m"), (9, 12, "9 to 12 m"), (12, 15, "12 to 15 m"), (15, 99, "over 15 m")]
band = lambda d: next(lab for a, b, lab in BANDS if a <= d < b) if d == d else ""
SUB = lambda lab: lab.split("-")[0] if lab.startswith("O") and ("-M" in lab or "-P" in lab) else None


def old_ids():
    m = {}
    for f in ("rename_nodes.csv", "rename_links.csv"):
        for r in csv.DictReader(open(os.path.join(RENAME, f), encoding="utf-8")):
            m[r["new"]] = r["old"]
    return m


def rd(name, tag, kind):
    p = os.path.join(SCEN, name, f"{kind}_{tag}.csv")
    return pd.read_csv(p) if os.path.exists(p) else None


def build(name):
    pipes = rd(name, f"{name}-2070", "conduits")
    if pipes is None:
        print(name, "no exports yet"); return
    an70 = rd(name, f"{name}-2070a", "conduits"); an30 = rd(name, f"{name}-2030", "conduits")
    mh = rd(name, f"{name}-2070", "manholes")
    old = old_ids()
    plant = plant_of(name)
    tr, joins, stp = routing(name)
    os.makedirs(OUT, exist_ok=True)
    gpkg = os.path.join(OUT, f"{name}.gpkg")
    if os.path.exists(gpkg):
        os.remove(gpkg)

    # ---- manholes
    mh = mh[(mh["active"]) & mh["label"].str.match(r"^O\d+(-M\d+)?$")].copy()
    mh["sub"] = mh["label"].map(lambda l: SUB(l) or l)
    mh["zone"] = mh["sub"].map(lambda s: plant.get(s, ""))
    mh["depth_m"] = (mh["rim"] - mh["invert"]).round(2)
    mh["depth_band"] = mh["depth_m"].map(band)
    mh["old_id"] = mh["label"].map(lambda l: old.get(l, ""))
    nodes = mh.set_index("id")
    g_mh = gpd.GeoDataFrame(mh[["label", "old_id", "sub", "zone", "ground", "invert", "depth_m", "depth_band"]],
                            geometry=[Point(x, y) for x, y in zip(mh["x"], mh["y"])], crs=CRS)
    manholes = g_mh[g_mh["label"].str.contains("-M")]
    manholes.to_file(gpkg, layer="manholes", driver="GPKG")

    # ---- pipes
    geom = {}
    if os.path.exists(GEOM):
        for r in csv.DictReader(open(GEOM, encoding="utf-8"), delimiter="\t"):
            geom[r["label"]] = wkt.loads(r["wkt"])
    p = pipes[(pipes["active"]) & pipes["label"].str.match(r"^O\d+-P\d+$")].copy()
    a70 = an70.set_index("label") if an70 is not None else None
    a30 = an30.set_index("label") if an30 is not None else None
    rows, gs, deep_edges = [], [], []
    for r in p.itertuples():
        s, e = nodes.loc[r.start] if r.start in nodes.index else None, nodes.loc[r.stop] if r.stop in nodes.index else None
        if s is None or e is None:
            continue
        g = geom.get(r.label) or LineString([(s["x"], s["y"]), (e["x"], e["y"])])
        d_up, d_dn = s["ground"] - r.start_inv, e["ground"] - r.stop_inv
        if e["label"] == r.label.replace("-P", "-M"):     # drawn against the flow: the upstream manhole is the stop node
            d_up, d_dn = d_dn, d_up
        od = int(str(r.size_label).split()[0]) if str(r.size_label).split()[0].isdigit() else 0
        q70 = a70.loc[r.label, "flow_m3d"] / 86.4 if a70 is not None else float("nan")
        q30 = a30.loc[r.label, "flow_m3d"] / 86.4 if a30 is not None else float("nan")
        v70 = a70.loc[r.label, "velocity_ms"] if a70 is not None else float("nan")
        dd70 = max(a70.loc[r.label, "depth_in_m"], a70.loc[r.label, "depth_out_m"]) * 1000 / r.diameter_mm if a70 is not None else float("nan")
        sub = SUB(r.label)
        rows.append(dict(label=r.label, old_id=old.get(r.label, ""), sub=sub, zone=plant.get(sub, ""), od_mm=od,
                         id_mm=round(r.diameter_mm, 1), length_m=round(r.length_m, 1),
                         slope_pc=round(100 * abs(r.start_inv - r.stop_inv) / r.length_m, 3) if r.length_m else 0,
                         depth_up_m=round(d_up, 2), depth_dn_m=round(d_dn, 2), depth_avg_m=round((d_up + d_dn) / 2, 2),
                         depth_band=band((d_up + d_dn) / 2), q2030_ls=round(q30, 2), q2070_ls=round(q70, 2),
                         v2070_ms=round(v70, 2), dd2070=round(dd70, 2)))
        gs.append(g)
        if (d_up + d_dn) / 2 > 12:                        # the red bands of the depth map
            deep_edges.append((r.start, r.stop))
    gpd.GeoDataFrame(rows, geometry=gs, crs=CRS).to_file(gpkg, layer="pipes", driver="GPKG")
    gp = gpd.GeoDataFrame(rows, geometry=gs, crs=CRS)

    # ---- the deepest manhole of every run of pipes deeper than 12 m, labelled with its depth alone
    parent = {}
    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for a, b in deep_edges:
        parent[find(a)] = find(b)
    runs = collections.defaultdict(list)
    for a, b in deep_edges:
        runs[find(a)] += [a, b]
    dr, dg = [], []
    for ids in runs.values():
        best = max(set(ids), key=lambda i: nodes.loc[i, "rim"] - nodes.loc[i, "invert"])
        n = nodes.loc[best]; dep = n["rim"] - n["invert"]
        dr.append(dict(label=n["label"], depth_m=round(dep, 2), run_pipes=len(ids) // 2, map_label=f"{dep:.1f}m"))
        dg.append(Point(n["x"], n["y"]))
    if dr:
        gpd.GeoDataFrame(dr, geometry=dg, crs=CRS).to_file(gpkg, layer="deep_runs", driver="GPKG")

    # ---- pumping stations and plants
    pumps_csv = os.path.join(W17, "results", name, f"{name}_pumps.csv")
    pumps = pd.read_csv(pumps_csv) if os.path.exists(pumps_csv) else None
    outf = g_mh[~g_mh["label"].str.contains("-M")].set_index("label")
    ps_rows, ps_g = [], []
    if pumps is not None:
        for r in pumps.itertuples():
            o = outf.loc[r.ps]
            out_depth = o["ground"] - o["invert"]
            # the engineer's label (2026-10-01): outfall, its depth, the average flow through the station; pump head and duty
            lab = f"{r.ps} {out_depth:.1f}m {r.avg2070_m3d:,.0f} m3/d\nPMP {r.H:.0f}m {r.duty:.0f}L/s"
            ps_rows.append(dict(label=r.ps, old_id=r.old, to=r.to, kind=r.kind, ps_type=int(r.type), outfall_depth_m=round(out_depth, 2),
                                wet_well_depth_m=round(r.wet_well_depth, 2), q2070_ls=round(r.q70, 1), duty_ls=round(r.duty, 1),
                                avg2070_m3d=round(r.avg2070_m3d, 0),
                                main_dn=int(r.dn), main_m=round(r.L, 0), static_m=round(r.static, 1), head_m=round(r.H, 1),
                                kw=round(r.kw, 1), mwh_2030=round(r.kwh2030 / 1000, 1), mwh_2070=round(r.kwh2070 / 1000, 1),
                                route=getattr(r, "route", ""), map_label=lab, depth_label=f"{r.ps} {out_depth:.1f}m"))
            ps_g.append(o.geometry)
    if ps_rows:
        gpd.GeoDataFrame(ps_rows, geometry=ps_g, crs=CRS).to_file(gpkg, layer="pumping_stations", driver="GPKG")
    summ = os.path.join(W17, "results", name, f"{name}_plants.csv")
    pl_rows, pl_g = [], []
    if os.path.exists(summ):
        for r in csv.DictReader(open(summ, encoding="utf-8")):
            o = outf.loc[r["plant"]]
            d = {k: (float(v) if k != "plant" else v) for k, v in r.items()}
            d["old_id"] = OLD[r["plant"]]
            dep = o["ground"] - o["invert"]                  # depth of the sewer arriving at the plant
            d["inlet_depth_m"] = round(dep, 2)
            d["map_label"] = f"STP {r['plant']} {dep:.1f}m\n{float(r['avg_2070']):,.0f} m3/d"
            d["short_label"] = f"STP {r['plant']} {dep:.1f}m"
            pl_rows.append(d); pl_g.append(o.geometry)
    if pl_rows:
        gpd.GeoDataFrame(pl_rows, geometry=pl_g, crs=CRS).to_file(gpkg, layer="plants", driver="GPKG")

    # ---- rising mains of this option
    rm_path = os.path.join(W17, "results", "rising_mains.gpkg")
    if os.path.exists(rm_path):
        rm = gpd.read_file(rm_path)
        links = {(s, mhl) for s, mhl, _ in tr} | {(s, z) for s, z in joins.items()}
        rm = rm[[(a, b) in links for a, b in zip(rm["source"], rm["dest"])]].copy()
        if pumps is not None:
            pk = pumps.set_index("ps")
            rm["main_dn"] = rm["source"].map(lambda s: int(pk.loc[s, "dn"]) if s in pk.index else 0)
            rm["duty_ls"] = rm["source"].map(lambda s: round(pk.loc[s, "duty"], 1) if s in pk.index else 0)
            rm["map_label"] = [f"DN{d} rising main, {L:,.0f} m" for d, L in zip(rm["main_dn"], rm["length_m"])]
        rm.to_file(gpkg, layer="rising_mains", driver="GPKG")

    # ---- the 24 outfalls, labelled with the current name only
    of = outf[outf.index.str.match(r"^O\d+$")].reset_index()
    of["zone"] = of["label"].map(lambda s: plant.get(s, ""))
    of["depth_m"] = (of["ground"] - of["invert"]).round(2); of["is_plant"] = of["label"].isin(list(stp))
    gpd.GeoDataFrame(of[["label", "zone", "ground", "invert", "depth_m", "is_plant"]], geometry=list(of.geometry), crs=CRS) \
        .to_file(gpkg, layer="outfalls", driver="GPKG")

    # ---- zones (one per plant) and subnetworks, as outlines of the buffered pipes
    zones = gp.assign(geometry=gp.buffer(60)).dissolve(by="zone").reset_index()[["zone", "geometry"]]
    zones["old_id"] = zones["zone"].map(OLD)
    zones["map_label"] = zones["zone"].map(lambda z: f"Zone of the STP at {z}")
    zones.to_file(gpkg, layer="zones", driver="GPKG")
    subs = gp.assign(geometry=gp.buffer(40)).dissolve(by="sub").reset_index()[["sub", "zone", "geometry"]]
    subs["old_id"] = subs["sub"].map(OLD)
    subs.to_file(gpkg, layer="subnetworks", driver="GPKG")
    print(f"{name}: {len(manholes):,} manholes, {len(rows):,} pipes, {len(ps_rows)} pumping stations, {len(pl_rows)} plants -> {gpkg}")


if __name__ == "__main__":
    names = sys.argv[1:] or list(SCENARIOS)
    for n in names:
        build(n)
