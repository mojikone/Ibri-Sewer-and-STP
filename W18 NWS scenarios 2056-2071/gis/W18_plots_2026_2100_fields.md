# W18_plots_2026_2100 - field dictionary

Plots of the model (the W14 plot set, 77,265, row for row with the model's plot layer), EPSG:32640.
Load basis: the team's settlement population (mean of NCSI, meters x 4.8 and APSR), each settlement capped at its
capacity (2026 population + growth plots x the team's properties per plot x 4.8); 171.03 L/person/day; no
infiltration (the model adds 720 L/day/km). The 2026 flow sits
on the existing plots in their 2024 pattern (homes, shops and government on their own plots); everything above 2026
is shared equally by the growth plots. The two industrial estates (316.4 m3/d) are added on their plots every year.

| field | meaning | unit |
|---|---|---|
| PLOT_NO | plot number of the model's plot layer | |
| CADASTRE | MoH planned use, under the name the model's plot layer gives it (identical to MOH_USE; the source holds no cadastre number) | |
| SETTLE | settlement the plot belongs to | |
| AREA_M2 | plot area | m2 |
| STATUS | Existing (built or metered in 2024) or Future (empty) | |
| LANDUSE | plot use: Residential, Residential-Commercial, Commercial, Government, Industrial, Agricultural, Heritage, Empty (unmetered) - from the meters on the plot, farms by meter or satellite grove test | |
| MOH_USE | MoH planned use of the plot | |
| M_DOM | domestic meters (primary, subsidised and additional tariffs) | meters |
| M_COM | commercial meters (shops, offices; large users identified as commercial) | meters |
| M_GOV | government meters (including large users identified as government) | meters |
| M_SPEC | special meters (the two industrial estates) | meters |
| M_AGR | farm meters (no sewage load) | meters |
| PROP_EX | existing properties, 2024 (= M_DOM) | properties |
| PROP_FUT | properties added on the plot by 2100: people added / 4.8 | properties |
| PROPS | PROP_EX + PROP_FUT | properties |
| IN_BOUND | 1 = centroid inside its own settlement's boundary; 0 = outside, takes no people and no flow | |
| GROWTH | 1 = growth plot: future, any zoning but agricultural, heritage (Tourism) or industrial, 200-3,000 m2, not odd-shaped (compact >= 0.6, aspect <= 3), not agricultural (zoned or grove), heritage, industrial or estate, inside its boundary | |
| NETWORK | connected; inactive manhole (planted areas, outlying catchments); over 200 m from a sewer - the last two are not carried by the network | |
| MH_W18 | manhole the plot loads in the model | |
| POP_yyyy | residents on the plot, every year 2026-2100 | people |
| Q_yyyy | average dry-weather sewage, every year 2026-2100 (unpeaked, no infiltration) | m3/d |

Residents and flow differ on purpose: on a growth plot Q = POP x 171.03 L/d; on an existing plot Q also carries the
plot's shops, offices and estate workers, who are not residents, so a shop has flow and no residents.
A settlement stops growing the year its people reach its capacity; Ibri is full in 2063.
