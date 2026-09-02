# DESIGN PHILOSOPHY — how to arrive at a good sewer network

**Companion to `02_DESIGN_CRITERIA.md`. The two are not the same thing and must not be
merged.**

> **Criteria tell you whether a design is LEGAL. Philosophy tells you how to make it GOOD.**
>
> A design can satisfy every number in `02` and still be one no contractor would build and
> no operator would adopt. W10 proved it: it met the gradient table, the velocity band and
> the depth limit, and it produced 4,041 dead-end fingers, 310 loops, 62 km of pipe in wadis
> serving nothing, and a trunk that carried a main on only 21 % of its length.

This document is binding on every network design in this project. Where it conflicts with
`02`, `02` wins — a criterion is a rule of law and this is a rule of judgement.

**Scope:** the **gravity foul sewer network**, from the property connection to the works
inlet, including its lifting stations and rising mains. The treated-effluent network and the
treatment works are governed by their own criteria in `02` and need their own philosophy;
neither is covered here, and that omission is deliberate rather than an oversight.

> ## ⛔ STATUS 2026-09-02: NOT READY TO DESIGN FROM
>
> An adversarial review (`W10/docs/research/PHILOSOPHY_REVIEW.md`, 727 lines) returned
> **8 CRITICAL and 14 MAJOR findings**. The *judgement* in this document survives — the
> objective ordering, the order of design, the cap-and-veto ladder, the two-pass method, and
> "a solver can referee hydraulics and never routing" all check out. **What failed is the
> layer beneath it: the numbers, the citations and the checks.**
>
> The worst of it, and it is this document convicting itself: **about a dozen headline
> measurements cannot be traced to any saved file** — including four in the blockquote below,
> which is the document's whole reason to exist. They were computed in throwaway scripts that
> were never kept. That is a direct breach of **P2 — "every published number comes from
> exactly one function"** — by the document that states it.
>
> Fixed so far: the 20 mm tolerance (was wrongly stated as 40 mm), the missing 0.75 m/s
> minimum velocity and 0.90 m/s preferred, and the tier-vocabulary clash with G203.
> **Outstanding: the traceability rebuild, the depth re-measurement in §5.1b, and the §9
> citations.** Do not design from this until that banner is removed. Everything else rests on measurements made in W8, W10 and NAMA's as-built network,
and every claim carries where it came from.

---

## 1. What "best" means, and in what order

A sewer network is not optimised for one thing. These are the objectives in **priority
order**, and the order is the philosophy:

| # | Objective | Why it outranks what follows |
|---|---|---|
| 1 | **It complies** | A design that breaks a "shall" is not a design |
| 2 | **It can be built** | A contractor prices what he can dig. Fingers, bends, loops and 6.5 km reaches with no chamber are not buildable, whatever their hydraulics |
| 3 | **It can be operated and adopted** | NAMA has to run it for fifty years. It must read like their own network — tiers, packages, manhole numbering, jetting access |
| 4 | **It can be built in stages** | 1,883 km is not one contract. Every stage must be commissionable on its own |
| 5 | **It costs least over 25 years** | Life-cycle, not capital. Pumping is an operating cost forever; a deeper trench is paid once |
| 6 | **It is hydraulically minimal** | Smallest pipe, flattest legal gradient, least depth — **last**, because this is what a solver optimises by default and it is the least important of the six |

**W10 optimised 6 and ignored 2, 3 and 4.** That single inversion explains almost every
defect found in it.

---

## 2. The order of design

Decide in this order. Each stage is fixed before the next begins, and going back is a
decision, not a drift.

| # | Decided | Why here |
|---|---|---|
| 0 | **The auditor** | You cannot know a design is good if nothing independent checks it. Write the checks before the design |
| 1 | **What is served** | 6–20 % of W10 should never have been designed. Deciding scope after design is how you get 333 km of sewer collecting 151 m³/d |
| 2 | **The corridors, with their provenance** | A pipe cannot be better than the line it is laid on. Wadi and dual-carriageway exclusions apply HERE, not in the router |
| 3 | **The trunk** | Designed end to end as a main, at main diameter, before anything drains to it. If the trunk emerges from accumulated flow it will not be a trunk |
| 4 | **The hierarchy** | Sub-mains chosen as collector routes on through-streets, then laterals chained into them |
| 5 | **The chambers** | Spacing, junctions, bends, drops, heads at gates |
| 6 | **The levels and sizes** | Only now. This is the part software does |
| 7 | **The packages** | Phases and contracts, seams at lifting stations |

The single most important line in this table is **stage 3 before stage 6**. The trunk is an
engineering decision about where the town drains; it is not an output of a sizing loop.

---

## 3. Layout philosophy

**3.1 A network is a hierarchy, and the hierarchy is generated by a rule.**
Properties feed riders, riders feed laterals, laterals chain into laterals, laterals join a
sub main, sub mains join the trunk. Measured on NAMA's properly labelled packages:

- a **lateral zone is one unbranched street run** — 99.6 % a simple path with one head;
  median 132 m, 5 chambers, 4 properties; cap 920 m
- **at most 3 lateral zones and 750 m of flow path before a main** (as-built p95: 3 / 722 m)
- a **sub main is a collector route defined by its outlet**, not by a load threshold — 4 of
  10 begin with zero properties; it is about 21 % of the length of the catchment it drains;
  one per 4–10 km of network
- the **trunk is traced from the outfall backwards**, top-down

*Correction on the record:* W8's headline that 91 % of laterals chain with a median depth of
11 is dominated by package 5A-1, which carries **zero TM and zero SM tokens** across its
1,123 pipes — everything there parses as a lateral because no other label exists. In the
labelled packages the chain is **median 2, max 5**.

**3.1a A WARNING ON VOCABULARY — ours and the guideline's do not agree.** The tier names above
come from NAMA's own manhole tokens. **G203 uses them differently**, and the clash must be
resolved before any rule is applied to a named tier:

| Term | G203 (p17, p21, p22) | NAMA's tokens / this document |
|---|---|---|
| **Lateral sewer** | **tertiary** — max **45 m**, 1–10 %, OD200 minimum | a street run, median 132 m, cap 920 m |
| **Main sewer** | the street run | *no equivalent tier* |
| **Sub main** | *not used* | a collector route, from NAMA's `SM` tokens |

**The consequence is not cosmetic:** whether a street run takes Table 11's 0.5 % or Table 5's
1 % turns on which name it carries, and `02_DESIGN_CRITERIA.md` calls the wrong choice a
design trap by name. Until this is settled, **every tier rule in this document must state
which vocabulary it is using**, and H8 (minimum sizes and materials by tier) cannot be applied
at all. Proposed resolution, for the engineer's decision: adopt **G203's names** as the
governing vocabulary — rider, lateral (tertiary), main, sub main, trunk main — and carry
NAMA's tokens only as a cross-reference for reading their as-built.

**3.2 Long runs beat short ones — but chamber spacing is capped by the jetting truck, not
by hydraulics.** Every junction is a chamber, a cost and a place to block, so maximise the
distance between junctions. The cap is an operations rule and every adoption standard says
so: **90 m** manhole-to-manhole (Water UK DCG), **120 m** for ≤375 mm and **150 m** for
450–750 mm (Ten States). WEF MOP 60: *"this must be coordinated with the capabilities of the
utility's cleaning equipment."* Target the as-built's median run of 88 m or better; W10
achieved 76 m with 3.5 junctions per km — **and a longest reach of 6,541 m, roughly fifty
times outside every adoption standard in the English-speaking world.**

**3.3 No fingers — and this rule is OURS, not a standard.** A dead-end reach under ~60 m
serving nothing is an artefact of routing. Prune it or absorb it into its neighbour. W10
carried **4,041 fingers, 126 km**.

*Stated honestly because it will be challenged:* **no adoption standard prohibits dead ends
or short branches.** They price them instead — every branch head needs an adopted chamber,
and Water UK DCG B5.2.5 relaxes the requirement below three properties. If we penalise short
branches it is on cost grounds, and it must never be cited to a standard.

**3.4 Straight and uniform between chambers.** Stronger than a preference — it is unanimous
across the adoption standards. Ten States §33.5: *"straight alignment between manholes …
checked by laser beam or lamping"*, and §33.44: *"uniform slope between manholes"*. Water UK
DCG B4.2 requires straight in **both plan and profile**. Curves are a size-gated exception
(>600 mm, beginning and ending at manholes). So a main follows a through-route and changes
direction at a chamber, never between. W10 had no bend rule at all and put 2,372° of
direction change into its DN900+ pipes, one reach turning 165°.

**3.5 Sub mains belong on through-streets.** Chaining a sub main through small residential
roads to save length produces many bends and a route no jetting crew can work. This is
checked and corrected in the review pass (§7), not left to the router.

**3.6 The network is a forest.** Zero loops, by construction and by check. W10's published
layer contains **310 independent cycles**.

**3.7 A head starts at the gate.** The first chamber of a run sits on the road at the foot
of the perpendicular from the first plot's centroid — where the house connection will
actually arrive. Not at the end of a road centreline.

**3.8 Inlets arrive at 90° or better, and anything less is flagged by name.** G203-p30
requires an incoming pipe to make an angle of **not less than 90°** with the flow — no pipe
may arrive pointing against it. Where a street meets at a bad angle, a **bend chamber** goes
a few metres short of the junction so the turn is made in two halves. Where there is no room
for one — 2 m plot clearance, 3 m chamber clearance — the junction is **flagged individually
for a purpose-made chamber with a curved channel**, never quietly accepted.

*Recorded because it is a live inconsistency:* W8's code carries `INLET_MIN_DEG = 85.0` while
its own docstring and assumption register say 75°, and W7 relaxed 90° to 85° as a stated
deviation. **A deviation from a "shall" cannot be carried at three different values.** W11a
holds the guideline's 90° and reports every junction below it as a named exception. W10
checked the angle nowhere at all.

**3.9 Ten metres of clearance at a junction.** A branch starts at least 10 m from the
chamber it will join, so the junction is a chamber and not a collision.

**3.10 The tertiary layer is part of the design, not a detail left for later.** A network that
stops at the lateral has not connected anybody. Three elements, each with its own rule:

- **Property connection** — from the plot to the rider or lateral, at 3–10 %, **maximum 50 m**
  (G203-p18 Tab 4/5), minimum 0.60 m cover, OD160 minimum
- **Rider** — a shallow pipe in the frontage collecting up to **3 property connections** before
  it joins a lateral (G203-p19 3.4)
- **Stub-out** — a capped connection left at the frontage of every **future** plot, sized for
  that area's saturation flow. Building the main and returning later to break into it is the
  most expensive way to connect a house

The gate rule in §3.7 exists to serve this layer: the head chamber sits where the connections
will actually arrive. **W10 has no tertiary layer at all** — its loads land on a corridor node
and no property connects to anything.

---

## 4. Levelling philosophy

**4.1 Lay as shallow as the cover rule allows.** Start every head at minimum cover and let
the invert fall only as fast as it must. Depth is the enemy; it is bought back nowhere.

**4.2 Hold the gradient constant along a run.** Constant slope between chambers is what
makes the drawing match the levels and what the contractor sets his laser to. Change the
gradient at a chamber, never between. W8 laid on round 0.05 % steps for exactly this.

**4.3 But never buy a pumping station with a rounding.** Rounding a gradient to a step is
always upward, so it always adds depth. **Every station that exists only because of the
rounding must be flagged and the rounding relaxed on that run.** Constructability is worth
paying for; it is not worth a pumping station.

**4.4 On steep ground, the pipe does not follow the cliff.** Where the ground falls faster
than the maximum-velocity gradient, the pipe holds its gradient and the difference is taken
at a **drop chamber** — **ramped, not vertical** (DCG B5.2.27), used only where a steeper
gradient is impractical (Ten States triggers a drop at ≥610 mm). W10 had no such rule: it let the pipe follow the ground to a laid
gradient of **980 %**, put 43 reaches over the 3.0 m/s maximum, and published `SLOPE_PCT`
as the *minimum required* gradient, so none of it was visible.

**4.5 Publish the laid gradient.** The deliverable carries the gradient the pipe is laid at,
with the minimum beside it. A layer that reports only the minimum cannot be checked by
anyone.

---

## 5. When to pump

**A depth limit is not a reason to pump. Excavation cost is.** G203-p33 says so in as many
words: *"Where the cost of excavation becomes prohibitive the Engineer shall incorporate
pumping stations into the design."*

**5.1 A breach is usually NOT local — a claim made on 2026-09-01 and retracted on 2026-09-02.**

The retracted claim was that of 239 breaches, 115 recovered below 12 m within 100 m and none
failed to recover within 3 km — so every station was spurious. **It was wrong, and the error
was mine.** The look-ahead clamped the depth to minimum cover at each step
(`d = min(d, MIN_COVER_CROWN + od)`), so at a breach of 12 m or more the test passed on the
first pipe every time and the "recovery distance" was simply the length of one reach. The
comment written beside it — *"the pipe can also come back to cover if the ground drops below
it"* — is the wrong physics: an invert cannot rise.

**Re-measured correctly** (independent rebuild reproducing all 239 lift heights to 0.005 m):

| | |
|---|---|
| Breaches that **never rejoin** — the pipe only gets deeper | **226 of 239** |
| Breaches that **do rejoin** downstream | **13** |
| Of those 13, **cheaper to dig through than to pump** | **10** |
| **Clusters that still need a station** (the level rule 9 counts) | **30 of 30**, at every rate and every cost exponent |

So the station count stands. What survives is the *method*, not the result: **you must look
ahead and price the excursion before placing a station** — it just does not remove many here.

**5.1a The real defect the correct measurement exposed.** W10 triggers a station on **depth**,
and depth is uncorrelated with flow. Node 2933 **breaches by 3 mm** while carrying **36,974
plots and 42,754 m³/d**, and the design answers that with an **85 kW station** where about
279 kOMR of extra excavation would have done. Node 8543 is the same at 16,368 plots. In the
literature a station's cost correlates 0.99 with power and 0.72 with head — so **a station
belongs upstream where the flow is small**, and depth alone must never choose its position.
Station placement has to be a decision variable inside the design search, not a trigger fired
by a threshold.

**5.1b THE CAP-AND-VETO LADDER — the economics is third, never first.** (User instruction,
2026-09-02, and the data proves the need.)

Left to the cost test alone the design runs away, because manning is 86 % of a station's
life-cycle cost and a trench is paid once. Allowed to dig through every breach, W10 would
reach **12–14 m at 132 breaches, 14–16 m at 63, 16–20 m at 27, 20–30 m at 11, and past 30 m
at 6, the deepest chamber at 57.9 m** — while no published excavation rate table extends past
about 5 m. Beyond the cap the economics is arithmetic on air.

So the decision is a ladder of three layers, applied in order. **The first two are
non-negotiable and only the third weighs anything:**

| | Layer | Test | Overridable |
|---|---|---|---|
| 1 | **CAP** | Cover reaches 12 m → **station, mandatory** | **No.** Not by cost, not by anything |
| 2 | **VETO** | A chamber here would be unmaintainable — no plant access, confined-space entry with no rescue route, under a live carriageway → **station** | **No.** A veto, not a term in a sum |
| 3 | **ECONOMICS** | Only now: is a station cheaper over 25 years than carrying the trench on? (§8) | Yes — the only layer that weighs |

**The property that makes it safe: layers 1 and 2 can only ever ADD a station.** The
economics can only make you pump **earlier** than the cap, never later. The design therefore
cannot drift past the cap whatever the rates say — which matters when every rate past 5 m is
an extrapolation.

Each layer catches what the others cannot see. The **cap** exists because the cost curve has
no data past 5 m. The **veto** exists because maintainability appears in no published cost
function — a 12 m chamber is a fifty-year operating liability and no exponent captures it.
The **economics** exists because a bare threshold has no cost basis at all, which is how node
2933 was given an 85 kW station for a **3 mm** breach.

**5.1c The single bounded derogation — the only thing that can REMOVE a station.**
An excursion may be dug through past the cap **only if all of these hold**:

- it **demonstrably rejoins** downstream (here: 13 of 239 breaches, not a general case)
- it peaks **within a stated band**, 12 → 14 m of cover
- it is **short**, and the length is stated
- it is **listed by name**, item by item, never as a class
- it is **put to NWS** and accepted

G203-p33 requires that depths past the range *"shall be investigated with pipe manufacturers
to identify any special requirements"* — that is a procedure to follow, not permission to
ignore the range. So the derogation is a named exception list NWS can accept or refuse line
by line, and it is thirteen lines long, not a licence.

**5.2 The rule is: look ahead, then price the excursion.**

> At a breach, carry the pipe on until the depth recovers. Measure the excursion — how deep,
> for how long, at what diameter. Price that extra excavation against a station plus 25
> years of pumping at 5 %. Place a station only when the trench loses.

**5.3 A lifting station is also a commissioning device.** NAMA's 5A-1 terminates at one, and
that station plus the only built force main is what let 60.8 km and ~5,963 properties be
commissioned without first building 7 km of deep gravity trunk. **A station that makes a
package independently buildable earns its place even when the trench would have been
cheaper.** This is the one case where objective 4 outranks objective 5.

The cost curve, the break-even rule and its sensitivity are in **§8**.

---

## 6. Sizing philosophy

**6.1 The diameter is set by the flow, never by the depth you want.** G203-p29: *"Sewers
shall not be oversized to facilitate flatter slopes."* **This is not an Omani quirk** — Ten
States §33.43 says the same thing independently: *"Flatter slopes shall not be justified with
oversize sewers."* Two unrelated codes, one sentence. Every pipe records **what set its
diameter** — capacity, d/D limit, velocity, or the ultimate-flow horizon. "Depth" is not an
admissible answer.

**6.2 The gradient follows the diameter.** The steeper of Table 11 and the tractive-force
minimum, at the actual peak flow.

**6.3 Size on the ultimate horizon, check on the first year.** Buried civil work is sized at
saturation. Self-cleansing is verified at start-year flows, because a pipe that scours at
2055 and silts in 2030 has failed.

**6.3a Septicity is a design driver here, not an afterthought.** G203 devotes a whole chapter
to hydrogen sulphide, and it is the **reason** the oversizing prohibition in §6.1 exists.
p167 lists the causes: *"a. Oversized lateral sewers and mains resulting in low sewage
velocity in sewers causing solids deposition and long retention times, promoting anaerobic
conditions"* and *"b. Low sewer gradients resulting in low velocity"*. p185 adds that
*"Gravity sewers with very low slopes are the ones with the greatest risk of H₂S formation"*,
and warns about networks that become oversized when occupancy varies seasonally.

At Omani wastewater temperatures the margin is thin, so three things follow:

- **retention time is a design output**, reported per route from the head to the works, not
  discovered later in an odour study
- a long flat run at minimum gradient carrying little flow is the **highest-risk
  combination**, and it is exactly what an outlying branch produces
- the odour and corrosion assessment is a **reason to shorten a marginal branch or not sewer
  it at all** — it belongs in the §7 review pass, not only in the treatment design

**6.4 Diameter is not a tier label.** NAMA used OD160 for every lateral *and* every sub main,
one of them carrying 686 properties, and 110 of their pipes cannot pass today's peak flow.
Copy their shape and their packaging; do not copy their sizing.

---

## 6a. The constraint ranking — what yields when two rules disagree

§9.2 calls a written ranking the most transferable thing in the whole research, and we had
none. This is ours. **Every reach records which constraint set its diameter and which set its
gradient**, so the ranking is auditable rather than aspirational.

**Our ranking differs from Bentley's in one structural way, and it matters.** Bentley resolves
the classic conflict — minimum gradient forcing depth past maximum cover — by *demoting
maximum cover*. We cannot: maximum cover is the 12 m cap. **So for us that conflict is not
resolved by yielding at all. It is resolved by adding a lifting station or a drop chamber.**
That is why our hard set can hold both constraints where Bentley's cannot.

### Hard — never yield. A conflict between two of these is resolved by a station, a drop chamber or a re-route, never by relaxation

| | Constraint | Source |
|---|---|---|
| H1 | No pipe along a dual carriageway; no pipe or chamber in a wadi | project rules 7 and 8 |
| H2 | Capacity ≥ discharge within the d/D limit | G203-p27 Tab 10 |
| H3 | Minimum cover 1.30 m to crown, on the reach's **own** outside diameter | G203-p33 4.6.3 |
| H4 | **Maximum cover 12 m — the cap** | G203-p33 + project rule, no exemption |
| H5 | **Minimum velocity 0.75 m/s AT PEAK FLOW** — G203-p26, *"the minimum velocity in the pipe shall be above 0.75 m/s at peak flow, with preferred velocity at 0.90m/s"*. A "shall", and a **separate, stronger test** than H5a | G203-p26 |
| H5a | Gradient at least the steeper of Table 11 and the tractive-force minimum | G203-p26–29 |
| H6 | Maximum velocity — 3.0 m/s gravity, **2.5 m/s rising main** | G203-p27, p50 |
| H7 | Diameter set by flow; **never** by the depth wanted | G203-p29, Ten States §33.43 |
| H8 | Minimum sizes and materials by tier | G203-p22 Tab 6 |
| H9 | Inlet angle ≥ 90° | G203-p30 |
| H10 | No reverse gradient. **The guideline tolerance is 20 mm**: G203-p29, *"The lines and level of any pipeline shall not deviate from that described in the contract by more than 20mm and combination of such deviation shall not create a reverse gradient."* The 40 mm used in the solver is a **derived** two-end combination, and must be labelled as derived wherever it appears | G203-p29 4.3.1 |
| H11 | Chamber spacing within Table 12 | G203-p30 |
| H12 | The network is a forest — zero loops | project rule |

**Why H5 and H5a are two rules and not one.** Table 11 is a **full-bore** derivation — it
gives the gradient at which a *pipe running full* reaches 0.75 m/s. The p26 "shall" is
0.75 m/s **at peak flow**, which is a partly-full condition. `GRADIENT_CRITERIA_VERIFIED.md`
§2.1 establishes [Certain] that **Table 11 is the weaker of the two**. A design that meets
every gradient in Table 11 can therefore still breach a "shall", which is exactly what H5
exists to catch. The **0.90 m/s preferred** value is a target, not a constraint, and belongs
in the review pass.

**And the τ that H5a depends on is not in the guideline.** The tractive formula
`Smin = 2.33e-4·τ^1.23·Q^-0.461` is given at G203-p27, but **no numeric τ appears anywhere in
G203 or G201** — the project assumes 1.0 Pa and carries it as **GAP-9**. At τ = 2 the
requirement rises by 2.35×. Any station count, depth or diameter that rests on H5a must be
reported with that sensitivity, never as a settled number.

### Preferences — these DO yield, and in this order

| | Preference | Yields to |
|---|---|---|
| P1 | Constant gradient along a run, on round 0.05 % steps | any hard constraint — **and never at the price of a station** (§4.3) |
| P2 | Straight between chambers | P1 |
| P3 | Long runs, few junctions | P1, P2 |
| P4 | Sub mains on through-streets | P1–P3 |
| P5 | Invert or crown matching at a chamber | P1–P4 |
| P6 | Minimum depth | everything above — it is last, as in §1 |

**The reading rule:** a preference never overrides a hard constraint; preferences yield to
each other in the order listed; and where two hard constraints cannot both be met, the
resolution is a **physical element** — a station, a drop chamber, a re-route — recorded by
name with the two constraints that forced it.

---

## 7. Iteration — design strictly, then review and redesign

**One pass is not a design.** The philosophy is two passes and a check:

| Pass | What it does |
|---|---|
| **1 — strict** | Apply every rule mechanically. No judgement, no exceptions. This produces a compliant but ugly network |
| **2 — review** | Look at what pass 1 produced and fix what a person would fix: sub mains moved onto through-streets, fingers absorbed, bends taken out of mains, stations re-sited onto package seams, runs merged |
| **3 — audit** | Re-run every check. Pass 2 must not have broken pass 1's compliance |

Pass 2 is where the design becomes one a real engineer would sign, and **W10 had no pass 2
at all.**

**What the solvers do here, and what to take from it (§9).** Bentley runs a forward pass then
a **reverse reconciliation pass** — four operations, not a re-solve. Adopt that shape: pass 2
is cheap and structural, not another optimisation. And the mature form of our two-pass method
is Duque et al.'s (2020): **let pass 2 feed a cost surrogate back into the layout of pass 1**,
so the review is not merely cosmetic but changes what pass 1 would produce next time. Bentley
say plainly what one pass is worth: *"Automated design is not meant to provide perfect
results."*

---

## 8. The excavation-versus-pumping economics

Researched 2026-09-02. Full account, sources and sensitivity:
`W10/docs/research/DEPTH_VS_PUMPING.md`.

**8.1 The honest headline: it is not the excavation rate that decides. It is the manning.**
NWS's own pre-investment appraisals price station establishment at **169,127 OMR of present
value per station — 86 % of the median station's whole life-cycle cost.** Pumping **energy is
0.4 % of OPEX** (median 49 OMR/yr). Sensitivity across the whole rule: the cost exponent is
irrelevant (≤2 breaches change across b = 1.0–2.0), the excavation rate is weak (11→4
breaches across 10–90 OMR/m/m), and **the manning rule is decisive (10→2).**

**Settle station establishment cost with NWS before spending another day on excavation
rates.** Every hour spent refining the dig cost is an hour spent on the wrong variable.

**8.2 The cost of depth — and the honest limit of what is published.** Three modern fitted
forms exist and they disagree on the depth exponent: **1.0** (Maurer et al. 2010, as
reproduced by Duque et al. 2024), **1.47–1.53** (Mansouri & Khanjani 1999), **2.0** (Swamee &
Sharma). None uses the classic separable `a·D^b·d^c`; every fitted form is additive — a
diameter term plus a depth term plus a manhole term.

**No published depth-banded rate table goes past about 5 m.** Our excursions run 12 to 57 m,
so **every rate we can cite is a two- to threefold extrapolation** and must be labelled as
one. Two empirical tables were extracted in full: Central Coast NSW DSP 2019/20 (median
marginal 93 AUD per metre of trench per metre of depth) and EPA-430/9-81-003 (777 projects;
the marginal cost per unit depth rises **2.7× to 17×** above 15 ft on seven of nine
diameters).

Where the construction method changes — these are the real steps in the curve: **1.52 m**
(OSHA protection required), **~2 m** (microtunnelling starts to beat open cut in a road
reserve), **4.5–4.6 m** (the last band of every published table), **~6 m** (standard trench
boxes stop), **6.1 m** (OSHA requires a professionally designed system), **6–10 m** (the depth
limit the optimisation literature actually imposes), **10–12 m** (G203-p33).

**8.3 A station costs roughly the square root of its duty.** `ln C = 4.3189 + 0.5329·ln Pe`
from 360 Portuguese stations (Cabral et al. 2018), cross-checked against EPA's
`Cost = 1.59×10³·q^0.59`. Exponents 0.53 and 0.59, forty years and a continent apart.

**8.4 The rule, as something implementable.** At a breach, project the un-stationed invert
downstream — `invert_noPS[m] = min(invert_shipped[m], invert_noPS[prev] − s·L)`, exact by the
monotonicity of `min`, no re-solve needed. Integrate the **excursion depth-metre integral**
`DM = ∫(depth_noPS − depth_withPS) dL` in m². Price the dig against a rate anchored at 4 m,
the deepest depth with real data. Price the station as capital plus PVAF(14.0939) × (energy +
M&E + **manning**). Dig through only if it is cheaper **and** the excursion actually rejoins;
if it re-breaches, the station is deferred, not saved.

**Report `K_FLIP = k_ref·C_PS/C_dig`** — the excavation rate at which the decision flips. It
is rate-free, so it survives the missing BoQs and can be quoted today.

---

## 9. What the design software actually does — and does not

Researched 2026-09-02 across Bentley SewerGEMS/SewerCAD, Autodesk InfoDrainage and Civil 3D,
Innovyze InfoWorks ICM and InfoSewer, and the sewer-optimisation literature. Full account and
citations: `W10/docs/research/SEWERGEMS_DESIGN_METHOD.md` and `DESIGN_ENGINES_COMPARED.md`.

**9.1 The finding that matters most: not one of them chooses a layout.** [Certain, four
independent vendors] Every engine sizes and levels a layout the engineer hands it. **A solver
can referee our hydraulics and can never referee our routing** — which is exactly why §1 puts
buildability above hydraulic minimality, and why stages 1–5 of §2 finish before any solver
runs.

**9.2 Bentley alone publishes its rule priority, and it is a real ranking.** Verbatim,
identical in SewerCAD and SewerGEMS:

| | Constraint |
|---|---|
| 1 | Pipe fits within adjacent **existing** structures |
| 2 | Pipe crown not above an adjacent **designed** structure |
| 3 | Capacity ≥ discharge |
| 4 | Downstream pipe ≥ upstream pipe in size |
| 5 | **Downstream** invert/crown matching |
| 6 | **Minimum cover** |
| 7 | **Upstream** invert/crown matching |
| 8 | **Maximum slope** |

Genuinely ordered: every entry that names an overriding rule names one *earlier*
("because of higher design priorities, such as the pipe fitting within existing structures,
the matching criteria may not always be met"). Minimum velocity and minimum slope act but are
unranked. **Maximum cover and maximum velocity are explicitly demoted** as "may be too
limiting"; tractive stress ranks below both.

**ADOPT the artefact. REJECT that demotion.** A written ranking with the winner recorded on
every reach is the most transferable thing in this research and we have no equivalent — W10
shipped 45.92 km below minimum cover partly because nothing stated which rule yields. But for
Bentley maximum cover is a preference; **for us it is the 12 m rule, the single constraint
that decides whether a pumping station exists.** It cannot be demoted.

**9.3 The order of operations, and the reverse pass.** Bentley runs a **forward pass
upstream→downstream, then a separate reverse pass downstream→upstream**. Two passes, fixed,
**no published convergence criterion**. The forward pass answers "size first or level first"
with *neither*: **bracket the diameter range → level → size for capacity → re-level**. The
reverse pass has no sizing, cover or capacity step; its first action adjusts the *structure*
elevation to match the conduit invert — **the manhole yields to the pipe**. Reconciliation,
not re-optimisation.

Two details to copy exactly: **"adjust both ends"** — translate the pipe rigidly rather than
rotating it, which preserves a gradient decision, and for us preserves the round 0.05 % step
the drawing depends on; and the reverse pass is **four operations, not a re-solve** —
precisely the class of cheap check that would have caught our minimum-cover failure.

*The earlier caveat is withdrawn.* A follow-up sweep of Bentley's knowledge base settled it.
KB0016752, scoped to **SewerCAD, SewerGEMS, CivilStorm and StormCAD**, states: *"The design
solver runs a check in both directions, so it is designed both ways."* And KB0016766 — the
article titled for SewerCAD — carries the reverse pass verbatim: *"After designing all pipes
from upstream to downstream, we design all pipes from downstream to upstream."* [Certain,
verified against Bentley's own API]

**Bentley's staff confirm the ranking in plain words.** Jesse Dringoli, their Manager of
Technical Support, answering a user whose design had violated maximum cover to satisfy
minimum slope: *"minimum cover is higher priority than minimum slope, and maximum cover is
below everything. So, automated design selected the smaller (cheaper) pipe size … since it
met all the constraints that it deems as important."*

**And they say plainly what it is for.** KB0016766: *"the constraint-based design feature is
intended to help give you a starting point for your design based on the criteria that you
enter, but the final choice of the design should be based on engineering judgment and
experience."* Dringoli: *"Automated design is not meant to provide perfect results."* Read
that as the vendor agreeing with §7 — one solver pass is not a design, and the review pass is
not optional.

**9.3a Drop structures — the steep-ground mechanism, and it is switchable.** Bentley inserts
them automatically, on two separate triggers (KB0015543, KB0057310):

- `Allow Drop Structure` — fires *"when manhole upstream pipe slope exceeds the conduit
  maximum slope"*, i.e. exactly the cliff case in §4.4
- `Use Drop Structure to Minimize Cover` + `Minimum Drop Depth` — added later, *"to minimize
  the volume of excavation"*

KB0016766 gives the reasoning: a drop is used *"instead of a pipe that is too steep, or
instead of upstream piping that would require much more excavation."* **This is direct vendor
support for §4.4, and it is the feature W10 had no equivalent of** — which is why W10 let a
pipe follow the ground to a laid gradient of 980 %.

**9.3b The design engine will never propose a pumping station.** [Certain — now on a named
Bentley staffer, not only on mechanism] Sushma Choure of Bentley, answering a user asking
directly how to design a pumping station in SewerGEMS: *"SewerGEMS will only analyze pressure
components like the pumping mains, pumps, wet wells etc. You need to enter the input data and
based on the results you can later adjust the sizes to get the desired results."* The
mechanism agrees — only gravity elements are designed (KB0016750) and maximum cover is the
lowest priority, so the solver **keeps deepening rather than escalating to pumping**. It has
no concept of the trade in §5.

**The pumping decision belongs to us, taken before the solver runs, and cannot be delegated
to a referee model.** This is the clearest single justification for the order in §2.

**9.3c Design runs in steady state only.** Confirmed by three named Bentley staff: *"automated
design can only be performed in steady state"* (Dringoli); *"for EPS runs automated design is
not applicable"* (Choure); and it requires the GVF-Convex solver (Kampa). So the referee run
sizes on a steady peak and never on a hydrograph. Anything we want checked dynamically is a
separate analysis run, not a design run.

**9.3d One sizing detail to watch when we use SewerGEMS as referee.** KB0057316: *"during the
constraint based design calculations, pipes are sized based on the flow at the upstream end
of the conduit, before such attenuation is accounted for."* A referee run will therefore size
marginally conservatively against a dynamic solve; do not read small differences as our
error.

**9.4 What the other engines add.**

| | InfoDrainage | Civil 3D | InfoWorks ICM 2027 | InfoSewer | SewerGEMS |
|---|---|---|---|---|---|
| Optimises | shallowest trench | nothing | a penalty score, **not cost** | "cost", undefined | minimum excavation |
| Priority published | **no** | yes, 3 levels | no | no | **yes, 8 levels** |
| Iteration | one downstream sweep, **no reverse pass** | one-directional | unpublished | one pipe at a time | **forward + reverse** |
| Chooses layout | no | no | no | no | **no** |

Convergent across four vendors: the objective is **minimum excavation**, and layout is always
the engineer's. **Nobody ships a global optimiser** — no vendor claims anywhere to minimise
network cost.

*Correction, made 2026-09-02 after a second sweep.* An earlier draft of this section called
the method a "greedy downstream sweep". **That is wrong for Bentley and must not be written
down**: KB0016752 states the solver checks **both** directions. The supportable description is
**priority-ordered constraint satisfaction over a user-drawn layout, run in both directions,
and sold by its own vendor as a starting point.** The one-directional sweep is real for
InfoDrainage (no reverse pass documented) and InfoSewer (which additionally stops the whole
downstream branch on failure) — not for SewerGEMS.

**9.5 The literature, and where it disagrees with the manuals.** The standard objective
(de Villiers et al. 2017, after Moeini & Afshar 2012) prices pipe as a function of **diameter
and mean cover depth**, and manholes by depth — excavation is never a separate term, which is
why "minimise excavation" and "minimise cost" collapse into one for a fixed layout. **But WEF
MOP FD-5 §6.1 requires the lowest ANNUAL cost** — life-cycle, not capital. The academic
literature almost never optimises life-cycle; the manual of practice does, and **our settled
NPV-at-5 %-over-25-years method sides with the manual.** All three formulations agree on one
thing: **station count is not an objective.**

**On separating layout from sizing** the literature openly disagrees. de Villiers et al.
(2018): *"the sub-problems have to be solved simultaneously."* Duque et al. (2020): *"This
separation allows for tractability of the problem **at the price of design optimality**."*
Separation is theoretically wrong and practically universal. **Our justification must be
stated, not assumed**: our layout is nearly determined already — corridors are roads, dual
carriageways excluded, the trunk is an input — so the price is small here. The mature third
way (Duque et al. 2020) separates but gives the layout stage a **cost surrogate refined by
feedback from the sizing stage**, and that is what the two-pass method in §7 should become.

**On depth versus pumping**, Li & Matthew (1990) find the optimum is a *balance* between
excavation depth and the number of online pumping stations, and that **relaxing the maximum
depth constraint reduces the station count.** That independently corroborates our own
measurement — 10 m cover gives 16 stations but 3,095 m of lift, 14 m gives 2,247 m — and
confirms §5: total lift is the honest measure, station count an artefact of where the limit
is drawn.

## 10. How to know you followed this

Philosophy that cannot be checked is decoration. Each rule above has a check in the audit
registry, and the registry runs on every build:

| § | Check |
|---|---|
| 3.1 | Tier populated; tier monotonic downstream; chain ≤3 zones and ≤750 m |
| 3.2 | Median run length reported against the as-built's 88 m |
| 3.3 | Count and length of dead-end reaches under 60 m serving no plot |
| 3.4 | Degrees of direction change per 100 m, by tier |
| 3.6 | Independent cycles = 0 |
| 3.7 | Every head chamber within tolerance of its gate |
| 3.8 | Every branch start ≥10 m from its junction |
| 4.2 | Gradient constant within a run; changes only at chambers |
| 4.3 | Stations attributable to gradient rounding, listed by name |
| 4.4 | Reaches over the velocity maximum; drop chambers where the ground outruns the pipe |
| 4.5 | Laid gradient present in the deliverable |
| 5.2 | Every station carries its excursion economics |
| 3.8 | Inlet angle ≥ 90° at every junction; anything less listed by name |
| 3.10 | Property connections ≤50 m at 3–10 %; riders ≤3 connections; a stub-out at every future frontage |
| 5.1b | Every station attributed to its layer — cap, veto or economics |
| 5.1c | The derogation list: excursions dug through past the cap, named individually |
| 6.1 | Every diameter carries `SIZED_BY`; "depth" prohibited |
| 6.3a | Retention time per route, head to works; long flat lightly-loaded runs flagged for septicity |
| 6a | Every reach records the constraint that set its diameter and the one that set its gradient |
| 2 §3 | The given trunk carries a main diameter over its whole length |
| 7 | Pass 2 ran, and pass 3 passes everything pass 1 passed |

---

## 11. Where this came from

Measured in this project, not borrowed:

- **NAMA's built network** (`W10/shp/W10_existing_built.shp`, 3,266 pipes, 101.1 km, of
  which 2,142 carry real diameters and inverts) — the hierarchy rules, the packaging, the
  run lengths, and the warning about sizing
- **W8** (`W8/docs/LEARNING_FROM_ASBUILT.md`) — the three-tier reading of the manhole IDs,
  the constructability constants, the audit registry
- **W10** (`W10/docs/`, `W10/docs/research/`) — every failure mode this document guards
  against, measured rather than imagined
- **PAM-GUD-203 / -201**, read from source with page citations, in `02_DESIGN_CRITERIA.md`
  and `GRADIENT_CRITERIA_VERIFIED.md`
