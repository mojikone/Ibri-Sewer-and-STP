# W11b STAGE 6 - LEVELS AND SIZES

`W11b-s6_levels-1.0` | contract `W11b-contract-1.0` | written 2026-09-03 14:19

```
W11b-contract-1.0 | criteria w11b.criteria | EPSG:32640

TRACTIVE STRESS tau = 1 Pa - AN ASSUMPTION, NOT A GUIDELINE VALUE. PAM-GUD-203 sec 4.2.2.1 (p27) gives the equation Smin = K tau^1.23 Q^-0.461 and no numeric design tau (GAP-9). At tau = 1.0 Pa the required gradients are the shallowest the method allows, so the pipes are shallower and the stations fewer. If NWS return tau = 2.0 Pa every tractive-governed gradient rises by 2.346x and every level downstream of it changes.

THE TREE AGAINST THE GROUND (philosophy sec 4 - bounded and REPORTED)
  draining against the ground     26.3 % of 1,478.5 km   (389.0 km, 14,783 reaches)
    W11a, the defect being fixed    42.5 % of 1,731.7 km
  cumulative climb                   3,930 m  against 9,473 m of descent
    W11a                             7,061 m
  worst single rise                  10.66 m
  VORTEX DROP SHAFTS                    73   <- THE DIAGNOSTIC
    built by NAMA at Ibri               37
    W11a wanted                     2,449   (philosophy sec 4 says 2,254 - the two live documents disagree, and that is itself a finding)
  backdrops over 0.60 m                   119   total drop 546 m
```

## The headline

| QUANTITY | VALUE | UNIT | NOTE |
|---|---|---|---|
| gravity network published | 1,478.468 | km | 56,227 reaches, 56,930 chambers |
| chambers per km | 38.506 | /km | built 34.23, band 33.29 - 36.76 |
| ADWF levelled | 70,405.494 | m3/d | s4 connections; the project total is 74,701.2 (A-LEV-1) |
| largest peak flow on any gravity reach | 225.630 | L/s | the whole basis of the diameter series |
| largest diameter | 900.000 | mm | series reaches DN2400 - see the diameter table |
| cover, median (length-weighted) | 2.361 | m | built 1.72, band 1.34 - 2.07 |
| deepest excavation | 19.778 | m | the cap is 12 m of cover (G203-p33) |
| VORTEX DROP SHAFTS | 73.000 | - | W11a wanted 2,449; NAMA built 37 in 63.2 km |
| vortex drop shafts per km | 0.049 | /km | built 0.585/km; W11a 1.475/km |
| lifting stations the cap demands | 508.000 | - | LOCATED here with a real duty flow; DESIGNED by s7 |
| length draining against the ground | 26.310 | % | s2/s3's layout, unchanged here. Built 34.1 %, W11a 42.5 % |
| climb divided by descent | 0.415 | - | built 0.483, band <= 0.647; W11a 0.747 |
| reaches below the 1.30 m minimum cover | 0.000 | - | G203-p33 4.6.3; the built network is short on 35.9 % of its length |
| reaches over the d/D limit | 0.000 | - | G203-p27 Table 10; W10 shipped 66, W11a 168 |
| reaches over 3.0 m/s | 0.000 | - | G203-p27 4.2.2.2 |
| reaches laid at the 25 % publishing bound | 182.000 | - | the contract's own range guard on SLOPE_LAID, not a guideline rule - these reaches wanted to be steeper still |
| chambers deepened for a cliff the pipe may not follow | 15.000 | - | philosophy sec 5: hold the gradient and take the difference at a drop chamber - the chamber is at the TOP of the cliff |


## What has to be decided, and by whom

| ID | WHOSE | FINDING | ASK |
|---|---|---|---|
| F1 | stage 2 / 3 - the layout | 281 of the 508 stations the cap demands lift LESS THAN 1 L/s, and 193 of all of them sit on ground that rises along the flow. A lifting station for three properties is not a pumping scheme; it is a lateral pointing the wrong way up a hill. | Re-orient those laterals (stage 2), or decide those plots are served by another system (philosophy sec 8a). Neither is a levelling decision. |
| F2 | THE ENGINEER | 325 chambers stand past the 12 m cap on a philosophy sec 5 exit, the deepest at 19.78 m of cover. They are inside the declared 20 m ceiling (A-LEV-11) and that ceiling is an ASSUMPTION, not a guideline number. | Confirm the ceiling, or set one. At 20 m these stand; tighter and they become stations. `--sweep` prices both. |
| F3 | NWS | 87.9 % of the length is self-cleansing ONLY by the tractive route, which rests on tau = 1 Pa - a number G203-p27 never gives (GAP-9). | Give us tau. At 2.0 Pa every tractive-governed gradient rises 2.346x and every level below it moves; `--sweep` runs it. |
| F4 | NWS | The invert the existing works will accept is unconfirmed, so the 195 terminals were levelled to whatever the network gave them (A-LEV-7). The deepest sits at 17.30 m. | The inlet invert in m aOD. If it is above a terminal, that terminal becomes a station and this stage has to run again. |
| F5 | stage 2 - the corridors | 58.8 km of pipe RUNS ALONG a wadi rather than crossing it, in 337 separate contacts, the longest 1618 m. H1 forbids that outright. And 3,365 chambers stand on wadi ground, which H1a condition 2 forbids. | Re-route, or accept and price the protection. The crossings register here is a STAND-IN (A-LEV-8): every row is APPROVED = 0 and MoAFWR consent (G201-p85) exists for none of them. |
| F6 | stage 4 / the engineer | 5 vortex drop shafts sit on a STRAIGHT RUN. NAMA has none - all 37 of theirs are at a junction, where a branch arrives high and has to be let down. A drop on a straight run is a design levelling its way out of a layout fault. | Look at these individually. Each is a place the ground does something the chamber spacing cannot follow. |
| F7 | reported, no decision needed | Median cover is 2.35 m against NAMA's 1.72 m, and the 90th percentile is 7.63 m against their 4.38 m. The design is DEEPER than the network next door because it is compliant: NAMA sit below their own 1.30 m minimum on 35.9 % of their length and this design does so on none of it. | - |
| F8 | reported, no decision needed | The tier shares look wrong against the as-built and are not. This design's 'main' maps to NAMA's SUBMAIN token, so main + sub main reads as 32.2 % against their 16.6 %; and the TRUNK MAIN is the client's own drawing, an INPUT, which s4 never chambered - so the trunk share of the LEVELLED network is 0 % by construction. | - |
| F9 | the contract | Four vocabulary conflicts between live modules, all in `conflicts`: the 'held' peak factor has three definitions and one of them the contract rejects; GRAD_BY has no token for a gradient set by the level its downstream chamber needs; NODES.COVER_M is defined as a quantity the 12 m cap does not test; and s1's provenance vocabulary is not the contract's. | Reconcile them in ONE place. Every one of them currently costs a label chosen to satisfy a validator. |


## Flatness FIRST, then direction (philosophy sec 4)

> *What actually buys depth on this ground is not that pipes point the wrong way - it is that the ground is too flat to lay them on.*

| TEST | N | KM | PCT_LEN | DEBT_M |
|---|---|---|---|---|
| ground flatter than DN200's Table 11 minimum (5.00 mm/m) | 34585 | 912.066 | 61.690 | - |
| ground flatter than the reach's OWN governing minimum | 33918 | 894.470 | 60.500 | - |
| ground FALLS at or steeper than the reach's own minimum | 22309 | 583.998 | 39.500 | - |
| ground rises along the direction of flow (AGN_GRADE) | 14783 | 388.989 | 26.310 | - |
| ACCUMULATED DEPTH DEBT - sum over reaches of (the reach's own minimum gradient minus the ground fall) x length. This is the depth the ground does not give back, and it is what the 12 m cap eventually runs into | 33918 | - | - | 7,267.034 |
| the same, per km of network | 56227 | 1,478.468 | - | 4.915 |


## Depth and cover

| QUANTITY | VALUE | UNIT | BUILT | BAND |
|---|---|---|---|---|
| cover to crown, median (length-weighted) | 2.361 | m | 1.720 | 1.34 - 2.07 |
| cover to crown, 90th percentile | 7.675 | m | 4.380 | 2.82 - 4.48 |
| cover to crown, 99th percentile | 11.364 | m | - | - |
| deepest cover on any reach | 19.092 | m | 8.190 | <= 12  G203-p33 |
| deepest EXCAVATION at any chamber | 19.778 | m | - | <= 12  G203-p33 |
| length below the 1.30 m minimum cover | 0.000 | km | 22.680 | 0  G203-p33 4.6.3 |
| share of length below the 1.30 m minimum cover | 0.000 | % | 35.900 | 0  G203-p33 4.6.3 |
| chambers past the 12 m cap | 325.000 | - | 0.000 | 0 unless a sec 5 exit applies |


## THE DIAGNOSTIC: drop structures

> *A design generating vortex shafts by the thousand where the built network has tens is describing its own tree, not the ground.*

| QUANTITY | VALUE | UNIT | BUILT | BAND |
|---|---|---|---|---|
| vortex drop shafts (drop > 2.00 m) | 73.000 | - | 37.000 | - |
| vortex drop shafts per km | 0.049 | /km | 0.585 | <= 0.605  MEASURED |
| vortex per 1,000 chambers | 1.282 | - | 19.710 | <= 21.06  MEASURED |
| vortex shafts sitting at a junction | 93.151 | % | 100.000 | >= 100  MEASURED |
| vortex shafts on a STRAIGHT RUN - NAMA has none, and a drop on a straight run is a design levelling its way out of a layout fault | 5.000 | - | 0.000 | 0  MEASURED |
| backdrops (0.60 - 2.00 m) | 46.000 | - | 84.000 | - |
| backdrops per km | 0.031 | /km | 1.329 | <= 1.700  MEASURED |
| deepest single drop | 8.389 | m | - | <= 20  PROJECT CEILING |
| total drop taken at structures | 545.556 | m | - | - |


## Gradients

| QUANTITY | VALUE | UNIT | BUILT | BAND |
|---|---|---|---|---|
| laid gradient, median (length-weighted) | 5.000 | mm/m | 6.000 | 5.96 - 6.63  MEASURED |
| laid gradient, mean | 13.689 | mm/m | 8.890 | - |
| laid gradient, length-weighted mean | 13.385 | mm/m | 8.690 | - |
| laid gradient, DN200 median | 5.000 | mm/m | 5.190 | info |
| steepest laid gradient | 250.000 | mm/m | 160.900 | - |
| reaches laid against the flow (reverse gradient) | 0.000 | - | 0.000 | 0  G203-p29 4.3.1 |


## Self-cleansing - which route, and how much rests on the assumed tau

| ROUTE | N | KM | PCT_LEN |
|---|---|---|---|
| velocity | 6888 | 179.290 | 12.127 |
| tractive | 49339 | 1,299.178 | 87.873 |
| neither | 0 | 0.000 | 0.000 |
| minimum gradient SET BY table11 | 30166 | 797.125 | 53.916 |
| minimum gradient SET BY tractive | 0 | 0.000 | 0.000 |


## Diameters

| DN | N | KM | PCT_LEN | DOD_MAX | V_MAX | QPK_MAX_LS |
|---|---|---|---|---|---|---|
| 200 | 51967 | 1,367.332 | 92.483 | 0.650 | 2.999 | 25.786 |
| 250 | 1103 | 28.897 | 1.955 | 0.650 | 2.999 | 39.839 |
| 315 | 1053 | 27.528 | 1.862 | 0.650 | 2.998 | 103.796 |
| 400 | 658 | 17.251 | 1.167 | 0.499 | 2.119 | 103.899 |
| 500 | 908 | 23.686 | 1.602 | 0.499 | 2.844 | 131.678 |
| 600 | 312 | 7.997 | 0.541 | 0.499 | 3.000 | 139.400 |
| 700 | 181 | 4.608 | 0.312 | 0.495 | 2.947 | 142.333 |
| 800 | 11 | 0.252 | 0.017 | 0.208 | 2.366 | 179.299 |
| 900 | 34 | 0.916 | 0.062 | 0.440 | 0.837 | 225.630 |


## What set the size and the gradient

| FIELD | VALUE | N | KM | PCT_LEN | FINE |
|---|---|---|---|---|---|
| SIZED_BY | capacity | 1126 | 29.555 | 1.999 |  |
| SIZED_BY | dod | 3096 | 80.580 | 5.450 |  |
| SIZED_BY | minimum | 51967 | 1,367.332 | 92.483 |  |
| SIZED_BY | velocity | 38 | 1.001 | 0.068 |  |
| GRAD_BY | cover_min | 7182 | 185.824 | 12.569 |  |
| GRAD_BY | ground | 3274 | 85.493 | 5.783 |  |
| GRAD_BY | table11 | 30166 | 797.125 | 53.916 |  |
| GRAD_BY | uniform | 15590 | 409.592 | 27.704 |  |
| GRAD_BY | vmax | 15 | 0.433 | 0.029 |  |
| GRAD_FINE |  | 30166 | 797.125 | 53.916 | G203-p29 Table 11 floor for this diameter |
| GRAD_FINE |  | 15 | 0.433 | 0.029 | held back by the 3.0 m/s cap or the 25 % publishing bound |
| GRAD_FINE |  | 1310 | 32.537 | 2.201 | steepened to arrive at the level its downstream chamber needs, instead of dropping into it (P5 crown matching) |
| GRAD_FINE |  | 5872 | 153.287 | 10.368 | steepened to hold 1.30 m of cover at the downstream end (G203-p33) |
| GRAD_FINE |  | 3274 | 85.493 | 5.783 | the ground fall; both minima already satisfied |
| GRAD_FINE |  | 15590 | 409.592 | 27.704 | the run's common gradient (P1), laid to land on its junction invert |


## Stations the cap demands

| QUANTITY | VALUE | UNIT |
|---|---|---|
| stations demanded by the 12 m cap | 508.000 | - |
| duty (peak) flow, minimum | 0.032 | L/s |
| duty (peak) flow, median | 0.732 | L/s |
| duty (peak) flow, maximum | 139.200 | L/s |
| total peak flow lifted | 2,456.421 | L/s |
| properties upstream of a station, counted ONCE per station - stations nest, so this SUMS TO MORE than the network's 93,320 and is not a count of properties served by pumping | 101,830.878 | - |
| deepest station chamber | 12.593 | m |
| gravity reaches withdrawn to the rising main | 508.000 | - |
| length withdrawn | 13.481 | km |
| static lift to the discharge chamber, median | 0.702 | m |
| static lift, maximum | 21.911 | m |
| stations sited inside a contiguous UPHILL stretch - the ideal site is the FOOT of the climb and moving it there is a layout change (A-LEV-12) | 193.000 | - |
| climb those stations sit on, total | 270.213 | m |
| stations stepped upstream off a drop chamber | 1.000 | - |


## Past the cap - every excursion an exit lets stand

> *An exit is bounded by DEPTH as well as by distance, and is withdrawn when either bound is crossed (A-LEV-11).*

| EXIT | N | KM | MAX_COVER_M | MEDIAN_COVER_M | MAX_DROP_M | CEILING_M |
|---|---|---|---|---|---|---|
| outfall_1000m | 209 | 5.121 | 17.331 | 13.531 | 8.389 | 20.000 |
| recovers_500m | 116 | 3.088 | 19.778 | 12.630 | 5.147 | 20.000 |
| DEEPEST SINGLE CHAMBER: N0031347 at 453649 E 2570142 N | 1 | 0.029 | 19.778 | 19.778 | 0.000 | 20.000 |


## The outer loop, pass by pass

| PASS | STATIONS | PAST_CAP_N | PAST_CAP_KM | EXCUSED_N | MAX_COVER_M | MAX_DROP_M | VORTEX_N | NEW_STATIONS | RUNS | UNIFORM | LATE | FALL_RECOVERED_M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 5679 | 149.810 | 351 | 85.710 | 79.280 | 196 | 327 | 8568 | 2574 | 1722 | 17,126.900 |
| 2 | 327 | 3212 | 84.830 | 345 | 74.930 | 68.500 | 273 | 120 | 8878 | 2713 | 1576 | 12,669.300 |
| 3 | 447 | 1749 | 45.910 | 430 | 64.180 | 57.760 | 200 | 36 | 8993 | 2796 | 1491 | 10,710.400 |
| 4 | 483 | 1139 | 30.040 | 327 | 54.220 | 47.800 | 130 | 11 | 9025 | 2829 | 1456 | 10,060.100 |
| 5 | 494 | 826 | 21.670 | 427 | 43.430 | 37.010 | 105 | 9 | 9032 | 2845 | 1438 | 9,845.500 |
| 6 | 503 | 540 | 14.260 | 361 | 32.530 | 26.110 | 78 | 4 | 9041 | 2862 | 1421 | 9,695.700 |
| 7 | 507 | 436 | 11.390 | 324 | 21.820 | 15.400 | 75 | 1 | 9043 | 2867 | 1415 | 9,631.400 |
| 8 | 508 | 325 | 8.210 | 325 | 19.780 | 8.390 | 73 | 0 | 9044 | 2869 | 1413 | 9,614.800 |


## Pass 2: what the review pass recovered

| QUANTITY | VALUE |
|---|---|
| fall_recovered_m | 9,614.843 |
| fallback_cap | 44.000 |
| fallback_slope | 0.000 |
| late | 1,413.000 |
| reaches_absorbed | 16,809.000 |
| reaches_uniform | 15,998.000 |
| run_len_max_m | 4,737.345 |
| runs | 9,044.000 |
| skipped_capped | 11.000 |
| uniform | 2,869.000 |
| untouched | 4,751.000 |


## What kind of station the cap is asking for

| BAND | N | Q_TOTAL_LS | N_PROP | ON_UPHILL |
|---|---|---|---|---|
| under 1 L/s | 281 | 95.669 | 3,006.062 | 73 |
| 1 - 5 L/s | 127 | 287.556 | 8,882.574 | 61 |
| 5 - 20 L/s | 74 | 709.898 | 26,174.826 | 42 |
| 20 - 100 L/s | 24 | 1,112.600 | 50,995.036 | 16 |
| over 100 L/s | 2 | 250.697 | 12,772.380 | 1 |


## Wadi crossings - H1a, tested as far as this stage can

> *The full register, one row per contact, is in `run/levels/wadi_h1a.csv`.*

| QUANTITY | VALUE | UNIT |
|---|---|---|
| length on wadi ground (hazard class 4-6 of the 50-year grid) | 75.236 | km |
| share of the published network on wadi ground | 5.089 | % |
| separate on-wadi contacts (one contiguous run = one contact) | 466.000 | - |
| contacts that CROSS - within the 25 deg skew tolerance of square | 129.000 | - |
| length in those crossings | 16.457 | km |
| contacts that RUN ALONG the wadi - H1 forbids these outright | 337.000 | - |
| length running ALONG a wadi | 58.779 | km |
| longest single run along a wadi | 1,618.400 | m |
| chambers standing on wadi ground - H1a condition 2 forbids ANY. DISTINCT chambers, off the node layer; summing the per-contact counts double-counts a junction two contacts share | 3,365.000 | - |
| contacts meeting our own 1.50 m wadi cover (A-LEV-14) | 244.000 | - |
| contacts passing ALL FOUR of H1a's conditions | 0.000 | - |
| third-party consent obtained on any of them (MoAFWR, G201-p85) | 0.000 | - |


## Reconciliation against s5_flows

| QUANTITY | S6 | S5 | DIFF | NOTE |
|---|---|---|---|---|
| ADWF, m3/d - the project total | 74,701.172 | 74,701.100 | -0.072 |  |
| ADWF, m3/d - reaching a terminal HERE | 70,405.494 | 73,938.500 | 3,533.006 |  |
| ADWF, m3/d - s4 `unserved`: no chamber within 45 m | 4,295.679 | 0.000 | -4,295.679 | in neither network; a scope answer, not a levelling one |
| ADWF, m3/d - s5 `undelivered`: 184 island arcs | 0.000 | 762.600 | 762.600 | s2's to connect; s4 never chambered them |
| ADWF, m3/d - RESIDUAL after both | 74,701.172 | 74,701.100 | -0.072 | must be zero |
| properties - the project total | 98,681.110 | 98,680.000 | -1.110 |  |
| properties - reaching a terminal HERE | 93,319.654 | 97,691.000 | 4,371.346 |  |
| properties - s4 `unserved`: no chamber within 45 m | 5,361.456 | 0.000 | -5,361.456 | in neither network; a scope answer, not a levelling one |
| properties - s5 `undelivered`: 184 island arcs | 0.000 | 989.000 | 989.000 | s2's to connect; s4 never chambered them |
| properties - RESIDUAL after both | 98,681.110 | 98,680.000 | -1.110 | must be zero |


## The trunk main

| QUANTITY | VALUE | UNIT | NOTE |
|---|---|---|---|
| trunk main in this design's `reaches` layer | 0.000 | km | the tier does not appear, and that is CORRECT, not a gap |
| trunk main published by s3 in its own layer | 85.491 | km | 54 features, SRC = main_pipe - the client's drawing, an INPUT |
| terminals discharging into it | 195.000 | - | their inverts were chosen freely; the level the trunk will accept is UNCONFIRMED and is a data request (A-LEV-7) |
| trunk share of the levelled length | 0.000 | % | NAMA's built network is 5.78 % trunk, band 1.48 - 13.45. The comparison does not apply: theirs includes their trunk, ours does not |


## Calibration against NAMA's built network

> *A benchmark is a calibration reference and never a limit. A band is the spread between NAMA's five construction packages, not a guessed plus-minus.*

| label | unit | as_built | band | design | verdict | basis |
|---|---|---|---|---|---|---|
| median cover to crown | m | 1.725 | 1.337 .. 2.07425 | 2.349 | HIGH | MEASURED |
| 90th-percentile cover | m | 4.383 | 2.8159 .. 4.47975 | 7.626 | HIGH | MEASURED |
| deepest cover | m | 8.193 | <= 12 | 19.092 | HIGH | GUIDELINE |
| chambers per km | 1/km | 34.227 | 33.288 .. 36.7608 | 38.506 | HIGH | MEASURED |
| submain share of built length | % | 16.608 | 10.8477 .. 17.1521 | 32.170 | HIGH | MEASURED |
| share of vortex drops that sit at a junction, not on a straight run | % | 100.000 | >= 100 | 92.424 | LOW | MEASURED |
| trunk share of built length | % | 5.781 | 1.47596 .. 13.4491 | 0.000 | LOW | MEASURED |
| median laid gradient | mm/m | 6.001 | 5.95732 .. 6.62643 | 5.000 | LOW | MEASURED |
| lateral share of built length | % | 77.611 | 71.5709 .. 81.3719 | 67.830 | LOW | MEASURED |
| share of length whose GROUND rises in the direction of flow | % | 34.098 | <= 38.147 | 34.276 | PASS | MEASURED |
| backdrops per km (invert step 0.60-2.00 m) | 1/km | 1.329 | <= 1.70042 | 0.031 | PASS | MEASURED |
| vortex drop shafts per 1,000 chambers | 1/1000 | 19.712 | <= 21.0632 | 1.159 | PASS | MEASURED |
| reaches laid against the flow (US invert below DS) | count | 0.000 | <= 0 | 0.000 | PASS | MEASURED |
| vortex drop shafts per km (invert step > 2.00 m) | 1/km | 0.585 | <= 0.605236 | 0.045 | PASS | MEASURED |
| ground climb bought per km of sewer | m/km | 4.060 | <= 5.07515 | 2.658 | PASS | MEASURED |
| longest single reach between chambers | m | 71.381 | <= 100 | 31.024 | PASS | GUIDELINE |
| cumulative ground climb / cumulative ground descent along the flow path | - | 0.483 | <= 0.647362 | 0.415 | PASS | MEASURED |
| length below the guideline's OD 200 minimum for a lateral | % | 61.472 | <= 0 | 0.000 | PASS | GUIDELINE |
| length below the 1.30 m minimum cover | % | 35.927 | <= 0 | 0.000 | PASS | GUIDELINE |
| median chamber spacing | m | 29.773 | 26.8467 .. 30.3002 | 27.183 | PASS | MEASURED |
| median laid gradient, OD200 (the trunk mains) | mm/m | 5.187 | - | 5.000 | INFO | MEASURED |
| junction chambers per km | 1/km | 4.830 | - | 2.813 | INFO | MEASURED |
| design tractive stress | Pa | 1.000 | - | 1.000 | INFO | ASSUMPTION |


## Terminals

| NODE_UID | X | Y | GRD_M | INV_M | DEPTH_M | KIND | Q_ADF_M3D | Q_PK_LS | N_PROP |
|---|---|---|---|---|---|---|---|---|---|
| N0005088 | 451,730.777 | 2,572,623.843 | 378.820 | 370.562 | 8.258 | outfall | 9,600.147 | 225.675 | 12,920.480 |
| N0003537 | 449,912.100 | 2,568,732.673 | 356.271 | 347.199 | 9.072 | outfall | 8,641.818 | 205.498 | 11,600.744 |
| N0003280 | 449,147.758 | 2,567,800.172 | 352.369 | 343.776 | 8.593 | outfall | 5,763.198 | 143.898 | 7,473.056 |
| N0045904 | 452,361.418 | 2,572,993.929 | 381.592 | 374.167 | 7.425 | station | 5,540.354 | 139.200 | 7,340.544 |
| N0007565 | 459,201.382 | 2,568,020.653 | 383.012 | 370.015 | 12.998 | outfall | 5,477.600 | 137.524 | 7,146.456 |
| N0033751 | 447,833.605 | 2,567,924.181 | 347.353 | 334.759 | 12.593 | station | 4,311.451 | 111.497 | 5,431.836 |
| N0005517 | 453,065.561 | 2,566,674.509 | 357.165 | 345.867 | 11.298 | outfall | 3,162.985 | 84.838 | 4,298.118 |
| N0029310 | 453,479.622 | 2,571,852.798 | 377.470 | 365.105 | 12.366 | station | 3,114.187 | 83.724 | 4,359.776 |
| N0002823 | 448,426.383 | 2,567,652.575 | 349.691 | 347.582 | 2.109 | outfall | 3,098.340 | 83.482 | 4,179.732 |
| N0033746 | 446,225.101 | 2,567,913.469 | 341.030 | 328.546 | 12.483 | station | 3,082.511 | 83.001 | 3,805.506 |
| N0007762 | 459,838.046 | 2,567,762.869 | 383.190 | 374.168 | 9.022 | outfall | 2,832.153 | 76.951 | 3,646.770 |
| N0014881 | 449,294.068 | 2,567,680.194 | 351.490 | 338.976 | 12.514 | station | 2,800.548 | 76.409 | 3,755.430 |
| N0001689 | 446,780.354 | 2,565,204.675 | 341.282 | 325.304 | 15.978 | outfall | 2,670.354 | 73.191 | 3,533.766 |
| N0026349 | 444,563.301 | 2,567,809.780 | 335.198 | 322.693 | 12.505 | station | 2,496.096 | 68.939 | 3,044.940 |
| N0016247 | 459,201.358 | 2,570,525.827 | 381.993 | 380.136 | 1.857 | station | 2,353.988 | 65.401 | 2,990.276 |
| N0016241 | 459,301.571 | 2,570,655.705 | 382.343 | 371.994 | 10.349 | station | 2,351.763 | 65.346 | 2,987.276 |
| N0033229 | 449,622.460 | 2,566,866.842 | 347.845 | 335.424 | 12.421 | station | 2,304.076 | 64.390 | 3,066.916 |
| N0001464 | 446,428.551 | 2,564,506.492 | 335.296 | 324.270 | 11.026 | outfall | 1,964.397 | 55.871 | 2,584.682 |
| N0001857 | 447,026.038 | 2,565,695.250 | 342.271 | 334.813 | 7.458 | outfall | 1,790.311 | 51.425 | 2,341.090 |
| N0032402 | 450,469.802 | 2,565,269.956 | 341.746 | 329.980 | 11.767 | station | 1,736.720 | 50.176 | 2,329.606 |
| N0007525 | 459,106.878 | 2,568,058.917 | 381.799 | 371.648 | 10.151 | outfall | 1,622.316 | 47.283 | 2,134.858 |
| N0000174 | 442,064.743 | 2,569,072.417 | 334.167 | 320.458 | 13.709 | outfall | 1,586.787 | 46.304 | 2,120.408 |
| N0001039 | 445,664.518 | 2,563,174.812 | 327.813 | 316.918 | 10.895 | outfall | 1,523.473 | 44.959 | 2,086.676 |
| N0004649 | 451,015.736 | 2,567,194.219 | 352.935 | 348.080 | 4.855 | outfall | 1,517.866 | 44.493 | 1,897.052 |
| N0042857 | 455,766.056 | 2,570,900.602 | 373.788 | 370.481 | 3.306 | station | 1,495.390 | 43.929 | 1,956.658 |
| N0033069 | 446,362.730 | 2,566,647.862 | 340.649 | 328.402 | 12.247 | station | 1,446.956 | 42.641 | 1,888.782 |
| N0005554 | 453,144.068 | 2,574,008.756 | 385.395 | 382.831 | 2.563 | station | 1,395.440 | 41.372 | 1,763.564 |
| N0044272 | 447,141.484 | 2,564,052.283 | 333.728 | 325.890 | 7.838 | station | 1,383.439 | 41.034 | 1,812.182 |
| N0006976 | 456,383.820 | 2,571,321.591 | 376.267 | 363.941 | 12.326 | station | 1,368.278 | 40.621 | 1,790.600 |
| N0000784 | 445,032.981 | 2,564,862.856 | 332.489 | 320.041 | 12.449 | station | 1,355.836 | 40.333 | 1,812.174 |


## Assumptions

| ID | KIND | WHAT |
|---|---|---|
| A-LEV-1 | project doctrine | The load levelled here is s4_chambers' `connections` layer - 70,405.5 m3/d over 53,018 plots - not the 74,701.2 m3/d of the project total. |
| A-LEV-2 | project decision | Below 100 properties the peak factor is the Merrimack formula evaluated AT 100 properties (3.62139), and PF_METH says 'merrimack'. |
| A-LEV-3 | project decision | A reach is never smaller than the reach immediately upstream of it. |
| A-LEV-4 | project decision | CROWN MATCHING at every chamber: an incoming pipe's soffit is never below the outgoing pipe's soffit, so a step of (OD_out - OD_in) is the smallest legal invert difference where the pipe grows. |
| A-LEV-5 | method | Pass 2 NEVER lays a reach flatter than pass 1 did. |
| A-LEV-6 | ASSUMPTION (GAP-9) | Tractive stress tau = 1.0 Pa. |
| A-LEV-7 | GAP | The 195 terminals are levelled to whatever the network gives them. No tie-in invert is imposed, and TIE_TYPE is 'none' on every reach. |
| A-LEV-8 | STAND-IN | The crossings register is minted HERE, provisionally, because no corridor stage published one. Every row is APPROVED = 0. |
| A-LEV-9 | GAP | No start-year flows exist, so self-cleansing is checked at the SATURATION flow only. |
| A-LEV-10 | project decision | A station is LOCATED here and DESIGNED by s7_pumps. It terminates its gravity component; the chamber it would have drained to is re-based at minimum cover and receives the rising main (G203-p55 8.5: termination not more than 300 mm above the receiving flow line). |
| A-LEV-11 | project assumption | A philosophy sec 5 exit is WITHDRAWN when any chamber inside the excursion carries a drop OR a cover greater than criteria.DROP_CEILING_M (20.0 m). |
| A-LEV-12 | project decision | A station is sited at the last chamber still INSIDE the cap on the branch whose arriving invert governs the breach - never at the junction the branch ends at. |
| A-LEV-13 | method | Five chamber pairs closer than criteria.MH_SNAP_M (3.0 m) are CONTRACTED into one structure before levelling. |
| A-LEV-14 | project decision | 1.30 m of cover is required everywhere, INCLUDING on wadi ground, and the 1.50 m wadi figure is reported as a shortfall rather than designed to. |


## Conflicts found between live documents

| ID | WHAT | WHO |
|---|---|---|
| C-LEV-1 | 'held' peak factor: three live definitions. | criteria.py / contract.py / s5_flows.py / this stage |
| C-LEV-2 | contract.GRAD_BY has no token for 'laid to the level its downstream chamber needs'. | contract.GRAD_BY |
| C-LEV-3 | contract NODES.COVER_M is defined as the SHALLOWEST connected pipe's cover, which is not the quantity the 12 m cap tests. | contract.NODES.COVER_M |
| C-LEV-4 | s1_roads' provenance vocabulary is not the contract's. | s1_roads / contract.SRC, contract.CONFIDENCE |


## Funnel

```
chambers read      56,930
reaches published  56,227   1,478.5 km
withdrawn to a rising main  508
uphill length      26.31 %  (389.0 km)
climb / descent    0.415   (built 0.483, W11a 0.747)
```
