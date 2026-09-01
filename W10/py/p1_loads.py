# -*- coding: utf-8 -*-
"""W10 Phase 1.3 - saturation sewage load, every plot in the study area.

WHAT THIS IS
    One record per cadastral plot (61,272) plus one per unparceled building (2,799),
    each carrying the saturation average dry-weather flow it discharges to the sewer.
    The pipe-sizing solver accumulates Q_AVG_M3D down the tree and applies the peaking
    factor to the ACCUMULATED flow - never to a single plot.

THE BASIS IS LOCKED (PROJECT-STATE 2 items 1, 1b, 1c, 1d; 02_DESIGN_CRITERIA 11.1-11.4).
    Tier A ratios set the VOLUME; land use sets the PLACEMENT.
      domestic     = domestic properties x OR x LPCD x return
      non-domestic = +22 % of domestic WATER, returned at 54 %, landed on commercial plots
      governmental = +14 % of domestic WATER, returned at 54 %, landed on government plots
    Table 12 is NOT used and must never be combined with the ratios.
    Agricultural meters are irrigation pumps: they carry no sewage load, and an
    agricultural plot with no household meter carries no dwelling.

WHY NOT W8/py/sewnet/stages/loads.py
    That stage predates the 2026-08-30 lock. It multiplies every counted property by the
    single blended figure WWG_LCD = 171.3 l/c/d, which is the AREA AVERAGE - domestic plus
    the smeared non-domestic and governmental uplift. Under the locked basis a residential
    plot runs at 164 x 0.85 = 139.4 l/c/d and the uplift is concentrated on the plots that
    actually generate it. It also carries OCCUPANCY = 5.0 (superseded by 5.32) and falls
    back to 1.0 property on a plot with no meter. The chamber-assignment and accumulation
    halves of that class generalise fine and are reused unchanged by the solver; only the
    per-plot allocation is rebuilt here.

OUTPUTS
    W10/shp/W10_plot_loads.shp   one record per plot + per unparceled building
    W10/run/W10_load_summary.csv totals by class and category + the 49,700 reconciliation
    W10/run/W10_load_checks.csv  the five checks, machine readable

RE-RUN
    python W10/py/p1_loads.py
    Everything the GIS expert's clean land-use file will change is a named constant or a
    named crosswalk below. Nothing is hard-coded downstream.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as CFG  # noqa: E402


# ===========================================================================
#  1. CONSTANTS - every one of them with the page it came from
# ===========================================================================
@dataclass(frozen=True)
class LoadBasis:
    """Design values. G1-p## = PAM-GUD-201; 02 = _BRAIN/02_DESIGN_CRITERIA.md."""

    # ---- volume chain (Tier A ratios; 02 11.1 LOAD BASIS LOCKED 2026-08-30)
    OR: float = 5.32          # people per domestic property, DERIVED  02 11.1, G1-p58
    LPCD_WATER: float = 164.0  # l/c/d domestic water, Adh Dhahirah   G1-p59-60 Tab 11
    RET_DOM: float = 0.85     # domestic + tanker return rate          G1-p70-71 Tab 19
    RET_NONDOM: float = 0.54  # non-domestic + governmental return     G1-p70-71 Tab 19
    RATIO_ND: float = 0.22    # "Distributed Non-Domestic Ratio"       G1-p60 Tab 11
    RATIO_GOV: float = 0.14   # "Distributed Governmental Ratio"       G1-p60 Tab 11

    # ---- placement (measured on this dataset; see docs/LOAD_ALLOCATION.md 4)
    DOM_PER_PLOT: float = 1.456   # domestic properties per matched plot   02 11.1
    ND_PER_PLOT: float = 4.434    # non-domestic premises per commercial plot, W10-measured
    GOV_PER_PLOT: float = 1.530   # government premises per government plot, W10-measured
    UNPARCELED_DWELLINGS: float = 1.0   # one building = one dwelling  [ASSUMPTION]

    # ---- what counts as a premises at all
    MIN_PREMISES_AREA_M2: float = 100.0  # [ASSUMPTION, evidence in docs 5.3]

    # ---- carried for the solver, not applied here
    INFILT_L_D_KM: float = 720.0   # new networks, a PIPE load          G1-p72-73
    PF_HOLD_PROPERTIES: int = 100  # Merrimack is mandatory above this  G1-p71
    STP_MARGIN: float = 0.10       # +10 % on a NEW STP                 G1-p73

    @property
    def WWG_DOM_LCD(self) -> float:
        """Residential-only wastewater rate: 164 x 0.85 = 139.4 l/c/d."""
        return self.LPCD_WATER * self.RET_DOM

    @property
    def WWG_AREA_AVG_LCD(self) -> float:
        """Area average incl. the concentrated uplift = 171.3 l/c/d (cross-check only)."""
        return self.LPCD_WATER * (self.RET_DOM +
                                  (self.RATIO_ND + self.RATIO_GOV) * self.RET_NONDOM)

    @property
    def ASSUMPTIONS(self) -> Dict[str, Tuple]:
        return {
            "DOM_PER_PLOT": (self.DOM_PER_PLOT,
                             "measured on plots that carry a domestic meter (02 11.1). "
                             "Applied to every residential plot at saturation, built or "
                             "planned. Assumes future plots develop at today's density; "
                             "G1-p59 NOTE warns subdivision usually pushes it UP."),
            "ND_PER_PLOT": (self.ND_PER_PLOT,
                            "measured: mean non-domestic meters on a built plot that has "
                            "one. Affects PLACEMENT only - the non-domestic total is fixed "
                            "by the 22 % ratio and is normalised across these premises."),
            "GOV_PER_PLOT": (self.GOV_PER_PLOT,
                             "measured: mean government meters on a built plot that has "
                             "one. Placement only, as above."),
            "UNPARCELED_DWELLINGS": (self.UNPARCELED_DWELLINGS,
                                     "a building with no parcel is taken as one dwelling. "
                                     "Median footprint 75 m2, so a single household is the "
                                     "likely case, but nothing measures it."),
            "MIN_PREMISES_AREA_M2": (self.MIN_PREMISES_AREA_M2,
                                     "a parcel below this area carrying NO electricity "
                                     "meter is a service parcel (substation, kiosk, tank) "
                                     "and gets no load. Evidence: of 1,562 government-"
                                     "land-use parcels under 100 m2, ZERO carry a "
                                     "government meter and 2 carry any meter; the meter "
                                     "attachment rate runs 1.9 % below 20 m2 and 3.4 % at "
                                     "20-50 m2 against 36.7 % at 200-400 m2. The 100 m2 "
                                     "line itself is a judgement on that breakpoint."),
            "NULL_LANDUSE_IS_RESIDENTIAL": ("39,838 plots",
                                            "65 % of the cadastre has no LANDUSE value. "
                                            "Every one of them that the imagery classifier "
                                            "did not call agricultural is loaded as "
                                            "residential (the W3 A7 convention). This is "
                                            "the single largest placeholder in the run."),
            "CRT_IS_NON_DOMESTIC": ("499 accounts",
                                    "the Cost Reflective Tariff is a consumption threshold, "
                                    "not a land use (02 11.1). Counted as non-domestic "
                                    "premises because it is certainly not a dwelling; a "
                                    "large government building in CRT is misplaced."),
            "INDUSTRIAL_EXCLUDED": ("55 plots, 1 account",
                                    "G1-p59: identified non-domestic projects such as "
                                    "economic zones are NOT covered by the ratios and are "
                                    "determined case by case. No quantities were supplied, "
                                    "so industrial plots carry ZERO here. This is a hole in "
                                    "the total, not a finding that they discharge nothing."),
        }


B = LoadBasis()


# ---- tariff -> guideline category (GUD-201 7.3.1-7.3.4; the W4/W9 crosswalk) ----------
TARIFF_CAT: Dict[str, str] = {
    "Primary Account Tariff": "domestic",
    "Primary Account Tariff (with National Subsidy)": "domestic",
    "Additional Account Tariff": "domestic",     # I-3: a separate dwelling, not a 2nd meter
    "Commercial": "non_domestic",
    "Fisheries": "non_domestic",
    "Tourism": "non_domestic",
    "CRT Seasonal": "non_domestic",              # [ASSUMPTION] CRT cannot be classified
    "CRT Time of Use": "non_domestic",
    "CRT Fixed Rate": "non_domestic",
    "Government": "government",
    "MOD": "government",
    "Agricultural": "agricultural",              # irrigation pump - no sewage (I-4)
    "Industrial": "industrial",                  # outside the ratios (G1-p59)
}

# ---- MoH LANDUSE (Arabic, stored as latin-1 mojibake in the DBF) ---------------------
LU_RES = {"سكني"}
LU_MIX = {"سكني/تجاري", "سكنى/زراعى"}      # residential AND commercial on one parcel
LU_COM = {"تجاري", "مسجد"}                  # commercial, mosque
LU_GOV = {"حكومي"}
LU_IND = {"صناعي"}
LU_AGR = {"زراعى"}
LU_NAME = {"سكني": "res", "سكني/تجاري": "res+com", "سكنى/زراعى": "res+agri",
           "تجاري": "com", "مسجد": "mosque", "حكومي": "gov", "صناعي": "ind",
           "زراعى": "agri"}


# ---- why a record ends with no load. Short codes: the DBF stores one per record --------
ZERO_WHY_LEGEND = {
    "INDUSTRIAL": "industrial - outside the ratios (G1-p59), quantities not supplied",
    "AGRI_NO_HSE": "agricultural plot, no household meter (I-5)",
    "SERVICE_PCL": "parcel under MIN_PREMISES_AREA_M2 carrying no meter - service parcel",
    "NO_LOAD_LU": "no meter and no residential land use",
}


def demojibake(s):
    """MoH_Plots stores Arabic land use as utf-8 bytes read back as latin-1."""
    try:
        return s.encode("latin-1").decode("utf-8") if isinstance(s, str) else s
    except Exception:
        return s


# ===========================================================================
#  2. INPUTS
# ===========================================================================
def read_inputs():
    plots = gpd.read_file(CFG.PLOTS_CLASS, encoding="utf-8")
    plots = plots[plots.geometry.notna()].copy()
    plots["LU"] = plots["LANDUSE"].map(demojibake)

    acc = gpd.read_file(CFG.ACCOUNTS, encoding="utf-8")
    acc = acc[acc.geometry.notna()].copy()
    acc["GUD_CAT"] = acc["TARIFF"].map(TARIFF_CAT).fillna("unmapped")

    unp = gpd.read_file(CFG.UNPARCELED)
    unp = unp[unp.geometry.notna()].copy()

    bnd = gpd.read_file(CFG.BOUNDARY).to_crs(plots.crs)
    poly = bnd.union_all() if hasattr(bnd, "union_all") else bnd.unary_union
    return plots, acc, unp, poly


def accounts_per_plot(acc: gpd.GeoDataFrame) -> pd.DataFrame:
    """Counted premises per plot, split by guideline category.

    Agricultural meters are dropped outright (I-4/I-5): the pump discharges nothing, and
    a plot whose ONLY meter is agricultural therefore ends with no dwelling.
    """
    a = acc.dropna(subset=["PLOT_ID"]).copy()
    a["PLOT_ID"] = a["PLOT_ID"].astype("int64")
    g = a.groupby(["PLOT_ID", "GUD_CAT"]).size().unstack(fill_value=0)
    for c in ("domestic", "non_domestic", "government", "agricultural", "industrial",
              "unmapped"):
        if c not in g.columns:
            g[c] = 0
    return pd.DataFrame({
        "C_DOM": g["domestic"],
        "C_ND": g["non_domestic"],
        "C_GOV": g["government"],
        "C_AGRI": g["agricultural"],
        "C_IND": g["industrial"],
    })


# ===========================================================================
#  3. PREMISES AT SATURATION
# ===========================================================================
def premises(plots: pd.DataFrame, basis: LoadBasis):
    """How many dwellings / commercial premises / government premises each plot holds
    when the study area is fully developed.

    Counted meters where they exist, the measured rate for its category where they do
    not, and the LARGER of the two where both apply - 27 % of the accounts fall outside
    every plot polygon, so a counted zero is at least as often a cadastre gap as an
    empty plot.
    """
    lu = plots["LU"]
    cls = plots["CLASS"]
    area = plots["AREA_M2"].fillna(0.0).values

    counted = (plots[["C_DOM", "C_ND", "C_GOV"]].fillna(0.0).values.sum(axis=1) > 0)
    too_small = (area < basis.MIN_PREMISES_AREA_M2) & (~counted)   # service parcels

    developable = cls.isin(("B", "P")).values & (~too_small)
    industrial = lu.isin(LU_IND).values

    res_elig = developable & (lu.isna() | lu.isin(LU_RES | LU_MIX)).values
    com_elig = developable & lu.isin(LU_COM | LU_MIX).values
    gov_elig = developable & lu.isin(LU_GOV).values

    n_dom = np.maximum(plots["C_DOM"].fillna(0).values,
                       np.where(res_elig, basis.DOM_PER_PLOT, 0.0))
    n_nd = np.maximum(plots["C_ND"].fillna(0).values,
                      np.where(com_elig, basis.ND_PER_PLOT, 0.0))
    n_gov = np.maximum(plots["C_GOV"].fillna(0).values,
                       np.where(gov_elig, basis.GOV_PER_PLOT, 0.0))

    # G1-p59: identified non-domestic projects are outside the ratios entirely
    n_dom = np.where(industrial, 0.0, n_dom)
    n_nd = np.where(industrial, 0.0, n_nd)
    n_gov = np.where(industrial, 0.0, n_gov)

    basis_tag = np.where(counted & (res_elig | com_elig | gov_elig), "counted+rate",
                         np.where(counted, "counted",
                                  np.where(res_elig | com_elig | gov_elig, "rate", "none")))

    why = np.full(len(plots), "", dtype=object)
    zero = (n_dom + n_nd + n_gov) <= 0
    # short codes keep the DBF small; the legend is ZERO_WHY_LEGEND below and docs 9
    why[zero & industrial] = "INDUSTRIAL"
    why[zero & (cls == "A").values & ~industrial] = "AGRI_NO_HSE"
    why[zero & too_small & ~industrial & (cls != "A").values] = "SERVICE_PCL"
    why[zero & (why == "")] = "NO_LOAD_LU"
    return n_dom, n_nd, n_gov, basis_tag, why, too_small, industrial


# ===========================================================================
#  4. VOLUME AND PLACEMENT
# ===========================================================================
def allocate(n_dom, n_nd, n_gov, basis: LoadBasis):
    """Tier A ratios set the volume; the premises counts place it.

    Q_dom     = properties x OR x 164 x 0.85              (per plot, direct)
    Q_nd_tot  = POP x 164 x 0.22 x 0.54                   (project total, then shared)
    Q_gov_tot = POP x 164 x 0.14 x 0.54                   (project total, then shared)

    The shares are normalised, so the total is preserved exactly whatever the premises
    rates are - which is why ND_PER_PLOT and GOV_PER_PLOT move flow between branches but
    never change the project figure.
    """
    pop = n_dom * basis.OR
    POP = pop.sum()

    q_dom = pop * basis.WWG_DOM_LCD / 1000.0
    q_nd_tot = POP * basis.LPCD_WATER * basis.RATIO_ND * basis.RET_NONDOM / 1000.0
    q_gov_tot = POP * basis.LPCD_WATER * basis.RATIO_GOV * basis.RET_NONDOM / 1000.0

    q_nd = q_nd_tot * n_nd / n_nd.sum() if n_nd.sum() > 0 else n_nd * 0.0
    q_gov = q_gov_tot * n_gov / n_gov.sum() if n_gov.sum() > 0 else n_gov * 0.0
    return pop, q_dom, q_nd, q_gov


# ===========================================================================
#  5. BUILD THE LAYER
# ===========================================================================
def build(basis: LoadBasis = B):
    plots, acc, unp, poly = read_inputs()
    n_acc = len(acc)
    per_plot = accounts_per_plot(acc)

    p = plots.set_index("OBJECTID").join(per_plot).reset_index()
    for c in ("C_DOM", "C_ND", "C_GOV", "C_AGRI", "C_IND"):
        p[c] = p[c].fillna(0.0)

    n_dom, n_nd, n_gov, basis_tag, why, too_small, industrial = premises(p, basis)

    # unparceled buildings: real dwellings the cadastre never drew
    u = unp.copy()
    u_dom = np.full(len(u), basis.UNPARCELED_DWELLINGS)

    all_dom = np.concatenate([n_dom, u_dom])
    all_nd = np.concatenate([n_nd, np.zeros(len(u))])
    all_gov = np.concatenate([n_gov, np.zeros(len(u))])
    pop, q_dom, q_nd, q_gov = allocate(all_dom, all_nd, all_gov, basis)

    lu_name = p["LU"].map(LU_NAME).fillna("unknown")
    out = pd.DataFrame({
        "PLOT_ID": np.concatenate([p["OBJECTID"].values, -(np.arange(len(u)) + 1)]),
        "SRC": ["plot"] * len(p) + ["unparceled"] * len(u),
        "CLASS": np.concatenate([p["CLASS"].values, np.full(len(u), "U")]),
        "LU": np.concatenate([lu_name.values, np.full(len(u), "building")]),
        "N_DOM": all_dom, "N_ND": all_nd, "N_GOV": all_gov,
        "POP": pop,
        "Q_DOM_M3D": q_dom, "Q_ND_M3D": q_nd, "Q_GOV_M3D": q_gov,
        "AREA_M2": np.concatenate([p["AREA_M2"].fillna(0).values,
                                   u["AREA_M2"].fillna(0).values]),
        "BASIS": np.concatenate([basis_tag, np.full(len(u), "rate")]),
        "ZERO_WHY": np.concatenate([why, np.full(len(u), "", dtype=object)]),
    })
    out["N_PROP"] = out.N_DOM + out.N_ND + out.N_GOV
    out["Q_AVG_M3D"] = out.Q_DOM_M3D + out.Q_ND_M3D + out.Q_GOV_M3D
    out["Q_AVG_LS"] = out.Q_AVG_M3D * 1000.0 / 86400.0
    out["Q_L_M2D"] = np.where(out.AREA_M2 > 0, out.Q_AVG_M3D * 1000.0 / out.AREA_M2, 0.0)

    cat = np.full(len(out), "none", dtype=object)
    cat[out.N_GOV.values > 0] = "government"
    cat[out.N_ND.values > 0] = "commercial"
    cat[(out.N_ND.values > 0) & (out.N_GOV.values > 0)] = "com+gov"
    cat[out.N_DOM.values > 0] = "domestic"
    cat[(out.N_DOM.values > 0) & ((out.N_ND.values > 0) | (out.N_GOV.values > 0))] = "mixed"
    agri = np.concatenate([((p["C_AGRI"].values > 0) | (p["CLASS"].values == "A")),
                           np.zeros(len(u), bool)])
    cat[agri & (out.Q_AVG_M3D.values <= 0)] = "agricultural"
    cat[np.concatenate([industrial, np.zeros(len(u), bool)])] = "industrial"
    out["CAT"] = cat

    # sanity band on load per unit parcel area
    # order matters: the flow-relevant flag must survive, so it is written last
    sanity = np.full(len(out), "", dtype=object)
    loaded = out.Q_AVG_M3D.values > 0
    sanity[loaded & (out.AREA_M2.values < basis.MIN_PREMISES_AREA_M2) &
           (out.SRC.values == "plot")] = "micro_parcel"
    sanity[loaded & (out.Q_L_M2D.values < 0.05)] = "low_mega_parcel"
    sanity[loaded & (out.Q_L_M2D.values > 25.0)] = "high"
    sanity[loaded & (out.Q_L_M2D.values > 100.0)] = "very_high"
    out["SANITY"] = sanity

    geom = pd.concat([p.geometry, u.geometry], ignore_index=True)
    g = gpd.GeoDataFrame(out, geometry=geom.values, crs=plots.crs)
    g["IN_BND"] = g.geometry.representative_point().within(poly).astype(int)
    return g, n_acc, per_plot


# ===========================================================================
#  6. SUMMARY, CHECKS AND RECONCILIATION
# ===========================================================================
# W2 screening chain, PROJECT-STATE 5 - the figure this run has to be reconciled against
W2 = dict(qadf=49714.8, pop=279756, res_plots=46626, plots=53503, sewer_km=2496.91,
          OR=6.0, props_per_plot=1.0)
# NCSI / R0 projections inside the 25 settlement polygons (W3/analysis/A1_zone_capacity)
R0 = dict(pop2024=116456, pop2055=237885, pop2100=691264, ceiling_OR6=269796,
          wilayat_pop2024=183564)


def summarise(g: gpd.GeoDataFrame, basis: LoadBasis, n_acc: int):
    d = g[g.IN_BND == 1]
    rows = []
    for cls, s in d.groupby("CLASS"):
        rows.append(dict(group="class", key=cls, records=len(s),
                         n_dom=s.N_DOM.sum(), n_nd=s.N_ND.sum(), n_gov=s.N_GOV.sum(),
                         pop=s.POP.sum(), q_m3d=s.Q_AVG_M3D.sum(),
                         q_ls=s.Q_AVG_LS.sum(), zero_load=int((s.Q_AVG_M3D <= 0).sum())))
    for cat, s in d.groupby("CAT"):
        rows.append(dict(group="category", key=cat, records=len(s),
                         n_dom=s.N_DOM.sum(), n_nd=s.N_ND.sum(), n_gov=s.N_GOV.sum(),
                         pop=s.POP.sum(), q_m3d=s.Q_AVG_M3D.sum(),
                         q_ls=s.Q_AVG_LS.sum(), zero_load=int((s.Q_AVG_M3D <= 0).sum())))
    for nm, col in (("domestic", "Q_DOM_M3D"), ("non_domestic", "Q_ND_M3D"),
                    ("governmental", "Q_GOV_M3D")):
        rows.append(dict(group="flow_stream", key=nm, records="",
                         n_dom="", n_nd="", n_gov="", pop="",
                         q_m3d=d[col].sum(), q_ls=d[col].sum() * 1000 / 86400,
                         zero_load=""))
    rows.append(dict(group="total", key="study area", records=len(d),
                     n_dom=d.N_DOM.sum(), n_nd=d.N_ND.sum(), n_gov=d.N_GOV.sum(),
                     pop=d.POP.sum(), q_m3d=d.Q_AVG_M3D.sum(), q_ls=d.Q_AVG_LS.sum(),
                     zero_load=int((d.Q_AVG_M3D <= 0).sum())))

    Q = d.Q_AVG_M3D.sum()
    POP = d.POP.sum()
    recon = [
        ("W10 saturation Qadf, plots only (no infiltration)", round(Q, 1), "m3/d"),
        ("W10 saturation population", round(POP), "people"),
        ("W10 domestic properties", round(d.N_DOM.sum()), "properties"),
        ("W10 implied area-average rate", round(Q * 1000 / POP, 2), "l/c/d"),
        ("W2 screening Qadf carried since W2 (incl. infiltration)", W2["qadf"], "m3/d"),
        ("W2 infiltration inside that figure (720 L/d/km x 2,497 km)",
         round(basis.INFILT_L_D_KM * W2["sewer_km"] / 1000.0, 1), "m3/d"),
        ("W2 plot load only", round(W2["qadf"] - basis.INFILT_L_D_KM * W2["sewer_km"] / 1000.0, 1),
         "m3/d"),
        ("W2 population", W2["pop"], "people"),
        ("difference W10 - W2, plot load", round(
            Q - (W2["qadf"] - basis.INFILT_L_D_KM * W2["sewer_km"] / 1000.0), 1), "m3/d"),
        ("ratio W10 / W2 plot load", round(
            Q / (W2["qadf"] - basis.INFILT_L_D_KM * W2["sewer_km"] / 1000.0), 3), "-"),
        # ---- where the difference comes from: it is ALL population
        ("W2 people per residential plot (1.0 property x OR 6.0)",
         W2["props_per_plot"] * W2["OR"], "people/plot"),
        ("W10 people per residential plot (1.456 properties x OR 5.32)",
         round(basis.DOM_PER_PLOT * basis.OR, 3), "people/plot"),
        ("factor A - property and occupancy basis",
         round(basis.DOM_PER_PLOT * basis.OR / (W2["props_per_plot"] * W2["OR"]), 3), "x"),
        ("W2 residential plots", W2["res_plots"], "plots"),
        ("W10 plots carrying dwellings", int(((d.SRC == "plot") & (d.N_DOM > 0)).sum()),
         "plots"),
        ("factor B - wider plot base (whole cadastre inside the boundary, not 36 zones)",
         round(POP / (basis.DOM_PER_PLOT * basis.OR) / W2["res_plots"], 3), "x"),
        ("factor A x factor B (should equal the population ratio)",
         round(basis.DOM_PER_PLOT * basis.OR / (W2["props_per_plot"] * W2["OR"]) *
               POP / (basis.DOM_PER_PLOT * basis.OR) / W2["res_plots"], 3), "x"),
        ("population ratio W10 / W2", round(POP / W2["pop"], 3), "x"),
        ("R0/NCSI population 2024, 25 settlements", R0["pop2024"], "people"),
        ("R0/NCSI population 2055, 25 settlements", R0["pop2055"], "people"),
        ("R0/NCSI population 2100, 25 settlements", R0["pop2100"], "people"),
        ("W3 A1 land ceiling at OR 6.0 x 1 property/plot", R0["ceiling_OR6"], "people"),
        ("W10 saturation pop / R0 2055", round(POP / R0["pop2055"], 3), "-"),
        ("W10 saturation pop / R0 2100", round(POP / R0["pop2100"], 3), "-"),
        ("electricity accounts read", n_acc, "accounts"),
    ]
    return pd.DataFrame(rows), pd.DataFrame(recon, columns=["item", "value", "unit"])


def checks(g: gpd.GeoDataFrame, basis: LoadBasis):
    d = g[g.IN_BND == 1]
    loaded = d[d.Q_AVG_M3D > 0]
    zero = d[d.Q_AVG_M3D <= 0]
    Q = d.Q_AVG_M3D.sum()
    rows = [
        ("properties", "total premises at saturation", round(d.N_PROP.sum())),
        ("properties", "domestic properties (dwellings)", round(d.N_DOM.sum())),
        ("properties", "non-domestic premises", round(d.N_ND.sum())),
        ("properties", "government premises", round(d.N_GOV.sum())),
        ("population", f"at OR {basis.OR}", round(d.POP.sum())),
        ("population", "vs R0/NCSI 2055 (settlements)", round(d.POP.sum() / R0["pop2055"], 2)),
        ("population", "vs R0/NCSI 2100 (settlements)", round(d.POP.sum() / R0["pop2100"], 2)),
        ("zero load", "records with zero load", len(zero)),
    ]
    for cls, s in zero.groupby("CLASS"):
        rows.append(("zero load", f"class {cls}", len(s)))
    for w, s in zero.groupby("ZERO_WHY"):
        rows.append(("zero load reason", f"{w} = {ZERO_WHY_LEGEND.get(w, w)}", len(s)))
    rows += [
        ("sanity", "loaded records", len(loaded)),
        ("sanity", "load > 25 L/m2/d (high)", int((loaded.Q_L_M2D > 25).sum())),
        ("sanity", "load > 100 L/m2/d (very high)", int((loaded.Q_L_M2D > 100).sum())),
        ("sanity", "load < 0.05 L/m2/d (mega parcel)", int((loaded.Q_L_M2D < 0.05).sum())),
        ("sanity", "micro parcels (<100 m2) still loaded", int(
            ((loaded.AREA_M2 < basis.MIN_PREMISES_AREA_M2) & (loaded.SRC == "plot")).sum())),
        ("sanity", "median L/m2/d", round(float(loaded.Q_L_M2D.median()), 2)),
        ("sanity", "95th percentile L/m2/d", round(float(loaded.Q_L_M2D.quantile(0.95)), 2)),
        ("sanity", "share of flow on records flagged high/very_high %", round(
            100 * loaded.loc[loaded.Q_L_M2D > 25, "Q_AVG_M3D"].sum() / Q, 2)),
        ("share of flow", "domestic %", round(100 * d.Q_DOM_M3D.sum() / Q, 2)),
        ("share of flow", "non-domestic %", round(100 * d.Q_ND_M3D.sum() / Q, 2)),
        ("share of flow", "governmental %", round(100 * d.Q_GOV_M3D.sum() / Q, 2)),
        ("outside boundary", "records dropped from totals", int((g.IN_BND == 0).sum())),
    ]
    return pd.DataFrame(rows, columns=["check", "item", "value"])


def sensitivity(basis: LoadBasis = B):
    """What the two levers that actually move the total are worth."""
    from dataclasses import replace
    out = []
    for name, bb in (("design basis (DOM_PER_PLOT 1.456, OR 5.32)", basis),
                     ("built-plot rate 1.413", replace(basis, DOM_PER_PLOT=1.413)),
                     ("one dwelling per plot (W8 fallback)", replace(basis, DOM_PER_PLOT=1.0)),
                     ("OR 5.00 (superseded placeholder)", replace(basis, OR=5.0)),
                     ("OR 6.00 (W1-W3 basis)", replace(basis, OR=6.0)),
                     ("no micro-parcel filter", replace(basis, MIN_PREMISES_AREA_M2=0.0))):
        g, _, _ = build(bb)
        d = g[g.IN_BND == 1]
        out.append(dict(variant=name, dom_props=round(d.N_DOM.sum()),
                        pop=round(d.POP.sum()), qadf_m3d=round(d.Q_AVG_M3D.sum(), 1),
                        vs_49700_pct=round(100 * d.Q_AVG_M3D.sum() / W2["qadf"] - 100, 1)))
    return pd.DataFrame(out)


# ===========================================================================
def main():
    os.makedirs(CFG.OUT_SHP, exist_ok=True)
    os.makedirs(CFG.OUT_RUN, exist_ok=True)
    os.makedirs(CFG.OUT_DOCS, exist_ok=True)

    g, n_acc, _ = build(B)
    shp = os.path.join(CFG.OUT_SHP, "W10_plot_loads.shp")
    cols = ["PLOT_ID", "SRC", "CLASS", "LU", "CAT", "N_DOM", "N_ND", "N_GOV", "N_PROP",
            "POP", "Q_DOM_M3D", "Q_ND_M3D", "Q_GOV_M3D", "Q_AVG_M3D", "Q_AVG_LS",
            "AREA_M2", "Q_L_M2D", "BASIS", "SANITY", "ZERO_WHY", "IN_BND", "geometry"]
    g[cols].to_file(shp, encoding="utf-8")
    print(f"wrote {shp}  ({len(g):,} records)")

    summ, recon = summarise(g, B, n_acc)
    chk = checks(g, B)
    sens = sensitivity(B)

    csv = os.path.join(CFG.OUT_RUN, "W10_load_summary.csv")
    with open(csv, "w", encoding="utf-8", newline="") as f:
        f.write("# W10 Phase 1.3 - saturation load summary\n")
        f.write("# basis: Tier A ratios set the volume, land use sets the placement "
                "(PROJECT-STATE 2.1b, locked 2026-08-30)\n")
        f.write(f"# OR {B.OR} | LPCD {B.LPCD_WATER} | return dom {B.RET_DOM} / nondom "
                f"{B.RET_NONDOM} | ND {B.RATIO_ND:.0%} | GOV {B.RATIO_GOV:.0%}\n")
        f.write("\n## TOTALS BY CLASS AND CATEGORY\n")
        summ.to_csv(f, index=False)
        f.write("\n## RECONCILIATION AGAINST THE 49,700 m3/d CARRIED SINCE W2\n")
        recon.to_csv(f, index=False)
        f.write("\n## CHECKS\n")
        chk.to_csv(f, index=False)
        f.write("\n## SENSITIVITY - the levers that move the total\n")
        sens.to_csv(f, index=False)
    print(f"wrote {csv}")

    chk.to_csv(os.path.join(CFG.OUT_RUN, "W10_load_checks.csv"), index=False)

    d = g[g.IN_BND == 1]
    print("\n" + "=" * 72)
    print(f"  saturation Qadf (plots only)  {d.Q_AVG_M3D.sum():,.0f} m3/d "
          f"= {d.Q_AVG_LS.sum():,.0f} L/s")
    print(f"  domestic properties           {d.N_DOM.sum():,.0f}")
    print(f"  population at OR {B.OR}          {d.POP.sum():,.0f}")
    print(f"  shares  dom {100*d.Q_DOM_M3D.sum()/d.Q_AVG_M3D.sum():.1f} %  "
          f"nd {100*d.Q_ND_M3D.sum()/d.Q_AVG_M3D.sum():.1f} %  "
          f"gov {100*d.Q_GOV_M3D.sum()/d.Q_AVG_M3D.sum():.1f} %")
    print(f"  vs the 49,700 m3/d carried since W2: "
          f"{d.Q_AVG_M3D.sum()/W2['qadf']:.2f} x")
    print("=" * 72)
    print(sens.to_string(index=False))
    print()
    print(chk.to_string(index=False))


if __name__ == "__main__":
    main()
