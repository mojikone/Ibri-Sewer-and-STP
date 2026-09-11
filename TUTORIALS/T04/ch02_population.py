"""T04 chapters 3 to 5: properties per plot and the occupancy rate, the capacity of the empty land,
and growth, overflow and saturation.

Every number is read live from the W14 outputs through facts_w14 (and, where facts_w14 has no
function for it, from the same W14 files facts_w14 reads). Guideline values carry their page.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report"))   # after T04: its doc.py must not shadow ours
import doc as D  # noqa: E402
import omml as M  # noqa: E402
import facts_w14 as F  # noqa: E402

from functools import lru_cache  # noqa: E402

UP, R = M.up, M.r
IMG = os.path.join(HERE, "img")


# ------------------------------------------------------------------ helpers
def _lead(d, lead, text):
    """One of the five parts of a step: a bold lead, then the text."""
    return D.rich(d, (lead + ".  ", {"bold": True, "colour": D.MID}), (text, {}))


def _symbols(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)
    D.p(d, "", space_after=2)


def _fig(d, name, width, caption):
    D.picture(d, os.path.join(IMG, name), width)
    D.fig_caption(d, caption)


def _pct(x, nd=1):
    return F.fmt(x * 100, nd)


def _signed(x):
    if x >= 0.5:
        return "+" + F.fmt(x)
    if x <= -0.5:
        return "−" + F.fmt(-x)
    return "0"


def _by():
    return {r["key"]: r for r in F.settlement_table()}


@lru_cache(None)
def _plot_stats():
    """Counts on the plot layer that the text quotes and facts_w14 does not already return."""
    p = F.plots()
    built = p.Buiding_St == "EXisting"
    empty = p.Buiding_St == "Future"
    pure = built & (p.DERIVED == "Residential") & (p.G_DOM < F.HIGH_METERS) & (p.G_DOM > 0)
    anyd = built & (p.G_DOM > 0)
    high = built & (p.G_DOM >= F.HIGH_METERS)
    bh = built & (p.HOMESHAPE == 1) & (p.N_ACC > 0)
    ib = p.SETTLE == "IBRI"
    a = p.AREA_M2
    inr = empty & (a >= F.HOME_LO) & (a <= F.HOME_HI)
    return dict(
        pure=int(pure.sum()), pure_dom=int(p.loc[pure, "G_DOM"].sum()),
        ib_pure=int((pure & ib).sum()), ib_pure_dom=int(p.loc[pure & ib, "G_DOM"].sum()),
        ib_any=int((anyd & ib).sum()), ib_any_dom=int(p.loc[anyd & ib, "G_DOM"].sum()),
        high=int(high.sum()), high_dom=int(p.loc[high, "G_DOM"].sum()),
        bh=int(bh.sum()), bh_pure=int((bh & pure).sum()),
        ib_bh=int((bh & ib).sum()), ib_bh_pure=int((bh & pure & ib).sum()),
        med_area=float(a[pure].median()), med_compact=float(p.loc[pure, "COMPACT"].median()),
        med_aspect=float(p.loc[pure, "ASPECT"].median()),
        pure_homeshape=float((pure & (p.HOMESHAPE == 1)).sum() / max(int(pure.sum()), 1)),
        empty=int(empty.sum()), lt=int((empty & (a < F.HOME_LO)).sum()),
        gt=int((empty & (a > F.HOME_HI)).sum()),
        gt_mid=int((empty & (a > F.HOME_HI) & (a <= F.BIG)).sum()),
        gt_big=int((empty & (a > F.BIG)).sum()),
        not_compact=int((inr & (p.COMPACT < 0.6)).sum()),
        strip=int((inr & (p.COMPACT >= 0.6) & (p.ASPECT > 3)).sum()),
        homeshape=int((empty & (p.HOMESHAPE == 1)).sum()),
        cap=int((p.FUT_CAP == 1).sum()),
        med_cap_area=float(a[p.FUT_CAP == 1].median()),
        spread=int((p.SPREAD_W > 0).sum()),
        sliver_w=float(p.loc[(p.SPREAD_W > 0) & (a < F.HOME_LO), "SPREAD_W"].sum() / p.SPREAD_W.sum()),
    )


@lru_cache(None)
def _workbook_2100():
    """Settlement total of the Inception series in 2100 (sheet Workbook projection of the W14 growth workbook)."""
    import pandas as pd
    wp = pd.read_excel(os.path.join(F.ANA, "W14_growth_by_settlement.xlsx"), sheet_name="Workbook projection")
    wp = wp.set_index(wp.columns[0])
    return float(wp[2100].sum())


@lru_cache(None)
def _settlement_layer():
    import geopandas as gpd
    return gpd.read_file(os.path.join(F.SHP, "Settlements_merged.shp"), ignore_geometry=True).set_index("SETTLE")


# ================================================================ CHAPTER 3
def c03_occupancy(d):
    st = F.settlement_table(); by = _by(); ib = by["IBRI"]
    ps = F.plot_summary(); mc = F.meter_counts(); t = F.totals(); s = _plot_stats()
    small = [r for r in st if r["small"]]
    big = [r for r in st if r["workbook_2024"] >= 2000]
    cap_row = max(big, key=lambda r: r["workbook_2024"] / r["properties"])
    cap_or = cap_row["workbook_2024"] / cap_row["properties"]
    floored = [r for r in st if not r["small"] and r["or_raw"] < F.OR_FLOOR]
    above_cap = [r for r in st if r["workbook_2024"] / r["properties"] > cap_or]
    tay = by["AT TAYYIB"]; mia = by["MIAYRID"]; sam = by["SAYH AL MASARRAT"]; jah = by["AL JAHLI"]
    # lowest derived rate among the settlements whose derived rate is adopted as it stands (no floor, cap or small rule)
    # (or_raw is rounded to 2 dp in facts_w14, so compare within half that step)
    unbounded = [r for r in st if not r["small"] and abs(r["or_used"] - r["or_raw"]) <= 0.005]
    lo_unb = min(unbounded, key=lambda r: r["or_raw"])
    top_or = max(st, key=lambda r: r["or_raw"])
    small_lo = min(r["or_raw"] for r in small); small_hi = max(r["or_raw"] for r in small)
    wb_tot = sum(r["workbook_2024"] for r in st)
    diffs = [r["people_today"] - r["workbook_2024"] for r in st]
    up_ = [x for x in diffs if x > 0.5]; dn_ = [x for x in diffs if x < -0.5]

    D.h(d, 1, "3   Properties per plot and the occupancy rate", page_break=True)
    D.p(d, "This chapter turns the domestic electricity meters into people. It needs two numbers per "
           "settlement. The occupancy rate converts a property into persons, and it sets the population "
           "of 2024 on every built plot. The number of properties on a home plot is measured here too, "
           "although it is not used for today's population: the meters already count today's properties "
           "directly. It is used in Chapter 4, to say how many properties a future home plot will carry.")
    D.p(d, "Both numbers are set per settlement. T03 Revision 01 and Revision 1 of the concept report used "
           "one occupancy rate, 5.32, for the whole study area; the rate per settlement described here "
           "replaces it, and every population and flow in this tutorial follows from it.")

    # ------------------------------------------------------------ 3.1
    D.h(d, 2, "3.1   One domestic meter is one property")
    _lead(d, "What it is for", "A property is the unit the occupancy rate multiplies. Counting it from "
          "the meters gives the number of dwellings on every plot without assuming a plot typology.")
    _lead(d, "The rule", "Every meter on a domestic tariff is one property: the primary account, the "
          "primary account with the national subsidy, and the additional account. An additional account "
          "is a second dwelling on the same plot, so it counts as a property of its own. Shop, "
          "government, farm, industrial and large-consumer meters carry no people.")
    _lead(d, "Source", "The guideline accepts electricity accounts as the basis for distributing "
          "population below settlement scale (G201-p58, §7.2.1). Counting the domestic accounts as "
          "properties is the project's substitute for NCSI housing units, declared as a departure in "
          "Section 3.3.")
    _lead(d, "Worked for Ibri", f"Ibri holds {F.fmt(ib['properties'])} domestic properties. Over the "
          f"study area {F.fmt(mc['domestic'])} meters are domestic; {F.fmt(ps['properties'])} of them lie "
          f"on a plot or within 15 m of one and are carried in the plot table. The other "
          f"{F.fmt(mc['domestic'] - ps['properties'])} are among the {F.fmt(mc['free'])} meters that "
          f"lie further from any plot and carry no load.")
    _lead(d, "Where it lives", "W14/py/plots_meters_load.py assigns each meter to a plot; field G_DOM on "
          "W14/shp/PLOTS_load.shp is the count of domestic meters, and so of properties, on the plot. "
          "Column PROPS of W14/analysis/settlements_today.csv is its sum per settlement.")

    # ------------------------------------------------------------ 3.2
    D.h(d, 2, "3.2   Properties per home plot")
    _lead(d, "What it is for", "A future home plot has no meter yet. The number of properties it will "
          "carry is taken from the built home plots of the same settlement, so this ratio must be "
          "measured on plots that look like what a future home plot will become.")
    _lead(d, "The rule", "The ratio is measured per settlement on the pure home plots only: built plots "
          "whose use is Residential by the meter rule of Chapter 2 (more than two thirds of the meters "
          f"domestic) and that carry between 1 and {F.HIGH_METERS - 1} domestic meters.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("p"), UP("s")), M.EQ,
                       M.frac(M.nary("∑", UP("pure, s"), "", M.sub(R("N"), UP("dom")), hide_hi=True),
                              M.sub(R("n"), UP("pure, s")))), number=eq)
    _symbols(d, [
        ["p s", "properties per home plot in settlement s", "properties per plot"],
        ["N dom", "domestic meters on one pure home plot", "count"],
        ["n pure, s", "number of pure home plots in settlement s", "count"]])
    _lead(d, "Why the two exclusions", f"A plot with {F.HIGH_METERS} or more dwelling meters is a block "
          f"of flats or workers' housing, not a home plot. There are {F.fmt(s['high'])} such plots with "
          f"{F.fmt(s['high_dom'])} dwellings between them, enough to pull the ratio up in the settlement "
          f"that holds them. A plot that also carries shops, offices or a farm is counted for its people "
          f"but is not a template for a future home plot. Counting every built plot with a dwelling was "
          f"tried first and rejected: it gives Ibri {s['ib_any_dom'] / s['ib_any']:.2f} "
          f"({F.fmt(s['ib_any_dom'])} dwellings on {F.fmt(s['ib_any'])} plots) against the "
          f"{ib['ratio']:.2f} of the pure home plots.")
    _lead(d, "Source", "G201-p58, §7.2.2: population from plots uses the average number of properties "
          "per plot, taken from plots classified by clear typologies. The pure-home-plot definition and "
          "the 15-meter limit are a project rule (engineer, 2026-09-09).")
    _lead(d, "Worked for Ibri", f"{F.fmt(s['ib_pure_dom'])} domestic meters on {F.fmt(s['ib_pure'])} "
          f"pure home plots: {F.fmt(s['ib_pure_dom'])} ÷ {F.fmt(s['ib_pure'])} = {ib['ratio']:.2f} "
          f"properties per home plot. Over the whole study area, {F.fmt(s['pure_dom'])} meters on "
          f"{F.fmt(s['pure'])} pure home plots give {s['pure_dom'] / s['pure']:.2f}.")
    D.p(d, f"A settlement with fewer than ten pure home plots has no sample to speak of. Its derived "
           f"ratio is the study-area value, {s['pure_dom'] / s['pure']:.2f}, and its derived home share "
           f"(Chapter 4) the study-area value, {s['bh_pure'] / s['bh']:.2f}. Every settlement that falls "
           f"back in this way is under 1,000 people, so the rule of Section 3.5 replaces both values anyway.")
    D.tab_caption(d, "Properties per home plot by settlement, derived and adopted")
    rows = [[r["name"], F.fmt(r["properties"]), F.fmt(r["home_plots"]), f"{r['ratio_raw']:.2f}",
             f"{r['ratio']:.2f}" if not r["small"] else f"**{r['ratio']:.2f}**"] for r in st]
    D.table(d, ["Settlement", "Domestic properties", "Pure home plots measured", "Derived", "Adopted"],
            rows, widths=[4.2, 3.0, 3.4, 2.7, 2.7], font=8.5, align_right={1, 2, 3, 4})
    D.p(d, "Adopted values in bold are set by the rule for settlements under 1,000 people (Section 3.5).",
        size=9, italic=True, colour=D.GREY)
    _lead(d, "Where it lives", "W14/py/plot_class_v2_apply.py, mask pure and series ppp (constant HIGH = "
          "15, MIN_SAMPLE = 10). Columns PPP_RAW (derived), PROPS_PER_BUILT_PLOT (adopted) and "
          "DOM_PLOTS_BUILT (plots measured) in W14/analysis/settlements_today.csv; field PPP_S on every "
          "plot of PLOTS_load.shp.")

    # ------------------------------------------------------------ 3.3
    D.h(d, 2, "3.3   The occupancy rate")
    _lead(d, "What it is for", "The occupancy rate converts a property into persons. It is the one "
          "number that ties the meter count to the official population.")
    _lead(d, "The guideline's rule", "The guideline defines the rate as population over housing units, "
          "both from NCSI, from the most recent data and at the geographic scale of the project.")
    eq = D.next_eq()
    M.display(d, M.seq(UP("OR"), M.EQ, M.frac(UP("Population"), UP("Housing units"))), number=eq)
    _lead(d, "Source", "G201-p58, §7.2.2, for the equation; G201-p59 for the requirement that both "
          "terms come from NCSI at the scale of the project area.")
    D.callout(d, "A declared departure.",
              "NCSI publishes housing units at governorate and wilayat level only (G201-p59). A wilayat "
              "rate would put the same household size on Ibri town and on a village. The project "
              "therefore divides the population of each settlement by the domestic properties counted "
              "in it. The departure is listed in the concept report, Revision 2, Section 10.1, and "
              "needs NWS concurrence.")
    _lead(d, "The rule used", "For each settlement s, the 2024 population of the Inception Report series "
          "is divided by the domestic properties counted in the same settlement. 2024 is the year of "
          "the electricity accounts, so the two halves of the fraction describe the same year and the "
          "same ground.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(UP("OR"), UP("der, s")), M.EQ,
                       M.frac(M.sub(R("P"), UP("2024, s")), M.sub(R("N"), UP("dom, s")))), number=eq)
    _symbols(d, [
        ["OR der, s", "occupancy rate derived for settlement s", "persons per property"],
        ["P 2024, s", "population of settlement s in 2024, Inception Report series", "persons"],
        ["N dom, s", "domestic properties counted in settlement s (Section 3.1)", "properties"]])
    _lead(d, "Worked for Ibri", f"{F.fmt(ib['workbook_2024'])} ÷ {F.fmt(ib['properties'])} = "
          f"{ib['workbook_2024'] / ib['properties']:.2f} persons per property. Ibri needs neither the "
          f"floor nor the cap of Section 3.4, so the adopted rate is the derived one.")
    _lead(d, "Where it lives", "W14/py/plot_class_v2_apply.py, series or_raw: the workbook sheet Project "
          "Pop Settlements, column Pop 2024, over G_DOM summed per settlement. Columns WB_2024, PROPS and "
          "OR_RAW in settlements_today.csv; OR_raw in W14/analysis/occupancy_by_settlement.csv.")

    # ------------------------------------------------------------ 3.4
    D.h(d, 2, "3.4   The floor and the cap")
    _lead(d, "What it is for", "A derived rate can be wrong for reasons that have nothing to do with "
          "household size. The floor and the cap keep those errors out of the design.")
    _lead(d, "The rule", f"The derived rate is bounded below by {F.OR_FLOOR:.1f} and above by the "
          f"highest rate derived in any settlement of 2,000 people or more.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(UP("OR"), UP("s")), M.EQ,
                       M.func("min", M.delim(M.seq(M.func("max", M.delim(M.seq(M.sub(UP("OR"), UP("der, s")),
                                                                                 R(", "), R(f"{F.OR_FLOOR:.1f}")))),
                                                   R(", "), M.sub(UP("OR"), UP("cap")))))), number=eq)
    eq2 = D.next_eq()
    M.display(d, M.seq(M.sub(UP("OR"), UP("cap")), M.EQ,
                       M.sub(UP("max"), UP("s: P ≥ 2,000")), R(" "), M.sub(UP("OR"), UP("der, s"))), number=eq2)
    _symbols(d, [
        ["OR s", "occupancy rate adopted for settlement s", "persons per property"],
        ["OR cap", "highest derived rate among the settlements of 2,000 people or more", "persons per property"]])
    _lead(d, "Why the floor", "In some settlements the domestic meters include the housing of the police "
          "headquarters, the college and similar institutions. Their occupants are not census residents, "
          "so the census population is small against the meters and the derived rate falls to between "
          "one and four. Those dwellings discharge to the sewer whatever the census says. The floor keeps "
          f"them in the design. Its value, {F.OR_FLOOR:.1f}, is {lo_unb['name']}'s measured "
          f"{lo_unb['or_raw']:.2f} at {F.fmt(lo_unb['workbook_2024'])} people, the lowest rate measured "
          "in any settlement whose derived rate is used without a bound.")
    _lead(d, "Why the cap", f"A rate above the highest one measured on a large sample says that too few "
          f"meters were found for the census count, not that households are larger. {top_or['name']} is "
          f"the extreme case: {F.fmt(top_or['workbook_2024'])} people on {F.fmt(top_or['properties'])} "
          f"meters give {top_or['or_raw']:.2f}; {mia['name']}'s {F.fmt(mia['workbook_2024'])} people on "
          f"{F.fmt(mia['properties'])} meters give {mia['or_raw']:.2f}. The cap is "
          f"{cap_row['name']}'s {cap_or:.2f}.")
    _lead(d, "What they change", "The floor lifts " + " and ".join(
          f"{r['name']} ({r['or_raw']:.2f})" for r in floored) + f" to {F.OR_FLOOR:.1f}. The settlements "
          "above the cap, " + ", ".join(f"{r['name']} ({r['or_raw']:.2f})" for r in above_cap) +
          ", are all under 1,000 people and take the rule of Section 3.5 instead. No settlement of "
          "1,000 people or more is cut by the cap.")
    _lead(d, "Source", "Project rule (engineer, 2026-09-10). The guideline gives no bound on the rate.")
    _lead(d, "Where it lives", "plot_class_v2_apply.py: OR_FLOOR = 4.0, OR_CEIL computed from or_raw over "
          "the settlements with a 2024 population of 2,000 or more, or_s = or_raw.clip(OR_FLOOR, OR_CEIL). "
          "Column rule in occupancy_by_settlement.csv names the bound that applied.")

    # ------------------------------------------------------------ 3.5
    D.h(d, 2, "3.5   Settlements under 1,000 people")
    _lead(d, "What it is for", "A small settlement has too few meters to measure any of its three rates "
          "on. One rule sets all three for it.")
    _lead(d, "The rule", f"A settlement with fewer than 1,000 people in 2024 takes an occupancy of "
          f"{F.OR_FLOOR:.1f}, one property per home plot and a home share of 0.9, whatever its meters "
          "return.")
    _lead(d, "Why", "There are two reasons. The meters return rates on a handful of accounts that swing "
          f"from {small_lo:.2f} to {small_hi:.2f}. And a village of that size does not attract second "
          "dwellings on a plot, so one property per plot describes its future homes better than a ratio "
          f"measured on a dozen plots. The occupancy of {F.OR_FLOOR:.1f} is the floor of Section 3.4. The home share of "
          "0.9 lies within the range measured in the settlements of 1,000 people or more (Chapter 4).")
    _lead(d, "Which settlements", f"The rule applies to {len(small)} settlements: "
          + ", ".join(r["name"] for r in small) + f". {sam['name']} and {jah['name']} are among them "
          f"although their meters say {F.fmt(sam['properties'])} and {F.fmt(jah['properties'])} "
          f"properties: the census counts {F.fmt(sam['workbook_2024'])} and "
          f"{F.fmt(jah['workbook_2024'])} residents there, because the police headquarters housing and "
          f"the college housing are not census residents. Their derived rates, {sam['or_raw']:.2f} and "
          f"{jah['or_raw']:.2f}, would have been floored to {F.OR_FLOOR:.1f} in any case.")
    _lead(d, "Source", "Project rule (engineer, 2026-09-10).")
    _lead(d, "Where it lives", "plot_class_v2_apply.py, SMALL_POP = 1000 and the series small; column "
          "SMALL in settlements_today.csv; the derived values stay beside the adopted ones in the columns "
          "OR_RAW, PPP_RAW and HOME_SHARE_RAW.")

    # ------------------------------------------------------------ 3.6
    D.h(d, 2, "3.6   The population in 2024")
    _lead(d, "The rule", "The people on a built plot are its domestic properties times the adopted "
          "occupancy of its settlement. The settlement population is the sum over its plots.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("P"), UP("plot")), M.EQ, M.sub(R("N"), UP("dom")), M.TIMES,
                       M.sub(UP("OR"), UP("s"))), number=eq)
    _lead(d, "Worked for Ibri", f"A plot with four domestic meters in Ibri carries 4 × "
          f"{ib['or_used']:.2f} = {F.fmt(4 * ib['or_used'], 1)} people. Ibri as a whole carries "
          f"{F.fmt(ib['properties'])} × {ib['or_used']:.4f} = {F.fmt(ib['people_today'])} people, the "
          "census figure, because no bound applies to it.")
    D.tab_caption(d, "Occupancy rate by settlement: derived, adopted, and the people it gives in 2024")
    occ = F.occupancy()
    rule_txt = lambda k: ("derived" if occ.at[k, "rule"] == "derived" else
                          "floor" if str(occ.at[k, "rule"]).startswith("floor") else
                          "cap" if str(occ.at[k, "rule"]).startswith("cap") else "under 1,000")
    rows = [[r["name"], F.fmt(r["properties"]), F.fmt(r["workbook_2024"]), f"{r['or_raw']:.2f}",
             f"{r['or_used']:.2f}", rule_txt(r["key"]), F.fmt(r["people_today"]),
             _signed(r["people_today"] - r["workbook_2024"])] for r in st]
    rows.append(["**Total**", f"**{F.fmt(ps['properties'])}**", f"**{F.fmt(wb_tot)}**",
                 f"**{F.census_rate():.2f}**", f"**{t['pop_today'] / ps['properties']:.2f}**", "",
                 f"**{F.fmt(t['pop_today'])}**", f"**{_signed(t['pop_today'] - wb_tot)}**"])
    D.table(d, ["Settlement", "Domestic properties", "Census 2024", "Rate derived", "Rate adopted", "Rule",
                "People 2024", "Difference"], rows,
            widths=[3.2, 1.9, 2.0, 1.6, 1.6, 2.0, 2.0, 1.9], font=8, align_right={1, 2, 3, 4, 6, 7})
    D.p(d, "In the total row the derived rate is the census population over all properties and the "
           "adopted rate is the design population over all properties.", size=9, italic=True, colour=D.GREY)
    _lead(d, "What the bounds cost", f"The floor and the small-settlement rule put {F.fmt(sum(up_))} "
          f"people above the census in {len(up_)} settlements and {F.fmt(-sum(dn_))} below it in "
          f"{len(dn_)} of the smallest, which the rule brings down to {F.OR_FLOOR:.1f}. The net is "
          f"{F.fmt(t['pop_today'] - wb_tot)} above the {F.fmt(wb_tot)} of the census series, giving "
          f"{F.fmt(t['pop_today'])} people in 2024. The census over the properties of the study area "
          f"gives {F.census_rate():.2f} persons per property; the design population gives "
          f"{t['pop_today'] / ps['properties']:.2f}. The meters flush whether the census counts their "
          "occupants or not, so the design keeps the higher figure.")
    _fig(d, "C02_occupancy.png", 15.0,
         "Occupancy by settlement: the rate derived from the 2024 population and the domestic "
         "properties, and the rate adopted after the floor of 4.0, the cap and the rule for settlements "
         "under 1,000 people.")
    _lead(d, "Where it lives", "Field OR_S (the adopted rate, four decimals) and field POP (people in "
          "2024, = G_DOM × OR_S) on PLOTS_load.shp; columns OR_S and POP_TODAY in settlements_today.csv; "
          "the full table with the rule in occupancy_by_settlement.csv, read by facts_w14.settlement_table() "
          "and facts_w14.occupancy().")

    # ------------------------------------------------------------ check
    D.h(d, 2, "3.7   Check it yourself")
    D.numbered(d, f"In settlements_today.csv, divide WB_2024 by PROPS for Ibri. The answer, "
                  f"{ib['workbook_2024'] / ib['properties']:.4f}, must equal OR_S.", restart=True)
    D.numbered(d, f"In QGIS, select on PLOTS_load.shp: Buiding_St = 'EXisting' and DERIVED = 'Residential' "
                  f"and G_DOM between 1 and {F.HIGH_METERS - 1} and SETTLE = 'IBRI'. The selection holds "
                  f"{F.fmt(s['ib_pure'])} plots and sums to {F.fmt(s['ib_pure_dom'])} domestic meters.")
    D.numbered(d, f"Sum POP over the plots of any settlement; it must equal POP_TODAY. The sum over all "
                  f"plots is {F.fmt(t['pop_today'])}.")
    D.numbered(d, "In occupancy_by_settlement.csv, every row whose rule is not 'derived' must be a "
                  f"settlement under 1,000 people or one whose OR_raw is below {F.OR_FLOOR:.1f}.")
    D.numbered(d, "Recompute OR_CEIL: the largest OR_RAW among the rows of settlements_today.csv with "
                  f"WB_2024 of 2,000 or more. It is {cap_row['name']}'s {cap_or:.4f}.")


# ================================================================ CHAPTER 4
def c04_capacity(d):
    st = F.settlement_table(); by = _by(); ib = by["IBRI"]
    ps = F.plot_summary(); t = F.totals(); s = _plot_stats()
    hs = F.home_share_range()
    n = ib["cap_plots"]; h = ib["home_share"]; pr = ib["ratio"]; orr = ib["or_used"]
    props = round(n * pr * h); cap_ib = round(props * orr)
    tay = by["AT TAYYIB"]

    D.h(d, 1, "4   The empty land and its capacity", page_break=True)
    D.p(d, f"Of the {F.fmt(ps['total'])} plots in the cadastre, {F.fmt(ps['empty'])} carry no meter. "
           "This chapter sets how many people that empty land can hold when it is fully built. The "
           "answer is the capacity of each settlement, and it is the ceiling that Chapter 5 fills with "
           "growth. It rests on three measurements taken from the built plots of the same settlement: "
           "what a home plot looks like, what share of such plots are homes, and how many properties a "
           "home plot carries (Section 3.2). The occupancy of Section 3.4 turns properties into people.")

    # ------------------------------------------------------------ 4.1
    D.h(d, 2, "4.1   Which empty plots become homes")
    _lead(d, "What it is for", "Not every empty plot will carry a house. A sliver, a strip along a road, "
          "a grove or a plot the size of a district will not. The test picks the plots that look like "
          "the built home plots.")
    _lead(d, "The rule", f"An empty plot is counted as a future home plot when all of the following "
          f"hold: its area is between {F.fmt(F.HOME_LO)} and {F.fmt(F.HOME_HI)} m²; it is compact, meaning "
          "its area is at least 0.6 of the area of its smallest enclosing rotated rectangle; it is not a "
          "strip, meaning that rectangle's long side is no more than three times its short side; and its "
          "use by the rules of Chapter 2 is not grove, industrial or heritage, and it lies outside the two "
          "industrial estates.")
    _lead(d, "Why these bounds", f"The pure home plots of Section 3.2 have a median area of "
          f"{F.fmt(s['med_area'])} m², a median compactness of {s['med_compact']:.2f} and a median aspect "
          f"of {s['med_aspect']:.2f}. The test is stricter than the built stock: only "
          f"{_pct(s['pure_homeshape'], 0)} per cent of today's home plots would pass it. The capacity it "
          f"gives therefore errs towards fewer homes, not more. A plot above {F.fmt(F.BIG)} m² is a future "
          "district drawn as one parcel and takes nothing until it is subdivided.")
    D.tab_caption(d, "From empty plots to counted future home plots, the study area")
    D.table(d, ["Test", "Plots removed", "Plots left"], [
        ["Empty plots in the cadastre", "", F.fmt(s["empty"])],
        [f"Smaller than {F.fmt(F.HOME_LO)} m² (slivers)", F.fmt(s["lt"]), F.fmt(s["empty"] - s["lt"])],
        [f"Larger than {F.fmt(F.HOME_HI)} m² ({F.fmt(s['gt_mid'])} up to {F.fmt(F.BIG)} m², "
         f"{F.fmt(s['gt_big'])} above)", F.fmt(s["gt"]), F.fmt(s["empty"] - s["lt"] - s["gt"])],
        ["Not compact (below 0.6)", F.fmt(s["not_compact"]),
         F.fmt(s["empty"] - s["lt"] - s["gt"] - s["not_compact"])],
        ["A strip (aspect above 3)", F.fmt(s["strip"]), F.fmt(s["homeshape"])],
        ["Grove, industrial, heritage or in an estate", F.fmt(s["homeshape"] - s["cap"]), f"**{F.fmt(s['cap'])}**"],
    ], widths=[9.6, 3.2, 3.2], font=9, align_right={1, 2})
    D.p(d, "", space_after=2)
    _lead(d, "Source", "Project rule (engineer, 2026-09-10). The guideline asks for population from plots "
          "classified by clear typologies and warns that plot subdivision must be reflected in the "
          "housing units created (G201-p58, §7.2.2, and the NOTE at G201-p59). The shape test is the "
          "typology; the exclusion of plots above 2,000 m² is the subdivision caution.")
    _lead(d, "Worked for Ibri", f"Ibri has {F.fmt(ib['empty_plots'])} empty plots, of which {F.fmt(n)} "
          f"pass the test. Across the study area the median counted plot is "
          f"{F.fmt(s['med_cap_area'])} m².")
    _lead(d, "Where it lives", "W14/py/plot_class_v2_apply.py: fields COMPACT (area over the area of "
          "minimum_rotated_rectangle), ASPECT (long over short side of that rectangle), HOMESHAPE "
          "(1 = size and shape pass) and FUT_CAP (1 = counted: empty, home-shaped and not excluded) on "
          "PLOTS_load.shp; column FUT_CAP_PLOTS in settlements_today.csv.")

    # ------------------------------------------------------------ 4.2
    D.h(d, 2, "4.2   The home share")
    _lead(d, "What it is for", "A district needs mosques, shops and offices as well as houses, so not "
          "every home-shaped plot becomes a home. The home share is the fraction that does, measured "
          "where the district already exists.")
    _lead(d, "The rule", "For each settlement, among its built plots that carry a meter and pass the "
          "size and shape test of Section 4.1, the home share is the number that are pure home plots "
          "(Section 3.2) divided by all of them.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("h"), UP("s")), M.EQ,
                       # U+2011 non-breaking hyphen: a plain '-' in a math run is set as a minus sign
                       M.frac(M.sub(R("n"), UP("pure, home‑shaped, s")),
                              M.sub(R("n"), UP("built, metered, home‑shaped, s")))),
              number=eq)
    _symbols(d, [
        ["h s", "home share of settlement s", "—"],
        ["n pure, home-shaped, s", "built, metered, home-shaped plots that are pure home plots", "count"],
        ["n built, metered, home-shaped, s", "all built, metered, home-shaped plots", "count"]])
    _lead(d, "Worked for Ibri", f"{F.fmt(s['ib_bh_pure'])} ÷ {F.fmt(s['ib_bh'])} = "
          f"{s['ib_bh_pure'] / s['ib_bh']:.3f}. Among the settlements of 1,000 people or more the measured "
          f"share runs from {hs[0]:.2f} in {hs[1]}, with its workshops, to {hs[2]:.2f} in {hs[3]}. "
          f"The settlements under 1,000 people take 0.9 (Section 3.5).")
    _lead(d, "Source", "Project rule (engineer, 2026-09-10). It is the coverage by land-use typology that "
          "the NOTE at G201-p59 asks for.")
    _lead(d, "Where it lives", "plot_class_v2_apply.py, masks bh and pure and the series home_share; "
          "columns HOME_SHARE_RAW (derived) and HOME_SHARE (adopted) in settlements_today.csv; field "
          "HOMESH_S on every plot.")

    # ------------------------------------------------------------ 4.3
    D.h(d, 2, "4.3   The capacity equation")
    _lead(d, "What it is for", "The capacity is the number of people the empty land of a settlement can "
          "hold when every counted plot is built. It is the ceiling of that settlement's growth.")
    _lead(d, "The rule", "The counted plots, times the home share, give the future home plots. Times the "
          "properties per home plot, they give the future properties. Times the occupancy, they give the "
          "people.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("C"), UP("s")), M.EQ, M.sub(R("N"), UP("hs, s")), M.TIMES,
                       M.sub(R("h"), UP("s")), M.TIMES, M.sub(R("p"), UP("s")), M.TIMES,
                       M.sub(UP("OR"), UP("s"))), number=eq)
    _symbols(d, [
        ["C s", "capacity of the empty land of settlement s", "persons"],
        ["N hs, s", "empty plots counted as future home plots (Section 4.1)", "count"],
        ["h s", "home share (Section 4.2), adopted value", "—"],
        ["p s", "properties per home plot (Section 3.2), adopted value", "properties per plot"],
        ["OR s", "occupancy rate (Section 3.4), adopted value", "persons per property"]])
    _lead(d, "Source", "It is the guideline's equation, population equals number of plots times average "
          "properties per plot times occupancy rate (G201-p58, §7.2.2), with the home share as the "
          "typology factor. It gives the build-out ceiling only. The NOTE at G201-p59 requires "
          "development to be phased, not assumed simultaneous; Chapter 5 does that.")
    _lead(d, "Worked for Ibri", f"{F.fmt(n)} counted plots × {h:.3f} × {pr:.2f} = {F.fmt(props)} future "
          f"properties. {F.fmt(props)} × {orr:.4f} = {F.fmt(cap_ib)} people. The occupancy is carried to "
          f"four decimals in the calculation; it prints as {orr:.2f}. The properties are rounded to whole "
          f"numbers before the occupancy is applied, as the script does.")
    _lead(d, "Where it lives", "plot_class_v2_apply.py: FUT_CAP_PROPS = round(FUT_CAP_PLOTS × "
          "PROPS_PER_BUILT_PLOT × HOME_SHARE) and FUT_CAP_POP = round(FUT_CAP_PROPS × OR_S) in "
          "settlements_today.csv; FUT_PROPS on each counted plot is its expected properties, p × h.")

    # ------------------------------------------------------------ 4.4
    D.h(d, 2, "4.4   Capacity by settlement")
    D.tab_caption(d, "Capacity of the empty land by settlement")
    rows = [[r["name"], F.fmt(r["empty_plots"]), F.fmt(r["cap_plots"]), f"{r['home_share_raw']:.2f}",
             f"{r['home_share']:.2f}", f"{r['ratio']:.2f}", f"{r['or_used']:.2f}", F.fmt(r["cap_people"]),
             F.fmt(r["people_today"]), F.fmt(r["people_today"] + r["cap_people"])] for r in st]
    rows.append(["**Total**", f"**{F.fmt(sum(r['empty_plots'] for r in st))}**",
                 f"**{F.fmt(sum(r['cap_plots'] for r in st))}**", "", "", "", "",
                 f"**{F.fmt(t['capacity'])}**", f"**{F.fmt(t['pop_today'])}**",
                 f"**{F.fmt(t['pop_today'] + t['capacity'])}**"])
    D.table(d, ["Settlement", "Empty plots", "Counted", "Home share derived", "Home share adopted",
                "Props per plot", "Occu-pancy", "Capacity, people", "People 2024", "Full, people"],
            rows, widths=[2.8, 1.5, 1.5, 1.4, 1.4, 1.3, 1.3, 1.7, 1.6, 1.7], font=7.5,
            align_right=set(range(1, 10)))
    D.p(d, "Full, people = people in 2024 + capacity: the population of the settlement in its "
           "saturation year.", size=9, italic=True, colour=D.GREY)
    D.p(d, f"The empty land of the study area holds {F.fmt(t['capacity'])} people, against "
           f"{F.fmt(t['pop_today'])} living in it in 2024. When every counted plot is built the study area "
           f"holds {F.fmt(t['pop_today'] + t['capacity'])} people. That is the saturation population of "
           "Chapter 5, and it follows from the land alone. The growth series only says when it is reached.")
    D.p(d, f"The table also shows why the next chapter needs an overflow rule. At Tayyib has room for "
           f"{F.fmt(tay['cap_people'])} people against {F.fmt(tay['people_today'])} living there, far more "
           f"than its own growth will ever fill. Ibri's capacity of {F.fmt(ib['cap_people'])} is about "
           f"{ib['cap_people'] / ib['people_today']:.1f} times its 2024 population. It fills in "
           f"{ib['sat_year']}, and from then on the growth of the largest settlement in the study area "
           "has to be housed on its neighbours' land.")

    # ------------------------------------------------------------ check
    D.h(d, 2, "4.5   Check it yourself")
    D.numbered(d, f"Select on PLOTS_load.shp: Buiding_St = 'Future' and FUT_CAP = 1 and SETTLE = 'IBRI'. "
                  f"The selection holds {F.fmt(n)} plots.", restart=True)
    D.numbered(d, f"Select Buiding_St = 'EXisting' and HOMESHAPE = 1 and N_ACC > 0 and SETTLE = 'IBRI': "
                  f"{F.fmt(s['ib_bh'])} plots. Of these, DERIVED = 'Residential' and G_DOM between 1 and "
                  f"{F.HIGH_METERS - 1}: {F.fmt(s['ib_bh_pure'])}. The ratio is Ibri's home share.")
    D.numbered(d, "Open any counted plot and check its COMPACT against the area of its oriented minimum "
                  "bounding box (QGIS: Processing, Oriented minimum bounding box).")
    D.numbered(d, "In settlements_today.csv recompute FUT_CAP_POP from FUT_CAP_PLOTS, "
                  "PROPS_PER_BUILT_PLOT, HOME_SHARE and OR_S for three settlements; the column sums to "
                  f"{F.fmt(t['capacity'])}.")
    D.numbered(d, "The sum of FUT_PROPS over a settlement's plots equals FUT_CAP_PROPS within rounding.")


# ================================================================ CHAPTER 5
def c05_growth(d):
    st = F.settlement_table(); by = _by(); ib = by["IBRI"]
    t = F.totals(); gr = F.growth_rates(); s = _plot_stats()
    g = F.growth(); pop = g["Population by year"]
    S = _settlement_layer()
    ult = t["ultimate"]
    p0 = ib["people_today"]; cap_ib = ib["cap_people"]
    f30 = float(pop.at["IBRI", 2030]) / p0
    tot30 = t["pop"][2030] / t["pop_today"]
    h30 = float(pop.at["IBRI", 2030]) - p0; h55 = float(pop.at["IBRI", 2055]) - p0
    sat = {r["key"]: r["sat_year"] for r in st}
    first_fill = min(r for r in sat.values() if r)
    first_name = next(by[k]["name"] for k, v in sat.items() if v == first_fill)
    own = F.own_growth_saturation(); own_by = {r["key"]: r for r in own}
    never = [r["name"] for r in own if r["own"] is None]
    rcv_all = F.ibri_receivers(0); rcv_big = F.ibri_receivers()
    ar = next(r for r in rcv_all if r["receiver"] == "AL ARAQI")
    top = rcv_all[0]
    stage1 = {r["receiver"]: r for r in rcv_all if r["receiver"] in ("AL QURAYN", "SHALASHIL", "AD DARIZ")}
    out_ib = float(S.at["IBRI", "OUT_PEOPLE"])
    housed50 = t["pop"][2050] - t["pop_today"]
    after50 = sum(1 for v in sat.values() if v and v > 2050)
    wsum = float(F.settlements().at["IBRI", "SPREAD_W_SUM"]); nspread = int(F.settlements().at["IBRI", "SPREAD_PLOTS"])
    wb2100 = _workbook_2100()

    D.h(d, 1, "5   Growth, overflow and saturation", page_break=True)
    D.p(d, "Chapter 3 put people on the built plots of 2024 and Chapter 4 set how many more the empty "
           "land of each settlement can hold. This chapter fills that land year by year. It answers three "
           "questions: how fast each settlement grows, where its growth goes once its own land is full, "
           "and in which year the study area is full, which is the saturation the design is sized for. "
           "The last step places the people housed in each year on the individual empty plots, so that "
           "the network sees a load on every plot it passes.")
    _fig(d, "D7_saturation.png", 12.5, "From the empty plot to the saturation year: the three rates of "
         "Chapters 3 and 4 set the capacity, the growth rate fills it, the overflow moves what a full "
         "settlement cannot house, and the housed people are spread over the plots.")

    # ------------------------------------------------------------ 5.1
    D.h(d, 2, "5.1   The growth series")
    _lead(d, "What it is for", "The growth series says how fast each settlement's population grows. It "
          "is used for its rate only; the starting population is the counted one of Chapter 3.")
    _lead(d, "The series", "The population series of the Inception Report is built in three parts. The "
          "wilayat total is then split between the settlements in fixed shares from the census, so every "
          "settlement carries the same annual rate in every year.")
    D.tab_caption(d, "The three parts of the growth series and the mean annual rate")
    D.table(d, ["Part", "Years", "Basis", "Mean rate, % a year"], [
        ["1", "2024 to 2040", "NCSI forecast for the Wilayat of Ibri, Omani and expatriate population "
                              "separately", f"{F.fmt(gr['d2024_2030'], 2)} (2024 to 2030); "
                                            f"{F.fmt(gr['d2030s'], 2)} (2030s)"],
        ["2", "2041 to 2050", "Extrapolation of the NCSI forecast, documented in the technical note on "
                              "population issued with the Inception Report", f"{F.fmt(gr['d2040s'], 2)} (2040s)"],
        ["3", "2051 to 2100", f"Rising from {F.fmt(gr['r2051'], 2)} in 2051 to {F.fmt(gr['d2060on'], 2)} "
                              f"by {gr['year_240']}, "
                              f"then constant to 2100, the planning horizon instructed by NWS",
         f"{F.fmt(gr['d2050s'], 2)} (2050s); {F.fmt(gr['d2060on'], 2)} (2060 on)"],
    ], widths=[1.2, 2.6, 8.6, 4.2], font=8.5)
    D.p(d, "", space_after=2)
    _fig(d, "C12_growth_rate.png", 15.5, "The annual growth rate of the population series by year: the "
         f"census forecast to 2040, the extrapolation to 2050, and the rise to a constant "
         f"{F.fmt(gr['d2060on'], 2)} per cent.")
    _lead(d, "The rule", "Each settlement's growth factor is its workbook population in year y over its "
          "workbook population in 2024. The new people who want a home in the settlement by year y are "
          "its counted 2024 population times that factor, less the 2024 population.")
    eq = D.next_eq()
    M.display(d, M.seq(R("g"), M.delim(R("y")), M.EQ,
                       M.frac(M.sub(R("P"), UP("wb, s")) + M.delim(R("y")),
                              M.sub(R("P"), UP("wb, s")) + M.delim(UP("2024")))), number=eq)
    eq2 = D.next_eq()
    M.display(d, M.seq(M.sub(R("D"), UP("s")), M.delim(R("y")), M.EQ, M.sub(R("P"), UP("2024, s")), M.TIMES,
                       M.delim(M.seq(R("g"), M.delim(R("y")), M.MINUS, UP("1")))), number=eq2)
    _symbols(d, [
        ["g(y)", "growth factor from 2024 to year y, the same for every settlement", "—"],
        ["P wb, s (y)", "population of settlement s in year y, Inception Report series", "persons"],
        ["P 2024, s", "counted population of settlement s in 2024 (Section 3.6)", "persons"],
        ["D s (y)", "new people wanting a home in settlement s by year y", "persons"]])
    _lead(d, "Worked for Ibri", f"The factor to 2030 is {f30:.4f}; for the study-area total it is "
          f"{tot30:.4f}, the same, because the shares are fixed. Ibri's growth to 2030 is "
          f"{F.fmt(p0)} × ({f30:.4f} − 1) = {F.fmt(h30)} people.")
    _lead(d, "Source", "Inception Report Revision 0, Section 6, and its demand workbook, sheet Project Pop "
          "Settlements. The split in census shares is the guideline's rule for a forecast held only at "
          "wilayat level (G201-p58, §7.2.1).")
    _lead(d, "Where it lives", "W14/py/growth_by_settlement.py: P (the workbook sheet), growth = P / "
          "P[2024], demand = pop0 × (growth − 1). The rates are printed by facts_w14.growth_rates().")

    # ------------------------------------------------------------ 5.2
    D.h(d, 2, "5.2   The ten-year limit, and why saturation rests on the land")
    _lead(d, "The rule", "NCSI forecasts cover 20 to 25 years. Beyond them the guideline permits a "
          "regression, but states that it is \"not recommended to extrapolate more than ten years beyond "
          "the available forecast period\".")
    _lead(d, "Source", "G201-p58, §7.2.1, time scale.")
    _lead(d, "What it means here", f"The NCSI forecast ends in 2040, so the limit falls in 2050, which is "
          f"exactly where part 2 of the series stops. Everything after 2050 is outside it. By 2050 the "
          f"growth has housed {F.fmt(housed50)} people, {_pct(housed50 / t['capacity'], 0)} per cent of the "
          f"capacity; {after50} of the 25 settlements fill after 2050, and the study area fills in {ult}.")
    D.callout(d, "The curve dates saturation; it does not size it.",
              f"The population at saturation is the 2024 population plus the capacity: "
              f"{F.fmt(t['pop_today'])} + {F.fmt(t['capacity'])} = {F.fmt(t['pop_ult'])}. That sum does not "
              f"depend on the growth curve. A faster curve brings {ult} forward and a slower one pushes it "
              f"back; neither changes the {F.fmt(t['pop_ult'])} people or the {F.fmt(t['q_ult'])} m³/d. "
              f"Left to run, the series itself would reach {F.fmt(wb2100)} people in the 25 settlements by "
              f"2100, which the land cannot hold. It is not a target and not a saturation figure.",
              fill="EAF1F8", colour=D.MID)
    D.p(d, f"This is why the two flow cases of the network design rest on firm ground. Pipes are sized on "
           f"the saturation flow, which comes from the land. Self-cleansing is checked on the 2030 flow, "
           f"which lies inside the NCSI forecast. The 2055 model year, {F.fmt(t['pop'][2055])} people, "
           f"lies on the extrapolated part of the curve: quote it as a dated estimate, not as data. The "
           f"concept report records the use of the series beyond 2050 as a departure (Revision 2, "
           f"Section 10.1).")
    _lead(d, "Where it lives", "The two flow cases are the project rule of 2026-09-11 (engineer), taught in "
          "Chapters 11 and 12. The saturation population is column SAT_POP of W14/shp/Settlements_merged.shp "
          "and field POP_ULT on every plot.")

    # ------------------------------------------------------------ 5.3
    D.h(d, 2, "5.3   Filling the land in proportion")
    _lead(d, "What it is for", "A settlement's new people have to be housed somewhere on its land. The "
          "rule says how, and it sets the year the settlement is full.")
    _lead(d, "The rule", "A settlement's growth fills all its counted plots together and in proportion, "
          "not plot by plot. Its fill fraction in year y is the people it has housed since 2024 over its "
          "capacity. The settlement is full, and that year is its saturation year, when the housed people "
          "reach the capacity. Growth it cannot house from then on is overflow (Section 5.4).")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("f"), UP("s")), M.delim(R("y")), M.EQ,
                       M.frac(M.sub(R("H"), UP("s")) + M.delim(R("y")), M.sub(R("C"), UP("s"))),
                       R(" ≤ 1,   "), M.sub(R("P"), UP("s")), M.delim(R("y")), M.EQ,
                       M.sub(R("P"), UP("2024, s")), M.PLUS, M.sub(R("H"), UP("s")), M.delim(R("y"))),
              number=eq)
    _symbols(d, [
        ["f s (y)", "fill fraction of settlement s in year y", "—"],
        ["H s (y)", "new people housed in s since 2024, its own growth plus what it received", "persons"],
        ["C s", "capacity of settlement s (Section 4.3)", "persons"],
        ["P s (y)", "population of settlement s in year y", "persons"]])
    _lead(d, "Worked for Ibri", f"In 2030 Ibri has housed {F.fmt(h30)} people, {_pct(h30 / cap_ib)} per cent "
          f"of its capacity of {F.fmt(cap_ib)}. In 2055 it has housed {F.fmt(h55)}, "
          f"{_pct(h55 / cap_ib)} per cent. It is full in {ib['sat_year']}, with {F.fmt(p0 + cap_ib)} people; "
          "from then on its population stays there and its growth goes elsewhere.")
    _lead(d, "Source", "Project rule (engineer, 2026-09-10). The gradual fill is the phasing that the "
          "NOTE at G201-p59 requires in place of a simultaneous build-out.")
    _lead(d, "Where it lives", "growth_by_settlement.py, the year loop: own_c (housed from own growth), "
          "in_c (received), sat_year; sheets Population by year, Housed own growth, Inflow from overflow "
          "and Fill fraction of W14/analysis/W14_growth_by_settlement.xlsx.")

    # ------------------------------------------------------------ 5.4
    D.h(d, 2, "5.4   The overflow rules")
    _lead(d, "What it is for", "A full settlement's growth does not stop; it moves to land that is still "
          "empty. The rules say where it goes, in which order.")
    _lead(d, "The rule", "Each year, the largest settlements are served first, and each settlement's "
          "growth is housed in this order.")
    D.numbered(d, "In its own counted plots, while it has room.", restart=True)
    D.numbered(d, "Ibri's overflow goes in parallel to Al Araqi, Al Qurayn and Shalashil, in shares of "
                  "70, 20 and 10 per cent. When one of the three is full, its share is offered again to "
                  "the others of the same group.")
    D.numbered(d, "When those three are full, Ibri's overflow goes to Ad Dariz.")
    D.numbered(d, "At Tayyib's overflow goes first to Miayrid, the small settlement beside it.")
    D.numbered(d, "After its named receivers, and for every other settlement from the start, the overflow "
                  "goes to the nearest settlement with room, by distance between the settlement "
                  "centroids, then the next nearest.")
    D.numbered(d, "Every settlement receives, whatever its size. A receiver's own growth continues "
                  "alongside what it receives, and both count against its capacity.")
    _lead(d, "Why", "The parallel routes out of Ibri reflect local knowledge of where Ibri's growth is "
          "going. The nearest-with-room rule stands for everything else. Letting every settlement receive "
          "is what lets all 25 fill; with a minimum receiver size the small settlements with large empty "
          "land would never fill (Section 5.7).")
    _lead(d, "Source", "Project rule (engineer, 2026-09-10), from a person who knows the area.")
    _lead(d, "Where it lives", "growth_by_settlement.py: SPILL = {'IBRI': [[AL ARAQI 0.7, AL QURAYN 0.2, "
          "SHALASHIL 0.1], [AD DARIZ 1.0]], 'AT TAYYIB': [[MIAYRID 1.0]]}, RECEIVER_MIN_POP = 0, the "
          "receivers sorted by centroid distance in order[s]; sheet Overflow routes of the growth "
          "workbook.")

    # ------------------------------------------------------------ 5.5
    D.h(d, 2, "5.5   What the rules produce")
    D.p(d, f"The rule sets the order; the land sets the result. Al Araqi fills in {sat['AL ARAQI']}, a year "
           f"after Ibri, so it takes only {F.fmt(ar['people'])} of Ibri's people. Its share passes to the "
           f"other two of the group: Shalashil takes {F.fmt(stage1['SHALASHIL']['people'])} and Al Qurayn "
           f"{F.fmt(stage1['AL QURAYN']['people'])} before they fill in {sat['SHALASHIL']} and "
           f"{sat['AL QURAYN']}. Ad Dariz, next in line, is filling with its own growth and takes "
           f"{F.fmt(stage1['AD DARIZ']['people'])}. The rest goes by distance, and the largest single route "
           f"is Ibri to {top['receiver_name']}, {F.fmt(top['people'])} people. Ibri sends out "
           f"{F.fmt(out_ib)} people in all, to {len(rcv_all)} settlements; {len(rcv_big)} take a thousand "
           "or more.")
    D.tab_caption(d, "The main overflow routes: every route carrying 1,000 people or more at saturation")
    rts = [r for r in F.routes() if r["people"] >= 1000]
    D.table(d, ["From", "To", "People at saturation", "Donor full", "Receiver starts", "Receiver full"],
            [[r["donor_name"], r["receiver_name"], F.fmt(r["people"]), str(r["donor_full"] or ""),
              str(r["starts"] or ""), str(r["receiver_full"] or "")] for r in rts],
            widths=[3.0, 3.2, 2.6, 2.3, 2.6, 2.6], font=8.5, align_right={2, 3, 4, 5})
    D.p(d, "Receiver starts is the first year the receiver takes overflow from any donor, which can be "
           "before this donor is full.", size=9, italic=True, colour=D.GREY)
    _fig(d, "M10_overflow.png", 16.0, "Where the growth goes once a settlement is full. Arrows show the "
         "routes carrying 500 people or more at saturation; the shading shows how much of each "
         "settlement's capacity is taken by its neighbours' overflow.")
    _fig(d, "C10_fill_years.png", 15.0, "The year each settlement's empty plots are full. Ibri and the "
         "settlements that take 1,000 or more of its people are marked.")

    # ------------------------------------------------------------ 5.6
    D.h(d, 2, "5.6   The saturation year")
    _lead(d, "The rule", "The study area is saturated in the year its last settlement fills. Because "
          "every settlement receives overflow, that is also the first year in which growth finds no empty "
          "plot anywhere. Growth after it is reported as unhoused and is not placed.")
    _lead(d, "The result", f"The first settlement to fill is {first_name}, in {first_fill}; there is no "
          f"overflow before then, so the 2030 figures are each settlement's own growth. The last "
          f"{sum(1 for v in sat.values() if v == ult)} settlements fill in {ult}, which is the saturation "
          f"year, with {F.fmt(t['pop_ult'])} people and "
          f"{F.fmt(t['q_ult'])} m³/d of average sewage flow. The table below gives every settlement at "
          "five-year steps; a cell is blank once the settlement is full, and the last two columns give "
          "its saturation year and its population then.")
    _lead(d, "Source", "Project rule (engineer, 2026-09-10). The Terms of Reference ask for the design to "
          "completion plus 25 years or to the ultimate saturated condition, with five-year intervals "
          "(scope, pp 3 and 14–15).")
    D.tab_caption(d, "Population at five-year steps to saturation, every settlement")
    cols, rows = F.five_year_rows("pop")
    hdr = ["Settlement"] + [str(c) for c in cols[1:-1]] + ["Sat. year", "Sat. population"]
    rows = [[f"**{c}**" if r[0] == "Total" and c else c for c in r] for r in rows]
    nyr = len(hdr) - 3
    D.table(d, hdr, rows, widths=[2.3] + [round(11.0 / nyr, 2)] * nyr + [1.3, 1.6], font=6.5,
            align_right=set(range(1, len(hdr))))
    D.p(d, "Totals are rounded from the unrounded values and may differ by one from the sum of the rows.",
        size=9, italic=True, colour=D.GREY)
    _fig(d, "C08_growth.png", 15.5, "People by year to saturation, the six largest settlements shown "
         "separately. The flat top of each band is the year that settlement fills.")
    _lead(d, "Where it lives", "growth_by_settlement.py: first_unhoused and ult; sheets Five-year to "
          "saturation and Unhoused of the growth workbook; field ULT_YEAR on every plot and column "
          "SAT_YEAR on every plot and settlement. facts_w14.five_year_rows('pop') prints the table.")

    # ------------------------------------------------------------ 5.7
    D.h(d, 2, "5.7   Saturation with and without the overflow")
    D.p(d, f"On its own growth alone, {len(never)} of the 25 settlements would not fill before 2100: "
           f"{', '.join(never)}. With the overflow every settlement fills by {ult}. Their land is large "
           f"against their own population, and it is Ibri's growth and its neighbours' that occupies it. "
           f"Ibri itself fills a year earlier with the overflow ({own_by['IBRI']['with_spill']} against "
           f"{own_by['IBRI']['own']}), because it receives {F.fmt(own_by['IBRI']['inflow'])} people from "
           "small neighbours that fill before it.")
    D.tab_caption(d, "The year each settlement is full, on its own growth and with the overflow")
    D.table(d, ["Settlement", "Capacity, people", "Full on own growth", "Full with overflow", "People received"],
            [[r["name"], F.fmt(r["capacity"]), str(r["own"]) if r["own"] else "not before 2100",
              str(r["with_spill"] or ""), F.fmt(r["inflow"])] for r in own],
            widths=[3.8, 2.8, 3.2, 3.2, 3.0], font=8.5, align_right={1, 2, 3, 4})
    D.p(d, "", space_after=2)
    _lead(d, "Why it matters", "The design puts every settlement at its capacity at saturation either way. "
          "The overflow decides when each settlement's land fills and who fills it. That sets the "
          "population of each settlement in the intermediate years, the loads on its plots in 2055, and "
          "the order in which the network and the plant are needed.")
    _lead(d, "Where it lives", "growth_by_settlement.py: sat_own (the year demand alone reaches the "
          "capacity) and sat_year; columns SAT_OWN (0 = not before 2100), SAT_YEAR, IN_PEOPLE, "
          "OUT_PEOPLE, MAIN_TO and INSHARE of Settlements_merged.shp; facts_w14.own_growth_saturation().")

    # ------------------------------------------------------------ 5.8
    D.h(d, 2, "5.8   Placing the housed people on the plots")
    _lead(d, "What it is for", "The capacity count of Chapter 4 decides how many people a settlement can "
          "hold. The network needs to know on which plots they live, and a sewer that serves a street "
          "serves every plot on it, whether or not the plot passed the home-shape test.")
    _lead(d, "The rule", f"The people a settlement has housed by year y are spread over all its empty "
          f"plots up to {F.fmt(F.BIG)} m² (not grove, industrial, heritage or in an estate), in proportion "
          f"to plot area capped at {F.fmt(F.HOME_HI)} m². A sliver takes a sliver's share and a large plot "
          "no more than a full home plot. The sum over the plots equals the settlement's housed people "
          "by construction, so the network total and the plant total are the same figure.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("n"), UP("i")), M.delim(R("y")), M.EQ,
                       M.sub(R("H"), UP("s")), M.delim(R("y")), M.TIMES,
                       M.frac(M.sub(R("w"), UP("i")), M.nary("∑", UP("j ∈ s"), "", M.sub(R("w"), UP("j")), hide_hi=True)),
                       R(",   "), M.sub(R("w"), UP("i")), M.EQ,
                       M.func("min", M.delim(M.seq(M.sub(R("A"), UP("i")), R(", "), UP(F.fmt(F.HOME_HI)))))),
              number=eq)
    _symbols(d, [
        ["n i (y)", "new people placed on empty plot i in year y", "persons"],
        ["H s (y)", "new people housed in settlement s by year y (Section 5.3)", "persons"],
        ["w i", "spread weight of plot i: its area capped at 1,000 m²; zero for a plot above 2,000 m² "
                "or an excluded use", "m²"],
        ["A i", "area of plot i", "m²"]])
    a600 = 600.0
    _lead(d, "Worked for Ibri", f"Ibri has {F.fmt(nspread)} plots that receive the spread, with a total "
          f"weight of {F.fmt(wsum)} m². A {F.fmt(a600)} m² plot takes {F.fmt(a600)} ÷ {F.fmt(wsum)} of "
          f"Ibri's housed people: {F.fmt(h30 * a600 / wsum, 2)} people in 2030 and "
          f"{F.fmt(cap_ib * a600 / wsum, 2)} at saturation. A 1,500 m² plot takes the capped weight of "
          f"1,000 m²: {F.fmt(cap_ib * 1000 / wsum, 2)} people at saturation. Over the study area "
          f"{F.fmt(s['spread'])} empty plots receive people, and the slivers under {F.fmt(F.HOME_LO)} m² "
          f"carry {_pct(s['sliver_w'])} per cent of the weight. Chapter 7 turns these people into flow.")
    _lead(d, "Source", "Project rule (engineer, 2026-09-10).")
    _lead(d, "Where it lives", "plot_class_v2_apply.py writes SPREAD_W (the weight); growth_by_settlement.py "
          "writes POP_2030, POP_2055 and POP_ULT = POP + H × SPREAD_W / SPREAD_W_SUM, with Q_2030, Q_2055 "
          "and Q_ULT beside them, on PLOTS_load.shp. SPREAD_PLOTS and SPREAD_W_SUM per settlement are in "
          "settlements_today.csv.")

    # ------------------------------------------------------------ check
    D.h(d, 2, "5.9   Check it yourself")
    D.numbered(d, "In the growth workbook, sheet Population by year, divide Ibri's 2030 value by its 2024 "
                  f"value, then do the same for the total. Both give {f30:.4f}.", restart=True)
    D.numbered(d, "For every settlement in Settlements_merged.shp, SAT_POP equals POP_2024 plus CAP_POP to "
                  f"within one person. Their sum is {F.fmt(t['pop_ult'])}.")
    D.numbered(d, f"Sum POP_ULT over all plots of PLOTS_load.shp: {F.fmt(t['pop_ult'])}. Sum it over one "
                  "settlement: its saturation population.")
    D.numbered(d, "On an empty Ibri plot, POP_2030 − POP must equal Ibri's housed people in 2030 × "
                  f"SPREAD_W / {F.fmt(wsum)}.")
    D.numbered(d, "In the sheet Overflow routes, the column for the saturation year summed by receiver "
                  "equals IN_PEOPLE; summed by donor it equals OUT_PEOPLE.")
    D.numbered(d, "A settlement whose SAT_OWN is 0 must appear in the list of those that never fill on "
                  f"their own growth; there are {len(never)}.")
