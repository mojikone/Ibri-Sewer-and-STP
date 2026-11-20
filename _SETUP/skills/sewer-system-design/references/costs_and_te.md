# Treatment, treated effluent, station flows and costs

Reference: `scripts/py/final_financial.py`, `final_boq.py`, `te_sc4_network.py`, `final_station_flows.py`.

The rates below are those of the Ibri team's options cost estimate (October 2026), so they are a project's rates and not
guideline values. A new project takes its own team's or client's rates and keeps the method. Cost every design on its own
design year. Ibri costed all 12 designs: `case(sc, Y)` writes them to `financial.json["designs"]`, and the top-level keys
hold the adopted year.

## Treatment

- **Design capacity** = design-year average inflow with infiltration + 10 % (G201 p73 §7.4.5; G203 p65 Table 29).
- **Four equal modules per plant**, rounded up to 500 m³/d (250 below 5,000).
- **Phasing:**
  - the modules installed at opening cover the opening-year inflow + 10 %;
  - another module enters service in the first five-year step whose inflow + 10 % exceeds the installed capacity.
- **Ibri rates by design capacity, OMR per m³/d:**

  | Capacity up to | 1,000 | 5,000 | 10,000 | 20,000 | 50,000 | 100,000 |
  |---|---|---|---|---|---|---|
  | Rate | 1,000 | 900 | 800 | 700 | 600 | 500 |
  | Land, m² per m³/d | 8 | 6 | 4 | 3 | 2 | 1 |

  Power is 0.025 kW per m³/d.

## Network

- Quantities come from each case's named network and station products, priced at the project's rates. In the BOQ workbook
  every amount is a formula, so a rate can be changed in the sheet (`final_boq.py` → `network_cost.json`).
- Left out until the survey: house connections, crossings, excavation and backfill volumes, reinstatement.
- Station land: 5 m²/kW up to 10 kW, 3 m²/kW above (Ibri team sheet). The guideline minimum plot is p43 Table 21.

## Treated effluent

- **Supply:** production is 95 % of the plant inflow, with a 10 % network loss (G201 p73 §7.4.6). Size for the summer peak
  demand (G201 p76 §7.4.6.4, Table 23 seasonal factors).
- **Customers:** demands from the team's register (Ibri: 2030 and 2070, linear between). Each customer is supplied by the
  plant of the team's TE model.
- **Networks:** use the team's TE model per scenario where one exists, with its booster power (Ibri SC1–SC3: 750 / 850 / 497
  kW).
- **A scenario with no TE model** (Ibri SC4) is built from the others' networks by rule (`te_sc4_network.py`, rule in its
  docstring):
  - one plant's network as it stands;
  - the other plant's network cut to the shortest paths that reach its own customers;
  - booster power pro rata to the flow each plant supplies.
- **Boosters:** 5,000 OMR/kW and 3 m²/kW (Ibri).
- **Keep the team's raw TE data out of any public repository.**

## OPEX (the Ibri team's sheet)

- Maintenance and operation: 1 % a year of the capital in service.
- Power: installed kW × 8,760 h × 0.020 OMR/kWh × the year's flow as a share of the design flow.
- Land: 1 OMR/m² a month.
- Staff: (ROUNDUP(stations / 5) × 2 + 20 for one plant, 28 for two) × 2,500 OMR × 13.
- Chemicals: chlorine 8 g and NaHCO₃ 20 g per m³ of capacity at 0.3 OMR/kg, polymer at 1 OMR/kg, × the flow share.

## Prices

- Base year = opening (Ibri 2031).
- Capital and operating costs escalate at the team's inflation rate (Ibri 5 % a year).
- Present value at 5 % over 25 years (2031–2055), at constant prices.
- Assert any ranking the report states (cheapest in every design year, and so on) in the code that writes the table.

## People and flow at every station

`final_station_flows.py`, every five years from the base year to the last design year:
- **Own:** the catchment that drains by gravity to the station (its section):
  - the residents of the connected plots, by the manhole each plot loads;
  - their sewage, from `manhole_loads.csv`, which also carries shops, offices and estates;
  - the infiltration of the section's sewers.
  - The catchments are the same in every scenario.
- **Through:** the own catchment plus everything pumped into it, per scenario. A plant's inlet station carries the plant's
  whole flow.
