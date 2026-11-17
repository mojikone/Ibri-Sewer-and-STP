# Splitting the deep subnetworks - SC1-2056, gradients up to 0.00 %

Re-lay check (cover 1.3 m over the soffit, laid gradients): upstream inverts reproduce the design to 0.000 m for 99 % of 19,083 pipes (largest 0.164 m).

Pipes above DN200 steepened to reach 0.75 m/s at the 2031 peak: 0 (0.0 km); above DN200 that cannot reach it within 0.00 %: 1,664.

| | design | steepened, no cut | steepened, cut and joined |
|---|---|---|---|
| manholes deeper than 12 m | 320 | 320 | 232 |
| of which deeper than 12 m for good (to the outfall) | 247 | 247 | 0 |
| deepest manhole | 21.97 m | 21.97 m | 21.97 m |
| pumping stations (the plant inlet not counted) | 23 | 23 | 21 (6 new, 2 moved one manhole up, 9 joined by gravity) |

Deepest manhole left: a dip that comes back to 12 m or less before its outfall (allowed). Manholes deeper than 12 m after: 232.

Cuts:
- O11: new station at O11-M6 (11.0 m deep), 4.9 L/s in 2056, to O11-M5 over 98 m (pipe O11-P6, DN200); round 8
- O12: new station at O12-M26 (11.9 m deep), 7.2 L/s in 2056, to O12-M25 over 100 m (pipe O12-P26, DN200); round 2
- O12: new station at O12-M193 (11.9 m deep), 5.1 L/s in 2056, to O12-M192 over 100 m (pipe O12-P193, DN200); round 4
- O14: new station at O14-M2 (11.9 m deep), 6.9 L/s in 2056, to O14-M1 over 62 m (pipe O14-P2, DN200); round 1
- O20: existing station moved up at O20-M1 (9.8 m deep), 6.5 L/s in 2056, to O20 over 94 m (pipe O20-P1, DN200); round 6
- O23: existing station moved up at O23-M1 (11.8 m deep), 0.4 L/s in 2056, to O23 over 246 m (pipe O23-P1, DN200); round 7
- O9: new station at O9-M773 (11.9 m deep), 7.6 L/s in 2056, to O9-M772 over 89 m (pipe O9-P773, DN200); round 3
- O9: new station at O9-M166 (11.7 m deep), 21.1 L/s in 2056, to O9-M165 over 100 m (pipe O9-P166, DN280); round 5

Existing stations, gravity join tested (outfall at 12 m or less and the receiving manhole within Table 12 spacing):
- O5 -> O4-M1421 (103 m, outfall 10.9 m): joined by gravity - stations 30 -> 29
- O11 -> O10-M148 (28 m, outfall 9.8 m): joined by gravity - stations 29 -> 28
- O10 -> O9-M1184 (44 m, outfall 9.7 m): joined by gravity - stations 28 -> 27
- O12 -> O11-M96 (66 m, outfall 8.8 m): joined by gravity - stations 27 -> 26
- O7 -> O6-M93 (62 m, outfall 8.3 m): joined by gravity - stations 26 -> 25
- O2 -> O1-M1519 (43 m, outfall 6.8 m): joined by gravity - stations 25 -> 24
- O6 -> O5-M191 (64 m, outfall 6.6 m): joined by gravity - stations 24 -> 23
- O3 -> O2-M696 (17 m, outfall 6.6 m): joined by gravity - stations 23 -> 22
- O14 -> O9-M425 (99 m, outfall 5.5 m): joined by gravity - stations 22 -> 21
- O9 -> O1-M2472 (149 m, outfall 11.1 m): kept as a station - rising main 149 m > 120 m (Table 12, DN800)
- O15 -> O1-M2227 (1218 m, outfall 10.5 m): kept as a station - rising main 1218 m > 100 m (Table 12, DN280)
- O8 -> O5-M130 (3375 m, outfall 10.0 m): kept as a station - rising main 3375 m > 100 m (Table 12, DN250)
- O19 -> O16-M73 (1101 m, outfall 8.4 m): kept as a station - rising main 1101 m > 100 m (Table 12, DN200)
- O21 -> O1-M445 (2032 m, outfall 8.0 m): kept as a station - rising main 2032 m > 120 m (Table 12, DN630)
- O4 -> O3-M3205 (666 m, outfall 6.6 m): kept as a station - rising main 666 m > 120 m (Table 12, DN900)
- O20 -> O16-M44 (601 m, outfall 6.0 m): kept as a station - rising main 601 m > 100 m (Table 12, DN200)
- O24 -> O1-M445 (510 m, outfall 4.3 m): kept as a station - rising main 510 m > 120 m (Table 12, DN500)
- O13 -> O12-M440 (363 m, outfall 3.7 m): kept as a station - rising main 363 m > 100 m (Table 12, DN200)
- O22 -> O21-M559 (2407 m, outfall 1.9 m): kept as a station - rising main 2407 m > 100 m (Table 12, DN200)
- O23 -> O21-M559 (9455 m, outfall nan m): kept as a station - rising main 9455 m > 100 m (Table 12, DN200)
