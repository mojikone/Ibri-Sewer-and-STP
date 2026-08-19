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
| `StrCls` | 100 % | 01 National 270 · 02 Arterial 163 · 04 Distributor 329 · 05 Access 8,480 (no 03) | primary hierarchy — fully populated, so the reliable one |
| `TYPE` | 48 % | 1 → 340 · 2 → 84 · 3 → 42 · 4 → 3,972 | "the important rows" [U] — mapping to be confirmed |
| `Category` | 43 % | 1 → 2,172 · 2 → 1,197 · 3 → 604 | Category 1 includes dual carriageways but is **not** a safe exclusion proxy [U] |
| `STATUS` | 100 % | New 4,359 · Existing 2,839 · Modified 2,044 | affects whether a corridor can be built on today |
| `Name_Engli` | 12 % | 34 named routes | reporting only |

**Caveats to handle at load:**

- The `.prj` carries a **custom UTM 40N WKT (WGS84 datum), not an EPSG:32640 tag** — assign and
  verify the CRS explicitly rather than trusting the file. [R]
- `SHAPE_Leng` exists, but lengths still come from geometry (the previous layer's `Lenght` was all
  zeros). [R]
- 4,804 features have no `TYPE`; a rule keyed on `TYPE` alone silently ignores half the layer — so
  `StrCls` leads and `TYPE` refines. [R]

**Confirmation needed (blocks B2):** which of `StrCls 01/02` (433 features) or `TYPE 1/2/3` (466
features) is the authoritative "cannot open" set. They are similar in size and are probably the
same roads coded twice.

---

## B. Corridor treatment (stage: `RoadTreatment`)

| # | Rule | Source |
|---|---|---|
| B1 | **Roundabouts carry no sewer.** A roundabout needs no collection; the ring is excluded and its approach legs terminate at it. | [U] |
| B2 | **Dual carriageways and their links/ramps are excluded as pipe corridors** — they cannot be opened. Detect as two parallel lines (geometric) **and** by hierarchy field; remove the pair *and* the connectors feeding it. | [U] |
| B3 | **Crossings remain allowed.** Excluded roads may still be crossed (trenchless, G1-p85). Exclusion is longitudinal only — otherwise districts disconnect. | [U] |
| B4 | **Elevated intersections must not generate SLS.** Grade-separated points sit high and currently drive false deep-pocket flags; B2 should remove them — verify after implementation. | [U] |
| B5 | **A straight street between two intersections is ONE polyline.** Dissolve only at degree-2 nodes; intersections always break. (Already implemented; keep.) | [U] |
| B6 | **Head chambers start at the house gate, not the street end.** A street runs its full length, but the network starts where the first served property fronts it — trim each branch head to that gate. | [U] |

### B7 — chambers at bends

Umesh is **not** to be consulted; these numbers stand until you supply others. [U] [C]

| Geometry | Chambers | Basis |
|---|---|---|
| ≤ 5° at a point | none — joint deflection absorbs it | [C] |
| 5°–45° at a point (**sharp bend**) | **one** chamber at the bend | [U] |
| Sweeping curve, total turn > 45° (**wide bend**) | **two or three** chambers, breaking the curve into chords | [U] |
| Any case | inlet must meet the outlet at **≥ 90°** | [G] G203-p30, verbatim "shall" |

What decides two versus three: insert chambers so each chord's **offset from the road centreline
≤ 0.30 m** and each chamber's deflection ≤ 22.5°. `ROAD_CHORD_DEV_M` already exists in
`criteria.py` but is currently dead — this activates it. [R] [C]

Worth recording: the governing constraint is **maintenance access (rodding, jetting, CCTV) and
staying inside the trench**, not pipe flexibility. Corrugated HDPE bends further than the cleaning
equipment can negotiate.

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

**Open question:** large plots (up to 45,000 m² in the test area) currently get one connection each.
Institutional and industrial plots realistically need more. Your call. [C]

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
| **263 inlets under 90°** (audit C4) | ≥90° becomes a placement constraint at bends (B7), not just an after-the-fact check |
| **SLS pockets** | B4 removes elevated-intersection false positives |
| **Chamber count 1,655** | B6 removes chambers on unserved street ends; B2 removes dual-carriageway corridors entirely |
| **Network length 89.5 km** | drops by the dual-carriageway length plus untrimmed street heads |
| **Load per chamber** | C3 re-assigns plots by frontage, so flows redistribute between reaches |

Nothing here touches the **hydraulic** basis — Colebrook-White, Table 11, d/D, velocity, cover,
drops and the τ assumption are unchanged.

---

## F. Still open / awaiting input

| Item | Owner | Note |
|---|---|---|
| `StrCls` vs `TYPE` as the authoritative exclusion field | user | blocks B2 |
| Wadi layer for the no-chamber-in-wadi rule | user | parked 2026-08-19; 420 pipes currently cross mapped streams |
| Bend chamber counts if another standard applies | user | Umesh not to be consulted [U] |
| Multiple connections for large plots | user | section C open question |
| τ design value [GAP-9] | NWS | 1,124 pipes exposed if τ = 2 Pa |
| Occupancy / properties per plot [GAP-5] | NWS | load basis |
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
