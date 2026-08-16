# DESIGN CRITERIA — PAM-GUD-203 (201 pp) + PAM-GUD-201 (152 pp) + PAM-GUD-202 (177 pp)
Refs: `p##` = PAM-GUD-203; `G1-p##` = PAM-GUD-201; `G2-p##` = PAM-GUD-202 Water & TSE Design Guidelines v1.0 (added 2026-08-14, in `_STANDARDS/` + `Data/`). **Nothing here may be altered without re-reading the source.**

## 1. Hydraulic design — gravity sewers (§4.2, p24–28)
| Item | Value | Ref |
|---|---|---|
| Design formulas | Colebrook-White or Manning; licensed software approved by NWS (SewerGEMS per scope) | p24 |
| Colebrook-White ks | **1.5 mm** all pipe sizes/materials | p24, p28 |
| Kinematic viscosity | 15 °C → 1.141e-6 m²/s (conservative basic design) | p25 |
| Min self-cleansing velocity | **0.75 m/s at peak flow**, preferred 0.90 m/s | p26 |
| Min tractive force method | Mara/Sleigh/Taylor Smin = K·Q^-0.46 (d/D=0.2, n=0.013); K=2.33e-4 (Q m³/s) / 5.5e-3 (Q L/s). Steeper of the two methods governs. Use tractive force at network heads where 0.75 m/s unattainable | p27 |
| Max velocity | **3.0 m/s** at design depth of flow | p27 |
| d/D at peak flow | ≤ **0.65** for D ≤ 350 mm; ≤ **0.50** for D > 350 mm | p27 Tab 10 |
| Manning n (plastic/GRP) | 0.009–0.011 (PVC/GRP); PE 0.009–0.015; concrete cement-lined 0.012 | p23 Tab 8 |

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
| Design life (non-structural M&E) | 20 years | p38 |
| Stakeholder NOCs early (incl. Falaj crossings) | preliminary stage | p39 |

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
| Material | DI; stainless steel for PS < 100 L/s (in-station pipework) | p52 |

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
| Emergency lagoon | 48–72 h STP capacity (NWS approval); scope demands 5-day storage lagoons | p73; scope p13(61) |
| TSE quality | Class A for wadi discharge (MD 145/93; N/P per MD 159/2005) | p69–73 |

## 10. Vacuum systems (§9, p56–62) — screening only
- For low-density population, flat terrain, high groundwater where gravity uneconomical (p56). Max flows/lengths per Table 26 (p60): DN90 1 L/s; DN250 20 L/s, 1500 m.

## 11. Flow estimation chain (BINDING — PAM-GUD-201 §7, GAP-1..3 CLOSED)
| Step | Value | Ref |
|---|---|---|
| Population from plots | Population = plots × avg properties/plot × occupancy rate; OR = Population/Housing Units from **NCSI** latest wilayat data (value itself = `[GAP-5]`, methodology fixed) | G1-p58 |
| Domestic consumption — **Adh Dhahirah** | **164 l/c/d** (IMP 2024 baseline, Tab 11; validate w/ NWS) | G1-p60 |
| Non-domestic — **method** | **Tab 12 land-use unit rates are the method, not an option**: §7.3.2 says "if the project provides detailed land use allocation … **shall** be calculated using the reference values presented in Table 12" (school 130 l/pupil+staff, hospital 650 l/bed+staff, shops 12.2 l/m², restaurant 7.4 l/m², mosque 185 l/m², office & dry industry 93 l/employee, hotel 200–500 l/cap, army/prison 185 l/cap) | G1-p60–61 |
| Non-domestic — **fallback only** | +**22%** of domestic LPCD. Tab 11 calls this the "**Distributed** Non-Domestic Ratio" — the governorate's actual 2021–23 non-domestic volume divided by its population. It is a top-down aggregate, **not** a per-person demand. Use only while Tab 12 inputs are missing, and say so in the report | G1-p60 |
| Governmental | Same rule: §7.3.3 — with land-use allocation it "is to be calculated specifically for the project **and not as a ratio of domestic consumption**". Fallback +**14%** of domestic LPCD ("Distributed Governmental Ratio") | G1-p60–61 |
| **Spatial allocation (binding)** | Never apply the 22%/14% uplift per capita to every zone — a residential-only zone carries no commercial or government flow. Apply 164 l/c/d to the residential population, then place the non-domestic + governmental volume on the non-residential plots in proportion to their area (or Tab 12 quantities once received). Preserves the total, puts the load where the land use is. Effective rate on a residential-only branch is **164 × 0.85 = 139.4 l/c/d**, not the area-average 171.3 | G1-p60–61 + this project |
| **Double-count warning** | Use Tab 12 **or** the ratios, never both. Applying Tab 12 rates to commercial plots on top of the +22%/+14% uplift counts the same demand twice | G1-p60–61 |
| **Tab 12 unit basis** | Tab 12 is keyed to **floor area / pupils / beds / employees — never plot area**. Substituting cadastral plot area is wrong by an order of magnitude (Ibri check: 121.2 ha of mosque plots × 185 l/m²/d = 224,143 m³/d, ~4× the whole ultimate STP flow) | G1-p61 |
| Return rate water→WW | Domestic & tanker **85%**; non-domestic/governmental **54%** (Tab 19) | G1-p71 |
| WW peak factor | Merrimack Qpdf = 2.65·Qadf^0.879 (Ml/d, >100 properties) or IMP2024 **Peltier: PfWW = 1.5 + 1/√Qm** (Qm in l/s); hourly PF ≤ **5.0** | G1-p71–72 |
| Infiltration | New networks: **720 L/d per km** of sewer; existing inland: 10% of WW flow; GW/coastal existing: up to 40% (no stormwater) | G1-p72 |
| Yellow tankers | ≈17% of STP inflow (2024); design coverage 100% by end of planning period; check early-stage self-cleansing | G1-p73 |
| STP design margin | +**10%** on incoming flow | G1-p73, p65 |
| TSE production ratio | 95% of STP inlet | G1-p73 |
| Design/planning life | planning cycle **25 yr**; civils 50, mech 20, pipes 50 yr | G1-p57 |
| Scope horizon | completion + 25 yr or ultimate/saturated; model years start/2030/2055/ultimate; 5-yr projection intervals | scope p3, p14–15 |

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
| Tanker catchment | settlements within **25 km** of STP | not in GUD; R0 assumption |
| Weekly peak | +20 % | not in GUD-201 PF chain; R0 assumption |
| STP margin | +10 %; TE production 95 %; sludge 0.25 kg/m³ | = G1-p73 (sludge rate R0-only) |

## 12. Surveys (§13, p197)
- Topo survey along proposed routes w/ X,Y,Z Omani national datum; designer picks appropriate DTM. CCTV per NF EN 13508-2 for existing assets.
