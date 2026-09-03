# W11b stage 3 - the hierarchy, on the oriented tree

`W11b-hierarchy-1.0`  ·  2026-09-03 19:25 UTC  ·  tau=1 Pa ASSUMED (GAP-9)

## The answer

**Exceptions to the hard rule: 0.** 5,064 heads, 3,980 of them set back off a chamber that already had an outlet - s2 handed over 2,887 needing it. 148.7 km of pipe is NOT laid, because it would have run upstream of the first customer it serves.

1,662.0 km of corridor plus the client's 85.49 km Main Pipe = **1,747.5 km**, in **191 components, each ending at exactly one outfall** (H15), **0 draining nowhere**.

### Tier shares against the built network

| BUCKET                                     | W11b_PCT | BUILT_PCT | BAND_LO | BAND_HI | VERDICT |
|--------------------------------------------|----------|-----------|---------|---------|---------|
| trunk main                                 | 4.89     | 5.78      | 1.48    | 13.45   | PASS    |
| sub main                                   | 16.48    | 16.61     | 10.85   | 17.15   | PASS    |
| lateral + main  (= NAMA's 'lateral' token) | 78.63    | 77.61     | 71.57   | 81.37   | PASS    |

The vocabulary matters and the table says which one it uses. NAMA's manhole IDs carry three tokens - trunk main, sub main, and everything else - so their 'lateral' bucket is our lateral PLUS our main. Comparing a four-tier split against a three-tier one without saying so is the error philosophy sec 4 warns about.

| TIER       | KM       | PCT_OF_ALL | N_ARCS |
|------------|----------|------------|--------|
| lateral    | 1,168.54 | 66.87      | 8,757  |
| main       | 205.58   | 11.76      | 1,910  |
| sub main   | 287.90   | 16.48      | 1,899  |
| trunk main | 85.49    | 4.89       | 54     |

Philosophy sec 4 says to **expect roughly 270 km of sub main** and that a design producing 20 km is wrong on sight. This one produces **287.9 km** over **156 routes**, one per 10.7 km of network against the measured 4-10 km. **The route density is the one measure this stage does NOT hit.** The threshold that lands the sub-main SHARE on the built network's own 16.61 % gives fewer, longer routes; the sweep below shows nothing in the range satisfies both measures at once, and the share is preferred because it is the measurement the as-built actually supports.

The trunk's **diameter is not known at this stage**, so only the third of G203-p35 sec 5's three criteria - upstream of the STP or the main pumping station - can be tested here. D > 800 mm is stage 6's answer.

**G203-p22 Table 6's 45 m maximum length is NOT applied to this `lateral` tier.** It governs the TERTIARY lateral - the pipe from a house connection chamber to the street sewer, which stage 5b mints. NAMA's own street runs have a median of 68.7 m and a p90 of 218.6 m; applying the tertiary rule to them would condemn most of the built network.

### Runs

| ITEM                                                               | W11b     | BUILT  |
|--------------------------------------------------------------------|----------|--------|
| runs                                                               | 9,622.00 | 945.00 |
| run length median, m                                               | 116.37   | 68.74  |
| run length p90, m                                                  | 341.29   | 218.64 |
| run length MAXIMUM, m  (the governing statistic, philosophy sec 4) | 5,127.48 | -      |
| junctions per km                                                   | 2.82     | 4.83   |
| heads per km                                                       | 3.05     | 5.09   |

**Junctions per km reads low against the built network on purpose.** A junction is a node with two or more pipes arriving, and the tertiary tier - riders and the 45 m G203 laterals off every house connection - is not in this layer at all; stage 5b mints it. NAMA's 4.83/km counts a network that already has its tertiary in place, so the two are not yet comparable and the gap should not be read as this design being coarse.

The longest runs, so the chamber stage meets them on purpose rather than discovering them:

| RUN_ID  | TIER     | LEN_M   | CHAMBERS_AT_100M | SUB_KM |
|---------|----------|---------|------------------|--------|
| R005842 | sub main | 5,127.5 | 52               | 18.2   |
| R009349 | sub main | 3,808.9 | 39               | 3.8    |
| R000002 | sub main | 3,732.7 | 38               | 4.7    |
| R002826 | lateral  | 3,297.2 | 33               | 3.3    |
| R005286 | sub main | 3,221.8 | 33               | 6.6    |
| R009310 | lateral  | 2,929.5 | 30               | 2.9    |
| R002903 | sub main | 2,820.5 | 29               | 28.8   |
| R002656 | lateral  | 2,426.2 | 25               | 2.4    |
| R006536 | lateral  | 2,312.0 | 24               | 2.3    |
| R009348 | lateral  | 2,293.7 | 23               | 2.3    |
| R002897 | lateral  | 2,265.4 | 23               | 2.3    |
| R005190 | sub main | 2,244.0 | 23               | 4.6    |
| R001467 | sub main | 2,242.8 | 23               | 10.0   |
| R004139 | lateral  | 2,016.4 | 21               | 2.0    |
| R003590 | lateral  | 1,896.4 | 19               | 1.9    |

### Heads - where each one starts, and why

| HEAD_BY              | N     | KM     |
|----------------------|-------|--------|
| gate_clear           | 2,592 | 428.16 |
| gate                 | 966   | 113.32 |
| gate_at_corridor_end | 795   | 90.09  |
| clearance            | 422   | 99.67  |
| road_end_no_gate     | 289   | 61.12  |

| PASS | HEADS | PRUNED | KEPT_KM  |
|------|-------|--------|----------|
| 1    | 5,249 | 228    | 1,811.30 |
| 2    | 5,075 | 15     | 1,810.95 |
| 3    | 5,066 | 3      | 1,810.86 |
| 4    | 5,066 | 2      | 1,810.78 |
| 5    | 5,065 | 1      | 1,810.76 |
| 6    | 5,065 | 1      | 1,810.73 |
| 7    | 5,064 | 0      | 1,810.73 |

Pruned: 250 arcs, 8.72 km.

| WHY                                                             | N   | KM    | Q_M3D  |
|-----------------------------------------------------------------|-----|-------|--------|
| finger: serves nothing, under 60 m                              | 242 | 7.664 | 0.000  |
| the gate leaves less than the minimum chamber clearance of pipe | 8   | 1.055 | 14.572 |

### Nothing is dropped silently

| ITEM                                                                  | N   | Q_M3D  | RESOLUTION                                                                                                                                                                                                                                     |
|-----------------------------------------------------------------------|-----|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| plots whose gate falls inside a head setback                          | 310 | 340.44 | property connection to the junction chamber they were cut from; every one is inside the 10 m setback, far inside the 50 m PCS limit (G203-p18)                                                                                                 |
| plots on a pruned arc, MY nearest-arc allocation                      | 17  | 14.57  | connect at the chamber the pruned arc met; stage 5b sizes it                                                                                                                                                                                   |
| the same arcs under s1/s2's OWN allocation (Q_M3D carried on the arc) | -1  | 59.29  | the two allocations disagree because s2's ridge pre-split cut 151 corridors after s1 had allocated. BOTH are published rather than the smaller one: the gap is the honest measure of how much this depends on which corridor a plot is tied to |

**13 sub-networks disappeared entirely** - every arc in each was a dead-end reach under 60 m serving nothing, so the whole catchment was one finger. Together 6.552 km and 138.76 m3/d on s2's own allocation. Named, not absorbed.

| OUTFALL | SUBNET | ARCS_WAS | KM_WAS | Q_M3D_WAS |
|---------|--------|----------|--------|-----------|
| N001763 | S154   | 2        | 0.370  | 0.000     |
| N002439 | S157   | 3        | 0.606  | 12.631    |
| N003461 | S164   | 2        | 0.627  | 1.080     |
| N003540 | S165   | 2        | 0.192  | 1.080     |
| N003544 | S152   | 3        | 0.030  | 0.000     |
| N003548 | S153   | 2        | 0.302  | 6.882     |
| N006025 | S162   | 3        | 0.344  | 29.888    |
| N006139 | S172   | 2        | 0.040  | 1.080     |
| N006471 | S171   | 3        | 0.583  | 16.196    |
| N007474 | S170   | 3        | 1.771  | 12.720    |
| N007618 | S173   | 3        | 0.369  | 15.681    |
| N008198 | S181   | 3        | 0.361  | 2.563     |
| N009636 | S148   | 3        | 0.957  | 38.955    |

### The trunk, and what touches it

| ITEM                                                    | VALUE  |
|---------------------------------------------------------|--------|
| outfall nodes discharging into the Main Pipe            | 180.00 |
| Main Pipe length, km                                    | 85.49  |
| joins per km of trunk                                   | 2.11   |
| MEASURED in NAMA's built network, joins per km of trunk | 4.64   |
| MEASURED joins in NAMA's built network (count)          | 21.00  |

| TIER     | N   |
|----------|-----|
| lateral  | 253 |
| sub main | 51  |
| main     | 46  |

### Does a lateral find its own way to the trunk? (the W7 test)

**3.91 %** of lateral runs discharge STRAIGHT into the trunk, against NAMA's measured **2.19 %** of lateral zones. That is the one like-for-like row below, and it is the row the target exists for: a design where every catchment finds its own way to the trunk is the W7 failure.

| A LATERAL RUN DISCHARGES INTO     | N     | PCT   | NAMA_PCT | LIKE_FOR_LIKE                                                               |
|-----------------------------------|-------|-------|----------|-----------------------------------------------------------------------------|
| another lateral                   | 3,485 | 51.36 | 87.69    | no - NAMA count ZONES, we count RUNS                                        |
| a main                            | 1,937 | 28.54 | -        | no - NAMA's IDs carry no 'main' token                                       |
| a sub main                        | 1,099 | 16.20 | 10.12    | no - zones against runs                                                     |
| the TRUNK, direct  <- THE W7 TEST | 265   | 3.91  | 2.19     | YES - both count a lateral thing touching the trunk with nothing in between |

The other three rows are NOT comparable, and the table says so. NAMA's 87.69 % counts DRAFTING ZONES - zone A49 holds many runs and only its exit pipe is measured - while ours counts every run. Quoting our 51 % against their 87.69 % would be comparing two different objects, which is how a number gets retracted here.

### The uphill share - re-measured, NOT improved

| BASIS                                                                        | KM       | UPHILL_KM | UPHILL_PCT |
|------------------------------------------------------------------------------|----------|-----------|------------|
| s2's headline, as printed in its own manifest                                | 1,788.30 | 414.00    | 23.15      |
| s2's UPHILL flag over EVERY arc it published                                 | 1,819.45 | 413.97    | 22.75      |
| s3 after the island directions are repaired, before any trimming             | 1,819.45 | 419.30    | 23.05      |
| s3 AS PUBLISHED - set back, pruned, falls re-sampled on the trimmed geometry | 1,662.02 | 424.88    | 25.56      |
| MEASURED, NAMA's built network - CONTEXT, NOT PERMISSION                     | 95.45    | -         | 34.10      |
| W11a, the design this replaces                                               | 1,731.70 | 737.70    | 42.50      |

A hierarchy re-labels pipe. It does not tilt ground. The two W11b rows differ only because the setbacks and the pruning changed the denominator; the direction of every surviving arc is s2's, unchanged. **60 % of this corridor network lies on ground falling more gently than the 5.00 mm/m a DN200 may be laid at (G203-p29 Tab 11), and no tree fixes that.**

### Calibration - the sub-main threshold

| SUBMAIN_KM | SUBMAIN_KM_OF_NETWORK | SUBMAIN_PCT | MAIN_KM | LATERAL_KM | N_SUBMAIN_RUNS | N_SUBMAIN_ROUTES | KM_NET_PER_ROUTE | ROUTE_IN_4_10_KM | IN_BUILT_BAND | VERDICT | SHIPPED |
|------------|-----------------------|-------------|---------|------------|----------------|------------------|------------------|------------------|---------------|---------|---------|
| 0.50       | 837.21                | 47.91       | 3.02    | 821.79     | 3,830          | 884              | 1.88             | 0                | 0             | HIGH    | 0       |
| 0.75       | 677.56                | 38.77       | 8.92    | 975.54     | 3,143          | 602              | 2.76             | 0                | 0             | HIGH    | 0       |
| 1.00       | 594.22                | 34.00       | 23.37   | 1,044.44   | 2,769          | 477              | 3.48             | 0                | 0             | HIGH    | 0       |
| 1.50       | 481.99                | 27.58       | 68.46   | 1,111.57   | 2,239          | 340              | 4.89             | 1                | 0             | HIGH    | 0       |
| 2.00       | 397.79                | 22.76       | 115.04  | 1,149.19   | 1,904          | 252              | 6.60             | 1                | 0             | HIGH    | 0       |
| 2.50       | 344.72                | 19.73       | 154.99  | 1,162.31   | 1,685          | 206              | 8.07             | 1                | 0             | HIGH    | 0       |
| 3.00       | 318.23                | 18.21       | 178.55  | 1,165.24   | 1,528          | 187              | 8.89             | 1                | 0             | HIGH    | 0       |
| 3.25       | 301.97                | 17.28       | 194.81  | 1,165.24   | 1,450          | 169              | 9.83             | 1                | 0             | HIGH    | 0       |
| 3.50       | 287.90                | 16.48       | 205.58  | 1,168.54   | 1,380          | 156              | 10.65            | 0                | 1             | PASS    | 1       |
| 3.75       | 277.10                | 15.86       | 216.38  | 1,168.54   | 1,327          | 143              | 11.62            | 0                | 1             | PASS    | 0       |
| 4.00       | 263.79                | 15.09       | 225.89  | 1,172.35   | 1,272          | 130              | 12.78            | 0                | 1             | PASS    | 0       |
| 5.00       | 230.04                | 13.16       | 255.90  | 1,176.08   | 1,116          | 102              | 16.29            | 0                | 1             | PASS    | 0       |
| 6.00       | 200.24                | 11.46       | 285.71  | 1,176.08   | 977            | 83               | 20.02            | 0                | 1             | PASS    | 0       |
| 8.00       | 163.02                | 9.33        | 322.92  | 1,176.08   | 807            | 65               | 25.57            | 0                | 0             | LOW     | 0       |
| 12.00      | 122.65                | 7.02        | 363.29  | 1,176.08   | 607            | 37               | 44.92            | 0                | 0             | LOW     | 0       |

### Calibration - the lateral budget

| BUDGET_RUNS | BUDGET_PATH_M | LATERAL_KM | MAIN_KM | LATERAL_PCT | SHIPPED |
|-------------|---------------|------------|---------|-------------|---------|
| 2           | 400.0         | 1,068.5    | 305.6   | 61.1        | 0       |
| 2           | 750.0         | 1,091.9    | 282.2   | 62.5        | 0       |
| 2           | 1,200.0       | 1,099.5    | 274.6   | 62.9        | 0       |
| 2           | 2,000.0       | 1,103.1    | 271.0   | 63.1        | 0       |
| 3           | 400.0         | 1,113.1    | 261.1   | 63.7        | 0       |
| 3           | 750.0         | 1,168.5    | 205.6   | 66.9        | 1       |
| 3           | 1,200.0       | 1,185.4    | 188.7   | 67.8        | 0       |
| 3           | 2,000.0       | 1,192.4    | 181.7   | 68.2        | 0       |
| 4           | 400.0         | 1,131.2    | 242.9   | 64.7        | 0       |
| 4           | 750.0         | 1,216.4    | 157.7   | 69.6        | 0       |
| 4           | 1,200.0       | 1,245.3    | 128.8   | 71.3        | 0       |
| 4           | 2,000.0       | 1,254.6    | 119.5   | 71.8        | 0       |
| 5           | 400.0         | 1,137.1    | 237.0   | 65.1        | 0       |
| 5           | 750.0         | 1,244.6    | 129.5   | 71.2        | 0       |
| 5           | 1,200.0       | 1,285.2    | 88.9    | 73.5        | 0       |
| 5           | 2,000.0       | 1,298.8    | 75.3    | 74.3        | 0       |
| 6           | 400.0         | 1,138.9    | 235.2   | 65.2        | 0       |
| 6           | 750.0         | 1,258.4    | 115.7   | 72.0        | 0       |
| 6           | 1,200.0       | 1,312.0    | 62.1    | 75.1        | 0       |
| 6           | 2,000.0       | 1,327.5    | 46.7    | 76.0        | 0       |

### The islands s2 could not place

| COMP   | N_NODES | N_ARCS | KM    | ROOT    | ROOT_Z | RELIEF_M | IN_TREE_ARCS | FLIPPED |
|--------|---------|--------|-------|---------|--------|----------|--------------|---------|
| ISL000 | 2       | 1      | 1.04  | N000103 | 322.62 | 3.15     | 1            | 0       |
| ISL001 | 2       | 1      | 0.29  | N000751 | 332.89 | 3.30     | 1            | 0       |
| ISL002 | 2       | 1      | 0.09  | N003096 | 355.01 | 0.84     | 1            | 0       |
| ISL003 | 4       | 3      | 0.57  | N004650 | 345.71 | 1.82     | 3            | 1       |
| ISL004 | 2       | 1      | 0.01  | N005468 | 383.99 | 0.14     | 1            | 0       |
| ISL005 | 2       | 1      | 0.05  | N006623 | 363.37 | 0.34     | 1            | 0       |
| ISL006 | 2       | 1      | 0.32  | N006654 | 369.23 | 2.02     | 1            | 0       |
| ISL007 | 36      | 47     | 7.70  | N008472 | 389.45 | 5.84     | 35           | 14      |
| ISL008 | 56      | 80     | 10.97 | N008957 | 395.99 | 15.14    | 55           | 7       |
| ISL009 | 35      | 38     | 7.93  | N008831 | 390.01 | 17.62    | 34           | 13      |
| ISL010 | 8       | 8      | 1.82  | N009269 | 445.05 | 18.47    | 7            | 3       |
| ISL011 | 3       | 2      | 0.08  | N009549 | 430.18 | 0.48     | 2            | 0       |

Each is given a LOCAL outfall at its own lowest node so that no component drains nowhere (H15). Whether that becomes a pumping station or a satellite works is stage 7's question and the options appraisal's, not this one's.

### Exceptions

| KIND | WHERE | DETAIL                                |
|------|-------|---------------------------------------|
|      |       | NONE - the hard rule holds everywhere |

### Every constant, with where it came from

| ITEM                     | VALUE                | UNIT | SOURCE                                                                                                                   |
|--------------------------|----------------------|------|--------------------------------------------------------------------------------------------------------------------------|
| stage                    | W11b-hierarchy-1.0   |      | this file                                                                                                                |
| criteria                 | W11b-criteria-1.0    |      | w11b/criteria.py                                                                                                         |
| run_utc                  | 2026-09-03T19:26:00Z |      |                                                                                                                          |
| orient_sha1              | 9f094ccf44b2e3d0     |      | D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W11b\shp\W11b_orient.gpkg                                       |
| main_pipe_sha1           | f3594c9bef33f843     |      | D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\SHP\Main Pipe\Main Pipe.shp                                            |
| plots_sha1               | acdaab1d8d627d3e     |      | D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W10\shp\W10_plot_loads.gpkg                                     |
| INLET_MIN_DEG            | 90.0000              | deg  | G203-p30, verbatim                                                                                                       |
| DN_TRUNK_MIN             | 800                  | mm   | G203-p35 sec 5                                                                                                           |
| TRUNK_MIN_RUN_M          | 1,000.0000           | m    | G203-p35 sec 5 ('1,000 mm' typo)                                                                                         |
| LATERAL_MAX_LEN_G203     | 45.0000              | m    | G203-p22 Table 6 - READ AND NOT ENFORCED: it governs the TERTIARY lateral, not the street run this stage calls a lateral |
| PCS_MAX_LEN              | 50.0000              | m    | G203-p18 under Table 4                                                                                                   |
| MH_SNAP_M                | 3.0000               | m    | criteria - the one chamber-clearance constant                                                                            |
| FANOUT_OFFSET_M          | 10.0000              | m    | PROJECT rule, user 2026-08-18                                                                                            |
| FINGER_MIN_M             | 60.0000              | m    | PROJECT, philosophy sec 4 ('~60 m', ours)                                                                                |
| FRONTAGE_M               | 40.0000              | m    | PROJECT, inherited from s1_roads unchanged                                                                               |
| LATERAL_BUDGET_RUNS      | 3                    |      | PROJECT, philosophy sec 4                                                                                                |
| LATERAL_BUDGET_PATH_M    | 750.0000             | m    | PROJECT, philosophy sec 4                                                                                                |
| SUBMAIN_KM               | 3.5000               | km   | CALIBRATED against the built sub-main share; sweep_submain publishes the grid                                            |
| TAU_PA                   | 1.0000               | Pa   | ENGINEER 2026-09-03, GAP-9 open                                                                                          |
| BUILT_TIER_TRUNK_PCT     | 4.7455               | %    | MEASURED asbuilt.m_tiers, whole network                                                                                  |
| BUILT_TIER_SUBMAIN_PCT   | 10.3963              | %    | MEASURED asbuilt.m_tiers, whole network                                                                                  |
| BUILT_TIER_LATERAL_PCT   | 84.8583              | %    | MEASURED asbuilt.m_tiers, whole network                                                                                  |
| BUILT_RUN_MEDIAN_M       | 68.7441              | m    | MEASURED asbuilt.m_runs                                                                                                  |
| BUILT_JOINS_PER_KM_TRUNK | 4.6362               | 1/km | MEASURED asbuilt                                                                                                         |
| BUILT_LAT_INTO_LAT_PCT   | 87.6897              | %    | MEASURED asbuilt - a design where every catchment finds its own way to the trunk is the W7 failure                       |
| arcs_in                  | 12,816               |      | from s2_orient                                                                                                           |
| arcs_out                 | 12,566               |      | after pruning                                                                                                            |
| km_in                    | 1,819.4455           | km   | s2_orient's published corridor length                                                                                    |
| km_corridors             | 1,662.0193           | km   | after setbacks and pruning                                                                                               |
| km_trunk_input           | 85.4913              | km   | client Main Pipe, an INPUT                                                                                               |
| km_all                   | 1,747.5106           | km   | corridors + trunk                                                                                                        |
| nodes_out                | 13,877               |      | including the minted head chambers                                                                                       |
| heads_n                  | 5,064                |      | runs that start at a gate                                                                                                |
| heads_set_back_n         | 3,980                |      | s2 handed over 2,887 needing it                                                                                          |
| head_setback_km          | 148.7068             | km   | pipe NOT laid upstream of the first customer                                                                             |
| pruned_n                 | 250                  |      | fingers and sub-clearance stubs                                                                                          |
| pruned_km                | 8.7193               | km   |                                                                                                                          |
| exceptions_n             | 0                    |      | EXCEPTIONS TO THE HARD RULE - must be zero                                                                               |
| components               | 191                  |      | H15: each ends at exactly one outfall                                                                                    |
| orphan_roots             | 0                    |      | components draining nowhere                                                                                              |
| tier_inversions          | 0                    |      | a lateral receiving a main - must be zero                                                                                |
| runs_n                   | 9,622                |      |                                                                                                                          |
| run_median_m             | 116.3665             | m    | built 68.74                                                                                                              |
| run_max_m                | 5,127.4784           | m    | the governing statistic (philosophy sec 4)                                                                               |
| lat_into_lat_pct         | 51.3557              | %    | built 87.69 %                                                                                                            |
| joins_per_km_trunk       | 2.1055               | 1/km | built 4.64                                                                                                               |
| submain_routes           | 156                  |      | maximal chains of sub-main runs; philosophy sec 4 expects one per 4-10 km                                                |
| km_net_per_submain_route | 10.6540              | km   | THE ONE MEASURE THIS STAGE MISSES - see sweep_submain                                                                    |
| uphill_pct_after         | 25.5643              | %    | RE-MEASURED, not improved - a hierarchy re-labels pipe, it does not tilt ground. s2's own value is the row above it      |
| km_lateral               | 1,168.5363           | km   |                                                                                                                          |
| km_main                  | 205.5787             | km   |                                                                                                                          |
| km_sub_main              | 287.9044             | km   |                                                                                                                          |
| km_trunk_main            | 85.4913              | km   |                                                                                                                          |
