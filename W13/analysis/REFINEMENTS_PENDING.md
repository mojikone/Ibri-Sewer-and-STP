# Refinements on the plot classes and the empty plots (2026-09-10) — APPLIED in class v5 unless marked dropped

Items 1 and 4 and the empty-plot logic (B) went into `plot_class_v2_apply.py` and `growth_by_settlement.py` on 2026-09-10; items 2 and 3 were dropped by the engineer.

| # | Plots | What they are | What to do | Effect |
|---|---|---|---|---|
| 1 | 177 plots, MoH class "Tourism", fids 26027–26203, Ibri old quarter by the fort, E449549 N2570462, 2.3 ha, all empty, no meters | The ruined mud-brick town, cultural heritage | class **Heritage**, takes nothing (today they count as 235 future properties) | Ibri capacity −0.3 %, fill year unchanged |

| 2 | "Future" plots that carry meters | none exist: the September file already sets built/future from the meters | nothing to do | dropped |
| 3 | "Future" plots with a Microsoft building footprint ≥ 40 m² inside and no meter — **1,464 plots**, 1,015 of them in Ibri (`W13/shp/Future_plots_built_candidates.shp`, footprints in `W13/shp/MS_building_footprints_ibri.shp`) | built but unmetered: under construction or not yet connected | mark **built-unmetered**: no load today, fill first in the growth | **dropped by the engineer**: only meters make a plot built; the layer stays in QGIS as a reference |

| 4 | 49 built plots, government meters the largest group but under ⅔, green by NDVI | school grounds, ministry compounds | **government wins on a simple majority** over the NDVI grove test; the farm meter still beats everything | engineer agreed 2026-09-10 |

## B. Empty plots (engineer, 2026-09-10) — applied

1. Capacity per settlement = home-shaped empty plots (200–1,000 m², compact ≥ 0.6, aspect ≤ 3; not grove / industrial / heritage / estate) × home share (pure homes among the settlement's built, metered, home-shaped plots) × properties per home plot × 5.32.
2. Growth at the workbook rate fills that capacity; overflow to the nearest big neighbour; saturation year per settlement.
3. The housed people are spread over ALL the settlement's empty plots up to 2,000 m² (not grove / industrial / heritage / estate) by area capped at 1,000 m². Slivers take a sliver's share (1.3 % of the weight for 10 % of the plots). Shapes above 2,000 m² take nothing.
4. Load per plot per year from the people; the network is sized on saturation (2072); the works on the same yearly totals.
