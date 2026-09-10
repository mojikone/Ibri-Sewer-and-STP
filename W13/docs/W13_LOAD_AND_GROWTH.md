# Load per plot and growth to saturation — method and results (W13, 2026-09-09)

Written so the concept report can quote it. Every rule below was set by the engineer on
2026-09-09; the numbers come from the 7 September MoH plot file (77,265 plots), the shifted
electricity meters (33,971) and the inception workbook (`_CLIENT/Ibri Sewer Demand R0 2026 08 03.xlsx`,
sheet *Project Pop Settlements*, 25 settlements, 2023–2100).

Scripts: `W13/py/plots_meters_load.py` (QGIS, steps 1–4) then `W13/py/growth_by_settlement.py` (step 5).
Outputs: `W13/shp/ELE_meters_on_plots.shp`, `W13/shp/PLOTS_load.shp`, `W13/shp/Settlements_merged.shp`,
`W13/analysis/W13_growth_by_settlement.xlsx`; QGIS group *Claude W13 load*.

## 1. Rules

| # | Rule | Source |
|---|---|---|
| 1 | Every dwelling meter (primary, subsidised, additional tariff) is one property; **5.32 people per property** | measured OR, PROJECT-STATE |
| 2 | Water per person: **164 L/d domestic**; non-domestic **0.22 × 164 = 36 L/d**; governmental **0.14 × 164 = 23 L/d**. Never compounded into one rate | G1-p59–61 Tab 11 |
| 3 | Non-domestic and governmental water is a settlement pool from its people, landed on the settlement's shop and government meters in proportion; a settlement with none keeps it on its dwellings | locked basis, PROJECT-STATE §2 1b |
| 4 | Special = the two industrial estates: **4,500 workers Al Tayyeb, 1,800 Tanam**, spread over their industrial plots by area, **93 L/d each** (dry industry) | Tab 12, G1-p61; engineer's assumption |
| 5 | Sewage = **85 %** of domestic water, **54 %** of the rest; farm meters carry no load; large-user (CRT) meters carry the use identified in `CRT_accounts_identified.csv` | Tab 19, G1-p72 |
| 6 | A meter outside every plot snaps to the nearest plot within **15 m**; else it stays free and belongs to the nearest settlement | engineer |
| 7 | Every plot belongs to the settlement outline it lies in, else the nearest; the two AL AYNAYN outlines are one; the merged boundary is the Voronoi partition of plot centroids clipped to the project boundary | engineer |
| 8 | Growth: each settlement grows at its **own rate** from the workbook, applied to its metered population (base 2026) | engineer |
| 9 | Growth fills the settlement's **empty plots ≤ 2,000 m² that are not farm (by meter or NDVI) and not industrial**, at the settlement's own **properties per pure home plot**; all empty plots fill together in proportion; empty shapes above 2,000 m² take nothing | engineer |
| 9a | **Plot class, farm first**: any farm meter → Agricultural, never overridden. Then **Sentinel-2 NDVI** (scene 2026-09-09, 10 m, red and near-infrared from the public AWS bucket, `W13/py/ndvi_plots.py`): a grove = **≥ 1,000 m² of pixels at NDVI ≥ 0.30 with mean NDVI ≥ 0.20**, or a small plot ≥ 800 m² that is ≥ 60 % green at mean NDVI ≥ 0.40 → Agricultural unless a ⅔ shop or government majority says otherwise. Palms are evergreen, so one scene is enough. Calibrated on the 489 farm-meter plots (a quarter of them are bare pump sites) and checked on a 64-plot contact sheet (`W13/img/W13_ndvi_contact_sheet_T1000.png`). The old RGB excess-green test put farms on bare land and is kept only as `GREEN_IMG` | engineer, 2026-09-10 |
| 9b | **Then proportion of the plot's meters**: more than ⅔ home → Residential; ≥ ⅔ government → Government; ≥ ⅔ shop → Commercial; in between → mixed. Large-user meters count with their identified use | engineer, evening |
| 9c | **Properties per built plot** from pure home plots only: Residential by rule 9b, built, fewer than 15 dwelling meters | engineer, evening |
| 10 | Overflow goes to the **nearest settlement with spare room among those with 2,000+ people today**; **IBRI → AL ARAQI → AD DARIZ** first | engineer |
| 11 | A future plot's sewage = its people × (164 × 0.85 + 36 × 0.54 + 23 × 0.54) = **171.3 L/d per person**, all on the plot | rules 2, 5 |
| 12 | **Ultimate** = the first year growth finds no empty plot among the receivers; **2080** | result |

Peaking is not a plot property: the network engine sums the plots upstream of each pipe, adds
infiltration per km, and applies Merrimack (>100 properties) or Peltier (G1-p71–72). The STP
takes average, maximum day and peak hour from the same accumulated flow plus tankers and +10 %.

## 2. Today (base 2026)

| | |
|---|---|
| Meters on plots | 30,931 inside, 2,914 snapped (≤ 15 m), 126 free |
| Properties | 22,559 → **120,015 people** (workbook 2026 for the same 25 settlements: ≈ 120,000) |
| Water | 27,354 m³/d |
| **Sewage (Qadf)** | **20,873 m³/d** |
| Plot → settlement | 57,769 inside an outline, 19,496 by nearest |
| Empty plots that can take people | 45,300 of 60,509 future plots (the rest are groves by NDVI, industrial, or shapes > 2,000 m²) |
| Capacity of those plots | **369,172 people** (v1 loose class 407,411; RGB farm test 359,811; meter only 383,443) |

## 3. Growth

| Year | New people housed | Total people | Nowhere to go | Qadf m³/d |
|---|---|---|---|---|
| 2030 | 12,753 | 132,768 | 0 | 23,057 |
| 2055 | 113,021 | 233,036 | 0 | 40,231 |
| **2080 ultimate** | 299,679 | **419,694** | 1,712 | **72,202** |
| 2100 (workbook) | 313,215 | 433,230 | 243,944 | 74,520 |

Settlements fill between 2066 (Hijar) and 2087 (Usaybuq); **Ibri 2067**, Al Araqi 2067, Ad Dariz 2069. Eleven small
settlements never fill by 2100 (they are not receivers). The workbook's 2100 population for the 25
settlements is 690,000; the cadastre as drawn holds 489,000, so 244,000 of the workbook's 2100 people
have no plot — reported, not placed.

**How the class rule moved the answer.** v1 (one shop meter made a plot mixed, a house on a farm made it
residential, ratio from every built plot with a dwelling): capacity 407,000, ultimate 2084. v2 with the RGB
imagery test: 360,000, 2080 — rejected, it put farms on bare land. v3, meter only: 383,000, 2081 — rejected, it
left green groves as homes. **v4, the live one**: farm = farm meter or a grove by Sentinel-2 NDVI, then proportion
(> ⅔ home → Residential, ≥ ⅔ government → Government, ≥ ⅔ shop → Commercial, between → mixed), ratio from pure
home plots with fewer than 15 dwelling meters. 3,399 farms (489 by meter, 2,910 by NDVI); 2,027 of 15,400 built
metered plots change class from v1, 1,363 of them homes that are groves; Ibri's ratio 1.60 → 1.33; capacity
369,000; ultimate 2080. The v1 class is kept in `DERIVED1`; `WHYC` says why (AGR farm meter, GRN NDVI grove,
RES/COM/GOV/RC proportion, EST estate, UNM unmetered); `NDVI_MEAN`, `NDVI_SHARE`, `GREEN_M2` are on every plot.

**The R0 figure of ≈ 49,700 m³/d ultimate was built on connected population and Tier A at OR 6;
this table supersedes it for the concept report and should be reconciled there.**

## 4. Caveats

- Four small settlements show 2–3.5 properties per built plot (Sayh Al Masarrat, Al Jahli, Al
  Akheedar, Al Qali): institutional housing on a few plots. Their empty plots inherit that ratio.
- 19,000 "Residential" plots carry MoH codes 0 or 99, which look unclassified; harmless for the
  load (the class is not used) but weak for a land-use map.
- The 2,000 m² limit and the receiver threshold of 2,000 people are working settings, changeable
  at the top of the two scripts.
- The identified projects that carry no load (Ibri View resort, army camp) are in
  `W13/analysis/IDENTIFIED_PROJECTS.md` §5 for the concept report.
