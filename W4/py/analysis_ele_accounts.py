# -*- coding: utf-8 -*-
"""Electricity subscriber accounts -> properties per plot.

Purpose: replace the assumed PROPS_PER_PLOT = 1.0 (GAP-5) with a counted value, and give
the load model a land-use basis (GUD-201 Tier B) instead of a blanket per-capita rate.

Source: Data/Received/09-RECEIVED/NAMA/IBRI ELE ACCOUNTS.kmz — 33,970 placemarks, each an
electricity account with a TARIFF and X/Y already in EPSG:32640.

Outputs:
  W4/shp/ELE_accounts.shp       points with TARIFF, CATEGORY and the plot they fall in
  W4/analysis/ele_accounts.md   the distribution tables
"""
import collections
import os
import re
import zipfile

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"
KMZ = os.path.join(BASE, r"Data\Received\09-RECEIVED\NAMA\IBRI ELE ACCOUNTS.kmz")
PLOTS = os.path.join(BASE, r"Hydraulic\Claude\W3\shp\MoH_Plots_class_v4.shp")
BOUNDARY = os.path.join(BASE, r"Hydraulic\SHP\temp\Netwrok desing test boudary.shp")
W4 = os.path.join(BASE, r"Hydraulic\Claude\W4")

# tariff -> load category. Agricultural is a TE customer, not a sewage load (doctrine 2.1).
CATEGORY = {
    "Primary Account Tariff": "domestic",
    "Primary Account Tariff (with National Subsidy)": "domestic",
    "Additional Account Tariff": "domestic_additional",
    "Commercial": "commercial",
    "Government": "government",
    "Agricultural": "agricultural",
    "Fisheries": "commercial",
    "Industrial": "industrial",
    "Tourism": "commercial",
    "MOD": "government",
    "CRT Seasonal": "crt",
    "CRT Time of Use": "crt",
    "CRT Fixed Rate": "crt",
}


def parse_kmz(path):
    z = zipfile.ZipFile(path)
    raw = z.read("doc.kml").decode("utf-8", "ignore")
    chunks = raw.split("<Placemark")[1:]
    td = re.compile(r"<td>(.*?)</td>", re.S)
    name_re = re.compile(r"<name>(.*?)</name>", re.S)
    rows = []
    for ch in chunks:
        cells = td.findall(ch)
        nm = name_re.search(ch)
        tariff = (nm.group(1).strip() if nm else "")
        x = y = None
        for i, c in enumerate(cells):
            c = c.strip()
            if c == "X" and i + 1 < len(cells):
                try:
                    x = float(cells[i + 1].strip())
                except ValueError:
                    pass
            elif c == "Y" and i + 1 < len(cells):
                try:
                    y = float(cells[i + 1].strip())
                except ValueError:
                    pass
        if x is not None and y is not None:
            rows.append((tariff, x, y))
    return rows


def main():
    print("parsing KMZ ...")
    rows = parse_kmz(KMZ)
    print(f"  {len(rows):,} accounts with coordinates")
    df = pd.DataFrame(rows, columns=["TARIFF", "X", "Y"])
    df["CATEGORY"] = df["TARIFF"].map(CATEGORY).fillna("other")
    pts = gpd.GeoDataFrame(df, geometry=[Point(x, y) for x, y in zip(df.X, df.Y)],
                           crs="EPSG:32640")

    print("joining to plots ...")
    plots = gpd.read_file(PLOTS, encoding="utf-8")[["OBJECTID", "CLASS", "AREA_M2", "geometry"]]
    j = gpd.sjoin(pts, plots, how="left", predicate="within")
    pts["PLOT_ID"] = j["OBJECTID"].values
    pts["PLOT_CLS"] = j["CLASS"].values

    os.makedirs(os.path.join(W4, "shp"), exist_ok=True)
    os.makedirs(os.path.join(W4, "analysis"), exist_ok=True)
    pts.drop(columns=["X", "Y"]).to_file(os.path.join(W4, "shp", "ELE_accounts.shp"),
                                         encoding="utf-8")

    L = []
    L.append("# Electricity accounts -> properties per plot\n")
    L.append(f"Source: `IBRI ELE ACCOUNTS.kmz` — **{len(pts):,} accounts**, EPSG:32640.\n")

    L.append("## Accounts by category\n")
    L.append("| Category | Accounts | Share |\n|---|---|---|")
    for cat, n in pts["CATEGORY"].value_counts().items():
        L.append(f"| {cat} | {n:,} | {n/len(pts)*100:.1f} % |")
    inside = pts["PLOT_ID"].notna().sum()
    L.append(f"\n**{inside:,} accounts ({inside/len(pts)*100:.1f} %) fall inside a cadastral "
             f"plot**; {len(pts)-inside:,} fall outside (unparceled buildings, road-side "
             f"services, or cadastre gaps).\n")

    # ---- properties per plot
    sew = pts[~pts["CATEGORY"].isin(["agricultural"])]        # farms carry no sewage load
    per_plot = sew[sew["PLOT_ID"].notna()].groupby("PLOT_ID").size()
    dom = pts[pts["CATEGORY"].isin(["domestic", "domestic_additional"])]
    dom_per_plot = dom[dom["PLOT_ID"].notna()].groupby("PLOT_ID").size()

    L.append("## Accounts per plot (agricultural excluded)\n")
    L.append(f"- plots with at least one account: **{len(per_plot):,}**")
    L.append(f"- mean **{per_plot.mean():.2f}**, median **{per_plot.median():.0f}**, "
             f"max **{per_plot.max()}**")
    L.append(f"- domestic only: mean **{dom_per_plot.mean():.2f}**, "
             f"median **{dom_per_plot.median():.0f}**, max **{dom_per_plot.max()}**\n")
    L.append("| Accounts on the plot | Plots | Share |\n|---|---|---|")
    vc = per_plot.value_counts().sort_index()
    for k, n in vc.items():
        lab = f"{int(k)}" if k < 6 else None
        if lab:
            L.append(f"| {lab} | {n:,} | {n/len(per_plot)*100:.1f} % |")
    six = vc[vc.index >= 6].sum()
    L.append(f"| 6 or more | {six:,} | {six/len(per_plot)*100:.1f} % |")

    # ---- by plot class
    plots_idx = plots.set_index("OBJECTID")
    cls = plots_idx["CLASS"].reindex(per_plot.index)
    L.append("\n## By plot class\n")
    L.append("| CLASS | Plots with accounts | Mean accounts | Max |\n|---|---|---|---|")
    for c in ["B", "P", "A"]:
        m = cls == c
        if m.sum():
            L.append(f"| {c} | {m.sum():,} | {per_plot[m.values].mean():.2f} | "
                     f"{per_plot[m.values].max()} |")

    # ---- the assumption being replaced
    built = (plots["CLASS"] == "B").sum()
    L.append(f"\n## Against the current assumption\n")
    L.append(f"The pipeline assumes `PROPS_PER_PLOT = 1.0` for every plot [GAP-5]. Measured on "
             f"built plots, the mean is **{per_plot[(cls=='B').values].mean():.2f}** accounts "
             f"per plot that has any account.\n")
    L.append(f"- built plots in the cadastre: {built:,}")
    L.append(f"- built plots carrying at least one account: {(cls=='B').sum():,} "
             f"({(cls=='B').sum()/built*100:.1f} %)\n")

    # ---- test boundary
    b = gpd.read_file(BOUNDARY)
    from shapely.validation import make_valid
    geom = make_valid(b.geometry.iloc[0])
    if geom.geom_type == "GeometryCollection":
        geom = max([g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")],
                   key=lambda g: g.area)
    inb = pts[pts.within(geom)]
    L.append("## Inside the W4 test boundary\n")
    L.append(f"- accounts: **{len(inb):,}**")
    L.append("\n| Category | Accounts |\n|---|---|")
    for cat, n in inb["CATEGORY"].value_counts().items():
        L.append(f"| {cat} | {n:,} |")
    inb_sew = inb[~inb["CATEGORY"].isin(["agricultural"])]
    pp = inb_sew[inb_sew["PLOT_ID"].notna()].groupby("PLOT_ID").size()
    L.append(f"\n- plots with accounts: **{len(pp):,}** (the design currently loads 2,987 units)")
    L.append(f"- mean accounts per plot **{pp.mean():.2f}**, max **{pp.max()}**")
    multi = (pp >= 2).sum()
    L.append(f"- plots with 2 or more accounts: **{multi:,}** ({multi/len(pp)*100:.1f} %) "
             f"— these are the plots needing more than one connection\n")

    out = os.path.join(W4, "analysis", "ele_accounts.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
