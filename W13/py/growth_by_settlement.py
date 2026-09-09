# W13 — growth per settlement, year by year to saturation (step 5 of 2026-09-09). Plain python, run after plots_meters_load.py.
#
# Rules (engineer, 2026-09-09):
#   today's people = dwelling meters x 5.32; each settlement grows at its own RATE from the inception workbook (Project Pop Settlements)
#   growth fills the settlement's empty plots (<= 2,000 m2, not farm / industrial / proposed) at its own properties-per-built-plot, all together in proportion
#   when a settlement is full the overflow goes to the nearest settlement with spare room, among those with 2,000+ people today;
#   IBRI overflows to AL ARAQI first, then AD DARIZ
#   per person: 164 L/d domestic, 0.22 x 164 non-domestic, 0.14 x 164 governmental; sewage 85 % / 54 %
import pandas as pd, numpy as np, geopandas as gpd, openpyxl, math, os
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W13"
WB = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/_CLIENT/Ibri Sewer Demand R0 2026 08 03.xlsx"
OR, LPCD, R_ND, R_GOV, RET_DOM, RET_ND = 5.32, 164.0, 0.22, 0.14, 0.85, 0.54
BASE = 2026; YEARS = list(range(BASE, 2101)); DESIGN = [2030, 2055]
Q_PER_CAP = LPCD * (RET_DOM + R_ND * RET_ND + R_GOV * RET_ND) / 1000.0     # m3/d per person on a future plot (all three streams)
BIG = 2000.0; RECEIVER_MIN_POP = 2000.0; SPILL = {'IBRI': ['AL ARAQI', 'AD DARIZ']}

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
growth = P.div(P[BASE], axis=0)                                            # rate relative to 2026
pop0 = st['POP_TODAY'].astype(float); cap = st['FUT_CAP_POP'].astype(float)
demand = growth[YEARS].mul(pop0, axis=0).sub(pop0, axis=0).clip(lower=0)   # cumulative new people wanting a home in s

# receivers by distance, big settlements only
order = {}
for s in st.index:
    pref = list(SPILL.get(s, []))
    cands = [r for r in st.index if r != s and r not in pref and pop0[r] >= RECEIVER_MIN_POP]
    cands.sort(key=lambda r: cent[s].distance(cent[r]))
    order[s] = pref + cands

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
        for r in order[s]:
            if need <= 1e-9: break
            spare = cap[r] - own_c[r] - in_c[r] - (demand[r][YEARS[-1]] - own_c[r] if False else 0)
            take = min(need, max(spare, 0.0))
            if take > 0: in_c[r] += take; pair_c[(s, r)] = pair_c.get((s, r), 0.0) + take; need -= take
        un_c[s] += need
    housed_own[y] = own_c.values; inflow[y] = in_c.values; unhoused[y] = un_c.values
    for k, v in pair_c.items(): inflow_from.setdefault(k, {})[y] = v
housed = housed_own + inflow
fill = housed.div(cap.replace(0, np.nan), axis=0).fillna(0.0).clip(upper=1.0)
sat_year = {s: next((y for y in YEARS if cap[s] > 0 and housed.at[s, y] >= cap[s] - 0.5), None) for s in st.index}
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
xl = f"{W13}/analysis/W13_growth_by_settlement.xlsx"
summ = pd.DataFrame({'pop_today_meters': pop0.round(), 'workbook_2026': P[BASE].round(), 'props_per_built_plot': st['PROPS_PER_BUILT_PLOT'],
                     'cap_plots': st['FUT_CAP_PLOTS'], 'cap_people': cap.round(), 'saturation_year': pd.Series(sat_year),
                     'pop_2030': pop_total[2030].round(), 'pop_2055': pop_total[2055].round(), f'pop_{ult}_ultimate': pop_total[ult].round(), 'pop_2100': pop_total[2100].round(),
                     'inflow_at_ultimate': inflow[ult].round(), 'unhoused_2100': unhoused[2100].round(),
                     'Qadf_today_m3d': q0.round(1), 'Qadf_2030': q[2030].round(1), 'Qadf_2055': q[2055].round(1), f'Qadf_{ult}_ultimate': q[ult].round(1), 'Qadf_2100': q[2100].round(1)})
spill_tab = pd.DataFrame([{'from': k[0], 'to': k[1], **{y: round(v.get(y, 0)) for y in DESIGN + [ult, 2100]}} for k, v in inflow_from.items()])
rules = pd.DataFrame({'rule': [
    f'base year {BASE}: today = dwelling meters x {OR} people (primary, subsidised and additional tariffs)',
    'each settlement grows at its own rate from the inception workbook sheet "Project Pop Settlements", applied to the metered population',
    f'growth fills the settlement\'s empty plots (<= {BIG:.0f} m2, not Agricultural / Industrial / Proposed class) at its own properties per built plot; all empty plots fill together in proportion',
    f'overflow goes to the nearest settlement with spare room among those with {RECEIVER_MIN_POP:.0f}+ people today; IBRI -> AL ARAQI -> AD DARIZ first',
    f'water per person: {LPCD} L/d domestic, {R_ND} x {LPCD} non-domestic, {R_GOV} x {LPCD} governmental (never compounded); sewage {RET_DOM} / {RET_ND}',
    f'future plot sewage = {Q_PER_CAP*1000:.1f} L/d per person (all three streams on the plot, no better place known)',
    'existing plots keep today\'s load; the two industrial estates carry 4,500 and 1,800 workers at 93 L/d, 54 % return',
    'ultimate = the first year growth finds no empty plot among the receivers (big settlements full); else the year the last settlement fills; else 2100',
    'unhoused = growth that found no empty plot anywhere among the receivers (reported, not placed)']})
with pd.ExcelWriter(xl, engine='openpyxl') as xw:
    summ.to_excel(xw, sheet_name='Settlements')
    pop_total.round().to_excel(xw, sheet_name='Population by year')
    housed_own.round().to_excel(xw, sheet_name='Housed own growth')
    inflow.round().to_excel(xw, sheet_name='Inflow from overflow')
    unhoused.round().to_excel(xw, sheet_name='Unhoused')
    fill.round(3).to_excel(xw, sheet_name='Fill fraction')
    q.round(1).to_excel(xw, sheet_name='Qadf by year m3d')
    P[YEARS].round().to_excel(xw, sheet_name='Workbook projection')
    spill_tab.to_excel(xw, sheet_name='Overflow routes', index=False)
    rules.to_excel(xw, sheet_name='Rules', index=False)
print('excel:', xl)

# ---------- design-year columns on the plots and the settlements ----------
ff = fill.T   # years x settlements
for y, tag in [(2030, '2030'), (2055, '2055'), (ult, 'ULT')]:
    f_s = plots['SETTLE'].map(ff.loc[y]).fillna(0.0)
    newpop = plots['FUT_PROPS'] * OR * f_s * (plots['FUT_CAP'] == 1)
    plots[f'POP_{tag}'] = (plots['POP'] + newpop).round(2)
    plots[f'Q_{tag}'] = (plots['QADF'] + newpop * Q_PER_CAP).round(4)
plots['SAT_YEAR'] = plots['SETTLE'].map(pd.Series(sat_year)).fillna(0).astype(int)
plots['ULT_YEAR'] = ult
plots.to_file(f"{W13}/shp/PLOTS_load.shp", encoding='utf-8')
for y, tag in [(2030, '2030'), (2055, '2055'), (ult, 'ULT')]:
    sett[f'POP_{tag}'] = pop_total[y].round(); sett[f'Q_{tag}'] = q[y].round(1)
sett['SAT_YEAR'] = pd.Series(sat_year).fillna(0).astype(int); sett['ULT_YEAR'] = ult
sett.reset_index().to_file(f"{W13}/shp/Settlements_merged.shp", encoding='utf-8')
print('plot columns written; ultimate year', ult)
