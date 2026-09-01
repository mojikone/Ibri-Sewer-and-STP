# W10 Phase 1.3 — saturation sewage load, every plot in the study area

**Run 2026-09-01 · `W10/py/p1_loads.py` · outputs `W10/shp/W10_plot_loads.shp`,
`W10/run/W10_load_summary.csv`, `W10/run/W10_load_checks.csv`.**

**Headline: the saturated plot load over the whole study area is 74,675 m³/d, and that is
50 % above the 49,700 m³/d the project has carried since W2.** The whole of the difference
is population and none of it is a change of method: × 1.291 from the property and occupancy
basis the project itself settled on 30 August, × 1.207 from covering the whole cadastre
inside the boundary instead of only the 36 W2 zones, and 1.291 × 1.207 = 1.558 exactly. The
49,700 figure is stale and should be retired, not defended — see §7.

---

## 1. What this deliverable is

One record per cadastral plot (61,272) and one per unparceled building (2,799), each
carrying the average dry-weather flow it discharges when the study area is fully
developed. **64,071 records, 64,027 of them inside the boundary.** The pipe-sizing solver
accumulates `Q_AVG_M3D` down the tree and applies the peaking factor to the accumulated
flow; it is never applied to a single plot.

This is the **saturation** case, per the load-allocation doctrine
(`_BRAIN/07_PROJECT_STATE.md` §2 item 1): *plots at saturation size the pipes; capped-and-
spilled zone totals at dated years size the STP phases; the two meet only at trunk nodes.*
Dated-year totals are a separate zone-level exercise and are not in this run.

---

## 2. The chain, from an electricity account to litres

```
NAMA electricity account  ──tariff──►  guideline category   (GUD-201 §7.3.1–7.3.4)
                                          │
        ┌─────────────────────────────────┼──────────────────────────────┐
        ▼                                 ▼                              ▼
    domestic                        non-domestic                    agricultural
    (dwelling)                      / government                    (irrigation pump)
        │                                 │                              │
        │  counted per plot, or the       │  counted per plot, or the    │  NO sewage
        │  measured rate on a plot        │  measured rate on a plot     │  load at all
        │  with no meter                  │  with no meter               │  (I-4 / I-5)
        ▼                                 ▼
   N_DOM × OR 5.32 = POP           N_ND, N_GOV = premises
        │                                 │
        ▼                                 │
   POP × 164 l/c/d = domestic WATER       │
        │                                 │
        ├── × 0.85 return ──────────────► Q_DOM   (per plot, direct)
        │                                 │
        ├── × 0.22 × 0.54 ──► Q_ND_total ─┼──► shared over N_ND    ► Q_ND   (per plot)
        │                                 │
        └── × 0.14 × 0.54 ──► Q_GOV_total ┴──► shared over N_GOV   ► Q_GOV  (per plot)

   Q_AVG_M3D = Q_DOM + Q_ND + Q_GOV
```

**Tier A ratios set the volume; land use sets the placement.** The two axes do not overlap,
so this is not tier-mixing (`02_DESIGN_CRITERIA.md` §11.1, locked 2026-08-30). **Table 12 is
not used and must never be combined with the ratios.**

The ratio totals are normalised across the premises they land on, so `ND_PER_PLOT` and
`GOV_PER_PLOT` move flow **between branches** and can never change the project total. Only
`DOM_PER_PLOT` and `OR` move the total.

Cross-check on the arithmetic: 164 × (0.85 + 0.22×0.54 + 0.14×0.54) = **171.3 l/c/d**, the
area-average rate the project has used since W2, and the run reproduces it to two decimals
(74,675 × 1000 ÷ 435,945 = 171.3). The chain is the same; only the population it is applied
to has changed.

---

## 3. Every constant, with the page it came from

| Constant | Value | Source | Confidence |
|---|---|---|---|
| Occupancy rate `OR` | **5.32** people per domestic property | `02` §11.1 ★ (derived 2026-08-30: 2024 settlement population ÷ domestic properties, both clipped to the same 25 settlements); method G1-p58 §7.2.2 | [Certain] as a measurement of 2024 |
| Domestic water `LPCD_WATER` | **164** l/c/d, Adh Dhahirah | G1-p59–60 Tab 11 | [Certain] |
| Return rate, domestic | **0.85** | G1-p70–71 Tab 19 | [Certain] |
| Return rate, non-domestic + governmental | **0.54** | G1-p70–71 Tab 19 | [Certain] |
| Non-domestic ratio | **+22 %** of domestic water ("Distributed Non-Domestic Ratio") | G1-p60 Tab 11, §7.3.2 | [Certain] as a quoted value |
| Governmental ratio | **+14 %** of domestic water ("Distributed Governmental Ratio") | G1-p60–61 Tab 11, §7.3.3 | [Certain] as a quoted value |
| Residential wastewater rate (derived) | 164 × 0.85 = **139.4** l/c/d | arithmetic on the two rows above | [Certain] |
| Area-average rate (derived, cross-check only) | **171.3** l/c/d | arithmetic | [Certain] |
| Domestic properties per residential plot | **1.456** | `02` §11.1 ★ "1.456 domestic properties per matched plot" | [Likely] as a saturation rate — see §5.1 |
| Non-domestic premises per commercial plot | **4.434** | measured in this run on built plots that carry a non-domestic meter | [Likely], placement only |
| Government premises per government plot | **1.530** | measured in this run on built plots that carry a government meter | [Likely], placement only |
| Unparceled building | **1.0** dwelling | assumption, median footprint 75 m² | [Guessing] |
| Minimum premises parcel area | **100 m²** | assumption on measured evidence — see §5.3 | [Likely] |
| Infiltration | 720 L/d per km of sewer, new networks | G1-p72 §7.4.3 | [Certain] — **a pipe load, not in this layer** |
| Peaking factor | Merrimack `Qpdf = 2.65·Qadf^0.879` (Ml/d), mandatory above 100 properties | G1-p71 §7.4.2 | [Certain] — **applied on the accumulated flow, not here** |
| STP design margin | +10 % on a new STP, over and above redundancy | G1-p73 §7.4.5 | [Certain] — **not in this layer** |

### Tariff → guideline category crosswalk (GUD-201 §7.3.1–7.3.4)

| NAMA tariff | Accounts | Category | Note |
|---|---|---|---|
| Primary Account Tariff | 10,972 | domestic | one occupied dwelling (I-2) |
| Primary Account Tariff (with National Subsidy) | 5,272 | domestic | |
| Additional Account Tariff | 6,344 | **domestic** | a separate dwelling, not a second meter (I-3); counting primaries only under-predicts by ~19 % |
| Commercial | 9,385 | non-domestic | |
| Fisheries / Tourism | 7 | non-domestic | |
| CRT Seasonal / Time of Use / Fixed Rate | 499 | non-domestic | **[ASSUMPTION]** CRT is a consumption threshold, not a land use (I-6) |
| Government | 966 | government | |
| MOD | 1 | government | |
| Agricultural | 523 | agricultural | irrigation pump — **no sewage load** (I-4) |
| Industrial | 1 | industrial | **outside the ratios** (G1-p59) |

Total 33,970 accounts; **9,208 (27.1 %) fall outside every plot polygon** and could not be
attributed. That is why a counted zero on a plot is not treated as evidence of an empty
plot — see §4.

### MoH `LANDUSE` → placement category

| Arabic value | Plots | Placement |
|---|---|---|
| (empty) | 39,838 | residential if the imagery class is B or P — **the largest placeholder in the run**, §5.2 |
| سكني residential | 13,445 | residential |
| زراعى agricultural | 3,336 | no load unless a household meter is present |
| حكومي governmental | 2,502 | government |
| سكني/تجاري residential + commercial | 1,057 | both |
| تجاري commercial | 571 | commercial |
| مسجد mosque | 465 | commercial (non-domestic) |
| صناعي industrial | 55 | **zero, flagged** — outside the ratios |
| سكنى/زراعى residential + agricultural | 3 | residential |

---

## 4. How the premises count on each plot is set

For each plot, for each of the three categories:

```
N = max( meters counted on that plot ,  the measured rate if the plot is eligible )
```

- **Counted where meters exist.** A plot with 18 domestic meters is sized for 18 dwellings.
- **The measured rate where they do not.** 27 % of the accounts fall outside every plot
  polygon, so a counted zero is at least as often a cadastre gap as an empty plot. A plot
  that the classifier calls built or planned and whose land use is residential or empty
  carries 1.456 dwellings whether or not a meter landed inside it.
- **`max`, not a sum.** The two are alternative estimates of the same thing, never additive.
- **Agricultural meters are dropped outright** before any of this: an agricultural meter on a
  plot that already carries a household meter adds nothing, and an agricultural-only plot
  carries no dwelling (doctrine, I-4/I-5).
- **Industrial plots carry zero** and are flagged. G1-p59: *"These ratios do not apply to the
  water consumption of specific identified non-domestic projects such as economic zones[,
  which] are to be determined on a case-by-case basis."* No quantities were supplied. **This
  is a hole in the total, not a finding that they discharge nothing.**

`BASIS` in the shapefile records which route each record took: `counted`, `rate`,
`counted+rate`, `none`.

| BASIS | Records |
|---|---|
| rate | 43,880 |
| counted+rate | 10,399 |
| none (zero load) | 7,628 |
| counted | 2,120 |

---

## 5. What is a PLACEHOLDER, and what the clean data will change

The user has said clean land-use data is still coming from the GIS expert. Every item below
is a named constant or a named crosswalk in `W10/py/p1_loads.py`; nothing is hard-coded
downstream, and the run is a single command.

### 5.1 `DOM_PER_PLOT = 1.456` — the biggest single lever [Likely]

Measured on plots that carry a domestic meter, and then applied to **every** residential
plot at saturation, planned ones included. That assumes future plots develop at today's
density. G1-p59 NOTE warns that plot subdivision usually pushes the effective number of
housing units **up**, not down, so the direction of the assumption is conservative for pipe
sizing — which is the correct direction (`02` §11.1 ★★ accuracy is directional).

It is also the number that decides whether this run agrees with 49,700:

| `DOM_PER_PLOT` | Dwellings | Population | Qadf m³/d | vs 49,700 |
|---|---|---|---|---|
| 1.456 (design basis, `02` §11.1) | 81,945 | 435,945 | **74,675** | +50.2 % |
| 1.413 (built plots only) | 79,867 | 424,894 | 72,782 | +46.4 % |
| 1.000 (the W8 fallback) | 59,917 | 318,758 | 54,602 | +9.8 % |

**Replace with:** the clean plot layer's dwelling count, or NCSI housing units at settlement
level (GAP-5).

### 5.2 65 % of the cadastre has no land-use attribute [Guessing on placement]

39,838 plots carry no `LANDUSE` value. Every one of them that the imagery classifier did not
call agricultural is loaded as residential, which is the W3 A7 convention. **36,489 of the
51,917 dwelling-bearing plots (70.3 %) reach that status on this convention alone.** If even a
tenth of them are actually commercial, government or open space, the domestic total moves by
several thousand m³/d and, more importantly, the flow moves between branches.

**Replace with:** the clean land-use attribute. This is the single change most likely to
alter branch sizing.

### 5.3 `MIN_PREMISES_AREA_M2 = 100` — the service-parcel filter [Likely]

A parcel below 100 m² carrying **no** electricity meter is treated as a service parcel
(substation, kiosk, tank) and gets no load. The evidence, measured in this run:

| Parcel area | Plots | Carry a meter | Rate |
|---|---|---|---|
| ≤ 20 m² | 519 | 10 | 1.9 % |
| 20–50 m² | 2,221 | 75 | 3.4 % |
| 50–100 m² | 898 | 103 | 11.5 % |
| 100–200 m² | 1,221 | 230 | 18.8 % |
| 200–400 m² | 3,220 | 1,182 | 36.7 % |

And decisively: of the **1,562 parcels whose land use is حكومي (governmental) and whose area
is under 100 m² — median 40 m² — not one carries a government meter, and two carry any meter
at all.** Those are electrical and telecom plots, not buildings. Without the filter they
absorbed 39 % of the governmental premises count and pushed 2,870 records past 25 L/m²/d.

The 100 m² line itself is a judgement on that breakpoint, not a guideline value.
**Sensitivity:** removing the filter raises the total from 74,675 to 76,998 m³/d (+3.1 %) and
triples the sanity-band failures.

### 5.4 CRT accounts counted as non-domestic [Guessing]

499 accounts on the Cost Reflective Tariff. CRT is a consumption threshold, so a mall, a
factory, a hotel and a large government building all land in it (I-6). They are counted as
non-domestic premises because they are certainly not dwellings; a large government building
sitting in CRT is therefore placed on the wrong stream. **Resolve against the plot layer or
by site check.**

### 5.5 The industrial estate is missing entirely [Certain that it is missing]

55 industrial-land-use plots and one Industrial-tariff account carry **zero**. G1-p59 puts
identified projects outside the ratios and requires a case-by-case figure that nobody has
supplied. The industrial estate is also not identifiable in the account data (I-7). **This is
an open hole in the total.** Four streams sit outside the ratios in the same way and are all
still zero here: identified projects, special consumption (labour camps), blue and yellow
tankers, and private wells — all four are additive when their data arrives, and **tanker
water returns sewage at the same 85 % as domestic** (Tab 19). Given Tab 13 puts Adh
Dhahirah's tanker demand at 333 % of network domestic consumption, this omission is more
likely to raise the total than to lower it.

### 5.6 Smaller placeholders

| Item | Value | What would settle it |
|---|---|---|
| Unparceled building = 1 dwelling | 2,789 records, 2,068 m³/d | the clean plot layer, which should parcel them |
| `ND_PER_PLOT` 4.434, `GOV_PER_PLOT` 1.530 | placement only, total unaffected | Table 12 quantities (pupils, beds, employees, floor areas) |
| 9,208 accounts with no plot (27.1 %) | not attributed to any record | the clean plot layer |
| 34 plots fall outside the boundary | excluded from totals, kept in the layer with `IN_BND = 0` | boundary confirmation |

---

## 6. Totals

### By plot class (inside the boundary)

| CLASS | Records | Dwellings | ND premises | Gov premises | Population | Qadf m³/d | Qadf L/s | Zero load |
|---|---|---|---|---|---|---|---|---|
| B built | 17,960 | 27,129 | 7,510 | 412 | 144,325 | 25,725 | 297.7 | 1,054 |
| P planned | 36,927 | 48,669 | 6,710 | 967 | 258,917 | 43,096 | 498.8 | 2,343 |
| A agricultural | 6,351 | 3,358 | 858 | 244 | 17,865 | 3,787 | 43.8 | 4,242 |
| U unparceled buildings | 2,789 | 2,789 | 0 | 0 | 14,837 | 2,068 | 23.9 | 0 |
| **Total** | **64,027** | **81,945** | **15,078** | **1,623** | **435,945** | **74,675** | **864.3** | **7,639** |

### By category

| CAT | Records | Qadf m³/d | Share |
|---|---|---|---|
| domestic | 52,214 | 56,534 | 75.7 % |
| mixed (dwellings + premises on one plot) | 2,492 | 11,568 | 15.5 % |
| government | 675 | 3,412 | 4.6 % |
| commercial | 837 | 2,004 | 2.7 % |
| commercial + government | 170 | 1,158 | 1.6 % |
| agricultural | 4,240 | 0 | — |
| none | 3,344 | 0 | — |
| industrial | 55 | 0 | — |

### By flow stream — the check that matters

| Stream | Qadf m³/d | Share |
|---|---|---|
| **Domestic** | **60,771** | **81.4 %** |
| Non-domestic | 8,497 | 11.4 % |
| Governmental | 5,407 | 7.2 % |

Domestic dominates, as it must. The 81.4 / 11.4 / 7.2 split is the arithmetic consequence of
0.85 : 0.22×0.54 : 0.14×0.54 and is therefore fixed by the guideline, not by our placement.

### Not in this layer, and why

| Item | Value | Where it belongs |
|---|---|---|
| Infiltration | 720 L/d per km of upstream sewer | on the **pipe**, unpeaked (G1-p72) — the solver adds it |
| Peaking factor | Merrimack, mandatory above 100 properties | on the **accumulated** flow at each reach |
| STP margin | +10 % | at the works, over and above redundancy (G1-p73) |
| Tankers, private wells, labour camps, the industrial estate | unknown | **additive outside the ratios** when the data lands |

---

## 7. Reconciliation against 49,700 m³/d — and the disagreement

**This run disagrees with 49,700 m³/d by +50 %, and the newer figure is the one to use.**

First, what 49,700 actually is. It comes from `W2/report/zone_flows.csv`: 36 zones,
53,503 plots, of which 46,626 were called residential, at **1.0 property per plot and OR
6.0** → 279,756 people → 47,917 m³/d, **plus 1,798 m³/d of infiltration** (720 L/d/km over
2,497 km of screening-level sewer) = 49,715. Compared like with like, the W2 **plot** load is
47,917 m³/d, not 49,700.

| | W2 (2026-08) | W10 (this run) | Ratio |
|---|---|---|---|
| People per residential plot | 1.0 × OR 6.0 = 6.00 | 1.456 × OR 5.32 = 7.746 | **× 1.291** |
| Plots carrying dwellings | 46,626 | 51,917 | **× 1.207** |
| Population | 279,756 | 435,945 | × 1.558 |
| Plot load | 47,917 m³/d | 74,675 m³/d | × 1.558 |

1.291 × 1.207 = 1.558 exactly. **The entire difference is population; the flow chain is
identical** (both land on 171.3 l/c/d).

**Which is more likely right: W10.** Three reasons.

1. **W2's inputs were already declared superseded.** `_BRAIN/07_PROJECT_STATE.md` §5 carries
   the warning in its own heading: *"W1–W3 numbers below were built at OR 6.0 — the design
   basis is now OR 5.32 with properties COUNTED from electricity accounts, so they need
   rescaling before reuse."* This run is that rescaling. 49,700 was never re-derived after
   the basis changed; it was carried forward because nothing had replaced it.
2. **1.0 property per plot is contradicted by the data.** 6,344 "Additional Account Tariff"
   records are 28 % of all domestic accounts, and I-3 records that counting primaries only
   under-predicts dwellings by ~19 %. A plot is not a dwelling.
3. **The plot base is wider because the boundary is wider.** W2 assigned 53,503 of 61,272
   plots to one of its 36 zones; 7,769 plots sat outside every zone and carried no load.
   W10 covers all 61,238 plots inside the 531.4 km² boundary. Those plots exist and will be
   sewered.

**What would make W10 wrong, and by how much.** Only two things move the total: the property
rate and the occupancy rate. Both are recorded above (§5.1). If `DOM_PER_PLOT` should be 1.0
after all, the answer falls to 54,602 m³/d and 49,700 is nearly vindicated. Nothing in the
data supports 1.0, but the number rests on applying a measurement made on **built** plots to
**planned** ones, which is an assumption and not a measurement.

**What must not be concluded from this.** 74,675 m³/d is the **saturation envelope for buried
civil works**. It is not the 25-year STP capacity and must never be quoted as one. G1-p59
NOTE is explicit: *"development speed must be considered through appropriate phasing
assumptions, as not all plots will be developed simultaneously … particularly avoiding
overestimation."* Raw plot count × OR at 100 % build-out is non-compliant **as a design-period
population**. The doctrine resolves the tension by using saturation for pipes and capped
zone totals for STP phasing; this run supplies the first only.

### Against NCSI / R0

| | Population | W10 saturation ÷ |
|---|---|---|
| R0/NCSI 2024, 25 settlement polygons | 116,456 | 3.74 |
| R0/NCSI 2055 | 237,885 | **1.83** |
| R0/NCSI 2100 | 691,264 | **0.63** |
| W3 A1 land ceiling at OR 6.0 × 1 property/plot | 269,796 | 1.62 |

Two consequences worth carrying forward.

- **The A1 capacity ceilings all move.** A1 computed them at OR 6.0 × 1 property per plot and
  found IBRI crossing its ceiling around 2038. On the counted-property basis the boundary
  ceiling rises from 269,796 to 435,945 people, so **every ceiling-crossing year in
  `W3/analysis/A1_zone_capacity.csv` is now too early** and A1/A2 should be re-run before any
  dated-year or spillover figure is quoted again.
- **R0's 2100 projection is still unhousable**, even on the raised ceiling: 691,264 projected
  against 435,945 that the cadastre can physically hold, a surplus of 255,000. That confirms
  the A1 finding rather than overturning it, and it is a reason to defend the ultimate case
  on land capacity rather than on the extrapolated curve (G1-p58 limits extrapolation to ten
  years beyond NCSI's own horizon).

---

## 8. Checks

| Check | Result | Read |
|---|---|---|
| Total premises at saturation | 98,646 (81,945 dwellings + 15,078 non-domestic + 1,623 government) | — |
| Population at OR 5.32 | 435,945 | 1.83 × R0 2055, 0.63 × R0 2100 |
| Records with zero load | 7,639 of 64,027 (11.9 %) | every one has a stated reason, none silent |
| — agricultural plot, no household meter (I-5) | 4,235 | doctrine, correct |
| — parcel under 100 m² with no meter | 3,349 (B 1,046 · P 2,303) | service parcels, §5.3 |
| — industrial, outside the ratios (G1-p59) | 55 | **an open hole**, §5.5 |
| Zero load by class | A 4,242 · P 2,343 · B 1,054 | class B zeros are 1,046 micro service parcels + 8 industrial; no built plot is dropped for any other reason |
| Median load per parcel area | 1.67 L/m²/d | a 690 m² plot at 1.456 dwellings — sane |
| 95th percentile | 8.83 L/m²/d | below the Tab 12 shopping rate on plot area, sane |
| Above 25 L/m²/d | 554 records, **2.5 % of total flow** | dense metered plots; the count fell from 2,870 once §5.3 was applied |
| Above 100 L/m²/d | 12 records | **all 12 are parcels under 100 m² that carry a meter**, i.e. the meter point landed on a sliver parcel beside the real building. Worst is 233 L/m²/d on 18.9 m². A cadastre/meter-position artefact for the clean layer to fix, not a design case |
| Below 0.05 L/m²/d | 543 records | large compounds and farms with a couple of meters — harmless |
| Micro parcels still loaded | 187 | they carry a meter, so the load is real even if the parcel is not the building. `SANITY` shows only 57 of them because the flow-relevant `high`/`very_high` label takes precedence |
| Share of flow, domestic | **81.4 %** | domestic dominates, as required |
| Records outside the boundary | 44 (34 plots + 10 buildings) | kept in the layer, `IN_BND = 0`, excluded from totals |

---

## 9. Shapefile fields

`W10/shp/W10_plot_loads.shp` — 64,071 polygons, EPSG:32640.

| Field | Meaning |
|---|---|
| `PLOT_ID` | MoH `OBJECTID`; negative for an unparceled building |
| `SRC` | `plot` / `unparceled` |
| `CLASS` | B built / P planned / A agricultural / U unparceled |
| `LU` | land use, romanised: res / com / gov / mosque / ind / agri / res+com / unknown / building |
| `CAT` | domestic / commercial / government / commercial+government / mixed / agricultural / industrial / none |
| `N_DOM`, `N_ND`, `N_GOV` | premises at saturation, by category |
| `N_PROP` | total premises — **a peaking-factor input** (Merrimack is mandatory above 100) |
| `POP` | `N_DOM × 5.32` |
| `Q_DOM_M3D`, `Q_ND_M3D`, `Q_GOV_M3D` | the three streams |
| `Q_AVG_M3D`, `Q_AVG_LS` | saturation Qadf — **the peaking-factor input**; PF is applied to the ACCUMULATED value, never to one plot |
| `AREA_M2`, `Q_L_M2D` | parcel area and load intensity |
| `BASIS` | counted / rate / counted+rate / none |
| `SANITY` | high / very_high / low_mega_parcel / micro_parcel / empty |
| `ZERO_WHY` | why a record carries no load |
| `IN_BND` | 1 inside the project boundary |

---

## 10. On reusing `W8/py/sewnet/stages/loads.py`

**It does not generalise, and it was not reused for the allocation.** That stage predates the
30 August lock. It multiplies every counted property by the blended `WWG_LCD = 171.3` l/c/d,
which is the **area average** — domestic plus the non-domestic and governmental uplift
smeared across the population. Under the locked basis a residential plot runs at 139.4 l/c/d
and the uplift is concentrated on the plots that generate it. It also carries `OCCUPANCY =
5.0` (superseded by 5.32) and falls back to 1.0 property on a plot with no meter.

Its farm rule, its no-silent-drops discipline and its reporting shape are all carried over,
and its **assignment and accumulation** halves — nearest-chamber assignment with reported
distances, topological accumulation, Merrimack and Peltier on the accumulated flow,
infiltration per km of upstream network — are unchanged and are what the solver will use on
top of this layer. Only the per-plot allocation is rebuilt.

---

## 11. Re-running

```
python W10/py/p1_loads.py
```

Reads `MoH_Plots_class_v4.shp`, `ELE_accounts.shp`, `Unparceled_Buildings.shp` and the
project boundary; writes the shapefile, the summary CSV and the checks CSV. Every value that
the clean data will change is a field on the frozen `LoadBasis` dataclass or an entry in the
`TARIFF_CAT` / `LU_*` crosswalks at the top of the file. `LoadBasis.ASSUMPTIONS` prints the
full register, and `sensitivity()` re-runs the whole allocation under alternative values in
one call.
