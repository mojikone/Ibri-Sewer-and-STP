# DESIGN CRITERIA — PAM-GUD-203 (201 pp) + PAM-GUD-201 (152 pp) + PAM-GUD-202 (177 pp)
Refs: `p##` = PAM-GUD-203; `G1-p##` = PAM-GUD-201; `G2-p##` = PAM-GUD-202 Water & TSE Design Guidelines v1.0 (added 2026-08-14, in `_STANDARDS/` + `Data/`). **Nothing here may be altered without re-reading the source.**

> ## ⚠ READ FIRST — the two-tier rule (§11.0)
> **PAM-GUD-201 §7 gives two methods for almost every demand and flow parameter.** Tier A (LPCD ratios 22 %/14 %, return rates 85 %/54 %) is for *"planning and forecasting purposes across broader service areas"*. Tier B — **mandatory "shall" wording wherever detailed land use exists** — is Table 12 unit rates for non-domestic/governmental demand and BS EN 752 for design flows. **Ibri is a project-specific design with detailed land use: Tier B governs, Tier A is a labelled fallback.** W1–W3 used Tier A throughout without saying so. Full rule and quotes in §11.0.
>
> **Rule for anyone editing this file:** a row that paraphrases the guideline **must carry the verbatim phrase** that makes the rule conditional or mandatory ("shall", "recommended", "Distributed", "in the absence of", "where detailed land use…"). The non-domestic error of 2026-08-16 happened in the gap between a table and a paraphrase of it. Rows marked ★ were verified against the source PDF page on 2026-08-17.
>
> **Audit provenance:** full row-by-row audit 2026-08-17 (13 agents over all three guidelines, 145 findings) — record and open items in [`W3/analysis/A9_criteria_audit.md`](../W3/analysis/A9_criteria_audit.md).

## 1. Hydraulic design — gravity sewers (§4.2, p24–28)
| Item | Value | Ref |
|---|---|---|
| Design formulas | Colebrook-White or Manning; licensed software approved by NWS (SewerGEMS per scope) | p24 |
| Colebrook-White ks | **1.5 mm** all pipe sizes/materials | p24, p28 |
| Kinematic viscosity | 15 °C → 1.141e-6 m²/s (conservative basic design) | p25 |
| Min self-cleansing velocity | **0.75 m/s at peak flow**, preferred 0.90 m/s | p26 |
| ★ Min tractive force method | **Mara/Sleigh/Taylor Smin = K · τ^1.23 · Q^−0.461** (τ = tractive tension in **Pa**; assumptions d/D = 0.2, n = 0.013); K = 2.33e-4 (Q m³/s) / 5.5e-3 (Q L/s). **Corrected 2026-08-17** — the file previously carried `Smin = K·Q^-0.46`, dropping the τ^1.23 term (the equation is an embedded image with no text layer, which is how it was miscopied). The simplified form is only valid at **τ = 1 Pa**. GUD-203 §4.2.2 gives **no numeric design τ** — the value must be selected and justified, or confirmed with NWS → `[GAP-9]`. *"Steeper gradient calculated based on self-cleansing velocity and minimum tractive force methodology shall be adopted as minimum pipe gradient."* Use tractive force at network heads where 0.75 m/s unattainable | p27 §4.2.2.1 |
| Max velocity | **3.0 m/s** at design depth of flow | p27 |
| d/D at peak flow | ≤ **0.65** for D ≤ 350 mm; ≤ **0.50** for D > 350 mm | p27 Tab 10 |
| Manning n (plastic/GRP) | 0.009–0.011 (PVC/GRP); PE 0.009–0.015; concrete cement-lined 0.012 | p23 Tab 8 |
| Early-phase low flows | Actual flow in early development phases is below design flow → **clogging risk at low velocity**; more frequent inspection/cleansing required in that period. Relevant to the 2030 → 2055 → ultimate phasing | p28 §4.2.6 |

## 2. Minimum gradients (§4.3.1, p29, Table 11 — Colebrook-White @ 0.75 m/s)
| DN (mm) | Smin (mm/m) | | DN (mm) | Smin (mm/m) |
|---|---|---|---|---|
| 200 | 5.00 | | 500 | 1.55 |
| 250 | 3.75 | | 600 | 1.25 |
| 315 | 2.70 | | 700 | 1.00 |
| 400 | 2.05 | | 800 | 0.85 |
| | | | **≥900** | **0.75** |
- No oversizing to get flatter slopes; uniform slope between manholes (p29).
- Max gradient: governed by v ≤ 3.0 m/s (p29).
- ★ **Construction tolerance**: *"The lines and level of any pipeline shall not deviate from that described in the contract by more than **20 mm** and combination of such deviation shall not create a **reverse gradient**"* (p29 §4.3.1). At DN ≥ 900 the minimum gradient is 0.75 mm/m, so 20 mm over a 120 m manhole spacing eats ~0.17 mm/m — **~22 % of the available fall**. Flat trunk profiles must carry margin for it.
- ★ **Tertiary slopes are separate and much steeper** (p18 Tab 5): property connection sewer min **3 %** / max 10 %; rider sewer min **1 %** / max 10 %; lateral sewer min **1 %** / max 10 %. Table 11 above applies to the secondary network — using its 0.5 % at DN200 for a *lateral* is a design trap.

## 3. Pipes (§4.1, p21–23; §5 p35)
| Item | Value | Ref |
|---|---|---|
| Min diameters | Property connection OD160; lateral OD200 (max length 45 m); main sewer OD200 min | p22 Tab 6 |
| Secondary network range | 200–400 mm typical (400 not mandatory ceiling) | p23 |
| Materials, main ≥350 | GRP, HDPE, lined RCC (open trench); GRP/HDPE (trenchless) | p22 |
| **Trunk main definition** | **D > 800 mm, length > 1,000 m without connections, upstream of STP/main PS** | p35 |
| Trunk material > 600 | GRP, lined RCC, profile-wall HDPE | p35 Tab 14 |

## 4. Depth / cover / corridors (§3.5 p19; §4.6 p32–33)
| Item | Value | Ref |
|---|---|---|
| Min cover (gravity sewer) | **1.3 m to crown**; 0.5 m if concrete-protected | p33 |
| Property connection cover | min 600 mm | p19 |
| **Max cover** | **~10–12 m**; beyond → manufacturer check; where excavation cost prohibitive → **incorporate pumping station** | p33 |
| Min horizontal clearance to other utilities | 3 m | p33 |
| Service corridor widths | DN200–500: 2.0 m; 600–900: 2.8 m; 1000–1200: 3.2 m; 1400–1700: 4.0 m; 1800: 4.1 m; 2000–2400: 4.4 m | p32 Tab 13/p35 Tab 15 |

## 5. Manholes (§4.4, p29–31)
| Item | Value | Ref |
|---|---|---|
| Max spacing | DN200–315: **100 m**; 350–900: **120 m**; 1000–1400: **150 m**; >1400: **200 m** (deviation needs NWS pre-approval) | p30 Tab 12 |
| Locations | grade/diameter change, junctions, end of laterals, regular spacing | p29 |
| Backdrop | required when invert drop > 600 mm; external; max height 2 m (beyond → vortex drop shaft); internal only if MH ≥ 1.5 m dia | p30 |
| Inlet angle | ≥ 90° to flow direction | p30 |
| **Prohibited locations** | **wadis & flood-prone/washout areas** (pipelines AND chambers) | p30 §4.4.1, p33 |

## 6. Wadi / crossings
| Item | Value | Ref |
|---|---|---|
| Pipelines+chambers in wadis | avoid — washout risk | p30, p33 |
| Force main cover at wadi crossing | **1.5 m to crown** (vs 1.3 normal) | p52 §8.2.4 |
| Twin pipelines for obstacle (highway/wadi) crossing | allowed w/ dedicated hydraulic justification (0.75 m/s in all modes, mechanically independent restraint) | p52 §8.2.3 |
| Inverted siphons | avoid; only where no other feasible means (scope TOR) | scope p12(60) |
| Trenchless as alternative at major crossings | subject NWS approval; settlement decisive | p21, p35 |
| TSE discharge to wadi | min Class A (MD 145/93); EA + APSR approval | p73 |
| STP flood criteria | 25 & 100-yr flood levels; STP fully operational during floods | p63 Tab 27(i) |

## 7. Pumping stations (§7, p38–49)
| Item | Value | Ref |
|---|---|---|
| Siting | hydraulics-driven; flooded suction preferred; force-main energy-economic study determines optimal location | p38 |
| Pumps | small PS: min 2 identical (duty/standby) each 100% design flow; peak flow achievable with any one unit out | p39 |
| Design life (non-structural) | *"non-structural mechanical installations"* **20 yr** (p38). ★ But Tab 17 assigns **pumps a 15-yr service rating** (p40) — use 15 yr for pump replacement in LCC, not 20 | p38; p40 Tab 17 |
| Stakeholder NOCs early (incl. Falaj crossings) | preliminary stage | p39 |
| ★ Siting — additional binding rules | PS site **approved in advance by NWS at concept/preliminary stage**; pump pedestal/building floor, transformers/substation and emergency generator **above maximum flood level**, floors min **300 mm above the 1:50-yr flood level**; surface/stormwater designed for **1:50 ARI**; sites **under electrical power lines avoided** | p38 §7.2 |
| ★ PS type classification | **Type 1 ≤100 l/s** (min 1 duty + 1 standby); **Type 2 >100–300 l/s** (2 duty + 1 standby); **Type 3 >300 l/s** (3 duty + 1 standby); pumps duty-rotate each cycle; station pipework 0.6–2.5 m/s (0.5 with grinder); max motor speed 1,450 rpm (>5 l/s) / 2,800 rpm (≤5 l/s); solids handling min 76 mm (65 mm with upstream basket) | p40–41 Tab 17 |
| ★ **Minimum PS land area** (drives SLS plot reservations) | **Type 1: 50–100 m²; Type 2: 200–400 m²; Type 3: ≥900 m²**; access with ≥6 m wide turning circle and hard standing | p43 Tab 21 |
| ★ Minimum-flow factors (Tab 16) | Initial minimum flow = average flow × factor: 50 l/s → **0.25**; 500 → 0.35; 2500 → 0.45; 5000 → 0.50. **This flow — not the average — sizes the force main against deposition** | p40 §7.4 Tab 16 |
| ★ Emergency overflow (mandatory) | **All** pumping stations shall have an emergency overflow (Environmental Authority approval); **never at upstream manholes**; wet-well overflow fitted with dip tube/baffle; storage above start level of the last duty pump; prevention = dual power, trunk/basin storage, emergency storage, emergency pumping | p46–47 §7.5 |
| ★ Wet-well volume | Min live volume **V = 0.25·Q·T** (Q = single-pump capacity m³/s, T = 3600/starts-per-hour; min 10 starts/h up to 30 kW); successive start/stop levels separated **200–300 mm**; 5–10 s start delay; **CFD + physical modelling for stations ≥0.5 m³/s** | p48 §7.8 |
| ★ NPSH | NPSHa = Ha − Hvpa − Hst − Hf, with an **NPSH margin of at least 1 m** | p47 §7.6 |
| ★ H₂S at force-main termination | Where H₂S is expected and no field data exists, design for management/monitoring at **avg 50–100 ppm, peak ≤200 ppm** at the pressure-main termination; H₂S monitoring at the termination manhole controls chemical injection at the force-main start | p47 §7.7; p55 §8.5 |

## 8. Force mains (§8, p50–55)
| Item | Value | Ref |
|---|---|---|
| Min velocity | 0.75 m/s (continuous); **1.0 m/s intermittent**; 1.2 m/s vertical | p50 |
| Max velocity | **2.5 m/s** | p50 |
| Gradients | min 1:500 rising, 1:300 falling; never below 1:750 | p50 §8.2.1 |
| Retention time | ideally ≤ 30 min; air/washout valves at high/low points | p50 |
| Access | every 500 m | p50 |
| Separation from water mains | 3.0 m horizontal; cross **under** water main, 450 mm vertical | p51 |
| Layout | straight lines; sharp bends avoided; ≥1 m from kerb line in carriageway | p51 |
| Material — in-station | DI recommended; **stainless steel for PS < 100 L/s** | p52 §8.3 |
| ★ Material — pressure main | *"The recommended pipe material for the pressure main is **Ductile Iron and HDPE**"* — HDPE is permitted for the force main itself (previously missing) | p53 §8.3 |
| ★ Min velocity applies at **minimum** flow | The 0.75 m/s is to be maintained **at design minimum flow** (max static head), with that flow taken from Tab 16 factors — not at continuous/average flow | p50 §8.1; p40 Tab 16 |
| ★ Min diameter | **75 mm ID** for non-clog pumps; **50 mm ID** for grinder pumps | p50 §8.1 |
| ★ Run full | Pumping mains shall be designed to **run full and remain full at all times** | p51 §8.2.1 |
| ★ Valve spacing | In-line isolation valves at **~500 m, never exceeding 800 m**; washout valves at low points sized for **3–4 h section emptying** (≤400 mm main → 100 mm; 500–800 → 150; 900–1200 → 200; ≥1200 → 300 mm); double-orifice air valves at high points, approach gradient not flatter than 1:500 and departure not flatter than 1:300, each with separate geared isolation valve | p53–54 §8.4 |
| ★ Termination | Force mains shall discharge to the gravity system **at a manhole, entering not more than 300 mm above the receiving manhole flow line**; water seal + forced venting through odour control where turbulent; corrosion-resistant/lined receiving manhole | p55 §8.5 |
| ★ Water-main crossing detail | The 450 mm vertical is **outside-to-outside**; one full length of water pipe centred so both joints are as far from the force main as possible; special structural support may be required | p51 §8.2.2 |
| ★ Surge analysis criteria | Transient analysis in NWS-approved software; simultaneous pump start/stop modelled to **N+1**; **no vapour cavities / column separation**; min pressure not below manufacturer limit or **−0.2 bar** below atmospheric, whichever is higher; max ≤ hydraulic test pressure / lowest component rating; zero-roughness run first for worst case | G1-p146–147 App III |

## 9. STP (§10, p63–74)
| Item | Value | Ref |
|---|---|---|
| Size categories | Small <500; **Medium 500–20,000**; Large ≥20,000 m³/d | p65 |
| Design horizon (STP) | ≥ 15 yr, projected population + industrial | p65 |
| Site selection criteria | Table 27: accessibility, land/phasing, winds/geology/hydrology, **topography to limit pumping**, groundwater & flood protection (25/100-yr), buffer from residential, CAPEX/OPEX LCC | p63–64 |
| Land footprint | MBR 0.45–0.9; MBBR 0.9–1.8; SBR 0.9–1.8; IFAS 1.2–2.5; CAS/EA 1.8–3.6; wetland >10 m² per m³/d | p64 Tab 28 |
| Incoming flow | avg sewage flow + infiltration (**per AM/PAM-GUD-201**) + **10% STP operational allowance** | p65 Tab 29 |
| Flow definitions | AAF (annual avg), MDF (max day), PHF (peak hour); hydraulic pass-through sized on PHF; biology on AAF+load | p65–66 |
| Organic load | ≥ **60 g BOD5/cap/d**, **80 g TSS/cap/d** unless justified | p74 |
| COD/BOD domestic | 1.8–2.2 | p74 |
| Emergency lagoon | 48–72 h STP capacity, only *"in specific cases, under NWS requirement and approval"*; purpose = holding problematic influent/effluent within the **tanker/septage** provisions, pumped back to inlet works when capacity allows. **Not** a general emergency store — not the same thing as the scope's 5-day storage lagoons | p73; scope p13(61) |
| TSE quality | *"At least Class A"* per MD 145/93 for wadi discharge, **subject to prior agreement with NWS**, + EA and APSR approval. ★ The MD 159/2005 N/P modification applies **only** *"if the Wadi discharges to sea at a reasonable distance"* — **Ibri's wadis are inland, so applying 159/2005 blindly would impose ammoniacal-N 1.0 vs 5 mg/L and TP 2.0 vs 30 mg/L** and over-specify the plant | p72–73 §10.2.4.3 |
| ★ Total nitrogen + chlorine | Selected technology shall meet **TN < 15 mg/L as N**; chlorine residual at STP discharge **0.3–1.0 mg/L** minimum, up to 3.0 mg/L permitted to allow decay along the TSE network | p71 §10.2.4.1 |
| ★ Raw sewage characteristics | Influent quality primarily from **NWS LIMS** data for the catchment. Tab 30 defaults (usable only by NWS agreement when data unavailable): BOD₅ 350–400, COD 700–900, TSS 400–500, TKN 60–80, NH₃-N 40–50, TP 10–15 mg/l, 20–35 °C. **Tab 31 tanker sewage: BOD 350–1050, COD 1350–5000, TSS 900–4300 mg/l** — material at Ibri's ≈17 % tanker share | p67 Tab 30; p68 Tab 31 |
| ★ Tanker/septage reception (mandatory) | Septage allowances **must** be provided by: (1) dedicated tanker discharge station with screening + oil & grease removal; (2) **flow-equalization tank specifically for tanker discharge** to prevent shock loads; (3) the 48–72 h emergency lagoon in NWS-approved cases; (4) operational measures (pre-acceptance sampling, SOPs, traceability, contractual limits). Also GUD-201: *"In the case of receiving tankers and/or non-domestic sewage, appropriate **pre-treatment** processes shall be selected"* | p73 §10.3.1; G1-p55 §6.8 |
| ★ COD/BOD > 2.2 | Influents above the 1.8–2.2 domestic range are *"not effectively biologically treatable"* and a **separate treatment line for high-strength wastewater shall be required** if such volumes are significant → directly triggered by the tanker/septage stream (Tab 31 COD/BOD ≫ 2.2) | p74 §10.3.1 |
| ★ Organic peak factors | Shock/diurnal peaks shall be considered in aeration design: **PF BOD & COD = 1.5** (small STP) / **1.2** (medium–large); **PF TKN = 2.0** (small) / **1.5** (medium–large); flow/load equalisation considered where surge loadings are critical | p74 §10.3.1 |
| ★ Existing-works organic basis | For upgrade/expansion of an existing STP (**Ibri has one**), organic design shall be based on **actual measured strength from the Client's laboratory** (LIMS historic + updated data) with a growth increment — not on default per-capita loads | p74 §10.3.1 |
| ★ **Buffer zones (numeric)** | GUD-201 Tab 8, subject to NWS approval + ESIA: STP **small/medium 500 m** to residential **and** industrial; **large 300–1000 m** based on odour modelling (5 OU contour); small STP <150 PE 10–30 m; **sewage pumping station 30 m** residential / 20 m industrial. Ultimate Ibri flow ≥20,000 m³/d = **Large** category | G1-p43–44 §6.1.3.3 Tab 8 |
| ★ Built-footprint cap | Total built footprint of all structures ≤ **35 %** of allocated land (remainder for circulation, buffers, setbacks, future expansion); boundary setbacks min **5 m**. Applies on top of the m²-per-m³/d rates in Tab 28 above | G1-p50 §6.4.2 |
| ★ Phased process lines | *"Treatment plants **shall** be designed using **several process lines** allowing additional capacity for different design horizons or phases"* — mandatory support for the phased build-out decision | G1-p53 §6.6.2 |
| ★ N+1 process capacity | At site level (treatment plants, reservoirs, pumping stations) adopt modular **N+1**: N elements meet average day flows, N+1 meets peak capacity | G1-p33 §4.3 |
| ★ Capacity basis | STP treatment capacity shall be based on **average per-capita consumption per the latest NWS Integrated Master Plan**; a more realistic figure only as an NWS-accepted, Designer-justified exception | p65 §10.2.2.1 |
| ★ Flow definitions — omissions | Sizing rules carry an escape clause *"Except when stated otherwise … or instructed otherwise by NWS"*; *"The hydraulic and load design **shall include recycled liquors and the received tanker volumes** if applicable"*; a fourth flow exists — **Design Peak Instantaneous Flow** | p65–66 §10.2.2.1 |
| ★ Climate resilience | Resilience assessed at a **50-yr horizon** even where asset design life is shorter, using an NWS-agreed climate model, at both **+2 °C and +4 °C** IPCC scenarios — including changed flood frequency/intensity on site selection. Supplements the 25/100-yr flood levels | G1-p33 §4.4 |

## 10. Vacuum systems (§9, p56–62) — screening only
- For low-density population, flat terrain, high groundwater where gravity uneconomical (p56). Max flows/lengths per Table 26 (p60): DN90 1 L/s; DN250 20 L/s, 1500 m.

## 11. Flow estimation chain (BINDING — PAM-GUD-201 §7)
> **Audited 2026-08-17** against the source PDFs, row by row (13-agent sweep + manual re-verification of every rule marked ★). Rows carry the verbatim source phrase wherever the wording changes how the rule is applied. **Do not paraphrase a row without the quote — that is exactly how the non-domestic error happened.**

### ★ 11.0 THE TWO-TIER RULE — read this before using any number below
GUD-201 §7 gives **two methods for everything**, and the wrong tier was applied throughout W1–W3:

| Tier | Applies when | Methods |
|---|---|---|
| **A — Planning / forecasting** | broad service areas, no land-use detail | Tab 11 LPCD + "Distributed" ratios 22 %/14 %; Tab 19 return rates 85 %/54 % |
| **B — Project-specific design** ← **Ibri is here** | "where detailed land use information is available" | **Tab 12** unit rates for non-domestic & governmental; design flows per **BS EN 752** (or stated equivalent) + site-specific evidence |

Source, twice, in mandatory wording:
- §7.3.2 (G1-p60): *"If the project provides detailed land use allocation within the project area, the non-domestic water Consumption **shall** be calculated using the reference values presented in the Table 12."*
- §7.3.3 (G1-p61): *"…the Governmental Consumption is to be calculated specifically for the project **and not as a ratio of domestic consumption**."*
- §7.4.1 (G1-p71): *"For project-specific designs where detailed land use information is available, Design flows **shall** be calculated in accordance with a relevant international standard such as BS EN 752 … **Calculations shall clearly state which standard has been used.** This shall be supported by the collection of data and site-specific evidence to validate the design criteria."*

Tier A values are self-described as provisional: Tab 19 figures are *"baseline figures [that] provide a general framework for **planning and forecasting purposes across broader service areas**"* (G1-p70). **Every Tier-A number used in a deliverable must be labelled as a fallback pending the Tier-B data, with the data request named.** Tier-B inputs are data-request items 3 and 6 (`W3/analysis/A7_data_request_note.md`).

**Precedence above both tiers** — *"In the absence of a developer-provided water demand calculation based on an approved methodology, the water demand shall be calculated in accordance with the methodology detailed below"* (G1-p59 §7.3; identical clause for WW at G1-p70 §7.4). A developer/NWS-approved calculation, if one exists, outranks this whole chain.

### 11.1 Population
| Step | Value | Ref |
|---|---|---|
| NCSI is the official source | population + housing data at **Governorate / Wilayat / Settlement** levels, GIS-deliverable from NCSI | G1-p58 §7.2.1 |
| ★ Wilayat→settlement disaggregation | If forecasts exist only at wilayat level, distribution **must** be carried out pro-rata to the **latest census settlement shares** | G1-p58 |
| ★ Sub-settlement split | Where the project area is smaller than a settlement: pro-rata by **number of electricity accounts**, provided by NWS | G1-p58 |
| ★ **Extrapolation limit** | NCSI forecasts cover 20–25 yr. Beyond: polynomial regression on NCSI data, but *"it is not recommended to extrapolate more than **ten years** beyond the available forecast period"*. **Project consequence: the R0 series runs to 2100 — anything past ~10 yr beyond NCSI's own horizon is uncertainty, not data. The 2055 and ultimate cases must be defended on land capacity, not on the extrapolated curve** | G1-p58 |
| Population from plots | Population = plots × avg properties per plot × occupancy rate; OR = Population ÷ Housing Units from NCSI, most recent data, at the geographic scale of the project (value = `[GAP-5]`) | G1-p58–59 §7.2.2 |
| ★ **Mandatory build-out NOTE** | *"special care must be given in cases of **plot subdivision**, to ensure that population estimates properly reflect the **effective number of housing units created**. In addition, **development speed must be considered through appropriate phasing assumptions**, as not all plots will be developed simultaneously. Coverage will be estimated using planning data and land use typologies, and **development percentages must be applied over the design period** … particularly avoiding overestimation."* → **Raw plot count × OR at 100 % build-out is non-compliant.** | G1-p59 NOTE |

### 11.2 Water demand (§7.3)
| Step | Value | Ref |
|---|---|---|
| Domestic — **Adh Dhahirah** | **164 l/c/d**. Tab 11 values are *"indicative figures derived from the recent Integrated Master Plan (2024)"*, apply *"in absence of any updated figures"*, and *"should be validated by NWS as essential design criteria, before designing the project"* | G1-p59–60 Tab 11 |
| ★ **What 164 actually measures** | `LPCD = Total Domestic Water Accounted ÷ (OR × active Domestic Accounts)` — **network-accounted water only**. It does not include tanker or private-well supply. See §11.3 "other sources" | G1-p60 |
| **Non-domestic — Tier B (the method)** | **Tab 12** unit rates: educational 130 l/d per pupil+staff; hospitals 650 l/d per bed+staff; commercial shopping 12.2 l/d/m²; hotels 200–500 l/cap/d; office 93 l/d per employee; restaurant 7.4 l/d/m²; mosques 185 l/d/m²; **wet industry = "Not Applicable / Variable" (no unit rate — developer must supply)**; dry industry 93 l/d per employee; army camps 185 l/d per occupant; prisons 185 l/d per **prisoner + staff** | G1-p61 Tab 12 |
| ★ **Tab 12 unit basis** | Keyed to **floor area / pupils / beds / employees — never plot area**. Ibri check: 121.2 ha of mosque *plots* × 185 l/m²/d = 224,143 m³/d ≈ **4× the whole ultimate STP flow**. Substituting cadastral plot area is wrong by an order of magnitude | G1-p61 |
| Tab 12 NOTE | *"The designer can provide additional details per category or data for his design and **shall substantiate** the use of an alternative value"* — rates are defaults; deviation needs justification, not silence | G1-p61 |
| **Non-domestic — Tier A (fallback only)** | +**22 %** of domestic LPCD. Tab 11 header: **"*Distributed* Non-Domestic Ratio (% LPCD)"** — governorate 2021–23 water-balance volume spread over population, **not** a per-person demand | G1-p60 §7.3.2 |
| ★ **Ratios exclude identified projects** | *"These ratios do not apply to the water consumption of **specific identified non-domestic projects such as economic zones**[, which] are to be determined on a case-by-case basis."* → a named industrial estate (e.g. AL TAYYEB IND.) can never be covered by the 22 % | G1-p59 §7.3.1 |
| Ratio is not frozen | *"The updated ratio can be provided by the NWS Planning department"* | G1-p60 |
| Governmental | Tier B: calculated specifically for the project, *"not as a ratio of domestic consumption"*. Tier A fallback +**14 %** ("Distributed Governmental Ratio") | G1-p60–61 §7.3.3 |
| ★ **Special consumption** | *"specific projects within the project perimeter … **must be provided by the developer** … labour camps, industrial facilities with high water usage … **These needs are not covered by population forecasts**"* → **additive** to the LPCD chain, never inside the 22 %/14 % | G1-p61 §7.3.4 |
| ★ **Blue (potable) tanker demand** | If a TFS is in/near the project area, tanker consumption **must be explicitly assessed** from NWS TFS data (historical use, service area, change over horizon), NWS-validated, and added to total demand. **Tab 13: Adh Dhahirah = 5,145 m³/d (2021–23 avg) = 333 % of 2023 network domestic consumption — by far the highest in Oman (next: Ash Sharqiyah South 56 %).** IMP holds tanker demand constant over time | G1-p61–62 §7.3.5, Tab 13 |
| **Double-count warning** | Use Tab 12 **or** the ratios, never both. Tab 12 rates on commercial plots *plus* the +22 %/+14 % uplift counts the same water twice | G1-p60–61 |
| ★ **Spatial allocation — PROJECT DEVIATION, needs NWS concurrence** | GUD-201 wording is *"spatially distributed non-domestic consumption that are to be added to the domestic consumption"* (G1-p59), which reads as smearing the uplift across the served population. **This project concentrates it instead**: 164 l/c/d on the residential population, then the ND+Gov volume onto non-residential plots by area (Tab 12 quantities once received). Justification: a residential-only branch generates no commercial or government flow; total is preserved, allocation moves. Effect measured in W3 A7: project Qadf unchanged, zones shift −16.8 % to +127.2 %. A residential-only branch runs at **164 × 0.85 = 139.4 l/c/d**, not the area-average 171.3. **Flag as a deviation in the report and obtain NWS agreement** | G1-p59 §7.3.1 + `W3/py/a7_load_alloc.py` |

### 11.3 Wastewater generation (§7.4)
| Step | Value | Ref |
|---|---|---|
| Return rate water→WW | Tab 19: domestic & tanker **85 %**; non-domestic (government and commercial) **54 %** — *"baseline figures [that] provide a general framework for planning and forecasting purposes across broader service areas"* (Tier A) | G1-p70–71 §7.4.1 |
| ★ **Tier B design-flow route** | *"For project-specific designs where detailed land use information is available, Design flows **shall** be calculated in accordance with a relevant international standard such as **BS EN 752** … or another equivalent standard. **Calculations shall clearly state which standard has been used.** This shall be supported by the collection of data and site-specific evidence."* Also *"refer to international industry guides and codes of practice such as **British Water Code of Practice for Flows & Loads**"* | G1-p71 §7.4.1 |
| ★ **Other water sources — BINDING** | *"the Designer **shall** carry out an assessment of other potential water sources within the project area, such as **private wells, private water providers, or other non-network abstractions**, to ensure that their contribution to wastewater generation is properly accounted for."* Plus: *"A specific attention is to be taken for catchments covered with private wells."* **Project consequence: with tanker water at 333 % of network domestic consumption (Tab 13), deriving Ibri's WW from network demand alone under-predicts the load. This is a Tier-1 data request** | G1-p70 §7.4, §7.4.1 |
| WW components | domestic + non-domestic + **tanker discharges** + special facilities (industrial/institutional) | G1-p70 §7.4 |

### 11.4 Peaking, infiltration and tankers
| Step | Value | Ref |
|---|---|---|
| WW peak factor — primary | **Merrimack** `Qpdf = 2.65·Qadf^0.879` (both in **Ml/d**) — *"is to be used"* (mandatory) for a catchment/sub-catchment *"having **over 100 properties**"*; Pf = Qpdf/Qadf | G1-p71 §7.4.2 |
| WW peak factor — alternative | *"Alternatively"* IMP2024 **Peltier**: `PfWW = 1.5 + 1/√Qm`, NOTE: *"the Average Daily Flow in this formula is in **liters per second**"* | G1-p72 |
| ★ 5.0 cap is a **recommendation** | Source: *"It is **recommended** that the **hourly** peak factor should not exceed 5.0"* — not an absolute limit. Do not silently truncate peak capacity at 5.0 on small headworks without saying so | G1-p72 NOTE |
| Infiltration | New networks **720 L/d per km of sewer**; existing inland (outside GW influence) **10 %** of WW flow; existing in GW-table zones or coastal **up to 40 %**. *"Infiltration due to storm water is not considered."* | G1-p72 §7.4.3 |
| ★ Infiltration exemption | *"**Tanker or vacuum collection do not require to account for infiltration volume**"* — tanker-delivered flow carries none | G1-p73 |
| Infiltration is a **pipe** load | It enters through joints/walls along the network → assign per pipe (720 L/d/km × length) in SewerGEMS, not as an STP-gate addition. [Likely] add unpeaked (no diurnal pattern) — GUD-201 does not state the order; confirm at kickoff | G1-p72 + engineering judgement |
| ★ Yellow (sewage) tankers | *"In 2024, the yellow tanker represented approximately **17 %** of the total flow reaching the STPs of Nama WS"* — a **company-wide 2024 observation, not a per-STP design allowance**. Collection-system capacity *"should assume the same coverage as for the water supply"*, with **100 % coverage assumed by end of planning period**. Check self-cleansing at initial operations. *"The pollution loads of tankers are **higher** than the network effluent"* → affects STP **process** sizing, not only hydraulics (see GUD-203 Tab 31) | G1-p73 §7.4.4 |
| STP design margin | +**10 %** *"when designing **new** STPs"*, covering fluctuations in population, consumption, infiltration and unforeseen factors; *"to be applied **over and above any redundancies** in the design to mitigate operational outages"* — never netted against duty/standby | G1-p73 §7.4.5; p65 Tab 29 |

### 11.5 TSE / treated-effluent side (§7.4.6)
| Step | Value | Ref |
|---|---|---|
| TSE production ratio | **95 %** of STP inlet | G1-p73 |
| ★ **TSE network system loss** | *"For design purposes, a system loss of **10 percent** of all produced TSE **shall** be assumed"* (joints, connections) → deliverable TSE ≈ **0.95 × 0.90 = 85.5 %** of STP inflow, not 95 % | G1-p76 §7.4.6.3(b) |
| ★ TSE sizing basis | *"The TSE system **shall** be sized to accommodate the **peak demand experienced during the summer months**."* Tab 23 seasonal factors (% of summer): Dec–Feb **50 %**, Mar–May & Sep–Nov **75 %**, Jun–Aug **100 %** | G1-p76 §7.4.6.4, Tab 23 |
| TSE demand rates | Tab 21 summer planting rates: shrubs 20–40, palms 120–165, other trees 40–80 L/plant/d; hedges 10 L/m/d; ground cover & seasonal flowers 10, **grass 12 L/m²/d**. Tab 22 densities: trees 15 m, shrubs 3 m spacing. Roads/junctions with mixed vegetation and no specific data: **10 L/m²/d, subject to Municipality approval** | G1-p73–75 §7.4.6.2 |
| Large TSE consumers | *"Any consumer with an average daily demand larger than **500 m³/day** is to be studied individually, and an irrigation timing pattern shall be applied that reflects its actual settings"*; consumers with large storage → demand spread over storage hours | G1-p76 §7.4.6.4 |
| Sludge production | **0.25 kg/m³** — GUD-201 master-plan baseline, *"a general guideline"*, process-dependent (**not** an R0 invention, as previously recorded) | G1-p78 §7.4.7 |

### 11.6 Design life and horizons
| Step | Value | Ref |
|---|---|---|
| Planning life | **25 yr**, which *"corresponds both to the **ultimate design capacity** of the project, as well as the period over which the **NPV** will be calculated for … comparing schemes"* — binding for the ≥3-options appraisal | G1-p57 §7.1 |
| Asset lifetimes (Tab 10) | Civil/structures **50**; mechanical **20**; electrical **15–50**; ICA works **15**; pipework **50** yr. *"These asset lifetimes are used for financial asset depreciation calculations"* — technical life may differ with manufacturer/material | G1-p57 Tab 10 |
| Scope horizon | completion + 25 yr or ultimate/saturated; model years start/2030/2055/ultimate; 5-yr projection intervals | scope p3, p14–15 |
| ★ Climatic design (inland) | Ibri = inland: max peak shade **55 °C**, max daily avg 50 °C, max yearly avg 35 °C, metal in sun 85 °C, RH to 100 %. *"All equipment shall be rated for continuous operation under [these] ambient conditions … and performance guarantees shall be given at these conditions"* | G1-p78–79 §7.5 Tab 24 |

## 11b. Wadi crossings (PAM-GUD-201 §9.3 — supplements §6 above)
| Item | Value | Ref |
|---|---|---|
| Data & approvals | wadi bed profiles/cross-sections, flood frequency 1:20/1:50/1:100, bed material, bed-level change — from CAA & **MoAFWR**; MoAFWR approval required | G1-p85 |
| Pipe material | **DI over crossing length + 15 m each side**, mechanical/detachable joints | G1-p86 |
| Protection | per NWS std dwg **PAM-STD-404**; anti-flotation check (empty pipe, flood/high GW) | G1-p86 |
| Cover in soft soil | **min 2.0 m** (vs 1.5 m force-main GUD-203 p52) | G1-p86 |
| Valves | isolation + air valves both sides of active/major crossings; washout at low point one side; **no chambers/markers in wadi bed or embankments**; all accessible during flood | G1-p86 |
| Road crossings | trenchless preferred; reinstatement per Oman Highway Design Manual | G1-p85 |
| Falaj crossings | buffer zones, protection, min safe excavation distances | G1-p86 |

## 12b. Water & TSE networks — PAM-GUD-202 (§7 Transmission, §9 Distribution)
| Item | Value | Ref |
|---|---|---|
| Transmission velocity | 1.0 ≤ v < 2.0 m/s (1.5 m/s common practical peak, 25-yr horizon) | G2-p103–104 |
| Head loss equations | Darcy-Weisbach (large pipes/high v) or Hazen-Williams (small dia); others need NWS Hydraulic Team approval | G2-p104 |
| Roughness (age-dependent, Tab 21) | DI: C 140→120, ε 0.26→0.45 mm (0→20 yr); GRP C 150 / ε 0.005; HDPE C 150 / ε 0.007; PVC C 150 / ε 0.0015 | G2-p104 |
| **TE pipeline roughness penalty** | **ε +30 %, Hazen-Williams C −10 %** vs tabulated potable values | G2-p104 Note |
| Max linear head loss | transmission < **5.0 m/km**; distribution < **3.0 m/km** | G2-p105, p136 |
| Distribution velocity | **0.4 ≤ v < 1.5 m/s** (below 0.4 → water-quality/age model + 0.2 mg/l residual Cl proof) | G2-p136 |
| Distribution pressure | min **1.5 bar** worst point peak-hour; max **4 bar**; fire flow: pressure stays positive | G2-p137 |
| Distribution pipe material | PE100 ≤ 1000 mm (fixed OD series); DI > 300 mm and at road/wadi crossings | G2-p138 |
| Pumping stations, reservoirs, surge | §5 storage classes, §6 PS design + NPSH/transient, §10 surge analysis mandatory ref | G2-p53+, p70+, p144 |
| Tanker filling stations | peak-hour factor 1.5–2.0 on avg flow; ≥ 2 concurrent bays; +20 % reserve; ≥ 1 m³/min per bay @ 2–4 bar | G2-p154 |

## 12c. Ibri Inception R0 adopted values (workbook `Ibri Sewer Demand R0 2026 08 03.xlsx`, received 2026-08)
Project-specific adoptions — reconcile against GUD-201 §11 above; deviations flagged:
| Item | R0 value | vs standard |
|---|---|---|
| Population basis | NCSI wilayat series: Ibri 183,564 (2024), growth ≈ 2.4–3.0 %/yr, settlement disaggregation | consistent G1-p58 |
| Domestic LPCD (Adh Dhahirah) | **163.5 l/c/d** (computed from actual consumption 2021–24) | ≈ GUD-201 Tab 11 164 |
| Return ratios | domestic & tanker 0.85; non-domestic & governmental 0.54 | = G1-p71 |
| Infiltration | **10 % of WW flow** (settlement-conditional) | GUD-201 says 720 L/d/km for NEW networks — flag at kickoff |
| Tanker catchment | settlements within **25 km** of STP | ★ **Corrected**: the 25 km IS in GUD-201 — §8.1 (G1-p80) defines **Remote Areas** as settlements *"approximately 25 km or more from existing centralized … networks"*, or *"population less than 500 residents or fewer than 100 plots at the end of design period"*, to be served by on-site solutions rather than network connection. R0 reused the same 25 km as a tanker-catchment radius — cite G1-p80 and confirm the reading with NWS |
| Weekly peak | +20 % | not in the GUD-201 WW peaking chain (§7.4.2 = Merrimack or Peltier only). Note GUD-201 **does** define a water-side peak day as *"the average day consumption in the peak week (7-days rolling) excluding leakage"* (G1-p62 §7.3.6) — R0 appears to have carried a water-side concept into the WW chain, on top of Peltier. **Peaking twice; needs an NWS ruling** |
| STP margin | +10 %; TE production 95 %; sludge 0.25 kg/m³ | = G1-p73. ★ **Corrected**: sludge 0.25 kg/m³ is **also in GUD-201** (G1-p78 §7.4.7, master-plan baseline, process-dependent) — not an R0-only value |
| ★ TSE network loss | not applied in R0 | GUD-201 G1-p76 requires **10 % system loss on produced TSE** — R0's 95 % production ratio alone overstates deliverable TSE by ~10 % |

## 12d. Odour & H₂S — PAM-GUD-203 §11 (★ whole chapter was absent from this file until 2026-08-17)
| Item | Value | Ref |
|---|---|---|
| Designer deliverable | Designers of sewage networks, PS and force mains **shall provide NWS a dedicated H₂S management evaluation** — preventive (re-sizing, chemical injection) and corrective (monitoring, flushing, coatings, odour treatment). A design-report deliverable | p162 §11.1 |
| Network design for odour | Networks shall minimise odour-generating conditions: retention times minimised, turbulence avoided, **no over-sizing of trunk sewers** (creates deposition) | p166 §11.3.2; p168 §11.4.2 |
| **Inverted siphons prohibited** | *"Inverted siphons **shall not be allowed**"* — stronger than the scope-TOR "avoid where no other feasible means". Any siphon is a formal deviation needing justification | p182 §11.5.3.1(c) |
| PS / force-main odour rules | PS and pressure mains avoided wherever gravity is feasible and cost-effective; minimise hydraulic detention (consider twinning force mains at low flow); FM discharges **submerged** where possible; allow FM to drain back to wet well between cycles; avoid partially-full FM | p181–182 §11.5.3.1 |
| Risk-assessment methods | Qualitative: **Fayoux** scoring (temperature, residence time, velocity, redox — 0–5 no risk, 5–10 low, 10–30 significant/certain), evaluated at max temperature and night-time flow. Quantitative: **Pomeroy-Parkhurst**, EBOD = BOD₅ × 1.07^(T−20) | p185 Tab 99; p186 §11.5.3.4 |
| Odour limits at boundary | Urban/near residential **3–5 OU/m³**; industrial 10–15; rural/isolated 10–20. Compliance (Tab 90): **5 OU/m³ sensitive / 15 OU/m³ industrial at the boundary wall**, continuous online e-noses (min 3). MD 41/2017; BS EN 13725:2022 | p165 §11.3.1; p170 Tab 90 |
| Odour treatment | Abatement assessment + dispersion modelling mandatory to justify the odour unit (or its absence); in most cases **multi-stage** (bio-trickling filter + chemical scrubber, +carbon where needed), integrated **99.95 % H₂S / 85 % odour** removal; **N+1 redundancy on every odour control system** | p170–176 §11.5.2 |
| Network emergency overflow sizing | Retention basins sized for **24 h of nominal flow** (emptied by yellow tanker); relief sewers at **1.5 × nominal flow**. Distinct from the STP 48–72 h emergency lagoon | p191 §12.1.1 |

## 12e. Modelling, options appraisal and project workflow (★ added 2026-08-17)
| Item | Value | Ref |
|---|---|---|
| ★ **Hydraulic model methodology** | Per **WaPUG/CIWEM Code of Practice** and US EPA SWMM manuals; modelling at design phase **and after construction**. Models (static, EPS and surge) submitted to NWS after **each** design phase including final as-built models | G1-p144, p109 §13.4.2 |
| ★ **Model calibration acceptance** | Tab 32: peak flow **±10–15 %**, volume **±15 %**, correct peak-arrival timing, pump runtime **±10 %**. Binding on the SewerGEMS deliverable | G1-p145 Tab 32 |
| ★ Options appraisal (≥3 options) | Minimum three options with equivalent functional requirements/reliability; guidance mix = one NBS/environmental-ambition, one international best-in-class, one standard current-practice. Evaluation horizon **25 yr**; LCCA/NPV discount rate **5 %** unless NWS instructs otherwise; NWS sets MCDA weightings; **if options are within 10 % on total cost, sustainability breaks the tie** | G1-p95–96 §12, p99, p106 |
| ★ Value Engineering | Formal VE study by an independent VE-certified consultant at concept **and** preliminary stages for projects ≥ OMR 5M — **footnote lowers the trigger to any sewer treatment plant or pump station > OMR 2M** | G1-p93 §11.2 Tab 27 |
| ★ Cost/schedule accuracy by phase | Feasibility **±30 %**; preliminary/concept **±20 %**; detailed **±10 %**. Tab 2 requires a Flood Protection Assessment at **all three** phases | G1-p17–20 §1.6 Tab 2 |
| Remote areas / on-site solutions | Remote Area = ~≥25 km from centralized networks, **or** <500 residents / <100 plots at end of design period → septic tanks (Oman Private Sewage Disposal Code), holding tanks with vacuum-tanker emptying, or decentralized package plants for 50–5,000 inhabitants; package-plant TSE stored min 1 day | G1-p80 §8.1, p83–84 §8.4 |
| Trade effluent policy | Non-domestic (trade) discharges to sewer shall comply with **Appendix 3 of Royal Decree 115/2001**; customer agreement with NWS per AM-PRO-209; NWS-validated pre-treatment if necessary | p20 §3.10 |

## 12. Surveys (§13, p197)
- Topo survey along proposed routes w/ X,Y,Z Omani national datum, **metric units**; include existing utilities and adjacent roads with cross-sections near proposed pipelines; maps show grid, permanent benchmark, invert levels of existing drains; designer picks appropriate DTM. CCTV per NF EN 13508-2 for existing assets — **a Designer obligation to conduct and to provide with the Tender Documents**. CCTV/topo/geotechnical surveys at **early** design stage (p197–198).
- ★ **Topographic accuracy by stage** (95 % confidence, G1-p36 Tab 5): feasibility 1–5 m H / 0.5–2 m V (existing DEM acceptable); **preliminary/concept 0.25–1.0 m H / 0.05–0.5 m V** (UAV photogrammetry with ground control, LiDAR, GNSS RTK); detailed 0.02–0.10 m H / 0.01–0.05 m V. **Consequence: the 5 m DTM is feasibility-grade — concept-stage invert and slope claims cannot rest on it alone.**
- ★ Control benchmarks **±0.05 m** spherical accuracy, min "Order C, Class 3" GPS. Underground-services detection shall cover oil, gas, water, effluent pipelines, cables **and irrigation falaj** (trial pits, probes between manholes, ground radar, electro-location) — p198 §13.3.
- ★ STP/PS site surveys: full plot dimensions, GPS coordinates of every boundary corner, surface strata description (sand, rock, vegetation, sabkha), coverage extending **10 m beyond plot limits** — p198 §13.2.
- ★ Geotechnical: boreholes to **5.0 m below pipe invert** for shallow pipelines (p199 §13.4). Investigation spacing (G1-p40–41 Tab 7): secondary/tertiary gravity sewers — trial trench ≤3.0 m depth or borehole >3.0 m at **100 m** spacing; primary gravity sewers and force mains at **500 m**. Geophysical investigation mandatory at the earliest stage for STPs, PS and major wadi/falaj/road crossings.
