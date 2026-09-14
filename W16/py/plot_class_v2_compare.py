# W13 — plot class v2 (farm first, then proportion) and what it does to the settlement ratios. Comparison only; writes nothing to the layers.
# Rules (engineer, 2026-09-09, evening):
#   farm first: any farm meter, or green in the imagery (W3 rule: vegfrac >= 0.55 & area >= 2000 m2, or vegfrac >= 0.85 & area >= 800 m2) -> Agricultural
#   then proportion of the plot's meters: shop share >= 2/3 Commercial, <= 1/3 Residential, between Residential-Commercial; government the same way
#   properties per built plot from PURE home plots only (not mixed, not farm, not plots with 15+ dwelling meters)
import geopandas as gpd, pandas as pd, numpy as np, openpyxl
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
OR, BIG, HIGH = 5.32, 2000.0, 15
plots = gpd.read_file(f"{W13}/shp/PLOTS_load.shp")
old = gpd.read_file("D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W3/shp/MoH_Plots_class_v4.shp")[['VEGFRAC', 'geometry']]
cent = plots[['geometry']].copy(); cent['geometry'] = plots.geometry.centroid
j = gpd.sjoin(cent, old, how='left', predicate='within')
j = j[~j.index.duplicated(keep='first')]
plots['VEGFRAC'] = j['VEGFRAC'].reindex(plots.index).values
a = plots['AREA_M2']; v = plots['VEGFRAC'].fillna(0)
plots['GREEN'] = (((v >= 0.55) & (a >= 2000)) | ((v >= 0.85) & (a >= 800))).astype(int)
print('vegfrac known for', int(plots.VEGFRAC.notna().sum()), 'of', len(plots), '| green plots', int(plots.GREEN.sum()))

def classify(r):
    dom = r.G_DOM; nd = r.G_NDOM; gv = r.G_GOV; sp = r.G_SPEC; agr = r.G_AGR; n = dom + nd + gv + sp + agr
    if r.ESTATE in ('AL TAYYEB', 'TANAM'): return 'Industrial'
    if agr > 0 or r.GREEN == 1: return 'Agricultural'
    if n == 0: return 'Unmetered'
    if sp > 0 and sp >= dom: return 'Industrial'
    tot = dom + nd + gv
    if tot == 0: return 'Unresolved'
    if gv / tot >= 2 / 3: return 'Government'
    if nd / tot >= 2 / 3: return 'Commercial'
    if (nd + gv) / tot <= 1 / 3: return 'Residential'
    return 'Residential-Commercial' if nd >= gv else 'Government'
plots['CLASS2'] = plots.apply(classify, axis=1)
plots['HIGH'] = (plots.G_DOM >= HIGH).astype(int)
built = plots.Buiding_St == 'EXisting'
pure = built & (plots.CLASS2 == 'Residential') & (plots.HIGH == 0) & (plots.G_DOM > 0)
old_home = built & (plots.G_DOM > 0)                                        # the v1 basis: any built plot with a dwelling meter
cap2 = (plots.Buiding_St == 'Future') & (plots.AREA_M2 <= BIG) & (plots.CLASS2 != 'Agricultural') & (plots.CLASS2 != 'Industrial') & (plots.Classes != 'Industrial') & (~plots.ESTATE.isin(['AL TAYYEB', 'TANAM']))
cap1 = plots.FUT_CAP == 1

print('\nclass v1 -> v2 (built plots with meters):')
print(pd.crosstab(plots.loc[built & (plots.N_ACC > 0), 'DERIVED'], plots.loc[built & (plots.N_ACC > 0), 'CLASS2']).to_string())
print('\nfarm plots v2 with dwellings on them:', int(((plots.CLASS2 == 'Agricultural') & (plots.G_DOM > 0)).sum()), '| their properties:', int(plots.loc[(plots.CLASS2 == 'Agricultural'), 'G_DOM'].sum()))
print('high-dwelling plots (>= %d):' % HIGH, int((plots.HIGH == 1).sum()), '| properties on them:', int(plots.loc[plots.HIGH == 1, 'G_DOM'].sum()))

g = plots.groupby('SETTLE')
tab = pd.DataFrame({
    'pop_today': (g.G_DOM.sum() * OR).round(),
    'home_plots_v1': plots[old_home].groupby('SETTLE').size(), 'ppp_v1': (plots[old_home].groupby('SETTLE').G_DOM.sum() / plots[old_home].groupby('SETTLE').size()).round(3),
    'home_plots_v2': plots[pure].groupby('SETTLE').size(), 'ppp_v2': (plots[pure].groupby('SETTLE').G_DOM.sum() / plots[pure].groupby('SETTLE').size()).round(3),
    'cap_plots_v1': plots[cap1].groupby('SETTLE').size(), 'cap_plots_v2': plots[cap2].groupby('SETTLE').size()}).fillna(0)
tab['cap_pop_v1'] = (tab.cap_plots_v1 * tab.ppp_v1 * OR).round(); tab['cap_pop_v2'] = (tab.cap_plots_v2 * tab.ppp_v2 * OR).round()
# fill year on the settlement's own growth only (no overflow in or out), for the comparison
wb = openpyxl.load_workbook("D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/_CLIENT/Ibri Sewer Demand R0 2026 08 03.xlsx", read_only=True, data_only=True)
ws = wb['Project Pop Settlements']; rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]
yc = {int(h.split()[1]): k for k, h in enumerate(hdr) if h.startswith('Pop ')}
P = {str(r[1]).strip().upper(): {y: float(r[k]) for y, k in yc.items()} for r in rows[1:] if r[1] and str(r[1]).strip().upper() in tab.index}
def fill_year(s, cap):
    if cap <= 0 or s not in P: return 'n/a'
    base = P[s][2026]; pop0 = tab.at[s, 'pop_today']
    for y in range(2026, 2101):
        if pop0 * (P[s][y] / base - 1) >= cap: return y
    return 'after 2100'
tab['fill_own_v1'] = [fill_year(s, tab.at[s, 'cap_pop_v1']) for s in tab.index]
tab['fill_own_v2'] = [fill_year(s, tab.at[s, 'cap_pop_v2']) for s in tab.index]
tab = tab.sort_values('pop_today', ascending=False)
pd.set_option('display.width', 250); print('\n', tab.to_string())
print('\nTOTAL capacity v1 %.0f  v2 %.0f' % (tab.cap_pop_v1.sum(), tab.cap_pop_v2.sum()))
tab.to_csv(f"{W13}/analysis/plot_class_v2_comparison.csv", encoding='utf-8-sig')
plots[['Name', 'SETTLE', 'Buiding_St', 'Classes', 'DERIVED', 'CLASS2', 'GREEN', 'VEGFRAC', 'HIGH', 'G_DOM', 'G_NDOM', 'G_GOV', 'G_SPEC', 'G_AGR']].to_csv(f"{W13}/analysis/plot_class_v2_per_plot.csv", index_label='fid', encoding='utf-8-sig')
print('written comparison csvs')
