# SC1-2056 at 0.75 %: fewer stations by the engineer's logic

Split as searched: 27 stations (9 new, 5 joined by gravity), 274 manholes deeper than 12 m. Caps: new station <= 12.65 m, outfall <= 14.65 m, no manhole deeper than 16.5 m.

## O3

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 1 new | O3-M1443 11.59 | 11.56 m | 13.61 m | 26 |
| (all new stations removed, not allowed) | 0 new | - | 18.11 m | 19.79 m | 71 |

## O9

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 6 new | O9-M103 11.96, O9-M166 11.96, O9-M72 11.82, O9-M728 11.39, O9-M773 11.95, O9-M89 11.93 | 9.83 m | 16.19 m | 98 |
| O9-M103 + O9-M89 as one at O9-M101 | 5 new | O9-M101 12.63, O9-M166 11.96, O9-M72 11.82, O9-M728 11.39, O9-M773 11.95 | 9.83 m | 16.19 m | 100 |
| drop O9-M728 | 4 new | O9-M101 12.63, O9-M166 11.96, O9-M72 11.82, O9-M773 11.95 | 14.25 m | 16.19 m | 147 |
| (all new stations removed, not allowed) | 0 new | - | 22.56 m | 27.80 m | 253 |

## O12

| step | new stations | station depths, m | outfall | deepest manhole | manholes > 12 m |
|---|---|---|---|---|---|
| as searched | 2 new | O12-M193 11.93, O12-M26 11.93 | 8.73 m | 14.75 m | 2 |
| drop O12-M193 | 1 new | O12-M26 11.93 | 13.66 m | 14.75 m | 16 |
| (all new stations removed, not allowed) | 0 new | - | 14.71 m | 15.42 m | 39 |

Stations for split_deep_subnetworks.FIXED: {"O9": ["O9-M101", "O9-M166", "O9-M72", "O9-M773"], "O12": ["O12-M26"]}

