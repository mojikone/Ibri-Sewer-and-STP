# W18_settlements_2026_2100 - fields

25 settlements, 184 fields, EPSG:32640. Built by `py/settlements_2100.py`.

| Field | Meaning | Unit |
|---|---|---|
| SETTLE | settlement name |  |
| AREA_KM2 | area of the settlement boundary | km² |
| OR | occupancy measured in 2024 (W14, persons per domestic meter; floor 4.0, cap 6.12) | persons/property |
| OR_2026 | the team's 2026 population / existing properties (domestic meters) | persons/property |
| PPP_SAT | properties added per growth plot when the settlement is full (saturation) | properties/plot |
| PPP_2100 | properties added per growth plot by 2100 (= PPP_SAT where full by 2100) | properties/plot |
| PPP_TEAM | the team's residential properties per future plot (MOHUP DATA - NA, column D) | properties/plot |
| CAPACITY | population capacity (team's sheet, column G: total properties x 4.8) | people |
| FULL_YEAR | year the settlement is full on the team's series (0 = not by 2100) | year |
| FULL_TEAM | the team's saturation year (column H) |  |
| N_PLOTS | plots inside the settlement boundary | plots |
| N_EXIST | existing plots inside the boundary | plots |
| N_EMPTY | empty (future) plots inside the boundary | plots |
| EMPTY_PCT | empty plots / all plots, by count | % |
| EMPTY_APCT | empty plots / all plots, by area | % |
| N_GROWTH | growth plots: take the growth flow (future, 200-3,000 m², not odd-shaped, not agricultural, heritage or industrial) | plots |
| N_OUTSIDE | plots of the settlement outside its boundary (no flow) | plots |
| TEAM_PLOTS | the team's future residential plots (column C) | plots |
| PROP_2026 | existing properties (domestic meters 2024) | properties |
| PROP_2100 | properties in 2100: existing + added on growth plots | properties |
| EX_RES ... EX_AGR | existing plots by land use: residential, residential-commercial, commercial, government, industrial, agricultural | plots |
| NA_DOM ... NA_AGR | existing plots with at least one Nama meter of the category: domestic, commercial, government, special, agricultural (a plot can count in more than one) | plots |
| QNC_2031, _2056, _2071 | flow not carried by the network (inactive manhole or over 200 m from a sewer) | m³/d |
| P_2026 ... P_2100 | population (team's series, capped at the capacity) | people |
| Q_2026 ... Q_2100 | average sewage flow, all plots of the settlement (estates included, infiltration not) | m³/d |
