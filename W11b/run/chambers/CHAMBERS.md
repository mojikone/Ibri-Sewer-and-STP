# W11b stage 4 - chambers, and every plot's way into them

_2026-09-03 12:37 - W11b-chambers-1.0 - tau=1 Pa ASSUMED (GAP-9)_

## The headline

**56,935 chambers on 1,491.9 km - 38.2 per km against the built network's 34.2** - and **53,018 of 56,414 load-bearing plots connected, carrying 70,405 of 74,701 m3/d (94.2 %)** on 508.6 km of tertiary pipe. 3,396 plots are NOT connected and every one of them is named with a reason.

**184.6 km of corridor was thrown away** because it neither collects a connection nor conveys one - 10 % of what stage 2 handed over. W10 shipped 117.3 km of exactly that.

## The uncomfortable part first

**The drainability test is not run.** `CAN_DRAIN` asks whether a plot's outlet sits above the sewer invert where it joins, and there is no designed invert at stage 4. Running it against a seeded depth is what rejected 5,715 plots for nothing last time. What is published instead is a bound that needs no invert: **DRAIN_SHALLOW = 1 on 48,177 of 53,018 connections (90.9 %)**, meaning the plot can drain into a sewer laid at the MINIMUM legal cover. A 1 is a guarantee. A 0 is not a rejection - it says the sewer must be deeper there, which is stage 6's decision.

**And the biggest number in this stage is a choice, not a calculation.** Table 12 (G203-p30) permits 100 m between chambers at DN200-315. NAMA build at a median of 29.77 m and have never built one longer than 71.38 m - not one of their 3,265 pipes exceeds Table 12. Since G203-p29 4.4 hands regular spacing to "maintenance equipment", their network is the evidence of what that equipment reaches, and this design is laid at 30 m. **On the same corridors before any pruning that is 65,940 chambers against 23,460 at Table 12's ceiling - a factor of 2.8.** The whole sweep is below. Nothing else in this stage moves a quantity by that much, and it is the one number an engineer should overrule if NWS say their jetting equipment reaches further than their 2006 contractor's did.

## What G203 asks for, and what was done about it

G203-p29 4.4, verbatim: _"Manholes shall be provided at the following locations: Change in pipe gradient; Change in pipe diameter; Junction of two or more pipes; At regular spacing on straight pipeline based on maintenance equipment"_, continuing on p30 with _"End of each lateral sewer"_. Five triggers. Three are placed:

| TRIGGER  | N      | PER_KM | SOURCE                                                                                                                                                                                                                                                                                       |
|----------|--------|--------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| spacing  | 43,520 | 29.17  | G203-p29 4.4 'At regular spacing on straight pipeline based on maintenance equipment', G203-p30 Table 12 the ceiling                                                                                                                                                                         |
| bend     | 3,900  | 2.61   | PROJECT, calibrated: a pipe is laid straight between chambers (98.1 % of NAMA's built pipes are a straight 2-point line). G203 lists NO bend trigger                                                                                                                                         |
| chamber  | 3,795  | 2.54   | a stage-2 graph node that is neither a junction nor a head - two corridors meeting end to end                                                                                                                                                                                                |
| junction | 2,582  | 1.73   | G203-p29 4.4 'Junction of two or more pipes'                                                                                                                                                                                                                                                 |
| head     | 2,005  | 1.34   | G203-p30 'End of each lateral sewer'                                                                                                                                                                                                                                                         |
| fanout   | 957    | 0.64   | PROJECT (criteria.FANOUT_OFFSET_M, user rule 2026-08-18; philosophy sec 4's 10 m clearance): a run leaving a chamber that already has an outlet starts 10 m away. It is what keeps 'exactly one pipe leaves a junction' true where stage 2 hands over more than one corridor out of one node |
| outfall  | 176    | 0.12   | G203-p29 4.4 (terminal); the only chamber with no DS_NODE                                                                                                                                                                                                                                    |


Two are not placed because they cannot fall between two chambers. That is an argument, and it is written out so it can be attacked:

| TRIGGER                 | SOURCE                                     | STATUS                                                                               | ARGUMENT                                                                                                                                                                                                                                                                                                                                      |
|-------------------------|--------------------------------------------|--------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| change in pipe diameter | G203-p29 4.4                               | SATISFIED BY CONSTRUCTION                                                            | flow only enters at a chamber (G203-p19 3.6 'Connection to the Main Sewer will be done at a manhole ... There must be no penetrating connection'), and a reach here IS chamber to chamber, so a diameter cannot change between two chambers. Re-checked when the diameters exist.                                                             |
| change in pipe gradient | G203-p29 4.4                               | SATISFIED BY CONSTRUCTION at 30 m spacing, to the limit of what the terrain resolves | a DESIGNED gradient change lands on a chamber by definition (G203-p29: 'Uniform slopes must be maintained between successive manholes'). A GROUND grade break below 67.4 mm/m cannot be seen at all: sigma_dz = 0.4769 m over a 30 m window gives a 3-sigma detection floor of that size. Breaks coarser than it are longer than the spacing. |
| drop / backdrop chamber | G203-p30 (>0.60 m backdrop, >2.0 m vortex) | CANNOT RUN AT THIS STAGE                                                             | a drop is a difference of INVERTS and there are no inverts until stage 6. Reported as a blank, not as a zero.                                                                                                                                                                                                                                 |


**Note what G203 does NOT list: a change of direction.** A bend chamber is not a guideline requirement. It is here because a pipe is laid straight between chambers, and that is measured, not assumed: 98.1 % of NAMA's built pipes are a straight two-point line, the median departure from the chord is 0.000 m and the p99 is 0.020 m. So the split rule is a CHORD OFFSET of 0.5 m, not an invented angle.

## Spacing, against Table 12 and against the operator

| WHAT                                | median_m | mean_m | p90_m | max_m  | per_km | over_tab12_pct |
|-------------------------------------|----------|--------|-------|--------|--------|----------------|
| this design                         | 27.18    | 26.29  | 29.43 | 30.00  | 38.16  | 0.00           |
| NAMA built                          | 29.77    | 29.23  | 38.25 | 71.38  | 34.23  | 0.00           |
| G203-p30 Tab 12 ceiling (DN200-315) | -        | -      | -     | 100.00 | -      | 0.00           |



| SPLIT_M | chambers  | per_km | max_spacing_m | over_tab12 | vs_built_per_km |
|---------|-----------|--------|---------------|------------|-----------------|
| 20.00   | 96,961.00 | 53.30  | 21.90         | 0.00       | 19.07           |
| 25.00   | 78,584.00 | 43.19  | 27.40         | 0.00       | 8.97            |
| 30.00   | 65,940.00 | 36.24  | 31.90         | 0.00       | 2.02            |
| 35.00   | 57,780.00 | 31.76  | 37.40         | 0.00       | -2.47           |
| 40.00   | 51,681.00 | 28.41  | 40.00         | 0.00       | -5.82           |
| 50.00   | 41,641.00 | 22.89  | 51.20         | 0.00       | -11.34          |
| 60.00   | 36,091.00 | 19.84  | 60.60         | 0.00       | -14.39          |
| 71.40   | 31,931.00 | 17.55  | 71.40         | 0.00       | -16.68          |
| 100.00  | 23,460.00 | 12.89  | 100.00        | 0.00       | -21.33          |


`over_tab12` is 0 on every row up to 100 m, which is the point: Table 12 is not the binding constraint anywhere in this design. The binding constraint is the operator's own practice, and it costs 38 chambers per km.

## Plot connections - ranking every carrier, and what that is worth

Same cost function, same chamber set, three candidate sets. Arm A is what the last iteration did.

| SEARCH                  | connected_n | connected_pct | load_m3d  | load_pct | tertiary_km | chambers_used | crosses_a_plot | crosses_a_dual | chamber_on_wadi | max_conn_per_chamber | load_pts_vs_A | km_vs_A | wayleaves_vs_A |
|-------------------------|-------------|---------------|-----------|----------|-------------|---------------|----------------|----------------|-----------------|----------------------|---------------|---------|----------------|
| A nearest chamber only  | 53,019      | 93.98         | 70,406.60 | 94.25    | 489.90      | 33,670        | 2,889          | 6              | 1,460           | 8                    | 0.00          | 0.00    | 0              |
| B nearest corridor only | 53,015      | 93.97         | 70,237.50 | 94.02    | 506.40      | 33,567        | 1,622          | 6              | 935             | 7                    | -0.23         | 16.50   | -1,267         |
| C every carrier ranked  | 53,019      | 93.98         | 70,406.60 | 94.25    | 508.60      | 33,678        | 1,321          | 2              | 779             | 6                    | 0.00          | 18.70   | -1,568         |


**Ranking every carrier is worth +0.00 percentage points of load. That is the honest number and it is nearly nothing.** With a chamber every 30 m the nearest one is almost always inside 45 m already, so there is no load left for a better search to find. **The last iteration's 30 % rejection was its sparse carrier set, not its search**, and this stage cannot reproduce that gain because it does not have that problem.

**What ranking every carrier DOES buy is legality.** Same load, same plots, and: third-party plot crossings fall from 2,889 to 1,321 (-54 %), dual-carriageway crossings from 6 to 2, connections onto a chamber standing on wadi ground from 1,460 to 779 (-47 %), and the busiest chamber from 8 connections to 6. The price is +18.7 km of tertiary pipe, about 0.4 m per connection. **A wayleave over a neighbour's plot is not a length, it is a negotiation, and 1,568 fewer of them is what the extra pipe buys.**

_The three arms are measured BEFORE pruning, on one candidate set and one cost, so their counts differ from the published layer by the handful of connections the prune re-pointed._

The cost, in metres of equivalent pipe, is: the tertiary length, plus 45 m if the run crosses a third party's plot, plus 45 m if it crosses a dual carriageway, plus 45 m if the chamber stands on wadi ground, plus 15 m for every connection already on that chamber beyond the 3 G203-p17 calls usual. Constrained plots choose first.

| CONGEST_M | connected_n | load_m3d  | tertiary_km | chambers_used | crosses_a_plot | max_per_chamber | SHIPPED |
|-----------|-------------|-----------|-------------|---------------|----------------|-----------------|---------|
| 0.00      | 53,019.00   | 70,406.60 | 505.90      | 33,531.00     | 1,324.00       | 10.00           | 0.00    |
| 5.00      | 53,019.00   | 70,406.60 | 507.10      | 33,631.00     | 1,322.00       | 8.00            | 0.00    |
| 15.00     | 53,019.00   | 70,406.60 | 508.60      | 33,678.00     | 1,321.00       | 6.00            | 1.00    |
| 30.00     | 53,019.00   | 70,406.60 | 510.70      | 33,720.00     | 1,335.00       | 5.00            | 0.00    |
| 60.00     | 53,019.00   | 70,406.60 | 511.00      | 33,757.00     | 1,401.00       | 4.00            | 0.00    |



| connections_per_chamber | chambers | pct   |
|-------------------------|----------|-------|
| 1-1                     | 18,752   | 55.69 |
| 2-3                     | 14,703   | 43.66 |
| 4-6                     | 220      | 0.65  |
| 7-10                    | 0        | 0.00  |
| 11+                     | 0        | 0.00  |


## What is not connected, and why

3,396 load-bearing plots carrying 4,296 m3/d (5.8 %) have no chamber within 45 m of tertiary run.

- **1,796 of them (2,569 m3/d) sit within a chained rider + lateral** (2 x 45 m, the chain G203-p17 3.2 describes). They are reachable, but only by laying a lateral where the drawing has no corridor. That is a corridor question, not a connection one.
- **1,600 (1,727 m3/d) are beyond even that** and are not served by the central network at all. Philosophy 8a: every plot is SERVED, the question is by which system, and these belong in the options appraisal as satellite or on-site.


## Compliance, recomputed

| CHECK                                                          | SOURCE                                                                             | RESULT                                                                                                                                                                                  | PASS       |
|----------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|
| H12 chamber spacing within G203-p30 Table 12 (DN200-315 band)  | G203-p30 Tab 12                                                                    | 0 of 56,740 segments over 100 m                                                                                                                                                         | pass       |
| chamber spacing within the shipped split length                | PROJECT, calibrated to the built median                                            | 0 over 30 m                                                                                                                                                                             | pass       |
| H10 inlet angle at least 90 deg                                | G203-p30                                                                           | 2,881 of 54,553 measurable inlets below 90 deg; worst 0.0 deg                                                                                                                           | FAIL       |
| no two chambers inside the 3 m minimum clearance               | criteria.MH_SNAP_M (PROJECT - no minimum chamber spacing exists in G201/G202/G203) | 5 pair(s), of which 5 are BOTH stage-2 graph nodes - a corridor-snapping artefact this stage inherits and must not silently merge, because merging changes stage 2's published topology | FAIL       |
| H1 no chamber on wadi ground                                   | G203-p30 4.4.1 i.a; the CLASS test is a project assumption                         | 3,366 chambers on hazard class 4/5/6 of the 50-yr grid                                                                                                                                  | FAIL       |
| tertiary run within 45 m                                       | G203-p22 Tab 6 lateral row + p17 3.2, taken on both                                | 0 of 53,018 over 45 m                                                                                                                                                                   | pass       |
| H15 every component ends at exactly one outfall                | project rule / philosophy H15                                                      | OK - 195 components, exactly one outfall each                                                                                                                                           | pass       |
| H16 topology written down (US_NODE / DS_NODE on every segment) | project rule / philosophy H16                                                      | 56,740 segments, 0 inferred from geometry                                                                                                                                               | pass       |
| zero silent drops - every load-bearing plot accounted for      | project doctrine                                                                   | 53,018 connected + 3,396 named = 56,414 of 56,414                                                                                                                                       | pass       |
| CAN_DRAIN - does the plot outlet sit above the sewer invert    | contract.CONNECTIONS.CAN_DRAIN                                                     | CANNOT RUN - no designed invert exists at stage 4. NOT run against a seeded depth. DRAIN_SHALLOW published instead                                                                      | cannot run |


## What this stage cannot fill

29 of 91 contract fields are filled. The rest are named, with what they wait on - an unfilled field that nobody named is how a stage silently does nothing.

| WAITS_ON                                      | FIELDS |
|-----------------------------------------------|--------|
| s6 levels                                     | 18     |
| s6 sizing                                     | 12     |
| a later stage                                 | 10     |
| s5 flows                                      | 7      |
| s8 packages                                   | 6      |
| s3 hierarchy - NOT BUILT in W11b              | 2      |
| detail design                                 | 1      |
| carried on the reach at sizing                | 1      |
| a crossings register, not built in this stage | 1      |
| detail design (contractor's number)           | 1      |
| s6 (existing-network tie-in)                  | 1      |
| s6 levels - REFUSED here rather than seeded   | 1      |
| s8 packages (needs the tier and package)      | 1      |


**`TIER` is the one that matters.** There is no hierarchy stage in W11b, so no reach here knows whether it is a lateral, a sub main or a trunk main. Table 12's spacing band, the minimum diameter (G203-p22 Tab 6) and the permitted materials all key off it. This design is laid at the DN200-315 band, which is the tightest, so nothing here becomes illegal when the tiers arrive - but the larger pipes are carrying more chambers than they need.


## Pruning

| WHAT                                                            | arcs      | km       |
|-----------------------------------------------------------------|-----------|----------|
| corridors handed over by stage 2                                | 12,815.00 | 1,819.30 |
|   less the 10 m fan-out at a chamber that already has an outlet | 3,135.00  | -31.30   |
|   less arcs that neither collect nor convey, WHOLLY pruned      | 1,221.00  | -184.60  |
|   less the upper part of arcs pruned only in PART               | -         | -111.40  |
| = published                                                     | 11,594.00 | 1,491.90 |
|    memo: pruned fingers under 60 m (philosophy sec 4)           | 122.00    | 4.30     |
|    memo: pruned arcs carrying a chamber on wadi ground          | 116.00    | -        |


The rule is 'a chosen chamber keeps its whole path to the outfall; everything else goes'. It uses no length threshold, so it is not the philosophy's 60 m finger rule - it is stronger, and the finger count is reported inside it. Note that an arc can be pruned in PART: a corridor whose upper end serves nothing but whose lower end conveys keeps only the lower end, which is why the two 'less' rows do not add up to the arc count.
2 connections were re-pointed onto a surviving chamber because the one they had chosen was a TERMINAL with nothing kept above it. Nothing was dropped in silence - `verify()` reconciles the load to the milligram against the source plot file.


## Every number, with where it came from

| ITEM                                               | VALUE             | UNIT | SOURCE                                                                       |
|----------------------------------------------------|-------------------|------|------------------------------------------------------------------------------|
| chambers                                           | 56,935            | -    | this stage                                                                   |
| chambers per km                                    | 38.16             | -    | built network 34.23 (asbuilt, measured)                                      |
| network published                                  | 1,491.90          | km   | this stage, after pruning                                                    |
| corridors in                                       | 1,819.30          | km   | stage 2                                                                      |
| pruned - neither collects nor conveys              | 184.60            | km   | this stage                                                                   |
| segments                                           | 56,740            | -    | chamber to chamber                                                           |
| spacing median                                     | 27.18             | m    | G203-p30 Tab 12 allows 100 m at DN200-315                                    |
| spacing max                                        | 30.00             | m    | G203-p30 Tab 12                                                              |
| segments over Table 12                             | 0                 | -    | G203-p30 Tab 12                                                              |
| junction chambers                                  | 2,582             | -    | G203-p29 4.4 'Junction of two or more pipes'                                 |
| head chambers                                      | 2,005             | -    | G203-p30 'End of each lateral sewer'                                         |
| bend chambers                                      | 3,900             | -    | PROJECT, calibrated to built straightness                                    |
| spacing chambers                                   | 43,520            | -    | G203-p29 4.4 regular spacing                                                 |
| outfalls                                           | 195               | -    | philosophy H15                                                               |
| inlets below 90 deg                                | 2,881             | -    | G203-p30                                                                     |
| chambers on wadi ground                            | 3,366             | -    | G203-p30 4.4.1 i.a; class test is a project assumption                       |
| pipe with BOTH chambers on wadi ground             | 75.92             | km   | G203-p30 4.4.1 i.a - running ALONG a wadi, not crossing it (H1)              |
| components with no path to the Main Pipe           | 19                | -    | H15: a piece that drains nowhere is never legal. Stage 2's `island` arcs     |
| chambers in those components                       | 507               | -    | H15                                                                          |
| plots connected                                    | 53,018            | -    | this stage                                                                   |
| plots not connected                                | 3,396             | -    | each with a WHY                                                              |
| load connected                                     | 70,405.50         | m3/d | of 74,701.2 = 94.25 %                                                        |
| load connected                                     | 94.25             | %    | of the load-bearing plots                                                    |
| properties connected                               | 93,320.00         | -    | of 98,681                                                                    |
| tertiary pipe                                      | 508.60            | km   | HCC to chamber, each within 45 m                                             |
| tertiary run median                                | 7.20              | m    | G203-p22 Tab 6 lateral row caps it at 45 m                                   |
| connections crossing a third-party plot            | 1,321             | -    | needs a wayleave                                                             |
| connections crossing a dual carriageway            | 2                 | -    | legal as a crossing (H1a), priced as a structure                             |
| load not connected                                 | 4,295.70          | m3/d | 5.75 % - every plot named                                                    |
|   of it, within a chained rider+lateral (2 x 45 m) | 2,569.00          | m3/d | G203-p17 3.2 chain; needs a corridor the drawing does not have               |
|   of it, beyond even that                          | 1,726.70          | m3/d | philosophy 8a: served by ANOTHER system, not by this network                 |
| chambers with more than 3 connections              | 220               | -    | G203-p17 3.2 'usually up to 3'                                               |
| DRAIN_SHALLOW                                      | 48,177            | -    | connections that drain into a sewer at MINIMUM cover; a bound, NOT CAN_DRAIN |
| CAN_DRAIN                                          | cannot run        | -    | no designed invert exists at stage 4; NOT run against a seed                 |
| uphill share of the published length               | 26.42             | %    | stage 2 published 23.15 % over ALL its arcs; this is over the pruned network |
| tau                                                | 1.00              | Pa   | ASSUMED (GAP-9), unused by this stage                                        |
| split length                                       | 30.00             | m    | MEASURED from the built median                                               |
| sigma_dz                                           | 0.48              | m    | terrain manifest, differential                                               |
| grade-break detection floor                        | 67.40             | mm/m | derived; below it a ground grade break is DEM noise                          |
| runtime                                            | 45.90             | s    |                                                                              |
| stage version                                      | W11b-chambers-1.0 | -    |                                                                              |


## Assumptions

| ITEM                | VALUE     | UNIT         | BASIS                                                                                                                                                                                                                                                                                            |
|---------------------|-----------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| MH_SPLIT_M          | 30.00     | m            | MEASURED. The built network's median chamber spacing (29.77 m) rounded to 10 m. G203-p29 4.4 hands regular spacing to 'maintenance equipment' and the operator's own 3,265 built pipes are the record of what that reaches - none of them exceeds Table 12's 100 m and their longest is 71.38 m. |
| STRAIGHT_TOL_M      | 0.50      | m            | PROJECT, CALIBRATED. 98.1 % of built pipes are a straight 2-point line; the polyline departs from its chord by a median 0.000 m and p99 0.020 m, and 99.36 % are inside 0.5 m. Replaces an invented bend angle with the physical rule a straight pipe obeys.                                     |
| TERT_MAX_M          | 45.00     | m            | G203-p22 Table 6 prints 'Maximum Length 45 m' on the LATERAL SEWER ROW ONLY (read from the PDF 2026-09-03). G203-p17 3.2 writes 'Rider Sewers and Lateral Sewers (maximum Length 45 m)', attaching it to both. Conservative reading taken: 45 m on the whole tertiary run. PROJECT.              |
| HCC_OFFSET_M        | 2.50      | m            | G203-p17 3.2, verbatim.                                                                                                                                                                                                                                                                          |
| PEN_CROSS_PLOT_M    | 45.00     | m            | PROJECT. One full legal tertiary run, so a wayleave is always worth avoiding and never worth dropping a plot for.                                                                                                                                                                                |
| PEN_CROSS_DUAL_M    | 45.00     | m            | PROJECT. Same price. Crossing is legal (philosophy H1a); running ALONG is not (project rule 7).                                                                                                                                                                                                  |
| PEN_WADI_M          | 45.00     | m            | PROJECT. A chamber on wadi ground is prohibited (G203-p30 4.4.1 i.a). A penalty and not a veto, because a veto drops load silently.                                                                                                                                                              |
| CONGEST_M           | 15.00     | m/connection | PROJECT. Charged beyond the free 3 of G203-p17 3.2 ('usually up to 3'). A third of a legal run. Swept - see congestion_sweep.                                                                                                                                                                    |
| CAND_TOPK           | 8         | -            | PROJECT. How many candidates per plot carry the crossing tests. The cheap ones are always in, because the ranking is by bare length first.                                                                                                                                                       |
| DUAL_BAND_M         | 6.00      | m            | PROJECT, matching stage 1's own band half-width, whose `dual_band` table publishes the exposure at eight widths.                                                                                                                                                                                 |
| FINGER_M            | 60.00     | m            | PROJECT (philosophy sec 4, ours on cost grounds). REPORTED ONLY - the prune rule is 'neither collects nor conveys' and needs no length threshold.                                                                                                                                                |
| GRADE_BREAK_FLOOR   | 67.40     | mm/m         | DERIVED. 3 * sqrt(2) * sigma_dz / window, sigma_dz = 0.4769 m (terrain manifest, the DIFFERENTIAL error) over the 30 m spacing. Below this a ground grade break is indistinguishable from DEM noise, which is why the gradient trigger is not fired from the terrain.                            |
| HAZARD_WADI_CLASSES | (4, 5, 6) | -            | PROJECT ASSUMPTION. AR&R flood-hazard classes 4/5/6 of the 50-yr grid stand in for G203's 'areas subject to washout', which is a SCOUR criterion. No-data is read as DRY HIGH GROUND (engineer, 2026-09-03).                                                                                     |
| MH_ROUND_STEP       | 10.00     | m            | NOT APPLIED. A straight piece is divided into EQUAL parts instead; rounding leaves a stub chamber a few metres from its neighbour. Declared departure.                                                                                                                                           |
| tau                 | 1.00      | Pa           | ASSUMED (GAP-9). Not used by this stage - no gradient is set here - and carried on the outputs so the exposure travels.                                                                                                                                                                          |


## Notes

- 1 arc(s) excluded: a closed ring whose two ends are the same node (132 m). It cannot carry a direction, so it cannot carry a chamber sequence.

- 4 corridor(s), 13 m in total, leave a chamber that already has an outlet and are shorter than twice the 3 m minimum chamber clearance, so no run can start on them. They are absorbed and appear in the `pruned` layer.

- 3 plots had chosen a chamber that was a TERMINAL with nothing kept above it, so no segment mentioned it and the prune removed it. 2 were re-ranked onto a surviving chamber and 1 moved to the unserved schedule. None was dropped in silence.

- 19 components (507 chambers, 13.4 km) have NO outfall on the client's Main Pipe. They are stage 2's `island` corridors, which it published with 'no path to the Main Pipe; direction provisional'. H15 allows several components - a satellite works is legal - but never a piece that drains nowhere. Each needs a connection or its own works: an engineer's decision, and it is NOT resolved here.
