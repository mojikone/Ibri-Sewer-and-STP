# W13 — apply plot class v2 to PLOTS_load.shp, refresh the settlement table, then re-run growth_by_settlement.py.
# Rules (engineer, 2026-09-09 evening):
#   farm first: any farm meter -> Agricultural (never overridden); a grove by Sentinel-2 NDVI -> Agricultural unless a 2/3 shop or government majority says otherwise (RGB test kept in GREEN_IMG for the record only)
#   more than two thirds of the meters home -> Residential; two thirds or more government -> Government; two thirds or more shop -> Commercial; between -> mixed
#   properties per built plot from pure home plots only (Residential, fewer than 15 dwelling meters)
#   capacity = future plots <= 2,000 m2 that are not farm, not industrial, not in an estate
import geopandas as gpd, pandas as pd, numpy as np, csv
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W13"
OR, BIG, HIGH = 5.32, 2000.0, 15
plots = gpd.read_file(f"{W13}/shp/PLOTS_load.shp")
veg = np.load(f"{W13}/analysis/vegfrac_plots.npy"); assert len(veg) == len(plots)
plots['VEGFRAC'] = np.where(veg >= 0, veg, np.nan).round(3)
a = plots['AREA_M2']; v = plots['VEGFRAC'].fillna(0)
plots['GREEN_IMG'] = (((v >= 0.55) & (a >= 2000)) | ((v >= 0.85) & (a >= 800))).astype(int)   # kept for the record only
# engineer 2026-09-10: the RGB test put farms on bare land, so it is off; Sentinel-2 NDVI (W13/py/ndvi_plots.py, scene 2026-09-09) is the green test:
#   a grove = at least 1,000 m2 of pixels at NDVI >= 0.30 with mean NDVI >= 0.20, OR a small plot (>= 800 m2) that is at least 60 % green at mean NDVI >= 0.40
nd = pd.read_csv(f"{W13}/analysis/ndvi_plots.csv").set_index('fid')
for c in ('NDVI_MEAN', 'NDVI_SHARE', 'GREEN_M2'): plots[c] = nd[c].reindex(range(len(plots))).values
nm, ns, ga = plots['NDVI_MEAN'].fillna(0), plots['NDVI_SHARE'].fillna(0), plots['GREEN_M2'].fillna(0)
plots['GREEN'] = (((ga >= 1000) & (nm >= 0.20)) | ((ns >= 0.60) & (nm >= 0.40) & (a >= 800))).astype(int)
est = plots.ESTATE.isin(['AL TAYYEB', 'TANAM'])

def classify(r):
    dom, nd, gv, sp, agr = r.G_DOM, r.G_NDOM, r.G_GOV, r.G_SPEC, r.G_AGR
    tot = dom + nd + gv
    if r.EST: return 'Industrial', 'EST'
    if agr > 0: return 'Agricultural', 'AGR'
    if r.GREEN == 1 and not (tot > 0 and (nd / tot >= 2 / 3 or gv / tot >= 2 / 3)): return 'Agricultural', 'GRN'
    if tot + sp == 0: return 'Unmetered', 'UNM'
    if sp > 0 and sp >= dom: return 'Industrial', 'IND'
    if tot == 0: return 'Unresolved', 'UNR'
    if dom / tot > 2 / 3: return 'Residential', 'RES'
    if gv / tot >= 2 / 3: return 'Government', 'GOV'
    if nd / tot >= 2 / 3: return 'Commercial', 'COM'
    return ('Residential-Commercial', 'RC') if nd >= gv else ('Government', 'RG')
plots['EST'] = est
cls = plots.apply(classify, axis=1, result_type='expand'); plots['DERIVED1'] = plots['DERIVED']; plots['DERIVED'] = cls[0]; plots['WHYC'] = cls[1]
plots['HIGH'] = (plots.G_DOM >= HIGH).astype(int)
plots['AGREE'] = np.where(plots.DERIVED == 'Unmetered', 'unmetered', np.where(plots.DERIVED == plots.Classes, 'same', np.where((plots.DERIVED == 'Government') | (plots.Classes == 'Proposed'), 'new', 'differs')))
built = plots.Buiding_St == 'EXisting'
pure = built & (plots.DERIVED == 'Residential') & (plots.HIGH == 0) & (plots.G_DOM > 0)
ppp = (plots[pure].groupby('SETTLE').G_DOM.sum() / plots[pure].groupby('SETTLE').size()).fillna(0)
cap = (plots.Buiding_St == 'Future') & (plots.AREA_M2 <= BIG) & (~plots.DERIVED.isin(['Agricultural', 'Industrial'])) & (plots.Classes != 'Industrial') & (~est)
plots['FUT_CAP'] = cap.astype(int); plots['FUT_PROPS'] = np.where(cap, plots.SETTLE.map(ppp).fillna(0), 0.0).round(3)
plots = plots.drop(columns=['EST'])
print('class v2:', plots.DERIVED.value_counts().to_dict())
print('changed from v1 (built, metered):', int((built & (plots.N_ACC > 0) & (plots.DERIVED != plots.DERIVED1)).sum()))
print('green plots', int(plots.GREEN.sum()), '| vegfrac known', int(plots.VEGFRAC.notna().sum()))

# write the plot layer with the same narrow schema
props = {}
ints = ['Moh_Classi', 'N_ACC', 'N_DOM', 'N_DOMADD', 'N_COM', 'N_GOV', 'N_AGR', 'N_CRT', 'N_IND', 'G_DOM', 'G_NDOM', 'G_GOV', 'G_SPEC', 'G_AGR', 'PROPS', 'FUT_CAP', 'SAT_YEAR', 'ULT_YEAR', 'GREEN', 'GREEN_IMG', 'HIGH']
for c in plots.columns:
    if c == 'geometry': continue
    if c in ints: plots[c] = plots[c].fillna(0).astype(int); props[c] = 'int:6'
    elif plots[c].dtype.kind == 'f':
        props[c] = 'float:12.1' if c == 'AREA_M2' else ('float:9.1' if c in ('WORKERS', 'POP', 'POP_2030', 'POP_2055', 'POP_ULT', 'GREEN_M2') else ('float:6.3' if c in ('VEGFRAC', 'FUT_PROPS', 'NDVI_MEAN', 'NDVI_SHARE') else 'float:10.4'))
    else: props[c] = f'str:{max(int(plots[c].astype(str).str.len().max()), 1)}'
plots.to_file(f"{W13}/shp/PLOTS_load.shp", schema={'geometry': 'Polygon', 'properties': props}, encoding='utf-8', engine='fiona')

# settlement table for the growth run
g = plots.groupby('SETTLE')
st = pd.DataFrame({'POP_TODAY': (g.G_DOM.sum() * OR).round(), 'DOM_PLOTS_BUILT': plots[pure].groupby('SETTLE').size(), 'PROPS_PER_BUILT_PLOT': ppp.round(3),
                   'NDOM_METERS': g.G_NDOM.sum(), 'GOV_METERS': g.G_GOV.sum(), 'FREE_METERS': 0,
                   'FUT_CAP_PLOTS': plots[cap].groupby('SETTLE').size()}).fillna(0)
st['FUT_CAP_PROPS'] = (st.FUT_CAP_PLOTS * st.PROPS_PER_BUILT_PLOT).round(); st['FUT_CAP_POP'] = (st.FUT_CAP_PROPS * OR).round()
st.index.name = 'SETTLE'; st.to_csv(f"{W13}/analysis/settlements_today.csv", encoding='utf-8-sig')
sett = gpd.read_file(f"{W13}/shp/Settlements_merged.shp").set_index('SETTLE')
sett['PPP'] = st.PROPS_PER_BUILT_PLOT; sett['CAP_PLOTS'] = st.FUT_CAP_PLOTS.astype(int); sett['CAP_POP'] = st.FUT_CAP_POP
sett.reset_index().to_file(f"{W13}/shp/Settlements_merged.shp", encoding='utf-8')
print('capacity people:', int(st.FUT_CAP_POP.sum()), '| ratios:', st.PROPS_PER_BUILT_PLOT.round(2).to_dict())
