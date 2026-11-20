# Loads: from population to plots to manholes

Reference implementation: `scripts/py/nws_loads.py` (Ibri W18, NWS basis of November 2026). Its audit is
`scripts/py/audit_w18.py`.

## 1. The volume per settlement

- **Population per settlement and year:** the series the client or the team adopts. Ibri used the mean of three series
  (NCSI census forecast, domestic meters × 4.8, the APSR master plan), from sheet "Average" of the team's workbook.
- **Per-capita rate:** the client's figure. Ibri used 171.03 L/person/day, from the team's sheet "Base Demand". Use the
  guideline's method (PAM-GUD-201 §7) only where the client has not set one, and say which.
- **Capacity:** a settlement stops growing once its growth plots are full.
  - Capacity = base-year population + growth plots × properties per plot × occupancy.
  - Ibri: 2026 population + growth plots × the team's properties per plot × 4.8. Ibri itself is full in 2063, at 144,537
    people.
  - **No overflow** to other settlements unless the client agrees; Ibri's was refused (engineer, 2026-11-16).
  - The capacity only sets the year growth stops. It does not change the adopted population before that year.

## 2. Placement on the plots

- **Existing plots** keep the settlement's base-year flow in the pattern of their metered flow: homes, shops and government
  plots each carry their own load. They take no growth.
- **Growth** (everything above the base year) is shared **equally** among the settlement's growth plots. Which plots count is
  the engineer's decision, tuned on check maps. Ibri's rule (2026-11-17):
  - a future plot, inside its own settlement's boundary;
  - 200–3,000 m²;
  - home-shaped: compact ≥ 0.6 and aspect ≤ 3, so no strips or slivers;
  - any zoning, because the planning layer's proposed uses were not trusted, except agricultural (zoned so, or a grove
    on the satellite test), heritage (MoHUP "Tourism") and industrial;
  - not an estate.
  - That gave 43,230 plots.
  - Rejected on the way: area caps of 1,000 and 2,000 m², residential zoning only, a 10 m width cut (it caught real row
    plots), and putting the commercial share on shop plots (about 8.7 m³/d per plot, implausible).
- **A plot outside its settlement's boundary** takes no flow.
- **Special loads are additive:** the industrial estates (Ibri: 6,300 workers × 93 L/d × 0.54 = 316.4 m³/d) go on their own
  plots, outside the per-capita volume.
- **No infiltration in the plot loads** when the model adds it on the conduits (720 L/day per km, G201 p72 §7.4.3).

## 3. Plots to manholes

- Each plot loads the manhole the model's plot layer assigns it (Ibri: field `HMINNODE`).
- A plot with no manhole (Ibri: 6,499 of them, `HMINNODE` 0) goes to the nearest manhole that has a load row. Loading a
  manhole that has no load row made SewerGEMS jobs fail (Ibri jobs 060–066).
- Outputs, every five years:
  - `plot_loads.csv`, per plot;
  - `manhole_loads.csv`, per manhole (the model's input);
  - `settlement_flows.csv` and a `check.md` with the totals.

## 4. Flow the network does not carry

- **Two categories** (Ibri, engineer 2026-11-16):
  - **inactive network:** the plot's manhole lies in the part of the network switched off. At Ibri that meant planted areas,
    where terrain levels are unreliable under trees until the survey, and small outlying catchments proposed for on-site
    treatment;
  - **too far:** the plot's edge is more than 200 m from the nearest active sewer.
- The flow stays in the settlement totals and is reported separately with a map. Ibri: 693 m³/d in 2031 and 1,128 m³/d in
  2056.
- The plant inflow leaves it out. It is connected at the preliminary design, within the plant's 10 % margin. Say so in the
  executive summary, the network chapter, the plant chapter and the risk register.

## 5. Check it independently

- Write an audit that recomputes every total from the raw sources **without importing the code under test** (Ibri: 44
  checks). Run it after any change to the loads.
  - Why: a check that imports the function it checks repeats the function's mistakes.
- Make check maps for the engineer: plot flows per settlement on A3, and which plots take growth and why the others do not.
  The growth rule above was settled on those maps, plot by plot.
- Produce a plot layer carrying, per year: meters, land use, status, properties, residents and flow. Every later map and
  table reads it.
