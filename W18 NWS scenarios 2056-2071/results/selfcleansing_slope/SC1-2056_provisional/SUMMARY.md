# Gradient for 0.75 m/s at the 2031 peak flow - SC1-2056

Pipes above DN200: 1,840 (151.3 km). Check of the calculation against SewerGEMS at the laid gradient (2031): calc/model velocity median 1.000, 90 % within 0.1 %.

Already at 0.75 m/s at the laid gradient: 164 pipes (8.4 % of length). Cannot reach it at any gradient below 100 % (no flow or too little): 0.

Required gradient of the pipes that fail at the laid gradient, percentiles 10/25/50/75/90: 0.13 % / 0.18 % / 0.33 % / 0.48 % / 0.63 %

Re-lay check with the laid gradients: largest difference from the designed inverts 0.0000 m. Added depth uses up the manhole drops before it is carried on.

| threshold gradient | length reaching 0.75 m/s | pipes steepened | km steepened | largest added depth | added depth at an outfall | manholes deepened > 1 m | manholes > 12 m (now) | deepest manhole |
|---|---|---|---|---|---|---|---|---|
| 0.50 % | 82.8 % | 1,349 | 112.6 | 5.62 m | 5.62 m | 420 | 354 (334) | 23.75 m |
| 0.75 % | 95.1 % | 1,588 | 131.3 | 13.58 m | 9.75 m | 717 | 424 (334) | 28.46 m |
| 1.00 % | 98.4 % | 1,648 | 136.2 | 22.86 m | 19.03 m | 781 | 459 (334) | 29.71 m |
| 1.50 % | 99.5 % | 1,666 | 137.9 | 22.86 m | 19.03 m | 796 | 464 (334) | 29.71 m |
| 2.00 % | 99.6 % | 1,669 | 138.1 | 22.86 m | 19.03 m | 799 | 469 (334) | 29.71 m |
| 3.00 % | 100.0 % | 1,676 | 138.7 | 22.86 m | 19.03 m | 807 | 477 (334) | 29.71 m |
| 4.00 % | 100.0 % | 1,676 | 138.7 | 22.86 m | 19.03 m | 807 | 477 (334) | 29.71 m |

By size, median gradient required (failing pipes):
- 1000 mm: 150 pipes, median 0.12 %, laid median 0.08 %
- 1400 mm: 27 pipes, median 0.08 %, laid median 0.08 %
- 250 mm: 394 pipes, median 0.55 %, laid median 0.38 %
- 280 mm: 164 pipes, median 0.46 %, laid median 0.38 %
- 315 mm: 92 pipes, median 0.40 %, laid median 0.27 %
- 355 mm: 262 pipes, median 0.34 %, laid median 0.27 %
- 450 mm: 55 pipes, median 0.27 %, laid median 0.20 %
- 500 mm: 143 pipes, median 0.30 %, laid median 0.16 %
- 560 mm: 76 pipes, median 0.23 %, laid median 0.16 %
- 630 mm: 109 pipes, median 0.18 %, laid median 0.13 %
- 710 mm: 29 pipes, median 0.18 %, laid median 0.10 %
- 800 mm: 87 pipes, median 0.16 %, laid median 0.09 %
- 900 mm: 88 pipes, median 0.13 %, laid median 0.08 %

## Outfalls and what stays below 0.75 m/s (re-lay with the manhole drops)

| threshold | added depth at outfalls (pumping stations) | plant O1 | still below 0.75 m/s at 2031 |
|---|---|---|---|
| 0.50 % | O9 5.6 m, O3 4.2 m, O21 2.0 m, O24 1.3 m, others < 1 m | unchanged | 327 pipes, 26.1 km = 17.2 % of the length above DN200 (DN250 20.9 km); at 0.50 % their median 2031 velocity is 0.69 m/s |
| 0.75 % | O3 9.8 m, O9 6.2 m, O24 3.0 m, O21 2.0 m | unchanged | 88 pipes, 7.3 km = 4.9 % (almost all DN250); median 0.72 m/s |

## Recommendation for the discussion with NWS (engineer's request, 2026-11-16)

- Threshold gradient **0.50 %**: no pipe above DN200 laid steeper than the DN200 minimum of PAM-GUD-203 Table 11.
  83 % of the length above DN200 then reaches 0.75 m/s at the 2031 peak, for 20 more manholes over 12 m (354 against
  334) and up to 5.6 m more depth at two pumping-station outfalls (O9, O3); the plant inlet does not change.
- Tolerance: **about 17 % of the length above DN200** (26 km, nearly all DN250 head runs at about 0.69 m/s) not reaching
  0.75 m/s in 2031, listed for flushing until the flows grow.
- 0.75 % buys 12 more points of length (95 %) for 70 more manholes over 12 m and up to 9.8 m more depth at O3.
Provisional loads (about 3 % more flow than the final) and SC1 only; rerun on each final scenario with this script.
