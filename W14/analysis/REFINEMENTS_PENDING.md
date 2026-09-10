# Refinements on the plot classes and the empty plots (2026-09-10) — APPLIED in class v5 unless marked dropped

Items 1 and 4 and the empty-plot logic (B) went into `plot_class_v2_apply.py` and `growth_by_settlement.py` on 2026-09-10; items 2 and 3 were dropped by the engineer.

| # | Plots | What they are | What to do | Effect |
|---|---|---|---|---|
| 1 | 177 plots, MoH class "Tourism", fids 26027–26203, Ibri old quarter by the fort, E449549 N2570462, 2.3 ha, all empty, no meters | The ruined mud-brick town, cultural heritage | class **Heritage**, takes nothing (today they count as 235 future properties) | Ibri capacity −0.3 %, fill year unchanged |

| 2 | "Future" plots that carry meters | none exist: the September file already sets built/future from the meters | nothing to do | dropped |
| 3 | "Future" plots with a Microsoft building footprint ≥ 40 m² inside and no meter — **1,464 plots**, 1,015 of them in Ibri (`W14/shp/Future_plots_built_candidates.shp`, footprints in `W14/shp/MS_building_footprints_ibri.shp`) | built but unmetered: under construction or not yet connected | mark **built-unmetered**: no load today, fill first in the growth | **dropped by the engineer**: only meters make a plot built; the layer stays in QGIS as a reference |

| 4 | 49 built plots, government meters the largest group but under ⅔, green by NDVI | school grounds, ministry compounds | **government wins on a simple majority** over the NDVI grove test; the farm meter still beats everything | engineer agreed 2026-09-10 |

## B. Empty plots (engineer, 2026-09-10) — applied

1. Capacity per settlement = home-shaped empty plots (200–1,000 m², compact ≥ 0.6, aspect ≤ 3; not grove / industrial / heritage / estate) × home share (pure homes among the settlement's built, metered, home-shaped plots) × properties per home plot × 5.32.
2. Growth at the workbook rate fills that capacity; overflow to the nearest big neighbour; saturation year per settlement.
3. The housed people are spread over ALL the settlement's empty plots up to 2,000 m² (not grove / industrial / heritage / estate) by area capped at 1,000 m². Slivers take a sliver's share (1.3 % of the weight for 10 % of the plots). Shapes above 2,000 m² take nothing.
4. Load per plot per year from the people; the network is sized on saturation (2070 in v7); the works on the same yearly totals.

## C. Population base (engineer, 2026-09-10 evening) — applied

1. Occupancy per settlement = workbook population 2024 ÷ metered properties, floor 4.0. Ibri 6.07. Replaces the single 5.32. The load per property moves with it.
2. Base year 2024, the electricity accounts' year and the concept report's base.
3. Ibri overspills in parallel: Al Araqi 70 %, Al Qurayn 20 %, Shalashil 10 %; when full, Ad Dariz; then nearest big settlement (local knowledge, via the engineer).
4. Settlement polygons: pure Voronoi partition, dissolved, clipped, coverage-smoothed; the union with the client's outlines that left gaps is gone.
5. Occupancy also capped at 6.12 (Bat's, the highest among settlements with 2,000+ people); only Satwah, Miayrid, Wadi Al Mankas are touched.
6. Every settlement receives overflow from its nearest neighbour with spare room, whatever its size, so all 25 saturate (2073 in v6, 2070 in v7).
7. Settlements with fewer than 10 built, metered, home-shaped plots (Miayrid, Ash Shiab, Satwah, Usaybuq, Wadi Al Mankas) take the area-wide home share (0.87) and ratio (1.30); Miayrid had none and could never fill. At Tayyib's overflow goes to Miayrid first (engineer). W14 carries this from here; W13 stays as the pipe-laying folder. Superseded for these five by item 8.
8. **Under-1,000 rule (engineer, 2026-09-10 night, class v7)**: a settlement with fewer than 1,000 people in the 2024 workbook takes occupancy 4.0 (At Tayyib, 3,300 people, measures 4.02), one property per home plot and a home share of 0.9, whatever its meters return: too few to measure on, and a village of that size does not attract second dwellings. 13 settlements: Al Akheedar, Al Ghubayrah, Al Jahli, Al Makhtibyah, Al Qali, Al Qurayn, Ash Shiab, Miayrid, Satwah, Sayh al Masarrat, Shalashil, Usaybuq, Wadi al Mankas. Capacity 247,671 → 229,133; ultimate 2073 → 2070 (349,019 people, 60,097 m³/d); Ibri full 2056. The report's Table 28 (A3) shows derived and adopted side by side.
9. **Report R2 additions (2026-09-10)**: the five-year tables (Tables 17 and 19) stop at saturation, blank after a settlement fills, and end with the saturation year and the saturation population or flow; the growth series' provenance (census to 2040, extrapolation to 2050, 2.40 %/yr beyond) in 14.7 with a rate chart; the overflow rule in words, the main routes (≥ 1,000 people) in the body, every route (≥ 50) in A5, the saturation year with and without overflow in A6, and the overflow map (M10, Figure 19).
