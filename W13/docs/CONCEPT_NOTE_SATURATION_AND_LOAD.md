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
÷ metered properties, **floored at 4.0**. Ibri 6.07, Bat 6.12, Ad Dariz 4.86, Al Araqi 4.34; eleven small
settlements sit on the floor because the census does not count their institutional residents. This
replaces the single measured 5.32 and makes today's population match the workbook settlement by
settlement.

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
Al Qurayn 20 %, Shalashil 10 %, then to Ad Dariz** (local knowledge); other settlements to the nearest
neighbour with spare room among those with 2,000 or more people.

**Fill years.** Ibri and Al Araqi 2056, Al Qurayn 2060, Shalashil and Ad Dariz 2062; the last receiver
fills in **2068, the saturation (ultimate) year**: 333,400 people. Seven small settlements never fill by
2100. The workbook's 2100 population for the 25 settlements is 690,000; the cadastre as drawn holds
369,000, so 361,000 of the workbook's 2100 people have no plot. The report should say so.

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
| Today (2024) | 120,100 | 20,900 |
| 2030 | 139,800 | 24,200 |
| 2055 | 245,300 | 42,300 |
| **Saturation 2068** | **333,400** | **57,400** |

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
| Population projection | growth rate per settlement, capacity, fill years, saturation year; the gap between the workbook's 2100 and the cadastre | **Chart 2** population by year per settlement (stacked); **Chart 3** fill years; **Flowchart B** "from empty plot to saturation" |
| Design flows | per-person rates, the three streams, return rates, the estates; totals today / 2030 / 2055 / saturation; peaking method | **Chart 4** sewage by year and by stream; **Map 3** Qadf per plot at saturation |
| Basis of design (criteria) | the rules in one table with guideline pages | **Flowchart C** "from plot to pipe flow" (plot → pipe sum → peak → works) |

**Appendix** — the working, so a reviewer can check without the scripts:

- A1 Tariff-to-category table and the 499 large-consumer accounts with their identified use and evidence.
- A2 Identified projects and special consumption register (the two estates, the army camp, Ibri View, the tanker sources).
- A3 Land-use derivation: the rule order, the NDVI calibration (thresholds, the 489 farm-meter plots, the contact sheet), the class change table v1 → v6.
- A4 Properties per plot and occupancy per settlement (table, 25 rows).
- A5 Empty plots: the home-shape rule, home share per settlement, capacity per settlement; the spread rule.
- A6 Growth tables: population and sewage per settlement per year 2024–2100, overflow routes, fill years.
- A7 The plot table field dictionary (`PLOTS_load.shp`), so the GIS deliverable is self-describing.

**Figures.** Maps from QGIS on the satellite base at 30 %, plots coloured by class, settlements as the
smoothed partition (Maps 1–3, A3 landscape). Charts from the growth workbook (Charts 1–4, the report's
chart style). Flowcharts A, B, C drawn in Figma, one page each, boxes in the report's words: *meters →
categories → land use → ratio → capacity → growth → load → pipe → works*. Figure numbers belong to the
caption, never to the image.

**Order of writing.** Sections 5 and 6 first (they carry the numbers), then 3 and 4 (they justify them),
then 2 (the data), then the executive summary last, placed first.
