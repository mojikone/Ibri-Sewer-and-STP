# -*- coding: utf-8 -*-
"""W10 Phase 0.5 — rebuild the existing NAMA network as clean, tiered layers.

Regenerates everything in W10/docs/EXISTING_NETWORK.md. Re-runnable, no side effects
outside W10/.

    python W10/py/p05_existing.py

SOURCE NOTE. This reads the ESRI shapefiles NAMA delivered in
`Data/Received/09-RECEIVED/NAMA/IBRI/WW/SHIP`, NOT the KMZ-derived copies in `W7/shp/`.
The KMZ route (W8/py/export_existing.py) loses data: 74 of the 129 proposed gravity
records, 2 of 8 proposed force mains, 2 of 8 treated-effluent mains, and 7 attribute
columns that fall past its 40-field cap. The four headline lengths in PROJECT-STATE
reproduce to the metre from the shapefiles and cannot be reproduced from the KMZ.
"""
from __future__ import annotations

import os
import sys
import warnings

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import rasterio

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "W8", "py"))

import config as CFG                                    # noqa: E402
from sewnet.criteria import DEFAULT as C                 # noqa: E402
from sewnet.hydra import q_partial, v_full              # noqa: E402

SRC = CFG.BASE + r"\Data\Received\09-RECEIVED\NAMA\IBRI\WW\SHIP"
EPSG = CFG.EPSG

# The rising main is catalogued a SECOND time inside the gravity layer as this record
# (project code 8F-1, source cctv, DS_MHID `5A-1-FL-STP`). 88 % of it lies within 100 m
# of the FORCELINE polyline. Counting it as gravity inflates built gravity by 10.5 km.
DUP_RISING_MAIN = "L012750"

# Proposed records carry no manhole IDs, so their tier is banded on nominal diameter.
# This is our banding, not NAMA's — the built network is 160/200 mm throughout and so
# offers no diameter signature to calibrate against.
PROP_TIER_BANDS = [(600, "trunk_main"), (315, "sub_main"), (0, "lateral")]


# ----------------------------------------------------------------- helpers
def _zone(mhid):
    """`5A-2-SM.2-MH391` -> `5A-2-SM.2`. Every built ID is exactly 4 tokens."""
    p = str(mhid).split("-")
    return "-".join(p[:3]) if len(p) >= 4 else None


def _tier(mhid):
    """The designer's own decomposition, read off the third token."""
    p = str(mhid).split("-")
    t = p[2] if len(p) >= 4 else ""
    if t.startswith("TM"):
        return "trunk_main"
    if t.startswith("SM"):
        return "sub_main"
    return "lateral"


def _num(s):
    return pd.to_numeric(s, errors="coerce").replace(0, np.nan)


def _components(gdf, snap=0.5):
    """Endpoint-snapped connectivity — the independent check on the ID topology."""
    def k(p):
        return (round(p[0] / snap), round(p[1] / snap))
    G = nx.Graph()
    for i, r in gdf.iterrows():
        c = list(r.geometry.coords)
        G.add_edge(k(c[0]), k(c[-1]), i=i)
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    n2c = {n: j for j, c in enumerate(comps) for n in c}
    return [n2c[k(list(r.geometry.coords)[0])] for _, r in gdf.iterrows()], G


def _write(gdf, name):
    p = os.path.join(CFG.OUT_SHP, name + ".shp")
    gdf.to_file(p, encoding="utf-8")
    return p


# ----------------------------------------------------------------- load
def load():
    bnd = gpd.read_file(CFG.BOUNDARY).to_crs(EPSG)
    lay = {}
    for n in ("SEWERLINE", "FORCELINE", "TE_LINE", "STP_PT", "GR_TEPS", "STP_BUILDING"):
        lay[n] = gpd.read_file(f"{SRC}/{n}_IBRI.shp").to_crs(EPSG)
    return bnd, lay


# ----------------------------------------------------------------- built gravity
def build_built(sew, clip_geom):
    b = sew[sew.OP_STATUE == 1].copy()
    b["IS_DUP"] = (b.FEATUREID == DUP_RISING_MAIN).astype(int)
    b["TIER"] = b.US_MHID.map(_tier)
    b["ZONE"] = b.US_MHID.map(_zone)
    b.loc[b.IS_DUP == 1, "TIER"] = "rising_main"

    for a, c in (("US_INV", "US_INVERT_"), ("DS_INV", "DS_INVERT_"),
                 ("US_GRD", "US_GROUND_"), ("DS_GRD", "DS_GROUND_")):
        b[a] = _num(b[c])
    b["DIA_OUT"] = _num(b.OUT_DIAMET)
    b["DIA_IN"] = _num(b.IN_DIAMETE)
    b["LEN_M"] = b.geometry.length
    b["SLOPE_PCT"] = 100.0 * (b.US_INV - b.DS_INV) / b.LEN_M
    b["DEP_US"] = b.US_GRD - b.US_INV
    b["DEP_DS"] = b.DS_GRD - b.DS_INV
    b["HAS_LVL"] = b.US_INV.notna().astype(int)

    # systems: endpoint connectivity on the true gravity only
    g = b[b.IS_DUP == 0].copy()
    gc, _ = _components(g)
    g["GC"] = gc
    order = g.groupby("GC").geometry.count().sort_values(ascending=False).index
    label = {}
    for j in order:
        pk = sorted(g[g.GC == j].PROJECTCOD.unique())
        label[j] = "+".join(pk)
    g["SYSTEM"] = g.GC.map(label)
    b["SYSTEM"] = g.SYSTEM
    b.loc[b.IS_DUP == 1, "SYSTEM"] = "rising_main_duplicate"

    keep = ["FEATUREID", "PROJECTCOD", "SYSTEM", "TIER", "ZONE", "US_MHID", "DS_MHID",
            "US_INV", "DS_INV", "US_GRD", "DS_GRD", "DEP_US", "DEP_DS", "DIA_OUT",
            "DIA_IN", "MATERIAL", "SUBTYPE", "LEN_M", "SLOPE_PCT", "HAS_LVL", "IS_DUP",
            "INSTALLDAT", "SOURCE", "geometry"]
    out = gpd.GeoDataFrame(b[keep], geometry="geometry", crs=EPSG)
    out["INSTALLDAT"] = out.INSTALLDAT.astype(str).str[:10]
    out = gpd.clip(out, clip_geom)
    out["LEN_M"] = out.geometry.length
    return out


# ----------------------------------------------------------------- proposed
def build_proposed(sew, clip_geom):
    p = sew[sew.OP_STATUE == 0].copy()
    p["DIA_NOM"] = _num(p.N_DIAMETER)

    def band(d):
        for lo, t in PROP_TIER_BANDS:
            if pd.notna(d) and d >= lo:
                return t
        return "lateral"
    p["TIER"] = p.DIA_NOM.map(band)
    p["TIER_SRC"] = "diameter band (W10) — no manhole IDs on proposed records"
    p["LEN_M"] = p.geometry.length
    p["US_MHID"] = None
    p["DS_MHID"] = None
    keep = ["FEATUREID", "PROJECTCOD", "TIER", "TIER_SRC", "US_MHID", "DS_MHID",
            "DIA_NOM", "SUBTYPE", "REMARKS", "STATUS", "LEN_M", "geometry"]
    out = gpd.GeoDataFrame(p[keep], geometry="geometry", crs=EPSG)
    out = gpd.clip(out, clip_geom)
    out["LEN_M"] = out.geometry.length
    return out


# ----------------------------------------------------------------- force / TE
def build_force(force, clip_geom):
    f = force.copy()
    f["STATUSCLS"] = np.where(f.OP_STATUE == 1, "built", "proposed")
    f["DIA_NOM"] = _num(f.N_DIAMETER)
    f["LEN_M"] = f.geometry.length
    keep = ["FEATUREID", "PROJECTCOD", "STATUSCLS", "DIA_NOM", "REMARKS", "STATUS",
            "LEN_M", "geometry"]
    out = gpd.clip(gpd.GeoDataFrame(f[keep], geometry="geometry", crs=EPSG), clip_geom)
    out["LEN_M"] = out.geometry.length
    return out


def build_te(te, clip_geom):
    t = te.copy()
    t["STATUSCLS"] = np.where(t.OP_STATUE == 1, "built", "proposed")
    t["DIA_NOM"] = _num(t.N_DIAMETER)
    t["LEN_M"] = t.geometry.length
    keep = ["FEATUREID", "PROJECTCOD", "STATUSCLS", "DIA_NOM", "REMARKS", "STATUS",
            "LEN_M", "geometry"]
    out = gpd.clip(gpd.GeoDataFrame(t[keep], geometry="geometry", crs=EPSG), clip_geom)
    out["LEN_M"] = out.geometry.length
    return out


# ----------------------------------------------------------------- nodes
def build_nodes(built, force, stp_pt, teps, terrain):
    """STP records, the pumping station, and the outfall head of the 5A-2/3/4 system.

    The pumping station has NO record of its own in the delivered data. It exists only
    as the manhole ID `5A-1-FL-SPS` and as the upstream end of the force main. That is a
    gap, not a coordinate we invented.
    """
    rows = []
    for _, r in stp_pt.iterrows():
        rows.append(dict(NODE="STP", NAME=str(r.STP_NAME), STATUSCLS=str(r.STATUS),
                         CAP_M3D=float(r.CAPACITY or 0), PROJECTCOD=str(r.PROJECTCOD),
                         SOURCE=str(r.SOURCE), NOTE="STP_PT record",
                         geometry=r.geometry))
    for _, r in teps.iterrows():
        rows.append(dict(NODE="TE_PUMPS", NAME=str(r.PSNAME), STATUSCLS=str(r.STATUS),
                         CAP_M3D=0.0, PROJECTCOD=str(r.PROJECTCOD), SOURCE=str(r.SOURCE),
                         NOTE="treated-effluent pumps, proposed", geometry=r.geometry))

    fb = force[force.OP_STATUE == 1]
    if len(fb):
        from shapely.geometry import Point
        c = list(fb.iloc[0].geometry.coords)
        rows.append(dict(NODE="SPS", NAME="Existing sewage pumping station",
                         STATUSCLS="Ex", CAP_M3D=0.0, PROJECTCOD="5A-1", SOURCE="derived",
                         NOTE="no point record supplied; head of the built rising main "
                              "and the manhole ID 5A-1-FL-SPS",
                         geometry=Point(c[0])))
        outf = built[built.DS_MHID == "5A-4-SM-MH917"]
        if len(outf):
            cc = list(outf.iloc[0].geometry.coords)
            rows.append(dict(NODE="OUTFALL", NAME="5A-4-SM-MH917",
                             STATUSCLS="Ex", CAP_M3D=0.0, PROJECTCOD="5A-4",
                             SOURCE="derived",
                             NOTE="head of the 5A-2/3/4 system; the 8F-1 line starts here",
                             geometry=Point(cc[-1])))
    n = gpd.GeoDataFrame(rows, geometry="geometry", crs=EPSG)
    with rasterio.open(terrain) as r:
        z = [v[0] for v in r.sample([(p.x, p.y) for p in n.geometry])]
        nd = r.nodata
    n["GROUND_M"] = [round(float(v), 2) if v != nd else None for v in z]
    n["E"] = n.geometry.x.round(1)
    n["N"] = n.geometry.y.round(1)
    return n


# ----------------------------------------------------------------- analyses
def hierarchy_stats(built):
    g = built[built.IS_DUP == 0]
    zt = g.groupby("ZONE").TIER.first().to_dict()
    rows = []
    for _, r in g.iterrows():
        dz = _zone(r.DS_MHID)
        if r.ZONE and dz and dz != r.ZONE:
            rows.append((zt.get(r.ZONE), zt.get(dz, "outside_dataset")))
    fl = pd.DataFrame(rows, columns=["from_tier", "to_tier"])
    return g, zt, fl


def force_main_profile(force, terrain, step=10.0):
    fb = force[force.OP_STATUE == 1].iloc[0].geometry
    ch = np.append(np.arange(0, fb.length, step), fb.length)
    pts = [fb.interpolate(c) for c in ch]
    with rasterio.open(terrain) as r:
        z = np.array([v[0] for v in r.sample([(p.x, p.y) for p in pts])], float)
        z[z == r.nodata] = np.nan
    return fb, ch, z


def gravity_check(ch, z, il_plant):
    """Shallowest feasible gravity profile on this alignment, per diameter.

    Walk downstream hugging the minimum-cover ceiling, dropping at the Table-11
    minimum gradient wherever the ground will not fall that fast on its own. That is
    the shallowest pipe that still self-cleanses, so its depth is a LOWER bound on how
    deep a gravity main here has to be, and its arrival level is the HIGHEST it can
    reach the plant at.
    """
    out = []
    for dn in [400, 500, 600, 700, 800, 900, 1000, 1200]:
        D = C.internal_diameter(dn)
        OD = C.outside_diameter(dn)
        S = C.TABLE11.get(dn, C.TABLE11_FLOOR)
        dod = C.DOD_MAX_SMALL if dn <= C.DOD_DN_THRESHOLD else C.DOD_MAX_LARGE
        ceil_ = z - C.MIN_COVER_CROWN - OD
        inv = np.empty_like(z)
        inv[0] = ceil_[0]
        for i in range(1, len(ch)):
            inv[i] = min(ceil_[i], inv[i - 1] - S * (ch[i] - ch[i - 1]))
        dep = z - inv
        q = q_partial(D, S, dod * D) * 1000.0
        out.append(dict(DN=dn, S_PCT=round(S * 100, 3),
                        ARRIVE_IL=round(inv[-1], 2),
                        VS_PLANT=round(inv[-1] - il_plant, 2),
                        MAX_DEPTH=round(dep.max(), 2),
                        AT_CH=int(ch[dep.argmax()]),
                        LEN_OVER_12M=int(np.trapezoid((dep > C.MAX_DEPTH).astype(float), ch)),
                        V_FULL=round(v_full(D, S), 2),
                        Q_PEAK_LS=round(q, 1),
                        Q_PEAK_M3D=int(q * 86.4)))
    return pd.DataFrame(out)


# ----------------------------------------------------------------- main
def main():
    for d in (CFG.OUT_SHP, CFG.OUT_RUN, CFG.OUT_DOCS):
        os.makedirs(d, exist_ok=True)
    bnd, lay = load()
    clip_geom = bnd.union_all()
    print(f"boundary {bnd.area.sum()/1e6:,.2f} km2")

    built = build_built(lay["SEWERLINE"], clip_geom)
    prop = build_proposed(lay["SEWERLINE"], clip_geom)
    force = build_force(lay["FORCELINE"], clip_geom)
    te = build_te(lay["TE_LINE"], clip_geom)
    nodes = build_nodes(built, lay["FORCELINE"], lay["STP_PT"], lay["GR_TEPS"],
                        CFG.TERRAIN)

    for g, n in ((built, "W10_existing_built"), (prop, "W10_existing_proposed"),
                 (force, "W10_existing_force"), (te, "W10_existing_te"),
                 (nodes, "W10_existing_nodes")):
        print(f"  {n:26s} {len(g):5d} features -> {os.path.basename(_write(g, n))}")

    # ---- (a) headline lengths
    tot = pd.DataFrame([
        dict(layer="gravity", status="built (incl. 8F-1 duplicate)",
             n=int((built.IS_DUP == 0).sum() + (built.IS_DUP == 1).sum()),
             km=round(built.LEN_M.sum() / 1000, 3)),
        dict(layer="gravity", status="built, true gravity",
             n=int((built.IS_DUP == 0).sum()),
             km=round(built[built.IS_DUP == 0].LEN_M.sum() / 1000, 3)),
        dict(layer="gravity", status="proposed SUREKHA", n=len(prop),
             km=round(prop.LEN_M.sum() / 1000, 3)),
        dict(layer="force main", status="built", n=int((force.STATUSCLS == "built").sum()),
             km=round(force[force.STATUSCLS == "built"].LEN_M.sum() / 1000, 3)),
        dict(layer="force main", status="proposed",
             n=int((force.STATUSCLS == "proposed").sum()),
             km=round(force[force.STATUSCLS == "proposed"].LEN_M.sum() / 1000, 3)),
        dict(layer="treated effluent", status="built", n=0, km=0.0),
        dict(layer="treated effluent", status="proposed", n=len(te),
             km=round(te.LEN_M.sum() / 1000, 3)),
    ])
    tot.to_csv(os.path.join(CFG.OUT_RUN, "p05_lengths.csv"), index=False)
    print("\n" + tot.to_string(index=False))

    # ---- (b) attribute completeness, BUILT gravity, from the raw table
    raw = lay["SEWERLINE"]
    rb, rp = raw[raw.OP_STATUE == 1], raw[raw.OP_STATUE == 0]
    rows = []
    for c in raw.columns:
        if c == "geometry":
            continue

        def pct(df):
            s = df[c]
            if s.dtype.kind in "ifc":
                ok = s.notna() & (s != 0)
            elif s.dtype.kind == "M":
                ok = s.notna()
            else:
                ok = s.notna() & ~s.astype(str).str.strip().isin(
                    ["", "<Null>", "Null", "None", "nan", "0"])
            return round(100 * ok.sum() / max(len(df), 1), 1)
        rows.append(dict(field=c, built_pct=pct(rb), proposed_pct=pct(rp)))
    comp = pd.DataFrame(rows)
    comp.to_csv(os.path.join(CFG.OUT_RUN, "p05_completeness.csv"), index=False)

    lvl = rb.assign(has=_num(rb.US_INVERT_).notna()).groupby("PROJECTCOD").has.agg(
        ["size", "sum", "mean"]).rename(columns={"size": "pipes", "sum": "with_levels"})
    lvl["pct"] = (100 * lvl.pop("mean")).round(1)
    lvl.to_csv(os.path.join(CFG.OUT_RUN, "p05_levels_by_package.csv"))
    print("\nlevels by package:\n" + lvl.to_string())

    # ---- (c) hierarchy and connectivity
    g, zt, fl = hierarchy_stats(built)
    tier = g.groupby("TIER").LEN_M.agg(n="size", km=lambda s: round(s.sum() / 1000, 2))
    tier["pct"] = (100 * tier.km / tier.km.sum()).round(1)
    tier["zones"] = g.groupby("TIER").ZONE.nunique()
    tier["med_pipe_m"] = g.groupby("TIER").LEN_M.median().round(1)
    zl = g.groupby("ZONE").LEN_M.sum()
    tier["med_zone_m"] = g.groupby("TIER").ZONE.apply(
        lambda s: round(zl[s.unique()].median(), 1))
    tier.to_csv(os.path.join(CFG.OUT_RUN, "p05_tiers.csv"))
    print("\ntiers:\n" + tier.to_string())

    lat = fl[fl.from_tier == "lateral"].to_tier.value_counts()
    lat.to_csv(os.path.join(CFG.OUT_RUN, "p05_lateral_outflow.csv"))
    print("\nwhere lateral zones drain:\n" + lat.to_string())

    sysm = g.groupby("SYSTEM").LEN_M.agg(n="size", km=lambda s: round(s.sum() / 1000, 2))
    sysm.to_csv(os.path.join(CFG.OUT_RUN, "p05_systems.csv"))
    print("\nsystems:\n" + sysm.to_string())

    _, G = _components(g)
    deg = dict(G.degree())
    km = g.LEN_M.sum() / 1000
    dens = pd.Series({"nodes": len(deg),
                      "junctions_deg3plus": sum(1 for v in deg.values() if v >= 3),
                      "dead_ends_deg1": sum(1 for v in deg.values() if v == 1),
                      "manholes_per_km": round(len(deg) / km, 2),
                      "junctions_per_km": round(
                          sum(1 for v in deg.values() if v >= 3) / km, 2)})
    dens.to_csv(os.path.join(CFG.OUT_RUN, "p05_density.csv"))
    print("\ndensity:\n" + dens.to_string())

    # gradients actually built
    h = g[g.SLOPE_PCT.notna()]
    grad = (h.SLOPE_PCT * 10).describe(percentiles=[.05, .25, .5, .75, .95]).round(3)
    grad.to_csv(os.path.join(CFG.OUT_RUN, "p05_gradients_mm_per_m.csv"))
    print("\nbuilt gradients, mm/m:\n" + grad.to_string())

    # ---- what the built network reaches: electricity accounts within a frontage of it
    acc = gpd.read_file(CFG.ACCOUNTS).to_crs(EPSG)
    served = []
    for name, sub in list(g.groupby("SYSTEM")) + [("ALL BUILT", g)]:
        buf = sub.geometry.buffer(CFG.PLOT_SERVED_M).union_all()
        n = int(acc.geometry.within(buf).sum())
        served.append(dict(system=name, km=round(sub.LEN_M.sum() / 1000, 2),
                           accounts=n,
                           qadf_m3d=round(n * C.PLOT_QADF_M3D, 0)))
    sv = pd.DataFrame(served)
    sv.to_csv(os.path.join(CFG.OUT_RUN, "p05_served.csv"), index=False)
    print(f"\naccounts within {CFG.PLOT_SERVED_M:.0f} m of the built network "
          f"(of {len(acc):,} in the study area):\n" + sv.to_string(index=False))

    # ---- (d) force main profile and the gravity question
    fb, ch, z = force_main_profile(lay["FORCELINE"], CFG.TERRAIN)
    prof = pd.DataFrame(dict(CH_M=ch.round(1), GROUND_M=z.round(2)))
    prof.to_csv(os.path.join(CFG.OUT_RUN, "p05_forcemain_profile.csv"), index=False)
    il_plant = 322.99      # arrival invert of the built 5A-5 trunk at the plant (NAMA)
    chk = gravity_check(ch, z, il_plant)
    chk.to_csv(os.path.join(CFG.OUT_RUN, "p05_gravity_check.csv"), index=False)
    print(f"\nforce main {fb.length:,.0f} m, ground {z[0]:.2f} -> {z[-1]:.2f}, "
          f"fall {z[0]-z[-1]:.2f} m, avg {100*(z[0]-z[-1])/fb.length:.3f} %")
    print(f"lowest ground on route {z.min():.2f} at ch {ch[z.argmin()]:.0f} "
          f"(that is {z[-1]-z.min():.2f} m BELOW the ground at the plant)")
    print("\ngravity main on the same alignment (plant inlet 322.99 m):")
    print(chk.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
