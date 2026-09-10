# Inference register — land-use and load basis from electricity accounts

**Purpose.** The load calculation rests on the NAMA electricity account dataset. That
dataset carries no land-use attribute. Every land-use statement in the concept report
is therefore an inference drawn from the account tariff, and this register records each
one: what it claims, what it rests on, and what would overturn it.

**Rule.** No row here may be quoted in the report as a measured fact unless its Basis
column says *supplied*. Rows marked *derived* or *assumed* must be presented as such.

---

## 1. What the source actually contains

`IBRI ELE ACCOUNTS.kmz` — 33,970 points, EPSG:32640. Fields supplied by NAMA:

| Field | Content |
|---|---|
| `FID` | record number |
| `TARIFF` | billing tariff name — the only descriptive attribute |
| `X`, `Y`, `LONGITUDE`, `LATITUDE` | coordinates |
| `Gov` | "Dahira" on every record |
| `Wilaya` | **empty on all 33,970 records** |

There is no land use, no floor area, no occupancy, and **no consumption figure**. The
dataset can classify and locate an account; it cannot size one.

---

## 2. Inference register

| # | Inference | Basis | Rests on | Would be overturned by |
|---|---|---|---|---|
| I-1 | Tariff name indicates land use | **derived** | our mapping of 13 tariffs to 7 categories | NAMA supplying a land-use attribute |
| I-2 | "Primary Account Tariff" and "Primary (National Subsidy)" each represent one occupied dwelling | **assumed** | tariff nomenclature; consistent with GUD-201 Table 11, which computes LPCD from *"active Domestic Accounts"* (G1-p60) | account status data showing vacant or inactive meters |
| I-3 | "Additional Account Tariff" is a separate dwelling, not a second meter on one home | **derived** | 6,344 records = 28 % of domestic; counting primaries only under-predicts dwellings by ~19 % | premises-level meter records |
| I-4 | An agricultural meter is an irrigation pump and generates no wastewater | **derived** | on 172 of 319 agricultural plots NAMA bills a separate household tariff alongside the farm tariff — dwelling and pump are metered independently | site survey finding dwellings on farm-only meters |
| I-5 | An agricultural plot with no household tariff carries no dwelling | **assumed** | the billing pattern in I-4; excludes 147 plots ≈ 782 people ≈ 0.67 % of settlement population | GIS or survey evidence of occupied farm buildings |
| I-6 | CRT accounts cannot be classified by tariff | **supplied** | CRT is a consumption-threshold tariff, so a mall, factory, hotel or large government building all fall in it | plot-level land use for the 499 CRT points |
| I-7 | The industrial estate is not identifiable in the dataset | **derived** | one account carries the Industrial tariff; CRT clustering finds no industrial concentration — the largest CRT clusters are Ibri's commercial core | NAMA confirming how the estate is metered |
| I-8 | Occupancy rate = 5.32 people per domestic property | **derived** | 2024 settlement population ÷ domestic properties, both clipped to the same 25 settlements | NCSI housing-unit counts at settlement level |
| I-9 | The dataset covers ~64 % of Ibri wilayat | **derived** | settlements hold 63.4 % of wilayat population; meters represent 65.5 % of the properties implied at OR 5.32 — the two agree within 2.1 points | the GIS expert's completed plot coverage |
| I-10 | Tankered and non-network water generates wastewater | **supplied** | GUD-201 Table 19 gives tanker the same 85 % return rate as domestic; §7.4 names tanker and requires assessment of private wells and other non-network abstraction | — binding, not an inference |

---

## 3. Departures from GUD-201 to be declared

| Departure | Guideline position | What this project does | Why |
|---|---|---|---|
| Occupancy rate source | *"Occupancy Rate = Population / Housing Unit"*, both from NCSI (G1-p58) | population from NCSI, properties counted from electricity accounts | NCSI housing units are not published at settlement level, and the master plan holding NWS's own figures was requested and not provided |
| Non-domestic allocation | *"spatially distributed non-domestic consumption that are to be added to the domestic consumption"* (G1-p59) | the ratio volume is concentrated on non-residential plots rather than spread across population | a residential-only branch generates no commercial or government flow; the total is preserved and only the allocation moves |
| Tier selection | Table 12 *"shall"* be used where detailed land-use allocation exists (G1-p60 §7.3.2) | Tier A ratios retained for volume | Table 12 is priced in pupils, beds, employees and floor area; none were supplied, so the condition is unmet in substance |

Each departure requires NWS concurrence and is to be stated plainly in the report, not
buried in an appendix.

---

## 4. Outstanding data requests

| Item | Blocks | Status |
|---|---|---|
| NWS Integrated Master Plan | independent check of population, LPCD and demand chain | requested, not provided |
| Annual domestic consumption and customer counts for Adh Dhahirah | direct verification that our occupancy rate reproduces the published 163.5 l/c/d | not held; R0 publishes only the result |
| Table 12 quantities — pupils, beds, staff, employees, floor areas | upgrade from Tier A to Tier B | not supplied |
| Clean plot layer with digitised missing plots and land-use attribute | 9,081 unmatched accounts (26.7 %) | in preparation |
| How the industrial estate is metered | case-by-case costing required by G1-p59 | open |
| Ibri STP tanker delivery records | out-of-boundary septage load and influent strength | open |
| Local tanker share for Ibri | Table 13's 333 % is governorate-wide, not Ibri | open |

---

## 5. Accuracy is directional, not uniform

The same population figure cannot serve all three uses, because the safe direction
reverses between them:

| Use | Driven by | Dangerous direction |
|---|---|---|
| Pipe sizing | peak flow and load distribution | under-estimate — surcharging |
| STP capacity and staging | total average flow and its growth curve | under-estimate — plant too small |
| Self-cleansing and the early washing schedule | **minimum** flow in the opening years | **over-estimate** — pipes assumed to scour themselves while silting, and maintenance instructed to stop washing too soon |

The connection ratio (connected population ÷ total population, 0.51 in 2024 rising to
0.61 by 2028 in the R0 series) governs the third case and must not be omitted from it.
