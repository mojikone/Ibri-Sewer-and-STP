# SC1-2056 at 0.50 %: fewer stations by the engineer's logic

Split as searched: 25 stations (7 new, 5 joined by gravity), 231 manholes deeper than 12 m. Caps: new station <= 14.65 m, outfall <= 14.65 m, no manhole deeper than 16.5 m.

## O9

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 5 new | O9-M103 11.96, O9-M166 11.96, O9-M728 11.39, O9-M773 11.95, O9-M89 11.93 | 9.56 m | 16.14 m | 97 |
| O9-M728 + O9-M103 as one at O9-M5 | 4 new | O9-M166 11.96, O9-M5 14.15, O9-M773 11.95, O9-M89 13.74 | 8.68 m | 16.14 m | 153 |
| O9-M773 + O9-M5 as one at O9-M763 | 3 new | O9-M166 11.96, O9-M763 13.61, O9-M89 13.74 | 10.89 m | 16.14 m | 122 |
| (all new stations removed, not allowed) | 0 new | - | 22.51 m | 23.68 m | 253 |

## O12

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 2 new | O12-M193 11.93, O12-M26 11.93 | 8.73 m | 14.75 m | 2 |
| engineer's decision | 0 new | - | 14.63 m | 15.42 m | 39 |

Stations for split_deep_subnetworks.FIXED: {"O9": ["O9-M166", "O9-M763", "O9-M89"], "O12": []}

