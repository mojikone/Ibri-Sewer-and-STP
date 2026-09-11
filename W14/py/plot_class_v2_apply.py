# W13 — apply plot class v2 to PLOTS_load.shp, refresh the settlement table, then re-run growth_by_settlement.py.
# Rules (engineer, 2026-09-09 evening):
#   farm first: any farm meter -> Agricultural (never overridden); a grove by Sentinel-2 NDVI -> Agricultural unless a 2/3 shop or government majority says otherwise (RGB test kept in GREEN_IMG for the record only)
#   more than two thirds of the meters home -> Residential; two thirds or more government -> Government; two thirds or more shop -> Commercial; between -> mixed
#   government wins on a simple majority over the NDVI grove test (engineer 2026-09-10); the farm meter beats everything
#   MoH class 'Tourism' = the old quarter of Ibri, cultural heritage -> Heritage, takes nothing (engineer 2026-09-10)
#   properties per built plot from pure home plots only (Residential, fewer than 15 dwelling meters)
#   EMPTY PLOTS (engineer 2026-09-10): capacity = home-shaped empty plots (200-1,000 m2, compact >= 0.6, aspect <= 3, not grove / industrial / heritage / estate)
#     x the settlement's home share (share of pure homes among its built home-shaped metered plots) x its properties per home plot x its occupancy;
#   LOADS: the non-domestic and governmental pools land on the settlement's shop and government meters at a unit rate per meter (U_NDOM, U_GOV);
#     the estates' meters stay out of the pool, the estates carry workers x 93 L/d only (engineer 2026-09-10)
#     the growth is then SPREAD over every empty plot <= 2,000 m2 (not grove / industrial / heritage / estate) by area capped at 1,000 m2 (SPREAD_W)
import geopandas as gpd, pandas as pd, numpy as np, csv
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
OR_DEFAULT, OR_FLOOR, BASE, BIG, HIGH = 5.32, 4.0, 2024, 2000.0, 15
LPCD, R_ND, R_GOV, L_IND, RET_DOM, RET_ND = 164.0, 0.22, 0.14, 93.0, 0.85, 0.54
WB = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/_CLIENT/Ibri Sewer Demand R0 2026 08 03.xlsx"
# engineer 2026-09-10: the electricity accounts are 2024, the concept report's base year; the occupancy rate is PER SETTLEMENT =
# workbook population 2024 / metered properties, floored at 4.0 (small settlements with institutional housing would otherwise fall to 1-2)
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
# the workforce spread by area upstream (plots_meters_load.py) loses a few workers to rounding: scale back to the stated totals
for _e, _n in (('AL TAYYEB', 4500.0), ('TANAM', 1800.0)):
    _m = plots.ESTATE == _e; plots.loc[_m, 'WORKERS'] = plots.loc[_m, 'WORKERS'] * _n / plots.loc[_m, 'WORKERS'].sum()

def classify(r):
    dom, nd, gv, sp, agr = r.G_DOM, r.G_NDOM, r.G_GOV, r.G_SPEC, r.G_AGR
    tot = dom + nd + gv
    if r.EST: return 'Industrial', 'EST'
    if r.Classes == 'Tourism': return 'Heritage', 'HER'
    if agr > 0: return 'Agricultural', 'AGR'
    if r.GREEN == 1 and not (tot > 0 and (nd / tot >= 2 / 3 or gv / tot > 0.5)): return 'Agricultural', 'GRN'
    if tot + sp == 0: return 'Unmetered', 'UNM'
    if sp > 0 and sp >= dom: return 'Industrial', 'IND'
    if tot == 0: return 'Unresolved', 'UNR'
    if dom / tot > 2 / 3: return 'Residential', 'RES'
    if gv / tot >= 2 / 3: return 'Government', 'GOV'
    if nd / tot >= 2 / 3: return 'Commercial', 'COM'
    return ('Residential-Commercial', 'RC') if nd >= gv else ('Government', 'RG')
plots['EST'] = est
cls = plots.apply(classify, axis=1, result_type='expand')
_v1 = pd.read_csv(f"{W13}/analysis/plot_class_v2_per_plot.csv", usecols=['fid', 'DERIVED']).set_index('fid')['DERIVED']   # the first class (9 Sept), kept for the audit
plots['DERIVED1'] = _v1.reindex(range(len(plots))).fillna('').values; plots['DERIVED'] = cls[0]; plots['WHYC'] = cls[1]
plots['HIGH'] = (plots.G_DOM >= HIGH).astype(int)
plots['AGREE'] = np.where(plots.DERIVED == 'Unmetered', 'unmetered', np.where(plots.DERIVED == plots.Classes, 'same', np.where((plots.DERIVED == 'Government') | (plots.Classes == 'Proposed'), 'new', 'differs')))
built = plots.Buiding_St == 'EXisting'
pure = built & (plots.DERIVED == 'Residential') & (plots.HIGH == 0) & (plots.G_DOM > 0)
ppp = (plots[pure].groupby('SETTLE').G_DOM.sum() / plots[pure].groupby('SETTLE').size()).fillna(0)
# shape of the plot: compactness against the minimum rotated rectangle, and that rectangle's aspect
mbr = plots.geometry.minimum_rotated_rectangle()
plots['COMPACT'] = (plots.geometry.area / mbr.area.replace(0, np.nan)).fillna(0).round(3)
def _aspect(r):
    try:
        c = np.array(r.exterior.coords[:4]); d = np.hypot(*(c[1:] - c[:-1]).T); return max(d[0], d[1]) / max(min(d[0], d[1]), 0.1)
    except Exception: return 99.0
plots['ASPECT'] = mbr.apply(_aspect).round(2)
HOME_LO, HOME_HI = 200.0, 1000.0
homeshape = (plots.AREA_M2 >= HOME_LO) & (plots.AREA_M2 <= HOME_HI) & (plots.COMPACT >= 0.6) & (plots.ASPECT <= 3)
plots['HOMESHAPE'] = homeshape.astype(int)
excluded = plots.DERIVED.isin(['Agricultural', 'Industrial', 'Heritage']) | (plots.Classes == 'Industrial') | est
# home share: among the settlement's built, metered, home-shaped plots, the share that are pure homes
bh = built & homeshape & (plots.N_ACC > 0)
home_share = (plots[bh & pure].groupby('SETTLE').size() / plots[bh].groupby('SETTLE').size())
# a settlement with fewer than 10 built, metered, home-shaped plots has no sample to speak of: it takes the area-wide share (2026-09-10, Miayrid had none and could never fill)
MIN_SAMPLE = 10; share_all = float((bh & pure).sum() / bh.sum()); n_bh = plots[bh].groupby('SETTLE').size()
home_share = home_share.reindex(props_s.index if 'props_s' in dir() else plots.SETTLE.unique()).where(n_bh.reindex(home_share.index).fillna(0) >= MIN_SAMPLE, share_all).fillna(share_all)
ppp_all = float(plots[pure].G_DOM.sum() / max(pure.sum(), 1)); n_pure = plots[pure].groupby('SETTLE').size()
ppp = ppp.reindex(home_share.index).where(n_pure.reindex(home_share.index).fillna(0) >= MIN_SAMPLE, ppp_all).fillna(ppp_all)
print('home share fallback %.2f and ratio fallback %.2f for settlements with under %d sample plots:' % (share_all, ppp_all, MIN_SAMPLE), sorted(n_bh.reindex(home_share.index).fillna(0)[lambda x: x < MIN_SAMPLE].index.tolist()))
cap = (plots.Buiding_St == 'Future') & homeshape & ~excluded
plots['FUT_CAP'] = cap.astype(int)
plots['FUT_PROPS'] = np.where(cap, plots.SETTLE.map(ppp).fillna(0) * plots.SETTLE.map(home_share).fillna(0), 0.0).round(3)   # expected properties per counted plot
spread = (plots.Buiding_St == 'Future') & (plots.AREA_M2 <= BIG) & ~excluded
plots['SPREAD_W'] = np.where(spread, np.minimum(plots.AREA_M2, HOME_HI), 0.0).round(1)
plots = plots.drop(columns=['EST'])
print('class v5:', plots.DERIVED.value_counts().to_dict())
print('home-shaped empty plots counted:', int(cap.sum()), '| empty plots that receive the spread:', int(spread.sum()), '| home share:', home_share.round(2).to_dict())
print('changed from v1 (built, metered):', int((built & (plots.N_ACC > 0) & (plots.DERIVED != plots.DERIVED1)).sum()))
print('green plots', int(plots.GREEN.sum()), '| vegfrac known', int(plots.VEGFRAC.notna().sum()))

# ---------- occupancy per settlement and the loads, recomputed ----------
import openpyxl
wb = openpyxl.load_workbook(WB, read_only=True, data_only=True); ws = wb['Project Pop Settlements']
rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]; kb = hdr.index(f'Pop {BASE}')
wb_base = {str(r[1]).strip().upper(): float(r[kb]) for r in rows[1:] if r[1]}
props_s = plots.groupby('SETTLE').G_DOM.sum()
or_raw = pd.Series({st: (wb_base[st] / props_s[st] if props_s.get(st, 0) > 0 and st in wb_base else OR_DEFAULT) for st in props_s.index})
# ceiling (engineer 2026-09-10): the highest occupancy among the settlements with 2,000+ workbook people (Bat, 6.12); it touches only the tiny ones
OR_CEIL = float(or_raw[[st for st in or_raw.index if wb_base.get(st, 0) >= 2000]].max())
or_s = or_raw.clip(lower=OR_FLOOR, upper=OR_CEIL).round(4)   # four decimals: the adopted rate prints as the derived one where no rule applies
# engineer 2026-09-10: a settlement under 1,000 people (workbook 2024) is not attractive enough for second dwellings and has no sample to
# measure on: occupancy 4.0, one property per plot, home share 0.9. The derived values are kept beside the adopted ones for the report.
SMALL_POP = 1000.0
small = pd.Series({st: wb_base.get(st, 0) < SMALL_POP for st in props_s.index})
ppp_raw = ppp.copy(); share_raw = home_share.copy()
or_s = or_s.where(~small, 4.0)
ppp = ppp.where(~small.reindex(ppp.index).fillna(False), 1.0)
home_share = home_share.where(~small.reindex(home_share.index).fillna(False), 0.9)
print('small settlements (under %d people): occupancy 4.0, ratio 1, share 0.9:' % SMALL_POP, sorted(small[small].index.tolist()))
print('occupancy ceiling %.2f (largest among settlements with 2,000+ people)' % OR_CEIL)
plots['OR_S'] = plots.SETTLE.map(or_s).fillna(OR_DEFAULT)
plots['PPP_S'] = plots.SETTLE.map(ppp).fillna(ppp_all).round(3); plots['HOMESH_S'] = plots.SETTLE.map(home_share).fillna(share_all).round(3)
plots['POP'] = (plots.G_DOM * plots.OR_S).round(4)   # four decimals, or thousands of equal values round the same way
# The non-domestic and governmental water of a settlement is a pool: its people x 22 % and x 14 % of 164 L/d (Tab 11, "distributed" ratios).
# The pool lands on the settlement's shop and government meters in equal shares per meter, so each settlement has a unit rate in L/d per
# meter (U_NDOM, U_GOV). The two industrial estates are special consumption (workers x 93 L/d) and their meters stay OUT of the pool
# (engineer 2026-09-10). A settlement with no such meter outside the estates keeps the pool on its dwellings, by people.
pop_s = plots.groupby('SETTLE').POP.sum(); town = ~est
nd_s = plots[town].groupby('SETTLE').G_NDOM.sum().reindex(pop_s.index).fillna(0); gv_s = plots[town].groupby('SETTLE').G_GOV.sum().reindex(pop_s.index).fillna(0)
pool_nd_s = pop_s * R_ND * LPCD / 1000.0; pool_gv_s = pop_s * R_GOV * LPCD / 1000.0          # m3/d per settlement
u_nd_s = pool_nd_s * 1000.0 / nd_s.replace(0, np.nan); u_gv_s = pool_gv_s * 1000.0 / gv_s.replace(0, np.nan)   # L/d per meter
plots['U_NDOM'] = plots.SETTLE.map(u_nd_s).fillna(0).round(1); plots['U_GOV'] = plots.SETTLE.map(u_gv_s).fillna(0).round(1)
nd_m = plots.SETTLE.map(nd_s); gv_m = plots.SETTLE.map(gv_s); p_s = plots.SETTLE.map(pop_s)
pool_nd = plots.SETTLE.map(pool_nd_s); pool_gv = plots.SETTLE.map(pool_gv_s)
plots['W_DOM'] = (plots.POP * LPCD / 1000.0).round(4)
w_nd = np.where(nd_m > 0, plots.G_NDOM * plots.SETTLE.map(u_nd_s).fillna(0) / 1000.0, np.where(p_s > 0, pool_nd * plots.POP / p_s.replace(0, np.nan), 0.0))
w_gv = np.where(gv_m > 0, plots.G_GOV * plots.SETTLE.map(u_gv_s).fillna(0) / 1000.0, np.where(p_s > 0, pool_gv * plots.POP / p_s.replace(0, np.nan), 0.0))
plots['W_NDOM'] = pd.Series(np.where(est, 0.0, w_nd), index=plots.index).fillna(0).round(4)
plots['W_GOV'] = pd.Series(np.where(est, 0.0, w_gv), index=plots.index).fillna(0).round(4)
plots['W_SPEC'] = (plots.WORKERS.fillna(0) * L_IND / 1000.0).round(4)
plots['W_TOT'] = (plots.W_DOM + plots.W_NDOM + plots.W_GOV + plots.W_SPEC).round(4)
plots['S_DOM'] = (plots.W_DOM * RET_DOM).round(4); plots['S_NDOM'] = (plots.W_NDOM * RET_ND).round(4); plots['S_GOV'] = (plots.W_GOV * RET_ND).round(4); plots['S_SPEC'] = (plots.W_SPEC * RET_ND).round(4)
plots['QADF'] = (plots.S_DOM + plots.S_NDOM + plots.S_GOV + plots.S_SPEC).round(4)
plots['FUT_PROPS'] = np.where(cap, plots.SETTLE.map(ppp).fillna(0) * plots.SETTLE.map(home_share).fillna(0), 0.0).round(3)   # adopted ratio and share
print('occupancy per settlement (workbook %d / metered properties, floor %.1f):' % (BASE, OR_FLOOR), or_s.round(2).to_dict())
print('TODAY: people %.0f (workbook %d for the 25: %.0f) | Qadf %.0f m3/d' % (plots.POP.sum(), BASE, sum(wb_base.get(st, 0) for st in props_s.index), plots.QADF.sum()))

# the audit fields (the first class, the dropped tests) go to a csv; the delivered layer carries only what the report and the network read
AUDIT = ['DERIVED1', 'AGREE', 'GREEN', 'GREEN_IMG', 'VEGFRAC', 'HIGH']
aud = plots[AUDIT].copy(); aud.index.name = 'fid'; aud.to_csv(f"{W13}/analysis/plot_class_audit.csv")
plots = plots.drop(columns=AUDIT + ['PROPS'], errors='ignore')   # PROPS is gone from the layer after the first run      # PROPS was a copy of G_DOM: every domestic meter is one property
# write the plot layer with the same narrow schema; people to two decimals so the plots sum to the settlement to the person
props = {}
ints = ['Moh_Classi', 'N_ACC', 'N_DOM', 'N_DOMADD', 'N_COM', 'N_GOV', 'N_AGR', 'N_CRT', 'N_IND', 'G_DOM', 'G_NDOM', 'G_GOV', 'G_SPEC', 'G_AGR', 'FUT_CAP', 'SAT_YEAR', 'ULT_YEAR', 'HOMESHAPE']
float3 = ('FUT_PROPS', 'NDVI_MEAN', 'NDVI_SHARE', 'COMPACT', 'PPP_S', 'HOMESH_S')
for c in plots.columns:
    if c == 'geometry': continue
    if c in ints: plots[c] = plots[c].fillna(0).astype(int); props[c] = 'int:6'
    elif plots[c].dtype.kind == 'f':
        props[c] = 'float:12.1' if c == 'AREA_M2' else ('float:11.4' if c in ('WORKERS', 'POP', 'POP_2030', 'POP_2055', 'POP_ULT', 'OR_S') else ('float:9.1' if c in ('GREEN_M2', 'U_NDOM', 'U_GOV') else ('float:6.3' if c in float3 else ('float:7.2' if c in ('ASPECT', 'SPREAD_W') else 'float:10.4'))))
    else: props[c] = f'str:{max(int(plots[c].astype(str).str.len().max()), 1)}'
plots.to_file(f"{W13}/shp/PLOTS_load.shp", schema={'geometry': 'Polygon', 'properties': props}, encoding='utf-8', engine='fiona')

# settlement table for the growth run
g = plots.groupby('SETTLE')
empty_all = plots[plots.Buiding_St == 'Future'].groupby('SETTLE').size()
st = pd.DataFrame({'WB_2024': pd.Series(wb_base).reindex(pop_s.index), 'PROPS': props_s, 'POP_TODAY': g.POP.sum().round(2),
                   'OR_RAW': or_raw.round(3), 'OR_S': or_s, 'SMALL': small.astype(int),
                   'BUILT_PLOTS': plots[built].groupby('SETTLE').size(), 'EMPTY_PLOTS': empty_all, 'DOM_PLOTS_BUILT': plots[pure].groupby('SETTLE').size(),
                   'PPP_RAW': ppp_raw.round(3), 'PROPS_PER_BUILT_PLOT': ppp.round(3), 'HOME_SHARE_RAW': share_raw.round(3), 'HOME_SHARE': home_share.round(3),
                   'NDOM_METERS': g.G_NDOM.sum(), 'NDOM_POOL': nd_s, 'GOV_METERS': g.G_GOV.sum(), 'GOV_POOL': gv_s, 'AGR_METERS': g.G_AGR.sum(), 'SPEC_METERS': g.G_SPEC.sum(),
                   'WORKERS': g.WORKERS.sum().round(), 'U_NDOM': u_nd_s.round(1), 'U_GOV': u_gv_s.round(1),
                   'W_DOM': g.W_DOM.sum().round(2), 'W_NDOM': g.W_NDOM.sum().round(2), 'W_GOV': g.W_GOV.sum().round(2), 'W_SPEC': g.W_SPEC.sum().round(2), 'W_TOT': g.W_TOT.sum().round(2),
                   'S_DOM': g.S_DOM.sum().round(2), 'S_NDOM': g.S_NDOM.sum().round(2), 'S_GOV': g.S_GOV.sum().round(2), 'S_SPEC': g.S_SPEC.sum().round(2), 'Q_2024': g.QADF.sum().round(2),
                   'FUT_CAP_PLOTS': plots[cap].groupby('SETTLE').size(), 'SPREAD_PLOTS': plots[spread].groupby('SETTLE').size(), 'SPREAD_W_SUM': plots[spread].groupby('SETTLE').SPREAD_W.sum()}).fillna(0)
st['FUT_CAP_PROPS'] = (st.FUT_CAP_PLOTS * st.PROPS_PER_BUILT_PLOT * st.HOME_SHARE).round(); st['FUT_CAP_POP'] = (st.FUT_CAP_PROPS * st.OR_S).round()
st.index.name = 'SETTLE'; st.to_csv(f"{W13}/analysis/settlements_today.csv", encoding='utf-8-sig')
# the occupancy table the report prints: derived, adopted, and the rule that set it
rule = pd.Series('derived', index=props_s.index)
rule[or_raw < OR_FLOOR] = 'floor %.1f' % OR_FLOOR; rule[or_raw > OR_CEIL] = 'cap %.2f' % OR_CEIL; rule[small] = 'under %d people: 4.0' % SMALL_POP
occ = pd.DataFrame({'properties': props_s, 'workbook_2024': st.WB_2024.round(1), 'OR_raw': or_raw.round(2), 'OR_used': or_s.round(2), 'rule': rule,
                    'people_used': st.POP_TODAY.round(), 'delta_vs_workbook': (st.POP_TODAY - st.WB_2024).round()})
occ.index.name = 'SETTLE'; occ.sort_values('workbook_2024', ascending=False).to_csv(f"{W13}/analysis/occupancy_by_settlement.csv")
# the settlement layer is written by growth_by_settlement.py, with the growth results, from this table
print('capacity people:', int(st.FUT_CAP_POP.sum()), '| ratios:', st.PROPS_PER_BUILT_PLOT.round(2).to_dict())
print('unit rates L/d per meter, shop / government:', {k: (round(float(u_nd_s.get(k, 0) or 0)), round(float(u_gv_s.get(k, 0) or 0))) for k in ['IBRI', 'AD DARIZ', 'AL ARAQI', 'AT TAYYIB', 'TANAM']})
