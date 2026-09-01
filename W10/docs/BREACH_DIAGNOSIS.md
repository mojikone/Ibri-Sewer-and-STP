# Why each of the 220 depth breaches happens — W10 Phase 3 diagnosis, 2026-09-01

The sized run puts **220 points** on the 1,883.6 km network where cover would pass 12.00 m.
This is each one taken individually: what caused it, how far over the limit it is, what
gradient would clear it, which diameter would deliver that gradient, and whether anything
can.

**Read this first. This diagnosis was commissioned to support upsizing runs so they could be
laid flatter. That is prohibited, in one unqualified sentence, and I verified it in the
source PDF:**

> **PAM-GUD-203 p29 §4.3.1** — *"Sewers shall not be oversized to facilitate flatter slopes.
> Uniform slopes must be maintained between successive manholes."*

The reason is on p167, listing what causes hydrogen sulphide: *"a. Oversized lateral sewers
and mains resulting in low sewage velocity in sewers causing solids deposition and long
retention times, promoting anaerobic conditions"*, with p185 adding *"Gravity sewers with
very low slopes are the ones with the greatest risk of H₂S formation"*. Long runs, low
velocity, Omani ground temperatures — the move triggers both listed causes at once.
`TUTORIALS/T02` §6.3 already carries the clause. The parallel optimisation study reached the
same conclusion independently, from the same page, on the same day.

**So the honest answer to "how many are irreducible" is three numbers, not one:**

| Question | Answer |
|---|---:|
| Irreducible **under the guideline as written** — no oversizing permitted | **219 of 220** |
| Irreducible **if the prohibition did not exist** — the size of the forbidden prize | **108 of 220** |
| Irreducible **on topography alone** — every reach at 0.075 %, self-cleansing set aside | **49 of 220** |

The one breach that is genuinely removable is a coding defect, not a design choice (§9).

The diagnosis below is still the useful part, and it is more useful now than it would have
been: with the gradient lever gone, the only levers left are the corridor and the scope, and
the classification says exactly which breach belongs to which.

---

## 1. What a breach actually is

In the lay-shallow construction the invert at a node is the lower of (upstream invert −
gradient × length) and (ground − cover − outside diameter). So a run starts at minimum cover
and everything after that is bookkeeping:

> **depth at node k = cover + OD + (pipe fall from the run head to k) − (ground fall to k)**

Nothing else enters it. Checked on all 220 runs: worst residual **0.000000 m**. A breach is
therefore always the same statement — the pipe fell further than the ground did over the
same stretch — and the diagnosis is only ever about which of the two terms did it.

[Certain] on the arithmetic: the reconstruction reproduces all 220 breach positions to
0.000 m and all 220 lift heights to 0.005 m against `W10_lift_sized.shp`.
[Likely] on the classification, which uses stated thresholds, all of them recorded per
breach in the CSV so the cut can be redrawn without re-running the solve.

**Runs are short and margins are small.** Median run 1.44 km, median margin over 12.00 m
just **0.88 m**. 76 of the 220 breach by 0.5 m or less — which is why the gradient lever
looked so attractive, and why losing it costs less than it appears to.

| Margin over 12.00 m | Breaches | Would clear by upsizing | Would not |
|---|---:|---:|---:|
| ≤ 0.5 m | 76 | 68 | 8 |
| 0.5 – 1 m | 40 | 20 | 20 |
| 1 – 2 m | 37 | 17 | 20 |
| 2 – 5 m | 40 | 6 | 34 |
| 5 – 10 m | 16 | 1 | 15 |
| > 10 m | 11 | 0 | 11 |

---

## 2. Cause classes

`CAUSE` partitions all 220; a chained breach is counted as D. `CAUSE_PHY` gives the same
breach its physical cause ignoring the chain.

| Class | n | Median margin | Worst | Median run | Median ground fall | Median peak flow | Median catchment |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A** long flat run | 14 | 0.40 m | 3.47 m | 3.17 km | +4.84 m | 8.9 L/s | 282 plots |
| **B** adverse ground | 62 | 1.62 m | 45.09 m | 1.56 km | −4.73 m | 1.3 L/s | 55 plots |
| **C** local ridge | 79 | 0.76 m | 25.38 m | 1.31 km | −5.28 m | 4.5 L/s | 147 plots |
| **D** inherited (cascade) | 24 | 1.40 m | 20.95 m | 1.51 km | −6.27 m | 4.2 L/s | 122 plots |
| **E** artefact | 41 | 0.73 m | 8.51 m | 1.25 km | −5.28 m | 1.5 L/s | 56 plots |

Physical cause ignoring the chain: **A 14 · B 77 · C 88 · E 41**.

**A — long flat run.** The ground falls, just slower than DN200's 0.500 % must. Median run
3.17 km, much the longest class, healthiest flows and largest catchments of the five. This
is the textbook case the upsizing idea was invented for, and **there are only fourteen of
them.** Even if the prohibition were lifted, class A is 6 % of the problem.

**B — adverse ground.** The route climbs, net, from run head to breach; median −4.73 m.
Worst is BID 28: a single 6,095 m corridor reach carrying **0.24 L/s** that gains 23.9 m of
ground, giving a 57.09 m chamber. That is not a hydraulic problem. It is a corridor drawn
across a hill to serve 11 plots.

**C — local ridge.** The biggest class. The ground rises to the breach and then gives at
least half the rise back within 1.5 km downstream — the corridor climbs out of one wadi and
drops into the next, which is the shape of this terrain. Worst is BID 189: 30.7 m of climb
over 1.0 km, then 40.2 m of fall immediately below it. **These are the re-routing
candidates**: unlike class B, there is lower ground nearby by definition.

**D — inherited.** The run head is itself a breach, so the pipe was reset to minimum cover
by a station above and dug back to 12 m. Only 24, and the cascade is shallow — §5.

**E — artefact.** The corridor should not be there: 29 runs more than 40 % inside 50-year
flood class 4–6, 11 more than 40 % on `auto_link` (the stitching lines that reach stranded
skeleton pockets across open ground), 1 a sizing defect. **These 41 are removed by editing
the corridor set, not by pumping.**

---

## 3. The gradient that would clear each run, and the diameter that would deliver it

Recorded because it was asked for and because it sizes what the prohibition costs — **not as
a recommendation**. Rearranging the identity, the run does not breach if at every node k

> **s ≤ (allowance + ground fall to k) / (length to k)**,  allowance = 12.00 − 1.30 − OD

`SREQ_PCT` is the smallest of those over the run; Table 11 (G203-p29) maps it to a diameter.
For the 112 that it would clear:

| Diameter that would be needed | n | Median relieving gradient | Pipe to upsize |
|---|---:|---:|---:|
| **DN250** (0.375 %) | 93 | 0.473 % | 166.8 km |
| DN315 (0.270 %) | 12 | 0.323 % | 16.0 km |
| DN400 (0.205 %) | 6 | 0.251 % | 9.7 km |
| DN600 (0.125 %) | 1 | 0.152 % | 2.5 km |
| **total** | **112** | 0.465 % | **195.0 km** |

**83 % of the prize is one diameter step**, DN200 → DN250, at a median gradient reduction of
under three hundredths of a per cent. 195.0 km is about **10 % of the network** — and it is
the minimum relief, each reach taken to the gradient the run needs or its own floor,
whichever is steeper. So the prohibition costs roughly 195 km of upsizing that would have
bought 112 breaches and, once consolidation is applied, **5 of the 21 stations** (§6).

That is the whole trade, and it is not ours to make: "shall not" has no exception in 201
pages.

---

## 4. What blocks the other 108 anyway — and it is mostly not the ground

Even setting the prohibition aside, 108 of the 220 would not clear. Two different blockers,
and they are not the same problem.

| Blocker | n | Median peak flow | Median catchment | Median margin |
|---|---:|---:|---:|---:|
| — (would clear) | 112 | 7.78 L/s | 233 plots | 0.37 m |
| **GROUND** | 42 | 0.36 L/s | 20 plots | 3.59 m |
| **TRACTIVE** | 66 | 0.62 L/s | 37 plots | 2.05 m |

**GROUND** means the relieving gradient is negative or below 0.075 %: the ground rises more
than the 10.4 m allowance over the run, so no diameter and no positive gradient clears it.

**TRACTIVE** is the interesting one. `smin_for` takes the **steeper** of Table 11 and the
tractive-force minimum (G203-p27 §4.2.2.1), and the tractive minimum is a function of
**flow, not diameter**:

> S = 2.33e-4 · τ^1.23 · Q^-0.461, with Q floored at Mara's 1.5 L/s design minimum

At that floor it is **0.467 %** — barely under DN200's 0.500 %. On a branch carrying nothing,
a DN900 would buy 0.033 percentage points of gradient and nothing else. You need about
**2.4 L/s** before DN250's 0.375 % is reachable, **16 L/s** before DN500's 0.155 % is, and
**79 L/s** before DN900's 0.075 % is. The self-cleansing physics and the p29 prohibition are
therefore saying the same thing from two directions, which is a good sign that both are right.

Reducibility consequently tracks flow almost perfectly and topography hardly at all:

| Peak flow at the breach | Would not clear | Would clear | % blocked |
|---|---:|---:|---:|
| < 1 L/s | 63 | 8 | 89 % |
| 1 – 5 L/s | 30 | 27 | 53 % |
| 5 – 20 L/s | 14 | 53 | 21 % |
| 20 – 100 L/s | 1 | 21 | 5 % |
| > 100 L/s | 0 | 3 | 0 % |

**Flag it plainly: τ = 1.0 Pa is an assumption, not a guideline value.** GUD-203 mandates the
tractive method and gives **no numeric design stress** (`criteria.ASSUMPTIONS`, GAP-9); 1.0 Pa
comes from the Mara literature, as does the 1.5 L/s floor. Set self-cleansing aside entirely,
lay the whole path at 0.075 %, and **49 breaches still fail**. That 49 is the hard topographic
floor and is the only number here that no assumption can move.

---

## 5. Chains

**192 independent chains among the 220 breaches**, once every class-D breach is attributed to
the breach that started it. Only **20 chains have more than one member** — 14 pairs, 4 threes,
2 fours; 172 breaches are their own root. **97 chains contain at least one that would not
clear.**

The cascade barely exists, and the interaction it does create runs the *wrong* way: relieving
an upstream breach removes its reset, so the pipe arrives at the next one deeper than the
station left it. That is why the three counts differ and why the middle one is not the answer:

| Question asked | Would clear |
|---|---:|
| the stretch below the station above, judged alone | 120 (upper bound) |
| the whole path from the true network head, always | 102 (lower bound) |
| **chains walked top down, each decision setting the next one's start** | **112** |

---

## 6. Breaches are not stations

Rule 9 consolidates anything within 1.5 km and keeps a station only where the flow arriving
at it reaches 50 properties (54.0 m³/d on the locked basis — the `p6_force.py` test):

| | Breaches | Clusters at 1.5 km | Stations |
|---|---:|---:|---:|
| as solved | 220 | 33 | **21** |
| if upsizing were permitted | 108 | 38 | 22 |
| topographic floor | 49 | 27 | 17 |

**Read the middle row carefully: the station count does not fall.** That is not a mistake.
Consolidation chains transitively, so removing breaches in the *middle* of a cluster splits
it in two and the count rises even as the problem shrinks. The monotone statement is the one
to quote:

> **Of the 21 stations as solved, 5 would lose every one of their breaches to upsizing and 16
> would keep at least one.** The forbidden lever was worth about a quarter of the stations,
> not half the breaches.

It was worth more in duty than in count: **1,244 m of the 2,846 m of total lift** sits on
breaches upsizing would have cleared.

**On the published station figure.** `W10_SUMMARY.md` quotes 11. Measured consistently it is
**21** — the 11 double-filters, applying the catchment test to a set already cut to those
with 50+ plots *within 750 m*. `W10_stations_final.shp` holds a third number, 28, on that
proximity count alone. This document uses 21, which agrees with the parallel optimisation
study's independent correction.

---

## 7. The empty branches — the largest lever still available

**128 of the 220 breaches sit on runs carrying under 5 L/s peak. 71 carry under 1 L/s. 93 of
the 128 would not clear even if oversizing were allowed.** Between them the breach runs
contain **177.1 km** of reaches under 1 L/s.

The physical shape of it: **105 pipe reaches in the network are longer than 1 km**, of which
53 are `auto_road` corridors with a **median peak flow of 0.05 L/s** across 95.8 km — single
unsplit polylines across open desert, one of them 6.1 km end to end. They pick up almost no
load, they cannot be laid flatter because they carry nothing, and every kilometre at 0.500 %
eats 5 m of the 10.4 m allowance.

The 108 blocked breaches carry **17,746 m³/d** between them at a **median of 27.4 m³/d**,
against 73,442 m³/d network-wide. Half serve fewer than 26 plots.

**These are a scope question, not a pumping question.** Three options, none decided here:
(a) do not sewer them — on-site or tankered collection for isolated pockets is a normal
answer at this density; (b) sewer them and accept an in-line station as cheaper than
kilometres of corridor; (c) re-draw the corridor so it does not run uphill for eleven plots.

`FIX` carries the first cut of that judgement: **DELETE CORRIDOR 41 · NO SEWER / RETHINK 43 ·
STATION 41**, with the remaining 95 tagged UPSIZE — which now reads as *would have been
upsized*, and must be re-tagged STATION or re-scoped.

---

## 8. What is still permitted

The gradient lever is gone. These remain, and this diagnosis points at each:

| Lever | Reaches it applies to | Evidence here |
|---|---|---|
| **Lay the correct minimum gradient** where the code laid a steeper one | 5 reaches, 2.8 km | §9 defect 1 — removes the deepest breach in the network |
| **Delete corridors that should not exist** | class E, 41 breaches | 29 wadi, 11 `auto_link`, and the wadi rule is not applied at all (§9 defect 3) |
| **Re-route around a local high** | class C, 88 physical | 13 of the blocked breaches have a corridor edge on their run carrying no pipe and falling, best 20.95 m |
| **Do not sewer the empty branches** | 128 under 5 L/s | §7 |
| **Split the very long reaches** | 105 over 1 km | the solve cannot see depth inside a 6 km reach (§10) |
| Accept the station | the remainder | 21 as solved |

---

## 9. Three defects found while doing this

**1. `p2_sizing.size_all` writes a large pipe at a small pipe's gradient.** The loop iterates
diameter and gradient together; when `hydra.size_pipe` returns `None` it forces DN to the top
of the series and **breaks, leaving `s` at the previous iteration's value** — DN200's
0.500 %. Detected exactly (laid gradient ≠ `smin_for(own DN, own flow)`): **5 reaches,
2.8 km, all DN1200 carrying ~1,360 L/s, laid at 0.500 % where the Table 11 floor for ≥ DN900
is 0.075 %.** They carry **11.9 m of fall that should be 1.6 m**.

The consequence is not small: **BID 220, the deepest breach in the network at 20.51 m, is
this defect.** It is the trunk arriving at the existing works with all 62,615 plots behind
it, and 12.63 m of its fall comes from one 2,526 m reach laid nine times steeper than its own
minimum. Correcting it takes the depth to about 8.6 m and the breach disappears — and this is
**not** oversizing: the diameter is already DN1200 for capacity, and the fix is to lay it at
the minimum for the diameter capacity requires. The underlying hydraulic fact stays and needs
a decision: a single DN1200 **cannot** carry 1,361 L/s at 0.075 % inside its 0.50 d/D limit,
so that reach needs a gradient chosen by capacity, a pipe larger than the series holds, or
twin barrels. Not fixed here.

**2. The wadi test in this analysis, corrected before use.** `Hazard_T50y.tif` is a
**continuous float** grid (1.00, 1.01, 1.02 …) with −9999 outside the modelled basin, not
integer classes. Testing membership of {4, 5, 6} matches almost nothing and silently reports
no wadi anywhere. Read as `floor(value) ≥ 4`, as `p4_stp_siting.py` does, **62 of the 220
breach runs touch wadi ground and 32 are more than 40 % inside it**. Coverage caveat: the
grid spans only part of the study area — median 47 % of the samples on a run — so `WADI_PCT`
is the share of *covered* samples and the true figure is higher.

**3. The wadi exclusion is not applied to the corridors at all.** `HAZARD_WADI_CLASSES`
(classes 4/5/6, "no pipes or chambers", user 2026-08-19) appears only in `p4_stp_siting.py`.
No corridor phase reads it. That is a settled rule the corridor network does not obey, and it
is generating breaches.

---

## 10. Caveats

- **The sized solve checks depth at nodes only.** `p2_depths` sampled the ground between
  nodes at 20 m; `p2_sizing` re-implements the solve inline and drops that. With 48 breach
  runs containing a single reach over 1 km — one of 6.1 km — that is not a small omission.
  Sampled here at 20 m along every breach run: **7 breaches that clear on nodes do not clear
  with the ground between them** (`SLACKMID_M` < 0 where `SLACK_M` ≥ 0), and one run hides a
  ridge worth 3.77 percentage points of gradient. Headline numbers are node-based so they
  reconcile with the 220; the sampled columns say where that is optimistic.
- **The outside diameter in the solve is a fixed 0.30 m** regardless of DN, so a run upsized
  to DN900 would lose another 0.6 m of allowance the published run does not charge it.
  Accounted for in the relief test, not in the 220 as solved.
- **"Alternative corridor within reach" is weak evidence.** 13 of the 108 have a corridor edge
  touching their run that carries no pipe and falls. The router may have skipped it because it
  dead-ends. It says a re-route is geometrically possible, not that it works.
- **Load basis.** Flows are the placeholder allocation, 73,442 m³/d placed. Since the analysis
  tracks flow this closely, the clean land-use data will move these counts: a branch that
  gains flow changes class, one that loses it does not.
- **Baseline difference.** This reconstruction gives 220 breaches; the parallel optimisation
  study's base run gives 219. One breach, not chased. Both give 21 stations.
- Classification thresholds (ridge 1.0 m with half given back within 1.5 km, artefact at 40 %
  link or wadi, empty at 5 L/s) are **method choices**. Every underlying quantity is in the CSV.

---

## 11. Outputs

| Path | Content |
|---|---|
| `W10/py/p3_breach_diag.py` | re-runnable, ~34 s, modifies nothing upstream |
| `W10/shp/W10_breach_diagnosis.shp` | 220 points, 58 fields |
| `W10/run/W10_breach_diagnosis.csv` | the same, machine readable |
| `W10/run/W10_breach_stations.csv` | the three consolidation cases of §6 |

Field guide: `CAUSE`/`CAUSE_PHY`/`E_REASON` the classes · `MARGIN_M` depth over 12.00 ·
`RUN_M`/`RUN_N`/`GFALL_M`/`PFALL_M`/`MAXREACH` the run that caused it · `QADF_M3D`/`QPK_LS`/
`PLOTS_UP` the catchment draining through it · `SREQ_PCT` the relieving gradient and
`SREQM_PCT` the same with the ground between nodes · `DN_REQ` the diameter that would deliver
it · `STRACT_PCT` the tractive floor · `RED_SEQ` the would-it-clear answer, with
`REDUCIBLE`/`RED_FULL` the two bounds and `RED_T11` the topography-only test ·
`BLOCKER`/`FIX` the verdict · `CHAIN_RT`/`CHAIN_POS` the cascade · `SUBNET` ·
`ALT_N`/`ALT_DZ_M` untaken corridor · `ARTFALL_M` fall from the sizing defect.

Verification, mechanical and not from memory: 220 of 220 breach positions reproduced to
0.000 m, 220 lift heights to 0.005 m, the depth identity closing to 0.000000 m,
`1.6 + s_req·L − ground fall ≤ 12.00` on every row with equality on the 37 whose binding node
is the breach itself, and the Table 11 diameter mapping re-derived independently. The p29,
p167 and p185 quotations were read from `Data/PAM-GUD-203 - Wastewater Design Guidelines
v1.0.pdf`, not recalled.
