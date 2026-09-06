# INHERITANCE — what each iteration learned, and what the next one lost

**Companion to `08_DESIGN_PHILOSOPHY.md`. Not a duplicate of it.**

> **The philosophy says what a good design looks like. This says what has already been
> learned, so it is never learned twice.**

`02` says whether a design is legal. `08` says how to make it good. Neither of them stops a
new iteration from silently dropping something an earlier one had already got right, because
neither is a list of what was got right.

**The evidence that this file is needed, and it is recent.** On 2026-09-03, W11b published
three pumping stations in the test area where the built network has none and W8's design of
the same ground has none. They were leftovers: the solver only ever *added* a station and
never re-tested one placed in an earlier pass. **W8 knew this on 2026-08-21** and said so in
a comment — *"a pump placed in an earlier pass may not be needed once diameters change, and a
stale flag would double-count stations"* — and cleared every flag at the top of every pass.
W11b did not carry it. Pruning afterwards took the demand from **83 stations to 14**.

That happened *after* `08_DESIGN_PHILOSOPHY.md` existed and *after* `W8_W10_POSTMORTEM.md`
had already named "W8's auditor was not carried" as the cause of the previous failure. So the
philosophy is necessary and **not sufficient**. What was missing is a ledger.

**How to use it.** A new `W#` may not declare itself complete until every row below is either
(a) implemented, with the enforcing check named, or (b) explicitly waived, with a reason on
the record. A finding with no check is the definition of a finding that will be lost.

---

## 1. The ledger — findings that must survive every iteration

Ordered by the cost of losing them. `ENFORCED BY` names the thing that fails if it is dropped;
where that column reads **none**, the finding is currently protected by nothing but attention.

| # | Finding | Learned in | Cost when it was lost | Enforced by |
|---|---|---|---|---|
| 1 | **An independent audit registry runs on every build.** Each check recomputes its own constraint and carries its guideline page | W8 (22 checks) | W10 shipped 2.80 km surcharged, 10.68 km over d/D, 45.92 km below cover, 1.67 km along a dual — none subtle, none looked at | W11b `tests -m audit` |
| 2 | **A check that cannot run is a FAILURE, not a blank** | W11a | W10's audit had no "cannot run" state, so absent chambers read as compliance | W11a `audit.py`; W11b test gate |
| 3 | **The auditor reads the PUBLISHED layers, never an in-memory model** | W11a | W10's flow tree existed only inside a sizing script; the shapefile inherited geometry alone | W11a `audit.py`; W11b `contract.py` |
| 4 | **Clear every pumping-station flag at the top of every pass** — a station placed early may not be needed once diameters and drops change | W8 | W11b published 3 spurious stations in the test area; demand fell 83 to 14 once pruning ran | **none — add it** |
| 5 | **A sewer network is a three-tier hierarchy**, read from NAMA's own manhole IDs (`5A-2-TM-MH185`). Trunk 5.1 %, sub main 18.4 %, laterals 66.5 % across 419 zones | W8 | W7 had no sub-main tier: 30 things touched the trunk, 14 carrying under 100 properties, one carrying 3. W10 had no `TIER` field at all | W11b tier tests |
| 6 | **91 % of laterals drain into another lateral**, median 11 before a sub main, so only ~16 things touch the trunk — 4.0 per km of trunk | W8, corrected in W10 | The correction matters: W8's "91 %" is dominated by one package carrying zero TM/SM tokens. In labelled packages the chain is median 2, max 5 | philosophy §3.1 checks |
| 7 | **Report joins per km of trunk, never joins in total.** W8 3.3/km capped at 20; W10 2.3/km uncapped at 214; as-built 4.0/km | W10 postmortem | "20 versus 206" was quoted as a discipline failure. It is a length effect | **none — add it** |
| 8 | **Matching averages proves nothing about layout.** W7's gradients, depths, spacing and junctions/km all matched the as-built while the hierarchy was entirely absent | W8 | A calibration passed that should have failed | **none — doctrine, not a check** |
| 9 | **Every constant is re-read from its cited page at build time** | W11a (P9) | Rising mains capped at 3.0 m/s where G203-p50 says 2.5; inlet angle carried at 85° in code and 75° in its own docstring | W11b `test_constants.py` |
| 10 | **One published quantity, one function.** Any metric with a filter chain prints its own funnel | W10 postmortem (P2) | Seven station counts in circulation: 19, 21, 25, 37, 140, 184, 239. **Still failing: W11b's levelling demands 14 and its pump stage designed 47** | **none — add it** |
| 11 | **The graph is the design; geometry is derived.** Nodes have identity; an edge's line is built from its own nodes' coordinates | W11b `contract.py` | W10's published layer was 7,919 disconnected components; 91.4 % of stitch links stopped exactly 1.000 m short | W11b, by construction |
| 12 | **Zero silent drops.** Every load unit is assigned to a chamber or named in a funnel | W11a | W10 dropped 1,233 m³/d (1.7 %) at an assignment radius, invisibly | W11b `Funnel` |
| 13 | **A stage may not silently no-op.** Every step reports a count or declares itself skipped | W10 postmortem | `RoadTreatment(units=None, sampler=None)` — 3 of 9 steps did nothing; the roundabout guard that rejected 69 of 81 candidates in W8 was off, and 34 collapsed "roundabouts" contain a registered plot | **none — add it** |
| 14 | **Chamber clearance applies to every chamber, against every plot** — not only bend chambers, not only loaded plots | W8 | 49 chambers landed inside house plots, one 4.8 m inside a 739 m² plot. 48 found, 26 freed, 22 reported rather than hidden | W11b chamber stage |
| 15 | **Charge every pipe that physically crosses a dual carriageway**, not only crossings the code creates; underpass radius 30 m, not 120 m | W8 | 8 pipes crossing, 1 reported; the labelled one sat 97 m from the underpass | W11b crossings layer |
| 16 | **The wadi rule is applied at the corridor, not in the router** — and a *crossing* is legal where *presence* is not | W8, restated W11a (H1a) | W10 never wired it in: 131.7 km on wadi ground. Reading the prohibition as one on passage severed W11a's network into 1,381 pieces | philosophy; W11b hazard stage |
| 17 | **Round 0.05 % gradient steps, and publish the gradient the pipe is LAID at**, with the minimum beside it | W8 | W10 published the *minimum required* gradient, so a laid gradient of 980 % was invisible. Round steps cut distinct gradients 448 to 103 for 1.0 % more excavation | W11b levels stage |
| 18 | **Depth is COVER, and it is measured between nodes as well as at them** | W8 (`p2_depths`) | W10 computed 82,187 mid-span samples in one module and threw them away in another; 120 reaches laid below minimum cover, worst 0.40 m | W11b invariants |
| 19 | **The trunk is an INPUT, designed end to end before anything drains to it** | W7 → W8 | W6 guessed it from streets near a described line: 2.1 km found, 4 stations needed | philosophy §2 stage 3 |
| 20 | **Topology is written down, never inferred from a snap tolerance** | W11a (H16) | "W10 has 310 loops" was false — it has none; 311 appear only at a 2.5 m snap. Seven numbers were retracted on this basis | W11b `contract.py` |
| 21 | **Rerouting to avoid a breach does not work at scale** — measured, not assumed | W10 | 219 breaches base, 223 after one avoid round. Only 13 of 108 irreducible breaches have any alternative corridor at all | recorded finding |
| 22 | **A published column that is constant where it should vary is a fabrication** | W11b | `ANGLE_DEG = 90` on all 3,290 crossings, called a declaration. Measured minimum was 0.00°, with 23 under 45° | W11b `test_columns.py` |
| 23 | **No-data is not data.** `-9999` is finite; an unfound riverbank is not an 800 m channel | W11b | Twice: a flood grid's no-data passed an `isfinite` guard, and a search cap was published as a distance | W11b `test_nodata.py` |
| 24 | **A lifting station is a commissioning device**, not only a depth device — one is what let 60.8 km and ~5,963 properties be built before the deep trunk existed | W10 research | W10 treated stations purely as a cost to minimise | philosophy §5.3 |
| 25 | **Manning is 86 % of a station's life-cycle cost; energy is 0.4 %** | W10 research | Effort was going into excavation rates, which move the answer from 11 breaches to 4, while manning moves it from 10 to 2 | philosophy §8 |
| 26 | **No solver chooses a layout** — SewerGEMS, InfoDrainage, Civil 3D, InfoWorks, InfoSewer. None will ever propose a pumping station | W10 research | prevented a wrong delegation rather than fixing one | philosophy §9 |
| 27 | **Tighter manhole spacing does NOT keep trenches shallower** — tested and rejected | W8 | a rejected hypothesis is a finding; re-testing it costs a day | recorded finding |
| 28 | **Upstream claims are verified before they are believed.** `tarjans_pq` is Prim's on a reversed graph, not Tarjan's branching — proved against `networkx`, 36–57 % above optimum | W11b | would have imported a wrong topology engine | `W11b/docs/UPSTREAM_METHODS.md` |

**Five rows have no enforcement: 4, 7, 10, 13, and the doctrine in 8.** Row 4 has already cost
one iteration, and row 10 is failing in the live design right now.

---

## 2. What each iteration contributed, and what it dropped

### W8 — the small design that got the shape right
*5.51 km², 71.6 km, 1,415 chambers, deepest 10.45 m, **zero pumping stations**, 3 checks failing.*

**Contributed:** rows 1, 4, 5, 6, 8, 14, 15, 17, 18, 19, 27 — the hierarchy read from the
as-built's manhole IDs, the join sweep (20 is the tightest structure that stays on gravity
without cutting a dual carriageway; below 14 buys a pump, below 8 crosses 15 of them), the
`TIER` field on every pipe, and the audit registry itself.

**Lacked:** everything that scale reveals. Its zero-stations result is a property of a flat
town core — 3 of W10's 239 breaches fall inside its boundary, 236 on the other 1,807 km. Its
chamber rules, its round gradient steps and its reroute passes had never met adverse ground.

### W10 — the full area, with the auditor left behind
*531.4 km² (96×), 1,883 km (26×), 20,936 reaches, 239 breaches → 19 stations, **0 checks**.*

**Contributed:** the first full-area design, and the nine research documents everything since
rests on — hierarchy rules measured from the as-built, corridor provenance and trust grading,
what to sewer, the depth-versus-pumping economics, the two solver studies, the deliverable
spec, the philosophy review and the build brief. Rows 7, 10, 13, 21, 24, 25 and 26 are all
W10's, and most are lessons drawn from its own failures.

**Dropped from W8:** the auditor (22 checks to 0), chambers entirely (it solves on corridor
nodes; 4,763 reaches exceed Table 12 spacing — 64.8 % of the length, longest 6,541 m), the
`TIER` field, the wadi exclusion, round gradient steps, the mid-span depth check, and the
`RoadTreatment` guards. It kept exactly one thing from W8 across 36 scripts: the string
`"one dwelling per plot (W8 fallback)"`.

**Result:** not issuable. 2.80 km surcharged · 10.68 km over d/D · 45.92 km below cover ·
1.67 km along a dual · 131.7 km on wadi ground · 7,919 disconnected pieces · 4,041 dead-end
fingers · 1,233 m³/d silently dropped.

### W11a — the auditor first
*1,731.7 km, 49,624 chambers, 247 components each with one outfall, 18 pass / 4 fail / 0 cannot-run.*

**Contributed:** rows 2, 3, 12, 16, 20. The auditor was written before the design and run
against W10 on day one — 2 pass / 13 fail / 7 cannot run — and that table became the
specification. `contract.py` maps every published field to the check it feeds. Seven numbers
were retracted, including the "310 loops" that had been quoted as a defect for a week.

**Lacked, against W8:** nothing structural — but scale exposed what W8's flat core had hidden.
**42.5 % of the length drained uphill, and the design wanted 2,449 vortex drop shafts where
NAMA built 37.** No levelling arithmetic fixes that; it is a tree-orientation problem. Also
168 reaches over the d/D limit, stations located but never designed (zero duty flow, zero
rising mains), two study-area boundaries in simultaneous use, and no test suite.

### W11b — the graph is the design
*1,489.7 km, 56,930 chambers (38.2/km), 41 drop shafts, 26.3 % uphill, 0 below cover, 0 over d/D, 0 over 3 m/s.*

**Contributed:** row 11 — four W10 failure modes made impossible *by construction* rather than
caught by check. Rows 22, 23 and 28, and the test suite: six files, each written against a bug
that actually happened, including two no result-based check could ever find (a constant that
disagreed with itself across two files, and dead code costing 26 minutes a run for weeks).
Pumps are **designed** — duty flow, lift, wet-well volume, motor size, life-cycle cost, 47
rising mains — where W11a only located them. A survey of 839 upstream repositories found
nothing that sizes a wet well.

**On the two measures that say whether a layout follows the ground — drop shafts and uphill
drainage — W11b beats the built network** (41 against 37, at a twentieth the density; 26.3 %
against 34.1 %). That is the first iteration to manage it.

**Dropped:** row 4, W8's pump-flag clearing — the failure that prompted this file.

**Open now:** the two station counts disagree (14 demanded, 47 designed) · 15 of those 47 have
nothing draining into them · 42 components discharge with more than half their catchment below
the outlet (389.5 km) · 18 subnetworks stop short of the main pipe · 5,521 plots cannot drain
on gravity · deepest excavation 19.78 m past the 12 m cap · `s8_export` fails its own contract ·
four of eight stages record no runtime at all.

---

## 3. What the next iteration should improve

**Engineering, in order of size:**

1. **The 42 badly-placed outfalls, 389.5 km** — an outlet sitting above its own catchment is a
   layout decision. The largest open defect; it needs the engineer.
2. **Reconcile the station count** (14 vs 47) under row 10 — one function, one number, funnel
   printed. This is the same defect that produced seven station counts in W10.
3. **The 15 stations with nothing draining into them**, and the 18 subnetworks that stop short
   of the main pipe.
4. **The 5,521 plots that cannot drain to their chamber on gravity** — G203-p18 Table 5.
5. **Chambers at 38.2/km against the built band 33.3–36.8** — defensible, but that is 2,000+
   chambers of difference and it should be a decision, not a residue.
6. **Implement `K_FLIP`** from philosophy §8, so every station carries the excavation rate at
   which its own decision flips. It is rate-free and quotable before the BoQs arrive.
7. **Instrument every stage with a runtime** — four of eight record none, and total compute is
   only about 5.5 minutes, so measuring it costs nothing.

**Process:**

8. **Close the five unenforced rows** — 4, 7, 10, 13, and a written statement of 8.
9. **`τ` from NWS.** Held at 1.0 Pa by the engineer's decision; at 2.0 the required gradients
   roughly double and 1,124 pipes change.

---

## 4. The rule this file creates

**Every new `W#` opens by copying this ledger into its own folder and marking each row:
IMPLEMENTED (naming the check), WAIVED (with the reason), or NOT YET. It closes with no row
left at NOT YET.**

The mechanical form of that is a check inside the iteration's own audit registry — the same
argument `08` §10 makes about philosophy. A rule that cannot be checked is decoration, and a
finding that is not checked is a finding waiting to be lost twice.
