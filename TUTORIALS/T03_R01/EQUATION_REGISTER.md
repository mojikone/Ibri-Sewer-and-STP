# Equation register — verified source of every formula in T03

**Guidelines** PAM-GUD-201 (152 pp), -202 (177 pp), -203 (201 pp), all **Rev. 01, March 2026**. The filenames say "v1.0"; every page header says Revision 01 — cite as Rev. 01.
**Page numbering** printed page = PDF page in all three.
**Verification** every equation below was re-rendered from the PDF as an image and read visually. Text extraction mangles fraction bars, radicals and exponents, and three equations exist in the PDF **only as raster images** and are invisible to any text-based search.

---

## PART 1 — Equations that EXIST in the guidelines

### Population and demand

| # | Equation | Source | Notes |
|---|---|---|---|
| 1 | `Population = Plots × Properties per plot × Occupancy rate` | G201-p58 | one of three permitted approaches |
| 2 | `Occupancy Rate = Population / Housing Unit` | G201-p58 | *"must be derived from official data provided by NCSI"* |
| 3 | `LPCD = Total Domestic Water Accounted / (OR × Active Domestic Accounts)` | G201-p60 | the derivation behind Table 11, not a routine design step |

### Peak factors

| # | Equation | Source | Unit trap |
|---|---|---|---|
| 4 | `Q_pdf = 2.65 · Q_adf^0.879` (Merrimack) | G201-p71 | **Ml/day both sides.** Mandatory for catchments over 100 properties |
| 5 | `Pf = Q_pdf / Q_adf` | G201-p71 | dimensionless |
| 6 | `Q_pdf = Q_adf × Pf_WW` | G201-p72 | **m³/d** — different units from eq 4, one page apart |
| 7 | `Pf_WW = 1.5 + 1/√Q_m` (Peltier) | G201-p72 | **Q_m in l/s.** See defect D1 |
| 8 | `P_HF = Q_max.hr / Q_avg` | G201-p63 | water side |
| 9 | `P_DF = Q_max.day / Q_avg` | G201-p63 | water side |

### Gravity sewer hydraulics

| # | Equation | Source | Notes |
|---|---|---|---|
| 10 | `V = -2√(2gDS) · log₁₀[ k_s/(3.7D) + 2.51ν/(D√(2gDS)) ]` (Colebrook–White) | G203-p24 | **k_s = 1.5 mm mandatory**, all sizes and materials; ν = 1.141×10⁻⁶ m²/s at 15 °C |
| 11 | `Q_o = V × A` | G203-p24 | **source prints V / A — see defect D2** |
| 12 | `Q_p = Q / Q_o` | G203-p24 | proportional discharge |
| 13 | `v = (1/n) · R^(2/3) · S^(1/2)` (Manning) | G203-p25 | permissive: *"can be used"* |
| 14 | `S = v²n² · 6.3448 / D^1.333` | G203-p25 | full-bore only; see defect D3 |
| 15 | `Q = (1/n) · R^(2/3) · S^(1/2) · A` | G203-p25 | |
| 16 | `τ = W·sin(θ) / (p·L)` (tractive tension) | G203-p26 | **raster image only** |
| 17 | `W = ρ·g·a·L` | G203-p26 | companion to 16 |
| 18 | `S_min = K · τ^1.23 · Q^(-0.461)` | G203-p27 | **raster image only.** K = 2.33×10⁻⁴ (Q in m³/s) or 5.5×10⁻³ (Q in l/s). Assumes d/D = 0.2, n = 0.013. **See defect D4** |

### Screening

| # | Equation | Source | Notes |
|---|---|---|---|
| 19 | `H_L = β · (w/b)^(4/3) · h · sin θ` (Kirschmer) | G203-p104 | source prints the exponent flat as "1.33"; it is 4/3 |

### Pumping and force mains

| # | Equation | Source | Notes |
|---|---|---|---|
| 20 | `V = 0.25 · Q · T` (wet well live volume) | G203-p48 | single constant-speed pump. T = 3600/starts per hour; **minimum 10 starts/h up to 30 kW** |
| 21 | `NPSHa = Ha − Hvpa − Hst − Hf` | G203-p47 | no units, no sign convention given. Margin ≥ 1 m |
| 22 | `ΔH = (c/g) · Δv` (Joukowsky) | **G201-p146** | not in G202 or G203 — G202 §10 is a one-line cross-reference |
| 23 | Pipeline emptying time | G201-p144 | **dimensionally inconsistent as printed — see defect D5.** Guideline calls it a quick check only |

### Sulphide

| # | Equation | Source | Notes |
|---|---|---|---|
| 24 | `dS/dt = 3.23·M'·[EBOD]·r⁻¹ − 2.1·N·(s·v)^0.375·[S]·d_m⁻¹` (Pomeroy–Parkhurst, gravity) | G203-p186 | only 2 of 9 symbols carry units. **No diameter limit — the "800 mm" premise is not in the guideline** |
| 25 | `EBOD = BOD × 1.07^(T−20)` | G203-p186 | |
| 26 | `S = K_s · BOD₅ · t · f(T)` (force mains) | G203-p186 | **unusable as printed** — K_s has no value or unit, f(T) has no form |

### Process and product ratios

| # | Relation | Source |
|---|---|---|
| 27 | `Q_TSE = 0.95 × Q_STP,inlet` | G201-p73, p75 |
| 28 | TSE network loss = 10 % of TSE produced (**"shall"**) | G201-p76 |
| 29 | Sludge = 0.25 kg/m³ × inlet volume | G201-p78 |
| 30 | `Aerated biomass = Total biomass × aerated fraction of SBR cycle` | G203-p94 |
| 31 | `Total N = Org-N + NH₃ + NH₄ + NO₂-N + NO₃-N` | G203-p71 |

---

## PART 2 — Formulae that do NOT exist in the guidelines

**Citing any of these to NWS would be a fabricated reference.** Each must be attributed to the standard source named.

| Missing formula | Attribute instead to | What NWS does supply |
|---|---|---|
| Net Present Value | ISO 15686-5 / standard finance | discount rate 5 %, horizon 25 yr (G201-p95–96) |
| Life cycle cost | ISO 15686-5 | the cost-stage scope list (G201-p96) |
| Carbon footprint | ISO 14064 / GHG Protocol (as G201-p99 directs) | units tCO₂e/yr and /m³; benchmark 1.17×10⁻³ tCO₂e/m³ TSE |
| MCDA weighted score | designer's own, agreed with NWS | criteria list and weights set by NWS (G201-p105) |
| Total dynamic head | standard hydraulics | component list in prose only |
| Pump power / brake power | standard hydraulics | no efficiency assumption given |
| Darcy–Weisbach | standard form | **named** and its ε tabulated (G202-p104), never written |
| Hazen–Williams | standard form | **named** and its C tabulated, never written |
| Wave celerity *c* | Korteweg | described qualitatively only |
| Mass load `kg/d = Q × C / 1000` | standard | per-capita loads and concentrations given, never the equation |
| Oxygen demand, SRT, clarifier area, sludge yield from BOD | **Metcalf & Eddy / DWA (ATV)** at concept and preliminary; **IWA models** at detailed design — G203-p75, p102 | ranges to land inside, in tables |
| Surge vessel volume | — | only "minimum 20 % allowance" (G201-p147) |
| Emergency storage at a pumping station | — | **no duration, no method.** Designer proposes, NWS approves |
| Minor loss coefficients | — | required to be considered, none tabulated |
| Roughness for a **raw sewage** force main | — | G202 Table 21 is potable/TSE only; its 30 %/10 % derating covers TSE only |
| Aquifer recharge criteria | — | **absent from all three documents.** State the gap |
| MD 145/93 Table 2 sludge heavy metals | the Ministerial Decision itself | referenced, not reproduced |

---

## PART 3 — Defects in the guidelines

Each was verified at the source page. Reproduce the guideline's value where the tutorial quotes it, and flag; never silently repair.

| # | Defect | Page | Handling |
|---|---|---|---|
| D1 | **Peltier numerator is `1`, not the classical `2.5`.** Verified at 600 dpi, by vector span dump, and in the text layer | G201-p72 | Print as the guideline prints it. Query NWS |
| D2 | **`Q_o = V / A`** — dimensionally impossible, yields m⁻¹s⁻¹ | G203-p24 | Use `Q_o = V × A`, note the typo |
| D3 | Manning constant **6.3448** vs exact 4^(4/3) = 6.3496 (0.08 % low) | G203-p25 | Quote 6.3448, footnote the exact value |
| D4 | **No value of τ in pascals exists** in G203 (201 pp) or G201 (152 pp). The tractive-force method is mandatory and not executable from NWS documents | G203-p26–27 | State the gap. Do not import an outside value as NWS-sanctioned |
| D5 | Pipeline emptying-time equation evaluates to m¹·⁵·s², not seconds | G201-p144 | Quote verbatim with the caveat; the guideline itself mandates a transient model |
| D6 | **Adh Dhahirah tanker ratio 333 %** is arithmetically impossible — implies ~9,400 people in the governorate | G201-p62 | Volumes column is sound; the ratio is not. Query NWS |
| D7 | Tables 17 and 19 disagree on Type 3 duty pumps (3 vs 2) | G203-p40 vs p42 | Flag; Table 17 is the conservative reading |
| D8 | Fayoux H₂S risk bands overlap (10–30 "significant", 20–30 "certain") and nothing covers > 30 | G203-p185 | Reproduce verbatim, flag |
| D9 | Aerobic digestion: text requires SRT ≥ 45 d; its own Table 77 gives 10–15 d | G203-p146 | Text governs; note the conflict |
| D10 | Final clarifier surface loading 1.0–1.4 m/h (= 24–34 m³/m²·d) contradicts the overflow rate 16–28 m³/m²·d, both "at average flow" | G203-p124 | Reproduce both, flag |
| D11 | Chlorine residual *"shall be at least between 0.3 and 1.0"* — self-contradictory | G203-p71 vs p130 | 0.3–1.0 at the consumer end; up to 3.0 at the STP discharge |
| D12 | OSEC free chlorine *"> 0.06 mg/L"* — four orders of magnitude out | G203-p132 | Report, do not use |
| D13 | Air valve size bands overlap (300 in two rows) and gap (500–600 missing) | G203-p53 | Reproduce as printed |
| D14 | Washout size bands overlap (1200 twice) and gap (400–500, 800–900) | G203-p54 | Reproduce as printed |
| D15 | Package plant peak factor 3.0 attributed to G201, which never prints 3.0 | G203-p96 | Unreconciled cross-reference. Query NWS |
| D16 | Trunk main *"Length above 1,000 mm without connexions"* — units typo for metres | G203-p35 | Quote with [sic] |
| D17 | Motor *"service factor minimum of 1.15%"* — spurious percent sign | G202-p96 | 1.15 intended |
| D18 | *"AM-GUD-201"* / *"AM-GUD-202"* for PAM-GUD-201/-202 | G203-p65, p51 | Typos |
| D19 | Table 63 preceded by an orphan caption reading "Table 58" | G203-p124 | Numbering defect |
| D20 | Tanker discharge cross-references point to §10.6.4 and §10.6.3; the actual section is **§10.6.2** | G203-p73, p83 | Two wrong internal references |
| D21 | Primary settler detention "1.2" with no unit | G203-p119 | Read as 1.2 h from the companion row; state the inference |
| D22 | Table 2 header row collapsed to zero height, invisible in the page image | G201-p19 | Recovered by coordinate-level character extraction |
| D23 | Table 2 "Field Investigations for risk identification" — Detailed cell genuinely blank | G201-p19 | Reproduce as blank |
| D24 | Value Engineering timing: Table 27 says Concept; Table 2 says Detailed only | G201-p93 vs p20 | §11.3.2 supports Table 27. Flag |
| D25 | EIA timing: Table 2 says scoping at Preliminary; §6.1.4.3 says full EIA at concept/preliminary | G201-p19 vs p44 | Large cost and programme difference. Query NWS |
| D26 | Two undefined asterisks — Table 12 header, and `*Q_adf` on p71 | G201-p61, p71 | No footnote exists anywhere |
| D27 | Design life 20 yr (mechanical installation) vs 15 yr (pump service rating) | G203-p38 vs p40 | Different things; state both with context |
| D28 | "Nominal flow" undefined for retention basin (24 h) and relief sewer (1.5×) | G203-p191 | Query NWS |

---

## PART 4 — The findings that change the Ibri design

**1. Table 11's minimum gradients are FULL-BORE values.** Reproduced independently: all nine rows return 0.75 m/s full bore to within ±1.9 % using Colebrook–White at k_s = 1.5 mm and 15 °C. The guideline separately requires 0.75 m/s **at peak flow**. Part-full velocities at a Table 11 gradient:

| d/D | velocity | verdict |
|---|---|---|
| 0.65 (≤ 350 mm, mandated) | 0.82 m/s | passes |
| 0.50 (> 350 mm, mandated) | 0.75 m/s | passes with **no margin** |
| 0.30 | 0.58 m/s | fails |
| 0.20 | 0.46 m/s | fails |

Laying to Table 11 is therefore not, by itself, compliance — and in early years every pipe falls below the threshold. This is the quantitative basis for the maintenance washing schedule.

**2. Total Nitrogen < 15 mg/L as N** (G203-p71) is an NWS overlay on MD 145/93, which carries no TN limit. Class A alone would permit roughly 21 mg/L. **Full nitrification–denitrification is therefore mandatory**, and TN, not BOD or SS, drives process selection and SRT.

**3. Ibri STP is designated as Adh Dhahirah's sludge treatment centre** — Table 67, G203-p136: *"STC – composting in Ibri STP"*. The plant is the governorate's sludge centre, not merely a producer, with land, buffer and access consequences. Be'ah's landfill route needs **80 % DS**, which no mechanical dewatering in the guideline reaches (best case 40–45 %), so drying or composting is effectively forced.

**4. At roughly 49,700 m³/d ultimate, Ibri is a "Large STP" (≥ 20,000 m³/d).** That single classification changes four things: the residential buffer becomes **300–1000 m set by the 5 OU/m³ dispersion contour** rather than a flat 500 m; **CFD modelling becomes mandatory** unless the TOR excludes it; the chlorine contact tank is replaced by a **TSE storage tank acting as contact tank**; and organic peak factors drop to **1.2 for BOD/COD and 1.5 for TKN**.

**5. Wadi discharge, if contemplated, is the most consequential clause in the set.** G203-p72–73: TSE to a wadi that reaches the sea must meet Class A *except* that ammonia, nitrogen and phosphorus take the MD 159/2005 values — dropping total phosphorus from 30 to **2 mg/L** and ammoniacal nitrogen from 5 to **1 mg/L**. That forces enhanced biological phosphorus removal plus chemical polishing.

**6. Pumping stations are to be avoided, and the trigger is cost not depth.** G203-p181: *"The use of pumping stations and pressure mains shall be avoided whenever gravity sewer designs are feasible and cost effective."* The 10–12 m figure is a **recommendation** about **cover**, and the pumping obligation is triggered by *"where the cost of excavation becomes prohibitive"*. The current zero-pumping-station design is what the guideline asks for.

**7. Inlet angles below 90° are prohibited**, stated twice in mandatory voice (G203-p19, p30). The project's 85° deviation is a live non-compliance.
