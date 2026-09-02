# Tertiary rejections and wadi chambers — decomposition, and what to do about each

**Analysis only. No `.py` file was touched. Every code block below is a proposal, marked
with the file and the function it replaces.** Measured 2026-09-02 against the published
layers `W11a/shp/W11a.gpkg` (`nodes` 50,033 · `reaches` 49,274 · `connections` 45,232),
`W10/shp/W10_plot_loads.gpkg` (64,071) and `Data/04 Lekhuwair/Hazard_T50y.tif`.

---

## 0. Both headlines in the brief are wrong, in opposite directions

| | Brief says | Measured | |
|---|---|---|---|
| **Defect 1** | "the 45 m tertiary limit rejects 30 % of the load" | 30.14 % is rejected, but only **8.59 %** of it is the 45 m rule | the *rule* is over-blamed |
| **Defect 2** | "1,051 chambers on wadi ground" | **2,354** on the published `nodes` layer | the *defect* is 2.2× bigger |

**Defect 1 — the second half of the brief's hypothesis is also wrong.** The brief expected the
"30 %" to shrink once no-load plots came out. It does not move at all: the 7,639 no-load plots
carry **0.0 m³/d** by construction, so removing them changes the plot count by 31 % and the load
by **nothing**. 22,513 m³/d really is 30.1 % of 74,701 m³/d. What is wrong is the *attribution* —
the largest single group is not the 45 m rule at all, it is a **level test run against placeholder
levels**, and it should never have been run.

**Defect 2 — the 1,051 is a stale number from the wrong stage.** It is
`manifest_s4.json → "chambers_on_wadi_measured": 1051`, taken at stage 4 *before stage 5 minted
the chamber set*. Stage 5's own CSV (`run/s5_wadi_chambers.csv`) holds 2,834 rows / **2,356
unique XY**, and re-sampling the published `nodes` layer gives **2,354**. Quote the published
layer, not stage 4.

**And a coverage statement is mandatory beside every wadi number** (philosophy §3, "the untested
fraction is published beside every wadi result). Of 50,033 nodes, **24,132 (48.2 %) fall on valid
hazard-grid cells and 25,901 (51.8 %) do not.** The 2,354 is *2,354 of the 24,132 that could be
tested* — 9.8 % of the tested half. The other half is unknown, not clean.

---

# DEFECT 1 — the tertiary rejections

## 1a. The decomposition asked for

Total published plot load **74,701.2 m³/d over 64,071 plots**. Stage 5b's own funnel:

| | plots | m³/d | % of 74,701 |
|---|---:|---:|---:|
| Outside the project boundary | 44 | 25.9 | 0.03 |
| **No wastewater load** (`AGRI_NO_HSE` 4,235 · `SERVICE_PCL` 3,349 · `INDUSTRIAL` 55) | **7,639** | **0.0** | **0.00** |
| → load units entering the stage | 56,388 | 74,675.3 | 99.97 |

And the rejections, re-grouped from the free-text `WHY` in `run/s5b_unassigned.csv`:

| Rejection family | plots | m³/d | % of load | What it actually is |
|---|---:|---:|---:|---|
| No wastewater load | 7,639 | 0.0 | 0.00 | **not a defect** — land use with no flow |
| Outside the boundary | 44 | 25.9 | 0.03 | not a defect |
| **`cannot drain to N…`** | **5,715** | **7,194.2** | **9.63** | a level test against **placeholder levels** — see §1b |
| **No carrier within 47.5 m** | **5,289** | **6,715.4** | **8.99** | **a corridor / hierarchy gap**, not a tertiary one |
| **Leg > 45 m** | **4,633** | **6,418.1** | **8.59** | **the only group the 45 m rule owns** |
| Corridor through the plot, gate on the chamber | 1,234 | 2,159.6 | 2.89 | a geometry-collapse artefact — see §1e |
| **Total rejected** | **24,554** | **22,513.2** | **30.14** | |

So: **the 45 m rule owns 6,418 m³/d, 8.6 % of the load — not 30 %.** Three-quarters of the
rejection is three other problems wearing the tertiary stage's label, because the tertiary stage
is the first stage that ever tests them.

## 1b. The single largest group is a test that should not have run

`nodes.DEPTH_M` on the published layer: **min = max = 1.600 m on all 50,033 chambers**;
`COVER_M` is 1.300 on all of them; `INV_M − (GRD_M − 1.6) = 0.0` exactly, everywhere.
Stage 5 says so itself (`s5_chambers.py`, manifest note):

> *"levels and flows are stage 5 SEEDS, not design values: INV_M/DEPTH_M/COVER_M at the
> shallowest legal invert"*

Stage 6 (levels) has not run — `W11a/shp/W11a_s6.gpkg` does not exist. But stage 5b decides the
levels are real on this test alone (`s5b_tertiary.py:598`):

```python
levels_known = bool(pd.to_numeric(nodes["INV_M"], errors="coerce").notna().any())
```

A *seeded, non-null* invert passes. So 5,715 plots (7,194 m³/d, the biggest group in the table)
were failed against a chamber invert that is a constant 1.6 m below the street, everywhere, by
construction. That is not a design result. Philosophy §8: *"a check that cannot run is a failure"*
— but a check run on placeholder inputs and reported as a design failure is worse, because it
produces a number that looks like evidence.

**How small the failure actually is.** The shortfall — how much lower the chamber invert would
have to sit — is tiny:

| shortfall | plots | m³/d | receiving-chamber depth after deepening |
|---|---:|---:|---|
| ≤ 0.10 m | 1,960 | 2,479.8 | ≤ 1.70 m |
| ≤ 0.20 m | 3,089 | 3,899.7 | ≤ 1.80 m |
| ≤ 0.30 m | 3,659 | 4,600.9 | ≤ 1.90 m |
| ≤ 0.50 m | 4,229 | 5,334.4 | ≤ 2.10 m |
| ≤ 1.00 m | 4,644 | 5,864.5 | ≤ 2.60 m |

p50 = 0.15 m, p90 = 0.63 m, max 8.79 m. **3,934 distinct chambers are implicated; 2,870 of them
need ≤ 0.30 m and 3,376 need ≤ 0.50 m of extra depth.** Nothing here goes anywhere near H4's
12 m cap. This is a levelling decision, not a servicing decision.

**The engineering point, and it is a doctrine point, not a code point:** a chamber invert is a
*designed* variable and the tertiary connection is one of the constraints that sets it. Laying
every chamber at the shallowest legal invert (philosophy P6) and *then* asking whether the
frontage can reach it inverts the dependency. **The deepest fronting connection is an input to
the chamber invert.** Stage 6 must take the tertiary arrivals as a floor.

## 1c. The 45 m rule, checked against the source — and it is narrower than the code applies it

Read back from `Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf` today:

**G203-p22 Table 6** — the 45 m sits in the **Lateral Sewer** row and nowhere else:

> Rider Sewer, Property Connection Sewer\* | OD 160 mm (minimal) | Open Trench | PVC-U, HDPE
> **Lateral Sewer | OD 200 mm (minimal) Maximum Length 45 m** | Open Trench | PVC-U, HDPE, GRP

The Rider Sewer row carries **no length limit at all**.

**G203-p17 §3.2** — the ambiguous sentence the code chose to read conservatively:

> *"Rider Sewers and Lateral Sewers (maximum Length 45 m) are forming the Tertiary Sewage Network"*

**G203-p18, note under Table 4** — and this is the guideline's own remedy for an over-long run:

> *"The length of the PCS should not exceed 50 m in order to allow maintenance.
> **If necessary, a manhole will be added.**"*

**G203-p19 §3.4** — and its own permission for more than one connection on a big plot:

> *"Chambers are to be provided with stubs / plugged ports for the future connections … big plots
> might require more than one property connection."*

**G203-p17 §3.2** on sharing — the code already uses this, at its stated ceiling:

> *"Several HCC (**usually up to 3**) may be connected together by one or several Rider Sewers
> within the public ROW."*

Three conclusions, and I am **not** recommending we act on the first two:

1. **The looser reading is available and defensible** — cap the *lateral* at 45 m and leave the
   *rider* uncapped, exactly as Table 6 is written. The stage's own docstring already promises to
   report what that reading would recover. **Do not adopt it.** An uncapped OD160 rider at 1 % is
   bad engineering regardless of what the table omits, and NAMA operate this network for fifty
   years. If the project wants headroom, take it as a *stated project cap* (e.g. rider ≤ 45 m,
   lateral ≤ 45 m, so a chained path may reach 90 m) declared in `02` as a deviation with the
   Table 6 quote beside it — not as a silent re-reading.
2. **"Several HCC (usually up to 3)"** — "usually" is not "shall", so 4 or 5 HCC on one rider is
   inside the guideline's own wording. This buys almost nothing here (the binding constraint is
   geometry, not the chain length) and it is not worth the derogation.
3. **"If necessary, a manhole will be added" is the guideline's answer**, and it is the one I
   recommend — but only for the 647 plots that actually need it (§1d).

## 1d. What each genuine failure needs, and what it costs

**The largest fix costs nothing at all.** `Frontages.build` picks the **nearest carrier** and then
**the nearer of that one reach's two end chambers** — `tree.query_nearest(..., all_matches=False)`
followed by `to_us = st <= (L - st)`. It never looks at the other end of the same reach, and never
at a second carrier. Re-running the assignment over **every carrier within 47.5 m and both ends of
each** (380,236 candidate connections over 56,388 plots):

| | plots | m³/d | % of 74,701 |
|---|---:|---:|---:|
| Leg > 45 m under *nearest-only* | 4,633 | 6,418.1 | 8.59 |
| **Recovered by choosing the best candidate instead** | **3,986** | **5,622.5** | **7.53** |
| Still over 45 m to every candidate | 647 | 795.5 | 1.07 |

And on the level side, at the *same* seed levels, best-of-all cuts "no chamber in range drains"
from **5,715 / 7,194 m³/d to 1,048 / 1,364 m³/d**. Zero new chambers, zero new pipe, no rule change.

**After that change the residue is 5,936 plots / 7,510.9 m³/d (10.05 %)**, and it decomposes into
three problems that belong to three different stages:

| Residue | plots | m³/d | Whose problem | Fix | Cost |
|---|---:|---:|---|---|---|
| Carrier reach in range, **no chamber within a 45 m run** | 647 | 795.5 | stage 5 | a chamber at the gate — G203-p18's own *"a manhole will be added"* | **545 chambers** |
| **Corridor in range but no pipe laid in it** | 3,268 | 4,148.3 | **stage 4 (hierarchy)** | lay the lateral | 968 corridors, 255.8 km implicated |
| **No corridor within 47.5 m either** | 2,021 | 2,567.1 | **scope** (philosophy §8a) | another system, or a new corridor | client decision |

Notes that matter:

* The 647 have offset p50 = **44.7 m** — they are set well back from the carrier. A chamber at the
  gate leaves them a spur of ≤ 45 m, so it does clear the rule; but a 42 m private spur must run in
  a public reserve (G203-p17 §3.2 puts the HCC *"in the public right-of-way"*), and at concept scale
  we have not shown one exists. **Flag these 647, do not just build them.**
* The 545 chambers take the network from 50,033 to 50,578 — **28.8 → 29.1 chambers/km**, still well
  under NAMA's as-built **32.3/km**. There is headroom for ~6,100 chambers before we exceed the
  network they already maintain. Maintenance cost is not the binding argument here; the argument is
  that 545 is *targeted* rather than uniform.
* Of the 3,915 residue plots with a corridor in range, **2,447 front a corridor whose `CONFIDENCE`
  is `provisional`** — a platted reserve with nothing built on it (philosophy §4). They are
  servable, at provisional confidence, and must never be reported as existing.
* `corridors.USED` is **0 on all 25,122 rows**. Stage 2 writes it and no later stage writes back,
  so 494 km of corridor carrying no pipe cannot be distinguished from corridor deliberately not
  used. That is a provenance defect in its own right and it is why the 3,268 had to be found by
  re-measuring rather than by reading a field.

**Uniform spacing reduction is the wrong instrument.** Stage 5b's own `chamber_spacing_p90_m` =
26.3 m says that to clear the *90th-percentile* offset by spacing alone the mean spacing has to
come down from 34.7 m to 26.3 m: 1,737.5 km ÷ 26.3 m = **66,062 chambers, +16,029 on what is
designed**, taking density to 38.0/km — **past NAMA's as-built 32.3/km** — to buy 6,418 m³/d that
best-of-all selection recovers 88 % of for nothing. Reject it.

## 1e. One inconsistency worth fixing while we are here

The "corridor runs through the plot" rejection (1,234 plots, 2,159.6 m³/d) fires only when
**two** things coincide: offset ≈ 0 **and** the gate lands exactly on the chosen chamber
(`LineString(coords).length < 0.05`). Measured: **3,086 plots have offset < 0.005 m, and 2,055 of
them were accepted and published.** Only the 1,031 where the gate also hit the chamber were
refused. The message names it a right-of-way fault, which is a statement about the *offset* — so
either all 3,086 are a corridor fault or none are. Test the offset, not the collapsed geometry.

## 1f. Recommendation — Defect 1

**In priority order, and only the first is urgent:**

1. **Stop running the drain test against seeds.** One line. It removes 7,194 m³/d of phantom
   failure and it removes a number that would otherwise be quoted in a report.
2. **Choose the best chamber, not the nearest one.** Recovers 5,622 m³/d (7.5 % of project load)
   for no capital cost. This is the single highest-value change in the stage.
3. **Make the tertiary arrival a constraint on the chamber invert in stage 6**, not a test after
   it. Median 0.15 m, 2,870 chambers at ≤ 0.30 m.
4. **Add 545 chambers** for the 647 plots the geometry genuinely strands, per G203-p18's own
   *"a manhole will be added"* — and flag each with the right-of-way question.
5. **Hand 3,268 plots back to stage 4** (corridor exists, no pipe) and **2,021 to the scope
   decision** (no corridor at all, philosophy §8a).
6. **Do not** relax the 45 m rule. Do not add chambers uniformly. Do not raise the 3-HCC rider
   ceiling.

Projected end state after 1–4, on the geometry as it stands: load reaching a chamber goes from
**52,188 m³/d (69.9 %)** to about **67,190 m³/d (89.9 %)**, with the remaining 10.05 % named as a
corridor question (5.6 %), a scope question (3.4 %) and 545 chambers (1.1 %) rather than as a
tertiary failure. That figure assumes stage 6 lands the chamber inverts the §1b shortfalls need;
until stage 6 runs, the honest statement is **`CAN_DRAIN` is null and the level test has not been
performed** — not that 5,715 plots fail it.

## 1g. Exact code

### Change 1 — `W11a/py/s5b_tertiary.py`, line 598: do not mistake a seed for a level

```python
# BEFORE
        levels_known = bool(pd.to_numeric(nodes["INV_M"], errors="coerce").notna().any())
```

```python
# AFTER
        # A non-null INV_M is NOT a levelled network. Stage 5 seeds every chamber at the
        # shallowest legal invert and says so in its own manifest, and on the layer read on
        # 2026-09-02 all 50,033 nodes carry DEPTH_M = 1.600 m exactly. Solving the tertiary
        # against that constant and publishing the failures as "cannot drain" reports 5,715
        # plots (7,194 m3/d) that are an artefact of the seed. Philosophy sec 8: a check that
        # cannot run is a failure - it is NOT a design result with the same name.
        inv = pd.to_numeric(nodes["INV_M"], errors="coerce")
        dep = pd.to_numeric(nodes.get("DEPTH_M", pd.Series(index=nodes.index, dtype=float)),
                            errors="coerce")
        seeded = bool(dep.notna().any() and float(dep.std(skipna=True) or 0.0) < 1e-6)
        levels_known = bool(inv.notna().any()) and not seeded
        if seeded:
            levelled_note = (f"INV_M is present but DEPTH_M is constant at "
                             f"{float(dep.dropna().iloc[0]):.3f} m on {int(dep.notna().sum()):,} "
                             "nodes - these are stage 5 SEEDS, not levels. CAN_DRAIN is left "
                             "null and no plot is rejected on a level test. Re-run after stage 6.")
        else:
            levelled_note = ""
```

…and carry `levelled_note` onto `Inputs` beside `levelled_elsewhere`, so the manifest records
*why* `CAN_DRAIN` is null. `Tertiary._level_and_emit` already does the right thing when
`levels_known` is False: it declares the Tab 5 minimum, sets `CAN_DRAIN=None`, and appends
`"; LEVELS PENDING …"` to `WHY`. Nothing else changes.

### Change 2 — `W11a/py/s5b_tertiary.py`, `Frontages.build`: rank the candidates

```python
# BEFORE (the whole per-plot body of Frontages.build)
        for i, pg in zip(plots.index, plots.geometry.values):
            hit = tree.query_nearest(pg, max_distance=CARRIER_SEARCH_M,
                                     return_distance=False, all_matches=False)
            hit = np.atleast_1d(hit)
            if not hit.size:
                rejected[i] = (f"no {'/'.join(CARRIER_TIERS)} reach within "
                               f"{CARRIER_SEARCH_M:.1f} m of the plot boundary")
                continue
            j = int(hit[0])
            line = geoms[j]
            g_pt, p_pt = nearest_points(line, pg)
            gate = (g_pt.x, g_pt.y)
            pcc = (p_pt.x, p_pt.y)
            offset = math.hypot(gate[0] - pcc[0], gate[1] - pcc[1])
            hcc = _lerp(pcc, gate, min(HCC_OFFSET_M, offset))
            st = float(line.project(g_pt))
            L = float(line.length)
            to_us = st <= (L - st)
            out.append(Frontage(plot_i=i, reach_i=j, pcc=pcc, hcc=hcc, gate=gate,
                                station=st, offset=offset,
                                out_node=(us[j] if to_us else ds[j]),
                                d_along=(st if to_us else L - st), to_us=to_us))
```

```python
# AFTER
        # EVERY carrier within reach, and BOTH ends of each - not the nearest reach and its
        # nearer end. The old rule inspected exactly ONE of a plot's candidate chambers, and
        # measured on the published layers it stranded 4,633 plots (6,418 m3/d) over the 45 m
        # limit of which 3,986 (5,622 m3/d, 7.5 % of project load) have another chamber inside
        # the limit that it never looked at. Both ends of a reach are manholes, which is all
        # G203-p19 3.6 asks for, and a chamber upstream of the flow is still a chamber.
        #
        # RANKING, and it is the philosophy's order, not a solver's:
        #   1. it drains            - only tested when the levels are real (see levels_known);
        #                             at seed levels every candidate scores equal and the rule
        #                             falls through to the geometry, which is honest.
        #   2. shortest leg         - P6 (minimum depth) and the least OD160 in the ground.
        #   3. EDGE_UID, then node  - determinism, so two runs of the same layers agree.
        inv_of = {r.NODE_UID: float(r.INV_M) for r in self.inp.nodes.itertuples()
                  if pd.notna(getattr(r, "INV_M", None))} if self.inp.levels_known else {}
        edge_uid = self.carriers.EDGE_UID.astype(str).values
        for i, pg in zip(plots.index, plots.geometry.values):
            hits = np.atleast_1d(tree.query(pg, predicate="dwithin",
                                            distance=CARRIER_SEARCH_M))
            best: Optional[Tuple[Tuple, Frontage]] = None
            for j in hits:
                j = int(j)
                line = geoms[j]
                g_pt, p_pt = nearest_points(line, pg)
                gate = (g_pt.x, g_pt.y)
                pcc = (p_pt.x, p_pt.y)
                offset = math.hypot(gate[0] - pcc[0], gate[1] - pcc[1])
                if offset > CARRIER_SEARCH_M:          # dwithin tests the buffered box edge
                    continue
                hcc = _lerp(pcc, gate, min(HCC_OFFSET_M, offset))
                st = float(line.project(g_pt))
                L = float(line.length)
                spur = max(0.0, offset - HCC_OFFSET_M)
                for d_along, node, to_us in ((st, us[j], True), (L - st, ds[j], False)):
                    leg = spur + d_along
                    if leg > TERTIARY_MAX_LEN_M:       # G203-p22 Tab 6, Lateral Sewer
                        continue
                    # "does it drain" is a LEVEL question and is only asked when the levels
                    # are levels. `grd` is the terrain at the PCC, the same point the level
                    # solve uses, so the ranking and the solve cannot disagree.
                    drains = 0
                    if inv_of and node in inv_of:
                        grd = float(self.ground.at([pcc])[0])
                        if np.isfinite(grd):
                            inv_up = (grd - PCS_MIN_INV_DEPTH_M
                                      - PCS_MIN_SLOPE_PCT / 100.0 * min(HCC_OFFSET_M, offset))
                            drains = int((inv_up - inv_of[node])
                                         >= RIDER_MIN_SLOPE_PCT / 100.0 * leg)
                    key = (-drains, round(leg, 3), edge_uid[j], str(node))
                    if best is None or key < best[0]:
                        best = (key, Frontage(plot_i=i, reach_i=j, pcc=pcc, hcc=hcc,
                                              gate=gate, station=st, offset=offset,
                                              out_node=node, d_along=d_along, to_us=to_us))
            if best is None:
                rejected[i] = (f"no {'/'.join(CARRIER_TIERS)} reach within "
                               f"{CARRIER_SEARCH_M:.1f} m of the plot boundary, or none with a "
                               f"chamber inside the {TERTIARY_MAX_LEN_M:.0f} m tertiary run "
                               f"(G203-p22 Tab 6)")
                continue
            out.append(best[1])
```

Two supporting edits this needs:

* `Frontages.__init__` must take the terrain so the ranking can sample it — add
  `self.ground = Ground(inp.terrain)` beside the existing members (`Tertiary` already builds
  one; share it rather than opening the VRT twice).
* **Sample the terrain in one batch, not per candidate.** 380,236 candidates × one
  `rasterio.sample()` call each is minutes; collect the PCCs into a list on a first pass, call
  `self.ground.at(all_pccs)` once, then rank on a second pass. The per-candidate call is written
  inline above only to keep the ranking readable. (The measurement in §1d used the batched form
  and the whole thing ran in about 90 s.)
* The `reach_over` block in `Tertiary.run` still runs, but it will now only ever see the 647
  genuinely-stranded plots, because a candidate over 45 m is never emitted. Keep the block —
  `run/s5b_chamber_requests.csv` is exactly the deliverable stage 5 needs — and it drops from
  5,867 rows to about 647.

**Rider grouping caveat, and it is real.** `group_riders` buckets on
`(reach_i, out_node, to_us)`. Ranking each plot independently can split neighbours onto different
carriers and cost rider length. Measure `tertiary_km` before and after; if it rises materially,
re-rank inside `group_riders` on the majority choice of each street rather than per plot. I have
not measured that trade — it needs the stage re-run, which I did not do.

### Change 3 — `W11a/py/s5b_tertiary.py`, the degenerate test: test the offset, not the collapse

```python
# BEFORE
                if len(coords) < 2 or LineString(coords).length < 0.05:
```

```python
# AFTER   (with this module-level constant added beside HCC_OFFSET_M)
# Half the narrowest service reservation G203-p33 Tab 13 gives - DN200-500 is 2.0 m - so a
# plot boundary closer than this to the carrier CENTRELINE is inside the reserve and there is
# no right-of-way for a PCC or an HCC. A DERIVED value: the guideline gives the corridor
# width, not this offset. Declared here rather than assumed inside a geometry test.
ROW_MIN_OFFSET_M = 1.0

                # The fault is that the carrier has no right-of-way beside it, and that is a
                # statement about the OFFSET. Testing the collapsed geometry instead fires only
                # when the gate also happens to land on the chosen chamber: on the layers read
                # 2026-09-02, 3,086 plots have offset < 5 mm and 2,055 of them were published
                # anyway - the same fault accepted and refused in the same run.
                no_row = f.offset < ROW_MIN_OFFSET_M
                collapsed = len(coords) < 2 or LineString(coords).length < 0.05
                if no_row or collapsed:
```

…with the `why` string set from `no_row` / `collapsed` separately, so the corridor stage gets
"no right-of-way (offset 0.00 m, reserve is 2.0 m wide — G203-p33 Tab 13)" as a *corridor*
finding, and "gate coincides with the chamber" as a *chamber-selection* finding, which Change 2
already removes.

**Order the two changes and the count goes DOWN, not up.** Applied on its own, the honest offset
test would reject 3,866 plots (5,633 m³/d) instead of 1,234 — the same fault reported consistently.
Applied *after* Change 2, with the offset test as a candidate filter rather than a post-hoc
rejection, **only 30 plots have no candidate carrier with a 1.0 m offset.** So Change 2 must
carry the filter, not just the ranking — add to the candidate loop, before the leg test:

```python
                    if offset < ROW_MIN_OFFSET_M and n_row_ok:   # a ROW-clear carrier exists
                        continue                                  # G203-p17 3.2 / p33 Tab 13
```

with `n_row_ok` computed in a first pass over the same `hits`. A plot with *no* ROW-clear
candidate keeps its zero-offset carrier and is published with `CONFIDENCE` degraded and the
finding recorded — 30 plots, listable by name.

---

# DEFECT 2 — chambers on wadi ground

## 2a. The number, and the coverage statement that has to travel with it

| | count |
|---|---:|
| Nodes published | 50,033 |
| On a **valid** hazard cell (testable) | 24,132 (48.2 %) |
| On nodata / outside the grid (**UNTESTED**) | 25,901 (51.8 %) |
| **On wadi ground (`floor(class) ≥ 4`)** | **2,354** |
| — hazard class 4 / 5 / 6 | 543 / 1,455 / 356 |
| — tier: lateral / main / sub main / **trunk main** | 1,488 / 627 / 167 / **72** |
| — kind: chamber / head / junction / outfall | 1,721 / 308 / 212 / 113 |

**On the nodata trap the brief raises:** `Surface.is_wadi` (`s5_chambers.py:474`) and
`audit.r4` both use `np.isfinite(v) & (np.floor(v) >= 4)`. `np.isfinite(-9999.0)` is True, but
`np.floor(-9999) >= 4` is False, so nodata scores as **not wadi** — a silent PASS on 51.8 % of
the chamber set. The wadi *flag* is therefore correct; the *coverage* is not reported, and
philosophy §3 requires it to be. `audit.py` already knows this (its own docstring, line 574) and
publishes `no_data_reach`; `Surface.is_wadi` does not, and stage 5's manifest carries no untested
count at all.

**And R4 cannot run.** `run/s4_audit_readiness.csv` shows `R4,False,external.hazard` — the wadi
regression check is not wired to the grid, so nothing independently confirms any of this. That is
a blocking failure under philosophy §8 in its own right.

## 2b. The rule, read back from the source — it is not what H1a cites

**G203-p30 §4.4.1(i)(a)**, verbatim:

> *"**Wadis and Flood-Prone Areas**: Locating pipelines and associated chambers in wadis or areas
> subject to washout during heavy storms **must be avoided**."*

**G203-p33 §4.6.2**, verbatim:

> *"Locating pipelines and associated chambers in wadis and areas subject to washout during heavy
> storms **shall be avoided**."*

**G201-p86 §9.3**, verbatim — and this is the clause philosophy H1a item 2 cites:

> *"**No valve chambers or marker posts** shall be constructed in the wadi bed or on the
> embankments of the wadi and all valves and marker posts must be visible and fully accessible
> when the Wadi is in flood."*

**G201-p86 is about valve chambers and marker posts on a pressure crossing** — it sits between
the DI-pipe clause and the isolation/air-valve clause of §9.3, which is written for a force main.
It is absolute, and it does not mention manholes. The clause that *does* cover a gravity manhole
is G203-p30/p33, and its wording is **"must be avoided" / "shall be avoided"**, under a heading
the guideline itself calls *"Prohibited and Unsuitable Zones"*.

So H1a item 2 — *"No chamber on wadi ground or on the embankment, and none in the bed
(G201-p86)"* — is **stronger than its own citation supports**, and the citation is to the wrong
clause. This project has been bitten by exactly this before (the 3.0 vs 2.5 m/s rising main, and
`INLET_MIN_DEG` 85 vs 75). Two honest options:

* **Keep the absolute rule** (my recommendation) but **re-cite it to G203-p30 §4.4.1(i)(a) and
  G203-p33 §4.6.2**, and record that we are reading *"must be avoided"* as a prohibition — a
  deliberate, conservative project decision, not a quote. Keep G201-p86 where it belongs: valve
  chambers on a crossing.
* **Align to the source wording**, which would make a wadi chamber permissible with justification
  and a designed detail. That opens a derogation register of 2,354 entries and the client has to
  approve every one. Not worth it.

**A second, larger substitution nobody has declared.** `HAZARD_WADI_CLASSES = (4, 5, 6)` is not a
wadi delineation. `Data/04 Lekhuwair/Hazard_T100y.rasscript` shows the grid is the AR&R **flood
hazard** classification, keyed on human/vehicle/building safety:

```
ElseIf d > 4 Or v > 4 Or d*v > 4  -> 6  'H6 unsafe for people, vehicles & all buildings
ElseIf d > 2 Or v > 2 Or d*v > 1  -> 5  'H5 unsafe for people, vehicles & some buildings
ElseIf d > 1.2 Or d*v > 0.6       -> 4  'H4 unsafe for people & vehicle
```

Class 4 means **1.2 m of water in a 50-year event**, which is a floodplain statement, not a wadi
statement, and the hazard to a *buried* manhole is **scour**, which tracks velocity, not depth.
The 4/5/6 threshold is a defensible proxy for G203's *"areas subject to washout"* — but it is a
**project assumption and must be tagged as one in `02`**, with the rasscript quoted. It is not a
guideline number. Tag it alongside GAP-9.

## 2c. Where they are, and whether they can move

Two independent measurements, both on the published layers.

**Euclidean, to the nearest cell of known non-wadi ground** (400 m window per node):
p10 6.7 m · **p50 32.4 m** · p90 127.0 m · max 348.6 m. Only 371 of 2,354 have dry ground within
10 m.

**Along the pipe network** (Dijkstra across reach boundaries, hazard sampled every 1.5 m — half
the 3 m cell, `audit.WADI_SAMPLE_M`):

| distance to non-wadi ground along the network | chambers |
|---|---:|
| ≤ 5 m | 82 |
| ≤ 10 m | 166 |
| ≤ 20 m | 319 |
| ≤ 50 m | 791 |
| ≤ 100 m | 1,230 |
| **> 250 m — no non-wadi ground on the network at all** | **587** |

**This kills the nudge.** `_nudge_off_wadi` tries ±5, ±10, ±15, ±20 m. It can reach at most **319
of 2,354 (13.6 %)**, and it will not touch a junction, outlet, gate or start (633 of them) or a
Table 12 spacing chamber (319). The reason is not the search radius. It is that **the corridors run
down the wadis, not across them.**

**Contiguous on-wadi runs, measured along the corridor** (the unsplit route — the per-reach
`CROSS_ID` is useless for this, because stage 5 minted **one CROSS_ID per reach**, 3,037 of them,
so every "crossing" is capped at the 94 m maximum reach length by construction):

| contiguous run | runs | % | km |
|---|---:|---:|---:|
| ≤ 20 m | 1,270 | 52.3 | 9.4 |
| ≤ 50 m | 1,944 | 80.1 | 31.1 |
| ≤ 100 m | 2,205 | 90.9 | 49.9 |
| **> 100 m** | **222** | **9.1** | **50.5** |
| longest | | | **789 m** (`W11a-C010206`) |

**100.4 km of corridor / 82.3 km of laid pipe is on wadi ground**, and half of that length is in
runs over 100 m. Twelve runs exceed 480 m. Those are not crossings under H1a item 1 by any
tolerance.

Classifying each chamber by `SKEW = run length ÷ (2 × distance to dry ground)` — i.e. the run
against the shortest crossing available at that point:

| | chambers | reading |
|---|---:|---|
| SKEW ≤ 2 | 1,429 | genuinely inside a crossing |
| 2 < SKEW ≤ 4 | 460 | marginal / skewed crossing |
| **SKEW > 4** | **465** | **the corridor runs ALONG the wadi — H1 breach, not H1a** |

**The four resolution buckets:**

| | chambers | connections they carry | Resolution |
|---|---:|---:|---|
| 1 — slide ≤ 20 m along the route | **319** | 205 | stage 5 can fix in place |
| 2 — slide 20–50 m | **472** | 178 | stage 5 can fix, but it eats Table 12 headroom |
| 3 — > 50 m, crossing-like | **1,272** | 236 | **re-design the crossing** — shorten/skew the alignment, or trenchless (G203-p21/p35) |
| 4 — > 50 m, running along the wadi | **291** | 119 | **re-route the corridor (stage 2)** or another system (§8a) |

Total tertiary load discharging at a wadi chamber: **738 connections, 980.5 m³/d (1.3 %)**. Only
426 of the 2,354 carry any connection at all — so re-siting is overwhelmingly a *pipe* problem,
not a *servicing* problem. Of those 426, **319 would push an existing leg over 45 m** if moved to
the nearest non-wadi point; those must be re-sited *and* re-assigned in the same pass, which the
Change-2 ranking already handles.

## 2d. Exact code

### Change 4 — `W11a/py/s5_chambers.py`, `Surface.is_wadi`: return coverage, never assume it

```python
# BEFORE
    def is_wadi(self, xs, ys) -> np.ndarray:
        """audit.r4's own test, recomputed here so the design does not have to be told."""
        if self._h is None or not len(xs):
            return np.zeros(len(xs), dtype=bool)
        v = np.array([w[0] for w in self._h.sample(zip(xs, ys))], dtype=float)
        return np.isfinite(v) & (np.floor(v) >= min(C.HAZARD_WADI_CLASSES))
```

```python
# AFTER
    def wadi_and_cover(self, xs, ys) -> Tuple[np.ndarray, np.ndarray]:
        """(on_wadi, tested). audit.r4's own test, recomputed so the design is not told.

        The grid's declared nodata is -9999.0 and np.isfinite(-9999.0) is TRUE, so a nodata
        cell falls through `floor(v) >= 4` as False and scores a silent PASS. The flag is
        right; the SILENCE is the defect - on the layer read 2026-09-02, 25,901 of 50,033
        chambers (51.8 %) sit on nodata and the run reported a clean result for them.
        Philosophy sec 3: the untested fraction is published beside every wadi result.
        """
        n = len(xs)
        if self._h is None or not n:
            return np.zeros(n, dtype=bool), np.zeros(n, dtype=bool)
        v = np.array([w[0] for w in self._h.sample(zip(xs, ys))], dtype=float)
        nod = self._h.nodata
        tested = np.isfinite(v)
        if nod is not None:
            tested &= (v != nod)
        tested &= (v > -1000.0)                 # belt and braces: any sentinel, not just nodata
        return (tested & (np.floor(v) >= min(C.HAZARD_WADI_CLASSES))), tested

    def is_wadi(self, xs, ys) -> np.ndarray:
        """Kept for call sites that only need the flag. Coverage comes from wadi_and_cover."""
        return self.wadi_and_cover(xs, ys)[0]
```

…and in `build()` (near the `wadi_moved` / `wadi_stuck` counters) record
`notes["wadi_untested"] += int((~tested).sum())`, so the manifest carries the untested count
beside the breach count. **A wadi result published without its coverage is not a result.**

### Change 5 — `W11a/py/s5_chambers.py`, `_nudge_off_wadi`: bounded search, and honest failure

```python
# BEFORE (the search loop inside _nudge_off_wadi)
        for i in np.flatnonzero(hit):
            s = stations[i]
            if why.get(s) in ("junction", "outlet", "head_at_gate", "start"):
                continue
            for d in (5.0, -5.0, 10.0, -10.0, 15.0, -15.0, 20.0, -20.0):
                t = s + d
                if not (0.0 <= t <= L):
                    continue
                p = line.interpolate(t)
                if not self.surf.is_wadi([p.x], [p.y])[0]:
                    out[i] = t
                    why[t] = why.get(s, "chamber")
                    self.notes["wadi_moved"] += 1
                    break
        return sorted(set(out))
```

```python
# AFTER
        # Search at HALF the hazard cell (1.5 m, audit.WADI_SAMPLE_M), not in 5 m jumps: a
        # 3.0 m grid resolves a bank to within a cell and a 5 m step steps over it. Search out
        # to the Table 12 headroom rather than a flat 20 m, and take the SMALLEST move that
        # works so P1/P6 lose as little as possible.
        #
        # What this can and cannot do, measured on the published layers 2026-09-02: 2,354
        # chambers stand on wadi ground; 319 have non-wadi ground within 20 m along the
        # network and 791 within 50 m. 587 have NONE within 250 m. Sliding chambers is not
        # the fix for this defect - the corridors run DOWN the wadis - so what matters as
        # much as the move is that the ones that cannot move are named, classified and
        # costed rather than counted.
        STEP = 1.5
        span = SPACING_TARGET_M                       # 94 m: Table 12's 100 m with the 3 m
        clear = C.MH_MIN_CLEAR_M                      # node-merge radius reserved at both ends
        for i in np.flatnonzero(hit):
            s = stations[i]
            if why.get(s) in ("junction", "outlet", "head_at_gate", "start"):
                continue
            # How far this chamber may travel before Table 12 bites on either neighbour, or
            # before it merges into one of them (contract.NODE_MERGE_M = criteria.MH_SNAP_M).
            lo = (out[i - 1] if i else 0.0)
            hi = (out[i + 1] if i + 1 < len(out) else L)
            back = max(0.0, min(s - lo - clear, span - (hi - s)))
            fwd = max(0.0, min(hi - s - clear, span - (s - lo)))
            offs = sorted(
                [d for d in np.arange(STEP, max(back, fwd) + 1e-9, STEP) if d <= fwd]
                + [-d for d in np.arange(STEP, max(back, fwd) + 1e-9, STEP) if d <= back],
                key=abs)
            for d in offs:
                t = s + d
                if not (lo + clear <= t <= hi - clear) or not (0.0 <= t <= L):
                    continue
                p = line.interpolate(float(t))
                on, tested = self.surf.wadi_and_cover([p.x], [p.y])
                if tested[0] and not on[0]:      # only move ONTO ground we have actually tested
                    out[i] = float(t)
                    why[float(t)] = why.get(s, "chamber")
                    self.notes["wadi_moved"] += 1
                    break
        return sorted(set(out))
```

### Change 6 — `W11a/py/s5_chambers.py`, `_report_wadi`: classify, do not just count

`_report_wadi` currently writes `TRIGGER`, a fixed `WHY_STUCK` and a fixed `REMEDY`. Those three
strings are the same for every row and therefore carry no information a person can act on. Add the
four measurements that decide the remedy, then derive the remedy from them:

```python
# ADD inside _report_wadi, replacing the fixed WHY_STUCK / REMEDY strings
        # RUN_LEN_M   the contiguous on-wadi run this chamber sits in, measured along the
        #             route - NOT the per-reach ON_WADI_M, which is capped by how the reach
        #             was split (3,037 CROSS_IDs, one per reach, max 93.8 m by construction).
        # D_DRY_M     straight-line distance to the nearest cell of KNOWN non-wadi ground.
        # SKEW        RUN_LEN_M / (2 x D_DRY_M): the run against the shortest crossing
        #             available at that point. H1a item 1 is a statement about this ratio.
        # MOVE_NET_M  distance to non-wadi ground ALONG the network. inf = it cannot move.
        run_len = self._on_wadi_run_len(line, s)          # walk the route, STEP = 1.5 m
        d_dry = self._dist_to_dry(pts[i])                 # 400 m window on the hazard grid
        skew = run_len / (2.0 * d_dry) if d_dry > 0 else float("inf")
        move = self._net_dist_to_dry(corr_id, s)          # Dijkstra, budget 250 m
        if move <= 20.0:
            remedy = ("slide it along its own route - non-wadi ground is within 20 m and "
                      "Table 12 has the headroom")
        elif move <= 50.0:
            remedy = ("slide it 20-50 m; check Table 12 on both neighbours and re-check every "
                      "tertiary leg discharging here against the 45 m of G203-p22 Tab 6")
        elif skew > 4.0:
            remedy = ("the corridor RUNS ALONG the wadi for "
                      f"{run_len:.0f} m against a {2 * d_dry:.0f} m crossing - this is an H1 "
                      "breach, not an H1a crossing. Re-route the corridor (stage 2), or the "
                      "plots behind it are served by another system (philosophy sec 8a)")
        else:
            remedy = (f"inside a {run_len:.0f} m crossing with no non-wadi ground within "
                      f"{move:.0f} m along the network: re-design the crossing (shorten or "
                      "de-skew the alignment, or take it trenchless, G203-p21/p35) so no "
                      "chamber falls on wadi ground. NOT a chamber-stage fix")
        self.wadi_stuck_rows.append(dict(
            CORR_ID=corr_id, STATION_M=round(float(s), 2),
            X=round(pts[i].x, 3), Y=round(pts[i].y, 3), TRIGGER=trig,
            HAZ_CLASS=int(np.floor(hazv[i])), RUN_LEN_M=round(run_len, 1),
            D_DRY_M=round(d_dry, 1), SKEW=round(skew, 2),
            MOVE_NET_M=(round(move, 1) if np.isfinite(move) else ""),
            WHY_STUCK=..., REMEDY=remedy))
```

The three helpers are the ones used to produce §2c and are reproducible from
`W11a/shp/W11a.gpkg` + the hazard grid alone; the working code is in §4 below.

### Change 7 — wire R4 to the grid

`run/s4_audit_readiness.csv` reports `R4,False,external.hazard`. Until `run_audit.py` passes
`hazard=` into the `Ctx`, the *only* wadi statement in the project is the design stage's own —
which is precisely the W8→W10 failure mode the philosophy names ("W8's engineering was carried
into W10 and W8's auditor was not"). Fix it before anything else in this document.

## 2e. Recommendation — Defect 2

1. **Fix the number first.** Retire the 1,051 (a stage-4 figure) and publish **2,354 of 24,132
   tested, 25,901 untested**. Never publish a wadi count without the coverage beside it.
2. **Correct the citation in `08_DESIGN_PHILOSOPHY.md` H1a item 2** from G201-p86 to
   G203-p30 §4.4.1(i)(a) + G203-p33 §4.6.2, and record that we read *"must be avoided"* as a
   prohibition by project decision. Keep the absolute rule.
3. **Tag `HAZARD_WADI_CLASSES = (4,5,6)` in `02` as a project assumption**, with the rasscript
   quoted, alongside GAP-9. It is a flood-safety classification standing in for a scour test.
4. **Slide the 791 that can slide** (Changes 5 and 6). That is a third of the problem and it is
   the only part that belongs to stage 5.
5. **Send the other 1,563 back up the pipeline, classified** — 1,272 to crossing design and
   291 to stage 2 corridor re-routing. Do not let stage 5 "solve" them; it cannot.
6. **Fetch the T50y grid for the other 51.8 %.** This is a data request, not a modelling choice
   (philosophy §3). Until it lands, the wadi result is a statement about half the network.

---

# 3. What needs a human decision

| # | Decision | Size | Who |
|---|---|---|---|
| **1** | **72 trunk-main chambers stand on wadi ground, and the trunk is the client's own drawn alignment** (`reaches.SRC = main_pipe`, 1,698 of 1,714). We cannot re-route it. Worst clusters below. | 72 chambers, 43 corridors | **User / draftsman** |
| **2** | **2,021 plots / 2,567 m³/d have no corridor within 47.5 m.** Philosophy §8a and TOR scope p4/p6/p8 say every plot is served — the question is *by which system*. | 2,567 m³/d (3.4 %) | **Client**, on life-cycle cost |
| **3** | **647 plots need a 42 m-median spur from the plot boundary to the carrier.** G203-p17 §3.2 puts the HCC in the public right-of-way. Does one exist across that land, or is the corridor on the wrong side of the block? | 647 plots / 795 m³/d | **User**, with the GIS land-use data |
| **4** | **The 45 m reading.** Table 6 puts the 45 m on the *Lateral Sewer* row only; p17 attaches it to riders as well. Keep the conservative reading (my recommendation), or declare a project cap. | affects 6,418 m³/d of headroom | **User** |
| **5** | **H1a item 2's citation is to the wrong clause** (G201-p86 is valve chambers and marker posts on a pressure crossing). Keep the absolute prohibition and re-cite, or align to G203's *"shall be avoided"* and open a derogation register. | 2,354 chambers | **User** |
| **6** | **587 chambers have no non-wadi ground within 250 m along the network**, and 291 of those sit in corridors that run *along* a wadi for up to 789 m. Re-route, or serve the plots behind them another way. | 152 corridors | **User**, then stage 2 |
| **7** | **51.8 % of the network is outside the T50y hazard grid.** Request full coverage from MoAFWR/CAA (G201-p85 lists it as a designer obligation for crossings anyway). | half the network | **Client / data request** |

**Decision 1 — the trunk clusters, worst first** (EPSG:32640; `run` = contiguous on-wadi metres,
`dry` = median metres to non-wadi ground):

| CORR_ID | chambers | run (m) | haz | dry (m) | approx X | approx Y |
|---|---:|---:|---:|---:|---:|---:|
| W11a-C024869 | 4 | 234 | 6 | 36 | 450 067–450 079 | 2 569 329–2 569 548 |
| W11a-C024722 | 5 | 216 | 5 | 38 | 452 647–452 776 | 2 573 157–2 573 243 |
| W11a-C024746 | 3 | 197 | 5 | 54 | 449 770–449 865 | 2 568 627–2 568 700 |
| W11a-C024691 | 4 | 188 | 5 | 21 | 453 009–453 083 | 2 573 442–2 573 536 |
| W11a-C024870 | 4 | 149 | 6 | 67 | 450 048–450 066 | 2 569 199–2 569 314 |
| W11a-C024868 | 3 | 147 | 6 | 36 | 450 079–450 080 | 2 569 554–2 569 694 |
| W11a-C025029 | 2 | 138 | 5 | 10 | 465 590–465 633 | 2 566 033–2 566 060 |
| W11a-C025119 | 2 | 129 | 5 | 23 | 459 958–460 032 | 2 567 677–2 567 707 |
| W11a-C024615 | 1 | 363 | 4 | 13 | 450 330 | 2 571 333 |
| W11a-C010320 | 1 | 230 | 4 | 9 | 452 597 | 2 573 124 |

Three of these (`C024869`, `C024870`, `C024868`) are consecutive on the same north–south leg
around E450 050–450 080 / N2 569 200–2 569 700: **the trunk runs down a class-5/6 wadi for
roughly 500 m there.** That is one decision, not three.

**Decision 6 — the worst "running along" clusters** (all `MOVE_NET_M` > 250 m):

| CORR_ID | chambers | run (m) | tier | approx X | approx Y |
|---|---:|---:|---|---:|---:|
| W11a-C010132 | 27 | 590 | main | 446 429 | 2 558 734 |
| W11a-C010048 | 19 | 651 | main | 457 519 | 2 567 065 |
| W11a-C018411 | 15 | 269 | main | 460 259 | 2 566 906 |
| W11a-C010005 | 11 | 734 | main | 459 236 | 2 566 737 |
| W11a-C011662 | 10 | 567 | sub main | 470 891 | 2 563 523 |
| W11a-C012150 | 9 | 542 | main | 454 606 | 2 566 079 |
| W11a-C010206 | — | **789** | — | (longest run in the network) | |

152 corridors carry the 587 unmovable chambers in total.

---

# 4. Reproducing every number here

Nothing above is quoted from a stage manifest except where it is named as such. All of it is
re-measured from the published layers. The scripts are in the session scratchpad
(`d1.py` … `d2g.py`); the load-bearing steps are:

```python
# on-wadi flag, WITH coverage - the version every wadi number in this file uses
v = np.array([w[0] for w in haz.sample(zip(xs, ys))], dtype="float64")
tested = np.isfinite(v) & (v != haz.nodata) & (v > -1000.0)
on_wadi = tested & (np.floor(v) >= 4)          # G203-p30 4.4.1 via HAZARD_WADI_CLASSES
```

```python
# contiguous on-wadi run along a corridor, sampled at half the 3.0 m cell
st = np.arange(0.0, g.length + 1e-9, 1.5)
f  = on_wadi_at([g.interpolate(float(s)) for s in st])
d  = np.diff(np.concatenate(([0], f.view(np.int8), [0])))
runs = [(st[a], st[b]) for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1)]
```

```python
# network distance from a chamber to non-wadi ground: Dijkstra over reach ends, checking
# every 1.5 m sample on each reach as it is relaxed. Reach-local walks stop at reach ends
# (max 94 m here) and report a false "unreachable" - that error cost 1,756 vs the true 587.
```

```python
# best-of-all-chambers assignment (Defect 1, Change 2), the version measured in 1d
hits = tree.query(plot_geom, predicate="dwithin", distance=47.5)   # shapely >= 2.0
# ... for each hit: offset, station, spur = max(0, offset - 2.5)
# ... for each END of the reach: leg = spur + d_along;  keep if leg <= 45
# ... rank on (-drains, leg, EDGE_UID, node)
```

Environment as measured: shapely 2.1.2 (GEOS 3.13.1), geopandas 1.1.4, numpy 2.4.6,
pandas 3.0.3, rasterio with `pdfplumber` available for the constant gate.

---

## Appendix — every number in this document, with its source

| Number | Source |
|---|---|
| 74,701.2 m³/d over 64,071 plots | `W10/shp/W10_plot_loads.gpkg[plot_loads].Q_AVG_M3D` |
| 7,639 zero-load plots at 0.0 m³/d | same, `Q_AVG_M3D <= 0`, `ZERO_WHY` |
| 22,513.2 m³/d over 24,554 plots rejected | `W11a/run/s5b_unassigned.csv` |
| 5,715 / 7,194.2 cannot drain; shortfall p50 0.15 m | same, `WHY` parsed |
| `DEPTH_M` = 1.600 on all 50,033 nodes | `W11a/shp/W11a.gpkg[nodes]` |
| 3,986 plots / 5,622.5 m³/d recovered by best-of-all | re-run of the frontage rule, 380,236 candidates |
| 5,936 / 7,510.9 residue; 3,268 / 4,148.3; 2,021 / 2,567.1; 647 / 795.5 | same, joined to `[corridors]` |
| 545 chambers, one per 45 m gate cluster | clustering of the 647 gates by reach and station |
| 3,086 plots at offset < 5 mm (2,055 published, 1,031 refused); 3,866 at offset < 1.0 m; **30** with no ROW-clear candidate | frontage rebuild + candidate table |
| 28.8 chambers/km, 34.7 m mean spacing | 50,033 nodes ÷ 1,737.5 km of `[reaches]` |
| 32.3 chambers/km as-built | `W8/docs/LEARNING_FROM_ASBUILT.md` |
| 2,354 wadi nodes; 24,132 tested; 25,901 untested | point-sample of `[nodes]` on `Hazard_T50y.tif` |
| 1,051 | `W11a/run/manifest_s4.json` — **stage 4, superseded** |
| 100.4 km on-wadi corridor / 82.3 km on-wadi pipe | 1.5 m sampling of `[corridors]` / `[reaches].ON_WADI_M` |
| 789 m longest contiguous run | `W11a-C010206` |
| 319 / 472 / 1,272 / 291 buckets | network Dijkstra + SKEW classification |
| 738 connections / 980.5 m³/d at a wadi chamber | `W11a/shp/W11a.gpkg[connections].OUT_NODE` |
| 72 trunk-main wadi chambers; `SRC = main_pipe` | `[nodes]` ∩ `[reaches].TIER == 'trunk main'` |
| G203 p17/18/19/22/30/33 quotes | `Data/PAM-GUD-203 …pdf`, pdfplumber, 2026-09-02 |
| G201 p85/86 quotes | `Data/PAM-GUD-201 …pdf`, pdfplumber, 2026-09-02 |
| AR&R hazard class definitions | `Data/04 Lekhuwair/Hazard_T100y.rasscript` |
