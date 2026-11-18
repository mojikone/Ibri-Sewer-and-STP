# SC4-2051 at 0.75 %: fewer stations by the engineer's logic

Split as searched: 27 stations (10 new, 5 joined by gravity), 244 manholes deeper than 12 m. Caps: new station <= 14.65 m, outfall <= 14.65 m, no manhole deeper than 16.5 m.

## O3

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 2 new | O3-M1410 11.18, O3-M1449 11.66 | 11.59 m | 13.64 m | 18 |
| O3-M1449 + O3-M1410 as one at O3-M1446 | 1 new | O3-M1446 12.80 | 11.59 m | 13.64 m | 21 |
| (all new stations removed, not allowed) | 0 new | - | 19.94 m | 21.65 m | 68 |

## O9

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 6 new | O9-M103 11.96, O9-M166 11.93, O9-M72 11.97, O9-M728 11.39, O9-M773 11.95, O9-M89 11.93 | 9.70 m | 15.98 m | 97 |
| O9-M728 + O9-M103 as one at O9-M5 | 5 new | O9-M166 11.93, O9-M5 13.97, O9-M72 11.97, O9-M773 11.95, O9-M89 13.74 | 8.66 m | 15.98 m | 153 |
| O9-M773 + O9-M5 as one at O9-M763 | 4 new | O9-M166 11.93, O9-M72 11.97, O9-M763 13.61, O9-M89 13.74 | 10.78 m | 15.98 m | 121 |
| (all new stations removed, not allowed) | 0 new | - | 22.40 m | 27.28 m | 253 |

## O12

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 2 new | O12-M193 11.93, O12-M26 11.93 | 8.73 m | 14.75 m | 2 |
| engineer's decision | 0 new | - | 14.71 m | 15.42 m | 39 |

Stations for split_deep_subnetworks.FIXED: {"O3": ["O3-M1446"], "O9": ["O9-M166", "O9-M72", "O9-M763", "O9-M89"], "O12": []}

