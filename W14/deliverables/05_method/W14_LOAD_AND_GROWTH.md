# Load per plot and growth to saturation — method and results (W14, class v7, 2026-09-10)

Written so the concept report can quote it. Every rule below was set by the engineer on
2026-09-09; the numbers come from the 7 September MoH plot file (77,265 plots), the shifted
electricity meters (33,971) and the inception workbook (`_CLIENT/Ibri Sewer Demand R0 2026 08 03.xlsx`,
sheet *Project Pop Settlements*, 25 settlements, 2023–2100).

Scripts: `W14/py/plots_meters_load.py` (QGIS, steps 1–4) then `W14/py/growth_by_settlement.py` (step 5).
Outputs: `W14/shp/ELE_meters_on_plots.shp`, `W14/shp/PLOTS_load.shp`, `W14/shp/Settlements_merged.shp`,
`W14/analysis/W14_growth_by_settlement.xlsx`; QGIS group *Claude W13 load*.

## 1. Rules

| # | Rule | Source |
|---|---|---|
| 1 | Every dwelling meter (primary, subsidised, additional tariff) is one property. **Occupancy per settlement** = workbook population **2024** (the accounts' year and the report's base) ÷ metered properties, **floored at 4.0, capped at 6.12** (Bat's, the highest among settlements with 2,000+ people): Ibri 6.07, Ad Dariz 4.86, Al Araqi 4.34; ten settlements are lifted by the floor, none is cut by the cap (Bat sets it). **A settlement under 1,000 people in 2024 takes 4.0 outright, one property per plot and a home share of 0.9** — it has too few meters to measure on and does not attract second dwellings (13 settlements, At Tayyib's 4.02 at 3,300 people being the reference). The single 5.32 is superseded | engineer, 2026-09-10 |
| 2 | Water per person: **164 L/d domestic**; non-domestic **0.22 × 164 = 36 L/d**; governmental **0.14 × 164 = 23 L/d**. Never compounded into one rate | G1-p59–61 Tab 11 |
| 3 | Non-domestic and governmental water is a settlement pool from its people, landed on the settlement's shop and government meters in proportion; a settlement with none keeps it on its dwellings | locked basis, PROJECT-STATE §2 1b |
| 4 | Special = the two industrial estates: **4,500 workers Al Tayyeb, 1,800 Tanam**, spread over their industrial plots by area, **93 L/d each** (dry industry) | Tab 12, G1-p61; engineer's assumption |
| 5 | Sewage = **85 %** of domestic water, **54 %** of the rest; farm meters carry no load; large-user (CRT) meters carry the use identified in `CRT_accounts_identified.csv` | Tab 19, G1-p72 |
| 6 | A meter outside every plot snaps to the nearest plot within **15 m**; else it stays free and belongs to the nearest settlement | engineer |
| 7 | Every plot belongs to the settlement outline it lies in, else the nearest; the two AL AYNAYN outlines are one; the merged boundary is the **Voronoi partition of plot centroids, dissolved by settlement, clipped to the project boundary, shared edges smoothed as a coverage** — no gaps, no overlaps (`W14/py/settlements_partition.py`) | engineer |
| 8 | Growth: each settlement grows at its **own rate** from the workbook, applied to its metered population (base **2024**) | engineer |
| 9 | **Empty plots, capacity**: a settlement's capacity = its **home-shaped empty plots** (200–1,000 m², compactness ≥ 0.6 against the rotated bounding box, aspect ≤ 3; not grove, industrial, heritage or estate) × its **home share** (pure homes among its built, metered, home-shaped plots; Ibri 0.87) × its **properties per home plot** × its **occupancy** (rule 1); a settlement under 1,000 people takes one property per plot and a home share of 0.9. Slivers under 200 m², odd shapes and everything above 1,000 m² are not counted as homes | engineer, 2026-09-10 |
| 9d | **Empty plots, spread**: the people a settlement houses each year are spread over **all** its empty plots up to 2,000 m² (not grove, industrial, heritage or estate) **by plot area capped at 1,000 m²**, so every plot the network passes carries a load and the totals stay consistent with the capacity; a 50 m² sliver takes a twentieth of a plot's share; shapes above 2,000 m² take nothing | engineer, 2026-09-10 |
| 9e | **Heritage**: the 177 MoH "Tourism" plots, the ruined old quarter of Ibri by the fort, take nothing | engineer, 2026-09-10 |
| 9a | **Plot class, farm first**: any farm meter → Agricultural, never overridden. Then **Sentinel-2 NDVI** (scene 2026-09-09, 10 m, red and near-infrared from the public AWS bucket, `W14/py/ndvi_plots.py`): a grove = **≥ 1,000 m² of pixels at NDVI ≥ 0.30 with mean NDVI ≥ 0.20**, or a small plot ≥ 800 m² that is ≥ 60 % green at mean NDVI ≥ 0.40 → Agricultural unless ≥ ⅔ shop meters or a simple government majority says otherwise. Palms are evergreen, so one scene is enough. Calibrated on the 489 farm-meter plots (a quarter of them are bare pump sites) and checked on a 64-plot contact sheet (`W14/img/W13_ndvi_contact_sheet_T1000.png`). The old RGB excess-green test put farms on bare land and is kept only as `GREEN_IMG` | engineer, 2026-09-10 |
| 9b | **Then proportion of the plot's meters**: more than ⅔ home → Residential; ≥ ⅔ government → Government; ≥ ⅔ shop → Commercial; in between → mixed. Large-user meters count with their identified use | engineer, evening |
| 9c | **Properties per built plot** from pure home plots only: Residential by rule 9b, built, fewer than 15 dwelling meters | engineer, evening |
| 10 | Overflow: **Ibri in parallel to Al Araqi 70 %, Al Qurayn 20 %, Shalashil 10 %; when those are full, Ad Dariz**; then the nearest settlement with spare room, any size (a person who knows the area, via the engineer, 2026-09-10). At Tayyib overflows to Miayrid first. Other settlements: nearest with spare room, any size — **every settlement receives, so all 25 saturate** | engineer |
| 11 | A future plot's sewage = its people × (164 × 0.85 + 36 × 0.54 + 23 × 0.54) = **171.3 L/d per person**, all on the plot | rules 2, 5 |
| 12 | **Ultimate** = the year the last settlement fills; **2070** | result |
| 13 | **Growth series**: the Inception Report's, used for its rates only — NCSI census forecast to 2040 (Omani and expatriate separately), extrapolation 2041–2050 (technical note), constant 2.40 %/yr from 2060 to 2100 (ramp 2.19 → 2.40 over 2051–2060); settlements are fixed shares of the wilayat (183,564 in 2024). Decade means 2.60 / 2.51 / 2.05 / 2.33 / 2.40 %. Its 2100 total (691,264 for the 25) is not a saturation figure | Inception Report §6, workbook |

Peaking is not a plot property: the network engine sums the plots upstream of each pipe, adds
infiltration per km, and applies Merrimack (>100 properties) or Peltier (G1-p71–72). The STP
takes average, maximum day and peak hour from the same accumulated flow plus tankers and +10 %.

## 2. Today (base 2024)

| | |
|---|---|
| Meters on plots | 30,931 inside, 2,914 snapped (≤ 15 m), 126 free |
| Properties | 22,559 → **119,886 people** with the per-settlement occupancy (workbook 2024 for the 25: 116,452; the floor at 4.0 and the under-1,000 rule add 3,434 net) |
| Water | 27,325 m³/d |
| **Sewage (Qadf)** | **20,851 m³/d** |
| Plot → settlement | 57,769 inside an outline, 19,496 by nearest |
| Empty plots | 60,509; **46,109 home-shaped** count for capacity; 54,163 (all up to 2,000 m² except groves, industrial, heritage) receive the spread; slivers under 270 m² are 10 % of the plots but 1.3 % of the spread weight |
| Capacity | **229,133 people** (v6 before the under-1,000 rule: 247,671; at 5.32 everywhere: 274,565; all empty plots ≤ 2,000 m² at the ratio, v4: 369,172; v1 loose class: 407,411) |

## 3. Growth

| Year | New people housed | Total people | Nowhere to go | Qadf m³/d |
|---|---|---|---|---|
| 2030 | 19,641 | 139,527 | 0 | 24,215 |
| 2055 | 125,013 | 244,899 | 0 | 42,263 |
| **2070 ultimate** | 229,133 | **349,019** | 333 | **60,097** |
| 2100 (workbook) | 229,133 | 349,019 | 362,625 | 60,097 |

Settlements fill between 2036 (Al Akheedar) and 2070 (Al Wahrah, Al Jibayyah, Suwayda al Ma, Al Ghubayrah, Miayrid); **Ibri 2056**, Al Araqi 2057, Al Qurayn 2060,
Shalashil 2061, Ad Dariz 2062. All 25 fill: every settlement receives its neighbours' overflow. The workbook supplies
growth rates only; its 2100 total is neither a target nor a saturation figure (engineer, 2026-09-10). Saturation
is what the cadastre holds.

**How the class rule moved the answer.** v1 (one shop meter made a plot mixed, a house on a farm made it
residential, ratio from every built plot with a dwelling): capacity 407,000, ultimate 2084. v2 with the RGB
imagery test: 360,000, 2080 — rejected, it put farms on bare land. v3, meter only: 383,000, 2081 — rejected, it
left green groves as homes. **v4, the live one**: farm = farm meter or a grove by Sentinel-2 NDVI, then proportion
(> ⅔ home → Residential, ≥ ⅔ government → Government, ≥ ⅔ shop → Commercial, between → mixed), ratio from pure
home plots with fewer than 15 dwelling meters. 3,399 farms (489 by meter, 2,910 by NDVI); 2,027 of 15,400 built
metered plots change class from v1, 1,363 of them homes that are groves; Ibri's ratio 1.60 → 1.33; capacity
369,000; ultimate 2080. **v5 (2026-09-10, live)**: same classes plus Heritage and the government
majority, capacity from home-shaped plots × home share (rule 9), spread by capped area (rule 9d): capacity
275,000; ultimate 2072. **v6 (2026-09-10 evening, live)**: occupancy per settlement from the 2024 workbook
(floor 4, cap 6.12), base year 2024, Ibri's parallel overspill, every settlement a receiver; capacity 248,000; ultimate 2073. **v7 (2026-09-10 night, live)**: a settlement under 1,000 people in 2024 takes occupancy 4.0, one property per plot and a home share of 0.9 (13 settlements, Al Jahli and Sayh al Masarrat among them); At Tayyib overflows to Miayrid first; capacity 229,133; ultimate 2070, 349,019 people, 60,097 m³/d; Ibri full 2056. The report's five-year tables stop at saturation and carry the saturation year and value; the growth-series provenance, the overflow routes and the saturation year with and without overflow are in the report (14.7, A5, A6, map M10). The v1 class is kept in `DERIVED1`; `WHYC` says why (AGR farm meter, GRN NDVI grove,
RES/COM/GOV/RC proportion, EST estate, UNM unmetered); `NDVI_MEAN`, `NDVI_SHARE`, `GREEN_M2`, `COMPACT`, `ASPECT`, `HOMESHAPE`, `SPREAD_W`, `OR_S` are on every plot.

**The R0 figure of ≈ 49,700 m³/d ultimate was built on connected population and Tier A at OR 6;
this table supersedes it for the concept report and should be reconciled there.**

## 4. Caveats

- Four small settlements show 2–3.5 properties per built plot (Sayh Al Masarrat, Al Jahli, Al
  Akheedar, Al Qali): institutional housing on a few plots. Their empty plots inherit that ratio.
- 19,000 "Residential" plots carry MoH codes 0 or 99, which look unclassified; harmless for the
  load (the class is not used) but weak for a land-use map.
- The 2,000 m² limit and the 1,000-people threshold of the small-settlement rule are working settings, changeable
  at the top of the two scripts.
- The identified projects that carry no load (Ibri View resort, army camp) are in
  `W14/analysis/IDENTIFIED_PROJECTS.md` §5 for the concept report.
