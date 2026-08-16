# A7 — Data required to make the load calculation defensible

Prepared 2026-08-16. Supersedes nothing; feeds the report's data-request register.
All figures below trace to `_BRAIN/02_DESIGN_CRITERIA.md` (PAM-GUD-201 = `G1-p##`),
the client workbook `Ibri Sewer Demand R0 2026 08 03.xlsx`, or W3 analyses A1–A6.

---

## 1. The parameter that actually matters is a product, not the occupancy rate

PAM-GUD-201 §7 (G1-p58) defines:

```
Population = plots × (average properties per plot) × (occupancy rate)
```

Requesting the occupancy rate alone leaves the product undetermined. Empirically,
from the NCSI settlement populations (2025) divided by the plots classified as
built in W3 A5b/A6:

| Basis | Plots | Persons per built plot |
|---|---|---|
| Built cadastral plots only | 17,139 | **6.96** |
| Built plots + 2,799 unparceled buildings (A5a) | 19,938 | **5.98** |

So the **product is 6.0–7.0 persons per built plot**, which is a measured quantity,
not an assumption. Against it:

| If occupancy rate is | then properties per plot must be |
|---|---|
| 4.9 | 1.22 – 1.42 |
| 6.0 | 1.00 – 1.16 |

An occupancy rate of 4.9 is therefore only consistent with the observed population
if roughly 1.2–1.4 dwellings sit on each built plot. **Adopting 4.9 with 1 property
per plot would under-predict the load by about 18 %** and contradicts the measured
population. The two parameters must be received together.

### Consequence if occupancy is 4.9

W2's ultimate figures were built on OR 6.0 and 1 property/plot. Rescaling the same
pop-basis plot count (46,633):

| OR | Saturation population | NCSI curve reaches it in | Ultimate Qadf | with +10 % STP margin |
|---|---|---|---|---|
| 4.9 | 228,501 | **2054** | ~40,600 m³/d | ~44,600 m³/d |
| 5.5 | 256,481 | 2059 | ~45,600 m³/d | ~50,100 m³/d |
| 6.0 (W2 basis) | 279,798 | 2062 | ~49,700 m³/d | ~54,700 m³/d |

The load reduction is not the important part. The important part is that at OR 4.9
the project area **runs out of developable land in 2054 — inside the design horizon**,
so the 2055 model year becomes a saturation case rather than a growth case. That
changes the phasing argument, not just the numbers.

---

## 2. Data request list (ranked by effect on the load calculation)

| # | Item | Source | Why it is needed |
|---|---|---|---|
| 1 | **Existing Ibri STP inflow records** — daily/monthly inlet flow and load (BOD, COD, TSS, NH₄) for 3 years, plus tanker delivery logs (loads/day, volume/load, origin) | NWS operations | The only way to *calibrate* the whole chain rather than assume it. Measured inflow ÷ served population back-calculates the effective l/c/d, the return rate and the infiltration allowance in one step, and settles the occupancy debate empirically. Currently absent from every dataset received. |
| 2 | **NCSI housing units per settlement** (not wilayat) + average properties per plot, same vintage as the population series | NCSI via NWS | Closes `GAP-5`. Requesting occupancy without housing-unit counts per settlement leaves the product in §1 open. |
| 3 | **Final MoHUP plots layer** with: complete coverage (2,799 buildings currently sit on no plot — A5a), populated land-use for all plots (**39,838 of 61,272 are blank today**), plot status existing/approved/future, number of properties or dwelling units per plot, and plot release/subdivision programme | MoHUP | Drives the population-from-plots chain, the spatial load allocation to manholes, and the land ceiling. Today 65 % of plots carry no land-use attribute at all. |
| 4 | **Administrative assignment of plots outside the settlement boundaries** — 10,315 of 61,272 plots (17 %) fall outside all 25 NCSI settlement polygons | MoHUP / NCSI | Currently these plots cannot be assigned population, so their load is either lost or double-counted. Includes the future plots straddling the wilayat limit. |
| 5 | **Water billing and consumption records** (3 yr) with active account counts by category — domestic, non-domestic, governmental — per settlement, plus electricity account counts for sub-settlement pro-rata (G1-p58) | NWS | Validates the 164 l/c/d Adh Dhahirah rate and the +22 % / +14 % ratios against Ibri's actual consumption, and gives the spatial weighting inside settlements. |
| 6 | **BLOCKING — Table 12 inputs**: gross floor area (commercial, office, mosque, restaurant), pupils + staff per school, beds + staff for the hospital, employees per industrial unit, incl. AL TAYYEB IND. estate | MoHUP / NWS / Ministries of Health & Education | GUD-201 §7.3.2–7.3.3 **mandate** the Table 12 land-use method wherever land use exists; the 22 % / 14 % ratios are only the fallback (see §3). Without these the mandated method cannot be run and NWS must formally accept the fallback. |
| 7 | **Existing network as-builts** (F2 served area, F3 design-stage areas), pipe sizes, invert levels, condition/CCTV | NWS | Determines which population is already connected, which infiltration class applies (existing inland 10 % vs new 720 L/d/km), and what can be reused. |
| 8 | **Saturation / ultimate definition** — MoHUP land bank and future development plan | MoHUP / NWS | The R0 workbook compounds at ~2.2–2.4 %/yr to 2100 (691,264 persons) and **never saturates**; it contains no ultimate case. The TOR asks for one. |
| 9 | **Confirmation of model start year** and the 2030 / 2055 / ultimate horizons | NWS | Required before any phasing arithmetic is fixed. |

---

## 3. Method — water demand first, then the sewage load

Yes, demand comes first, and the method is PAM-GUD-201 §7, not GUD-202. GUD-202 covers
water and TSE *network* design (velocities, head loss, materials, pressures — `_BRAIN/02`
§12b); it does not derive per-capita demand.

### 3.1 The 22% / 14% ratios are a fallback, not the method

Table 11 (G1-p60) names these columns "**Distributed** Non-Domestic Ratio" and
"**Distributed** Governmental Ratio". They are the governorate's actual 2021–23
non-domestic and governmental volumes divided by its population — a top-down aggregate.
They are not a demand that each person carries.

The guideline is explicit about what to do instead:

- §7.3.2 (G1-p60): if the project provides detailed land use allocation, non-domestic
  consumption **shall** be calculated using Table 12.
- §7.3.3 (G1-p61): governmental consumption is then calculated for the project
  specifically **and not as a ratio of domestic consumption**.

So Table 12 is the method. The ratios apply only while the Table 12 inputs are missing,
and the report must say so.

**Two traps:**

1. Use Table 12 **or** the ratios — never both. Applying Table 12 rates to commercial
   plots on top of the +22% / +14% uplift counts the same water twice.
2. Table 12 is keyed to **floor area, pupils, beds and employees — never plot area**.
   Substituting cadastral plot area is wrong by an order of magnitude: 121.2 ha of mosque
   plots × 185 l/m²/d = 224,143 m³/d, about four times the whole ultimate STP flow.

### 3.2 What we can do before the data arrives

Keep the ratio-derived total (it is calibrated against real water balance data), but stop
spreading it per capita. Apply 164 l/c/d to the residential population, then put the
non-domestic + governmental volume on the non-residential plots in proportion to their
area. Total preserved, load lands where the land use is.
Implemented in [`py/a7_load_alloc.py`](../py/a7_load_alloc.py) → [`A7_load_alloc.csv`](A7_load_alloc.csv).

Run over the W2 zones, holding every other parameter fixed so only the allocation changes:

| | Result |
|---|---|
| Project Qadf | 53,339 m³/d — unchanged, as intended |
| Zone-level shift | **−16.8 % to +127.2 %** |
| Zones down / up | 21 down, 13 up |
| Zone 1 (Ibri core, 97.2 ha non-residential) | **+12.6 %** |
| Zone 8 (25,374 people, only 10.9 ha non-residential) | **−14.5 %** |

This is why the correction matters: the STP total does not move, but the branches do.
A residential-only branch drops from the area-average 171.3 l/c/d to **164 × 0.85 =
139.4 l/c/d**, about 19 % lower, because the 54 % return rate travels with the
non-domestic volume when it moves.

Land use in the cadastre today, for reference:

| Land use | Plots | Area (ha) | % of area |
|---|---|---|---|
| (blank) | 39,838 | 7,132.7 | 52.3 |
| زراعى agricultural | 3,336 | 3,870.3 | 28.4 |
| سكني residential | 13,445 | 1,168.1 | 8.6 |
| حكومي governmental | 2,502 | 1,134.9 | 8.3 |
| تجاري + سكني/تجاري | 1,628 | 198.5 | 1.5 |
| مسجد mosque | 465 | 121.2 | 0.9 |
| صناعي industrial | 55 | 17.7 | 0.1 |

Sense check on whether the 22 % is even the right size: it implies 4,302 m³/d of
non-domestic water, which at Table 12's 12.2 l/m²/d needs 35.3 ha of commercial floor
area. The cadastre has 198.5 ha of commercial and mixed plots, so a floor-area ratio
around 18 % — plausible. The ratio is not obviously inflated. Note also that Ibri is the
wilayat capital and holds the hospital and government offices, so once Table 12 is applied
the IBRI zones will most likely go **up**, not down, while the small settlements come
down. It is a redistribution, not a saving.

### 3.3 The chain itself

Taking the raw 164 l/c/d straight to Qadf skips two mandatory steps:

| Step | Value | Ref |
|---|---|---|
| Domestic consumption, Adh Dhahirah | 164 l/c/d | G1-p60 |
| Non-domestic add-on | +22 % of domestic | G1-p60 |
| Governmental add-on | +14 % of domestic | G1-p60 |
| Return rate — domestic & tanker | 85 % | G1-p71 Tab 19 |
| Return rate — non-domestic & governmental | 54 % | G1-p71 Tab 19 |

Effective wastewater generation:

```
164 × 0.85  +  164 × 0.22 × 0.54  +  164 × 0.14 × 0.54
= 139.4     +  19.5              +  12.4                =  171.3 l/c/d
```

Qadf = population × 171.3 l/c/d, **then** add infiltration, **then** apply the peaking
factor (Peltier PfWW = 1.5 + 1/√Qm, capped at 5.0, G1-p71–72) to obtain Qpdf and the
peak-hour flow, and **then** the +10 % STP design margin (G1-p73).

Using the raw 164 l/c/d as the sewage rate happens to land within ~4.5 % of the correct
171.3, but it is not traceable to the guideline and it applies the wrong return rate to
the non-domestic share — which is exactly where the industrial and commercial loads sit.

**Open conflict to settle with NWS:** the R0 workbook applies infiltration as **10 % of
wastewater flow**, whereas GUD-201 specifies **720 L/d per km for new networks** and
reserves the 10 % figure for *existing* inland networks (G1-p72). For a 194 km network
these give materially different trunk sizes. The workbook also adds a **+20 % weekly
peak** that does not appear anywhere in the GUD-201 peaking chain.

---

## 4. Assumptions that remain, and how they scale

| Assumption | Current value | Scaling |
|---|---|---|
| Occupancy rate `[GAP-5]` | 6.0 (W2/W3 basis) — challenged, see §1 | Qadf and land ceiling scale linearly |
| Properties per plot `[GAP-5]` | 1.0 | Qadf and land ceiling scale linearly |
| Built/planned plot classification | imagery classifier, 95.9 % accuracy (A5b) | affects the built-plot denominator in §1 |
| Settlement boundaries | NCSI polygons from `Final_Boundary_IBRI.kmz`; five flagged unreliable in A2 (TANAM, SATWAH, AL MAKHTIBYAH, USAYBUQ, ASH SHIAB) | affects plot-to-settlement allocation |
