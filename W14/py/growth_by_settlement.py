# W14 — growth per settlement, year by year to saturation. Plain python, run after plot_class_v2_apply.py (which writes settlements_today.csv).
#
# Rules (engineer, 2026-09-09 and 2026-09-10; the Rules sheet of the workbook states them in full):
#   today's people per settlement from plot_class_v2_apply.py (domestic meters x the settlement occupancy, base 2024); each settlement grows
#   at its own RATE from the inception workbook (Project Pop Settlements); capacity from home-shaped empty plots x home share x ratio x occupancy;
#   the housed people are spread over all empty plots <= 2,000 m2 by capped area
#   overflow: IBRI in parallel to AL ARAQI 70 %, AL QURAYN 20 %, SHALASHIL 10 %, then AD DARIZ, then the nearest settlement with room;
#   AT TAYYIB to MIAYRID first; every other settlement to its nearest neighbour with room, whatever its size
#   per person: 164 L/d domestic, 0.22 x 164 non-domestic, 0.14 x 164 governmental; sewage 85 % / 54 %; a future plot 171.3 L/d per person
import pandas as pd, numpy as np, geopandas as gpd, openpyxl, math, os
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
WB = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/_CLIENT/Ibri Sewer Demand R0 2026 08 03.xlsx"
LPCD, R_ND, R_GOV, RET_DOM, RET_ND = 164.0, 0.22, 0.14, 0.85, 0.54
BASE = 2024; YEARS = list(range(BASE, 2101)); DESIGN = [2030, 2055]   # 2024 = the electricity accounts' year and the concept report's base
Q_PER_CAP = LPCD * (RET_DOM + R_ND * RET_ND + R_GOV * RET_ND) / 1000.0     # m3/d per person on a future plot (all three streams)
BIG = 2000.0; RECEIVER_MIN_POP = 0.0   # engineer 2026-09-10: every settlement receives overflow from its neighbours, so the small ones saturate too
# engineer 2026-09-10, from a person who knows the area: Ibri overspills IN PARALLEL to Al Araqi 70 %, Al Qurayn 20 %, Shalashil 10 %;
# when those are full, to Ad Dariz; after that the nearest settlement with spare room, any size
SPILL = {'IBRI': [[('AL ARAQI', 0.7), ('AL QURAYN', 0.2), ('SHALASHIL', 0.1)], [('AD DARIZ', 1.0)]],
         'AT TAYYIB': [[('MIAYRID', 1.0)]]}   # engineer 2026-09-10: Miayrid fills from At Tayyib's overflow first

st = pd.read_csv(f"{W13}/analysis/settlements_today.csv").set_index('SETTLE')
plots = gpd.read_file(f"{W13}/shp/PLOTS_load.shp")
sett = gpd.read_file(f"{W13}/shp/Settlements_merged.shp").set_index('SETTLE')
cent = sett.geometry.centroid

# workbook projection
wb = openpyxl.load_workbook(WB, read_only=True, data_only=True); ws = wb['Project Pop Settlements']
rows = list(ws.iter_rows(values_only=True)); hdr = [str(h) for h in rows[0]]
ycols = {int(h.split()[1]): k for k, h in enumerate(hdr) if h.startswith('Pop ')}
proj = {}
for r in rows[1:]:
    if r[1] and str(r[1]).strip().upper() in st.index:
        proj[str(r[1]).strip().upper()] = {y: float(r[k]) for y, k in ycols.items()}
missing = [s for s in st.index if s not in proj]; assert not missing, missing
P = pd.DataFrame(proj).T.reindex(st.index)                                  # settlements x years (workbook)
growth = P.div(P[BASE], axis=0)                                            # growth relative to the base year
pop0 = st['POP_TODAY'].astype(float); cap = st['FUT_CAP_POP'].astype(float)
demand = growth[YEARS].mul(pop0, axis=0).sub(pop0, axis=0).clip(lower=0)   # cumulative new people wanting a home in s

# receivers by distance, every settlement (RECEIVER_MIN_POP = 0)
order = {}
for s in st.index:
    stages = [list(stage) for stage in SPILL.get(s, [])]
    named = {r for stage in stages for r, _ in stage}
    cands = [r for r in st.index if r != s and r not in named and pop0[r] >= RECEIVER_MIN_POP]
    cands.sort(key=lambda r: cent[s].distance(cent[r]))
    order[s] = stages + [[(r, 1.0)] for r in cands]          # each later stage: one receiver, all of the remainder

housed_own = pd.DataFrame(0.0, index=st.index, columns=YEARS)     # new people housed in their own settlement
inflow = pd.DataFrame(0.0, index=st.index, columns=YEARS)         # new people housed here that came from elsewhere
inflow_from = {}                                                   # (donor, receiver) -> series
unhoused = pd.DataFrame(0.0, index=st.index, columns=YEARS)
own_c = pd.Series(0.0, index=st.index); in_c = pd.Series(0.0, index=st.index); un_c = pd.Series(0.0, index=st.index)
pair_c = {}
prev = pd.Series(0.0, index=st.index)
for y in YEARS:
    inc = (demand[y] - prev).clip(lower=0); prev = demand[y]
    for s in st.index.sort_values(key=lambda ix: -pop0[ix]):     # big donors first
        need = inc[s]
        spare = cap[s] - own_c[s] - in_c[s]; take = min(need, max(spare, 0.0)); own_c[s] += take; need -= take
        for stage in order[s]:
            if need <= 1e-9: break
            # a stage splits the overflow by share; what a full receiver refuses is re-offered to the others of the same stage
            todo = {r: need * sh for r, sh in stage}
            for _ in range(len(stage)):
                left = 0.0
                for r in list(todo):
                    spare = max(cap[r] - own_c[r] - in_c[r], 0.0); take = min(todo[r], spare)
                    if take > 0: in_c[r] += take; pair_c[(s, r)] = pair_c.get((s, r), 0.0) + take; need -= take
                    left += todo[r] - take; todo[r] = 0.0
                    if spare - take <= 1e-9: todo.pop(r)
                if left <= 1e-9 or not todo: break
                for r in todo: todo[r] = left / len(todo)
        un_c[s] += need
    housed_own[y] = own_c.values; inflow[y] = in_c.values; unhoused[y] = un_c.values
    for k, v in pair_c.items(): inflow_from.setdefault(k, {})[y] = v
housed = housed_own + inflow
fill = housed.div(cap.replace(0, np.nan), axis=0).fillna(0.0).clip(upper=1.0)
sat_year = {s: next((y for y in YEARS if cap[s] > 0 and housed.at[s, y] >= cap[s] - 0.5), None) for s in st.index}
sat_own = {s: next((y for y in YEARS if cap[s] > 0 and demand.at[s, y] >= cap[s] - 0.5), None) for s in st.index}   # on its own growth alone
out_people = pd.Series({s: sum(v for (d, r), v in pair_c.items() if d == s) for s in st.index})
main_to = pd.Series({s: (max(((r, v) for (d, r), v in pair_c.items() if d == s), key=lambda kv: kv[1], default=('', 0.0))[0]) for s in st.index})
pop_total = housed.add(pop0, axis=0)
# sewage per settlement: today's Qadf from the plot table (existing plots) + future plots at Q_PER_CAP
q0 = plots.groupby('SETTLE')['QADF'].sum().reindex(st.index).fillna(0.0)
q = housed.mul(Q_PER_CAP).add(q0, axis=0)
# ultimate = the first year growth finds no empty plot anywhere among the receivers (the big settlements are full);
# if that never happens, the year the last settlement fills, else 2100
first_unhoused = next((y for y in YEARS if unhoused[y].sum() > 0.5), None)
ult = first_unhoused or max([y for y in sat_year.values() if y] or [YEARS[-1]])
print('first year with nowhere to go:', first_unhoused)
print('base', BASE, 'pop today %.0f' % pop0.sum(), 'capacity %.0f' % cap.sum())
for y in DESIGN + [ult, 2100]:
    print(f'  {y}: housed new {housed[y].sum():.0f} | total pop {pop_total[y].sum():.0f} | unhoused {unhoused[y].sum():.0f} | Qadf {q[y].sum():.0f} m3/d')
print('saturation years:', {s: sat_year[s] for s in st.index if sat_year[s]})
print('ultimate (all full or 2100):', ult)

# ---------- Excel ----------
xl = f"{W13}/analysis/W14_growth_by_settlement.xlsx"
summ = pd.DataFrame({'pop_today_meters': pop0.round(), 'workbook_2024': P[BASE].round(), 'props_per_built_plot': st['PROPS_PER_BUILT_PLOT'],
                     'cap_plots': st['FUT_CAP_PLOTS'], 'cap_people': cap.round(), 'saturation_year': pd.Series(sat_year),
                     'pop_2030': pop_total[2030].round(), 'pop_2055': pop_total[2055].round(), f'pop_{ult}_ultimate': pop_total[ult].round(), 'pop_2100': pop_total[2100].round(),
                     'inflow_at_ultimate': inflow[ult].round(), 'unhoused_2100': unhoused[2100].round(),
                     'Qadf_today_m3d': q0.round(1), 'Qadf_2030': q[2030].round(1), 'Qadf_2055': q[2055].round(1), f'Qadf_{ult}_ultimate': q[ult].round(1), 'Qadf_2100': q[2100].round(1)})
spill_tab = pd.DataFrame([{'from': k[0], 'to': k[1], **{y: round(v.get(y, 0)) for y in DESIGN + [ult, 2100]}} for k, v in inflow_from.items()])
rules = pd.DataFrame({'rule': [
    f'base year {BASE}: today = dwelling meters (primary, subsidised and additional tariffs) x the settlement occupancy = workbook {BASE} people / domestic meters, floored at 4.0 and capped at the highest rate among settlements of 2,000+ people (Bat, 6.12)',
    'a settlement under 1,000 people (workbook 2024) takes occupancy 4.0, one property per home plot and a home share of 0.9, whatever its meters return (13 settlements)',
    'each settlement grows at its own rate from the inception workbook sheet "Project Pop Settlements", applied to the metered population',
    'capacity = home-shaped empty plots (200-1,000 m2, compact, not a strip; not grove / industrial / heritage / estate) x home share x properties per home plot x the settlement occupancy',
    'the housed people are spread over ALL the settlement empty plots <= 2,000 m2 (not grove / industrial / heritage / estate) by plot area capped at 1,000 m2; slivers take a sliver share',
    f'overflow: IBRI in parallel to AL ARAQI 70 %, AL QURAYN 20 %, SHALASHIL 10 %, then AD DARIZ, then the nearest settlement with spare room, any size; AT TAYYIB -> MIAYRID first; other settlements: nearest with spare room, any size',
    f'water per person: {LPCD} L/d domestic, {R_ND} x {LPCD} non-domestic, {R_GOV} x {LPCD} governmental (never compounded); sewage {RET_DOM} / {RET_ND}',
    'existing plot: people = domestic meters x occupancy; non-domestic and governmental water = the settlement pool (people x 22 % / 14 % of 164) landed on its shop and government meters at a unit rate per meter (U_NDOM, U_GOV, L/d); the estates meters stay out of the pool',
    f'future plot sewage = {Q_PER_CAP*1000:.1f} L/d per person (all three streams on the plot, no better place known)',
    'existing plots keep today\'s load; the two industrial estates carry 4,500 and 1,800 workers at 93 L/d, 54 % return, plus any dwelling meters on them at the domestic rate, and no share of the shop pool',
    'ultimate = the year the last settlement fills; growth after that has nowhere to go and is reported as unhoused, not placed',
    'unhoused = growth that found no empty plot anywhere among the receivers (reported, not placed)']})
with pd.ExcelWriter(xl, engine='openpyxl') as xw:
    summ.to_excel(xw, sheet_name='Settlements')
    pop_total.round(2).to_excel(xw, sheet_name='Population by year')   # two decimals: totals are rounded from the unrounded sum
    housed_own.round().to_excel(xw, sheet_name='Housed own growth')
    inflow.round().to_excel(xw, sheet_name='Inflow from overflow')
    unhoused.round().to_excel(xw, sheet_name='Unhoused')
    fill.round(3).to_excel(xw, sheet_name='Fill fraction')
    q.round(1).to_excel(xw, sheet_name='Qadf by year m3d')
    P[YEARS].round().to_excel(xw, sheet_name='Workbook projection')
    spill_tab.to_excel(xw, sheet_name='Overflow routes', index=False)
    rules.to_excel(xw, sheet_name='Rules', index=False)
# the report tables: five-year steps to saturation (blank once full, the saturation year and value last), and the occupancy table
def _five(tab, nd):
    yrs = [BASE] + [y for y in range(2025, 2101, 5) if y <= ult]; out = []
    order = sorted(tab.index, key=lambda s: -float(tab.at[s, BASE]))
    for s in order:
        sat = sat_year.get(s); r = [s]
        for y in yrs: r.append(round(float(tab.at[s, y]), nd) if (sat is None or y <= sat) else None)
        r += [sat, round(float(tab.at[s, sat]), nd) if sat else None]; out.append(r)
    out.append(['TOTAL'] + [round(float(tab[y].sum()), nd) for y in yrs] + [ult, round(float(tab[ult].sum()), nd)])   # rounded from the unrounded sum, as every total in the report
    return pd.DataFrame(out, columns=['Settlement'] + [str(y) for y in yrs] + ['Saturation year', 'Saturation value'])
occ = st[['OR_RAW', 'OR_S', 'SMALL', 'PPP_RAW', 'PROPS_PER_BUILT_PLOT', 'HOME_SHARE_RAW', 'HOME_SHARE', 'EMPTY_PLOTS', 'FUT_CAP_PLOTS', 'FUT_CAP_POP']].copy()
with pd.ExcelWriter(xl, engine='openpyxl', mode='a', if_sheet_exists='replace') as xw:
    _five(pop_total, 0).to_excel(xw, sheet_name='Five-year to saturation', index=False)
    _five(q, 1).to_excel(xw, sheet_name='Five-year Qadf', index=False)
    occ.to_excel(xw, sheet_name='Occupancy')
print('excel:', xl)

# ---------- design-year columns on the plots and the settlements ----------
# spread: each settlement's housed new people go over ALL its empty plots <= 2,000 m2 (not grove / industrial / heritage / estate) by area capped at 1,000 m2
wsum = plots.groupby('SETTLE')['SPREAD_W'].sum()
for y, tag in [(2030, '2030'), (2055, '2055'), (ult, 'ULT')]:
    h_s = plots['SETTLE'].map(housed[y]).fillna(0.0); w_s = plots['SETTLE'].map(wsum).replace(0, np.nan)
    newpop = (h_s * plots['SPREAD_W'] / w_s).fillna(0.0)
    plots[f'POP_{tag}'] = (plots['POP'] + newpop).round(4)   # four decimals: thousands of equal shares must not round the same way
    plots[f'Q_{tag}'] = (plots['QADF'] + newpop * Q_PER_CAP).round(4)
plots['SAT_YEAR'] = plots['SETTLE'].map(pd.Series(sat_year)).fillna(0).astype(int)
plots['ULT_YEAR'] = ult
def narrow_schema(df):
    ints = ['Moh_Classi', 'N_ACC', 'N_DOM', 'N_DOMADD', 'N_COM', 'N_GOV', 'N_AGR', 'N_CRT', 'N_IND', 'G_DOM', 'G_NDOM', 'G_GOV', 'G_SPEC', 'G_AGR', 'FUT_CAP', 'SAT_YEAR', 'ULT_YEAR', 'HOMESHAPE']
    props = {}
    for c in df.columns:
        if c == 'geometry': continue
        if c in ints: df[c] = df[c].fillna(0).astype(int); props[c] = 'int:6'
        elif df[c].dtype.kind == 'f':
            props[c] = 'float:12.1' if c == 'AREA_M2' else ('float:11.4' if c in ('POP_2030', 'POP_2055', 'POP_ULT', 'WORKERS', 'POP', 'OR_S') else ('float:10.2' if c in () else ('float:9.1' if c in ('GREEN_M2', 'U_NDOM', 'U_GOV') else ('float:6.3' if c in ('FUT_PROPS', 'NDVI_MEAN', 'NDVI_SHARE', 'COMPACT', 'PPP_S', 'HOMESH_S') else ('float:7.2' if c in ('ASPECT', 'SPREAD_W') else 'float:10.4')))))
        else: props[c] = f'str:{max(int(df[c].astype(str).str.len().max()), 1)}'
    return {'geometry': 'Polygon', 'properties': props}
plots.to_file(f"{W13}/shp/PLOTS_load.shp", schema=narrow_schema(plots), encoding='utf-8', engine='fiona')   # narrow widths: 35 MB, not 117
# ---------- the settlement layer: one row per settlement with everything the report and the workbook say about it ----------
S = pd.DataFrame(index=st.index)
S['AREA_KM2'] = (sett.geometry.area / 1e6).round(3)
for a, b in [('WB_2024', 'WB_2024'), ('PROPS', 'PROPS'), ('OR_RAW', 'OR_RAW'), ('OR_S', 'OR_S'), ('SMALL', 'SMALL'), ('PPP_RAW', 'PPP_RAW'), ('PPP_S', 'PROPS_PER_BUILT_PLOT'),
             ('HOMESH_RAW', 'HOME_SHARE_RAW'), ('HOMESH_S', 'HOME_SHARE'), ('BUILT_PL', 'BUILT_PLOTS'), ('EMPTY_PL', 'EMPTY_PLOTS'), ('HOME_MEAS', 'DOM_PLOTS_BUILT'),
             ('CAP_PLOTS', 'FUT_CAP_PLOTS'), ('CAP_POP', 'FUT_CAP_POP'), ('G_NDOM', 'NDOM_METERS'), ('NDOM_POOL', 'NDOM_POOL'), ('G_GOV', 'GOV_METERS'), ('GOV_POOL', 'GOV_POOL'),
             ('G_AGR', 'AGR_METERS'), ('G_SPEC', 'SPEC_METERS'), ('WORKERS', 'WORKERS'), ('U_NDOM', 'U_NDOM'), ('U_GOV', 'U_GOV'), ('POP_2024', 'POP_TODAY'),
             ('W_DOM', 'W_DOM'), ('W_NDOM', 'W_NDOM'), ('W_GOV', 'W_GOV'), ('W_SPEC', 'W_SPEC'), ('W_TOT', 'W_TOT'),
             ('S_DOM', 'S_DOM'), ('S_NDOM', 'S_NDOM'), ('S_GOV', 'S_GOV'), ('S_SPEC', 'S_SPEC'), ('Q_2024', 'Q_2024')]:
    S[a] = st[b]
for y in [y for y in range(2025, 2101, 5) if y <= ult]:
    S[f'POP_{y}'] = pop_total[y].round(); S[f'Q_{y}'] = q[y].round(1)
S['POP_ULT'] = pop_total[ult].round(); S['Q_ULT'] = q[ult].round(1)
S['SAT_YEAR'] = pd.Series(sat_year).fillna(0).astype(int)
S['SAT_POP'] = pd.Series({s: (pop_total.at[s, sat_year[s]] if sat_year[s] else pop_total.at[s, ult]) for s in st.index}).round()
S['SAT_Q'] = pd.Series({s: (q.at[s, sat_year[s]] if sat_year[s] else q.at[s, ult]) for s in st.index}).round(1)
S['SAT_OWN'] = pd.Series(sat_own).fillna(0).astype(int)          # 0 = not before 2100 on its own growth
S['IN_PEOPLE'] = inflow[ult].round(); S['OUT_PEOPLE'] = out_people.round(); S['MAIN_TO'] = main_to
S['INSHARE'] = (inflow[ult] / cap.replace(0, np.nan)).fillna(0).round(3)
S['ULT_YEAR'] = ult; S['WB_2100'] = P[2100].round(); S['UNHOUSED'] = unhoused[2100].round()
for c in ['SMALL', 'BUILT_PL', 'EMPTY_PL', 'HOME_MEAS', 'CAP_PLOTS', 'G_NDOM', 'NDOM_POOL', 'G_GOV', 'GOV_POOL', 'G_AGR', 'G_SPEC', 'PROPS']:
    S[c] = S[c].fillna(0).astype(int)
out = gpd.GeoDataFrame(S.reset_index(), geometry=sett.geometry.reindex(S.index).values, crs=sett.crs)
for ext in ('.shp', '.shx', '.dbf', '.prj', '.cpg'):
    f = f"{W13}/shp/Settlements_merged{ext}"
    if os.path.exists(f): os.remove(f)
out.to_file(f"{W13}/shp/Settlements_merged.shp", encoding='utf-8', engine='fiona')
print('settlement layer:', len(out), 'rows,', len(out.columns) - 1, 'fields')
print('plot columns written; ultimate year', ult)
