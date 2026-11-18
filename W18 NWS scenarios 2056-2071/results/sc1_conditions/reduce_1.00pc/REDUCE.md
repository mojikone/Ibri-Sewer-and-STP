# SC1-2056 at 1.00 %: fewer stations by the engineer's logic

Split as searched: 29 stations (11 new, 5 joined by gravity), 275 manholes deeper than 12 m. Caps: new station <= 12.65 m, outfall <= 14.65 m, no manhole deeper than 16.5 m.

## O3

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 2 new | O3-M1434 11.85, O3-M1463 11.46 | 11.56 m | 13.61 m | 26 |
| (all new stations removed, not allowed) | 0 new | - | 25.90 m | 27.58 m | 91 |

## O9

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 7 new | O9-M103 11.96, O9-M166 11.96, O9-M2805 11.96, O9-M69 11.86, O9-M728 11.39, O9-M773 11.95, O9-M89 11.93 | 9.83 m | 16.19 m | 99 |
| O9-M103 + O9-M89 as one at O9-M101 | 6 new | O9-M101 12.63, O9-M166 11.96, O9-M2805 11.96, O9-M69 12.64, O9-M728 11.39, O9-M773 11.95 | 9.83 m | 16.19 m | 104 |
| drop O9-M728 | 5 new | O9-M101 12.63, O9-M166 11.96, O9-M2805 11.96, O9-M69 12.64, O9-M773 11.95 | 14.25 m | 16.19 m | 151 |
| (all new stations removed, not allowed) | 0 new | - | 23.66 m | 30.02 m | 266 |

## O12

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 2 new | O12-M193 11.93, O12-M26 11.93 | 8.73 m | 14.75 m | 2 |
| drop O12-M193 | 1 new | O12-M26 11.93 | 13.66 m | 14.75 m | 16 |
| (all new stations removed, not allowed) | 0 new | - | 14.71 m | 15.42 m | 39 |

Stations for split_deep_subnetworks.FIXED: {"O9": ["O9-M101", "O9-M166", "O9-M2805", "O9-M69", "O9-M773"], "O12": ["O12-M26"]}

