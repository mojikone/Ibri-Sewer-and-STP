# W11b stage 5 - flow accumulation

_2026-09-03 12:16 - W11b-s5_flows-1.0 - TRACTIVE STRESS tau = 1 Pa - AN ASSUMPTION, NOT A GUIDELINE VALUE. PAM-GUD-203 sec 4.2.2.1 (p27) gives the equation Smin = K tau^1.23 Q^-0.461 and no numeric design tau (GAP-9). At tau = 1.0 Pa the required gradients are the shallowest the method allows, so the pipes are shallower and the stations fewer. If NWS return tau = 2.0 Pa every tractive-governed gradient rises by 2.346x and every level downstream of it changes._

## The health check

```
======================================================================================
  HEALTH CHECK - WHAT SHARE OF THE PLACED LOAD DOES THE BIGGEST PIPE CARRY?
======================================================================================
  13.42 %   (10,025 m3/d of 74,701 m3/d placed)
  NAMA's own built network, same accumulator, same plot loads: 61.17 % on 3 outfalls (95.4 km, 74,701 m3/d placed)
  193 outfalls; the largest takes 13.42 %, the top ten 63.24 %; HHI 0.0579
  98.98 % of the placed load reaches an outfall; 763 m3/d is on pieces that drain nowhere
  the largest PEAK flow on any gravity pipe is 234.7 L/s; 989 reaches (140 km) carry nothing at all

  READ THIS BEFORE THE NUMBER: in a network draining to ONE works the top pipe
  carries nearly all of the load. It does not here, and the reason is structural,
  not hydraulic - the client's Main Pipe is an INPUT and is not in this graph, so
  every one of these outfalls is a SEPARATE connection to it. The figure that would
  compare like with like is TRUNK_IF_JOINED_PCT, and it is a hypothetical until a
  stage actually routes the Main Pipe. What the number DOES measure, honestly, is
  how much of the load any single designed gravity pipe would ever have to carry.
======================================================================================
```

| ITEM | VALUE | UNIT | WHAT | BENCHMARK | SOURCE |
|---|---|---|---|---|---|
| TOP_PIPE_PCT | 13.42 | % | share of the PLACED load carried by the single biggest pipe | 61.17 | s5_flows health check; benchmark = the same accumulator over NAMA's built network |
| TOP_PIPE_M3D | 10,024.9 | m3/d | that pipe is E0006194 (N005120->N005087), subnet S001 | 45,693.9 | arcs.QADF_M3D. The benchmark's ABSOLUTE m3/d is not comparable - the nearest-pipe rule has no cap, so the built 95.4 km receives the whole study area's load. Its SHARE is what compares, and share is what this check measures |
| DELIVERED_PCT | 98.98 | % | share of the placed load that reaches an outfall at all |  | conservation: delivered / placed |
| LOST_M3D | 762.6 | m3/d | load on pieces that drain nowhere - H15 forbids these, they are NOT dropped silently |  | arcs where DELIVERED = 0 |
| N_OUTFALL | 193 | - | separate discharge points. Each is a connection to the client's Main Pipe, which is an INPUT and is NOT in this graph | 3 | nodes.KIND == 'outfall', written by s2_orient |
| BIGGEST_OUTFALL_PCT | 13.42 | % | share of the placed load arriving at the largest single outfall |  | in_q at outfalls / placed |
| TOP10_OUTFALL_PCT | 63.24 | % | the ten largest outfalls together |  | in_q at outfalls / placed |
| OUTFALL_HHI | 0.0579 | - | Herfindahl concentration of load over outfalls. 1.00 = one works; 1/N = perfectly split |  | sum of squared outfall shares |
| TRUNK_IF_JOINED_PCT | 98.98 | % | what the client's Main Pipe would carry below the last connection, IF every outfall discharges into it. A STATED HYPOTHETICAL - the Main Pipe is not in this graph and this stage has not routed it |  | hypothetical, tagged |
| EMPTY_OUTFALL | 16 | - | outfalls with NOTHING draining to them - a connection to the client's Main Pipe that serves nobody. Not this stage's to fix: the flow arithmetic is what exposes them and the resolution is s2's |  | in_q at outfalls == 0 |
| TRUNK_IF_JOINED_LS | 1,362.2 | L/s | and the PEAK flow that trunk would carry - Merrimack on the whole delivered load plus the system infiltration. A STATED HYPOTHETICAL, on the same footing as TRUNK_IF_JOINED_PCT: it is the number a trunk-sizing stage would start from, not a number this stage has designed |  | G201-p71 7.4.2 on the delivered total |
| MAX_PIPE_LS | 234.65 | L/s | the largest PEAK flow any gravity pipe in this design carries. This is the number the sizing stage starts from, and it is small: nothing here needs a large-diameter sewer |  | arcs.QPK_MONO |
| ZERO_FLOW_KM | 139.5 | km | 989 reaches have NOTHING draining through them - no load of their own and none from above. Pruning candidates for the hierarchy stage (philosophy sec 4, 'no fingers'), not a defect of this one |  | arcs.QADF_M3D <= 0 |
| INFIL_SYSTEM_LS | 14.905 | L/s | system infiltration = 720 L/d/km x delivered network length |  | G201-p72 7.4.3 |
| INFIL_IF_SUMMED_LS | 421.3 | L/s | THE WRONG ANSWER, printed on purpose: the same column summed over every reach instead of over the outfalls |  | the W11a defect, reproduced so it cannot recur unnoticed |

## What the biggest pipe number means, and what it does not

It is the honest measure of **how much load any one designed gravity pipe would ever have to carry**, and on this design it is small because the network reaches the client's Main Pipe at **193 separate points**. The Main Pipe is an INPUT to this project and it is not in this graph, so those connections are not modelled as joining. `TRUNK_IF_JOINED_PCT` is what the trunk would carry if they all do; it is tagged a hypothetical and it stays one until a stage routes the trunk.

The benchmark beside it is not a target somebody chose. It is the same accumulator, on the same plot loads, run over NAMA's own built network - the pipe that is in the ground and works.

## Conservation - every identity, computed twice

| CHECK | A | B | RESID | UNIT | TOL | PASS | NOTE |
|---|---|---|---|---|---|---|---|
| plot load allocated == plot load available | 74,701.2 | 74,701.2 | 0 | m3/d | 1e-06 | 1 | nearest arc, no cap (A-FLOW-4): nothing can fall outside a radius |
| properties allocated == properties available | 98,681.1 | 98,681.1 | 0 | - | 1e-06 | 1 | same allocation, same basis - this is why the load is not read from s2 |
| local load on arcs == plot load allocated | 74,701.2 | 74,701.2 | 0 | m3/d | 1e-06 | 1 | the local column is the allocation, transposed onto arcs |
| delivered + undelivered == placed | 74,701.2 | 74,701.2 | 0 | m3/d | 1e-06 | 1 | load that reaches an outfall plus load that cannot; there is no third bucket |
| delivered sewer length == length of arcs that reach an outfall | 1,788,570.3 | 1,788,570.3 | 0 | m | 0.001 | 1 | every metre drains to exactly ONE outfall, so accumulating length cannot double-count it |
| infiltration: rate x length == sum of LOCAL values | 14.9048 | 14.9048 | 0 | L/s | 1e-06 | 1 | G201-p72 7.4.3, 720 L/d/km. THE definition is rate x network length |
| infiltration: rate x length == cumulative value at the OUTFALLS ONLY | 14.9048 | 14.9048 | 0 | L/s | 1e-06 | 1 | the cumulative column IS summable, but only over a partition - the outfalls |
| node Q at an outfall == what arrives there | 73,938.6 | 73,938.6 | 0 | m3/d | 1e-06 | 1 | the node layer and the arc layer come from the same accumulation, not two solves |
| route local + branch local == placed | 74,701.2 | 74,701.2 | 0 | m3/d | 1e-06 | 1 | A-FLOW-5: every arc is one or the other and no arc is both |
| this stage's allocation == s2_orient's Q_M3D, in total | 74,701.2 | 74,701.6 | -0.4096 | m3/d | 0.5 | 1 | per-arc agreement: 12,501 of 12,816 identical, largest single difference 10.0 m3/d, correlation 0.998766. Two allocations, one answer - the tolerance is s2's 3-dp rounding |

## Infiltration, and the trap

G201-p72 7.4.3 gives **720 L/d/km of sewer** for a new network. The design value on a reach has to be CUMULATIVE - a reach forty hops down carries every kilometre above it - and that is exactly why the column must never be summed. The right total is the rate times the NETWORK length. Both are printed:

| ITEM | VALUE | UNIT | SOURCE | NOTE |
|---|---|---|---|---|
| rate | 720 | L/d/km | G201-p72 7.4.3, new networks | 'Infiltration due to storm water is not considered' - same clause |
| network length, delivered | 1,788.6 | km | accumulated, checked against the arc lengths | arcs that reach an outfall |
| network length, published | 1,819.4 | km | sum of arcs.LEN_M | includes the pieces that drain nowhere |
| SYSTEM INFILTRATION | 14.9048 | L/s | THE definition: rate x network length | one function, contract.published('infiltration_system_ls') |
| system infiltration, published length | 15.162 | L/s | rate x published length | the upper bound if every piece is built |
| SUM of the per-reach cumulative column | 421.3 | L/s | arcs.QINF_LS summed - THE WRONG ANSWER | printed on purpose |
| overstatement factor | 28.3 | x | wrong / right on THIS network | W11a shipped 1,259 L/s against 14.5 - 87x - the same mistake |
| sum of the per-reach LOCAL column | 14.9048 | L/s | arcs.QINF_LOC summed over delivered arcs | THIS one is summable, and it lands on the definition |
| infiltration as a share of average dry weather flow | 1.742 | % | derived | G201-p72 allows 10 % for an EXISTING inland network; a new one on this length is far below that, which is the point of the 720 L/d/km rule |

## The peak factor

G201-p71 7.4.2, verbatim: *"The Merrimack formula is to be used for calculating the peak factors for wastewater discharge for an area (catchment or sub catchment) having over 100 properties."* Below 100 the guideline prescribes **nothing**. Merrimack RISES as the catchment shrinks, so extrapolating it invents factors on the pipes where it was never validated; and holding it at 1.0 - which `criteria.peak_factor()` currently does - would size every lateral at average flow. This stage holds it at the value Merrimack gives AT the threshold, **3.621**, and every such row says `PF_METH = 'held'`.

| ITEM | VALUE | UNIT | SOURCE | NOTE |
|---|---|---|---|---|
| held peak factor | 3.6214 | - | A-FLOW-2: Merrimack AT the 100-property threshold | evaluated at 100 x 0.7570 m3/d/property = 75.70 m3/d |
| load per property, measured | 0.757 | m3/d/property | allocated load / allocated properties, ALL property types | criteria.PLOT_QADF_M3D is 0.9113 and it is NOT the same quantity: it is OCCUPANCY x WWG_LCD, and WWG_LCD already spreads the non-domestic and governmental volume over the DOMESTIC population, so it is a per-DOMESTIC-property figure. G201-p71's threshold counts properties without qualification, so the threshold is evaluated on all of them |
| domestic load per property, measured | 0.7416 | m3/d/property | plot_loads Q_DOM_M3D / N_DOM | reproduces OCCUPANCY x LPCD_WATER x RETURN_DOM / 1000 = 5.32 x 164 x 0.85 / 1000 = 0.74161 EXACTLY (G201-p59-60 Table 11 water, G201-p71 Table 19 return ratio) - the load basis and the criteria agree where they are measuring the same thing |
| held peak factor on the criteria per-property figure | 3.541 | - | sensitivity | the alternative basis, published so the choice is visible |
| criteria.peak_factor() below the threshold | 1 | - | criteria.py | DISAGREES with this stage. See A-FLOW-2 - holding at 1.0 sizes every lateral at average flow |
| reaches on the held factor | 9,976.0 | - | PF_METH | 77.8 % of reaches, 1,450.3 km |
| reaches on Merrimack | 2,840.0 | - | PF_METH | 369.1 km, carrying 92.6 % of the accumulated flow |
| peak factor, min on a LOADED reach | 2.005 | - | arcs.PF where QADF_M3D > 0 | the largest catchment peaks least. 989 reaches carry nothing at all and are given PF = 1.0, which is arithmetic, not a factor |
| peak factor, max | 3.7185 | - | arcs.PF | G201-p72 RECOMMENDS not exceeding 5.0 |
| reaches above the recommended 5.0 | 0 | - | G201-p72 NOTE | reported, NEVER truncated |
| reaches where the peak flow would FALL downstream | 0 | - | MONO_FIX | it can happen at the held/Merrimack boundary, which is a step, because the switch is on property count and the curves meet only at the project-average load per property |
| largest monotonicity correction | 0 | L/s | QPK_MONO - QPK_LS | a sizing stage must carry QPK_MONO, not QPK_LS, or a pipe is smaller than the one above it |
| whole-network peak factor | 1.5744 | - | Merrimack on the delivered load | what the works inlet would see if everything arrived together |
| Peltier on the same total | 1.5342 | - | G201-p72, the IMP2024 alternative | carried for comparison only. NOT applied anywhere |

**This is a real disagreement with `criteria.py`, not a rounding.** It is A-FLOW-2, it is on the assumptions layer, and the owner of `criteria.py` has to settle it.

## What the sizing stage is being handed

| BAND_LS | N | KM | PCT_KM | NOTE |
|---|---|---|---|---|
| 0 - 1 | 7669 | 1,087.9 | 59.79 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 1 - 2 | 1479 | 244.59 | 13.44 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 2 - 5 | 1536 | 206.17 | 11.33 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 5 - 10 | 843 | 116.55 | 6.41 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 10 - 25 | 633 | 80.1 | 4.4 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 25 - 50 | 324 | 42.78 | 2.35 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 50 - 100 | 233 | 30.96 | 1.7 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 100 - 250 | 99 | 10.4 | 0.57 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 250 - 500 | 0 | 0 | 0 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |
| 500 and above | 0 | 0 | 0 | presentation bands only - the diameter follows the flow and the gradient (G203-p29, H8), never a band |

## How each kind of arc was treated

The orientation stage publishes a drainage **tree** plus the corridors it did not need. Those still need a sewer, and at a junction exactly one pipe leaves (philosophy sec 4), so a leftover corridor is a **source branch**: its own load, delivered at its downstream node, taking nothing off the node it starts at.

| ROLE | N | KM | Q_LOC_M3D | PCT_LOAD | N_PROP | ROUTE | BRANCH | DELIVERED | TREATMENT |
|---|---|---|---|---|---|---|---|---|---|
| head | 3081 | 642.08 | 28,183.4 | 37.73 | 37,453.0 | 0 | 3081 | 3081 | SOURCE BRANCH (A-FLOW-5): its own local load only, delivered at its downstream node |
| island | 184 | 30.88 | 762.6 | 1.02 | 989 | 0 | 184 | 0 | SOURCE BRANCH (A-FLOW-5): its own local load only, delivered at its downstream node |
| ring | 1 | 0.13 | 3.6 | 0 | 5 | 0 | 1 | 1 | SOURCE BRANCH (A-FLOW-5): its own local load only, delivered at its downstream node |
| tree | 9550 | 1,146.4 | 45,751.5 | 61.25 | 60,235.0 | 9550 | 0 | 9550 | carries everything from upstream, plus its own load |
| head, chained | 743 | 139.89 | 5,488.1 | 7.35 | 7,223.0 | 0 | 743 | 743 | THE RISK IN A-FLOW-5: these head arcs START where another head arc ENDS. If they are really one street draining end to end, the lower segment is under-loaded by the upper one's load. It is not lost - it enters the tree at the shared node - but it is on the wrong pipe |

## Where the load ends up

| OUTFALL | SUBNET | X | Y | GRD_M | Q_ADF_M3D | N_PROP | KM | PCT_LOAD | PF | PF_METH | QINF_LS | Q_PK_LS | M_PER_PROP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N005087 | S001 | 451,730.8 | 2,572,623.8 | 378.67 | 10,024.9 | 13,441.0 | 241.53 | 13.42 | 2.005 | merrimack | 2.0127 | 234.65 | 18 |
| N003536 | S002 | 449,912.1 | 2,568,732.7 | 356.27 | 9,111.8 | 12,247.0 | 189.26 | 12.198 | 2.028 | merrimack | 1.5772 | 215.45 | 15.5 |
| N003279 | S003 | 449,147.8 | 2,567,800.2 | 352.37 | 6,019.6 | 7,725.0 | 120.85 | 8.058 | 2.133 | merrimack | 1.0071 | 149.62 | 15.6 |
| N007564 | S006 | 459,201.4 | 2,568,020.7 | 382.8 | 5,790.0 | 7,535.0 | 105.32 | 7.751 | 2.143 | merrimack | 0.8777 | 144.49 | 14 |
| N002822 | S005 | 448,426.4 | 2,567,652.6 | 349.69 | 3,398.6 | 4,564.0 | 88.59 | 4.55 | 2.285 | merrimack | 0.7383 | 90.62 | 19.4 |
| N005516 | S010 | 453,065.6 | 2,566,674.5 | 357.39 | 3,197.5 | 4,329.0 | 58.39 | 4.28 | 2.302 | merrimack | 0.4866 | 85.68 | 13.5 |
| N001688 | S007 | 446,780.4 | 2,565,204.7 | 341.36 | 2,926.6 | 3,874.0 | 67.96 | 3.918 | 2.327 | merrimack | 0.5663 | 79.39 | 17.5 |
| N007761 | S013 | 459,838.0 | 2,567,762.9 | 383.15 | 2,895.2 | 3,731.0 | 50.56 | 3.876 | 2.33 | merrimack | 0.4213 | 78.5 | 13.6 |
| N001463 | S011 | 446,428.6 | 2,564,506.5 | 335.34 | 1,987.9 | 2,616.0 | 46.75 | 2.661 | 2.439 | merrimack | 0.3896 | 56.51 | 17.9 |
| N000173 | S009 | 442,064.7 | 2,569,072.4 | 334.13 | 1,890.4 | 2,422.0 | 43.5 | 2.531 | 2.453 | merrimack | 0.3625 | 54.03 | 18 |
| N001038 | S004 | 445,664.5 | 2,563,174.8 | 327.82 | 1,868.8 | 2,552.0 | 108.63 | 2.502 | 2.457 | merrimack | 0.9052 | 54.05 | 42.6 |
| N001856 | S016 | 447,026.0 | 2,565,695.2 | 342.26 | 1,831.7 | 2,409.0 | 34.11 | 2.452 | 2.463 | merrimack | 0.2843 | 52.5 | 14.2 |
| N007524 | S014 | 459,106.9 | 2,568,058.9 | 381.8 | 1,769.3 | 2,328.0 | 48.12 | 2.369 | 2.473 | merrimack | 0.401 | 51.04 | 20.7 |
| N004648 | S015 | 451,015.7 | 2,567,194.2 | 352.94 | 1,532.2 | 1,920.0 | 33.74 | 2.051 | 2.517 | merrimack | 0.2812 | 44.92 | 17.6 |
| N008125 | S012 | 460,845.1 | 2,578,417.2 | 425.64 | 1,423.7 | 1,812.0 | 47.6 | 1.906 | 2.539 | merrimack | 0.3967 | 42.23 | 26.3 |
| N006167 | S019 | 454,173.9 | 2,575,321.8 | 396.94 | 1,311.7 | 1,755.0 | 28.76 | 1.756 | 2.564 | merrimack | 0.2397 | 39.17 | 16.4 |
| N008025 | S017 | 460,638.5 | 2,578,385.6 | 425.27 | 1,249.3 | 1,712.0 | 28.67 | 1.672 | 2.58 | merrimack | 0.2389 | 37.54 | 16.7 |
| N002173 | S021 | 447,505.1 | 2,566,505.5 | 345.05 | 1,043.6 | 1,386.0 | 19.06 | 1.397 | 2.636 | merrimack | 0.1589 | 32 | 13.8 |
| N005842 | S022 | 453,637.1 | 2,574,113.0 | 388.5 | 751.4 | 989 | 20.73 | 1.006 | 2.743 | merrimack | 0.1728 | 24.03 | 21 |
| N006617 | S029 | 455,118.7 | 2,567,616.2 | 365.08 | 666.1 | 899 | 15.2 | 0.892 | 2.784 | merrimack | 0.1267 | 21.59 | 16.9 |
| N003611 | S024 | 450,004.2 | 2,570,283.9 | 363.68 | 649.9 | 863 | 15.84 | 0.87 | 2.792 | merrimack | 0.132 | 21.13 | 18.4 |
| N007508 | S018 | 459,073.4 | 2,578,155.0 | 422.11 | 637 | 832 | 25.17 | 0.853 | 2.799 | merrimack | 0.2098 | 20.85 | 30.2 |
| N003373 | S031 | 449,486.1 | 2,568,501.4 | 354.72 | 598.5 | 796 | 11.14 | 0.801 | 2.82 | merrimack | 0.0928 | 19.63 | 14 |
| N009028 | S028 | 464,070.6 | 2,577,929.1 | 435.04 | 595.6 | 788 | 12.23 | 0.797 | 2.821 | merrimack | 0.1019 | 19.55 | 15.5 |
| N006143 | S026 | 454,131.5 | 2,575,214.7 | 395.92 | 535.8 | 705 | 13.03 | 0.717 | 2.858 | merrimack | 0.1086 | 17.83 | 18.5 |

_168 more rows in the CSV._

## Sub-networks

`TOP_PCT` is the health check applied one sub-network at a time. Inside a sub-network the answer SHOULD be close to 100 %: everything that sub-network collects leaves through one pipe.

**Five sub-networks have no arcs at all** and sixteen outfalls receive nothing - a connection to the client's Main Pipe that serves nobody. That is not a flow defect, it is what the flow arithmetic exposes about the orientation, and the resolution belongs to stage 2.

| SUBNET | N_ARCS | KM | Q_LOC_M3D | N_PROP | TOP_M3D | TOP_PCT | PCT_PLACED | QPK_LS |
|---|---|---|---|---|---|---|---|---|
| S001 | 1694 | 241.53 | 10,024.9 | 13,441.0 | 10,024.9 | 100 | 13.42 | 234.65 |
| S002 | 1855 | 189.26 | 9,111.8 | 12,247.0 | 7,887.6 | 86.56 | 12.198 | 189.77 |
| S003 | 893 | 120.85 | 6,019.6 | 7,725.0 | 5,944.8 | 98.76 | 8.058 | 147.95 |
| S006 | 763 | 105.32 | 5,790.0 | 7,535.0 | 5,790.0 | 100 | 7.751 | 144.47 |
| S005 | 652 | 88.59 | 3,398.6 | 4,564.0 | 3,396.4 | 99.94 | 4.55 | 90.58 |
| S010 | 364 | 58.39 | 3,197.5 | 4,329.0 | 3,061.8 | 95.75 | 4.28 | 82.46 |
| S007 | 479 | 67.96 | 2,926.6 | 3,874.0 | 2,926.6 | 100 | 3.918 | 79.39 |
| S013 | 372 | 50.56 | 2,895.2 | 3,731.0 | 2,837.0 | 97.99 | 3.876 | 77.07 |
| S011 | 350 | 46.75 | 1,987.9 | 2,616.0 | 1,982.4 | 99.72 | 2.661 | 56.36 |
| S009 | 141 | 43.5 | 1,890.4 | 2,422.0 | 1,332.2 | 70.47 | 2.531 | 39.6 |
| S004 | 571 | 108.63 | 1,868.8 | 2,552.0 | 1,861.0 | 99.58 | 2.502 | 53.85 |
| S016 | 264 | 34.11 | 1,831.7 | 2,409.0 | 1,831.7 | 100 | 2.452 | 52.5 |
| S014 | 260 | 48.12 | 1,769.3 | 2,328.0 | 1,769.3 | 100 | 2.369 | 51.05 |
| S015 | 487 | 33.74 | 1,532.2 | 1,920.0 | 1,467.7 | 95.79 | 2.051 | 43.23 |
| S012 | 236 | 47.6 | 1,423.7 | 1,812.0 | 1,407.1 | 98.83 | 1.906 | 41.8 |
| S019 | 165 | 28.76 | 1,311.7 | 1,755.0 | 1,265.5 | 96.48 | 1.756 | 37.96 |
| S017 | 213 | 28.67 | 1,249.3 | 1,712.0 | 1,241.6 | 99.38 | 1.672 | 37.34 |
| S021 | 175 | 19.06 | 1,043.6 | 1,386.0 | 941.2 | 90.18 | 1.397 | 29.23 |
| S022 | 154 | 20.73 | 751.4 | 989 | 685.4 | 91.21 | 1.006 | 22.17 |
| S029 | 100 | 15.2 | 666.1 | 899 | 666.1 | 100 | 0.892 | 21.58 |
| S024 | 163 | 15.84 | 649.9 | 863 | 643 | 98.94 | 0.87 | 20.93 |
| S018 | 126 | 25.17 | 637 | 832 | 611.4 | 95.98 | 0.853 | 20.11 |
| S031 | 107 | 11.14 | 598.5 | 796 | 562.2 | 93.95 | 0.801 | 18.57 |
| S028 | 85 | 12.23 | 595.6 | 788 | 589.5 | 98.97 | 0.797 | 19.37 |
| S026 | 119 | 13.03 | 535.8 | 705 | 534.7 | 99.8 | 0.717 | 17.8 |

_163 more rows in the CSV._

## Load that reaches no outfall

| ROLE | N | KM | Q_M3D | N_PROP | NOTE |
|---|---|---|---|---|---|
| island | 184 | 30.875 | 762.6 | 989 | H15: a piece that drains nowhere is never legal. This load is NOT dropped - it is published here and it is in the denominator of the health check |
| TOTAL | 184 | 30.875 | 762.6 | 989 | resolution is s2's, not this stage's: connect, or serve by another system (philosophy sec 8a) |

## The allocation

Nearest arc, exactly once per plot, **no distance cap** (A-FLOW-4). A cap is how W10 lost 1,233 m3/d without anyone noticing. The distance curve is published instead, so the reader can judge the reach of the drawing rather than inherit an assumed radius:

| WITHIN_M | PCT_LOAD | PCT_PROP | PCT_PLOTS |
|---|---|---|---|
| 10 | 1.86 | 1.81 | 1.92 |
| 20 | 16.93 | 17.14 | 16.59 |
| 30 | 66.24 | 67.31 | 70.49 |
| 40 | 80.49 | 81.84 | 83.48 |
| 50 | 87.02 | 88.22 | 88.79 |
| 75 | 93.29 | 94.22 | 94.05 |
| 100 | 95.69 | 96.37 | 96.05 |
| 150 | 97.92 | 98.31 | 97.9 |
| 200 | 98.63 | 98.92 | 98.64 |
| 300 | 99.43 | 99.54 | 99.33 |
| 500 | 99.75 | 99.78 | 99.66 |
| 1,000.0 | 99.96 | 99.96 | 99.95 |

| | |
|---|---|
| plots_total | 64,071 |
| plots_with_load | 56,414 |
| q_total_m3d | 74,701.17 |
| q_allocated_m3d | 74,701.17 |
| prop_total | 98,681.11 |
| prop_allocated | 98,681.11 |
| arcs_with_load | 10,093 |
| arcs_without_load | 2,723 |
| dist_median_m | 25.27 |
| dist_p90_m | 54.11 |
| dist_max_m | 2,575.92 |
| q_per_property_m3d | 0.76 |

## Every number, with its source

| ITEM | VALUE | UNIT | SOURCE |
|---|---|---|---|
| stage | W11b-s5_flows-1.0 | - | this file |
| contract | W11b-contract-1.0 | - | w11b.contract |
| tau | 1 | Pa | ASSUMED, GAP-9 - flagged on every row as TAU_FLAG |
| arcs | 12816 | - | s2_orient arcs, read |
| nodes | 9897 | - | s2_orient nodes, read |
| network length, published | 1,819.5 | km | sum LEN_M |
| network length, delivered | 1,788.6 | km | accumulated to the outfalls |
| plots read | 64071 | - | D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W10\shp\W10_plot_loads.gpkg |
| plots with saturated load | 56414 | - | Q_AVG_M3D > 0 |
| properties | 98,681.1 | - | plot_loads.N_PROP, allocated once each |
| placed load | 74,701.2 | m3/d | allocation, A-FLOW-4 |
| delivered load | 73,938.6 | m3/d | accumulated to the outfalls |
| undelivered load | 762.6 | m3/d | arcs that reach no outfall - H15 |
| load per property, measured | 0.757 | m3/d/property | placed / properties |
| occupancy | 5.32 | people/property | PROJECT, derived 2026-08-30 |
| wastewater generation | 171.3 | L/c/d | PROJECT, derived |
| peak factor formula | Qpdf = 2.65 Qadf^0.879, both Ml/d | - | G201-p71 7.4.2, read from the PDF 2026-09-03 |
| peak factor threshold | 100 | properties | G201-p71 7.4.2 'having over 100 properties' |
| held peak factor | 3.6214 | - | A-FLOW-2, PROJECT DECISION - Merrimack AT the threshold |
| peak factor recommendation | 5 | - | G201-p72 NOTE - a recommendation; reported, never truncated |
| infiltration rate | 720 | L/d/km | G201-p72 7.4.3, new networks |
| SYSTEM infiltration | 14.9048 | L/s | contract.published('infiltration_system_ls') - rate x NETWORK length |
| STP design margin | 0.1 | - | G201-p73 7.4.5 - carried at the works, never on a pipe (A-FLOW-7) |
| works inlet Qadf, delivered | 73,938.6 | m3/d | delivered load; add the margin at the works, not here |
| works inlet Qadf + 10 % margin | 81,332.4 | m3/d | G201-p73 7.4.5 |
| biggest pipe, Qadf | 10,024.9 | m3/d | arcs.QADF_M3D |
| trunk peak flow IF every outfall joins | 1,362.2 | L/s | HYPOTHETICAL - Merrimack on the delivered load plus system infiltration. The Main Pipe is an INPUT and this stage has not routed it |
| biggest pipe, Qpeak | 234.65 | L/s | arcs.QPK_MONO |
| biggest pipe share of placed load | 13.42 | % | contract.published('top_pipe_load_share_pct') |
| outfalls | 193 | - | nodes.KIND |
| arcs carrying no load | 2723 | - | corridors with no plot nearest to them - they still carry upstream flow |
| arcs with zero accumulated flow | 989 | - | nothing at all drains through them - candidates for pruning at stage 4 |
| length carrying zero flow | 139.5 | km | arcs.QADF_M3D <= 0 |
| median accumulated Qadf | 15.43 | m3/d | arcs.QADF_M3D |
| p95 accumulated Qadf | 852.6 | m3/d | arcs.QADF_M3D |
| median peak flow | 0.65 | L/s | arcs.QPK_MONO |
| p95 peak flow | 26.83 | L/s | arcs.QPK_MONO |
| max upstream length on one reach | 241.35 | km | arcs.UPS_LEN_M - the flow path that reach sits at the bottom of |
| max reaches draining through one reach | 1693 | - | arcs.UPS_ARCS |
| as-built benchmark: biggest pipe share | 61.17 | % | the SAME accumulator over NAMA's 3,265 built pipes and the same plot loads |
| as-built benchmark: built length | 95.4 | km | asbuilt.pipes |
| as-built benchmark: terminals | 3 | - | asbuilt topology |
| as-built benchmark: load placed on it | 74,701.2 | m3/d | nearest built pipe, no cap - the same rule, so the two are comparable |

## Assumptions

| ID | KIND | WHAT | SOURCE |
|---|---|---|---|
| A-FLOW-1 | project assumption | Infiltration is UNPEAKED and added AFTER the sanitary peak factor. | G201-p72 7.4.3 is silent |
| A-FLOW-2 | project decision | Below 100 properties the peak factor is HELD at the value Merrimack gives AT 100 properties, not at 1.0 and not extrapolated. | G201-p71 7.4.2 (threshold), plateau is OURS |
| A-FLOW-3 | project assumption | A plot's load enters the network at the UPSTREAM node of the arc nearest it, so that arc carries its own local load over its whole length. | practice; no guideline states a loading point |
| A-FLOW-4 | project doctrine | Each plot is allocated to the NEAREST arc, exactly once, with NO distance cap. | s1_roads; W10 defect |
| A-FLOW-5 | project decision | An arc that is not in the drainage tree (ROLE head / island / ring) is a SOURCE BRANCH: it carries only its own local load and delivers it at its downstream node. | philosophy sec 4 |
| A-FLOW-6 | GAP | SATURATION horizon only. There are no start-year flows. | data; G201-p73 phasing not modelled |
| A-FLOW-7 | reading | The 10 % STP design margin is carried at the WORKS total only, never on a pipe. | G201-p73 7.4.5 |

Full text, with what changes if each is wrong, is on the `assumptions` layer and in `run/flows/assumptions.csv`.

## What is NOT here

- **No start-year flows.** The plot loads carry a saturation figure and no phasing, so philosophy sec 6's start-year self-cleansing check cannot run from this data. A-FLOW-6.
- **No retention time.** Septicity needs a velocity and a velocity needs a diameter. `UPS_LEN_M` is published so the sizing stage can compute it in one pass.
- **No sizing, no levels, no tiers.** This stage publishes flow.

## Outputs

- `W11b\shp\W11b_flows.gpkg` - 15 layers
- `W11b_flows_peak.kmz` - present.py view 'flow', 12,816 reaches
- `W11b\run\flows/*.csv` - every table above
- `W11b\run\flows\FLOWS.md` - this file