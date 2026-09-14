# Decisions and clarifications required from NWS

**Project** T/2719110/2025 — Ibri STP, Sewer & TE Networks
**Purpose** Every item below either blocks the Concept Design Report or would make it wrong if left unresolved. The Inception Report R0 promised a data-gap register and a coordination and approval register (R0 p28 §8, p29 §10) and populated neither; this is that register.

Priority: **1** blocks the report · **2** changes report content · **3** clarification.

---

## Part 1 — Decisions that block the report

| # | Item | Position | Why it blocks |
|---|---|---|---|
| D-01 | **Design horizon** | R0 p18 states planning extends to **2100, "as instructed by NWS"**. Our working basis is start / 2030 / 2055 / ultimate saturated. The TOR (p51) says completion + 25 years or ultimate saturated flow | Population, flows, phasing and life cycle cost all key off this. The two bases give materially different answers |
| D-02 | **Governing programme** | Kickoff deck: Concept 15 Aug – 13 Oct 2026. R0 p29–31: Concept 2 Aug – 30 Sep 2026. Tender p147/p177: 60 days plus 21-day review | 15–20 % of the design fee and a 1 %/week delay charge turn on the submission date |
| D-03 | **Approved project boundary** | The R0 package contains two: `Project_Boundary.kmz` ≈439 km² (21 Jul) and `Final_Boundary_IBRI.kmz` ≈520 km² (3 Aug). The survey is priced at "approximately 450 km²" (R0 §16.2) | Catchments, plot counts and survey scope cannot be fixed. An 18 % discrepancy against a priced scope |
| D-04 | **Figures 1, 2 and 3 as georeferenced data** | Supplied as raster PDFs with no coordinates. Figure 3 defines the concept boundary; Figure 2 defines the as-built and GIS boundary | We cannot demonstrate that our study area matches the boundaries we are contracted to |
| D-05 | **Modelling software** | Tender p123 requires proficiency in **MIKE URBAN**. The TOR (p56, p57, p62, p65, p73) requires **SewerGEMS and WaterGEMS**. R0 p25 commits us to SewerGEMS and WaterGEMS | The model is a deliverable; we cannot build it twice |

---

## Part 2 — Corrections to figures already issued to the client

| # | Item | Issued position | Our position |
|---|---|---|---|
| D-06 | **Double peaking in the R0 flow series** | R0 applies a **+20 % weekly peak factor on top of Peltier**. GUD-201 §7.4.2 gives Merrimack **or** Peltier; the +20 % is a water-side peak-day concept (G1-p62) | Every figure in R0 Table 3 is inflated. Requires reissue or a stated correction |
| D-07 | **2100 flow of 156,627 m³/d** | R0 Table 3 p22 | Our ultimate is ≈49,700 m³/d. Our 2055 position agrees with R0 almost exactly; the divergence is entirely post-2060 and follows from D-01 and D-08 |
| D-08 | **Population beyond ~2070 exceeds available land** | R0 p21 gives 691,264 by 2100, Ibri town 398,339 | Boundary saturation is ≈326,000 around 2062–2070. R0's NCSI basis stops at 2040, so 2050–2100 is sixty years of linear extrapolation against a guideline advising no more than ten (G1-p58) |
| D-09 | **Existing STP capacity** | R0 p15/p17: 1,800 + 500 package = **2,300 m³/d**; inflow 1,100 network + 1,200 tanker; "little or no spare capacity" — all from a site visit, not records | NWS's own GIS records **1,800 m³/d**. This figure is the denominator of the whole phasing argument and must be verified from operational data |
| D-10 | **Infiltration basis** | R0 adopts 10 % of wastewater flow | GUD-201 requires **720 L/d/km** for new networks. Different basis entirely |
| D-11 | **TSE system loss** | Not applied in R0 | GUD-201 p76 requires a **10 % loss on produced TSE**. Overstates deliverable TSE by about 10 % |
| D-12 | **Project Manager of record** | Kickoff deck names Mehrdad Hadi Zadeh over an 8-person chart. R0 p34 names Hossein Forouzan over 27 | Two different people have been presented to the client as Project Manager |

---

## Part 3 — Method rulings needed

| # | Item | Question |
|---|---|---|
| D-13 | **Tier A versus Tier B demand** | The electricity dataset carries no land use, no floor area and no consumption — only a tariff name. Table 12 is priced in pupils, beds, employees and floor area, none of which were supplied. We propose Tier A ratios for volume with land use setting placement, and adoption of Table 12 when quantities arrive. Confirm acceptable |
| D-14 | **Occupancy rate basis** | G201-p58 defines OR from **NCSI housing units**, which are not published at settlement level. We derive OR = 5.32 from settlement population ÷ domestic electricity accounts. Confirm acceptable, and release NCSI housing units if held |
| D-15 | **Spatial allocation of non-domestic and governmental demand** | G201-p59 wording distributes it across population; we concentrate it on non-residential plots. Project total is unchanged; zone loads shift −16.8 % to +127.2 % |
| D-16 | **"Saturation" has two meanings in play** | R0 p19 defines it as a hydraulic capacity trigger. Our doctrine defines it as land exhaustion. Both are in client-facing documents. Propose naming them separately |
| D-17 | **EIA timing** | G201 Table 2 places EIA scoping at Preliminary and permitting at Detailed; G201 §6.1.4.3 p44 says the **full EIA** must be done in concept/preliminary. The cost and programme difference is large |
| D-18 | **Value Engineering timing** | G201 Table 2 marks VE as Detailed only; Table 27 p93 requires formal VE at **concept** for an STP above OMR 2 M. Table 27 is the more specific clause |
| D-19 | **Tanker catchment radius** | R0 uses 25 km as a tanker catchment. G201 §8.1 p80 uses 25 km to define **Remote Areas**, not tanker catchment; the observed catchment is nearer 150 km |
| D-20 | **CFD modelling** | Mandatory for large plants *"unless clearly stated in the TOR"* (G203-p66). The TOR is silent. Confirm whether it is required at concept |

---

## Part 4 — Documents we do not hold and need

| # | Document | Why |
|---|---|---|
| D-21 | **NWS Integrated Master Plan** | Requested and not provided. It is the only independent check on population, LPCD and the demand chain, and the TOR's stated objective is to verify the RG Master Plan |
| D-22 | **Our own Technical Proposal volume** | Not in the project record. It contains the methodology, named software, programme and QA we are contractually bound to |
| D-23 | **Appendix to Form of Bid** | Referenced by the signed Form of Bid; holds the contractual concept deadline |
| D-24 | **Pre-bid query replies 01–09 and Circular 02-EOT 01** | Acknowledged in our signed bid, therefore contractually incorporated. Any methodology clarification NWS gave in them binds us |
| D-25 | **Appendix A, Oman Standard Form of Agreement 1987** | Tender p191 relies on it to define the design stages; not reproduced in the tender |
| D-26 | **Kickoff minutes** | None exist in our record. Nothing can currently be described as agreed at kickoff |
| D-27 | **Adh Dhahirah consumption and customer counts** | R0 publishes LPCD 163.5 but not the inputs, so the guideline occupancy check cannot be run directly |
| D-28 | **Ibri STP tanker delivery records** | Needed for tankered septage load and influent strength, including out-of-boundary camps reported verbally at the site visit |
| D-29 | **Utility records** — electricity cables, telecom, gas | We hold electricity **meter points**, not cable routes. Water mains in the NWS data total 3.5 km, which cannot serve the city |
| D-30 | **Table 12 quantities** — pupils, beds, staff, floor areas | The trigger that would move the demand calculation from Tier A to Tier B |

---

## Part 5 — Tender document defects to raise formally

| # | Item |
|---|---|
| D-31 | **NWS review period**: 21 days (tender p147, p150, p177) versus 30 days (ITB p15) |
| D-32 | **Commencement**: within 7 days (Form of Bid p145) versus 15 days (p147, p177) |
| D-33 | **Standards edition**: "current at the time of Tender" (p12) versus "applicable on the commencement effective date" (p190) |
| D-34 | **Glossary truncated at "N"** (p204). STP, TE, TSE and SCADA have no definitions, although Section 03 p50 directs the reader there for the TE system definition, and mis-cites it as Section 10 when it is Section 9 |
| D-35 | **Alternative bids prohibited** (p33) yet a minimum of three options per system is required. Confirm the options are internal design options within the base scope |
| D-36 | **"Provisions for future Sea outfall"** appears in the binding glossary definition of STP System (p202). Ibri is roughly 200 km inland. Confirm whether this applies |
| D-37 | **TOR cites "item 2.1, Wastewater Design Manual Section 05"**, which does not exist in PAM-GUD-203 Rev.01. The equivalent is G203 §10.1, p63–64 |
| D-38 | **No environmental specialist** appears among the eight Design Key Positions in the tender, although obtaining the EIA and NOCs is a priced concept deliverable. R0 p34 names one; the tender staffing schedule does not |
