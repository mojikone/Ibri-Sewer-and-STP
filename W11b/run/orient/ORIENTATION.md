# W11b stage 2 - orientation: what the tree actually achieved

_2026-09-03 11:52 - W11b-orient-1.0 - tau=1 Pa ASSUMED (GAP-9)_

## The headline

**23.15 % of the published length (414.0 km) drains against the ground.**  W11a measured **42.5 %**; NAMA's own built network runs **34.10 %** uphill, which is context and not permission.  The same graph with the method W11a used gives **33.13 %**, so the improvement is **10.0 percentage points** and it is attributable to the algorithm and the weights, not to a different input.

Over the **tree arcs alone** - excluding the 3,081 dead-end heads, which drain to their low end by construction and so cannot be uphill - the figure is **36.11 %**.  That is the honest measure of the orientation itself; the published figure above is the one that compares like for like with W11a's, which was also quoted over a whole published network.  Both are in the manifest and neither is the headline on its own.

Cumulative climb **2,451 m** against **9,507 m** of descent; **1.37 m** of climb per km of sewer against the built network's **4.06**.

## What a better tree cannot fix

**58.41 % of the corridor network - 1062.7 km - lies on ground falling more gently than the minimum gradient a DN200 may be laid at** (5.00 mm/m, G203-p29 Tab 11).  There the pipe sinks below the surface whichever way it points and no orientation helps.  Terrain confidence over the corridor length: certain 32.8 %, likely 34.5 %, uncertain 1.4 %, flat 29.9 %, split 1.4 %, no-data 0.0 %.

## The evidence - four trees on the same graph

| tree                                            | km      | uphill_pct | uphill_pct_all | climb_m | joins | path_med_m | path_p95_m | path_max_m | n_over_budget |
|-------------------------------------------------|---------|------------|----------------|---------|-------|------------|------------|------------|---------------|
| A naive shortest-path tree, LENGTH only         | 1,271.0 | 46.6       | 33.1           | 3,776.4 | 193   | 2,265.8    | 7,170.1    | 13,661.9   | 3,845         |
| B optimum branching, LENGTH only                | 1,064.9 | 47.6       | 28.4           | 3,561.6 | 193   | 3,751.1    | 12,826.5   | 18,862.5   | 5,460         |
| C shortest-path tree, slope-weighted            | 1,281.0 | 41.9       | 30.0           | 3,271.2 | 193   | 2,345.7    | 7,283.0    | 13,684.2   | 3,082         |
| D optimum branching, slope-weighted             | 1,153.8 | 28.6       | 18.4           | 1,995.6 | 193   | 5,423.9    | 17,377.6   | 22,384.2   | 5,615         |
| E optimum branching, slope + detour  <- SHIPPED | 1,146.5 | 35.9       | 23.0           | 2,441.9 | 193   | 2,724.1    | 8,978.0    | 15,075.3   | 3,606         |

`uphill_pct` is over each tree's own arcs; `uphill_pct_all` adds the dead-end heads, which drain to their low end whichever tree is built, and is therefore the column to compare with W11a's published 42.5 %.  **Part of the gap between the two columns is not orientation at all**: a branching leaves more corridors unused than a shortest-path tree does, and every unused corridor becomes a head that drains downhill.  That is a real property of the network that gets built - a dead-end run genuinely does drain downhill - but it is not the algorithm pointing pipes better, and it is why both columns are printed instead of whichever one flatters the answer.


**Read the last four columns.** An optimum branching minimises the sum of arc costs and has no term at all for how far one property's sewage then travels. That is why a detour term was added, why it is swept and published rather than asserted, and why `n_over_budget` - the count of nodes whose flow path demands more fall than the ground gives, by more than the workable depth - is in the same table.  A long path buys depth debt at every metre of it, so the two columns are not independent and the trade is not the one it first looks like.

**And there is a result in this table nobody was looking for.**  Charged at the DN200 minimum, the SHORT-PATH trees are the feasible ones (A 3,845 nodes over budget, D 5,615).  Charged at Table 11's FLATTEST gradient - the one a DN900 or larger may be laid at - the order reverses (D 613, A 1,254): with the gradient cost almost gone, all that is left is whether the pipe points downhill, and the branching wins.  Read together that says the two methods belong to different TIERS: the trunk and the sub mains, which are large and laid flat, want the downhill-biased branching, and the laterals, which are DN200 and pay 5.00 mm/m for every metre, want short paths.  This stage cannot act on that - it has no tiers yet - but the hierarchy stage can, and the numbers are here for it.

## The trade the engineer has to make, and it is not scalarised

Two objectives pull against each other and there is no exchange rate between them that is not invented: **a percentage point of uphill length** against **a kilometre of flow path**.  So the whole weight grid is published, the Pareto-optimal settings are marked, and the shipped default is the knee.  Move `LAMBDA_SLOPE` and `LAMBDA_DETOUR` at the top of `s2_orient.py` to move along the front.

| LAMBDA_SLOPE | LAMBDA_DETOUR | uphill_pct | km      | path_med_m | path_p95_m | path_max_m | n_over_budget | n_over_floor | SHIPPED |
|--------------|---------------|------------|---------|------------|------------|------------|---------------|--------------|---------|
| 8.0          | 0.0           | 26.6       | 1,195.6 | 5,102.2    | 17,255.1   | 22,448.1   | 5,383         | 637          | 0       |
| 8.0          | 0.2           | 27.0       | 1,188.1 | 5,027.9    | 16,762.4   | 22,201.1   | 5,316         | 607          | 0       |
| 8.0          | 0.5           | 27.5       | 1,184.5 | 4,752.2    | 16,265.9   | 22,115.7   | 4,878         | 608          | 0       |
| 8.0          | 1.0           | 28.6       | 1,179.9 | 4,286.0    | 14,600.1   | 22,298.8   | 4,666         | 602          | 0       |
| 5.0          | 0.5           | 29.0       | 1,164.1 | 4,400.1    | 14,406.3   | 22,298.8   | 4,861         | 604          | 0       |
| 5.0          | 1.0           | 31.3       | 1,160.2 | 3,197.9    | 12,059.0   | 21,575.8   | 3,997         | 839          | 0       |
| 8.0          | 2.0           | 32.4       | 1,171.1 | 3,012.0    | 10,951.0   | 19,081.1   | 3,740         | 914          | 0       |
| 2.0          | 0.5           | 35.1       | 1,125.9 | 3,031.9    | 10,091.2   | 15,172.6   | 4,006         | 1,001        | 0       |
| 3.0          | 1.0           | 35.9       | 1,146.5 | 2,724.1    | 8,978.0    | 15,075.3   | 3,606         | 1,018        | 1       |
| 5.0          | 2.0           | 36.7       | 1,161.4 | 2,558.3    | 8,143.1    | 14,697.1   | 3,358         | 1,096        | 0       |
| 8.0          | 4.0           | 37.7       | 1,179.6 | 2,475.3    | 7,800.4    | 13,792.9   | 3,328         | 1,112        | 0       |
| 3.0          | 2.0           | 39.8       | 1,163.7 | 2,414.2    | 7,465.7    | 13,976.6   | 3,302         | 1,180        | 0       |
| 5.0          | 4.0           | 40.0       | 1,179.6 | 2,360.4    | 7,406.6    | 13,693.0   | 3,285         | 1,183        | 0       |
| 2.0          | 2.0           | 41.3       | 1,163.9 | 2,356.1    | 7,311.3    | 13,976.6   | 3,321         | 1,187        | 0       |
| 3.0          | 4.0           | 42.1       | 1,188.2 | 2,307.4    | 7,199.3    | 13,661.9   | 3,800         | 1,261        | 0       |
| 2.0          | 4.0           | 43.5       | 1,190.5 | 2,283.2    | 7,188.8    | 13,661.9   | 3,818         | 1,277        | 0       |
| 1.0          | 4.0           | 44.6       | 1,194.8 | 2,278.5    | 7,187.4    | 13,661.9   | 3,839         | 1,273        | 0       |

`n_over_budget` is the count of the 9,743 nodes whose flow path demands more fall, at the DN200 minimum, than the ground gives - by more than the 10.70 m of workable depth.  `n_over_floor` is the same count charged at the FLATTEST gradient Table 11 allows any pipe (0.75 mm/m, DN900 and above).  **The floor figure is the hard one**: it is what remains when every pipe on the path is a large one laid as flat as the guideline permits, and it cannot be argued away by sizing.

## The bend term, and why it is the weak one

| pass_ | inlets | sharp | sharp_pct | worst_deg | uphill_pct | km       | kept |
|-------|--------|-------|-----------|-----------|------------|----------|------|
| 0     | 9,361  | 2,170 | 23.18     | 23.18     | 35.92      | 1,146.53 | 0    |
| 1     | 9,361  | 2,136 | 22.82     | 23.18     | 35.99      | 1,145.85 | 0    |
| 2     | 9,361  | 2,121 | 22.66     | 23.18     | 35.98      | 1,146.39 | 0    |
| 3     | 9,360  | 2,104 | 22.48     | 23.18     | 36.11      | 1,146.36 | 1    |


A turn is a property of two arcs and an arborescence weight can only see one, so this is iterative re-weighting.  The table is here so the reader can see whether it converged instead of taking a claim for it.

## Sub-networks and the gravity early warning

193 sub-networks, each ending at exactly one outfall.  27 of them contain at least one node whose flow path demands more fall than the ground provides, by more than the 10.70 m of workable depth between the 1.30 m minimum cover and the 12 m cap (both G203-p33).  That is arithmetic available BEFORE any invert is set; it is deliberately pessimistic, because it charges every metre at the DN200 minimum and Table 11 lets DN900 and above be laid at 0.75 mm/m (`DEF_FLOOR_M` is the same sum at that floor).

**Two things overstate this deficit and both should be read before anyone prices a pumping station on it.**  First, the outfall level used is the GROUND at the point the corridor meets the Main Pipe - the trunk's own INVERT is not known (NWS still owe the existing works inlet invert), so every deficit is overstated by the trunk's depth there, somewhere between the 1.30 m minimum cover and the 8.78 m the trunk reaches at the works.  Second, it charges the DN200 minimum for the whole path; `DEF_FLOOR_M` is the same sum at Table 11's flattest gradient and is the figure that cannot be argued away by sizing.

| SUBNET | OUTFALL | N_NODES | KM    | Q_M3D   | X         | Y           | Z     | D_MAIN_M | PATH_MAX_M | FALL_MIN_M | N_BELOW | DEF_MAX_M | DEF_FLOOR_M | N_OVER_BUDGET | GRAVITY                                | N_BREACH | N_RESCUED | WORST_WAS_M | WORST_AFTER_M |
|--------|---------|---------|-------|---------|-----------|-------------|-------|----------|------------|------------|---------|-----------|-------------|---------------|----------------------------------------|----------|-----------|-------------|---------------|
| S001   | N005087 | 1,324   | 158.0 | 6,454.5 | 451,730.8 | 2,572,623.8 | 378.7 | 3.4      | 15,075.3   | -9.7       | 238     | 50.8      | 15.0        | 623           | NOT on gravity inside the cover cap    | 266.0    | 29.0      | 44.4        | 43.3          |
| S002   | N003536 | 1,377   | 122.4 | 5,707.7 | 449,912.1 | 2,568,732.7 | 356.3 | 3.1      | 8,933.6    | -1.7       | 13      | 15.2      | 2.3         | 17            | gravity if the big pipes are laid flat | 17.0     | 0.0       | 15.2        | 15.7          |
| S003   | N003279 | 691     | 77.0  | 3,810.5 | 449,147.8 | 2,567,800.2 | 352.4 | 0.2      | 14,590.6   | -22.7      | 604     | 95.7      | 33.6        | 573           | NOT on gravity inside the cover cap    | 573.0    | 0.0       | 95.7        | 95.8          |
| S004   | N001038 | 468     | 76.7  | 1,419.6 | 445,664.5 | 2,563,174.8 | 327.8 | 4.8      | 11,523.0   | -18.6      | 233     | 59.8      | 24.8        | 268           | NOT on gravity inside the cover cap    | 268.0    | 0.0       | 59.8        | 60.3          |
| S005   | N002822 | 534     | 62.6  | 2,379.0 | 448,426.4 | 2,567,652.6 | 349.7 | 3.7      | 10,955.3   | -13.7      | 211     | 60.5      | 20.3        | 461           | NOT on gravity inside the cover cap    | 461.0    | 0.0       | 60.5        | 59.4          |
| S006   | N007564 | 541     | 59.6  | 2,969.8 | 459,201.4 | 2,568,020.7 | 382.8 | 3.8      | 8,095.7    | -8.3       | 198     | 42.7      | 13.0        | 453           | NOT on gravity inside the cover cap    | 453.0    | 44.0      | 42.7        | 42.0          |
| S007   | N001688 | 345     | 39.1  | 1,600.9 | 446,780.4 | 2,565,204.7 | 341.4 | 1.7      | 9,128.9    | -26.3      | 334     | 71.4      | 33.1        | 299           | NOT on gravity inside the cover cap    | 299.0    | 26.0      | 71.4        | 58.8          |
| S008   | N009409 | 145     | 38.8  | 322.5   | 469,502.0 | 2,564,322.2 | 417.5 | 1.6      | 6,023.9    | -11.5      | 36      | 28.6      | 14.0        | 22            | NOT on gravity inside the cover cap    | 8.0      | 8.0       | 28.6        | 10.6          |
| S009   | N000173 | 117     | 36.7  | 1,450.8 | 442,064.7 | 2,569,072.4 | 334.1 | 1.4      | 13,661.9   | -22.7      | 99      | 91.0      | 32.9        | 72            | NOT on gravity inside the cover cap    | 2.0      | 0.0       | 15.1        | 28.5          |
| S010   | N005516 | 262     | 32.0  | 1,588.2 | 453,065.6 | 2,566,674.5 | 357.4 | 1.4      | 4,936.5    | -3.4       | 18      | 13.8      | 4.4         | 13            | gravity if the big pipes are laid flat | 13.0     | 0.0       | 13.8        | 16.5          |
| S011   | N001463 | 274     | 30.8  | 1,397.8 | 446,428.6 | 2,564,506.5 | 335.3 | 3.9      | 4,463.1    | -4.4       | 74      | 19.2      | 5.7         | 77            | gravity if the big pipes are laid flat | 77.0     | 32.0      | 19.2        | 17.7          |
| S012   | N008125 | 188     | 30.7  | 1,038.1 | 460,845.1 | 2,578,417.2 | 425.6 | 0.1      | 5,574.7    | -4.8       | 52      | 25.1      | 6.6         | 145           | gravity if the big pipes are laid flat | 145.0    | 2.0       | 25.1        | 25.3          |
| S013   | N007761 | 258     | 28.7  | 1,582.6 | 459,838.0 | 2,567,762.9 | 383.1 | 1.5      | 6,726.4    | -1.2       | 5       | 17.2      | 1.3         | 70            | gravity if the big pipes are laid flat | 70.0     | 0.0       | 17.2        | 18.9          |
| S014   | N007524 | 204     | 28.1  | 1,058.1 | 459,106.9 | 2,568,058.9 | 381.8 | 1.8      | 8,610.4    | -20.8      | 187     | 62.4      | 26.9        | 147           | NOT on gravity inside the cover cap    | 147.0    | 0.0       | 62.4        | 63.6          |
| S015   | N004648 | 369     | 23.7  | 994.2   | 451,015.7 | 2,567,194.2 | 352.9 | 4.1      | 3,753.7    | -1.4       | 8       | 4.5       | 1.8         | 0             | gravity                                | 0.0      | 0.0       | -           | -             |
| S016   | N001856 | 198     | 19.2  | 1,040.4 | 447,026.0 | 2,565,695.2 | 342.3 | 2.0      | 5,752.6    | -14.5      | 190     | 43.3      | 18.8        | 149           | NOT on gravity inside the cover cap    | 149.0    | 5.0       | 43.3        | 41.7          |
| S017   | N008025 | 155     | 18.6  | 774.6   | 460,638.5 | 2,578,385.6 | 425.3 | 0.7      | 5,702.3    | 0.0        | 0       | 23.0      | 0.0         | 16            | gravity if the big pipes are laid flat | 16.0     | 0.0       | 23.0        | 23.5          |
| S018   | N007508 | 95      | 15.8  | 363.2   | 459,073.4 | 2,578,155.0 | 422.1 | 3.5      | 3,922.0    | -11.2      | 84      | 30.5      | 14.1        | 47            | NOT on gravity inside the cover cap    | 47.0     | 0.0       | 30.5        | 31.0          |
| S019   | N006167 | 119     | 14.3  | 638.8   | 454,173.9 | 2,575,321.8 | 396.9 | 4.0      | 6,327.5    | -1.2       | 1       | 16.2      | 1.4         | 23            | gravity if the big pipes are laid flat | 1.0      | 0.0       | 10.8        | 19.5          |
| S020   | N008726 | 31      | 13.5  | 196.5   | 462,531.9 | 2,567,268.1 | 389.8 | 1.7      | 4,793.0    | -2.7       | 10      | 10.2      | 3.2         | 0             | gravity                                | 0.0      | 0.0       | -           | -             |
| S021   | N002173 | 139     | 13.1  | 665.3   | 447,505.1 | 2,566,505.5 | 345.0 | 1.0      | 4,487.9    | -13.4      | 135     | 35.9      | 16.8        | 74            | NOT on gravity inside the cover cap    | 74.0     | 9.0       | 35.9        | 35.9          |
| S022   | N005842 | 116     | 11.7  | 408.7   | 453,637.1 | 2,574,113.0 | 388.5 | 4.3      | 3,686.6    | -4.5       | 66      | 20.3      | 6.8         | 40            | gravity if the big pipes are laid flat | 40.0     | 0.0       | 20.3        | 21.5          |
| S023   | N009671 | 54      | 11.1  | 447.3   | 474,582.2 | 2,574,770.8 | 496.5 | 4.3      | 3,819.2    | -4.8       | 6       | 9.5       | 5.5         | 0             | gravity                                | 0.0      | 0.0       | -           | -             |
| S024   | N003611 | 124     | 10.8  | 388.3   | 450,004.2 | 2,570,283.9 | 363.7 | 2.3      | 3,471.7    | -1.6       | 11      | 5.4       | 2.2         | 0             | gravity                                | 0.0      | 0.0       | -           | -             |
| S025   | N009666 | 27      | 9.6   | 60.2    | 474,455.1 | 2,571,775.6 | 493.7 | 1.7      | 4,145.3    | -3.5       | 8       | 8.3       | 4.2         | 0             | gravity                                | 0.0      | 0.0       | -           | -             |


### Asking the neighbours first

**3,619 nodes breach the depth budget.  3,156 of them have a different sub-network somewhere on their flow path, and diverting the branch there keeps 158 of them on gravity - 4.4 % of all the breaches - for a connecting corridor of median 116 m.**  The remaining 3,461 are where the pump ladder legitimately starts.  This is philosophy sec 5's cheap step and it is run before anything here is called a station.  The 25 worst are below; the full list is `run/orient/neighbours.csv`.

| NODE    | SUBNET | WAS_M | DIVERT_AT | DIVERT_DOWN_M | TO_NODE | TO_SUBNET | EXTRA_M | DEF_M | RESCUED |
|---------|--------|-------|-----------|---------------|---------|-----------|---------|-------|---------|
| N000017 | S003   | 95.65 | N003270   | 14,548.10     | N003298 | S160      | 116.20  | 95.81 | 0       |
| N000018 | S003   | 93.45 | N003270   | 14,351.60     | N003298 | S160      | 116.20  | 93.61 | 0       |
| N000023 | S003   | 91.95 | N003270   | 14,406.70     | N003298 | S160      | 116.20  | 92.11 | 0       |
| N000026 | S003   | 91.92 | N003270   | 14,504.50     | N003298 | S160      | 116.20  | 92.09 | 0       |
| N000025 | S003   | 90.80 | N003270   | 14,326.00     | N003298 | S160      | 116.20  | 90.96 | 0       |
| N000020 | S003   | 90.15 | N003270   | 14,131.80     | N003298 | S160      | 116.20  | 90.31 | 0       |
| N000021 | S003   | 89.86 | N003270   | 14,108.30     | N003298 | S160      | 116.20  | 90.03 | 0       |
| N000028 | S003   | 89.79 | N003270   | 14,241.90     | N003298 | S160      | 116.20  | 89.95 | 0       |
| N000024 | S003   | 89.19 | N003270   | 14,110.00     | N003298 | S160      | 116.20  | 89.36 | 0       |
| N000022 | S003   | 89.03 | N003270   | 14,023.30     | N003298 | S160      | 116.20  | 89.19 | 0       |
| N000027 | S003   | 86.77 | N003270   | 13,852.90     | N003298 | S160      | 116.20  | 86.93 | 0       |
| N000029 | S003   | 86.54 | N003270   | 13,942.90     | N003298 | S160      | 116.20  | 86.70 | 0       |
| N000033 | S003   | 86.54 | N003270   | 14,073.30     | N003298 | S160      | 116.20  | 86.70 | 0       |
| N000030 | S003   | 86.41 | N003270   | 13,769.10     | N003298 | S160      | 116.20  | 86.57 | 0       |
| N000035 | S003   | 84.90 | N003270   | 13,941.10     | N003298 | S160      | 116.20  | 85.06 | 0       |
| N000032 | S003   | 84.49 | N003270   | 13,690.10     | N003298 | S160      | 116.20  | 84.65 | 0       |
| N000031 | S003   | 84.34 | N003270   | 13,645.70     | N003298 | S160      | 116.20  | 84.50 | 0       |
| N000036 | S003   | 84.28 | N003270   | 13,822.90     | N003298 | S160      | 116.20  | 84.44 | 0       |
| N000034 | S003   | 84.07 | N003270   | 13,778.60     | N003298 | S160      | 116.20  | 84.24 | 0       |
| N000040 | S003   | 83.97 | N003270   | 13,937.80     | N003298 | S160      | 116.20  | 84.13 | 0       |
| N000037 | S003   | 83.92 | N003270   | 13,864.20     | N003298 | S160      | 116.20  | 84.09 | 0       |
| N000038 | S003   | 83.60 | N003270   | 13,912.20     | N003298 | S160      | 116.20  | 83.76 | 0       |
| N000039 | S003   | 83.23 | N003270   | 13,910.60     | N003298 | S160      | 116.20  | 83.39 | 0       |
| N000041 | S003   | 82.90 | N003270   | 13,994.20     | N003298 | S160      | 116.20  | 83.06 | 0       |
| N000043 | S003   | 81.92 | N003270   | 14,165.80     | N003298 | S160      | 116.20  | 82.08 | 0       |

## Is the client's trunk above the town?

A fair question, because if it were, no tree could drain into it.  Corridor node level less the ground level of the nearest point on the Main Pipe:

| PCTILE        | RELIEF_M |
|---------------|----------|
| 1             | -11.45   |
| 5             | -5.77    |
| 10            | -3.63    |
| 25            | -1.09    |
| 50            | 0.52     |
| 75            | 4.01     |
| 90            | 8.12     |
| 95            | 10.59    |
| 99            | 17.97    |
| mean          | 1.64     |
| share_below_% | 40.83    |


So the trunk sits at about town level and is not the cause.

## The one lever with a big number on it: how close is 'meets the trunk'

The shipped radius is 5 m - a corridor node that literally touches the Main Pipe.  Allowing a short spur instead changes the gravity picture materially, and that is an engineer's decision, not a tolerance:

| MAIN_SNAP_M | roots | km      | uphill_pct | path_med_m | path_p95_m | n_over_budget | n_over_floor | n_below_outfall | n_nodes |
|-------------|-------|---------|------------|------------|------------|---------------|--------------|-----------------|---------|
| 5.0         | 193   | 1,146.5 | 35.9       | 2,724.1    | 8,978.0    | 3,606         | 1,018        | 3,309           | 9,743   |
| 15.0        | 322   | 1,120.9 | 36.4       | 2,292.5    | 8,340.8    | 3,275         | 990          | 3,589           | 9,778   |
| 25.0        | 355   | 1,117.4 | 36.3       | 2,273.2    | 8,332.0    | 3,256         | 995          | 3,572           | 9,781   |
| 50.0        | 501   | 1,092.5 | 36.5       | 1,859.5    | 6,661.4    | 2,765         | 594          | 3,216           | 9,781   |
| 100.0       | 867   | 1,046.1 | 36.4       | 1,467.6    | 5,893.8    | 2,149         | 404          | 2,669           | 9,783   |


## What is NOT decided here

- No chamber, no invert, no diameter, no station.  The levelling stage will still find this tree infeasible in places; that is what the deficit columns are for.
- 30.88 km carrying 763.0 m3/d has no path to the client's Main Pipe at all and is published as `ROLE = island`, oriented to its low end but PROVISIONAL - a corridor with no outfall has no drainage direction in the sense the rest of the layer means.  That is a scope answer, not a routing one.
- Nothing is deleted and no crossing is manufactured.
- The 9,550 tree arcs are 1146.36 km; the other 642.2 km are dead-end heads.  Every head drains to its low end BY CONSTRUCTION, so it contributes nothing to the uphill share - which is why the tree-only figure (36.11 %) is quoted beside the published one and is the honest measure of the orientation itself.

## Every number in this run

| ITEM                       | VALUE                | UNIT | SOURCE                                                                                                                                                                                          |
|----------------------------|----------------------|------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| stage                      | W11b-orient-1.0      |      | this file                                                                                                                                                                                       |
| criteria                   | W11b-criteria-1.0    |      | w11b/criteria.py                                                                                                                                                                                |
| run_utc                    | 2026-09-03T18:52:55Z |      |                                                                                                                                                                                                 |
| corridors_sha1             | ab7684b667cf6153     |      | D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W11b\shp\W11b_roads.gpkg                                                                                                               |
| main_pipe_sha1             | f3594c9bef33f843     |      | D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\SHP\Main Pipe\Main Pipe.shp                                                                                                                   |
| terrain_grid               | R5                   |      | w11b/terrain.py, 5 m working grid                                                                                                                                                               |
| SMIN_DN200                 | 0.0050               | m/m  | G203-p29 Tab 11, DN200 row (5.00 mm/m)                                                                                                                                                          |
| SMIN_FLOOR                 | 0.0008               | m/m  | G203-p29 Tab 11, '900 and above' (0.75 mm/m)                                                                                                                                                    |
| MIN_COVER_M                | 1.3000               | m    | G203-p33 sec 4.6.3                                                                                                                                                                              |
| MAX_COVER_M                | 12.0000              | m    | G203-p33 sec 4.6.3 (recommended 10-12 m)                                                                                                                                                        |
| DEPTH_BUDGET_M             | 10.7000              | m    | MAX_COVER - MIN_COVER, by subtraction                                                                                                                                                           |
| INLET_MIN_DEG              | 90.0000              | deg  | G203-p30, verbatim                                                                                                                                                                              |
| FANOUT_OFFSET_M            | 10.0000              | m    | PROJECT rule, user 2026-08-18                                                                                                                                                                   |
| ADVERSE_MIN_M              | 0.0500               | m    | PROJECT ASSUMPTION - below this a rise is DEM noise                                                                                                                                             |
| RUN_MEDIAN_M               | 68.7440              | m    | MEASURED asbuilt.m_runs() - the ridge-split threshold                                                                                                                                           |
| SIGMA_DZ_M                 | 0.4769               | m    | MEASURED differential DEM error vs NAMA's surveyed levels                                                                                                                                       |
| RIDGE_PROM_MIN_M           | 1.4310               | m    | 3 x SIGMA_DZ_M                                                                                                                                                                                  |
| BUILT_UPHILL_PCT           | 34.1000              | %    | MEASURED asbuilt.m_terrain() - CONTEXT, NOT PERMISSION                                                                                                                                          |
| BUILT_JOINS                | 21                   |      | MEASURED asbuilt joins onto the trunk                                                                                                                                                           |
| BUILT_VORTEX               | 37                   |      | MEASURED vortex drops in the built net                                                                                                                                                          |
| W11A_UPHILL_PCT            | 42.5000              | %    | criteria.BENCHMARKS - the defect W11b exists to fix                                                                                                                                             |
| LAMBDA_SLOPE               | 3.0000               |      | PROJECT, swept: sweep_lambda_slope                                                                                                                                                              |
| SLOPE_CAP                  | 4.0000               |      | PROJECT                                                                                                                                                                                         |
| LAMBDA_DETOUR              | 1.0000               |      | PROJECT, forced by measurement, swept                                                                                                                                                           |
| LAMBDA_BEND                | 1.0000               |      | PROJECT                                                                                                                                                                                         |
| BEND_EQUIV_M               | 150.0000             | m    | PROJECT                                                                                                                                                                                         |
| BEND_PASSES                | 3                    |      | PROJECT                                                                                                                                                                                         |
| JOIN_COST_M                | 0.0000               | m    | PROJECT, swept: sweep_join_cost                                                                                                                                                                 |
| MAIN_SNAP_M                | 5.0000               | m    | PROJECT, swept: sweep_main_snap                                                                                                                                                                 |
| TAU_PA                     | 1.0000               | Pa   | ENGINEER 2026-09-03, GAP-9 open - flagged on output                                                                                                                                             |
| corridors_n                | 12,815               |      | after the ridge pre-split                                                                                                                                                                       |
| corridor_km                | 1,819.3100           | km   |                                                                                                                                                                                                 |
| nodes_n                    | 9,897                |      |                                                                                                                                                                                                 |
| ridge_splits               | 151                  |      | corridors cut at a crest                                                                                                                                                                        |
| outfalls_n                 | 193                  |      | corridor nodes within 5 m of the Main Pipe                                                                                                                                                      |
| main_pipe_km               | 85.4900              | km   | client INPUT                                                                                                                                                                                    |
| closed_basins_n            | 59                   |      | terrain.py                                                                                                                                                                                      |
| closed_basins_forced       | 0                    |      | basins deeper than the cover cap - roots if any                                                                                                                                                 |
| flat_ground_pct            | 58.4100              | %    | corridor length on ground flatter than SMIN_DN200 either way                                                                                                                                    |
| flat_ground_km             | 1,062.7000           | km   | the same, in km                                                                                                                                                                                 |
| tree_arcs                  | 9,550                |      | the drainage tree                                                                                                                                                                               |
| tree_km                    | 1,146.3600           | km   |                                                                                                                                                                                                 |
| joins_realised             | 193                  |      | onto the Main Pipe; NAMA built 21                                                                                                                                                               |
| subnetworks_n              | 193                  |      | each ends at exactly one outfall                                                                                                                                                                |
| heads_n                    | 3,081                |      | dead-end runs: the corridors the tree could not use, all draining to their low end                                                                                                              |
| heads_needing_setback      | 2,887                |      | heads starting at a chamber that already has an outlet, so the chamber stage must set them back 10 m (philosophy sec 4). A HAND-OVER NUMBER, counted here rather than discovered there          |
| junctions_per_km           | 2.3100               | 1/km | MEASURED built network 4.83 (asbuilt.m_runs)                                                                                                                                                    |
| heads_per_km               | 2.6700               | 1/km | MEASURED built network 5.09 (asbuilt.m_runs)                                                                                                                                                    |
| UPHILL_PCT_PUBLISHED       | 23.1500              | %    | THE HEADLINE. W11a 42.5 %, built network 34.1 %                                                                                                                                                 |
| UPHILL_KM_PUBLISHED        | 414.0000             | km   |                                                                                                                                                                                                 |
| uphill_pct_tree_only       | 36.1100              | %    | over the tree arcs alone, excluding dead-end heads                                                                                                                                              |
| uphill_pct_naive           | 33.1300              | %    | THE SAME GRAPH with the method this replaces, on the SAME BASIS - the whole in-play corridor length, dead-end heads included, exactly as UPHILL_PCT_PUBLISHED is measured. This is the evidence |
| uphill_pct_naive_tree_only | 46.6200              | %    | the same tree measured over its own arcs only, to compare with uphill_pct_tree_only                                                                                                             |
| climb_m                    | 2,451.0000           | m    | cumulative climb along the flow                                                                                                                                                                 |
| descent_m                  | 9,507.0000           | m    |                                                                                                                                                                                                 |
| climb_per_km               | 1.3700               | m/km | built network 4.06                                                                                                                                                                              |
| worst_rise_m               | 20.7300              | m    | worst single reach                                                                                                                                                                              |
| path_median_m              | 2,735.0000           | m    | flow path to the outfall                                                                                                                                                                        |
| path_p95_m                 | 8,996.0000           | m    |                                                                                                                                                                                                 |
| path_max_m                 | 15,075.0000          | m    |                                                                                                                                                                                                 |
| published_km               | 1,819.4500           | km   | every corridor                                                                                                                                                                                  |
| island_km                  | 30.8800              | km   | cannot reach the Main Pipe at all                                                                                                                                                               |
| island_q_m3d               | 763.0000             | m3/d |                                                                                                                                                                                                 |
| nodes_over_budget          | 3,619                |      | flow path demands more fall than the ground gives, by more than 10.70 m, charged at the DN200 minimum                                                                                           |
| nodes_over_budget_floor    | 999                  |      | the same charged at G203-p29 Tab 11's flattest gradient (0.75 mm/m) - THE HARD NUMBER: it cannot be argued away by sizing                                                                       |
| nodes_total                | 9,743                |      | nodes with a flow path to an outfall                                                                                                                                                            |
| subnets_over_budget        | 27                   |      | deficit beyond the 10.70 m depth budget                                                                                                                                                         |
| breaching_nodes            | 3,619                |      | nodes whose flow path demands more fall than the ground gives, by more than the 10.70 m depth budget                                                                                            |
| breaching_with_a_neighbour | 3,156                |      | of those, the ones with a different sub-network somewhere on their flow path, so the neighbour question can even be asked                                                                       |
| neighbour_rescues          | 158                  |      | of those, the ones a NEIGHBOURING sub-network keeps on gravity. Philosophy sec 5's cheap step, run before anything is called a station                                                          |
