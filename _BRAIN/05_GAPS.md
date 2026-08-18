# GAPS & OPEN QUESTIONS
Rule: items here are the ONLY permitted uses of assumptions — and each assumption must be tagged in outputs as `[GAP-n]` until closed.

| ID | Gap | Needed from | Interim handling |
|---|---|---|---|
| GAP-1 | ~~Per-capita rate~~ **CLOSED 2026-07-20**: 164 l/c/d Adh Dhahirah (GUD-201 Tab 11, G1-p60) | — | validate w/ NWS at kickoff |
| GAP-2 | ~~Infiltration~~ **CLOSED**: new networks 720 L/d/km; existing inland 10% (G1-p72) | — | — |
| GAP-3 | ~~Peaking factor~~ **CLOSED**: Peltier 1.5+1/√Qm (IMP2024) or Merrimack; PF ≤ 5 (G1-p71–72) | — | — |
| GAP-4 | `Data/sample report` folder is EMPTY → no styling reference | User to drop the sample report file | Draft report content in Word (docx skill) with neutral styling; restyle when sample arrives |
| GAP-5 | Occupancy rate + properties/plot — **PARTLY CLOSED 2026-08-14**: NCSI wilayat population series now in `Ibri Sewer Demand R0 2026 08 03.xlsx` (Ibri 183,564 @2024, settlement disaggregation; **population only — NO housing-unit counts**, so OR itself still open). Remaining: NCSI housing units → OR per settlement, properties/plot subdivision check, electricity account counts for sub-settlement pro-rata (G1-p58) | R0 workbook + NWS confirmation | Use R0 settlement populations directly; OR = 6.0 fallback only where R0 has no coverage `[GAP-5]` |
| GAP-6 | Existing sewer network extents (F2) & design-stage areas (F3) are scanned PDFs | Read/georef when zoning is finalised | Flag zones overlapping existing-served areas as "verify vs F2" |
| GAP-7 | Ibri STP existing capacity/inlet invert | NWS data collection | Use ground level −(2–4 m) as screening inlet range, tagged |
| GAP-9 | **MoHUP cadastre incomplete** (found 2026-08-15): 2,799 buildings with no plot polygon (`W3/shp/Unparceled_Buildings.shp`); 65 % of plots have empty LANDUSE (imagery-characterized in `MoH_Plots_class_v4.shp` — screening only) | MoHUP via NWS: complete cadastre + building/completion records | Use v4 CLASS layer for design; unparceled buildings carry demand at their location |
| GAP-10 | Settlement boundary polygons wrong/missing: TANAM, SATWAH, AL MAKHTIBYAH, BAT polygons miss their plots; 24 of 50 R0 settlements have no polygon in kmz | NWS/R0 authors: corrected boundaries (or agree to derive zones from plot clusters) | A1/A2 exclude bad-boundary zones from ceilings/spill reception |
| GAP-11 | NWS confirmations from T01/W3: infiltration basis (720 L/d/km vs R0 10 %), peaking formula per element (Peltier/Merrimack), tanker catchment (25 km assumed vs 150 km observed), model start year | NWS at kickoff | T01 §15 register; design basis = guideline values, R0 values as sensitivity |
| GAP-8 | STP-vs-SLS decision criteria not explicit in GUD-203 | Composed from GUD-203 fragments (p33 max cover→PS, p38 PS siting, p63 Tab 27 topography-to-limit-pumping, p64 footprints, p65 categories) + cited literature (Metcalf&Eddy, US EPA) — must stay clearly referenced, engineering-judgment items labelled | Criteria note in report §STP/SLS |

| GAP-9 | **Design tractive tension τ not defined in GUD-203.** §4.2.2 gives Smin = K·τ^1.23·Q^−0.461 but no numeric τ anywhere. The simplified form previously used in `_BRAIN/02` implied τ = 1 Pa without saying so | NWS Hydraulic Team | Adopt τ = 1 Pa (Mara et al. literature basis), tagged `[GAP-9]`, and confirm at kickoff. Min gradients in §2 Tab 11 are unaffected (they come from the 0.75 m/s method) |
| GAP-10 | **Tier-B design inputs missing** (audit 2026-08-17). GUD-201 §7.3.2/§7.3.3/§7.4.1 mandate Table 12 unit rates and BS EN 752 design flows "where detailed land use information is available" — Ibri qualifies, but the inputs (floor areas, pupils, beds, employees) do not exist yet | MoHUP / NWS / Ministries — data-request item 3 & 6 | Tier-A ratios (22 %/14 %) used as an explicitly labelled fallback; every deliverable must say so and name the missing data. NWS must formally accept the fallback |
| GAP-11 | **Non-network water sources not assessed.** GUD-201 §7.4 (G1-p70): the Designer *shall* assess private wells, private water providers and other non-network abstractions for their contribution to WW generation. Tab 13 shows Adh Dhahirah tanker water = **333 % of network domestic consumption** — the highest in Oman — so WW derived from network demand alone under-predicts | NWS + NCSI + field survey | Flag all pre-2026 flow figures as network-basis only; quantify once STP inflow records (data-request item 1) arrive |
| GAP-12 | **NCSI extrapolation limit exceeded.** G1-p58: not recommended to extrapolate >10 yr beyond the available forecast; the R0 series runs to 2100 | NCSI / NWS | Treat post-~2050 population as scenario, not data; defend 2055 and ultimate on land capacity (W3 A1/A2) rather than the extrapolated curve |

## Kickoff questions for client (carry into report annex)
1. Confirm per-capita, infiltration, peaking values (PAM-GUD-201 / IMP 2055).
2. Existing Ibri STP: capacity, headworks invert, spare capacity, condition; decommission-vs-integrate intent (scope demands old↔new STP integration).
3. F3 boundaries: which areas are redesign vs new design; existing-network As-built availability.
4. Status of MoHUP land bank for new STP / PS sites.
5. Model start year + confirmation of 2030/2055/ultimate horizons.
