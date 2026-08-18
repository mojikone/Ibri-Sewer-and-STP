# GRAVITY SANITARY SEWER NETWORK — complete rule set (Ibri 2621)

Sources: `_BRAIN/02_DESIGN_CRITERIA.md` (only permitted numeric source), `_BRAIN/07_PROJECT_STATE.md` §2 (doctrine), `TUTORIALS/T01_Sewage_Flow_and_Load_Calculation.md` (flow chain), `W3/analysis/A9_criteria_audit.md` (amendments). Refs: `p##` = PAM-GUD-203, `G1-p##` = PAM-GUD-201, `G2-p##` = PAM-GUD-202. Rows tagged **[A9]** carry an audit correction; rows tagged **[A9-only]** are verified against source in A9 but NOT yet folded into 02 — for synthesis, treat the A9 wording as the corrected rule but cite it as an A9 amendment, not as an 02 row.

---

## 1. Property/house connections and rider sewers

| Rule | Value | Ref |
|---|---|---|
| Property Connection Sewer (PCS) + Rider Sewer min diameter | OD 160 mm minimal, open trench, PVC-U/HDPE. Tab 6 lists them jointly ("Rider Sewer, Property Connection Sewer*"); Tab 4 (p18) gives PCS "150 mm (minimal)" — consistent (DN150 = OD160 plastic); cite the Tab 6 / OD basis | p22 Tab 6; p18 Tab 4 **[A9]** |
| Lateral sewer | OD 200 mm min, **max length 45 m** | p22 Tab 6; §3.2 p17 |
| PCS slope | min **3 %** / max 10 % | p18 Tab 5 (in 02 §2 ★ bullet) |
| Rider sewer slope | min **1 %** / max 10 % | p18 Tab 5 |
| Lateral sewer slope | min **1 %** / max 10 % — design trap: Table 11's 0.5 % at DN200 applies to the **secondary** network only, never to a lateral | p18 Tab 5 (02 §2 ★) |
| PCS cover | min **600 mm**; **[A9-only]** source also caps PCS depth at **1.50 m** (in 800×800 square chamber) — this bounds how deep a main can sit while still receiving direct property connections | p19 §3.5 |
| PCS max length | **50 m** (maintenance); if exceeded, add a manhole. 02 carries only the 45 m lateral limit — the 50 m PCS limit is a distinct rule | p18 Tab 4 note **[A9-only]** |
| House Connection Chamber (HCC) | usually **2.5 m from property boundary** in public ROW; **up to ~3 HCC may share one rider sewer**; HCC depth 1.2–2.0 m; rectangular concrete 600×750 mm only for depth ≤1.4 m and NOT recommended under traffic lanes; circular 1.0 m dia (concrete/GRP/HDPE/PRC) for 1.0–2.0 m | p17; p19 §3.4; p31 §4.4.1(i)(b) **[A9-only]** |
| Stub-outs (project doctrine) | capped connections at future-plot frontage, sized for that area's **saturation** flow; usually **DN200 minimum governs** | PROJECT-STATE §2.3 |
| Where riders discharge | **ABSENT from 02/A9** — sources establish riders collect up to ~3 HCC, but the rider's discharge point (lateral vs manhole) is not extracted. Treat as explicit assumption pending source re-read | — |

## 2. Public sewers — diameters, materials, roughness, formula

| Rule | Value | Ref |
|---|---|---|
| Main sewer min diameter | **OD 200 mm** | p22 Tab 6 |
| Secondary network range | 200–400 mm typical (400 is not a mandatory ceiling) | p23 |
| Trunk main definition | D > 800 mm, length > 1,000 m without connections, upstream of STP/main PS (source typo "1,000 mm" — 1,000 m is the only sensible reading) | p35 **[A9]** |
| Materials, main OD200–300 (open trench) | PVC-U **up to 250 mm only**, HDPE, GRP; Tab 7 matrix: U-PVC (SN4–SN8) permitted OD160–315 only, prohibited above OD315 (conservative reading 250 for mains — confirm with NWS); specs PAM-SPC-207 (U-PVC), -204 (GRP), -206 (HDPE) | p22 Tab 6; p23 Tab 7 **[A9-only]** |
| Materials, main ≥350 | open trench: GRP, HDPE, **GRP/PVC** (A9 adds), lined RCC; trenchless: GRP/HDPE — with condition: encased in concrete, or slip-lined through sleeve pipe and grouted, or standalone pipe with suitable stiffness | p22 Tab 6; p21 §4.1.1 **[A9]** |
| Trunk material > 600 | GRP, lined RCC, profile-wall HDPE; alternate materials must be justified and approved by NWS | p35 Tab 14 **[A9]** |
| Alternate materials (all) | "Use of alternate materials must be justified and approved by NWS" | p21 §4.1.1 **[A9]** |
| Hydraulic formula | **Colebrook-White or Manning**; licensed software approved by NWS (SewerGEMS per scope) | p24 |
| Colebrook-White ks | **1.5 mm** all pipe sizes/materials | p24, p28 |
| Manning n | PVC/GRP 0.009–0.011; PE 0.009–0.015; concrete cement-lined 0.012 | p23 Tab 8 |
| Kinematic viscosity | 15 °C → 1.141e-6 m²/s (conservative basic design) | p25 |

## 3. Manholes

| Rule | Value | Ref |
|---|---|---|
| Max spacing | DN200–315: **100 m**; 350–900: **120 m**; 1000–1400: **150 m**; >1400: **200 m**; deviation needs NWS pre-approval (heading says "recommended maximum" but the pre-approval sentence makes it effectively binding) | p30 Tab 12 |
| Locations | change of grade/diameter, junctions, **end of each lateral sewer**, regular spacing on straight pipeline (basis: maintenance equipment) | p29–30 |
| Drop (backdrop) trigger | required when invert drop > **600 mm** | p30 |
| Backdrop rules | shall be **external**; max height **2 m** (beyond → vortex drop shaft); internal backdrops ONLY for new connections to **existing** manholes where external is not practicable, AND never on MH < 1.5 m dia. 02's row ("internal only if MH ≥ 1.5 m dia") drops the existing-manhole condition — as written it would permit internal backdrops on new manholes, which the source forbids | p30 §4.4 **[A9-only correction]** |
| Inlet angle | ≥ **90°** to flow direction; no penetrating connections | p30; p19 §3.6 |
| Benching | benching/channels with smooth transitions between inlet and outlet diameters/inverts ("shall") — detail-design level | p30 §4.4 **[A9 note]** |
| Min cover (gravity sewer) | **1.3 m to crown** (shall); if <1.3 m: concrete protection required and the **0.5 m minimum is measured above the pipe AND its protection**; design check required for shallow pipe beneath major roads/highways | p33 §4.6.3 **[A9]** |
| Max depth (the 12 m rule) | max cover **~10–12 m**; beyond → manufacturer check; where excavation cost prohibitive → **incorporate pumping station**. SLS consequence (project rule 9): one consolidated station per contiguous non-gravity pocket, cascade within ~1.5 km, absorb pockets <50 plots to detail design | p33; CLAUDE.md rule 9 |
| Prohibited locations (5 zones, not 1) | (a) wadis & flood-prone/washout areas (pipelines AND chambers); (b) rectangular 600×750 chambers not under traffic lanes; (c) infrastructure **must not be under electrical power lines**; (d) overflow points avoid sensitive ecosystems; (e) avoid unstable/highly erodible ground | p30–31 §4.4.1; p33 **[A9-only for b–e]** |
| Position vs kerb | outside of **manholes ≥ 0.5 m from kerb line**; outside of mains in the vehicle carriageway (not footpath) ≥ 1 m from kerb — stated in the **force-main** layout clause (§8.2.2); no gravity-specific equivalent exists in 02 | p51 §8.2.2 **[A9]** — flag context |
| Manhole min/max sizes by depth & pipe diameter | **ABSENT from 02** — no manhole diameter/size table exists in the digest (only the 1.5 m internal-backdrop threshold and HCC dimensions). Needed for W4; treat as explicit assumption or extract from GUD-203 §4.4 tables |

## 4. Hydraulic constraints

| Rule | Value | Ref |
|---|---|---|
| Min self-cleansing velocity | **0.75 m/s at peak flow**, preferred 0.90 m/s | p26 |
| Min tractive force method | **Smin = K · τ^1.23 · Q^−0.461** (Mara/Sleigh/Taylor; τ in **Pa**; assumptions d/D = 0.2, n = 0.013); K = 2.33e-4 (Q in m³/s) or 5.5e-3 (Q in L/s). **A9 MISREAD correction 2026-08-17**: file previously carried Smin = K·Q^−0.46, dropping τ^1.23 (equation is an embedded image with no text layer); simplified form valid only at τ = 1 Pa. "Steeper gradient calculated based on self-cleansing velocity and minimum tractive force methodology shall be adopted as minimum pipe gradient." Apply at network heads where 0.75 m/s unattainable | p27 §4.2.2.1 **[A9, folded]** |
| Design τ value | **GAP-9: GUD-203 gives NO numeric design τ anywhere in §4.2.2** — adopt τ = 1 Pa (Mara et al. literature basis) as a tagged pending assumption, confirm with NWS Hydraulic Team | p27; 05_GAPS GAP-9 — **PENDING** |
| Max velocity | **3.0 m/s** at design depth of flow; max gradient governed by v ≤ 3.0 | p27; p29 |
| d/D at peak flow | ≤ **0.65** for D ≤ 350 mm; ≤ **0.50** for D > 350 mm | p27 Tab 10 |
| Min gradients (secondary network, Colebrook-White @ 0.75 m/s) | DN200: 5.00 mm/m · DN250: 3.75 · DN315: 2.70 · DN400: 2.05 · DN500: 1.55 · DN600: 1.25 · DN700: 1.00 · DN800: 0.85 · **≥DN900: 0.75 mm/m** | p29 Tab 11 |
| No oversizing / uniform slope | no oversizing to obtain flatter slopes; uniform slope between manholes | p29 |
| Construction tolerance | line/level shall not deviate > **20 mm** from contract, and combined deviations shall not create a **reverse gradient**. At DN ≥ 900 (0.75 mm/m min), 20 mm over 120 m spacing eats ~0.17 mm/m ≈ **22 % of available fall** — flat trunk profiles must carry margin | p29 §4.3.1 **[A9, folded]** |
| Early-phase low flows | actual flow in early phases below design flow → clogging risk at low velocity; more frequent inspection/cleansing. Project doctrine: self-cleansing (0.75 m/s / tractive) **verified at start-year flows** | p28 §4.2.6; PROJECT-STATE §2.1 |
| Tertiary vs secondary slopes | Table 11 applies to the secondary network only; tertiary minimums (PCS 3 %, rider/lateral 1 %) are separate and steeper | p18 Tab 5; p29 (02 §2 ★) |

## 5. Loads (flow/load chain — T01 method + PROJECT-STATE §2 doctrine)

| Rule | Value | Ref |
|---|---|---|
| **Two-tier rule (governs everything below)** | Tier A (LPCD ratios 22 %/14 %; returns 85 %/54 %) = planning/forecasting fallback. **Tier B mandatory where detailed land use exists** ("shall"): Tab 12 unit rates for non-domestic/governmental + design flows per **BS EN 752** (standard must be named), with site-specific evidence. **Ibri is Tier B**; W1–W3 used Tier A unlabelled. Every Tier-A number in a deliverable must be labelled fallback with the data request named — **GAP-10 (Tier-B inputs: floor areas/pupils/beds/employees do not exist yet)** | G1-p59–61 §7.3.2–7.3.3; G1-p71 §7.4.1 — **PENDING** |
| Precedence clause | a developer/NWS-approved demand calculation, if one exists, outranks the whole chain | G1-p59 §7.3; G1-p70 §7.4 |
| Domestic per-capita rate | **164 l/c/d** Adh Dhahirah (R0 computes 163.5 — same for practical purposes); measures **network-accounted water only** (excludes tanker/private-well supply); to be validated by NWS before design | G1-p59–60 Tab 11 |
| Occupancy | Population = plots × properties/plot × OR; OR = Population ÷ Housing Units from NCSI at project scale. **GAP-5: OR value open (NCSI housing units missing); fallback OR 6.0** where R0 has no coverage | G1-p58–59 §7.2.2; 05_GAPS GAP-5 — **PENDING** |
| Build-out NOTE (mandatory) | plot subdivision must reflect effective housing units; development percentages must be applied over the design period — raw plot count × OR at 100 % build-out is **non-compliant for dated-year population**. (The saturation doctrine below applies to the ultimate/pipe-sizing horizon, not dated years — keep the distinction explicit) | G1-p59 NOTE |
| Wastewater return rates | domestic & tanker **85 %**; non-domestic & governmental **54 %** (Tier-A baseline wording) → per-capita WWG ≈ **171.3 l/c/d** area-average; residential-only branch = 164 × 0.85 = **139.4 l/c/d** | G1-p70–71 Tab 19; T01 Step 3 |
| Non-domestic Tier B unit rates (Tab 12) | educational 130 l/d per pupil+staff; hospital 650 l/d per bed+staff; commercial shopping 12.2 l/d/m²; hotels 200–500 l/cap/d; office 93 l/d/employee; restaurant 7.4 l/d/m²; mosques 185 l/d/m²; wet industry = **no unit rate** (developer supplies); dry industry 93 l/d/employee; army camps 185 l/d/occupant; prisons 185 l/d per **prisoner + staff**. Rates keyed to **floor area/pupils/beds/employees — NEVER plot area** (Ibri check: mosque plot-area substitution errs by ~4× the whole STP flow). Use Tab 12 **or** the ratios, never both | G1-p61 Tab 12 |
| Governmental | Tier B: calculated specifically for the project, "not as a ratio of domestic consumption"; Tier-A fallback +14 % | G1-p60–61 §7.3.3 |
| Special consumption | labour camps, high-water-use industry: developer-provided, **additive** — never inside the 22 %/14 % | G1-p61 §7.3.4 |
| Spatial allocation (project deviation) | 164 l/c/d on residential population; ND+Gov volume concentrated onto non-residential plots by area (Tab 12 quantities once received) — total preserved, zones shift −16.8 % to +127.2 %. **Flag as deviation; obtain NWS concurrence** | G1-p59 §7.3.1 + W3 A7 — **PENDING** |
| Infiltration | **new networks 720 L/d per km of sewer**; existing inland 10 % of WW; GW-table/coastal up to 40 %; no stormwater; **tanker/vacuum-collected flow carries NO infiltration**. It is a **pipe load** (assign per pipe in SewerGEMS, not at STP gate); [Likely] added unpeaked — add-order not settled by GUD-201, confirm at kickoff. R0 uses 10 % — reconcile (GAP-11 confirmations) | G1-p72–73 §7.4.3 — **PENDING (basis + add-order)** |
| Peak factor — primary | **Merrimack Qpdf = 2.65·Qadf^0.879** (both Ml/d) — "is to be used" (mandatory) for catchment **>100 properties**; no formula prescribed ≤100 properties | G1-p71 §7.4.2 |
| Peak factor — alternative | Peltier (IMP2024) **PfWW = 1.5 + 1/√Qm**, Qm in **l/s**. The two disagree (worked example 1.72 vs 2.48) — binding choice = NWS kickoff item (GAP-11 confirmations) | G1-p72 — **PENDING** |
| PF cap | hourly PF ≤ 5.0 is a **recommendation**, not an absolute limit — do not silently truncate | G1-p72 NOTE **[A9, folded]** |
| R0 +20 % weekly peak | carried a water-side peak-week concept into the WW chain on top of Peltier — **peaking twice; needs NWS ruling** | 02 §12c — **PENDING** |
| Other water sources (binding) | Designer **shall** assess private wells/providers/non-network abstractions for WW contribution; Adh Dhahirah blue-tanker water = **333 % of network domestic consumption** → network-demand-derived WW under-predicts. **GAP-11** | G1-p70 §7.4; G1-p62 Tab 13 — **PENDING** |
| Yellow tankers | ~17 % of NWS STP inflow (2024, company-wide observation — not a per-STP allowance); collection capacity assumes water-supply coverage, 100 % by end of planning period; tanker loads higher-strength (STP process issue) | G1-p73 §7.4.4 |
| Organic loads | BOD₅ ≥ **60 g/cap/d**; TSS **80 g/cap/d**; COD/BOD 1.8–2.2 domestic; concentration always derived C = load/Q (expect BOD ≈ 300–400 mg/l here) | p74; T01 Step 7 |
| **Saturation-load doctrine (settled, binding)** | *plots at saturation size the pipes; capped-and-spilled zone totals at dated years size the STP phases; the two meet only at trunk nodes.* Pipes/buried civil: EVERY plot (built + future + unparceled buildings) at full saturation load (properties × OR × 171 l/c/d) accumulated with PF, no timing. Dated years: zone totals only, R0 projection capped at zone ceiling, surplus spills to adjacent zones by vacancy (A2). Phased elements = M&E (~20 yr). **CLASS=A farms carry NO sewage load** (they are TE customers). Stub-outs DN200 min. Early-years self-cleansing check at start-year flows | PROJECT-STATE §2 (user-agreed 2026-08-15) |
| Flow uses | gravity pipe sizing on peak (hourly) flow with d/D and velocity limits; STP hydraulics on PHF, biology on AAF+load; STP inflow = Qadf + tankers + 10 % operational allowance | T01 Step 8–9; p65–66 |

## 6. Layout-in-road rules

| Rule | Value | Ref |
|---|---|---|
| Min horizontal clearance to other utilities | **3 m**; if same trench, other utility on a separate bench on undisturbed soil | p33 §4.6.3 **[A9 adds bench clause]** |
| Service corridor widths | DN200–500: 2.0 m; 600–900: 2.8 m; 1000–1200: 3.2 m; 1400–1700: 4.0 m; 1800: 4.1 m; 2000–2400: 4.4 m. Conditions (A9): widths are **indicative**, dictated by manhole size, gravity sewers only; force-main corridors case-by-case (valve chambers); allow temporary construction space; no class for 1300/1900 mm (**source gap — interpolate/confirm with NWS**) | p32–33 Tab 13; p35 Tab 15 **[A9]** — partly **PENDING** |
| Position in carriageway | outside of mains in the **vehicle carriageway (not footpath)**, ≥ 1 m from kerb line; manholes ≥ 0.5 m from kerb — stated for **force mains** (§8.2.2); **no gravity-specific in-road position rule exists in 02** — treat gravity application as an assumption or re-extract | p51 §8.2.2 — flag context |
| Straight runs | explicit "shall be laid in straight lines" exists only for force mains (p51); for gravity, straightness between manholes is implied by manhole-location rules (MH at every change of grade/diameter/direction/junction) + uniform slope between manholes — **no verbatim gravity straight-run clause in 02** | p29–30; p51 — flag |
| Road crossings | trenchless "wherever possible"; open-cut only exceptional; reinstatement per Oman Highway Design Manual; trenchless generally only "where excavating the trench is not feasible", NWS approval; at major road crossings approval by NWS AND concerned authorities; settlement decisive | G1-p85 §9.1–9.2; p21; p35 **[A9]** |
| Dual carriageways | two parallel polylines collapse to a single routing corridor; a trunk never runs twice along one road — **project working rule, not PAM** | CLAUDE.md rule 7 |

## 7. Other 02 rules constraining network geometry/sizing

| Rule | Value | Ref |
|---|---|---|
| Wadis | pipelines AND chambers prohibited in wadis/flood-prone/washout areas | p30 §4.4.1; p33 |
| Wadi crossings (when unavoidable) | DI over crossing length **+15 m each side**, mechanical/detachable joints; protection per PAM-STD-404; anti-flotation check (empty pipe, flood/high GW); cover min **2.0 m in soft soil**; isolation + air valves both sides, washout at low point one side; **no chambers/markers in wadi bed or embankments**, all accessible during flood; data + approvals from CAA & MoAFWR (flood frequencies 1:20/1:50/1:100) | G1-p85–86 §9.3 (02 §11b) |
| Inverted siphons | **"Inverted siphons shall not be allowed"** (p182) — stronger than scope-TOR "avoid where no other feasible means"; any siphon = formal deviation needing justification (§1.1 p9); if ever adopted, self-cleansing must be verified at ALL flows | p182 §11.5.3.1(c); scope p12(60) **[A9]** |
| Odour/H₂S — designer deliverable | dedicated H₂S management evaluation to NWS (preventive: re-sizing, chemical injection; corrective: monitoring, flushing, coatings, odour treatment) | p162 §11.1 |
| Network design for odour | retention times minimised, turbulence avoided, **no over-sizing of trunk sewers** (deposition); consider parallel smaller-diameter sewers for low-flow conditions — directly relevant to trunk sizing at 2030-era low flows | p166 §11.3.2; p168 §11.4.2 **[A9 adds parallel-sewer clause]** |
| Septicity risk assessment | qualitative Fayoux scoring (0–5 none / 5–10 low / 10–30 significant-certain, at max temperature and night-time flow); quantitative Pomeroy-Parkhurst, EBOD = BOD₅ × 1.07^(T−20) | p185 Tab 99; p186 §11.5.3.4 |
| Network emergency overflows | retention basins **24 h nominal flow** (emptied by yellow tanker); relief sewers **1.5 × nominal flow** — distinct from STP 48–72 h lagoon | p191 §12.1.1 |
| Air vents on gravity network | min **150 mm** dia, min **6 m** above ground, UV-resistant cap; empirical per-point venting approach (airflow models unreliable) | p32 §4.5 **[A9-only — absent from 02]** |
| Force-main termination into gravity | discharge at a manhole, entering ≤ **300 mm above receiving MH flow line**; water seal + forced venting where turbulent; corrosion-resistant/lined receiving manhole — fixes geometry at every SLS discharge point | p55 §8.5 |
| PS avoidance principle | PS and pressure mains avoided wherever gravity is feasible and cost-effective | p181–182 §11.5.3.1 |
| Remote areas | settlements ~≥25 km from centralized networks, OR <500 residents / <100 plots at end of design period → on-site solutions (septic/holding tanks/package plants 50–5,000 inhabitants), not network — interacts with rule 9 (absorb pockets <50 plots) | G1-p80 §8.1; p83–84 §8.4 |
| Trade effluent | non-domestic discharges comply with Appendix 3 of RD 115/2001; NWS agreement per AM-PRO-209; NWS-validated pre-treatment if needed | p20 §3.10 |
| Deviation governance | any deviation from criteria "shall be justified and substantiated by a detailed analysis" | p9 §1.1 **[A9 note]** |
| Model calibration (SewerGEMS deliverable) | WaPUG/CIWEM CoP + EPA SWMM methodology; calibration: peak flow ±10–15 %, volume ±15 %, correct peak-arrival timing, pump runtime ±10 %; static/EPS/surge models submitted after **each** design phase incl. as-built | G1-p144–145 Tab 32; p109 §13.4.2 |
| Survey grade constraint | preliminary/concept topo accuracy 0.25–1.0 m H / **0.05–0.5 m V** required — the 5 m DTM (and the new 0.5 m blend) is feasibility-grade for invert/slope claims near the 0.75–1.0 mm/m minimum gradients; geotech: trial trench/borehole every **100 m** (secondary/tertiary), **500 m** (primary + FM); boreholes 5.0 m below pipe invert | G1-p36 Tab 5; G1-p40–41 Tab 7; p199 §13.4 |
| Vacuum systems (screening) | restricted to specific cases; DN90 = interface valve only (6 m); caps: main ≤3,000 m, lift ≤4.5 m, ≤5 mains/station, ≤80 L/s/station, min slope 0.2 % | p56–62 Tab 26 **[A9]** |

## Rules 02 explicitly marks PENDING / GAP (gravity-network-relevant)

| Tag | Item | Disposition |
|---|---|---|
| GAP-9 | design tractive tension τ — no numeric value in GUD-203 §4.2.2 | adopt τ = 1 Pa tagged, confirm with NWS Hydraulic Team |
| GAP-5 | occupancy rate / properties-per-plot (NCSI housing units missing) | OR 6.0 fallback; A7 refinement: request *persons per built plot* ≈ 6.0–6.96 as a product |
| GAP-10 (2026-08-17 set) | Tier-B inputs (floor areas, pupils, beds, employees) for Tab 12 unit rates | Tier-A 22 %/14 % as labelled fallback; NWS must formally accept |
| GAP-11 (2026-08-17 set) | non-network water sources (tanker 333 %, private wells) unassessed → WW under-prediction | flag all pre-2026 flows as network-basis only |
| GAP-11 (older set) | NWS kickoff confirmations: infiltration basis (720 L/d/km vs R0 10 %), peaking formula per element (Peltier vs Merrimack), tanker catchment (25 km vs 150 km observed), model start year | design basis = guideline values, R0 as sensitivity |
| GAP-12 | NCSI extrapolation >10 yr beyond forecast (R0 runs to 2100) | ultimate defended on land capacity, not the curve |
| — | infiltration add-order (before/after PF) not stated in GUD-201 | [Likely] unpeaked; confirm at kickoff |
| — | R0 +20 % weekly peak = double peaking | NWS ruling |
| — | spatial concentration of ND+Gov load = project deviation | NWS concurrence |
| — | corridor width: no class for 1300/1900 mm; PVC-U 250 vs 315 cap | interpolate/confirm with NWS |
| — | GAP numbering collision: 05_GAPS carries two GAP-9/10/11 sets (cadastre/boundaries/confirmations vs τ/Tier-B/non-network) — cite by description, not number alone | housekeeping flag |

## ABSENT from 02 (needed for gravity network design; treat as explicit assumptions)

| Missing rule | Note |
|---|---|
| Manhole internal sizes (min diameter vs depth and vs pipe diameter) | no table anywhere in 02; only 1.5 m internal-backdrop threshold + HCC dims exist. GUD-203 §4.4 presumably has it — re-extract before W4 |
| Rider sewer discharge point (to lateral? to manhole?) | only "up to ~3 HCC per rider" extracted |
| Gravity-sewer in-road position (kerb clearance, carriageway side) | only the force-main clause (p51) exists; gravity application is an inference |
| Explicit straight-run-between-manholes clause for gravity sewers | implied by MH-location + uniform-slope rules only |
| Vertical clearance gravity sewer vs other utilities (esp. water mains) | 02 has only the force-main 450 mm outside-to-outside cross-under rule (p51) |
| Air vent spacing/frequency on gravity network | geometry given (150 mm / 6 m, A9), spacing "empirical per-point" — no number |
| Minimum drop across manholes at junctions / through-MH invert losses | not in 02 |
| Manhole cover class / frame rules by location | not in 02 (detail design) |
| BS EN 752 design-flow parameter values | the route is mandated (G1-p71) but no parameters extracted — the standard itself must be sourced for Tier-B flows |
| Design flow formula for catchments ≤100 properties | GUD-201 prescribes none (A9 verbatim finding) — relevant to rider/lateral/small-branch sizing |

## A9 amendments still NOT folded into 02 (use A9 wording in synthesis)

PCS 50 m length limit · PCS 1.5 m depth cap · HCC chamber types/depths · backdrop internal-only-on-existing-MH condition · five prohibited-location zones (b–e) · min-cover-above-protection measurement + major-road check · same-trench bench exception · PVC-U 250/315 cap + Tab 7 matrix · corridor-width caveats · gravity air vents · benching smooth transitions. Everything else gravity-relevant from A9 (τ^1.23, 20 mm tolerance, tertiary slopes, early low flows, odour chapter, modelling/workflow) was folded into 02 on 2026-08-17.

**File paths:** `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\_BRAIN\02_DESIGN_CRITERIA.md` · `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\_BRAIN\07_PROJECT_STATE.md` · `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\TUTORIALS\T01_Sewage_Flow_and_Load_Calculation.md` · `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W3\analysis\A9_criteria_audit.md` · `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\_BRAIN\05_GAPS.md`