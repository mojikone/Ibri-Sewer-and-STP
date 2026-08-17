# A9 — PAM-GUD criteria audit record (2026-08-17)

Full row-by-row audit of `_BRAIN/02_DESIGN_CRITERIA.md` against PAM-GUD-201 / 202 / 203.
13 parallel agents: 9 verified existing rows against their cited pages, 4 swept the guidelines
for load-relevant rules the criteria never carried. **145 issues, 50 rows confirmed as written.**

Verdicts: **MISREAD** = value/formula wrong · **INCOMPLETE** = value right, a condition or
mandatory qualifier omitted · **WRONG_REF** = wrong page · **MISSING_FROM_CRITERIA** = rule absent.

Every finding below carries the verbatim source quote it rests on. Items folded into
`_BRAIN/02` on 2026-08-17 are marked ✅; the remainder are recorded here for detail design.

| Verdict | Count |
|---|---|
| MISSING_FROM_CRITERIA | 83 |
| INCOMPLETE | 59 |
| MISREAD | 3 |

---
## v:hydraulics+gradients — 10 confirmed, 3 issues

> Page mapping verified: PDF 1-based page == printed page ("Page 19 of 201" appears on PDF page 19; "Page 27 of 201" on PDF page 27) — no offset. Extraction method: PyMuPDF text layer for pp19-31 plus 150-dpi full-page and 400-dpi cropped renders of pp26-27, because the tractive-force equation exists only as an embedded image with no text layer — this is almost certainly how the original criteria author missed the tau^1.23 term. Secondary observations not warranting rows: (1) p24 requires "official licensed software approved by NWS" while the p28 restatement (§4.2.4) says only "recognised propriety software" — the stricter p24 wording, already in the criteria file, governs; §4.2.4/§4.2.5 are near-duplicate boilerplate of §4.2.1. (2) p25 note that gravity network modelling "will usually be done for the Primary networks; the secondary sewage network can be partially or totally involved" — context only, no numeric criterion. (3) Source-internal inconsistency, not a criteria error: p27 text cites "Figure 4" for the d/D vs q/Q curve but the figure on p28 is captioned "Figure 2". (4) No numeric minimum tractive tension (tau) value exists anywhere in §4.2.2 (pp26-27) — the tau-selection gap flagged in the MISREAD correction is a genuine source gap, not an extraction failure.

### [MISREAD] Min tractive force method Smin = K*Q^-0.46
**Ref:** p27 §4.2.2.1

> Mara, Sleigh, and Taylor (2000) developed the following relationship for minimum slope based on the assumption of d/D = 0.2 and n = 0.013: Smin = K tau^1.23 Q^-0.461 ... tau = Tractive Tension (Pa); Q = Flow (m3/s) and K = 2.33 x 10-4 or Q = Flow (L/s) and K = 5.5 x 10-3 [formula verified from the embedded equation image at 400 dpi]

**Action:** Formula is Smin = K * tau^1.23 * Q^-0.461 (tau = tractive tension in Pa; assumptions d/D = 0.2, n = 0.013); K = 2.33e-4 for Q in m3/s or 5.5e-3 for Q in L/s. The criteria file omits the tau^1.23 term and truncates the exponent (-0.46 vs -0.461). GUD-203 gives NO numeric design tau anywhere in §4.2.2 (pp26-27) — the simplified form K*Q^-0.461 is only valid at tau = 1 Pa (the Mara et al. literature assumption). The design tractive tension must be explicitly selected/justified or confirmed with NWS — tag as a pending assumption per _BRAIN/05_GAPS.md if 1 Pa is adopted. Unchanged and re-confirmed: steeper of the two methods governs ("Steeper gradient calculated based on self-cleansing velocity and minimum tractive force methodology shall be adopted as minimum pipe gradient"), and tractive force applies at network heads where 0.75 m/s is unattainable.

### [MISSING_FROM_CRITERIA] Line/level construction tolerance 20 mm, no reverse gradient
**Ref:** p29 §4.3.1

> The lines and level of any pipeline shall not deviate from that described in the contract by more than 20mm and combination of such deviation shall not create a reverse gradient.

**Action:** Add to section 2: "Line & level tolerance: pipeline shall not deviate from contract line/level by more than 20 mm, and combined deviations shall not create a reverse gradient (p29 §4.3.1)". Material for this project: at DN>=900 the minimum gradient is 0.75 mm/m, so a 20 mm level tolerance over a 120 m manhole spacing consumes ~0.17 mm/m (~22%) of the available fall — flat trunk profiles must carry margin for it.

### [MISSING_FROM_CRITERIA] Low-flow conditions during early periods (clogging risk)
**Ref:** p28 §4.2.6

> During early development phases, the actual flow will usually be below the flow of design inducing risk of clogging due to low velocity. The operator should proceed to more frequent inspections and cleansings during this period.

**Action:** Add to section 1: "Early development phases: actual flow will usually be below design flow -> clogging risk at low velocity; operator should carry out more frequent inspection/cleansing during this period (p28 §4.2.6)". Directly relevant to this project's phased build-out (2030/2055/ultimate model years) and to the existing early-stage self-cleansing check noted in §11 (yellow tankers row).

---
## v:pipes+cover — 4 confirmed, 11 issues

> Page mapping confirmed: PDF 1-based page == printed page ("Page 19 of 201" footer on PDF page 19); no offset. Pages read: printed 17–25 and 30–38 (text extraction via PyMuPDF; the Read tool's PDF renderer is unavailable — pdftoppm missing). Table 7 (p23) is an image with no extractable text; it was rendered at 200 dpi and read visually — matrix content reported in the PVC-U finding. Internal source inconsistency worth flagging at kickoff: Table 4 (p18) gives PCS "150 mm (minimal)" while Table 6 (p22) gives "OD 160 mm (minimal)" — physically consistent (DN150 ≈ OD160 plastic) but the criteria should keep citing Tab 6/OD basis; also Table 6 caps PVC-U at 250 mm for open-trench mains while the Tab 7 matrix allows U-PVC to OD 315 — conservative reading is 250 mm for mains, 315 mm applicability per matrix; confirm with NWS. The asterisk on "Property Connection Sewer*" in Table 6 has no footnote anywhere on p22 (dangling in source). Trunk-main definition source text literally reads "Length above 1,000 mm without connexions" — typo for 1,000 m; criteria's value is the only sensible reading. Corridor width tables (Tab 13 p32–33 and Tab 15 p35) are verbatim-identical; Tab 13 is titled "Minimum Corridor Widths", Tab 15 "Typical Service Corridor Width".

### [INCOMPLETE] Min diameters (Property connection OD160; lateral OD200 max 45 m; main sewer OD200 min)
**Ref:** p22 Tab 6

> Rider Sewer, Property Connection Sewer* | OD 160 mm (minimal) | Open Trench | PVC-U, HDPE ... Lateral Sewer Maximum Length 45 m | OD 200 mm (minimal) ... Main sewer | OD 200 mm (minimal) to 300 mm

**Action:** Property connection & RIDER sewer OD160 min (Tab 6 lists them jointly: 'Rider Sewer, Property Connection Sewer*'); lateral OD200 (max length 45 m, also §3.2 p17); main sewer OD200 min. Note: the asterisk on 'Property Connection Sewer*' has no footnote anywhere on p22 (dangling); Table 4 (p18) gives PCS '150 mm (minimal)' — consistent with OD160 plastic (DN150).

### [INCOMPLETE] Materials, main >=350: GRP, HDPE, lined RCC (open trench); GRP/HDPE (trenchless)
**Ref:** p22 Tab 6; p21 §4.1.1

> Main sewer | 350 mm and above | Open Trench | GRP, HDPE, GRP/PVC, lined Reinforced Cement Concrete (RCC) pipes | Trenchless | GRP, HDPE | Either encased in Concrete or slip lined through sleeve pipe and grouted, or standalone pipe with suitable stiffness. [p21:] Use of alternate materials must be justified and approved by NWS.

**Action:** Open trench: GRP, HDPE, GRP/PVC, lined RCC — criteria omits GRP/PVC. Trenchless GRP/HDPE carries an installation condition: 'either encased in concrete or slip lined through sleeve pipe and grouted, or standalone pipe with suitable stiffness'. Additionally mandatory: 'Use of alternate materials must be justified and approved by NWS' (p21, §4.1.1).

### [INCOMPLETE] Trunk material > 600: GRP, lined RCC, profile-wall HDPE
**Ref:** p35 Tab 14

> Recommended pipe material to be used for trunk mains pipes are given in the following Table 14. Use of alternate materials must be justified and approved by NWS. | Trunk Mains | > 600 mm | GRP, lined Reinforced Cement Concrete (RCC) pipes, Profile-wall HDPE pipes.

**Action:** Values exact, but append the mandatory clause that immediately precedes Table 14: alternate materials must be justified and approved by NWS.

### [INCOMPLETE] Min cover (gravity sewer): 1.3 m to crown; 0.5 m if concrete-protected
**Ref:** p33 §4.6.3

> The minimum depth for sewer pipes shall be 1.3 m to the crown of the pipe. ... If circumstances require installation of a pipe with depth less than 1.3 m above the crown, then concrete protection is required. The minimum cover above the pipe and its protection shall be 0.5 m. A proper design check is required for the pipe at shallow depth beneath the major roads or highways.

**Action:** 1.3 m to crown (shall). If <1.3 m: concrete protection required AND the 0.5 m minimum is measured above the pipe AND ITS PROTECTION (i.e., 0.5 m above the concrete, not above the crown). Also omitted mandatory condition: a proper design check is required for pipe at shallow depth beneath major roads or highways.

### [INCOMPLETE] Min horizontal clearance to other utilities: 3 m
**Ref:** p33 §4.6.3

> Minimum horizontal clearance of 3 m is required. If utilities are in the same trench, the other utility shall be placed on a separate bench on un-disturbed soil.

**Action:** 3 m minimum horizontal clearance; ADD the same-trench exception: if utilities are in the same trench, the other utility shall be placed on a separate bench on undisturbed soil.

### [INCOMPLETE] Service corridor widths (DN200–500: 2.0 ... 2000–2400: 4.4)
**Ref:** p32–33 Tab 13; p35 Tab 15

> Permanent corridor width for gravity sewer is dictated by the size of the sewage manhole. Table 13 presents indicative corridor width for each sewer diameter. ... Permanent corridor widths for force mains for sewage are dictated by the dimensions of valve chambers and will be determined on a case-by-case basis. ... Allocation of reservation for the pipelines should take into consideration the temporary space required for the construction of the pipelines at various depths.

**Action:** All six width values confirmed in both Tab 13 (starts p32, rows 600–2400 print on p33) and Tab 15 (p35). Omitted conditions: (a) widths are INDICATIVE and dictated by sewage-manhole size — gravity sewers only; (b) force-main corridors are excluded — dictated by valve-chamber dimensions, case-by-case; (c) reservation allocation shall also consider temporary construction space at various depths; (d) table has no class for 1300 mm or 1900 mm (source gap — interpolate/confirm with NWS).

### [MISSING_FROM_CRITERIA] PVC-U diameter cap for main sewers (no material row for mains <350)
**Ref:** p22 Tab 6; p23 Tab 7

> Main sewer | OD 200 mm (minimal) to 300 mm | Open Trench | PVC-U (up to 250 mm), HDPE, GRP. [Tab 7 matrix: 'OD over 315 mm' = X for U-PVC, check for GRP and Welded Corrugated HDPE]

**Action:** Add row: Main sewer OD200–300 (open trench): PVC-U up to 250 mm ONLY, HDPE, GRP | p22 Tab 6. Tab 7 pipe-selection matrix (image, p23): U-PVC (SN4–SN8) permitted OD 160–315 mm only, prohibited above OD 315; GRP and welded corrugated HDPE (SN4–SN12) permitted through ND >1000 mm; reference specs PAM-SPC-207 (U-PVC), PAM-SPC-204 (GRP), PAM-SPC-206 (HDPE).

### [MISSING_FROM_CRITERIA] Tertiary network gradients (Table 5)
**Ref:** p18 Tab 5

> Table 5 Typical Pipe Slopes for House Connection, Riders & Lateral Sewers: Property Connection Sewer | Property Connection | 3 % | 10 % ... Rider Sewer | Tertiary Sewage Network | 1 % | 10 % ... Lateral Sewer | Tertiary Sewage Network | 1 % | 10 %

**Action:** Add row: Tertiary slopes — Property Connection Sewer min 3% / max 10%; Rider Sewer min 1% / max 10%; Lateral Sewer min 1% / max 10% | p18 Tab 5. Design trap: criteria §2 (Tab 11, p29) gives 0.5% (5.00 mm/m) at DN200, but a LATERAL at OD200 is governed by Tab 5's 1% minimum — Tab 11 applies to the secondary network, not laterals.

### [MISSING_FROM_CRITERIA] Property Connection Sewer max length 50 m
**Ref:** p18 Tab 4 note

> The length of the PCS should not exceed 50 m in order to allow maintenance. If necessary, a manhole will be added.

**Action:** Add to min-diameters row or as its own row: PCS length shall not exceed 50 m (maintenance); if exceeded, add a manhole | p18 (note under Tab 4). Criteria currently carries only the 45 m lateral limit.

### [MISSING_FROM_CRITERIA] Air vents on gravity network (§4.5)
**Ref:** p32 §4.5

> The design of the vent shall be adapted to the urban area and the surroundings but shall not be less than 150mm and 6m above ground and equipped with a cap made of UV resisting material.

**Action:** Add row: gravity-network vents — min 150 mm diameter, min 6 m above ground, cap of UV-resistant material; empirical (per-point) venting approach recommended since airflow models are unreliable | p32 §4.5. Nothing in criteria §4 or §5 covers venting.

### [MISSING_FROM_CRITERIA] House Connection Chamber type/depth restrictions
**Ref:** p19 §3.4; p31 §4.4.1(i)(b)

> a. Rectangular concrete chambers with internal dimensions of 600 mm x 750 mm, these are usually used for shallow connection with depth not exceeding 1.4 m and are not recommended where chambers are located under the traffic lanes. b. Circular Chambers (Concrete, GRP, HDPE or Polycrete/PRC) with internal diameter of 1.0 m ... depth ranges from 1.0 m to 2.0 m.

**Action:** Add (detail-design row): HCC depth 1.2–2.0 m; rectangular concrete 600x750 mm only for depth <=1.4 m and NOT recommended under traffic lanes (restated as a restricted location on p31); circular 1.0 m dia (concrete/GRP/HDPE/PRC) for 1.0–2.0 m; HCC usually 2.5 m from property boundary in ROW; up to ~3 HCC may share a rider sewer (p17).

---
## v:manholes+wadi203 — 6 confirmed, 6 issues

> Page alignment verified: PDF 1-based page == printed page for PAM-GUD-203 (footer 'Page 29 of 201' on PDF page 29; no offset). Scope ref notation decoded and verified: 'scope p12(60)' = scope.pdf page 12 whose footer reads 'Page 60 of 204' of the tender document — ref is correct. Nuances not raised to findings: (1) Table 12 heading says 'recommended maximum spacing' but the NWS pre-approval sentence makes it effectively binding — criteria row already captures both; (2) manhole locations list: 'At regular spacing on straight pipeline based on maintenance equipment' — the maintenance-equipment basis is rationale, numbers governed by Tab 12; the fifth bullet ('End of each lateral sewer') sits on p30, so a stricter ref for that row is p29–30; (3) Table 27(i) parenthetical '(existing and future sites)' means the flood-operability requirement also binds the EXISTING Ibri STP site — relevant to the phasing decision, quoted in the CONFIRMED finding; (4) p30 §4.4 also requires benching/channels with smooth transitions between inlet and outlet diameters and inverts ('shall') — detail-design level, not added as a criteria row. Out of my assigned rows but noticed in the read pages: §8.2.2 marker posts/tape rules (p51), air valve sizing Tab 24 (p53), washout sizing and isolation-valve 500/800 m spacing (p54), force-main minimum bores 75/50 mm (p50) are absent from criteria §8 — flag to whoever audits section 8.

### [INCOMPLETE] 5. Manholes — Backdrop
**Ref:** p30 §4.4

> Backdrops shall be constructed external to the manhole. Internal backdrops, whilst permissible, shall only be used for new connections to existing manholes where external connections are not practicable. Internal backdrops are not permitted on manholes that are less than 1.5 m in diameter since this would restrict access to an unacceptable degree.

**Action:** required when invert drop > 600 mm; shall be constructed external; internal backdrops permissible ONLY for new connections to EXISTING manholes where an external connection is not practicable, AND never on manholes < 1.5 m dia; max height 2 m (beyond → vortex drop shaft). The criteria's 'internal only if MH ≥ 1.5 m dia' drops the existing-manhole/not-practicable condition — as written it would permit internal backdrops on new manholes ≥ 1.5 m, which the source forbids.

### [INCOMPLETE] 5. Manholes — Prohibited locations
**Ref:** p30–31 §4.4.1

> a. Wadis and Flood-Prone Areas: Locating pipelines and associated chambers in wadis or areas subject to washout during heavy storms must be avoided. b. High-Traffic Areas for Specific Manhole Types: Rectangular concrete chambers (600 mm x 750 mm) are not recommended for use where chambers are located under traffic lanes. c. Electrical Hazards: Infrastructure sites must not be located under electrical power lines. d. Environmental Sensitivity: Overflow points must be positioned strategically to avoid sensitive ecosystems. e. Unstable Ground: Locating infrastructure in unstable or highly erodible seabed areas (for outfalls) or exceptionally weak ground should be avoided.

**Action:** §4.4.1 'Prohibited and Unsuitable Zones' lists FIVE zones, not one. Add: (b) rectangular concrete chambers 600×750 mm not recommended under traffic lanes; (c) infrastructure sites MUST NOT be located under electrical power lines (directly relevant to SLS/manhole siting); (d) overflow points positioned to avoid sensitive ecosystems; (e) avoid unstable or highly erodible ground. Ref should read p30–31 §4.4.1 (items b–e are on p31), p33.

### [INCOMPLETE] 6. Wadi — Twin pipelines for obstacle crossing
**Ref:** p52 §8.2.3

> Designer will be required to conduct a dedicated hydraulic study in order to : ● Ensure the operational modes (1+1 in standby, 2 simultaneously) ● Guarantee the minimum velocity requirement of 0.75 m/s in any case, ● Reduce stagnation time and sedimentation by alternating or flushing, ● Not increase the risk of H2S generation of the flow, [...] Duplication shall be limited to critical lengths if restraints are applied. [...] Space between pipelines shall ensure no interactions.

**Action:** The dedicated hydraulic study has FOUR mandatory objectives, not one: (1) ensure operational modes (1+1 standby, 2 simultaneous); (2) guarantee 0.75 m/s in any case; (3) reduce stagnation time and sedimentation by alternating or flushing; (4) not increase H2S generation risk. Also add: each pipeline mechanically restrained independently (captured); duplication shall be limited to critical lengths if restraints are applied; space between pipelines shall ensure no interactions. Criteria currently lists only the velocity item + restraint.

### [INCOMPLETE] 6. Wadi — Inverted siphons
**Ref:** scope p12(60) clause 12

> This shall be resorted to only where other means of passing the obstruction are not feasible, as they require considerable attention in maintenance (self-cleansing velocity at all flows is very important).

**Action:** Add the design condition attached to the exception: if a siphon is adopted, self-cleansing velocity must be verified at ALL flows (source flags this as maintenance-critical). Ref verified correct: scope.pdf page 12, clause 12 (tender-document footer 'Page 60 of 204').

### [INCOMPLETE] 6. Wadi — Trenchless as alternative at major crossings
**Ref:** p21 §4.1 / p35 §5

> Use of the trenchless technology, as an alternative to the commonly used open trench method, will be employed where excavating the trench is not feasible, based on NWS approval. [...] In major road crossings, possible settlement can be decisive criteria and based on the approval of NWS and concerned authorities.

**Action:** Add the applicability condition: trenchless is employed 'where excavating the trench is not feasible' (not a free alternative), and approval at major road crossings is by NWS AND concerned authorities, not NWS alone. Both p21 and p35 carry identical wording.

### [INCOMPLETE] 6. Wadi — TSE discharge to wadi
**Ref:** p72–73 §10.2.4.3

> Subject to prior agreement with NWS: ● If the Wadi discharges to sea at a reasonable distance, TSE discharged to Wadi's shall conform to the effluent quality given under Class "A" effluent, relating to Ministerial Decision 145/93, with a modification pertaining to ammonia, nitrogen and phosphorus which shall respect the Decision 159/2005 values. ● Any TSE discharged to Wadi's shall conform at least to the effluent quality given under Class "A" effluent, relating to Ministerial Decision 145/93. In any case, TSE discharge to Wadi is subject to the approval of the Environmental Authority and APSR.

**Action:** Add two omitted conditions: (1) the whole clause is 'Subject to prior agreement with NWS'; (2) if the wadi discharges to sea at a reasonable distance, Class A applies WITH a modification — ammonia, nitrogen and phosphorus shall respect MD 159/2005 values (the file's §9 row line 97 has this, but this row omits it). Ref should read p72–73 §10.2.4.3 (clause starts on p72).

---
## v:ps+forcemains — 6 confirmed, 17 issues

> Page parity confirmed: PDF 1-based page = printed page (PDF page 36 footer reads "Page 36 of 201"); no offset. Read tool could not render the PDF (pdftoppm missing) so text was extracted verbatim with PyMuPDF — all quotes are from the extracted text layer. Out-of-scope cross-checks done in passing because the pages were in range: criteria §6 row "Force main cover at wadi crossing 1.5 m (vs 1.3 normal) p52 §8.2.4" is CONFIRMED verbatim ("Without protection: 1.3 m ... With protection: 0.5 m ... At Wadi crossing: 1.5 m (depth to crown of pipe)"), and §6 row on twin pipelines p52 §8.2.3 is CONFIRMED ("Guarantee the minimum velocity requirement of 0.75 m/s in any case ... each pipeline shall be designed to be mechanically restrained independently of the other"), with added source nuances: duplication limited to critical lengths, spacing to ensure no interaction, and no increase in H2S risk. Biggest design-impacting gaps for this project: Table 16 minimum-flow factors (force-main sizing check), Table 17 PS type classification with per-type duty/standby minimums, and Table 21 minimum land areas (SLS plot reservations).

### [INCOMPLETE] §7 Siting (hydraulics-driven; flooded suction; energy-economic study)
**Ref:** p38 §7.2

> the site shall be approved in advance by NWS during the concept/preliminary design stage. Pump pedestal level or building floor, electrical transformers/ pad mounted substation or emergency generator are to be located above maximum flood level, with the floors being a minimum of 300 mm above the 1:50 year flood level.

**Action:** Add to row: PS site shall be approved in advance by NWS during concept/preliminary design stage; pump pedestal/building floor, transformers/substation and emergency generator located above maximum flood level with floors min 300 mm above the 1:50-yr flood level; surface/stormwater management designed for 1:50 ARI; sites under electrical power lines avoided (all p38).

### [INCOMPLETE] §7 Design life (non-structural M&E) 20 years
**Ref:** p38 §7.1 + p40 Tab 17

> Life time for non-structural mechanical installations shall be considered as 20 years. [p38] ... Service rating: 15 years design life [p40 Tab 17]

**Action:** Source wording is 'non-structural mechanical installations' (not M&E), 20 yr (p38). Additionally Table 17 assigns pumps a 'Service rating: 15 years design life' (p40) — the 15-yr pump service rating must appear alongside the 20-yr figure or LCC/replacement planning will use the wrong life for the pumps themselves.

### [INCOMPLETE] §8 Min velocity 0.75 m/s (continuous); 1.0 intermittent; 1.2 vertical
**Ref:** p50 §8.1 + p40 §7.4 Tab 16

> At design minimum flow (that is, maximum static head), a velocity of at least 0.75 m/s shall be maintained for raw sewage ... in the case of intermittent flow, required minimum velocity shall be 1.0 m/s. For vertical force mains, a velocity of at least 1.2 m/s shall be maintained

**Action:** 0.75 m/s is not a 'continuous-flow' figure — it must be maintained AT DESIGN MINIMUM FLOW (i.e. maximum static head). The initial minimum flow used for this check is approximated with Table 16 multipliers (avg flow 50/500/2500/5000 l/s → factor 0.25/0.35/0.45/0.50, p40) and explicitly governs force-main sizing. Intermittent 1.0 m/s and vertical 1.2 m/s confirmed.

### [INCOMPLETE] §8 Separation from water mains: 3.0 m horizontal; cross under, 450 mm vertical
**Ref:** p51 §8.2.2

> Sewage force mains shall cross under the water mains and shall be laid to provide a minimum vertical distance of 450 mm between the outside of the force main and the outside of the water main. At a crossing, one full length of water pipe shall be located so both joints will be as far from the force main as possible.

**Action:** 3.0 m horizontal and cross-under confirmed. Add: the 450 mm is measured OUTSIDE-to-OUTSIDE of the two pipes, and at a crossing one full length of water pipe shall be centred so both its joints are as far from the force main as possible; special structural support for both mains may be required (all shall-clauses, p51).

### [INCOMPLETE] §8 Layout: straight lines; sharp bends avoided; ≥1 m from kerb in carriageway
**Ref:** p51 §8.2.2

> the outside of the mains shall be in the vehicle carriageway (not footpath) and be at least 1 m from the kerb line. The outside of manholes shall be at least 0.5 m from the kerb line. ... Force mains shall be laid in straight lines. Where bends are used, they shall be pre-formed and securely anchored with thrust blocks, if required.

**Action:** Confirmed as far as it goes; add from the same bullet list: outside of MANHOLES at least 0.5 m from the kerb line; where bends are used they shall be pre-formed and securely anchored with thrust blocks; marker tape 300 mm above rising mains (trace wire every ~1,000 m for non-metal mains).

### [INCOMPLETE] §8 Material: DI; stainless steel for PS <100 L/s (in-station pipework)
**Ref:** p52–53 §8.3

> The recommended material for the pipes and fittings within the pumping station shall be Ductile Iron. For small capacity pumping stations (less than 100 L/s), pipe material shall be stainless steel. [p52] The recommended pipe material for the pressure main is Ductile Iron and HDPE. [p53]

**Action:** The row captures only IN-STATION pipework (DI recommended; stainless steel for PS <100 L/s — p52) and omits the force-main pipe material itself: 'The recommended pipe material for the pressure main is Ductile Iron and HDPE' (p53). HDPE is a permitted force-main material and the pressure-main sentence sits on p53, not p52. Split the row: in-station = DI / SS(<100 L/s) [p52]; pressure main = DI and HDPE [p53].

### [MISSING_FROM_CRITERIA] PS type classification and per-type minimum pump numbers
**Ref:** p40–41 Tab 17

> Type 1: Design flow up to 100 l/s. Type 2: Design flow greater than 100 l/s up to 300 l/s. Type 3: Design flow greater than 300 l/s. ... Minimum number of duty pumps 1 / 2 / 3 ... Minimum number of standby pumps 1 / 1 / 1

**Action:** Add: PS Type 1 ≤100 l/s (min 1 duty + 1 standby), Type 2 >100–300 l/s (2 duty + 1 standby), Type 3 >300 l/s (3 duty + 1 standby); pumps duty-rotate each start/stop cycle; station pipework velocity max 2.5 m/s / min 0.6 m/s (0.5 with grinder); max motor speed 1,450 rpm (>5 l/s), 2,800 rpm (≤5 l/s); solids handling min 76 mm (65 mm with upstream basket).

### [MISSING_FROM_CRITERIA] Minimum pump flow factors (Table 16) govern force-main sizing
**Ref:** p40 §7.4 Tab 16

> the initial minimum flow rate shall be considered in sizing the force main so that deposition at low velocity is avoided. Initial minimum flows to be pumped shall be approximated by using the multipliers in Table 16.

**Action:** Add: initial minimum flow = avg flow × Table 16 factor (50 l/s → 0.25; 500 → 0.35; 2500 → 0.45; 5000 → 0.50) and this flow — not average — is the one used to size the force main against deposition at low velocity.

### [MISSING_FROM_CRITERIA] Minimum PS land area per type
**Ref:** p43 Tab 21

> Minimum area of land required 50-100 m2 / 200-400 m2 / ≥900 m2 ... At least 6 m wide turning circle with hard standing for vehicles

**Action:** Add (directly drives SLS plot reservations in concept design): minimum area of land required — Type 1: 50–100 m²; Type 2: 200–400 m²; Type 3: ≥900 m²; access with ≥6 m wide turning circle and hard standing.

### [MISSING_FROM_CRITERIA] Emergency overflow mandatory at all PS
**Ref:** p46–47 §7.5

> All pumping stations shall have an emergency overflow to prevent flooding of pumping station equipment or dwellings connected to the system. ... Overflows are to be approved by the Environmental Authority. Overflows shall not be provided at upstream manholes

**Action:** Add: all pumping stations shall have an emergency overflow (Environmental Authority approval required); never at upstream manholes; wet-well overflow fitted with dip tube/baffle board; storage provided above start level of last duty pump; prevention methods = dual power, trunk/basin storage, emergency storage, emergency pumping.

### [MISSING_FROM_CRITERIA] Wet well active volume and start limits
**Ref:** p48 §7.8

> V = 0.25 QT ... The number of starts per hour for the pump/motor shall be minimum 10 for smaller motors (Up to 30 Kw) ... For large pumping stations flow (0.5 m³/s) and above, Computation Fluid Dynamics (CFD) numerical models and physical models shall be considered.

**Action:** Add: minimum live volume V = 0.25·Q·T (Q single-pump capacity m³/s, T = 3600/starts-per-hour; min 10 starts/h up to 30 kW, NEMA MG 1 for larger); successive pump start/stop levels separated 200–300 mm; 5–10 s start delay; CFD + physical modelling for stations ≥0.5 m³/s.

### [MISSING_FROM_CRITERIA] NPSH margin
**Ref:** p47 §7.6

> NPSH margin of at least 1 meter should be considered for the pump.

**Action:** Add: NPSHa = Ha − Hvpa − Hst − Hf with an NPSH margin of at least 1 m for the pump.

### [MISSING_FROM_CRITERIA] H2S design concentrations at force-main termination
**Ref:** p47 §7.7 + p55 §8.5

> H₂S average concentration between 50 and 100 ppm ... H₂S peak concentration <= 200 ppm

**Action:** Add: where H2S generation is expected and no field data exists, design management/monitoring for avg 50–100 ppm and peak ≤200 ppm H2S at the pressure-main termination (STP or network); H2S monitoring at termination manhole to control chemical injection at force-main start (p55).

### [MISSING_FROM_CRITERIA] Minimum force-main diameter
**Ref:** p50 §8.1

> A force main shall be a minimum 75 mm inside diameter for non-clog pumps and minimum 50 mm inside diameter for grinder pumps.

**Action:** Add: force main minimum 75 mm ID for non-clog pumps; minimum 50 mm ID for grinder pumps.

### [MISSING_FROM_CRITERIA] Pumping mains run full at all times
**Ref:** p51 §8.2.1

> Pumping mains shall be designed to run full and to remain full at all times.

**Action:** Add: pumping mains shall be designed to run full and remain full at all times (profile/air-valve implication).

### [MISSING_FROM_CRITERIA] Force-main valve spacing and sizing rules
**Ref:** p53–54 §8.4

> In-line valves shall be considered in the pumping mains at intervals of about 500 m, but not exceeding 800 m ... the time required to empty the relevant section of main is no longer than 3 to 4 hours ... Air valves are required at high points in the force main, and the approaching gradient shall not be flatter than 1:500, with the gradient from the valve not flatter than 1:300.

**Action:** Add: in-line isolation valves at ~500 m intervals, never exceeding 800 m; washout valves at low points, section emptying time 3–4 h, minimum washout 100 mm (≤400 mm main → 100 mm; 500–800 → 150 mm; 900–1200 → 200 mm; ≥1200 → 300 mm); air valves double-orifice at high points with approach gradient not flatter than 1:500 and departure not flatter than 1:300, each with separate geared isolation valve; sizes per Table 24.

### [MISSING_FROM_CRITERIA] Force-main termination rule
**Ref:** p55 §8.5

> Force mains shall enter the gravity sewer system at a manhole and at a point not more than 300 mm above the flow line of the receiving manhole.

**Action:** Add: force mains shall discharge into the gravity system at a manhole, entering not more than 300 mm above the receiving manhole flow line; water seal + forced venting through odour control where turbulent; corrosion-resistant/lined receiving manhole; vertical bell-mouth termination where possible.

---
## v:stp+vacuum — 4 confirmed, 13 issues

> Page alignment verified: PDF 1-based page == printed page (footer 'Page 54 of 201' at PDF index 53; 'Page 56 of 201' at index 55) — no offset adjustment needed. Table 26 (p60) and Tables 27/28 (p63–64) column structures were double-checked with pdfplumber because plain text extraction interleaves columns; the DN90 row genuinely reads 'flow 1.0 L/s, note: Vacuum interface valve, max length 6 m'. Incidental source defect (not a criteria error): p61 §9.1.6 cross-references 'Table 12 – Maximum Design Flow Rates' for valve-pit capacity, but that table is actually Table 25 (p57) — worth knowing if the report ever cites it. Also incidental: the §6 row 'TSE discharge to wadi | min Class A ... | p73' (outside my assigned lines) shares the same gap as the §9 TSE row — it omits that the MD 159/2005 N/P modification is conditional on the wadi reaching the sea; the finding on 'TSE quality' covers the needed wording for both. All refs in lines 85–100 pointed to the correct printed pages; no WRONG_REF found.

### [INCOMPLETE] Design horizon (STP)
**Ref:** p65 §10.2.1

> Sewage Treatment Plants shall be designed for a design horizon of at least 15 years and shall meet the needs for the projected population. Anticipated capacity for future industrial needs and other institutions shall be taken into account when estimating the design capacity.

**Action:** ≥ 15 yr, projected population + anticipated capacity for future industrial needs AND other institutions

### [INCOMPLETE] Site selection criteria
**Ref:** p63–64 Tab 27

> j — Minimum nuisance / Noise / Odours / Emergency outfall discharge / Treated effluent storage and reuse ... o — Suitable technologies for the local context ... i — Flood considerations (25 and 100 year flood levels, compliance when constructing in flood prone areas) / STPs shall be fully operational during floods (existing and future sites)

**Action:** Add omitted Table 27 criteria: (b) access to sludge disposal points; (g) protection of resources, fish and wildlife; (j) minimum nuisance/noise/odours + emergency outfall discharge + treated effluent storage and reuse; (l) public acceptance/aesthetics; (o, on p64) suitable technologies for the local context. Also (i) includes 'compliance when constructing in flood prone areas', and the flood-operability clause applies to 'existing and future sites'.

### [INCOMPLETE] Flow definitions
**Ref:** p65–66 §10.2.2.1

> Except when stated otherwise in these specifications or instructed otherwise by NWS: ● Hydraulic pass-through process structures are to be sized based on peak hourly flow ● Biological treatment systems are to be sized based on the AAF and the design inlet load. The hydraulic and load design shall include recycled liquors and the received tanker volumes if applicable.

**Action:** Add three omissions: (1) the sizing rules carry an escape clause — 'Except when stated otherwise in these specifications or instructed otherwise by NWS'; (2) 'The hydraulic and load design shall include recycled liquors and the received tanker volumes if applicable' — binding for Ibri where tankers ≈ 17% of STP inflow; (3) a fourth flow is defined: Design Peak Instantaneous Flow (instantaneous maximum flow rate to be received, p66). PHF is also denoted QPDF.

### [INCOMPLETE] COD/BOD domestic
**Ref:** p74 §10.3.1

> Typical COD/BOD ratios for domestic wastewater range from 1.8 - 2.2. Influents with higher COD/BOD ratios are not effectively treatable via biological means due to the high contribution of recalcitrant or refractory organics. These non-domestic volumes shall be considered and a separate treatment line for high-strength wastewater shall be required if volumes are significant.

**Action:** 1.8–2.2 typical domestic; influents with higher COD/BOD are not effectively biologically treatable, and a SEPARATE treatment line for high-strength wastewater SHALL be required if such volumes are significant — directly relevant to Ibri's tanker/septage stream (Table 31 tanker COD up to 5,000 mg/l gives COD/BOD >> 2.2).

### [INCOMPLETE] Emergency lagoon
**Ref:** p73 §10.3.1

> In specific cases, under NWS requirement and approval, an Emergency storage lagoon equivalent to a total of 48-72 hours of the STP capacity can be implemented in the STP for potentially problematic loads (influent or effluent not meeting specifications). Flow in the emergency lagoon is pumped back to the inlet facilities for treatment when capacity becomes available at the STP.

**Action:** 48–72 h of STP capacity, only 'in specific cases, under NWS requirement and approval'; its purpose is holding potentially problematic loads (influent or effluent not meeting specifications) within the tanker/septage provisions, and its content is pumped back to the inlet works when capacity is available. It is NOT a general TSE/emergency storage — not directly comparable with the scope's 5-day storage lagoons (different function; keep both, labelled separately).

### [INCOMPLETE] TSE quality
**Ref:** p72–73 §10.2.4.3

> Subject to prior agreement with NWS: ● If the Wadi discharges to sea at a reasonable distance, TSE discharged to Wadi's shall conform to the effluent quality given under Class “A” effluent, relating to Ministerial Decision 145/93, with a modification pertaining to ammonia, nitrogen and phosphorus which shall respect the Decision 159/2005 values. ● Any TSE discharged to Wadi's shall conform at least to the effluent quality given under Class “A” effluent, relating to Ministerial Decision 145/93. In any case, TSE discharge to Wadi is subject to the approval of the Environmental Authority and APSR.

**Action:** Both wadi-discharge bullets are 'Subject to prior agreement with NWS'. The ammonia/N/P modification per MD 159/2005 applies ONLY 'if the Wadi discharges to sea at a reasonable distance'; otherwise the requirement is 'at least' Class A per MD 145/93, plus EA and APSR approval in any case. Ibri wadis are inland — blindly applying the 159/2005 modification would impose ammoniacal-N 1.0 vs 5 mg/L and TP 2.0 vs 30 mg/L, a much stricter (and unrequired) process duty. Also p69: process shall be capable of Class A or B per MD 145/1993 'or as per the last requirements stated by APSR'.

### [INCOMPLETE] Vacuum systems (§10 line 100)
**Ref:** p56, p60 Tab 26, p61, p62

> The selection of the Vacuum Sewage System should be restricted to very specific cases (small mountainous small networks, ports, flat areas with shallow groundwater table). Implementation decisions must be supported by a comprehensive financial evaluation, including the solution by tanker ... ● No vacuum main length should be greater than 3,000 m ● There should be no more than 4.5 m of lift throughout a single sewer ... ● The number of vacuum mains ... should be limited to five ● The maximum flow at the vacuum station should be limited to 80 litres per second for sewage

**Action:** Add for screening: (1) selection 'should be restricted to very specific cases (small mountainous small networks, ports, flat areas with shallow groundwater table)' and 'must be supported by a comprehensive financial evaluation, including the solution by tanker' over whole-life CAPEX+OPEX (p56); (2) Table 26 DN90 row is the vacuum-interface-valve connection with max length 6 m — not a usable main; intermediate rows DN125 5 L/s/800 m, DN160 10 L/s/1,000 m, DN200 15 L/s/1,500 m; (3) system caps (p60): no vacuum main > 3,000 m, ≤ 4.5 m of lift per sewer, ≤ 5 vacuum mains per station, max 80 L/s sewage per vacuum station, min slope 0.2% (1:500); (4) min partial vacuum 25 kPa at each interface valve, recovery time ≤ 30 min (p61); (5) BS EN 1091 compliance, whole system designed by a single entity (p62).

### [MISSING_FROM_CRITERIA] STP capacity basis = IMP per-capita consumption
**Ref:** p65 §10.2.2.1

> The STP treatment capacity shall be based on the average consumption per capita as specified in the latest updated NWS’ Integrated Master Plan. Exceptions can be accepted by Nama Water Services if a more realistic figure is available and justified by the Designer.

**Action:** Add row: STP treatment capacity shall be based on average per-capita consumption per the latest updated NWS Integrated Master Plan; a more realistic figure is admissible only as an NWS-accepted, Designer-justified exception (p65 §10.2.2.1). Links the STP section to the §11 GUD-201 chain.

### [MISSING_FROM_CRITERIA] Raw sewage characteristics (Tables 30/31)
**Ref:** p67 Tab 30, p68 Tab 31

> The following values are given indicatively and shall be used after agreement with NWS, in case the above data points are not available, or if instructed as so by NWS. ... Sludge liquor returns, side streams and tanker loads are not included in the table above.

**Action:** Add row: influent quality primarily from NWS LIMS data for the catchment; Table 30 default values (BOD5 350–400, COD 700–900, TSS 400–500, TKN 60–80, NH3-N 40–50, TP 10–15 mg/l, T 20–35°C) are indicative and usable only after agreement with NWS when data unavailable; tanker sewage per Table 31 (avg–max: BOD 350–1050, COD 1350–5000, TSS 900–4300 mg/l) — material at Ibri's ≈17% tanker share; sludge liquors, side streams and tanker loads are NOT included in Table 30 and must be added per unit.

### [MISSING_FROM_CRITERIA] Mandatory tanker/septage reception provisions
**Ref:** p73 §10.3.1

> Allowances for septic or leachate to be discharged to the wastewater treatment facility must be accounted for by means of: ○ A dedicated tanker discharge station with proper screening facilities to remove large debris and inorganic materials and oil and grease removal system ... ○ A flow equalization tank specifically for tanker discharge to regulate hydraulic and organic loading into the main treatment process to prevent shock loads

**Action:** Add row: septage/leachate allowances MUST be accounted for by (1) a dedicated tanker discharge station with screening + oil & grease removal, (2) a flow-equalization tank specifically for tanker discharge to prevent shock loads, (3) the 48–72 h emergency lagoon (NWS-approved cases), and (4) operational measures (pre-acceptance sampling, SOPs, traceability records, contractual limits). The criteria file currently carries only the lagoon bullet.

### [MISSING_FROM_CRITERIA] Organic peak factors (aeration / peak O2 demand)
**Ref:** p74 §10.3.1

> ○ Peak Factor for BOD and COD = For small STPs = 1.5; For medium-large STPs = 1.2 ○ Peak Factor for TKN: For small STPs = 2; For medium-large STPs = 1.5

**Action:** Add row: shock/diurnal peaks shall be considered in aeration design; Peak Factor BOD & COD = 1.5 (small STP) / 1.2 (medium–large); Peak Factor TKN = 2 (small) / 1.5 (medium–large); flow/load equalisation to be considered at plants critically affected by surge loadings.

### [MISSING_FROM_CRITERIA] Total Nitrogen limit + chlorine residual at discharge
**Ref:** p71 §10.2.4.1

> The technology selected and designed shall meet the combined concentration of Total Nitrogen limit < 15 mg/L as N. ... chlorine residual concentrations at the STP point of discharge shall be at least between 0.3 mg/L and 1.0 mg/L. Concentrations at the STP point of discharge up to 3.0 mg/L are permitted to allow for degradation in the TSE distribution network.

**Action:** Add row: selected technology shall meet combined Total Nitrogen < 15 mg/L as N (TN = organic N + NH3 + NH4 + NO2-N + NO3-N); chlorine residual at STP point of discharge 0.3–1.0 mg/L minimum, up to 3.0 mg/L permitted to allow decay in the TSE network.

### [MISSING_FROM_CRITERIA] Existing-works organic design basis
**Ref:** p74 §10.3.1

> When an existing treatment Works is to be upgraded or expanded, the organic design shall be based upon the actual strength of the wastewater as determined from the measurements from the Client’s laboratory, with an appropriate increment for growth.

**Action:** Add row: for upgrade/expansion of an existing STP (Ibri has one), organic design shall be based on actual measured wastewater strength from the Client's laboratory (LIMS historic + updated data to be obtained) with an appropriate growth increment — not on the default per-capita loads.

---
## v:demand-chain — 4 confirmed, 7 issues

> Page alignment verified: 'Page 3 of 152' on PDF page 3, 'Page 56 of 152' on PDF page 56 — printed page == PDF 1-based page, no offset; refs need no adjustment. Extraction via PyMuPDF (pdftoppm unavailable on this machine); text layer is clean. Items considered but kept out of the findings list as water-side only, low relevance to the sewer/TE criteria file: §7.3.6 water peak factors + Tables 14/15 EPS diurnal patterns (patterns must be obtained from or validated by the NWS Hydraulic team prior to design — becomes relevant if EPS diurnal curves are used in WaterGEMS for the TE network); §7.3.7 headroom (explicitly applies to strategic transmission/PS/reservoirs/sources only, not distribution); §7.3.8 NRW leakage allowance (higher of 15% of consumption or 10/5 m³/d/km — water networks, does not enter sewer flow). The Adh Dhahirah 333% tanker ratio (finding 11) deserves escalation beyond the criteria file: it interacts with the R0 workbook's 25-km tanker catchment assumption (criteria §12c) and with the yellow-tanker 17% row — the water-balance data implies most domestic water in this governorate arrives by blue tanker, so network-LPCD-based sewage estimates for unconnected/tanker-supplied settlements need an explicit position at kickoff.

### [INCOMPLETE] Population from plots (line 105)
**Ref:** G1-p59 §7.2.2 NOTE

> NOTE: When applying this methodology, special care must be given in cases of plot subdivision, to ensure that population estimates properly reflect the effective number of housing units created. In addition, development speed must be considered through appropriate phasing assumptions, as not all plots will be developed simultaneously. Coverage will be estimated using planning data and land use typologies, and development percentages must be applied over the design period to reflect realistic build-out scenarios and particularly avoiding overestimation.

**Action:** Formula and NCSI occupancy source correct, but ref should be G1-p58–59 (equation p58; NCSI derivation sentence and NOTE are p59) and the mandatory §7.2.2 NOTE is omitted. Add: 'NOTE (G1-p59, mandatory): in plot subdivision cases, population must reflect the effective number of housing units created; development phasing must be applied — development percentages over the design period per planning data and land-use typologies, to avoid overestimation. Raw plot count × occupancy with 100% build-out is non-compliant.'

### [MISSING_FROM_CRITERIA] §7.2.1 Population from NCSI — distribution and extrapolation rules
**Ref:** G1-p58 §7.2.1

> If population forecast data is only available at the Wilayat level and not at the Settlement level, a distribution of the forecasted figures must be carried out. This distribution should be based on the proportion of population recorded in the latest census at the Settlement level. […] Statistically, it is not recommended to extrapolate more than ten years beyond the available forecast period due to increased uncertainty, especially when current international forecasts foresee a worldwide fall in birth rates.

**Action:** Add row: 'NCSI forecast handling (G1-p58 §7.2.1): wilayat-level forecasts must be distributed to settlements pro-rata to latest-census settlement population; sub-settlement areas pro-rata by electricity accounts (provided by NWS); NCSI horizon is 20–25 yr — beyond it use polynomial regression, but extrapolating more than 10 years past the available forecast period is not recommended.' Directly relevant: model years run to 2055/ultimate, so the 10-yr extrapolation cap constrains the ultimate-horizon population claim.

### [INCOMPLETE] Non-domestic — method, Tab 12 rates (line 107)
**Ref:** G1-p61 Tab 12 + NOTE

> Wet Industry | Not Applicable | Variable — Prisons | No. of Prisoners + Staff | 185/day/capita — NOTE : The designer can provide additional details per category or data for his design and shall substantiate the use of an alternative value.

**Action:** The 'shall' quote and all listed rates are verbatim-correct, but three Tab 12 items are dropped. Add: (a) Wet Industry = 'Not Applicable / Variable' — no unit rate exists, demand must come from the facility/developer; (b) Prisons basis is 'No. of Prisoners + Staff' (Army Camps is occupants only) — '185 l/cap' without staff undercounts prisons; (c) Tab 12 NOTE: the designer may use alternative values per category but shall substantiate them — i.e. the reference rates are defaults, deviations need justification, not NWS silence.

### [INCOMPLETE] Non-domestic — fallback +22% Distributed ratio (line 108)
**Ref:** G1-p59 §7.3.1; G1-p60 §7.3.2

> The non-domestic and government ratios refer to spatially distributed non-domestic consumption that are to be added to the domestic consumption. These ratios do not apply to the water consumption of specific identified non-domestic projects such as economic zones are to be determined on a case-by-case basis. […] The updated ratio can be provided by the NWS Planning department.

**Action:** 22% value and 'Distributed Non-Domestic Ratio' label confirmed (Tab 11 header: 'Distributed Non-Domestic Ratio (% LPCD)'). Two source conditions omitted — add: (a) 'The ratios do NOT apply to specific identified non-domestic projects (e.g. economic zones); those are case-by-case (§7.3.1)' — so a named industrial/economic development inside a zone cannot be covered by the 22%; (b) 'An updated ratio can be obtained from the NWS Planning department (§7.3.2)' — the 2021–23 value is not frozen. Also note: the file's derivation gloss (volume ÷ population) is an inference; the source only says the ratio is 'between the non-domestic and domestic consumption', derived from 2021–2023 water-balance averages.

### [INCOMPLETE] Spatial allocation binding rule (line 110)
**Ref:** G1-p59 §7.3.1

> The non-domestic and government ratios refer to spatially distributed non-domestic consumption that are to be added to the domestic consumption.

**Action:** The arithmetic checks out (164×0.85=139.4; 139.4+164×0.36×0.54=171.3) and the row honestly tags itself '+ this project'. But it omits the source sentence an NWS reviewer will quote back: GUD-201 calls the ratios 'spatially distributed non-domestic consumption that are to be added to the domestic consumption' — a wording that can be read as smearing the uplift across the served population, the opposite of the project's concentrate-on-non-residential-plots rule. Add the verbatim §7.3.1 sentence to the row and mark the concentration rule explicitly as a project deviation requiring NWS concurrence, defended on the grounds that residential-only branches carry no commercial flow.

### [MISSING_FROM_CRITERIA] §7.3.4 Special Consumption
**Ref:** G1-p61 §7.3.4

> The special consumption represents an additional consumption required to accommodate specific projects within the project perimeter. This consumption must be provided by the developer. Special consumptions can include labour camps, industrial facilities with high water usage, etc. These needs are not covered by population forecasts and reflect the specific requirements of the project.

**Action:** Add row: 'Special consumption (G1-p61 §7.3.4): specific projects inside the perimeter — labour camps, high-water-use industrial facilities — are NOT covered by population forecasts or the 22%/14% ratios; their demand must be provided by the developer and added explicitly.' For the sewer design this is the hook for any large identified generator (labour camp, wet industry) whose WW load would otherwise be invisible to the plots×LPCD chain.

### [MISSING_FROM_CRITERIA] §7.3.5 Blue Tankers + Table 13 (Adh Dhahirah 333%)
**Ref:** G1-p61 §7.3.5, G1-p62 Tab 13

> Adh Dhahirah | 5,145 | 333% [Table 13: Tanker (Free + sold) 2021-2023 average in m3/d; Ratio of the Tankers (free+sold) over domestic consumption (via network) in 2023]. If the design includes a tanker filling station (TFS) within or near the project area, the tanker Consumption must be explicitly assessed and incorporated into the overall design.

**Action:** Add row: 'Blue tanker water supply (G1-p61–62 §7.3.5, Tab 13): Adh Dhahirah tanker volume 5,145 m³/d (2021–23 avg) = 333% of 2023 network domestic consumption — the highest ratio in Oman. Consequence for WW estimation: the 164 LPCD is derived from network-accounted water only (LPCD formula, G1-p60), so in tanker-supplied settlements household water use — and hence sewage generation — is NOT captured by 164×0.85; tanker-supplied water returning as sewage must be assessed explicitly. Any TFS in/near the project area requires explicit demand assessment from NWS TFS data, validated by NWS; IMP holds tanker demand constant over time.' This is the largest uncarried number in §7.3 and directly biases Ibri WW flows low if ignored.

---
## v:ww-chain — 1 confirmed, 8 issues

> Page alignment: confirmed no offset — PDF 1-based page 57 carries footer 'Page 57 of 152', so printed page == PDF page throughout. Direct answers to the flagged questions, verbatim: (1) Peak formula applicability: 'The Merrimack formula is to be used for calculating the peak factors for wastewater discharge for an area (catchment or sub catchment) having over 100 properties' (G1-p71), Qpdf/Qadf in Ml/day; Peltier is 'Alternatively... The method proposed in the IMP2024', Qm in l/s ('NOTE: The Average Daily Flow in this formula is in liters per second', G1-p72). No formula is prescribed for ≤100 properties. (2) The 5.0 cap is HOURLY and RECOMMENDED, not mandatory: 'NOTE : It is recommended that the hourly peak factor should not exceed 5.0' (G1-p72). (3) 720 L/d/km applies to 'newly designed networks, a linear infiltration allowance of 720 liters per day per kilometer (L/d/km) of sewer' — per km of sewer length, new networks only; 10% = existing inland networks; up to 40% = existing networks in groundwater/coastal zones; stormwater excluded. (4) ADD-ORDER NOT SETTLED BY THE TEXT: a full-document scan of every 'infiltration' occurrence in GUD-201 (pp. 6, 32, 37, 43, 47, 72-74, 100, 102, 112, 132) finds no sentence stating whether infiltration is added before or after the peak factor. §7.4.2 applies Pf to the average daily flow; §7.4.3 only says the infiltration volume 'must be accounted for'. The only ordering anywhere in the criteria framework is GUD-203 p65 Tab 29 (STP incoming flow = avg sewage flow + infiltration + 10%), which is at the STP, not the network, and is outside my assigned source — the project question remains open and should be resolved with NWS or via BS EN 752 (which G1-p71 mandates when detailed land use exists). Engineering-inference (not text): a fixed 720 L/d/km allowance is diurnally flat, which argues for adding it after peaking the sanitary component, but the guideline does not say so. (5) Tanker percentages: only one figure exists — 'In 2024, the yellow tanker represented approximately 17% of the total flow reaching the STPs of Nama WS' (company-wide observation, G1-p73); coverage assumption 100% by end of planning period, same coverage as water supply. Extracted source text retained at C:/Users/mojtaba/AppData/Local/Temp/claude/D--Mojtaba-Renardet-2621-Ibri-Sewer-STP-Hydraulic-Claude/85f9b688-45e6-4631-b96d-2cee752ad021/scratchpad/gud201_pages.txt (printed pages 55-59, 64-78).

### [INCOMPLETE] Return rate water→WW (line 113)
**Ref:** G1-p71 §7.4.1 (para directly below Tab 19); G1-p70 for private wells

> For project-specific designs where detailed land use information is available, Design flows shall be calculated in accordance with a relevant international standard such as BS EN 752 : Drain & Sewer System Outside Building (latest edition) or another equivalent standard. Calculations shall clearly state which standard has been used. This shall be supported by the collection of data and site-specific evidence to validate the design criteria.

**Action:** Values and ref right (Tab 19, G1-p71: Domestic & Tanker 85%; Non-Domestic (Government and commercial) 54%), but two conditions are omitted: (1) the ratios are baseline figures 'for planning and forecasting purposes across broader service areas' — and immediately below Table 19 the guideline makes a different method MANDATORY when detailed land use exists: design flows shall be calculated per BS EN 752 (or stated equivalent) supported by site-specific data, with British Water CoP for Flows & Loads as flow-rate guidance. Same pattern as the Tab 12 land-use rule the prior audit caught — Ibri has detailed land-use allocation, so this clause bites. (2) 'A specific attention is to be taken for catchments covered with private wells' and the Designer shall assess other water sources (private wells, private providers, non-network abstractions) for their wastewater contribution (G1-p70). Suggested row addition: 'Where detailed land-use information is available, design flows SHALL be per BS EN 752 or stated equivalent w/ site-specific evidence (G1-p71); assess private wells / non-network sources (G1-p70).'

### [INCOMPLETE] WW peak factor Merrimack/Peltier + 5.0 cap (line 114)
**Ref:** G1-p71 §7.4.2 (Merrimack); G1-p72 (Peltier + both NOTEs)

> The Merrimack formula is to be used for calculating the peak factors for wastewater discharge for an area (catchment or sub catchment) having over 100 properties. [...] NOTE: The Average Daily Flow in this formula is in liters per second. NOTE : It is recommended that the hourly peak factor should not exceed 5.0.

**Action:** Formulas, units and threshold all check out: Merrimack Qpdf=2.65·Qadf^0.879 with Qpdf/Qadf in Ml/day, and it 'is to be used' (mandatory wording) for an area 'having over 100 properties'; Peltier PfWW=1.5+1/√Qm with Qm = Average Daily Flow in l/s (explicit NOTE), introduced as 'Alternatively' / 'proposed in the IMP2024'. Two omissions: (1) the 5.0 cap is a RECOMMENDATION, not a mandatory limit — source wording is 'It is recommended that the hourly peak factor should not exceed 5.0'; treating it as a hard cap could undersize peak capacity. It is explicitly HOURLY. (2) Both formulas are defined on peak DAILY flow (Qpdf = 'Peak daily flow (Ml/day)' / 'Peak Flow (m³/d)'); the hourly-PF ≤5.0 note is the only hourly reference — the criteria should not imply the formulas themselves yield an hourly factor. Suggested row wording: 'Merrimack (mandatory >100 properties, Ml/d, gives peak-daily factor) or IMP2024 Peltier PfWW=1.5+1/√Qm (Qm in l/s); hourly PF ≤5.0 is recommended (not mandatory)'.

### [INCOMPLETE] Infiltration 720 L/d/km / 10% / 40% (line 115)
**Ref:** G1-p72 §7.4.3; tanker/vacuum exception G1-p73

> For newly designed networks, a linear infiltration allowance of 720 liters per day per kilometer (L/d/km) of sewer should be incorporated into the design. Infiltration due to storm water is not considered. [...] Tanker or vacuum collection do not require to account for infiltration volume.

**Action:** All three values, their conditions and the stormwater exclusion are correct: newly designed networks → 720 L/d per km OF SEWER; existing networks inland/outside groundwater influence → 10% (of the wastewater flow, by parallel with the 40% bullet); existing networks in groundwater-table zones or coastal areas → up to 40% of the wastewater flow; 'Infiltration due to storm water is not considered.' Omitted exception on the next page: 'Tanker or vacuum collection do not require to account for infiltration volume' (G1-p73) — material here because ~17% of STP inflow arrives by tanker and carries no infiltration allowance. Also note the framing: the umbrella sentence is mandatory ('The infiltration volume must be accounted for in the design of sewerage infrastructure') while the three rates are 'recommended' guidelines 'for more detailed design purposes'. ADD-ORDER: the text does NOT state whether infiltration is added before or after the peak factor — §7.4.2 applies Pf to average daily flow and §7.4.3 is silent on sequencing; GUD-201 does not settle the project's open question (see notes).

### [INCOMPLETE] Yellow tankers 17% (line 116)
**Ref:** G1-p73 §7.4.4

> the capacity of the collection system should assume the same coverage as for the water supply, since customers will progressively connect to any available collection infrastructure and it is assumed that the coverage will be 100% by the end of the planning period. [...] In 2024, the yellow tanker represented approximately 17% of the total flow reaching the STPs of Nama WS. The pollution loads of tankers are higher than the network effluent (see Sewage characteristics PAM-GUD-203 Wastewater Guidelines).

**Action:** The three captured points are right: ~17% (2024), 100% coverage assumed by end of planning period, self-cleansing check at initial operations ('to ensure self-cleaning velocities at all times'). Omitted: (1) 17% is a 2024 OBSERVATION of total flow reaching the STPs of Nama WS company-wide — not a per-STP design allowance for Ibri; (2) the collection-system capacity 'should assume the same coverage as for the water supply'; (3) tanker pollution loads are HIGHER than network effluent (STP load design per Sewage characteristics, PAM-GUD-203) — relevant to STP process sizing; (4) tanker-collected flow carries no infiltration allowance (G1-p73 §7.4.3 end).

### [INCOMPLETE] STP design margin +10% (line 117)
**Ref:** G1-p73 §7.4.5

> A 10% margin should be applied when designing new STPs. [...] This headroom is to be applied over and above any redundancies in the design to mitigate operational outages.

**Action:** 10% correct; G1-p73 ref correct (GUD-203 p65 Tab 29 cross-ref not re-verified, outside assigned source). Two omitted qualifiers: (1) the margin applies 'when designing NEW STPs'; (2) it is 'to be applied over and above any redundancies in the design to mitigate operational outages' — i.e. it cannot be absorbed by duty/standby redundancy. Also the margin is on the forecasted design flow ('conditions exceeding the forecasted design flow'), covering fluctuations in population, water consumption, infiltration and other unforeseen factors.

### [INCOMPLETE] Design/planning life (line 119)
**Ref:** G1-p57 §7.1, Tab 10

> The designs shall have a planning life cycle of 25 years, which corresponds both to the ultimate design capacity of the project, as well as the period over which the NPV will be calculated for the purpose of comparing schemes for total lifetime cost analysis. [Table 10: Civil/structures building 50; Mechanical equipment 20; Electrical equipment 15 - 50; ICA works 15; Pipe work 50] These asset lifetimes are used for financial asset depreciation calculations.

**Action:** 25-yr planning cycle, civils 50, mech 20, pipes 50 all correct (G1-p57 Tab 10). Omitted: (1) Tab 10 also lists Electrical equipment 15–50 yr and ICA works 15 yr; (2) the note that 'These asset lifetimes are used for financial asset depreciation calculations' (technical lifetimes may vary); (3) the 25-yr planning cycle 'corresponds both to the ultimate design capacity of the project, as well as the period over which the NPV will be calculated for the purpose of comparing schemes for total lifetime cost analysis' — directly load-bearing for this project's ≥3-options comparisons. Suggested row: 'planning cycle 25 yr (= ultimate design capacity AND NPV period for scheme comparison); civils 50, mech 20, electrical 15–50, ICA 15, pipes 50 yr (depreciation lifetimes)'.

### [MISSING_FROM_CRITERIA] TSE network system loss 10% (not in criteria)
**Ref:** G1-p76 §7.4.6.3.b

> Further losses will occur in the TSE transmission and distribution network principally from pipe joints and connection points. [...] For design purposes, a system loss of 10 percent of all produced TSE shall be assumed.

**Action:** Add to §11 (or 12b): 'TSE network losses: a system loss of 10% of all produced TSE SHALL be assumed in the TE transmission/distribution design | G1-p76 §7.4.6.3.b'. Mandatory 'shall'; the project designs a TE network, and criteria §12b (GUD-202 hydraulics) does not carry it. Net TSE available to consumers = STP inlet × 0.95 × 0.90, not × 0.95.

### [MISSING_FROM_CRITERIA] TSE demand seasonal peaking & sizing rules (not in criteria)
**Ref:** G1-p76 §7.4.6.4 (Tab 23); G1-p74–75 §7.4.6.2 (Tab 21, 22)

> The TSE system shall be sized to accommodate the peak demand experienced during the summer months. [...] Any consumer with an average daily demand larger than 500 m3/day is to be studied individually, and an irrigation timing pattern shall be applied that reflects its actual settings.

**Action:** Add: 'TSE system SHALL be sized on summer peak demand; Tab 23 seasonal factors (% of summer): Dec–Feb 50%, Mar–May & Sep–Nov 75%, Jun–Aug 100%. Any consumer >500 m³/d average demand is to be studied individually with its actual irrigation timing pattern; consumers with large storage → demand spread over storage hours. Conceptual TSE demand rates Tab 21 (e.g. grass 12 L/m²/d, ground cover 10 L/m²/d; roads/junctions mixed vegetation 10 L/m²/d subject to Municipality approval) | G1-p74–76 §7.4.6.2–7.4.6.4'.

---
## v:wadi201+surveys — 2 confirmed, 10 issues

> Page alignment verified in both PDFs: GUD-201 pdf page 85 footer reads "Page 85 of 152"; GUD-203 pdf page 197 footer reads "Page 197 of 201" — printed page == pdf 1-based page, no offset. All core hard numbers in 11b survive audit: DI + 15 m each side with mechanical/detachable joints (G1-p86, verbatim), PAM-STD-404 (G1-p86, verbatim "Wadi protection is to be designed according to NWS standard drawings PAM-STD-404"), min 2.0 m cover in soft soil (G1-p86, verbatim), no chambers/markers in wadi bed or embankments (G1-p86). No MISREAD and no WRONG_REF found in either assigned section — every defect is an omitted condition or mandatory clause. Two lower-priority observations not raised as findings: (1) G1-p82 §8.3.5 (Remote Areas potable pipelines) independently requires "2000 mm cover at wadi crossings" and "1000 mm cover at road crossings" — consistent with the 11b soft-soil rule, no conflict; (2) G1-p86–87 §9.5 lists the trenchless-selection references (Pipe Jacking Association 1987, BS EN 14457:2004, BS EN 13566 pts 1–4+7, ISTT) and requires rehab-method selection only after CCTV + hydraulic assessment — the criteria file's §6 trenchless row cites only GUD-203 p21/p35; adding "G1-p86 §9.5" as a ref would strengthen it. The p199 borehole finding sits one page outside the assigned check window (196–198) but belongs to the same §13 the criteria's Section 12 claims to summarize, so it was included.

### [INCOMPLETE] 11b Data & approvals (wadi crossings)
**Ref:** G1-p85 §9.3

> Approvals shall be obtained from MoAFWR and any other relevant agencies. The designer shall conduct all the necessary investigations and surveys (geophysical, geotechnical, topographic surveys, georesistivity surveys, environmental Impact assessment, hydraulic & scour analysis, etc…)

**Action:** Data & approvals | wadi bed profiles/cross-sections, flood frequency 1:20/1:50/1:100 (etc.), grain size of bed material, long-term bed-level change monitoring — from CAA & MoAFWR; approvals from MoAFWR AND any other relevant agencies. Designer shall ALSO conduct own investigations/surveys: geophysical, geotechnical, topographic, georesistivity, EIA, hydraulic & scour analysis | G1-p85

### [INCOMPLETE] 11b Protection — PAM-STD-404 / anti-flotation
**Ref:** G1-p86 §9.3

> Wadi protection shall be designed to prevent flotation of the pipeline in the event of flooding or in coastal areas where the pipeline is installed under mean sea level or in areas where the water table is high, while the pipe is empty.

**Action:** Protection | per NWS std dwg PAM-STD-404; anti-flotation check with pipe empty for: flooding, high water table, OR coastal installation below mean sea level (third case n/a inland Ibri, recorded for completeness) | G1-p86

### [INCOMPLETE] 11b Valves (wadi crossings)
**Ref:** G1-p86 §9.3

> No valve chambers or marker posts shall be constructed in the wadi bed or on the embankments of the wadi and all valves and marker posts must be visible and fully accessible when the Wadi is in flood.

**Action:** Valves | isolation + air valves both sides of active and major crossings (air valves ensure hydraulic performance since crossing runs at a lower level); washout at low point one side; no valve chambers/marker posts in wadi bed or embankments; all valves and marker posts must be VISIBLE and fully accessible when wadi is in flood (visibility drives marker-post height above flood level) | G1-p86

### [INCOMPLETE] 11b Road crossings
**Ref:** G1-p85 §9.1, §9.2

> Wherever possible trenchless techniques are to be used for pipelines crossing under existing roads. […] In exceptional cases, the excavation of existing roads is allowed […] Valves shall be installed either side of major road crossings to permit the isolation of the pipeline under the road.

**Action:** Road crossings | trenchless "wherever possible"; open-cut only in EXCEPTIONAL cases, reinstatement per Oman Highway Design Manual (MoT + Regional Municipality); valves shall be installed either side of MAJOR road crossings to permit isolation of pipeline under the road | G1-p85 §9.1–9.2

### [INCOMPLETE] 11b Falaj crossings
**Ref:** G1-p86 §9.4

> Appropriate protection from accidental damage shall be specified for the contractor’s ESMP, including vibration control from plant and equipment, structural integrity assessments, use of appropriate protection barriers, avoid water contamination from accidental spills.

**Action:** Falaj crossings | buffer zones around Aflaj, min safe excavation distances; protection measures shall be SPECIFIED FOR THE CONTRACTOR'S ESMP: vibration control from plant/equipment, structural integrity assessments, protection barriers, prevention of water contamination from spills | G1-p86

### [INCOMPLETE] 12 Surveys (§13, p197)
**Ref:** p197 §13, §13.1, §13.2

> The Designer shall conduct and provide with the Tender Documents thorough inspections to specify the initial condition of the existing structure […] be carried out in accordance with ASTM standards and national codes where applicable. […] with reference to Omani national datum and in metric units.

**Action:** - CCTV, topo and geotechnical surveys at EARLY design stage, per ASTM standards and national codes where applicable (p197). Topo along proposed sewer/TSE routes: X,Y,Z Omani national datum, METRIC UNITS; include existing utilities and adjacent roads with cross-sections near proposed pipelines; maps show grid, permanent benchmark, invert levels of existing drains; designer picks appropriate DTM (p197). CCTV of existing assets per NF EN 13508-2, condition survey results to be PROVIDED WITH THE TENDER DOCUMENTS; drones/ROV/sonar/lidar/3D scan permitted as supplements (p197).

### [MISSING_FROM_CRITERIA] Duct/culvert crossing rules (§9.2)
**Ref:** G1-p85 §9.2

> Details of the proposed arrangement including the pipeline support method shall be submitted to NWS for approval. […] A separate pressure test shall be carried out for the sections of pipe inside the duct to ensure the integrity of the pipe and that correct installation has been achieved.

**Action:** Crossings via existing ducts/culverts | exact location on construction dwgs; pipe support arrangement submitted to NWS for approval; SEPARATE pressure test for pipe sections inside duct; after approval seal both duct ends with lean concrete (unless duct shared with other utilities) | G1-p85 §9.2

### [MISSING_FROM_CRITERIA] Control benchmark accuracy + underground services detection
**Ref:** p198 §13.3

> Surveying of control point bench marks should be conducted to achieve a spherical accuracy of ± 0.05 m, relative to existing control stations, conforming to a minimum "Order C, Class 3" category survey as per “Geometric Geodetic Accuracy Standards and Specifications for using GPS relative positioning techniques.

**Action:** Underground services detection: min scope oil, gas, water, effluent pipelines, cables and irrigation FALAJ; methods incl. trial pits, probes between manholes, ground radar (non-metallic), electro-location. Control point benchmarks: spherical accuracy ±0.05 m relative to existing control stations, min "Order C, Class 3" GPS survey | p198 §13.3

### [MISSING_FROM_CRITERIA] STP/PS site topo survey scope
**Ref:** p198 §13.2

> complete dimensions of the plot project area and GPS coordinates for each corner of the plot boundary, size and description of the following features to identify sub-surface strata such as sand, rock, vegetation, Sabkha etc. for complete site within the plot boundary limits and surrounding up to 10 m beyond the plot limits

**Action:** STP & PS topo surveys: horizontal + vertical/depth location, complete plot dimensions, GPS coordinates of each plot-boundary corner, surface strata description (sand, rock, vegetation, sabkha), full site coverage extending 10 m BEYOND plot limits; below-ground structures/services identified on maps | p198 §13.2

### [MISSING_FROM_CRITERIA] Geotechnical borehole depth for pipelines
**Ref:** p199 §13.4

> For shallow pipelines it is generally adequate to take exploration boreholes to 5.0 m below the invert level of pipelines.

**Action:** Geotechnical survey (pipelines): shallow pipelines — exploration boreholes to 5.0 m below pipe invert level; staged investigation (desk study + reconnaissance → detailed ground investigation with topo/hydro-geological survey → additional investigation during construction if required) | p199 §13.4

---
## v:gud202 — 4 confirmed, 8 issues

> Page alignment verified: PDF 1-based page 102 carries footer "Page 102 of 177" — printed page == PDF page, no offset. All G2 page refs in criteria lines 133-145 are correct as cited (no WRONG_REF findings). The p53+/p70+ legs of the pumping-station row were outside the assigned source pages (102-106, 135-139, 143-145, 151-155 read as 100-108/133-147/151-157 with context) and were not verified — only the p144 surge leg was audited. Two context items observed but not raised as findings because they fall outside the section's water/TSE-network design scope for this sewer/TE project: (a) Table 26 house-connection header sizes (≤3 conn → 32 mm, 4-11 → 63 mm, 12-16 → 110 mm, G2-p143); (b) DMA design mandates for water distribution (500-2500 connections, ≤30 m elevation change per DMA, DMA designs required at earliest concept stage, G2-p141-142) — worth a row only if the project ends up designing potable distribution. Extraction was text-based (PyMuPDF) because pdftoppm is unavailable; Table 21 column order (C-value, ε per age step) was cross-checked against the header row and is internally consistent.

### [INCOMPLETE] Transmission velocity
**Ref:** G2-p103 §7.1.3.1 (band '1.0 ≤ v < 2.0 m/s' on p104)

> The peak velocity as high as 2.0 m/s, at a horizon of 25 years for transmission, is possible but is seldom considered due to the high stresses this can cause and high pressure loss that can be generated over short distances. A peak velocity of 1.5 m/s is more common but will depend on pipe diameter (more acceptable for large pipes than small diameters). However, a safety factor shall be considered for future expansion of the network.

**Action:** 1.0 ≤ v < 2.0 m/s; 2.0 m/s peak (25-yr horizon) possible but seldom used due to stress/head loss; 1.5 m/s more common, diameter-dependent (more acceptable for large pipes than small); a safety factor SHALL be considered for future network expansion

### [INCOMPLETE] Distribution velocity
**Ref:** G2-p136 §9.1.1.1

> The minimum design velocity is set at 0.4 m/s. This value represents the minimum that is required for maintaining water quality and must be validated using hydraulic and water quality models. The maximum allowable velocity within the distribution network is set at 1.5 m/s. ... In special cases, where the velocity is below 0.4 m/s water quality assurances (water age) must be presented and justified with the use of a water quality model which clearly shows the residual chlorine concentration and the water residence time. The minimum residual chlorine concentration, according to WHO Guidelines, is 0.2 mg/l.

**Action:** 0.4 ≤ v < 1.5 m/s; the 0.4 m/s minimum itself MUST be validated using hydraulic and water quality models (not only the below-0.4 exception); below 0.4 → water-quality/age model showing residual Cl and residence time, min residual chlorine 0.2 mg/l per WHO

### [INCOMPLETE] Distribution pressure
**Ref:** G2-p137 §9.1.1.4

> the pressure head in the network should, wherever possible, be at least 1.5 bar (15 mwc, worst point peak day, peak hour) in all parts of the network, including the remotest and highest points. The maximum pressure should not exceed 4 bar (40 mwc). In case of firefighting flows, pressure in the network shall be maintained as minimum positive value i.e. negative pressure should not be developed in the network assuming zero parallel domestic use during fire.

**Action:** min 1.5 bar (15 mwc) at worst point, PEAK HOUR OF PEAK DAY, wherever possible incl. remotest/highest points; max 4 bar (40 mwc); fire flow: pressure shall stay positive (no negative pressure anywhere) ASSUMING ZERO PARALLEL DOMESTIC USE during fire

### [INCOMPLETE] Distribution pipe material
**Ref:** G2-p138 §9.1.4, §9.1.5; G2-p139

> PE 100 up to 1000 mm diameter (OD 110, 180, 225, 355, 500, 630, 710, 900 and 1000 shall be used); Ductile Iron (DI) above 300 mm diameter; DI for special locations like road/wadi crossings. ... The recommended diameters for the distribution system are from DN100 mm to DN 400 mm, unless otherwise specified.

**Action:** PE100 up to 1000 mm — ONLY OD 110, 180, 225, 355, 500, 630, 710, 900, 1000 shall be used (intermediate ODs like 250/315 not permitted); DI above 300 mm and at road/wadi crossings; recommended distribution diameters DN100–DN400 unless otherwise specified (p139); pipe sizing per §9.1.1.1 with NWS-approved licensed hydraulic modelling software, model copy submitted to NWS (p138 §9.1.5)

### [INCOMPLETE] Pumping stations, reservoirs, surge (p144 leg)
**Ref:** G2-p144 §10

> 10. Surge Analysis & Protection Refer to Appendix III of PAM-GUD-201 General Design Guidelines

**Action:** §10 (p144) contains NO surge requirements of its own — it is a one-line cross-reference: 'Surge Analysis & Protection — Refer to Appendix III of PAM-GUD-201 General Design Guidelines'. The actual surge criteria live in GUD-201 Appendix III; cite that, not G2-p144, as the technical source. (p53+/p70+ legs of this row are outside the audited page set — unverified.)

### [INCOMPLETE] Tanker filling stations
**Ref:** G2-p154 §12.4; G2-p155 §12.5.1–12.5.2

> Peak hour factors (typically 1.5-2.0 times average flow); Future growth projections for a minimum of 10 years ... Peak hour flow rate during the maximum demand day; Concurrent filling of multiple tankers (minimum of two); Operational reserve capacity of 20% ... Minimum flow rate of 1 m3 per minute per filling point; Working pressure of 2-4 bar at the discharge point ... Storage facilities, if required, shall: Provide minimum 2-hour peak demand storage ... For the TSE TFS, the hydraulic supply can be adapted : STP or Ground reservoir + VFD pumping station for 12hrs of average demand.

**Action:** peak-hour factor typically 1.5–2.0 × avg flow; min design capacity = peak-hour flow of max demand day + concurrent filling min 2 tankers + 20% operational reserve; ≥1 m³/min per filling point at 2–4 bar working pressure; capacity based on future growth projections MIN 10 YEARS; storage (if provided) min 2-h peak demand; queue min 3 tankers per filling point at peak (p155); potable TFS supply = ground reservoir + VFD PS + 48-h genset OR elevated tank 48-h storage; TSE TFS supply = STP or ground reservoir + VFD PS for 12 h of AVERAGE demand (p155)

### [MISSING_FROM_CRITERIA] Transmission pressure / hydraulic gradient rules (no row exists)
**Ref:** G2-p105 §7.1.3.4

> Pressure at various points along the pipeline is shown on the hydraulic gradient that must be prepared for all transmission pipelines during preliminary design at the latest. ... 1. Pipeline profile should not go above the gradient line at any point; ... 3. At no place must the pressure within the pipeline exceed the manufacturer's pressure rating for the pipe

**Action:** Add row — Transmission pressures: hydraulic gradient MUST be prepared for every transmission pipeline by preliminary design at the latest; pipeline profile shall not rise above the gradient line at any point; pressure must never exceed manufacturer's pipe rating (internal + external/surcharge load); control at receiving reservoir (motorized/altitude valve each end) so line does not empty; break pressure tank or terminal control system where needed; branch take-offs need pressure adequacy check (booster or PRV if inadequate) | G2-p105 §7.1.3.4

### [MISSING_FROM_CRITERIA] TFS siting buffers & transmission-connection prohibition (no row exists)
**Ref:** G2-p153 §12.3.1; G2-p156 §12.6.1

> Min. 200 m apart from the residential plot and 500 m away from public amenities viz., school/Park/Mosque/Eid prayer area ... NOTE : No water TFS shall be installed or connected to a Transmission line. ... Direct connection to water or TSE transmission mains shall be avoided whenever possible and shall only be considered as a last resort

**Action:** Add row — TFS siting: min 200 m from residential plots, 500 m from public amenities (school/park/mosque/Eid prayer area); spilled water gravitated to wadi/low ground without flooding neighbours; NO water TFS installed on or connected to a transmission line (p153 NOTE); direct connection to water or TSE transmission mains avoided, last resort only with comprehensive technical justification that distribution connection downstream of service reservoirs is unfeasible (p156); TFS in network-covered areas needs a comprehensive needs assessment | G2-p153, p156

---
## s:gud201-ch7-full — 7 confirmed, 24 issues

> Page numbering verified: PDF 1-based page N carries footer "Page N of 152" (checked p6, p56, p61) — no offset. §7 actually spans printed p57–79, not 56–77: §7.4.7 (sludge) and §7.5 (climatic) sit on p78–79 and were read and swept. Source-internal inconsistency worth recording in _BRAIN/05_GAPS: headroom appendix is cited as "Appendix IV - Headroom Factors" on p65 but "presented in Appendix II" on p66. On R0's "+20% weekly peak — not in GUD": partially right — GUD-201 §7.3.6 defines the peak-day-as-peak-week(7-day-rolling)-average CONCEPT (excluding leakage) but gives no numeric factor, so the R0 flag stands for the value, not the concept. Biggest engineering-impact finds: (1) TSE network 10% system loss + seasonal 50/75/100% peaking + Tab 21/22 unit demands — the TE-network demand chain is entirely absent from criteria while TE design is core scope; (2) mandatory non-network-source (private wells/tankers) assessment for WW generation, sharpened by Adh Dhahirah's 333% tanker-to-network ratio; (3) BS EN 752 mandatory design-flow route when land use is known; (4) NCSI extrapolation cap (≤10 yr beyond forecast) directly constrains the 2055/ultimate model years; (5) plot-method phasing NOTE forbids instantaneous build-out — touches the saturation scenario. Sludge 0.25 kg/m³ mislabeled "R0-only" in §12c is the one outright provenance error found.

### [INCOMPLETE] §11 Population from plots
**Ref:** G1-p59 §7.2.2 NOTE

> NOTE: When applying this methodology, special care must be given in cases of plot subdivision, to ensure that population estimates properly reflect the effective number of housing units created. In addition, development speed must be considered through appropriate phasing assumptions, as not all plots will be developed simultaneously. Coverage will be estimated using planning data and land use typologies, and development percentages must be applied over the design period to reflect realistic build-out scenarios and particularly avoiding overestimation.

**Action:** Append to row: NOTE (G1-p59) — account for plot subdivision (effective housing units created) and apply development/phasing percentages over the design period; build-out is never assumed instantaneous ('avoiding overestimation'). Coverage estimated from planning data and land-use typologies.

### [INCOMPLETE] §11 Non-domestic method (Tab 12 mandatory)
**Ref:** G1-p61 Tab 12 + NOTE

> Wet Industry | Not Applicable | Variable ... NOTE : The designer can provide additional details per category or data for his design and shall substantiate the use of an alternative value.

**Action:** Add to row: Wet Industry = 'Not Applicable / Variable' (developer data, not a Tab 12 unit rate); Tab 12 NOTE permits alternative unit values only if the designer substantiates them.

### [INCOMPLETE] §11 Non-domestic fallback +22%
**Ref:** G1-p59 §7.3.1; G1-p60 §7.3.2

> These ratios do not apply to the water consumption of specific identified non-domestic projects such as economic zones are to be determined on a case-by-case basis. ... The updated ratio can be provided by the NWS Planning department.

**Action:** Add two clauses: (a) the distributed ratios do NOT apply to specific identified non-domestic projects (e.g. economic zones) — those are case-by-case; (b) an updated ratio can be obtained from the NWS Planning department (the 22% is the IMP2024 snapshot, not frozen).

### [INCOMPLETE] §11 WW peak factor (Merrimack/Peltier, hourly PF <= 5.0)
**Ref:** G1-p72 §7.4.2

> NOTE : It is recommended that the hourly peak factor should not exceed 5.0.

**Action:** Change 'hourly PF ≤ 5.0' to 'hourly PF ≤ 5.0 (source wording: recommended, not absolute)'. Merrimack '>100 properties' and Peltier Qm in l/s confirmed verbatim.

### [INCOMPLETE] §11 Infiltration (720 L/d/km new; 10%; 40%)
**Ref:** G1-p73 §7.4.3

> Tanker  or vacuum collection do not require to account for infiltration volume.

**Action:** Add: tanker- or vacuum-collected catchments carry NO infiltration allowance.

### [INCOMPLETE] §11 Yellow tankers ~17%
**Ref:** G1-p73 §7.4.4

> The pollution loads of tankers are higher than the network effluent (see Sewage characteristics PAM-GUD-203 Wastewater Guidelines).

**Action:** Add: tanker pollution loads are HIGHER than network effluent (per PAM-GUD-203 sewage characteristics) — affects STP load design, not just hydraulics.

### [INCOMPLETE] §11 STP design margin +10%
**Ref:** G1-p73 §7.4.5

> This headroom is to be applied over and above any redundancies in the design to mitigate operational outages.

**Action:** Add: the 10% margin is applied over and above any redundancy designed in for operational outages (margin and redundancy never netted against each other).

### [INCOMPLETE] §11 Design/planning life (25 yr; civils 50, mech 20, pipes 50)
**Ref:** G1-p57 Tab 10

> Electrical equipment 15 - 50 ... ICA works 15 ... These asset lifetimes are used for financial asset depreciation calculations. The technical lifetimes may vary depending on the initial selection of equipment manufacturers and materials

**Action:** Complete Table 10: Civil/structures 50; Mechanical 20; Electrical 15–50; ICA works 15; Pipe work 50. Note: these lifetimes are for financial depreciation — technical lifetimes may vary with equipment/material selection. 25-yr planning cycle = ultimate design capacity AND the NPV comparison period.

### [MISSING_FROM_CRITERIA] NCSI forecast processing (disaggregation + extrapolation limit)
**Ref:** G1-p58 §7.2.1

> If population forecast data is only available at the Wilayat level and not at the Settlement level, a distribution of the forecasted figures must be carried out. ... Statistically, it is not recommended to extrapolate more than ten years beyond the available forecast period due to increased uncertainty

**Action:** | Population forecast processing | Wilayat→settlement disaggregation is mandatory using latest-census settlement shares; sub-settlement areas: pro-rata by electricity accounts (data from NWS); NCSI horizon is 20–25 yr — beyond it apply polynomial regression on NCSI data, and never extrapolate more than 10 yr past the available forecast (relevant: model year 2055/ultimate) | G1-p58 §7.2.1 |

### [MISSING_FROM_CRITERIA] Developer-figures default clause
**Ref:** G1-p59 §7.3

> In the absence of a developer-provided water demand calculation based on an approved methodology, the water demand shall be calculated in accordance with the methodology detailed below.

**Action:** | Demand methodology precedence | Developer-provided demand calc on an approved methodology takes precedence; the GUD-201 §7.3 chain applies only in its absence (same rule repeated for WW generation §7.4) | G1-p59 §7.3, G1-p70 §7.4 |

### [MISSING_FROM_CRITERIA] Special Consumption (§7.3.4)
**Ref:** G1-p61 §7.3.4

> The special consumption represents an additional consumption required to accommodate specific projects within the project perimeter. This consumption must be provided by the developer. Special consumptions can include labour camps, industrial facilities with high water usage, etc. These needs are not covered by population forecasts

**Action:** | Special consumption | Additional demand for specific projects in the perimeter (labour camps, high-usage industry) — must be provided by the developer; NOT covered by population forecasts, so it is additive to the LPCD chain | G1-p61 §7.3.4 |

### [MISSING_FROM_CRITERIA] Blue tanker consumption (§7.3.5, Tab 13)
**Ref:** G1-p61–62 §7.3.5 + Tab 13

> If the design includes a tanker filling station (TFS) within or near the project area, the tanker Consumption must be explicitly assessed and incorporated into the overall design. ... Adh Dhahirah 5,145 [m3/d] 333%

**Action:** | Blue (potable) tanker demand | If a TFS is within/near the project area, tanker consumption MUST be explicitly assessed (historical TFS data from NWS, service area, change over horizon; NWS-validated) and added to total demand. Tab 13: Adh Dhahirah tanker volume 5,145 m³/d (2021–23 avg) = 333% of 2023 network domestic consumption — network coverage in this governorate is marginal, so tanker-side flows dominate; IMP holds tanker demand constant over time | G1-p61–62 §7.3.5, Tab 13 |

### [MISSING_FROM_CRITERIA] Water peak factors (§7.3.6)
**Ref:** G1-p62–63 §7.3.6

> water distribution networks shall be designed for peak hour Consumption. However, transmission pipelines shall be designed for peak day Consumption. ... known as the peak day consumption and shall be calculated as the average day consumption in the peak week (7-days rolling) excluding leakage. ... the peak hour factor can be as much as 2-2.5 times the average hour on average day consumption

**Action:** | Water peak factors | Distribution networks designed for PEAK HOUR; transmission pipelines for PEAK DAY. Peak day = average day consumption of the peak week (7-day rolling), EXCLUDING leakage. PHF in residential areas can reach 2–2.5× avg hour. Peak factors do not apply to leakage; industrial draw smoothed via storage/service-pipe limits. (Basis for judging R0's +20% weekly peak) | G1-p62–63 §7.3.6 |

### [MISSING_FROM_CRITERIA] EPS diurnal demand patterns (Tabs 14/15)
**Ref:** G1-p64 §7.3.6

> Such profiles are to be obtained from the NWS Hydraulic team or established based on data and validated by the NWS Hydraulic team prior to design.

**Action:** | Diurnal patterns (EPS) | Tabs 14/15 give EXAMPLE domestic (peak 2.5 at 06:00, night min 0.213–0.23) and non-domestic (flat 0.859/1.198) 15-min patterns; project-specific patterns shall be obtained from, or validated by, the NWS Hydraulic team PRIOR to design | G1-p64–65 §7.3.6, Tabs 14–15 |

### [MISSING_FROM_CRITERIA] Headroom factor (§7.3.7)
**Ref:** G1-p65–66 §7.3.7

> Headroom must be considered in the design of strategic transmission pipelines, pumping stations, reservoirs, and water sources only. It does not apply to the design of distribution pipelines and networks. ... the designer will apply a 24/21 operating factor (equivalent to about 15% additional capacity) ... NOTE: Headroom is to be applied on top of any redundancy that is designed into the system

**Action:** | Headroom factor (water) | Applies ONLY to strategic transmission pipelines, pumping stations, reservoirs and water sources — never to distribution networks. Transmission/PS: 24/21 operating factor (≈+15%) for post-outage recovery. Project value provided by NWS Planning per WSZ (Appendix, updatable); applied ON TOP of redundancy | G1-p65–66 §7.3.7 |

### [MISSING_FROM_CRITERIA] NRW / new-network leakage allowance (§7.3.8)
**Ref:** G1-p68 §7.3.8.1–7.3.8.3

> This allowance should be the higher of the following: 15% of the total domestic and non-domestic consumption / 10 m³/day/km of network length in dense urban areas, and 5 m³/day/km in other areas. ... It shall nevertheless not be considered for the Water demand calculation for the design, unless justified by the Designer and approved by the NWS Planning team.

**Action:** | NRW & leakage allowance (water) | Physical NRW must be added to demand for capacity sizing. New networks: leakage allowance = the HIGHER of 15% of total domestic+non-domestic consumption OR 10 m³/d/km (dense urban) / 5 m³/d/km (other). Existing networks: technical losses from NWS historical data, validated with NWS Planning. Operational water use (1–2% of demand) is EXCLUDED from design demand unless justified and NWS-approved; commercial losses already inside per-capita rates | G1-p66–68 §7.3.8 |

### [MISSING_FROM_CRITERIA] Firefighting provisions (§7.3.9)
**Ref:** G1-p69 §7.3.9

> the hydrants shall be designed to deliver a flow of 1 m3/min. Water pressure in adjacent networks supplying residential areas may become affected during fire, but the design should ensure that no negative pressure occurs.

**Action:** | Firefighting (water) | Hydrants per CDAA, location approval per project; hydrant flow 1 m³/min. Extra reservoir capacity by population (Tab 17): <5k→50 m³ … >60k→500 m³. Tab 18: residential 1 hydrant @100–150 m spacing, 30 min; commercial 2 @75–100 m, 60 min; industrial 4 @60–75 m, 90 min. Adjacent network pressure may drop during fire but must never go negative | G1-p69 §7.3.9, Tabs 17–18 |

### [MISSING_FROM_CRITERIA] Non-network water sources in WW generation (§7.4/7.4.1)
**Ref:** G1-p70 §7.4, §7.4.1

> the Designer shall carry out an assessment of other potential water sources within the project area, such as private wells, private water providers, or other non-network abstractions, to ensure that their contribution to wastewater generation is properly accounted for. ... A specific attention is to be taken for catchments covered with private wells.

**Action:** | Other WW sources (binding) | Designer SHALL assess other water sources in the project area — private wells, private water providers, non-network abstractions — and include their return in WW generation; specific attention to catchments on private wells. Critical for Ibri: Adh Dhahirah blue-tanker ratio 333% of network domestic consumption (G1-p62) means network-supplied water understates true consumption, so WW derived from network demand alone under-predicts | G1-p70 §7.4 + §7.4.1 |

### [MISSING_FROM_CRITERIA] BS EN 752 route for design flows (§7.4.1)
**Ref:** G1-p71 §7.4.1

> For project-specific designs where detailed land use information is available, Design flows shall be calculated in accordance with a relevant international standard such as BS EN 752 : Drain & Sewer System Outside Building (latest edition) or another equivalent standard. Calculations shall clearly state which standard has been used.

**Action:** | Design-flow standard (with land use) | Where detailed land-use information exists, design flows SHALL be calculated per a relevant international standard — BS EN 752 (latest) or equivalent — with the standard named in the calculations, supported by site-specific data; also refer to British Water Code of Practice for Flows & Loads. This parallels the mandatory Tab 12 rule: with land use, the ratio shortcut is not the sanctioned method | G1-p71 §7.4.1 |

### [MISSING_FROM_CRITERIA] TSE demand estimation method (§7.4.6.2)
**Ref:** G1-p74–75 §7.4.6.2

> In the absence of specific vegetation type information and subject to the concerned Municipality approval, a TSE demand of 10 L/m2/day can be used for roads and junctions considering mixed vegetation type.

**Action:** | TSE demand (TE network sizing) | Consumers: public (road/interchange beautification, public parks) vs private (community parks, golf, gardens, nurseries/farms). Summer planting rates (Tab 21): shrubs 20–40 & palms 120–165 & other trees 40–80 L/plant/d; hedges 10 L/m/d; ground cover & seasonal flowers 10, grass 12 L/m²/d. Densities (Tab 22): trees 15 m, shrubs 3 m spacing. Roads/junctions, mixed vegetation, no specific data: 10 L/m²/d (subject to Municipality approval). Verify plant demands/densities with a landscape architect for small schemes | G1-p73–75 §7.4.6.2, Tabs 20–22 |

### [MISSING_FROM_CRITERIA] TSE network system losses 10% (§7.4.6.3)
**Ref:** G1-p76 §7.4.6.3(b)

> For design purposes, a system loss of 10 percent of all produced TSE shall be assumed.

**Action:** | TSE network losses | Beyond the 95% STP production ratio, a system loss of 10% of ALL produced TSE shall be assumed in the TE transmission/distribution network (joints, connections) — i.e. deliverable TSE ≈ 0.95 × 0.90 = 85.5% of STP inflow, not 95% | G1-p75–76 §7.4.6.3 |

### [MISSING_FROM_CRITERIA] TSE peak factors & diurnal handling (§7.4.6.4)
**Ref:** G1-p76 §7.4.6.4

> The TSE system shall be sized to accommodate the peak demand experienced during the summer months. ... Any consumer with an average daily demand larger than 500 m3/day is to be studied individually, and an irrigation timing pattern shall be applied that reflects its actual settings.

**Action:** | TSE peak factors | Seasonal (Tab 23, % of summer demand): Dec–Feb 50%, Mar–May & Sep–Nov 75%, Jun–Aug 100%; TE system SHALL be sized for summer peak. Consumers >500 m³/d avg: studied individually with actual irrigation-timing pattern. Consumers with large internal storage: demand spread evenly over storage hours. Diurnal patterns from concerned authority/private customers (Figs 2–3 reference only) | G1-p76–77 §7.4.6.4, Tab 23 |

### [MISREAD] §12c sludge 0.25 kg/m³ labeled 'R0-only'
**Ref:** G1-p78 §7.4.7

> For the purposes of the master plan, a baseline value of 0.25 kg/m³ is used as a general guideline to estimate sludge production.

**Action:** §12c row 'STP margin' — change '(sludge rate R0-only)' to 'sludge 0.25 kg/m³ = G1-p78 §7.4.7 master-plan baseline (process-dependent, general guideline)'. The value IS in GUD-201, not an R0 invention.

### [MISSING_FROM_CRITERIA] Climatic design conditions (§7.5, Tab 24)
**Ref:** G1-p78 §7.5 Tab 24

> All equipment shall be rated for continuous operation under the ambient conditions indicated below, unless otherwise specified, and performance guarantees shall be given at these conditions. ... Maximum peak ambient shade temperature 50°C [coastal] 55°C [inland]

**Action:** | Climatic design conditions (M&E) | Ibri = inland: max peak shade 55°C, max daily avg 50°C, max yearly avg 35°C, metal in sun 85°C, RH 100%; all equipment rated for continuous operation and performance-guaranteed at these conditions; rainfall high-intensity/short-duration Dec–Mar; prevailing winds N & W | G1-p78–79 §7.5, Tab 24 |

---
## s:gud201-rest — 2 confirmed, 17 issues

> Page alignment CONFIRMED: PDF 1-based page == printed page ("Page 3 of 152" on PDF page 3); no offset. Method note: the Read tool could not render this PDF (pdftoppm missing on this machine), so all pages were extracted verbatim as text via PyMuPDF 1.28 — same printed pages, quotes are verbatim from extraction; table cell order in quotes follows extraction order. Scope: swept §1, §2, §3, §4, §5, §6, §8, §9.1/9.2/9.4/9.5, §10-§14, §19, Appendices I-VII; §7 and §9.3 excluded per task. Chapters read and judged NOT load/sizing-relevant (no findings): §2 terminology, §3 HSE (confined space/fire/chemical bunds — construction detail), §5 water sources, §10 valve design, §14 ICA, §15-18 (electrical/HVAC/corrosion/QA), Appendix I/II/V/VI/VII. Two anomalies in the source worth recording: (1) pages 148-149 carry a different footer ("Revision: Final Draft / Classification: Design Guidelines") vs "Revision: 01 / Classification: R" elsewhere — Appendix IV may be a draft insert; treat Table 33 values as subject to confirmation with NWS. (2) §11.2 and §12.1 both reference a "Table 27" numbering clash with GUD-203's Table 27 (STP site selection) — always cite document + page, not table number alone. Priority ranking of the MISSING items for the criteria file: buffer zones (Tab 8), N+1 sizing, remote-areas rule, MCDA/options method, WW model calibration, VE threshold are the six that materially bind the current W-iteration work (STP siting, 3-options exercise, SewerGEMS deliverable); the rest are survey/workflow rows.

### [MISREAD] §12c Tanker catchment 25 km — 'not in GUD; R0 assumption' note
**Ref:** G1-p80 §8.1

> Remote Areas shall be defined as locations that meet one or more of the following criteria: ● Not connected to existing centralised water or wastewater networks ● Settlements located approximately 25 km or more from existing centralized water or wastewater networks ● Communities with population less than 500 residents or fewer than 100 plots at the end of design period

**Action:** Replace 'not in GUD; R0 assumption' with: 'aligns with GUD-201 §8.1 Remote Areas definition (G1-p80): settlements ~25 km or more from existing centralized networks, or <500 residents / <100 plots at end of design period, are Remote Areas to be served by on-site solutions (septic/holding tanks/package plants) rather than network connection. R0 applied the same 25 km as a tanker catchment radius — cite G1-p80 and confirm the reading with NWS.'

### [MISSING_FROM_CRITERIA] STP / pumping station minimum buffer-zone distances (Table 8)
**Ref:** G1-p43–44 §6.1.3.3 Tab 8

> the Table 8 gives the minimum distancing buffer requirements, subject to NWS approval and the results of the Environmental and Social Impact Assessments. ... STP (small/medium) 500 m 500 m ... STP (large) 300 m –1000 m 300 m –1000 m Based on odour modelling (5 Odour Units OU contour) ... Sewage Pumping Station 30 m 20 m Noise/vibration setback aligned with WWTP industrial buffers

**Action:** Add to §9 STP siting: Minimum buffer zones (G1-p43–44 Tab 8, subject to NWS approval + ESIA): STP small/medium 500 m to residential AND to industrial; STP large 300–1000 m based on odour modelling (5 OU contour); small STP <150 PE 10–30 m (10 m if fully enclosed); sewage pumping station 30 m residential / 20 m industrial. Criteria file currently says only 'buffer from residential' with no numbers — for the ultimate ~49,700 m³/d (Large) STP the odour-modelled 300–1000 m band applies.

### [MISSING_FROM_CRITERIA] N+1 process capacity sizing for STPs, reservoirs and pumping stations
**Ref:** G1-p33 §4.3

> the designer should adopt a modular approach and adopt a process capacity sizing of N+1, N being the number of elements required to meet the average day flows and N+1 to meet the peak capacity requirements. N refers to the number of process elements (e.g. pumps, storage cells in a reservoir complex, treatment trains).

**Action:** Add: At site level (treatment plants, reservoirs, pumping stations) adopt modular N+1 process capacity: N elements meet average day flows, N+1 meets peak capacity (G1-p33 §4.3). Broader than the GUD-203 p39 small-PS duty/standby rule already listed — applies to STP process trains and storage cells too.

### [MISSING_FROM_CRITERIA] Remote Areas / on-site wastewater solutions (definitions + methods + cost ratios)
**Ref:** G1-p80 §8.1, p83 §8.4.1, p84 §8.4.2

> Decentralized compact treatment units (package plants) for communities with a population between 50-5,000 inhabitants.

**Action:** Add: Remote Areas = ~≥25 km from centralized networks, or <500 residents / <100 plots at end of design period (G1-p80). Wastewater there: septic tanks per Oman Private Sewage Disposal Code, holding tanks with vacuum-tanker emptying, or decentralized package plants for communities of 50–5,000 inhabitants (G1-p83); TSE from package plants stored min 1 day (G1-p84). Simplified remote-option costing: energy 0.8 kWh/m³, annual O&M 5% of CAPEX (G1-p84). Governs which Ibri outlying settlements should NOT be networked — interacts with working rule 9 (absorb pockets <50 plots).

### [MISSING_FROM_CRITERIA] Multicriteria options appraisal method (min 3 options, 25-yr NPV @ 5%, 10% sustainability tie-break)
**Ref:** G1-p95–96 §12, p106 §12.9, p99 §12.5.1

> The designer shall develop a minimum of three (3) design options ... The time horizon adopted to conduct the evaluation for each of the parameters is 25 years. ... Unless otherwise instructed by NWS, the discount rate to be applied is 5%. ... If equivalent options are within 10% Total Lifetime Cost, the more sustainable option will be adopted.

**Action:** Add a §-row for the ≥3-options exercise: minimum three design options with equivalent functional requirements/reliability; guidance mix = one NBS/environmental-ambition option, one international best-in-class option, one standard current-practice option (G1-p95 §12.1); evaluation horizon 25 yr; LCCA/NPV discount rate 5% unless NWS instructs otherwise (G1-p96); NWS sets MCDA weightings; if options are within 10% Total Lifetime Cost the more sustainable option is adopted (G1-p106 §12.9). Carbon footprint mandatory at feasibility/design, benchmarked vs NWS intensity 1.17E-03 tCO2eq/m³ treated effluent (G1-p99).

### [MISSING_FROM_CRITERIA] Formal Value Engineering mandatory for STP/PS > OMR 2M at concept and preliminary stages
**Ref:** G1-p93 §11.2 Tab 27 footnote

> # for sewer treatment plant or pump station that has a value of >2 M, formal VE during the concept and preliminary stage is required.

**Action:** Add: VE thresholds (G1-p93 Tab 27): projects ≥ OMR 5M need a formal VE study by an independent VE-certified consultant at concept+preliminary; footnote lowers the trigger for this project type — any sewer treatment plant or pump station > OMR 2M requires formal VE during concept and preliminary stages.

### [MISSING_FROM_CRITERIA] Wastewater hydraulic model methodology, calibration acceptance, and submission per design phase
**Ref:** G1-p144–145 App III, p109 §13.4.2

> Table 32 Wastewater Model Calibration Parameters ... Peak Flow ± 10 – 15% Volume ± 15% Timing Correct peak arrival Pump runtime ± 10% ... Hydraulic models (Static, EPS and Surge Analysis) to be submitted to NWS after each design phase included the final models after construction.

**Action:** Add for the SewerGEMS deliverable: methodology per WaPUG/CIWEM Code of Practice and US EPA SWMM manuals; modelling at design phase AND after construction; calibration acceptance (G1-p145 Tab 32): peak flow ±10–15%, volume ±15%, correct peak-arrival timing, pump runtime ±10%; hydraulic models (static, EPS and surge) submitted to NWS after each design phase incl. final as-built models (G1-p109); model must run all scenarios error-free before submission, with background image/shapefiles (G1-p141–142).

### [MISSING_FROM_CRITERIA] Headroom Factors — Adh Dhahirah WSZ 13/14 (Appendix IV Table 33)
**Ref:** G1-p31 §4.1 + G1-p148–149 App IV Tab 33

> The capacity of the transmission system shall be designed to include the consumption, necessary peak factors (peak day of the peak week), losses and headroom factors ("used to determine the required extra capacity on top of the estimated water demand in Oman to avoid water shortages in the future", HR Factor Study, October 2023).

**Action:** Add with a caveat: water transmission capacity shall include 'consumption, necessary peak factors (peak day of the peak week), losses and headroom factors' (G1-p31 §4.1); Table 33 gives Adh Dhahirah Zone 1 (WSZ 13) 1.01 (2022) rising to a 1.06 plateau from 2034, Zone 2 (WSZ 14) rising to 1.07 from 2033 (G1-p148–149). Headroom is defined as extra WATER-supply capacity to avoid shortages — its applicability to wastewater/STP inflow is NOT stated and would risk double counting with the +10% STP margin (G1-p73). Record it and settle applicability with NWS at kickoff.

### [MISSING_FROM_CRITERIA] Climate-change resilience: 50-yr horizon, +2 °C and +4 °C scenarios
**Ref:** G1-p33 §4.4

> The following events are to be considered for the design at 50 years horizon (even if the design lifespan of the asset may be lower) ... will be evaluated at both +2 °C and +4 °C average world temperature rises v. pre-industrial levels as recommended by the Intergovernmental Panel on Climate Change (IPCC).

**Action:** Add to STP siting / flood criteria: resilience events assessed at 50-yr horizon even if asset design life is shorter, using an NWS-agreed climate model, evaluated at both +2 °C and +4 °C IPCC world-temperature rises; impacts include changed flood frequency/intensity on site selection (G1-p33 §4.4). Supplements the 25/100-yr flood levels already listed from GUD-203 p63.

### [MISSING_FROM_CRITERIA] STP shall use several process lines for phased design horizons
**Ref:** G1-p53 §6.6.2

> Treatment plants shall be designed using several process lines allowing additional capacity for different design horizons or phases.

**Action:** Add to §9 (feeds the pivotal STP-phasing decision): 'Treatment plants shall be designed using several process lines allowing additional capacity for different design horizons or phases' — mandatory wording supporting phased STP build-out for start/2030/2055/ultimate (G1-p53 §6.6.2).

### [MISSING_FROM_CRITERIA] Pre-treatment for tanker-received and non-domestic sewage at STP
**Ref:** G1-p55 §6.8

> In the case of receiving tankers and/or non-domestic sewage, appropriate pre-treatment processes shall be selected.

**Action:** Add to §9: STP design shall include screens, grit chambers, FOG removal; and specifically 'In the case of receiving tankers and/or non-domestic sewage, appropriate pre-treatment processes shall be selected' (G1-p55 §6.8) — binding given yellow tankers ≈17% of STP inflow (G1-p73).

### [MISSING_FROM_CRITERIA] Max 35% built footprint of allocated land; 5 m boundary setbacks
**Ref:** G1-p50 §6.4.2

> The total built footprint of all structures shall not occupy more than 35% of allocated land. ... Setbacks from site boundaries shall be observed at all times, with a minimum of five meters.

**Action:** Add to §9 land footprint row: total built footprint of all structures ≤35% of allocated land (remainder for circulation, buffers, safety setbacks, future expansion); boundary setbacks min 5 m (G1-p50 §6.4.2). Affects STP land-take on top of the m²-per-m³/d rates from GUD-203 Tab 28.

### [MISSING_FROM_CRITERIA] TSE reservoirs minimum 24 h storage
**Ref:** G1-p31 §4.1

> TSE reservoirs shall be designed to have a minimum storage capacity of 24 hours.

**Action:** Add to §12b (TE network): 'TSE reservoirs shall be designed to have a minimum storage capacity of 24 hours' (G1-p31 §4.1). Note remote-area package-plant TSE tanks need min 1-day storage too (G1-p84).

### [MISSING_FROM_CRITERIA] Surge analysis operational criteria (N+1 pump events; negative-pressure exception for WW/TSE force mains)
**Ref:** G1-p146–147 App III

> The maximum number for simultaneous pump startups and shutdowns shall follow the N+1, where N is the number of pumps at any given station. ... NOTE: Only for the Forced Mains in Wastewater or TSE networks, a negative pressure (air entering the pipe at the air valve) can be acceptable for the surge analysis as long as the surge protection and hydraulic equipment is adapted to this situation.

**Action:** Add to §8 force mains: transient analysis in NWS-approved software; simultaneous pump start/stop events modelled to N+1 (N = pumps at the station); no vapour cavities/column separation; min pressure not below manufacturer limit or −0.2 bar below atmospheric, whichever is higher; max pressure ≤ hydraulic test pressure / lowest component rating; zero-roughness run first to capture worst case, then realistic roughness with sensitivity check. Exception: only for wastewater/TSE force mains, negative pressure (air entry at air valve) is acceptable if the surge protection and hydraulic equipment is adapted (G1-p146–147 App III).

### [MISSING_FROM_CRITERIA] Design-phase cost accuracy and minimum phase deliverables (Table 2)
**Ref:** G1-p17–19 §1.6 Tab 2

> Estimate costs and schedule with planning-level accuracy @ +-30%. ... Provide cost and schedule accuracy (reducing contingencies and uncertainty) to +-20%. ... Accurate quantities and cost estimates to +-10%

**Action:** Add a workflow row: cost/schedule accuracy targets — feasibility ±30%, preliminary/concept ±20%, detailed ±10% (G1-p17–18); Table 2 minimum contents per phase requires Flood Protection Assessment at ALL three phases, optioneering/whole-life costing at feasibility+preliminary, hydraulic routing + initial capacity sizing at feasibility, steady-state time-series model + water-hammer risk at preliminary (G1-p19–20).

### [MISSING_FROM_CRITERIA] Topographic data accuracy per design stage (Table 5)
**Ref:** G1-p36 §6.1.1 Tab 5

> Preliminary / Concept design ... 0.25–1.0 m [horizontal] 0.05–0.5 m [vertical] ... Detailed design ... 0.02–0.10 m 0.01–0.05 m

**Action:** Add to §12 Surveys: required topo accuracy (95% conf.) — feasibility: 1–5 m horizontal / 0.5–2 m vertical (existing DEM acceptable); preliminary/concept: 0.25–1.0 m horizontal / 0.05–0.5 m vertical (UAV photogrammetry with ground control, LiDAR, GNSS RTK); detailed: 0.02–0.10 m horizontal / 0.01–0.05 m vertical (G1-p36 Tab 5). Implication: the 5 m DTM is feasibility-grade only — concept-stage invert/slope claims near the 0.75–1.0 mm/m minimum gradients need preliminary-grade survey before they harden.

### [MISSING_FROM_CRITERIA] Soil investigation spacing for sewer networks (Table 7)
**Ref:** G1-p40–41 §6.1.2.2 Tab 7

> Secondary & Tertiary Gravity Sewer Trial trench Borehole ≤3.0 >3.0 100 ... Primary Gravity Sewers Trial trench Borehole ≤3.0 >3.0 500 ... NWS is to be consulted to approve the spacing of soil investigation for networks.

**Action:** Add to §12 Surveys: geotechnical investigation spacing for networks (NWS to approve): secondary & tertiary gravity sewers — trial trench ≤3.0 m depth / borehole >3.0 m at 100 m spacing; primary gravity sewers and force mains — 500 m spacing (G1-p40–41 Tab 7). Geophysical investigation mandatory at earliest stage for STPs, pumping/lifting stations and major wadi/falaj/road crossings (G1-p40 §6.1.2.1).

---
## s:gud203-flow — 0 confirmed, 12 issues

> Page numbering confirmed: PDF 1-based page == printed page ("Page 3 of 201" footer on PDF page 3; total 201 pp). Flow-estimation conflict check: PAM-GUD-203 carries NO independent flow-estimation/design-flows chapter — TOC (p3-8) shows §1 Intro, §2 Terminology (delegates definitions/numbering to GUD-201, p14), §3 Property Connections, §4-10 (already audited), §11 H2S/Odour, §12 Emergency Overflows & Sea Outfalls, §13 Inspections & Surveys, §14 Associated Documents. Incoming-flow definition sits only in §10.2.1 Tab 29 (p65, already in criteria §9) and explicitly defers infiltration to "AM/PAM-GUD-201" — no conflict with GUD-201 found anywhere in the sweep zone. §12.2 Sea Outfalls (p192-196) judged not applicable to inland Ibri (noted d/D 91%, 0.75/3.0 m/s outfall velocities in case a TSE outfall ever arises). §1.1 p9 general governance worth remembering: "Where any deviation from these criteria is considered necessary by the designer, it shall be justified and substantiated by a detailed analysis." §3.6 p19 corroborates existing criteria §5 rows (>=90 deg inlet angle, no penetrating connection, falls >600 mm need external backdrop) — consistent, no action. Read method: PyMuPDF text extraction (Read tool's PDF rendering unavailable — pdftoppm not installed); text layer is clean and complete including table content. Source: D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf; criteria file: D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/_BRAIN/02_DESIGN_CRITERIA.md.

### [INCOMPLETE] §6 Inverted siphons — "avoid; only where no other feasible means (scope TOR)"
**Ref:** p182 §11.5.3.1(c)

> Wherever possible, discharges shall be submerged to absorb hydraulic energy and minimise turbulence. Inverted siphons shall not be allowed.

**Action:** Add GUD-203 ref and strengthen: PAM-GUD-203 §11.5.3.1(c) p182 flatly states "Inverted siphons shall not be allowed" (odour/H2S design of pumping facilities & force mains). This is stronger than the scope-TOR 'avoid where no other feasible means' — any siphon proposal is a formal deviation needing justification per §1.1 p9. Row ref should read: scope p12(60); p182 §11.5.3.1 (prohibition).

### [INCOMPLETE] §4 Property connection cover — min 600 mm
**Ref:** p19 §3.5

> For Property Connection Sewer a minimum cover of 600 mm is required and can go up to 1.50 m depth (in square dimension 800x800).

**Action:** Value confirmed, but source also caps the depth: PC sewer cover 600 mm minimum and up to 1.50 m depth (in 800x800 square chamber). Add the 1.5 m upper bound — it constrains how deep a main can sit while still receiving direct property connections.

### [INCOMPLETE] §12 (criteria file) Surveys row — topo/DTM/CCTV
**Ref:** p197 §13.1-13.2, p198 §13.3, p199-200 §13.4

> The Designer shall conduct and provide with the Tender Documents thorough inspections to specify the initial condition of the existing structure ... It must be conducted according to standard NF EN 13508-2.

**Action:** Stated content confirmed verbatim on p197. Add three omitted mandatory/scoping points: (1) CCTV is a Designer obligation to conduct AND provide with the Tender Documents; (2) underground-services detection must include irrigation falaj, with benchmark accuracy ±0.05 m to Order C Class 3 (p198); (3) geotech boreholes min 5.0 m below pipe invert for shallow pipelines, deeper where dewatering/shoring design needs it (p199-200).

### [MISSING_FROM_CRITERIA] Trade effluents / non-domestic connections policy
**Ref:** p20 §3.10

> the discharge into the sewer shall comply with Appendix 3 of Royal Decree No. 115/2001 ... Customers shall submit an agreement with NWS as per AM-PRO-209 Non-Domestic Wastewater Standards & Procedure and, if necessary, to adequate pre-treatment validated by NWS.

**Action:** Add row: Non-domestic (trade) discharges to sewer shall comply with Appendix 3 of Royal Decree 115/2001 limits; customer agreement with NWS per AM-PRO-209 required; NWS-validated pre-treatment if necessary. Load-relevant: governs what industrial/commercial flows and loads may enter the network and reach the STP.

### [MISSING_FROM_CRITERIA] Tertiary network slopes (Table 5)
**Ref:** p18 Tab 5

> Property Connection Sewer | Property Connection | 3 % | 10 % ... Rider Sewer | Tertiary Sewage Network | 1 % | 10 % ... Lateral Sewer | Tertiary Sewage Network | 1 % | 10 %

**Action:** Add row: Property Connection Sewer gradient min 3% / max 10%; Rider Sewer and Lateral Sewer min 1% / max 10% (p18 Tab 5). Criteria §2 min-gradient table starts at DN200 mains only — tertiary minimums are separate and much steeper.

### [MISSING_FROM_CRITERIA] PC sewer size/material/length + HCC layout
**Ref:** p18 Tab 4, p17 §3.2, p19 §3.4

> The length of the PCS should not exceed 50 m in order to allow maintenance. If necessary, a manhole will be added.

**Action:** Add: PC Sewer 150 mm minimal, PVC-U/HDPE, open trench (p18 Tab 4); PCS length shall not exceed 50 m else add a manhole; HCC usually 2.5 m from property boundary in public ROW; up to ~3 HCC may share a rider sewer; HCC depth 1.2-2.0 m (p17, p19). Criteria has only OD160 (p22 Tab 6) and the 45 m lateral limit — the 50 m PCS limit is a distinct rule.

### [MISSING_FROM_CRITERIA] Odour limits at STP/PS boundary + continuous monitoring
**Ref:** p165 §11.3.1, p170 Tab 90

> a. Urban areas/near residential: 3-5 OU/m³ b. Industrial areas: 10-15 OU/m³ c. Rural / isolated areas: 10-20 OU/m³ ... NWS requires continuous odour monitoring for all its STP and pumping facilities.

**Action:** Add row: odour at STP boundary — urban/near residential 3-5 OU/m3, industrial 10-15, rural/isolated 10-20 (p165); compliance Table 90: 5 OU/m3 sensitive area / 15 OU/m3 industrial at boundary wall, continuous online e-noses (min 3) with spot checks never exceeding the standard (p170); comply with MD 41/2017; NWS requires continuous odour monitoring for ALL STP and pumping facilities per BS EN 13725:2022 / ASTM E679. Feeds STP siting/buffer decision (criteria §9).

### [MISSING_FROM_CRITERIA] STP odour treatment: multi-stage, N+1, efficiencies
**Ref:** p175 §11.5.2.4, p176 Tab 93-94, p174 Tab 92, p170 §11.5.2.1

> In most cases multi-stage odour control is required at STPs to meet NWS odour level requirements at the facility boundary. Two-stage systems shall be based on a bio-trickling filter followed by a chemical scrubbing unit. ... the efficiency of the integrated odour control system shall be 99.95 % H2S Removal and 85 % Odor Removal ... Every odour control system shall provide N+1 redundancy.

**Action:** Add row: odour abatement assessment study + dispersion modelling mandatory to justify odour unit (or its absence) (p170); in most cases multi-stage odour control required — two-stage bio-trickling filter + chemical scrubber, three-stage (+carbon) when needed, integrated efficiency 99.95% H2S / 85% odour removal; every odour control system N+1 redundancy; design temp 35-45 degC process / 0-55 degC equipment; final treated air per Table 93 (H2S <0.1 mg/m3 at 99.95%, NH3 <1 mg/m3 at 90%) (p175-176); ventilation rates Table 92 incl. PS wet wells 20 ACH (p174).

### [MISSING_FROM_CRITERIA] H2S management: designer deliverable + network design-for-odour rules
**Ref:** p162 §11.1, p166 §11.3.2, p168 §11.4.2(5)

> It is the responsibility of the designers of Sewage networks, Pumping stations, forced mains to consider the H2S management throughout the project and provide NWS with a dedicated evaluation of the preventive (re-sizing, injections of chemicals) and corrective measures (monitoring, flushing tanks, specific coatings, odour treatment). ... Retention times shall be kept to a minimum, and turbulent flows shall be avoided. Over-sizing of trunk sewers creating deposition shall be also avoided ... Consider installing parallel smaller diameter sewers for low flow conditions to reduce retention time.

**Action:** Add row: designers of sewage networks/PS/force mains shall provide NWS a dedicated H2S management evaluation (preventive: re-sizing, chemical injection; corrective: monitoring, flushing, coatings, odour treatment) — a design-report deliverable (p162). Networks shall be designed to minimise odour-generating conditions; retention times kept to minimum, turbulence avoided, no over-sizing of trunk sewers creating deposition; consider parallel smaller-diameter sewers for low-flow conditions (p166, p168). Directly load-relevant to trunk sizing at early-year low flows in this project.

### [MISSING_FROM_CRITERIA] PS/FM odour-driven design rules (supplements criteria §7-§8)
**Ref:** p181-182 §11.5.3.1

> The use of pumping stations and pressure mains shall be avoided whenever gravity sewer designs are feasible and cost effective. ... Consider twinning of force mains to minimise retention time at low flows. ... Wherever possible, discharges shall be submerged to absorb hydraulic energy and minimise turbulence.

**Action:** Add: PS and pressure mains avoided whenever gravity feasible and cost-effective; design to minimise hydraulic detention time — consider twinning force mains for low-flow retention; FM discharges submerged wherever possible to minimise turbulence/H2S stripping; provide for FM to drain back to wet well between cycles where possible, avoid partially-full FM conditions; wet-well levels shall not impede free air movement through the sewer except above peak dry weather flow (p181-182).

### [MISSING_FROM_CRITERIA] H2S risk assessment methods (Fayoux, Pomeroy-Parkhurst)
**Ref:** p185 Tab 99, p186 §11.5.3.4

> If the sum of score is between 0 and 5: No risk; between 5 and 10: Low risk, between 10 and 30: Significant risk, and between 20 and 30: Certain risk. ... (EBOD) = (BOD) (1.07)^(T-20)

**Action:** Add method row: qualitative H2S risk via Fayoux scoring (temperature, residence time, velocity, redox — sum 0-5 no risk, 5-10 low, 10-30 significant/certain risk; parameters at max temperature and night-time flow) (p185 Tab 99); quantitative sulphide prediction via Pomeroy-Parkhurst equation with EBOD = BOD5 x 1.07^(T-20), modified S = Ks.BOD5.t.f(T) for pumping mains (p186). Needed for septicity screening of the long Ibri trunks/FMs at early-stage low flows.

### [MISSING_FROM_CRITERIA] Emergency overflow structure sizing (network/PS)
**Ref:** p191 §12.1.1

> Retention Basins ... Sizing corresponds to 24h of nominal flow ... Relief Sewer ... Sizing corresponds to 1.5 times the nominal flow

**Action:** Add row: emergency overflow retention basins sized for 24 h of nominal flow (emptied by yellow tanker; sedimentation/disinfection often equipped); relief sewers sized at 1.5 x nominal flow (p191). Distinct from the STP emergency lagoon 48-72 h (p73) already in criteria §9 — this governs network/SLS overflow storage.

---
## s:gud202-tse — 0 confirmed, 9 issues

> Page numbering: PDF page == printed page, confirmed by footer "Page 50 of 177" on PDF page 50 — no offset. Tooling: the Read tool could not render PDF pages in this environment (poppler missing), so pages were read via PyMuPDF full-text extraction; all quotes are verbatim extracted text. Scope discipline: existing 12b network-hydraulics rows (velocity, head loss, roughness incl. the TE +30%/−10% note on p104, pressures, materials) were NOT re-audited per task instructions — except the demand-side Tanker Filling Station row, which drew one INCOMPLETE. Two observations outside the demand scope, flagged for whichever auditor owns 12b: (1) G2-p137 states min pressure 1.5 bar at "worst point peak day, peak hour" — the criteria row says only "peak-hour"; (2) the same page conditions the fire-flow positive-pressure rule on "assuming zero parallel domestic use during fire", which the criteria row omits. Structural conclusion for the parent: GUD-202's TSE demand content is confined to (a) Reservoirs §5 storage-vs-peak-day-demand rules, (b) TSE Tanker Filling Stations §12, and (c) generic sizing-on-projected-demand clauses; irrigation unit rates genuinely do not exist in this volume, so the TE-network demand build must source rates from the NWS master plan / IMP or MoAFWR data — recommend adding this as an explicit GAP entry. Distribution §9.1.3 lists only a generic nodal-demand allocation method (district population → nodal demand), no rates — mentioned here for completeness, not worth a criteria row.

### [INCOMPLETE] Tanker filling stations (existing 12b row, G2-p154)
**Ref:** G2-p154 §12.4.1, §12.4.2

> Design capacity shall be based on: Number of consumers to be served by tankers in the area / Average daily water demand in the service area / Peak hour factors (typically 1.5-2.0 times average flow) / Future growth projections for a minimum of 10 years / Seasonal demand variations. The minimum design capacity shall accommodate: Peak hour flow rate during the maximum demand day / Concurrent filling of multiple tankers (minimum of two) / Operational reserve capacity of 20% ... Storage facilities, if required, shall: Provide minimum 2-hour peak demand storage ... Be sized to accommodate diurnal demand variations

**Action:** Row keeps PF 1.5–2.0, ≥2 concurrent bays, +20% reserve, ≥1 m³/min per bay @ 2–4 bar — all CONFIRMED — but must add the omitted capacity conditions: demand basis = number of tanker-served consumers + average daily demand of service area; future growth projections for a MINIMUM of 10 years; SEASONAL demand variations; minimum capacity = peak-hour flow rate during the maximum demand day; on-site storage (if provided) ≥ 2-hour peak-demand storage sized for diurnal demand variations. Ref stays G2-p154 §12.4.1–12.4.2.

### [MISSING_FROM_CRITERIA] TSE tanker filling stations as TE-network demand nodes
**Ref:** G2-p152 §12.1, §12.2

> Similarly, Treated Sewerage Effluent Filling Stations shall be defined as a designated facility for the controlled filling of authorised green tankers with TSE for distribution for irrigation and industrial uses. ... Tanker Filling Stations shall comply with all applicable regulations including Regulatory Authority Decision No. 31/2025 regarding the regulation of independent tanker operation in the water and wastewater sector.

**Action:** | TSE tanker filling stations | TSE TFS = facility for controlled filling of authorised **green tankers** with TSE for distribution for **irrigation and industrial uses** — model as demand nodes on the TE network; comply with Regulatory Authority Decision No. 31/2025 (independent tanker operation) | G2-p152 §12.1–12.2 |

### [MISSING_FROM_CRITERIA] TSE TFS hydraulic supply / storage (12 h average demand)
**Ref:** G2-p155 §12.5.1

> For Potable water TFS, the hydraulic supply shall be any of the 2 option below ... Ground reservoir + VFD pumping station + diesel generator for 48hrs of peak demand, / Elevated tank for 48hrs of storage capacity. For the TSE TFS, the hydraulic supply can be adapted : STP or Ground reservoir + VFD pumping station for 12hrs of average demand.

**Action:** | TSE TFS supply & storage | TSE TFS supplied from **STP or ground reservoir + VFD pumping station sized for 12 hrs of AVERAGE demand** (contrast potable TFS: ground reservoir + VFD PS + 48-h diesel genset for peak demand, or elevated tank with 48 h storage) | G2-p155 §12.5.1 |

### [MISSING_FROM_CRITERIA] TFS connection point restriction (no transmission-main tap)
**Ref:** G2-p153 §12.3.1, G2-p156 §12.6.1

> NOTE : No water TFS shall be installed or connected to a Transmission line. ... Direct connection to water or TSE transmission mains shall be avoided whenever possible and shall only be considered as a last resort; any proposal for such connection must be accompanied by comprehensive technical documentation demonstrating why connection to the distribution network (downstream of service reservoirs) is technically unfeasible.

**Action:** | TFS connection point | No TFS on transmission lines (p153 NOTE); direct connection to water **or TSE** transmission mains is last-resort only, requiring technical documentation proving connection downstream of service reservoirs (distribution network) is unfeasible — governs where TSE TFS hang off the TE network | G2-p153, p156 §12.6.1 |

### [MISSING_FROM_CRITERIA] TFS siting buffers and needs assessment
**Ref:** G2-p153 §12.3.1

> Min. 200 m apart from the residential plot and 500 m away from public amenities viz., school/Park/Mosque/Eid prayer area ... For areas with existing or planned water distribution network coverage, any proposed Tanker Filling Station must be supported by a comprehensive needs assessment that provides strong evidence of necessity

**Action:** | TFS siting | ≥ 200 m from residential plots; ≥ 500 m from public amenities (school/park/mosque/Eid prayer area); spilled water gravitates to wadi/low level without flooding neighbours; spacing between TFS from population density, expected tanker numbers, supply infrastructure, future plans; where distribution-network coverage exists or is planned, a comprehensive needs assessment is mandatory | G2-p153 §12.3.1 |

### [MISSING_FROM_CRITERIA] Reservoir storage times by class (applies to water & TSE storage)
**Ref:** G2-p53–54 §5.1, §5.2.1–5.2.5

> The size of the reservoir in volume is determined by the number of hours of storage which refers to 24h of the peak day of water demand. ... Storage time shall be a minimum of 4 hours of the downstream peak day water demand. ... [Distribution Storage Reservoirs] Storage time shall be a minimum of 48 hours. ... [Elevated tank] Storage time shall be a minimum of 4 hours. However, for small villages having less than 2,500 inhabitants, the elevated tank may be designed to satisfy one full day demand. ... [Break Tank] Storage time shall be 2 hours.

**Action:** | Reservoir storage times | Storage expressed as hours of the 24-h **peak-day** demand (p53 example given); transmission-pumping reservoirs ≥ **4 h** of downstream peak-day demand (larger allowed for energy optimisation); distribution storage reservoirs ≥ **48 h**; elevated pressure-balancing tanks ≥ **4 h** (villages < 2,500 inhabitants: one full day); break tanks **2 h** (need justified vs PRV); strategic reservoirs (≈≥100,000 m³) studied case-by-case incl. desal internal storage ≈ 1 day plant capacity; holding capacity to maintain LOS ~48 h during major shutdown | G2-p53–54 §5.1–5.2 |

### [MISSING_FROM_CRITERIA] Storage demand basis: NWS master-plan forecast + NCSI; two-peak-day effective storage
**Ref:** G2-p54–55 §5.3.1

> The capacity allocation for each type of reservoir shall be governed by the project's demand calculations based on the latest version of NWS master plan demands forecasting and trending according to National Centre for Statistics and Information (NCSI). ... In general, the designer is to consider two peak day demand, pumps off, storage capacity. ... In addition to the two peak day demand and for Distribution Storage Reservoirs only, water required for firefighting shall be included as per the Public Authority for Civil Defense and Ambulance (CDAA) guidelines. ... The dead storage volume should not be more than 5% of the reservoir's effective volume. ... The Effective Storage (ES) or the service storage for peak day is the volume of storage aiming to meet two peak day demands in a water distribution system and is excluding the water required for firefighting. ... For transmission pumping reservoirs, the difference between HH and LL levels shall ... accommodate the maximum hour of a peak week.

**Action:** | Storage demand basis | Reservoir capacity governed by project demand calculations from the **latest NWS master plan demand forecasting, trending per NCSI**; general rule: **two peak-day demand, pumps-off** storage; Distribution Storage Reservoirs ONLY add CDAA firefighting volume; Effective Storage = two peak-day demands EXCLUDING firefighting (HH–LL × area); dead storage ≤ **5 %** of effective volume; ≥ 2 similar compartments when > 200 m³ (except elevated tanks); transmission-pumping HH–LL must also accommodate the **maximum hour of a peak week** | G2-p54–55 §5.3.1 |

### [MISSING_FROM_CRITERIA] Transmission/pipeline sizing must carry present + projected demand at 25-yr horizon
**Ref:** G2-p103 §7.1.2–7.1.3.1, G2-p8 §1.1

> The following factors should be considered when sizing a pipeline: ... The designed capacity (present and projected demand); ... The peak velocity as high as 2.0 m/s, at a horizon of 25 years for transmission, is possible ... The intended design lifetime shall be 25 years for all kinds of assets, unless otherwise stated.

**Action:** | TE pipeline sizing basis | Pipeline design validated systematically by hydraulic study; sizing factors include **the designed capacity (present and projected demand)**, min/max pressure, allowable head loss, stagnation/water-hammer risk, CAPEX vs OPEX; velocity criterion set at a **25-year horizon**; all hydraulic calcs on nominal internal diameters; design lifetime **25 years for all assets** unless otherwise stated | G2-p103 §7.1.2–7.1.3, G2-p8 §1.1 |

### [MISSING_FROM_CRITERIA] TSE irrigation/landscaping unit demand rates — absent from PAM-GUD-202 (GAP, not a criteria omission)
**Ref:** G2-p13 + full-document keyword sweep

> The present Guidelines cover the design of potable water and treated effluent systems. [p13 — yet no irrigation unit-rate table exists anywhere in the volume; TSE-specific clauses are limited to p8/p13 scope, p59 liners, p70 PS, p104 TE roughness note, p119 air valves, p152–156 TSE TFS]

**Action:** | TSE irrigation demand rates | **PAM-GUD-202 provides NO irrigation application rates, landscaping per-area (l/m² or m³/ha) rates, crop factors, or seasonal irrigation coefficients** — full-volume keyword sweep (irrigat/landscap/garden/seasonal/demand/agricultur/evapotranspir/l-m²/ha) returns only the TFS clauses above; the only 'seasonal' demand reference is the TFS bullet 'Seasonal demand variations' (p154). TSE demand quantities must therefore come from the NWS master-plan demand forecast (G2-p54) or project-specific data (MoAFWR / municipality green-area schedules) → log as pending-data GAP in _BRAIN/05_GAPS.md so nobody cites GUD-202 for irrigation rates | G2 full sweep, 177 pp |
