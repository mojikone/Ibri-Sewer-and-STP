# W9 - electricity accounts as land-use layer

Source `ELE_accounts.shp` joined to `Towns.shp`. **33,970 accounts**, EPSG:32640.


## Guideline category counts

| GUD_CAT | Accounts |
|---|---|
| domestic | 16,244 |
| non_domestic | 9,392 |
| domestic_add | 6,344 |
| government | 967 |
| agricultural | 523 |
| CRT_review | 499 |
| industrial | 1 |

## REVIEW queue (tariff cannot classify these)

| Flag | Points |
|---|---|
| no_plot | 9,081 |
| high_plot | 1,030 |
| CRT | 499 |
| industrial | 1 |

## Occupancy rate by settlement (Pop_2024 / domestic properties)

| Settlement | Domestic properties | Pop 2024 | OR |
|---|---|---|---|
| IBRI | 10,802 | 67,106 | 6.21 |
| AL ARAQI | 2,425 | 10,696 | 4.41 |
| AD DARIZ | 2,380 | 11,850 | 4.98 |
| AL AYNAYN | 856 | 4,554 | 5.32 |
| AT TAYYIB | 797 | 3,348 | 4.2 |
| AL WAHRAH | 718 | 3,351 | 4.67 |
| AD DIBAYSHI | 670 | 2,411 | 3.6 |
| AL JIBAYYAH | 526 | 2,686 | 5.11 |
| SAYH AL MASARRAT | 434 | 466 | 1.07 |
| BAT | 420 | 2,557 | 6.09 |
| HIJAR | 330 | 1,033 | 3.13 |
| TANAM | 322 | 2,116 | 6.57 |
| AL JAHLI | 320 | 415 | 1.3 |
| SUWAYDA AL MA | 297 | 1,559 | 5.25 |
| AL QURAYN | 137 | 549 | 4.01 |
| AL GHUBAYRAH | 126 | 631 | 5.01 |
| AL AKHEEDAR | 121 | 198 | 1.64 |
| AL MAKHTIBYAH | 63 | 122 | 1.94 |
| AL QALI | 54 | 191 | 3.54 |
| SATWAH | 26 | 263 | 10.12 |
| SHALASHIL | 24 | 130 | 5.42 |
| USAYBUQ | 17 | 91 | 5.35 |
| ASH SHIAB | 12 | 47 | 3.92 |
| WADI AL MANKAS | 8 | 52 | 6.5 |
| MIAYRID | 4 | 34 | 8.5 |
| **TOTAL** | **21,889** | **116,456** | **5.32** |

## Coverage consistency check

- Settlements hold 116,456 of the wilayat's 183,564 people = **63.4 %**.
- At OR 5.32 the whole wilayat implies 34,504 domestic properties; the file holds 22,588 = **65.5 %**.
- The two coverages agree to 2.0 pp, so OR 5.32 is internally consistent rather than a coverage artefact.
