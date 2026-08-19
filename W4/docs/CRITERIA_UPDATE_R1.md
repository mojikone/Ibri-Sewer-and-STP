# W4 — Criteria & Constraints Update R1 (pending implementation)

**Status: SPECIFICATION ONLY — nothing here is implemented yet.** It consolidates every change
agreed or discovered between 2026-08-18 and 2026-08-19, so the pipeline can be updated in one pass
instead of piecemeal. Each item carries its source and the stage it lands in.

Source tags: **[U]** user instruction · **[G]** PAM-GUD clause · **[R]** review/analysis finding ·
**[C]** my proposal awaiting your call.

---

## A. Input data — new road layer

**New source (supersedes `W1/shp/roads_study.shp` for corridor derivation):**
`Hydraulic/SHP/Road centerline 2/Road_Centercline.shp` — 9,242 features. [U]

| Field | Coverage | Values | Use |
|---|---|---|---|
| `StrCls` | 100 % | 01 National 270 · 02 Arterial 163 · 04 Distributor 329 · 05 Access 8,480 (no 03) | **AUTHORITATIVE hierarchy field — decided 2026-08-19 [U]** |
| `TYPE` | 48 % | 1 → 340 · 2 → 84 · 3 → 42 · 4 → 3,972 | superseded by `StrCls`; keep as a cross-check only |
| `Category` | 43 % | 1 → 2,172 · 2 → 1,197 · 3 → 604 | Category 1 includes dual carriageways but is **not** a safe exclusion proxy [U] |
| `STATUS` | 100 % | New 4,359 · Existing 2,839 · Modified 2,044 | **IGNORED — decided 2026-08-19 [U]** |
| `dual` **(new, added by user 2026-08-19)** | 100 % | 0 → 8,909 · **1 → 289** (146.9 km) · **2 → 44** (4.9 km) | **THE exclusion field.** 1 = dual carriageway, 2 = two-lane, one side only [U] |
| `Name_Engli` | 12 % | 34 named routes | reporting only |

**Caveats to handle at load:**

- The `.prj` carries a custom UTM 40N WKT rather than an EPSG code. **The CRS is EPSG:32640
  (WGS 84 / UTM 40N) — confirmed 2026-08-19 [U];** assign it explicitly on load. [R]
- `SHAPE_Leng` exists, but lengths still come from geometry (the previous layer's `Lenght` was all
  zeros). [R]
- 4,804 features have no `TYPE`; a rule keyed on `TYPE` alone silently ignores half the layer — so
  `StrCls` leads and `TYPE` refines. [R]

**Resolved 2026-08-19 [U]:** CRS is EPSG:32640, `STATUS` ignored, `StrCls` is the authoritative
*hierarchy* field — but the **`dual` field, not `StrCls`, drives exclusion.** That distinction
matters: cross-tabulating the two shows **95 National and 55 Arterial roads carry `dual = 0`**, so
excluding by class (my earlier option A) would have wrongly removed 150 single-carriageway roads,
while `dual = 1` also catches 6 Distributors that no class rule would have found. `StrCls` stays
useful for corridor preference/weighting, not for exclusion. [R]

Geometry check on the new field: **79 % of `dual = 1` and 77 % of `dual = 2` features have a
parallel twin within 3–45 m** (the remainder are end stubs shorter than the test window), which
confirms both are digitised as line pairs and makes the one-side rule implementable. [R]

---

## B. Corridor treatment (stage: `RoadTreatment`)

| # | Rule | Source |
|---|---|---|
| B1 | **Roundabouts carry no sewer.** A roundabout needs no collection; the ring is excluded and its approach legs terminate at it. | [U] |
| B2 | **`dual = 1` → no pipe of any kind, trunk included** (289 features, 146.9 km). Both lines of the pair are removed, along with their links and ramps. | [U] |
| B2b | **`dual = 2` → usable, but ONE side only** (44 features, 4.9 km, all Distributor). The pair is reduced to a single line and the sewer stays on that side for the whole corridor — never both, never alternating between sides. Plots on the far side connect by a direct link at the road end. | [U] |
| B3 | **Crossing is allowed only as a short perpendicular pipe**, where necessary (trenchless, G1-p85). No longitudinal run, no diagonal crossing, no chamber on the carriageway. | [U] |
| B4 | **Elevated intersections must not generate SLS.** Grade-separated points sit high and currently drive false deep-pocket flags; B2 should remove them — verify after implementation. | [U] |
| B4b | **Traffic-geometry links are not sewer corridors** (2026-08-19). Turning fillets, corner splays, slip roads and the diagonal/curved links between two parallel carriageways exist for vehicle movement; the sewer joins at a **point**. Following them adds chambers at every curve break, serves no frontage, and produces the acute inlet angles behind audit C4. See B9 for the test. | [U] |
| B5 | **A straight street between two intersections is ONE polyline.** Dissolve only at degree-2 nodes; intersections always break. (Already implemented; keep.) | [U] |
| B6 | **Head chambers start at the house gate, not the street end.** A street runs its full length, but the network starts where the first served property fronts it — trim each branch head to that gate. | [U] |

### B9 — identifying a traffic link (so it can be dropped)

Deliberately **not** based on road class — a link can be any class. A corridor segment is a link,
and is removed, when **all four** hold: [C]

1. **no frontage** — no loaded plot within the frontage distance (40 m) of it;
2. **both ends are attached** — degree >= 3 at each end, so it is not a cul-de-sac or a street head;
3. **redundant** — after removing it, its two endpoints remain connected through the corridor
   network with a detour no greater than **3x its own length**;
4. **it looks like a link** — either short (<= 120 m) or strongly curved (total turn >= 45 deg).

Test 3 is what makes this safe: a link that is the *only* connection between two areas fails it and
is kept, so nothing can be stranded. Everything removed is written to the corridor layer with
`EXCL_RSN = 'traffic-link'` so it is reviewable in QGIS rather than silently gone. [C]

Consequence to expect: where a side road meets a main road through a splay, the sewer will connect
by a straight run to the junction node instead of sweeping around the fillet — fewer chambers, and
the inlet arrives closer to the 90 deg the guideline requires. Corridors must be re-dissolved (B5)
after link removal so the street returns to one polyline. [C]

### B7 — chambers at bends

Umesh is **not** to be consulted; these numbers stand until you supply others. [U] [C]

| Geometry | Chambers | Basis |
|---|---|---|
| ≤ 5° at a point | none — joint deflection absorbs it | [C] |
| 5°–45° at a point (**sharp bend**) | **one** chamber at the bend | [U] |
| Sweeping curve, total turn > 45° (**wide bend**) | **two or three** chambers, breaking the curve into chords | [U] |
| Any case | inlet must meet the outlet at **≥ 90°** | [G] G203-p30, verbatim "shall" |

**Small-radius bends — one chamber at the corner point (2026-08-19) [U].** Rather than following
a tight curve, run straight to the intersection of the two tangents and turn there, **provided that
corner point lies outside every plot boundary by at least 2 m** (it must sit in the road reserve).
If the corner falls inside a plot or within 2 m of one, the curve must be followed instead with
2 chambers (3 only when the bend is wide and long). Cap is **3 chambers per bend**. [U]

What decides two versus three: insert chambers so each chord's **offset from the road centreline
≤ 0.30 m** and each chamber's deflection ≤ 22.5°. `ROAD_CHORD_DEV_M` already exists in
`criteria.py` but is currently dead — this activates it. [R] [C]

Worth recording: the governing constraint is **maintenance access (rodding, jetting, CCTV) and
staying inside the trench**, not pipe flexibility. Corrugated HDPE bends further than the cleaning
equipment can negotiate.

---

## B8. Wadi / flood hazard (new input, 2026-08-19)

**Source:** `Data/04 Lekhuwair/Hazard_T50y.tif` — the **50-year** hazard grid. EPSG:32640, 3 m
cells, 68,000 x 58,097, float32, nodata -9999. Covers the test boundary in full. [U] [R]

| Classes | Treatment |
|---|---|
| **4, 5, 6** | **wadi crossing** — G203-p30-31 forbids pipelines and chambers here; crossings only, with DI over the crossing +15 m each side, anti-flotation check and 2.0 m cover (G1-p85-86) |
| 1, 2, 3 | safe, unless revised later [U] |
| nodata (-9999) | **see F — meaning to confirm** |

**Exposure of the current (R1) design, measured 2026-08-19:** [R]

- **101 of 1,655 chambers (6.1 %)** sit in hazard 4–6 — 33 in class 4, 54 in class 5, 14 in class 6.
- **5.65 km of 89.5 km (6.3 %)** of network crosses hazard 4–6.
- 1,142 chambers (69 %) fall on nodata cells.

This replaces the earlier stream-line proxy (420 pipes crossing mapped drainage lines), which
overstated the problem badly — the hazard grid is the defensible basis.

---

## B10. Load basis — electricity subscriber accounts (new input, 2026-08-19)

**Source:** `Data/Received/09-RECEIVED/NAMA/IBRI ELE ACCOUNTS.kmz` — **33,970 accounts**, each
carrying a TARIFF and X/Y already in EPSG:32640. Parsed by `W4/py/analysis_ele_accounts.py` to
`W4/shp/ELE_accounts.shp`; full tables in `W4/analysis/ele_accounts.md`. [U] [R]

**Each account is a property.** A plot with 3 accounts has 3 properties, so `PROPS_PER_PLOT`
becomes **counted, not assumed** — this is the first real evidence against GAP-5. [U]

| Category | Accounts | Load treatment |
|---|---|---|
| domestic (Primary +/- subsidy) | 16,244 | per-capita x OR |
| domestic additional | 6,344 | counts as a property — see the validation below |
| commercial | 9,392 | non-domestic, Tier B driver still needed |
| government | 967 | non-domestic, Tier B driver still needed |
| agricultural (tariff) | 523 | TE customer, no sewage load |
| CRT / industrial | 500 | large consumers, case by case |

**Occupancy: OR = 5 (decided 2026-08-19 [U])**, replacing the 6.0 fallback.

**Validation that settles the "additional account" question [R]:** counting primary accounts only
gives 1.18 properties/plot -> **5.90 persons per plot at OR 5**; counting primary + additional
gives 1.46 -> **7.28 persons per plot**. The independent NCSI-derived figure from W3/A8 is
**~7.0 persons per built plot**. So additional accounts are separate dwellings and **must** be
counted; primary-only would under-predict the load by about 19 %.

**Load model becomes land-use based, not blanket per-capita [U].** Domestic load = counted
domestic properties x OR x per-capita rate; non-domestic identified by tariff instead of by the
22 %/14 % ratios. Honest limit: GUD-201 Tab 12 unit rates are keyed to floor area, pupils, beds and
employees, which subscriber counts do not provide — so this reaches **Tier B for domestic and
identifies non-domestic properly, but non-domestic still needs its own driver** before it is fully
Tier B compliant. [G] [R]

### Two findings that need your ruling

1. **Only 54.9 % of "built" plots carry an electricity account** (9,859 of 17,961). Either the W3
   imagery classifier over-called built, or the account layer is incomplete. This is the first
   independent check on that classification and it disagrees materially. [R]
2. **1,947 CLASS=A farm plots carry domestic accounts** (3,366 accounts). Doctrine 2.1 says farms
   carry no sewage load because they are TE customers — but a farm with houses on it produces
   sewage. The doctrine may need narrowing to "the agricultural *use* carries no load, the
   dwellings on it do". [R]

---

## C. House connections — the tertiary layer (stage: `ConnectabilityStage`)

**The flaw being fixed:** connection points sit at plot centroids *inside* plots, and lines run
diagonally from centroid to a distant chamber, crossing blocks and other plots. Sewers do not do
that. [U]

| # | Rule | Source |
|---|---|---|
| C1 | **Connection point = frontage projection** — the perpendicular projection of the plot onto the corridor it fronts, never the centroid. | [U] |
| C2 | **The connection is a short perpendicular spur** from the frontage to the pipe. Schematic geometry is acceptable. | [U] |
| C3 | **Load assignment follows frontage**, not straight-line distance: a plot loads the reach it actually fronts, not the nearest chamber across a block. | [U] |
| C4 | **Rider sewer runs along the frontage** in the public ROW, collecting **up to 3 HCC** — G203: *"Several HCC (usually up to 3) may be connected together by one or several Rider Sewers within the public ROW."* | [G] [U] |
| C5 | **A lone house connects directly by a lateral sewer** — no rider. | [U] |
| C6 | **Stub-outs at empty/planned plots**: capped connection at the frontage, sized for saturation flow, DN200 minimum governing. (Doctrine §2.3 — agreed earlier, never built into the tertiary layer.) | [U] [G] |
| C7 | **Elevation checked against the pipe invert interpolated at the connection chainage**, not the downstream chamber invert. A plot near the upstream end of a 90 m reach is otherwise checked against an invert up to ~0.5 m too low, which flatters the result. | [R] |
| C8 | **Gravity viability is the only hydraulic test at concept** — plot outlet level versus pipe invert. No tertiary sizing. | [U] |
| C9 | **Separate layers in every output** (SHP and DXF): house connections and riders must not sit in the mains layer, so SewerGEMS never imports tertiary as conduits and CAD can switch them off. | [U] |

**Resolved by B10 [U]:** connection count follows the counted accounts. In the test boundary
**352 of 1,331 plots with accounts (26.4 %) carry 2 or more**, so roughly a quarter of plots need
more than one connection; the maximum observed on a single plot is 51 accounts (a compound or
apartment block).

---

## D. Doctrine changes — what this supersedes

1. **CLAUDE.md working rule 7 is superseded for sewer corridors.** It reads *"Dual carriageways are
   two parallel polylines — collapse to a single routing corridor."* The new rule is **exclude**,
   not collapse, because the carriageway cannot be opened. Rule 7 may still hold for trunk-routing
   studies (W2), so the wording needs narrowing rather than deletion. [U]
2. **Main-road handling moves from derived to data-driven.** The betweenness-derived classification
   in `RoadTreatment.classify_main_roads` is replaced by the hierarchy field, and the flag stops
   being advisory — it will actually exclude corridors. [U] [R]
3. **Corridor source layer changes.** Every figure in the current report (98.7 km of roads, chamber
   counts, network length) is re-based by this.

---

## E. Consequences — expect these results to move

| Current result | Why it changes |
|---|---|
| **152 house connections over 50 m, longest 182 m** (audit D1) | largely an artefact of centroid-to-chamber measurement; frontage projection should collapse most to 5–25 m |
| **263 inlets under 90°** (audit C4) | two causes removed at once: ≥90° becomes a placement constraint at bends (B7), and the diagonal traffic links that produce acute arrivals are dropped (B4b/B9) |
| **SLS pockets** | B4 removes elevated-intersection false positives |
| **Chamber count 1,655** | B6 removes chambers on unserved street ends; B2 removes dual carriageways; **B9 removes chambers on turning fillets and slip roads** — the stated goal is chambers only where necessary |
| **Network length 89.5 km** | drops by the dual-carriageway length plus untrimmed street heads |
| **Load per chamber** | C3 re-assigns plots by frontage, so flows redistribute between reaches |

Nothing here touches the **hydraulic** basis — Colebrook-White, Table 11, d/D, velocity, cover,
drops and the τ assumption are unchanged.

---

## F. Still open / awaiting input

| Item | Owner | Note |
|---|---|---|
| ~~Hazard nodata meaning~~ | — | **RESOLVED 2026-08-19 [U]: nodata = dry** |
| ~~Which side to keep for `dual = 2`~~ | — | **RESOLVED 2026-08-19 [U]: side with more fronting plots, tie-broken by lower ground, held for the whole corridor** |
| ~~Wadi layer~~ | — | **RESOLVED 2026-08-19** — 50-year hazard grid supplied, see B8 |
| **Built-plot classification disagrees with accounts** — 45 % of built plots have no electricity | user | B10 finding 1 |
| **Farms with dwellings** — do they carry sewage load after all? | user | B10 finding 2 |
| Bend chamber counts if another standard applies | user | Umesh not to be consulted [U] |
| ~~Multiple connections for large plots~~ | — | **RESOLVED 2026-08-19 — driven by counted accounts (B10)** |
| τ design value [GAP-9] | NWS | 1,124 pipes exposed if τ = 2 Pa |
| Occupancy [GAP-5] | — | **OR = 5 decided [U]**; properties per plot now COUNTED from accounts (B10) |
| PVC-U wall class (SDR) per PAM-SPC-207 | NWS | true bore for capacity |

---

## G. Implementation order when you say go

1. `criteria.py` — new constants: exclusion classes, bend bands, chord tolerance, gate offset.
2. `prep.py` — load the new layer, assign CRS explicitly, keep geometry-derived lengths.
3. `RoadTreatment` — B1, B2, B5, B6 plus hierarchy-driven exclusion; the corridor layer gains
   `STR_CLS`, `TYPE`, `EXCL_RSN` so every exclusion is reviewable in QGIS.
4. `ChamberPlacer` — B7 bend bands and chord control.
5. `ConnectabilityStage` — C1–C8, rewritten around frontage projection.
6. Exports — C9 separate tertiary layers in SHP and DXF; SewerGEMS schema unchanged.
7. Audit — re-point D1 at frontage distance; add "no corridor on an excluded road" and "every head
   starts at a served frontage".
8. Re-run, compare against the R1 baseline, and report every metric that moved, with its reason.
