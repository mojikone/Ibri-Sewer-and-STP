"""
A7 — corrected load allocation.

W2 applied the Adh Dhahirah non-domestic (+22%) and governmental (+14%) ratios
as a flat per-capita uplift on every zone. PAM-GUD-201 Table 11 calls these the
"Distributed" ratios -- the governorate's actual 2021-23 volumes divided by its
population, i.e. a top-down aggregate, not a demand every person carries. §7.3.2
and §7.3.3 (G1-p60-61) say that where land-use allocation exists the non-domestic
and governmental demand SHALL come from Table 12 instead.

Table 12 needs floor areas, pupils, beds and employees, which we do not have
(data request A7 item 3). Until they arrive, this script keeps the ratio-derived
TOTAL but stops spreading it per capita: the non-domestic + governmental volume
is placed on the non-residential plots in proportion to their area.

Total project flow is unchanged. What changes is where it lands -- which is what
sizes the branches. Run against the W2 zones so the shift is quantified.

Outputs W3/analysis/A7_load_alloc.csv and prints the summary.
"""
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP")
REPO = ROOT / "Hydraulic/Claude"
ZONES = REPO / "W2/shp/zones.shp"
PLOTS = REPO / "W3/shp/MoH_Plots_class_v4.shp"
W2FLOWS = REPO / "W2/report/zone_flows.csv"
OUT = REPO / "W3/analysis/A7_load_alloc.csv"

LPCD = 164.0                      # G1-p60 Tab 11, Adh Dhahirah
ND_RATIO, GOV_RATIO = 0.22, 0.14  # G1-p60 "Distributed" ratios -- FALLBACK ONLY
RET_DOM, RET_ND = 0.85, 0.54      # G1-p71 Tab 19
INFIL_L_D_KM = 720.0              # G1-p72, new networks
PF_CAP = 5.0                      # G1-p72
OR_ASSUMED, PROP_PER_PLOT = 6.0, 1.0   # [GAP-5], unchanged from W2 so the
                                       # comparison isolates the allocation

# LANDUSE values in MoH_Plots (Arabic, stored mojibake in the DBF)
RESIDENTIAL = {"سكني", "سكني/تجاري", "سكنى/زراعى"}
NONRES = {"تجاري", "حكومي", "مسجد", "صناعي"}
AGRI = {"زراعى"}


def fix(s):
    """Repair the latin-1/utf-8 mojibake in the LANDUSE field."""
    try:
        return s.encode("latin-1").decode("utf-8") if isinstance(s, str) else s
    except Exception:
        return s


def peaking(qadf_m3d: float) -> float:
    """Peltier PfWW = 1.5 + 1/sqrt(Qm), Qm in l/s, capped at 5.0 (G1-p72)."""
    qm = qadf_m3d / 86.4
    return min(1.5 + 1 / math.sqrt(qm), PF_CAP) if qm > 0 else PF_CAP


def main():
    z = gpd.read_file(ZONES)
    p = gpd.read_file(PLOTS)
    zid = "zone" if "zone" in z.columns else z.columns[0]

    p["LU"] = p["LANDUSE"].map(fix)
    # A plot with no land-use attribute (52% of area) is treated as residential
    # if the imagery classifier called it built or planned, and dropped if it
    # reads as agriculture. Tagged assumption -- closes with A7 item 4.
    p["kind"] = "other"
    p.loc[p.LU.isin(RESIDENTIAL), "kind"] = "res"
    p.loc[p.LU.isin(NONRES), "kind"] = "nonres"
    p.loc[p.LU.isin(AGRI) | (p.CLASS == "A"), "kind"] = "agri"
    p.loc[p.LU.isna() & (p.CLASS != "A"), "kind"] = "res"

    pts = p.copy()
    pts["geometry"] = p.geometry.representative_point()
    j = gpd.sjoin(pts, z[[zid, "geometry"]].to_crs(p.crs), how="inner",
                  predicate="within")
    print(f"plots assigned to a W2 zone: {len(j)} of {len(p)}")

    g = j.groupby([zid, "kind"]).agg(n=("kind", "size"),
                                     area=("AREA_M2", "sum")).unstack(fill_value=0)
    res_n = g[("n", "res")]
    nonres_area = g[("area", "nonres")]

    df = pd.DataFrame({"zone": res_n.index, "res_plots": res_n.values,
                       "nonres_area_m2": nonres_area.values})
    df["pop"] = (df.res_plots * PROP_PER_PLOT * OR_ASSUMED).round().astype(int)
    df["q_dom_m3d"] = df["pop"] * LPCD / 1000.0

    # one project-wide non-domestic + governmental volume, then split by area
    ndg_total = df["q_dom_m3d"].sum() * (ND_RATIO + GOV_RATIO)
    share = df["nonres_area_m2"] / df["nonres_area_m2"].sum()
    df["q_ndg_m3d"] = ndg_total * share

    # sewer length per zone, reused from W2 so infiltration is like-for-like
    w2 = pd.read_csv(W2FLOWS).rename(columns={"Qadf_m3d": "W2_Qadf",
                                              "sewer_km": "sewer_km"})
    df = df.merge(w2[["zone", "sewer_km", "W2_Qadf", "pop"]]
                  .rename(columns={"pop": "W2_pop"}), on="zone", how="left")
    df["infil_m3d"] = INFIL_L_D_KM * df.sewer_km.fillna(0) / 1000.0

    df["Qadf_m3d"] = (df.q_dom_m3d * RET_DOM + df.q_ndg_m3d * RET_ND
                      + df.infil_m3d)
    df["PF"] = df.Qadf_m3d.map(peaking)
    df["Qpeak_m3d"] = df.Qadf_m3d * df.PF

    # W2 basis for the same zones: uplift applied per capita
    df["Qadf_W2method"] = (df.q_dom_m3d * RET_DOM
                           + df.q_dom_m3d * (ND_RATIO + GOV_RATIO) * RET_ND
                           + df.infil_m3d)
    df["delta_pct"] = ((df.Qadf_m3d / df.Qadf_W2method - 1) * 100).round(1)

    cols = ["zone", "res_plots", "pop", "nonres_area_m2", "q_dom_m3d",
            "q_ndg_m3d", "infil_m3d", "Qadf_m3d", "PF", "Qpeak_m3d",
            "Qadf_W2method", "delta_pct"]
    df = df[cols].round(1).sort_values("Qadf_m3d", ascending=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    tot_new, tot_old = df.Qadf_m3d.sum(), df.Qadf_W2method.sum()
    print(f"\nproject Qadf: corrected {tot_new:,.0f} m3/d vs per-capita method "
          f"{tot_old:,.0f} m3/d  ({(tot_new/tot_old-1)*100:+.1f}% overall)")
    print(f"zone-level shift: {df.delta_pct.min():+.1f}% to "
          f"{df.delta_pct.max():+.1f}%  |  zones down {int((df.delta_pct<0).sum())}, "
          f"up {int((df.delta_pct>0).sum())}")
    print(f"\ntop and bottom movers:\n"
          f"{pd.concat([df.head(6), df.tail(6)])[['zone','pop','nonres_area_m2','Qadf_m3d','Qadf_W2method','delta_pct']].to_string(index=False)}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
