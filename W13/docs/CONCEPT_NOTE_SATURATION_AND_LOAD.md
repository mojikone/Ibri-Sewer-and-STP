# Note for the Concept Design Report — saturation population and sewage load per plot

*W13, 10 September 2026. This note is the bridge between the working files and the report: what was
done, in what order, with which numbers, and where each piece lands in the report. Written for the
report author; the client-facing wording comes in the report itself.*

Live figures come from three scripts run in order: `W13/py/plots_meters_load.py` (QGIS),
`W13/py/plot_class_v2_apply.py`, `W13/py/growth_by_settlement.py`; the settlement polygons from
`W13/py/settlements_partition.py`; the NDVI from `W13/py/ndvi_plots.py`. Decisions and their dates are in
`W13/analysis/REFINEMENTS_PENDING.md`; the identified projects in `W13/analysis/IDENTIFIED_PROJECTS.md`.

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
Madayn, OSM footprints). Result (`W13/analysis/CRT_accounts_identified.csv`, with the evidence and a
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
plots** — built, Residential by rule 5, fewer than 15 dwelling meters (blocks of flats and labour housing
are excluded). Ibri 1.33, Al Araqi 1.32, Ad Dariz 1.20; small settlements with institutional housing run to
2.5. The first reading, which counted every built plot with a dwelling, gave Ibri 1.60 and was rejected.

**Occupancy rate**, per settlement: workbook population **2024** (the accounts' year, the report's base)
÷ metered properties, **floored at 4.0 and capped at 6.12** (the highest value among the settlements with
2,000 or more people, which is Bat's). Ibri 6.07, Bat 6.12, Ad Dariz 4.86, Al Araqi 4.34; eleven small
settlements sit on the floor because the census does not count their institutional residents, three tiny
ones on the cap. This replaces the single measured 5.32 and makes today's population match the workbook
settlement by settlement.

**The report must change with it.** Revision 1 states one occupancy rate, 5.32, measured over the whole
area, and every population and flow in it descends from that figure. The next revision states the rate per
settlement with the floor and the cap, explains the two in one sentence each (institutional residents the
census does not see; tiny settlements with a handful of meters), and re-derives the tables. The area-wide
average on today's 22,559 domestic properties is 5.16, not 5.32 (R1 divided by the 21,889 meters that fell inside a
plot, before the off-plot meters were snapped in); the settlement rows move, and so does the headline by three
percent.

**Say this in the report.** The rate is built on **domestic meters only**: the primary, subsidised and additional
dwelling tariffs. Shop, government, farm and large-consumer meters carry no people. And the floor at 4.0 puts
**3,300 people above the census** in eleven small settlements — Sayh Al Masarrat (+1,960) and Al Jahli (+1,410)
above all, where the police headquarters housing and the college housing carry 800 dwelling meters against 880
census residents. Those meters flush whether the census counts their occupants or not, so the design keeps them.
The report states the difference, the reason, and the choice, in one paragraph next to the occupancy table
(Appendix A4), so nobody reconciles the two totals by hand later.

**The occupancy table the report carries** (Appendix A4, and the used column in the main text):

| Settlement | Domestic properties | Workbook 2024 | Occupancy raw | Occupancy used | People used | Difference |
|---|---|---|---|---|---|---|
| IBRI | 11,052 | 67,105.51 | 6.07 | 6.07 | 58,663 | -8,443 |
| AD DARIZ | 2,439 | 11,849.67 | 4.86 | 4.86 | 12,937 | 1,087 |
| AL ARAQI | 2,466 | 10,695.68 | 4.34 | 4.34 | 13,087 | 2,391 |
| AL AYNAYN | 889 | 4,554.03 | 5.12 | 5.12 | 4,716 | 162 |
| AL WAHRAH | 716 | 3,351.08 | 4.68 | 4.68 | 3,799 | 448 |
| AT TAYYIB | 833 | 3,348.08 | 4.02 | 4.02 | 4,418 | 1,070 |
| AL JIBAYYAH | 524 | 2,685.66 | 5.13 | 5.12 | 2,780 | 94 |
| BAT | 418 | 2,556.77 | 6.12 | 6.12 | 2,218 | -339 |
| AD DIBAYSHI | 681 | 2,410.90 | 3.54 | 4 | 3,613 | 1,202 |
| TANAM | 403 | 2,116.16 | 5.25 | 5.25 | 2,140 | 24 |
| SUWAYDA AL MA | 301 | 1,558.64 | 5.18 | 5.18 | 1,598 | 39 |
| HIJAR | 352 | 1,033.10 | 2.93 | 4 | 1,868 | 835 |
| AL GHUBAYRAH | 161 | 631.45 | 3.92 | 4 | 854 | 223 |
| AL QURAYN | 147 | 548.52 | 3.73 | 4 | 779 | 230 |
| SAYH AL MASARRAT | 457 | 465.59 | 1.02 | 4 | 2,429 | 1,963 |
| AL JAHLI | 344 | 414.64 | 1.21 | 4 | 1,828 | 1,413 |
| SATWAH | 27 | 262.77 | 9.73 | 6.12 | 143 | -120 |
| AL AKHEEDAR | 120 | 197.83 | 1.65 | 4 | 638 | 440 |
| AL QALI | 56 | 190.83 | 3.41 | 4 | 297 | 106 |
| SHALASHIL | 38 | 129.89 | 3.42 | 4 | 202 | 72 |
| AL MAKHTIBYAH | 91 | 121.89 | 1.34 | 4 | 483 | 361 |
| USAYBUQ | 21 | 90.92 | 4.33 | 4.33 | 111 | 20 |
| WADI AL MANKAS | 8 | 51.95 | 6.49 | 6.12 | 42 | -10 |
| ASH SHIAB | 11 | 46.96 | 4.27 | 4.27 | 58 | 11 |
| MIAYRID | 4 | 33.97 | 8.49 | 6.12 | 21 | -13 |

---

## 5. Saturation: capacity, growth, fill year

**Which empty plots become homes.** A future home plot must look like the built ones: **200 to 1,000 m²,
compact** (≥ 0.6 of its rotated bounding box), **not a strip** (aspect ≤ 3), not a grove, not industrial, not
heritage, not in an estate. 46,109 of the 60,509 empty plots qualify. Slivers under 200 m² (6,084 plots,
1 % of the empty land), odd shapes and everything above 1,000 m² do not.

**Home share.** Not every home-shaped plot becomes a home: a district needs mosques, shops, offices.
The share is **measured** on each settlement's built, metered, home-shaped plots: pure homes ÷ all.
Ibri 0.87; the range is 0.82 to 0.94, with Tanam 0.67 and Al Akheedar 0.53 (shop-heavy).

**Capacity** per settlement = home-shaped empty plots × home share × properties per home plot ×
occupancy. Total **248,500 people** on top of today's 120,100.

**Growth.** Each settlement grows at its own **rate** from the inception workbook (*Project Pop
Settlements*, 2024–2100), applied to its metered population, and fills its capacity; all empty plots fill
together in proportion. When a settlement is full its overflow moves: **Ibri in parallel to Al Araqi 70 %,
Al Qurayn 20 %, Shalashil 10 %, then to Ad Dariz** (local knowledge), then to the nearest settlement with
spare room; every other settlement to its nearest neighbour with spare room. Every settlement receives,
whatever its size, so all 25 saturate.

**Fill years.** Ibri and Al Araqi 2057, Al Qurayn 2060, Shalashil and Ad Dariz 2062, Suwayda Al Ma last in
**2073, the saturation (ultimate) year**: every settlement full, **367,650 people**. The workbook is used
for its growth rates only; its 2100 total (690,000 for the 25 settlements) is not a target and not a
saturation figure. Saturation is what the cadastre holds. Growth beyond it is not planned for in this
concept, and the report says that in one sentence.

**Five-year steps to saturation, every settlement** (the table the report carries in the population section; a cell
is empty once the settlement is full; the last column is the exact year it fills; the sewage version is the sheet
*Five-year Qadf* of the growth workbook):

| Settlement | 2024 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 | 2055 | 2060 | 2065 | 2070 | 2075 | Saturation year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IBRI | 67,094 | 68,702 | 78,086 | 88,257 | 100,049 | 110,330 | 122,514 | 137,057 |  |  |  |  | 2,057 |
| AD DARIZ | 11,852 | 12,136 | 13,794 | 15,590 | 17,673 | 19,490 | 21,642 | 24,211 | 27,246 |  |  |  | 2,062 |
| AL ARAQI | 10,698 | 10,954 | 12,451 | 14,072 | 15,953 | 17,592 | 19,535 | 21,854 |  |  |  |  | 2,057 |
| AL AYNAYN | 4,553 | 4,662 | 5,299 | 5,989 | 6,789 | 7,487 | 8,314 | 9,301 | 12,012 |  |  |  | 2,060 |
| AL WAHRAH | 3,351 | 3,431 | 3,900 | 4,408 | 4,997 | 5,510 | 6,119 | 6,845 | 7,703 | 8,684 | 9,803 |  | 2,071 |
| AT TAYYIB | 3,349 | 3,429 | 3,898 | 4,405 | 4,994 | 5,507 | 6,115 | 6,841 | 8,131 | 17,539 |  |  | 2,069 |
| AD DIBAYSHI | 2,724 | 2,789 | 3,170 | 3,583 | 4,062 | 4,479 | 4,974 | 5,564 | 6,262 |  |  |  | 2,063 |
| AL JIBAYYAH | 2,684 | 2,749 | 3,128 | 3,538 | 4,014 | 4,429 | 4,921 | 5,508 | 6,201 | 6,985 | 8,694 |  | 2,072 |
| BAT | 2,558 | 2,619 | 2,977 | 3,365 | 3,814 | 4,206 | 4,671 |  |  |  |  |  | 2,052 |
| TANAM | 2,116 | 2,167 | 2,463 | 2,783 | 3,155 | 3,480 | 3,864 | 4,322 | 4,864 | 5,961 | 8,895 |  | 2,070 |
| SAYH AL MASARRAT | 1,828 | 1,872 | 2,127 | 2,405 | 2,726 | 3,006 | 3,338 | 3,734 | 4,202 | 4,750 | 6,229 |  | 2,072 |
| SUWAYDA AL MA | 1,559 | 1,596 | 1,814 | 2,051 | 2,325 | 2,564 | 2,847 | 3,185 | 3,584 | 4,035 | 4,543 |  | 2,073 |
| HIJAR | 1,408 | 1,442 | 1,639 | 1,852 | 2,100 | 2,315 | 2,571 |  |  |  |  |  | 2,053 |
| AL JAHLI | 1,376 | 1,409 | 1,601 | 1,810 | 2,052 | 2,263 | 2,513 | 2,811 | 3,163 | 8,264 |  |  | 2,065 |
| AL GHUBAYRAH | 644 | 659 | 750 | 847 | 960 | 1,059 | 1,176 | 1,756 | 2,576 | 3,502 | 4,546 |  | 2,071 |
| AL QURAYN | 588 | 602 | 684 | 773 | 877 | 967 | 1,074 | 1,201 | 8,376 |  |  |  | 2,060 |
| AL AKHEEDAR | 480 | 492 | 559 | 631 |  |  |  |  |  |  |  |  | 2,039 |
| AL MAKHTIBYAH | 364 | 373 | 424 | 479 | 543 | 599 | 665 | 744 | 837 | 1,140 | 5,288 |  | 2,070 |
| AL QALI | 224 | 229 | 261 | 295 | 366 | 474 | 602 | 851 | 1,415 |  |  |  | 2,061 |
| SATWAH | 165 | 169 | 192 | 217 | 246 | 271 | 301 | 337 | 625 |  |  |  | 2,061 |
| SHALASHIL | 152 | 156 | 177 | 200 | 227 | 250 | 278 | 311 | 7,004 |  |  |  | 2,062 |
| USAYBUQ | 91 | 93 | 106 | 120 | 136 | 150 | 166 |  |  |  |  |  | 2,054 |
| WADI AL MANKAS | 49 | 50 | 57 | 64 | 73 | 81 | 89 | 100 | 113 | 2,903 | 8,576 |  | 2,070 |
| ASH SHIAB | 47 | 48 | 55 | 62 | 70 | 77 | 86 | 96 | 107 |  |  |  | 2,060 |
| MIAYRID | 24 | 24 | 24 | 24 | 24 | 24 | 24 | 24 | 24 | 24 | 24 | 24 |  |
| TOTAL | 119,978 | 122,852 | 139,636 | 157,820 | 178,909 | 197,294 | 219,083 | 245,087 | 275,803 | 310,526 | 349,622 | 367,649 | 2,073 |

---|---|---|
| 2024 (base) | 119,978 | 20,872 |
| 2025 | 122,852 | 21,365 |
| 2030 | 139,636 | 24,239 |
| 2035 | 157,820 | 27,354 |
| 2040 | 178,909 | 30,966 |
| 2045 | 197,294 | 34,115 |
| 2050 | 219,083 | 37,847 |
| 2055 | 245,087 | 42,301 |
| 2060 | 275,803 | 47,563 |
| 2065 | 310,526 | 53,510 |
| 2070 | 349,622 | 60,206 |
| 2075 ≈ saturation | 367,649 | 63,294 |

The ten largest settlements, people at five-year steps and the year each fills:

| Settlement | 2024 | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 | 2055 | 2060 | 2065 | 2070 | 2075 | full |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Ibri | 67,094 | 68,702 | 78,086 | 88,257 | 100,049 | 110,330 | 122,514 | 137,057 | 140,395 | 140,395 | 140,395 | 140,395 | 2057 |
| Al Araqi | 10,698 | 10,954 | 12,451 | 14,072 | 15,953 | 17,592 | 19,535 | 21,854 | 22,529 | 22,529 | 22,529 | 22,529 | 2057 |
| Ad Dariz | 11,852 | 12,136 | 13,794 | 15,590 | 17,673 | 19,490 | 21,642 | 24,211 | 27,246 | 28,704 | 28,704 | 28,704 | 2062 |
| Al Aynayn | 4,553 | 4,662 | 5,299 | 5,989 | 6,789 | 7,487 | 8,314 | 9,301 | 12,012 | 12,012 | 12,012 | 12,012 | 2060 |
| At Tayyib | 3,349 | 3,429 | 3,898 | 4,405 | 4,994 | 5,507 | 6,115 | 6,841 | 8,131 | 17,539 | 38,021 | 38,021 | 2069 |
| Al Wahrah | 3,351 | 3,431 | 3,900 | 4,408 | 4,997 | 5,510 | 6,119 | 6,845 | 7,703 | 8,684 | 9,803 | 10,460 | 2071 |
| Ad Dibayshi | 2,724 | 2,789 | 3,170 | 3,583 | 4,062 | 4,479 | 4,974 | 5,564 | 6,262 | 10,644 | 10,644 | 10,644 | 2063 |
| Al Jibayyah | 2,684 | 2,749 | 3,128 | 3,538 | 4,014 | 4,429 | 4,921 | 5,508 | 6,201 | 6,985 | 8,694 | 13,990 | 2072 |
| Bat | 2,558 | 2,619 | 2,977 | 3,365 | 3,814 | 4,206 | 4,671 | 4,785 | 4,785 | 4,785 | 4,785 | 4,785 | 2052 |
| Tanam | 2,116 | 2,167 | 2,463 | 2,783 | 3,155 | 3,480 | 3,864 | 4,322 | 4,864 | 5,961 | 8,895 | 8,895 | 2070 |


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
every year 2024–2100 per settlement in `W13_growth_by_settlement.xlsx`.

**What the plot does not carry.** Peak flow. Peaking is a property of the accumulated flow in a pipe
(Merrimack over 100 properties, Peltier as the alternative, G1-p71–72) and of the works (average, maximum
day, peak hour, plus tankers and the 10 % allowance). The network engine sums the plots upstream of each
pipe, adds infiltration per kilometre, and peaks there.

**The totals.**

| | People | Sewage m³/d |
|---|---|---|
| Today (2024) | 120,000 | 20,900 |
| 2030 | 139,600 | 24,200 |
| 2055 | 245,100 | 42,300 |
| **Saturation 2073** | **367,650** | **63,300** |

The inception report's ≈ 49,700 m³/d ultimate was built on connected population and the old occupancy;
this basis supersedes it and the report must reconcile the two in one paragraph.

---

## 7. How it goes into the report

**Two parts, one tone.** Official for the client, plain words, no internal vocabulary, every number traceable.

**Main body** — answers the TOR item by item, short, with the result and the one figure that shows it:

| Report section (TOR) | What goes there | Figure |
|---|---|---|
| Existing situation: population and connections | today's people and properties per settlement; how they were counted | **Map 1** settlements with people today; **Chart 1** properties per settlement |
| Land use | the derived land-use map and the seven classes; the two industrial estates as identified projects | **Map 2** land use per plot; **Flowchart A** "from meter to land use" |
| Population projection | growth rate per settlement, capacity, fill years, saturation year, **the five-year table to saturation**; the occupancy per settlement replacing R1's 5.32; the gap between the workbook's 2100 and the cadastre | **Table** five-year steps; **Chart 2** population by year per settlement (stacked); **Chart 3** fill years; **Flowchart B** "from empty plot to saturation" |
| Design flows | per-person rates, the three streams, return rates, the estates; totals today / 2030 / 2055 / saturation; peaking method | **Chart 4** sewage by year and by stream; **Map 3** Qadf per plot at saturation |
| Basis of design (criteria) | the rules in one table with guideline pages | **Flowchart C** "from plot to pipe flow" (plot → pipe sum → peak → works) |

**Appendix** — the working, so a reviewer can check without the scripts:

- A1 Tariff-to-category table and the 499 large-consumer accounts with their identified use and evidence.
- A2 Identified projects and special consumption register (the two estates, the army camp, Ibri View, the tanker sources).
- A3 Land-use derivation: the rule order, the NDVI calibration (thresholds, the 489 farm-meter plots, the contact sheet), the class change table v1 → v6.
- A4 Properties per plot and occupancy per settlement (table, 25 rows, with the floor and the cap and why).
- A5 Empty plots: the home-shape rule, home share per settlement, capacity per settlement; the spread rule.
- A6 Growth tables: population and sewage per settlement at five-year steps to saturation (and per year in the digital annex), overflow routes, fill years.
- A7 The plot table field dictionary (`PLOTS_load.shp`), so the GIS deliverable is self-describing.

**Figures.** Maps from QGIS on the satellite base at 30 %, plots coloured by class, settlements as the
smoothed partition (Maps 1–3, A3 landscape). Charts from the growth workbook (Charts 1–4, the report's
chart style). Flowcharts A, B, C drawn in Figma, one page each, boxes in the report's words: *meters →
categories → land use → ratio → capacity → growth → load → pipe → works*. Figure numbers belong to the
caption, never to the image.

**Order of writing.** Sections 5 and 6 first (they carry the numbers), then 3 and 4 (they justify them),
then 2 (the data), then the executive summary last, placed first.
