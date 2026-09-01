# STP site suitability — W10 Phase 4.3

**Ibri Sewer, TE & STP (2621) · Renardet / Nama Water Services · greenfield run W10 · 2026-09-01**

**S1 at E443075 N2566675 is the best site the data can find, and it holds first place under every
weighting I tried. The existing works cannot take 50,000 m³/d — it has 20.6 ha of unplatted land
around it against a 30 ha target, and that, not odour, is what rules it out. The proposed southern
site is a genuinely good site that the scoring puts 11th of 12, entirely on conveyance: it is
4.1 km from the trunk, 9.1 km from the nearest dual carriageway, and its load-weighted conveyance
distance is 17.2 km against S1's 12.5 km. If NWS already owns the southern land, that ranking is
worth revisiting — ownership is the one criterion I could not score at all.**

---

## 1. What was built

| Output | Path |
|---|---|
| Scored surface, 50 m grid, 0–1 | `W10/shp/W10_stp_suitability.tif` |
| Seven criterion bands, same grid | `W10/shp/W10_stp_criteria.tif` |
| Shortlist + the two known sites | `W10/shp/W10_stp_candidates.shp` |
| Same table as CSV | `W10/run/p4_stp_candidates.csv` |
| Map | `W10/img/W10_P4_stp_suitability.png` |
| Script (re-runnable, ~20 s) | `W10/py/p4_stp_siting.py` |

Grid: 50 m scoring cells (475,230 over the bounding box, 212,586 inside the boundary). Masks and
distance transforms are computed at 10 m and aggregated down, because the median built plot in Ibri
is 0.064 ha — about 25 m across — and a 50 m rasterisation loses it.

---

## 2. Method in one paragraph

Seven criteria, each normalised to 0–1 over the whole surface, combined by fixed weights that sum
to 1.00. Four hard exclusions zero the score outright — they are regulatory or physical, not
tradeable. Candidates are the ten highest-scoring cells subject to a 2.5 km minimum separation, so
the shortlist is ten distinct locations rather than ten cells of the same hill. The existing works
and the proposed southern site are then sampled off the identical surface, and an unmasked
`SCORE_RAW` is carried alongside the masked `SCORE` so a site that trips an exclusion can still be
compared on merit.

---

## 3. Guideline values — read from the source, with pages

Every number below was read out of the PDF for this task. None is quoted from memory.

| Value | Source | Page |
|---|---|---|
| STP site selection criteria (accessibility, land availability, topography to limit pumping, flood, nuisance/odour, proximity to residential, buffer requirement, capex/opex) | PAM-GUD-203 §10.1, **Table 27 Site Selection Requirements** | G203-p63 |
| Land area requirement by technology, m² per m³/d | PAM-GUD-203, **Table 28 Land Area Requirement** | G203-p64 |
| Buffer STP (small/medium) 500 m to residential / sensitive uses | PAM-GUD-201 §6.1.3.3, **Table 8 Minimum buffer zone requirements** | G201-p43 |
| Buffer STP (large) **300 m – 1000 m**, "Based on odour modelling (5 Odour Units OU contour)" | PAM-GUD-201, Table 8 | G201-p43 |
| Sewage pumping station 30 m to residential | PAM-GUD-201, Table 8 | G201-p44 |
| Built footprint ≤ 35 % of allocated land; boundary setback ≥ 5 m | PAM-GUD-201 §6.4.2 Land Occupancy | G201-p50 |
| "Wastewater systems benefit from natural slopes, minimizing the need for costly pumping and lifting stations" | PAM-GUD-201 §6.1.1 Topography, item 1(b) | G201-p37 |
| Geophysical + geotechnical investigation mandatory for STPs | PAM-GUD-201 §6.1.2.1 / §6.1.2.2 | G201-p40 |
| Groundwater and wellfield protection buffers required | PAM-GUD-201 §6.1.3.2 | G201-p43 |
| EIA in concept / preliminary design | PAM-GUD-201 §6.1.4.3 | G201-p44 |
| TSE used to irrigate farms and landscaping under MD 145-93 | PAM-GUD-201 §5.4 | G201-p35 |

### 3.1 Where the guidelines give no number

- **Wadi / flood setback for an STP site.** G203-p63 Table 27 (i) requires compliance with the 25
  and 100 year flood levels and states that "STPs shall be fully operational during floods", but
  neither book gives a metric setback from a wadi for a *site*. The only wadi distance in either
  document is 15 m either side of a **pipe** crossing for ductile iron (G201-p86), which is a
  pipeline rule and does not transfer. **I used 100 m from the 50-year hazard edge as my own
  engineering judgement**, on the grounds that the hazard grid is a 3 m regional product and a
  one-cell margin is meaningless against model error and lateral bank migration. It is not a
  guideline value and is flagged as ours on the map. [Certain that no number exists — grep of all
  three guidelines for wadi + setback/buffer/distance returns only the pipe-crossing clause.]
- **Which flood return period governs siting.** The available hazard grid is the 50-year
  `Hazard_T50y.tif`. G203-p63 asks for 25 and 100 year. The 50-year is a defensible interim
  screening layer, but the 100-year extent must be obtained before any site is fixed. [Certain
  this is a gap.]
- **Design horizon flow for the buffer band.** G201-p43 does not say what "large" means in m³/d.
  49,700 m³/d is not arguable as small or medium, so the 300–1000 m band governs. [Likely.]

---

## 4. Land requirement — how 30 ha was arrived at

Ultimate saturated design flow for the whole study area is **49,700 m³/d**, +10 % = **54,700 m³/d**
(established, PROJECT-STATE — not re-derived here).

Applying G203-p64 Table 28:

| Technology | Footprint m²/(m³/d) | Land at 54,700 m³/d |
|---|---|---|
| MBR | 0.45 – 0.90 | 2.5 – 4.9 ha |
| SBR | 0.90 – 1.80 | 4.9 – 9.8 ha |
| MBBR | 0.90 – 1.80 | 4.9 – 9.8 ha |
| IFAS / hybrid fixed biofilm | 1.20 – 2.50 | 6.6 – 13.7 ha |
| **CAS and Extended Aeration** | **1.80 – 3.60** | **9.8 – 19.7 ha** |
| Constructed wetland (reed bed) | > 10 | > 55 ha — out of scope at this flow |

**Adopted: 20 ha absolute minimum, 30 ha target.** The 20 ha is the CAS/EA upper bound rounded up —
the most land-hungry mainstream process, kept open because the process is not yet chosen and a site
that only fits an MBR pre-commits the option. The 30 ha adds 50 % for the things Table 28's own
preamble lists but does not size: phasing, sludge handling, buffer zones, TSE storage, and the
solar farm G203-p64 explicitly asks the designer to assess.

The 35 % built-footprint rule (G201-p50) is **not** applied on top of this. Table 28's preamble
describes it as "the total land footprint required to accommodate all associated infrastructure …
including the main process units, sludge handling facilities, buffer zones", i.e. it is the plant
land, not the building plan area. Multiplying by 1/0.35 would double-count and give 56 ha.
[Likely — the wording supports this reading but it is a reading, not a statement.] The 35 % rule
governs the internal layout at detail design.

Measured on the grid as the free land inside a **650 m square** (13 cells × 50 m = 42.25 ha
window). A 30 ha block is 548 m square, so the window is the smallest odd-cell square that can
contain the target with a working margin.

---

## 5. The criteria

`ramp(x, a, b)` = 0 at a, 1 at b, linear between, clipped.

| # | Criterion | Source | What was measured | Score |
|---|---|---|---|---|
| **C2** | Gravity reachability of the catchment | G203-p63 Table 27 (f); G201-p37 §6.1.1(1)(b) | share of the ultimate load that reaches the cell by gravity | see §5.1 |
| **C1** | Separation from dwellings | G201-p43 Table 8 | metres to the nearest odour receptor | `ramp(d, 300, 1000)` |
| **C4** | Land availability | G203-p63 Table 27 (c); p64 Table 28 | free land in a 650 m square, ha | `ramp(A, 20, 30)` |
| **C5** | Conveyance cost | G203-p63 Table 27 (n) | ½ trunk proximity + ½ load-weighted distance | `½·ramp(d,5000,0) + ½·ramp(L, p90, min)` |
| **C7** | TSE reuse proximity | G201-p35 §5.4 | ½ distance to agriculture + ½ agricultural area within 5 km | `½·ramp(d,5000,500) + ½·ramp(A, 0, p90)` |
| **C6** | Road access | G203-p63 Table 27 (a)(b) | ½ any road + ½ dual carriageway (sludge tankers) | `½·ramp(d,2000,200) + ½·ramp(d,5000,1000)` |
| **C3** | Flood margin beyond the exclusion | G203-p63 Table 27 (i) | metres from the 50-yr hazard edge | `ramp(d, 100, 500)` |

### 5.1 C2 — the gravity test

The brief asked for hydraulic reachability, not raw elevation, and raw elevation would be wrong:
the lowest ground in the study area is in the south-east, 20 km from most of the population.

54,906 built and planned plots are aggregated onto a 500 m grid, giving **1,059 load centres**,
each weighted by its plot count. A load centre *k* reaches a works at cell *c* by gravity when

```
(z_k − 2.0) − 0.0010 × 1.30 × d(k,c)  ≥  z_c − 6.0
```

- **0.0010** is the gradient the given trunk is actually laid at (DN1000 at 0.10 %, Phase 4.2).
- **1.30** sinuosity converts straight-line distance into a plausible street-network pipe length.
  [Guessing — 1.30 is a standard orthogonal-grid figure, not measured on this network. The pure
  Manhattan bound is 1.41. It has not been calibrated against the W10 corridor network.]
- **2.0 m** collector invert below ground where the load enters; **6.0 m** the deepest acceptable
  inlet at the works.

C2 is the load-weighted fraction for which the test holds. Note the algebra: only the *difference*
(6.0 − 2.0) = 4.0 m enters, so both depth assumptions shift every cell equally and barely touch the
ranking. The sinuosity and the gradient do matter.

**This is a screen, not a design.** It does not check the 12 m cover limit at intermediate
chambers, it does not route pipes, and it assumes a single gravity path from each load centre.

Load weighting is one unit per built or planned plot; agricultural plots carry zero, per project
doctrine (the farming carries no load, the houses on it do, and those are separately classified B).

---

## 6. Hard exclusions

| Exclusion | Basis | Share of the 531.4 km² |
|---|---|---|
| 50-year flood hazard class 4–6, plus 100 m | G203-p63 Table 27 (i); the 100 m is ours (§3.1) | 25.4 % |
| Under 300 m to an odour receptor | G201-p43 Table 8, lower bound of the large-STP band | 43.2 % |
| On a registered MoHUP plot | land acquisition proxy | 37.7 % |
| Under 20 ha free in a 650 m square | G203-p64 Table 28 (§4) | 43.8 % |
| **Passes all four** | | **184.7 km² = 34.8 %** |

The four overlap heavily, so the percentages do not sum.

### 6.1 A correction that changed the answer, and why it matters

W3's `CLASS='B'` means *there are structures on this plot*, not *people live on it*. Eleven built
plots are 5 ha or larger with no land-use attribute; together they cover 1,005 ha, and the largest
is **899 ha — fourteen thousand times the median built plot of 0.064 ha**. Two of them, at 6.6 ha
and 29.0 ha, are the existing works compound itself.

Left uncorrected, that produced two false results in the first run:

1. The 899 ha parcel threw a 300 m exclusion and a 1 km buffer ring across ~20 km² of the west, and
   **three of the first ten shortlist positions were sitting on that ring** — an artefact of one
   polygon, not an engineering result.
2. The existing works measured **0 m to the nearest dwelling** and was excluded on odour, because it
   was acting as its own odour receptor.

**Rule adopted:** a built plot of 5 ha or more counts as an odour receptor only if its `LANDUSE`
says people are on it — residential, residential/commercial, residential/agricultural, mosque, or
government. Government is deliberately kept, because a government parcel may be a school or clinic.
This drops 11 parcels and keeps 17,950 receptors covering 1,617 ha. After the correction the
existing works measures **718 m** to the nearest receptor.

**Caveat that follows from this:** only 2,652 of the 17,961 built plots carry a residential land
use at all; 14,408 have none. The buffer is therefore measured to *built plots*, not to *confirmed
dwellings*, which is conservative in the right direction but imprecise. Three candidates sit close
to one of the eleven dropped parcels and the field `D_BUILT_M` records it: **S3 at 125 m, S4 at
671 m, S5 at 882 m**. Before any of those three is adopted, somebody has to establish on the ground
what those parcels are. [Certain that the distances are as recorded; guessing as to what the
parcels contain.]

---

## 7. Weights, and why

| # | Criterion | Weight | Reasoning |
|---|---|---|---|
| C2 | Gravity reachability | **0.25** | The only criterion that changes the whole-life cost *structure*. A site needing terminal pumping carries an energy bill and a failure mode for 25+ years, and G201-p37 and G203-p63(f) both single topography out. |
| C1 | Separation from dwellings | **0.20** | The only criterion with a numeric regulatory threshold (G201-p43 Table 8) and the one most likely to stop the scheme at consent stage. |
| C4 | Land availability | **0.15** | G203-p63(c), p64 Table 28. Binary in practice — either 30 ha exists or the option dies — but scored so a generous site beats a marginal one. |
| C5 | Conveyance cost | **0.15** | Capex, G203-p63(n). Weighted below C2 because pipe length is a one-off and pumping is forever. |
| C7 | TSE reuse proximity | **0.10** | G201-p35 §5.4. Lower, because reuse mains can be extended later and TSE can be tankered. |
| C6 | Road access | **0.08** | G203-p63(a)(b). Almost always solvable with an access road, so it should not decide a site. |
| C3 | Flood margin beyond the exclusion | **0.07** | G203-p63(i). Nearly all the flood requirement is already carried by the hard exclusion. |

**These are my weights, not NWS's.** The settled options doctrine (PROJECT-STATE §2 item 1e) is
that NWS sets the weights for the option appraisal; this set is a defensible default for screening.
§9 shows how much the answer moves if they are changed.

---

## 8. The shortlist

Coordinates EPSG:32640. GL from the authoritative 0.5 m terrain (`IBRI_0p5_VRT2.vrt`) at the point;
the surface itself uses the 5 m component of the same VRT block-averaged to 50 m, which agrees to
mean +0.06 m / std 0.46 m over 2,000 random points inside the boundary.

| # | Site | Easting | Northing | Score | GL m | Gravity % | To nearest dwelling m | Free 650 m ha | To trunk m | Conveyance km | To agri m | To existing km |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **S1** | 443 075 | 2 566 675 | **0.915** | 327.3 | 99.1 | 1 036 | 40.1 | 1 504 | 12.52 | 502 | 3.60 |
| 2 | **S2** | 443 025 | 2 564 075 | 0.881 | 326.8 | 99.5 | 1 040 | 40.7 | 1 578 | 13.56 | 446 | 1.58 |
| 3 | S3 | 440 525 | 2 568 325 | 0.880 | 325.4 | 98.7 | 1 096 | 30.8 | 1 492 | 14.46 | 822 | 6.33 |
| 4 | **S4** | 444 325 | 2 561 425 | 0.863 | 320.3 | 99.6 | 1 020 | 41.7 | 1 146 | 14.27 | 864 | 1.92 |
| 5 | S5 | 438 275 | 2 571 825 | 0.849 | 325.9 | 93.6 | 1 033 | 40.8 | 2 290 | 16.64 | 974 | 10.48 |
| 6 | S6 | 454 875 | 2 565 025 | 0.846 | 362.5 | **65.4** | 1 055 | 29.9 | 1 967 | 9.45 | 130 | 10.59 |
| 7 | S7 | 449 825 | 2 562 275 | 0.830 | 334.3 | 88.2 | 1 051 | 41.8 | 4 051 | 11.39 | 506 | 5.51 |
| 8 | S8 | 439 375 | 2 565 775 | 0.810 | 314.0 | 99.7 | 1 028 | 35.8 | 4 256 | 16.02 | 191 | 5.61 |
| 9 | S9 | 443 425 | 2 558 875 | 0.807 | 313.8 | 99.8 | 1 854 | 40.0 | 3 808 | 16.66 | 94 | 4.57 |
| 10 | S10 | 435 475 | 2 574 325 | 0.791 | 320.6 | 94.4 | 1 175 | 32.3 | 6 008 | 19.72 | 94 | 14.17 |
| 11 | **SOUTH** (proposed) | 442 451.3 | 2 558 941.8 | 0.791 | 311.9 | 99.8 | 2 616 | 41.1 | 4 091 | 17.20 | 1 050 | 4.82 |
| 12 | **EXISTING** works | 444 422.8 | 2 563 337.9 | *0.678 raw* | 328.7 | 98.6 | 718 | 20.6 | 5 | 12.97 | 653 | 0.00 |

Per-criterion scores:

| Site | C1 dwell | C2 gravity | C3 flood | C4 land | C5 pipe | C6 road | C7 TSE |
|---|---|---|---|---|---|---|---|
| S1 | 1.000 | 0.991 | 1.000 | 1.000 | 0.661 | 0.939 | 0.729 |
| S2 | 1.000 | 0.995 | 1.000 | 1.000 | 0.612 | 0.625 | 0.705 |
| S3 | 1.000 | 0.987 | 1.000 | 1.000 | 0.586 | 0.856 | 0.569 |
| S4 | 1.000 | 0.996 | 1.000 | 1.000 | 0.626 | 0.466 | 0.625 |
| S5 | 1.000 | 0.936 | 1.000 | 1.000 | 0.421 | 0.983 | 0.535 |
| S6 | 1.000 | 0.655 | 1.000 | 0.992 | 0.735 | 0.883 | 0.827 |
| S7 | 1.000 | 0.882 | 1.000 | 1.000 | 0.450 | 0.518 | 0.807 |
| S8 | 1.000 | 0.997 | 1.000 | 1.000 | 0.248 | 0.597 | 0.559 |
| S9 | 1.000 | 0.998 | 1.000 | 1.000 | 0.267 | 0.500 | 0.574 |
| S10 | 1.000 | 0.944 | 1.000 | 1.000 | 0.025 | 0.943 | 0.560 |
| **SOUTH** | 1.000 | 0.998 | 1.000 | 1.000 | **0.218** | **0.482** | 0.502 |
| **EXISTING** | 0.575 | 0.986 | 1.000 | **0.061** | **0.789** | 0.575 | 0.730 |

### 8.1 Reading the shortlist

- **S1 (0.915)** is 3.6 km north-west of the existing works, 1.5 km from the trunk, 99.1 % gravity,
  40.1 ha free and 1,036 m from the nearest dwelling. It wins on having no weakness rather than on
  any single strength.
- **S2 and S4** bracket the existing works at 1.6 km and 1.9 km. Either is close enough that the
  existing 1,800 m³/d works could stay in service through construction and be decommissioned or
  kept as a phase, and both are inside 1.6 km of the trunk. S4 at 320.3 m is 7.0 m lower than S1.
- **S6 (0.846)** is the interesting outlier: nearest to the population by conveyance (9.45 km, the
  best of all twelve) and the best TSE position (1,237 ha of agriculture within 5 km), but at
  362.5 m it is the *highest* site on the list and only **65.4 %** of the load reaches it by
  gravity. It is a satellite-works candidate for the eastern arm, not a candidate for the whole
  flow.
- **S9 is 976 m from the proposed southern site and scores 0.807 against its 0.791.** The southern
  area is genuinely good; the user's point is close to a local optimum within it.
- **C3 has zero spread across all twelve sites** (every one scores 1.000). Its 0.07 weight does
  nothing to the ranking — flood works entirely through the hard exclusion. That is worth knowing
  before anyone re-tunes the weights.

---

## 9. How the two known sites score

### The existing works — E444422.8 N2563337.9, GL 328.7 m

**Raw score 0.678, twelfth of twelve. Excluded by one test only: it sits on a registered plot —
its own 6.56 ha compound.** That exclusion is a proxy for *land you would have to acquire*, and it
does not apply to land NWS already holds, so the raw score is the fair number.

| | |
|---|---|
| Gravity | **0.986** — 98.6 % of the ultimate load reaches it by gravity. It is the trunk outlet, 5 m from the given alignment, and Phase 4.2 already showed the trunk works entirely by gravity to it at a maximum depth of 7.72 m. |
| Conveyance | **0.789 — the best of all twelve.** Nothing beats being the point the trunk was drawn to. |
| **Land** | **0.061 — this is what kills it.** 20.6 ha of unplatted land in the 650 m square, against a 20 ha floor and a 30 ha target. Add its own 35.6 ha compound and the site is workable at ~56 ha *if* the two compound plots are usable and the surrounding platted land is not, but there is no room for the 50 % phasing/sludge/TSE/solar allowance without acquiring registered plots. |
| Dwellings | **0.575** — 718 m to the nearest receptor. Clears the 300 m hard rule and the 500 m small/medium generic default (G201-p43), but is inside the 1,000 m upper bound of the large-STP band. At 49,700 m³/d, with the 5 OU odour contour unmodelled, 718 m is not a comfortable margin. |

**Conclusion: the existing site is the right place hydraulically and the wrong place for 50,000
m³/d.** Expanding it means acquiring platted land and accepting a 718 m odour buffer on a plant
28 times its present capacity. That is a decision for NWS with an odour model in hand, not a
screening result. [Likely.]

### The proposed southern site — E442451.3 N2558941.8, GL 311.9 m

**Score 0.791, eleventh of twelve — but the ranking is decided almost entirely by conveyance.**

| | |
|---|---|
| Gravity | **0.998 — the joint best on the list.** 99.8 % of the ultimate load reaches it. It is 16.8 m below the existing works (0.5 m terrain: 328.68 − 311.88), which is what buys that. |
| Dwellings | **1.000** — 2,616 m to the nearest receptor. Two and a half times the 1,000 m upper bound of the large-STP band. Nothing else on the list has this much room. |
| Land | **1.000** — 41.1 ha free in the 650 m square, largest inscribed clear circle 635 m across, in a 666 ha contiguous free block. |
| Flood | **1.000** — 765 m from the 50-year wadi edge. |
| **Conveyance** | **0.218 — the weakness.** 4,091 m from the trunk and a load-weighted conveyance distance of 17.20 km against S1's 12.52 km. Every additional metre of trunk between the existing outlet and this site is new DN1000-class pipe. |
| **Road access** | **0.482** — 343 m to the nearest road, but **9,052 m to the nearest dual carriageway**, the furthest of all twelve. Sludge cake and chemicals will travel 9 km of single carriageway. |
| TSE reuse | **0.502** — 1,050 m to the nearest agriculture, but only **220 ha within 5 km**, against S1's 867 ha and S6's 1,237 ha. It is at the edge of the irrigation market, not in it. |

**Conclusion: the southern site is the safest site on amenity, flood and land, and the most
expensive to pipe to.** Its 11th place is not a judgement that it is a bad site — its raw scores
are 1.000 on three criteria — it is the arithmetic of a 0.15 weight on conveyance meeting a
score of 0.218. Two things would change the ranking, and neither is in the data: **if NWS already
owns that land**, or **if the odour model puts the 5 OU contour beyond 1 km**, the southern site
moves up sharply.

---

## 10. Weight sensitivity

Five weightings, the same twelve sites. Rank in each:

| Site | base | gravity-led | cost-led | amenity-led | equal |
|---|---|---|---|---|---|
| **S1** | **1** | **1** | **1** | **1** | **1** |
| S2 | 2 | 2 | 3 | 3 | 4 |
| S3 | 3 | 3 | 4 | 2 | 3 |
| S4 | 4 | 4 | 5 | 5 | 6 |
| S5 | 5 | 5 | 6 | 6 | 5 |
| S6 | 6 | **11** | **2** | 4 | 2 |
| S7 | 7 | 8 | 7 | 7 | 7 |
| S8 | 8 | 6 | 9 | 8 | 9 |
| S9 | 9 | 7 | 8 | 9 | 10 |
| S10 | 10 | 9 | 12 | 11 | 8 |
| SOUTH | 11 | 10 | 11 | 10 | 11 |
| EXISTING | 12 | 12 | 10 | 12 | 12 |

(gravity-led 0.40/0.15/0.10/0.10/0.10/0.08/0.07 · cost-led 0.15/0.15/0.15/0.35/0.08/0.07/0.05 ·
amenity-led 0.15/0.35/0.15/0.15/0.08/0.07/0.05, order C2 C1 C4 C5 C7 C6 C3)

**S1 is first under every weighting.** S2–S5 stay in the top six under every weighting. S6 is the
only site that swings hard (2nd under cost-led, 11th under gravity-led) — exactly what you would
expect of a site that is close to the load and too high for it. The southern site and the existing
works stay in the bottom three throughout: no reasonable reweighting of the criteria *that could be
scored* promotes either. Ownership, which could not be scored, is the thing that would.

---

## 11. What could NOT be evaluated

These are unresolved, not scored as zero. Any of them can overturn the ranking.

| Not evaluated | Why | Guideline that requires it |
|---|---|---|
| **Land ownership and acquisition** | `MoH_Plots.OWNER_NAME` is populated for 1,704 of 61,272 plots (2.8 %); `MULKIYA`, `TITLE` and `LAND_STATU` are empty throughout. Nothing usable, and nothing at all for the unplatted land every candidate sits on | — (the single biggest gap) |
| **Geotechnical / bearing capacity / rock** | no borehole or geophysics data in the project | G201-p40 §6.1.2.1–2, mandatory for STPs |
| **Groundwater depth and aquifer vulnerability** | no piezometric data | G201-p43 §6.1.3.2 |
| **Prevailing wind direction** | no wind rose; this makes the odour buffer directional rather than circular | G203-p63 Table 27 (e) |
| **Odour dispersion model (5 OU contour)** | the thing that actually sets the 300–1000 m band | G201-p43 Table 8 note |
| **EIA** | to be run in concept / preliminary design | G201-p44 §6.1.4.3 |
| **Wellfield, falaj and drinking-water protection zones** | no wellfield layer received | G201-p43 §6.1.3.2 (2)(b) |
| **Archaeology and heritage** | no layer | — |
| **Power supply proximity** | no HV/MV network layer | G202-p153 (analogous requirement for TFS) |
| **MoHUP land-use consent for the unplatted land** | the "not on a plot" test says nothing about whether the land can be allocated | G203-p63 Table 27 (k) |
| **100-year flood extent** | only the 50-year grid exists | G203-p63 Table 27 (i) |
| **Actual TSE irrigation demand** | agricultural plot *locations* are known, their water demand is not | G201-p35 §5.4 |

---

## 12. Other caveats worth carrying forward

1. **C1 saturates at 1,000 m**, so seven of the ten candidates sit on the 1,020–1,096 m contour.
   That is the criterion working as specified — beyond the top of the G201 Table 8 band, more
   distance buys nothing and costs pipe — but it means the shortlist deliberately hugs the urban
   edge. If the odour model comes back with a 5 OU contour beyond 1 km, re-run with
   `DWELL_FULL_M` raised and the shortlist will move outward.
2. **`INSCR_M` is pessimistic.** It is the largest fully-free inscribed circle, and the free mask
   cuts a 20 m strip along every road centreline, so a minor track crossing a site chops it. S1's
   279 m against S4's 694 m is a shape warning, not a disqualification. `FREE600_HA` is the
   binding metric.
3. **The 1.30 sinuosity in C2 is not calibrated** on the W10 corridor network. It should be, before
   C2 is used for anything but screening.
4. **`COMP_HA` (contiguous free component) is not a useful discriminator here** — most sites sit on
   very large open desert components (S3, S5, S10 all report the same 4,510 ha block). It is in the
   attribute table for completeness.
5. **The trunk alignment is an input, not a result.** C5 rewards proximity to a line that was drawn
   to end at the existing works, which structurally favours sites near the existing works. If the
   works moves, the trunk should be re-drawn and C5 re-run — otherwise C5 is partly circular.
   [Certain — this is the most important methodological weakness in the whole surface.]
6. **The 50 m grid** cannot resolve a site boundary. Every candidate coordinate is a cell centre and
   the actual footprint has to be laid out on the 0.5 m terrain at the next stage.

---

## 13. Re-running

```
python "W10/py/p4_stp_siting.py"
```

~20 s. All constants are at the top of the file with their guideline page in the comment. Changing
`WEIGHTS`, `DWELL_HARD_M`, `DWELL_FULL_M`, `LAND_MIN_HA`, `LAND_GOOD_HA`, `S_MIN` or `SINUOSITY`
re-derives the surface, the shortlist, the map and the CSV together, and the map panels read their
statistics from the run rather than from hard-coded text.
