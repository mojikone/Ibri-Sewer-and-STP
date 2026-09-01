# What stands between a network solve and a signable sewer design

**Research note, 2026-09-01. W10 produced a network solve with 8 fields per pipe. This
document establishes, from the tender and the guidelines, what a concept design must
contain, what W10 is missing, how NAMA's own contractor built the existing network, and
the exact target for W11a.**

The single most important finding is in one line: **W10 has no chambers.** It has
corridor nodes about 100 m apart, and 65 % of its pipe length sits in reaches longer than
the maximum manhole spacing the guideline allows. Everything a design is judged
on — the schedule, the profile, the model, the take-off, the package — hangs off the
chamber, and none of it can be produced until the chamber exists and every pipe names the
chamber at each end.

## How to read this

| | |
|---|---|
| **[Certain]** | read directly from a source document or measured from the data, with the page or the script named |
| **[Likely]** | a strong inference from evidence that is here, but not stated by anybody |
| **[Guessing]** | filling a gap; the source is silent and I say so |

**Citations.** `G201-p##` = PAM-GUD-201, `G203-p##` = PAM-GUD-203 (printed page = PDF
page in both). `scope-p##` = `Data/scope.pdf`; that file is an extract of the tender
document, so **scope p*n* is printed page *n*+48 of `IBRI TD - Consultancy Services.pdf`**
(scope p2 carries "Page 50 of 204"). `TD-p##` = the tender document's own printed page,
used for material outside the scope extract.

**Sources read for this note.** `scope.pdf` (all 35 pages), TD pp. 147–150, G201
pp. 16–22 and 134–143, G203 pp. 17–36, 38–55 and 197–199, `W8/py/sewnet/` (criteria,
stages, export_gems), `TUTORIALS/T02` §14–16, `W10/docs/W10_SUMMARY.md`, and the W10 and
W8 shapefiles. Measurements come from `W10/py/research/r1_packages.py`, re-runnable, with
its CSVs in `W10/run/research_packages_*.csv`.

---

# Part A — What the client and the guidelines require

## A.1 The three stages are not the three stages

Before any content list: **NWS's guideline and NWS's tender do not use the same stage
names, and this matters for what W10 is allowed to be.**

[Certain] G201-p17 §1.6 lists the project phases as *Project Definition and Feasibility
Study → PIAD → **Concept / Preliminary Design** → Detailed Design*, and then says there
are **three** design stages: Feasibility, "Preliminary (concept)", and Detailed. Concept
and preliminary are one stage in the guideline. Table 2 (G201 pp. 19–22), the only
content list NWS publishes, has three columns: **Feasibility | Preliminary | Detailed**.
There is no concept column.

[Certain] The tender splits them. scope-p3 requires "the Concept, preliminary, detailed
designs and tenders", scope-pp12–16 give a concept stage with its own 40-item deliverable
list, and TD-p147–149 prices and programmes four separate submissions (Concept 60 days,
Preliminary 70, Detailed 90, Tender 61, each plus 21 days NWS review).

[Likely] **Read against G201 Table 2, the tender's Concept stage sits on the
*Feasibility* column, not the Preliminary one.** The evidence is the content itself:
minimum three options (scope-p13), cost estimate by asset category (G201-p21 Table 2,
feasibility only), remote-sensing and historical-records field investigation (G201-p19,
feasibility only), "Hydraulic Design – Routing and Initial Capacity Sizing" (G201-p19,
**feasibility only**), and "Project Phasing" (G201-p21, feasibility only). The tender's
Preliminary stage then matches G201's Preliminary column almost item for item — ±10 %
cost (scope-p16), HAZOP, P&ID, physical field investigation, EPC tender documents.

**This is the anti-gold-plating rule for W11a.** If a row of G201 Table 2 carries `y`
only in the Preliminary or Detailed column, W11a should not attempt it. That single table
settles most of the scope questions below, so it is transcribed in full.

## A.2 G201 Table 2 — Minimum contents required for each Design Phase (pp. 19–22)

[Certain] Transcribed from the source. Column order confirmed from the word positions on
p19 (Feasibility x≈356, Preliminary x≈426, Detailed x≈493). Rows are verbatim; the
"relevant to a sewer network" column is my reading.

| Task / content of deliverable | Feas | Prelim | Detail | Relevant to a sewer network |
|---|:--:|:--:|:--:|---|
| Performance Specifications | y | y | y | design criteria register |
| Site Selection, Routing and Layout | y | y | y | **corridors, trunk route, STP and station sites** |
| Field investigations — remote sensing / historical records | y | – | – | DEM, imagery, NAMA as-built |
| Field investigations — physical, topo, geotech, geophysical (risk ID) | – | y | – | not now |
| Field investigations — physical, topo, geotech, geophysical (construction) | – | – | y | not now |
| Environmental Impact Assessment — Major Risks | y | – | – | wadi, flood, separation |
| EIA — Scoping / Permitting | – | y | y | not now |
| Flood Protection Assessment | y | y | y | **wadi exclusion of pipes and chambers** |
| Environmental and Social Management Plan Specifications | – | – | y | not now |
| Sustainability Strategy (carbon, circular economy, NBS, ICV) | y | – | – | narrative |
| Sustainability Options / Solutions and Specifications | – | y | y | not now |
| Optioneering / Whole Life Costing / Life Cycle Cost estimation | y | y | – | **three options, LCC at 5 % over 25 yr** |
| **Hydraulic Design — Routing and Initial Capacity Sizing** | **y** | – | – | **exactly what W10 did** |
| Hydraulic Design — steady state time series, water hammer risk | – | y | – | not now |
| Hydraulic Design — contingencies, water hammer model and protection | – | – | y | not now |
| Process Design — concept, global sizing, criteria, effluent standards | y | – | – | STP only |
| Process Design — simulation, train sizing, PFD (prelim / detail) | – | y | y | not now |
| Mechanical — process level and pipelines, types | – | y | – | not now |
| Mechanical — equipment, pipelines, appurtenances, specifications | – | – | y | not now |
| Electrical / HVAC / PV / lighting — loads and performance | – | y | – | not now |
| Electrical — specifications and routing | – | – | y | not now |
| P&ID draft / final | – | y | y | not now |
| Value Engineering — system / equipment level | – | – | y | (tender adds VE after concept: scope-p10 item 47) |
| HAZOP informal / formal | – | y | y | not now |
| Permitting scoping / formal | – | y | y | not now |
| ICA functional specs (+ detailed I/O) | – | y | y | not now |
| Corrosion Protection Specifications | – | – | y | not now |
| Civil / Structural — sizing and type | – | y | – | not now |
| Civil / Structural — detailing and material specifications | – | – | y | not now |
| Architectural — massing / for permitting | – | y | y | not now |
| Utility and Road Tie-ins — identification | – | y | – | not now |
| Utility and Road Tie-ins — specification and coordination | – | – | y | not now |
| Commissioning Plan and Requirements | – | – | y | not now |
| **Project Phasing** | **y** | – | – | **phases and packages** |
| Construction Phasing | – | y | – | not now |
| Construction Planning | – | – | y | not now |
| **Cost Estimate — by asset category** | **y** | – | – | **quantity by DN and depth band** |
| Cost Estimate — by system element, cost curve | – | y | – | not now |
| Cost Estimate — Bill of Quantities | – | – | y | not now |
| Procurement Plan | – | y | – | not now |
| Tender Documents EPC | – | y | – | not now |
| Tender Documents — Design, Bid, Build | – | – | y | not now |
| **Drawings — site location, routing, boundaries** | **y** | – | – | **key plan, layout, flow direction** |
| Drawings — layout, routing, connections and cross sections | – | y | – | not now |
| Drawings — layout, routing, connections, cross sections, reinforcement schedules, valve and equipment placement, architectural details, landscaping, fencing | – | – | y | not now |

[Certain] Accuracy bands, G201-pp17–18: feasibility ±30 %, preliminary ±20 %, detailed
±10 %. [Certain] The tender is tighter at preliminary — scope-p16 says ±10 percent for
its preliminary stage and scope-p22 item 28 wants a priced BOQ at 80 % accuracy there,
90 % at detailed (scope-p26 item 6).

## A.3 The tender's own three content lists, side by side

[Certain] All rows read from `scope.pdf`. This is the operative list — it is the contract.

| Item | Concept (§4.1.1, pp. 12–16) | Preliminary (§4.1.2, pp. 16–23) | Detailed (§4.1.3, pp. 24–27) |
|---|---|---|---|
| Network layout | "layout of the main trunk sewers, Main sewers, Laterals, riders and property connections on property map background **including manholes at all junctions**"; flow direction; possible pump/lift station locations; STP location (p12) | designs and drawings of the network incl. house connection design sheets, riders, laterals, trunks, PS, rising mains (p22 item 6) | complete construction set; horizontal and vertical alignment based on house connections, utility survey, geotech (p24) |
| Profiles | "**indicative** longitudinal profiles of the proposed sewer network" (p12) | "Preliminary drawings of Sewer layouts with Horizontal and Vertical profiles" (p22 item 15); plans 1:2500, profiles 1:1000 H / 1:100 V (p23 item 40) | profiles 1:100 V / 1:1000 H carrying sewer line name, stations, distances, ground level, invert level, pipe slope, pipe material, manhole number, ground structure, branch connections, house connections (p26 item 4) |
| Manholes | "manholes at all junctions" on the layout (p12) | "number of manholes & locations" known (p17) | manhole numbering to **NWS's numbering system**, issued to the successful consultant (p25) |
| Hydraulic tables | "Concept hydraulic design calculations and capacities for sewerage network, TE network, STP and sewage pumping stations" (p16 item 36) | hydraulic calculations for sewer and TE pipelines, rising mains and pump stations (p22 item 19) | "hydraulic calculation tables that includes all design results including number, levels and depths of upstream and downstream manholes; slopes, length, diameter and material of pipelines; peaking factor, flow and velocity" (p25) |
| Model | "Concept Hydraulic Design Calculations for Wastewater Network System **based on SewerGEMS software**" (p14); three design years start / 2030 / 2055 / ultimate (p14) | full SewerGEMS simulation **after** the preliminary design is complete; H₂S/septicity model; surge where pressurised (p17) | "Final Hydraulic Design modeling and calculations (SewerGEMS software) … including surge"; WATS model (pp. 24–25) |
| Options | **minimum three** options for the wastewater network, three for TE, three per STP (p13); recommended option on life-cycle cost and risk (p13) | one selected option developed (p16) | — |
| Costs | cost estimates, life-cycle cost, PIAD support (pp. 8, 14, 16) | preliminary detailed cost estimate + priced BOQ, 80 % accuracy, CESMM3 (pp. 22–23) | measured BOQ + priced BOQ 90 %; final estimate ±10 % (p26) |
| House / property connections | "List of Customer / house connection **Excel list**, Existing, future … as per BD requirements" (p12); connections shown on the layout (p12) | "House Connection **Design sheets**" (p22 items 4 and 6); "Wastewater Riders and House Connections Design sheets" in the drawing set (p23) | "Final Wastewater House Connection design and drawings sets" (p25) |
| Pumping / lifting | "Concept sewage pumping station design wherever required" (p15 item 19); trunk mains, rising mains and stations connecting areas to the STP (p13) | pumps, valves, flow meters, ventilation, odour control, E&I recommendations; site layout and architectural drawings (p22 items 16–18) | equipment layout and sections, structural details, surge, I/O list, control philosophy, commissioning plans (pp. 25–26) |
| Packaging | "**Contract Strategy, packages and implementation plans**" (p5 item 7; p16 item 39) | contracting-strategy workshop and **Detailed Contracting Strategy Report** (p21 §4.1.2.8) | tender documents and packages (p27) |
| Surveys | topographic survey and geotechnical investigation *required for concept design* (p12) | full survey, trial pits, utility detection, geo-database (pp. 16, 18) | geotech and utility survey complete **before** detailed design starts (p24) |
| Formats | hard copy + PDF, Word, AutoCAD, searchable (p4 item 6); Excel, Word, AutoCAD, PDF (p10 item 52) | same, plus coloured drawings at required sizes (p23 items 38–39) | A3 in the report, two coloured A0 sets, layout on satellite imagery at A0 (p27) |

## A.4 What must be modelled, and in what

[Certain] scope-p8 item 19: "Hydraulic designs / models in WaterGEMS and SewerGEMS format
or equivalent software." scope-p14: concept hydraulic design calculations for the
wastewater network **based on SewerGEMS**, with the assessment carried out "taking into
consideration that the submission should be in WaterGEMS and SewerGEMS format … and excel
sheet for the three design years start (to be agreed), middle (2030), end (2055) and
ultimate".

[Certain] G203-p24 §4.2.1: gravity systems shall be designed with Colebrook-White (ks =
1.5 mm for all sizes and materials) or Manning, and "the Designer/Contractor shall carry
out the calculations using official licensed software approved by NWS".

[Certain] **G203-p25 scopes the model narrowly:** "Gravity sewage network modelling will
usually be done for the Primary networks; the secondary sewage network can be partially or
totally involved in that type of analysis." Primary = trunk mains, defined at G203-p35 as
diameter above 800 mm, length above 1,000 m without connections, or upstream of the STP or
main pumping station.

[Likely] The defensible concept-stage model is therefore **trunk + sub-mains as modelled
conduits, laterals as loads applied at the manhole where they join**. That satisfies
G203-p25 exactly and scope-p14 in substance, and it keeps the model to a size a reviewer
can open. Modelling 1,883 km of DN200 lateral at concept stage is not required by
anything I can find and would be gold-plating.

[Certain] G201-pp138–140 Appendix III sets the model input requirements. The section is
written for potable water and TSE, but the element data it demands is generic: nodes need
identification, location, elevation and base load; pipes need identification, length,
diameter and roughness; pumps need identification and characteristics; the model must run
all scenarios without errors before submission, with background image and shapefiles.

## A.5 What the sources do **not** say

Stated plainly rather than invented:

| Question | Status |
|---|---|
| Bedding and cover classes for sewers | **Not in G203.** A full-text search returns zero hits for "bedding". G201-p136 puts civil works in **PAM-SPC-4xx** and civil drawings in **PAM-STD-4xx**, neither of which we hold. Cannot be specified from anything in `Data/` |
| Standard chamber details | Same — PAM-STD-4xx. G203-p19 §3.4 gives only two House Connection Chamber forms (rectangular 600 × 750 mm to 1.4 m deep, not under traffic lanes; circular 1.0 m internal, 1.0–2.0 m deep) |
| Manhole numbering | scope-p25: "shall follow NWS (OWWSC)'s numbering system. Sufficient information … will be given to the successful Consultant." We do not have it. NAMA's own as-built pattern (`5A-2-SM.2-MH391`) is the only evidence |
| Geo-database schema | scope-p18 refers to "NWS (OWWSC)'s Geo-Database Specifications" repeatedly. Not held |
| Temporary works / interim outfalls during phased construction | **The scope is silent.** It requires emergency overflow and 5-day emergency lagoons for STP *failure* (scope-p9 items 25–26), which is a different thing. Nothing states how a package is served before its downstream neighbour exists |
| A target number or size of construction packages | **Not stated.** scope-p6 item D.1 leaves packages "subject to NWS acceptance and instruction"; TD-p149 programmes the networks, lifting stations, pumping stations and house connections as **one** tender |
| Maximum depth as a hard number | G203-p33 says "recommended maximum cover for sewer pipes is approximately 10 – 12 m", triggered by excavation **cost**. The 12.00 m used in W8/W10 is a project decision, not a guideline limit |
| Tractive tension τ | G203-p27 gives the method and the constant K but no value in Pa. W8 uses τ = 1.0 Pa as a declared assumption |

---

# Part B — The gap

## B.0 What W10 actually is

[Certain] Measured from the layers.

| | W8 (test area) | W10 (full area) |
|---|---|---|
| Pipe fields | 26 | **8** — `DN, SLOPE_PCT, QADF_M3D, PF, QPK_LS, LEN_M, US_DEPTH, DS_DEPTH` |
| Node/manhole layer | `W8_manholes.shp`, 15 fields, 1,415 chambers | `W10_nodes_depth.shp`, 6 fields, 20,937 corridor nodes |
| Node identity on pipes | `ND_UP` / `ND_DN` | **none** |
| Invert levels | `INV_UP` / `INV_DN` on pipes, `INVERT` on chambers | on nodes only, and from a superseded solve (B.2) |
| Material | `MAT` | none |
| Tier | `TIER` (lateral / sub_main / trunk) | none |
| Velocity, d/D | `VEL_MS`, `DOD` | none |
| Drops / backdrops | `DROP_UP`, `DROP_DN`, `N_DROPS`, `VORTEX` | none |
| Chamber density | 19.8 / km | **11.1 / km** |
| House connections | `ConnectabilityStage`, plot-by-plot | none |
| SewerGEMS export | `W8/sewergems/` (4 layers + loads + procedure) | none |
| Independent audit | 22 named checks, `stages/audit.py` | none |

## B.1 Item by item, with the stage that requires it

[Certain] on the "required at" column — every entry has its citation. The "W10" column is
measured.

| # | Item | Required at | Source | In W10 | Note |
|---|---|:--:|---|:--:|---|
| 1 | **Chamber layer with identity** (ID, cover level, invert level, depth, type) | Concept | scope-p12 "manholes at all junctions"; scope-p16 item 36 | **no** | 20,937 corridor nodes are not chambers |
| 2 | **US / DS chamber ID on every pipe** | Concept | implied by 1; required by SewerGEMS import and by scope-p25's schedule | **no** | the single enabling defect |
| 3 | Chamber at every junction | Concept | G203-p29 §4.4; scope-p12 | partial | junction nodes exist, but are not chamber records |
| 4 | Chamber at change of direction | Concept | G203-p29 §4.4 | **no** | no bend rule in the W10 pipeline |
| 5 | Chamber at change of gradient | Concept | G203-p29 §4.4 | **no** | |
| 6 | Chamber at change of diameter | Concept | G203-p29 §4.4 | **no** | |
| 7 | Chamber at the end of each lateral | Concept | G203-p29 §4.4 | **no** | |
| 8 | **Spacing ≤ Table 12** (100 / 120 / 150 / 200 m by DN) | Concept | G203-p30 Table 12 | **no** | **4,763 of 20,936 reaches breach it, 1,220 km = 65 % of the length; longest reach 6,541 m** |
| 9 | Drops recorded, backdrop above 600 mm, external | Concept (bookkeeping) / Detailed (detail) | G203-p30 §4.4 | **no** | a drop changes the depth, so it belongs at concept as a number |
| 10 | Vortex drop shaft above 2 m backdrop | Concept (flag) | G203-p30 | **no** | |
| 11 | Inlet angle ≥ 90° to the direction of flow | Concept (flag) | G203-p30; G203-p19 §3.6 | **no** | W8 checked and flagged this |
| 12 | One outlet per structure | Concept | user rule / SWNETWROK; a two-outlet junction is not buildable | **no** | 5,394 of 20,937 nodes carry more than one outgoing pipe when snapped |
| 13 | Property / house connections **as a list** | Concept | scope-p12 "List of Customer / house connection Excel list" | **no** | plot loads exist; the connection point does not |
| 14 | Riders and property connections **shown on the layout** | Concept | scope-p12 | **no** | |
| 15 | House connection **design sheets** | **Preliminary** | scope-p22 items 4 and 6; scope-p23 item 40.7 | n/a | **do not attempt now** |
| 16 | Pipe material by diameter and construction method | Concept (indicative) / Detailed (final) | G203-p22 Table 6; scope-p10 §I; scope-p25 "Final recommendations on pipe materials" | **no** | Table 6 is mechanical: PVC-U ≤ DN250, HDPE/GRP above, GRP or lined RCC ≥ 350 mm, GRP / lined RCC / profile-wall HDPE for trunk mains > 600 mm (G203-p35 Table 14) |
| 17 | Bedding and cover classes | **Detailed** | not in G203 at all; PAM-SPC-4xx (G201-p136) | n/a | **cannot be specified — the standard is not held** |
| 18 | Rising main: DN, material, length, duty, velocity, static and friction head, air valves, washouts | Concept (sizing) / Preliminary (detail) | G203-pp50–55; scope-p13, scope-p22 item 14 | partial | `W10_rising_mains.shp` has DN, length, static head, velocity — **no material, no friction head, no TDH, no valves** |
| 19 | Rising main velocity within limits | Concept | G203-p50 §8.1: ≥ 0.75 m/s at design minimum flow, 1.0 m/s intermittent, 1.2 m/s vertical, **≤ 2.5 m/s** | **fails** | 17 of 25 below 0.75 m/s, 3 of the 11 "real" stations among them |
| 20 | Lifting station wet-well live volume | Concept | G203-p48 §7.8, `V = 0.25 · Q · T`, `T = 3600 / starts`, starts ≥ 10 for motors up to 30 kW | **no** | no volume anywhere in W10 |
| 21 | Station duty / standby configuration | Concept | G203-p39 §7.3: minimum duty + standby, peak achievable with any one pump out | **no** | |
| 22 | Station minimum flow factor | Concept | G203-p40 Table 16 (0.25 at 50 L/s → 0.5 at 5,000 L/s) | **no** | needed to size the rising main against deposition |
| 23 | Station land requirement and flood level | Concept | G203-p38 §7.2: site approved by NWS **at concept/preliminary**; floor ≥ 300 mm above the 1:50 flood level | **no** | W10 says the stations "are at hydraulic positions, not land parcels" |
| 24 | Longitudinal profiles, **indicative** | Concept | scope-p12 | partial | only the main pipe (`W10_mainpipe_profile.shp`) |
| 25 | Longitudinal profiles at 1:1000 H / 1:100 V with the full annotation set | **Preliminary / Detailed** | scope-p23 item 40.6; scope-p26 item 4 | n/a | **do not attempt now** |
| 26 | `TIER` on every pipe | Concept | not a guideline requirement; scope-p12 names "trunk sewers, Main sewers, Laterals, riders" as distinct things on the layout | **no** | W8 had it; the hierarchy is what makes the layout buildable (`W8/docs/LEARNING_FROM_ASBUILT.md`) |
| 27 | Construction packages and implementation plan | Concept | scope-p5 item 7; scope-p16 item 39; G201-p21 Table 2 "Project Phasing" | **no** | Part C |
| 28 | Detailed Contracting Strategy Report | **Preliminary** | scope-p21 §4.1.2.8 | n/a | concept owes the packages, not the report |
| 29 | Quantity summary by asset category | Concept | G201-p21 Table 2, feasibility column | **no** | length by DN and depth band |
| 30 | Bill of Quantities | **Detailed** (priced 80 % at preliminary) | G201-p22 Table 2; scope-p22 item 28 | n/a | **do not attempt now** |
| 31 | Minimum three network options | Concept | scope-p13 | **no** | W10 is one option |
| 32 | Life-cycle cost, recommended option | Concept | scope-p13, scope-p16 item 37 | **no** | flagged in W10 as Phase 4.4 |
| 33 | SewerGEMS model, four horizons | Concept | scope-p14 | **no** | W8's `export_gems.py` has the schema |
| 34 | Velocity and d/D on every pipe | Concept | G203-p26–27, Table 10 | **no** | the pipes are sized but the result is not published |
| 35 | Minimum cover 1.3 m to crown, checked along the whole pipe | Concept | G203-p33 §4.6.3 | partial | depths exist at the ends only; the shallowest point on a rising ground is between them |
| 36 | Corridor width reserved by diameter | Concept (layout) | G203-pp32–33 Table 13 / G203-p35 Table 15 | **no** | 2.00 m to DN500, 2.80 m to DN900, 3.20 m to DN1200 |
| 37 | Wadi and flood exclusion for pipes and chambers | Concept | G203-p30 §4.4.1(i)(a), G203-p33; G201 Table 2 "Flood Protection Assessment" (all three phases) | partial | W8 carried `HAZ_CLASS` / `IN_WADI`; W10 does not publish them |
| 38 | Air vents on the gravity network | **Preliminary** | G203-pp31–32 §4.5 (≥ 150 mm, 6 m above ground) | n/a | do not attempt now |
| 39 | H₂S / septicity and WATS model | **Preliminary / Detailed** | scope-p17, scope-p24 | n/a | do not attempt now |
| 40 | Surge analysis | **Preliminary / Detailed** | scope-p17, scope-p25 | n/a | do not attempt now |

## B.2 Four defects in the W10 outputs themselves

[Certain] All four measured.

1. **The node layer and the pipe layer are from different solves.**
   `W10_nodes_depth.shp` is written by `p2_depths.py` at one assumed uniform gradient;
   `W10_pipes.shp` is written by `p2_sizing.py` after the pipes are sized and the depths
   re-solved on the real gradients. Snapping pipe ends to the node layer, the two
   disagree by **up to 10.39 m of depth**. There is currently **no node layer consistent
   with the published pipes**, so no invert can be quoted for any chamber.

2. **`SLOPE_PCT` is the minimum required gradient, not the laid gradient.**
   `p2_sizing.py` line ~206 writes `SLOPE_PCT = 100 × p["SMIN"]`. The median value is
   0.500 % because DN200 governs, which is Table 11's DN200 minimum (G203-p29). The laid
   gradient — the one that reconciles the two end depths with the ground — is not
   published, and cannot be reconstructed because the ground level is not on the pipe
   either.

3. **The lifting-station count is reported three ways.** `W10_SUMMARY.md` says 19 in the
   headline table and 21 in answer 3; `W10_stations_final.shp` and
   `W10_rising_mains.shp` hold 25; `W10_lift_consolidated.shp` holds 37;
   `W10_lift_opt.shp` 184; `W10_lift_stations.shp` 140; `W10_lift_sized.shp` 239. A
   deliverable can carry exactly one station count.

4. **Rising main velocities breach G203-p50 in both directions of the rule.** 17 of 25
   are below the 0.75 m/s self-cleansing minimum, three of them at stations flagged
   `REAL`. Separately, W8's audit check A9 states the limit as "between 0.75 and 3.0 m/s"
   citing G203-p50 §8.1 — **the source says 2.5 m/s** ("The maximum allowable velocity
   (worst case scenario) in the pipe shall be not greater than 2.5 m/s"). The 3.0 m/s
   figure is the *gravity* maximum from G203-p27. W11a must not inherit that.

## B.3 What the chamber unlocks

[Likely] Items 1 and 2 in B.1 are not one gap among forty. They are the gap, because
nine of the others are downstream of them:

- no chamber ⇒ no chamber schedule (scope-p25's column list is per-manhole)
- no chamber ⇒ no longitudinal profile (a profile is drawn between chambers)
- no chamber ID on pipes ⇒ no SewerGEMS import (`START_ND` / `STOP_ND` are mandatory)
- no chamber ⇒ no drop, no backdrop, no vortex shaft, no inlet angle
- no chamber ⇒ no quantity take-off (chambers are a pay item, and their count depends on
  Table 12 spacing, which W10 breaches on 65 % of its length)
- no chamber at a package boundary ⇒ nothing to hand over at, nothing to commission to

The arithmetic of that last point: splitting W10's reaches at the Table 12 maximum alone
adds **10,002 chambers**, taking the network from 11.1 to 16.4 per km. NAMA's built
network runs at **32.3 manholes per km** (3,268 nodes over 101.1 km) and W8's test area at
19.8. At W8's density the full area needs about **37,000 chambers**; at NAMA's built
density, about **61,000**. W10 currently has 20,937 objects that are not chambers.

---

# Part C — How a contractor actually builds this

## C.1 What a package IS, measured

Script: `W10/py/research/r1_packages.py`. Outputs:
`W10/run/research_packages_{summary,overlap,topology,outlets,interleave,proximity,components}.csv`.
Source layer: `W10/shp/W10_existing_built.shp` (3,266 gravity pipes, 101.1 km, installed
2006, `PROJECTCOD` = 5A-1 … 5A-5). Where these overlap the sibling note's
`research_hierarchy_packages.csv`, the numbers agree to the third decimal.

[Certain]

| Package | Pipes | Length km | Trunk / sub-main / lateral km | Zones | Hull km² | km per km² | Plots ≤ 50 m | Properties ≤ 50 m | Q<sub>adf</sub> m³/d | Levels |
|---|--:|--:|--|--:|--:|--:|--:|--:|--:|--:|
| 5A-1 | 1,123 | 32.25 | 0 / 0 / 32.25 | 312 | 2.36 | 12.0 | 1,917 | 3,589 | 2,762 | **0 %** |
| 5A-2 | 679 | 20.01 | 2.26 / 3.43 / 14.32 | 72 | 1.96 | 10.3 | 1,015 | 1,504 | 1,182 | 100 % |
| 5A-3 | 126 | 3.45 | 1.08 / 0 / 2.38 | 21 | 0.30 | 7.3 | 180 | 303 | 220 | 100 % |
| 5A-4 | 183 | 5.04 | 0.68 / 0.55 / 3.81 | 23 | 0.35 | 8.7 | 299 | 567 | 416 | 100 % |
| 5A-5 | 1,155 | 40.35 | 6.16 / 5.95 / 28.23 | 168 | 8.66 | 9.6 | 2,172 | 3,421 | 2,602 | 100 % |
| **Total** | **3,266** | **101.10** | 10.18 / 9.93 / 81.00 | 596 | — | — | 5,583 | 9,384 | 7,182 | 65.6 % |

**A package is 3.5–40 km of sewer serving 180–2,180 plots in 0.3–8.7 km²**, at a pipe
density of 7–14 km per km². Median 20 km. Every pipe is DN160 or DN200 — there is no
large diameter anywhere in the built network.

## C.2 Are the packages geographically clean? Yes.

[Certain] Convex-hull overlap suggests otherwise — 5A-1 and 5A-2 share 0.30 km², 12.8 % of
5A-1's hull. That is a hull artefact. The honest test is distance from each pipe to the
nearest pipe of a **different** package:

| Package | Median distance to the nearest foreign pipe | Pipes within 60 m of one | Share |
|---|--:|--:|--:|
| 5A-1 | 402 m | 138 | 12.3 % |
| 5A-2 | 347 m | 89 | 13.1 % |
| 5A-3 | 237 m | 12 | 9.5 % |
| 5A-4 | 367 m | 19 | 10.4 % |
| 5A-5 | **3,935 m** | 0 | **0 %** |

**Packages are territories, not interleaved slices.** Roughly one pipe in ten is near a
foreign package, and those are the seam pipes where two territories meet. 5A-5 is a
different settlement entirely, 3.9 km from the nearest other package, with its own 5.6 km
trunk main straight to the STP.

## C.3 Is a package a complete hydraulic unit? Yes — one outlet each.

[Certain] Reconstructed from NAMA's own manhole IDs (`US_MHID` → `DS_MHID`), which encode
package, zone and tier: `5A-2-SM.2-MH391`.

| Package | Nodes | Connected components | Outlets | Discharges to | Receives from |
|---|--:|--:|--:|---|---|
| 5A-1 | 1,124 | **1** | 1 (`5A-1-FL-SPS`) | its own pumping station | 5A-4 (physically — see below) |
| 5A-2 | 679 | **1** | 1 | **5A-4** | 5A-3 |
| 5A-3 | 127 | **1** | 1 | **5A-2** | — |
| 5A-4 | 184 | **1** | 1 (`5A-4-SM-MH917`, two pipes into it) | terminal in the dataset | 5A-2 |
| 5A-5 | 1,156 | **1** | 1 (`5A-1-FL-STP`) | **the STP direct** | — |

Every package is **one** connected drainage tree with **one** outlet. Not one of the five
is an arbitrary slice. [Likely] 5A-4's terminal node at (450565, 2567465) is 111 m from
5A-1's network and 672 m from 5A-2's, so 5A-4 discharges into 5A-1; the connecting pipe is
simply not in the dataset. That is an inference, not a record.

## C.4 The order of construction, read off the data

[Certain] Outlet coordinates and their distance to the STP at (444422.8, 2563337.9):

| Outlet | Package | Ends at | To STP |
|---|---|---|--:|
| `5A-5-TM-MH1759` → `5A-1-FL-STP` | 5A-5 | 444422, 2563344 | **6 m** |
| `5A-1-A-MH9` → `5A-1-FL-SPS` | 5A-1 | 449898, 2567299 | 6,758 m |
| `5A-4-SM.6-MH918` → `5A-4-SM-MH917` | 5A-4 | 450565, 2567465 | 7,400 m |
| `5A-2-TM-MH6032` → `5A-4-TM-MH6033` | 5A-2 | 450723, 2568118 | 7,909 m |
| `5A-3-TM-MH78` → `5A-2-TM-MH79` | 5A-3 | 450764, 2570230 | 9,365 m |

[Certain] Two independent chains:

```
  5A-3 ──► 5A-2 ──► 5A-4 ──► 5A-1 ──► SPS ──► 10.0 km force main ──► STP
  5A-5 ──────────── 5.6 km gravity trunk main ────────────────────► STP
```

**Can a package be commissioned before its downstream neighbour exists? Measured answer:
no — unless a pumping station stands in the way of that dependency.** 5A-3 is 3.5 km and
238 properties of sewer that is inert until 5A-2 exists. The construction order is forced:
downstream first, 5A-1 before 5A-4 before 5A-2 before 5A-3.

**The one exception is the important one.** 5A-1 terminates at a pumping station, not at a
gravity trunk. That station and its 10.0 km force main (`L021671`, the only built force
main) are what let the whole eastern cluster — 60.8 km, roughly 5,963 properties across
5A-1 to 5A-4 — be commissioned without first building 7 km of deep gravity trunk to the
STP. [Likely] **A lifting station is a commissioning device, not only a depth device.**
That is the most transferable lesson in the built network.

## C.5 What this means for W11a partitioning 1,883 km

[Certain] arithmetic, [Likely] conclusions.

1. **Size.** At NAMA's median package of 20 km, 1,883 km is **≈ 94 packages**; at its
   largest (40 km), **≈ 47**. Neither is a number of separate tenders — TD-p149 programmes
   the networks, lifting stations, pumping stations and house connections as **one**
   tender. So "package" here means a **buildable, separately-commissionable section within
   one contract**, and W11a should say so rather than implying 90 procurements.

2. **The unit is a subtree, not a polygon.** Every built package has exactly one outlet.
   A W11a package must therefore be **the set of everything draining through one chosen
   node**, cut at that node. Drawing a boundary on a map and taking whatever falls inside
   it will produce packages with several outlets, which is what NAMA did not do.

3. **The 206 W10 subnetworks are not packages.** Measured from `W10_joins.shp`: median
   1.16 km, but 10 of them exceed 80 km and the largest is 265.8 km with 6,327 plots,
   while 99 of 214 are under 1 km. That distribution is a hydraulic artefact of where the
   corridor network happens to touch the trunk. A package needs a size band; a subnetwork
   has none.

4. **Two levels are needed, not one.** NAMA's 101 km is one *phase* of a network whose
   ultimate is 1,883 km. W11a should carry **PHASE** (when it is built, driven by demand,
   the STP capacity and G201-p21's "Project Phasing") and **PACKAGE** (a buildable unit
   inside a phase, 15–40 km, one outlet). These are different fields and should not be
   collapsed.

5. **The lifting stations are the seams.** [Likely] The 19–25 stations W10 identified sit
   at exactly the points where a subtree can be cut off from gravity and served
   independently. Aligning package outlets with station locations gives each package a
   commissioning point that does not depend on the downstream trunk being finished. This
   is the 5A-1 pattern, applied deliberately.

6. **The territorial test is a deliverable criterion.** A W11a package should score like
   NAMA's: under about 15 % of its pipes within 60 m of another package's, and a median
   separation in the hundreds of metres. That is checkable by the same script that
   measured the built network.

7. **Temporary arrangements are not specified by anybody.** [Certain] The scope is silent
   (A.5). [Guessing] The realistic options for an upstream package awaiting its downstream
   neighbour are a temporary lifting station with tankering, an interim connection into
   the existing 2006 network where one is adjacent, or simply sequencing so it is never
   needed. **W11a should put this to NWS as a decision, not choose it.**

---

# Part D — The deliverable specification for W11a

Concept stage. Everything below is justified by Part A; anything a source puts at
preliminary or detailed is in D.7 as *do not attempt*.

**Canonical store: GeoPackage** (`W11a.gpkg`), one layer per table, with a shapefile copy
for exchange. Shapefile DBF field names are capped at 10 characters and every name below
respects that. CRS EPSG:32640 throughout.

## D.1 Layers and fields

### D.1.1 `W11a_manholes` (point) — the layer W10 does not have

| Field | Type | Meaning | Source of the requirement |
|---|---|---|---|
| `MH_ID` | text | unique chamber ID. Format mirrors NAMA's until NWS issues theirs: `<PKG>-<TIER>-MH<n>` | scope-p25 (numbering system pending) |
| `MH_TYPE` | text | `junction` / `bend` / `grade` / `diameter` / `spacing` / `lateral_end` / `head` / `lift` / `outfall` | G203-p29 §4.4 lists exactly these triggers |
| `GRD_LVL` | float | cover level, m, from the 0.5 m VRT | scope-p25 "levels … of upstream and downstream manholes" |
| `INV_LVL` | float | **outgoing** invert level, m | as above |
| `DEPTH` | float | `GRD_LVL − INV_LVL` | as above |
| `MH_DIA` | float | internal diameter, m (1.0 m default; ≥ 1.5 m where an internal backdrop is unavoidable) | G203-p30 |
| `N_IN` | int | incoming pipes | needed for the drop and inlet-angle checks |
| `DROP_MAX` | float | largest inlet-invert-to-outgoing-invert drop, m | G203-p30 |
| `BACKDROP` | int | 1 where `DROP_MAX` > 0.60 m; external by default | G203-p30 |
| `VORTEX` | int | 1 where `DROP_MAX` > 2.0 m | G203-p30 |
| `MIN_ANG` | float | smallest inlet angle to the direction of flow, degrees | G203-p30 (≥ 90°) |
| `TIER` | text | `lateral` / `sub_main` / `trunk_main` | scope-p12 names the tiers on the layout |
| `SUBNET` | int | hydraulic subnetwork | internal |
| `PKG` | text | construction package | scope-p16 item 39 |
| `PHASE` | int | construction phase | G201-p21 Table 2 |
| `IS_LIFT` | int | 1 if a lifting station sits here | scope-p12 |
| `LIFT_M` | float | static lift, m | |
| `ON_TRUNK` | int | 1 if on the main pipe | |
| `HAZ_CLASS` | int | flood hazard class from the 50-yr grid | G203-p30 §4.4.1(i)(a) |
| `IN_WADI` | int | 1 = in a wadi; must be zero everywhere | G203-p30, G203-p33 |
| `IN_PLOT` | int | 1 if the chamber lands inside a registered plot; must be zero | layout convention (W8 rule) |

### D.1.2 `W11a_pipes` (line)

| Field | Type | Meaning | Source |
|---|---|---|---|
| `PIPE_ID` | text | unique | |
| `US_MH`, `DS_MH` | text | chamber IDs — **the field whose absence is the gap** | scope-p25; SewerGEMS `START_ND`/`STOP_ND` |
| `DN_MM` | int | nominal diameter, 200 minimum | G203-p22 Table 6 |
| `MAT` | text | `PVC-U` ≤ DN250; `HDPE`/`GRP` DN300–315; `GRP` or lined RCC ≥ DN350; trunk mains > DN600 `GRP` / lined RCC / profile-wall HDPE | G203-p22 Table 6, G203-p35 Table 14 |
| `CONSTR` | text | `open_trench` / `trenchless` | G203-p21 §4.1, G203-p35 |
| `LEN_M` | float | | |
| `SLOPE_PCT` | float | **the laid gradient**, reconciling `INV_UP`, `INV_DN` and `LEN_M` | G203-p29 (uniform slope between manholes) |
| `SMIN_PCT` | float | the governing minimum — steeper of Table 11 and tractive force | G203-p27, G203-p29 Table 11 |
| `INV_UP`, `INV_DN` | float | invert levels, m | scope-p25 |
| `GRD_UP`, `GRD_DN` | float | cover levels, m | scope-p26 item 4 |
| `DEP_UP`, `DEP_DN` | float | depths, m | scope-p25 |
| `COV_MIN` | float | **minimum cover to crown anywhere along the reach**, not at the ends | G203-p33 (1.30 m) |
| `QADF_M3D` | float | accumulated average dry weather flow | T01 |
| `PF` | float | peaking factor | G201-p71–72 |
| `PF_METH` | text | `merrimack` / `peltier` / `held` | G201-p71–72; T02 §15 |
| `QPK_LS` | float | peak flow | |
| `VEL_MS` | float | velocity at peak | G203-p26 (≥ 0.75), G203-p27 (≤ 3.0) |
| `DOD` | float | d/D at peak | G203-p27 Table 10 (≤ 0.65 / ≤ 0.50) |
| `TIER` | text | | scope-p12 |
| `SUBNET`, `PKG`, `PHASE` | int/text | | |
| `ON_TRUNK`, `IS_XING`, `RISE_MAIN` | int | | rule 7; G203-p50 |
| `CORR_W` | float | reserved corridor width by diameter, m | G203-pp32–33 Table 13, G203-p35 Table 15 |

### D.1.3 `W11a_stations` (point)

| Field | Meaning | Source |
|---|---|---|
| `ST_ID`, `MH_ID` | station ID, and the chamber it sits on | |
| `ST_TYPE` | `Type 1` ≤ 100 L/s, `Type 2` 100–300, `Type 3` > 300 | G203-p40 |
| `Q_ADF`, `Q_PK_LS`, `Q_MIN_LS` | average, peak, and initial minimum flow (Table 16 factor) | G203-pp39–40 Table 16 |
| `N_DUTY`, `N_STBY` | pumps; minimum duty + standby, peak achievable with one out | G203-p39 §7.3 |
| `LIFT_M`, `TDH_M` | static lift and total dynamic head | |
| `WW_VOL` | wet-well **live volume**, m³, `0.25 · Q · T`, `T = 3600 / starts`, starts ≥ 10 for motors ≤ 30 kW | **G203-p48 §7.8** |
| `WW_STARTS` | assumed starts per hour, declared | G203-p48 |
| `PLOTS`, `PROPS` | catchment served | rule 9 (≥ 50 plots) |
| `GRD_LVL`, `FLOOD_LV` | ground and the 1:50 flood level; floor ≥ flood + 0.30 m | G203-p38 §7.2 |
| `LAND_M2` | indicative land take, with future expansion | scope-p20 §4.1.2.5 |
| `PKG`, `PHASE`, `COMM_PT` | package, phase, and whether this station is a commissioning point | Part C.4 |

### D.1.4 `W11a_rising_mains` (line)

`RM_ID`, `ST_ID`, `DN_MM`, `MAT`, `LEN_M`, `Q_DUTY`, `VEL_MS`, `VEL_MIN` (at design
minimum flow), `STATIC_M`, `FRIC_M`, `TDH_M`, `RETENT_M` (retention time, minutes),
`GRAD_UP`, `GRAD_DN`, `N_AIRV`, `N_WASH`, `N_ACCESS`, `PKG`.

Constraints to satisfy and record, all G203-pp50–51 §8.1–8.2: **0.75 m/s minimum at design
minimum flow** (1.0 m/s intermittent, 1.2 m/s vertical), **2.5 m/s maximum**, minimum
75 mm internal bore for non-clog pumps, access every 500 m, gradient 1:500 rising and
1:300 falling and never flatter than 1:750, air valves at high points and washouts at low
points, retention ideally under half an hour.

### D.1.5 `W11a_connections` (line) — indicative only

Required because scope-p12 puts "riders and property connections" on the concept layout.
Fields: `PLOT_ID`, `MH_ID` (receiving chamber), `PIPE_ID` (fronting sewer), `CONN_TYPE`
(`PCS` / `rider` / `lateral`), `LEN_M`, `N_PROP`, `Q_M3D`, `CAN_DRAIN` (does the plot
outlet sit above the sewer invert at the joining point), `PKG`.

Schematic. G203-p17 §3.2 gives the chain PCC → PC sewer → HCC → rider → lateral → main
sewer, with the HCC 2.5 m inside the right of way, up to three HCCs per rider, PCS ≤ 50 m
(G203-p18 Table 4 note) and laterals ≤ 45 m (G203-p22 Table 6). **The design sheets are
preliminary-stage (scope-p22) and must not be attempted.**

### D.1.6 `W11a_packages` (polygon)

`PKG_ID`, `NAME`, `PHASE`, `OUTLET_MH`, `DS_PKG` (the package it discharges into, or
`STP`), `COMM_SEQ` (commissioning order), `INDEP` (1 if it can be commissioned without its
downstream neighbour — i.e. it ends at a station, at the STP, or at existing works),
`KM`, `MH_N`, `PLOTS`, `PROPS`, `QADF_M3D`, `QPK_LS`, `AREA_KM2`, `KM_PER_KM2`,
`TRUNK_KM`, `SUBMAIN_KM`, `LAT_KM`, `LIFT_N`, `RM_KM`, `SEAM_PCT` (share of its pipes
within 60 m of another package — the territorial test from C.2).

Sizing target, from C.1: **15–40 km, 500–2,500 plots, one outlet.**

## D.2 Schedules

CSV **and** XLSX, one file each, in `W11a/run/`:

| Schedule | Keyed on | Columns | Required by |
|---|---|---|---|
| Chamber schedule | `MH_ID` | ID, easting, northing, type, cover level, invert level, depth, diameter, inlets, max drop, backdrop, vortex, tier, package, phase | scope-p25 (the detailed-stage column list, produced here at concept precision) |
| Pipe / hydraulic calculation schedule | `PIPE_ID` | US and DS manhole, their levels and depths, length, DN, material, laid slope, governing minimum slope, PF and method, Q<sub>adf</sub>, Q<sub>peak</sub>, velocity, d/D | scope-p25 verbatim column list; scope-p16 item 36 |
| Lifting station schedule | `ST_ID` | as D.1.3 | scope-p15 item 19 |
| Rising main schedule | `RM_ID` | as D.1.4 | scope-p13 |
| House / property connection list | `PLOT_ID` | plot, package, receiving chamber, connection type, properties, flow, can-drain flag | **scope-p12** ("List of Customer / house connection Excel list") |
| Package schedule | `PKG_ID` | as D.1.6 plus commissioning order and dependency | scope-p16 item 39 |
| Quantity summary by asset category | DN × depth band × package | length, chamber count by depth band, station count, rising main length | **G201-p21 Table 2**, feasibility column |
| Compliance / audit table | check ID | check, guideline reference, criterion, result, count of failures | T02 §16; no-exemption rule |
| Data request register | item | what is missing, who holds it, what it blocks | scope-p15 item 6; `_BRAIN/05_GAPS.md` |

## D.3 Drawings

[Certain] Concept-stage drawing scope is G201-p22 Table 2 feasibility row — *"Drawings —
site location, routing, boundaries"* — plus scope-p12's layout content sentence and
scope-p27's presentation rules.

| Drawing | Content | Source |
|---|---|---|
| Key plan, A0, whole boundary | proposed network on satellite imagery, tiers distinguished, **flow direction arrows**, lifting/pumping stations, STP, package boundaries | scope-p26 item 2, scope-p27; scope-p12 |
| Network layout, one per package | trunk, main, laterals, riders and property connections **on a property-map background, with manholes at all junctions** | **scope-p12** |
| Indicative longitudinal profiles | the trunk main and every sub-main: ground line, invert line, chamber positions, DN, gradient, depth | **scope-p12** ("indicative longitudinal profiles … as part of the detailed concept design") |
| Package and phasing plan | packages, commissioning order, dependency arrows, station-served islands | scope-p16 item 39; G201-p21 |
| Options comparison plan | the three network options side by side | scope-p13 |

Presentation: A3 inside the report, A0 for the coloured sets, superimposed on satellite
imagery (scope-p27). **Not now:** 1:2500 plan sets and 1:1000/1:100 profile sets
(scope-p23 item 40), standard details, sections, house connection sheets.

## D.4 The SewerGEMS package

Reuse `W8/py/sewnet/export_gems.py` unchanged — it was written to the Bentley
ModelBuilder schema and carries the import procedure.

| File | Fields |
|---|---|
| `MANHOLES.shp` | `LABEL`, `GRD_EL`, `INV_EL`, `MH_DIA` |
| `CONDUITS.shp` | `LABEL`, `START_ND`, `STOP_ND`, `DIA_MM`, `MATERIAL`, `MANNING_N`, `INV_UP`, `INV_DN`, `LEN_M` |
| `OUTFALL.shp` | `LABEL`, `GRD_EL`, `INV_EL` |
| `LOADS.xlsx` / `.csv` | `MH_LABEL`, `LOADTYPE`, `BASEFLOW` (L/s), `PATTERN` |
| `REFEREE_pipes.csv` | our Q, v, d/D per conduit against empty SewerGEMS columns |

Scope of the model, and the citation for keeping it that size: **trunk mains and
sub-mains as conduits, laterals as loads at the junction chamber** (G203-p25: modelling
"will usually be done for the Primary networks; the secondary … can be partially or totally
involved"). Four horizons — start, 2030, 2055, ultimate (scope-p14). Elevations, never
depths; single-part polylines digitised upstream to downstream; endpoints vertex-snapped;
the model must open and run every scenario without error before submission (G201-p140).

## D.5 Documents

1. **Concept design report** section set — the 40 items of scope-pp15–16, built with the
   `report-writing` skill, revision-foldered.
2. **Three network options** with the seven-criterion appraisal, LCC at 5 % over 25 years,
   and a recommendation (scope-p13; PROJECT-STATE §2 item 1e).
3. **Contract strategy, packages and implementation plan** (scope-p5 item 7, scope-p16
   item 39) — the Part C output. *Not* the Detailed Contracting Strategy Report, which is
   preliminary (scope-p21).
4. **Design criteria register** — every value with its page, every assumption tagged as
   one (T02 §14–15; the no-invented-metrics rule).
5. **Audit report** — every check, every element, no exemptions (T02 §16).
6. **Data request register** — D.8.

## D.6 Acceptance tests W11a must pass

Extend `W8/py/sewnet/stages/audit.py`. Existing checks A1–A9, B1–B2, C1–C8, D1, E1–E2
carry over with two corrections and eight additions.

**Corrections**

| Check | Change |
|---|---|
| A9 rising mains | upper limit **2.5 m/s**, not 3.0 (G203-p50 §8.1). Lower limit 0.75 m/s at *design minimum* flow, 1.0 m/s intermittent, 1.2 m/s vertical |
| C1 spacing | must run on the **as-built reach set after chamber placement**, not on corridor segments — this is the check W10 would have failed on 4,763 reaches |

**Additions**

| ID | Check | Criterion | Reference |
|---|---|---|---|
| F1 | Referential integrity | every `US_MH` and `DS_MH` exists in `W11a_manholes`; every manhole is referenced by at least one pipe | enabling defect B.1 item 2 |
| F2 | Level consistency | `GRD_LVL − INV_LVL = DEPTH` on every chamber, to 1 mm | scope-p25 |
| F3 | Gradient consistency | `(INV_UP − INV_DN) / LEN_M` reproduces `SLOPE_PCT` to 0.001 %/m | G203-p29 (uniform slope) |
| F4 | Chamber triggers | a chamber exists at every junction, change of gradient, change of diameter, change of direction beyond the declared threshold, and end of lateral | G203-p29 §4.4 |
| F5 | Cover along the reach | `COV_MIN` ≥ 1.30 m measured at every profile step, not only at the ends | G203-p33 |
| F6 | Package outlet | every package has exactly one outlet chamber | Part C.3 |
| F7 | Commissioning order | the package dependency graph is acyclic and `COMM_SEQ` respects it | Part C.4 |
| F8 | Territorial packaging | `SEAM_PCT` ≤ 15 % for every package | Part C.2 |

Two rules from T02 §16 apply to all of them: **check every element, not a sample**, and
**never let a check carry an exemption** — a skipped row reads as a pass.

## D.7 Explicitly out of scope at concept — do not attempt

| Item | Stage it belongs to | Citation |
|---|---|---|
| House connection **design sheets** | Preliminary | scope-p22 items 4 and 6; scope-p23 item 40.7 |
| Profiles at 1:1000 H / 1:100 V with the full annotation set | Preliminary / Detailed | scope-p23 item 40.6; scope-p26 item 4 |
| Plan sets at 1:2500 | Preliminary | scope-p23 item 40.5 |
| Bedding and cover classes | Detailed — **and unspecifiable** | not in G203; PAM-SPC-4xx / PAM-STD-4xx not held (G201-p136) |
| Structural, mechanical, electrical, ICA design; P&ID; SLD | Preliminary onward | G201-pp20–21 Table 2; scope-p22 items 9, 34, 35 |
| HAZOP | Preliminary | G201-p21 Table 2; scope-p22 item 24 |
| Surge analysis | Preliminary / Detailed | scope-p17; scope-p25 |
| H₂S / septicity model, WATS | Preliminary / Detailed | scope-p17; scope-p24 |
| Air vent design on the gravity network | Preliminary | G203-pp31–32 §4.5 |
| Bill of Quantities (measured or priced) | Preliminary 80 % / Detailed 90 % | G201-p22 Table 2; scope-p22 item 28, scope-p26 item 6 |
| Geotechnical interpretation, trial pits, utility clash resolution | Preliminary / Detailed | scope-pp16, 18, 24 |
| Final material selection | Detailed | scope-p25 "Final recommendations on pipe materials and diameters" |
| Manhole numbering in NWS format | Detailed — **and blocked** | scope-p25 (system to be issued to the successful consultant) |
| Architectural and landscaping drawings | Preliminary | scope-p18 §4.1.2.3 |
| ETAP power system analysis | Preliminary onward | scope-p8 item 20 |
| Construction phasing / construction planning | Preliminary / Detailed | G201-p21 Table 2 — concept owes **Project** Phasing only |

## D.8 What NWS must supply before parts of this can close

| Item | Blocks | Source of the obligation |
|---|---|---|
| NWS manhole numbering system | final `MH_ID` format; every schedule and drawing annotation | scope-p25 |
| NWS Geo-Database Specifications | the layer schema itself, and the GIS upload | scope-p18; scope-p4 item 3 |
| PAM-SPC-4xx (civil works) and PAM-STD-4xx (civil drawings) | bedding, cover classes, chamber types, standard details | G201-p136 |
| Topographic survey, geotechnical investigation, 50 trial pits | depths, constructability, and the utility clashes behind rule 7 | scope-p7 items 11–13; scope-p12 |
| NWS's preferred contracting split | whether packages are contract sections or separate tenders | scope-p6 item D.1; TD-p149 |
| Confirmation of the maximum-depth working figure | whether 12.00 m is cover or invert, and whether it is a limit at all | G203-p33 says "approximately 10 – 12 m", recommended, cost-triggered |
| A design value for tractive tension τ | the minimum gradient at the head of every branch | G203-p27 gives the method, not the value |

---

## Appendix — the measurement scripts

| File | What it produces |
|---|---|
| `W10/py/research/r1_packages.py` | `W10/run/research_packages_summary.csv`, `_overlap.csv`, `_topology.csv`, `_outlets.csv`, `_interleave.csv`, `_proximity.csv`, `_components.csv` |

Re-run with `python W10/py/research/r1_packages.py` from the repo root. It reads
`W10/shp/W10_existing_built.shp` and `W10/shp/W10_plot_loads.shp` only, and writes nothing
outside `W10/run/`.
