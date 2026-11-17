# Splitting the deep subnetworks - SC1-2056, gradients up to 1.00 %

Re-lay check (cover 1.3 m over the soffit, laid gradients): upstream inverts reproduce the design to 0.000 m for 99 % of 19,083 pipes (largest 0.164 m).

Pipes above DN200 steepened to reach 0.75 m/s at the 2031 peak: 1,628 (134.8 km); above DN200 that cannot reach it within 1.00 %: 36.

| | design | steepened, no cut | steepened, cut and joined |
|---|---|---|---|
| manholes deeper than 12 m | 320 | 478 | 241 |
| of which deeper than 12 m for good (to the outfall) | 247 | 351 | 0 |
| deepest manhole | 21.97 m | 29.42 m | 16.17 m |
| pumping stations (the plant inlet not counted) | 23 | 23 | 31 (13 new, 2 moved one manhole up, 6 joined by gravity) |

Deepest manhole left: a dip that comes back to 12 m or less before its outfall (allowed). Manholes deeper than 12 m after: 241.

Cuts:
- O11: new station at O11-M6 (11.0 m deep), 4.9 L/s in 2056, to O11-M5 over 98 m (pipe O11-P6, DN200); round 15
- O12: new station at O12-M26 (11.9 m deep), 7.2 L/s in 2056, to O12-M25 over 100 m (pipe O12-P26, DN200); round 8
- O12: new station at O12-M193 (11.9 m deep), 5.1 L/s in 2056, to O12-M192 over 100 m (pipe O12-P193, DN200); round 12
- O14: new station at O14-M2 (11.9 m deep), 6.9 L/s in 2056, to O14-M1 over 62 m (pipe O14-P2, DN200); round 5
- O20: existing station moved up at O20-M1 (9.8 m deep), 6.5 L/s in 2056, to O20 over 94 m (pipe O20-P1, DN200); round 10
- O23: existing station moved up at O23-M1 (11.8 m deep), 0.4 L/s in 2056, to O23 over 246 m (pipe O23-P1, DN200); round 14
- O3: new station at O3-M1462 (11.7 m deep), 14.3 L/s in 2056, to O3-M1461 over 100 m (pipe O3-P1462, DN250); round 1
- O3: new station at O3-M1432 (11.9 m deep), 29.7 L/s in 2056, to O3-M1431 over 100 m (pipe O3-P1432, DN315); round 9
- O9: new station at O9-M2804 (11.9 m deep), 15.7 L/s in 2056, to O9-M2803 over 117 m (pipe O9-P2804, DN250); round 2
- O9: new station at O9-M773 (11.9 m deep), 7.6 L/s in 2056, to O9-M772 over 89 m (pipe O9-P773, DN200); round 3
- O9: new station at O9-M103 (12.0 m deep), 5.1 L/s in 2056, to O9-M102 over 100 m (pipe O9-P103, DN200); round 4
- O9: new station at O9-M89 (11.9 m deep), 6.8 L/s in 2056, to O9-M88 over 103 m (pipe O9-P89, DN200); round 6
- O9: new station at O9-M166 (11.9 m deep), 21.1 L/s in 2056, to O9-M165 over 100 m (pipe O9-P166, DN280); round 7
- O9: new station at O9-M728 (11.4 m deep), 10.4 L/s in 2056, to O9-M727 over 85 m (pipe O9-P728, DN200); round 11
- O9: new station at O9-M69 (11.8 m deep), 21.9 L/s in 2056, to O9-M68 over 105 m (pipe O9-P69, DN280); round 13

Existing stations, gravity join tested (outfall at 12 m or less and the receiving manhole within Table 12 spacing):
- O3 -> O2-M696 (17 m, outfall 11.8 m): joined by gravity - stations 37 -> 36
- O5 -> O4-M1421 (103 m, outfall 11.5 m): joined by gravity - stations 36 -> 35
- O7 -> O6-M93 (62 m, outfall 9.9 m): joined by gravity - stations 35 -> 34
- O2 -> O1-M1519 (43 m, outfall 7.2 m): joined by gravity - stations 34 -> 33
- O6 -> O5-M191 (64 m, outfall 6.9 m): joined by gravity - stations 33 -> 32
- O14 -> O9-M425 (99 m, outfall 5.5 m): joined by gravity - stations 32 -> 31
- O15 -> O1-M2227 (1218 m, outfall 10.5 m): kept as a station - rising main 1218 m > 100 m (Table 12, DN280)
- O11 -> O10-M148 (28 m, outfall 10.5 m): kept as a station - joining leaves 31 stations against 31
- O8 -> O5-M130 (3375 m, outfall 10.3 m): kept as a station - rising main 3375 m > 100 m (Table 12, DN250)
- O21 -> O1-M445 (2032 m, outfall 10.1 m): kept as a station - rising main 2032 m > 120 m (Table 12, DN630)
- O10 -> O9-M1184 (44 m, outfall 9.7 m): kept as a station - joining leaves 31 stations against 31
- O9 -> O1-M2472 (149 m, outfall 9.4 m): kept as a station - rising main 149 m > 120 m (Table 12, DN800)
- O12 -> O11-M96 (66 m, outfall 8.9 m): kept as a station - joining leaves 31 stations against 31
- O19 -> O16-M73 (1101 m, outfall 8.4 m): kept as a station - rising main 1101 m > 100 m (Table 12, DN200)
- O24 -> O1-M445 (510 m, outfall 8.1 m): kept as a station - rising main 510 m > 120 m (Table 12, DN500)
- O4 -> O3-M3205 (666 m, outfall 6.6 m): kept as a station - rising main 666 m > 120 m (Table 12, DN900)
- O20 -> O16-M44 (601 m, outfall 6.0 m): kept as a station - rising main 601 m > 100 m (Table 12, DN200)
- O13 -> O12-M440 (363 m, outfall 3.7 m): kept as a station - rising main 363 m > 100 m (Table 12, DN200)
- O22 -> O21-M559 (2407 m, outfall 1.9 m): kept as a station - rising main 2407 m > 100 m (Table 12, DN200)
- O23 -> O21-M559 (9455 m, outfall nan m): kept as a station - rising main 9455 m > 100 m (Table 12, DN200)
