# STP site options — W11a

**Ibri Sewer, TE & STP (2621) · Renardet / Nama Water Services · 2026-09-02**

**Four proposed STP sites have been sitting in the project data since 9 August and not one
of them has ever been assessed.** `Hydraulic/SHP/Proposed STP/Proposed STP.shp` arrived in a
zip dated 2026-08-09 carrying three proposed locations; `Hydraulic/SHP/IBRI STP/IBRI STP.shp`
arrived the same day with the existing works alone and was edited on 2026-09-01 to hold five
points — the works plus four proposals. **No script in this repository has ever read
`Proposed STP.shp`**, `_BRAIN/03_DATA_INVENTORY.md` still records `IBRI STP` as "1 point",
and W10's siting study (`W10/docs/STP_SITING.md`) invented ten candidates of its own on a
weighted surface and scored only two real sites — the existing works and the southern one.
The brief for this task describes the southern point as *the* proposed site. It is one of
four.

**Two of the four are not central-works candidates and the measurements say so plainly.**
The eastern site sits **125 m** from a built plot, below the **300 m** floor of the
large-STP buffer band in PAM-GUD-201 p43 Table 8, and takes 68.9 % of the load by gravity.
The north-eastern site takes **15.2 %** — and the two client layers disagree by **1.9 km**
about where it is, with the August reading having 1.8 ha of free land and failing the same
300 m floor at 250 m. Only the southern and north-western proposals are candidates for a
single central works, and both are.

**Only one of the seven points assessed clears the buffer requirement — the southern one.**
PAM-GUD-201 p43 Table 8 gives a large STP a band of **300 m to 1,000 m**, resolved *"based on
odour modelling (5 Odour Units OU contour)"*. No odour model exists, so the band cannot be
closed. Measured to the nearer of a built plot and a planned residential plot: B clears at
2,627 m; A (712 m), C (850 m), E (375 m) and the W10 reference cell (708 m) sit inside the
band; D (125 m) and E2 (250 m) are below its floor.

**And the land answer has changed underneath us.** W10 sized the site against 49,700 m³/d,
which was retired in favour of 74,700. On the current published load the central-STP design
flow is **81,258 m³/d**, the plant land from PAM-GUD-203 p64 Table 28 is **14.6–29.3 ha** for
conventional activated sludge, and the TOR's five-day emergency lagoon (scope p13) adds a
further **8.1–13.5 ha** that Table 28 does not cover. Against that the existing works has
**37.1 ha** of unplatted land inside an 825 m square, and 117 registered plots covering
66.6 ha inside the same square.

**Nothing here decides the phasing, and nothing here can.** There is no flow-versus-year
curve in this project; PAM-GUD-201 p59 makes development percentages a mandatory input to
phasing and they have not been supplied. Section 9 sets out exactly what the appraisal needs.

---

## 1. What was measured, and from what

| Output | Path |
|---|---|
| Module (re-runnable, ~4 min; `--cache` redraws the figures in seconds) | `W11a/report/stp_options.py` |
| Site-options map | `W11a/report/img/F20_stp_site_options.png` |
| Gravity-reach figure | `W11a/report/img/F21_stp_gravity_reach.png` |
| Measurement table (CSV, scratchpad — not in the repo) | `%TEMP%\w11a_figkit\stp_options_measurements.csv` |

Every number in this document came out of one of these artefacts:

| Artefact | What it gave |
|---|---|
| `Hydraulic/SHP/IBRI STP/IBRI STP.shp` (5 pts, edited 2026-09-01) | the existing works and four proposed sites |
| `Hydraulic/SHP/Proposed STP/Proposed STP.shp` (3 pts, 2026-08-09) | the original three proposals, one of which has since moved 1.9 km |
| `W11a/shp/W11a.gpkg [servicing]`, 187 rows | the published ultimate load, 74,701 m³/d total, 73,871 m³/d to a central works |
| `W11a/shp/W11a_trunk.gpkg [reaches, nodes]`, 754 + 758 rows | 85.55 km of trunk, laid levels, the outfall invert, the three lifting stations |
| `Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt`, 0.5 m | every ground level quoted |
| `Data/04 Lekhuwair/Hazard_T50y.tif`, 3 m, nodata −9999.0 | flood hazard, and the untested share |
| `W3/shp/MoH_Plots_class_v4.shp`, 61,272 plots | odour receptors, planned residential plots, agriculture, and what land is already platted |
| `W7/shp/EXISTING_STP_PT.shp` | the 1,800 m³/d existing works record and the 29,038 m³/d SUREKHA concept record |
| `W7/shp/EXISTING_TE_LINE.shp`, 49.35 km, every segment `OP_STATUE = 0` | the proposed TE network — **none of it is built** |

**Both rasters have nodata −9999.0, which is finite.** `np.isfinite` alone passes it as a
real value. Guarded in one place in the module, as `figkit` requires.

---

## 2. The guideline values, read from the source

| Value | Source | Page |
|---|---|---|
| **Buffer, STP (large): 300 m – 1,000 m**, note: *"Based on odour modelling (5 Odour Units OU contour)"* | PAM-GUD-201 §6.1.3.3, **Table 8 Minimum buffer zone requirements** | **G201-p43** |
| Buffer, STP (small/medium): 500 m to residential / sensitive uses, *"Generic default based on Water Corporation practice"* | PAM-GUD-201, Table 8 | G201-p43 |
| Buffer, sewage pumping station: 30 m residential / 20 m industrial | PAM-GUD-201, Table 8 | G201-p44 |
| Table 8 is *"subject to NWS approval and the results of the Environmental and Social Impact Assessments"* | PAM-GUD-201 §6.1.3.3 | G201-p43 |
| **STP size classes: large ≥ 20,000 m³/d** (small < 500; medium 500–20,000) | PAM-GUD-203 §10.2.1 | **G203-p65** |
| **Site selection criteria**, fifteen headings (a)–(o), including (c) land availability / phasing, (f) topography to limit pumping, (i) 25- and 100-year flood levels and *"STPs shall be fully operational during floods"*, (j) minimum nuisance / noise / odours / emergency outfall, (k) proximity to residential areas, (m) **buffer area requirement from residential zones** | PAM-GUD-203 §10.1, **Table 27** | **G203-p63** |
| **Land area requirement, m² per m³/d**: MBR 0.45–0.9 · MBBR 0.9–1.8 · SBR 0.9–1.8 · IFAS 1.2–2.5 · CAS/extended aeration 1.8–3.6 · reed bed > 10 | PAM-GUD-203, **Table 28** | **G203-p64** |
| Design flow: average sewage flow plus infiltration plus *"a 10% increment for STP design as operational safety flow allowance"* | PAM-GUD-203, Table 29 | G203-p65 |
| STPs *"shall be designed for a design horizon of at least 15 years"* | PAM-GUD-203 §10.2.1 | G203-p65 |
| Minimum sewer gradient, DN900 and above: **0.75 mm/m** | PAM-GUD-203 §4.3.1, **Table 11** | G203-p29 |
| Maximum velocity 3.0 m/s at design depth of flow | PAM-GUD-203 §4.2.2.2 | G203-p27 |
| Minimum cover 1.30 m to the crown | PAM-GUD-203 §4.6.3 | G203-p33 |
| **Site selection, routing and layout · flood protection assessment · optioneering and whole-life costing · project phasing** are all **concept-stage minimum contents** | PAM-GUD-201 **Table 2** | **G201-p19, p21** |
| *"development speed must be considered through appropriate phasing assumptions … development percentages must be applied over the design period to reflect realistic build-out scenarios and particularly avoiding overestimation"* | PAM-GUD-201 §7.2 note | **G201-p59** |
| EIA must be initiated at feasibility, *"the full EIA must be done in the concept / preliminary design stages"* | PAM-GUD-201 §6.1.4.3 | G201-p44 |
| Geophysical and geotechnical investigation for STPs | PAM-GUD-201 §6.1.2.1–2 | G201-p40 |

### 2.1 Where the guideline gives no number, and it matters

**The buffer for a plant this size is not a number, it is an output of a model nobody has
run.** G203-p63 Table 27 (m) names *"buffer area requirement from residential zones"* as a
site-selection criterion and gives no value at all. G201-p43 Table 8 gives one — and for a
**large** STP it is a **band, 300 m to 1,000 m, explicitly resolved by odour modelling to the
5 OU contour**. At 81,258 m³/d this plant is large by G203-p65 with no argument possible, so
the band governs, and **the band cannot be closed without an odour dispersion model.** Six of
the seven sites assessed here are inside it or below it.

Measured against the **governing horizon buffer** — the nearer of a built plot and a planned
residential plot, because a planned plot is a receptor the site acquires rather than one it
swaps for — the seven candidates fall out as **one clear, four inside the band, two below its
floor**:

| | clears ≥ 1,000 m | inside 300–1,000 m | **below the 300 m floor** |
|---|---|---|---|
| | **B** 2,627 m | A 712 · C 850 · E 375 · W10-S1 708 | **D 125 · E2 250** |

Three consequences follow, and all three are decisions for NWS rather than findings of ours:

1. **Only the 300 m floor is testable today.** Two sites fail it outright — D at 125 m and
   E2 at 250 m.
2. **Everything between 300 m and 1,000 m is provisional**, including the existing works at
   712 m.
3. **The buffer is directional, not circular.** G203-p63 Table 27 (e) requires *"direction of
   prevailing winds"* to be considered. There is no wind rose in the project, so every
   distance in this document is an omnidirectional radius, which is the conservative form
   only if the receptor happens to lie downwind.

**No wadi or flood setback for an STP *site* exists in either guideline.** G203-p63 Table 27
(i) requires compliance with 25- and 100-year flood levels and full operation during floods,
but gives no metric distance. The only wadi distance in either book is 15 m either side of a
**pipe** crossing (G201-p86), which is a pipeline rule and does not transfer to a site. No
setback of our own is applied here; the measured distance to hazard class ≥ 4 is reported
raw so the appraisal can set its own.

---

## 3. The land requirement, corrected

W10 sized the site against **49,700 m³/d**. That figure is retired (`CLAUDE.md`: the ultimate
saturated Qadf is ≈74,700 m³/d, measured over 64,027 records at OR 5.32 and 1.456 properties
per plot). The published `servicing` layer measures **74,701 m³/d** across all systems, of
which **73,871 m³/d** is allocated to a central STP (139 of 187 sets; 716 m³/d to satellite
package plants and 114 m³/d to on-site systems).

Design flow = 73,871 × 1.10 (G203-p65 Table 29) = **81,258 m³/d**.

Applying **G203-p64 Table 28**:

| Technology | m²/(m³/d) | Plant land at 81,258 m³/d |
|---|---|---|
| MBR | 0.45 – 0.90 | **3.7 – 7.3 ha** |
| MBBR | 0.90 – 1.80 | 7.3 – 14.6 ha |
| SBR | 0.90 – 1.80 | 7.3 – 14.6 ha |
| IFAS / hybrid fixed biofilm | 1.20 – 2.50 | 9.8 – 20.3 ha |
| **CAS / extended aeration** | **1.80 – 3.60** | **14.6 – 29.3 ha** |
| Constructed wetland (reed bed) | > 10 | > 81.3 ha — out of scope at this flow |

**Plus the emergency lagoon, which Table 28 does not include.** TOR scope p13: *"Preparation
of designs of Emergency Lagoons (for 5 days storage) from STP / Pumping stations in case of
STP failure and out of operations."* Five days at the design flow is **406,290 m³**.

| Lagoon depth (**PROJECT ASSUMPTION** — no guideline value) | Area, ultimate | Area at a 20,000 m³/d phase 1 |
|---|---|---|
| 3 m | 13.5 ha | 3.3 ha |
| 4 m | 10.2 ha | 2.5 ha |
| 5 m | 8.1 ha | 2.0 ha |

**Working land envelope for the ultimate central works: about 12 ha (MBR + a 5 m-deep
lagoon) to about 43 ha (CAS/EA + a 3 m-deep lagoon).** Both ends are legal readings of
Table 28; the process is not chosen, so a site that only fits the low end pre-commits the
process choice. That is a **project judgement**, not a guideline rule, and it is the single
most consequential judgement in this document.

Two things sit outside the envelope and would add to it. Table 28's own preamble (G203-p64)
says the total land must be sufficient for *"regulatory compliance (e.g., buffer zones from
residential areas), and flexibility for future expansion or technological upgrades"*, and
separately asks the designer to *"assess the land requirements for implementing
energy-efficient solutions such as solar farms, ideally integrated within the STP
perimeter"*. **Whether the m²/(m³/d) benchmark already contains the expansion and buffer
allowance is not stated anywhere in the guideline.** Read conservatively it does not, and the
solar farm certainly does not — it is asked for as a separate assessment.

W10's stated 20 ha floor / 30 ha target is therefore superseded. At the corrected flow the
comparable pair is roughly **30 ha floor / 44 ha target**.

---

## 4. The measurements

Seven points: the existing works, the four proposals in the client layer, the 2026-08-09
reading of the north-eastern proposal (which has since moved 1.9 km), and W10's top-ranked
cell carried for comparison. Coordinates EPSG:32640, ground levels from the 0.5 m VRT.

| | **A** existing works | **B** proposed south | **C** proposed north-west | **D** proposed east | **E** proposed north-east | **E2** NE, Aug-09 reading | W10-S1 (reference) |
|---|---|---|---|---|---|---|---|
| Easting | 444 423.0 | 442 448.3 | 440 797.0 | 452 431.9 | 457 546.9 | 458 738.6 | 443 075 |
| Northing | 2 563 343 | 2 558 942 | 2 567 533 | 2 567 077 | 2 576 181 | 2 577 651 | 2 566 675 |
| Ground level, m aOD | 328.72 | **311.74** | 321.59 | 360.37 | 409.70 | 418.92 | 327.31 |
| **To nearest built plot, m** (today's receptor) | 712 | **2 627** | 850 | **125** ✗ | 375 | 250 | 1 045 |
| To nearest **planned** residential plot, m (a *new* receptor at the horizon, not a replacement) | 732 | **3 818** | 1 261 | 125 | 419 | 257 | **708** |
| **Governing buffer at the saturation horizon, m** = the smaller of the two | 712 | **2 627** | 850 | 125 | 375 | 250 | 708 |
| Against G201-p43 Table 8 (300–1,000 m) | inside band | **clears** | inside band | **fails floor** | inside band | **fails floor** | inside band |
| Free unplatted land, 625 m square, ha (max 39.1) | 17.8 | 38.4 | 36.8 | 11.2 | 30.3 | **0.0** | 37.0 |
| Free unplatted land, 825 m square, ha (max 68.1) | 37.1 | **66.2** | 64.9 | 23.8 | 49.4 | **1.8** | 64.7 |
| Sits on a registered plot? | **yes, its own 6.56 ha compound** | no | no | yes, 0.76 ha agri | no | yes, 27.3 ha agri | no |
| Registered plots within 800 m | 117 / 66.6 ha | **0 / 0 ha** | **0 / 0 ha** | 386 / 56.6 ha | 357 / 83.2 ha | 556 / 163.2 ha | 15 / 10.5 ha |
| To hazard class ≥ 4, m | 1 800 | 917 | **3 220** | 152 | 451 | 1 137 | 2 381 |
| Hazard class at the point | no answer | no answer | no answer | no answer | no answer | 1 | 2 |
| **Ground within 1 km with no hazard answer, %** | **46.7** | 28.1 | 20.1 | 35.7 | 17.8 | 11.2 | 11.5 |
| **Load arriving by gravity, %** | 99.5 | **100.0** | **100.0** | 68.9 | 15.2 | 13.9 | 99.8 |
| …as m³/d | 73 140 | 73 500 | 73 496 | 50 650 | 11 182 | 10 237 | 73 358 |
| Load-weighted conveyance, km | 16.21 | **21.77** | 18.00 | **10.17** | 12.58 | 14.14 | 15.63 |
| To the load centroid, km | 11.79 | 16.20 | 13.32 | **3.69** | 6.80 | 8.69 | 11.37 |
| Cover at the site if the built trunk is carried on at 0.75 mm/m, m | 7.08 | **−5.21** (surplus fall) | 5.34 | 47.32 ✗ | 105.91 ✗ | 116.96 ✗ | 9.16 |
| To the trunk as drawn, m | 0 | 4 092 | 1 995 | 371 | 1 137 | 455 | 1 504 |
| To the nearest agricultural plot, m | 643 | 1 075 | 862 | 0 | 90 | 0 | 495 |
| Agriculture in a 10 km square, ha | 1 110 | **253** | 504 | **2 322** | 1 980 | 1 702 | 1 046 |
| To the (proposed) TE network, m | 134 | 284 | **5 607** | 376 | 1 516 | 2 996 | 3 694 |
| To the nearest road, m | 0 | 325 | 112 | 283 | 447 | 251 | 135 |
| To the nearest dual carriageway, m | 4 414 | **9 062** | 2 007 | 382 | 1 152 | 492 | 1 532 |
| From the existing works, km | 0 | 4.82 | 5.54 | 8.84 | 18.36 | 20.24 | 3.59 |

Figures: **F20** (`W11a/report/img/F20_stp_site_options.png`) plots the sites, both buffer
rings, the receptors, the agriculture, the trunk and the load centroid, with the untested
hazard ground hatched. **F21** (`F21_stp_gravity_reach.png`) is the gravity answer — the share
of the load arriving at each site, and the load-weighted distribution of spare head behind it.

### 4.1 The gravity test, stated exactly

A load centre reaches a works when

```
(z_k − 2.0) − 0.00075 × 1.296 × d(k, site)  ≥  z_site − 6.0
```

- **0.00075** is G203-p29 Table 11 for DN900 and above. Guideline value.
- **1.296** is the **measured** sinuosity of the W11a trunk — path length along the trunk
  divided by straight-line distance to the outfall, taken over 753 nodes (median 1.296,
  p75 1.346, p90 1.425). W10 used 1.30 and its own documentation flagged that as
  uncalibrated; this closes that item, and the assumed value turns out to have been right.
- **2.0 m** collector invert below ground where the load enters, and **6.0 m** deepest
  acceptable works inlet: both **PROJECT ASSUMPTIONS**. Only their difference (4.0 m) enters,
  so they shift every site equally. At a 9.0 m inlet — which is what the trunk actually
  delivers at the existing works, 8.78 m — nothing in the ranking moves (A 99.9 %, D 70.8 %,
  E 16.5 %).
- Load: the published ultimate Q of the 139 central-STP servicing sets, spread over the
  built and planned plots inside each set and aggregated to 1,043 cells of 500 m carrying
  73,510 m³/d. Nothing is re-derived; the total is the published one.

**This is a head screen, not a design.** It does not test the 12 m cover cap along the route.
The proof that this matters is site A itself: it takes 99.5 % of the load on this test, and
the actual W11a trunk still needs **three lifting stations** to get there — at
E445 113/N2 567 695 (5,554 m³/d, 12.62 m deep), E447 698/N2 567 164 (9,298 m³/d, 12.79 m) and
E464 359/N2 566 792 (963 m³/d, 11.44 m). **A site can pass this screen and still need
pumping.** Read it as an elimination test, never as a clearance.

---

## 5. The seven sites, read one at a time

### A — the existing works, E444 423 N2 563 343, GL 328.72 m

The NAMA asset record puts a **1,800 m³/d ASEA plant** here (`EXISTING_STP_PT.shp`,
`STP_ID 102`, `PROJECTCOD 5A-1`, at E444 375.6 N2 563 334.5 — 48.2 m from our point).
**NWS's own asset-planning record for a 29,038 m³/d plant sits 134.5 m away** at
E444 376.0 N2 563 217.3 (47 m west, 126 m south), `STATUS = Design`,
`SOURCE = ASSET PLANNING`, and its own `HYPERLINK` field reads *"RG Master Plan (Concept
Design) not approved yet. Kindly consult Asset Planning for any NOC's"*. That record is not a
commitment, but it is evidence that NWS has already contemplated expansion on this ground —
at 36 % of this scheme's design flow.

**What is right about it:** it is the point the trunk was drawn to, so conveyance costs
nothing extra; 99.5 % gravity; 134 m from the proposed TE network, the closest of all seven;
1,110 ha of agriculture within a 10 km square; on a road.

**Three things are wrong with it, and they compound.**

1. **Land.** 37.1 ha of unplatted land inside an 825 m square, against a plant-plus-lagoon
   envelope of ~12–43 ha. It fits the low end of the envelope and not the high end, and
   there is no room for the phasing, expansion and solar allowance G203-p64 asks for without
   acquiring some of the **117 registered plots covering 66.6 ha** that surround it — one of
   which is a **12.9 ha planned plot 283 m away**. The site's own compound is 6.56 ha, with a
   further 29.0 ha built parcel 95 m off.
2. **Buffer.** 712 m to the nearest built plot and 732 m to the nearest planned residential
   plot. That clears the 500 m small/medium generic default and the 300 m floor, and sits
   inside the 300–1,000 m large-STP band. For a plant **more than forty times** the capacity
   of the one there now (81,258 ÷ 1,800 = 45), 712 m is not a margin anybody should accept
   without the odour model that G201-p43 says sets the number.
3. **Flood evidence.** **46.7 % of the ground within 1 km of this site has no answer in the
   only hazard grid we hold** — the worst of all seven candidates. G203-p63 Table 27 (i)
   requires 25- and 100-year flood levels and full operation during floods, and we have
   neither return period, over a site half of whose surroundings are untested.

**And it sits on a local rise.** Ground at the works is 328.72 m; the lowest ground within
3 km upstream along the trunk's main stem is 325.39 m. Over the final kilometre the ground
climbs 3.22 m while the pipe falls 0.96 m, so the trunk's depth to invert grows from 4.60 m at
chainage 959 m to **8.78 m at the works** (6.98 m of cover on a DN1700). **The last kilometre
of trunk costs 4.18 m of depth purely because the works sits uphill of its own approach.**

### B — proposed south, E442 448 N2 558 942, GL 311.74 m

*(The brief quotes E442 451.3 N2 558 941.8. The layer holds E442 448.3 N2 558 942.0 — 3.0 m
away. Immaterial, but the layer is the artefact and it is what was measured.)*

**The only candidate whose buffer clears the top of the band, today and at saturation.**
2,627 m to the nearest built plot and **3,818 m to the nearest planned residential plot** —
2.6× and 3.8× the 1,000 m upper bound. No registered plot within 800 m in any direction, so
the whole 66.2 ha inside an 825 m square is unplatted desert and the acquisition is one
allocation rather than an assembly.

**Gravity is not merely satisfied, it is over-satisfied.** 100 % of the central load reaches
it. Continuing the existing trunk 6.25 km from its outfall at the Table 11 minimum would put
the invert **6.51 m above the shallowest legal position** — the pipe would daylight, so it is
laid steeper instead. A uniform grade from the trunk's arriving invert of 319.94 m to a
1.30 m-cover invert at B is **0.179 %**, against a 0.075 % minimum: at DN1700 and the peak
1,350 L/s that is **d/D 0.399 and v = 1.60 m/s** — inside the Table 10 limit of 0.50 for pipes
over 350 mm, and well under the 3.0 m/s ceiling (both G203-p27). *(Hydraulics computed with
`W8/py/sewnet/hydra.py`, which reproduces the trunk's own published d/D 0.471 and v 1.285 m/s
at 0.10 % exactly.)*

**What the surplus fall actually means on the ground, checked on the straight line at 12 m
intervals:** the ground falls away faster than any uniform grade can follow. On a single
uniform grade the pipe would have **less than 1.30 m of cover over the last 1.9 km**
(chainage 2,877–4,764 m) and would stand **1.84 m above ground at chainage 3,700 m**. That is
not a depth problem — it is the inverse of one — but it does mean **the extension is not a
single grade.** It is laid to follow the ground at minimum cover, steeper than the minimum
gradient, with the surplus taken in steeper reaches or drop structures. Both are far cheaper
than digging, and both need the profile drawn on a real corridor rather than a straight line.
The 6.25 km used here is a straight line times the measured sinuosity, not a routed length.

**What it costs:** the worst conveyance position on the list. Load-weighted conveyance
**21.77 km** against A's 16.21 km, and 16.20 km to the load centroid. Every additional metre
between the existing outfall and B is new DN1700-class trunk. It is also **9,062 m from the
nearest dual carriageway** — sludge cake, chemicals and every heavy delivery for fifty years
travel that on single carriageway — and it has the **poorest TE position of the seven**,
253 ha of agriculture in a 10 km square against A's 1,110 ha and D's 2,322 ha, though the
proposed TE main passes within 284 m.

### C — proposed north-west, E440 797 N2 567 533, GL 321.59 m

**The quietly strong one, and the one nobody has looked at.** 100 % gravity; 850 m to the
nearest built plot, and the nearest *planned* residential plot is further out at 1,261 m, so
the buffer **does not deteriorate at the saturation horizon** — unlike W10-S1, which drops
from 1,045 m today to 708 m once the planned plots are built. It stays inside the band and
needs the odour model like the others. **No registered plot within 800 m**; 64.9 ha free
inside an 825 m square;
**3,220 m from hazard class ≥ 4, the best flood margin of the seven**, with only 20.1 % of the
surrounding kilometre untested; 112 m from a road; 2,007 m from a dual carriageway, better
than A or B; and 7.1 m lower than the existing works, which is where its gravity margin comes
from.

**Its weakness is the treated effluent.** 5,607 m from the proposed TE network — by far the
furthest — and only 504 ha of agriculture in a 10 km square. Conveyance 18.00 km, between A
and B.

One caution that is *not* a disqualification: carrying the existing trunk on to C at the
Table 11 minimum reaches **11.64 m of cover** at the worst point on the straight line, 0.36 m
under the 12 m cap, because a rise to 333.08 m sits between the two. C is not downstream of
the existing works in any useful sense; if the works moves there the trunk's western end is
re-drawn to it, not extended. That re-solve has not been run.

### D — proposed east, E452 431.9 N2 567 077, GL 360.37 m

**Excluded as a central works, on the guideline's own floor.** 125 m to the nearest built
plot against the **300 m** lower bound of G201-p43 Table 8. It is also 152 m from hazard class
≥ 4, sits on a 0.76 ha agricultural plot with 386 registered plots (56.6 ha) within 800 m,
has 23.8 ha free in an 825 m square, and takes only 68.9 % of the load by gravity — the other
31 % would be pumped for fifty years.

**But it is the best-placed site on the list for conveyance** — 10.17 km load-weighted,
3.69 km from the load centroid, 2,322 ha of agriculture within a 10 km square — and that is
worth saying because it names the trade this whole scheme turns on. **The load is in the east;
the low ground and the empty land are in the west.**

### E and E2 — proposed north-east

The client layer and the August delivery disagree by **1.9 km** about where this site is:
`IBRI STP.shp` holds E457 546.9 N2 576 181.0, `Proposed STP.shp` holds E458 738.6
N2 577 651.0. **Both were measured. They are not the same site and one of them has to be
withdrawn.**

**E2 fails on two counts at once.** It is **250 m from a built plot — below the 300 m floor**
of the large-STP band and less than half the 500 m generic default that would apply to a
medium works — and it has **no land**: 0.0 ha free inside a 625 m square and 1.8 ha inside an
825 m square, sitting on a 27.3 ha agricultural plot with 556 registered plots (163.2 ha)
within 800 m.

**E is a satellite candidate, and a coherent one.** 30.3 ha free in an 825 m square, 375 m to
the nearest built plot (above the 300 m floor, well inside the band), and only 17.8 % of the
surrounding kilometre untested for flood. It takes **15.2 % of the central load, 11,182 m³/d,
by gravity, with a mean haul of 9.11 km.** That figure is not arbitrary: the servicing layer
puts **AL DIREZ at 9,488 m³/d and BAT at 1,479 + 263 m³/d — 11,230 m³/d together**, and their
centroids (E462 707 and E474 010) are east of E. **E's gravity catchment is the Al Direz / Bat
arm, almost exactly.**

Today that arm is hauled 18.3–29.6 km west to the existing works, and it is why the trunk
carries a lifting station at E464 359 N2 566 792, 11.44 m deep, handling **963 m³/d — 1.3 % of
the central load**.

### W10-S1 — carried for comparison only

E443 075 N2 566 675, a 50 m cell centre from W10's weighted suitability surface, not a site
anyone has proposed. On this project's own measurements it looks much like C: 99.8 % gravity,
64.7 ha free in an 825 m square, 1,045 m to a built plot today — **but 708 m once the planned
plots are built**, because a planned residential plot sits closer than any built one. It is
the only site on the list whose buffer gets materially worse at the design horizon, which is
worth knowing about the site a previous study ranked first under every weighting it tried.

**It is not one of the options below** — proposing a new site while four client sites sit
unassessed would repeat exactly the mistake this document is reporting.

---

## 6. The options

Scope p13: *"The Consultant shall prepare and submit minimum three option for STP"*, and
*"The Consultant shall prepare and submit recommended option based on Life Cycle cost and
Risk Assessment."* Four are set out. **No recommendation is made here** — the recommendation
is a life-cycle-cost output and the cost basis is not yet in place (`_BRAIN/05_GAPS.md`:
Renardet's priced BoQs are still awaited and the TE price and offtaker are unknown).

### Option 1 — Single central works, expanded in place at **A**

The existing 1,800 m³/d plant grows on its own ground, in phases, to the ultimate duty.
Matches NWS's own unapproved 29,038 m³/d asset-planning concept. The trunk is already drawn
to it; nothing about the network changes.

**Turns entirely on two questions that are not ours:** can NWS acquire enough of the 66.6 ha
of registered plots within 800 m, and does the odour model put the 5 OU contour inside 712 m?
If either answer is no, this option ends. It also carries the weakest flood evidence of the
seven and the deepest trunk arrival, 8.78 m.

### Option 2 — Single central works relocated south to **B**, with A retained through the transition

A stays in service, and can serve as the phase-1 works, while the trunk is carried 6.25 km
south to a new works at B. Buys the largest amenity margin available (2,627 m built,
3,818 m planned), a single unplatted land parcel, and 100 % gravity with surplus head.

**Costs 6.25 km of new DN1700-class trunk and the worst conveyance position on the list**
(21.77 km load-weighted). Puts the works 9 km from the nearest dual carriageway and at the
edge of the irrigation market (253 ha of agriculture in a 10 km square). The extension itself
is hydraulically straightforward — surplus fall, d/D 0.399, v 1.60 m/s on a 0.179 % uniform
grade — but it is **not** a single grade: over the last 1.9 km of the straight line the ground
falls away faster than the pipe, so the profile is broken into steeper reaches. It needs a
corridor and a real profile before the length is quoted as anything but a straight line.

### Option 3 — Single central works relocated north-west to **C**

The trunk's western end is re-drawn to C rather than extended. Buys the best flood margin
(3,220 m from hazard, only 20.1 % of the surrounding kilometre untested), unplatted land with
no registered plot within 800 m, a buffer of 850 m that **does not deteriorate** at the
saturation horizon, and 7.1 m of relief on the existing works' ground level, at a conveyance
penalty between A and B.

**Its open item is the TE network**, 5,607 m away with 504 ha of agriculture nearby, and the
trunk re-solve, which has not been run.

### Option 4 — Split system: a western/southern central works **plus an eastern satellite at E**

Any of A, B or C takes the Ibri core; **E takes the Al Direz / Bat arm — 11,182 m³/d by
gravity, mean haul 9.11 km** — and removes an 18–30 km westward haul and the 963 m³/d lifting
station at E464 359 from the trunk. It also puts a works where the TE customers are: 1,980 ha
of agriculture within a 10 km square against B's 253 ha.

**Note this is a materially different question from Option 1–3, and the difference is
regulatory.** An eastern works at 11,182 m³/d is **medium**, not large (G203-p65: 500 ≤ medium
< 20,000). Its buffer requirement under G201-p43 Table 8 would be the **500 m generic
default**, not the 300–1,000 m band — and E measures **375 m**. **A satellite at E does not
clear the medium-STP buffer as things stand**, and the resolution is a site adjustment of a
few hundred metres, not a waiver. It is a real option and it needs its own siting exercise
inside its own catchment, which this document does not attempt.

**Not carried forward as central-works options:** **D**, which fails the 300 m guideline floor
at 125 m; and **E2**, which fails the same floor at 250 m and has 1.8 ha of free land in an
825 m square. Both are measurements against a stated guideline value, not judgements, and both
are reversible only by moving the point.

---

## 7. Comparison table for the appraisal

Scored against what can actually be measured. **No weights are applied and no total is
struck** — the settled options doctrine is that NWS sets the weights.

| Criterion (G203-p63 Table 27 ref) | Option 1 · A | Option 2 · B | Option 3 · C | Option 4 · split (× + E) |
|---|---|---|---|---|
| **(m) Buffer to dwellings, today** | 712 m — inside band, needs the odour model | **2 627 m — clears** | 850 m — inside band | E at 375 m — **fails the 500 m medium default** |
| **(k) Governing buffer at the saturation horizon** | 712 m — no change | **2 627 m — no change** | 850 m — no change | E at 375 m — no change |
| **(c) Land, unplatted, 825 m square** | 37.1 ha, plus an assembly of 117 plots | **66.2 ha, no plots at all** | 64.9 ha, no plots at all | E 49.4 ha |
| Land against the 12–43 ha envelope | fits the low end only | fits either end | fits either end | ample for 11,182 m³/d |
| **(f) Gravity share of the central load** | 99.5 % (3 trunk stations remain) | **100 %, with surplus head** | 100 % | E takes 15.2 % of the whole by gravity |
| **(n) Conveyance, load-weighted** | **16.21 km** | 21.77 km — worst | 18.00 km | removes an 18–30 km arm |
| New trunk beyond what is drawn | none | 6.25 km DN1700-class | western end re-solved | eastern arm truncated |
| **(i) Flood — distance to hazard class ≥ 4** | 1 800 m | 917 m | **3 220 m** | E 451 m |
| **(i) Flood — untested ground within 1 km** | **46.7 % — worst** | 28.1 % | **20.1 %** | E 17.8 % |
| **(a)(b) Access — to a dual carriageway** | 4 414 m | 9 062 m — worst | **2 007 m** | E 1 152 m |
| TE reuse — agriculture in a 10 km square | **1 110 ha** | 253 ha | 504 ha | **E 1 980 ha** |
| TE reuse — to the proposed TE main | **134 m** | 284 m | 5 607 m | E 1 516 m |
| Trunk arrival depth at the works | 8.78 m (measured) | shallow, surplus fall | not re-solved | — |
| Existing 1,800 m³/d plant | absorbed | retained through transition, then a decision | retained through transition, then a decision | either |
| Land acquisition | **assembly of registered plots** | single allocation | single allocation | E: 357 plots within 800 m |
| **Cannot be scored** | ownership · odour model · geotechnical · groundwater · wind direction · 100-year flood · TE demand · EIA | as A | as A | as A |

---

## 8. What needs a client decision

| # | Decision | Why it cannot be ours | Blocks |
|---|---|---|---|
| **1** | **Commission an odour dispersion model and fix the 5 OU contour.** | G201-p43 Table 8 says the 300–1,000 m band is set by that model. Four of the seven candidates sit inside the band and two below its floor; only B clears it. | every site with a buffer under 1,000 m — A, C, E and the W10 reference cell inside the band, D and E2 below its floor |
| **2** | **Is the ground around the existing works acquirable, and how much of it?** 117 registered plots, 66.6 ha, within 800 m, including a 12.9 ha planned plot at 283 m. | Land is acquired by NWS from MoHUP (TOR p20, 4.1.2.5); ownership is not in any layer we hold. | Option 1 entirely |
| **3** | **Which north-eastern point is the real one** — E457 546.9 N2 576 181.0 or E458 738.6 N2 577 651.0? | Two client layers disagree by 1.9 km, and the two positions score differently on land: 30.3 ha versus 0.0 ha in a 625 m square. | Option 4 |
| **4** | **Confirm in writing that the SUREKHA 29,038 m³/d record is not a commitment.** Its own field says the concept is *"not approved yet"*. | A committed plant at that capacity, 134.5 m from the existing works, would constrain every option here. | Options 2, 3, 4 |
| **5** | **Phase-1 capacity — above or below 20,000 m³/d?** | It is a scope boundary, not only an engineering choice: TOR p3, p4, p6, p27 and p30 make preliminary design and the EPC tender for STP Phase I part of the consultancy scope **only if Phase I is under 20,000 m³/d**. | the whole phasing question, and the consultant's own scope |
| **6** | **Weights for the options appraisal.** | Settled project doctrine: NWS sets them. | the recommendation the TOR asks for |
| **7** | **Is the existing 1,800 m³/d plant decommissioned, retained as a phase, or kept as standby?** | TOR p5 items 6 and p13 require integration between old and new STP; it is an asset decision. | Options 2 and 3, and the emergency-lagoon sizing |
| **8** | **Lagoon depth for the 5-day emergency storage.** | No guideline value; 3 m versus 5 m moves the land requirement by 5.4 ha at the ultimate flow. | the land envelope, and therefore Option 1 |

---

## 9. What the phasing decision needs, and why it cannot be taken yet

**The phasing is a concept-stage deliverable** — G201-p19/p21 Table 2 lists *Project Phasing*
under the concept column, alongside *Site Selection, Routing and Layout*, *Flood Protection
Assessment* and *Optioneering / Whole Life Costing*. It is due now, not later. It still cannot
be taken, for one reason:

**There is no flow-versus-year curve in this project.** Every flow figure quoted anywhere in
W11a is the ultimate saturated load. G201-p59 is explicit: *"development speed must be
considered through appropriate phasing assumptions, as not all plots will be developed
simultaneously … development percentages must be applied over the design period to reflect
realistic build-out scenarios and particularly avoiding overestimation."* Those percentages
have not been supplied. `W11a/py/s8_packages.py` already refuses to invent them, and says so
in its own docstring: it can mark a package as having demand at the start year and *"does
not, and cannot, place a package in 2030 rather than 2055."*

To close it, the appraisal needs, in this order:

1. **The build-out curve** — plots developed per model year (start / 2030 / 2055 / ultimate),
   from NWS or MoHUP planning data, per G201-p59. Without it there is no Q(t) and no phase
   sizing.
2. **The site**, from §6 — because the phase-1 works has to be laid out on the site that will
   also hold the ultimate works, and A's land envelope is the binding one.
3. **The 15-year rule.** G203-p65: an STP *"shall be designed for a design horizon of at
   least 15 years."* A phase that serves less than that is not a phase, whatever the flow
   curve says.
4. **Life-cycle cost per option**, per TOR p13 and G201-p19. Needs the unit-rate basis that
   is still awaited (`_BRAIN/05_GAPS.md`: Renardet priced BoQs; energy tariff; TE price).
5. **The existing plant's fate** (decision 7) — 1,800 m³/d of existing capacity either counts
   towards phase 1 or does not.
6. **The technology short-list**, because Table 28 spans a factor of 8 in land between MBR
   and CAS/EA and the site decision cannot be finalised while the process is open. TOR p15
   item 11 asks for *"an appropriate technology for the STPs for the allocated land and the
   required Class A standards"* — note the direction of that sentence: the TOR expects the
   land to be allocated first and the technology chosen to fit it.

**What the phasing decision does *not* need is more site analysis.** The measurements in §4
are sufficient to eliminate D and E2 and to carry three central-works options and one split
option forward.

---

## 10. What is missing, and what it would change

| Missing | Consequence | Guideline that requires it |
|---|---|---|
| **Odour dispersion model (5 OU contour)** | The buffer band cannot be closed; every site except B is provisional on amenity, and two are below the floor without it | G201-p43 Table 8 note |
| **Prevailing wind direction / wind rose** | Every buffer here is a circle; the real requirement is directional | G203-p63 Table 27 (e) |
| **100-year flood extent** — we hold only `Hazard_T50y` | (i) asks for 25 and 100 year and full operation during floods; neither is available | G203-p63 Table 27 (i) |
| **Hazard-grid coverage** — 62.2 % of the working frame has an answer; **46.7 % of the ground within 1 km of the existing works has none** | The flood credential of the preferred-on-conveyance site is the least evidenced | G203-p63 Table 27 (i) |
| **Land ownership** — `MoH_Plots.OWNER_NAME` is populated on **1,704 of 61,272 plots (2.8 %)**; `MULKIYA`, `TITLE` and `LAND_STATU` are populated on **zero** (measured 2026-09-02) | The single biggest unscored criterion. If NWS already owns one of these parcels, that alone can decide the ranking | TOR p20 4.1.2.5 |
| **Geotechnical / geophysical investigation** | Mandatory for STPs, and bearing capacity and rock could move the earthworks cost by more than the conveyance difference between the options | G201-p40 §6.1.2.1–2 |
| **Groundwater depth and aquifer vulnerability** | B is the lowest site by 17 m and the most likely to meet groundwater; untested | G201-p43 §6.1.3.2 |
| **Wellfield, falaj and drinking-water protection zones** | No layer received; a protection zone could exclude a site outright | G201-p43 §6.1.3.2 (2)(b) |
| **EIA** | Full EIA due in concept / preliminary design | G201-p44 §6.1.4.3 |
| **Actual TE irrigation demand and the offtaker** | Agricultural plot *locations* are known; their water demand is not, so the TE column above is a proximity proxy, not a market | G201-p35 §5.4; `_BRAIN/05_GAPS.md` |
| **Build-out curve (development percentages by year)** | Blocks the phasing entirely — see §9 | G201-p59 |
| **Power supply network** | No HV/MV layer; connection cost and distance unscored for every option | TOR p15 item 25, p23 item 36 |
| **Archaeology and heritage** | No layer; MoHC is a named consultee | G203-p39 §7.2 (stakeholder list) |
| **Existing works inlet invert and condition** | Open item S3-3. The trunk is laid to its own level, 319.94 m aOD, 8.78 m below ground, published for confirmation | GAP-7 |

---

## 11. Method, assumptions and known weaknesses

**Guideline values** are quoted in §2 with pages, read out of the PDFs for this task.
**Project assumptions** are these, and only these:

| Assumption | Value | What would settle it |
|---|---|---|
| Wadi ground | 50-year hazard class 4–6 | A scour-depth study. The classes are AR&R flood-hazard classes keyed on danger to people and vehicles, standing in for G203-p30 4.4.1 *"areas subject to washout"*, which is a scour criterion. Philosophy H1a |
| Collector invert where load enters | 2.0 m below ground | Only the 4.0 m difference from the works inlet enters the test |
| Works inlet depth | 6.0 m below site ground; 9.0 m tested as a sensitivity | The trunk actually delivers 8.78 m at A. Nothing in the ranking moves between the two |
| Emergency-lagoon depth | 3 / 4 / 5 m, all three reported | Client decision 8 |
| Land within 20 m of a road centreline is not free | 20 m | The service-corridor widths G203-p33 tabulates are for pipes, not for a works boundary; 20 m is ours |
| Odour receptor set | 17,950 built plots — every W3 class-B plot, except a plot of ≥ 5 ha whose land use does not say people are on it | A field check. 11 large unlabelled parcels are dropped by this rule; two of them are the existing works' own compound, which would otherwise measure 0 m to a dwelling |
| Plant-plus-lagoon land envelope | ~12–43 ha | The technology short-list, decision 6 |

**Known weaknesses, stated so nobody has to find them:**

1. **The gravity test is a head screen and nothing more.** §4.1. It does not route pipes, does
   not test the 12 m cover cap between the load and the works, and assumes a single gravity
   path from each load centre. Site A passes at 99.5 % and the real trunk still needs three
   lifting stations.
2. **Only 2,652 of the 17,961 built plots carry a residential land use at all.** The buffer is
   measured to *built plots*, not to *confirmed dwellings*. Conservative in the right
   direction, imprecise in an unknown one. (`GAP-9`: 65 % of plots have an empty `LANDUSE`.)
3. **Free-land measurement is on a 25 m grid.** A 625 m window holds at most 39.1 ha and an
   825 m window at most 68.1 ha, so B's 66.2 ha means "almost all of it", not "66.2 ha and no
   more". The measurement cannot resolve a site boundary; a footprint has to be laid out on
   the 0.5 m terrain at the next stage.
4. **Conveyance is a straight line times a measured sinuosity, not a route.** A measures
   16.21 km here against W10's 12.97 km; 16.21 ÷ 1.296 = 12.51, so most of the difference is
   the sinuosity factor W10 did not apply, and the residual is the weighting — plot count
   there, published Q here.
5. **The trunk alignment is an input.** It was drawn to end at the existing works, so any
   metric using distance-to-trunk structurally favours A. `D_TRUNK_M` is reported for
   information and is deliberately not used as a criterion in §7.
6. **The extension profile for Option 2 was checked on a straight line, not a corridor.** The
   1.9 km stretch where the ground falls below a uniform grade, and the 1.84 m of daylight at
   chainage 3,700 m, are real on that line. A corridor route will differ. A corridor **does**
   exist near it — 18 corridor segments totalling 6.56 km lie within 300 m of the straight
   line, and the nearest corridor to site B is 344 m away (for A→C, 133 segments / 19.91 km,
   nearest corridor to C 133 m; both read from a snapshot of `W11a.gpkg [corridors]` taken
   2026-09-02). **That is proximity, not connectivity**: no route has been traced and no
   continuity check has been run.
7. **Ground levels use the 0.5 m VRT at every point that is quoted.** The 25 m mask grid uses
   the 5 m component of the same VRT, because the 0.5 m blend carries no overviews and a
   decimated read across 48 × 27 km would touch 5.2 billion source pixels.
8. **The study boundary used here is `MoHUP_DATA/Project_boundary.shp`, 439.8 km²**, which is
   what `figkit` uses. W10 used `Study area/Project Boundary.shp`, 531.4 km². Percentages of
   "the study area" are not comparable between the two documents.

---

## 12. Re-running

```
python "W11a/report/stp_options.py"            # full measurement + both figures, ~4 min
python "W11a/report/stp_options.py" --cache    # redraw the figures from the last measurement
```

All guideline constants sit at the top of the module with their page in the comment beside
them. Changing `WORKS_INLET_M`, `COLLECTOR_INVERT_M`, `WADI_CLASSES`, `RECEPTOR_BIG_HA` or
`FREE_CELL_M` re-derives the table and both figures together. Nothing in the module writes to
`W11a/shp/`; every layer is read from a verified copy in the figkit scratchpad.

---

## 13. Live-document entries this creates

Written here rather than applied, because several stage modules and the live documents were
being edited by other work at the same time as this study. Somebody has to fold these in:

| Document | Entry |
|---|---|
| `_BRAIN/03_DATA_INVENTORY.md` | `IBRI STP` is **5 points**, not 1 (1 existing + 4 proposed, edited 2026-09-01), and **`SHP/Proposed STP` (3 points, delivered 2026-08-09) is missing from the inventory entirely**. The north-east point differs between the two layers by 1.9 km |
| `_BRAIN/00_CURRENT.md` | Add this document to the live table. Add the open item: **two client layers disagree on the north-eastern STP site by 1.9 km** |
| `_BRAIN/07_PROJECT_STATE.md` | The STP land requirement is **12–43 ha** at the corrected flow, not W10's 20/30 ha. STP siting has four client-proposed sites, of which two fail the G201-p43 buffer floor |
| `_BRAIN/05_GAPS.md` | New gap: **no odour dispersion model**, which is what G201-p43 Table 8 says sets the 300–1,000 m band. New gap: **no build-out curve**, which G201-p59 makes mandatory input to phasing and which blocks the STP phase sizing |
| `W10/docs/STP_SITING.md` | Mark **superseded on the land requirement** — it was sized against the retired 49,700 m³/d. Its method and its "cannot be evaluated" register still stand |
