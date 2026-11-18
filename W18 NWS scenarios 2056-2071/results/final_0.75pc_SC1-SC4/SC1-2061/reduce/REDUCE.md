# SC1-2061 at 0.75 %: fewer stations by the engineer's logic

Split as searched: 27 stations (9 new, 5 joined by gravity), 301 manholes deeper than 12 m. Caps: new station <= 14.65 m, outfall <= 14.65 m, no manhole deeper than 16.5 m.

## O3

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 1 new | O3-M1442 11.27 | 11.94 m | 14.31 m | 42 |
| (all new stations removed, not allowed) | 0 new | - | 18.06 m | 19.81 m | 85 |

## O9

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 6 new | O9-M103 11.96, O9-M167 11.82, O9-M711 11.94, O9-M72 11.95, O9-M773 11.95, O9-M89 11.93 | 10.25 m | 16.34 m | 102 |
| O9-M711 + O9-M103 as one at O9-M6 | 5 new | O9-M167 11.82, O9-M6 13.23, O9-M72 11.95, O9-M773 11.95, O9-M89 13.74 | 8.70 m | 16.34 m | 140 |
| O9-M6 + O9-M773 as one at O9-M763 | 4 new | O9-M167 11.82, O9-M72 11.95, O9-M763 13.61, O9-M89 13.74 | 10.25 m | 16.34 m | 126 |
| (all new stations removed, not allowed) | 0 new | - | 22.19 m | 28.29 m | 255 |

## O12

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 2 new | O12-M193 11.93, O12-M26 11.93 | 8.73 m | 14.75 m | 2 |
| engineer's decision | 0 new | - | 14.71 m | 15.42 m | 39 |

Stations for split_deep_subnetworks.FIXED: {"O9": ["O9-M167", "O9-M72", "O9-M763", "O9-M89"], "O12": []}

