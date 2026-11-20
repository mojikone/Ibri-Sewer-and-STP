---
name: nws-basis-change-nov-2026
description: "Nov 2026 NWS/team decisions replace the W14 load basis and the S1-S7 options; adopted with the final design and reports R9-R12 (2026-11-18/19) - 3-method average population, occupancy 4.8, four STP scenarios, final design years 2051/2056/2061"
metadata:
  node_type: memory
  type: project
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-16T12:44:52.956Z
---

On 2026-11-08, after the NWS progress meeting of 2026-11-02 (MOM-5), the team's senior hydraulic engineer (Mehrdad Hadizadeh) issued a new wastewater basis: `New Calculation MH.xlsx` and `WW Generation - Network Scenarios.xlsx`, on the server under `06-WORKING\04-Hydraulic\7- Demand`. Population is the mean of three series (NCSI, domestic meters x 4.8, APSR master plan), at 2.11 %/yr beyond the forecasts and with no cap. The rate is 171 L/c/d. Infiltration at 720 L/km/d is already inside the settlement totals. Design years are 2056/2061/2066/2071, with a self-cleansing check at 2031. Three STP sites are kept: STP-1 (= O1), STP-2 (= O16) and STP-5 (= O4). That gives four scenarios: SC1 = STP-1, SC2 = STP-2, SC3 = STP-1+5 and SC4 = STP-2+5 (new), so 16 designs.

The engineer replied the same day:
- loads go on the new MoHUP plots, with growth spread equally over the future plots;
- no overflow;
- only pipes larger than DN200 are checked at 0.75 m/s;
- tractive force is dropped and pipes are laid at the Table 11 gradients.

No written confirmation of that reply had arrived by 2026-11-16. **Adopted since:** the final design (2026-11-18, design years 2051/2056/2061, [[w18-final-design-brief]]) and reports R9–R12 are on this basis, and the team restructured Chapter 6 on it in their report-structure email. A formal NWS confirmation is not on record. The team's report is `Ibri_Concept_Design_Report_R8-MH.docx` (server `04-DOCUMENTS\06-Design Reports\2. Concept\Concept Design Report_R0\temp`), which the team restructured from our R7 (change log `Validation Comments.docx`, same folder). Its chapter 4 is new; the rest was still on the R7 basis on 2026-11-16.

**The engineer's rulings of 2026-11-16:**
- **Growth cap:** each settlement grows only until its empty plots are full, with no overflow. Ibri is full in 2064 on the team's capacity table (146,116 people) and stays flat after that, so the team's 2066 and 2071 scenario flows are about 1,480 and 4,400 m³/d too high.
- **Plots:** the new MoHUP plots were too messy to use, so the plots stay the W14 `PLOTS_load` layer. The team's MoHUP counts are already that layer.
- **Design-year search:** design for 2056 and check the 2031 flow, where every pipe larger than DN200 must reach 0.75 m/s. If it passes, design for 2061 and check again, then 2066 and 2071; if 2056 fails, step back to 2051. Whether a tolerance is acceptable (for example 95 % passing) is still open.
- **Check flow:** the analysis uses the wastewater generated in 2031.
- **STP-5:** stays on its site (read from his answer "same").
- **Load placement:** commercial and government loads go on their own existing plots, as in W14. Future plots take the growth equally.

**Evidence that the design-year rule is hard to meet:** in the W17 S1 run at 2070, only 37 % of the pipes larger than DN200 reach 0.75 m/s even at their own design flow. At the 2030 flow it is 5.9 % (source: `D:\VBOX\bridge\out\scen\S1\conduits_S1-*.csv`).

**Why:** this replaces [[load-basis-locked-tier-a-volume]], [[concept-saturation-population-and-load]] and [[design-flows-handoff]]. On 2026-11-16 the engineer asked that the team's report structure, ideas and level of detail be kept, because reviewing it cost the team a lot of time.

**How to apply:** where the flow goes on the plots is settled in [[w18-growth-plot-rule]]. Where a design takes its flows: [[design-flows-handoff]]. Do not reuse the W14 flows or the S1-S7 ranking for new work. Do the work in a new W folder, and edit R8-MH rather than rebuilding our own report.
