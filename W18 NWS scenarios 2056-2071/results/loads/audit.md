# W18 audit

44 checks, 44 pass, 0 fail. Built by `py/audit_w18.py` from the raw sources (team workbook, W14 plots, model plots, W14 boundaries); nothing imported from the scripts it checks.

| | check | result | detail |
|---|---|---|---|
| A | sheets | pass | ['MOHUP DATA - NA', 'Team original', 'Average', 'Notes'] |
| A | Average sheet = the team's Average, rows 1-27 x 2026-2100 | pass | max difference 5.82e-11 |
| A | Team original = the team's MOHUP DATA - NA (values, to Excel's 15 figures) | pass | 0 cells differ [] |
| A | persons per new property B29 = 4.8 | pass |  |
| A | every row recomputed from the raw sources (B-O, 25 settlements) | pass | 0 mismatches [] |
| A | total row = sum of the rows | pass | capacity 403,668, team 443,102 |
| A | formula cells hold formulas (not typed values) | pass | 0 typed: [] |
| A | no error values | pass | [] |
| A | population never falls (the COUNTIF saturation year relies on it) | pass |  |
| B | 77,265 plots, row for row with W14 and the model | pass |  |
| B | PLOT_NO unique | pass |  |
| B | STATUS and LANDUSE = the model's | pass |  |
| B | MOH_USE = W14 Classes (MoH file) | pass |  |
| B | CADASTRE = MOH_USE, and the field list says so (the model's name; no cadastre number in the source) | pass | equal on 100.0% of plots |
| B | meters = W14 meters by category; PROP_EX = M_DOM | pass |  |
| B | IN_BOUND recomputed (centroid in own settlement) | pass | 5,907 outside |
| B | GROWTH recomputed from the rule | pass | 43,230 growth plots recomputed, 0 differ |
| B | no NaN or negative people or flow | pass |  |
| B | plots outside their boundary: no people, no flow, every year | pass |  |
| B | existing plots: people and flow fixed at 2026 every year | pass |  |
| B | future plots that do not take growth: no people; flow only the estates' own (constant) | pass | 11,376 plots, 100 estate plots among them, max deviation 0.0e+00 |
| B | no future plot carries a 2024 flow (the 2026 pattern stays on existing plots) | pass | max 0.00e+00 |
| B | existing plots, 2026 people in the W14 resident pattern | pass | max spread of people/W14 resident within a settlement 1.8e-06 |
| B | existing plots, 2026 flow in the 2024 pattern of the model | pass | max spread 3.1e-05 |
| B | existing plots hold the team's 2026 population | pass | max difference 0.009 people |
| B | growth plots: one equal share per settlement and year | pass | max spread 0.0e+00 people |
| B | growth share = (min(team average, capacity) - 2026 population) / growth plots | pass | max error 5.0e-06 people |
| B | growth plots: flow = people x 171.03 L/d | pass | rate 171.028 L/d, max error 5.8e-06 m3/d |
| B | settlement people = min(team average, capacity), every year | pass | max error 0.063 people |
| B | settlement flow = people x rate + estates, every year | pass | max error 0.0714 m3/d |
| B | no settlement above its capacity | pass | max excess 0.023 |
| B | PROP_FUT = people added by 2100 / 4.8; PROPS = PROP_EX + PROP_FUT | pass |  |
| B | growth plots never lose people from one year to the next | pass |  |
| B | largest existing plot (64 properties, Ibri) fixed | pass | 383.1 people, 59.8 m3/d every year |
| C | 25 settlements, the W14 boundaries | pass |  |
| C | P_yyyy and Q_yyyy = sums of the plot layer, 2026-2100 | pass | max 0.050 people, 0.0050 m3/d |
| C | settlement fields recomputed (capacity, years, counts, properties, OR, not carried) and = workbook | pass | 0 mismatches [] |
| D | plot_loads.csv = plot layer in the ten model years | pass | max 5.0e-06 m3/d |
| D | plot_loads.csv growth flag = recomputed rule | pass |  |
| D | not carried = inactive manhole or over 200 m (and nothing else) | pass |  |
| D | manhole_loads.csv = carried plot flow summed per manhole | pass | 15,482 manholes, max 2.5e-04 m3/d; carried 2056 37,892.2, 2071 46,809.6 |
| D | settlement_flows.csv capacity = recomputed capacity | pass | max 5.0e-05 |
| E | zip layers and workbook = the files on disk | pass | stale or missing: [] |
| E | project inside the zip reads ./layers only | pass |  |
