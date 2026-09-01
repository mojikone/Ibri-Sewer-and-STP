# W9 — GHS population grid as a check on our population data

**Internal only. Nothing here goes into the report**, other than the map that
shows where population lies. The purpose is to judge how far the GHS grid can
be trusted in future work, and to see what it says about the settlements our
own data flags as odd.

Source: `Hydraulic/Raster/GHS POP 2025 IBRI.tif` — GHS-POP, JRC, 2025 epoch,
100 m grid, EPSG:32640, CC BY 4.0. A 100 m cell is one hectare, so the value
is persons per hectare. Zonal sums computed against `SHP/Towns/Towns.shp` and
the approved boundary. All 25 settlement polygons lie wholly inside the
boundary, so the sums below subtract cleanly.

## Headline

| | Value |
|---|---|
| GHS inside the study boundary, 2025 | **127,210** |
| GHS inside the 25 named settlements | **122,817** |
| GHS inside the boundary, outside every settlement | **4,393  (3.5 %)** |
| NCSI 2025, the same 25 settlements | 119,244 |
| GHS ÷ NCSI, all settlements together | **1.03** |
| Densest cell inside the boundary | 237 persons per hectare |

**The totals agree and the distribution does not.** That is the whole result.
GHS descends from the same census we already use, so a 3 % agreement on the
total tells us nothing new. Per settlement the ratio runs from **0.43 to 2.70**,
and that is where the information is.

## Per settlement

Ordered by counted domestic properties. OR (NCSI) is the occupancy rate the
report adopts; OR (GHS) is what it would be if GHS were right instead.

| Settlement | Props | NCSI 2024 | OR (NCSI) | GHS 2025 | GHS/NCSI | OR (GHS) |
|---|---|---|---|---|---|---|
| Ibri | 10,802 | 67,106 | 6.21 | 73,428 | 1.07 | 6.80 |
| Al Araqi | 2,425 | 10,696 | 4.41 | 16,190 | 1.48 | 6.68 |
| Ad Dariz | 2,380 | 11,850 | 4.98 | 7,986 | 0.66 | 3.36 |
| Al Aynayn | 856 | 4,554 | 5.32 | 5,346 | 1.15 | 6.25 |
| At Tayyib | 797 | 3,348 | 4.20 | 4,549 | 1.33 | 5.71 |
| Al Wahrah | 718 | 3,351 | 4.67 | 1,910 | 0.56 | 2.66 |
| Ad Dibayshi | 670 | 2,411 | 3.60 | 2,227 | 0.90 | 3.32 |
| Al Jibayyah | 526 | 2,686 | 5.11 | 2,287 | 0.83 | 4.35 |
| **Sayh Al Masarrat** | 434 | 466 | **1.07** | 1,205 | **2.53** | 2.78 |
| Bat | 420 | 2,557 | 6.09 | 1,330 | 0.51 | 3.17 |
| Hijar | 330 | 1,033 | 3.13 | 866 | 0.82 | 2.62 |
| Tanam | 322 | 2,116 | 6.57 | 923 | 0.43 | 2.87 |
| **Al Jahli** | 320 | 415 | **1.30** | 794 | **1.87** | 2.48 |
| Suwayda Al Ma | 297 | 1,559 | 5.25 | 1,143 | 0.72 | 3.85 |
| Al Qurayn | 137 | 549 | 4.01 | 548 | 0.97 | 4.00 |
| Al Ghubayrah | 126 | 631 | 5.01 | 340 | 0.53 | 2.70 |
| **Al Akheedar** | 121 | 198 | **1.64** | 520 | **2.56** | 4.30 |
| Al Makhtibyah | 63 | 122 | 1.94 | 179 | 1.43 | 2.84 |
| **Al Qali** | 54 | 191 | 3.54 | 526 | **2.70** | 9.74 |
| **Satwah** | 26 | 263 | **10.12** | 233 | 0.87 | 8.95 |
| Shalashil | 24 | 130 | 5.42 | 128 | 0.96 | 5.35 |
| Usaybuq | 17 | 91 | 5.35 | 58 | 0.62 | 3.40 |
| Ash Shiab | 12 | 47 | 3.92 | 32 | 0.67 | 2.67 |
| Wadi Al Mankas | 8 | 52 | 6.50 | 49 | 0.92 | 6.11 |
| Miayrid | 4 | 34 | 8.50 | 22 | 0.63 | 5.52 |
| **TOTAL** | **21,889** | **116,456** | **5.32** | **122,817** | **1.03** | **5.61** |

Ratio column compares GHS 2025 against NCSI 2025, same epoch. The OR columns
use NCSI 2024, which is the year the report adopts.

## What it tells us

**1. Three of the four flagged settlements are explained, and the diagnosis is
NCSI, not our property count.** Sayh Al Masarrat, Al Jahli and Al Akheedar all
return occupancy near or below 1.6, which is not physically sensible. GHS finds
1.9 to 2.6 times more people in the same polygons than NCSI attributes to them.
Recomputed on GHS their occupancy becomes 2.78, 2.48 and 4.30 — still low, but
in the range of a real place. The likely cause is that NCSI's settlement
attribution is short there, not that the electricity accounts are wrong.

**2. Satwah is the opposite case and needs a different fix.** GHS agrees with
NCSI (ratio 0.87), so its occupancy of 10.12 survives at 8.95. The problem
there is the property side — 26 domestic accounts for roughly 250 people. That
points at accounts unmatched to a plot or missing from the extract, not at a
boundary.

**3. GHS adds a fifth settlement to the review list: Al Qali.** Ratio 2.70,
and its occupancy would jump from 3.54 to 9.74. It was not flagged by our own
data and should be looked at with the other four.

**4. GHS reads low on mid-size settlements, systematically.** Tanam 0.43, Bat
0.51, Al Ghubayrah 0.53, Al Wahrah 0.56 — four settlements where GHS finds
about half the population. Low-rise scattered development is the likely cause:
the model weights census counts by built-up surface, and it under-detects that
kind of fabric. **So a low GHS value is not evidence of few people.** The grid
is trustworthy upward and unreliable downward.

**5. About 4,400 people live inside the study area and outside every named
settlement** — 3.5 % of the in-boundary population, spread across the 224.6 km²
the settlement polygons do not cover. Small, but they still need collecting,
and they are invisible in a settlement-based population model.

## Reliability, for future work

| Where | Verdict |
|---|---|
| Ibri town, Al Aynayn, Ibri as a whole | Within about 10 %. Usable as a sense check |
| Settlements above roughly 2,000 people | Ratio 0.43 to 1.48. Directionally useful, not quantitative |
| Settlements below roughly 1,000 people | Ratio 0.43 to 2.70. Not usable for any number |
| Any load, flow or sizing calculation | **Never.** It is modelled, and using it would breach the project's own rule that no metric is invented |
| Spotting a boundary or attribution error | **Its best use.** It found three of our four anomalies and one we had missed |
| Finding population outside the settlement polygons | Good, and nothing else we hold does this |

## What to do with it

1. Add **Al Qali** to the settlement boundary review, with the existing four.
2. Treat **Satwah** as a property-count problem, not a boundary problem.
3. When the corrected plot layer and the survey land, rerun this comparison.
   If the three low-occupancy settlements resolve upward, that confirms the
   NCSI attribution reading; if they do not, our account matching is at fault.
4. Do **not** revise the adopted occupancy rate of 5.32 on this evidence. The
   GHS-implied 5.61 is a modelled figure, and the report's rate has to trace to
   NCSI (G201-p58).
