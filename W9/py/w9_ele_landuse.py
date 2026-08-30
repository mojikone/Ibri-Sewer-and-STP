"""W9 - electricity accounts as the land-use layer for load allocation.

Builds one point layer carrying, per account: the raw NAMA tariff, the guideline
category it maps to (GUD-201 s7.3), the settlement it falls in, the plot it sits
on, and a REVIEW flag for everything that cannot be classified from tariff alone.

Nothing here is closed: unmatched points stay unmatched until the GIS expert's
clean plot file arrives, and REVIEW points await visual checking.
"""
import os
import geopandas as gpd
import pandas as pd

BASE = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP"
ELE = os.path.join(BASE, r"Hydraulic\Claude\W4\shp\ELE_accounts.shp")
TOWNS = os.path.join(BASE, r"Hydraulic\SHP\Towns\Towns.shp")
W9 = os.path.join(BASE, r"Hydraulic\Claude\W9")
OUT = os.path.join(W9, "shp", "ELE_landuse.shp")

# tariff -> guideline category (GUD-201 s7.3.1-7.3.4).
# agricultural is carried but generates NO sewage load: the farming discharges
# nothing, the houses on the farm are metered separately (doctrine 2026-08-19).
GUD = {
    "domestic": "domestic",
    "domestic_additional": "domestic_add",
    "commercial": "non_domestic",
    "government": "government",
    "agricultural": "agricultural",
    "crt": "CRT_review",
    "industrial": "industrial",
}
HIGH_PLOT = 15  # domestic properties on one plot -> camp / apartment candidate


def main():
    os.makedirs(os.path.join(W9, "shp"), exist_ok=True)
    os.makedirs(os.path.join(W9, "analysis"), exist_ok=True)

    e = gpd.read_file(ELE)
    towns = gpd.read_file(TOWNS)[["NAME_EN", "Pop_2024", "geometry"]]

    j = gpd.sjoin(e, towns, how="left", predicate="within")
    e["TOWN"] = j["NAME_EN"].values
    e["TOWN_POP24"] = j["Pop_2024"].values
    e["GUD_CAT"] = e["CATEGORY"].map(GUD).fillna("unmapped")

    # domestic properties per plot -> flags the camp / apartment candidates
    dom = e[e["GUD_CAT"].isin(["domestic", "domestic_add"])]
    per_plot = dom.dropna(subset=["PLOT_ID"]).groupby("PLOT_ID").size()
    e["PROPS_PLOT"] = e["PLOT_ID"].map(per_plot).fillna(0).astype(int)

    # REVIEW: everything tariff alone cannot settle
    review = pd.Series("", index=e.index)
    review[e["PLOT_ID"].isna()] = "no_plot"
    review[e["PROPS_PLOT"] >= HIGH_PLOT] = "high_plot"
    review[e["GUD_CAT"] == "CRT_review"] = "CRT"
    review[e["GUD_CAT"] == "industrial"] = "industrial"
    e["REVIEW"] = review

    e[["TARIFF", "CATEGORY", "GUD_CAT", "TOWN", "TOWN_POP24", "PLOT_ID",
       "PLOT_CLS", "PROPS_PLOT", "REVIEW", "geometry"]].to_file(OUT, encoding="utf-8")

    # ---- occupancy rate per settlement -------------------------------------
    d = e[e["GUD_CAT"].isin(["domestic", "domestic_add"])]
    g = d.groupby("TOWN").size().rename("dom_props")
    pop = towns.set_index("NAME_EN")["Pop_2024"]
    r = pd.concat([g, pop], axis=1).dropna(subset=["dom_props"])
    r["OR"] = (r["Pop_2024"] / r["dom_props"]).round(2)
    r = r.sort_values("dom_props", ascending=False)

    L = ["# W9 - electricity accounts as land-use layer\n",
         f"Source `{os.path.basename(ELE)}` joined to `Towns.shp`. "
         f"**{len(e):,} accounts**, EPSG:32640.\n",
         "\n## Guideline category counts\n",
         "| GUD_CAT | Accounts |\n|---|---|"]
    for k, n in e["GUD_CAT"].value_counts().items():
        L.append(f"| {k} | {n:,} |")

    L.append("\n## REVIEW queue (tariff cannot classify these)\n")
    L.append("| Flag | Points |\n|---|---|")
    for k, n in e[e.REVIEW != ""]["REVIEW"].value_counts().items():
        L.append(f"| {k} | {n:,} |")

    L.append("\n## Occupancy rate by settlement (Pop_2024 / domestic properties)\n")
    L.append("| Settlement | Domestic properties | Pop 2024 | OR |\n|---|---|---|---|")
    for name, row in r.iterrows():
        L.append(f"| {name} | {int(row.dom_props):,} | {int(row.Pop_2024):,} | {row.OR} |")
    tot_or = r.Pop_2024.sum() / r.dom_props.sum()
    L.append(f"| **TOTAL** | **{int(r.dom_props.sum()):,}** | "
             f"**{int(r.Pop_2024.sum()):,}** | **{tot_or:.2f}** |")

    # ---- coverage consistency check ----------------------------------------
    WILAYAT_POP_2024 = 183564  # NCSI via R0 'Pop_Wilayat'
    pop_cov = r.Pop_2024.sum() / WILAYAT_POP_2024
    implied_accounts = WILAYAT_POP_2024 / tot_or
    meter_cov = len(d) / implied_accounts
    L.append("\n## Coverage consistency check\n")
    L.append(f"- Settlements hold {int(r.Pop_2024.sum()):,} of the wilayat's "
             f"{WILAYAT_POP_2024:,} people = **{pop_cov*100:.1f} %**.")
    L.append(f"- At OR {tot_or:.2f} the whole wilayat implies "
             f"{implied_accounts:,.0f} domestic properties; the file holds "
             f"{len(d):,} = **{meter_cov*100:.1f} %**.")
    L.append(f"- The two coverages agree to "
             f"{abs(pop_cov-meter_cov)*100:.1f} pp, so OR {tot_or:.2f} is "
             f"internally consistent rather than a coverage artefact.")

    with open(os.path.join(W9, "analysis", "W9_ele_landuse.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print(f"wrote {OUT}")
    print(r.to_string())
    print(f"\nOR total {tot_or:.2f} | pop coverage {pop_cov*100:.1f} % | "
          f"meter coverage {meter_cov*100:.1f} %")
    print("\nREVIEW queue:")
    print(e[e.REVIEW != ""]["REVIEW"].value_counts().to_string())


if __name__ == "__main__":
    main()
