"""T04 chapters 1 and 2: the data, and from the meter to the use of every plot.

Every number is read at build time from facts_w14 (and, where facts_w14 has no
function for it, from the same W14 layers and client workbook facts_w14 reads).
Guideline values carry their page in PAM-GUD-201 (G201-p##).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report"))   # after T04: its doc.py must not shadow ours
import doc as D
import omml as M
import facts_w14 as F
UP, R = M.up, M.r
IMG = os.path.join(HERE, "img")

from functools import lru_cache

# the tariff crosswalk as W14/py/plots_meters_load.py applies it (GROUP and GUD dictionaries)
TARIFFS = [
    ("Primary Account Tariff", "Domestic", "one property"),
    ("Primary Account Tariff (with National Subsidy)", "Domestic", "one property"),
    ("Additional Account Tariff", "Domestic", "one property, a second dwelling on the plot"),
    ("Commercial", "Non-domestic", "none"),
    ("Fisheries", "Non-domestic", "none"),
    ("Tourism", "Non-domestic", "none"),
    ("Government", "Governmental", "none"),
    ("MOD", "Governmental", "none"),
    ("Agricultural", "Agricultural", "none, and no sewage"),
    ("Industrial", "Special", "none"),
    ("CRT Seasonal", "by the use found (1.2)", "none"),
    ("CRT Time of Use", "by the use found (1.2)", "none"),
    ("CRT Fixed Rate", "by the use found (1.2)", "none"),
]
# the use found for a large-consumer account and the category it takes (GUD_OF_USE in plots_meters_load.py)
CRT_USE = [
    ("Commercial", "Non-domestic", "Bawadi shopping centre, the Al Murtafa souq, the Araqi strip, hypermarkets, banks, fuel"),
    ("Government", "Governmental", "police headquarters, post office, directorates"),
    ("Education", "Governmental", "the university campus, the college, schools"),
    ("Health", "Governmental", "Ibri Hospital, clinics"),
    ("Religious", "Governmental", "mosques"),
    ("Industrial", "Special", "mostly the Tanam estate"),
    ("Agricultural", "Agricultural", "farm pumps at Al Aynayn"),
    ("Telecom/Utility", "Non-domestic", "exchanges, water works, masts"),
    ("Unresolved", "Non-domestic", "no named feature within 80 m"),
]
CAT_KEY = {"Domestic": "domestic", "Non-domestic": "non_domestic", "Governmental": "government",
           "Agricultural": "agricultural", "Special": "special"}
ESTATE_OSM = {"AL TAYYEB": "صناعية الطيب", "TANAM": "صناعية تنعم"}
ESTATE_NAME = {"AL TAYYEB": "Al Tayyeb", "TANAM": "Tanam"}


# --------------------------------------------------------------- the numbers
@lru_cache(None)
def _n():
    """Every figure the two chapters quote, computed once from the live layers."""
    import numpy as np, pandas as pd, geopandas as gpd, openpyxl
    mc, ps, cs = F.meter_counts(), F.plot_summary(), F.crt_summary()
    m, p = F.meters(), F.plots()
    c = F.crt(); c = c[c.tariff != "Industrial"]
    t = mc["tariff"]
    n = dict(mc=mc, ps=ps, cs=cs)

    # meters: tariff side and large-consumer side of each category
    tar_cat = {}
    for name, cat, _ in TARIFFS:
        if cat in CAT_KEY:
            tar_cat[CAT_KEY[cat]] = tar_cat.get(CAT_KEY[cat], 0) + t.get(name, 0)
    crt_cat = {}
    for use, cat, _ in CRT_USE:
        crt_cat[CAT_KEY[cat]] = crt_cat.get(CAT_KEY[cat], 0) + cs["use"].get(use, 0)
    n["tar_cat"], n["crt_cat"] = tar_cat, crt_cat
    n["dom_parts"] = (t.get("Primary Account Tariff", 0), t.get("Primary Account Tariff (with National Subsidy)", 0),
                      t.get("Additional Account Tariff", 0))
    n["crt_total_tariff"] = t.get("CRT Seasonal", 0) + t.get("CRT Time of Use", 0) + t.get("CRT Fixed Rate", 0)
    n["free_by"] = m[m.PLACE == "free"].GUD.value_counts().to_dict()
    n["snap_nonzero"] = int((m.loc[m.PLACE == "snapped", "SNAP_M"] > 0).sum())

    # large consumers
    inc = c[c.cl >= 0]
    n["crt_in_clusters"], n["crt_clusters"] = len(inc), int(inc.cl.nunique())
    top = inc.cl.value_counts()
    n["crt_top"] = [int(v) for v in top.head(2).values]
    n["crt_conf"] = pd.crosstab(c.USE, c.CONF)
    n["crt_register_rows"] = len(F.crt())

    # estates, army camp and the other footprints
    osm = gpd.read_file(os.path.join(F.SHP, "Identified_projects_OSM.shp")).to_crs(32640)
    osm["ha"] = osm.area / 1e4
    est = {}
    for code, arab in ESTATE_OSM.items():
        s = p[p.ESTATE == code]
        est[code] = dict(ha=float(osm.loc[osm.name == arab, "ha"].sum()), plots=len(s),
                         ind_plots=int((s.Classes == "Industrial").sum()), built=int((s.Buiding_St == "EXisting").sum()),
                         com=int(s.N_COM.sum()), crt=int(s.N_CRT.sum()), spec=int(s.G_SPEC.sum()), dom=int(s.G_DOM.sum()),
                         workers=F.WORKERS[ESTATE_NAME[code]])
    n["est"] = est
    n["army_ha"] = float(osm.loc[osm.kind == "landuse=military", "ha"].sum())
    n["madayn_ha"] = float(osm.loc[osm.name.fillna("").str.contains("Madayn"), "ha"].sum())
    outside = p[(p.G_SPEC > 0) & p.ESTATE.isna()]
    n["spec_outside"] = [(int(i), F.NAME.get(r.SETTLE, r.SETTLE.title()), float(r.W_SPEC)) for i, r in outside.iterrows()]

    # cadastre
    built = p.Buiding_St == "EXisting"
    n["built"], n["empty"] = int(built.sum()), int((~built).sum())
    n["future_metered"] = int(((~built) & (p.N_ACC > 0)).sum())
    n["built_unmetered"] = int((built & (p.N_ACC == 0)).sum())
    n["codes_0_99"] = int(p.Moh_Classi.isin([0, 99]).sum())
    n["res_all"] = int((p.Classes == "Residential").sum())
    n["tourism"] = int((p.Classes == "Tourism").sum())
    n["agree"] = int((built & (p.DERIVED == p.Classes)).sum())
    ct = pd.crosstab(p.loc[built, "Classes"], p.loc[built, "DERIVED"])
    n["ct"] = ct
    n["res_to_farm"] = int(ct.at["Residential", "Agricultural"]) if "Agricultural" in ct.columns else 0
    n["res_to_shop"] = int(ct.at["Residential", "Commercial"]) if "Commercial" in ct.columns else 0
    n["gov_derived"] = int((built & (p.DERIVED == "Government")).sum())

    # settlements and the series
    st = F.settlement_table()
    n["st"] = st
    n["wb_25"] = sum(r["workbook_2024"] for r in st)
    wb = openpyxl.load_workbook(os.path.join(os.path.dirname(F.W14), "_CLIENT", "Ibri Sewer Demand R0 2026 08 03.xlsx"),
                                read_only=True, data_only=True)
    rows = list(wb["Pop_Wilayat"].iter_rows(values_only=True))
    hdr = next(r for r in rows if r and r[2] == "Name" and F.BASE_YEAR in r)
    row = next(r for r in rows if r and r[2] == "IBRI")
    n["wilayat_2024"] = float(row[hdr.index(F.BASE_YEAR)])
    n["area_km2"] = float(gpd.read_file(os.path.join(F.SHP, "Settlements_merged.shp")).area.sum() / 1e6)
    n["gr"] = F.growth_rates()

    # land-use rules
    n["why_all"] = p.WHYC.value_counts().to_dict()
    n["why_built"] = p.loc[built, "WHYC"].value_counts().to_dict()
    ag = p.DERIVED == "Agricultural"
    n["farm_pop"], n["farm_q"] = float(p.loc[ag, "POP"].sum()), float(p.loc[ag, "QADF"].sum())
    n["farm_with_dom"] = int((ag & (p.G_DOM > 0)).sum())
    tot = p.G_DOM + p.G_NDOM + p.G_GOV
    base = built & p.ESTATE.isna() & (p.G_AGR == 0) & (p.G_SPEC == 0)
    ex = lambda dd, nd, gv: p.loc[base & (p.G_DOM == dd) & (p.G_NDOM == nd) & (p.G_GOV == gv), "WHYC"].value_counts().to_dict()
    n["ex_21"], n["ex_31"], n["ex_2g"] = ex(2, 1, 0), ex(3, 1, 0), ex(2, 0, 1)

    # satellite test
    a = p.AREA_M2; nm = p.NDVI_MEAN.fillna(0); ns = p.NDVI_SHARE.fillna(0); ga = p.GREEN_M2.fillna(0)
    b1 = (ga >= 1000) & (nm >= 0.20); b2 = (ns >= 0.60) & (nm >= 0.40) & (a >= 800); green = b1 | b2
    grn = p.WHYC == "GRN"
    n["grn_b1only"], n["grn_b2only"], n["grn_both"] = int((grn & b1 & ~b2).sum()), int((grn & b2 & ~b1).sum()), int((grn & b1 & b2).sum())
    fm = built & (p.G_AGR > 0)
    n["fm"], n["fm_green"] = int(fm.sum()), int((fm & green).sum())
    hm = built & p.ESTATE.isna() & (p.G_AGR == 0) & (tot > 0) & (p.G_DOM / tot.where(tot > 0) > 2 / 3)
    n["hm"], n["hm_green"] = int(hm.sum()), int((hm & green).sum())
    ov = green & built & (p.G_AGR == 0) & p.ESTATE.isna() & (p.Classes != "Tourism") & ~grn
    n["override"] = p.loc[ov, "WHYC"].value_counts().to_dict()
    n["grn_built"], n["grn_empty"] = int((grn & built).sum()), int((grn & ~built).sum())
    n["ndvi_empty"] = float(np.nanmedian(p.loc[~built & ~green, "NDVI_MEAN"]))
    n["ndvi_res50"], n["ndvi_res90"] = [float(v) for v in np.nanpercentile(p.loc[built & (p.WHYC == "RES"), "NDVI_MEAN"], [50, 90])]
    n["ndvi_fm"] = float(np.nanmedian(p.loc[fm, "NDVI_MEAN"]))
    n["ndvi_grn"] = float(np.nanmedian(p.loc[grn, "NDVI_MEAN"]))

    def pick(mask):
        s = p[mask].sort_values("AREA_M2")
        r = s.iloc[len(s) // 2]
        return dict(fid=int(s.index[len(s) // 2]), settle=F.NAME.get(r.SETTLE, r.SETTLE.title()), area=float(r.AREA_M2),
                    mean=float(r.NDVI_MEAN), share=float(r.NDVI_SHARE), green=float(r.GREEN_M2), dom=int(r.G_DOM),
                    pop=float(r.POP))
    n["ex_b1"] = pick(grn & built & b1 & ~b2)
    n["ex_b2"] = pick(grn & built & b2 & ~b1)
    return n


# ------------------------------------------------------------------ helpers
def _lab(d, lead, text):
    return D.rich(d, (lead + "  ", {"bold": True}), (text, {}))


def _src(d, text):
    return D.rich(d, ("Source.  ", {"bold": True}), (text, {"italic": True, "colour": D.GREY}))


def _where(d, text):
    return D.rich(d, ("Where it lives.  ", {"bold": True}), (text, {"colour": D.GREY}), space_after=10)


def _sym(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)
    D.p(d, "", space_after=2)


def _pct(a, b, nd=1):
    return F.fmt(100.0 * a / b, nd) if b else "0"


def _sub(base, s):
    return M.sub(R(base), UP(s))


# =============================================================== CHAPTER 1
def c01_data(d):
    n = _n(); mc, ps, cs = n["mc"], n["ps"], n["cs"]
    D.h(d, 1, "1   The data", page_break=True)
    D.p(d, "The load chain rests on five datasets. None of them was made for sewer design, and each answers "
           "only part of the question. The electricity meters say how many premises there are and what kind, "
           "but not how large they are. The cadastre says where the plots are and whether they are built, but "
           "its land-use field is unreliable. The settlement series says how many people live in each "
           "settlement and how fast that number grows, but not where inside the settlement they live. The "
           "public record finds the few large users that none of the three shows. This chapter describes what "
           "each dataset carries, what it lacks, and the decisions taken to make it usable. Chapter 2 then puts "
           "the meters on the plots and reads the use of every plot from them.")

    D.tab_caption(d, "The five datasets and what each can and cannot tell")
    D.table(d, ["Dataset", "Carries", "Does not carry", "Used for"], [
        ["Electricity meters, 2024", f"{F.fmt(mc['total'])} points, a tariff name each",
         "consumption, address, land use, floor area", "properties; non-domestic and governmental premises"],
        ["Large-consumer register", f"{F.fmt(cs['total'])} accounts on the Cost Reflective Tariff, placed by public data",
         "any use in the source data; the use was found by search", "the category of the largest consumers"],
        ["Cadastre, September 2026", f"{F.fmt(ps['total'])} plots, geometry, a built flag, a class",
         "a government class; a reliable use", "the unit the load lands on; built or empty"],
        ["Settlements and population series", "25 settlement outlines; population per settlement, 2023 to 2100",
         "where inside a settlement people live", "occupancy in 2024; the growth rate"],
        ["Identified projects", "estates, camps, planned schemes, tanker sources found in public records",
         "workforce, occupancy, discharge", "loads kept outside the population ratios"],
    ], widths=[3.4, 4.6, 4.2, 4.3], font=8.5)
    D.p(d, "", space_after=2)

    # ------------------------------------------------------------ 1.1 meters
    D.h(d, 2, "1.1   The electricity meters")
    _lab(d, "What it is for.", "The meters are the only complete count of premises in the study area. A domestic "
         "meter is a property, and a shop or government meter is a non-domestic or governmental premises. "
         "Every population and every load placement in this tutorial starts from them.")
    D.p(d, f"The dataset holds {F.fmt(mc['total'])} electricity accounts for 2024, the base year of the design. "
           "Each is one point with one attribute, the tariff name. There is no consumption figure, no address and "
           "no land use. The points were shifted onto the cadastre before use, so that a meter drawn on a house "
           "falls inside that house's plot. The dataset therefore says what kind of customer sits at a point and "
           "how many there are. It can never say how large the customer is, and that single limit is why the "
           "non-domestic demand is set by the guideline ratios and not by the unit rates of G201 Table 12, "
           "which are priced in pupils, beds, employees and floor area.")
    _lab(d, "The rule.", "Each of the thirteen tariffs is folded into one of the guideline's demand categories. "
         "A domestic tariff is one property, whatever it is called. The Additional Account Tariff is a second "
         "dwelling on the same plot, so it is a property in its own right. Shop, government, farm and "
         "large-consumer meters carry no people. An agricultural meter drives an irrigation pump whose water goes "
         "onto a field, so it carries no sewage. The Cost Reflective Tariff (CRT) is a consumption class, not a "
         "use, and each of its accounts takes the category of the use found for it in Section 1.2.")
    rows = [[name, F.fmt(mc["tariff"].get(name, 0)), cat, ppl] for name, cat, ppl in TARIFFS]
    rows.append(["**Total**", f"**{F.fmt(mc['total'])}**", "", ""])
    D.tab_caption(d, "The thirteen tariffs and the category each takes")
    D.table(d, ["Tariff, as received", "Meters", "Category", "People"], rows, widths=[6.6, 1.8, 3.9, 4.2], font=8.5)
    D.p(d, "", space_after=2)

    D.p(d, "The number of domestic properties is the sum of the three domestic tariffs.")
    eq = D.next_eq()
    M.display(d, M.seq(_sub("N", "dom"), M.EQ, _sub("N", "P"), M.PLUS, _sub("N", "PS"), M.PLUS, _sub("N", "A")), number=eq)
    _sym(d, [["N dom", "domestic properties in the study area", "—"],
             ["N P", "meters on the Primary Account Tariff", "—"],
             ["N PS", "meters on the Primary Account Tariff with National Subsidy", "—"],
             ["N A", "meters on the Additional Account Tariff", "—"]])
    pp, ps_, pa = n["dom_parts"]
    _lab(d, "Ibri number.", f"N_dom = {F.fmt(pp)} + {F.fmt(ps_)} + {F.fmt(pa)} = {F.fmt(pp + ps_ + pa)} domestic "
         f"properties. The additional accounts are {_pct(pa, pp + ps_ + pa)} per cent of them: counting the "
         "primary tariffs alone would lose more than a quarter of the dwellings.")

    D.p(d, "Once the large-consumer accounts are resolved (Section 1.2), every meter sits in one of five "
           "categories. The table shows where each total comes from, so the two halves can be checked "
           "against each other.")
    cats = [("Domestic", "domestic"), ("Non-domestic", "non_domestic"), ("Governmental", "government"),
            ("Agricultural", "agricultural"), ("Special", "special")]
    rows = [[lab, F.fmt(n["tar_cat"].get(k, 0)), F.fmt(n["crt_cat"].get(k, 0)), F.fmt(mc["gud"].get(k, 0))] for lab, k in cats]
    rows.append(["**Total**", f"**{F.fmt(sum(n['tar_cat'].values()))}**", f"**{F.fmt(sum(n['crt_cat'].values()))}**",
                 f"**{F.fmt(sum(mc['gud'].values()))}**"])
    D.tab_caption(d, "Meters by category: from the tariff, from the large-consumer accounts, and in total")
    D.table(d, ["Category", "From the tariff", "From the large-consumer accounts", "Meters in the category"], rows,
            widths=[4.0, 3.6, 5.0, 3.9], font=9, align_right={1, 2, 3})
    D.p(d, "", space_after=2)
    _src(d, "G201-p59 §7.3 names the components of demand (domestic, non-domestic, tanker, and special "
            "categories such as industrial or institutional uses); §7.3.1 domestic G201-p59, §7.3.2 "
            "non-domestic G201-p60, §7.3.3 governmental G201-p61, §7.3.4 special G201-p61. The crosswalk from "
            "tariff to category is a project inference, not a guideline table (project rule, engineer, "
            "2026-09-09). Table 12 is not used: its drivers were not supplied (G201-p61; locked load basis, "
            "engineer, 2026-08-30).")
    _where(d, "W14/py/plots_meters_load.py, dictionaries GROUP (tariff to group) and GUD (group to category), "
              "run inside QGIS on the shifted meter layer. Output W14/shp/ELE_meters_on_plots.shp, one point "
              "per meter, fields TARIFF, GROUP, GUD, USE, PROPERTY (1 for a domestic meter). "
              "Counts: facts_w14.meter_counts().")
    D.picture(d, os.path.join(IMG, "M04_electricity.png"), 16.0)
    D.fig_caption(d, "The electricity meters by category after the large consumers are resolved, placed on the "
                     "plots. The data box gives the count in each category and the meters left free.")

    # ------------------------------------------------------------ 1.2 CRT
    D.h(d, 2, "1.2   The large-consumer accounts")
    _lab(d, "What it is for.", f"The {F.fmt(cs['total'])} accounts on the Cost Reflective Tariff are the "
         "largest consumers in the study area, and the tariff says nothing about what they are. The tariff "
         "applies above a consumption threshold, so a shopping centre, a hospital, a mosque and a factory all "
         "fall in it. Each account must be given a category before its water can be placed.")
    _lab(d, "The rule.", "Each account was placed by public data, in four passes, and takes the category of the "
         "use found:")
    D.numbered(d, "the accounts are clustered at 120 m, so a shopping centre with twenty meters is one site "
                  "and not twenty;", restart=True)
    D.numbered(d, "each cluster and each single account is matched against the named features of OpenStreetMap "
                  "within 80 m;")
    D.numbered(d, "what remains is reverse geocoded (Nominatim), and the largest clusters are inspected on the "
                  "aerial imagery;")
    D.numbered(d, "the identified-projects search (Section 1.5) adds the industrial estates and the "
                  "institutions named in the press.")
    D.p(d, "An account with no named feature within 80 m is recorded as unresolved and carried as non-domestic, "
           "the largest class among the resolved accounts. Every account carries a confidence: certain where a "
           "named feature lies within 20 m or the site was inspected; likely where one lies within 80 m or the "
           "reverse geocoding names it; guessing where only the surroundings speak.")
    conf = n["crt_conf"]
    cc = lambda use, k: F.fmt(int(conf.at[use, k])) if (use in conf.index and k in conf.columns) else "0"
    rows = [[use.replace("Telecom/Utility", "Telecommunications, utility"), F.fmt(cs["use"].get(use, 0)), cat,
             cc(use, "Certain"), cc(use, "Likely"), cc(use, "Guessing"), sites] for use, cat, sites in CRT_USE]
    rows.append(["**Total**", f"**{F.fmt(cs['total'])}**", "", F.fmt(cs['conf'].get('Certain', 0)),
                 F.fmt(cs['conf'].get('Likely', 0)), F.fmt(cs['conf'].get('Guessing', 0)), ""])
    D.tab_caption(d, "Large-consumer accounts by the use found, the category adopted and the confidence")
    D.table(d, ["Use found", "Accounts", "Category", "Certain", "Likely", "Guessing", "Typical sites"], rows,
            widths=[2.9, 1.5, 2.4, 1.3, 1.3, 1.5, 5.6], font=8, align_right={1, 3, 4, 5})
    D.p(d, "", space_after=2)
    top = n["crt_top"]
    _lab(d, "Ibri number.", f"{F.fmt(n['crt_in_clusters'])} of the {F.fmt(cs['total'])} accounts sit in "
         f"{n['crt_clusters']} clusters; the two largest hold {top[0]} and {top[1]} accounts (the Bawadi shopping "
         f"centre and the Al Murtafa souq). {cs['use'].get('Commercial', 0)} accounts are commercial and "
         f"{n['crt_cat'].get('government', 0)} governmental, educational, medical or religious. "
         f"{cs['use'].get('Unresolved', 0)} are unresolved and carried as non-domestic.")
    D.callout(d, "What a wrong category costs.",
              "The non-domestic and governmental water of a settlement is a pool set by its population, not by "
              "its meters (Chapter 2 and the load chapters). A large-consumer account in the wrong category "
              "therefore moves water from one plot to another inside the settlement; it does not change the "
              "total. The exception is a farm pump, which leaves the pool, and an estate meter, which the "
              "estate's workforce replaces.", fill="EAF1F8", colour=D.MID)
    D.p(d, "Older project documents left the large-consumer accounts unresolved, pending a site check. They are "
           "now resolved account by account, with the evidence recorded.")
    _src(d, "Project rule (engineer, 2026-09-09); G201-p59 §7.3.1 keeps specific identified non-domestic "
            "projects outside the ratios, which is why the industrial accounts are separated.")
    _where(d, f"W14/analysis/CRT_accounts_identified.csv, one row per account ({n['crt_register_rows']} rows: the "
              f"{F.fmt(cs['total'])} large-consumer accounts and the single Industrial-tariff account), fields USE, "
              "GUD_CAT, CONF, EVIDENCE and cl (the cluster; -1 for a single account). The register writes "
              "CRT_review for an unresolved account; the meter layer carries it as non_domestic. Working files "
              "in W14/analysis/crt_identify/ (classify_crt.py, osm_tiles.py, nominatim.csv). The category reaches "
              "each meter through the dictionary GUD_OF_USE in W14/py/plots_meters_load.py, field USE on "
              "ELE_meters_on_plots.shp. Counts: facts_w14.crt_summary().")

    # ------------------------------------------------------------ 1.3 cadastre
    D.h(d, 2, "1.3   The cadastre")
    _lab(d, "What it is for.", "The plot is the unit the load lands on. The network passes plots, and a pipe's "
         "flow is the sum of the plots upstream of it, so the plot layer is the load table of the design.")
    D.p(d, f"The cadastral layer received in September 2026 holds {F.fmt(ps['total'])} plots. Each has a geometry, "
           f"a class code and name, and a built flag. {F.fmt(n['built'])} plots are marked built and "
           f"{F.fmt(n['empty'])} future. In the file as used, the flag and the meters agree exactly: "
           f"{F.fmt(n['built_unmetered'])} built plots are without a meter and {F.fmt(n['future_metered'])} "
           "future plots carry one. The built flag can therefore be read as \"has a meter\", and it is not an "
           "independent check on the meters.")
    _lab(d, "The rule.", "Trust the geometry and the built flag. Use the class for two things only: the "
         "Tourism class, which is the old quarter of Ibri, and the Industrial class inside the two estates, "
         "which carries the estate workforce. Derive the use of every other plot from its meters "
         "(Chapter 2).")
    D.p(d, "The class field cannot be trusted for use, for three reasons, each visible in the data:")
    D.bullet(d, "The classes are Residential, Residential-Commercial, Commercial, Agricultural, Industrial, "
                f"Tourism and Proposed. There is no government class, yet {F.fmt(n['gov_derived'])} built plots "
                "carry a government majority of meters;", lead="No government class. ")
    D.bullet(d, f"{F.fmt(n['codes_0_99'])} plots carry the codes 0 and 99 under the name Residential. The codes "
                "look like placeholders for an unclassified plot, not a survey of use;",
             lead="Placeholder codes. ")
    D.bullet(d, f"On the {F.fmt(n['built'])} built plots the class matches the use derived from the meters on "
                f"{F.fmt(n['agree'])} ({_pct(n['agree'], n['built'])} per cent). The largest disagreements are "
                f"{F.fmt(n['res_to_farm'])} plots called Residential that the satellite shows as groves and "
                f"{F.fmt(n['res_to_shop'])} called Residential whose meters are two thirds or more shops.",
             lead="Disagreement with the meters. ")
    ct = n["ct"]
    rows = []
    for cls in ct.index:
        tot = int(ct.loc[cls].sum()); same = int(ct.at[cls, cls]) if cls in ct.columns else 0
        other = ct.loc[cls].drop(labels=[cls], errors="ignore").sort_values(ascending=False)
        rows.append([cls, F.fmt(tot), F.fmt(same), _pct(same, tot, 0),
                     f"{other.index[0]} ({F.fmt(int(other.iloc[0]))})" if len(other) and other.iloc[0] > 0 else "—"])
    D.tab_caption(d, "Class in the cadastre against the use derived from the meters, built plots")
    D.table(d, ["Cadastre class", "Built plots", "Derived use the same", "Per cent", "Largest other derived use"], rows,
            widths=[3.8, 2.2, 3.2, 1.8, 5.5], font=8.5, align_right={1, 2, 3})
    D.p(d, "", space_after=2)
    _lab(d, "Ibri number.", f"{_pct(n['agree'], n['built'])} per cent agreement on the built plots, "
         f"{F.fmt(n['codes_0_99'])} plots on placeholder codes, and no government class at all.")
    _src(d, "G201-p58 §7.2.2 names the Ministry of Housing and Urban Planning as the official source of plot "
            "information and asks for plots \"classified by clear typologies\". The cadastre supplies the plots; "
            "the typology is derived (project rule, engineer, 2026-09-09).")
    _where(d, "W14/shp/PLOTS_load.shp, fields Name, Moh_Classi, Classes and Buiding_St as received, AREA_M2 added. "
              "The comparison of class and derived use per plot is the field AGREE in "
              "W14/analysis/plot_class_audit.csv (same, differs, new, unmetered).")

    # ------------------------------------------------------------ 1.4 settlements
    D.h(d, 2, "1.4   The settlements and the population series")
    _lab(d, "What it is for.", "Every rate in the load chain is a property of a settlement: the occupancy, the "
         "properties per plot, the share of empty land that becomes housing, the growth rate and the year the "
         "land is full. The series supplies two things and nothing else: each settlement's population in 2024, "
         "which the occupancy is measured against, and its growth rate.")
    D.p(d, f"The Inception Report supplied 25 settlement outlines and a population series for each settlement, "
           f"year by year from 2023 to 2100. The outlines are drawn around the built cores. They do not touch one "
           f"another and they leave the land between them unassigned. The project boundary, "
           f"{F.fmt(n['area_km2'], 1)} km², holds plots far outside every outline.")
    _lab(d, "The rule.", "The series is built in three parts. To 2040 it is the forecast of the National Centre "
         "for Statistics and Information for the Wilayat of Ibri, Omani and expatriate population separately. "
         "From 2041 to 2050 it is an extrapolation of that forecast, documented in the technical note on "
         "population issued with the Inception Report. "
         f"From 2051 the rate rises from {F.fmt(n['gr']['r2051'], 2)} per cent to 2.40 per cent a year, reached in "
         f"{n['gr']['year_240']}, and holds at 2.40 to 2100, the planning horizon instructed by Nama Water "
         "Services. The wilayat total is then split between "
         "the settlements in fixed shares taken from the census.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("P"), R("s")), M.delim(R("y")), M.EQ, M.sub(R("k"), R("s")), M.TIMES,
                       M.sub(R("P"), R("W")), M.delim(R("y")), R(",   "), M.sub(R("k"), R("s")), M.EQ,
                       M.frac(M.sub(R("P"), UP("s,census")), M.sub(R("P"), UP("W,census")))), number=eq)
    _sym(d, [["P s(y)", "population of settlement s in year y", "persons"],
             ["P W(y)", "population of the Wilayat of Ibri in year y", "persons"],
             ["k s", "settlement's share of the wilayat, fixed at the census", "—"]])
    D.p(d, "Because every share is fixed, every settlement grows at the same annual rate as the wilayat. The "
           "series says nothing about any one settlement's own momentum; it is used for the rate only.")
    gr = n["gr"]
    D.tab_caption(d, "Mean annual growth rate of the series, the 25 settlements")
    D.table(d, ["Period", "Mean rate, per cent a year", "Basis of the series"], [
        ["2024 to 2030", F.fmt(gr["d2024_2030"], 2), "national forecast"],
        ["2030 to 2040", F.fmt(gr["d2030s"], 2), "national forecast"],
        ["2040 to 2050", F.fmt(gr["d2040s"], 2), "extrapolation of the forecast"],
        ["2050 to 2060", F.fmt(gr["d2050s"], 2), f"ramp from {F.fmt(gr['r2051'], 2)} in 2051 to 2.40 by {gr['year_240']}"],
        ["2060 to 2100", F.fmt(gr["d2060on"], 2), "constant rate instructed by Nama Water Services"],
    ], widths=[3.5, 4.0, 9.0], font=9, align_right={1})
    D.p(d, "", space_after=2)
    ib = next(r for r in n["st"] if r["key"] == "IBRI")
    _lab(d, "Ibri number.", f"The wilayat holds {F.fmt(n['wilayat_2024'])} people in 2024. The 25 settlements in "
         f"the project boundary hold {F.fmt(n['wb_25'])}, which is {_pct(n['wb_25'], n['wilayat_2024'])} per cent "
         f"of it. Ibri itself holds {F.fmt(ib['workbook_2024'])}, a share of k = {F.fmt(ib['workbook_2024'] / n['wilayat_2024'], 3)}. "
         f"The series' own total in 2100 is not a saturation figure and is not used as one.")
    D.callout(d, "The series beyond 2050 is not data.",
              "G201-p58 does not recommend extrapolating more than ten years beyond the available forecast. The "
              "national forecast ends in 2040, so the series is inside that limit to 2050 and outside it after. "
              "The design therefore defends its saturation population on the capacity of the land, counted plot "
              "by plot, and uses the series only for the pace at which that land fills.")
    D.p(d, "Each plot is assigned to the settlement whose outline contains its centroid or, where none does, to "
           "the nearest outline. The outlines are then redrawn as a partition of the whole boundary, so that every "
           "plot lies in exactly one settlement and the settlements meet without gaps. The two outlines of Al "
           "Aynayn are treated as one settlement.")
    small = [r for r in n["st"] if r["small"]]
    rows = [[r["name"], F.fmt(r["workbook_2024"]), _pct(r["workbook_2024"], n["wb_25"]), F.fmt(r["properties"]),
             F.fmt(r["built_plots"]), F.fmt(r["empty_plots"]), "yes" if r["small"] else ""] for r in n["st"]]
    rows.append(["**Total**", f"**{F.fmt(n['wb_25'])}**", "**100.0**", f"**{F.fmt(sum(r['properties'] for r in n['st']))}**",
                 f"**{F.fmt(sum(r['built_plots'] for r in n['st']))}**", f"**{F.fmt(sum(r['empty_plots'] for r in n['st']))}**",
                 f"**{len(small)}**"])
    D.tab_caption(d, "The 25 settlements: census population 2024, domestic properties and plots")
    D.table(d, ["Settlement", "Census population 2024", "Share of the 25, %", "Domestic properties on plots",
                "Built plots", "Empty plots", "Under 1,000 people"], rows,
            widths=[3.4, 2.4, 2.0, 2.6, 2.0, 2.0, 2.1], font=8, align_right={1, 2, 3, 4, 5})
    D.p(d, "", space_after=2)
    D.p(d, f"The {len(small)} settlements of fewer than a thousand people have too few meters to measure a rate "
           "on. They are flagged here and take fixed rates in the occupancy chapter.")
    _src(d, "G201-p58 §7.2.1: the NCSI is the official source; a wilayat forecast is distributed to settlements in "
            "proportion to the latest census; extrapolation beyond ten years of the forecast is not recommended. "
            "The 2.40 per cent rate from 2051 is an instruction of Nama Water Services recorded in the Inception "
            "Report. Plot-to-settlement assignment and the partition: project rule (engineer, 2026-09-09 and "
            "2026-09-10).")
    _where(d, "_CLIENT/Ibri Sewer Demand R0 2026 08 03.xlsx, sheets Pop_Wilayat (the wilayat series) and Project "
              "Pop Settlements (the 25 settlements, columns Pop 2023 to Pop 2100). Plot to settlement: "
              "W14/py/plots_meters_load.py, field SETTLE on PLOTS_load.shp. Partition: "
              "W14/py/settlements_partition.py (Voronoi of the plot centroids, dissolved by settlement, clipped to "
              "the boundary, shared edges simplified at 25 m), output W14/shp/Settlements_merged.shp. Rates: "
              "facts_w14.growth_rates(); the settlement rows: facts_w14.settlement_table().")
    D.picture(d, os.path.join(IMG, "M05_settlements.png"), 16.0)
    D.fig_caption(d, "The 25 settlements redrawn as a partition of the project boundary, over the plots.")

    # ------------------------------------------------------------ 1.5 identified projects
    D.h(d, 2, "1.5   The identified projects")
    _lab(d, "What it is for.", "The guideline's population ratios cover the ordinary shops, offices and public "
         "buildings of a town. They exclude economic zones and special consumers such as labour camps and "
         "high-water industry, which must be found and added separately. None of these is visible as such in "
         "the meters, so the public record was searched for them.")
    e1, e2 = n["est"]["AL TAYYEB"], n["est"]["TANAM"]
    _lab(d, "The rule.", "Each site found is placed in one of three treatments: an identified project inside the "
         "boundary whose load is added to its plots; a site recorded but given no load until its data exists; or "
         "a source outside the boundary that can only reach the plant by tanker.")
    D.tab_caption(d, "Identified projects and special consumers")
    D.table(d, ["Site", "What the data shows", "Treatment"], [
        ["Al Tayyeb industrial area", f"{F.fmt(e1['ha'], 1)} ha footprint; {e1['plots']} plots inside it, "
         f"{e1['ind_plots']} of them Industrial in the cadastre; {F.fmt(e1['com'])} meters on the Commercial "
         f"tariff, {e1['crt']} large-consumer", f"special: {F.fmt(e1['workers'])} workers at {F.L_IND:.0f} l/d"],
        ["Tanam industrial area", f"{F.fmt(e2['ha'], 1)} ha footprint; {e2['plots']} plots, {e2['ind_plots']} "
         f"Industrial; {F.fmt(e2['com'])} Commercial-tariff meters, {e2['crt']} large-consumer",
         f"special: {F.fmt(e2['workers'])} workers at {F.L_IND:.0f} l/d"],
        ["Army camp, Northern Frontier Regiment", f"{F.fmt(n['army_ha'])} ha military land use, no meter in the "
         "dataset", "recorded; not connected; occupancy to come from the Ministry of Defence"],
        ["Ibri View resort, As Sulayf", "announced, about 2 km², not in the cadastre",
         "recorded; no load until its masterplan is issued"],
        ["Madayn Ibri Industrial City", f"outside the boundary, {F.fmt(n['madayn_ha'])} ha footprint, first phase "
         "on a collection tank", "possible tanker source to the plant"],
        ["Power station and solar plants", "outside the boundary, with a construction camp",
         "possible tanker source to the plant"],
    ], widths=[4.0, 7.0, 5.5], font=8.5)
    D.p(d, "", space_after=2)
    D.p(d, "The two estates were hidden under the Commercial tariff, which is why the tariff alone never showed an "
           "industrial area. Their workforce is an assumption made from the meter count, since no employment "
           "figure was supplied. It is spread over the estate's Industrial plots by area, and the meters inside "
           "the estates are taken out of the non-domestic pool so the estate water is not counted twice.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("W"), UP("spec,i")), M.EQ, R("93"), M.TIMES, M.sub(R("N"), UP("w")), M.TIMES,
                       M.frac(M.sub(R("A"), R("i")), M.nary("∑", R("j"), "", M.sub(R("A"), R("j")), hide_hi=True))),
              number=eq)
    _sym(d, [["W spec,i", "special water on Industrial plot i of an estate", "l/d"],
             ["93", "dry industry, per employee (G201-p61 Table 12)", "l/d"],
             ["N w", "assumed workforce of the estate", "persons"],
             ["A i, A j", "area of plot i; areas of all the estate's Industrial plots", "m²"]])
    wt = e1["workers"] + e2["workers"]
    _lab(d, "Ibri number.", f"{F.fmt(e1['workers'])} + {F.fmt(e2['workers'])} = {F.fmt(wt)} workers × "
         f"{F.L_IND:.0f} l/d = {F.fmt(wt * F.L_IND / 1000, 1)} m³/d of water, and × {F.RET_ND} returned = "
         f"{F.fmt(wt * F.L_IND * F.RET_ND / 1000, 1)} m³/d of sewage. The plot layer sums to "
         f"{F.fmt(ps['s_spec'], 1)} m³/d. The dwellings on estate plots ({e1['dom']} and {e2['dom']} domestic "
         "meters) still carry their people at the domestic rate.")
    if n["spec_outside"]:
        sites = " and ".join(f"one in {s} (fid {fid})" for fid, s, _ in n["spec_outside"])
        D.p(d, f"Special meters also stand on {len(n['spec_outside'])} plots outside both estates, {sites}. They make their "
               "plots industrial in Chapter 2, but they carry no water of their own: they are not in the "
               "non-domestic pool and they have no workforce.")
    _src(d, "G201-p59 §7.3.1: the ratios do not apply to specific identified non-domestic projects such as economic "
            "zones, which are determined case by case. G201-p61 §7.3.4: special consumption is not covered by the "
            "population forecast. G201-p61 Table 12: dry industry 93 l/d per employee; army camps 185 l/d per "
            "occupant. G201-p71 Table 19: non-domestic return 54 per cent. Workforce 4,500 and 1,800: outside "
            "assumption, tagged (engineer, 2026-09-09). Army camp, resort and tanker sources: recorded only "
            "(engineer, 2026-09-09).")
    _where(d, "W14/analysis/IDENTIFIED_PROJECTS.md (every site, its source and confidence); footprints in "
              "W14/shp/Identified_projects_OSM.shp. On the plots: fields ESTATE, WORKERS, W_SPEC and S_SPEC of "
              "PLOTS_load.shp, the workforce written by W14/py/plots_meters_load.py and rescaled to the stated "
              "totals in W14/py/plot_class_v2_apply.py. Constants facts_w14.WORKERS and facts_w14.L_IND.")

    # ------------------------------------------------------------ 1.6 check
    D.h(d, 2, "1.6   Check it yourself")
    D.numbered(d, "Open ELE_meters_on_plots.shp and count the points by TARIFF; the thirteen counts must match "
                  "the tariff table and sum to the total.", restart=True)
    D.numbered(d, "Count the same layer by GUD and compare with the category table: the tariff side plus the "
                  "large-consumer side must give each category total.")
    D.numbered(d, "Filter CRT_accounts_identified.csv on USE = Unresolved and confirm every row has CONF = Guessing "
                  "and no feature within 80 m in EVIDENCE.")
    D.numbered(d, "In PLOTS_load.shp, cross-tabulate Classes against DERIVED on the built plots; the diagonal is "
                  "the agreement quoted in Section 1.3.")
    D.numbered(d, "Sum Pop 2024 over the 25 settlements in the demand workbook and divide by the wilayat's 2024 "
                  "value in Pop_Wilayat; the share must match Section 1.4.")
    D.numbered(d, "Sum WORKERS over the plots with ESTATE = AL TAYYEB and = TANAM; each must return the stated "
                  "workforce, and S_SPEC must sum to the estate sewage in Section 1.5.")


# =============================================================== CHAPTER 2
def c02_plots(d):
    n = _n(); mc, ps = n["mc"], n["ps"]
    D.h(d, 1, "2   From meter to plot, and the use of every plot", page_break=True)
    D.p(d, "This chapter does two things. It puts every meter on a plot, so that each plot carries a count of "
           "its meters in every category. It then reads the main use of every plot from those counts, in a fixed "
           "order of rules, with the satellite deciding where the plot is a grove. The first step sets the load of "
           "every built plot. The second does not, and it is worth being clear about that before the rules.")

    # ------------------------------------------------------------ 2.1 meter to plot
    D.h(d, 2, "2.1   Meter to plot")
    _lab(d, "What it is for.", "A meter's load reaches the network only through a plot. Every meter must "
         "therefore sit on exactly one plot, or be recorded as carrying nothing.")
    _lab(d, "The rule.", "Each meter is tested in this order:")
    D.numbered(d, "a meter inside a plot belongs to that plot;", restart=True)
    D.numbered(d, "a meter inside no plot, on a road or in a gap, is moved to the nearest plot within 15 m (the "
                  "five nearest plots are tested and the closest is taken);")
    D.numbered(d, "a meter further than 15 m from any plot stays free. It is listed with its nearest settlement "
                  "and carries no load in the plot table.")
    D.p(d, "Each plot then counts its meters twice: by tariff group, as received, and by category, with the large "
           "consumers placed by their use. The domestic count is the property count of the plot.")
    eq = D.next_eq()
    M.display(d, M.seq(_sub("G", "DOM"), M.EQ, _sub("N", "DOM"), M.PLUS, _sub("N", "DOMADD")), number=eq)
    _sym(d, [["G DOM", "domestic meters on the plot: its properties", "—"],
             ["N DOM", "meters on the primary and subsidised primary tariffs", "—"],
             ["N DOMADD", "meters on the Additional Account Tariff", "—"]])
    D.tab_caption(d, "The meter counts every plot carries")
    D.table(d, ["Field", "Counts", "Includes"], [
        ["N_DOM, N_DOMADD", "tariff groups, domestic", "primary and subsidised; additional"],
        ["N_COM, N_GOV", "tariff groups", "Commercial with Fisheries and Tourism; Government with MOD"],
        ["N_AGR, N_CRT, N_IND", "tariff groups", "Agricultural; the three CRT tariffs; Industrial"],
        ["G_DOM", "category, domestic", "N_DOM + N_DOMADD"],
        ["G_NDOM", "category, non-domestic", "N_COM + large consumers found commercial, utility or unresolved"],
        ["G_GOV", "category, governmental", "N_GOV + large consumers found government, education, health, religious"],
        ["G_SPEC", "category, special", "N_IND + large consumers found industrial"],
        ["G_AGR", "category, agricultural", "N_AGR + large consumers found agricultural"],
    ], widths=[3.6, 4.0, 8.9], font=8.5)
    D.p(d, "", space_after=2)
    fb = n["free_by"]
    _lab(d, "Ibri number.", f"Of the {F.fmt(mc['total'])} meters, {F.fmt(mc['inside'])} fall inside a plot, "
         f"{F.fmt(mc['snapped'])} were moved to a plot within 15 m and {F.fmt(mc['free'])} stay free: "
         f"{fb.get('domestic', 0)} domestic, {fb.get('non_domestic', 0)} non-domestic, {fb.get('government', 0)} "
         f"governmental and {fb.get('agricultural', 0)} agricultural. The plots therefore hold "
         f"{F.fmt(mc['gud'].get('domestic', 0))} − {fb.get('domestic', 0)} = {F.fmt(ps['properties'])} domestic "
         "properties.")
    D.callout(d, "The free dwellings are a stated gap, not a rounding.",
              f"The {fb.get('domestic', 0)} free domestic meters are real dwellings whose people are not in the "
              "plot table. They are too few to move a pipe size, but whether to snap them regardless of distance "
              "is an open decision, and the total is stated rather than hidden.")
    D.p(d, "Older project documents left meters outside a plot unassigned until the corrected cadastre arrived, "
           "so that a moved meter would not shift load between streets. The corrected cadastre has arrived, and "
           "the 15 m rule now applies.")
    _src(d, "Project rule (engineer, 2026-09-09). G201-p58 §7.2.1 itself allows population to be distributed "
            "within a settlement \"on a pro-rata basis using the number of electricity accounts\"; the method "
            "goes one step finer, to the plot.")
    _where(d, "W14/py/plots_meters_load.py (run inside QGIS), constant SNAP_M = 15.0 m; field PLACE (inside, snapped, free) "
              "and PLOT_FID on W14/shp/ELE_meters_on_plots.shp; the counts N_* and G_* on "
              f"W14/shp/PLOTS_load.shp. The layer also has a field SNAP_M for the distance moved, but it reads 0 "
              f"on all {F.fmt(mc['snapped'])} moved meters ({n['snap_nonzero']} non-zero): the distance was not "
              "written, and the 15 m limit is enforced only by the search radius. Counts: "
              "facts_w14.meter_counts().")

    # ------------------------------------------------------------ 2.2 what the use does
    D.h(d, 2, "2.2   What the use of a plot does, and what it does not")
    _lab(d, "What it is for.", "The use class answers questions the meters alone cannot: which built plots are "
         "plain homes, so that properties per plot and the home share can be measured on them; and which empty "
         "plots can ever become homes or receive growth. It also draws the land-use map.")
    D.p(d, "The use class does not set the load of a built plot. The people come from the domestic meters, the "
           "non-domestic water from the shop meters and the governmental water from the government meters, "
           "whatever the plot is called. A house in a palm grove is classed as a farm, and its dwellings still "
           "carry their people. The only exception is the estate, which is decided by the footprint and not by "
           "the class: an estate plot carries its workforce and its dwellings, and its shop meters leave the pool.")
    _lab(d, "Ibri number.", f"The plots classed as farms carry {F.fmt(n['farm_pop'])} people and "
         f"{F.fmt(n['farm_q'])} m³/d of sewage in 2024, because {F.fmt(n['farm_with_dom'])} of them hold "
         "dwelling meters. Reclassifying all of them would not change today's flow by one litre; it would change only "
         "the samples and the exclusions described above.")

    # ------------------------------------------------------------ 2.3 rules
    D.h(d, 2, "2.3   The land-use rules, in their fixed order")
    _lab(d, "What it is for.", "One class per plot, set the same way everywhere, so that the samples used later "
         "(the pure home plots) and the exclusions (groves, estates, heritage) are reproducible.")
    D.picture(d, os.path.join(IMG, "D6_landuse.png"), 13.5)
    D.fig_caption(d, "How the use of each plot is derived from the electricity meters, the satellite and the plot "
                     "itself.")
    D.p(d, "The proportion rules work on the meters that carry people or water. Farm and special meters are kept "
           "out of the denominator, so a farm pump does not dilute the home share of a house.")
    eq = D.next_eq()
    M.display(d, M.seq(_sub("N", "t"), M.EQ, _sub("G", "DOM"), M.PLUS, _sub("G", "NDOM"), M.PLUS, _sub("G", "GOV"),
                       R(",     "), _sub("f", "k"), M.EQ, M.frac(_sub("G", "k"), _sub("N", "t"))), number=eq)
    _sym(d, [["N t", "meters on the plot that carry people or water: domestic, non-domestic, governmental", "—"],
             ["f k", "share of those meters in category k (dom, nd, gov)", "—"],
             ["G k", "meters of category k on the plot", "—"],
             ["G SPEC, G AGR", "special and agricultural meters; they enter only rules 3 and 6", "—"]])
    _lab(d, "The rule.", "The first rule that holds sets the class. The order matters: a rule lower down never "
         "sees a plot a rule above has taken.")
    wa, wb = n["why_all"], n["why_built"]
    rules = [
        ("1", "centroid inside the Al Tayyeb or Tanam footprint", "Industrial", "EST"),
        ("2", "cadastre class Tourism (the old quarter of Ibri)", "Heritage", "HER"),
        ("3", "any agricultural meter, G_AGR > 0", "Agricultural", "AGR"),
        ("4", "a grove by satellite (Section 2.4), unless f_nd ≥ 2/3 or f_gov > 1/2", "Agricultural", "GRN"),
        ("5", "no domestic, non-domestic, governmental or special meter", "Unmetered (empty)", "UNM"),
        ("6", "G_SPEC > 0 and G_SPEC ≥ G_DOM", "Industrial", "IND"),
        ("7", "N_t = 0 (a guard; cannot hold after rules 5 and 6)", "Unresolved", "UNR"),
        ("8", "f_dom > 2/3", "Residential (home)", "RES"),
        ("9", "f_gov ≥ 2/3", "Government", "GOV"),
        ("10", "f_nd ≥ 2/3", "Commercial (shop)", "COM"),
        ("11a", "none of 8 to 10, and G_NDOM ≥ G_GOV", "Residential-Commercial (home and shop)", "RC"),
        ("11b", "none of 8 to 10, and G_NDOM < G_GOV", "Government", "RG"),
    ]
    rows = [[o, test, cls, code, F.fmt(wa.get(code, 0)), F.fmt(wb.get(code, 0))] for o, test, cls, code in rules]
    rows.append(["", "**Total**", "", "", f"**{F.fmt(sum(wa.values()))}**", f"**{F.fmt(sum(wb.values()))}**"])
    D.tab_caption(d, "The land-use rules in the order they are applied, and the plots each one sets")
    D.table(d, ["Rule", "Test", "Class", "WHYC", "All plots", "Built plots"], rows,
            widths=[1.1, 6.6, 3.7, 1.3, 1.9, 1.9], font=8.5, align_right={4, 5})
    D.p(d, "", space_after=2)
    D.p(d, "Four features of the order carry the method:")
    D.bullet(d, "The estate footprint comes first, so a house or a shop inside an estate is industrial land. Its "
                "people still count; its shop meters leave the pool (Section 1.5).", lead="Estate first. ")
    D.bullet(d, "A farm meter beats every meter mix, because the pump proves the land is irrigated. The satellite "
                "grove is weaker evidence and gives way to a clear shop majority (two thirds) or a simple "
                "government majority, since a school or a clinic often stands among palms.",
             lead="Farm by meter, then by satellite. ")
    D.bullet(d, "A plot is a home only if more than two thirds of its meters are domestic. Government and shop "
                "take two thirds or more. A plot with exactly two thirds dwellings is therefore mixed, not a home, "
                "and the home sample stays pure.", lead="The strict inequality. ")
    D.bullet(d, "Between the thresholds the shop and government meters decide: a tie goes to home and shop.",
             lead="Mixed plots. ")
    x21, x31, x2g = n["ex_21"], n["ex_31"], n["ex_2g"]
    _lab(d, "Ibri number.", "Three meter mixes that occur in the data, outside the estates and without farm or "
         "special meters:")
    D.tab_caption(d, "Three meter mixes and the class each takes")
    D.table(d, ["Meters on the plot", "N t", "Shares", "Rule", "Class", "Built plots with this mix"], [
        ["2 domestic, 1 shop", "3", "f_dom = 0.667, f_nd = 0.333", "11a", "Residential-Commercial",
         ", ".join(f"{F.fmt(v)} {k}" for k, v in x21.items())],
        ["3 domestic, 1 shop", "4", "f_dom = 0.750", "8", "Residential",
         ", ".join(f"{F.fmt(v)} {k}" for k, v in x31.items())],
        ["2 domestic, 1 government", "3", "f_dom = 0.667, f_gov = 0.333", "11b", "Government",
         ", ".join(f"{F.fmt(v)} {k}" for k, v in x2g.items())],
    ], widths=[3.4, 1.0, 4.0, 1.2, 3.4, 3.5], font=8.5)
    D.p(d, "", space_after=2)
    D.p(d, "The plots of the same mix that carry the code GRN are groves: rule 4 took them before the proportion "
           "was read. The third row shows what rule 11b does to a small house with a government meter: the plot "
           "is classed Government, while its two dwellings keep their people.")
    if n["spec_outside"]:
        D.p(d, f"Rule 6 fires on {wa.get('IND', 0)} plots, the ones with special meters outside the estates: each "
               "has no dwelling and one special meter, so G_SPEC ≥ G_DOM holds.")
    _src(d, "Project rules: farm first and the two-thirds proportions (engineer, 2026-09-09); the government "
            "majority over the satellite grove, the heritage quarter and the satellite test (engineer, "
            "2026-09-10). The guideline asks for plots \"classified by clear typologies\" (G201-p58 §7.2.2) and "
            "gives no rule for deriving them; the thresholds are the project's.")
    _where(d, "W14/py/plot_class_v2_apply.py, function classify(r); fields DERIVED (the class) and WHYC (the rule "
              "code) on W14/shp/PLOTS_load.shp. The first, naive class and the dropped tests are kept for audit in "
              "W14/analysis/plot_class_audit.csv (DERIVED1, AGREE, GREEN, GREEN_IMG, VEGFRAC, HIGH).")

    # ------------------------------------------------------------ 2.4 NDVI
    D.h(d, 2, "2.4   The satellite grove test")
    _lab(d, "What it is for.", f"The farm meter alone under-counts farms. Of the {F.fmt(n['fm'])} built plots "
         f"with a farm meter, {F.fmt(n['fm'] - n['fm_green'])} ({F.fmt(F.farm_bare_share() * 100)} per cent) show "
         "no crop: they are pump sites, and the grove the pump waters lies on a neighbouring plot that carries "
         "only a house meter, or none. The satellite finds those groves.")
    D.p(d, "The test uses one cloud-free Sentinel-2 scene of 9 September 2026, red and near-infrared bands at 10 m, "
           "from the public archive. One scene is enough because the date palm is evergreen: a grove reads green "
           "in any month, and a dry-season scene keeps seasonal crops from passing for groves.")
    _lab(d, "The rule.", "The vegetation index is computed per pixel from the surface reflectance of the two bands.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("NDVI"), M.EQ, M.frac(M.seq(_sub("ρ", "NIR"), M.MINUS, _sub("ρ", "red")),
                                                 M.seq(_sub("ρ", "NIR"), M.PLUS, _sub("ρ", "red"))),
                       R(",     "), R("ρ"), M.EQ, UP("max"),
                       M.delim(M.seq(R("0, "), M.frac(M.seq(UP("DN"), M.MINUS, R("1000")), R("10000"))))), number=eq)
    _sym(d, [["ρ NIR, ρ red", "surface reflectance, band B08 (near-infrared) and band B04 (red)", "—"],
             ["DN", "stored value of the Level-2A product, which carries an offset of 1,000", "—"],
             ["NDVI", "normalised difference vegetation index", "—"]])
    D.p(d, "The offset matters and the scale does not: the 10,000 cancels in the ratio, but without subtracting "
           "the 1,000 a dark grove reads an index above one. Each plot then gets three numbers over the pixels that "
           "touch it: the mean index, the share of pixels at 0.30 or more, and the green area.")
    eq = D.next_eq()
    M.display(d, M.seq(_sub("A", "g"), M.EQ, R("s"), M.TIMES, UP("min"), M.delim(M.seq(R("A, 100"), R("n")))), number=eq)
    _sym(d, [["A g", "green area of the plot (GREEN_M2)", "m²"],
             ["s", "share of the plot's pixels with NDVI ≥ 0.30 (NDVI_SHARE)", "—"],
             ["A", "plot area (AREA_M2)", "m²"],
             ["n", "pixels touching the plot; each covers 100 m²", "—"]])
    D.p(d, "A plot is a grove where either condition holds:")
    D.bullet(d, "A green area of at least 1,000 m² at a mean index of at least 0.20; this catches a large orchard "
                "even when part of the plot is bare or built;", lead="Large grove. ")
    D.bullet(d, "A plot of at least 800 m² that is at least 60 per cent green at a mean index of at least 0.40; "
                "this catches a small, dense garden that never reaches 1,000 m² of green.", lead="Small grove. ")
    D.p(d, "The thresholds were set on two groups of built plots: the plots with a farm meter as the positives, and "
           "the plots whose meters are more than two thirds domestic and carry no farm meter as the negatives. "
           "Mean index and green area were swept against both groups, then the result was checked by eye on "
           "contact sheets of aerial thumbnails. An earlier test on the colour of the aerial imagery was tried and "
           "dropped, because it put farms on bare ground.")
    D.tab_caption(d, "What the index reads on the ground, and how the test separates the groups")
    D.table(d, ["Group of plots", "Plots", "Median mean NDVI", "Called a grove by the test"], [
        ["Empty plots that fail the test (bare desert)", "", F.fmt(n["ndvi_empty"], 3), "—"],
        ["Built plots classed as homes", F.fmt(wb.get("RES", 0)), f"{F.fmt(n['ndvi_res50'], 3)} (90th percentile "
         f"{F.fmt(n['ndvi_res90'], 3)})", "none, by construction"],
        ["Built plots with a farm meter (positives)", F.fmt(n["fm"]), F.fmt(n["ndvi_fm"], 3),
         f"{F.fmt(n['fm_green'])} ({_pct(n['fm_green'], n['fm'], 0)} %)"],
        ["Built plots, more than two thirds domestic, no farm meter", F.fmt(n["hm"]), "",
         f"{F.fmt(n['hm_green'])} ({_pct(n['hm_green'], n['hm'])} %)"],
        ["Plots classed as groves by rule 4", F.fmt(wa.get("GRN", 0)), F.fmt(n["ndvi_grn"], 3), "all"],
    ], widths=[6.6, 1.8, 3.9, 4.2], font=8.5, align_right={1})
    D.p(d, "", space_after=2)
    b1, b2 = n["ex_b1"], n["ex_b2"]
    _lab(d, "Ibri number.", f"Of the {F.fmt(wa.get('GRN', 0))} groves, {F.fmt(n['grn_both'])} pass both conditions, "
         f"{F.fmt(n['grn_b1only'])} only the large-grove one and {F.fmt(n['grn_b2only'])} only the small-grove one. "
         f"Two of them, each the median-sized plot of its kind:")
    D.tab_caption(d, "Two groves worked through the test")
    D.table(d, ["", "Large grove only", "Small grove only"], [
        ["Plot (fid), settlement", f"{b1['fid']}, {b1['settle']}", f"{b2['fid']}, {b2['settle']}"],
        ["Area A, m²", F.fmt(b1["area"]), F.fmt(b2["area"])],
        ["Share s at NDVI ≥ 0.30", F.fmt(b1["share"], 3), F.fmt(b2["share"], 3)],
        ["A g = s × A, m²", f"{F.fmt(b1['share'] * b1['area'])} (stored {F.fmt(b1['green'])})",
         f"{F.fmt(b2['share'] * b2['area'])} (stored {F.fmt(b2['green'])})"],
        ["Mean NDVI", F.fmt(b1["mean"], 3), F.fmt(b2["mean"], 3)],
        ["Large grove: A g ≥ 1,000 and mean ≥ 0.20", "yes" if (b1["green"] >= 1000 and b1["mean"] >= 0.2) else "no",
         "yes" if (b2["green"] >= 1000 and b2["mean"] >= 0.2) else "no"],
        ["Small grove: A ≥ 800, s ≥ 0.60, mean ≥ 0.40",
         "yes" if (b1["area"] >= 800 and b1["share"] >= 0.6 and b1["mean"] >= 0.4) else "no",
         "yes" if (b2["area"] >= 800 and b2["share"] >= 0.6 and b2["mean"] >= 0.4) else "no"],
        ["Dwelling meters; people carried", f"{b1['dom']}; {F.fmt(b1['pop'], 1)}", f"{b2['dom']}; {F.fmt(b2['pop'], 1)}"],
    ], widths=[6.0, 5.2, 5.2], font=8.5)
    D.p(d, "", space_after=2)
    ov = n["override"]
    D.p(d, f"{F.fmt(n['grn_built'])} of the groves are built plots and {F.fmt(n['grn_empty'])} are empty. The "
           "empty ones matter for the future: a grove is never counted as a future home and never receives "
           f"growth. The override kept {F.fmt(sum(ov.values()))} green built plots out of the farm class: "
           f"{F.fmt(ov.get('COM', 0))} with a shop majority and {F.fmt(ov.get('GOV', 0))} with a government "
           f"majority. {F.fmt(n['hm_green'])} home-majority plots became groves; they leave the home sample, and "
           "their people stay in the load.")
    _src(d, "Project calibration, not a guideline value (engineer, 2026-09-10). Sentinel-2 Level-2A, tile 40QDL, "
            "scene S2B_40QDL_20260909, bands B04 and B08 at 10 m, read from the public cloud archive.")
    _where(d, "W14/py/ndvi_plots.py (the index, the per-plot statistics and the calibration sweeps it prints); the "
              "index raster is saved under Hydraulic/Imagery, outside the repository, and never pushed. Per plot: "
              "W14/analysis/ndvi_plots.csv, and fields NDVI_MEAN, NDVI_SHARE and GREEN_M2 on PLOTS_load.shp. The "
              "test is applied as the flag GREEN in W14/py/plot_class_v2_apply.py (kept in plot_class_audit.csv); "
              "the contact sheets come from W14/py/ndvi_contact_sheet.py. facts_w14.farm_bare_share() repeats the "
              "test.")

    # ------------------------------------------------------------ 2.5 result
    D.h(d, 2, "2.5   The use of every plot")
    _lab(d, "What it is for.", "The class table is the input to the later chapters: the home plots give the "
         "properties per plot and the home share, and the exclusions decide which empty land can fill.")
    cls = ps["classes"]
    rows = [
        ["Home", F.fmt(cls.get("Residential", 0)), _pct(cls.get("Residential", 0), ps["metered"]), "8 (RES)"],
        ["Farm", F.fmt(cls.get("Agricultural", 0)), _pct(cls.get("Agricultural", 0), ps["metered"]),
         f"3 (AGR {F.fmt(ps['farms_by'].get('AGR', 0))}), 4 (GRN {F.fmt(ps['farms_by'].get('GRN', 0))})"],
        ["Shop", F.fmt(cls.get("Commercial", 0)), _pct(cls.get("Commercial", 0), ps["metered"]), "10 (COM)"],
        ["Home and shop", F.fmt(cls.get("Residential-Commercial", 0)), _pct(cls.get("Residential-Commercial", 0), ps["metered"]), "11a (RC)"],
        ["Government", F.fmt(cls.get("Government", 0)), _pct(cls.get("Government", 0), ps["metered"]),
         f"9 (GOV {F.fmt(wb.get('GOV', 0))}), 11b (RG {F.fmt(wb.get('RG', 0))})"],
        ["Industrial", F.fmt(cls.get("Industrial", 0)), _pct(cls.get("Industrial", 0), ps["metered"]),
         f"1 (EST {F.fmt(wb.get('EST', 0))}), 6 (IND {F.fmt(wb.get('IND', 0))})"],
        ["**Built plots with meters**", f"**{F.fmt(ps['metered'])}**", "**100.0**", ""],
        ["Heritage, the old quarter", F.fmt(ps["heritage"]), "", "2 (HER); no meter, no load"],
        ["Empty, no meter", F.fmt(wa.get("UNM", 0)), "", "5 (UNM)"],
        ["Empty grove", F.fmt(n["grn_empty"]), "", "4 (GRN); excluded from future homes"],
        ["Empty, inside an estate", F.fmt(wa.get("EST", 0) - wb.get("EST", 0)), "", "1 (EST); excluded from future homes"],
    ]
    D.tab_caption(d, "Use of every plot, built and empty")
    D.table(d, ["Use", "Plots", "Per cent of built", "Rule (code, built plots)"], rows,
            widths=[4.6, 2.0, 2.4, 7.5], font=8.5, align_right={1, 2})
    D.p(d, "", space_after=2)
    _lab(d, "Ibri number.", f"{F.fmt(ps['total'])} plots: {F.fmt(ps['metered'])} built with meters, of which "
         f"{_pct(cls.get('Residential', 0), ps['metered'])} per cent homes and "
         f"{_pct(cls.get('Agricultural', 0), ps['metered'])} per cent farms. "
         f"{F.fmt(ps['pure_home_plots'])} of the homes have fewer than {F.HIGH_METERS} dwelling meters and form "
         "the pure home sample used for properties per plot.")
    D.picture(d, os.path.join(IMG, "C07_landuse.png"), 15.0)
    D.fig_caption(d, "Use of the built plots that carry meters, as derived. Farms are found by the meter or by the "
                     "satellite.")
    D.picture(d, os.path.join(IMG, "M07_landuse.png"), 16.0)
    D.fig_caption(d, "Use of each plot derived from the meters and the satellite. Empty plots are shown in grey.")
    _src(d, "The rules of Section 2.3 and the test of Section 2.4.")
    _where(d, "field DERIVED on W14/shp/PLOTS_load.shp; counts facts_w14.plot_summary() (keys classes, farms_by, "
              "heritage, metered, pure_home_plots). The map is the QGIS layout behind report map M07; the chart "
              "is built by W14/report/charts_w14.py.")

    # ------------------------------------------------------------ 2.6 check
    D.h(d, 2, "2.6   Check it yourself")
    D.numbered(d, "Count ELE_meters_on_plots.shp by PLACE; inside, snapped and free must sum to the total. Select "
                  "the free meters and confirm none lies within 15 m of a plot.", restart=True)
    D.numbered(d, "Sum G_DOM over PLOTS_load.shp; it must equal the domestic meters less the free domestic ones.")
    D.numbered(d, "Pick any built plot, read G_DOM, G_NDOM, G_GOV, G_SPEC, G_AGR, NDVI_MEAN, NDVI_SHARE, GREEN_M2 "
                  "and AREA_M2, walk the rules of Section 2.3 in order, and compare the class you reach with DERIVED "
                  "and the rule with WHYC.")
    D.numbered(d, "Filter WHYC = GRN and G_DOM > 0: these are houses in groves. Their POP is not zero, which "
                  "confirms that the class does not remove people.")
    D.numbered(d, "Filter G_AGR > 0 on built plots and count those that fail both grove conditions; the share must "
                  "match the pump-site share in Section 2.4.")
    D.numbered(d, "Count DERIVED on the built plots; the counts must match the class table and the data box of the "
                  "land-use map.")
