# Note for the Concept Design Report — saturation population and sewage load per plot

*W14, 10 September 2026, class v7. This note is the bridge between the working files and the report: what was
done, in what order, with which numbers, and where each piece lands in the report. Written for the
report author; the client-facing wording comes in the report itself.*

Live figures come from three scripts run in order: `W14/py/plots_meters_load.py` (QGIS),
`W14/py/plot_class_v2_apply.py`, `W14/py/growth_by_settlement.py`; the settlement polygons from
`W14/py/settlements_partition.py`; the NDVI from `W14/py/ndvi_plots.py`. Decisions and their dates are in
`W14/analysis/REFINEMENTS_PENDING.md`; the identified projects in `W14/analysis/IDENTIFIED_PROJECTS.md`.

---

## 1. What the method answers

Three questions the TOR asks and the inception report could only estimate:

1. How many people and how much sewage are there **today**, and where exactly (per plot)?
2. When does each settlement **fill up**, and what is the town's **saturation** population and flow?
3. How does the load grow **year by year** so the network, the pumping and the treatment works can be staged?

The answer rests on one principle: **count, do not assume.** Every property is an electricity meter;
every plot's use is read from the meters on it; every empty plot's future is read from the built plots
around it. The inception workbook supplies only the growth rate and the split between settlements.

---

## 2. The electricity meters: from tariff to NAMA category

**Data.** 33,971 electricity accounts (2024), one point each, shifted onto the cadastre by the engineer.
Each carries a tariff name, nothing else: no consumption, no address, no land use.

**Step 2.1 — tariff to category.** The thirteen tariffs fold into the guideline's categories
(PAM-GUD-201 §7.3):

| Tariff (as received) | Category | Count |
|---|---|---|
| Primary Account Tariff; Primary Account Tariff (with National Subsidy); Additional Account Tariff | **Domestic** — one property each | 22,589 |
| Commercial; Fisheries; Tourism | **Non-domestic** | 9,392 |
| Government; MOD | **Governmental** | 967 |
| Agricultural | **Agricultural** — an irrigation pump, no sewage | 523 |
| Industrial | **Special** (identified project) | 1 |
| CRT Seasonal; CRT Time of Use; CRT Fixed Rate | **Large consumer** — a consumption class, not a use; resolved in 2.2 | 499 |

**Step 2.2 — the 499 large-consumer (CRT) accounts.** The Cost Reflective Tariff says only that the
account uses over 150 MWh a year. A mall, a hospital, a mosque and a factory all land in it. Each account
was placed by public data: OpenStreetMap (1,001 named features around them), Nominatim reverse geocoding,
Google satellite by eye for the fifteen largest clusters, and the identified-projects search (press,
Madayn, OSM footprints). Result (`W14/analysis/CRT_accounts_identified.csv`, with the evidence and a
confidence per account):

| Use found | Accounts | NAMA category |
|---|---|---|
| Commercial (Bawadi Mall, the Al Murtafa souq, the Araqi strip, hypermarkets, banks, fuel) | 205 | non-domestic |
| Government, education, health, religious (Police HQ, UTAS, Ibri Hospital, schools, mosques) | 135 | governmental |
| Industrial (the Tanam estate) | 16 | special |
| Agricultural (Aynayn farm pumps) | 28 | agricultural, no load |
| Telecom / utility | 6 | non-domestic |
| Unresolved (no public feature within 80 m) | 110 | non-domestic, flagged |

**Step 2.3 — identified projects and special consumption.** The guideline keeps economic zones and
high-water users outside the population ratios (G1-p59 §7.3.1, G1-p61 §7.3.4). Public data found two
industrial estates inside the boundary that the tariff had hidden under "Commercial": **Al Tayyeb**
(94 ha, 202 industrial plots, 1,035 shop meters) and **Tanam** (61 ha, 105 plots, 409 meters). They are
treated as special: an assumed workforce of 4,500 and 1,800, spread over their industrial plots by area,
at the dry-industry rate. The army camp (296 ha, no meter), the planned Ibri View resort (2 km² at
As Sulayf, not yet in the cadastre) and the two tanker sources outside the boundary (Madayn Ibri
Industrial City, the IPP construction camp) are recorded for the report and carry no network load.

**Step 2.4 — meter to plot.** 30,931 meters fall inside a plot; 2,914 sit on a road or a gap and were
moved to the nearest plot within 15 m; 126 stay free. Every plot now carries its meter counts by tariff
and by category (`ELE_meters_on_plots.shp`, `PLOTS_load.shp` fields `N_*` and `G_*`).

---

## 3. The land-use layer: every plot's main use

The MoH file (77,265 plots, 7 September 2026) carries a class, but on the plots with meters it is wrong
one time in seven, has no government class, and calls whole districts "Residential" under codes that mean
"unclassified". The use was therefore **derived**, plot by plot, in this order:

1. **Estate.** Inside the Al Tayyeb or Tanam footprint → Industrial.
2. **Heritage.** The 177 "Tourism" plots are the ruined old quarter of Ibri by the fort → Heritage, no load.
3. **Farm by meter.** Any agricultural meter on the plot → Agricultural. Never overridden.
4. **Farm by satellite.** One cloud-free Sentinel-2 scene (9 September 2026; red and near-infrared, 10 m,
   from the public archive). The desert reads NDVI 0.08, palms 0.8, and palms are evergreen, so one scene
   is enough. A plot is a grove if it holds **≥ 1,000 m² of pixels at NDVI ≥ 0.30 with a mean ≥ 0.20**, or,
   for small plots, is at least 60 % green at a mean ≥ 0.40 — unless two thirds of its meters are shops or
   a majority are government. Calibrated on the 489 farm-meter plots and checked on a 64-plot contact sheet
   the engineer reviewed. (The RGB "excess green" test from the earlier imagery pass was tried and dropped:
   it put farms on bare ground.)
5. **Proportion of the meters.** More than two thirds home → **Residential**; two thirds or more
   government → **Government**; two thirds or more shop → **Commercial**; in between → **Residential-
   Commercial**. Large-consumer meters count with the use found in 2.2.
6. **No meter** → Unmetered (all the empty plots).

Result on the 15,400 built, metered plots: 12,464 homes, 1,321 shops, 614 mixed, 409 government,
3,399 farms (489 by meter, 2,910 by satellite), 467 industrial, 177 heritage. The first, naive reading
(one shop meter made a plot "mixed", a house on a farm made it "residential") is kept in `DERIVED1` for the
audit; `WHYC` records which rule fired.

---

## 4. Properties per plot and the occupancy rate

**Properties per home plot**, per settlement: dwelling meters ÷ plots, counted only on the **pure home
plots** (built, Residential by rule 5, fewer than 15 dwelling meters; blocks of flats and labour housing are
excluded). Ibri 1.33, Al Araqi 1.32, Ad Dariz 1.20. The first reading, which
counted every built plot with a dwelling, gave Ibri 1.60 and was rejected. A settlement under 1,000 people
takes 1.0 (the rule below).

**Occupancy rate**, per settlement: workbook population **2024** (the accounts' year, the report's base)
÷ **domestic** properties (primary, subsidised and additional tariffs; shop, government, farm and large-consumer
meters carry no people), **floored at 4.0 and capped at 6.12** (the highest value among the settlements
with 2,000 or more people, which is Bat's). Ibri 6.07, Bat 6.12, Ad Dariz 4.86, Al Araqi 4.34.
The floor lifts Ad Dibayshi (3.54), Hijar (2.93); no settlement is cut by the cap.

**The under-1,000 rule** (engineer, 10 September, class v7). A settlement with fewer than 1,000 people in the
2024 workbook takes **occupancy 4.0, one property per home plot and a home share of 0.9**, whatever its meters
return. Two reasons: it has too few meters to measure on (Miayrid 4, Wadi al Mankas 8, Ash Shiab 11 return
4.3 to 8.5 on a handful of accounts), and a village of that size does not attract second dwellings on a plot.
The 4.0 is At Tayyib's measured 4.02 at 3,300 people, the smallest settlement whose rate is trusted. The rule
applies to 13 settlements: Al Akheedar, Al Ghubayrah, Al Jahli, Al Makhtibyah, Al Qali, Al Qurayn, Ash Shiab, Miayrid, Satwah, Sayh al Masarrat, Shalashil, Usaybuq, Wadi al Mankas. Sayh al Masarrat and
Al Jahli are among them although their meters say 457 and 344 properties: the census counts 466 and
415 residents there, because the police headquarters housing and the college housing are not
census residents, and their raw rates of 1.02 and 1.21 would have been floored to 4.0 anyway.

**The report states it so.** Revision 1 carried one rate, 5.32, measured over the whole area. Revision 2 states
the rate per settlement with the floor, the cap and the under-1,000 rule (section 14.4, Table 15), and puts the
derived and the adopted values side by side for all three rates in Appendix A3 (Table 28), with the count of
empty plots and of those counted as future homes. The area-wide average on today's 22,559 domestic properties
is 5.31. The floor and the rule put **3,650 people above the census** in 14 settlements
(Sayh al Masarrat +1,362, Al Jahli +961, Hijar +375), and 217 below it
in the tiny ones brought down to 4.0; the net is 3,433 above the workbook's 116,453, giving
**119,886 people in 2024**. The meters flush whether the census counts their occupants or not, so the design
keeps them; the report says the difference and the reason in one footnote next to the occupancy table.

**The occupancy table** (report Table 15 and Table 28):

| Settlement | Domestic properties | Workbook 2024 | Occupancy derived | Occupancy adopted | Rule | People 2024 | Difference |
|---|---|---|---|---|---|---|---|
| Ibri | 11,052 | 67,106 | 6.07 | 6.07 | derived | 67,094 | -12 |
| Ad Dariz | 2,439 | 11,850 | 4.86 | 4.86 | derived | 11,852 | +2 |
| Al Araqi | 2,466 | 10,696 | 4.34 | 4.34 | derived | 10,698 | +2 |
| Al Aynayn | 889 | 4,554 | 5.12 | 5.12 | derived | 4,553 | -1 |
| Al Wahrah | 716 | 3,351 | 4.68 | 4.68 | derived | 3,351 | -0 |
| At Tayyib | 833 | 3,348 | 4.02 | 4.02 | derived | 3,349 | +1 |
| Al Jibayyah | 524 | 2,686 | 5.13 | 5.12 | derived | 2,684 | -2 |
| Bat | 418 | 2,557 | 6.12 | 6.12 | derived | 2,558 | +1 |
| Ad Dibayshi | 681 | 2,411 | 3.54 | 4.00 | floor 4.0 | 2,724 | +313 |
| Tanam | 403 | 2,116 | 5.25 | 5.25 | derived | 2,116 | -0 |
| Suwayda al Ma | 301 | 1,559 | 5.18 | 5.18 | derived | 1,559 | +0 |
| Hijar | 352 | 1,033 | 2.93 | 4.00 | floor 4.0 | 1,408 | +375 |
| Al Ghubayrah | 161 | 631 | 3.92 | 4.00 | under 1,000: 4.0 | 644 | +13 |
| Al Qurayn | 147 | 548 | 3.73 | 4.00 | under 1,000: 4.0 | 588 | +40 |
| Sayh al Masarrat | 457 | 466 | 1.02 | 4.00 | under 1,000: 4.0 | 1,828 | +1,362 |
| Al Jahli | 344 | 415 | 1.21 | 4.00 | under 1,000: 4.0 | 1,376 | +961 |
| Satwah | 27 | 263 | 9.73 | 4.00 | under 1,000: 4.0 | 108 | -155 |
| Al Akheedar | 120 | 198 | 1.65 | 4.00 | under 1,000: 4.0 | 480 | +282 |
| Al Qali | 56 | 191 | 3.41 | 4.00 | under 1,000: 4.0 | 224 | +33 |
| Shalashil | 38 | 130 | 3.42 | 4.00 | under 1,000: 4.0 | 152 | +22 |
| Al Makhtibyah | 91 | 122 | 1.34 | 4.00 | under 1,000: 4.0 | 364 | +242 |
| Usaybuq | 21 | 91 | 4.33 | 4.00 | under 1,000: 4.0 | 84 | -7 |
| Wadi al Mankas | 8 | 52 | 6.49 | 4.00 | under 1,000: 4.0 | 32 | -20 |
| Ash Shiab | 11 | 47 | 4.27 | 4.00 | under 1,000: 4.0 | 44 | -3 |
| Miayrid | 4 | 34 | 8.49 | 4.00 | under 1,000: 4.0 | 16 | -18 |

**The three rates side by side** (Appendix A3, Table 28):

| Settlement | Pop. 2024 | Empty plots | of which future homes | Occupancy derived | adopted | Properties per home plot derived | adopted | Home share derived | adopted | Capacity, people |
|---|---|---|---|---|---|---|---|---|---|---|
| Ibri | 67,094 | 14,203 | 10,469 | 6.07 | 6.07 | 1.33 | 1.33 | 0.87 | 0.87 | 73,301 |
| Ad Dariz | 11,852 | 4,888 | 3,219 | 4.86 | 4.86 | 1.20 | 1.20 | 0.90 | 0.90 | 16,852 |
| Al Araqi | 10,698 | 3,360 | 2,463 | 4.34 | 4.34 | 1.32 | 1.32 | 0.84 | 0.84 | 11,831 |
| Al Aynayn | 4,553 | 1,780 | 1,362 | 5.12 | 5.12 | 1.14 | 1.14 | 0.94 | 0.94 | 7,459 |
| Al Wahrah | 3,351 | 2,000 | 1,373 | 4.68 | 4.68 | 1.22 | 1.22 | 0.91 | 0.91 | 7,109 |
| At Tayyib | 3,349 | 10,012 | 8,640 | 4.02 | 4.02 | 1.09 | 1.09 | 0.92 | 0.92 | 34,672 |
| Al Jibayyah | 2,684 | 2,784 | 1,966 | 5.13 | 5.12 | 1.26 | 1.26 | 0.89 | 0.89 | 11,306 |
| Bat | 2,558 | 879 | 355 | 6.12 | 6.12 | 1.17 | 1.17 | 0.88 | 0.88 | 2,227 |
| Ad Dibayshi | 2,724 | 2,430 | 1,887 | 3.54 | 4.00 | 1.16 | 1.16 | 0.90 | 0.90 | 7,920 |
| Tanam | 2,116 | 2,045 | 1,556 | 5.25 | 5.25 | 1.24 | 1.24 | 0.67 | 0.67 | 6,779 |
| Suwayda al Ma | 1,559 | 1,593 | 937 | 5.18 | 5.18 | 1.60 | 1.60 | 0.82 | 0.82 | 6,369 |
| Hijar | 1,408 | 375 | 211 | 2.93 | 4.00 | 1.69 | 1.69 | 0.90 | 0.90 | 1,288 |
| Al Ghubayrah | 644 | 1,448 | 1,094 | 3.92 | 4.00 | 1.12 | 1.00 | 0.84 | 0.90 | 3,940 |
| Al Qurayn | 588 | 2,051 | 1,830 | 3.73 | 4.00 | 1.14 | 1.00 | 0.93 | 0.90 | 6,588 |
| Sayh al Masarrat | 1,828 | 1,745 | 1,384 | 1.02 | 4.00 | 2.52 | 1.00 | 0.92 | 0.90 | 4,984 |
| Al Jahli | 1,376 | 1,235 | 1,023 | 1.21 | 4.00 | 2.16 | 1.00 | 0.78 | 0.90 | 3,684 |
| Satwah | 108 | 181 | 79 | 9.73 | 4.00 | 1.23 | 1.00 | 0.87 | 0.90 | 284 |
| Al Akheedar | 480 | 120 | 45 | 1.65 | 4.00 | 2.12 | 1.00 | 0.53 | 0.90 | 160 |
| Al Qali | 224 | 220 | 157 | 3.41 | 4.00 | 2.20 | 1.00 | 0.92 | 0.90 | 564 |
| Shalashil | 152 | 3,686 | 3,250 | 3.42 | 4.00 | 1.11 | 1.00 | 0.91 | 0.90 | 11,700 |
| Al Makhtibyah | 364 | 1,523 | 1,192 | 1.34 | 4.00 | 1.15 | 1.00 | 0.90 | 0.90 | 4,292 |
| Usaybuq | 84 | 60 | 39 | 4.33 | 4.00 | 1.25 | 1.00 | 0.87 | 0.90 | 140 |
| Wadi al Mankas | 32 | 1,580 | 1,394 | 6.49 | 4.00 | 1.30 | 1.00 | 0.87 | 0.90 | 5,020 |
| Ash Shiab | 44 | 65 | 13 | 4.27 | 4.00 | 1.10 | 1.00 | 0.87 | 0.90 | 48 |
| Miayrid | 16 | 246 | 171 | 8.49 | 4.00 | 1.30 | 1.00 | 0.87 | 0.90 | 616 |

---

## 5. Saturation: capacity, growth, fill year

**Which empty plots become homes.** A future home plot must look like the built ones: **200 to 1,000 m²,
compact** (≥ 0.6 of its rotated bounding box), **not a strip** (aspect ≤ 3), not a grove, not industrial, not
heritage, not in an estate. 46,109 of the 60,509 empty plots qualify. Slivers under 200 m², odd shapes and
everything above 1,000 m² do not.

**Home share.** Not every home-shaped plot becomes a home: a district needs mosques, shops, offices. The share
is **measured** on each settlement's built, metered, home-shaped plots: pure homes ÷ all. Ibri 0.87; the
principal settlements lie between 0.67 and 0.94, Tanam 0.67 (shop-heavy). A settlement under
1,000 people takes 0.9.

**Capacity** per settlement = home-shaped empty plots × home share × properties per home plot × occupancy.
Total **229,133 people** on top of today's 119,886; Ibri 73,301, At Tayyib 34,672,
Ad Dariz 16,852, Al Araqi 11,831, Shalashil 11,700.

**The growth series and where it comes from** (report section 14.7, with a chart of the rate by year). The
population series of the Inception Report is used for its growth rates only. It is built in three parts: to
2040 the National Centre for Statistics and Information forecast for the Wilayat of Ibri, Omani and expatriate
population separately; 2041 to 2050 an extrapolation of that forecast, documented in the technical note on
population issued with the Inception Report; from 2051 a constant 2.40 per cent a year to 2100, the planning
horizon instructed by Nama Water Services, the rate rising from 2.19 per cent in 2051 to 2.40 by 2060. The
wilayat total (183,564 in 2024) is split between the settlements in fixed shares from the census, so every
settlement carries the same annual rate: 2.6 per cent a year over 2024–2030, 2.5 over the 2030s, 2.1 over the
2040s, 2.3 over the 2050s, 2.4 from 2060. The twenty-five settlements are 63.4 per cent of the wilayat; their
workbook total in 2100 is 691,264, which is not a target and not a saturation figure.

**Growth and overflow.** Each settlement grows at that rate, applied to its counted 2024 population, and its
growth fills its empty plots together and in proportion. When a settlement is full its further growth moves:
**Ibri in parallel to Al Araqi 70 %, Al Qurayn 20 %, Shalashil 10 %, then to Ad Dariz** when those are full,
then to the nearest settlement with room (local knowledge of where Ibri's growth is going); **At Tayyib to
Miayrid first**; every other settlement to its nearest neighbour with room. Every settlement receives, whatever
its size, so all 25 saturate. A receiver's own growth continues alongside what it receives; the report explains
the rule in words in 14.7, shows the main routes in Table 18, every route of fifty people or more in Appendix A5,
and the year each settlement would fill on its own growth alone in Appendix A6; the overflow map is M10.

**Fill years.** Ibri **2056**, Al Araqi 2057, Al Qurayn 2060, Shalashil 2061, Ad Dariz 2062; Al Akheedar
first in 2036; Al Wahrah, Al Jibayyah, Suwayda al Ma, Al Ghubayrah, Miayrid last in **2070, the saturation (ultimate) year**: every settlement full,
**349,019 people**. Ibri sends out 55,213 people in all; the largest single route is Ibri to
At Tayyib, 22,074. Without the overflow 7 settlements would not fill before 2100
(At Tayyib, Al Ghubayrah, Al Qurayn, Al Makhtibyah, Shalashil, Wadi al Mankas, Miayrid). Growth beyond saturation is not planned for in this concept.

**Five-year steps to saturation, every settlement** (report Table 17; a cell is empty once the settlement is
full; the last two columns are the exact year and the population then):

| Settlement | 2024 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 | 2055 | 2060 | 2065 | 2070 | Saturation year | Saturation population |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ibri | 67,094 | 68,702 | 78,086 | 88,257 | 100,049 | 110,330 | 122,514 | 137,175 |  |  |  | 2056 | 140,395 |
| Ad Dariz | 11,852 | 12,136 | 13,794 | 15,590 | 17,673 | 19,490 | 21,642 | 24,211 | 27,356 |  |  | 2062 | 28,704 |
| Al Araqi | 10,698 | 10,954 | 12,451 | 14,072 | 15,953 | 17,592 | 19,535 | 21,854 |  |  |  | 2057 | 22,529 |
| Al Aynayn | 4,553 | 4,662 | 5,299 | 5,989 | 6,789 | 7,487 | 8,314 | 9,301 | 12,012 |  |  | 2060 | 12,012 |
| Al Wahrah | 3,351 | 3,431 | 3,900 | 4,408 | 4,997 | 5,510 | 6,119 | 6,845 | 7,703 | 8,683 | 10,460 | 2070 | 10,460 |
| At Tayyib | 3,349 | 3,429 | 3,898 | 4,405 | 4,994 | 5,507 | 6,115 | 6,841 | 8,131 | 23,962 |  | 2068 | 38,021 |
| Ad Dibayshi | 2,724 | 2,789 | 3,170 | 3,583 | 4,062 | 4,479 | 4,974 | 5,564 | 6,262 |  |  | 2063 | 10,644 |
| Al Jibayyah | 2,684 | 2,748 | 3,124 | 3,531 | 4,002 | 4,414 | 4,901 | 5,483 | 6,170 | 6,947 | 13,990 | 2070 | 13,990 |
| Bat | 2,558 | 2,619 | 2,977 | 3,365 | 3,814 | 4,206 | 4,671 |  |  |  |  | 2052 | 4,785 |
| Tanam | 2,116 | 2,167 | 2,463 | 2,783 | 3,155 | 3,480 | 3,864 | 4,322 | 4,864 | 5,961 |  | 2069 | 8,895 |
| Sayh al Masarrat | 1,828 | 1,872 | 2,127 | 2,405 | 2,726 | 3,006 | 3,338 | 3,734 | 4,202 | 4,786 |  | 2069 | 6,812 |
| Suwayda al Ma | 1,559 | 1,596 | 1,814 | 2,051 | 2,325 | 2,564 | 2,847 | 3,185 | 3,584 | 4,035 | 7,928 | 2070 | 7,928 |
| Hijar | 1,408 | 1,442 | 1,639 | 1,852 | 2,100 | 2,315 | 2,571 |  |  |  |  | 2053 | 2,696 |
| Al Jahli | 1,376 | 1,409 | 1,601 | 1,810 | 2,052 | 2,263 | 2,513 | 2,831 | 3,746 |  |  | 2063 | 5,060 |
| Al Ghubayrah | 644 | 659 | 750 | 847 | 960 | 1,059 | 1,176 | 1,756 | 2,576 | 3,502 | 4,584 | 2070 | 4,584 |
| Al Qurayn | 588 | 602 | 684 | 773 | 877 | 967 | 1,074 | 1,201 | 7,176 |  |  | 2060 | 7,176 |
| Al Akheedar | 480 | 492 | 559 | 631 |  |  |  |  |  |  |  | 2036 | 640 |
| Al Makhtibyah | 364 | 373 | 424 | 479 | 543 | 599 | 665 | 744 | 837 | 1,522 |  | 2069 | 4,656 |
| Al Qali | 224 | 229 | 261 | 295 | 410 | 518 | 646 |  |  |  |  | 2054 | 788 |
| Shalashil | 152 | 156 | 177 | 200 | 227 | 250 | 278 | 311 | 8,322 |  |  | 2061 | 11,852 |
| Satwah | 108 | 111 | 126 | 142 | 161 | 178 | 197 | 221 | 392 |  |  | 2060 | 392 |
| Usaybuq | 84 | 86 | 98 | 110 | 125 | 138 | 153 |  |  |  |  | 2054 | 224 |
| Ash Shiab | 44 | 45 | 51 | 58 | 66 | 72 | 80 | 90 |  |  |  | 2056 | 92 |
| Wadi al Mankas | 32 | 33 | 37 | 42 | 48 | 53 | 58 | 65 | 74 | 2,859 |  | 2068 | 5,052 |
| Miayrid | 16 | 16 | 19 | 21 | 24 | 26 | 29 | 33 | 37 | 41 | 632 | 2070 | 632 |
| Total | 119,886 | 122,758 | 139,527 | 157,701 | 178,770 | 197,141 | 218,913 | 244,899 | 275,591 | 310,288 | 349,019 | 2070 | 349,019 |

**The same for sewage, m³/d** (report Table 19):

| Settlement | 2024 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 | 2055 | 2060 | 2065 | 2070 | Saturation year | Saturation flow |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ibri | 11,492 | 11,768 | 13,375 | 15,117 | 17,137 | 18,898 | 20,985 | 23,496 |  |  |  | 2056 | 24,048 |
| Ad Dariz | 2,030 | 2,079 | 2,363 | 2,670 | 3,027 | 3,338 | 3,707 | 4,147 | 4,686 |  |  | 2062 | 4,916 |
| Al Araqi | 1,832 | 1,876 | 2,132 | 2,410 | 2,732 | 3,013 | 3,346 | 3,743 |  |  |  | 2057 | 3,859 |
| At Tayyib | 799 | 813 | 893 | 980 | 1,081 | 1,169 | 1,273 | 1,398 | 1,618 | 4,330 |  | 2068 | 6,738 |
| Al Aynayn | 780 | 798 | 908 | 1,026 | 1,163 | 1,282 | 1,424 | 1,593 | 2,057 |  |  | 2060 | 2,057 |
| Al Wahrah | 574 | 588 | 668 | 755 | 856 | 944 | 1,048 | 1,172 | 1,319 | 1,487 | 1,792 | 2070 | 1,792 |
| Ad Dibayshi | 481 | 492 | 557 | 628 | 710 | 782 | 866 | 967 | 1,087 |  |  | 2063 | 1,838 |
| Al Jibayyah | 460 | 471 | 535 | 605 | 686 | 756 | 840 | 939 | 1,057 | 1,190 | 2,396 | 2070 | 2,396 |
| Bat | 438 | 449 | 510 | 576 | 653 | 720 | 800 |  |  |  |  | 2052 | 820 |
| Tanam | 419 | 428 | 478 | 533 | 597 | 653 | 718 | 797 | 890 | 1,078 |  | 2069 | 1,580 |
| Sayh al Masarrat | 313 | 321 | 364 | 412 | 467 | 515 | 572 | 640 | 720 | 820 |  | 2069 | 1,167 |
| Suwayda al Ma | 267 | 273 | 311 | 351 | 398 | 439 | 488 | 546 | 614 | 691 | 1,358 | 2070 | 1,358 |
| Hijar | 241 | 247 | 281 | 317 | 360 | 397 | 440 |  |  |  |  | 2053 | 462 |
| Al Jahli | 236 | 241 | 274 | 310 | 351 | 388 | 430 | 485 | 642 |  |  | 2063 | 867 |
| Al Ghubayrah | 110 | 113 | 128 | 145 | 164 | 181 | 201 | 301 | 441 | 600 | 785 | 2070 | 785 |
| Al Qurayn | 101 | 103 | 117 | 132 | 150 | 166 | 184 | 206 | 1,229 |  |  | 2060 | 1,229 |
| Al Akheedar | 82 | 84 | 96 | 108 |  |  |  |  |  |  |  | 2036 | 110 |
| Al Makhtibyah | 82 | 83 | 92 | 101 | 112 | 122 | 133 | 147 | 163 | 280 |  | 2069 | 817 |
| Al Qali | 38 | 39 | 45 | 50 | 70 | 89 | 111 |  |  |  |  | 2054 | 135 |
| Shalashil | 26 | 27 | 30 | 34 | 39 | 43 | 48 | 53 | 1,425 |  |  | 2061 | 2,030 |
| Satwah | 18 | 19 | 22 | 24 | 28 | 30 | 34 | 38 | 67 |  |  | 2060 | 67 |
| Usaybuq | 14 | 15 | 17 | 19 | 22 | 24 | 26 |  |  |  |  | 2054 | 38 |
| Ash Shiab | 8 | 8 | 9 | 10 | 11 | 12 | 14 | 15 |  |  |  | 2056 | 16 |
| Wadi al Mankas | 6 | 6 | 6 | 7 | 8 | 9 | 10 | 11 | 13 | 490 |  | 2068 | 865 |
| Miayrid | 3 | 3 | 3 | 4 | 4 | 4 | 5 | 6 | 6 | 7 | 108 | 2070 | 108 |
| Total | 20,851 | 21,343 | 24,215 | 27,328 | 30,936 | 34,083 | 37,812 | 42,263 | 47,520 | 53,463 | 60,097 | 2070 | 60,097 |

**The main overflow routes** (report Table 18; every route carrying a thousand people or more at saturation;
all routes of fifty or more are in Appendix A5):

| From | To | People at saturation | Donor full | Receiver starts | Receiver full |
|---|---|---|---|---|---|
| Ibri | At Tayyib | 22,074 | 2056 | 2060 | 2068 |
| Ibri | Shalashil | 11,471 | 2056 | 2056 | 2061 |
| Ibri | Al Qurayn | 5,856 | 2056 | 2056 | 2060 |
| Ad Dariz | Wadi al Mankas | 4,965 | 2062 | 2062 | 2068 |
| Al Araqi | At Tayyib | 4,873 | 2057 | 2060 | 2068 |
| Ibri | Ad Dibayshi | 4,078 | 2056 | 2062 | 2063 |
| Ibri | Al Jibayyah | 3,940 | 2056 | 2068 | 2070 |
| Bat | Al Ghubayrah | 2,494 | 2052 | 2052 | 2070 |
| Ibri | Al Makhtibyah | 2,441 | 2056 | 2063 | 2069 |
| Ibri | Tanam | 2,010 | 2056 | 2063 | 2069 |
| Al Araqi | Al Aynayn | 1,791 | 2057 | 2057 | 2060 |
| Al Aynayn | At Tayyib | 1,639 | 2060 | 2060 | 2068 |
| Al Araqi | Al Jibayyah | 1,410 | 2057 | 2068 | 2070 |
| Ibri | Sayh al Masarrat | 1,215 | 2056 | 2063 | 2069 |
| Ad Dibayshi | Tanam | 1,004 | 2063 | 2063 | 2069 |

**Saturation with and without the overflow** (Appendix A6):

| Settlement | Capacity, people | Full on own growth | Full with overflow | People received |
|---|---|---|---|---|
| Ibri | 73,301 | 2057 | 2056 | 117 |
| Ad Dariz | 16,852 | 2063 | 2062 | 805 |
| Al Araqi | 11,831 | 2057 | 2057 | 160 |
| Al Aynayn | 7,459 | 2066 | 2060 | 1,791 |
| Al Wahrah | 7,109 | 2073 | 2070 | 924 |
| At Tayyib | 34,672 | not before 2100 | 2068 | 28,932 |
| Ad Dibayshi | 7,920 | 2083 | 2063 | 4,078 |
| Al Jibayyah | 11,306 | 2095 | 2070 | 6,352 |
| Bat | 2,227 | 2052 | 2052 | 0 |
| Tanam | 6,779 | 2086 | 2069 | 3,015 |
| Sayh al Masarrat | 4,984 | 2081 | 2069 | 1,651 |
| Suwayda al Ma | 6,369 | 2094 | 2070 | 3,385 |
| Hijar | 1,288 | 2053 | 2053 | 0 |
| Al Jahli | 3,684 | 2080 | 2063 | 1,743 |
| Al Ghubayrah | 3,940 | not before 2100 | 2070 | 2,751 |
| Al Qurayn | 6,588 | not before 2100 | 2060 | 5,856 |
| Al Akheedar | 160 | 2036 | 2036 | 0 |
| Al Makhtibyah | 4,292 | not before 2100 | 2069 | 3,644 |
| Al Qali | 564 | 2078 | 2054 | 351 |
| Shalashil | 11,700 | not before 2100 | 2061 | 11,503 |
| Satwah | 284 | 2080 | 2060 | 150 |
| Usaybuq | 140 | 2067 | 2054 | 60 |
| Ash Shiab | 48 | 2056 | 2056 | 0 |
| Wadi al Mankas | 5,020 | not before 2100 | 2068 | 4,965 |
| Miayrid | 616 | not before 2100 | 2070 | 586 |

---

## 6. Load per plot, today and in every year

**Per person** (G1-p59–61, Table 11, Adh Dhahirah): domestic **164 L/d**; non-domestic **0.22 × 164 =
36 L/d**; governmental **0.14 × 164 = 23 L/d**. The three are separate streams, never compounded into one
rate. Sewage: **85 %** of domestic water, **54 %** of the rest (Table 19).

**Today, per plot.** People = dwelling meters × the settlement's occupancy. Domestic water and sewage
follow. The settlement's non-domestic and governmental water (its people × 36 and × 23 L/d) is landed on
its shop and government meters in proportion to their count; a settlement with none keeps it on its
dwellings. The two estates add their workforce × 93 L/d. Farm meters carry nothing. The plot table
(`PLOTS_load.shp`) holds every intermediate: `POP`, `W_DOM`, `W_NDOM`, `W_GOV`, `W_SPEC`, `S_*`, `QADF`.

**Future, per plot.** The people a settlement houses in a year are **spread over all its empty plots up
to 2,000 m²** (not grove, industrial, heritage, estate) **by plot area capped at 1,000 m²**. So every plot the
network passes carries a load, the slivers carry a sliver's share (1.3 % of the total), and the sum over
the plots equals the settlement's housed population by construction. A future plot's sewage is its people
× (164 × 0.85 + 36 × 0.54 + 23 × 0.54) = **171 L/d per person**, all three streams on the plot since no
better place is known. Columns `POP_2030`, `Q_2030`, `POP_2055`, `Q_2055`, `POP_ULT`, `Q_ULT`;
every year 2024–2100 per settlement in `W14_growth_by_settlement.xlsx`.

**What the plot does not carry.** Peak flow. Peaking is a property of the accumulated flow in a pipe
(Merrimack over 100 properties, Peltier as the alternative, G1-p71–72) and of the works (average, maximum
day, peak hour, plus tankers and the 10 % allowance). The network engine sums the plots upstream of each
pipe, adds infiltration per kilometre, and peaks there.

**The totals.**

| | People | Sewage m³/d |
|---|---|---|
| Today (2024) | 119,886 | 20,850 |
| 2030 | 139,529 | 24,215 |
| 2055 | 244,900 | 42,263 |
| **Saturation 2070** | **349,019** | **60,097** |

The inception report's ≈ 49,700 m³/d ultimate was built on connected population and the old occupancy;
this basis supersedes it and the report reconciles the two in one footnote (15.7).

---

## 7. Where it sits in the report (Revision 2)

**Two parts, one tone.** Official for the client, plain words, no internal vocabulary, every number read from
`W14/report/facts_w14.py`. Maps on A4 landscape pages, cloned from the saved layout; figure numbers only in the
captions.

| Report section | What is there | Figures and tables |
|---|---|---|
| 14.1 Approach | the chain in one paragraph and a flowchart | flowchart D3 |
| 14.2 Settlements | the merged settlement boundary and how a plot is assigned | map M05 |
| 14.3 Properties per plot | pure home plots, the ratio per settlement | Table 14 |
| 14.4 Occupancy rate | the equation, the floor and the cap, the under-1,000 rule, the full table | Table 15, charts C02 (derived v adopted), C04 |
| 14.5 Land use | the six rules, the satellite test, the class table | flowchart D6, chart C07, map M07 |
| 14.6 Capacity | the equation and the home-shape rule | — |
| 14.7 Growth | the series and its provenance, the filling, the five-year table, the overflow rule and main routes | chart C12 (rate by year), Table 17, Table 18, flowchart D7, charts C08 and C10, map M10 |
| 14.8 Spread | how the housed people land on the plots | — |
| 15.1–15.7 Flows | rates per person, the estates, return, flow per plot, infiltration, peak per pipe, the five-year flow table | chart C11 (streams), Table 19, chart C09, map M09 |
| 16 Identified projects | the large-consumer accounts, the estates, the army camp, Ibri View, the tanker sources | map M08 |
| A1 | tariff to category | |
| A2 | the 499 large-consumer accounts and their identified use | |
| A3 | occupancy, properties per plot and home share by settlement, derived and adopted, with the empty-plot counts | Table 28 |
| A4 | the field dictionary of the plot layer | |
| A5 | every overflow route of fifty people or more | |
| A6 | the saturation year with and without the overflow | |
