# AS-BUILT CALIBRATION — the numbers every run is scored against

**Measured from NAMA's built 2006 network, 2026-09-06.** Six independent studies, every claim
then re-measured by a second engineer told to refute it: **73 claims raised, 44 corrected,
4 refuted, 25 survived unchanged.** Two thirds of the first-pass findings had a wrong number
or a wrong rule — do not quote a figure that is not in this file.

Full record and method: `W12/docs/ASBUILT_STUDY.md`. Raw claims: `…_claims.json`.

**This is EVIDENCE, not a requirement.** `02_DESIGN_CRITERIA.md` holds the guideline values and
is the only source of a "shall". What NAMA built is how a real engineer solved this ground —
and 238 of their reaches cannot pass the saturated peak. Copy the plan geometry and the corridor
discipline. Copy nothing about size or level.

---

## The canonical funnel — quote it with every figure

```
SEWERLINE_IBRI.shp           3,396 rows / 314.28 km
  → STATUS == 'Ex'           3,267 rows / 111.57 km
  → drop 2 schematic rows    3,265 pipes /  95.4498 km   ← the built network
  → HAS_LVL == 1             2,142 pipes /  63.2043 km   ← the only levelled+sized part
```

`W10/shp/W10_existing_built.shp` is exactly the `Ex` subset (FEATUREID set equality, 3,267/3,267).
Diameters are in `OUT_DIAMET` — **`N_DIAMETER` is 0 on every built record**, a trap that has
already produced wrong numbers here.

**Package 5A-1 — 1,123 pipes, 32.245 km, 33.78 % of the network — carries no diameters, no
inverts, no material and no tier tokens.** It parses entirely as "lateral" by construction. It
corrupts the hierarchy ratio, chain depth, zone density, tier shares, uphill share and wadi
exposure *simultaneously* — it alone holds 89.6 % of the network's severe-hazard length. **Never
pool it. State it separately or exclude it and say so.**

---

## 1. Gates — a run that fails one of these is not finished

| Metric | Built value | Band for W12 |
|---|---|---|
| **Chambers per km** | 34.227 (trunk 32.45, sub-main 33.26, lateral 35.38) | **33–37 every tier**; flag < 28 |
| **Spacing median** | 29.77 m; p95 39.85; max 71.38. **140 reaches exactly 30.00 m, 46 exactly 35.00 m** | median **29–31 m**, p95 ≤ 40, declared cap **45 m** |
| **Chain depth, lateral → main** | median 2 hops, p90 3, max 5 (excl. 5A-1) | **≤ 2 median, ≤ 4 p90, 5 absolute**, per subnetwork |
| **Lateral-zone density** | 4.27 zones/km (excl. 5A-1) | **> 7/km means the main tier is missing** — the single best structural symptom |
| **Hierarchy ratio** | 73.2 % lateral→lateral / 22.1 % →sub main / 4.8 % →trunk | **window 60–78 %**, never a floor |
| **Tier length shares** | trunk 4.75 % / sub-main 10.40 % / lateral 84.86 % | **per subnetwork**: trunk 1.5–13.5 %, sub-main 10.9–17.2 %. A subnetwork with 0 % sub-main fails even if the average passes |
| **Cover by tier (median)** | lateral **1.395** / trunk **3.004** / sub-main **4.010 m** | publish all three. **The 2.6 m spread is the depth budget a branch needs** — a flattened-tier design fails on sight |
| **Deepest cover** | p99 6.02 m, max 8.693 m. Over 10 m: **zero**. Over 12 m: **zero** | **layout-fault trigger at 6 m**; 12 m is the separate compliance bar |
| **Uphill share / climb÷descent** | **29.88 % / 0.265** over the whole 95.45 km on the DEM | **beat both**, reported per subnetwork. Do NOT fit a terrain-dependent target — it is noise (ρ = −0.20, p = 0.70) |
| **Drops** | 0.585 vortex/km, 1.329 backdrop/km. **120 of 121 drops > 0.60 m sit at a junction** | beat both rates; **a non-junction drop is a hard failure**. Publish the same-tier / cross-tier split |
| **Flush pass-through** | **99.26 %** flush, median step 0.0000 m | hard gate |
| **Straightness per chamber** | trunk 3.31° / sub-main 5.35° / lateral 18.19°; 98.13 % two-vertex reaches | trunk ≤ 4°, sub-main ≤ 7°, lateral ≤ 22°. **No internal vertex over 20° without a chamber** |
| **Laid gradient** | median **6.001 mm/m** (mean 8.889). Lateral 6.032, trunk 5.187, **sub-main 4.036** | lateral median ≈ 6.0 with ≥ 20 % of length on the 6.0 rung; **a sub-main is never flatter than the laterals feeding it**; trunk ≥ Table 11 for its own bore |
| **Detour ratio** | median 1.23, p90 2.26 | median ≤ 1.45, p90 ≤ 2.8, ≤ 5 % above 4.0 |
| **Corridor** | 90.51 % within 8 m of road-or-plot-boundary; **7.52 % inside a plot** against a 3.04 % road null | **≥ 90 % on the first AND ≤ 3.04 % on the second** — as a pair. The first alone is passed for free |
| **Dual carriageways** | 0.0820 % of length, 1 chamber of 3,267 within 4 m — **~160× avoidance** | ≤ 0.2 % at a 4 m buffer; **publish the buffer** (1 chamber at 4 m becomes 12 at 10 m) |
| **Trunk hazard** | class 5–6 **1.15 %**, class ≥1 69.5 % — follows the valley, stays out of the channel | trunk class 5–6 ≤ 1.2 %, network ≤ 2.1 %. **Measure against roads within 150 m of the trunk, not the whole envelope** |
| **Trunk shadowing** | 6.6 % of trunk length has non-trunk pipe within 10 m | ≤ 10 % in a 10 m band |
| **Crossings** | **0** reaches cross without a shared chamber, in 95.45 km | any crossing W12 publishes is a defect |
| **Utilisation** | 238 reaches / 7.54 km over the d/D cap at saturation | **zero above 1.0 at the ultimate horizon**. SewerGEMS remains the referee |

**Advisory, not gates** — the evidence is too thin: joins per km of trunk (~4–5/km, but only
21 observations, and 0–11.7 across packages) · descent taken at chambers (28.1 %, biased high
by an unknown amount because 5A-1 is missing).

---

## 2. Three structural rules the built network settles

**T1 — A terminal is legal if it is the main pipe OR a pumping station with a designed rising
main.** NAMA's 5A-1 — **a third of the built network** — terminates 6,754 m short of the works
at a station and a 10 km rising main. **This retires the standing criticism of W11b's 18
subnetworks that "stop short of the main pipe":** the question is whether each ends at a
designed station, not whether gravity reaches.

**T2 — One package is one connected component with exactly one outlet.** True for all five
packages. Packages nest and cascade; they do not mesh. Exactly 2 cross-package pipes exist.

**T3 — Chambers first, then fill.** Head, junction, every direction change > 20°, then fill the
gaps at 30 m and let the remainder fall where it falls. Within-run length CV is **0.153** —
neither equal division (1.1 % of runs) nor max-then-remainder (8.0 %). The 30 m is roughly one
plot frontage: median plot 600 m², 24.5 m side.

---

## 3. Do not copy — with the measured reason

| | |
|---|---|
| **Two diameters for 95 km** | Tier explains **100.0000 %** of diameter variance. OD160 = 61.5 % of built length, below the OD200 minimum G203-p22 Tab 6 sets for a lateral or main |
| **Sizing a tier, not a flow** | 80.2× load spread inside one bore; 39.1 % of OD160 reaches carry more than the smallest OD200 |
| **The sizing itself** | 238 reaches fail at saturation — **trunk 63.5 %, sub-main 45.3 %**; worst 7.9× over |
| **Sub-mains flatter than their laterals** | 71.7 % of 60 lateral→sub-main pairs get flatter downstream. **Not a τ problem** — the flat sub-main has the *higher* tractive stress. It is pure capacity: `DIA_OUT` never steps up |
| **Shallow cover** | **43.0 % of levelled length below 1.30 m** at the shallow end; 1.8 % below the 0.50 m protected floor. Measure at `min(COVER_US, COVER_DS)` — a reach-mean check misses 153 reaches |
| **Under-graded trunk** | 31.1 % of trunk length below the Table 11 DN200 floor. There is **no "pinned at the minimum" habit to copy** |
| **Pipe inside plots** | 7.52 % (7.18 km) against a 3.04 % road-corridor null — **2.5× worse than simply following the mapped roads** |
| **A station rate per km** | One station in 95.45 km, but that is one alluvial fan draining one way. Extrapolating it across 531 km² would licence a design that under-pumps the west |
| **Presenting any of this to NWS as their design practice** | Their own unbuilt SUREKHA rows use **twelve** diameters. This is the 2006 scheme only |

**Two method rules that came out of the study and bind the routing:**

- **No steep-ground penalty in the W12 routing objective, and no as-built authority for one.**
  The apparent 9× steep-ground avoidance was an artefact of comparing against all ground.
  Against its own road corridor the built pipe sits on **steeper** ground (0.87×).
- **Grade against the DEM by along-reach regression, never two-point sampling.** Signal-to-noise
  below 0.5 at reach length; fitted per-point vertical error σ_z ≈ 0.27–0.39 m. Neither the DEM
  nor the 2006 survey is ground truth — the survey has *more* gradient variance than the raster.

---

## 4. Corrections to our own live documents

Project rule 12 keeps a superseded number as the record — **mark, do not delete.**

| Where | Was | Is |
|---|---|---|
| `W11b/docs/AS_BUILT_TARGETS.md:119` | "87.69 %, 520 of 582" | wrong twice; use **73.2 % on 272 exits**, banded 60–78 % |
| `W11b/docs/AS_BUILT_TARGETS.md:145` | steep-ground refutation | it was tested on flood-hazard class, not ground steepness. **They do go steeper on steep ground** |
| `HIERARCHY_RULES.md` §10, quoted into `README.md` | "110 pipes over capacity today" | **93 over capacity / 28 surcharged** — and the old figure used the retired one-property-per-plot basis |
| same | "686 properties on the worst OD160" | **1,401 saturated / 538 today** |
| `W11a_BUILD_BRIEF.md`, `contract.py` | "5,963 properties commissioned" | does not reproduce. Measured: **4,876 saturated / 3,645 live accounts** at 60 m |
| several | "60.8 km commissioned" | 60.753 km reproduces, but from our own documents — **no external commissioning record exists** |
| `08_DESIGN_PHILOSOPHY.md` | infiltration at 10 % of WW flow | **10 % is the EXISTING-network allowance (G201-p72). A new network is 720 L/d per km.** The swap moves the capacity gate's own output by 11.7 % |

---

## 5. Named gaps — nobody may assume these were covered

1. **Package 5A-1 entirely** — 33.78 % of the built network. No diameter, level, material or
   tier. It is also the pumped catchment, so the depth-versus-pumping question is unanswerable
   on exactly the ground where it matters.
2. **The rising main's diameter, material and class.** Honest bracket from friction and the
   2.5 m/s cap (G203-p50, *not* the 3.0 m/s gravity max): **ID ~205–375 mm = DN250–DN400.**
3. **The trunk's internal bore.** `IN_DIAMETE = 0` on all 145 rows. Say "most of the trunk is at
   or past capacity at saturation on any plausible bore" — **never a count**.
4. **Load allocation.** Only 7.40 % of the plot layer matched within 60 m. **Publish the radius
   with every property figure, always.**
5. **Whether the built network runs in a road reserve.** 32 % of chambers are more than 25 m from
   any mapped centreline. Report "3 m clear of the plot boundary", never "in the road reserve".
6. **Whether 90° branch inlets are a drafting rule or the street grid.** Untestable here.

**Data requests to NWS, in value order:** 5A-1's as-built pipe schedule **and its tier labels** ·
the rising main's diameter, material and class · the trunk's internal bore.
